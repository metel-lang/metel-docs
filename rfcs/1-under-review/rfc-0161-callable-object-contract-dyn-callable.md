---
id: rfc-0161
title: "Callable Object Contract (dyn Callable)"
date: '2026-09-01'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/923'
updated: '2026-09-22'
---

> **Status — under review (2026-09-01).** Extracted from the v0.13.0 closure cluster during the third adversarial review; dyn Callable deferred to its own RFC (v0.13.1) rather than shipping a normative default resting on unbuilt RFC-0096/0061 machinery.

> **Revised 2026-09-22 — receiver derivation closed, one open question dissolved, delivery phased.** Three changes:
>
> 1. **The by-value receiver split (open question 7) is now exact, not approximate.** RFC-0169 (Mutable-By-Value Receivers and Parameters, `1-under-review`, opened as this RFC's dependency) adds `var self` alongside `self`. A user-authored `Callable` impl now spells "once, reading" as `self` and "once, mutating" as `var self`, the same written distinction `&self` / `&var self` already give the *many* case — no receiver-derivation choice (the former options A/B/C) remains to make.
> 2. **Open question 3 (`dyn Callable` + multiple non-auto aspects) dissolves.** RFC-0008 §9 already permits `dyn Principal + Marker1 + Marker2 + …` for any zero-method marker aspect, not a closed set — `CallMany` / `CallShared` compose under that existing rule with no special-casing.
> 3. **Delivery is phased**, separating what needs no unbuilt dependency (§1–§3, the aspect, synthesized and user impls, bounds) from what needs the RFC-0008 amendment (`dyn Callable` itself, §4–§5). RFC-0096 is no longer a hard dependency of the useful core — only of eventually re-expressing the marker-derivation algorithm in its general terms, an implementation-quality improvement, not a blocker. See "Phased delivery" below.
>
> RFC-0151 (`Args` as a numeric-label row) is deferred to a later revision of this RFC's `Args` plumbing (open question 4); Phase A uses ordinary tuple types, which read as the same row once RFC-0151 exists (source-compatible).

## Summary

Define the object-safe form of a closure — `dyn Callable<Args, Ret>` — for the flat
three-field `Type::Fun` closure model that RFC-0134 / RFC-0152 / RFC-0050 / RFC-0153 ship
at v0.13.0. This RFC is deliberately **not** part of that cluster: the v0.13.0 model is
monomorphic (`Type::Fun` is a flat `(code ptr, env ptr)` with three multiplicity fields,
no vtable), and every example and stdlib signature in the cluster is first-order and
concrete. `dyn Callable` is the type-erased case.

Delivered in two phases (see "Phased delivery"):

- **Phase A** — the `Callable<Args, Ret>` aspect itself, compiler-synthesized impls for
  closures and named functions, user-authored impls on nominal types, call syntax on a
  callable object, and generic bounds with the `CallMany` / `CallShared` markers. Needs
  no unbuilt dependency.
- **Phase B** — `dyn Callable`, needing an RFC-0008 amendment (§4) admitting a consuming
  `self` / `var self` receiver on an owned aspect object.

**The `Callable` aspect itself is introduced here — not just `dyn Callable`.** The fourth
adversarial review of the v0.13.0 closure cluster (2026-09-01) confirmed `Callable<A, B>`
and its auto-impl for function types were never built (RFC-0061 §7.1 and RFC-0008 now
carry "not implemented" annotations pointing here). So at **v0.13.0 there is no
predeclared / stdlib `Callable` aspect**: a closure is only ever a concrete `Type::Fun`, a
generic parameter cannot be bounded `where F: Callable<…>` against a standard aspect (a
higher-order function takes a concrete function type — how the stdlib combinators already
work), and abstracting over "any callable representation" is not expressible. `Callable`
is not reserved in v0.13.0, and the `dyn <Aspect>` *syntax* is unchanged (RFC-0008) —
`dyn Callable<…>` just resolves to an unknown aspect (`T0003`) unless the program declares
one itself. This RFC introduces the real aspect from Phase A's target release, at which
point any user-defined `Callable` collides and must be renamed.

## Motivation

The flat `Type::Fun` model is fast and static, but it cannot express "some callable of
this shape, chosen at runtime" — a heterogeneous `List<dyn Callable<(), ()>>` of
callbacks, a struct field holding one of several handlers, a plugin boundary. Nor can a
library name and reuse a stateful callable object, decorate one, or retain its concrete
`Copy` capability through a generic API. Rust solves these cases with `Fn` / `FnMut` /
`FnOnce` implementations on concrete closure types, generic bounds over those traits,
and `dyn Fn*` as an opt-in erased form. Metel wants the same split (RFC-0153's
"recommended synthesis"): keep `Type::Fun` flat as the default, expose an aspect view
for generic and erased cases.

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

```metel
aspect Callable<Args, Ret> {
    fun call(...) -> Ret;
}
```

`Args` is a tuple type in Phase A (`Callable<(i64, i64), i64>`); RFC-0151, once it
exists, lets `Args` be spelled as the same numeric-label row `call`'s parameter list
already reads as (open question 4).

**Coherence: at most one `Callable` impl per type.** A closure or named function has
exactly one call signature today, and the marker derivation below (§2) reads the single
impl's declared receiver. A type with two different `Callable<A₁, R₁>` /
`Callable<A₂, R₂>` impls would make `F: CallMany` ambiguous — which impl's markers? This
RFC does not admit that case; a type overloading its call signature is future work (for
example, marker-parameterized `CallMany<A, R>`), not part of this RFC.

#### Closure environments are callable objects

Every closure literal has a distinct, compiler-generated environment aggregate. Its
owned captures are fields in capture-list order; a shared or exclusive capture is a
reference field; and a mutating closure has its `in_call` guard in that aggregate. The
compiler synthesizes a `Callable<Args, Ret>` implementation whose `call` body is the
closure body. Consequently, the closure's concrete `Copy` capability follows from the
environment fields and dropping the closure drops the owned capture fields in their
declared order.

This is a **semantic lowering model**, not a commitment to expose an anonymous generated
type or to change the v0.13.0 inline closure-value representation. A program cannot name
the generated environment type, depend on its field names, or use capture-list order as
a public layout API. Those remain closure implementation details, so changing a closure's
capture list does not become a source-compatibility break.

#### User-authored callable objects

`Callable` is an open standard aspect from Phase A's target release. A program may
implement it for a nominal type it may legally extend, subject to the ordinary coherence
and orphan rules (and the one-impl-per-type rule above). The type then participates in
call syntax and in generic callable bounds just as a compiler-generated closure
environment does:

```metel
struct Offset {
    amount: i64,
}

extend Offset: Callable<(i64,), i64> {
    fun call(&self, x: i64) -> i64 {
        x + self.amount
    }
}

fun apply_twice<F>(f: F, x: i64) -> i64
where F: Callable<(i64,), i64> + CallMany {
    f(f(x))
}
```

This provides named stateful callbacks, factories returning a concrete callable type,
and wrappers such as logging, retry, caching, validation, or tracing decorators. The
generic `F` preserves the callable's actual type and capabilities; it is deliberately
different from a bare function type or `dyn Callable`, both of which erase information.
For example, a `Logged<F>` struct can store `inner: F`, implement `Callable` by
delegation, and retain `F: Copy` when its own fields permit it.

`Copy` is unchanged: a type's `Callable`-related markers (§2) are independent of whether
it is `Copy`, exactly as for a closure — a `dyn Callable`'s fat-pointer representation is
never `Copy` regardless (§3), but a *concrete* user-authored callable type follows the
ordinary rule, `Copy` iff every field is.

### 2. Receiver kind and markers are derived from the written receiver, exactly

RFC-0169 gives Metel a fourth receiver form, `var self`, alongside `self`, `&self`, and
`&var self`. A `Callable` impl's declared receiver now maps onto `call_multiplicity` /
`call_mutation` exactly as the closure axes already do — no inference, no approximation:

| receiver | `call_multiplicity` | `call_mutation` | markers | Rust analogue |
|---|---|---|---|---|
| `&self` | `many` | `reading` | `CallMany` + `CallShared` | `Fn` |
| `&var self` | `many` | `mutating` | `CallMany` | `FnMut` |
| `self` | `once` | `reading` | *(none)* | `FnOnce` |
| `var self` | `once` | `mutating` | *(none)* | `FnOnce` that mutates first |

A user impl's receiver **is** its marker declaration — there is no separate marker
syntax and no way to claim a marker inconsistent with the receiver, because the
markers are read off the receiver mechanically, not asserted independently. This
replaces the former open question 7 (whether the receiver alone derives the markers, or
whether an impl writes refinements) — the receiver alone does, now that `self` and `var
self` are both spellable.

**`CallShared` present without `CallMany` never occurs.** Both `once` rows carry no
markers regardless of `call_mutation`, so `call_mutation` is not independently visible
for a `once` callable — reading a once value and mutating it in place before consuming
it are equally invisible to a caller, who owns the value and calls it exactly once
either way. `CallShared`'s definition (present iff `call_mutation` is `reading`) is
still stated for the `many` row, where it matters, and is simply never asserted for the
`once` row — not because a fifth marker state is forbidden, but because no reading of
the axes ever produces it.

### 3. Marker aspects and widening

Two orthogonal markers record the axis values on the erased type:

- **`CallMany`** — present iff `call_multiplicity` is `many`. Absent ⟹ single-call;
  see §4.
- **`CallShared`** — present iff `call_multiplicity` is `many` and `call_mutation` is
  `reading`. Absent ⟹ `call` takes `&var self` when `CallMany` is present, or consumes
  the value (`self` / `var self`) when it is not.

`Copy` is the existing value aspect, present iff every capture (or field, for a
user-authored type) is `Copy`; unchanged, and — see §1 — independent of these two.

Polarity is fixed so **present = more permissive** uniformly (hence `CallShared`, not
`CallMun`). Widening is then **capability subset**: a slot of type `dyn Callable<A, R> +
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

**`CallMany` / `CallShared` compose under RFC-0008 §9 as ordinary marker aspects — no
new grammar.** RFC-0008 §9 already permits `dyn Principal + Marker1 + Marker2 + …` for
any zero-method aspect (the same mechanism `dyn Display + Send` already uses). `CallMany`
and `CallShared` are exactly that: zero-method marker aspects. This is why former open
question 3 is dissolved rather than answered — there is nothing `Callable`-specific to
decide.

**`+ Copy` is never satisfiable on `dyn Callable`.** A `dyn Aspect` fat pointer is not
`Copy` at the representation level (RFC-0008 §2), regardless of what the erased concrete
value's own `Copy` status was before erasure. `dyn Callable<A, R> + Copy` is legal to
write as a bound but is vacuous — no value ever satisfies it. This dissolves the
Motivation's "a non-`Copy` closure erased to `dyn Callable` must not become duplicable"
concern structurally, rather than needing an enforcement rule: erasure to `dyn` already
drops `Copy` unconditionally.

**Marker derivation is compiler-builtin logic in Phase A, not routed through RFC-0096.**
The aspects `CallMany` and `CallShared` are real, `std::core`-predeclared, zero-method
aspects from Phase A onward — usable in bounds immediately, with no dependency on RFC-0096
(Auto-Impl Aspects, `1-under-review`). Only the *implementation* of "which closures and
which user impls get which markers" is expressed as ad hoc compiler logic until RFC-0096
exists, at which point it can be re-expressed in RFC-0096's general structural-composition
terms without changing the aspects' identity or any program's observed markers — an
internal refactor, not a breaking change. This removes RFC-0096 as a hard dependency of
this RFC's schedule.

### 4. `dyn Callable` (Phase B)

An owned `dyn Callable<A, R>` reuses RFC-0008's existing fat-pointer aspect-object
representation and RFC-0141's explicit-placement form (`@[r] dyn Callable<A, R>`)
unchanged — nothing about erasure's representation or `dyn` syntax is new here.

**The consuming call (single-call state) needs one RFC-0008 amendment.** RFC-0008's
object-safety rule 1 admits `&self` and `&var Self` receivers; a by-value `self`
receiver is not object-safe as RFC-0008 is written, because moving a value out from
behind an erased pointer needs the vtable entry to take ownership of the data pointer —
something no existing `dyn Aspect` method does. §5 proposes the amendment: **a consuming
`self` or `var self` method is object-safe on an *owned* `dyn`**, callable only there
(`&dyn` / `&var dyn` cannot call it — there is no ownership to move out of a shared or
exclusive reference). This is the resolution of the RFC's former open question 1.

With that amendment:

- **Bare `dyn Callable<A, R>`** (no `CallMany`) is owned-only, and `call` is a
  consuming method. A second call is a use-after-move error on the binding holding the
  `dyn` value — the same static guarantee a `once` closure already has, now checked on
  the erased owner rather than on a closure literal the checker can see. This resolves
  the former open question 2 without a runtime poison flag: no `Box` type exists in
  Metel, and none is needed — the owned `dyn` value itself is what gets consumed,
  exactly as an owned struct is consumed by a by-value method today.
- **`dyn Callable<A, R> + CallMany`** is repeatable through `&var dyn`; `+ CallShared`
  (which per §2/§3 never appears without `CallMany`) additionally allows `&dyn`.
- **A `mutating` closure erased behind `dyn Callable + CallMany`** (no `CallShared`)
  keeps its RFC-0153 `in_call` flag in the environment the fat pointer's data half
  points at; the vtable's `call` entry checks it exactly as the concrete call path does
  today (`R0015` on reentrancy). Nothing new is needed here: the flag already lives in
  the value, not in the call site, so erasure does not remove it. A user-authored
  callable's `&var self` impl is an ordinary exclusive borrow, unenforced beyond the
  type system until RFC-0122 (borrow checking) exists, matching every other `&var self`
  method today.

### 5. RFC-0008 amendment (proposed text, applied at RFC-0161's acceptance)

Add to RFC-0008 §3 (Object Safety — the receiver rule): a method whose receiver is
by-value `self` (or, with RFC-0169, `var self`) is object-safe **only** when the
aspect additionally guarantees no method needs to be called through a shared or
exclusive *reference* to the object — practically, only for an aspect (such as
`Callable`, bare or `+ CallMany` alone) whose consuming method is its sole
by-value-receiver method, and where the `dyn` value in question is used only in owned
position. The vtable entry for such a method takes ownership of the data pointer instead
of borrowing it; calling it drops the vtable half of the fat pointer and hands the data
half, plus its size/alignment/drop metadata (already present per RFC-0008 §2), to the
callee. `&dyn Aspect` and `&var dyn Aspect` continue to reject a consuming method exactly
as they reject one today — this amendment only widens what an *owned* `dyn` may call.

This is scoped narrowly (owned `dyn` only, consuming methods only) rather than a general
relaxation of by-value-`self` object-safety, to avoid reopening RFC-0008's broader
receiver-rule design.

### 6. Relationship to the v0.13.0 cluster and to RFC-0169

- **RFC-0134 / RFC-0153** — the field values on `Type::Fun` decide which markers the
  `dyn` form carries. Both are computed from the same body analysis and kept in
  agreement. Nothing in this RFC changes the flat representation or its checking.
- **RFC-0152** — first-order widening among concrete `Type::Fun` values is unchanged.
  This RFC's subset rule is the erased-case analogue, not a replacement.
- **RFC-0169 (Mutable-By-Value Receivers and Parameters, `1-under-review`)** — supplies
  `var self`, without which §2's exact receiver-to-marker mapping is not expressible.
  This RFC's Phase A is blocked on RFC-0169 reaching at least the same review depth (its
  own open questions — closure parameters, a `var`-unused lint, pattern-destructured
  `var` params — do not block this RFC, since only the plain-`self` case is used here).
- **RFC-0096 (Auto-Impl Aspects)** — no longer a scheduling dependency (§3); remains the
  eventual general framework the marker-derivation algorithm is re-expressed in.
- **RFC-0061 §7.1 / metel-core#893** — the original `Callable<A, B>` reservation. This
  RFC is its concrete design.
- **RFC-0008 (Aspect Objects)** — object-safety of `Callable::call`; §5 proposes its
  amendment, needed only for Phase B.

## Phased delivery

- **Phase A** (§1–§3): the `Callable` aspect, synthesized impls for closures and
  functions, user-authored impls, call syntax, and `CallMany` / `CallShared` bounds.
  Depends only on RFC-0169 reaching a review depth sufficient to rely on `var self`.
  No RFC-0096 or RFC-0151 dependency.
- **Phase B** (§4–§5): `dyn Callable`, gated on the RFC-0008 amendment (§5) being
  accepted alongside or after this RFC.

Scheduling for each phase is the tracking issue's milestone, not this document (per
`rfcs/PROCESS.md`, "Roadmap and scheduling" — GitHub milestones are the single source
of truth). metel-core#923 currently carries **no milestone**: a strategic call
(2026-09-22) to keep the v0.13.1–v0.17.0 line on ownership-finalization and
row-polymorphism, not general aspect/closure completeness (see `GAP-FUNCTIONS-002`).
This RFC's design work continues regardless; a milestone, split per phase, is set once
a release adopts it.

## Non-Goals

- **Any change to the flat `Type::Fun` model or the v0.13.0 cluster.** This RFC is
  purely additive and strictly later.
- **Higher-order variance for erased callables** — RFC-0155's scope, unchanged.
- **Direct access to a compiler-generated closure environment type.** User-authored
  callable structs are public nominal types; anonymous closure environments remain
  opaque.
- **A `Copy` marker on `dyn Callable`.** Structurally excluded (§3), not merely unlisted.
- **A general receiver-refinement syntax for `Callable` impls.** §2's mapping is total
  and mechanical; there is no case that needs a declared marker independent of the
  receiver.
- **`dyn Callable` before the RFC-0008 amendment lands** — Phase B is gated on §5, not
  shipped speculatively.
- **Automatically solving recursive closures, heterogeneous collections without `dyn`,
  or borrow/lifetime safety.** Recursive callable objects still need finite indirection;
  heterogeneous collections need an enum or `dyn Callable`; reference captures remain
  governed by RFC-0122 and the ownership rules.

## Open Questions

1. ~~By-value `self` object-safety~~ — resolved: §5 proposes the amendment (owned-`dyn`,
   consuming-method carve-out).
2. ~~Erased single-call mechanics~~ — resolved: static, via the consuming call on the
   owned `dyn` binding (§4); no poison flag, no `Box` (Metel has none).
3. ~~`dyn Callable` + multiple non-auto aspects~~ — dissolved: RFC-0008 §9 already
   permits it for any zero-method marker aspect (§3).
4. **`Args` row plumbing** — RFC-0151's numeric-label row applied to `call`'s parameter
   list; Phase A uses a plain tuple type instead (§1). Confirm the eventual row form
   preserves arity and per-parameter reference qualifiers, and that the tuple spelling
   is source-compatible with it.
5. ~~Erased `mutating`-call exclusivity~~ — resolved: the existing RFC-0153 `in_call`
   flag on the closure's own environment is reused unchanged (§4); a user-authored
   `&var self` impl gets no new runtime check, matching every other `&var self` method
   until RFC-0122 (unchanged answer, restated for clarity).
6. ~~User-authored marker derivation~~ — resolved: the receiver alone, exactly (§2), now
   that RFC-0169 makes `self` / `var self` both spellable.
7. **Coherence: one `Callable` impl per type.** §1 states this as this RFC's rule (no
   overloaded call signatures). Confirm this is acceptable long-term, or whether a
   future marker-parameterized form (`CallMany<A, R>`, allowing several signatures) is
   wanted from the start.
8. **Per-phase tracking.** Whether metel-core#923 splits into two tracking issues (one
   per phase) or stays one issue with phase sub-tasks, and each phase's milestone —
   scheduling questions for the tracking issue, not this document (see "Phased
   delivery").

## References

- **RFC-0134 (Closure Call Capability)** — the flat model and `call_multiplicity`;
  its Open Questions name `Callable` / `dyn Callable` as unbuilt.
- **RFC-0153 (Closure Mutation Axis)** — carried the interim `dyn` erasure default now
  moved here; §3's exclusive-borrow rule the erased `mutating` case preserves unchanged.
- **RFC-0152 (Function-Type Multiplicity Widening)** — the first-order widening this
  RFC's subset rule mirrors for the erased case.
- **RFC-0050 (Closure Capture Lists)** — capture classification feeding the markers.
- **RFC-0169 (Mutable-By-Value Receivers and Parameters, `1-under-review`,
  metel-core#1245)** — supplies `var self`, the dependency this revision's §2 relies on;
  split out of this RFC's own design discussion as a general surface feature.
- **RFC-0008 (Aspect Objects)** — object-safety rules; §5 proposes its amendment.
- **RFC-0096 (Auto-Impl Aspects)** — the eventual general form of the marker-derivation
  algorithm; no longer a scheduling dependency (§3).
- **RFC-0061 §7.1 / metel-core#893** — the original `Callable<A, B>` reservation.
- **RFC-0151 (Numeric-Label Rows)** — `Args`, deferred to a later revision (open
  question 4).
- **RFC-0141 (Aspect Objects: Explicit Allocator Placement)** — `@[r] dyn Callable`
  composes with §4's consuming call unchanged, since it moves out of the region the
  same way an ordinary owned `dyn` moves out of implicit placement.
- **RFC-0163 (Function-Type Use-Multiplicity Surface)** — bare function types erase a
  callable's concrete use multiplicity; generic `F: Callable<…> + Copy` is the later
  capability-preserving alternative.

---

## Decision

**Outcome:** *(pending — `1-under-review`. Opened 2026-09-01, extracted from the v0.13.0
closure cluster so `dyn Callable` is not a normative forward reference resting on unbuilt
machinery. Revised 2026-09-22: receiver derivation closed by RFC-0169, delivery phased,
RFC-0096 no longer a hard dependency, one open question dissolved. Remaining open
questions (7, 8 above) are scheduling and coherence-scope choices, not design gaps in
the mechanism; §4's Args plumbing (4) is deferred to a later revision by design. Phase A
could reach acceptance once RFC-0169 does; Phase B needs its RFC-0008 amendment (§5)
accepted alongside it.)*
