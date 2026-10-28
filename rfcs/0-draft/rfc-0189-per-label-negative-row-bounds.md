---
id: rfc-0189
title: "Per-Label Negative Row Bounds"
date: '2026-10-28'
status: draft
---

## Summary

A row bound may carry **negative entries**: a label written with a leading `!`, in the same
braces as the positive ones.

```metel
fun route<record R: { path: String, !token, !session: u64, .. }>(r: R) -> String { r.path }
//                    has a String `path`  ^        ^ no `token`   ^ no u64 `session`
```

An entry is one of four forms:

| entry | holds when the record has |
|---|---|
| `x` | a field `x`, of any type |
| `x: T` | a field `x` of type `T` |
| `!x` | no field `x`, of any type |
| `!x: T` | no field `x` of type `T` (an `x` of another type is fine) |

The existing whole-row form `!{ a, b: T }` (RFC-0118 §2) is kept and is defined as sugar for
`{ !a, !b: T, .. }`. Nothing already written changes meaning; the change is additive.

This amends RFC-0118 (row bounds, implemented). It does not touch RFC-0186's `..R`, RFC-0123's
field-wise bounds, or the semantics of negative *aspect* bounds (RFC-0072).

---

## Motivation

A row bound today is positive or negative as a **whole**. `{ x: f64, .. }` says what a record
must carry; `!{ token }` says what it must not. They are different bounds, so a function that
needs both has to write two:

```metel
fun route<record R: { path: String, .. } + !{ token }>(r: R) -> String { r.path }
```

This works (checked against the current build: a record with `token` is rejected with `T0012`,
one without is accepted), so mixed constraints are *expressible* now. What is missing is
locality and a place to put a per-label negative:

- **The fields a record must and must not have are one question** ("what shape is `R`?"), but
  the bound splits it over two braces joined by `+`, and a reader has to merge them to see the
  shape.
- **Each additional negative is a separate decision about the same row.** `+ !{ token } +
  !{ session }` reads as three bounds; `{ …, !token, !session, .. }` reads as one row.
- **Tail extension needs exactly this combination.** Adding a field to a record that is
  generic in its rest requires the rest to be provably free of that label (`R: !{ host }`,
  spec, *Row arguments*), usually next to other requirements on the same `R`:
  ```metel
  fun add_host<record R: { token, !host, .. }>(r: Req<..R>, h: String) -> Req<..{ host: String, ..R }>
  ```
- **Row-conditional impls (RFC-0121 §3) are disjoint exactly when some label is present in one
  and absent in the other.** `extend<record R: { name, !id, .. }>` and `extend<record R: { name,
  id, .. }>` can be seen to be disjoint from the entries themselves, in one row each.

---

## 1. Entries

A row bound is a comma-separated list of entries, optionally followed by `..`:

```
row_bound = { "{" ~ (row_entry ~ ("," ~ row_entry)*)? ~ ("," ~ "..")? ~ ","? ~ "}" }
row_entry = { bang? ~ ident ~ (":" ~ type_expr)? }
```

(`bang?` is the only change; `{ .. }` alone still does not parse, so `<record T>` remains the one
spelling of "any record".) After `{` or `,` a `!` can only begin a negative entry, so the grammar
stays unambiguous with the bound-level `!` (`T: !{ … }`), which precedes the brace.

The row holds when **every** entry holds. Positive entries behave exactly as in RFC-0118 §1–2a.
`!x: T` is the per-entry complement already specified for `!{ x: T }`: it is satisfied by a
record whose `x` is not a `T`, and `!x` is the form that rejects the label outright.

### Openness

**A row containing a negative entry must be open: it ends in `..`.** A closed bound already
excludes every label it does not list, so a negative entry in it states nothing and is an error
with a fix-it ("add `..`, or drop the entry"). With the trailing `..` the row says "these fields,
not these ones, and anything else".

```metel
fun a<record R: { x: f64, !token, .. }>(r: R)   // ok
fun b<record R: { x: f64, !token }>(r: R)       // error: closed row; `!token` is redundant
fun c<record R: { !token, .. }>(r: R)           // ok: only a negative entry, still open
```

The sugar form needs no `..` because `!{ … }` is open by definition: it is the complement per
entry, never a closed shape (RFC-0118 §2).

### The same label more than once

A label may appear **once positively** and **any number of times negatively**:

```metel
{ x, !x: u8, .. }             // an `x` that is not a u8 (any other type)
{ !x: u8, !x: u16, .. }       // no u8 `x` and no u16 `x`
```

It is an error if the entries cannot all hold: `{ x, !x }`, and `{ x: T, !x: T }`. Two positive
entries for one label stay a duplicate-field error. `{ x: f64, !x: u8 }` is satisfiable, merely
redundant, and is accepted without diagnostics.

### Where it may be written

Wherever a row bound is accepted: at the parameter (`<record R: { … }>`), in a `where`
constraint (`where record R: { … }`), and combined with aspect bounds (`record R: Show + { x,
!y, .. }`). Negative entries are part of the *bound* only; they do not appear in record types,
literals or patterns.

---

## 2. Interaction

- **Sugar, not replacement.** `!{ a, b }` ≡ `{ !a, !b, .. }`. Neither is deprecated. The prefix
  form stays the short spelling when the whole bound is "none of these".
- **Coherence (RFC-0060, RFC-0121 §3).** Two row-conditional impls are disjoint when some label
  has contradictory entries across them (`x` against `!x`, or `x: T` against `!x: T`). A typed
  negative alone proves nothing against a positive entry of another type (`!x: T` and `x: U`
  overlap). No new coherence rule; the existing rule now reads entries instead of whole bounds.
- **Delimiters and labels.** Row bounds are written with whichever delimiter RFC-0187 settles on
  for records; entries use whatever label spelling RFC-0188 settles on. Examples here use `{ … }`
  and plain identifiers.
- **Field-wise bounds (RFC-0123, RFC-0186).** `..R: A` is a constraint on the members of a
  record parameter and is unaffected.

---

## Alternatives Considered

- **Keep `+` (status quo).** Works today (see Motivation). Rejected as the end state only
  because it cannot hold a per-label typed negative next to its positive and splits one shape
  over several bounds. It stays legal.
- **A keyword (`without token`).** Adds a reserved word to say what `!` already says in every
  other bound position (`!Copy`, `!{ … }`).
- **A different sigil on the label (`-token`, `~token`).** `-` and `~` are operators in
  expressions; `!` is already the bound grammar's negation.

---

## Open Questions

1. **May an outer negative row bound contain negative entries (`!{ !a, b }`)?** Under the
   per-entry complement, `!{ e1, e2 }` holds when *no* entry holds, so `!{ !a }` would hold when
   `a` is **present**, and `!{ !a, b }` means "has `a`, lacks `b`". That is coherent but is
   `{ a, !b, .. }` written backwards. **Leaning: reject it** with a diagnostic pointing at the
   positive spelling. The outer `!` keeps one meaning, "none of these labels", and a double
   negation is never the clearest way to say a row's shape.

2. **May a negative entry carry a type (`!x: T`)?** The outer form already allows it
   (`!{ id: String }`), so removing it from the entry form would make the two spellings differ.
   The cost is that it reads like "x is not T" yet is satisfied by a record with no `x`, and
   by one whose `x` is another type; the spec already warns about this. **Leaning: allow**, for
   parity with the shipped form, with the same documented reading. It is the only way to say
   "`x`, but not this type" (`{ x, !x: u8, .. }`).

3. **Several typed negatives for one label: repeated entries, or a list?**
   - **A. Repeat the entry:** `{ !x: u8, !x: u16, .. }`. No new syntax; falls out of §1 since
     negatives conjoin. Verbose beyond two or three types.
   - **B. One negative over a union:** `!x: u8 | u16`, read as "no `x` that is a `u8` or a
     `u16`", the same meaning as A by De Morgan. Needs structural unions in type position
     (RFC-0165, `1-under-review`, unscheduled).
   - **C. A mixed-polarity list in the type position:** `x: !u8, u16, !u32`. **Not
     recommended.** The comma is already the entry separator, so `{ x: u8, u16 }` is an entry `x: u8`
     followed by a label-only entry `u16`; a type list would need a second separator and a
     rule for the ambiguity. And a positive list member (`u16`) is a *disjunction* ("`x` is
     `u16`"), a feature of its own, which makes the negatives next to it redundant (an `x` that
     is a `u16` is already neither a `u8` nor a `u32`).

   **Leaning: A now; B when unions exist, as sugar for A; not C.** Nothing is lost by shipping
   A first, since B only abbreviates it.

---

## Changes on Acceptance

- `reference/spec/types.md`, *Row bounds*: the entry table, the openness rule, and the
  repeated-label rule, with rigor blocks and fixtures.
- Grammar: `row_entry` takes an optional `!`; `row_field` is renamed accordingly.
- Diagnostics: closed row with a negative entry; contradictory entries for one label;
  negative entry inside an outer `!{ }` (if Open Question 1 is settled as above).
- RFC-0118 gains an amendment note pointing here.

## References

- RFC-0118 (Row Bounds, `4-implemented`) §2, §2a: the per-entry complement and label-only
  entries this builds on.
- RFC-0121 (Open Rows) §3: row-conditional impl resolution, where entry-level disjointness is used.
- RFC-0186 (Rows as an Operator on Record Parameters): `record R` and `..R`; the tail-extension
  example uses both.
- RFC-0072 (Negative Bounds): the `!Aspect` form, whose `!` this reuses.
- RFC-0165 (Structural Union Types): needed only for Open Question 3, option B.
- RFC-0187, RFC-0188: record delimiters and label spelling, independent of this RFC.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
