---
id: rfc-0136
title: "Walrus for Kept Bindings"
date: '2026-08-23'
status: under-review
target:
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/804'
---

> **Status — under review (2026-08-23).** Design-complete three-way split, formalized from reports/syntax/colon-classifies-equals-labels-walrus-binds.md's design discussion; open questions remain (compound ops, RFC-0132 coordination, migration strategy) so under-review, not accepted.
>
> **Updated 2026-08-31.** Three Open Questions closed. **#1 (compound operators):** resolved — `+= -= *= /= %=` stay unchanged; only *plain* `=` moves to `:=`. **#2 (RFC-0132 `comptime let`):** moved out of scope — `comptime let` is `let`-family so RFC-0136's classification applies (`:=`), but the syntax is RFC-0132's to introduce and spell that way from the start; this RFC does not block on it. **#5 (pattern-position field renaming, metel-core#706):** moved out of scope — separator and argument order belong to #706 (which needs rewriting against the kept/not-kept classification). **Only open question left: #4 (migration mechanics)** — corpus sizing, rewrite strategy, and the transition-alias decision, which is genuinely this RFC's own to settle.
>
> **Updated 2026-08-25, corrected same day.** Added Open Question 5 and a new audit-table
> row: metel-core#706 proposes pattern-position field renaming (`{ field = local_name }`)
> with `=`, but the renamed name is a *kept* binding under this RFC's own principle. A
> first pass here corrected the token but not the order (`field := local_name`) — every
> other `:=` site in this RFC puts the kept name on the *left*, and `local_name`, not
> `field`, is what's kept. The internally consistent spelling is `local_name := field`.
> Found while reviewing #706 directly; the ordering fix found by the reviewer, not caught
> here first.

## Summary

`let x = e`, plain reassignment (`x = e`), and `type X = Concrete` all currently spell
"define" with `=` — the same token struct/record field-init (`Point { x = 1.0 }`),
associated-type binding (`Deref<Target = Node>`), and future call-site keyword arguments
(`method(param1 = 4)`) use to mean something different: a label consumed once, at the
site, with no persisting name. This RFC splits the token along that line. `let`, plain
reassignment, and type-alias/associated-type *definition* move to `:=`; field-init,
associated-type *binding*, and keyword arguments stay on `=`; every `:` site is untouched.

---

## Motivation

`reports/syntax/colon-classifies-equals-labels-walrus-binds.md` established, and this
RFC's audit reconfirms, that Metel already satisfies a classify/define invariant at all
fourteen `:`/`=` sites in the grammar: `:` classifies (`x: T`, `T: Bound`), `=` defines or
equates (`let x = e`, `type X = Concrete`, `Deref<Target = Node>`). That invariant is
sound as far as it goes, but it treats two different things as one:

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

- **Kept → `:=`.** `let`/`var` declarations, plain reassignment, `type X := Concrete`
  (type-alias and associated-type *definition*).
- **Not kept → `=`.** Struct/record field-init (`Point { x = 1.0 }`), associated-type
  *binding* at a use site (`Deref<Target = Node>`), and future call-site keyword arguments
  (`method(param1 = 4)`).
- **Unchanged → `:`.** Every site the existing classify/define invariant already calls
  "classifies" — ascription, bounds, param and generic-param types, `where` constraints,
  `extend`'s aspect list. This proposal touches only the `=` side.

### The audit

Every `:`/`=` site in `metel-frontend/src/grammar.pest`, current as of this RFC:

| Line | Rule | Form today | Kept? | Proposed |
|---|---|---|---|---|
| 62–63 | `let_decl`, `let_mut_decl` | `x: T = e` | **kept** | `x: T := e` |
| 76 | `struct_field` | `ident ":" type_expr` | n/a (type position) | unchanged |
| 85–86 | `extend_impl_bodyless`, `_braced` | `extend Foo: Display` | n/a | unchanged |
| 89 | `assoc_type_def` | `type X = type_expr;` | **kept** — `X` usable afterward | `type X := type_expr;` |
| 93 | `assoc_type_decl` | `type X: bound_list;` | n/a | unchanged |
| 98 | `param` | `ident ":" type_expr` | n/a | unchanged |
| 101 | `generic_param` | `T: bound_list` | n/a | unchanged |
| 117 | `assoc_binding` | `Item = type_expr` | **not kept** — label, not referenceable after | stays `=` |
| 119 | `where_constraint` | `T: bound_list` | n/a | unchanged |
| 160 | `assign_op` (plain `=` only) | `= expr` | **kept** — name already exists, continues to | `:= expr` |
| 160 | `assign_op` (compound `+= -= *= /= %=`) | `+= expr` etc. | **kept**, but self-evident from the token | unchanged — see Open Questions #1 |
| 178 | `asc_expr` | `expr ":" type_expr` | n/a | unchanged |
| 260 | `field_init` | `ident ("=" expr)?` | **not kept** — consumed at construction | stays `=` |
| *(RFC-0100, proposed)* | `keyword_arg` | `ident "=" expr` | **not kept** — consumed at the call | stays `=` |
| *(metel-core#706, proposed)* | `record_pattern`/`enum_pattern` field rename | no production exists today — proposed `field = local_name` | **kept** — `local_name` is a fresh binding, usable through the rest of the arm/block, exactly like a `let` name | *out of scope for this RFC* — #706's own decision, informed by the kept/not-kept classification (see Open Questions #5) |

Four rules change: `let_decl`, `let_mut_decl`, `assign_op` (**plain `=` only** — the
compound operators `+= -= *= /= %=` stay unchanged, Open Questions #1), and
`assoc_type_def`. Everything else in the fourteen-site audit is already where this
principle would put it, including RFC-0100's not-yet-live `keyword_arg`, which needs no
change under this proposal. Pattern-position field renaming (metel-core#706) is a
separate proposal and not one of the four — see Open Questions #5.

### Worked examples

```metel
// before                              // after
let total = 0;                         let total := 0;
var count = compute();                 var count := compute();
total = total + 1;                     total := total + 1;
type Meters = f64;                     type Meters := f64;

// unchanged — none of these are "kept" bindings
Point { x = 1.0, y = 2.0 };
Deref<Target = Node>
method(param1 = 4)                     // RFC-0100, not yet live
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
   *Resolved 2026-08-31 — they stay exactly as they are.* A compound operator is
   only ever legal against a name that already exists and persists (`x += 1` is
   meaningless otherwise), so it is unambiguously a kept-binding operation on its
   face — the `:=`/`=` distinction carries no information a reader doesn't already
   have from the `+=` token itself. Prefixing them (`+:=`) would add keystrokes and
   a novel operator family to signal something the form already guarantees. Only
   *plain* `=` is genuinely ambiguous between reassignment and a field/label site
   (`Point { x = 1.0 }` vs `total = total + 1`), and only plain `=` moves to `:=`.
2. ~~**Comptime interaction (RFC-0132).**~~ *Moved out of scope 2026-08-31 — RFC-0132's
   to handle, not this RFC's.* `comptime let` / `pub comptime let` are `let`-family
   declarations, so RFC-0136's classification puts them squarely under `:=` — a kept
   binding is a kept binding regardless of a `comptime` prefix. But `comptime let` is
   RFC-0132's syntax to introduce, so RFC-0132 spells it `comptime <name> := <expr>`
   from the start, consistent with this principle. RFC-0136 does not block on RFC-0132
   and does not restate its grammar; the classification above is the only input it
   owes.
3. **Enum discriminants.** `enum E { A = 1 }` is field-init-shaped under this proposal:
   the discriminant value `1` is a label consumed at the declaration, `A` itself is
   already the kept name (introduced by the variant syntax, not by this `=`). Stays `=`.
   Included here for completeness, not because it is contested.
4. **Migration mechanics.** RFC-0115's field-initializer migration (573 literal sites, a
   parser-driven rewrite rather than a regex sweep, because declarations/patterns/literals
   share brace syntax) is the closest precedent in scale, but this RFC's surface is
   considerably larger (every `let` and every plain reassignment in the corpus, not just
   struct literals). Sizing against the current corpus, choosing a rewrite strategy, and a
   transition-alias decision (RFC-0042 §D1 and RFC-0098 both shipped renames with **no**
   transition alias; whether that precedent should hold here, given the surface size, is
   worth deciding explicitly rather than defaulting to it) are not resolved in this
   document.

5. ~~**Pattern-position field renaming (metel-core#706).**~~ *Moved out of scope
   2026-08-31 — this is not RFC-0136's to decide.* Pattern-position field renaming
   is its own feature with its own owner (metel-core#706 / whatever RFC supersedes
   it), and the separator and argument order for `{ field ? local_name }` belong to
   that proposal, not this one. RFC-0136 only supplies the classification: a
   pattern's `local_name` is a **kept** binding — a fresh name used through the rest
   of the arm or block, identical in kind to a `let` name, not to a `field_init`
   label consumed once at construction — so #706's cited "reads like `field_init`'s
   `x = 1`" precedent does not apply, and the kept/not-kept convention points at
   `:=`, kept name on the left (`local_name := field`), matching every other `:=`
   row in the audit. That is *input* to #706, which needs rewriting against it;
   RFC-0136 does not block on the outcome and adds no pattern-rename production of
   its own. The audit table's `metel-core#706` row is annotated to the same effect.

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
  syntax; **out of scope for this RFC** (Open Questions #2). `comptime let` is
  `let`-family, so RFC-0136's classification puts it under `:=`; RFC-0132 introduces
  that syntax and is responsible for spelling it `comptime <name> := <expr>` from the
  start. RFC-0136 does not block on it.
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the record-syntax
  question the classify/define invariant originally generalized from
- metel-core#706 — proposes pattern-position field renaming with `=`; **out of scope
  for this RFC** (Open Questions #5). RFC-0136 supplies only the kept/not-kept
  classification (`local_name` in a pattern is a kept binding, so `=` on the
  `field_init` precedent does not apply); the separator and argument order are #706's to
  settle, and #706 needs rewriting against that classification.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
