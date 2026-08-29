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


if __name__ == "__main__":
    unittest.main()
