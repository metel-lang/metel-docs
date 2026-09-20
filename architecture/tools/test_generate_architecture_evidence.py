import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).with_name("generate_architecture_evidence.py")
SPEC = importlib.util.spec_from_file_location("architecture_evidence", TOOL)
evidence = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = evidence
SPEC.loader.exec_module(evidence)


class ArchitectureEvidenceTests(unittest.TestCase):
    def init_git(self, core: Path) -> None:
        subprocess.run(["git", "-C", str(core), "init", "-q"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.email", "test@example.com"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.name", "test"], check=True, capture_output=True)

    def commit(self, core: Path, message: str = "commit") -> str:
        subprocess.run(["git", "-C", str(core), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "commit", "-q", "-m", message], check=True, capture_output=True)
        return self.head(core)

    def head(self, core: Path) -> str:
        return subprocess.check_output(["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()

    def make_core(self, root: Path, rust: str, fixture: str = "", git: bool = True) -> Path:
        core = root / "core"
        (core / "src").mkdir(parents=True)
        (core / "src/lib.rs").write_text(rust)
        if fixture:
            sidecar = core / "tests/integration/sources/example.toml"
            sidecar.parent.mkdir(parents=True)
            sidecar.write_text(fixture)
        if git:
            self.init_git(core)
            self.commit(core, "initial")
        return core

    def make_spec(self, root: Path, extra: str = "", last_reviewed: str = "") -> Path:
        spec = root / "docs/architecture/spec"
        spec.mkdir(parents=True)
        reviewed_row = f"| `last_reviewed` | {last_reviewed} |\n" if last_reviewed else ""
        (spec / "example.md").write_text(
            "##### Requirement {#arch.example.requirement-1}\n\n"
            "Claim.\n\n| Field | Value |\n|---|---|\n"
            "| `implements` | old path |\n| `verified by` | old test |\n" + reviewed_row + extra
        )
        return spec

    def regenerate(self, spec: Path, core: Path, check: bool, ref: str = "a" * 40):
        previous = evidence.DOCS
        evidence.DOCS = spec.parent.parent
        try:
            return evidence.regenerate(spec, core, evidence.citations(core), check, ref)
        finally:
            evidence.DOCS = previous

    def test_scans_unit_and_fixture_citations_and_regenerates_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {}\n\n// arch-verifies: [\"arch.example.requirement-1\"]\n#[test]\nfn run_is_tested() {}\n", "[options]\narch_verifies = [\"arch.example.requirement-1\"]\n")
            spec = self.make_spec(root, last_reviewed=self.head(core))
            findings = self.regenerate(spec, core, False)
            self.assertEqual([], findings)
            text = (spec / "example.md").read_text()
            self.assertIn("src/lib.rs::run", text)
            self.assertIn("src/lib.rs::run_is_tested", text)
            self.assertIn("tests/integration/sources/example.toml", text)
            self.assertIn("/blob/" + "a" * 40, text)

    def test_missing_evidence_requires_a_structured_exemption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn run() {}\n", git=False)
            spec = self.make_spec(root)
            findings = self.regenerate(spec, core, True)
            self.assertTrue(any("lacks arch-implements" in finding for finding in findings))
            self.assertTrue(any("lacks arch-verifies" in finding for finding in findings))

    def test_verification_citation_must_bind_a_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-verifies: [\"arch.example.requirement-1\"]\npub fn run() {}\n", git=False)
            with self.assertRaisesRegex(ValueError, "#\\[test\\]"):
                evidence.citations(core)

    def test_function_extent_spans_the_body_and_ignores_braces_in_strings(self):
        text = 'fn foo() {\n    let x = "{ not a brace }";\n    x\n}\n'
        self.assertEqual((1, 4), evidence.function_extent(text, 0))

    def test_function_extent_of_a_decl_only_signature_is_one_line(self):
        text = "trait T {\n    fn foo(&self);\n}\n"
        fn_start = text.index("fn foo")
        self.assertEqual((2, 2), evidence.function_extent(text, fn_start))

    def test_missing_last_reviewed_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {}\n")
            spec = self.make_spec(root)  # no last_reviewed
            findings = self.regenerate(spec, core, False)
            self.assertTrue(any("is missing a `last_reviewed` field" in f for f in findings), findings)

    def test_last_reviewed_at_the_latest_touch_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {\n    1\n}\n")
            spec = self.make_spec(root, last_reviewed=self.head(core))
            findings = self.regenerate(spec, core, False)
            self.assertFalse(any("was touched by" in f for f in findings), findings)

    def test_code_touched_after_last_reviewed_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {\n    1\n}\n")
            old_sha = self.head(core)
            (core / "src/lib.rs").write_text(
                "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {\n    2\n}\n"
            )
            new_sha = self.commit(core, "change run's body")
            spec = self.make_spec(root, last_reviewed=old_sha)
            findings = self.regenerate(spec, core, False)
            matches = [f for f in findings if "was touched by" in f]
            self.assertEqual(1, len(matches), findings)
            self.assertIn(new_sha[:12], matches[0])
            self.assertIn(old_sha[:12], matches[0])

    def test_unresolvable_last_reviewed_sha_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {}\n")
            spec = self.make_spec(root, last_reviewed="deadbeefcafe")
            findings = self.regenerate(spec, core, False)
            self.assertTrue(any("is not a commit reachable" in f for f in findings), findings)

    def test_fully_exempt_requirement_never_touches_git(self):
        exemption = (
            "| `implements exemption` | kind: untestable; reason: none; owner: test |\n"
            "| `verification exemption` | kind: untestable; reason: none; owner: test |\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Deliberately not a git repo -- if review_staleness ever called
            # git here for a fully-exempt requirement, this would raise.
            core = self.make_core(root, "pub fn unrelated() {}\n", git=False)
            spec = self.make_spec(root, extra=exemption, last_reviewed="0000000")
            findings = self.regenerate(spec, core, False)
            self.assertFalse(any("was touched by" in f for f in findings), findings)
            self.assertFalse(any("is not a commit reachable" in f for f in findings), findings)

    def test_pest_rule_can_carry_an_implements_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn unrelated() {}\n", git=False)
            (core / "src/grammar.pest").write_text(
                '// arch-implements: ["arch.example.requirement-1"]\n'
                'ident = @{\n    !keyword ~ ("a" | "{")\n}\n\nother = { "x" }\n'
            )
            found = evidence.citations(core)["arch.example.requirement-1"]["implements"]
            self.assertEqual(1, len(found))
            self.assertEqual(("src/grammar.pest", "ident", 1, 4), (str(found[0].path), found[0].item, found[0].line, found[0].end_line))

    def test_pest_marker_must_directly_precede_a_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(Path(directory), "pub fn x() {}\n", git=False)
            (core / "src/grammar.pest").write_text(
                '// arch-implements: ["arch.example.requirement-1"]\nstray text\nident = { "a" }\n'
            )
            with self.assertRaisesRegex(ValueError, "directly precede a grammar rule"):
                evidence.citations(core)

    def test_pest_rule_cannot_be_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(Path(directory), "pub fn x() {}\n", git=False)
            (core / "src/grammar.pest").write_text(
                '// arch-verifies: ["arch.example.requirement-1"]\nident = { "a" }\n'
            )
            with self.assertRaisesRegex(ValueError, "only arch-implements"):
                evidence.citations(core)

    def test_ignored_test_is_not_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(
                Path(directory),
                '// arch-verifies: ["arch.example.requirement-1"]\n#[test]\n#[ignore]\nfn t() {}\n',
                git=False,
            )
            with self.assertRaisesRegex(ValueError, "ignored test never runs"):
                evidence.citations(core)

    def test_skipped_fixture_is_not_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(
                Path(directory),
                "pub fn x() {}\n",
                '[options]\narch_verifies = ["arch.example.requirement-1"]\nskip = "not yet"\n',
                git=False,
            )
            with self.assertRaisesRegex(ValueError, "skipped fixture"):
                evidence.citations(core)

    def with_stubs(self, state=("open", None), stages=None, on=None):
        saved = (evidence.issue_state, evidence.rfc_stages, evidence.today)
        evidence.issue_state = lambda repo, num: state
        evidence.rfc_stages = lambda: stages or {}
        evidence.today = lambda: on or evidence.datetime.date(2026, 9, 20)
        self.addCleanup(lambda: (setattr(evidence, "issue_state", saved[0]),
                                 setattr(evidence, "rfc_stages", saved[1]),
                                 setattr(evidence, "today", saved[2])))

    def test_untestable_exemption_needs_reason_and_owner_only(self):
        self.with_stubs()
        self.assertEqual([], evidence.exemption_problems("kind: untestable; reason: r; owner: o"))
        self.assertEqual(["missing `owner`"], evidence.exemption_problems("kind: untestable; reason: r"))

    def test_legacy_rationale_key_and_missing_kind_are_rejected(self):
        self.with_stubs()
        problems = evidence.exemption_problems("rationale: r; owner: o; review: 2030-01-01")
        self.assertTrue(any("must be one of" in p for p in problems), problems)

    def test_elsewhere_needs_a_ref(self):
        self.with_stubs()
        self.assertIn("kind `elsewhere` needs a `ref`", evidence.exemption_problems("kind: elsewhere; reason: r; owner: o"))

    def test_blocked_needs_ref_owner_and_review(self):
        self.with_stubs()
        problems = evidence.exemption_problems("kind: blocked; reason: r")
        self.assertIn("missing `owner`", problems)
        self.assertIn("kind `blocked` needs a `ref`", problems)
        self.assertTrue(any("needs a `review` date" in p for p in problems), problems)

    def test_blocked_exemption_expires(self):
        self.with_stubs()
        problems = evidence.exemption_problems("kind: blocked; ref: metel-core#9; reason: r; owner: o; review: 2026-09-19")
        self.assertTrue(any("has passed" in p for p in problems), problems)
        self.assertEqual([], evidence.exemption_problems("kind: blocked; ref: metel-core#9; reason: r; owner: o; review: 2026-09-20"))

    def test_blocked_on_a_closed_issue_prompts_adding_evidence(self):
        self.with_stubs(state=("closed", None))
        problems = evidence.exemption_problems("kind: blocked; ref: metel-core#9; reason: r; owner: o; review: 2030-01-01")
        self.assertTrue(any("now closed" in p and "delete this exemption row" in p for p in problems), problems)

    def test_unreachable_issue_api_never_fails(self):
        self.with_stubs(state=(None, "GitHub API request failed"))
        self.assertEqual([], evidence.exemption_problems("kind: blocked; ref: metel-core#9; reason: r; owner: o; review: 2030-01-01"))

    def test_blocked_on_an_implemented_rfc_prompts_adding_evidence(self):
        self.with_stubs(stages={"rfc-0001": "implemented"})
        problems = evidence.exemption_problems("kind: blocked; ref: RFC-0001; reason: r; owner: o; review: 2030-01-01")
        self.assertTrue(any("now implemented" in p for p in problems), problems)

    def test_expired_blocked_exemption_is_a_finding_on_both_sides(self):
        self.with_stubs()
        exemption = "kind: blocked; ref: metel-core#9; reason: r; owner: o; review: 2020-01-01"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn unrelated() {}\n", git=False)
            spec = self.make_spec(
                root,
                extra=f"| `implements exemption` | {exemption} |\n| `verification exemption` | {exemption} |\n",
                last_reviewed="0000000",
            )
            findings = self.regenerate(spec, core, False)
            for field in ("implements exemption", "verification exemption"):
                self.assertTrue(any(f"`{field}`" in f and "has passed" in f for f in findings), findings)

    def test_marker_above_a_non_fn_item_does_not_latch_onto_a_later_fn(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(
                Path(directory),
                '// arch-implements: ["arch.example.requirement-1"]\nstruct Env {}\n\nfn later() {}\n',
                git=False,
            )
            with self.assertRaisesRegex(ValueError, "directly precede its item"):
                evidence.citations(core)

    def test_comments_and_multiline_attributes_may_sit_between_marker_and_item(self):
        with tempfile.TemporaryDirectory() as directory:
            core = self.make_core(
                Path(directory),
                '// arch-implements: ["arch.example.requirement-1"]\n'
                '// an explanatory comment\n#[allow(\n    clippy::too_many_lines\n)]\n'
                '/// docs\npub(crate) fn run() {}\n',
                git=False,
            )
            found = evidence.citations(core)["arch.example.requirement-1"]["implements"]
            self.assertEqual("run", found[0].item)


if __name__ == "__main__":
    unittest.main()
