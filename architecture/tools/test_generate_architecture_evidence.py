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
            "| `implements exemption` | rationale: none; owner: test; review: 2030-01-01 |\n"
            "| `verification exemption` | rationale: none; owner: test; review: 2030-01-01 |\n"
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


if __name__ == "__main__":
    unittest.main()
