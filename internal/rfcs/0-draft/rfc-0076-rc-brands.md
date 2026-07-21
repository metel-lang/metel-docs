---
id: rfc-0076
title: "Brand Types"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0063 (Allocator Handles), RFC-0071 (Ownership and
> Move Semantics), RFC-0072 (Negative Bounds). Introduces brands as a general
> language feature: phantom type parameters that carry unforgeable allocation-site
> identity. `Rc` and `Arc` (RFC-0074) using brands for precise alias analysis is one
> application among several.

> **Drift audit — 2026-07-21.** Fixed mechanically: RFC-0063's title (`Region Handles` →
> `Allocator Handles`), its retired `@[r] T` bracket syntax (now `@a T`), and the
> `BumpRegion`/`AutoRegion` type names (now `BumpAlloc`/`AutoAlloc`). Flagged but *not*
> fixed: the "Why regions do not need explicit brands" section rests on RFC-0063's
> abandoned triple-duty premise and needs re-derivation (see the note there). Added:
> Unresolved Question on binding-site brands, raised while asking whether `&T` could become
> `Ref<T, 'b>`.

## Summary

A **brand** is a phantom type parameter with two properties:

1. **Freshness** — each brand introduction site produces a brand that the compiler
   treats as distinct from every other brand, regardless of structural type equality.
2. **Rigidity** — the compiler never unifies two distinct brands. A brand can only
   equal itself.

Brands carry no runtime data. They exist purely at the type level to give the compiler
a way to distinguish values that would otherwise be indistinguishable — two `Rc<Node>`
pointers to different cells, two arena allocators in different scopes, two capability
tokens with different permissions.

Any type can carry a brand parameter. The compiler provides two mechanisms for
introducing fresh brands: an explicit **brand block** and an implicit **allocation-site
brand** for types that opt in. Brand parameters propagate through type inference and
are erased at compile time.

Beyond simple identity, brands enable a general pattern — **token-gated access** —
where a linear token `Token<'b>` holds the permission to access a set of branded
resources, and `&mut Token<'b>` is the access key enforced by the standard borrow
checker. This pattern applies to RC memory cells, effect handlers, concurrent fibers,
and shared mutable state. In every case the soundness argument is the same: ordinary
`&mut` exclusivity, no runtime check required.

---

## Motivation

Several language features need to distinguish values of the same type by identity
rather than by structure:

- `Rc<T, 'b>` and `Rc<T, 'c>` are smart pointers of the same structural type but to
  different cells. Without brands, there is no type-level way to express "does not
  alias this specific cell."
- Two `BumpAlloc` handles in the same scope allocate into different arenas. Without
  brands, the type system cannot prevent mixing pointers from the two arenas.
- A capability token for a file descriptor and a capability token for a socket are
  both "capability tokens" — but they should not be interchangeable.

In all three cases, the required distinction is **identity**, not **structure**. Two
values of the same structural type need to be different types when they represent
different things. Brands are the mechanism for this.

### Why regions do not need explicit brands — and why Rc and Arc do

> **Needs re-derivation (flagged 2026-07-21, not resolved here).** This section's argument
> rests on the premise that a handle is "simultaneously the runtime allocator, the
> compile-time lifetime tag, and the identity token — three roles unified in one value."
> That is precisely the triple-duty premise RFC-0063 **abandoned** when it was rewritten
> on 2026-07-05: under the split model the allocator (RFC-0063) and the lifetime anchor
> (RFC-0067) are separate things, exactly because RFC-0066's individual move-out showed a
> value's lifetime and its allocator's scope can diverge. So the conclusion — that scoped
> allocators need no explicit brand because the handle already serves as one — no longer
> follows from a premise that holds, and must be re-derived against the split model. The
> conclusion may well survive; the argument for it does not, as written. Terminology below
> has been mechanically updated (`BumpRegion`/`AutoRegion` → `BumpAlloc`/`AutoAlloc`), but
> the reasoning has deliberately been left alone rather than patched, since patching it
> would disguise a real design question as an editing pass.

Handle regions (`BumpAlloc`, `AutoAlloc`) introduce a fresh runtime handle at each
scope entry. That handle is simultaneously the runtime allocator, the compile-time
lifetime tag, and the identity token — three roles unified in one value. The handle's
freshness per scope is the brand: two `BumpAlloc` handles are already distinct types
because the compiler treats each introduction site as producing a new region kind.

Unique-ownership regions (`Heap`, `LocalHeap`) introduce no handle and no aliasing.
Unique ownership means the pointer itself is the proof of exclusive access; no identity
token is needed because aliasing cannot occur.

`Rc<T>` and `Arc<T>` are not regions — they are library smart pointer structs (RFC-0074).
They require explicit brand parameters because aliasing is their entire purpose and they
have no runtime handle to serve as an implicit identity token. The brand parameter `'b`
in `Rc<T, 'b>` fills exactly the role that the runtime handle fills for scoped regions:
it makes two pointers to the same cell type-distinguishable from two pointers to
different cells.

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
// Rc carries the brand as a type parameter — no field needed at runtime
struct Rc<T, brand 'b> { inner: @[Heap] RcInner<T>, _brand: PhantomBrand<'b> }
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

Types may declare that each construction of that type implicitly introduces a fresh
brand. This is the **allocation-site brand** mechanism. A type opts in by declaring a
brand parameter that the compiler fills with a fresh brand per call site:

```metel
let a: Rc<Node> = Rc::new(Node { val: 1 });   // a: Rc<Node, '_>, brand inferred as fresh
let b: Rc<Node> = Rc::new(Node { val: 2 });   // b: Rc<Node, '_>, different fresh brand
```

The compiler desugars this as if each construction were wrapped in a `brand` block:

```metel
// Conceptual desugaring:
brand 'a { let a: Rc<Node, 'a> = Rc::new(Node { val: 1 }); ... }
brand 'b { let b: Rc<Node, 'b> = Rc::new(Node { val: 2 }); ... }
```

The allocation-site form is the ergonomic entry point for types like `Rc` and `Arc`.

### Brand propagation

Brands propagate through type parameters like lifetimes. A function that takes a
branded value and returns a value with the same brand makes the aliasing relationship
visible to callers:

```metel
// Clone preserves the brand — caller knows the result aliases the input
fun clone<T, brand 'b>(self: &Rc<T, 'b>) -> Rc<T, 'b>

// Constructor — fresh brand per call (existential return)
fun new<T>(val: T) -> Rc<T>   // brand is existential, fresh per call site
```

The compiler infers which form applies from the function body: if the return value
is a fresh allocation the brand is existential; if it derives from a branded input
the brand propagates.

### Brand rigidity

The compiler enforces two rules:

1. **Non-unification.** Two distinct brand introduction sites produce brands that the
   type checker never unifies, even if both appear in the same type position. A function
   that returns `Rc<T, 'b>` for some `'b` cannot return values from two different
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
let a = Rc::new(Node { val: 1 });
let b = a.clone();               // compiler infers b has same brand as a
let c = Rc::new(Node { val: 2 });   // compiler infers fresh brand for c
```

Brands appear in error messages only when relevant to the reported issue.

---

## Applications

### Shared pointer alias analysis (RFC-0074)

`Rc<T, 'b>` and `Arc<T, 'b>` carry a brand identifying their backing cell. Clone
preserves the brand. `NotCapturing<Rc<T, 'b>>` becomes a precise alias exclusion: it
excludes same-brand bindings (aliases of the same cell) and allows different-brand
bindings (independent cells).

```metel
let a = Rc::new(Node { val: 1 });   // a: Rc<Node, 'a>
let b = a.clone();                   // b: Rc<Node, 'a> — same cell
let c = Rc::new(Node { val: 2 });   // c: Rc<Node, 'c> — different cell

// NotCapturing<Rc<Node, 'a>> excludes b (same brand), allows c (different brand)
// Future: RcToken<'a> gates exclusive write access to the 'a cell (RFC-0074 §6.1)
// Present: a.get_mut() returns None because b is a live alias
```

### Arena identity

A `BumpAlloc` could carry a brand to prevent mixing pointers from different arenas:

```metel
// Two arenas — same type, different brands
brand 'r1 {
    let arena1 = BumpAlloc::new<'r1>();
    brand 'r2 {
        let arena2 = BumpAlloc::new<'r2>();
        let x = @[arena1] Node { val: 1 };
        let y = @[arena2] Node { val: 2 };
        // x: @arena1 Node — cannot be used where 'r2 is expected
    }
}
```

This RFC does not mandate that `BumpAlloc` carries a brand; it provides the mechanism
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

### Token-gated access

A brand token held uniquely proves exclusive access to all resources carrying the
same brand. The pattern has three components:

- A **token** `Token<'b>` — a non-`Copy`, non-`Clone` struct; holds no data, only
  the brand. Its linearity means exactly one live binding exists at any time.
- **Cells** — resource holders of any kind, each parameterised by `'b`.
- **`&mut Token<'b>`** — the access key. The borrow checker ensures only one
  `&mut token` exists at a time, granting exclusive access to all same-brand cells.
  No runtime check. Soundness is ordinary `&mut` exclusivity.

The three components are separate values. Cells may be freely aliased via `Rc<_>` or
shared via `Arc<_>`; the token is the one value that cannot be aliased. Access to cell
data requires passing the token borrow — and that borrow is the proof.

This pattern generalises the GhostCell design (Yanovski et al., 2021) to any resource
that needs scoped, exclusive, identity-specific access. Three concrete instantiations
follow.

#### RC memory — `RcToken<'b>`

```metel
struct RcToken<brand 'b> { _brand: PhantomBrand<'b> }
struct RcCell<brand 'b, T> { value: T, _brand: PhantomBrand<'b> }

impl<brand 'b, T> RcCell<'b, T> {
    fun borrow_mut<'s>(self: &'s RcCell<'b, T>, _token: &mut RcToken<'b>) -> &'s mut T {
        &mut self.value
    }
}

brand 'b {
    let token = RcToken::<'b>::new();
    let cell_a: Rc<RcCell<'b, I32>, 'b> = Rc::new(RcCell { value: 0, _brand: PhantomBrand });
    let alias_a = cell_a.clone();   // multiple RC owners — fine

    cell_a.borrow_mut(&mut token).value = 42;
    // alias_a is still live; soundness from &mut token, not from RC count
}
```

`RcToken<'b>` is the future direction for static exclusive mutable access to
`Rc<T, 'b>` cells, as described in RFC-0074 §6.1. It does not require proving
the RC count is one; it requires holding the token exclusively.

#### Effect handlers — `HandlerToken<'b, E>`

An effect handler with mutable state has the same aliasing problem as an RC cell:
multiple call sites may reference the same handler concurrently. A `HandlerToken`
separates the permission from the handler state:

```metel
struct HandlerToken<brand 'b, E> { _brand: PhantomBrand<'b> }
struct HandlerCell<brand 'b, E, S> { state: S, _brand: PhantomBrand<'b> }

impl<brand 'b> HandlerCell<'b, Logger, List<String>> {
    fun record(self: &HandlerCell<'b, Logger, List<String>>, msg: String,
               _token: &mut HandlerToken<'b, Logger>) {
        self.state.push(msg);
    }
}

brand 'h {
    let token = HandlerToken::<'h, Logger>::new();
    let handler: Rc<HandlerCell<'h, Logger, List<String>>, 'h> =
        Rc::new(HandlerCell { state: List::new(), _brand: PhantomBrand });

    // Explicit dispatch to this specific handler:
    handler.record("first message", &mut token);
    handler.record("second message", &mut token);

    // handler.state contains ["first message", "second message"]
}
```

`&mut HandlerToken<'h, Logger>` is the proof that no other caller is currently
accessing handler `'h`'s state. Non-reentrant handlers become statically
non-reentrant: attempting to call `handler.record` while already holding `&mut token`
is a borrow error. See §Algebraic effects for how this integrates with `perform` dispatch.

#### Structured concurrency — `JoinToken<'b>`

A fork produces a `JoinToken<'b>` that must be consumed at the join point. The token
is linear — it cannot be dropped without joining:

```metel
struct JoinToken<brand 'b, T> { _brand: PhantomBrand<'b> }

fun fork<brand 'b, T, F>(f: F) -> JoinToken<'b, T>
    where F: forall<brand 'b> fun() -> T + Send

fun join<brand 'b, T>(token: JoinToken<'b, T>) -> T

brand 'fiber {
    let join_token: JoinToken<'fiber, I32> = fork::<'fiber>(|| heavy_computation());
    do_other_work();
    let result: I32 = join(join_token);   // consumes token; waits for fiber
}
// brand 'fiber is gone; no dangling fiber handle
```

The brand `'fiber` ensures a join token can only be paired with the fork that produced
it — you cannot accidentally join the wrong fiber when multiple forks are in scope with
different brands. The linearity of `JoinToken<'b, T>` makes fiber abandonment a compile
error: the only way to consume the token is to join. This gives structured concurrency
the same static guarantee that scoped regions give to allocation.

This is a forward-looking application. Full specification is contingent on RFC-0064
(Fork-Join Parallelism).

#### The general shape

All three instantiations follow the same structure:

| Resource | Token | Cells | `&mut token` grants |
|---|---|---|---|
| RC-aliased memory | `RcToken<'b>` | `Rc<T, 'b>` | Exclusive write to all `'b` cells |
| Effect handler state | `HandlerToken<'b, E>` | `HandlerCell<'b, E, S>` | Exclusive write to handler state |
| Concurrent fiber | `JoinToken<'b, T>` | Fiber-local values | Join and collect result |

In every case: the token is unique, the cells are freely shareable, and `&mut token`
is the access key enforced entirely by the existing borrow checker.

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

#### Handler identity and static dispatch

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

#### Handler state exclusivity via `HandlerToken`

When a handler carries mutable state — accumulating results, tracking budgets — the
token-gated access pattern from §Token-gated access applies directly. A
`HandlerToken<'h, E>` is the proof of exclusive access to handler `'h`'s state; the
`perform` desugaring passes this token to the handler cell, which requires `&mut token`
to mutate its state. Non-reentrant handlers (handlers that must not be called while
already running) become statically non-reentrant: re-entrant calls would require a
second `&mut HandlerToken<'h, E>`, which the borrow checker rejects.

Stateless handlers (those that only read or that produce fresh values on each invocation)
need only `&HandlerToken<'h, E>` — shared read access, which supports multiple concurrent
`perform` calls at the same handler.

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

Typestate, algebraic effects, token-gated access, and brands all address the same
underlying need: the type system must distinguish values that are structurally identical
but semantically distinct — the same file in different states, the same effect type in
different handler scopes, the same capability type in different permission contexts.
Brands provide the identity dimension; the token pattern provides the exclusive-access
dimension.

| Mechanism | Tracks *what* | Tracks *which* | Exclusive access |
|---|---|---|---|
| Typestate (phantom state) | Yes | No | No |
| Effect annotations (`^IO`) | Yes | No | No |
| Capability objects | Partial | No | Via `&mut cap` |
| Brands alone | No | Yes | No |
| Brands + typestate | Yes | Yes | No |
| Brands + capabilities | Yes | Yes | Via `&mut cap` |
| Brands + token-gated access | No | Yes | Yes — `&mut token` over all `'b` cells |
| Brands + typestate + token | Yes | Yes | Yes |

The combinations compose without new primitives:
- **Brands + typestate**: linear state machines where identity is preserved across
  transitions (`File<'f, Open>` → `File<'f, Closed>`, same file, different state).
- **Brands + capabilities**: effect systems where each handler instance is type-distinct
  and unforgeable.
- **Brands + token-gated access**: exclusive mutable access to arbitrarily-aliased cells
  — RC nodes, handler state, or fiber results — without runtime checks.

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

4. **Binding-site brands — required if references are ever branded** (raised 2026-07-21
   while asking whether `&T` could become `Ref<T, 'b>`; recorded here, not proposed).
   Neither introduction mechanism in this RFC fits references. Allocation-site brands are
   fresh **per construction site**, and for a reference the construction site is the `&`
   expression — so `&x` written twice would mint two *different* brands for the same
   storage, making two references to one variable type-incompatible. That is backwards:
   reference identity has to be minted where the *storage* is created (the binding) and
   then **inherited** by every `&` of it. Call it a binding-site or storage-site brand;
   it is a third mechanism, not an application of the two here.

   Two further findings from the same discussion, both relevant to whether this is worth
   building. First, **brands would give provenance, not cell identity** — this RFC's own
   framing is "unforgeable *allocation-site* identity," so `&q.x` and `&q.y` share an
   allocation and would share a brand. Branded references therefore would *not* answer the
   "should two references be equal only when pointing at the same variable" question
   (metel-core#263, deliberately open). Second, **ergonomics is the gating constraint**:
   `Ref<T, 'b>` on the language's most-used type needs near-total brand elision — Rust's
   lifetime elision exists for exactly this — and that is the same verbosity objection
   already raised against the allocator annotations in RFC-0065. Establish elision before
   committing, not after.

   Note also that this whole direction is blocked on a representation change: `&T` is a
   structural `Type::Reference(Box<Type>)` with exactly one slot, so no brand parameter can
   be added to it at all until references become nominal. Not proposed here either.

5. **`RcToken<'b>` and `Arc<'b>` across fiber boundaries.** `RcToken<'b>`
   grants exclusive access to all `Rc<T, 'b>` cells within a single fiber. When
   `Arc<T, 'b>` clones are distributed across fibers, the brand correctly identifies
   them as aliases, but a single `RcToken<'b>` cannot be the access key — it would
   need to coordinate across fiber boundaries. Whether this requires a distinct
   `SharedToken<'b>` with lock-like semantics, or whether `Arc<'b>` simply does not
   participate in token-gated access and remains runtime-only (`get_mut`), is unresolved.
   Deferred to the concurrency RFC cluster (RFC-0064).

5. **Brand equality across modules.** If a library returns `Rc<T, 'b>` from an
   opaque function, the caller cannot inspect the brand's origin. Whether opaque brands
   from library functions are treated as always-distinct or sometimes-equal requires a
   visibility rule. Deferred.

---

## References

- RFC-0063 (Allocator Handles, accepted) — `@a T` allocator-owned value types. Note this
  RFC was rewritten 2026-07-05 from the original "Region Handles" draft, splitting the
  allocator from the lifetime anchor (RFC-0067); the `@[r] T` bracket syntax this RFC
  previously cited no longer exists. `Rc` and `Arc` are library structs, not allocators
  (RFC-0074).
- RFC-0071 (Ownership and Move Semantics) — `Clone`; clone-preserving brands make the
  alias relationship visible in the type.
- RFC-0072 (Negative Bounds) — `NotCapturing<T>`; with brands, this bound becomes a
  precise alias exclusion for `Rc<T, 'b>`.
- RFC-0074 (Shared Pointers — Rc and Arc) — `Rc<T, 'b>`, `Arc<T, 'b>` as library
  smart pointer structs with brand parameters; the RC alias analysis application of brands.
- Report: `algebraic-effects-and-memory-model.md` — evidence-passing model for
  algebraic effects; brands on handler instances enable O(1) type-directed dispatch.
- Report: `capability-objects.md` — capability-based effect model; branded capabilities
  make effect contexts type-distinct and unforgeable.
- GhostCell (Yanovski et al., 2021) — demonstrates that phantom brand types enable
  safe interior mutability without runtime cost; directly inspires the GhostCell
  application in §Applications.
- Haskell `ST` monad — the original rank-2 brand introduction (`runST`) that ensures
  brands cannot escape their introduction scope.
- RFC-0064 (Fork-Join Parallelism) — `JoinToken<'b>` structured concurrency application
  (§Token-gated access) is contingent on this RFC being accepted.
- Report: `shared-ownership-survey-2026-06-29` — survey of Ante, Rust RC APIs, Pony
  reference capabilities, and GhostCell/qcell; establishes that `RcToken<'b>` is the
  correct future direction for static exclusive access to `Rc<T, 'b>` (RFC-0074 §6.1).
