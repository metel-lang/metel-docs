#!/usr/bin/env python3
"""Render Architecture Spec evidence from citations owned by metel-core.

``arch-implements`` belongs immediately before the Rust item (or, in a
``.pest`` file, the grammar rule) that implements a claim. ``arch-verifies``
belongs immediately before a unit test; integration fixture sidecars use
``[options] arch_verifies``. A ``#[ignore]``d test or a fixture with
``skip = ...`` never runs, so citing one is an error, not evidence. The
generated fields below are deliberately the only implementation and
verification inventories in the Atlas: editing a rendered cell is
overwritten, and ``--check`` rejects it.

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

A claim with no evidence for one side carries an ``implements exemption`` /
``verification exemption`` row instead (metel-core#1193), in rfc.py's ``kind``
vocabulary: ``kind: untestable; reason: ...; owner: ...`` (permanent),
``kind: elsewhere; ref: <path or claim id>; reason: ...; owner: ...``, or
``kind: blocked; ref: <RFC id or repo#N>; reason: ...; owner: ...; review:
YYYY-MM-DD`` (temporary: CI fails once the review date passes or the ref
resolves). Evidence and an exemption on the same side are mutually exclusive.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
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
ATTRIBUTE = re.compile(r"#!?\[.*?\]", re.S)
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
PEST_RULE = re.compile(r"^[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*[@_$!]?\{", re.M)
REQ = re.compile(rf"^(##### Requirement \{{#({ID})\}}\n.*?)(?=^##### Requirement|\Z)", re.M | re.S)
ROW = re.compile(r"^\| `(?P<field>implements|verified by)` \|.*?\|$", re.M)
EXEMPTION = re.compile(r"^\| `(?P<field>implements exemption|verification exemption)` \| (?P<value>.*?) \|$", re.M)
LAST_REVIEWED = re.compile(r"^\| `last_reviewed` \| (?P<sha>[0-9a-f]{7,40}) \|$", re.M)


@dataclass(frozen=True)
class Citation:
    path: Path
    item: str | None
    line: int
    # The cited item's own extent: `start_line` is its `fn`/rule line (not the
    # marker's, which is `line`) and `end_line` its last line (equal to
    # `start_line` for a decl-only signature). Both are None for a whole-file
    # citation (a fixture .toml's `arch_verifies`, which has no meaningful
    # sub-range). Used to scope the metel-core#1191 review-staleness check to
    # exactly the item a human read -- not the whole file, which would fire on
    # every unrelated edit, and not the marker lines above the item, where
    # touching a *sibling* claim's marker would otherwise flag this claim.
    start_line: int | None
    end_line: int | None


def git_ref(core: Path) -> str:
    # The evidence reference is the most recent commit that changed a citation
    # marker (arch-implements/arch-verifies or, since metel-core#1247, limit:),
    # rather than the checkout's incidental HEAD. This breaks the otherwise
    # circular docs-submodule pairing: updating core CI must not rewrite an
    # Atlas link when it did not change the cited source.
    #
    # This is a proxy, not a guarantee: it catches a commit that changed a
    # marker's own occurrence count, not one that shifted a cited item's line
    # number some other way (inserting an unrelated line above it, including
    # one kind of marker while pickaxing for the other). The two calls this
    # function's caller makes both scan *current* file content for line
    # numbers, so a ref this heuristic gets wrong is a wrong line number, not
    # a missing citation -- `--check` catches that the next time this runs
    # against an unchanged core, the same way any other staleness is caught.
    ref = subprocess.check_output(
        [
            "git", "-C", str(core), "log", "-1", "--format=%H", "--pickaxe-regex", "-S", "arch-|limit:",
            "--", "*.rs", "*.pest",
        ],
        text=True,
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
    # Only comments and attributes may sit between the marker and its item;
    # anything else means the marker is attached to something it does not
    # precede (a struct, an impl header, a stray statement) and would
    # otherwise silently latch onto whatever `fn` happens to come next.
    leftover = ATTRIBUTE.sub("", COMMENT.sub("", between)).strip()
    if leftover:
        raise ValueError(
            f"{path}:{line}: citation must directly precede its item; found `{leftover.splitlines()[0]}` in between"
        )
    if test_only and "#[test]" not in between:
        raise ValueError(f"{path}:{line}: arch-verifies must precede a #[test] function")
    if test_only and re.search(r"#\[ignore\b", between):
        raise ValueError(
            f"{path}:{line}: arch-verifies cites an #[ignore]d test; an ignored test never runs "
            f"and cannot verify a claim"
        )
    return item.group(1), start + item.start()


def following_rule(text: str, start: int, path: Path, line: int) -> tuple[str, int]:
    """The `.pest` counterpart of `following_item`: a marker must sit
    directly above a grammar rule (only blank/comment lines in between)."""
    rule = PEST_RULE.search(text, start)
    if not rule:
        raise ValueError(f"{path}:{line}: citation has no following grammar rule")
    for between in text[start:rule.start()].splitlines():
        if between.strip() and not between.strip().startswith("//"):
            raise ValueError(f"{path}:{line}: arch-implements must directly precede a grammar rule")
    return rule.group(1), rule.start(1)


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


# A `LIMIT-*`/`GAP-*` record's `## Affects` may cite code directly, by name, with no
# marker in metel-core (metel-core#1236 level 2 -- level 3, below, is a code-side
# `// limit:` marker instead): `path::symbol`. Resolved the same way a `.pest` rule or
# a Rust item is elsewhere in this file, just by searching for the name instead of
# following a marker.
ITEM_KEYWORDS = ("fn", "static", "const", "struct", "enum", "trait")
AFFECTS_SECTION = re.compile(r"(^## Affects\n)(.*?)(?=^## |\Z)", re.M | re.S)
AFFECTS_BULLET = re.compile(r"^-\s+(?:\[)?`([^`]+)`(?:\]\([^)]*\))?.*$", re.M)
# A bare path (existing, file-level-only behaviour, left to the website's own
# fallback link) or `path::symbol`, restricted to the languages this file already
# knows how to search: Rust and `.pest`. Anything else -- a `.toml` fixture, a doc
# path -- is not a code citation this function resolves.
CODE_SYMBOL_RE = re.compile(r"^([\w.\-]+(?:/[\w.\-]+)+\.(?:rs|pest))::([A-Za-z_][A-Za-z0-9_]*)$")


NAMED_ITEM = re.compile(rf"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:{'|'.join(ITEM_KEYWORDS)})\s+([A-Za-z_][A-Za-z0-9_]*)")


def following_named_item(text: str, start: int, path: Path, line: int) -> tuple[str, int]:
    """The `fn`/`static`/`const`/`struct`/`enum`/`trait` counterpart of `following_item`
    (which is deliberately `fn`-only, `arch-implements`'s own original scope): the next
    item of any of those kinds after `start`, with the same "only comments/attributes in
    between" rule, so a `// limit:` marker cannot silently latch onto the wrong item."""
    remainder = text[start:]
    item = NAMED_ITEM.search(remainder)
    if not item:
        raise ValueError(f"{path}:{line}: citation has no following item (fn/static/const/struct/enum/trait)")
    between = remainder[: item.start()]
    leftover = ATTRIBUTE.sub("", COMMENT.sub("", between)).strip()
    if leftover:
        raise ValueError(
            f"{path}:{line}: citation must directly precede its item; found `{leftover.splitlines()[0]}` in between"
        )
    return item.group(1), start + item.start()


def find_named_item(text: str, name: str) -> int | None:
    """Byte offset of the keyword introducing the first `fn`/`static`/`const`/
    `struct`/`enum`/`trait` named `name`, in file order -- not a real parser (a
    match inside a string or comment is not excluded), sufficient for a name that
    is not itself shadowed or overloaded in the file, which is what a `## Affects`
    citation names in practice."""
    pattern = re.compile(rf"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:{'|'.join(ITEM_KEYWORDS)})\s+{re.escape(name)}\b")
    m = pattern.search(text)
    return m.start() if m else None


def resolve_named_citation(core: Path, rel_path: str, symbol: str) -> Citation:
    """A `path::symbol` `## Affects` entry, resolved the way a marker citation is:
    the item's own start line (for the link) and its full extent (for the
    metel-core#1191 staleness check, folded in should limitations ever join it)."""
    full = core / rel_path
    if not full.is_file():
        raise ValueError(f"{rel_path}::{symbol}: no such file")
    text = full.read_text(errors="ignore")
    if rel_path.endswith(".pest"):
        rule = re.search(rf"^[ \t]*{re.escape(symbol)}[ \t]*=[ \t]*[@_$!]?\{{", text, re.M)
        if not rule:
            raise ValueError(f"{rel_path}::{symbol}: no such grammar rule")
        line = text.count("\n", 0, rule.start()) + 1
        return Citation(Path(rel_path), symbol, line, line, line)
    start = find_named_item(text, symbol)
    if start is None:
        raise ValueError(f"{rel_path}::{symbol}: no fn/static/const/struct/enum/trait named `{symbol}`")
    start_line, end_line = function_extent(text, start)
    return Citation(Path(rel_path), symbol, start_line, start_line, end_line)


def regenerate_record_affects(records_dir: Path, core: Path, core_ref: str, check: bool) -> list[str]:
    """Rewrite every resolvable `path::symbol` bullet in a `LIMIT-*`/`GAP-*`
    record's `## Affects` into a commit-pinned, line-accurate link -- the same
    check/write duality as `regenerate` above, just sourced from record markdown
    instead of Architecture Spec requirement tables. A bare path (no `::symbol`)
    is untouched; the website's own file-level fallback link still applies to it."""
    stale = []
    if not records_dir.is_dir():
        return stale
    for path in sorted(records_dir.glob("*.md")):
        text = path.read_text()
        section = AFFECTS_SECTION.search(text)
        if not section:
            continue
        body = section.group(2)
        new_body = body
        # Level 3's delimited subsection (metel-core#1247), if present, is off limits --
        # its bullets are machine-owned by `regenerate_record_markers`, not this
        # function, even though they're shaped identically (a link-wrapped `path::symbol`
        # bullet). Skip any match whose span falls inside it.
        owned_span = LIMIT_MARKERS_BLOCK.search(body)
        owned = (owned_span.start(), owned_span.end()) if owned_span else None
        for bullet in list(AFFECTS_BULLET.finditer(body)):
            if owned and owned[0] <= bullet.start() < owned[1]:
                continue
            token = bullet.group(1)
            code = CODE_SYMBOL_RE.match(token)
            if not code:
                continue
            rel_path, symbol = code.groups()
            try:
                citation = resolve_named_citation(core, rel_path, symbol)
            except ValueError as error:
                stale.append(f"{path.relative_to(DOCS)}: {error}")
                continue
            link = f"https://github.com/metel-lang/metel-core/blob/{core_ref}/{citation.path}#L{citation.line}"
            new_line = f"- [`{token}`]({link})"
            new_body = new_body.replace(bullet.group(0), new_line, 1)
        if new_body != body:
            new_text = text[: section.start(2)] + new_body + text[section.end(2) :]
            if check:
                stale.append(f"{path.relative_to(DOCS)}: generated Affects code links are stale")
            else:
                path.write_text(new_text)
    return stale


# Level 3 (metel-core#1236, ADR-0055 amendment #1247): `// limit: ["LIMIT-X-001"]` in
# metel-core, mirroring `arch-implements`'s placement rule and discovery mechanism. The
# marker is a coordinate, not a contract -- it never states the limitation is handled,
# only where it currently lives, and it is checked *against* the record, never trusted
# as a citation on its own. It is written only into a delimited, fully machine-owned
# subsection of `## Affects`; nothing hand-written can appear inside it, and this code
# never touches anything outside it (a bare path, a `path::symbol` line, any other
# citation -- all level 2 or hand-authored, untouched here).
LIMIT_CITE = re.compile(r"^\s*//\s*limit:\s*\[([^]]*)\]\s*$", re.M)
LIMIT_ID = r"LIMIT-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}"
LIMIT_IDS = re.compile(rf'"({LIMIT_ID})"')
RECORD_ID = re.compile(rf"^id:\s*({LIMIT_ID})\s*$", re.M)
RECORD_DISPOSITION = re.compile(r"^disposition:\s*(\S+)\s*$", re.M)
LIMIT_MARKERS_START = "<!-- limit.py:markers:start -->"
LIMIT_MARKERS_END = "<!-- limit.py:markers:end -->"
LIMIT_MARKERS_BLOCK = re.compile(re.escape(LIMIT_MARKERS_START) + r"\n.*?" + re.escape(LIMIT_MARKERS_END) + r"\n?", re.S)
LIMIT_ACTIVE_DISPOSITIONS = {"known", "accepted", "mitigated", "planned"}


def limit_citations(core: Path):
    """`{LIMIT-* id: [Citation, ...]}` for every `// limit: [...]` marker in metel-core,
    resolved the same way `citations()` resolves `arch-implements`: `following_item`/
    `following_rule` finds what the marker precedes, `function_extent` its extent."""
    found = defaultdict(list)
    sources = [p for pattern in ("*.rs", "*.pest") for p in core.rglob(pattern)]
    for path in sources:
        if any(part in {"target", ".git"} for part in path.parts):
            continue
        text = path.read_text(errors="ignore")
        for match in LIMIT_CITE.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            ids = LIMIT_IDS.findall(match.group(1))
            if not ids:
                raise ValueError(f"{path}:{line}: limit citation contains no well-formed LIMIT-* id")
            if path.suffix == ".pest":
                item, item_start = following_rule(text, match.end(), path, line)
            else:
                item, item_start = following_named_item(text, match.end(), path, line)
            start_line, end_line = function_extent(text, item_start)
            rel = path.relative_to(core)
            citation = Citation(rel, item, line, start_line, end_line)
            for record_id in ids:
                found[record_id].append(citation)
    return found


def limit_ids_ever_marked(core: Path) -> set[str]:
    """Every LIMIT-* id that has ever appeared in a `// limit:` marker anywhere in
    metel-core's checked-out history, added or removed -- one `git log -G` pickaxe
    scoped to Rust/`.pest` sources (needs full history, `fetch-depth: 0`, same as
    `git_ref` above), not a per-record walk. Used only to flag a record whose marker
    has since disappeared; never to decide what a marker currently says."""
    out = subprocess.run(
        ["git", "-C", str(core), "log", "-p", "-G", "limit:", "--", "*.rs", "*.pest"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        return set()
    ids: set[str] = set()
    for line in out.stdout.splitlines():
        if line[:1] in ("+", "-") and "limit:" in line:
            ids.update(re.findall(LIMIT_ID, line))
    return ids


def regenerate_record_markers(records_dir: Path, core: Path, core_ref: str, check: bool) -> list[str]:
    """The delimited subsection of a `LIMIT-*` record's `## Affects` driven by
    `// limit:` markers: fully regenerated each run from every current marker citing
    that record's id, the same full-replace treatment `implements`/`verified by` cells
    get -- not the line-level patch `regenerate_record_affects` (level 2) does for a
    human's own `path::symbol` bullet. A record with no current marker has no block at
    all (most limitation records cite no code, and an empty block on every one of them
    would be pure noise); a record whose block would become empty has it removed
    entirely, not left as empty delimiters."""
    stale = []
    if not records_dir.is_dir():
        return stale
    markers = limit_citations(core)
    ever_marked = limit_ids_ever_marked(core)
    known_ids: set[str] = set()
    for path in sorted(records_dir.glob("*.md")):
        text = path.read_text()
        id_match = RECORD_ID.search(text)
        if not id_match:
            continue
        record_id = id_match.group(1)
        known_ids.add(record_id)
        disposition_match = RECORD_DISPOSITION.search(text)
        disposition = disposition_match.group(1) if disposition_match else None
        citations = sorted(set(markers.get(record_id, [])), key=lambda c: (str(c.path), c.item or "", c.line))
        if citations and disposition not in LIMIT_ACTIVE_DISPOSITIONS:
            stale.append(
                f"{path.relative_to(DOCS)}: `{record_id}` is `{disposition}` but a `// limit:` marker "
                f"still cites it; remove the marker or reactivate the record"
            )
        section = AFFECTS_SECTION.search(text)
        if not section:
            if citations:
                stale.append(f"{path.relative_to(DOCS)}: `{record_id}` has a live `// limit:` marker but no `## Affects` section")
            continue
        body = section.group(2)
        if not citations and not LIMIT_MARKERS_BLOCK.search(body):
            continue  # nothing to add, nothing to remove -- leave the section exactly as it is
        without_block = LIMIT_MARKERS_BLOCK.sub("", body).rstrip("\n")
        if citations:
            block = LIMIT_MARKERS_START + "\n" + "".join(
                f"- [`{c.path}::{c.item}`]"
                f"(https://github.com/metel-lang/metel-core/blob/{core_ref}/{c.path}#L{c.line})\n"
                for c in citations
            ) + LIMIT_MARKERS_END
            new_body = (without_block + "\n\n" + block + "\n\n") if without_block else (block + "\n\n")
        else:
            new_body = without_block + "\n\n" if without_block else ""
        if new_body != body:
            if check:
                stale.append(f"{path.relative_to(DOCS)}: generated `// limit:` marker citations for `{record_id}` are stale")
            else:
                path.write_text(text[: section.start(2)] + new_body + text[section.end(2) :])
    for record_id in sorted(set(markers) - known_ids):
        rel = markers[record_id][0].path
        stale.append(f"{rel}: `// limit:` marker cites `{record_id}`, which does not exist")
    for record_id in sorted(ever_marked - set(markers)):
        stale.append(
            f"{record_id}: was cited by a `// limit:` marker in metel-core history and no longer is by any "
            f"current one; confirm the limitation is resolved (and update its disposition) or restore the marker"
        )
    return stale


def citations(core: Path):
    found = defaultdict(lambda: {"implements": [], "verifies": []})
    sources = [p for pattern in ("*.rs", "*.pest") for p in core.rglob(pattern)]
    for path in sources:
        if any(part in {"target", ".git"} for part in path.parts):
            continue
        text = path.read_text(errors="ignore")
        for match in CITE.finditer(text):
            kind = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            claim_ids = IDS.findall(match.group(2))
            if not claim_ids:
                raise ValueError(f"{path}:{line}: citation contains no well-formed arch claim")
            if path.suffix == ".pest":
                if kind != "implements":
                    raise ValueError(f"{path}:{line}: only arch-implements can cite a grammar rule")
                item, item_start = following_rule(text, match.end(), path, line)
            else:
                item, item_start = following_item(text, match.end(), kind == "verifies", path, line)
            start_line, end_line = function_extent(text, item_start)
            rel = path.relative_to(core)
            citation = Citation(rel, item, line, start_line, end_line)
            for claim in claim_ids:
                found[claim][kind].append(citation)
    for path in core.rglob("*.toml"):
        if "tests" not in path.parts:
            continue
        try:
            data = tomllib.loads(path.read_text())
        except tomllib.TOMLDecodeError:
            continue
        options = data.get("options", {})
        values = options.get("arch_verifies", [])
        if values and options.get("skip"):
            raise ValueError(
                f"{path}: arch_verifies cites a skipped fixture (`skip = ...`); a skipped fixture "
                f"never runs and cannot verify a claim"
            )
        for claim in values:
            if re.fullmatch(ID, claim):
                found[claim]["verifies"].append(Citation(path.relative_to(core), None, 1, None, None))
    return found


def last_touch_commit(core: Path, citation: Citation) -> str:
    """The most recent commit that changed the text a citation actually
    points at: a line range for a Rust item, or the whole file for a
    fixture .toml citation (which has no meaningful sub-range to scope to).
    Requires full history (`git log`'s default shallow-unfriendly walk) --
    see the fetch-depth: 0 note on the CI job that runs this."""
    if citation.start_line is None:
        scope = ["--", str(citation.path)]
    else:
        scope = ["-L", f"{citation.start_line},{citation.end_line}:{citation.path}"]
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


EXEMPTION_KEYS = ("kind", "ref", "reason", "owner", "review")
EXEMPTION_SPLIT = re.compile(r";\s*(?=(?:" + "|".join(EXEMPTION_KEYS) + r"):)")
ISSUE_REF = re.compile(r"^(?P<repo>[a-zA-Z0-9_.-]+)#(?P<num>\d+)$")
RFC_REF = re.compile(r"^rfc-\d{4}$", re.IGNORECASE)
_RFC_TOOL = None


def _rfc_tool():
    """rfc.py owns the exemption vocabulary (`COVERAGE_VALID_KINDS`) and the
    live blocker checks (`fetch_issue_state`, RFC stage lookup); import it
    rather than reimplementing either (metel-core#1193). Loaded from this
    repo's own copy, independent of the DOCS override tests use."""
    global _RFC_TOOL
    if _RFC_TOOL is None:
        path = Path(__file__).resolve().parents[2] / "rfcs/tools/rfc.py"
        spec = importlib.util.spec_from_file_location("rfc_tool", path)
        _RFC_TOOL = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _RFC_TOOL
        spec.loader.exec_module(_RFC_TOOL)
    return _RFC_TOOL


def issue_state(repo: str, number: str):
    """(state, error) for a metel-lang issue; best-effort, never raises."""
    return _rfc_tool().fetch_issue_state("metel-lang", repo, number)


def rfc_stages() -> dict:
    return _rfc_tool().scan_rfc_metadata()[4]


def today() -> datetime.date:
    return datetime.date.today()


def parse_exemption(value: str) -> dict:
    fields = {}
    for part in EXEMPTION_SPLIT.split(value.strip()):
        key, sep, rest = part.partition(":")
        fields[key.strip()] = rest.strip() if sep else ""
    return fields


def exemption_problems(value: str) -> list[str]:
    """Problems with one `implements exemption` / `verification exemption`
    cell, using rfc.py's kind vocabulary (untestable / blocked / elsewhere)
    with an *enforceable* lifetime for the temporary kind: a `blocked`
    exemption fails CI once its review date passes or its `ref` resolves
    (an unreachable GitHub API degrades to skipping that live check, never
    to a failure -- same rule as rfc.py's own `blocked` check)."""
    fields = parse_exemption(value)
    problems = [f"unrecognized exemption key `{k}`" for k in fields if k not in EXEMPTION_KEYS]
    kind = fields.get("kind", "")
    if kind not in _rfc_tool().COVERAGE_VALID_KINDS:
        problems.append(f"`kind` must be one of {sorted(_rfc_tool().COVERAGE_VALID_KINDS)}, not {kind!r}")
        return problems
    for required in ("reason", "owner"):
        if not fields.get(required):
            problems.append(f"missing `{required}`")
    ref = fields.get("ref", "")
    if kind in ("blocked", "elsewhere") and not ref:
        problems.append(f"kind `{kind}` needs a `ref`")
    if kind != "blocked":
        return problems
    review = fields.get("review", "")
    try:
        due = datetime.date.fromisoformat(review)
    except ValueError:
        problems.append("kind `blocked` needs a `review` date (YYYY-MM-DD)")
        due = None
    if due is not None and due < today():
        problems.append(f"`review` date {review} has passed; re-confirm the blocker or cite real evidence")
    closed = "cite real evidence for this claim and delete this exemption row"
    if RFC_REF.match(ref):
        stage = rfc_stages().get(ref.lower())
        if stage is None:
            problems.append(f"blocked on `{ref}`, which does not exist")
        elif stage == "implemented":
            problems.append(f"blocked on `{ref}`, which is now implemented -- {closed}")
    elif ISSUE_REF.match(ref):
        m = ISSUE_REF.match(ref)
        state, error = issue_state(m.group("repo"), m.group("num"))
        if error is None and state == "closed":
            problems.append(f"blocked on `{ref}`, which is now closed -- {closed}")
    return problems


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
                elif not values[kind] and field not in exemptions:
                    stale.append(f"{path.relative_to(DOCS)}: `{claim}` lacks arch-{kind} evidence or valid `{field}`")
                elif not values[kind]:
                    for problem in exemption_problems(exemptions[field]):
                        stale.append(f"{path.relative_to(DOCS)}: `{claim}` `{field}`: {problem}")
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
        core_ref = args.core_ref or git_ref(args.core)
        findings = regenerate(DOCS / "architecture/spec", args.core, citations(args.core), args.check, core_ref)
        findings += regenerate_record_affects(DOCS / "architecture/limitations", args.core, core_ref, args.check)
        findings += regenerate_record_affects(DOCS / "architecture/gaps", args.core, core_ref, args.check)
        # Level 3 (metel-core#1247) is LIMIT-* only -- GAP-* is chartered by ADR-0057 as
        # a Language Spec concept, not architecture, and metel-core's Rust source has
        # nothing to mark for a gap in what the spec itself says.
        findings += regenerate_record_markers(DOCS / "architecture/limitations", args.core, core_ref, args.check)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        findings = [str(error)]
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
