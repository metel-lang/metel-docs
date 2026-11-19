import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_lint


def rules(text):
    return sorted({f.rule for f in spec_lint.lint_text(text, "x.md")})


def findings(text, rule):
    return [f for f in spec_lint.lint_text(text, "x.md") if f.rule == rule]


class InternalNumbers(unittest.TestCase):
    def test_flags_rfc_issue_and_record_numbers_in_prose(self):
        text = "A field is private (RFC-0032), see metel-core#1234 and GAP-TYPES-005 and ADR-0049.\n"
        self.assertEqual([f.detail for f in findings(text, "internal-number")],
                         ["RFC-0032", "metel-core#1234", "GAP-TYPES-005", "ADR-0049"])

    def test_tracking_markers_may_cite_a_record(self):
        for marker in ("> **Gap** GAP-TYPES-005", "> **Limitation** metel-core#12", "> **Pending** metel-core#1234",
                       "> **Planned for v0.17.0 (RFC-0123).** text"):
            self.assertEqual(findings(marker + "\n", "internal-number"), [], marker)

    def test_a_marker_block_continuation_is_exempt_but_a_plain_quote_is_not(self):
        marker = "> **Pending** metel-core#1\n> continues with metel-core#2\n"
        self.assertEqual(findings(marker, "internal-number"), [])
        self.assertEqual(len(findings("> a note about RFC-0123\n", "internal-number")), 1)

    def test_code_and_generated_blocks_are_not_scanned(self):
        text = ("```metel\n// RFC-0123\n```\n<!-- rfc.py:origins:start -->\n_Referenced by: [rfc-0123](x.md)_\n"
                "<!-- rfc.py:origins:end -->\n")
        self.assertEqual(findings(text, "internal-number"), [])


class ProvenanceMarkers(unittest.TestCase):
    def test_availability_since_and_changed_in_are_flagged(self):
        for line in ("> **Availability:** Since v0.8.0.", "> **Since v0.16.0 (RFC-0219).**",
                     "> **Changed in v0.11.0: x.**", "text **Since v0.3.0** inline"):
            self.assertEqual(len(findings(line + "\n", "provenance-marker")), 1, line)

    def test_planned_markers_and_ordinary_words_are_not_flagged(self):
        for line in ("> **Planned for v0.17.0.** x", "Since the value is moved, it is gone.",
                     "The changed in behaviour"):
            self.assertEqual(findings(line + "\n", "provenance-marker"), [], line)


class Length(unittest.TestCase):
    def test_a_long_paragraph_is_flagged_and_a_long_list_is_not(self):
        long = " ".join(["word"] * 121)
        self.assertEqual(len(findings(long + "\n", "long-paragraph")), 1)
        bullets = "\n".join(f"- {' '.join(['word'] * 50)}" for _ in range(5))
        self.assertEqual(findings(bullets + "\n", "long-paragraph"), [])

    def test_a_long_quote_is_flagged(self):
        quote = "> " + " ".join(["word"] * 61)
        self.assertEqual(len(findings(quote + "\n", "long-quote")), 1)
        self.assertEqual(findings("> " + " ".join(["word"] * 60) + "\n", "long-quote"), [])


class RuleLinks(unittest.TestCase):
    RULE = ("##### Legality Rule {#spec.a.b.legality-1}\n\nA thing is an error (T0001).\n\n"
            "<!-- rfc.py:last_reviewed abc -->\n")

    def test_normative_prose_needs_a_rule_link(self):
        bare = "A private field is an error to read.\n"
        self.assertEqual(len(findings(bare, "unlinked-normative")), 1)
        linked = "A private field is [an error](#spec.a.b.legality-1) to read.\n"
        self.assertEqual(findings(linked, "unlinked-normative"), [])

    def test_a_rule_block_itself_is_not_scanned_for_normative_prose(self):
        self.assertEqual(findings("## S\n\n[r](#spec.a.b.legality-1)\n\n" + self.RULE, "unlinked-normative"), [])

    def test_a_section_with_rules_must_link_one_from_its_prose(self):
        self.assertEqual(len(findings("## Section\n\nSome prose.\n\n" + self.RULE, "section-links-no-rule")), 1)
        linked = "## Section\n\nSome [prose](#spec.a.b.legality-1).\n\n" + self.RULE
        self.assertEqual(findings(linked, "section-links-no-rule"), [])


class Baseline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "reference" / "spec").mkdir(parents=True)
        self.baseline = self.root / "baseline.json"

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, text):
        (self.root / "reference" / "spec" / "types.md").write_text(text)

    def test_a_count_above_the_baseline_is_a_problem_and_below_it_a_warning(self):
        self.write_spec("one RFC-0001 here\n")
        problems, warnings = spec_lint.check_problems(self.root, self.baseline)
        self.assertEqual(len(problems), 1)
        self.assertIn("internal-number", problems[0])
        self.baseline.write_text(json.dumps({"reference/spec/types.md": {"internal-number": 1}}))
        self.assertEqual(spec_lint.check_problems(self.root, self.baseline), ([], []))
        self.write_spec("clean\n")
        problems, warnings = spec_lint.check_problems(self.root, self.baseline)
        self.assertEqual(problems, [])
        self.assertEqual(len(warnings), 1)

    def test_the_repository_spec_has_no_unbaselined_finding(self):
        problems, _ = spec_lint.check_problems()
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
