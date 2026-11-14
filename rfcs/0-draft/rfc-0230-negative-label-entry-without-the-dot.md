---
id: rfc-0230
title: "Negative Label Entry Without the Dot"
date: '2026-11-14'
status: draft
---

## Summary

A negative entry of a row bound names the label it excludes without the leading dot: `!label` and `!label: T`, where
RFC-0189 writes `!.label` and `!.label: T`.

```metel
fun route<record R: .{ .path: String, !token, !session: u64, .. }>(r: R) -> String { r.path }   // was !.token, !.session: u64
```

Only the negated entry changes. A positive entry stays `.label` (RFC-0221), so a bound reads: *the fields it requires are
dotted, the fields it forbids are not*. The whole-row negative bound `!{ .a, .b: T }` and the projection lists are unchanged.

This amends RFC-0189 section 1 and one line of RFC-0221's table. It changes spelling only: what a negative entry means, the
error code T0043, and every rule about openness and duplicate labels stay as RFC-0189 states them. This is a design draft.
Nothing here is accepted. Tracked by metel-core#2021.

---

## Motivation

The request comes from the language owner (metel-core#2021). The reasons the draft can give for it, from the current corpus:

1. **`!.x` is two marks in a row.** `!` already says "not", and `.` says "label of a row"; on an entry that excludes a label the
   second mark adds nothing the first does not. `!{ host }` is what the compiler's own diagnostic suggests today
   (`bound the row parameter with \`!{ host }\``), and it already disagrees with the grammar that requires `!{ .host }`.
2. **A forbidden label is not a member of the row.** RFC-0221's rule is that a name is dotted when it is a label *of a row*,
   the way field selection `p.x` is `p` followed by the label `.x`. A negative entry says the row has no such label, so there is
   no row member for the dot to mark.
3. **Reading.** `{ .path: String, !token, .. }` puts the required and the forbidden next to each other with one visible
   difference, the `!`.

These are reasons to prefer the form, not facts about it. The costs are in the sections below, and RFC-0221 decided the opposite
for negative entries on purpose (section 3).

---

## Proposal

### 1. Entries

| Entry | Meaning | Spelling |
|---|---|---|
| `.x` | a field `.x` of any type | unchanged |
| `.x: T` | a field `.x` of type `T` | unchanged |
| `!x` | no field `.x` | was `!.x` |
| `!x: T` | no field `.x` of type `T` (an `.x` of another type is fine) | was `!.x: T` |

`x` after the `!` is a plain identifier that names the label `.x`. The label variable and the numeric label (RFC-0188) have no
plain spelling, so they are the subject of section 4.

### 2. Where a bare name can occur

A negative entry occurs only **inside the braces of a row bound** (`.{ ... }`, `{ ... }`, `Req<..{ ... }>` as a bound). Inside
those braces every entry is a label entry: there is no position at which an aspect name or an expression can stand. So the bare
`!x` does not compete with the negative aspect bounds `R: !Copy` and `R: !Display`, which sit in the bound list *outside* any
row braces, and it does not compete with the expression `!x`, since a row bound is a type, not an expression. The parser needs
no lookahead beyond "inside a row bound's braces".

### 3. Consistency with RFC-0221

RFC-0221 states the rule: *a name is dotted when it is a label of a row, and bare when it is a member a nominal type declares for
itself*, and its table lists the negative entry `{ !.x: T }` among the dotted forms (its answer to RFC-0188's open question 2).
This RFC makes the negative entry a second exception to a rule that has one. Three ways to hold the line:

- **A. Only negated entries drop the dot** (this draft's primary proposal): `.{ .path, !token, .. }`.
- **B. Every entry of a row bound drops the dot**: `{ path, !token, .. }`. It restores the pre-RFC-0221 look inside bounds and
  leaves bound entries different from the record types they bound (`{ .path: String }`), which RFC-0221 set out to make one
  shape.
- **C. Status quo**: `!.token`, keeping RFC-0221's single rule.

The draft proposes A because the request names only the negated entry. A is the least consistent and the shortest; B is the most
consistent with *itself* and the least with RFC-0221; C costs nothing. The choice is open question 1.

### 4. Entries with no bare spelling

RFC-0189 and RFC-0188 give two label forms that are not identifiers:

| Written today | With the dot dropped | Problem |
|---|---|---|
| `!.0` (numeric label, RFC-0151) | `!0` | reads as the boolean not of the number `0` |
| `!.[L]` (label variable, RFC-0188) | `![L]` | `!` followed by an array-shaped `[L]`; `[L]` is also the shape of an array literal and of a capture list |

Inside the braces of a row bound neither is an expression, but a reader meets `!0` and `![L]` in code that also contains the
expression `!x`. Two choices: keep the dot for the forms that are not identifiers (`!.0`, `!.[L]`), so one entry has two spellings
by what the label is; or drop it for all and accept `!0` and `![L]`. Open question 2.

### 5. The whole-row form

`!{ .a, .b: T }` is sugar for `{ !a, !b: T, .. }` after this RFC (it was `{ !.a, !.b: T, .. }`). The labels inside the
negative braces stay dotted: they are the entries of a row literal that is being negated, not negative entries themselves, and
RFC-0225 keeps `!{` as its own contiguous introducer. The sugar then rewrites a dotted label to a bare one. The alternative is
to drop the dots inside `!{ ... }` as well (`!{ a, b: T }`), which restores the pre-RFC-0221 spelling of the whole-row negative
bound; open question 3.

### 6. Migration

The language has no users, so there is no deprecation period: `!.x` and `!.x: T` become a parse error whose message names the
new spelling (`write \`!x\``), and every use in the repository is rewritten in the same change. Uses today: the spec's
row-bounds legality-8 and its neighbours (types chapter), about eight integration fixtures, the text of RFC-0189, RFC-0191,
RFC-0221 and RFC-0225, and the draft RFC-0175. The diagnostic that already prints `!{ host }` needs no change.

---

## Interaction with other work

- **RFC-0189** (implemented): section 1's entry table and every example are amended; sections 2 onward are unaffected.
- **RFC-0221** (implemented): its table row for the negative entry and its Interactions text on negative bounds change; the
  rule in its Summary gains the exception (or, under B, changes).
- **RFC-0225** (implemented): the `!{` introducer is untouched.
- **RFC-0188** (draft, label syntax) and **RFC-0175** (draft, label polymorphism): the label variable `.[L]` and numeric labels
  are the entries section 4 cannot spell plainly.
- **RFC-0229** (draft, single-field projection shorthand, metel-docs#633): both RFCs decide how a label is written after a type
  or a bang. If projections follow row bounds, the two should be settled together.

---

## Alternatives considered

1. **Status quo, `!.label`.** Consistent with RFC-0221; costs the doubled mark.
2. **A keyword (`without token`).** RFC-0189 already rejected it: it adds a reserved word for what `!` says in every other
   bound position.
3. **A different sigil (`-token`, `~token`).** RFC-0189 already rejected these: `-` and `~` are expression operators, `!` is
   the bound grammar's negation.
4. **Both spellings accepted.** Two ways to write one thing, for a language with no users to migrate; rejected.

---

## Open questions

1. **A, B or C (section 3).** Does only the negated entry drop the dot, do all row-bound entries drop it, or does the dot stay?
   A reverses a point RFC-0221 settled on purpose.
2. **Numeric labels and label variables (section 4).** Keep `!.0` and `!.[L]`, or accept `!0` and `![L]`?
3. **The whole-row form (section 5).** Do the labels inside `!{ ... }` keep their dots?
4. **Does the draft's reasoning (Motivation 2) hold?** It says a forbidden label is not a row member, so the dot has nothing to
   mark. A negative entry on an *open* row says "this label stays absent", which is a fact about the row; if that makes the dot
   apt, the argument for the change weakens.
5. **Diagnostics that print an entry.** T0043 messages and bound-printing today show the dotted form; they follow whichever
   spelling this RFC settles.

---

## Implementation notes

- Grammar (`grammar.pest`, the row-bound entry rule: "RFC-0189: an entry may be negative"), parser and AST: a negative entry
  takes an identifier where it took a dotted label; the old form is a parse error with a rewrite hint.
- Rewrite the fixtures and spec text listed in section 6, add a fixture that `!.x` is rejected with the new spelling in the
  message, and keep T0043's behaviour unchanged.
- No type-checker or runtime change: the entry denotes the same label.

---

## Decision

**Outcome:** *(pending)*
