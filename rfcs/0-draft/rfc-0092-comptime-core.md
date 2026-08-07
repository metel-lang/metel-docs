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
> collectively — see `public/rfcs/5-superseded/rfc-0012-derived-aspects.md`.
>
> **Reconciled with RFC-0055 the same day**, after `public/rfcs/INDEX.md` surfaced an
> overlap that had gone undiscovered through this RFC's entire drafting: RFC-0055
> ("Comptime," draft since 2026-06-05) already covers foundational execution-model
> ground this RFC had silently assumed — `comptime let` for constants, `comptime fun`'s
> general restrictions (no I/O, no non-comptime calls, a recursion limit), and
> `comptime if`. §0 below folds that content in. RFC-0055's own Open Question 4 ("can
> comptime code inspect whether a type implements an aspect... could replace some uses
> of conditional `impl` blocks") is answered more precisely by RFC-0093's `@derive`
> registration than by RFC-0055's own sketch. RFC-0055 is now superseded by this RFC
> (plus RFC-0093 for OQ-4 and RFC-0095 for the `comptime if`/`@cfg` overlap RFC-0055's
> design already anticipated without RFC-0095 knowing it) —
> `public/rfcs/5-superseded/rfc-0055-comptime.md`.
>
> **RFC-0083 folded in, 2026-07-12.** RFC-0083 (Public Value Exports, `pub let`) had
> reached `3-integrated` on the strength of a "constant expression" concept it never
> specified — it deferred that definition to this RFC while this RFC only existed as a
> pending cross-RFC question (§0 below, "added 2026-07-11"). Codeberg issue #539 (its
> implementation tracking) was closed without implementing RFC-0083 as drafted, since
> doing so would have meant building a bespoke restricted evaluator now, then
> reconciling it against `comptime let` later. §0a below resolves the pending question
> directly: `pub` value exports are `pub` applied to `comptime let`, not a
> parallel concept. RFC-0083 is superseded by this RFC —
> `public/rfcs/5-superseded/rfc-0083-public-value-exports.md`.

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

## 0. Execution model: `comptime let`, `comptime fun`, `comptime if`

Before `type`-as-value (§1) or reflection (§2) mean anything, comptime needs a base
execution model — folded in here from RFC-0055, which specified this ground first and
was never cross-checked against while this RFC was drafted (see the note above).

**`comptime let`.** A binding whose initializer is evaluated at compile time:

```metel
comptime let MAX_CONNECTIONS: i64 = 1024;
comptime let BUFFER_SIZE: i64 = MAX_CONNECTIONS * 64;
```

Motivating cases RFC-0055 identified and this RFC inherits: derived constants (a
buffer size computed from a protocol limit, rather than duplicated or computed at
runtime), and compile-time lookup tables (`comptime let SIN_TABLE: [f64; 256] = ...`) —
zero runtime cost, since the value is fully computed before any generated code runs.
Also the natural source of `N` in fixed-size array types (`[T; N]`, RFC-0053/RFC-0084):
`comptime let CHUNK: i64 = 64; let buf: [u8; CHUNK] = [0; CHUNK];`.

### 0a. `pub` on `comptime let`: public value exports

RFC-0083 (Public Value Exports, superseded by this RFC — see the note at the top)
identified a real, independent need: a named value — an error code, a default
timeout, a protocol limit — exported from a module and imported by name, the same way
`struct`/`enum`/`fun`/`aspect` already can be:

```metel
// config.mtl
pub comptime let MAX_CONNECTIONS: u64 = 1024;
pub comptime let DEFAULT_TIMEOUT_MS: u64 = 5000;

// importer
import config::MAX_CONNECTIONS;
fun accept(current: u64) -> boolean { current < MAX_CONNECTIONS }
```

RFC-0083's draft required `pub let` initializers to be "constant expressions" —
literals, arithmetic on literals, struct constructors over other constant
expressions — without tying that restriction to any actual language mechanism; it
deferred the full definition to this RFC, while this RFC only carried it as an open
question. That was circular, not just incomplete: neither RFC specified the thing the
other depended on. `comptime let` already *is* the restricted, order-independent,
compile-time-evaluated binding RFC-0083 was describing by another name — so the
resolution is that public value exports are `pub` applied directly to `comptime let`,
not a second, parallel "constant expression" concept living under plain `let`:

- **Visibility composes with `comptime let` exactly as it already does with
  `struct`/`enum`/`fun`/`aspect`** (module spec, "Visibility") — no new visibility rule,
  just a new declaration kind `pub` can attach to.
- **Import/export syntax is unchanged.** `import config::MAX_CONNECTIONS;` and
  `export config::MAX_CONNECTIONS;` work exactly as for any other `pub` item.
- **There is no `pub comptime var`** — `comptime let` has no mutable form at all
  (mirroring RFC-0083's "no `pub var`" rule, but for a stronger reason: comptime
  bindings aren't mutable regardless of visibility).
- **Ordinary (non-`pub`, non-`comptime`) module-level `let`/`mut` is untouched by this.**
  Their evaluation order remains unspecified — an implementation detail (evaluate
  top-to-bottom in declaration order; forward reference is a runtime error), not
  resolved by this RFC, exactly as RFC-0083 itself left it.

This also retires RFC-0083's own Unresolved Question 2 (added 2026-07-11, asking the
same "desugar to `comptime let`, or a separate evaluator?" question from the other
side) — answered: desugar, no separate evaluator.

**`comptime fun`.** A function evaluable at compile time. The annotation means "the
compiler *can* evaluate this," not "this may only be called at compile time" — an
ordinary call site at runtime is still legal:

```metel
comptime fun pow2(n: i64) -> i64 {
    var result = 1;
    var i = 0;
    while (i < n) { result *= 2; i += 1; }
    result
}

comptime let PAGE_SIZE: i64 = pow2(12);   // 4096, computed at compile time
```

Restrictions, inherited from RFC-0055: no I/O builtins (`print`, `println`); no heap
allocation via runtime allocators (comptime needs its own scratch storage, distinct
from `@a T`'s runtime allocators — see Open Question 6); no calls to non-comptime
functions; no recursion beyond a compiler-enforced depth limit (Open Question 5).
`@derive(Aspect)`-tagged functions (RFC-0093) and `emit` (§3) are comptime functions in
this sense, with `emit` as an additional capability layered on top, not a different
execution model.

**`comptime if`.** A conditional whose condition is a comptime-known value is resolved
at compile time; the untaken branch is never type-checked or emitted:

```metel
comptime let IS_64BIT: boolean = target_pointer_width() == 64;

fun word_size() -> i64 {
    comptime if (IS_64BIT) { 8 } else { 4 }
}
```

This is the mechanism RFC-0095's Open Question 4 already speculates might subsume
`@cfg` — RFC-0055 had already reached the same conclusion independently
("conditional boolean conditions fold cleanly into the generated code with no
overhead"), without RFC-0095 knowing RFC-0055 existed. Both RFCs converging on the same
answer from opposite starting points is worth treating as *more* confidence in it, not
double work to reconcile — no content conflict here, just independent confirmation.

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
    return Perhaps::Some { value = arr[0] };
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
    Struct { row = Row },
    Enum { variants = (name: Symbol, fields: Row)[] },
    Int { bits = i64, signed = boolean },
    Float { bits = i64 },
    Pointer { target = type },
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
`extend T: Aspect` — as a side effect of compile-time evaluation, not just compute a
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
6. **Recursion and termination for `comptime fun`** (inherited from RFC-0055 OQ-1).
   Should Metel allow recursive comptime functions with a compiler-enforced depth
   limit (Zig's approach), or forbid comptime recursion entirely (forcing comptime
   loops to cover all cases, at the cost of some recursively-natural programs being
   inexpressible as comptime)? Neither this RFC nor RFC-0055 settles this.
7. **Comptime and allocation** (inherited from RFC-0055 OQ-2). Can comptime functions
   allocate at all? §0 asserts comptime needs "its own scratch storage, distinct from
   `@a T`'s runtime allocators" without specifying what that storage is or how it's
   bounded — does comptime get its own dedicated allocator kind, or is heap-shaped
   allocation simply disallowed in comptime functions, with only stack-like/scratch
   values permitted?
8. **Comptime error messages.** When a comptime computation fails (division by zero,
   an assertion, an unsupported type reaching `comptime if`), the error must report the
   original comptime call site, not the internals of whatever comptime function was
   evaluating — otherwise error quality regresses badly relative to ordinary runtime
   errors. RFC-0094 §3 specifies span-tracking for comptime-*parsed strings*
   specifically; this is the same concern for comptime *execution* errors generally,
   inherited from RFC-0055 OQ-5, and not obviously the same mechanism.

---

## Timing Recommendation

Deferred to **v0.5+**, after the core language (generics, aspects, concurrency, memory
model) is stable. `type`-as-comptime-value and `typeinfo` reflection (with Open
Question 1 resolved) must exist before any derive function can be written (RFC-0093) —
RFC-0080's `Clone` derive is blocked on this.

Minimum action before v0.5: reserve `comptime` as a keyword.

**Cost of the §0a fold, noted honestly.** Prior strategy reports (e.g.
`reports/strategy/strategic-overview-2026-07-01.md`,
`reports/strategy/strategic-overview-2026-07-05.md`) categorized `pub let` (RFC-0083)
as a small, mechanical, near-term, independently-parallelizable change — a three-file
diff, unblocked by nothing else. Folding it into this RFC means public value exports
now wait on `comptime let` reaching a settled, implemented state — this RFC's own
target — rather than shipping on its own timeline. That's a real cost, accepted here
because the alternative (implementing RFC-0083's undefined "constant expression"
restriction now) would either duplicate `comptime let`'s evaluator or produce a
different-but-similar restricted evaluator to reconcile later. If the wait proves too
costly in practice, the base `comptime let` mechanism (§0/§0a only, not `type`-as-value
or reflection) could in principle ship ahead of the rest of this RFC — that's a
sequencing question for whoever schedules the work, not resolved here.

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
- RFC-0055 (Comptime, superseded) — original design sketch; §0's execution model
  (`comptime let`/`fun`/`if`) and Open Questions 6-8 are inherited from it, reconciled
  2026-07-09 after `INDEX.md` surfaced the overlap
- RFC-0053 (Fixed-Size Array Type) / RFC-0084 (Fixed-Size Array Syntax) — `[T; N]`'s `N`
  is the concrete motivating case for `comptime let` (§0)
- RFC-0083 (Public Value Exports, superseded) — original `pub let` design; folded into
  §0a 2026-07-12, its Codeberg tracking issue (#539) closed unimplemented in favor of
  this RFC's `pub comptime let` mechanism
- Prior art: Zig `comptime`, `@typeInfo`, `comptime T: type`

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
