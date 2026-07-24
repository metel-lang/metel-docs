---
id: rfc-0115
title: "Field Initializer Separator"
date: '2026-07-24'
status: implemented
target:
updated: '2026-07-24'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/287'
impl_status: implemented
---

> **New RFC, split out of RFC-0100 on 2026-07-24.** RFC-0100 bundled two things: a
> separator change (`field_init`'s `:` → `=`) and a construction-syntax change (brace
> literals → `Type(args)` call-shaped construction, plus general keyword arguments). The
> first is small, has no dependencies, and is ready; the second is a real feature that is
> still under review and has been reopened once. Bundling them meant a grammar-wide
> invariant was hostage to an unrelated open question. This RFC takes the separator half
> **only**. RFC-0100 keeps the rest, intact and still `1-under-review`, and is neither
> blocked by nor blocking this one.
>
> `rfc.py new`'s overlap check flagged RFC-0100 (0.161), RFC-0033, RFC-0045, RFC-0091,
> RFC-0096. Checked each: RFC-0100 is the parent, handled above. RFC-0033 (Field-Level
> Mutability) and RFC-0045 (Mutable Address-Of) concern *mutation* of fields, not the
> literal that initializes them — no shared grammar rule. RFC-0091 and RFC-0096 matched on
> the word "record" alone and touch neither `struct_literal` nor `field_init`.

> **Status — under review (2026-07-24).** Pulled into v0.12.0 alongside RFC-0116: shipping RFC-0116's { x = 1.0 } anonymous records without this would release the nominal/anonymous separator mismatch that this RFC exists to remove.

> **Status — accepted (2026-07-24).** OQ3 resolved by direct verification: the parser never sees the separator (zero parser changes needed), punning is unaffected, no fixture uses = inside a literal brace, and no negative test pins the : spelling. OQ1 is inherited unchanged from the current syntax; OQ2 is delegated to colon-classifies-equals-defines.md by construction. Neither blocks.

> **Status — integrated 2026-07-24, targeting v0.12.0.** `field_init`'s change is merged
> into `public/reference/spec/`: 41 struct- and enum-literal sites across six spec files
> converted to `=`, with a one-line availability marker at `declarations.md`'s
> "Instantiation and Field Access", and the shorthand prose reworded (`the : value part`
> → `the = value part`). Field *declarations*, enum *variant* declarations
> (`Circle { radius: f64 }`, `B { y: ! }`) and patterns were verified untouched.
>
> **Cross-checked against the siblings still in flight for v0.12.0**, per `PROCESS.md`'s
> requirement that integration test against active cluster members and not only
> already-integrated work:
>
> - **RFC-0116 (Anonymous Record Types)** — no collision, and this is the pairing that
>   motivated pulling this RFC into the release: `struct_literal = { type_path ~ "{" … }`
>   requires a preceding path, so `Point { x = 1.0 }` and bare `{ x = 1.0 }` are
>   distinguishable by the path alone, and now differ only by that path rather than also by
>   separator.
> - **RFC-0118 (Row Bounds)** — no interaction. A row *type* (`{ x: f64 }`) and a row bound
>   (`T: { x: f64, .. }`) both classify and keep `:`; only initialization moves to `=`.
>   The two constructs becoming visually distinct is the separator invariant working, not a
>   clash.
> - **RFC-0114 (Construct)** — a positive interaction worth recording. RFC-0114 §2 desugars
>   `Point { x = 1.0 }` to `Point::construct({ x = 1.0 })`; with this RFC the literal's
>   inner form is now *character-identical* to the record it desugars to, so the
>   desugaring is transparent rather than a re-spelling.
> - **RFC-0071 (Ownership and Move Semantics)** — separator-neutral. Whether the
>   initializer expression moves or copies is unaffected by the token before it.
> - **RFC-0100 (Constructor-Call Construction, `1-under-review`)** — the one live conflict,
>   already recorded as an accepted risk: if it lands, `field_init` ceases to exist and
>   these sites migrate twice.
>
> **Two behaviours confirmed unchanged against `grammar.pest` directly.** Patterns have no
> separator to change — `enum_pattern` (line 265) accepts a bare `ident` in field position
> and nothing else — so destructuring is untouched. And `Point { x == y }` fails exactly as
> it does today: `field_init` matches the bare `x`, then the literal fails on `==`, before
> and after.

> **Status — integrated (2026-07-24).** Spec merged into public/reference/spec/ (41 literal sites, one-line availability marker, shorthand prose reworded); cross-checked against RFC-0116/0118/0114/0071/0100, the siblings still in flight for v0.12.0.

> **Implemented 2026-07-24 in `develop` (`00d0bd9`).** The grammar change and the
> 566-substitution corpus migration were this RFC's entire scope; both are done, verified at
> 805 tests passing with clippy unchanged. Delegated to codex, diff reviewed and
> independently re-verified.
>
> **Ships in v0.12.0, which has not been tagged — and that does not hold the lifecycle
> back.** `4-implemented` means the code is built, not that the version shipped: RFC-0110
> reached `4-implemented` on 2026-07-21, three days before v0.11.0 was tagged, and carried a
> `Changed in v0.11.0` marker throughout. The spec marker here follows the same convention —
> the future-facing `Planned for v0.12.0 (RFC-0115)` form is replaced by `Changed in
> v0.12.0`, which names the version a reader needs and persists as permanent availability
> documentation rather than needing a second edit at release.

> **Status — implemented (2026-07-24).** Grammar change and 566-substitution corpus migration landed in develop (00d0bd9); 805 tests passing, clippy unchanged. Spec marker moved from the future-facing 'Planned for' form to 'Changed in v0.12.0', per RFC-0110's precedent of reaching 4-implemented before its release was tagged.

## Summary

`field_init` changes from `ident ":" expr` to `ident "=" expr`, so a struct literal is
written `Point { x = 1.0, y = 2.0 }` instead of `Point { x: 1.0, y: 2.0 }`. Braces,
punning, and everything else about construction stay exactly as they are.

This is a one-token change with an outsized payoff: `field_init` is the **only** site in
the entire grammar where `:` introduces a value, so this single edit completes the
`:` classifies / `=` defines invariant, with no exceptions left anywhere in the language.

---

## Motivation

`reports/syntax/colon-classifies-equals-defines.md` audits every `:` and `=` site in
`grammar.pest` against one rule:

> **`:` classifies. `=` defines or equates.**

Thirteen of fourteen sites conform. `field_init` (`grammar.pest:242`) is the sole
violation — `Point { x: 1.0 }` uses the classification separator to bind a value.

That report expected RFC-0100 to remove the violation as a side effect, since RFC-0100
retires brace literals entirely. **Relying on that turned out to be the wrong structure,
for two reasons that only became clear once RFC-0100 was revised on 2026-07-24:**

1. **RFC-0100 is genuinely uncertain, and the invariant is not.** RFC-0100 was reverted
   from `2-accepted` to `1-under-review` during integration (`OBJECTIVES.md` Trigger 14)
   and still carries open questions about whether general keyword arguments belong in the
   spec at all. The invariant has none. Coupling them meant a settled question could only
   land when an unsettled one did.
2. **The report itself recorded the failure mode and it came true.** Its own open question
   4 asked "what happens if RFC-0100 is refused?" and answered: "the single violation
   becomes permanent, and the principle would have to be stated with an exception — which
   is materially weaker than a rule with none." Splitting removes that risk entirely
   rather than continuing to carry it.

A second, independent motivation surfaced from RFC-0090's 2026-07-24 amendment, and it is
the stronger of the two:

**It aligns nominal struct literals with anonymous record values.** RFC-0090 now spells an
anonymous record `{ x = 1.0, y = 2.0 }`. Under this RFC a nominal struct literal is
`Point { x = 1.0, y = 2.0 }` — *the same form with a brand prefix.* That is exactly the
relationship RFC-0090 tier 3 claims holds semantically (a named record is a row plus a
brand), now visible in the surface syntax rather than contradicted by it. Without this
RFC, the two would differ by separator for no reason a reader could recover:

```metel
{ x = 1.0, y = 2.0 }         // anonymous record          (RFC-0090, settled)
Point { x: 1.0, y: 2.0 }     // nominal struct — today, gratuitously different
Point { x = 1.0, y = 2.0 }   // nominal struct — this RFC, the same form plus a brand
Point.{ x }                  // projection from a receiver (RFC-0090 §3.5, settled)
```

---

## 1. The change

```
field_init = { ident ~ ("=" ~ expr)? }
```

That is the entire grammar diff. Specifically unchanged:

- **Braces stay.** `struct_literal = { type_path ~ "{" ~ … ~ "}" }` is untouched. This RFC
  takes no position on call-shaped construction; that is RFC-0100's question.
- **Punning stays.** The `("=" ~ expr)?` clause is still optional, so `Point { x }` — take
  `x` from the enclosing scope — works exactly as today.
- **Pattern destructuring is untouched**, because it has no separator to change:
  `enum_pattern` (`grammar.pest:263`) accepts a bare `ident` in field position and nothing
  else. There is no `field: subpattern` renaming form in the grammar.
- **Enum-variant literals** follow `struct_literal`'s rule and change with it, for free.

## 2. Why this carries no grammar risk

Worth stating explicitly, because both syntax changes in this area that were proposed
*before* this one did carry a real hazard, and this one is cheaper than either:

- **RFC-0100's `name: value` keyword arguments** collided head-on with type ascription
  (`asc_expr`), because call arguments route through a general `expr`.
- **RFC-0100's revised `name = value` keyword arguments** collide with assignment
  (`assign_expr = { unary_expr ~ assign_op ~ assign_expr | … }`), needing a reordered
  `call_arg` rule and a `!"="` guard.

**Neither applies here.** `field_init` matches `ident ~ "="` *directly* — the field label
never routes through `expr`, exactly as it never routes through `expr` today with `:`. So
there is no alternation to reorder, no lookahead guard needed, and no expression form that
could shadow it. This is the same structural reason `reports/substructural-types/access-and-presence-rows.md`
§3.5 gives for why today's `Point { x: 1.0 }` does not collide with type ascription
either.

`Point { x == y }` is rejected before and after, by the same path (`field_init` matches
bare `x`, then the literal fails on `==`).

## 3. Migration

No semantics change and no AST shape change — `FieldInit` keeps its existing shape; only
the token the parser expects between label and value moves.

**Sized against the corpus 2026-07-24, and it is not the trivial sweep an earlier draft of
this section implied.** That draft said "mechanical and total"; the second half is right,
the first needs qualifying.

| | count |
|---|---|
| Literal sites to change (`:` → `=`) | **573** |
| Declaration lines that must **not** change | **382** |
| `.mtl` files touched | ~238 |

**The hazard is that three different constructs share brace syntax and only one of them
changes:**

```metel
struct Point { x: f64 }                     // declaration — `:` classifies, stays
match p { Some { value } => … }             // pattern — no separator at all, unchanged
Some { value: f(value) }                    // literal — `:` becomes `=`
```

and they co-occur, including on a single line — `stdlib/core.mtl:42` is
`Perhaps::Some { value } => Perhaps::Some { value: f(value) }`, a pattern and a literal in
one expression.

**Consequence: a naive regex sweep will corrupt declarations.** The migration wants either a
parser-driven rewrite (walk the AST, rewrite only `FieldInit` spans) or a careful pass with
the declaration and pattern forms explicitly excluded and the full test suite as the check.
The parser-driven option is strongly preferred and is cheap, since the parser already
distinguishes all three.

**This is a breaking surface change with no transition alias**, per RFC-0042 §D1's
precedent ("the language keeps only one binding introducer... does not carry a transition
alias") and RFC-0098's, which renamed three keywords the same way. Accepting both
spellings during a migration window is not proposed.

**Scheduling note (2026-07-24).** Pulled into v0.12.0, which also carries RFC-0071
(ownership and move semantics) — by far the more breaking of the two. Batching a small
breaking syntax change into a release that is already breaking is preferable to spending a
separate breaking release on it later.

**This is a breaking surface change with no transition alias**, per RFC-0042 §D1's
precedent ("the language keeps only one binding introducer... does not carry a transition
alias") and RFC-0098's, which renamed three keywords the same way. Accepting both
spellings during a migration window is not proposed.

---

## Alternatives Considered

- **Leave `field_init` alone and let RFC-0100 remove it.** The status quo ante, and the
  thing this RFC exists to stop doing — see Motivation. Still the outcome if this RFC is
  refused *and* RFC-0100 is accepted; the invariant then completes later, by a different
  route, having been unavailable in the meantime.
- **State the invariant with `field_init` as a permanent exception.** Materially weaker: a
  rule with one exception does not settle future "which separator?" questions cheaply,
  which is the invariant's main practical value.
- **Change `field_init` to `=` *and* adopt keyword arguments here too.** Rejected as
  re-bundling: keyword arguments carry a real grammar hazard (§2) and an open question
  about whether they belong in the spec at all. Keeping them in RFC-0100 is the point of
  the split.
- **Keep `:` and instead change the anonymous record former to match it** (`{ x: 1.0 }` as
  a value). Rejected — it fixes the mismatch in the wrong direction, preserving the
  grammar's only invariant violation and propagating it to a new construct rather than
  retiring it.

---

## Unresolved Questions

1. **Does `Point { x = 1.0 }` read as data when it is not?** Under RFC-0114, construction
   invokes `Construct::construct`, which may normalize — `SortedPair { small = 3, big = 1 }`
   yields `small = 1, big = 3`. Braces suggest an inert literal; a call-shaped form
   (RFC-0100) would signal that something runs. **This RFC does not resolve the tension, it
   inherits it** — the same surprise exists today with `:`, unchanged by the separator. It
   is recorded here because it is the strongest argument for RFC-0100's call-shaped
   construction, and splitting the RFCs should not make it easier to lose track of.
2. **Should the invariant itself be normative?** `colon-classifies-equals-defines.md` is a
   report and binds nothing. This RFC applies it to one site; whether the *rule* should be
   ratified so it settles future syntax questions by default is that document's own open
   question 1, not decided here.
3. ~~Does anything in the test corpus depend on the current spelling in a non-mechanical
   way?~~ **Resolved 2026-07-24 — verified against the fixtures and the parser, which was
   the one thing blocking acceptance.** Four checks:
   - **The parser never sees the separator.** `parse_expr`'s `struct_literal` branch takes
     `it.next()` for the name and `it.next()` for the value; `:` is a bare literal in the
     grammar rule, so pest emits no pair for it (`parser/mod.rs:1885-1895`). Changing the
     token therefore requires **zero parser changes** — grammar line only.
   - **Punning survives untouched.** `tests/.../43_shorthand_field.mtl` exercises
     `Point { x, y }`; the `("=" ~ expr)?` clause stays optional, so the fixture is
     unaffected. Only its explanatory comment ("desugars to `Point { x: x, y: y }`") needs
     rewording.
   - **No fixture currently writes `=` inside a literal brace**, so nothing that is a parse
     error today silently becomes valid.
   - **No negative test asserts the `:` spelling.** Nothing in `tests/` pins the separator
     as behaviour.

   So the migration is mechanical, subject to §3's caveat that a *regex* sweep is unsafe
   because declarations, patterns and literals share brace syntax — the rewrite must be
   parser-driven.

**Neither remaining question blocks acceptance, and it is worth being explicit about why**
rather than leaving a reader to infer it. Question 1 is *inherited, not created* — the
data-versus-computation tension exists identically today with `:`, so this RFC does not
change it in either direction. Question 2 is delegated by construction: whether the
separator invariant should be normative is `colon-classifies-equals-defines.md`'s own open
question, and this RFC applies the invariant to one site whatever that document decides.

---

## References

- `reports/syntax/colon-classifies-equals-defines.md` — the invariant, the fourteen-site
  grammar audit, and the open question 4 ("what if RFC-0100 is refused?") this split
  answers
- `internal/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` — the parent
  RFC; keeps call-shaped construction and general keyword arguments, and is independent of
  this one in both directions
- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` — its 2026-07-24
  amendment settles `{ x = 1.0 }` for anonymous record values, the form this RFC aligns
  nominal struct literals with
- `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md` — its
  §2 desugars a literal to `Self::construct(row)`; under this RFC that desugaring reads
  directly off the surface (`Point { x = 1.0 }` → `Point::construct({ x = 1.0 })`)
- `internal/rfcs/4-implemented/rfc-0098-surface-keyword-renames.md`,
  `internal/rfcs/4-implemented/rfc-0042-let-mut-bindings.md` §D1 — precedent
  for a surface rename shipping without a transition alias (§3)

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
