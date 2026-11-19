#!/usr/bin/env python3
"""Tests for record.py: id assignment, overlap and contradiction signals, `new`, and `check`."""
import argparse
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record as rec


def make(rid, *, title="A limitation", summary="s", body="Some text about something.", affects=None, disposition="known",
         scope="architecture/spec/x.md#x", repros=None, tracked_by=None, rfc=None, relates=None):
    fm = {"id": rid, "title": title, "summary": summary, "scope": scope, "disposition": disposition,
          "tracked_by": tracked_by, "rfc": rfc, "relates": relates}
    r = rec.build_record(fm, body, affects or [], "None yet.", None)
    r.repros = repros or []
    return r


class IdTests(unittest.TestCase):
    def test_next_id_counts_within_the_area(self):
        rs = [make("LIMIT-TYPES-001"), make("LIMIT-TYPES-007"), make("LIMIT-OTHER-003")]
        self.assertEqual(rec.next_id("limit", "TYPES", rs), "LIMIT-TYPES-008")
        self.assertEqual(rec.next_id("limit", "NEW", rs), "LIMIT-NEW-001")
        self.assertEqual(rec.next_id("gap", "TYPES", rs), "GAP-TYPES-001")

    def test_relates_reasons_may_contain_semicolons(self):
        r = make("GAP-A-001", relates="GAP-A-002 (one; and the other); LIMIT-B-003 (separate)")
        self.assertEqual(r.relates, {"GAP-A-002": "one; and the other", "LIMIT-B-003": "separate"})


class CompareTests(unittest.TestCase):
    def sim(self, a, b):
        return rec._similarities([a], [b])[(a.id, b.id)]

    def test_unrelated_records_say_nothing(self):
        a = make("LIMIT-A-001", title="Closure environment copying", body="closures copy their captured environment on every call")
        b = make("LIMIT-B-001", title="Module path normalisation", body="root paths through submodules fail to resolve in expressions")
        self.assertEqual(rec.compare(a, b, self.sim(a, b)), [])

    def test_a_near_identical_record_is_a_blocking_duplicate(self):
        a = make("LIMIT-A-001", body="the evaluator never runs a drop implementation so only empty drop bodies are accepted")
        b = make("LIMIT-A-002", body="the evaluator never runs a drop implementation so only empty drop bodies are accepted")
        found = rec.compare(a, b, self.sim(a, b))
        self.assertTrue(any(f.blocking and "duplicate" in f.reason for f in found))

    def test_a_shared_target_with_some_text_in_common_is_an_overlap(self):
        a = make("LIMIT-A-001", affects=["spec.x.y.legality-1"], body="closures cannot name a row variable in their parameter annotation")
        b = make("LIMIT-A-002", affects=["spec.x.y.legality-1"], body="closures cannot name a row variable in their return annotation")
        found = rec.compare(a, b, self.sim(a, b))
        self.assertTrue(any(f.kind == "overlap" and not f.blocking for f in found))

    def test_a_shared_tracking_issue_is_an_overlap(self):
        a, b = make("LIMIT-A-001", tracked_by="metel-core#12"), make("LIMIT-B-001", tracked_by="metel-core#12, metel-core#13")
        self.assertTrue(any("same issue metel-core#12" in f.reason for f in rec.compare(a, b, 0.0)))

    def test_one_rfc_alone_is_not_a_signal(self):
        a, b = make("LIMIT-A-001", rfc="RFC-0001"), make("LIMIT-B-001", rfc="RFC-0001")
        self.assertEqual(rec.compare(a, b, 0.0), [])

    def test_two_active_records_expecting_different_results_for_one_target_contradict(self):
        a = make("LIMIT-A-001", affects=["spec.x.y.legality-1"], repros=[("T0002", "")])
        b = make("LIMIT-A-002", affects=["spec.x.y.legality-1"], repros=[("ok", "")])
        self.assertTrue(any(f.kind == "contradiction" and "expects T0002" in f.reason for f in rec.compare(a, b, 0.0)))

    def test_accepted_against_planned_needs_similar_text(self):
        a = make("LIMIT-A-001", affects=["arch.x.requirement-1"], disposition="accepted", body="a shared subject here")
        b = make("LIMIT-A-002", affects=["arch.x.requirement-1"], disposition="planned", body="entirely different words")
        self.assertEqual([f for f in rec.compare(a, b, 0.05) if f.kind == "contradiction"], [])
        self.assertTrue(any(f.kind == "contradiction" for f in rec.compare(a, b, 0.3)))

    def test_an_overlap_with_a_resolved_record_asks_whether_it_is_a_regression(self):
        a = make("LIMIT-A-001", tracked_by="metel-core#12")
        b = make("LIMIT-A-002", tracked_by="metel-core#12", disposition="resolved")
        self.assertTrue(any("regression" in f.reason for f in rec.compare(a, b, 0.0)))


class OwnFindingTests(unittest.TestCase):
    def test_a_limit_about_the_spec_and_a_gap_about_the_implementation_are_the_wrong_kind(self):
        limit = make("LIMIT-A-001", scope="reference/spec/types.md#x")
        gap = make("GAP-A-001", scope="architecture/spec/x.md#x")
        self.assertTrue(any(f.blocking and "is a GAP" in f.reason for f in rec.own_findings(limit)))
        self.assertTrue(any(f.blocking and "is a LIMIT" in f.reason for f in rec.own_findings(gap)))

    def test_a_reproduction_that_does_not_give_its_claimed_result_blocks(self):
        r = make("LIMIT-A-001", repros=[("T0002", "fun main() {}")])
        found = rec.own_findings(r, run_repro=lambda src: "ok")
        self.assertTrue(any(f.blocking and "gives `ok`" in f.reason for f in found))
        self.assertEqual(rec.own_findings(r, run_repro=lambda src: "T0002"), [])

    def test_a_closed_issue_a_refused_rfc_and_an_implemented_rfc_are_flagged(self):
        r = make("LIMIT-A-001", tracked_by="metel-core#9", rfc="RFC-0001, RFC-0002, RFC-0003")
        stages = {"RFC-0001": "6-refused", "RFC-0002": "4-implemented", "RFC-0003": "2-accepted"}
        found = rec.own_findings(r, resolver=lambda n: {"state": "closed"}, rfc_stage=stages.get)
        text = " ".join(f.reason for f in found)
        self.assertIn("metel-core#9, which is closed", text)
        self.assertIn("RFC-0001, which is refused", text)
        self.assertIn("RFC-0002, which is implemented", text)
        self.assertNotIn("RFC-0003", text)

    def test_an_unreachable_github_is_silent(self):
        self.assertEqual(rec.own_findings(make("LIMIT-A-001", tracked_by="metel-core#9"), resolver=lambda n: None), [])


class AuditTests(unittest.TestCase):
    def pair(self, **kw):
        a = make("LIMIT-A-001", tracked_by="metel-core#12", **kw)
        b = make("LIMIT-A-002", tracked_by="metel-core#12")
        return a, b

    def test_an_unacknowledged_pair_is_reported_and_an_acknowledgement_in_either_record_clears_it(self):
        a, b = self.pair()
        self.assertEqual(len(rec.audit([a, b])), 1)
        a2, b2 = self.pair(relates="LIMIT-A-002 (different cause)")
        self.assertEqual(rec.audit([a2, b2]), [])
        b3 = make("LIMIT-A-002", tracked_by="metel-core#12", relates="LIMIT-A-001 (different cause)")
        self.assertEqual(rec.audit([make("LIMIT-A-001", tracked_by="metel-core#12"), b3]), [])

    def test_finished_records_are_not_audited(self):
        a = make("LIMIT-A-001", tracked_by="metel-core#12", disposition="resolved")
        self.assertEqual(rec.audit([a, make("LIMIT-A-002", tracked_by="metel-core#12")]), [])


class NewTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        for d in ("limitations", "gaps"):
            (self.root / "architecture" / d).mkdir(parents=True)
        self.old = rec.DOCS
        rec.DOCS = self.root
        (self.root / "architecture" / "limitations" / "limit-types-001.md").write_text(
            '---\nid: LIMIT-TYPES-001\ntitle: "Closures cannot name a row variable"\nsummary: "A closure parameter cannot name a row variable."\n'
            'scope: "architecture/spec/x.md#x"\nowner: metel-frontend\ndiscovered_by: "t"\ndisposition: known\nreview: null\n---\n\n'
            '## Limitation\n\nA closure parameter cannot name a row variable declared by an enclosing function.\n\n## Impact\n\nx\n\n'
            '## Affects\n\n- `arch.x.requirement-1`\n\n## Resolution\n\nNone yet.\n')

    def tearDown(self):
        rec.DOCS = self.old
        self.td.cleanup()

    def run_new(self, **over):
        a = dict(kind="limit", area="TYPES", title="Something else entirely", summary="Unrelated.", description="Generics monomorphise slowly.",
                 scope="architecture/spec/x.md#x", owner="metel-frontend", discovered_by="t", disposition="known", affects=["arch.y.requirement-1"],
                 tracked_by=None, rfc=None, repro=None, repro_expect=None, relates=None, core=None, offline=True, dry_run=False)
        a.update(over)
        out = io.StringIO()
        with redirect_stdout(out):
            code = rec.cmd_new(argparse.Namespace(**a))
        return code, out.getvalue()

    def files(self):
        return sorted(p.name for p in (self.root / "architecture" / "limitations").glob("*.md"))

    def test_a_clean_record_is_numbered_and_written(self):
        code, out = self.run_new()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.files(), ["limit-types-001.md", "limit-types-002.md"])
        self.assertEqual(rec.parse_record(self.root / "architecture/limitations/limit-types-002.md").id, "LIMIT-TYPES-002")

    def test_dry_run_writes_nothing(self):
        code, out = self.run_new(dry_run=True)
        self.assertEqual((code, self.files()), (0, ["limit-types-001.md"]))
        self.assertIn("dry run", out)

    def test_an_overlap_needs_an_acknowledgement_and_the_reason_is_stored(self):
        over = dict(title="Closure annotations and enclosing rows", summary="Annotations in closures cannot refer to an enclosing function's row variable.",
                    description="A closure annotation cannot refer to a row variable declared by the enclosing function.",
                    affects=["arch.x.requirement-1"])
        code, out = self.run_new(**over)
        self.assertEqual(code, 1, out)
        self.assertIn("acknowledge each overlap", out)
        self.assertEqual(self.files(), ["limit-types-001.md"])
        code, out = self.run_new(**{**over, "relates": ["LIMIT-TYPES-001=the other is the return position"]})
        self.assertEqual(code, 0, out)
        written = rec.parse_record(self.root / "architecture/limitations/limit-types-002.md")
        self.assertEqual(written.relates, {"LIMIT-TYPES-001": "the other is the return position"})

    def test_an_acknowledgement_needs_a_reason(self):
        code, out = self.run_new(relates=["LIMIT-TYPES-001="])
        self.assertEqual(code, 2)

    def test_a_reproduction_that_contradicts_the_claim_blocks_even_when_acknowledged(self):
        src = self.root / "p.mtl"
        src.write_text("fun main() {}\n")
        old = rec.make_runner
        rec.make_runner = lambda core: (lambda source: "ok")
        try:
            code, out = self.run_new(repro=str(src), repro_expect="T0002", core=str(self.root))
        finally:
            rec.make_runner = old
        self.assertEqual(code, 1, out)
        self.assertIn("not true today", out)
        self.assertEqual(self.files(), ["limit-types-001.md"])


if __name__ == "__main__":
    unittest.main()
