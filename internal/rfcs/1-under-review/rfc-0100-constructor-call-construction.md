---
id: rfc-0100
title: "Constructor-Call Construction"
date: '2026-07-13'
status: under-review
target:
updated: '2026-07-24'
---

> **Split 2026-07-24, later the same day.** The separator half of this RFC — changing
> `field_init` from `ident ":" expr` to `ident "=" expr` — is extracted into
> **RFC-0115 (Field Initializer Separator)** and is no longer this RFC's to deliver.
> The two were bundled only because retiring brace literals happened to remove the
> grammar's single separator-invariant violation as a side effect; that made a settled,
> dependency-free question hostage to this RFC's own unsettled one. **RFC-0115 keeps
> braces and changes only the separator; this RFC keeps call-shaped construction and
> general keyword arguments.** Neither blocks the other, and this RFC's §5 case is
> genuinely weaker for the split — see §5, which no longer gets to claim the
> invariant as a reason to retire the literal.
>
> **Status — under review, revised 2026-07-24.** **The reason this RFC was reopened is
> dissolved, not answered on its own terms.** The ascription collision that motivated
> reopening was a consequence of spelling keyword arguments `name: value`, not of keyword
> arguments as a feature. Under the separator invariant `:` classifies, `=` defines
> (`reports/syntax/colon-classifies-equals-defines.md`), keyword arguments are spelled
> `name = value`, and the collision cannot arise: keyword binding and type ascription use
> different tokens. §1, §2, §3 and §6 are revised to `=` throughout; §3 is rewritten to
> state the smaller collision `=` trades into (with `assign_expr`, not `asc_expr`) rather
> than the one it removes. The RFC stays under review because adopting `=` is itself a
> decision this revision proposes rather than one already taken — but the question in
> front of review is now "is `=` the right separator", not "should keyword arguments exist
> at all."

> **Previous Status — under review (2026-07-14).** Reconsidering whether general keyword arguments belong in the spec at all, given the collision with type ascription at call sites. *(Superseded above: that collision is separator-specific.)*

> **Previous Status — accepted (2026-07-14).** Reviewed and revised: found and fixed a real grammar collision between keyword arguments and type ascription (arg_list reordering fix), resolved all three remaining Unresolved Questions (evaluation order, aspect-method calls, overload resolution) against the actual implementation. No open questions block it.

## Summary

`Type(args)` call-shaped syntax replaces `Type { field: value }` struct literals at construction sites. The RFC's real deliverable isn't the struct-literal rename — it's **general keyword arguments for function calls**, spelled `name = value`, since positional-only construction is unreadable beyond one or two fields, and struct construction is just the first, motivating use of that mechanism. Like RFC-0099, this is not a pure token/reordering change: keyword arguments occupy a grammar position already spoken for, and this RFC has to settle that before the feature is well-formed (§3) — though the `=` spelling adopted here trades the original, severe collision with type ascription (RFC-0023) for a much smaller one with assignment-as-an-expression. Raises (and resolves) a symmetry question against pattern-matching destructuring, which keeps its current syntax unchanged.

---

## Motivation

`Type { field: value }` free-standing struct literals are one of the more recognizable Rust tells in Metel's surface syntax — most languages, including every OOP-flavored one, construct values through a call-shaped constructor. But a naive rename to `Type(value1, value2, ...)` only reads well for one or two fields; anything larger needs field names at the call site to stay readable, which means this RFC can't just rename struct construction — it has to introduce keyword arguments as a real, general call-syntax feature, with struct construction as the first consumer rather than a special case bolted onto structs alone.

---

## 1. Construction syntax

Today:
```metel
struct IntBox { value: i64 }
let b = IntBox { value = 42 };

struct Token { public value: String, secret: String }
let t = Token { value = "x".to_string(), secret = "shh".to_string() };
```

Proposed:
```metel
struct IntBox { value: i64 }
let b = IntBox(value = 42);

struct Token { public value: String, secret: String }
let t = Token(value = "x".to_string(), secret = "shh".to_string());
```

**`=`, not `:`, and for a reason that is not aesthetic.** A keyword argument binds a value
to a name — it *defines*, it does not *classify* — so it takes `=` under the separator
invariant `reports/syntax/colon-classifies-equals-defines.md` audits the grammar against
(`:` classifies: `x: T`, `T: Bound`; `=` defines or equates: `let x = e`,
`type X = Concrete`, `Deref<Target = Node>`). **The invariant applies to keyword arguments
on its own merits, independently of RFC-0115** — a keyword argument would take `=` whether
or not `field_init` ever changes, because binding a value to a name is defining in either
construct. The split does not weaken this section; it only means this RFC is no longer the
vehicle that *completes* the invariant.

Field order at the construction site becomes non-load-bearing — `Token(secret = "shh".to_string(), value = "x".to_string())` is equally valid, matching keyword-argument semantics in every language that has them (Python, Kotlin, F#, Ada). Positional arguments remain available for the common one-or-two-field case: `IntBox(42)` is valid when there's exactly one field and no ambiguity about which one it binds to; mixing positional and keyword arguments in one call follows the same rule most languages use (positional arguments must precede keyword ones).

## 2. Keyword arguments as a general call-syntax feature

This is the section that makes this RFC bigger than "rename struct literals." Once `name = value` is legal at a struct's construction call site, the natural and more valuable generalization is allowing it at *any* function call:

```metel
fun connect(host: String, port: i64, timeout: i64) -> Connection { ... }

connect(host = "db.local", port = 5432, timeout = 30);
connect("db.local", port = 5432, timeout = 30);   // positional + keyword mix
```

Note that the declaration side is untouched and stays `:` — `host: String` classifies, as
it always has. Only the *call* side, where a value is bound to a name, takes `=`. The two
sides of a function reading differently is the invariant working, not a wart: they are
doing genuinely different things.

Parameter names become part of a function's public call-site surface, the same way they already are conceptually (every existing signature already names its parameters — this RFC exposes that naming at the call site rather than introducing new declaration syntax). Keyword arguments are optional at every call site — purely positional calls remain valid and unchanged for any function, including ones defined before this RFC.

## 3. The grammar position keyword arguments occupy, and what `=` costs

**Rewritten 2026-07-24.** The previous version of this section fixed a collision with type
ascription that the `=` spelling (§1) removes outright. That analysis is kept below, under
"Superseded", because it is what the RFC was reopened over and the record should show why
the reopening no longer bites — not because it still describes the design.

Keyword arguments are still not a pure addition to the grammar. `arg_list = { expr ~ ("," ~
expr)* ~ ","? }` (`grammar.pest:182`) makes every call argument a plain `expr`, and `expr =
{ assign_expr }` (line 146) puts **assignment** at the very top of the expression chain:
`assign_expr = { unary_expr ~ assign_op ~ assign_expr | or_expr }` (line 148), with
`assign_op = { "+=" | "-=" | "*=" | "/=" | "%=" | ("=" ~ !"=") }` (line 149). So `f(x = 1)`
already parses today — as one positional argument whose value is an assignment expression.

**Fix: the same shape of fix the previous version designed, retargeted to `=`** —
restructure `arg_list` to try a keyword-argument shape before falling through to plain
`expr`:

```
arg_list    = { call_arg ~ ("," ~ call_arg)* ~ ","? }
call_arg    = { keyword_arg | expr }
keyword_arg = { ident ~ "=" ~ !"=" ~ expr }
```

The `!"="` lookahead mirrors `assign_op`'s own and keeps `f(x == y)` from even attempting
the keyword alternative. It is a cheapness/style choice, not a correctness one — without
it, PEG would try `ident ~ "="` against `x ==`, fail to parse `= y` as an `expr`, backtrack
to the `expr` alternative, and reach the same answer by a longer route.

**The cost, stated plainly and much smaller than the one this replaces: a bare assignment
can no longer be passed as a positional argument.** `f(x = 1)` now means "pass `1` as the
argument named `x`", never "assign `1` to `x` and pass the result." This is the C `if (x =
5)` footgun, which several languages ban outright; Metel's assignment is an expression
today (`assign_expr` is in the expression chain), so this is a real narrowing, but of a
form with no known legitimate use. **Compound assignment is unaffected** — `f(x += 1)`
never matches `ident ~ "="`, so it still parses as today.

**What `=` refunds, relative to the previous fix.** Type ascription as a bare positional
call argument comes back: `f(x: SomeType)` again means "pass the expression `x`, ascribed
to `SomeType`", exactly as `asc_expr = { unary_expr ~ (":" ~ type_expr)? }` (line 167) has
always allowed. RFC-0023 is not narrowed by this RFC at all any more, in any position.

**RFC-0101 (Grammar-Enforced Naming Case Conventions) is no longer load-bearing here.**
It was cited previously to make the ascription trade-off negligible in practice; with the
trade-off gone, the two RFCs are simply independent. Nothing about `=` depends on
PascalCase carrying meaning.

<details>
<summary><strong>Superseded — the ascription collision, as analysed 2026-07-14</strong></summary>

Under the `name: value` spelling, every call argument resolved down through `asc_expr = {
unary_expr ~ (":" ~ type_expr)? }` — the existing type-ascription expression (`expr: Type`,
RFC-0023). Any bare identifier is a syntactically valid zero-arg `type_expr`, so
`Foo(bar: Baz)` was genuinely ambiguous in the grammar's own terms: keyword argument `bar`
bound to value `Baz`, or one positional argument `bar` ascribed to type `Baz`? PEG's
ordered choice commits to the first match, so `bar: Baz` was always consumed as ascription,
and `name: value` would never have parsed as intended without a fix.

The fix was `call_arg = { (ident ~ ":" ~ expr) | expr }`, keyword shape first — with the
accepted cost that a bare ascribed variable could no longer be a positional call argument.
**That cost, and the reconsideration it triggered ("do keyword arguments belong in the spec
at all?"), were both consequences of the separator, not of the feature.** Both are gone
under `=`.

</details>

## 4. Symmetry with pattern-matching destructuring

**The separator invariant does not reach destructuring, checked directly.** `enum_pattern =
{ ident ~ "::" ~ ident ~ ("{" ~ ident ~ ("," ~ ident)* ~ "}")? }` (`grammar.pest:263`) —
pattern field positions accept a bare `ident` and nothing else. There is no `field:
subpattern` renaming form in the grammar today, so patterns contain no separator at all in
field position, and §1's `:`-versus-`=` question simply has no site to apply to here. The
asymmetry argued below is therefore purely about braces-versus-parens.

`match x { IntBox { value } => ... }`-style destructuring **keeps its current `{ field }` syntax, unchanged by this RFC.** Construction and destructuring diverge in spelling after this RFC ships — `Type(value = 42)` to build, `Type { value }` to take apart. This is a deliberate choice, not an oversight: destructuring's `{ field }` shape already reads as "match against this shape" (consistent with `enum`-variant destructuring, which also uses `{ field }` when a variant carries named fields), and forcing it into call-shape would suggest destructuring *invokes* something, which it doesn't. The asymmetry is judged acceptable because the two operations are already conceptually distinct (construction produces a value; destructuring matches an existing one), not a case where readers would expect symmetry in the first place.

## 5. Coexistence with the old literal syntax

**The old `Type { field: value }` literal syntax is retired, not kept as a second valid spelling.** Keeping both was considered (see Alternatives) and rejected: having two equally-valid ways to construct any struct is a worse ergonomic outcome than a one-time mechanical migration, and this project's own precedent (RFC-0042 §D1: "the language keeps only one binding introducer... does not carry a transition alias") already establishes that a clean single spelling is preferred over a permanent dual-syntax compromise when a rename like this ships.

**An argument this section briefly had, and lost in the split — recorded rather than
quietly dropped.** For part of 2026-07-24 this RFC also claimed a second, independent
reason to retire the literal: `field_init` is the only site in the grammar where `:`
introduces a value, so retiring the literal would remove the language's single
separator-invariant violation for free. **RFC-0115 now does that directly, keeping the
braces**, so this RFC no longer gets the credit — and, more to the point, the invariant is
no longer at risk if this RFC is refused. That is a real weakening of the case for §5:
retiring the literal must now be justified on the "one spelling per action" ground alone,
which is the ground it was originally proposed on. The split was made knowing this.

## 6. Evaluation order, aspect methods, and overload resolution

Three questions an earlier draft of this RFC left open, resolved here against the actual implementation
rather than by analogy alone. **All three are separator-independent** — none of them turns on `:` versus
`=` — so the 2026-07-24 revision leaves their substance untouched and only restates their examples in the
adopted spelling:

**Evaluation order.** `evaluator/mod.rs`'s existing `TypedExpr::Call` handling evaluates arguments via
`args.iter().map(|a| eval_expr(a, ...))` — strict left-to-right over the stored argument list, which today
(positional-only, no reordering possible) is naturally call-site text order. Keyword arguments break the
assumption that "stored order" and "written order" are the same thing, since `f(port = getPort(), host =
getHost())` writes `port` first but binds to a parameter declared second. **Resolution: evaluation happens
in two separate steps, not one** — first, evaluate every argument expression strictly in the order written
at the call site (left to right, exactly as today, regardless of position vs. keyword), producing a list of
already-computed values; only then re-map those *values* (never the expressions) onto the callee's declared
parameter positions for the actual call. Reordering the expressions themselves to declaration order before
evaluating them, instead, would silently run `getPort()` before `getHost()` despite it being written second
— an easy mistake to make, invisible to any type-only test, and exactly the mistake most languages with
keyword arguments (Python, Swift, Kotlin) are careful to avoid.

**Aspect-method calls.** No special case: the receiver (`self`) is always positional, supplied by the
expression before the dot, and can never be targeted by a keyword argument — `self` is a reserved keyword,
so it can't collide with an ordinary parameter name either. Every parameter after `self` is an ordinary
named parameter, structurally identical to a free function's from this RFC's perspective. Keyword arguments
apply to aspect-method calls exactly as they do to free functions, confirmed against RFC-0044's three
receiver forms (`self`, `&self`, `&var self` post-RFC-0098) — none of which interact with argument naming at
all.

**Overload resolution.** `overload.rs`'s own doc comment settles the general rule already in force:
resolution is "exact-match only... argument types must equal a candidate's parameter types exactly" — by
full parameter type list, not merely argument count. Keyword arguments extend this rather than replace it:
for each candidate overload, the call's keyword-named arguments must name-match some subset of *that
candidate's own* declared parameter names (any remaining slots filled by leftover positional arguments, in
order), and the resulting per-slot argument types must exact-match that candidate's parameter types — the
same rule as today, with keyword names doing the slot assignment instead of pure position. A keyword name
absent from a candidate's own parameter list disqualifies that candidate for the call, the same way an
argument-count or type mismatch already does. Checked against the real overloaded natives this RFC's
Unresolved Questions cited hypothetically: `assert(cond: boolean)` and `assert(cond: boolean, msg: String)`
(`stdlib/core.mtl:336-337`) both have real, distinct declared parameter names, so `assert(cond = true, msg =
"x")` resolves to the two-parameter overload by the rule above with no special-casing needed. (Those two
signatures are quoted in *declaration* form, which keeps `:` — `cond: boolean` classifies. Only the call
site takes `=`.)

---

## Alternatives Considered

- **Positional-only construction (`IntBox(42)`, no keyword arguments at all).** Rejected as the primary proposal — unreadable for any struct with more than two or three fields, and silently order-dependent in a way today's named-field literal never was. Kept as sugar for the single-field case (§1).
- **Struct-only keyword arguments, not a general call-syntax feature.** Rejected: this would need its own separate desugaring/typechecking path distinct from ordinary function calls for no real benefit, when generalizing costs little extra and gives every function call the same ergonomic win.
- **Keep `Type { field: value }` as a second valid spelling alongside `Type(field = value)`.** The lower-risk option, and the one worth revisiting if migration friction during review turns out to be worse than expected — noted here as the fallback, not the default, per RFC-0042's own precedent against carrying a permanent transition alias (§5).
- **Making destructuring call-shaped too, for symmetry with construction.** Rejected (§4) — `match Type(value) => ...` reads as invoking something, not matching against a shape, and would be a bigger, more confusing change than the asymmetry it "fixes."
- **Keyword arguments spelled `name: value`** (the original proposal, 2026-07-13 through 2026-07-23).
  Rejected 2026-07-24 in favour of `=`: it violates the separator invariant (§1), it collides head-on with
  type ascription and forces the narrowing §3's superseded half describes, and that collision is what got
  this RFC reopened. **Its one real advantage is precedent** — Swift and C# both spell keyword arguments
  with `:`, and a reader arriving from either will find `=` less familiar. Python, Kotlin, F# and Ada split
  the other way. Precedent alone does not outweigh a grammar-wide invariant plus a removed collision, but
  the trade is genuine rather than one-sided.
- **Keyword-argument-vs-ascription disambiguation alternatives** (casing-based, requiring parens around nested ascription, a distinct marker token) — considered while `:` was still the proposed separator; all are moot under `=`, which removes the ambiguity rather than disambiguating it. See §3's superseded half.

---

## Unresolved Questions

**Rewritten 2026-07-24.** The three questions this section carried are all downstream of the
`:` spelling, and all three lapse under `=`:

1. ~~Should Metel keep only constructor-call syntax and drop general keyword arguments?~~
   **Lapsed.** The case for dropping them rested on the ascription collision, which was
   separator-specific (§3).
2. ~~Is removing bare type-ascription from positional call arguments an acceptable cost?~~
   **Lapsed — the cost is not incurred.** Ascription is untouched in every position.
3. ~~Should new surface syntax be admitted when it weakens an already-specified construct?~~
   **Still a real question, but it no longer applies to this RFC**, which now weakens
   nothing already specified. Worth carrying somewhere corpus-wide rather than dying here.

What actually remains open:

- **Is `=` the right separator?** This revision proposes it; review has not accepted it.
  The honest case against is precedent (Swift, C#), stated in Alternatives.
- **Is losing `f(x = 1)` as a positional bare assignment acceptable?** Argued in §3 as a
  benefit — it is the C `if (x = 5)` footgun — but Metel's assignment is a genuine
  expression today, and this has **not** been checked against existing test fixtures. That
  check is cheap and should happen before acceptance rather than after.
- **The `arg_list`/`call_arg`/`keyword_arg` restructuring in §3 is designed from grammar
  reading, not from a built prototype.** Same caveat the record-syntax work carries: pest's
  behaviour under the new ordering is predicted, not observed.
- **Does retiring the literal need a migration story for existing `.mtl` sources?**
  Unaddressed throughout, and the one piece of this RFC that is pure mechanical work rather
  than design.

Evaluation order, aspect-method calls, and overload resolution stay resolved in §6 — and
are now known to be separator-independent, so this revision does not reopen them.

---

## References

- RFC-0023 (Type Ascription vs Turbofish) — the `expr: Type` production the `:` spelling collided with
  (§3, superseded half). **Under `=` this RFC does not touch RFC-0023 in any position.**
- `reports/syntax/colon-classifies-equals-defines.md` — the separator invariant `=` is adopted from (§1),
  and its fourteen-site grammar audit. Its recommendation that this RFC switch separators is now split
  across two RFCs: keyword arguments here, `field_init` in RFC-0115.
- RFC-0115 (Field Initializer Separator) — the separator half of this RFC, split out 2026-07-24. Keeps
  brace literals and changes only `field_init`'s `:` to `=`. Independent of this RFC in both directions:
  it does not need call-shaped construction, and this RFC does not need it. If both land, `field_init`
  ceases to exist and RFC-0115 becomes moot rather than conflicting.
- RFC-0042 (`var` for Mutable Bindings) — precedent cited in §5 for retiring an old spelling outright rather than keeping a permanent transition alias.
- RFC-0044 (Explicit Receiver Semantics) — receiver-form distinctions confirmed against §6's aspect-method-call resolution.
- RFC-0091 (Linear Records) — uses `record { field: Type }` as a *type-level* notation (not a construction-site expression); related surface shape, but a different grammar position, not directly amended by this RFC. Its `:` is classification and conforms to §1's invariant unchanged. **Note (2026-07-24):** RFC-0090 has since dropped the `record` keyword from the anonymous former, so RFC-0091's ~20 uses of it are now stale spelling — a mechanical sweep not yet done.
- RFC-0114 (Constructor Aspect and Canonical Construction) — the downstream consumer: it makes
  `Type(args)` desugar to `Self::construct(row)`, so this RFC's status directly gates its §2. Its own
  fallback (banning the bare literal only for types with a non-default `Construct` impl, should this RFC be
  refused) is not worked out there.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0099 (Dot-Separated Module Paths) — sibling surface-syntax RFC from the same review; independent of this one.
- RFC-0101 (Grammar-Enforced Naming Case Conventions) — reviewed alongside this RFC. It was cited as
  narrowing the `:` spelling's ascription trade-off; **under `=` that trade-off does not exist and the two
  RFCs are simply independent** (§3).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
