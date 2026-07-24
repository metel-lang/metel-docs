---
id: rfc-0090
title: "Structural Records — Rows and Tiers"
date: '2026-07-09'
status: under-review
target:
updated: '2026-07-24'
---

> **New RFC, split out 2026-07-09** from `reports/substructural-types/structural-records.md`
> (a living design report), as part of decomposing an oversized RFC-0012 into smaller,
> independently reviewable pieces. Scoped to the structural-typing/row foundation and
> the three-tier capability model specifically. Partial consumption's record-based
> extension (Option C) and the per-field-multiplicity worked examples move to RFC-0091
> (Linear Records), which depends on this RFC and RFC-0089. No dependency on comptime
> (RFC-0092/0093) — `ToRecord`/`FromRecord` are ordinary, hand-writable aspects; only the
> convenience of auto-deriving them depends on comptime, and that convenience is
> RFC-0093's concern, not this RFC's.
>
> **Revised 2026-07-10.** §8 amended: tier 2's conversion is bare/anonymous *except* for
> a fiat-linear source struct (RFC-0089 §2.1), whose `Linear` status a bare row can't
> represent (RFC-0089 §3.1). For that narrow case, the derived conversion carries the
> source's brand and the derive emits one explicit `impl Linear` against that specific
> branded shape — full mechanism and scope in RFC-0089 §3.1.
>
> **Revised 2026-07-23 — `HasField`/`Lacks` retired; bound position now a bare row.**
> `HasField<"name", T>` never actually parsed: `bound_arg` accepts only `assoc_binding`
> or `type_expr`, and `type_expr` has no string-literal alternative — the gap the
> 2026-07-11 note below already flagged, now fixed rather than left open. Replaced
> outright (no named-sugar layer kept) with the row-bound syntax settled in
> `reports/substructural-types/access-and-presence-rows.md` §3.5/§12 of
> `reports/substructural-types/nominal-types-as-branded-rows.md`: a bound is a bare row,
> `T: { x: f64 }` in place of `T: HasField<"x", f64>`, compacting an ANDed chain of
> `HasField` facts into one bound naming several labels at once. `Lacks<"tag">` becomes
> `!{ tag: _ }`, reusing the bound's existing `bang?` negation. This amendment is
> independent of that document's own central, still-exploratory thesis (whether every
> struct, not just tier-3, carries this row-and-brand representation) — folding back
> only the syntax fix, which is needed regardless of how that broader question resolves,
> not the wider claim. **Two pieces of grammar work remain unwritten** and are not
> resolved by this amendment: `bound_head`'s new alternative (a bound starting from a
> bare row instead of only a `type_path`), and a type-position wildcard `_` (`Lacks`'s
> `_` needs "any type," and `_` exists only in `pattern` today). Also folds back this
> RFC's own **open question 8** (tier-3's declaration syntax): resolved to
> `record X { ... }`, joining the `struct`/`enum`/`aspect` declaration family, per the
> same source. Open question 10 (`FromRecord` bypassing constructor invariants) has a
> proposed answer too, split out as its own RFC rather than folded in here — see
> `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md`.
>
> **Revised 2026-07-24 — the `record` keyword is dropped from anonymous records.** The
> anonymous type-former is now bare braces: `{ x: f64, y: f64 }` as a type, `{ x = 1.0,
> y = 2.0 }` as a value (the `=` per `reports/syntax/colon-classifies-equals-defines.md`,
> adopted the same day by RFC-0100 for keyword arguments and RFC-0114 for record values).
> This completes the adoption of `reports/substructural-types/access-and-presence-rows.md`
> §3.5, whose rule is that the row-former carries a prefix **only where there is a receiver
> to project from** — `Handle.{ fd }` keeps its dot; every freestanding position drops
> everything. The 2026-07-23 revision above had already taken the bound half of that rule
> (`T: { x: f64 }`); this takes the rest, so the corpus no longer spells one construct two
> ways depending on which position it appears in.
>
> **`record` survives as a declaration keyword only** — `record X { ... }` (tier 3, §8),
> alongside `struct`/`enum`/`aspect`. That is now the *only* thing the keyword does:
> mint a nominal type. Open question 8 is folded into §8's prose accordingly, rather than
> left flagged as inconsistent with it.
>
> **One real cost this creates, stated rather than glossed (new open question 13):** the
> `record` keyword was the only visible difference between a *closed* anonymous record
> type (`record { x: f64 }` — exactly these fields) and a *bound* (`{ x: f64 }` — at
> least these fields). Both are now spelled `{ x: f64 }`, and only grammatical position
> distinguishes them: after `:` in a `generic_param`/`where_constraint` it is an
> existential bound; after `:` in a `param`/`let` annotation it is an exact closed type.
> The parser can tell these apart — they are disjoint nonterminals — but a *reader* cannot
> tell from the braces alone, and §5's "a closed record is not a predicate" bullet was
> written on the assumption that the two spellings differed. That bullet is rewritten
> below.
>
> **What this amendment does not do: sweep the rest of the corpus.** The old spelling
> survives in RFC-0091 (~20 uses), RFC-0109 (7), RFC-0089 (5), and the design reports
> this RFC was extracted from — `structural-records.md` (57) most of all. Those are
> mechanical, but they are not this RFC's text and were left rather than swept silently.
> `reports/substructural-types/archive/` should keep the old spelling permanently, as a
> historical record. Also unchanged here, and separately stale: this RFC still uses
> pre-RFC-0098 spellings throughout (`&mut` for `&var`, `impl Aspect for Type` for
> `extend Type: Aspect`). Fixing those uniformly is a larger, unrelated pass; doing half
> of it inside this amendment would have left the RFC internally inconsistent, which is
> worse than uniformly stale.

> **Status — under review (2026-07-21).** Reviewing the records/views substrate cluster together, per OBJECTIVES.md Priority 1 (reordered 2026-07-22). The cluster's first deliverable is the record/row semantics themselves -- RFC-0090 SS3 step 1's closed `record` type-former plus `HasField` -- not the `ToRecord`/`FromRecord` conversions the blog names, which are tier 2 of RFC-0090 SS8 and convert into a type-former that must exist first. Thorough draft with a substantiated primary proposal; open questions remain, chiefly the RFC-0089/RFC-0090 dependency direction that Trigger 6 tracks.

## Summary

Adds structural typing to Metel without adopting a full row-kind system wholesale, via
two complementary, additive mechanisms — `HasField`/`Lacks`-style auto-derived
structural aspect bounds (flow-insensitive, for generic code matching "any struct with
these fields") and a closed `{ ... }` type-former (an anonymous, exact-shape
product type). Row capability is then split into three tiers of increasing commitment —
plain `struct` (unchanged), `derives ToRecord, FromRecord` (on-demand conversion, no
representation change), and a named `record` kind (permanent, intrinsic, the only tier
eligible for row-conditional impls) — so that structural capability is never ambient:
a type author opts into exactly the tier their use case needs, avoiding the "silent
nominal-identity collapse" failure mode structural typing is often criticized for
(TypeScript being the frequently-cited example).

---

## Motivation

Generic code often wants to accept "anything with a matching field," not a specific
nominal type — but Metel's aspect system, as it stands, requires an explicit `impl
Aspect for Type` for every capability, including this one. Without a structural
mechanism, every such case needs either a bespoke aspect per field-shape (unworkable at
scale) or falls back to requiring callers to wrap values in a common nominal type just
to satisfy a bound that was never really about identity.

---

## 1. Two complementary mechanisms, not one import

Rather than adopting OCaml/PureScript's row-kind system wholesale, this splits into two
pieces that each extend something Metel already has:

- **Bare-row bound syntax, auto-derived structural aspect bounds** — flow-
  *in*sensitive, for generic code that wants to work on "any struct with a matching
  field" regardless of nominal identity. This is the same problem GHC Haskell's
  `HasField "x" MyRecord Float` (auto-derived, no shared row-kind system needed) ships
  an answer to, but spelled as a bare row (`T: { x: f64 }`) rather than a named,
  string-literal-parameterized aspect — see the 2026-07-23 revision note above for why.
  Structurally still an extension of RFC-0080's auto-impl pattern: the *checking rule*
  (existential row-membership) is the same regardless of the surface name.

  > **Note (2026-07-11), resolved 2026-07-23 (see revision note above):** RFC-0096
  > (Auto-Impl Aspects) §7 already worked out that the *old* `HasField<"x", f64>` form
  > didn't fit RFC-0096 §2's recursive algorithm (existential satisfaction, not
  > universal) and that its string-literal bound-position syntax wasn't covered by the
  > grammar. The bare-row spelling sidesteps the second problem entirely — there is no
  > string literal to fail to parse — and does not change the first: row-membership
  > checking is still existential, still not RFC-0096 §2's algorithm, for the same
  > reason as before.
- **A closed `{ ... }` type-former** (§3) — an anonymous, exact-shape product
  type, usable in ordinary value positions. No keyword: the braces are the former (see
  the 2026-07-24 revision note).

Per-value, flow-sensitive tracking of which fields a specific binding has had consumed
is a different concern, handled by RFC-0091 (Linear Records) on top of RFC-0089's
multiplicity model — this RFC's row/`HasField` machinery supplies the vocabulary
(`HasField`, `Lacks`, row shrink/grow) that mechanism reuses, but does not itself track
consumption state.

---

## 2. `{ ... }` as a real type-former

Once the anonymous record exists as a type, it is a genuine product type, usable anywhere
an ordinary type is:

- **Closed by default.** `{ x = 1.0, y = 2.0 }` as a value is an exact, concrete
  product — no hidden extra fields. This matters specifically because of the tension in
  §6: an *open* record (accept "at least these fields") permits width subtyping, i.e.
  silently forgetting fields, which is exactly what non-`Copy` ownership exists to
  prevent. Closed-by-default sidesteps this for the common case.
- **As a bound, a bare row directly — not sugar over a named aspect anymore.**
  `T: { x: f64, y: f64 }` in **bound** position means "anything satisfying both fields,"
  one bound naming several labels rather than an ANDed chain of separate per-field
  facts (see the 2026-07-23 revision note above). *(Corrected 2026-07-24: this bullet
  previously said "in a parameter position", which the keyword drop made wrong — braces
  in `param` position are the closed type of the bullet above, not this bound.)* Combined with §1's auto-derivation,
  **any existing nominal struct with matching fields satisfies it with no explicit
  opt-in** — Go's implicit
  interface satisfaction (a type satisfies an interface by having matching methods,
  with no `implements` declaration) is the closer real-world precedent here than
  OCaml, since it's the same "structural match, no declared relationship" story without
  OCaml's object/method-dispatch baggage, which would be redundant with Metel's
  existing aspects anyway.

  > **Position, not spelling, now carries the closed/open distinction (2026-07-24).**
  > `{ x: f64 }` after `:` in a `generic_param` or `where_constraint` is this existential
  > bound — "at least these fields." The identical text after `:` in a `param` or `let`
  > annotation is the *closed* type of the bullet above — "exactly these fields." Dropping
  > the `record` keyword is what merged the two spellings; the grammar keeps them apart
  > (disjoint nonterminals), a reader has only position to go on. See open question 13.
- **Open generalization reuses the existing channel pattern.** If genuine row
  polymorphism is wanted later — "at least these fields, generic over the rest" — that
  is exactly the shape of `<&r>` and `<@a>`: an explicit compile-time parameter in the
  `<>` channel. Proposed form: `<row R>`, e.g. `fun get_x<row R>(p: { x: f64,
  ..R }) -> f64`. Consistent with the pattern this cluster already uses everywhere —
  open/generic behavior is an explicit declared parameter; concrete use stays closed.

---

## 3. Recommended build order

1. **Closed `{ ... }` record types + bare-row bound auto-derivation first.** No row-kind, no
   row-unification algorithm — a closed record over *N* fields is a product type with a
   compiler-synthesized identity; the space of "which subset remains" is bounded by
   2^*N*, trivial for realistic struct sizes.
2. **`<row R>` open generics later, separately, only if a real duck-typing need
   materializes.** This is where the actual cost lives (§7) — treat it as its own
   decision with its own timeline, not a prerequisite for step 1.

---

## 4. Typestate via row-conditional impls

If step 2 of §3 is ever pursued, it enables **typestate**, realized directly by the row
rather than by a hand-rolled phantom marker. With a row-typed record, the state *is* the
row, and RFC-0036's conditional impl blocks generalize directly from aspect conditions
to row-shape conditions:

```metel
impl<row R: { token: Token }> Session<R> {
    fun authenticate(self) -> Session<R without "token"> { ... }
}

impl<row R: !{ token: _ }> Session<R> {
    fun send_data(&self, bytes: Bytes) { ... }
}
```

`send_data` does not exist on a `Session` whose row still has `token` — not a runtime
precondition, an absent method. Calling it too early is the same class of error as
calling a method that was never defined.

**This is one of (at least) two competing typestate encodings, not the only one — and
which is canonical is not yet decided.** `brand-types.md` does typestate via a phantom
type parameter — `File<'b, Open>` — the conventional approach, simpler, already
well-precedented (Rust idiom). Row-conditional impls are more novel and tie into the
larger structural-records vision. One consideration for whenever this *is* decided:
making row-conditional the canonical path would pull open-row generics, row-conditional
coherence, and the width-subtyping rule (§7) onto the critical path, which the build
order deliberately avoids — a point in the brand form's favor, but not treated as
decisive.

**Where row-conditional typestate is compelling, concretely:**

- **Protocol/session state machines** — handshake steps, auth flows, parser
  progress — where each transition adds or removes a marker field and the available
  API tracks it exactly.
- **Builders, in the dual direction.** Consumption removes a field from a row;
  building one up adds one. A config builder where `.with_timeout()` requires
  `R: !{ timeout: _ }` and returns `R + "timeout"` prevents setting the same field
  twice, at compile time.

**What it costs, beyond §7's general row-polymorphism costs:**

- **Coherence has to grow, not just get reused.** RFC-0036/RFC-0060's conditional-impl
  coherence checking would need extending to row-shape conditions specifically,
  ensuring two conditional impls (one gated `HasField`, one gated `Lacks`) can't both
  apply to some under-constrained row-variable case.
- **Diagnostics need their own care.** "Method does not exist" is a worse error than
  "method requires row to contain `authenticated`, but this session's row is
  `{tcp_connected}`" — getting the legible version is not automatic just because the
  mechanism works.

This is not part of the recommended build order in §3 — it is a reason step 2 might
eventually earn its cost, not an argument for taking on that cost now.

---

## 5. Where records are — and aren't — usable

**Usable, no special treatment needed:**

- **Ordinary value positions** — parameters, returns, `let` bindings, struct/enum
  fields.
- **Allocator-tagged and borrowed positions** — `@a { x: f64, y: f64 }`, `&r
  { x: f64, y: f64 }`. A record is an ordinary owned value; it participates in
  `@a T` / `&r T` exactly like a struct.
- **Pattern matching.**
- **Generic instantiation.**
- **Aspect impls, if the aspect is local to you** — reusing RFC-0061's orphan-rule
  treatment of `T[]`/tuples/function types directly.
- **Auto-derived aspects** — `Send`, `Sync` extend to records via the same
  field-composition rule already used for structs; `Linear` (RFC-0089) does too.
- **Open records whose row variable is only ever passed through, never inspected.**

**Not usable, and why:**

- **Inherent impls.** Records have no nominal owner for orphan-rule purposes, so two
  unrelated modules could write conflicting inherent methods for the same shape with no
  principled way to say which wins.
- **Aspect impls for a non-local aspect** — banned the other direction of the same
  rule.
- **Custom `Drop` logic, specifically.** `Drop` is a stdlib aspect, never local to
  ordinary user code, so no record can ever carry custom teardown logic — only nominal
  structs can.
- **Serving as an allocator type.** RFC-0063 §2's disjointness story depends on
  allocator identity being per-*instance*, while a record's entire premise is that two
  values with the same row are interchangeable — a category mismatch, not a coherence
  technicality.
- **Reading a closed record type as if it were a bound, or vice versa.** *(Rewritten
  2026-07-24 — this bullet previously leaned on a spelling difference that no longer
  exists.)* A closed record type names a concrete shape; a bound is a predicate. They
  remain **semantically distinct** — a closed `{ x: f64 }` is satisfied only by a value
  with exactly that row, a bound `{ x: f64 }` by any type carrying at least that field.
  What changed is that both are now written `{ x: f64 }`, so the distinction is carried
  entirely by **which position the braces appear in**, not by a keyword. Concretely: a
  closed record type still cannot be used *as* a predicate, and a bound still cannot be
  used *as* a type — but a reader who mistakes one position for the other gets no
  syntactic warning, where `record { ... }` used to give one. This is the cost recorded in
  open question 13, not a claim that the two have merged.
- **Open records where a non-empty row-variable remainder is silently discarded,
  without a guarantee everything in it is `Copy`** — a silent leak or soundness hole if
  the remainder contains a `Linear` or `Drop`-bearing field (§7's width-subtyping
  tension). No bound expressing "every field in `R` is `Copy`" is proposed anywhere
  yet, so this pattern should be rejected outright for now.

---

## 6. Considered and declined: a fully record-based type system

Whether records should stop being an *addition* alongside nominal structs and become
the *foundation* everything else reduces to — nominal types as pure sugar over an
underlying record. Considered and declined:

- **Enums don't fit.** Records are products; enums are sums. A records-only foundation
  has nothing to say about sum types on its own — it would need a *separate*
  structural mechanism ("variant rows") with a well-known cost: materially weaker
  exhaustiveness checking, since the compiler can't always know the full set of
  possible tags for an open variant. Metel's enum system leans on closed-world
  exhaustiveness as a real, hard-won property; trading it away for structural
  uniformity would be a regression.
- **Primitives don't fit either.** `i64` as "a one-field record" is indirection with no
  payoff.
- **Nominal identity can't actually become sugar — it's load-bearing.** §5 already
  establishes records can't be allocators and can't carry inherent impls or non-local
  aspect impls. If "structs are sugar over records," the sugar has to reintroduce a
  real, separate identity/ownership tag for any of that to keep working — at which
  point the reframing hasn't reduced what the system has to track, only renamed the
  part that was never really sugar.
- **Implementation cost for the common case.** Routing every ordinary struct through
  row-unification machinery means the 99% of code that never writes an anonymous
  `{ ... }` or a row bound pays for machinery it never asked for.

**Verdict:** records as the natural representation for structural, identity-free data —
yes. Records as the universal foundation — no.

---

## 7. Consequences and costs, if the fuller version is pursued

- **Row-kinded type variables and row unification** — a genuinely new piece of the
  elaborator/type-inference system, not a small patch, and only needed for step 2 of
  §3.
- **Object-style (OCaml) vs. plain-record-style (Elm/PureScript) — recommend plain
  records.** Metel's aspects already cover interface-with-methods polymorphism; adding
  a second, structural mechanism for the same job would be redundant.
- **Width subtyping vs. affine/linear ownership — the genuinely novel problem.** Row
  polymorphism's defining move (silently using a wider record where a narrower one is
  expected, forgetting the extra fields) is harmless in garbage-collected OCaml, Elm,
  and PureScript. None of them have affine/linear ownership, so none had to ask what
  happens when a forgotten field isn't garbage. Proposed rule: width subtyping is only
  sound when every silently-dropped field is `Copy`; anything `Drop`- or
  `Linear`-bearing forces explicit handling. Not decided; this is the one piece with no
  precedent to lean on at all.
- **Monomorphization vs. erasure.** Storage-transparent constructs elsewhere in this
  cluster monomorphize at compile time, erased at runtime. PureScript's row
  polymorphism typically compiles via runtime dictionary-passing. A zero-cost
  row-polymorphic feature for Metel would be its own implementation project.
- **Implicit structural satisfaction is a real departure from how the rest of the
  aspect system works.** Every other aspect requires an explicit `impl Aspect for
  Type`. Go's implicit interfaces draw exactly this criticism.

  **Resolved by the tier system (§8) — narrower than a blanket accept-or-require-opt-in
  choice.** `HasField`/`Lacks` as a *bound* stays implicit — a struct satisfies a
  field-shape bound just by having the right fields, no opt-in required, because a
  bound alone grants no new capability *over the type itself*; it only lets a generic
  function accept it. What the tier system gates is capability that changes what the
  type can do on its own: row-conditional impls, `to_record`/`from_record` conversion,
  and per-field multiplicity tracking all require an explicit tier-2/tier-3 opt-in.

---

## 8. Resolution: three tiers of row capability, not one mechanism

`struct` and the row machinery this RFC specifies do not merge into one representation
applied to every struct. Row capability comes in three tiers of increasing commitment,
each answering a genuinely different question, and a type author opts into exactly the
tier their use case needs.

**Tier 1 — plain `struct`, unchanged.** Whole-value semantics only: one multiplicity
for the entire value, moved or dropped as a single unit, no partial consumption, no
`Lacks`/row-conditional typestate applicable to it. Nothing about the core
`Type::Named` representation or the ordinary struct typechecking path needs to change,
ever, to support anything else in this RFC. This stays the default.

**Tier 2 — `derives ToRecord, FromRecord`: on-demand, explicit, no impl or coherence
exposure.** A struct stays a `struct` — no representation change, no row-conditional
impls become legal against it, no `HasField`/`Lacks` bound is ever satisfied by it
implicitly — but gains two derivable conversions:

```metel
@derive(ToRecord, FromRecord)
struct Handle { fd: i32, alloc: @a Buffer }

let h: Handle = ...;
let r = h.to_record();        // { fd: i32, alloc: @a Buffer } — same bits, new static type
let h2 = Handle::from_record(r);
```

Both directions are zero-cost — a relabeling of the same bits, not a real conversion —
but the two aspects are kept **separate, not merged into one**, because the two
directions carry different soundness weight. Consider a type with a constructor-checked
invariant:

```metel
struct SortedPair { small: i32, big: i32 }   // invariant: small <= big, enforced by SortedPair::new
```

`ToRecord` here is always safe — reading fields out can't violate anything.
Auto-deriving `FromRecord` would synthesize a reconstruction that packs whatever
`small`/`big` a record holds straight back into a `SortedPair`, silently bypassing
`new`'s check. So a type like this derives `ToRecord` alone, and either hand-writes
`FromRecord` with the check re-added or declines it entirely, forcing reconstruction
through the real constructor. This mirrors a decision the ecosystem has already made
and kept for the same reason — serde's `Serialize`/`Deserialize` are separate traits,
commonly derived together but not merged, because "safe to read out" and "safe to
construct from arbitrary input" are different risk profiles in practice. A bundled
`Record` shorthand expanding to both was considered and declined for the same reason
this cluster has repeatedly avoided a second spelling for the same action.

Whether these conversions are auto-*derivable* at all (versus always hand-written)
depends on RFC-0093's comptime derive mechanism — this RFC only requires that
`ToRecord`/`FromRecord` exist as ordinary, hand-writable aspects with these signatures;
the `@derive(...)` convenience is additive, specified in RFC-0093, not a prerequisite
for tier 2 to have value.

**`to_record_mut`/`from_record_mut` extend tier 2 to the borrowed case.** The by-value
pair alone only covers "consume the whole struct, get a whole record, maybe build a new
struct later." It does not cover "keep using `h.fd` while `h.alloc` is being drained."
Both directions come from the *same* two aspects, not new ones: `ToRecord` yields
`to_record(self) -> {...}` **and** `to_record_mut(&mut self) -> &mut {...}`;
`FromRecord` yields `from_record({...}) -> Self` **and**
`from_record_mut(&mut {...}) -> &mut Self`. By-value vs. by-reference is a mode,
not a separate capability — only the `To`/`From` direction is worth keeping split.

```metel
@derive(ToRecord, FromRecord)
struct Handle { fd: i32, alloc: @a Buffer }

fun drain(h: &mut Handle) -> (@a Buffer, &mut { fd: i32 }) {
    let view = h.to_record_mut();   // &mut { fd: i32, alloc: @a Buffer } — reborrow, zero-cost
    let buf = move view.alloc;       // ordinary row-shrink; view's type narrows to { fd: i32 }
    (buf, view)
}

fun restore(view: &mut { fd: i32 }, buf: @a Buffer) -> &mut Handle {
    view.alloc = buf;                // ordinary row-grow; view's type widens back to the full row
    Handle::from_record_mut(view)    // trivial re-coercion — the row already matches Handle's in full
}
```

Soundness is the same reason the by-value pair is sound — a reborrow, not a copy or
allocation — and `restore` requires the row to have already grown back to `Handle`'s
exact full shape by ordinary field assignment *before* `from_record_mut` is reached, so
there is nothing beyond structural row-matching to check. Nothing stops code from never
calling `restore` and simply being stuck holding `&mut { fd: i32 }` forever,
unable to typecheck it back to `&mut Handle` — the type system enforces safety, not
liveness.

**This does not erode the tier 2 / tier 3 boundary.** Tier 3's one remaining, unique
advantage is untouched: row-conditional impls and direct `HasField`/`Lacks` bound
satisfaction still require a type to intrinsically carry row structure at
impl-resolution time, which no amount of explicit conversion machinery provides.
`Handle` itself is still never usable where a row-generic bound is expected — only
`view` is, and only for as long as it's held.

**Exception: a fiat-linear source struct's `ToRecord` output carries its origin brand,
not a bare row.** RFC-0089 §2.1 allows a struct to be declared `Linear` by fiat (`impl
Linear for Receipt {}`), independent of any field's own multiplicity. The tier-2
conversion specified above cannot represent that fact as stated: a record's `Linear`
status is always recomputed from its row alone (§5's field-composition rule), and a fiat
assertion isn't row content, so it would otherwise be silently lost by an ordinary bare
conversion. For this narrow case only — a struct whose `Linear` status the row cannot
reconstruct on its own — the derived `.to_record()` output carries the source struct's
brand, and the derive (RFC-0093) emits one ordinary explicit `impl Linear` against that
specific branded shape. See RFC-0089 §3.1 for the full mechanism, its worked example, and
its scope.

This does not itself erode the tier 2 / tier 3 boundary either: carrying a brand for
aspect-impl-targeting purposes is not the same capability as row-conditional-impl
eligibility, which tier 2 still lacks entirely regardless of this exception — a value
produced this way is nominally distinguishable enough to host one specific explicit impl,
but still cannot satisfy `HasField`/`Lacks` bounds or match row-conditional impls the way
a true tier-3 named record can. The exception is scoped exactly as narrowly as RFC-0089
§3.1 states: ordinary structurally-linear structs (the overwhelming majority) keep
converting to a fully bare, brand-less record exactly as specified above — this fires
only when the row alone cannot already answer the `Linear` question correctly.

**No implicit coercion at call sites, regardless of tier.** A `ToRecord`-deriving
struct must never be silently accepted wherever a row-generic bound is expected —
`.to_record()` has to appear in the source. Allowing implicit structural coercion here
would quietly re-widen tier 2 into tier 3 without the type author having asked for it.

**Tier 3 — named record kind: permanent, intrinsic, impl-eligible.** A second, opt-in
nominal kind — a *named record*, distinct from but closely related to §2's anonymous
`{...}` type-former — carries a `(row, brand)` representation intrinsically, not
just convertibly. **Syntax settled 2026-07-23, folded in here 2026-07-24** (this
paragraph previously read "illustrative only, not settled"; open question 8 is now
resolved rather than flagged as inconsistent with this prose):

```metel
record Handle { fd: i32, alloc: @a Buffer }   // row machinery, permanently
```

`record` joins `struct`/`enum`/`aspect` as a declaration keyword, and — since the
2026-07-24 revision dropped it from the anonymous former — **declaring a nominal type is
now the only job the keyword has.** The division of labour is exactly the one
`access-and-presence-rows.md` §3.5 draws between `type X = { ... }` (binds a name to a
row, mints no identity) and `record X { ... }` (mints identity): a keyword where new
identity is created, bare braces where none is.

This is strictly more than tier 2, and tier 2 cannot substitute for it:
**row-conditional impls are resolved by the type system matching a type's own declared
row at impl-resolution time, not by calling a conversion function.**
`impl<row R: !{ token: _ }> Session<R> { ... }` needs `Session` to intrinsically carry
row structure as part of its type — there is no call site for a derived conversion to
intercept, so a type that merely derives `ToRecord`/`FromRecord` can never have
row-conditional impls written against it. Conversely, a tier-3 type gets tier 2's
conversions for free — `to_record`/`from_record` on a type that already *is* `(row,
brand)` are the trivial identity coercion, nothing to derive separately.

**Why three tiers and not two, and why not merge 2 and 3:** collapsing tier 2 into tier
3 would force anyone who wants a single local drain/restore dance in one function to
also accept the coherence-priority and private-field-leakage exposure (§9) that only
matters for types with row-conditional impls — paying for machinery never asked for.
The guardrail this depends on: **each tier must correspond to a distinct capability
requirement — "no row access" / "temporary, explicit, non-impl-eligible row access" /
"permanent, impl-eligible row access" — never offered as interchangeable alternatives
for the same need.**

**A separate, smaller feature riding on top of either tier: `from_record` tolerating
omitted fields typed `Perhaps<T>`.** If a struct declares a field as `Perhaps<T>`
rather than bare `T`, `from_record` can accept an input record missing that field's key
entirely and default it to `Perhaps::none()`:

```metel
@derive(ToRecord, FromRecord)
struct Config {
    host: String,
    timeout: Perhaps<i32>,
}

let partial = { host = "example.com" };   // `timeout` key absent entirely
let cfg = Config::from_record(partial);          // cfg.timeout == Perhaps::none()
```

This is *value-level* and dynamic (the field's key and static type are unchanged), a
different axis from *row-level* absence, which is what drain/restore's static tracking
uses. It earns its keep for generic, struct-agnostic code — one library function that
reconstructs *any* `FromRecord`-deriving type from a partial record, defaulting
whichever fields happen to be declared `Perhaps<T>` — essentially Rust's
`..Default::default()` struct-update syntax, generalized to per-field defaults instead
of requiring the whole remainder to implement `Default`.

**Why any of this split:**

- **Closes the TypeScript failure mode at its root.** Structural matching stays
  non-ambient — the overwhelming majority of types never raise "does this support
  drain/restore, Lacks-typestate, or some absence-idiom" at all, because the answer is
  fixed once, by the author, at the declaration or derive, never re-litigated per call
  site.
- **Shrinks the implementation cost by confining row-awareness to whichever tier a
  type opted into** — an additive path alongside ordinary `Type::Named` handling, not a
  change to it, for both tier 2 and tier 3.
- **Cleanly separates Cluster A / Cluster B phasing.** Ordinary structs need none of
  the affine/multiplicity/row work to exist.

**The non-breaking upgrade path.** Tier 1 → tier 2 (adding `@derive(ToRecord,
FromRecord)`) is additive by construction. Tier 1 → tier 3 (`struct` → `record`) needs
more care; converting should not require touching any existing caller, provided:

- The nominal name and identity are unchanged — aspect impls, orphan-rule coherence,
  and generic instantiation all key off the same identity as before.
- Construction and field-access syntax are unchanged.
- Whole-value use sites keep typechecking exactly as before, against the record's full
  row.
- Row tracking costs nothing at runtime for whole-value-only callers.

**One honest caveat, for tier 3 specifically: "non-breaking" means "doesn't break
existing callers," not "changes nothing observable about the type."** The conversion
does newly make row-conditional generic functions and drain/restore-style APIs legal
against `Handle`, callable from the declaring module forward — that is the point of
upgrading, not a side effect to apologize for.

---

## 9. Reconciling with the inverse direction: structural types as the foundation

Real precedent exists for representing every named type as `(row, brand)` internally —
a structural shape plus an identity tag (TypeScript: every named type is a label over a
structural descriptor; OCaml's object/row system, where a class name is a constructor
convenience over a structural object type). **This is not a re-litigation of §6.** §6
already considered "nominal types as pure sugar over an underlying record" and declined
it, for a reason that still holds at full strength: nominal identity is load-bearing,
so the sugar has to reintroduce a real identity tag to keep working, "at which point
the reframing hasn't reduced what the system has to track, only renamed the part that
was never really sugar." What survives is narrower: not *elimination* of the tag, but
*reuse* of it.

**The tag doesn't need to be a bespoke fourth mechanism.** `brand-kind-unification.md`
already proposes that `@a` (allocator tags), `&r` (lifetime anchors), and `'c` (brands,
RFC-0076) are one underlying identity kind under three sigils. A struct's inevitable
identity tag is a plausible fourth surface use of that same `'c`-role kind, not a new
kind alongside it — implementer economy (one freshness/erasure/rigidity checker), not a
new concept for users. See that document's Open Questions for the specific new question
this raises (whether nesting a brand-carrying struct inside `@a`/`Rc` is an intentional
role-crossing or just ordinary composition of the same role at two levels — unresolved
there, not here).

**Scope stays where §6 already drew it.** This is a representation-sharing move for
structs specifically. It says nothing new about enums (§6's sum-type objection is
untouched) or primitives.

**Two open questions this raises:**

- **Coherence needs a specificity rule between the two axes an impl can now match on.**
  An ordinary `impl Display for Point` is brand-keyed; RFC-0061's structural/blanket
  impls (`impl<row R: { x: f64 }> Display for { ..R }`) are row-keyed — the target
  spelled with §2's spread tail now that `record R` has no keyword to lean on. If a
  `Point` value matches both, which wins? The obvious default — brand-keyed beats
  row-keyed blanket impls, more-specific-wins — is not written down as a rule anywhere,
  and RFC-0060/RFC-0061's coherence checking does not yet account for a second axis at
  all.
- **Field-level visibility (RFC-0032) and structural matching haven't been
  reconciled.** If a bound `{ secret: T }` is checked directly against a struct's row,
  does code outside the declaring module get to observe — or structurally match
  against — a private field? It shouldn't, which means the row isn't a single flat
  structure per brand; cross-module structural matching needs to see only a *public
  projection* of the row, with private fields invisible to `HasField`/`Lacks` checks
  from outside the module.

Partial consumption's residual reusing this same `(row, brand)` machinery for a
*nominal* type (rather than an anonymous record) is a Linear-specific application of
this idea, specified in RFC-0091, not here.

---

## Open Questions

1. Ship closed `record` types only for now, or also `<row R>` open generics
   immediately (§3) — recommend closed-only first; not ratified.
2. Plain-record style vs. OCaml-object style (§7) — recommend plain records; not
   ratified.
3. Width-subtyping-requires-`Copy` rule (§7) — proposed with no existing precedent to
   verify it against; not ratified. No bound expressing "every field in row `R` is
   `Copy`" is defined yet.
4. Row-conditional impl coherence (§4) — extending RFC-0036/RFC-0060's conditional-impl
   checking to `HasField`/`Lacks`-style row conditions is asserted to be tractable but
   not worked out.
5. **Phantom-type-parameter typestate (`brand-types.md`) vs. row-conditional-impl
   typestate (§4) — which is canonical, or do both stay, and for which cases?** Not
   resolved — too early to decide.
6. **Brand-vs-row impl coherence priority (§9)** — no specificity rule between
   brand-keyed and row-keyed blanket impls is written down.
7. **Private-field leakage into cross-module structural matching (§9)** — no mechanism
   for the public-only row projection is designed yet.
8. ~~What syntactically marks tier 3, the named record kind?~~ **Resolved 2026-07-23,
   folded into §8's prose 2026-07-24:** `record X { ... }`, a separate keyword joining
   the `struct`/`enum`/`aspect` declaration family — see the revision notes above and
   `reports/substructural-types/access-and-presence-rows.md` §3.5. §8 no longer describes
   this as illustrative-only, so the inconsistency this entry flagged is gone. The
   2026-07-24 revision sharpens the answer: since the anonymous former dropped the
   keyword, **declaring a nominal type is the only remaining job `record` has**, which is
   a cleaner justification for spending a keyword on it than the original "it joins a
   family" argument.
9. **Whether §5's allocator-type restriction transfers to tier 3 (§8)** — §5's
   objection assumed structural interchangeability, which tier 3's fixed brand
   arguably avoids; unresolved.
10. **Whether `FromRecord` needs a guard against bypassing constructor invariants
    (§8)** — the `SortedPair` case shows auto-derived reconstruction can silently skip
    validation a hand-written constructor enforces; no compile-time check for this is
    proposed here. **Proposed answer split out as its own RFC, 2026-07-23:**
    `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md` —
    a `Construct` aspect returning `Result<Self, Self::Error>`, with `FromRecord`
    collapsing into the same mechanism. Not merged into this RFC's own text; that
    reconciliation is left to whichever review pass handles both.
11. **Whether the brand-carrying `ToRecord` exception (§8, RFC-0089 §3.1) needs its own
    coherence check** to guarantee no other code can independently produce a value
    carrying the same brand plus a conflicting impl. Likely resolves to "no need" given
    brand rigidity/freshness (RFC-0076) — the brand is unforgeable from outside the
    derive — but this is asserted, not proven, matching RFC-0089's own Open Question 6.
12. **New, 2026-07-23. Two pieces of grammar work the bound-syntax revision above
    depends on, neither written yet:** a new `bound_head` alternative letting a bound
    start from a bare row instead of only a `type_path`, and a type-position wildcard
    `_` (meaning "any type") for `!{ tag: _ }` — `_` exists only in `pattern` today,
    confirmed absent from `type_expr`. Whether this lands as part of this RFC's own
    acceptance or as a separate small amendment is not decided.
    **Widened 2026-07-24 by the keyword drop:** the anonymous former now needs a bare
    `{ ... }` alternative in `type_expr` and in expression position too, not only in
    bound position. `access-and-presence-rows.md` §3.5 checked both against
    `grammar.pest` and found them safe — a bare block is not an expression alternative,
    and `struct_literal` requires a preceding `type_path` — but "safe" was established by
    grammar reading, not by a built prototype, and the interaction with
    `block_expr_stmt`'s `!"}"` lookahead is explicitly unchecked there.
13. **New, 2026-07-24. A closed record type and a row bound are now spelled identically.**
    Dropping `record` from the anonymous former means `{ x: f64 }` is an exact, closed
    product type in `param`/`let` position and an existential "at least these fields"
    predicate in `generic_param`/`where_constraint` position. The grammar keeps them
    apart; a reader has only position to go on, where the keyword used to disambiguate
    (§2, §5). Three things not settled: whether this is acceptable as-is (the position
    genuinely does track the meaning, and no other language spells these differently
    either — PureScript and Elm both reuse braces for both roles); whether diagnostics
    need to name which reading was taken when a mismatch occurs; and whether any position
    exists where *both* readings are grammatically admissible, which would turn a
    readability cost into a real ambiguity. The third is the one worth checking first,
    and it has not been checked.

---

## Example Programs

### Records, row bounds, and where they stop being usable

```metel
let point = { x = 1.0, y = 2.0 };   // closed record — exact shape

fun magnitude<T: { x: f64, y: f64 }>(p: T) -> f64 {
    (p.x * p.x + p.y * p.y).sqrt()
}

println("mag = ${magnitude(point)}");

// Any nominal struct with matching fields satisfies the same bound, no opt-in (§5):
struct ScreenPos { x: f64, y: f64, z_index: i64 }
println("mag = ${magnitude(ScreenPos { x: 3.0, y: 4.0, z_index: 1 })}");

// Not usable, per §5:
//   impl { x: f64, y: f64 } { fun scale(&self, k: f64) -> ... }
//   -- no owning module; inherent impls on records are banned outright.
//   aspect impl Display for { x: f64, y: f64 } { ... }
//   -- Display isn't local to this module; banned the other direction of the same rule.
```

### Typestate via row-conditional impls

```metel
struct Session<row R> { data: { ..R } }

impl<row R: { token: String }> Session<R> {
    fun authenticate(self) -> Session<R without "token"> { ... }
}

impl<row R: !{ token: _ }> Session<R> {
    fun send_data(&self, bytes: String) {
        println("sending: ${bytes}");
    }
}

fun main() -> i64 {
    let s = Session { data: { token = "secret", host = "example.com" } };
    let authenticated = s.authenticate();
    authenticated.send_data("hello");
    // s.send_data("hello");   -- would not compile: s's row still has `token`
    0
}
```

### Tier 3: an upgrade that doesn't touch existing callers

`record` as a named-declaration keyword is settled (§8, open question 8).

```metel
// Before: an ordinary struct, whole-value only.
struct Handle { fd: i32, alloc: @a Buffer }

fun close_it(h: Handle) { /* uses h.fd, h.alloc as a whole */ }

// After: `Handle` opts into row machinery. Same name, same fields, same construction
// and field-access syntax — `close_it` above still typechecks unchanged.
record Handle { fd: i32, alloc: @a Buffer }

fun drain(h: &mut Handle) -> (@a Buffer, &mut { fd: i32 }) {
    let buf = move h.alloc;
    (buf, h)
}

fun restore(h: &mut { fd: i32 }, buf: @a Buffer) -> &mut Handle {
    h.alloc = buf;
    h
}
```

### Tier 2: on-demand conversion, and where `ToRecord`/`FromRecord` stay separate

```metel
@derive(ToRecord)   // ToRecord only — see below
struct SortedPair {
    small: i32,
    big: i32,
}

impl SortedPair {
    fun new(a: i32, b: i32) -> SortedPair {
        if a <= b { SortedPair { small: a, big: b } } else { SortedPair { small: b, big: a } }
    }
}

// A caller can still read the shape out generically:
let p = SortedPair::new(3, 1);
let r = p.to_record();   // { small: i32, big: i32 } == { small = 1, big = 3 }

// FromRecord is deliberately not derived: an auto-derived reconstruction would pack
// whatever small/big a record holds straight back into a SortedPair, silently
// bypassing new's reordering. Reconstruction stays routed through SortedPair::new.
```

---

## References

- `reports/substructural-types/structural-records.md` — the living design report this
  RFC is extracted from
- RFC-0080 (Standard Library Aspects) — auto-impl pattern this RFC's `HasField` family
  and `ToRecord`/`FromRecord` reuse
- RFC-0096 (Auto-Impl Aspects, draft) §7 — works out precisely how the row-bound
  mechanism differs from `Send`/`Sync`/`Linear`'s auto-impl mechanism (family vs. fixed
  marker, existential vs. universal satisfaction), and flags the coherence gap this RFC
  still leaves unresolved; the bound-syntax gap it also flagged is fixed by the
  2026-07-23 revision above
- `reports/substructural-types/access-and-presence-rows.md` §3.5,
  `reports/substructural-types/nominal-types-as-branded-rows.md` §12 — the bare-row
  bound syntax this RFC's `HasField`/`Lacks` were replaced with
- RFC-0036 (Conditional Impl Blocks) — row-conditional impls generalize this directly
- RFC-0060 (Aspect Impl Coherence), RFC-0061 (Structural Aspect Bounds) — coherence
  checking this RFC's row-conditional impls and structural bounds extend
- RFC-0063 (Allocator Handles) — §2's disjointness story, the reason records cannot
  serve as allocator types
- `brand-types.md` — phantom-type-parameter typestate, the alternative to §4's
  row-conditional encoding
- `brand-kind-unification.md` — the `(row, brand)` tag-reuse claim in §9
- RFC-0089 (Linear Types) — the multiplicity model tier 2/3's field composition rules
  extend to records
- RFC-0091 (Linear Records) — depends on this RFC for the row/tier machinery it
  extends with per-field multiplicity tracking
- RFC-0093 (Derive Registration) — the comptime mechanism that makes tier 2's
  conversions auto-derivable, not a prerequisite for tier 2 to exist

---

## Decision

**Outcome:** *(pending)*
**Target:** unspecified

*(Decision rationale goes here when the RFC is evaluated.)*
