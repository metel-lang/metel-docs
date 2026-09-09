---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors: [vladislav]
tags: [language-design, metel, roadmap]
---

# Introducing Metel

Metel is a research language exploring new paths to compile-time safety. It brings
together ideas from across modern language design — ownership, capabilities,
effects, explicit allocation, and structural types — to ask how they can work
together in a system that is both explicit and practical to use.

Here is a small taste of the language:

```metel
fun main() {
    let name = "Metel";
    let answer: Perhaps<i64> = Some { value = 42 };
    println("${name} says the answer is ${answer.yolo()}");
}
```

`.yolo()` is not a typo — more on that name below.

<!--truncate-->

At first, the goal was small and personal: a statically typed, Rust-influenced interpreted language with a garbage collector, built as a way to learn by making.

As the basics took shape, the project opened into a larger set of questions about
memory safety, ownership, regions, linear capabilities, structural typing, and
identity. Federico Bruzzone's [tour of substructural, uniqueness, ownership, and
capability types](https://federicobruzzone.github.io/posts/eter/a-friendly-tour-of-substructural-uniqueness-ownership-and-capabilities-types-and-more.html)
was one of the pieces that pushed me further in that direction.

None of these ideas begins with Metel. Region calculi, explicit allocators,
branded identity, and structural typing have all proved useful somewhere already.
The question is whether they can form a coherent whole rather than remain useful
tools in separate languages.

That is not a finished question. Rust itself continues to explore [view
types](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/) and a
[place-based lifetime syntax](https://smallcultfollowing.com/babysteps/blog/2024/06/02/the-borrow-checker-within/)
aimed at making borrowing easier to teach. Even well-established languages are
not set in stone: language design is still an active problem.

Metel is my attempt to explore that space: not to replace another language, but to
find out what these tools look like when they are designed to meet each other.

## The Shape Of The Project

Metel is a personal project, guided by curiosity rather than a company roadmap. It is an exploration, not a bid to replace Rust, Zig, or C++. Its direction comes from a few design commitments:

- Allocation should be explicit when it matters;
- Resource usage should be visible in the type system;
- Ordinary code should still read like ordinary modern code;
- Lifetimes should be easy to understand and to reason about — for now that means treating bindings themselves as lifetime anchors;
- Ownership should eventually work over structured values, not only whole values.

Allocators were the first piece I built, but they turned out to be just the first use case of a broader substrate — structural shape, field-sensitive ownership, brand-like identity, lifetimes named after real bindings. That's too much for one post, so this is the first in a series: an overview here, then a dedicated post on **records** — the piece I currently find most worth pursuing — once that design is further along.

Metel is heavily AI-assisted, particularly in the interpreter implementation. Design decisions are curated and reviewed against the RFCs, specification, and working implementation.

## Why Metel?

The project has had a few names — including Yoloscript, which is why `.yolo()`
survived — but **Metel** is the one that stuck: Russian for “blizzard,” and the
title of a poem by Sergei Yesenin, one of my late father's favorite poets:

The name reflects my own personal cultural baggage, not political support or
affiliation.

> Прядите, дни, свою былую пряжу...
>
> *(Spin on, you days, your age-old thread...)*
>
> — Sergei Yesenin, "Метель" (1924)

It kept the wind and carried more weight than a pun.

## What Already Exists

Metel already has an interpreter, modules, generics, aspects, exhaustive pattern
matching, a standard library, and a growing specification and RFC process. Recent
releases have also brought coherence rules, associated types, structural bounds,
and the `public`/`var`/`extend` surface syntax into the implementation.

The deepest ownership and allocation model is still ahead of the runtime. **The
interpreter is a feedback mechanism, not a finished semantic engine**: it lets
syntax, modules, generics, and library code pressure-test a design before it is
written in stone.

## Records And Field-Sensitive Ownership

The next post will make the case in full. The short version is that Metel should
keep ordinary nominal types, while offering an explicit structural record view
when the checker needs to reason about individual fields. That bridge may make
partial consumption practical: one field can be moved or destroyed while the
rest of a value remains available.

This is a design sketch, not executable Metel, and an acknowledged-hard problem
rather than a demonstrated improvement over Rust. The interesting question is
whether an explicit nominal-to-structural bridge can make that capability both
safe and legible.

## Other Directions I'm Weighing

Other active directions include brands for allocator, lifetime, and capability
identity; comptime based on ordinary Metel evaluation; linear types; and algebraic
effects. Each has substantial prior art, but each still has to earn a coherent
place in Metel's memory model.

## Why Build It?

A language design only becomes interesting when its ideas meet generics, borrowing,
closures, partial moves, diagnostics, and performance constraints. Metel is where
those ideas can be tested together. Some will change under that pressure; that is
the point of building it.

## What Now?

Next comes the records post, followed by the first ownership and move-checking
work. Brands, borrowing, allocator lifetimes, and eventually a compiler follow as
the design earns the machinery they require. Feedback, critique, and
counterexamples are welcome along the way.
