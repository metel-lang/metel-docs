---
id: rfc-0194
title: "Linear Closures and Captures"
date: '2026-10-29'
status: under-review
updated: '2026-10-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/1670'
---

> **Design settled (2026-11-07, language owner), decision D14.** The rules of this RFC are accepted in design,
> including the generic-capture rule (a closure over a value of bare type `T` is declared `linear` or the function
> bounds `T: Discard`; there is no conditional closure class). Formal acceptance of the RFC is a separate step.

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1670 (Linear types); one open question (spelling of must-call)

## Summary

A closure that captures a `Linear` value (RFC-0089) must be declared `linear`: written in its
prefix and in any function type that names it. A linear closure must be called exactly once,
it cannot be dropped, and its body must consume what it captured. Nothing is inferred
(RFC-0089 amendment, 2026-11-06): a closure that captures a linear value without the keyword is
an error whose fix-it adds it, and `linear` may also be written on a closure with no linear
capture, to demand a must-call callback. A `linear` closure is `once` on the call axis, so the two
are never written together.

```metel
fun finish(t: Token) {                        // Token: Linear
    let release := [t] linear || { close(t); };   // captures a Linear value: declared `linear`
    release();                                // consumes `release`: exactly once
}

fun forgot(t: Token) {
    let release := [t] linear || { close(t); };
    // error: `release` is linear and is never called
}

fun undeclared(t: Token) {
    let release := [t] || { close(t); };
    // error: the closure captures linear `t`; declare it `linear`: `[t] linear || { ... }`
}
```

This closes the gap RFC-0134 §5 left on purpose ("no `linear` vocabulary, no `Drop`-for-closures,
and deliberately not waiting on the rest of the linear-types tower") and replaces RFC-0049, which
was written on RFC-0046 (refused). It builds on the shipped closure model (RFC-0050 capture lists,
RFC-0134 call capability, RFC-0153 mutation axis, RFC-0157 move default) and on RFC-0089.

---

## Motivation

`Linear` (RFC-0089) makes a value's consumption mandatory: a file handle, a lock guard, a
one-shot capability token. Closures are how deferred work is written, and deferred work is where
such values end up:

- **Deferred cleanup.** `let release := [guard] linear || { close(guard); };` registered now, run later.
- **A one-shot continuation.** An effect handler's resumption is a closure that must be resumed
  or explicitly abandoned. The effects design draft (metel-core#1662) needs "exactly-once
  consumption" and says it "requires the separately designed linear-type system".
- **Transferring authority.** A capability moved into a callback must reach the callee, not
  vanish if the callback is never called.

Today the closure model cannot express this. RFC-0134's `once` is **affine** by decision: a
call-once closure that is never called is silently dropped. That is the wrong answer for a closure
that owns a linear value, because dropping it discharges the closure while the captured value is
silently lost. RFC-0134 recorded the condition for revisiting its decision: when destructors (#261)
run and a real bug appears. Linear captures are the case that forces the question without needing
destructors, because the obligation is on the closure, not on a `Drop` body.

### What goes wrong without a rule

```metel
let release := [t] || { close(t); };   // t moved into the closure
// ... scope ends; `release` is an ordinary affine closure: dropped, `t` never closed
```

`t` is `Linear`, so the checker would reject dropping `t` directly. Moving it into a closure
launders the obligation, unless the closure carries it. The rule is that it carries it explicitly:
the example above is an error, and the fix-it writes `[t] linear || { close(t); }`.

---

## 1. The rule

### A closure that captures a linear value is declared `linear`

RFC-0089 declares a type's class and checks it against its fields. A closure's captured environment is the same kind
of aggregate, so the same check applies: **a closure that captures a `Linear` value by value must be declared
`linear`**, and the compiler reports the missing keyword at the capture. The keyword sits in the literal's prefix
(`[t] linear || .{ ... }`) and in a function type (`linear || -> ()`). Its position follows `copy`, `once` and `var`
(RFC-0219): order-insensitive in a type, first in a literal's prefix. `linear` implies `once`, and a `linear` closure
may have no linear capture at all (a fiat `linear`, a must-call callback). `copy` and `linear` are mutually exclusive.

- A by-value capture is a move (RFC-0157: a bare non-`Copy` capture moves and the capture list is
  required when it would). A `Linear` value cannot be duplicated implicitly (RFC-0089 §1: no contraction), so
  `[t]` is a move; `[t.clone()]` is legal only if the type satisfies `Clone` (written or derived, RFC-0089 §2).
- A capture by reference (`[&t]`, `[&var t]`) does not move the value and does not require `linear`. The `Linear` value is still owned outside and must still be consumed there.
- A closure that captures another linear closure captures a linear value, so it must be declared `linear` too.
- Capturing a *field* of a declared linear struct is not possible: a declared linear aggregate has no partial moves
  (RFC-0089 section 2, "Consuming a linear aggregate"). Destructure it totally and capture the resulting linear
  binding.

### A linear closure is called exactly once

- **Calling consumes it.** A linear closure is `once` on the call axis (RFC-0134 §2): its call moves
  the environment in, and a second call is a use of a moved value. A linear closure is never `many`.
- **It cannot be dropped.** A scope that ends with a linear closure unconsumed is an error naming the
  closure and the captured linear value, as for any unconsumed `Linear` binding. `drop(f)` does not
  apply: its bound is `T: Discard` (RFC-0089 §2.2), which a linear closure does not satisfy.
- **Its body consumes what it captured.** Inside the body, the captured linear values are owned
  locals, and the linearity checker requires each to be consumed exactly once on every path.
  Returning a captured linear value is a consumption (`[buf] linear || -> Buffer { buf }` is valid: the
  caller receives the buffer by calling the closure).
- **It may be consumed by being passed on.** Moving a linear closure into a function, a struct field
  or a return value is a consumption of the binding and transfers the obligation, as for any `Linear`
  value.

Because the closure must be called, and calling runs the body, the "captured value never
consumed inside an uncalled closure" problem (RFC-0049 OQ-1) cannot arise: an uncalled linear
closure is itself an error.

### Function values are `Discard` unless `linear`

A closure that captures a linear value must be declared `linear`, so every closure not declared `linear` captures only
`Discard` values and is itself `Discard`. A written function type that is not `linear` therefore guarantees `Discard`
(RFC-0089 section 2.2); a `linear` function type is not `Discard`. A closure that captures a value of bare type `T` captures a possibly-linear value, so it must be declared `linear` or the function must bound `T: Discard`.

### No `Drop` for closures

A closure type is not `Drop` (function types satisfy no aspects today, #739), and this RFC does not
make it so. RFC-0049's proposal to synthesize a `Drop` for `linear fun` closures is not adopted: it
would let a linear closure be discarded and have its captured values cleaned up implicitly, which
removes the obligation this RFC adds, and destructors do not run yet (#261). The way to abandon a
linear closure is to call it. If real code needs a cheaper abandonment, that is a separate decision
and belongs to the cleanup design, not to the closure model.

### Passing a linear closure: which parameters accept it

A parameter's written function type says how the callee may use the closure (RFC-0134 §3):
`many` by default, `once` when written. The callee's freedom determines what it may be given:

| the parameter expects | accepts a `many` closure | accepts an affine `once` closure | accepts a linear closure |
|---|---|---|---|
| `many` (the default) | yes | no | no |
| `once` (affine: the callee may drop it) | yes | yes | **no** |
| `linear` (the callee consumes it exactly once) | yes | yes | yes |

`-> linear || -> ()` names a **linear callable type**. A binding of a linear type needs no qualifier, so the caller may
write a plain `let`; RFC-0220's rule that a linear result is bound with `linear let` concerns the `-> linear T`
return *qualifier* on a type that is not itself linear.

**Strengthening and invocation.** Passing a reusable or `once` closure into a `linear` slot strengthens it at the
boundary, and an invocation through a `linear` function type consumes the slot even when the supplied callable was
reusable. Occurrences of `linear` in nested function types match exactly, as `copy` does (RFC-0219 rule 4).

A linear closure is not accepted where the callee may drop it, because the callee could discard the
obligation. A `many` or affine `once` closure is accepted where the callee must call it: it is
simply called once. This is the useful direction of RFC-0049 OQ-3 (a plain closure can go where a
once-callable one is required); the converse, passing a linear closure as a plain one, is unsound.

The written spelling of "must-call" is `linear` (decided 2026-11-06); a reusable or `once` closure may be passed where
`linear` is expected, since the callee simply calls it once.

### Worked examples

A one-shot cleanup registered by a function and run by its caller:

```metel
fun with_guard(g: Guard) -> linear || -> () {   // a linear callable type: a plain `let done := with_guard(..)` is legal (see below)
    [g] linear || { release(g); }                // linear closure returned: caller must call it
}

fun main() {
    let done := with_guard(acquire());
    // ... work ...
    done();                                      // consumed exactly once
}
```

Rejected, each with a message naming the closure and the linear capture:

```metel
fun never_called(t: Token) { let f := [t] linear || { close(t); }; }         // never called
fun called_twice(t: Token) { let f := [t] linear || { close(t); }; f(); f(); } // used after move
fun not_consumed(t: Token) { let f := [t] linear || { }; f(); }              // body does not consume `t`
fun undeclared(t: Token)   { let f := [t] || { close(t); }; f(); }           // captures linear `t`: write `linear`
fun cloned(t: Token)       { let f := [t.clone()] linear || { close(t); }; } // f is never called, and the original `t` is never consumed (the clone also needs `Token: Clone`)

fun run_maybe(f: once || -> ()) { }                                          // affine `once`: the callee may drop it
fun passes(t: Token)       { let f := [t] linear || { close(t); }; run_maybe(f); } // rejected: would let the obligation vanish
```

---

## 2. Interactions

- **RFC-0089.** The declared class, its check against the fields, and the marker aspect are its (amendment
  2026-11-06). This RFC depends on RFC-0089 settling its surface (§2.1) and `Discard`. It does not reopen them.
- **RFC-0134, RFC-0163 and RFC-0219.** The call-count axis (`many`/`once`) is unchanged. A linear closure is
  `once` plus the declared `Linear` property; the written surface for "must-call" is `linear`, in the position
  RFC-0219 gives `copy`.
- **RFC-0050, RFC-0157.** No new capture syntax. A linear value captured by move needs its list
  entry, as any move does.
- **RFC-0153.** A linear closure may also be `mutating`. The environment is consumed on its single
  call, so persistent state across calls cannot arise.
- **RFC-0166.** Written function types are move-only. A linear closure is move-only a fortiori.
- **Effects (#1662).** A one-shot continuation is the intended consumer: resumption is the call, and
  abandonment is not available unless the effects design adds an explicit, checked one.
- **Function types and aspects (#739, RFC-0161).** A closure's `Linear` class is declared (the `linear` keyword) and
  checked against its captures, so it needs no auto-impl. `Copy` and `Discard` for function types come from the Copy
  migration's std impls; function types satisfy no aspects today. This is a prerequisite, not part of this RFC.

---

## Alternatives Considered

1. **Status quo (affine `once` only).** Leaves the laundering hole: a linear value moved into a
   closure can be silently lost. Rejected.
2. **A `linear fun` type and `[move x]` captures (RFC-0046/0049).** A separate closure type and
   capture keyword. RFC-0046 was refused; the shipped capture lists and the single `Type::Fun`
   already carry what it wanted, with linearity written in the closure prefix and checked against the captures.
3. **Auto-generated `Drop` for linear closures (RFC-0049 option B).** Lets the obligation be
   discharged by discarding. Rejected above; reopenable with the cleanup design.
4. **Strengthen `once` to mean forced consumption everywhere.** RFC-0134 names this as a way to
   reopen its decision. It would make every `once` closure linear, including ones that capture
   nothing linear, and break code that drops an unused `once` callback. Rejected: linearity follows
   the captures, so only closures that need it pay for it.
5. **Let a linear closure be passed where a plain `once` is expected.** Unsound: the callee may drop it.

---

## Open question

**How is "must-call" written in a function type? Resolved 2026-11-06: `linear`**, a modifier in the same prefix
position as `copy`, `once` and `var` (`linear || -> ()`). The candidates considered were a stronger form of `once`
and a `Linear` bound on a type parameter. The modifier won because it is explicit, uniform with `copy` (RFC-0219) and
needs no new bound form. `copy` and `linear` are mutually exclusive, and `linear` implies `once`.

Still open: the diagnostic text and error codes, and whether a `linear` function type may be named by a type
alias (RFC-0160).

---

## Specification impact

Spec text lands only at `3-integrated`, and only after RFC-0089. `reference/spec/functions.md`
Closures: a legality rule that a closure capturing a `Linear` value is `Linear`, a rule that it is
called exactly once and cannot be dropped, and the parameter-acceptance table. `ownership.md`:
the linear-capture rules beside the capture rules. No new error code is proposed: the diagnostics are
the existing unconsumed-linear and use-after-move errors with the closure and capture named.

## Implementation notes

Implementation detail goes in an ADR at `3-integrated`. The constraints:

- The environment's class is checked against the declared one (a closure that captures a linear value must be
  declared `linear`), at the point where `Copy` is computed for a
  closure today (RFC-0134 §1).
- The linearity checker (RFC-0089) runs over the closure body with captures as owned locals.
- Nothing here needs destructors (#261) or a closure `Drop`.

## References

- RFC-0089 (Linear Types): the lattice, the declared class and its check, the marker aspect.
- RFC-0134 (Closure Call Capability) §§1, 2, 5 and "Decision: affine `once`, not linear".
- RFC-0050, RFC-0153, RFC-0157, RFC-0163, RFC-0166, RFC-0096.
- RFC-0049 (superseded by this RFC), RFC-0046 (refused): the earlier `linear fun` design.
- metel-core#739, #261, #1662.

---

## Decision

**Outcome:** *(pending)*
