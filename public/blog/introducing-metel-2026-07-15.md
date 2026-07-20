---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors: [vladislav]
tags: [language-design, metel, roadmap]
---

# Introducing Metel

You surely know as well as I do that the world does not need another amateur C++/Rust/Zig/Go/Odin clone, so the honest introduction is this: I started building Metel because I wanted to build a programming language.

Here's a taste of what that turned into:

```metel
fun main() {
    let name = "Metel";
    let answer: Perhaps<i64> = Perhaps::Some { value: 42 };
    println("${name} says the answer is ${answer.yolo()}");
}
```

`.yolo()` is not a typo — more on that name below.

At first, the goal was small and personal: a statically typed, Rust-influenced interpreted language with a garbage collector, **built to learn rather than to ship**.

That version did not stay small for long. Once the basics existed, I started reading more seriously about memory safety, type systems, ownership, regions, linear capabilities, structural typing, and brand-like identity systems — Federico Bruzzone's [A friendly tour of substructural, uniqueness, ownership and capabilities types (and more)](https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html) was one of the pieces that pushed me deeper in that direction.

What struck me reading that material was how vast it was, and how much of it is already proven out somewhere — region calculus, explicit allocators, branded identity, structural typing, each already shipped in some corner of some language (more on each below). Almost none of the individual ideas is unclaimed.

What is still genuinely open is how much room is left in combining them. Each already solves its own problem well, in its own language; what's still unexplored is whether several of these already-researched concepts can hold together at once, in a single language, rather than each staying in a different one.

There's also a more immediate motivation: mainstream languages are still actively floating new proposals for these exact problems — Rust's own Niko Matsakis has one for [view types](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/) and, separately, one for a [place-based lifetime syntax](https://smallcultfollowing.com/babysteps/blog/2024/06/02/the-borrow-checker-within/) aimed at teachability. Watching that, I realized I could try my hand at the same problems myself, in a language of my own.

The project slowly stopped being "my small Rust-like interpreter" and became a different question — not "how do I clone Rust" and not "what entirely new idea can I invent," but something in between: what does a language look like that takes several of these already-proven ideas seriously and actually puts them together? That question is what Metel is now.

{/* truncate */}

## The Shape Of The Project

Metel is a personal project. **There is no team, no company, and no roadmap** driven by anything other than my own curiosity — I work on it because I want to know whether these ideas actually fit together, not because it needs to ship or win adoption. It is not trying to beat Rust, Zig, or C++ at their own game, and it is not production-ready. It is built around a few bets I take seriously:

- Allocation should be explicit when it matters;
- Resource usage should be visible in the type system;
- Ordinary code should still read like ordinary modern code;
- Lifetimes should be easy to understand and to reason about — for now that means treating bindings themselves as lifetime anchors;
- Ownership should eventually work over structured values, not only whole values.

Allocators were the first piece I built, but they turned out to be just the first use case of a broader substrate — structural shape, field-sensitive ownership, brand-like identity, lifetimes named after real bindings. That's too much for one post, so this is the first in a series: an overview here, then a dedicated post on **records** — the piece I currently find most worth pursuing — once that design is further along.

One thing I want to be explicit about upfront: **Metel is heavily AI-assisted**. The implementation of the interpreter especially has been built with a lot of help from AI tools.
The design work however, while also AI-assisted, is very carefully curated and reviewed in detail. Whether that puts the result closer to careful engineering or vibe-coded slop, I'll let you be the judge – but I'd like to think closer to the middle than to the latter.

## Why Metel?

The name has had two prior lives, and neither one explains itself, so it's worth telling.

The project started as **Yoloscript**, with one deliberately silly objective: a language where `.yolo()` was the equivalent of `unwrap()`. That objective actually survived every rewrite since — **`.yolo()` is still there today**, the way you unwrap a `Result` or a `Perhaps`.

The next iteration tried to be a mix of Rust and Go, and I named it **Gust** — which felt clever for about a week, until I realized I was nowhere near the first person to think "a Rust/Go hybrid should be called Gust." A fair number of other projects had already landed on the same name. That was a small crisis: I'd already grown attached to the wind theme Gust had put in my head, and I wasn't ready to let it go.

After a bit of wandering, I landed on **Metel** — Russian for "blizzard," and the title of a poem by Sergei Yesenin, one of my late father's favorite poets:

> Прядите, дни, свою былую пряжу...
>
> *(Spin on, you days, your age-old thread...)*
>
> — Sergei Yesenin, "Метель" (1924)

It kept the wind, carried more weight than a pun, and it's the one that stuck.

## What Already Exists

Metel is already in a pretty good shape. There is a real interpreter, a module system, generics, aspects, exhaustive pattern matching, a standard library with `Perhaps`, `Result`, `List`, strings, host-backed `fs`/`env`/`process` modules, and a growing specification and RFC process. Recent work has also moved a large batch of type-system and surface-language ideas into the implementation: negative bounds and impls, associated types, bottom type `!`, structural aspect bounds, coherence checks, `return`/`break`/`continue` as expressions, and the newer `public`/`var`/`extend` surface syntax. For example, this is ordinary Metel today:

```metel
aspect Greet {
    fun greet(&self) -> String;
}

struct Person { name: String }

extend Person: Greet {
    fun greet(&self) -> String { "Hello, ${self.name}!" }
    fun rename(&var self, new_name: String) { self.name = new_name; }
}

fun greet_all<T: Greet>(people: T[]) {
    for (p in people) { println(p.greet()); }
}

fun main() -> i64 {
    var ada = Person { name: "Ada" };
    let ada_ref: &var Person = &var ada;
    ada_ref.rename("Ada Lovelace");   // auto-deref through &var — writes back to ada

    greet_all([ada, Person { name: "Grace" }]);
    return 0;
}
```

The deepest ownership and allocation model is still ahead of the runtime. **The interpreter is a feedback mechanism, not a finished semantic engine**, but it is enough machinery for syntax, modules, generics, aspects, and standard-library code to push back on design ideas before they are written down in stone.

That means that all of the ideas described in this article are subject to change. Any feedback on them is welcome and may very well make me change my mind on some things.

## The Foundation: Allocators And Lifetimes

Two questions that many systems languages tie tightly together, Metel keeps apart: where does a value live, and for how long is a reference to it valid? Allocators answer the first, lifetime anchors answer the second. Both are background for the main event, so I will keep them short.

**Allocators** make storage an explicit program-level choice. [Zig](https://ziglang.org/documentation/master/#Choosing-an-Allocator) and [Odin](https://odin-lang.org/docs/overview/#allocators) already make allocator-passing normal, and Rust has an experimental [`Allocator` API](https://doc.rust-lang.org/std/alloc/trait.Allocator.html). Metel's bet is that allocator identity should be visible in the language's own type and syntax rules, not only in library APIs, because allocator choice is often part of an invariant a value's type should preserve:

```metel
let user = @Heap User { name: "Ada" };

fun identity(value: @Node) -> @Node { value }
```

**Lifetimes** in Metel anchor to a binding that already exists in the program, rather than a fresh abstract variable (`'a`). The idea descends from Tofte and Talpin's [region calculus](https://dl.acm.org/doi/10.1145/174675.177855) and [Cyclone](https://cyclone.thelanguage.org/wiki/Introduction%20to%20Regions/)'s named regions, the direct ancestor of [Rust](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)'s lifetimes; what Metel varies is only the spelling:

```metel
fun first(x: &Str, y: &Str) -> &x Str {
    x
}
```

Both code samples above are design sketches, not executable Metel — the allocator and
lifetime-anchor cluster is accepted design, not yet built. The name in the return type
refers to a real binding in the function. The common case should still avoid
annotation — **treat this as an ergonomic variant on old machinery, not a new
capability**.

## Records And Field-Sensitive Ownership

This is the first post in a series, and records are the idea I want to introduce here rather than fully argue for — they get a dedicated, more in-depth post of their own, because they are the part of Metel I find most worth pursuing.
They may let **nominal and structural typing coexist** without choosing one as the whole language, and they are the closest Metel gets to a genuinely open problem rather than re-treading solved ground. What follows is the shape of the idea, not the full case for it.

Purely structural systems are powerful — [TypeScript](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) is built around structural compatibility, and [PureScript](https://book.purescript.org/chapter3.html) has records as a standard feature — but structural compatibility can also **blur distinctions that matter**. That is one reason TypeScript developers reach for [branded types](https://www.learningtypescript.com/articles/branded-types) and other [nominal-typing patterns](https://www.totaltypescript.com/workshops/advanced-typescript-patterns/branded-types/what-is-a-branded-type).

What I want to explore in Metel is narrower: **ordinary nominal types, plus an explicit structural `record` view** when the checker needs to reason about fields. The bridge would be opt-in — a nominal type can derive `ToRecord` to expose its fields as a structural row, and `FromRecord` to allow reconstruction from the full row again:

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

Those two aspects are deliberately separate: types with constructor-checked invariants may want `ToRecord` without derived `FromRecord`.

The real use case is **partial consumption** — a program needs to say: this field is gone, these fields are still here.

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

This is a design sketch, not executable Metel. The motivating case is `Rc`/`Arc`-style teardown: the payload may need to be destroyed when the last strong reference disappears, while the allocation and counters remain alive until weak references are gone too — exactly the kind of logic visible in the standard library's actual [`RcInner`/`Rc::drop_slow`](https://doc.rust-lang.org/src/alloc/rc.rs.html#284-288) and [`ArcInner`/`Arc::drop_slow`](https://doc.rust-lang.org/src/alloc/sync.rs.html#387-391) layouts. **The nominal type remains the normal interface, and the structural view appears only when the program deliberately takes a value apart.**

This is where Metel is closest to an open problem. The same need — letting a function say "I only touch these fields" so that a partial move or a disjoint borrow can type-check — is exactly what Rust compiler team member Niko Matsakis's ["view types" idea](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/) is reaching for. It is a personal exploration on his blog, not an accepted RFC or a language feature Rust has committed to, but it names the same open problem Rust's affine-only field-sensitivity keeps running into. Metel's bet is to reach it through an explicit nominal-to-structural bridge rather than by annotating references — **a different approach to an acknowledged-hard problem, not a demonstrated improvement over it**.

## Other Directions I'm Weighing

**Brands** are already decided as a piece of Metel — a single mechanism for tracking allocator, lifetime, and capability identity, in the spirit of [GhostCell](https://plv.mpi-sws.org/rustbelt/ghostcell/) and Scala's [capture checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html) — **it is the details that are still unsettled, not whether they belong**.

**Comptime** is further along than either, on paper: two draft RFCs already specify it in Zig's image — compile-time execution of ordinary Metel code, staged by the same evaluator, rather than a separate macro language with its own grammar and hygiene rules. The interesting bet in those drafts is that generalizing a single primitive — `emit`, which lets comptime code register a declaration or splice an expression back at its own call site — plus exposing Metel's own parser as an ordinary comptime-callable function, **closes most of what a macro system is normally needed for**: derive, repetitive declaration generation, compile-time-validated embedded DSLs, even Rust's `matches!`-style pattern macros. No token-stream grammar, no macro-invocation syntax, no hygiene system to design. It is still draft and deferred to after the core language settles.

Less settled than either are [linear types](https://arxiv.org/abs/1710.09756) (use *exactly* once, stricter than Rust's affine ownership, as shipped in [Austral](https://borretti.me/article/introducing-austral)) and [algebraic effects and handlers](https://arxiv.org/abs/1312.1399) in the style of [Koka](https://koka-lang.github.io/koka/doc/index.html) — but "less settled" means different things for each. Linear types already have a draft RFC and real design work behind them; effects don't have an RFC at all yet. Both have strong prior art elsewhere, and I think both are worth having — **the honest open question isn't whether they belong, it's whether either fits Metel's own memory model cleanly enough to commit to**, rather than sitting beside it as a bolted-on feature. I will write these up separately as they firm up.

## Why Build It?

A lot of languages sound interesting in design documents. **The hard part is whether the ideas still hold together** when they collide with generics, borrowing, closures, partial moves, collections, modules, diagnostics, and performance constraints. Metel is at that stage now. Some ideas have worked; some have been reopened after implementation exposed problems. That is healthy.

What Metel actually claims is **smaller than "new research"**: almost none of the individual ingredients is novel, and several are already formalized and proven sound. If Metel is worth anything, it will be because the *combination*, and the ergonomics of that combination, turn out to be coherent, teachable, and implementable. The single place Metel might push past the state of the art is field-sensitive ownership over structured data — and even there the status is "an open problem others are also stuck on," not "solved."

## What Now?

One deliberate inversion worth flagging: allocators are the language's public face, but they're the *last* major piece I plan to build. The more I work on the design, the more it looks like a combination of simpler things — an `@a T` is roughly an owned box carrying a brand, and checking it doesn't outlive its allocator is just the borrow checker's job — rather than a primitive of its own. So allocators wait until brands, records, and borrow-checking exist, and the finished design becomes an acceptance test: can I rebuild `Heap` and `BumpAlloc` from those pieces, or is there a genuinely allocator-specific remainder?

So: **short term**, the records post and `ToRecord`/`FromRecord` working in the interpreter. **Medium term**, the borrow checker, linear types, and brands as real primitives. **Then allocators**, on top of all of it. **Long term:** a real compiler and soundness arguments for the parts that matter most — an interpreter can pressure-test syntax, but it can't carry that weight.

I'd also like to **open parts of the process to outside contributions**. Not design-by-committee — I want the room to be wrong in my own direction for a while first — but real feedback, critique, counterexamples, and eventually carefully-scoped contributions, once there's enough structure for that to land somewhere useful.

## References

- Federico Bruzzone, [A friendly tour of substructural, uniqueness, ownership and capabilities types (and more)](https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html)
- The Rust Programming Language, [Validating References with Lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)
- Mads Tofte, Jean-Pierre Talpin, [Implementation of the Typed Call-by-Value λ-calculus using a Stack of Regions](https://dl.acm.org/doi/10.1145/174675.177855) (POPL 1994)
- Dan Grossman, Greg Morrisett, Trevor Jim, Michael Hicks, Yanling Wang, [Region-Based Memory Management in Cyclone](https://dl.acm.org/doi/10.1145/543552.512563) (PLDI 2002); see also the [Cyclone regions manual](https://cyclone.thelanguage.org/wiki/Introduction%20to%20Regions/)
- Rust standard library source, [`RcInner` and `Rc::drop_slow`](https://doc.rust-lang.org/src/alloc/rc.rs.html)
- Rust standard library source, [`ArcInner` and `Arc::drop_slow`](https://doc.rust-lang.org/src/alloc/sync.rs.html)
- Niko Matsakis, [View types for Rust](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
- TypeScript Handbook, [Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
- PureScript Book, [Records and Row Polymorphism](https://book.purescript.org/chapter3.html)
