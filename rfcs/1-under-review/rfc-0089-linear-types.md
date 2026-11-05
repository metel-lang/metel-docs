---
id: rfc-0089
title: "Linear Types"
date: '2026-07-09'
status: under-review
updated: '2026-09-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/953'
---

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

## Summary

Adds an opt-in `Linear` aspect: a value whose type is `Linear` must be consumed exactly
once — not silently dropped, not used twice. This sits on top of RFC-0071's existing
affine-by-default model rather than replacing it: affine already means "at most once, no
duplication"; `Linear` narrows that to "at least once too," ruling out silent drop.
Linearity is checked statically, no runtime overhead. Partial consumption of a struct
with mixed multiplicities (some `Linear` fields, some not) moved to RFC-0215 on 2026-11-05; this RFC is the
lattice, the aspect and the class keywords (`copy`, `affine`, `linear`) that the Copy and Clone settlement
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

**A struct's overall discipline is the most restrictive of its fields' multiplicities**
(`1` is more restrictive than `affine`, and `affine` than `ω`; this is the meet toward restriction,
not a join toward permissiveness, which an earlier draft of this paragraph said and then contradicted).
A struct with any `1` field is linear overall; a struct with only `affine`/`ω` fields (no `1`) is
affine overall; a struct with only `ω` fields may (if it opts in) be `Copy`. `Drop` is compatible with
`affine` only: not with `ω`, because a representation copy cannot perform the per-owner cleanup bookkeeping
a destructor needs, and not with `1`, because a linear value is never implicitly discarded (section 2).
RFC-0071 §4's `Copy`/`Drop` exclusion is the first of these two facts, and the lattice states them
together; the exclusion rests on those operational reasons, not on the ordering alone (weakening says
that discarding is permitted, not that discarding cannot run cleanup).

---

## 2. `Linear` as an aspect

```metel
aspect Linear { }
```

A marker aspect, structurally identical in form to `Send` (RFC-0080). Auto-derived, not
opt-in: a struct containing a multiplicity-`1` field is `Linear` automatically, per
RFC-0080 §3.2's auto-impl rule (the same structural-composition mechanism that grants
`Send`/`Sync`, substituting `Linear` for `Send`), matching the lattice's composition rule
directly rather than being a bespoke case — RFC-0096 (2026-07-11) is where that
mechanism is now formalized once, generically, since this citation and RFC-0080 §3.2's
own text were the two places it was previously only informally assumed. **No
`#derive(Linear)` annotation is needed or meaningful** — this is category 1 (auto-trait
structural composition), not category 2 (derive-as-codegen); it should never appear in
a derivable-aspects list alongside `Clone`/`Eq`/`Display` (RFC-0093 §"Derivable Aspects"
corrects an earlier draft's error on exactly this point). A type
with a `Linear` field **cannot opt out**: `extend X: !Linear;` on it is an error, because the assertion would make the
field's exactly-once obligation disappear (Austral likewise refuses to classify a structurally linear type as
freely usable). `!Linear` is accepted where no field is `Linear`, for example the locking pair of `affine struct`
(section 2.1), which prevents a later fiat grant.

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

Every mechanism that needs `Linear` in a bound position (`drop<T: !Linear>`,
`HasField`/`Lacks` conditions in RFC-0090, residual recomposition in RFC-0091) needs
`Linear` to be usable as an aspect, not just a keyword. A bare keyword with no backing
aspect either collapses into aspect sugar or is a strictly weaker mechanism that can't
participate in the rest of this design. Aspect-plus-sugar wins on one real capability:
declaring a type linear *by fiat* when nothing about its fields structurally requires
it (a capability token wrapping a plain `i64`, say):

```metel
extend Receipt: Linear {}          // explicit, forces it
linear struct Receipt { id: i64 }   // proposed sugar for exactly the line above
```

The keyword should stay struct-only, never extended to the `{ … }` type-former
(RFC-0090) — records have no declaration site to attach it to, and forcing a
structurally-plain row to be linear "by fiat" undermines the premise that a record is
*just* its row.

**`Affine` needs no aspect of its own.** It's definitionally "not `Copy` and not
`Linear`" — `T: !Copy + !Linear` (RFC-0072's already-accepted mixed positive/negative
bound form) already says it. RFC-0039 (`aspect` Alias Syntax, `1-under-review`) is the vehicle to
name it without writing the compound bound at every call site:

```metel
aspect Affine = !Copy + !Linear
```

Symmetrically to `linear struct`, a struct-only `affine struct` keyword would desugar
to a *locking pair of negative impls* — `extend X: !Copy; extend X: !Linear;` —
not a positive capability grant, since affine is an absence, not an addition. That pair
is more than documentation: RFC-0081's negative impls override any later conflicting
impl via ordinary coherence, so `affine struct Handle { fd: i64 }` is a real, checked
commitment that nothing elsewhere in the codebase can later add `extend Handle: Copy`
and silently change what moving a `Handle` means.


### 2.2 Generic code and the capability to discard (accepted 2026-11-05; repaired after review 5)

**The problem.** A generic body can do two things to a value of parameter type `T` without writing a call: copy it
and drop it. A copy happens at a visible use site (a second use of `x` is a use-after-move unless `T: Copy`), so the
author is told. A **drop** is implicit: scope end, an early `return` or `?`, an overwritten assignment, an unused
argument, a discarded expression statement, the unmoved rest of a partial move. If a bare `T` is affine (the
RFC-0071 default), then a linear type can never instantiate it, and generic code cannot be used with linear
types at all. If a bare `T` is possibly linear and the author must write the bound, nearly every generic
function that ever drops needs one. A scan of std and the integration programs (2026-11-05) found that 30 to 40 % of
the functions that take a bare `T` by value drop it on some path (`unwrap_or` drops its fallback, `ok` drops the
error, `print` takes a `T: Display` by value and only borrows it); the count is a floor, since it ignores locals,
early returns and drops through `Option<T>` or `List<T>`.

**The capability.** `Discard` is an aspect that says a value may be dropped. It is a positive capability, so
generic code never needs the absence reasoning that RFC-0213 section 3 keeps out of v0.16.0.
1. For a concrete type, `Discard` holds exactly when the type is not `Linear`. It is **computed by the compiler**
   (an `auto` aspect, RFC-0212, structural as `Send` is, RFC-0096): a type is `Discard` when all its fields are,
   and it is not linear by fiat. `Drop` types are `Discard`: their drop runs. `T: Copy` entails `T: Discard`.
   **No user writes or negates a `Discard` impl.** Only fiat (`linear struct`, section 2.1) removes it.
2. For a type parameter, `Discard` holds only if a bound says so (`T: Discard`, or `T: Copy`).
3. The generic `drop` is `drop<T: Discard>`, replacing the `T: !Linear` of section 2.
4. **Obligation versus published capability.** The computed `Discard`/`Linear` obligation is determined by
   representation and fiat and is exact. A public type may state a stronger condition for what generic code sees
   (RFC-0206 section 6); that can **withhold** `Discard` but can never create it or suppress a structural linear
   obligation, so a public annotation cannot make a linear value droppable. `Linear` and `Discard` are complements
   for the computed obligation only.

**Bare `T` is possibly linear.** A generic body may consume a `T` (move it, return it, pass it, store it) and may
not drop or copy it unless the bounds say so. This is the strictest assumption and the one under which the body is
checked, once, at its definition (RFC-0173).

**Elaboration of `Discard`.** The compiler collects `Discard` obligations from two sources and adds them to the
function's bounds: (a) every implicit drop of a value whose `Discard` depends on a parameter (a `T`, or an
`Option<T>`, `List<T>` or struct holding one), and the explicit `drop(x)`; and (b) the interfaces of the callees,
after substitution, so a function that only forwards a `T` to a function that drops it inherits the obligation. The
body is then checked once against the elaborated bounds, so RFC-0173 holds in its checking rule: `T` is opaque and
supports only its bounds, one of which the compiler wrote. For a method of a generic impl, the bound attaches to the
method, not the impl, so `Option<Tx>` exists and `unwrap_or` is available only when `T: Discard`. The drop sites that
count are the six listed under "The problem".
- **Only `Discard` is elaborated.** Methods, operators, `Copy`, `Clone` and every other bound stay declared. The
  reason is the one above: a drop is the only implicit operation. This is a single named exception to "declared
  bounds", limited to the one implicit operation. **RFC-0173 is amended accordingly** ("declared bounds, plus the
  `Discard` elaboration defined in RFC-0089 section 2.2"): its "no inference" wording applies to every other bound.
  The amendment lands with the ratification sweep.
- **Recursive helpers.** The requirements of a recursive group are a least fixed point: obligations only
  accumulate, so the group is solved by iterating from the empty set until nothing is added (RFC-0206 section 2,
  "Recursion and termination").
- **No circularity with selection.** Obligations are computed against the declared dispatch. An implementation is
  never selected on a bound that the selection itself would cause to be inferred.
- **`pub` generic functions state the bound.** Once `linear` is implemented, a `pub` generic function must write
  every `Discard` obligation its body requires, including those inherited from callees (`pub fun api<T>(x: T) {
  relay(x) }` states `T: Discard` if `relay` requires it). The compiler must **suggest the inferred capability**
  in the diagnostic, as a fix-it that inserts the bound it computed, so the author confirms it instead of working it
  out. Otherwise a change from consuming to dropping would change the public interface silently and break linear
  callers. The rule covers every exported function: exported methods, re-exported items and a function value that
  escapes carry the stated bound in their type, not only a `pub` on the definition. Swift's SE-0426 is the nearest
  precedent, at the type level: exported types get no inferred `BitwiseCopyable`, because a current representation
  is not a lasting public promise. A non-`pub` function is elaborated silently. This is the rule of RFC-0206
  section 6 ("One rule for types and functions") applied to functions, with the same condition language.
- **Closures and trait objects.** Whether a closure value is `Discard` depends on what it captures and on its
  multiplicity qualifier (RFC-0134, RFC-0153); this section does not decide it. Before `linear` ships, erasing a
  possibly-linear capture behind a droppable closure value or an existential must be forbidden or must retain the
  obligation.

**Staging.** In v0.16.0 every type is `Discard`, so every bare `T` behaves exactly as the affine default does
today, no program changes, and `T: Discard` written explicitly is accepted and always true. What v0.16.0 must do so
that nothing is foreclosed:
1. The generic-body analysis (ADR-0063) records the drop sites of values whose type depends on a parameter, and the
   callee interfaces it consults. It needs the record to compute the elaboration when `linear` lands; today it does
   not report them. (Recording is migration preparation; it does not prove that existing APIs stay
   source-compatible when linearity arrives.)
2. The aspect name `Discard` and the rule that a bare `T` is possibly linear are reserved here.
3. No std API documents a bare `T` as "droppable" as a guarantee.

**Demonstration (paper derivations, required before acceptance of sections 1 to 2.1).** Using `linear struct Tx
{ id: i64 }` and the rules above:
1. `fun identity<T>(x: T) -> T { x }`: `x` is moved into the result; there is no drop site and no callee, so no
   obligation. `identity(tx)` is accepted. **Follows.**
2. `struct Pair<T> { a: T, b: T }`: `Discard(Pair<T>)` is `Discard(T)` (two equal atoms); `Pair<i64>` is `Discard`,
   `Pair<Tx>` is not, so it is linear by the exact predicate and must be consumed. `fun swap<T>(p: Pair<T>) ->
   Pair<T>` destructures `p`, moves both fields out and rebuilds: nothing is dropped, so no obligation. It assumes the
   rule that moving every field out of a by-value struct consumes it (a residual would need its own `Discard`;
   partial consumption of mixed fields is RFC-0215). **Follows, given that rule.**
3. `Option<T>::unwrap_or(self, fallback: T) -> T`: the arm `Some { value } => value` drops `fallback`, so the method
   elaborates `T: Discard`; the arm `None => fallback` consumes it. `Option<Tx>::unwrap_or` is therefore unavailable
   and `Option<i64>::unwrap_or` is unchanged. `Option<T>::map(self, f)` has no `T` drop, but its `None` arm drops
   the closure `f`, so it depends on the open closure-discard rule. **Follows for `unwrap_or`; `map` is open on closure
   discard.**
4. A linear value ended through an author-named method: `fun commit(tx: Tx) { let Tx { id } := tx; flush(id); }` is
   checked in its own body (the destructured `i64` fields are `Discard`), and generic code reaches it through a
   declared aspect, `aspect Finish { fun finish(self); }` with `fun run<T: Finish>(x: T) { x.finish() }`: `x` is
   moved into the call, so `run` needs no `Discard`. **Follows.**
5. Private helper and public wrapper: `fun sink<T>(x: T) { }` elaborates `T: Discard` silently;
   `pub fun api<T>(x: T) { sink(x) }` inherits it from the callee and, once `linear` ships, must state `T: Discard`
   (the diagnostic suggests it). **Follows.**
6. `Vec<T>`/`List<T>` holding linear values: **not established by today's std.** `List<T>` contains `[T]`, so
   `List<Tx>` is linear by the exact predicate, which is correct. But `List`'s destructor is native and
   unconditional, and an unconditional `Drop` conflicts with structural `Linear`. The derivation needs a std change at
   `linear` time: the destructor becomes conditional (`extend<T: Discard> List<T>: Drop`), `push` and `pop` are
   unchanged (they move), `clear` and any other dropping method elaborate `T: Discard`, and a consuming extraction
   (`pop` in a loop, or a `drain`/`into_each(self, f)` that consumes every element) is how a `List<Tx>` is ended.
   That change is part of the std audit below, not a v0.16.0 deliverable.

**Std audit list** (the functions that drop and so elaborate `Discard`): `Option::unwrap_or`, `Option::ok_or`,
`Result::unwrap_or`, `Result::unwrap_or_else`, `Result::ok`, `print`, `println`, `__eq_array_item`, and the list
destructor and `clear` (item 6).

**Alternatives considered.** (a) *A written `T: ?Linear` opt-in on an affine default*: works, but linear types are
locked out of every generic function until its author opts in (Swift needed several releases, SE-0427), and
`T: !Linear` for the `drop` signature needs absence reasoning. (b) *A written `T: Discard` on a linear default*: no
retrofit, but the author pays the 30 to 40 % of functions that drop, plus transitive cases, at once, and it is a
breaking change. (c) *Check drop sites at each instantiation* (C++-template style): no bounds to write, but a body
change breaks callers and it contradicts RFC-0173. (d) *Let a generic drop of a linear value run a
type-supplied cleanup*: no lock-out, but the value is then affine with a destructor, not linear, which defeats the
purpose. The decision takes inference for the one implicit operation, written bounds for everything else.

**Open.** The enforcement point for the `pub` rule (the release that implements `linear`); the spelling `Discard`;
whether an explicit `where T: !Discard` ("this parameter must be linear") is ever needed (probably not); closure
discard (RFC-0134, RFC-0153); the rule that moving every field out consumes a struct (RFC-0215).

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
2. Struct-and-enum `copy`/`affine`/`linear` keyword sugar (§2.1): **resolved 2026-11-05** in favour, for
   structs and enums, not the anonymous record type; the sugar is `copy struct P` = `struct P derives Copy`,
   `affine struct H` = the locking pair of negative impls, `linear struct T` = `extend T: Linear {}`. In v0.16.0
   `copy` and `affine` are implemented and `linear` is reserved ("Planned for").
3. *(Moved to RFC-0215.)* `NonLinear<T>`'s surface syntax.
4. Multiplicity polymorphism (`Guarded<T, Cap>` generic over a field's multiplicity) — noted as a real, later
   extension; not attempted here.
5. **The default for an unbounded type parameter with respect to `Linear`**: **decided 2026-11-05**, section 2.2. A bare `T`
   is possibly linear; `T: Discard` is elaborated for the one implicit operation (drop) and stated on `pub` functions
   once `linear` ships. In v0.16.0 every type is `Discard`, so nothing changes for existing programs. The
   demonstration required there remains a gate for accepting sections 1 to 2.1.
6. *(Moved to RFC-0215.)* The brand-carrying `ToRecord` for fiat-linear structs.

---

## References

- RFC-0071 (Ownership and Move Semantics, integrated 2026-07-24, target v0.12.0) —
  affine-by-default foundation this RFC builds on
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern `Linear` reuses (§2),
  substituting `Linear` for `Send`
- RFC-0096 (Auto-Impl Aspects, under review) — formalizes that pattern once, generically,
  rather than each auto-impl aspect (`Send`/`Sync`/`Linear`) restating it
- RFC-0081 (Negative Impls) — `extend X: !Linear;` opt-out
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
