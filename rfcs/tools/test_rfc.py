#!/usr/bin/env python3
"""Regression tests for RFC lifecycle checks."""

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


class SpecBlockBodiesTests(unittest.TestCase):
    """metel-core#1192: spec_block_bodies() isolates each rigor block's body
    span -- the region a hand-typed `last_reviewed` comment lives in, and the
    same span regenerate_backlinks_in_text carries through untouched."""

    def test_body_stops_at_origins_marker(self):
        text = (
            "##### Legality Rule {#spec.x.y.legality-1}\n\n"
            "Some prose about the rule.\n\n"
            "<!-- rfc.py:origins:start -->\n"
            "backlink\n"
            "<!-- rfc.py:origins:end -->\n"
        )
        blocks = rfc.spec_block_bodies(text)
        self.assertEqual(len(blocks), 1)
        spec_id, body = blocks[0]
        self.assertEqual(spec_id, "spec.x.y.legality-1")
        self.assertIn("Some prose about the rule.", body)
        self.assertNotIn("origins:start", body)
        self.assertNotIn("backlink", body)

    def test_body_stops_at_fixtures_marker_with_no_origins(self):
        text = (
            "##### Dynamic Semantics {#spec.x.y.dynamics-1}\n\n"
            "Prose only, no origins backlink for this one.\n\n"
            "<!-- rfc.py:fixtures:start -->\nfixture\n<!-- rfc.py:fixtures:end -->\n"
        )
        _spec_id, body = rfc.spec_block_bodies(text)[0]
        self.assertIn("Prose only, no origins backlink for this one.", body)
        self.assertNotIn("fixture", body)

    def test_hand_typed_last_reviewed_comment_stays_in_body(self):
        text = (
            "##### Legality Rule {#spec.x.y.legality-1}\n\n"
            "Prose.\n\n"
            "<!-- rfc.py:last_reviewed: 1234567890abcdef1234567890abcdef12345678 -->\n\n"
            "<!-- rfc.py:origins:start -->\nbacklink\n<!-- rfc.py:origins:end -->\n"
        )
        _spec_id, body = rfc.spec_block_bodies(text)[0]
        m = rfc.SPEC_LAST_REVIEWED_RE.search(body)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("sha"), "1234567890abcdef1234567890abcdef12345678")

    def test_two_blocks_in_one_file_are_isolated(self):
        text = (
            "##### Legality Rule {#spec.x.y.legality-1}\n\n"
            "First rule prose.\n\n"
            "<!-- rfc.py:origins:start -->\nA\n<!-- rfc.py:origins:end -->\n\n"
            "##### Dynamic Semantics {#spec.x.y.dynamics-1}\n\n"
            "Second rule prose.\n\n"
            "<!-- rfc.py:fixtures:start -->\nB\n<!-- rfc.py:fixtures:end -->\n"
        )
        blocks = rfc.spec_block_bodies(text)
        self.assertEqual([b[0] for b in blocks], ["spec.x.y.legality-1", "spec.x.y.dynamics-1"])
        self.assertIn("First rule prose.", blocks[0][1])
        self.assertNotIn("Second rule prose.", blocks[0][1])
        self.assertIn("Second rule prose.", blocks[1][1])
        self.assertNotIn("First rule prose.", blocks[1][1])

    def test_exemption_trigger_line_stays_in_body_but_rendered_block_does_not(self):
        text = (
            "##### Legality Rule {#spec.x.y.legality-1}\n\n"
            "Prose.\n\n"
            '<span class="spec-exemption-trigger" kind="blocked" ref="metel-core#1" '
            'reason="not yet"></span>\n'
            "<!-- rfc.py:exemption:rendered:start -->\nrendered\n"
            "<!-- rfc.py:exemption:rendered:end -->\n"
        )
        _spec_id, body = rfc.spec_block_bodies(text)[0]
        self.assertIn("spec-exemption-trigger", body)
        self.assertNotIn("rendered", body)


class GitHistoryHelperTests(unittest.TestCase):
    """metel-core#1192's git-history helpers, exercised against this repo's
    own real history rather than a fixture repo -- ancestry/ordering is what
    matters here, not any specific commit's content."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]

    def test_resolve_commit_accepts_head_and_rejects_garbage(self):
        sha = rfc.git_resolve_commit(self.repo_root, "HEAD")
        self.assertIsNotNone(sha)
        self.assertEqual(len(sha), 40)
        self.assertIsNone(rfc.git_resolve_commit(self.repo_root, "not-a-real-ref"))

    def test_is_ancestor_of_head_and_of_itself(self):
        head = rfc.git_resolve_commit(self.repo_root, "HEAD")
        self.assertTrue(rfc.git_is_ancestor(self.repo_root, head, head))
        parent = rfc.git_resolve_commit(self.repo_root, "HEAD~1")
        if parent:
            self.assertTrue(rfc.git_is_ancestor(self.repo_root, parent, head))
            self.assertFalse(rfc.git_is_ancestor(self.repo_root, head, parent))

    def test_most_recent_commit_of_one_is_itself(self):
        head = rfc.git_resolve_commit(self.repo_root, "HEAD")
        self.assertEqual(rfc.git_most_recent_commit(self.repo_root, [head]), head)

    def test_most_recent_commit_picks_the_descendant(self):
        head = rfc.git_resolve_commit(self.repo_root, "HEAD")
        parent = rfc.git_resolve_commit(self.repo_root, "HEAD~1")
        if parent:
            self.assertEqual(
                rfc.git_most_recent_commit(self.repo_root, [parent, head]), head
            )
            self.assertEqual(
                rfc.git_most_recent_commit(self.repo_root, [head, parent]), head
            )


if __name__ == "__main__":
    unittest.main()
