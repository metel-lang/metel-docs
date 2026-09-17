#!/usr/bin/env python3
"""Architecture integrity checker (ADR-0055 §6, metel-core#1162).

Validates `arch-*` records in `architecture/spec/*.md` and `LIMIT-*` records
in `architecture/limitations/*.md`: ID well-formedness and uniqueness,
cross-reference resolution (`specified by` / `scope` anchors, `affects`
targets), required-field presence, the disposition rules ADR-0055 §4
states in prose (an `accepted` limitation needs a review date; a `resolved`
one needs real exit evidence, not a placeholder), and that an `arch-*`
requirement's `related` field never cites a since-superseded ADR (reads
`architecture/decisions/*.md`'s own `status:`/`supersedes:` fields, both
live frontmatter shapes in the corpus, to know which ADRs are superseded
and by what) -- `LIMIT-*`'s `discovered_by` is deliberately exempt from this
one check, since citing the ADR that originally documented a now-resolved
limitation is expected even after that ADR is itself superseded.

Also validates `architecture/decisions/*.md`'s own frontmatter structure
directly: every ADR has real YAML frontmatter (not a plain `**Status:**`
header) with non-empty `id`/`title`/`date`/`status`, `id` matching its own
filename exactly, and `status` either a known value or a well-formed
"superseded by ADR-NNNN" -- the structural backbone `#1172`'s hand-done
backfill depends on staying true, not just a one-time state to have
reached.

This generalizes `rfcs/tools/rfc.py`'s existing anchor/backlink/coverage
machinery rather than introducing new tooling -- per ADR-0055's explicit
deferral of a relational-schema-plus-Datalog composition (the prior-art
survey's own recommendation, `architecture-atlas-prior-art-survey.html` §7)
until real reconciliation-rule volume justifies it. It reports findings; it
never silently mutates a disposition or any other field -- a human triages
every finding.

Fixture-sidecar `arch = [...]` cross-checking is a documented no-op here for
the same reason `rfc-check.yml` already documents for RFC-section fixture
coverage: the fixture corpus lives in `metel-interpreter/tests`, in
metel-core, one level up from this repo when it's embedded as a submodule --
a bare metel-docs checkout structurally can't reach it. It degrades to an
informational skip, not a failure.

Usage:
  architecture/tools/check_architecture.py            # print a report
  architecture/tools/check_architecture.py --check     # CI gate: exit 1 on any finding
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO_ROOT / "architecture" / "spec"
LIMITATIONS_DIR = REPO_ROOT / "architecture" / "limitations"
DECISIONS_DIR = REPO_ROOT / "architecture" / "decisions"

ARCH_ID_RE = re.compile(r"^arch\.[a-z0-9][a-z0-9.\-]*\.requirement-\d+$")
LIMIT_ID_RE = re.compile(r"^LIMIT-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}$")
STATUS_VALUES = {"implemented", "partial", "planned", "superseded", "retired"}
DISPOSITION_VALUES = {"known", "accepted", "mitigated", "planned", "resolved", "superseded"}

SECTION_ANCHOR_RE = re.compile(r"^#\s+.+\{#([a-z0-9][a-z0-9-]*)\}\s*$", re.MULTILINE)
REQUIREMENT_RE = re.compile(
    r"^#####\s+Requirement\s+\{#([a-z0-9.\-]+)\}\s*\n(.*?)(?=^#####\s+Requirement|\Z)",
    re.MULTILINE | re.DOTALL,
)
FIELD_ROW_RE = re.compile(r"^\|\s*`([a-z ]+)`\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)
KNOWN_LIMITATIONS_LINK_RE = re.compile(r"\[`(LIMIT-[A-Z0-9\-]+)`\]\(([^)]+)\)")

FRONTMATTER_KEY_RE = re.compile(
    r'^([a-z_]+):\s*(?:"((?:[^"\\]|\\.)*)"|(\S.*?)|)\s*$', re.MULTILINE
)
AFFECTS_ITEM_RE = re.compile(r"^-\s+`([A-Za-z0-9.\-]+)`", re.MULTILINE)

ADR_REF_RE = re.compile(r"\bADR-(\d{4})\b", re.IGNORECASE)
# Two live formats in the corpus: YAML `status: superseded by ADR-0029` /
# `supersedes: adr-0019`, and pre-frontmatter `**Status:** Superseded by ADR-0028`.
YAML_SUPERSEDED_BY_RE = re.compile(r"^status:\s*superseded by\s+(?:ADR-|adr-)?(\d{4})", re.MULTILINE | re.IGNORECASE)
YAML_SUPERSEDES_RE = re.compile(r"^supersedes:\s*(?:ADR-|adr-)?(\d{4})", re.MULTILINE | re.IGNORECASE)
PLAIN_SUPERSEDED_BY_RE = re.compile(r"^\*\*Status:\*\*\s*Superseded by\s+ADR-(\d{4})", re.MULTILINE | re.IGNORECASE)

ADR_FILENAME_ID_RE = re.compile(r"^(adr-\d{4})-")
ADR_STATUS_VALUES = {"accepted", "active", "implemented", "proposed", "historical", "retired"}
ADR_SUPERSEDED_STATUS_RE = re.compile(r"^superseded by (?:ADR-|adr-)\d{4}$", re.IGNORECASE)


class Finding:
    def __init__(self, source: str, message: str):
        self.source = source
        self.message = message

    def __str__(self) -> str:
        return f"{self.source}: {self.message}"


def frontmatter_and_body(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_idx = len(lines)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    fm_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])
    fm: dict = {}
    for m in FRONTMATTER_KEY_RE.finditer(fm_text):
        key = m.group(1)
        value = m.group(2) if m.group(2) is not None else m.group(3)
        if value is None:
            value = ""
        value = value.strip()
        if value == "null":
            value = None
        fm[key] = value
    return fm, body


def parse_spec_file(path: Path):
    text = path.read_text()
    section_ids = set(SECTION_ANCHOR_RE.findall(text))
    requirements = []
    for m in REQUIREMENT_RE.finditer(text):
        req_id = m.group(1)
        block = m.group(2)
        fields = {}
        for fm_field in FIELD_ROW_RE.finditer(block):
            fields[fm_field.group(1).strip()] = fm_field.group(2).strip()
        requirements.append((req_id, fields))
    kl_links = []
    kl_idx = text.find("## Known limitations")
    if kl_idx != -1:
        kl_links = KNOWN_LIMITATIONS_LINK_RE.findall(text[kl_idx:])
    return section_ids, requirements, kl_links


def parse_limitation_file(path: Path):
    text = path.read_text()
    fm, body = frontmatter_and_body(text)
    affects = []
    affects_idx = body.find("## Affects")
    if affects_idx != -1:
        next_heading = body.find("\n## ", affects_idx + 1)
        segment = body[affects_idx : next_heading if next_heading != -1 else len(body)]
        affects = AFFECTS_ITEM_RE.findall(segment)
    resolution_text = ""
    res_idx = body.find("## Resolution")
    if res_idx != -1:
        resolution_text = body[res_idx + len("## Resolution") :].strip()
    return fm, affects, resolution_text


def load_adr_supersessions(decisions_dir: Path) -> dict:
    """{'0027': '0039', ...} -- normalized 4-digit ADR number -> the ADR that
    supersedes it, if known (empty string if superseded but no replacement
    was stated). Reads both live frontmatter shapes in the corpus (YAML
    `status:`/`supersedes:`, and pre-frontmatter `**Status:**`), and cross-fills
    from whichever side states the relationship -- a superseded ADR does not
    always say so about itself (see architecture/decisions/TRIAGE.md)."""
    superseded: dict = {}
    if not decisions_dir.is_dir():
        return superseded

    for path in sorted(decisions_dir.glob("adr-*.md")):
        m = re.match(r"adr-(\d{4})", path.name)
        if not m:
            continue
        own_number = m.group(1)
        text = path.read_text()

        by_match = YAML_SUPERSEDED_BY_RE.search(text) or PLAIN_SUPERSEDED_BY_RE.search(text)
        if by_match:
            superseded.setdefault(own_number, by_match.group(1))

        for m2 in YAML_SUPERSEDES_RE.finditer(text):
            superseded.setdefault(m2.group(1), own_number)

    return superseded


def check_adr_frontmatter(decisions_dir: Path, repo_root: Path) -> list:
    """Every architecture/decisions/adr-*.md has real YAML frontmatter with
    non-empty id/title/date/status, id matching its own filename exactly
    (catches e.g. an uppercase ADR-0025 id on a lowercase-filed file, or a
    legacy id: decision-N left over from before this convention), and a
    status that's either one of ADR_STATUS_VALUES or a well-formed
    "superseded by ADR-NNNN" -- not a general "did this get backfilled"
    survey but a real, CI-enforced structural check (#1172 did the backfill
    by hand; this is what stops it from silently rotting)."""
    findings: list = []
    if not decisions_dir.is_dir():
        return findings

    for path in sorted(decisions_dir.glob("adr-*.md")):
        rel = path.relative_to(repo_root)
        text = path.read_text()

        if not text.lstrip().startswith("---"):
            findings.append(Finding(str(rel), "no YAML frontmatter (file does not start with `---`)"))
            continue

        fm, _ = frontmatter_and_body(text)

        for required_field in ("id", "title", "date", "status"):
            if not fm.get(required_field):
                findings.append(Finding(str(rel), f"frontmatter missing or empty `{required_field}`"))

        expected_id_match = ADR_FILENAME_ID_RE.match(path.name)
        expected_id = expected_id_match.group(1) if expected_id_match else None
        fm_id = fm.get("id", "")
        if expected_id and fm_id and fm_id != expected_id:
            findings.append(
                Finding(str(rel), f"frontmatter `id: {fm_id}` does not match filename (expected `{expected_id}`)")
            )

        status = fm.get("status", "")
        if status and status not in ADR_STATUS_VALUES and not ADR_SUPERSEDED_STATUS_RE.match(status):
            findings.append(
                Finding(
                    str(rel),
                    f"status `{status}` is not one of {sorted(ADR_STATUS_VALUES)} or a well-formed "
                    f"\"superseded by ADR-NNNN\"",
                )
            )

    return findings


def resolve_scope_anchor(scope: str, all_section_ids_by_file: dict, repo_root: Path) -> bool:
    if "#" not in scope:
        return False
    file_part, anchor = scope.split("#", 1)
    candidate = repo_root / file_part
    if not candidate.exists():
        return False
    return anchor in all_section_ids_by_file.get(candidate.resolve(), set())


def run_checks(
    repo_root: Path = REPO_ROOT,
    spec_dir: Path = None,
    limitations_dir: Path = None,
    decisions_dir: Path = None,
) -> list[Finding]:
    spec_dir = spec_dir or (repo_root / "architecture" / "spec")
    limitations_dir = limitations_dir or (repo_root / "architecture" / "limitations")
    decisions_dir = decisions_dir or (repo_root / "architecture" / "decisions")
    findings: list[Finding] = []
    superseded_adrs = load_adr_supersessions(decisions_dir)
    findings.extend(check_adr_frontmatter(decisions_dir, repo_root))

    if not spec_dir.is_dir():
        findings.append(Finding(str(spec_dir), "directory does not exist"))
        return findings

    spec_files = sorted(spec_dir.glob("*.md"))
    limitation_files = sorted(limitations_dir.glob("*.md")) if limitations_dir.is_dir() else []

    all_section_ids_by_file: dict = {}
    all_arch_ids: dict = {}
    kl_links_by_file: dict = {}

    for path in spec_files:
        section_ids, requirements, kl_links = parse_spec_file(path)
        all_section_ids_by_file[path.resolve()] = section_ids
        kl_links_by_file[path] = kl_links

        rel = path.relative_to(repo_root)
        if not section_ids:
            findings.append(Finding(str(rel), "no top-level `{#section-id}` heading anchor found"))

        for req_id, fields in requirements:
            if req_id in all_arch_ids:
                findings.append(
                    Finding(
                        str(rel),
                        f"duplicate arch-* id `{req_id}` (also in {all_arch_ids[req_id]})",
                    )
                )
            else:
                all_arch_ids[req_id] = str(rel)

            if not ARCH_ID_RE.match(req_id):
                findings.append(Finding(str(rel), f"`{req_id}` does not match the arch.<path>.requirement-<N> shape"))

            for required_field in ("status", "owner", "specified by", "implements", "verified by", "related"):
                if not fields.get(required_field):
                    findings.append(Finding(str(rel), f"`{req_id}`: missing or empty `{required_field}` field"))

            status = fields.get("status", "").strip("`")
            if status and status not in STATUS_VALUES:
                findings.append(Finding(str(rel), f"`{req_id}`: status `{status}` is not one of {sorted(STATUS_VALUES)}"))

            specified_by = fields.get("specified by", "").strip("`")
            if specified_by:
                anchor = specified_by.lstrip("#")
                if anchor not in section_ids:
                    findings.append(
                        Finding(
                            str(rel),
                            f"`{req_id}`: `specified by` anchor `{specified_by}` does not resolve within this file",
                        )
                    )

            related = fields.get("related", "")
            for adr_match in ADR_REF_RE.finditer(related):
                number = adr_match.group(1)
                if number in superseded_adrs:
                    replacement = superseded_adrs[number]
                    by_text = f" by ADR-{replacement}" if replacement else ""
                    findings.append(
                        Finding(
                            str(rel),
                            f"`{req_id}`: `related` cites ADR-{number}, which is superseded{by_text}",
                        )
                    )

    all_limit_ids: dict = {}
    limitation_records = []

    for path in limitation_files:
        rel = path.relative_to(repo_root)
        fm, affects, resolution_text = parse_limitation_file(path)
        limitation_records.append((path, fm, affects, resolution_text))

        for required_field in ("id", "title", "scope", "owner", "discovered_by", "disposition"):
            if not fm.get(required_field):
                findings.append(Finding(str(rel), f"missing or empty frontmatter field `{required_field}`"))

        record_id = fm.get("id", "")
        expected_slug = record_id.lower() + ".md"
        if record_id and path.name != expected_slug:
            findings.append(Finding(str(rel), f"filename does not match `id: {record_id}` (expected `{expected_slug}`)"))

        if record_id:
            if not LIMIT_ID_RE.match(record_id):
                findings.append(Finding(str(rel), f"`{record_id}` does not match the LIMIT-<AREA>-<NNN> shape"))
            if record_id in all_limit_ids:
                findings.append(
                    Finding(str(rel), f"duplicate LIMIT-* id `{record_id}` (also in {all_limit_ids[record_id]})")
                )
            else:
                all_limit_ids[record_id] = str(rel)

        disposition = fm.get("disposition", "")
        if disposition and disposition not in DISPOSITION_VALUES:
            findings.append(
                Finding(str(rel), f"disposition `{disposition}` is not one of {sorted(DISPOSITION_VALUES)}")
            )

        if disposition == "accepted" and not fm.get("review"):
            findings.append(
                Finding(str(rel), "disposition `accepted` requires a `review` date (ADR-0055 §4: an accepted temporary limitation requires a review-by date)")
            )

        if disposition == "resolved":
            if not resolution_text or resolution_text.lower().startswith("none yet"):
                findings.append(
                    Finding(str(rel), "disposition `resolved` requires real exit evidence in `## Resolution`, not a placeholder")
                )

        scope = fm.get("scope", "")
        if scope and not resolve_scope_anchor(scope, all_section_ids_by_file, repo_root):
            findings.append(Finding(str(rel), f"`scope: {scope}` does not resolve to a real file+anchor"))

        if not affects:
            findings.append(Finding(str(rel), "`## Affects` lists no targets"))

    # Cross-file: every `affects` entry, and every "Known limitations" link,
    # must resolve to a real id that actually exists somewhere in the corpus.
    for path, fm, affects, _ in limitation_records:
        rel = path.relative_to(repo_root)
        for target in affects:
            if target not in all_arch_ids and target not in all_limit_ids:
                findings.append(Finding(str(rel), f"`affects` target `{target}` does not exist"))

    for path, kl_links in kl_links_by_file.items():
        rel = path.relative_to(repo_root)
        for limit_id, link_path in kl_links:
            if limit_id not in all_limit_ids:
                findings.append(Finding(str(rel), f"Known-limitations link `{limit_id}` does not exist"))
            target = (path.parent / link_path).resolve()
            if not target.exists():
                findings.append(Finding(str(rel), f"Known-limitations link target `{link_path}` does not exist on disk"))

    return findings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="CI gate: exit 1 on any finding")
    args = p.parse_args()

    findings = run_checks()

    spec_count = len(list(SPEC_DIR.glob("*.md"))) if SPEC_DIR.is_dir() else 0
    limit_count = len(list(LIMITATIONS_DIR.glob("*.md"))) if LIMITATIONS_DIR.is_dir() else 0
    print(f"Checked {spec_count} spec file(s), {limit_count} limitation record(s).")
    print("Fixture-sidecar arch=[...] cross-checking: skipped (fixture corpus lives in metel-core, not reachable from a bare metel-docs checkout -- same degrade rfc-check.yml already documents for RFC coverage).")

    if not findings:
        print("No findings.")
        return 0

    print(f"\n{len(findings)} finding(s):")
    for f in findings:
        print(f"  - {f}")

    if args.check:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
