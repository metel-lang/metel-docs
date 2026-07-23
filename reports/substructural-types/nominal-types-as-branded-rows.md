---
id: nominal-types-as-branded-rows
title: "Nominal Types as Branded Rows — A Structural-First Reconsideration"
type: report
status: active
last_synced_against_model: '2026-07-22'
supersedes: null
revives: null
---

# Nominal Types as Branded Rows

*Written 2026-07-22, out of a full audit of the records/views cluster
(`access-and-presence-rows.md`) that surfaced `HasField` as bolted onto nominal types
rather than derived from them, plus a chain of findings about `uses (…)` and RFC-0090's
own internal contradictions. This document asks a more radical question than that audit
did: what if every nominal type's canonical representation is `(brand, row)`, not just
tier-3's opt-in "named record"? It is a genuinely different thesis from
`access-and-presence-rows.md` and is kept separate deliberately, not merged into it —
that document argues within the current three-tier architecture; this one asks whether
the architecture itself should change underneath it.*

**Status: pressure-tested, not settled.** Several findings below are sharp enough that
the model's central promise — a single mechanism, invisible to ordinary code — is not
yet proven. Read this as the state of an argument in progress, not a proposal ready to
replace anything.

---

## 1. The intuition, stated plainly

Every nominal type — not just tier-3's opt-in "named record" — is represented as
`(brand, row)` under the hood. As long as a value has all its original fields, the
surface presents it exactly as an ordinary struct; nothing about writing or reading
`Handle` looks any different from today. When a field is moved out, the value's
*type* degrades to a narrower row of the same brand — `Handle` becomes `Handle.{ fd }`
— rather than becoming an opaque "partially moved" marker with no structural content.
Per-field multiplicity, on this view, is not a separate mechanism layered on top of
ordinary structs; it's what the existing representation already gives you, once the
representation itself is row-shaped by default. Ergonomic sugar is then a separate,
later question about how much of this stays invisible — not a justification for the
mechanism's existence.

---

## 2. What this responds to

`access-and-presence-rows.md`'s audit found that `HasField` as RFC-0090 §1 drafts it is
an **auto-derived aspect family checked externally** against an untouched `Type::Named`
struct — a fact *about* the type, computed by a separate mechanism, not a query against
the type's own structure. RFC-0090 §9 already sketches the alternative — "representing
every named type as `(row, brand)` internally... not elimination of the tag, but reuse of
it" — but §9 is the RFC's *last* substantive section, framed as a reconciliation against
an architecture (§1–§8) that assumes the opposite by default. This document asks what
happens if §9's move is taken as the foundation rather than an afterthought, **and pushes
it one step further than §9 itself does**: §9 is about sharing a representation for
*identity* purposes; nothing in it proposes that the row *degrades on partial move*. The
degradation is this document's own addition, not already present in RFC-0090.

---

## 3. What the model resolves immediately

### 3.1 `HasField` stops being bolted on

If every nominal type already carries a row, `HasField<"fd", i64>` (as RFC-0090 §1
drafts it — see §12 for why that syntax does not survive) is not a derived fact computed
by a second mechanism — it is the same row-membership query already used for anonymous
records and row-conditional impls. One representation, one query.

### 3.2 Presence and access collapse into one operation, not two roles of one mechanism

`access-and-presence-rows.md` §3.6 concluded "one row mechanism whose field types carry
the distinction" — presence and access as two *roles* of a shared solver. This model is a
cleaner unification than that: there is exactly **one operation, narrowing**, applied to
either an owned value (a partial move: `Handle` → `Handle.{ fd }`, fields are gone) or a
borrowed one (a view: `&mut Handle` → `record { fd: &mut i32 }`, fields are aliased
elsewhere). The distinction was never between two kinds of row — it was always about
whether the thing being narrowed is owned or borrowed, the same axis that already
distinguishes ordinary field access everywhere else in the language.

### 3.3 `uses (…)` stops needing a declaration

Once "which fields remain" is the value's actual, ordinary type, there is nothing left to
declare. The type checker already knows.

---

## 4. The sharp fork this surfaces: how does `Drop` dispatch?

Take `struct Handle { fd: i32, tag: u64 }` with a custom destructor tearing down `fd`.
Once `tag` is moved out, `self`'s type is `Handle.{ fd }`. When that value's scope ends,
does the custom `Drop::drop` fire?

**Reading (i) — `Drop` fires only against the exact original row** (brand *and* full
shape, not brand alone). A narrower residual reaching end-of-scope instead falls back to
ordinary recursive per-field drop. This reading has a concrete, serious hole:

```metel
struct Handle { fd: i32, tag: u64 }
impl Drop for Handle { fun drop(self) { close_fd(self.fd) } }

fun leak(h: Handle) {
    let t = h.tag;       // h narrows to Handle.{ fd }
}                        // h's scope ends here — reading (i): custom drop does NOT fire,
                         // fd (a bare i32, no Drop impl of its own) gets ordinary
                         // per-field drop, which does nothing. close_fd never runs.
```

**Reading (ii) — `Drop` is row-bounded, inferred from the body**, the same "accuracy
checking, not a declared-and-trusted annotation" discipline RFC-0109 §4.10 already
specifies for self-view narrowing. `drop`'s body reads `self.fd`, so its bound is
`{ fd: i32 }` (§12 — a bound is freestanding, no receiver, so it is bare); it fires on
*any* residual satisfying that bound, regardless of what else was moved out first. This
closes the leak, and it also beats plain decomposition (the earlier proposed fix for
`uses (…)`) specifically on this case: no wrapper type is needed, `fd` stays a direct
field of `Handle`, `{ fd: i32 }` stays satisfiable on `Handle` itself — the `HasField`-transparency gap
`access-and-presence-rows.md`'s audit found in the decomposition fix does not arise here.

**Revised 2026-07-23: the cost above is overstated.** Reading (ii) does not actually
require general `<row R>` open-generics machinery, ahead of RFC-0090 §3's deferred build
order or otherwise. Working through what it needs mechanically, rather than what it
sounds like it needs, resolves Open Question 3.

### 4.1 What reading (ii) needs is a fixed set, not a row variable

For one specific `Drop` impl, dispatch needs exactly two things: **a body-analysis pass,
computed once at compile time, producing a fixed, concrete required-field-set** — here,
`{fd}` — the same "accuracy checking" discipline RFC-0109 §4.10 already specifies for
self-view narrowing; and **a subset check**, at whatever point `drop` might fire, of
whether the value's current residual row contains that fixed set.

Neither is what RFC-0090 §3 defers. `<row R>` open generics are about a function written
*once* that stays polymorphic over an *a priori unknown* shape, with a real unification
variable threaded through every call site (`drain_field<row R, name, T>`). Drop's
required set isn't a variable — it is fixed, computed once per impl, never re-solved per
call. "Does this row contain `fd`" against a known, concrete target is exactly
`HasField`-as-a-bound-check, which §3.1 already needs regardless of `Drop` — dispatch
asks for nothing beyond machinery this document already posits elsewhere.

### 4.2 Generic structs and conditional bodies don't change this

`struct Container<T> { data: T, count: usize }` with a `Drop` impl touching only `data` —
the field *type* varies with `T`, but *which field* the body touches does not; the
analysis stays `{data}` at every instantiation, composing with ordinary monomorphization
rather than needing anything new. A body that branches (`if cond { self.fd } else {
self.tag }`) still produces one fixed set, conservatively the union over every branch —
still no path-sensitivity, still no variable.

### 4.3 The one place real complexity survives — and it is a different kind

RFC-0091 §1's own "not resolved" note: if `drop` calls a helper method, the required set
must compose *transitively* across that call. This is genuine, unavoidable work — a
whole-program, call-graph-level analysis, closer to effect inference than to ordinary
type-checking — but it still bottoms out in one fixed set per `Drop` impl; it is harder to
*compute*, not a different *kind* of mechanism. `access-and-presence-rows.md` §4 already
connects this exact transitivity gap to the effect system as the one access-row case that
does not desugar away — the same open thread, not a new one.

### 4.4 This is unrelated to §7's eligibility gate — stated explicitly to avoid confusion

§7.1's brand-scoped visibility answers a different question: whether *other, generic user
code* may query a type's row (`fun f<row R: HasField<...>>`). `Drop`'s dispatch is the
compiler checking *one type's own* impl against *its own* residual — internal bookkeeping,
not user-facing structural matching, and **not gated behind tier-3 opt-in**. Every struct
implementing `Drop`, tier-1 or tier-3, needs this analysis to avoid reading (i)'s leak;
consistent with `Drop` already receiving bespoke treatment elsewhere in the corpus
(RFC-0096 §4: "`Drop` is not a fourth instance of [the auto-impl] pattern"), so this is
not a new precedent.

---

## 5. The scope consequence: this reaches past the cluster under review

RFC-0071 §7 states its rule as a blanket ban: "A struct implementing `Drop` may not be
partially moved — the destructor requires access to the complete value." That rule is
written under the assumption that **no representation exists** for "which fields remain"
on a `Drop`-implementing type. Under this model, one always does. §7 is not narrowed by
an exception under this proposal (which is what RFC-0091 §1's `uses (…)` tried to do) —
it is **obsolete as stated** and needs rewriting at the source. That is a materially
bigger blast radius than "the four RFCs under review" — RFC-0071 has been `2-accepted`
since 2026-06-28.

---

## 6. Pressure test 1 — the sharpest problem found: widening reopens OQ10 as a general risk

RFC-0090's own worked example for constructor-invariant bypass:

```metel
struct SortedPair { small: i32, big: i32 }   // invariant: small <= big, enforced by SortedPair::new
```

Its **open question 10** asks whether `FromRecord` needs a guard against reconstructing a
`SortedPair` that violates this, since "auto-derived reconstruction can silently skip
validation a hand-written constructor enforces" — scoped, in the RFC's text, to that one
explicit conversion function.

If narrowing and widening are both fully automatic — a move narrows the type, a field
assignment widens it back, no conversion function involved anywhere — the same bypass is
reachable through nothing more than ordinary code:

```metel
fun mess_with_it(p: &mut SortedPair) {
    let old_small = p.small;   // move small out; p narrows to .{ big }
    p.small = 999_999;         // assign an arbitrary value back in; p widens to full SortedPair
    // no call to SortedPair::new, anywhere. invariant possibly broken.
}
```

**Precision about what's actually new here.** Plain mutable-field reassignment already
has this exact problem today, with zero row machinery involved — `p.small = 999_999`
bypasses `new` right now, in the current language, if the field is accessible. The model
does not create a hole from nothing. What it does is reveal that **OQ10 was mis-scoped
from the start** — RFC-0090 frames it as a risk specific to the `FromRecord` conversion
path, but it was always a general constructor-invariant problem, reachable via ordinary
field mutation. Taking narrow/widen fully seriously just makes that pre-existing
mis-scoping impossible to keep ignoring, since move-then-reassign is now *structurally
identical* to what `FromRecord` already does.

**The practical consequence:** whatever fixes OQ10 has to be a general answer about
mutable-field access on invariant-bearing types — banning automatic widening outright,
requiring it to re-run some validation, or something else not yet proposed here — not
something that can live inside one conversion function's design. This is left genuinely
open below; no answer was settled on while working through it.

---

## 7. Pressure test 2 — does universal `(brand, row)` reopen ambient structural matching?

RFC-0090 §8's whole argument for opt-in tiers: "Structural matching stays non-ambient —
the overwhelming majority of types never raise 'does this support drain/restore,
Lacks-typestate, or some absence-idiom' at all, because the answer is fixed once, by the
author, at the declaration or derive, never re-litigated per call site."

If **every** struct is always `(brand, row)`, and a row-conditional blanket impl exists
anywhere in the corpus (RFC-0061), every struct becomes structurally eligible to match it
— whether its author ever opted into structural exposure or not. That is the exact
TypeScript failure mode §8 exists to prevent, reintroduced at the level of coherence
rather than at the level of a type's own declared capability.

**Reconciliation, checked 2026-07-23:** separate *"has a row, for narrowing purposes"*
(universal — needed for move-tracking to work uniformly across every struct) from *"row
is visible to `HasField`/row-conditional-impl matching"* (stays opt-in, gated exactly the
way tier 3 gates it today). The representation can be uniform without the row being an
ambient input to coherence.

**The caveat this puts on §3.1's win.** The *mechanism* becomes uniform — one query,
checked the same way everywhere — but *eligibility* to be checked still needs a
deliberate gate. The opt-in does not disappear under this model; it moves from "does this
struct have a row at all" to "is this struct's row visible to structural matching." That
is a real, if smaller, concession against the model's promise of one unified mechanism
with nothing bolted on.

### 7.1 The sharper version of the question: does narrowing itself change eligibility?

Stating the reconciliation as a per-*struct* property leaves open what happens to a
specific narrowed residual, e.g. `Handle.{ fd }` after `tag` is moved out of an ordinary,
non-opted-in `Handle`. Does that residual inherit `Handle`'s "not visible" status, or does
producing a row-shaped value via narrowing itself grant visibility — since a residual
*structurally* looks like exactly the kind of value `HasField` checks are built to find?

**Answer: visibility is scoped to the brand, fixed at declaration time, and inherited
unchanged by every narrowing and every view under that brand.** `Handle.{ fd }`'s brand
is still `Handle`; if `Handle` never opted into tier-3, neither `Handle` nor any residual
or view produced from it is ever visible to structural matching, regardless of which
fields happen to remain. The row's *content* is irrelevant to the eligibility question —
only the brand's own, once-fixed declaration matters. This closes the gap precisely: a
genuinely-declared tier-3 record and an ordinary struct's narrowed residual are never
confusable, even if their rows happen to look identical, because their brands carry
independently-fixed eligibility.

### 7.2 This restates, rather than extends, RFC-0090's existing three tiers

No new category is needed — the split was already there, just not previously stated in
eligibility terms:

- **Tier 1 (ordinary struct):** brand not visible to matching. Narrowing it produces
  residuals under the *same* invisible brand; narrowing never changes eligibility.
- **Tier 2 (`ToRecord`/`FromRecord`):** the conversion **strips the brand entirely** —
  `.to_record()` produces a bare, brandless anonymous record, trivially eligible for
  `HasField` because there is no brand left to gate behind. This was always tier 2's
  mechanism; it just was not previously stated in these terms.
- **Tier 3 (named record):** brand visible to matching, by declaration.

### 7.3 A bonus this produces for RFC-0090 §9's still-open coherence question

§9 asks which wins when a value could match both a brand-keyed impl and a row-keyed
blanket impl. Under brand-scoped visibility, that ambiguity **can only arise for types
that opted into tier-3 in the first place** — a tier-1 struct's row is never visible to a
row-conditional impl at all, so there is nothing to arbitrate for the overwhelming
majority of types. A real narrowing of an open question, not just a side effect of this
one.

**One case left unchecked:** does `.to_record()` work on an *already-narrowed* residual —
`handle_narrowed.to_record()` after `tag` was already moved out — producing an
even-smaller anonymous record than the type's full declared row? Plausible, not worked
through; the seam between tier-2 conversion and universal narrowing is not examined
anywhere in this document or RFC-0090.

---

## 8. Passing residuals across function boundaries

A residual's whole purpose is often to cross a function boundary — "pass a partially
consumed struct to another method." Two different capabilities hide under that
description, and they get different treatment.

### 8.1 Two readings, only one of which needs anything from §7

- **Reading A — the receiving method's signature names a concrete residual shape**,
  e.g. `fun process(h: Handle.{ fd })`. The "check" happens entirely at compile time: the
  parameter type *is* the check. This is ordinary type-matching — the same kind that
  already governs passing an `i64` to something expecting `i64` — and needs nothing from
  `HasField` or coherence. **It is available to every struct, tier-1 or tier-3,
  unconditionally**; §7's brand-gating does not touch it.
- **Reading B — the receiving method is *generic* over which residual it gets**, e.g.
  `fun process<row R: { fd: i32 }>(h: Handle.{ R })` — bare in bound position, dotted
  in the projected parameter — bounding an abstract row
  variable rather than naming a fixed shape. This is exactly the reusable-helper case
  (`drain_field<row R, name, T>`) §7 gates behind tier-3, deliberately — an ordinary
  struct choosing to stay tier-1 is choosing not to be usable this way.

Most of what "pass a residual to a method" actually needs is Reading A, and it costs
nothing extra under this model.

### 8.2 Owned residuals need a stricter rule than borrowed ones

For a *view* (borrowed), passing a wider row where a narrower one is expected is always
safe — nothing is consumed, only the reference's promise about what it touches shrinks
(`access-and-presence-rows.md` §3.2). For an **owned** residual, the same move is exactly
RFC-0090 §7's width-subtyping hazard: passing `Handle.{ fd, tag }` where
`Handle.{ fd }` (owned) is expected means something has to happen to `tag`, and silently
discarding it is only sound if `tag` carries no drop obligation (the corrected form of
RFC-0090's guard, from `access-and-presence-rows.md` §3.3).

**Resolution: strict, no implicit truncation at the call boundary, ever.** A caller
holding `Handle.{ fd, tag }` who wants to call `process(h: Handle.{ fd })` must narrow
*itself* first, explicitly (`let t = h.tag;`), so that by the time the call happens its
own binding's type already matches exactly — the call performs no narrowing of its own.
This matches RFC-0090 §8's own stance for tier 2 ("no implicit coercion at call sites,
regardless of tier... would quietly [widen] without the type author having asked for
it") and RFC-0065's "elision is never a silent choice," applied one level down: narrowing
only ever happens through the caller's own ordinary moves, never as a side effect of
argument-passing. The full, un-narrowed `Handle` is not a special case under this rule —
it is simply the residual where nothing has been narrowed yet, and follows the same
"match exactly, or narrow yourself first" requirement as any other too-wide residual.

### 8.3 A future ergonomic utility: `.narrow()`

Requiring the caller to spell out every field being moved-and-discarded is real ceremony,
and a Rust-`.into()`-shaped utility is a plausible answer — **called `.narrow()` here,
provisionally.** The reason it does not reopen §8.2's hazard is a distinction worth
keeping precise: the danger was *implicit* coercion, invisible at a call site.
`.narrow()` is an ordinary, explicit method call, visible in the source, whose body does
exactly what strict narrowing already requires by hand — move each field not in the
target row into a discard binding and let it drop normally. Because the call is visible,
`.narrow()` does **not** need to be gated by droppability the way implicit truncation
would — it can handle `Drop`-bearing fields uniformly, since nothing is silently skipped,
only mechanically performed on the caller's behalf.

What it needs: the target row known from context (inferred from a `let` binding's or
parameter's declared type, the same way Rust's `Into` infers its target — and the same
open monomorphization-timing question this document's Open Question 4 already asks, now
with a second consumer), and a compile-time check that the target is an actual subset of
the source row.

**Naming left open, deliberately.** Borrowing `Into`'s name implies more machinery than
is confirmed to exist — Metel's `?`-operator already does `From`-based coercion for
*error* types (live since v0.4.0), but a general `Into`/`From` conversion aspect for
ordinary values is not confirmed. `.narrow()` may be closer kin to RFC-0090 §8's
`to_record`/`from_record` pattern — an explicit, named structural conversion, same shape,
just narrowing between two residuals of the *same* brand rather than converting to an
anonymous record. Not designed further here; recorded as a forward-looking sketch, not a
committed mechanism.

---

## 9. Flagged, not worked through — and one resolved

### 9.1 Enums stay out of scope

Consistent with RFC-0090 §6/§9's existing scoping (unambiguous now that this document has
its own §9) — this is a structs-only move. Worth stating explicitly in whatever
eventually gets written, rather than left to be assumed.

### 9.2 Generic structs — resolved 2026-07-23: no deferral needed

**Revised.** This was originally left as unresolved homework. Working through it the same
way §4.2 already did for `Drop`'s generic-struct case resolves it, by the same reasoning
applied to a sibling question.

**The load-bearing fact is the one §4.2 already established:** for `struct Container<T> {
data: T, count: usize }`, *which* field a piece of code touches never depends on `T` —
only the field's *type* does. The same split answers row-narrowing and `HasField`
bound-checking here.

**Row-narrowing needs nothing beyond what generic field access already has.** Narrowing
`Pair<T> { a: T, b: T }` via `let x = pair.a;` only needs to know *which labels* survive
— fixed the moment `Pair<T>` is declared, before any instantiation exists. The residual
type stays exactly as generic as `Pair<T>` itself (`Pair<T>.{ b }`, with `b: T`
unresolved). This is not a new capability: Pass 1/Pass 2 already track `pair.a`'s type
symbolically as `T` without waiting for monomorphization; narrowing only adds "this label
is now absent" to information already carried. **Deferred generic bodies
(`FunBody::Generic`/`TypedExpr::GenericClosure`) are about execution and codegen —
different instantiations may need different runtime representations — not about
type-*checking*, which already happens symbolically.**

**Bound-checking against a generic struct's row needs nothing new either.** Checking
whether `Pair<T>` satisfies `{ b: i64 }` means unifying `T` with `i64` — the same shape of
check already used for ordinary aspect bounds (`S: Display`) on a generic parameter. In
practice, by the time a `Pair<T>` *value* exists to check a bound against, `T` is normally
already concrete — a genuinely uninstantiated struct value cannot exist at runtime, only
generic *code* stays parametric. Where the bound is checked *inside* still-generic code,
that is ordinary symbolic type-variable unification, unchanged from what aspect-bound
checking already does.

**No hidden exception found, checked structurally rather than asserted.** Metel has no
mechanism where a generic parameter changes *which fields exist* — no variadic generics,
no field-set-parameterized structs anywhere in this corpus. Field sets are fixed at
declaration; only field types vary with instantiation. That structural fact is what makes
both narrowing and bound-checking monomorphization-independent with no exception located.

**Extends to `.narrow()` (§8.3), the second consumer this question named.** Its
target-row inference is "which labels," inferred from context — the same kind of
inference Metel already performs for type-argument inference from a `let` binding's
declared type. Same reasoning, same answer.

**One adjacent question this does *not* settle, kept separate rather than folded in:**
whether a generic struct's *brand* is tied to the declaration (`Pair`) regardless of
instantiation, or varies per instantiation. Assumed to be the former, matching how
nominal identity already works for generics elsewhere in the language — but this is not
what this question asked, and the assumption has not been checked against anything
written down. See Open Question 10.

---

## 10. The zero-cost claim: what rests on solid ground, and what doesn't

The model's appeal rests partly on "the surface does not care that it's actually a row."
For that to be true at the implementation level, not just the surface-syntax level, an
unnarrowed value's type would need to stay representationally identical to today's plain
`Type::Named` — row machinery activating only at an actual narrowing operation (a move,
or a projection), never for code that does neither. Breaking this into its parts, rather
than treating it as one claim, separates the pieces that already stand on something real
from the piece that turned out to rest on nothing.

**Revised 2026-07-23, after a real error while first working through this: an earlier
draft of this section claimed RFC-0071's partial-move tracking "is already implemented,
already fully static" as evidence the static-bookkeeping approach costs nothing — while,
a few paragraphs later in the same draft, repeating this document's own standing caveat
that "the interpreter still deep-clones values and has no borrow checker." Those two
statements directly contradict each other. Checked precisely: RFC-0071 is `2-accepted`,
not implemented — `REGISTRY.md` confirms the stage, and grepping the interpreter source
for partial-move tracking returns nothing. The correction below is kept visible rather
than smoothed into the text, because which claims survive it and which don't is the
substance of the answer.**

### 10.1 Two ways narrowing could be implemented, and which one is cost-free

- **Static** — the row is a type-checker fiction. A struct's memory layout never changes
  at runtime; narrowing only updates what the type checker believes is legal to touch. A
  moved-out field's memory sits inert until the whole value is eventually torn down by
  ordinary recursive per-field drop.
- **Dynamic** — the value actually carries a runtime discriminant recording which fields
  are present, checked at runtime.

Static bookkeeping is the cost-free option, matching how Rust's borrow checker already
works and matching what RFC-0071's own text specifies (a compile-time check, not a
runtime one). **This is a design argument, not a demonstrated one** — before the
correction above, this section claimed it as already-validated fact; it is not. It rests
on external precedent and on RFC-0071's stated design, and on nothing currently running
in Metel.

### 10.2 `Drop` dispatch resolving at compile time is conditional, not observed

§4.1 argued `Drop`'s row-bounded dispatch (reading ii) could resolve entirely at compile
time with zero runtime branches, because the type checker already knows the exact
residual type at every specific program point. That conclusion followed directly from
"Metel's ownership tracking is already fully static" — which is RFC-0071's *design*, not
its *status*. The conclusion still follows **if** RFC-0071 is built as specified, and
does not silently reintroduce runtime cost while being built — but it is contingent two
levels deep, not something to cite as already true.

### 10.3 What doesn't depend on RFC-0071, and stays on solid ground

**Views cost exactly what taking a reference already costs**, and this piece of the
argument does not need the correction above: `&`/`&mut` with auto-deref (RFC-0067a) is
genuinely implemented, confirmed earlier this session. A view is a small value holding
references to specific fields — the same cost as any struct containing reference fields,
which already exists in the shipped language, independent of anything in this document.

**The eligibility gate (§7) is a declaration-time flag, unaffected either way.** Whether a
struct's brand is visible to structural matching is a single fact fixed once, at
declaration (tier-1 vs. tier-3) — O(1) per declaration, never rechecked per call site,
and this has nothing to do with move-tracking or RFC-0071 at all.

### 10.4 One genuinely unchecked edge case

Dynamic dispatch through `dyn Aspect` (RFC-0008) could need a runtime row representation,
if a call site cannot statically know the concrete residual shape behind a trait object.
RFC-0008 is explicitly deferred with "no consumer yet" per this session's earlier
research, so this is not a live concern today — but it is the one case where even the
*static* design, once built, might not hold, and it deserves a note rather than silence.

### 10.5 What this means for the property as a whole

Not resolved — sharpened. The claim is contingent on a foundation (RFC-0071) that is
accepted as a design but does not exist as an implementation, so "zero cost" cannot be
validated by inspection the way OQ1–4 were; it can only be validated once that
foundation is actually built, and even then only by checking that the implementation
doesn't quietly reintroduce cost RFC-0071's own design says it shouldn't have. The two
pieces that don't depend on RFC-0071 (views, the eligibility gate) are the parts of this
claim currently on solid ground; the rest is a coherent design argument, not yet
evidence.

---

## 11. Status summary

| | Resolved by this model | Newly opened by this model | Flagged, unexamined |
|---|---|---|---|
| `HasField` bolted-on-ness | ✅ §3.1 | — | eligibility-gating caveat, §7 |
| presence/access split | ✅ §3.2 — one operation, not two roles | — | — |
| `uses (…)`'s declaration | ✅ §3.3 | `Drop` dispatch must become row-bounded (§4) | ✅ §4.1 — a fixed-set check, not `<row R>`; transitivity (§4.3) remains real work |
| `HasField`-transparency gap (from `access-and-presence-rows.md`) | ✅ §4, via reading (ii) | — | — |
| RFC-0071 §7 | — | needs rewriting, not narrowing (§5) | — |
| RFC-0090 OQ10 | ✅ fix in RFC-0114, incl. fallibility, via `Result<Self, Self::Error>` + RFC-0078 | reopened as a general risk first (§6), then resolved | RFC-0114's own OQ3 (default-derivation mechanism) |
| RFC-0090 §8's non-ambient guarantee | ✅ §7.1–7.3 — visibility scoped to brand, inherited by narrowing/views | at risk under universal rows, first pass (§7) | `.to_record()` on an already-narrowed residual, unexamined |
| passing owned residuals across calls | ✅ §8.2 — strict, no implicit truncation ever | reopens RFC-0090 §7's width-subtyping hazard, first pass | `.narrow()`'s mechanism/naming, sketched not designed (§8.3, OQ8) |
| enums | out of scope, unchanged | — | should be stated explicitly |
| generic structs | ✅ §9.2 — no deferral needed; field sets are declaration-fixed, only types vary | — | brand identity per instantiation, unchecked (OQ10) |
| zero-cost-for-ordinary-structs | ✅ views + eligibility gate, on real ground (§10.3) | — | narrowing/`Drop` dispatch rest on unbuilt RFC-0071 (§10.1–10.2); a prior draft wrongly claimed this as already validated |
| `HasField<"fd", i64>` bound syntax | ✅ §12 — replaced outright by bare `{ fd: i64 }` | `bound_head` grammar needs a new alternative; `Lacks` needs a type-position wildcard | neither piece of grammar work is written yet |

---

## 12. `HasField`/`Lacks` bound syntax: replaced outright by `{ … }`

**The premise, checked directly against `grammar.pest` rather than assumed: `HasField<"fd",
i64>` does not parse today.** `bound_arg = { assoc_binding | type_expr }`, and `type_expr`
has no string-literal alternative anywhere in its grammar. This is not new information —
RFC-0090 §1 and RFC-0096 §7 both already flagged it as an unresolved gap — but it means
what follows fills a hole nothing currently occupies, rather than migrating working
syntax.

**Decision: replace `HasField`/`Lacks` outright with the row syntax already settled in
`access-and-presence-rows.md` §3.5**, rather than keeping them as named sugar over it.
Keeping both would reintroduce exactly the "two spellings for one fact" problem this whole
session has been eliminating everywhere else. **Revised 2026-07-23, same day as written:**
§3.5 itself was revised to split the row-former on whether a receiver is present, and a
bound has none — so this uses **bare `{ … }`**, not `.{ … }`. Pressure-testing the dot in
this exact position is what surfaced that the receiver-based split was needed at all.

```metel
fun magnitude<T: { x: f64, y: f64 }>(p: T) -> f64 { ... }         // was: HasField<"x", f64> + HasField<"y", f64>
impl<row R: { x: f64 }> Display for record R { ... }               // RFC-0090 §4's row-conditional impls, same reuse
```

A bound *is* a row, spelled the same way a row is spelled everywhere else — no string
literal, no separate aspect-name concept. It also compacts multi-field bounds for free:
what is currently an ANDed chain of separate `HasField` instances becomes one bound
naming several labels at once.

**The grammar change this needs, precisely.** `bound_head = { type_path ~ (...)? }`
currently requires every bound to start from an identifier (`type_path`); a bare row is
not one, so `bound_head` needs a genuinely new alternative
(`bound_head = { type_path ~ (...)? | row_bound }`). Bound position has no receiver to
disambiguate from, so this alternative needs no dot — bound position parses neither
struct literals nor blocks, so a bare `{ … }` there collides with nothing, the same
finding §3.5 already established for every other freestanding position.

**`Lacks` is the harder half.** `Lacks<"tag">` asserts absence regardless of type — it
does not care what `tag` would be, only that no field by that name exists. Row-bound
negation, reusing the *existing* `bang?` already in `bound = { bang? ~ bound_head }`, gets
close: `T: !{ tag: _ }`. But this needs a type-position wildcard meaning "any type,"
which does not exist today — checked directly: `_` appears only inside `pattern`
(`Pattern::Wildcard`), nowhere in `type_expr`. A genuinely new, small addition, not a
reuse.

**Consequence beyond the bound-position gap.** This is not narrowly scoped to
`HasField<"fd", i64>` — it is the spelling for every `HasField`-shaped construct in the
corpus, including RFC-0090 §4's row-conditional-impl typestate examples
(`impl<row R: HasField<"x", f64>> Session<R> { ... }` becomes
`impl<row R: { x: f64 }> Session<R> { ... }`).

---

## Open Questions

1. ~~How does OQ10's reopened, general form get fixed?~~ **Resolved by delegation,
   2026-07-23, then resolved in substance the same day:**
   `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md`
   proposes a `Construct` aspect — `construct(row) -> Result<Self, Self::Error>` as the
   one path any value of a nominal type is produced through, whether fresh or
   reassembled after narrowing — with a separate, opt-in `ConstructUnchecked` escape
   hatch for code that already knows the invariant holds. Its own fallibility question
   (whether an automatically-firing `construct()` can support a genuinely *rejecting*
   invariant without an ordinary field assignment becoming able to fail) is answered
   there too, reusing two already-*implemented* RFC-0078 rules (uninhabited-variant
   exhaustiveness, inhabited-singleton coercion): `Self::Error = !` collapses to bare
   `Self` provably, and a real error type loses the automatic-firing sugar in exchange —
   one rule, not a special case invented for this. Kept as a struck-through entry rather
   than removed, per this corpus's convention.
2. ~~Is "has a row" vs. "row is visible to structural matching" a clean, implementable
   separation?~~ **Resolved 2026-07-23, §7.1–7.3:** visibility is scoped to the *brand*,
   fixed at declaration time, and inherited unchanged by every narrowing and view under
   it — a residual's row *content* never affects its eligibility, only its brand's
   once-fixed declaration does. Restates RFC-0090's existing three tiers rather than
   adding a fourth, and narrows §9's brand-vs-row coherence question to types that opted
   into tier-3 in the first place. One sub-question left open: whether `.to_record()` on
   an already-narrowed residual is examined anywhere (it isn't).
3. ~~Does `Drop`'s row-bounded dispatch actually require general `<row R>` machinery?~~
   **Resolved 2026-07-23, §4.1–4.4: no.** It needs a fixed, concrete required-field-set
   per impl, computed once from the body, plus an ordinary subset check against it — not
   a row *variable* unified per call site, which is what `<row R>` actually means. This
   composes with generic structs and conditional bodies without change (§4.2), and is
   unrelated to §7's eligibility gate (§4.4) — `Drop`'s dispatch is compiler-internal
   bookkeeping on every struct regardless of tier, not user-facing structural matching.
   The one genuine remaining complexity is transitivity through helper calls (§4.3,
   RFC-0091 §1's own unresolved note) — real, harder to compute, but not a different
   *kind* of mechanism, and already tracked as the same open thread
   `access-and-presence-rows.md` §4 connects to the effect system.
4. ~~Does row-narrowing/`HasField`-checking on generic structs need to defer to
   monomorphization time?~~ **Resolved 2026-07-23, §9.2: no.** Which fields exist is
   fixed at declaration, independent of the generic parameter — only field *types* vary,
   the same split §4.2 already established for `Drop`'s generic-struct case. Narrowing
   and bound-checking need nothing beyond the symbolic, pre-monomorphization type-checking
   generic field access and aspect bounds already get; deferred generic bodies are about
   execution and codegen, not type-checking. No exception found: Metel has no mechanism
   where a generic parameter changes which fields exist, only what type they hold. Also
   answers `.narrow()`'s (§8.3) target-row inference, the second consumer this question
   named.
5. **Does the zero-cost-for-ordinary-structs property actually hold at the implementation
   level?** **Sharpened, not resolved, 2026-07-23 (§10.1–10.5).** Two pieces stand on
   real ground independent of anything else: views cost exactly what reference-taking
   already costs (RFC-0067a, implemented), and the eligibility gate is a declaration-time
   flag (O(1), unrelated to move-tracking). The rest — static-vs-dynamic narrowing,
   `Drop`'s compile-time-only dispatch — is a coherent design argument resting on
   RFC-0071, which is `2-accepted`, **not implemented**: an earlier pass through this
   question wrongly cited RFC-0071's tracking as already-shipped evidence, contradicting
   this document's own standing caveat in the same breath. Corrected and left visible.
   Cannot be validated further until RFC-0071 is actually built.
6. **What is this document's precise relationship to RFC-0090 §9?** §9 proposes
   representation-sharing for identity purposes only; this document's degrade-on-move
   extension is not present in §9 at all. Is this an amendment to §9, or a distinct,
   further claim that should be argued on its own terms rather than presented as "§9,
   promoted"?
7. **Process question, not a design one:** if this line of argument survives further
   pressure-testing, does it become an RFC-0090 rewrite, an RFC-0071 amendment, a new
   draft RFC of its own, or does it wait until §1's open question is resolved before any
   of that is decided? Not addressed here.
8. **What is `.narrow()`, mechanically, and does it belong to an existing pattern or a new
   one?** (§8.3) Whether it extends RFC-0090 §8's `to_record`/`from_record` naming, needs
   a general `Into`/`From`-shaped conversion aspect that is not confirmed to exist yet, or
   is its own dedicated mechanism, is not decided — recorded only as a forward-looking
   sketch, not a committed design.
9. **Two pieces of grammar work for §12, neither written yet:** the new `bound_head`
   alternative that lets a bound start from a bare `{ … }` instead of only a `type_path`,
   and a type-position wildcard (`_`, meaning "any type") for `Lacks`'s replacement
   (`T: !{ tag: _ }`) — `_` exists only in `pattern` today, confirmed absent from
   `type_expr`. Whether this becomes an RFC-0090 amendment or its own small RFC is also
   not decided.
10. **Does a generic struct's brand vary per instantiation, or stay tied to the
    declaration regardless of `T`?** (§9.2) Assumed to be the latter, matching ordinary
    nominal identity elsewhere in the language, but this is a genuinely separate question
    from OQ4's resolution and has not been checked against anything written down.

---

## References

- `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md` —
  the answer to Open Question 1, split out 2026-07-23 and resolved the same day,
  including the fallibility question it initially carried forward unresolved
- `access-and-presence-rows.md` — the audit that found `HasField` bolted-on and worked
  through `uses (…)`'s reduction to existing mechanisms; this document responds to and
  extends that audit's findings, particularly §3 (views desugar to rows of borrows) and
  its finding that decomposition breaks `HasField` transparency
- `internal/rfcs/1-under-review/rfc-0090-structural-records.md` §1 (`HasField` as
  currently drafted), §3 (recommended build order, `<row R>` deferral), §8 (the
  non-ambient-structural-matching argument, the `SortedPair`/OQ10 example), §9 (the
  narrower, representation-sharing-only sketch this document extends)
- `internal/rfcs/1-under-review/rfc-0091-linear-records.md` §1/§1.1 — `uses (…)` and the
  `Handle`/`RcBox` motivating examples, resolved here without a declared field-usage
  mechanism
- `internal/rfcs/1-under-review/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  §4.10 — the "accuracy checking, not a declared-and-trusted annotation" discipline §4
  reuses for `Drop`'s row-bounded dispatch
- `internal/rfcs/2-accepted/rfc-0071-ownership-and-move-semantics.md` §7 — the blanket
  partial-move ban this proposal requires rewriting, not narrowing
