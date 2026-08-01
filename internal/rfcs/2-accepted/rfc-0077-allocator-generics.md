---
id: rfc-0077
title: "Allocator Generics"
date: '2026-06-29'
updated: '2026-07-10'
status: accepted
---

> **Status — under review.** Rewritten 2026-07-05. The original RFC used the bracket
> channel `[r]` for impl headers and `Outlives` for wellformedness. Under the split
> model, allocators live in the value channel `()` with the `@` prefix; impl headers
> for structs with external allocators use type parameters `<A: Alloc>` plus a
> corresponding `(@a: A)` parameter; `Outlives` is dropped from the allocator layer;
> wellformedness for nested allocator-tagged types is borrow-checker derived. Variance
> is restated for `@a T`, `&r T`, and `&r mut T`. Depends on RFC-0063 (Allocator
> Handles), RFC-0065 (Allocator Ergonomics), RFC-0067 (Lifetime Anchors), and RFC-0068
> (Struct-Owned Allocators).
>
> **Updated 2026-07-06:** §2.3's bounds table adds the tag-only `<@a>` form
> (RFC-0063 §4); §3.1 notes that wellformedness applies unchanged to it.

> **Status — accepted (2026-07-10).** Phase 0 ratification sweep: split model consistency-checked (RFC-0063 sec9 items 1/2/5 synced with roadmap-2026-07-07 Phase 0 decision; RFC-0066/0068 stale titles fixed); sweeping the cluster from under-review to accepted per reports/implementation/roadmap-2026-07-07.md Phase 0.

## Summary

RFC-0063 establishes allocator parameters on functions and structs but leaves four
questions open:

1. **`impl` blocks** — how do `impl` and `aspect impl` blocks introduce an allocator
   parameter for a struct declared with an external allocator `<A: Alloc>`?
2. **Generic allocator bounds** — how does a function or struct declare that its
   allocator parameter must satisfy `Alloc` rather than naming a concrete type?
3. **Wellformedness** — when `T` contains allocator-tagged types, what constraints are
   required for `@a T` to be safe?
4. **Variance** — is `@a T` covariant, contravariant, or invariant in its allocator tag
   and value type?

These four questions arise together in any generic code involving allocators.

---

## Motivation

A generic arena-backed collection illustrates all four gaps at once:

```metel
struct ArenaSet<T, A: Alloc> {
    data: @a List<T>,   // `a` must be an allocator parameter
}
```

- Writing methods on `ArenaSet<T, A>` requires an `impl` header that names the
  allocator parameter.
- `ArenaSet` should work with any allocator, not just `BumpAlloc`.
- If `T = @b Node`, what must hold between the lifetimes of `b` and `a` for
  `@a List<@b Node>` to be safe?
- Can `@b ArenaSet<T, B>` be passed where `@a ArenaSet<T, A>` is expected?

---

## 1. `impl` blocks with external allocator parameters

A struct that holds externally-allocated values carries the allocator as a type
parameter bound to `Alloc`, plus a corresponding value parameter in the primary
constructor or methods. The `impl` header repeats the type parameter:

```metel
struct Parser<A: Alloc> {
    input: @a String,
    pos:   u64,
}

extend<A: Alloc> Parser<A> {
    fun new(@a: A, src: String) -> Parser<A> {
        Parser { input: @a src, pos: 0 }
    }

    fun remaining<&s>(&s self) -> &s String {
        &self.input
    }
}
```

The type parameter `A` names the allocator type; the value parameter `(@a: A)` names
the instance. `a` appears in `@a String` in field types.

### 1.1 `aspect impl` blocks

`aspect impl` follows the same header form:

```metel
aspect impl<A: Alloc> Display for Parser<A> {
    fun fmt<&s>(&s self, buf: &mut Buf) { ... }
}
```

The allocator type parameter is on the `aspect impl`, not on the `Display` aspect.

### 1.2 Multiple external allocators

```metel
struct Pair<A: Alloc, B: Alloc> {
    left:  @a Node,
    right: @b Node,
}

extend<A: Alloc, B: Alloc> Pair<A, B> {
    fun left_ref<&s>(&s self) -> &s Node {
        &self.left
    }
}
```

### 1.3 Owned vs. external — the complete rule

RFC-0068 specifies that for `struct Foo(@a: BumpAlloc)`, `a` is implicitly in scope in
`impl Foo`. This RFC provides the complementary rule for external allocator parameters:

| Declaration | `impl` header | `a` in scope |
|-------------|---------------|--------------|
| `struct Foo(@a: BumpAlloc)` | `extend Foo { … }` | always implicit |
| `struct Foo<A: Alloc>` | `extend<A: Alloc> Foo<A> { … }` | via `(@a: A)` parameters |

---

## 2. Generic allocator bounds

RFC-0063 §4 supports two annotation forms for allocator parameters:

| Form | Meaning |
|------|---------|
| `(@a: BumpAlloc)` | exactly the type `BumpAlloc` |
| `<A: Alloc>(@a: A)` | any type implementing `Alloc` |

The generic bound form allows writing allocator-polymorphic functions and structs:

```metel
fun alloc_copy<T: Clone, A: Alloc>(@a: A, val: T) -> @a T {
    @a val.clone()
}
```

`A` is declared in `<...>` with an `Alloc` bound; `(@a: A)` in the value channel
names the instance.

### 2.1 Structs

```metel
struct Cache<A: Alloc> {
    data: @a HashMap<Key, Value>,
}

extend<A: Alloc> Cache<A> {
    fun new(@a: A) -> Cache<A> {
        Cache { data: @a HashMap::new() }
    }

    fun get<&s>(&s self, key: &Key) -> Perhaps<&s Value> {
        self.data.get(key)
    }
}
```

`Cache` is polymorphic over the allocator kind. A caller using `BumpAlloc` gets an
arena-backed cache; a caller using `Heap` gets a heap-allocated cache.

### 2.2 Allocator bounds on aspect methods

Aspects do not carry allocator parameters. Allocator generics are expressed at the
method level:

```metel
aspect Serialize {
    fun serialize<A: Alloc>(@a: A, self: &Self) -> @a Bytes;
}

aspect impl Serialize for Record {
    fun serialize<A: Alloc>(@a: A, self: &Self) -> @a Bytes {
        @a Bytes::encode(self)
    }
}
```

### 2.3 Bounds table

| Form | Constraint | Typical use |
|------|------------|-------------|
| `(@a: BumpAlloc)` | exactly `BumpAlloc` | arena-only |
| `(@a: Heap)` | exactly `Heap` | heap-only |
| `<A: Alloc>(@a: A)` | any allocator implementing `Alloc` | allocator-polymorphic |
| `<@a>` (no value parameter) | no bound — tag only, no runtime handle | pass-through / preservation, never allocates |

The first three rows all carry a real runtime value parameter and therefore always
satisfy some concrete or bounded `Alloc` type, because the function may need to call
`a.alloc(...)`. `<@a>` (RFC-0063 §4) is categorically different, not just a weaker
bound: it never allocates, so it has nothing to prove about a concrete `Alloc` type —
it only relays a tag that was already established elsewhere. Reach for it when a
function's allocator parameter exists purely to relate an input tag to an output tag,
never to name a type whose interface (`AllocationError`, etc.) the function actually
uses.

---

## 3. Wellformedness of `@a T` when `T` contains allocator-tagged types

### 3.1 The wellformedness rule

`@a T` allocates a value of type `T` into allocator `a`. When `T` contains fields of
type `@b U`, those fields are stored inside the `a`-allocated slot. For this to be safe,
the inner allocator `b` must not be freed while the outer allocation in `a` is still
live.

The borrow checker derives this from scope nesting — no explicit `Outlives` constraint
is required or available. If allocator `b` is nested inside allocator `a` in the program
text, the borrow checker enforces that `@b U` values do not outlive `b`'s scope, and
therefore do not outlive `a`'s slot that contains them.

The concrete rule: `@a T` is well-formed if and only if, for every allocator tag `b`
appearing in `T`, `b`'s scope encloses `a`'s scope — i.e., `b` lives at least as long
as `a`. The borrow checker verifies this from scope structure.

This applies unchanged whether `a` and `b` came from real value-channel parameters
(`(@a: A)`) or from tag-only parameters (`<@a>`, RFC-0063 §4) — wellformedness is a
property of the scope a tag names, not of whether a runtime handle happens to be
attached to it.

### 3.2 Concrete examples

**Heap pointer stored in a scoped allocator — safe:**

```metel
BumpAlloc::scoped((@a) -> {
    let heap_node: @Heap Node = @Heap Node { val: 1 };
    let wrapper: @a @Heap Node = @a heap_node;
    // ✓ — Heap's scope encloses all scoped allocators
});
```

**Scoped pointer stored on the heap — rejected:**

```metel
BumpAlloc::scoped((@a) -> {
    let scoped_node: @a Node = @a Node { val: 1 };
    let bad: @Heap @a Node = @Heap scoped_node;
    // ✗ — a's scope ends inside this closure; the heap allocation would outlive it
});
```

**Subscope stored in outer allocator — rejected:**

```metel
BumpAlloc::scoped((@outer) -> {
    BumpAlloc::scoped((@inner) -> {
        let inner_node: @inner Node = @inner Node { val: 1 };
        let bad: @outer @inner Node = @outer inner_node;
        // ✗ — inner drops before outer; inner does not enclose outer's scope
    });
});
```

**Both allocations in the same allocator — safe:**

```metel
BumpAlloc::scoped((@a) -> {
    let node: @a Node = @a Node { val: 1 };
    let container: @a Container = @a Container { ptr: node };
    // ✓ — same allocator, trivially safe
});
```

### 3.3 Wellformedness in generic functions

When `T` is a type parameter, wellformedness is checked at each instantiation site:

```metel
fun wrap<T, A: Alloc>(@a: A, val: T) -> @a T { @a val }

// instantiation 1: T = u64 — no allocator tags; trivially well-formed
let x = wrap(@a, 42_u64);

// instantiation 2: T = @b Node — requires b's scope to enclose a's
let y = wrap(@outer, inner_node);
// error if inner_node: @inner Node and inner drops before outer
```

---

## 4. Variance of allocator-annotated types

### 4.1 Definitions

If allocator `b` has a longer scope than `a` (b's scope encloses a's), may `@b T` be
used where `@a T` is expected? **Covariant** means yes — a longer scope may substitute.
**Invariant** means no substitution is allowed regardless of scope nesting.

### 4.2 Rules

| Type | Variance in allocator tag | Variance in value type `T` |
|------|--------------------------|---------------------------|
| `@a T` | covariant | covariant |
| `&r T` | covariant in anchor `r` | covariant |
| `&r mut T` | covariant in anchor `r` | invariant |

**Covariance in the allocator tag.** If `b` outlives `a`, then `@b T` may be used where
`@a T` is expected. The function sees `@a T`; the actual allocation is in `b`, which
lives longer — the guarantee is only strengthened.

**Covariance in `T` for `@a T` and `&r T`.** Structural: if `T` contains `@b U`,
substituting `b` with a longer-lived `b'` is safe.

**Invariance in `T` for `&r mut T`.** A mutable borrow allows both reading and writing.
Reading requires the actual type to be at least as capable as the expected type; writing
requires the actual type to accept values of the expected type. These are contradictory
except when the types are identical.

### 4.3 Interaction with wellformedness

Covariance and wellformedness constrain in opposite directions for nested types:

- **Wellformedness**: `@a @b T` requires b's scope to enclose a's (inner lives longer).
- **Covariance**: a longer-lived `b'` may substitute for `b` in `@b T`, producing
  `@a @b' T` — also well-formed, since `b'` encloses `a`.

Once wellformedness is satisfied at the allocation site, covariance allows passing values
with longer-scoped tags to functions that require shorter guarantees.

---

## Alternatives considered

### Explicit wellformedness bounds

An explicit `T: WellFormed<a>` bound in generic signatures would move the check to the
definition site. The downside is annotation noise in the common case where `T` has no
allocator tags. The instantiation-site approach (§3.3) keeps generic signatures clean.
An opt-in `WellFormed<a>` can be added later if instantiation-site errors prove
confusing.

### Invariance for `@a T`

Making `@a T` invariant in the allocator tag would force exact scope matching and
eliminate variance questions, but significantly reduces composability: a function
expecting `@outer Node` could not accept `@inner Node` even when `inner` outlives
`outer`.

---

## Unresolved questions

1. **Full subtype formalisation.** This RFC states variance informally. A formal
   subtyping judgement suitable for a type-checker specification is deferred.

2. **Variance for user-defined generic types.** When a user writes `struct Foo<T, A: Alloc>`,
   variance in `A` and `T` should be derived from the struct's fields. The derivation
   rules are a natural follow-on.

3. **Allocator parameters on closures.** RFC-0065 defers the grammar for allocator
   parameters on closure literals. The rules here apply to closures by analogy.

---

## References

- RFC-0063 (Allocator Handles) — allocator parameters; `@a T`; sendability; §4's
  tag-only parameter form, added to the bounds table in §2.3.
- RFC-0065 (Allocator Ergonomics) — elision; the forms that make generic allocator
  parameters less frequently needed in simple cases.
- RFC-0067 (Lifetime Anchors) — `&r T` / `&r mut T`; lifetime anchors; variance in `T`
  for mutable borrows.
- RFC-0068 (Struct-Owned Allocators) — `(@a: AllocType)` and the implicit-`a` rule for
  `impl` blocks; §1.3 of this RFC provides the complementary rule for external allocators.
