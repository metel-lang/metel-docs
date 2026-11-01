---
id: rfc-0203
title: "List Comprehensions"
date: '2026-11-01'
status: draft
---

## Summary

Add comprehension syntax as sugar over iterator adapters:

```metel
let squares := [x * x for (x in 1..=10) if (x % 2 == 0)];
let pairs   := [(a, b) for (a in 1..=3) for (b in a..=3) if (a + b == 4)];
let lookup  := {w: w.len() for (w in words)};
```

A comprehension has a result expression, one or more `for` generators, and optional `if`
filters. It lowers to chained `filter`/`map`/flat-map calls on `IntoIterator`s and then to a
`collect` into a collection chosen by the delimiter or an annotation.

---

## Motivation

Chains such as

```metel
List::from([1, 2, 3, 4])
    .filter(|x: i64| -> boolean { x % 2 == 0 })
    .map(|x: i64| -> i64 { x * x })
```

repeat full closure annotations on every stage. Nested loops that build a collection need a
`var` accumulator and a `push` per iteration. Comprehensions are the readable form for the
common "build a collection from another" case, and the `for (x in xs)` loop syntax is already
established.

---

## Design

### 1. Grammar

```
comprehension := '[' expr clauses ']'            // List<T>
               | '{' expr clauses '}'            // Set<T>
               | '{' expr ':' expr clauses '}'   // Map<K, V>
clauses       := clause+
clause        := 'for' '(' pattern 'in' expr ')'
               | 'if' '(' expr ')'
```

The first clause must be `for`. Parentheses match the existing `for (x in xs)` and `if (c)` forms.

### 2. Lowering

```metel
[e for (p1 in s1) if (c1) for (p2 in s2)]
```

lowers to

```metel
s1.into_iter()
  .filter(...c1...)
  .flat_map(|p1| s2.into_iter().map(|p2| e))
  .collect()
```

with the pattern bound by an ordinary closure parameter. A refutable pattern in a generator
**skips** non-matching items (as in Haskell/Python), rather than panicking:
`[name for (Some { value = name } in lookups)]`.

### 3. Result collection

The collection is chosen from the delimiter: `[...]` is `List`, `{...}` is `Set`,
`{k: v ...}` is `Map`. The collect target requires a `FromIterator`-style aspect (not yet
specified; see Open Question 1). An annotation (`let xs: List<i64> := [...]`) overrides it.

### 4. Evaluation order and laziness

Generators evaluate left to right, outer to inner, exactly like nested `for` loops. The
comprehension is **eager**: the whole result is built before the expression yields. A lazy form
is a library concern (return the adapter chain itself); it is not given syntax here.

### 5. Ownership

Each source is consumed (`into_iter`) unless written as a reference:
`[x.name.clone() for (x in &users)]` iterates by reference. Captured variables in the result
expression and filters follow normal closure capture rules, i.e. the lowered closures are
non-escaping and capture by reference where possible.

### 6. Scoping

A pattern binding is visible to later clauses and the result expression, not before. Bindings
shadow outer names. No binding escapes the comprehension.

### 7. `?` inside a comprehension

`?` in the result expression propagates out of the *enclosing function*, not out of the
comprehension, matching the behaviour of `?` inside any block. Collecting `Result`s into a
`Result<List<_>, E>` is done via an aspect on the collect target (Open Question 3).

---

## Interactions

- **RFC-0124 (sequence types):** `List`, arrays and slices are the generator sources and
  targets; the ranges `1..=10` are already iterables.
- **RFC-0190 (`Try`):** a `Try`-generic `collect` is the obvious way to get fallible
  comprehensions.
- **RFC-0204 (pipelines and composition):** `[f(x) for (x in xs)]` and `xs |> map(f)` overlap;
  both are sugar over the same adapters.
- **RFC-0199 (`Lazy<T>`):** a comprehension over a `Stream` terminates only if the source is
  bounded by a `take`; unbounded sources need the lazy form.
- **RFC-0201 (pattern synonyms):** patterns in generators may use synonyms.
- **RFC-0131 (hoisting):** unaffected; comprehensions introduce their own scope.

---

## Alternatives considered

1. **Only method chains** (status quo). Verbose closure annotations; eased in part by RFC-0205 (hole sections) and RFC-0204 (pipelines).
2. **`do`/`for`-yield blocks** (Scala/Haskell `do`). More general (any `Try`), but a larger
   change. Comprehensions can be defined later as a special case of such a form.
3. **Python-order syntax** (`[x for x in xs]`). Rejected: parentheses are required for the
   `for`/`if` headers throughout the language.

---

## Open Questions

1. There is no `FromIterator`/`collect` aspect in the corpus. Is that a prerequisite RFC, or
   part of this one?
2. Is `{...}` for sets and maps acceptable given records already use `{...}` (RFC-0187)? A
   clash with anonymous-record delimiters is likely; the alternative is explicit
   `Set::from([... ])`.
3. How should fallible element expressions collect: `[f(x)? for ...]` versus a
   `try_collect()` stage?
4. Should a mutable accumulator be exposed (`fold`-style comprehensions)? Probably not.
5. Cost transparency: every nested generator allocates an intermediate closure and iterator.
   Is this acceptable in the interpreter, and optimisable in the compiler?

---

## Decision

**Outcome:** *(pending)*
