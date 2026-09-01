---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
status: integrated
target: v0.13.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/803'
coverage:
  "1": { spec: "spec.functions.closures.legality-5" }
  "2": { spec: "spec.functions.closures.legality-6" }
  "3": { spec: "spec.functions.closures.legality-22" }
  "4": { spec: "spec.functions.closures.legality-19" }
  "5": { spec: "spec.functions.closures.legality-13" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/926'
impl_status: not-started
---


> **Status — accepted 2026-09-01**, co-accepted with RFC-0153 as the capture half of the
> v0.13.0 closure cluster (RFC-0134 / RFC-0152 / RFC-0050 / RFC-0153 / RFC-0157).
> Enforcement of the borrow-shaped Resolved Questions is RFC-0122's (§2e/§2f); the
> pre-RFC-0122 interim window is catalogued there. Implementation shape: **ADR-0052**.

> **Status — integrated (2026-09-01).** Closure cluster spec-integrated (Legality 5/6/13/19/22, with 11/17/21/23 as sub-rules); coverage.spec frontmatter added; fixtures blocked on metel-core#925. Shape: ADR-0052.

## Summary

Add a capture list syntax to closure expressions, with three specifiers: `&var ident`
captures by mutable reference; `&ident` captures by read-only reference; **bare `ident`
captures by value** — a copy for a `Copy` binding, an affine **move** for a non-`Copy`
binding (the outer binding is consumed), with `[ident.clone()]` for an explicit
independent copy. All three may appear in one list.

The list is **required** whenever the closure captures a free non-`Copy` local, or
captures by `&` / `&var`; it is omissible only when the closure captures nothing or
captures only `Copy` bindings by value. Once present, it is **exhaustive** — every free
variable the body references, where "free variable" means an outer-scope local binding
(not a module-level function, constant, type, or aspect), must appear. Captures are
explicit at the definition site.

Ownership-transfer capture — moving a binding into a closure — is covered: it is bare
`[ident]` for a non-`Copy` binding, needing no keyword (an affine move takes none
elsewhere in Metel either). This lands with RFC-0157's D5 as one hard change; see
"Migration" below.

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

### 1. Capture-list grammar

Extend the closure expression syntax with a capture list placed before the parameter list:

```
closure_expr  = capture_list? "(" params ")" "->" return_type? block
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&var" ident | "&" ident | ident | ident "." "clone" "(" ")"
```

The `capture_list?` is syntactically optional but **semantically required** unless every
free variable the body references is a `Copy` binding captured by value (or there are no
free variables) — see "When the list is required" below.

**Full prefix order.** A closure literal's prefixes appear in a
fixed order — **capture list, then multiplicity/mutation qualifiers, then the parameter
spelling**:

```
[captures]  once? var?  ( params ) -> ret  block          // current spelling
[captures]  once? var?  | params | -> ret? block          // under RFC-0154
```

e.g. `[s, &cfg] once var (req: Request) -> Response { … }`. The capture list is
outermost because it describes the *environment*, which is conceptually prior to the
callable's signature; `once` / `var` (RFC-0134 / RFC-0153) qualify the signature; the
pipe/paren params come last. RFC-0154 settles only the `(params)` ↔ `|params|` half; the
`[captures] qualifiers …` prefix composes ahead of whichever it picks.

**Literal order is fixed; type-spelling order is not.** In a closure *literal* the two
qualifiers appear in exactly the order `once? var?` — `[c] var once () -> T { … }` is a
parse error. Order-insensitivity of `once` / `var` (RFC-0134 §5, RFC-0153 §2) is a
property of the *function type* spelling only: `once var (T) -> U` and `var once (T) -> U`
denote the identical `Type::Fun`. This RFC is the normative source for the literal
grammar; RFC-0153 §2's `var once fun(T) -> U` line is a type, not a literal prefix.

`&var ident` captures a binding by mutable reference. `&ident` captures a binding by
read-only reference — no copy, and the closure may not write through it. **Bare `ident`
captures by value:** a copy for a `Copy` binding, an affine **move** for a non-`Copy`
binding — the outer binding is consumed at closure creation, exactly as `let y := x`
consumes `x`. `[ident.clone()]` captures an explicit independent copy of a `Clone`
binding, leaving the outer binding usable. All specifiers may appear in one list:
`[&var count, &config, buf, prefix.clone()]`.

Bindings named with `&var` in the capture list are captured by mutable reference rather than by value. Inside the closure body they are used with ordinary read and assignment syntax — no explicit dereference required. **A `&var` capture makes the closure `mutating` (RFC-0153 §1), so the literal must be written `var`** — a `[&var …]` closure without `var` is a compile error (*"a `&var` capture makes this closure `var`; write `[&var count] var (…)`, or capture `[&count]` if the body only reads `count`"*). The `&var` capture is not itself the written signal; the `var` keyword is.

```metel
fun main() {
    var count := 0;

    var inc := [&var count] var () -> () {   // `var inc`: a `var` closure needs a `var` callee binding
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

### 2. When the list is required

A closure may omit the capture list only if **every** free variable it references is a
`Copy` binding captured by value (a copy — semantically free), or it has no free variables
at all. Those closures keep the RFC-0006 implicit path unchanged.

The list is **required** the moment the closure references a free non-`Copy` local, or
needs `&` / `&var` for any capture. A non-`Copy` free variable referenced with no list is
a compile error: *"closure captures non-`Copy` `s`; add a capture list — `[s]` to move it
in, `[&s]` / `[&var s]` to borrow, `[s.clone()]` to copy."* This makes RFC-0006's implicit
deep-clone unreachable for non-`Copy` values — nothing is cloned into a closure without
`.clone()` written at the capture site.

(A non-`Copy`, non-`Clone` binding can enter a closure: `[s]` moves it in.)

**Bare `[s]` for a non-`Copy` `s` often forces `once`.** `[s]` is a by-value *move* into
the environment; if the body then moves `s` out — returns it, passes it by value to
something that takes ownership — that is a body that consumes a by-value capture, so
RFC-0134 §2 makes the closure `once` and (post the `many`-default amendment) the literal
must be written `[s] once (…) -> … { … }` or be a definition-site error. A body that only
*reads* `[s]` stays `many`. This is intended, but callers of this RFC should know that the
most obvious `[s]` closure — `[s] () -> String { s }` — needs the `once` qualifier.

**Unknown `Copy`-ness in a generic body.** Inside `fun make<T>(x: T) -> …`, a free
variable of type parameter `T` is treated as **non-`Copy` unless `T: Copy` is in scope**
— conservative, so the list is required and `[x]` is a move. The capture kind is fixed at
the generic definition site, not re-decided per monomorphisation, so instantiating `T`
with a `Copy` type does not silently change capture semantics; it only means the move is
a copy at that instantiation.

**A closure literal cannot reference its own `let` binding.** `let f := () -> i64 { f() };`
is an unresolved-name error — `f` is not in scope inside its own initializer, so it is
neither a free variable nor a capture. Recursive closures need a named `fun` (which has
runtime knot-tying) or an explicit fixpoint helper; this RFC adds no self-capture form.

**Capturing `self` inside a method.** In `extend Foo { fun m(&self) -> … { … } }` the
receiver `self` is an ordinary binding in `m`'s scope, so a closure written inside `m`
that names `self` (or `self.x`) has `self` as a **free variable** and the ordinary rules
apply — there is no special "receiver capture" form:

- `self` is typically `&Self` or `&var Self`. `&Self` is `Copy` (RFC-0134 §1 / RFC-0153
  §3), so `|| self.x` may omit the list and captures the `&Self` handle by copy. `&var
  Self` is **not** `Copy`, so a closure using it needs a list — `[self]` moves the `&var
  Self` handle into the closure (the receiver borrow itself; not `&&Self` — there is no
  double reference), and `[&self]` / `[&var self]` are rejected as "cannot take a
  reference to a reference binding here."
- A by-value `self` receiver (RFC-0044) is captured exactly like any other owned local:
  `[self]` moves it in, forcing `once` if the body then moves it out.
- **Lifetime.** The captured receiver borrow is a `&`/`&var` capture, so Resolved
  Question 1 applies: it is held for the closure's whole lifetime, and the closure
  therefore **cannot outlive `m`'s call**. Returning such a closure from `m` — `fun m(&self)
  -> (() -> i64) { || self.x }` — is the ordinary "captured reference escapes its
  scope" error (the escape check over the capture aggregate), not a new rule. It becomes
  expressible only when lifetime anchors (RFC-0067 / RFC-0159) let `m` tie the closure's
  region to `self`'s; until then it is rejected.

If a closure *does* have a capture list, that list must be exhaustive: every free variable the closure body references must appear in it, with the specifier matching how it's used. "Free variable" means an outer-scope **local binding** — a `let` binding or function/closure parameter visible in the lexical scope enclosing the closure. It does not include references to module-level functions, constants, types, or aspects: those are resolved by ordinary name resolution regardless of any capture list, and never need to appear in it, since nothing about them is being captured from a stack frame. A closure mixing a mutable-reference capture with a by-value capture now looks like:

```metel
fun main() {
    var count := 0;
    let log_prefix := "counter: ";        // String — non-Copy

    var inc := [&var count, &log_prefix] var () -> () {   // `var` qualifier — the body assigns `count` via a `&var` capture; `var inc` — a `var` closure needs a `var` callee binding
        count += 1;
        print(log_prefix + count.to_string());   // `print` is a module-level function, not a free variable
    };

    inc();
    inc();                                  // `log_prefix` borrowed, still usable here
}
```

Referencing a free local binding that is not in the list — of any kind, including ones that would only need clone capture — is a compile error once the closure has a capture list at all. References to module-level items are unaffected.

### 3. Nested closures

**Nested closures.** A capture-list item may name a binding that is itself a capture of an
*enclosing* closure — from the inner closure's point of view it is still an outer-scope
local. Rules:

- **The outer closure must list `s` in its own capture list** — it is a free variable of
  the outer body (the inner literal reads it), so the outer's exhaustiveness rule applies
  normally.
- **`[s]` (by-value) in the inner requires the outer to hold `s` by value** (`[s]`). You
  cannot move out of an `[&s]` / `[&var s]` borrow — an inner `[s]` naming an outer `[&s]`
  capture is a compile error (`move out of borrowed content`).
- **Evaluating the inner literal performs the capture.** So an inner `[s]` that moves an
  outer-held `s` makes the **outer** closure `once` by RFC-0134 §2 — the move happens when
  the outer body runs and constructs the inner closure, whether or not the inner closure
  is ever called. `[&s]` / `[&var s]` in the inner does not affect the outer's
  multiplicity (it only borrows).
- **An inner `[&s]` / `[&var s]` that borrows an outer *by-value* capture is an interim
  rejection in v0.13.0** — *"cannot borrow into an enclosing closure's environment yet;
  bind a copy, or wait for the borrow checker (RFC-0122)."* The inner closure would hold a
  reference into the outer closure's environment aggregate, live for the inner's whole
  lifetime; whether that is a sound local reborrow (the inner is strictly local to one
  activation and dies before the outer touches `s` again) or an escaping alias is exactly
  the NLL question RFC-0122 answers and this RFC cannot. Conservative rejection now; lifted
  to a checked local-reborrow rule when RFC-0122 lands (RFC-0122 §2f notes this as its
  one closure gap, §2e catalogues it). Borrowing an outer `[&s]` / `[&var s]` *reference*
  capture (not a by-value one) by the same reference kind is fine — the reference is
  copied/reborrowed by the ordinary rule, nothing points into the outer aggregate.

### 4. Checking order

A closure literal is resolved in a fixed order; the first stage that fails is the reported
error, and later stages are suppressed for that closure:

1. **Capture classification** — which free variables the body references, whether each is
   `Copy`, whether a list is required, and (if a list is present) exhaustiveness and
   specifier-matches-use. The "add a capture list" / "not in the list" errors are here.
   Deciding a free variable's `Copy`-ness needs its type to be known, which it is by this
   point (classification runs after type checking); for a type parameter `T` it consults
   the **declared bounds** (`T: Copy` present or not — no solver invocation), matching
   RFC-0134 §2's definition-site rule.
2. **`use_multiplicity`** — derived from the capture set (RFC-0134 §1).
3. **`call_multiplicity` verification** — the body vs. the declared/default/expected
   `many` (RFC-0134 §2). The "unqualified closure consumes a capture" error is here.
4. **`call_mutation` verification** — the body vs. the declared/default/expected `reading`
   (RFC-0153). The "unqualified closure mutates a capture" error is here.

Because stages 3–4 reason about *classified* captures, a capture-classification failure
(stage 1) is always reported before a multiplicity or mutation failure. Stages 3 and 4 are
independent; a body that both consumes and mutates without the qualifiers gets both
errors, and each offers its own real alternatives — "add `once`, or stop moving the
capture" / "add `var`, or stop mutating it" — not a single prescribed `once var`.

### 5. Semantics

**`&var` captures:**
- At closure creation time, each `&var ident` capture takes `&var ident` and stores the resulting `&var T` in the closure's captured environment.
- Inside the closure body, reads and writes of the binding are automatically routed through the stored reference. The programmer never sees an explicit dereference.
- The outer binding must be declared `var`. Attempting to capture a non-`var` binding via `&var` is a compile error.

**`&` (read-only reference) captures:**
- At closure creation time, each `&ident` capture takes `&ident` and stores the resulting `&T` in the closure's captured environment. No clone occurs.
- Inside the closure body, reads of the binding are automatically routed through the stored reference. The programmer never sees an explicit dereference, and cannot write through it — assigning to a `&`-captured binding inside the closure body is a compile error, the same rule that applies to any `&T` value outside a closure.
- Unlike `&var`, the outer binding does not need to be declared `var` — `&ident` is valid for any addressable binding, matching `&x`'s existing rules outside of closures (RFC-0067a).

**Bare `ident` (by-value) captures:**
- At closure creation time, each bare `ident` capture takes the binding **by value**: a
  copy if the binding is `Copy`, an **affine move** if it is not — the outer binding is
  consumed and using it after closure creation is a compile error, exactly as `let y :=
  x;` consumes `x` (RFC-0071). No implicit clone: a non-`Copy` value is moved, never
  duplicated, unless `.clone()` is written.
- A `once`-vs-`many` consequence: a closure whose body *moves* a bare-captured non-`Copy`
  binding out is call-once — see RFC-0134 §2, which inspects exactly these captures.

**`ident.clone()` (explicit copy) captures:**
- At closure creation time, `[ident.clone()]` evaluates `ident.clone()` and stores the
  resulting independent value in the environment. The outer binding stays usable. Requires
  `ident`'s type to be `Clone` (RFC-0080).
- This is the only way to duplicate a non-`Copy` value into a closure; it is deliberately
  the explicit, visible form.

**All specifiers:**
- A binding may not appear more than once across the capture list (no dual capture of the same name under different kinds).
- **Exhaustiveness.** A closure with a capture list must enumerate every free local binding it references — there is no partial mode where some captures are explicit and others are silently implicit. Module-level functions, constants, types, and aspects are never "free variables" for this rule (see Proposal); only outer-scope `let` bindings and parameters count. A listless closure is permitted only in the `Copy`-only / no-free-variables case (see "When the list is required"), where there is nothing whose capture kind could surprise a reader; see Implementation Guidance for why this matters beyond ergonomics.

---

## Alternatives Considered

### Keep requiring an outer `&var` reference binding (status quo)

Works today. Verbose, non-obvious, and puts a semantically empty binding in the outer scope. Rejected as the permanent answer given the ergonomic cost.

### Allow `&var ident` inside the closure body

Syntactically simple but does not work under the current capture semantics — the closure holds a deep-cloned copy, so the internal reference targets the copy, not the original. Making it work would require abandoning deep-clone capture entirely or adding a special case that distinguishes "address-of a captured binding" from "address-of a local binding", both of which are more invasive than a capture list.

### Implicit mutable capture

Allow closures to detect at analysis time that a captured binding is assigned and automatically capture it by reference. Rejected: breaks the design principle that mutation is always explicit in Metel, and makes closure behaviour harder to reason about from the definition site alone.

### A `move ident` specifier for ownership-transfer capture

> **Conclusion superseded by the 2026-08-31 amendment.** Ownership-transfer capture is
> now in scope — as bare `[ident]` for a non-`Copy` binding, which *is* an affine move and
> needs no keyword, exactly as this section concludes. What changed is only that RFC-0157's
> D5 is now settled, so "deferred to RFC-0157" below reads as "adopted from RFC-0157's D5."
> The history and the no-keyword argument stand.

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
Both are larger than this RFC and are the subject of **RFC-0157 (Copy and Clone Model
Re-analysis, `1-under-review`)**, alongside the adjacent RFC-0135. Ownership-transfer capture is
therefore deferred to RFC-0157; this one is scoped to `&var`/`&`/clone, which stand on
their own and depend only on RFC-0067a. (RFC-0157's current recommendation would settle
this as "no specifier — bare capture of a non-`Copy` value *is* the move"; that is a
recommendation under review, not yet a decision.)

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

1. **Lifetime and exclusivity of a `&`/`&var` capture. ✓ Resolved; the *rule* is stated now, enforcement lands with RFC-0122.** A `[&var x]` / `[&x]` capture takes the borrow at closure creation and **holds it for the closure value's whole lifetime** — from creation to the closure's last use / drop. For that whole span the outer binding `x` is borrowed exactly as `let r := &var x;` / `let r := &x;` would borrow it: while a `[&var x]` closure is live, any other read or write of `x` — `x += 10` between creating the closure and calling it, another `[&var x]` / `[&x]` closure, a bare `&x` — is a borrow-conflict error; while a `[&x]` closure is live, `x` may be read but not written or `&var`-borrowed. This is not a new rule, only the ordinary reference-borrow rule applied to the capture. The **interpreter does not enforce it yet** (heap-backed storage means no memory unsoundness in the meantime); enforcement arrives with the borrow checker (RFC-0122), and until then a program that violates it is accepted but ill-formed by this rule. **RFC-0122 §2e catalogues this as one of the interim rules it subsumes** — including the fixture-corpus constraint below.

2. **Interaction with concurrency. ✓ Resolved** — a closure's `Send`/`Sync` is the **ordinary aggregate rule over its captures**, and a `&T` / `&var T` capture follows **RFC-0080**'s reference rules (`&T: Send if T: Sync`; `&var T: Send if T: Send`; likewise `Sync`). This RFC does not restate or strengthen those — the earlier flat "any `[&var x]` / `[&x]` closure is non-`Send`" was too strong (a `[&n]` capture of `n: i64` is `&i64: Send`, so that closure *is* `Send`). RFC-0153 carries the one closure-specific fact — a `mutating` closure is `!Sync` — as an interim statement pending RFC-0096. Once RFC-0067 adds lifetime anchors (`&r var T` / `&r T`), the reference `Send` rules gain an anchor dimension (RFC-0067/RFC-0074) — a residual, not a blocker.

3. **Multiple closures capturing the same binding. ✓ Resolved** — folds into Resolved Question 1: two live `[&var x]` closures are two live `&var x` borrows, which conflict; `[&x]` closures may coexist with each other but not with a `[&var x]` closure or a write to `x`. The interpreter accepts aliased `[&var x]` today (single-threaded, sequential calls — no memory unsoundness); RFC-0122 enforces the rule.

4. **Syntax. ⚠ Re-resolved, with one live contention.** `[&var x]` was confirmed jointly
   with RFC-0046. RFC-0063's pre-split "Region Handles" draft briefly introduced
   `[region]` in the same position (historical, no longer applicable), but the split-model
   rewrite of RFC-0063/0065 dropped bracket syntax for allocator parameters (`@[r]` → `@`)
   before this RFC reached implementation, and `reports/memory-model/lifetimes-vs-regions-2026-07-02.md`
   §7 explicitly freed `[]` for capture lists.

   **The contention: RFC-0159 (Abstract Regions and a Dedicated Identity Channel,
   `1-under-review`)** revisits whether lifetimes, brands, and storage identities want a
   dedicated non-`<>` parameter channel, for which `[]` is the historically natural glyph.
   RFC-0159 **does not claim `[]`** — it lists `[]` as unavailable *because of this RFC*
   and names `<T; r>` / a `where identity r` clause / a new delimiter as its candidates.
   So there is no conflict today, and RFC-0159 defers to this RFC. If RFC-0159's prototype
   nonetheless concludes `[]` is the right identity channel, this RFC yields it: capture
   lists fall back to a `capture(...)` keyword form, or a `|caps|` prefix composing with
   RFC-0154's proposed `|params|` literal. Recorded here so the v0.13.0 implementation
   does not treat `[...]` as permanently settled.

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

7. **Closure equality and ordering. ✓ Resolved.** Two
   closure values are **not comparable**. `Type::Fun` satisfies no aspects at all
   (RFC-0134's Open-Questions finding: `InferType::Fun` implements nothing), `Eq` / `Ord`
   included, so `a == b` / `a < b` on closures is an aspect-not-satisfied type error — the
   same as `==` on any non-`Eq` struct. The unifier's structural comparison of two
   `Type::Fun` *types* is a type-identity relation and implies nothing about value
   equality; two closures of the same type with different captures simply cannot be
   compared. No closure identity, hash, or by-address comparison is introduced by this
   RFC. (RFC-0153 records the same fact for its Non-Goals.)

---

## Migration

Metel has no public users and no `--edition` tooling. The whole closure cluster — this
RFC's required-list rule and bare-`[s]`-is-move, RFC-0153 §1a's write-back, RFC-0134's
`once`/`many` verification, RFC-0157's D5 capture default, and the removal of RFC-0006's
per-call environment re-clone — lands as **one implementation PR** at v0.13.0. There is
no old/new edition and no fixer; the interpreter's own `.mtl` fixture corpus is updated
in the same change.

Three behaviour-change classes the corpus sweep must find, all legal under RFC-0006:

1. **Capture-then-still-use** — `let f := () -> Int { len(s) }; let n := s.len();` was fine
   (`f` held a clone); now `[s]` moves `s`, so the later use is use-after-move. Fix:
   `[s.clone()]` or reorder. The common case.
2. **Mutate a per-call clone** — `let bump := () -> Int { x := x + 1; x };` returned `1`
   every call under RFC-0006 (writing a throwaway clone); under D5 + RFC-0153 it needs
   `[x] var` and the write-back makes it a stateful counter. A semantic change, reviewed
   by hand — `[x.clone()]` per call if the reset was the intent.
3. **`&var` capture used read-only** — a `[&var x]` closure whose body only reads `x` is
   now `mutating` / `!Sync` / non-widening; switch it to `[&x]`.

The sweep also **excludes** programs relying on the not-yet-enforced `[&var x]`
borrow-freeze (Resolved Question 1) — those are ill-formed by this RFC and are valid only
as `expected-error` fixtures once RFC-0122 lands. The grep recipe, measured corpus counts,
and the always-on vs `--move-check` decision are in **ADR-0052**.

## Implementation Guidance

One constraint on the representation, so later structural-record / brand-escape work does
not force a rewrite: **store a closure's captures as a plain closed named-field aggregate**
— the same shape as struct field storage, not a bespoke closure-environment type. The
capture list *is* the field list; each field's kind (`&var` / `&` / owned) is fixed by its
specifier. Escape / brand checking is then a generic check over an aggregate's field types,
with nothing closure-specific. RFC-0153 §1a's move-once mutable environment is this same
aggregate, held owned-and-mutable rather than re-cloned. Full runtime shape, the
`Type::Fun` match-site set, error codes, and `capture_clone` removal are in **ADR-0052**.

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
  spells explicitly. That default **is** changed — a non-`Copy` value *moves* — by
  **RFC-0157**'s D5, now `2-accepted`.
- RFC-0157: Closure Capture Default (Move) (`2-accepted`, #918) — the RFC this one defers
  ownership-transfer capture to. Its D5 decision (closure capture by value = move,
  `let y := x`) settles this RFC's out-of-scope note as "no specifier needed"; it lands as
  one hard change (Metel has no public users; no edition gate). The regular-value
  `Copy`/`Clone` model analysis it originally carried is **RFC-0162** (`1-under-review`).
- RFC-0046: Linear Closure Capture — **refused** (`6-refused/`); specified a `move` capture in
  `linear fun` / exactly-once terms against the old unified `Region` model. Not the framing to
  inherit. Listed only to note that this RFC's dropped `move` specifier is *not* a revival of it.
- RFC-0134: Closure Call Capability (`2-accepted`, 2026-08-30) — `call_multiplicity`
  (`once`/`many`), the affine answer to "does calling a closure consume a capture." **No longer
  a dependency of this RFC** (the `move` specifier that needed it is dropped); relevant to
  RFC-0157.
- RFC-0135: Multiplicity for Ordinary Types (`1-under-review`, #892) — reframes `Copy` as
  `many` for by-value use; adjacent to RFC-0157 (RFC-0157 questions the model RFC-0135
  renames).
- RFC-0071: Ownership and Move Semantics (`3-integrated`) — the settled affine ownership
  model. An affine move takes no keyword under it, which is why this RFC has no `move`
  specifier.
- RFC-0063: Allocator Handles (`2-accepted`, retitled from "Region Handles" in the 2026-07-05
  split-model rewrite) — no longer uses bracket syntax for allocator parameters; see Historical
  section above.
- RFC-0065: Allocator Ergonomics (`2-accepted`, retitled from "Region Ergonomics") — no
  longer affects this RFC's bracket syntax.
- RFC-0067a: Reference Types (`4-implemented`, split from RFC-0067 2026-07-07) — supersedes
  RFC-0043's `*var T`/`*T` with `&var T`/`&T`; the only prerequisite for this RFC.
- RFC-0067: Lifetime Anchors (`1-under-review`) — adds
  `&r var T`/`&r T` on top of RFC-0067a — a residual, not a blocker.
- `reports/implementation/roadmap-2026-07-07.md` — phased sequencing this RFC fits into.
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Accepted 2026-09-01**, co-accepted with RFC-0153, as the closure-capture half of the
v0.13.0 closure cluster. Capture semantics are settled: move-by-default (RFC-0157 D5), a
capture list required the moment a non-`Copy` move or an `&`/`&var` capture occurs, bare
`[s]` = move for non-`Copy`, `[s.clone()]` for an explicit copy, `[&var x]` ⇒ `mutating`
(`var` written). All seven Resolved Questions closed. `[]` syntax carries RQ4's recorded
RFC-0159 contention (fallback: `capture(...)` / `|caps|`) — not a blocker; RFC-0159 defers
to this RFC. Interim borrow-rule enforcement and the pre-RFC-0122 window are catalogued in
RFC-0122 §2e/§2f.

**Target:** v0.13.0 (#803) — one implementation PR with RFC-0134 / RFC-0152 / RFC-0153 /
RFC-0157; shape per ADR-0052.
