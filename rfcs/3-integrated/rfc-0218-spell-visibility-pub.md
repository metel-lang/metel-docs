---
id: rfc-0218
title: "Spell Visibility pub"
date: '2026-11-06'
status: integrated
updated: '2026-11-07'
tracking: 'https://github.com/metel-lang/metel-core/issues/1837'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1837'
impl_status: not-started
coverage:
  "1": { spec: "spec.modules.visibility.legality-1" }
  "2": { kind: untestable, reason: "The migration plan and sweep policy are process, not language behavior." }
  "3": { kind: blocked, reason: "The worked examples become fixtures of the pub implementation.", ref: "metel-core#1837" }
---

> **Status — draft (2026-11-06).** Decided in direction by the language owner for v0.16.0; the open questions below remain.

> **Status — under review (2026-11-06).** Visibility spelling decided in direction for v0.16.0

> **Status — accepted (2026-11-07).** Reviewed 2026-11-07: every open question resolved (reserved-word parse error for public; one-shot sweep script; blog swept, release notes left; marker spelling moved to RFC-0089 and #1828).

> **Status — integrated (2026-11-07).** Integrated 2026-11-07: spec keyword list and visibility legality-1 state pub; worked examples and sibling cross-check recorded; sweep and implementation tracked in metel-core#1837.

## Summary

The visibility keyword is spelled `pub`. This reverses section 2 of RFC-0098, which renamed `pub` to `public` in July 2026. The other renames of RFC-0098 (`extend` for impl blocks, `var` for `mut`) stay.

```metel
pub struct Token {
    pub value: String,
    secret: i64,
}
pub fun get(t: &Token) -> String { t.value.clone() }
```

The change is a token rename with no semantic effect: module-private by default, `pub` to expose, on every site that takes a visibility today (functions, structs and their fields, records, enums, aspects, type aliases).

---

## Motivation

- **It is written on every exported item.** The corpus and stdlib use `public` on 514 lines across 248 `.mtl` files; every declaration the spec calls exported carries it. Three letters shorter is a small saving paid on every line of a library's surface.
- **It composes with the new prefix keywords.** The settlement (RFC-0206, RFC-0207, RFC-0212) puts contextual keywords in front of the declaration keyword: `copy struct`, `linear struct`, `declared aspect`. With visibility outermost, `pub declared implicit aspect X` and `pub copy struct P` read as one short prefix; `public declared implicit aspect X` is long.
- **The reason for `public` was identity, and it does not hold up.** RFC-0098 chose `public` because Metel "reads as a deliberate identity rather than an accident" where it diverges from Rust at no cost. Its cost is not zero (the line length above), and `pub` is the keyword the rest of the corpus already used before RFC-0098 and the one readers of Rust-family languages know. The identity argument still stands for `aspect`, `extend` and `var`, which are not reversed.

---

## 1. The rule

1. `pub` is the visibility keyword at every site that accepts a visibility today. It is a reserved word.
2. `public` is reserved as the legacy spelling. It stays in the grammar's reserved-word list, so using it is an ordinary parse error, exactly as `pub` is reserved today and as `mut` is reserved since RFC-0098 and `impl` since RFC-0130. **Decided 2026-11-06 (language owner): a hard error**, with no transition warning. **Decided 2026-11-07:** the diagnostic is the existing parse error for a reserved word; a tailored "use `pub`" hint is added only if the parser's error machinery already supports hints for reserved words, and is not part of this RFC's contract.
3. With the prefix keywords of RFC-0206, RFC-0207 and RFC-0212, `pub` is outermost: `pub copy struct P`, `pub declared aspect Validated;`.
4. No semantic change: RFC-0032 (field-level visibility), RFC-0083 (public value exports) and the module visibility rules apply unchanged under the new spelling.

**Grammar.** One rule changes: `pub_kw = @{ "public" ~ ... }` becomes `"pub"`. The reserved-word list swaps `public` for the legacy entry.

## 2. Migration

A sweep, not a blind regex (PROCESS.md, exit criterion of 2026-07-31), done by one one-shot script under `tools/`
(decided 2026-11-07): it works by token context, scopes by code-fence language, preserves line endings (at least one file is
CRLF), and each sweep is verified by compiling at least one complete swept example. There is no permanent `metel fmt` or
`--fix` rewrite: Metel has no users to migrate, and the mechanical rewrite (`public` to `pub`) is safe because the token is
only ever the visibility keyword. Existing programs get the reserved-word parse error of rule 2.

Scope (decided 2026-11-07, language owner):
- **Swept:** the stdlib and the fixture corpus (518 lines in 247 `.mtl` files in metel-core on 2026-11-07), the spec
  (15 keyword uses), the tutorials, the RFCs outside the terminal stages, the architecture reports, and **the blog** (a handful of
  keyword uses in the posts; the English word "public" stays): code samples in them are instructions and not historical
  claims (the metel-core#585 precedent).
- **Left alone (decided 2026-11-07, language owner):** the release notes, including their code samples, which record
  what each release said; released-version documentation snapshots; `5-superseded` and `6-refused` RFCs; ADRs (dated
  decision records); and any prose that *describes the rename itself*.
- **Sequencing across the two repos:** docs CI compiles examples with metel-core's rolling binary, and metel-core's doc
  check compiles the pinned docs. So the grammar, stdlib and fixture change lands in metel-core first; the docs sweep
  is a docs pull request marked `Depends-on: metel-lang/metel-core#N`; and metel-core then bumps the pin to the swept docs
  commit. One sweep per pull request (this one is first, before `:=`, construction calls and dotted labels).

RFC text written during the Copy and Clone settlement already uses `pub` in examples and prose, as the target spelling.

---

## 3. Worked examples (integration, 2026-11-07)

Each combines the rename with an integrated feature or a sibling RFC in flight. They cannot compile until the grammar change
lands, so each becomes a fixture of the implementation (metel-core#1837 and its children). A hit means a contradiction.

```metel
pub struct Token { pub value: String, secret: i64 }     // RFC-0032: field visibility independent of the struct's
struct Hidden { pub n: i64 }                            // a pub field on a private struct is unreachable (legality-1)
pub copy struct Id { pub n: i64 }                       // RFC-0206/0207: pub outermost, then the class keyword
pub declared aspect Validated;                          // RFC-0212: pub outermost on a declaration with a prefix keyword
pub fun get(t: &Token) -> String { t.value.clone() }
```

1. **Identifiers that begin with `pub`.** `publish`, `pub_key` and `pubs` stay identifiers: the keyword rule requires that no
   alphanumeric or `_` follows, as it does for `public` today. `let pub := 1;` and `let public := 1;` are both errors, because
   both are reserved.
2. **The legacy spelling.** `public fun f() {}` is a parse error at `public` (rule 2), and the same source with `pub` compiles.
3. **No visibility on a record field.** A record field cannot be private, so `pub` on one is the same syntax error `public`
   is today (it points at `struct`). With RFC-0221's dotted labels the field is `.x`, and `pub .x` is still rejected.
4. **Public value exports (RFC-0083).** `pub let` stays invalid exactly as `public let` is (the fixture
   `v0_15_0_neg_public_let_is_not_valid`); `pub fun` and `pub struct` are valid.
5. **Sibling RFCs in flight.** RFC-0100 (`Type(args)`) and RFC-0183 (`:=`) add no visibility site; RFC-0221 changes labels
   and not visibility; RFC-0191 and RFC-0189 act on rows. The prefix-keyword order of RFC-0207 and RFC-0212 puts `pub`
   outermost, as rule 3 says.

Exit check: no contradiction with the integrated spec (modules visibility, field-level visibility, public value exports) and
none with the sibling RFCs of the v0.16.0 surface stage. The token is the only change.

---

## Alternatives considered

1. **Keep `public`** (RFC-0098). No migration, no churn. Keeps the identity argument and costs the line length on every item.
2. **Accept both spellings forever.** No migration, but two spellings for one thing; the formatter would have to pick one.
3. **`export`.** A different word, no Rust-family precedent, and the same sweep cost.
4. **Capitalisation** (Go-style). Rejected by RFC-0098 as a larger lexical change.

## Relationship to existing RFCs

- **RFC-0098** — amended: section 2 (`pub` to `public`) is reversed; sections 1 and 3 stand.
- **RFC-0032, RFC-0083** — visibility semantics, unchanged.
- **RFC-0206, RFC-0207, RFC-0212** — the prefix keywords this composes with; their examples already use `pub`.
- **RFC-0101** — naming case conventions; no conflict (`pub` is lowercase).

## Open questions

None blocking.

1. ~~**Hard error or one-minor warning for `public`**~~ **Resolved 2026-11-06.** A hard error.
2. ~~**A rewrite tool.**~~ **Resolved 2026-11-07.** A one-shot sweep script, no permanent `fmt` or `--fix` feature (section 2).
3. ~~**Docs and versioned snapshots.**~~ **Resolved 2026-11-07.** Released-version snapshots keep `public`; the blog is corrected in place;
   the release notes, superseded and refused RFCs, ADRs and prose describing the rename are left (section 2).
4. ~~**Diagnostic for `public`.**~~ **Resolved 2026-11-07.** The reserved-word parse error (rule 2).
5. The spelling of the dismantling-method marker of RFC-0089 (decision D13) moved to RFC-0089 and metel-core#1828 on
   2026-11-07: it is a different feature, effective with the `linear` release, and does not block this RFC. The constraint
   it carries into this RFC is only that the marker must not collide with `pub`.

---

## Decision

**Outcome:** *(pending)*
