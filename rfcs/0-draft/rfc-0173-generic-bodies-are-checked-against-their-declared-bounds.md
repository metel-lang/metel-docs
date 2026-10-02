---
id: rfc-0173
title: "Generic bodies are checked against their declared bounds"
date: '2026-10-02'
status: draft
---

## Summary

A declared generic parameter is **opaque inside its own body**: it unifies only with itself and supports only what its declared bounds entail. Today a generic body is also re-checked at every call with the concrete argument types substituted, which lets a definition that over-constrains its parameters, or uses something its bounds never granted, be accepted and fail later at a call site, inside the body, or not at all. This RFC makes the definition-time check the contract (metel-core#1320, #1323) and records that the per-call re-check is an implementation device, not language semantics.

---

## Motivation

### The language already half-says this

RFC-0040 §3 states that inside a body a bounded parameter has *the declared aspect's methods available*, and that calling a method the bounds do not grant is an error. That is a bounds-only rule, and the checker already enforces it for methods and for field access:

```metel
aspect Show { fun show(self) -> i64; }
extend i64: Show { fun show(self) -> i64 { 1 } }
fun f<T>(x: T) -> i64 { x.show() }     // rejected: T has no Show bound
```

```metel
struct P { public x: i64 }
fun gx<T>(a: T) -> i64 { a.x }         // rejected: T has no fields
```

Both are rejected on `develop` (with `T0002`, "cannot infer receiver/struct type", rather than the `T0013` RFC-0040 names; see Open Question 5).

But the same body is accepted when it constrains the parameter by *unification* or uses an *operator*:

```metel
fun pick<T>(a: T) -> i64 { a }          // accepted: T := i64
fun id2<T, U>(a: T) -> U { a }          // accepted: T and U collapse into one variable
fun add<T>(a: T, b: T) -> T { a + b }   // accepted: no Add-like bound exists
```

Each such function silently stops being generic. The error appears, if at all, at a call (`pick("hello")` fails with `cannot unify String with i64`), at the wrong place.

### What it breaks

- **Row polymorphism (RFC-0121).** `Rest` is only meaningful as a variable *distinct from* `R`. `fun authenticate<row R, row Rest>(s: Session<..R>) -> Session<..Rest> where R = { token: String, ..Rest } { .. }` is accepted even when the body returns the wrong row, because `Rest` and `R` collapse. The `Rest` derivation of metel-core#1310 leaves a collapsed `Rest` alone (metel-core#1320).
- **Conditional impls (RFC-0036, RFC-0121 §3).** `extend<T: Tag> Box<T> { fun f(self) }` should make `f` visible only where `T: Tag` is entailed. Inside `fun g<U>(b: Box<U>) { b.f() }` it is visible anyway, and the condition is checked per call, with the error reported inside `g` (metel-core#1323).
- **Error locality.** A wrong definition is reported at its callers.

### Why the lax behaviour exists

Generic bodies are re-constructed at every call with concrete types substituted (ADR-0010, `LIMIT-EVALUATION-001`). That is template-style checking layered on an inference pass. It is also how the interpreter gets away without a monomorphization phase (metel-core#288). The spec states neither rule, so users cannot tell which they are getting. This RFC states one.

---

## Proposal (primary)

### D1: Declared parameters are rigid in their own definition

Inside a generic function or method, each declared type parameter (including `row` parameters and the parameters of the enclosing `extend`) is an opaque type. It unifies only with itself. Unifying it with a concrete type, or with another declared parameter, is a type error **at the definition**, reported against the offending expression.

```metel
fun pick<T>(a: T) -> i64 { a }   // error: expected i64, found T
fun id2<T, U>(a: T) -> U { a }   // error: expected U, found T
```

### D2: A body may use only what its bounds entail

A body may call a method, use an operator, or rely on a conditional impl only if the parameter's declared bounds (inline, `where`, and the enclosing impl's) entail it. This is RFC-0040 §3 extended from methods to every use, and it makes RFC-0036's conditional-impl visibility rule true: `b.f()` over `Box<U>` needs `U: Tag`.

### D3: No special case for a parameter in call position

A bare parameter `F` is not callable. `fun apply<F, T>(f: F, x: T) -> T { f(x) }` is a definition error; the spelling is `f: |T| -> T`, which already works. A `Callable` bound (RFC-0161) would make the bare form legal later without changing this rule. The only fixture that depends on the bare form is `stage10_neg_06`, a negative test; a scan of core, docs and website sources found no other code that does (RFC text excepted).

### D4: The per-call re-check is not semantics

A well-formed generic definition (D1-D3) is accepted or rejected independently of any call. Re-checking a body with concrete types may remain as an implementation device (until #288), but it must never accept something D1-D3 reject, and it must not be the source of the first error. Any future monomorphization phase instantiates a body already checked; it does not re-check it.

### D5: Operators on a parameter need a bound

`a + b` over `T` requires a bound that grants `+`. Whether the language has such aspects is not settled here (Open Question 2), so until it does, D2 would reject the `add<T>` above and give users no spelling for it.

---

## Measurement (prototype, discarded)

A throwaway prototype of D1 for free functions (each declared parameter must resolve to a distinct, unbound variable after the body is solved) catches `pick`, `id2`, and the row `R`/`Rest` collapse. With it on, 7 of 1463 tests fail:

| Failures | Pattern | Verdict |
|---|---|---|
| 4 (`move_check` 34, 35 and two unit tests) | `fun f<T: GenericSink, U>(value: T, other: U) { value.sink(other) }`: the call unifies the caller's `U` with the aspect method's own `U` | false positive; an artifact of how aspect-method generics are instantiated. Fix first. |
| 1 (`stage10_neg_06`) | `apply_twice<F, T>` calls `f(x)` | covered by D3; becomes a definition error |
| 1 (enum-variant identity fixture) | `fun radius<T>(v: T) { match v { Shape::Circle { r } => r, .. } }` | relies on template checking; needs a bound or a concrete type |
| 1 (`stage10_neg_02`) | `fun always_int<T>(_x: T) -> T { 42 }` | the old behaviour enshrined as a test; the error moves from the call to the definition |

Not measured: impl methods, closures, nested generic functions, operators (D5). The measurement must be extended to those before this RFC leaves draft.

---

## Alternatives

- **B. Template-checked, documented.** State in the spec that a generic body is checked per instantiation, as in C++. Cheapest; leaves #1320 and #1323 as designed behaviour and gives up definition-site errors and the row guarantees above. It also contradicts RFC-0040 §3, which already treats bounds as the contract inside the body.
- **C. Opt-in.** Keep today's behaviour and add a rigid mode (an attribute or a keyword). Two semantics for one construct, and the default stays the unsafe one.
- **Rigid only for `row` parameters.** Fixes the RFC-0121 case but leaves the rest inconsistent, and the same collapse is possible with ordinary parameters.

---

## Open Questions

1. **The `radius<T>` pattern.** Is matching a generic value against a concrete enum something the language wants to support (it would need a bound or an explicit coercion), or is it an accident of template checking?
2. **Operators.** What grants `+`, `==`, `<` on a parameter: built-in marker aspects, the equality model of RFC-0168, or something else? D5 cannot ship before there is an answer.
3. **Closures and nested generics.** Does a closure inside a generic body see the enclosing parameters as rigid? Expected yes; unmeasured.
4. **Associated-type projections.** `T::Assoc` inside a body must stay a projection of the opaque `T`; check the interaction with the opaque `impl Aspect` returns of RFC-0037.
5. **Error codes.** RFC-0040 §3 names `T0013` for a missing bound, which is now "ambiguous resolution"; the checker currently reports `T0002`. D2 should state one code for "not granted by the declared bounds".
6. **Migration.** Whether any programs outside this repository use an unbounded `F` in call position or rely on collapsing; and whether a warning period is wanted.

---

## Implementation Notes (an ADR accompanies, once the RFC is accepted)

1. Fix the aspect-method instantiation artifact first, so a call does not merge the caller's parameter with the method's.
2. Then enforce D1 for free functions, then impl methods and closures, behind the measured fixtures.
3. Fixtures to change: `stage10_neg_06`, `stage10_neg_02`, the enum-variant fixture.
4. Depends on: RFC-0040, RFC-0036, RFC-0121 §3; related: RFC-0138, RFC-0161, RFC-0168. Unblocks metel-core#1320 and #1323. No dependency on #288, but the monomorphization design must honour D4.

---

## Decision

**Outcome:** *(pending)*
