---
id: rfc-0194
title: "Linear Closures and Captures"
date: '2026-10-29'
status: under-review
updated: '2026-10-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/1670'
---

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1670 (Linear types); one open question (spelling of must-call)

## Summary

A closure that captures a `Linear` value (RFC-0089) is itself linear. It must be called
exactly once, it cannot be dropped, and its body must consume what it captured. There is no
new closure syntax and no new closure type: linearity is derived from the captures, as `Copy`
already is (RFC-0134 §1).

```metel
fun finish(t: Token) {                        // Token: Linear
    let release := [t] || { close(t); };      // captures a Linear value: `release` is linear
    release();                                // consumes `release`: exactly once
}

fun forgot(t: Token) {
    let release := [t] || { close(t); };
    // error: `release` captures a Linear value and is never called
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

- **Deferred cleanup.** `let release := [guard] || { close(guard); };` registered now, run later.
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
launders the obligation, unless the closure inherits it.

---

## 1. The rule

### A closure is linear when it captures a linear value

RFC-0089 §1 defines a struct's discipline as the join of its fields' multiplicities. A closure's
captured environment is the same kind of aggregate, so the same join applies: **a closure is
`Linear` iff some by-value capture is `Linear`** (RFC-0089 §2's auto-derived marker aspect, read
over the environment). No annotation is written and none is meaningful, matching RFC-0089 §2:
this is structural composition, not derive-as-codegen.

- A by-value capture is a move (RFC-0157: a bare non-`Copy` capture moves and the capture list is
  required when it would). A `Linear` value cannot be duplicated (RFC-0089 §1: no contraction), so
  `[t.clone()]` is rejected and `[t]` is a move.
- A capture by reference (`[&t]`, `[&var t]`) does not move the value and does not make the closure
  linear. The `Linear` value is still owned outside and must still be consumed there.
- A closure that captures another linear closure is linear, by the same join.
- Capturing a *field* of a linear struct follows RFC-0089 §3: convert with `ToRecord` first and
  capture the resulting field. A partial move out of a plain linear struct is not allowed.

### A linear closure is called exactly once

- **Calling consumes it.** A linear closure is `once` on the call axis (RFC-0134 §2): its call moves
  the environment in, and a second call is a use of a moved value. A linear closure is never `many`.
- **It cannot be dropped.** A scope that ends with a linear closure unconsumed is an error naming the
  closure and the captured linear value, as for any unconsumed `Linear` binding. `drop(f)` does not
  apply: its bound is `T: !Linear` (RFC-0089 §2).
- **Its body consumes what it captured.** Inside the body, the captured linear values are owned
  locals, and the linearity checker requires each to be consumed exactly once on every path.
  Returning a captured linear value is a consumption (`[buf] || -> Buffer { buf }` is valid: the
  caller receives the buffer by calling the closure).
- **It may be consumed by being passed on.** Moving a linear closure into a function, a struct field
  or a return value is a consumption of the binding and transfers the obligation, as for any `Linear`
  value.

Because the closure must be called, and calling runs the body, the "captured value never
consumed inside an uncalled closure" problem (RFC-0049 OQ-1) cannot arise: an uncalled linear
closure is itself an error.

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
| must-call (the callee consumes it exactly once) | yes | yes | yes |

A linear closure is not accepted where the callee may drop it, because the callee could discard the
obligation. A `many` or affine `once` closure is accepted where the callee must call it: it is
simply called once. This is the useful direction of RFC-0049 OQ-3 (a plain closure can go where a
once-callable one is required); the converse, passing a linear closure as a plain one, is unsound.

The written spelling of "must-call" is the one open question (below).

### Worked examples

A one-shot cleanup registered by a function and run by its caller:

```metel
fun with_guard(g: Guard) -> once || -> () {     // must-call return: see Open question
    [g] || { release(g); }                       // linear closure returned: caller must call it
}

fun main() {
    let done := with_guard(acquire());
    // ... work ...
    done();                                      // consumed exactly once
}
```

Rejected, each with a message naming the closure and the linear capture:

```metel
fun never_called(t: Token) { let f := [t] || { close(t); }; }               // never called
fun called_twice(t: Token) { let f := [t] || { close(t); }; f(); f(); }     // used after move
fun not_consumed(t: Token) { let f := [t] || { }; f(); }                    // body does not consume `t`
fun cloned(t: Token)       { let f := [t.clone()] || { close(t); }; }       // a Linear value cannot be duplicated

fun run_maybe(f: once || -> ()) { }                                         // affine `once`: the callee may drop it
fun passes(t: Token)       { let f := [t] || { close(t); }; run_maybe(f); } // rejected: would let the obligation vanish
```

---

## 2. Interactions

- **RFC-0089.** The join rule and the marker aspect are its. This RFC depends on RFC-0089 settling
  its surface (§2.1) and its drop/`!Linear` bound. It does not reopen them.
- **RFC-0134 and RFC-0163.** The call-count axis (`many`/`once`) is unchanged. A linear closure is
  `once` plus the structural `Linear` property; the written surface for "must-call" is co-designed
  with RFC-0163's use-multiplicity surface for function types.
- **RFC-0050, RFC-0157.** No new capture syntax. A linear value captured by move needs its list
  entry, as any move does.
- **RFC-0153.** A linear closure may also be `mutating`. The environment is consumed on its single
  call, so persistent state across calls cannot arise.
- **RFC-0166.** Written function types are move-only. A linear closure is move-only a fortiori.
- **Effects (#1662).** A one-shot continuation is the intended consumer: resumption is the call, and
  abandonment is not available unless the effects design adds an explicit, checked one.
- **Function types and aspects (#739, RFC-0161).** `Linear` over a closure needs the auto-impl
  mechanism (RFC-0096) to reach function types, which today satisfy no aspects. This is a
  prerequisite, not part of this RFC.

---

## Alternatives Considered

1. **Status quo (affine `once` only).** Leaves the laundering hole: a linear value moved into a
   closure can be silently lost. Rejected.
2. **A `linear fun` type and `[move x]` captures (RFC-0046/0049).** A separate closure type and
   capture keyword. RFC-0046 was refused; the shipped capture lists and the single `Type::Fun`
   already carry what it wanted, with linearity derived from captures instead of written.
3. **Auto-generated `Drop` for linear closures (RFC-0049 option B).** Lets the obligation be
   discharged by discarding. Rejected above; reopenable with the cleanup design.
4. **Strengthen `once` to mean forced consumption everywhere.** RFC-0134 names this as a way to
   reopen its decision. It would make every `once` closure linear, including ones that capture
   nothing linear, and break code that drops an unused `once` callback. Rejected: linearity follows
   the captures, so only closures that need it pay for it.
5. **Let a linear closure be passed where a plain `once` is expected.** Unsound: the callee may drop it.

---

## Open question

**How is "must-call" written in a function type?** A parameter, return type or field needs a way to
say "the holder must call this exactly once", distinct from affine `once` ("may call once"). Candidates:
split RFC-0134's `once` into `once` (affine) and a stronger form; use the `Linear` aspect as a bound
(`F: Linear + once || -> ()`); or a modifier on the type (`linear || -> ()`). The rules above do not
depend on the spelling. It is co-designed with RFC-0163, which owns the function-type use-multiplicity
surface, so it is settled there or here with that RFC's agreement.

---

## Specification impact

Spec text lands only at `3-integrated`, and only after RFC-0089. `reference/spec/functions.md`
Closures: a legality rule that a closure capturing a `Linear` value is `Linear`, a rule that it is
called exactly once and cannot be dropped, and the parameter-acceptance table. `ownership.md`:
the linear-capture rules beside the capture rules. No new error code is proposed: the diagnostics are
the existing unconsumed-linear and use-after-move errors with the closure and capture named.

## Implementation notes

Implementation detail goes in an ADR at `3-integrated`. The constraints:

- The environment's multiplicity is the join over captures, computed where `Copy` is computed for a
  closure today (RFC-0134 §1).
- The linearity checker (RFC-0089) runs over the closure body with captures as owned locals.
- Nothing here needs destructors (#261) or a closure `Drop`.

## References

- RFC-0089 (Linear Types): the lattice, the join rule, the marker aspect.
- RFC-0134 (Closure Call Capability) §§1, 2, 5 and "Decision: affine `once`, not linear".
- RFC-0050, RFC-0153, RFC-0157, RFC-0163, RFC-0166, RFC-0096.
- RFC-0049 (superseded by this RFC), RFC-0046 (refused): the earlier `linear fun` design.
- metel-core#739, #261, #1662.

---

## Decision

**Outcome:** *(pending)*
