---
id: rfc-0094
title: "Comptime Metaprogramming — Generalized Emit, Comptime-Callable Parsing, Diagnostics"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects), as part of decomposing that RFC into smaller, independently
> reviewable pieces. Depends on RFC-0092 (Comptime Core) for `type`-as-value, `typeinfo`,
> and single-declaration `emit`. Genuinely independent of RFC-0093 (Derive
> Registration): derive itself never needs multi-declaration or expression-position
> `emit`, so this RFC and RFC-0093 can be accepted, implemented, or deferred on separate
> schedules.

## Summary

Generalizes RFC-0092's `emit` to (1) produce more than one declaration from a single
comptime function and (2) splice an expression back at its own call site rather than
only registering a declaration elsewhere. Combined with exposing Metel's own parser as
an ordinary comptime-callable function over string values, this covers nearly
everything a general macro system would otherwise be needed for — repetitive
declaration generation, compile-time-validated embedded DSLs, and pattern-as-argument
macros (Rust's `matches!`) — without a token-stream grammar, a macro-invocation syntax
form, or a hygiene system to design. Also specifies span-tracked comptime strings, the
primitive needed for precise diagnostics (and, downstream, LSP highlighting) over
comptime-parsed string content, and explicitly scopes body reflection (inspecting a
function's own statements, as opposed to a type's shape) out of this RFC's mechanism.

---

## Motivation

### Macros — mostly closed by comptime, not just superseded for derive

A general macro system enables syntactic abstraction — generating code from a compact
notation, operating on unexpanded syntax. RFC-0093's derive mechanism gets its own
extensibility without one, and — once `emit` is generalized (§1) and Metel's parser is
exposed as a comptime-callable function (§2) — this RFC reaches most of what a macro
system is normally reached for, not only derive:

- **Repetitive declaration generation** (one getter per field, one match arm per
  variant, builder-pattern boilerplate) — a loop over `typeinfo(T).row` emitting one
  declaration per iteration. No grammar needed; this is ordinary comptime control flow.
- **Compile-time-validated embedded DSLs** (a `sql("SELECT ...", id)` that parses and
  type-checks its query string at compile time) — a comptime function receiving a
  string literal and parsing it with an exposed grammar production, producing a value
  or a type. No foreign parser integration or macro-invocation syntax needed.
- **Pattern-as-argument macros** (Rust's `matches!(expr, Pattern::Variant(x) if x > 0)`)
  — previously assumed to need genuine syntax-level macros. It does not: a comptime
  function parses the pattern from a string using the same exposed grammar, then emits
  an expression *at the call site* (§1), evaluated against the caller's own locals.
  Because the parsed text is spliced back at the exact position the caller wrote it,
  there is no cross-scope identifier injection and therefore no new hygiene problem to
  solve — the caller's `x` binds exactly where they typed it.

What remains is a short, specific list, not "everything else is still open": tooling
ergonomics for DSL text embedded in string literals (§3, closable with span-tracked
comptime strings), auto-capturing a caller's own source text without them retyping it as
a string (a narrow, separately addressable ask), and genuinely bare, unquoted foreign
syntax appearing directly in Metel source with no call-syntax wrapping at all (the one
case that is structurally out of reach — Zig does not support this either). None of the
three motivate a token-stream/hygiene macro system on their own.

---

## 1. Emitting more than one declaration, and at expression position

RFC-0093's derive mechanism only ever needs `emit` to produce a single `impl` block.
Reaching the macro-like use cases above needs two generalizations of the same
primitive, neither of which changes what kind of thing `emit` fundamentally does — a
side effect of compile-time evaluation that registers a checked declaration:

- **Multiple declarations from one comptime function.** `emit` inside a loop over
  `typeinfo(T).row` can run once per field, each iteration emitting its own declaration
  (a getter function, a match arm, a builder method). This requires no new concept —
  ordinary comptime control flow around an `emit` that was always going to run zero or
  more times, not exactly once.

- **Expression-position `emit`.** Rather than registering a declaration to live
  elsewhere, comptime code can produce an expression that is spliced back in *at its
  own call site*, evaluated in the caller's lexical scope against the caller's own
  locals. This is the piece that makes pattern-as-argument macros (§2) possible: a
  comptime function receiving `"Variant(x) if x > 0"` as a string can parse it and emit
  the resulting pattern expression back into the `match` the caller wrote, binding `x`
  exactly where the caller's own code expects it. Because the splice target is the same
  textual position the caller invoked from — not some other scope the macro expansion
  reaches into — this does not reintroduce the identifier-capture hygiene problems
  syntax-level macros are known for; the caller's own scoping rules apply unchanged.

---

## 2. Comptime-callable parsing

The other piece needed is exposing Metel's own parser as an ordinary function callable
from comptime code — parsing a string value into a pattern, expression, or (subject to
Open Question 3) other grammar productions, rather than requiring a macro-invocation
syntax form that operates on unexpanded surrounding tokens.

```metel
comptime fun matches_str(comptime pat: string, expr: T) -> boolean {
    let parsed = parse_pattern(pat);   // Metel's own pattern grammar, comptime-callable
    emit match expr {
        parsed => true,
        _ => false,
    }   // expression-position emit (§1): spliced back at the call site
}
```

```metel
comptime fun sql(comptime query: string, params: ...) -> QueryResult {
    let validated = parse_sql(query);   // validated at compile time against schema
    // ordinary comptime code computing a result type/value from `validated`
}
```

Both read a string the caller wrote directly as an argument — not raw, unexpanded
surrounding syntax the way a syntax-level macro would receive it — and both produce
either a value/type (the `sql` case) or a spliced-back expression via §1 (the
`matches_str` case). Neither needs a macro grammar, a separate expansion phase, or
hygiene machinery: it is a function call with a string-literal argument, using the same
`comptime`/`emit`/`type`-as-value pieces RFC-0092 already specifies.

**What this does not close**, honestly: an embedded DSL inside a string literal loses
editor syntax highlighting and autocomplete even when the compiler validates it
correctly (§3 addresses diagnostics, not highlighting, directly); auto-capturing a
caller's own literal source text without them retyping it as a string (Rust's `dbg!`
printing both a value and its literal expression text) is a separate, narrower ask this
does not provide by itself; and genuinely bare, unquoted foreign syntax appearing
directly in Metel source (no wrapping call, no quotes) is structurally out of reach,
because it requires the parser to accept something other than Metel's own grammar at
that exact position — which comptime, operating strictly after Metel's own parse
completes, cannot do. Zig does not support this case either.

---

## 3. Span-tracked comptime strings and diagnostics

Good error messages for a comptime-parsed string need more than "the call to `sql(...)`
on line 10 failed" — they need to point at the exact offset inside the string literal
where parsing broke. This requires the compiler to preserve, for any string value
originating from a literal at a comptime-known source location, a mapping from
byte-offset-within-the-string back to absolute source position, and a span-aware
error-reporting primitive (e.g. `compileError(msg, at: span)`) that the exposed parser
(§2) can call using spans it already tracks internally while walking the string.

This also happens to be the same primitive an LSP would need to offer semantic
highlighting for embedded DSL text — by invoking the same comptime-exposed parser
interactively over a string literal's known span and mapping the resulting tokens back
to editor ranges. That is downstream tooling architecture, not something this RFC
specifies, but it rests on nothing beyond the span-tracking this section already needs
for diagnostics.

**A real limit, not a hand-wave:** this works cleanly only for strings that are literals
typed directly at the call site. A string built up via comptime concatenation or
`format`-style assembly from multiple pieces has no single contiguous source range the
final value corresponds to, so span attribution degrades or disappears — mirroring a
well-known limitation in existing macro/DSL tooling (a literal format string gets
precise diagnostics; a dynamically assembled one usually does not).

---

## 4. Body reflection: a plausible but much larger extension, not proposed here

RFC-0092's `typeinfo(T)` reflects a *type's* shape — a flat row of (name, type) pairs, a
handful of enum arms. It is natural to ask whether the same idea extends to a
*function's own body*: a `bodyinfo(f)`-style value exposing its statements,
expressions, and control flow to comptime code, for uses like linting, custom
style-rule enforcement, or security auditing ("does this function call an unsafe
operation").

This does not belong in this RFC's proposed mechanism, for two separate reasons, and is
recorded here only as a scoped, deliberately-not-designed open question:

- **It is a much larger reflection surface than `typeinfo`.** A type's shape is a flat
  set of fields; a function body is arbitrarily nested expressions, control flow,
  closures, pattern matches. Where `TypeInfo` (RFC-0092 §2) has a handful of arms, a
  body representation would need to cover every expression and statement form in the
  grammar — closer to exposing the compiler's own AST than to `typeinfo`'s narrow,
  purpose-built shape.

- **The motivating use case — auditing for a property like "performs IO" or "uses
  unsafe" — is a transitive, whole-call-graph question that body reflection cannot
  actually answer, regardless of how much of it gets built.** Checking "does this
  function, or anything it calls, do X" requires walking into every callee, and RFC-0008
  (Aspect Objects) already establishes that a `dyn Aspect` method call's concrete callee
  is not known until runtime. Auditing cannot walk into a call it cannot resolve at
  compile time — this is not a design gap more comptime power closes, it is what dynamic
  dispatch means by definition. The properly-scoped mechanism for exactly this
  motivation is an effect system, not source inspection: `reports/substructural-types/algebraic-effects.md`
  §11.1 already works through IO as a tracked effect, checked and propagated through a
  function's *signature*, compositionally, and (because the obligation lives on the
  aspect's interface contract rather than requiring the compiler to inspect whatever
  concrete type shows up at a `dyn` boundary) does not hit the same dynamic-dispatch
  wall that defeats body reflection for this purpose.

If Metel ever wants shallow, non-transitive body reflection for its own sake (custom
lints, style-rule enforcement scoped to a single function's own written code, not its
transitive callees), that remains a legitimate, separate design question — just not one
this RFC scopes or proposes a mechanism for.

---

## Alternatives Considered

### Lisp-style macros (hygienic, syntax-level)

Full hygienic macro system allowing arbitrary syntactic transformation over unexpanded
syntax. Maximum power, maximum complexity — well outside the scope of a v0.5 feature
for a language at v0.1, and no longer motivated by derive specifically now that
RFC-0093 covers that case. More than that: §1/§2 above show that generalized `emit`
plus a comptime-callable parser already reaches repetitive declaration generation,
compile-time-validated embedded DSLs, and pattern-as-argument macros — the use cases
that would normally motivate reaching for this alternative in the first place. What
remains unreachable without it is narrow: genuinely bare, unquoted foreign syntax with
no call-site wrapping at all. Not ruled out for that one residual case, but no longer a
broad, open-ended future direction — a small, specific, likely-skippable gap.

---

## Open Questions

1. **Expression-position `emit`'s scoping rules.** §1 asserts that splicing a
   comptime-parsed expression back at its own call site avoids syntax-macro-style
   hygiene problems because the caller's own scope applies unchanged — but the precise
   rule (what exactly counts as "the call site" once a comptime function itself calls
   other comptime functions before emitting; whether an emitted expression can
   reference comptime-local bindings from inside the emitting function, not just the
   caller's locals) is asserted, not specified. Needs a formal scoping rule before
   §1/§2's pattern-as-argument examples can be trusted.

2. **Comptime-callable parser API surface.** §2 sketches `parse_pattern`/`parse_sql`-
   style functions informally. Which grammar productions does Metel actually expose as
   comptime-callable (expressions only? patterns? statement lists? full item
   declarations?), and is this a small fixed set of builtins or a general
   "parse-a-production-by-name" facility? The broader the surface, the more this
   overlaps with exposing the compiler's own parser as a library, which is a larger
   commitment than derive alone needs.

3. **Scope of span-tracking, and whether highlighting is this RFC's concern.** §3
   commits to span-tracked comptime strings for diagnostics but explicitly limits this
   to literal strings, not computed/concatenated ones — is that limitation acceptable
   long-term, or does it need a real solution (e.g. span-preserving string
   concatenation) before v0.5? Separately: is LSP/editor semantic-highlighting support
   for embedded DSL text in scope for this RFC at all, or does it belong in a dedicated
   tooling RFC that merely depends on the span-tracking primitive specified here?

4. **Is body reflection in scope for this RFC at all?** §4 deliberately does not
   propose a mechanism for reflecting over a function's own statements/expressions, on
   the grounds that it is a much larger reflection surface and that its main
   motivating use case is better served by an effect system than by source inspection.
   Confirm this scoping decision, or, if shallow non-transitive body reflection is
   wanted for its own sake, decide whether it belongs in this RFC or a separate one.

---

## References

- RFC-0092 (Comptime Core) — `type`-as-value, `typeinfo`, single-declaration `emit`
  this RFC generalizes
- RFC-0093 (Derive Registration) — genuinely independent sibling; neither RFC depends
  on the other's specific mechanism beyond RFC-0092
- RFC-0008 (Aspect Objects) — the dynamic-dispatch limit §4 relies on to scope body
  reflection out of this RFC
- `reports/substructural-types/algebraic-effects.md` — §11.1's tracked IO effect, the
  recommended mechanism for audit-style motivations (§4), in place of body reflection
- Prior art: Rust `matches!`/`dbg!` (motivating pattern-as-argument and source-capture
  cases); compile-time-validated query-builder libraries in macro-free languages
  (motivating comptime-on-strings for embedded DSLs); `syn`/proc-macro span-tracked
  diagnostics (motivating §3's span-aware `compileError`)

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
