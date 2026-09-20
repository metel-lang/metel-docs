#!/usr/bin/env python3
"""Render Architecture Spec evidence from citations owned by metel-core.

``arch-implements`` belongs immediately before the Rust item that implements a
claim. ``arch-verifies`` belongs immediately before a unit test; integration
fixture sidecars use ``[options] arch_verifies``. The generated fields below
are deliberately the only implementation and verification inventories in the
Atlas: editing a rendered cell is overwritten, and ``--check`` rejects it.

``last_reviewed`` (metel-core#1191) is the opposite of those fields: a
requirement's evidence table also carries a hand-typed commit SHA, and this
script only ever *audits* it -- never writes it -- against the most recent
commit that actually touched the cited code (a line-range ``git log -L`` for
a Rust item, the whole file for a fixture citation). A field this script
could refresh for you would give no forcing function at all: accepting an
auto-regenerated diff takes no more attention than resolving a merge
conflict. ``last_reviewed`` only does its job if a person writes it by hand
after rereading the claim; the check's only role is to notice when the code
moved on since the last time someone did.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2]
ID = r"arch\.[a-z0-9.-]+\.requirement-\d+"
CITE = re.compile(r"^\s*//\s*arch-(implements|verifies):\s*\[([^]]*)\]\s*$", re.M)
IDS = re.compile(rf'"({ID})"')
ITEM = re.compile(r"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)")
REQ = re.compile(rf"^(##### Requirement \{{#({ID})\}}\n.*?)(?=^##### Requirement|\Z)", re.M | re.S)
ROW = re.compile(r"^\| `(?P<field>implements|verified by)` \|.*?\|$", re.M)
EXEMPTION = re.compile(r"^\| `(?P<field>implements exemption|verification exemption)` \| (?P<value>.*?) \|$", re.M)
LAST_REVIEWED = re.compile(r"^\| `last_reviewed` \| (?P<sha>[0-9a-f]{7,40}) \|$", re.M)


@dataclass(frozen=True)
class Citation:
    path: Path
    item: str | None
    line: int
    # Last line of the cited Rust item's own body (equal to `line` for a
    # decl-only signature), or None for a whole-file citation (a fixture
    # .toml's `arch_verifies`, which has no meaningful sub-range). Used to
    # scope the metel-core#1191 review-staleness check to exactly the text a
    # human would have read when the citation was placed -- not the whole
    # file, which would fire on every unrelated edit anywhere in it.
    end_line: int | None


def git_ref(core: Path) -> str:
    # The evidence reference is the most recent commit that changed a Rust
    # citation, rather than the checkout's incidental HEAD. This breaks the
    # otherwise circular docs-submodule pairing: updating core CI must not
    # rewrite an Atlas link when it did not change the cited source.
    ref = subprocess.check_output(
        ["git", "-C", str(core), "log", "-1", "--format=%H", "-Sarch-", "--", "*.rs"], text=True
    ).strip()
    return ref or subprocess.check_output(["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()


def following_item(text: str, start: int, test_only: bool, path: Path, line: int) -> tuple[str, int]:
    """Resolve an annotation without allowing it to silently skip an item.

    Returns the item's name and the absolute text offset its `fn` keyword
    starts at (so the caller can resolve the item's own end line).
    """
    remainder = text[start:]
    item = ITEM.search(remainder)
    if not item:
        raise ValueError(f"{path}:{line}: citation has no following Rust item")
    between = remainder[:item.start()]
    if test_only and "#[test]" not in between:
        raise ValueError(f"{path}:{line}: arch-verifies must precede a #[test] function")
    return item.group(1), start + item.start()


def _skip_string_or_comment(text: str, i: int) -> int | None:
    """If `text[i:]` opens a string/char literal or a comment, return the
    index just past it; otherwise None. Not a real Rust lexer (raw strings,
    byte strings, and nested block comments aren't handled) -- good enough to
    keep brace-matching below from miscounting `{`/`}` inside a string or
    comment, which is the only thing that would actually break it."""
    if text.startswith('"', i):
        j = i + 1
        while j < len(text) and text[j] != '"':
            j += 2 if text[j] == "\\" else 1
        return j + 1
    if text.startswith("//", i):
        j = text.find("\n", i)
        return len(text) if j == -1 else j
    if text.startswith("/*", i):
        j = text.find("*/", i + 2)
        return len(text) if j == -1 else j + 2
    if text.startswith("'", i):
        # A char literal ('x', '\n', '\'', ...) closes within a few chars;
        # a lifetime ('a, 'static) does not. Braces never appear in either,
        # so on ambiguity it's safe to just not skip (leave `'` as an
        # ordinary character) rather than risk skipping too far.
        j = i + 1
        if j < len(text) and text[j] == "\\":
            j += 1
        j += 1
        return j + 1 if j < len(text) and text[j] == "'" else None
    return None


def function_extent(text: str, fn_start: int) -> tuple[int, int]:
    """The (start_line, end_line) 1-indexed lines an item beginning at
    `fn_start` (the index of its `fn` keyword) spans: through its matching
    closing brace, or just its own line for a decl-only signature (a trait
    method with no body, ending in `;` before any `{`). This is what
    metel-core#1191's review-staleness check diffs against -- deliberately
    the item's signature-and-body only, not its leading doc comments (a
    comment-only edit shouldn't force a re-review) and not its callees (see
    ADR discussion: tracking the call graph trades a crisp, unambiguous
    boundary for one with no principled stopping depth)."""
    start_line = text.count("\n", 0, fn_start) + 1
    i = fn_start
    depth = 0
    brace_seen = False
    while i < len(text):
        skip = _skip_string_or_comment(text, i)
        if skip is not None:
            i = skip
            continue
        c = text[i]
        if c == ";" and not brace_seen:
            return start_line, start_line
        if c == "{":
            depth += 1
            brace_seen = True
        elif c == "}":
            depth -= 1
            if brace_seen and depth == 0:
                return start_line, text.count("\n", 0, i) + 1
        i += 1
    raise ValueError(f"unterminated item starting at line {start_line}")


def citations(core: Path):
    found = defaultdict(lambda: {"implements": [], "verifies": []})
    for path in core.rglob("*.rs"):
        if any(part in {"target", ".git"} for part in path.parts):
            continue
        text = path.read_text(errors="ignore")
        for match in CITE.finditer(text):
            kind = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            claim_ids = IDS.findall(match.group(2))
            if not claim_ids:
                raise ValueError(f"{path}:{line}: citation contains no well-formed arch claim")
            item, item_start = following_item(text, match.end(), kind == "verifies", path, line)
            _, end_line = function_extent(text, item_start)
            rel = path.relative_to(core)
            citation = Citation(rel, item, line, end_line)
            for claim in claim_ids:
                found[claim][kind].append(citation)
    for path in core.rglob("*.toml"):
        if "tests" not in path.parts:
            continue
        try:
            data = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError:
            continue
        values = data.get("options", {}).get("arch_verifies", [])
        for claim in values:
            if re.fullmatch(ID, claim):
                found[claim]["verifies"].append(Citation(path.relative_to(core), None, 1, None))
    return found


def last_touch_commit(core: Path, citation: Citation) -> str:
    """The most recent commit that changed the text a citation actually
    points at: a line range for a Rust item, or the whole file for a
    fixture .toml citation (which has no meaningful sub-range to scope to).
    Requires full history (`git log`'s default shallow-unfriendly walk) --
    see the fetch-depth: 0 note on the CI job that runs this."""
    if citation.end_line is None:
        scope = ["--", str(citation.path)]
    else:
        scope = ["-L", f"{citation.line},{citation.end_line}:{citation.path}"]
    out = subprocess.check_output(
        ["git", "-C", str(core), "log", "-1", "--format=%H", *scope], text=True
    )
    sha = out.split("\n", 1)[0].strip()
    if not sha:
        raise ValueError(f"{citation.path}: no commit history found for the cited range")
    return sha


def is_ancestor(core: Path, maybe_ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(core), "merge-base", "--is-ancestor", maybe_ancestor, descendant],
        capture_output=True,
    )
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise ValueError(
        f"git merge-base --is-ancestor {maybe_ancestor} {descendant} failed: "
        f"{result.stderr.decode(errors='replace').strip()}"
    )


def most_recent_commit(core: Path, shas: list[str]) -> str:
    """Reduce commits from possibly-several citations for one claim to the
    single most recent, by pairwise ancestry -- valid here because this
    repo's history is linear per branch, so any two of these are always
    comparable."""
    newest = shas[0]
    for candidate in shas[1:]:
        if is_ancestor(core, newest, candidate):
            newest = candidate
    return newest


def resolve_commit(core: Path, ref: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(core), "rev-parse", "--verify", f"{ref}^{{commit}}"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def render(values, core_ref):
    result = []
    for value in sorted(set(values), key=lambda v: (str(v.path), v.item or "", v.line)):
        label = f"`{value.path}" + (f"::{value.item}`" if value.item else "`")
        target = f"https://github.com/metel-lang/metel-core/blob/{core_ref}/{value.path}#L{value.line}"
        result.append(f"[{label}]({target})")
    return "; ".join(result)


def valid_exemption(value):
    return bool(re.search(r"\brationale:\s*\S", value) and re.search(r"\bowner:\s*\S", value)
                and re.search(r"\breview:\s*\d{4}-\d{2}-\d{2}\b", value))


def review_staleness(core: Path, path: Path, claim: str, block: str, values) -> str | None:
    """metel-core#1191: flag a claim whose cited code moved on since a human
    last reviewed it. `last_reviewed` is deliberately hand-typed, never
    auto-written here the way `implements`/`verified by` are -- a field the
    generator could refresh for you gives no forcing function at all,
    since accepting its diff takes no more attention than a merge
    conflict. This function only ever reports staleness; nothing in this
    module writes to `last_reviewed`."""
    reviewed = LAST_REVIEWED.search(block)
    if not reviewed:
        return f"{path.relative_to(DOCS)}: `{claim}` is missing a `last_reviewed` field (metel-core#1191)"
    all_citations = values["implements"] + values["verifies"]
    if not all_citations:
        return None  # fully exempt; nothing to compare `last_reviewed` against
    reviewed_sha = resolve_commit(core, reviewed.group("sha"))
    if reviewed_sha is None:
        return (
            f"{path.relative_to(DOCS)}: `{claim}`'s `last_reviewed` "
            f"(`{reviewed.group('sha')}`) is not a commit reachable in metel-core"
        )
    code_touch = most_recent_commit(core, [last_touch_commit(core, c) for c in all_citations])
    if not is_ancestor(core, code_touch, reviewed_sha):
        return (
            f"{path.relative_to(DOCS)}: `{claim}`'s cited code was touched by {code_touch[:12]} "
            f"after `last_reviewed` ({reviewed_sha[:12]}) -- confirm the claim still holds and "
            f"bump `last_reviewed`"
        )
    return None


def regenerate(spec_dir: Path, core: Path, evidence, check: bool, core_ref: str):
    stale, known = [], set()
    for path in spec_dir.glob("*.md"):
        text = path.read_text()
        changed = text
        for match in list(REQ.finditer(text)):
            block, claim = match.groups()
            known.add(claim)
            values = evidence.get(claim, {"implements": [], "verifies": []})
            exemptions = {m.group("field"): m.group("value") for m in EXEMPTION.finditer(block)}
            for kind, field in (("implements", "implements exemption"), ("verifies", "verification exemption")):
                if values[kind] and field in exemptions:
                    stale.append(f"{path.relative_to(DOCS)}: `{claim}` has evidence and `{field}`")
                elif not values[kind] and not valid_exemption(exemptions.get(field, "")):
                    stale.append(f"{path.relative_to(DOCS)}: `{claim}` lacks arch-{kind} evidence or valid `{field}`")
            finding = review_staleness(core, path, claim, block, values)
            if finding:
                stale.append(finding)
            def replace(row):
                field = row.group("field")
                key = "implements" if field == "implements" else "verifies"
                value = render(values[key], core_ref) if values[key] else "_Exempt; see exemption below._"
                return f"| `{field}` | {value} |"
            new_block = ROW.sub(replace, block)
            if new_block != block:
                changed = changed.replace(block, new_block)
        if changed != text and not check:
            path.write_text(changed)
        if changed != text and check:
            stale.append(f"{path.relative_to(DOCS)}: generated evidence is stale")
    for claim in sorted(evidence):
        if claim not in known:
            stale.append(f"metel-core: citation targets unknown Architecture Spec claim `{claim}`")
    return stale


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--core-ref", help="immutable metel-core commit used in generated web links")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        findings = regenerate(
            DOCS / "architecture/spec", args.core, citations(args.core), args.check, args.core_ref or git_ref(args.core)
        )
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        findings = [str(error)]
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
