---
id: rfc-0153
title: "Closure Mutation Axis"
date: '2026-08-30'
status: under-review
target: v0.13.1
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/902'
---

> **Amendment, 2026-08-31 — folded into the closure-model work; scope widened to the
> case that makes the axis worth having.** Three changes, all consequences of decisions
> taken this cycle on RFC-0134 / RFC-0050 / RFC-0157:
>
> - **`reading` is a fixed default, not inferred** — matching RFC-0134's 2026-08-31
>   amendment (`many` default, `once` written). `mutating` is always written (`mut`); the
>   body analysis below runs to *verify* it — a `reading`/unqualified closure whose body
>   mutates a capture is a compile error at the definition site ("mutates captured `x`;
>   annotate `mut …` or don't mutate it"). §1's "inferred" language should be read that way.
> - **Two cases, not one.** *(a)* Mutating **outer** state through a `&var`-captured
>   reference (`[&var count] mut () -> () { count += 1 }`) — persists today, because the
>   captured reference survives RFC-0006's per-call environment re-clone; this RFC only
>   adds the no-overlapping-calls rule. *(b)* Mutating a **by-value / owned** capture so
>   the mutation persists across calls — the returnable counter / accumulator / memoizer,
>   Rust's `move ||` + `FnMut`. That is the expressiveness gap the closure model otherwise
>   leaves open (see RFC-0134 §5's "no mechanism for retaining private mutated state").
> - **Non-Goal #1 is reversed for case (b).** A `mutating` closure's by-value captures are
>   **written back** into its environment instead of re-cloned-and-discarded per call.
>   This is a change to RFC-0006's runtime capture model, the same weight and the same
>   `--edition` gate as RFC-0157's D5; a `reading` closure keeps today's clone semantics
>   (nothing mutates, so the difference is unobservable). Scoped this way, `mutating` stops
>   being a type-level fact with no runtime effect.
> - **Timing.** This amendment **recommends pulling the RFC forward to v0.13.1** (from its
>   current v0.17.0 milestone, #902), landing whole — the `call_mutation` field, the `mut`
>   qualifier, the §3 exclusive-access rule, and §1a's write-back — right after RFC-0134,
>   RFC-0152, and the RFC-0006/D5 edition change, so the closure model ships complete
>   rather than with a known `FnMut`-shaped hole for four minor versions. RFC-0134 §4
>   already frames adding the field as a cheap, anticipated change, so it is *not*
>   reserved in v0.13.0 — v0.13.0's `Type::Fun` stays at two fields and every function
>   type is `reading` implicitly until this lands. The milestone move itself is a
>   release-planning call; `target:` here reflects the recommendation.

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

Like RFC-0134's other axes (as amended 2026-08-31), **`reading` is a fixed default
and `mutating` is written** (`mut`); the body analysis *verifies* the declared value
rather than sourcing it. It is orthogonal to `call_multiplicity`: `many` × mutating is
`FnMut`, `once` × mutating is a closure that mutates then consumes, `many` × reading is
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

Checked at the closure's creation site, where captures and body are both available,
by the same pass RFC-0134 §2 uses — as a *verification* of the declared/default value:

- A body that assigns to a by-value capture, takes `&var` of one, or calls a
  `&var self` / `&var`-parameter method or function on one **is `mutating`**; if the
  closure was not written `mut` (or defaulted `reading`), that is a compile error, with
  the fix being to add `mut` or to stop mutating.
- A body that only reads captures (including taking `&` of them) is `reading` and needs
  no annotation.

### 1a. Runtime model — what `mutating` actually does

RFC-0006 evaluates a call as `call_env = closure.captured.clone()` and never writes the
result back, so a mutation to a by-value capture is discarded when the call returns. That
makes `mutating` on a by-value capture a type-level fact with no runtime effect — useless.
This RFC fixes that:

- **`reading` closure:** unchanged — per-call clone of the captured environment, nothing
  written back. Since the body does not mutate, this is unobservable.
- **`mutating` closure:** its by-value captures are **written back** into the closure's
  stored environment at the end of each call, so mutation *persists across calls*. The
  closure now holds private mutable state — a returnable counter / accumulator / memoizer,
  Rust's `move ||` + `FnMut`. Captures held by `&var` reference already persist (through
  the outer cell); this only adds persistence for the *owned* captures.
- This is a change to RFC-0006 (`4-implemented`), edition-gated exactly like RFC-0157's
  D5 change to the capture default. Behind the old edition, a `mut` closure is a
  parse/type error; behind the new one it has the write-back semantics above.

The exclusive-access rule in §3 is what keeps the write-back sound: a `mutating` call
takes `&var self` on the closure, so no two calls (including reentrant ones) can be
mid-write-back at once.

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

The `many` × `mutating` cell is the one the rest of the closure model cannot express
without this RFC (see RFC-0134 §5). Worked:

```metel
fun make_counter() -> mut () -> i64 {
    let mut n := 0;
    [n] mut () -> i64 { n := n + 1; n }   // `n` moved in; writes persist (§1a); closure returnable
}

fun main() {
    let mut c := make_counter();
    assert(c() == 1);
    assert(c() == 2);   // state lives inside `c`
    // `c` is `many mut` — not `Copy` (§3); no two calls overlap
}
```

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
a generic `extends Callable` parameter monomorphizes. RFC-0134's field model changes
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

- ~~Changing RFC-0006's by-value capture model.~~ **Reversed by the 2026-08-31
  amendment for the `mutating` case only** (see §1a): a `mutating` closure's by-value
  captures are written back so mutation persists across calls. A `reading` closure is
  unchanged. *How* a capture gets into the closure is still RFC-0050/RFC-0157's concern,
  not this RFC's — this RFC governs only what a `mutating` *call* does to an
  already-captured value and whether that survives the call.
- Capture-list syntax (`&var` / bare specifiers) — RFC-0050, sequenced together for
  v0.13.0 (field) / v0.13.1 (`mut` + persistence) but a separate document.
- `Drop`-for-closures / unconsumed-closure cleanup — RFC-0134 §5 rules it out and
  this RFC does not reopen it.
- Multiplicity for ordinary types — RFC-0135.

## Open Questions

1. **Qualifier spelling** (§2): `mut fun` vs `var fun` vs something else, and
   confirming order-insensitivity with `once`/`many` is actually implemented
   rather than just grammar-allowed.
2. **Interaction with higher-order variance** — a function type carrying a
   `mutation` field inside another function type's argument compounds the
   contravariant-nesting question, which is **RFC-0155** (split out of RFC-0152
   on 2026-08-30); resolve them together.
3. **`Send`/`Sync` derivation** — should this RFC also specify that a `reading`
   closure over `Send`/`Sync` captures is `Send`/`Sync` and a `mutating` one is
   not, or leave that to RFC-0096 and only provide the fact it needs?
4. **`&var`-capture without mutation.** A body that takes `&var` of a capture but
   never writes through it — `mutating` (conservative, matches the borrow) or
   `reading` (precise, matches the effect)? Leaning conservative.
5. **Timing.** The 2026-08-31 amendment recommends landing the whole RFC together at
   **v0.13.1**, after RFC-0134, RFC-0152, and the RFC-0006/D5 edition change — a
   pull-forward from the current v0.17.0 milestone (#902), so the closure model ships
   without a known `FnMut`-shaped hole. Not reserved in v0.13.0 (RFC-0134 §4 makes adding
   the field cheap later). **Open:** whether release planning takes the v0.17.0 → v0.13.1
   move, or v0.14.0 with the rest of the edition machinery.

## References

- **RFC-0134 (Closure Call Capability)** — §4 reserves this field; §5 states the
  compose-as-independent-prefix constraint this RFC's qualifier satisfies; §2's
  inference pass is the one that also computes this axis. §3a's `fun(T) -> U`
  spelling assumed.
- **RFC-0152 (Function-Type Multiplicity Widening)** — the widening relation this
  axis joins, same `reading`-permits-`mutating` direction.
- **RFC-0006 (Closure Capture Semantics), `4-implemented`** — the per-call environment
  re-clone that §1a changes for `mutating` closures (write-back), edition-gated.
- **RFC-0067a (Reference Types)** — the exclusive-`&var` rule §3's call-site
  soundness reuses.
- **RFC-0050 (Closure Capture Lists), `1-under-review` (v0.13.0)** — as amended
  2026-08-31: capture list required for non-`Copy`/by-ref captures, bare `[n]` = by-value
  move. §1a's write-back applies to exactly those bare by-value captures. Sequenced with
  this RFC.
- **RFC-0157 (Copy and Clone Model Re-analysis), `1-under-review`** — its D5 edition
  gate (change to RFC-0006's capture default) is the same gate §1a's write-back rides.
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

**Outcome:** *(pending — `1-under-review`, opened 2026-08-30, deferred from RFC-0134
§4/§5, widened 2026-08-31 to cover encapsulated persistent state (§1a) — the case that
makes the axis worth having. Targets v0.13.1 (#902), whole RFC together, after RFC-0134
and the RFC-0006/D5 edition change. Open points: qualifier spelling (`mut` vs `var fun`),
whether to own the `Send`/`Sync` consequence, `&var`-capture-without-write precision, and
confirming the v0.13.1 milestone vs. v0.14.0.)*
**Target:** v0.13.1 (#902).
