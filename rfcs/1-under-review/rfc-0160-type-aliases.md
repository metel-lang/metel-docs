---
id: rfc-0160
title: "Type Aliases"
date: '2026-09-01'
status: under-review
target: v0.13.0
updated: '2026-09-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/921'
---

> **Opened 2026-09-01 as a future-ergonomics RFC.** Metel has no way to name a type. `type
> Name = T;` currently exists **only** as an associated type inside an aspect / `extend`
> block (RFC-0082); RFC-0039 names compound *bounds* (`aspect Sortable = A + B + C`), not
> types. This RFC fills the gap.

> **Brought into v0.13.0 (2026-09-02).** Originally recorded as non-blocking. Re-scoped to
> co-land with **RFC-0154** (the `|...|` function-type spelling) and the closure cluster
> (RFC-0050 / RFC-0134 / RFC-0152 / RFC-0153 / RFC-0157): the qualifier grammar (`once` /
> `var`), its base spelling, and the tool for naming the results all ship in one
> migration. RFC-0154 §5 recommends parenthesizing a nested function type (`|A| -> (|B| ->
> C)`); an alias is how you write that parenthesis once. Examples below use
> RFC-0154's `|...|` form and the `var` qualifier accordingly. **All five Open Questions
> resolved 2026-09-02 — acceptance-ready.**

> **Status — under review (2026-09-01).** type-alias gap confirmed (no existing RFC);
> brought into v0.13.0 2026-09-02 to co-land with RFC-0154 + the closure cluster.

## Summary

A **type alias** is a module-level, transparent name for an existing type:

```metel
type Bytes = List<u8>;
type Handler = once var |Request, &Config| -> Response;       // closure qualifiers included
type Renderer<W> = context(theme: Theme) var |W| -> Html;    // parameterised; context requirement included
```

- **Transparent (structural), not nominal.** `Handler` *is* `once var |Request, &Config|
  -> Response` — same type, interchangeable everywhere, no coercion, no distinct identity.
  RFC-0152 widening flows straight through it.
- **May be parameterised.** `type X<A, B> = …` with the same generic-parameter and
  bound rules as any declaration.
- **Names any type**, including function/closure types with their `once` / `var`
  qualifiers (RFC-0134 / RFC-0153), the nested function types RFC-0154 §5 recommends
  parenthesizing, and, once RFC-0113 lands, their `context(...)` requirement.

It does **not** introduce a newtype, does not add nominal identity, and does not carry a
closure's capture list (see §"Function and closure types").

---

## Motivation

- Compound types recur in signatures and drift out of sync when edited in place — the
  same problem RFC-0039 solves for bounds, unsolved for types.
- The closure cluster puts up to two qualifiers on a function type (`once`, `var`), on
  RFC-0154's `|...|` base spelling. `once var |Request, &Config| -> Response` written in
  every route table, struct field, and higher-order parameter is real noise, and it is
  exactly the kind of type an alias is best at: long, structural, repeated.
- RFC-0154 §5 recommends parenthesizing a function type nested in another (`|A| -> (|B| ->
  C)`, `|(|i64| -> i64)| -> String`). An alias writes that parenthesis once and hands out a
  plain name: `type Curried = |A| -> (|B| -> C);`.
- RFC-0113 context parameters will add a `context(...)` clause to function types for the
  deferral case (§"Context parameters"). Without aliases, `context(theme: Theme) var
  |Widget| -> Html` is the worst case.
- Metel deliberately has **one structural function type** (no per-closure nominal type),
  which makes a type alias here a pure synonym with zero semantic weight — the cheapest
  possible version of the feature.

---

## Proposal

### 1. Declaration

```
type_alias = "public"? "type" IDENT type_params? "=" type ";"
```

Allowed at **module scope or inside a function / block body** (Open Question 1). `public`
is module-scope only. A module-level `public type` participates in the module's public
surface exactly like a `struct` / `enum` / `fun` declaration; a **function-local alias is
never exported**, may reference the enclosing function's generic parameters, and follows
block-local `fun`'s scoping and shadowing rules — visible throughout its block regardless
of textual position (RFC-0131).

### 2. Transparency

An alias is erased during type checking to its right-hand side before any further
reasoning. Consequences:

- `Handler` and its expansion unify, satisfy the same bounds, and are accepted in the
  same positions. There is no `T0015`-style coherence concern — an alias defines no impl.
- Diagnostics **prefer the alias name** the user wrote (as RFC-0039 Q5 does for bound
  aliases), expanding it only when the mismatch is inside the expansion.
- An alias may reference another alias; expansion is recursive; cycles are a compile
  error (RFC-0039 Q3).

### 3. Parameters

```metel
type Pair<A, B> = (A, B);
type Cache<K, V> = Map<K, List<V>>;
type Predicate<T> = |T| -> bool;
```

Generic parameters and their bounds follow the ordinary declaration rules. Turbofish
applies to the alias, resolving through the expansion: `Predicate::<i64>` is `|i64| ->
bool`. An alias with unused parameters is a warning, not an error (it may exist to keep a
family of aliases uniform).

### 4. Disambiguation from associated types (RFC-0082)

`type Name = T;` inside an `aspect` or `extend` block is an associated-type definition
(RFC-0082) and is unchanged. Anywhere else — module scope or a function / block body — it
is a type alias. The two never collide — position decides — and this RFC adds no new
keyword.

---

## Function and closure types

This is the motivating case and the one with a subtlety.

**What the alias carries.** A function type in Metel is `Type::Fun(params, ret,
call_multiplicity, use_multiplicity, call_mutation)` — the qualifiers `once` / `var` are
*part of the type*, so an alias captures them:

```metel
type Reducer<T> = |T, T| -> T;              // many reading
type Sink<T>    = var |T| -> ();            // FnMut-shaped
type Consumer<T> = once |T| -> ();          // FnOnce-shaped
type Middleware = |Handler| -> (|Request| -> Response);   // returns a function -> §5 parens
```

**What the alias does not carry: the capture list.** `[&var count, buf]` is on the
closure *literal*, not its type (spec: "captures distinguish closure values at runtime
rather than introducing a distinct closure type"). The capture list only *influences* the
three multiplicity fields — `use_multiplicity` from whether every capture is `Copy`,
`call_multiplicity` from whether the body moves a by-value non-`Copy` capture,
`call_mutation` from whether the body mutates one — and those the alias already carries. A
type alias therefore cannot and should not embed a capture list; two closures satisfying
`Sink<Event>` may capture entirely different things.

To reuse a *capture pattern*, write a factory function:

```metel
fun counting_sink(var seen: List<Event>) -> var |Event| -> () {
    [seen] var |e| -> () { seen.push(e); }
}
```

**Where the alias still helps the literal.** An alias on a `let` / parameter / field
**ascription** supplies the expected type, so the literal need not restate the
qualifiers:

```metel
type Handler = once var |Request| -> Response;
let h: Handler = [&cfg] |req| -> Response { … };   // `once var` come from `Handler`
```

---

## Context parameters (RFC-0113)

RFC-0113 is amended in parallel with the function-type half of this interaction. In
summary, for aliases:

- **Default — the closure captures the context.** A `context c: C` in scope at a closure
  literal is an ordinary free binding the closure closes over at creation. The resulting
  type is plain (`|T| -> U`) and an alias of it needs no `context` clause.
- **Deferral — a context function type.** `context(c: C) |T| -> U` defers `c` to the
  closure's call site (Scala 3's context functions). This *is* type information, so an
  alias carries it: `type Renderer<W> = context(theme: Theme) var |W| -> Html;`.
- The `context(...)` clause is a **row** of `(role, type)` requirements — orthogonal to
  the `once` / `mut` multiplicity axes, following the row shape RFC-0140 already uses for
  its handler channel. Whether it becomes a fourth `Type::Fun` field or stays a
  resolution-time-only fact (capture-only, no deferral) is RFC-0113's call; this RFC
  aliases whichever form results.

---

## Relationship to existing RFCs

- **RFC-0039 (aspect Alias Syntax, `1-under-review`)** — complementary and disjoint: RFC-0039
  names compound *bounds* (`aspect X = A + B`), this names *types* (`type X = T`).
  RFC-0039 Q1 Option C briefly floated `type Alias = A & B & C` as a bound-alias *syntax*;
  that is not this feature. Diagnostics-name-the-alias (RFC-0039 Q5) is adopted here too.
- **RFC-0082 (Associated Types, `4-implemented`)** — `type Name = T;` in aspect / `extend`
  scope is associated types, unchanged. Position disambiguates; no keyword clash.
- **RFC-0134 (Closure Call Capability) / RFC-0153 (Closure Mutation Axis)** — supply the
  `once` / `var` qualifiers an alias captures. Co-land in v0.13.0.
- **RFC-0152 (Function-Type Multiplicity Widening)** — widening is structural, so it
  applies through an alias unchanged (a `many reading` closure satisfies a `Handler`
  parameter aliased to `once var |…|`).
- **RFC-0113 (Context Parameters, `1-under-review`, v0.13.1)** — see §"Context
  parameters"; amended in parallel.
- **RFC-0154 (Pipe Notation, `2-accepted`)** — **co-lands in v0.13.0**. The alias RHS
  uses its `|...|` form; RFC-0154 §5's recommendation to parenthesize a nested function
  type is what makes aliases the practical tool for the returns-a-function case.
- **RFC-0121 (Open Rows) / RFC-0140 (Algebraic Effects)** — the row shape the
  `context(...)` clause reuses.

---

## Open Questions

*All resolved 2026-09-02.*

1. **Function-body-local aliases.** **✓ Resolved — allowed.** `type X = T;` may appear as
   a block statement, scoped to that block, as well as at module scope. A local alias may
   reference enclosing generic parameters (`fun f<T>() { type Pair = (T, T); … }` — a
   reason to have it: a module alias would need its own `<T>`). It cannot carry `public`
   (nothing local is exported). Shadowing and visibility follow block-local `fun`: an
   inner `type` shadows an outer alias / type of the same name within its block, and it is
   visible throughout its block regardless of textual position (types have no
   initialisation-order hazard — the same reason RFC-0131 hoists `fun`). The motivating
   case is the complex one-off closure type used only inside one function.
2. **Visibility granularity.** **✓ Resolved — no alias-specific design.** A module-level
   `public type` participates in the public surface exactly like `public struct` / `fun` /
   `enum`; whatever finer visibility the module system grows, aliases inherit. A
   function-local alias is never exported (OQ1).
3. **Alias in `extend` target position.** **✓ Resolved — forbidden for v0.13.0.**
   `extend MyAlias: Aspect { … }` is a compile error; write `extend <the real type>:
   Aspect`. It only matters for aliases of *nominal* types (`type Bytes = List<u8>; extend
   Bytes`), which reopens the orphan-rule / coherence surface for no clear gain in a first
   cut and hides impls from where a reader looks for them. A pure restriction — liftable
   later (coherence check running on the expansion) if demand appears.
4. **Recursive aliases.** **✓ Resolved — rejected, direct and mutual.** `type Json =
   Map<String, Json>;` and any cycle through a chain of aliases is a compile error (same
   rule as RFC-0039 Q3). A transparent alias expands eagerly and a cycle has no finite
   expansion; a genuinely recursive type needs a `struct` / `enum` indirection point, as
   in every language with transparent aliases.
5. **Turbofish for partially-applied aliases.** **✓ Resolved — no special rule.**
   `M::<i64>` binds the alias's own type parameters positionally, then expands:
   `type M<V> = Map<String, V>` makes `M::<i64>` the type `Map<String, i64>`. The alias is
   another generic name; RFC-0023's ascription-vs-turbofish placement rule applies to it
   unchanged.

---

## Decision

**Outcome:** *(pending — `1-under-review` (#921), opened 2026-09-01. **All five Open
Questions resolved 2026-09-02** (local aliases allowed, no alias-specific visibility,
`extend`-on-alias forbidden for now, cycles rejected, turbofish through expansion) —
acceptance-ready.)*
**Target:** **v0.13.0** — set 2026-09-02 to co-land with RFC-0154 (`|...|` spelling) and
the closure cluster's `once` / `var` qualifier grammar, so the function-type spelling and
the tool for naming its results ship in one migration.
