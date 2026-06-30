---
id: rfc-0076
title: "Brand Types"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0063 (Region Handles), RFC-0071 (Ownership and
> Move Semantics), RFC-0072 (Negative Bounds). Introduces brands as a general
> language feature: phantom type parameters that carry unforgeable allocation-site
> identity. `Rc` and `Arc` (RFC-0074) using brands for precise alias analysis is one
> application among several.

## Summary

A **brand** is a phantom type parameter with two properties:

1. **Freshness** — each brand introduction site produces a brand that the compiler
   treats as distinct from every other brand, regardless of structural type equality.
2. **Rigidity** — the compiler never unifies two distinct brands. A brand can only
   equal itself.

Brands carry no runtime data. They exist purely at the type level to give the compiler
a way to distinguish values that would otherwise be indistinguishable — two `@[Rc] Node`
pointers to different cells, two arena allocators in different scopes, two capability
tokens with different permissions.

Any type can carry a brand parameter. The compiler provides two mechanisms for
introducing fresh brands: an explicit **brand block** and an implicit **allocation-site
brand** for types that opt in. Brand parameters propagate through type inference and
are erased at compile time.

---

## Motivation

Several language features need to distinguish values of the same type by identity
rather than by structure:

- `@[Rc<'b>] T` and `@[Rc<'c>] T` are pointers of the same type but to different
  cells. Without brands, `NotCapturing<@[Rc] T>` cannot express "does not alias this
  specific cell."
- Two `BumpRegion` handles in the same scope allocate into different arenas. Without
  brands, the type system cannot prevent mixing pointers from the two arenas.
- A capability token for a file descriptor and a capability token for a socket are
  both "capability tokens" — but they should not be interchangeable.

In all three cases, the required distinction is **identity**, not **structure**. Two
values of the same structural type need to be different types when they represent
different things. Brands are the mechanism for this.

---

## Design

### Brand parameters

A brand parameter is declared like a lifetime parameter but prefixed with the `brand`
keyword in type definitions:

```metel
struct Branded<brand 'b, T> {
    value: T,
    _marker: PhantomBrand<'b>,
}
```

`PhantomBrand<'b>` is a zero-size stdlib type that carries a brand parameter with no
runtime content — the brand equivalent of `PhantomData` in Rust.

Types do not need to hold a `PhantomBrand` field; the brand parameter may appear only
in the context of another type that uses it:

```metel
// Rc carries the brand in its region tag position — no field needed
impl<brand 'b> Region for Rc<'b> { ... }
```

### Brand introduction — explicit form

The `brand` block introduces a fresh brand into a lexical scope:

```metel
brand 'b {
    // 'b is a fresh, rigid brand inside this block
    let token: PhantomBrand<'b> = PhantomBrand::new();
    use_branded(token);
}
// 'b is no longer in scope
```

The brand `'b` is rigid within the block — it does not unify with any other brand,
including brands introduced by other `brand` blocks of identical structure. Two `brand`
blocks in the same function produce two distinct brands.

The explicit form is the desugaring target for all other forms. It corresponds to
rank-2 brand introduction in type theory: the brand is universally quantified over the
block body, preventing any value carrying `'b` from escaping the block.

#### Brand introduction — function form

The `brand` block can be expressed as a higher-order function for use as a library
primitive:

```metel
// Standard library
fun with_brand<R, F>(f: F) -> R
    where F: forall<brand 'b> fun(PhantomBrand<'b>) -> R

// Usage
let result = with_brand(fun<brand 'b>(token: PhantomBrand<'b>) -> I32 {
    ...
});
```

`forall<brand 'b>` is the rank-2 quantifier. It ensures `'b` cannot be unified with
any brand outside the closure.

### Brand introduction — allocation-site form

Types may declare that each allocation of that type implicitly introduces a fresh
brand. This is the **allocation-site brand** mechanism. A type opts in by declaring a
brand parameter without an explicit value in its allocation expression:

```metel
// @[Rc] T { ... } introduces a fresh brand per allocation
let a = @[Rc] Node { val: 1 };   // a: @[Rc<'_>] Node, brand inferred as fresh
let b = @[Rc] Node { val: 2 };   // b: @[Rc<'_>] Node, different fresh brand
```

The compiler desugars this as if each allocation were wrapped in a `brand` block:

```metel
// Conceptual desugaring:
brand 'a { let a = @[Rc<'a>] Node { val: 1 }; ... }
brand 'b { let b = @[Rc<'b>] Node { val: 2 }; ... }
```

The allocation-site form is the ergonomic entry point for types like `Rc` and `Arc`.

### Brand propagation

Brands propagate through type parameters like lifetimes. A function that takes a
branded value and returns a value with the same brand makes the aliasing relationship
visible to callers:

```metel
// Clone preserves the brand — caller knows the result aliases the input
fun clone<brand 'b, T>(self: @[Rc<'b>] T) -> @[Rc<'b>] T

// Constructor — fresh brand per call (existential return)
fun new<T>(val: T) -> @[Rc] T   // brand is existential, fresh per call site
```

The compiler infers which form applies from the function body: if the return value
is a fresh allocation the brand is existential; if it derives from a branded input
the brand propagates.

### Brand rigidity

The compiler enforces two rules:

1. **Non-unification.** Two distinct brand introduction sites produce brands that the
   type checker never unifies, even if both appear in the same type position. A function
   that returns `@[Rc<'b>] T` for some `'b` cannot return values from two different
   brand introduction sites without a type error.

2. **Non-escape.** A value carrying a brand from a `brand` block cannot escape the
   block. This is enforced by the existing lifetime rules: the brand's scope is the
   block, and any reference to the brand outside the block is a lifetime error.

### Brand inference

Brands are inferred in the common case. The programmer does not write `Rc<'b>` in
normal code; the compiler assigns internal brand constants and uses binding names in
error messages:

```metel
// Written — no brand annotations:
let a = @[Rc] Node { val: 1 };
let b = a.clone();   // compiler infers b has same brand as a
let c = @[Rc] Node { val: 2 };   // compiler infers fresh brand for c
```

Brands appear in error messages only when relevant to the reported issue.

---

## Applications

### Shared pointer alias analysis (RFC-0074)

`Rc<'b>` and `Arc<'b>` carry a brand identifying their backing cell. Clone preserves
the brand. `NotCapturing<@[Rc<'b>] T>` becomes a precise alias exclusion: it excludes
same-brand bindings (aliases of the same cell) and allows different-brand bindings
(independent cells).

```metel
let a = @[Rc] Node { val: 1 };   // a: @[Rc<'a>] Node
let b = a.clone();                // b: @[Rc<'a>] Node — same cell
let c = @[Rc] Node { val: 2 };   // c: @[Rc<'c>] Node — different cell

// NotCapturing<@[Rc<'a>] Node> excludes b, allows c
Rc::unique(a, fun(node: &mut Node) -> () {
    node.val = c.val;   // OK
    node.val = b.val;   // ERROR: b has same brand as a
});
```

### Arena identity

A `BumpRegion` could carry a brand to prevent mixing pointers from different arenas:

```metel
// Two arenas — same type, different brands
brand 'r1 {
    let arena1 = BumpRegion::new<'r1>();
    brand 'r2 {
        let arena2 = BumpRegion::new<'r2>();
        let x = @[arena1] Node { val: 1 };
        let y = @[arena2] Node { val: 2 };
        // x: @[BumpRegion<'r1>] Node — cannot be used where 'r2 is expected
    }
}
```

This RFC does not mandate that `BumpRegion` carries a brand; it provides the mechanism
for a future RFC to add it.

### Capability tokens

A brand on a capability type creates an unforgeable token that cannot be confused with
other capability tokens of the same structural type:

```metel
struct FileCapability<brand 'b> {
    fd: I32,
    _brand: PhantomBrand<'b>,
}

// Two file capabilities have different brands — cannot be mixed accidentally
brand 'f1 { let log_cap: FileCapability<'f1> = open_file("log.txt"); ... }
brand 'f2 { let data_cap: FileCapability<'f2> = open_file("data.bin"); ... }
```

### GhostCell-style interior mutability

A brand token held uniquely proves exclusive access to a branded cell:

```metel
struct GhostToken<brand 'b> { _brand: PhantomBrand<'b> }
struct GhostCell<brand 'b, T> { value: T, _brand: PhantomBrand<'b> }

impl<brand 'b, T> GhostCell<'b, T> {
    // Exclusive access requires the unique token for this brand
    fun borrow_mut<'a>(self: &'a mut GhostCell<'b, T>, _token: &mut GhostToken<'b>) -> &'a mut T {
        &mut self.value
    }
}
```

The token `GhostToken<'b>` is unique (not `Clone`). Holding `&mut GhostToken<'b>`
proves no one else has access — the borrow checker enforces this. No runtime check
needed.

### Typestate

Plain typestate uses phantom type parameters to track which state an object is in:

```metel
struct File<State> { fd: I32 }
struct Open {}
struct Closed {}

fun read(f: &File<Open>) -> Bytes { ... }
fun close(f: File<Open>) -> File<Closed> { ... }
```

This answers "what state is this object in?" but not "which object is this?" — two
open files have identical type `File<Open>` and are interchangeable where the type
system is concerned.

Brands answer the identity question. Adding a brand parameter gives each instance a
unique type that persists through state transitions:

```metel
struct File<brand 'b, State> { fd: I32, _brand: PhantomBrand<'b> }

fun open<brand 'b>(path: &String) -> File<'b, Open>
fun read<brand 'b>(f: &File<'b, Open>) -> Bytes
fun close<brand 'b>(f: File<'b, Open>) -> File<'b, Closed>
//                                               ^^
//                       same brand — provably the same file in a new state
```

Two open files are now `File<'f1, Open>` and `File<'f2, Open>` — different types.
A cursor, lock guard, or read buffer that was opened against a specific file can carry
that file's brand, making it a type error to use it with a different file even in the
same state. Typestate expresses *what*; brands express *which*.

#### Brand-indexed state machines

Brands compose naturally with state transition functions that involve multiple objects.
A mutex and its guard can share a brand, proving at compile time that the guard belongs
to the mutex that issued it:

```metel
struct Mutex<brand 'b, T> { ... }
struct MutexGuard<brand 'b, T> { ... }   // same brand as the Mutex it locked

impl<brand 'b, T> Mutex<'b, T> {
    fun lock(self: &'b Mutex<'b, T>) -> MutexGuard<'b, T> { ... }
}

// MutexGuard<'m1, T> cannot be used to unlock Mutex<'m2, T>
```

No runtime ID comparison needed — the type system enforces guard–mutex pairing.

### Algebraic effects

Brands address two distinct problems in algebraic effect systems.

#### Handler identity

When effect handlers are nested, the runtime must determine which handler handles each
effect operation. In the evidence-passing model (RFC report: `algebraic-effects-and-memory-model.md`),
each handler is threaded as a hidden parameter — the brand on a handler instance makes
each nesting level a distinct type, so dispatch is resolved at the type level rather
than by lexical search at runtime:

```metel
brand 'h1 {
    handle<Fail<'h1>> {               // outer handler — brand 'h1
        brand 'h2 {
            handle<Fail<'h2>> {       // inner handler — brand 'h2
                perform Fail<'h2>::throw("inner");   // type directs to 'h2
                perform Fail<'h1>::throw("outer");   // type directs to 'h1
            }
        }
    }
}
```

Without brands, two nested handlers of the same effect type are structurally identical
and the runtime must inspect the handler stack to find the right one. With brands, the
type of the `perform` expression encodes which handler to use — O(1) dispatch with no
stack search.

#### Capability-based effects

The two main approaches to effect tracking in Metel's design space — effect marker
aspects (`^IO`) and capability objects (an `IO` struct passed explicitly) — converge
when the capability carries a brand.

A branded capability is an unforgeable, instance-specific effect permission. It cannot
be fabricated inside a sandbox (brands are not constructible without a brand block);
it cannot be confused with a capability for a different effect context; and it can be
threaded implicitly using the `given`/`using` mechanism from the capability-objects
report:

```metel
struct IO<brand 'io> { _brand: PhantomBrand<'io> }

fun println<brand 'io>(given cap: IO<'io>, s: String) { ... }

// A sandboxed function receives no IO<'_> in its scope — cannot perform IO
// A function in the normal context receives IO<'main> implicitly
```

The brand `'io` identifies the specific IO context. Two separate IO contexts — a test
harness that captures output and the real standard output — have different brands and
are type-incompatible even though both are `IO<_>`. The effect annotation `^IO` is
replaced by the presence or absence of an `IO<'io>` in scope; the brand makes that
presence context-specific and unforgeable.

#### The unifying pattern

Typestate, algebraic effects, and brands all address the same underlying need: the type
system must distinguish values that are structurally identical but semantically distinct
— the same file in different states, the same effect type in different handler scopes,
the same capability type in different permission contexts. Brands provide the identity
dimension that the other two mechanisms lack on their own:

| Mechanism | Tracks *what* | Tracks *which* |
|---|---|---|
| Typestate (phantom state) | Yes | No |
| Effect annotations (`^IO`) | Yes | No |
| Capability objects | Partial | No |
| Brands alone | No | Yes |
| Brands + typestate | Yes | Yes |
| Brands + capabilities | Yes | Yes |

The combination of brands with typestate gives linear state machines where identity
is preserved across transitions. The combination of brands with capability objects
gives effect systems where each handler instance is type-distinct. Neither combination
requires new language primitives beyond what this RFC introduces.

---

## Alternatives considered

### Targeting only `Rc` and `Arc`

An earlier draft of this RFC added brands only to `Rc` and `Arc`. The same mechanism
is useful for arenas, capabilities, and interior mutability patterns — limiting it to
shared pointers would require re-inventing the same machinery for each use case.

### Nominal newtype wrappers

The capability and arena examples can be approximated today using distinct newtype
structs:

```metel
struct LogCapability { fd: I32 }
struct DataCapability { fd: I32 }
```

This works for a fixed number of known types but does not scale to dynamic contexts
where the number of distinct identities is not known at definition time (e.g., an
arbitrary number of open files, or two arenas created in the same generic function).

### Singleton types

A singleton type `Singleton<N: const I32>` distinguishes values by a compile-time
constant. This covers some use cases but requires a constant to exist — it cannot
express "fresh per allocation site" without a global counter, and does not integrate
naturally with the lifetime/borrow system.

---

## Unresolved questions

1. **Brand introduction mechanism.** The `brand` block and `forall<brand 'b>` require
   the language to support rank-2 polymorphism. Whether this is the right mechanism,
   or whether fresh brands can be introduced via a simpler rule (e.g., each binding of
   a brand-parameterised type gets a fresh brand from the compiler), is unresolved.
   Deferred.

2. **Brand kind.** Brands and region lifetime tags are both phantom type parameters
   but represent different things. Whether they share a syntactic kind or are
   distinguished (`brand 'b` vs. `'r` for lifetimes) is a surface design question.
   Deferred.

3. **Brand inference at function boundaries.** The rule for inferring whether a brand
   parameter is existential (fresh per call) or propagating (shared with input) must be
   specified precisely, especially for recursive functions and trait objects. Deferred.

4. **Interaction with `unique` across fiber boundaries.** When `@[Arc<'b>] T` clones
   are distributed across fibers, the brand correctly identifies them as aliases. The
   mechanism for ensuring `unique` blocks in different fibers do not overlap is
   unresolved. Deferred to the concurrency RFC cluster.

5. **Brand equality across modules.** If a library returns `@[Rc<'b>] T` from an
   opaque function, the caller cannot inspect the brand's origin. Whether opaque brands
   from library functions are treated as always-distinct or sometimes-equal requires a
   visibility rule. Deferred.

---

## References

- RFC-0063 (Region Handles) — `@[r] T` pointer types; `Rc` and `Arc` use brands as
  their region tag parameter.
- RFC-0071 (Ownership and Move Semantics) — `Clone`; clone-preserving brands make the
  alias relationship visible in the type.
- RFC-0072 (Negative Bounds) — `NotCapturing<T>`; with brands, this bound becomes a
  precise alias exclusion for `@[Rc<'b>] T`.
- RFC-0074 (Shared Ownership) — `Rc`, `Arc`, `unique`; the RC alias analysis
  application of brands.
- Report: `algebraic-effects-and-memory-model.md` — evidence-passing model for
  algebraic effects; brands on handler instances enable O(1) type-directed dispatch.
- Report: `capability-objects.md` — capability-based effect model; branded capabilities
  make effect contexts type-distinct and unforgeable.
- GhostCell (Yanovski et al., 2021) — demonstrates that phantom brand types enable
  safe interior mutability without runtime cost; directly inspires the GhostCell
  application in §Applications.
- Haskell `ST` monad — the original rank-2 brand introduction (`runST`) that ensures
  brands cannot escape their introduction scope.
- Report: `shared-ownership-survey-2026-06-29` — survey of Ante, Rust RC APIs, Pony
  reference capabilities, and GhostCell/qcell; establishes that `RegionToken<b>` is the
  correct future direction for static exclusive access to `@[Rc<b>] T` (RFC-0074 §6.1).
