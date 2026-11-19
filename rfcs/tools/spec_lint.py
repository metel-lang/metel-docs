#!/usr/bin/env python3
"""Style lint for the public specification (reference/spec/*.md, error-codes.md, spec.md).

The rules enforce reference/spec/STYLEGUIDE.md and rfcs/PROCESS.md ("Public availability"):

  internal-number       an RFC, ADR, issue, PR or GAP/LIMIT record number in the public text. The marker blocks
                        (`> **Gap`, `> **Limitation`, `> **Pending`, `> **Planned for`) are the one exception:
                        they cite the record that tracks what is not yet true.
  provenance-marker     an `Availability`, `Since vX` or `Changed in vX` callout. The spec states the current
                        language; versions live in the changelog and in the versioned docs snapshots.
  long-paragraph        a prose paragraph or list item of more than MAX_PARAGRAPH_WORDS words.
  long-quote            a quote block of more than MAX_QUOTE_WORDS words.
  unlinked-normative    a paragraph that states a rule ("is an error", an error code) with no link to a rule.
  section-links-no-rule a section with rules whose prose never links one of them.

Existing violations are grandfathered by reference/spec/SPEC-LINT-BASELINE.json, a ratchet: a count above the
baseline is a problem, a count below it is a warning to shrink the baseline (a release treats that as a problem).

    python3 rfcs/tools/spec_lint.py                    # check against the baseline
    python3 rfcs/tools/spec_lint.py --write-baseline   # record the current counts
    python3 rfcs/tools/spec_lint.py --list internal-number
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = DOCS_ROOT / "reference" / "spec" / "SPEC-LINT-BASELINE.json"
SPEC_FILES = [
    "reference/spec/declarations.md",
    "reference/spec/expressions.md",
    "reference/spec/functions.md",
    "reference/spec/lexical.md",
    "reference/spec/modules.md",
    "reference/spec/runtime.md",
    "reference/spec/ownership.md",
    "reference/spec/types.md",
    "reference/error-codes.md",
    "reference/spec.md",
]
RULES = (
    "internal-number",
    "provenance-marker",
    "long-paragraph",
    "long-quote",
    "unlinked-normative",
    "section-links-no-rule",
)
MAX_PARAGRAPH_WORDS = 120
MAX_QUOTE_WORDS = 60

NUMBER_RE = re.compile(
    r"\bRFC-?\d{2,4}\b|\brfc-\d{4}\b|\bmetel-(?:core|docs)#\d+|(?<![\w&/])#\d{3,5}\b"
    r"|\b(?:GAP|LIMIT)-[A-Z]+-\d+\b|\bADR-\d+\b"
)
MARKER_START_RE = re.compile(r"^>\s*\*\*(?:Gap|Limitation|Pending|Planned for)\b")
PROVENANCE_RE = re.compile(r"\*\*(?:Availability:|Since v\d|Changed in v\d)")
RULE_HEADING_RE = re.compile(r"^#{5} (?:Legality Rule|Dynamic Semantics) \{#")
RULE_LINK_RE = re.compile(r"#spec\.[a-z0-9_.-]+\.(?:legality|dynamics)-\d+")
NORMATIVE_RE = re.compile(
    r"\b(?:is an error|are an error|is rejected|are rejected|is illegal|is a compile error|is a type error"
    r"|is a parse error|must not)\b|\b[TP]\d{4}\b"
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int
    detail: str


def _label(lines: list[str]) -> list[str]:
    """Classify each line: code, gen (generated block), rule (a rule block), head, table, quote, html, blank, text."""
    labels = ["text"] * len(lines)
    fenced = generated = in_rule = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            labels[i] = "code"
            continue
        if fenced:
            labels[i] = "code"
            continue
        if "rfc.py:fixtures:start" in stripped or "rfc.py:origins:start" in stripped:
            generated = True
        if generated:
            labels[i] = "gen"
            if "rfc.py:fixtures:end" in stripped or "rfc.py:origins:end" in stripped:
                generated = False
            continue
        if RULE_HEADING_RE.match(line):
            in_rule = True
            labels[i] = "rule"
            continue
        if in_rule:
            if "rfc.py:last_reviewed" in stripped:
                in_rule = False
                labels[i] = "rule"
                continue
            if re.match(r"^#{1,6} ", line):
                in_rule = False
            else:
                labels[i] = "rule"
                continue
        if re.match(r"^#{1,6} ", line):
            labels[i] = "head"
        elif stripped == "":
            labels[i] = "blank"
        elif stripped.startswith("|"):
            labels[i] = "table"
        elif stripped.startswith(">"):
            labels[i] = "quote"
        elif stripped.startswith("<"):
            labels[i] = "html"
    return labels


def _blocks(lines: list[str], labels: list[str], kind: str):
    """Contiguous runs of `kind` lines; a prose run also breaks at each list item, so an item is its own paragraph."""
    i = 0
    while i < len(lines):
        if labels[i] != kind:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and labels[j] == kind and not (kind == "text" and LIST_ITEM_RE.match(lines[j])):
            j += 1
        yield i, j
        i = j


def lint_text(text: str, path: str) -> list[Finding]:
    lines = text.split("\n")
    labels = _label(lines)
    found: list[Finding] = []

    # Quote blocks that are tracking markers are exempt from the number rule.
    marker_lines: set[int] = set()
    for start, end in _blocks(lines, labels, "quote"):
        if MARKER_START_RE.match(lines[start]):
            marker_lines.update(range(start, end))
    for i, line in enumerate(lines):
        if labels[i] in {"code", "gen"}:
            continue
        if i not in marker_lines:
            for match in NUMBER_RE.finditer(line):
                found.append(Finding("internal-number", path, i + 1, match.group(0)))
        for _ in PROVENANCE_RE.finditer(line):
            found.append(Finding("provenance-marker", path, i + 1, line.strip()[:70]))

    for start, end in _blocks(lines, labels, "text"):
        words = sum(len(line.split()) for line in lines[start:end])
        if words > MAX_PARAGRAPH_WORDS:
            found.append(Finding("long-paragraph", path, start + 1, f"{words} words"))
        paragraph = " ".join(lines[start:end])
        if NORMATIVE_RE.search(paragraph) and not RULE_LINK_RE.search(paragraph):
            found.append(Finding("unlinked-normative", path, start + 1, paragraph.strip()[:70]))
    for start, end in _blocks(lines, labels, "quote"):
        words = sum(len(line.lstrip("> ").split()) for line in lines[start:end])
        if words > MAX_QUOTE_WORDS:
            found.append(Finding("long-quote", path, start + 1, f"{words} words"))

    headings = [i for i, line in enumerate(lines) if re.match(r"^#{2,3} ", line)] + [len(lines)]
    for a, b in zip(headings, headings[1:]):
        rules = sum(1 for k in range(a, b) if labels[k] == "rule" and re.match(r"^#{5} ", lines[k]))
        if not rules:
            continue
        linked = any(RULE_LINK_RE.search(lines[k]) for k in range(a, b) if labels[k] in {"text", "quote", "table"})
        if not linked:
            found.append(Finding("section-links-no-rule", path, a + 1, f"{lines[a][:60]} ({rules} rules)"))
    return found


def lint_all(root: Path = DOCS_ROOT) -> list[Finding]:
    found: list[Finding] = []
    for rel in SPEC_FILES:
        path = root / rel
        if path.is_file():
            found.extend(lint_text(path.read_text(encoding="utf-8"), rel))
    return found


def counts(found: list[Finding]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for f in found:
        table.setdefault(f.path, {}).setdefault(f.rule, 0)
        table[f.path][f.rule] += 1
    return {path: dict(sorted(rules.items())) for path, rules in sorted(table.items())}


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, dict[str, int]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def check_problems(root: Path = DOCS_ROOT, baseline_path: Path | None = None) -> tuple[list[str], list[str]]:
    """(problems, warnings): a count above the baseline is a problem, one below it a warning to shrink it."""
    baseline_path = baseline_path or root / "reference" / "spec" / BASELINE_PATH.name
    found = lint_all(root)
    now = counts(found)
    baseline = load_baseline(baseline_path)
    by_key: dict[tuple[str, str], list[Finding]] = {}
    for f in found:
        by_key.setdefault((f.path, f.rule), []).append(f)
    problems: list[str] = []
    warnings: list[str] = []
    for path in sorted(set(now) | set(baseline)):
        for rule in RULES:
            have = now.get(path, {}).get(rule, 0)
            allowed = baseline.get(path, {}).get(rule, 0)
            if have > allowed:
                where = ", ".join(str(f.line) for f in by_key[(path, rule)][:6])
                problems.append(
                    f"{path}: {have} `{rule}` finding(s), the baseline allows {allowed} "
                    f"(lines {where}{', …' if have > 6 else ''}); see reference/spec/STYLEGUIDE.md"
                )
            elif have < allowed:
                warnings.append(
                    f"{path}: `{rule}` is down to {have} from {allowed} in {BASELINE_PATH.name}; "
                    "run `python3 rfcs/tools/spec_lint.py --write-baseline`"
                )
    return problems, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-baseline", action="store_true", help="record the current counts as the baseline")
    parser.add_argument("--list", metavar="RULE", choices=RULES, help="print every finding of one rule")
    args = parser.parse_args(argv)
    found = lint_all()
    if args.list:
        for f in found:
            if f.rule == args.list:
                print(f"{f.path}:{f.line}: {f.detail}")
        return 0
    if args.write_baseline:
        BASELINE_PATH.write_text(json.dumps(counts(found), indent=2) + "\n", encoding="utf-8")
        total = sum(sum(rules.values()) for rules in counts(found).values())
        print(f"wrote {BASELINE_PATH.relative_to(DOCS_ROOT)}: {total} grandfathered finding(s)")
        return 0
    problems, warnings = check_problems()
    for problem in problems:
        print(f"  - {problem}")
    for warning in warnings:
        print(f"warning: {warning}")
    print("spec-lint: no new findings." if not problems else f"spec-lint: {len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
