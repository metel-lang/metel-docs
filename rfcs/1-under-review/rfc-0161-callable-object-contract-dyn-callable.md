---
id: rfc-0161
title: "Callable Object Contract (dyn Callable)"
date: '2026-09-01'
status: under-review
target: v0.13.1
tracking: 'https://github.com/metel-lang/metel-core/issues/923'
updated: '2026-09-01'
---

> **Status — under review (2026-09-01).** Extracted from the v0.13.0 closure cluster during the third adversarial review; dyn Callable deferred to its own RFC (v0.13.1) rather than shipping a normative default resting on unbuilt RFC-0096/0061 machinery.

## Summary

Define the object-safe form of a closure — `dyn Callable<Args, Ret>` — for the flat
three-field `Type::Fun` closure model that RFC-0134 / RFC-0152 / RFC-0050 / RFC-0153 ship
at v0.13.0. This RFC is deliberately **not** part of that cluster: the v0.13.0 model is
monomorphic (`Type::Fun` is a flat `(code ptr, env ptr)` with three multiplicity fields,
no vtable), and every example and stdlib signature in the cluster is first-order and
concrete. `dyn Callable` is the type-erased case, and it rests on two things that do not
exist at v0.13.0:

- **A callable-receiver contract.** A call under the `call_multiplicity` / `call_mutation`
  axes needs, respectively, a by-value / `&var self` / `&self` receiver. RFC-0008
  (Aspect Objects) rejects by-value object receivers and has specific rules for `&var
  Self`. Whether `Callable::call` is object-safe under RFC-0008 with an axis-selected
  receiver has never been worked out.
- **Marker aspects.** The `CallMany` / `CallShared` / `Copy` markers that a `dyn Callable`
  would carry to record its axis values are auto-impl aspects (RFC-0096, `0-draft`), and
  `Callable<A, B>` itself is RFC-0061 §7.1 / metel-core#893 — "a specification that was
  never built" per RFC-0134's own Open Questions.

RFC-0153 §3 carried an interim "`dyn` erasure default" (bare `dyn Callable` = most
restrictive; `+ CallMany` / `+ CallShared` / `+ Copy` widen). The third adversarial review
of the closure cluster (2026-09-01) flagged that as a normative rule resting on unbuilt
machinery — a forward reference the cluster cannot satisfy at v0.13.0. This RFC is where
that default is designed properly, targeting **v0.13.1**.

**The `Callable` aspect itself is deferred here — not just `dyn Callable`.** The fourth
adversarial review (2026-09-01) confirmed `Callable<A, B>` and its auto-impl for function
types were never built (RFC-0061 §7.1 and RFC-0008 now carry "not implemented"
annotations pointing here). So at **v0.13.0 there is no `Callable` aspect at all**: a
closure is only ever a concrete `Type::Fun`, a generic parameter cannot be bounded `where
F: Callable<…>` (a higher-order function takes a concrete function type — how the stdlib
combinators already work), and `dyn Callable<…>` / `&dyn Callable<…>` / `Box<dyn
Callable<…>>` do not parse. This RFC owns the aspect, its auto-impl, the object form, and
the marker refinements, in full, from v0.13.1.

## Motivation

The flat `Type::Fun` model is fast and static, but it cannot express "some callable of
this shape, chosen at runtime" — a heterogeneous `List<dyn Callable<(), ()>>` of
callbacks, a struct field holding one of several handlers, a plugin boundary. Rust
solves this with `dyn Fn` / `dyn FnMut` / `dyn FnOnce` as an opt-in on top of concrete
closure types with `Fn*` impls. Metel wants the same split (RFC-0153's "recommended
synthesis"): keep `Type::Fun` flat as the default, expose an aspect view for the erased
case.

The design cannot be hand-waved because erasure has to preserve the three axes
soundly:

- A `once` closure erased to `dyn Callable` must still be callable **at most once** —
  the single-call check RFC-0134 §2 does structurally now has to survive erasure, when
  the checker can no longer see the closure literal.
- A `mutating` closure erased to `dyn Callable` still needs the §3 exclusive-borrow
  discipline of RFC-0153 at every call — through a vtable dispatch.
- A non-`Copy` closure erased to `dyn Callable` must not become duplicable.

## Proposal

### 1. The `Callable` aspect

```
aspect Callable<Args, Ret> {
    fun call(...) -> Ret;
}
```

`Args` is a numeric-label row (RFC-0151); `call`'s parameter list is `Args` applied.
Every closure literal gets a synthesized `extend … : Callable<Args, Ret>` whose `call`
body is the closure body — the same body analysis RFC-0134 §2 / RFC-0153 §1 already run,
emitting an impl instead of setting `Type::Fun` fields. `Callable` is a closed,
compiler-synthesized aspect: users never write `extend T : Callable` by hand, so it
stays out of the coherence / orphan machinery (same profile as `Send` / `Sync`).

### 2. Receiver kind is selected by the axes

`call`'s receiver is not fixed; it is the least-privileged receiver the closure's axis
values permit:

| `call_multiplicity` | `call_mutation` | `call` receiver | Rust analogue |
|---|---|---|---|
| `many` | `reading` | `&self` | `Fn` |
| `many` | `mutating` | `&var self` | `FnMut` |
| `once` | `reading` | `self` (by value) | `FnOnce` |
| `once` | `mutating` | `self` (by value) | `FnOnce` that mutates first |

This is the crux of the object-safety question. Under RFC-0008:

- `&self` and `&var Self` receivers are object-safe. The `many` row is fine.
- A **by-value `self` receiver is not object-safe** under RFC-0008 as written. The
  `once` row therefore needs either (a) an RFC-0008 amendment admitting by-value `self`
  for a sized `dyn` behind a pointer (the receiver is moved out of the `dyn` box, which
  is well-defined when the box owns the value), or (b) `dyn Callable` for a `once`
  closure is boxed-only (`Box<dyn Callable<…>>`) and `call` consumes the box. **Open
  question 1.**

### 3. Marker aspects and widening

Three orthogonal markers record the axis values on the erased type:

- **`CallMany`** — present iff `call_multiplicity` is `many`. Absent ⟹ single-call;
  see §4.
- **`CallShared`** — present iff `call_mutation` is `reading`. Absent ⟹ `call` takes
  `&var self`.
- **`Copy`** — the existing value aspect; present iff every capture is `Copy` (RFC-0134
  §1). Unchanged.

Polarity is fixed so **present = more permissive** uniformly (hence `CallShared`, not
`CallMut`). Widening is then **capability subset**: a slot of type `dyn Callable<A, R> +
M` accepts any value whose marker set `⊇ M`. `dyn Callable<A, R>` with no markers is the
most-restrictive form — single-call, exclusive-access, non-`Copy`. This is exactly
RFC-0152's superset direction, dissolved into an ordinary bound; RFC-0152's bespoke
first-order coercion is not needed for the erased case.

```metel
fun store(f: dyn Callable<(), i64> + CallMany) {
    f();
    f();        // ok — CallMany present
}

fun run_once(f: dyn Callable<(), i64>) {
    f();        // ok
    f();        // error: no CallMany — dyn Callable is single-call
}
```

### 4. Erased call-state

When a `once` (no `CallMany`) closure is erased, the single-call check can no longer be
structural. Two candidate mechanics, **open question 2**:

- **Move-out-of-box.** `dyn Callable` without `CallMany` is only usable as `Box<dyn
  Callable<…>>`; `call` takes `self` (the box), consuming it. A second call is a
  moved-value error on the box binding — the check stays structural, just on the box.
- **Runtime poison flag.** The `dyn` fat pointer carries a "spent" bit; `call` on a
  spent single-call callable panics. Cheap, but turns a static guarantee into a runtime
  one.

The move-out-of-box mechanic is preferred (keeps the guarantee static), at the cost of
`once` erased callables always being heap-allocated.

**The `mutating` axis has the same shape of problem.** A concrete `mutating` closure gets
its exclusive-per-call access from RFC-0153 §3's `&var self` receiver, checked statically
(RFC-0122). Once erased to `dyn Callable` (no `CallShared`) and stored in a shared
structure, that static check is no longer available at the call site. The erased
`mutating` call therefore needs the **dynamic** form RFC-0153 §3 records as its
alternative: a runtime "borrowed" flag on the closure value, set-and-checked per call,
overlap/reentrancy a panic. This RFC adopts that for erased `mutating` callables (it is
the erased-case analogue of the poison flag in §4). **Open question 6.**

### 5. Relationship to the v0.13.0 cluster

- **RFC-0134 / RFC-0153** — the field values on `Type::Fun` decide which markers the
  `dyn` form carries. Both are computed from the same body analysis and kept in
  agreement. Nothing in this RFC changes the flat representation or its checking.
- **RFC-0152** — first-order widening among concrete `Type::Fun` values is unchanged.
  This RFC's subset rule is the erased-case analogue, not a replacement.
- **RFC-0096 (Auto-Impl Aspects)** — `CallMany` / `CallShared` are auto-impl aspects,
  the same closed-set machinery as `Send` / `Sync` / `Linear`. This RFC depends on
  RFC-0096 being built; that dependency is why it is v0.13.1, not v0.13.0.
- **RFC-0061 §7.1 / metel-core#893** — the original `Callable<A, B>` reservation. This
  RFC is its concrete design.
- **RFC-0008 (Aspect Objects)** — object-safety of `Callable::call`; open question 1 may
  require an amendment here.

## Non-Goals

- **Any change to the flat `Type::Fun` model or the v0.13.0 cluster.** This RFC is
  purely additive and strictly later.
- **Higher-order variance for erased callables** — RFC-0155's scope, unchanged.
- **User-written `extend T : Callable`** — `Callable` stays compiler-synthesized.
- **`dyn Callable` at v0.13.0** — explicitly deferred; the cluster ships monomorphic.

## Open Questions

1. **By-value `self` object-safety** (§2) — amend RFC-0008 to admit by-value `self` for
   a pointer-backed `dyn`, or make `once` erased callables `Box`-only?
2. **Erased single-call mechanics** (§4) — move-out-of-box (static, always heap) vs
   runtime poison flag (cheap, dynamic).
3. **`dyn Callable` + multiple non-auto aspects** — does the grammar permit `dyn
   Callable<A, R> + SomeUserAspect`, or only the closed marker set? The auto-impl route
   (§3) sidesteps this but ties the markers to RFC-0096.
4. **Interaction with RFC-0141** (explicit allocator placement for aspect objects) — a
   `Box<dyn Callable>` needs an allocator; does the `once` move-out-of-box mechanic
   compose with RFC-0141's placement syntax?
5. **`Args` row plumbing** — RFC-0151's numeric-label row applied to `call`'s parameter
   list; confirm the erasure preserves arity and per-parameter reference qualifiers.
6. **Erased `mutating`-call exclusivity** (§4) — the runtime "borrowed" flag is the
   proposed mechanic (the static `&var self` check of RFC-0153 §3 is unavailable after
   erasure). Confirm the flag lives in the `dyn` value, its overhead, and its interaction
   with `Send`/`Sync` (an erased `mutating` callable stays `!Sync`).

## References

- **RFC-0134 (Closure Call Capability)** — the flat model and `call_multiplicity`;
  its Open Questions name `Callable` / `dyn Callable` as unbuilt.
- **RFC-0153 (Closure Mutation Axis)** — carried the interim `dyn` erasure default now
  moved here; §3's exclusive-borrow rule the erased `mutating` case must preserve.
- **RFC-0152 (Function-Type Multiplicity Widening)** — the first-order widening this
  RFC's subset rule mirrors for the erased case.
- **RFC-0050 (Closure Capture Lists)** — capture classification feeding the markers.
- **RFC-0008 (Aspect Objects)** — object-safety rules; open question 1.
- **RFC-0096 (Auto-Impl Aspects)** — `CallMany` / `CallShared` as auto-impl aspects;
  the hard dependency setting this RFC's v0.13.1 timing.
- **RFC-0061 §7.1 / metel-core#893** — the original `Callable<A, B>` reservation.
- **RFC-0151 (Numeric-Label Rows)** — `Args`.
- **RFC-0141 (Aspect Objects: Explicit Allocator Placement)** — open question 4.

---

## Decision

**Outcome:** *(pending — `1-under-review`, opened 2026-09-01. Extracted from the v0.13.0
closure cluster during the third adversarial review so that `dyn Callable` is not a
normative forward reference resting on unbuilt machinery. Targets v0.13.1, sequenced
after RFC-0096. Two design open questions (by-value `self` object-safety; erased
single-call mechanics) must close before acceptance.)*
**Target:** v0.13.1 (#923).
