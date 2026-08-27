#!/usr/bin/env python3
"""Regression tests for RFC lifecycle checks."""

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


if __name__ == "__main__":
    unittest.main()
