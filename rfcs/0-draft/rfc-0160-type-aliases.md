---
id: rfc-0160
title: "Type Aliases"
date: '2026-09-01'
status: draft
target:
---

> **Opened 2026-09-01 as a future-ergonomics RFC.** Metel has no way to name a type. `type
> Name = T;` currently exists **only** as an associated type inside an aspect / `extend`
> block (RFC-0082); RFC-0039 names compound *bounds* (`aspect Sortable = A + B + C`), not
> types. This RFC fills the gap. It is **not blocking** the closure cluster (RFC-0134 /
> RFC-0152 / RFC-0050 / RFC-0153) or anything else in v0.13.0 — it is recorded now because
> the closure amendments made function-type signatures the noisiest in the language, and
> because RFC-0113 (context parameters) will make them noisier still.

## Summary

A **type alias** is a module-level, transparent name for an existing type:

```metel
type Bytes = List<u8>;
type Handler = once mut (Request, &Config) -> Response;     // closure qualifiers included
type Renderer<W> = context(theme: Theme) mut (W) -> Html;   // parameterised; context requirement included
```

- **Transparent (structural), not nominal.** `Handler` *is* `once mut (Request, &Config)
  -> Response` — same type, interchangeable everywhere, no coercion, no distinct identity.
  RFC-0152 widening flows straight through it.
- **May be parameterised.** `type X<A, B> = …` with the same generic-parameter and
  bound rules as any declaration.
- **Names any type**, including function/closure types with their `once` / `mut`
  qualifiers (RFC-0134 / RFC-0153) and, once RFC-0113 lands, their `context(...)`
  requirement.

It does **not** introduce a newtype, does not add nominal identity, and does not carry a
closure's capture list (see §"Function and closure types").

---

## Motivation

- Compound types recur in signatures and drift out of sync when edited in place — the
  same problem RFC-0039 solves for bounds, unsolved for types.
- The closure cluster's 2026-08-31 amendments put up to two qualifiers on a function type
  (`once`, `mut`), on top of a base spelling that RFC-0154 is still revising. `once mut
  (Request, &Config) -> Response` written in every route table, struct field, and
  higher-order parameter is real noise, and it is exactly the kind of type an alias is
  best at: long, structural, repeated.
- RFC-0113 context parameters will add a `context(...)` clause to function types for the
  deferral case (§"Context parameters"). Without aliases, `context(theme: Theme) mut
  (Widget) -> Html` is the worst case.
- Metel deliberately has **one structural function type** (no per-closure nominal type),
  which makes a type alias here a pure synonym with zero semantic weight — the cheapest
  possible version of the feature.

---

## Proposal

### 1. Declaration

```
type_alias = "public"? "type" IDENT type_params? "=" type ";"
```

Module-level only (not inside a function body, for now — see Open Questions). `public
type` participates in the module's public surface exactly like a `struct` / `enum` / `fun`
declaration.

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
type Predicate<T> = (T) -> bool;
```

Generic parameters and their bounds follow the ordinary declaration rules. Turbofish
applies to the alias, resolving through the expansion: `Predicate::<i64>` is `(i64) ->
bool`. An alias with unused parameters is a warning, not an error (it may exist to keep a
family of aliases uniform).

### 4. Disambiguation from associated types (RFC-0082)

`type Name = T;` inside an `aspect` or `extend` block is an associated-type definition
(RFC-0082) and is unchanged. At module scope it is a type alias. The two never collide —
position decides — and this RFC adds no new keyword.

---

## Function and closure types

This is the motivating case and the one with a subtlety.

**What the alias carries.** A function type in Metel is `Type::Fun(params, ret,
call_multiplicity, use_multiplicity, call_mutation)` — the qualifiers `once` / `mut` are
*part of the type*, so an alias captures them:

```metel
type Reducer<T> = (T, T) -> T;              // many reading
type Sink<T>    = mut (T) -> ();            // FnMut-shaped
type Consumer<T> = once (T) -> ();          // FnOnce-shaped
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
fun counting_sink(var seen: List<Event>) -> mut (Event) -> () {
    [seen] mut (e) -> () { seen.push(e); }
}
```

**Where the alias still helps the literal.** An alias on a `let` / parameter / field
**ascription** supplies the expected type, so the literal need not restate the
qualifiers:

```metel
type Handler = once mut (Request) -> Response;
let h: Handler = [&cfg] (req) -> Response { … };   // `once mut` come from `Handler`
```

---

## Context parameters (RFC-0113)

RFC-0113 is amended in parallel with the function-type half of this interaction. In
summary, for aliases:

- **Default — the closure captures the context.** A `context c: C` in scope at a closure
  literal is an ordinary free binding the closure closes over at creation. The resulting
  type is plain (`(T) -> U`) and an alias of it needs no `context` clause.
- **Deferral — a context function type.** `context(c: C) (T) -> U` defers `c` to the
  closure's call site (Scala 3's context functions). This *is* type information, so an
  alias carries it: `type Renderer<W> = context(theme: Theme) mut (W) -> Html;`.
- The `context(...)` clause is a **row** of `(role, type)` requirements — orthogonal to
  the `once` / `mut` multiplicity axes, following the row shape RFC-0140 already uses for
  its handler channel. Whether it becomes a fourth `Type::Fun` field or stays a
  resolution-time-only fact (capture-only, no deferral) is RFC-0113's call; this RFC
  aliases whichever form results.

---

## Relationship to existing RFCs

- **RFC-0039 (aspect Alias Syntax, `0-draft`)** — complementary and disjoint: RFC-0039
  names compound *bounds* (`aspect X = A + B`), this names *types* (`type X = T`).
  RFC-0039 Q1 Option C briefly floated `type Alias = A & B & C` as a bound-alias *syntax*;
  that is not this feature. Diagnostics-name-the-alias (RFC-0039 Q5) is adopted here too.
- **RFC-0082 (Associated Types, `4-implemented`)** — `type Name = T;` in aspect / `extend`
  scope is associated types, unchanged. Position disambiguates; no keyword clash.
- **RFC-0134 (Closure Call Capability) / RFC-0153 (Closure Mutation Axis)** — supply the
  `once` / `mut` qualifiers an alias captures. Not blocked by this RFC and not blocking
  it.
- **RFC-0152 (Function-Type Multiplicity Widening)** — widening is structural, so it
  applies through an alias unchanged (a `many reading` closure satisfies a `Handler`
  parameter aliased to `once mut (…)`).
- **RFC-0113 (Context Parameters, `1-under-review`, v0.13.1)** — see §"Context
  parameters"; amended in parallel.
- **RFC-0154 (Pipe Notation, `1-under-review`)** — whatever base function-type spelling it
  settles (`|T| -> U`), the alias RHS uses it; nothing here depends on the choice.
- **RFC-0121 (Open Rows) / RFC-0140 (Algebraic Effects)** — the row shape the
  `context(...)` clause reuses.

---

## Open Questions

1. **Function-body-local aliases.** Allow `type` inside a `fun` body, or module scope
   only? Module-only is simpler and covers the motivating cases; local aliases are a
   later relaxation.
2. **Visibility granularity.** Is `public type` the whole story, or is a
   `pub(module)`-style intermediate ever wanted? Follow whatever the module system settles
   generally.
3. **Alias in `extend` target position.** `extend MyAlias: Aspect { … }` — allowed
   (transparent, so it means `extend <expansion>: Aspect`), or forbidden to keep impls
   visibly attached to a named type? Leaning: allowed, with the coherence check running on
   the expansion.
4. **Recursive aliases.** `type Json = Map<String, Json>;` — rejected as a cycle (RFC-0039
   Q3 rule), or permitted for genuinely recursive shapes the way a `struct` can be
   self-referential through indirection? Leaning: reject direct cycles; a recursive type
   needs a `struct`/`enum`.
5. **Turbofish ergonomics** for partially-applied aliases — `type M<V> = Map<String, V>;`
   then `M::<i64>` — confirm this composes with RFC-0023's ascription-vs-turbofish rules.

---

## Decision

**Outcome:** *(pending — `0-draft`, opened 2026-09-01 as non-blocking future ergonomics)*
**Target:** *(set when accepted)*
