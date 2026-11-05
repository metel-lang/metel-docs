---
title: "Inferred or Declared Conditions for ImplicitClone: A Comparison"
date: '2026-11-05'
status: report
relates: rfc-0206, rfc-0207, rfc-0211, rfc-0212, rfc-0213
---

# Inferred or Declared Conditions for ImplicitClone: A Comparison

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
