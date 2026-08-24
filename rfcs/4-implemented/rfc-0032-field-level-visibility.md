---
id: rfc-0032
title: "Field-Level Visibility"
date: '2026-05-30'
status: implemented
spec_status: done
coverage:
  "1": { spec: "spec.modules.visibility.legality-1" }
  "2": { spec: "spec.modules.visibility.legality-3" }
  "3": { spec: "spec.modules.visibility.legality-4" }
  "4": { spec: "spec.modules.visibility.legality-7" }
  "5": { spec: "spec.expressions.struct-patterns.legality-1" }
  "6": { spec: "spec.modules.visibility.legality-6" }
  "7": { kind: blocked, reason: "check_field_visibility only checks the field's own visibility marker, never the enclosing struct's -- a public field on a private struct is actually reachable across modules once a value is obtained some other way, contradicting this claim. Confirmed independently of the pattern-matching gap (#753); the mechanism this needs already works, the enforcement itself is missing.", ref: "metel-core#776" }
  "8": { spec: "spec.modules.visibility.legality-5" }
---

## Summary

Make struct field visibility independent of the struct's own visibility. Fields are currently all-public when the struct is `pub`. This RFC proposes making fields **module-private by default** and requiring an explicit `pub` annotation to expose them. This is a **breaking change** for existing `pub struct` definitions.

---

## Motivation

The current spec states: *"Fields of a `pub struct` are public."* There is no mechanism to expose a type's name and API while keeping its internal state hidden. This makes it impossible to enforce invariants on public types — any module can read or write any field directly.

### The core problem

```metel
// token.mln
pub struct Token {
    kind:   TokenKind,   // can't make this read-only from outside
    span:   Span,        // can't hide implementation detail
    offset: Int,         // internal implementation detail — exposed anyway
}
```

Without field-level visibility, `Token` cannot:
- Prevent callers from reading `offset` (an internal detail).
- Prevent callers from constructing `Token` directly with arbitrary field values (bypassing validation logic in a constructor function).
- Expose a stable read-only surface while keeping internal layout flexible.

### Cross-language precedent

All major statically-typed languages with module/package systems support field-level visibility:

| Language | Default field visibility | Opt-in for visibility |
|---|---|---|
| **Rust** | Private to enclosing module | `pub` on field |
| **Swift** | `internal` (module-level) | `private`, `public`, etc. |
| **Kotlin** | `public` | `private`, `internal`, etc. |
| **Java** | Package-private | `public`, `private`, etc. |
| **C#** | `private` | `public`, `internal`, etc. |

Metel's current all-public-or-nothing model is an outlier. The Rust model (fields private by default, `pub` to expose) is the right fit given Metel's Rust-inspired syntax and module system.

---

## Proposal

### Rule: fields are module-private by default

A field with no visibility annotation is accessible only within the module that declares the struct. A field annotated with `pub` is accessible from any module that can see the struct type.

```metel
pub struct Token {
    pub kind:   TokenKind,   // externally readable
    pub span:   Span,        // externally readable
        offset: Int,         // module-private implementation detail
}
```

The struct name (`Token`) follows its own `pub` annotation independently. Field annotations are orthogonal.

### Visibility matrix

| Struct annotation | Field annotation | Type accessible externally? | Field accessible externally? |
|---|---|---|---|
| `pub struct` | `pub field` | Yes | Yes |
| `pub struct` | *(none)* | Yes | No |
| *(none)* `struct` | `pub field` | No | No (struct not nameable) |
| *(none)* `struct` | *(none)* | No | No |

A `pub` annotation on a field of a non-`pub` struct is syntactically valid but has no effect — the field cannot be accessed because the type itself is not externally nameable. It is not an error (it may become relevant if the struct is later made public).

### Construction

Constructing a `pub struct` with any private field from outside the module is a compile error (T0xxx — new error code in the private-field-access family):

```metel
// outside token.mln
let t = Token { kind = TokenKind::Ident, span = s, offset = 0 };  // ERROR: field `offset` is private
```

The intended pattern is a public constructor function:

```metel
// token.mln
pub struct Token {
    pub kind:   TokenKind,
    pub span:   Span,
        offset: Int,
}

pub fun Token::new(kind: TokenKind, span: Span) -> Token {
    Token { kind, span, offset = span.start }
}
```

From outside the module, callers use `Token::new(...)`. This enforces invariants at the boundary.

### Pattern matching

Pattern matching from outside the declaring module must use `..` (struct rest pattern) to skip private fields. Explicitly naming a private field in a pattern is a compile error (same error as construction):

```metel
// outside token.mln
match token {
    Token { kind, span, .. } => { ... }  // OK — offset skipped with ..
    Token { kind, span, offset }         => { ... }  // ERROR: field `offset` is private
}
```

> **Correction (2026-08-24, metel-core#753/#755).** Struct pattern matching was
> implemented with bare field bindings only — there is no `field: subpattern` form
> (this example originally showed `kind: TokenKind::Ident`, matching a specific value
> for that field). A field can be bound to a name or skipped via `..`; matching one
> against a nested pattern isn't part of what shipped, and isn't required by this
> section's actual normative claims (which are about which field *names* may appear,
> not about matching a field's own value).

Pattern matching **within** the declaring module has no restrictions — all fields are visible regardless of annotation.

Exhaustiveness checking: a struct with any private fields cannot be exhaustively matched by an external pattern that does not use `..`. The compiler must enforce this.

### `linear struct` and `linear enum`

> **Correction (2026-08-22).** `linear struct`/`linear enum` never materialized as a
> language construct. The `linear` keyword traces to RFC-0024 (Linear Types); metel-core#753
> flagged real ambiguity over whether that lineage was merely unimplemented or dropped
> outright, given that RFC-0024's superseding RFC (RFC-0028, refused) carries a note that
> its "foundation layer... linear types... stands and may be implemented." Resolved by RFC-0071
> (Ownership and Move Semantics) itself, whose own References section settles it: *"RFC-0024
> (Linear Types, superseded) — prior exploration of linear/affine ownership in Metel; this
> RFC is the settled formulation of the same core idea."* RFC-0071's accepted, implemented
> `Copy`/`Drop` aspect model is that settled formulation — not a `linear` type qualifier.
> There is no `linear` keyword anywhere in the current grammar, and none is planned under
> this design. This section is retained as historical record of the RFC's original
> assumptions, not as a description of implementable behavior.

The same rules apply to `linear struct`. Linear types are still constructable from outside only if all fields are `pub`, or via a public constructor function.

### Enum struct variants

Struct-variant fields in an enum follow the same rules. Tuple-variant fields are positional and cannot be individually annotated; if the enum is `pub`, those tuple-variant fields are public as part of the public variant shape.

```metel
pub enum Shape {
    Circle { pub radius: Float },            // radius is public
    Rect { pub width: Float, height: Float } // width public, height private
}
```

### Breaking change scope

This RFC changes the default for fields of `pub struct` from implicitly public to module-private. Every existing `pub struct` that expects external field access must be updated to add `pub` on those fields. The compiler must emit a clear migration error.

Because Metel is pre-1.0, this breaking change is acceptable. The CHANGELOG for the target version must document it.

---

## Alternatives Considered

### A — Additive `priv` keyword (non-breaking)

Fields inherit the struct's visibility by default; a `priv` keyword restricts a field to module-private:

```metel
pub struct Token {
    kind:       TokenKind,
    span:       Span,
    priv offset: Int,   // restricted
}
```

**Pros:** Non-breaking; no migration needed.

**Cons:** Unusual — virtually no language uses this model. The default (public fields) is the wrong default for encapsulation. Developers unfamiliar with this choice will accidentally expose fields they intended to keep private. The long-term design pressure will be toward the Rust default anyway; accepting this option defers the breaking change, not eliminates it.

**Verdict:** Rejected. The breaking change at pre-1.0 is the correct time to establish the right default.

### B — Type sealing (OCaml `private` type)

Rather than per-field visibility, seal the struct's *constructor*: the type is visible and field values are readable, but external code cannot construct a value of the type using struct-literal syntax:

```metel
sealed pub struct Token {
    kind:   TokenKind,
    span:   Span,
    offset: Int,
}
```

All fields remain readable; only construction is blocked.

**Pros:** No per-field annotation clutter; read access always works; simple mental model.

**Cons:** Does not support hiding fields (callers can still read `offset`). Does not support partial exposure (some fields public, some private). Less granular than the proposed design. Adding read-hiding later would still require per-field annotations.

**Verdict:** May be useful as a complementary feature alongside field visibility (a sealed type with all-public fields provides a constructor barrier). Not a replacement. Deferred.

### C — Getter/setter asymmetry (Swift / Kotlin model)

Allow a field to have a public getter and a private setter:

```metel
pub struct Counter {
    pub(set: priv) count: Int,
}
```

**Pros:** Expressive; common pattern (read-only external access).

**Cons:** Adds syntax complexity; requires understanding of "properties" vs. raw fields. The same effect can be achieved today with a private field and a public accessor function. Metel does not yet have computed properties, making this premature.

**Verdict:** Deferred until computed properties or properties-as-first-class-syntax are designed.

### D — Module-path scoped visibility (`pub(super)`, `pub(in path)`)

Add scoped visibility modifiers mirroring Rust:

```metel
pub(super) kind: TokenKind,  // visible to parent module
pub(in parser) span: Span,   // visible within parser module subtree
```

**Pros:** Very fine-grained access control; enables crate-internal APIs.

**Cons:** High complexity; Metel's current module system has no `crate`-equivalent scope. `pub` vs. module-private is sufficient for the stated motivation. Can be added later without a breaking change.

**Verdict:** Deferred. The two-level system (`pub` / private) is sufficient for v1.0 scope.

---

## Resolved Decisions

### D1 — Private-field access uses one error code family

Constructing a struct with a private field from outside the declaring module and pattern-matching a private field from outside the declaring module are treated as the same language error category: private field access across a module boundary. The diagnostic text may distinguish construction from pattern matching, but the spec and error-code table should treat them as one error family.

### D2 — No per-field visibility on tuple variants

This RFC does not introduce per-position visibility syntax for tuple variants. If an enum is `pub`, its tuple-variant fields are public as part of that public variant shape. Struct-variant fields continue to use named-field visibility annotations.

### D3 — Inert `pub` on a field of a non-`pub` struct should warn

When a field is marked `pub` but the enclosing struct is not public, the compiler should emit a warning rather than silently accepting the inert annotation. This is a developer-intent issue, not a language error.

### D4 — Spec changes are part of acceptance work

Accepting this RFC requires a same-change spec update in `docs/public/reference/spec/modules.md`, including:
- replacing the blanket "fields of a `pub struct` are public" rule
- documenting construction restrictions for private fields
- documenting pattern-matching restrictions for private fields

---

## Timing Recommendation

This RFC should be resolved before any feature that adds new struct-based types to `std::core` or the standard library — once public structs with all-public fields proliferate in shipped library code, the migration cost grows.

The earliest sensible target is the sprint that first adds library types with private implementation details. It should **not** block v0.6.x or v0.7.0 unless those versions introduce such types.

---

## References

- Language spec: `docs/public/spec/modules.md` — Visibility section
- Implementation report: `metel-interpreter/docs/module-system-report.md` §7.4 (Field-level visibility)
- GitHub issue: #468
- Rust reference: [Visibility and Privacy](https://doc.rust-lang.org/reference/visibility-and-privacy.html)
- Swift: [Access Control](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/accesscontrol/)
- OCaml: [Private Types](https://ocaml.org/manual/5.1/privatetypes.html)

---

## Decision

**Outcome:** Accepted
**Target:** *(pending milestone assignment)*

The field-visibility design and its remaining language-shape questions are resolved. Follow-up work is spec alignment and later implementation planning.

## Coverage Checklist (added 2026-08-19, not part of the original RFC)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims
(expanded 2026-08-19: added item 8, missed in the original pass),
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. Struct fields are module-private unless declared public

Field visibility is independent of the enclosing struct's visibility. A `public`
field of a public struct may be accessed from another module, while an unmarked
field may not.

### 2. Private fields cannot be read or assigned across modules

Reading or assigning a private field outside its declaring module is rejected with
the private-field visibility error `T0009`. The declaring module retains access to
all of its fields.

### 3. External construction requires every named field to be visible

Constructing a struct literal outside its declaring module is rejected if it names
any private field. A module-local constructor or helper may construct the value
instead.

### 4. External patterns may not name private fields

A pattern outside the declaring module cannot explicitly bind a private field and
must use `..` to omit private fields. A pattern in the declaring module may name
all fields.

### 5. Private fields prevent externally exhaustive named-field patterns

An external named-field pattern for a struct with private fields must include `..`;
otherwise it is not a permitted exhaustive representation of that struct.

### 6. Field visibility also applies to enum struct variants

Named fields of enum struct variants use the same public/private rules as ordinary
struct fields. Public enum tuple-variant positions remain exposed as part of their
positional variant shape.

> **Note (2026-08-22):** this item originally also claimed the same for `linear
> struct`/`linear enum`, which don't exist in the language — see the correction on the
> RFC's own "`linear struct` and `linear enum`" section above. Dropped from this item;
> it is not part of what remains to be tested here.

### 7. Public fields on a private struct do not expose the struct externally

Marking a field `public` does not make its enclosing private struct nameable from
another module, so that field remains inaccessible through the private type.

### 8. A public field on a private struct produces a warning

The compiler warns when a field is declared `public` on a struct that is not
public, because the field cannot be accessed across a module boundary.
