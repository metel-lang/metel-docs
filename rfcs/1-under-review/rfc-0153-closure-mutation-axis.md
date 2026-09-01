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
>   and landing with it as one hard change (no edition gate — Metel has no public users).
>   *(Superseded 2026-09-01: D5's decision removes the per-call `captured.clone()` for a
>   `reading` closure too — it now also reads its moved-in aggregate in place. §1a is the
>   current text; this bullet is kept for history.)* Scoped this way, `mutating` stops
>   being a type-level fact with no runtime effect.
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
> - **§3: a `mutating` call is `&var self`-shaped** (pass 2 corrected pass 1's
>   consumes-and-rebinds over-reach) — it needs *exclusive* access to the closure value
>   for the call's duration and does **not** consume it. *(Pass 2 added "the callee must be
>   an lvalue place; a temporary is a compile error" — the temporary half was wrong and is
>   withdrawn by the 2026-09-01 follow-up below; a temporary is trivially exclusive.)*
>   `once mut` composes the axes independently — the `once` axis consumes at the call
>   expression, the `mut` borrow is then moot.
> - **§1a's early-exit rule** split by axis: plain `mut` + panic → callable, partial
>   mutation visible; `once`/`once mut` + panic → moved value (RFC-0134 §2), no
>   "still callable" question.
> - **§1a storage model** unchanged: one environment cell owned by the closure value,
>   moves with it, copied for a `Copy` closure.
> - **§3 gains an interim `Send`/`Sync` rule** (`mutating` ⇒ not `Sync`; `Send` follows
>   captures) and a **`dyn` erasure default** (bare `dyn Callable` = most-restrictive;
>   `+ CallMany`/`+ CallShared`/`+ Copy` widen).
> - `.clone()` on a closure is a non-goal (closures are outside the aspect system).

> **Adversarial-review fixes, 2026-09-01 (third pass)** — cluster-wide re-review:
> - **`dyn Callable` erasure is removed from this RFC.** The pass-2 "`dyn` erasure
>   default" (§3) rested on unbuilt machinery (RFC-0096 auto-impl aspects; RFC-0061
>   §7.1's never-built `Callable`; RFC-0008 object-safety of a by-value `self` receiver).
>   It moves to its own RFC — **RFC-0161 (Callable Object Contract)**, target v0.13.1.
>   For v0.13.0 the closure model ships **monomorphic**: a closure is only ever a concrete
>   `Type::Fun`. The `Callable` aspect was never built either (pass 4, 2026-09-01), so
>   there is no `where F: Callable` bound in v0.13.0 — higher-order functions take a
>   concrete function type. Writing `dyn Callable<…>` is a v0.13.0 compile error. See §3.
> - **§1a nails the environment representation.** The `mutating` closure's environment is
>   **one inline owned aggregate that is part of the closure value** — bit-copied with it,
>   moved with it, never behind a shared pointer. Returnability (`make_counter`) is the
>   inline value being moved out, not heap/`Rc` indirection. A closure is `Copy` iff that
>   inline copy is trivial (every capture `Copy`, RFC-0134 §1); any representation that
>   would need indirection is non-`Copy`.
> - **Captured `Drop` values now have a rule** (§1a "Captured `Drop`"). RFC-0134 §5's "no
>   `Drop`-for-closures" bans a user `drop(&var self)` *on a closure*; it never exempted a
>   closure's captured values from being dropped. They are dropped when the closure value
>   is dropped, in capture-list order, like struct fields (RFC-0071); a `once`-consumed or
>   partially-moved-out env drops only its still-owned fields. Execution waits on #292;
>   the rule does not.
> - **Closure equality / ordering, comptime** — added as Non-Goals (closures satisfy no
>   aspects, so `==` / `<` on them does not type-check; comptime creation and call use the
>   same interpreter and the same axis semantics).
> - **`mut` env cell = the RFC-0050 capture aggregate**, not a wrapper around it — escape
>   / brand checking sees the same field types (§1a, and RFC-0050 Implementation Guidance).
> - **§3 reframed (2026-09-01, follow-up) — no closure-specific place calculus.** The
>   pass-2 "callee must be an lvalue place; a temporary is a compile error" was two things
>   at once: a real soundness property (the call needs *exclusive* access to the closure
>   value) and a mis-statement (a temporary *is* exclusive — one owner, gone after the
>   statement). §3 now says: **`mutating` makes the synthesized `call` take `&var self`**,
>   with the same callee-eligibility as any `&var self` method — closures add no case the
>   borrow checker doesn't already handle. *(Pass 4 then made §3 state that rule in full
>   rather than only pointing at RFC-0122.)* A **minimal interim static rule** covers the
>   pre-RFC-0122 window: reject only a **shared-`&` callee**; owned bindings, owned
>   temporaries, exclusive projections, and `&var` parameters all pass.

> **D5 decided, 2026-09-01 (language owner) — the closure-capture default is `move`.**
> RFC-0157's D5 is no longer a recommendation. It removes RFC-0006's per-call
> `call_env = captured.clone()` re-clone for **every** closure, so §1a's single moved-in
> environment aggregate is now the *universal* runtime model, not a `mutating`-only
> special case: a `reading` closure reads it in place, a `mutating` one also mutates it in
> place. §1a is rewritten accordingly. **RFC-0006 (`4-implemented`) carries a matching
> amendment note.**

> **Adversarial-review fixes, 2026-09-01 (fourth pass):**
> - **§3 now states the `&var self` receiver rule in full** (callee eligibility: owned
>   binding / owned temporary / exclusive projection / `&var` param; shared-`&` callee
>   rejected) rather than pointing at RFC-0122 as though the rule were written there.
>   RFC-0122 §2f gains a matching clause; RFC-0122 is cited for *enforcement*.
> - **Reentrancy is now enforced in v0.13.0** by a runtime in-call flag on every
>   `mutating` closure value (reentrant call → panic). Not removed when RFC-0122 lands —
>   defence in depth. Makes RFC-0122 §2e's "subset" claim true.
> - **`Send`/`Sync`:** the "`[&var n]` / `[&n]` closures are never `Send`" claim is
>   **withdrawn** — closure `Send`/`Sync` is the aggregate rule over captures, `&T` / `&var
>   T` per RFC-0080. Only `mutating` ⇒ `!Sync` remains, interim pending RFC-0096.
> - **`[&var x]` capture ⇒ `mutating`** regardless of body (Open Question 4 closed,
>   conservative). Use `[&x]` for a read-only reference capture.
> - **`Callable` aspect / `dyn Callable` deferred in full to RFC-0161** — never built
>   (RFC-0061 §7.1 / RFC-0008). v0.13.0: no `where F: Callable` bound, higher-order
>   functions take concrete function types, `dyn Callable<…>` is a compile error. RFC-0008
>   and RFC-0061's stale passages get "not implemented" annotations.

> **Adversarial-review fixes, 2026-09-01 (fifth pass):**
> - **Reentrancy claim narrowed.** The in-call flag catches **same-closure-value**
>   reentrancy only. *Aliased-capture* reentrancy — two distinct `mutating` closures (or a
>   `Copy` closure + its copy) each holding `[&var x]` to one `x` — is **not** caught; it
>   is in the same unenforced `[&var x]` borrow-freeze gap (RFC-0050 RQ1), closed by
>   RFC-0122. §3, RFC-0122 §2e/§2f updated.
> - **`[&var x]` still needs `mut` written** — `[&var x] () -> i64 { x }` is an error
>   ("add `mut` or use `[&x]`"); the `&var` capture is not itself the written signal.
> - **In-call flag details:** part of the closure value's representation (not the env
>   aggregate, not `Copy` state — a `bool` stays trivially copyable; a copy always starts
>   idle); cleared on the **single** unwind/return path that also does partial-move `Drop`
>   bookkeeping; runs in the comptime evaluator too (a compile-time *diagnostic* — not a
>   panic — on reentrancy).
> - **`Callable` wording corrected:** the `dyn <Aspect>` *syntax* is unchanged; there is
>   just no predeclared / stdlib `Callable`, so `dyn Callable<…>` is unknown-aspect
>   `T0003` unless the program declares one. Not reserved.
> - **`mutating` ⇒ `!Sync` owner:** RFC-0153 §3 owns the rule now; it *migrates* to
>   RFC-0096 once RFC-0096 models closure mutation (it does not yet).
> - **Nested closure borrowing an enclosing by-value capture** — RFC-0050 rejects it in
>   the v0.13.0 interim (local-reborrow-into-enclosing-env; RFC-0122 replaces the
>   rejection with an NLL check). RFC-0050 Migration gains class 3 (`&var` capture used
>   read-only → switch to `[&x]`).
> - **RFC-0006** body + `spec/functions.md` now carry section-level "historical / not yet
>   updated" fences, not just a top note.

> **Adversarial-review fixes, 2026-09-01 (sixth pass):**
> - **Widened `reading`→`mut` call dispatch specified** — call lowering branches on the
>   closure *value's* own `call_mutation`, not the slot type; a widened `reading` value
>   takes the plain call path (no exclusive borrow, no flag — it carries none). §3, §1a,
>   and RFC-0152 aligned.
> - **RFC-0050 `[&var count]` examples** now carry `mut` (they contradicted RFC-0153's
>   "`mut` is always written"); RFC-0050 states the requirement explicitly.
> - **"nothing the interim rule accepts is newly rejected" was backwards** — corrected in
>   §3 and RFC-0122 §2e: the interim rule has no false positives but *does* accept
>   programs RFC-0122 later rejects (the accepted-but-ill-formed gap; corpus must not rely
>   on it).
> - **RFC-0006** → `spec_status: pending` + `amended_by: rfc-0157, rfc-0050, rfc-0153`;
>   the amendment note now carries the `dynamics-1..4` anchor disposition; `spec/functions.md`
>   update is a tracked deliverable on the impl PR.
> - **`Copy` `mutating` ≠ shared `mutating`** — explicit note + test item (two-fiber copy
>   gives independent counters, not shared state).
> - **comptime reentrancy** is a compile-time *diagnostic* (source span), not a "panic".
> - RFC-0008's "reserved" wording for `Callable` dropped (it is not reserved).

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
- **A `[&var x]` (exclusive-reference) capture makes the closure `mutating` regardless of
  what the body does through it** — decided 2026-09-01 (was Open Question 4). The capture
  *acquires exclusive capability* over `x` for the closure value's whole lifetime
  (RFC-0050 Resolved Question 1's borrow-freeze), so the closure is not a value two
  threads may share (`!Sync`) and must not widen into a `reading` slot, even if this
  particular body only reads `x`. Classifying on the *effect* instead would need
  whole-body write-through analysis (including across calls) — exactly the inference this
  cluster rejects (RFC-0134 verify-not-infer).
  - **`mut` is still written.** Because `mutating` is always the written value (never
    inferred), a `[&var x]` closure literal must carry `mut`: `[&var x] mut () -> i64 {
    x }`. Omitting it — `[&var x] () -> i64 { x }` — is a compile error, *"a `&var`
    capture makes this closure `mut`; write `[&var x] mut (…)`, or capture `[&x]` if the
    body only reads `x`."* The `[&var x]` capture is not itself the "written" signal; the
    keyword is.
  - **If a read-only reference capture is what you want, capture `[&x]` (shared)** — that
    is what the shared/exclusive capture split is for; a `[&x]` capture whose body only
    reads is `reading` (and widens into `reading` slots normally), and a `[&x]` capture
    whose body tries to write is a compile error at the capture, not a `mutating`
    classification. **Migration:** existing closures that wrote `&var` for capability or
    habit but only read must move to `[&x]` — see RFC-0050 "Migration", class 3.
- A body that only reads captures — by value, or through a `[&x]` shared reference,
  including taking `&` of them — is `reading` and needs no annotation.

### 1a. Runtime model — what `mutating` actually does

RFC-0006 evaluated a call as `call_env = closure.captured.clone()` and never wrote the
result back, so a mutation to a by-value capture was discarded when the call returned.
That made `mutating` on a by-value capture a type-level fact with no runtime effect —
useless.

**RFC-0157's D5 (decided 2026-09-01 — the closure-capture default is `move`) removes the
per-call re-clone for *every* closure**, not just `mutating` ones: the captured
environment is moved into the closure's environment aggregate **once**, at creation, and
lives there for the closure's lifetime. On that base:

- **`reading` closure:** reads its moved-in environment aggregate **in place** — no
  per-call clone (there is no `Clone` bound to require and nothing to gain; a moved-in
  non-`Copy` value could not be re-cloned anyway). Since the body does not mutate, no
  write-back question arises. This is a behaviour change from RFC-0006 but an unobservable
  one for well-typed `reading` closures — it only removes wasted deep-clones (RFC-0050
  RQ5).
- **`mutating` closure:** the same single moved-in aggregate, additionally **mutated in
  place** — assignments to a by-value capture, and `&var` taken of one, land in the
  aggregate and *persist across calls*. The closure holds private mutable state: a
  returnable counter / accumulator / memoizer, Rust's `move ||` + `FnMut`. Captures held
  by `&var` reference already persist (through the outer cell); this makes the *owned*
  captures behave the same way.
  - **Storage and movement.** The environment cell is **one inline owned aggregate that
    is part of the closure value** — the same aggregate RFC-0050's Implementation Guidance
    describes for captures, held owned-and-mutable rather than re-cloned per call, *not* a
    wrapper around it and *not* behind a shared pointer. It moves with the closure value:
    assigning the closure to a new binding, passing it by value, or returning it
    (`make_counter`) moves the inline aggregate out with the rest of the closure value;
    the write-back target travels with the closure and stays valid. Returnability is that
    move, **not** heap/`Rc` indirection — there is no separate allocation to alias. There
    is at most one live owner (§3).
  - **`Copy` and the cell.** Copying the closure value is possible only when its
    `use_multiplicity` is `many` — every capture `Copy`, RFC-0134 §1 — in which case the
    inline aggregate is **bit-copied** with the rest of the closure value and the copies
    then diverge, exactly as copying a struct with a counter field would. This is a
    *trivial* copy (no allocation, no indirection); a `[n] mut` closure with `n: i64` is
    `Copy` and `let mut d := c;` gives `d` an independent counter. Any representation that
    would require non-trivial copy (a heap cell, an `Rc`) is by construction non-`Copy` —
    it necessarily captured a non-`Copy` value — so the "two `Copy` owners aliasing one
    mutable backing" state cannot arise.
  - **The §3 in-call flag is part of the closure value's representation** (it sits beside
    the environment aggregate, not inside it) and is present **only on closure values
    whose `call_mutation` is `mutating`** — a `reading` closure value carries no `in_call`
    field, which is why §3's call dispatch branches on the value's `call_mutation` and a
    widened `reading`-in-a-`mut`-slot value is never asked for a flag it doesn't have. It
    is **not** part of `use_multiplicity` / `Copy` reasoning — a `bool` is trivially
    copyable, so a `[n: i64] mut` closure stays `Copy`. A copy is only reachable when the
    source is not mid-call (the source is exclusively borrowed for the whole of its own
    `mutating` call), so the flag is always `false` at the moment of copy and the copy
    starts idle. No "copied a set flag" observable exists.
  - **Captured `Drop`.** A closure value **owns its by-value captures**; when the closure
    value is dropped, its environment aggregate is dropped — fields in capture-list order,
    exactly as a struct's fields (RFC-0071). RFC-0134 §5's "no `Drop`-for-closures" means
    a closure has no user `drop(&var self)` of its own; it does **not** exempt captured
    values from being dropped. A `once`-consumed closure: the moved-out value is dropped
    at the end of the scope that consumed it, per ordinary move rules; if the body moved
    *some* captures out and left others, only the still-owned fields are dropped (ordinary
    partial-move drop). Actually *running* destructors waits on RFC-0071 destructor
    invocation (metel-core#292); until then a non-trivial captured `Drop` value behaves as
    everywhere else in the language (empty `drop` bodies only). The **rule** — what gets
    dropped and in what order — is fixed here and does not wait on #292.
  - **Early exit.** Write-back is **in place, not transactional.** One unwind/return
    cleanup path handles all of: ending the §3 exclusive borrow, clearing the §3 in-call
    flag, and running/marking the partial-move `Drop` bookkeeping for any capture the body
    moved out before exiting. These are **not independent cleanup paths** — an
    implementation runs them in one RAII/`finally` frame so they cannot disagree about
    what state the aggregate is in. The distinction is which axis governs:
    - **Plain `mut` (not `once`):** the call does not consume the closure (§3). If the
      body exits via `panic` / a propagated error (`?`) / any non-normal `Signal`, the
      mutations that ran are visible in the cell, the exclusive borrow ends and the
      in-call flag clears with the unwind, and the closure remains **callable in a
      valid-but-partial state** — exactly as a `&var self` method that panicked
      mid-mutation leaves its receiver. No rollback.
    - **`once` or `once mut`:** the `once` axis consumed the callee place *at the call
      expression*, before the body ran (RFC-0134 §2). So the closure is a moved value
      whether the body returned normally or panicked, and a later use is the ordinary
      moved-value error. There is no "still callable after panic" question — `once`
      already answered it. The environment aggregate may hold a partial or moved-out
      state; that is unobservable *as closure state* — the closure cannot be called
      again — but the aggregate's **still-owned fields are still dropped** when the moved
      closure value goes out of scope, per "Captured `Drop`" above (drop of a
      partially-moved aggregate drops only the fields that were not moved out). (If the
      panic is caught, the moved-out *outer* bindings the `once` call consumed are
      handled by RFC-0134 §2's existing rules, unchanged.)
- This is a change to RFC-0006 (`4-implemented`), landing with RFC-0157's D5 change to the
  capture default as **one hard change** at v0.13.0 — **no edition gate**: Metel has no
  public users, so the `mut` keyword, the write-back semantics, and the fixture corpus all
  move together (see RFC-0050's "Migration (no edition gate)").

§3's `&var self` receiver is what keeps the write-back sound: for a plain `mut` closure
the closure value is exclusively borrowed for each call's duration, so no two calls —
reentrant included — are ever mid-mutation on the same aggregate at once; for `once mut`
the `once` consumption makes a second call impossible outright.

### 2. Qualifier

An explicit qualifier for the promise case (a `native` declaration, an aspect
method signature, or a stdlib signature that must stay `mutating` regardless of
its current body), composing with `once`/`many` as an independent prefix per
RFC-0134 §5's constraint:

```
mut fun(T) -> U            // reading is the default; `mut` marks mutating
once mut fun(T) -> U       // consumes and mutates
mut once fun(T) -> U       // the same TYPE — the two qualifiers are order-insensitive
                           //   as type spelling (RFC-0134 §5)
```

**Type spelling vs. literal prefix.** The qualifiers are order-insensitive *as a type
spelling* — `once mut fun(T) -> U` and `mut once fun(T) -> U` denote the identical
`Type::Fun` — matching RFC-0134 §5's "independent, order-insensitive prefix" constraint.
A **closure literal**, by contrast, has a single fixed prefix order, set by RFC-0050:
`[captures] once? mut? (params) -> ret block`. So `[c] mut once () -> T { … }` is a
*parse* error even though `mut once fun(T) -> U` is a valid type; write `[c] once mut
() -> T { … }`. RFC-0050 is the normative source for the literal grammar; this RFC's
examples use that order.

Spelling of the qualifier keyword itself is Open Question 1 — `mut` reuses Metel's
mutation vocabulary (`&var`, `var` bindings) but `var fun` may read better; deciding this
is part of this RFC. Whichever wins, both the type spelling and the literal prefix use it.

### 3. Call-site soundness

**A `mutating` closure's synthesized `call` takes `&var self`.** That is the whole rule.
A `mutating` call needs *exclusive* access to the closure value for the call's duration —
because §1a mutates the environment aggregate in place, and two overlapping or reentrant
calls would alias `&var` to that aggregate — and "exclusive access to a receiver for a
call's duration" is precisely what a `&var self` method already means. So `call_mutation
= mutating` selects the `&var self` receiver for `call`. This section **states the rule in
full**; RFC-0122 (Borrow Checker) is where it is *statically enforced*, and RFC-0122 §2f
carries a matching clause so the two do not drift.

**Callee eligibility (the `&var self` receiver rule, stated here).** A `mutating` call
`e(args)` requires `e` to denote a place the caller can exclusively borrow for the call's
dynamic extent:

- an **owned binding** (`c`) — eligible;
- an **owned temporary** (`make_counter()()`, a block-expression result `({ f })()`, any
  other rvalue) — eligible: a temporary has exactly one owner and is unreachable after the
  enclosing statement, so it is trivially exclusive. *(This RFC's pass-2 text said "a
  temporary is a compile error" — that half was wrong and is withdrawn.)*
- an **exclusive projection** off an owned or `&var` base — `b.handler`, `arr[i]`, `*p` —
  where **every** step of the path is reached through owning or `&var` access; eligible;
- a **`&var` parameter** or a place reached through one by exclusive projection —
  eligible;
- a **shared-`&` callee** — a `&Self`/`&self` receiver, `(&b).handler()`, an `&`-captured
  closure, any place reached through a `&` step — **not eligible**, compile error
  *"a `mut` closure cannot be called through a shared reference; it needs exclusive
  access"*.

For the call's dynamic extent the place is exclusively borrowed exactly as `&var self`
borrows a method receiver: no other read, write, `&`, or `&var` of the place may be live
across the call, and **two `mutating` calls on the same place cannot overlap**.

**Reentrancy.** A second `mutating` call reached from *inside* a still-live one re-enters
the exclusive borrow. RFC-0122 rejects **every** form statically (`T0020`-shaped "already
borrowed exclusively"). Before RFC-0122, v0.13.0 splits into two cases:

- **Same closure value** — the body calls *this* closure again (through a handler stored
  in a structure the body reaches, an aliasing `&var` binding, etc.; a closure cannot name
  its own `let` binding, so never directly). **Guarded at runtime.** Every `mutating`
  closure value carries a one-bit "in-call" flag: set on entry to a `mutating` call,
  checked on entry, cleared on the single unwind/return cleanup path (§1a "Early exit" —
  the same path that finalises partial-mutation and partial-move `Drop` bookkeeping, not a
  second independent one); a reentrant call finds it set and **panics**
  (`"re-entrant call to a mutating closure"`). One bit per closure value, one branch per
  `mutating` call — the `RefCell`-style guard. Kept after RFC-0122 lands as a
  defence-in-depth backstop (in a `--borrow-check`-clean program it can never fire).
- **Distinct closure values aliasing one place** — two different `mutating` closures, or a
  `Copy` closure and its copy, each holding `[&var x]` to the same `x`; one calls the
  other while its own call is live, so both mutate `x` at once. The in-call flag is
  per-closure-value and does **not** catch this. It is exactly RFC-0050 Resolved
  Question 1's `[&var x]` borrow-freeze — **accepted-but-ill-formed** in v0.13.0, in the
  same unenforced gap, and the fixture corpus must not rely on it (RFC-0050 "Migration").
  RFC-0122 closes it statically.

So v0.13.0 *enforces* no same-closure-value reentrancy and *asserts but does not enforce*
the aliased case; RFC-0122 enforces both.

**The call does not consume the closure** (unlike a `once` call). After it returns the
closure is still bound and still callable, its environment in whatever state §1a left it.
`mut` is `&var self`-shaped, not `self`-shaped.

**`once mut`** composes the two axes independently: the `once` axis consumes the callee
*at the call expression, before the body runs* (RFC-0134 §2), so any later use is a
moved-value error regardless of the body; the `mut` exclusive borrow is then moot — there
is no valid second call for it to guard. A `once mut` body can only reach its own closure
value through an aliasing binding (a closure cannot name its own `let` binding), and any
such alias is itself an ill-formed borrow of a moved-then-borrowed value (RFC-0134 §2 +
§3); the interpreter reports whichever it detects first — the moved-value error or the
in-call panic — and this RFC does not fix a diagnostic order for that unreachable-by-
construction case.

**Interim static rule for the pre-RFC-0122 window.** Until RFC-0122 lands, the front-end
enforces the cheap, statically-checkable half of the eligibility rule above: **reject a
shared-`&` callee**; accept an owned binding, an owned temporary, an exclusive projection
whose every step the front-end can see is owning/`&var`, or a `&var` parameter. What it
**cannot** check without the borrow checker — that no *other* borrow of the place is live
across the call, and that an exclusive projection's dynamic base is genuinely unaliased —
is left to RFC-0122; a program that violates only those parts is accepted-but-ill-formed
by this section (the fixture corpus must not rely on it — see RFC-0050 "Migration"), the
same status as RFC-0050's `[&var x]` borrow-freeze. **Same-closure-value reentrancy is not
in that gap** — the in-call flag catches it at runtime. **Aliased-capture reentrancy is**
in the gap (distinct closure values, one place — above). The interim rule is **weaker**
than the full `&var self` receiver rule (it rejects less): so it never rejects a program
the full rule would accept — nothing written against it is stranded when RFC-0122 lands —
but it *does* accept programs RFC-0122 later rejects (`T0020`), and those are exactly the
accepted-but-ill-formed gap above. That is intended, not a contradiction; the corpus
constraint is what keeps it from mattering. When RFC-0122 lands the interim static rule is
deleted and the full rule (stated above) takes over. **RFC-0122 §2e catalogues this**
alongside the other interim borrow-shaped stopgaps.

**Other axes and type-level interactions.**

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
- **Widening `reading` → `mutating` slot (RFC-0152) is type-level only, and call dispatch
  is on the *value*, not the slot.** A `reading` value passed to a `mut (T) -> U`
  parameter keeps its actual runtime behavior. **Call lowering branches on the closure
  value's own `call_mutation`** (carried on every runtime closure value, from `Type::Fun`
  — RFC-0134 §1), **not on the static slot type**:
  - a value whose `call_mutation` is `mutating` → the exclusive-borrow path + the in-call
    flag set/check (this section, above);
  - a value whose `call_mutation` is `reading` → the plain call path, **no flag touched,
    no exclusive borrow** — even when the *slot* it arrived through is typed `mut (…)`.
    (A `reading` closure genuinely cannot alias-mutate, so nothing is lost by not
    guarding it; and it carries no `in_call` field to read — see §1a "the flag is only on
    `mutating` closure values".)

  So a widened `reading` value in a `mut` slot is called exactly as it would be through a
  `reading` slot; the slot type only bounds what the callee is *allowed to assume* (it may
  treat `f` as needing `&var self`), not what actually happens. Widening happens only at
  first-order by-value / owned positions (argument, return, ascription, struct-field
  init), so the callee always holds the value by value or `&var` and this dispatch is
  always well-defined. The reverse — a `mutating` value into a `reading` slot — is
  rejected.

- **`Send` / `Sync` — defer to the aggregate rule; one closure-specific fact.** A closure
  value's `Send`/`Sync` is the **ordinary aggregate rule over its captures**, applied to
  the inline environment aggregate (§1a): `Send`/`Sync` iff every capture is. `&T` / `&var
  T` captures follow **RFC-0080** (`&T: Send if T: Sync`; `&var T: Send if T: Send`; the
  `Sync` rules likewise) — this RFC does **not** restate or override those, and the
  earlier "`[&var n]` / `[&n]` closures are never `Send`" claim is **withdrawn** as an
  unowned exception to RFC-0080. A `[n] mut` closure over an owned `n` is `Send` iff `n`
  is, transferring sole ownership of the aggregate (sound — one owner, §1a; if `n: Drop`
  the sending fiber has moved it, so no double drop). A `Copy` `mutating` closure sent by
  copy gives the receiver an independent aggregate, also sound.
  - The **one** closure-specific fact: a **`mutating` closure value is not `Sync`** — two
    fibers sharing `&` to it would each need §3's exclusive per-call borrow at once.
    **This RFC owns that rule** for now — it is not yet in RFC-0096. When RFC-0096's
    auto-impl marker-aspect machinery grows a closure-mutation hook (it does not have one
    today), this rule migrates there; until it does, RFC-0153 §3 is the normative source.
    RFC-0122 §2e records the migration, not a present ownership. (A `reading` closure over
    `Sync` captures is `Sync` by the aggregate rule, no special case.)

- **Type erasure (`dyn`) / the `Callable` aspect — not in v0.13.0 at all.** The
  `Callable<A, R>` aspect and `dyn Callable<A, R>` were **specified but never built**
  (RFC-0061 §7.1, RFC-0008; verified against the interpreter — no `Callable` impl for
  function types, no `dyn Callable` coercion). The whole concept — the aspect, the object
  form, and the `+ CallMany` / `+ CallShared` marker widening an earlier draft of this
  section sketched — is **deferred in full to RFC-0161 (Callable Object Contract)**, target
  v0.13.1. **Normative for v0.13.0:**
  - A closure is only ever a **concrete `Type::Fun`**. **There is no predeclared /
    stdlib `Callable` aspect** — so a generic parameter cannot be bounded `where F:
    Callable<…>` against a standard aspect, and a higher-order function takes a **concrete
    function type** (`f: (T) -> U`, with the `once` / `mut` qualifiers as needed) — which
    is how `List::map` and every other stdlib combinator already work (RFC-0134 §3; checked
    against `core.mtl`). Abstracting over "any callable representation" is not expressible
    in v0.13.0; RFC-0161 is where it returns.
  - The `dyn <Aspect><…>` *syntax* is unchanged (RFC-0008) — `dyn Callable<…>` resolves
    only if the program itself declares an aspect named `Callable`, and is a plain
    unknown-aspect `T0003` otherwise. `Callable` is **not a reserved word** in v0.13.0; a
    fixture that defines its own `Callable` aspect keeps working and will need renaming
    when RFC-0161 introduces the real one.
  - RFC-0008 and RFC-0061's passages describing the *stdlib* `dyn Callable` / "function
    types automatically implement `Callable`" are annotated "not implemented — deferred to
    RFC-0161".

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

**`Copy` `mutating` ≠ shared `mutating`.** Copying a `Copy` `mutating` closure — including
sending it to two fibers (`spawn(c); spawn(c);`) — gives each site its **own** environment
aggregate and its **own** idle in-call flag; the counters advance independently. This is
*not* shared mutation and needs no `Sync` (`c` is `Send` by copy). It is the same
"`Copy` means an independent value" the language has everywhere, but the `mut` keyword can
prime a "shared state" expectation, so it is a documented test-and-doc item (#902).

A closure that captures a *non-`Copy`* value by value (`[buf] mut (e) -> () { buf.push(e); }`)
is non-`Copy` by RFC-0134 §1 — so there is exactly one owner and the "two owners mutate
the same backing" case cannot arise. To *share* mutable state across fibers, capture
`[&var shared]` (or an `Rc`-like handle) — the closure is then non-`Copy` and `!Sync`, and
the sharing is explicit.

**Capturing an `Rc` / `Share` handle (RFC-0158).** `[rc]` on an `Rc<T>` capture *moves
the handle in* — `Rc` is non-`Copy` (it is `Share`, not `Copy`, under RFC-0158), so the
list is required and the closure is non-`Copy`. Aliasing is explicit inside the body:

```metel
let rc := Rc::new(Node { value: 1 });
let mut bump := [rc] mut () -> Rc<Node> {
    rc := rc.share();   // explicit new handle; write-back (§1a) stores it in the env
    rc
};
```

`rc.share()` is an ordinary method call on a *captured* value; the write-back rule of
§1a persists the reassigned handle in the environment aggregate exactly as it would any
other `mut` reassignment. This is unrelated to the "`.share()` **on a closure value**"
non-goal below — that non-goal is about a closure having no `Share` impl of its own, not
about what a closure body may call on its captures.

## Alternatives considered

### Independent marker aspects instead of fields on `Type::Fun`

> **This subsection is now RFC-0161's design space.** It sketches the `Callable<A, R>` +
> `CallMany` / `CallShared` marker-aspect model for the *erased* case. That model, the
> `Callable` aspect, and `dyn Callable` are **entirely RFC-0161 (Callable Object
> Contract), v0.13.1** — none of it exists in v0.13.0 (§3). Kept here as the record of the
> fork this RFC chose against for the flat model; RFC-0161 takes it as its starting point.

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

- ~~Changing RFC-0006's by-value capture model.~~ **Now changed, cluster-wide.** RFC-0157
  D5 (decided 2026-09-01) makes by-value capture a move and removes the per-call
  `captured.clone()` for *every* closure; this RFC additionally **writes back** a
  `mutating` closure's captures so mutation persists across calls (§1a). *How* a capture
  gets into the closure is RFC-0050/RFC-0157's concern; this RFC governs only what a
  `mutating` *call* does to an already-captured value and whether that survives the call.
- Capture-list syntax (`&var` / bare specifiers) — RFC-0050, a separate document, but
  sequenced into the same v0.13.0 closure-model cluster.
- `Drop`-for-closures / unconsumed-closure cleanup — RFC-0134 §5 rules it out and
  this RFC does not reopen it. **Distinct from "captured `Drop` values,"** which §1a
  *does* specify (the closure owns its captures and drops them like struct fields); the
  non-goal is only a closure having a user `drop(&var self)` of its own.
- **`dyn Callable` / type-erased callables — RFC-0161** (v0.13.1). The pass-2 interim
  `dyn` erasure default is withdrawn (§3); v0.13.0 is monomorphic.
- **Closure equality / ordering.** `Type::Fun` values satisfy **no aspects** (RFC-0134's
  Open-Questions finding: `InferType::Fun` implements nothing), including `Eq` / `Ord`,
  so `a == b` / `a < b` on closure values does **not** type-check — it is an aspect-not-
  satisfied error, the same as `==` on any non-`Eq` type. Structural equality of two
  `Type::Fun` *types* (used by the unifier) is a type relation and says nothing about
  value equality; two closures of the same type with different captures are simply not
  comparable. No closure-identity or by-address comparison is introduced.
- **`comptime` / `const` closures.** A closure may be created and called at `comptime`;
  the comptime evaluator is the same interpreter, so `mut` write-back (§1a), `once`
  consumption, **and the §3 in-call flag** all run on the same code path — a `comptime`
  `[n] mut () -> i64` counter advances between `comptime` calls exactly as a runtime one
  does. A `comptime` reentrant `mutating` call surfaces as a **compile-time evaluation
  diagnostic** (a proper error with a source span, the comptime analogue of the runtime
  panic — the same `"re-entrant call to a mutating closure"` condition, reported through
  whatever mechanism comptime-evaluation failures already use; **not** an evaluator panic
  and **not** unguarded recursion). No separate const-closure model, and no relaxation of
  §3's exclusive-place rule. That the flag path is shared between the two evaluators is a
  delivery-test item on #902.
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
3. **`Send`/`Sync` derivation. ✓ Resolved (2026-09-01, pass 4).** Deferred to the
   ordinary aggregate rule over captures (RFC-0080 owns `&T` / `&var T`); this RFC
   restates none of it. The one closure-specific fact — a `mutating` closure is `!Sync` —
   is an interim statement pending RFC-0096 (§3, catalogued in RFC-0122 §2e).
4. **`&var`-capture without mutation. ✓ Resolved (2026-09-01, pass 4): conservative.** A
   `[&var x]` capture is `mutating` regardless of the body — it takes exclusive capability
   over `x` for the closure's lifetime. For a read-only reference capture, use `[&x]`
   (shared). See §1.
6. **`mutating`-callee eligibility. ✓ Resolved (2026-09-01).** §3 states the full
   `&var self` receiver rule; RFC-0122 enforces it statically (a matching clause in
   RFC-0122 §2f), and v0.13.0 additionally carries a **runtime in-call flag** that
   panics on reentrancy. The interim static rule (reject shared-`&` callees) covers the
   pre-RFC-0122 window for the rest. The broader "dynamic path so `mutating` closures work
   freely through shared structures" question is RFC-0161's (erased case).
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
- **RFC-0122 (Borrow Checker)** — §3 delegates `mutating`-callee eligibility to its
  `&var self`-receiver rules; closures add no new case. The §3 interim rule is a stopgap
  for the v0.13.0 window before RFC-0122 lands and is deleted when it does.
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
- **RFC-0161 (Callable Object Contract), `1-under-review` (v0.13.1)** — the home of the
  `dyn Callable` design that §3's pass-2 interim default was withdrawn into; takes this
  RFC's Alternatives section as its starting point.
- **RFC-0158 (Share and Clone)** — `Rc` is `Share`, not `Copy`, so an `[rc]` capture
  makes the closure non-`Copy`; the §4 worked example of a captured `Share` handle.
- **RFC-0071 (Destructors)** — the field-order drop rule §1a's "Captured `Drop`"
  reuses; its invocation is metel-core#292, which gates *execution* not the rule.
- **RFC-0080 (Stdlib Aspects — …, `Send`/`Sync`)** — owns the `&T` / `&var T` reference
  `Send`/`Sync` rules §3 defers closure `Send`/`Sync` to; this RFC restates none of them.
- **RFC-0122 (Borrow Checker)** — §3's `&var self` receiver rule is enforced there;
  §2f carries the matching clause, §2e catalogues the interim window.

---

## Decision

**Outcome:** *(pending — `1-under-review`, opened 2026-08-30, deferred from RFC-0134
§4/§5, widened 2026-08-31 to cover encapsulated persistent state (§1a) — the case that
makes the axis worth having. Milestone moved to v0.13.0 (#902) so the closure model ships
complete; lands whole, with RFC-0134 / RFC-0152. Needs review → accepted and Open
Question 1 (qualifier spelling) closed to hold v0.13.0. Other open points: `Send`/`Sync`
ownership, `&var`-capture-without-write precision.)*
**Target:** v0.13.0 (#902).
