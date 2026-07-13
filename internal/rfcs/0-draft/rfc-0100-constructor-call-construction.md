---
id: rfc-0100
title: "Constructor-Call Construction"
date: '2026-07-13'
status: draft
target:
---

## Summary

`Type(args)` call-shaped syntax replaces `Type { field: value }` struct literals at construction sites. The RFC's real deliverable isn't the struct-literal rename — it's **general keyword arguments for function calls**, since positional-only construction is unreadable beyond one or two fields, and struct construction is just the first, motivating use of that mechanism. Raises (and resolves) a symmetry question against pattern-matching destructuring, which keeps its current syntax unchanged.

---

## Motivation

`Type { field: value }` free-standing struct literals are one of the more recognizable Rust tells in Metel's surface syntax — most languages, including every OOP-flavored one, construct values through a call-shaped constructor. But a naive rename to `Type(value1, value2, ...)` only reads well for one or two fields; anything larger needs field names at the call site to stay readable, which means this RFC can't just rename struct construction — it has to introduce keyword arguments as a real, general call-syntax feature, with struct construction as the first consumer rather than a special case bolted onto structs alone.

---

## 1. Construction syntax

Today:
```metel
struct IntBox { value: i64 }
let b = IntBox { value: 42 };

struct Token { pub value: String, secret: String }
let t = Token { value: "x".to_string(), secret: "shh".to_string() };
```

Proposed:
```metel
struct IntBox { value: i64 }
let b = IntBox(value: 42);

struct Token { pub value: String, secret: String }
let t = Token(value: "x".to_string(), secret: "shh".to_string());
```

Field order at the construction site becomes non-load-bearing — `Token(secret: "shh".to_string(), value: "x".to_string())` is equally valid, matching keyword-argument semantics in every language that has them (Python, Swift, Kotlin). Positional arguments remain available for the common one-or-two-field case: `IntBox(42)` is valid when there's exactly one field and no ambiguity about which one it binds to; mixing positional and keyword arguments in one call follows the same rule most languages use (positional arguments must precede keyword ones).

## 2. Keyword arguments as a general call-syntax feature

This is the section that makes this RFC bigger than "rename struct literals." Once `Name: value` is legal at a struct's construction call site, the natural and more valuable generalization is allowing it at *any* function call:

```metel
fun connect(host: String, port: i64, timeout: i64) -> Connection { ... }

connect(host: "db.local", port: 5432, timeout: 30);
connect("db.local", port: 5432, timeout: 30);   // positional + keyword mix
```

Parameter names become part of a function's public call-site surface, the same way they already are conceptually (every existing signature already names its parameters — this RFC exposes that naming at the call site rather than introducing new declaration syntax). Keyword arguments are optional at every call site — purely positional calls remain valid and unchanged for any function, including ones defined before this RFC.

## 3. Symmetry with pattern-matching destructuring

`match x { IntBox { value } => ... }`-style destructuring **keeps its current `{ field }` syntax, unchanged by this RFC.** Construction and destructuring diverge in spelling after this RFC ships — `Type(value: 42)` to build, `Type { value }` to take apart. This is a deliberate choice, not an oversight: destructuring's `{ field }` shape already reads as "match against this shape" (consistent with `enum`-variant destructuring, which also uses `{ field }` when a variant carries named fields), and forcing it into call-shape would suggest destructuring *invokes* something, which it doesn't. The asymmetry is judged acceptable because the two operations are already conceptually distinct (construction produces a value; destructuring matches an existing one), not a case where readers would expect symmetry in the first place.

## 4. Coexistence with the old literal syntax

**The old `Type { field: value }` literal syntax is retired, not kept as a second valid spelling.** Keeping both was considered (see Alternatives) and rejected: having two equally-valid ways to construct any struct is a worse ergonomic outcome than a one-time mechanical migration, and this project's own precedent (RFC-0042 §D1: "the language keeps only one binding introducer... does not carry a transition alias") already establishes that a clean single spelling is preferred over a permanent dual-syntax compromise when a rename like this ships.

---

## Alternatives Considered

- **Positional-only construction (`IntBox(42)`, no keyword arguments at all).** Rejected as the primary proposal — unreadable for any struct with more than two or three fields, and silently order-dependent in a way today's named-field literal never was. Kept as sugar for the single-field case (§1).
- **Struct-only keyword arguments, not a general call-syntax feature.** Rejected: this would need its own separate desugaring/typechecking path distinct from ordinary function calls for no real benefit, when generalizing costs little extra and gives every function call the same ergonomic win.
- **Keep `Type { field: value }` as a second valid spelling alongside `Type(field: value)`.** The lower-risk option, and the one worth revisiting if migration friction during review turns out to be worse than expected — noted here as the fallback, not the default, per RFC-0042's own precedent against carrying a permanent transition alias (§4).
- **Making destructuring call-shaped too, for symmetry with construction.** Rejected (§3) — `match Type(value) => ...` reads as invoking something, not matching against a shape, and would be a bigger, more confusing change than the asymmetry it "fixes."

---

## Unresolved Questions

1. **Keyword-argument evaluation order when arguments have side effects.** Most languages evaluate call arguments left-to-right regardless of positional/keyword mixing; this RFC should state that explicitly rather than leave it implicit, but doesn't yet.
2. **Do keyword arguments apply to aspect-method calls the same way as free functions?** Likely yes, no special case — `self`/receiver position aside, an aspect method's parameter list is an ordinary parameter list — but worth confirming against RFC-0044's receiver-form distinctions before acceptance.
3. **Interaction with existing overloaded natives** (`assert`, dispatched by `SymbolId`, not by name) — does keyword-argument matching need to account for overload resolution, or is this scoped to non-overloaded calls only? Needs checking against the actual overload-table mechanism before this RFC is accepted, not assumed.

---

## References

- RFC-0042 (`let mut` for Mutable Bindings) — precedent cited in §4 for retiring an old spelling outright rather than keeping a permanent transition alias.
- RFC-0044 (Explicit Receiver Semantics) — receiver-form distinctions relevant to Unresolved Question 2.
- RFC-0091 (Linear Records, draft) — uses `record { field: Type }` as a *type-level* notation (not a construction-site expression); related surface shape, but a different grammar position, not directly amended by this RFC.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0099 (Dot-Separated Module Paths) — sibling surface-syntax RFC from the same review; independent of this one.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
