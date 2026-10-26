---
id: rfc-0185
title: "Remove Type-Directed Dereference"
date: '2026-10-24'
status: accepted
updated: '2026-10-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/1596'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

> **Status — accepted (2026-10-26).** Open questions resolved 2026-10-26

## Summary

Remove the implicit **type-directed read-copy** out of a reference (RFC-0067a §3a, spec
"Reading a value out of a reference"). Reading the value a reference points to is always
spelled `*r`:

```metel
let x := 42;
let r: &i64 := &x;

let y: i64 := r;       // today: copies x out (annotation drives it); proposed: T0001
let y: i64 := *r;      // proposed: the one way to read through a reference

fun get(r: &i64) -> i64 { r }      // today: tail expression copies out; proposed: T0001
fun get(r: &i64) -> i64 { *r }     // proposed
```

Auto-deref at **selectors** (field access, indexing, method dispatch, calling through a
reference) is *not* touched; this RFC removes only the case where an expected *type*, not a
selector, decides that a reference should be read through.

This is the "Strict Go" alternative that RFC-0112 §5 considered and declined. It is filed as
a separate RFC so the choice is explicit: **accepting it makes RFC-0112 unnecessary**, and
accepting RFC-0112 forecloses it. It breaks shipped, spec'd behaviour, so it needs this RFC
before any implementation (see `metel_rfc_before_implementation`).

Terminology: the spec calls the mechanism "type-directed copy" / "read-copy". "Type-directed
dereference" is used here for the same thing: a reference is dereferenced because of a
*type*, with no `*` in the source.

---

## Motivation

### 1. An annotation elsewhere changes what an expression does

The same expression means two different things depending on a type written somewhere else:

```metel
let a := r;          // a: &i64, an alias of x
let b: i64 := r;     // b: i64, a copy of x   <- same `r`, different operation
```

Every other type annotation in Metel *checks* what an expression already is. This one
changes what the expression *does*, and with it the aliasing of the result (an alias versus
an independent copy), the `Copy` obligation, and (for `&var`) whether later writes are
visible. The effect reaches across a declaration boundary: in

```metel
fun get(r: &i64) -> i64 { r }
```

whether the body copies is decided by the return type in the signature, not by anything on
the line that does it. A reader has to look up the signature to learn that `r` is being
dereferenced.

### 2. The boundary is hard to state and expensive to hold

The rule fires at `let`/`var` annotations, ascriptions, `return`, `break`, and tail
expressions. It does not fire at call arguments or operands (measured against the current
build: `take(r)` and `r + 1` are `T0001`/`T0005`). RFC-0110 measured that RFC-0067a's own
text "overstates its own coverage", and RFC-0112 exists only to give the boundary a stated
rule ("the expected type must be authored in the declaration you are lexically inside") and a
mechanical enforcement (a provenance tag carried alongside every expected type, classified at
every site that supplies one). That is a design and a compiler mechanism whose sole job is to
keep an implicit conversion from spreading. Removing the conversion removes the job.

### 3. The spec already says it does not exist

`expressions.md`, "Auto-deref covers **selectors only** … Everywhere else, reading through a
reference is spelled explicitly." The `types.md` section on reading a value out of a
reference is an exception to that sentence, listed in the bullet that follows it. RFC-0110
adopted exactly the Go split (selectors implicit, everything else spelled `*`), applied it to
the write side, and explicitly left the read side to RFC-0112. This RFC finishes that split.

### 4. Two ways to say the same thing

`*r` already reads through a reference in every expression position
(`spec.expressions.references.dynamics-7`). With read-copy, `let y: i64 := r` and
`let y: i64 := *r` are both accepted and mean the same thing, and a code base mixes them.
One spelling is easier to read, search for, and lint.

### 5. Inference

An implicit conversion keyed on a solved expected type is sensitive to inference order:
RFC-0112 §1.0 records a solve-order defect that made the rule's behaviour depend on when a
substitution was applied, fixed only by running the peel test against the substituted type.
A rule that needs that care to be well-defined is a rule worth not having.

---

## Prior decisions this has to answer

RFC-0112 §5 declined "Strict Go: retire read-copy entirely" for two reasons. They are the
case against this RFC, so each gets an answer.

1. *"§3a is implemented and integrated, retiring it is a breaking change across existing
   code."* True, and the cost is real (Costs below). It is also **measurable before it is
   paid**: the rule fires at a bounded set of positions, so a diagnostic-first
   implementation (the old behaviour becomes an error with a `*r` suggestion, run over the
   whole fixture and example corpus) gives the exact number of affected sites. The corpus
   has 8 fixtures that cite the rule, 5 of them positive. RFC-0136 and RFC-0098 are the
   precedent for a pre-1.0 lexical migration with no edition gating.
2. *"The annotation is right there at the use site — the ambiguity that justifies requiring
   a sigil elsewhere genuinely is absent here."* This holds for `let y: i64 := r` (the
   annotation is on the line). It does not hold for the tail expression and `return` cases,
   where the deciding type is in the signature, nor for the `let` case in the other
   direction: dropping the annotation silently changes the operation (Motivation §1). The
   absence of *ambiguity for the compiler* is not the same as the operation being *visible to
   the reader*, and the Go model's objection is to the latter.

---

## 1. The change

### Rule

Delete `spec.types.references.reading-a-value-out-of-a-reference.legality-1` and the prose
section it belongs to. A reference-typed expression is never implicitly read through. Where
a non-reference type is expected and a reference is found, the existing mismatch error is
reported, with a targeted suggestion:

```
T0001: expected `i64`, found `&i64`
  = help: read the value out with `*r` (copies a `Copy` referent)
```

### What stays

- `*r` (RFC-0110, `spec.expressions.references.dynamics-7`, `-8`): unchanged. Each leading
  `*` reads through one layer, so the chain case is `**rr`.
- Selector auto-deref: field access, indexing, method dispatch, and calling through a
  reference, through any number of layers. Unchanged.
- `&var T` to `&T` coercion (`spec.types.references.legality-1`). That is a reference-to-
  reference weakening, not a dereference. Unchanged.
- RFC-0108 reference-transparent `match` scrutinees. A scrutinee is a selector-like
  position (patterns select into it); unchanged.
- The `Copy` requirement. `*r` of a non-`Copy` referent is still rejected as a move out of
  a reference; the three negative fixtures for the old rule
  (`neg_14`, `neg_16`, `neg_19`) become fixtures for `*r` on a non-`Copy` value.

### Before / after

```metel
// before                                       // after
let y: i64 := r;                               let y: i64 := *r;
let z: i64 := rr;        // two layers         let z: i64 := **rr;
fun get(r: &i64) -> i64 { r }                  fun get(r: &i64) -> i64 { *r }
fun get(r: &i64) -> i64 { return r; }          fun get(r: &i64) -> i64 { return *r; }
let n: i64 := loop { break (p: i64); };        let n: i64 := loop { break *p; };
```

### What this does to RFC-0112

RFC-0112's whole subject (the provenance tag, the four categories, the enforcement in §3,
the declined extensions in §4) is moot if read-copy does not exist. Its unresolved questions
1, 2 and 5 disappear. If this RFC is accepted, RFC-0112 moves to `5-superseded`. If RFC-0112
is accepted instead, this one is refused. They are two answers to one question and the
corpus should hold only one.

---

## 2. Alternatives considered

1. **Keep the rule, adopt RFC-0112's provenance enforcement.** Preserves the ergonomics and
   the shipped behaviour; pays for it with a compiler mechanism and a boundary a reader must
   learn. This is the live competitor.
2. **Keep the rule at `let`/ascription only; drop it at `return`, `break` and tail.** The
   position where the deciding type is on the same line stays; the positions where it is in
   a signature go. Smaller migration, but it keeps two spellings and leaves RFC-0112's
   boundary question open for the positions that remain.
3. **Status quo with documentation fixes** (RFC-0112's "leave it as documentation").
   Cheapest. Leaves Motivation §§1 and 4.
4. **Make the copy explicit but shorter** (a method such as `r.copy()`, or reuse
   `Clone`). `*r` already exists and is the language's dereference; a second spelling would
   repeat Motivation §4.

---

## 3. Costs

- **Breaks shipped, spec'd, tested behaviour.** The old rule is
  `spec.types.references.reading-a-value-out-of-a-reference.legality-1`, covered by 8
  fixtures. Any program that returns or binds a reference where a value is declared
  changes. The corpus measure above bounds it.
- **More `*` in code.** Code that returns a `Copy` value read through a reference now says
  so. That is the point of the change, and it is also a keystroke cost.
- **Churn in implemented RFCs.** RFC-0067a (§3a), RFC-0110 (its measured-table row), RFC-0108
  (the "type-directed copy" cross-reference) cite the mechanism; their prose is amended and
  RFC-0112 is superseded.
- **Diagnostics work.** Every site that formerly accepted the conversion now needs the
  `*r` suggestion; without it the error ("expected `i64`, found `&i64`") is a regression for
  anyone who relied on the old rule.

---

## Open Questions — resolved 2026-10-26

1. **RFC-0066 §3a, extraction of an allocated value.** *Resolved: extraction is explicit
   too.* RFC-0066 is amended in the same change: `*ptr` is the only way to move a value out
   of an `@a T` pointer, and the type-directed forms (`let node: Node := ptr;`, `ptr: Node`,
   `process(ptr: Node)`) are removed. RFC-0066 returns to `1-under-review` with the amendment
   (it is not implemented, so nothing regresses) and is re-accepted on its own track.
2. **Corpus measurement first?** *Resolved: measured.* With the read-copy disabled, 22 of
   1541 integration fixtures fail (6 negative `evaluator/references/neg_14..19_read_copy_*`
   and 16 positive: references 01, 02, 03, 05, 07, 13; functions 66-70; closures 74; types
   14; structs 70, 94; move_check `abstract_read_copy_boundaries`), 4 of 427 unit tests
   (`move_check::tests`), and 4 of 215 documentation examples (`expressions.md`, three in
   `types.md`). README, getting-started, tutorials and the blog: none. Every site is migrated
   in the implementing change.
3. **Hard cut or deprecation window.** *Resolved: hard cut*, with a diagnostic help line:
   `= help: read the value out with `*r` (copies a Copy referent)`.
4. **`break (p: i64)` and ascription.** *Resolved.* Ascription stops performing the
   read-copy. It keeps its dyn-erasure and singleton coercions (RFC-0078), which are
   unrelated to references. `spec.types.type-ascription.legality-1` is reworded to say so;
   it previously claimed "no runtime conversion", which was already untrue.
5. **Release timing.** *Resolved: v0.15.0*, with a changelog migration note.

---

## References

- RFC-0067a — Reference Types (§3a introduced the read-copy; amended by this RFC).
- RFC-0110 — Explicit Dereference Operator (the `*r` operator and the selectors-only split).
- RFC-0112 — Auto-Deref Scope and Expected-Type Provenance (draft; made moot if this is
  accepted; its §5 "Strict Go" is this RFC).
- RFC-0108 — Reference-transparent match scrutinees (unchanged).
- RFC-0066 — Allocated Value Extraction (§3a, the parallel mechanism; Open Question 1).
- RFC-0136, RFC-0098 — pre-1.0 syntax migrations without edition gating.
- `reference/spec/types.md` — "Reading a value out of a reference";
  `reference/spec/expressions.md` — "Auto-deref covers selectors only".

---

## Decision

**Outcome:** accepted (2026-10-26).

Reading through a reference is always `*r`. The type-directed read-copy is removed at every
site (`let` annotation, call argument, `return`, tail, `break`, ascription) as a hard cut
in v0.15.0 with a `*r` help line and a changelog migration note. Ascription keeps its
dyn/singleton coercions. RFC-0066's type-directed extraction is made explicit (`*ptr`) in
the same change. Supersedes RFC-0112.
