---
id: rfc-0219
title: "The copy Function-Type Qualifier"
date: '2026-11-06'
status: integrated
updated: '2026-11-15'
tracking: 'https://github.com/metel-lang/metel-core/issues/1839'
coverage:
  "1": { kind: blocked, reason: "The copy qualifier is not implemented until metel-core#2049 (grammar) and #2050 (typechecker); the rules are first-class-functions legality-5 to legality-10 and dynamics-1.", ref: "metel-core#2050" }
  "2": { kind: untestable, reason: "The worked examples are fixtures citing the first-class-functions copy rules." }
  "3": { kind: untestable, reason: "The alternatives considered state no rule." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/2048'
impl_status: not-started
---

> **Status — draft (2026-11-06).** A narrow split of RFC-0163, in the style of RFC-0166 (which split RFC-0163's urgent part in September). It re-litigates nothing: the design space is RFC-0163's. It adds one qualifier and nothing else.

> **Status — under review (2026-11-06).** Narrow split of RFC-0163 for v0.16.0

> **Status — accepted (2026-11-15).** Accepted 2026-11-15 by the language owner after a review against the shipped Copy settlement: rule 6 reworded (resolver, not std impls; Discard when it exists), rule 7 (copy var) added, the diagnostics fixed (T0001, P0001), open questions 1 to 3 resolved.

> **Status — integrated (2026-11-15).**

## Summary

A written function type can spell `once` and `var` but not copyability. RFC-0166 settled the bare case: a written `|T| -> U` is **move-only**, and a copyable function value flows into it by moving. This RFC adds the missing spelling:

```metel
fun duplicate_callback(f: copy |i64| -> i64) -> () {
    let g := f;        // a copy of the callback
    let h := f;        // another; f is still usable
}
```

`copy |T| -> U` is a function type whose values are **copyable**: the callable passed in must be one RFC-0134 proved copyable from its captures (a named function, a capture-free closure, a closure whose captures are all `Copy`). The holder may then copy it. It adds **no `Erased` state, no per-node provenance and no coercion table**; those stay in RFC-0163.

---

## Motivation

The Copy and Clone settlement (RFC-0206, RFC-0207, RFC-0089) answered the two questions RFC-0163 was waiting on. Regular values keep an implicit `Copy`, sealed and granted only in the declaration; and the declaration keyword (`copy struct P`) and the function-type qualifier name **one property** (RFC-0206 section 5). With that settled:

- **There is a visible gap.** After v0.16.0 a type author can write `copy struct`, but an API author cannot write a function-typed parameter that the callee may copy. `fun fanout(f: |i64| -> i64)` takes a move-only `f`: it can call `f` repeatedly (a reusable callback needs no copy to be called twice), but it cannot hand independent copies to two helpers or keep one while passing another on, so a fan-out API cannot be typed.
- **The Copy migration already moves function-type `Copy`/`Clone` into std** (#739, #893, #894). A written spelling is the user-facing half of that work.
- **The narrow slice is safe under every remaining design question.** RFC-0166's reasoning applies: a qualifier that only *requires* a property already carried by `Type::Fun.use_multiplicity` (RFC-0134) cannot disagree with how regular values behave.

---

## 1. The rule

1. **Syntax.** `copy` is a function-type qualifier, written in the same prefix position as `once` and `var`, and order-insensitive with them: `copy |T| -> U`, `copy once |T| -> U`, `copy var |T| -> U`. It is **contextual**: it is a qualifier only before a function type and a declaration keyword only before `struct` / `enum`, and it is not a reserved word elsewhere (RFC-0207 section 3). This replaces RFC-0163's global reservation.
2. **Requirement.** A `copy |T| -> U` slot accepts a function value only if RFC-0134 proves it copyable. A move-only value (a closure capturing a non-`Copy` value, or an exclusive reference `[&var x]`, which is not `Copy`) is rejected at the argument as a type mismatch (`T0001`) whose message names the capture that prevents copying, in the words of the existing explanation ("owns a capture that is not `Copy`").
3. **Permission.** A value of type `copy |T| -> U` may be copied. A bare `|T| -> U` value may not (RFC-0166).
4. **Directions.** A copyable value flows into a bare slot by moving (RFC-0166, RFC-0152's first-order direction). A `copy |T| -> U` value flows into a bare `|T| -> U` slot by moving. The reverse is rejected: a bare (move-only) value is not accepted where `copy` is required. Below the first function level the qualifier matches exactly, as `once` and `var` already do (RFC-0152).
5. **Closure literals.** `copy` is rejected in the prefix of a closure literal (`[x] copy |y| .{ ... }`): a literal's copyability is derived from its captures, not asserted. The diagnostic says so, and it is a parse error (`P0001`) with that message.
6. **Aspects.** `copy |T| -> U` satisfies `Copy` and the provided `Clone` through the aspect resolver, the same answer move checking gets (RFC-0071 section 2, metel-core#739): one property, two spellings (RFC-0206). It is `Discard` once RFC-0089's check exists: until then every type is `Discard` and nothing is checked. A closure that captures a linear value must be declared `linear` (RFC-0194, reserved here).
7. **Mutating callables.** `copy var |T| -> U` is a copyable function whose call mutates its own captured state (`var`, RFC-0153). Each copy owns an independent copy of that state, so copies diverge as they are called. This is the same representation copy as any other (rule 2 guarantees every capture is `Copy`), and it is why a `[&var x]` capture, which aliases state it does not own, cannot be `copy`.

**Dynamic semantics.** Copying a `copy |T| -> U` value duplicates its environment. Every capture is `Copy` (rule 2), so this is a representation copy that runs no user code (RFC-0206 section 2).

---

## 2. Worked examples

```metel
fun fanout(f: copy |i64| -> i64) -> i64 {
    let g := f;                  // independent copies of the callback
    let h := f;
    g(1) + h(2)
}

let k := 3;
fanout([k] |x: i64| -> i64 { x + k });          // ok: the capture is Copy
let name := "x";
fanout([name] |x: i64| -> i64 { x + name.len() });   // error: capturing `name` (String, not Copy) prevents `copy`

fun double(x: i64) -> i64 { x * 2 }
fun at_most_once(f: copy once |i64| -> i64) -> i64 { f(1) }   // accepts a copyable (hence reusable) callable; this slot calls it at most once
fun once_only(f: |i64| -> i64) -> i64 { f(1) }    // bare: f may be called once, as a move
once_only(double);               // ok: a copyable value flows in by moving
```

Combining it with the integrated closure rules:

```metel
// RFC-0153 `var` with `copy` (rule 7): each copy owns its own counter.
fun two_counters(make: copy var || -> i64) -> i64 {
    var a := make;                 // a copy of the callable, with its own state
    var b := make;                 // another, independent
    a() + a() + b()                // 0 + 1 + 0 when `make` counts from zero
}
var n := 0;
two_counters([n] var || -> i64 { let r := n; n += 1; r });       // ok: the capture `n` is Copy

// RFC-0134: capture-derived copyability decides, not the slot.
var shared := 1;
fanout([&var shared] |x: i64| -> i64 { x });  // error (T0001): `[&var shared]` is not Copy, so it prevents `copy`

// RFC-0166 directions: copy flows into bare by moving, bare does not flow into copy.
fun keep(f: |i64| -> i64) -> i64 { f(1) }
fun relay(f: copy |i64| -> i64) -> i64 { keep(f) + f(2) }   // ok: `f` is copyable, so `keep(f)` takes a copy and `f` stays usable
fun accept_copy(f: |i64| -> i64) -> i64 { fanout(f) }        // error (T0001): a bare (move-only) value is not accepted where `copy` is required
```

Below the first function level the qualifier matches exactly (rule 4, RFC-0152): a parameter of type `|copy |i64| -> i64| -> i64` accepts only a function whose own parameter is written `copy |i64| -> i64`, not a bare one.

---

## 3. Alternatives considered

1. **Leave it to RFC-0163** (rescheduled to "Views and projections"). No work now, and the gap above stays through v0.16.0.
2. **Bring in RFC-0163 whole** (the `Erased` third state, provenance, the coercion table). The settlement removed its blocker, but its machinery was designed before the sealed `Copy`, `Discard` and the lattice, and needs a full re-review against them.
3. **A bound instead of a qualifier** (`F: Copy`). Possible once function types satisfy `Copy` (rule 6), but a generic callback parameter does not replace a written type, and RFC-0163's review found the shape unavailable before the migration lands.
4. **Reserve `copy` globally**, as RFC-0163 proposed. Rejected: RFC-0207 makes the class keywords contextual and the grammar does not reserve `copy` today.

## Relationship to existing RFCs

`copy once |T| -> U` is a requirement on the supplied callable (copyable, so reusable) combined with a `once` interface for the holder: a reusable callable is accepted into a `once` slot, and the holder of the slot may call it at most once per copy.

- **RFC-0163** — amended: the `copy` qualifier is split out here; the `Erased` state, provenance model, coercion table and join rule stay there.
- **RFC-0166** — the bare case; this RFC adds the qualifier it explicitly left out.
- **RFC-0134, RFC-0152, RFC-0153** — capture-derived copyability, the use-axis directions, and `once` / `var`.
- **RFC-0206, RFC-0207, RFC-0089** — the one property, the contextual keyword, and `Discard`.

## Open questions

1. **The diagnostic: resolved 2026-11-15.** A capture that prevents `copy` is a type mismatch (`T0001`) naming the capture; `copy` in a closure-literal prefix is a parse error (`P0001`).
2. **Generic callbacks: out of scope, kept so.** A generic parameter `F` stays outside this RFC; whether it can be bounded so that a `copy |T| -> U` is accepted is RFC-0163's section "Generic callbacks".
3. **Display of `copy` in inferred function types: resolved 2026-11-15.** It prints as `copy |T| -> U`, written like `once` and `var`.
4. **The must-call spelling: resolved 2026-11-06.** RFC-0194's must-call form is `linear`, a modifier in the same prefix
   position as `copy`, `once` and `var` (`linear || -> ()`). `copy` and `linear` are mutually exclusive (a copyable callable
   cannot be linear), and `linear` implies `once`. The family reads as: `copy |T| -> U` (may be copied), bare `|T| -> U`
   (move-only, may be dropped), `once |T| -> U` (at most once, may be dropped), `linear |T| -> U` (exactly once, cannot be
   dropped). RFC-0219 specifies only `copy`; `linear` is RFC-0194's and RFC-0089's.

---

## Decision

**Outcome:** *(pending)*
