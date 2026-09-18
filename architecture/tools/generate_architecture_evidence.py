#!/usr/bin/env python3
"""Render Architecture Spec evidence from citations owned by metel-core.

``arch-implements`` belongs immediately before the Rust item that implements a
claim. ``arch-verifies`` belongs immediately before a unit test; integration
fixture sidecars use ``[options] arch_verifies``. The generated fields below
are deliberately the only implementation and verification inventories in the
Atlas: editing a rendered cell is overwritten, and ``--check`` rejects it.
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


@dataclass(frozen=True)
class Citation:
    path: Path
    item: str | None
    line: int


def git_ref(core: Path) -> str:
    return subprocess.check_output(["git", "-C", str(core), "rev-parse", "HEAD"], text=True).strip()


def following_item(text: str, start: int, test_only: bool, path: Path, line: int) -> str:
    """Resolve an annotation without allowing it to silently skip an item."""
    remainder = text[start:]
    item = ITEM.search(remainder)
    if not item:
        raise ValueError(f"{path}:{line}: citation has no following Rust item")
    between = remainder[:item.start()]
    if test_only and "#[test]" not in between:
        raise ValueError(f"{path}:{line}: arch-verifies must precede a #[test] function")
    return item.group(1)


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
            item = following_item(text, match.end(), kind == "verifies", path, line)
            rel = path.relative_to(core)
            citation = Citation(rel, item, line)
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
                found[claim]["verifies"].append(Citation(path.relative_to(core), None, 1))
    return found


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


def regenerate(spec_dir: Path, evidence, check: bool, core_ref: str):
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
        findings = regenerate(DOCS / "architecture/spec", citations(args.core), args.check, args.core_ref or git_ref(args.core))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        findings = [str(error)]
    if findings:
        print("\n".join(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
