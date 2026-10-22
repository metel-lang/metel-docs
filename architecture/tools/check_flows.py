#!/usr/bin/env python3
"""Staleness checks for the Operations Specification's flow diagrams (metel-core#1534).

`operations/flows.md` draws the implementation flow and the release flow as Mermaid. A node names
the requirement it depicts (`PROC-CI-001`) and the asset that performs it (`ci.yml`, `/cut-release`).
These checks keep the pictures tied to the repositories and to the requirements:

- a node cites a requirement or an asset that does not exist (dangling);
- a workflow or slash command appears in no node and is not excused under "Not drawn" (undrawn);
- an `implemented` or `partial` requirement is cited by no node and is not excused (undrawn);
- a node says `manual` for a workflow that also runs on events, or omits it for one that only
  runs when dispatched (drift).

Severity follows ADR-0064: what is wrong with the change fails; what may be only stale is a warning
that `--strict` (a release) turns into a finding. A reference that cannot be resolved is an error
only when every repository is readable; otherwise the asset may live in one that is not, and nothing
is said (the notice of repositories that were not checked already covers it).
"""
from __future__ import annotations

import re
from pathlib import Path

from check_architecture import Finding

ID_RE = r"PROC-[A-Z]+-\d{3}"
MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
NODE_RE = re.compile(r'\b([A-Za-z_]\w*)\s*(?:\[\[|\[\(|\(\[|\(\(|\[|\(|\{)\s*"((?:[^"\\]|\\.)*)"')
FILE_RE = re.compile(r"(?<![\w.-])((?:[\w.-]+/)*[\w-]+\.(?:yml|yaml|sh|py|mjs))\b")
COMMAND_RE = re.compile(r"(?:(?<=\s)|(?<=>)|^)/([a-z][a-z-]*)(?![\w/-])")
NOT_DRAWN_ROW_RE = re.compile(r"^\| `([^`]+)` \| (.+?) \|\s*$")


def parse_nodes(text: str):
    """[(node id, label text)] over every Mermaid block of the page."""
    nodes = []
    for block in MERMAID_RE.findall(text):
        for m in NODE_RE.finditer(block):
            nodes.append((m.group(1), m.group(2).replace("\\n", " ").replace("<br/>", " ")))
    return nodes


def parse_not_drawn(text: str) -> dict[str, str]:
    """`id or asset` -> reason, from the table under the `## Not drawn` heading."""
    m = re.search(r"^## Not drawn\s*$(.*?)(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            r = NOT_DRAWN_ROW_RE.match(line)
            if r and r.group(1) not in ("Item",):
                out[r.group(1)] = r.group(2)
    return out


def workflow_triggers(text: str) -> set[str]:
    """The event names in a workflow's `on:`; empty when they cannot be read."""
    m = re.search(r"^[\"']?on[\"']?:[ \t]*(.*)$((?:\n(?:[ \t].*|))*)", text, re.MULTILINE)
    if not m:
        return set()
    inline, block = m.group(1).strip(), m.group(2)
    if inline:
        return set(re.findall(r"[a-z_]+", inline))
    return set(re.findall(r"^  ([a-z_]+):", block, re.MULTILINE))


def check_flows(ops: Path, root: Path, reqs, ids: set, assets: dict[str, list[str]], repos: dict, all_repos: list[str], local_assets: set[str]):
    """(errors, warnings). `assets` maps repository -> discovered asset paths; `reqs` is the
    parse_requirements list; `local_assets` holds the names the inventory marks `local`."""
    errors: list[Finding] = []
    warnings: list[Finding] = []
    page = ops / "flows.md"
    rel = str(page.relative_to(root)) if page.is_relative_to(root) else str(page)
    if not page.is_file():
        return [Finding(rel, "the flow diagrams page is missing")], []
    text = page.read_text()
    nodes = parse_nodes(text)
    if not nodes:
        errors.append(Finding(rel, "no Mermaid diagram with nodes was found"))
    excused = parse_not_drawn(text)
    complete = all(r in repos for r in all_repos)
    unresolved = errors if complete else []  # unverifiable, not stale, while a repository cannot be read

    by_name: dict[str, tuple[str, str]] = {}
    for repo, paths in assets.items():
        for p in paths:
            by_name.setdefault(p.rsplit("/", 1)[-1], (repo, p))
    command_names = {n[:-3] for n in by_name if n.endswith(".md") and by_name[n][1].startswith(".claude/commands/")}

    drawn_ids: set[str] = set()
    drawn_assets: set[str] = set()
    for node, label in nodes:
        where = f"{rel}: node {node}"
        for rid in re.findall(ID_RE, label):
            drawn_ids.add(rid)
            if rid not in ids:
                errors.append(Finding(where, f"cites `{rid}`, which is not a requirement"))
        files = [f.rsplit("/", 1)[-1] for f in FILE_RE.findall(label)]
        cmds = COMMAND_RE.findall(label)
        for name in files:
            drawn_assets.add(name)
            if name not in by_name:
                unresolved.append(Finding(where, f"names `{name}`, which is not a workflow, script or tool of any readable repository"))
        for name in cmds:
            drawn_assets.add(name + ".md")
            if name not in command_names:
                unresolved.append(Finding(where, f"names the command `/{name}`, which does not exist"))
        workflows = [n for n in files if n.endswith((".yml", ".yaml")) and n in by_name]
        if len(workflows) == 1:
            repo, path = by_name[workflows[0]]
            events = workflow_triggers((repos[repo] / path).read_text()) if repo in repos else set()
            manual_only = events == {"workflow_dispatch"}
            says_manual = bool(re.search(r"\bmanual", label, re.IGNORECASE))
            if events and manual_only != says_manual:
                what = "runs only when dispatched but the node does not say `manual`" if manual_only else "also runs on events but the node says `manual`"
                warnings.append(Finding(where, f"`{workflows[0]}` {what}"))

    for item in excused:
        if re.fullmatch(ID_RE, item) and item not in ids:
            errors.append(Finding(f"{rel}: Not drawn", f"excuses `{item}`, which is not a requirement"))

    for repo, paths in sorted(assets.items()):
        for p in paths:
            name = p.rsplit("/", 1)[-1]
            is_flow = p.startswith(".github/workflows/") or p.startswith(".claude/commands/")
            if not is_flow or name in drawn_assets or name in local_assets:
                continue
            if name in excused or f"/{name.removesuffix('.md')}" in excused:
                continue
            (errors if repo == "metel-docs" else warnings).append(
                Finding(f"{repo}/{p}", "appears in no flow diagram; draw it or list it under `## Not drawn` in operations/flows.md"))

    for page_rel, rid, _, fields, _ in reqs:
        if fields is None or rid in drawn_ids or rid in excused:
            continue
        if re.sub(r"[`\s]", "", fields["status"]) in ("implemented", "partial"):
            warnings.append(Finding(f"{page_rel}: {rid}", "is cited by no flow diagram node; draw it or list it under `## Not drawn` in operations/flows.md"))
    return errors, warnings
