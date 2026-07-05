---
id: blog-regions-not-lifetimes-2026-07-02
title: "Memory without magic: Metel's approach to static safety"
type: blog
created_date: '2026-07-02'
updated_date: '2026-07-04'
---

# Memory without magic: Metel's approach to static safety

Metel is a programming language I've been building out of a personal interest in type systems and memory safety. It started as a toy project and has grown into a more serious design effort — not a Rust competitor, but an exploration of what a memory-safe systems language can look like when you're willing to make different trade-offs.

This post is about the memory model: how Metel handles allocation, borrows, and lifetimes, and the core design principle that ties them together.

## Two jobs, two tools

Every memory-safe language without a garbage collector has to answer two questions for every value:

1. **Where does it live?** Stack, heap, arena, somewhere else?
2. **How long is it valid?** When can something hold a reference to it and know that reference won't dangle?

Rust answers both questions through a single mechanism: lifetimes. A lifetime tags both the allocation's scope and the borrow's validity, and the borrow checker enforces consistency between the two. It works — but it means lifetimes are everywhere, even in code that has no opinion about allocation at all. A function that just reads a field and returns a view into it still has to carry lifetime annotations through its signature.

Metel separates the two questions and gives each its own tool.

**Allocators** answer where a value lives. They are first-class runtime values — ordinary objects you can pass around, store in structs, and name in function signatures. `Heap` is a global allocator. `BumpAlloc` is a scoped bump arena. `AutoAlloc` is a compiler-managed scoped allocator that chooses its strategy freely. You allocate into one with the `@` prefix:

```metel
BumpAlloc::scoped([@a]() -> {
    let node = @[a] Node { val: 42 };
    process(&node);
});
```

The bracket channel `[a]` carries the allocator. `@[a] Node` means "allocate a `Node` into `a`." The allocator's scope is real — `a` is a binding, and when it goes out of scope the arena is freed.

**Lifetime anchors** answer how long a reference is valid. A borrow `&[r] T` carries `r` — not an abstract `'a`-style variable, but a concrete binding name. The borrow is valid for as long as `r` is alive. Multiple anchors mean intersection: `&[r, s] T` is valid while both `r` and `s` are alive.

```metel
fun longest(x: &Str, y: &Str) -> &[x, y] Str {
    if x.len() > y.len() { x } else { y }
}
```

The return borrow is valid while both `x` and `y` are alive. No made-up variable. The names in the bracket slot are the names you already have.

Allocators live in `@[...]`. Lifetime anchors live in `&[...]`. The prefix sigil is the disambiguator — the same bracket channel, two categories, no ambiguity.

## The storage transparency principle

Separating the two questions makes a stronger claim possible: **most code doesn't make storage decisions at all.**

A function that reads a field and returns a view isn't deciding where anything lives or how long it lives — it's just moving a value from one place to another. It shouldn't need storage annotations. In Metel, it doesn't:

```metel
fun get_name(user: &User) -> &Str {
    &user.name
}
```

No `@`, no `&[r]` in the signature. The compiler infers that the returned borrow is anchored to `user`'s borrow, and that inference is right. Storage flows through the function transparently.

This is the Storage Transparency Principle: **any language construct that doesn't explicitly reference an allocator or lifetime anchor is implicitly polymorphic over storage.** Annotations appear at the decision points — allocation expressions and explicit borrow anchors — and nowhere else.

The full language surface partitions into two strata:

**Storage-transparent — no annotation needed:**
- Functions that don't allocate
- Struct definitions without owned allocators
- Closures, pattern matching, operators, type aliases

**Storage-explicit — where annotations appear:**
- Allocation: `@[a] expr`
- Explicit borrow anchors: `&[r] T`
- Struct allocator ownership: `struct Foo[@a] { ... }`
- Passing allocators as values: `fun new(alloc: BumpAlloc)`

If a piece of code requires storage annotations and it's not in that second list, it's a design leak — the feature should be revised until the annotation is gone.

## Elision: the common cases require nothing

Even within the storage-explicit layer, most uses don't need explicit annotations.

**For allocations**, if there's exactly one allocator in scope, a bare `@` without a bracket is enough:

```metel
BumpAlloc::scoped([@a]() -> {
    let x = @Node { val: 1 };   // same as @[a] Node { val: 1 }
    let y = @Node { val: 2 };
    process(&x, &y);
});
```

The moment a second allocator enters scope, elision switches off and you name both explicitly. The ambiguity is caught before it silently picks the wrong one.

**For borrow anchors**, the common cases are covered by three rules:
1. A single input borrow anchor elides to the output
2. If `&self` is present, it wins as the output anchor
3. Otherwise — multiple borrows, no `self` — annotation required

```metel
fun first_char(&self) -> &Char { ... }       // self wins — no annotation needed
fun get(&self, key: &Key) -> &Val { ... }    // self wins over key — no annotation
fun longest(x: &Str, y: &Str) -> &[x, y] Str { ... }  // ambiguous — explicit
```

The annotation only appears at the one point where the compiler genuinely can't infer what you mean.

## Declaring bracket parameters

When a function or struct needs to introduce explicit allocator or lifetime anchor parameters, they go in the bracket channel with an optional prefix that makes the kind visible at the declaration point:

```metel
fun transfer[@a, @b](@[a] T) -> @[b] T { ... }   // two allocator params
fun copy[&r, &s](&[r] T, &[s] U) -> &[r] T { ... }  // two lifetime anchor params
fun mixed[@a, &r](@[a] T, &[r] Config) -> @[a] T { ... }  // one of each
```

`@r` declares an allocator parameter; `&r` declares a lifetime anchor parameter. The prefix mirrors the use-site syntax exactly — `@r` declared, used as `@[r]`; `&r` declared, used as `&[r]`.

The prefix is **optional when unambiguous**. If every use of `r` in the signature is as `@[r]`, the compiler infers it's an allocator parameter and you can write just `[r]`. The prefix is **required** when a declaration has both kinds, or when a parameter is never used in the signature:

```metel
fun process[r](@[r] Data) -> @[r] Result { ... }  // r inferred as allocator — prefix optional
fun mixed[@a, &r](@[a] T, &[r] Config) -> @[a] T { ... }  // mixed — prefixes required
```

Type parameters use the angle bracket channel `<T>` as usual. The two channels stay separate.

## Allocators own their scope

A struct can own an allocator, declared with a bracket parameter:

```metel
struct Cache[@a] {
    entries: @[a] HashMap<Key, Val>,
}
```

The struct's constructor creates `a`; the struct's destructor frees it. Any borrow into `a`'s memory is bounded by the struct's lifetime — the borrow checker derives this from scope nesting, with no explicit constraint annotation needed.

`AutoAlloc` is the allocator for code that wants lifetime safety without choosing a strategy. It's compiler-managed — the compiler picks stack, arena, heap, or inline allocation per-value based on escape analysis — and is observationally equivalent to heap allocation within its scope. The programmer says what, the compiler decides how:

```metel
AutoAlloc::scoped([@a]() -> {
    let node = @[a] Node { val: 1 };   // compiler allocates however it sees fit
    process(&node);
});
```

## Sendability

Allocator sendability is per-kind: `Heap` is sendable across fibers; `LocalHeap`, `BumpAlloc`, `AutoAlloc`, and all scoped allocators are not. An owned value `@[a] T` is sendable iff `a` is sendable and `T` is sendable. Borrows `&[r] T` are never sendable — borrows are scoped to lifetime anchors, and scopes are per-fiber. Cross-fiber sharing uses `Arc`, which transfers ownership rather than a scoped reference.

## Where things stand

The design is ahead of the implementation. The interpreter today has no borrow checker, no allocator, and no lifetime tracking — it deep-clones values and leans on reference counting internally. That's deliberate: the goal right now is a stable design target before building the enforcement machinery. Most of what's described here is a plan, not a runnable program.

The remaining open design questions are small. The grammar rules for elision and bracket-channel disambiguation are still being refined. The ratification process — which of the region RFCs get rewritten, which get retracted — is the next concrete step.

What I'm most pleased with is the Storage Transparency Principle as a design constraint. It gives every future feature proposal a clear test: does this require annotations on code that isn't making storage decisions? If yes, the design needs another pass. That's a sharper criterion than "is this ergonomic?" and I think it'll keep the system honest as the language grows.
