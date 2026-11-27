---
id: rfc-0257
title: "Whole-Row Construction Arguments"
date: '2026-11-27'
status: draft
---

> **Split from [RFC-0100](../3-integrated/rfc-0100-constructor-call-construction.md) section 6 (language owner, 2026-11-27).** RFC-0100 originally defined its own
> `..r`/`..{ ... }` grammar for the constructor whole-row operand. RFC-0255 has
> since proposed a shared "section" grammar and extraction contract for every
> `..value`/`..{ entries }` consumer (record assembly, this one, and RFC-0256's
> ordinary-call expansion), explicitly preserving this RFC's own exact-label
> binding rule (RFC-0255 section 7). RFC-0100's other sections (1/2/3/5/7) do not
> depend on RFC-0255 at all and stay `3-integrated`, unblocked; only this one
> piece is split out, so it can wait on RFC-0255/RFC-0256 without holding up
> anything already settled.

## Summary

A whole-row construction operand supplies exactly a constructor's parameter
row — the same labels and corresponding field types, every field, no extras —
as the sole argument to a call-syntax construction (RFC-0100 section 2):

```metel
let fields := .{ .x = 10, .y = 20 };
let a := Point(..fields);
let c := Point(..{ .x = 10, .y = 20 });
```

This RFC owns exactly one thing: that a constructor's whole-row operand binds
by exact label, as the sole argument, with no implicit record-to-nominal
coercion elsewhere. It does not define the `..value`/`..{ entries }` grammar,
extraction eligibility, ownership or evaluation-order rules — those are RFC-0255's,
shared across every consumer of that syntax. This RFC consumes RFC-0255's
"section" the same way record assembly and (via RFC-0256) ordinary calls do,
each with its own binding policy.

## Motivation

RFC-0100 section 6 originally specified `..r`/`..{ ... }` as a plain-binding-only
operand, explicitly deferring "arbitrary expression operands after `..` (for
example `..make_fields()`)" as "a future extension, not included here." RFC-0255
is that extension, generalized across every section consumer rather than
constructor-specific. Keeping RFC-0100 itself pinned to its own, narrower
grammar once RFC-0255 exists would mean two competing specifications of the
same `..` syntax; splitting this content out lets it track RFC-0255 directly
instead.

## 1. The binding rule (unchanged from RFC-0100 section 6)

A whole-row operand supplies exactly the construction parameter row, with the
same labels and corresponding field types under ordinary checking and generic
inference. It supplies every field, no extra fields, and satisfies the same
visibility requirements as explicit field arguments. Anonymous record field
order does not determine the binding: row labels do.

A whole-row operand must be the sole argument. Reject multiple whole-row
operands and mixtures such as `Point(..fields, x = 5)`. To replace a field,
explicitly build an updated record using the existing record-update rules
first, or use a whole-row literal containing the update:

```metel
let p := Point(..{ ..fields, .x = 5 });
```

Evaluate the operand once, then perform the same canonical construction as
positional/keyword arguments. No record-to-nominal coercion is added outside
these explicitly marked expressions.

```metel
struct Wrapper { position: .{ .x: i64, .y: i64 } }
Wrapper(fields)                 // position receives one record value
Wrapper(..fields)               // error: the whole row needs .position
Wrapper(..{ .position = fields }) // accepted
```

RFC-0255 section 7 already states this exact-label contract as the one it
preserves for construction; this RFC is the citable owner of that contract,
not a restatement of RFC-0255's own text.

## 2. What moved to RFC-0255

The following, previously stated as RFC-0100's own rules, are now RFC-0255's
shared grammar and extraction contract, applying uniformly to this consumer:

- The `..value` / `..{ entries }` grammar itself, including the contiguous
  `..{` literal opener (not `..` followed by `.{`), and that parsing is
  contextual rather than an unrestricted unary-expression rule.
- Arbitrary expression operands (`Point(..make_fields())`), superseding this
  RFC's original plain-binding-only restriction.
- Source eligibility, visibility, ownership and single-evaluation rules for
  the operand.
- The literal's own spread/update semantics (RFC-0191 still owns those, per
  RFC-0255 section 6).

## 3. Dependencies

| RFC | Relationship |
|---|---|
| RFC-0255 | Owns the shared section grammar, extraction and ownership rules this operand uses; this RFC does not proceed to integration ahead of it |
| RFC-0256 | Sibling consumer (ordinary calls); no shared rule between the two beyond RFC-0255's contract — construction keeps its exact-label binding regardless of what RFC-0256 settles for positional/keyword expansion |
| RFC-0100 | Owns call-syntax construction itself (section 2) and the privileged representation form (section 3); this RFC supplies only the whole-row operand to that call syntax |

## Open questions

Inherits RFC-0255's own unresolved acceptance questions (value-source
eligibility, owned nominal extraction, abstract-row reconciliation) as
blocking preconditions — this RFC adds none of its own beyond confirming its
exact-label binding rule is unaffected by however those resolve.

---

## Decision

**Outcome:** *(pending, blocked on RFC-0255/RFC-0256 reaching at least `2-accepted`)*
