import importlib.util
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
    def make_core(self, root: Path, rust: str, fixture: str = "") -> Path:
        core = root / "core"
        (core / "src").mkdir(parents=True)
        (core / "src/lib.rs").write_text(rust)
        if fixture:
            sidecar = core / "tests/integration/sources/example.toml"
            sidecar.parent.mkdir(parents=True)
            sidecar.write_text(fixture)
        return core

    def make_spec(self, root: Path, extra: str = "") -> Path:
        spec = root / "docs/architecture/spec"
        spec.mkdir(parents=True)
        (spec / "example.md").write_text(
            "##### Requirement {#arch.example.requirement-1}\n\n"
            "Claim.\n\n| Field | Value |\n|---|---|\n"
            "| `implements` | old path |\n| `verified by` | old test |\n" + extra
        )
        return spec

    def test_scans_unit_and_fixture_citations_and_regenerates_cells(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-implements: [\"arch.example.requirement-1\"]\npub fn run() {}\n\n// arch-verifies: [\"arch.example.requirement-1\"]\n#[test]\nfn run_is_tested() {}\n", "[options]\narch_verifies = [\"arch.example.requirement-1\"]\n")
            spec = self.make_spec(root)
            previous = evidence.DOCS
            evidence.DOCS = root / "docs"
            try:
                findings = evidence.regenerate(spec, evidence.citations(core), False, "a" * 40)
            finally:
                evidence.DOCS = previous
            self.assertEqual([], findings)
            text = (spec / "example.md").read_text()
            self.assertIn("src/lib.rs::run", text)
            self.assertIn("src/lib.rs::run_is_tested", text)
            self.assertIn("tests/integration/sources/example.toml", text)
            self.assertIn("/blob/" + "a" * 40, text)

    def test_missing_evidence_requires_a_structured_exemption(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "pub fn run() {}\n")
            spec = self.make_spec(root)
            previous = evidence.DOCS
            evidence.DOCS = root / "docs"
            try:
                findings = evidence.regenerate(spec, evidence.citations(core), True, "a" * 40)
            finally:
                evidence.DOCS = previous
            self.assertTrue(any("lacks arch-implements" in finding for finding in findings))
            self.assertTrue(any("lacks arch-verifies" in finding for finding in findings))

    def test_verification_citation_must_bind_a_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = self.make_core(root, "// arch-verifies: [\"arch.example.requirement-1\"]\npub fn run() {}\n")
            with self.assertRaisesRegex(ValueError, "#\\[test\\]"):
                evidence.citations(core)


if __name__ == "__main__":
    unittest.main()
