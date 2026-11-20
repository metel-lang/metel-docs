#!/usr/bin/env python3
"""Tests for check_keywords.py."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_keywords as ck

PEST = 'keyword = @{\n    ("fun" | "let" // note\n     | "where")\n    ~ !(ASCII_ALPHANUMERIC | "_")\n}\n'


def lexical(words):
    return f"# Lexical\n\n## Keywords\n\n```\n{' '.join(words)}\n```\n\ntext\n"


class KeywordCheck(unittest.TestCase):
    def test_parser_keywords_skip_lookahead_and_comments(self):
        self.assertEqual(ck.parser_keywords(PEST), {"fun", "let", "where"})

    def test_matching_lists_have_no_problems(self):
        self.assertEqual(ck.problems(PEST, lexical(["where", "fun", "let"])), [])

    def test_missing_and_extra_words_are_reported(self):
        out = ck.problems(PEST, lexical(["fun", "let", "bogus"]))
        self.assertEqual(len(out), 2)
        self.assertTrue(any("reserves `where`" in m for m in out))
        self.assertTrue(any("lists `bogus`" in m for m in out))

    def test_missing_rule_or_block_is_an_error(self):
        with self.assertRaises(ValueError):
            ck.parser_keywords("other = { }")
        with self.assertRaises(ValueError):
            ck.spec_keywords("# no keywords here")


if __name__ == "__main__":
    unittest.main()
