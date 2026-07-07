---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
---

*Updated 2026-07-07 against the split model: the bracket-syntax conflict with region/allocator
parameters no longer applies (RFC-0063/0065 dropped bracket syntax for allocators); the `&mut`
and `move` halves now have independent timing, since only `move` depends on linear types; and an
implementation-guidance section was added covering how to build captures so structural records
and brand types don't force a rewrite later. See Timing Recommendation and Implementation
Guidance below.*

*Updated again 2026-07-07: capture lists are now exhaustive. A bare `ident` specifier captures
by value (clone), and once a closure has a capture list at all, every free variable it references
must appear in it — no more silent, unlisted clone captures alongside explicit `&mut`/`move`
items. This was previously deferred (see the old "Exhaustive capture lists" alternative, now
adopted below) and is what makes the capture list a complete, checkable field list for the
closure's captured-environment aggregate — see Implementation Guidance.*

*Updated a third time 2026-07-07: read-only reference captures (`&ident`), previously deferred,
are now included — see the Semantics section. "Free variable," for exhaustiveness purposes, is
clarified to mean outer-scope local bindings only; references to module-level functions,
constants, types, and aspects are name resolution, not capture, and never need to appear in the
list.*

## Summary

Add an optional capture list syntax to closure expressions. The capture list supports four specifiers: `&mut ident` captures a non-linear binding by mutable reference, enabling a closure to mutate outer-scope state without a separate `*mut` binding; `&ident` captures a non-linear binding by read-only reference, avoiding a clone for values that are only read; `move ident` transfers ownership of a linear binding into the closure (RFC-0046 — refused; a split-model successor is needed, see Timing Recommendation); bare `ident` captures by value (clone). All four may appear in the same list. Once a closure has a capture list at all, it must be exhaustive — every free variable the closure body references, where "free variable" means an outer-scope local binding (not a module-level function, constant, type, or aspect), must appear in it. All captures are explicit at the closure definition site.

---

## Motivation

Closures in Metel currently capture all outer bindings by value (deep clone at creation time). To share mutable state between a closure and its enclosing scope, the programmer must explicitly declare a `*mut` pointer in the outer scope before the closure is defined:

```metel
fun main() {
    let mut count = 0;
    let p: *mut Int = &mut count;   // extra binding required

    let inc = () -> () { *p += 1; };
    inc();
    inc();
    // count is now 2
}
```

This pattern works but carries a cost: `p` is a binding whose sole purpose is to outlive the closure capture window. It adds a name to the scope that has no semantic value beyond enabling the share, and it distances the expression of intent (mutation of `count`) from the place where it matters — the closure definition.

An attempt to take `&mut count` inside the closure body does not work — the closure's captured environment is a deep clone, so the pointer targets the copy, not the original binding. This is a non-obvious gotcha that the current documentation has to explain at length. Tests 72–74 in `tests/evaluator/sources/closures/` confirm and document this behaviour.

A capture list allows the programmer to declare the mutable capture at the closure site, eliminating the extra binding and making the intent legible without sacrificing explicitness.

---

## Proposal

Extend the closure expression syntax with an optional capture list placed before the parameter list:

```
closure_expr  = capture_list? "(" params ")" "->" return_type block
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&mut" ident | "&" ident | "move" ident | ident
```

`&mut ident` captures a non-linear binding by mutable reference. `&ident` captures a non-linear binding by read-only reference — the value is not cloned, but the closure may not write through it. `move ident` transfers ownership of a linear binding into the closure (see RFC-0046). A bare `ident` captures by value (clone) — the same behavior closures have always had for unlisted bindings, just now written explicitly. All four specifiers may appear in the same list: `[&mut count, &config, move buf, log_prefix]`.

Bindings named with `&mut` in the capture list are captured by mutable reference rather than by value. Inside the closure body they are used with ordinary read and assignment syntax — no pointer dereference required:

```metel
fun main() {
    let mut count = 0;

    let inc = [&mut count] () -> () {
        count += 1;
    };

    inc();
    inc();
    assert(count == 2);
}
```

`&ident` exists for the same reason `&mut ident` does: avoiding a cost the clone-capture default imposes unnecessarily. A large read-only structure that a closure only reads doesn't need to be cloned into it:

```metel
fun main() {
    let config: Config = Config::load();   // large struct, read-only in the closure below

    let handle = [&config] (req: Request) -> Response {
        route(req, config)   // reads through the reference; no clone at closure-creation time
    };

    handle(req_a);
    handle(req_b);
}
```

If a closure has no capture list at all, every free variable it references continues to be captured by value (deep clone) implicitly — the RFC-0006 default, unchanged for the common case where nothing needs `&mut`, `&`, or `move`.

If a closure *does* have a capture list, that list must be exhaustive: every free variable the closure body references must appear in it, with the specifier matching how it's used. "Free variable" means an outer-scope **local binding** — a `let` binding or function/closure parameter visible in the lexical scope enclosing the closure. It does not include references to module-level functions, constants, types, or aspects: those are resolved by ordinary name resolution regardless of any capture list, and never need to appear in it, since nothing about them is being captured from a stack frame. A closure mixing a mutable capture with an otherwise-ordinary clone capture now looks like:

```metel
fun main() {
    let mut count = 0;
    let log_prefix = "counter: ";

    let inc = [&mut count, log_prefix] () -> () {
        count += 1;
        print(log_prefix + count.to_string());   // `print` is a module-level function, not a free variable
    };

    inc();
}
```

Referencing a free local binding that is not in the list — of any kind, including ones that would only need clone capture — is a compile error once the closure has a capture list at all. References to module-level items are unaffected.

### Semantics

**`&mut` captures:**
- At closure creation time, each `&mut ident` capture takes the address of the named binding (equivalent to `&mut ident`) and stores the resulting `*mut T` in the closure's captured environment.
- Inside the closure body, reads and writes of the binding are automatically routed through the stored pointer. The programmer never sees the pointer explicitly.
- The outer binding must be declared `let mut`. Attempting to capture a non-mutable binding via `&mut` is a compile error.

**`&` (read-only reference) captures:**
- At closure creation time, each `&ident` capture takes the address of the named binding (equivalent to `&ident`) and stores the resulting `*T` in the closure's captured environment. No clone occurs.
- Inside the closure body, reads of the binding are automatically routed through the stored pointer. The programmer never sees the pointer explicitly, and cannot write through it — assigning to a `&`-captured binding inside the closure body is a compile error, the same rule that applies to any `*T` value outside a closure.
- Unlike `&mut`, the outer binding does not need to be declared `let mut` — `&ident` is valid for any addressable non-linear binding, matching `&x`'s existing rules outside of closures (RFC-0043).

**`move` captures:**
- At closure creation time, each `move ident` capture transfers ownership of the named linear binding into the closure's environment. The outer binding is consumed at closure creation — using it after is a compile error.
- A closure with any `move` capture has type `linear fun(...) -> T`: it must be called exactly once (see RFC-0046).
- Linear bindings referenced in the closure body that are not listed with `move` are a type error — linear values cannot be clone-captured.

**Bare `ident` (clone) captures:**
- At closure creation time, each bare `ident` capture deep-clones the named binding into the closure's captured environment — identical to today's implicit RFC-0006 capture, just named explicitly.
- Any non-linear binding the closure body reads (without mutating through it or moving it) can use this form; `&ident` is usually preferable for large values purely to avoid the clone, but both are legal.

**All four:**
- A binding may not appear more than once across the capture list (no dual capture of the same name under different kinds).
- **Exhaustiveness.** A closure with no capture list retains the RFC-0006 default: every free local binding is implicitly clone-captured. A closure *with* a capture list must enumerate every free local binding it references — there is no partial mode where some captures are explicit and others are silently implicit. Module-level functions, constants, types, and aspects are never "free variables" for this rule (see Proposal); only outer-scope `let` bindings and parameters count. This closes a gap in the original design, where `[&mut count]` could coexist with other, unlisted clone-captured variables in the same closure; see Implementation Guidance for why this matters beyond ergonomics.

---

## Historical: Conflict with Region Syntax (resolved, no longer applicable)

*This section described a real conflict against the pre-split "Region Handles" version of
RFC-0063, which used `[region]` bracket syntax for region parameters on closures. It is kept
here for the record; it no longer applies to the current design.*

The original concern: RFC-0063/0065 appeared to introduce allocator/region parameters on
closures using the same bracket position this RFC uses for capture lists (`[region]()` vs.
`[&mut count]()`), which would have been ambiguous or required one of three disambiguation
schemes (sequential brackets, a unified bracket, or moving captures to a `capture(...)`
keyword form).

**Resolution:** RFC-0063's 2026-07-05 rewrite (the "split model," retitled "Allocator
Handles") dropped the bracket channel for allocator parameters entirely — RFC-0065 §1a notes
the change explicitly as `@[r]` → `@`. Allocator/tag parameters are now written with the `@`
prefix directly on the type or value channel, not with `[...]`. `[...]` is therefore
unambiguously reserved for capture lists; no disambiguation scheme is needed, and Resolved
Question 4 below is re-resolved rather than left open.

---

## Alternatives Considered

### Keep requiring an outer `*mut` pointer (status quo)

Works today. Verbose, non-obvious, and puts a semantically empty binding in the outer scope. Rejected as the permanent answer given the ergonomic cost.

### Allow `&mut ident` inside the closure body

Syntactically simple but does not work under the current capture semantics — the closure holds a deep-cloned copy, so the internal pointer targets the copy, not the original. Making it work would require abandoning deep-clone capture entirely or adding a special case that distinguishes "address-of a captured binding" from "address-of a local binding", both of which are more invasive than a capture list.

### Implicit mutable capture

Allow closures to detect at analysis time that a captured binding is assigned and automatically capture it by reference. Rejected: breaks the design principle that mutation is always explicit in Metel, and makes closure behaviour harder to reason about from the definition site alone.

### Exhaustive capture lists

*Adopted 2026-07-07 — see the Semantics section above.* Originally considered and deferred:
require every captured binding to appear in the list, with `&mut`, `move`, or by-value markers.
The concern at the time was boilerplate for the common case where most captures are read-only
values. That concern is addressed by scoping exhaustiveness to closures that already have a
capture list — a closure with no `&mut`/`move` need still writes no list at all and keeps full
implicit clone-capture, so the common case pays nothing. What changed the calculus: once a
closure has a list, allowing some captures to stay implicit means the list is no longer a
reliable field enumeration for the closure's environment, which undermines treating that
environment as a checkable aggregate (see Implementation Guidance). Adopting exhaustiveness only
for closures that opt into a list at all gets both properties — no boilerplate tax on the common
case, and a trustworthy field list wherever a capture list exists.

---

## Resolved Questions

1. **Lifetime of the mutable reference. ✓ Resolved** — In the interpreter, the outer binding's storage is heap-backed so there is no unsoundness. Under a future compiler, a closure holding `&mut` (or `&`) to a stack binding must not outlive that binding. Precise enforcement defers to the borrow checker. No interpreter-level restriction is imposed now.

2. **Interaction with concurrency. ✓ Resolved** — `*mut T` and `*T` (or, targeting RFC-0067a, `&mut T` and `&T`) are not `Send` (RFC-0003's `Send` marker aspect; the original citation of RFC-0028 no longer applies — that RFC is refused). A closure is `Send` only if all its captured values are `Send`. Any `[&mut x]` or `[&x]` closure is therefore automatically non-`Send` — no new rule needed; falls out of the existing model. Once the remaining RFC-0067 lands and adds lifetime anchors (`&r mut T`/`&r T`), this should be restated in terms of whatever `Send` rule RFC-0067/RFC-0074 give anchored references — not yet specified, tracked as a residual, not a blocker.

3. **Multiple closures capturing the same binding. ✓ Resolved** — Two closures with `[&mut x]` both hold a mutable pointer to `x`. This is safe in the single-threaded interpreter (sequential calls; aliased mutation is not concurrent). Under the borrow checker, at most one live mutable reference at a time (or many live `&x` read-only references, exclusive of any `&mut x`) will be enforced. Document now; restrict later.

4. **Syntax. ✓ Re-resolved** — `[&mut x]` was confirmed jointly with RFC-0046. RFC-0063's
   pre-split "Region Handles" draft briefly introduced `[region]` in the same position,
   creating a conflict (see the Historical section above), but the split-model rewrite of
   RFC-0063/0065 dropped bracket syntax for allocator parameters (`@[r]` → `@`) before this
   RFC reached implementation. `[...]` is unambiguously capture-list syntax; no grammar
   change is needed.

5. **Read-only reference captures. ✓ Resolved (2026-07-07)** — Originally deferred on the
   grounds that clone capture "already handles the immutable case adequately." Adopted instead:
   clone capture handles correctness but not cost — a large read-only value captured by many
   closures pays a full deep clone per closure for no reason, symmetric to why `&mut` was added
   over the `*mut` workaround in the first place. `&ident` closes that gap using exactly the
   existing `&x` → `*T` rule (RFC-0043); no new addressing mechanism was needed, only exposing it
   as a capture-list specifier.

6. **Scope of "free variable" for exhaustiveness. ✓ Resolved (2026-07-07)** — Only outer-scope
   local bindings (`let` bindings and parameters visible in the closure's enclosing lexical
   scope) count. Module-level functions, constants, types, and aspects are resolved by ordinary
   name resolution and are never subject to the capture list or its exhaustiveness rule — nothing
   about them is being captured from a stack frame, so there is nothing for the list to enumerate.

---

## Timing Recommendation

*Superseded 2026-07-07: the original recommendation below tied the entire RFC — including
`&mut`/`&`/clone captures, which have no linear dependency — to linear types landing first,
because it was written jointly with RFC-0046 before the split model existed. `move` now has
independent timing from the other three.*

*Updated again 2026-07-07: RFC-0067 has since been split. Its allocator/borrow-checker
independent slice — the plain `&T`/`&mut T` rename — is now accepted separately as **RFC-0067a**
and sequenced into Cluster A, removing the mechanical-rename concern below entirely: `&mut`/`&`
captures can target RFC-0067a's syntax directly instead of today's `*mut T`/`*T`, with no
rename step to schedule around.*

**`&mut`, `&`, and bare `ident` (clone) captures** have no dependency on linear types,
allocators, or brands. Their only prerequisites are RFC-0043 (already implemented) or, once it
lands, RFC-0067a (accepted, Cluster A — `&T`/`&mut T` with no anchors, no allocator
interaction). Target RFC-0067a's syntax rather than RFC-0043's `*mut T`/`*T` if sequencing this
RFC after it; both are implementable in the same Cluster-A timeframe, so there's no reason to
prefer one over the other except avoiding a later rename. Bare `ident` has no pointer
representation to rename at all, in either case.

**`move` captures** remain blocked. RFC-0046, which specified `move`'s semantics (`linear fun`,
consume-at-capture, single-call safety), is refused — not merely on hold — because it was
written entirely in terms of the old unified `Region` model (cites RFC-0025, RFC-0028,
RFC-0051, all now in `5-refused/`). `move` capture needs a split-model successor to RFC-0046
before it can be implemented. That successor is not yet written and is properly a Stage B
concern (see `reports/implementation/roadmap-2026-07-07.md`), alongside the rest of the
linear-types tower.

**Suggested order:** implement the `&mut`/`&`/clone three of this RFC now, targeting RFC-0067a's
`&T`/`&mut T`; implement `move` once a split-model successor to RFC-0046 exists and linear types
have a settled design.

---

## Implementation Guidance: Build Captures as Aggregates, Not a Closure-Specific Mechanism

*Added 2026-07-07.* Structural records and brand types are both expected in later stages (see
`reports/substructural-types/` and `reports/strategy/integrated-language-overview-2026-07-07.md`).
Neither is a dependency of this RFC, but the implementation should be shaped so that neither
forces a rewrite of closure capture when they land:

- **Representation.** Store a closure's captured bindings as a plain closed, named-field
  aggregate — the same shape as struct field storage — not a bespoke closure-environment type.
  Structural records, when they land, are closed field-lists of the same shape; if the
  representation already matches, records can describe or subsume it without a runtime rewrite.
  Exhaustiveness (see Semantics) is what makes this more than aspirational: when a closure has a
  capture list, that list *is* the complete field list of the aggregate, with each field's
  capture kind (`&mut`/`move`/clone) known statically from the specifier. Without exhaustiveness,
  some fields would exist in the runtime environment without appearing anywhere in the syntax,
  which is exactly the kind of implicit state that would need discovering and reconciling by hand
  when records or brand-based escape checking arrive.
- **Escape checking.** Whatever the split model uses to check that an allocator/lifetime-tagged
  value doesn't escape its scope should be written as a generic check over an aggregate's field
  types, not as bespoke closure logic. A `[&mut count]` or future `[move buf]` closure is then
  covered automatically because its captured environment *is* an aggregate, with nothing
  closure-specific to revisit if brand-kind unification later generalizes escape checking.
- **`move` and linear consumption, when Stage B lands.** Implement "is this closure `linear
  fun`" as a derived fact — the captured-environment aggregate has an outstanding unconsumed
  linear field — using the same per-field consumption mechanism adopted for partial consumption
  of a linear struct (RFC-0063 §9 item 5's eventual resolution). This treats linear closure
  capture and linear struct partial-consumption as one mechanism applied to two syntactic forms,
  rather than two features designed separately that later need reconciling.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0041: Lambda Syntax for Anonymous Functions
- RFC-0043: Regular Pointers and Mutable Pointers
- Closure capture tests: `tests/evaluator/sources/closures/72_closure_internal_ptr_no_outer_effect.mtl`, `73_closure_direct_assign_no_outer_effect.mtl`, `74_closure_external_ptr_affects_outer.mtl`
- RFC-0046: Linear Closure Capture — **refused** (`5-refused/`); specified `move`'s semantics
  (`linear fun` type, consume-at-capture) against the old unified `Region` model. A split-model
  successor is needed before `move` capture can be implemented — see Timing Recommendation above.
- RFC-0063: Allocator Handles (`1-under-review`, retitled from "Region Handles" in the 2026-07-05
  split-model rewrite) — no longer uses bracket syntax for allocator parameters; see Historical
  section above.
- RFC-0065: Allocator Ergonomics (`1-under-review`, retitled from "Region Ergonomics") — no
  longer affects this RFC's bracket syntax.
- RFC-0067a: Reference Types (`2-accepted`, split from RFC-0067 2026-07-07) — supersedes
  RFC-0043's `*mut T`/`*T` with `&mut T`/`&T`; no anchors, no dependency on this RFC's timing.
- RFC-0067: Lifetime Anchors and Allocator-Pointer References (`1-under-review`) — adds
  `&r mut T`/`&r T` on top of RFC-0067a; see Timing Recommendation above for sequencing.
- `reports/implementation/roadmap-2026-07-07.md` — phased sequencing this RFC's two halves fit
  into.
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
