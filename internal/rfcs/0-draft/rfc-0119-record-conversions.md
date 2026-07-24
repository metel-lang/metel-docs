---
id: rfc-0119
title: "Record Conversions"
date: '2026-07-24'
status: draft
target:
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

## Summary

Two derivable aspects, `ToRecord` and `FromRecord`, converting between a nominal struct and
a record of its fields:

```metel
@derive(ToRecord, FromRecord)
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
mode — `to_record_mut(&mut self) -> &mut { … }` and
`from_record_mut(&mut { … }) -> &mut Self` — framed as a *mode* rather than a separate
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
  `&mut { fd: i32 }` could.
- **Moving a field *out* through a borrow** (`let buf = move view.alloc;`) — **not
  replaced.** Views govern access, not consumption. Nothing in the remaining cluster lets
  you take ownership of one field while the rest stays borrowed.

**That second capability is not obviously wanted, and it was the source of three separate
problems.** Rust does not permit moving out of `&mut` either. Every open question this RFC
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

1. **Is `@derive` available?** Whether these conversions are auto-*derivable* (versus always
   hand-written) depends on RFC-0093's comptime derive mechanism, which is `0-draft`. This
   RFC requires only that `ToRecord`/`FromRecord` exist as ordinary, hand-writable aspects
   with these signatures; the `@derive(…)` convenience is additive.
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
4. **What exactly does `to_record()` return for a generic struct?** `Pair<T>`'s row is not
   fully known until `T` is concrete. Believed to need no deferral to monomorphization time
   — the row is computed from the declaration — but unverified. *(Shared with RFC-0114 OQ4.)*

*Questions 5–8 were opened together on 2026-07-24, from a design conversation about whether
`FromRecord` and `Construct` are the same thing. They are listed in the order the reasoning
ran, because each one exposed the next.*

5. **Should `FromRecord` collapse into `Construct` outright, rather than being sugar over
   it?** RFC-0114 §4 already says `from_record(row)` *is* `Self::construct(row)`; the
   stronger form is to stop having two names. **Two arguments for it, both real:**
   - §1's serde analogy holds only because serde has no constructor to route through.
     Metel would. Once `construct` owns the invariant, `SortedPair` need not *decline*
     `FromRecord` — it just has a `construct` that validates. The separation stops being
     about soundness and becomes only about capability gating.
   - RFC-0114 §1.1 admits row-to-`Self` at exactly one privileged site. A separate
     `Self`-producing `from_record` either needs that privilege too — widening the one hole
     the design deliberately narrowed — or must call `construct`, making it an alias.

   **The catch is structural and is the reason this is a question rather than a proposal.**
   RFC-0114 §1 *synthesizes* a `Construct` default for every struct with no invariant.
   `FromRecord` is an opt-in derive, and the tier system's foundational rule is that no
   capability is ambient. If `FromRecord ≡ Construct` and `Construct` is universal, **every
   struct is tier 2 by default and the tier boundary collapses.**

   **A candidate escape, which is the most interesting part:** make the gate *visibility*
   rather than a derive. `construct` can only be *called* by code that can write its
   argument — a record naming all of `Self`'s fields — which requires those fields to be
   visible. A struct with private fields is then not externally constructible even though
   `construct` exists. This converges with RFC-0116 OQ3 and RFC-0114 OQ8, which are already
   asking exactly this; three questions turn out to be one. But it genuinely changes the
   tier model — tier 2 stops being a derive — and should be decided, not slid into.
6. ~~The by-value and by-reference halves of `FromRecord` are not the same kind of
   operation.~~ **Dissolved 2026-07-24 by dropping the by-reference mode (§2).** There is
   no second half left to be asymmetric with. Recorded because the asymmetry was real and
   is the reason the mode looked wrong before the decision was taken: `from_record_mut`
   constructed nothing, it re-coerced an existing borrow, so it never fit `construct`'s
   owned-`Self` signature.
7. ~~§2 and RFC-0114 §3 contradict each other.~~ **Dissolved 2026-07-24, same cause.**
   §2 claimed reassembly needed nothing beyond structural row-matching while RFC-0114 §3
   requires row completion to fire `construct()`. With no by-reference reassembly, the
   contradiction has no site: rebuilding a struct now always goes through
   `from_record` — that is, through `construct` — by value. **RFC-0114 §3's rule stands
   unamended and is now the only story**, which is what it was written to be.
   RFC-0114's own open question 10 is closed by this.
8. ~~Reassembly needs provenance, not shape.~~ **Dissolved 2026-07-24 by adopting the
   third of its own three options.** The question was whether `from_record_mut` could know
   that all the borrows it reassembles belong to one struct instance — a real hole, since
   under the record-of-borrows reading (`access-and-presence-rows.md` §3) nothing prevented
   `fd` borrowing one `Handle` and `alloc` another, producing a `&mut Handle` whose fields
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
9. **Should `ToRecord` be a marker aspect enabling a *destructuring operation*, rather than
   an aspect bearing `to_record` methods?** It is the exact dual of `Construct` — row to
   `Self` at one privileged site, `Self` to row at the dual site — which is the symmetry
   RFC-0114 §8 already gestures at for `Construct`/`Drop`. A methodless marker also matches
   RFC-0096's `Send`/`Sync`/`Linear` pattern rather than inventing a shape.

   **It would close a gap RFC-0109 found independently:** Metel has **no struct-destructuring
   pattern at all** — `Pattern` has seven variants (`Wildcard`, `None`, `Literal`,
   `Binding`, `EnumVariant`, `Tuple`, `Array`) and no `Struct` case, so `let { fd, alloc } =
   h;` does not parse today. RFC-0109 §2 says it needs that by-value form as a foundation
   for its reference-destructuring patterns; a `ToRecord`-gated destructuring supplies it,
   and `let &mut { a, b } = h;` becomes the borrowed mode of the same operation.

   **What needs answering:** destructuring binds fields to names, while `to_record()`
   yields a record *value* that can be passed onward — strictly more general. A marker-only
   `ToRecord` needs an account of how the value form is still obtained.

---

## References

- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` §8 — the source (tier 2), and
  the brand exception §5 explains the absence of
- RFC-0116 (Anonymous Record Types), RFC-0117 (Row Narrowing) — the codomain of the
  conversion, and the narrowing the by-reference mode relies on
- RFC-0120 (Named Records) — tier 3, the capability §4 says deriving does not buy
- RFC-0114 (Constructor Aspect and Canonical Construction) — the general answer to §1's
  invariant-bypass risk
- RFC-0093 (Derive Registration) — the comptime mechanism OQ1 depends on
- RFC-0076 (Brand Types) — **not a dependency of this RFC**; see §5
- `internal/rfcs/0-draft/rfc-0089-linear-types.md` §2.1, §3.1 — fiat-linearity and the
  brand exception, deferred until records are implemented
- `internal/rfcs/0-draft/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  — deferred; works around §3's no-implicit-coercion rule for method receivers specifically

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
