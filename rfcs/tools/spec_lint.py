#!/usr/bin/env python3
"""Style lint for the public specification (reference/spec/*.md, error-codes.md, spec.md).

The rules enforce reference/spec/STYLEGUIDE.md and rfcs/PROCESS.md ("Public availability"):

  internal-number       an RFC, ADR, issue, PR or GAP/LIMIT record number in the public text. The marker blocks
                        (`> **Gap`, `> **Limitation`, `> **Pending`, `> **Planned for`) are the one exception:
                        they cite the record that tracks what is not yet true.
  provenance-marker     an `Availability`, `Available in`, `Since` or `Changed in` callout, or a sentence saying
                        which version added or changed something. The spec states the current language; versions
                        live in the changelog and in the versioned docs snapshots.
  long-paragraph        a prose paragraph or list item of more than MAX_PARAGRAPH_WORDS words.
  long-quote            a quote block of more than MAX_QUOTE_WORDS words.
  unlinked-normative    a paragraph that states a rule ("is an error", an error code) with no link to a rule.
  section-links-no-rule a section with rules whose prose never links one of them.
  limit-in-prose        a limit stated in prose ("not yet", "planned", "in this release", "under review") instead of
                        a `Gap`, `Limitation` or `Pending` marker that cites the record tracking it.
  allow-invalid         a malformed or useless `spec-lint: allow` comment (below).

A finding that is right is accepted in one of two ways. The baseline grandfathers what predates a rule. A single
justified exception is written next to the text, on the line before the paragraph, quote or heading it covers (for a
rule block, right after the rule's `last_reviewed` line, where rfc.py keeps it):

    <!-- spec-lint: allow RULE reason="why this is correct" -->

The reason is required, RULE must be a rule above, and an allow that covers nothing is itself a finding, so
exceptions cannot rot. `--allows` lists every one.

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
    "limit-in-prose",
    "allow-invalid",
)
MAX_PARAGRAPH_WORDS = 120
MAX_QUOTE_WORDS = 60

NUMBER_RE = re.compile(
    r"\bRFC-?\d{2,4}\b|\brfc-\d{4}\b|\bmetel-(?:core|docs)#\d+|(?<![\w&/])#\d{3,5}\b"
    r"|\b(?:GAP|LIMIT)-[A-Z]+-\d+\b|\bADR-\d+\b"
)
MARKER_START_RE = re.compile(r"^>\s*\*\*(?:Gap|Limitation|Pending|Planned for)\b")
PROVENANCE_RE = re.compile(
    r"\*\*(?:Availability:|Since\b|Changed in\b|Available in\b)"
    r"|\b(?:[Ss]ince|[Aa]vailable in|[Cc]hanged in|[Aa]dded in|[Ii]ntroduced in) v\d+\.\d+"
)
RULE_HEADING_RE = re.compile(r"^#{5} (?:Legality Rule|Dynamic Semantics) \{#")
RULE_LINK_RE = re.compile(r"#spec\.[a-z0-9_.-]+\.(?:legality|dynamics)-\d+")
NORMATIVE_RE = re.compile(
    r"\b(?:is an error|are an error|is rejected|are rejected|is illegal|is a compile error|is a type error"
    r"|is a parse error|must not)\b|\b[TP]\d{4}\b"
)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
LIMIT_PHRASE_RE = re.compile(
    r"\bnot yet\b|\bdeferred (?:to|pending|until)\b|\bnot supported\b|\bplanned, not implemented\b"
    r"|\b(?:is|are) (?:only )?planned\b|\bnot (?:yet )?implemented\b|\bfuture release\b"
    r"|\bnot part of this release\b|\bdoes not (?:yet )?exist\b|\bin this release\b|\bunder review\b"
    r"|\bplanned extension\b|\bstage note\b|\bonce [\w`' -]{0,40}(?:lands|ships)\b",
    re.IGNORECASE,
)
PENDING_MARKER_RE = re.compile(r"^>\s*\*\*Pending\*\*")
ALLOW_RE = re.compile(r'^<!--\s*spec-lint:\s*allow\s+(?P<rule>[\w-]+)\s+reason="(?P<reason>[^"]*)"\s*-->\s*$')
MIN_REASON_CHARS = 8


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int
    detail: str


@dataclass(frozen=True)
class Allow:
    rule: str
    path: str
    line: int
    reason: str


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
    return lint_text_with_allows(text, path)[0]


def _pending_excused(lines: list[str]) -> set[int]:
    """0-based lines of the prose a `> **Pending**` marker excuses: its own block and the one before it."""
    blocks: list[tuple[int, int]] = []
    start = None
    for i, line in enumerate(lines + [""]):
        if line.strip():
            start = i if start is None else start
        elif start is not None:
            blocks.append((start, i - 1))
            start = None
    excused: set[int] = set()
    for index, (first, last) in enumerate(blocks):
        if any(PENDING_MARKER_RE.match(lines[i]) for i in range(first, last + 1)):
            for a, b in ([blocks[index - 1]] if index else []) + [(first, last)]:
                excused.update(range(a, b + 1))
    return excused


def _allows(lines: list[str], labels: list[str], path: str) -> tuple[list[Allow], list[Finding], dict[Allow, range]]:
    """The `spec-lint: allow` comments, the findings for bad ones, and the lines each one covers (1-based)."""
    allows: list[Allow] = []
    bad: list[Finding] = []
    covers: dict[Allow, range] = {}
    for i, line in enumerate(lines):
        if labels[i] != "html" or "spec-lint:" not in line:
            continue
        match = ALLOW_RE.match(line.strip())
        if not match:
            bad.append(Finding("allow-invalid", path, i + 1, "expected <!-- spec-lint: allow RULE reason=\"…\" -->"))
            continue
        rule, reason = match.group("rule"), match.group("reason").strip()
        if rule not in RULES or rule == "allow-invalid":
            bad.append(Finding("allow-invalid", path, i + 1, f"unknown rule `{rule}`"))
            continue
        if len(reason) < MIN_REASON_CHARS:
            bad.append(Finding("allow-invalid", path, i + 1, "the reason is missing or too short to review"))
            continue
        before = next((k for k in range(i - 1, -1, -1) if lines[k].strip()), None)
        if before is not None and "rfc.py:last_reviewed" in lines[before]:
            # The canonical spot for a rule: right after its `last_reviewed` line, where rfc.py keeps it.
            head = next((k for k in range(before, -1, -1) if RULE_HEADING_RE.match(lines[k])), None)
            if head is None:
                bad.append(Finding("allow-invalid", path, i + 1, "no rule block above the comment"))
                continue
            allow = Allow(rule, path, i + 1, reason)
            allows.append(allow)
            covers[allow] = range(head + 1, before + 2)
            continue
        first = next((k for k in range(i + 1, len(lines)) if lines[k].strip() and "spec-lint:" not in lines[k]), None)
        if first is None:
            bad.append(Finding("allow-invalid", path, i + 1, "nothing follows the comment"))
            continue
        last = first
        if RULE_HEADING_RE.match(lines[first]):
            while last + 1 < len(lines) and labels[last + 1] == "rule":
                last += 1
        else:
            while last + 1 < len(lines) and lines[last + 1].strip():
                last += 1
        allow = Allow(rule, path, i + 1, reason)
        allows.append(allow)
        covers[allow] = range(first + 1, last + 2)
    return allows, bad, covers


EXEMPTION_REF_RE = re.compile(r'(\bref=")[^"]*(")')
EXEMPTION_BLOCKED_ON_RE = re.compile(r"(— blocked on )metel-(?:core|docs)#\d+")


def _without_exemption_ref(line: str) -> str:
    """A fixture-coverage exemption cites the issue that blocks it in `ref="..."`, and the generated
    "blocked on <issue>" line repeats it. That citation is a tracking marker by design, like a `Gap`
    marker, so it is not an internal number; the `reason` text beside it still is."""
    if "rfc.py:exemption " in line:
        return EXEMPTION_REF_RE.sub(r"\1\2", line)
    if "Exempt from fixture coverage" in line:
        return EXEMPTION_BLOCKED_ON_RE.sub(r"\1", line)
    return line


def lint_text_with_allows(text: str, path: str) -> tuple[list[Finding], list[Allow]]:
    lines = text.split("\n")
    labels = _label(lines)
    found: list[Finding] = []

    # Quote blocks that are tracking markers are exempt from the number rule.
    # A marker inside a rule block is labelled "rule", not "quote", so find markers by their opening
    # line rather than by block label, and take the quote lines that continue them.
    marker_lines: set[int] = set()
    for i, line in enumerate(lines):
        if labels[i] in {"code", "gen"} or not MARKER_START_RE.match(line):
            continue
        j = i
        while j < len(lines) and lines[j].startswith(">"):
            marker_lines.add(j)
            j += 1
    for i, line in enumerate(lines):
        if labels[i] in {"code", "gen"}:
            continue
        if i not in marker_lines:
            for match in NUMBER_RE.finditer(_without_exemption_ref(line)):
                found.append(Finding("internal-number", path, i + 1, match.group(0)))
        if PROVENANCE_RE.search(line):
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

    excused = _pending_excused(lines)
    for i, line in enumerate(lines):
        if labels[i] not in {"text", "quote", "rule"} or i in marker_lines or i in excused:
            continue
        if line.lstrip().startswith("<") or line.startswith("#"):
            continue
        match = LIMIT_PHRASE_RE.search(line)
        if match:
            found.append(Finding("limit-in-prose", path, i + 1, match.group(0)))

    headings = [i for i, line in enumerate(lines) if re.match(r"^#{2,3} ", line)] + [len(lines)]
    for a, b in zip(headings, headings[1:]):
        rules = sum(1 for k in range(a, b) if labels[k] == "rule" and re.match(r"^#{5} ", lines[k]))
        if not rules:
            continue
        linked = any(RULE_LINK_RE.search(lines[k]) for k in range(a, b) if labels[k] in {"text", "quote", "table"})
        if not linked:
            found.append(Finding("section-links-no-rule", path, a + 1, f"{lines[a][:60]} ({rules} rules)"))

    allows, bad, covers = _allows(lines, labels, path)
    used: set[Allow] = set()
    kept: list[Finding] = []
    for f in found:
        owner = next((al for al in allows if al.rule == f.rule and f.line in covers[al]), None)
        if owner:
            used.add(owner)
        else:
            kept.append(f)
    for allow in allows:
        if allow not in used:
            bad.append(Finding("allow-invalid", path, allow.line, f"the `{allow.rule}` allow covers no finding"))
    return kept + bad, allows


def lint_all(root: Path = DOCS_ROOT) -> list[Finding]:
    found: list[Finding] = []
    for rel in SPEC_FILES:
        path = root / rel
        if path.is_file():
            found.extend(lint_text(path.read_text(encoding="utf-8"), rel))
    return found


def all_allows(root: Path = DOCS_ROOT) -> list[Allow]:
    found: list[Allow] = []
    for rel in SPEC_FILES:
        path = root / rel
        if path.is_file():
            found.extend(lint_text_with_allows(path.read_text(encoding="utf-8"), rel)[1])
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
    parser.add_argument("--allows", action="store_true", help="print every `spec-lint: allow` comment with its reason")
    args = parser.parse_args(argv)
    if args.allows:
        for allow in all_allows():
            print(f"{allow.path}:{allow.line}: {allow.rule}: {allow.reason}")
        return 0
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
