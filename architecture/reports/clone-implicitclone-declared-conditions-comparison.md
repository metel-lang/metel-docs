---
title: "Inferred or Declared Conditions for ImplicitClone: A Comparison"
date: '2026-11-05'
status: report
relates: rfc-0206, rfc-0207, rfc-0211, rfc-0212, rfc-0213
---

# Inferred or Declared Conditions for ImplicitClone: A Comparison

> **Revised later on 2026-11-05.** This comparison was written for the `ImplicitClone` (hook) design. The language owner
> then chose a sealed implicit copy named `Copy` (RFC-0206); read `ImplicitClone` below as `Copy`. The question
> (inferred or declared conditions for a generic nominal type) and the hybrid end state are unchanged; the hook,
> the copy-site retention and the lowering rules mentioned in places no longer exist.

A comparison of two ways to decide when a generic nominal type is `ImplicitClone`, written after
the third adversarial review of the Clone and ImplicitClone design (metel-core#1809, review 3,
alternative E). It records the effects of each on the review findings, on the RFCs and on the v0.16.0
plan. It does not decide; the decision is the language owner's.

## 1. The question

`struct Wrapper<T> { value: T }` is implicitly copyable exactly when `T` is. Something has to say so,
and the generic-body analysis (ADR-0063) has to be able to use that answer without instantiating the
body.

- **Current design (inferred).** RFC-0206 rule 3: `T<A>: ImplicitClone` is the least solution of "every
  field is `ImplicitClone`, `T<A>: Clone`, not `Drop`", evaluated per instantiation. The header only
  *authorizes* (`: ImplicitClone`) or *generates* (`derives ImplicitClone`); the condition is
  inferred from the fields. The generic-body analysis is a sound approximation of it. A spike (#1810)
  estimated a production solver at 15 to 30 engineer-days, so v0.16.0 ships a fallback and the solver
  is deferred (#1813, #1814).
- **E (declared).** The header states the condition, as a list of conditions on the type's own
  parameters, and the compiler validates it as sufficient against the fields. `derives` computes the
  condition; the colon form requires it written.

> **Status note, 2026-11-05.** Decision 1 of review 3 was applied: the v0.16.0 limitation for an undecided
> abstract ownership is a diagnostic, not a move ("fallback" below refers to the earlier move-based wording).

## 2. The two designs side by side

```metel
// Current: the condition is inferred from the fields.
struct View<T> derives ImplicitClone { r: &T }                  // ImplicitClone for every T (because &T is)
struct Wrapper<T> derives ImplicitClone { value: T }             // only when T is
struct Cache: ImplicitClone { data: i64, hits: i64 }             // with a hand-written Clone

// E: the condition is declared in the header (spelling open, see section 6).
struct View<T>: ImplicitClone { r: &T }                          // unconditional; checked: &T is ImplicitClone for all T
struct Wrapper<T>: ImplicitClone when T: ImplicitClone
    derives Clone when T: Clone { value: T }                     // stated, checked sufficient
struct Wrapper2<T> derives ImplicitClone { value: T }            // the compiler computes `when T: ImplicitClone`
struct Pair<A, B> derives ImplicitClone { a: A, b: B }           // computes `when A: ImplicitClone, B: ImplicitClone`
struct Outer<T> derives ImplicitClone { p: Pair<Wrapper2<T>, i64> }
                                                                 // computed from the declared interfaces of Pair and Wrapper2:
                                                                 // `when T: ImplicitClone`
```

| Question | Current | E |
|---|---|---|
| Where is the condition? | Derived from the fields on demand | Written (or computed once by `derives`) in the header |
| What does the colon mean? | Authorizes; the condition is inferred | Authorizes and states the condition; the compiler checks it is sufficient |
| What does `derives` do? | Generates `Clone` | Generates `Clone` and computes the conditions |
| Proof of `N<args>: ImplicitClone` | Recursion over fields (needs a solver for nested and field-wise cases) | Recursion over the type expression using each nominal's declared conditions |
| Recursion through fields | A real problem (RFC-0206 "Recursion and termination") | Does not arise for markers: the condition is declared |
| What changes if a field changes? | The interface changes silently | Validation fails at the declaration (Swift's `Sendable` reasoning, SE-0302) |
| Generic body, unbounded `T` | Unknown, treated as a move (fallback) or a diagnostic (decision 1 of review 3) | A definite "not `ImplicitClone`" from the visible bounds |
| Witness of a proof | The impl or derivation selected by a solver | The declaration's own impl plus the witnesses of its arguments |

## 3. Why E is plausible: it fits what the implementation already has

`OwnershipRule` (`type_engine/ownership_rules.rs`) is a list of `(aspect, polarity)` conditions per
type parameter of an impl. `nominal_ownership_rule` builds it from impls such as
`extend<T: Copy> Wrapper<T>: Copy`, and `abstract_nominal_aspect` applies it to an abstract application.
That is exactly the shape E's header declares. What the machinery cannot do (the spike's findings) is
field-wise conditions, nested applications whose arguments are not bare parameters, and witnesses.
E removes the need for field-wise conditions on nominal types by making the header the source of the rule, and
reduces nested applications to substitution into declared conditions.

**Correction, 2026-11-05 (E spike, section 11).** This overstated how much of generic-body reuse the existing
machinery already gives: `OwnershipRule::applicability` accepts only bare parameters and returns unknown for an absent
bound, so nested applications need a recursive evaluator over type expressions, and an unbounded parameter needs an
explicit definite-no policy.

Grammar fact: `struct_decl` already accepts `where_clause?` between the generic parameters and `{`
(`grammar.pest`), where it constrains the type itself. A per-entry condition therefore needs another
spelling (`when` below, or a form inside the entry).

## 4. Effect on the review findings

| Finding | Current (with decisions 1 to 3) | E |
|---|---|---|
| Review 2 M1: exact predicate needs a proof system | Deferred; fallback | Reduced to resolution over declared interfaces |
| Review 2 M2: recursive eligibility | Rules written; algorithm deferred with the solver | Marker recursion disappears; derivation checked with the type's own interface assumed |
| Review 3 blocker 1: unknown-to-move is observable | Resolved by making unknown a diagnostic (decision 1) | Moot: classification is by declared interfaces and visible bounds |
| Review 3 blocker 2: copy-site retention in v0.16.0 | Needed | Needed; the witness is the declaration, a stable identity |
| Review 3 blocker 3: lowering semantics | Needed | Unchanged |
| Review 3 major 1: fallback baseline corpus | Needed | A corpus is still needed, but a fallback is not |
| Review 3 major 2: recursive derivation algorithm | Needed now | Small: assume the declared interface |
| Review 3 major 3: coherence | Syntactic closure plus conservative rejection | Ordinary impl-bound comparison plus the signed closure |
| Review 2 M3/M5/M6/M7 | Resolved | Unchanged |

## 5. Effect on the plan and the RFCs

| Item | If E is adopted |
|---|---|
| RFC-0206 rule 3, section 2 | "Exact least solution" becomes "declared condition, validated as sufficient"; the recursion and fallback text shrinks |
| RFC-0207 | The header gains a per-entry condition; `derives` computes it; the colon form requires it |
| RFC-0212 | `declared` gains a validation meaning: every field satisfies the marker under the declared condition |
| RFC-0211 / RFC-0209 / RFC-0210 | Marker eligibility for named types no longer needs row templates; they remain for residual projections. The row machinery leaves the critical path unless residual projections are kept |
| #1813 (solver, later minor) | Largely unnecessary: nominal resolution is part of validation |
| #1814 (fallback) | Replaced by "resolve against declared interfaces" |
| #1799 to #1803 | Unchanged in order; #1800 grows by the condition clause; #1803 by the validation |
| #1804 (ImplicitClone in std) | No longer blocked by the Row machinery stage |
| Copy-site retention (decision 2) | Still required, and simpler |

I have not estimated E's size. The spike measured the solver, not this. A short spike on two risky parts
would settle it: the header grammar with a per-entry condition, and the sufficiency validation built on
the existing `OwnershipRule`.

## 6. Costs and risks of E

1. **It reverses an accepted decision** (the exact inferred predicate, review 2 M1, RFC-0206 rule 3).
2. **The structural check becomes native.** Validating "every field satisfies the marker" is needed at
   the declaration. In v0.16.0 it is a native check that belongs to the meaning of `declared`, and row
   templates can replace it later, as derivation is native first. This is close to the `structural all`
   property that was removed in favour of row templates. It trades generality for schedule.
3. **Verbosity.** A hand-written generic wrapper needs an explicit condition. `derives` computes it, and
   a fix-it can propose the missing condition when validation fails.
4. **A limited condition language.** Conditions are on type parameters (positive aspect bounds; possibly
   negative ones such as `T: !Drop`). A type whose exact condition needs more cannot be generically
   `ImplicitClone` until the language grows.
5. **`derives` still infers, locally.** Computing the conditions from field types through declared
   interfaces is finite and deterministic, and independent of solver strength, but it makes derived
   conditions depend on the declared interfaces of the types used. Changing a nested type's condition
   changes its dependants' derived conditions. That is part of that type's contract.
6. **Grammar and spec work:** a per-entry condition in the header, with `grammar.pest`, the spec and the
   formatter.
7. **The residual rule** (RFC-0211 rule 6) still needs the field-wise check over present fields; it is
   covered by the same native rule for `declared` markers.

## 7. Open design questions if E is adopted

- **Spelling.** `when` is a new keyword; the existing struct-level `where` constrains the type. An entry
  form such as `: ImplicitClone [T: ImplicitClone]` is another option.
- **The condition language:** positive bounds only, or negative ones too (`T: !Drop`); conditions on
  associated types.
- **Computation rules for `derives`:** which positions of a type parameter generate a condition (a shared
  reference does not; a field of type `T` does; an application uses the declared interface of its
  head).
- **Validation algorithm:** sufficiency of the declared condition and of the declared `Clone` impls
  (the written `Clone` must cover the `ImplicitClone` condition).
- **Written conditional `Clone` impls and the declared `ImplicitClone` condition:** how the implication
  between them is checked and reported.
- **User markers:** whether `when` applies to `declared` user markers (an unchecked promise).
- **Enums and residuals:** enums are atomic for narrowing; the residual check is native.
- **Coherence:** the declared condition is an impl bound, so ordinary overlap rules apply together with
  the signed closure (RFC-0213 section 3).

## 8. Options

1. **Keep the current design** with the three decisions from review 3: unknown is a diagnostic,
   copy-site retention in v0.16.0, and the lowering rules drafted. The solver stays in a later minor.
2. **Adopt E.** Rewrite RFC-0206 rule 3 and sections 2 and 6, RFC-0207, RFC-0212, the scope of RFC-0209
   to RFC-0211, and the issue plan (#1800, #1803, #1804, #1813, #1814). Decisions 2 and 3 still apply.
3. **Adopt E in two steps.** Ship E for unconditional and parameter-conditional declarations in v0.16.0,
   and keep the door open for richer inferred conditions through `derives` later.

## 9. Recommendation

Adopt E (option 2, or option 3 if the condition language needs to start smaller), after a short spike on
the header grammar and the sufficiency validation. E removes the three things the reviews found hardest:
an observable inference boundary, a solver on the release's critical path, and a recursion algorithm for
markers. It also makes the public interface explicit in the declaration, which serves the first goal
directly. The price is a native structural check and a reversed decision, both of which are reversible
later.

## 10. Not verified

- The size of E; no spike has been run.
- That the existing `OwnershipRule` handles negative conditions in headers the way impl bounds do (it
  stores polarity, but the header path has not been exercised).
- Whether `derives` can compute conditions for every field type form used in std.

## 11. Spike result (2026-11-05, metel-core#1815)

A codex spike prototyped E for the existing `Copy` aspect on branch `spike/1815-declared-conditions`
(uncommitted; local worktree). I re-ran its fixtures: 7 passed, 3 failed, as it reported.

| Part | Result |
|---|---|
| Header grammar and AST | Worked. `struct W<T>: Copy when T: Copy .{ .. }`; `when` is contextual; the struct-level `where` stays separate; about 212 lines |
| Desugaring | Worked. The parser lowers each entry to an ordinary bodyless impl (`extend<T> W<T>: Copy where T: Copy;`) before name resolution and coherence |
| Sufficiency validation | Worked, reusing `check_copy_impl_eligibility`: nested fields accepted under the declared condition, an unconditional `Bad<T> .{ .value: T }` and a `String` field rejected. The missing-condition fix-it was not implemented |
| Generic bodies | **Partial.** Bounded `Wrapper<T>` and unconditional `View<T>` accepted. The unbounded case and both nested cases still give `I0011`; nothing flipped from `I0011` to definite |
| Condition computation (`derives`) | Not implemented; the spike stopped at the generic-body limit |
| Coherence | Generated impls go through the positional bound collection; disjointness still compares direct aspect names, so the signed closure (RFC-0213 section 3) is additional work; no header-versus-written overlap test |
| Recursion | Positive for the forms tried: a recursive type through a non-Copy `List` is rejected, an unconditional recursive type through shared references is accepted; no cycle detector was needed |

**Why the three cases fail.** The existing consumer needs two things E does not provide by itself: a recursive
evaluator over type expressions (nested applications), and an explicit definition-time policy that an absent bound
is a definite "not Copy" rather than unknown. Neither needs field recursion.

**Effort.** 12 to 25 engineer-days for production across `Copy`/`Clone`/`ImplicitClone` (Copy alone 6 to 12), against
15 to 30 for the solver. The spike does not establish a large saving. Unknowns: absent-bound semantics, signed
closure, `Clone` coverage implication, generated-impl provenance, `derives` coverage; callable witnesses are separate.

**The spike's recommendation:** adopt E in two steps, conditional on resolving the three failing cases first. Step
one: unconditional and own-parameter-conditional declarations, sufficiency validation, nested declared-interface
evaluation, an absent-bound policy, diagnostics, tooling and coherence coverage. Step two: `derives` computation and
richer conditions. If step one cannot fit, defer E.

**An observation for the next step.** The earlier solver spike (#1810) already contains a nested-application evaluator
that made `Pair<Wrapper<T>, i64>` and the shared-reference cases definite. Applying it to E's desugared rules, which
need no field-wise recursion, would test whether the three failing cases flip. That is a cheap combined spike and it
would answer the open condition of the recommendation.

## 12. Combined spike result (2026-11-05, metel-core#1815)

The solver spike's nested evaluator was ported onto E's desugared rules, with an absent-bound policy. I re-ran the
fixtures (13 passed) and the two correctness failures named below (both fail, as reported).

- **The three target cases became definite.** `spike1815_nested` accepted; `spike1815_unbounded` and
  `spike1815_nested_unbounded` T0019. The recursive evaluator is reusable.
- **The absent-bound policy leaked.** The same evaluator answers `Drop` queries, so "an absent `T: Copy` bound is a
  definite no" made `Guard<T>: Drop where T: Copy` inapplicable for an unbounded `T`, and the checker then permits
  extracting a field from a possibly destructible value. Two existing tests fail for that reason
  (`abstract_ownership_does_not_assume_conditional_destructor_absent` and `..._preserves_aliased_ownership_aspects`),
  alongside the six `abstract_ownership_*` tests that expect unresolved ownership to leave a body unchecked.
  Production needs copy-site classification separated from obligation entailment (RFC-0213 section 3: absence is not
  negation).
- **Computed defaults were not built.** Computation needs resolved names and cross-module interfaces, so it cannot run
  at parse time. The earliest workable point is after path normalization and before coherence, with its own ordering
  and cycle policy over the module graph. The spike stopped there.
- **Computed interfaces can change silently** (public bounds strengthening and propagating to dependants). The
  "validation fails when a field changes" benefit applies to explicit conditions only. This weakens the case for
  computed-by-default on public types.
- **Marker recursion does not disappear:** it moves from consumption to the computation of the interfaces.
- **Effort.** E computed by default: 18 to 35 engineer-days (low confidence), against E-explicit 12 to 25 and the solver
  15 to 30. No schedule saving over the solver is shown. With observable clone-call semantics a provisional end-to-end
  planning range is 26 to 50 days.
- **The spike's recommendation:** adopt in steps and do not schedule computed defaults for v0.16.0 on this evidence.
  First explicit parameter conditions, preserved definition-time decisions, and copy classification separated from
  entailment; then prototype the resolved-graph computation phase, imports, ordering and inductive cycles.

**Effect on the comparison.** The first summary table put E ahead of the solver on effort. The evidence now shows E-explicit
roughly level with the solver, and E computed by default costlier, so the earlier recommendation (section 9) should be
read as: E is attractive for its explicit public interface and its clearer diagnostics, not for a schedule saving.

## 13. The hybrid: solve once, store, consume (intended end state, 2026-11-05)

Considered with development cost set aside. Not decided; the language owner asked for it to be recorded as the
intended end state.

**The idea.** The general solver is the *producer* of each type's interface, and E's stored interface is what
everything else reads.

1. **At the declaration (once per type)**, the solver computes the weakest condition on the type's parameters under
   which the exact predicate holds (every field `ImplicitClone`, `Clone` holds, not `Drop`). Where the exact
   predicate can be written as parameter conditions, the stored interface equals it. Where it cannot, the stored
   interface is a sound under-approximation and the author states a `when` that the compiler checks as sufficient.
2. **The stored interface is an ordinary impl set**: heads with bounds, the shape `OwnershipRule` already models (a list
   of candidates per `(type, aspect)` with polarity). Heads may be instantiation patterns, so a written `Clone` that
   covers only `T = i64` is stored as the head `Narrow<i64>`, which a pure parameter-bound language cannot express
   (RFC-0206 rule 3 keeps this case).
3. **At every use, including generic bodies**, only stored interfaces are consulted: a small evaluator substitutes
   arguments into declared conditions. The search never runs at use sites.
4. **The stated condition is the interface** (decided 2026-11-05, after the fourth review). If written, `when` is checked
   sufficient against the computed condition (stronger is allowed) and is what other code sees; a representation
   change that would weaken the computed condition then cannot change the published interface;
   if omitted, the computed interface is used, **except on a `pub` generic type, where leaving the condition unstated is
   an error** (decided 2026-11-05; the fix-it shows the computed condition). A non-`pub` type may rely on the computed
   condition.

```metel
struct Wrapper<T> derives ImplicitClone { value: T }                   // stored: `where T: ImplicitClone`
struct View<T> derives ImplicitClone { r: &T }                         // stored: no condition
struct Outer<T> derives ImplicitClone { p: Pair<Wrapper<T>, i64> }     // solved once from Pair's and Wrapper's stored interfaces
struct Cursor<I: Iterator> derives ImplicitClone { cur: I::Item }      // exact: `I::Item: ImplicitClone`; stored if the condition
                                                                       // language has projections, else "write `when ..` or drop the claim"
```

**Invariant (one sentence for RFC-0206):** a type's stored interface implies the exact predicate, and equals it whenever
the condition language can express it and none is stated; a stated condition is the interface. The stored condition
language is finite and acyclic so that use-site evaluation terminates by construction. The generic-body analysis remains a sound approximation of the exact predicate and
becomes complete for markers on nominal types.

| Property | Solver | E (computed) | Hybrid |
|---|---|---|---|
| Exact predicate (rule 3 unchanged) | yes | no (parameter bounds only) | yes where expressible; sound under-approximation otherwise |
| Generality for other aspects (`Eq`, `Hash`, coherence) | yes | no | yes: the same producer solves their conditions |
| Nested generic bodies accepted | yes (later) | yes | yes |
| Stable witnesses (the declaration's identity) | no | yes | yes |
| Termination at use sites | needs guards | by construction | by construction |
| Visible interface, clear diagnostics | partly | yes | yes |
| Cycle and coinduction policy | at every query | at declaration | at declaration only |

**What it still costs.**
- A declaration-graph phase after name resolution and before coherence (ordering, cross-module interfaces, a cycle
  policy). This is the phase the combined spike stopped at.
- Silent change on public types is ruled out by making an unstated condition on a `pub` generic type an error (decided
  2026-11-05): a field change then either keeps the stated condition sufficient or fails validation. The cost is that
  public generic types always state their condition; non-generic and unconditional types state nothing, and non-`pub`
  types may use the computed default.
- Two notions in the spec (the exact predicate and the stored interface), tied by the invariant above.

**Reversal check.** Nothing already accepted is reversed: the exact predicate stays the meaning and the analysis stays a
sound approximation.

**Path to it.** This is where option (c) of section 8 converges: v0.16.0 ships the current design with the three
decisions from review 3 (unknown is a diagnostic, copy-site retention, lowering rules); a later minor introduces stored
interfaces with explicit conditions (E-explicit, with the absent-bound leak fixed by separating copy classification from
entailment); the solver then replaces the syntactic computation as the producer of the interfaces. Choosing (c) now does
not close the door on the hybrid.

## 14. Decision (2026-11-05)

The language owner chose **option (c) with the hybrid of section 13 as the explicit end goal**: v0.16.0 ships the
current design with the three decisions of review 3 (undecided abstract ownership is a diagnostic, copy-site retention,
the lowering rules), and the later minors converge on the hybrid in steps (stored interfaces with explicit conditions;
the declaration-graph computation phase with the solver as producer; an error for an unstated condition on a `pub`
generic type). The
route is recorded in RFC-0206 section 6, "End state", and tracked by the epic metel-core#1821 (#1818 to #1820 and
#1813).

