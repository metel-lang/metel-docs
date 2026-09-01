---
id: rfc-0153
title: "Closure Mutation Axis"
date: '2026-08-30'
status: under-review
target: v0.13.0
updated: '2026-09-01'
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
> - **Timing — v0.13.0** (#902, milestone moved from v0.17.0 on 2026-08-31 at the language
>   owner's direction). The whole RFC lands with the rest of the closure-model cluster —
>   the `call_mutation` field, the `mut` qualifier, the §3 exclusive-access rule, and
>   §1a's write-back — so the closure model ships **complete**, with no known
>   `FnMut`-shaped hole. `call_mutation` co-lands with RFC-0134's two fields, giving
>   `Type::Fun` its three multiplicity fields in one go rather than a v0.13.0→later
>   representational change. Sequenced after RFC-0134 / RFC-0152 and on the same
>   `--edition` gate as RFC-0157's D5 (the RFC-0006 capture-model change). **Still
>   `1-under-review`:** for v0.13.0 it needs review → accepted, and Open Question 1
>   (qualifier spelling) has to close.

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

> **Adversarial-review fixes, 2026-09-01.** From a cross-RFC review of the v0.13.0 closure
> cluster:
> - **§3's "a `mutating` closure is not `Copy`" is withdrawn** — it contradicted RFC-0134
>   §1 and was too strong. `use_multiplicity` stays exactly RFC-0134 §1 (Copy iff every
>   capture is Copy); `call_mutation` is fully independent. All 2×2×2 field combinations
>   are well-formed (§4). `&T` is `Copy`, `&var T` is not.
> - **§3's "`&var self`" is now a place rule**, not a metaphor: a `mutating` call
>   consumes-and-rebinds the closure binding, reusing RFC-0134 §2's `once`-call machinery.
> - **§1a gains a storage model** (one environment cell owned by the closure value, moves
>   with it) and an **early-exit rule** (in-place, non-transactional; panic/`?`/`Signal`
>   leaves partial mutation visible, closure not poisoned).
> - `.clone()` on a closure is a non-goal (closures are outside the aspect system).

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
- **`mutating` closure:** its owned (by-value) captures live in **one mutable environment
  cell held by the closure value itself** — not re-snapshotted per call. Each call
  operates on that cell in place, so mutation *persists across calls*. The closure holds
  private mutable state: a returnable counter / accumulator / memoizer, Rust's `move ||` +
  `FnMut`. Captures held by `&var` reference already persist (through the outer cell);
  this makes the *owned* captures behave the same way.
  - **Storage and movement.** The environment cell is part of the closure value and moves
    with it — assigning the closure to a new binding, passing it by value, or returning it
    (`make_counter`) transfers ownership of the cell; the write-back target travels with
    the closure and stays valid. It is not shared: there is at most one live owner (§3).
    Copying the closure value (only possible when its `use_multiplicity` is `many` — see
    §3) copies the cell, and the copies then diverge, exactly as copying any struct with a
    counter field would.
  - **Early exit.** Write-back is **in place, not transactional.** If a call exits
    normally the cell holds the body's final state. If a call exits via `panic`, a
    propagated error (`?`), or any non-normal `Signal`, the mutations that ran are visible
    in the cell and the closure is **not poisoned** — it remains callable, in a
    valid-but-partial state, exactly as a `&var self` method that panicked mid-mutation
    leaves its receiver. Callers that need atomicity guard it themselves; this RFC does
    not add rollback.
- This is a change to RFC-0006 (`4-implemented`), edition-gated exactly like RFC-0157's
  D5 change to the capture default. Behind the old edition, `mut` is not a keyword in
  function-type position and a mutating body under an implicit by-value capture is the
  existing "cannot mutate a copy" error; behind the new edition it has the semantics
  above.

§3's exclusive-access rule is what keeps this sound: a `mutating` call holds the closure
exclusively for its duration, so no two calls — including reentrant ones — are ever
mid-mutation on the same cell at once.

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

- **Exclusive access during a call — stated as a place rule, not a metaphor.** A
  `mutating` call **consumes-and-rebinds the closure binding at the call expression**:
  the same callee-place consumption RFC-0134 §2 specifies for a `once` call, except the
  closure is immediately rebound with its updated environment instead of ending. This
  holds for *any* `use_multiplicity`. Consequences: two `mutating` calls on the same
  closure cannot overlap; a reentrant call reached from within the first call's dynamic
  extent is rejected as use of a consumed place (the same rule and diagnostic as
  RFC-0134's reentrant `once` call); no `&` to the closure may be live across a call; and
  a `mutating` closure held only behind a shared `&` cannot be called at all.
  - **On `self`.** Metel closures have no written `self`, so "`&var self`" was only ever
    shorthand. The mechanism is the place-consumption above, which the move checker
    already implements for `once` — this RFC reuses it, it does not add a receiver-kind
    concept for callables.
- **`use_multiplicity` is unchanged by this axis.** A closure's `Copy`-ness is exactly
  RFC-0134 §1 — `many` iff every capture is `Copy` — and `call_mutation` does **not**
  override it. The earlier "a `mutating` closure is not `Copy`" rule is **withdrawn**: it
  was too strong. A `[n] mut () -> i64 { n := n + 1; n }` closure with `n: i64` captures
  only a `Copy` value, so it is `Copy`, and that is sound — each copy carries its own
  independent counter cell, which is what `Copy` means. The soundness concern the old
  rule was reaching for (two owners mutating *the same* backing) only arises for a
  non-`Copy` capture, and such a closure is already non-`Copy` by §1. `&var T` and `&T`:
  `&T` is `Copy`, `&var T` is **not** (mirroring `&`/`&mut`), so a `[&var x]` capture
  makes the closure non-`Copy` through §1 with no special case — see RFC-0134 §1's note.
- **Widening `reading` → `mutating` slot (RFC-0152) is type-level only.** A `reading`
  value passed to a `mut (T) -> U` parameter keeps its actual runtime behavior; the slot
  type only bounds how the callee may use it. Widening happens only at first-order
  by-value / owned positions (argument, return, ascription, struct-field init), so the
  callee always has the value by value or `&var` and can call it under the same
  place-consumption rule with no penalty and no latent capability tracking. The reverse —
  a `mutating` value into a `reading` slot — is rejected.

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

**No cross-axis well-formedness constraint.** `call_multiplicity`, `use_multiplicity`
(RFC-0134 §1), and `call_mutation` are fully independent — every one of the eight
combinations (2×2×2) is a well-formed `Type::Fun`. In particular a `Copy` (`use = many`)
closure may be `mutating`, and a `mutating` closure may be `many` or `once` on the call
axis. Each field is computed from the closure at its creation site by the rule for that
axis; none gates another.

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
    assert(c() == 2);   // state lives inside `c`'s environment cell
    // `c` is `many mut`. Here `n: i64` is Copy, so `c` is also Copy (§3, RFC-0134 §1):
    // `let mut d := c;` gives an independent counter. Calls still can't overlap.
}
```

A closure that captures a *non-`Copy`* value by value (`[buf] mut (e) -> () { buf.push(e); }`)
is non-`Copy` by RFC-0134 §1 — so there is exactly one owner and the "two owners mutate
the same backing" case cannot arise.

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
- Capture-list syntax (`&var` / bare specifiers) — RFC-0050, a separate document, but
  sequenced into the same v0.13.0 closure-model cluster.
- `Drop`-for-closures / unconsumed-closure cleanup — RFC-0134 §5 rules it out and
  this RFC does not reopen it.
- Multiplicity for ordinary types — RFC-0135.
- **`.clone()` / `.share()` on a closure value** — closures are outside the aspect system
  (RFC-0134's Open-Questions finding: `InferType::Fun` implements nothing; RFC-0158 does
  not change that), so a closure has no `Clone` or `Share` impl and `c.clone()` does not
  type-check. The only way to duplicate a `Copy` (`use = many`) closure is ordinary
  by-value copy, which copies the environment cell (§1a). A non-`Copy` closure — every
  `mutating` closure over a non-`Copy` capture — cannot be duplicated at all, which is
  the property the withdrawn "not `Copy`" rule was reaching for, now obtained from
  RFC-0134 §1 instead.

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
5. **Timing. ✓ v0.13.0** (2026-08-31, #902 moved from v0.17.0). Whole RFC lands with
   RFC-0134 / RFC-0152 and the closure-model cluster; `call_mutation` co-lands with
   RFC-0134's two `Type::Fun` fields. On the same `--edition` gate as RFC-0157's D5.
   What this needs to hold v0.13.0: review → accepted, and Open Question 1 closed.

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
makes the axis worth having. Milestone moved to v0.13.0 (#902) so the closure model ships
complete; lands whole, with RFC-0134 / RFC-0152. Needs review → accepted and Open
Question 1 (qualifier spelling) closed to hold v0.13.0. Other open points: `Send`/`Sync`
ownership, `&var`-capture-without-write precision.)*
**Target:** v0.13.0 (#902).
