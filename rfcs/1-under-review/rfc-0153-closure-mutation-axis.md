---
id: rfc-0153
title: "Closure Mutation Axis"
date: '2026-08-30'
status: under-review
target:
updated: '2026-08-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/902'
---

> **Deferred from RFC-0134 §4/§5.** RFC-0134 models a closure's capability as
> independent per-operation multiplicity axes on `Type::Fun` — `call_multiplicity`
> (does invoking consume a capture) and `use_multiplicity` (is the value `Copy`).
> §4 reserves "a third field of the same kind, on the same rationale, whenever
> something needs it," and §5 states a forward-compatibility constraint for it
> without designing it: it must compose with `once`/`many` as an **independent,
> order-insensitive prefix**, not a fused phrase. This RFC is that third axis:
> whether calling the closure needs *exclusive* (`&var`) access to a capture,
> i.e. Rust's `FnMut`.

> **Status — under review (2026-08-30).** Deferred from RFC-0134 §4/§5: the reserved third Type::Fun axis -- whether a call needs exclusive (&var) access to a capture, i.e. FnMut.

## Summary

Add a **mutation axis** to `Type::Fun`: does invoking the closure mutate a
capture — needing `&var` access to it for the duration of the call — or only read
it? A closure whose body assigns to, or takes `&var` of, a by-value capture is
*call-mutating*; one that only reads its captures is *call-reading*.

Like RFC-0134's other axes it is **inferred from the body** by default, with an
explicit qualifier for a signature that must promise more than its current body
needs. It is orthogonal to `call_multiplicity`: `many` × mutating is `FnMut`,
`once` × mutating is a closure that mutates then consumes, `many` × reading is
the plain `Fn` case, `once` × reading consumes without mutating first.

## Motivation

RFC-0134 makes the move checker sound for *consuming* calls. It says nothing
about *mutating* calls, because RFC-0006's capture model captures by value and
RFC-0134 §2 only asks "does a call move a capture out." A call that mutates a
capture in place is invisible to that question but has its own soundness
requirements:

- Two overlapping calls to a mutating closure would alias `&var` to the same
  capture — the exact thing Metel's exclusive-reference rule forbids everywhere
  else.
- A mutating closure stored where callers expect a read-only one (a `many fun`
  callback that a data structure calls during iteration) can mutate shared state
  mid-traversal, an iterator-invalidation-shaped bug.
- `Send`/`Sync` for closures (RFC-0096 territory) depends on whether a call
  mutates: a call-reading closure over `Sync` captures is `Sync`; a call-mutating
  one is not.

None of these are expressible today because the type does not record the fact.

## Proposal

### 1. The axis

A third field on `Type::Fun`, alongside RFC-0134's two:

```
Type::Fun(params, ret, call_multiplicity, use_multiplicity, call_mutation)
```

`call_mutation` is `reading` or `mutating`. `reading` is the default and the
more-permissive value (a reading closure is usable wherever a mutating one is
asked for; RFC-0152's widening direction, unchanged).

Inferred at the closure's creation site, where captures and body are both
available, the same pass RFC-0134 §2 uses:

- A body that assigns to a by-value capture, takes `&var` of one, or calls a
  `&var self` / `&var`-parameter method or function on one → `mutating`.
- A body that only reads captures (including taking `&` of them) → `reading`.

### 2. Qualifier

An explicit qualifier for the promise case (a `native` declaration, an aspect
method signature, or a stdlib signature that must stay `mutating` regardless of
its current body), composing with `once`/`many` as an independent prefix per
RFC-0134 §5's constraint:

```
mut fun(T) -> U            // reading is the default; `mut` marks mutating
once mut fun(T) -> U       // consumes and mutates; order-insensitive with `once`
mut once fun(T) -> U       // same type
```

Spelling is Open Question 1 — `mut` reuses Metel's mutation vocabulary (`&var`,
`var` bindings) but `var fun` may read better; deciding this is part of this RFC.

### 3. Call-site soundness

- A `mutating` closure's call needs exclusive access to the closure value for the
  duration of the call — modeled as the call taking `&var self` on the closure,
  so two calls cannot overlap and a `&` to the closure cannot be live across one.
- A `mutating` closure is **not `Copy`** (`use_multiplicity` cannot be `many`):
  copying it would let two copies mutate captures independently. This is the same
  implication RFC-0134 notes for `call = once`, on the same grounds.
- Passing a `mutating` closure where a `reading` one is required is rejected;
  the reverse (a `reading` closure into a `mutating` slot) is allowed by RFC-0152.

### 4. Relationship to the 2×2 (×2)

| call | mutation | Rust analogue |
|---|---|---|
| `many` | `reading` | `Fn` |
| `many` | `mutating` | `FnMut` |
| `once` | `reading` | `FnOnce` (that doesn't mutate first) |
| `once` | `mutating` | `FnOnce` (that mutates, then consumes) |

RFC-0134 §4 makes the case for axes over a hierarchy: the four states are all
meaningful and independently reachable, so `mutation` is a separate binary field,
not a third point on the `call` axis.

## Alternatives considered

### Independent marker aspects instead of fields on `Type::Fun`

The two axes this RFC and RFC-0134 carry as fields could instead be **orthogonal
marker aspects** on a per-closure anonymous type. This is a real fork worth
recording, and it is the better shape for the *erased* case (`dyn`, RFC-0061
§7.1 / metel-core#893), so the two are complementary rather than exclusive.

The decomposition:

- **`Callable<Args, Ret>`** — the base aspect. Declares `call`. Every callable
  value implements it.
- **`CallMany`** — orthogonal marker: `call` is repeatable. Absent ⟹ call-once,
  and the checker enforces a single call (RFC-0134 §2's rule).
- **`CallShared`** — orthogonal marker: `call` needs only `&` access to captures.
  Absent ⟹ `call` takes `&var self` (this RFC's `mutating`).
- **`Copy`** — the existing value-duplication aspect. This *is* RFC-0134's `use`
  axis, already an independent marker; nothing new.

A closure literal gets a synthesized `extend`: `Callable` always, plus whichever
of `CallMany` / `CallShared` / `Copy` its body analysis licenses — the same
analysis this RFC and RFC-0134 §2 already specify, emitting impls instead of
setting fields. Four states (eight with `Copy`), each independently reachable and
*nameable*, which Rust's `Fn : FnMut : FnOnce` chain cannot do (it cannot
distinguish "mutates then consumes" from "just consumes," nor express a `&self`
closure that is nonetheless call-once).

**Widening falls out** (this is RFC-0152 dissolving into an ordinary bound). With
markers named so that **present = more permissive** — hence `CallShared`, not
`CallMut`; the reading closure is the permissive one — widening is
**capability superset**: a slot requiring marker set `M` accepts any value whose
markers `⊇ M`. No bespoke coercion rule; RFC-0152 becomes "the required bound is
a subset of the value's."

**Fit with the existing aspect machinery.** `CallMany` / `CallShared` are
structurally derived and never user-declared — the same profile as `Send` /
`Sync` / `Linear`. Making them **auto-impl aspects** (RFC-0096's closed set) is
the natural home: they ride along on `dyn Callable<A, R>` the way `Send` rides on
`dyn Aspect`, and they stay out of the coherence/orphan machinery a per-closure
`extend` block would otherwise stress.

**Why this RFC does not adopt it as the baseline.** It still needs per-closure
**anonymous types with synthesized impls** — a representational change
`Type::Fun` does not have today (RFC-0134 §1) and a coherence carve-out so those
impls never conflict. And `dyn Callable` reintroduces the vtable and boxing that
`Type::Fun`'s flat `(code ptr, env ptr)` representation deliberately avoids, while
a generic `impl Callable` parameter monomorphizes. RFC-0134's field model changes
one enum variant and two read sites (`is_copy`, the move checker) to close a
specific `--move-check` soundness hole; the marker-aspect model is the larger
"closures are structural types with capability aspects" redesign, which belongs
with metel-core#893 and metel-core#702.

**Recommended synthesis.** Keep `Type::Fun` flat with the multiplicity fields as
the **default** representation (fast, static, no vtable — RFC-0134, this RFC), and
expose `Callable<Args, Ret>` + `CallMany` / `CallShared` as an **opt-in aspect
view** for the object-safe / type-erased case. Both are computed from the same
body analysis and kept in agreement: the field values decide which markers the
`dyn` form carries. This is Rust's own split — concrete closure types with
`Fn*` impls, `dyn Fn` opt-in — and it composes with RFC-0151 (`Args` a
numeric-label row).

**Open caveats if pursued:** marker polarity/naming must be locked so "more
markers = more permissive" holds uniformly (else the superset rule needs a case
split); `Callable::call`'s receiver kind is refined by `CallShared` (`&self` when
present, `&var self` when absent), which the object-safety / vtable rules
(RFC-0008) must accept; and whether `dyn` permits multiple non-auto aspects at
all — the auto-impl route above sidesteps this but ties the markers to RFC-0096.

## Non-Goals

- Changing RFC-0006's by-value capture model. A `mutating` closure still captured
  its target by value at creation; the axis is about what the *call* does to that
  captured value, not how it got there.
- Capture-list syntax (`move`, `&var` specifiers) — RFC-0050, independently timed.
- `Drop`-for-closures / unconsumed-closure cleanup — RFC-0134 §5 rules it out and
  this RFC does not reopen it.
- Multiplicity for ordinary types — RFC-0135.

## Open Questions

1. **Qualifier spelling** (§2): `mut fun` vs `var fun` vs something else, and
   confirming order-insensitivity with `once`/`many` is actually implemented
   rather than just grammar-allowed.
2. **Interaction with RFC-0152's widening for higher-order positions** — a
   function type carrying a `mutation` field inside another function type's
   argument compounds RFC-0152 Open Question 2; resolve them together.
3. **`Send`/`Sync` derivation** — should this RFC also specify that a `reading`
   closure over `Send`/`Sync` captures is `Send`/`Sync` and a `mutating` one is
   not, or leave that to RFC-0096 and only provide the fact it needs?
4. **`&var`-capture without mutation.** A body that takes `&var` of a capture but
   never writes through it — `mutating` (conservative, matches the borrow) or
   `reading` (precise, matches the effect)? Leaning conservative.
5. **Timing.** After RFC-0134 and RFC-0152, or can it land with RFC-0134 as a
   third field from the start? RFC-0134 §4 reserves the field either way.

## References

- **RFC-0134 (Closure Call Capability)** — §4 reserves this field; §5 states the
  compose-as-independent-prefix constraint this RFC's qualifier satisfies; §2's
  inference pass is the one that also computes this axis. §3a's `fun(T) -> U`
  spelling assumed.
- **RFC-0152 (Function-Type Multiplicity Widening)** — the widening relation this
  axis joins, same `reading`-permits-`mutating` direction.
- **RFC-0006 (Closure Capture Semantics)** — the by-value capture model this does
  not change.
- **RFC-0067a (Reference Types)** — the exclusive-`&var` rule §3's call-site
  soundness reuses.
- **RFC-0050 (Closure Capture Lists)** — capture syntax, independently timed.
- **RFC-0096 (Auto-Impl Aspects)** — `Send`/`Sync`/`Linear`; Open Question 3, and
  the natural home for `CallMany` / `CallShared` in the Alternatives section.
- **RFC-0135 (Multiplicity for Ordinary Types)** — the axis vocabulary applied
  beyond closures.
- **RFC-0061 §7.1 / metel-core#893** — the `Callable<A, B>` aspect for function
  types and `dyn Callable`; the Alternatives section's marker-aspect decomposition
  is a direct input to it.
- **RFC-0008 (Aspect Objects)** — `dyn Aspect`; the Alternatives section's
  `dyn Callable + CallMany` composition and the `CallShared`-refined receiver kind
  depend on its object-safety rules.

---

## Decision

**Outcome:** *(pending — draft, opened 2026-08-30, deferred from RFC-0134 §4/§5.
The axis and its inference mirror RFC-0134's `call_multiplicity`; open points are
the qualifier spelling, whether to also own the `Send`/`Sync` consequence, and
whether it lands with RFC-0134 or after it and RFC-0152.)*
**Target:** *(set when accepted; after or with RFC-0134.)*
