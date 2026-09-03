---
id: rfc-0061
title: "Structural Aspect Bounds"
date: '2026-07-01'
status: implemented
updated: '2026-08-14'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/549'
impl_status: implemented
coverage:
  "1": { spec: "spec.declarations.structural-aspect-bounds.legality-1" }
  "1.1": { spec: "spec.types.arrays.legality-1" }
  "2": { spec: "spec.declarations.structural-aspect-bounds.legality-2" }
  "3": { spec: "spec.declarations.structural-aspect-bounds.legality-3" }
  "4": { spec: "spec.declarations.structural-aspect-bounds.legality-4" }
  "4.1": { kind: blocked, reason: "The Ord array impl is blocked on draft RFC-0062; the Hash half is likewise deferred but has no dedicated RFC yet.", ref: "docs/public/rfcs/0-draft/rfc-0062-ord-comparison-aspect.md" }
  "5": { spec: "spec.declarations.structural-aspect-bounds.legality-5" }
  "6": { spec: "spec.declarations.structural-aspect-bounds.legality-6" }
  "7": { spec: "spec.declarations.structural-aspect-bounds.legality-7" }
  "7.1": { spec: "spec.declarations.structural-aspect-bounds.legality-8" }
  "7.2": { spec: "spec.declarations.structural-aspect-bounds.legality-9" }
  "7.3": { spec: "spec.declarations.structural-aspect-bounds.legality-10" }
  "7.4": { spec: "spec.declarations.structural-aspect-bounds.legality-11" }
---

> **Status — accepted.** Depends on RFC-0060 (Aspect Impl Coherence) and
> RFC-0036 (Conditional Impl Blocks). Specifies how aspect bounds are satisfied for
> structural types — arrays (`T[]`), tuples, and function types — and how `std::core`
> provides blanket impls for structural type constructors.

> **Status — integrated (2026-07-13).** Integrated ahead of implementing issue #549. Confirmed no error-code collision (T0012 reuse, consistent with RFC-0036's precedent). Confirmed via direct source testing that #537/#545 did NOT leave structural impls in a safe not-yet-implemented state as this RFC's dependents assumed -- three independent hard-crash/skip bugs block any structural impl today (inference.rs's unconditional internal error for any non-Named impl target, a hardcoded array-method dispatch gate, and registry.rs silently skipping structural targets during registration) -- flagged as groundwork issue #549 must fix first, not a gap in this RFC's own content. A first integration draft also carried array auto-impl propagation as §5, but that was later rehomed to RFC-0096 so this RFC only owns structural impl lookup/bounds and the explicit std::core structural impl surface.

> **Status — implemented (2026-07-14).** Issue #549 landed the structural impl machinery this RFC depends on. The earlier array auto-impl propagation subsection was rehomed to RFC-0096, so no remaining unimplemented dependency stays inside RFC-0061's own scope.

> **Status — qualified (2026-08-01, metel-core#581 and #239).** Of the three structural
> target kinds this RFC grants, **one is implemented**: `extend<T> T[]: Display { … }`
> registers via `array_target_generic_name` and dispatches. Everything else is accepted by
> the parser and then invisible to *both* method dispatch and bound satisfaction — a
> concrete array target, and a tuple, record or `fun` target in **either** form. All of it
> is now rejected with `T0003`, rather than reaching an internal error (the concrete case)
> or compiling into a silent no-op (the generic tuple/record case).
>
> Rejected rather than accepted because a block whose methods can never be found is the
> "compiles and does nothing" failure RFC-0071 §9c exists to prevent, and the same
> judgement was applied to inert `Drop` impls in metel-core#601. It costs nothing: nobody
> can depend on the current behaviour, because the current behaviour is that the impl has
> no effect.
>
> Tuple and record dispatch is metel-core#239, deferred to v0.13.0. RFC-0116 §3's
> local-aspect-impl-on-a-record bullet stays aspirational until it lands.

> **Status — corrected (2026-08-14, found while drafting RFC-0134).** §7.4 below claims
> closures "have distinct anonymous types... generated per-closure-site," distinguishing
> them from `fun(A) -> B`. That does not match the implementation and never did — checked
> directly against `metel-frontend/src/types/mod.rs`: `Type` has exactly one function-type
> variant, `Fun(Vec<Type>, Box<Type>)`, with no separate closure case and no
> per-closure-site tag anywhere in the enum. `RuntimeCallable` has only `Closure` and
> `Intrinsic`, not a third closure-specific kind either. A closure and a named function
> pointer of matching signature are the same `Type::Fun` value, distinguished (if at all)
> only by an empty vs. non-empty capture list at the value level, never by type. §7.4's
> text below is left as originally written for the historical record; read "distinct
> anonymous types" as this RFC's own uncorrected assumption, inherited from RFC-0050/
> RFC-0049's framing at the time this RFC was integrated, not a description of anything
> that was ever built. RFC-0134 (Closure Call Capability) §4 is the document that depends
> on "no distinct closure type" and is where this was found; nothing in §§1-6 of this RFC
> (array/tuple structural impls) is affected.

> **Status — superseded in part (2026-08-14): §1.1's array model is out of date.** §1.1
> below describes `T[]` as a **sized, owned** sequence — "a fat struct carrying a pointer
> to element storage, a length, and a capacity" — and concludes "because it owns its
> element storage, `T[]` is never `Copy`." **RFC-0126 (`T[]` as a Copy Borrowed View,
> `4-implemented`, shipped in metel-core#593, v0.12.0) replaced that model**: `T[]` is a
> non-owning, immutable *view*, and is `Copy` **unconditionally** — including when the
> element type is not `Copy`, since a view of a `T` holds a location rather than a `T`.
> The implementation matches RFC-0126, not §1.1: `infer_type_satisfies_aspect`
> (`typeinference/mod.rs`) returns `true` for `Copy` on `InferType::Array` with no
> condition on the element type, and the behaviour is observable —
>
> ```metel
> let a = [1, 2, 3];
> let b = a;
> println(a[0]);   // accepted under --move-check; prints 1
> ```
>
> — where the same shape on a non-`Copy` named struct is correctly rejected with `T0019`.
> Read §1.1's representation paragraph and its `Copy` conclusion as describing the model
> RFC-0126 superseded. §§2-6's structural-impl lookup rules are unaffected: they concern
> which impls can be *written* and *found* for array targets, which RFC-0126 does not
> change. Neither RFC previously cited the other; RFC-0126 is now in References below.
> (Found while checking RFC-0134 §1's premise that `Type::Fun`'s unconditional `Copy` was
> a lone anomaly — `InferType::Array` has the same shape, but by design rather than by
> regression. Separately, that both live as hardcoded typechecker rules rather than
> stdlib impls is already tracked as metel-core#263.)

> **Status — §7.2 is not implemented (2026-08-14).** §7 below states that every function
> type automatically implements `Callable` (§7.1) and that `Copy`, `Clone`, `Send`, and
> `Sync` are provided for function pointers by `std::core` with no user declaration
> needed (§7.2's table). **None of that is in the implementation.** Function types satisfy
> *no* aspects: `infer_type_satisfies_aspect` (`typeinference/mod.rs`) answers every
> aspect query for them with `false`, via an arm whose own comment states the intent —
> `InferType::Var(_) | InferType::Never | InferType::Fun(_, _) => false`, *"`Never` and
> `Fun` implement nothing."* Confirmed against the release binary for a named function and
> a closure alike:
>
> ```
> [T0012] `(i64) -> i64` does not implement `Copy` (required by `needs_copy`)
> [T0012] `(i64) -> i64` does not implement `Clone` (required by `needs_clone`)
> [T0012] `() -> String` does not implement `Copy` (required by `needs_copy`)
> ```
>
> This is the same category as the §7.4 correction above — specification that was never
> built — but with a wider blast radius, since §7.2's table is what RFC-0134 §1 originally
> cited as corroboration for "a named function pointer is trivially `Copy`." That claim
> remains true of the *move checker*, which special-cases `Type::Fun` to `Copy` in
> `is_copy` and bypasses the aspect system entirely; it is false of aspect-bound
> satisfaction. RFC-0134's Open Questions section now records the resulting two-notions-of-
> `Copy` split in detail. Note the 2026-08-01 status block above already found the
> *impl-registration* side of `fun` targets inert (rejected with `T0003`); this note
> records that the `std::core`-provided side of §7 is equally absent. §§1-6 are unaffected.
> **Tracked as metel-core#739**, which owns closing the gap — including whether §7.2's
> table is implemented as specified or amended, and whether §7.1's `Callable<A, B>`
> auto-impl (which RFC-0008's `dyn Callable<A, B>` depends on) is built or explicitly
> deferred. Related: metel-core#702 is the architectural root cause (model non-record
> structural types as regular types), and metel-core#263 tracks moving the analogous
> hardcoded tuple/fixed-array `Copy` rules into the stdlib.

## Summary

Aspect bounds on structural types — `T[]`, `(A, B)`, `fun(A) -> B` — cannot be
satisfied by the standard impl lookup, which keys on type names. Without a
specification for structural impls:

- `println([1, 2, 3])` fails at compile time with no way to fix it.
- Generic library code cannot write `extend<T: Display> T[]: Display`.
- The type checker has no representation for "array of displayable elements is
  displayable."

This RFC specifies:

1. **Structural type constructors** (`T[]`, tuples, `fun`) are owned by `std::core`
   for orphan rule purposes.
2. **Blanket impls for structural constructors** may be declared in `std::core` using
   the conditional impl syntax from RFC-0036.
3. **Phase 1 behaviour**: without a matching structural impl, structural types fail
   aspect bounds with a precise diagnostic.
4. **Standard impls**: `std::core` provides `Display`, `Clone`, and `Eq` for arrays
   when the element type satisfies the bound.
5. **Out of scope here:** array auto-impl propagation (`Send`/`Sync`/`Drop`) belongs
   to RFC-0096's auto-impl mechanism, not to this RFC's structural-impl lookup rules.
6. Tuples and function types are covered below; tuples are deferred.

---

## 1. Structural Type Constructors

A structural type is one defined by a constructor built into the language rather than
declared by a user. The structural constructors in Metel are:

| Constructor | Example | Notes |
|---|---|---|
| Array | `T[]` | Owned, sized, homogeneous sequence of `T` |
| Tuple | `(A, B)`, `(A, B, C)`, … | Heterogeneous fixed-arity product |
| Function type | `fun(A) -> B` | Function pointer; not closures (RFC-0050) |

These are not nominal types — they have no name that can appear as the key in an
impl. For the orphan rule (RFC-0060 §1), structural type constructors are treated as
belonging to `std::core`. A user module may not write `extend T[]: Aspect` unless
the **aspect** is local to that module.

### 1.1 Array representation

`T[]` is a **sized, owned** sequence type: a fat struct carrying a pointer to
element storage, a length, and a capacity. It is not an unsized slice. It may be
passed by value (moving ownership of the fat struct) and may appear as a struct field.
Because it owns its element storage, `T[]` is never `Copy`.

---

## 2. Blanket Impls for Structural Constructors

`std::core` may declare impls whose target is a structural type constructor. The
syntax follows RFC-0036 conditional impl syntax:

```metel
// std::core
extend<T: Display> T[]: Display {
    fun to_string(self: &T[]) -> String { ... }
}
```

The type parameter `T` ranges over all types; the `where` bound `T: Display` is the
condition. The impl is applicable to any array `U[]` where `U: Display`.

This is the mechanism that makes `println([1, 2, 3])` compile: `[1, 2, 3]` has type
`i64[]`; `i64: Display`; therefore the conditional impl applies.

Coherence rules for structural impl targets follow RFC-0060 §2 and RFC-0036 §3.1
without special cases: two impls of the same aspect for `T[]` are checked for
overlap by the standard rules. If one uses `T: Bound` and the other uses `T: !Bound`
(syntactic negation, RFC-0036 §3.1), they are disjoint and both accepted. If neither
directly negates the other, they are a conflict.

---

## 3. Phase 1 Behaviour

Until `std::core` provides an impl for a structural type constructor, any attempt to
use a value of a structural type in a position that requires an aspect bound fails
with a diagnostic that names the structural constructor:

```
T0012: i64[] does not implement Display
       hint: arrays implement Display only when their element type does;
             no impl<T: Display> Display for T[] is registered
```

This is a compile error, not a runtime panic. Code that was previously passing this
check silently (because structural types were skipped by the bound checker) is now
correctly rejected.

---

## 4. Standard Impls

`std::core` provides the following explicit blanket impls for arrays:

```metel
extend<T: Display> T[]: Display {
    fun to_string(self: &T[]) -> String {
        // "[" + elements joined by ", " + "]"
    }
}

extend<T: Clone> T[]: Clone {
    fun clone(self: &T[]) -> T[] {
        // element-wise clone into new backing storage
    }
}

extend<T: Eq> T[]: Eq {
    fun eq(self: &T[], other: &T[]) -> boolean {
        // element-wise equality, short-circuiting; false if lengths differ
    }
}
```

These impls are in `std::core` and cannot be overridden by user code (orphan rule).
`List<T>` is a nominal struct and its impls are separate from the array impls; both
coexist.

### 4.1 Deferred standard impls

> **Coverage: blocked** (see frontmatter). `Ord` awaits RFC-0062; `Hash` has no aspect RFC yet.

The following blanket impls are natural but deferred pending their aspect definitions:

| Impl | Blocked on |
|---|---|
| `extend<T: Ord> T[]: Ord` — lexicographic ordering | RFC-0062 (Ord Comparison Aspect, draft) |
| `extend<T: Hash> T[]: Hash` — element-wise hashing | No Hash RFC yet |

Until RFC-0062 is accepted, `T[]` does not implement `Ord`. Until a Hash RFC is
accepted, `T[]` does not implement `Hash`. The blanket impls will be added to
`std::core` when the respective aspect RFCs are accepted.

---

## 5. Rehomed: Array Auto-Impl Propagation

An earlier integrated draft placed array propagation of `Send`, `Sync`, and `Drop`
here, because arrays are structural types and the rule is phrased structurally over an
array's element type. That ownership boundary was wrong.

Whether `T[]` auto-implements a marker aspect is part of the **auto-impl mechanism**
itself, now owned by RFC-0096, not part of structural impl lookup. RFC-0061 owns:

- how structural types participate in ordinary impl lookup
- which explicit blanket impls `std::core` may write for structural constructors
- what diagnostics appear when no matching structural impl exists

RFC-0096 owns whether a marker aspect is synthesized without any explicit impl block
at all, arrays included.

---

## 6. Tuples

Tuples (`(A, B)`, `(A, B, C)`, …) have variable arity and heterogeneous element
types. Providing blanket impls for every arity — the Rust approach — requires
per-arity boilerplate or variadic generics. Both are deferred:

- Per-arity impls (e.g. up to arity 12): deferred pending a decision on where
  boilerplate of this kind lives.
- Variadic generics: no design exists; deferred.

Until tuples have impls, they fail aspect bounds in Phase 1 with a diagnostic:

```
T0012: (i64, String) does not implement Display
       hint: tuple impls are not yet provided; use a named struct instead
```

Auto-impl propagation (RFC-0096) applies to tuples as soon as per-arity blanket impls land:
`(A, B): Send` when `A: Send` and `B: Send`, and so on. The auto-impl rule already
handles this — no separate specification is needed once the blanket impls exist.

---

## 7. Function Types

`fun(A) -> B` is a **function pointer** type — a word-sized code address with no
captured state. It is distinct from closures, which are covered by RFC-0050.

### 7.1 `Callable`

> **Not implemented — deferred to RFC-0161 (2026-09-01).** The `Callable<A, B>` aspect,
> its auto-impl for function types, and `dyn Callable<A, B>` were **specified here and in
> RFC-0008 but never built** (verified against the interpreter: no `Callable` impl for
> function types, no `dyn Callable` coercion). The whole concept — aspect, object form,
> and the marker-aspect refinements the v0.13.0 closure cluster once sketched — is now
> owned in full by **RFC-0161 (Callable Object Contract), v0.13.1**. In v0.13.0 a closure
> or function value is only ever a concrete function type; there is no `Callable` bound
> and `dyn Callable<…>` does not parse. This subsection is retained as the original
> reservation RFC-0161 builds on.

Every function type `fun(A) -> B` automatically implements `Callable<A, B>` — the
aspect for callable values. The compiler provides this impl for all function pointer
types without a declaration at the user level:

```metel
// auto-provided by the compiler for every function pointer type
extend fun(A) -> B: Callable<A, B> {
    fun call(self: &fun(A) -> B, arg: A) -> B { (*self)(arg) }
}
```

This is what allows function pointers to be passed as `&dyn Callable<A, B>` (RFC-0008)
and used in higher-order functions. The formal definition of `Callable` — its aspect
declaration and method signatures — is deferred to a follow-on stdlib RFC; its
object-safety is established in RFC-0008 §3.

### 7.2 Copy, Clone, Send, Sync

Function pointers carry no state. Their relevant aspect impls:

| Aspect | Status | Reason |
|---|---|---|
| `Copy` | Yes | Function pointers are word-sized; bitwise copy is correct |
| `Clone` | Yes | Derived from `Copy` via RFC-0080 blanket |
| `Send` | Yes | No captured state; code pointers are globally valid |
| `Sync` | Yes | Same reason as `Send` |

These are provided by `std::core`. No user declaration is needed.

### 7.3 Aspects function pointers do not implement

| Aspect | Reason |
|---|---|
| `Display` | No canonical string representation for code addresses |
| `Eq` | Function equality is undecidable in general |
| `Ord` | No total ordering on functions |
| `Hash` | Pointer-equality hashing would be address-dependent and non-portable |
| `Drop` | Function pointers own no resources |

Attempting to use `fun(A) -> B` where one of these bounds is required is a compile
error under Phase 1 behaviour (§3).

### 7.4 Closures

Closures defined in RFC-0050 have distinct anonymous types that implement `Callable`
and may implement `Send` and `Sync` depending on their captures. `fun(A) -> B` is not
a closure type; closure types are structural types generated per-closure-site. Their
aspect impls are specified in RFC-0050.

---

## 8. Unresolved Questions

1. **Tuple impls.** Per-arity blanket impls vs. variadic generics. Deferred.

2. **`Display` vs `Debug` for arrays.** Rust provides `Debug` for arrays but not
   `Display`, arguing that collections have no canonical human format. Metel's
   decision to provide `Display for T[]` is made here based on the `dbg` formatter
   already covering the debug case. This may be revisited.

3. **`Callable` formal definition.** The `Callable<A, B>` aspect is referenced in
   RFC-0008 (object safety) and this RFC (function pointer auto-impl) but has no
   formal aspect declaration. Its definition — including multi-argument forms and
   the distinction between `&self`, `&var self`, and by-move receivers — is deferred
   to a follow-on stdlib RFC.

4. **Multi-argument function types.** `fun(A, B) -> C` should implement
   `Callable<(A, B), C>` (with a tuple argument) or a multi-parameter `Callable`.
   The exact mechanism depends on the tuple blanket impls and the `Callable` formal
   definition; both are deferred.

---

## References

- RFC-0036 (Conditional Impl Blocks) — the conditional impl syntax used for
  structural blanket impls.
- RFC-0050 (Closure Capture Lists, `4-implemented` as of 2026-09-02) — closure types and
  their aspect impls; distinct from function pointer types.
- RFC-0060 (Aspect Impl Coherence) — orphan rule; structural constructors owned by
  `std::core`; overlap detection.
- RFC-0062 (Ord Comparison Aspect, draft) — prerequisite for `extend<T: Ord> T[]: Ord`.
- RFC-0066 (Region Pointer Extraction) — §2.2 move-out constraint requires `T: !Drop`;
  array `!Drop` propagation now belongs to RFC-0096.
- RFC-0071 (Ownership and Move Semantics) — `Copy`/`Drop` mutual exclusion; function
  pointers are `Copy`.
- RFC-0080 (Stdlib Aspects) — `Clone`, `Send`, `Sync` formal definitions; `Copy`
  implies `Clone` blanket; function pointer `Send`/`Sync` follows from §3.2/§4.2.
- RFC-0096 (Auto-Impl Aspects, under review) — owns array propagation of `Send`/`Sync`/`Drop`
  that an earlier draft of this RFC had carried as §5.
- RFC-0008 (Aspect Objects) — `Callable<A, B>` object safety; `dyn Callable<A, B>`.
- RFC-0054 — `List<T>` as a nominal struct; `List<T>` impls are separate from array
  impls and coexist.
- RFC-0126 (`T[]` as a Copy Borrowed View, `4-implemented`) — replaced §1.1's owning-buffer
  array model with a non-owning view that is `Copy` unconditionally; see the 2026-08-14
  partial-supersession note above.
- RFC-0134 (Closure Call Capability, implemented) — the RFC whose §4 investigation found
  §7.4's "distinct anonymous types" claim below doesn't match the implementation; see
  the 2026-08-14 correction note above.
