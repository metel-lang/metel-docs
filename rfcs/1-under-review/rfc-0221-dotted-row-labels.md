---
id: rfc-0221
title: "Dotted Row Labels"
date: '2026-11-07'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/1847'
updated: '2026-11-07'
---

> **Status — under review (2026-11-07).** Committed to the v0.16.0 stage Call and record syntax (metel-core#1847); review still has an open prerequisite (the parser prototype). It does not depend on RFC-0151 (decided 2026-11-07): the empty brace group keeps today's rule, section 5.

## Summary

**A label of a row is written `.name`.** In an anonymous record literal, pattern, type, row bound and row
equation, and in a projection list (`Handle.{ .fd, ..R }`), the label is `.x`, never a bare `x`. Field selection
is unchanged: `p.x` is `p` followed by the label `.x`.

```metel
let p := { .x = 1.0, .y = 2.0 };                 // was { x = 1.0, y = 2.0 }
let { .x, .y } := p;                             // was let { x, y } := p;
fun norm<record R>(v: { .x: f64, ..R }) -> f64   // was { x: f64, ..R }
fun read<record R>(h: Handle.{ .fd, ..R })     // was Handle.{ fd, ..R }
```

The rule: **a name is dotted when it is a label of a row, and bare when it is a member that a nominal type
declares for itself.** Struct and enum construction is the call of RFC-0100 (`Point(x = 1.0, y = 2.0)`), and
struct and enum declarations and patterns keep bare names. Those names are the type's own parameters. An
anonymous record and a projection list are views of a row, which is where a label can be a variable
(`.[L]`, RFC-0188).

This is the field-entry half of RFC-0188. RFC-0188 spells a label `.name` and `.[L]` but leaves the fields of an
anonymous record bare. This RFC makes the label spelling the only spelling there. Nothing here changes the
semantics of records or rows.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### The only brace expression left is the record

RFC-0100 prohibits `Type { x = 1 }` and `Enum::Variant { x = 1 }` in expression position (its §5) and replaces
them with calls. If that lands, a brace group in expression position is a block or an anonymous record, and
nothing else. The collision that RFC-0187 (refused) described is then between those two alone:

- A single pun `{ x }` is a block returning `x`. RFC-0187's workaround is the trailing comma `{ x, }`.
- The empty literal `{}` is an empty block in body and arm positions and an empty record elsewhere (§5).
- With RFC-0183, assignment is a statement and needs its `;`, so `{ x = 1 }` cannot be a block tail. That
  already removes the single-field assignment case without any new syntax.

A block cannot start with `.`. A brace group whose first entry is `.x` is therefore a record in every position,
with no lookahead, no trailing-comma rule and no parentheses. That removes the pun case. It does not help the empty record, which has no field to mark; §5 resolves that case another way.

### A label has two spellings

RFC-0188 introduces `.name` for a label used as a value and keeps a plain identifier for the same label used as
a field of a record. Its own numeric-label examples already write `.0 = a, .1 = b`, because `0 = a` cannot
be a bare identifier, so a tuple's fields are dotted and a record's are not. RFC-0188 Open Question 1 asks
whether `.x` should also be accepted in field position and recommends no, on the grounds that "a mandatory
prefix would mark everything twice."

That reasoning holds while the dot only marks a *value* label. If the dot is what a label *is*, a field of an
anonymous record is the same thing as a label literal, and the second spelling is the redundancy:

```metel
let p := { .x = 1.0, .y = 2.0 };
p.x                          // `p` followed by the label `.x`
p.[l]                        // `p` followed by the label variable `.[l]`
{ .[l] = v, ..p }            // the same slot, filled by a variable
let t := { .0 = a, .1 = b }; // numeric labels need no special case (RFC-0151)
```

### The left of `=` is a label, not a name

RFC-0183 states the separator invariant: `:=` when the left-hand side is a name the site introduces, `=` when
it is a place, slot or label that already exists. In `{ x = x }` the same word appears twice with different
roles. `{ .x = x }` shows the roles: the left is a label, the right is a variable.

### Where the dot applies

A struct's field names are parameter names of its constructor (RFC-0100 §7), and the type path that heads a
struct declaration, call or pattern says whose members they are. A bare name there is unambiguous and carries no
extra information if dotted.

A row is different. An anonymous record has no head, and a projection list `Handle.{ … }` does not name the
type's members but selects labels out of its row, and leaves a residual `..R`. In both, the names are labels,
they can be label variables, and they take part in row bounds and equations (RFC-0121, RFC-0189). One list of
labels is then spelled the same way wherever it appears: `{ .fd, ..R }` and `Handle.{ .fd, ..R }`.

---

## Proposal

### 1. The field form

A **label** is `.name`, `.0` (a decimal integer) or `.[expr]`; the last is RFC-0188's and is not extended here.
In an **anonymous record**, each field is a label followed by what the site gives it:

| site | today | proposed |
|---|---|---|
| record literal | `{ x = 1, y }` | `{ .x = 1, .y }` |
| spread | `{ ..r, x = 1 }` | `{ ..r, .x = 1 }` (the spread keeps `..`) |
| record pattern | `{ x, y: _, ..rest }` | `{ .x, .y: _, ..rest }` |
| record type | `{ x: i64, ..R }` | `{ .x: i64, ..R }` |
| row bound entry | `{ x: T, .. }` | `{ .x: T, .. }` |
| negative bound entry (RFC-0189) | `!{x}`, `{ !x: T }` | `!{.x}`, `{ !.x: T }` |
| row equation | `R = { x: T, ..Rest }` | `R = { .x: T, ..Rest }` |
| projection list (type and expression) | `Handle.{ fd, ..R }` | `Handle.{ .fd, ..R }` |

A pun is a label with no value: `{ .x }` means `{ .x = x }`, and in a pattern binds `x`.

**Unchanged:**

- Field selection and method calls: `p.x`, `p.0`, `p.f()`.
- Struct and enum construction, which is the call of RFC-0100: `Point(x = 1.0)`, `Shape::Rect(w = 2.0, h = 3.0)`.
- Struct and enum declarations: `struct Point { x: f64 }`, `enum Shape { Rect { w: f64, h: f64 } }`.
- Struct and enum patterns: `Point { x, y }`, `Shape::Rect { w, h }` (RFC-0100 §4).
- Parameter lists, keyword arguments and associated-type bindings (`Deref<Target = Node>`). A parameter or an
  associated type is not a label of a row.
- Tuple expressions and types `(a, b)` / `(A, B)`, which RFC-0151 treats as notation for a numeric-label row.
  The dotted form `{ .0 = a, .1 = b }` is what they denote.

### 2. Between a struct and a record

A struct and its row are the same fields seen two ways (RFC-0137). The member spelling (`x`) and the label
spelling (`.x`) meet in the spread of RFC-0100 §7, and a projection list `Handle.{ .fd }` is on the label side:

```metel
let r := { .x = 1.0, .y = 2.0 };      // a record: labels
let p := Point(..r);                  // a struct from a record: Point::construct(r)
let q := Point(x = 1.0, y = 2.0);     // the same struct, by parameter name
p.x == r.x                            // selection is the same on both
```

### 3. Why this parses without lookahead

In a brace group, an entry that starts with a single `.` is a field. Nothing else starts with a single `.` there:

- `..` starts a spread or a rest, and is distinguished from `.x` by its second character.
- A block statement or expression never starts with `.`; `float_lit` requires a leading digit.

A brace group that starts with a field is a record in every position. It is not a block in an `if` arm, a `match`
arm, a function body or a closure body, and a single-field literal needs no parentheses.

### 4. Diagnostics

A bare field in an anonymous record becomes a targeted error, not a bare parse failure:

- `{ x = 1 }` → "a record field is written `.x = 1`; to assign, end the statement with `;`" (the second half
  applies when RFC-0183 is accepted and the group could be read as a block).

The one-dot slip: `{ .a = 1, .r }` where `..r` was meant is a valid pun of a field `r`. When the group has an
expected row that does not contain `r`, the field is rejected by the ordinary row check. When it does not, the
program is accepted and means a pun. An optional lint (not an error) warns when a pun names an in-scope variable
whose type is a record or struct and the group has no spread.

### 5. The empty record

A dot cannot mark a field that does not exist, so the empty record has no dotted form, and it needs no new one. **This
RFC does not change `{}`** (decided 2026-11-07, language owner): the rule in force today stays.

- `{}` as the body of a function, an `if` or `else`, a loop or a match arm parses as a block, and elsewhere as a record.
  A mismatch between the empty block and the empty record is a type error, never a silent wrong meaning, and the
  workarounds `({})` and `{ {} }` stay.
- No new delimiter is needed for the empty record (RFC-0187's `{| |}`).
- The remaining mismatches are type errors on non-empty values, as before.

Making `()` and `{}` one type and one value (RFC-0151 §6) would remove the workarounds. That is a separate decision,
and the text above works with or without it: if it is accepted later, an empty brace group becomes the same value
under either reading and the workarounds are no longer needed.

---

## Interactions

- **RFC-0100 (Constructor-call construction):** removes struct and enum brace construction, which is what makes
  the anonymous record the only brace expression. Its `Type(..r)` is the bridge from a dotted record to a struct
  (§2).
- **RFC-0188 (Label syntax):** this RFC answers its Open Question 1 as "yes, required, not equivalent": a field
  of an anonymous record is a label. It also answers Open Question 2 the other way: label lists in projections
  (`Handle.{ .fd }`) and negative bounds (`!{.fd}`) are dotted, not plain. RFC-0188's statement that "ordinary field entries keep the plain
  identifier" is replaced for records. RFC-0188 keeps the spelling of `.[L]`, numeric labels and its remaining
  open questions.
- **RFC-0175 (Label Polymorphism):** a fixed label and a label variable share one slot, so `{ .[L]: T, ..R }`
  and `{ .x: T, ..R }` are the same shape.
- **RFC-0187 (Anonymous record delimiters, refused 2026-11-07):** this RFC removes the pun collision without a
  new delimiter, and the empty record needs none (§5), so no case for a delimiter remained.
- **RFC-0183 (Initialization-only walrus):** unchanged and still needed. Statement-only assignment removes the
  `f(x = 1)` and `if (x = 1)` expression hazards, and with RFC-0100 `f(x = 1)` is unambiguously a keyword
  argument. RFC-0183's tail-assignment rule has no bare-field case left to cover.
- **RFC-0191 (One-field record update):** `{ ..s, .a = 10 }`. Its open question on the replacement marker is
  unaffected: the replacement is a field in the new spelling.
- **RFC-0189 (Per-label negative bounds):** entries become `!.x` / `!.x: T`. The whole-row form `!{ .a, .b: T }`
  is sugar for `{ !.a, !.b: T, .. }` as before.
- **RFC-0151 (Tuples as numeric-label rows):** `{ .0 = a, .1 = b }` is what `(a, b)` denotes, with no special
  lexical case. This RFC does not depend on RFC-0151. Its §6 (`()` is the empty row `{}`) would remove the `{}`
  workarounds of §5 and is a separate decision.
- **RFC-0216 (Constructing rows and residuals):** its computed-label literal `{ [field.name] = expr }` is a
  third spelling of a computed label; under this RFC it is `{ .[field.name] = expr }`. Its residual construction
  `T.{ ..R } { entries }` is a brace construction and falls under RFC-0100 §5 (see RFC-0100's open questions).
- **RFC-0115 (Field initializer separator):** the separator stays `=`. Only the left-hand side changes.
- **RFC-0121 / RFC-0137 / RFC-0186 / RFC-0208 (Open rows, branded rows, `..R` operator, row binder):** the row
  splice `..R` and the binder are unchanged. Only the labels inside the braces move, including those in the
  projections `Handle.{ fd }` that RFC-0121 and RFC-0137 write.

---

## Alternatives Considered

| Option | Record | Verdict |
|---|---|---|
| **Dotted fields, anonymous records only** | `{ .x = 1 }` | **Proposed.** One spelling for a label, no pun collision, numeric labels uniform, nominal syntax untouched. Costs a dot on every record field. |
| Dotted fields for structs and enums too | `Point { .x = 1 }` | The earlier form of this RFC. Dropped: RFC-0100 removes struct and enum brace construction, and a head already says whose fields they are, so the dot adds nothing there. |
| A spelling for the empty record (`{\| \|}`) | `{\| \|}` for `{}` | Removes the position rule, but adds a special spelling for one value, and rewrites every `{}` value in current code. Unneeded once `()` and `{}` are one type (§5). |
| Bare fields + statement-only assignment | `{ x = 1 }`, `{ x, }` for one pun | The smaller change. Leaves the pun needing a trailing comma and the label with two spellings. Viable if the label model is not adopted. |
| `{\| … \|}` delimiters (RFC-0187, refused) | `{\| x = 1 \|}` | Solves the pun and the empty record. Does not unify the label spelling, and adds a delimiter pair. Not exclusive of this RFC. |
| Bare projection lists | `Handle.{ fd, ..R }` | Simpler head rule, but then a list of labels is spelled two ways in one signature (`{ .fd, ..R }` and `Handle.{ fd, ..R }`), and RFC-0188's `!{.fd}` would differ from `.{ fd }`. Rejected. |
| Dotted literals only | `{ .x = 1 }` literal, `{ x: T }` type | Cheaper in signatures. Keeps the second spelling at exactly the sites where a label variable is written. |
| Zig-style | `.{ .x = 1 }` | Clashes with `..{` row-literal splices (RFC-0180) and dot paths (RFC-0099). Heavier. |
| `#{ … }` | `#{ x = 1 }` | Unambiguous and light, but a second sigil for the same idea and does nothing for the label spelling. |

---

## Migration

Every anonymous record literal, pattern, type, row bound and row equation gains a dot on each field. The sites
are syntactically identifiable by the productions in §1, so the rewrite is mechanical, and a bare field produces
the targeted error in §4. Struct and enum code, selections, parameter lists and keyword arguments are untouched
by this RFC. (RFC-0100 has its own rewrite for struct and enum construction.)

This is a second pass over the same records as RFC-0115 (separator) and, if accepted, RFC-0183 (assignment), and
should be scheduled with them. It is a breaking change to the most common record form, so it needs this RFC first
(see `metel_rfc_before_implementation`). A count of affected sites in fixtures, spec examples and the blog is
taken for the prototype, not estimated here.

---

## Costs

- **Verbosity.** Every record field gains a character. Signatures with several fields are the heaviest case.
- **The same field has two spellings across the struct/record boundary.** `Point(x = 1.0)` and `{ .x = 1.0 }`
  differ. The rule explains it (members versus labels of a row), but a reader has to learn it.
- **The one-dot slip** (§4). `.r` for `..r` is a valid pun. Mitigated by the row check and the lint, not
  eliminated.
- **A second breaking pass** over record code (Migration).

---

## Changes on Acceptance

- `grammar.pest` and the generated `grammar.md`: the anonymous-record forms of `field_init`,
  `record_type_field`, the record pattern, `row_field`, the negative-bound entry, and the projection lists
  (`record_projection_expr`, `record_projection_type`, `open_record_projection_type`) take a `label`.
- Spec: records, patterns, types and row bounds. Rules that say "a field `x`" of a record are restated in terms
  of the label `.x`.
- RFC-0188 amended (Interactions). RFC-0187 refused.
- Error code for a bare record field, with a fixture each for literal, pattern, type and bound.
- A migration tool or rewrite recipe, and fixtures and spec examples converted.

---

## Open Questions

None blocking.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- A brace group starting with `.x`, `.0` or `.[e]` parses as a record in every position where a block is also
  allowed, and a group starting with a bare identifier never parses as a record.
- `.x` is confirmed unambiguous against `..` spreads, float literals and every other brace-group entry.
- A count of affected sites in fixtures and spec examples.
- `{}` behaves as it does today in every position: a block where a block is required, a record elsewhere, with the
  workarounds `({})` and `{ {} }` unchanged, and a fixture for each position.
- The `.r` / `..r` slip: the row check rejects it when the expected row is known, and the lint fires when it is
  not.

---

## References

- RFC-0188 — Label syntax; RFC-0175 — Label Polymorphism; RFC-0151 — Tuples as numeric-label rows.
- RFC-0100 — Constructor-call construction; RFC-0114 — Constructor aspect and canonical construction.
- RFC-0187 — Anonymous record delimiters; RFC-0183 — Initialization-only walrus;
  RFC-0115 — Field initializer separator.
- RFC-0191 — One-field record update; RFC-0189 — Per-label negative row bounds;
  RFC-0216 — Constructing rows and residuals from per-field results.
- RFC-0116, RFC-0121, RFC-0186, RFC-0208 — records, open rows, the `..R` operator and the row binder.

---

## Decision

**Outcome:** *(pending)*
