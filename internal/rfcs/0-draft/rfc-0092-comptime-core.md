---
id: rfc-0092
title: "Comptime Core — Type-as-Value, Reflection, and Emit"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects), as part of decomposing that RFC into smaller, independently
> reviewable pieces. This RFC is the dependency root of the split: RFC-0093 (Derive
> Registration) and RFC-0094 (Comptime Metaprogramming) both build on the mechanism
> specified here. RFC-0012 itself is superseded by this RFC plus RFC-0093/0094/0095,
> collectively — see `internal/rfcs/4-superseded/rfc-0012-derived-aspects.md`.

## Summary

Establishes `comptime` — Zig's model directly: compile-time execution of ordinary
Metel code, not a separate macro language. Three pieces: `type` as a first-class
comptime value (and its consequence for `<T>` generics), `typeinfo(T)` reflection over
a type's structure, and `emit` — a way for comptime code to register a declaration as a
side effect of compile-time evaluation. This RFC specifies only the single-declaration
form of `emit` (sufficient for aspect derivation, RFC-0093); the generalization to
multiple declarations and expression-position splicing (needed for macro-like
metaprogramming, not for derive) is RFC-0094's concern.

---

## Motivation

Every mechanism this RFC and its siblings specify — `@derive(Aspect)` registration
(RFC-0093), comptime-callable parsing (RFC-0094) — assumes a derive/compile-time-
execution mechanism that no prior document specifies. Zig's answer avoids the two
failure modes of Rust's alternative (a closed, compiler-hardcoded derive list; a
separate procedural-macro language with its own grammar, token streams, and hygiene
system): comptime code is the same language as runtime code, staged earlier, because
the same evaluator runs it.

---

## 1. Generics as comptime sugar

A `type` (e.g. `Point`, `i64`, `Perhaps<T>`) can be bound, passed, and returned like any
other comptime-known value. This is also the natural explanation for Metel's existing
`<T>` generics (spec: `public/reference/spec/types.md`, "Generics"): Zig does not have
`<T>`-style generics as a mechanism separate from comptime — `fun first(comptime T: type, arr: T[])`
*is* how Zig spells a generic function, because a compile-time-known `type` parameter
is just an ordinary parameter, staged. Under this RFC, `fun first<T>(arr: T[])` is
sugar over the same comptime type-parameter mechanism, rather than a second,
independently-specified feature living alongside it.

This is worth more than a passing mention, because it isn't a free-standing design
choice — it interacts with two things Metel's generics already commit to in accepted
RFCs, one confirming the unification and one in tension with it.

**Monomorphization is already assumed, not a retrofit.** RFC-0008 (Aspect Objects,
accepted) draws its entire dynamic-dispatch proposal as a contrast against an existing
default: "Static dispatch (generics + monomorphisation) requires the concrete type to
be known at compile time... a function accepting `impl Aspect` is monomorphised per
caller type." That is exactly what comptime-parameter semantics produce: a distinct,
compile-time-known `T` triggers a fresh evaluation of the function body specialized to
that `T`, i.e. monomorphization, by construction, with no separate codegen step to
design. Adopting comptime for generics doesn't change Metel's dispatch model — it gives
the model RFC-0008 already assumes an actual mechanism, rather than leaving
"monomorphisation" as an unexamined word every generics-adjacent RFC (RFC-0008,
RFC-0036, RFC-0037, RFC-0061, RFC-0072, RFC-0082) currently relies on without
specifying how it happens.

**Bound-checking timing is a real tension, not a free unification.** RFC-0061
(Structural Aspect Bounds, accepted) already assumes a *bound checker*: aspect bounds
like `T: Display` are checked with "a precise diagnostic" when a bound cannot be
satisfied, implying failures are caught systematically against the bound, not merely
wherever a missing method happens to be called. Zig's actual comptime generics have no
equivalent: there is no bound-checking layer at all. A Zig generic function's body is
type-checked only once instantiated with a concrete `T`; a call to a method that `T`
does not provide fails at the use site, deep inside that specific instantiation,
frequently with an error pointing into generic library code rather than at the caller
who chose an unsuitable `T`. This is a well-known, deliberate ergonomic trade in Zig
(simplicity of "just duck-type it") that Metel's aspect system has already rejected in
favour of checked bounds. Adopting comptime's *execution model* for generics does not
require adopting Zig's *checking discipline* along with it — but naming them as "the
same mechanism" without saying so risks implying it does.

**Recommendation:** keep `<T: Clone>`-style bounds checked structurally at the generic
function's own definition, as RFC-0061 already establishes for structural types —
implemented as a constraint verified against `typeinfo(T)` and aspect-impl lookups
*before* any instantiation is permitted, not as a property only discovered during
comptime evaluation of the body. Concretely:

```metel
fun first<T: Clone>(arr: T[]) -> Perhaps<T> {
    // comptime T: type, with `T: Clone` checked against typeinfo(T)/impl lookup
    // at this definition, exactly as RFC-0061's bound checker already does today —
    // not deferred to whichever call site happens to instantiate T
    if (array_len(arr) == 0) { return None; }
    return Perhaps::Some { value: arr[0] };
}
```

This gets Metel Zig's single-execution-model economy (one evaluator, staged, no
separate generics-codegen machinery to specify) without Zig's weaker error locality.
The cost is that this checked layer is itself new design work: neither Zig (which has
no such layer) nor RFC-0061 (which specifies checked bounds but not a comptime
substitution mechanism underneath them) hands it over pre-assembled.

---

## 2. Reflection: `typeinfo(T)`, and its relationship to structural records

`typeinfo(T)` (Zig calls its equivalent `@typeInfo`) returns an ordinary, inspectable
comptime value describing `T`'s shape. `@` is not reused for this name because `@`
already denotes allocators in Metel (RFC-0063 and the allocator-handle cluster);
colliding an established sigil with an unrelated meaning is worth avoiding even though
Zig itself overloads `@` for both.

`typeinfo` cannot be a single record type, because different kinds of type have
different shapes to describe — a struct has fields, an enum has variants, a primitive
has a bit width and signedness. That is a sum type, which is what Metel's enums are
for:

```metel
enum TypeInfo {
    Struct { row: Row },
    Enum { variants: (name: Symbol, fields: Row)[] },
    Int { bits: i64, signed: boolean },
    Float { bits: i64 },
    Pointer { target: type },
    // ...
}
```

The `Struct` arm's payload, however, is exactly what RFC-0090's **row** concept already
models: a name-to-type mapping, already used there for `HasField`/`Lacks` bound
satisfaction and Tier 2/3 record conversion. Rather than invent a parallel `FieldInfo[]`
descriptor type for reflection, the struct arm of `typeinfo` should return `T`'s own
row, reified as a comptime value. This gives one concept spanning two phases:
`typeinfo` inspects the row at comptime; `ToRecord`/`FromRecord` (RFC-0090 Tier 2)
converts to/from a value of that row at runtime. A derive function and a runtime
record-conversion are, underneath, working with the same fact about `T`.

This reuse is not free, and surfaces two gaps neither RFC currently resolves:

- **Rows may need metadata they don't currently carry.** Rows as scoped in RFC-0090 are
  presence facts — name/type pairs — used for bound satisfaction and conversion, where
  declaration order and per-field visibility don't matter. Reflection likely needs
  three things rows don't carry today: order, for deterministic codegen (a derived
  `Clone` or `Display` needs a stable field order, not whatever order a set happens to
  iterate in); visibility, to decide whether a comptime function defined outside a
  type's module should see its private fields at all; and each field's `@` attributes
  (RFC-0095), for a derive function to act on `@skip`/`@rename(...)` and similar
  per-field metadata. Whether this means extending the row concept itself with this
  metadata, or defining a reflection-only superset of it, is open.

- **Reflection and the tier system are orthogonal, not layered.** Reflecting a
  struct's shape at comptime grants no *runtime* capability — it is compile-time only,
  in the same category RFC-0090 §7 already resolved for `HasField`-as-bound: implicit,
  available on any struct, regardless of tier. `typeinfo` must work on plain Tier-1
  structs — RFC-0080's own `Point` (§1.3) is a plain struct, and its `Clone` derive
  example requires reflecting it — even though Tier 1 structs never opt into
  `ToRecord`/`FromRecord` at runtime. Comptime reflection therefore should not be gated
  behind the tier-2/3 opt-in that governs runtime record conversion; the two mechanisms
  answer different questions (what does `T` look like at compile time, vs. what can be
  done with a value of `T` at runtime) and should stay decoupled.

---

## 3. Emitting a declaration (single-declaration form)

Comptime code needs a way to **emit a declaration** — specifically, a coherence-checked
`impl Aspect for T` — as a side effect of compile-time evaluation, not just compute a
value or a type. This is the one genuine extension beyond Zig's own model: Zig has no
nominal aspect/impl/coherence system to target (a Zig "generic" function returning a
`type` returns a struct with its methods already inside it), so Zig itself never had to
solve "synthesize an impl of an existing nominal aspect for an existing type." Metel's
aspect system means this is new design work, not a transplant, and it is where this
RFC's soundness questions concentrate (see Open Questions): does normal orphan-rule/
coherence checking (RFC-0060) apply unchanged to an emitted impl? Can a comptime
function emit an impl for a type it does not own?

This RFC specifies only the form needed for aspect derivation: `emit` produces exactly
one declaration (an `impl` block), registered at the point the comptime function
completes. RFC-0094 generalizes this to multiple declarations per comptime function and
to expression-position splicing, needed for macro-like metaprogramming but not for
derive itself.

---

## Pros and cons

**Pros:** one execution model instead of two (no separate macro grammar, no token
stream, no hygiene problem). Unifies with `<T>` generics rather than sitting beside them
as an unrelated feature.

**Cons:** requires `type` to become a first-class comptime value and a reflection
primitive over it — both new to the language, not currently specified anywhere in the
type system (`public/reference/spec/types.md`'s "Generics" section has no notion of
`type`-as-value). Emitting a coherence-checked impl from arbitrary user code raises
soundness questions not yet worked out. The row-reuse in §2 is itself not yet fully
specified (ordering, visibility, attributes).

---

## Open Questions

1. **Row metadata for reflection.** Do rows need declaration order, per-field
   visibility, and each field's `@` attributes (RFC-0095) added to their definition in
   RFC-0090, or should `typeinfo`'s `Row` be a reflection-specific superset that
   carries all three without changing the row concept used for `HasField`/`Lacks`/Tier
   2-3? Blocks a concrete `typeinfo` spec.
2. **`emit` soundness.** Does ordinary orphan-rule/coherence checking (RFC-0060) apply
   unchanged to an impl emitted by comptime code? Can a comptime function emit an impl
   for a type it does not own (e.g. a third-party library deriving an aspect for a
   stdlib type)? Needs its own worked examples before the mechanism can be specified
   precisely.
3. **How does declaration-site bound checking compose with comptime substitution?** §1
   recommends keeping RFC-0061's checked-bounds discipline layered on top of comptime
   type parameters, rather than drifting toward Zig's use-site duck typing. Is that
   check a distinct compiler pass that runs before any comptime evaluation of the body,
   or is it itself expressible as comptime code? Neither Zig nor RFC-0061 specifies this
   composition today — it is new design work either way.
4. **Is the `<T>`-generics/comptime unification required, or just recommended?** This
   RFC works even if `<T>` generics remain a separate, unrelated mechanism — the
   unification in §1 is presented as desirable (one explanation instead of two, and a
   concrete mechanism underneath RFC-0008's assumed monomorphisation) but not
   load-bearing for derive itself. Confirm whether pursuing it is in scope here or
   belongs in a generics-specific RFC — no such RFC currently exists;
   `public/reference/spec/types.md`'s "Generics" section is the only current
   specification.
5. **Incremental rollout.** Can `typeinfo`'s `TypeInfo` enum be introduced starting with
   only the `Struct` arm (sufficient for every aspect in RFC-0093's initial derivable
   set), deferring `Enum`/`Int`/`Pointer`/... arms until something actually needs them?
   Or does the sum type need to be specified in full before any of it ships, to avoid a
   breaking change to `TypeInfo` later?

---

## Timing Recommendation

Deferred to **v0.5+**, after the core language (generics, aspects, concurrency, memory
model) is stable. `type`-as-comptime-value and `typeinfo` reflection (with Open
Question 1 resolved) must exist before any derive function can be written (RFC-0093) —
RFC-0080's `Clone` derive is blocked on this.

Minimum action before v0.5: reserve `comptime` as a keyword.

---

## References

- Language spec: `public/reference/spec/types.md` ("Generics" section — no current
  notion of `type`-as-value)
- RFC-0090 (Structural Records — Rows and Tiers) — row concept reused by `typeinfo`'s
  struct arm (§2); its Tier system is the model for reflection vs. runtime conversion
- RFC-0008 (Aspect Objects) — states "static dispatch (generics + monomorphisation)" as
  Metel's existing default, confirming §1's generics-as-comptime-sugar unification
- RFC-0061 (Structural Aspect Bounds) — the existing bound checker §1 recommends
  preserving alongside comptime substitution
- RFC-0060 (Aspect Impl Coherence) — coherence/orphan rules `emit` must respect (Open
  Question 2)
- RFC-0080 (Standard Library Aspects) — `Clone`'s derive is the concrete first test
  case for this RFC's mechanism (via RFC-0093)
- RFC-0093 (Derive Registration) — depends on this RFC
- RFC-0094 (Comptime Metaprogramming) — depends on this RFC, generalizes `emit`
- Prior art: Zig `comptime`, `@typeInfo`, `comptime T: type`

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
