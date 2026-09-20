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
| `last_reviewed` | 0123456789ab |

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-RESOLUTION-001`](../limitations/limit-resolution-001.md) — an example limitation.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
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
        self.decisions_dir = self.tmp / "architecture" / "decisions"
        self.spec_dir.mkdir(parents=True)
        self.limitations_dir.mkdir(parents=True)
        self.decisions_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_corpus(self, spec_text=VALID_SPEC, limitation_text=VALID_LIMITATION):
        (self.spec_dir / "resolution.md").write_text(spec_text)
        if limitation_text is not None:
            (self.limitations_dir / "limit-resolution-001.md").write_text(limitation_text)

    def write_adr(self, filename: str, text: str):
        (self.decisions_dir / filename).write_text(text)

    def run_checks(self):
        return ca.run_checks(
            repo_root=self.tmp,
            spec_dir=self.spec_dir,
            limitations_dir=self.limitations_dir,
            decisions_dir=self.decisions_dir,
        )

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

    def test_stale_process_narration_is_a_finding(self):
        self.write_corpus()
        (self.tmp / "architecture" / "architecture.md").write_text(
            "# Architecture\n\nThe limitation inventory runs next in the chain.\n"
        )
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("stale process narration" in f for f in findings), findings)

    def test_nonstandard_known_limitations_structure_is_a_finding(self):
        broken = VALID_SPEC.replace("### Active records", "### Open limitations")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("must use the standard inventory" in f for f in findings), findings)

    def test_resolved_record_in_active_group_is_a_finding(self):
        resolved = VALID_LIMITATION.replace("disposition: known", "disposition: resolved").replace(
            "None yet.", "Fixed by #999, verified by some_test."
        )
        self.write_corpus(limitation_text=resolved)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("Active records link" in f and "resolved" in f for f in findings), findings)

    def test_missing_last_reviewed_is_a_finding(self):
        broken = VALID_SPEC.replace("| `last_reviewed` | 0123456789ab |\n", "")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("missing or empty `last_reviewed`" in f for f in findings), findings)

    def test_malformed_last_reviewed_is_a_finding(self):
        broken = VALID_SPEC.replace("| `last_reviewed` | 0123456789ab |", "| `last_reviewed` | not-a-sha |")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("is not a 7-40 character hex commit SHA" in f for f in findings), findings)

    def test_missing_spec_dir_reports_one_finding_not_a_crash(self):
        shutil.rmtree(self.spec_dir)
        findings = self.run_checks()
        self.assertEqual(1, len(findings))
        self.assertIn("does not exist", str(findings[0]))

    def test_related_citing_a_yaml_superseded_adr_is_a_finding(self):
        self.write_adr(
            "adr-0019-old.md",
            "---\nid: adr-0019\nstatus: superseded by ADR-0029\n---\n\nOld.\n",
        )
        self.write_adr(
            "adr-0029-new.md",
            "---\nid: adr-0029\nsupersedes: adr-0019\n---\n\nNew.\n",
        )
        broken = VALID_SPEC.replace("| `related` | ADR-0054 |", "| `related` | ADR-0019 |")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("cites ADR-0019, which is superseded by ADR-0029" in f for f in findings), findings)

    def test_related_citing_a_plain_status_superseded_adr_is_a_finding(self):
        self.write_adr(
            "adr-0016-old.md",
            "# ADR-0016: Old Thing\n\n**Status:** Superseded by ADR-0028\n\nOld.\n",
        )
        broken = VALID_SPEC.replace("| `related` | ADR-0054 |", "| `related` | ADR-0016 |")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("cites ADR-0016, which is superseded by ADR-0028" in f for f in findings), findings)

    def test_related_citing_a_current_adr_is_not_a_finding(self):
        self.write_adr("adr-0054-current.md", "---\nid: adr-0054\nstatus: accepted\n---\n\nCurrent.\n")
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("is superseded" in f for f in findings), findings)

    def test_adr_with_no_frontmatter_is_a_finding(self):
        self.write_adr("adr-0001-old-style.md", "# ADR-0001: Old Style\n\n**Status:** Accepted\n")
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("no YAML frontmatter" in f for f in findings), findings)

    def test_adr_id_not_matching_filename_is_a_finding(self):
        self.write_adr(
            "adr-0002-mismatch.md",
            "---\nid: ADR-0099\ntitle: \"X\"\ndate: '2026-01-01'\nstatus: accepted\n---\n\nBody.\n",
        )
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("does not match filename" in f for f in findings), findings)

    def test_adr_missing_required_field_is_a_finding(self):
        self.write_adr(
            "adr-0003-no-date.md",
            "---\nid: adr-0003\ntitle: \"X\"\nstatus: accepted\n---\n\nBody.\n",
        )
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("missing or empty `date`" in f for f in findings), findings)

    def test_adr_unrecognized_status_is_a_finding(self):
        self.write_adr(
            "adr-0003-bad-status.md",
            "---\nid: adr-0003\ntitle: \"X\"\ndate: '2026-01-01'\nstatus: banana\n---\n\nBody.\n",
        )
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("is not one of" in f and "banana" in f for f in findings), findings)

    def test_adr_well_formed_superseded_status_is_not_a_finding(self):
        self.write_adr(
            "adr-0004-good.md",
            "---\nid: adr-0004\ntitle: \"X\"\ndate: '2026-01-01'\nstatus: superseded by ADR-0005\n---\n\nBody.\n",
        )
        self.write_corpus()
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("adr-0004-good.md" in f for f in findings), findings)

    def test_limit_discovered_by_citing_a_superseded_adr_is_exempt(self):
        # LIMIT-*'s discovered_by is historical (who originally found/documented
        # the limitation) -- citing an ADR that's since been superseded there is
        # expected, not a bug, unlike an arch-* requirement's `related` field.
        self.write_adr(
            "adr-0027-old.md",
            "---\nid: adr-0027\nstatus: superseded by adr-0039\n---\n\nOld.\n",
        )
        broken = VALID_LIMITATION.replace('discovered_by: "a test"', 'discovered_by: "ADR-0027"')
        self.write_corpus(limitation_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("is superseded" in f for f in findings), findings)


if __name__ == "__main__":
    unittest.main()
