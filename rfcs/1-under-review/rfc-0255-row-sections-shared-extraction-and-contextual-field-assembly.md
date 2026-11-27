---
id: rfc-0255
title: "Row Sections: Shared Extraction and Contextual Field Assembly"
date: '2026-11-27'
status: under-review
updated: '2026-11-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/2206'
---

> **Status — under review (2026-11-27).** Acceptance review: reconcile generic eligibility, nominal ownership, and symbolic rows

## Summary

Introduce a **contextual row section**: a structural field source consumed by record
assembly or whole-row argument binding. `..value` extracts a section; `..{ ... }`
introduces one literally. An ordinary anonymous record is its storable value form.
There is no first-class runtime `RowSection<R>` type.

```metel
let fields := .{ ..point };
let next := Point(..{ ..fields, .x = 10 });
```

This is the primary proposal from the 2026-11-27 design discussion, recorded at the
language owner's request. Its choices are proposals, not accepted resolutions.
The RFC has no milestone assignment or implementation authorization.

Extraction is shared; consumer policies remain explicit. Record assembly can
replace fields, and constructors require their exact parameter row. Ordinary call
expansion belongs to RFC-0256. Borrowed extraction follows
ordinary field auto-dereference. The proposed symbolic rule for abstract rows
still needs reconciliation with RFC-0254 before acceptance.

## Motivation and existing behavior

Metel already has type-row extraction, record spread/update, owned remainder
patterns, numeric-label tuples and structural bounds. RFC-0100 integrates whole-row
construction into the specification (implementation remains pending), RFC-0208 separates row binders from types, and RFC-0247 proposes
collecting positional arguments into tuples. Their common machinery should be
stated once without making their binding and ownership policies identical.

The strongest argument against first-class sections is existing borrowed update:
only carried fields must be Copy. A replaced non-Copy field is not copied.

```metel
// Proposed spelling; token is non-Copy, id is Copy.
let source := .{ .id = 1, .token = make_token() };
let reference := &source;
let result := .{ ..reference, .token = make_token() };
```

A materialized standalone section would need to copy the old token. A deferred
section object would instead need stored loans, consumption rules and a lifetime.
The contextual model preserves existing behavior without either cost.

The investigation checked the current open-row specification and frontend
`pipeline/type_checking/inference/expressions.rs` record-literal inference. Both
specify same-type replacement and Copy checks on carried fields only. The current
parser admits spread as a record initializer, not an unrestricted unary operator.
These are evidence for the design, not claims that this RFC is implemented.

## 1. Row, section and record

| Concept | Meaning | Spelling |
|---|---|---|
| Row | Labels and field types | `R`, `..T`, `..{ .x: i32 }` |
| Section | Fields supplied to a surrounding operation | `..value`, `..{ .x = 1 }` |
| Anonymous record | An ordinary aggregate value | `.{ .x = 1 }`, type `.{ R }` |

A section has a row and source-access information: source expression/place,
ownership mode and visibility. It carries no nominal brand, constructor privilege
or aspect implementation. The compiler may represent it during checking and
elaboration, without a runtime wrapper, allocation or dynamic reflection. Ordinary
record materialization still has its usual representation and storage costs.

## 2. Syntax and materialization

Value sections are admitted in record assembly, whole-row constructor calls and RFC-0100's
privileged representation construction. A section is `..expr` or a dedicated
literal `..{ entries }`. Arbitrary expression operands are allowed:

```metel
let stored := .{ ..make_fields() };
Point(..stored);
Point(..make_fields());
Point(..{ .x = 1, .y = 2 });
```

Parsing is contextual rather than an unrestricted unary-expression rule. Postfix
operations belong to the operand: `..make_fields()` extracts the call result.
Parentheses delimit larger operands, `..(expression)`. `..{` remains the contiguous
literal opener, not `..` followed by `.{`.

Reject standalone sections and suggest explicit record materialization:

```metel
let fields := ..point; // error: use .{ ..point }
return ..point;       // error: section requires a consumer
```

`Wrapper(fields)` passes one ordinary value; `Wrapper(..fields)` supplies the
constructor parameter row. There is no implicit spreading based on argument type.

In type position, RFC-0208's `..{ .x: i32 }` remains a row literal, `..T` extracts a
type's row, and bare `R` uses a bound row. Applying extraction to a row parameter
is a kind error suggesting `R`. No new generic kind is introduced. Bindings use
`:=` and literal field associations use `=`, following RFC-0136.

## 3. Symbolic type extraction

Concrete extraction follows RFC-0254's public, present-field classification.
Abstract extraction is a symbolic projection, not proof of an empty row:

| Available fact | Meaning of `..T` |
|---|---|
| Unconstrained `T` | Unknown row projection |
| `T: .{ .id: i32, .. }` | `.id: i32` plus a symbolic remainder |
| `T: .{ .id: i32 }` | Exactly that public row |
| Concrete primitive or enclosing enum | Empty ordinary field row |

Unknown-row field-wise constraints require evidence. They do not hold vacuously
because no fields are known. Provably empty rows still satisfy universal
field-wise constraints vacuously. Neither case grants a whole-type aspect.

Specializing `T` to `U` specializes its projection to `..U`. Extraction must not
infer a nominal type backwards from a row, change overload selection after generic
body checking, or authorize accessing an unconstrained field by name. An unknown
remainder may be carried opaquely; row equations determine provable decomposition.
This introduces no general inverse solver for extraction.

This proposes resolving RFC-0254's final abstract-row reconciliation issue. Its
earlier empty-abstract-row wording must be amended before conflicting rules are
accepted. Equation solving and separate compilation need joint RFC-0208 review.

## 4. Value-source eligibility and visibility

Anonymous records and tuples supply their present fields. Structs and residuals
supply present public fields. A statically known variant supplies public payload
fields, subject to ownership restrictions. Ordinary extraction is public-only,
even inside the declaring module.

Shared and exclusive references expose the referent’s public row through every
reference layer, following field access and the same structural row as RFC-0254.

```metel
let reference := &fields;
let nested := &reference;
let copied := .{ ..nested };
```

Each carried field must be Copy. Explicit dereference is also valid when the
operand denotes a borrowed place. The source category after auto-dereference
determines eligibility. Under this draft’s current rule, primitives, enclosing
enums, arrays, functions and other non-field-bearing values are ineligible,
including through a reference. Empty records and zero-field structs are eligible
with their ordinary ownership obligations.

Generic value extraction requires an anonymous-record type or an explicit
structural bound supporting the requested field operation, plus the necessary
ownership facts. A type-level `..T` projection alone is not ownership evidence.
An abstract empty public row must never justify disposing of unknown private state.

Aliases, remainders, reflection and inferred interfaces cannot expose private
fields through extraction. Opaque types expose only their public structural
contract. Privileged full-representation extraction remains deferred and separate.

## 5. Ownership and evaluation

The consumer statically determines carried, replaced and added labels before
ownership checking. This is not runtime filtering or repeated source evaluation.

1. An owned anonymous-record source transfers carried fields under ordinary
   move/Copy rules. Replaced old fields are discarded only when the existing
   Discard/destruction rules permit it. A move consumes the source.
2. A borrowed place supplies carried fields only when they are provably Copy.
   Replaced fields are not read, copied or dropped in the source. Exclusive access
   alone does not permit moving out without replacement.
3. Extraction from a nominal place has the authority of the selected ordinary
   field accesses. Moves leave the appropriate branded residual. Fields outside
   the public row remain with the source, including all private fields.
4. A temporary is evaluated once. Untransferred state retains its cleanup and
   linear obligations; unsupported cleanup or partial moves cause rejection.
5. Extraction never implicitly clones, generates references, suppresses Drop,
   or grants Copy/Discard to the nominal source.

Initializers evaluate in source order. The source expression and selected
transfers occur at the section's written position. Result layout follows the row,
not initializer order. Replaced owned-field destruction follows existing record
update rules; this RFC introduces no destructor ordering change. Earlier moves
must be visible to checks on later entries.

An empty section still evaluates its operand. Extracting no fields from an
existing nominal place does not consume that place. Empty extraction from a
temporary never erases the temporary's ownership obligations.

No new Drop or linear nominal dismantling permission is introduced. Unsupported
cases are rejected; RFC-0071 and the applicable ownership proposals own extensions.
Variant payload moves requiring a variant residual remain deferred to RFC-0150.
Borrowed Copy extraction needs no variant residual and can compose with RFC-0210's
known-variant borrowing rules.

## 6. Record assembly and updates

Retain at most one spread section per record literal. A section literal uses the
same assembly rules internally:

```metel
let next := .{ ..source, .existing = replacement, .extra = value };
Point(..{ ..fields, .x = 5 });
```

An explicit label is an addition if provably absent, a same-type replacement if
provably present, and an error otherwise. Duplicate explicit labels are errors.
There is no last-write-wins or implicit type-changing update. Field selection is
independent of entry order; evaluation remains in source order.

Selection is local to an assembly operation. A nested literal, ordinary record
expression or function call establishes its own field obligations; an outer update
cannot remove an inner Copy or Discard obligation. Optimizations must preserve
this boundary. In particular, section extraction is not a lazy expression language
that permits deleting an initializer because a later consumer replaces its label.

```metel
fun attach_id<..R>(fields: .{ R }, id: i32) -> .{ .id: i32, R }
where R: !{ .id }
{
    .{ ..fields, .id = id }
}
```

The candidate `R # S` relation could prove disjoint labels if its owner adopts it;
it is not an established operator introduced here. Label disjointness does not
prove source-place non-aliasing or disjoint opaque borrow footprints. Multiple
value sections and their merge policy remain out of scope.

## 7. Constructor consumers

Preserve RFC-0100's exact whole-row contract: a section is the sole argument and
supplies every constructor parameter by label, without extras, under ordinary
checking, inference and visibility rules.

```metel
Point(..fields);
Point(..make_fields());         // new arbitrary-expression operand
Point(..fields, x = 5);         // error: mixed whole-row call
Point(..{ ..fields, .x = 5 });  // update first, then bind
```

The row is the constructor's interface, not necessarily its stored representation.
A constructor accepting `id` and `password` may store `id` and a private hash.
Sections cannot supply inaccessible representation fields or bypass validation.
Section expansion does not change a constructor's result type. Variant-preserving
results remain RFC-0210's proposal, not a guarantee of integrated RFC-0100 or a
prerequisite for ordinary section construction.

`Self { ..fields }` retains RFC-0100's constructor-body privilege and complete
representation-row check. The nominal brace form, including its restriction in
unparenthesized condition positions, follows RFC-0100 section 3. Dotted braces
remain anonymous-record/projection syntax, not privileged nominal construction. Sections transport values, never minting authority.
A tuple row does not become a constructor's named row by matching arity.
Fallibility and unchecked boundaries remain with RFC-0100/0114. Per-variant
privileged minting is owned by RFC-0114 section 9; this RFC introduces no independent
per-variant privilege.

## 8. Ordinary calls are a separate consumer

> **Split to [RFC-0256](rfc-0256-whole-row-argument-expansion-at-ordinary-calls.md) (language owner, 2026-11-27).** Ordinary argument expansion,
> dense numeric row evidence and generic callable compatibility are owned by
> RFC-0256. It depends on this RFC's extraction contract; this RFC's acceptance
> does not wait for that call feature.

RFC-0255 specifies record assembly and RFC-0100's constructor consumer. It does not
add `f(..args)` to ordinary functions or methods. RFC-0256 contains the sole-section
call proposal and its examples. The extraction contract can support that consumer
without deciding positional concatenation, defaults or generic call evidence here.

## 9. Patterns and binders

```metel
let .{ .id, ..rest } := fields;
```

This decomposes a row and binds an ordinary anonymous remainder record. It does
not evaluate extraction on a variable that has yet to be bound. Row facts must
determine the remainder, ordinary pattern ownership rules apply, and numeric labels
are preserved. Bare `..` binds no value and exempts no discarded ownership state.

This RFC does not broaden remainder patterns to borrowed or private nominal
state. Reference destructuring and nominal pattern extensions retain their owners,
including RFC-0109 and RFC-0150.

Likewise `<..R>` and `..rest: .{ R }` are declarations, not unary expressions.
Bare `..` in bounds permits an unknown tail; in calls it requests defaults under
RFC-0248. These uses share row vocabulary without being fictitious value operators.

## 10. Composition and deferred work

| RFC | Contract and required reconciliation |
|---|---|
| RFC-0208 | Row binders, literals, equations and bare uses; no new kind |
| RFC-0254 | Concrete extraction; reconcile symbolic abstract rows with section 3 |
| RFC-0243 | Public/present fields; no automatic nominal row implementation |
| RFC-0100 / RFC-0114 | Construction authority and parameter contracts; allow expression operands |
| RFC-0256 / RFC-0247 / RFC-0125 | Ordinary expansion moved to RFC-0256; rest collection and concatenation retain their owners |
| RFC-0248 | Defaults remain explicit, never implied by incomplete sections |
| RFC-0210 | Known-variant payload rows; variant inventories are separate |
| RFC-0150 / RFC-0071 | Variant residuals, nested projections and ownership/Drop extensions |
| RFC-0253 | Generic residual aliases keep their brand; extraction explicitly forgets it |
| RFC-0252 | Opaque contracts and origins; no representation or footprint proof inferred |
| RFC-0174 / RFC-0216 | Symbolic field iteration and computed-label assembly remain separate |
| RFC-0250 / derivation proposals | Field bundles grant no nominal aspect or derivation privilege |

A materialized record may use structural implementations applicable to its own
type. They do not transfer to its nominal source. Derived Clone versus field-wise
Clone, privileged full-field extraction and enum-wide derivation remain deferred.

`&.{ R }`, a record containing references, and a borrow of a branded projection
remain different types. No `&.` operator or structural reference layout is added.

## 11. Alternatives and costs

**First-class `RowSection<R>`.** Storing field values duplicates anonymous records.
Storing deferred transfers requires loan lifetimes, capture and consumption rules,
and a choice of evaluation time. Borrowed replacement makes these differences
observable. Revisit only for a concrete need to store deferred transfers.

**Standalone extraction returning a record.** Possible sugar for `.{ ..value }`,
but suggests independent evaluation where selective borrowed update depends on the
consumer. The primary proposal requires explicit record materialization.

**One universal merge rule.** Would change record replacement, constructor
exactness or positional binding. Sharing extraction does not justify doing so.

Costs include contextual parsing, source-place-aware elaboration and symbolic generic
projections. Ordinary-call expansion costs belong to RFC-0256. This is more than a terminology change. It retains
distinct declaration, pattern and default-marker uses of `..` deliberately.

## 12. Compatibility and integration

1. Preserve anonymous-record replacement typing, carried-field Copy checks and
   owned Discard checks.
2. Preserve existing borrowed spread spelling and extend extraction through
   nested references in line with ordinary field access.
3. Reconcile RFC-0254's abstract-row classification and RFC-0208's equations before
   implementing generic value extraction.
4. Extend RFC-0100's binding-only operands to expressions, retaining constructor
   exactness. Ordinary-call expansion is a dependent RFC-0256 feature.
5. Reject deferred ownership cases rather than supplying a permissive fallback.

Specification targets are records/open rows, calls, construction, patterns,
grammar and ownership. Integration must include the syntax migration across code
and prose required by PROCESS.md, with executable examples where the integrated
features are available.

No normative specification or sibling RFC resolution is changed by this draft.
Acceptance requires reconciliation and the project's adversarial review; integration
and implementation require their normal lifecycle gates.

## 13. Adversarial cases and validation obligations

These are design checks and future fixtures, not tests of an implementation of
this proposal.

| Case | Required outcome |
|---|---|
| Borrowed non-Copy token is replaced; carried fields are Copy | Accepted; original token untouched |
| Same borrowed source materialized without replacement | Rejected if token cannot be copied |
| Owned replacement discards a linear field | Rejected without required discard permission |
| Struct contains private linear state | No exposure or erased obligation |
| Unknown T instantiated with public fields | No empty-row equality or vacuous proof in generic body |
| Constructor accepts password but stores private hash | Bind password; no representation bypass |
| Source expression has observable effects | Evaluate once at its written position |
| Earlier entry moves a field the section needs | Ordinary move error |
| Variant extraction needs an unsupported residual | Rejected; RFC-0150 owns extension |
| Extracted record has an aspect absent from source | Only the record can use that implementation |
| Disjoint labels refer to overlapping places | No authorization for conflicting loans |
| Empty section from nominal temporary with obligations | Obligations remain |

### Worked counterexamples

The following fragments attack the proposed rules, not the current interpreter.
They expose the acceptance decisions in section 14. Types and helper functions
such as `Token` and `make_token` are schematic; no proposed-syntax execution is
claimed.

**A. Generic eligibility cannot be proved by an empty public-row bound.**

```metel
fun snapshot<T: .{}>(x: &T) -> .{} {
    .{ ..(*x) }
}
// T = i32: section 4 rejects primitive value sources.
// T = a zero-public-field struct: section 4 admits the source category.
```

RFC-0254 lets both types satisfy the exact-empty public-row bound. The generic
body cannot use that bound as proof that T belongs to an eligible nominal source
category. This is a contradiction between the proposed generic eligibility rule
and its concrete rejection rule, not an ownership issue: both copies select no
fields. Checking it differently after instantiation would break definition-site
checking. Either value extraction becomes total for these empty cases, eligibility
gets a separate proof, or generic value extraction is narrowed in scope.

**B. Replacement does not specify the nominal source's remaining state.**

```metel
struct Source { pub token: Token, pub id: i32, hidden: i32 }
// s is an existing Source place; Token is non-Copy but discardable.
let updated := .{ ..s, .token = make_token() };
// Is s.token still present here?
```

Section 5 consumes an anonymous source and discards its replaced token, but
characterizes a nominal source as selected ordinary field accesses. Under that
characterization the old token is never accessed and remains in s. The draft must
choose and specify the result, including the case where Token is linear. A shape
bound alone does not distinguish those ownership protocols in a generic body.
Recommendation: initially support owned anonymous-record transfer and borrowed
Copy extraction; defer owned nominal extraction until its replacement, residual
and temporary-cleanup rules are explicit. This is a scope recommendation, not an
adopted removal of section 5's proposed nominal feature.

**C. A nested materialization cannot inherit the outer replacement mask.**

```metel
// reference points to { id: Copy, token: non-Copy }.
let direct := .{ ..reference, .token = make_token() }; // can copy only id
let all := .{ ..reference };                         // rejected: token not Copy
let indirect := .{ ..all, .token = make_token() };
```

The second line must be rejected even if the third would replace token. The same
boundary applies when the inner assembly is written as a nested literal. Section
6 makes this explicit. A field initializer with effects cannot be eliminated by
an outer replacement either. This clarifies the contextual design without adding
first-class deferred transfers.

**D. Unknown is not empty.**

```metel
// Schematic obligation: every field of ..T must implement Clone.
fun inspect<T>(x: &T) {
    // Cannot discharge that obligation merely because T has no known fields.
}
// Instantiate with a public-field struct containing a non-Clone Token.
```

Section 3 correctly rejects the vacuous proof. RFC-0254 still contains the earlier
empty-abstract-row rule as well as its reconciliation warning. Acceptance requires
one rule in that owner RFC, including unknown versus exact-empty equality and
field-wise obligations. This RFC cannot claim that conflict resolved solely by
stating the desired replacement locally.

**E. Borrowed extraction must retain the place through dereference.**

```metel
let reference := &source;
let copied := .{ ..reference, .token = make_token() };
```

An eager by-value read of the whole referent would incorrectly require token to
be Copy. Extract from the borrowed place, and copy only the selected fields. The
same rule applies if the source is a nested reference or is written explicitly as
`..(*reference)`.

## 14. Acceptance decisions

The following are unresolved; recommendations are not owner resolutions. Review
should settle these one at a time and update the governing sections, rather than
accumulate a parallel history of decisions.

1. **Value-source eligibility — owner decision, joint RFC-0254 reconciliation.**
   Resolve case A. Recommend allowing empty value extraction for concrete empty-row
   categories, with operand evaluation and ownership obligations preserved, rather
   than introducing a new record-like kind or treating an empty bound as category
   evidence. An empty projection does not consume an existing place or dispose of
   a temporary. This would amend section 4's rejection rule and needs explicit
   approval; universal type extraction alone has not adopted it.
2. **Owned nominal extraction — owner decision and RFC-0071/0150 boundaries.**
   Resolve case B and give exact ownership/cleanup rules, or defer the feature.
   Recommend the narrower initial scope stated in case B. Borrowed Copy extraction
   and owned anonymous records remain useful without nominal dismantling.
3. **Abstract rows — RFC-0254/0208 settlement.** Adopt a substitution-stable symbolic
   projection with explicit exact/open/unknown rules, and reconcile the owner RFCs.
   Section 3 is the recommended rule, not evidence that the owner text agrees yet.
Design settlement is tracked by metel-core#2206. Acceptance requires resolving
these blocking questions, rerunning the counterexamples and reconciling sibling
text. No implementation is authorized before integration.

## Decision

**Outcome:** Acceptance pending. The language owner approved splitting ordinary
call expansion into RFC-0256 and making references transparent to structural
bounds and extraction on 2026-11-27. The three acceptance questions above
remain unresolved.
