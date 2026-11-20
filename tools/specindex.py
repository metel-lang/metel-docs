"""The layout of the public spec, found by anchor rather than by file name.

`reference/spec` holds chapters. A chapter is either a single file (`lexical.md`) or a directory
(`declarations/`) whose pages nest as deep as the content wants. Anchors do not depend on the layout:
a rule is `spec.<chapter>.<section>.<rule>` wherever its page lives. So a tool that needs to find a
rule, or a link that needs to point at one, asks this module which file holds the anchor.

    spec_files(root)        every spec page, recursively, in a stable order
    chapter_of(path, root)  the chapter a page belongs to: its file stem, or its top-level directory
    anchors(root)           {anchor: relative path} for every explicit `{#id}` and rule anchor
    heading_slugs(path)     {slug: line} for the headings of one page (explicit id, else the slug)
    duplicates(root)        anchors defined on more than one page
"""
from __future__ import annotations

import re
from pathlib import Path

SPEC_REL = Path("reference") / "spec"
EXPLICIT_ID_RE = re.compile(r"\{#([A-Za-z0-9_.\-]+)\}")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# Pages that are part of the directory but not the language specification itself.
NOT_THE_SPEC = {"STYLEGUIDE.md"}


def spec_root(root: Path) -> Path:
    return root / SPEC_REL


def pages_under(base: Path, *, include_styleguide: bool = True) -> list[Path]:
    """Every markdown page under `base` (a spec directory), parents before children, in name order."""
    if not base.is_dir():
        return []
    pages = [p for p in base.rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(base).parts)]
    if not include_styleguide:
        pages = [p for p in pages if p.name not in NOT_THE_SPEC or p.parent != base]
    return sorted(pages, key=lambda p: (len(p.relative_to(base).parts), p.relative_to(base).as_posix()))


def spec_files(root: Path, *, include_styleguide: bool = True) -> list[Path]:
    """Every page of the spec under `root/reference/spec`."""
    return pages_under(spec_root(root), include_styleguide=include_styleguide)


def chapter_of(path: Path, root: Path) -> str:
    """`declarations` for declarations.md, declarations/index.md and declarations/aspects/dyn.md."""
    parts = path.relative_to(spec_root(root)).parts
    return parts[0][:-3] if len(parts) == 1 and parts[0].endswith(".md") else parts[0]


def slug(heading: str) -> str:
    """The anchor Docusaurus gives a heading that has no explicit id."""
    text = EXPLICIT_ID_RE.sub("", heading)
    text = re.sub(r"[`*_]", "", text).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text).strip()
    return re.sub(r"\s+", "-", text)


def heading_slugs(path: Path) -> dict[str, int]:
    """{anchor: 1-based line} of the headings of a page, outside code fences."""
    out: dict[str, int] = {}
    fenced = False
    for i, line in enumerate(path.read_text().split("\n"), 1):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        m = None if fenced else HEADING_RE.match(line)
        if not m:
            continue
        explicit = EXPLICIT_ID_RE.search(m.group(2))
        out.setdefault(explicit.group(1) if explicit else slug(m.group(2)), i)
    return out


def anchors(root: Path) -> dict[str, str]:
    """{explicit anchor: path relative to the docs root} for the whole spec; the first definition wins."""
    out: dict[str, str] = {}
    for page in spec_files(root):
        rel = page.relative_to(root).as_posix()
        for a in explicit_anchors(page):
            out.setdefault(a, rel)
    return out


_page_cache: dict[Path, dict[str, str]] = {}


def page_for(root: Path, anchor: str) -> str | None:
    """The page holding `anchor`, relative to reference/spec (`declarations/aspects/dyn.md`), or None."""
    root = root.resolve()
    if root not in _page_cache:
        _page_cache[root] = {a: Path(rel).relative_to(SPEC_REL).as_posix() for a, rel in anchors(root).items()}
    return _page_cache[root].get(anchor)


def explicit_anchors(path: Path) -> list[str]:
    found, fenced = [], False
    for line in path.read_text().split("\n"):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced and line.startswith("#"):
            found.extend(EXPLICIT_ID_RE.findall(line))
    return found


def duplicates(root: Path) -> dict[str, list[str]]:
    """Anchors defined more than once (in one page or across pages): a link to one is ambiguous."""
    seen: dict[str, list[str]] = {}
    for page in spec_files(root):
        rel = page.relative_to(root).as_posix()
        for a in explicit_anchors(page):
            seen.setdefault(a, []).append(rel)
    return {a: pages for a, pages in seen.items() if len(pages) > 1}


if __name__ == "__main__":
    import json
    import sys

    docs = Path(__file__).resolve().parents[1]
    json.dump(anchors(docs), sys.stdout, indent=1, sort_keys=True)
    print()
