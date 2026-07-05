---
id: rfc-0077
title: "Region Generics"
date: '2026-06-29'
---

> **Status — under review.** Moved back from accepted, together with the rest of the
> region RFC cluster (RFC-0063, 0065, 0066, 0067, 0068, 0069, 0073) — see RFC-0063's status
> note and `docs/reports/lifetimes-vs-regions-2026-07-02.md`. Under the proposed split, this
> RFC's wellformedness and variance rules need restating once over **durations** (allocator
> scopes and value lifetimes together), rather than over regions alone. Depends on RFC-0063
> (Region Handles), RFC-0065 (Region Ergonomics), RFC-0068 (Struct-Owned Regions), and
> RFC-0069 (Sub-Region Typing). Fills four gaps in the accepted region RFCs: `impl` and
> `aspect impl` block headers for structs with external region parameters; generic region
> bounds in the bracket channel; wellformedness of `@[r] T` when `T` contains nested
> region-tagged types; and variance rules for region-annotated pointer types.

## Summary

RFC-0063 establishes the bracket parameter channel and shows region parameters on
functions and structs, but leaves four questions open:

1. **`impl` blocks** — how do `impl` and `aspect impl` blocks introduce a region
   parameter for a struct declared with an external `[r]`?
2. **Generic region bounds** — how does a function or struct declare that its region
   parameter must satisfy a region aspect, rather than naming a concrete type?
3. **Wellformedness** — when `T` contains region-tagged types, what constraints on the
   region tags in `T` are required for `@[r] T` to be safe?
4. **Variance** — is `@[r] T` covariant, contravariant, or invariant in its region tag
   `r` and value type `T`?

These four questions arise together in any generic code involving regions. This RFC
answers them.

---

## Motivation

A generic arena-backed collection illustrates all four gaps at once:

```metel
struct ArenaSet<T>[r] {
    data: @[r] List<T>,
}
```

- Writing methods on `ArenaSet<T>[r]` requires an `impl` header with a region
  parameter — the form is not specified by any existing RFC.
- `ArenaSet` should work with any arena, not just `BumpRegion`. There is currently no
  way to express "any region implementing `Region`" in the bracket channel.
- If `T = @[s] Node`, what must hold between `s` and `r` for `@[r] List<@[s] Node>`
  to be safe?
- Can `@[s] ArenaSet<T>[s]` be passed where `@[r] ArenaSet<T>[r]` is expected, if
  `s: Outlives<r>`?

None of these questions are answered by RFC-0063 through RFC-0075.

---

## 1. `impl` blocks with external region parameters

A struct declared with an external region parameter — `struct Foo[r]`, not `struct
Foo[own r]` — introduces that parameter in the `impl` header using the same bracket
syntax:

```metel
struct Parser[r] {
    source: @[r] String,
    pos:    U64,
}

impl[r] Parser[r] {
    fun new(source: @[r] String) -> Parser[r] {
        Parser { source, pos: 0 }
    }

    fun remaining[s](self: &[s] Parser[r]) -> &[r] String {
        &self.source
    }
}
```

`[r]` after `impl` is a bracket parameter declaration. `Parser[r]` is the type being
implemented; `r` is in scope in every method signature and body in the block. The
pattern `[s]` on `remaining` introduces a separate lifetime for the duration of the
borrow of `self` — the same two-lifetime pattern that RFC-0068 §4 describes for
struct-owned regions.

### 1.1 Bounds in the `impl` header

Region bounds follow the same inline form as RFC-0063 §3:

```metel
impl[r: Outlives<outer>] Parser[r] {
    // all methods here receive an r that is guaranteed to outlive outer
}
```

Generic region bounds (§2) compose with the `impl` header in the natural way:

```metel
impl<R: Region>[r: R] Cache<R>[r: R] {
    fun insert[s](self: &mut [s] Cache<R>[r: R], key: Key, val: @[r] Value) { … }
}
```

### 1.2 `aspect impl` blocks

`aspect impl` follows the same header form:

```metel
aspect impl[r] Display for Parser[r] {
    fun fmt[s](self: &[s] Parser[r], buf: &mut Buf) { … }
}
```

The region parameter is on the `aspect impl`, not on the `Display` aspect. Aspects
describe behaviour; regions are a detail of the concrete implementation.

### 1.3 Multiple external region parameters

```metel
struct Pair[r, s] {
    left:  @[r] Node,
    right: @[s] Node,
}

impl[r, s: Outlives<r>] Pair[r, s] {
    fun left_ref[t](self: &[t] Pair[r, s]) -> &[r] Node {
        &self.left
    }
}
```

### 1.4 Owned vs. external — the complete rule

RFC-0068 specifies that for `struct Foo[own r]`, `r` is always implicit in `impl Foo`.
This RFC provides the complementary rule for external region parameters:

| Declaration | `impl` header | `r` in scope |
|---|---|---|
| `struct Foo[own r]` | `impl Foo { … }` | always implicit |
| `struct Foo[r]` | `impl[r] Foo[r] { … }` | explicit bracket |

The owned/external distinction is preserved in the `impl` header: a caller-supplied
region is explicit; the struct-private region is implicit.

---

## 2. Generic region bounds in the bracket channel

RFC-0063 §3 supports two annotation forms for bracket parameters:

| Form | Meaning |
|---|---|
| `[r]` | any infallible region (`AllocationError = !`) |
| `[r: BumpRegion]` | exactly the type `BumpRegion` |

Neither expresses "any region satisfying aspect `A`". This RFC introduces the
**generic region bound** form.

### 2.1 Syntax

A type parameter in `<...>` may be bound to a region aspect. A bracket parameter then
annotates with that type parameter:

```metel
fun alloc_copy<T: Clone, R: Region>[r: R](val: T) -> @[r] T {
    @[r] val.clone()
}

```

`R` is declared in `<...>` with a region aspect bound (`R: Region`, or any aspect that
is itself a supertrait of `Region`). `[r: R]` constrains the bracket parameter `r` to
have concrete type `R`. At the call site, `R` is inferred from the supplied region
handle, or written explicitly as a type argument.

Note: `Rc<T>` and `Arc<T>` are **not** regions (RFC-0074). There is no `SharedRegion`
aspect. Shared-ownership types do not participate in the bracket channel and cannot
appear as region bounds.

### 2.2 Structs

```metel
struct Cache<R: Region>[r: R] {
    data: @[r] HashMap<Key, Value>,
}

impl<R: Region>[r: R] Cache<R>[r: R] {
    fun new() -> Cache<R>[r: R] {
        Cache { data: @[r] HashMap::new() }
    }

    fun get[s](self: &[s] Cache<R>[r: R], key: &Key) -> Perhaps<&[r] Value> {
        self.data.get(key)
    }
}
```

`Cache` is polymorphic over the region kind. A caller using `BumpRegion` gets an
arena-backed cache; a caller using `Heap` gets a heap-allocated cache — with no
specialisation in the library.

### 2.3 Region bounds on `aspect` methods

Aspects do not carry region parameters. Region generics are expressed at the method
level:

```metel
aspect Serialize {
    fun serialize<R: Region>[r: R](self: &Self) -> @[r] Bytes;
}

aspect impl Serialize for Record {
    fun serialize<R: Region>[r: R](self: &Self) -> @[r] Bytes {
        @[r] Bytes::encode(self)
    }
}
```

### 2.4 Bounds table

| Form | Constraint on `r` | Typical use |
|---|---|---|
| `[r]` | any infallible region | allocate, no opinion on region kind |
| `[r: Heap]` | exactly `Heap` | heap-only |
| `[r: R]` where `R: Region` | any region implementing `Region` | region-polymorphic allocation |

The bare form `[r]` is preserved as the ergonomic default. The generic bound form is
used when the region type must be named (as a struct field, or to constrain multiple
parameters consistently).

---

## 3. Wellformedness of `@[r] T` when `T` contains region-tagged types

### 3.1 The wellformedness rule

`@[r] T` allocates a value of type `T` into region `r`. When `T` contains fields of
type `@[s] U`, those fields are stored inside the `r`-allocated slot. For this to be
safe, the inner region `s` must not be freed while the outer allocation in `r` is
still live — otherwise those fields become dangling. The same holds for borrow fields
`&[s] U` and `&mut [s] U`: the data they refer to must remain valid.

> **Wellformedness rule.** `@[r] T` is well-formed if and only if for every region tag
> `s` that appears in `T` (in any field, transitively), `s: Outlives<r>` holds — that
> is, `s` lives at least as long as `r`.

The rule is symmetric with ownership: if `r` owns a slot whose content points into `s`,
then `s` must outlive `r`.

### 3.2 Concrete examples

**Heap pointer stored in a scoped region — safe:**

```metel
BumpRegion::scoped([r]() -> {
    let heap_node: @[Heap] Node = @[Heap] Node { val: 1 };
    let wrapper: @[r] @[Heap] Node = @[r] heap_node;
    // ✓ — Heap outlives every scoped region; Heap: Outlives<r> always holds
});
```

**Scoped pointer stored on the heap — rejected:**

```metel
BumpRegion::scoped([r]() -> {
    let scoped_node: @[r] Node = @[r] Node { val: 1 };
    let bad: @[Heap] @[r] Node = @[Heap] scoped_node;
    // ✗ — r does not outlive Heap; the heap allocation would outlive the scoped node
});
```

**Subscope stored in outer region — rejected:**

```metel
BumpRegion::scoped([outer]() -> {
    BumpRegion::scoped([inner]() -> {
        let inner_node: @[inner] Node = @[inner] Node { val: 1 };
        let bad: @[outer] @[inner] Node = @[outer] inner_node;
        // ✗ — inner drops before outer; inner does not outlive outer
    });
});
```

**Both allocations in the same region — safe:**

```metel
BumpRegion::scoped([r]() -> {
    let node: @[r] Node = @[r] Node { val: 1 };
    let container: @[r] Container = @[r] Container { ptr: node };
    // ✓ — r: Outlives<r> holds trivially; same region, same lifetime
});
```

This last case is the common one for recursive data structures (RFC-0063 §2): every
`@[r]` field is safe to store inside another `@[r]` allocation.

### 3.3 Wellformedness in generic functions

When `T` is a type parameter, the compiler cannot check wellformedness at definition
time. The check is deferred to each instantiation site:

```metel
fun wrap<T>[r](val: T) -> @[r] T { @[r] val }

// instantiation 1: T = U64 — no region tags; trivially well-formed
let a = wrap[my_region](42_u64);

// instantiation 2: T = @[inner] Node — requires inner: Outlives<r]
let b = wrap[outer](inner_node);
// error if inner does not outlive outer:
//   `@[outer] @[inner] Node` is not well-formed:
//   `inner` does not outlive `outer`
//   — note: bound required by `wrap`, instantiated here
```

No wellformedness annotation is required in the generic definition. When the
instantiation bound is non-obvious, the programmer may add an explicit `Outlives` bound
to document the requirement:

```metel
// explicit: callers must ensure that every region tag in T outlives r
fun wrap_constrained<T, S: Outlives<R>, R: Region>[r: R, s: S](val: @[s] T) -> @[r] @[s] T {
    @[r] val
}
```

### 3.4 Interaction with the `transfer` example

RFC-0063 §3 gives:

```metel
fun transfer<T>[src, dst: Outlives<src>](val: @[src] T) -> @[dst] T {
    @[dst] *val
}
```

The bound `dst: Outlives<src>` (dst outlives src) is a semantic intent — the caller
is promoting data to a longer-lived region. It does not satisfy the wellformedness
direction for nested region tags. If `T` itself contains `@[src] U` fields, then
`@[dst] T` would additionally require `src: Outlives<dst>` — the opposite direction.
Those two bounds together would force `src` and `dst` to have the same lifetime, which
is usually too restrictive.

The `transfer` function is therefore only well-formed when `T` does not itself contain
any region-tagged types. When `T` is generic, the compiler enforces this at the
instantiation site per §3.3.

---

## 4. Variance of region-annotated types

### 4.1 Definitions

Variance describes when one type may be silently substituted for another. In the
region system, the relevant substitution is: if `s: Outlives<r>` (s is longer-lived),
may `@[s] T` be used where `@[r] T` is expected?

This RFC uses **covariant** to mean: a longer-lived (more precise) region may
substitute for a shorter-lived (less precise) one. If the substitution is forbidden
regardless of the `Outlives` relationship, the type is **invariant** in that position.

### 4.2 Rules

| Type | Variance in region tag | Variance in value type `T` |
|---|---|---|
| `@[r] T` | covariant | covariant |
| `&[r] T` | covariant | covariant |
| `&mut [r] T` | covariant | invariant |

**Covariance in the region tag.** If `s: Outlives<r>`, then `@[s] T` may be used
where `@[r] T` is expected. The caller is simply providing a longer guarantee than
required. The region tag is "forgotten" at the use site: the function sees `@[r] T`,
unaware that the actual allocation is in `s`.

```metel
fun use_node[r](n: @[r] Node) -> I64 { n.val }

BumpRegion::scoped([outer]() -> {
    BumpRegion::scoped([inner: Outlives<outer>]() -> {
        let n: @[inner] Node = @[inner] Node { val: 42 };
        let v = use_node(n);   // @[inner] Node passed as @[outer] Node — ✓
        //                       inner: Outlives<outer> holds; the substitution is safe
    });
});
```

**Covariance in `T` for `@[r] T` and `&[r] T`.** Region covariance in `T` is
structural: if `T` contains `@[s] U`, substituting `s` with a longer-lived `s'` is
safe. The compiler derives this structurally — no annotation is required.

**Invariance in `T` for `&mut [r] T`.** A mutable borrow allows both reading and
writing through the reference. Reading requires the actual type to be at least as
capable as the expected type; writing requires the actual type to accept values of the
expected type. These two requirements are contradictory except when the types are
identical. `&mut [r] T` does not allow substitution in `T`.

```metel
// ✗ — cannot pass &mut [r] Node where &mut [r] BaseNode is expected,
//     even if Node is "more capable" than BaseNode, because the function
//     could write a BaseNode through the reference, violating Node's invariants
fun take_base_mut(n: &mut [r] BaseNode) { n.val = 0; }

let node: @[r] Node = @[r] Node { val: 1, extra: true };
take_base_mut(&mut node);   // ✗ — invariant in T for &mut
```

### 4.3 Covariance and affine ownership

`@[r] T` is an affine type — it has exactly one owner. The covariance rule allows the
owner to "weaken" the precision of the region tag when passing the value to a consumer.
The value itself is moved; the consumer takes full ownership and the region tag recorded
in the consumer's signature determines the lifetime constraint going forward.

The affine move does not conflict with covariance: the move transfers ownership of the
allocation; the covariance shortens the recorded lifetime to the required minimum. The
allocation in `s` is still freed when `s` drops — the compiler retains the original
`s` tag internally; only the type visible to the consumer is weakened to `r`.

### 4.4 Interaction with wellformedness

Covariance and wellformedness constrain in opposite directions for nested types:

- **Wellformedness**: `@[r] @[s] T` requires `s: Outlives<r]` (inner lives longer).
- **Covariance**: a longer-lived `s'` may substitute for `s` in `@[s] T`, producing
  `@[r] @[s'] T` — also well-formed, since `s': Outlives<r>` holds if `s: Outlives<r>`
  and `s': Outlives<s>`.

The two rules compose: once the wellformedness condition is satisfied at the allocation
site, region covariance allows consumers to pass values with more precise tags to
functions that require less precise ones.

---

## Alternatives considered

### Explicit wellformedness bounds in generic signatures

An explicit `T: WellFormed<r>` or `T: RegionSafe<r>` bound in generic function
signatures would move the wellformedness check from the call site to the definition
site. This allows library authors to document the requirement and enables better error
messages at call sites.

The downside is that `WellFormed<r>` would be a new built-in aspect that must be
derived for every type, and every generic function that allocates into a region would
need to carry it. In the common case where `T` has no region tags, the bound is always
satisfied, so the annotation is pure noise. The deferred-check approach (§3.3) keeps
generic signatures clean at the cost of moving errors to instantiation sites.

This RFC takes the deferred approach as the default. If experience shows that
instantiation-site errors are frequently confusing, an explicit `WellFormed<r>` bound
can be added as a first-class opt-in.

### Invariance in the region tag for `@[r] T`

Making `@[r] T` invariant in `r` would forbid the substitution in §4.2 and force
callers to match region tags exactly. This eliminates all variance questions but
significantly reduces composability: a function expecting `@[outer] Node` could not
accept an `@[inner] Node` with `inner: Outlives<outer>`.

Invariance is the correct choice only for mutable borrows (`&mut [r] T` in `T`), where
unsoundness can result from substitution. For owned pointers and shared borrows,
covariance is sound and necessary for practical generic code.

---

## Unresolved questions

1. **Full subtype formalisation.** This RFC states the variance rules informally. A
   formal subtyping judgement over region-annotated types, suitable for a type-checker
   specification, is deferred.

2. **Explicit `WellFormed<r>` bound.** Whether to add an opt-in `WellFormed<r>` bound
   for library authors who want definition-site error reporting, rather than relying
   solely on instantiation-site checking, is left open.

3. **Variance for user-defined generic types.** When a user writes `struct Foo<T>[r]`,
   the variance of `Foo` in `r` and `T` should be derived automatically from the
   struct's fields (as in Rust's variance inference). The derivation rules are not
   specified here; they are a natural follow-on to the rules in §4.

4. **Region parameters on closures.** RFC-0065 defers the grammar for region parameters
   on closure types and closure literals. The rules in this RFC (generic region bounds,
   `impl` headers, wellformedness) apply to closures by analogy, but the concrete
   syntax is still open.

---

## References

- RFC-0063 (Region Handles) — bracket parameter channel (§3); `Outlives` bounds; the
  `transfer` example (§3) to which §3.4 of this RFC adds a wellformedness caveat.
- RFC-0065 (Region Ergonomics) — elision and inference; the single-region forms that
  make the generic forms in this RFC less frequently needed.
- RFC-0068 (Struct-Owned Regions) — `[own r]` and the implicit-`r` rule for `impl`
  blocks; §1.4 of this RFC provides the complementary rule for external `[r]`.
- RFC-0069 (Sub-Region Typing) — `SubRegion<R: Region>`; the sole pre-existing use of
  a `<R: Region>` generic region bound, now generalised in §2 of this RFC.
- RFC-0074 (Shared Pointers — Rc and Arc) — `Rc<T>` and `Arc<T>` are library structs,
  not regions; they do not appear in the generic region bound table.
