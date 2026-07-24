---
id: rfc-0118
title: "Row Bounds"
date: '2026-07-24'
status: integrated
target:
updated: '2026-07-24'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/289'
impl_status: not-started
---

> **Extracted from RFC-0090 on 2026-07-24** (superseded; see RFC-0116's header for the
> split rationale).
>
> **Depends on RFC-0116 (Anonymous Record Types)** for the row syntax it reuses in bound
> position, and on nothing else. It does **not** depend on RFC-0121 (Open Rows): a bound
> is a predicate over a type, not a row variable, and the two were conflated in RFC-0090
> partly because they shared a spelling.

> **Status — under review (2026-07-24).** Scheduled for v0.12.0 alongside RFC-0116, which is its only dependency.

> **Status — accepted (2026-07-24).** OQ1/OQ2 resolved by prototype (wildcard_type + row_bound built, 755 tests green, reverted). OQ3 resolved: bounds match the public projection of a row, making satisfaction module-relative -- acceptable because a bound grants no capability. OQ4 deferred to RFC-0121, which is not in this release and is the only thing that could make it reachable. OQ5 is an implementation-location question, not a design one.

> **Status — integrated 2026-07-24, targeting v0.12.0.** A "Row bounds" subsection is
> merged into `public/reference/spec/types.md` under Generics, covering open and closed
> bounds, the trailing `..`, negation with the type wildcard, why implicit structural
> satisfaction is safe, and the public-projection rule. Three one-line availability markers.
>
> **Cross-checked against the siblings still in flight for v0.12.0**, per `PROCESS.md`:
>
> - **RFC-0116 (Anonymous Record Types)** — this RFC's only dependency, now `3-integrated`.
>   No conflict: a row *type* and a row *bound* are distinguished by position, and by the
>   `..` marker for the open reading, which RFC-0116's closed types never carry.
> - **RFC-0115 (Field Initializer Separator)** — no interaction. Bounds and row fields both
>   classify and keep `:`; RFC-0115 moves only *initializers* to `=`.
> - **RFC-0071 (Ownership)** — no interaction. Bound satisfaction is a static question about
>   a type's fields, not about any value's multiplicity.
> - **RFC-0121 (Open Rows), not in this release** — inherits two questions from here
>   (impl-selection coherence, and the module-relative consequence of the public-projection
>   rule). Both are unreachable in v0.12.0 because nothing in it lets an impl be keyed on a
>   row; re-checked against RFC-0116 and this RFC rather than assumed.
>
> **The design questions that were open at review are settled, two of them by building the
> change rather than reasoning about it.** `wildcard_type` and a `row_bound` alternative to
> `bound_head` were added to the grammar, run against the suite (755 green), and reverted:
> `T: { x: f64, y: f64, .. }` and `T: !{ token: _ }` both parse, `T: Show + Clone` is
> unaffected. The prototype also settled a detail the RFC had not specified — the trailing
> `..` is admitted only after at least one field, so bare `{ .. }` does not parse.
>
> **The one substantive decision taken at integration** is the public-projection rule for
> private fields, and its consequence is unusual enough to state plainly: **bound
> satisfaction is module-relative.** The same type may satisfy a bound in one module and
> not another. That is acceptable here only because a bound grants no capability — it means
> "not callable from here," never divergent behaviour — and it is explicitly *not*
> acceptable for row-keyed impls, which is why RFC-0121 inherits it.

> **Status — integrated (2026-07-24).** Row bounds merged into public/reference/spec/types.md under Generics; three availability markers. Cross-checked against RFC-0116/0115/0071 and RFC-0121 (which inherits the impl-coherence and module-relative questions). Grammar verified by prototype.

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

1. ~~The type-position wildcard `_` does not exist.~~ **Resolved 2026-07-24 by prototype.**
   `wildcard_type = { "_" ~ !(ASCII_ALPHANUMERIC | "_") }` added to `type_expr` ahead of
   `named_type`; the negative-guard stops it swallowing `_foo`.
2. ~~`bound_head` needs a new alternative.~~ **Resolved 2026-07-24 by the same prototype:**

   ```
   bound_head = { row_bound | type_path ~ ("<" ~ bound_arg ~ … ~ ">")? }
   row_bound  = { "{" ~ (row_field ~ ("," ~ row_field)*)? ~ ("," ~ "..")? ~ ","? ~ "}" }
   row_field  = { ident ~ ":" ~ type_expr }
   ```

   **Both were built, run and reverted**, rather than reasoned about:
   - **755 tests green** with both additions.
   - `fun magnitude<T: { x: f64, y: f64, .. }>(p: T)` **parses** — the failure is
     `path: unexpected rule row_field`, a missing parser arm, not a grammar conflict.
   - `fun send<T: !{ token: _ }>(t: T)` **parses**, exercising the negative bound and the
     new wildcard together.
   - `fun f<T: Show + Clone>(t: T)` still works — existing named bounds unaffected.

   **One detail the prototype settled that the RFC had not specified:** the rule above
   admits the trailing `..` only *after* at least one field, so `{ .. }` alone — "any row
   at all" — does not parse. That looks right (a bound constraining nothing is better
   spelled by omitting the bound), but it is a decision, and it should be stated rather
   than left to fall out of the grammar.
3. ~~Cross-module private-field leakage.~~ **Resolved 2026-07-24. Rule: a row bound is
   matched against the *public projection* of a type's row, as seen from the module doing
   the matching.** RFC-0032 (`4-implemented`) already makes fields module-private by
   default, so a private field is not observable from outside; a structural bound must not
   be a back door around that. Concretely: `{ secret: T, .. }` written outside the
   declaring module never matches a struct whose `secret` is private, and the same bound
   written inside the module does match.

   **The consequence worth stating explicitly, because it is unusual: bound satisfaction is
   module-relative.** The same type may satisfy a bound in one module and not in another.
   That is acceptable *here* for the reason §3 already gives — a bound grants no capability
   over the type itself, it only decides whether a generic function will accept it, so
   module-relative satisfaction means "not callable from here," never divergent behaviour.

   **It would not be acceptable for row-conditional *impls*** (RFC-0121), where
   module-relative matching could make the same type have an impl in one module and not
   another — genuine incoherence. Flagged there rather than solved here; this RFC ships no
   impls keyed on rows. *(From RFC-0090 OQ7, via RFC-0116 OQ3.)*
4. **Coherence between structural and nominal impl selection** — **real, but not reachable
   in v0.12.0, and therefore not blocking.** An ordinary `extend Point: Display` is keyed on
   nominal identity; RFC-0121's row-conditional impls are keyed on shape, and if a value
   matched both there would be no written rule for which wins. **That collision needs impls
   keyed on rows, which is RFC-0121 and is not in this release** — this RFC contributes
   bounds only, and a bound selects nothing. Re-checked rather than assumed: nothing in
   RFC-0116 or this RFC lets an impl be written against a row. Deferred to RFC-0121, where
   open question 3 above also lands. *(From RFC-0090 OQ6.)*
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
