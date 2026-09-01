---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
status: under-review
target: v0.13.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/803'
---

> **Amendment, 2026-08-31 (second pass) — capture semantics settled; targeted at v0.13.0.**
> The earlier correction pass (below) dropped the `move` specifier and deferred
> ownership-transfer capture to RFC-0157. RFC-0157's D5 has since been settled in the
> direction this RFC needs, so the deferral is lifted and folded in here:
>
> **D5 decided 2026-09-01 (language owner): the closure-capture default is `move`.** What
> was "settled in the direction this RFC needs" is now a decision. It also removes
> RFC-0006's per-call environment re-clone — the captured environment is moved in once and
> read (or, for a `mutating` closure, mutated — RFC-0153 §1a) in place. Precondition (1)
> in "Migration" below is met; only RFC-0050/RFC-0153 reaching `accepted` remains.
>
> - **A capture list is semantically required** whenever a closure captures a free
>   non-`Copy` local binding, or captures anything by `&` / `&var`. It stays *omissible*
>   only when the closure captures nothing, or captures only `Copy` bindings by value
>   (where "by value" is a copy and so carries no risk). This makes RFC-0006's implicit
>   deep-clone default unreachable for non-`Copy` captures — you can no longer clone a
>   `Vec` into a closure by accident.
> - **Bare `ident` is by-value capture:** a copy for a `Copy` binding, an **affine move**
>   for a non-`Copy` binding (the outer binding is consumed — `let y := x` semantics,
>   RFC-0157 D5). An explicit independent copy is written `[ident.clone()]` (RFC-0080's
>   `Clone`). This is the change from "bare `ident` = clone" in the correction-pass text
>   below.
> - **Ownership-transfer capture is therefore back in scope, and still needs no keyword:**
>   `[buf]` for a non-`Copy` `buf` moves it in. That is exactly the "an affine move takes
>   no keyword" reasoning that removed the `move` specifier — now realized rather than
>   deferred. The "out of scope" / "deferred to RFC-0157" wording everywhere below this
>   note, and the *conclusion* (not the history) of the "A `move ident` specifier"
>   alternative, are superseded by this bullet.
> - **Pairs with RFC-0134's same-day amendment** (`many` by default, explicit `once`): a
>   listed by-value non-`Copy` capture is what RFC-0134 §2's consumption check inspects.
> - **Timing.** Lands with RFC-0157's D5 (the RFC-0006 default change) as **one hard
>   change** — see "Migration (no edition gate)" below. Milestoned **v0.13.0** (#803)
>   alongside RFC-0134 (#269) and RFC-0152 (#901) — closure capture lists and closure call
>   capability are one feature area. Still `1-under-review`; needs to reach `accepted` to
>   match the rest of that milestone.

> **Adversarial-review fixes, 2026-09-01** (two passes, cross-RFC review of the v0.13.0
> cluster):
> - "When the list is required": bare `[s]` for non-`Copy` `s` often forces `once`;
>   a generic `T` is non-`Copy` unless `T: Copy` is a declared bound (capture kind and
>   `once`/`many` both fixed at the definition site — see RFC-0134 §2); a closure literal
>   cannot reference its own `let` binding.
> - **Full prefix order** stated: `[captures] once? mut? (params) -> ret block`.
> - **Nested closures** (3 rules): the outer must list `s`; an inner `[s]` can't move out
>   of an outer `[&s]`; evaluating the inner literal performs the capture, so an inner
>   `[s]` makes the *outer* closure `once` even if the inner is never called.
> - **Checking order** subsection: capture classification (with `Copy` from declared
>   bounds, no solver call) → `use` → `call` → `mutation`; stages 3/4 independent, each
>   offering its own fix rather than a forced `once mut`.
> - **Resolved Question 1/3** sharpened from "no restriction now" to a stated
>   borrow-duration rule (a `[&var x]` / `[&x]` capture holds the borrow for the closure's
>   lifetime; the outer binding is borrow-frozen accordingly; interpreter enforcement
>   lands with RFC-0122).

> **Adversarial-review fixes, 2026-09-01 (third pass):**
> - **Capturing `self` in a method** — new subsection under "When the list is required":
>   `self` is an ordinary receiver binding, so it is a free variable for a nested closure;
>   `&Self` is `Copy` (listless capture copies the handle), `&var Self` is not (list
>   required); the captured receiver borrow cannot outlive the method call, so a closure
>   escaping the method while holding it is rejected by the same escape check as any other
>   captured reference until lifetime anchors (RFC-0067/0159) exist.
> - **Closure equality** — Resolved Question added: closure values satisfy no aspects
>   (RFC-0134), so `==` / `<` on them does not type-check.
> - **Prefix order** — clarified that the fixed `[captures] once? mut?` order is the
>   *literal* grammar; the qualifiers are order-insensitive only as a *type* spelling
>   (RFC-0134 §5, RFC-0153 §2).
> - **Migration** — the v0.13.0 fixture corpus must exclude programs that rely on the
>   not-yet-enforced `[&var x]` borrow-freeze (Resolved Q1), so no wrong accepted
>   behavior is baked in before RFC-0122.
> - **Implementation Guidance** — the RFC-0153 §1a mutable env cell *is* the capture
>   aggregate, not a wrapper; escape / brand checking sees the same field types.

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
>   That is a larger design question than this RFC — opened as **RFC-0157 (Copy and
>   Clone Model Re-analysis, `1-under-review`)**, alongside the adjacent RFC-0135. This RFC now
>   covers only `&var` / `&` reference captures and the explicit spelling of today's
>   implicit clone capture; **ownership-transfer capture is explicitly out of scope**,
>   deferred to RFC-0157. *(Lifted by the amendment above: RFC-0157's D5 is settled,
>   ownership-transfer capture is bare `[ident]` for non-`Copy`, back in scope.)*
>   Consequence: nothing in this RFC is blocked on RFC-0134 or
>   RFC-0028 any more — its only prerequisite is RFC-0067a (`4-implemented`).
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

> **Status — under review (2026-08-23; correction pass + amendment 2026-08-31, see frontmatter notes).** Six Resolved Questions checked. Amended 2026-08-31: capture list required for non-`Copy`/by-ref captures; bare `ident` is by-value (move for non-`Copy`); ownership-transfer capture folded back in (no keyword). Milestoned **v0.13.0** with RFC-0134 (#269) / RFC-0152 (#901); lands with RFC-0157's D5 as one hard change (no edition gate). Needs to reach `accepted`. -- #803

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
"Migration (no edition gate)".

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

Extend the closure expression syntax with a capture list placed before the parameter list:

```
closure_expr  = capture_list? "(" params ")" "->" return_type? block
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&var" ident | "&" ident | ident | ident "." "clone" "(" ")"
```

The `capture_list?` is syntactically optional but **semantically required** unless every
free variable the body references is a `Copy` binding captured by value (or there are no
free variables) — see "When the list is required" below.

**Full prefix order** *(added 2026-09-01)*. A closure literal's prefixes appear in a
fixed order — **capture list, then multiplicity/mutation qualifiers, then the parameter
spelling**:

```
[captures]  once? mut?  ( params ) -> ret  block          // current spelling
[captures]  once? mut?  | params | -> ret? block          // under RFC-0154
```

e.g. `[s, &cfg] once mut (req: Request) -> Response { … }`. The capture list is
outermost because it describes the *environment*, which is conceptually prior to the
callable's signature; `once` / `mut` (RFC-0134 / RFC-0153) qualify the signature; the
pipe/paren params come last. RFC-0154 settles only the `(params)` ↔ `|params|` half; the
`[captures] qualifiers …` prefix composes ahead of whichever it picks.

**Literal order is fixed; type-spelling order is not.** In a closure *literal* the two
qualifiers appear in exactly the order `once? mut?` — `[c] mut once () -> T { … }` is a
parse error. Order-insensitivity of `once` / `mut` (RFC-0134 §5, RFC-0153 §2) is a
property of the *function type* spelling only: `once mut (T) -> U` and `mut once (T) -> U`
denote the identical `Type::Fun`. This RFC is the normative source for the literal
grammar; RFC-0153 §2's `mut once fun(T) -> U` line is a type, not a literal prefix.

`&var ident` captures a binding by mutable reference. `&ident` captures a binding by
read-only reference — no copy, and the closure may not write through it. **Bare `ident`
captures by value:** a copy for a `Copy` binding, an affine **move** for a non-`Copy`
binding — the outer binding is consumed at closure creation, exactly as `let y := x`
consumes `x`. `[ident.clone()]` captures an explicit independent copy of a `Clone`
binding, leaving the outer binding usable. All specifiers may appear in one list:
`[&var count, &config, buf, prefix.clone()]`.

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

### When the list is required

A closure may omit the capture list only if **every** free variable it references is a
`Copy` binding captured by value (a copy — semantically free), or it has no free variables
at all. Those closures keep the RFC-0006 implicit path unchanged.

The list is **required** the moment the closure references a free non-`Copy` local, or
needs `&` / `&var` for any capture. A non-`Copy` free variable referenced with no list is
a compile error: *"closure captures non-`Copy` `s`; add a capture list — `[s]` to move it
in, `[&s]` / `[&var s]` to borrow, `[s.clone()]` to copy."* This makes RFC-0006's implicit
deep-clone unreachable for non-`Copy` values — nothing is cloned into a closure without
`.clone()` written at the capture site.

(A non-`Copy`, non-`Clone` binding can now enter a closure: `[s]` moves it in. That is the
change from the pre-amendment text, where such a binding could not be captured at all.)

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
  scope" error (Implementation Guidance's escape check), not a new rule. It becomes
  expressible only when lifetime anchors (RFC-0067 / RFC-0159) let `m` tie the closure's
  region to `self`'s; until then it is rejected.

If a closure *does* have a capture list, that list must be exhaustive: every free variable the closure body references must appear in it, with the specifier matching how it's used. "Free variable" means an outer-scope **local binding** — a `let` binding or function/closure parameter visible in the lexical scope enclosing the closure. It does not include references to module-level functions, constants, types, or aspects: those are resolved by ordinary name resolution regardless of any capture list, and never need to appear in it, since nothing about them is being captured from a stack frame. A closure mixing a mutable-reference capture with a by-value capture now looks like:

```metel
fun main() {
    var count := 0;
    let log_prefix := "counter: ";        // String — non-Copy

    let inc := [&var count, &log_prefix] () -> () {
        count += 1;
        print(log_prefix + count.to_string());   // `print` is a module-level function, not a free variable
    };

    inc();
    inc();                                  // `log_prefix` borrowed, still usable here
}
```

Referencing a free local binding that is not in the list — of any kind, including ones that would only need clone capture — is a compile error once the closure has a capture list at all. References to module-level items are unaffected.

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

### Checking order

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
capture" / "add `mut`, or stop mutating it" — not a single prescribed `once mut`.

### Semantics

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

1. **Lifetime and exclusivity of a `&`/`&var` capture. ✓ Resolved; the *rule* is stated now, enforcement lands with RFC-0122.** *(Sharpened 2026-09-01, adversarial review — the earlier "no restriction is imposed now" was too loose to be a spec.)* A `[&var x]` / `[&x]` capture takes the borrow at closure creation and **holds it for the closure value's whole lifetime** — from creation to the closure's last use / drop. For that whole span the outer binding `x` is borrowed exactly as `let r := &var x;` / `let r := &x;` would borrow it: while a `[&var x]` closure is live, any other read or write of `x` — `x += 10` between creating the closure and calling it, another `[&var x]` / `[&x]` closure, a bare `&x` — is a borrow-conflict error; while a `[&x]` closure is live, `x` may be read but not written or `&var`-borrowed. This is not a new rule, only the ordinary reference-borrow rule applied to the capture. The **interpreter does not enforce it yet** (heap-backed storage means no memory unsoundness in the meantime); enforcement arrives with the borrow checker (RFC-0122), and until then a program that violates it is accepted but ill-formed by this rule. **RFC-0122 §2e catalogues this as one of the interim rules it subsumes** — including the fixture-corpus constraint below.

2. **Interaction with concurrency. ✓ Resolved** — `&var T` and `&T` (RFC-0067a) are not `Send` (RFC-0003's `Send` marker aspect; the original citation of RFC-0028 no longer applies — that RFC is refused). A closure is `Send` only if all its captured values are `Send`. Any `[&var x]` or `[&x]` closure is therefore automatically non-`Send` — no new rule needed; falls out of the existing model. Once RFC-0067 lands and adds lifetime anchors (`&r var T`/`&r T`), this should be restated in terms of whatever `Send` rule RFC-0067/RFC-0074 give anchored references — not yet specified, tracked as a residual, not a blocker.

3. **Multiple closures capturing the same binding. ✓ Resolved** — folds into Resolved Question 1: two live `[&var x]` closures are two live `&var x` borrows, which conflict; `[&x]` closures may coexist with each other but not with a `[&var x]` closure or a write to `x`. The interpreter accepts aliased `[&var x]` today (single-threaded, sequential calls — no memory unsoundness); RFC-0122 enforces the rule.

4. **Syntax. ⚠ Re-resolved, with one live contention.** `[&var x]` was confirmed jointly
   with RFC-0046. RFC-0063's pre-split "Region Handles" draft briefly introduced
   `[region]` in the same position (see the Historical section above), but the split-model
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

7. **Closure equality and ordering. ✓ Resolved (2026-09-01, adversarial review).** Two
   closure values are **not comparable**. `Type::Fun` satisfies no aspects at all
   (RFC-0134's Open-Questions finding: `InferType::Fun` implements nothing), `Eq` / `Ord`
   included, so `a == b` / `a < b` on closures is an aspect-not-satisfied type error — the
   same as `==` on any non-`Eq` struct. The unifier's structural comparison of two
   `Type::Fun` *types* is a type-identity relation and implies nothing about value
   equality; two closures of the same type with different captures simply cannot be
   compared. No closure identity, hash, or by-address comparison is introduced by this
   RFC. (RFC-0153 records the same fact for its Non-Goals.)

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

*Retargeted 2026-08-31 (third pass): the frontmatter amendment folds ownership-transfer
capture back in (bare `[ident]` for non-`Copy` = move, no keyword). The whole RFC is now
one feature with one timing story, milestoned **v0.13.0** (#803) alongside RFC-0134 (#269)
and RFC-0152 (#901).*

**`&var`, `&`, and `Copy`-only listless captures** have no dependency beyond RFC-0067a
(`4-implemented`) and are implementable immediately.

**Bare `ident` by-value capture of a non-`Copy` binding** (the move case) is the change to
RFC-0006's implicit deep-clone default — RFC-0157's D5, **decided 2026-09-01 (language
owner): the closure-capture default is `move`.** This RFC's grammar and Semantics carry
it. The decision also removes RFC-0006's per-call `call_env = captured.clone()` re-clone:
the environment is moved in once and read (or, for a `mutating` closure, mutated —
RFC-0153 §1a) in place. RFC-0046 (`6-refused/`), which specified the old `move` in `linear
fun` / exactly-once terms, is not the framing inherited — an affine move takes no keyword,
which is why bare `[ident]` suffices.

**Suggested order:** land RFC-0157 D5 + this RFC together for v0.13.0, sequenced with
RFC-0134 (#269) — capture lists and call capability are one review.

### Migration (no edition gate)

*Amended 2026-09-01: the earlier "edition boundary" framing is dropped.* **Metel has no
public users and no `--edition` tooling.** The whole closure cluster — this RFC's
required-list rule and bare-`[s]`-is-move, RFC-0153 §1a's write-back, RFC-0134's
`once`/`many` verification, RFC-0157's D5 capture default (**decided 2026-09-01: `move`**),
and the removal of RFC-0006's per-call environment re-clone — lands as **one hard change**
at v0.13.0. There is no old/new edition, no fixer, no mixed mode.

Migration is entirely internal: the interpreter's own `.mtl` fixture corpus is updated in
the same change. Where a fixture captured a non-`Copy` value it then returns, that is the
multi-step rewrite the review noted (`() -> String { s }` → add `[s]` → the body consumes
it → add `once`), applied by hand to the corpus, not shipped as a user tool. Nothing about
`--edition` is a deliverable here.

**The corpus sweep must exclude programs that rely on the not-yet-enforced borrow-freeze
(Resolved Question 1).** RFC-0122 is not part of v0.13.0, so the interpreter will *run*
`[&var x]` closures without checking the borrow-duration rule. A fixture that exercises
what the rule forbids — two live `[&var x]` closures over the same binding, a write to `x`
while a `[&var x]` closure is live, a bare `&x` alongside one — is **ill-formed by this
RFC** even though the interpreter accepts it, and must not be added as an
expected-behavior fixture: doing so would bake a wrong "accepted" result into the corpus
that RFC-0122 then has to break. Such programs are only valid to add as
`expected-error` fixtures once RFC-0122 lands.

**"One hard change" is one implementation PR, but not one RFC stage yet.** RFC-0134 and
RFC-0152 are `2-accepted`; RFC-0050, RFC-0153, and RFC-0157 are `1-under-review`.
**RFC-0157's D5 is now decided** (2026-09-01, language owner — the closure-capture default
is `move`), so precondition (1) is met. The single implementation PR is now contingent
only on: (2) RFC-0050 and RFC-0153 reaching `accepted`; then (3) `Type::Fun` gains all
three multiplicity fields, the capture-list grammar, the `once`/`mut` qualifiers, the §1a
write-back, the removal of RFC-0006's per-call re-clone, and the corpus sweep, together.
Until (2), "one hard change" is the *plan*, not a settled cross-RFC fact.

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
  - **RFC-0153 §1a does not change this.** A `mutating` closure's environment is held as
    *one mutable owned cell* rather than re-cloned per call, but that cell **is this same
    aggregate** — the identical named-field list, with the same per-field types — held
    owned-and-mutable, not a wrapper struct around it and not a new representation. Escape
    and brand checking walk the same fields whether the closure is `reading` or
    `mutating`; the write-back is a mutation of the aggregate in place, not a change to
    its shape. Anything that inspected the capture aggregate's field types before RFC-0153
    inspects the same thing after it.
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
  than clones, or fails) is **RFC-0157**'s question, not this RFC's.
- RFC-0157: Copy and Clone Model Re-analysis (`1-under-review`, opened 2026-08-31, #918) — the RFC this
  one defers ownership-transfer capture to. Analyzes whether closure capture by value should
  mean move (consistent with `let y := x`) or clone (RFC-0006 today); its recommendation is
  the former, as a hard change (Metel has no public users; no edition gate), which settles
  this RFC's out-of-scope note as "no specifier needed."
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
