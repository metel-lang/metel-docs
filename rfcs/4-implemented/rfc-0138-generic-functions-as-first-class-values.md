---
id: rfc-0138
title: "Generic Functions as First-Class Values"
date: '2026-08-24'
status: implemented
target:
updated: '2026-08-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/736'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/736'
impl_status: implemented
coverage:
  "1": { spec: "spec.functions.first-class-functions.legality-2" }
  "2": { kind: untestable, reason: "Internal representation choice (which TypedExpr node backs a bare reference) -- not itself specified, observable behavior." }
  "3": { kind: untestable, reason: "Internal runtime-representation rationale, not a separate behavioral claim from legality-2." }
  "4": { spec: "spec.functions.first-class-functions.legality-2" }
  "5": { kind: untestable, reason: "Rationale for what stays out of scope (rank-2 polymorphism, standalone turbofish-without-call) -- not a specified behavior, a boundary statement." }
---

> **Status — under review (2026-08-27).** Committed to a specific implementation, already underway (metel-core#844), against v0.13.0 -- real engagement, not a schedule bump.

> **Status — accepted (2026-08-27).** Design proven by implementation: all four open questions resolved (see Implementation Notes), full acceptance-criteria coverage (bare reference + higher-order argument, top-level + nested) shipped with passing regression fixtures in metel-core#844.

> **Status — integrated (2026-08-27).** Merged into spec.functions.first-class-functions.legality-2, checked against the rest of the currently-integrated spec; no soundness gap found.

> **Status — implemented (2026-08-27).** metel-core#844 merged to develop; 869+ workspace tests green, clippy/fmt clean. Out-of-scope boundaries (rank-2, standalone turbofish value form) now documented in the spec and covered by regression fixtures (metel-core#845 filed separately for an unrelated pre-existing gap found while adding one of them).

## Summary

`functions.md`'s first-class-functions claim ("named functions and closures are
values of their function type and may be bound, passed as arguments, and returned
as results") has no carve-out for generic functions, but a `<T>`-declared named
function today has no value form at all — not a bare reference, not a higher-order
argument, in any position, fully instantiated or not (metel-core#736). This RFC
proposes closing that gap by extending the mechanism that already exists for
closure let-polymorphism — deferred, per-use-site instantiation from a stored
`TypeScheme`, currently gated on the right-hand side being a syntactic closure
literal — to also recognize a bare reference to an already-declared generic
function.

---

## Motivation

```metel
fun identity<T>(x: T) -> T { return x; }

fun main() -> i64 {
    let alias = identity;     // T0003 undefined name -- `identity` plainly exists
    return alias(3);
}
```

A non-generic function is genuinely first-class today (`let f = add; f(1, 2)`
works). A generic function is call-only: `identity(3)` and
`identity::<i64>(3)` both work, but naming `identity` in any other position —
a bare reference, a higher-order argument (`apply(identity, 3)`), or an
explicit-instantiation-without-calling form (`identity::<i64>`, which is also
a parse error today — the turbofish production is fused to the following call
parens) — fails. `functions.md`'s claim is unqualified; the implementation
doesn't match it.

This is a narrower, more specific gap than the historical let-polymorphism
epic (#10/#290/#295, closed): that work covered a closure *inferred* to be
generic through how its body is used (`let id = fun(x) { x };`), and already
shipped — see `spec.functions.closures` and the `GenericClosure` construction
path below. This RFC is about a function whose generic signature is already
fully known from its own `<T>` declaration, referenced by name rather than
constructed as a literal at the reference site.

### Root cause, traced end to end

Contrary to this RFC's own issue (#736), which locates the gap in
`construction.rs`, **inference already succeeds** for `let alias = identity;`:

- `hoist_fun_decls` (`inference.rs`) binds every top-level function — generic
  or not — into `poly_env` via `ctx.bind_poly`, including a real quantified
  `TypeScheme` for a generic function built from its own signature (no body
  inference needed first, unlike a closure).
- `InferContext::lookup` auto-instantiates a `poly_env` hit with fresh type
  variables on every call. So `identity` resolves fine inside `infer_expr`'s
  `Expr::Ident` arm, for a bare reference exactly the same way it does for a
  call's callee position (`Expr::Call` recurses into the same `infer_expr` on
  its callee).
- What inference does *not* do is re-generalize `alias` itself: the closure
  special case (`infer_decl`'s `Decl::Let` arm) that re-quantifies an
  unannotated let-binding's free variables into a fresh `poly_env` scheme is
  gated on `matches!(&ld.value, Expr::Closure { .. })` — a bare `Expr::Ident`
  RHS never reaches it. `alias` gets bound as one fixed monomorphic
  instantiation of `identity`'s type via the ordinary path instead.

The actual, currently-observed failure is in the **construction** pass
(`construction.rs`), which runs second, over the substitution inference already
solved:

- `ConstructCtx::new` populates its own name→`Type` env (`ctx.env`) from
  `scheme_env` — but only for monomorphic entries (`scheme.quantified_vars.is_empty()`).
  A generic function's scheme is deliberately excluded, exactly as the
  `GenericClosure` construction comment states for the closure case: *"the
  name stays absent from `ctx.env` so call sites use `scheme_env`
  instantiation in `construct_call`."*
- `ConstructCtx::lookup` (a plain `ctx.env` scan, no `scheme_env` fallback) is
  what `construct_expr`'s `Expr::Ident` arm calls. For `identity`, this
  correctly finds nothing — by the design above — and the arm has no
  fallback to `ctx.scheme_env`, so it falls through to `T0003 undefined name`.
  The call-construction path (`construct_call` and the several sites it
  shares the pattern with) does check `ctx.scheme_env` directly, which is why
  `identity(3)` constructs fine: the callee is never routed through the
  generic `Expr::Ident` arm for a direct call.

So: inference's gap is that `alias` doesn't get re-generalized (a latent
correctness issue, currently unobserved because construction fails first);
construction's gap is that a bare `Expr::Ident` referencing a generic
function's `scheme_env` entry has no handling at all, matching neither the
monomorphic env fast path nor the closure-literal special case. Both need to
be closed for a bare reference to be genuinely, reusably polymorphic rather
than either an error or a single frozen instantiation.

---

## Design

### 1. Recognize a generic-function reference, not just a closure literal

Both of the closure-let-polymorphism special cases — `infer_decl`'s
`Decl::Let` arm (inference) and `construct_decl`'s `Decl::Let` arm
(construction) — are currently gated on:

```rust
matches!(&ld.value, Expr::Closure { .. })
```

Widen the condition to also match `Expr::Ident(name, _)` where `name` names an
existing polymorphic scheme (`ctx.poly_scheme(name)` on the inference side,
`ctx.scheme_env.get(name)` on the construction side) with a non-empty
`quantified_vars`. This is a narrow, syntactic RHS-shape check — the same
kind the closure case already uses — not a general expression-position
analysis. It does **not** need to look inside `apply(x)` or any other
non-trivial expression; only `let name = <bare generic function name>;`.

- **Inference side**: skip the ordinary `infer_expr(&ld.value, ...)`
  monomorphic-instantiation result for `alias`'s own binding, and instead
  re-bind `alias` into `poly_env` under the *same* scheme `identity` already
  has (or a renamed copy of it — see below on why a copy, not the same
  scheme object, is what mutual-recursion-safe code already does elsewhere).
  This is strictly simpler than the closure case, which has to *derive* the
  scheme via `generalize()` after solving a freshly-inferred body; here the
  scheme already exists, fully formed, at `identity`'s own declaration.
- **Construction side**: produce a construction-side value node carrying the
  referenced scheme (see §2), and — mirroring the closure case exactly —
  keep `alias` absent from `ctx.env` so `alias`'s own later call and
  higher-order-argument sites resolve through `ctx.scheme_env`, the same as
  `identity`'s did.

### 2. A value node for "reference to a scheme," not just "closure body"

`TypedExpr::GenericClosure` currently carries the closure's own AST
(`params`, `return_type`, `body`) — appropriate for a literal, since the
closure has no separate declared existence to point back to. A named generic
function already has one: it's a top-level (or nested) `FunDecl`, checked
once, with a stable name and (per METEL-187) potentially a `SymbolId`.

Two shapes are viable:

- **(a) Reuse `GenericClosure`**, populating `name: Some(identity)` (a field
  it already carries) and treating a `None` body, or a body reference, as "go
  look this up by name in `scheme_env`/the function table instead of
  interpreting an inline body." Minimal new surface, but overloads a node
  whose other fields (`params`, `return_type`, `body`) don't obviously apply
  to a named function the same way.
- **(b) A new `TypedExpr::GenericFunctionRef { name, ty }` node**, parallel to
  the existing plain `TypedExpr::Ident` but explicitly carrying that this
  name resolves polymorphically through `scheme_env` rather than a concrete
  binding. Keeps the closure-literal and named-function cases textually
  distinct at the one place (interpreter dispatch) that has to know the
  difference, at the cost of one more node variant threaded through
  construction, interpretation, and any exhaustive match over `TypedExpr`.

(b) is likely the better fit — a named generic function is not a closure, and
forcing it through `GenericClosure`'s shape to satisfy an interpreter that
already knows how to call a named function by name (todays's ordinary path
for `identity(3)`) adds indirection without buying anything. This RFC does
not commit to (a) vs (b); it's an implementation-time call once the
interpreter-side dispatch (§3) is worked out concretely, not a decision with
externally-visible consequences either way.

### 3. Runtime representation

The interpreter's existing dispatch for a direct call to a named function
(generic or not) already knows how to find and execute it by name — that
path is untouched by this RFC. What's new is a **value** — something that can
be bound to a variable, stored in a struct field typed `(i64) -> i64`, or
passed to a higher-order parameter — that, when later called, dispatches the
same way.

The natural representation is a closure value whose captured environment is
empty and whose "body" is: call the named function `identity` (dictionary/
generic dispatch resolved the same way a direct call already resolves it,
since — per RFC's own `spec.declarations.aspects.static-dispatch-only` —
this compiler monomorphises rather than using vtables; a generic-function
*value* still needs a call-site-driven, not creation-site-driven,
instantiation, exactly like the existing `GenericClosure` value already
provides for the closure case). No new runtime value kind is needed if the
existing `GenericClosure` runtime representation (however the interpreter
already executes one — this RFC does not need to re-derive that, only extend
what constructs one) already defers instantiation to each call. If it does
not — if it bakes in a single instantiation at closure-value-creation time —
that would already be a latent bug for the existing closure-let-polymorphism
feature (a closure value reused at two different types), independent of this
RFC, and should be checked as a prerequisite rather than assumed.

### 4. Higher-order argument position

`apply(identity, 3)` (the issue's own example) passes `identity` where
`apply`'s own parameter has a concrete, monomorphic function type
(`(i64) -> i64` or similar) — inferred per call site as today, from the
argument's expected type. This is **rank-1** use: `identity` itself stays
polymorphic as a name, but any single occurrence of it as an argument value
is instantiated once, at that call, against whatever the parameter position
expects — exactly parallel to how a bare reference's `let`-binding gets one
instantiation per distinct use of the *alias*, not one global instantiation
shared across every use. This does not require rank-2 polymorphism (a
function parameter that is *itself* still-generic inside the callee body) —
`apply`'s own parameter type is concrete before and after this RFC. The
issue's acceptance criteria list this as a required case; it falls out of
§1's mechanism directly, since inferring an argument expression already goes
through the same `infer_expr`/`Expr::Ident` path a bare reference does — no
separate mechanism is needed for it.

### 5. What stays out of scope

- **A standalone instantiation-without-calling form** (`identity::<i64>` as
  a value, not a call) — currently a parse error (turbofish is fused to a
  following call's parens). Worth its own, separate grammar change if wanted;
  not required for `functions.md`'s claim, which only promises a function is
  a value, not that every explicit-instantiation spelling produces one.
  Tracked here as a known related gap, not part of this RFC's Decision.
- **Rank-2 polymorphism** (a function value whose own parameter position is
  still quantified inside the callee) — not implied by the issue, not
  proposed here.
- **Nested generic functions** (`fun outer() { fun identity<T>(x: T) -> T { ... } identity }`
  as opposed to top-level) — the issue's acceptance criteria explicitly
  requires this to work identically to the top-level case. `hoist_fun_decls`
  already runs per-block (it's how mutual recursion within one block works
  today), so the same `poly_env` binding this RFC relies on for the
  top-level case should already exist at the same scope for a nested
  declaration; this needs confirming during implementation, not a separate
  design.

---

## Relationship to existing RFCs

- **RFC-0041 (Lambda Syntax for Anonymous Functions)** and the historical
  let-polymorphism work it built on (#10/#290/#295) — this RFC extends the
  same `scheme_env`-deferred-instantiation mechanism to a second syntactic
  shape (a bare name) rather than introducing a new one.
- **RFC-0134 (Closure Call Capability)** — adjacent surface (calling a stored
  closure value); this RFC does not depend on it and proposes no change to
  how a *call* through a first-class value works, only to how a *generic
  named function* becomes such a value in the first place.
- **`spec.functions.first-class-functions.legality-2`** — this RFC narrows
  that rule's call-only carve-out to the two cases actually left in scope
  (§5): a bare reference and a higher-order argument are no longer call-only;
  a rank-2 position and a standalone turbofish-without-call value form still
  are.

---

## Out of Scope

See "What stays out of scope" above (§5) for the specific deferred surfaces
(bare turbofish-without-call, rank-2 polymorphism). This RFC is scoped to:
a bare reference, a higher-order-argument use, for both top-level and nested
named generic functions — matching metel-core#736's acceptance criteria
exactly.

---

## Open Questions

All four resolved during implementation (metel-core#844); see "Implementation
Notes" below for how each was actually settled.

1. ~~**`GenericClosure` reuse vs. a new node** (§2) — not resolved here;
   implementation-time call once interpreter dispatch is worked out.~~
2. ~~**Does the existing `GenericClosure` runtime value already defer
   instantiation per call, or bake one in at creation?** (§3) — if the
   latter, that's a pre-existing bug independent of this RFC and should be
   fixed first; this RFC's design assumes per-call deferral either way, so
   it isn't blocked on the answer, only on the fix if the answer is "bakes
   one in."~~
3. ~~**Scheme copy vs. shared reference when re-binding `alias` into
   `poly_env`** (§1) — whether `identity`'s own scheme object can be shared
   directly or must be cloned per alias name to keep quantified-variable
   identity from leaking between them under later renaming/instantiation.
   Existing `bind_poly` call sites already clone `TypeScheme`s on every bind,
   suggesting cloning is the established pattern, not a new decision — flagged
   here for implementation-time confirmation rather than left implicit.~~
4. ~~**Interaction with `#735`'s `ClosureBody::Untyped` runtime scheme
   lookup** — the issue that found this one suspected that lookup's `None`
   branch might be dead code, since nothing upstream currently produces a
   bare generic-function value for it to receive. Once this RFC's mechanism
   exists, that branch may become reachable for the first time; needs
   re-checking against `#735` when this lands, not assumed resolved by
   either issue alone.~~

---

## Implementation Notes (2026-08-27, metel-core#844)

Written after implementation, to record how design questions this RFC left
open were actually settled — not a re-derivation of the Design section
above, which stands as originally proposed.

1. **§2 resolved as neither (a) nor (b) as stated, for the bare-reference
   case — reused `GenericClosure`, but sourced from the referenced
   function's own declaration rather than an inline literal.** A new
   `ConstructCtx::fn_table` (scope-stacked, hoisted top-level in
   `construct_program` and per-block in `construct_block`, mirroring the
   existing local-struct hoist) maps a generic function's name to its own
   `params`/`return_type`/`body`, letting `construct_decl`'s `Decl::Let` arm
   build a `GenericClosure` node for a bare `Expr::Ident` RHS exactly the
   way it already does for a closure literal RHS. No new `TypedExpr`
   variant was needed.
2. **The higher-order-argument case needed neither (a) nor (b) at all.**
   Tracing the evaluator found every top-level function (generic or not) is
   already bound into the runtime environment as a `Value::Callable` at
   program setup (independent of this RFC), and `TypedExpr::Ident`'s
   evaluator arm is a plain, type-agnostic `env.get(name)` that ignores its
   own `ty` field. So `construct_expr`'s `Expr::Ident` arm, given a concrete
   `expected_ty` (from a monomorphic higher-order parameter, or an
   explicitly-annotated `let`), instantiates the reference directly via
   `instantiate_scheme_for_call` — the same helper and bound/assoc-eq/
   neg-bound checks a direct call already runs — and emits an ordinary
   `TypedExpr::Ident`. No `GenericClosure`, no `fn_table` lookup, no new
   runtime representation.
3. **Confirmed: `GenericClosure`'s existing runtime value already defers
   instantiation per call.** Read directly in
   `metel-interpreter/src/evaluator/mod.rs`: evaluating a
   `TypedExpr::GenericClosure` produces `ClosureBody::Untyped(body.clone())`
   with `type_ctx: env.type_ctx.clone()` — re-typechecked per call site, not
   baked in at creation. No prerequisite bug existed.
4. **Resolved implicitly, not by an explicit clone-vs-share decision.**
   The inference-side widening re-generalizes `alias`'s own already-fresh,
   unconstrained auto-instantiation via the same `generalize()` call the
   closure case already used — this naturally produces an independent
   scheme (fresh quantified vars via `generalize`'s own renaming), with no
   separate cloning logic to write.
5. **§735 interaction, checked**: not exercised further here — flagged as a
   follow-up rather than verified end-to-end; `#735`'s own issue should be
   re-checked against this RFC's mechanism directly, not assumed resolved by
   this note.
6. **§5's "nested generic functions... needs confirming during
   implementation" — confirmed working**, via
   `evaluator/generics/104_generic_fn_nested_bare_reference.mtl`: the same
   `fn_table`/`poly_env` mechanism applies unchanged at nested scope.
7. **Scope actually shipped, vs. the RFC's own scope statement**: exactly
   as scoped — a bare reference and a higher-order argument, for both
   top-level and nested generic functions. Both items in "What stays out of
   scope" (§5) — a standalone turbofish-without-call value form, and rank-2
   polymorphism — remain unimplemented and out of scope, unchanged.

---

## References

- metel-core#736 (this RFC's originating issue, including the acceptance
  criteria this RFC's scope is drawn from)
- metel-core#735 (found the gap; see Open Question 4)
- `spec.functions.first-class-functions.legality-2`
- `spec.functions.closures` (the existing closure let-polymorphism mechanism
  this RFC extends)
- historical let-polymorphism work: #10, #290, #295 (closed)

---

## Decision

**Outcome:** Accepted, as scoped in §5 (a bare reference and a higher-order
argument, for both top-level and nested generic functions; rank-2 positions
and a standalone turbofish-without-call form remain out of scope).
Implemented in metel-core#844, tracked end-to-end by metel-core#736.
**Target:** v0.13.0
