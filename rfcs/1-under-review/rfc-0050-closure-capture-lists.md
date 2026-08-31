---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
status: under-review
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/803'
---

> **Correction pass, 2026-08-31.** Two changes: the `move` specifier is **dropped**
> from this RFC, and stale syntax is refreshed.
>
> - **`move` specifier removed.** The first draft of this pass reframed `move` off
>   `linear` as "an ordinary affine move into the closure." Followed through, that
>   reframing removes the specifier's reason to exist: an ordinary affine move has
>   **no keyword** anywhere else in Metel (`let y := x;` consumes `x` with no marker,
>   RFC-0071). A dedicated `move` capture word is only coherent if capture-by-move is
>   *special* — and deciding whether it is means revisiting the closure-capture
>   default itself (RFC-0006's "deep-clone every free variable") and, under it, the
>   `Copy`/`Clone` model Metel adopted from Rust without a written trade-off analysis.
>   That is a larger design question than this RFC, and it has adjacent work already
>   in flight (RFC-0135, Multiplicity for Ordinary Types). This RFC now covers only
>   `&var` / `&` reference captures and the explicit spelling of today's implicit
>   clone capture; **ownership-transfer capture is explicitly out of scope**, deferred
>   to that future RFC. Consequence: nothing in this RFC is blocked on RFC-0134 or
>   RFC-0028 any more — its only prerequisite is RFC-0067a (`4-implemented`), so the
>   whole RFC is implementable now.
> - **Syntax refresh.** `&mut` → `&var` in the grammar; `*mut T`/`*T` → `&var T`/`&T`
>   throughout Semantics (RFC-0067a (`4-implemented`), supersedes RFC-0043); `=`
>   initializers → `:=` in every example (RFC-0136, implemented). Dangling "see
>   RFC-0046" (`6-refused`) pointers removed.
> - **Cross-refs.** Added a note on composing the `[captures]` prefix with RFC-0154's
>   function-literal spelling.
>
> No change to the `&var`/`&`/clone design, the exhaustiveness rule, or any Resolved
> Question.
>
> **The header notes below about `move`'s design — linear vs. affine, an RFC-0046
> successor, RFC-0134 as the blocker — are all superseded by the above: `move` is not
> part of this RFC. They are kept for history.**

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

> **Status — under review (2026-08-23; correction pass 2026-08-31, see frontmatter note).** Zero remaining open questions in its own ledger -- all 6 Resolved Questions checked. `move` specifier dropped 2026-08-31 (ownership-transfer capture deferred to a future RFC); the RFC is now `&var`/`&`/clone only and unblocked on RFC-0067a (`4-implemented`) -- #803

## Summary

Add an optional capture list syntax to closure expressions. The capture list supports three specifiers: `&var ident` captures a binding by mutable reference, enabling a closure to mutate outer-scope state without a separate `&var` reference binding; `&ident` captures a binding by read-only reference, avoiding a clone for values that are only read; bare `ident` captures by value (clone). All three may appear in the same list. Once a closure has a capture list at all, it must be exhaustive — every free variable the closure body references, where "free variable" means an outer-scope local binding (not a module-level function, constant, type, or aspect), must appear in it. All captures are explicit at the closure definition site.

**Out of scope:** *ownership-transfer* capture — moving a binding into a closure so the closure owns it and the outer binding is consumed. An early draft of this RFC had a `move ident` specifier for it; it was dropped (see the frontmatter note and Alternatives) because an affine move needs no keyword elsewhere in Metel, and deciding whether closure capture is the exception requires revisiting RFC-0006's clone-by-default capture model and the `Copy`/`Clone` design underneath it — a separate RFC. Until then, a non-`Copy`, non-`Clone` binding still cannot be captured at all, exactly as today.

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
capture_item  = "&var" ident | "&" ident | ident
```

*(The base closure-literal spelling — `(params) -> ret block` vs. RFC-0154's proposed
`|params| body` — is RFC-0154's to settle. The `[captures]` prefix composes ahead of
whichever it is: `[&var count] |req| { … }` under RFC-0154, `[&var count] (req: Request)
-> Response { … }` today. Examples below use the current form.)*

`&var ident` captures a binding by mutable reference. `&ident` captures a binding by read-only reference — the value is not cloned, but the closure may not write through it. A bare `ident` captures by value (clone) — the same behavior closures have always had for unlisted bindings, just now written explicitly. All three specifiers may appear in the same list: `[&var count, &config, log_prefix]`. There is no specifier for moving a binding into the closure (see Summary, "Out of scope").

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

If a closure has no capture list at all, every free variable it references continues to be captured by value (deep clone) implicitly — the RFC-0006 default, unchanged for the common case where nothing needs `&var` or `&`. (A closure that references a non-`Copy`, non-`Clone` binding — with or without a list — is an error today, independent of this RFC: there is nothing to clone, and this RFC adds no way to move such a value in. `&`/`&var` cover the read and mutate cases; ownership transfer is the deferred question in the Summary.)

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

**Ownership-transfer captures — out of scope:**
- There is no specifier for moving a binding into the closure so the closure owns it and the outer binding is consumed. An early draft had `move ident` for this.
- It was dropped because an affine move needs no keyword anywhere else in Metel (`let y := x;`, `f(x)` both consume `x` unmarked, RFC-0071), so a `move` capture word only makes sense if closure capture is a deliberate exception — and settling that means revisiting RFC-0006's clone-by-default capture model and the `Copy`/`Clone` design under it. That is a separate RFC; see the frontmatter note, Alternatives, and Timing Recommendation.
- Until that RFC: a non-`Copy`, non-`Clone` binding cannot be captured by a closure at all, and a `Clone` binding is always deep-cloned in (never moved). This is exactly today's behavior — this RFC neither improves nor regresses it.

**Bare `ident` (clone) captures:**
- At closure creation time, each bare `ident` capture deep-clones the named binding into the closure's captured environment — identical to today's implicit RFC-0006 capture, just named explicitly.
- Any binding whose value is cloneable (`Copy`, or `Clone`) and which the closure body reads without mutating through it can use this form; `&ident` is usually preferable for large values purely to avoid the clone, but both are legal.

**All three:**
- A binding may not appear more than once across the capture list (no dual capture of the same name under different kinds).
- **Exhaustiveness.** A closure with no capture list retains the RFC-0006 default: every free local binding is implicitly clone-captured. A closure *with* a capture list must enumerate every free local binding it references — there is no partial mode where some captures are explicit and others are silently implicit. Module-level functions, constants, types, and aspects are never "free variables" for this rule (see Proposal); only outer-scope `let` bindings and parameters count. This closes a gap in the original design, where `[&var count]` could coexist with other, unlisted clone-captured variables in the same closure; see Implementation Guidance for why this matters beyond ergonomics.

If a future RFC adds an ownership-transfer specifier, it slots into the same exhaustive list as a fourth capture kind with no change to this rule.

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

### A `move ident` specifier for ownership-transfer capture

*In the RFC from 2026-06 through the first 2026-08-31 correction draft; removed 2026-08-31.*
The list had a fourth specifier, `move ident`, to move a binding into the closure so the
closure owns it and the outer binding is consumed. Its original justification was that such
a closure had type `linear fun(...) -> T` and had to be called exactly once — a real
type-level effect. That justification collapsed: RFC-0071 settled Metel's ownership model as
**affine, not linear**, `linear struct`/`linear fun` never became language constructs, and
RFC-0134 answered "does calling a closure consume a capture" as an ordinary affine question.
With the `linear fun` effect gone, `move ident` reduces to "do an ordinary affine move at
the capture site" — and an ordinary affine move has **no keyword** anywhere else in Metel:
`let y := x;` and `f(x)` both consume `x` unmarked (RFC-0071). A dedicated capture keyword
for it would be inconsistent with the rest of the language.

Keeping it would only be defensible on a *different* ground than the one it was added for —
that a closure outlives its capture site, so a silent capture-by-move is surprising and
deserves a marker (the same principle that rejects *Implicit mutable capture* above). That
may well be right, but it is an argument about the **closure-capture default itself** —
RFC-0006's "deep-clone every free variable," which predates settled move semantics — and
about the `Copy`/`Clone` model Metel took from Rust without a written trade-off analysis.
Both are larger than this RFC. Adjacent work is already open (RFC-0135, Multiplicity for
Ordinary Types). Ownership-transfer capture is therefore deferred to a future RFC that
settles the default; this one is scoped to `&var`/`&`/clone, which stand on their own and
depend only on RFC-0067a.

### Exhaustive capture lists

*Adopted 2026-07-07 — see the Semantics section above.* Originally considered and deferred:
require every captured binding to appear in the list, with `&var`, `&`, or by-value markers.
The concern at the time was boilerplate for the common case where most captures are read-only
values. That concern is addressed by scoping exhaustiveness to closures that already have a
capture list — a closure with no `&var`/`&` need still writes no list at all and keeps full
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

*Retargeted 2026-08-31 (second pass): the `move` specifier is dropped from this RFC
(see the frontmatter note and Alternatives), so there is no longer a blocked half to
sequence. What remains — `&var`/`&`/clone — has one prerequisite, RFC-0067a, which is
`4-implemented`. The RFC is implementable now, in full, with nothing pending.*

**`&var`, `&`, and bare `ident` (clone) captures** — the whole of this RFC — have no
dependency on linear types, allocators, brands, RFC-0134, or RFC-0028. Their only
prerequisite is RFC-0067a (`4-implemented`, Cluster A — `&T`/`&var T` with no anchors, no
allocator interaction). Bare `ident` has no reference representation at all. Implementable
now.

**Ownership-transfer capture** is deferred to a future RFC that first settles the
closure-capture default (RFC-0006's clone-by-default) and the `Copy`/`Clone` model under
it. That RFC — not this one — is where an ownership-transfer specifier, if any, is
designed. RFC-0046 (`6-refused/`), which specified the old `move` in `linear fun` /
exactly-once terms against the unified `Region` model, is not the framing to inherit.

**Suggested order:** implement this RFC (`&var`/`&`/clone) now against RFC-0067a. Revisit
ownership-transfer capture when the capture-default RFC exists.

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
  capture kind (`&var`/`&`/clone) known statically from the specifier. Without exhaustiveness,
  some fields would exist in the runtime environment without appearing anywhere in the syntax,
  which is exactly the kind of implicit state that would need discovering and reconciling by hand
  when records or brand-based escape checking arrive.
- **Escape checking.** Whatever the split model uses to check that an allocator/lifetime-tagged
  value doesn't escape its scope should be written as a generic check over an aggregate's field
  types, not as bespoke closure logic. A `[&var count]` closure is then covered automatically
  because its captured environment *is* an aggregate, with nothing closure-specific to revisit if
  brand-kind unification later generalizes escape checking.
- **If ownership-transfer capture is added later**, keep it on this same footing: a moved-in
  field is an ordinary owned field of the capture aggregate, and any "does calling this closure
  consume a capture" question (RFC-0134's `call_multiplicity`) should be the same move-tracking
  the checker already runs on any body, applied to the capture aggregate as its place — one
  mechanism on two syntactic forms, not a bespoke `linear fun` type. This RFC does not
  implement that; it only asks the aggregate representation not to foreclose it.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0041: Lambda Syntax for Anonymous Functions — the base closure-literal spelling
- RFC-0154: Pipe Notation for Closures and Function Types (`1-under-review`) — proposes
  `|x| body` for the literal; the `[captures]` prefix composes ahead of whichever base
  spelling settles
- RFC-0043: Regular Pointers and Mutable Pointers — **superseded by RFC-0067a**
- Closure capture tests: `tests/evaluator/sources/closures/72_closure_internal_ptr_no_outer_effect.mtl`, `73_closure_direct_assign_no_outer_effect.mtl`, `74_closure_external_ptr_affects_outer.mtl`
- RFC-0006: Closure Capture Semantics and Cross-Closure Reference Sharing (`4-implemented`) —
  defines the current clone-by-default capture behavior this RFC's bare `ident` specifier
  spells explicitly. Whether that default should change (so a non-`Copy` value moves rather
  than clones, or fails) is the question a future ownership-transfer-capture RFC must settle;
  out of scope here.
- RFC-0046: Linear Closure Capture — **refused** (`6-refused/`); specified a `move` capture in
  `linear fun` / exactly-once terms against the old unified `Region` model. Not the framing to
  inherit. Listed only to note that this RFC's dropped `move` specifier is *not* a revival of it.
- RFC-0134: Closure Call Capability (`2-accepted`, 2026-08-30) — `call_multiplicity`
  (`once`/`many`), the affine answer to "does calling a closure consume a capture." **No longer
  a dependency of this RFC** (the `move` specifier that needed it is dropped); relevant to the
  future ownership-transfer-capture RFC.
- RFC-0135: Multiplicity for Ordinary Types (`1-under-review`, #892) — reframes `Copy` as
  `many` for by-value use; the adjacent work on the `Copy`/`Clone` model that a
  capture-default RFC would build on.
- RFC-0071: Ownership and Move Semantics (`3-integrated`) — the settled affine ownership
  model. An affine move takes no keyword under it, which is why this RFC has no `move`
  specifier.
- RFC-0063: Allocator Handles (`2-accepted`, retitled from "Region Handles" in the 2026-07-05
  split-model rewrite) — no longer uses bracket syntax for allocator parameters; see Historical
  section above.
- RFC-0065: Allocator Ergonomics (`2-accepted`, retitled from "Region Ergonomics") — no
  longer affects this RFC's bracket syntax.
- RFC-0067a: Reference Types (`4-implemented`, split from RFC-0067 2026-07-07) — supersedes
  RFC-0043's `*mut T`/`*T` with `&var T`/`&T`; the only prerequisite for this RFC.
- RFC-0067: Lifetime Anchors (`1-under-review`) — adds
  `&r var T`/`&r T` on top of RFC-0067a; see Timing Recommendation above for sequencing.
- `reports/implementation/roadmap-2026-07-07.md` — phased sequencing this RFC fits into.
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
