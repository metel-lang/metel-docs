#!/usr/bin/env python3
"""RFC lifecycle tool for metel-docs. See internal/rfcs/PROCESS.md.

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
                                       (a ClickUp task/URL) and sets
                                       `impl_status: not-started` alongside it —
                                       no RFC enters integrated without a
                                       linked implementation-tracking task.
                                       `--to implemented` sets
                                       `impl_status: implemented`.
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
                                       references, and (for integrated/implemented
                                       RFCs) that impl_status/impl_tracking are set
                                       and the spec actually references the RFC.
                                       Read-only.
  index --check-drift                  Compare INDEX.md's last_built date against
                                       every RFC's own frontmatter date. Read-only.
  index --suggest-placement <rfc-id>   Suggest which INDEX.md cluster section an
                                       RFC's content is most similar to. Read-only.

No dependencies beyond the Python 3 standard library.
"""

import argparse
import datetime
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RFCS_DIR = REPO_ROOT / "internal" / "rfcs"

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
    print(f"Created {path.relative_to(REPO_ROOT)}")
    print("Reminder: internal/rfcs/INDEX.md needs a new entry for this RFC.")


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
    print("Reminder: internal/rfcs/INDEX.md may need updating for this RFC's new status.")
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
                "transitioning to 'integrated' requires --tracking <ClickUp task/URL> — "
                "no RFC enters integrated without a linked implementation-tracking task "
                "(see PROCESS.md's 3-integrated exit criteria)."
            )
        extra_fm["impl_tracking"] = args.tracking
        extra_fm["impl_status"] = "not-started"
    elif args.tracking:
        extra_fm["impl_tracking"] = args.tracking
    if args.to == "implemented":
        extra_fm["impl_status"] = "implemented"
    do_transition(rid, args.to, args.reason, extra_fm=extra_fm or None)
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
    print(f"{rid.upper()}: impl_status -> {args.set}" + (f", impl_tracking -> {args.tracking}" if args.tracking else ""))
    if args.set == "implemented" and stage != "implemented":
        print(f"Reminder: run `rfc.py transition {rid} --to implemented` to move the RFC itself.")


def cmd_supersede(args):
    rid = normalize_id(args.rfc_id)
    by_ids = [normalize_id(x) for x in args.by.split(",")]
    reason = args.reason or f"Superseded by {', '.join(i.upper() for i in by_ids)}."
    do_transition(rid, "superseded", reason, extra_fm={"superseded_by": ", ".join(by_ids)})
    print("Reminder: write the reconciliation content by hand (what carried forward, "
          "what didn't) — this tool only performs the mechanical move.")
    cmd_check(args)


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

# [a-z-]+ not [a-z]+: stage dir names like "1-under-review" have more than one hyphen.
PATH_REF_RE = re.compile(r"internal/rfcs/[0-6]-[a-z-]+/rfc-[\w.-]+\.md")


SPEC_DIR = REPO_ROOT / "public" / "reference" / "spec"
VALID_IMPL_STATUS = {"not-started", "in-progress", "implemented"}


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


def cmd_check(args=None):
    problems = []
    seen_ids = {}
    known_paths = set()

    for f in find_rfc_files():
        rel = str(f.relative_to(REPO_ROOT))
        known_paths.add(rel)
        rid = rfc_id_from_filename(f)
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

    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("check: no problems found.")
    return problems


# --------------------------------------------------------------------------
# index --check-drift / --suggest-placement
# --------------------------------------------------------------------------

def cmd_index(args):
    index_path = RFCS_DIR / "INDEX.md"
    if not index_path.exists():
        error(f"{index_path} not found")

    if args.check_drift:
        fm, _ = parse_file(index_path)
        last_built = fm.get("last_built")
        if not last_built:
            error("INDEX.md has no last_built frontmatter field")
        stale = []
        for f in find_rfc_files():
            rfm, _ = parse_file(f)
            rfc_date = rfm.get("updated") or rfm.get("date")
            if rfc_date and rfc_date > last_built:
                stale.append((rfc_date, f.relative_to(REPO_ROOT)))
        if stale:
            print(f"INDEX.md last_built = {last_built}. Changed since then:")
            for d, path in sorted(stale):
                print(f"  {d}  {path}")
        else:
            print(f"INDEX.md ({last_built}) looks current.")
        return

    if args.suggest_placement:
        rid = normalize_id(args.suggest_placement)
        target_path = find_path_for_id(rid)
        if target_path is None:
            error(f"RFC {rid} not found")
        clusters = parse_index_clusters(index_path.read_text())
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

    error("index requires --check-drift or --suggest-placement RFC-ID")


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
    p_trans.add_argument("--tracking", default="", help="ClickUp task/URL — required when --to integrated")
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

    p_index = sub.add_parser("index", help="Index maintenance helpers (read-only)")
    p_index.add_argument("--check-drift", action="store_true")
    p_index.add_argument("--suggest-placement", metavar="RFC_ID")
    p_index.set_defaults(func=cmd_index)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
