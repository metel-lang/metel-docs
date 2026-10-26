#!/usr/bin/env python3
"""Validate the Operations Specification against the repositories (metel-core#1507).

Structure of `operations/spec/*.md`, the cross-references inside `operations/`, and the paths a
requirement says implement it; and discovery: every workflow, script, hook and command in the
reachable repositories must appear in `operations/inventory.md` (or be marked `local`), and every
inventory row must name something that exists.

Severity follows ADR-0064 and metel-core#1417. Structural findings, and assets of `metel-docs`
itself, fail. An asset of *another* repository that the inventory does not list is a warning, and
fails under `--strict` (a release): demanding that the inventory in `metel-docs` change before a
`metel-core` pull request can pass is the cross-repository circularity ADR-0064 removed.

Usage: check_operations.py [--check] [--strict] [--workspace DIR]
  --workspace  a directory holding sibling checkouts named metel-core, metel-docs, metel-website,
               metel-docs-internal; default is the parent of the metel-docs checkout, and a core
               checkout that embeds docs as `docs/` is detected. Repositories that are not there
               are skipped, and the output says which.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_architecture import Finding  # noqa: E402
from check_flows import check_flows  # noqa: E402

DOCS_ROOT = Path(__file__).resolve().parent.parent.parent
STATUSES = {"implemented", "partial", "planned"}
FIELDS = ["status", "owner", "trigger", "produces", "implemented by", "verified by", "related"]
REPOS = ["metel-core", "metel-docs", "metel-website", "metel-docs-internal"]
ID_RE = r"PROC-[A-Z]+-\d{3}"
HEADING_RE = re.compile(rf"^### ({ID_RE}) — (.+?) \{{#([a-z0-9-]+)\}}\s*$", re.MULTILINE)
ISSUE_RE = re.compile(r"(?:metel-core)?#\d+")
MARKER_RE = re.compile(rf"#\s*Process:\s*({ID_RE})")
# `metel-core/path`, `metel-docs/path` ... inside backticks, optionally followed by `::something`
REPO_PATH_RE = re.compile(r"`(metel-core|metel-docs|metel-website|metel-docs-internal)/([^`\s]+)`")


# ---------------------------------------------------------------- the specification
def parse_requirements(spec_dir: Path, root: Path):
    """[(page, id, anchor, fields dict or None, line)] in file order; findings for malformed ones."""
    findings: list[Finding] = []
    reqs = []
    for page in sorted(spec_dir.glob("*.md")) if spec_dir.is_dir() else []:
        text = page.read_text()
        rel = str(page.relative_to(root))
        matches = list(HEADING_RE.finditer(text))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[m.end():end]
            fields = {}
            order = []
            for row in re.finditer(r"^\| `([a-z ]+)` \| (.*?) \|\s*$", block, re.MULTILINE):
                fields[row.group(1)] = row.group(2).strip()
                order.append(row.group(1))
            where = f"{rel}: {m.group(1)}"
            if order != FIELDS:
                findings.append(Finding(where, f"the field table must have exactly {FIELDS} in that order, found {order}"))
                fields = None
            reqs.append((rel, m.group(1), m.group(3), fields, block))
        for stray in re.finditer(r"^### (PROC-\S+).*$", text, re.MULTILINE):
            if not HEADING_RE.match(stray.group(0)):
                findings.append(Finding(f"{rel}: {stray.group(1)}", "heading is not `### PROC-AREA-NNN — title {#proc-area-nnn}`"))
    return reqs, findings


def check_spec(spec_dir: Path, ops_dir: Path, root: Path):
    reqs, findings = parse_requirements(spec_dir, root)
    seen: dict = {}
    for rel, rid, anchor, fields, block in reqs:
        where = f"{rel}: {rid}"
        if anchor != rid.lower():
            findings.append(Finding(where, f"anchor `{anchor}` must be `{rid.lower()}`"))
        if rid in seen:
            findings.append(Finding(where, f"duplicate id (also in {seen[rid]})"))
        seen[rid] = rel
        if fields is None:
            continue
        status = fields["status"].strip("`")
        if status not in STATUSES:
            findings.append(Finding(where, f"`status` is `{status}`; use one of {sorted(STATUSES)}"))
        for name in ("implemented by", "verified by"):
            if not fields[name].strip():
                findings.append(Finding(where, f"`{name}` is empty; say `none` and why if nothing applies"))
        if status == "planned" and not ISSUE_RE.search(block):
            findings.append(Finding(where, "a `planned` requirement must name its tracking issue (`metel-core#N`)"))
        if status in ("implemented", "partial") and fields["implemented by"].strip().lower().startswith("none"):
            findings.append(Finding(where, f"`{status}` but `implemented by` is `none`"))
    ids = set(seen)
    # every PROC id mentioned anywhere under operations/ resolves
    for path in sorted(ops_dir.rglob("*.md")):
        text = path.read_text()
        for m in re.finditer(ID_RE, text):
            if m.group(0) not in ids:
                findings.append(Finding(f"{path.relative_to(root)}", f"mentions `{m.group(0)}`, which is not a requirement"))
    return reqs, ids, findings


# ---------------------------------------------------------------- paths
def reachable_repos(workspace: Path, docs_root: Path) -> dict[str, Path]:
    """repository name -> root, for the repositories that can be read from here."""
    found = {"metel-docs": docs_root}
    for name in REPOS:
        if name in found:
            continue
        candidate = workspace / name
        if candidate.is_dir():
            found[name] = candidate
    # a metel-core checkout that embeds this docs repository as `docs/`
    parent = docs_root.parent
    if (parent / ".gitmodules").is_file() and (parent / "metel-frontend").is_dir():
        found.setdefault("metel-core", parent)
    return found


def check_paths(reqs, repos: dict[str, Path], root: Path):
    """(errors, warnings): a path in `metel-docs` that is gone is an error; a path in another
    repository is a warning, since the change that removed it was made there and the specification
    can only follow (the circularity of ADR-0064)."""
    findings: list[Finding] = []
    warnings: list[Finding] = []
    for rel, rid, _, fields, _ in reqs:
        if fields is None:
            continue
        for m in REPO_PATH_RE.finditer(fields["implemented by"]):
            repo, path = m.group(1), m.group(2).split("::")[0].rstrip(".,;:")
            base = repos.get(repo)
            if base is None or any(c in path for c in "*<>"):
                continue
            if not (base / path).exists():
                target = findings if repo == "metel-docs" else warnings
                target.append(Finding(f"{rel}: {rid}", f"`implemented by` names `{repo}/{path}`, which does not exist"))
    return findings, warnings


# ---------------------------------------------------------------- discovery
def discover(repo: str, base: Path) -> list[str]:
    """Operational assets of a repository, as paths relative to its root."""
    out: set[str] = set()

    def add_files(rel_dir: str, patterns, skip_tests=True):
        d = base / rel_dir
        if not d.is_dir():
            return
        for pat in patterns:
            for f in d.glob(pat):
                if f.is_file() and not (skip_tests and f.name.startswith("test_")) and not f.name.endswith(".test.mjs"):
                    out.add(str(f.relative_to(base)))

    add_files(".github/workflows", ["*.yml", "*.yaml"])
    add_files(".github/scripts", ["*"])
    if repo == "metel-core":
        add_files("tools", ["*.py", "*.sh"])
        add_files(".githooks", ["*"])
        add_files(".claude/commands", ["*.md"])
        for crate_bin in sorted(base.glob("*/src/bin")):
            add_files(str(crate_bin.relative_to(base)), ["*.rs"])
    elif repo == "metel-docs":
        add_files("architecture/tools", ["*.py"])
        add_files("rfcs/tools", ["*.py"])
        add_files(".githooks", ["*"])
        if (base / "tools" / "mdx-check-site").is_dir():
            out.add("tools/mdx-check-site")
    elif repo == "metel-website":
        add_files("scripts", ["*.mjs"])
    elif repo == "metel-docs-internal":
        add_files("reports/strategy/tools", ["*.py"])
    return sorted(out)


def parse_inventory(path: Path):
    """[(repo, [asset tokens], requirement-cell text, line)]"""
    rows = []
    if not path.is_file():
        return rows
    for n, line in enumerate(path.read_text().splitlines(), 1):
        m = re.match(r"^\| `(metel-[a-z-]+)` \| (.*?) \| (.*?) \|\s*$", line)
        if m:
            rows.append((m.group(1), re.findall(r"`([^`]+)`", m.group(2)), m.group(3), n))
    return rows


def mapped(asset: str, repo: str, rows) -> bool:
    """An asset is listed when a backticked token of one of the repository's rows ends the way
    the asset path does: the full path, or its name when a row groups several in one directory."""
    base = asset.rsplit("/", 1)[-1]
    for r, tokens, _, _ in rows:
        if r != repo:
            continue
        for t in tokens:
            t = t.split(" ")[0]
            if t == asset or t.endswith("/" + base) or t == base or asset.endswith("/" + t):
                return True
    return False


def check_inventory(ids: set, repos: dict[str, Path], inventory: Path, root: Path):
    errors: list[Finding] = []
    warnings: list[Finding] = []
    rows = parse_inventory(inventory)
    rel = str(inventory.relative_to(root)) if inventory.exists() else "operations/inventory.md"
    for repo, tokens, req_cell, line in rows:
        where = f"{rel}:{line}"
        if repo not in REPOS:
            errors.append(Finding(where, f"unknown repository `{repo}`"))
        refs = re.findall(ID_RE, req_cell)
        marked = re.search(r"\blocal\b|process document|authority for", req_cell)
        if not refs and not marked:
            errors.append(Finding(where, "row names no requirement and is not marked `local` or a process document"))
    for repo, base in sorted(repos.items()):
        for asset in discover(repo, base):
            if not mapped(asset, repo, rows):
                target = errors if repo == "metel-docs" else warnings
                target.append(Finding(f"{repo}/{asset}", "operational asset is not in operations/inventory.md; add a row (or mark it `local`)"))
    # the reverse: a listed asset that no longer exists (repositories we can read only)
    for repo, tokens, _, line in rows:
        base = repos.get(repo)
        if base is None:
            continue
        for t in tokens:
            token = t.split(" ")[0]
            if "/" not in token and "." not in token:
                continue  # a hook or command name inside a group, not a path
            if token.startswith(("--", "-")):
                continue
            candidates = [base / token]
            if not (base / token).exists():
                hit = any((base / d / token).exists() for d in
                          [".github/workflows", ".githooks", ".claude/commands", ".github/scripts", "tools", "architecture/tools", "rfcs/tools", "scripts", "reports/strategy/tools", "metel-frontend/src/bin"])
                if not hit and not any(base.glob(f"**/{token}")) and "*" not in token:
                    (errors if repo == "metel-docs" else warnings).append(Finding(f"{rel}:{line}", f"lists `{token}` under `{repo}`, which does not exist"))
    return errors, warnings


# ---------------------------------------------------------------- markers
def check_markers(repos: dict[str, Path], ids: set):
    findings: list[Finding] = []
    for repo, base in repos.items():
        for asset in discover(repo, base):
            f = base / asset
            if not f.is_file():
                continue
            try:
                text = f.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for m in MARKER_RE.finditer(text):
                if m.group(1) not in ids:
                    findings.append(Finding(f"{repo}/{asset}", f"`# Process: {m.group(1)}` names a requirement that does not exist"))
    return findings


def run(docs_root: Path | None = None, workspace: Path | None = None):
    docs_root = docs_root or DOCS_ROOT
    ops = docs_root / "operations"
    workspace = workspace or docs_root.parent
    repos = reachable_repos(workspace, docs_root)
    reqs, ids, errors = check_spec(ops / "spec", ops, docs_root)
    path_errors, path_warnings = check_paths(reqs, repos, docs_root)
    errors += path_errors
    inv_errors, warnings = check_inventory(ids, repos, ops / "inventory.md", docs_root)
    errors += inv_errors
    warnings = path_warnings + warnings
    errors += check_markers(repos, ids)
    rows = parse_inventory(ops / "inventory.md")
    local = {t.split(" ")[0].rsplit("/", 1)[-1] for _, tokens, cell, _ in rows if re.search(r"\blocal\b", cell) for t in tokens}
    flow_errors, flow_warnings = check_flows(ops, docs_root, reqs, ids, {r: discover(r, b) for r, b in repos.items()}, repos, REPOS, local)
    errors += flow_errors
    warnings += flow_warnings
    skipped = [r for r in REPOS if r not in repos]
    return errors, warnings, skipped, len(reqs)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="exit 1 on any finding")
    p.add_argument("--strict", action="store_true", help="treat warnings as findings (a release)")
    p.add_argument("--workspace", type=Path, help="directory holding sibling repository checkouts")
    args = p.parse_args()
    errors, warnings, skipped, count = run(workspace=args.workspace)
    print(f"Operations Specification: {count} requirement(s) checked.")
    if skipped:
        print(f"Repositories not reachable from here, so their assets were not checked: {', '.join(skipped)}.")
    for w in warnings:
        print(f"warning: {w}")
    if args.strict:
        errors, warnings = errors + warnings, []
    if warnings:
        print(f"{len(warnings)} warning(s); `--strict` (a release) treats them as findings.")
    if not errors:
        print("No findings.")
        return 0
    print(f"{len(errors)} finding(s):")
    for e in errors:
        print(f"  - {e}")
    return 1 if args.check or args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
