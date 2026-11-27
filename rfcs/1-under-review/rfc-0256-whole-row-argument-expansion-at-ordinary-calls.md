---
id: rfc-0256
title: "Whole-Row Argument Expansion at Ordinary Calls"
date: '2026-11-27'
status: under-review
updated: '2026-11-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/2207'
---

> **Split from [RFC-0255](rfc-0255-row-sections-shared-extraction-and-contextual-field-assembly.md) (language owner, 2026-11-27).** Ordinary call expansion
> is a dependent proposal: RFC-0255 owns contextual section extraction and record/
> constructor consumers; this RFC owns ordinary argument binding, positional
> density evidence and generic forwarding. RFC-0255 does not wait for this feature.

> **Status — under review (2026-11-27).** Owner-approved split from RFC-0255 for ordinary call expansion and generic forwarding review

## Summary

Allow a single row section to supply an ordinary call's entire argument list:

```metel
let args := (1, "hello");
consume(..args);
configure(..{ .host = "localhost", .port = 8080 });
```

Dense numeric rows supply positional arguments; named rows supply keyword
arguments to direct calls. The section is the sole written argument, with the
receiver of a method call outside the supplied row. A section is contextual, not
a first-class argument-pack value; ordinary records store its fields (RFC-0255).

The owner authorized this split and review, not acceptance of its individual
rules. No milestone or implementation work is assigned by this proposal.

## Motivation

RFC-0247 collects positional arguments into an ordinary tuple, but leaves the dual
call-site expansion operation to another RFC. Expansion makes an existing record
usable as arguments without manually selecting every field. It also exposes the
real generic questions: a row parameter alone proves neither positional density
nor that a target accepts the row.

Those questions should not block RFC-0255's shared extraction machinery. This RFC
is the explicit owner of that dependent consumer. Constructor whole-row calls
remain RFC-0100's distinct exact-label contract; no constructor behavior is
changed by ordinary positional expansion.

## 1. Syntax and targets

A function, associated-function or method call may contain one section argument,
using RFC-0255's `..expr` or `..{ entries }` spelling:

```metel
consume(..make_args());
configure(..{ .host = "localhost", .port = 8080 });
receiver.send(..args);
```

The section must be the sole written argument. Mixed forms and multiple sections
are rejected initially:

```metel
consume(prefix, ..args); // not included: concatenation
consume(..left, ..right); // not included: merging
configure(..args, ..);    // not included: expansion plus defaults
```

Ordinary argument passing is unchanged: `consume(args)` passes one record value.
No implicit expansion depends on a parameter's expected type. Standalone section
expressions remain rejected under RFC-0255.

The target is resolved as a type or a value by existing name resolution before
choosing its consumer policy. A type target uses RFC-0100 construction binding;
an ordinary callable uses this RFC. Argument shape cannot select between the two.
This introduces no binding separator: field associations use `=`, and local
bindings use `:=`, consistently with RFC-0136.

## 2. Numeric and named binding

Classify the section's row before overload-specific binding:

| Row | Expansion |
|---|---|
| Exactly numeric labels `.0` through `.n-1` | n positional arguments in numeric order |
| Identifier labels only | Keyword arguments with those exact names |
| Empty row | Zero arguments |
| Sparse numeric row | Error; no implicit renumbering |
| Mixed identifier/numeric row | Error in this proposal |
| Symbolic row lacking sufficient classification evidence | Generic checking obligation, not permission to guess |

Positional expansion follows existing positional parameter order. Named expansion
is available only where explicit keywords are already legal under RFC-0223.
Unknown keywords, missing required arguments and incompatible types remain errors.
Expansion does not silently discard fields or bind a named field positionally.

Calls through function values accept numeric sections only: function types do not
expose keyword parameter names. An empty section works through either direct or
indirect calls, subject to arity. Method receivers are bound by existing method
rules, not by an entry in the section.

Every supplied field binds exactly once. A target's rest parameter collects
remaining positionals only under RFC-0247; it does not absorb unknown keywords.

## 3. Ownership and evaluation

Use RFC-0255's extraction rules without adding an ownership conversion. All
supplied fields are carried: ordinary call expansion has no replacement mask.
Owned records transfer under ordinary move/Copy rules. Borrowed extraction must
satisfy Copy for every supplied field, since none is replaced. No implicit Clone
or reference generation is introduced.

A section operand is evaluated exactly once in the argument position. A section
literal evaluates its initializers in written order before the callee executes.
Binding by label or numeric position never re-evaluates or reorders initializers.
For an already-built record, canonical label order determines binding, not a new
order of source-expression effects. Callee and receiver evaluation retain the
existing ordinary-call order.

Nominal and temporary sources are eligible only to the extent RFC-0255 ultimately
permits them. This RFC does not independently authorize private-field extraction,
nominal dismantling, Drop suppression or a borrowed move.

## 4. Generic evidence and checking

A row binder `<..R>` binds any ordinary field row. It does not imply that R is a
dense numeric row, a named-only row, or accepted by a particular function.

Generic expansion requires two independent proofs at definition time:

1. **Shape:** the row has a supported expansion mode, including density for a
   positional expansion.
2. **Call compatibility:** ordinary parameter binding and bounds succeed for that
   expanded row and the chosen callable.

A concrete tuple supplies density evidence. A rest parameter under RFC-0247 must
supply density evidence for its collected row if generic forwarding is supported.
The representation and propagation of that fact across row aliases, equations,
return values and ordinary generic parameters remain an acceptance question.
No new `Dense` aspect, row kind or syntax is adopted implicitly by this statement.

```metel
// Insufficient on its own: R could be sparse, named or mixed.
fun forward<..R>(args: .{ R }) {
    target(..args);
}
```

That body is not accepted merely because current callers happen to use tuples.
A rest declaration can address shape but does not prove target compatibility:

```metel
// Schematic: target and the required compatibility proof must also be declared.
fun forward_rest<..R>(..args: .{ R }) {
    target(..args);
}
```

RFC-0232/0161's callable argument row is the natural source of callable
compatibility evidence for a generic target. Exact surface bounds and the
relationship between that row and R require joint review; these fragments are
not claimed to be complete legal generic programs.

Generic body checking must not defer overload selection, keyword-name validity or
row classification errors until monomorphization. Unknown is not empty; the
symbolic extraction reconciliation belongs to RFC-0254/0208 via RFC-0255.

The primary direction includes generic forwarding once these facts are expressible.
An explicitly concrete-only first stage is an alternative, not an implicit fallback.

## 5. Variadics, defaults and overloads

For RFC-0247, expand the numeric row and apply its normal fixed/rest split. The
callee's collected rest is numbered from zero locally. This does not renumber the
source record or define general tuple concatenation.

RFC-0248 defaults require its explicit bare `..` marker. This RFC's sole-section
form cannot combine with that marker, so an omitted defaulted parameter is still
an error. An empty section supplies no arguments and never means “use defaults.”

Overload resolution uses the same expanded shape for every candidate, applying
ordinary specificity rules. A candidate cannot reinterpret numeric labels as
parameter names, silently remove extras, or fall back to treating the entire
section as one ordinary record argument. Expansion supplies no new tie-breaker.
Generic overloads require the same definition-site evidence as other generic calls.

## 6. Worked examples and counterexamples

Examples use proposed syntax and are design cases, not interpreter test results.

**Concrete positional expansion.**

```metel
fun add(a: i32, b: i32) -> i32 { a + b }
fun example() -> i32 {
    let pair: (i32, i32) := (10, 20);
    add(..pair) // binds a=10, b=20; result 30
}
```

**Named binding is independent of field layout.**

```metel
fun subtract(a: i32, b: i32) -> i32 { a - b }
fun example() -> i32 {
    subtract(..{ .b = 3, .a = 10 }) // result 7, not -7
}
```

**Sparse rows remain sparse.**

```metel
let sparse := .{ .0 = 10, .2 = 20 };
add(..sparse); // error: missing positional label .1
```

A record-rest pattern that removes `.0` from a tuple leaves the original labels;
it cannot be forwarded as a new dense pack without explicit renumbering owned by
RFC-0125. Sharing the row kind is not a proof that every numeric row is a tuple.

**Borrowed non-Copy values cannot be passed by value.**

```metel
// r refers to a tuple containing a non-Copy Token.
consume(..r); // rejected if expansion needs to copy that Token
```

Passing references explicitly in an ordinary record is a separate, valid operation
when the callee expects references. Expansion does not manufacture that record.

**Constructor asymmetry is deliberate and visible.**

```metel
let coordinates := (10, 20);
add(..coordinates);   // ordinary call: numeric positional expansion
Point(..coordinates); // constructor: error if its row is named .x and .y
Point(..{ .x = 10, .y = 20 }); // constructor's exact-label contract
```

**Function values have no keyword names.**

A value of function type accepting two i32 arguments can consume the dense pair
above. A named section `.a/.b` is rejected even if the underlying function's
original declaration used those names; erasure must not recover hidden names.

**Single evaluation and effects.**

For `subtract(..{ .b = next_b(), .a = next_a() })`, evaluate `next_b` once, then
`next_a` once, then invoke subtract with the fields bound by name. For
`subtract(..make_pair())`, invoke `make_pair` once, not once per field or overload.

## 7. Dependencies and scope

| Owner | Relationship |
|---|---|
| RFC-0255 | Required shared section extraction, visibility and ownership rules; does not depend on this RFC |
| RFC-0223 | Existing keyword binding and indirect-call restrictions |
| RFC-0247 | Rest collection and its proposed density invariant |
| RFC-0208 / RFC-0254 | Row facts, equations and symbolic type extraction |
| RFC-0232 / RFC-0161 | Callable argument-row evidence for generic function values |
| RFC-0125 | General concatenation, positional recursion and renumbering remain separate |
| RFC-0248 | Explicit defaults; no combined section/default syntax here |
| RFC-0100 / RFC-0114 | Constructor binding and authority remain distinct and unchanged |

Out of scope: multiple sections, mixed explicit/expanded arguments, automatic
renumbering, keyword rest parameters, homogeneous runtime variadics, first-class
section objects and generic code checked only after concrete instantiation.

## 8. Alternatives and costs

- Pass a record as one parameter: already sufficient for many APIs and introduces
  no call expansion. It does not adapt an existing multi-parameter callable.
- Permit only concrete expansion initially: smaller checking surface, but does
  not complete generic rest forwarding. Decide explicitly if adopted.
- Permit mixed calls immediately: useful for prefixes, but requires positional
  concatenation and duplicate-binding rules. Deferred to keep the first form exact.
- Infer density from observed instantiations: rejected because it makes generic
  correctness dependent on callers rather than declared facts.
- Use one rule for constructors and ordinary functions: would reopen RFC-0100's
  exact named-row contract. This RFC does not do so.

Costs are new contextual argument syntax, expanded diagnostics and generic proof
obligations. Expansion is syntactic convenience for concrete calls; generic
forwarding is the stronger motivation and the main unresolved design work.

## 9. Acceptance questions

1. How is dense numeric shape represented and propagated in generic code? Does a
   rest binder supply an intrinsic fact, and how can an ordinary generic API state
   or preserve it without a new row kind? Joint review with RFC-0247/0208/0125.
2. What exact callable-row constraint proves generic target compatibility? Settle
   against RFC-0232/0161; do not treat the schematic forwarding examples as a proof.
3. Include generic forwarding in the first accepted scope, or explicitly stage a
   concrete-only form? The primary proposal aims for the generic form once its
   evidence is specified; no stage is selected merely by implementation difficulty.

The sole-section restriction, numeric/named classification, explicit defaults and
constructor separation are primary recommendations to attack during adversarial
review. If a counterexample changes one, update its governing rule, not a parallel
list of historical resolutions.

## 10. Validation and integration

Before acceptance, test the proposed rules against sparse and mixed rows, empty
rows, indirect keyword calls, generic rest forwarding, generic target compatibility,
overload ambiguity, private sources, non-Copy borrowed fields and side effects.
After resolutions, reconcile RFC-0247's call-site-spread question and the relevant
callable/row proposals. RFC-0255's own acceptance does not wait on these questions.

Integration targets the call and grammar specifications with cross-references to
section extraction and rest-parameter binding. Future fixtures must cover both
concrete and generic successful/rejected cases, and verify evaluate-once behavior.
No implementation is authorized before integration.

## Decision

**Outcome:** *(pending)*
