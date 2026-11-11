---
id: rfc-0225
title: "Dot-prefixed anonymous records"
date: '2026-11-11'
status: under-review
updated: '2026-11-11'
tracking: 'https://github.com/metel-lang/metel-core/issues/1943'
---

> **Status — under review (2026-11-11).** Language owner requested review and scheduled design settlement; parser prototype remains required before acceptance.

## Summary

An anonymous record starts with `.{`: `.{ .x: i64 }` is a type and
`.{ .x = 0 }` is a value. The prefix also applies to anonymous record patterns,
open record types, row bounds and row equations. Labels keep their leading dots
from RFC-0221. The closing delimiter stays `}`.

```metel
let origin: .{ .x: i64, .y: i64 } := .{ .x = 0, .y = 0 };
let .{ .x, .y } := origin;
fun zero() -> .{ .x: i64 } { .{ .x = 0 } }
```

This is a syntax proposal. Record identity, field typing, ownership, evaluation
order and structural matching keep their existing rules. Nothing here is accepted. Design-settlement tracking is metel-core#1943; its
milestone is the source of truth for scheduling. The implementation and normative
specification are unchanged.

## Motivation

RFC-0221 gives row labels one spelling and makes nonempty dotted-field records
recognisable. It deliberately keeps bare braces as the outer delimiters, including
the context-dependent reading of `{}`. A reader must still distinguish record
braces from function bodies and blocks, especially in a return type followed by
a body, nested records, and empty records.

A leading dot marks the entire anonymous record, even when it has no fields:

```metel
fun empty() -> .{} { .{} }
fun nested() -> .{ .point: .{ .x: i64 } } {
    .{ .point = .{ .x = 0 } }
}
```

The field dot identifies a label; the opening dot identifies an anonymous record.
These are separate roles. This proposal accepts the extra character to make the
outer form explicit everywhere.

## Proposal

### 1. One opening delimiter

Use the contiguous delimiter `.{` wherever the current grammar introduces an
anonymous record shape. Whitespace and comments may follow the delimiter; they
may not separate its dot and opening brace. Trailing commas keep their current
rules. There is no expected-type inference implied by the prefix: the fields
still determine an anonymous structural record, rather than a nominal constructor.

| Position | Proposed spelling |
|---|---|
| Closed type | `.{ .x: i64 }` |
| Open type | `.{ .x: i64, ..R }` |
| Tail-only type | `.{ ..R }` |
| Value | `.{ .x = 0 }` |
| Punned value | `.{ .x }` |
| Spread and update | `.{ ..p, .x = 1 }` |
| Pattern | `let .{ .x, ..rest } := p;` |
| Empty type or value | `.{}` |
| Row bound | `record R: .{ .x: i64, .. }` |
| Negative row entry | `record R: .{ !.token, .. }` |
| Whole-row negative bound | `record R: !.{ .token: i64, .. }` |
| Row equation | `where R = .{ .x: i64, ..Rest }` |
| Anonymous structural impl target | `extend<record R> .{ ..R }: Aspect ...` |

Only forms already allowed at each site remain allowed. In particular this RFC
adds neither empty patterns nor new spread, row-bound or impl capabilities.
A dot is required even for an empty, tail-only or spread-only form.

Named declarations and nominal patterns keep their brace bodies, for example
`struct Point { x: i64 }` and `Point { x }`. Named construction remains a call,
`Point(x = 0)` or `Point(..p)` (RFC-0100). Field selection remains `p.x`.

### 2. Blocks and empty records

Bare braces no longer introduce anonymous records in any position. `{}` denotes
an empty block wherever a block is permitted; it is an error where neither a
block nor another brace construct is permitted. It never falls back to an empty
record. A block returning an empty record is `{ .{} }`.

Function and closure bodies still require blocks. The prefix does not introduce
expression-bodied declarations or closures:

```metel
fun zero() -> .{ .x: i64 } { .{ .x = 0 } }
let make := |x: i64| { .{ .x = x } };
```

Where an expression arm is already permitted, a record needs no parentheses:
`if (flag) .{ .x = 1 } else .{ .x = 0 }`. A match arm may likewise return
`.{ .x = 0 }` directly. A function body written `fun f() -> .{} .{}` is rejected
because its body is not a block.

`.{}` denotes the existing empty-record type or value; `()` keeps its existing unit semantics. This RFC does not identify unit
with the empty record. RFC-0151's proposed identification remains a separate
question, and is not needed to distinguish their syntax from blocks.

### 3. Grammar and adjacent dot forms

The intended grammar change is to replace the opening `"{"` with `".{"` in
`RecordLiteral`, `RecordPattern`, `RecordType`, `OpenRecordType` and `RowBound`.
Row equations and structural impl targets consume those productions. Their entry
and closing-delimiter productions stay the same. The grammar source, rather than
hand-edited generated grammar documentation, is changed at implementation time.

**Projections keep their existing spelling:** `Handle.{ .fd, ..R }` and
`value.{ .fd }`. A projection has a preceding type or value path; an anonymous
record has none. `Handle..{ ... }` is not introduced. Both constructs list row
labels, but this RFC does not change projection eligibility or residual semantics.

**Literal-row arguments keep `..{ ... }`.** Write
`Req<..{ .x: i64, ..R }>` and `Req<..{}>` as today. `..R` is also unchanged.
The row introducer already identifies a literal row, so it does not acquire the
anonymous-record dot. `..{` is the literal-row introducer in row-argument
position; it is not defined by concatenating `..` with the new `.{` opener.

The grammar must therefore factor the brace contents out of `RecordType` and
`OpenRecordType`: anonymous record types use `".{" RecordTypeBody "}"`, while
literal-row arguments use `"..{" RecordTypeBody "}"`. Here `RecordTypeBody`
stands for the existing closed/open field-and-tail alternatives, with their
current legality rules. This preserves the same row meaning without giving
ordinary record types a bare-brace alias. The introducer is contiguous, just as
`.{` is. Neither `Req<.. .{ .x: i64 }>` nor `Req<...{ .x: i64 }>` is introduced
as an alternative spelling.

RFC-0099's proposed `parser.{Ast, Token}` is a path-headed import group in
import/export grammar, not a headless record. It stays a proposal independent of
this RFC. These distinctions must be confirmed by a parser prototype; this RFC
does not claim they have already been tested.

### 4. Diagnostics and compatibility

The change uses a single breaking cutover after a parser-based migration tool
is available. There is no temporary compatibility window or permanent bare-brace
alias. Old
`{ .x = 0 }`, `{ .x: i64 }`, `{ ..R }` and anonymous record patterns are rejected
at their respective record sites. Where the parser recognises an old record form,
it should suggest inserting `.` immediately before `{`. Ordinary block errors
must not be misreported as missing record prefixes.

Empty braces require special migration care: an old `{}` record value may become
a valid block returning unit, so a parse error cannot reliably catch every missed
site. Migration must classify it using the old grammar and AST before the grammar
switch. No new semantic error code is proposed; diagnostic coverage must establish
whether the existing parser-error machinery can provide the targeted suggestion.

## Interactions and prior decisions

- **RFC-0221:** retains dotted labels and revisits only the outer delimiter.
  Its alternatives table rejects the Zig-style `.{ .x = 1 }` as heavier and as
  clashing with row splices and dot paths. This draft accepts the verbosity cost
  and preserves the dedicated literal-row introducer described in section 3.
  Acceptance requires the prototype to demonstrate that the forms coexist; the objection cannot
  simply be deleted without evidence.
- **RFC-0187 (refused):** proposed `{| ... |}` to separate records from blocks.
  This RFC revisits that goal with a different opener while retaining RFC-0221's
  labels. It does not reopen RFC-0187 or change its historical refusal.
- **RFC-0183:** assignment remains a statement, `:=` remains initialization-only,
  and record values retain `=`. Removing delimiter ambiguity is not a reason to
  reintroduce assignment expressions.
- **RFC-0180 / RFC-0186:** `record R`, `..R`, field-wise bounds and literal-row
  arguments keep their meaning; only the anonymous record operand changes.
- **RFC-0189 / RFC-0191:** negative row bounds and record updates use the new
  opener, including `!.{ ... }` and `.{ ..p, .x = e }`.
- **RFC-0151:** numeric labels retain `.0`, for example `.{ .0 = a, .1 = b }`.
  Tuple-to-row equivalence and unit-to-empty-record equivalence remain undecided
  by this RFC.
- **RFC-0188 / RFC-0175 / RFC-0216:** proposed computed labels would live inside
  the same opener, `.{ .[label] = value }`. This example does not accept or
  implement computed labels.

These are proposed amendments on acceptance. The normative spec and other RFCs'
current rules remain in force while this document is a draft.

## Alternatives considered

1. **Keep `{ .x = 0 }`.** Lowest migration cost; dotted labels already disambiguate
   common nonempty forms. Leaves empty records dependent on position and leaves
   record types visually close to bodies. This is the current design.
2. **Prefix values and types only.** Matches the two primary examples but leaves
   patterns and constraints spelling the same anonymous shape differently. The
   agreed scope uses a consistent prefix at all anonymous record sites.
3. **Use `{| ... |}` or `#{ ... }`.** Distinct delimiters without dot composition;
   introduces another delimiter or sigil, and `{| ... |}` was RFC-0187's proposal.
4. **Drop the field dots once the opener is dotted.** Shorter, but reverses the
   label-unification decision of RFC-0221. Outside this proposal's scope.
5. **Accept both forms indefinitely.** Avoids a forced migration, but preserves
   the context-sensitive empty record and gives every anonymous record two forms.

## Migration and implementation plan

Before accepting, build a parser prototype and inventory affected sites. Before
switching grammars, implement a migration against the old parser that inserts a
single dot at each anonymous record opening delimiter, including patterns and
empty records. The tool must preserve comments, strings and line endings,
recognise nested sites, and leave blocks, nominal declaration/pattern braces,
projection lists and literal-row arguments (`..{ ... }`) untouched. Run it a
second time to verify that it makes no additional edits. The migration tool must
be available before the single grammar cutover; old anonymous record forms are
rejected from that cutover onward.

On implementation, migrate stdlib and fixtures together with the grammar. Update
spec rules, tutorials, quickstart, checked blog examples and active RFC worked
examples in their owning repositories, including relevant internal reports under
the syntax-sweep policy. Preserve historical release notes, released snapshots,
superseded/refused proposals and prose intentionally quoting the old spelling.
Land public docs in `metel-docs`, then update core's docs pin through the normal
workflow. The changelog explains the breaking change and migration command when
implementation lands, rather than describing this draft as shipped.

Design settlement is tracked by metel-core#1943; release assignment lives in
that issue's milestone. Implementation may begin only after acceptance, spec
integration and an implementation tracking issue.

## Acceptance and verification

The parser prototype and later regression fixtures must cover:

- Closed, open, empty, tail-only and nested types; values with explicit fields,
  puns, numeric labels, spreads and updates; existing pattern forms and rests.
- Positive and negative row bounds, row equations, anonymous impl targets, and
  empty/nonempty literal-row arguments in the retained `..{ ... }` spelling;
  rejection of `.. .{ ... }` and `...{ ... }` as row arguments.
- Record return values in function/closure blocks and expression arms; empty
  blocks and unit; rejection of a record where a body block is required.
- Projection forms, field selection, nominal constructors and patterns, floats,
  ranges and existing dot syntax, including rejection of `. { ... }`.
- Rejection of old anonymous record forms and targeted migration suggestions;
  old `{}` record sites correctly classified before rewriting.
- A migration corpus with blocks and records in the same source, strings and
  comments containing brace examples, nested records and existing projections.
  Compare program results before/after migration and compile the migrated docs.

The all-sites scope and single-cutover migration policy were agreed by the
language owner on 2026-11-11. Acceptance still requires prototype evidence
resolving RFC-0221's row-splice/dot-path objection. Parser compatibility remains
unverified; agreement on the design does not supply that evidence.

## Costs and remaining verification

The prefix adds a character to every anonymous record. Literal-row arguments
keep their spelling, at the cost of a dedicated grammar production rather than
pure composition of `..` and an anonymous record type. Migrating immediately after the dotted-label
change would require another syntax sweep. These costs must be weighed against
uniform empty-record syntax and clearer separation from blocks.

No design question remains open in this draft. The remaining prerequisite is a
parser prototype verifying the dedicated `..{ ... }` row-literal production
alongside `.{ ... }` record types and the other cases listed above.

## References

RFC-0116 (anonymous records), RFC-0121 (open rows), RFC-0123 (field-wise row
constraints), RFC-0187 (refused record delimiters), RFC-0221 (dotted row labels),
RFC-0180 (literal-row arguments), RFC-0186 (record parameters and row operator),
RFC-0099 (proposed dot paths), RFC-0100 (construction calls), RFC-0183
(initialization-only walrus), RFC-0189 (negative row bounds), RFC-0191 (record
update), RFC-0151 (proposed tuples as rows), RFC-0188 (label syntax), RFC-0175
(label polymorphism) and RFC-0216 (computed row construction).

## Decision

**Design decisions agreed by the language owner (2026-11-11):**

- Use `.{ ... }` for anonymous record values, types, patterns, open types, row
  bounds and row equations, including empty and tail-only forms.
- Keep `..{ ... }` for literal-row arguments, `..R` for row parameters, and
  `T.{ ... }` / `value.{ ... }` for existing projections.
- Make a single breaking cutover, with a parser-based migration tool available
  first; provide targeted errors for old forms and no compatibility window.
- Keep empty-record and unit semantics separate under the current rules, and
  keep function and closure bodies as blocks.

**Lifecycle outcome:** Under review, tracked by metel-core#1943, pending
parser-prototype evidence and formal acceptance. These decisions do not transition the RFC or authorise implementation
before spec integration.
