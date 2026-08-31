---
id: rfc-0131
title: "Hoist let/var Bindings to the Top of Their Containing Block"
date: '2026-08-09'
status: draft
target:
---

## Summary

Extend the existing fun-declaration hoisting rule to let/var bindings, so a block's declaration order stops mattering for name visibility the same way it already doesn't for functions -- surfaced while fixing metel-core#656, where a nested fun's forward-reference support had to be narrowed specifically because let/var visibility is NOT hoisted today.

---

## Motivation

`fun` declarations are already hoisted: "All `fun` declarations in a block are mutually
visible to each other and to all other statements in that block, regardless of
declaration order" (`declarations.md`, "Scoping and Shadowing"). `let`/`var` are
explicitly not: "`let` and `var` declarations are sequential — a binding is visible only
from its declaration point to the end of its containing block." One block, two different
name-visibility rules depending on which keyword introduced the name — and nothing about
the *keyword* is what actually determines whether hoisting is safe or not.

This stopped being a purely theoretical asymmetry while fixing
[metel-core#656](https://github.com/metel-lang/metel-core/issues/656): the evaluator
built a nested `fun`'s closure only when the ordinary sequential statement loop reached
its own declaration, so calling it from an earlier statement in the same block failed
with "undefined variable", even though the type checker's own hoisting pass already
accepted the program. The fix taught the evaluator to build every `fun` in a block
up front, before any statement runs — but a `fun` that closes over a `let`/`var` in the
same block breaks that: the eager build captures the block's environment *before
anything in the block has run*, so a `let` sitting between an early call and the callee's
own declaration line is invisible to the eagerly-built closure even though it had, by the
time of the call, already executed. Not a merely confusing error — a wrong one: the same
already-initialized variable goes missing depending on an unrelated detail (has the loop
reached the *fun's* declaration yet, not the *let's*).

The shipped fix (metel-core#658) works around this by narrowing the guarantee: a block
gets eager, order-independent `fun` hoisting only if it contains **no** `let`/`var` at
all. Mix the two and every `fun` in that block reverts to the old, declaration-order-
sensitive behavior. This is safe and passes the full test suite, but it's a workaround,
not a resolution — it exists specifically because `let`/`var` visibility isn't hoisted,
so the evaluator can't tell, in general, whether a name a `fun` closes over is "already
guaranteed to have run by any call site" or not. If `let`/`var` bindings were hoisted the
same way `fun` declarations are, that distinction wouldn't need to exist: any name
declared in a block would carry a single, well-defined answer to "has this run yet,
right now" — including the `let`/`var` case that today makes the answer depend on
program order in a way `fun` alone doesn't.

---

## 1. The central problem: shadowing

The current spec explicitly permits declaring the same name twice with `let`/`var` in
one block, each declaration shadowing the previous one from its own point forward:

```metel
fun main() {
    let x := 1;
    fun get_x() -> i64 { x }
    let a := get_x();   // a = 1
    let x := 2;
    let b := get_x();   // b = 1 -- get_x captured the FIRST x, unaffected by the shadow
    println("a=${a} b=${b}");
}
```

This isn't hypothetical — it's the exact case that had to be re-verified while fixing
#656, and it must keep working under any hoisting design: `get_x`'s closure captured a
specific binding, and a *later* declaration of the same name must not retroactively
change what that closure sees.

Hoisting `let`/`var` "the same way `fun` is hoisted" — one placeholder slot per name,
created at the top of the block, filled in when the declaration statement runs — does
not obviously survive this example. If `x`'s hoisted slot is a single, shared location
that every reference to the name `x` in this block resolves to, then `let x = 2`
overwriting that slot would make `get_x()` return 2 the second time, breaking the
worked example above. Whatever design this RFC settles on has to say precisely what
happens when the same name is hoisted-and-then-shadowed in one block, and that answer is
not free — it's the reason this is a draft with unresolved questions rather than a
one-line spec amendment.

## 2. Sketched designs

**A. Name-only hoisting with a temporal-dead-zone read error (closest to JavaScript's
`let`/`const`).** Every `let`/`var` name in a block gets a placeholder slot at the top of
the block, exactly like `fun` does today — so a `fun` closing over it can be built eagerly
and safely, the actual gap #656/#658 ran into. Reading a slot before its own declaration
statement has run is a distinct, clearly-named runtime error ("`x` used before its
declaration"), not "undefined variable" and not a silently wrong value. Redeclaring the
same name with a second `let` in the same block is rejected outright (a compile-time
error) — sidestepping the shadowing question above by making the worked example in §1
illegal in its current form; it would need an inner `{ }` block to shadow `x` instead.
This is the smallest change that actually closes the #658 workaround (a `fun`'s eager
build no longer needs to special-case "does this block contain a `let`/`var`") but it
changes existing, spec'd, working behavior: today's shadowing example is legal and
tested; this design would make it a new compile error.

**B. Full dynamic hoisting, no redeclaration ban.** Same placeholder-slot mechanism as A,
but a second `let x` in the same block is still legal and still shadows — meaning the
runtime has to distinguish *which* declaration of `x` a given reference means, which
can no longer be "whichever one is nearest going backward from here" once `fun`s (and
now `let`/`var`s) are allowed to be referenced before their own declaration point in
program order. This likely needs each reference resolved to a specific declaration's
identity at name-resolution time (the type checker already assigns stable per-declaration
ids for other purposes — see `def_id`/`SymbolId` in `metel-frontend`), with the runtime
keying environment lookups by that identity rather than by name. A materially bigger
change to both the name resolver and the evaluator's environment representation than A,
and unlike A it does not change any currently-legal program's meaning — but it needs a
concrete resolution-by-identity design worked out before it's implementable, not just
this paragraph.

**C. Don't hoist `let`/`var` at all — narrow `fun` hoisting differently instead.** Keep
today's sequential `let`/`var` semantics untouched, and instead give the type checker
(which already computes free variables for other purposes) a free-variable check per
`fun`: only eagerly build a nested `fun` whose body references no `let`/`var` from its
own enclosing block at all, regardless of whether *other* `fun`s in the same block do.
Strictly more precise than #658's per-block gate (a `fun` that only calls its siblings
gets full hoisting even in a block that also happens to declare an unrelated `let`), but
it's new static analysis with its own room for under-approximation bugs (missing a
reference through a match arm, a closure literal, or similar), and it doesn't remove the
underlying asymmetry this RFC's motivation is about — `fun` and `let`/`var` would still
follow two different visibility rules, just with a more forgiving line between them.

No option is recommended yet. A and B represent a genuine fork (accept a small breaking
change to get a simple mechanism, vs. keep full backward compatibility at the cost of a
resolve-by-identity redesign); C keeps `let`/`var` semantics untouched entirely, at the
cost of not actually resolving this RFC's own motivating asymmetry, only shrinking one
symptom of it.

---

## Alternatives Considered

- **Do nothing; keep #658's per-block gate indefinitely.** Already shipped, already
  correct, and costs nothing further. Rejected as the final answer (though it's exactly
  right as an interim state) because it's a workaround for an asymmetry, not a design:
  a block mixing `fun` and `let`/`var` permanently loses forward-reference support for
  every `fun` in it, including ones that don't touch the `let`/`var` at all.
- **Free-variable-gated `fun` hoisting (§2 Option C)**, recorded above as a design
  sketch rather than here, since it's a real contender, not a rejected one — it's listed
  as an alternative to hoisting `let`/`var` at all, not to doing nothing.

---

## Unresolved Questions

- Which of §2's designs (A, B, or C) should this RFC actually propose? This draft
  deliberately does not choose yet.
- If A: is banning same-block `let`/`var` redeclaration an acceptable breaking change,
  and does existing code (stdlib, fixtures) rely on the pattern being banned?
- If B: what's the concrete resolve-by-identity design — does it reuse `def_id`/
  `SymbolId` as-is, or does environment lookup need a new per-declaration key entirely?
  What does this cost at the evaluator's `Environment` representation, which is
  currently name-keyed throughout?
- Does whichever design is chosen also apply at the top level (module scope), where
  `run_passes` already has its own, independent version of exactly this same
  fun-hoisted/let-sequential split?

---

## References

- [metel-core#656](https://github.com/metel-lang/metel-core/issues/656) — the evaluator
  bug this RFC's motivation traces back to: nested `fun` hoisting typechecked but failed
  at runtime.
- [metel-core#658](https://github.com/metel-lang/metel-core/pull/658) — the shipped fix,
  and the source of the per-block `let`/`var` gate this RFC exists to potentially remove.
- `declarations.md`, "Scoping and Shadowing" — the two visibility rules (`fun` hoisted,
  `let`/`var` sequential) this RFC proposes reconciling.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
