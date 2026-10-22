#!/usr/bin/env python3
"""Tests for check_operations.py (metel-core#1507): a synthetic workspace per case."""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_operations as co

FIELDS = ["status", "owner", "trigger", "produces", "implemented by", "verified by", "related"]


def requirement(rid="PROC-CI-001", title="A thing", status="implemented", anchor=None, values=None, extra_text=""):
    values = {"status": f"`{status}`", "owner": "ci", "trigger": "push", "produces": "a pass",
              "implemented by": "`metel-core/.github/workflows/ci.yml`", "verified by": "the job", "related": "none",
              **(values or {})}
    rows = "\n".join(f"| `{k}` | {values[k]} |" for k in FIELDS)
    return f"### {rid} — {title} {{#{anchor or rid.lower()}}}\n\n{extra_text}Statement.\n\n| Field | Value |\n|---|---|\n{rows}\n"


class Workspace(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.ws, True)
        self.docs = self.ws / "metel-docs"
        (self.docs / "operations" / "spec").mkdir(parents=True)
        self.core = self.ws / "metel-core"
        (self.core / ".github" / "workflows").mkdir(parents=True)
        (self.core / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
        self.write_spec(requirement())
        self.write_inventory("| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n")

    def write_spec(self, *reqs, page="ci.md"):
        (self.docs / "operations" / "spec" / page).write_text("# Page\n\n" + "\n".join(reqs))

    def write_inventory(self, rows):
        (self.docs / "operations" / "inventory.md").write_text(
            "# Inventory\n\n| Repository | Asset | Requirements |\n|---|---|---|\n" + rows
        )

    def run_checks(self):
        errors, warnings, skipped, count = co.run(self.docs, self.ws)
        return [str(e) for e in errors], [str(w) for w in warnings], skipped, count

    def errors(self):
        return self.run_checks()[0]


class StructureTests(Workspace):
    def test_a_valid_tree_is_clean(self):
        errors, warnings, skipped, count = self.run_checks()
        self.assertEqual(([], []), (errors, warnings))
        self.assertEqual(1, count)
        self.assertIn("metel-website", skipped)

    def test_a_malformed_heading_is_a_finding(self):
        self.write_spec("### PROC-CI-1 — short id {#proc-ci-1}\n\ntext\n")
        self.assertTrue(any("heading is not" in e for e in self.errors()), self.errors())

    def test_the_anchor_must_be_the_lowercase_id(self):
        self.write_spec(requirement(anchor="proc-ci-9"))
        self.assertTrue(any("anchor `proc-ci-9` must be `proc-ci-001`" in e for e in self.errors()))

    def test_duplicate_ids_across_pages_are_a_finding(self):
        self.write_spec(requirement())
        self.write_spec(requirement(), page="other.md")
        self.assertTrue(any("duplicate id" in e for e in self.errors()))

    def test_an_unknown_status_is_a_finding(self):
        self.write_spec(requirement(status="done"))
        self.assertTrue(any("`status` is `done`" in e for e in self.errors()))

    def test_a_missing_field_is_a_finding(self):
        text = requirement().replace("| `verified by` | the job |\n", "")
        self.write_spec(text)
        self.assertTrue(any("field table must have exactly" in e for e in self.errors()))

    def test_fields_out_of_order_are_a_finding(self):
        text = requirement()
        text = text.replace("| `owner` | ci |\n| `trigger` | push |", "| `trigger` | push |\n| `owner` | ci |")
        self.write_spec(text)
        self.assertTrue(any("field table must have exactly" in e for e in self.errors()))

    def test_an_empty_verified_by_is_a_finding(self):
        self.write_spec(requirement(values={"verified by": ""}))
        self.assertTrue(any("`verified by` is empty" in e for e in self.errors()), self.errors())

    def test_implemented_with_nothing_implementing_it_is_a_finding(self):
        self.write_spec(requirement(values={"implemented by": "none"}))
        self.assertTrue(any("`implemented by` is `none`" in e for e in self.errors()))

    def test_a_planned_requirement_must_name_its_issue(self):
        self.write_spec(requirement(status="planned", values={"implemented by": "none"}))
        self.assertTrue(any("tracking issue" in e for e in self.errors()))

    def test_a_planned_requirement_with_an_issue_in_its_text_passes(self):
        self.write_spec(requirement(status="planned", values={"implemented by": "none"},
                                    extra_text="Tracked in metel-core#692.\n\n"))
        self.assertEqual([], self.errors())

    def test_a_reference_to_a_missing_requirement_is_a_finding(self):
        (self.docs / "operations" / "index.md").write_text("See PROC-CI-099 and PROC-CI-001.\n")
        errors = self.errors()
        self.assertEqual(1, len([e for e in errors if "PROC-CI-099" in e]), errors)


class PathTests(Workspace):
    def test_a_missing_path_in_the_docs_repository_is_a_finding(self):
        self.write_spec(requirement(values={"implemented by": "`metel-docs/tools/gone.py`"}))
        self.assertTrue(any("gone.py" in e and "does not exist" in e for e in self.errors()))

    def test_a_missing_path_in_another_repository_is_a_warning(self):
        self.write_spec(requirement(values={"implemented by": "`metel-core/.github/workflows/gone.yml`"}))
        errors, warnings, _, _ = self.run_checks()
        self.assertEqual([], errors)
        self.assertTrue(any("gone.yml" in w and "does not exist" in w for w in warnings), warnings)

    def test_a_symbol_suffix_is_ignored(self):
        self.write_spec(requirement(values={"implemented by": "`metel-core/.github/workflows/ci.yml::job`"}))
        self.assertEqual([], self.errors())

    def test_a_path_in_an_unreachable_repository_is_skipped_not_failed(self):
        self.write_spec(requirement(values={"implemented by": "`metel-website/.github/workflows/deploy.yml`"}))
        errors, _, skipped, _ = self.run_checks()
        self.assertEqual([], errors)
        self.assertIn("metel-website", skipped)


class DiscoveryTests(Workspace):
    def add_core(self, rel, text="x\n"):
        f = self.core / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)

    def test_an_unlisted_asset_of_another_repository_is_a_warning(self):
        self.add_core("tools/new_tool.py")
        errors, warnings, _, _ = self.run_checks()
        self.assertEqual([], errors)
        self.assertTrue(any("metel-core/tools/new_tool.py" in w for w in warnings), warnings)

    def test_an_unlisted_asset_of_the_docs_repository_is_an_error(self):
        wf = self.docs / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "new.yml").write_text("name: n\n")
        self.assertTrue(any("metel-docs/.github/workflows/new.yml" in e for e in self.errors()))

    def test_listing_by_name_in_a_grouped_row_maps_the_asset(self):
        self.add_core(".claude/commands/start-issue.md")
        self.add_core(".claude/commands/ship-issue.md")
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n"
            "| `metel-core` | `.claude/commands/start-issue.md`, `ship-issue.md` | PROC-CI-001 |\n"
        )
        self.assertEqual(([], []), self.run_checks()[:2])

    def test_test_files_are_not_assets_of_their_own(self):
        self.add_core("tools/test_something.sh")
        self.add_core("tools/check_x.py")
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n| `metel-core` | `tools/check_x.py` | PROC-CI-001 |\n"
        )
        self.assertEqual(([], []), self.run_checks()[:2])

    def test_every_asset_kind_is_discovered(self):
        for rel in (".githooks/pre-push", ".claude/commands/c.md", "tools/t.sh", "metel-frontend/src/bin/g.rs",
                    "metel-interpreter/src/bin/m.rs", ".github/scripts/s.sh"):
            self.add_core(rel)
        found = co.discover("metel-core", self.core)
        for rel in (".githooks/pre-push", ".claude/commands/c.md", "tools/t.sh", "metel-frontend/src/bin/g.rs",
                    "metel-interpreter/src/bin/m.rs", ".github/scripts/s.sh", ".github/workflows/ci.yml"):
            self.assertIn(rel, found)

    def test_a_row_naming_a_vanished_asset_of_another_repository_is_a_warning(self):
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n| `metel-core` | `tools/vanished.py` | PROC-CI-001 |\n"
        )
        errors, warnings, _, _ = self.run_checks()
        self.assertEqual([], errors)
        self.assertTrue(any("vanished.py" in w and "does not exist" in w for w in warnings), warnings)

    def test_a_row_naming_a_vanished_asset_of_the_docs_repository_is_a_finding(self):
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n| `metel-docs` | `tools/vanished.py` | PROC-CI-001 |\n"
        )
        self.assertTrue(any("vanished.py" in e and "does not exist" in e for e in self.errors()))

    def test_a_row_without_a_requirement_or_a_local_mark_is_a_finding(self):
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n| `metel-core` | `.github/workflows/ci.yml` | nothing |\n"
        )
        self.assertTrue(any("names no requirement" in e for e in self.errors()))

    def test_a_local_row_needs_no_requirement(self):
        self.add_core("tools/aid.sh")
        self.write_inventory(
            "| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001 |\n| `metel-core` | `tools/aid.sh` | local: a manual aid |\n"
        )
        self.assertEqual(([], []), self.run_checks()[:2])

    def test_a_row_naming_a_requirement_that_does_not_exist_is_a_finding(self):
        self.write_inventory("| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-042 |\n")
        self.assertTrue(any("PROC-CI-042" in e for e in self.errors()))


class MarkerTests(Workspace):
    def test_a_process_marker_must_name_an_existing_requirement(self):
        (self.core / ".github" / "workflows" / "ci.yml").write_text("name: CI\n# Process: PROC-CI-999\n")
        self.assertTrue(any("PROC-CI-999" in e and "does not exist" in e for e in self.errors()))

    def test_a_valid_process_marker_passes(self):
        (self.core / ".github" / "workflows" / "ci.yml").write_text("name: CI\n# Process: PROC-CI-001\n")
        self.assertEqual([], self.errors())


class ReachabilityAndCliTests(Workspace):
    def test_an_embedded_docs_checkout_finds_its_core(self):
        embedded = self.ws / "embedded-core"
        (embedded / "metel-frontend").mkdir(parents=True)
        (embedded / ".gitmodules").write_text("[submodule \"docs\"]\n")
        docs = embedded / "docs"
        (docs / "operations" / "spec").mkdir(parents=True)
        repos = co.reachable_repos(self.ws / "nowhere", docs)
        self.assertEqual(embedded, repos["metel-core"])

    def run_main(self, *args):
        previous, original = sys.argv, co.DOCS_ROOT
        sys.argv = ["check_operations", "--workspace", str(self.ws), *args]
        co.DOCS_ROOT = self.docs
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = co.main()
        finally:
            sys.argv, co.DOCS_ROOT = previous, original
        return code, out.getvalue()

    def test_a_cross_repository_warning_prints_and_exits_zero_but_strict_fails(self):
        (self.core / "tools").mkdir()
        (self.core / "tools" / "new_tool.py").write_text("x\n")
        code, out = self.run_main("--check")
        self.assertEqual(0, code, out)
        self.assertIn("warning: metel-core/tools/new_tool.py", out)
        code, out = self.run_main("--strict")
        self.assertEqual(1, code, out)
        self.assertIn("1 finding(s)", out)

    def test_a_finding_fails_under_check(self):
        self.write_spec(requirement(status="done"))
        code, out = self.run_main("--check")
        self.assertEqual(1, code, out)

    def test_a_clean_run_says_so(self):
        code, out = self.run_main("--check")
        self.assertEqual(0, code, out)
        self.assertIn("No findings.", out)
        self.assertIn("metel-website", out)  # named as not reachable

    def test_the_real_tree_is_clean(self):
        # The repository this file lives in, with only itself reachable (a bare checkout).
        errors, warnings, _, count = co.run(co.DOCS_ROOT, co.DOCS_ROOT.parent / "nonexistent-workspace")
        self.assertEqual([], [str(e) for e in errors])
        self.assertGreater(count, 40)


if __name__ == "__main__":
    unittest.main()
