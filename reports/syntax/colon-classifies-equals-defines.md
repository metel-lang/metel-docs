---
id: colon-classifies-equals-defines
title: "`:` Classifies, `=` Defines — A Separator Invariant Metel Almost Already Has"
type: report
created_date: '2026-07-22'
---

# `:` Classifies, `=` Defines

*Short report. Came out of a syntax question about anonymous records (see
`substructural-types/access-and-presence-rows.md` §3.5) that turned out to generalize past
records into a grammar-wide invariant — one the language already satisfies at thirteen of
fourteen sites, with the fourteenth already slated for removal by an RFC under review.*

---

## The principle

> **`:` classifies. `=` defines or equates.**

`x: T` — x *has type* T. `T: Bound` — T *is bounded by* Bound. `extend Foo: Display` — Foo
*implements* Display. All classification, all `:`.

`let x = e`, `type X = Concrete`, `Deref<Target = Node>` — *this is defined to be that*.
All definition or equality, all `=`, regardless of which universe the right-hand side
lives in.

**The tempting shorter version — "`:` for types, `=` for values" — is wrong**, and worth
naming as wrong because it is the version people will remember. It makes
`type X = Concrete` and `Item = i64` into exceptions, since both put a *type* after `=`.
The classification/definition split has no exceptions.

---

## The audit

Every `:` and `=` site in `metel-interpreter/src/grammar.pest`, checked directly (line
numbers as of 2026-07-22):

| Line | Rule | Form | Conforms |
|---|---|---|---|
| 62–63 | `let_decl`, `let_mut_decl` | `x: T = e` | ✓ both |
| 76 | `struct_field` | `ident ":" type_expr` | ✓ classifies |
| 85–86 | `extend_impl_bodyless`, `_braced` | `extend Foo: Display` | ✓ classifies |
| 89 | `assoc_type_def` | `type X = type_expr;` | ✓ defines |
| 93 | `assoc_type_decl` | `type X: bound_list;` | ✓ classifies |
| 98 | `param` | `ident ":" type_expr` | ✓ classifies |
| 101 | `generic_param` | `T: bound_list` | ✓ classifies |
| 115 | `assoc_binding` | `Item = type_expr` | ✓ equates |
| 117 | `where_constraint` | `T: bound_list` | ✓ classifies |
| 149 | `assign_op` | `= expr` | ✓ defines |
| 167 | `asc_expr` | `expr ":" type_expr` | ✓ classifies |
| **245** | **`field_init`** | **`ident ":" expr`** | **✗ — the only violation** |

Thirteen of fourteen. The exception is struct-literal field initialization, where `:`
introduces a value.

**RFC-0115 (Field Initializer Separator) fixes that site directly** — `field_init = { ident
~ ("=" ~ expr)? }`, braces and punning unchanged. `Point { x = 1.0 }`.

*(Written 2026-07-22, superseded 2026-07-24: this paragraph originally read "**And RFC-0100
(Constructor-Call Construction) deletes that site**… the single violation is already
scheduled for removal by an RFC written for unrelated reasons." That was true but load-
bearing in the wrong direction — RFC-0100 retires brace literals entirely, so the invariant
could only complete if a much larger, still-contested change landed. RFC-0115 was split out
of RFC-0100 to decouple them; see Recommendation 3.)*

---

## The consequence for RFC-0100

RFC-0100's real deliverable is general keyword arguments, currently spelled
`Foo(bar: Baz)`. Under the invariant they would be `Foo(bar = Baz)` — and that **dissolves
the grammar collision the RFC spends its §3 on.**

The collision, in RFC-0100's own words:

> Any bare identifier is already a syntactically valid, zero-arg `type_expr`… so
> `Foo(bar: Baz)` is genuinely ambiguous in the grammar's own terms… Since `asc_expr`'s
> optional ascription clause sits *below* `arg_list`'s `expr` in the precedence chain, and
> PEG's ordered choice commits to the first alternative that matches, `bar: Baz` would
> always be consumed as ascription first.

With `=`, keyword binding and type ascription use different tokens and cannot be confused
at all. Two further consequences:

1. **It refunds the cost RFC-0100 explicitly accepted** — "it is no longer possible to
   write a bare ascribed variable as a positional call argument." Under `=`,
   `f(x: SomeType)` remains ascription and means what it says.
2. **It weakens the reason the RFC was reopened.** Its current status line reads:
   "Reconsidering whether general keyword arguments belong in the spec at all, given the
   collision with type ascription at call sites." If the collision is a consequence of the
   separator choice rather than of keyword arguments as a feature, that reconsideration is
   answering the wrong question.

This is the practical reason to settle the invariant now rather than treat it as
housekeeping: it bears on a decision currently in review.

---

## Costs, stated plainly

**It trades one collision for a smaller one.** `assign_expr` sits at the top of the
expression chain (`expr = { assign_expr }`), so `f(x = 1)` can parse as a positional
argument containing an assignment. That needs the same shape of fix RFC-0100 already
designed — `call_arg = { (ident ~ "=" ~ expr) | expr }`, keyword shape tried first. What is
given up is passing a bare assignment as an argument: the C `if (x = 5)` footgun, which
several languages ban deliberately. Cheaper to lose than ascription, but not free.

**Precedent splits.** Swift and C# spell keyword arguments `f(x: 1)`; Python, Kotlin, F#,
and Ada use `=`-shaped ones. Neither is unfamiliar; `=` is not obviously more natural to a
reader arriving from Swift.

**The rule has to be taught in its correct form.** Anyone who learns the short, wrong
version will meet `type X = Concrete` and conclude the language is inconsistent.

**It is not free for records either.** The record forms settled in
`access-and-presence-rows.md` §3.5 (revised 2026-07-23 to drop the dot from every
freestanding position) are `{ x = 1.0 }` for values and `{ x: f64 }` for types — the
projection forms (`Handle.{ fd }`) keep the dot, since that is the one position that
still depends on it. Freestanding is now the F# split almost verbatim, minus F#'s own
pipes. It still means record literals and struct fields read differently from each
other for as long as both exist.

---

## Recommendation

**Adopt it as a named design principle**, not as a syntax patch. This corpus already works
this way — RFC-0065's "elision is never a silent choice," Storage Transparency — and a
principle pays for itself by settling later questions cheaply: every future "what separator
for this new form?" gets a default instead of a fresh debate, and `{ x = 1 }` versus
`{ x: f64 }` stops being a special case about records and becomes an instance of a general
rule.

Concretely:

1. Record the principle (this document, or a short RFC if it should be normative).
2. ~~Recommend `=` for RFC-0100's keyword arguments, with the `call_arg` ordering fix
   restated for `=`, and note that its ascription collision — and the reason it was
   reopened — dissolve under the change.~~ **Done 2026-07-24.** RFC-0100 §1/§2/§3/§6 now
   use `=`; §3 is rewritten around the `assign_expr` collision `=` trades into, with the
   superseded ascription analysis kept behind a fold; its status note records the
   reopening reason as dissolved rather than answered; and its Unresolved Questions are
   rewritten to what actually remains (is `=` right; is losing `f(x = 1)` acceptable).
   RFC-0114 adopts the same separator for record values, so both RFCs moved together.
   One detail this document did not have: the fix wants `keyword_arg = { ident ~ "=" ~
   !"=" ~ expr }`, mirroring `assign_op`'s own `("=" ~ !"=")` guard.
3. ~~Leave `field_init` alone; RFC-0100 removes it. If RFC-0100 is refused instead, the
   invariant has one permanent exception and this recommendation should be revisited
   rather than forced.~~ **Reversed 2026-07-24 — this was the wrong structure, and its own
   stated risk is what changed it.** Waiting on RFC-0100 made a settled, dependency-free
   question hostage to an unsettled one, with "the invariant has one permanent exception"
   as the downside if RFC-0100 never lands. **RFC-0115 (Field Initializer Separator) now
   changes `field_init` directly, keeping braces**, so the invariant completes on its own
   regardless of RFC-0100's fate. Open question 4 below lapses with it.

   The second, stronger reason arrived from elsewhere the same day: RFC-0090 dropped the
   `record` keyword, settling anonymous record values as `{ x = 1.0 }`. Leaving
   `field_init` as `:` would have made a nominal struct literal differ from an anonymous
   record by separator for no recoverable reason — where `Point { x = 1.0 }` is just
   `{ x = 1.0 }` with a brand in front, which is exactly the relationship RFC-0090 tier 3
   claims holds.

---

## Open questions

1. **Should this be normative or advisory?** A design principle in `reports/` binds
   nothing. As an RFC it would bind future syntax decisions — which is the point, but also
   raises the bar for adopting it.
2. **Does the invariant survive features not yet designed?** Enum discriminants
   (`enum E { A = 1 }`) would conform; default parameter values (`fun f(x: T = e)`) would
   conform and read well. Comptime (RFC-0092–0095) is the untested case — if
   `comptime` blurs the type/value distinction, "classifies vs defines" may need
   restating, since it is currently phrased against two universes that comptime
   deliberately merges.
3. **Is `f(x = 1)`'s loss actually acceptable?** Argued here as a benefit, but Metel's
   assignment returns a value today (`assign_expr` is an expression form), so this is a
   real if small narrowing that has not been checked against existing test fixtures.
4. ~~What happens if RFC-0100 is refused?~~ **Lapsed 2026-07-24.** The single violation
   becoming permanent was the risk of routing the fix through RFC-0100; RFC-0115 removes
   the routing. The invariant no longer depends on any RFC whose outcome is uncertain.
   Worth keeping visible as the question that motivated the split, since the split is the
   answer to it.

---

## References

- `metel-interpreter/src/grammar.pest` — the fourteen sites audited above
- `internal/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` §3 — the
  ascription collision, its grammar-ordering fix, and the alternatives it set aside
- `internal/rfcs/1-under-review/rfc-0099-dot-separated-module-paths.md` — the sibling
  reopened-during-integration RFC; `OBJECTIVES.md` Trigger 14 tracks both
- `internal/rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md` — the `expr: Type`
  production the invariant keeps unambiguous; not reopened by any of this
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the record-syntax
  question this generalizes from, and the record syntax (`{ x = 1.0 }` / `{ x: f64 }` /
  `Handle.{ fd }`, dotted only where projection needs it) that depends on this invariant
  for its type/value distinction
