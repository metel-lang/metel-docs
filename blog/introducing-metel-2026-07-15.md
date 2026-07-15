---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors: [vladislav]
tags: [language-design, metel, roadmap]
---

# Introducing Metel

We probably agree on the fact that the world does not need another amateur C++/Rust/Zig/Go/Odin clone, so the honest introduction is this: I started building Metel because I wanted to build a programming language.

At first, the goal was small and personal: a statically typed, Rust-influenced interpreted language with a garbage collector. I wanted to learn, and I wanted to build something that felt like a real language rather than a parser demo.

That version did not stay small for long.

Once the basics existed, I started reading more seriously about memory safety, type systems, ownership, regions, linear capabilities, structural typing, and brand-like identity systems. The project slowly stopped being "my small Rust-like interpreter" and became a more interesting question:

What if I tried to combine several well-researched ideas into a language with its own point of view?

That question is what Metel is now.

{/* truncate */}

## The Shape Of The Project

Metel is an exploratory systems language. It is not trying to beat Rust, Zig, or C++ at their own game, and it is not production-ready. The project is an attempt to design a language around a few bets that I find worth taking seriously:

- allocation should be explicit when it matters;
- resource usage should be visible in the type system;
- ordinary code should still read like ordinary modern code;
- lifetime errors should name real program bindings, not abstract `'a` variables;
- ownership should eventually work over structured values, not only whole values.

Earlier, I thought of Metel mainly as "the allocator-aware language." That is still part of its identity, but the better description is broader. The current design treats allocators as the first major use case of a lower-level substrate: structural shape, field-sensitive ownership, brand-like identity, and lifetimes named after actual bindings.

In other words, allocators are not the whole story. They are where the story starts to get interesting.

## What Already Exists

Metel is not just notes in a folder anymore. There is a real interpreter, a module system, generics, exhaustive pattern matching, a standard library with `Perhaps`, `Result`, `List`, strings, host-backed `fs`/`env`/`process` modules, and a growing specification and RFC process.

Recent work has also moved a large batch of type-system and surface-language ideas into the implementation: negative bounds and impls, associated types, bottom type `!`, structural aspect bounds, coherence checks, `return`/`break`/`continue` as expressions, and the newer `public`/`var`/`extend` surface syntax.

For example, this is ordinary Metel today:

```metel
fun main() -> i64 {
    let nums = List::from([1, 2, 3, 4]);

    let total = nums
        .filter((x: i64) -> boolean { x % 2 == 0 })
        .map((x: i64) -> i64 { x * 10 })
        .fold(0i64, (acc: i64, x: i64) -> i64 { acc + x });

    println("total = ${total}");
    return total;
}
```

The deepest ownership and allocation model is still ahead of the runtime. The interpreter is a feedback mechanism, not a finished semantic engine. That gap is real, and it is the main discipline problem in the project: not inventing endlessly, but deciding what is settled enough to build.

That also makes the interpreter useful in a very specific way. It is not proof that the whole design works, but it is enough machinery for syntax, modules, generics, aspects, and standard-library code to push back on design ideas before they become too abstract.

One more thing I want to be explicit about: Metel is heavily AI-assisted. The implementation of the interpreter especially has been built with a lot of help from AI tools. The design work is also AI-assisted, but in a different way: the ideas, priorities, trade-offs, and final decisions are personal and carefully curated. AI has been useful as a collaborator, critic, and accelerator, not as a substitute for deciding what Metel should be.

## The Ideas I Care About

The part of Metel I currently find most worth pursuing is the separation between two questions that many systems languages tie tightly together:

1. Where does a value live?
2. For how long is a reference to it valid?

In Metel's design, allocators answer the first question. Lifetime anchors answer the second. Brands may eventually answer a third: which specific resource, region, or cell family are we talking about?

### Allocators

The allocator side of the design makes storage an explicit program-level choice. [Zig](https://ziglang.org/documentation/master/#Choosing-an-Allocator) and [Odin](https://odin-lang.org/docs/overview/#allocators) already make allocator-passing a normal part of programming, and Rust has an [`Allocator` API](https://doc.rust-lang.org/std/alloc/trait.Allocator.html). Metel's bet is slightly different: allocator identity should be visible in the language's own type and syntax rules, not only in library APIs.

That matters because allocator choice is often part of an invariant. A value may live in a bump arena, a long-lived heap, or a scoped temporary region, and APIs sometimes need to preserve that fact rather than merely receive an allocator argument by convention.

```metel
let user = @Heap User { name: "Ada" };
```

If `Heap` is the only allocator in scope, the common case can stay terse:

```metel
import std::mem::Heap;

let user1 = @User { name: "Ada" };
let user2 = @User { name: "Alan" };
```

Scoped allocators would make the same idea local:

```metel
BumpAlloc::scoped((@a) -> {
    let node = @Node { value: 42 }; // `a` is the only allocator in scope
    process(&node);
});
```

The important point is not the exact spelling. It is that a function should be able to preserve storage in its signature instead of silently erasing it:

```metel
fun identity(value: @Node) -> @Node { value }
```

That is the small version of the bigger goal: memory-safe allocator-aware programming where storage is explicit enough for the checker to reason about, but not so noisy that ordinary heap allocation becomes ceremony.

### Lifetimes

Lifetimes are not a new idea. [Rust](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html) is the obvious reference point, and [Move](https://arxiv.org/abs/2205.05181) also has a static reference-safety model. The Metel direction is to use real binding handles where possible instead of abstract lifetime parameters everywhere.

```metel
fun first(x: &Str, y: &Str) -> &x Str {
    x
}
```

The name in the return type refers to a real binding already present in the function. The signature says directly that the result is tied to `x`.

The common case should still avoid annotation. A method like `as_slice(&self) -> &Byte[]` should not need to invent a lifetime name just to say "the result comes from `self`." The explicit form is for the cases where there is real ambiguity.

This is design syntax, not implemented surface syntax today, and the exact spelling may still change. The accepted direction is the important part: lifetime anchors should be names from the program, not invented variables that only exist in the type signature.

### Records

Records are interesting to me because they may let nominal and structural typing coexist without choosing one as the whole language.

Purely structural systems are powerful. [TypeScript](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) is built around structural compatibility, and [PureScript](https://book.purescript.org/chapter3.html) has records as a standard feature. But structural compatibility can also blur distinctions that are meaningful in a program. If everything matches because the shape lines up, it becomes easier to frankenstein together values that should remain conceptually distinct. That is one reason TypeScript developers reach for [branded types](https://www.learningtypescript.com/articles/branded-types) and other [nominal-typing patterns](https://www.totaltypescript.com/workshops/advanced-typescript-patterns/branded-types/what-is-a-branded-type).

What I want to explore in Metel is narrower: ordinary nominal types, plus an explicit structural `record` view when the checker needs to reason about fields.

The bridge would be opt-in. A nominal type can derive `ToRecord` to expose its fields as a structural row, and `FromRecord` to allow reconstruction from the full row again:

```metel
@derive(ToRecord, FromRecord)
struct Handle {
    fd: i32,
    label: String,
}

let handle = Handle { fd: 3, label: "log" };
let row: record { fd: i32, label: String } = handle.to_record();
let handle2 = Handle::from_record(row);
```

Those two aspects are deliberately separate. Reading a type into a record is not the same promise as reconstructing the type from arbitrary field values; types with constructor-checked invariants may want `ToRecord` without derived `FromRecord`.

The real use case is partial consumption. Sometimes a program needs to say: this field is gone, these fields are still here.

```metel
@derive(ToRecord, FromRecord)
struct RcBox<T> {
    strong: AtomicUsize,
    weak: AtomicUsize,
    value: T,
}

fun drop_value<T>(cell: &var RcBox<T>) {
    let view = cell.to_record_mut();
    let value = move view.value;
    drop(value);
    // view is now `&var record { strong: AtomicUsize, weak: AtomicUsize }`
}
```

This is a design sketch, not executable Metel. `to_record_mut()` would come from `ToRecord`; `from_record_mut()` would only be available again once the row has been restored to the full `RcBox<T>` shape. The motivating case is `Rc`/`Arc`-style teardown: the payload may need to be destroyed when the last strong reference disappears, while the allocation and counters remain alive until weak references are gone too. In Rust, this is exactly the kind of internal logic that tends to involve `unsafe` and `ManuallyDrop`. A field-sensitive record view might let the type system model that transition directly.

That is the part I find more interesting than "structural typing" on its own. The nominal type remains the normal interface. The structural view appears only when the program deliberately takes a value apart and the checker needs vocabulary for what remains.

### Brands

Brands are less designed than allocators and lifetimes, but they seem to fill an important identity-tracking gap.

The prior art is strong. Rust's [`PhantomData`](https://doc.rust-lang.org/std/marker/struct.PhantomData.html) carries type-level information without runtime data. Haskell's [`ST`](https://hackage.haskell.org/package/base/docs/Control-Monad-ST.html) uses a state-thread parameter to keep mutable state from escaping. [GhostCell](https://plv.mpi-sws.org/rustbelt/ghostcell/) uses Rust lifetimes to imitate brands: a `GhostCell` and its token share a lifetime that acts less like "how long does this borrow live?" and more like "which cell family is this?"

That is close to the role I am interested in, but Metel may not need to encode all identity through lifetimes. Allocator identities, lifetime anchors, and pure identity brands might be different roles of the same underlying idea:

```metel
fun preserve_storage<@a>(value: @a Node) -> @a Node { value }

fun borrow_from_value<&l>(x: &Str) -> &l Str { x }

fun preserve_identity<'b>(cell: RcCell<'b, Node>) -> RcCell<'b, Node> {
    cell
}
```

The exact syntax is undecided. The point is conceptual: allocators, lifetimes, and identity brands all give the type checker a concrete identity to preserve and compare.

If that unification holds, it could keep the design from becoming three unrelated special cases. An allocator brand says where storage comes from. A lifetime brand says which binding bounds a borrow. An identity brand says which family of cells or permissions a value belongs to. Different roles, same underlying channel.

## Why Build It?

A lot of languages sound interesting in design documents. The hard part is whether the ideas still hold together when they collide with generics, borrowing, closures, partial moves, collections, modules, diagnostics, and performance constraints.

Metel is at that stage now. Some ideas have worked. Some have been reopened after implementation exposed problems. That is healthy. I would rather have a project that corrects itself than one that preserves a fake sense of certainty.

I am building Metel because it gives me a place to test a combination I do not see assembled quite this way elsewhere: allocator-aware programming, binding-named lifetime reasoning, resource-sensitive types, and eventually field-sensitive ownership over structured data.

The immediate job is not to add ten more ambitious ideas. It is to keep turning the parts that already define the language's shape into working machinery.

If Metel ends up being worth anyone else's time, it will not be because it looked clever in RFCs. It will be because the language demonstrates that these ideas can form a coherent, teachable, implementable whole.
