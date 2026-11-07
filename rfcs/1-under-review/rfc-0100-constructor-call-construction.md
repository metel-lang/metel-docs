---
id: rfc-0100
title: "Constructor-Call Construction"
date: '2026-07-13'
status: under-review
updated: '2026-11-07'
tracking: 'https://github.com/metel-lang/metel-core/issues/807'
---

> **Tracking added retroactively (2026-08-23).** This RFC reached under-review before
> the tracking-issue requirement existed (PROCESS.md, 2026-08-23); filed metel-core#807
> (design-settlement, no code — notes the interaction with RFC-0136, which resolves
> this RFC's own "is losing `f(x = 1)` acceptable" question as a side effect if it
> lands first).

> **Scheduled for v0.16.0 and widened (2026-11-07, language owner).** This RFC is part of the v0.16.0 stage "Call and record
> syntax" (metel-core#807, milestone 84). Keyword arguments are part of the call syntax of **every** function call, not a
> feature of constructors: section 2 is now normative and states the rules (section 2.1). The rules marked *proposed* there
> are drafted for review and are not yet accepted.

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
> (`reports/syntax/colon-classifies-equals-labels-walrus-binds.md`), keyword arguments are spelled
> `name = value`, and the collision cannot arise: keyword binding and type ascription use
> different tokens. §1, §2, §3 and §6 are revised to `=` throughout; §3 is rewritten to
> state the smaller collision `=` trades into (with `assign_expr`, not `asc_expr`) rather
> than the one it removes. The RFC stays under review because adopting `=` is itself a
> decision this revision proposes rather than one already taken — but the question in
> front of review is now "is `=` the right separator", not "should keyword arguments exist
> at all."

> **Previous Status — under review (2026-07-14).** Reconsidering whether general keyword arguments belong in the spec at all, given the collision with type ascription at call sites. *(Superseded above: that collision is separator-specific.)*

> **Previous Status — accepted (2026-07-14).** Reviewed and revised: found and fixed a real grammar collision between keyword arguments and type ascription (arg_list reordering fix), resolved all three remaining Unresolved Questions (evaluation order, aspect-method calls, overload resolution) against the actual implementation. No open questions block it.

> **Split in two (2026-11-07, language owner).** This RFC was one proposal with two pieces that lead to the same form.
> The first stays here: **`Type(args)` is the instantiation form of structs and enum variants**, positional like any
> call, and the brace literal is retired. The second moved to **RFC-0223** (Keyword Arguments at Every Call): the optional
> `Type(x = 0, y = 0)` keyword form, for every function call. Keyword arguments, their grammar position and the evaluation
> order are RFC-0223's. This RFC is scheduled for v0.16.0 (metel-core#807, milestone 84).

## Summary

**`Type(args)` is the instantiation form of structs and enum variants.** It is a call, so positional arguments bind
fields in declaration order exactly as for a function, and the brace literal `Type { field = value }` is retired (§5):

```metel
struct Point { x: i64, y: i64 }
let p := Point(1, 2);                // positional, like any call
let q := Point(x = 1, y = 2);        // the keyword form of RFC-0223, which lands in the same release
```

For a struct, `Type(args)` is a call of the constructor function that the `Construct` aspect (RFC-0114) provides (§7),
with a compiler-synthesized default for types that have no invariant. In v0.16.0 only the synthesized default exists: the
call builds the struct directly, and RFC-0114 is not part of the stage. For an enum variant, `Enum::Variant(args)` builds the
variant directly. The field shorthand `Type { x, y }` is retired with the brace form. Keyword arguments, `x = 0`, are
RFC-0223's; this RFC needs nothing from them to work positionally.

---

## Motivation

`Type { field: value }` free-standing struct literals are one of the more recognizable Rust tells in Metel's surface syntax. Most
languages, including every OOP-flavored one, construct values through a call-shaped constructor. A call is also what a later
`Construct` aspect (RFC-0114) needs, and with the brace form gone the only brace expression left is the anonymous record, which
RFC-0221's dotted labels depend on. Positional construction alone only reads well for one or two fields; the readable form for
more fields is the keyword argument of RFC-0223, a general call feature that this RFC does not define.

---

## 1. Construction syntax

Today:
```metel
struct IntBox { value: i64 }
let b := IntBox { value = 42 };

struct Token { public value: String, secret: String }
let t := Token { value = "x".to_string(), secret = "shh".to_string() };
```

Proposed:
```metel
struct IntBox { value: i64 }
let b := IntBox(value = 42);

struct Token { public value: String, secret: String }
let t := Token(value = "x".to_string(), secret = "shh".to_string());
```

The call is the only way to construct a struct. `IntBox { value = 42 }` is a compile error (§5), and the call
is a call of the constructor function that the `Construct` aspect provides (§7).

An enum variant with named fields is built the same way. Today it takes the brace form
(`enum_variant = ident ~ ("{" ~ struct_fields ~ "}")?`, and `Result::Ok { value = "42" }` in the fixtures):

```metel
enum Shape { Circle { r: f64 }, Rect { w: f64, h: f64 } }
let a := Shape::Rect(w = 2.0, h = 3.0);       // was Shape::Rect { w = 2.0, h = 3.0 }
let b := Shape::Circle(1.5);                  // one-field positional sugar, as for a struct
```

**The keyword spelling is `=`, not `:`.** That decision and its reasoning (the separator invariant) moved with keyword
arguments to RFC-0223.

**Positional rule.** A construction call follows the function rule (RFC-0223 section 2): positional arguments bind the fields in
declaration order, at any arity. With RFC-0223's keyword form field order at the call site is not load-bearing:
`Token(secret = "shh".to_string(), value = "x".to_string())` is equally valid. **Field shorthand is retired** (decided 2026-11-07):
`Point { x, y }` builds by name from variables, but `Point(x, y)` binds by position, so the migration rewrites it to the keyword
form `Point(x = x, y = y)` and the construction sweep runs after RFC-0223 is implemented.

## 2. Keyword arguments at every call

Moved to **RFC-0223** (Keyword Arguments at Every Call), 2026-11-07. This RFC no longer defines keyword arguments: the
call form `Type(x, y)` is positional on its own (section 1), and `Type(x = 0, y = 0)` is the keyword form RFC-0223 adds for every
call, constructors included. The two RFCs lead to the same final form and land in the same release.

## 3. The grammar position keyword arguments occupy, and what `=` costs

Moved to **RFC-0223** section 3, 2026-11-07.

## 4. Symmetry with pattern-matching destructuring

**The separator invariant does not reach destructuring, checked directly.** `enum_pattern =
{ ident ~ "::" ~ ident ~ ("{" ~ ident ~ ("," ~ ident)* ~ "}")? }` (`grammar.pest:263`) —
pattern field positions accept a bare `ident` and nothing else. There is no `field:
subpattern` renaming form in the grammar today, so patterns contain no separator at all in
field position, and §1's `:`-versus-`=` question simply has no site to apply to here. The
asymmetry argued below is therefore purely about braces-versus-parens.

`match x { IntBox { value } => ... }`-style destructuring **keeps its current `{ field }` syntax, unchanged by this RFC.** Construction and destructuring diverge in spelling after this RFC ships — `Type(value = 42)` to build, `Type { value }` to take apart. This is a deliberate choice, not an oversight: destructuring's `{ field }` shape already reads as "match against this shape" (consistent with `enum`-variant destructuring, which also uses `{ field }` when a variant carries named fields), and forcing it into call-shape would suggest destructuring *invokes* something, which it doesn't. The asymmetry is judged acceptable because the two operations are already conceptually distinct (construction produces a value; destructuring matches an existing one), not a case where readers would expect symmetry in the first place.

## 5. Coexistence with the old literal syntax

**Brace construction of a struct or an enum struct-variant is prohibited.** `Type { field = value }` and
`Enum::Variant { field = value }` in expression position are errors (the ordinary parse error, see the scope note below). The rule applies to every struct, whether or not it
implements `Construct` (§7), and to every enum variant, for these reasons:

1. **One spelling per action** (below). This covers structs and variants alike.
2. **Braces read as inert data, but construction runs code.** `construct` may normalise or validate, so
   `SortedPair { small = 3, big = 1 }` can evaluate to `small = 1, big = 3`. RFC-0114 §2 records this as the
   cost the brace form carries and the call form does not. A call reads as a call. (Structs only: a variant
   has no `construct`.)
3. **The spelling must not depend on whether a type has an invariant.** If only types with a non-default
   `Construct` impl required the call form (RFC-0114's fallback), adding an invariant to a type would change
   every construction site of it. Under this rule it changes none. (Structs only.)
4. **No brace expression is left except the anonymous record.** A brace group in expression position is then
   always an anonymous record or a block, and never a construction that needs a type path to be read.

**Scope for v0.16.0 (2026-11-07).** Reasons 2 and 3 assume a `construct` that can run code (RFC-0114), which is not part of the
stage: with only the synthesized default, the brace form and the call form behave identically. The case for retiring braces in
v0.16.0 therefore rests on reasons 1 and 4: one spelling per action, and no brace expression left but the anonymous record, which
RFC-0221 needs. The call is also what a later `Construct` requires, so nothing is lost. Diagnostic (decided 2026-11-07): `Type { x = 1 }`
in expression position is the ordinary parse error, with no promised targeted message, as for RFC-0218 and RFC-0183.

Braces after a type name remain legal in declarations (`struct Point { … }`, `enum Shape { Rect { … } }`) and
in patterns (§4). They are no longer an expression.

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

Moved to **RFC-0223** section 4, 2026-11-07. Construction calls follow those rules unchanged.

## 7. Construction is a call of `Construct::construct`

**Scope for v0.16.0 (decided 2026-11-07, language owner): construction goes through the compiler-synthesized default
only.** `Type(args)` builds the struct directly, which is exactly what the synthesized default does (`Error = !`,
`construct(row) { Ok(row) }`, compiled away). The `Construct` aspect, a written `construct`, fallible construction
(item 3), the minting-site rule (item 4) and `ConstructUnchecked` are not part of v0.16.0 and stay with RFC-0114,
which is not in the stage. Items 1, 2 (as the default), 5 (as a direct build from a record of exactly the type's row),
6 and the enum rule apply. When RFC-0114 is accepted later, the call becomes a call of `Construct::construct`
without changing any call site, because the default compiles away.

`Type(args)` is not a special form. It is a call of the constructor function that the `Construct` aspect
(RFC-0114) provides, after the arguments are collected into the type's row:

```metel
IntBox(value = 42)                  // IntBox::construct({ value = 42 })
SortedPair(small = 3, big = 1)      // SortedPair::construct({ small = 3, big = 1 })
SortedPair(3, 1)                    // positional sugar, assigned to labels first (§1), then the same call
```

The record spelling inside `construct(…)` follows whichever record-literal syntax is current (RFC-0221 is
the draft that dots the fields of anonymous records). Structs are not affected by that choice: a struct's
field names here are parameter names, not labels.

1. **Collection.** Keyword arguments become the row's labels. A positional argument is assigned to a label
   by declaration order, as for a function (§1). The row must be exactly the type's complete row, no more and no
   fewer. Evaluation order is §6's.
2. **No impl to write.** A struct with no invariant gets the compiler-synthesized default
   (`type Error = !`, `construct(row) { Ok(row) }`, RFC-0114 §1), which compiles away. Its author writes
   nothing and sees only the call.
3. **Result handling** is RFC-0114 §5's, unchanged. When `Self::Error` is `!`, the call yields a bare `Self`.
   Otherwise it yields `Result<Self, Self::Error>` and the caller handles it with `?`, `match` or
   `.unwrap_or`.
4. **The only minting site.** A row becomes a `Self` inside `construct` and `construct_unchecked` and
   nowhere else (RFC-0114 §1.1). `Type::construct(row)` can be written explicitly and means the same as the
   call.
5. **From a record.** *(v0.16.0 scope, decided 2026-11-07: `Type(..r)` appears alone, as the only argument; `Type(..r, x = 5)`
   is an error until RFC-0191's override semantics are settled.)* A record value of exactly the type's row is passed with a spread:
   `Type(..r)` is `Type::construct(r)`. The `..` marks the argument as a row and not as the value of a
   field, so `Wrapper(r)` for a one-field struct whose field is itself a record keeps its §1 meaning. This
   is the form RFC-0114 open question 9 left open for `FromRecord`, and like `construct` it has no
   separate body, so it cannot bypass an invariant.
6. **Visibility.** A call must be able to name every label it supplies. A struct with private fields cannot
   be constructed by a call from outside its module, which is the rule the brace literal has today and is
   not changed here. RFC-0114 open question 8 asks whether that rule is enough once `construct` is
   public, and stays RFC-0114's.

**Enum variants.** `Enum::Variant(args)` collects keyword and positional arguments exactly as items 1 and 6
do, and builds the variant directly. Enums have no `Construct` (RFC-0114 §8 scopes it to structs), so items
2 to 5 do not apply to them, and there is no spread form: a variant has no record to be built from.

**Dependency on RFC-0114.** RFC-0114 is `0-draft`. This section states the contract the call has with it.
If RFC-0114 is not accepted, `Type(args)` builds the struct directly, the synthesized default is the whole
behaviour, and nothing else in this RFC changes. RFC-0114 stays independent of this RFC in the other
direction (its §2): it is satisfied by any surface form that desugars to `construct`.

---

## Alternatives Considered

- **Positional-only construction, no keyword arguments at all.** Rejected as the end state: unreadable beyond two or three fields and silently order-dependent in a way the named-field literal never was. It is this RFC's own floor, and RFC-0223 adds the keyword form for every call.
- **Struct-only keyword arguments.** Rejected; see RFC-0223 (keyword arguments are a property of every call).
- **Keep `Type { field = value }` as a second valid spelling alongside `Type(field = value)`.** The lower-risk option, and the one worth revisiting if migration friction during review turns out to be worse than expected — noted here as the fallback, not the default, per RFC-0042's own precedent against carrying a permanent transition alias (§5). RFC-0114 §2 shows it would be sound, since a brace literal that desugars to `construct` is not a bypass. §5 prohibits it anyway, because braces hide that construction runs code and because the spelling should not change when a type gains an invariant.
- **Prohibit the brace form only for types with a non-default `Construct` impl** (RFC-0114's fallback). Rejected (§5, reason 3): adding an invariant to a type would then change every construction site.
- **Making destructuring call-shaped too, for symmetry with construction.** Rejected (§4) — `match Type(value) => ...` reads as invoking something, not matching against a shape, and would be a bigger, more confusing change than the asymmetry it "fixes."
- **The keyword spelling and its disambiguation alternatives** (`name: value`, casing, parenthesised ascription): moved with keyword arguments to RFC-0223.

## Unresolved Questions

Open after the split of 2026-11-07 (the questions about keyword arguments, the `=` separator, the grammar prototype and positional-only
parameters moved to RFC-0223):

- ~~**Is losing `f(x = 1)` as a positional bare assignment acceptable?**~~ **Resolved 2026-11-07 by RFC-0183:** assignment is a statement,
  so there is no positional-assignment reading to lose. RFC-0183 lands before this RFC in the v0.16.0 sweep order.
- ~~**Field shorthand** `Type { x, y }`.~~ **Resolved 2026-11-07:** retired with the brace form; the migration produces the keyword form
  `Type(x = x, y = y)` (§1).
- ~~**The positional rule.**~~ **Resolved 2026-11-07:** the function rule, declaration order at any arity (§1).
- ~~**Diagnostic for the old brace form.**~~ **Resolved 2026-11-07:** the ordinary parse error (§5).
- **Spread in call arguments (§7 item 5).** v0.16.0: `Type(..r)` alone; `Type(..r, x = 5)` is an error until RFC-0191's override
  semantics are settled. It must still be checked against RFC-0125's pack expansion, which also uses `..`.
- **Migration.** The rewrite is `Type { f = v }` to `Type(f = v)` and `Type { x, y }` to `Type(x = x, y = y)`, by a parser-based tool
  (struct literals, blocks and records look alike), swept after RFC-0223 is implemented. About 1378 brace-construction lines in 684
  `.mtl` files in metel-core on 2026-11-07 (rough), plus the spec, docs and RFCs.
- **RFC-0216's residual construction.** `T.{ ..R } { entries }` (RFC-0216 §2) is a brace expression after a type head, so §5 prohibits
  it. It should take the spread call, `T.{ ..R }(..record)`, with the same defining-module restriction. RFC-0216 would be amended; this
  RFC does not decide it.
- **The `Construct` items of §7** (result handling, the minting site, an explicit `Type::construct(row)`) are RFC-0114's and dormant in v0.16.0.

---

## References

- RFC-0223 (Keyword Arguments at Every Call) — the other half of this RFC's split, 2026-11-07: the optional `Type(x = 0, y = 0)` keyword form
  for every call.
- RFC-0023 (Type Ascription vs Turbofish) — the `expr: Type` production the `:` spelling collided with
  (§3, superseded half). **Under `=` this RFC does not touch RFC-0023 in any position.**
- `reports/syntax/colon-classifies-equals-labels-walrus-binds.md` — the separator invariant `=` is adopted from (§1),
  and its fourteen-site grammar audit. Its recommendation that this RFC switch separators is now split
  across two RFCs: keyword arguments here, `field_init` in RFC-0115.
- RFC-0115 (Field Initializer Separator) — the separator half of this RFC, split out 2026-07-24. Keeps
  brace literals and changes only `field_init`'s `:` to `=`. Independent of this RFC in both directions:
  it does not need call-shaped construction, and this RFC does not need it. If both land, `field_init`
  ceases to exist and RFC-0115 becomes moot rather than conflicting.
- RFC-0042 (`var` for Mutable Bindings) — precedent cited in §5 for retiring an old spelling outright rather than keeping a permanent transition alias.
- RFC-0044 (Explicit Receiver Semantics) — receiver-form distinctions confirmed against §6's aspect-method-call resolution.
- RFC-0091 (Linear Records) — uses `record { field: Type }` as a *type-level* notation (not a construction-site expression); related surface shape, but a different grammar position, not directly amended by this RFC. Its `:` is classification and conforms to §1's invariant unchanged. **Note (2026-07-24):** RFC-0090 has since dropped the `record` keyword from the anonymous former, so RFC-0091's ~20 uses of it are now stale spelling — a mechanical sweep not yet done.
- RFC-0114 (Constructor Aspect and Canonical Construction) — supplies `Construct::construct`, the function
  `Type(args)` calls (§7), the synthesized default, and the result-handling rule. `0-draft`; a soft dependency
  (§7). RFC-0114 does not require this RFC (its §2), and its fallback of banning the literal only for types with
  a non-default impl is rejected here (§5).
- RFC-0221 (Dotted Row Labels, under review) — dots the labels of rows (anonymous records and projection lists) only. Struct and enum
  construction here uses parameter names and is unaffected (§7); `Type(..r)` takes a dotted record.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0099 (Dot-Separated Module Paths) — sibling surface-syntax RFC from the same review; independent of this one.
- RFC-0101 (Grammar-Enforced Naming Case Conventions) — reviewed alongside this RFC. It was cited as
  narrowing the `:` spelling's ascription trade-off; **under `=` that trade-off does not exist and the two
  RFCs are simply independent** (§3).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
