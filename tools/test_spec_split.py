#!/usr/bin/env python3
"""Tests for specindex.py and spec_split.py on a toy docs tree."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_split
import specindex

CHAPTER = """# Chapter

Intro with [a rule](#spec.chapter.b.legality-1) and [an error](../error-codes.md#t1).

## Alpha

Alpha text, see [beta](#spec.chapter.b.legality-1) and [the sub](#alpha-sub).

### Alpha sub {#alpha-sub}

Sub text.

##### Legality Rule {#spec.chapter.a.legality-1}

Rule A, see [beta](#spec.chapter.b.legality-1).

<!-- rfc.py:last_reviewed abc -->

## Beta

##### Legality Rule {#spec.chapter.b.legality-1}

Rule B.

<!-- rfc.py:last_reviewed abc -->

## Known gaps

<!-- records:gaps -->
"""

PLAN = """source = "reference/spec/chapter.md"

[[page]]
file = "index.md"
sections = ["Known gaps"]

[[page]]
file = "alpha.md"
sections = ["Alpha"]

[[page]]
file = "beta.md"
sections = ["Beta"]
"""


class Tree(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name).resolve()
        spec = self.root / "reference" / "spec"
        spec.mkdir(parents=True)
        (spec / "chapter.md").write_text(CHAPTER)
        (spec / "other.md").write_text("# Other\n\nSee [rule A](chapter.md#spec.chapter.a.legality-1), [chapter](chapter.md), [site](/docs/x) and [gone](missing.md).\n")
        (self.root / "reference" / "error-codes.md").write_text("# Errors\n\n### T1 {#t1}\n")
        (self.root / "rfcs").mkdir()
        (self.root / "rfcs" / "r.md").write_text("[sub](../reference/spec/chapter.md#alpha-sub)\n")
        (self.root / "architecture" / "gaps").mkdir(parents=True)
        (self.root / "architecture" / "gaps" / "g.md").write_text('---\nscope: "reference/spec/chapter.md#spec.chapter.b.legality-1"\n---\n')
        self.plan = self.root / "plan.toml"
        self.plan.write_text(PLAN)
        self.old = spec_split.DOCS
        spec_split.DOCS = self.root

    def tearDown(self):
        spec_split.DOCS = self.old
        self.td.cleanup()

    def read(self, rel):
        return (self.root / rel).read_text()


class IndexTests(Tree):
    def test_pages_chapters_and_anchors_are_found_whatever_the_layout(self):
        before = specindex.anchors(self.root)
        self.assertEqual(specindex.chapter_of(self.root / "reference/spec/chapter.md", self.root), "chapter")
        spec_split.apply(self.plan, False)
        self.assertEqual(specindex.chapter_of(self.root / "reference/spec/chapter/alpha.md", self.root), "chapter")
        after = specindex.anchors(self.root)
        self.assertEqual(set(before), set(after))
        self.assertEqual(after["spec.chapter.b.legality-1"], "reference/spec/chapter/beta.md")
        self.assertEqual(specindex.page_for(self.root, "spec.chapter.a.legality-1"), "chapter/alpha.md")
        self.assertEqual(specindex.duplicates(self.root), {})


class SplitTests(Tree):
    def setUp(self):
        super().setUp()
        spec_split.apply(self.plan, False)

    def test_the_chapter_file_becomes_a_directory_of_pages(self):
        self.assertFalse((self.root / "reference/spec/chapter.md").exists())
        for name in ("index", "alpha", "beta"):
            self.assertTrue((self.root / f"reference/spec/chapter/{name}.md").is_file(), name)

    def test_headings_are_relevelled_and_rule_headings_are_not(self):
        alpha = self.read("reference/spec/chapter/alpha.md")
        self.assertIn("# Alpha\n", alpha)
        self.assertIn("## Alpha sub {#alpha-sub}", alpha)
        self.assertIn("##### Legality Rule {#spec.chapter.a.legality-1}", alpha)
        self.assertTrue(alpha.startswith("---\nsidebar_position: 2\n---\n"))

    def test_the_index_keeps_the_introduction_and_the_known_gaps_section(self):
        index = self.read("reference/spec/chapter/index.md")
        self.assertIn("# Chapter", index)
        self.assertIn("## Known gaps", index)

    def test_links_within_the_chapter_follow_their_fragment_to_its_page(self):
        index = self.read("reference/spec/chapter/index.md")
        self.assertIn("(beta.md#spec.chapter.b.legality-1)", index)
        alpha = self.read("reference/spec/chapter/alpha.md")
        self.assertIn("(beta.md#spec.chapter.b.legality-1)", alpha)
        self.assertIn("(#alpha-sub)", alpha)  # same page: stays a bare fragment

    def test_links_out_of_a_moved_page_are_recomputed_for_the_new_depth(self):
        self.assertIn("(../../error-codes.md#t1)", self.read("reference/spec/chapter/index.md"))

    def test_links_into_the_old_file_from_elsewhere_are_followed(self):
        other = self.read("reference/spec/other.md")
        self.assertIn("(chapter/alpha.md#spec.chapter.a.legality-1)", other)
        self.assertIn("(chapter/index.md)", other)
        self.assertIn("(../reference/spec/chapter/alpha.md#alpha-sub)", self.read("rfcs/r.md"))

    def test_site_routes_and_already_dangling_links_are_left_alone(self):
        other = self.read("reference/spec/other.md")
        self.assertIn("(/docs/x)", other)
        self.assertIn("(missing.md)", other)

    def test_a_bare_path_in_frontmatter_names_the_new_page(self):
        self.assertIn('scope: "reference/spec/chapter/beta.md#spec.chapter.b.legality-1"', self.read("architecture/gaps/g.md"))

    def test_no_link_is_broken_by_the_split(self):
        self.assertEqual([p for p in spec_split.check_links(self.root) if "missing.md" not in p], [])


class RepairTests(Tree):
    def test_slugs_match_github_slugger_so_a_punctuation_gap_keeps_its_hyphens(self):
        self.assertEqual(specindex.slug("The ? Operator"), "the--operator")
        self.assertEqual(specindex.slug("`dyn Aspect` and more {#x}"), "dyn-aspect-and-more")
        self.assertEqual(specindex.slug("Open rows"), "open-rows")

    def test_fix_links_follows_a_link_that_still_names_a_chapter_that_became_a_directory(self):
        spec_split.apply(self.plan, False)
        (self.root / "release-notes").mkdir()
        (self.root / "release-notes" / "changelog.md").write_text(
            "See [beta](../reference/spec/chapter.md#spec.chapter.b.legality-1) and [chapter](../reference/spec/chapter.md#nope).\n")
        spec_split.fix_links(self.root, False)
        body = (self.root / "release-notes" / "changelog.md").read_text()
        self.assertIn("(../reference/spec/chapter/beta.md#spec.chapter.b.legality-1)", body)
        self.assertIn("(../reference/spec/chapter/index.md#nope)", body)  # unknown fragment: the chapter's index

    def test_release_notes_are_relinked_by_apply_too(self):
        (self.root / "release-notes").mkdir()
        (self.root / "release-notes" / "changelog.md").write_text("[a](../reference/spec/chapter.md#spec.chapter.a.legality-1)\n")
        spec_split.apply(self.plan, False)
        self.assertIn("(../reference/spec/chapter/alpha.md#spec.chapter.a.legality-1)", (self.root / "release-notes" / "changelog.md").read_text())


class PlanTests(Tree):
    def test_an_unplaced_section_is_an_error(self):
        self.plan.write_text(PLAN.replace('[[page]]\nfile = "beta.md"\nsections = ["Beta"]\n', ""))
        with self.assertRaises(SystemExit) as cm:
            spec_split.apply(self.plan, False)
        self.assertIn("Beta", str(cm.exception))
        self.assertTrue((self.root / "reference/spec/chapter.md").exists())

    def test_a_section_placed_twice_is_an_error(self):
        self.plan.write_text(PLAN + '\n[[page]]\nfile = "again.md"\nsections = ["Beta"]\n')
        with self.assertRaises(SystemExit):
            spec_split.apply(self.plan, False)

    def test_own_places_a_section_without_its_subsections(self):
        self.plan.write_text('source = "reference/spec/chapter.md"\n[[page]]\nfile = "index.md"\nsections = ["Known gaps"]\n'
                             '[[page]]\nfile = "alpha/index.md"\nsections = ["Alpha:own"]\n'
                             '[[page]]\nfile = "alpha/sub.md"\nsections = ["Alpha sub"]\n[[page]]\nfile = "beta.md"\nsections = ["Beta"]\n')
        spec_split.apply(self.plan, False)
        self.assertNotIn("Sub text", self.read("reference/spec/chapter/alpha/index.md"))
        self.assertIn("Sub text", self.read("reference/spec/chapter/alpha/sub.md"))

    def test_dry_run_writes_nothing(self):
        spec_split.apply(self.plan, True)
        self.assertTrue((self.root / "reference/spec/chapter.md").exists())
        self.assertFalse((self.root / "reference/spec/chapter").exists())

    def test_check_links_finds_a_missing_anchor(self):
        (self.root / "rfcs" / "r.md").write_text("[x](../reference/spec/chapter.md#nope)\n")
        self.assertTrue(any("no such anchor" in p for p in spec_split.check_links(self.root)))


if __name__ == "__main__":
    unittest.main()
