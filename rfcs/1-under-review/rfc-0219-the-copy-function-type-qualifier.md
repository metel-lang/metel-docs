---
id: rfc-0219
title: "The copy Function-Type Qualifier"
date: '2026-11-06'
status: under-review
updated: '2026-11-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1839'
---

> **Status — draft (2026-11-06).** A narrow split of RFC-0163, in the style of RFC-0166 (which split RFC-0163's urgent part in September). It re-litigates nothing: the design space is RFC-0163's. It adds one qualifier and nothing else.

> **Status — under review (2026-11-06).** Narrow split of RFC-0163 for v0.16.0

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

- **There is a visible gap.** After v0.16.0 a type author can write `copy struct`, but an API author cannot write a function-typed parameter that the callee may copy. `fun apply_twice(f: |i64| -> i64)` takes a move-only `f`, so it can call it once as a move, and a "retry" or "fan-out" API cannot be typed.
- **The Copy migration already moves function-type `Copy`/`Clone` into std** (#739, #893, #894). A written spelling is the user-facing half of that work.
- **The narrow slice is safe under every remaining design question.** RFC-0166's reasoning applies: a qualifier that only *requires* a property already carried by `Type::Fun.use_multiplicity` (RFC-0134) cannot disagree with how regular values behave.

---

## 1. The rule

1. **Syntax.** `copy` is a function-type qualifier, written in the same prefix position as `once` and `var`, and order-insensitive with them: `copy |T| -> U`, `copy once |T| -> U`, `copy var |T| -> U`. It is **contextual**: it is a qualifier only before a function type and a declaration keyword only before `struct` / `enum`, and it is not a reserved word elsewhere (RFC-0207 section 3). This replaces RFC-0163's global reservation.
2. **Requirement.** A `copy |T| -> U` slot accepts a function value only if RFC-0134 proves it copyable. A move-only value (a closure capturing a non-`Copy` value) is rejected at the argument, with a diagnostic that names the capture that prevents copying.
3. **Permission.** A value of type `copy |T| -> U` may be copied. A bare `|T| -> U` value may not (RFC-0166).
4. **Directions.** A copyable value flows into a bare slot by moving (RFC-0166, RFC-0152's first-order direction). A `copy |T| -> U` value flows into a bare `|T| -> U` slot by moving. The reverse is rejected: a bare (move-only) value is not accepted where `copy` is required. Below the first function level the qualifier matches exactly, as `once` and `var` already do (RFC-0152).
5. **Closure literals.** `copy` is rejected in the prefix of a closure literal (`[x] copy |y| { ... }`): a literal's copyability is derived from its captures, not asserted. The diagnostic says so (code assigned at `4-implemented`).
6. **Aspects.** `copy |T| -> U` satisfies `Copy`, the provided `Clone` and `Discard` through the function-type impls of the Copy migration (#739, #893, #894): one property, two spellings (RFC-0206). Whether a bare function value is `Discard` is the open closure-discard question of RFC-0089 section 2.2, unchanged here.

**Dynamic semantics.** Copying a `copy |T| -> U` value duplicates its environment. Every capture is `Copy` (rule 2), so this is a representation copy that runs no user code (RFC-0206 section 2).

---

## 2. Worked examples

```metel
fun retry(f: copy || -> boolean) -> boolean {
    if (f()) { return true; }
    f()                          // f was copied at the first call site: it is usable again
}

let flag := true;
retry([flag] || { flag });       // ok: the capture is Copy
let name := "x";
retry([name] || { name.len() > 0 });   // error: capturing `name` (String, not Copy) prevents `copy`

fun double(x: i64) -> i64 { x * 2 }
fun once_only(f: |i64| -> i64) -> i64 { f(1) }    // bare: f may be called once, as a move
once_only(double);               // ok: a copyable value flows in by moving
```

---

## 3. Alternatives considered

1. **Leave it to RFC-0163** (rescheduled to "Views and projections"). No work now, and the gap above stays through v0.16.0.
2. **Bring in RFC-0163 whole** (the `Erased` third state, provenance, the coercion table). The settlement removed its blocker, but its machinery was designed before the sealed `Copy`, `Discard` and the lattice, and needs a full re-review against them.
3. **A bound instead of a qualifier** (`F: Copy`). Possible once function types satisfy `Copy` (rule 6), but a generic callback parameter does not replace a written type, and RFC-0163's review found the shape unavailable before the migration lands.
4. **Reserve `copy` globally**, as RFC-0163 proposed. Rejected: RFC-0207 makes the class keywords contextual and the grammar does not reserve `copy` today.

## Relationship to existing RFCs

- **RFC-0163** — amended: the `copy` qualifier is split out here; the `Erased` state, provenance model, coercion table and join rule stay there.
- **RFC-0166** — the bare case; this RFC adds the qualifier it explicitly left out.
- **RFC-0134, RFC-0152, RFC-0153** — capture-derived copyability, the use-axis directions, and `once` / `var`.
- **RFC-0206, RFC-0207, RFC-0089** — the one property, the contextual keyword, and `Discard`.

## Open questions

1. **The diagnostic text and code** for a capture that prevents `copy` (assigned at `4-implemented`).
2. **Generic callbacks.** Whether a generic parameter `F` can be bounded so that a `copy |T| -> U` is accepted (RFC-0163 section "Generic callbacks"); out of scope here.
3. **Display of `copy` in inferred function types** for tooling (hover, errors).
4. **The must-call spelling: resolved 2026-11-06.** RFC-0194's must-call form is `linear`, a modifier in the same prefix
   position as `copy`, `once` and `var` (`linear || -> ()`). `copy` and `linear` are mutually exclusive (a copyable callable
   cannot be linear), and `linear` implies `once`. The family reads as: `copy |T| -> U` (may be copied), bare `|T| -> U`
   (move-only, may be dropped), `once |T| -> U` (at most once, may be dropped), `linear |T| -> U` (exactly once, cannot be
   dropped). RFC-0219 specifies only `copy`; `linear` is RFC-0194's and RFC-0089's.

---

## Decision

**Outcome:** *(pending)*
