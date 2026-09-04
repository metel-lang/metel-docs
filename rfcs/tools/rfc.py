#!/usr/bin/env python3
"""RFC lifecycle tool for metel-docs. See rfcs/PROCESS.md.

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
                                       RFC still exists under reference/spec/.
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
                                       a live link under ). Also rejects a draft that
                                       carries tracking metadata and, best-effort via
                                       GitHub, any draft named by an open, milestoned
                                       `RFC-NNNN...` tracking issue. Read-only.
  index --check-drift                  Check whether generated REGISTRY.md matches
                                       the current RFC corpus exactly, and whether
                                       the curated INDEX.md mentions every current
                                       RFC at least once. Read-only.
  index --rebuild-registry             Regenerate rfcs/REGISTRY.md from
                                       the current RFC corpus.
  index --suggest-placement <rfc-id>   Suggest which INDEX.md cluster section an
                                       RFC's content is most similar to. Read-only.
  index --write-coverage-baseline      Regenerate rfcs/COVERAGE-BASELINE.json
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
                                       reference/spec/*.md from the
                                       RFCs currently linking to it via
                                       `coverage.spec` frontmatter. Reads only
                                       RFC frontmatter and the spec files --
                                       no fixture corpus needed, unlike
                                       --write-coverage-baseline.

`cycle-prep` moved out of this tool (ADR-0051, step 2) — its inputs were all
public but its output (a private planning snapshot) belonged with
reports/strategy/, not with the corpus this script itself is moving to
metel-docs. See reports/strategy/tools/rfc_cycle_prep.py.

No dependencies beyond the Python 3 standard library.
"""

import argparse
import base64
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

REPO_ROOT = Path(__file__).resolve().parents[2]
RFCS_DIR = REPO_ROOT / "rfcs"
INDEX_PATH = RFCS_DIR / "INDEX.md"
REGISTRY_PATH = RFCS_DIR / "REGISTRY.md"
COVERAGE_BASELINE_PATH = RFCS_DIR / "COVERAGE-BASELINE.json"

# The project's canonical issue tracker, and hosts it has fully retired. A
# reference to a retired host is either a dead link (published, live content) or
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
    print("Reminder: rfcs/INDEX.md needs a new entry for this RFC.")


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
    print("Reminder: rfcs/INDEX.md may need updating for this RFC's new status.")
    return new_path


def fix_referrers(old_rel, new_rel):
    old_str = str(old_rel)
    new_str = str(new_rel)
    changed = []
    for f in REPO_ROOT.rglob("*.md"):
        # Same historical-record exemption as status_citation_problems, and for the
        # same reason (found 2026-08-23 rewriting reports/strategy/cycles/2026-08-01/
        # cycle.md's own citation of RFC-0127's path *at that date* to match today's
        # location): a dated snapshot's citation of a path is correct for when it was
        # written, and rewriting it to match the present corrupts the record rather
        # than fixing it.
        if (
            ".git" in f.parts
            or "archive" in f.parts
            or "5-superseded" in f.parts
            or "6-refused" in f.parts
            or "cycles" in f.parts
        ):
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
    if args.to == "under-review":
        if not args.tracking:
            error(
                "transitioning to 'under-review' requires --tracking <tracking task/URL> — "
                "an RFC entering under-review needs a linked tracking issue in the same "
                "change (see PROCESS.md's 2026-08-23 addition). --tracking sets the "
                "'tracking' field, distinct from 'impl_tracking' (set later, at "
                "'integrated' onward) since a design-settlement issue and an "
                "implementation issue are usually not the same issue."
            )
        extra_fm["tracking"] = args.tracking
    elif args.to == "integrated":
        if not args.tracking:
            error(
                "transitioning to 'integrated' requires --tracking <tracking task/URL> — "
                "no RFC enters integrated without a linked implementation-tracking task "
                "(see PROCESS.md's 3-integrated exit criteria)."
            )
        extra_fm["impl_tracking"] = args.tracking
        extra_fm["impl_status"] = "not-started"
        # ADR-0050 §8: fixture-citation migration gate. An RFC entering
        # `integrated` is having its claims restructured into spec
        # Legality Rule/Dynamic Semantics blocks in the same change --
        # every existing direct `rfc =`/prose fixture citation for it must
        # be migrated to a `spec =` id then, not left for a later sweep
        # (that's exactly the backlog metel-core#769 had to clear by hand).
        # Refuses rather than degrading when the corpus is unreachable,
        # same as the --to implemented gate below (ADR-0049 §5/§6) --
        # "unknown" must not be treated as "pass" for a gate that actually
        # blocks a transition.
        tests_dir = metel_core_tests_dir()
        if tests_dir is None:
            error(
                "cannot verify fixture-citation migration: metel-interpreter/tests is "
                "not reachable from here (see ADR-0049 §6). Run this from a metel-core "
                "checkout with docs/ embedded as its submodule, or set "
                "METEL_CORE_ROOT to point at one."
            )
        sidecar, prose = scan_fixture_citations(tests_dir)
        leftover = sorted(
            ({s for s, _ in sidecar.get(rid, [])} | {s for s, _ in prose.get(rid, [])})
            - {None}
        )
        if leftover:
            error(
                f"{rid.upper()} still has direct `rfc =`/prose fixture citations for "
                f"section(s) {', '.join(leftover)} (ADR-0050 §8) — every citation must "
                f"migrate to a `spec =` id before this RFC enters integrated. Restructure "
                f"the relevant spec content into Legality Rule/Dynamic Semantics blocks, "
                f"add `coverage.spec` frontmatter links for each section, and update the "
                f"citing fixtures' sidecar key from `rfc =` to `spec =`."
            )
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
                f"reference/spec/ — delete it (it's a required one-liner, safe "
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
        uncovered = uncovered_sections_for_implemented(
            rid, tests_dir, find_path_for_id(rid)
        )
        if uncovered:
            error(
                f"{rid.upper()} has normative sections with neither a qualifying "
                f"fixture nor a coverage exemption: {', '.join(sorted(uncovered))} "
                f"(ADR-0049/ADR-0050) — cite a fixture (an `options.rfc` sidecar "
                f"key, or an `options.spec` key linked from a `coverage` "
                f"frontmatter entry) or add a typed `coverage` entry for each"
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
PATH_REF_RE = re.compile(r"rfcs/[0-6]-[a-z-]+/rfc-[\w.-]+\.md")


SPEC_DIR = REPO_ROOT / "reference" / "spec"
VALID_IMPL_STATUS = {"not-started", "in-progress", "implemented"}

# metel-core#981: error-codes.md gets the same rigor-block treatment as a
# Legality Rule / Dynamic Semantics block -- a real, spec-cited fixture
# rendered as an inline viewer instead of a hand-typed, unverified terminal
# snippet. It lives outside SPEC_DIR and its headings carry no explicit
# `{#id}` the way a rigor-block heading does -- the code is already the
# heading's own first token, so it's the id, extracted directly rather than
# minted.
ERROR_CODES_PATH = REPO_ROOT / "reference" / "error-codes.md"
ERROR_CODE_HEADING_RE = re.compile(r"^### (?P<code>[A-Z]\d{4}) — .+$")
# A fixture's *display* citation -- deliberately a separate sidecar key from
# `spec = […]`, not a widened COVERAGE_SPEC_ID_RE alternative folded into that
# same list. "Evidence for a language rule" and "evidence for a diagnostic"
# are different axes even when the same fixture happens to serve both, and a
# dedicated key is what lets a future error-code <-> Legality-Rule cross-link
# (metel-core#977) read a fixture's *intentional* documented connection
# instead of inferring one from every incidental [expect].code match.
COVERAGE_ERROR_LIST_RE = re.compile(r"^\s*error\s*=\s*\[(.*?)\]\s*$", re.MULTILINE)
COVERAGE_ERROR_CODE_RE = re.compile(r"[A-Z]\d{4}")
EXPECT_CODE_RE = re.compile(r'^\s*code\s*=\s*"([^"]*)"\s*$', re.MULTILINE)
EXPECT_SECTION_RE = re.compile(r"\[expect\](.*?)(?=\n\[|\Z)", re.S)

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

# metel-core#944: the fixture backlink renders as an inline collapsible viewer
# on the site (`<details class="spec-fixture" data-fixture="<base64 JSON>">`,
# hydrated by src/theme/Details), not a bare link. The `href` and the inlined
# source snapshot are pinned to the *release tag*, not `main`: the spec is a
# versioned document, and `/cut-release` bumps this constant and re-runs
# `--write-spec-origins` so the pinned ref and the snapshot move together, once
# per release. Between releases the committed spec carries the previous tag.
SPEC_FIXTURE_REF = "v0.13.0"
METEL_CORE_GITHUB_BLOB = f"https://github.com/metel-lang/metel-core/blob/{SPEC_FIXTURE_REF}"

# A rigor block's fixture-coverage exemption (ADR-0050 §6, extended to the
# spec-id surface -- same three kinds ADR-0049 §3 already validates for RFC
# sections: untestable/blocked/elsewhere). Unlike origins/fixtures, this is
# hand-authored, not derived from another file -- there is no corpus to scan
# that would tell a tool "this claim can't be tested". A person decides that
# and writes the one-line trigger; `--write-spec-origins` then generates the
# rendered sentence from it, same one-source-of-truth relationship origins
# has to RFC frontmatter, just sourced from a per-block marker instead of a
# cross-file scan. The trigger line itself is never rewritten or removed by
# regeneration -- only the :rendered: slot it produces is.
#
# Deliberately does NOT let a rigor block describe present-day buggy
# behavior as if it were the rule: a block always states the accepted
# design, and a gap between that design and what's actually implemented
# gets a `blocked` (or, if genuinely unfixable, `untestable`) exemption
# instead -- the same discipline that keeps a fixture from ever being
# fabricated just to satisfy the coverage mandate (ADR-0050 §6's own
# reasoning), applied to prose instead of tests.
SPEC_EXEMPTION_TRIGGER_RE = re.compile(
    r'^<!--\s*rfc\.py:exemption\s+(?P<attrs>.+?)\s*-->$'
)
SPEC_EXEMPTION_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
SPEC_EXEMPTION_RENDERED_START = "<!-- rfc.py:exemption:rendered:start -->"
SPEC_EXEMPTION_RENDERED_END = "<!-- rfc.py:exemption:rendered:end -->"
# Valid kinds are COVERAGE_VALID_KINDS (defined further below, alongside
# ADR-0049 §3's RFC-level exemption) -- same vocabulary, not a second scheme.
# Referenced by name at point of use rather than aliased here, since this
# constant is defined before COVERAGE_VALID_KINDS in the file.

# A `blocked` exemption's `ref` when it names a GitHub issue rather than an
# RFC id -- e.g. "metel-core#775". Deliberately narrower than a bare `\d+`:
# requires the `owner-less repo#number` shape this corpus's own exemptions
# already use, so a `ref` that's just a stray word or a URL doesn't get
# mistaken for one and sent to fetch_issue_state for nothing.
SPEC_EXEMPTION_ISSUE_REF_RE = re.compile(r'^(?P<repo>[a-zA-Z0-9_.-]+)#(?P<num>\d+)$')

# An issue beginning with an RFC id is an explicit tracker for that RFC. Merely
# mentioning an RFC later in a title/body is deliberately insufficient: dependency,
# regression, and documentation issues routinely cite RFCs without tracking their
# settlement or implementation. Combined with a milestone and an open issue, this is
# the issue-tracker half of PROCESS.md's "scheduled work => under review" trigger.
RFC_TRACKER_TITLE_RE = re.compile(r'^\s*RFC-(?P<num>\d{1,4})(?P<suffix>[a-z]?)\b', re.IGNORECASE)


def all_spec_block_ids():
    """Every Legality Rule / Dynamic Semantics id across the spec corpus,
    sorted. The one place that enumerates the spec side directly rather than
    starting from an RFC or a fixture -- every other coverage check in this
    file is keyed off `rfc_sections`/`per_rfc_coverage` and so can only ever
    ask "is this RFC's claim covered", never "does this spec block have
    anything pointing at it at all". A block an RFC never claims (a real,
    valid state -- not every rule needs one) still has to have a fixture."""
    ids = set()
    for spec_path in sorted(SPEC_DIR.glob("*.md")):
        for line in spec_path.read_text().split("\n"):
            m = SPEC_BLOCK_HEADING_RE.match(line)
            if m:
                ids.add(m.group("id"))
    return sorted(ids)


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


def exemption_block_text(kind, ref, reason):
    """The exact content between a rigor block's exemption :rendered: markers,
    generated from its hand-authored trigger (kind/ref/reason) -- the same
    one-source-of-truth relationship origins_block_text has to RFC
    frontmatter, just sourced from a per-block marker instead of a
    cross-file scan. Renders even a malformed kind/ref (visible on the page
    is more useful than silently dropped -- `check` flags the malformed
    attributes separately)."""
    if kind == "blocked":
        label = f"blocked on {ref}" if ref else "blocked (no `ref` given)"
    elif kind == "elsewhere":
        label = f"tested elsewhere ({ref})" if ref else "tested elsewhere (no `ref` given)"
    elif kind == "untestable":
        label = "untestable"
    else:
        label = kind or "exempt"
    return f'<span class="rigor-backlink">_Exempt from fixture coverage — {label}: {reason}_</span>'


def scan_spec_exemptions():
    """{spec_id: (kind, ref, reason, spec_path, lineno)} -- every rigor
    block's hand-authored `<!-- rfc.py:exemption ... -->` trigger, read
    directly (never the generated :rendered: span, which just mirrors it).
    A block with no trigger has no entry here -- the normal, common case
    (most rules have a real fixture), not a gap needing a placeholder."""
    exemptions = {}
    for spec_path in sorted(SPEC_DIR.glob("*.md")):
        lines = spec_path.read_text().split("\n")
        for idx, line in enumerate(lines):
            m = SPEC_BLOCK_HEADING_RE.match(line)
            if not m:
                continue
            spec_id = m.group("id")
            j = idx + 1
            while j < len(lines):
                nxt = lines[j]
                if SPEC_BLOCK_HEADING_RE.match(nxt) or nxt.strip() == "</details>":
                    break
                tm = SPEC_EXEMPTION_TRIGGER_RE.match(nxt.strip())
                if tm:
                    attrs = dict(SPEC_EXEMPTION_ATTR_RE.findall(tm.group("attrs")))
                    exemptions[spec_id] = (
                        attrs.get("kind", ""),
                        attrs.get("ref", ""),
                        attrs.get("reason", ""),
                        spec_path.relative_to(REPO_ROOT),
                        j + 1,
                    )
                    break
                j += 1
    return exemptions


def spec_exemption_problems():
    """Validates every rigor block's hand-authored exemption trigger --
    kind/ref/reason well-formedness, and (best-effort) whether a `blocked`
    ref has actually resolved: an RFC ref checked locally against RFC stage
    (scan_rfc_metadata, no network), an issue ref (`repo#N`) checked live
    against the GitHub API (fetch_issue_state). Deliberately independent of
    coverage_check_problems()'s fixture-corpus reachability gate -- none of
    this needs metel-interpreter/tests, so cmd_check() runs it
    unconditionally, and it's the one piece of exemption validation that
    actually fires from a bare docs-internal checkout, not only from inside
    metel-core. A network failure or rate limit degrades to skipping that one
    ref's live check silently, never to a problem -- only a *confirmed*
    closed issue is one; a check this could ever fail on infrastructure
    flakiness alone would defeat the whole point of exempting something
    deliberately."""
    problems = []
    exemptions = scan_spec_exemptions()
    if not exemptions:
        return problems
    all_ids = set(all_spec_block_ids())
    _sections, _fm, _inline, _spec_links, rfc_stage = scan_rfc_metadata()
    for sid, (kind, ref, reason, epath, elineno) in exemptions.items():
        if sid not in all_ids:
            continue
        if kind not in COVERAGE_VALID_KINDS:
            problems.append(
                f"{epath}:{elineno}: exemption for `{sid}` has kind={kind!r}, "
                f"not one of {sorted(COVERAGE_VALID_KINDS)}"
            )
            continue
        if kind in ("blocked", "elsewhere") and not ref:
            problems.append(
                f"{epath}:{elineno}: exemption for `{sid}` (kind={kind}) needs a `ref` attribute"
            )
        if not reason:
            problems.append(f"{epath}:{elineno}: exemption for `{sid}` has no `reason`")
        if kind != "blocked" or not ref:
            continue
        if re.match(r"rfc-\d{4}$", ref, re.IGNORECASE):
            ref_id = ref.lower()
            if ref_id not in rfc_stage:
                problems.append(f"{epath}:{elineno}: exemption for `{sid}` is blocked on `{ref}`, which doesn't exist")
            elif rfc_stage[ref_id] == "implemented":
                problems.append(
                    f"{epath}:{elineno}: exemption for `{sid}` is blocked on `{ref}`, which is now "
                    f"4-implemented -- verify the blocker actually closed, and cite a real fixture if so"
                )
            continue
        m = SPEC_EXEMPTION_ISSUE_REF_RE.match(ref)
        if not m:
            continue  # free-form ref (a URL, a bare description) -- nothing to check live
        state, err = fetch_issue_state("metel-lang", m.group("repo"), m.group("num"))
        if err is not None:
            continue  # best-effort -- unreachable/rate-limited network never fails the build
        if state == "closed":
            problems.append(
                f"{epath}:{elineno}: exemption for `{sid}` is blocked on `{ref}`, which is now "
                f"closed -- verify the blocker actually resolved this claim, and cite a real fixture if so"
            )
    return problems


# --- fixture viewer payloads (metel-core#944) ---------------------------------
#
# The rendered "Tested by" slot is one `<details class="spec-fixture"
# data-fixture="<base64>">` per citing fixture; `src/theme/Details` in
# metel-website decodes the base64 JSON and renders an inline collapsible
# viewer. The payload rides in the attribute (not a fenced code block) so it
# survives CommonMark's raw-HTML handling and stays invisible to
# check-examples / check-mdx. The JSON is emitted with sorted keys and compact
# separators so the base64 is byte-stable -- `--check-drift` catches a stale
# inlined snapshot exactly the way it already catches a stale link.

_EXPECT_KEY_RE = re.compile(
    r'^\s*(?P<k>status|code|contains|line|col)\s*=\s*(?P<v>.+?)\s*$', re.MULTILINE
)
_SPEC_TITLE_RE = re.compile(
    r'^\s*spec_title\s*=\s*(?P<v>.+?)\s*$', re.MULTILINE
)


def _toml_scalar(raw):
    """Unquote a sidecar scalar (`"x"` / `'x'` / bare) -- the harness's own
    parse_scalar, kept minimal."""
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def _sidecar_expect(toml_text):
    """`{status, code, contains, line, col}` from the sidecar's `[expect]`
    table (any of them possibly None, except `status`). `line`/`col` pinpoint
    the expected diagnostic's position in the fixture's own source, so the
    viewer can show a reader exactly what the fixture checks, not just that it
    checks something. Scanned only within the `[expect]` section so an
    `[options]`-level key of the same name can't leak in.

    `status` defaults to `"success"` when absent -- not left `None` -- because
    that's the harness's own default (`Expectation::success()` in
    `merge_config`, metel-core's `fixture.rs`): a fixture with no `[expect]`
    table at all, which is most of them (an unannotated positive fixture is
    the common case), still has a real, defined expectation. Leaving `status`
    unset here made `_spec_fixture_marker`'s `any(expect.values())` guard
    false for every such fixture, so the vast majority of fixtures silently
    got no `expect` payload and the viewer showed no footer at all --
    reported as a bug (metel-core#973 follow-up, 2026-09-04) before this was
    traced to its actual cause."""
    out = {"status": None, "code": None, "contains": None, "line": None, "col": None}
    in_expect = False
    for line in toml_text.split("\n"):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_expect = s == "[expect]"
            continue
        if not in_expect:
            continue
        m = _EXPECT_KEY_RE.match(line)
        if m:
            out[m.group("k")] = _toml_scalar(m.group("v"))
    if out["status"] is None:
        out["status"] = "success"
    return out


def _sidecar_spec_title(toml_text):
    """`spec_title` from `[options]` (metel-core#974), or None. Whitespace-only
    is treated as unset, matching the harness."""
    in_options = False
    for line in toml_text.split("\n"):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_options = s == "[options]"
            continue
        if not in_options:
            continue
        m = _SPEC_TITLE_RE.match(line)
        if m:
            v = _toml_scalar(m.group("v")).strip()
            return v or None
    return None


def _fixture_files(toml_path):
    """`[(name, source), ...]` -- the Metel file(s) a reader wants to see. A
    directory fixture (`test.toml`) is every `.mtl` under the fixture dir,
    recursively (nested module folders included), `main.mtl` first and the rest
    by relative path; the `name` for a nested file is its path relative to the
    fixture dir (`parser/facade.mtl`) so the viewer can render it as a tree.
    `test.toml` is deliberately excluded -- its `[expect]` is surfaced
    separately and its `[options]` are test plumbing, not source. Otherwise the
    single sibling `.mtl`."""
    if toml_path.name == "test.toml":
        d = toml_path.parent
        mtls = sorted(
            (p for p in d.rglob("*.mtl") if p.is_file()),
            key=lambda p: (
                p.relative_to(d).as_posix() != "main.mtl",
                p.relative_to(d).as_posix(),
            ),
        )
        return [(p.relative_to(d).as_posix(), p.read_text()) for p in mtls]
    mtl = toml_path.with_suffix(".mtl")
    return [(mtl.name, mtl.read_text())] if mtl.is_file() else []


def _spec_fixture_marker(toml_path, core_root):
    """One `<details class="spec-fixture" ...>` line for `toml_path`, or None
    when its `.mtl` isn't there / isn't under `core_root`."""
    files = _fixture_files(toml_path)
    if not files:
        return None
    primary = _sidecar_mtl_path(toml_path)  # main.mtl for a dir, else the .mtl
    try:
        rel = primary.resolve().relative_to(core_root.resolve())
    except ValueError:
        return None
    is_dir_fixture = toml_path.name == "test.toml"
    href_target = rel.parent.as_posix() if is_dir_fixture else rel.as_posix()
    toml_text = toml_path.read_text()
    payload = {
        "name": toml_path.parent.name if is_dir_fixture else primary.name,
        "href": f"{METEL_CORE_GITHUB_BLOB}/{href_target}",
        "files": [{"name": n, "source": s} for n, s in files],
    }
    title = _sidecar_spec_title(toml_text)
    if title:
        payload["title"] = title
    # _sidecar_expect always resolves a status (defaulting to "success" per
    # the harness), so a fixture's expectation is never actually absent --
    # every marker carries `expect`.
    payload["expect"] = _sidecar_expect(toml_text)
    raw = base64.b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return f'<details class="spec-fixture" data-fixture="{raw}"></details>'


def fixtures_block_text(toml_paths, core_root):
    """The exact content between the fixtures markers for one rigor block, or
    "" if no fixture cites it yet -- as valid a state as an RFC with no
    fixture yet (ADR-0050's own Context section names this as real),
    rendered as no slot at all rather than a fabricated "untested"
    placeholder. One `<details class="spec-fixture">` per citing fixture (the
    site renders each as an inline viewer over the fixture's own .mtl -- the
    actual Metel source a reader wants -- not its .toml sidecar).

    metel-core#979: a rule citing several fixtures showed that many collapsed
    toggle-bar *rows* by default, with nothing to collapse them as a group --
    one rule cited 26. A flat "always collapsed" wrapper would have forced an
    extra click on the far more common 2-3-fixture case for no real benefit
    (measured against the actual corpus: 247 rules cite exactly 1, 80 cite 2
    or 3, only 24 cite 4+), so the wrapper's presence *and* its default
    open/closed state are graded by the citing count instead of a single
    fixed rule:
      - 1 fixture:  unwrapped, exactly as before -- the plain <p> label.
      - 2-3:        wrapped, `open` by default -- same rows visible as
                    before, but now a closeable "Tested by (N)" toggle.
      - 4+:         wrapped, collapsed by default -- the actual fix.
    The wrapper carries no special class, so it dispatches through the
    website's existing generic Details disclosure (src/theme/Details), not
    SpecFixtureView -- nested <details> already works today (a fixture
    viewer already lives inside the outer "Formal rules" one)."""
    if not toml_paths:
        return ""
    markers = []
    for p in sorted(set(toml_paths), key=lambda x: (x.name, str(x))):
        marker = _spec_fixture_marker(p, core_root)
        if marker:
            markers.append(marker)
    n = len(markers)
    if n == 0:
        return ""
    if n == 1:
        return "\n".join(['<p class="rigor-backlink"><em>Tested by</em></p>', *markers])
    open_attr = " open" if n < 4 else ""
    return "\n".join(
        [
            f'<details class="rigor-fixtures-toggle"{open_attr}>',
            f"<summary>Tested by ({n})</summary>",
            *markers,
            "</details>",
        ]
    )


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
        exemption_trigger = None  # (kind, ref, reason), from the hand-authored line, if present
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
            if nxt.strip() == SPEC_EXEMPTION_RENDERED_START:
                # Generated purely from the trigger line -- always dropped and
                # rebuilt fresh below, same as origins/fixtures, never carried
                # over verbatim the way an unreachable fixtures slot is.
                i += 1
                while i < n and lines[i].strip() != SPEC_EXEMPTION_RENDERED_END:
                    i += 1
                i += 1  # consume the end marker itself
                continue
            tm = SPEC_EXEMPTION_TRIGGER_RE.match(nxt.strip())
            if tm:
                attrs = dict(SPEC_EXEMPTION_ATTR_RE.findall(tm.group("attrs")))
                exemption_trigger = (attrs.get("kind", ""), attrs.get("ref", ""), attrs.get("reason", ""))
            body.append(nxt)  # the trigger line itself is hand-authored -- kept, never rewritten
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

        if exemption_trigger is not None:
            out.append("")
            out.append(SPEC_EXEMPTION_RENDERED_START)
            out.append(exemption_block_text(*exemption_trigger))
            out.append(SPEC_EXEMPTION_RENDERED_END)

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


def regenerate_error_code_fixtures_in_text(text, fixtures_by_code, core_root):
    """error-codes.md's equivalent of regenerate_backlinks_in_text -- same
    idempotent remove-and-reappend shape, simplified: no origins slot (an
    error code has no RFC-origins backlink the way a rigor block does), just
    the fixtures marker and the exemption trigger/render pair. A code's
    section ends at the next `### CODE` heading or a `## ` section header
    (error-codes.md has no `<details>` wrapper to also break on).

    The fixtures marker (metel-core#981) always regenerates as the *last*
    thing in a code's section, after any hand-authored prose (including a
    trailing "**Fix:**" line) -- matching where a rigor block's own fixtures
    slot sits relative to its body, not narrative ordering.

    fixtures_by_code is None when metel-interpreter/tests isn't reachable: an
    existing fixtures slot is carried over exactly as it already reads, the
    same ADR-0049 §6 degrade path regenerate_backlinks_in_text uses."""
    lines = text.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        m = ERROR_CODE_HEADING_RE.match(line)
        if not m:
            i += 1
            continue
        code = m.group("code")
        i += 1
        body = []
        existing_fixtures_content = None
        exemption_trigger = None
        while i < n:
            nxt = lines[i]
            if ERROR_CODE_HEADING_RE.match(nxt) or nxt.strip().startswith("## "):
                break
            if nxt.strip() == FIXTURES_MARKER_START:
                i += 1
                slot = []
                while i < n and lines[i].strip() != FIXTURES_MARKER_END:
                    slot.append(lines[i])
                    i += 1
                i += 1  # consume the end marker itself
                existing_fixtures_content = "\n".join(slot).strip()
                continue
            if nxt.strip() == SPEC_EXEMPTION_RENDERED_START:
                i += 1
                while i < n and lines[i].strip() != SPEC_EXEMPTION_RENDERED_END:
                    i += 1
                i += 1  # consume the end marker itself
                continue
            tm = SPEC_EXEMPTION_TRIGGER_RE.match(nxt.strip())
            if tm:
                attrs = dict(SPEC_EXEMPTION_ATTR_RE.findall(tm.group("attrs")))
                exemption_trigger = (attrs.get("kind", ""), attrs.get("ref", ""), attrs.get("reason", ""))
            body.append(nxt)  # hand-authored -- kept, never rewritten
            i += 1
        while body and body[-1].strip() == "":
            body.pop()
        out.extend(body)

        if exemption_trigger is not None:
            out.append("")
            out.append(SPEC_EXEMPTION_RENDERED_START)
            out.append(exemption_block_text(*exemption_trigger))
            out.append(SPEC_EXEMPTION_RENDERED_END)

        if fixtures_by_code is None:
            fixtures_content = existing_fixtures_content
        else:
            fixtures_content = fixtures_block_text(fixtures_by_code.get(code, []), core_root)
        if fixtures_content:
            out.append("")
            out.append(FIXTURES_MARKER_START)
            out.append(fixtures_content)
            out.append(FIXTURES_MARKER_END)

        out.append("")
    return "\n".join(out)


def write_error_code_fixtures():
    """rfc.py index --write-spec-origins's error-codes.md half (metel-core#981).
    Regenerates every code's fixtures backlink when metel-interpreter/tests is
    reachable; a no-op (file unchanged) otherwise. Returns True if the file
    changed."""
    if not ERROR_CODES_PATH.exists():
        return False
    tests_dir = metel_core_tests_dir()
    fixtures_by_code = scan_error_code_citations(tests_dir) if tests_dir is not None else None
    core_root = tests_dir.parent.parent if tests_dir is not None else None
    text = ERROR_CODES_PATH.read_text()
    new_text = regenerate_error_code_fixtures_in_text(text, fixtures_by_code, core_root)
    if new_text != text:
        ERROR_CODES_PATH.write_text(new_text)
        return True
    return False


def error_code_fixtures_drift_problems():
    """--check-drift's error-codes.md half: whether its fixtures slots still
    match what write_error_code_fixtures() would produce."""
    if not ERROR_CODES_PATH.exists():
        return []
    tests_dir = metel_core_tests_dir()
    fixtures_by_code = scan_error_code_citations(tests_dir) if tests_dir is not None else None
    core_root = tests_dir.parent.parent if tests_dir is not None else None
    text = ERROR_CODES_PATH.read_text()
    if regenerate_error_code_fixtures_in_text(text, fixtures_by_code, core_root) != text:
        return [
            f"{ERROR_CODES_PATH.relative_to(REPO_ROOT)}: fixtures backlinks are stale -- "
            f"run `rfc.py index --write-spec-origins`"
        ]
    return []


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
        "This file is generated by `rfcs/tools/rfc.py index --rebuild-registry`.",
        "Do not edit it by hand. It is the authoritative RFC state inventory; `INDEX.md` is",
        "the curated thematic map.",
        "",
        "**Every `implemented`/`integrated` RFC listed below is checked by CI, on every "
        "push, for regressed fixture coverage** — `rfc.py check` (metel-core's `rfc-check` "
        "job; degrades to an informational skip when run from a bare docs-internal "
        "checkout) fails if any RFC's uncovered normative sections grow "
        "past what `rfcs/COVERAGE-BASELINE.json` already grandfathers in. This is "
        "the retroactive half of the coverage mandate; the forward-looking half "
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
        return "rfcs/REGISTRY.md is missing — run `rfc.py index --rebuild-registry`"
    actual = REGISTRY_PATH.read_text()
    if _without_generated_on_stamp(actual) != _without_generated_on_stamp(expected):
        return "rfcs/REGISTRY.md is stale or hand-edited — run `rfc.py index --rebuild-registry`"
    return None


def retired_host_references():
    """Flag references to a retired host (RETIRED_HOSTS) in two places: any RFC's
    impl_tracking field (structured, checked directly against parsed frontmatter —
    this field must always resolve, so any non-canonical host is unambiguously
    wrong), and any live URL anywhere in this repo's body text — this whole repo
    is the exported/published surface a reader could actually click (ADR-0051:
    metel-docs holds nothing else, unlike metel-docs-internal's old `public/`
    subtree, which needed `reports/`/`internal/` excluded for exactly this
    reason — that exclusion no longer applies or exists here). Zero network
    calls; pure text matching, so this runs on every `check`. (A duplicate of
    this function also runs from metel-docs-internal's
    reports/strategy/tools/rfc_cycle_prep.py — ADR-0051 step 2 — kept in sync by
    hand; see that file's module docstring. That copy still excludes
    `reports/`/`internal/`, since it also reads metel-docs-internal directly
    when pointed at a pre-migration checkout.)"""
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
    for f in sorted(REPO_ROOT.rglob("*.md")):
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


# rfc_git_staleness() and fetch_open_milestones() moved to
# reports/strategy/tools/rfc_cycle_prep.py (ADR-0051 step 2) — cycle-prep was
# their only caller in this file.


def fetch_issue_state(owner, repo, number):
    """Best-effort GitHub REST call for one issue's state -- (state, None) on
    success, (None, reason) on any failure, network or auth -- never raises.
    Unlike a milestone-listing call, no token is required: a single-issue GET
    on a public repo is anonymous-readable, so a `blocked` exemption's issue
    ref (spec_exemption_problems, below) gets checked in CI with zero secret
    configuration on either side (metel-docs-internal's bare job included --
    this needs no fixture corpus, so it isn't gated behind METEL_CORE_ROOT the
    way fixture-coverage counting is). GITHUB_TOKEN/GH_TOKEN, when present, is
    used only to raise the request above the much lower unauthenticated rate
    limit, not a hard requirement here since the target data is public either
    way."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rfc.py-check"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        return None, f"GitHub API request failed ({e})"
    state = data.get("state")
    if state is None:
        return None, "response had no `state` field"
    return state, None


def fetch_open_milestoned_rfc_trackers(owner="metel-lang", repo="metel-core"):
    """Return explicit RFC trackers among the repository's scheduled open issues.

    This is the reverse check frontmatter alone cannot provide: an issue can be
    created and milestoned before anybody edits the RFC. Titles must *begin* with an
    RFC id, which avoids treating an issue that merely cites a dependency or reports
    a conformance bug as that RFC's lifecycle tracker.

    The GitHub issues endpoint includes pull requests, so those are excluded. Results
    are paginated rather than silently checking only the newest 100 scheduled issues.
    Like fetch_issue_state(), network/API failure is reported to the caller instead
    of raising; structural checks remain usable offline.
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "rfc.py-check"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    trackers = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/issues"
            f"?state=open&milestone=*&per_page=100&page={page}"
        )
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                issues = json.loads(resp.read())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
            return None, f"GitHub API request failed ({e})"
        if not isinstance(issues, list):
            return None, "GitHub API response was not an issue list"

        for issue in issues:
            if issue.get("pull_request") or not issue.get("milestone"):
                continue
            match = RFC_TRACKER_TITLE_RE.match(issue.get("title", ""))
            if not match:
                continue
            trackers.append({
                "rfc_id": normalize_id(match.group("num") + match.group("suffix")),
                "number": issue.get("number"),
                "title": issue.get("title", ""),
                "milestone": issue["milestone"].get("title", ""),
                "url": issue.get("html_url", ""),
            })

        if len(issues) < 100:
            break
        page += 1
    return trackers, None


def scheduled_draft_problems(id_to_stage, trackers):
    """Flag scheduled RFC trackers whose RFC has not entered review."""
    problems = []
    for tracker in trackers:
        rid = tracker["rfc_id"]
        if id_to_stage.get(rid) != "draft":
            continue
        problems.append(
            f"{rid.upper()} is still in 0-draft but open issue #{tracker['number']} "
            f"is committed to milestone '{tracker['milestone']}' ({tracker['url']}) — "
            f"PROCESS.md requires the RFC to transition to 1-under-review and link "
            f"the tracker in the same change"
        )
    return problems


def index_mentioned_rfc_ids(text):
    ids = set()
    for m in re.finditer(r"RFC-(\d+[a-z]?)", text, flags=re.IGNORECASE):
        ids.add(normalize_id(m.group(1)))
    return ids


def spec_mentions(rid):
    """Does anything under reference/spec/ reference this RFC id? Case-insensitive
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
    """Lines under reference/spec/ that read as a "Not yet implemented" callout
    *for this specific RFC* — the phrase appears on the line, and the line's own
    `rfcs/.../rfc-....md` path reference (not just any RFC number mentioned in
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
        # stale, and must not be "fixed" to match the present. RFCs sitting in
        # 5-superseded/ or 6-refused/ themselves are the same case one level up:
        # found 2026-08-23 when moving RFC-0092 to under-review broke two citations
        # inside superseded RFC-0083, written when RFC-0092 really was draft and
        # never meant to track its subject's later movement. reports/strategy/cycles/
        # dated snapshots are the same case again — proactively exempted alongside
        # fix_referrers' identical exemption, added the same day for the same reason.
        if (
            ".git" in f.parts
            or "archive" in f.parts
            or "5-superseded" in f.parts
            or "6-refused" in f.parts
            or "cycles" in f.parts
            or f == REGISTRY_PATH
        ):
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


def scan_error_code_citations(tests_dir):
    """{code: [toml_path, ...]} -- metel-core#981's *display* set: which
    fixture(s) a sidecar's `error = […]` key explicitly, intentionally cites
    as documentation for that code. Mirrors scan_spec_citations exactly, one
    key over."""
    out = {}
    for toml_path in tests_dir.rglob("*.toml"):
        try:
            text = toml_path.read_text()
        except OSError:
            continue
        m = COVERAGE_ERROR_LIST_RE.search(text)
        if not m:
            continue
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            item = item.strip()
            if COVERAGE_ERROR_CODE_RE.fullmatch(item):
                out.setdefault(item, []).append(toml_path)
    return out


def scan_error_code_expectations(tests_dir):
    """{code: [toml_path, ...]} -- metel-core#981's *coverage* set: every
    fixture whose own `[expect].code` names a code, scanned directly with no
    citation required. Free, zero-authoring-cost proof that a code fires
    somewhere in the corpus -- a superset of scan_error_code_citations'
    curated/display set; a code can be in this set without a citing entry
    yet (proven, but nothing chosen to show a reader), which is the visible
    gap `check` reports."""
    out = {}
    for toml_path in tests_dir.rglob("*.toml"):
        try:
            text = toml_path.read_text()
        except OSError:
            continue
        em = EXPECT_SECTION_RE.search(text)
        if not em:
            continue
        cm = EXPECT_CODE_RE.search(em.group(1))
        if cm and cm.group(1):
            out.setdefault(cm.group(1), []).append(toml_path)
    return out


def all_error_codes():
    """Every code documented in error-codes.md, in file order -- the error-
    codes equivalent of all_spec_block_ids()."""
    if not ERROR_CODES_PATH.exists():
        return []
    codes = []
    for line in ERROR_CODES_PATH.read_text().split("\n"):
        m = ERROR_CODE_HEADING_RE.match(line)
        if m:
            codes.append(m.group("code"))
    return codes


def scan_error_code_exemptions():
    """{code: (kind, ref, reason, path, lineno)} -- error-codes.md's own
    hand-authored exemption triggers, same shape and same
    <!-- rfc.py:exemption ... --> syntax as scan_spec_exemptions(), one file
    instead of a directory of them."""
    exemptions = {}
    if not ERROR_CODES_PATH.exists():
        return exemptions
    lines = ERROR_CODES_PATH.read_text().split("\n")
    for idx, line in enumerate(lines):
        m = ERROR_CODE_HEADING_RE.match(line)
        if not m:
            continue
        code = m.group("code")
        j = idx + 1
        while j < len(lines):
            nxt = lines[j]
            if ERROR_CODE_HEADING_RE.match(nxt) or nxt.strip().startswith("## "):
                break
            tm = SPEC_EXEMPTION_TRIGGER_RE.match(nxt.strip())
            if tm:
                attrs = dict(SPEC_EXEMPTION_ATTR_RE.findall(tm.group("attrs")))
                exemptions[code] = (
                    attrs.get("kind", ""),
                    attrs.get("ref", ""),
                    attrs.get("reason", ""),
                    ERROR_CODES_PATH.relative_to(REPO_ROOT),
                    j + 1,
                )
                break
            j += 1
    return exemptions


def _sidecar_mtl_path(toml_path):
    return (
        toml_path.parent / "main.mtl"
        if toml_path.name == "test.toml"
        else toml_path.with_suffix(".mtl")
    )


def uncovered_sections_for_implemented(rid, tests_dir, rfc_path):
    """The `--to implemented` fixture-coverage gate (ADR-0049 §5/§6): normative
    sections of `rid` covered by *nothing*. A section counts as covered by any
    of -- matching what `check`'s per_rfc_coverage() accepts:

    - an `options.rfc` sidecar or prose `RFC-NNNN§N` citation (ADR-0049 §1);
    - an `options.spec` fixture behind a `coverage: { "N": { spec: ... } }`
      frontmatter link whose spec id actually has a citing fixture (ADR-0050 §5);
    - a typed `coverage` exemption entry.

    Kept as a pure function (no `error()`, no I/O beyond the paths it's handed)
    so it's unit-testable without a live repo.
    """
    fm_text = frontmatter_raw_text(rfc_path)
    _, body = parse_file(rfc_path)
    sections = set(rfc_normative_sections(body))
    sidecar, prose = scan_fixture_citations(tests_dir)
    cited = {s for s, _ in sidecar.get(rid, [])} | {s for s, _ in prose.get(rid, [])}
    cited.discard(None)
    spec_citations = scan_spec_citations(tests_dir)
    spec_anchored = {
        section
        for section, spec_id in parse_coverage_spec_links(fm_text).items()
        if spec_citations.get(spec_id)
    }
    exempted = set(parse_coverage_frontmatter(fm_text))
    return sections - cited - spec_anchored - exempted


def scan_rfc_metadata():
    """Every RFC's stage, normative sections, and `coverage` frontmatter --
    everything scan_coverage_corpus() needs from the RFC side, but with none
    of its fixture-corpus dependency. Always available, even from a bare
    docs-internal checkout with no metel-interpreter/tests in reach -- so a
    check that only needs the RFC/spec side (spec_exemption_problems, below)
    doesn't have to wait on METEL_CORE_ROOT the way fixture-coverage counting
    genuinely does."""
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
    return rfc_sections, rfc_coverage_fm, rfc_coverage_inline, rfc_coverage_spec, rfc_stage


def scan_coverage_corpus():
    """ADR-0049. The corpus-wide scan `coverage_check_problems()` and the
    `--write-coverage-baseline` writer both need: everything
    scan_rfc_metadata() provides, plus the fixture corpus's sidecar/prose
    citations. Factored out so the two only disagree about what they *do*
    with this, never about how it's gathered. None (not an error) when
    metel-interpreter/tests isn't reachable -- see ADR-0049 §6; callers
    degrade independently from there."""
    tests_dir = metel_core_tests_dir()
    if tests_dir is None:
        return None

    rfc_sections, rfc_coverage_fm, rfc_coverage_inline, rfc_coverage_spec, rfc_stage = (
        scan_rfc_metadata()
    )
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


def build_coverage_baseline_json(coverage_by_rfc, spec_ids_without_fixture=()):
    """`{"rfc": {rid: [uncovered section ids]}, "spec": [spec ids with no
    citing fixture]}`. Two independent gaps, two independent directions
    (ADR-0050 §5): "rfc" is an RFC's own claim going uncovered; "spec" is a
    spec block -- whether or not any RFC claims it at all -- going untested.
    Fully-covered RFCs and "*" whole-RFC exemptions are simply absent from
    "rfc" (always zero-gap by construction), keeping the file's diff focused
    on what's actually being grandfathered in rather than restating every
    RFC that already needs nothing."""
    rfc_gaps = {
        rid: sorted(uncovered)
        for rid, (_sections, uncovered, _kind, _spec_anchored, _rfc_only) in coverage_by_rfc.items()
        if uncovered
    }
    baseline = {"rfc": rfc_gaps, "spec": sorted(spec_ids_without_fixture)}
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
    # Back-compat with the pre-spec-check baseline shape (a bare {rid: [...]}
    # dict, no "rfc"/"spec" nesting): fall back to treating the whole loaded
    # value as the rfc-gaps mapping, same as before this existed.
    rfc_baseline = (
        baseline.get("rfc", baseline) if isinstance(baseline, dict) else None
    )
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
        if rfc_only:
            # ADR-0050 §8's other half of the migration gate: --to integrated
            # (cmd_transition) only stops a *new* un-migrated citation from
            # entering at the moment of transition; this is what catches one
            # added or reintroduced afterward -- a fixture reverted to
            # `rfc =`, or a new fixture citing an already-integrated RFC the
            # old way instead of picking up its spec = id. Every RFC in this
            # loop is already integrated or implemented (per_rfc_coverage's
            # own filter above), so rfc_only here is never "not yet
            # migrated, in progress" -- it's always a regression.
            problems.append(
                f"{rid}: {len(rfc_only)} section(s) still cited via direct "
                f"`rfc =`/prose instead of `spec =` ({', '.join(sorted(rfc_only))}) -- "
                f"ADR-0050 §8 requires migration complete once an RFC reaches "
                f"integrated. Add the missing `coverage.spec` frontmatter link(s) and "
                f"update the citing fixture(s)' sidecar key from `rfc =` to `spec =`."
            )
        info.append(
            f"  {rid}: {covered_n}/{len(sections)} normative sections covered"
            + (f" -- uncovered: {', '.join(sorted(uncovered))}" if uncovered else "")
            + migration_note
        )
        if rfc_baseline is not None:
            new_gaps = uncovered - set(rfc_baseline.get(rid, []))
            if new_gaps:
                problems.append(
                    f"{rid}: coverage regressed against rfcs/COVERAGE-BASELINE.json "
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
                f"spec-anchoring migration: {total_spec_anchored}/{migratable} "
                f"citable normative sections spec-anchored ({pct:.0f}%); "
                f"{total_rfc_only} still on a direct `rfc =`/prose citation"
            )

    # 6. Every spec block needs a fixture, independent of whether any RFC
    #    claims it (a real, valid state -- not every rule needs one, but
    #    every one needs a test). per_rfc_coverage above can't see this: it's
    #    keyed off rfc_sections, so a spec block no RFC cites never enters
    #    that loop at all. Same baseline-ratchet shape as the RFC-side check
    #    (5b) -- a gap already grandfathered in doesn't fail every run, a new
    #    one does.
    #
    #    6a. A block can carry a typed exemption instead (ADR-0050 §6,
    #    reattached to a spec id -- same untestable/blocked/elsewhere
    #    vocabulary ADR-0049 §3 already validates for RFC sections). An
    #    exempted block is removed from `untested` the same way a real
    #    fixture would remove it, but reported in its own visible line
    #    rather than folded silently into "covered" -- the same reason
    #    `untestable` stays a visible list on the RFC side. Exemption
    #    *validity* (kind/ref/reason well-formedness, whether a blocker has
    #    resolved) is checked by spec_exemption_problems() instead of here --
    #    that check needs none of this function's fixture-corpus dependency,
    #    so it runs unconditionally from cmd_check(), not only when
    #    METEL_CORE_ROOT is reachable.
    all_ids = all_spec_block_ids()
    exemptions = scan_spec_exemptions()
    untested = sorted(
        sid for sid in all_ids if not spec_citations.get(sid) and sid not in exemptions
    )
    if all_ids:
        cited_n = sum(1 for sid in all_ids if spec_citations.get(sid))
        info.append(
            f"spec blocks with a citing fixture: {cited_n}/{len(all_ids)}"
            + (f" -- untested: {', '.join(untested)}" if untested else "")
        )
        exempt_ids = sorted(sid for sid in exemptions if sid in all_ids)
        if exempt_ids:
            kind_counts = Counter(exemptions[sid][0] for sid in exempt_ids)
            breakdown = ", ".join(f"{c} {k}" for k, c in sorted(kind_counts.items()))
            detail = "; ".join(f"{sid} ({exemptions[sid][0]}: {exemptions[sid][2]})" for sid in exempt_ids)
            info.append(
                f"spec blocks exempt from fixture coverage: {len(exempt_ids)} ({breakdown}) -- {detail}"
            )
    # "spec" is only meaningful in the new, nested baseline shape -- a
    # pre-existing flat {rid: [...]} baseline has no such key and no
    # spec-side ratchet was ever recorded, so treat that the same as no
    # baseline file at all (skip the ratchet) rather than reading an absent
    # key as an empty, already-clean baseline.
    spec_baseline = baseline.get("spec") if isinstance(baseline, dict) and "rfc" in baseline else None
    if spec_baseline is not None:
        new_untested = set(untested) - set(spec_baseline)
        if new_untested:
            problems.append(
                "spec blocks newly missing a citing fixture, against "
                "rfcs/COVERAGE-BASELINE.json: "
                + ", ".join(sorted(new_untested))
                + ". Cite one (`spec = [...]` sidecar key); if the gap is deliberate and "
                "already tracked elsewhere, update the baseline instead: "
                "`rfc.py index --write-coverage-baseline`"
            )

    # metel-core#981: error-codes.md gets the same coverage visibility a
    # rigor block gets, split into two counts -- curated (a fixture someone
    # chose via `error = […]`, and so is actually shown on the page) and
    # auto-discovered (some fixture's own [expect].code proves the trigger
    # is real, whether or not anyone's picked it to display yet). The gap
    # between them is itself informative: a code proven but not yet curated
    # is a smaller, different task than a code nobody has proven at all.
    all_codes = all_error_codes()
    if all_codes:
        tests_dir = metel_core_tests_dir()
        if tests_dir is not None:
            error_citations = scan_error_code_citations(tests_dir)
            error_expectations = scan_error_code_expectations(tests_dir)
            error_exemptions = scan_error_code_exemptions()
            cited_n = sum(1 for c in all_codes if error_citations.get(c))
            proven_n = sum(1 for c in all_codes if error_expectations.get(c))
            uncited = sorted(
                c for c in all_codes
                if not error_citations.get(c) and c not in error_exemptions
            )
            unproven = sorted(
                c for c in all_codes
                if not error_expectations.get(c) and c not in error_exemptions
            )
            info.append(
                f"error codes with a citing fixture: {cited_n}/{len(all_codes)}"
                + (f" -- uncited: {', '.join(uncited)}" if uncited else "")
            )
            info.append(
                f"error codes proven by some fixture (auto-discovered via [expect].code): "
                f"{proven_n}/{len(all_codes)}"
                + (f" -- unproven: {', '.join(unproven)}" if unproven else "")
            )
            exempt_codes = sorted(c for c in error_exemptions if c in all_codes)
            if exempt_codes:
                kind_counts = Counter(error_exemptions[c][0] for c in exempt_codes)
                breakdown = ", ".join(f"{n} {k}" for k, n in sorted(kind_counts.items()))
                detail = "; ".join(
                    f"{c} ({error_exemptions[c][0]}: {error_exemptions[c][2]})"
                    for c in exempt_codes
                )
                info.append(
                    f"error codes exempt from fixture coverage: {len(exempt_codes)} "
                    f"({breakdown}) -- {detail}"
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
        if expected_status == "draft" and (fm.get("tracking") or impl_tracking):
            fields = ", ".join(
                name for name in ("tracking", "impl_tracking") if fm.get(name)
            )
            problems.append(
                f"{rel}: draft has {fields} metadata — tracked work must transition "
                f"to 1-under-review (PROCESS.md)"
            )
        if expected_status == "under-review" and not fm.get("tracking"):
            # Hard-enforced, retroactively: an RFC entering under-review needs a
            # linked tracking issue in the same change (PROCESS.md, 2026-08-23).
            # Unlike impl_status's grandfather clause below, this one has no
            # exemption for RFCs that reached under-review before the rule existed —
            # backfilled 2026-08-23 for all pre-existing cases found.
            problems.append(f"{rel}: missing tracking (required from under-review onward)")

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
                    f"{rel}: no reference to {rid.upper()} found under reference/spec/ — "
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

    trackers, tracker_error = fetch_open_milestoned_rfc_trackers()
    if tracker_error:
        tracker_info = "scheduled RFC tracker check skipped: " + tracker_error
        if os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"):
            problems.append(
                "scheduled RFC tracker check failed despite a configured GitHub "
                f"token — refusing to pass without verifying milestones: {tracker_error}"
            )
    else:
        tracker_info = (
            f"scheduled RFC tracker check: {len(trackers)} open milestoned "
            f"RFC tracker(s) checked"
        )
        problems.extend(scheduled_draft_problems(id_to_stage, trackers))

    problems.extend(status_citation_problems(id_to_stage))
    problems.extend(retired_host_references())

    for f in REPO_ROOT.rglob("*.md"):
        # Same historical-record exemption as status_citation_problems/fix_referrers,
        # same day, same root cause: a dated snapshot citing an RFC's path as it was
        # when written is correct, not dangling, even after that RFC moves stage.
        if (
            ".git" in f.parts
            or "archive" in f.parts
            or "5-superseded" in f.parts
            or "6-refused" in f.parts
            or "cycles" in f.parts
        ):
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
                "rfcs/INDEX.md is missing RFC mentions for: "
                + ", ".join(r.upper() for r in missing)
            )

    # Runs unconditionally, unlike coverage_check_problems() below -- exemption
    # validity needs no fixture corpus, so it isn't gated behind METEL_CORE_ROOT.
    problems.extend(spec_exemption_problems())

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
    print(tracker_info)
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
                "rfcs/INDEX.md is missing RFC mentions for: "
                + ", ".join(r.upper() for r in missing)
            )

        problems.extend(spec_origins_drift_problems())
        problems.extend(error_code_fixtures_drift_problems())

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
        exemptions = scan_spec_exemptions()
        untested = [
            sid for sid in all_spec_block_ids()
            if not spec_citations.get(sid) and sid not in exemptions
        ]
        COVERAGE_BASELINE_PATH.write_text(
            build_coverage_baseline_json(coverage_by_rfc, untested)
        )
        gap_count = sum(
            1
            for _s, uncovered, kind, _spec_anchored, _rfc_only in coverage_by_rfc.values()
            if kind is None and uncovered
        )
        print(
            f"Wrote {COVERAGE_BASELINE_PATH.relative_to(REPO_ROOT)} "
            f"({gap_count} RFC(s) with a recorded gap, {len(untested)} spec block(s) "
            f"with no citing fixture)"
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
        if write_error_code_fixtures():
            print(f"Wrote fixtures backlinks in {ERROR_CODES_PATH.relative_to(REPO_ROOT)}.")
        else:
            print("error-codes.md fixtures backlinks already current -- nothing to write.")
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
    p_trans.add_argument("--tracking", default="", help="Tracking task/URL — required when --to under-review or --to integrated")
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
