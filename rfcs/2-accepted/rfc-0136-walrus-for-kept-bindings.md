---
id: rfc-0136
title: "Walrus for Kept Bindings"
date: '2026-08-23'
status: accepted
target:
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/804'
---

> **Status — under review (2026-08-23).** Design-complete three-way split, formalized from reports/syntax/colon-classifies-equals-labels-walrus-binds.md's design discussion; open questions remain (compound ops, RFC-0132 coordination, migration strategy) so under-review, not accepted.
>
> **Updated 2026-08-25, corrected same day.** Added Open Question 5 and a new audit-table
> row for metel-core#706's proposed pattern-position field renaming (superseded by the
> normative invariant and the reworked OQ#5 below).

> **Status — accepted (2026-08-31).** The five open questions are resolved.
> **#1** compound operators (`+= -= *= /= %=`) stay `=` — they update an assignable place
> that already holds a value, so the token already signals it; only *plain* `=` moves to
> `:=`. **#3** enum discriminants stay `=` (the `1` is a label; the variant name is the
> kept name). **#4** hard switch, no transition alias (no public users), AST-level
> rewrite governed by PROCESS.md's existing "changes existing syntax" checklist — plan
> is #804's. **#2 (`comptime let`)** and **#5 (pattern field renaming)**: the *separator*
> is settled by the new **normative invariant** (§Proposal) — a kept binding uses `:=` —
> and the *productions* belong to RFC-0132 and metel-core#706. Nothing blocks acceptance.
>
> This is a re-acceptance. A first "accepted" transition earlier the same day was sent
> back by an adversarial review (Codex): the migration plan was thinner than PROCESS.md
> requires, worked examples used a standalone `type X = …` form the grammar does not
> have, OQ#1's rationale said "name" where it meant "assignable place," and the audit
> over-claimed completeness. All fixed in this revision — the kept/not-kept design is
> unchanged; the migration spec and the audit are tighter, and the invariant is now
> stated normatively so future kept-binding sites inherit `:=` without re-litigation.

## Summary

`let x = e`, plain reassignment (`x = e`), and associated-type *definition*
(`type Item = i64;` inside an `extend` block) all currently spell "define" with `=` —
the same token struct/record field-init (`Point { x = 1.0 }`), associated-type
*binding* (`Deref<Target = Node>`), and future call-site keyword arguments
(`method(param1 = 4)`) use to mean something different: a label consumed once, at the
site, with no persisting name. This RFC splits the token along that line. `let`, plain
reassignment, and associated-type definition move to `:=`; field-init, associated-type
binding, and keyword arguments stay on `=`; every `:` site is untouched.

Standalone `type X = …` aliases do not exist in the grammar today (RFC-0082 deferred
them); when a future RFC adds them they inherit `:=` by the normative invariant below,
as a kept binding — this RFC does not introduce them.

---

## Motivation

`reports/syntax/colon-classifies-equals-labels-walrus-binds.md` established, and this
RFC's audit reconfirms, that Metel already satisfies a classify/define invariant at
every `:`/`=` *binding-or-label* site in the grammar: `:` classifies (`x: T`,
`T: Bound`), `=` defines or equates (`let x = e`, `type Item = i64` in an impl,
`Deref<Target = Node>`). That invariant is sound as far as it goes, but it treats two
different things as one:

```metel
let total = 0;                    // total is usable from here on
Point { x = 1.0, y = 2.0 };       // x is a field label, gone the instant the value is built
total = total + 1;                // total, again, still usable
Deref<Target = Node>              // Target is a label picking out an associated type; not a name
```

Reading these side by side is where the confusion this RFC responds to actually shows up:
`Point { x = 1.0 }` and `total = total + 1` share a token despite meaning categorically
different things — one introduces a value that is thrown away as soon as it is consumed,
the other names a place that persists. **The core difference is whether the name is
kept** — referenceable again after the statement — **or not kept** — consumed once, at
the site. That distinction is real, it is not currently visible in the syntax, and it
generalizes cleanly across values, types, and (per RFC-0100's still-`1-under-review`
keyword-argument proposal) call arguments too — it is not a records-only or an
assignment-only question.

**Why this needs to happen now rather than later:** RFC-0100's keyword arguments
(`method(param1 = 4)`) are still under review and not yet live. Landing them on `=` first
and correcting the underlying assignment/label conflation afterward would mean touching
every keyword-argument call site a second time. Settling the three-way split before
RFC-0100 ships (or alongside it) avoids that.

---

## Proposal

> **`:` classifies. `=` labels — a value or type consumed at the construction or call
> site, not kept as a name. `:=` binds — a name that outlives the expression it appears
> in.**

- **Kept → `:=`.** `let`/`var` declarations, plain reassignment, and associated-type
  *definition* (`type Item := i64;` inside an `extend`/`aspect` block).
- **Not kept → `=`.** Struct/record field-init (`Point { x = 1.0 }`), associated-type
  *binding* at a use site (`Deref<Target = Node>`), and future call-site keyword arguments
  (`method(param1 = 4)`).
- **Unchanged → `:`.** Every site the existing classify/define invariant already calls
  "classifies" — ascription, bounds, param and generic-param types, `where` constraints,
  `extend`'s aspect list. This proposal touches only the `=` side.

### The invariant (normative)

> **A site that introduces a *kept* binding — a name referenceable after the statement
> it appears in — uses `:=`. A site that consumes a name, value, or type as a one-shot
> label — not referenceable afterward — uses `=`. `:` is unchanged everywhere.**

This binds sites that do not exist in the grammar yet. When a future RFC adds any of
the following, each introduces a kept binding and therefore uses `:=`:

- **standalone `type` aliases** (`type Meters := f64;` — RFC-0082 deferred these);
- **`comptime let` / `pub comptime let`** (RFC-0132) — `let`-family, so `:=`;
- **pattern-position field renaming** (metel-core#706) — the renamed `local_name` is a
  fresh binding used through the rest of the arm or block, so `:=`.

Those RFCs own their own productions and, where applicable, argument order; they do
**not** get to re-decide the separator. If one of them lands before this RFC's
migration, it must land on `:=`, not `=` — landing on `=` and migrating afterward is
the exact double-touch this RFC exists to avoid.

### The audit

Every `:`/`=` *binding-or-label* site in `metel-frontend/src/grammar.pest` as of this
RFC. **Scope:** this classifies the sites where `:` or `=` introduces or labels a name,
value, or type. Multi-character operator tokens that merely *contain* `=` — `==`,
`!=`, `<=`, `>=`, `..`, `..=` — are lexically distinct and not in scope. `:` ascription
of the shape `ident ":" type_expr` recurs under several rule names (`struct_field`,
`record_type_field`, `row_field`, `param`); it is listed once as a representative row
and is categorically **unchanged** wherever it appears. Line numbers are approximate
and move; the rule names are the stable reference.

| Rule(s) | Form today | Kept? | Proposed |
|---|---|---|---|
| `let_decl`, `let_mut_decl` | `x: T = e` | **kept** | `x: T := e` |
| `assign_op` — plain `=` (`"=" ~ !"="`) | `place = e` (`place` is a name, field, index, or deref) | **kept** — reassigns an existing binding, still live after | `place := e` |
| `assign_op` — compound (`+= -= *= /= %=`) | `place += e` etc. | **kept**, and self-evident from the token — see Open Questions #1 | **unchanged** |
| `assoc_type_def` (inside `extend`/`aspect` braces) | `type Item = type_expr;` | **kept** — `Item` is nameable afterward as `Type::Item` and inside the block | `type Item := type_expr;` |
| `assoc_binding` (at a use site, `Deref<Target = Node>`) | `Target = type_expr` | **not kept** — a label selecting an associated type; not a name | **unchanged** (`=`) |
| `field_init` (`Point { x = 1.0 }`) | `ident ("=" expr)?` | **not kept** — consumed at construction | **unchanged** (`=`) |
| `keyword_arg` *(RFC-0100, not yet live)* | `ident "=" expr` | **not kept** — consumed at the call | **unchanged** (`=`) — no change needed |
| `struct_field` / `record_type_field` / `row_field` / `param` / `generic_param` / `where_constraint` / `assoc_type_decl` / `asc_expr` / `extend`'s aspect list | `ident ":" type_or_bound` | n/a — `:` classifies | **unchanged** |
| *pattern field rename* *(metel-core#706, no production yet)* | proposed `field = local_name` | **kept** — `local_name` is a fresh binding, live through the rest of the arm/block | *out of scope for this RFC* — #706's production and argument order, but `:=` per the normative invariant (Open Questions #5) |
| *standalone `type` alias* *(no production yet — RFC-0082 deferred)* | — | **kept** | `:=` when a future RFC adds it (normative invariant) — not introduced here |

**What changes:** the `let`-family (`let_decl`, `let_mut_decl`), `assign_op`'s plain-`=`
alternative (`"=" ~ !"="`), and `assoc_type_def` — each `=` in those becomes `:=`.
`assign_op`'s compound alternatives are untouched. Everything else in the audit is
already where this principle would put it, including RFC-0100's not-yet-live
`keyword_arg`. Compound `assign_op` and pattern-position field renaming are explicitly
*not* among the changes — see Open Questions #1 and #5.

### Worked examples

```metel
// before                                    // after
let total = 0;                               let total := 0;
var count = compute();                        var count := compute();
total = total + 1;                            total := total + 1;
obj.field = obj.field + 1;                     obj.field := obj.field + 1;

extend Counter: Iterator {                     extend Counter: Iterator {
    type Item = i64;                               type Item := i64;
}                                             }

// unchanged — none of these are "kept" bindings
Point { x = 1.0, y = 2.0 };
Deref<Target = Node>
method(param1 = 4)                            // RFC-0100, not yet live
```

### A resolved side effect: the `f(x = 1)` collision

The original classify/define report flagged, as an accepted cost, that `assign_expr` sits
high in the expression precedence chain, so `f(x = 1)` can parse as a positional argument
containing an assignment — needing a `call_arg` reordering fix in RFC-0100. Under this
proposal that collision disappears rather than needing a fix: once plain assignment
requires `:=`, `=` can no longer parse as `assign_op` inside an argument position at all,
so `f(x = 1)` is unambiguously a keyword-argument label. RFC-0100's `call_arg` ordering
concern is moot if this RFC lands first.

---

## Alternatives Considered

- **Two-way "define vs. mutate" split** (`let x := 1` defines, `x = 2` mutates). The
  framing first proposed in discussion. Rejected: it cannot classify `assoc_binding`
  (`Deref<Target = Node>`) or the field-init/keyword-arg family at all, since none of
  those is a mutation of anything — lumping them under "definition" alongside `let`
  reintroduces the conflation the original classify/define report already fixed. The axis
  that explains every site is *kept vs. not kept*, not *created vs. changed*: `let x :=
  1` and `x := 2` (reassignment) are the same case under kept/not-kept despite one
  "defining" and one "mutating," and landing on the same token is the point.
- **Go-style `:=` means "first occurrence."** Go's `:=` contrasts with `=` on whether the
  name has been declared before, not on whether it persists afterward. Considered and set
  aside: under that rule Metel's plain reassignment (name already exists) would stay `=`,
  which does not resolve the struct-instantiation-vs-assignment confusion motivating this
  RFC — `Point { x = 1.0 }` and `total = total + 1` would still share a token. The
  distinction needed here is whether the name is usable *after* the statement, and by
  that measure reassignment belongs with `let`, not with field-init.
- **Leave `=` alone; disambiguate only at RFC-0100's call sites.** Fixes the narrowest
  visible symptom (keyword args vs. positional assignment) without touching the
  `let`/field-init conflation that motivated this RFC in the first place. Rejected as
  addressing a special case of a general problem rather than the problem.
- **Do nothing; treat it as a report-only style note.** The classify/define report already
  exists and binds nothing normatively. Given the migration scope below, report-only
  status was judged insufficient — see `colon-classifies-equals-labels-walrus-binds.md`'s
  own updated Recommendation.

---

## Costs

**This is the largest syntax-migration surface proposed to date.** `let`/`var`
declarations and plain reassignment are the most common statement forms in any Metel
program. Every existing `.mtl` fixture, every spec example, and every RFC's worked
examples that show a `let` or a reassignment need updating. This is a breaking change to
the most-written syntax in the language, and should not be minimized as a small
punctuation fix.

**A real token to learn and to type.** `:=` is not a single keystroke on most keyboards
the way `=` is. Every language that uses it as sugar for "declare" (Go, Pascal, Ada's
distinct assignment/equality split) accepts that friction deliberately; Metel would accept
it for a narrower reason (kept vs. label, not first-occurrence), which is real but is
still friction for anyone arriving from a `=`-only-means-assignment language — the
overwhelming majority of working programmers (C-family, Python, JavaScript, Rust).

**Precedent is genuinely split**, as the original classify/define report already noted for
the `=`-vs-`:` question and which carries over here: some languages use `:=` for
assignment/declaration (Pascal, Ada, Go), most mainstream languages do not (C-family,
Python, Rust, Swift). Adopting `:=` is a real departure from what most of Metel's likely
readers already know, not a return to a majority convention.

---

## Open Questions

1. **Do compound assignment operators (`+=`, `-=`, `*=`, `/=`, `%=`) move too?**
   *Resolved 2026-08-31 — they stay exactly as they are.* A compound operator is only
   ever legal against an **assignable place that already holds a value** — a name, a
   field (`obj.x += 1`), an index (`xs[i] += 1`), a deref (`*p += 1`); `x += 1` where
   `x` names nothing is a resolution error. So it is unambiguously an in-place update
   of existing storage on its face, and the `:=`/`=` distinction carries no
   information a reader doesn't already have from the `+=` token itself. Prefixing them
   (`+:=`) would add keystrokes and a novel operator family to signal something the
   form already guarantees. Only *plain* `=` is genuinely ambiguous between
   reassignment and a field/label site (`Point { x = 1.0 }` vs `total = total + 1`),
   and only plain `=` moves to `:=`.

   *Accepted seam:* `let x := 0; x += 1;` uses two different token shapes for one
   variable's lifecycle — `:=` to introduce, `+=` to update. This is deliberate and
   fine: `:=` marks *introduction of a kept name*, `+=` marks *update of existing
   storage*, and the two are genuinely different operations. `x := x + 1` (the plain
   reassignment form) is still available for anyone who wants one token shape
   throughout.
2. ~~**Comptime interaction (RFC-0132).**~~ *Moved out of scope 2026-08-31 — RFC-0132's
   to handle, not this RFC's.* `comptime let` / `pub comptime let` are `let`-family
   declarations, so they fall under the **normative invariant** above: a kept binding
   uses `:=`, `comptime` prefix or not. RFC-0132 owns that production and is bound to
   spell it `comptime <name> := <expr>`; if RFC-0132 lands before this RFC's migration,
   it lands on `:=`, not on `=` with a follow-up. *(RFC-0132's current draft examples
   still show `comptime let ... = ...`; that is stale against this invariant and is
   RFC-0132's to correct, tracked at metel-core#726.)* RFC-0136 does not block on
   RFC-0132.
3. **Enum discriminants.** `enum E { A = 1 }` is field-init-shaped under this proposal:
   the discriminant value `1` is a label consumed at the declaration, `A` itself is
   already the kept name (introduced by the variant syntax, not by this `=`). Stays `=`.
   Included here for completeness, not because it is contested.
4. **Migration mechanics.** *Two design decisions resolved 2026-08-31; the detailed
   plan is #804's, governed by an existing checklist.*

   **No transition alias — hard switch.** The alias question turns on who bears the
   cost of a hard break, and the answer is: nobody outside this repository. Metel has
   no public users and no external corpus, so once the in-repo surface is migrated **in
   the same change** that makes `:=` the grammar, there is nothing a compatibility alias
   would protect. RFC-0042 §D1 and RFC-0098 both shipped renames with no alias; the
   larger surface here is more edits, not more risk, when every edit is in a tree the
   same PR owns.

   **Rewrite is AST-level, not line-based.** Assignment is an *expression*
   (`assign_expr = { unary_expr ~ assign_op ~ assign_expr | or_expr }`), so `place = e`
   can appear anywhere an expression can — a call argument, a `match` guard, a
   `while`/`for` clause, a `return`/`break` value, an array literal — not only as a
   statement. The migration therefore targets **every `assign_op` node whose operator
   is plain `=` (`"=" ~ !"="`)**, wherever it occurs, plus the two keyword-anchored
   `let_decl`/`let_mut_decl` forms and `assoc_type_def`. A blind `s/=/:=/` is unsafe —
   `=` also appears in `==`, in struct/record literals, in `assoc_binding`, and in the
   future `keyword_arg` — so the rewriter must run over the parsed AST (the RFC-0115
   precedent), not the text.

   **The sweep is governed by PROCESS.md's "changes existing syntax" exit criterion,
   not restated here.** That checklist already requires: sweep *this whole repo* and
   `metel-docs-internal/reports/` in the same change (not just fixtures/spec/RFCs — the
   `getting-started/` tutorials, `blog/`, `stdlib/`, and `tools/check_doc_examples.py`
   inputs all carry live syntax); no blind regex; **verify by compiling** at least one
   complete example extracted from swept prose; watch for CRLF files; and decide the
   treatment of dated documents explicitly (correct code samples in place; leave
   superseded/refused RFCs and `reports/archive/` alone). Old `=` in a declaration or
   reassignment position becomes a parse error the moment `:=` lands, and a `neg_*`
   fixture guards that (the RFC-0130 pattern).

   Corpus sizing and the mechanical rewriter are #804's to build — a finite, one-shot,
   in-repo job against a checklist that already exists — not a design question this
   document needs to answer.

5. ~~**Pattern-position field renaming (metel-core#706).**~~ *Separator settled by the
   normative invariant 2026-08-31; production and argument order are #706's.* A
   pattern's `local_name` is a **kept** binding — a fresh name live through the rest of
   the arm or block, identical in kind to a `let` name, not a `field_init` label — so
   by the invariant above it uses **`:=`**, and #706's cited "reads like `field_init`'s
   `x = 1`" precedent does not apply. That much is not negotiable and does not wait on
   #706. What is #706's to decide: the grammar production itself, and the argument order
   — `local_name := field` (kept name on the left, matching every other `:=` row) versus
   `field := local_name` (matching Rust's field-first `Circle { radius: r }`); both have
   a real cost and this RFC does not pick between them. If #706 lands before this RFC's
   migration it lands on `:=`. RFC-0136 adds no pattern-rename production of its own.

**Explicitly out of scope:** declaration-side default parameter values (hypothetical `fun
f(x: T = e)`). Raised once during the discussion that produced this RFC and set aside — a
different syntactic position from the call-site keyword-arg case this RFC addresses (`x`
there is a parameter declaration with a type and a default, not a label), with its own
kept/not-kept answer not decided here. Left for a future RFC.

---

## References

- `reports/syntax/colon-classifies-equals-labels-walrus-binds.md` — the classify/define
  invariant this RFC extends, the full fourteen-site audit (original and extended), and
  the design discussion that produced the kept/not-kept axis
- `public/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` — proposes the
  `keyword_arg` site this RFC's audit covers; unaffected by this proposal (stays `=`), and
  this RFC's resolution of the `f(x = 1)` collision (see Proposal) simplifies RFC-0100's
  own `call_arg` ordering concern
- `public/rfcs/4-implemented/rfc-0115-field-initializer-separator.md` — the closest
  precedent in migration shape and scale (a parser-driven corpus rewrite, no transition
  alias), though smaller in surface than this proposal
- `public/rfcs/1-under-review/rfc-0132-comptime-execution-model-comptime-let-comptime-fun-comptime-if.md` — `comptime let`
  syntax. `comptime let` is `let`-family, so the **normative invariant** (§Proposal)
  puts it under `:=`; RFC-0132 owns the production and is bound to spell it
  `comptime <name> := <expr>`. Its current draft examples still show `= …` — stale
  against the invariant, RFC-0132's to fix (metel-core#726). RFC-0136 does not block
  on it. (Open Questions #2.)
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the record-syntax
  question the classify/define invariant originally generalized from
- metel-core#706 — proposes pattern-position field renaming with `=`. The **separator**
  is fixed by the normative invariant (a pattern's renamed name is a kept binding →
  `:=`); the **production and argument order** are #706's to settle, and #706 needs
  rewriting against the invariant. RFC-0136 adds no pattern-rename production.
  (Open Questions #5.)

---

## Decision

**Outcome:** Accepted 2026-08-31 (re-accepted after an adversarial review the same day —
see the status note). All five open questions are closed: #1 (compound operators stay
`=`) and #4 (hard switch, no alias, AST-level rewrite governed by PROCESS.md's existing
syntax-change checklist) are resolved here; #3 (enum discriminants) is answered inline;
the *separator* for #2 (`comptime let`) and #5 (pattern field renaming) is fixed by the
normative invariant, and their *productions* are RFC-0132's and metel-core#706's. The
kept/not-kept design was not changed by the review — the migration spec and the audit
were tightened and the invariant made normative. The migration itself is a finite
in-repo job tracked by metel-core#804.
**Target:** v0.13.1 (metel-core#804).
