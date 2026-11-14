---
id: rfc-0151
title: "Tuples as Numeric-Label Rows"
date: '2026-08-29'
status: under-review
updated: '2026-11-14'
tracking: 'https://github.com/metel-lang/metel-core/issues/1956'
---

> **Consolidation RFC.** Anonymous record types (RFC-0116) landed a general
> structural product former with a closed row. This RFC observes that a tuple is
> that former with numeric labels, and proposes making `(A, B)` *sugar* for the
> row `{ 0: A, 1: B }` rather than a parallel type with its own representation,
> its own narrowing story, its own branding question, and its own variadic
> spine. The surface syntax stays; the second type-former goes away.

> **Status — under review (2026-11-12).** Language owner moved it to review for v0.16.0 (Copy migration stage); design settlement tracked in metel-core#1956, decision in #1848

## Summary

`(A, B, C)` desugars to the closed anonymous record type `{ 0: A, 1: B, 2: C }` —
a row whose labels are the integers `0 .. N-1`. The value `(a, b, c)` desugars to
`{ 0 = a, 1 = b, 2 = c }`, and `t.0` is field access on the label `0`. Tuple
patterns desugar to record patterns. The compiler still *prints* `(i64, String)`,
and the surface forms `(a, b)` / `(A, B)` / `let (x, y) = …` remain — they are
notation for a numeric-label row, the way `[T]` is notation for an array.

There is one structural product former (the row), one narrowing rule, one row
type-identity, one branding story. Tuple-specific machinery — a distinct
`Type::Tuple`, a distinct `Copy` derivation, a distinct residual form (which
RFC-0150 currently has to invent) — is deleted or folded in.

## Motivation

After RFC-0116, a tuple brings nothing a numeric-label anonymous record could not
express, and each downstream feature has had to answer the tuple question
separately:

- **Row narrowing (RFC-0117)** is defined for records and structs. Moving `t.1`
  out of `(A, B)` is a partial move (RFC-0071 §9a tracks tuple elements like
  struct fields) but has no residual type.
- **Nested row narrowing (RFC-0150)** has an entire open question (§3) whose
  whole content is "define a residual form for tuple-typed fields, or ban nested
  narrowing through them." With this RFC that question is answered for free: a
  tuple residual is a row residual.
- **Variadic generics (RFC-0125, v0.14.0)** need to fold a type pack into a
  positional heterogeneous sequence. If that sequence is a row, the fold is a row
  operation and there is no separate tuple-pack calculus to design.
- **`Callable<Args, Ret>` (RFC-0061 §7.1, metel-core#893)** encodes a function's
  argument list as a tuple. As a numeric-label row it is one more anonymous
  record, subject to the same rules as any other.
- **Row bounds (RFC-0118)**, **branded rows (RFC-0137)**, and the `Copy` / `Ord`
  derivations all already work on rows. A tuple inherits them by being one.

The cost of *not* consolidating is a permanent second column in every one of
these designs.

## Proposal

### 1. The desugaring

| Surface | Desugars to |
|---|---|
| `(A, B, C)` *(type)* | `{ 0: A, 1: B, 2: C }` |
| `(a, b, c)` *(value)* | `{ 0 = a, 1 = b, 2 = c }` |
| `(T,)` *(type)* | `{ 0: T }` |
| `(x,)` *(value)* | `{ 0 = x }` |
| `t.0`, `t.1`, … | field access on labels `0`, `1`, … |
| `let (x, y) = t` | `let { 0 = x, 1 = y } = t` *(record pattern; bind label to name)* |
| `match … { (0, y) => … }` | `match … { { 0 = 0, 1 = y } => … }` |
| `(T)` *(type)*, `(e)` *(value)* | grouping only — **not** a 1-tuple (unchanged) |

Desugaring happens after parsing and before type-checking; nothing downstream of
that point sees a distinct tuple node.

### 2. Numeric labels and row order

A row's labels become **integers or identifiers**. Label order for iteration,
canonical form, and derived `Ord` is:

1. integer labels first, in **numeric** order (`0, 1, 2, … 9, 10, 11`);
2. then identifier labels, lexicographic.

The numeric ordering is the point — a tuple `(a₀ … a₁₀)` must keep `0 < … < 10`,
not the lexicographic `0 < 1 < 10 < 2` that string labels would give.

A row may mix the two (`{ 0: A, .name: B }`); it is legal and simply unusual.
Constructing one requires the `{ … }` form — the `(…)` sugar only produces
integer labels `0 .. N-1` with no gaps.

### 3. Copy, Drop, Ord — derived from the row, not the former

- **`Copy`**: a numeric-label row is `Copy` when every field is `Copy` — the
  existing anonymous-record rule (RFC-0071 `spec.ownership.copy.legality-1`
  already reads "every struct field or enum payload"), no tuple special case.
- **`Drop`**: RFC-0116 §3 forbids a custom `Drop` on an anonymous record; that
  now covers tuples too (they could never carry one anyway). Field-wise teardown
  is unchanged.
- **`Ord` / `PartialOrd` / `Eq`**: the anonymous-record derivation compares
  fields in label order; for an integer-labelled row that is positional order, so
  `(1, 2) < (1, 3)` falls out. This RFC depends on that derivation existing for
  anonymous records (RFC-0080 territory); if it does not yet, that is a
  prerequisite, not new work this RFC adds.

### 4. Narrowing, row bounds, branding — apply unchanged

- **Narrowing (RFC-0117)**: moving the last element, `t.1` out of `(A, B)`, narrows `t` to
  `{ 0: A }` = `(A,)`. Moving any other element leaves a gap and a row that is not a tuple
  (§4a). The `2^N` subset-lattice bound, the "residual is an ordinary value" property, and
  path-sensitivity all apply with no addition.
- **Nested narrowing (RFC-0150)**: a tuple-typed field's residual is a
  numeric-label row residual. RFC-0150 §3 (define tuple residuals or ban them)
  is **resolved** by this RFC — delete the open question, keep the recursion.
- **Row bounds (RFC-0118)**: `<record T: { 0: i64, .. }>` matches any row with an
  `i64` at label `0`, tuple or hand-written. Whether that cross-match is
  desirable is Open Question 3.
- **Branded rows (RFC-0137)**: a tuple is an *anonymous* row — no brand, never
  satisfies a nominal projection bound — exactly as an anonymous record does not.

### 4a. A partial move out of a tuple leaves a row, and nothing compacts it

*Added 2026-11-14.* Today move checking tracks tuple elements (RFC-0071 section 9a, `spec.ownership.partial-moves`):
moving `t.0` and then `t.1` is accepted, moving `t.0` twice and using `t` whole after `t.0` moved are rejected. What a
tuple lacks is a **type** for what is left: a struct narrows to `S.{ .b }` and passes to a function that names it, while a
tuple's remainder has no spelling, and a projection `t.{ .1 }` is rejected. Measured 2026-11-14 on the metel-core checkout.
This RFC gives the remainder the type RFC-0117 already gives every other row.

**The rule is RFC-0117's, with no tuple case.** The residual of `t` after a move is the row with the same labels minus the
moved ones, at the same types. The remaining elements keep their labels:

```metel
let t := (a, b, c);          // .{ .0: A, .1: B, .2: C }
let x := t.1;                // t : .{ .0: A, .2: C }   (a gap at .1)
```

The residual is a tuple, under section 5, only when the labels that remain are exactly `.0 .. .N-1`, which is when the moved
elements were a suffix: `(A, B)` after `t.1` is `(A,)`. Any other residual is a sparse row and prints in brace form,
`.{ .0: A, .2: C }`.

**Nothing compacts the remainder, and no rule says it should.** Renumbering `.2` to `.1` would be a rule for tuples alone,
and it would be unsound for the program that wrote the move:

- *Names would stop being stable.* Moves, projections and bounds name elements by label. If the remainder were renumbered
  after `t.1` moved, `t.2` would stop existing and `t.1` would mean what `t.2` meant a statement before, so one expression
  changes meaning with the statements around it. A live `&t.2` would be left pointing at a renamed element.
- *It would hide a cost.* A compacted value moves the remaining elements down, O(n), as a side effect of a move.
- *The general rule says otherwise.* Every other row keeps its labels. A rule that keeps them except when they are numeric is
  a special case, and the only way to avoid it is to make numeric labels ordinal (derived from position rather than named),
  which makes a tuple a different kind of type than a row and gives up what this RFC is for.

**Getting a tuple back is explicit.** Two ways, neither a tuple rule:

- *Destructure.* A pattern that names the elements to keep builds a new tuple from them, by position, so it is already the
  compaction when it is wanted.
- *Relabel.* A general row operation that renames labels in a projection (`.2` as `.1`) turns the sparse remainder into a
  dense row, with its cost visible and its effect on the type stated. It applies to any row, so it is not part of this RFC. If
  it is wanted, it is a small follow-on RFC beside RFC-0191 (one-field record update).

A function that takes `(A, C)` takes a dense tuple. The sparse remainder is passed to one that takes a row bound
(`.{ .0: A, ..R }`), or relabelled first.

### 5. Type display

The printer renders a row whose labels are exactly `0 .. N-1` with no gaps as
`(T₀, …, Tₙ)`, and any other row as `{ … }`. Round-trips: `(i64, String)` prints
as `(i64, String)`, `{ 0: i64, 1: String }` written by hand prints the same, and
`{ 0: i64, 2: String }` (a gap) prints as `{ 0: i64, 2: String }`.

### 6. `()` and the unit type

**`()` is the empty closed row `{}`.** The primitive `Unit` type is retired as a separate type, and the two
spellings denote one type with one value:

- **Type.** `()` and `{}` are the same type. `-> ()`, `Result<(), E>` and a closed empty row are
  interchangeable. The tuple sugar has arity 0 as well: `(A, B)` is `.{ .0: A, .1: B }`, and no elements give
  `{}`.
- **Value.** The unit value is the empty record. A literal `()` and an empty record literal `{}` denote it, and
  an empty block, or a block with no tail, has this type.
- **Patterns.** `()` and `{}` match it.
- **One impl target.** `extend (): A` and `extend {}: A` name the same target, so writing both is an overlap
  error.
- **Printing.** The type prints as `()`.
- **Surface.** There is no `Unit` name in the standard library today, so nothing user-facing is renamed.

This accepts strictly more programs than today: `{}` where `()` is expected now type-checks. The one program it
can reject is an overload set or a pair of impls that distinguished `()` from `{}`. The change is internal:
measured on the metel-core checkout on 2026-11-07, `Type::Unit`/`InferType::Unit` appears 32 times in 14
files, `Value::Unit` 44 times, and the grammar has `unit_type` and `unit_lit`. How the checker represents the
empty row is an ADR matter.

RFC-0221 relies on this: with one type, an empty brace group is the same value whether it is read as a block or
as a record.

## What this RFC does not cover

- **Homogeneous sequences.** `[T]` / arrays stay their own thing — a row is
  heterogeneous and fixed-arity by construction.
- **Abstracting over arity.** `(...Ts)` folding a type pack is RFC-0125; this RFC
  gives it a row to fold *into*, nothing more.
- **Labelled tuples / named-positional hybrids.** A row already does this
  (`{ 0: A, .name: B }`); no new surface syntax for it here.
- **Removing the `(…)` surface syntax.** It stays as sugar indefinitely.

## Representation and migration

The end state is that `Type::Tuple` / `InferType::Tuple` no longer exist —
everything is `Type::Record` / `InferType::Record` with integer-or-identifier
labels. Possible staging:

1. Extend the row label type to `int | ident` and teach the record machinery
   (construction, projection, patterns, `Copy`, display, unification) the numeric
   ordering.
2. Lower tuple syntax to record nodes in a desugaring pass; keep `Type::Tuple`
   internally as a thin alias that is *definitionally equal* to the matching
   numeric-label row (weak form — reduces churn, but two representations coexist).
3. Delete `Type::Tuple` and rewrite its call sites to the row form (strong form —
   the actual goal).

Move checking already treats tuple elements as struct-like fields (RFC-0071 §9a),
so `move_check` is close to free. The parser keeps the tuple productions; they
just emit record AST.

## Alternatives considered

### Keep tuples fully distinct (status quo)

Every structural-type feature carries a second column forever: RFC-0117 a second
narrowing case, RFC-0150 the tuple-residual open question, RFC-0125 a separate
pack-into-tuple calculus, RFC-0118 a separate bound target. Rejected — the
duplication compounds.

### Remove tuple syntax; write `{ 0 = a, 1 = b }`

Consolidates by deletion. Rejected — `(a, b)` for a pair or triple is a real
ergonomic win and its removal buys nothing the sugar-only approach does not.

### Tuples as structs with a synthetic brand (Rust's tuple structs)

Gives `(A, B)` a nominal identity. Rejected — a brand would stop `(A, B)` being
structurally interchangeable, which is the whole reason tuples are used for
ad-hoc returns and argument lists.

## Open Questions

1. ~~**`()` vs `Unit`** (§6).~~ **Resolved:** unify. `()` is the empty row `{}` and `Unit` is retired as a
   separate type.
2. **Mixed-label rows.** Are `{ 0: A, .name: B }` rows worth allowing at all, or
   should integer and identifier labels be mutually exclusive per row (tuples
   integer-only, records identifier-only, and a row is one or the other)? The
   latter is simpler to reason about and to print; the former is more uniform.
3. **Cross-shape row bounds.** Should `<record T: { 0: i64, .. }>` accept a
   hand-written `{ 0: i64, .name: … }`, and should a bound written for named data
   ever accidentally accept a tuple? Probably harmless given structural identity,
   but worth a decision.
4. **Staging** (§Representation). Weak alias first (step 2) then delete, or go
   straight to the row representation (step 3)? Depends on how many `Type::Tuple`
   match sites there are.
5. **Grammar ambiguity.** `(A, B)` in type position versus a parenthesised
   grouping, and interaction with turbofish and function-type syntax
   `(A) -> B` — confirm the existing tuple grammar's disambiguation survives
   unchanged when the node it builds is a record.
6. ~~**Compacting the remainder of a partial move** (§4a).~~ **Resolved:** the remainder keeps its labels and is a
   sparse row unless the moved elements were a suffix; getting a tuple back is a destructuring pattern or an explicit relabel,
   and no rule renumbers automatically.

## References

- RFC-0116 (Anonymous Record Types, `4-implemented`) — the row former tuples
  become an instance of
- RFC-0117 (Row Narrowing, `4-implemented`) — the narrowing rule tuples inherit
- RFC-0150 (Nested Row Narrowing) — its §3 tuple-residual open question is
  resolved by this RFC
- RFC-0118 (Row Bounds, `4-implemented`) — bound targets; Open Question 3
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — tuples stay
  brandless, like anonymous records
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) — §9a already tracks
  tuple elements as struct-like fields; `Copy` derivation
- RFC-0080 (Standard Aspects) — the `Ord` / `Eq` derivation §3 depends on
- RFC-0125 (Variadic Generics, v0.14.0) — folds a type pack into the row this
  RFC provides
- RFC-0061 §7.1 / metel-core#893 — `Callable<Args, Ret>` with `Args` a
  numeric-label row

---

## Decision

**Outcome:** *(pending — draft, opened 2026-08-29. The core desugaring is
straightforward; the open questions are whether
mixed-label rows are allowed, and the migration staging. Sequence before
RFC-0125, which depends on it.)*
**Target:** *(set when accepted; naturally lands with or just before v0.14.0's
variadic/row work.)*
