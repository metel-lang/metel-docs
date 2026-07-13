---
id: rfc-0060
title: "Aspect Impl Coherence"
date: '2026-07-01'
status: integrated
updated: '2026-07-12'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/244'
impl_status: in-progress
---

> **Status — accepted.** No dependencies on other under-review RFCs; this RFC
> is a prerequisite for RFC-0036 (Conditional Impl Blocks), RFC-0061 (Structural
> Aspect Bounds), RFC-0080 (Stdlib Aspects), and RFC-0081 (Negative Impls). Defines
> the orphan rule, overlap detection, closed-world coherence, auto-impl rules, and
> the priority of negative impls over blanket impls.

> **Status — integrated (2026-07-11).** Integrated into public/reference/spec/declarations.md as a new Aspect Implementation Coherence section (orphan rule, overlap detection, closed-world assumption, auto-impl, negative-impl priority). Two forward-references in Negative Bounds/Negative Impls, written anticipating this integration, now point here instead. Added T0014/T0015 to error-codes.md. Fixed a stale error-code collision in RFC-0033 (its recommended T0013/T0014 were both already claimed by other, unrelated shipped features).

> **Status — in progress (2026-07-12).** Confirmed via issue #244: §1 (orphan rule) and §2's concrete-impl half (overlap detection between fully-applied types) were already delivered by #238; §5's explicit-vs-explicit half (negative impl conflicting with a concrete positive impl) was delivered by #264. The `merge_from` bug named in #244's own text (`method_env`/`method_receiver_env` silently dropping one module's methods when two independent modules implement different aspects for the same foreign type — confirmed live via a diamond-dependency repro) is now fixed. Still unimplemented: §2's blanket-impl disjointness half and §5's blanket-priority half (both blocked on RFC-0036/#241), §3 closed-world negative-bound discharge (blocked on RFC-0072/#243), and §4 auto-impl rules (blocked on RFC-0080/RFC-0096) — a majority of this RFC's own specified content, not merely sibling properties. #244 stays open until those land.

> **Status — in progress (2026-07-13).** #244 landed the remaining, previously-blocked-but-now-unblocked pieces: struct/enum literal construction and RFC-0082 associated-type completeness now consult conditional impls for §3's closed-world negative-bound discharge (both polarities — a genuine type-arg-stripping bug in the original construction.rs call sites had made this vacuously pass regardless of the real bound, found and fixed during review); a concrete negative impl now overrides a blanket positive impl for its exact instantiation (§5's blanket-priority half), without disturbing the existing negative-vs-concrete-positive conflict rule (RFC-0081 §2.2/#264); and §2's blanket-impl disjointness half now works via a shape-crossing compatibility check in `coherence.rs`'s overlap detection (the pre-#244 exact-key grouping never even compared a blanket impl's canonicalized target against a concrete impl's, silently missing real conflicts). Only §4 (auto-impl rules) remains unimplemented, still blocked on RFC-0080/RFC-0096 on their own unrelated timeline — everything else this RFC specifies is done.

## Summary

Every `(aspect, type)` pair must have at most one implementation visible to the
program, independent of module load order. This RFC specifies:

1. **Orphan rule** — an impl is permitted only when the aspect or the type is local.
2. **Overlap detection** — two impls for the same `(aspect, type)` pair are a
   compile error.
3. **Closed-world assumption** — absence of an applicable impl is a provable fact;
   `T: !Aspect` is dischargeable from the absence of any impl covering `T`.
4. **Auto-impl rules** — marker aspects may declare rules under which the compiler
   automatically derives an impl for a type.
5. **Negative impl priority** — an explicit negative impl (RFC-0081) overrides any
   blanket positive impl.

---

## 1. Orphan Rule

An `impl Aspect for Type` is permitted only if **at least one of** the following is
declared in the same module as the impl:

- the aspect (`Aspect`), or
- the outermost type constructor of `Type` (i.e., the struct or enum, ignoring
  type arguments).

Built-in aspects and built-in types are considered local to `std::core`. User code
may write:

- `impl Display for MyStruct` — type is local. Permitted.
- `impl MyAspect for i64` — aspect is local. Permitted.
- `impl Display for i64` — both foreign. Permitted only in `std::core`.

A violating impl is a compile-time error (`T0014 — orphan implementation`).

> **Note (2026-07-11):** this wording assumes `Type` always has an outermost type
> constructor. A bare-parameter blanket impl (`impl<T: Bound> Aspect for T` — see this
> RFC's own §3/§5 examples below, which already use exactly this form) has none: `T`
> is the impl's own generic parameter, not a declared struct or enum. RFC-0097
> (draft) formalizes that target-locality is vacuously unsatisfiable for this shape of
> impl, so such an impl is permitted only via the aspect side of this rule.

The orphan rule guarantees that coherence is checkable locally: a module can only
add impls it "owns" one half of. No whole-program overlap scan is required at each
use site.

---

## 2. Overlap Detection

Two impls of the same aspect conflict when there exists any concrete type instantiation
that both would cover. A conflict is a compile-time error (`T0015 — conflicting
implementation`), reported with both impl spans.

**Concrete impls** (no type parameters) conflict when their fully-applied types are
identical. `impl Display for List<i64>` and `impl Display for List<String>` do not
conflict — they cover disjoint sets of types. `impl Display for List<i64>` appearing
twice is a conflict.

**Conditional/blanket impls** (RFC-0036) conflict when there exists a concrete
instantiation satisfying both impls' bounds simultaneously. The compiler checks whether
the bound sets are disjoint; if it cannot prove disjointness, the pair is a conflict.
Negative bounds (RFC-0072) in `where` clauses can make disjointness explicit.

With the orphan rule in force, overlap can only arise within a single module or
between a module and `std::core`, making detection local.

---

## 3. Closed-World Assumption

The compiler operates under a closed-world assumption (CWA): the set of impls in the
program is known at compile time and is complete. No future impl can be added by a
module not visible at compilation.

**Consequence for negative bounds:** To discharge `T: !Aspect`, the compiler checks
whether any impl — concrete or blanket — applies to `T`. If none applies, `T: !Aspect`
is proven. This requires no explicit negative impl declaration when no blanket covers `T`.

**Consequence for blanket impls:** A blanket `impl<T: Foo> Bar for T` makes every
type satisfying `Foo` implement `Bar`. The compiler expands blankets when checking
applicability. `T: !Bar` is dischargeable only when no applicable blanket covers `T`.

When a blanket would otherwise cover a type that must not have the aspect, a negative
impl (RFC-0081) is required to override it. CWA is what makes the negative impl's
override definitive: there are no future impls that could re-grant the aspect.

---

## 4. Auto-Impl Aspects

A marker aspect (an aspect with no methods) may be designated as an **auto-impl
aspect**: the compiler automatically derives an implementation for any type all of
whose field types also implement the aspect, without requiring an explicit impl
declaration from the programmer.

The rule is structural: for a struct, every field type must implement the aspect;
for an enum, every field type in every variant must implement the aspect.

The following stdlib aspects are auto-impl aspects (RFC-0080):
- `Send` — auto-impl when all fields are `Send`
- `Sync` — auto-impl when all fields are `Sync`

An auto-impl is a positive impl generated by the compiler. It is subject to negative
impl override (§5) and to overlap detection (§2): an explicit impl for a type that
the auto-impl rule would also cover is a conflict.

The syntax by which an aspect definition declares itself as auto-impl is deferred to
RFC-0012 (Derived Aspects), which will specify the general derive mechanism. This RFC
establishes the concept and its coherence properties; RFC-0012 specifies the surface
syntax.

---

## 5. Negative Impl Priority

An explicit negative impl (RFC-0081) takes priority over any auto-impl or blanket
positive impl that would otherwise apply. Priority resolution:

1. Explicit negative impl → type does not have the aspect.
2. Explicit positive impl → type has the aspect.
3. Auto-impl rule matches → type has the aspect (unless overridden by 1).
4. Blanket positive impl matches → type has the aspect (unless overridden by 1).
5. No applicable impl → type does not have the aspect (CWA, §3).

An explicit positive impl and an explicit negative impl for the same concrete type
is a coherence error (`T0015`). A negative impl and a blanket positive impl for the
same concrete type is permitted — the negative impl wins.

---

## 6. Diagnostics

| Code | Meaning | Reported at |
|---|---|---|
| `T0014` | Orphan implementation: neither the aspect nor the outermost type constructor is local | the `impl` block |
| `T0015` | Conflicting implementation: two impls of the same aspect for the same type, or a positive and negative impl for the same concrete type | both impl spans |

---

## 7. Alternatives Considered

### Global overlap check without orphan rule

Allow impls anywhere but reject programs where two impls overlap. This permits
cross-module impls but makes coherence a whole-program property: adding a module can
break an unrelated module. Rejected — the orphan rule gives the same safety with
local, predictable errors.

### Last-impl-wins

Define dispatch as the last-registered impl wins by module topological order.
Rejected — order-dependent semantics are a footgun and contradict Metel's design
preference for no hidden behaviour.

### Open-world assumption

Under open-world semantics, absence of an impl does not prove non-implementation.
Negative bounds (`T: !Aspect`) would require explicit negative impl declarations for
every type the programmer wants to exclude. Rejected — the closed-world assumption is
consistent with Metel's module system (all code is visible at compilation) and makes
negative bounds ergonomic: types without impls are provably absent.

### Specialisation

Allowing a more-specific impl to override a more general one — for example, a
concrete `impl Aspect for i64` silently winning over a blanket `impl<T> Aspect for T`
— is rejected. Overlapping impls are always a coherence error. Programmers who need
different behaviour for specific types use negative bounds to make impls disjoint
rather than relying on resolution order. Rust's decade-long failed attempt to
stabilise specialisation demonstrates the soundness complexity this introduces;
Metel avoids it entirely by making overlap unconditionally illegal.

---

## 8. Unresolved Questions

1. **Coherence across packages.** Coherence is scoped to the single program's module
   graph. A future package system will need a coherence model for separately compiled
   packages; this RFC does not address that. Deferred to the package system design.

2. **Auto-impl declaration syntax.** The surface syntax by which an aspect definition
   declares itself as auto-impl is deferred to RFC-0012.

---

## References

- RFC-0036 (Conditional Impl Blocks) — conditional impls interact with overlap
  detection; this RFC's first cut defers parameterised non-overlap to remain
  compatible.
- RFC-0061 (Structural Aspect Bounds) — structural type constructors are owned by
  `std::core` and follow the orphan rule.
- RFC-0072 (Negative Bounds) — `T: !Aspect` bounds discharged via CWA (§3).
- RFC-0080 (Stdlib Aspects) — `Send`/`Sync` auto-impl rules; depend on §4.
- RFC-0081 (Negative Impls) — negative impl priority over blanket impls; depend on §5.
- RFC-0097 (Orphan Rule for Bare-Parameter Blanket Impls, draft) — formalizes §1 for
  the `impl<T: Bound> Aspect for T` case this RFC's own §3/§5 examples already use.
