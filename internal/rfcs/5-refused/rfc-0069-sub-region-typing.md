---
id: rfc-0069
title: "Sub-Region Typing"
date: '2026-06-28'
---

> **RETRACTED — 2026-07-05.** `SubRegion<R>` exists solely to propagate `Outlives`
> relationships when a struct with a struct-owned allocator is nested inside an outer
> allocator. Under the split model (RFC-0088), `Outlives` is dropped from the allocator
> layer entirely. Nesting relationships between allocator scopes are now derived by the
> borrow checker from scope nesting — no explicit constraint type is needed. The struct
> allocator owned-by-value pattern (`struct Foo(@a: BumpAlloc)`) makes the scope nesting
> structurally visible; the borrow checker reads it directly. See
> `reports/memory-model/lifetimes-vs-regions-2026-07-02.md` §5.

## Summary

When a struct with a struct-owned region `[own r]` (RFC-0068) is itself allocated into an
existing region `R`, the owned arena `r` is structurally bounded by `R`: the struct cannot
outlive `R`, so neither can its arena. This relationship is currently invisible to the type
system — the caller holding `@[R] Parser` has no way to know that borrows tagged `[r]`
are bounded by `R`, and explicit `Outlives` annotations would be required everywhere the
two regions interact.

This RFC introduces `SubRegion<R>` — a region type in the stdlib that carries the
constraint `R: Outlives<SubRegion<R>>` by construction. When a struct with `[own r]` is
allocated into region `R`, the compiler assigns `r` the type `SubRegion<R>`. The
`Outlives` relationship becomes automatic and derivable from the allocation site alone.

---

## Motivation

Consider a `Parser` with an owned arena allocated into a scoped region:

```metel
struct Parser[own r] {
    nodes: @[r] List<AstNode>,
}

BumpRegion::scoped([outer]() -> {
    let parser: @[outer] Parser = @[outer] Parser::new(src);
    let node = parser.root();  // returns &[r] AstNode
    // What is the relationship between r and outer?
    // The borrow checker cannot tell without an explicit annotation.
});
```

`node` is tagged `[r]` — Parser's owned arena — but the borrow checker has no way to
confirm that `r` is bounded by `outer`. The result is either a spurious error or the need
for an explicit `Outlives` annotation threaded through the call chain.

`SubRegion<R>` resolves this: allocating `Parser` into `outer` types `r` as
`SubRegion<outer>`, which carries `outer: Outlives<r>`. The borrow checker derives the
bound automatically; no annotation is written.

---

## 1. The `SubRegion<R>` type

`SubRegion<R>` is a region type in the stdlib with one constraint baked in:

```metel
// stdlib definition (normative — see RFC-0082 §7)
struct SubRegion<R: Region> { /* compiler-managed */ }

impl<R: Region> Region for SubRegion<R> {
    type AllocationError = !;
}

impl<R: Region> Outlives<R> for SubRegion<R> {}
```

It is not a user-constructible type. The compiler assigns it when a struct-owned region is
established at an allocation site with a known outer region. The programmer may name it in
type annotations and bounds but never constructs it directly.

`SubRegion<R>` satisfies the `Region` interface and may appear anywhere a region type is
expected. Because it implements `Outlives<R>`, any code that requires `R: Outlives<r>` is
satisfied automatically when `r: SubRegion<R>`.

---

## 2. Assignment at the allocation site

When `@[R] Foo::new()` is evaluated and `Foo` declares `[own r]`, the compiler types `r`
as `SubRegion<R>`:

```metel
BumpRegion::scoped([outer]() -> {
    let parser = @[outer] Parser::new(src);
    // parser's owned region r : SubRegion<outer>
    // outer: Outlives<r>  — held automatically

    let node: &[r] AstNode = parser.root();
    // borrow checker knows r is bounded by outer;
    // node is valid as long as parser (and therefore outer) is alive
});
```

No annotation is written at the call site. The `SubRegion<R>` type is an internal
compiler-assigned fact that surfaces in diagnostics and hover information but does not
appear in source unless the programmer inspects it.

---

## 3. Edge cases

### 3.1 Stack-allocated struct

When a struct with `[own r]` is constructed without an enclosing region — on the stack or
in a plain `let` binding — there is no outer region to sub from:

```metel
let parser = Parser::new(src);  // no @[R] prefix
```

In this case `r` is typed as a plain `BumpRegion` with no outer bound. The borrow checker
treats `r`'s lifetime as the scope of `parser`'s binding, the same as any
`let r = BumpRegion::new()` (RFC-0063 §1).

### 3.2 Heap-allocated struct

`@[Heap] Parser::new()` gives `r: SubRegion<Heap>`. Because `Heap: Outlives<SubRegion<Heap>>` —
the heap pointer is the unique owner of the struct, and when it is dropped the owned arena
is freed — the bound holds by the same construction argument. In practice this means borrows
`&[r] T` returned from heap-allocated Parser methods are valid for as long as the heap
pointer `@[Heap] Parser` is alive.

### 3.3 Nesting

Nesting composes naturally. If Parser's arena `r: SubRegion<outer>` itself contains an
`@[r] SubParser` where `SubParser[own s]`, then `s: SubRegion<r>`. The full chain:

```
r : SubRegion<outer>  →  outer: Outlives<r>
s : SubRegion<r>      →  r:     Outlives<s>
                      ∴  outer: Outlives<s>  (by Outlives transitivity — RFC-0063 §3)
```

Each level is a distinct type: `SubRegion<outer>` and `SubRegion<r>` are not collapsed.
This preserves every intermediate `Outlives` relationship — in particular `r: Outlives<s>`,
which is required to prove that borrows into `s` are valid within the scope of `r`. The
borrow checker derives the full chain without any explicit annotation.

---

## 4. Interaction with explicit `Outlives` bounds

`SubRegion<R>` does not replace explicit `Outlives` bounds in multi-region function
signatures — it only eliminates the annotation at the allocation site where the relationship
is structurally determined.

When two regions arrive as external bracket parameters with no known allocation
relationship, explicit bounds are still required:

```metel
// r and s are both external — relationship must be stated
fun copy_nodes<[src, dst: Outlives<src>]>(…) -> … { … }

// r is the struct's owned region; outer is the allocation site — SubRegion handles it
let p = @[outer] Parser::new();  // r : SubRegion<outer>, no annotation needed
```

---

## 5. Interaction with RFC-0068 `[own r, s]`

RFC-0068 §7 notes that a struct may have both an owned region and a borrowed region:
`struct Foo[own r, s]`. RFC-0068 §8.3 marks the `Outlives` relationship between `r` and
`s` as unresolved.

`SubRegion<R>` partially resolves this: when `Foo` is allocated into the same region as
`s` — i.e., when `R = s` at the allocation site — `r` is typed as `SubRegion<s>`, which
automatically satisfies `s: Outlives<r>`. When `R ≠ s` (Foo is allocated into a third
region while borrowing from `s`), the relationship between `r` and `s` is not structurally
determined and an explicit bound is still required.

---

## 6. Unresolved questions

1. **Naming `SubRegion<R>` in source — resolved.** The programmer may write `SubRegion<R>`
   explicitly in type annotations and bracket channel bounds. The full form
   `[r: SubRegion<outer>]` is valid where the compiler cannot infer the allocation context
   automatically. `SubRegion<R>` is a stdlib type like any other; restricting its use to
   compiler-internal assignment only would create an unnecessary asymmetry.

2. **`SubRegion` of `SubRegion` — resolved.** `SubRegion<SubRegion<R>>` is kept as a
   distinct type — no normalisation. Each nesting level carries a real `Outlives`
   relationship: `r: SubRegion<outer>` gives `outer: Outlives<r>`, and
   `s: SubRegion<r>` gives `r: Outlives<s>`. Erasing intermediate levels would lose
   these relationships and break borrow checking across nesting boundaries.

3. **`SubRegion` and sendability — resolved.** `SubRegion<R>` is sendable iff `R` is
   sendable. When `R = Heap`, the arena is tied to the heap allocation, not to a thread;
   if the heap struct is sent to another fiber the arena moves with it. No aliasing hazard
   arises because the owned region is private to the struct's impl blocks (RFC-0068 §1) —
   no external code holds the arena handle independently, so concurrent allocation through
   it is impossible.

---

## References

- RFC-0063 (Region Handles) §3 — `Outlives` bounds; §1 — `BumpRegion::new()` and region
  creation.
- RFC-0068 (Struct-Owned Regions) — `[own r]` declaration; §8.3 — the unresolved
  `Outlives` question this RFC partially resolves.
