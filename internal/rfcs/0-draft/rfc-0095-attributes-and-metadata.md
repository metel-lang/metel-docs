---
id: rfc-0095
title: "Attributes and Metadata"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects), as part of decomposing that RFC into smaller, independently
> reviewable pieces. Mostly independent of the comptime cluster (RFC-0092/0093/0094):
> pure compiler hints (`@inline`, `@cfg`, `@allow`) need nothing from comptime and could
> ship first. Only the "attributes as comptime-visible metadata" piece (§2) depends on
> RFC-0092's `typeinfo`.

## Summary

Specifies `@` as the single grammar symbol for attributes and metadata: compiler hints
(`@inline`, `@cold`, `@must_use`), conditional compilation (`@cfg(...)`), FFI
annotations (`@extern("C")`), lints (`@allow(...)`, `@deny(...)`), and documentation
(`@doc(...)`). Also specifies that field- and type-level attributes are not independent
of the comptime derive mechanism (RFC-0093) the way pure compiler hints are — they are
exactly the kind of metadata a comptime derive function needs to read to customize its
output (skip a field, rename it), matching how nearly every language with both a
metadata layer and a reflection/codegen layer actually uses them.

---

## Motivation

Without a principled attribute syntax, compiler directives accumulate as ad-hoc
keywords or magic comments. A single syntax form (`@`) handles all of them uniformly.

Whether this is independent of the derive mechanism depends on which attribute. Pure
compiler hints (`@inline`, `@cold`, `@must_use`, `@allow`, `@deny`) are: nothing about
RFC-0093 changes what they mean or how they're checked. Field- and type-level
attributes are not — they are exactly the kind of metadata a comptime derive function
needs to read to customize its output, and treating them as unrelated to comptime, as
an earlier revision of this thread's design did, doesn't match how nearly every
language with both a metadata layer and a reflection/codegen layer actually uses them:
Rust's derive macros read sibling attributes (`#[serde(rename = "...")]`,
`#[serde(skip)]`) to customize their generated code; C#/Java's serialization and ORM
frameworks reflect over annotations precisely to decide field-by-field behavior. §2
works this out concretely.

---

## 1. Preferred Syntax: `@`

The preferred grammar symbol for attributes and metadata, derive included, is `@`. This
is distinct from all current Metel operators and consistent with annotation syntax in
several modern languages (Java, Python decorators, Zig's `@builtins`).

```metel
@derive(Clone, Eq)
struct Point {
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
expressions. Derive uses `@derive(Aspect, ...)`, both to request derivation (attached
to a struct/enum) and to register an implementation (attached to a comptime
function) — see RFC-0093.

The `@` form is preferred over Rust's `#[...]` because:
- `#` is visually associated with comments in many languages; `@` is unambiguously an
  annotation sigil
- `@` is already unused in Metel's grammar (outside allocators, which use it in a
  different grammatical position)
- `@(...)` is unambiguous as a prefix — no bracket/brace confusion with other
  constructs

---

## 2. Attributes as comptime-visible metadata

Not every `@` attribute interacts with comptime. Pure compiler hints — `@inline`,
`@cold`, `@must_use`, `@allow`, `@deny` — are directives the compiler reads directly;
comptime derive code has no reason to see them, and nothing else in this section
applies to them.

Field- and type-level attributes are different. In nearly every language with both a
metadata layer and a reflection/codegen layer, the two are tightly coupled: Rust's
derive macros read sibling attributes to customize their generated code; C#/Java's
serialization and ORM frameworks reflect over annotations precisely to decide
field-by-field behavior.

Concretely: for a comptime derive function to honor `@skip` or `@rename(...)`,
`typeinfo(T)`'s row (RFC-0092 §2) needs to carry each field's attributes, not just its
name and type — a gap in RFC-0092's row-metadata question (Open Question 1), alongside
declaration order and visibility.

```metel
struct User {
    id: i64,
    @skip
    password_hash: String,
    @rename("full_name")
    name: String,
}

comptime fun derive_display(comptime T: type) {
    let fields = typeinfo(T).row;   // now carrying each field's @ attributes too
    emit impl Display for T {
        fun to_string(self: &T) -> String {
            // ordinary comptime code: skip fields tagged @skip, and use
            // @rename's argument in place of the field's own name
        }
    }
}
```

**`@cfg` deserves its own note**, because Zig doesn't have a separate attribute for
conditional compilation at all — it's ordinary `comptime if`, branching on a
comptime-known value, the same mechanism as everything else in the comptime cluster.
Whether Metel's `@cfg` should stay its own attribute or collapse into comptime `if` the
way macros collapsed into generalized `emit` (RFC-0094) is folded into Open Question 4
rather than treated as settled here.

**One open design fork this raises, not resolved here:** should a derive function's own
configuration travel as arguments nested inside `@derive(...)` itself
(`@derive(Serialize(rename_all = "camelCase"))`), or always as separate per-field/
per-type `@` attributes read via `typeinfo`, as sketched above? Rust does the latter —
configuration lives beside the derive, not inside its invocation. Recorded as RFC-0093
Open Question 5 rather than decided here.

---

## Alternatives Considered

### `#[...]` Rust-style attributes

Familiar to Rust programmers but visually ambiguous with comments (`#`). Rejected in
favour of `@`.

### No attribute syntax — ad-hoc keywords only

Each compiler directive is its own keyword or syntax form. Avoids designing a general
system but leads to keyword proliferation and inconsistency. Rejected as a long-term
position; acceptable only before v0.5 when no attribute-dependent features have
shipped.

---

## Interaction with Other RFCs

### RFC-0001 (Pointers) and RFC-0026 (Unsafe Blocks)

`@extern("C")` for FFI function signatures (RFC-0026 open question 4) uses the `@`
attribute syntax defined here. The attribute system is a soft prerequisite for a clean
FFI story; unaffected by the comptime cluster.

### RFC-0009 (Module System)

`@pub`, `@cfg`, and documentation attributes interact with the module system's
visibility model. Also relevant to §2 directly: reflection's need for per-field
visibility (RFC-0092 Open Question 1) means `typeinfo` and the module system's privacy
rules are not fully independent.

---

## Open Questions

1. **`@` attribute scope.** What items can be annotated — struct/enum declarations,
   function declarations, `let` bindings, individual fields? Field-level attributes
   (e.g. `@skip` on a field to exclude it from `Display`) are no longer just "useful
   but add parsing complexity" — §2 gives them a concrete consumer (comptime derive
   functions reading them via `typeinfo`), so this question is load-bearing for
   RFC-0092 Open Question 1, not merely nice-to-have.

2. **Compiler-known attribute registry.** The compiler needs a fixed set of recognised
   `@` attributes (e.g. `@inline`, `@cfg`, `@allow`). Should unknown `@` attributes be a
   compile error, a warning, or silently ignored (for forward compatibility)?

3. **`@cfg` and conditional compilation.** Conditional compilation is a significant
   feature in its own right (platform-specific code, feature flags). Should `@cfg` be
   in scope for this RFC or a separate one?

4. **Does `@cfg` collapse into comptime `if`?** §2 adds a sharper version of Open
   Question 3: Zig has no `@cfg`-equivalent attribute at all, using ordinary
   `comptime if` instead — should Metel's `@cfg` similarly collapse into comptime `if`,
   the way general macros collapsed into generalized `emit` (RFC-0094), rather than
   staying a bespoke directive? Independently corroborated after the fact: RFC-0055
   (Comptime, superseded by RFC-0092), discovered 2026-07-09 via `INDEX.md` after this
   question was already written, reached the same conclusion from its own motivation
   section ("conditional boolean conditions fold cleanly into the generated code with
   no overhead") without knowing this RFC existed. Two independent routes reaching the
   same answer is worth reading as added confidence, not as work needing reconciling.

---

## Timing Recommendation

Pure compiler-hint attributes (`@inline`, `@allow`, `@cfg` as a bespoke directive) need
nothing from the comptime cluster and could ship independently, before v0.5. §2's
attributes-as-comptime-visible-metadata piece is gated on RFC-0092's `typeinfo` and
therefore shares RFC-0092/0093's v0.5+ timeline.

Minimum action before v0.5: reserve `@` as a grammar token so it cannot be used for
other purposes. This prevents a breaking change when the attribute system and comptime
derive land.

---

## References

- RFC-0092 (Comptime Core) — `typeinfo`'s row-metadata question (Open Question 1),
  which §2's field-attribute reflection need feeds into
- RFC-0093 (Derive Registration) — Open Question 5's derive-configuration fork, which
  §2 raises but does not resolve
- RFC-0094 (Comptime Metaprogramming) — the `emit`-generalization precedent §2's `@cfg`
  question is modeled on
- RFC-0009 (Module System) — visibility and `@cfg` interaction; also field-visibility
  for reflection
- RFC-0026 (Unsafe Blocks) — `@extern` for FFI uses this RFC's attribute syntax
- Prior art: Rust `#[serde(...)]` sibling-attribute pattern; Java annotations; Python
  decorators; Zig `@builtins`

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+ for §2; pure compiler-hint attributes could ship earlier

*(Decision rationale goes here when the RFC is evaluated.)*
