---
id: rfc-0221
title: "Dotted Field Entries"
date: '2026-11-07'
status: draft
---

## Summary

**A field entry is written as a label: `.name`.** In record and struct literals, in patterns, in
anonymous record types, in row bounds and in projection lists, the field a brace group names is
`.x`, never a bare `x`. Field selection is unchanged: `p.x` is `p` followed by the label `.x`.

```metel
let p := { .x = 1.0, .y = 2.0 };                 // was { x = 1.0, y = 2.0 }
let q := Point { .x = 1.0, .y = 2.0 };           // was Point { x = 1.0, y = 2.0 }
let { .x, .y } := p;                             // was let { x, y } := p;
fun norm<record R>(v: { .x: f64, ..R }) -> f64   // was { x: f64, ..R }
```

This is the field-entry half of RFC-0188. RFC-0188 spells a label as `.name` and `.[L]` but leaves
ordinary field entries bare. This RFC makes the label spelling the only spelling of a field entry, so
a fixed label (`.x`) and a label variable (`.[L]`) occupy the same slot and differ only in what is
inside the dot form.

Nominal `struct` and `record` declarations are unchanged (Open Question 1). Nothing here changes the
semantics of records, structs or rows.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### A field entry is a bare identifier, and a block can start with one

A record literal and a block are the same text until something later in the group disambiguates them.
RFC-0187 records the consequences: `{ x }` and `{ x = 1 }` are records only in some positions, a
multi-field literal works anywhere only because a comma cannot appear in a block, and the empty
literal is position-dependent. RFC-0183 makes plain assignment `=`, which adds a third reading of
`{ x = 1 }` (a block whose tail is an assignment).

Assignment as a statement removes most of this: an assignment needs its `;`, so `{ x = 1 }` cannot be
a block tail. Two cases survive. A single pun `{ x }` is still a block returning `x` (RFC-0187's
workaround is the trailing comma `{ x, }`), and `{}` is still an empty block in statement position.

A block cannot start with `.`. A brace group whose first entry is `.x` is therefore a record in every
position, with no lookahead, no trailing-comma rule and no parentheses. That removes the pun case.
It does not remove the empty-record case (Open Question 2).

### A label has two spellings

RFC-0188 introduces `.name` for a label used as a value and keeps a plain identifier for the same label
used as a field entry. Its own numeric-label examples already write `{| .0 = a, .1 = b |}`, because
`0 = a` cannot be a bare identifier, so a tuple's fields are dotted and a record's are not. RFC-0188
Open Question 1 asks whether `.x` should also be accepted in field position and recommends no, on the
grounds that "a mandatory prefix would mark everything twice."

That reasoning holds while the dot only marks a *value* label. If the dot is what a label *is*, a field
entry is the same thing as a label literal, and the second spelling is the redundancy:

```metel
let p := { .x = 1.0, .y = 2.0 };
p.x                          // `p` followed by the label `.x`
p.[l]                        // `p` followed by the label variable `.[l]`
{ .[l] = v, ..p }            // the same slot, filled by a variable
let t := { .0 = a, .1 = b }; // numeric labels need no special case (RFC-0151)
```

### The left of `=` is a label, not a name

RFC-0183 states the separator invariant: `:=` when the left-hand side is a name the site introduces,
`=` when it is a place, slot or label that already exists. A bare `x` on the left of `=` in
`Point { x = x }` is the same word twice, with different roles. `Point { .x = x }` shows the role: the
left is a label, the right is a variable.

---

## Proposal

### 1. The field-entry form

A **field entry** is a label followed by what the site gives it. A **label** is `.name`, `.0` (a
decimal integer) or `.[expr]`; the last is RFC-0188's and is not extended here.

| site | today | proposed |
|---|---|---|
| record or struct literal | `{ x = 1, y }` | `{ .x = 1, .y }` |
| spread | `{ ..r, x = 1 }` | `{ ..r, .x = 1 }` (the spread keeps `..`) |
| record or struct pattern | `{ x, y: _, ..rest }` | `{ .x, .y: _, ..rest }` |
| anonymous record type | `{ x: i64, ..R }` | `{ .x: i64, ..R }` |
| row bound entry | `{ x: T, .. }` | `{ .x: T, .. }` |
| negative bound entry (RFC-0189) | `!{x}`, `{ !x: T }` | `!{.x}`, `{ !.x: T }` |
| projection list | `Handle.{ fd, ..R }` | `Handle.{ .fd, ..R }` |
| row equation | `R = { x: T, ..Rest }` | `R = { .x: T, ..Rest }` |

A pun is a label with no value: `{ .x }` means `{ .x = x }`, and in a pattern binds `x`.

**Unchanged:**

- Field selection and method calls: `p.x`, `p.0`, `p.f()`.
- Nominal declarations: `struct Point { x: f64 }`, `record Packet { data: … }` (Open Question 1).
- Parameter lists, keyword arguments (`f(x = 1)`) and associated-type bindings (`Deref<Target = Node>`).
  A parameter or an associated type is not a label of a row.
- Tuple expressions and types `(a, b)` / `(A, B)`, which RFC-0151 treats as notation for a numeric-label
  row. The dotted form `{ .0 = a, .1 = b }` is what they denote.

### 2. Why this parses without lookahead

In a brace group, an entry that starts with a single `.` is a field entry. Nothing else starts with a
single `.` there:

- `..` starts a spread or a rest, and is distinguished from `.x` by its second character.
- A block statement or expression never starts with `.`; `float_lit` requires a leading digit.

A brace group that starts with a field entry is a record in every position. It is not a block in an
`if` arm, a `match` arm, a function body or a closure body, and a single-field literal needs no
parentheses.

### 3. Struct literals and patterns

A named literal uses the same production. The type path before the brace is unchanged:

```metel
let origin := Point { .x = 0.0, .y = 0.0 };
let moved  := Point { .x = 1.0, ..origin };
match shape { Circle { .r } => r, Rect { .w, .h } => w * h }
```

The dot adds no disambiguation here, since the type path already marks the literal. It is there for the
single field-entry rule (Motivation).

### 4. Diagnostics

A bare entry in a brace group becomes a targeted error, not a bare parse failure:

- `{ x = 1 }` → "a field entry is written `.x = 1`; to assign, end the statement with `;`" (the second half
  applies when RFC-0183 is accepted and the group could be read as a block).
- `Point { x = 1 }` → "a field entry is written `.x = 1`".

The one-dot slip: `{ .a = 1, .r }` where `..r` was meant is a valid pun of a field `r`. When the group has
an expected row that does not contain `r`, the field is rejected by the ordinary row check. When it does
not, the program is accepted and means a pun. An optional lint (not an error) warns when a pun names an
in-scope variable whose type is a record or struct and the group has no spread.

---

## Interactions

- **RFC-0188 (Label syntax):** this RFC answers its Open Question 1 as "yes, required, not equivalent":
  a field entry is a label. RFC-0188's statement that "ordinary field entries keep the plain identifier"
  is replaced. RFC-0188 keeps the spelling of `.[L]`, numeric labels and its remaining open questions.
- **RFC-0175 (Label Polymorphism):** a fixed label and a label variable share one slot, so
  `{ .[L]: T, ..R }` and `{ .x: T, ..R }` are the same shape.
- **RFC-0187 (Anonymous record delimiters):** the pun and multi-field collisions are removed without a new
  delimiter. What remains of RFC-0187 is the empty record `{}` (Open Question 2). This RFC does not
  decide that, and does not supersede RFC-0187.
- **RFC-0183 (Initialization-only walrus):** unchanged and still needed. Statement-only assignment removes
  the `f(x = 1)` and `if (x = 1)` expression hazards. With this RFC, RFC-0183's tail-assignment rule
  (a single-field `{ label = expr }` with no `;` is a record) no longer has a bare-entry case to cover,
  because that text is an error.
- **RFC-0191 (One-field record update):** `{ ..s, .a = 10 }`. Its open question on the replacement
  marker is unaffected: the replacement is a field entry in the new spelling.
- **RFC-0189 (Per-label negative bounds):** entries become `!.x` / `!.x: T`. The whole-row form
  `!{ .a, .b: T }` is sugar for `{ !.a, !.b: T, .. }` as before.
- **RFC-0151 (Tuples as numeric-label rows):** `{ .0 = a, .1 = b }` is what `(a, b)` denotes, with no
  special lexical case.
- **RFC-0115 (Field initializer separator):** the separator stays `=`. Only the left-hand side changes.
- **RFC-0100 (Constructor-call construction):** not assumed. If accepted, `Point(x = 1)` takes
  parameter names, which are not labels, and stays bare.
- **RFC-0121 / RFC-0186 / RFC-0208 (Open rows, `..R` operator, row binder):** the row splice `..R` and the
  binder are unchanged. Only the labels inside the braces move.

---

## Alternatives Considered

| Option | Record | Verdict |
|---|---|---|
| **Dotted field entries** | `{ .x = 1 }` | **Proposed.** One spelling for a label, no block collision for a non-empty literal, numeric labels uniform. Costs a dot on every field. |
| Bare entries + statement-only assignment | `{ x = 1 }`, `{ x, }` for one pun | The smaller change. Leaves the pun needing a trailing comma and the label with two spellings. Viable if the label model is not adopted. |
| `{\| … \|}` delimiters (RFC-0187) | `{\| x = 1 \|}` | Solves the pun and the empty record. Does not unify the label spelling, and adds a delimiter pair. Not exclusive of this RFC. |
| Dotted literals only | `{ .x = 1 }` literal, `{ x: T }` type | Cheaper in signatures. Keeps the second spelling at exactly the sites where a label variable is written. Open Question 1. |
| Zig-style | `.{ .x = 1 }` | Clashes with `..{` row-literal splices (RFC-0180) and dot paths (RFC-0099). Heavier. |
| `#{ … }` | `#{ x = 1 }` | Unambiguous and light, but a second sigil for the same idea and does nothing for the label spelling. |

---

## Migration

Every record and struct literal, pattern, anonymous record type, row bound and projection list gains a dot
on each field. The sites are syntactically identifiable by the grammar productions in §1, so the rewrite is
mechanical, and a bare entry produces the targeted error in §4. Declarations, selections, parameter lists
and keyword arguments are untouched.

This is a second pass over the same records as RFC-0115 (separator) and, if accepted, RFC-0183 (assignment),
and should be scheduled with them. It is a breaking change to the most common record form, so it needs this
RFC first (see `metel_rfc_before_implementation`). A count of affected sites in fixtures, spec examples and
the blog is taken for the prototype, not estimated here.

---

## Costs

- **Verbosity.** Every field in every literal, pattern and anonymous type gains a character. Signatures
  with several fields are the heaviest case.
- **The one-dot slip** (§4). `.r` for `..r` is a valid pun. Mitigated by the row check and the lint, not
  eliminated.
- **A second breaking pass** over record code (Migration).
- **Two forms for a nominal field.** `struct Point { x: f64 }` declares bare and `Point { .x = 1.0 }` uses
  dotted (Open Question 1). This is the same shape as a parameter list and its keyword call today.

---

## Changes on Acceptance

- `grammar.pest` and the generated `grammar.md`: `field_init`, `record_type_field`, `record_field_pat`,
  `field_pat_list`, `row_field`, `record_projection_expr` and `record_projection_type`, and the negative-bound
  entry, take a `label`.
- Spec: records, structs, patterns, types and row bounds. Rules that say "a field `x`" are restated in terms
  of the label `.x`.
- RFC-0188 amended (Interactions). RFC-0187 narrowed to the empty record or refused, by its own review.
- Error code for a bare field entry, with a fixture each for literal, pattern, type and bound.
- A migration tool or rewrite recipe, and fixtures and spec examples converted.

---

## Open Questions

1. **Extent: types, bounds and declarations.** The proposal dots every site in §1 and leaves nominal
   `struct`/`record` declarations bare, on the reading that a declaration introduces a field the way a
   parameter list introduces a parameter, while an anonymous type, a bound and a projection *name* labels.
   The alternatives are literals and patterns only (cheaper signatures, label variables still written next
   to bare names in types), or declarations too (`struct Point { .x: f64 }`, fully uniform, heaviest).
   This is the decision that most affects the cost.
2. **The empty record.** `{}` is an empty block in statement position and an empty record elsewhere. A dot
   cannot mark an entry that does not exist. Candidates: leave `{}` position-dependent as today; give the
   empty record its own spelling; or keep RFC-0187's `{| |}` for the empty case alone. This belongs to
   RFC-0187's remainder, not here.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- A brace group starting with `.x`, `.0` or `.[e]` parses as a record in every position where a block is
  also allowed, and a group starting with a bare identifier never parses as a record.
- `.x` is confirmed unambiguous against `..` spreads, float literals and every other brace-group entry.
- A count of affected sites in fixtures and spec examples.
- The `.r` / `..r` slip: the row check rejects it when the expected row is known, and the lint fires when it
  is not.

---

## References

- RFC-0188 — Label syntax; RFC-0175 — Label Polymorphism; RFC-0151 — Tuples as numeric-label rows.
- RFC-0187 — Anonymous record delimiters; RFC-0183 — Initialization-only walrus;
  RFC-0115 — Field initializer separator; RFC-0100 — Constructor-call construction.
- RFC-0191 — One-field record update; RFC-0189 — Per-label negative row bounds.
- RFC-0116, RFC-0121, RFC-0186, RFC-0208 — records, open rows, the `..R` operator and the row binder.

---

## Decision

**Outcome:** *(pending)*
