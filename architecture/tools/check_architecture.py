#!/usr/bin/env python3
"""Architecture integrity checker (ADR-0055 §6, metel-core#1162).

Validates `arch-*` records in `architecture/spec/*.md` and `LIMIT-*` records
in `architecture/limitations/*.md` (and, ADR-0057, `GAP-*` records in
`architecture/gaps/*.md`, which describe gaps in the Language Spec and carry
extra rules: area/scope agreement, `spec.*`/RFC `affects`, RFC-backed
`resolved`/`planned`, and reciprocal `LIMIT-*` links): ID well-formedness and uniqueness,
cross-reference resolution (`specified by` / `scope` anchors, `affects`
targets), required-field presence (including `last_reviewed`, metel-core#1191
-- shape only here; whether the cited code actually moved on since that
commit needs metel-core's git history, checked by
`generate_architecture_evidence.py` instead), the disposition rules ADR-0055
§4 states in prose (an `accepted` limitation needs a review date; a `resolved`
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

Every relative Markdown link under `architecture/` must resolve to a real file
and, when it carries a `#fragment`, a real anchor in that file
(metel-core#1180): a broken cross-section link is otherwise only a warning in
the website build.

The published Architecture Spec is durable system documentation, not a task
log. Its overview and section prose may cite an issue or ADR where that adds
architectural context, but must not narrate a completed milestone, a next
step, or an unaudited session as if it were current behavior.

A `LIMIT-*` / `GAP-*` record may carry `planned_for: vX.Y.Z` and `rfc: RFC-NNNN[, ...]`,
the release and RFC(s) for pending work; a Language Spec chapter states a limit as a
one-line marker, `> **Gap** GAP-X-001` or `> **Limitation** LIMIT-X-001`, that cites an
existing active record, and the site renders the record's summary and these fields
into it (metel-core#1235). Only the checks are here; the chapters convert in a later step.

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
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO_ROOT / "architecture" / "spec"
LIMITATIONS_DIR = REPO_ROOT / "architecture" / "limitations"
DECISIONS_DIR = REPO_ROOT / "architecture" / "decisions"
GAPS_DIR = REPO_ROOT / "architecture" / "gaps"
LANGUAGE_SPEC_DIR = REPO_ROOT / "reference" / "spec"
RFCS_DIR = REPO_ROOT / "rfcs"

ARCH_ID_RE = re.compile(r"^arch\.[a-z0-9][a-z0-9.\-]*\.requirement-\d+$")
LIMIT_ID_RE = re.compile(r"^LIMIT-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}$")
# ADR-0057: `GAP-*` records describe a gap in what the Language Spec says; the
# area is the Language Spec chapter (its file stem, uppercased).
GAP_AREAS = ("TYPES", "EXPRESSIONS", "FUNCTIONS", "DECLARATIONS", "MODULES", "OWNERSHIP", "RUNTIME", "LEXICAL")
GAP_ID_RE = re.compile(r"^GAP-(" + "|".join(GAP_AREAS) + r")-\d{3}$")
SPEC_RULE_ID_RE = re.compile(r"^spec\.[a-z0-9][a-z0-9.\-]*$")
RFC_REF_RE = re.compile(r"^(?:RFC|rfc)-(\d{4})$")
RFC_LANDED_STAGES = {"3-integrated", "4-implemented"}
# The `## Known limitations` / `## Known gaps` sections are rendered by the website
# from the records themselves; the page holds only the heading and this marker
# (metel-core#1182). The list is never written into the markdown.
LIMITATIONS_MARKER = "<!-- records:limitations -->"
GAPS_MARKER = "<!-- records:gaps -->"
KNOWN_GAPS_HEADING_RE = re.compile(r"^## Known gaps\s*$", re.MULTILINE)
SUMMARY_MAX_LENGTH = 240
# A Language Spec chapter states a limit as a one-line pointer to the record that
# tracks it (metel-core#1235): `> **Gap** GAP-X-001` or `> **Limitation** LIMIT-X-001`.
# The label says which kind of record it cites; the text and the version/RFC chips are
# taken from the record when the site is built, so the chapter never copies them.
SPEC_LIMIT_MARKER_RE = re.compile(
    r"^>\s*\*\*(Gap|Limitation)\*\*\s+((?:GAP|LIMIT)-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3})\b", re.MULTILINE
)
MARKER_LABEL_FOR_PREFIX = {"GAP": "Gap", "LIMIT": "Limitation"}
# Optional scheduling fields on an active record: the release it is planned for and the
# RFC(s) that specify the change. The chapter marker renders them from here.
PLANNED_FOR_RE = re.compile(r"^v\d+\.\d+\.\d+$")
# Flipped on by the chapter conversion (metel-core#1235 step 3): until every active GAP
# is cited from its chapter, requiring it would fail the corpus.
REQUIRE_GAP_CITATIONS = False
GAP_ACTIVE_DISPOSITIONS = {"known", "accepted", "mitigated", "planned"}
STATUS_VALUES = {"implemented", "partial", "planned", "superseded", "retired"}
DISPOSITION_VALUES = {"known", "accepted", "mitigated", "planned", "resolved", "superseded"}

SECTION_ANCHOR_RE = re.compile(r"^#\s+.+\{#([a-z0-9][a-z0-9-]*)\}\s*$", re.MULTILINE)
REQUIREMENT_RE = re.compile(
    r"^#####\s+Requirement\s+\{#([a-z0-9.\-]+)\}\s*\n(.*?)(?=^#####\s+Requirement|\Z)",
    re.MULTILINE | re.DOTALL,
)
FIELD_ROW_RE = re.compile(r"^\|\s*`([a-z_ ]+)`\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)
LAST_REVIEWED_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")

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
STALE_PROCESS_PROSE_RE = re.compile(
    r"\b(?:runs next|next in the chain|not audited this session|landed since|"
    r"closing that parent tracking issue)\b",
    re.IGNORECASE,
)


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


def parse_known_limitations(text: str):
    """The section's marker line when the page carries the required
    `## Known limitations` heading followed only by the records marker, else
    None. The list itself is rendered from the LIMIT records."""
    match = re.search(
        r"^## Known limitations\n\n" + re.escape(LIMITATIONS_MARKER) + r"\n(?=\n*(?:^## |\Z))",
        text,
        re.MULTILINE,
    )
    return match.group(0) if match else None


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
    return section_ids, requirements, parse_known_limitations(text)


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


def check_stale_process_prose(spec_files: list[Path], repo_root: Path) -> list:
    """Reject task-log language in published Architecture Spec prose.

    Issue and ADR references remain valid evidence and context. This narrowly
    targets the time-sensitive phrases found in the #1181 audit, leaving
    durable descriptions of current boundaries and tracked limitations alone.
    """
    findings: list = []
    overview = repo_root / "architecture" / "architecture.md"
    paths = [*spec_files, overview] if overview.exists() else spec_files
    for path in paths:
        text = path.read_text()
        match = STALE_PROCESS_PROSE_RE.search(text)
        if match:
            findings.append(
                Finding(
                    str(path.relative_to(repo_root)),
                    f"stale process narration `{match.group(0)}` belongs in issue history, not published Architecture Spec prose",
                )
            )
    return findings


# Mirrors metel-website's docusaurus.config.ts docs `exclude` list for
# architecture/: these sources are not published, so a relative link into them
# from a published page resolves in the repo but 404s on the site.
UNPUBLISHED_DIRS = ("decisions", "reports", "tools")
MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*$", re.MULTILINE)
EXPLICIT_ANCHOR_RE = re.compile(r"\{#([^}\s]+)\}")


def markdown_anchors(path: Path) -> set:
    """Every anchor a link into `path` can target: explicit `{#id}` anchors
    and the slug of each heading (lowercased, punctuation dropped, spaces to
    hyphens -- the github-slugger shape Docusaurus uses)."""
    text = path.read_text()
    anchors = set(EXPLICIT_ANCHOR_RE.findall(text))
    for heading in HEADING_RE.findall(FENCE_RE.sub("", text)):
        heading = EXPLICIT_ANCHOR_RE.sub("", heading)
        slug = re.sub(r"[^\w\s-]", "", re.sub(r"[`*_]", "", heading).lower()).strip()
        anchors.add(re.sub(r"\s+", "-", slug))
    return anchors


def _under_unpublished(path: Path, root: Path) -> bool:
    try:
        return path.resolve().relative_to(root.resolve()).parts[0] in UNPUBLISHED_DIRS
    except (ValueError, IndexError):
        return False


def check_links(repo_root: Path) -> list:
    """Every relative Markdown link under `architecture/` must resolve to a
    real file, and a `#fragment` must resolve to a real anchor in it
    (metel-core#1180). Cross-section navigation is part of the reader
    contract; a link into a page that does not exist (or an anchor that was
    renamed) is otherwise only a build-time warning on the website.
    External URLs are out of scope, as are code fences."""
    findings: list = []
    root = repo_root / "architecture"
    if not root.is_dir():
        return findings
    anchor_cache: dict = {}
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(repo_root)
        text = FENCE_RE.sub("", path.read_text())
        for match in MD_LINK_RE.finditer(text):
            url = match.group(2)
            if url.startswith(("http://", "https://", "mailto:")):
                continue
            target_part, _, fragment = url.partition("#")
            target = path if not target_part else Path(os.path.normpath(path.parent / target_part))
            if not target.exists():
                findings.append(Finding(str(rel), f"link `{url}` points at a file that does not exist"))
                continue
            if _under_unpublished(target, root) and not _under_unpublished(path, root):
                findings.append(
                    Finding(
                        str(rel),
                        f"link `{url}` targets an unpublished source (the website excludes "
                        f"architecture/{'|'.join(UNPUBLISHED_DIRS)}/**); link its repository URL instead",
                    )
                )
                continue
            if fragment and target.suffix == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = markdown_anchors(target)
                if fragment not in anchor_cache[target]:
                    findings.append(Finding(str(rel), f"link `{url}` points at an anchor that does not exist"))
    return findings


def resolve_scope_anchor(scope: str, all_section_ids_by_file: dict, repo_root: Path) -> bool:
    if "#" not in scope:
        return False
    file_part, anchor = scope.split("#", 1)
    candidate = repo_root / file_part
    if not candidate.exists():
        return False
    return anchor in all_section_ids_by_file.get(candidate.resolve(), set())


def validate_record(
    path: Path,
    rel: Path,
    fm: dict,
    affects: list,
    resolution_text: str,
    prefix: str,
    id_re,
    seen_ids: dict,
    section_ids_by_file: dict,
    repo_root: Path,
) -> list:
    """Checks shared by every durable limitation-style record (`LIMIT-*`,
    `GAP-*`): required fields, filename/ID agreement, ID shape and
    uniqueness, disposition rules, scope anchor, and a non-empty `## Affects`.
    Kind-specific rules live with their own kind."""
    findings: list = []
    for required_field in ("id", "title", "scope", "owner", "discovered_by", "disposition"):
        if not fm.get(required_field):
            findings.append(Finding(str(rel), f"missing or empty frontmatter field `{required_field}`"))

    summary = fm.get("summary", "")
    if not summary:
        findings.append(Finding(str(rel), "missing or empty frontmatter field `summary` (the one-line row shown in the section list)"))
    elif len(summary) > SUMMARY_MAX_LENGTH:
        findings.append(Finding(str(rel), f"`summary` is {len(summary)} characters; keep it to one line of at most {SUMMARY_MAX_LENGTH}"))

    record_id = fm.get("id", "")
    expected_slug = record_id.lower() + ".md"
    if record_id and path.name != expected_slug:
        findings.append(Finding(str(rel), f"filename does not match `id: {record_id}` (expected `{expected_slug}`)"))

    if record_id:
        if not id_re.match(record_id):
            findings.append(Finding(str(rel), f"`{record_id}` does not match the {prefix}-<AREA>-<NNN> shape"))
        if record_id in seen_ids:
            findings.append(
                Finding(str(rel), f"duplicate {prefix}-* id `{record_id}` (also in {seen_ids[record_id]})")
            )
        else:
            seen_ids[record_id] = str(rel)

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
    if scope and not resolve_scope_anchor(scope, section_ids_by_file, repo_root):
        findings.append(Finding(str(rel), f"`scope: {scope}` does not resolve to a real file+anchor"))

    if not affects:
        findings.append(Finding(str(rel), "`## Affects` lists no targets"))
    return findings


def language_spec_ids(language_spec_dir: Path) -> set:
    """Every explicit or heading anchor in the Language Spec chapters."""
    if not language_spec_dir.is_dir():
        return set()
    ids: set = set()
    for path in sorted(language_spec_dir.glob("*.md")):
        ids |= markdown_anchors(path)
    return ids


def rfc_stage(rfcs_dir: Path, number: str):
    """The lifecycle stage directory (`3-integrated`, ...) of RFC `number`, or
    None if no such RFC file exists."""
    for path in rfcs_dir.glob(f"*/rfc-{number}-*.md"):
        return path.parent.name
    return None


def known_gaps_section(text: str):
    """The body of a chapter's `## Known gaps` section, or None if absent."""
    m = KNOWN_GAPS_HEADING_RE.search(text)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.MULTILINE)
    return (rest[: nxt.start()] if nxt else rest).strip()


def check_known_gaps_sections(language_spec_dir: Path, repo_root: Path) -> list:
    """Each Language Spec chapter ends with a `## Known gaps` heading whose only
    content is the records marker; the website renders the list from the
    `GAP-*` records (ADR-0057 §3, metel-core#1182)."""
    findings: list = []
    for area in GAP_AREAS:
        chapter = language_spec_dir / f"{area.lower()}.md"
        if not chapter.is_file():
            continue
        rel = chapter.relative_to(repo_root)
        section = known_gaps_section(chapter.read_text())
        if section is None:
            findings.append(Finding(str(rel), "missing `## Known gaps` section (ADR-0057 §3)"))
        elif section != GAPS_MARKER:
            findings.append(Finding(str(rel), f"`## Known gaps` must hold only the `{GAPS_MARKER}` marker; the list is rendered from the GAP records"))
    return findings


HEALTH_PAGES = (
    ("status/architecture-health.md", "<!-- health:architecture -->"),
    ("status/language-health.md", "<!-- health:language -->"),
)


def check_health_pages(repo_root: Path) -> list:
    """The two Health pages hold a marker the website replaces with a report
    computed from the specs and records (metel-core#1182 follow-up)."""
    findings: list = []
    for rel, marker in HEALTH_PAGES:
        path = repo_root / rel
        if not path.is_file():
            continue
        if path.read_text().count(marker) != 1:
            findings.append(Finding(rel, f"must contain the `{marker}` marker exactly once"))
    return findings


def check_gap_records(
    gap_files: list,
    limit_records: list,
    all_arch_ids: dict,
    repo_root: Path,
    rfcs_dir: Path,
    language_spec_dir: Path,
) -> tuple:
    """`GAP-*` records (ADR-0057): a known, accepted gap in what the Language
    Spec specifies. Returns (findings, {gap id: (path, fm, affects)})."""
    findings: list = []
    gap_ids: dict = {}
    gaps: list = []

    spec_files = sorted(language_spec_dir.glob("*.md")) if language_spec_dir.is_dir() else []
    anchors_by_file = {p.resolve(): markdown_anchors(p) for p in spec_files}
    all_spec_ids = set().union(*anchors_by_file.values()) if anchors_by_file else set()

    for path in gap_files:
        rel = path.relative_to(repo_root)
        fm, affects, resolution_text = parse_limitation_file(path)
        findings.extend(
            validate_record(path, rel, fm, affects, resolution_text, "GAP", GAP_ID_RE, gap_ids, anchors_by_file, repo_root)
        )
        gaps.append((path, fm, affects, resolution_text))

        record_id = fm.get("id", "")
        area = record_id.split("-")[1] if GAP_ID_RE.match(record_id) else None
        scope = fm.get("scope", "")
        if scope and not scope.startswith("reference/spec/"):
            findings.append(Finding(str(rel), f"`scope: {scope}` must point into `reference/spec/` (a GAP describes the Language Spec)"))
        elif area and scope and Path(scope.split("#", 1)[0]).stem.upper() != area:
            findings.append(Finding(str(rel), f"`{record_id}` area `{area}` does not match the chapter its `scope` points into"))

        rfc_targets = [t for t in affects if RFC_REF_RE.match(t)]
        rule_targets = [t for t in affects if SPEC_RULE_ID_RE.match(t)]
        if affects and not rfc_targets and not rule_targets:
            findings.append(Finding(str(rel), "`## Affects` must name at least one Language Spec rule (`spec.*`) or RFC"))

        disposition = fm.get("disposition", "")
        stages = {}
        for target in affects:
            m = RFC_REF_RE.match(target)
            if m:
                stage = rfc_stage(rfcs_dir, m.group(1))
                if stage is None:
                    findings.append(Finding(str(rel), f"`affects` RFC `{target}` does not exist under rfcs/"))
                stages[target] = stage
        if disposition == "resolved" and not any(st in RFC_LANDED_STAGES for st in stages.values()):
            findings.append(
                Finding(str(rel), "disposition `resolved` requires an `affects` RFC at stage 3-integrated or 4-implemented (a closed issue is not enough, ADR-0055 §4)")
            )
        if disposition == "planned" and not stages and not re.search(r"#\d+", resolution_text):
            findings.append(Finding(str(rel), "disposition `planned` requires an RFC in `affects` or an issue reference in `## Resolution`"))
        if disposition == "accepted" and not re.search(r"\b(?:ADR|RFC)-\d{4}\b|#\d+", resolution_text, re.IGNORECASE):
            findings.append(Finding(str(rel), "disposition `accepted` requires an accepting ADR, RFC or issue named in `## Resolution`"))

        for target in affects:
            if SPEC_RULE_ID_RE.match(target):
                if target not in all_spec_ids:
                    findings.append(Finding(str(rel), f"`affects` spec rule `{target}` does not exist in reference/spec/"))
            elif RFC_REF_RE.match(target) or LIMIT_ID_RE.match(target):
                continue
            elif target not in all_arch_ids and target not in gap_ids:
                findings.append(Finding(str(rel), f"`affects` target `{target}` does not exist"))

    # A GAP and a LIMIT that cite each other must do so in both directions.
    limit_affects = {fm.get("id"): (path, affects) for path, fm, affects, _ in limit_records}
    for path, fm, affects, _ in gaps:
        rel = path.relative_to(repo_root)
        gap_id = fm.get("id", "")
        for target in affects:
            if not LIMIT_ID_RE.match(target):
                continue
            if target not in limit_affects:
                findings.append(Finding(str(rel), f"`affects` LIMIT record `{target}` does not exist"))
            elif gap_id not in limit_affects[target][1]:
                findings.append(Finding(str(rel), f"`{target}` does not link back to `{gap_id}` in its `## Affects`"))
    for limit_id, (lpath, affects) in limit_affects.items():
        for target in affects:
            if GAP_ID_RE.match(target):
                gap = next((g for g in gaps if g[1].get("id") == target), None)
                if gap is None:
                    continue  # reported by the generic affects-target check
                if limit_id not in gap[2]:
                    findings.append(
                        Finding(str(lpath.relative_to(repo_root)), f"`{target}` does not link back to `{limit_id}` in its `## Affects`")
                    )
    findings.extend(check_known_gaps_sections(language_spec_dir, repo_root))
    return findings, {fm.get("id"): (p, fm, a) for p, fm, a, _ in gaps}


def check_schedule_fields(records: list, repo_root: Path, rfcs_dir: Path) -> list:
    """`planned_for` (a `vX.Y.Z` release) and `rfc` (`RFC-NNNN`, comma-separated for
    several) are optional on an active record, and meaningless on a finished one."""
    findings: list = []
    for path, fm in records:
        rel = path.relative_to(repo_root)
        planned_for = fm.get("planned_for")
        rfc = fm.get("rfc")
        if not planned_for and not rfc:
            continue
        if fm.get("disposition") in ("resolved", "superseded"):
            findings.append(Finding(str(rel), "`planned_for` / `rfc` describe pending work; remove them from a resolved or superseded record"))
            continue
        if planned_for and not PLANNED_FOR_RE.match(planned_for):
            findings.append(Finding(str(rel), f"`planned_for: {planned_for}` must be a release like `v0.14.0`"))
        for ref in [r.strip() for r in (rfc or "").split(",") if r.strip()]:
            m = RFC_REF_RE.match(ref)
            if not m or not ref.startswith("RFC-"):
                findings.append(Finding(str(rel), f"`rfc` entry `{ref}` must look like `RFC-0071`"))
            elif rfc_stage(rfcs_dir, m.group(1)) is None:
                findings.append(Finding(str(rel), f"`rfc` entry `{ref}` does not exist under rfcs/"))
    return findings


def check_spec_limit_markers(
    language_spec_dir: Path,
    gap_records: dict,
    limit_records: list,
    repo_root: Path,
    require_gap_citations: bool,
) -> list:
    """The `> **Gap** ID` / `> **Limitation** ID` markers in the Language Spec chapters
    (metel-core#1235): each cites an existing, active record of the kind its label
    names; a gap is cited from the chapter its own `scope` names; and (once
    `require_gap_citations` is on) every active `GAP-*` is cited there at least once."""
    findings: list = []
    active = GAP_ACTIVE_DISPOSITIONS
    gaps = {rid: fm for rid, (_, fm, _) in gap_records.items()}
    limits = {fm.get("id"): fm for _, fm, _, _ in limit_records}
    cited: dict = {}
    for path in sorted(language_spec_dir.glob("*.md")) if language_spec_dir.is_dir() else []:
        if path.name.upper() == "STYLEGUIDE.MD":
            continue
        rel = path.relative_to(repo_root)
        text = FENCE_RE.sub("", path.read_text())
        for m in SPEC_LIMIT_MARKER_RE.finditer(text):
            label, record_id = m.group(1), m.group(2)
            prefix = record_id.split("-")[0]
            if MARKER_LABEL_FOR_PREFIX[prefix] != label:
                findings.append(Finding(str(rel), f"marker `{label}` cites `{record_id}`; use `{MARKER_LABEL_FOR_PREFIX[prefix]}` for a {prefix}-* record"))
                continue
            fm = (gaps if prefix == "GAP" else limits).get(record_id)
            if fm is None:
                findings.append(Finding(str(rel), f"marker cites `{record_id}`, which does not exist"))
                continue
            if fm.get("disposition") not in active:
                findings.append(Finding(str(rel), f"marker cites `{record_id}`, which is `{fm.get('disposition')}`; remove the marker (only active records are cited)"))
                continue
            if prefix == "GAP":
                scope_chapter = Path(fm.get("scope", "").split("#", 1)[0]).name
                if scope_chapter and scope_chapter != path.name:
                    findings.append(Finding(str(rel), f"marker cites `{record_id}`, whose `scope` is `{scope_chapter}`; cite a gap from its own chapter"))
                    continue
                cited.setdefault(record_id, set()).add(path.name)
    if require_gap_citations:
        for record_id, fm in gaps.items():
            if fm.get("disposition") in active and record_id not in cited:
                chapter = Path(fm.get("scope", "").split("#", 1)[0])
                findings.append(Finding(str(chapter), f"active `{record_id}` is not cited by a `> **Gap** {record_id}` marker in this chapter"))
    return findings


def run_checks(
    repo_root: Path = REPO_ROOT,
    spec_dir: Path = None,
    limitations_dir: Path = None,
    decisions_dir: Path = None,
    gaps_dir: Path = None,
    language_spec_dir: Path = None,
    rfcs_dir: Path = None,
    require_gap_citations: bool = None,
) -> list[Finding]:
    spec_dir = spec_dir or (repo_root / "architecture" / "spec")
    limitations_dir = limitations_dir or (repo_root / "architecture" / "limitations")
    decisions_dir = decisions_dir or (repo_root / "architecture" / "decisions")
    gaps_dir = gaps_dir or (repo_root / "architecture" / "gaps")
    language_spec_dir = language_spec_dir or (repo_root / "reference" / "spec")
    rfcs_dir = rfcs_dir or (repo_root / "rfcs")
    findings: list[Finding] = []
    superseded_adrs = load_adr_supersessions(decisions_dir)
    findings.extend(check_adr_frontmatter(decisions_dir, repo_root))

    if not spec_dir.is_dir():
        findings.append(Finding(str(spec_dir), "directory does not exist"))
        return findings

    spec_files = sorted(spec_dir.glob("*.md"))
    limitation_files = sorted(limitations_dir.glob("*.md")) if limitations_dir.is_dir() else []
    findings.extend(check_stale_process_prose(spec_files, repo_root))
    findings.extend(check_links(repo_root))
    findings.extend(check_health_pages(repo_root))

    all_section_ids_by_file: dict = {}
    all_arch_ids: dict = {}
    known_limitations_by_file: dict = {}

    for path in spec_files:
        section_ids, requirements, known_limitations = parse_spec_file(path)
        all_section_ids_by_file[path.resolve()] = section_ids
        known_limitations_by_file[path] = known_limitations

        rel = path.relative_to(repo_root)
        if not section_ids:
            findings.append(Finding(str(rel), "no top-level `{#section-id}` heading anchor found"))

        if known_limitations is None:
            findings.append(
                Finding(
                    str(rel),
                    f"`## Known limitations` must hold only the `{LIMITATIONS_MARKER}` marker; the list is rendered from the LIMIT records",
                )
            )

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

            for required_field in ("status", "owner", "specified by", "implements", "verified by", "related", "last_reviewed"):
                if not fields.get(required_field):
                    findings.append(Finding(str(rel), f"`{req_id}`: missing or empty `{required_field}` field"))

            # metel-core#1191: this only checks the field's *shape* -- whether
            # the code it points at has actually moved on since that commit
            # needs real git history (the metel-core checkout), which a bare
            # metel-docs checkout structurally can't reach; that half of the
            # check lives in generate_architecture_evidence.py instead, the
            # same split this file already documents for fixture-sidecar
            # `arch = [...]` cross-checking.
            last_reviewed = fields.get("last_reviewed", "")
            if last_reviewed and not LAST_REVIEWED_SHA_RE.match(last_reviewed.strip("`")):
                findings.append(
                    Finding(str(rel), f"`{req_id}`: `last_reviewed` (`{last_reviewed}`) is not a 7-40 character hex commit SHA")
                )

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
        findings.extend(
            validate_record(
                path, rel, fm, affects, resolution_text, "LIMIT", LIMIT_ID_RE, all_limit_ids,
                all_section_ids_by_file, repo_root,
            )
        )

    gap_files = sorted(gaps_dir.glob("*.md")) if gaps_dir.is_dir() else []
    gap_findings, gap_records = check_gap_records(
        gap_files, limitation_records, all_arch_ids, repo_root, rfcs_dir, language_spec_dir
    )
    findings.extend(gap_findings)
    findings.extend(
        check_schedule_fields(
            [(p, fm) for p, fm, _, _ in limitation_records] + [(p, fm) for p, fm, _ in gap_records.values()],
            repo_root,
            rfcs_dir,
        )
    )
    findings.extend(
        check_spec_limit_markers(
            language_spec_dir,
            gap_records,
            limitation_records,
            repo_root,
            REQUIRE_GAP_CITATIONS if require_gap_citations is None else require_gap_citations,
        )
    )

    # Cross-file: every `affects` entry, and every standardized
    # "Known limitations" link, must resolve to a real id that actually exists
    # somewhere in the corpus. The groups must agree with record disposition.
    for path, fm, affects, _ in limitation_records:
        rel = path.relative_to(repo_root)
        for target in affects:
            if SPEC_RULE_ID_RE.match(target):
                # A limitation may cite the Language Spec rule that specifies its
                # behaviour (for example when it turns out not to be a limitation).
                if target not in language_spec_ids(language_spec_dir):
                    findings.append(Finding(str(rel), f"`affects` spec rule `{target}` does not exist in reference/spec/"))
                continue
            if target not in all_arch_ids and target not in all_limit_ids and target not in gap_records:
                findings.append(Finding(str(rel), f"`affects` target `{target}` does not exist"))

    # A record only renders in the section of the page its `scope` names, so that
    # page must carry the marker.
    without_marker = {path.resolve() for path, marker in known_limitations_by_file.items() if marker is None}
    for path, fm, _, _ in limitation_records:
        scope_page = (repo_root / fm.get("scope", "").split("#", 1)[0]).resolve()
        if scope_page in without_marker:
            findings.append(Finding(str(path.relative_to(repo_root)), f"`scope` page has no `## Known limitations` marker, so this record never renders"))

    return findings


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true", help="CI gate: exit 1 on any finding")
    args = p.parse_args()

    findings = run_checks()

    spec_count = len(list(SPEC_DIR.glob("*.md"))) if SPEC_DIR.is_dir() else 0
    limit_count = len(list(LIMITATIONS_DIR.glob("*.md"))) if LIMITATIONS_DIR.is_dir() else 0
    gap_count = len(list(GAPS_DIR.glob("*.md"))) if GAPS_DIR.is_dir() else 0
    print(f"Checked {spec_count} spec file(s), {limit_count} limitation record(s), {gap_count} gap record(s).")
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
