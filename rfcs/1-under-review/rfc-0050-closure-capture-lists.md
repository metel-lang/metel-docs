---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
status: under-review
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/803'
---

> **Correction pass, 2026-08-31.** Applied the rewrite the 2026-08-23 note below said
> was needed but recorded rather than performed, plus a syntax refresh:
>
> - **`move` half rewritten off `linear`.** `move` no longer produces a `linear
>   fun(...) -> T` "must be called exactly once" closure. It is ordinary affine
>   move-into-closure (RFC-0071, settled and implemented): the outer binding is
>   consumed at capture, and the resulting closure is call-once (`once`) or reusable
>   (`many`) per **RFC-0134 §2's `call_multiplicity`**, decided by whether the body
>   consumes the moved-in capture. "Linear values cannot be clone-captured" becomes
>   "a non-`Copy` binding the body uses must be `move`, `&`, or `&var` — not bare
>   clone." Timing Recommendation retargeted: `move` is blocked on **RFC-0134**
>   (`2-accepted`), not on "the rest of the linear-types tower."
> - **Syntax refresh.** `&mut` → `&var` in the grammar; `*mut T`/`*T` → `&var T`/`&T`
>   throughout Semantics (RFC-0067a (`4-implemented`), supersedes RFC-0043); `=`
>   initializers → `:=` in every example (RFC-0136, implemented). Dangling "see
>   RFC-0046" (`6-refused`) pointers for `move` semantics removed.
> - **Cross-refs.** RFC-0134 is `2-accepted` (was cited as `1-under-review`). Added a
>   note on composing the `[captures]` prefix with RFC-0154's function-literal
>   spelling.
>
> No change to the `&var`/`&`/clone design, the exhaustiveness rule, or any Resolved
> Question. The `&var`/`&`/clone half is unblocked on RFC-0067a and ready per the
> Suggested Order; only `move` still waits (now on RFC-0134).

*Updated 2026-07-07 against the split model: the bracket-syntax conflict with region/allocator
parameters no longer applies (RFC-0063/0065 dropped bracket syntax for allocators); the `&var`
and `move` halves now have independent timing, since only `move` depends on linear types; and an
implementation-guidance section was added covering how to build captures so structural records
and brand types don't force a rewrite later. See Timing Recommendation and Implementation
Guidance below.*

> **A draft successor exists, 2026-08-13.** RFC-0134 (Closure Call Capability) proposes an
> answer to the type-level question this RFC's `move` half depends on — but scoped narrower
> than what the Timing Recommendation below anticipated: it treats "does calling a closure
> consume a capture" as an ordinary affine question, not a linear one, specifically to avoid
> waiting on the rest of the linear-types tower.

> **Correction, 2026-08-23: the "Open Question 1" cited above no longer exists as an open
> item, and the answer it settled cuts against this section's own framing, not just past
> it.** RFC-0134 reached `1-under-review` and its Open Questions section now reads "None
> blocking" — the affine-vs-linear choice was resolved as **"Decision: affine `once`, not
> linear"**, with a stated reopening condition, not left open for this RFC to answer. That
> decision is a real mismatch with this section's own text, not a gap in it: `move`'s
> design here is written throughout in terms of a **linear** binding and a `linear
> fun(...) -> T` closure type (see the `Semantics` subsection below), the exact vocabulary
> RFC-0046 used and RFC-0134 explicitly declined to adopt. This also lines up with a
> separate, independently-reached finding from the same day (the RFC-0032 fix,
> `metel-docs-internal`): `linear struct`/`linear enum` never materialized as a language
> construct at all — RFC-0071 (accepted, implemented) is the settled ownership model, and
> it is affine (`Copy`/`Drop` aspects), not linear. Two unrelated investigations landing on
> the same conclusion the same day is worth treating as real signal, not coincidence.
>
> **What this likely means, stated as a finding for whoever resolves it, not decided
> here:** `move ident` plausibly needs nothing more than ordinary affine move-into-closure
> (already-implemented RFC-0071 semantics — the outer binding is consumed, using it after
> is a compile error, exactly as written below) plus RFC-0134's `call_multiplicity` axis,
> inferred from whether the closure body consumes the moved-in capture, to determine
> whether the resulting closure is call-once (`once`) or reusable (`many`) — replacing
> "has type `linear fun(...) -> T`: it must be called exactly once" with "has
> `call_multiplicity: once`, per RFC-0134 §2, if its body consumes the capture." That is a
> real rewrite of this subsection's substance, not a status update, so it is recorded here
> as what the evidence points to rather than applied to the text below.

*Updated again 2026-07-07: capture lists are now exhaustive. A bare `ident` specifier captures
by value (clone), and once a closure has a capture list at all, every free variable it references
must appear in it — no more silent, unlisted clone captures alongside explicit `&var`/`move`
items. This was previously deferred (see the old "Exhaustive capture lists" alternative, now
adopted below) and is what makes the capture list a complete, checkable field list for the
closure's captured-environment aggregate — see Implementation Guidance.*

*Updated a third time 2026-07-07: read-only reference captures (`&ident`), previously deferred,
are now included — see the Semantics section. "Free variable," for exhaustiveness purposes, is
clarified to mean outer-scope local bindings only; references to module-level functions,
constants, types, and aspects are name resolution, not capture, and never need to appear in the
list.*

> **Status — under review (2026-08-23; correction pass 2026-08-31, see frontmatter note).** Zero remaining open questions in its own ledger -- all 6 Resolved Questions checked. Split readiness: &var/&/clone ready per its own Suggested Order (unblocked on RFC-0067a); move blocked on RFC-0134 landing (`2-accepted`) -- #803

## Summary

Add an optional capture list syntax to closure expressions. The capture list supports four specifiers: `&var ident` captures a binding by mutable reference, enabling a closure to mutate outer-scope state without a separate `&var` reference binding; `&ident` captures a binding by read-only reference, avoiding a clone for values that are only read; `move ident` transfers ownership of a non-`Copy` binding into the closure (ordinary affine move — RFC-0071); bare `ident` captures by value (clone). All four may appear in the same list. Once a closure has a capture list at all, it must be exhaustive — every free variable the closure body references, where "free variable" means an outer-scope local binding (not a module-level function, constant, type, or aspect), must appear in it. All captures are explicit at the closure definition site.

A closure with a `move` capture is call-once (`once`) or reusable (`many`) per RFC-0134 §2's `call_multiplicity`, decided by whether the body consumes the moved-in capture — not a distinct `linear fun` type. See Semantics and the Timing Recommendation.

---

## Motivation

Closures in Metel currently capture all outer bindings by value (deep clone at creation time). To share mutable state between a closure and its enclosing scope, the programmer must explicitly declare a `&var` reference binding in the outer scope before the closure is defined:

```metel
fun main() {
    var count := 0;
    let p: &var i64 := &var count;   // extra binding required

    let inc := () -> () { *p += 1; };
    inc();
    inc();
    // count is now 2
}
```

This pattern works but carries a cost: `p` is a binding whose sole purpose is to outlive the closure capture window. It adds a name to the scope that has no semantic value beyond enabling the share, and it distances the expression of intent (mutation of `count`) from the place where it matters — the closure definition.

An attempt to take `&var count` inside the closure body does not work — the closure's captured environment is a deep clone, so the reference targets the copy, not the original binding. This is a non-obvious gotcha that the current documentation has to explain at length. Tests 72–74 in `tests/evaluator/sources/closures/` confirm and document this behaviour.

A capture list allows the programmer to declare the mutable capture at the closure site, eliminating the extra binding and making the intent legible without sacrificing explicitness.

---

## Proposal

Extend the closure expression syntax with an optional capture list placed before the parameter list:

```
closure_expr  = capture_list? "(" params ")" "->" return_type? block
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&var" ident | "&" ident | "move" ident | ident
```

*(The base closure-literal spelling — `(params) -> ret block` vs. RFC-0154's proposed
`|params| body` — is RFC-0154's to settle. The `[captures]` prefix composes ahead of
whichever it is: `[&var count] |req| { … }` under RFC-0154, `[&var count] (req: Request)
-> Response { … }` today. Examples below use the current form.)*

`&var ident` captures a binding by mutable reference. `&ident` captures a binding by read-only reference — the value is not cloned, but the closure may not write through it. `move ident` transfers ownership of a binding into the closure by an ordinary affine move (RFC-0071); it is how a non-`Copy` value that the body will consume gets into a closure. A bare `ident` captures by value (clone) — the same behavior closures have always had for unlisted bindings, just now written explicitly. All four specifiers may appear in the same list: `[&var count, &config, move buf, log_prefix]`.

Bindings named with `&var` in the capture list are captured by mutable reference rather than by value. Inside the closure body they are used with ordinary read and assignment syntax — no explicit dereference required:

```metel
fun main() {
    var count := 0;

    let inc := [&var count] () -> () {
        count += 1;
    };

    inc();
    inc();
    assert(count == 2);
}
```

`&ident` exists for the same reason `&var ident` does: avoiding a cost the clone-capture default imposes unnecessarily. A large read-only structure that a closure only reads doesn't need to be cloned into it:

```metel
fun main() {
    let config: Config := Config::load();   // large struct, read-only in the closure below

    let handle := [&config] (req: Request) -> Response {
        route(req, config)   // reads through the reference; no clone at closure-creation time
    };

    handle(req_a);
    handle(req_b);
}
```

If a closure has no capture list at all, every free variable it references continues to be captured by value (deep clone) implicitly — the RFC-0006 default, unchanged for the common case where nothing needs `&var`, `&`, or `move`. (A closure with no list that references a non-`Copy`, non-`Clone` binding is already an error today, independent of this RFC — there is nothing to clone; such a binding is exactly the case `move` or `&`/`&var` exists for.)

If a closure *does* have a capture list, that list must be exhaustive: every free variable the closure body references must appear in it, with the specifier matching how it's used. "Free variable" means an outer-scope **local binding** — a `let` binding or function/closure parameter visible in the lexical scope enclosing the closure. It does not include references to module-level functions, constants, types, or aspects: those are resolved by ordinary name resolution regardless of any capture list, and never need to appear in it, since nothing about them is being captured from a stack frame. A closure mixing a mutable capture with an otherwise-ordinary clone capture now looks like:

```metel
fun main() {
    var count := 0;
    let log_prefix := "counter: ";

    let inc := [&var count, log_prefix] () -> () {
        count += 1;
        print(log_prefix + count.to_string());   // `print` is a module-level function, not a free variable
    };

    inc();
}
```

Referencing a free local binding that is not in the list — of any kind, including ones that would only need clone capture — is a compile error once the closure has a capture list at all. References to module-level items are unaffected.

### Semantics

**`&var` captures:**
- At closure creation time, each `&var ident` capture takes `&var ident` and stores the resulting `&var T` in the closure's captured environment.
- Inside the closure body, reads and writes of the binding are automatically routed through the stored reference. The programmer never sees an explicit dereference.
- The outer binding must be declared `var`. Attempting to capture a non-`var` binding via `&var` is a compile error.

**`&` (read-only reference) captures:**
- At closure creation time, each `&ident` capture takes `&ident` and stores the resulting `&T` in the closure's captured environment. No clone occurs.
- Inside the closure body, reads of the binding are automatically routed through the stored reference. The programmer never sees an explicit dereference, and cannot write through it — assigning to a `&`-captured binding inside the closure body is a compile error, the same rule that applies to any `&T` value outside a closure.
- Unlike `&var`, the outer binding does not need to be declared `var` — `&ident` is valid for any addressable binding, matching `&x`'s existing rules outside of closures (RFC-0067a).

**`move` captures:**
- At closure creation time, each `move ident` capture transfers ownership of the named binding into the closure's environment. This is an **ordinary affine move** (RFC-0071, settled and implemented): the outer binding is consumed at closure creation, and using it after is a compile error — the same rule as `let y := x;` for any non-`Copy` `x`.
- A closure with any `move` capture is **not** a distinct `linear fun` type. Its call-count capability — `once` (call-once) or `many` (reusable) — is determined by **RFC-0134 §2's `call_multiplicity`**: if some conservatively-reachable path through the body consumes a moved-in (or bare-clone) non-`Copy` capture, the closure is `once` and a second call is rejected as use of a moved value; otherwise it is `many`. A `move`d capture that the body only *reads* leaves the closure `many`.
- A non-`Copy` binding the closure body references and that is **not** listed with `move`, `&`, or `&var` is a compile error — a non-`Copy` value cannot be bare-clone-captured (there is nothing to clone). It is not "linear"; it is ordinary affine, and `move`/`&`/`&var` is how a closure takes it.
- `move` capture is **not** implementable until RFC-0134 lands (`2-accepted`); it supplies the `call_multiplicity` axis above. See the Timing Recommendation.

**Bare `ident` (clone) captures:**
- At closure creation time, each bare `ident` capture deep-clones the named binding into the closure's captured environment — identical to today's implicit RFC-0006 capture, just named explicitly.
- Any binding whose value is cloneable (`Copy`, or `Clone`) and which the closure body reads without mutating through it or moving it can use this form; `&ident` is usually preferable for large values purely to avoid the clone, but both are legal.

**All four:**
- A binding may not appear more than once across the capture list (no dual capture of the same name under different kinds).
- **Exhaustiveness.** A closure with no capture list retains the RFC-0006 default: every free local binding is implicitly clone-captured. A closure *with* a capture list must enumerate every free local binding it references — there is no partial mode where some captures are explicit and others are silently implicit. Module-level functions, constants, types, and aspects are never "free variables" for this rule (see Proposal); only outer-scope `let` bindings and parameters count. This closes a gap in the original design, where `[&var count]` could coexist with other, unlisted clone-captured variables in the same closure; see Implementation Guidance for why this matters beyond ergonomics.

---

## Historical: Conflict with Region Syntax (resolved, no longer applicable)

*This section described a real conflict against the pre-split "Region Handles" version of
RFC-0063, which used `[region]` bracket syntax for region parameters on closures. It is kept
here for the record; it no longer applies to the current design.*

The original concern: RFC-0063/0065 appeared to introduce allocator/region parameters on
closures using the same bracket position this RFC uses for capture lists (`[region]()` vs.
`[&var count]()`), which would have been ambiguous or required one of three disambiguation
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

### Keep requiring an outer `&var` reference binding (status quo)

Works today. Verbose, non-obvious, and puts a semantically empty binding in the outer scope. Rejected as the permanent answer given the ergonomic cost.

### Allow `&var ident` inside the closure body

Syntactically simple but does not work under the current capture semantics — the closure holds a deep-cloned copy, so the internal reference targets the copy, not the original. Making it work would require abandoning deep-clone capture entirely or adding a special case that distinguishes "address-of a captured binding" from "address-of a local binding", both of which are more invasive than a capture list.

### Implicit mutable capture

Allow closures to detect at analysis time that a captured binding is assigned and automatically capture it by reference. Rejected: breaks the design principle that mutation is always explicit in Metel, and makes closure behaviour harder to reason about from the definition site alone.

### Exhaustive capture lists

*Adopted 2026-07-07 — see the Semantics section above.* Originally considered and deferred:
require every captured binding to appear in the list, with `&var`, `move`, or by-value markers.
The concern at the time was boilerplate for the common case where most captures are read-only
values. That concern is addressed by scoping exhaustiveness to closures that already have a
capture list — a closure with no `&var`/`move` need still writes no list at all and keeps full
implicit clone-capture, so the common case pays nothing. What changed the calculus: once a
closure has a list, allowing some captures to stay implicit means the list is no longer a
reliable field enumeration for the closure's environment, which undermines treating that
environment as a checkable aggregate (see Implementation Guidance). Adopting exhaustiveness only
for closures that opt into a list at all gets both properties — no boilerplate tax on the common
case, and a trustworthy field list wherever a capture list exists.

---

## Resolved Questions

1. **Lifetime of the mutable reference. ✓ Resolved** — In the interpreter, the outer binding's storage is heap-backed so there is no unsoundness. Under a future compiler, a closure holding `&var` (or `&`) to a stack binding must not outlive that binding. Precise enforcement defers to the borrow checker. No interpreter-level restriction is imposed now.

2. **Interaction with concurrency. ✓ Resolved** — `&var T` and `&T` (RFC-0067a) are not `Send` (RFC-0003's `Send` marker aspect; the original citation of RFC-0028 no longer applies — that RFC is refused). A closure is `Send` only if all its captured values are `Send`. Any `[&var x]` or `[&x]` closure is therefore automatically non-`Send` — no new rule needed; falls out of the existing model. Once RFC-0067 lands and adds lifetime anchors (`&r var T`/`&r T`), this should be restated in terms of whatever `Send` rule RFC-0067/RFC-0074 give anchored references — not yet specified, tracked as a residual, not a blocker.

3. **Multiple closures capturing the same binding. ✓ Resolved** — Two closures with `[&var x]` both hold a mutable reference to `x`. This is safe in the single-threaded interpreter (sequential calls; aliased mutation is not concurrent). Under the borrow checker, at most one live mutable reference at a time (or many live `&x` read-only references, exclusive of any `&var x`) will be enforced. Document now; restrict later.

4. **Syntax. ✓ Re-resolved** — `[&var x]` was confirmed jointly with RFC-0046. RFC-0063's
   pre-split "Region Handles" draft briefly introduced `[region]` in the same position,
   creating a conflict (see the Historical section above), but the split-model rewrite of
   RFC-0063/0065 dropped bracket syntax for allocator parameters (`@[r]` → `@`) before this
   RFC reached implementation. `[...]` is unambiguously capture-list syntax; no grammar
   change is needed.

5. **Read-only reference captures. ✓ Resolved (2026-07-07)** — Originally deferred on the
   grounds that clone capture "already handles the immutable case adequately." Adopted instead:
   clone capture handles correctness but not cost — a large read-only value captured by many
   closures pays a full deep clone per closure for no reason, symmetric to why `&var` was added
   over the `&var` reference-binding workaround in the first place. `&ident` closes that gap using
   exactly the existing `&x` → `&T` rule (RFC-0067a); no new addressing mechanism was needed,
   only exposing it as a capture-list specifier.

6. **Scope of "free variable" for exhaustiveness. ✓ Resolved (2026-07-07)** — Only outer-scope
   local bindings (`let` bindings and parameters visible in the closure's enclosing lexical
   scope) count. Module-level functions, constants, types, and aspects are resolved by ordinary
   name resolution and are never subject to the capture list or its exhaustiveness rule — nothing
   about them is being captured from a stack frame, so there is nothing for the list to enumerate.

---

## Timing Recommendation

*Superseded 2026-07-07: the original recommendation below tied the entire RFC — including
`&var`/`&`/clone captures, which have no linear dependency — to linear types landing first,
because it was written jointly with RFC-0046 before the split model existed. `move` now has
independent timing from the other three.*

*Updated again 2026-07-07: RFC-0067 has since been split. Its allocator/borrow-checker
independent slice — the plain `&T`/`&var T` rename — is now accepted separately as **RFC-0067a**
and sequenced into Cluster A, removing the mechanical-rename concern below entirely: `&var`/`&`
captures can target RFC-0067a's syntax directly instead of today's `*mut T`/`*T`, with no
rename step to schedule around.*

*Retargeted 2026-08-31: `move`'s blocker is now RFC-0134 (`2-accepted`), not "the
linear-types tower." RFC-0134 decoupled the "does calling a closure consume a capture"
question from linear types by answering it as an ordinary affine one — so `move` needs
only RFC-0071 (settled) + RFC-0134's `call_multiplicity`, both concrete, not RFC-0028's
tower.*

**`&var`, `&`, and bare `ident` (clone) captures** have no dependency on linear types,
allocators, brands, or RFC-0134. Their only prerequisite is RFC-0067a (`4-implemented`,
Cluster A — `&T`/`&var T` with no anchors, no allocator interaction). Bare `ident` has no
reference representation at all. These three are implementable now.

**`move` captures** are blocked only on **RFC-0134 (`2-accepted`)** landing. RFC-0046,
which originally specified `move` in `linear fun` / exactly-once terms against the old
unified `Region` model, is refused (`6-refused/`); its framing is not the one to inherit.
The replacement is small and already accepted in outline: `move` is an ordinary affine
move into the captured-environment aggregate (RFC-0071), and RFC-0134 §2's
`call_multiplicity` decides whether the resulting closure is `once` or `many`. Nothing in
`move` waits on RFC-0028's linear-types tower.

**Suggested order:** implement `&var`/`&`/clone now against RFC-0067a; implement `move`
once RFC-0134 lands.

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
  capture kind (`&var`/`move`/clone) known statically from the specifier. Without exhaustiveness,
  some fields would exist in the runtime environment without appearing anywhere in the syntax,
  which is exactly the kind of implicit state that would need discovering and reconciling by hand
  when records or brand-based escape checking arrive.
- **Escape checking.** Whatever the split model uses to check that an allocator/lifetime-tagged
  value doesn't escape its scope should be written as a generic check over an aggregate's field
  types, not as bespoke closure logic. A `[&var count]` or future `[move buf]` closure is then
  covered automatically because its captured environment *is* an aggregate, with nothing
  closure-specific to revisit if brand-kind unification later generalizes escape checking.
- **`move` and `call_multiplicity`, when RFC-0134 lands.** Do not implement a distinct
  `linear fun` type. RFC-0134 §2's `call_multiplicity` (`once`/`many`) is derived from the
  captured-environment aggregate: the closure is `once` iff some conservatively-reachable
  path through the body moves a non-`Copy` field of that aggregate out. This is the same
  move-tracking the checker already runs on any body, applied to the closure's capture
  aggregate as its place — closure `move` capture and ordinary partial move of a struct
  become one mechanism on two syntactic forms, not two features to reconcile later.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0041: Lambda Syntax for Anonymous Functions — the base closure-literal spelling
- RFC-0154: Pipe Notation for Closures and Function Types (`1-under-review`) — proposes
  `|x| body` for the literal; the `[captures]` prefix composes ahead of whichever base
  spelling settles
- RFC-0043: Regular Pointers and Mutable Pointers — **superseded by RFC-0067a**
- Closure capture tests: `tests/evaluator/sources/closures/72_closure_internal_ptr_no_outer_effect.mtl`, `73_closure_direct_assign_no_outer_effect.mtl`, `74_closure_external_ptr_affects_outer.mtl`
- RFC-0046: Linear Closure Capture — **refused** (`6-refused/`); specified `move` in
  `linear fun` / exactly-once terms against the old unified `Region` model. Not the framing
  to inherit — RFC-0134 (affine) is the successor.
- RFC-0134: Closure Call Capability (`2-accepted`, 2026-08-30) — supplies `call_multiplicity`
  (`once`/`many`), the affine (not linear) answer this RFC's `move` half needs. `move` is
  blocked on it landing; see Timing Recommendation.
- RFC-0071: Ownership and Move Semantics (`3-integrated`) — the settled affine ownership
  model; `move` capture is an ordinary move into the captured-environment aggregate under it.
- RFC-0063: Allocator Handles (`2-accepted`, retitled from "Region Handles" in the 2026-07-05
  split-model rewrite) — no longer uses bracket syntax for allocator parameters; see Historical
  section above.
- RFC-0065: Allocator Ergonomics (`2-accepted`, retitled from "Region Ergonomics") — no
  longer affects this RFC's bracket syntax.
- RFC-0067a: Reference Types (`4-implemented`, split from RFC-0067 2026-07-07) — supersedes
  RFC-0043's `*mut T`/`*T` with `&var T`/`&T`; the only prerequisite for the `&var`/`&`/clone half.
- RFC-0067: Lifetime Anchors (`1-under-review`) — adds
  `&r var T`/`&r T` on top of RFC-0067a; see Timing Recommendation above for sequencing.
- `reports/implementation/roadmap-2026-07-07.md` — phased sequencing this RFC's two halves fit
  into.
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
