---
id: rfc-0232
title: "Function Types as Regular Types"
date: '2026-11-16'
status: draft
---

> **Design draft.** Nothing here is accepted. It reframes RFC-0161 and RFC-0219 and absorbs the idea of metel-core#702 for
> function types. It changes no behaviour by itself: the first step it asks for is RFC-0161 Phase A.

## Summary

A written function type is not a type former of its own. `|A, B| -> R` is the erased callable type
`dyn Callable<.{ .0: A, .1: B }, R>` together with marker aspects that say what the callable may do, and the qualifiers
`once`, `var` and `copy` are the markers:

```metel
|i64| -> i64                  // dyn Callable<.{ .0: i64 }, i64> + CallMany + CallShared      (as today: many, reading, move-only)
once |i64| -> i64             // dyn Callable<.{ .0: i64 }, i64>
var |i64| -> i64              // dyn Callable<.{ .0: i64 }, i64> + CallMany
copy |i64| -> i64             // dyn Callable<.{ .0: i64 }, i64> + CallMany + CallShared + Copy
```

The parameters are one record, the row of the call's argument labels, so a function of any arity is one generic impl
over a row-kinded `Args`. The return is the second type argument. A closure literal has its own anonymous environment
type, which implements `Callable` and earns its markers from its body, and gets `Copy`, `Clone`, `Send` and `Sync` from its
captures the way a declared type gets them from its fields. The erased written type is where a closure, a named function
or any other callable is stored when its type is not wanted.

Today `Type::Fun` carries the same facts in three enum fields (`call_multiplicity`, `use_multiplicity`, `call_mutation`).
This RFC says they are aspects, and that the one place that is not an aspect (the structural `Copy` of a function type) is
the `Copy` aspect.

---

## Motivation

Measured on `develop`, 2026-11-16.

1. **Function types are the one structural kind whose capabilities are not aspects.** `Type::Fun` has three axes and
   `InferType::Fun` the same; metel-core#702 counts 68 and 47 match sites. `Copy` of a function type is the `copy`
   qualifier (RFC-0219), answered by a special arm of the resolver (`infer_type_satisfies_aspect`); `Clone` is the provided
   one of a `Copy` type; `Send` and `Sync` do not exist for it (RFC-0080). A user cannot write `F: Copy` and mean the same
   as `copy |T| -> U`, and cannot write an impl over "every function type".
2. **Widening is a bespoke `unify` rule.** A copyable function is accepted where a move-only one is expected, a many one
   where a once one is, a reading one where a mutating one is (RFC-0152, RFC-0166), at the first function level only.
   `unify` cannot tell which side is expected, so it accepts both directions and the real check is repeated at call
   arguments and at `maybe_dyn_coerce` (metel-core#2049, #2050). The same widening is, for a `dyn` bound, dropping a marker.
3. **Any-arity impls are not expressible.** metel-core#894 (move the function-type aspects into std) and #893 (`Callable`
   for function types) both stall on "a function type of any arity" in an impl target: per-arity impls, variadic packs
   (RFC-0125) or a dedicated `fun(..)` form. With `Args` a row, the answer is an ordinary row-generic impl, the way
   `extend<record R> .{ ..R }: Copy` already covers every tuple.
4. **The abstract ownership analysis reinvents the environment.** `AbstractType::Closure { signature, owned_captures }`
   and the contract machinery (`merge_contracts`, `bind_template`, `retain_aggregate_closures`, metel-core#2000 to #2014)
   are a hand-built record of a closure's captures. If the closure had a type whose fields were its captures, that is an
   ordinary type fact and a record.
5. **The pieces are already designed.** RFC-0161 gives `Callable<Args, Ret>`, the markers `CallMany` and `CallShared`,
   widening by marker subset, and the model "a closure literal has a compiler-generated environment aggregate that
   implements `Callable`". RFC-0151 made a tuple the row of integer labels. RFC-0219 spelled `copy`. This RFC states what
   they add up to.

---

## 1. The meaning of a written function type

**Rule 1.** `|P₀, …, Pₙ| -> R` with qualifiers `Q` is `dyn Callable<.{ .0: P₀, …, .n: Pₙ }, R> + markers(Q)`, with
`markers` given by the table:

| Written | Markers on the `dyn` |
|---|---|
| `|P…| -> R` | `CallMany + CallShared` |
| `once |P…| -> R` | none |
| `var |P…| -> R` | `CallMany` |
| `once var |P…| -> R` | none (a once, mutating call takes `var self`) |
| `copy |P…| -> R` | the markers above, plus `Copy` |

The bare form keeps today's meaning (many, reading) and its move-only use (RFC-0166); `copy` adds the permission to
duplicate (RFC-0219), `once` and `var` remove `CallMany` and `CallShared` as RFC-0161 section 3 defines them. A qualifier
is therefore a marker, not a field of a type former, and the existing diagnostics for a misused qualifier become
diagnostics about a missing marker.

**Rule 2.** The parameter list is a record. A function with keyword parameters (RFC-0223) has a row with those labels; one
with positional parameters has integer labels. The call `f(a, b)` is `Callable::call` with the row `.{ .0 = a, .1 = b }`,
which is how RFC-0161 already reads a `call` signature. The return type is the second argument.

**Rule 3 (any arity).** An impl or a bound over every function type is written over a row-kinded `Args`:

```metel
extend<record Args, Ret> dyn Callable<Args, Ret> + Copy: Clone;       // the provided Clone of a Copy callable
fun call_twice<record Args, Ret>(f: dyn Callable<Args, Ret> + CallMany, a: Args) -> .{ .0: Ret, .1: Ret } { .. }
```

This is what #894 and #893 ask for, with no variadic pack and no per-arity impl.

---

## 2. Closure and function environments are types

**Rule 4.** A closure literal has a distinct, unnameable type: the environment aggregate RFC-0161 section 1 already
describes (owned captures are fields in capture-list order, a shared or exclusive capture is a reference field, a
mutating closure holds its in-call guard). The compiler writes its `Callable` impl, with `call`'s receiver chosen by the
body (`self` when it consumes a capture, `&var self` when it mutates one, `&self` otherwise), and derives:

- the markers from that receiver (RFC-0161 section 2);
- `Copy` and `Clone` from the fields exactly as `derives Copy` does for a struct (RFC-0206, RFC-0224: the environment is
  `Copy` when every captured field is, and a `[&var x]` field makes it not);
- `Send` and `Sync` from the fields (RFC-0080 once it exists), with the RFC-0153 rule that a mutating closure is not `Sync`
  falling out of its `&var self` receiver instead of being a special case.

A named function is the same with no fields: unit-like, `Copy`, `Callable` with the markers of a pure call.

**Rule 5.** A value of an environment type (a closure, a named function, a user type that implements `Callable`) is stored
in a slot of a written function type by the ordinary `dyn` coercion (RFC-0008 section 6). A generic parameter `F:
Callable<Args, Ret> + CallMany` keeps the environment type, so a generic function that takes a closure and returns it keeps
its `Copy` by the usual rule for a type parameter (`derives Copy via F` style flow, RFC-0224). This replaces the contract
retention of metel-core#2000 to #2014: what those retain is the environment type's fields.

---

## 3. Widening is marker subset

**Rule 6.** `dyn Callable<A, R> + M` is accepted where `dyn Callable<A, R> + M'` is expected when `M ⊇ M'` (RFC-0161 section
3). That is the rule RFC-0152 states as a first-order coercion, and it needs no table: the cases `copy` to bare, many to
once and reading to mutating are all "drop a marker". The coercion changes no representation, so it composes under
function-typed parameters by ordinary variance: a parameter position is contravariant, a return position covariant.
Today RFC-0152 and RFC-0166 require the qualifiers to match exactly below the first function level because the checker
cannot prove the nested step sound; with the bound form the nested step is the same no-op and is accepted.

---

## 4. What this changes in the compiler

Not required at once; each is a consequence, in the order they become possible:

1. `Type::Fun` and `InferType::Fun` stay as the canonical form of an erased callable for now, and their three axes are read
   as the marker set. This is an alias, not a second model.
2. `infer_type_satisfies_aspect`'s function arm goes: `Copy`, `Clone` and the markers are answered by the impls of
   section 1 rule 3.
3. `unify`'s lenient use, call and mutation axes go: the check is the marker subset, applied where a coercion is.
4. A closure literal's inferred type is its environment type; the abstract-body `AbstractType::Closure` contract becomes a
   field list of that type.
5. A generic `F: Callable<..>` is monomorphized or passed as an environment type; the erased form is `dyn`.

---

## Interactions

- **RFC-0161** (under review). Its Phase A (the aspect, the synthesized impls, the markers, bounds) is the prerequisite and
  is unchanged. This RFC differs in three places: the written function type is *the* `dyn Callable` rather than a
  separate flat type (section 1); `+ Copy` on an erased callable is satisfiable (open question 1, which changes RFC-0161
  section 3's "never satisfiable"); and `Args` is the row from the start (RFC-0161's open question 4).
- **RFC-0008** (implemented). A consuming receiver on an owned aspect object (RFC-0161 section 5), and a `dyn` upcast that
  drops marker aspects, are needed. Fat pointers are not `Copy` today (section 2): open question 1.
- **RFC-0134, RFC-0152, RFC-0153, RFC-0166, RFC-0219** (integrated or implemented). The qualifiers and their rules are
  kept; they are re-expressed as markers (section 1) and the first-level restriction of RFC-0152 and RFC-0166 is relaxed
  by variance (section 3, open question 3).
- **RFC-0151, RFC-0206, RFC-0224.** `Args` is a row; an environment type derives `Copy` through the flow machinery.
- **RFC-0154.** The surface `|T| -> U` and its nesting rules are unchanged; only its meaning is stated.
- **metel-core#702.** The function half of its proposal; its tuple half is done (RFC-0151).

---

## Alternatives considered

1. **RFC-0161 as written.** Keep `Type::Fun` as a flat, three-axis type and add `dyn Callable` beside it. Two ways to hold
   a callable, with the markers duplicated as enum axes and as aspects, and `+ Copy` vacuous on the erased form (so
   `copy |T| -> U` and `dyn Callable + Copy` could not be the same thing). Rejected as the end state, kept as the first
   step.
2. **Rust's model, no erased written type.** A written function type is always a bound `F: Fn(A) -> R`; `dyn` is explicit
   and boxed. Rejected: it removes the written `|T| -> U` from struct fields, array elements and signatures, which
   RFC-0154 and the whole closure cluster keep, and it makes a non-generic higher-order function a generic one.
3. **A nominal `Fn<Args, Ret>` struct with marker parameters.** One type, but the markers become type arguments, so
   widening is a conversion between types of different argument lists, not a subset check, and a closure's environment
   cannot be its type.

---

## Non-goals

- Changing the interpreter's closure representation or the surface syntax of a function type.
- `Callable` overloading (one impl per type, as RFC-0161 section 1 fixes).
- Opaque return types for returning an environment type (`impl Callable`). Related, separate.

---

## Open questions

1. **`Copy` on an erased callable.** RFC-0008 section 2 says a fat pointer is not `Copy`, and RFC-0161 section 3 makes `+
   Copy` vacuous for that reason. But the vtable already holds the concrete type's size and alignment, and `copy |T| -> U`
   (RFC-0219) must be copyable. Either an erased callable whose bound lists `Copy` is a value whose representation copy
   duplicates the environment (the vtable gains a copy entry), or `copy |T| -> U` stays a distinct flat type. Recommended:
   the former, for callables only, because it is what makes qualifier and marker one thing.
2. **Default markers of the bare form.** Section 1 keeps many, reading, move-only. RFC-0161's un-annotated `dyn Callable`
   is the most restrictive (single-call, exclusive, non-`Copy`). Recommended: keep the written form's meaning and let the
   explicit `dyn Callable` spelling be the restrictive one.
3. **Variance of nested widening (section 3).** Relaxing RFC-0152 and RFC-0166's exact match below the first level is a
   language change. Recommended: accept it with the bound form, and keep the exact rule until then.
4. **Naming the environment type.** Rule 4 makes it unnameable, as RFC-0161 does. A function that returns a closure
   without erasing it needs an opaque return. Out of scope here; the erased return works.
5. **Interaction with RFC-0089.** A closure that captures a linear value is `linear` (RFC-0194): its environment is
   linear, its `Callable` impl takes `self`. Not decided here.
6. **Cost of the erased form at a call.** A `dyn` call is an indirect call. For the interpreter this is nothing; for the
   compiled profile it argues for keeping the generic bound the preferred form in the standard library.

---

## Implementation notes

Staged, each step independent of the next: RFC-0161 Phase A (the aspect, the markers, the environment impls); the any-arity
impls of section 1 rule 3, which close metel-core#894 and #893; the `unify` simplification; then the environment types of
section 2 and the removal of the abstract closure contracts. The language has no users, so no step needs a deprecation
period.

---

## Decision

**Outcome:** *(pending)*
