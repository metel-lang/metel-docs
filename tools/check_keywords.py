#!/usr/bin/env python3
"""Check that the keyword list in reference/spec/lexical.md matches the parser.

The parser's reserved words are the `keyword` rule of metel-frontend/src/grammar.pest.
The spec lists them in the fenced block under `## Keywords` of lexical.md. The two must
name the same words: a word the parser reserves and the spec omits is an undocumented
reservation, and a word the spec lists that the parser does not reserve is a false claim.

grammar.pest lives in metel-core. Inside metel-core it is found at ../metel-frontend/src/grammar.pest;
elsewhere pass --grammar (CI fetches it from metel-core `develop`). Without it the check is skipped
unless --require is given.

    python3 tools/check_keywords.py [--grammar PATH] [--require]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parent.parent
LEXICAL = DOCS_ROOT / "reference" / "spec" / "lexical.md"
DEFAULT_GRAMMAR = DOCS_ROOT.parent / "metel-frontend" / "src" / "grammar.pest"


def parser_keywords(pest: str) -> set[str]:
    m = re.search(r"^keyword\s*=\s*@\{(.*?)\n\}", pest, re.S | re.M)
    if not m:
        raise ValueError("no `keyword = @{ ... }` rule found in grammar.pest")
    # Only the alternation: the rule ends with a `~ !(ASCII_ALPHANUMERIC | "_")` word-boundary lookahead.
    alternation = re.sub(r"//.*", "", m.group(1)).split("~")[0]
    return set(re.findall(r'"([A-Za-z_]+)"', alternation))


def spec_keywords(lexical: str) -> set[str]:
    m = re.search(r"^## Keywords\s*\n+```[^\n]*\n(.*?)^```", lexical, re.S | re.M)
    if not m:
        raise ValueError("no fenced block under `## Keywords` in lexical.md")
    return set(m.group(1).split())


def problems(pest: str, lexical: str) -> list[str]:
    parser, spec = parser_keywords(pest), spec_keywords(lexical)
    out = [f"the parser reserves `{w}` but lexical.md's keyword list omits it" for w in sorted(parser - spec)]
    out += [f"lexical.md lists `{w}` as a keyword but the parser's keyword rule does not reserve it" for w in sorted(spec - parser)]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grammar", type=Path, help="path to metel-frontend/src/grammar.pest")
    ap.add_argument("--require", action="store_true", help="fail instead of skipping when grammar.pest is unavailable")
    args = ap.parse_args(argv)
    grammar = args.grammar or DEFAULT_GRAMMAR
    if not grammar.is_file():
        msg = f"keyword check: {grammar} not available"
        if args.require:
            print(msg + " (--require)", file=sys.stderr)
            return 1
        print(msg + "; skipped (pass --grammar, or run inside metel-core)")
        return 0
    found = problems(grammar.read_text(), LEXICAL.read_text())
    if found:
        print(f"lexical.md keyword list has drifted from the parser ({len(found)}):", file=sys.stderr)
        for p in found:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"keyword check: lexical.md lists the parser's {len(parser_keywords(grammar.read_text()))} keywords")
    return 0


if __name__ == "__main__":
    sys.exit(main())
