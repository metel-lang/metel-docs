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
> **One thing was deliberately left behind in the extraction: RFC-0090 §8's brand-carrying
> exception for fiat-linear structs.** That exception existed solely to serve RFC-0089
> §2.1's fiat-linearity, and the per-field-multiplicity work is deferred until records are
> implemented. Dropping it removes this cluster's **only** dependency on RFC-0076 (Brand
> Types, `0-draft`) — see §5.

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
soundness weight. A by-reference mode (`to_record_mut`/`from_record_mut`) extends the same
two aspects to borrowed access rather than adding new ones.

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

## 2. By-reference mode

The by-value pair covers "consume the struct, get a record, maybe rebuild later." It does
not cover "keep using `h.fd` while `h.alloc` is being drained." Both modes come from the
*same* two aspects:

- `ToRecord` yields `to_record(self) -> { … }` **and** `to_record_mut(&mut self) -> &mut { … }`
- `FromRecord` yields `from_record({ … }) -> Self` **and** `from_record_mut(&mut { … }) -> &mut Self`

By-value versus by-reference is a **mode**, not a separate capability; only the `To`/`From`
direction is worth splitting.

```metel
fun drain(h: &mut Handle) -> (@a Buffer, &mut { fd: i32 }) {
    let view = h.to_record_mut();   // &mut { fd: i32, alloc: @a Buffer } — reborrow, zero-cost
    let buf = move view.alloc;      // RFC-0117 narrowing; view : &mut { fd: i32 }
    (buf, view)
}

fun restore(view: &mut { fd: i32 }, buf: @a Buffer) -> &mut Handle {
    view.alloc = buf;               // row grows back to Handle's exact full shape
    Handle::from_record_mut(view)
}
```

Soundness is the by-value argument unchanged — a reborrow, not a copy — and `restore`
requires the row to have grown back to `Handle`'s exact shape *before* `from_record_mut` is
reached, so there is nothing beyond structural matching to check.

**This enforces safety, not liveness.** Nothing stops code from never calling `restore` and
simply being stuck holding `&mut { fd: i32 }` forever, unable to typecheck it back. That is
accepted.

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
only the converted `view` is, and only while it is held.

## 5. The brand exception, and why it is not here

RFC-0090 §8 carried an exception: a struct declared `Linear` **by fiat** (RFC-0089 §2.1 —
forced linear with no field of its own explaining it) loses that status on conversion, since
a record's `Linear` status is recomputed from its row alone. The fix was for the derived
conversion to carry the source struct's **brand**, with the derive emitting one explicit
`impl Linear` against that branded shape.

**That exception is not carried into this RFC**, because per-field multiplicity is deferred
until records are implemented. It must be restored — here or in whichever RFC carries
fiat-linearity — at the point per-field multiplicity is taken up again.

> **Correction, 2026-07-24, later the same day. The claim this section originally made was
> too strong and is withdrawn.** It read: *"this RFC has no dependency on RFC-0076 (Brand
> Types, `0-draft`), and neither does any other RFC in the records cluster."* That is
> established only for the **by-value** pair. **§2's by-reference mode may reinstate the
> dependency by a completely different route** — not through fiat-linearity, but through
> reassembly provenance (open question 8). The accurate statement is: *removing
> fiat-linearity removed the brand dependency that came from fiat-linearity.* Whether the
> cluster is brand-free overall depends on how open question 8 resolves, and that is not
> yet decided.
>
> The same overstated claim was repeated in `internal/rfcs/INDEX.md` and
> `reports/strategy/OBJECTIVES.md` when the cluster was decomposed; both are corrected.
> Kept visible here rather than quietly edited, because "this cluster now depends on
> nothing unratified" was used as evidence that the decomposition had simplified the
> design, and that evidence is weaker than it was presented as.

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
6. **The by-value and by-reference halves of `FromRecord` are not the same kind of
   operation, and §2 presents them as if they were.** `from_record(row) -> Self`
   constructs. `from_record_mut(&mut { … }) -> &mut Self` **constructs nothing** — it
   re-coerces an existing borrow whose row has grown back to full shape. `construct`
   returns `Result<Self, _>` by value and does not fit the second. So OQ5's collapse, if
   adopted, cleanly absorbs the by-value half and leaves the by-reference half homeless.
7. **§2 and RFC-0114 §3 contradict each other, and neither document notices.** §2 states
   that `restore` *"requires the row to have already grown back to `Handle`'s exact full
   shape... so there is nothing beyond structural row-matching to check."* RFC-0114 §3
   states that **any assignment completing a narrowed row is sugar for calling
   `construct()`** on the completed row. Under §2, `view.alloc = buf; from_record_mut(view)`
   validates nothing — which is precisely the invariant bypass RFC-0114 exists to close.
   One of the two is wrong. Note the asymmetry that makes this hard: `construct` produces an
   owned `Self`, so it cannot be what fires behind a `&mut` view.
8. **Reassembly needs *provenance*, not shape — and whether that is free depends on a
   question the corpus currently answers two ways.** For `from_record_mut` to hand back a
   `&mut Self`, the compiler must know all the fields belong to **the same struct instance**.
   Two readings of what a view *is* are both live:
   - **(a) A borrow of a record** — §2's own signature, `&mut { … }`, one pointer, "same
     bits, new static type." Under (a) the guarantee is structural: one pointer, one
     object, nothing to check.
   - **(b) A record of borrows** — `reports/substructural-types/access-and-presence-rows.md`
     §3 reads `&mut Handle.{fd, alloc}` as `{ fd: &mut i32, alloc: &mut Buffer }`, *N*
     independent pointers, and argues this reading is **better** (mode moves inside the row,
     mixed `&`/`&mut` access falls out for free, RFC-0109 §4.9's tuple-of-views becomes
     unnecessary).

   **Under (b), §2 is unsound as written.** Nothing prevents `fd` borrowing `h1` and
   `alloc` borrowing `h2`; `from_record_mut` would then produce one `&mut Handle` whose
   fields live in different objects — not merely odd, but a direct contradiction of the
   zero-cost "same bits" claim, because the bits are not one struct's bits.

   The check would have to be an **identity** check, and the corpus has exactly one
   mechanism for those: brands. RFC-0109 already brands its named views for an adjacent
   reason (so an unrelated same-shaped value cannot satisfy one). **That is what reinstates
   the RFC-0076 dependency §5's correction withdraws the denial of** — and it collides with
   tier 2's defining bare-ness (RFC-0090 §8 specified the conversion as bare/anonymous; a
   provenance brand is not bare).

   **Three ways out, and the third deserves the hardest look:**
   1. Views are (a). Sound, no check — but forgoes the desugaring the corpus found better,
      and RFC-0109 §4.9's separate construct stays necessary.
   2. Views are (b). Better ergonomics, but by-reference conversion needs a brand,
      contradicting bare-ness and reinstating RFC-0076.
   3. **Drop by-reference conversion from tier 2 entirely.** Keep only the by-value pair
      here; let RFC-0109's branded named views own the borrowed case, which is what they
      were designed for. This makes the tier boundary *cleaner* rather than patching it —
      by-value conversion is bare and needs no identity, anything borrowed needs identity
      and belongs where brands already live — and it dissolves OQ6 and OQ7 as a side
      effect, since the homeless half simply stops existing.
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
