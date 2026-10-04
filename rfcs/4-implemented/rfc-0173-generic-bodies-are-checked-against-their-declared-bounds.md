---
id: rfc-0173
title: "Generic bodies are checked against their declared bounds"
date: '2026-10-02'
status: implemented
updated: '2026-10-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/1334'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1364'
impl_status: implemented
---

> **Status — integrated (2026-10-03).** Spec integrated: spec.types.generics.rigid-type-parameters; limits LIMIT-TYPES-004, GAP-TYPES-005; implementation tracked in #1364

> **Status — implemented (2026-10-04).**

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

Both are rejected on `develop` (with `T0002`, "cannot infer receiver/struct type", rather than the `T0013` RFC-0040 names; see Error codes below).

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

Inside a generic function or method, each declared type parameter (including `row` parameters and the parameters of the enclosing `extend`) is an opaque type. It unifies only with itself, **or with a type that the definition's declared bounds Γ state is equal to it**. Unifying it with a concrete type, or with another declared parameter, in any other way is a type error **at the definition**, reported against the offending expression.

```metel
fun pick<T>(a: T) -> i64 { a }   // error: expected i64, found T
fun id2<T, U>(a: T) -> U { a }   // error: expected U, found T
```

Γ states equalities in exactly two places, and the set is closed (a future `where T = U` would need its own RFC):

1. **Row equations.** `where R = { token: String, ..Rest }` says `R` has `token: String`, that `Rest` is *derived*, namely `R` without `token`, and that `Rest` lacks `token`. `Rest` is not an independent parameter; the caller does not choose it, and it is computed at each call. So the body may treat `R` and `{ token: String, ..Rest }` as equal, and `R` can never equal `Rest`: unifying them is an occurs-check failure, which is how returning the wrong row is rejected at the definition.
2. **Associated-type bindings.** `T: Iterable<Item = X>` makes `T::Item` equal to `X`.

A closure or nested generic function inside a generic body sees the enclosing parameters as rigid. A recursive or mutually recursive generic call instantiates the callee's parameters afresh, so it checks against the callee's declared bounds like any other call.

Equalities are symmetric but applied on demand: the checker rewrites `R` to its decomposition only when unification needs it, and diagnostics keep printing `R`. They propagate through generic arguments in the usual argument-wise way, so `Session<..R>` equals `Session<..{ token: String, ..Rest }>`.

### D2: A body may use only what its bounds entail

A body may call a method, use an operator, or rely on a conditional impl only if the parameter's declared bounds (inline, `where`, and the enclosing impl's) entail it. This is RFC-0040 §3 extended from methods to every use, and it makes RFC-0036's conditional-impl visibility rule true: `b.f()` over `Box<U>` needs `U: Tag`.

Matching a value of a bare parameter against a concrete enum or struct pattern is a type mismatch (`T0001`): the parameter is opaque. The spelling is a bound, or a concrete type in the signature. The `radius<T>` fixture below is an accident of template checking and is rejected.

### D3: No special case for a parameter in call position

A bare parameter `F` is not callable. `fun apply<F, T>(f: F, x: T) -> T { f(x) }` is a definition error; the spelling is `f: |T| -> T`, which already works. A `Callable` bound (RFC-0161) would make the bare form legal later without changing this rule. The only fixture that depends on the bare form is `stage10_neg_06`, a negative test; a scan of core, docs and website sources found no other code that does (RFC text excepted).

### D4: The per-call re-check is not semantics

A well-formed generic definition (D1-D3) is accepted or rejected independently of any call. The per-call reconstruction is recorded as `LIMIT-EVALUATION-001`, with its removal owned by metel-core#1352. Re-checking a body with concrete types may remain as an implementation device (until #288), but it must never accept something D1-D3 reject, and it must not be the source of the first error.

The other direction is also fixed. If the re-check rejects a body that the definition check accepted, the two checks disagree, and the definition check is wrong. That is an **internal error** with its own `I`-code (not an existing one: its cause differs from `I0009`), following RFC-0167's rule that a state reachable only through a checker bug is an internal error. Its message names the definition and says the checks disagree; it never blames the call site.

The rule applies **per construct, from the point that construct's definition check is enforced** (free functions, then impl methods, closures, nested generics, as the measurement extends). Until a construct is enforced, the re-check may still reject what the definition check lets through, and that rejection stays an ordinary diagnostic.

How agreement between the two checks is verified is an implementation matter, specified in the accompanying ADR.

The I-code and the re-check both go away when run-time generic reconstruction is removed (metel-core#1352, v0.17.0, with frontend monomorphization #288). Any monomorphization phase instantiates a body already checked; it does not re-check it.

### D5: Operators on a parameter are rejected until operator aspects exist

`a + b` over a bare `T` is rejected at the definition, like any other use the bounds do not grant. The language has no aspects that grant arithmetic or ordering operators yet, so for now there is no spelling for a generic `add<T>`. That is a **temporary, recorded limit**, not a design position: it lasts until operator desugaring to aspects is specified and implemented (Open Question 2), at which point `T: Add` grants `+` by D2 with no change to this RFC. Implementation adds a limit entry that names the operator-desugaring work as its owner. Equality is not affected: `Eq` already grants `==` through its `eq` method.

### D6: Entailment

D2 and D5 rest on one judgment: given the declared bounds Γ of a definition, is a use of a rigid parameter `T` entailed? Γ is the parameter's bounds from inline `T: A`, `where` clauses, and the enclosing `extend`'s bounds. Entailment is **membership in Γ, forwarded by the uses below, with no search and no inference**:

1. **Method call.** `x.m()` is entailed iff some `A ∈ Γ(T)` declares `m`.
2. **Forwarding to a callee's bound.** Passing `x` where a callee requires `U: A` is entailed iff `A ∈ Γ(T)`.
3. **Conditional-impl visibility.** A method of `extend<T: Tag> Box<T>` is visible on `Box<U>` iff `Tag ∈ Γ(U)` (metel-core#1323).
4. **Row field access.** `x.label` on a row-bounded parameter is entailed iff some row bound in Γ names `label`; its type is the type that bound declares, not a fresh variable.
5. **`where all R: A`** grants `A` for the fields of `R`, not for `R` itself. It is forwarded only to another `where all R: A` bound.
6. **Associated types.** `T::Assoc` is an opaque projection of `T`, equal only to itself or to what an associated-type equality in Γ declares (RFC-0082 §4), and supports only the bounds the aspect declares on it.
7. **Impl resolution assumes Γ.** An impl applies to a type built from `T` (for example `extend<U: Clone> List<U>: Clone` on `List<T>`) iff its own conditions are entailed by Γ. This is what keeps D2 consistent with RFC-0036.

There is no transitive closure: aspects have no supertrait syntax, so `T: A` grants `A` and nothing else. If supertraits are added, they extend this rule. A `where` equality in Γ is also an entailment fact; its handling is stated under D1.

### Error codes

- **Rigid-parameter mismatch** (D1): `T0001`, with a note that the type is a declared parameter and opaque in its definition. A rigid parameter is an opaque type, so this is an ordinary mismatch.
- **Use not granted by the declared bounds** (D2, D6 cases 1, 3 and 4: a method call, a conditional-impl method, or a field access): a new `T0035`. The message names the parameter and the bound that would grant the use. This replaces today's `T0002`, which is misleading here. RFC-0040 §3's citation of `T0013` for a missing bound is superseded; `T0013` stays "ambiguous resolution".
- **Forwarding to a callee's bound** (D6 case 2): the existing `T0012` (aspect bound not satisfied), the same code the call gets with a concrete type.
- **Operator on a bare parameter** (D5, while operator aspects do not exist): the existing `T0005`. When operator aspects exist, the same use is `T0035` or `T0012` as appropriate, and the limit entry says so.
- **Definition and re-check disagree** (D4): a new `I0010`, "Generic definition and construction disagree". It is not `I0009`, whose cause is a missing type context.

The `error-codes.md` entries are added when the checks are implemented, so no documented code lacks a raise site.

---

## Measurement (prototype, discarded)

A throwaway prototype of D1 for free functions (each declared parameter must resolve to a distinct, unbound variable after the body is solved) catches `pick`, `id2`, and the row `R`/`Rest` collapse. With it on, 7 of 1463 tests fail:

| Failures | Pattern | Verdict |
|---|---|---|
| 4 (`move_check` 34, 35 and two unit tests) | `fun f<T: GenericSink, U>(value: T, other: U) { value.sink(other) }`: the call unifies the caller's `U` with the aspect method's own `U` | false positive; an artifact of how aspect-method generics are instantiated. Fix first. |
| 1 (`stage10_neg_06`) | `apply_twice<F, T>` calls `f(x)` | covered by D3; becomes a definition error |
| 1 (enum-variant identity fixture) | `fun radius<T>(v: T) { match v { Shape::Circle { r } => r, .. } }` | relies on template checking; needs a bound or a concrete type |
| 1 (`stage10_neg_02`) | `fun always_int<T>(_x: T) -> T { 42 }` | the old behaviour enshrined as a test; the error moves from the call to the definition |

Not measured: impl methods, closures, nested generic functions, operators (D5). Enforcement of each construct is gated on extending the measurement to it (D4); acceptance of this RFC does not wait for that.

### Migration

No warning period. The language is pre-1.0 with no known external users, and the only in-repo programs affected are the three fixtures listed under Implementation Notes.

---

## Worked examples (integration review)

Each combines this RFC with an already-integrated feature, looking for a soundness gap at the intersection. The outcomes are what the rules above require; none is implemented yet (metel-core#1364).

**1. With RFC-0121 row equations and RFC-0123 `where all`.**

```metel
fun authenticate<row R, row Rest>(s: Session<..R>) -> Session<..Rest>
where R = { token: String, ..Rest } { s.drop_token() }   // body returns Session<..R>
```

`Rest` lacks `token` and `R` has it, so `Session<..R>` is not `Session<..Rest>`: rejected at the definition (`T0001`). Today this is accepted because `Rest` collapses into `R`.

**2. With RFC-0137 by-value narrowing.**

```metel
fun first<row R>(r: { x: i64, ..R }) -> { x: i64 } { r }   // forgets the fields of R
```

Narrowing by value forgets `R`'s fields, so it needs `where all R: Copy`; without it the body is rejected at the definition (`T0033`). This closes the definition-time half of `LIMIT-TYPES-002` that waited on this RFC. With `where all R: Copy` it is accepted, and `all R: Copy` is not granted to `R` itself (D6 case 5).

**3. With RFC-0036 conditional impls and the aspect-method instantiation artifact.**

```metel
fun f<T: GenericSink, U>(value: T, other: U) { value.sink(other) }
```

`sink<U>` has its own generic parameter. The call instantiates it afresh and does not unify it with the caller's `U`, so `f` stays generic in `U`. This is the artifact the prototype measurement found, and it is a precondition of enforcing D1, not a consequence of it.

**Gap found.** None in the rules. One implementation precondition (example 3) and one new piece of checker work (a typed row decomposition inside the body, example 1) are recorded under Implementation Notes.

---

## Alternatives

- **B. Template-checked, documented.** State in the spec that a generic body is checked per instantiation, as in C++. Cheapest; leaves #1320 and #1323 as designed behaviour and gives up definition-site errors and the row guarantees above. It also contradicts RFC-0040 §3, which already treats bounds as the contract inside the body.
- **C. Opt-in.** Keep today's behaviour and add a rigid mode (an attribute or a keyword). Two semantics for one construct, and the default stays the unsafe one.
- **Rigid only for `row` parameters.** Fixes the RFC-0121 case but leaves the rest inconsistent, and the same collapse is possible with ordinary parameters.

---

## Open Questions

1. **Operators.** What grants `+`, `<` on a parameter: operator desugaring to aspects, the equality model of RFC-0168, or something else? D5 records the interim limit; this question is owned by the operator-desugaring work, not this RFC.
2. **Associated-type projections and opaque returns.** D6 case 6 states the rule for `T::Assoc`. How it interacts with the opaque `impl Aspect` returns of RFC-0037 is not settled; it does not block acceptance.

---

## Implementation Notes (an ADR accompanies, once the RFC is accepted)

1. Fix the aspect-method instantiation artifact first, so a call does not merge the caller's parameter with the method's. Row equations are derived at the call today (metel-core#1313, #1321); D1 needs the checker to hold the decomposition as a typed fact inside the body, which is new work and probably the hardest part for row parameters.
2. Then enforce D1 for free functions, then impl methods and closures, behind the measured fixtures.
3. Fixtures to change: `stage10_neg_06`, `stage10_neg_02`, the enum-variant fixture (`radius<T>`, now a rejection). Fixtures to add: a closure inside a generic body sees the enclosing parameters as rigid; a generic function that calls itself, and one that calls another generic function, still checks.
4. Depends on: RFC-0040, RFC-0036, RFC-0121 §3; related: RFC-0138, RFC-0161, RFC-0168. Unblocks metel-core#1320 and #1323. No dependency on #288, but the monomorphization design must honour D4.

---

## Decision

**Outcome:** *(pending)*
