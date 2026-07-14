---
id: surface-syntax-cluster-examples
title: "Surface Syntax RFC Cluster — Example Programs"
type: report
created_date: '2026-07-14'
---

# Surface Syntax RFC Cluster — Example Programs

Worked `.mtl` examples for the current surface-syntax review cluster: RFC-0098
(Surface Keyword Renames), RFC-0099 (Dot-Separated Module Paths), and RFC-0100
(Constructor-Call Construction) — three independent, sibling RFCs opened from
the same review pass, all still `0-draft`.

**Status: illustrative, not executable.** All three RFCs are still `0-draft` —
the interpreter (`metel-core`) parses and runs today's syntax (`impl X for Y`,
`::`, `Type { field: value }`), not the syntax shown here. Treat these as "what
the surface syntax will look like once accepted," not as a working test suite.

**Function and method names stay snake_case throughout** (`to_string`,
`new_token`, `print_all`), matching today's actual convention. RFC-0101
(Grammar-Enforced Naming Case Conventions — camelCase for `fun` declarations)
was reviewed alongside this cluster but deliberately left as an independent
draft, not assumed to land together with these three; none of the syntax
shown here depends on it.

## Files

| File | RFC(s) | Covers |
|---|---|---|
| [`01-keyword-renames.mtl`](01-keyword-renames.mtl) | 0098 | `extend Type` / `extend Type: Aspect` (inherent and aspect impls), negative impls via `extend Type: !Aspect`, generic impls (`extend<T: Bound> ...`), a bare-parameter blanket impl (RFC-0097) under the new spelling, `public`, `var` in every position (bindings, for-loops, `&var`) |
| [`02-dot-paths-and-turbofish.mtl`](02-dot-paths-and-turbofish.mtl) | 0099 | Import/export paths, reserved path roots (`root.`/`std.`), enum-variant paths, static/associated-function calls, turbofish respelled `.<T>` |
| [`03-constructor-call-construction.mtl`](03-constructor-call-construction.mtl) | 0100 | Call-shaped construction (`Type(field: value)`), single-field positional shorthand, general keyword arguments on ordinary function calls, positional/keyword mixing, destructuring's unchanged `{ field }` syntax |
| [`04-combined-program.mtl`](04-combined-program.mtl) | 0098, 0099, 0100, 0097 | One realistic program using all three (plus RFC-0097, already integrated) together, to sanity-check they compose cleanly rather than fighting each other |

Read `01`–`03` in any order — each is self-contained. `04` assumes all three
and is meant to be read last.

## Notes on specific choices

- **`01`'s two `Printable` impls** (a bare-parameter blanket `extend<T:
  Display> T: Printable` alongside a named-type impl `extend<T: Display>
  SortedList<T>: Printable`) are deliberately shown together: they target
  structurally different shapes (a bare type parameter vs. a concrete named
  type) and don't conflict under coherence, illustrating that RFC-0097's form
  and an ordinary conditional impl (RFC-0036) coexist without special-casing.
- **`03`'s trailing comment** about ascription — `f(x: SomeType)` no longer
  being available as a bare positional call argument — is the one accepted,
  narrow trade-off from RFC-0100 §3's grammar-ordering fix for the keyword-
  argument/type-ascription collision. Ascription itself (`let`, match arms,
  general sub-expressions) is untouched.
- **`04` drops raw-array `.push`** in favor of an array literal — `T[]` has no
  `.push` (that's `List<T>`, a separate, unrelated stdlib type), which isn't
  part of this cluster and would have been a distracting error to leave in.
