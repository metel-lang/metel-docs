---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors: [vladislav]
tags: [language-design, metel, roadmap]
---

# Introducing Metel

The world does not need another amateur C++/Rust/Zig/Go/Odin clone, so the honest introduction is this: I started building Metel because I wanted to build a programming language.

At first, the goal was small and personal: a statically typed, Rust-influenced interpreted language with a garbage collector. I wanted to learn, and I wanted to build something that felt like a real language rather than a parser demo.

That version did not stay small for long. Once the basics existed, I started reading more seriously about memory safety, type systems, ownership, regions, linear capabilities, structural typing, and brand-like identity systems. Federico Bruzzone's [A friendly tour of substructural, uniqueness, ownership and capabilities types (and more)](https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html) was one of the pieces that pushed me deeper in that direction. The project slowly stopped being "my small Rust-like interpreter" and became a more interesting question:

What if I tried to combine several well-researched ideas into a language with its own point of view?

That question is what Metel is now.

{/* truncate */}

## The Shape Of The Project

Metel is an exploratory systems language. It is not trying to beat Rust, Zig, or C++ at their own game, and it is not production-ready. It is an attempt to design a language around a few bets that I find worth taking seriously:

- allocation should be explicit when it matters;
- resource usage should be visible in the type system;
- ordinary code should still read like ordinary modern code;
- lifetime errors should name real program bindings, not abstract `'a` variables;
- ownership should eventually work over structured values, not only whole values.

Earlier, I thought of Metel mainly as "the allocator-aware language." That is still part of its identity, but the better description is broader. The current design treats allocators as the first major use case of a lower-level substrate: structural shape, field-sensitive ownership, brand-like identity, and lifetimes named after actual bindings.

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

The deepest ownership and allocation model is still ahead of the runtime. The interpreter is a feedback mechanism, not a finished semantic engine, but it is enough machinery for syntax, modules, generics, aspects, and standard-library code to push back on design ideas before they become too abstract.

Metel is also heavily AI-assisted. AI has been useful as a collaborator, critic, and accelerator, but the ideas, priorities, trade-offs, and final decisions are personal and carefully curated.

## The Ideas I Care About

The part of Metel I currently find most worth pursuing is the separation between two questions that many systems languages tie tightly together:

1. Where does a value live?
2. For how long is a reference to it valid?

In Metel's design, allocators answer the first question. Lifetime anchors answer the second. Brands may eventually answer a third: which specific resource, region, or cell family are we talking about?

Before going through these, one honest disclaimer that applies to all of them. Each idea below has deep, well-studied prior art — in several cases formalized and proven sound by people far better at type theory than I am — and I will point at that work as I go. Metel's bet is not any single one of these mechanisms. It is whether these particular pieces fit together into one coherent language. Read the sections with that framing.

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

The goal is memory-safe allocator-aware programming where storage is explicit enough for the checker to reason about, but not so noisy that ordinary heap allocation becomes ceremony.

### Lifetimes

Lifetimes are not a new idea, and Metel is not inventing the mechanism. Region-based memory management goes back to Tofte and Talpin's [region calculus](https://dl.acm.org/doi/10.1145/174675.177855), and [Cyclone](https://cyclone.thelanguage.org/wiki/Introduction%20to%20Regions/), a safe C dialect, already had named, lexically-scoped regions threaded through pointer types two decades ago. [Rust](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)'s lifetimes descend directly from that line, and [Move](https://github.com/move-language/move) has its own static reference-safety model. So this is old, well-explored ground. The only thing Metel varies is spelling: instead of a fresh abstract lifetime variable (`'a`) or a separate region declaration, a borrow anchors to a binding that already exists in the program.

```metel
fun first(x: &Str, y: &Str) -> &x Str {
    x
}
```

The name in the return type refers to a real binding already present in the function. The signature says directly that the result is tied to `x`.

The common case should still avoid annotation. A method like `as_slice(&self) -> &Byte[]` should not need to invent a lifetime name just to say "the result comes from `self`." The explicit form is for real ambiguity. This is design syntax, not implemented surface syntax today, and the exact spelling may still change, but the direction is the point: lifetime anchors should be names from the program, not invented variables that only exist in the type signature.

To be clear about the size of that claim: I have not found this exact "anchor to an existing value binding" spelling in prior work, but the underlying machinery is Cyclone's, and Rust's lifetime elision already removes annotations in these same common cases. This is an ergonomic bet, not a new capability — and it may turn out to be a rediscovery.

### Records

Records are interesting to me because they may let nominal and structural typing coexist without choosing one as the whole language.

Purely structural systems are powerful. [TypeScript](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) is built around structural compatibility, and [PureScript](https://book.purescript.org/chapter3.html) has records as a standard feature. But structural compatibility can also blur distinctions that matter. If everything matches because the shape lines up, it becomes easier to frankenstein together values that should remain conceptually distinct. That is one reason TypeScript developers reach for [branded types](https://www.learningtypescript.com/articles/branded-types) and other [nominal-typing patterns](https://www.totaltypescript.com/workshops/advanced-typescript-patterns/branded-types/what-is-a-branded-type).

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

This is a design sketch, not executable Metel. `to_record_mut()` would come from `ToRecord`; `from_record_mut()` would only be available again once the row has been restored to the full `RcBox<T>` shape. The motivating case is `Rc`/`Arc`-style teardown: the payload may need to be destroyed when the last strong reference disappears, while the allocation and counters remain alive until weak references are gone too. In Rust, this is exactly the kind of internal logic you can see in the standard library's actual [`RcInner`](https://doc.rust-lang.org/src/alloc/rc.rs.html#284-288) and [`ArcInner`](https://doc.rust-lang.org/src/alloc/sync.rs.html#387-391) layouts, along with the corresponding [`Rc::drop_slow`](https://doc.rust-lang.org/src/alloc/rc.rs.html#393-399) and [`Arc::drop_slow`](https://doc.rust-lang.org/src/alloc/sync.rs.html#2131-2135) teardown paths. That is the part I find more interesting than "structural typing" on its own: the nominal type remains the normal interface, and the structural view appears only when the program deliberately takes a value apart and the checker needs vocabulary for what remains.

This is also the one area where I think Metel is closest to a genuinely open problem rather than re-treading solved ground. The same need — letting a function say "I only touch these fields" so that a partial move or a disjoint borrow can type-check — is exactly what Rust's proposed [view types](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/) are reaching for, and it is unsolved there too. Metel's bet is to reach it through an explicit nominal-to-structural bridge (a value becomes a row only when you ask for it) rather than by annotating references. But I want to be honest that this is a *different approach to an acknowledged-hard problem*, not a demonstrated improvement over it. It may not pan out.

### Linear Types

Another idea I take seriously is [linear types](https://arxiv.org/abs/1710.09756), which are stricter than the affine ownership model that languages like [Rust](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) already use.

The difference is simple. An affine value may be used at most once: you can move it, or you can drop it without using it again. A linear value must be used exactly once: it cannot be silently discarded, because consuming it is part of the invariant. Rust is mostly affine in this sense. An ordinary non-`Copy` value can always just go out of scope:

```rust
fn main() {
    let file = std::fs::File::open("log.txt").unwrap();
    // `file` is never used again, but this is fine: it is simply dropped.
}
```

That is often the right default. Most resources do not need a proof that they were consumed in some specific way; they only need to avoid accidental duplication. But some things are stronger than that. Protocol enforcement is the clearest example: if opening a session gives you a value representing "handshake in progress," and the only legal next steps are "authenticate," "reject," or "close," then silently dropping that value means the protocol was abandoned halfway through. The same shape appears with must-join concurrency handles, transactional capabilities that must commit or roll back, and resources that must be explicitly returned to some owner.

That is why affine ownership does not make linear types redundant. Affinity is a good default for ordinary resources. Linearity is useful for the smaller set of values where dropping them is itself a bug, because the program has failed to discharge some obligation the type system was supposed to track.

None of this is new theory, and I do not want to imply otherwise. Combining "use at most once" and "use exactly once" in one system is precisely what graded and quantitative type systems already do: [Quantitative Type Theory](https://idris2.readthedocs.io/en/latest/tutorial/multiplicities.html), as realized in Idris 2 with its `0`/`1`/`many` multiplicities, and [Granule](https://granule-project.github.io/) treat linear, affine, and unrestricted use uniformly — and Granule's group has gone further and unified linearity, uniqueness, and ownership in a single type system. [Austral](https://borretti.me/article/introducing-austral) already ships a strict linear-versus-unrestricted split in a real systems language today. Metel's job here is not to invent the combination but to fit it to the rest of the memory model without making everyday code pay for it.

### Algebraic Effects

Another design area I am evaluating, as an option for now rather than a committed direction, is [algebraic effects and handlers](https://arxiv.org/abs/1312.1399). Languages like [Koka](https://koka-lang.github.io/koka/doc/index.html) make that tradition concrete.

What makes that interesting in Metel is not the surface syntax by itself, but the interaction with ownership, borrows, allocator-tagged values, handler state, and sendability across fibers. If Metel ever goes in that direction, the effect system would need to fit the memory model cleanly rather than sit beside it as an unrelated feature.

I should be honest that this interaction is not unexplored either. [Effekt](https://effekt-lang.org/), through its [System C](https://se.cs.uni-tuebingen.de/publications/brachthaeuser22effects/) calculus, already reconciles effect handlers with a second-class-value and capability discipline, and proves it sound. So if Metel goes here, it would be joining an active line of work, not opening one — and the honest question is only whether the specific memory model it has to fit against is different enough to be worth the effort.

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

Two honest caveats. The brand idea itself is settled prior art: [GhostCell](https://plv.mpi-sws.org/rustbelt/ghostcell/) formalized branded types in Rust and proved them sound in Coq, building on a trick that goes back to Haskell's `ST` monad. And the broader move — tracking resource, lifetime, and capability identity through a single mechanism — is an active research program in its own right, closest to Scala's [capture checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html). Metel's specific unification, treating allocators, anchors, and brands as one named channel, is a design bet placed inside that space, not a discovery of it.

## Why Build It?

A lot of languages sound interesting in design documents. The hard part is whether the ideas still hold together when they collide with generics, borrowing, closures, partial moves, collections, modules, diagnostics, and performance constraints. Metel is at that stage now. Some ideas have worked. Some have been reopened after implementation exposed problems. That is healthy. I would rather have a project that corrects itself than one that preserves a fake sense of certainty.

I am building Metel because it gives me a place to test a combination I do not see assembled quite this way elsewhere: allocator-aware programming, binding-named lifetime reasoning, resource-sensitive types, and eventually field-sensitive ownership over structured data.

I want to be plain about the size of that claim. Almost none of the individual ingredients is novel, and several have been formalized and proven sound already — regions in Cyclone and the Tofte–Talpin calculus, linearity and affinity in the graded-types literature, brands in GhostCell, effects-with-capabilities in System C. If Metel is worth anything, it will not be because it invented one of these mechanisms. It will be because the *combination*, and the ergonomics of that combination, turn out to be coherent, teachable, and implementable. That is a smaller and more honest claim than "new research," and it is the one I actually intend to defend. The single place I think Metel might push past the state of the art rather than reassemble it is field-sensitive ownership over structured data — and even there, the honest status is "an open problem others are also stuck on," not "solved."

The immediate job is not to add ten more ambitious ideas. It is to keep turning the parts that already define the language's shape into working machinery.

If Metel ends up being worth anyone else's time, it will not be because it looked clever in RFCs. It will be because the language demonstrates that these ideas can form a coherent, teachable, implementable whole.

## What Now?

The long-term goal is to finish the language design far enough that the remaining open questions are narrow, explicit, and attached to real trade-offs. That means turning exploratory reports into accepted RFCs, rejecting ideas that do not justify their cost, and getting the ownership, allocation, lifetime, record, brand, and effect stories into a shape that can actually be taught and implemented.

It also means opening parts of that process to outside contribution carefully. I do not want Metel to become a design-by-committee project, but I do want serious feedback, counterexamples, and eventually carefully-scoped contributions.

Past that, the project needs to become more than an interpreter. It needs a real compiler, a research-quality paper or technical report, and eventually rigorous soundness arguments for the interesting parts of the design.

## References

- Federico Bruzzone, [A friendly tour of substructural, uniqueness, ownership and capabilities types (and more)](https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html)
- The Rust Programming Language, [Understanding Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
- The Rust Programming Language, [Validating References with Lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)
- Mads Tofte, Jean-Pierre Talpin, [Implementation of the Typed Call-by-Value λ-calculus using a Stack of Regions](https://dl.acm.org/doi/10.1145/174675.177855) (POPL 1994)
- Dan Grossman, Greg Morrisett, Trevor Jim, Michael Hicks, Yanling Wang, [Region-Based Memory Management in Cyclone](https://dl.acm.org/doi/10.1145/543552.512563) (PLDI 2002); see also the [Cyclone regions manual](https://cyclone.thelanguage.org/wiki/Introduction%20to%20Regions/)
- The Move Programming Language, [move-language/move](https://github.com/move-language/move)
- Rust standard library source, [`RcInner` and `Rc::drop_slow`](https://doc.rust-lang.org/src/alloc/rc.rs.html)
- Rust standard library source, [`ArcInner` and `Arc::drop_slow`](https://doc.rust-lang.org/src/alloc/sync.rs.html)
- Niko Matsakis, [View types for Rust](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
- TypeScript Handbook, [Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
- PureScript Book, [Records and Row Polymorphism](https://book.purescript.org/chapter3.html)
- Jean-Philippe Bernardy, Mathieu Boespflug, Ryan R. Newton, Simon Peyton Jones, Arnaud Spiwack, [Linear Haskell: practical linearity in a higher-order polymorphic language](https://arxiv.org/abs/1710.09756)
- Idris 2 documentation, [Multiplicities (Quantitative Type Theory)](https://idris2.readthedocs.io/en/latest/tutorial/multiplicities.html)
- Danielle Marshall, Michael Vollmer, Dominic Orchard, [Linearity and Uniqueness: An Entente Cordiale](https://granule-project.github.io/) (ESOP 2022; Granule project)
- Fernando Borretti, [Introducing Austral: A Systems Language with Linear Types and Capabilities](https://borretti.me/article/introducing-austral)
- Gordon D. Plotkin, Matija Pretnar, [Handling Algebraic Effects](https://arxiv.org/abs/1312.1399)
- Koka documentation, [The Koka Programming Language](https://koka-lang.github.io/koka/doc/index.html)
- Jonathan Immanuel Brachthäuser, Philipp Schuster, Klaus Ostermann, [Effects, Capabilities, and Boxes (System C)](https://se.cs.uni-tuebingen.de/publications/brachthaeuser22effects/) (OOPSLA 2022)
- Rust standard library, [`PhantomData`](https://doc.rust-lang.org/std/marker/struct.PhantomData.html)
- Haskell base library, [`Control.Monad.ST`](https://hackage.haskell.org/package/base/docs/Control-Monad-ST.html)
- Joshua Yanovski, Hoang-Hai Dang, Ralf Jung, Derek Dreyer, [GhostCell: Separating Permissions from Data in Rust](https://plv.mpi-sws.org/rustbelt/ghostcell/) (ICFP 2021)
- Scala 3 Reference, [Capture Checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html)
