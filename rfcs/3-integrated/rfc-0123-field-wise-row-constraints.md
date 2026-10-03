---
id: rfc-0123
title: "Field-Wise Row Constraints"
date: '2026-07-24'
status: integrated
tracking: 'https://github.com/metel-lang/metel-core/issues/793'
updated: '2026-10-01'
coverage:
  "1": { spec: "spec.types.generics.field-wise-row-constraints.legality-1" }
  "2": { kind: untestable, reason: "Rationale for a primitive quantifier over comptime-derive-per-shape as an alternative; not an independent testable claim beyond legality-1's own rule." }
  "3": { kind: untestable, reason: "Prior-art survey (PureScript RowToList, Haskell row-types), not a testable claim of this RFC's own design." }
  "4": { spec: "spec.types.generics.field-wise-row-constraints.legality-1" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1302'
impl_status: in-progress
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

> **Status — under review (2026-09-27).** Committed to v0.14.0, tracking issue #793 filed
> 2026-08-22. RFC-0121 (Open Rows) reached `2-accepted` 2026-09-27, clearing this RFC's
> only blocker. All five open questions closed the same day — OQ1 (surface syntax) and OQ2
> (primitive vs. reified mechanism) ratified, OQ3 (heterogeneous fields), OQ4 (nested-record
> termination) and OQ5 (orphan-rule wording) resolved by inspection. See §1, §4, and Open
> Questions below.

> **Status — accepted (2026-09-27).** All five open questions closed 2026-09-27, reviewed once more before this transition with no issues found. Design settled per PROCESS.md's 2-accepted bar.

> **Status — integrated (2026-10-01).** Merged into `reference/spec/types.md#field-wise-row-constraints`: `where all R: Aspect` as a `WhereConstraint` alternative, holding when every field type in `R` satisfies `Aspect`. Not implemented yet (`LIMIT-TYPES-002`, `blocked`-exempt on metel-core#1302); additionally depends on RFC-0121's row-kinded generic parameters (`LIMIT-TYPES-001`), landing the same day. Closes `GAP-TYPES-004` (a blanket row-conditional impl's body needing a per-field aspect bound) together with RFC-0121. Cross-checked against RFC-0121 (satisfied — this RFC's `all R: Copy` is exactly what RFC-0121 §4/OQ1 names as the missing piece for abstract-row width subtyping) and RFC-0116/RFC-0120 (satisfied — the motivating `Display`/`Copy`-for-records use cases) — no contradiction found.

> **Status — integrated (2026-10-01).** Spec-rule pass: where all R: Aspect as a WhereConstraint alternative. Blocked-exempt on metel-core#1302 (not implemented); depends on RFC-0121's row-kinded generics. Closes GAP-TYPES-004 together with RFC-0121.

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
let p := { x = 1.0, y = 2.0 };
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
let a := { x = 1, y = 2 };
let b := a;        // a MOVES. Every record is affine, forever.
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

## 1. Shape of the constraint, syntax ratified 2026-09-27

`where all R: Aspect`:

```metel
extend<row R> { ..R }: Display  where all R: Display  { … }
fun consume<row R>(r: { ..R })  where all R: Copy     { … }
```

`all R: A` holds when every field type in `R` satisfies `A`. On an empty row it holds
vacuously.

**It is a constraint, not a bound on the row itself.** `R: { x: f64, .. }` constrains the
row's *shape* — which labels it has. `all R: Display` constrains the row's *contents* —
what the field types can do. The two compose and neither subsumes the other.

**Why this spelling over the alternatives (OQ1, resolved).** `where all R: Aspect` is the
cheapest extension of a channel that already carries two `WhereConstraint` alternatives —
the ordinary bound (`ident : BoundList`) and RFC-0121's row equation (`ident = Type`).
Adding `all R : BoundList` as a third costs exactly one keyword (`all`) and no new grammar
shape, the same cost RFC-0121 already paid for `row`. The alternatives considered and set
aside: `R: all Display` moves the keyword inside a bound-list entry for no compensating
clarity; a bound-position marker (`{ ..R }: Display` meaning "apply recursively") is
genuinely ambiguous with an ordinary row bound of the same shape; `AllFields<R, Display>`
invents a synthetic generic-looking construct that isn't an aspect, isn't a type, and
would need its own special-cased resolution rule. `WhereConstraint` gains:

```
WhereConstraint → RowEquation
                | "all" IDENTIFIER ":" BoundList
                | "record"? IDENTIFIER ":" BoundList
```

(Ordering matters only for parse-choice clarity, not semantics — `all` and `record` are
both keyword-led alternatives distinguishable from the lookahead token, unambiguous
against `RowEquation`'s `IDENTIFIER "="` and the bare `IDENTIFIER ":"` bound form.)

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

## 4. Mechanism: primitive, not reified (OQ2, resolved 2026-09-27)

Both known precedents (§3) implement `all`/`Forall` via row-to-list reification plus
ordinary instance induction — a real, working design, and worth weighing seriously before
picking a built-in instead of it. It is set aside here, not because it's wrong, but because
it solves a more general problem than this project currently has:

- **Every actual use needed is "apply one fixed aspect to every field," never
  user-programmable.** RFC-0121's width-subtyping rule needs `all R: Copy`; RFC-0116's
  `Display` gap needs `all R: Display`. Neither needs a user to write their own inductive
  instance over an arbitrary row — reification's whole value is letting users do exactly
  that, and nothing on this project's critical path asks for it.
- **Reification is a real forward dependency this project doesn't want yet.** A
  type-level list needs type-as-value machinery to reify a row into, which is RFC-0092
  (Comptime Core) — itself still `1-under-review`. Building `all` on top of it would chain
  this RFC's acceptance to comptime's, the same critical-path risk this cluster has
  repeatedly split RFCs apart to avoid (RFC-0121's own header makes the identical argument
  against pulling in more than the cluster needs).
- **A primitive rule is a small, self-contained typechecker addition.** `all R: A` checked
  as "for each field in `R`'s (finite — see Open Question 4) structure, check the field's
  type against `A`'s bound, short-circuiting on the first failure" is a direct structural
  recursion, no new kind, no reification, and no dependency beyond RFC-0121's row
  machinery, already accepted.

**Not a closed door.** If a real need for user-authored row induction shows up later —
the same "don't build it until it materializes" bar RFC-0090/RFC-0121 already hold
`<row R>` itself to — reification is the well-precedented way to get there, and nothing
about shipping `all` as a primitive now forecloses it; a later reified form can coexist
with (or, for the compiler's own internal uses, ideally paper over) `all`'s current
fixed-shape rule, similar to how RFC-0121 §3 lets row-conditional and phantom-parameter
typestate coexist rather than forcing one to subsume the other.

---

## Open Questions

1. ~~**Is `where all R: A` the right surface?** It reads well and reuses `where`, but `all`
   is a new keyword in a language that has been reluctant to spend them. Alternatives:
   `R: all Display`, a bound-position marker (`{ ..R }: Display`), or a named aspect
   (`AllFields<R, Display>`) — the last being closest to PureScript's constraint-class
   framing and requiring no keyword.~~
   **Resolved 2026-09-27 — see "Why this spelling over the alternatives" in §1 above.**
   `where all R: Aspect` ratified: the cheapest extension of `WhereConstraint`, which
   already carries the ordinary bound and RFC-0121's row equation; costs exactly one
   keyword, the same price RFC-0121 paid for `row`.
2. ~~**Is it primitive, or induction over a reified row?** PureScript and `row-types` both
   derive it from a row-to-list reification plus ordinary instance resolution. A built-in
   is simpler to specify and harder to generalise; the reified form is more expressive and
   drags in type-level lists.~~
   **Resolved 2026-09-27 — see §4 above.** Primitive: a direct structural recursion over
   the row's fields, no reification, no new kind, no dependency beyond RFC-0121's already-
   accepted row machinery. Every actual use on this project's critical path is a fixed
   single-aspect check, not user-programmable induction, so reification's extra generality
   isn't needed yet — and building on it now would create a forward dependency on RFC-0092
   (Comptime Core), still `1-under-review`. Not a closed door: a reified form remains
   available later if a real need for user-authored row induction shows up.
3. ~~**Does it need to be per-field rather than uniform?** `all R: Display` applies one
   aspect to every field. `Display` for a record needs exactly that. But a heterogeneous
   requirement — "field `x` is `Copy` and the rest are `Display`" — is expressible as
   decomposition (`R = { x: T, ..Rest } where T: Copy, all Rest: Display`), so probably not.
   Unverified.~~
   **Confirmed 2026-09-27, not merely "probably."** Any finite set of per-field exceptions
   chains via repeated decomposition — `where R = { x: T, ..R2 }, R2 = { y: U, ..Rest }`,
   each exception constrained individually and `all Rest: A` covering the remainder — so
   `all` itself never needs to be heterogeneous. §2's existing decomposition machinery
   (RFC-0121 §2) is exactly what makes this compositionally complete.
4. ~~**What does it mean for a record containing a record?** `all R: Display` on
   `{ inner: { a: i64 } }` requires `{ a: i64 }: Display`, which requires the very impl
   being defined. Whether that terminates or needs a coinductive rule is unexamined, and
   PureScript's answer should be checked rather than guessed.~~
   **Resolved 2026-09-27 — not coinductive.** An anonymous row type is written in finite
   source text and cannot be self-referential — Metel has no nominal recursion through
   anonymous records; only named types can recurse, and only through indirection (`&`,
   allocator handles), which resolves through ordinary nominal impl search, never through
   `all`'s own unfolding. `all R: Display` on `{ inner: { a: i64 } }` therefore terminates
   by plain structural induction on syntactic nesting depth, which is always finite.
   PureScript's induction-over-reification needing care there is about *that* mechanism
   working over nominally-recursive ADTs, not evidence this construct needs coinduction —
   it's the wrong precedent to import the concern from.
5. ~~**How does it interact with the orphan rule?** §1's motivating impl is a *stdlib* impl
   for a structural type, which is precisely what RFC-0116 §3 bans for non-local aspects.
   It is presumably fine because stdlib owns `Display`, but the rule as written keys on the
   *record* having no owner, not on the aspect — so the wording may need amending rather
   than merely being read charitably.~~
   **Resolved 2026-09-27 — no amendment needed, the premise was a misreading.** RFC-0116
   §3's aspect-impl rule is keyed on **aspect locality** ("Aspect impls, when the aspect
   is local to you" / banned "for a non-local aspect") — the "record has no owner" language
   is scoped to the separate *inherent-impl* ban a few lines below it, not to aspect impls
   at all. A stdlib impl of `Display`/`Copy` over `{ ..R }`, written inside the module that
   owns `Display`/`Copy`, is an ordinary "aspect local to you" case, no different from any
   other module implementing its own local aspect for a record. The actual blocker is
   metel-core#581 (structural impl targets — records, tuples, `T[]` alike — unimplemented
   generally), a pre-existing implementation gap unrelated to this RFC's design.

---

## Alternatives Considered

- **Comptime derive per shape (RFC-0093).** Generates an impl for each concrete record type
  used. Avoids the constraint entirely; does not help the *bound* case (§2), and depends on
  comptime (RFC-0092, RFC-0093), both `1-under-review` — stale as `0-draft` here since
  2026-08-23; corrected 2026-09-27.
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
- RFC-0092 (Comptime Core) — the type-as-value/reification machinery §4's primitive-vs-
  reified resolution deliberately avoids depending on for now
- RFC-0061 (Structural Aspect Bounds), RFC-0060 (Aspect Impl Coherence) — the coherence
  machinery a stdlib impl over all rows would have to satisfy
- `reports/substructural-types/structural-records.md` — the living report the cluster was
  extracted from

---

## Decision

**Outcome:** **Ready for acceptance, 2026-09-27.** No blocking open question remains: OQ1
(surface syntax, §1) and OQ2 (primitive vs. reified mechanism, §4) are ratified; OQ3
(heterogeneous fields), OQ4 (nested-record termination) and OQ5 (orphan-rule wording) are
resolved by inspection and need no design change. The sole prerequisite, RFC-0121, is
itself `2-accepted`. The only work left is the spec-rule pass (coverage frontmatter +
Legality Rule blocks for the `all R: Aspect` constraint form and its field-wise checking
rule) done at the `3-integrated` transition, as for RFC-0117 and RFC-0129.

**Target:** v0.14.0, via metel-core#793.
