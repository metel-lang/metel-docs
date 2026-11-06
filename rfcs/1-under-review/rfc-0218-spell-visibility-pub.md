---
id: rfc-0218
title: "Spell Visibility pub"
date: '2026-11-06'
status: under-review
updated: '2026-11-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1837'
---

> **Status — draft (2026-11-06).** Decided in direction by the language owner for v0.16.0; the open questions below remain.

> **Status — under review (2026-11-06).** Visibility spelling decided in direction for v0.16.0

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
- **It composes with the new prefix keywords.** The settlement (RFC-0206, RFC-0207, RFC-0212) puts contextual keywords in front of the declaration keyword: `copy struct`, `affine struct`, `declared aspect`. With visibility outermost, `pub declared implicit aspect X` and `pub copy struct P` read as one short prefix; `public declared implicit aspect X` is long.
- **The reason for `public` was identity, and it does not hold up.** RFC-0098 chose `public` because Metel "reads as a deliberate identity rather than an accident" where it diverges from Rust at no cost. Its cost is not zero (the line length above), and `pub` is the keyword the rest of the corpus already used before RFC-0098 and the one readers of Rust-family languages know. The identity argument still stands for `aspect`, `extend` and `var`, which are not reversed.

---

## 1. The rule

1. `pub` is the visibility keyword at every site that accepts a visibility today. It is a reserved word.
2. `public` is reserved as the legacy spelling: using it is an error with a fix-it that replaces it with `pub`, the way `pub` is reserved today with a clear error (RFC-0098, RFC-0130). **Decided 2026-11-06 (language owner): a hard error**, as in RFC-0098, with no transition warning.
3. With the prefix keywords of RFC-0206, RFC-0207 and RFC-0212, `pub` is outermost: `pub copy struct P`, `pub declared aspect Validated;`.
4. No semantic change: RFC-0032 (field-level visibility), RFC-0083 (public value exports) and the module visibility rules apply unchanged under the new spelling.

**Grammar.** One rule changes: `pub_kw = @{ "public" ~ ... }` becomes `"pub"`. The reserved-word list swaps `public` for the legacy entry.

## 2. Migration

A sweep, not a blind regex (PROCESS.md, exit criterion of 2026-07-31): stdlib, the fixture corpus (248 files), the spec and docs, RFCs, the blog and reports, scoped by code-fence language, verified by compiling at least one complete swept example. Superseded and refused RFCs and dated records are left alone. Existing user programs get the hard fix-it error; a mechanical rewrite (`public` to `pub`) is safe because the token is only ever the visibility keyword.

RFC text written during the Copy and Clone settlement already uses `pub` in examples and prose, as the target spelling.

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

1. **Hard error or one-minor warning for `public`: resolved 2026-11-06.** A hard error with a fix-it, as RFC-0098 did.
2. **A rewrite tool.** Whether `metel fmt` or a dedicated `--fix` applies the rename, or only the diagnostic's fix-it does.
3. **Docs and versioned snapshots.** Whether versioned documentation of released versions keeps `public`.

---

## Decision

**Outcome:** *(pending)*
