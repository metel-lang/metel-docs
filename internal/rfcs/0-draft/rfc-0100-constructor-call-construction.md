---
id: rfc-0100
title: "Constructor-Call Construction"
date: '2026-07-13'
status: draft
target:
---

## Summary

`Type(args)` call-shaped syntax replaces `Type { field: value }` struct literals at construction sites. The RFC's real deliverable isn't the struct-literal rename — it's **general keyword arguments for function calls**, since positional-only construction is unreadable beyond one or two fields, and struct construction is just the first, motivating use of that mechanism. Like RFC-0099, this is not a pure token/reordering change: keyword arguments collide with the existing type-ascription expression (RFC-0023) at the grammar level, and this RFC has to settle that before the feature is well-formed (§3). Raises (and resolves) a symmetry question against pattern-matching destructuring, which keeps its current syntax unchanged.

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

## 3. Grammar collision with type ascription, and its fix

This is not a pure addition to the grammar — like RFC-0099's own dot/field-access collision, keyword
arguments collide with an existing production, and the RFC isn't well-formed without settling it.
`arg_list = { expr ~ ("," ~ expr)* ~ ","? }` today: every call argument is a plain `expr`, which resolves
down through `asc_expr = { unary_expr ~ (":" ~ type_expr)? }` — the *existing* type-ascription expression
(`expr: Type`, RFC-0023). Any bare identifier is already a syntactically valid, zero-arg `type_expr` (used
pervasively for generics), so `Foo(bar: Baz)` is genuinely ambiguous in the grammar's own terms: is it a
keyword argument `bar` bound to the value `Baz`, or one positional argument — the expression `bar`,
ascribed to the type `Baz`? Since `asc_expr`'s optional ascription clause sits *below* `arg_list`'s `expr`
in the precedence chain, and PEG's ordered choice commits to the first alternative that matches, `bar:
Baz` would always be consumed as ascription first under the grammar as it stands today — meaning `name:
value` keyword-argument syntax would never actually parse as intended without an explicit fix.

**Fix: restructure `arg_list` to try a keyword-argument shape before falling through to plain `expr`** —
`call_arg = { (ident ~ ":" ~ expr) | expr }`, tried in that order. Any argument shaped `ident : ...` inside
a call's parens then always reads as a keyword argument, unconditionally. The cost, stated plainly: it is
no longer possible to write a bare ascribed variable as a positional call argument (`f(x: SomeType)`,
meaning "pass the expression `x`, ascribed to `SomeType`, as one positional argument") — that shape is now
unambiguously a keyword argument named `x`, which will almost always fail typechecking immediately if
that's not what was intended, since `SomeType` used as an ordinary value expression is not valid. Ascription
everywhere *else* in the language (`let` bindings, match arms, general sub-expressions) is completely
untouched by this — only its availability as a bare, unparenthesized *positional call argument* is
affected, and RFC-0023's own decision (ascription vs. turbofish) is not reopened.

RFC-0101 (Grammar-Enforced Naming Case Conventions), reviewed alongside this RFC, narrows this ambiguity's
remaining edge case further without replacing the fix above: once bare PascalCase identifiers reliably
mean "type reference, never a standalone value" (since this RFC's own call-shaped construction means a
bare type name with no trailing `(args)` never constructs anything), the one case where someone might have
*wanted* `bar: Baz` to be a keyword argument with a bare-identifier value essentially can't arise in
legitimate code. The grammar-ordering fix above is what actually resolves the collision; RFC-0101 makes its
one accepted trade-off negligible in practice, it doesn't substitute for it.

## 4. Symmetry with pattern-matching destructuring

`match x { IntBox { value } => ... }`-style destructuring **keeps its current `{ field }` syntax, unchanged by this RFC.** Construction and destructuring diverge in spelling after this RFC ships — `Type(value: 42)` to build, `Type { value }` to take apart. This is a deliberate choice, not an oversight: destructuring's `{ field }` shape already reads as "match against this shape" (consistent with `enum`-variant destructuring, which also uses `{ field }` when a variant carries named fields), and forcing it into call-shape would suggest destructuring *invokes* something, which it doesn't. The asymmetry is judged acceptable because the two operations are already conceptually distinct (construction produces a value; destructuring matches an existing one), not a case where readers would expect symmetry in the first place.

## 5. Coexistence with the old literal syntax

**The old `Type { field: value }` literal syntax is retired, not kept as a second valid spelling.** Keeping both was considered (see Alternatives) and rejected: having two equally-valid ways to construct any struct is a worse ergonomic outcome than a one-time mechanical migration, and this project's own precedent (RFC-0042 §D1: "the language keeps only one binding introducer... does not carry a transition alias") already establishes that a clean single spelling is preferred over a permanent dual-syntax compromise when a rename like this ships.

## 6. Evaluation order, aspect methods, and overload resolution

Three questions an earlier draft of this RFC left open, resolved here against the actual implementation
rather than by analogy alone:

**Evaluation order.** `evaluator/mod.rs`'s existing `TypedExpr::Call` handling evaluates arguments via
`args.iter().map(|a| eval_expr(a, ...))` — strict left-to-right over the stored argument list, which today
(positional-only, no reordering possible) is naturally call-site text order. Keyword arguments break the
assumption that "stored order" and "written order" are the same thing, since `f(port: getPort(), host:
getHost())` writes `port` first but binds to a parameter declared second. **Resolution: evaluation happens
in two separate steps, not one** — first, evaluate every argument expression strictly in the order written
at the call site (left to right, exactly as today, regardless of position vs. keyword), producing a list of
already-computed values; only then re-map those *values* (never the expressions) onto the callee's declared
parameter positions for the actual call. Reordering the expressions themselves to declaration order before
evaluating them, instead, would silently run `getPort()` before `getHost()` despite it being written second
— an easy mistake to make, invisible to any type-only test, and exactly the mistake most languages with
keyword arguments (Python, Swift, Kotlin) are careful to avoid.

**Aspect-method calls.** No special case: the receiver (`self`) is always positional, supplied by the
expression before the dot, and can never be targeted by a keyword argument — `self` is a reserved keyword,
so it can't collide with an ordinary parameter name either. Every parameter after `self` is an ordinary
named parameter, structurally identical to a free function's from this RFC's perspective. Keyword arguments
apply to aspect-method calls exactly as they do to free functions, confirmed against RFC-0044's three
receiver forms (`self`, `&self`, `&var self` post-RFC-0098) — none of which interact with argument naming at
all.

**Overload resolution.** `overload.rs`'s own doc comment settles the general rule already in force:
resolution is "exact-match only... argument types must equal a candidate's parameter types exactly" — by
full parameter type list, not merely argument count. Keyword arguments extend this rather than replace it:
for each candidate overload, the call's keyword-named arguments must name-match some subset of *that
candidate's own* declared parameter names (any remaining slots filled by leftover positional arguments, in
order), and the resulting per-slot argument types must exact-match that candidate's parameter types — the
same rule as today, with keyword names doing the slot assignment instead of pure position. A keyword name
absent from a candidate's own parameter list disqualifies that candidate for the call, the same way an
argument-count or type mismatch already does. Checked against the real overloaded natives this RFC's
Unresolved Questions cited hypothetically: `assert(cond: boolean)` and `assert(cond: boolean, msg: String)`
(`stdlib/core.mtl:336-337`) both have real, distinct declared parameter names, so `assert(cond: true, msg:
"x")` resolves to the two-parameter overload by the rule above with no special-casing needed.

---

## Alternatives Considered

- **Positional-only construction (`IntBox(42)`, no keyword arguments at all).** Rejected as the primary proposal — unreadable for any struct with more than two or three fields, and silently order-dependent in a way today's named-field literal never was. Kept as sugar for the single-field case (§1).
- **Struct-only keyword arguments, not a general call-syntax feature.** Rejected: this would need its own separate desugaring/typechecking path distinct from ordinary function calls for no real benefit, when generalizing costs little extra and gives every function call the same ergonomic win.
- **Keep `Type { field: value }` as a second valid spelling alongside `Type(field: value)`.** The lower-risk option, and the one worth revisiting if migration friction during review turns out to be worse than expected — noted here as the fallback, not the default, per RFC-0042's own precedent against carrying a permanent transition alias (§5).
- **Making destructuring call-shaped too, for symmetry with construction.** Rejected (§4) — `match Type(value) => ...` reads as invoking something, not matching against a shape, and would be a bigger, more confusing change than the asymmetry it "fixes."
- **Keyword-argument-vs-ascription disambiguation alternatives** (casing-based, requiring parens around nested ascription, a distinct marker token) — see §3 for the grammar-ordering fix chosen and why the alternatives were set aside.

---

## Unresolved Questions

None load-bearing. The three questions an earlier draft left open — evaluation order, aspect-method
calls, and overload resolution — are resolved in §6, each checked directly against the relevant existing
implementation (`evaluator/mod.rs`'s argument evaluation, RFC-0044's receiver forms, and `overload.rs`'s
own documented exact-match rule) rather than assumed.

---

## References

- RFC-0023 (Type Ascription vs Turbofish) — the existing `expr: Type` production this RFC's keyword
  arguments collide with (§3); not amended — only the ability to use bare ascription as an unparenthesized
  positional call argument is affected.
- RFC-0042 (`let mut` for Mutable Bindings) — precedent cited in §5 for retiring an old spelling outright rather than keeping a permanent transition alias.
- RFC-0044 (Explicit Receiver Semantics) — receiver-form distinctions confirmed against §6's aspect-method-call resolution.
- RFC-0091 (Linear Records, draft) — uses `record { field: Type }` as a *type-level* notation (not a construction-site expression); related surface shape, but a different grammar position, not directly amended by this RFC.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0099 (Dot-Separated Module Paths) — sibling surface-syntax RFC from the same review; independent of this one.
- RFC-0101 (Grammar-Enforced Naming Case Conventions) — reviewed alongside this RFC; narrows (but does not
  replace) §3's grammar-ordering fix by making bare PascalCase identifiers reliably mean "type, never a
  standalone value."

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
