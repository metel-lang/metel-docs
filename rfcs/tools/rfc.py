#!/usr/bin/env python3
"""RFC lifecycle tool for metel-docs. See public/rfcs/PROCESS.md.

Subcommands:
  new <title> [-d description]        Create a new draft RFC, next free number,
                                       with a duplicate/overlap check against
                                       existing RFCs first.
  transition <rfc-id> --to <stage> [-r reason] [--tracking LINK]
                                       Move an RFC to a new lifecycle stage:
                                       git mv, update frontmatter, insert a
                                       dated status note, fix path references
                                       elsewhere in the repo, then run `check`.
                                       `--to integrated` requires `--tracking`
                                       (a tracking task/URL) and sets
                                       `impl_status: not-started` alongside it —
                                       no RFC enters integrated without a
                                       linked implementation-tracking task.
                                       `--to implemented` sets
                                       `impl_status: implemented`, and refuses to run
                                       while a "Not yet implemented" callout for this
                                       RFC still exists under public/reference/spec/.
  impl-status <rfc-id> --set <status> [--tracking LINK]
                                       Update `impl_status` (not-started /
                                       in-progress / implemented) on an RFC
                                       already at integrated or implemented,
                                       without moving it. Optionally updates
                                       `impl_tracking` too.
  supersede <rfc-id> --by <ids> [-r reason]
                                       Shortcut for `transition ... --to superseded`
                                       that also sets `superseded_by`.
  check                                Validate frontmatter/directory consistency,
                                       duplicate RFC ids, dangling path
                                       references, REGISTRY.md exact-generation
                                       drift, and (for integrated/implemented
                                       RFCs) that impl_status/impl_tracking are set
                                       and the spec actually references the RFC.
                                       Also flags any stale "Not yet implemented"
                                       callout left behind for an RFC that's already
                                       4-implemented, any inline "RFC-NNNN (...,
                                       status)" citation anywhere in the repo whose
                                       cited status no longer matches that RFC's
                                       actual current stage, and any reference to a
                                       retired issue-tracker host (impl_tracking or
                                       a live link under public/). Read-only.
  index --check-drift                  Check whether generated REGISTRY.md matches
                                       the current RFC corpus exactly, and whether
                                       the curated INDEX.md mentions every current
                                       RFC at least once. Read-only.
  index --rebuild-registry             Regenerate public/rfcs/REGISTRY.md from
                                       the current RFC corpus.
  index --suggest-placement <rfc-id>   Suggest which INDEX.md cluster section an
                                       RFC's content is most similar to. Read-only.
  index --write-coverage-baseline      Regenerate public/rfcs/COVERAGE-BASELINE.json
                                       (ADR-0049 §7) from the current per-RFC
                                       coverage state -- the snapshot `check`'s
                                       coverage ratchet compares against. Run
                                       this after deliberately widening a gap
                                       (a new typed exemption, e.g.) so `check`
                                       stops treating it as a regression; needs
                                       metel-interpreter/tests reachable (see
                                       ADR-0049 §6), same as `check`'s own
                                       coverage summary.
  index --write-spec-origins           Regenerate every rigor block's origins
                                       backlink (ADR-0050 §3a) in
                                       public/reference/spec/*.md from the
                                       RFCs currently linking to it via
                                       `coverage.spec` frontmatter. Reads only
                                       RFC frontmatter and the spec files --
                                       no fixture corpus needed, unlike
                                       --write-coverage-baseline.
  cycle-prep [--diff]                  One-shot pre-cycle report for
                                       reports/strategy/PROCESS.md §5 step 0:
                                       REGISTRY.md drift, retired-host references,
                                       RFC `updated:` vs. git-log staleness, and
                                       (best-effort, needs GITHUB_TOKEN/GH_TOKEN)
                                       open-milestone issue counts — one script
                                       run replacing dozens of one-file/one-issue
                                       lookups. `--diff` also compares against
                                       reports/strategy/.cycle-snapshot.json (the
                                       prior run's state) and prints only what
                                       changed, before overwriting it with the
                                       current state. Mostly read-only — only
                                       writes the snapshot file.

No dependencies beyond the Python 3 standard library. `cycle-prep`'s milestone
check needs network access and a token; everything else is fully offline.
"""

import argparse
import datetime
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RFCS_DIR = REPO_ROOT / "public" / "rfcs"
INDEX_PATH = RFCS_DIR / "INDEX.md"
REGISTRY_PATH = RFCS_DIR / "REGISTRY.md"
COVERAGE_BASELINE_PATH = RFCS_DIR / "COVERAGE-BASELINE.json"
STRATEGY_DIR = REPO_ROOT / "reports" / "strategy"
SNAPSHOT_PATH = STRATEGY_DIR / ".cycle-snapshot.json"

# The project's canonical issue tracker, and hosts it has fully retired. A
# reference to a retired host is either a dead link (public/-facing content) or
# an unresolvable/misleading identifier (impl_tracking) — added 2026-08-06 after
# the migration's own reference-rewrite missed impl_tracking backfill on several
# RFCs and one public spec page's live bug-report link (see
# `retired_host_references()` below). Append to RETIRED_HOSTS, don't replace, if
# the project ever moves host again — old retirements stay worth flagging.
CANONICAL_ISSUE_HOST = "github.com/metel-lang/metel-core"
RETIRED_HOSTS = ["codeberg.org"]

STAGES = {
    "draft": "0-draft",
    "under-review": "1-under-review",
    "accepted": "2-accepted",
    "integrated": "3-integrated",
    "implemented": "4-implemented",
    "superseded": "5-superseded",
    "refused": "6-refused",
}
STAGE_FOR_DIR = {v: k for k, v in STAGES.items()}

STAGE_LABELS = {
    "draft": "Status — draft",
    "under-review": "Status — under review",
    "accepted": "Status — accepted",
    "integrated": "Status — integrated",
    "implemented": "Status — implemented",
    "superseded": "Status — superseded",
    "refused": "Status — refused",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "is", "are",
    "this", "that", "with", "as", "by", "be", "at", "it", "its", "from", "not",
    "into", "over", "than", "then", "when", "which", "would", "could", "should",
    "has", "have", "had", "was", "were", "will", "can", "may", "if", "but",
    "rfc", "rfcs", "one", "two", "also", "these", "those", "any", "all",
}


# --------------------------------------------------------------------------
# File discovery and frontmatter parsing
# --------------------------------------------------------------------------

def find_rfc_files():
    for stage_dir in STAGES.values():
        d = RFCS_DIR / stage_dir
        if d.is_dir():
            for f in sorted(d.glob("rfc-*.md")):
                yield f


def rfc_id_from_filename(path):
    m = re.match(r"(rfc-\d+[a-z]?)(-.*)?$", path.stem)
    return m.group(1) if m else None


def normalize_id(s):
    s = s.strip().lower()
    if not s.startswith("rfc-"):
        s = "rfc-" + s
    m = re.match(r"rfc-0*(\d+)([a-z]?)$", s)
    if m:
        return f"rfc-{int(m.group(1)):04d}{m.group(2)}"
    return s


def find_path_for_id(rid):
    rid = normalize_id(rid)
    for f in find_rfc_files():
        if rfc_id_from_filename(f) == rid:
            return f
    return None


def rfc_sort_key(rid):
    m = re.match(r"rfc-(\d+)([a-z]?)$", rid)
    if not m:
        return (10**9, rid)
    return (int(m.group(1)), m.group(2))


def parse_file(path):
    """Return (frontmatter_dict, body_text). Flat `key: value` parser only —
    good enough for this repo's frontmatter, not a general YAML parser."""
    text = path.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm = {}
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
        m = re.match(r"^([\w-]+):\s*(.*)$", lines[i])
        if m:
            key, val = m.group(1), m.group(2).strip()
            fm[key] = val.strip("'\"")
    body = "\n".join(lines[end_idx + 1:]) if end_idx is not None else text
    return fm, body


def format_fm_value(val):
    val = str(val)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val) or ":" in val:
        return f"'{val}'"
    return val


def update_frontmatter_fields(text, updates):
    """Set or insert flat frontmatter fields, leaving everything else untouched."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return text
    fm_lines = lines[1:end_idx]
    remaining = dict(updates)
    new_fm_lines = []
    for line in fm_lines:
        m = re.match(r"^([\w-]+):\s*(.*)$", line.rstrip("\n"))
        if m and m.group(1) in remaining:
            key = m.group(1)
            val = remaining.pop(key)
            new_fm_lines.append(f"{key}: {format_fm_value(val)}\n")
        else:
            new_fm_lines.append(line)
    for key, val in remaining.items():
        new_fm_lines.append(f"{key}: {format_fm_value(val)}\n")
    return "".join(lines[:1]) + "".join(new_fm_lines) + lines[end_idx] + "".join(lines[end_idx + 1:])


def insert_status_note(text, stage_key, reason, date_str):
    label = STAGE_LABELS[stage_key]
    note = f"> **{label} ({date_str}).**"
    if reason:
        note += f" {reason}"
    note += "\n"
    lines = text.splitlines(keepends=True)
    heading_idx = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            heading_idx = i
            break
    if heading_idx is None:
        heading_idx = len(lines)
    before = "".join(lines[:heading_idx])
    after = "".join(lines[heading_idx:])
    if before and not before.endswith("\n\n"):
        before = before.rstrip("\n") + "\n\n"
    return before + note + "\n" + after


def today():
    return datetime.date.today().isoformat()


def run_git(args):
    subprocess.run(["git", *args], check=True, cwd=REPO_ROOT)


def error(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# TF-IDF / cosine similarity — pure Python, no dependencies
# --------------------------------------------------------------------------

def tokenize(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]*", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def build_tfidf(docs):
    """docs: dict[doc_id] -> list of tokens. Returns dict[doc_id] -> {term: weight}."""
    df = Counter()
    for tokens in docs.values():
        for term in set(tokens):
            df[term] += 1
    n = len(docs)
    idf = {term: math.log((n + 1) / (freq + 1)) + 1 for term, freq in df.items()}
    vectors = {}
    for doc_id, tokens in docs.items():
        tf = Counter(tokens)
        length = len(tokens) or 1
        vectors[doc_id] = {term: (count / length) * idf.get(term, 0) for term, count in tf.items()}
    return vectors


def cosine_sim(v1, v2):
    common = set(v1) & set(v2)
    dot = sum(v1[t] * v2[t] for t in common)
    n1 = math.sqrt(sum(x * x for x in v1.values()))
    n2 = math.sqrt(sum(x * x for x in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def rfc_corpus(char_cap=3000):
    """dict[rfc_id] -> (title, tokens) for every existing RFC."""
    corpus = {}
    for f in find_rfc_files():
        rid = rfc_id_from_filename(f)
        if not rid:
            continue
        fm, body = parse_file(f)
        title = fm.get("title", f.stem)
        text = f"{title} {body[:char_cap]}"
        corpus[rid] = (title, tokenize(text))
    return corpus


# --------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------

def cmd_new(args):
    corpus = rfc_corpus()
    docs = {rid: tokens for rid, (title, tokens) in corpus.items()}
    docs["__new__"] = tokenize(f"{args.title} {args.description or ''}")
    vectors = build_tfidf(docs)
    new_vec = vectors.pop("__new__")
    sims = sorted(
        ((cosine_sim(new_vec, v), rid) for rid, v in vectors.items()),
        reverse=True,
    )
    top = [s for s in sims if s[0] > 0.05][:5]
    if top:
        print("Possibly related existing RFCs — check these before continuing:")
        for score, rid in top:
            print(f"  {score:.3f}  {rid.upper()}  {corpus[rid][0]}")
        print()
        if not args.yes:
            reply = input("Continue creating the new RFC anyway? [y/N] ").strip().lower()
            if reply != "y":
                print("Aborted.")
                return

    existing_nums = []
    for f in find_rfc_files():
        rid = rfc_id_from_filename(f)
        m = re.match(r"rfc-(\d+)", rid or "")
        if m:
            existing_nums.append(int(m.group(1)))
    next_num = (max(existing_nums) + 1) if existing_nums else 1
    new_id = f"rfc-{next_num:04d}"
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
    path = RFCS_DIR / "0-draft" / f"{new_id}-{slug}.md"
    if path.exists():
        error(f"{path} already exists")

    template = f'''---
id: {new_id}
title: "{args.title}"
date: '{today()}'
status: draft
target:
---

## Summary

{args.description or ""}

---

## Motivation



---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
'''
    path.write_text(template)
    rebuild_registry()
    print(f"Created {path.relative_to(REPO_ROOT)}")
    print("Reminder: public/rfcs/INDEX.md needs a new entry for this RFC.")


# --------------------------------------------------------------------------
# transition / supersede
# --------------------------------------------------------------------------

def do_transition(rid, to_stage, reason, extra_fm=None):
    if to_stage not in STAGES:
        error(f"unknown stage '{to_stage}' — choose from {', '.join(STAGES)}")
    path = find_path_for_id(rid)
    if path is None:
        error(f"RFC {rid} not found")
    new_dir = RFCS_DIR / STAGES[to_stage]
    new_path = new_dir / path.name
    if path.resolve() == new_path.resolve():
        error(f"{rid} is already in stage '{to_stage}'")
    old_rel = path.relative_to(REPO_ROOT)
    new_rel = new_path.relative_to(REPO_ROOT)

    run_git(["mv", str(old_rel), str(new_rel)])

    text = new_path.read_text()
    updates = {"status": to_stage, "updated": today()}
    if extra_fm:
        updates.update(extra_fm)
    text = update_frontmatter_fields(text, updates)
    text = insert_status_note(text, to_stage, reason, today())
    new_path.write_text(text)

    changed = fix_referrers(old_rel, new_rel)

    print(f"{rid.upper()}: {old_rel} -> {new_rel}")
    if changed:
        print("Fixed path references in:")
        for c in changed:
            print(f"  {c}")
    print("Reminder: public/rfcs/INDEX.md may need updating for this RFC's new status.")
    return new_path


def fix_referrers(old_rel, new_rel):
    old_str = str(old_rel)
    new_str = str(new_rel)
    changed = []
    for f in REPO_ROOT.rglob("*.md"):
        if ".git" in f.parts:
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if old_str in text:
            f.write_text(text.replace(old_str, new_str))
            changed.append(f.relative_to(REPO_ROOT))
    return changed


def cmd_transition(args):
    rid = normalize_id(args.rfc_id)
    extra_fm = {}
    if args.to == "integrated":
        if not args.tracking:
            error(
                "transitioning to 'integrated' requires --tracking <tracking task/URL> — "
                "no RFC enters integrated without a linked implementation-tracking task "
                "(see PROCESS.md's 3-integrated exit criteria)."
            )
        extra_fm["impl_tracking"] = args.tracking
        extra_fm["impl_status"] = "not-started"
    elif args.tracking:
        extra_fm["impl_tracking"] = args.tracking
    if args.to == "implemented":
        extra_fm["impl_status"] = "implemented"
        # Checked before do_transition (and its fix_referrers path rewrite) runs:
        # once the RFC file moves to 4-implemented, a leftover "Not yet implemented"
        # callout's path reference would get silently rewritten to point at
        # 4-implemented too, turning it into self-contradictory nonsense instead of
        # failing loudly.
        hits = spec_not_implemented_refs(rid)
        if hits:
            lines = "\n".join(f"  {p}:{lineno}: {text}" for p, lineno, text in hits)
            error(
                f"{rid.upper()} still has a 'Not yet implemented' callout under "
                f"public/reference/spec/ — delete it (it's a required one-liner, safe "
                f"to remove outright, see PROCESS.md) before transitioning to "
                f"implemented:\n{lines}"
            )
        # ADR-0049: fixture coverage gate. Unlike `check`, this refuses rather
        # than degrading when the corpus is unreachable — "unknown" must not
        # be treated as "pass" for the one command that actually marks
        # something implemented. See ADR-0049 §5/§6.
        tests_dir = metel_core_tests_dir()
        if tests_dir is None:
            error(
                "cannot verify fixture coverage: metel-interpreter/tests is not "
                "reachable from here (see ADR-0049 §6). Run this from a metel-core "
                "checkout with docs/ embedded as its submodule, or set "
                "METEL_CORE_ROOT to point at one."
            )
        current_path = find_path_for_id(rid)
        _, body = parse_file(current_path)
        sections = set(rfc_normative_sections(body))
        sidecar, prose = scan_fixture_citations(tests_dir)
        cited = {s for s, _ in sidecar.get(rid, [])} | {s for s, _ in prose.get(rid, [])}
        cited.discard(None)
        exempted = set(parse_coverage_frontmatter(frontmatter_raw_text(current_path)))
        uncovered = sections - cited - exempted
        if uncovered:
            error(
                f"{rid.upper()} has normative sections with neither a qualifying "
                f"fixture nor a coverage exemption: {', '.join(sorted(uncovered))} "
                f"(ADR-0049) — cite a fixture (`options.rfc` sidecar key) or add a "
                f"typed `coverage` frontmatter entry for each"
            )
    do_transition(rid, args.to, args.reason, extra_fm=extra_fm or None)
    rebuild_registry()
    cmd_check(args)


def cmd_impl_status(args):
    rid = normalize_id(args.rfc_id)
    path = find_path_for_id(rid)
    if path is None:
        error(f"RFC {rid} not found")
    fm, _ = parse_file(path)
    stage = STAGE_FOR_DIR.get(path.parent.name)
    if stage not in ("integrated", "implemented"):
        error(
            f"{rid} is at stage '{stage}', not 'integrated' or 'implemented' — "
            "impl_status only applies once an RFC has reached integrated (PROCESS.md)."
        )
    updates = {"impl_status": args.set}
    if args.tracking:
        updates["impl_tracking"] = args.tracking
    text = update_frontmatter_fields(path.read_text(), updates)
    path.write_text(text)
    rebuild_registry()
    print(f"{rid.upper()}: impl_status -> {args.set}" + (f", impl_tracking -> {args.tracking}" if args.tracking else ""))
    if args.set == "implemented" and stage != "implemented":
        print(f"Reminder: run `rfc.py transition {rid} --to implemented` to move the RFC itself.")


def cmd_supersede(args):
    rid = normalize_id(args.rfc_id)
    by_ids = [normalize_id(x) for x in args.by.split(",")]
    reason = args.reason or f"Superseded by {', '.join(i.upper() for i in by_ids)}."
    do_transition(rid, "superseded", reason, extra_fm={"superseded_by": ", ".join(by_ids)})
    rebuild_registry()
    print("Reminder: write the reconciliation content by hand (what carried forward, "
          "what didn't) — this tool only performs the mechanical move.")
    cmd_check(args)


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

# [a-z-]+ not [a-z]+: stage dir names like "1-under-review" have more than one hyphen.
PATH_REF_RE = re.compile(r"public/rfcs/[0-6]-[a-z-]+/rfc-[\w.-]+\.md")


SPEC_DIR = REPO_ROOT / "public" / "reference" / "spec"
VALID_IMPL_STATUS = {"not-started", "in-progress", "implemented"}

# ADR-0050 §3a: a rigor block's generated backlink to the RFC(s) that
# established it, delimited so `index --write-spec-origins` can rewrite
# exactly its own slot without touching anything hand-authored around it.
SPEC_BLOCK_HEADING_RE = re.compile(
    r"^##### (?:Legality Rule|Dynamic Semantics) \{#(?P<id>spec\.[a-z0-9.-]+)\}\s*$"
)
ORIGINS_MARKER_START = "<!-- rfc.py:origins:start -->"
ORIGINS_MARKER_END = "<!-- rfc.py:origins:end -->"

# A rigor block's generated backlink to the fixture(s) that test it (ADR-0050
# §5's spec-id -> fixture check, made visible in the rendered spec). The
# fixture corpus lives in metel-interpreter/tests -- metel-core, a different
# repo from this one -- so this can't be a relative path the way the origins
# link is; it points at metel-core's default branch, not a pinned commit, so
# a renamed/moved fixture just goes stale until the next
# --write-spec-origins regenerates it, the same self-healing --check-drift
# already gives the origins slot, rather than freezing a link that's
# correct-forever but points at dead history.
FIXTURES_MARKER_START = "<!-- rfc.py:fixtures:start -->"
FIXTURES_MARKER_END = "<!-- rfc.py:fixtures:end -->"
METEL_CORE_GITHUB_BLOB = "https://github.com/metel-lang/metel-core/blob/main"


def compute_spec_origins_from_rfcs():
    """{spec_id: [rid, ...]} sorted by rfc_sort_key -- ADR-0050 §3a's inverted
    RFC-to-spec-id mapping. Reads RFC frontmatter only, not the fixture
    corpus (unlike scan_coverage_corpus/per_rfc_coverage) -- origins
    generation only needs to know which RFC currently claims a spec-id, not
    whether that claim also has a citing fixture, so it works from a bare
    docs-internal checkout with no ADR-0049 §6 reachability question at all."""
    origins = {}
    for f in find_rfc_files():
        rid = rfc_id_from_filename(f)
        if rid is None:
            continue
        links = parse_coverage_spec_links(frontmatter_raw_text(f))
        for _section, spec_id in links.items():
            origins.setdefault(spec_id, set()).add(rid)
    return {
        spec_id: sorted(rids, key=rfc_sort_key) for spec_id, rids in origins.items()
    }


def origins_block_text(spec_path, rids):
    """The exact content between the origin markers for one rigor block, or
    "" if it has no origins yet -- a normal, valid state (pre-RFC spec
    content, ADR-0050's own Context section names this as real), rendered as
    no slot at all rather than a fabricated "not yet linked" placeholder."""
    if not rids:
        return ""
    links = []
    for rid in rids:
        rfc_path = find_path_for_id(rid)
        if rfc_path is None:
            continue
        rel = os.path.relpath(rfc_path, start=spec_path.parent)
        links.append(f"[{rid}]({rel})")
    if not links:
        return ""
    # An inline <span>, not a block-level tag: CommonMark only stops parsing
    # markdown inside raw HTML for a handful of block-starting patterns (a
    # bare <p>/<div>/etc. alone, or followed only by whitespace, on its own
    # line) -- this line has real content after the opening tag, so it never
    # qualifies, and the [rid](rel) links above still parse normally inside
    # it. Website styling (src/theme/Details, custom.css) targets the class.
    return f'<span class="rigor-backlink">_Referenced by: {", ".join(links)}_</span>'


def fixtures_block_text(toml_paths, core_root):
    """The exact content between the fixtures markers for one rigor block, or
    "" if no fixture cites it yet -- as valid a state as an RFC with no
    fixture yet (ADR-0050's own Context section names this as real),
    rendered as no slot at all rather than a fabricated "untested"
    placeholder. Links to each fixture's .mtl (the actual Metel source a
    reader would want to read), not its .toml sidecar (the `spec =`
    citation lives there, but that's metadata about the test, not the test
    itself)."""
    if not toml_paths:
        return ""
    links = []
    for p in sorted(set(toml_paths)):
        mtl_path = _sidecar_mtl_path(p)
        if not mtl_path.is_file():
            continue
        try:
            rel = mtl_path.resolve().relative_to(core_root.resolve())
        except ValueError:
            continue
        links.append(f"[{mtl_path.name}]({METEL_CORE_GITHUB_BLOB}/{rel.as_posix()})")
    if not links:
        return ""
    # See origins_block_text's comment: inline <span>, not a block tag, so
    # the [name](url) links above still parse as markdown inside it.
    return f'<span class="rigor-backlink">_Tested by: {", ".join(links)}_</span>'


def regenerate_backlinks_in_text(text, spec_path, origins_by_id, fixtures_by_id, core_root):
    """Rewrites every rigor block's origins slot and (when reachable) its
    fixtures slot in `text` to match `origins_by_id`/`fixtures_by_id`,
    leaving everything else byte-identical. Idempotent -- an existing marker
    pair (stale or current) is always removed and a fresh one (or none, if
    that slot is now empty) is appended, so running this twice in a row on
    already-current content produces no further change.

    fixtures_by_id is None when metel-interpreter/tests isn't reachable
    (ADR-0049 §6): an existing fixtures slot is then carried over exactly as
    it already reads, since unreachability says nothing about whether that
    content is still accurate -- only a fixture-reachable run may add,
    change, or remove it. origins_by_id is never None; it only needs this
    repo's own RFC frontmatter, so it's always regenerated."""
    lines = text.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        m = SPEC_BLOCK_HEADING_RE.match(line)
        if not m:
            i += 1
            continue
        spec_id = m.group("id")
        i += 1
        body = []
        existing_fixtures_content = None
        while i < n:
            nxt = lines[i]
            if SPEC_BLOCK_HEADING_RE.match(nxt) or nxt.strip() == "</details>":
                break
            if nxt.strip() == ORIGINS_MARKER_START:
                i += 1
                while i < n and lines[i].strip() != ORIGINS_MARKER_END:
                    i += 1
                i += 1  # consume the end marker itself
                continue
            if nxt.strip() == FIXTURES_MARKER_START:
                i += 1
                slot = []
                while i < n and lines[i].strip() != FIXTURES_MARKER_END:
                    slot.append(lines[i])
                    i += 1
                i += 1  # consume the end marker itself
                existing_fixtures_content = "\n".join(slot).strip()
                continue
            body.append(nxt)
            i += 1
        while body and body[-1].strip() == "":
            body.pop()
        out.extend(body)

        origins_content = origins_block_text(spec_path, origins_by_id.get(spec_id, []))
        if origins_content:
            out.append("")
            out.append(ORIGINS_MARKER_START)
            out.append(origins_content)
            out.append(ORIGINS_MARKER_END)

        if fixtures_by_id is None:
            fixtures_content = existing_fixtures_content
        else:
            fixtures_content = fixtures_block_text(fixtures_by_id.get(spec_id, []), core_root)
        if fixtures_content:
            out.append("")
            out.append(FIXTURES_MARKER_START)
            out.append(fixtures_content)
            out.append(FIXTURES_MARKER_END)

        out.append("")
    return "\n".join(out)


def write_spec_origins():
    """rfc.py index --write-spec-origins (ADR-0050 §3a). Regenerates every
    rigor block's RFC-origins backlink unconditionally, and its fixture
    backlink too when metel-interpreter/tests is reachable (ADR-0049 §6) --
    run from a bare docs-internal checkout, only the origins slot is
    touched. Returns the list of spec files actually changed."""
    origins_by_id = compute_spec_origins_from_rfcs()
    tests_dir = metel_core_tests_dir()
    fixtures_by_id = scan_spec_citations(tests_dir) if tests_dir is not None else None
    core_root = tests_dir.parent.parent if tests_dir is not None else None
    changed = []
    for spec_path in sorted(SPEC_DIR.glob("*.md")):
        text = spec_path.read_text()
        new_text = regenerate_backlinks_in_text(
            text, spec_path, origins_by_id, fixtures_by_id, core_root
        )
        if new_text != text:
            spec_path.write_text(new_text)
            changed.append(spec_path)
    return changed


def spec_origins_drift_problems():
    """ADR-0050 §3a, the --check-drift half: which spec files' backlink
    slots no longer match what --write-spec-origins would produce -- a hand
    edit, an RFC's coverage.spec link changing, or a fixture's spec=
    citation changing, without regenerating after. Fixture-slot drift can
    only be checked when metel-interpreter/tests is reachable (ADR-0049
    §6); from a bare docs-internal checkout this validates the origins slot
    only, same as before fixtures backlinks existed."""
    origins_by_id = compute_spec_origins_from_rfcs()
    tests_dir = metel_core_tests_dir()
    fixtures_by_id = scan_spec_citations(tests_dir) if tests_dir is not None else None
    core_root = tests_dir.parent.parent if tests_dir is not None else None
    problems = []
    for spec_path in sorted(SPEC_DIR.glob("*.md")):
        text = spec_path.read_text()
        if (
            regenerate_backlinks_in_text(text, spec_path, origins_by_id, fixtures_by_id, core_root)
            != text
        ):
            problems.append(
                f"{spec_path.relative_to(REPO_ROOT)}: origins/fixtures backlinks are stale -- "
                f"run `rfc.py index --write-spec-origins`"
            )
    return problems


def collect_rfc_records():
    records = []
    for path in find_rfc_files():
        rid = rfc_id_from_filename(path)
        fm, _ = parse_file(path)
        stage = STAGE_FOR_DIR[path.parent.name]
        records.append({
            "id": rid,
            "title": fm.get("title", path.stem),
            "stage": stage,
            "stage_dir": path.parent.name,
            "path": path.relative_to(REPO_ROOT),
            "date": fm.get("date", ""),
            "updated": fm.get("updated", ""),
            "impl_status": fm.get("impl_status", ""),
            "impl_tracking": fm.get("impl_tracking", ""),
        })
    records.sort(key=lambda r: rfc_sort_key(r["id"]))
    return records


def build_registry_text(records=None):
    records = collect_rfc_records() if records is None else records
    by_stage = {stage: [] for stage in STAGES}
    for rec in records:
        by_stage[rec["stage"]].append(rec)
    counts = {stage: len(items) for stage, items in by_stage.items()}
    total = len(records)
    live = counts["draft"] + counts["under-review"] + counts["accepted"] + counts["integrated"]
    settled = counts["implemented"] + counts["superseded"] + counts["refused"]

    lines = [
        "---",
        "id: rfc-registry",
        'title: "RFC Registry"',
        "type: registry",
        f"generated_on: '{today()}'",
        "---",
        "",
        "# RFC Registry",
        "",
        "This file is generated by `public/rfcs/tools/rfc.py index --rebuild-registry`.",
        "Do not edit it by hand. It is the authoritative RFC state inventory; `INDEX.md` is",
        "the curated thematic map.",
        "",
        "**Every `implemented`/`integrated` RFC listed below is checked by CI, on every "
        "push, for regressed fixture coverage** — `rfc.py check` (metel-core's `rfc-check` "
        "job; degrades to an informational skip when run from a bare docs-internal "
        "checkout, see ADR-0049 §6) fails if any RFC's uncovered normative sections grow "
        "past what `public/rfcs/COVERAGE-BASELINE.json` already grandfathers in. This is "
        "the retroactive half of ADR-0049's coverage mandate (§7); the forward-looking half "
        "is `rfc.py transition --to implemented` itself refusing to run over an uncovered "
        "section.",
        "",
        f"**{total} RFCs total.** {counts['draft']} draft, {counts['under-review']} under review, "
        f"{counts['accepted']} accepted, {counts['integrated']} integrated ({live} live), "
        f"{counts['implemented']} implemented, {counts['superseded']} superseded, "
        f"{counts['refused']} refused ({settled} settled).",
        "",
    ]

    stage_titles = [
        ("draft", "Draft"),
        ("under-review", "Under Review"),
        ("accepted", "Accepted"),
        ("integrated", "Integrated"),
        ("implemented", "Implemented"),
        ("superseded", "Superseded"),
        ("refused", "Refused"),
    ]
    for stage, title in stage_titles:
        entries = by_stage[stage]
        lines.append(f"## {title} ({len(entries)})")
        lines.append("")
        if not entries:
            lines.append("*(none)*")
            lines.append("")
            continue
        for rec in entries:
            meta = [f"`{rec['stage_dir']}`", str(rec["path"])]
            if rec["date"]:
                meta.append(f"date {rec['date']}")
            if rec["updated"]:
                meta.append(f"updated {rec['updated']}")
            if rec["impl_status"]:
                meta.append(f"impl {rec['impl_status']}")
            if rec["impl_tracking"]:
                meta.append(f"tracking {rec['impl_tracking']}")
            lines.append(
                f"- **{rec['id'].upper()}** — {rec['title']} "
                f"({' ; '.join(meta)})"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def rebuild_registry():
    REGISTRY_PATH.write_text(build_registry_text())


def _without_generated_on_stamp(text):
    # `build_registry_text()` always stamps `generated_on` with *today's* date.
    # Diffing that directly against a committed file would report drift on any
    # day after the file was actually generated, even with zero real content
    # change — the stamp, not the content, would be the only difference. Real
    # staleness is about content (RFC list, stages, dates), so normalize the
    # one field that's expected to differ before comparing.
    return re.sub(r"^generated_on: '.*'$", "generated_on: 'IGNORED'", text, count=1, flags=re.MULTILINE)


def registry_drift_problem():
    expected = build_registry_text()
    if not REGISTRY_PATH.exists():
        return "public/rfcs/REGISTRY.md is missing — run `rfc.py index --rebuild-registry`"
    actual = REGISTRY_PATH.read_text()
    if _without_generated_on_stamp(actual) != _without_generated_on_stamp(expected):
        return "public/rfcs/REGISTRY.md is stale or hand-edited — run `rfc.py index --rebuild-registry`"
    return None


def retired_host_references():
    """Flag references to a retired host (RETIRED_HOSTS) in two places: any RFC's
    impl_tracking field (structured, checked directly against parsed frontmatter —
    this field must always resolve, so any non-canonical host is unambiguously
    wrong), and any live URL in `public/`'s body text (the exported/published
    surface a reader could actually click — `reports/` and `internal/` are
    deliberately excluded, since `reports/strategy/`'s dated overviews and
    OBJECTIVES.md legitimately discuss a retired host in past-tense narrative, and
    `internal/archive/` is an intentional historical snapshot, not live content —
    see `public/rfcs/PROCESS.md`'s "dated documents" rule for the same distinction
    applied to code samples). Zero network calls; pure text matching, so this runs
    on every `check`, not just `cycle-prep`."""
    problems = []
    for path in find_rfc_files():
        fm, _ = parse_file(path)
        tracking = fm.get("impl_tracking", "")
        if tracking and any(h in tracking for h in RETIRED_HOSTS):
            rel = str(path.relative_to(REPO_ROOT))
            problems.append(
                f"{rel}: impl_tracking references a retired host ({tracking}) — "
                f"canonical host is {CANONICAL_ISSUE_HOST}"
            )
    for f in sorted((REPO_ROOT / "public").rglob("*.md")):
        rel = str(f.relative_to(REPO_ROOT))
        try:
            _, body = parse_file(f)
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(body.splitlines(), start=1):
            for h in RETIRED_HOSTS:
                if h in line:
                    problems.append(f"{rel}:{lineno}: references a retired host ({h}): {line.strip()[:120]}")
                    break
    return problems


def rfc_git_staleness(records):
    """Best-effort, informational only (never added to `check`'s hard-fail list):
    for each RFC with an `updated` frontmatter date, compare it against git's own
    last-touch date for that file. A mismatch isn't necessarily wrong — a
    repo-wide sweep (a rename, a reference-rewrite pass) touches a file without
    its content meaningfully changing — but it is exactly the shape of drift
    Trigger 16 caught in RFC-0097, so a reader deserves to see the disagreement
    rather than trust `updated:` on faith. Skipped silently if git is
    unavailable.

    **Known limitation, honestly unresolved rather than papered over (2026-08-06):**
    this repo's last month includes two real mass-sweep events (the GitHub
    migration's ~307 path rewrites, the reference-rot fix's 659 substitutions
    across 77 files) that touch nearly the whole corpus without representing a
    design change — this function can't yet distinguish "content meaningfully
    changed" from "swept as part of an unrelated repo-wide edit," so on this
    corpus, as of this writing, it flags roughly half of all RFCs. `cmd_cycle_prep`
    caps how many rows it prints for exactly this reason. Filed as `OBJECTIVES.md`
    §2a Pending Recommendation 2 rather than shipped as if solved — a
    commit-message- or content-diff-based filter is the likely fix, not yet built."""
    rows = []
    for rec in records:
        if not rec.get("updated"):
            continue
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(rec["path"])],
                check=True, cwd=REPO_ROOT, capture_output=True, text=True,
            )
        except (subprocess.CalledProcessError, OSError):
            continue
        last_touch = out.stdout.strip()
        if last_touch and last_touch != rec["updated"]:
            rows.append((rec["id"], rec["updated"], last_touch))
    return rows


def fetch_open_milestones(owner="metel-lang", repo="metel-core"):
    """Best-effort GitHub REST call for open milestones and their issue counts —
    a single request replaces resolving priority-relevant issues one at a time
    (the shape of most of a manual cycle's tool-call cost). Needs GITHUB_TOKEN or
    GH_TOKEN in the environment; returns (milestones, None) on success or
    (None, reason) on any failure, network or auth — never raises, per §2's
    discipline that an unverifiable claim should say so rather than silently
    omit itself."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None, "no GITHUB_TOKEN/GH_TOKEN in environment — issue-tracker state not checked"
    url = f"https://api.github.com/repos/{owner}/{repo}/milestones?state=open&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "rfc.py-cycle-prep",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        return None, f"GitHub API request failed ({e}) — issue-tracker state not checked"
    milestones = [
        {
            "title": m.get("title", ""),
            "open_issues": m.get("open_issues", 0),
            "closed_issues": m.get("closed_issues", 0),
            "html_url": m.get("html_url", ""),
        }
        for m in data
    ]
    return milestones, None


def index_mentioned_rfc_ids(text):
    ids = set()
    for m in re.finditer(r"RFC-(\d+[a-z]?)", text, flags=re.IGNORECASE):
        ids.add(normalize_id(m.group(1)))
    return ids


def spec_mentions(rid):
    """Does anything under public/reference/spec/ reference this RFC id? Case-insensitive
    — callouts sometimes cite a lowercase file path (rfc-0067a-...md) rather than the
    RFC-0067a prose form, and both should count."""
    if not SPEC_DIR.is_dir():
        return False
    needle = rid.lower()
    for f in SPEC_DIR.rglob("*.md"):
        try:
            if needle in f.read_text().lower():
                return True
        except (UnicodeDecodeError, OSError):
            continue
    return False


NOT_IMPLEMENTED_RE = re.compile(r"not yet implemented", re.IGNORECASE)


def spec_not_implemented_refs(rid):
    """Lines under public/reference/spec/ that read as a "Not yet implemented" callout
    *for this specific RFC* — the phrase appears on the line, and the line's own
    `public/rfcs/.../rfc-....md` path reference (not just any RFC number mentioned in
    passing, e.g. background context about an older, unrelated RFC) resolves to this id.
    These callouts are required to be one-liners (PROCESS.md) specifically so this check
    (and a human deleting one by hand) never has to figure out where a multi-line
    blockquote ends."""
    if not SPEC_DIR.is_dir():
        return []
    hits = []
    for f in sorted(SPEC_DIR.rglob("*.md")):
        try:
            lines = f.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(lines, start=1):
            if not NOT_IMPLEMENTED_RE.search(line):
                continue
            for m in PATH_REF_RE.finditer(line):
                if rfc_id_from_filename(Path(m.group(0))) == rid:
                    hits.append((f.relative_to(REPO_ROOT), lineno, line.strip()))
                    break
    return hits


# --------------------------------------------------------------------------
# Inline status citations — "RFC-0044 (Explicit Receiver Semantics,
# implemented)" — checked against the cited RFC's actual current stage. This
# is prose, not frontmatter, so it can go stale silently the moment the cited
# RFC transitions; a human has to notice by reading, which is exactly the
# class of drift REGISTRY.md/INDEX.md's own automated checks exist to avoid
# for every *other* kind of cross-reference.
# --------------------------------------------------------------------------

# Word boundaries matter here: "unimplemented" must not match "implemented" —
# and it doesn't, because \b requires a transition to/from a non-word char, and
# there is none between "un" and "implemented" in one contiguous word.
STATUS_WORD_RE = re.compile(
    r"\b(draft|under-review|under review|accepted|integrated|implemented|superseded|refused)\b",
    re.IGNORECASE,
)
# An RFC id immediately followed by a parenthetical — "RFC-0044 (...)" — is
# this repo's established convention for annotating a cross-referenced RFC's
# current status inline. Capped at 200 chars so a multi-sentence parenthetical
# aside elsewhere in a line can't accidentally sprawl the match.
STATUS_CITATION_RE = re.compile(r"RFC-(\d+[a-z]?)\s*\(([^)]{0,200})\)")


def status_citation_problems(id_to_stage):
    problems = []
    for f in REPO_ROOT.rglob("*.md"):
        # "archive" dirs (reports/**/archive/) hold dated, superseded snapshots —
        # citing an RFC's then-current status there is historically correct, not
        # stale, and must not be "fixed" to match the present.
        if ".git" in f.parts or "archive" in f.parts or f == REGISTRY_PATH:
            continue
        try:
            lines = f.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = f.relative_to(REPO_ROOT)
        for lineno, line in enumerate(lines, start=1):
            for m in STATUS_CITATION_RE.finditer(line):
                rid = normalize_id(m.group(1))
                actual = id_to_stage.get(rid)
                if actual is None:
                    continue  # unknown/renumbered/non-Metel id — not this check's job
                words = {w.lower().replace(" ", "-") for w in STATUS_WORD_RE.findall(m.group(2))}
                words &= set(STAGES)
                if len(words) != 1:
                    continue  # no status word, or more than one — don't guess which is "the" claim
                cited = next(iter(words))
                if cited != actual:
                    problems.append(
                        f"{rel}:{lineno}: cites {rid.upper()} as '{cited}' but it is "
                        f"currently '{actual}' ({STAGES[actual]})"
                    )
    return problems


# --------------------------------------------------------------------------
# RFC section <-> fixture coverage (ADR-0049)
# --------------------------------------------------------------------------
#
# Cross-repo by construction: the fixture corpus lives in metel-interpreter/
# tests/, one level up from REPO_ROOT, reachable only when this checkout is
# embedded as metel-core's docs/ submodule (or METEL_CORE_ROOT points at a
# sibling checkout). `check` degrades to an informational skip when it isn't
# reachable; `transition --to implemented` refuses outright instead --
# "unknown" must not be treated as "pass" for the one command that actually
# marks something implemented. See ADR-0049 §5/§6 for why these two commands
# are not allowed to behave the same way here.

COVERAGE_NONNORMATIVE_TITLES = {
    "summary", "motivation", "background", "prior art", "alternatives considered",
    "open questions", "references", "decision", "unresolved questions",
}

# Section headers: `## N.` or `### N.M.`, with an optional letter suffix on
# either part (`9c`, `3a`) -- real, used across RFC-0071/0082/0118/0067a/0110.
COVERAGE_SECTION_HEADER_RE = re.compile(
    # Top-level headers carry a period after the number (`## 7. Function
    # Types`); subsection headers don't (`### 7.1 Callable`, straight to the
    # title) -- the period has to be optional, not required, or every
    # subsection header in the corpus fails to match.
    r"^(#{2,3})\s+(\d+[a-z]?(?:\.\d+[a-z]?)?)\.?\s+(.+)$", re.MULTILINE
)
# A citation: `rfc-NNNN` or `rfc-NNNN§section`, case-insensitive on `rfc`.
# The RFC id itself can carry the same optional letter suffix the section
# grammar already allows -- `rfc-0067a` is a real, distinct RFC id
# (Reference Types), not a typo for `rfc-0067` (a different RFC, Lifetime
# Anchors). Found the hard way: an earlier version of this regex accepted
# only a bare 4-digit id, and a migration pass silently mis-cited fixtures
# against the wrong RFC as a result -- this validator would have caught it
# immediately if it had been correct from the start.
COVERAGE_CITATION_RE = re.compile(
    r"rfc-(\d{4}[a-z]?)(?:§(\d+[a-z]?(?:\.\d+[a-z]?)?))?", re.IGNORECASE
)
COVERAGE_TOML_RFC_LIST_RE = re.compile(r"^\s*rfc\s*=\s*\[(.*?)\]\s*$", re.MULTILINE)
COVERAGE_FM_ENTRY_RE = re.compile(
    r'"(?P<section>[^"]+)"\s*:\s*\{\s*kind:\s*(?P<kind>\w+)\s*,\s*reason:\s*"(?P<reason>[^"]*)"'
    r'(?:\s*,\s*ref:\s*"(?P<ref>[^"]*)")?\s*\}'
)
COVERAGE_INLINE_RE = re.compile(r"^>\s*\*\*Coverage:\s*(?P<kind>\w+)\*\*")
COVERAGE_VALID_KINDS = {"untestable", "blocked", "elsewhere"}

# ADR-0050 §5: an `options.spec` sidecar citation, and the RFC-frontmatter
# link that points a section at one. Grammar per ADR-0050 §3 --
# `spec.<file>.<section>.<kind>-<n>`, no colons anywhere (Docusaurus's
# `{#custom-id}` heading attribute silently corrupts a colon rather than
# rejecting it, found by running a real `docusaurus build`; the grammar
# avoids the character entirely). `<section>` is one or more dot-separated
# segments, hence the `+` on the middle group -- `file` and `kind-n` are
# each exactly one segment, everything between them is `section`.
COVERAGE_SPEC_ID_RE = re.compile(
    r"spec\.[a-z0-9-]+(?:\.[a-z0-9-]+)+\.(?:legality|dynamics)-\d+[a-z]*"
)
COVERAGE_TOML_SPEC_LIST_RE = re.compile(r"^\s*spec\s*=\s*\[(.*?)\]\s*$", re.MULTILINE)
# A distinct shape from COVERAGE_FM_ENTRY_RE (`spec:` instead of `kind:`) so
# the two never collide -- an RFC-to-spec-id link isn't a typed exemption
# and doesn't participate in COVERAGE_VALID_KINDS validation at all.
COVERAGE_FM_SPEC_ENTRY_RE = re.compile(
    r'"(?P<section>[^"]+)"\s*:\s*\{\s*spec:\s*"(?P<spec_id>[^"]+)"\s*\}'
)


def metel_core_tests_dir():
    """Locate metel-interpreter/tests (ADR-0049 §6). None, not an error, when
    unreachable -- callers decide whether that's a skip or a hard failure."""
    override = os.environ.get("METEL_CORE_ROOT")
    if override:
        candidate = Path(override) / "metel-interpreter" / "tests"
        return candidate if candidate.is_dir() else None
    candidate = REPO_ROOT.parent / "metel-interpreter" / "tests"
    return candidate if candidate.is_dir() else None


def rfc_normative_sections(body):
    """Section numbers from the body's own headers, excluding the
    non-normative titles ADR-0049 §2 names by name."""
    out = []
    for m in COVERAGE_SECTION_HEADER_RE.finditer(body):
        num, title = m.group(2), m.group(3).strip()
        clean = re.sub(r"[*`]", "", title).strip()
        lead = re.split(r"[—\-:]", clean)[0].strip().lower()
        if lead not in COVERAGE_NONNORMATIVE_TITLES:
            out.append(num)
    return out


def frontmatter_raw_text(path_or_text):
    """Raw text between the `---` fences, for the nested `coverage:` block
    parse_file()'s flat scalar-only parser can't handle."""
    text = path_or_text if isinstance(path_or_text, str) else path_or_text.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    end_idx = len(lines)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    return "\n".join(lines[1:end_idx])


def parse_coverage_frontmatter(fm_text):
    """`coverage:` block per ADR-0049 §3's grammar -> {section: (kind, reason, ref)}."""
    if "coverage:" not in fm_text:
        return {}
    return {
        m.group("section"): (m.group("kind"), m.group("reason"), m.group("ref"))
        for m in COVERAGE_FM_ENTRY_RE.finditer(fm_text)
    }


def parse_coverage_spec_links(fm_text):
    """`coverage:` block entries of the form `"N": { spec: "spec.xxx" }` --
    ADR-0050 §5's RFC-to-spec-id link, the first of its two independent
    checks. Lives in the same `coverage:` block as ADR-0049 §3's typed
    exemptions but is a structurally distinct entry shape (no `kind`), so it
    never matches COVERAGE_FM_ENTRY_RE and never enters that check's
    kind-validation loop. -> {section: spec_id}."""
    if "coverage:" not in fm_text:
        return {}
    return {
        m.group("section"): m.group("spec_id")
        for m in COVERAGE_FM_SPEC_ENTRY_RE.finditer(fm_text)
    }


def parse_inline_coverage(body):
    """Map each `> **Coverage: kind**` callout to the section header
    immediately preceding it, for the frontmatter/inline drift check."""
    out = {}
    last_section = None
    for line in body.splitlines():
        hm = re.match(r"^(#{2,3})\s+(\d+[a-z]?(?:\.\d+[a-z]?)?)\.?\s+", line)
        if hm:
            last_section = hm.group(2)
            continue
        im = COVERAGE_INLINE_RE.match(line.strip())
        if im and last_section:
            out[last_section] = im.group("kind")
    return out


def scan_fixture_citations(tests_dir):
    """(sidecar, prose): each {rid: [(section_or_None, path)]}, the two
    citation surfaces ADR-0049 §1 keeps in sync by convention, not by force."""
    sidecar, prose = {}, {}
    for toml_path in tests_dir.rglob("*.toml"):
        try:
            text = toml_path.read_text()
        except OSError:
            continue
        m = COVERAGE_TOML_RFC_LIST_RE.search(text)
        if not m:
            continue
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            cm = COVERAGE_CITATION_RE.fullmatch(item.strip())
            if cm:
                rid = f"rfc-{cm.group(1).lower()}"
                sidecar.setdefault(rid, []).append((cm.group(2), toml_path))
    for mtl_path in tests_dir.rglob("*.mtl"):
        try:
            text = mtl_path.read_text(errors="replace")
        except OSError:
            continue
        for cm in COVERAGE_CITATION_RE.finditer(text):
            line_start = text.rfind("\n", 0, cm.start()) + 1
            line_end = text.find("\n", cm.start())
            line = text[line_start: line_end if line_end != -1 else None]
            if not line.strip().startswith("//"):
                continue
            rid = f"rfc-{cm.group(1).lower()}"
            prose.setdefault(rid, []).append((cm.group(2), mtl_path))
    return sidecar, prose


def scan_spec_citations(tests_dir):
    """{spec_id: [toml_path, ...]} -- ADR-0050 §5's spec-id -> fixture check,
    the second of its two independent checks. Mirrors scan_fixture_citations'
    sidecar half; spec ids have no prose-comment convention (nothing has
    migrated a prose citation yet, and ADR-0050 doesn't specify one the way
    ADR-0049 §1 does for `rfc =`), so there's no separate prose surface to
    scan here."""
    out = {}
    for toml_path in tests_dir.rglob("*.toml"):
        try:
            text = toml_path.read_text()
        except OSError:
            continue
        m = COVERAGE_TOML_SPEC_LIST_RE.search(text)
        if not m:
            continue
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            item = item.strip()
            if COVERAGE_SPEC_ID_RE.fullmatch(item):
                out.setdefault(item, []).append(toml_path)
    return out


def _sidecar_mtl_path(toml_path):
    return (
        toml_path.parent / "main.mtl"
        if toml_path.name == "test.toml"
        else toml_path.with_suffix(".mtl")
    )


def scan_coverage_corpus():
    """ADR-0049. The corpus-wide scan `coverage_check_problems()` and the
    `--write-coverage-baseline` writer both need: every RFC's normative
    sections, its `coverage` frontmatter/inline exemptions and stage, plus the
    fixture corpus's sidecar/prose citations. Factored out so the two only
    disagree about what they *do* with this, never about how it's gathered.
    None (not an error) when metel-interpreter/tests isn't reachable -- see
    ADR-0049 §6; callers degrade independently from there."""
    tests_dir = metel_core_tests_dir()
    if tests_dir is None:
        return None

    rfc_sections, rfc_coverage_fm, rfc_coverage_inline, rfc_coverage_spec, rfc_stage = (
        {}, {}, {}, {}, {},
    )
    for f in find_rfc_files():
        rid = rfc_id_from_filename(f)
        if rid is None:
            continue
        rfc_stage[rid] = STAGE_FOR_DIR.get(f.parent.name)
        text = f.read_text()
        _, body = parse_file(f)
        rfc_sections[rid] = set(rfc_normative_sections(body))
        rfc_coverage_fm[rid] = parse_coverage_frontmatter(frontmatter_raw_text(text))
        rfc_coverage_inline[rid] = parse_inline_coverage(body)
        rfc_coverage_spec[rid] = parse_coverage_spec_links(frontmatter_raw_text(text))

    sidecar, prose = scan_fixture_citations(tests_dir)
    spec_citations = scan_spec_citations(tests_dir)
    return (
        rfc_sections,
        rfc_coverage_fm,
        rfc_coverage_inline,
        rfc_coverage_spec,
        rfc_stage,
        sidecar,
        prose,
        spec_citations,
    )


def per_rfc_coverage(
    rfc_sections, rfc_coverage_fm, rfc_coverage_spec, rfc_stage, sidecar, prose, spec_citations
):
    """ADR-0049 §5/§9, extended by ADR-0050 §5: {rid: (sections, uncovered,
    whole_rfc_kind, spec_anchored, rfc_only)} for every `implemented`/
    `integrated` RFC, sorted by rfc_sort_key. `whole_rfc_kind` is the "*"
    exemption's kind string for a whole-RFC-exempt RFC (`uncovered`,
    `spec_anchored`, and `rfc_only` are then always empty, by construction);
    None for an ordinary RFC, where `uncovered` is what's left after direct
    citations, spec-anchored coverage, and per-section exemptions are all
    subtracted from its normative sections.

    A section counts as spec-anchored covered when *both* of ADR-0050 §5's
    independent checks hold: the RFC's own `coverage` frontmatter links it to
    a `spec.` id (rfc_coverage_spec), *and* that id has its own citing
    fixture (spec_citations) -- a link with nothing citing it, or a citing
    fixture nothing links to, doesn't count. This is the composition ADR-0050
    §8 describes for a `3-integrated`+ RFC whose claims have been re-anchored;
    it deliberately doesn't replace direct `rfc =` citation, which stays live
    for every RFC that hasn't been re-anchored (ADR-0050 §8's pre-integration
    phase, and any not-yet-migrated section of an integrated one).

    `spec_anchored` and `rfc_only` split `uncovered`'s complement into "moved
    to the spec-anchored mechanism" and "covered, but still only via a direct
    `rfc =`/prose citation" -- the two numbers the migration this ADR-0050
    §8 sequences is meant to move between. A section cited both ways at once
    (mid-migration, ADR-0050 §7) counts as spec_anchored only, since that's
    the state the migration is aiming for; it's not double-counted."""
    out = {}
    for rid in sorted(rfc_sections, key=rfc_sort_key):
        if rfc_stage.get(rid) not in ("implemented", "integrated"):
            continue
        sections = rfc_sections[rid]
        fm_cov = rfc_coverage_fm.get(rid, {})
        if "*" in fm_cov:
            out[rid] = (sections, set(), fm_cov["*"][0], set(), set())
            continue
        if not sections:
            continue
        direct_cited = {s for s, _ in sidecar.get(rid, [])} | {s for s, _ in prose.get(rid, [])}
        direct_cited.discard(None)
        spec_links = rfc_coverage_spec.get(rid, {})
        spec_anchored = {
            section for section, spec_id in spec_links.items() if spec_citations.get(spec_id)
        }
        rfc_only = direct_cited - spec_anchored
        cited = direct_cited | spec_anchored
        exempted = set(fm_cov)
        uncovered = sections - cited - exempted
        out[rid] = (sections, uncovered, None, spec_anchored, rfc_only)
    return out


def load_coverage_baseline():
    """ADR-0049 §7: the committed snapshot `check`'s coverage ratchet compares
    against, grandfathering in whatever gaps existed when it was last written
    (`rfc.py index --write-coverage-baseline`) so pre-existing, already-tracked
    gaps don't fail every run, while any *new* gap on top of that does. None
    (not an error) when the file doesn't exist yet -- callers treat that as "no
    ratchet enforced yet," the same degrade-not-fail treatment the rest of this
    check gives an unreachable fixture corpus."""
    if not COVERAGE_BASELINE_PATH.is_file():
        return None
    try:
        return json.loads(COVERAGE_BASELINE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def build_coverage_baseline_json(coverage_by_rfc):
    """{rid: [uncovered section ids]} for every RFC with at least one gap --
    fully-covered RFCs and "*" whole-RFC exemptions (always zero-gap by
    construction) are simply absent, keeping the file's diff focused on what's
    actually being grandfathered in rather than restating every RFC that
    already needs nothing."""
    baseline = {
        rid: sorted(uncovered)
        for rid, (_sections, uncovered, _kind, _spec_anchored, _rfc_only) in coverage_by_rfc.items()
        if uncovered
    }
    return json.dumps(baseline, indent=2, sort_keys=True) + "\n"


def coverage_check_problems():
    """ADR-0049. Returns (problems, info_lines) -- problems are check
    failures; info_lines is either the single skip note or the per-RFC
    coverage summary, always printed, never counted as a failure itself."""
    scanned = scan_coverage_corpus()
    if scanned is None:
        return [], [
            "coverage: metel-interpreter/tests not reachable, skipped "
            "(set METEL_CORE_ROOT, or run from within metel-core; see ADR-0049 §6)"
        ]
    (
        rfc_sections,
        rfc_coverage_fm,
        rfc_coverage_inline,
        rfc_coverage_spec,
        rfc_stage,
        sidecar,
        prose,
        spec_citations,
    ) = scanned

    problems = []

    # 1. Every cited section exists in the target RFC (renumbering drift),
    #    and every cited RFC exists at all.
    for source_name, source in (("sidecar", sidecar), ("prose", prose)):
        for rid, entries in source.items():
            for section, path in entries:
                rel = path.relative_to(REPO_ROOT.parent) if REPO_ROOT.parent in path.parents else path
                if rid not in rfc_sections:
                    problems.append(f"{rel}: cites unknown RFC `{rid}` ({source_name})")
                elif section is not None and section not in rfc_sections[rid]:
                    problems.append(
                        f"{rel}: cites `{rid}§{section}` ({source_name}), but that "
                        f"section doesn't exist in {rid} -- renumbering drift?"
                    )

    # 1b. ADR-0050 §5's RFC -> spec-id link: the linked section must exist in
    #     its own RFC (same renumbering-drift concern as 1, one hop over),
    #     and the spec id itself must match ADR-0050 §3's grammar. Does *not*
    #     check the id resolves to a real block in an actual spec file --
    #     that needs scanning the spec markdown corpus for `{#...}` anchors,
    #     deliberately out of scope here; a link with a well-formed but
    #     nonexistent id currently just reads as "not covered" rather than
    #     "malformed", since nothing cites a nonexistent id either.
    for rid, spec_links in rfc_coverage_spec.items():
        for section, spec_id in spec_links.items():
            if rid in rfc_sections and section not in rfc_sections[rid]:
                problems.append(
                    f"{rid}: coverage[{section!r}] links spec id `{spec_id}`, but "
                    f"section {section!r} doesn't exist in {rid} -- renumbering drift?"
                )
            if not COVERAGE_SPEC_ID_RE.fullmatch(spec_id):
                problems.append(
                    f"{rid} §{section}: spec link `{spec_id}` doesn't match ADR-0050's "
                    f"`spec.<file>.<section>.<kind>-<n>` grammar"
                )

    # 2. Sidecar vs. prose drift, per (fixture, RFC) pair -- only when prose
    #    actually names a section. A bare `RFC-0061` prose mention next to a
    #    section-precise sidecar citation is expected during migration, not
    #    a conflict: prose being less specific isn't prose being wrong.
    prose_sections_by_file_rid = {}
    for rid, entries in prose.items():
        for section, path in entries:
            if section is not None:
                prose_sections_by_file_rid.setdefault((path, rid), set()).add(section)
    for rid, entries in sidecar.items():
        by_file = {}
        for section, path in entries:
            by_file.setdefault(path, set()).add(section)
        for toml_path, sidecar_sections in by_file.items():
            mtl_path = _sidecar_mtl_path(toml_path)
            prose_sections = prose_sections_by_file_rid.get((mtl_path, rid))
            if prose_sections is not None and prose_sections != sidecar_sections:
                problems.append(
                    f"{toml_path}: sidecar cites `{rid}` sections {sorted(sidecar_sections)}, "
                    f"but {mtl_path.name}'s prose comment cites sections "
                    f"{sorted(prose_sections)} -- drifted"
                )

    # 3b. `"*"` (ADR-0049 §9): a whole-RFC exemption, not a section-keyed one.
    #     Only valid for a genuinely sectionless RFC -- flag it if the body
    #     actually has real normative sections (then those need their own,
    #     individual exemptions or citations, not one blanket wildcard), and
    #     flag it if it's combined with other section keys in the same block
    #     (redundant -- "*" already covers everything those would).
    for rid, fm_cov in rfc_coverage_fm.items():
        if "*" not in fm_cov:
            continue
        if rfc_sections.get(rid):
            problems.append(
                f"{rid}: coverage[\"*\"] claims a whole-RFC exemption, but the RFC "
                f"has real normative sections ({', '.join(sorted(rfc_sections[rid]))}) "
                f"-- exempt or cite them individually instead"
            )
        extra = sorted(k for k in fm_cov if k != "*")
        if extra:
            problems.append(
                f"{rid}: coverage[\"*\"] (whole-RFC exemption) is combined with "
                f"other section keys ({', '.join(extra)}) -- \"*\" already exempts "
                f"everything, so per-section entries alongside it are redundant"
            )

    # 3. RFC frontmatter `coverage` vs. its own inline callout.
    for rid, fm_cov in rfc_coverage_fm.items():
        inline_cov = rfc_coverage_inline.get(rid, {})
        for section, (kind, _reason, _ref) in fm_cov.items():
            if kind not in COVERAGE_VALID_KINDS:
                problems.append(
                    f"{rid}: coverage[{section!r}].kind = {kind!r} is not one of "
                    f"{sorted(COVERAGE_VALID_KINDS)}"
                )
            if section in inline_cov and inline_cov[section] != kind:
                problems.append(
                    f"{rid} §{section}: frontmatter coverage says `{kind}`, "
                    f"inline callout says `{inline_cov[section]}` -- drifted"
                )
        for section in inline_cov:
            if section not in fm_cov:
                problems.append(
                    f"{rid} §{section}: inline coverage callout has no matching "
                    f"frontmatter `coverage` entry"
                )

    # 4. `blocked` refs: the referenced RFC must exist; flag (not fail --
    #    resolving the specific blocker is a semantic judgment this can't
    #    make) when it looks like it may have already landed.
    for rid, fm_cov in rfc_coverage_fm.items():
        for section, (kind, _reason, ref) in fm_cov.items():
            if kind == "blocked" and ref:
                ref_id = ref if re.match(r"rfc-\d{4}$", ref, re.IGNORECASE) else None
                if ref_id:
                    ref_id = ref_id.lower()
                    if ref_id not in rfc_stage:
                        problems.append(f"{rid} §{section}: blocked on `{ref}`, which doesn't exist")
                    elif rfc_stage[ref_id] == "implemented":
                        problems.append(
                            f"{rid} §{section}: blocked on `{ref}`, which is now "
                            f"4-implemented -- verify the blocker actually closed, and "
                            f"drop this exemption if so"
                        )

    # 5. Per-RFC coverage summary, informational -- what's uncovered after
    #    citations and exemptions are both counted. A `"*"` frontmatter entry
    #    (ADR-0049 §9) is a whole-RFC exemption: the RFC has no normative
    #    sections at all (checked above, in 3b), and the whole thing is
    #    exempted for the one stated reason. It still needs to show up here,
    #    not silently vanish the way a genuinely-forgotten sectionless RFC
    #    would -- that invisibility is exactly what this summary exists to
    #    prevent.
    #
    #    5b. The coverage ratchet (ADR-0049 §7), folded into the same loop:
    #    every `implemented`/`integrated` RFC is checked here, not only the
    #    one being transitioned right now the way `transition --to implemented`
    #    already does -- that gate only ever fires once, at the moment an RFC
    #    crosses into `implemented`; it says nothing about an RFC that was
    #    already there and has since regressed (a citation deleted, a fixture
    #    disabled). A gap already present in the committed baseline is
    #    grandfathered in -- burn-down is `blocked`/`untestable`/`elsewhere`
    #    exemptions and real fixtures closing it over time, tracked outside
    #    this script (see the RFC's own tracking issue). A *new* gap on top of
    #    that baseline fails `check`.
    coverage_by_rfc = per_rfc_coverage(
        rfc_sections, rfc_coverage_fm, rfc_coverage_spec, rfc_stage, sidecar, prose, spec_citations
    )
    baseline = load_coverage_baseline()
    info = []
    total_spec_anchored, total_rfc_only = 0, 0
    for rid, (sections, uncovered, whole_kind, spec_anchored, rfc_only) in coverage_by_rfc.items():
        if whole_kind is not None:
            info.append(f"  {rid}: whole-RFC exemption ({whole_kind}) -- no normative sections")
            continue
        covered_n = len(sections) - len(uncovered)
        # ADR-0050 §8: what's driving the migration this ADR sequences -- of
        # what's covered, how much has moved to spec-anchoring vs. still
        # sitting on a direct `rfc =`/prose citation. Silent when neither
        # applies (an RFC with only exemptions, or nothing covered at all),
        # so an RFC untouched by the migration doesn't clutter every line.
        migration_note = ""
        if spec_anchored or rfc_only:
            migration_note = (
                f" ({len(spec_anchored)} spec-anchored, {len(rfc_only)} still rfc-cited)"
            )
        total_spec_anchored += len(spec_anchored)
        total_rfc_only += len(rfc_only)
        info.append(
            f"  {rid}: {covered_n}/{len(sections)} normative sections covered"
            + (f" -- uncovered: {', '.join(sorted(uncovered))}" if uncovered else "")
            + migration_note
        )
        if baseline is not None:
            new_gaps = uncovered - set(baseline.get(rid, []))
            if new_gaps:
                problems.append(
                    f"{rid}: coverage regressed against public/rfcs/COVERAGE-BASELINE.json "
                    f"-- newly uncovered: {', '.join(sorted(new_gaps))}. Cite a fixture "
                    f"(`options.rfc` sidecar key) or add a `coverage` frontmatter exemption "
                    f"for each; if the gap is deliberate and already tracked elsewhere (e.g. "
                    f"a filed issue), update the baseline instead: "
                    f"`rfc.py index --write-coverage-baseline`"
                )
    if info:
        info.insert(0, "coverage summary (implemented/integrated RFCs):")
        migratable = total_spec_anchored + total_rfc_only
        if migratable:
            pct = 100 * total_spec_anchored / migratable
            info.append(
                f"spec-anchoring migration (ADR-0050 §8): {total_spec_anchored}/{migratable} "
                f"citable normative sections spec-anchored ({pct:.0f}%); "
                f"{total_rfc_only} still on a direct `rfc =`/prose citation"
            )
    return problems, info


def cmd_check(args=None):
    problems = []
    seen_ids = {}
    known_paths = set()
    current_ids = set()
    id_to_stage = {}

    for f in find_rfc_files():
        rel = str(f.relative_to(REPO_ROOT))
        known_paths.add(rel)
        rid = rfc_id_from_filename(f)
        current_ids.add(rid)
        if rid is None:
            problems.append(f"{rel}: filename doesn't match rfc-NNNN[letter] pattern")
            continue
        if rid in seen_ids:
            problems.append(f"duplicate RFC id {rid}: {seen_ids[rid]} and {rel}")
        else:
            seen_ids[rid] = rel

        fm, _ = parse_file(f)
        stage_dir = f.parent.name
        expected_status = STAGE_FOR_DIR.get(stage_dir)
        id_to_stage[rid] = expected_status
        fm_status = fm.get("status")
        if fm_status and expected_status and fm_status != expected_status:
            problems.append(
                f"{rel}: frontmatter status '{fm_status}' doesn't match directory "
                f"'{stage_dir}' (expected '{expected_status}')"
            )

        impl_status = fm.get("impl_status")
        impl_tracking = fm.get("impl_tracking")
        if expected_status == "integrated":
            # Hard-enforced: nothing enters 3-integrated without these (PROCESS.md).
            if not impl_tracking:
                problems.append(f"{rel}: missing impl_tracking (required from integrated onward)")
            if impl_status not in VALID_IMPL_STATUS:
                problems.append(
                    f"{rel}: impl_status is '{impl_status}', expected one of {sorted(VALID_IMPL_STATUS)}"
                )
            elif impl_status == "implemented":
                problems.append(
                    f"{rel}: impl_status is 'implemented' but the RFC is still in 3-integrated — "
                    f"run `rfc.py transition {rid} --to implemented`"
                )
            if not spec_mentions(rid):
                problems.append(
                    f"{rel}: no reference to {rid.upper()} found under public/reference/spec/ — "
                    "was it actually integrated into the spec text?"
                )
        elif expected_status == "implemented" and impl_status is not None:
            # Not retroactively required (25 RFCs predate this convention, adopted
            # 2026-07-10) — only checked for consistency when the field is present.
            if impl_status != "implemented":
                problems.append(
                    f"{rel}: RFC is in 4-implemented but impl_status is '{impl_status}', not 'implemented'"
                )

        if expected_status == "implemented":
            for spec_path, lineno, text in spec_not_implemented_refs(rid):
                problems.append(
                    f"{spec_path}:{lineno}: stale 'Not yet implemented' callout for "
                    f"{rid.upper()}, which is already 4-implemented — delete this line: {text}"
                )

    problems.extend(status_citation_problems(id_to_stage))
    problems.extend(retired_host_references())

    for f in REPO_ROOT.rglob("*.md"):
        if ".git" in f.parts:
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(f.relative_to(REPO_ROOT))
        for m in PATH_REF_RE.finditer(text):
            ref = m.group(0)
            if ref not in known_paths:
                problems.append(f"{rel}: dangling path reference '{ref}'")

    registry_problem = registry_drift_problem()
    if registry_problem:
        problems.append(registry_problem)

    if INDEX_PATH.exists():
        mentioned = index_mentioned_rfc_ids(INDEX_PATH.read_text())
        missing = sorted(current_ids - mentioned, key=rfc_sort_key)
        if missing:
            problems.append(
                "public/rfcs/INDEX.md is missing RFC mentions for: "
                + ", ".join(r.upper() for r in missing)
            )

    coverage_problems, coverage_info = coverage_check_problems()
    problems.extend(coverage_problems)

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("check: no problems found.")
    for line in coverage_info:
        print(line)
    return problems


# --------------------------------------------------------------------------
# index --check-drift / --suggest-placement
# --------------------------------------------------------------------------

def cmd_index(args):
    if not INDEX_PATH.exists():
        error(f"{INDEX_PATH} not found")

    if args.rebuild_registry:
        rebuild_registry()
        print(f"Rebuilt {REGISTRY_PATH.relative_to(REPO_ROOT)}")
        return

    if args.check_drift:
        problems = []
        registry_problem = registry_drift_problem()
        if registry_problem:
            problems.append(registry_problem)

        current_ids = {r["id"] for r in collect_rfc_records()}
        mentioned = index_mentioned_rfc_ids(INDEX_PATH.read_text())
        missing = sorted(current_ids - mentioned, key=rfc_sort_key)
        if missing:
            problems.append(
                "public/rfcs/INDEX.md is missing RFC mentions for: "
                + ", ".join(r.upper() for r in missing)
            )

        problems.extend(spec_origins_drift_problems())

        if problems:
            print("index drift found:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("RFC registry/index look current.")
        return

    if args.suggest_placement:
        rid = normalize_id(args.suggest_placement)
        target_path = find_path_for_id(rid)
        if target_path is None:
            error(f"RFC {rid} not found")
        clusters = parse_index_clusters(INDEX_PATH.read_text())
        if not clusters:
            error("no cluster sections found in INDEX.md")
        corpus = dict(rfc_corpus())
        docs = {}
        for cname, ids in clusters.items():
            tokens = []
            for cid in ids:
                if cid in corpus:
                    tokens += corpus[cid][1]
            if tokens:
                docs[cname] = tokens
        fm, body = parse_file(target_path)
        docs["__target__"] = tokenize(f"{fm.get('title', '')} {body[:3000]}")
        vectors = build_tfidf(docs)
        target_vec = vectors.pop("__target__")
        sims = sorted(
            ((cosine_sim(target_vec, v), cname) for cname, v in vectors.items()),
            reverse=True,
        )
        print(f"Cluster similarity for {rid.upper()}:")
        for score, cname in sims:
            print(f"  {score:.3f}  {cname}")
        return

    if args.write_coverage_baseline:
        scanned = scan_coverage_corpus()
        if scanned is None:
            error(
                "cannot write the coverage baseline: metel-interpreter/tests is not "
                "reachable from here (see ADR-0049 §6). Run this from a metel-core "
                "checkout with docs/ embedded as its submodule, or set "
                "METEL_CORE_ROOT to point at one."
            )
        (
            rfc_sections,
            rfc_coverage_fm,
            _rfc_coverage_inline,
            rfc_coverage_spec,
            rfc_stage,
            sidecar,
            prose,
            spec_citations,
        ) = scanned
        coverage_by_rfc = per_rfc_coverage(
            rfc_sections, rfc_coverage_fm, rfc_coverage_spec, rfc_stage, sidecar, prose, spec_citations
        )
        COVERAGE_BASELINE_PATH.write_text(build_coverage_baseline_json(coverage_by_rfc))
        gap_count = sum(
            1
            for _s, uncovered, kind, _spec_anchored, _rfc_only in coverage_by_rfc.values()
            if kind is None and uncovered
        )
        print(
            f"Wrote {COVERAGE_BASELINE_PATH.relative_to(REPO_ROOT)} "
            f"({gap_count} RFC(s) with a recorded gap)"
        )
        return

    if args.write_spec_origins:
        changed = write_spec_origins()
        if changed:
            print(
                f"Wrote origins backlinks in {len(changed)} spec file(s): "
                + ", ".join(str(p.relative_to(REPO_ROOT)) for p in changed)
            )
        else:
            print("Spec origins backlinks already current -- nothing to write.")
        return

    error(
        "index requires --check-drift, --rebuild-registry, --suggest-placement RFC-ID, "
        "--write-coverage-baseline, or --write-spec-origins"
    )


# Prefixes, not substrings — "Comptime / Derive cluster (... least settled cluster)"
# contains "settled" as a substring but is a real cluster, not the Settled section.
SKIP_SECTION_PREFIXES = ("settled", "maintenance note", "known issue")


def parse_index_clusters(text):
    clusters = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            lname = re.sub(r"^[^\w]+", "", name.lower())  # strip a leading emoji/symbol
            if any(lname.startswith(p) for p in SKIP_SECTION_PREFIXES) or "overlap" in lname[:40]:
                current = None
                continue
            current = name
            clusters[current] = []
        elif current is not None:
            for m in re.finditer(r"RFC-(\d+[a-z]?)", line):
                cid = f"rfc-{m.group(1)}"
                if cid not in clusters[current]:
                    clusters[current].append(cid)
    return {k: v for k, v in clusters.items() if v}


# --------------------------------------------------------------------------
# cycle-prep — one consolidated pre-cycle report, replacing dozens of
# one-file/one-issue lookups with a single script run. See
# reports/strategy/PROCESS.md §5 step 0.
# --------------------------------------------------------------------------

def build_cycle_state(records):
    """The state `cycle-prep --diff` compares across runs. Deliberately narrow:
    only what's cheap and deterministic to compute (RFC stage/impl_status,
    REGISTRY.md's own counts, how many retired-host problems exist) — not an
    attempt to encode priorities or triggers, which need judgment and stay the
    reasoner's job, not this snapshot's."""
    by_stage_counts = Counter(r["stage"] for r in records)
    return {
        "generated_on": today(),
        "rfcs": {
            r["id"]: {"stage": r["stage"], "impl_status": r["impl_status"]}
            for r in records
        },
        "stage_counts": dict(by_stage_counts),
        "retired_host_problem_count": len(retired_host_references()),
    }


def diff_cycle_state(old, new):
    """Small, dense delta lines — not a generic dict-diff dump. Only reports
    what changed, matching the same "verify only what's flagged" principle the
    rest of cycle-prep exists to serve."""
    lines = []
    old_rfcs, new_rfcs = old.get("rfcs", {}), new.get("rfcs", {})
    for rid in sorted(set(old_rfcs) | set(new_rfcs), key=rfc_sort_key):
        o, n = old_rfcs.get(rid), new_rfcs.get(rid)
        if o is None:
            lines.append(f"  + {rid}: new ({n['stage']})")
        elif n is None:
            lines.append(f"  - {rid}: removed (was {o['stage']})")
        elif o != n:
            lines.append(
                f"  ~ {rid}: stage {o['stage']!r}→{n['stage']!r}, "
                f"impl_status {o['impl_status']!r}→{n['impl_status']!r}"
            )
    old_counts, new_counts = old.get("stage_counts", {}), new.get("stage_counts", {})
    for stage in sorted(set(old_counts) | set(new_counts)):
        if old_counts.get(stage, 0) != new_counts.get(stage, 0):
            lines.append(f"  stage_counts[{stage}]: {old_counts.get(stage, 0)} → {new_counts.get(stage, 0)}")
    old_rh, new_rh = old.get("retired_host_problem_count", 0), new.get("retired_host_problem_count", 0)
    if old_rh != new_rh:
        lines.append(f"  retired_host_problem_count: {old_rh} → {new_rh}")
    return lines


def cmd_cycle_prep(args):
    records = collect_rfc_records()

    print(f"cycle-prep — {today()}")
    print()

    print("## REGISTRY.md")
    reg_problem = registry_drift_problem()
    print(f"  {reg_problem}" if reg_problem else "  fresh, no drift")
    print()

    print("## Retired-host references (impl_tracking + public/ live links)")
    rh_problems = retired_host_references()
    if rh_problems:
        for p in rh_problems:
            print(f"  - {p}")
    else:
        print("  none found")
    print()

    print("## RFC `updated:` vs. git-log staleness (informational — verify, don't assume wrong)")
    staleness = rfc_git_staleness(records)
    if staleness:
        print(
            f"  {len(staleness)} mismatch(es) — known noisy on this corpus (mass-sweep commits "
            f"touch files without a real design change; see Pending Recommendation 2). Showing 5:"
        )
        for rid, updated, last_touch in staleness[:5]:
            print(f"    - {rid}: frontmatter says {updated!r}, git log's last touch is {last_touch!r}")
        if len(staleness) > 5:
            print(f"    ... and {len(staleness) - 5} more (not a reliable signal yet — see the caveat above)")
    else:
        print("  none found")
    print()

    print("## Open milestones (metel-lang/metel-core)")
    milestones, err = fetch_open_milestones()
    if err:
        print(f"  skipped: {err}")
    elif not milestones:
        print("  none open")
    else:
        for m in milestones:
            print(f"  - {m['title']}: {m['open_issues']} open, {m['closed_issues']} closed — {m['html_url']}")
    print()

    new_state = build_cycle_state(records)
    if args.diff:
        print("## Diff against previous snapshot")
        if SNAPSHOT_PATH.exists():
            try:
                old_state = json.loads(SNAPSHOT_PATH.read_text())
            except (json.JSONDecodeError, OSError) as e:
                print(f"  could not read previous snapshot ({e}) — treating this run as the new baseline")
                old_state = None
            if old_state is not None:
                delta = diff_cycle_state(old_state, new_state)
                if delta:
                    for line in delta:
                        print(line)
                else:
                    print("  no change since last snapshot")
        else:
            print("  no previous snapshot — this run is the new baseline")
        print()

    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(new_state, indent=2, sort_keys=True) + "\n")
    print(f"snapshot written: {SNAPSHOT_PATH.relative_to(REPO_ROOT)}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new draft RFC with an overlap check")
    p_new.add_argument("title")
    p_new.add_argument("-d", "--description", default="", help="Short description for the overlap check and Summary")
    p_new.add_argument("-y", "--yes", action="store_true", help="Skip the overlap confirmation prompt")
    p_new.set_defaults(func=cmd_new)

    p_trans = sub.add_parser("transition", help="Move an RFC to a new lifecycle stage")
    p_trans.add_argument("rfc_id")
    p_trans.add_argument("--to", required=True, choices=list(STAGES))
    p_trans.add_argument("-r", "--reason", default="", help="One-line reason, used in the inserted status note")
    p_trans.add_argument("--tracking", default="", help="Tracking task/URL — required when --to integrated")
    p_trans.set_defaults(func=cmd_transition)

    p_impl = sub.add_parser("impl-status", help="Update impl_status on an integrated/implemented RFC")
    p_impl.add_argument("rfc_id")
    p_impl.add_argument("--set", required=True, choices=sorted(["not-started", "in-progress", "implemented"]))
    p_impl.add_argument("--tracking", default="", help="Optionally update impl_tracking too")
    p_impl.set_defaults(func=cmd_impl_status)

    p_sup = sub.add_parser("supersede", help="Move an RFC to superseded and set superseded_by")
    p_sup.add_argument("rfc_id")
    p_sup.add_argument("--by", required=True, help="Comma-separated RFC ids that supersede it")
    p_sup.add_argument("-r", "--reason", default="", help="One-line reason")
    p_sup.set_defaults(func=cmd_supersede)

    p_check = sub.add_parser("check", help="Validate frontmatter/directory consistency and path references")
    p_check.set_defaults(func=cmd_check)

    p_index = sub.add_parser("index", help="Registry/index maintenance helpers")
    p_index.add_argument("--check-drift", action="store_true")
    p_index.add_argument("--rebuild-registry", action="store_true")
    p_index.add_argument("--suggest-placement", metavar="RFC_ID")
    p_index.add_argument("--write-coverage-baseline", action="store_true")
    p_index.add_argument("--write-spec-origins", action="store_true")
    p_index.set_defaults(func=cmd_index)

    p_cycle = sub.add_parser("cycle-prep", help="One-shot pre-cycle report for a strategic-overview cycle")
    p_cycle.add_argument("--diff", action="store_true", help="Also diff against reports/strategy/.cycle-snapshot.json")
    p_cycle.set_defaults(func=cmd_cycle_prep)

    args = parser.parse_args()
    result = args.func(args)
    # `check` is the only command a CI job runs expecting a real pass/fail
    # signal -- every other command (`new`, `transition`, ...) already fails
    # loudly via `error()` when something's actually wrong, and `transition`
    # calls `cmd_check(args)` internally, at the end, purely to print the
    # post-transition state -- that inner call must never turn a successful
    # transition into a failing process exit over some unrelated pre-existing
    # problem elsewhere in the corpus. Scoped to the top-level `check`
    # invocation specifically, not to `cmd_check`'s return value in general.
    #
    # Found the hard way: `cmd_check` has always returned its `problems` list
    # but nothing ever inspected it -- every CI job that has run `rfc.py
    # check` since it was added (metel-core's `rfc-check` job included) has
    # been printing failures and still reporting success, silently, for as
    # long as the job has existed. Added 2026-08-19 alongside ADR-0049's
    # coverage ratchet, which is what surfaced it -- the ratchet is pointless
    # if the process it fails inside still exits 0 regardless.
    if args.command == "check" and result:
        sys.exit(1)


if __name__ == "__main__":
    main()
