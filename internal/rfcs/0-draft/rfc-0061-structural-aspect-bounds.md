---
id: rfc-0061
title: "Aspect Bounds for Structural Types"
date: '2026-06-11'
status: draft
spec_status: pending
---

## Summary

Define how aspect bounds (`T: Display`) are checked when the argument type is
*structural* — arrays (`i64[]`), tuples, function types, pointers — rather
than a named type or primitive.

Today the static bound check silently skips structural types and the runtime
formatter cannot display them, so `println([1, 2, 3])` typechecks and then
panics at runtime — exactly the failure mode the Display bound (sprint 22)
was added to eliminate for named types.

This RFC proposes two phases:

1. **Phase 1 (immediate, small):** structural types *fail* aspect bounds at
   compile time, because no implementation for them can exist. This closes
   the static hole truthfully.
2. **Phase 2 (feature):** generic impls (`impl<T> …`) plus impl targets for
   structural type constructors, so std::core can provide *blanket impls*
   such as `impl<T: Display> Display for T[]` — the Rust/Haskell model —
   with coherence handled by RFC-0060's orphan rule. Tuples are explicitly
   deferred.

---

## Motivation

Sprint 22 gave `print`/`println` a `T: Display` bound, enforced at
construction via `TypeScheme::bounds`. The check resolves the concrete
argument to a type *name* and consults the aspect-impl registry:

- Named types and primitives: checked. `println(my_struct)` without a
  Display impl is a compile-time `T0012`.
- Structural types: **skipped** (`check_type_satisfies_bounds` returns `Ok`
  for any shape with no name), with the stated rationale that "the runtime
  remains the backstop".

The rationale is hollow: `value_to_display_string` covers only primitives,
`boolean`, `Char`, and `String`. There is no runtime backstop — a structural
type in a Display position is a *guaranteed* `R0009` panic that the
typechecker waves through. The skip-rule exists only because the bound
checker has no way to even ask "does `i64[]` implement Display?": the
aspect-impl registry is keyed by type name, and structural types have none.

Meanwhile users will reasonably expect `println([1, 2, 3])` to work — every
mainstream language prints collections one way or another.

### How other languages handle this

| Strategy | Languages | Mechanism |
|---|---|---|
| Blanket impls on structural constructors | Rust, Haskell | `instance Show a => Show [a]`; `impl<T: Debug, const N: usize> Debug for [T; N]`. Core library owns the constructors (orphan rule), so coherence holds. Tuples done per-arity (Rust ≤ 12, Haskell ≤ 15). |
| Compiler-builtin structural propagation | SML (`eqtype`), old Swift (`==` on tuples) | The satisfaction relation recurses structurally for a closed set of blessed bounds. Cheap; does not extend to user aspects. |
| Nominal collections + conditional conformance | Swift | `Array` is a nominal struct; `extension Array: Equatable where Element: Equatable`. Structural problem shrinks to tuples/functions. |
| Runtime reflection backstop | Go (`fmt`) | No static gate; reflection prints anything. |

Metel is already half-way down the Swift road (`List<T>` is a nominal struct
in core.mtl as of sprint 22), and RFC-0060 already defines the coherence
discipline the Rust road needs. This RFC takes the Rust/Haskell strategy for
arrays, keeps `List<T>` on the nominal road, and defers tuples like everyone
else did.

---

## Background: current behaviour

- `check_type_satisfies_bounds` (`typechecker/construction.rs`): maps the
  concrete `Type` to a name (`Named` or primitive); anything else returns
  `Ok(())` unchecked.
- Aspect impls are recorded per type *name* (`register_aspect_impl(String,
  String, Vec<Type>)`); there is no representation for "Display for `T[]`".
- Generic impls do not exist: `impl<T> …` has no syntax, and registry Pass 2
  stores aspect type args containing generic params verbatim as
  `Named("T")`, which breaks lookups (the standing `TODO(generic-impl)` in
  `registry.rs`).
- Runtime method dispatch on structural receivers exists in embryo:
  `RuntimeTypePattern::{Str, Array}` pattern methods serve `"s".len()` and
  `arr.len()`.
- `value_to_display_string` supports primitives only; `format_value` (the
  `dbg` formatter) supports everything, including arrays and structs.

---

## Design

### Phase 1 — close the static hole (no new features)

`check_type_satisfies_bounds` stops skipping shapeless types: if the
concrete type has no name **and no structural impl rule applies** (none
exist yet in Phase 1), the bound fails with a precise diagnostic:

```
[T0012] `i64[]` does not implement `Display` (required by `println`);
arrays do not implement aspects yet
```

This converts today's guaranteed runtime panic into a compile error. It is a
breaking change only for programs that were already broken (they panicked at
runtime). No fixture in the current suite prints a structural type.

### Phase 2 — blanket impls for structural constructors

Three pieces, in dependency order:

**1. Generic impls (`impl<T> … for …<T>`)** — prerequisite, independently
valuable. Syntax:

```metel
impl<T: Display> Display for List<T> {
    fun to_string(&self) -> String { … }
}
```

The registry gains *conditional impl* records: `(constructor, aspect,
elem-bound-list)` instead of only concrete `(name, aspect, type-args)`.
`has_aspect_impl`-style queries become recursive: `List<i64>: Display` holds
iff a conditional record matches `List` and `i64: Display` holds. This also
resolves the standing `TODO(generic-impl)`.

**2. Structural impl targets** — allow the impl target to be a structural
type expression:

```metel
// std::core
impl<T: Display> Display for T[] {
    native(@std.core.array_to_string) fun to_string(&self) -> String;
}
```

The conditional-impl record keys on the constructor *shape* (`Array`), not a
name. The runtime registers the method under the existing
`RuntimeTypePattern::Array` mechanism (extended to carry aspect membership),
and `value_to_display_string` grows an array case that recursively formats
displayable elements (`[1, 2, 3]`).

**3. Coherence** — RFC-0060's orphan rule extends naturally: the structural
constructors (`T[]`, tuples, function types) are *owned by std::core*. A
user impl for a structural target is permitted only when the **aspect** is
local (same rule as for foreign named types). std::core's blanket
`Display`/`From` impls therefore cannot be shadowed or duplicated.

With Phase 2, the Phase 1 hard-fail self-repairs: the bound check consults
the conditional-impl records, finds `Display for T[]`, recurses into the
element type, and `println([1, 2, 3])` compiles *and prints*.

### What this deliberately copies from Rust

Rust implements `Debug` for arrays/tuples but **not** `Display`, arguing
collections have no canonical human format. Metel's `dbg` already formats
everything (via `format_value`), which is the `Debug` analogue. Whether
std::core should provide `Display for T[]` (making `println([1,2,3])` print
`[1, 2, 3]`) or only the `dbg` route is Open Question 1 — the machinery is
identical either way.

---

## Diagnostics

- Phase 1: `T0012` with a structural-specific hint ("arrays do not implement
  aspects yet" / "function types cannot implement aspects").
- Phase 2: a failed recursive check reports the *innermost* failure:
  `[T0012] Point does not implement Display (required by Display for
  Point[], required by println)`.

---

## Alternatives Considered

**SML-style hardwired propagation** (arrays displayable iff element
displayable, baked into the checker for Display only). Cheapest path to
making `println([1,2,3])` work, and the runtime formatter would be extended
to match. Rejected as the *end state* because it cannot serve user aspects
and creates a blessed-aspect caste; acceptable as an interim only if Phase 2
stalls.

**Keep the skip-rule** (status quo). Rejected: it converts a statically
knowable error into a runtime panic, which is precisely what the sprint-22
Display work was for.

**Nominal-only collections** (push everything through `List<T>`, never bless
`T[]`). Rejected: arrays are a core surface type (literals, `as_slice`,
indexing); pretending they are second-class for aspects contradicts the rest
of the language.

---

## Interaction with other work

- **RFC-0060 (coherence/orphan rule, METEL-186):** Phase 2's coherence story
  is an extension of it; land RFC-0060 first.
- **METEL-185 (SymbolId rekeying):** conditional/structural impl records have
  no type SymbolId; they key on constructor shape. The rekeying design must
  reserve a representation for shape keys (mirroring `RuntimeTypePattern`).
- **Generic impls** benefit `From`/`Iterable` too (e.g. `impl<T> Iterable<T>
  for List<T>` could replace the hand-registered Range impls' pattern).

## Non-Goals

- **Tuples.** Per-arity instances (Rust/Haskell) or variadic generics are
  both out of scope; tuples keep the Phase 1 hard-fail.
- **Function types.** No aspect impls for closures; hard-fail with a clear
  message.
- **User-facing `native` in structural impls** — the array `to_string` host
  binding is std::core-only like every other native.

## Open Questions

1. Should std::core provide `Display for T[]` at all, or follow Rust and
   reserve human-readable formatting for scalars while `dbg` handles
   structure? (Phase 2 machinery is needed either way for user aspects.)
2. Phase 1 timing: ship the hard-fail immediately (sprint 23) or together
   with Phase 2 to avoid a temporary "arrays can never print" window?
3. Should conditional-impl satisfaction be cached per module (the recursive
   check is exponential-free but repeated)?

## References

- ADR-0038 (overload resolution), ADR-0039 (native bindings, embedded
  std::core), RFC-0060 (aspect impl coherence), sprint-22 implementation
  guide decisions 9–15.
- Rust: `impl<T: Debug, const N: usize> Debug for [T; N]`; RFC 1210
  (specialization, rejected complexity worth studying).
- SML Definition §4.4 (equality types); Swift SE-0143 (conditional
  conformances).
