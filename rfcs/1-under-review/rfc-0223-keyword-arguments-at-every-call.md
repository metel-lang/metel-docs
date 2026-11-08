---
id: rfc-0223
title: "Keyword Arguments at Every Call"
date: '2026-11-07'
status: under-review
updated: '2026-11-07'
tracking: 'https://github.com/metel-lang/metel-core/issues/1854'
---

> **Split out of RFC-0100 (2026-11-07, language owner).** RFC-0100 was one proposal with two pieces that lead to the same
> form. This RFC is the second: keyword arguments at every call. RFC-0100 keeps the first: `Type(args)` as the instantiation
> form of structs and enum variants. Sections 1 to 3 below are the text of RFC-0100's sections 2, 3 and 6, with section 2
> (the rules) proposed and unreviewed.

> **Status — under review (2026-11-07).** Split out of RFC-0100 on 2026-11-07 and committed to the v0.16.0 stage Call and record syntax (metel-core#1854); the rules of section 2 are proposed and review is open.

## Summary

**Keyword arguments `name = value` are part of the call syntax of every function.** The declaration side keeps `:`
(`host: String` classifies); only the call side, where a value is bound to a name, takes `=`. Positional arguments bind the
leading parameters in order, keyword arguments bind the rest by name, and a purely positional call stays valid.

```metel
fun connect(host: String, port: i64, timeout: i64) -> Connection { ... }

connect(host = "db.local", port = 5432, timeout = 30);
connect("db.local", port = 5432, timeout = 30);   // positional + keyword mix
```

It applies to free functions, associated functions, methods after the receiver, aspect methods and constructor calls
(RFC-0100). It depends on RFC-0183 (assignment is a statement), so that `f(x = 1)` is never an assignment.

---

## Motivation

Positional-only calls are unreadable beyond two or three arguments and silently order-dependent. Struct construction
(RFC-0100) is the use that motivated the mechanism, but every function with several parameters of the same type benefits,
and Python, Kotlin, F# and Ada all have it. Making it a property of every call, and not of constructors, avoids a second
desugaring path for structs and gives the call form of RFC-0100 its readable half.

---

## 1. The rule and its examples


**Keyword arguments are part of the call syntax of every function** (decided in principle 2026-11-07, language owner),
not a feature of constructors. Struct construction was the first use that motivated the mechanism, and it is a call like any other:

```metel
fun connect(host: String, port: i64, timeout: i64) -> Connection { ... }

connect(host = "db.local", port = 5432, timeout = 30);
connect("db.local", port = 5432, timeout = 30);   // positional + keyword mix
```

Note that the declaration side is untouched and stays `:` — `host: String` classifies, as
it always has. Only the *call* side, where a value is bound to a name, takes `=`. The two
sides of a function reading differently is the invariant working, not a wart: they are
doing genuinely different things.

**`=`, not `:`, for a reason that is not aesthetic.**  A keyword argument binds a value
to a name — it *defines*, it does not *classify* — so it takes `=` under the separator
invariant `reports/syntax/colon-classifies-equals-labels-walrus-binds.md` audits the grammar against
(`:` classifies: `x: T`, `T: Bound`; `=` defines or equates: `let x = e`,
`type X = Concrete`, `Deref<Target = Node>`). **The invariant applies to keyword arguments
on its own merits, independently of RFC-0115** — a keyword argument would take `=` whether
or not `field_init` ever changes, because binding a value to a name is defining in either
construct.



## 2. Rules (proposed 2026-11-07, for review)

1. **Binding.** A keyword argument `name = value` binds the callee's parameter `name`. Positional arguments bind the leading
   parameters in order; keyword arguments bind the rest by name. Positional arguments come first.
2. **Each parameter once.** A keyword that names a parameter already bound positionally, a repeated keyword, and an unknown
   name are errors. The unknown-name error lists the callee's parameter names.
3. **Every parameter bound.** There are no default values here, so a call binds every parameter. Default values are a
   separate decision.
4. **Every callable with declared parameter names.** Free functions, associated functions (`Type::f`), methods after the
   receiver, aspect methods, constructor calls (section 7), enum-variant calls and native std functions, whose declared
   names are their keyword names. The receiver is never a keyword argument (`self` is reserved).
5. **Calls through a function value are positional only.** A function type carries no parameter names, so a call
   through a closure, a `|T| -> U` parameter or a `dyn` callable binds by position, and a keyword argument there is an error.
   A function item passed as a value does not give the value names.
6. **Aspect methods have one name set.** The parameter names are those of the aspect's method declaration, and an impl
   method must declare the same names, checked at conformance as parameter types are. A call through a generic bound, a `dyn`
   and a call on the concrete type all use that set.
7. **Overloads** follow section 6: the call's keyword names must match some candidate's own parameter names.
8. **Parameter names are public API.** Renaming a parameter of a `pub` function or aspect method breaks callers that use
   it by keyword, so it is a breaking change of the declaring package, like changing a parameter's type. (Whether an author
   may mark a parameter positional-only is open, see Unresolved Questions.)
9. **Typing and evaluation** are unchanged: each argument is typed against its parameter, generic inference is
   unaffected, and evaluation order is the written order (section 6).

Parameter names become part of a function's public call-site surface, the same way they already are conceptually (every existing signature already names its parameters — this RFC exposes that naming at the call site rather than introducing new declaration syntax). Keyword arguments are optional at every call site — purely positional calls remain valid and unchanged for any function, including ones defined before this RFC.


## 3. The grammar position keyword arguments occupy, and what `=` costs

**With RFC-0183, the grammar change is small** (2026-11-07). Today `arg_list = { expr ~ ("," ~ expr)* ~ ","? }` makes every
call argument an `expr` and `expr` has assignment at the top, so `f(x = 1)` parses as one positional argument whose value is an
assignment. RFC-0183 makes assignment a statement, so an argument position never holds an assignment, and `ident = expr` there
is only ever a keyword argument:

```
arg_list    = { call_arg ~ ("," ~ call_arg)* ~ ","? }
call_arg    = { keyword_arg | expr }
keyword_arg = { ident ~ "=" ~ !"=" ~ expr }
```

The `!"="` lookahead keeps `f(x == y)` from attempting the keyword alternative. Compound assignment is unaffected (`f(x += 1)`
never matches `ident ~ "="`), and type ascription is untouched in every position (`f(x: T)` stays an ascribed positional
argument), because `=` replaced the original `:` spelling.

**Prototype (built and run 2026-11-07).** A scratch crate on pest 2.9 used metel-frontend's real `grammar.pest` in four
variants and parsed `expr` on each case, reporting whether the whole input was consumed and which rules matched:
(0) the current grammar, (A) the current grammar plus `keyword_arg` (assignment is still `:=`), (B) plain assignment as `=` and
still an expression, keyword-first, and (C) the same as B with the order reversed (`call_arg = expr | keyword_arg`).
Results: in (0) no keyword form parses, as expected. In (A) every keyword form parses (`f(x = 1)`, `f(a, b = 2)`, `p.m(k = 1,)`,
`Type(x = 1, y = 2)`, closures as keyword values and as positional neighbours), and `f(x: T)` and `f(x == y)` keep their
meaning, so with assignment spelled `:=` today the change is additive. In (B) keyword-first still wins every case. In (C)
every keyword argument is swallowed as an assignment expression, so **keyword-first ordering is mandatory whenever `=` is
an assignment expression**; RFC-0183 removes that need by making assignment a statement. `f(a = 1, 2)` (a positional argument
after a keyword) parses at the grammar level, so rule 1's "positional first" is a checker error, not a parse error. The
prototype shows the two RFCs may land in either order.

<details>
<summary><strong>History: the original `name: value` spelling and why it was replaced (RFC-0100, 2026-07-14 to 2026-07-24)</strong></summary>



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

---

## 4. Evaluation order, aspect-method calls and overload resolution


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


---

## Alternatives considered

- **Struct-only keyword arguments, not a general call-syntax feature.** Rejected: a separate desugaring and checking path
  for no benefit, when generalizing costs little and gives every function the feature.
- **Keyword arguments spelled `name: value`** (the original proposal, 2026-07-13 to 2026-07-23). Rejected 2026-07-24 in
  favour of `=`: it violates the separator invariant, it collides with type ascription, and that collision is what reopened
  RFC-0100. Its one real advantage is precedent (Swift and C# spell keyword arguments with `:`); Python, Kotlin, F# and Ada split
  the other way.
- **Disambiguation alternatives for `:`** (casing, parenthesised ascription, a distinct marker token): moot under `=`.
- **Default parameter values with keyword arguments.** Out of scope; keyword arguments are the usual prerequisite.

---

## Relationship to existing RFCs

- **RFC-0100** — the other half: `Type(args)` instantiation. Its constructor calls take keyword arguments by this RFC; the brace
  rewrite produces the keyword form.
- **RFC-0183** — assignment is a statement; this RFC depends on it (section 3).
- **RFC-0023** (type ascription) — untouched. **RFC-0115** (field initializer separator) — `=` stays.
- **RFC-0125** — pack expansion also uses `..`; spread in call arguments is RFC-0100's section 7.

---

## Unresolved Questions

1. **Positional-only parameters** (section 2 rule 8). Whether an author may declare that a parameter cannot be bound by
   keyword (Python's `/`), so renaming it is not a breaking change. Not proposed: every parameter name of a public function
   is API.
2. **Default parameter values** (rule 3). Out of scope.
3. **Impl parameter names** (rule 6). Requiring an impl method to repeat the aspect's parameter names is proposed and has not
   been checked against the aspect impls in std and the corpus.
4. **Native std functions** (rule 4). Every native must declare stable parameter names; the audit is part of the implementation.
5. ~~**A built prototype of the `arg_list`/`call_arg`/`keyword_arg` grammar** (section 3), before acceptance.~~ **Done 2026-11-07**:
   see section 3. Remaining: the same cases as fixtures once implemented, and the checker error for a positional argument after a keyword.
6. **Error codes** for the rejections of section 2 (unknown name, duplicate, missing parameter, positional after keyword, keyword on a call through a function value).
7. **Is `=` the right separator?** This proposes it; review has not accepted it. The honest case against is precedent (Swift, C#).

---

## References

- RFC-0100 (Constructor-Call Construction), the other half of the split; RFC-0183 (initialization-only `:=`); RFC-0115, RFC-0023, RFC-0125,
  RFC-0136, RFC-0044 (receiver forms), RFC-0098 and RFC-0130 (renames).

---

## Decision

**Outcome:** *(pending)*
