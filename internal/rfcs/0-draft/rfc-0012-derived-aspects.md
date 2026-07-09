---
id: rfc-0012
title: "Attributes, Metadata, Macros, and Derived Aspects"
date: '2026-05-21'
updated: '2026-07-09'
status: draft
target:
---

> **Rewritten 2026-07-09.** Previously presented four implementation paths for derive
> with no preference among them. This revision recommends **Path D — comptime derive**
> as the primary mechanism and rewrites the RFC around it; Paths A/B/C are kept as
> alternatives considered, not as live options of equal standing. This followed a
> Zig-style comptime design discussion in `reports/substructural-types/`, which also
> surfaced that `typeinfo`'s struct-describing arm should reuse the row concept from
> `structural-records.md` rather than invent a parallel descriptor type — folded in
> below. RFC-0080 (Standard Library Aspects) was moved back from accepted to
> under-review the same day: its §1.3 had specified `Clone` derive using
> `#[derive(Clone)]`, a syntax this RFC's Alternatives Considered section explicitly
> rejects. §1.3 now uses `derives Clone` (this RFC's chosen surface syntax) provisionally;
> RFC-0080 is blocked on this RFC's decision, not the reverse.

## Summary

This RFC proposes **comptime derive** as Metel's mechanism for automatically generating
aspect implementations: derive is not a special compiler feature, but ordinary code —
written in Metel itself — that runs at compile time over a reflected description of a
type's structure and emits a coherence-checked `impl` block. This follows Zig's
`comptime` model directly: there is no separate macro language, no token stream, no
hygiene problem, because compile-time code and run-time code are the same language,
staged differently. It requires two things new to Metel: `type` as a first-class
comptime value, and a reflection primitive over it.

This does not replace the rest of the meta-feature layer. The `@` attribute/metadata
system (`@inline`, `@cfg`, `@allow`, `@doc`) remains in scope, unaffected — those are
compiler hints and conditional compilation, not code generation, and gain nothing from
comptime. What comptime derive does replace is the need for a general **macro** system
(Path B) to get extensible derive: a library can make an aspect derivable by writing an
ordinary comptime function, not a procedural macro operating on syntax.

All features in this RFC remain tentatively deferred to **v0.5+**, after the core
language (generics, aspects, concurrency, memory model) is stable — comptime derive
specifically also requires `type`-as-value and reflection to exist first, which is new,
non-trivial design surface in its own right (see Open Questions).

---

## Motivation

### Derived aspect implementations

Writing `impl Eq for Point { fun eq(self, other: Point) -> boolean { self.x == other.x && self.y == other.y } }` by hand for every struct is tedious and error-prone. A derive mechanism generates these implementations structurally — field-by-field for structs, variant-by-variant for enums. The primary use cases are `Eq`, `Ord`/`Comparable`, `Display`, `Clone`, `Hash`, and `Linear` (for types that are linear by structure rather than explicit declaration).

The question this RFC exists to answer is not *whether* derive is useful — that much is
uncontested and already assumed by RFC-0080 — but *what kind of mechanism* generates
the impl: a closed list the compiler special-cases, or open code that anyone can write.

### Attributes and metadata

Beyond derive, a general attribute/metadata system enables:
- Compiler hints (`@inline`, `@cold`, `@must_use`)
- Conditional compilation (`@cfg(...)`)
- FFI annotations (`@extern("C")`)
- Lints and suppressions (`@allow(...)`, `@deny(...)`)
- Documentation metadata (`@doc(...)`)

Without a principled attribute syntax, these accumulate as ad-hoc keywords or magic comments. A single syntax form (`@`) handles all of them uniformly. This part of the RFC is independent of the derive mechanism and is unaffected by the Path D recommendation below.

### Macros — superseded for derive, still open for everything else

A general macro system enables syntactic abstraction — generating code from a compact
notation, operating on unexpanded syntax. Comptime derive (Path D) gets derive's
extensibility without one: a comptime function operates on ordinary, already-typed
values (a reflected `type`), not on syntax trees, so there is no grammar to define, no
hygiene to get right, no separate expansion phase to specify. Whether Metel wants a
*general* macro system — for syntactic abstraction beyond derive, e.g. compact
notations for repetitive expressions — remains an open question, but it is no longer a
prerequisite for extensible derive, which was macros' strongest motivating use case.

---

## Proposal: Comptime Derive (Path D)

Derive is an ordinary function that runs at compile time (`comptime`) over a reflected
description of a type's structure and produces an `impl` block as a value the compiler
registers. There is no macro grammar, no token stream, no hygiene problem — comptime
code is the same language as runtime code, staged earlier, because the same evaluator
runs it.

### 1. `type` as a first-class comptime value

A `type` (e.g. `Point`, `i64`, `Perhaps<T>`) can be bound, passed, and returned like any
other comptime-known value. This is also the natural explanation for Metel's existing
`<T>` generics (spec: `public/reference/spec/types.md`, "Generics"): Zig does not have
`<T>`-style generics as a mechanism separate from comptime — `fun first(comptime T: type, arr: T[])`
*is* how Zig spells a generic function, because a compile-time-known `type` parameter
is just an ordinary parameter, staged. If Path D is adopted, `fun first<T>(arr: T[])`
would most naturally be sugar over the same comptime type-parameter mechanism, rather
than a second, independently-specified feature living alongside it. This is not
required for Path D to work in isolation, but leaving `<T>` generics unrelated to
comptime would mean maintaining two separate explanations for what is, underneath, the
same idea.

### 2. Reflection: `typeinfo(T)`, and its relationship to structural records

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

The `Struct` arm's payload, however, is exactly what `structural-records.md`'s **row**
concept already models: a name-to-type mapping, already used there for `HasField`/`Lacks`
bound satisfaction and Tier 2/3 record conversion. Rather than invent a parallel
`FieldInfo[]` descriptor type for reflection, the struct arm of `typeinfo` should return
`T`'s own row, reified as a comptime value. This gives one concept spanning two phases:
`typeinfo` inspects the row at comptime; `ToRecord`/`FromRecord` (structural-records.md
Tier 2) converts to/from a value of that row at runtime. A derive function and a
runtime record-conversion are, underneath, working with the same fact about `T`.

This reuse is not free, and surfaces two gaps neither document currently resolves:

- **Rows may need metadata they don't currently carry.** Rows as scoped in
  `structural-records.md` are presence facts — name/type pairs — used for bound
  satisfaction and conversion, where declaration order and per-field visibility don't
  matter. Reflection likely needs both: order, for deterministic codegen (a derived
  `Clone` or `Display` needs a stable field order, not whatever order a set happens to
  iterate in); visibility, to decide whether a comptime function defined outside a
  type's module should see its private fields at all. Whether this means extending the
  row concept itself with this metadata, or defining a reflection-only superset of it,
  is open.

- **Reflection and the tier system are orthogonal, not layered.** Reflecting a
  struct's shape at comptime grants no *runtime* capability — it is compile-time only,
  in the same category `structural-records.md` §8 already resolved for `HasField`-as-
  bound: implicit, available on any struct, regardless of tier. `typeinfo` must work on
  plain Tier-1 structs — RFC-0080's own `Point` (§1.3) is a plain struct, and its
  `Clone` derive example requires reflecting it — even though Tier 1 structs never
  opt into `ToRecord`/`FromRecord` at runtime. Comptime reflection therefore should not
  be gated behind the tier-2/3 opt-in that governs runtime record conversion; the two
  mechanisms answer different questions (what does `T` look like at compile time, vs.
  what can be done with a value of `T` at runtime) and should stay decoupled.

### 3. Emitting the impl

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

### Worked example

```metel
comptime fun derive_clone(comptime T: type) {
    let fields = typeinfo(T).row;   // T's row, reified as a comptime value
    emit impl Clone for T {
        fun clone(self: &T) -> T {
            // built field-by-field from `fields` by ordinary comptime code —
            // a loop generating a constructor expression, not a macro template
        }
    }
}
```

Surface syntax at the call site stays exactly what RFC-0080 §1.3 already uses
provisionally: `struct Point derives Clone { x: f64, y: f64 }`. `derives Clone` parses
as Path C's syntax and resolves to a standard-library comptime function per Path D —
closed-list ergonomics today, with an open path to user-defined derivable aspects later,
with no syntax change required when that lands.

### Pros and cons

**Pros:** open/extensible like Path B (any library can write a comptime function that
emits an impl), without Path B's macro-hygiene and token-stream complexity — there is
only one language, not two. Subsumes the `linear` keyword vs. derive question (Open
Question 6) for free: `derives Linear` becomes an ordinary comptime function inspecting
field linearity via `typeinfo`, not a special case. Unifies with `<T>` generics rather
than sitting beside them as an unrelated feature.

**Cons:** requires `type` to become a first-class comptime value and a reflection
primitive over it — both new to the language, not currently specified anywhere in the
type system (`public/reference/spec/types.md`'s "Generics" section has no notion of
`type`-as-value). Emitting a coherence-checked impl from arbitrary user code raises
soundness questions not yet worked out. Larger design surface than Path A or C in
isolation, though smaller than a full Path B macro system, and the row-reuse in §2
above is itself not yet fully specified (ordering, visibility).

---

## Derivable Aspects (initial standard-library set)

Regardless of how much of Path D's extensibility ships initially, the standard library
should provide comptime derive functions for at least:

| Aspect | Behaviour |
|---|---|
| `Eq` | Field-by-field equality |
| `Ord` / `Comparable` | Lexicographic field ordering |
| `Display` | Structural `to_string` (see Open Question 3) |
| `Clone` | Deep field-by-field clone (RFC-0080 §1.3) |
| `Hash` | Structural hash combining all fields |
| `Linear` | Marks the type linear if all fields are linear (see RFC-0024) |

Under Path D, `Linear` as a derivable aspect is not merely an alternative to the
`linear` keyword — it is the same mechanism as the others, an ordinary comptime
function reading `typeinfo(T)` and checking each field's linearity, rather than a
bespoke compiler rule.

---

## Preferred Syntax: `@`, for non-derive attributes

The preferred grammar symbol for attributes and metadata *other than derive* is `@`.
This is distinct from all current Metel operators and consistent with annotation syntax
in several modern languages (Java, Python decorators, Zig's `@builtins`).

```metel
struct Point derives Clone, Eq {
    x: Float,
    y: Float,
}

@inline
fun fast_path(n: Int) -> Int { n * 2 }

@cfg(target = "linux")
fun platform_init() { ... }

@allow(unused)
let _debug_value = compute();
```

Multiple attributes stack vertically, one per line, before the item they annotate.
Attributes apply to the next declaration or binding — they do not apply to
expressions. Derive uses `derives`, not `@derive(...)` — see Proposal above.

The `@` form is preferred over Rust's `#[...]` because:
- `#` is visually associated with comments in many languages; `@` is unambiguously an annotation sigil
- `@` is already unused in Metel's grammar (outside allocators, which use it in a different grammatical position)
- `@(...)` is unambiguous as a prefix — no bracket/brace confusion with other constructs

---

## Alternatives Considered

### Path A — Compiler-built-in derive (no macro system)

Derive is a closed set of structurally derivable aspects known to the compiler, with no
user extensibility. Simple to implement, guaranteed-correct, but third-party libraries
can never add derivable aspects. Superseded by Path D, which gets the same closed
initial set (see Derivable Aspects above) without foreclosing extensibility later.

### Path B — Attribute macros (procedural macros)

`@derive(Aspect)` expands to an `impl` block generated by a macro associated with
`Aspect` — Rust's model. Fully extensible, but procedural macros are notoriously
complex to write and maintain, and require a full macro system (token streams, hygiene)
as a prerequisite. Superseded by Path D, which reaches the same extensibility by
running ordinary staged code over reflected values instead of syntax.

### Path C — Derive as a language keyword, closed

Derive expressed with a `derives` keyword rather than the `@` attribute system, but
still a closed, compiler-known list with no extensibility:

```metel
struct Point derives Eq, Ord, Display { x: Float, y: Float }
```

Ergonomic and self-contained, but does not scale to user-defined derivable aspects.
Not superseded so much as **absorbed**: this is the exact surface syntax Path D uses,
with the compiler-known list becoming the standard library's initial comptime derive
functions rather than a hardcoded special case. Path C is what a user of Path D sees
before writing a custom derivable aspect.

### `#[...]` Rust-style attributes

Familiar to Rust programmers but visually ambiguous with comments (`#`). Rejected in
favour of `@`. (RFC-0080 §1.3 briefly used this syntax for `Clone`'s derive example;
corrected 2026-07-09 to `derives Clone`, consistent with this RFC.)

### Lisp-style macros (hygienic, syntax-level)

Full hygienic macro system allowing arbitrary syntactic transformation over unexpanded
syntax. Maximum power, maximum complexity — well outside the scope of a v0.5 feature
for a language at v0.1, and no longer motivated by derive specifically now that Path D
covers that case. Not ruled out as a distant future direction for syntactic abstraction
unrelated to derive.

### No attribute syntax — ad-hoc keywords only

Each compiler directive is its own keyword or syntax form. Avoids designing a general
system but leads to keyword proliferation and inconsistency. Rejected as a long-term
position; acceptable only before v0.5 when no attribute-dependent features have shipped.

---

## Interaction with Other RFCs

### `structural-records.md` (design report, not yet an RFC)

`typeinfo(T)`'s struct arm reuses the row concept defined there for `HasField`/`Lacks`
and Tier 2/3 record conversion (§2 above). This is the load-bearing dependency for Path
D's reflection design and is not yet reconciled in either direction — row ordering and
visibility metadata, needed for reflection, are not currently specified there either.

### RFC-0080 (Standard Library Aspects)

`Clone`'s derive (§1.3) is the concrete first test case for this RFC's mechanism.
RFC-0080 was moved back to under-review 2026-07-09 pending this RFC's resolution, and
currently spells derive as `derives Clone` provisionally, matching the syntax this RFC
recommends regardless of whether the underlying mechanism is Path C or Path D.

### RFC-0024 (Linear Types)

The `linear` keyword on struct/enum declarations could be replaced by `derives Linear`
resolving to a comptime function per Path D. The keyword form is simpler and available
sooner; the derive form is more uniform and consistent with every other derivable
aspect once Path D lands. Open question for RFC-0024's final form.

### RFC-0001 (Pointers) and RFC-0026 (Unsafe Blocks)

`@extern("C")` for FFI function signatures (RFC-0026 open question 4) uses the `@`
attribute syntax defined here. The attribute system is a soft prerequisite for a clean
FFI story; unaffected by the Path D recommendation.

### RFC-0009 (Module System)

`@pub`, `@cfg`, and documentation attributes interact with the module system's
visibility model. Also relevant to Path D directly: reflection's need for per-field
visibility (§2 above) means `typeinfo` and the module system's privacy rules are not
fully independent.

### RFC-0011 (Operator Overloading)

Deriving `Eq` and `Ord` generates implementations of the operator aspects. RFC-0011
must be accepted before derived `Eq`/`Ord` can be implemented, regardless of mechanism.

---

## Open Questions

1. **Row metadata for reflection.** Do rows need declaration order and per-field
   visibility added to their definition in `structural-records.md`, or should
   `typeinfo`'s `Row` be a reflection-specific superset that carries this without
   changing the row concept used for `HasField`/`Lacks`/Tier 2-3? Blocks a concrete
   `typeinfo` spec.

2. **`emit` soundness.** Does ordinary orphan-rule/coherence checking (RFC-0060) apply
   unchanged to an impl emitted by comptime code? Can a comptime function emit an impl
   for a type it does not own (e.g. a third-party library deriving an aspect for a
   stdlib type)? This is the crux of Path D's "cons" above and needs its own worked
   examples before the mechanism can be specified precisely.

3. **Is the `<T>`-generics/comptime unification required, or just recommended?** Path D
   works even if `<T>` generics remain a separate, unrelated mechanism — the unification
   in §1 is presented as desirable (one explanation instead of two) but not load-bearing
   for derive itself. Confirm whether pursuing it is in scope for this RFC or belongs in
   a generics-specific RFC.

4. **Incremental rollout.** Can `typeinfo`'s `TypeInfo` enum be introduced starting with
   only the `Struct` arm (sufficient for every aspect in the initial derivable set),
   deferring `Enum`/`Int`/`Pointer`/... arms until something actually needs them? Or
   does the sum type need to be specified in full before any of it ships, to avoid a
   breaking change to `TypeInfo` later?

5. **`@` attribute scope.** What items can be annotated — struct/enum declarations, function declarations, `let` bindings, individual fields? Field-level attributes (e.g. `@skip` on a field to exclude it from `Display`) are useful but add parsing complexity.

6. **`Display` vs `From` for string conversion.** `print` currently only accepts `String`. When aspects land, `print` should accept any type with a string representation. The question is which aspect owns that conversion:
   - A `Display` aspect (`fun to_string(self) -> String`) implemented by the source type — the natural direction for user-defined types.
   - `String` implementing `From<T>` for each printable type — consistent with the `from` pattern but puts the responsibility on `String`, which cannot know about user-defined types without open dispatch.
   These serve different purposes and should likely remain separate aspects. Resolve before finalising the `print` signature.

7. **Compiler-known attribute registry.** The compiler needs a fixed set of recognised `@` attributes (e.g. `@inline`, `@cfg`, `@allow`). Should unknown `@` attributes be a compile error, a warning, or silently ignored (for forward compatibility)?

8. **`@cfg` and conditional compilation.** Conditional compilation is a significant feature in its own right (platform-specific code, feature flags). Should `@cfg` be in scope for this RFC or a separate one?

9. **`linear` keyword vs `derives Linear`.** Should RFC-0024's `linear` keyword be removed in favour of `derives Linear` once this RFC is accepted? The keyword form is available sooner (v0.3); the derive form is more uniform but requires v0.5+ and Path D's mechanism specifically. A possible migration: accept `linear` keyword now, deprecate in favour of derive when comptime derive lands.

---

## Timing Recommendation

All features in this RFC are **deferred to v0.5+**. The core language must stabilise first:

- Generics and aspects (v0.2) — derive requires aspects to exist, and Path D's `type`-as-value proposal (§1) touches generics directly
- Memory model (v0.3) — `@extern` for FFI requires unsafe blocks (RFC-0026)
- Concurrency (v0.4) — `@cfg` and platform attributes interact with the concurrency model

The `linear` keyword (RFC-0024) is the one meta-adjacent feature that ships early (v0.3) as a plain keyword, to be revisited for derive integration at v0.5.

Path D specifically has a longer critical path than Paths A/C would have had: `type`-
as-comptime-value and `typeinfo` reflection (with the row-metadata question in Open
Question 1 resolved) must exist before any derive function can be written, comptime or
otherwise. RFC-0080's `Clone` derive is blocked on this, not just on syntax.

Minimum action before v0.5: reserve `@` as a grammar token so it cannot be used for other purposes. Reserve `derives` and `comptime` as keywords for the same reason. This prevents a breaking change when the attribute system and comptime derive land.

---

## References

- Language spec: `public/reference/spec/types.md` ("Generics" section — no current notion of `type`-as-value)
- `reports/substructural-types/structural-records.md` — row concept reused by `typeinfo`'s struct arm (§2); §8's implicit/tier-gated split is the model for reflection vs. runtime conversion
- RFC-0011: `docs/internal/rfcs/rfc-0011-operator-overloading.md` — `Eq`/`Ord` derive depends on operator aspects
- RFC-0009: `docs/internal/rfcs/rfc-0009-module-system.md` — visibility and `@cfg` interaction; also field-visibility for reflection (Open Question 1)
- RFC-0024: `docs/internal/rfcs/rfc-0024-linear-types.md` — `linear` keyword vs `derives Linear`
- RFC-0026: `docs/internal/rfcs/rfc-0026-unsafe-blocks.md` — `@extern` for FFI uses attribute syntax
- RFC-0060: `docs/internal/rfcs/rfc-0060-aspect-impl-coherence.md` — coherence/orphan rules `emit` must respect (Open Question 2)
- RFC-0080: `docs/internal/rfcs/rfc-0080-stdlib-aspects.md` — `Clone`/`Send`/`Sync` derive
  and auto-impl semantics depend on this RFC's mechanism; moved back to under-review
  2026-07-09 pending it
- Prior art: Zig `comptime`, `@typeInfo`, `comptime T: type` — no separate macro
  language; `type` as a first-class comptime value; generics unified with comptime
- Prior art (superseded paths): Rust `#[derive(...)]` and proc-macro system, Java annotations, Python decorators

---

## Decision

**Outcome:** *(pending — Path D recommended by this revision, not yet formally accepted)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
