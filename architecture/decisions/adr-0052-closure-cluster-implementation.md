---
id: adr-0052
title: "v0.13.0 Closure Cluster — Implementation Shape"
date: '2026-09-01'
status: accepted
relates: adr-0006, adr-0007, adr-0045
implements: "metel-core#269, #803, #901, #902, #918"
---

## Context

The v0.13.0 closure cluster — RFC-0134 (Closure Call Capability), RFC-0152 (Function-Type
Multiplicity Widening), RFC-0050 (Closure Capture Lists), RFC-0153 (Closure Mutation
Axis), RFC-0157 (Closure Capture Default: Move) — is `2-accepted` as language design. A
readiness review (2026-09-01, seventh adversarial pass) found the *design* settled but
several *implementation* questions unstated, because the RFCs are design documents and
deliberately do not carry runtime-representation detail. This ADR records those decisions
so the single implementation PR does not rediscover them.

The cluster's accepted rules, for reference:

- **Capture default is `move`** (RFC-0157 D5): a by-value capture of a non-`Copy` free
  variable is moved into the closure; `Copy` is copied; `Clone`-not-`Copy` is an error
  unless `.clone()`d at the capture site. A capture list `[…]` is required the moment a
  move or an `&`/`&var` capture happens.
- **`Type::Fun` gains three multiplicity fields** (RFC-0134 §4, RFC-0153 §1):
  `call_multiplicity` (`once`/`many`), `use_multiplicity` (`Copy`-ness), `call_mutation`
  (`reading`/`mutating`).
- **The per-call environment re-clone is removed** (RFC-0157 D5 / RFC-0153 §1a): the
  captured environment is moved into the closure once, at creation, and read (or, for a
  `mutating` closure, mutated with write-back) in place.
- **A `mutating` call is a `&var self`-shaped exclusive borrow of the callee place**
  (RFC-0153 §3), with a runtime "in-call" flag guarding same-value reentrancy in the
  pre-RFC-0122 window.
- **Widened `reading` → `var` call dispatch is on the closure value's own
  `call_mutation`, not the slot type** (RFC-0153 §3, RFC-0152).

## Decision

### 1. Closure-specific move / call / mutation checking is **always-on** in v0.13.0

RFC-0134 §2's consumption check and RFC-0153 §1's mutation check are conceptually part of
the move checker (`move_check/`), which today is opt-in behind `--move-check`
(metel-core#267, #579). **For v0.13.0 the closure-cluster checks run unconditionally** —
the capture-list grammar, the `var` keyword, "add a capture list", "add `var`", the
`var`-closure-through-shared-`&` rejection, `once` requirement for a consuming body, and
the runtime in-call flag are all always-on, regardless of `--move-check`.

This is a deliberate, accepted inconsistency for this phase: the rest of move checking
stays opt-in until metel-core#267. The closure checks cannot be opt-in and mean anything —
`let f := [s] () -> String { s }; f(); f()` must be rejected as ordinary v0.13.0
behaviour, not only under a flag. When #267 makes move checking default-on, the closure
checks simply stop being a special case; nothing about them changes.

Practical wiring: the classification and verification passes RFC-0050 "Checking order"
describes (capture classification → `use` → `call` → `mutation`) run after type checking,
in the frontend, not gated by the `--move-check` entry point. Reuse `move_check/`'s place
abstraction (`metel-interpreter/src/place.rs`, adr-0045 / #579 — analysis-neutral) but
invoke it from the always-on path for closures.

### 2. Runtime closure representation

Today: `RuntimeCallable::Closure(Rc<ClosureValue>)`; `ClosureValue { captured:
Environment, fun_type: Option<Type>, … }`; a call clones the `ClosureValue`, then
`env.capture_clone()` deep-clones `captured` into a fresh `call_env`; closure creation
deep-clones the defining environment.

Target shape:

- **The closure value owns an inline environment aggregate**, not `Rc`-shared and not a
  full `Environment` snapshot. It is the named-field list from the capture list (or, for a
  listless `Copy`-only closure, the copied free `Copy` values), one field per capture,
  with each field's kind fixed by its specifier: `[x]` = owned (moved/copied in), `[&x]` =
  shared reference, `[&var x]` = exclusive reference, `[x.clone()]` = owned (explicit
  copy). Same shape as struct field storage (RFC-0050 Implementation Guidance) — reuse the
  aggregate machinery, do not invent a closure-specific env type.
- **No per-call clone.** A `reading` closure reads the aggregate in place. A `mutating`
  closure mutates it in place; the writes persist on the closure value across calls
  (RFC-0153 §1a write-back).
- **`Rc<ClosureValue>` sharing must not alias a `Copy` `mutating` closure's state.**
  `let var d := c;` on a `Copy` closure (`[n: i64] var`) must give `d` an *independent*
  counter. Either drop the `Rc` for closure values whose `use_multiplicity` is `many` and
  bit-copy the value (aggregate included), or keep `Rc` only for non-`Copy` closures
  (where there is exactly one owner anyway). The observable contract is: copying a `Copy`
  closure copies its environment aggregate; the copies diverge.
- **Add two explicit fields to the runtime closure value:**
  - `call_mutation: CallMutation` (`Reading` | `Mutating`) — the closure's *own* axis
    value, populated at creation from the literal's classification, **independent of any
    slot type it later flows through**. Call dispatch branches on this field: `Mutating` →
    exclusive-borrow path + in-call flag; `Reading` → plain call path, no flag. A generic
    closure (`fun_type: None`) still carries this field — it is not derived from
    `fun_type`.
  - `in_call: bool` — the RFC-0153 §3 reentrancy guard. Set on entry to a `mutating`
    call, checked on entry (set ⇒ runtime error, code below), cleared on the single
    unwind/return cleanup path (the same frame that finalises partial-mutation and
    partial-move `Drop` bookkeeping). Present only on closure values whose `call_mutation`
    is `Mutating`; a `Reading` closure has no such field. A `bool` is trivially copyable,
    so it does not affect `use_multiplicity`; a copy always starts `false` (the source is
    exclusively borrowed during its own call, so it is never mid-call when copied).
- **`capture_clone` removal is not a one-line swap.** `Environment::define` deep-clones
  values into cells; `capture_clone` deep-clones every scope. Replace the closure-creation
  path with capture-kind-selective construction: for each capture-list item, move / copy /
  take-reference per its specifier into the aggregate. The generic ordinary-binding
  `capture_clone` path is unaffected for non-closure uses.
- **`ClosureValue` vs named-function-pointer sameness.** RFC-0061's correction note relies
  on a closure and a named `fun` pointer of matching signature being the same `Type::Fun`
  *type*. That is a type-level statement and is unaffected — the new runtime fields are on
  the *value*, not the type. A named function has an empty capture aggregate and
  `call_mutation: Reading`.

### 3. `Type::Fun` change — the real match-site set

RFC-0134 §4 characterised this as "one enum variant and two read sites." That undersells
it. `Type::Fun(Vec<Type>, Box<Type>)` → `Type::Fun(Vec<Type>, Box<Type>, CallMult,
UseMult, CallMutation)` and the parallel `InferType::Fun` change touch, at minimum:

- `metel-frontend/src/types/mod.rs` — the `Type` and `InferType` enum variants, their
  `Display`, any `From`/`Into`, `value_to_type` / `type_of`.
- `typeinference/` — unification of two `Fun` types (currently symmetric structural
  equality — see RFC-0134 §3; the three fields are compared directionally per RFC-0152,
  not unified), the `infer_type_satisfies_aspect` `Fun => false` arm (unchanged in
  behaviour, but `use_multiplicity` now has a value to cross-check), inference-var
  lowering `InferType` → `Type`.
- Type-syntax lowering (parser → `Type`) for the `once? var? (params) -> ret` qualifier
  prefix, and RFC-0152's widening / `if`-`match` join sites.
- `move_check/` — the classification and verification passes (§1 above), the place
  abstraction is reused not changed.
- `construction.rs` / generic monomorphisation — `FunBody::Generic` closures build their
  `Type::Fun` per call site; the three fields are classified at the definition site
  (RFC-0134 §2 amendment) and carried on the scheme.
- Registry, projections, object-safety (`Fun` satisfies no aspects — unchanged), and the
  fixture corpus.

`use_multiplicity` overlaps what `infer_type_satisfies_aspect` computes for `Copy` on a
closure today (RFC-0134 §1: `Copy` iff every capture is `Copy`). Keep one source of
truth: the field is populated from that computation at creation, and the aspect query
reads the field rather than re-deriving.

### 4. Error and runtime codes

Allocate a contiguous `T00xx` block for the always-on static errors and one runtime code.
`T0019` is move checking; `T0020` is reserved for RFC-0122 (borrow checking) and must not
be used here.

| Condition | Code | Message shape |
|---|---|---|
| non-`Copy` free variable referenced with no capture list | `T0026` | *"closure captures non-`Copy` `s`; add a capture list — `[s]` to move it in, `[&s]` / `[&var s]` to borrow, `[s.clone()]` to copy"* |
| capture list present but not exhaustive / specifier mismatch | `T0026` | *"`s` is captured but not listed"* / *"`s` is listed `[&s]` but the body writes it"* |
| body consumes a by-value capture, closure not written `once` | `T0027` | *"this closure moves captured `s` out; write `[s] once (…)`"* |
| body mutates a capture / `[&var x]` capture, closure not written `var` | `T0028` | *"a `&var` capture makes this closure `var`; write `[…] var (…)`, or capture `[&x]` if the body only reads it"* |
| `mutating` closure called through a shared `&` | `T0029` | *"a `var` closure cannot be called through a shared reference; it needs exclusive access"* |
| inner closure borrows an enclosing closure's by-value capture | `T0030` | *"cannot borrow into an enclosing closure's environment yet; bind a copy, or wait for the borrow checker (RFC-0122)"* |
| re-entrant call to a `mutating` closure (runtime) | `R0016` | *"re-entrant call to a mutating closure"* — a runtime error / diagnostic, not a static one; the comptime evaluator surfaces it as a compile-time diagnostic with a source span (RFC-0153 Non-Goals) |

Exact numbers are a delivery detail; the constraint is a **contiguous block, distinct
from `T0019`/`T0020`**, registered in `public/reference/error-codes.md` at integration
(not before — a code no pass emits should not appear in the reference).

### 5. Migration sweep

The corpus sweep (RFC-0050 "Migration") has three behaviour-change classes. A grep recipe
for the one PR:

- **Class 1 — capture-then-still-use.** A closure literal capturing a non-`Copy` local,
  followed by a later use of that local in the same scope. Not fully grep-able (needs
  scope analysis); the practical proxy is: run the always-on checks against the corpus,
  every `T0026`/`use-after-move` in a fixture that previously passed is a class-1 site.
  Fix: `[s.clone()]` or reorder.
- **Class 2 — mutate-a-per-call-clone.** `grep -rn` for closure bodies with an assignment
  to a free local (`ident := ` / `ident +=` / `ident.field :=` where `ident` is not a
  closure parameter). Under RFC-0006 these mutated a discardable clone; now they need
  `[ident] var` and the write persists. Each is a semantic change to review by hand.
- **Class 3 — `&var` capture used read-only.** Once `[&var x]` syntax lands: any
  `[&var x]` closure whose body has no write / `&var`-use of `x` → change to `[&x]`.
  Measured 2026-09-01: ~6 reader closures in the pointer-sharing fixtures
  (`evaluator/functions/67`–`70`, `evaluator/closures/75`).
- **Exclude:** fixtures relying on the not-yet-enforced `[&var x]` borrow-freeze (two live
  `[&var x]` closures, a write to `x` while one is live) — those are ill-formed by
  RFC-0050 RQ1 and only valid as `expected-error` fixtures once RFC-0122 lands.

Sizing: literal `[&var x]` sites in the corpus today = 0 (syntax not landed); class-2
candidates are enumerable by the grep above; class-1 count comes from running the checks.

## Consequences

- The implementation PR has one enumerated surface (§3), a pinned runtime shape (§2), a
  settled flag question (§1), allocated codes (§4), and a sweep recipe (§5). It should not
  need to reopen any of these mid-build.
- The always-on/opt-in split (§1) is a temporary asymmetry. It is recorded here so that
  metel-core#267 (move checking default-on) knows the closure checks are already
  unconditional and does not try to "enable" them.
- The RFC bodies stay design-only. This ADR is cited from a one-line Implementation
  Guidance pointer in RFC-0153 and RFC-0050; it is not normative for the *language*, only
  for the build.
- `spec/functions.md`'s Closures section and RFC-0006's body are rewritten in this same
  PR (RFC-0006 is `spec_status: pending`), so the reference spec stops lagging the
  accepted design.
