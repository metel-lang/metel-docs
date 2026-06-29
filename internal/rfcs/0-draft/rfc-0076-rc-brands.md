---
id: rfc-0076
title: "RC Brand Types — Allocation-Site Identity for Shared Pointers"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0074 (Shared Ownership). Extends `Rc` and `Arc`
> with a phantom brand parameter that uniquely identifies each backing cell at the type
> level. Enables a precise, type-level alias check for the `unique` keyword and its
> canonical form, replacing the conservative binding-level clone-tracking from RFC-0074.

## Summary

In RFC-0074, the `unique` keyword is safe because the compiler performs a binding-level
alias analysis: it tracks which in-scope bindings are known clones of the pointer being
mutated and excludes them from the block. This works, but the analysis is limited to
what the compiler can observe at the syntactic level — it cannot extend to pre-built
closures or function-boundary alias relationships.

This RFC introduces **brand types**: a phantom type parameter on `Rc` and `Arc` that
records allocation-site identity. Every `@[Rc] T` allocation produces a fresh brand;
`clone` preserves it; independent allocations produce distinct brands. The type
`@[Rc<'b>] T` carries the brand `'b` — two bindings pointing to the same cell share
a brand, two bindings pointing to different cells have incomparable brands.

With brands, the alias check becomes a type-level property. `NotCapturing<@[Rc<'b>] T>`
means precisely "does not capture a binding that aliases this specific cell," not
"does not capture any `@[Rc] T` at all." The `unique` canonical form is restored as a
well-typed, precise function, and the keyword forms are sugar over it.

---

## Motivation

### The precision gap

RFC-0074 §2 describes the `unique` block's alias analysis as excluding "known clones"
— bindings derived from the mutated pointer via `.clone()` calls. Two problems remain:

1. **Pre-built closures.** For `Rc::unique(val, f)` where `f` is a pre-stored closure
   variable, the compiler cannot inspect `f`'s capture set at the call site. There is no
   type-level bound that expresses "does not alias `val`'s specific cell" without
   inspecting the closure body.

2. **Cross-function aliases.** If a function returns a clone of an RC pointer it
   received as an argument, the caller's alias graph gains an edge the compiler may
   not have tracked syntactically.

Both problems share a root: the compiler needs to ask "does this closure alias a
specific cell?" but the type system only knows "does this closure capture a specific
type?" Those are different questions without brand types.

### Brands close the gap

With a brand parameter `'b` on `Rc<'b>`:

- `NotCapturing<@[Rc<'b>] T>` means exactly "does not capture an alias of this cell."
- The check works for pre-built closures — the compiler checks the type, not the body.
- The canonical form `Rc::unique` becomes a regular, well-typed function that any
  user can call.

---

## Design

### Brand parameters on `Rc` and `Arc`

`Rc` and `Arc` gain a phantom brand parameter:

```metel
// 'brand identifies the backing cell — carries no runtime data
impl<'brand> Region for Rc<'brand> {
    type AllocationError = !;
}
impl<'brand> SharedRegion for Rc<'brand> {}

impl<'brand> Region for Arc<'brand> {
    type AllocationError = !;
}
impl<'brand> SharedRegion for Arc<'brand> {}
impl<'brand> Send for Arc<'brand> {}
impl<'brand> Sync for Arc<'brand> {}
```

The brand is a **phantom parameter** — it has no runtime representation. It is a
distinct kind from region scope tags: scope tags track where a value lives; brands
track which cell a pointer points to.

### Fresh brand introduction

Each `@[Rc] T { ... }` allocation expression introduces a **fresh, rigid brand**
assigned by the compiler:

```metel
let a = @[Rc] Node { val: 1 };   // a: @[Rc<$0>] Node — brand $0, fresh
let b = @[Rc] Node { val: 2 };   // b: @[Rc<$1>] Node — brand $1, fresh, $1 ≠ $0
```

Rigid brands are **never unified** with each other by the type checker — not even when
both sides have the same underlying type. Each allocation site is the sole source of
its brand. Brands are named `$0`, `$1`, … internally; in error messages the compiler
uses the binding name of the first owner (see §Brand inference).

### Clone preserves the brand

`Clone` for `@[Rc<'brand>] T` is typed to preserve the brand:

```metel
// Clone for @[Rc<'brand>] T, derived by SharedRegion
fun clone<'brand, T>(self: @[Rc<'brand>] T) -> @[Rc<'brand>] T
```

Clones share the brand of the original:

```metel
let a = @[Rc] Node { val: 1 };   // a: @[Rc<$0>] Node
let b = a.clone();                // b: @[Rc<$0>] Node — same cell, same brand
let c = @[Rc] Node { val: 1 };   // c: @[Rc<$1>] Node — new cell, new brand
```

`a` and `b` are type-level witnesses to the same cell. `c` is a distinct cell even
though its value is identical.

### `NotCapturing` with brands

With branded types, `NotCapturing<@[Rc<'b>] T>` is a precise alias check:

| Binding | Brand | Captured? |
|---|---|---|
| `b` (clone of `a`) | `$0` = `'b` | Excluded |
| `c` (independent alloc) | `$1` ≠ `'b` | Allowed |

This is the key improvement over the un-branded design: `c` is a different cell and
its capture is safe, yet an un-branded `NotCapturing<@[Rc] Node>` would have rejected
it.

### `unique` canonical form restored

The `unique` canonical form in the `SharedRegion` aspect is now well-typed and precise:

```metel
aspect SharedRegion: Region {
    type AllocationError = !;

    fun unique<'brand, T, U, F>(ptr: @[Self<'brand>] T, f: F) -> U
        where F: fun(&mut T) -> U,
              F: NotCapturing<@[Self<'brand>] T>;
}
```

where `Self<'brand>` denotes the implementing tag parameterised by the brand (e.g.,
`Rc<'brand>` when `Self = Rc`).

The call:

```metel
Rc::unique(val, fun(s: &mut Spaceship) -> () {
    s.engine = Engine::Impulse { fuel: 100 };
});
```

is now a plain function call. The compiler checks `NotCapturing<@[Rc<$0>] Spaceship>`
on the closure — excluding same-brand bindings, allowing all others. No closure-body
inspection required; the brand in the type carries all the information needed.

### Keyword forms as sugar

The keyword forms from RFC-0074 §2 remain and desugar to the canonical form:

```metel
unique val as s { BODY }
// desugars to:
Rc::unique(val, fun(s: &mut T) -> _ { BODY })
```

The `NotCapturing` check on the desugared closure is the same brand check as above.
Form B (implicit rebinding) and form C (deferred) desugar identically.

### Brand inference

Brands are inferred in nearly all positions; the programmer never writes `Rc<'b>` in
normal code. The compiler assigns internal fresh brands and uses the first-owner binding
name for error messages:

```metel
// Written:
let a = @[Rc] Node { val: 1 };
let b = a.clone();
let c = @[Rc] Node { val: 2 };

unique a as node {
    node.val = c.val;   // OK — c: @[Rc<brand_c>] Node, different brand
    node.val = b.val;   // ERROR — b: @[Rc<brand_a>] Node, same brand as a
}
```

Error message:

```
error: `b` cannot be used inside `unique a` — it aliases the same cell
  --> src/main.mt:6:15
   |
2  |     let b = a.clone();
   |             - `b` derives its brand from `a`
6  |     node.val = b.val;
   |                ^ same brand as `a`
```

When brands appear in signatures, the compiler shows them only when they are relevant
to the error and hides them when the signature is unambiguous.

### Function boundaries

When a function takes or returns branded pointers, the brand participates in the
function's type:

**Brand-preserving function** — the brand is a type parameter:

```metel
// Returns a clone of its argument; brand is shared with input
fun dup<'b>(x: @[Rc<'b>] Node) -> @[Rc<'b>] Node {
    x.clone()
}
```

The caller knows the returned value aliases the argument:

```metel
let a = @[Rc] Node { val: 1 };
let b = dup(a);   // b: @[Rc<brand_a>] Node — compiler knows b aliases a
```

**Fresh-brand function** — each call produces a distinct brand (existential return):

```metel
// Creates a new node; returned brand is fresh per call site
fun make_node(val: I32) -> @[Rc] Node {
    @[Rc] Node { val }
}

let a = make_node(1);   // a: @[Rc<brand_a>] Node
let b = make_node(1);   // b: @[Rc<brand_b>] Node — distinct brand, distinct cell
```

Brand inference determines which form a function has based on its body. If the
return value is always a fresh allocation, the brand is existential. If it is a
transformed version of an input with the same brand, the brand is a parameter.

---

## Interaction with RFC-0074

### `unique` keyword forms

The keyword forms in RFC-0074 §2 desugar to the canonical form. With brands, the
desugared `NotCapturing` check is precise — same-brand bindings are excluded;
different-brand bindings are allowed. The examples in RFC-0074 §6.3 (unrelated shared
pointers are not excluded) hold by type rather than by binding-level analysis.

### `Clone` and `Drop`

`Clone` and `Drop` are derived by `SharedRegion` exactly as before. `Clone` is now
brand-preserving (same brand in, same brand out). `Drop` is brand-agnostic (any
`@[Rc<'b>] T` can be dropped regardless of brand).

### The six stdlib regions

The region table from RFC-0074 §5 is unchanged in semantics. `Rc` and `Arc` now carry
an additional phantom brand parameter but are otherwise identical.

---

## Examples

### Safe mutation with unrelated pointers

```metel
let a = @[Rc] Spaceship { engine: Engine::StringTheory { ... } };
let b = @[Rc] Spaceship { engine: Engine::Impulse { fuel: 50 } };
let c = a.clone();   // c aliases a

// Using the canonical form:
Rc::unique(a, fun(s: &mut Spaceship) -> () {
    s.engine = Engine::Impulse { fuel: b.engine.fuel() };
    //                                 ^ OK: b has a different brand from a
});

// c cannot be used inside the closure — same brand as a (now consumed)
```

### Brand-preserving helper function

```metel
fun replace_engine<'b>(ship: @[Rc<'b>] Spaceship, fuel: I32) {
    Rc::unique(ship, fun(s: &mut Spaceship) -> () {
        s.engine = Engine::Impulse { fuel };
    });
}

let a = @[Rc] Spaceship { ... };
let b = a.clone();   // b: @[Rc<brand_a>] Spaceship

replace_engine(a, 100);
// After the call, a is consumed; b is still live but the unique block is complete.
```

### Pre-built closure

```metel
let a = @[Rc] Counter::new(0);
let b = a.clone();

// Build a closure that does NOT capture b
let increment = []() -> () {};   // empty capture list — NotCapturing<@[Rc<brand_a>] Counter> holds

Rc::unique(a, increment);   // OK: increment is known not to capture same-brand bindings

// Build a closure that DOES capture b
let bad = [b]() -> () { b.read() };   // captures b: @[Rc<brand_a>] Counter

Rc::unique(a, bad);   // ERROR: bad captures a same-brand binding
```

---

## Alternatives considered

### Binding-level clone tracking (RFC-0074 approach)

RFC-0074 §2 tracks clone provenance syntactically. This works for inline closure
literals and keyword forms but fails for pre-built closures and function-boundary
aliases. Brands solve both cases at the type level with no body inspection.

### Runtime RC == 1 check

Checking `rc_count(ptr) == 1` at runtime and panicking otherwise is Rust's `Rc::get_mut`
approach. It works but cannot be statically prevented from panicking. Brands make the
check static.

### No brands — keyword forms only

RFC-0074 without this RFC restricts `unique` to keyword forms (where the compiler can
inspect the block body). Brands restore the canonical form as a regular function,
enabling `unique` on pre-built closures and function-composed alias graphs.

---

## Unresolved questions

1. **Brand introduction mechanism.** Rigid fresh brands at allocation sites (the
   approach described here) require the compiler to generate and track brand constants.
   An alternative is rank-2 polymorphism (the Haskell `runST` / `GhostCell` pattern),
   where the brand is a universally-quantified type variable scoped to a closure. Both
   are sound; the rigid-constant approach is more ergonomic but requires the compiler
   to reason about brand identity globally. Deferred.

2. **Brand inference at function boundaries.** The distinction between brand-preserving
   functions (explicit `'b` parameter) and fresh-brand functions (existential return) must
   be inferred from the function body. The inference algorithm — and what happens when
   the body is opaque (foreign functions, trait objects) — is unspecified. Deferred.

3. **`unique` for `Arc` across fiber boundaries.** If `a: @[Arc<'b>] T` is cloned and
   the clone is sent to another fiber, both fibers may attempt to call `unique` on their
   respective handles simultaneously. Brands correctly identify them as aliases (same
   brand), so a `unique` block in one fiber must ensure the other fiber's handle is not
   live. The mechanism for statically enforcing this across fiber boundaries — if any
   exists — is unresolved. Deferred to the concurrency RFC cluster.

4. **Brands as a distinct kind.** Brands are different from region scope tags: a scope
   tag identifies where a value lives; a brand identifies which cell a pointer points
   to. Whether brands warrant a distinct syntactic kind (e.g., `@[Rc<cell: 'b>] T`
   vs. `@[Rc<'b>] T`) or share the existing lifetime-parameter syntax is a surface
   design question. Deferred.

5. **Interaction with weak pointers.** If `WeakRc<'b>` is introduced (RFC-0074 §Unresolved
   question 1), it must carry the same brand as the `Rc<'b>` it was downgraded from.
   The interaction between weak pointers, brands, and the `unique` alias check is
   unspecified. Deferred.

---

## References

- RFC-0074 (Shared Ownership) — `SharedRegion`, `Rc`, `Arc`, `unique` keyword; this
  RFC refines the `unique` alias check from binding-level to type-level.
- RFC-0072 (Negative Bounds) — `NotCapturing<T>` is a marker aspect; brands make its
  application to `@[Rc<'b>] T` precise rather than conservative.
- RFC-0065 (Region Ergonomics) — brand inference follows the same elision discipline
  as region tag elision; brands are hidden when unambiguous.
- Haskell `ST` monad — the `runST` / rank-2 brand pattern that inspired the soundness
  argument for brand introduction.
- GhostCell (Yanovski et al., 2021) — a Rust library demonstrating that phantom brand
  types enable safe interior mutability without runtime overhead.
