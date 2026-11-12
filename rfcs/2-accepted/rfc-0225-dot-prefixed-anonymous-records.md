---
id: rfc-0225
title: "Dot-prefixed anonymous records"
date: '2026-11-11'
status: accepted
updated: '2026-11-12'
tracking: 'https://github.com/metel-lang/metel-core/issues/1943'
---

> **Status — under review (2026-11-11).** Language owner requested review and scheduled design settlement; parser prototype remains required before acceptance.

> **Status — accepted (2026-11-12).** Accepted by the language owner after parser-prototype evidence (21 fixtures, migrated corpus passes, RFC-0221's objection answered) and an adversarial review whose findings were fixed

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
| Whole-row negative bound | `record R: !{ .token: i64 }` |
| Row equation | `where R = .{ .x: i64, ..Rest }` |
| Anonymous structural impl target | `extend<record R> .{ ..R }: Aspect ...` |

Only forms already allowed at each site remain allowed. In particular this RFC
adds neither empty patterns nor new spread, row-bound or impl capabilities.
A dot is required even for an empty, tail-only or spread-only anonymous record
form. Whole-row negative bounds retain their dedicated `!{ ... }` introducer
(section 3), just as literal-row arguments retain `..{ ... }`.

Named declarations and nominal patterns keep their brace bodies, for example
`struct Point { x: i64 }` and `Point { x }`. Nominal construction is separate: the RFC-0100 rollback (#1945) restores
`Point { x = 0 }`; RFC-0100 proposes `new Point(...)` and inferred `.(...)`.
This RFC changes neither nominal construction policy nor field selection `p.x`.

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

**Whole-row negative bounds keep `!{ ... }`.** Write
`record R: !{ .token: i64 }`, not `record R: !.{ .token: i64 }`. (A negative bound takes no trailing `..`;
RFC-0189 reserves that spelling and this RFC does not change it.)
The `!{` introducer identifies a negative row bound in bound position; it does
not compose a general negation operator with an anonymous record type. Preserve
RFC-0189's existing expansion into per-entry negative bounds, including its
legality rules. This changes no negative-bound semantics and introduces no
general-purpose record-negation operator. Labels inside remain dotted, and mixed
positive/negative entry bounds retain `record R: .{ .x: i64, !.token, .. }`.

The grammar must recognise whole-row negative bounds with their own `!{`
introducer and the existing row-bound body, rather than requiring `!` followed by
the new positive `.{` production. Like `.{` and `..{`, the introducer is
contiguous. `!.{ ... }` is not an alternative spelling. The parser prototype
must verify this bound-specific production and unchanged per-entry expansion.

RFC-0099's proposed `parser.{Ast, Token}` is a path-headed import group in
import/export grammar, not a headless record. It stays a proposal independent of
this RFC. These distinctions must be confirmed by a parser prototype; this RFC
does not claim they have already been tested.

### 4. Diagnostics and compatibility

The change uses a single breaking cutover after a parser-based migration tool
is available. There is no temporary compatibility window or permanent bare-brace
alias. Old
`{ .x = 0 }`, `{ .x: i64 }`, `{ ..R }` and anonymous record patterns are rejected
at their respective record sites. Where the parser fails at a bare `{` followed by a dotted label
(`{ .x = 0 }`, `{ .x: i64 }`, `{ ..R }`, `{ !.token }`), it names the old record form and suggests inserting `.`
immediately before `{`. Where the failure follows a spaced `!` or `..` introducer it names the gap instead (`!{` and
`..{` are contiguous), never a missing dot, which would produce the forbidden `!.{`. Ordinary block errors are not
misreported as missing record prefixes. Type displays and fix-it hints in diagnostics print anonymous records in
the new spelling (`.{ .x: i64 }`, with dotted labels), so that no message teaches a form that no longer parses.

`{}` is classified by the old grammar, not guessed. In the old grammar a block is the body of a function,
closure, `if`, `while`, `for` or `match` arm, and an expression position tries a record literal first; a `{}` in
the first group stays a block and a `{}` in an expression position was a record. After the switch an expression-
position `{}` is a parse error (the grammar has no general block expression), so a missed record site is caught,
and the prototype review found no old empty-record site that silently becomes a unit block. The migration
still classifies each `{}` from the old parse tree before the grammar switch. No new semantic error code is proposed; diagnostic coverage must establish
whether the existing parser-error machinery can provide the targeted suggestion.

## Interactions and prior decisions

- **RFC-0100 (under review):** proposed inferred nominal construction uses
  `.(...)`, so `.{ ... }` remains structural regardless of expected type.
  Whole-row literal constructor arguments use `..{ .x = 1 }`, retaining the
  dedicated `..{` introducer rather than composing `..` with `.{`. This is value
  argument syntax, distinct by context from the existing `..{ .x: i64 }` type
  argument. RFC-0226 was superseded when its proposal was consolidated into RFC-0100.


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
- **RFC-0189 / RFC-0191:** whole-row negative bounds keep `!{ ... }` and their
  existing per-entry expansion; mixed entry bounds use `.{ ... }` and keep
  `!.label` entries. Record updates use `.{ ..p, .x = e }`.
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
empty records. The tool must preserve comments, strings, non-ASCII text and line endings
byte for byte, recognise nested sites (including records inside string interpolations, through the compiler's
unescaping with an offset map back to the source), and leave blocks, nominal declaration/pattern braces,
projection lists, literal-row arguments (`..{ ... }`) and whole-row negative
bound introducers (`!{ ... }`) untouched except for whitespace between an introducer's tokens, which it removes.
A comment in that gap, an interpolation it cannot map, or an ordinary Rust string that holds an old record is not
guessed at: the tool reports it as needing manual migration, writes nothing for that file, and exits non-zero.
Nested anonymous record types inside those forms still gain their own prefix. Supported containers are `.mtl`
files, column-0 ```` ```metel ```` fences in Markdown and MDX, and Rust raw strings; other containers that hold
Metel are reported, not skipped silently. The tool runs under the old grammar and is one-shot: a rerun on migrated
sources reports them as unparseable and exits non-zero, and the check that no old site remains is the new parser's
rejection of old forms over the whole corpus. The migration tool must
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
- Positive row bounds, mixed negative entries, whole-row `!{ ... }` bounds
  (with unchanged expansion and rejection of `!.{ ... }`), row equations,
  anonymous impl targets, and
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
and whole-row negative bounds keep their spelling, at the cost of dedicated
grammar productions rather than pure operator composition. Migrating immediately after the dotted-label
change would require another syntax sweep. Specific readability costs: `.{}` adds a character where the position already
made an empty record unambiguous, `.{ ..p }` combines two different uses of the dot, and `Req<..{ .x: i64 }>` keeps
the longer introducer. These costs must be weighed against
uniform empty-record syntax and clearer separation from blocks.

## Prototype result (2026-11-12)

A parser prototype (metel-core branch `proto/rfc-0225-parser`; reference, not for merge) changes six grammar productions
(`record_lit`, `record_pattern`, `record_type`, `open_record_type`, `row_bound`, plus the dedicated `row_literal`
and `neg_row_bound`), about 40 lines of parser code, and adds the parser-driven migration tool
(`examples/record_prefix_migrate.rs`, run under the old grammar).

**Inventory (metel-core, 2026-11-12).** 2094 `.mtl` files scanned: 349 contain anonymous-record sites (1231 sites);
40 are parse-negative fixtures the tool cannot parse (3 hold an old record and were migrated by hand). Rust raw
strings: 3 files, 195 sites; 2 ordinary Rust strings were migrated by hand. metel-docs: 32 Markdown files, 281
fenced sites (spec, tutorials and active RFC examples).

**Results.** After migrating the corpus with the tool: `metel` integration 1902 passed (1881 migrated fixtures, which
are the same programs with the same expected results, plus 21 new `rfc0225_*` fixtures), unit 97 passed,
frontend 468 passed, 0 failed. The fixtures cover each form in the acceptance list: closed, open, empty, tail-only
and nested types; values, puns, numeric labels, spreads and updates; patterns; positive, mixed and whole-row
negative bounds; row equations; literal-row arguments; records in function bodies, closures and expression arms;
rejection of `.. .{`, `...{`, `. {`, `!.{`, a spaced `!` or `..` introducer, `{}` as a record value and every old brace form,
each with the targeted message; and one program in which a projection `p.{ .x }`, `.{ .x = 1 }`, `..{` and `!{`
coexist.

**RFC-0221's objection.** The Zig-style `.{` was rejected there as clashing with row splices and dot paths. In the
prototype the four forms are four distinct tokens (`.{`, `..{`, `!{` and a projection's `.{` after a path); an
anonymous record never follows an expression, and a projection always has a path before it. No program parsed
ambiguously, and no old program was reinterpreted instead of rejected. The objection does not hold.

**Adversarial review (Codex, read-only, 2026-11-12) and its outcome.** Findings that blocked acceptance were fixed
in the prototype and this text: the migration tool corrupted non-ASCII text in Rust files, deleted comments between
`..` and `{`, left a spaced or commented `!` `{` unmigrated, and silently skipped interpolations containing escapes;
`parse_row_bound` read openness from the bound's source text, so a comment containing `..` changed typing (now read from the tree);
and this RFC's own whole-row negative examples carried a forbidden trailing `..`. Each now has a fixture or a tool
check; the tool reports what it cannot migrate and exits non-zero instead of guessing.

**Not covered by the prototype.** Display of types and the fix-it hints in diagnostics still print the old spelling
(decided by the language owner to change with the implementation); the metel-docs sweep and `check-examples`
run; the metel-lsp formatter and highlighting; the changelog and migration command text.

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
- Keep `!{ ... }` for whole-row negative bounds with their existing per-entry
  expansion; keep `!.label` for negative entries inside a `.{ ... }` bound.
- Keep `..{ ... }` for literal-row arguments, `..R` for row parameters, and
  `T.{ ... }` / `value.{ ... }` for existing projections.
- Make a single breaking cutover, with a parser-based migration tool available
  first; provide targeted errors for old forms and no compatibility window.
- Keep empty-record and unit semantics separate under the current rules, and
  keep function and closure bodies as blocks.

**Lifecycle outcome:** Accepted 2026-11-12, tracked by metel-core#1943, on the parser-prototype evidence above.
Implementation begins only after spec integration and an implementation tracking issue (PROCESS.md).
