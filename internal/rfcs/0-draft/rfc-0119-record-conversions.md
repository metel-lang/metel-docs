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
until records are implemented. The consequence is worth stating plainly, since it is the
single largest simplification the deferral produced: **this RFC has no dependency on
RFC-0076 (Brand Types, `0-draft`)**, and neither does any other RFC in the records cluster.
The exception must be restored — here or in whichever RFC carries fiat-linearity — at the
point per-field multiplicity is taken up again.

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
