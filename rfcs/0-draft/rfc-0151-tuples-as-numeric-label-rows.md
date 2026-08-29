---
id: rfc-0151
title: "Tuples as Numeric-Label Rows"
date: '2026-08-29'
status: draft
target:
---

> **Consolidation RFC.** Anonymous record types (RFC-0116) landed a general
> structural product former with a closed row. This RFC observes that a tuple is
> that former with numeric labels, and proposes making `(A, B)` *sugar* for the
> row `{ 0: A, 1: B }` rather than a parallel type with its own representation,
> its own narrowing story, its own branding question, and its own variadic
> spine. The surface syntax stays; the second type-former goes away.

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

A row may mix the two (`{ 0: A, name: B }`); it is legal and simply unusual.
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

- **Narrowing (RFC-0117)**: moving `t.1` out of `(A, B)` narrows `t` to
  `{ 0: A }` = `(A,)`. The `2^N` subset-lattice bound, the "residual is an
  ordinary value" property, and path-sensitivity all apply with no addition.
- **Nested narrowing (RFC-0150)**: a tuple-typed field's residual is a
  numeric-label row residual. RFC-0150 §3 (define tuple residuals or ban them)
  is **resolved** by this RFC — delete the open question, keep the recursion.
- **Row bounds (RFC-0118)**: `<record T: { 0: i64, .. }>` matches any row with an
  `i64` at label `0`, tuple or hand-written. Whether that cross-match is
  desirable is Open Question 3.
- **Branded rows (RFC-0137)**: a tuple is an *anonymous* row — no brand, never
  satisfies a nominal projection bound — exactly as an anonymous record does not.

### 5. Type display

The printer renders a row whose labels are exactly `0 .. N-1` with no gaps as
`(T₀, …, Tₙ)`, and any other row as `{ … }`. Round-trips: `(i64, String)` prints
as `(i64, String)`, `{ 0: i64, 1: String }` written by hand prints the same, and
`{ 0: i64, 2: String }` (a gap) prints as `{ 0: i64, 2: String }`.

### 6. `()` and the unit type

Two options, deliberately left open (Open Question 1):

- **Unify**: `()` becomes the empty row `{}`, and the primitive `Unit` type is
  retired. One fewer type; but every `-> ()` signature, every `()` literal, and
  the evaluator's unit value are touched.
- **Keep `Unit` primitive**: the `(…)` sugar covers arity `≥ 1` only; `()`
  stays the unit type as today. Smaller blast radius; leaves `{}` and `()` as two
  spellings of "no information" if `{}` is also inhabited.

This RFC leans toward **keep `Unit` primitive** for the first cut and revisit
unification separately.

## What this RFC does not cover

- **Homogeneous sequences.** `[T]` / arrays stay their own thing — a row is
  heterogeneous and fixed-arity by construction.
- **Abstracting over arity.** `(...Ts)` folding a type pack is RFC-0125; this RFC
  gives it a row to fold *into*, nothing more.
- **Labelled tuples / named-positional hybrids.** A row already does this
  (`{ 0: A, name: B }`); no new surface syntax for it here.
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

1. **`()` vs `Unit`** (§6). Unify to `{}` and retire the primitive, or keep
   `Unit` and desugar arity `≥ 1` only? Blast radius versus type-count.
2. **Mixed-label rows.** Are `{ 0: A, name: B }` rows worth allowing at all, or
   should integer and identifier labels be mutually exclusive per row (tuples
   integer-only, records identifier-only, and a row is one or the other)? The
   latter is simpler to reason about and to print; the former is more uniform.
3. **Cross-shape row bounds.** Should `<record T: { 0: i64, .. }>` accept a
   hand-written `{ 0: i64, name: … }`, and should a bound written for named data
   ever accidentally accept a tuple? Probably harmless given structural identity,
   but worth a decision.
4. **Staging** (§Representation). Weak alias first (step 2) then delete, or go
   straight to the row representation (step 3)? Depends on how many `Type::Tuple`
   match sites there are.
5. **Grammar ambiguity.** `(A, B)` in type position versus a parenthesised
   grouping, and interaction with turbofish and function-type syntax
   `(A) -> B` — confirm the existing tuple grammar's disambiguation survives
   unchanged when the node it builds is a record.

## References

- RFC-0116 (Anonymous Record Types, `4-implemented`) — the row former tuples
  become an instance of
- RFC-0117 (Row Narrowing, `3-integrated`) — the narrowing rule tuples inherit
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
straightforward; the open questions are `()`/`Unit` unification, whether
mixed-label rows are allowed, and the migration staging. Sequence before
RFC-0125, which depends on it.)*
**Target:** *(set when accepted; naturally lands with or just before v0.14.0's
variadic/row work.)*
