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

<!-- records:limitations -->
"""

VALID_LIMITATION = """---
id: LIMIT-RESOLUTION-001
title: "Example limitation"
summary: "An example limitation."
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


class ArchitectureCorpusCase(unittest.TestCase):
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

    def run_checks(self, **kwargs):
        # The synthetic corpora do not cite their gaps; the citation rule has its own tests.
        kwargs.setdefault("require_gap_citations", False)
        return ca.run_checks(
            repo_root=self.tmp,
            spec_dir=self.spec_dir,
            limitations_dir=self.limitations_dir,
            decisions_dir=self.decisions_dir,
            gaps_dir=self.tmp / "architecture" / "gaps",
            language_spec_dir=self.tmp / "reference" / "spec",
            rfcs_dir=self.tmp / "rfcs",
            **kwargs,
        )


class CheckArchitectureTests(ArchitectureCorpusCase):
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

    def test_stale_process_narration_is_a_finding(self):
        self.write_corpus()
        (self.tmp / "architecture" / "architecture.md").write_text(
            "# Architecture\n\nThe limitation inventory runs next in the chain.\n"
        )
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("stale process narration" in f for f in findings), findings)

    def test_known_limitations_must_hold_only_the_marker(self):
        broken = VALID_SPEC.replace("<!-- records:limitations -->", "- a hand-written list item")
        self.write_corpus(spec_text=broken)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("must hold only the `<!-- records:limitations -->` marker" in f for f in findings), findings)

    def test_record_summary_is_required(self):
        self.write_corpus(limitation_text=VALID_LIMITATION.replace('summary: "An example limitation."\n', ""))
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("missing or empty frontmatter field `summary`" in f for f in findings), findings)

    def test_overlong_summary_is_a_finding(self):
        long = VALID_LIMITATION.replace("An example limitation.", "x" * (ca.SUMMARY_MAX_LENGTH + 1))
        self.write_corpus(limitation_text=long)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("keep it to one line" in f for f in findings), findings)

    def test_record_whose_scope_page_lacks_the_marker_is_a_finding(self):
        page = VALID_SPEC[: VALID_SPEC.index("## Known limitations")]
        self.write_corpus(spec_text=page)
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("never renders" in f for f in findings), findings)

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

    def write_page(self, name: str, text: str):
        (self.tmp / "architecture" / name).write_text(text)

    def test_link_to_a_missing_file_is_a_finding(self):
        self.write_corpus()
        self.write_page("overview.md", "See [the index](spec/index.md).\n")
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("points at a file that does not exist" in f and "spec/index.md" in f for f in findings), findings)

    def test_link_to_a_missing_anchor_is_a_finding(self):
        self.write_corpus()
        self.write_page("overview.md", "See [x](spec/resolution.md#no-such-anchor).\n")
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("points at an anchor that does not exist" in f for f in findings), findings)

    def test_valid_links_are_not_findings(self):
        self.write_corpus()
        self.write_page(
            "overview.md",
            "# Overview {#overview}\n\nSee [claim](spec/resolution.md#arch.resolution.requirement-1), "
            "[section](spec/resolution.md#resolution), [heading](spec/resolution.md#known-limitations), "
            "[here](#overview), [ext](https://example.com/x#y), and ```[fenced](nope.md)```.\n",
        )
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("does not exist" in f and "overview" in f for f in findings), findings)

    def test_published_page_linking_an_unpublished_adr_is_a_finding(self):
        self.write_corpus()
        self.write_adr("adr-0054-x.md", "---\nid: adr-0054\ntitle: \"X\"\ndate: '2026-01-01'\nstatus: accepted\n---\n\nBody.\n")
        self.write_page("overview.md", "See [the ADR](decisions/adr-0054-x.md).\n")
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("targets an unpublished source" in f for f in findings), findings)

    def test_an_unpublished_page_may_link_other_unpublished_pages(self):
        self.write_corpus()
        self.write_adr("adr-0001-a.md", "---\nid: adr-0001\ntitle: \"A\"\ndate: '2026-01-01'\nstatus: accepted\n---\n\nSee [b](adr-0002-b.md).\n")
        self.write_adr("adr-0002-b.md", "---\nid: adr-0002\ntitle: \"B\"\ndate: '2026-01-01'\nstatus: accepted\n---\n\nBody.\n")
        findings = [str(f) for f in self.run_checks()]
        self.assertFalse(any("unpublished" in f for f in findings), findings)

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


LANGUAGE_SPEC = """# Types

##### Legality Rule {#spec.types.generics.legality-1}

A rule.
"""

VALID_GAP = """---
id: GAP-TYPES-001
title: "Function parameters are monotypes"
summary: "A one-line summary."
scope: "reference/spec/types.md#spec.types.generics.legality-1"
owner: language
discovered_by: "a test"
disposition: known
review: null
---

## Gap

Some gap.

## Impact

Some impact.

## Affects

- `spec.types.generics.legality-1`

## Resolution

None yet.
"""


class HealthPageTests(ArchitectureCorpusCase):
    def test_health_page_needs_its_marker(self):
        self.write_corpus()
        (self.tmp / "status").mkdir(exist_ok=True)
        (self.tmp / "status" / "architecture-health.md").write_text("# Architecture Health\n")
        findings = [str(f) for f in self.run_checks()]
        self.assertTrue(any("health:architecture" in f for f in findings), findings)

    def test_health_page_with_its_marker_passes(self):
        self.write_corpus()
        (self.tmp / "status").mkdir(exist_ok=True)
        (self.tmp / "status" / "architecture-health.md").write_text("# Architecture Health\n\n<!-- health:architecture -->\n")
        self.assertEqual([], [str(f) for f in self.run_checks()])


class GapRecordTests(ArchitectureCorpusCase):
    """ADR-0057 `GAP-*` records (architecture/gaps/), validated by the same
    checker as `LIMIT-*` with Language-Spec-specific rules."""

    def write_gap_corpus(self, gap_text=VALID_GAP, gap_name="gap-types-001.md", limitation_text=None):
        self.write_corpus(limitation_text=limitation_text if limitation_text is not None else VALID_LIMITATION)
        (self.tmp / "reference" / "spec").mkdir(parents=True, exist_ok=True)
        (self.tmp / "reference" / "spec" / "types.md").write_text(LANGUAGE_SPEC + self.known_gaps_for(gap_text))
        gaps = self.tmp / "architecture" / "gaps"
        gaps.mkdir(parents=True, exist_ok=True)
        (gaps / gap_name).write_text(gap_text)

    @staticmethod
    def known_gaps_for(gap_text):
        """The chapter's `## Known gaps` section: only the records marker."""
        return "\n## Known gaps\n\n" + ca.GAPS_MARKER + "\n"

    def write_rfc(self, stage, number="0122"):
        d = self.tmp / "rfcs" / stage
        d.mkdir(parents=True, exist_ok=True)
        (d / f"rfc-{number}-x.md").write_text("# rfc\n")

    def findings(self):
        return [str(f) for f in self.run_checks()]

    def test_valid_gap_has_no_findings(self):
        self.write_gap_corpus()
        self.assertEqual([], self.findings())

    def test_unknown_area_is_a_finding(self):
        text = VALID_GAP.replace("GAP-TYPES-001", "GAP-WIDGETS-001")
        self.write_gap_corpus(gap_text=text, gap_name="gap-widgets-001.md")
        self.assertTrue(any("does not match the GAP-<AREA>-<NNN> shape" in f for f in self.findings()))

    def test_scope_outside_language_spec_is_a_finding(self):
        text = VALID_GAP.replace("reference/spec/types.md#spec.types.generics.legality-1", "architecture/spec/resolution.md#resolution")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("must point into `reference/spec/`" in f for f in self.findings()))

    def test_area_must_match_scope_chapter(self):
        text = VALID_GAP.replace("GAP-TYPES-001", "GAP-FUNCTIONS-001")
        self.write_gap_corpus(gap_text=text, gap_name="gap-functions-001.md")
        self.assertTrue(any("does not match the chapter" in f for f in self.findings()))

    def test_dangling_scope_anchor_is_a_finding(self):
        text = VALID_GAP.replace("legality-1\"", "legality-9\"")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("does not resolve to a real file+anchor" in f for f in self.findings()))

    def test_affects_unknown_spec_rule_is_a_finding(self):
        text = VALID_GAP.replace("- `spec.types.generics.legality-1`", "- `spec.types.generics.legality-9`")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("spec rule `spec.types.generics.legality-9` does not exist" in f for f in self.findings()))

    def test_affects_needs_a_spec_rule_or_rfc(self):
        text = VALID_GAP.replace("- `spec.types.generics.legality-1`", "- `arch.resolution.requirement-1`")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("at least one Language Spec rule" in f for f in self.findings()))

    def test_affects_missing_rfc_is_a_finding(self):
        text = VALID_GAP.replace("- `spec.types.generics.legality-1`", "- `spec.types.generics.legality-1`\n- `RFC-0122`")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("RFC `RFC-0122` does not exist" in f for f in self.findings()))

    def test_resolved_needs_a_landed_rfc(self):
        text = VALID_GAP.replace("disposition: known", "disposition: resolved").replace(
            "- `spec.types.generics.legality-1`", "- `spec.types.generics.legality-1`\n- `RFC-0122`"
        ).replace("None yet.", "Landed via the RFC.")
        self.write_rfc("1-under-review")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("requires an `affects` RFC at stage 3-integrated or 4-implemented" in f for f in self.findings()))

    def test_resolved_with_landed_rfc_passes(self):
        text = VALID_GAP.replace("disposition: known", "disposition: resolved").replace(
            "- `spec.types.generics.legality-1`", "- `spec.types.generics.legality-1`\n- `RFC-0122`"
        ).replace("None yet.", "Landed via the RFC.")
        self.write_rfc("3-integrated")
        self.write_gap_corpus(gap_text=text)
        self.assertEqual([], self.findings())

    def test_planned_needs_an_rfc_or_issue(self):
        text = VALID_GAP.replace("disposition: known", "disposition: planned")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("`planned` requires an RFC" in f for f in self.findings()))
        ok = text.replace("None yet.", "Tracked as #239.")
        self.write_gap_corpus(gap_text=ok)
        self.assertEqual([], self.findings())

    def test_accepted_needs_an_accepting_reference(self):
        text = VALID_GAP.replace("disposition: known", "disposition: accepted").replace("review: null", "review: 2027-01-01")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("requires an accepting ADR, RFC or issue" in f for f in self.findings()))
        ok = text.replace("None yet.", "Accepted per ADR-0057.")
        self.write_gap_corpus(gap_text=ok)
        self.assertEqual([], self.findings())

    def _linked_gap(self):
        return VALID_GAP.replace("- `spec.types.generics.legality-1`", "- `spec.types.generics.legality-1`\n- `LIMIT-RESOLUTION-001`")

    def test_gap_limit_link_must_be_reciprocal(self):
        self.write_gap_corpus(gap_text=self._linked_gap())
        self.assertTrue(any("`LIMIT-RESOLUTION-001` does not link back to `GAP-TYPES-001`" in f for f in self.findings()))

    def test_limit_gap_link_must_be_reciprocal(self):
        limit = VALID_LIMITATION.replace("- `arch.resolution.requirement-1`", "- `arch.resolution.requirement-1`\n- `GAP-TYPES-001`")
        self.write_gap_corpus(limitation_text=limit)
        self.assertTrue(any("`GAP-TYPES-001` does not link back to `LIMIT-RESOLUTION-001`" in f for f in self.findings()))

    def test_limitation_may_cite_a_language_spec_rule(self):
        limit = VALID_LIMITATION.replace("- `arch.resolution.requirement-1`", "- `arch.resolution.requirement-1`\n- `spec.types.generics.legality-1`")
        self.write_gap_corpus(limitation_text=limit)
        self.assertEqual([], self.findings())

    def test_limitation_citing_a_missing_spec_rule_is_a_finding(self):
        limit = VALID_LIMITATION.replace("- `arch.resolution.requirement-1`", "- `arch.resolution.requirement-1`\n- `spec.types.generics.legality-9`")
        self.write_gap_corpus(limitation_text=limit)
        self.assertTrue(any("spec rule `spec.types.generics.legality-9` does not exist" in f for f in self.findings()))

    def test_reciprocal_gap_limit_link_passes(self):
        limit = VALID_LIMITATION.replace("- `arch.resolution.requirement-1`", "- `arch.resolution.requirement-1`\n- `GAP-TYPES-001`")
        self.write_gap_corpus(gap_text=self._linked_gap(), limitation_text=limit)
        self.assertEqual([], self.findings())

    def test_duplicate_gap_id_is_a_finding(self):
        self.write_gap_corpus()
        (self.tmp / "architecture" / "gaps" / "gap-types-002.md").write_text(VALID_GAP)
        f = self.findings()
        self.assertTrue(any("duplicate GAP-* id" in x for x in f), f)

    def _types_md(self, section):
        (self.tmp / "reference" / "spec" / "types.md").write_text(LANGUAGE_SPEC + section)

    def test_missing_known_gaps_section_is_a_finding(self):
        self.write_gap_corpus()
        self._types_md("")
        self.assertTrue(any("missing `## Known gaps` section" in f for f in self.findings()))

    def test_known_gaps_must_hold_only_the_marker(self):
        self.write_gap_corpus()
        self._types_md("\n## Known gaps\n\n- `GAP-TYPES-001` — a hand-written entry\n")
        self.assertTrue(any("must hold only the `<!-- records:gaps -->` marker" in f for f in self.findings()))

    def test_known_gaps_marker_alone_passes_even_with_no_active_records(self):
        self.write_gap_corpus(gap_text=VALID_GAP.replace("disposition: known", "disposition: superseded"))
        self.assertEqual([], self.findings())


if __name__ == "__main__":
    unittest.main()


class SpecLimitMarkerTests(GapRecordTests):
    """`> **Gap** ID` / `> **Limitation** ID` markers in Language Spec chapters, and the
    optional `planned_for` / `rfc` scheduling fields on records (metel-core#1235)."""

    def chapter_with(self, marker_line):
        (self.tmp / "reference" / "spec" / "types.md").write_text(
            LANGUAGE_SPEC + "\n" + marker_line + "\n" + self.known_gaps_for(VALID_GAP)
        )

    def marker_findings(self, **kwargs):
        return [str(f) for f in self.run_checks(**kwargs)]

    def test_marker_for_an_active_gap_passes(self):
        self.write_gap_corpus()
        self.chapter_with("> **Gap** GAP-TYPES-001: a one-line boundary.")
        self.assertEqual([], self.marker_findings(require_gap_citations=True))

    def test_marker_for_missing_record_is_a_finding(self):
        self.write_gap_corpus()
        self.chapter_with("> **Gap** GAP-TYPES-009")
        self.assertTrue(any("GAP-TYPES-009" in f and "does not exist" in f for f in self.marker_findings()))

    def test_marker_label_must_match_the_record_kind(self):
        self.write_gap_corpus()
        self.chapter_with("> **Limitation** GAP-TYPES-001")
        self.assertTrue(any("use `Gap`" in f for f in self.marker_findings()))

    def test_marker_for_resolved_record_is_a_finding(self):
        resolved = VALID_GAP.replace("disposition: known", "disposition: superseded")
        self.write_gap_corpus(gap_text=resolved)
        self.chapter_with("> **Gap** GAP-TYPES-001")
        self.assertTrue(any("only active records are cited" in f for f in self.marker_findings()))

    def test_gap_may_be_cited_from_another_chapter_but_must_be_cited_in_its_own(self):
        self.write_gap_corpus()
        (self.tmp / "reference" / "spec" / "functions.md").write_text(LANGUAGE_SPEC + "\n> **Gap** GAP-TYPES-001\n")
        findings = self.marker_findings(require_gap_citations=True)
        self.assertFalse(any("does not exist" in f or "own chapter" in f for f in findings), findings)
        self.assertTrue(any("is not cited by" in f for f in findings), findings)

    def test_uncited_active_gap_is_flagged_only_when_required(self):
        self.write_gap_corpus()
        self.assertEqual([], self.marker_findings(require_gap_citations=False))
        self.assertTrue(any("is not cited by" in f for f in self.marker_findings(require_gap_citations=True)))

    def test_limitation_marker_cites_an_active_limit_record(self):
        self.write_gap_corpus()
        self.chapter_with("> **Gap** GAP-TYPES-001\n\n> **Limitation** LIMIT-RESOLUTION-001")
        self.assertEqual([], self.marker_findings(require_gap_citations=True))

    def test_marker_inside_a_code_fence_is_ignored(self):
        self.write_gap_corpus()
        self.chapter_with("```\n> **Gap** GAP-TYPES-009\n```")
        self.assertEqual([], self.marker_findings(require_gap_citations=False))

    def test_planned_for_must_be_a_release(self):
        text = VALID_GAP.replace("review: null", "planned_for: soon\nreview: null")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("must be a release" in f for f in self.marker_findings()))

    def test_valid_schedule_fields_pass(self):
        self.write_rfc("2-accepted", "0122")
        text = VALID_GAP.replace("review: null", "planned_for: v0.16.0\nrfc: RFC-0122\nreview: null")
        self.write_gap_corpus(gap_text=text)
        self.assertEqual([], self.marker_findings())

    def test_rfc_field_must_exist(self):
        text = VALID_GAP.replace("review: null", "rfc: RFC-0999\nreview: null")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("RFC-0999" in f and "does not exist" in f for f in self.marker_findings()))

    def test_schedule_fields_are_rejected_on_a_finished_record(self):
        text = VALID_GAP.replace("disposition: known", "disposition: superseded").replace("review: null", "planned_for: v0.16.0\nreview: null")
        self.write_gap_corpus(gap_text=text)
        self.assertTrue(any("remove them from a resolved or superseded record" in f for f in self.marker_findings()))


class LimitPhrasingLintTests(unittest.TestCase):
    """Warn-only lint for limits stated in prose instead of a marker (metel-core#1235)."""

    def lint(self, text):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root, True)
        spec = root / "reference" / "spec"
        spec.mkdir(parents=True)
        (spec / "types.md").write_text(text)
        return [str(w) for w in ca.lint_limit_phrasing(spec, root)]

    def test_prose_limit_is_flagged_with_its_line(self):
        warnings = self.lint("# T\n\nNamed records are planned, not implemented.\n")
        self.assertEqual(1, len(warnings))
        self.assertIn("types.md:3", warnings[0])

    def test_marker_and_since_notes_are_not_flagged(self):
        self.assertEqual([], self.lint("> **Gap** GAP-TYPES-001\n> **Limitation** LIMIT-X-001: not yet built.\n> **Since v0.13.0:** not yet.\n"))

    def test_code_fences_html_and_generated_exemptions_are_not_flagged(self):
        text = (
            "```\nnot yet\n```\n"
            "<span class=\"rigor-backlink\">_Exempt from fixture coverage: not implemented._</span>\n"
            "<!-- doc-example: expect-fail reason=\"not yet\" -->\n"
        )
        self.assertEqual([], self.lint(text))

    def test_lint_never_fails_the_check(self):
        # Warnings are separate from findings: run_checks does not include them.
        self.assertFalse(hasattr(ca, "lint_limit_phrasing") and "lint_limit_phrasing" in ca.run_checks.__code__.co_names)
