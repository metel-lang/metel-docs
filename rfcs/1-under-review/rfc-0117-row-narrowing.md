---
id: rfc-0117
title: "Row Narrowing"
date: '2026-07-24'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/789'
target:
updated: '2026-08-23'
---

> **Extracted from RFC-0090 on 2026-07-24** (superseded; see RFC-0116's header for why the
> split happened and what the six pieces are).
>
> **Depends on RFC-0116 (Anonymous Record Types) and on RFC-0071 (Ownership and Move
> Semantics).** RFC-0071 is `2-accepted` but **0% implemented** — confirmed by direct grep
> of the interpreter for borrow/move-tracking infrastructure. That is a sequencing
> dependency on already-accepted work, not a ratification blocker on a draft, but it is
> the reason this is a separate RFC from RFC-0116 rather than bundled with it: the
> type-former is buildable today and this is not.

> **Status — under review (2026-08-23).** Committed to v0.13.0, tracking issue #789 filed 2026-08-22 -- real dependency-chain engagement, not a calendar promotion

## Summary

Moving a field out of a record narrows the record's type to exactly the fields that
remain. `{ fd: i64, path: String }` with `path` moved out becomes `{ fd: i64 }` — not a
partially-valid value, not an opaque "moved-from" marker, but an ordinary value of a
narrower record type.

No row variables and no unification are involved. For a closed record over *N* fields the
space of possible residuals is the subset lattice, bounded by 2^*N* and trivial at
realistic struct sizes.

---

## Motivation

Without narrowing, a record is a product type you can build and read but never partially
consume, and the natural pattern of "take one field out, keep using the rest" has no
expression. Rust's answer is to track partial moves as compiler-internal state that the
type does not reflect; the value's type stays `Foo` while the compiler separately
remembers which fields are gone.

Making the residual a **real type** rather than hidden state is what lets it be passed to
a function, returned, and named in a signature — which is the whole point of the
downstream features (RFC-0119's `to_record`/`from_record` round trip, and eventually
per-field multiplicity, which is deferred until records are implemented).

---

## 1. The rule

```metel
let r = { fd = 3, path = "/tmp/x" };   // { fd: i64, path: String }
let p = move r.path;                    // r : { fd: i64 }
```

Narrowing is a **type-level consequence of an ordinary partial move**, not a separate
operation with its own syntax. Nothing is written at the narrowing site beyond the move
that causes it.

**The residual is an ordinary value.** It can be bound, passed, returned, dropped, and
narrowed again. It is not a special "partially moved" state that must be repaired before
use.

## 2. Why this needs no row machinery

A closed record over *N* fields has at most 2^*N* residual shapes, all of them concrete
record types that RFC-0116 can already express. Narrowing computes one concrete type from
another concrete type by removing a label. There is no unification variable, no row kind,
and no inference problem.

This is the load-bearing reason narrowing is specified here rather than in RFC-0121: it
looks like row polymorphism and is not. Abstracting over *which* residual a function
accepts is a genuinely different capability and belongs to RFC-0121.

## 3. What this RFC does not cover

- **Widening.** Assigning a moved-out field back is the inverse operation, and it raises a
  question narrowing does not: whether the reassembled value satisfies whatever invariant
  its type was built with. That is RFC-0114's (`Construct`), which specifies that row
  completion fires a constructor rather than being a bare write.
- **Narrowing a *nominal* type.** Whether `Handle` narrows to `Handle.{ fd }` on partial
  move — as opposed to a record narrowing to a record — depends on nominal types carrying
  rows at all, which is RFC-0120's question and, in its strong form, an open exploration
  (`reports/substructural-types/nominal-types-as-branded-rows.md`).
- **Borrowed narrowing.** Narrowing a `&var` view rather than an owned value is
  RFC-0119's by-reference mode and RFC-0109's views.
- **Per-field multiplicity.** Deliberately out of scope for the whole records cluster
  until records are implemented — see this RFC's References.

---

## Open Questions

1. **What is the interaction with `Drop`?** If a record type could carry custom teardown
   this would be the hard case — a narrowed residual reaching end of scope with the
   destructor's required fields already gone. RFC-0116 §3 forbids custom `Drop` on
   records outright, so **for records this question does not arise.** It arises the moment
   narrowing is extended to nominal types (RFC-0120), and a concrete leak example is
   worked through in `reports/substructural-types/nominal-types-as-branded-rows.md` §4.
   Recorded here so the extension does not inherit the exemption silently.
2. **Does narrowing interact correctly with RFC-0071 §7's blanket ban on partial moves out
   of `Drop`-implementing types?** RFC-0071 bans them wholesale; a narrowing-aware design
   might narrow the ban to the fields a destructor actually reads. That refinement was
   drafted in RFC-0091 §1 (`uses (fd)`), which is now deferred. Whether the ban simply
   applies as written, or needs revisiting for records, is unresolved.
3. **Is the 2^*N* claim actually the right bound in the presence of nesting?** A record
   whose field is itself a record has residuals in both dimensions. Believed fine —
   narrowing is per-value, not recursive — but not checked.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §3 step 1 — the source, which
  bundled narrowing with the type-former
- RFC-0116 (Anonymous Record Types) — the type-former this narrows
- RFC-0071 (Ownership and Move Semantics) — `2-accepted`, 0% implemented; supplies the
  move tracking this rule is a type-level consequence of
- RFC-0114 (Constructor Aspect and Canonical Construction) — the inverse operation:
  completing a row fires `construct` rather than a bare write
- `reports/substructural-types/nominal-types-as-branded-rows.md` §4 — the `Drop`-dispatch
  leak that arises when narrowing is extended to nominal types
- `public/rfcs/0-draft/rfc-0089-linear-types.md`,
  `public/rfcs/0-draft/rfc-0091-linear-records.md` — per-field multiplicity, deliberately
  deferred until records are implemented

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
