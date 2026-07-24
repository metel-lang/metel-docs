---
id: rfc-0123
title: "Field-Wise Row Constraints"
date: '2026-07-24'
status: draft
target:
---

> **Opened 2026-07-24, unifying three questions the corpus was carrying separately without
> noticing they were the same one.** RFC-0121's open question 1 needs "every field in row
> `R` is `Copy`" before its width-subtyping rule can be stated. RFC-0116 needs "every field
> in row `R` is `Display`" before an anonymous record can be printed. And — found the same
> day while integrating RFC-0071 — **no record can be `Copy` at all**, which makes every
> record permanently affine. Three symptoms, one missing construct.
>
> **Depends on RFC-0121 (Open Rows)** — it quantifies over a row variable, so `<row R>`,
> `..R`, and row-conditional impls must exist first. Deliberately *not* folded into
> RFC-0121: that RFC is already carrying row variables, row algebra, typestate, and the
> width-subtyping problem, and this cluster's repeated lesson is that large RFCs accumulate
> contradictions faster than they get read.

## Summary

A constraint form that applies an aspect bound to **every field of a row** rather than to
the row's type as a whole:

```metel
extend<row R> { ..R }: Display where all R: Display { … }
```

Read: *this impl applies to any record all of whose fields are themselves `Display`.*

Without it, three things the records cluster already promises cannot be written: an
implementation of any standard-library aspect for anonymous records, `Copy` for a record of
copyable fields, and the rule that makes width subtyping sound.

---

## Motivation

### 1. Anonymous records cannot satisfy a stdlib aspect at all

RFC-0116 §3 permits an aspect implementation for a record **only when the aspect is local
to the implementing module** — the orphan rule, and correctly so: `{ x: f64, y: f64 }` has
no owning module, so two modules writing `extend { x: f64, y: f64 }: Display` would conflict
with no principled tiebreak.

Every standard-library aspect is non-local. The consequence, which RFC-0116 states the
restriction for but never draws:

```metel
let p = { x = 1.0, y = 2.0 };
println("${p}");                  // no `Display` for any record, ever
```

A single stdlib impl would fix it for all records at once, and cannot be written today
because it needs to require `Display` of each field:

```metel
extend<row R> { ..R }: Display where all R: Display { … }
```

### 2. The width-subtyping rule cannot be stated

RFC-0121 §4 proposes that width subtyping — silently accepting a wider record where a
narrower one is expected — is sound only when every silently-dropped field is `Copy`.
Its own open question 1 records that this cannot be written: *"No bound expressing 'every
field in row `R` is `Copy`' is defined anywhere."*

### 3. No record can be `Copy`, which is sharper than either

Found 2026-07-24 while cross-checking RFC-0071 for integration. `Copy` is **declared**, not
auto-derived — RFC-0096's auto-impl set is a closed list of exactly three (`Send`, `Sync`,
`Linear`) and `Copy` is not among them (RFC-0071 §2 declares it with `extend T: Copy;`).
Since RFC-0116 §3 bans non-local aspect impls for records, and `Copy` is standard-library:

```metel
let a = { x = 1, y = 2 };
let b = a;        // a MOVES. Every record is affine, forever.
```

`{ x: i64, y: i64 }` is exactly the shape a reader expects to copy freely, so this is a
harsher cliff than `Display`. It also **blocks RFC-0121's width-subtyping rule from ever
applying to a nested record**, since that rule requires each silently-dropped field to be
`Copy` and a record field can never be.

The fix is the same single stdlib impl shape:

```metel
extend<row R> { ..R }: Copy where all R: Copy { }
```

**These are the same missing construct**, and recognising that is most of this RFC's
justification. Solving it once resolves a soundness rule and a usability cliff that were
being tracked as unrelated problems in different documents.

---

## 1. Shape of the constraint

Provisional syntax, not settled — `where all R: Aspect`:

```metel
extend<row R> { ..R }: Display  where all R: Display  { … }
fun consume<row R>(r: { ..R })  where all R: Copy     { … }
```

`all R: A` holds when every field type in `R` satisfies `A`. On an empty row it holds
vacuously.

**It is a constraint, not a bound on the row itself.** `R: { x: f64, .. }` constrains the
row's *shape* — which labels it has. `all R: Display` constrains the row's *contents* —
what the field types can do. The two compose and neither subsumes the other.

## 2. Why this is not simply "derive it"

Comptime derive (RFC-0093) could generate a per-shape implementation instead of quantifying.
That is a real alternative and is recorded in Alternatives — but it produces one impl per
concrete record shape encountered, whereas this produces one impl covering all of them.
The difference matters for a *bound*: `fun f<row R>(r: { ..R }) where all R: Copy` is a
constraint checked at the call site, and there is nothing to derive there.

## 3. Prior art

**PureScript is the direct precedent.** It expresses exactly this via `RowToList`, which
reifies a row as a type-level list, plus instance induction over that list — a `Cons` case
requiring the head's constraint and recursing on the tail, and a `Nil` base case. Its
`Show`, `Eq` and `Encode` instances for records are all written this way, so the shape is
known to work in a production row-typed language.

**Haskell's `row-types`** takes the same approach under the name `Forall r c`, with a
`metamorph`-style fold over the row's fields.

Both suggest the mechanism is induction over a reified row rather than a primitive — worth
knowing before designing this as a built-in.

---

## Open Questions

1. **Is `where all R: A` the right surface?** It reads well and reuses `where`, but `all`
   is a new keyword in a language that has been reluctant to spend them. Alternatives:
   `R: all Display`, a bound-position marker (`{ ..R }: Display`), or a named aspect
   (`AllFields<R, Display>`) — the last being closest to PureScript's constraint-class
   framing and requiring no keyword.
2. **Is it primitive, or induction over a reified row?** PureScript and `row-types` both
   derive it from a row-to-list reification plus ordinary instance resolution. A built-in
   is simpler to specify and harder to generalise; the reified form is more expressive and
   drags in type-level lists.
3. **Does it need to be per-field rather than uniform?** `all R: Display` applies one
   aspect to every field. `Display` for a record needs exactly that. But a heterogeneous
   requirement — "field `x` is `Copy` and the rest are `Display`" — is expressible as
   decomposition (`R = { x: T, ..Rest } where T: Copy, all Rest: Display`), so probably not.
   Unverified.
4. **What does it mean for a record containing a record?** `all R: Display` on
   `{ inner: { a: i64 } }` requires `{ a: i64 }: Display`, which requires the very impl
   being defined. Whether that terminates or needs a coinductive rule is unexamined, and
   PureScript's answer should be checked rather than guessed.
5. **How does it interact with the orphan rule?** §1's motivating impl is a *stdlib* impl
   for a structural type, which is precisely what RFC-0116 §3 bans for non-local aspects.
   It is presumably fine because stdlib owns `Display`, but the rule as written keys on the
   *record* having no owner, not on the aspect — so the wording may need amending rather
   than merely being read charitably.

---

## Alternatives Considered

- **Comptime derive per shape (RFC-0093).** Generates an impl for each concrete record type
  used. Avoids the constraint entirely; does not help the *bound* case (§2), and depends on
  comptime, which is `0-draft`.
- **Compiler-builtin structural printing.** Make `println` know how to print a record
  without going through `Display` at all. Much the cheapest fix for §1's motivation, and it
  does nothing for §2's soundness rule — the two problems would stay separate, which is the
  situation this RFC exists to end.
- **Accept the gap.** Records are not `Display`; convert to a named record or struct to
  print one. Coherent, and honestly viable for a first release, but it leaves RFC-0121's
  width-subtyping rule unstatable regardless.

---

## References

- RFC-0121 (Open Rows) — the prerequisite, and the source of open question 1's `Copy` rule
- RFC-0116 (Anonymous Record Types) §3 — the orphan-rule restriction whose consequence
  motivates §1
- RFC-0093 (Derive Registration) — the comptime alternative
- RFC-0061 (Structural Aspect Bounds), RFC-0060 (Aspect Impl Coherence) — the coherence
  machinery a stdlib impl over all rows would have to satisfy
- `reports/substructural-types/structural-records.md` — the living report the cluster was
  extracted from

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
