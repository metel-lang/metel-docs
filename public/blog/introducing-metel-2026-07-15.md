---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors:
  - name: Vladislav Parfeniuc
tags: [language-design, metel, roadmap]
---

# Introducing Metel

The world does not need another amateur Rust clone, so the honest introduction is this: I started building Metel because I wanted to build a programming language.

At the beginning, the goal was small and personal. I wanted a statically typed, Rust-influenced interpreted language with a garbage collector, partly as a learning project and partly because building languages is fun in a way that is hard to explain to anyone who has not fallen into that hole themselves.

That version of the project did not stay small for long.

Once the basic language existed, I started reading more seriously about memory safety, type systems, and the different ways languages model ownership and control over resources. That led me into substructural types, uniqueness, linear capabilities, regions, effect systems, structural typing, and brand-like identity systems. At some point the project stopped being "my small Rust-like interpreter" and turned into a more interesting question:

What if I tried to combine several well-researched ideas into a language with its own point of view?

That question is what Metel is now.

{/* truncate */}

## What Metel is trying to be

Metel is an exploratory systems language. It is not trying to beat Rust, Zig, or C++ at their own game, and it is not pretending to be production-ready today. The project is an attempt to design a language that is worth building because it makes a few unusual bets and follows them seriously.

The shortest version of the thesis is this:

- allocation should be explicit when it matters;
- resource usage should be visible in the type system;
- ordinary code should still read like ordinary modern code;
- lifetime errors should name real program bindings, not abstract `'a` variables;
- storage control and ownership should scale beyond "this whole value is movable or borrowable" toward more fine-grained reasoning over structured values.

That is the direction the project has converged on over the last few months.

Earlier, I thought of Metel mainly as "the allocator-aware language." That is still part of its identity, but the more precise version is deeper than that. The current design treats allocators as the first major use case of a lower-level semantic substrate: structural shape, per-field ownership discipline, brand-like identity and provenance, and lifetimes named after actual bindings in the source code.

In other words, allocators are not the whole story. They are the first place where the story gets interesting.

## What already exists

Metel is not just a set of ideas in a notebook anymore.

There is a real interpreter, a module system, generics, exhaustive pattern matching, a standard library with `Perhaps`, `Result`, `List`, strings, host-backed `fs`/`env`/`process` modules, and a growing language specification and RFC process behind it. Recent work has also pushed a large batch of type-system and surface-language RFCs from design into implementation: negative bounds and impls, associated types, bottom type `!`, structural aspect bounds, coherence checks, and several syntax cleanups.

For example, this is the kind of ordinary code Metel can already express today:

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

So the project has crossed the line from toy parser into real language work. There is enough implementation now for design mistakes to become visible in practice, which is exactly the stage I wanted to reach.

One more thing I want to be explicit about: Metel is heavily AI-assisted. The implementation of the interpreter especially has been built with a lot of help from AI tools. I do not want to pretend otherwise. The design work is also AI-assisted, but in a different way: the ideas, priorities, trade-offs, and final decisions are personal and carefully curated. AI has been useful as a collaborator, critic, and accelerator, not as a substitute for deciding what Metel should be.

At the same time, I want to be honest about the current state: the deepest parts of the design are still ahead of the runtime.

The interpreter today does not yet enforce the full ownership and allocation model the language is being designed around. It still acts as a feedback mechanism more than a finished semantic engine. That gap is real, and for a while the project was spending too much energy extending the design and not enough turning accepted ideas into working machinery.

That has started to improve, but it is still the main discipline problem in the project: not inventing endlessly, but deciding what is settled enough to build.

## The ideas I find most promising

The part of Metel I currently find most worth pursuing is its attempt to separate two questions that many systems languages tie tightly together:

1. Where does a value live?
2. For how long is a reference to it valid?

In Metel's design, allocators answer the first question, while lifetime anchors answer the second. The two are related, but they are not the same thing.

### Allocators

The allocator side of the design is appealing to me because it makes storage an explicit program-level choice. Instead of treating allocation as an invisible background detail, Metel treats allocators as ordinary runtime values that can appear in APIs and determine where values live.

The allocator idea is not a novel one. [Zig](https://ziglang.org/documentation/master/#Choosing-an-Allocator) makes allocator-passing a core part of its programming model, and [Odin](https://odin-lang.org/docs/overview/#allocators) has strong built-in support for allocators through its implicit context system. Rust also has an [`Allocator` API](https://doc.rust-lang.org/std/alloc/trait.Allocator.html), though today it is still an unsafe and lower-level interface rather than a first-class language feature.

However, in all of those cases, allocators live primarily at the library/API level rather than inside the language's own type and syntax rules. They are values you pass around, but not something the type system treats as a first-class part of storage and borrow reasoning.

That limits what the type system can say about allocator use. If allocator choice is not represented in types, the language cannot express relationships like "this value lives in allocator `a`" or "this function preserves whatever allocator its argument came from." Metel's bet is that those relationships are worth making explicit.

The thing I want to try to achieve in Metel is memory-safe allocators as first-class language constructs.

```metel
let user = @Heap User { name: "Ada" };
```

Or, if `Heap` is the only allocator in scope:

```metel
import std::mem::Heap;

let user1 = @User { name: "Ada" };
let user2 = @User { name: "Alan" };
```

```metel
BumpAlloc::scoped((@a) -> {
    let node = @Node { value: 42 }; // `a` is the only allocator in scope, so `@Node` elides to `@a Node`
    process(&node);
});
```

The common case can stay simple. `@Heap` makes ordinary long-lived allocation explicit, and when there is exactly one allocator in scope, bare `@` is enough for the compiler to infer which allocator you mean. At the same time, the allocator is still a real program value when you need to pass it around or make storage part of an API contract.

```metel
fun identity(val: @Node) -> @Node { val }
```

This is the other part I like: a function can explicitly preserve storage in its signature instead of silently stripping it away.

### Lifetimes

Lifetimes are also not a new idea. [Rust](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html) is the obvious reference point here, and languages like [Move](https://arxiv.org/abs/2205.05181) also have static reference-safety models. Initially the goal was to avoid lifetimes entirely, but for Metel that turned out to be too restrictive. The current direction is to use real binding handles where possible instead of abstract parameters everywhere.

```metel
fun first(x: &Str, y: &Str) -> &x Str {
    x
}
```

The point is modest but useful: the name refers to a real binding already present in the function. The signature says directly what the result is tied to.

This is design syntax, not implemented surface syntax today, and the exact spelling may still change. The accepted direction is the important part here: lifetime anchors are binding names, not abstract lifetime variables invented only for the type signature.

```metel
fun get_name(user: &User) -> &Str {
    &user.name
}
```

```metel
extend Buffer {
    fun as_slice(&self) -> &Byte[] {
        &self.data
    }
}
```

What I find promising here is the narrower balance: explicit when the code genuinely needs to say something precise, absent from ordinary accessors and helper functions. This part of the design is still open, and I do not want to oversell it, but I think that direction is a good balance between "lifetimes everywhere" or "no lifetimes at all."

### Records

Another idea in that same neighborhood that I find especially intriguing is the `record` direction. The interesting part is not just "Metel might have structural types." Plenty of languages have structural typing in one form or another: [TypeScript](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) is built around structural compatibility, and [PureScript](https://book.purescript.org/chapter3.html) has records as a standard part of the language.

That approach is powerful, but it also means purely structural systems can blur distinctions that are nominally meaningful. If everything is compatible just because the shape lines up, it becomes easier to frankenstein together values that are structurally similar but conceptually should remain distinct. In TypeScript, for example, this is one reason developers often reach for [branded types](https://www.learningtypescript.com/articles/branded-types) or other [nominal-typing patterns](https://www.totaltypescript.com/workshops/advanced-typescript-patterns/branded-types/what-is-a-branded-type) when they want to preserve a stronger notion of identity than plain structural compatibility provides.

What feels potentially powerful to me in Metel is the coexistence of ordinary nominal types with a structural `record` form, plus the ability to convert a nominal value into a structural row and back again.

The reason this matters is partial consumption. Records are interesting to me not because they are a different spelling for structs, but because they offer a way to express "this field is gone now, these fields are still here" as a real static fact.

The following is a design sketch rather than current executable Metel:

```metel
struct RcBox<T> {
    strong: AtomicUsize,
    weak: AtomicUsize,
    value: T,
}

extend<T> RcBox<T>: Drop {
    fun drop(self: RcBox<T>) uses (value) {
        drop(self.value);
    }
}
```

```metel
fun drop_value<T>(cell: &var RcBox<T>) {
    let view = cell.to_record_mut();
    let value = move view.value; // explicit partial move out of the record view
    drop(value);
    // view is now `&var record { strong: AtomicUsize, weak: AtomicUsize }`
    // The payload is gone, but the counters are still present.
}
```

That is the kind of use case where records seem genuinely valuable to me. When the last strong reference goes away, the payload may need to be destroyed immediately, while the allocation itself has to stay alive until the weak count also reaches zero. In languages like Rust, this kind of "tear down one field now, keep the rest valid" logic is exactly where implementations like `Rc` and `Arc` end up relying on `unsafe` machinery such as `ManuallyDrop`. The record-based partial-consumption idea offers a way to model that kind of transition directly in the type system instead.

That is also why I think the nominal/structural coexistence matters so much. A type like `RcBox<T>` can still be designed and used as a normal nominal type, but when the checker needs a field-sensitive view of what remains after consumption, the structural record form gives it exactly the vocabulary it needs.

I like that because it does not force an all-or-nothing choice between nominal and structural typing. It suggests a language where named types remain the normal unit of design, but structural records become an explicit tool for taking values apart, reasoning about their fields, and putting them back together when that buys real expressive power.

### Brands

Brands are the least settled part of this picture, but they are still worth mentioning because they seem to fill an important gap. Allocators and lifetimes can already explain where something lives and how long a borrow remains valid. Brands are the candidate answer to a third question: which specific resource or cell are we talking about?

The idea has useful prior art. Rust's [`PhantomData`](https://doc.rust-lang.org/std/marker/struct.PhantomData.html) is one way to carry type-level information without runtime data. Haskell's [`ST`](https://hackage.haskell.org/package/base/docs/Control-Monad-ST.html) uses a state-thread parameter to keep mutable state from escaping. [GhostCell](https://plv.mpi-sws.org/rustbelt/ghostcell/) makes the connection even more explicit: branded types plus tokens can separate permission from data while preserving static safety.

GhostCell is especially relevant because it uses Rust lifetimes to imitate brands. A `GhostCell` and its matching token share the same lifetime parameter, and that lifetime is not really about how long a borrow lasts in the everyday Rust sense. It acts more like a fresh identity: cells with the same lifetime belong to the same branded family, and the token for that lifetime is the permission needed to mutate them. The lifetime parameter becomes a type-level "which cell family is this?" marker.

That is close to the role I am interested in for Metel brands, but with one important difference: in Rust, this identity has to be encoded through the lifetime system and library patterns. In Metel, the open question is whether brands should be surfaced directly as their own concept, alongside allocator identities and lifetime anchors, instead of being simulated through another mechanism.

The precise syntax is not decided, but conceptually I imagine these as different roles of the same underlying idea:

```metel
fun preserve_storage<@a>(value: @a Node) -> @a Node {
    value
}

fun borrow_from_value<&l>(x: &Str) -> &l Str {
    x
}

fun preserve_identity<'b>(cell: RcCell<'b, Node>) -> RcCell<'b, Node> {
    cell
}
```

In the first case, `a` is an allocator binding used as an allocator brand: the type says the returned value lives in the same allocator as the input. In the second, `x` is a real binding used as a lifetime brand: the returned borrow is valid only as long as `x` is. In the third, `'b` is an identity brand: it says which particular cell family the value belongs to.

Those are different roles, but they rhyme strongly. The language would not need to treat every brand as the same kind of runtime thing. An allocator brand can come from an allocator value. A lifetime brand can come from a real binding. A pure identity brand can be compile-time-only. The unifying idea is that all three give the type checker a concrete identity to preserve and compare.

What makes them interesting to me is that they do not feel like a completely separate idea. They look more like the identity-tracking counterpart to allocators and lifetimes. That is still very much design work rather than a finished feature, but if it holds up, it could be one of the pieces that makes the lower-level model cohere instead of turning into a pile of unrelated mechanisms.

## Why this is still an experiment

A lot of languages sound interesting at the design-document level. That is the easy part.

The hard part is whether the ideas still hold together when they collide with each other: generics, borrowing, closures, partial moves, collections, module boundaries, diagnostics, and eventually performance constraints. Metel is at exactly that stage now. The project has enough implementation to support serious experimentation, but not enough to claim that the long-term design has already proved itself.

So I do not want to oversell it.

Metel is exploratory by design. Some RFCs have been accepted and implemented quickly. Others have been reopened after integration exposed problems that were not obvious at first. That is not a sign that the project is failing; it is a sign that it is still alive enough to correct itself.

If anything, I would rather have that than a fake sense of certainty.

## Why build it anyway

Because I think there is still room for languages that are not trying to be immediately practical products.

Metel gives me a place to test a combination of ideas that I do not see assembled quite this way elsewhere: allocator-aware programming, binding-named lifetime reasoning, resource-sensitive types, and eventually more fine-grained ownership over structured data rather than only whole-value ownership.

Even if the final result turns out to be narrower than the current design suggests, the project is already valuable to me for a simpler reason: it has forced me to move from "I like language design" to "can I make these decisions cohere across syntax, semantics, implementation, and documentation?"

That is a much better standard.

## Where it goes next

The immediate job is not to add ten more ambitious ideas.

The immediate job is to keep building out the parts that already define the language's shape: ownership, borrow checking, allocator-aware storage, and the lower-level substrate those features depend on. The project has done a lot of design work recently. Now it needs more of that design to become real.

If Metel ends up being worth anyone else's time, it will not be because it looked clever in RFCs. It will be because the language eventually demonstrates that these ideas can form a coherent, teachable, implementable whole.

That is the standard I want to hold it to.
