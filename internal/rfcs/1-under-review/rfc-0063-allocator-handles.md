---
id: rfc-0063
title: "Allocator Handles"
date: '2026-06-24'
updated: '2026-07-06'
---

> **Status — under review.** Rewritten 2026-07-05 from the original "Region Handles"
> draft. The original RFC's triple-duty premise — a region name is simultaneously a
> lifetime tag, a disjointness proof, and an allocation strategy — fails once RFC-0066
> (individual drop/move-out) is admitted: a value's lifetime and its allocator's scope
> are two distinct things. The split model separates them. This RFC specifies the
> allocator half. Lifetime anchors are specified in RFC-0067 (Reference Types). The
> unified model is documented in `reports/memory-model/lifetimes-vs-regions-2026-07-02.md`.
> Depends on RFC-0071 (Ownership and Move Semantics). Annotation-reduction ergonomics
> are deferred to RFC-0065. RFC-0069, RFC-0085, RFC-0087 are retracted.
>
> **Updated 2026-07-06:** added tag-only allocator parameters (§4, "Tag-only
> parameters — preservation without a handle"). The existing "naming only" form
> (a real value parameter that is never used to allocate) is a real but avoidable
> cost — the storage-preservation analysis in
> `reports/memory-model/lifetimes-vs-regions-2026-07-02.md` §12 works through why.
> Companion changes: RFC-0065 (elision for the new form), RFC-0066 §3a (extraction
> is never implicit at a plain-parameter call site — the rule this form's existence
> depends on), RFC-0077 (bounds table).

## Summary

An **allocator** is an allocation arena with a scope — an ordinary runtime value that
implements the `Alloc` aspect. Allocators are first-class: they are passed as value
parameters, stored in structs, and named in function signatures. The name of an
allocator binding appears as a compile-time tag on any value allocated into it: `@a T`
is the type of a `T` allocated in allocator `a`. That tag determines:

- **where** the backing memory lives and how it is freed;
- **whether** the value can cross a fiber boundary (sendability);
- **that** two values with distinct allocator tags provably cannot alias (disjointness).

This RFC specifies:

1. the `Alloc` aspect and the four stdlib allocators;
2. the `@a T` pointer type and the `@a expr` allocation expression;
3. allocator parameters in the value channel `()`;
4. tag-only allocator parameters — a compile-time-only form for code that relays
   an allocator tag without ever allocating through it;
5. sendability rules.

Lifetime anchor tracking (`&r T`, `&r mut T`) is specified in RFC-0067. Elision and
call-site inference are in RFC-0065.

---

## Motivation

The original region RFC (this document's prior version) gave a region name triple duty:
lifetime tag, disjointness witness, and allocator. That design held only when a value
lived exactly as long as its region. RFC-0066's move-out breaks that: a value can leave
its allocator's scope while the allocator continues to hold other data, so a value's
lifetime and its allocator's scope are different things.

The reframe is the natural resolution: allocators handle the "where" question
(allocation strategy, backing memory, disjointness); lifetime anchors handle the "how
long" question (borrow validity). Each concept gets exactly the role it was always meant
to play.

The renamed and split model preserves the two properties that made regions distinctive:

- **Concrete errors.** Allocator bindings are real values in scope, so diagnostics say
  "value outlives `arena`" rather than explaining an abstract `'a` the programmer never wrote.
- **Disjointness.** Two values with distinct allocator tags cannot alias; structured
  parallelism over allocator-tagged data requires no separate proof.

---

## 1. The `Alloc` aspect

The allocator interface is an aspect with one required associated type:

```metel
aspect Alloc {
    type AllocationError;
}
```

`AllocationError` is the error type an allocation may produce. Assigning `!` (the never
type) declares the allocator infallible — OOM panics rather than returning an error. The
compiler collapses `Result<@a T, !>` to `@a T` at infallible allocation sites.

The four stdlib allocators are all infallible:

| Allocator | `AllocationError` | OOM | Scope |
|-----------|-------------------|-----|-------|
| `BumpAlloc` | `!` | panics | scoped bump arena; `T: !Drop` for move-out |
| `AutoAlloc` | `!` | panics | scoped; compiler-chosen strategy (RFC-0073) |
| `Heap` | `!` | panics | global; sendable; per-slot free |
| `LocalHeap` | `!` | panics | thread-local; per-slot free |

Custom allocators assign their own error type. A bounded pool allocator may assign
`AllocationFailed` (a unit struct); callers propagate or handle the error at each
allocation site. Infallible custom allocators assign `!`.

---

## 2. Allocator types: `@a T`

`@a T` is the type of a value of type `T` owned by allocator `a`. It is an affine
owned type — non-`Copy` by default, moved rather than copied. The allocator tag `a`:

- is a compile-time property erased at runtime;
- names a specific allocator **instance**, not just a type (unlike `Box<T, A>`);
- serves as a static disjointness witness: `@a T` and `@b T` with distinct `a`, `b`
  cannot alias.

`@a T` behaves as an owned value. Auto-deref (RFC-0067) makes field access and method
dispatch transparent; extracting a plain `T` is via RFC-0066.

### Instance-level vs type-level tags

Two allocations into different `BumpAlloc` instances have different tags even though
their allocator type is the same. This is what gives Metel properties Rust's `Box<T, A>`
cannot express:

- **Lifetime safety without phantom lifetimes.** In Rust you thread `&'a BumpArena`
  through every containing type. In Metel, the allocator value `a` is the tag; when `a`
  drops, all `@a T` values are statically invalid, and the error names `a` directly.
- **Static disjointness between instances.** `@a T` and `@b T` with `a ≠ b` are
  provably non-aliasing at compile time.

---

## 3. Allocation expressions

`@a expr` allocates `expr` into allocator `a` and produces `@a T`:

```metel
let node = @a Node { val: 1, next: null };
// node : @a Node
```

This desugars to `a.alloc(expr)`. The `@a` prefix is a language construct, not a method
call; it may be elided to `@expr` when exactly one allocator is in scope (RFC-0065).

**Fallible allocators.** When `a::AllocationError ≠ !`, `@a expr` has type
`Result<@a T, E>`. The caller propagates with `?`:

```metel
let node = @pool Node { val: 1 }?;
// pool::AllocationError = AllocationFailed
```

**Type-directed allocation.** When a `let` binding carries an explicit `@a T`
annotation, the right-hand side may be a bare `T` — the declared type drives allocation:

```metel
let node: @a Node = Node { val: 1, next: null };
// equivalent to: let node = @a Node { val: 1, next: null }
```

Type-directed allocation applies at the binding level only; nested sub-expressions
require an explicit `@`.

---

## 4. Allocator parameters in the value channel

Allocators are values. They are passed as value parameters with the `@` prefix:

```metel
fun build_node(@a: BumpAlloc, val: i64) -> @a Node {
    @a Node { val, next: null }
}
```

The `@` prefix on the parameter name marks it as an allocator parameter: the name `a`
is simultaneously the runtime handle (you can call allocation through it) and the
compile-time tag (appears in `@a Node` return type). This mirrors the address-of sigil
— `@` means "this is about allocation."

**Generic allocators.** When the allocator type is not fixed, declare it as a type
parameter bound to `Alloc`:

```metel
fun build_node<A: Alloc>(@a: A, val: i64) -> @a Node {
    @a Node { val, next: null }
}
```

**Multiple allocators.** Multiple allocator parameters are listed in the value channel:

```metel
fun transfer<T, A: Alloc, B: Alloc>(@src: A, @dst: B, val: @src T) -> @dst T {
    @dst val: T   // move-out from src, allocate into dst
}
```

**Naming only.** A function that does not allocate but needs to name an allocator in its
signature (to relate input and output tags) simply declares the parameter and never uses
`@a expr`:

```metel
fun identity<A: Alloc>(@a: A, val: @a Node) -> @a Node { val }
```

### Tag-only parameters — preservation without a handle

The "naming only" form above still takes a real runtime value parameter `(@a: A)`,
even though `identity`'s body never calls `a.alloc(...)`. Under monomorphization the
parameter is never touched at runtime — it exists purely so the type checker has a
binding to attach the tag `a` to. That is a real, if small, cost: a parameter slot
for a capability the function never exercises.

A function or struct that only **relays** an already-allocated value — never
allocates through it, never inspects which concrete `Alloc` type it is — does not
need the runtime handle at all. It needs only the *name*, exactly the way a lifetime
anchor (RFC-0067) needs only a name and no accompanying value. Declare it in the
type-parameter channel, bare and unbounded:

```metel
fun identity<@a>(val: @a Node) -> @a Node { val }
```

`<@a>` is a **tag-only allocator parameter**: a compile-time-only name, erased at
runtime, with no paired value parameter and no `Alloc` bound. It may appear in `@a T`
positions for typing, exactly like `(@a: A)`'s tag does — but it grants no allocation
capability. A function or struct declaring `<@a>` (with no paired `(@a: A)`) may not
contain any `@a expr` allocation expression; that always requires the full
value-channel form.

No `Alloc` bound is needed on `<@a>` because it never has to prove anything about a
*concrete* allocator kind — it only asserts that `a` names an allocator instance
already in scope somewhere in the caller's chain, and that instance already
discharged its own `Alloc` obligation at the point it was actually created. `<@a>`
merely relays that fact; it does not re-derive it.

`<@a>` elides the same way lifetime anchors do (RFC-0065). `identity` above elides
fully to:

```metel
fun identity(val: @Node) -> @Node { val }
```

Here the bare `@` sigil (no name, no declaration) means "this position carries a
storage tag, generic over whatever it is" — resolved by the same rule that already
governs `@` elision (RFC-0065 §1): if a real value-channel allocator is in scope,
`@` names it (the existing rule); otherwise `@` introduces a fresh, per-call-site
tag-only parameter, following the same single-input/self/ambiguous structure already
given for lifetime anchor elision (RFC-0065 §2). Explicit `<@a>` is written out only
when that inference is ambiguous — for instance, relating two independently-tagged
parameters that must carry the *same* tag.

This is not new inference machinery: a `<@a>`-declared (or elided) function is
checked exactly like an ordinary `<T>` generic — its body is type-checked once,
abstractly, against the tag, and monomorphized per call site. A body that does not
actually preserve a single consistent tag on every path — one branch returning the
input, another fabricating a fresh, untagged value — fails to type-check, for the
same reason a generic `fun f<T>(x: T) -> T { ... }` fails to type-check if some
branch does not produce a `T`.

**Where extraction is still required.** `<@a>` / elided-`@T` positions only ever
*relay* a value — they never convert an allocator-tagged `@a T` into a genuinely
untagged, storage-erased `T`. That conversion is extraction (RFC-0066 §3), and it is
never implicit: passing an `@a T` value to a plain (`@`-free) `T` parameter without
explicit ascription is a compile error, not a silent move-out (RFC-0066 §3a). Use the
tag-only form when the goal is passing storage through unexamined; use explicit
ascription when the goal is genuinely discharging the tag.

---

## 5. Creating a scoped allocator

Two equivalent forms, following the pattern established for any scoped resource:

**Closure-scoped** — `BumpAlloc::scoped` passes the allocator to a closure via the
value channel; the arena is freed when the closure returns:

```metel
BumpAlloc::scoped((@a) -> {
    let node = @a Node { val: 1, next: null };
    process(&node);
});   // arena freed here; any @a T still live is a borrow-check error
```

**Variable-scoped** — `let a = BumpAlloc::new()` binds the allocator to `a`. The arena
is freed when `a` is dropped (explicitly or at scope end). The borrow checker rejects
any live `@a T` at the point of drop:

```metel
let a = BumpAlloc::new();
let node = @a Node { val: 1, next: null };
process(&node);
drop(a);   // error if node or any borrow of node is still live
```

`BumpAlloc::scoped` is equivalent to a block with an implicit drop at the end. The
closure form creates a visible syntactic boundary; the `let` form is more flexible (the
allocator can be passed as an argument, span multiple calls, or be dropped early).

---

## 6. Structs with allocator parameters

A struct that holds externally-allocated values carries a lifetime anchor parameter
`<&a>` expressing that its contents are valid while allocator `a` is alive:

```metel
struct Parser<&a> {
    input: @a String,
    pos:   u64,
}

fun parse<&a>(@a: BumpAlloc, src: String) -> Parser<&a> {
    Parser { input: @a src, pos: 0 }
}
```

`<&a>` in the struct declaration is a lifetime anchor parameter (RFC-0067). The `&a`
anchor and the `@a` allocator parameter use the same name — the binding `a` is both the
runtime allocator and the compile-time lifetime anchor bounding the struct's validity.

A struct that *owns* its allocator uses primary constructor syntax (RFC-0068):

```metel
struct Cache(@a: BumpAlloc) {
    entries: @a HashMap<Key, Val>,
}
```

The two forms are complementary:

| Form | Allocator owned by | Anchor visible externally |
|------|--------------------|--------------------------|
| `struct Foo<&a>` | Caller | Yes — `a` in `Foo<&a>` type |
| `struct Foo(@a: BumpAlloc)` | The struct | No — `a` is internal |

---

## 7. Sendability

Allocator sendability is per-kind:

```
Sendable across fibers:         @Heap T   (when T: Send)
Thread-local only:              @LocalHeap T
Not sendable (scope-bound):     @a T  where a is BumpAlloc, AutoAlloc, or any scoped allocator
```

More precisely: `@a T` implements `Send` if and only if `a: Send` and `T: Send`.
`Heap` implements `Send`; `LocalHeap`, `BumpAlloc`, `AutoAlloc`, and all scoped
allocators do not. A scoped allocator could be backed by stack memory; sending it to
another fiber would dangle immediately.

This is checked structurally at the type level — no separate annotation is needed.

---

## 8. Diagnostics

Single-allocator checking reduces to liveness of a named binding. Errors name the real
allocator:

```
error: value of type `@a Node` outlives allocator `a`
  --> src/main.mt:12:5
   | `a` is dropped at line 10; `node` is still live here
```

The programmer sees the name they wrote, not an abstract `'a`. For multi-allocator code
the same principle holds: each allocator tag in the error is a concrete name in scope.

---

## 9. Unresolved questions

None.

---

## References

- RFC-0065 (Allocator Ergonomics) — `@`-elision, call-site inference, and elision
  for tag-only parameters (§1a).
- RFC-0066 (Allocated Value Extraction) — how to obtain `T` or `&T` from `@a T`;
  §3a specifies why extraction never happens implicitly at a plain-parameter call
  site, which is what makes the tag-only form necessary rather than redundant.
- RFC-0067 (Reference Types) — lifetime anchors `&r T`, `&r mut T`; the split from
  allocator lifetime.
- RFC-0068 (Struct-Owned Allocators) — `struct Foo(@a: BumpAlloc)` primary constructor
  syntax for allocator ownership.
- RFC-0071 (Ownership and Move Semantics) — affine types, drop order, `Copy`/`Drop`.
- RFC-0073 (AutoAlloc) — compiler-managed scoped allocator.
- RFC-0077 (Allocator Generics) — generic allocator bounds, wellformedness, variance.
