#!/usr/bin/env python3
"""Regression tests for RFC lifecycle checks."""

import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rfc


class ScheduledDraftTests(unittest.TestCase):
    def test_open_milestoned_tracker_rejects_draft(self):
        trackers = [{
            "rfc_id": "rfc-0139",
            "number": 831,
            "title": "RFC-0139: Garbage-Collected Allocators — design settlement",
            "milestone": "v0.20.0",
            "url": "https://github.com/metel-lang/metel-core/issues/831",
        }]

        problems = rfc.scheduled_draft_problems({"rfc-0139": "draft"}, trackers)

        self.assertEqual(len(problems), 1)
        self.assertIn("still in 0-draft", problems[0])
        self.assertIn("v0.20.0", problems[0])

    def test_tracker_allows_under_review_or_later(self):
        tracker = [{
            "rfc_id": "rfc-0139",
            "number": 831,
            "title": "RFC-0139: Garbage-Collected Allocators — design settlement",
            "milestone": "v0.20.0",
            "url": "https://github.com/metel-lang/metel-core/issues/831",
        }]

        for stage in ("under-review", "accepted", "integrated", "implemented"):
            with self.subTest(stage=stage):
                self.assertEqual(
                    rfc.scheduled_draft_problems({"rfc-0139": stage}, tracker), []
                )

    def test_only_title_prefix_is_an_explicit_tracker(self):
        self.assertIsNotNone(rfc.RFC_TRACKER_TITLE_RE.match("RFC-76: settle brands"))
        self.assertIsNotNone(rfc.RFC_TRACKER_TITLE_RE.match("rfc-0067a: references"))
        self.assertIsNone(
            rfc.RFC_TRACKER_TITLE_RE.match(
                "Reject fields until lifetime anchors (RFC-0067) are implemented"
            )
        )


class MilestoneReportTests(unittest.TestCase):
    def test_report_orders_releases_and_marks_design_settlement(self):
        milestones = [
            {
                "title": "v0.17.0",
                "description": "Ownership completion.",
                "open_issues": 3,
                "closed_issues": 1,
                "html_url": "https://example.test/milestones/17",
            },
            {
                "title": "v0.14.0",
                "description": "Record finalization.",
                "open_issues": 2,
                "closed_issues": 2,
                "html_url": "https://example.test/milestones/14",
            },
        ]
        trackers = [{
            "rfc_id": "rfc-0122",
            "number": 847,
            "title": "RFC-0122: Borrow Checking — review",
            "milestone": "v0.17.0",
            "url": "https://example.test/issues/847",
            "labels": ["needs-design", "rfc-tracking"],
        }]

        report = rfc.build_milestone_report(milestones, trackers)

        self.assertLess(report.index("## v0.14.0"), report.index("## v0.17.0"))
        self.assertIn("Progress: 2/4 closed", report)
        self.assertIn("RFC-0122 #847", report)
        self.assertIn("design settlement", report)


class ImplementedCoverageGateTests(unittest.TestCase):
    """`--to implemented` must accept spec-anchored coverage (ADR-0050 §5), not
    only `options.rfc` / prose citations (ADR-0049 §1)."""

    SPEC_ID = "spec.declarations.aspects.implementing-an-aspect.legality-13"

    def _rfc_file(self, tmp, coverage_block):
        p = Path(tmp) / "rfc-9999-example.md"
        p.write_text(
            "---\n"
            "id: rfc-9999\n"
            "title: \"Example\"\n"
            "status: integrated\n"
            f"{coverage_block}"
            "---\n\n"
            "## 1. The One Rule\n\nBody.\n"
        )
        return p

    def _fixture(self, tests_dir, body):
        (Path(tests_dir) / "f.toml").write_text(body)
        (Path(tests_dir) / "f.mtl").write_text("fun main() {}\n")

    def test_spec_anchored_section_counts_as_covered(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tests:
            rfc_path = self._rfc_file(
                tmp, f'coverage:\n  "1": {{ spec: "{self.SPEC_ID}" }}\n'
            )
            self._fixture(tests, f'[options]\nspec = ["{self.SPEC_ID}"]\n')
            self.assertEqual(
                rfc.uncovered_sections_for_implemented(
                    "rfc-9999", Path(tests), rfc_path
                ),
                set(),
            )

    def test_spec_link_without_a_citing_fixture_is_uncovered(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tests:
            rfc_path = self._rfc_file(
                tmp, f'coverage:\n  "1": {{ spec: "{self.SPEC_ID}" }}\n'
            )
            self._fixture(tests, "[options]\n")  # no spec = citation
            self.assertEqual(
                rfc.uncovered_sections_for_implemented(
                    "rfc-9999", Path(tests), rfc_path
                ),
                {"1"},
            )

    def test_typed_exemption_still_counts(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tests:
            rfc_path = self._rfc_file(
                tmp,
                'coverage:\n  "1": { kind: untestable, reason: "no observable behavior" }\n',
            )
            self.assertEqual(
                rfc.uncovered_sections_for_implemented(
                    "rfc-9999", Path(tests), rfc_path
                ),
                set(),
            )


class PlannedMarkerTests(unittest.TestCase):
    """metel-core#985: stale `Planned for vX.Y.Z` callouts."""

    def test_regex_matches_only_the_planned_callout(self):
        self.assertEqual(
            rfc.PLANNED_MARKER_RE.match(
                "> **Planned for v0.16.0 (RFC-0122): shared XOR exclusive.**"
            ).group("ver"),
            "0.16.0",
        )
        self.assertIsNone(
            rfc.PLANNED_MARKER_RE.match("> **Changed in v0.13.0 (RFC-0111): ...**")
        )
        self.assertIsNone(
            rfc.PLANNED_MARKER_RE.match("> **Availability:** Since v0.13.0.")
        )

    def test_semver_orders_numerically(self):
        self.assertLess(rfc._semver("0.9.0"), rfc._semver("0.13.0"))
        self.assertLess(rfc._semver("0.13.0"), rfc._semver("0.16.0"))

    def _patch(self, tmp, dev="0.13.0", tests_dir=None):
        root = Path(tmp)
        (root / "reference" / "spec").mkdir(parents=True, exist_ok=True)
        self._orig = (rfc.REPO_ROOT, rfc.SPEC_DIR, rfc.ERROR_CODES_PATH,
                      rfc.current_dev_version, rfc.metel_core_tests_dir)
        rfc.REPO_ROOT = root
        rfc.SPEC_DIR = root / "reference" / "spec"
        rfc.ERROR_CODES_PATH = root / "reference" / "error-codes.md"
        rfc.current_dev_version = lambda: dev
        rfc.metel_core_tests_dir = lambda: tests_dir
        self.addCleanup(self._restore)

    def _restore(self):
        (rfc.REPO_ROOT, rfc.SPEC_DIR, rfc.ERROR_CODES_PATH,
         rfc.current_dev_version, rfc.metel_core_tests_dir) = self._orig

    def test_version_older_than_dev_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch(tmp)
            (Path(tmp) / "reference" / "spec" / "types.md").write_text(
                "## References\n\n"
                "> **Planned for v0.11.0 (RFC-9999): a bygone feature.**\n"
            )
            (Path(tmp) / "reference" / "error-codes.md").write_text("# Errors\n")
            problems = rfc.planned_marker_problems()
            self.assertEqual(len(problems), 1)
            self.assertIn("v0.11.0", problems[0])
            self.assertIn("older than the in-progress v0.13.0", problems[0])

    def test_current_and_future_versions_not_flagged_by_version_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch(tmp)
            (Path(tmp) / "reference" / "spec" / "types.md").write_text(
                "## A\n\n> **Planned for v0.13.0 (RFC-9999): landing now.**\n"
                "## B\n\n> **Planned for v0.16.0 (RFC-9999): later.**\n"
            )
            (Path(tmp) / "reference" / "error-codes.md").write_text("# Errors\n")
            self.assertEqual(rfc.planned_marker_problems(), [])

    def test_error_code_proof_flags_a_firing_code(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tests:
            self._patch(tmp, tests_dir=Path(tests))
            (Path(tmp) / "reference" / "spec" / "x.md").write_text("## X\n")
            (Path(tmp) / "reference" / "error-codes.md").write_text(
                "# Errors\n\n"
                "### T9999 — Example\n\n"
                "> **Planned for v0.99.0 (RFC-9999): not really.**\n\n"
                "Body.\n"
            )
            (Path(tests) / "f.toml").write_text('[expect]\ncode = "T9999"\n')
            problems = rfc.planned_marker_problems()
            self.assertTrue(
                any("T9999 is marked `Planned for`" in p for p in problems), problems
            )

    def test_styleguide_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch(tmp)
            (Path(tmp) / "reference" / "spec" / "STYLEGUIDE.md").write_text(
                "## Planned\n\n> **Planned for v0.9.0 (RFC-9999): the example.**\n"
            )
            (Path(tmp) / "reference" / "error-codes.md").write_text("# Errors\n")
            self.assertEqual(rfc.planned_marker_problems(), [])


class SpecRuleReviewStalenessTests(unittest.TestCase):
    """metel-core#1192: a Formal Rule's own `last_reviewed` checkpoint against
    its citing fixture(s), same model as metel-core#1191 for the Architecture
    Spec."""

    SPEC_ID = "spec.example.legality-1"

    def setUp(self):
        self._orig_repo_root = rfc.REPO_ROOT
        self.addCleanup(self._restore)

    def _restore(self):
        rfc.REPO_ROOT = self._orig_repo_root

    def init_git(self, core):
        subprocess.run(["git", "-C", str(core), "init", "-q"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.email", "test@example.com"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "config", "user.name", "test"], check=True, capture_output=True)

    def commit(self, core, message="commit"):
        subprocess.run(["git", "-C", str(core), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(core), "commit", "-q", "-m", message], check=True, capture_output=True)
        return self.head(core)

    def head(self, core):
        return subprocess.check_output(["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()

    def make_core(self, root, fixture_body, mtl_body="fun main() {}\n"):
        rfc.REPO_ROOT = Path(root)  # so spec_path.relative_to(REPO_ROOT) resolves
        core = Path(root) / "core"
        toml = core / "metel-interpreter/tests/integration/sources/example.toml"
        toml.parent.mkdir(parents=True)
        toml.write_text(fixture_body)
        toml.with_suffix(".mtl").write_text(mtl_body)
        self.init_git(core)
        self.commit(core, "initial")
        return core, toml

    def block(self, last_reviewed=""):
        marker = f"<!-- rfc.py:last_reviewed {last_reviewed} -->\n" if last_reviewed else ""
        return (
            "Some rule prose.\n\n" + marker
        )

    def test_no_citing_fixture_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, _ = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            self.assertIsNone(
                rfc.spec_review_staleness(
                    core, self.SPEC_ID, Path("x.md"), self.block(), []
                )
            )

    def test_missing_last_reviewed_with_a_citing_fixture_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, toml = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            problem = rfc.spec_review_staleness(
                core, self.SPEC_ID, Path(tmp) / "x.md", self.block(), [toml]
            )
            self.assertIsNotNone(problem)
            self.assertIn("no `last_reviewed` marker", problem)

    def test_reviewed_at_the_latest_touch_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, toml = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            sha = self.head(core)
            problem = rfc.spec_review_staleness(
                core, self.SPEC_ID, Path(tmp) / "x.md", self.block(sha), [toml]
            )
            self.assertIsNone(problem)

    def test_fixture_touched_after_last_reviewed_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, toml = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            old_sha = self.head(core)
            toml.with_suffix(".mtl").write_text("fun main() {\n    1;\n}\n")
            new_sha = self.commit(core, "change the fixture's .mtl")
            problem = rfc.spec_review_staleness(
                core, self.SPEC_ID, Path(tmp) / "x.md", self.block(old_sha), [toml]
            )
            self.assertIsNotNone(problem)
            self.assertIn(new_sha[:12], problem)
            self.assertIn(old_sha[:12], problem)

    def test_sidecar_only_change_is_also_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, toml = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            old_sha = self.head(core)
            toml.write_text('[options]\nspec = ["spec.example.legality-1"]\nerror = ["T9999"]\n')
            new_sha = self.commit(core, "change the sidecar only")
            problem = rfc.spec_review_staleness(
                core, self.SPEC_ID, Path(tmp) / "x.md", self.block(old_sha), [toml]
            )
            self.assertIsNotNone(problem)
            self.assertIn(new_sha[:12], problem)

    def test_unresolvable_last_reviewed_sha_is_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            core, toml = self.make_core(tmp, '[options]\nspec = ["spec.example.legality-1"]\n')
            problem = rfc.spec_review_staleness(
                core, self.SPEC_ID, Path(tmp) / "x.md", self.block("deadbeefcafe"), [toml]
            )
            self.assertIsNotNone(problem)
            self.assertIn("is not a commit reachable", problem)


class SpecBlockBodiesTests(unittest.TestCase):
    def test_splits_the_spec_corpus_into_per_block_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp)
            (spec_dir / "example.md").write_text(
                "##### Legality Rule {#spec.example.legality-1}\n\n"
                "First rule's prose.\n\n"
                "##### Dynamic Semantics {#spec.example.dynamics-1}\n\n"
                "Second rule's prose.\n"
            )
            orig_spec_dir = rfc.SPEC_DIR
            rfc.SPEC_DIR = spec_dir
            try:
                blocks = rfc.spec_block_bodies()
            finally:
                rfc.SPEC_DIR = orig_spec_dir
            self.assertIn("First rule's prose.", blocks["spec.example.legality-1"][1])
            self.assertNotIn("Second rule's prose.", blocks["spec.example.legality-1"][1])
            self.assertIn("Second rule's prose.", blocks["spec.example.dynamics-1"][1])


if __name__ == "__main__":
    unittest.main()
