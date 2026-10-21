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


class EvidenceHelpers:
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

    def regenerate(self, spec: Path, core: Path, check: bool, ref: str = "a" * 40, warnings=None, audit: bool = True):
        previous = evidence.DOCS
        evidence.DOCS = spec.parent.parent
        # `last_touch_commit` is memoized per citation for one run; a test that commits and
        # checks again is a new run.
        evidence.last_touch_commit.cache_clear()
        try:
            return evidence.regenerate(spec, core, evidence.citations(core), check, ref, warnings, audit)
        finally:
            evidence.DOCS = previous


class ArchitectureEvidenceTests(EvidenceHelpers, unittest.TestCase):

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
            self.assertEqual(
                ("src/grammar.pest", "ident", 1, 2, 4),
                (str(found[0].path), found[0].item, found[0].line, found[0].start_line, found[0].end_line),
            )

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

    def test_editing_a_sibling_marker_does_not_flag_the_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = "fn run() {\n    1\n}\n"
            marker = '// arch-implements: ["arch.example.requirement-%d"]\n'
            core = self.make_core(root, marker % 1 + marker % 2 + body)
            reviewed = self.head(core)
            (core / "src/lib.rs").write_text(marker % 1 + '// arch-implements: ["arch.example.requirement-2"] \n' + body)
            self.commit(core, "touch only the sibling marker")
            spec = self.make_spec(root, last_reviewed=reviewed)
            findings = self.regenerate(spec, core, False)
            self.assertFalse(any("was touched by" in f for f in findings), findings)


class CitationRefStabilityTests(unittest.TestCase):
    """metel-core#1272 found `git_ref`'s repo-wide ref (the most recent commit
    to touch *any* citation marker anywhere) baked into every citation's
    rendered link uniformly: a commit that only moved code near *one*
    citation changed the embedded ref for *all* of them, so `--check` failed
    across the whole corpus for a change relevant to none of it but that one
    citation. `citation_ref`/`render` replaced the shared ref with each
    citation's own `last_touch_commit`, so an unrelated commit -- even one
    that moves a *different* citation -- never changes a citation whose own
    line didn't move."""

    def init_git(self, core: Path) -> None:
        subprocess.run(["git", "-C", str(core), "init", "-q"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(core), "config", "user.email", "test@example.com"], check=True, capture_output=True
        )
        subprocess.run(["git", "-C", str(core), "config", "user.name", "test"], check=True, capture_output=True)

    def commit(self, core: Path, message: str = "commit") -> str:
        subprocess.run(["git", "-C", str(core), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "commit", "-q", "-m", message], check=True, capture_output=True)
        return subprocess.check_output(["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()

    def test_shifting_one_citations_line_does_not_change_either_citations_ref(self):
        """`git log -L` tracks a cited item's own content through history, not
        its raw line number -- inserting an unrelated line above `a` (moving
        its line number, exactly what a dedup/reorg commit like metel-core#1281
        does to every citation below the code it removes) does not change
        `a`'s last-touch commit, since `a`'s own text never changed. Confirms
        the fix's benefit is broader than "an unrelated file changed": a
        citation surviving unrelated churn *in its own file* also keeps its
        ref, unlike the old repo-wide `git_ref`, which changed for both."""
        with tempfile.TemporaryDirectory() as directory:
            core = Path(directory) / "core"
            core.mkdir()
            self.init_git(core)
            (core / "a.rs").write_text('// arch-implements: ["arch.example.requirement-1"]\npub fn a() {}\n')
            (core / "b.rs").write_text('// arch-implements: ["arch.example.requirement-2"]\npub fn b() {}\n')
            first = self.commit(core, "add both citations")
            # Insert an unrelated blank line above `a`'s citation, shifting its
            # line number down by one -- `a`'s own text is otherwise untouched.
            (core / "a.rs").write_text(
                '\n// arch-implements: ["arch.example.requirement-1"]\npub fn a() {}\n'
            )
            self.commit(core, "shift a's citation down; a's own text and b's file untouched")
            evidence.last_touch_commit.cache_clear()
            citation_a = evidence.Citation(Path("a.rs"), "a", 2, 3, 3)
            citation_b = evidence.Citation(Path("b.rs"), "b", 1, 1, 1)
            self.assertEqual(evidence.citation_ref(core, citation_a, None), first)
            self.assertEqual(evidence.citation_ref(core, citation_b, None), first)

    def test_explicit_core_ref_overrides_last_touch_commit_uniformly(self):
        with tempfile.TemporaryDirectory() as directory:
            core = Path(directory) / "core"
            core.mkdir()
            self.init_git(core)
            (core / "a.rs").write_text('// arch-implements: ["arch.example.requirement-1"]\npub fn a() {}\n')
            self.commit(core, "add a citation")
            evidence.last_touch_commit.cache_clear()
            citation_a = evidence.Citation(Path("a.rs"), "a", 1, 1, 1)
            self.assertEqual(evidence.citation_ref(core, citation_a, "pinned-ref"), "pinned-ref")

    def test_last_touch_commit_is_memoized_per_citation(self):
        with tempfile.TemporaryDirectory() as directory:
            core = Path(directory) / "core"
            core.mkdir()
            self.init_git(core)
            (core / "a.rs").write_text('// arch-implements: ["arch.example.requirement-1"]\npub fn a() {}\n')
            self.commit(core, "add a citation")
            evidence.last_touch_commit.cache_clear()
            citation_a = evidence.Citation(Path("a.rs"), "a", 1, 1, 1)
            first_call = evidence.last_touch_commit(core, citation_a)
            info = evidence.last_touch_commit.cache_info()
            second_call = evidence.last_touch_commit(core, citation_a)
            self.assertEqual(first_call, second_call)
            self.assertEqual(evidence.last_touch_commit.cache_info().hits, info.hits + 1)


class RecordAffectsCodeLinkTests(unittest.TestCase):
    """`## Affects` `path::symbol` citations (metel-core#1236 level 2)."""

    def make_core(self, root: Path, rust: str, filename: str = "src/lib.rs") -> Path:
        core = root / "core"
        target = core / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rust)
        return core

    def write_record(self, root: Path, affects_line: str, dirname: str = "limitations") -> Path:
        records = root / "docs" / "architecture" / dirname
        records.mkdir(parents=True, exist_ok=True)
        path = records / "example.md"
        path.write_text(
            "---\nid: LIMIT-X-001\n---\n\n## Limitation\n\nSome limitation.\n\n"
            f"## Affects\n\n{affects_line}\n\n## Resolution\n\nNone yet.\n"
        )
        return records

    def regenerate(self, records: Path, core: Path, check: bool, ref: str = "a" * 40):
        previous = evidence.DOCS
        evidence.DOCS = records.parent.parent.parent
        try:
            return evidence.regenerate_record_affects(records, core, ref, check)
        finally:
            evidence.DOCS = previous

    def test_resolves_a_function_and_rewrites_the_bullet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "fn one() {}\n\npub fn target_fn() -> i64 {\n    1\n}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`")
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            text = (records / "example.md").read_text()
            self.assertIn(f"[`src/lib.rs::target_fn`](https://github.com/metel-lang/metel-core/blob/{'a'*40}/src/lib.rs#L3)", text)

    def test_resolves_a_static_a_struct_and_a_pest_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "static COUNTER: u32 = 0;\n\npub struct Thing {\n    x: i64,\n}\n")
            self.make_core(root, "ident = { ASCII_ALPHA+ }\n", filename="src/grammar.pest")
            records = self.write_record(
                root,
                "- `src/lib.rs::COUNTER`\n- `src/lib.rs::Thing`\n- `src/grammar.pest::ident`",
            )
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            text = (records / "example.md").read_text()
            self.assertIn("src/lib.rs#L1", text)
            self.assertIn("src/lib.rs#L3", text)
            self.assertIn("src/grammar.pest#L1", text)

    def test_bare_path_with_no_symbol_is_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs` (`target_fn`)")
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            text = (records / "example.md").read_text()
            self.assertIn("- `src/lib.rs` (`target_fn`)", text)
            self.assertNotIn("](https://", text)

    def test_missing_symbol_is_a_finding_not_a_silent_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn real_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::not_real`")
            findings = self.regenerate(records, core, False)
            self.assertTrue(any("no fn/static/const/struct/enum/trait named" in f for f in findings), findings)
            text = (records / "example.md").read_text()
            self.assertIn("- `src/lib.rs::not_real`", text)  # left as-is, not silently linked

    def test_missing_file_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn f() {}\n")
            records = self.write_record(root, "- `src/does_not_exist.rs::f`")
            findings = self.regenerate(records, core, False)
            self.assertTrue(any("no such file" in f for f in findings), findings)

    def test_check_mode_never_writes_and_ignores_the_link(self):
        # metel-core#1417: whether the bullet carries a rendered link is cosmetic. A bare
        # `path::symbol` that resolves passes --check; only an unresolvable one is a finding.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`")
            before = (records / "example.md").read_text()
            self.assertEqual([], self.regenerate(records, core, True))
            self.assertEqual(before, (records / "example.md").read_text())

    def test_check_mode_fails_when_the_symbol_no_longer_resolves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`")
            self.regenerate(records, core, False)
            (core / "src/lib.rs").write_text("pub fn renamed() {}\n")
            findings = self.regenerate(records, core, True)
            self.assertEqual(1, len(findings), findings)
            self.assertIn("target_fn", findings[0])

    def test_check_mode_ignores_line_drift_in_a_rendered_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`")
            self.regenerate(records, core, False)
            (core / "src/lib.rs").write_text("// a\n// b\n// c\npub fn target_fn() {}\n")
            self.assertEqual([], self.regenerate(records, core, True))

    def test_rerun_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`")
            self.regenerate(records, core, False)
            once = (records / "example.md").read_text()
            findings = self.regenerate(records, core, True)
            self.assertEqual([], findings)
            self.assertEqual(once, (records / "example.md").read_text())

    def test_gaps_directory_is_also_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn target_fn() {}\n")
            records = self.write_record(root, "- `src/lib.rs::target_fn`", dirname="gaps")
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            self.assertIn("target_fn", (records / "example.md").read_text())

    def test_missing_records_directory_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn f() {}\n")
            findings = evidence.regenerate_record_affects(root / "docs/architecture/limitations", core, "a" * 40, False)
            self.assertEqual([], findings)


class RecordMarkerTests(unittest.TestCase):
    """`// limit: [...]` code-side markers (metel-core#1236 level 3, ADR-0055 amendment
    #1247): the delimited subsection of `## Affects`, and the drift check."""

    def init_git(self, core: Path) -> None:
        subprocess.run(["git", "-C", str(core), "init", "-q"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.email", "test@example.com"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.name", "test"], check=True, capture_output=True)

    def commit(self, core: Path, message: str = "commit") -> None:
        subprocess.run(["git", "-C", str(core), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "commit", "-q", "-m", message], check=True, capture_output=True)

    def make_core(self, root: Path, rust: str, git: bool = False) -> Path:
        core = root / "core"
        (core / "src").mkdir(parents=True)
        (core / "src/lib.rs").write_text(rust)
        if git:
            self.init_git(core)
            self.commit(core, "initial")
        return core

    def write_record(self, root: Path, record_id: str, affects: str = "", disposition: str = "known") -> Path:
        records = root / "docs" / "architecture" / "limitations"
        records.mkdir(parents=True, exist_ok=True)
        path = records / (record_id.lower() + ".md")
        path.write_text(
            f"---\nid: {record_id}\ndisposition: {disposition}\n---\n\n## Limitation\n\nSome limitation.\n\n"
            f"## Affects\n\n{affects}\n\n## Resolution\n\nNone yet.\n"
        )
        return records

    def regenerate(self, records: Path, core: Path, check: bool, ref: str = "a" * 40):
        previous = evidence.DOCS
        evidence.DOCS = records.parent.parent.parent
        try:
            return evidence.regenerate_record_markers(records, core, ref, check)
        finally:
            evidence.DOCS = previous

    def test_marker_inserts_a_new_delimited_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            text = (records / "limit-x-001.md").read_text()
            self.assertIn(evidence.LIMIT_MARKERS_START, text)
            self.assertIn(f"[`src/lib.rs::target_fn`](https://github.com/metel-lang/metel-core/blob/{'a'*40}/src/lib.rs#L1)", text)
            self.assertIn(evidence.LIMIT_MARKERS_END, text)
            # a blank line separates the block from the next section
            self.assertIn(f"{evidence.LIMIT_MARKERS_END}\n\n## Resolution", text)

    def test_resolves_static_struct_and_pest_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\nstatic COUNTER: u32 = 0;\n')
            (core / "src/grammar.pest").write_text('// limit: ["LIMIT-X-001"]\nident = { ASCII_ALPHA+ }\n')
            (core / "src/shapes.rs").write_text('// limit: ["LIMIT-X-001"]\npub struct Thing { x: i64 }\n')
            records = self.write_record(root, "LIMIT-X-001")
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            text = (records / "limit-x-001.md").read_text()
            self.assertIn("COUNTER", text)
            self.assertIn("src/grammar.pest#L1", text)
            self.assertIn("Thing", text)

    def test_no_markers_is_a_true_no_op(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn f() {}\n")
            records = self.write_record(root, "LIMIT-X-001", affects="- `arch.resolution.requirement-1`")
            before = (records / "limit-x-001.md").read_text()
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)
            self.assertEqual(before, (records / "limit-x-001.md").read_text())

    def test_hand_written_bullets_are_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(
                root, "LIMIT-X-001",
                affects="- `arch.resolution.requirement-1`\n- `RFC-0161`\n- `src/other.rs::hand_typed`",
            )
            self.regenerate(records, core, False)
            text = (records / "limit-x-001.md").read_text()
            self.assertIn("- `arch.resolution.requirement-1`", text)
            self.assertIn("- `RFC-0161`", text)
            self.assertIn("- `src/other.rs::hand_typed`", text)

    def test_block_removed_when_no_longer_marked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            self.regenerate(records, core, False)
            self.assertIn(evidence.LIMIT_MARKERS_START, (records / "limit-x-001.md").read_text())
            (core / "src/lib.rs").write_text("pub fn target_fn() {}\n")  # marker removed
            findings = self.regenerate(records, core, False)
            self.assertEqual([], findings)  # no git history here -- nothing to flag as drift
            self.assertNotIn(evidence.LIMIT_MARKERS_START, (records / "limit-x-001.md").read_text())

    def test_marker_citing_a_missing_record_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-999"]\npub fn f() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            findings = self.regenerate(records, core, False)
            self.assertTrue(any("LIMIT-X-999" in f and "does not exist" in f for f in findings), findings)

    def test_marker_citing_an_inactive_record_is_a_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn f() {}\n')
            records = self.write_record(root, "LIMIT-X-001", disposition="resolved")
            findings = self.regenerate(records, core, False)
            self.assertTrue(any("resolved" in f and "LIMIT-X-001" in f for f in findings), findings)

    def test_check_mode_reports_stale_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            before = (records / "limit-x-001.md").read_text()
            findings = self.regenerate(records, core, True)
            # ADR-0064: a record with no committed block is the normal state; the block is
            # produced at publish time, so there is nothing to compare.
            self.assertEqual([], findings)
            self.assertEqual(before, (records / "limit-x-001.md").read_text())

    def test_check_mode_still_compares_a_committed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            self.regenerate(records, core, False)  # writes the block
            (core / "src/lib.rs").write_text('// limit: ["LIMIT-X-001"]\npub fn other_fn() {}\n')
            findings = self.regenerate(records, core, True)
            self.assertTrue(any("stale" in f and "src/lib.rs::target_fn" in f for f in findings), findings)

    def test_check_mode_ignores_line_drift_in_the_marker_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            self.regenerate(records, core, False)
            (core / "src/lib.rs").write_text('// a\n// b\n// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            self.assertEqual([], self.regenerate(records, core, True))

    def test_check_mode_names_a_citation_the_block_lists_but_the_code_no_longer_marks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn old_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            self.regenerate(records, core, False)
            (core / "src/lib.rs").write_text('// limit: ["LIMIT-X-001"]\npub fn new_fn() {}\n')
            findings = [f for f in self.regenerate(records, core, True) if "src/lib.rs::" in f]
            self.assertEqual(2, len(findings), findings)
            self.assertTrue(any("lists `src/lib.rs::old_fn`" in f for f in findings), findings)
            self.assertTrue(any("does not list `src/lib.rs::new_fn`" in f for f in findings), findings)

    def test_rerun_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = self.write_record(root, "LIMIT-X-001")
            self.regenerate(records, core, False)
            once = (records / "limit-x-001.md").read_text()
            findings = self.regenerate(records, core, True)
            self.assertEqual([], findings)
            self.assertEqual(once, (records / "limit-x-001.md").read_text())

    def test_drift_flags_a_record_whose_marker_vanished_from_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n', git=True)
            (core / "src/lib.rs").write_text("pub fn target_fn() {}\n")
            self.commit(core, "remove the marker")
            records = self.write_record(root, "LIMIT-X-001")
            findings = self.regenerate(records, core, False)
            self.assertTrue(
                any("LIMIT-X-001" in f and "no longer is by any current" in f for f in findings), findings
            )

    def test_resolved_record_may_have_lost_its_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n', git=True)
            (core / "src/lib.rs").write_text("pub fn target_fn() {}\n")
            self.commit(core, "remove the marker")
            records = self.write_record(root, "LIMIT-X-001", disposition="resolved")
            findings = self.regenerate(records, core, False)
            self.assertFalse(any("no longer is by any current" in f for f in findings), findings)

    def test_no_drift_finding_while_the_marker_is_still_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, '// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n', git=True)
            records = self.write_record(root, "LIMIT-X-001")
            findings = self.regenerate(records, core, False)
            self.assertFalse(any("no longer is by any current" in f for f in findings), findings)

    def test_missing_records_directory_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn f() {}\n")
            findings = evidence.regenerate_record_markers(root / "docs/architecture/limitations", core, "a" * 40, False)
            self.assertEqual([], findings)


class Level2Level3BoundaryTests(unittest.TestCase):
    """The cross-function bug found and fixed while building level 3: level 2's own
    Affects rewriting must never see or touch level 3's delimited block, even though
    both produce an identically-shaped link-wrapped `path::symbol` bullet."""

    def make_core(self, root: Path, rust: str) -> Path:
        core = root / "core"
        (core / "src").mkdir(parents=True)
        (core / "src/lib.rs").write_text(rust)
        return core

    def write_record(self, root: Path, affects: str) -> Path:
        records = root / "docs" / "architecture" / "limitations"
        records.mkdir(parents=True, exist_ok=True)
        path = records / "limit-x-001.md"
        path.write_text(
            f"---\nid: LIMIT-X-001\ndisposition: known\n---\n\n## Limitation\n\nSome limitation.\n\n"
            f"## Affects\n\n{affects}\n\n## Resolution\n\nNone yet.\n"
        )
        return records

    def regenerate_both(self, records: Path, core: Path, check: bool, ref: str = "a" * 40):
        previous = evidence.DOCS
        evidence.DOCS = records.parent.parent.parent
        try:
            f1 = evidence.regenerate_record_affects(records, core, ref, check)
            f2 = evidence.regenerate_record_markers(records, core, ref, check)
            return f1, f2
        finally:
            evidence.DOCS = previous

    def test_level2_and_level3_coexist_and_stay_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(
                root,
                'pub fn hand_named() {}\n\n// limit: ["LIMIT-X-001"]\npub fn marked_fn() {}\n',
            )
            records = self.write_record(root, "- `src/lib.rs::hand_named`")
            f1, f2 = self.regenerate_both(records, core, False)
            self.assertEqual([], f1 + f2)
            text = (records / "limit-x-001.md").read_text()
            self.assertIn("hand_named", text)
            self.assertIn("marked_fn", text)
            # a second full pass changes nothing (level 2 does not perturb level 3's
            # block, and vice versa)
            once = text
            f1, f2 = self.regenerate_both(records, core, True)
            self.assertEqual([], f1 + f2)
            self.assertEqual(once, (records / "limit-x-001.md").read_text())


class SemanticCheckTests(EvidenceHelpers, unittest.TestCase):
    """metel-core#1417: --check compares what is cited, not how a link renders."""

    RUN = '// arch-implements: ["arch.example.requirement-1"]\npub fn run() {\n    1\n}\n'
    TEST = '\n// arch-verifies: ["arch.example.requirement-1"]\n#[test]\nfn run_is_tested() {}\n'
    CHANGED = RUN.replace("    1\n", "    2\n")

    def rendered(self, root: Path, rust: str | None = None):
        core = self.make_core(root, rust if rust is not None else self.RUN + self.TEST)
        spec = self.make_spec(root, last_reviewed=self.head(core))
        self.assertEqual([], self.regenerate(spec, core, False))  # write the cells
        self.assertEqual([], self.regenerate(spec, core, True))   # and they check clean
        return core, spec

    def check(self, spec: Path, core: Path, warnings=None):
        return self.regenerate(spec, core, True, warnings=warnings)

    def test_inserting_lines_above_a_cited_function_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text("// intro\n// more\n// lines\n" + self.RUN + self.TEST)
            self.commit(core, "insert lines above the cited items")
            self.assertEqual([], self.check(spec, core, []))

    def test_a_newer_commit_to_the_cited_function_does_not_fail_only_warns(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.CHANGED + self.TEST)
            self.commit(core, "change run's body")
            warnings: list[str] = []
            self.assertEqual([], self.check(spec, core, warnings))
            self.assertEqual(1, len(warnings), warnings)
            self.assertIn("last_reviewed", warnings[0])

    def test_moving_a_function_within_its_file_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.TEST.lstrip("\n") + "\n" + self.RUN)
            self.commit(core, "reorder")
            self.assertEqual([], self.check(spec, core, []))

    def test_a_removed_citation_fails_naming_the_requirement_and_the_citation(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.TEST.lstrip("\n"))
            self.commit(core, "remove run and its marker")
            findings = self.check(spec, core)
            self.assertTrue(
                any("`arch.example.requirement-1`" in f and "`implements` cell" in f
                    and "lists `src/lib.rs::run`" in f and "no longer cites" in f for f in findings),
                findings,
            )

    def test_a_renamed_function_fails_with_both_names(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.RUN.replace("run", "go") + self.TEST)
            self.commit(core, "rename run to go")
            findings = self.check(spec, core)
            self.assertTrue(any("lists `src/lib.rs::run`" in f for f in findings), findings)
            self.assertTrue(any("does not list `src/lib.rs::go`" in f for f in findings), findings)

    def test_moving_a_citation_to_another_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.TEST.lstrip("\n"))
            (core / "src/other.rs").write_text(self.RUN)
            self.commit(core, "move run to other.rs")
            findings = self.check(spec, core)
            self.assertTrue(any("lists `src/lib.rs::run`" in f for f in findings), findings)
            self.assertTrue(any("does not list `src/other.rs::run`" in f for f in findings), findings)

    def test_each_failing_citation_gets_its_own_line_never_a_corpus_lump(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(
                (self.RUN + self.TEST).replace("run_is_tested", "renamed_test").replace("fn run", "fn go")
            )
            self.commit(core, "rename both items")
            findings = [f for f in self.check(spec, core, []) if "cell" in f]
            self.assertEqual(4, len(findings), findings)
            self.assertFalse(any("corpus" in f or "generated evidence is stale" in f for f in findings), findings)

    def test_an_unknown_claim_id_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(
                (self.RUN + self.TEST) + '\n// arch-implements: ["arch.example.requirement-9"]\npub fn extra() {}\n'
            )
            self.commit(core, "cite an unknown claim")
            findings = self.check(spec, core)
            self.assertTrue(any("unknown Architecture Spec claim `arch.example.requirement-9`" in f for f in findings), findings)

    def test_check_mode_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text("// x\n" + self.RUN.replace("run", "go") + self.TEST)
            self.commit(core, "rename")
            before = (spec / "example.md").read_text()
            self.check(spec, core)
            self.assertEqual(before, (spec / "example.md").read_text())

    def test_a_stale_last_reviewed_is_a_warning_when_warnings_are_collected(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.CHANGED + self.TEST)
            self.commit(core, "change run")
            warnings: list[str] = []
            findings = self.check(spec, core, warnings)
            self.assertEqual([], findings)
            self.assertTrue(any("was touched by" in w for w in warnings), warnings)

    def test_a_stale_last_reviewed_stays_an_error_without_a_warnings_list(self):
        with tempfile.TemporaryDirectory() as directory:
            core, spec = self.rendered(Path(directory))
            (core / "src/lib.rs").write_text(self.CHANGED + self.TEST)
            self.commit(core, "change run")
            self.assertTrue(any("was touched by" in f for f in self.check(spec, core)))

    def test_a_missing_last_reviewed_field_is_always_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST)
            spec = self.make_spec(root)  # no last_reviewed
            self.regenerate(spec, core, False)
            warnings: list[str] = []
            findings = self.check(spec, core, warnings)
            self.assertTrue(any("missing a `last_reviewed` field" in f for f in findings), findings)
            self.assertEqual([], warnings)

    def run_main(self, root: Path, core: Path, *extra: str):
        import contextlib
        import io

        previous_docs, previous_argv = evidence.DOCS, sys.argv
        evidence.DOCS = root / "docs"
        evidence.last_touch_commit.cache_clear()
        sys.argv = ["generate", "--core", str(core), "--check", *extra]
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                code = evidence.main()
        finally:
            evidence.DOCS, sys.argv = previous_docs, previous_argv
        return code, err.getvalue()

    def test_warnings_exit_zero_but_strict_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core, spec = self.rendered(root)
            (core / "src/lib.rs").write_text(self.CHANGED + self.TEST)
            self.commit(core, "change run")
            code, err = self.run_main(root, core)
            self.assertEqual(0, code, err)
            self.assertIn("warning:", err)
            code, err = self.run_main(root, core, "--strict")
            self.assertEqual(1, code, err)
            self.assertIn("--strict", err)

    def test_strict_is_clean_when_nothing_is_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core, spec = self.rendered(root)
            code, err = self.run_main(root, core, "--strict")
            self.assertEqual(0, code, err)


class PublishModeTests(EvidenceHelpers, unittest.TestCase):
    """ADR-0064 / metel-core#1509: the committed cells are a placeholder; `--publish` renders them."""

    RUN = '// arch-implements: ["arch.example.requirement-1"]\npub fn run() {\n    1\n}\n'
    TEST = '\n// arch-verifies: ["arch.example.requirement-1"]\n#[test]\nfn run_is_tested() {}\n'

    def placeholder_spec(self, root: Path, **kwargs) -> Path:
        spec = self.make_spec(root, **kwargs)
        page = spec / "example.md"
        page.write_text(
            page.read_text()
            .replace("| old path |", f"| {evidence.EVIDENCE_PLACEHOLDER} |")
            .replace("| old test |", f"| {evidence.EVIDENCE_PLACEHOLDER} |")
        )
        return spec

    def publish(self, spec: Path, core: Path, ref: str = "v9.9.9", warnings=None):
        return self.regenerate(spec, core, False, ref, warnings, audit=False)

    def test_publish_pins_links_to_the_ref_with_no_git_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST, git=False)  # not even a git repository
            spec = self.placeholder_spec(root)
            self.assertEqual([], self.publish(spec, core))
            text = (spec / "example.md").read_text()
            self.assertIn("(https://github.com/metel-lang/metel-core/blob/v9.9.9/src/lib.rs#L1)", text)
            self.assertIn("`src/lib.rs::run`", text)
            self.assertIn("`src/lib.rs::run_is_tested`", text)
            self.assertNotIn(evidence.EVIDENCE_PLACEHOLDER, text)

    def test_publish_does_not_audit_last_reviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST, git=False)
            spec = self.placeholder_spec(root, last_reviewed="deadbeefcafe")  # unresolvable, no history
            self.assertEqual([], self.publish(spec, core))
            # the same input is audited when not publishing
            findings = self.regenerate(spec, self.make_core(root / "g", self.RUN + self.TEST), True)
            self.assertTrue(any("last_reviewed" in f for f in findings), findings)

    def test_check_never_compares_a_placeholder_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST)
            spec = self.placeholder_spec(root, last_reviewed=self.head(core))
            before = (spec / "example.md").read_text()
            self.assertEqual([], self.regenerate(spec, core, True))
            self.assertEqual(before, (spec / "example.md").read_text())

    def test_a_requirement_with_no_evidence_still_fails_with_a_placeholder_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn run() {}\n", git=False)
            spec = self.placeholder_spec(root)
            findings = self.regenerate(spec, core, True)
            self.assertTrue(any("lacks arch-implements" in f for f in findings), findings)

    def test_publish_is_idempotent_and_a_rendered_cell_then_checks_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST)
            spec = self.placeholder_spec(root, last_reviewed=self.head(core))
            self.publish(spec, core)
            once = (spec / "example.md").read_text()
            self.publish(spec, core)
            self.assertEqual(once, (spec / "example.md").read_text())
            self.assertEqual([], self.regenerate(spec, core, True))

    def test_publish_skips_the_limit_history_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = root / "core"
            (core / "src").mkdir(parents=True)
            (core / "src/lib.rs").write_text('// limit: ["LIMIT-X-001"]\npub fn target_fn() {}\n')
            records = root / "docs/architecture/limitations"
            records.mkdir(parents=True)
            (records / "limit-x-001.md").write_text(
                "---\nid: LIMIT-X-001\ndisposition: known\n---\n\n## Limitation\n\nx.\n\n"
                "## Affects\n\n- `src/lib.rs::target_fn`\n\n## Resolution\n\nNone yet.\n"
            )
            previous, previous_docs = evidence.limit_ids_ever_marked, evidence.DOCS
            evidence.DOCS = root / "docs"

            def forbidden(_core):
                raise AssertionError("publish must not read git history")

            evidence.limit_ids_ever_marked = forbidden
            try:
                findings = evidence.regenerate_record_markers(records, core, "v9.9.9", False, history=False)
            finally:
                evidence.limit_ids_ever_marked, evidence.DOCS = previous, previous_docs
            self.assertEqual([], findings)
            self.assertIn("blob/v9.9.9/src/lib.rs#L1", (records / "limit-x-001.md").read_text())

    def run_cli(self, root: Path, core: Path, *args: str):
        import contextlib
        import io

        previous_docs, previous_argv = evidence.DOCS, sys.argv
        evidence.DOCS = root / "docs"
        evidence.last_touch_commit.cache_clear()
        sys.argv = ["generate", "--core", str(core), *args]
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                try:
                    code = evidence.main()
                except SystemExit as exit_:
                    code = exit_.code
        finally:
            evidence.DOCS, sys.argv = previous_docs, previous_argv
        return code, err.getvalue()

    def test_cli_publish_needs_a_ref_and_excludes_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST, git=False)
            self.placeholder_spec(root)
            code, err = self.run_cli(root, core, "--publish")
            self.assertEqual(2, code, err)
            self.assertIn("--core-ref", err)
            code, err = self.run_cli(root, core, "--publish", "--core-ref", "v9.9.9", "--check")
            self.assertEqual(2, code, err)

    def test_cli_publish_renders_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, self.RUN + self.TEST, git=False)
            spec = self.placeholder_spec(root)
            code, err = self.run_cli(root, core, "--publish", "--core-ref", "v9.9.9")
            self.assertEqual(0, code, err)
            self.assertIn("blob/v9.9.9/src/lib.rs", (spec / "example.md").read_text())


if __name__ == "__main__":
    unittest.main()
