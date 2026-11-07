---
id: rfc-0089
title: "Linear Types"
date: '2026-07-09'
status: accepted
updated: '2026-11-05'
tracking: 'https://github.com/metel-lang/metel-core/issues/953'
---

> **Acceptance scope (2026-11-07, language owner): generic classes and the elimination rules are settled in design.**
> Accepted (inert in v0.16.0, because every type is `Discard` there): the class keywords (`copy`, `linear` reserved),
> `Linear` as a declared aspect, `Discard` as a compiler-computed capability written as a bound (`T: Discard`), bare `T`
> as possibly linear, and the generic-class model, decision D7: generic types are **open by default** and the class of
> an instance is **computed** from its owned fields; `linear` on a generic type is unconditional and `copy` states a
> capability (D8); `T: Discard` on a type parameter forbids linear arguments and every use repeats the bound (D9); a
> `pub` generic type states its `Discard` condition like `Copy` and `Clone`, with a conservative default (D19, RFC-0206
> section 6). The elimination rules are accepted in design and take effect with the `linear` release: a partial move
> out of a nominal aggregate needs the aggregate known `Discard` (D11); destructuring patterns consume their scrutinee,
> which removes narrowing through a pattern, while explicit field moves still narrow (D12, with the class-dependent
> variant kept as a fallback if needed); a `Drop` type is dismantled only by an explicitly marked method (D13, spelling
> open with RFC-0218); a field whose type mentions no type parameter and is linear forces `linear` on a generic type, a
> syntactic rule backed by the checked public `Discard` condition (D10, D19). **Still reserved, kept as design text for review and not binding on implementation:** the closure and
> binding-level rules (D14, D15). The reasoning and the alternatives are in the decision register
> (`architecture/reports/linear-types-decision-register.md`), the generic-class comparison
> (`architecture/reports/generic-class-computed-vs-explicit.md`) and its effects-library test
> (`architecture/reports/effects-generic-functions-computed-vs-explicit.md`).

> **Amendment (2026-11-06, language owner): a named type's class is declared and checked against its fields.** (Generic instantiations and structural types, such as tuples, arrays and anonymous records, compute their class from their components; generic code names the capabilities it needs in bounds, so a bare `T` is possibly linear and dropping it requires `T: Discard`, section 2.2.) `Linear` is a `declared` aspect (RFC-0212), granted only by the `linear` keyword in a declaration (struct, enum or named record) or in a closure's prefix or function type. A struct, record, enum or closure that holds a linear value must itself be declared `linear`, otherwise it is an error whose fix-it adds the keyword; the compiler checks the declared class against the fields (it must be at least as restrictive as every field). This supersedes the structural `auto` derivation of `Linear`, the `!Linear` opt-out, and the `affine` keyword: affine is the default and is never written. The amendment text is in sections 1, 2 and 2.1; the rest of this note is history.

> **New RFC, split out 2026-07-09** from `reports/substructural-types/linear-types.md`
> (a living design report) as part of decomposing an oversized RFC-0012 into smaller,
> independently reviewable pieces. Also resolves a lineage gap: RFC-0024 (Linear Types)
> was superseded by RFC-0028 (Memory and Reference Model), and RFC-0028 was refused —
> its own note says the foundation layer (linear types, owning pointers) "stands and
> may be implemented," but that content was never re-homed in an active RFC. This RFC
> is that re-homing, using the current, more developed design from `linear-types.md`
> rather than reviving RFC-0024's `linear`-keyword-only, `@T` read-reference form.
> Depends on RFC-0071 (Ownership and Move Semantics, integrated), RFC-0080 (Standard
> Library Aspects, for the auto-impl pattern), RFC-0081 (Negative Impls), and RFC-0072
> (Negative Bounds). No dependency on comptime derive (RFC-0092/0093).
>
> **Split 2026-11-05.** Sections 3 to 5 (partial consumption, the brand-carrying conversion, `NonLinear<T>`, the
> two-struct comparison) are RFC-0215; the notes below that mention them are the history of that text.

> **Revised 2026-07-09, later the same day.** §3 originally specified a bespoke
> "Option B" partial-consumption mechanism — ordinary field access directly off a
> nominal struct, with no record involved, requiring its own extension to RFC-0071
> §7's affine partial-move tracking for linear fields specifically. Decided against as
> a first implementation: `ToRecord` (RFC-0090) is the canonical mechanism instead —
> convert via `.to_record()`, move fields out of the resulting record value, where
> ordinary record field-narrowing (RFC-0090 §2-3) already determines the residual
> type. This removes a second, redundant partial-move mechanism that would have had to
> be built and maintained specifically for nominal structs, when records need
> equivalent field-narrowing semantics anyway. The real cost, stated plainly: a
> `Linear`-bearing struct now needs to additionally derive `ToRecord`/`FromRecord`
> before any of its fields can be partially consumed at all — plain structs with no
> such derive can only be consumed as a whole. §3 is rewritten accordingly, and this
> RFC now depends on RFC-0090 (specifically its `{ … }` type-former and tier 2, not
> tier 3 or RFC-0091's fuller automatic-downgrade extension) for the partial-
> consumption floor — the "no dependency on structural records" claim above no longer
> holds for that specific case, though the `Linear` aspect, lattice, and keyword sugar
> (§1-2, §4-5) remain fully independent of RFC-0090.
>
> **Revised 2026-07-10.** §3.1 added: fiat-linearity (§2.1) has a gap at the `ToRecord`
> boundary — a record's `Linear` status is always recomputed from its row alone (RFC-0090
> §5), so a struct forced `Linear` by fiat rather than by any field's own multiplicity
> silently loses that status on conversion. Resolved using a brand, not a synthetic field:
> the derived conversion for such a struct carries the source's brand, and the derive
> emits one ordinary explicit `impl Linear` against that specific branded shape.
> Corresponding amendment in RFC-0090 §8.
>
> **Revised 2026-07-24 — mechanical syntax sweep, no semantic change.** RFC-0090 dropped
> the `record` keyword from the anonymous type-former, so every `record { … }` here is now
> `{ … }`. This touches §3.1's branded-shape notation most visibly: the fiat-linear
> conversion's output is now written `{ id: i64 } @ 'receipt-origin` rather than
> `record { id: i64 } @ 'receipt-origin`, and the emitted impl targets
> `extend { id: i64 }: Linear @ 'receipt-origin`. **The brand is doing more visual work
> now that the keyword is gone** — `{ id: i64 }` and `{ id: i64 } @ 'receipt-origin` differ
> only by the tag, which is exactly §3.1's point (unrelated same-shaped records carry no
> such brand and so do not match the impl), but it is less obvious at a glance than it was.
> No change to the mechanism.

> **Status — under review (2026-07-21).** Reviewing the records/views substrate cluster together, per OBJECTIVES.md Priority 1 (reordered 2026-07-22). The cluster's first deliverable is the record/row semantics themselves -- RFC-0090 SS3 step 1's closed `{ … }` type-former plus `HasField` -- not the `ToRecord`/`FromRecord` conversions the blog names, which are tier 2 of RFC-0090 SS8 and convert into a type-former that must exist first. Thorough draft with a substantiated primary proposal; open questions remain, chiefly the RFC-0089/RFC-0090 dependency direction that Trigger 6 tracks.

> **Status — draft (2026-07-24).** Deferred 2026-07-24: per-field multiplicity waits until records are implemented. The RFC-0090 coupling was introduced by accident (RFC-0089's 2026-07-09 same-day revision rewrote its floor from Option B to ToRecord), which is why Trigger 6 could observe that neither RFC states the conflict. Returned to draft so the records cluster is not gated on it and the review backlog reflects what is actually reviewable.

> **Status — under review (2026-09-03).** Re-promoted 2026-09-03: the 2026-07-24 deferral condition (wait until records ship) is substantially met -- RFC-0116/0117/0118 implemented/integrated, RFC-0120 accepted; RFC-0119 (the ToRecord floor sec3 depends on) still under review but milestoned v0.13.1, ahead of this RFC's own v0.21.1 target. Milestoned v0.21.1 as a third design-settlement lane alongside RFC-0140/RFC-0003, not folded into v0.20.0's in-flight substrate milestone. metel-core#953.

> **Status — accepted (2026-11-05).** Ratified in the Copy and Clone settlement sweep (metel-core#1824); spellings ratified by the language owner 2026-11-05

## Summary

Adds an opt-in `Linear` aspect: a value whose type is `Linear` must be consumed exactly
once — not silently dropped, not used twice. This sits on top of RFC-0071's existing
affine-by-default model rather than replacing it: affine already means "at most once, no
duplication"; `Linear` narrows that to "at least once too," ruling out silent drop.
Linearity is checked statically, no runtime overhead. Partial consumption of a struct
with mixed multiplicities (some `Linear` fields, some not) moved to RFC-0215 on 2026-11-05; this RFC is the
lattice, the aspect and the class keywords (`copy`, `linear`) that the Copy and Clone settlement
(RFC-0206) depends on.

---

## Motivation

RFC-0071 makes affine ownership — move-by-default, at most once, no implicit copy — the
default for every field. That default has no way to express "this value's consumption
is mandatory," the property closing/freeing/releasing patterns actually need: a file
handle, a lock guard, a one-shot capability token. Today, that has to be enforced by
convention or a runtime check (a "was this closed?" flag, checked at drop time). `Linear`
makes it a compile-time-checked property instead — the type itself refuses to compile if
a value goes unused.

---

> **Prior-art note (2026-11-05).** Rust's ownership is affine, not linear: destruction is not guaranteed and
> safe `mem::forget` can discard ownership without cleanup, so Rust is evidence for the affine default and against
> reading it as exactly-once resource discharge. Austral's `Free`/`Linear` universes, Linear Haskell's multiplicities,
> Idris 2's quantities, Swift's `~Copyable` and Mojo's explicit destruction are the comparisons for `linear`
> (architecture/reports/copy-clone-prior-art-survey.md, section 7).

## 1. The multiplicity lattice

Quantitative type theory (Atkey 2018, Idris 2, Linear Haskell) typically uses a
three-point lattice — 0 (erased) / 1 (linear) / ω (unrestricted) — assuming an
ω-default background where ordinary bindings are already freely copyable. Metel inverts
this: RFC-0071 makes affine the default for every field, and ω-like unrestricted
behavior is something opted into via `Copy`. A three-point lattice has no point for
Metel's actual default. The lattice needs four:

```
0      — erased: a compile-time-only marker (a brand, a phantom state tag);
         not present as a runtime value at all
1      — linear: exactly once; no weakening (can't silently drop), no contraction
         (can't duplicate); must be explicitly consumed
affine — at most once: weakening allowed (may drop; Drop::drop runs), no
         contraction (can't duplicate); THE DEFAULT for ordinary fields (RFC-0071)
ω      — unrestricted: weakening and contraction both allowed; Copy fields
```

Ordered by how much the discipline permits: `1` is strictly more restrictive than
`affine` (affine additionally allows silent dropping); `affine` is strictly more
restrictive than `ω` (ω additionally allows duplication). `0` sits outside this
ordering — it's not "fewer uses," it's "not a runtime value," and behaves the way
`PhantomBrand` (RFC-0074) and phantom type-state parameters already do.

**A type's class is declared and checked against its fields (amendment 2026-11-06).** For a named type with no type
parameters the class is never inferred (a generic instance and a structural type compute theirs, section 2). The declared class must be at least as restrictive as the class of every field (`1` more restrictive than
`affine`, `affine` more than `ω`): a `copy` type needs every field `Copy`; an undeclared (affine) type may hold no
linear field; a `linear` type may hold anything, including no linear field at all (a capability token wrapping an
`i64`). A mismatch is an error at the field, and the fix-it adds the missing keyword (`declare it \`linear struct\``).
This is the earlier "most restrictive field wins" rule turned from a computation into a check. `Drop` is compatible with
`affine` only: not with `ω`, because a representation copy cannot perform the per-owner cleanup bookkeeping
a destructor needs, and not with `1`, because a linear value is never implicitly discarded (section 2).
RFC-0071 §4's `Copy`/`Drop` exclusion is the first of these two facts, and the lattice states them
together; the exclusion rests on those operational reasons, not on the ordering alone (weakening says
that discarding is permitted, not that discarding cannot run cleanup).

---

## 2. `Linear` as an aspect

```metel
declared aspect Linear;
```

A marker aspect that is `declared` (RFC-0212), like `Copy`: it is granted only in a type's declaration by the
`linear` keyword, never by `extend`, and for a type with no type parameters never inferred from the fields. There is no
`#derive(Linear)` and no structural `auto` rule for named types. The check runs the other way: a struct, record or enum that holds a linear
field (or a closure that captures a linear value) and is not declared `linear` is an error at the field, and the
diagnostic suggests the keyword. There is no `!Linear` opt-out (no negative impl), because nothing is inferred for it to opt out of. The negative *bound* `T: !Linear` of RFC-0072 remains a legal bound form.

- **Generic types.** A generic type's class is **computed per instantiation** from its owned fields, as a tuple's is
  (the keyword is not needed to admit a linear argument). `linear` on a generic type is **unconditional**: every
  instantiation is linear. `copy` states a capability: `Copy` exactly when the fields are. A type parameter written
  `T: Discard` forbids linear arguments. A field whose type **mentions no type parameter** and is linear (a concrete linear
  type) forces `linear` on the declaration, as for a non-generic type (D10, decided 2026-11-07), with the same error at
  the field and a fix-it that adds the keyword. The test is syntactic and needs no solver. A field such as
  `ticket: Ticket<T>`, which mentions `T` but is linear for every `T`, is not caught by it: the type's class then
  computes as linear without the keyword, which for a `pub` type is caught at the declaration by the checked `Discard`
  condition of RFC-0206 section 6 (D19), and for a private type surfaces at the drop sites. Details in section 2.2.
- **Types with no declaration site** (tuples, arrays, anonymous records) cannot carry the keyword. They are linear
  when a component is, by a compiler rule like the existing tuple and array rules for `Copy`.
- **Closures** are declared `linear` explicitly in the literal's prefix and in a function type (RFC-0194): a closure
  that captures a linear value without `linear` is an error whose fix-it adds it. `linear` implies `once`.

**Consuming an aggregate that is not known `Discard` (decided 2026-11-06, revised 2026-11-07).** A partial move out of a
nominal aggregate (struct, enum, named record) is legal only when the aggregate is **known `Discard`** in the current
context, so the leftover can be dropped (as today, where every type is `Discard`). Otherwise the aggregate is linear,
declared or computed, or possibly linear because it holds a parameter-dependent field of an unbounded `T`, and it is
consumed whole: by **total destructuring**, or by passing it to a function that consumes it. There are no residuals of
such an aggregate, which removes the question of whether a type was linear for its field or by fiat, and the rule does
not depend on how the class was determined.
- Reading a `Copy` field and borrowing a field (`&r.t`, `&var r.t`) change no ownership state and stay legal.
- **A destructuring pattern consumes its scrutinee** (decided 2026-11-07). Bound fields move; a field skipped by `..` or
  `_` is inaccessible afterwards and, where the aggregate is not known `Discard`, must itself be `Discard`. A pattern
  never leaves a partially moved residual: partial moves come only from explicit field moves. This holds for struct,
  tuple and enum-payload patterns, as it already does for a record rest binding (`{ x, ..rest }`). Skipped fields drop
  at the scrutinee's scope end; whether they should drop at the pattern is open (metel-core#1843). These rules
  describe **owning** patterns: matching through a reference keeps the reference-matching rules and consumes nothing.
  Ownership moves to the selected arm only, and a guard sees its bindings without moving them until it succeeds. A
  whole-value `_` destructures nothing and consumes nothing (a linear scrutinee under `_ =>` stays unconsumed and is an
  error); the skip check applies to `_` and `..` inside a destructuring pattern. A pattern on a value that an explicit
  field move already narrowed is rejected, as is any whole use of it. A refutable form added later must keep ownership
  on the non-matching path.
- Assigning to a linear field would drop its old value, so it is an error; replace by destructuring and rebuilding.
- Record spread (`{ ..r, n = 5 }`) consumes `r` totally and is legal when the replaced fields are `Discard`.
- A fiat `linear record` (no linear field) is allowed: destructuring it is an explicit consumption, so it cannot be
  dropped, but with public fields it does not protect a protocol against outside code; a `linear struct` with private
  fields can.
- **A type with a `Drop` impl, conditional or not, is dismantled only by a marked method** (D13, decided 2026-11-07).
  A *dismantling method* is an inherent method in the type's defining module whose receiver is an owned `self` carrying
  the dismantling marker (the spelling is open and settles with the `pub` sweep, RFC-0218; it is written `consume self`
  below as a placeholder). Its body destructures `self` totally: every field is bound or skipped (skipped fields
  `Discard`), and each bound field is moved on or dropped. The outer destructor is **suppressed**; nested field
  destructors still run when a field is skipped or dropped, and binding a field does not license dropping a bare `T`.
  The marker is not allowed on `&self` or `&var self`, in an aspect default body, on an aspect impl method, or outside
  the defining module. Without the marker such a type is never destructured, partially moved or used in a record
  spread, even in its own module. Callers see an ordinary consuming method. This is how a wrapper such as `Logged<T>`
  is unwrapped (`into_inner`), including for a linear `T`, where no destructor applies.
- This extends the existing enum rule (matching a variant and moving its payload consumes the enum wholly).
**Structural types are the exception.** An anonymous record or a tuple has no declaration: its class is computed from
its components (as `Copy` is for a tuple), so a field move narrows it and the leftover's class is recomputed, with the
obligation travelling with the moved value. Destructuring any aggregate and rebuilding an anonymous record or tuple from
the pieces is available as an escape hatch (except for a type with a `Drop` impl outside a dismantling method).

**`Clone` is not contraction (decided 2026-11-05).** `Clone` is explicit creation of another value, not the
implicit duplication that linearity forbids, so a linear type may have a **written** `Clone`: the author asserts that
another instance is valid (for example opening another handle). A **derived** `Clone` requires every field to satisfy
`Clone`, including linear fields; a fiat-linear resource leaf supplies a written one, and a struct whose linear field
already has a valid `Clone` (derived or written) derives normally. Forbidding `Clone` on linear types would stop a user
from duplicating a resource deliberately.

**Mutually exclusive with `Copy`** (`ω` and `1` can't coexist in the same field) **and
with `Drop`.** `Drop`'s triggers — implicit scope-end, the generic `drop(x)` free
function — have no legitimate firing point for a value that can never legally reach
scope-end unconsumed, and `drop`'s signature should require `T: Discard` (section 2.2; an earlier
draft excluded `Linear` with a negative bound, `T: !Linear`), specifically to avoid a documented
hazard (RFC-0049): a generic `drop` that discharges a linearity obligation without
running real cleanup ("`drop(f)` appears to work but leaves captured values dangling").
A linear type's teardown logic lives in an ordinary, author-named consuming method
instead, called directly.

### 2.1 Surface syntax: aspect, keyword, or a mix

Every mechanism that needs `Linear` in a bound position (`HasField`/`Lacks` conditions in RFC-0090, residual
recomposition in RFC-0091) needs `Linear` to be usable as an aspect, not just a keyword. A bare keyword with no backing
aspect either collapses into aspect sugar or is a strictly weaker mechanism that can't participate in the rest of this
design. So `Linear` is a `declared` aspect and the keyword is its one spelling:

```metel
linear struct Receipt { id: i64 }            // a capability token wrapping a plain i64: linear with no linear field
linear struct Guard { t: Token }             // required: a field is linear
struct Plain { t: Token }                    // error: field `t` is linear; declare it `linear struct Plain`
```

The keyword applies to `struct`, `enum` and named `record` (RFC-0120), which have a declaration site, and never to
the anonymous `{ … }` type-former (RFC-0090): a record there is *just* its row. `extend X: Linear {}` is not legal,
as for any `declared` aspect.

**There is no `affine` keyword (decided 2026-11-06).** Affine is the default class and is never written. `Copy` and
`Linear` are both declared only in a declaration, so nothing elsewhere in the codebase can change what moving a type
means, and a locking pair of negative impls would add nothing. **`Affine` needs no aspect of its own.** It's
definitionally "not `Copy` and not `Linear`" — `T: !Copy + !Linear` (RFC-0072's mixed positive/negative bound form)
says it, and RFC-0039 (`aspect` Alias Syntax, `1-under-review`) is the vehicle to name it:

```metel
aspect Affine = !Copy + !Linear
```

### 2.2 Generic code and the capability to discard (revised 2026-11-07: capabilities are bounds)

**The problem.** A generic body can do two things to a value of parameter type `T` without writing a call: copy it
and drop it. A copy happens at a visible use site (a second use of `x` is a use-after-move unless `T: Copy`), so the
author is told. A **drop** is implicit: scope end, an early `return` or `?`, an overwritten assignment, an unused
argument, a discarded expression statement, the unmoved rest of a partial move. If a bare `T` were affine, a linear
type could never instantiate it and generic code could not be used with linear types at all.

**The decision (language owner, 2026-11-07).** A bare `T` is **possibly linear** and assumes no capabilities (Rust is not
an exact precedent: its type parameters carry an implicit `Sized` bound). Each
operation that needs one names it in a bound, as `Copy` already does:

| Operation | Bound | Bare `T` |
|---|---|---|
| duplicate implicitly | `T: Copy` | not allowed |
| duplicate explicitly | `T: Clone` | not allowed |
| drop | `T: Discard` | not allowed |

Nothing is inferred. Generic bodies are checked once, at the definition, against their declared bounds (RFC-0173,
unchanged).

**The capability.** `Discard` says a value may be dropped. It is positive, so generic code never needs the absence
reasoning that RFC-0213 section 3 keeps out of v0.16.0.
1. For a concrete type, `Discard` holds exactly when the type's class (declared, or computed for a generic
   instantiation or a structural type) is not linear. `Drop` types are `Discard`: their drop runs. `T: Copy` entails
   `T: Discard`. **No user writes or negates a `Discard` impl.**
2. For a type parameter, `Discard` holds only if a bound says so.
3. The generic `drop` is `drop<T: Discard>`, replacing the `T: !Linear` of section 2.

**Rules.**
- **Bodies.** A generic body may consume a `T` (move it, return it, pass it, store it). It may not drop or copy it
  unless a bound entails `Discard` or `Copy`. Each implicit drop site (the list under "The problem") and each explicit
  `drop(x)` of a value whose `Discard` depends on a parameter is an error at that site, and the diagnostic suggests the
  bound (`add T: Discard`), as omitting `once` on a closure that consumes a capture does (RFC-0134).
- **Calls.** A callee's `T: Discard` bound must be entailed by the caller's bounds, by the ordinary bound rule. A
  function that only forwards a `T` to a function that drops it needs the bound too.
- **Generic types.** A generic type's parameters are **open by default** (they admit linear arguments), and its class
  is computed per instantiation from its owned fields, as a tuple's is. `linear` on a generic type is unconditional
  (every instantiation is linear). `copy` states a capability (`Copy` exactly when the fields are). A field that
  mentions no type parameter and is linear forces `linear` on the declaration (section 2). A parameter written `T: Discard` forbids
  linear arguments: instantiating it with one is an error naming the parameter. Naming such a type requires its bound at
  every use, by the ordinary well-formedness rule. A derived impl that requires `Discard`, or a field of a type whose
  parameter is `Discard`-bounded, is an error that suggests `T: Discard`.
- **`Drop` impls.** A `Drop` impl must prove its target `Discard` under the impl's bounds: an unconditional
  `extend<T> Foo<T>: Drop` is rejected when `Discard` of the target cannot be proved (`View<T> { value: &T }` owns
  no `T`, so its unconditional impl is legal), and a conditional `extend<T: Discard> Foo<T>: Drop` is the way to give a generic
  type a destructor without closing it to linear arguments. A conditional impl adds no bound to the type declaration.
  `Foo<Tx>` then exists, is linear and has no destructor. This is the same exclusion check as for `Copy` and `Drop` at
  an instantiation (RFC-0213). A type with any `Drop` impl is dismantled only by a marked dismantling method, by total destructuring that suppresses the destructor (section 2).
- **Methods.** In a generic impl the bound attaches to the method (`where T: Discard`), so `Option<Tx>` exists and
  `unwrap_or` is available only when `T: Discard`.
- **Conformance.** An impl method's requirements must be entailed by the impl's bounds, as for any aspect (an impl
  cannot silently strengthen an aspect contract).
- **Function values.** A function value that is not declared `linear` is `Discard`: a closure that captures a linear
  value must be declared `linear` (RFC-0194), so every captured value of a non-`linear` closure is droppable. A
  function type that is not `linear` therefore guarantees `Discard`, and `Option::map` may drop its callback. A
  `linear` function type is not `Discard`. A closure that captures a value of bare type `T` captures a possibly-linear
  value, so it must be declared `linear`, or the function must bound `T: Discard`.
- **Trait objects.** Coercing a possibly-linear value into `dyn Aspect` erases its class. Before `linear` ships this must
  be rejected, or the `dyn` type must retain the obligation (the existential-erasure gate, metel-core#1828).

**The cost, stated plainly.** `T: Discard` is needed whenever generic code drops a by-value `T`: `unwrap_or`, `ok`, an
ignored argument, `print<T: Display>(x: T)`. A scan of std and the integration programs (2026-11-05) found that 30 to
40 % of the functions taking a bare `T` by value drop it on some path, a floor that ignores locals and early returns.
That is a larger annotation cost than `Copy` bounds carry, and it is accepted for the same reason: the signature says
what the function may do with your value. Taking a reference where the function only reads (`print` and `println`
over `&T`) removes many of them. Metel has no users yet (language owner, 2026-11-07), so there is no lint or
migration-tool stage: the std audit below is done by hand.

**Staging.** In v0.16.0 every type is `Discard`, so `T: Discard` is accepted and always true, every bare `T` behaves
as the affine default does today, and no program changes. The check becomes an error at the `linear` release. What
v0.16.0 must do so that nothing is foreclosed:
1. The generic-body analysis (ADR-0063) records the drop sites of values whose type depends on a parameter, so the
   definition check can run when `linear` lands (metel-core#1827).
2. The aspect name `Discard` and the rule that a bare `T` is possibly linear are reserved here.
3. No std API documents a bare `T` as "droppable" as a guarantee.

**Demonstration (paper derivations, required before acceptance of sections 1 to 2.1).** Using `linear struct Tx
{ id: i64 }` and the rules above:
1. `fun identity<T>(x: T) -> T { x }`: `x` is moved into the result; there is no drop site, so no bound is needed.
   `identity(tx)` is accepted. **Follows.**
2. `struct Pair<T> { a: T, b: T }` (open by default, class computed): `Discard(Pair<T>)` is `Discard(T)`; `Pair<i64>`
   is `Discard`, `Pair<Tx>` is linear and must be consumed. `fun swap<T>(p: Pair<T>) -> Pair<T>` destructures `p`,
   moves both fields out and rebuilds: nothing is dropped, so no bound. **Follows.**
3. `Option<T>::unwrap_or(self, fallback: T) -> T where T: Discard`: the arm `Some { value } => value` drops
   `fallback`, so the bound is required and written; the arm `None => fallback` consumes it. `Option<Tx>::unwrap_or` is
   therefore unavailable and `Option<i64>::unwrap_or` is unchanged. `Option<T>::map(self, f)` has no `T` drop, and its
   `None` arm drops the closure `f`, which is `Discard` because a non-`linear` function type is. **Follows.**
4. A linear value ended through an author-named method: `fun commit(tx: Tx) { let Tx { id } := tx; flush(id); }` is
   checked in its own body (the destructured `i64` fields are `Discard`). Generic code reaches it through a declared
   aspect: `aspect Finish { fun finish(self); }`, `extend Tx: Finish { fun finish(self) { commit(self) } }` and
   `fun run<T: Finish>(x: T) { x.finish() }`. `x` is moved into the call, so `run` needs no `Discard`, and
   `run(tx)` is accepted. **Follows.**
5. Helper and wrapper: `fun sink<T: Discard>(x: T) { }` writes the bound; `fun api<T: Discard>(x: T) { sink(x) }` must
   write it too, by the ordinary rule (without it, `sink(x)` is an error that suggests it). **Follows.**
6. `List<T>` holding linear values. **Classification needs a named temporary rule.** `List<T>` declares `inner: [T]`,
   and RFC-0206 section 2 makes a view `[T]` `Copy` (hence `Discard`) for every `T`, so field composition alone gives
   `List<Tx>` no linear obligation and `fun abandon(xs: List<Tx>) { }` would be accepted. Until the std List is
   redesigned, the compiler applies a **named native rule**, `Discard(List<T>) = Discard(T)`, so `List<Tx>` is linear.
   Its exit is an owning-storage kind distinct from the `[T]` view (metel-core#1826). The rest of the derivation needs a
   std change at `linear` time:
   - The destructor becomes conditional, `extend<T: Discard> List<T>: Drop`, so `List<Tx>` has **no implicit
     destructor**. `push` and `pop` are unchanged (they move). `clear` and any other dropping method write
     `where T: Discard`.
   - **The ender is a native consuming method:** `native fun consume_each(self, f: |T|)`. It takes ownership of the
     list, calls `f` once per element (each linear element is moved into `f`), and frees the backing storage. The
     native's contract, trusted like the other std natives (`copy_value`, RFC-0206 section 2), is that it consumes every
     element exactly once.
   - Emptying a list does **not** consume it: after a `pop` loop the value is still a `List<Tx>` and still has to be
     ended. `fun end_all(xs: List<Tx>) { xs.consume_each(|t| commit(t)); }` ends a list.
   - **Depends on:** the closure `f` being `Discard` (a non-`linear` function type is, RFC-0194),
     the native's contract, and the temporary rule above; all tracked in metel-core#1826 and the linear-release gate
     #1828.
   **Follows, given the named rule, the std change, the native contract and the closure rule.**

**Std audit list** (the functions that drop and so write a bound, per parameter): `Option::unwrap_or` needs `T: Discard`
(the unused fallback); `Option::ok_or` needs `E: Discard` (the unused error), not `T`; `Result::ok` needs `E: Discard`;
`Result::unwrap_or` needs both `T: Discard` and `E: Discard`; `Result::unwrap_or_else` needs `E: Discard`;
`map` and `and_then` need no bound (their callbacks are `Discard`); `print` and `println` (or take `&T`);
`__eq_array_item`; and for lists: the conditional destructor, `clear`, and the native `consume_each`, which must **not**
require element `Discard` since it is the linear teardown (item 6). Borrowing `Eq` and `Hash` need no discard capability;
a helper taking compared values by value does.

**Alternatives considered.** (a) *A written `T: ?Linear` opt-in on an affine default*: linear types are locked out of
every generic function until its author opts in (Swift needed several releases, SE-0427). (b) *A `T: Discard` required
on a closed default for types and an explicit admission marker per parameter* (the Austral shape, `T: ?Discard`):
generic code would have to opt in to admit linear values, which defeats the goal. (c) *Silent elaboration of `Discard`*
from bodies, with use-site diagnostics, optional pins, a strict mode and an API-diff tool: no annotation cost, but it
needs transitive inference machinery (callees, recursive groups, well-formedness) and a named exception to RFC-0173,
and a public change can silently stop accepting linear arguments. Considered and set aside on 2026-11-07 in favour of
explicit bounds. (d) *Check drop sites at each instantiation* (C++-template style): no bounds to write, but a body change
breaks callers and it contradicts RFC-0173. (e) *Let a generic drop of a linear value run a type-supplied cleanup*:
the value is then affine with a destructor, not linear.

**Open (exit tracking: metel-core#1828, the linear-release gate).** The spelling `Discard`; whether an explicit
`where T: !Discard` ("this parameter must be linear") is ever needed (probably not); the rule that moving every field out consumes a struct (RFC-0215); whether `print` and `println` take `&T`.

---

> **Sections 3 to 5 moved to RFC-0215 on 2026-11-05.** Partial consumption through `ToRecord`, the brand-carrying
> conversion for fiat-linear structs (old section 3.1), `NonLinear<T>` and the two-struct comparison are in
> RFC-0215 (Partial Consumption of Mixed-Multiplicity Structs), which keeps their section numbers. This RFC is
> now the lattice (section 1), the `Linear` aspect and its exclusions (section 2) and the class keywords
> (section 2.1), which the Copy and Clone settlement (RFC-0206) depends on at the design level.

---

## Open Questions

1. Ship the four-point lattice (§1) as the documented model: **resolved 2026-11-05**, yes; the settlement of
   RFC-0206 is written against it.
2. The `copy` and `linear` class keywords (§2.1): **resolved 2026-11-05, amended 2026-11-06**. `copy struct P` = `struct P
   derives Copy`; `linear struct T` grants the declared aspect `Linear`; there is **no `affine` keyword**; `Linear` is
   declared and checked against the fields, not inferred. In v0.16.0 `copy` is implemented and `linear` is reserved
   ("Planned for"). Applies to structs, enums and named records, not the anonymous record type.
3. *(Moved to RFC-0215.)* `NonLinear<T>`'s surface syntax.
4. Multiplicity polymorphism (`Guarded<T, Cap>` generic over a field's multiplicity) — noted as a real, later
   extension; not attempted here.
5. **The default for an unbounded type parameter with respect to `Linear`**: **decided 2026-11-05, revised 2026-11-07**, section 2.2. A bare `T`
   is possibly linear and assumes no capabilities; dropping it requires a written `T: Discard`, as copying requires
   `T: Copy`. Nothing is inferred. In v0.16.0 every type is `Discard`, so nothing changes for existing programs. The
   demonstration required there remains a gate for accepting sections 1 to 2.1.
6. *(Moved to RFC-0215.)* The brand-carrying `ToRecord` for fiat-linear structs.
7. **Binding-level strengthening** (a `linear` binding, parameter, return or field on an ordinary type, never looser than the type): designed as an extension on 2026-11-06 and drafted as RFC-0220. It is local discipline and does not change the declared-class model of sections 1 to 2.1.

---

## References

- RFC-0071 (Ownership and Move Semantics, integrated 2026-07-24, target v0.12.0) —
  affine-by-default foundation this RFC builds on
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern `Linear` reuses (§2),
  substituting `Linear` for `Send`
- RFC-0096 (Auto-Impl Aspects, under review) — formalizes that pattern once, generically,
  rather than each auto-impl aspect (`Send`/`Sync`/`Linear`) restating it
- RFC-0081 (Negative Impls) — negative impls; `Linear` is no longer opted out of (it is declared, not inferred)
- RFC-0072 (Negative Bounds) — `T: !Copy + !Linear` compound bound form (§2.1)
- RFC-0039 (`aspect` Alias Syntax, `1-under-review`) — vehicle for the `Affine` alias (§2.1)
- RFC-0049 (Linear Function Type System, superseded by RFC-0194) — documents the generic-`drop`-discharges-
  linearity hazard this RFC's `drop<T: !Linear>` avoids
- RFC-0063 (Allocator Handles, accepted) — §9 item 5's deadline this RFC's §3
  satisfies, together with RFC-0090
- RFC-0090 (Structural Records — Rows and Tiers) — the `{ … }` type-former and tier 2
  (`ToRecord`/`FromRecord`) §3 depends on as the canonical partial-consumption
  mechanism; §8 there carries the corresponding amendment for §3.1's brand-carrying
  conversion
- RFC-0074 (Shared Ownership), RFC-0076 (Rc Brands) — brand rigidity/freshness
  properties §3.1's derive-emitted impl depends on being unforgeable from outside
- `brand-kind-unification.md` — the erased/value-channel distinction (§4 there) that
  separates "a brand carries the obligation" (no) from "a brand preserves identity so
  the obligation can still be checked" (yes), the distinction §3.1 turns on
- RFC-0024 (Linear Types, superseded) — prior exploration; superseded by RFC-0028
- RFC-0028 (Memory and Reference Model, refused) — its foundation-layer content is what
  this RFC re-homes, using the more developed design from `linear-types.md` rather than
  RFC-0024's original form
- `reports/substructural-types/linear-types.md` — the living design report this RFC is
  extracted from
- RFC-0091 (Linear Records) — the record-based fuller extension of §3's partial
  consumption, depends on this RFC
- Prior art: `archive/per-field-multiplicities.md` — the multiplicity lattice's
  theoretical foundation (Atkey 2018, Idris 2, Linear Haskell)

---

## Decision

**Outcome:** *(pending)*
**Target:** unspecified; the partial-consumption floor (now RFC-0215 §3) is required before RFC-0071/RFC-0067 Phase 3 begins
per RFC-0063 §9 item 5.

*(Decision rationale goes here when the RFC is evaluated.)*
