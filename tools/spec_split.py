#!/usr/bin/env python3
"""Split a spec chapter into a directory of pages, and keep every link pointing at the right page.

    spec_split.py skeleton reference/spec/declarations.md   # print a plan: one page per `##` section
    spec_split.py apply PLAN.toml [--dry-run]                # write the pages, remove the old file, relink
    spec_split.py check-links                                # every relative link and fragment resolves
    spec_split.py fix-links [--dry-run]                      # repair links that still name a chapter that became a directory

A plan names the chapter file and says which sections go to which page:

    source = "reference/spec/declarations.md"
    [[page]]
    file = "variables.md"                  # under reference/spec/<chapter>/
    sections = ["Variables"]               # a section and everything beneath it
    [[page]]
    file = "aspects/index.md"
    sections = ["Aspects:own"]             # only the text of the section, up to its first subsection
    [[page]]
    file = "aspects/dyn.md"
    sections = ["`dyn Aspect`"]

The chapter's own introduction becomes `index.md`. Every `##`..`####` section must be placed exactly once.
Headings are re-levelled so a page starts at `#`; rule blocks (`#####`) and every `{#anchor}` are untouched,
so rule ids do not change. Links are rewritten by anchor: a link into the old file goes to the page that now
holds its fragment, a link out of a moved page is recomputed for the page's new depth, and a bare
`reference/spec/<chapter>.md#frag` in prose or frontmatter is updated the same way.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent
sys.path.insert(0, str(HERE))
import specindex  # noqa: E402

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
RULE_HEAD_RE = re.compile(r"^#{5} (?:Legality Rule|Dynamic Semantics(?: Rule)?) \{#")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"(?<!\\)\]\(([^()\s]+(?:\([^()]*\))?[^()\s]*)(\s+\"[^\"]*\")?\)")
SECTION_LEVELS = (2, 3, 4)
# `reference/spec/<page>.md#frag` written as text (record frontmatter, prose), not as a markdown link
BARE_PAGE_RE = re.compile(r"(reference/spec/[A-Za-z0-9_/.-]+\.md)#([A-Za-z0-9_.-]+)")


@dataclass
class Section:
    level: int
    heading: str          # the heading text as written, `{#id}` included
    lines: list[str]      # its own lines: from the heading to the next heading of level 1..4
    children: list["Section"] = field(default_factory=list)
    parent: "Section | None" = None

    @property
    def title(self) -> str:
        return specindex.EXPLICIT_ID_RE.sub("", self.heading).strip()

    def tree(self) -> list["Section"]:
        out = [self]
        for c in self.children:
            out.extend(c.tree())
        return out


def parse_sections(text: str) -> tuple[list[str], list[Section]]:
    """(the lines before the first `##`, the top-level sections), headings found outside code fences."""
    lines = text.split("\n")
    fenced = False
    cut: list[tuple[int, int]] = []
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        m = None if fenced or RULE_HEAD_RE.match(line) else HEADING_RE.match(line)
        if m and len(m.group(1)) in SECTION_LEVELS:
            cut.append((i, len(m.group(1))))
    preamble = lines[: cut[0][0]] if cut else lines
    sections: list[Section] = []
    stack: list[Section] = []
    for k, (i, level) in enumerate(cut):
        end = cut[k + 1][0] if k + 1 < len(cut) else len(lines)
        sec = Section(level, HEADING_RE.match(lines[i]).group(2), lines[i:end])
        while stack and stack[-1].level >= level:
            stack.pop()
        if stack:
            sec.parent = stack[-1]
            stack[-1].children.append(sec)
        else:
            sections.append(sec)
        stack.append(sec)
    return preamble, sections


def all_sections(top: list[Section]) -> list[Section]:
    return [s for t in top for s in t.tree()]


# ------------------------------------------------------------------ plan and pages

@dataclass
class Page:
    file: str
    sections: list[tuple[Section, bool]]  # (section, tree?) in order
    title: str | None = None


def load_plan(plan_path: Path, sections: list[Section]) -> tuple[Path, list[Page]]:
    plan = tomllib.loads(plan_path.read_text())
    source = DOCS / plan["source"]
    by_title: dict[str, Section] = {}
    for s in all_sections(sections):
        if s.title in by_title:
            raise SystemExit(f"error: two sections are titled `{s.title}`; give the plan a unique spelling by renaming one")
        by_title[s.title] = s
    pages, placed = [], {}
    for entry in plan.get("page", []):
        items = []
        for ref in entry["sections"]:
            title, _, mode = ref.partition(":")
            if title not in by_title:
                raise SystemExit(f"error: the plan names no section `{title}` in {plan['source']}")
            sec = by_title[title]
            tree = mode != "own"
            for s in (sec.tree() if tree else [sec]):
                if s.title in placed:
                    raise SystemExit(f"error: section `{s.title}` is placed twice ({placed[s.title]} and {entry['file']})")
                placed[s.title] = entry["file"]
            items.append((sec, tree))
        pages.append(Page(entry["file"], items, entry.get("title")))
    missing = [s.title for s in all_sections(sections) if s.title not in placed]
    if missing:
        raise SystemExit("error: sections the plan does not place: " + ", ".join(missing))
    return source, pages


def relevel(lines: list[str], delta: int) -> list[str]:
    out, fenced = [], False
    for line in lines:
        if FENCE_RE.match(line):
            fenced = not fenced
        m = None if fenced or RULE_HEAD_RE.match(line) else HEADING_RE.match(line)
        if m and len(m.group(1)) in SECTION_LEVELS + (1,):
            out.append("#" * max(1, len(m.group(1)) + delta) + " " + m.group(2))
        else:
            out.append(line)
    return out


def split_frontmatter(lines: list[str]) -> tuple[list[str], list[str]]:
    """(the frontmatter lines without the fences, the rest) of a chapter's lines before its first section."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[1:i], lines[i + 1 :]
    return [], lines


def render_page(page: Page, position: int) -> str:
    blocks: list[list[str]] = []
    first_level = page.sections[0][0].level
    top_levels = [sec.level for sec, _ in page.sections]
    if page.file == "index.md":
        delta, head = 0, []  # the chapter index keeps the chapter's own heading levels
    elif page.title:
        delta = 2 - min(top_levels)
        head = [f"# {page.title}", ""]
    else:
        delta = 1 - first_level
        head = []
    for sec, tree in page.sections:
        body: list[str] = []
        for s in (sec.tree() if tree else [sec]):
            body.extend(s.lines)
        blocks.append(relevel(body, delta))
    text = "\n".join(head + [line for b in blocks for line in b]).rstrip("\n") + "\n"
    return f"---\nsidebar_position: {position}\n---\n\n{text}"


def skeleton(source_rel: str) -> str:
    text = (DOCS / source_rel).read_text()
    _, top = parse_sections(text)
    chapter = Path(source_rel).stem
    out = [f'source = "{source_rel}"', ""]
    for sec in top:
        slug = re.sub(r"[^a-z0-9]+", "-", sec.title.lower()).strip("-") or "section"
        out += ["[[page]]", f'file = "{slug}.md"', f"sections = [{sec.title!r}]".replace("'", '"'), ""]
    return "\n".join(out)


# ------------------------------------------------------------------ links

def docs_markdown(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*.md"):
        rel = p.relative_to(root).parts
        if any(part.startswith(".") for part in rel):
            continue
        out.append(p)
    return sorted(out)


def split_dest(dest: str) -> tuple[str, str]:
    path, _, frag = dest.partition("#")
    return path, frag


def is_external(dest: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", dest)) or dest.startswith("//")


def title_slug(text: str) -> str | None:
    """The slug of a page's `# Title`. The rendered page gives its title no anchor, so a link to that
    fragment from another page lands nowhere: such a link points at the page."""
    fenced = False
    for line in text.split("\n"):
        if FENCE_RE.match(line):
            fenced = not fenced
        m = None if fenced else re.match(r"^#\s+(.*?)\s*$", line)
        if m:
            explicit = specindex.EXPLICIT_ID_RE.search(m.group(1))
            return explicit.group(1) if explicit else specindex.slug(m.group(1))
    return None


def relpath(target: Path, start_dir: Path) -> str:
    return Path(os.path.relpath(target, start_dir)).as_posix()


def anchor_pages(root: Path, pages: list[Path]) -> dict[str, Path]:
    """{explicit anchor or slug: page} over the given pages; explicit anchors win."""
    out: dict[str, Path] = {}
    for page in pages:
        for a in specindex.explicit_anchors(page):
            out.setdefault(a, page)
    for page in pages:
        for a in specindex.heading_slugs(page):
            out.setdefault(a, page)
    return out


def apply(plan_path: Path, dry_run: bool) -> int:
    plan = tomllib.loads(plan_path.read_text())
    source = DOCS / plan["source"]
    chapter = source.stem
    new_dir = source.parent / chapter
    text = source.read_text()
    preamble, top = parse_sections(text)
    _, pages = load_plan(plan_path, top)

    # What each old fragment becomes: the page of the section holding it (rule anchors included).
    new_files: dict[Path, str] = {}
    section_page: dict[int, Path] = {}
    for n, page in enumerate(pages, 1):
        target = new_dir / page.file
        new_files[target] = render_page(page, n)
        for sec, tree in page.sections:
            for s in (sec.tree() if tree else [sec]):
                section_page[id(s)] = target
    index = new_dir / "index.md"
    own_frontmatter, intro = split_frontmatter(preamble)
    front = "---\n" + "".join(f"{line}\n" for line in own_frontmatter + ["sidebar_position: 0"]) + "---\n\n"
    intro_text = "\n".join(intro).strip("\n")
    if index not in new_files:
        new_files[index] = front + intro_text + "\n"
    else:
        body = new_files[index].split("---\n\n", 1)[1]
        new_files[index] = front + intro_text + "\n\n" + body

    # Old fragment -> new page, from the old file's own sections.
    old_frag_page: dict[str, Path] = {}
    for s in all_sections(top):
        page = section_page[id(s)]
        for line in s.lines:
            for a in specindex.EXPLICIT_ID_RE.findall(line) if line.startswith("#") else []:
                old_frag_page.setdefault(a, page)
        explicit = specindex.EXPLICIT_ID_RE.search(s.heading)
        old_frag_page.setdefault(explicit.group(1) if explicit else specindex.slug(s.heading), page)
    for a in specindex.explicit_anchors(source):
        old_frag_page.setdefault(a, index if a not in old_frag_page else old_frag_page[a])
    # the chapter's own `# Title` heading
    for a, s in specindex.heading_slugs(source).items():
        old_frag_page.setdefault(a, index)

    moved_from: dict[Path, Path] = {}  # new page -> the old file whose relative links it carries
    for p in new_files:
        moved_from[p] = source

    title_slugs = {p: title_slug(c) for p, c in new_files.items()}
    changed: dict[Path, str] = {}

    def rewrite_links(body: str, old_loc: Path, new_loc: Path) -> str:
        def fix(m: re.Match) -> str:
            dest, title = m.group(1), m.group(2) or ""
            if is_external(dest) or dest.startswith(("mailto:", "/")):
                return m.group(0)  # a URL, or a site-absolute route: nothing in the file tree to move
            path_part, frag = split_dest(dest)
            target = (old_loc.parent / path_part).resolve() if path_part else old_loc.resolve()
            if path_part and target != source.resolve() and not target.exists():
                return m.group(0)  # already dangling: not ours to fix
            if target == source.resolve():
                page = old_frag_page.get(frag, index) if frag else index
                if page == new_loc and frag:
                    return f"]({'#' + frag}{title})"
                if frag and frag == title_slugs.get(page):
                    frag = ""  # a page's own title has no anchor once rendered
                return f"]({relpath(page, new_loc.parent)}{'#' + frag if frag else ''}{title})"
            if not path_part:
                return m.group(0)
            return f"]({relpath(target, new_loc.parent)}{'#' + frag if frag else ''}{title})"
        return LINK_RE.sub(fix, body)

    for page_path, content in new_files.items():
        changed[page_path] = rewrite_links(content, source, page_path)

    # every other page that links into the old file, and bare path mentions
    path_re = re.compile(r"reference/spec/" + re.escape(chapter) + r"\.md(#[A-Za-z0-9_.\-]+)?")
    rewritten_outside = 0
    for md in docs_markdown(DOCS):
        if md == source:
            continue
        body = md.read_text()
        new_body = rewrite_links(body, md, md)

        def bare(m: re.Match) -> str:
            frag = (m.group(1) or "#")[1:]
            page = old_frag_page.get(frag, index) if frag else index
            return page.relative_to(DOCS).as_posix() + (f"#{frag}" if frag else "")
        new_body = path_re.sub(bare, new_body)
        if new_body != body:
            changed[md] = new_body
            rewritten_outside += 1

    print(f"{plan['source']}: {len(pages)} pages + index; {rewritten_outside} other file(s) relinked")
    if dry_run:
        for p in sorted(new_files):
            print("  would write", p.relative_to(DOCS))
        return 0
    for p, content in changed.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    source.unlink()
    return 0


# ------------------------------------------------------------------ check-links

def fix_links(root: Path, dry_run: bool) -> int:
    """Repair links that still name a chapter file that has become a directory: follow the fragment to its page.

    `apply` does this for the split it performs; this catches what it could not see (a page added to the
    tree after the split, a link in a file outside the docs tree walked, a branch merged late).
    """
    spec = root / specindex.SPEC_REL
    chapters = {p.name: p for p in spec.iterdir() if p.is_dir() and (p / "index.md").is_file()}
    pages = specindex.spec_files(root)
    where = anchor_pages(root, pages)
    fixed = 0
    for md in docs_markdown(root):
        body = md.read_text()

        def fix(m: re.Match) -> str:
            nonlocal fixed
            dest, title = m.group(1), m.group(2) or ""
            if is_external(dest) or dest.startswith(("mailto:", "/")):
                return m.group(0)
            path_part, frag = split_dest(dest)
            if not path_part:
                return m.group(0)
            target = (md.parent / path_part).resolve()
            if target.is_file() and target.suffix == ".md" and frag and spec.resolve() in target.parents:
                if frag == title_slug(target.read_text()) and frag not in specindex.explicit_anchors(target) and target != md.resolve():
                    fixed += 1
                    return f"]({path_part}{title})"
                return m.group(0)
            if target.exists() or target.suffix != ".md" or target.parent != spec.resolve() or target.stem not in chapters:
                return m.group(0)
            chapter = chapters[target.stem]
            page = where.get(frag) if frag else None
            if page is None or specindex.chapter_of(page, root) != target.stem:
                page = chapter / "index.md"
            if frag and frag == title_slug(page.read_text()):
                frag = ""
            fixed += 1
            return f"]({relpath(page, md.parent)}{'#' + frag if frag else ''}{title})"
        new = LINK_RE.sub(fix, body)

        def bare(m: re.Match) -> str:
            nonlocal fixed
            target = root / m.group(1)
            if target.is_file() and m.group(2) == title_slug(target.read_text()) and m.group(2) not in specindex.explicit_anchors(target):
                fixed += 1
                return m.group(1)
            return m.group(0)
        new = BARE_PAGE_RE.sub(bare, new)
        if new != body and not dry_run:
            md.write_text(new)
    print(f"{fixed} link(s) {'would be ' if dry_run else ''}repaired")
    return 0


def check_links(root: Path) -> list[str]:
    pages = docs_markdown(root)
    cache: dict[Path, tuple[set[str], set[str]]] = {}

    def anchors_of(p: Path):
        if p not in cache:
            cache[p] = (set(specindex.explicit_anchors(p)), set(specindex.heading_slugs(p)))
        return cache[p]
    problems = []
    for md in pages:
        fenced = False
        for n, line in enumerate(md.read_text().split("\n"), 1):
            if FENCE_RE.match(line):
                fenced = not fenced
                continue
            if fenced:
                continue
            for m in LINK_RE.finditer(line):
                dest = m.group(1)
                if is_external(dest) or dest.startswith("/"):
                    continue  # a URL or a site route: not a file in this tree
                path_part, frag = split_dest(dest)
                target = (md.parent / path_part).resolve() if path_part else md.resolve()
                if path_part and not target.exists():
                    problems.append(f"{md.relative_to(root)}:{n}: `{dest}` does not exist")
                elif frag and target.suffix == ".md" and target.is_file():
                    explicit, slugs = anchors_of(target)
                    if frag not in explicit and frag not in slugs:
                        problems.append(f"{md.relative_to(root)}:{n}: `{dest}`: no such anchor")
                    elif frag == title_slug(target.read_text()) and frag not in explicit and target != md.resolve():
                        problems.append(f"{md.relative_to(root)}:{n}: `{dest}`: the page's own title has no anchor once rendered; link the page")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sk = sub.add_parser("skeleton")
    sk.add_argument("source")
    ap_ = sub.add_parser("apply")
    ap_.add_argument("plan")
    ap_.add_argument("--dry-run", action="store_true")
    fl = sub.add_parser("fix-links")
    fl.add_argument("--dry-run", action="store_true")
    sub.add_parser("check-links")
    args = ap.parse_args()
    if args.cmd == "skeleton":
        print(skeleton(args.source))
        return 0
    if args.cmd == "apply":
        return apply(Path(args.plan).resolve(), args.dry_run)
    if args.cmd == "fix-links":
        return fix_links(DOCS, args.dry_run)
    problems = check_links(DOCS)
    for p in problems:
        print(p)
    print(f"{len(problems)} broken link(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
