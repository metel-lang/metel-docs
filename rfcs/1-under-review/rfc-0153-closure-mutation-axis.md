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
>   This is a change to RFC-0006's runtime capture model, the same weight as RFC-0157's D5
>   and landing with it as one hard change (no edition gate — Metel has no public users);
>   a `reading` closure keeps today's clone semantics (nothing mutates, so the difference
>   is unobservable). Scoped this way, `mutating` stops being a type-level fact with no
>   runtime effect.
> - **Timing — v0.13.0** (#902, milestone moved from v0.17.0 on 2026-08-31 at the language
>   owner's direction). The whole RFC lands with the rest of the closure-model cluster —
>   the `call_mutation` field, the `mut` qualifier, the §3 exclusive-access rule, and
>   §1a's write-back — so the closure model ships **complete**, with no known
>   `FnMut`-shaped hole. `call_mutation` co-lands with RFC-0134's two fields, giving
>   `Type::Fun` its three multiplicity fields in one go rather than a v0.13.0→later
>   representational change. Sequenced after RFC-0134 / RFC-0152 and landing with
>   RFC-0157's D5 (the RFC-0006 capture-model change) as one hard change — **no edition
>   gate** (see RFC-0050's "Migration (no edition gate)"). **Still `1-under-review`:** for
>   v0.13.0 it needs review → accepted, and Open Question 1 (qualifier spelling) has to close.

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

> **Adversarial-review fixes, 2026-09-01** (two passes, cross-RFC review of the v0.13.0
> cluster):
> - **§3's "a `mutating` closure is not `Copy`" is withdrawn** — it contradicted RFC-0134
>   §1 and was too strong. `use_multiplicity` stays exactly RFC-0134 §1 (Copy iff every
>   capture is Copy); `call_mutation` is fully independent. All 2×2×2 field combinations
>   are well-formed (§4). `&T` is `Copy`, `&var T` is not.
> - **§3 is now a precise place rule** (pass 2 corrected pass 1's over-reach): a `mutating`
>   call is an **exclusive borrow of the callee place for the call's duration**, `&var
>   self`-shaped — it does **not** consume the closure. The callee must be an lvalue place
>   (binding or a projection off one via exclusive access); a temporary (`make_counter()()`)
>   or a shared-`&` callee is a compile error. `once mut` composes the axes independently —
>   the `once` axis consumes at the call expression, the `mut` borrow is then moot.
> - **§1a's early-exit rule** split by axis: plain `mut` + panic → callable, partial
>   mutation visible; `once`/`once mut` + panic → moved value (RFC-0134 §2), no
>   "still callable" question.
> - **§1a storage model** unchanged: one environment cell owned by the closure value,
>   moves with it, copied for a `Copy` closure.
> - **§3 gains an interim `Send`/`Sync` rule** (`mutating` ⇒ not `Sync`; `Send` follows
>   captures) and a **`dyn` erasure default** (bare `dyn Callable` = most-restrictive;
>   `+ CallMany`/`+ CallShared`/`+ Copy` widen).
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
  - **Early exit.** Write-back is **in place, not transactional.** The distinction is
    which axis governs:
    - **Plain `mut` (not `once`):** the call does not consume the closure (§3). If the
      body exits via `panic` / a propagated error (`?`) / any non-normal `Signal`, the
      mutations that ran are visible in the cell, the exclusive borrow ends with the
      unwind, and the closure remains **callable in a valid-but-partial state** — exactly
      as a `&var self` method that panicked mid-mutation leaves its receiver. No rollback.
    - **`once` or `once mut`:** the `once` axis consumed the callee place *at the call
      expression*, before the body ran (RFC-0134 §2). So the closure is a moved value
      whether the body returned normally or panicked, and a later use is the ordinary
      moved-value error. There is no "still callable after panic" question — `once`
      already answered it. The environment cell may hold a partial or moved-out state;
      that is unobservable precisely because the closure cannot be called again. (If the
      panic is caught, the moved-out *outer* bindings the `once` call consumed are
      handled by RFC-0134 §2's existing rules, unchanged.)
- This is a change to RFC-0006 (`4-implemented`), landing with RFC-0157's D5 change to the
  capture default as **one hard change** at v0.13.0 — **no edition gate**: Metel has no
  public users, so the `mut` keyword, the write-back semantics, and the fixture corpus all
  move together (see RFC-0050's "Migration (no edition gate)").

§3's exclusive-borrow rule is what keeps the write-back sound: for a plain `mut` closure
the place is exclusively borrowed for each call's duration, so no two calls — reentrant
included — are ever mid-mutation on the same cell at once; for `once mut` the `once`
consumption makes a second call impossible outright.

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

- **A `mutating` call is an exclusive borrow of the callee place for the call's
  duration.** Stated precisely (this replaces the earlier "consumes-and-rebinds"
  wording, which over-reached):

  1. **The callee must be an lvalue place** — a binding, or a projection off one
     (`b.handler`, `arr[i]`, `*p`) — whose base is reached through exclusive (`&var` /
     owning) access all the way down. Calling a `mutating` closure that is a **temporary**
     (`make_counter()()`, a call result, a literal) is a compile error: *"a `mut` closure
     must be called through a place — bind it (`let mut c := …; c()`)."* Calling one
     through a shared `&` — a `&Self` receiver, `(&b).handler()`, an `&`-captured closure
     — is a compile error for the same reason.
  2. **For the call's dynamic extent the place is exclusively borrowed**, exactly as a
     `&var self` method borrows its receiver. So: two `mutating` calls on the same place
     cannot overlap; a reentrant `mutating` call reached from inside the first call is
     rejected (`T0003`-shaped "already exclusively borrowed"); no other read or write of
     the place, and no `&`/`&var` to it, may be live across the call.
  3. **The call does not consume the place** (unlike a `once` call). After it returns the
     closure is still bound, still callable, with its environment in whatever state §1a's
     write-back left it. `mut` is `&var self`-shaped, not `self`-shaped.

  - **`once mut` composes the two axes independently.** The `once` axis consumes the
    callee place *at the call expression, before the body runs* (RFC-0134 §2). The `mut`
    axis's exclusive borrow is then moot — there is no valid second call for it to guard.
    So a `once mut` call: place consumed at the call expression → any later use of the
    closure is a moved-value error, regardless of what the body did or whether it
    panicked (see §1a "Early exit").
  - **On `self`.** Metel closures have no written `self`; "`&var self`" is the borrow
    shape, not literal syntax. Point 1's place/exclusivity check is a small addition to
    the move checker (it already tracks exclusive borrows for `&var self` methods), not a
    new receiver-kind concept for callables.
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
  exclusive-borrow rule with no penalty and no latent capability tracking. The reverse —
  a `mutating` value into a `reading` slot — is rejected.

- **`Send` / `Sync` — an interim rule, not just a punt to RFC-0096.** With RFC-0003
  (concurrency) under review, a closure escaping to a fiber needs a rule now:
  - A **`mutating` closure value is not `Sync`.** Two fibers sharing `&` to it would each
    need the exclusive per-call borrow of §3 at once — the race the axis exists to
    prevent. (A `reading` closure over `Sync` captures is `Sync`.)
  - A closure is **`Send` iff every capture is `Send`** — the ordinary aggregate rule.
    For a `mutating` closure this means `Send` transfers sole ownership of the environment
    cell to the receiving fiber, which is sound (there is one owner, §1a). A `Copy`
    `mutating` closure sent by copy gives the receiver an independent cell, also sound.
  RFC-0096 may restate these through the general marker-aspect machinery later; until then
  these two lines are the rule.

- **Type erasure (`dyn`).** The flat 3-field `Type::Fun` degrades to `dyn
  Callable<Args, Ret>` (RFC-0061 §7.1 / metel-core#893) by carrying each field as an
  auto-marker bound — `CallMany` (call axis `many`), `CallShared` (mutation axis
  `reading`), and `Copy`. A bare `dyn Callable<A, R>` with **no** marker bounds is the
  most-restrictive form: call-once, exclusive-access, non-`Copy`. `+ CallMany` /
  `+ CallShared` / `+ Copy` widen it, per RFC-0152's superset direction. So `store(f: dyn
  Callable<(), i64>)` given a `once` `f` gets a value it may call **once**; to call it
  repeatedly `store` must take `dyn Callable<(), i64> + CallMany`. This is the default so
  the erased case is not undefined; the full `dyn Callable` design is metel-core#893's and
  is a non-goal here (see Alternatives).

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
   RFC-0134's two `Type::Fun` fields. Lands with RFC-0157's D5 as one hard change — no
   edition gate (Metel has no public users; RFC-0050's "Migration (no edition gate)").
   What this needs to hold v0.13.0: review → accepted, and Open Question 1 closed.

## References

- **RFC-0134 (Closure Call Capability)** — §4 reserves this field; §5 states the
  compose-as-independent-prefix constraint this RFC's qualifier satisfies; §2's
  inference pass is the one that also computes this axis. §3a's `fun(T) -> U`
  spelling assumed.
- **RFC-0152 (Function-Type Multiplicity Widening)** — the widening relation this
  axis joins, same `reading`-permits-`mutating` direction.
- **RFC-0006 (Closure Capture Semantics), `4-implemented`** — the per-call environment
  re-clone that §1a changes for `mutating` closures (write-back), as a hard change.
- **RFC-0067a (Reference Types)** — the exclusive-`&var` rule §3's call-site
  soundness reuses.
- **RFC-0050 (Closure Capture Lists), `1-under-review` (v0.13.0)** — as amended
  2026-08-31: capture list required for non-`Copy`/by-ref captures, bare `[n]` = by-value
  move. §1a's write-back applies to exactly those bare by-value captures. Sequenced with
  this RFC.
- **RFC-0157 (Copy and Clone Model Re-analysis), `1-under-review`** — its D5 (change to
  RFC-0006's capture default) lands together with §1a's write-back as one hard change; no
  edition gate.
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
