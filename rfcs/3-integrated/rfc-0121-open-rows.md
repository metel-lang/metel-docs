---
id: rfc-0121
title: "Open Rows"
date: '2026-07-24'
status: integrated
tracking: 'https://github.com/metel-lang/metel-core/issues/792'
updated: '2026-10-01'
coverage:
  "1": { spec: "spec.types.generics.open-rows.legality-1" }
  "2": { spec: "spec.types.generics.open-rows.legality-2" }
  "3": { spec: "spec.types.generics.row-conditional-impls.legality-1" }
  "4": { spec: "spec.types.generics.open-rows.legality-3" }
  "5": { kind: untestable, reason: "Grammar restated against the real generated grammar -- already stated as part of legality-1/legality-2's own rule text above, not an independent testable claim of its own." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1301'
impl_status: not-started
---

> **Extracted from RFC-0090 §2 (open half), §4 and §7 on 2026-07-24** (superseded; see
> RFC-0116's header for the split rationale). Depends on RFC-0118 (Row Bounds) and RFC-0120
> (Named Records).
>
> **This is the expensive half of the cluster, and RFC-0090's own build order said so:**
> *"`<row R>` open generics later, separately, only if a real duck-typing need
> materializes. This is where the actual cost lives — treat it as its own decision with its
> own timeline, not a prerequisite for step 1."* The split makes that literally true rather
> than an intention inside a document that had to be accepted whole.

> **Load-bearing for more than typestate, recorded 2026-07-24.** This RFC is easy to read
> as an optional convenience — RFC-0090 §3 called `<row R>` "later, separately, only if a
> real duck-typing need materializes," and its own header repeats that it is the expensive
> half. Three things turn out to depend on it, and none of them is duck typing:
>
> 1. **Records cannot satisfy any standard-library aspect without it.** RFC-0116 §3 bans
>    non-local aspect impls for records (correctly — a structural type has no owning module),
>    so `Display` for records requires one stdlib impl over all rows. That needs `<row R>`
>    *and* RFC-0123's field-wise constraints. Until then no record can be printed.
> 2. **Decomposition has no substitute.** RFC-0118's bounds are expressively a strict subset
>    of this RFC — every bound is writable as a row — but the reverse fails: `T` is atomic,
>    so `{ extra: i64, ..R }` and `where R = { token, ..Rest }` cannot be expressed with a
>    bounded type variable. `drain_field`, which RFC-0109 cites as the thing records give
>    that Rust's view types cannot, needs decomposition.
> 3. **The width-subtyping rule is unstatable without it** (open question 1, resolved
>    2026-09-27; the bound to *check* the concrete case's rule against remains RFC-0123).
>
> **Which reframes RFC-0118 honestly: it buys nothing in expressiveness, only implementation
> cost.** A row bound is a subset check against a concrete row; `..R` needs row unification.
> That is a real and large difference, and it is the whole justification for shipping bounds
> first — but it means bounds are the cheap path to a fraction of this RFC, not a peer
> feature.

> **Status — under review (2026-09-27).** Committed to v0.14.0, tracking issue #792 filed
> 2026-08-22. §3 gained a new normative rule 2026-08-25 (brand-keyed impls take priority
> over row-conditional ones), resolving the corpus-wide brand-vs-row coherence question
> carried since RFC-0090 OQ6. **All seven open questions are now closed** (resolved or
> explicitly descoped as non-blocking) as of 2026-09-27 — OQ1 (width subtyping, §4), OQ2
> (row-vs-row coherence, §3), OQ4 (phantom-vs-row-conditional typestate, §3) and OQ5
> (grammar, §5) are ratified rules; OQ3 (diagnostics) and OQ6 (label polymorphism) are
> descoped as non-blocking implementation follow-up and out-of-scope respectively; OQ7 was
> resolved 2026-08-25. Per `PROCESS.md`'s `2-accepted` bar ("no more open questions block
> it, alternatives have been weighed and one chosen"), this RFC now reads as
> acceptance-ready — transition is a separate, deliberate step, not implied by this note.

> **Status — accepted (2026-09-27).** All seven open questions closed 2026-09-27 (OQ1/OQ2/OQ4/OQ5 ratified, OQ3/OQ6 descoped non-blocking, OQ7 resolved 2026-08-25); design settled per PROCESS.md's 2-accepted bar.

> **Status — integrated (2026-10-01).** Merged into `reference/spec/types.md#open-rows` (row binder, `..R` use sites, row decomposition, width subtyping) and `#implementing-an-aspect-for-a-record` (row-conditional impl resolution against a value's *current* row, brand-vs-row priority, row-vs-row coherence). All five Legality Rules `blocked`-exempt on metel-core#1301 — `LIMIT-TYPES-001` records the grammar/elaborator gap. The abstract-row case of width subtyping stays additionally gated on RFC-0123's `all R: Copy` even once this RFC itself ships. `GAP-TYPES-004` (blanket row-conditional impl body needing a per-field aspect bound) is resolved the same day, once RFC-0123 supplied `all R: Aspect`. Cross-checked against RFC-0120 (`4-implemented`, satisfied — its row-bound-satisfaction claim is exactly what §"row-conditional-impls.legality-1" states) and RFC-0123 (`3-integrated` the same day, same cluster) — no contradiction found.

> **Status — integrated (2026-10-01).** Spec-rule pass: row binder, ..R use sites, row decomposition, row-conditional impl resolution against a value's current row, brand-vs-row priority, row-vs-row coherence, width-subtyping rule. Blocked-exempt on metel-core#1301 (row kind not implemented).

## Summary

Row-kinded generic parameters — `<row R>` at the binder, `..R` at every use — letting code
abstract over "the rest of a row" rather than naming a concrete shape. Adds a row equation
form in `where` clauses (`where R = { token: Token, ..Rest }`) which serves as row
*decomposition*, and row-conditional impls, which realize typestate directly in the row.

This is the only piece of the records cluster that introduces a **row kind** and
**row-unification** into the type system. Everything in RFC-0116 through RFC-0120 works over
concrete, closed rows.

---

## Motivation

RFC-0116's records are exact shapes and RFC-0118's bounds are predicates over a type. Neither
lets a function say "I take a record that has `x`, and I give you back whatever else it had."
Every generic helper over record shape — the reusable half of what Rust's view types set out
to solve — needs a name for the unknown remainder.

The typestate application is the more striking one: with a row-typed record, **the state *is*
the row**, and RFC-0036's conditional impl blocks generalize from aspect conditions to
row-shape conditions with no new dispatch mechanism.

---

## 1. `row` declares, `..` marks every use

```metel
fun get_x<row R>(p: { x: f64, ..R }) -> f64 { p.x }
```

A row variable is written `..R` **wherever it appears in a type** — `{ x: f64, ..R }`,
`Handle.{ ..R }`, `Session<..R>`. A bare identifier in type position is therefore always a
*type* variable, never a row.

**The binder keeps `row R`.** A declaration naming its own kind is ordinary (Rust's
`const N: usize` does exactly this, then uses bare `N`), and `<..R>` would read as splicing
into the parameter list rather than declaring.

**The forcing case was a genuine ambiguity, not a preference.** Inside projection braces a
bare identifier could be either a field label or a row variable — `Handle.{ fd }` projects a
field, `Handle.{ R }` a row — separated only by case convention, which would have made the
design depend on RFC-0101 (`0-draft`) to disambiguate.

`..` with no name is the anonymous form and is what makes a bound open (RFC-0118 §1); `..R`
is the same mechanism with the rest named.

## 2. Row algebra: extension is a literal, removal is a decomposition

**Extension needs no operator.** The new label goes in the row literal, exactly as PureScript
(`{ x :: Int | r }`), Koka (`<div|e>`) and OCaml (`< x : int; .. >`) all do it:

```metel
RequestBuilder<{ ..R, auth: String }>
```

**Removal has no literal form and gets a decomposition instead of a subtraction.** Name both
halves and state how they compose:

```metel
extend<row R, row Rest> Session<..R>
where R = { token: Token, ..Rest }
{
    fun authenticate(self) -> Session<..Rest> { ... }
}
```

`Rest` *is* `R` with `token` removed, because the equation says so. This follows PureScript's
`Prim.Row.Cons label typ tail row` — which means exactly `row = (label :: typ | tail)`, and
which types `Record.delete` by using it backwards — rather than Ur/Web's `--` operator.

Three things this buys beyond parsing: the equation **subsumes the bound** (it already
implies `R: { token: Token, .. }` and additionally names the remainder); `=` is the correct
separator because it *equates* two rows, matching `assoc_binding` (`Deref<Target = Node>`),
an equation already living in this channel; and **no label kind or label literal is
required**, unlike any operator-based design.

**The cost, and the condition to revisit.** It is verbose — every removal needs a second row
variable and a `where` clause. If row arithmetic ever appears in more than a handful of
places, an operator starts to look better. Weigh that against the one direct experiment:
**Elm shipped record extension and restriction and then withdrew both**, keeping only update
and open-row annotations, on complexity-versus-benefit grounds. (Recalled, not verified —
confirm before citing as precedent.)

## 3. Typestate via row-conditional impls

```metel
extend<row R, row Rest> Session<..R> where R = { token: Token, ..Rest } {
    fun authenticate(self) -> Session<..Rest> { ... }
}

extend<row R: !{ token }> Session<..R> {
    fun send_data(&self, bytes: Bytes) { ... }
}
```

`send_data` does not *exist* on a `Session` whose row still has `token` — not a runtime
precondition, an absent method. Calling it too early is the same class of error as calling a
method that was never defined.

**Where this is compelling:** protocol and session state machines, where each transition adds
or removes a marker field and the available API tracks it exactly; and builders in the dual
direction, where `.with_timeout()` requiring `R: !{ timeout: _ }` prevents setting the same
field twice at compile time.

**Phantom-parameter versus row-conditional typestate, resolved 2026-09-27 — both stay,
neither is canonical.** `brand-types.md` does typestate with a phantom type parameter —
`File<'b, Open>` — which is simpler and well-precedented. This RFC does not need to settle
which one wins, because they are not actually competing for the same job: nothing here
requires deprecating or subsuming the phantom form, and this RFC does not gain anything by
forcing exclusivity. The two differ in what they can express and what they cost, and that
difference is the selection rule:
- **Phantom-parameter typestate** stays the default — it's cheaper (no row kind, no row
  unification) and covers every case where the state is a closed, enumerable tag (`Open` /
  `Closed`) unrelated to the value's actual field shape.
- **Row-conditional typestate** (this RFC) is for the strictly narrower case where the
  state *is* the row shape itself — a field's presence or absence is both the state marker
  and a real structural fact about the value (RFC-0121's `Session` example: `token` isn't a
  phantom tag standing in for "authenticated," the field is literally present or absent).
  `drain_field`-style decomposition (§2) has no phantom-parameter equivalent at all, so
  for that one case row-conditional typestate isn't a stylistic choice, it's the only
  mechanism that can express it.

Nothing in this RFC's acceptance depends on ruling the other one out.

**Priority against brand-keyed impls, resolved 2026-08-25.** The moment this RFC lets an
impl be written against a row (`extend<row R: { x: f64, y: f64, .. }> T: Display`), it
creates the first real instance of a question the corpus has carried since RFC-0090 §9
without a written answer: an ordinary nominal impl (`extend Point: Display`) is keyed on
brand identity, this RFC's row-conditional impl is keyed on shape, and if a concrete value's
brand has an impl *and* its row matches a row-conditional impl of the same aspect, nothing
says which one resolution picks. Read literally, RFC-0060 §2's overlap rule — "two impls of
the same aspect conflict when there exists any concrete type instantiation that both would
cover" — is unconditional and carries no specificity exception for this pair: an
`extend Point: Display` sitting alongside a row-conditional `Display` impl whose row `Point`
satisfies would, taken at face value, be rejected outright as a `T0015` conflict the moment
both existed in the same crate. That is not what anyone building typestate or a `Display`
impl against a matching row expects, and it would make row-conditional impls unusable
alongside any nominal impl of the same aspect.

**The rule:** the brand-keyed impl wins. Resolution checks brand-exact dispatch first; a
match there is selected directly, without evaluating whether a row-conditional impl of the
same aspect also matches the value's row, and RFC-0060 §2's overlap check does not fire
between the two — the row-conditional impl simply never gets asked. This is a genuine new
carve-out to RFC-0060 §2, not a restatement of RFC-0060 §5 (Negative Impl Priority), which is
a narrower and unrelated rule about a negative impl versus a blanket positive impl of the
same aspect. The carve-out is scoped to exactly one shape — one brand-keyed impl versus one
row-conditional impl of the same aspect, for a value whose brand has the former — and leaves
RFC-0060 §2's ordinary concrete-vs-concrete and blanket-vs-blanket overlap detection
untouched.

**What the brand-priority rule does not resolve, and row-vs-row coherence, resolved
2026-09-27.** Two row-conditional impls of the same aspect are a separate question from
brand-vs-row priority above: whether they can both match the same row, and if so, whether
that's an error. **Rows are open** — extensible with arbitrarily many fields the impl's
condition never names — so satisfiability of two row conditions depends only on the field
names both conditions actually mention; nothing else can correlate them. That collapses
the check to a direct generalization of RFC-0060 §2's existing rule:

- Two row-conditional impls of the same aspect **do not conflict** if, for some field name
  both conditions mention, one requires it present and the other requires it absent, or
  both require it present with statically non-unifiable field types. Either way no concrete
  row can satisfy both — a field name maps to at most one type in any given row — so the
  pair is provably disjoint, exactly like `authenticate`/`send_data` above (`{ token, ..
  }` versus `!{ token }`, the same field, opposite polarity).
- **Otherwise they overlap**, and RFC-0060 §2 applies completely unmodified: reject as
  `T0015`, the same outcome two ordinary impls would get. Nothing about row-conditioning
  earns an exception here — only a direct presence/absence (or type) contradiction on a
  *shared* field name does.

This also answers the under-constrained-row-variable half directly: a generic body over an
unconstrained `<row R>` has no bound entailing either impl's condition, so **neither**
row-conditional method is visible inside it. That is not a new rule — it is RFC-0036's
existing conditional-impl visibility, which already denies a method when the caller's
bound doesn't entail the impl's condition, applied to a row-shaped condition instead of a
type-shaped one.

**Owning implementation issue:** metel-core#833, filed 2026-08-25 ahead of this RFC's own
acceptance so the decision has a tracked home rather than living only as RFC text. Gated on
this RFC reaching `2-accepted` (tracked by #792) — there is nothing to prioritize against
until row-conditional impls exist. #833's own scope note explicitly carved out row-vs-row
coherence as "Open Question 2, unresolved" — that carve-out is closed by this resolution;
#833 should be revisited to fold the field-name-disjointness check into its own scope
rather than treating it as still-open.

## 4. Costs, stated as costs

- **Row-kinded variables and row unification** are a genuinely new piece of the
  elaborator/inference system, not a small patch. This RFC is the only place in the cluster
  that needs them.
- **Width subtyping versus ownership — the genuinely novel problem, resolved 2026-09-27.**
  Row polymorphism's defining move (silently using a wider record where a narrower is
  expected, forgetting the extra fields) is harmless in garbage-collected OCaml, Elm and
  PureScript. None of them have affine or linear ownership, so none had to ask what
  happens when a forgotten field is not garbage. **The rule splits on whether the
  narrowing takes ownership:**
  - **Borrow position never has a drop obligation to violate.** `&{ x: f64, ..R }` (or
    `&mut`) over a wider record does not move the value — the extra fields stay owned
    exactly where they always were, `Copy` or not. Width subtyping through a reference is
    therefore always sound and needs no `Copy` restriction; this is the same reasoning
    RFC-0109 already applies to self-view narrowing, generalized from a fixed set of
    fields to an open row.
  - **By-value width subtyping is where the risk actually lives**, and here the RFC's
    original proposed rule is ratified as stated: sound only when every field silently
    widened away is `Copy`. A moved value with a non-`Copy` remainder has no owner left
    once the narrow-typed value is what's live — that field's drop obligation (or, for a
    linear field, its use-once obligation) would go unmet. A remainder with any non-`Copy`
    field is rejected outright and requires an explicit `where R = { .., ..Rest }`
    decomposition instead, which keeps `Rest` visible and owned.
  - Precedent: none directly on point (stated as a cost above, and still true — no
    row-polymorphic language in the corpus's survey combines this with affine/linear
    ownership), but the split itself is not novel in kind — it is the same borrow/move
    distinction RFC-0071 already draws everywhere else a value could be viewed instead of
    consumed. What is decided here is that width subtyping does not get an exemption from
    that distinction.
- **Monomorphization versus erasure.** Storage-transparent constructs elsewhere in this
  cluster monomorphize and erase at runtime. PureScript's row polymorphism typically
  compiles to runtime dictionary passing. A zero-cost row-polymorphic Metel would be its
  own implementation project.
- **Plain-record style over object style.** Metel's aspects already cover
  interface-with-methods polymorphism; an OCaml-object-style structural mechanism for the
  same job would be redundant.

## 5. Grammar, resolved 2026-09-27

Diffed against the actual generated grammar (`reference/spec/grammar.md`, current as of
this RFC's review — not the illustrative pest sketch OQ5 originally quoted from RFC-0090,
which predates and doesn't match the real production names below).

**Binder — `GenericParam` gains a `row` alternative,** parallel to the existing `record`
kind marker, carrying the same optional `BoundList` §1's `<row R: !{ token }>` needs:

```
GenericParam → "record"? IDENTIFIER ( ":" BoundList )?
             | "row" IDENTIFIER ( ":" BoundList )?
```

**Use site — a new `TypeArg` alternative carries `..R` (or anonymous `..`) into generic
argument position** (`Session<..R>`), replacing `TypeArgs`'s current `Type`-only list:

```
TypeArgs → TypeArg ( "," TypeArg )*
TypeArg  → Type
         | RowArg
RowArg   → ".." IDENTIFIER?
```

**Row body — `RecordType` and `RecordProjectionType` both gain a tail**, distinct from
`RowBound` (bound position, RFC-0118, already implemented and unchanged): this is *type*
position, e.g. `{ x: f64, ..R }` or `Handle.{ ..R }`.

```
RecordType           → "{" ( RecordTypeField ( "," RecordTypeField )*
                              ( "," RowTail )? | RowTail )? "}"
RecordProjectionType → TypePath ".{" ( IDENTIFIER ( "," IDENTIFIER )*
                              ( "," RowTail )? | RowTail ) "}"
RowTail              → ".." IDENTIFIER?
```

**`where` — `WhereConstraint` gains the `RowEquation` alternative** §2's decomposition
needs (`where R = { token: Token, ..Rest }`); `=` rather than `:=`, matching RFC-0136's
invariant (a one-shot type equation, not a kept binding — see PROCESS.md's acceptance-review
check on this point):

```
WhereConstraint → RowEquation
                | "record"? IDENTIFIER ":" BoundList
RowEquation     → IDENTIFIER "=" Type
```

**`..`/`..=` collision, checked against the real grammar, not just asserted.**
`RangeExpression → TermExpression ( ( "..=" | ".." ) TermExpression )?` requires a left
`TermExpression` before either range operator can appear — there is no prefix-`..` form in
expression position anywhere in the grammar — so `RowArg`/`RowTail`'s prefix `..` (type
position only) cannot collide with range syntax (expression position only) regardless of
context. Clean.

These are additive productions only; nothing existing changes shape, so no other RFC's
grammar citations need updating.

---

## Open Questions

1. ~~**The width-subtyping-requires-`Copy` rule is proposed with no precedent to verify
   it against, and not ratified.** Until it is, open records whose non-empty remainder is
   silently discarded should be rejected outright. *(From RFC-0090 OQ3.)*~~
   **Resolved 2026-09-27 — see "Width subtyping versus ownership" in §4 above.** The rule
   splits on borrow versus by-value: narrowing through a reference is always sound (no
   ownership transfer, nothing to drop); by-value narrowing is sound only when every
   silently-widened-away field is `Copy`, exactly as originally proposed, and is rejected
   outright otherwise in favor of an explicit `where R = { .., ..Rest }` decomposition.
   **The half of this that was "no bound expressing 'every field in row `R` is `Copy`' is
   defined anywhere" is still RFC-0123 (Field-Wise Row Constraints)**, needed identically
   by RFC-0116 for `Display`. This does not block *this* RFC's acceptance for the
   **concrete** case — when the narrowed value's row is fully known at the narrowing site,
   the checker can walk its fields and test each one structurally, no quantifier needed.
   It does still gate the **generic** case: a function generic over `<row R>` that
   narrows a `..R`-typed value by value, where `R` is abstract inside the body, has
   nothing to check the remainder's fields against without a bound at the binder —
   that bound is RFC-0123's `all R: Copy`-shaped quantifier, not yet accepted. Concretely:
   by-value narrowing of a concrete row can typecheck under this RFC alone; by-value
   narrowing of an abstract row stays rejected (unification has no fact to consult) until
   RFC-0123 lands and can be written as a bound on the binder.
2. ~~**Row-conditional impl coherence.** Extending RFC-0036/RFC-0060's conditional-impl
   checking to row-shape conditions — ensuring two impls, one gated on presence and one on
   absence, cannot both apply to an under-constrained row variable — is asserted tractable
   and not worked out. *(From RFC-0090 OQ4.)*~~
   **Resolved 2026-09-27 — see "What the brand-priority rule does not resolve, and
   row-vs-row coherence" in §3 above.** Two row-conditional impls of the same aspect
   conflict under RFC-0060 §2's existing rule unless some field name they both mention is
   required present by one and absent (or incompatibly typed) by the other, which proves
   them disjoint — rows being open means no other correlation is possible. An
   under-constrained `<row R>` simply has neither method visible, under RFC-0036's existing
   conditional-visibility rule, not a new one. Owning implementation issue metel-core#833
   should have its "Open Question 2, unresolved" carve-out updated to reflect this.
3. **Diagnostics — descoped from acceptance, not resolved.** "Method does not exist" is a
   much worse error than "method requires the row to contain `token`, but this session's
   row is `{ tcp_connected }`". The legible version is not automatic just because the
   mechanism works. *(From RFC-0090 §4.)* This is implementation quality, not a soundness
   or expressiveness question — nothing about the type system's design depends on the
   wording of a diagnostic — so it does not block `2-accepted`. Tracked as a follow-up
   implementation-quality item once row-conditional impls exist to generate diagnostics
   for.
4. ~~**Phantom-parameter versus row-conditional typestate — which is canonical, or do both
   stay, and for which cases?** Too early to decide. *(From RFC-0090 OQ5.)*~~
   **Resolved 2026-09-27 — see "Phantom-parameter versus row-conditional typestate" in
   §3 above.** Neither is canonical; both stay. Phantom-parameter typestate remains the
   default for closed, enumerable state tags; row-conditional typestate (this RFC) is for
   the narrower case where the state *is* the row shape, which is also the only mechanism
   that can express `drain_field`-style decomposition at all. This RFC's acceptance does
   not require deprecating or subsuming the phantom form.
5. ~~**Grammar work, none of it written.** `<..R>` must be accepted as a generic *argument*
   while `<row R>` remains the *parameter* form; a row body needs a `..`/`..R` tail
   alternative; `where_constraint` needs the `row_equation` alternative §2 requires
   (`where_constraint = { row_equation | ident ~ ":" ~ bound_list }`,
   `row_equation = { ident ~ "=" ~ type_expr }`). The `range_op = { "..=" | ".." }`
   collision was checked and is clean — `range_expr` requires a left operand, so no prefix
   `..` exists in expression position. Grammar reading, not a prototype. *(From RFC-0090
   OQ12.)*~~
   **Resolved 2026-09-27 — see §5 above.** Written against the actual generated grammar
   (`reference/spec/grammar.md`), not the illustrative pest-style sketch this open
   question originally quoted: `GenericParam` gains a `row` alternative, `TypeArgs` gains
   a `RowArg` alternative for `..R`/`..` at generic-argument position, `RecordType` and
   `RecordProjectionType` both gain a `RowTail`, and `WhereConstraint` gains a
   `RowEquation` alternative. The `..`/`..=` collision is confirmed clean against the real
   `RangeExpression` production, not just asserted.
6. **Label polymorphism — descoped, not blocking.** Being generic over *which label*, not
   just over the rest — `drain_field<row R, name, T>` — needs a label kind, a label
   literal, an index-by-label form, and rules for all three. §2's decomposition retires
   the need for a label *literal*, not for label *polymorphism*. Already out of scope for
   this RFC and tracked against the deferred RFC-0091, where the one construct needing it
   lives — restated here only to make explicit that this does not block `2-accepted`,
   since "not in scope" and "blocking" read the same at a glance otherwise.
7. ~~**Brand-versus-row impl coherence priority.** An ordinary `extend Point: Display` is
   brand-keyed; a row-conditional impl (§3) is row-keyed. If a value matches both, which
   wins? *(From RFC-0090 OQ6/§9; RFC-0118 OQ4 and RFC-0137 OQ4 are the same question seen
   from bound position and narrowing position respectively; RFC-0120 OQ2 restates it.)*~~
   **Resolved 2026-08-25 — see "Priority against brand-keyed impls" in §3 above.** The
   brand-keyed impl wins: brand-exact dispatch is checked first, and a match there
   short-circuits row-conditional resolution rather than conflicting with it under
   RFC-0060 §2. Row-vs-row coherence (open question 2 above) is unaffected and stays open.
   Owning implementation issue: metel-core#833.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §2 (open half), §3 step 2,
  §4 (typestate), §7 (costs) — the source
- RFC-0118 (Row Bounds) — the anonymous `..`, of which `..R` is the named form
- RFC-0120 (Named Records) — the tier that makes row-conditional impls resolvable at all
- RFC-0036 (Conditional Impl Blocks) — what §3's row-conditional impls generalize
- RFC-0060 (Aspect Impl Coherence), RFC-0061 (Structural Aspect Bounds) — the coherence
  checking OQ2 must extend; §3's "Priority against brand-keyed impls" is a new carve-out
  to RFC-0060 §2's overlap rule specifically, distinct from §5's unrelated negative-impl
  priority rule
- `reports/substructural-types/brand-types.md` — the phantom-parameter typestate
  alternative in §3 and OQ4
- `reports/substructural-types/access-and-presence-rows.md` §4 — Koka effect rows, and why
  effect rows and field rows are the same open-row shape
- `public/rfcs/5-superseded/rfc-0090-structural-records.md` OQ6/§9, RFC-0118 (Row Bounds,
  `4-implemented`) OQ4, RFC-0120 (Named Records) OQ2, RFC-0137 (Nominal Types as Branded
  Rows, `3-integrated`) OQ4 — the corpus-wide open item resolved in §3 above; each updated
  2026-08-25 to point back here

---

## Decision

**Outcome:** **Ready for acceptance, 2026-09-27.** No blocking open question remains: OQ1
(width subtyping, §4), OQ2 (row-vs-row coherence, §3), OQ4 (phantom-vs-row-conditional
typestate, §3), OQ5 (grammar, §5) and OQ7 (brand-vs-row priority, §3) are ratified rules;
OQ3 (diagnostics) and OQ6 (label polymorphism) are descoped as non-blocking
implementation follow-up and explicitly out-of-scope respectively. §5's grammar is
diffed against the real generated grammar, not an illustrative sketch. The only work left
is the spec-rule pass (coverage frontmatter + Legality Rule blocks for the `row` binder,
`..R` use sites, row decomposition, row-conditional impl resolution, and the
width-subtyping rule) done at the `3-integrated` transition, as for RFC-0117 and
RFC-0129.

**Target:** v0.14.0, via metel-core#792.
