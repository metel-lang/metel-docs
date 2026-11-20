#!/usr/bin/env python3
"""Create and audit gap and limitation records, flagging overlaps and contradictions.

A `LIMIT-*` record says what the implementation falls short of; a `GAP-*` record says what the
Language Spec leaves open (ADR-0055 section 4, ADR-0057). They were written by hand, so nothing
compared a new one with the 76 that already existed: two records on one rule, a record that said
"this fails" about a program that had started to work, a plan citing an issue that was long closed.
This tool is the one way to create one, and `check` audits the ones already written. It mirrors
`rfc.py new`, which assigns the number and runs an overlap check for RFCs.

    record.py new --kind limit --area TYPE-INFERENCE --title "..." --summary "..." \\
        --description "<what falls short>" --scope architecture/spec/x.md#y \\
        --affects arch.x.requirement-1 [--repro prog.mtl --repro-expect T0002] \\
        [--relates LIMIT-X-001="why this is not a duplicate"] [--dry-run]
    record.py check [--strict] [--core ../..]

Findings come in two kinds. An *overlap* is a record that may say the same thing: similar text, the
same spec rule or requirement in `affects`, the same tracking issue or RFC, the same diagnostic for
the same target, or the same marked code item. A *contradiction* is a claim that cannot be true
beside another fact: a reproduction that does not give the result the record says, a tracking issue
or RFC that has been closed or refused, a LIMIT that describes the spec (or a GAP the
implementation), or two active records on one target that expect different results.

`new` refuses to write the file on a *blocking* finding (an exact duplicate, a reproduction that
contradicts its own claim, a wrong kind) and on an overlap not acknowledged with
`--relates ID="reason"`. An acknowledgement is stored in the new record as `relates:` so the reason
stays beside the record. `check` applies the overlap rules to every active record pair: an
unacknowledged pair is a warning on a pull request and an error under `--strict` (a release).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DOCS / "tools"))
import check_architecture as ca  # noqa: E402
from textsim import build_tfidf, cosine_sim, tokenize  # noqa: E402

ACTIVE = {"known", "accepted", "mitigated", "planned"}
FENCE_RE = re.compile(r"^```metel([^\n]*)\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
REPRO_RE = re.compile(r"\brepro=(\S*)")
RELATES_ITEM_RE = re.compile(r"([A-Z]+-[A-Z0-9-]+-\d+)\s*\(([^)]*)\)")
ID_RE = {"limit": re.compile(r"^LIMIT-([A-Z0-9-]+)-(\d+)$"), "gap": re.compile(r"^GAP-([A-Z0-9-]+)-(\d+)$")}

# Similarity thresholds on the TF-IDF cosine of title + summary + body.
SIM_DUPLICATE = 0.85   # an exact duplicate in all but name: blocks
SIM_OVERLAP = 0.45     # similar enough to need an acknowledgement on its own
SIM_WITH_TARGET = 0.20  # similar enough to need one when they also share a target


@dataclass
class Record:
    id: str
    kind: str  # "limit" | "gap"
    path: Path | None
    fm: dict
    body: str
    affects: list[str]
    resolution: str
    repros: list[tuple[str | None, str]] = field(default_factory=list)  # (expect, source)

    @property
    def disposition(self) -> str:
        return self.fm.get("disposition") or ""

    @property
    def active(self) -> bool:
        return self.disposition in ACTIVE

    @property
    def targets(self) -> set[str]:
        """What the record is about: spec rules and architecture requirements it affects."""
        return {a for a in self.affects if a.startswith(("spec.", "arch."))}

    @property
    def issues(self) -> set[int]:
        return set(ca.tracked_issues(self.fm))

    @property
    def rfcs(self) -> set[str]:
        return {r.strip().upper() for r in str(self.fm.get("rfc") or "").split(",") if r.strip()}

    @property
    def relates(self) -> dict[str, str]:
        """`relates: "ID (reason); ID (reason)"`: the records this one has been compared with, and why
        each is not a duplicate. A reason may contain `;` but not `)`."""
        return {m.group(1): m.group(2).strip() for m in RELATES_ITEM_RE.finditer(str(self.fm.get("relates") or ""))}

    @property
    def text(self) -> str:
        return f"{self.fm.get('title', '')} {self.fm.get('summary', '')} {self.body[:3000]}"


@dataclass
class Finding:
    kind: str       # "overlap" | "contradiction"
    blocking: bool  # `new` refuses regardless of acknowledgements
    other: str | None  # the other record, if the finding is about a pair
    reason: str
    score: float = 0.0

    def __str__(self) -> str:
        tag = "BLOCK" if self.blocking else self.kind
        who = f" {self.other}:" if self.other else ""
        return f"[{tag}]{who} {self.reason}"


def parse_record(path: Path) -> Record:
    fm, affects, resolution = ca.parse_limitation_file(path)
    _, body = ca.frontmatter_and_body(path.read_text())
    return build_record(fm, body, affects, resolution, path)


def build_record(fm: dict, body: str, affects: list[str], resolution: str, path: Path | None) -> Record:
    rid = fm.get("id") or (path.stem.upper() if path else "")
    kind = "gap" if rid.startswith("GAP-") else "limit"
    repros = []
    for m in FENCE_RE.finditer(body):
        attr = REPRO_RE.search(m.group(1))
        repros.append((attr.group(1) if attr else None, m.group(2)))
    return Record(rid, kind, path, fm, body, affects, resolution, repros)


def load_records(root: Path = DOCS) -> list[Record]:
    out = []
    for sub in ("limitations", "gaps"):
        d = root / "architecture" / sub
        for path in sorted(d.glob("*.md")) if d.is_dir() else []:
            out.append(parse_record(path))
    return out


def next_id(kind: str, area: str, records: list[Record]) -> str:
    prefix = "LIMIT" if kind == "limit" else "GAP"
    nums = [int(m.group(2)) for r in records if (m := ID_RE[kind].match(r.id)) and m.group(1) == area]
    return f"{prefix}-{area}-{(max(nums) + 1) if nums else 1:03d}"


# ---------------------------------------------------------------- pair analysis

def _expect_of(r: Record) -> set[str]:
    return {e for e, _ in r.repros if e}


def compare(a: Record, b: Record, sim: float) -> list[Finding]:
    """What `a` and `b` have in common that a reader should know about (both directions at once)."""
    out: list[Finding] = []
    shared = sorted(a.targets & b.targets)
    issues = sorted(a.issues & b.issues)
    rfcs = sorted(a.rfcs & b.rfcs)
    if sim >= SIM_DUPLICATE:
        out.append(Finding("overlap", True, b.id, f"text is {sim:.0%} similar: an exact duplicate in all but name", sim))
    elif sim >= SIM_OVERLAP:
        out.append(Finding("overlap", False, b.id, f"text is {sim:.0%} similar", sim))
    elif shared and sim >= SIM_WITH_TARGET:
        out.append(Finding("overlap", False, b.id, f"affects the same {_fmt(shared)} and the text is {sim:.0%} similar", sim))
    if issues:
        out.append(Finding("overlap", False, b.id, "tracked by the same issue " + ", ".join(f"metel-core#{n}" for n in issues), 0.5))
    if rfcs and (shared or sim >= SIM_WITH_TARGET):
        # one RFC rightly carries several records: the RFC alone is not a signal
        out.append(Finding("overlap", False, b.id, "cites the same RFC " + ", ".join(rfcs) + " and is about the same thing", 0.4))
    same_code = sorted((_expect_of(a) & _expect_of(b)) - {"ok"})
    if same_code and shared:
        out.append(Finding("overlap", False, b.id, f"gives {', '.join(same_code)} for the same {_fmt(shared)}", 0.6))
    # contradictions between two active records about one target
    if shared and a.active and b.active:
        ea, eb = _expect_of(a), _expect_of(b)
        if ea and eb and ea != eb:
            out.append(Finding("contradiction", False, b.id,
                               f"expects {', '.join(sorted(ea))} where {b.id} expects {', '.join(sorted(eb))} for the same {_fmt(shared)}", 0.7))
        da, db = a.disposition, b.disposition
        if {da, db} == {"accepted", "planned"} and sim >= SIM_WITH_TARGET:
            out.append(Finding("contradiction", False, b.id,
                               f"is `{da}` while {b.id} is `{db}` for the same {_fmt(shared)}: a boundary cannot be both final and scheduled", 0.7))
    if b.disposition in ("resolved", "superseded"):
        out = [Finding(f.kind, f.blocking, f.other, f.reason + f" (and {b.id} is already {b.disposition}: is this a regression?)", f.score)
               if f.kind == "overlap" else f for f in out]
    return out


def _fmt(targets: list[str]) -> str:
    return ", ".join(f"`{t}`" for t in targets[:3]) + (" …" if len(targets) > 3 else "")


def _similarities(drafts: list[Record], others: list[Record]) -> dict[tuple[str, str], float]:
    docs = {r.id: tokenize(r.text) for r in drafts + others}
    vecs = build_tfidf(docs)
    return {(d.id, o.id): cosine_sim(vecs[d.id], vecs[o.id]) for d in drafts for o in others if d.id != o.id}


# ---------------------------------------------------------------- single-record checks

def own_findings(rec: Record, *, resolver=None, rfc_stage=None, run_repro=None) -> list[Finding]:
    """Contradictions between a record's claims and the facts around it."""
    out: list[Finding] = []
    scope = (rec.fm.get("scope") or "").split("#", 1)[0]
    if rec.kind == "limit" and scope.startswith("reference/spec"):
        out.append(Finding("contradiction", True, None, "a LIMIT is an implementation shortfall but its scope is the Language Spec: that is a GAP (ADR-0057)"))
    if rec.kind == "gap" and scope and not scope.startswith("reference/spec"):
        out.append(Finding("contradiction", True, None, "a GAP is a spec boundary but its scope is not the Language Spec: that is a LIMIT (ADR-0055 section 4)"))
    if resolver is not None:
        for n in sorted(rec.issues):
            info = resolver(n)
            if info is None:
                continue
            if info.get("missing"):
                out.append(Finding("contradiction", False, None, f"tracked by metel-core#{n}, which does not exist"))
            elif info.get("state") != "open":
                out.append(Finding("contradiction", False, None, f"tracked by metel-core#{n}, which is closed: a plan cannot rest on it"))
    if rfc_stage is not None:
        for r in sorted(rec.rfcs):
            stage = rfc_stage(r)
            if stage in ("5-superseded", "6-refused"):
                out.append(Finding("contradiction", False, None, f"cites {r}, which is {stage.split('-', 1)[1]}: it cannot carry the plan"))
            elif stage == "4-implemented" and rec.active:
                out.append(Finding("contradiction", False, None, f"cites {r}, which is implemented: is the limitation still true?"))
    if run_repro is not None:
        for expect, source in rec.repros:
            if expect is None:
                continue
            got = run_repro(source)
            if got != expect:
                out.append(Finding("contradiction", True, None,
                                   f"its reproduction is recorded as `repro={expect}` but the interpreter gives `{got}`: the claim is not true today"))
    return out


# ---------------------------------------------------------------- audit and creation

def acknowledged(a: Record, b: Record) -> bool:
    return b.id in a.relates or a.id in b.relates


def audit(records: list[Record]) -> list[tuple[Record, Record, list[Finding]]]:
    """Overlapping or contradicting pairs of active records that nobody has acknowledged."""
    active = [r for r in records if r.active]
    sims = _similarities(active, active)
    seen, out = set(), []
    for a in active:
        for b in active:
            if a.id >= b.id or (a.id, b.id) in seen:
                continue
            seen.add((a.id, b.id))
            if acknowledged(a, b):
                continue
            found = compare(a, b, sims.get((a.id, b.id), 0.0))
            if found:
                out.append((a, b, found))
    return out


def analyze_draft(draft: Record, records: list[Record], **kw) -> list[Finding]:
    sims = _similarities([draft], records)
    out = own_findings(draft, **kw)
    for other in records:
        out.extend(compare(draft, other, sims.get((draft.id, other.id), 0.0)))
    return sorted(out, key=lambda f: (not f.blocking, f.kind != "contradiction", -f.score))


def render(rec: Record) -> str:
    fm = rec.fm
    lines = ["---", f"id: {rec.id}", f'title: "{fm["title"]}"', f'summary: "{fm["summary"]}"', f'scope: "{fm["scope"]}"',
             f"owner: {fm['owner']}", f'discovered_by: "{fm["discovered_by"]}"', f"disposition: {fm['disposition']}"]
    for key in ("rfc", "tracked_by", "relates"):
        if fm.get(key):
            val = fm[key]
            lines.append(f'{key}: "{val}"' if key == "relates" else f"{key}: {val}")
    lines += [f"review: {fm.get('review') or 'null'}", "---", ""]
    return "\n".join(lines) + rec.body


def default_body(kind: str, description: str, repro: tuple[str, str] | None, affects: list[str]) -> str:
    head = "## Limitation" if kind == "limit" else "## Gap"
    parts = [head, "", description.strip(), ""]
    if repro:
        expect, source = repro
        parts += [f"```metel repro={expect}", source.rstrip(), "```", ""]
    parts += ["## Impact", "", "TODO: who sees this, and what they do instead.", "", "## Affects", ""]
    parts += [f"- `{a}`" for a in affects] or ["- TODO"]
    parts += ["", "## Resolution", "", "None yet.", ""]
    return "\n".join(parts)


def make_runner(core: Path | None):
    """A `run_repro(source) -> result` against core's interpreter, or None when it cannot run."""
    if core is None:
        return None
    binary = core / "target" / "release" / "metel"
    script = core / "tools" / "check_record_repros.py"
    if not binary.is_file() or not script.is_file():
        return None
    sys.path.insert(0, str(core / "tools"))
    import check_record_repros as crr  # noqa: E402
    return lambda source: crr.run(binary, source)


def cmd_new(args) -> int:
    records = load_records(DOCS)
    area = args.area.upper()
    rid = next_id(args.kind, area, records)
    fm = {"id": rid, "title": args.title, "summary": args.summary, "scope": args.scope, "owner": args.owner,
          "discovered_by": args.discovered_by, "disposition": args.disposition,
          "rfc": args.rfc or None, "tracked_by": args.tracked_by or None, "review": None}
    acks = dict(a.split("=", 1) for a in args.relates or [])
    for oid, reason in acks.items():
        if not reason.strip():
            print(f"error: --relates {oid}= needs a reason")
            return 2
    if acks:
        fm["relates"] = "; ".join(f"{k} ({v.strip()})" for k, v in acks.items())
    repro = None
    if args.repro:
        repro = (args.repro_expect or "ok", Path(args.repro).read_text())
    body = default_body(args.kind, args.description, repro, args.affects or [])
    draft = build_record(fm, body, args.affects or [], "None yet.", None)

    resolver = ca.gh_issue_resolver if not args.offline else None
    rfc_stage = (lambda r: ca.rfc_stage(DOCS / "rfcs", r[4:])) if (DOCS / "rfcs").is_dir() else None
    core = Path(args.core).resolve() if args.core else None
    findings = analyze_draft(draft, records, resolver=resolver, rfc_stage=rfc_stage, run_repro=make_runner(core))
    if repro and make_runner(core) is None:
        print("note: no interpreter found (pass --core with a built target/release/metel), so the reproduction was not run")

    blocking = [f for f in findings if f.blocking]
    unacked = [f for f in findings if not f.blocking and f.other and f.other not in acks]
    unacked_own = [f for f in findings if not f.blocking and not f.other and f.kind == "contradiction"]
    print(f"{rid}: {len(findings)} finding(s) against {len(records)} existing records")
    for f in findings:
        print(f"  {f}")
    if blocking or unacked_own:
        print("not written: resolve the blocking findings above")
        return 1
    if unacked:
        ids = sorted({f.other for f in unacked})
        print("not written: acknowledge each overlap with --relates ID=\"why this is not a duplicate\" ("
              + ", ".join(ids) + "), or fold this into the existing record")
        return 1
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    sub = "limitations" if args.kind == "limit" else "gaps"
    path = DOCS / "architecture" / sub / f"{rid.lower()}.md"
    path.write_text(render(Record(rid, args.kind, path, fm, body, args.affects or [], "None yet.")))
    print(f"wrote {path.relative_to(DOCS)}; fill in the TODOs, then run check_architecture.py --check")
    return 0


def cmd_check(args) -> int:
    records = load_records(DOCS)
    pairs = audit(records)
    for a, b, found in pairs:
        reasons = "; ".join(f.reason for f in sorted(found, key=lambda f: -f.score))
        print(f"{'error' if args.strict else 'warning'}: {a.id} and {b.id}: {reasons}"
              f" -- acknowledge with `relates: \"{b.id} (reason)\"` in {a.id.lower()}.md, or merge the records")
    print(f"record overlaps: {len(pairs)} unacknowledged pair(s) among {sum(r.active for r in records)} active records")
    return 1 if (pairs and args.strict) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="create a record, after checking it against the existing ones")
    n.add_argument("--kind", choices=["limit", "gap"], required=True)
    n.add_argument("--area", required=True, help="the AREA part of the id, e.g. TYPE-INFERENCE")
    n.add_argument("--title", required=True)
    n.add_argument("--summary", required=True)
    n.add_argument("--description", required=True, help="what falls short; also what similarity is measured on")
    n.add_argument("--scope", required=True)
    n.add_argument("--owner", default="metel-frontend")
    n.add_argument("--discovered-by", default="record.py new")
    n.add_argument("--disposition", default="known", choices=sorted(ACTIVE))
    n.add_argument("--affects", action="append")
    n.add_argument("--tracked-by")
    n.add_argument("--rfc")
    n.add_argument("--repro", help="a Metel program that shows it")
    n.add_argument("--repro-expect", help="ok, or the diagnostic code it gives (default ok)")
    n.add_argument("--relates", action="append", metavar='ID="reason"', help="acknowledge an overlap with a reason")
    n.add_argument("--core", help="metel-core checkout with a built target/release/metel, to run the reproduction")
    n.add_argument("--offline", action="store_true", help="do not ask GitHub about the tracking issue")
    n.add_argument("--dry-run", action="store_true")
    c = sub.add_parser("check", help="audit every active record pair for unacknowledged overlaps")
    c.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    return cmd_new(args) if args.cmd == "new" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
