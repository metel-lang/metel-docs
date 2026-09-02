---
id: rfc-0164
title: "Mutating Closures with a Propagating ? Are Call-Once"
date: '2026-09-02'
status: draft
target: v0.13.1
updated: '2026-09-02'
---

> **Follow-up to RFC-0153 (Closure Mutation Axis), opened 2026-09-02.** RFC-0153's
> early-exit rule (§1a, spec `dynamics-13`) ships in v0.13.0 as: a plain `var` closure
> whose body exits early via `?` or `return` is left as an ordinary value with mutated
> captured state and stays callable — a later call runs the body from the top over that
> state. That is consistent with how a `&var self` method leaves its receiver, and it is
> what v0.13.0 ships. This RFC proposes tightening the `?` half of it for **v0.13.1**: a
> `var` closure body that can `?`-propagate is `once`. It is **not** a v0.13.0 blocker and
> does not change anything about `once` closures, `return`, or `reading` closures.

## Summary

A closure whose function type is `var` (mutating, RFC-0153) and whose body can propagate
an error out via `?` — an implicitly-chosen exit that can land at any `?` in the body,
mid-mutation — is classified `once` (call multiplicity, RFC-0134). It is consumed at the
call expression like any other `once` closure, so there is never a live `var` closure
sitting in a partially-mutated, arbitrarily-chosen intermediate state that a caller can
invoke again.

An explicit `return` does **not** trigger this: the author chose that exit point, so the
state it leaves is designed rather than incidental.

## Motivation

RFC-0153 §1a settled that `var`-closure write-back is *in place, not transactional* — one
cleanup path, no rollback. For an **explicit `return`** that is unremarkable: the author
wrote `if done { return acc; }`, picked exactly where the body stops, and knows what the
environment holds there. Calling the closure again over that state is their design.

For **`?`** it is different. `foo(x)?` exits at whatever point `foo` happens to return
`Err`. A body with several `?` operators can be left in any of several partial states
depending on which one fired — and the author did not choose "stop here, with `acc`
holding three of the five pushes and `count` at 3." The closure's behaviour on a
*subsequent* call then depends on how far a *previous* call got before an error the caller
may never have inspected. That is a quiet footgun, and it is exactly the kind of
state-after-a-recoverable-error hazard the mutation axis exists to make visible.

```metel
// v0.13.0: `add_all` is `var`, and still callable after a mid-loop `?`.
let add_all := [&var acc] var (items: List<Item>) -> () {
    for item in items {
        acc.push(parse(item)?);   // an `Err` here leaves `acc` half-filled...
    }
};
add_all(batch_a);   // returns Err after 3 of 7 — `acc` now holds 3
add_all(batch_b);   // ...and this call appends to those 3. Intended? Unclear from the type.
```

Under this RFC `add_all` is `once var`, so the second call is a compile error, and the
author must decide: lift the `parse` out of the closure, handle the error inside it, or
accept that the closure is single-shot.

## Proposal

### 1. The rule

During the closure-creation-site analysis that RFC-0134 §2 and RFC-0153 §1 already run
over the body's control-flow graph:

> If the closure's `call_mutation` is `mutating` **and** some path from entry can reach a
> `?` operator whose error type propagates out of the body (is not caught by an enclosing
> handler within the same closure), the closure's `call_multiplicity` is **`once`**.

This is a *classification*, not a written qualifier — like `[&var x]` forcing `mutating`
(RFC-0153 §1). A closure that also moves a non-`Copy` capture out is `once` for that
reason too; the two causes are not additive, `once` is `once`.

"Can reach" uses the same **syntactic-conservative** reachability standard RFC-0134 §2
already defines for its consumption analysis: a `?` counts if a path to it exists in the
CFG, with no constant-folding of branch conditions and no dead-code pruning beyond what
the analysis already performs. A `?` the analysis itself proves unreachable does not
count.

### 2. `?` versus `return`

Only `?` triggers the rule. `return`, `break`, and `continue` are explicit,
author-placed exits; the environment state at an explicit `return` is a designed value.
`?` is an implicit exit whose position is determined by runtime error, not by the author,
so the partial state it leaves is incidental. A body that has both an explicit `return`
and a propagating `?` is `once` on account of the `?`.

A `?` that is **handled inside the closure body** — its `Err` matched, recovered, or
converted so nothing propagates past the closure boundary — does not count. The rule is
about errors *leaving* the closure mid-mutation, not about `?` as a token.

### 3. Composition with `once`

`once var` is already a well-formed `Type::Fun` (RFC-0153 §4). This RFC makes it the
*classified* type of a `?`-propagating `var` body; nothing about `once`'s own semantics
changes. In particular, RFC-0134 §2's operational rule still holds: a `once` call
**consumes the callee place at the call expression, before the body runs**. So by the
time the body reaches its first `?`, the closure value has already been moved out of the
caller's hands — there is no live closure for the "what partial state is it in" question
to be asked about. The partially-mutated environment aggregate is dropped (still-owned
fields only) when the moved value goes out of scope, per RFC-0153 §1a "Captured `Drop`".

Widening (RFC-0152) is unaffected: `once` still satisfies a `once` slot and not a `many`
slot, and a `once var` value flows wherever a `once var` or more-permissive slot is
expected.

### 4. Scope: by-value captures and `[&var x]`

The rule is stated **uniformly** — any `mutating` closure with a propagating `?`, whether
it mutates its own by-value captures (write-back) or drives mutation through a `[&var x]`
reference. For the `[&var x]` case the partial state lives in the outer `x` and is already
caller-visible, so forcing `once` there buys less; but a uniform "a `var` body that can
`?`-out is `once`" is simpler to teach and to implement than a rule that inspects capture
kinds, and it never *under*-restricts. See Open Question 3.

### 5. Relationship to RFC-0153's shipped rule

RFC-0153 §1a and spec `dynamics-13` keep their v0.13.0 wording for the **`return`** case
unchanged. Their **`?`** clause gets a carve-out: for a `var` closure the `?` path no
longer arises as "a later call over partial state," because the closure is `once` and was
consumed at the call expression. `dynamics-13`'s `once` / `once var` paragraph already
covers what happens — this RFC just moves `?`-capable `var` bodies into it.

## Migration

Breaking for any v0.13.0 code that calls a `?`-propagating `var` closure more than once.
Since Metel has no public users this is a plain corpus sweep (RFC-0050 "Migration (no
edition gate)"), but it is a **type-level behaviour change**, which is why it is v0.13.1
rather than folded into v0.13.0's cluster: v0.13.0 ships the looser rule plus RFC-0153's
reword, and this tightens it once the cluster has settled.

Three rewrites for an affected site:

1. **Lift the fallible part out.** `let parsed = parse(item)?;` at the call site, then a
   closure that only `push`es — infallible, stays `var`, stays reusable.
2. **Handle the error inside the body.** `match parse(item) { Ok(v) => acc.push(v), Err(e)
   => log(e) }` — nothing propagates, stays `var`.
3. **Accept `once var`.** The closure is genuinely single-shot; the call site moves it.

## Alternatives considered

### Status quo (what v0.13.0 ships)

A `?`-propagating `var` closure stays `var` and callable; RFC-0153's reword makes clear it
is "an ordinary value with mutated state," not a resumable one. Consistent with `&var
self` methods, which also leave their receiver mid-mutated and stay callable. The cost is
the footgun above: the type does not signal that a second call runs over an
error-determined partial state. This RFC argues that signal is worth a restriction; a
reasonable reviewer may disagree and keep the status quo.

### Runtime poison

Keep the closure `var`; make a call *after* a `?`-exit a runtime error (`R00xx`). Dynamic
rather than static — the author learns at runtime, not at the definition site — and it
needs a new per-closure-value "errored" bit and a new error code. Weaker than making the
type say `once`.

### Transactional rollback

Restore the captured environment to its pre-call state on a `?`-exit. RFC-0153 §1a
explicitly rejected this: it would need a second cleanup path that can disagree with the
in-place one about what state the aggregate is in, and it is a large mechanism for a
narrow case. Not revisited here.

## Relationship to existing RFCs

- **RFC-0153 (Closure Mutation Axis, `4-implemented`)** — this amends the `?` half of §1a
  "Early exit" and spec `dynamics-13`; the `return` half and everything else are
  unchanged.
- **RFC-0134 (Closure Call Capability, `4-implemented`)** — supplies `once` and its
  "consume at the call expression" rule; the classification here rides RFC-0134 §2's
  existing CFG analysis.
- **RFC-0152 (Function-Type Multiplicity Widening, `4-implemented`)** — unaffected; `once
  var` widens like any other `once` value.
- **RFC-0122 (Borrow Checking, `1-under-review`)** — orthogonal. RFC-0122 makes the
  `mutating`-call exclusive-borrow rule static; this RFC is about *multiplicity*, not
  borrow shape. No dependency either way.
- **RFC-0140 (Algebraic Effects, `1-under-review`)** — if `?` is later expressed through
  the effect/handler machinery, "a `?` that propagates past the closure" becomes "an
  effect that is not handled within the closure body"; the rule's phrasing should track
  whatever RFC-0140 settles for `?`'s desugaring, but the intent is stable.

## Open Questions

1. **Reachability standard.** Adopt RFC-0134 §2's syntactic-conservative standard verbatim
   (a `?` counts if a CFG path exists, no branch folding), or a tighter one? Leaning:
   verbatim — the two analyses share a pass and should not disagree.
2. **`?` in a nested closure literal inside the body.** A `?` inside an *inner* closure
   that the outer body only constructs (never calls) does not propagate out of the outer
   body — it belongs to the inner closure's own classification. Confirm the analysis walks
   only the outer body, as RFC-0134 §2's does.
3. **`[&var x]`-only closures.** Uniform rule (any `?`-capable `var` body is `once`), or
   scope it to closures with at least one by-value mutable capture, since the `[&var x]`
   partial state is already caller-visible? Leaning: uniform, for simplicity; the
   restriction is never unsound, only sometimes stricter than strictly needed.
4. **Diagnostic.** A second call to such a closure is the ordinary moved-value error
   (RFC-0134 §2's `PartialMoveUsedAsWhole`-shaped message). Does it need a note explaining
   *why* the closure is `once` ("its body can propagate `?` mid-mutation"), the way
   RFC-0134 §2 names the consumed capture? Leaning: yes, a one-line cause note.

---

## Decision

**Outcome:** *(pending — `0-draft`, opened 2026-09-02 as a follow-up to RFC-0153. This is
Option B from RFC-0153's early-exit review; v0.13.0 shipped the reword-only alternative
and this records the tightening for a later cycle.)*
**Target:** **v0.13.1** *(intent; confirmed on transition to `2-accepted`).*
