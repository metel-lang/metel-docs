---
id: rfc-0204
title: "Pipelines"
date: '2026-11-01'
status: under-review
updated: '2026-11-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/1754'
---

> **Status — under review.** Scheduled in Pipelines (metel-core#1754).

## Summary

The pipeline operator inserts its left operand as the first positional argument of
a written call. `x |> f(a)` means `f(x, a)`. A pipeline chains existing calls in
execution order.

Reusable function composition, including `.then`, fallible composition, and possible
symbolic operators, moved to RFC-0258.

## Motivation

A sequence of free-function calls can be easier to read in execution order:

```metel
let name := collapse_spaces(to_lower(trim(raw)));
let name := raw |> trim() |> to_lower() |> collapse_spaces();
```

## Design

```metel
xs |> filter(is_odd) |> map(times_ten) |> fold(0, add)
```

1. The left operand supplies the first positional argument of the right-hand call.
   The operand is evaluated once under ordinary argument evaluation order.
2. The right-hand stage must be a written call with parentheses. `x |> trim()`
   lowers to `trim(x)`. `x |> trim` is an error.
3. Pipelines associate to the left and bind more loosely than other binary operators.
   `x |> f(a) |> g(b)` lowers to `g(f(x, a), b)`.
   In particular, `a || b |> f()` lowers to `f(a || b)`. To apply `||` to the
   pipeline's result, write `(a |> f()) || b`. The ungrouped `a |> f() || b`
   is an error because the right-hand side is a Boolean expression.
4. The resulting call uses ordinary name lookup and overload resolution. A same-named
   method on the piped input does not participate. The receiver method can be
   called explicitly as `x.f(a)`.
5. Positional and keyword arguments, rest parameters, and the final default marker
   bind as they do in the resulting call. `xs |> pad(4, ..)` binds as
   `pad(xs, 4, ..)`. A bare hole in the stage, as in `xs |> pad(_, ..)`, is an
   error. Explicitly delimited hole sections retain their ordinary meaning under
   RFC-0205. An author can choose the input position with an explicit call such
   as `(pad(_, ..))(xs)`.

## Interactions

- **RFC-0205:** hole sections can appear in pipeline calls as ordinary arguments.
  Neither RFC requires the other.
- **RFC-0223, RFC-0247, and RFC-0248:** insertion precedes ordinary argument
  binding, including keyword matching, rest packing, and defaults.
- **RFC-0228:** ordinary call lookup applies, including the selected callee's
  rules for a written method receiver.
- **RFC-0203:** list comprehensions overlap with map and filter pipelines. The
  pipeline works with ordinary calls.

## Alternatives considered

- Thread the input into the last argument. The first position matches the
  data-first calls motivating the proposal.
- Look for a method on the type of the input before resolving a free call.
  Adding a method could redirect existing code. Ordinary call lookup is
  independent of same-named methods on the input.
- Accept an unapplied name as a stage. Requiring the call gives every stage an
  explicit argument list.
- Keep nested calls or introduce function composition alone. A pipeline gives a
  left-to-right spelling for an immediate chain of calls.

## Closure syntax

`|>` is a pipeline token between expressions. `||` can still begin a nullary
closure in operand position, and closure parameters retain their ordinary bars.

```metel
|| { 42 } |> run()          // run(|| { 42 })
xs |> map(|n| { n + 1 })    // map(xs, |n| { n + 1 })
```

## Decision

**Outcome:** *(pending)*
