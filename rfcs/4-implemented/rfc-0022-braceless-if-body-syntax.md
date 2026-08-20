---
id: rfc-0022
title: "Braceless if body syntax"
date: '2026-05-23'
---

## Summary

Allow `if` expressions to accept a single expression as the body without requiring braces, e.g. `if (condition) expr;`.

---
:
## Motivation

Currently, every `if` body must be a block (`{ ... }`), even for trivial single-expression branches. This is unnecessarily verbose for simple cases like `if (debug) print_state();`. Many Rust-inspired languages (C, Swift, Kotlin) permit braceless single-expression bodies as a convenience form.

---

## Proposal

Extend the `if` grammar to accept either a `block` or a single `expr` as the body:

```
if_expr = { "if" ~ "(" ~ expr ~ ")" ~ (block | expr) ~ ("else" ~ (if_expr | block | expr))? }
```

A bare expression body is sugar for a block with that expression as its tail:

```
if (condition) expr;
// equivalent to
if (condition) { expr; }
```

**Expression context:** A braceless `if` without an `else` branch produces `Unit` and may only appear in statement position. A braceless `if`–`else` may appear in expression position if both branches have the same type, identical to braced `if`–`else`.

> **Status — corrected (2026-08-19, found while linking Coverage Checklist
> fixtures).** "May only appear in statement position" does not describe the shipped
> behavior. Verified directly against the built interpreter:
> `let value = if (true) println("side effect");` runs successfully — a no-`else`
> braceless `if` is accepted as a `let` binding's initializer, which is expression
> position, not statement position. The implementation permits a no-`else` braceless
> `if` (Unit-typed) anywhere an expression of type `Unit` is accepted; nothing
> restricts it to appearing only as a bare statement. Left as historical record
> rather than silently edited. The Coverage Checklist item below that transcribes
> this claim (§2) is deliberately left uncited pending a decision on which side —
> this text or the implementation — is the intended design; tracked as
> metel-core#750.

**Parser normalization:** The parser wraps the bare expression in a synthetic `Block` (same technique used today for `else if`), so no changes are required downstream in the type checker or evaluator.

---
:
## Alternatives Considered

**Reject braceless bodies entirely.** Braces are explicit and eliminate ambiguity. This is Metel's current behavior. Rejected because it is overly strict for trivial single-expression branches.

**Allow braceless bodies only in statement position.** Prevents use as an expression even with an `else` branch. Overly restrictive — `let x = if (flag) a else b;` is unambiguous and useful.

**Allow braceless bodies without a semicolon.** `if (condition) expr` with no terminator is syntactically ambiguous when followed by another expression on the same line. Requiring a `;` at the statement level avoids this ambiguity.

> **Status — corrected (2026-08-19, found during a Coverage Checklist audit).** The
> shipped grammar/parser does not actually enforce the `;` this rejected alternative's
> rationale describes. Verified directly against the built interpreter:
> `if (debug) println("hi")` with no trailing semicolon runs correctly, both as the
> last statement in a block and followed immediately by another statement on the next
> line — no ambiguity error, no parse failure. The semicolon requirement recorded above
> was this RFC's own reasoning for rejecting the braceless-without-semicolon
> alternative; it does not describe the behavior the implementation actually shipped
> with. Left as historical record rather than silently edited; no fixture-testable
> claim in this RFC's own Coverage Checklist below asserts the semicolon is required,
> so this correction doesn't change what's covered.

---

## Decisions

1. **Braceless `if`–`else` in expression position: allowed.** When both branches have matching types, a braceless `if`–`else` may appear in expression position, identical to the braced form.
2. **Nested braceless bodies: allowed only when the inner `if` has no `else`.** `if (a) if (b) expr;` is valid. `if (a) if (b) x; else y;` is a parse error — the outer body must use braces whenever the inner `if` has an `else` branch. This eliminates the dangling-else ambiguity entirely.
3. **Mixing braced and braceless arms: not allowed.** Both the `then` and `else` arms must use the same style — either both braced (`block`) or both braceless (`expr`). A parse error is emitted for mismatched styles.

---
:
## Timing Recommendation

Target v0.3. This is a pure syntax extension with no type system or evaluator impact. The three-file change (grammar, parser, spec) is self-contained and low risk.

---

## References

- Language spec: `docs/public/reference/spec.md`
- `docs/public/reference/spec/expressions.md` — `if` expression section
- `metel-interpreter/src/grammar.pest` line 151 — current `if_expr` rule
- `metel-interpreter/src/parser/mod.rs` line 513 — `parse_if_expr`

## Coverage Checklist (added 2026-08-19, not part of the original RFC; corrected
2026-08-19: item 2 restated to match verified behavior, see metel-core#750)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for ADR-0049 citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. If branches may use a single braceless expression

An `if` branch may be a single expression without braces, as in `if (condition) expr;`.

### 2. A braceless if without else has type Unit

A braceless `if` that has no `else` branch has type `Unit`. It is not restricted to
statement position -- like any other `Unit`-typed expression, it may appear anywhere
an expression of that type is accepted, including as a `let` binding's initializer.
(Resolved 2026-08-19, metel-core#750: the RFC's own "may only appear in statement
position" claim does not match the shipped grammar/parser, and `docs/public/reference/
spec/expressions.md`'s actual restriction list for braceless bodies -- arm-style
consistency, dangling-else, no inter-arm semicolon -- has never listed a
position restriction either. The implementation and the published spec already
agreed; only this RFC's own text and this checklist item were stale.)

### 3. A braceless if-else may be an expression

A braceless `if`-`else` may appear in expression position when its two branches have the
same type, with the same result behavior as a braced `if`-`else`.

### 4. Nested braceless if bodies avoid dangling else ambiguity

`if (a) if (b) expr;` is valid, but an inner braceless `if` with an `else` cannot serve
as the outer braceless body. The outer body must be braced in that case.

### 5. An if-else must use one branch-body style consistently

The `then` and `else` arms must both be braced blocks or both be braceless expressions;
mixing the two styles is a parse error.
