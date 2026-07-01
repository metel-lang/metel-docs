---
id: region-rfc-dependency-audit
title: "Region RFC Cluster — Type System Dependency Audit"
type: report
created_date: '2026-07-01'
rfcs: [0063, 0065, 0066, 0067, 0068, 0069, 0071, 0072, 0073, 0074, 0075, 0076, 0077]
---

# Region RFC Cluster — Type System Dependency Audit

*This report audits all type system and language features assumed by the region RFC
cluster (accepted: 0063–0071; under review: 0072–0077) and checks whether those
features are actually specified. The goal is to identify what must be resolved during
the type system phase before the region design can be considered complete.*

**Status key:**
- **Accepted** — normative, not yet implemented
- **Implemented** — in the interpreter
- **Draft** — in 0-draft, not normative
- **Gap** — not specified anywhere

---

## 1. Ownership and Affine Types

| Feature | Assumed by | Status |
|---|---|---|
| Move-by-default, affine values | 0063, 0066, 0068, 0071 | Accepted — RFC-0071 |
| `Copy` aspect + mutual exclusion with `Drop` | 0071, 0072, 0073, 0074 | Accepted — RFC-0071 |
| `Drop` aspect + destructor dispatch | 0066, 0071, 0072, 0073 | Accepted — RFC-0071 |
| `drop(x)` free function | 0071, 0068, 0073 | Accepted — RFC-0071 |
| Partial moves + pattern destructuring | 0071 | Accepted — RFC-0071 (pattern ref-binding deferred) |

This cluster is clean. RFC-0071 covers it.

---

## 2. Negative Bounds and Conditional Impls

| Feature | Assumed by | Status |
|---|---|---|
| `T: !Aspect` negative bounds | 0066, 0071, 0072, 0073, 0074 | Draft — RFC-0072 (under review; used by 0066 and 0071 before it is accepted) |
| `impl<T: !Aspect> Foo for Bar` conditional impls | 0072 §4 | Draft — RFC-0036 |
| `where T: !Drop` in function signatures | 0072 | Draft — RFC-0072; `where` clause syntax on functions is unclear |
| Negative impls `impl !Send for Rc<T>` | 0074 §2.6 | Draft — RFC-0081 (under review) |

RFC-0080's `Send` auto-impl rule grants `Send` to any struct whose fields are all
`Send`. `Rc<T, 'b>`'s reference count is an integer — `Send` by value — so the
auto-impl would incorrectly grant `Rc<T>: Send`. Absence of a positive impl is
insufficient because the auto-impl fires automatically. RFC-0081 (Negative Impls)
provides `impl !Aspect for Type` as the explicit override mechanism, following
Rust's model: blanket impls are permitted, negative impls override them.

---

## 3. Never Type and Fallibility

| Feature | Assumed by | Status |
|---|---|---|
| Never type `!` | 0063 (`AllocationError = !`), 0073 | **Implemented** — defined in public spec (types.md §Never Type) as the bottom type for diverging expressions |
| `Perhaps<T>` stdlib type (nullable) | 0063, 0065, 0067, 0074, 0075 | **Implemented** — defined in public spec (types.md §Perhaps) |
| `Result<T, E>` stdlib type (fallible) | 0063, 0068, 0074, 0075 | **Implemented** — defined in public spec (types.md §Result) |
| `Result<T, !>` → `T` collapse rule | 0063 §1.1 | Draft — RFC-0078 (under review) §3.2 (uninhabited-variant exhaustiveness) and §3.3 (inhabited-singleton coercion) together specify this |

**Naming is settled** and both types are implemented. RFC-0078 resolves the collapse
rule via two general rules: any uninhabited variant may be omitted from a match
(§3.2), and any enum with exactly one inhabited single-field variant implicitly
coerces to that field's type (§3.3). `Result<T, !>` is a special case of both.
RFC-0063's infallible allocation (`@[r] T` when `AllocationError = !`) is a
separate allocation-expression rule that does not rely on the coercion.

---

## 4. Standard Aspects

| Feature | Assumed by | Status |
|---|---|---|
| `Clone` aspect | 0066, 0071, 0074, 0076 | Draft — RFC-0080 (under review) |
| `Deref<Target = T>` / `DerefMut` aspects | 0074 §2.3 | Draft — RFC-0080 (under review) |
| `Send` aspect | 0063, 0073, 0074 | Draft — RFC-0080 (under review); auto-impl rules depend on RFC-0060 closed-world coherence |
| `Sync` aspect | 0074 | Draft — RFC-0080 (under review); same coherence dependency |
| `NotCapturing<T>` bound | 0076 | **Gap** — referenced in RFC-0076; no RFC defines it |

`Clone` is used in RFC-0071 itself (which is accepted) without being formally
defined there — RFC-0071 treats it as pre-existing. `Send` and `Sync` are referenced
throughout the region system for sendability rules but live in the draft concurrency
RFC. `Deref` is structural to the smart pointer model in RFC-0074.

`NotCapturing<T>` is a novel bound introduced in RFC-0076 with no antecedent. It
would need its own RFC or a section within a type system RFC.

---

## 5. Brand Types and Rank-2 Quantification

| Feature | Assumed by | Status |
|---|---|---|
| `brand 'b` parameter syntax on types | 0074, 0076 | Draft — RFC-0076 (under review) |
| `brand` block scope introducer | 0074, 0076 | Draft — RFC-0076 (under review) |
| `PhantomBrand<'b>` zero-size stdlib type | 0074, 0076 | Draft — RFC-0076; required by accepted RFC-0074 |
| `forall<brand 'b>` rank-2 quantifier | 0076 | Draft — RFC-0076; no formal rank-2 mechanism otherwise specified |
| Allocation-site brand freshness rule | 0076 | Draft — RFC-0076 |

The brand cluster is self-contained within RFC-0076. The problem is that RFC-0074
(which is accepted-pending) already uses `Rc<T, 'b>` and `PhantomBrand<'b>`, making
it normatively dependent on a draft RFC. RFC-0074 cannot be fully accepted until
RFC-0076 is at minimum co-accepted.

---

## 6. Stdlib Types

| Feature | Assumed by | Status |
|---|---|---|
| `USize` | 0074 (`strong: USize`) | Partial — RFC-0007 specifies uint types (Implemented) but `USize` as platform-width type is unspecified |
| `AtomicUSize` | 0074 (`ArcInner.strong`) | **Gap** — no RFC specifies atomic types |
| `Vec<T>` | 0076 (example code) | **Gap** — RFC-0054 specifies `List<T>` (Implemented); RFC-0076 uses `Vec<T>`; relationship unclear |
| `String` | 0063–0077 throughout | **Gap** — used everywhere; no RFC specifies it |
| `Bytes` | 0077 | **Gap** — no RFC specifies this |
| `HashMap<K, V>` | 0077 | **Gap** — no RFC specifies this |
| `List<T>` | 0063, 0069, 0073, 0074 | Implemented — RFC-0054 |

The `Vec<T>` vs `List<T>` inconsistency is a naming problem: the implemented type is
`List<T>` but RFC-0076 writes `Vec<T>`. Either RFC-0076 uses the wrong name or the
type was renamed; either way, one needs updating. `String` is the most pervasive
unspecified stdlib type. `AtomicUSize` is structurally required by `Arc` internals.

---

## 7. Closures with Region/Brand Parameters

| Feature | Assumed by | Status |
|---|---|---|
| `[r]() -> {}` closure region parameter syntax | 0065 §4, 0073, 0075 | Draft — RFC-0050 (draft); RFC-0065 §4 explicitly defers to it |
| Closure types with brand parameters | 0076 | Draft — RFC-0050 (draft) |

RFC-0065 acknowledges the deferral. All region-parameterised closures depend on
RFC-0050 being resolved.

---

## 8. Type Aliases

| Feature | Assumed by | Status |
|---|---|---|
| `type Foo = Bar` alias syntax | 0075 UQ2 | **Gap** — no RFC specifies type aliases |
| `type SubRegion<R: Region> impl Region, Outlives<R>` — alias-with-impl form | 0069 | **Gap** — this notation does not match standard alias syntax; no RFC defines it |

RFC-0069 uses a notation that implies a constrained type alias with an embedded impl
bound. This is not standard alias syntax in any form specified elsewhere. It may be
that RFC-0069 intended a `where`-clause form, or a proper newtype — but the current
notation is underspecified.

---

## 9. Region System Internals

| Feature | Assumed by | Status |
|---|---|---|
| `Region` aspect — formal method signatures | 0063, 0077 | Partial — RFC-0063 §1.1 sketches it; allocation and deallocation methods are not fully listed |
| `Outlives<R>` as a formal stdlib aspect | 0063, 0069, 0077 | Partial — used throughout but never formally specified with a method signature or derive rule |
| `SharedRegion` aspect | 0077 §2.4 | **Gap** — mentioned in RFC-0077 without definition; may be a stale reference to the old RFC-0074 model |
| Arc/Rc model split between RFC-0063 and RFC-0074 | 0063 vs 0074 | **Gap** — RFC-0063 presents `Arc<T>[Heap]` as a region-parameterised type; RFC-0074 (post-rewrite) defines `Arc<T, 'b>` as a library struct; RFC-0063 has not been amended |

The RFC-0063 / RFC-0074 contradiction is the most urgent internal consistency issue.
RFC-0063 is an accepted RFC. It presents a model of Arc and Rc that RFC-0074 explicitly
rejects. Until RFC-0063 is amended, the accepted cluster contains a contradiction.

The `SharedRegion` reference in RFC-0077 is likely a stale reference from before the
RFC-0074 rewrite and should be removed or replaced.

---

## 10. Other Language Features

| Feature | Assumed by | Status |
|---|---|---|
| `given`/`using` implicit parameters | 0076 (IO capability example) | **Gap** — referenced in RFC-0076 as if it exists; no RFC specifies it |
| Return-position `impl Aspect` | referenced in drafts | Under review — RFC-0037 |
| Aspect objects (`dyn Aspect` or equivalent) | referenced by name | Under review — RFC-0008 |
| `impl[r] Struct[r]` / `aspect impl[r]` headers | 0077 | Draft — RFC-0077 specifies this |

---

## Summary

### Gaps That Block Region RFC Acceptance

These gaps mean the under-review or accepted region RFCs are internally inconsistent
or underspecified right now. They must be resolved in the type system phase:

1. **`Result<T, !>` collapse rule** — addressed by RFC-0078 (under review). The general
   uninhabited-variant exhaustiveness rule (§3.2) and the inhabited-singleton coercion
   rule (§3.3) together specify the collapse. `Result<T, !>` is a consequence of both
   general rules.

2. **`Clone`, `Deref`, `Send`, `Sync` aspects** — addressed by RFC-0080 (under review).
   Auto-impl rules for `Send` and `Sync` depend on RFC-0060 specifying closed-world
   coherence.

3. **Negative impls** (`impl !Send for Rc<T>`) — addressed by RFC-0081 (under review).
   Required because the `Send` auto-impl (RFC-0080) would otherwise grant sendability
   to `Rc<T>` via its integer reference-count field.

3. **RFC-0063 amendment for Arc/Rc** — resolved in this audit session (committed).

4. **`Vec<T>` vs `List<T>`** — resolved in this audit session (committed).

### Gaps That Can Wait for the Type System Phase

These are real gaps but do not block the immediate region RFC work:

- `NotCapturing<T>` — RFC-0076 internal; can be defined within or alongside it.
- `AtomicUSize` — required by `Arc` internals; can be deferred to an atomics RFC.
- `String`, `Bytes`, `HashMap` — stdlib gaps; lower priority than type system.
- `given`/`using` — RFC-0076 future-work example only; does not affect the core design.
- `Outlives<R>` formal spec — partial; needs completion but not a blocker.
- `Region` aspect formal method signatures — partial; RFC-0063 can be amended.
- RFC-0050 (closure region parameters) — explicitly deferred by RFC-0065; non-blocking.
- Type alias syntax — needed eventually; can be resolved alongside RFC-0075 which mentions it.
- `SharedRegion` stale reference in RFC-0077 — likely a leftover; should be cleaned up.
