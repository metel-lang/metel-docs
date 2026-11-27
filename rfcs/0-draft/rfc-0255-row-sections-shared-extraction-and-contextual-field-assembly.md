---
id: rfc-0255
title: "Row Sections: Shared Extraction and Contextual Field Assembly"
date: '2026-11-27'
status: draft
---

## Summary

Introduce a **contextual row section**: a structural field source consumed by record
assembly or whole-row argument binding. `..value` extracts a section; `..{ ... }`
introduces one literally. An ordinary anonymous record is its storable value form.
There is no first-class runtime `RowSection<R>` type.

```metel
let fields := .{ ..point };
let next := Point(..{ ..fields, .x = 10 });
consume(..arguments);
```

This is the primary proposal from the 2026-11-27 design discussion, recorded at the
language owner's request. Its choices are proposals, not accepted resolutions.
The RFC has no milestone assignment or implementation authorization.

Extraction is shared; consumer policies remain explicit. Record assembly can
replace fields, constructors require their exact parameter row, and positional
calls require dense numeric rows. Explicit dereferencing for borrowed extraction
and symbolic rather than empty abstract rows are deliberate proposed changes that
need reconciliation with existing text before acceptance.

## Motivation and existing behavior

Metel already has type-row extraction, record spread/update, owned remainder
patterns, numeric-label tuples and structural bounds. RFC-0100 proposes whole-row
construction, RFC-0208 separates row binders from types, and RFC-0247 proposes
collecting positional arguments into tuples. Their common machinery should be
stated once without making their binding and ownership policies identical.

The strongest argument against first-class sections is existing borrowed update:
only carried fields must be Copy. A replaced non-Copy field is not copied.

```metel
// Proposed spelling; token is non-Copy, id is Copy.
let source := .{ .id = 1, .token = make_token() };
let reference := &source;
let result := .{ ..(*reference), .token = make_token() };
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

Value sections are admitted in record assembly, whole-row calls and RFC-0100's
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

References are not implicitly dereferenced:

```metel
let reference := &fields;
let copied := .{ ..(*reference) };
```

Reference values, primitives, enclosing enums, arrays, functions and other
non-field-bearing values are rejected as value-section sources. Their empty
type-level rows do not authorize value dismantling. Empty records and zero-field
structs are eligible, with all nominal ownership obligations preserved.

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
Per-variant constructors retain their RFC-0210 variant result.

`Self .{ ..fields }` retains RFC-0100's constructor-body privilege and complete
representation-row check. Sections transport values, never minting authority.
A tuple row does not become a constructor's named row by matching arity.
Fallibility and unchecked boundaries remain with RFC-0100/0114.

## 8. Ordinary whole-row calls

Add a sole-section argument to ordinary function, associated-function and method
calls. For methods, the receiver is outside the supplied argument row.

- Dense numeric rows `.0` through `.n-1` supply positional arguments in numeric
  order. Sparse rows are rejected rather than renumbered.
- Named rows supply keyword arguments in direct calls that support them. Unknown
  names and duplicate bindings remain errors.
- Mixed numeric/named rows are rejected initially. An empty row supplies zero
  arguments, with no ambiguity between modes.
- Calls through function values accept numeric sections only.
- The section is the sole written argument. Missing arguments remain errors;
  sections neither imply defaults nor silently omit fields.

```metel
let args := (1, "hello");
consume(..args);
configure(..{ .host = "localhost", .port = 8080 });
consume(prefix, ..args); // deferred concatenation
configure(..args, ..);  // not admitted by this RFC
```

Existing overload rules apply to the expanded row. Candidates cannot silently
truncate it or reinterpret numeric labels as names to make themselves match.
Constructor calls retain section 7's exact named-row contract.

For RFC-0247, numeric expansion feeds its fixed/rest split. The collected rest is
an ordinary tuple with local numbering from zero. Whole-list forwarding needs no
concatenation:

```metel
// Fragment: target must accept R; any required bounds must be declared.
fun forward<..R>(..args: .{ R }) {
    target(..args);
}
```

Mixed calls, tuple concatenation and generic renumbering remain with RFC-0125 or a
follow-up. RFC-0248's explicit bare `..` default request remains unchanged.

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
| RFC-0247 / RFC-0125 | Sole-section forwarding here; collection and concatenation retain their owners |
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

**Implicit reference dereferencing.** Avoids a break, but leaves type-level
`..&T` describing the reference and value-level extraction describing its referent.
Explicit `..(*reference)` is the primary proposal.

**One universal merge rule.** Would change record replacement, constructor
exactness or positional binding. Sharing extraction does not justify doing so.

Costs include contextual parsing, source-place-aware elaboration, symbolic generic
projections and call expansion. This is more than a terminology change. It retains
distinct declaration, pattern and default-marker uses of `..` deliberately.

## 12. Compatibility and integration

1. Preserve anonymous-record replacement typing, carried-field Copy checks and
   owned Discard checks.
2. Replace implicit borrowed spread `..reference` with `..(*reference)`, with a
   targeted diagnostic. Never silently reinterpret it as an empty value section.
   Direct `..&record` can be rewritten using a named reference or explicitly
   parenthesized dereference expression.
3. Reconcile RFC-0254's abstract-row classification and RFC-0208's equations before
   implementing generic value extraction.
4. Extend RFC-0100's binding-only operands to expressions. Add ordinary-call
   expansion as a distinct consumer, retaining constructor exactness.
5. Reject deferred ownership cases rather than supplying a permissive fallback.

Specification targets are records/open rows, calls, construction, patterns,
grammar and ownership. Preserve the two-pass checker: inference records shape and
binding facts; construction reads solved facts and elaborates transfers. Retain
source order separately from canonical label order. The evaluator and move checker
must not guess missing ownership decisions from runtime records.

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
| Numeric row contains `.0` and `.2` | Record legal; positional expansion rejected |
| Source expression has observable effects | Evaluate once at its written position |
| Earlier entry moves a field the section needs | Ordinary move error |
| Variant extraction needs an unsupported residual | Rejected; RFC-0150 owns extension |
| Extracted record has an aspect absent from source | Only the record can use that implementation |
| Disjoint labels refer to overlapping places | No authorization for conflicting loans |
| Empty section from nominal temporary with obligations | Obligations remain |
| Named section through function-value signature | Rejected; numeric expansion available |

## 14. Questions for review

The primary proposal chooses concrete defaults, but these are acceptance questions,
not recorded owner resolutions:

1. Is contextual extraction sufficient, or is there a program requiring stored
   deferred transfers rather than ordinary field values?
2. Is explicit dereferencing worth the compatibility break? Review its diagnostics
   together with selective borrowed replacement.
3. Do symbolic projections compose with equations, exact bounds, overloads and
   separate compilation without inverse type inference? Joint RFC-0208/0254 review.
4. Are nominal place extraction and temporary cleanup fully justified by the
   ownership rules selected for integration? Unsupported Drop, linear and variant
   cases need explicit rejection boundaries.
5. Should ordinary whole-row calls land with this abstraction or in a dependent
   RFC? The primary proposal includes sole-section calls without concatenation.

## Decision

**Outcome:** *(pending)*
