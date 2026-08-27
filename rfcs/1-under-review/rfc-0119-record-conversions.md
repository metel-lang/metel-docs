---
id: rfc-0119
title: "Record Conversions"
date: '2026-07-24'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/790'
target: v0.13.1
updated: '2026-08-23'
---

> **Extracted from RFC-0090 §8 (tier 2) on 2026-07-24** (superseded; see RFC-0116's header
> for the split rationale). Depends on RFC-0116 (Anonymous Record Types) and RFC-0117 (Row
> Narrowing).
>
> **Two things from RFC-0090 §8 are deliberately not carried over.** Its brand-carrying
> exception for fiat-linear structs, which served RFC-0089 §2.1 and is deferred with the
> rest of the per-field-multiplicity work (§5); and its **by-reference mode**
> (`to_record_mut`/`from_record_mut`), dropped 2026-07-24 as superseded by RFC-0109's
> named views (§2).
>
> Between them these leave this RFC with **no dependency on RFC-0076 (Brand Types,
> `0-draft`)** — and, after §2, for a structural reason rather than by omission: tier 2
> never handles a borrow, so it never needs to establish which object one came from.

> **Status — under review (2026-08-23).** Tracking issue #790 filed 2026-08-22.
> **Moved out of v0.13.0 the next day**, once RFC-0120 was found not to actually depend
> on this RFC (RFC-0120's own header carried a stale dependency inherited from the
> original split's ordering, not a real requirement — see RFC-0120's 2026-08-23
> correction). Unplaced rather than pushed to a later milestone number: this RFC's real
> blocker is RFC-0093 (comptime derive, `1-under-review` as of 2026-08-23, `#799`, no
> target) — the same "don't force it
> into a milestone it doesn't fit" treatment RFC-0124 already got for its own RFC-0067
> dependency. OQ1 still holds: the hand-writable form needs no derive at all, so nothing
> here is refused, just not scheduled while its practical value (the `#derive(...)`
> convenience every example in this RFC actually uses) is on an open-ended wait.

## Summary

Two derivable aspects, `ToRecord` and `FromRecord`, converting between a nominal struct and
a record of its fields:

```metel
#derive(ToRecord, FromRecord)
struct Handle { fd: i32, alloc: @a Buffer }

let r  = h.to_record();            // { fd: i32, alloc: @a Buffer } — same bits, new static type
let h2 = Handle::from_record(r);
```

Both directions are zero-cost — a relabelling of the same bits, not a real conversion. They
are kept **separate aspects, not merged**, because the two directions carry different
soundness weight. **By-value only** — RFC-0090 §8's `to_record_mut`/`from_record_mut` are
dropped (§2); borrowed sub-row access belongs to RFC-0109's branded named views.

The struct itself is unchanged: no representation change, no new impls become legal against
it, and it never implicitly satisfies a row bound. Conversion is explicit and appears in the
source.

---

## Motivation

RFC-0116 gives records; RFC-0117 lets them narrow. Neither gives an existing nominal struct
any way to participate. Without conversion, records are useful only for data that was
structural from the start, and every "take one field out and keep using the rest" pattern
on an ordinary struct remains inexpressible.

The design constraint that shapes everything here: **structural capability must never be
ambient.** A struct that has not opted in is not usable where a row is expected — that is
what keeps Metel out of TypeScript's silent nominal-identity collapse, and it is why
conversion is a derive rather than a coercion.

---

## 1. `ToRecord` and `FromRecord` stay separate

Consider a type with a constructor-checked invariant:

```metel
struct SortedPair { small: i32, big: i32 }   // invariant: small <= big
```

`ToRecord` is always safe — reading fields out cannot violate anything. Auto-deriving
`FromRecord` would synthesize a reconstruction packing whatever `small`/`big` a record holds
straight back in, bypassing the check. So such a type derives `ToRecord` alone, and either
hand-writes `FromRecord` with the check restored or declines it.

This mirrors a decision the ecosystem already made for the same reason: serde's
`Serialize`/`Deserialize` are separate traits, commonly derived together but never merged,
because "safe to read out" and "safe to construct from arbitrary input" are different risk
profiles. A bundled `Record` shorthand was considered and declined on the same grounds.

**RFC-0114 (Constructor Aspect) generalizes the underlying problem** and, if adopted, makes
`from_record` sugar for `Self::construct(row)` — so the invariant is enforced once, in one
place, rather than by each conversion remembering to. This RFC does not depend on RFC-0114;
if it lands, the two reconcile as noted there.

## 2. By-value only: `to_record_mut`/`from_record_mut` are dropped

**Decided 2026-07-24.** RFC-0090 §8 gave `ToRecord`/`FromRecord` a second, by-reference
mode — `to_record_mut(&var self) -> &var { … }` and
`from_record_mut(&var { … }) -> &var Self` — framed as a *mode* rather than a separate
capability. **This RFC does not carry it.** Tier 2 is by-value: consume the struct, get a
record, maybe rebuild later.

**The chronology is the argument.** `to_record_mut` was added on 2026-07-08 with the commit
message *"resolving tier 2's borrow gap"* — invented because nothing else could express
borrowed sub-row access at the time. RFC-0109 (Self-View Narrowing, 2026-07-18) built that
mechanism properly ten days later: named views as *branded* records, plus
reference-destructuring patterns for the ad hoc case. The by-reference mode is what the
design reached for before the right tool existed.

**What this removes, stated precisely — it is not purely redundancy.** The dropped
construct did two things, and only one of them is replaced:

- **Borrowed access to a sub-row** — fully replaced by RFC-0109, and better: a named view is
  branded, so an unrelated same-shaped value cannot satisfy it, whereas a bare
  `&var { fd: i32 }` could.
- **Moving a field *out* through a borrow** (`let buf = view.alloc;` — moving a non-Copy
  field out is implicit, there is no `move` keyword) — **not replaced.** Views govern
  access, not consumption. Nothing in the remaining cluster lets you take ownership of
  one field while the rest stays borrowed. (This was never actually reachable in the
  first place: RFC-0071 §7.1 bans moving a non-`Copy` field out through any reference,
  `&var` included — the dropped construct's field-consumption story was aspirational
  even before it was removed.)

**That second capability is not obviously wanted, and it was the source of three separate
problems.** Rust does not permit moving out of `&var` either. Every open question this RFC
carried about provenance, about validation on reassembly, and about the by-value/by-reference
asymmetry originated in that one construct — see the struck-through entries in Open
Questions. Dropping it dissolves all three rather than answering them.

**Consequence for the tier boundary, which comes out cleaner.** By-value conversion is bare
and anonymous and needs no notion of identity: it consumes one whole value and produces one
whole record. Anything *borrowed* needs to know which object it came from, which is an
identity question, which is why RFC-0109's views are branded. The split is now along that
line exactly — **tier 2 is bare because it is by-value; borrowed access is branded because
it must be** — instead of tier 2 straddling both and needing a provenance rule it never
had.

## 3. No implicit coercion at call sites

A `ToRecord`-deriving struct must **never** be silently accepted where a row bound is
expected. `.to_record()` has to appear in the source. Allowing implicit structural coercion
here would quietly grant every deriving struct the capability RFC-0120 exists to gate,
without its author asking.

This is the rule RFC-0109 (self-view narrowing, deferred) exists to work *around* for the
specific case of method receivers — deliberately, and by a mechanism that does not weaken it
generally.

## 4. What deriving does not buy

Deriving these conversions does **not** make a struct row-conditional-impl eligible, and does
not let it satisfy a row bound directly. Those require the type to intrinsically carry row
structure at impl-resolution time, which no amount of explicit conversion machinery provides
— that is RFC-0120. `Handle` itself is never usable where a row-generic bound is expected;
only the record produced by `.to_record()` is, and that record is a separate owned value,
not a window onto the struct.

**Added 2026-08-25 — `.to_record()` on an already-narrowed residual (RFC-0137, then
accepted; reverted to `1-under-review` the same day — RFC-0137's own Open Questions
5-6, opened on reversion, didn't touch this reasoning directly, and RFC-0137 was
re-accepted 2026-08-27 with all four Open Questions closed).**
This RFC's text above describes `to_record()` against "the record" for a `#derive`-ing
struct, written before RFC-0137 gave residual types a way to exist — under move-tracking
alone (RFC-0071), a struct's declared row and its current row were always the same value,
so nothing here ever had to distinguish them. Under RFC-0137 they can diverge: a residual
like `Handle.{ fd }` (after `name` was moved out) has a smaller current row than `Handle`'s
full declared one. The consistent answer, not a new capability: `to_record()` produces a
record matching **self's current row**, whatever it presently is — this is exactly what
"reading fields out" (this RFC's own framing above) already meant for a whole, unnarrowed
value, and narrowing doesn't add anything `to_record()` has to newly account for beyond
which fields happen to be there when it's called. `handle_narrowed.to_record()` therefore
produces `{ fd: i64 }`, not `Handle`'s full `{ fd: i64, name: String }` — no implicit
widening or further narrowing at the call, consistent with §3's own no-implicit-coercion
stance.

## 5. The brand exception, and why it is not here

RFC-0090 §8 carried an exception: a struct declared `Linear` **by fiat** (RFC-0089 §2.1 —
forced linear with no field of its own explaining it) loses that status on conversion, since
a record's `Linear` status is recomputed from its row alone. The fix was for the derived
conversion to carry the source struct's **brand**, with the derive emitting one explicit
`impl Linear` against that branded shape.

**That exception is not carried into this RFC**, because per-field multiplicity is deferred
until records are implemented. It must be restored — here or in whichever RFC carries
fiat-linearity — at the point per-field multiplicity is taken up again.

> **Correction and re-resolution, both 2026-07-24, kept as a pair because the sequence is
> the point.** This section originally claimed removing fiat-linearity left *"no dependency
> on RFC-0076... and neither does any other RFC in the records cluster."* That was
> **withdrawn** hours later: it held only for the by-value pair, and the by-reference mode
> looked likely to reinstate a brand dependency by a different route entirely — reassembly
> provenance, then open question 8. The same overstated claim had been repeated in
> `INDEX.md` and `OBJECTIVES.md`.
>
> **The claim is now true again, but not for the original reason.** Dropping the
> by-reference mode (§2) dissolved open question 8 rather than answering it. So tier 2 is
> brand-free because it never touches a borrow — a structural property of what it does —
> rather than because fiat-linearity happened to be deferred. The whole sequence is kept
> visible because the first version was used as evidence that the decomposition had
> simplified the design, and it is worth showing that the evidence only became sound after
> a second, independent decision.

---

## Open Questions

1. **Is `#derive` available?** Whether these conversions are auto-*derivable* (versus always
   hand-written) depends on RFC-0093's comptime derive mechanism, which is `0-draft`. This
   RFC requires only that `ToRecord`/`FromRecord` exist as ordinary, hand-writable aspects
   with these signatures; the `#derive(…)` convenience is additive.
2. **Does `from_record` need a guard against bypassing constructor invariants?** §1 states
   the risk and the convention (don't derive it on such a type). RFC-0114 proposes a real
   mechanism. Whether this RFC should require RFC-0114, recommend it, or stay silent is
   undecided. *(From RFC-0090 OQ10.)*
3. **Omitted-field defaulting.** If a struct declares a field as `Perhaps<T>`, `from_record`
   could accept an input record lacking that label entirely and default it to
   `Perhaps::none()` — value-level and dynamic, a different axis from row-level absence. It
   earns its keep for generic code that reconstructs *any* `FromRecord` type from a partial
   record. Specified in RFC-0090 §8 as a rider; carried here unresolved, since it is
   separable from the core conversion and nothing depends on it.
4. **New, 2026-07-24, inherited from RFC-0118. What does `to_record()` produce for a
   struct with *private* fields, and who may call it?** RFC-0032 makes fields
   module-private by default. `to_record()` turns a struct into a record, and a record's
   fields are plainly readable — so a conversion callable from outside the declaring module
   would hand out private data, and one that silently omits private fields would produce a
   record whose row does not match `Self`, breaking `from_record`'s round trip.

   **This arrived here by elimination, and that is the useful part.** It was originally
   filed against RFC-0090 (OQ7), narrowed to RFC-0116, then to RFC-0118, where it was
   briefly "resolved" with a public-projection rule for bounds. That resolution was
   withdrawn once RFC-0118 settled that bounds are satisfied by *records* rather than
   structs — a record has no declaring module and no private fields, so it had nothing to
   project. **The question only ever had force where a row is derived *from* a nominal
   struct, which is this RFC and nowhere else.**

   Candidate answers, none adopted: `to_record()` is callable only where every field is
   visible; or it yields only the public projection and `from_record` is correspondingly
   partial; or private fields make a struct ineligible for the derive at all.
5. **What exactly does `to_record()` return for a generic struct?** `Pair<T>`'s row is not
   fully known until `T` is concrete. Believed to need no deferral to monomorphization time
   — the row is computed from the declaration — but unverified. *(Shared with RFC-0114 OQ4.)*

*Questions 5–9 were opened together on 2026-07-24, from a design conversation about
`FromRecord`'s relationship to `Construct`. They are listed in the order the reasoning ran,
because each one exposed the next. Questions 6–8 were dissolved the same day by dropping the
by-reference mode (§2).*

> **Questions 5 and 9 are deferred, 2026-07-24.** Both are genuine improvements and neither
> is refused — but working through them showed both are **more entangled than they looked**,
> and in each case the entanglement is with something that is not settled:
>
> - **OQ5** needs RFC-0100's positional-construction form settled before `Handle(r)` can be
>   given a meaning, and RFC-0100 is `1-under-review` and has been reopened once. Its
>   overridability sub-question also has to be answered *before* the syntax, not after,
>   since an overridable `FromRecord` reopens the invariant hole RFC-0114 §1.1 closes.
> - **OQ9** needs a struct-destructuring pattern that does not exist in the grammar at all,
>   and its natural home is RFC-0109, which is now `0-draft` and deferred until records are
>   implemented.
>
> Neither is a prerequisite for this RFC. `ToRecord`/`FromRecord` as specified above are
> complete and reviewable without them; these would change the *spelling* and the
> *derivation default*, not the capability. **They are candidate refinements to revisit once
> records are implemented and RFC-0100 has resolved** — at which point there will also be
> real usage to judge them against, which neither has today.

6. **Should `FromRecord` be spelled as a constructor call and default to `construct`'s
   logic?** *(Rewritten 2026-07-24 — the first version of this entry recorded a different
   and weaker proposal; see the correction at the end.)*

   The proposal: `FromRecord` **stays its own opt-in aspect**, but two things change.
   - **Surface syntax becomes the constructor call form** — `Handle({ fd = 3, alloc = buf })`
     or `Handle(r)` for an existing row value `r` — instead of a named
     `Handle::from_record(r)` method. There is then no `from_record` spelling at all.
   - **Its default body is `construct`.** Deriving `FromRecord` gives you the ability to
     build the type from a row; what *happens* when you do is RFC-0114's `construct`,
     including its validation, unless the author overrides it.

   **This separates capability from logic, and that is what makes it work.** `Construct`
   is synthesized for every struct and is the *internal* rule for how a `Self` comes into
   existence. `FromRecord` is the *external* permission to invoke that from a row. A struct
   without the derive still has a `construct` — it just cannot be called with a row from
   outside. So the tier boundary is untouched: capability stays opt-in, exactly as
   RFC-0090 §8 requires.

   It also completes a syntactic unification RFC-0114 §2 half-states. That section already
   desugars `SortedPair { small = 3, big = 1 }` to `SortedPair::construct({ small = 3, big
   = 1 })`. Under this proposal, building from a *row value* is the same call with the row
   passed rather than written inline — construction from a literal and construction from a
   record stop being two mechanisms.

   **What needs answering:**
   - **Does `Handle(r)` collide with RFC-0100's positional construction?** RFC-0100 proposes
     `Handle(3, buf)`. For a single-field struct, `Handle(r)` is ambiguous between "the row
     `r`" and "one positional argument `r`". Needs a disambiguation rule, or the row form
     restricted to an explicit record literal.
   - **Are `Handle { fd = 3 }` and `Handle({ fd = 3 })` both legal?** If so that is two
     spellings for one action, which this cluster has removed three times this week. The
     defensible reading is that the brace form takes an *inline* row and the call form takes
     a row *value* — one spelling per situation rather than two per action — but it has to
     be stated.
   - **Does the override story work?** If the default body is `construct` and an author may
     override `FromRecord`, they can bypass `construct` — reintroducing exactly the
     invariant hole RFC-0114 exists to close. Probably the override should be disallowed,
     making `FromRecord` purely a *permission* with no body at all, which converges with
     open question 9's marker-aspect treatment of `ToRecord`.

   > **Correction, same day.** This entry first recorded the proposal as *collapsing*
   > `FromRecord` into `Construct` — one aspect instead of two — and raised what looked
   > like a fatal objection: `Construct` is synthesized universally while `FromRecord` is
   > an opt-in derive, so equating them would make every struct tier 2 and collapse the
   > tier boundary. **That objection was answering a proposal that had not been made.**
   > Reusing the call syntax and the default logic is not merging the aspects, and it keeps
   > the opt-in gate intact.
   >
   > One claim built on the misreading is withdrawn with it: that entry asserted the tier
   > gate could become *visibility* rather than a derive, and that this made RFC-0114 OQ8
   > and RFC-0116 OQ3 "the same question asked three ways." Under the actual proposal the
   > gate stays the derive, so there is no such convergence. **The visibility question
   > remains real and open** — can code outside a module write a record naming private
   > fields? — but it is its own question, not the answer to this one.
7. ~~The by-value and by-reference halves of `FromRecord` are not the same kind of
   operation.~~ **Dissolved 2026-07-24 by dropping the by-reference mode (§2).** There is
   no second half left to be asymmetric with. Recorded because the asymmetry was real and
   is the reason the mode looked wrong before the decision was taken: `from_record_mut`
   constructed nothing, it re-coerced an existing borrow, so it never fit `construct`'s
   owned-`Self` signature.
8. ~~§2 and RFC-0114 §3 contradict each other.~~ **Dissolved 2026-07-24, same cause.**
   §2 claimed reassembly needed nothing beyond structural row-matching while RFC-0114 §3
   requires row completion to fire `construct()`. With no by-reference reassembly, the
   contradiction has no site: rebuilding a struct now always goes through
   `from_record` — that is, through `construct` — by value. **RFC-0114 §3's rule stands
   unamended and is now the only story**, which is what it was written to be.
   RFC-0114's own open question 10 is closed by this.
9. ~~Reassembly needs provenance, not shape.~~ **Dissolved 2026-07-24 by adopting the
   third of its own three options.** The question was whether `from_record_mut` could know
   that all the borrows it reassembles belong to one struct instance — a real hole, since
   under the record-of-borrows reading (`access-and-presence-rows.md` §3) nothing prevented
   `fd` borrowing one `Handle` and `alloc` another, producing a `&var Handle` whose fields
   live in different objects. Its three candidate resolutions were: (1) fix the view to be
   a borrow-of-a-record, (2) add a provenance brand, (3) drop by-reference conversion from
   tier 2 entirely. **(3) was taken.** Tier 2 no longer reassembles anything through a
   borrow, so there is no provenance to establish.

   **Two consequences worth keeping visible.** First, this reinstates the claim §5's
   correction had withdrawn: with the by-reference mode gone, **this RFC genuinely has no
   dependency on RFC-0076**, and now for a structural reason rather than by omission — it
   never handles a borrow, so it never needs an identity. Second, the
   borrow-of-a-record versus record-of-borrows question is *not* settled by this; it moves
   wholly to RFC-0109, which owns borrowed views and already brands them.
10. **Should `ToRecord` be a marker aspect enabling a *destructuring operation*, rather than
   an aspect bearing `to_record` methods?** It is the exact dual of `Construct` — row to
   `Self` at one privileged site, `Self` to row at the dual site — which is the symmetry
   RFC-0114 §8 already gestures at for `Construct`/`Drop`. A methodless marker also matches
   RFC-0096's `Send`/`Sync`/`Linear` pattern rather than inventing a shape.

   **It would close a gap RFC-0109 found independently:** Metel has **no struct-destructuring
   pattern at all** — `Pattern` has seven variants (`Wildcard`, `None`, `Literal`,
   `Binding`, `EnumVariant`, `Tuple`, `Array`) and no `Struct` case, so `let { fd, alloc } =
   h;` does not parse today. RFC-0109 §2 says it needs that by-value form as a foundation
   for its reference-destructuring patterns; a `ToRecord`-gated destructuring supplies it,
   and `let &var { a, b } = h;` becomes the borrowed mode of the same operation.

   **What needs answering:** destructuring binds fields to names, while `to_record()`
   yields a record *value* that can be passed onward — strictly more general. A marker-only
   `ToRecord` needs an account of how the value form is still obtained.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §8 — the source (tier 2), and
  the brand exception §5 explains the absence of
- RFC-0116 (Anonymous Record Types), RFC-0117 (Row Narrowing) — the codomain of the
  conversion, and the narrowing the by-reference mode relies on
- RFC-0120 (Named Records) — tier 3, the capability §4 says deriving does not buy
- RFC-0114 (Constructor Aspect and Canonical Construction) — the general answer to §1's
  invariant-bypass risk
- RFC-0093 (Derive Registration) — the comptime mechanism OQ1 depends on
- RFC-0076 (Brand Types) — **not a dependency of this RFC**; see §5
- `public/rfcs/0-draft/rfc-0089-linear-types.md` §2.1, §3.1 — fiat-linearity and the
  brand exception, deferred until records are implemented
- `rfcs/1-under-review/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md` (RFC-0109, `1-under-review`)
  — deferred; works around §3's no-implicit-coercion rule for method receivers specifically
- RFC-0137 (Nominal Types as Branded Rows, `2-accepted` 2026-08-27 — re-accepted
  after a same-day 2026-08-25 revert) — the source of "current row" as a concept
  distinct from "declared row," per §4's 2026-08-25 addition; that addition's design
  was unaffected by the reversion and RFC-0137 is accepted again as of 2026-08-27

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
