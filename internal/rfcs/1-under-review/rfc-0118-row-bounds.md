---
id: rfc-0118
title: "Row Bounds"
date: '2026-07-24'
status: under-review
target:
updated: '2026-07-24'
---

> **Extracted from RFC-0090 on 2026-07-24** (superseded; see RFC-0116's header for the
> split rationale).
>
> **Depends on RFC-0116 (Anonymous Record Types)** for the row syntax it reuses in bound
> position, and on nothing else. It does **not** depend on RFC-0121 (Open Rows): a bound
> is a predicate over a type, not a row variable, and the two were conflated in RFC-0090
> partly because they shared a spelling.

> **Status — under review (2026-07-24).** Scheduled for v0.12.0 alongside RFC-0116, which is its only dependency.

## Summary

A bound written as a bare row: `T: { x: f64, y: f64, .. }` means "any type carrying at
least these fields." Negation reuses the bound grammar's existing `!`: `T: !{ token: _ }`
means "any type carrying no field named `token`." **Any nominal struct with matching
fields satisfies a row bound with no explicit opt-in** — this is the one implicit,
structural satisfaction rule in an otherwise nominal aspect system, and §3 explains why
that is safe here specifically.

Replaces the `HasField<"x", f64>` / `Lacks<"tag">` aspect family, which **never parsed** —
`bound_arg` accepts only `assoc_binding` or `type_expr`, and `type_expr` has no
string-literal alternative.

---

## Motivation

Generic code often wants "anything with an `x` and a `y`," not a specific nominal type.
Without a structural bound, every such case needs either a bespoke aspect per field shape
— unworkable at scale — or forces callers to wrap values in a common nominal type to
satisfy a bound that was never about identity.

GHC's `HasField "x" r Float` answers the same problem. The first draft of this feature
copied that shape directly and inherited a spelling Metel's grammar cannot parse; writing
the bound as a row instead removes the string literal, compacts an ANDed chain of
per-field facts into one bound naming several labels, and reuses syntax that already
exists for an unrelated reason.

---

## 1. Positive bounds, and the `..` that makes them open

```metel
fun magnitude<T: { x: f64, y: f64, .. }>(p: T) -> f64 { ... }
```

**The trailing `..` is load-bearing.** It is an *anonymous row variable* — "and a rest I am
not naming" — and its presence is what makes the bound open:

```metel
fun f(p: { x: f64 })              // a closed type: exactly x
fun g<T: { x: f64 }>(p: T)        // a closed bound: T's row is exactly x
fun h<T: { x: f64, .. }>(p: T)    // an open bound: T has at least x
```

Without the marker, the closed and open readings would be spelled identically and told
apart only by grammatical position — and the closed *bound* reading could not be written at
all. The named form `..R` (RFC-0121) is the same mechanism with the rest given a name.

## 2. Negative bounds

`T: !{ token: _ }` asserts the absence of a label, reusing `bound = { bang? ~ bound_head }`
unchanged. **Negative bounds take no `..`**: absence has no rest to quantify over, and
`!{ token: _ }` already means "no field named `token`, whatever its type would have been."

The `_` is a type-position wildcard meaning "any type." It **does not exist today** —
confirmed directly: `_` appears only inside `pattern` (`Pattern::Wildcard`), nowhere in
`type_expr`. See Open Questions.

## 3. Structural satisfaction is implicit, and why that is safe here

Every other aspect in Metel requires an explicit impl. A row bound does not: any struct
with matching fields satisfies it. Go's implicit interface satisfaction draws exactly this
criticism, and TypeScript's silent nominal-identity collapse is the failure mode being
guarded against.

**The rule that makes it safe: a bound grants no capability over the type itself.** It only
lets a generic function accept the type. Nothing about satisfying `{ x: f64, .. }` changes
what `Point` can do, what impls resolve for it, or what it converts to. Capability that
*does* change the type — conversion (RFC-0119), row-conditional impls (RFC-0121) — stays
behind explicit opt-in.

That asymmetry is the whole of the answer, and it is why this RFC can ship implicit
satisfaction without reopening the tiering question the rest of the cluster is built on.

## 4. Relationship to RFC-0116's closed types

A closed record type and a row bound are now spelled with the same braces, distinguished by
position: after `:` in a `param` or `let` annotation it is RFC-0116's exact type; after `:`
in a `generic_param` or `where_constraint` it is this RFC's predicate. They remain
semantically distinct — a closed type cannot be used as a predicate, a bound cannot be used
as a type — and with the `..` marker present they are different token sequences, so no
position admits both readings.

---

## Open Questions

1. **The type-position wildcard `_` does not exist** and §2 requires it. `_` is
   `Pattern::Wildcard` only; `type_expr` has no wildcard alternative. A small, genuinely
   new addition. *(From RFC-0090 OQ12.)*
2. **`bound_head` needs a new alternative.** `bound_head = { type_path ~ (…)? }` requires
   every bound to start from an identifier; a bare row is not one. Bound position parses
   neither struct literals nor blocks, so bare `{ … }` collides with nothing there — but
   the rule still has to be written. *(From RFC-0090 OQ12.)*
3. **Cross-module private-field leakage.** If a bound `{ secret: T, .. }` is checked
   against a struct's row, does code outside the declaring module get to observe — or
   structurally match against — a private field? It should not, which implies the row is
   not one flat structure per type: cross-module matching needs to see a **public
   projection** of the row, with private fields invisible. No mechanism for that is
   designed. *(From RFC-0090 OQ7; RFC-0116's OQ3 is the type-former's half of the same
   problem.)*
4. **Coherence between structural and nominal impl selection.** An ordinary
   `impl Display for Point` is keyed on nominal identity; RFC-0121's row-conditional impls
   are keyed on shape. If a `Point` value matches both, which wins? The obvious default —
   more specific beats blanket — is written down nowhere, and RFC-0060/RFC-0061's coherence
   checking does not account for a second axis at all. *(From RFC-0090 OQ6.)* Listed here
   rather than in RFC-0121 because the ambiguity exists as soon as bounds do.
5. **How does row-membership checking relate to RFC-0096's auto-impl algorithm?**
   RFC-0096 §7 worked out that `HasField`-style satisfaction is *existential*, not the
   universal recursion `Send`/`Sync`/`Linear` use, so it does not fit that algorithm. The
   bare-row spelling does not change this — only the surface. What checks a row bound, and
   where it lives in the typechecker, is unspecified.

---

## References

- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` §1, §2, §7 — the source
- RFC-0116 (Anonymous Record Types) — the row syntax reused in bound position
- RFC-0121 (Open Rows) — `..R`, the named form of §1's anonymous `..`
- RFC-0096 (Auto-Impl Aspects) §7 — works out precisely how row-membership differs from
  the `Send`/`Sync`/`Linear` auto-impl algorithm, and flags the same coherence gap
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern this extends structurally
- RFC-0060 (Aspect Impl Coherence), RFC-0061 (Structural Aspect Bounds) — the coherence
  checking OQ4 would extend
- RFC-0032 (Field-Level Visibility) — the visibility model OQ3 must be reconciled with
- `reports/substructural-types/nominal-types-as-branded-rows.md` §12 — the derivation of
  the bare-row bound spelling and why `HasField` was replaced outright

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
