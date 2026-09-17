#!/usr/bin/env python3
"""Regression tests for check_architecture.py (metel-core#1162).

Builds a synthetic minimal architecture/{spec,limitations}/ tree per test
case rather than depending on the real corpus, so these stay meaningful even
as real content changes. Each "broken" case exists because the acceptance
criteria for #1162 requires a deliberately-broken reference to produce a
reported finding, not a silent pass -- this is that requirement checked in
CI on every future change, not just a one-off manual run.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_architecture as ca

VALID_SPEC = """# Resolution {#resolution}

Intro prose.

##### Requirement {#arch.resolution.requirement-1}

Some claim.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | `metel-frontend/src/identity.rs` |
| `verified by` | `metel-frontend/src/identity/tests.rs::some_test` |
| `related` | ADR-0054 |

## Known limitations

- [`LIMIT-RESOLUTION-001`](../limitations/limit-resolution-001.md) — an example limitation.
"""

VALID_LIMITATION = """---
id: LIMIT-RESOLUTION-001
title: "Example limitation"
scope: "architecture/spec/resolution.md#resolution"
owner: metel-frontend
discovered_by: "a test"
disposition: known
review: null
---

## Limitation

Some limitation.

## Impact

Some impact.

## Affects

- `arch.resolution.requirement-1`

## Resolution

None yet.
"""


class CheckArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.spec_dir = self.tmp / "architecture" / "spec"
        self.limitations_dir = self.tmp / "architecture" / "limitations"
        self.spec_dir.mkdir(parents=True)
        self.limitations_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_corpus(self, spec_text=VALID_SPEC, limitation_text=VALID_LIMITATION):
        (self.spec_dir / "resolution.md").write_text(spec_text)
        if limitation_text is not None:
            (self.limitations_dir / "limit-resolution-001.md").write_text(limitation_text)

    def run_checks(self):
        return ca.run_checks(repo_root=self.tmp, spec_dir=self.spec_dir, limitations_dir=self.limitations_dir)

    def test_valid_corpus_has_no_findings(self):
        self.write_corpus()
        findings = self.run_checks()
        self.assertEqual([], [str(f) for f in findings])

    def test_dangling_specified_by_anchor_is_a_finding(self):
        broken = VALID_SPEC.replace("| `specified by` | `#resolution` |", "| `specified by` | `#nonexistent` |")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("does not resolve within this file" in f for f in findings), findings)

    def test_duplicate_arch_id_is_a_finding(self):
        doubled = VALID_SPEC + "\n" + VALID_SPEC
        self.write_corpus(spec_text=doubled)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("duplicate arch-* id" in f for f in findings), findings)

    def test_accepted_without_review_is_a_finding(self):
        broken = VALID_LIMITATION.replace("disposition: known", "disposition: accepted")
        self.write_corpus(limitation_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("requires a `review` date" in f for f in findings), findings)

    def test_resolved_with_placeholder_resolution_is_a_finding(self):
        broken = VALID_LIMITATION.replace("disposition: known", "disposition: resolved")
        self.write_corpus(limitation_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("real exit evidence" in f for f in findings), findings)

    def test_resolved_with_real_evidence_is_not_a_finding_for_that_rule(self):
        fixed = VALID_LIMITATION.replace("disposition: known", "disposition: resolved").replace(
            "## Resolution\n\nNone yet.\n", "## Resolution\n\nFixed by #999, verified by some_test.\n"
        )
        self.write_corpus(limitation_text=fixed)
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("real exit evidence" in f for f in findings), findings)

    def test_affects_target_that_does_not_exist_is_a_finding(self):
        broken = VALID_LIMITATION.replace(
            "- `arch.resolution.requirement-1`", "- `arch.resolution.requirement-999`"
        )
        self.write_corpus(limitation_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("does not exist" in f for f in findings), findings)

    def test_malformed_limit_id_is_a_finding(self):
        broken = VALID_LIMITATION.replace("id: LIMIT-RESOLUTION-001", "id: LIMIT-resolution-001")
        self.write_corpus(limitation_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("does not match the LIMIT-<AREA>-<NNN> shape" in f for f in findings), findings)

    def test_known_limitations_link_to_nonexistent_id_is_a_finding(self):
        broken = VALID_SPEC.replace("LIMIT-RESOLUTION-001", "LIMIT-DOES-NOT-EXIST-001")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("does not exist" in f for f in findings), findings)

    def test_missing_spec_dir_reports_one_finding_not_a_crash(self):
        shutil.rmtree(self.spec_dir)
        findings = self.run_checks()
        self.assertEqual(1, len(findings))
        self.assertIn("does not exist", str(findings[0]))


if __name__ == "__main__":
    unittest.main()
