---
slug: introducing-metel
title: "Introducing Metel"
date: 2026-07-15
authors: [vladislav]
tags: [language-design, metel, roadmap]
---

# Introducing Metel

Metel is an experimental language built around four commitments, roughly in order: compile-time
safety, explicitness, expressivity, and — eventually — performance. It brings together ideas
from across modern language design — ownership, capabilities, effects, structural types, and
explicit allocation — to ask how they can be combined into a single coherent system.

Here is a small taste of the language:

```metel
fun main() {
    let name := "Metel";
    let answer: Perhaps<i64> := Some { value = 42 };
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

Metel is a personal project, guided by curiosity rather than a company roadmap. It is an exploration, not a bid to replace Rust, Zig, or C++. Safety, explicitness, and expressivity come first and performance comes later — not because it doesn't matter, but because an interpreter is the wrong place to chase it, and a sound design is the wrong thing to rush. Its direction comes from a few concrete design commitments:

- Resource usage should be visible in the type system;
- Ordinary code should still read like ordinary modern code;
- Lifetimes should be easy to understand and to reason about — for now that means treating bindings themselves as lifetime anchors;
- Ownership should eventually work over structured values, not only whole values;
- Allocation should be explicit when it matters.

Allocators were the first piece I built, but they turned out to be just the first use case of a broader substrate — structural shape, field-sensitive ownership, brand-like identity, lifetimes named after real bindings. That's too much for one post, so this is the first in a series: an overview here, then a [dedicated post on records](/blog/records) — the piece I currently find most worth pursuing.

Metel is heavily AI-assisted, particularly in the interpreter implementation. Design decisions are curated and reviewed against the RFCs, specification, and working implementation.

## Why Metel?

The project has had a few names — including Yoloscript, which is why `.yolo()`
survived — but **Metel** is the one that stuck: Russian for “blizzard,” and the
title of a poem by Sergei Yesenin, one of my late father's favorite poets:

> Прядите, дни, свою былую пряжу...
>
> *(Spin on, you days, your age-old thread...)*
>
> — Sergei Yesenin, "Метель" (1924)

It kept the wind and carried more weight than a pun. The name reflects my own
personal cultural baggage, not political support or affiliation.

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

The dedicated [records post](/blog/records) has the full case; the short version is that a struct is already two things at once — a row of fields, and a brand that says *this* row is a `Handle`, not just any row shaped like one. Those two can come apart: a function can accept a *residual* of a struct — the same brand, narrowed to a few named fields — so a partial move or a disjoint borrow can type-check without converting to a separate structural type first.

That's simpler than the derive-based bridge I originally sketched here, and it's still settling in. The underlying question hasn't changed: partial consumption is an acknowledged-hard problem, not a solved one — the bet is that the nominal type itself can express it, rather than something bolted on beside it.

## Other Directions I'm Weighing

**Brands** are the most settled of these: the core idea — a nominal type is a row of fields plus an identity tag — already landed as part of the records design above, and a more general mechanism for tracking lifetime, capability, and allocator identity, in the spirit of [GhostCell](https://plv.mpi-sws.org/rustbelt/ghostcell/) and Scala's [capture checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html), has its own RFC under review. What's left unsettled is scope, not whether brands belong.

**Comptime** has moved the furthest on paper: three RFCs under review spell out compile-time execution of ordinary Metel code, staged by the same evaluator, rather than a separate macro language with its own grammar and hygiene rules. The interesting bet is that generalizing a single primitive — `emit`, which lets comptime code register a declaration or splice an expression back at its own call site — plus exposing Metel's own parser as an ordinary comptime-callable function, closes most of what a macro system is normally needed for: derive, repetitive declaration generation, compile-time-validated embedded DSLs, even Rust's `matches!`-style pattern macros. No token-stream grammar, no macro-invocation syntax, no hygiene system to design.

Less settled than either: [linear types](https://arxiv.org/abs/1710.09756) (use *exactly* once, stricter than Rust's affine ownership, as shipped in [Austral](https://borretti.me/article/introducing-austral)) have a draft RFC and real design work behind them, but nothing implemented yet; [algebraic effects and handlers](https://arxiv.org/abs/1312.1399), in the style of [Koka](https://koka-lang.github.io/koka/doc/index.html), now have an RFC under review too. Both have strong prior art elsewhere — the open question for each isn't whether it belongs, it's whether it fits Metel's own memory model cleanly enough to commit to, rather than sitting beside it as a bolted-on feature.

## Why Build It?

A language design only becomes interesting when its ideas meet generics, borrowing,
closures, partial moves, diagnostics, and performance constraints. Metel is where
those ideas can be tested together. Some will change under that pressure; that is
the point of building it.

## What Now?

The goal for the near term is a stable base worth building a real compiler on top of, rather than more design documents. Roughly, in order:

1. **Records and rows.** The branded-row model described above, settled enough to stop changing shape under everything built on it.
2. **Move checker.** Ownership and move semantics are already designed and partly implemented; the remaining work is making that solid across the rest of the language, not inventing it.
3. **Borrow checker and lifetimes.** Where a value lives and how long a reference to it stays valid, checked rather than assumed — still under review, the least settled of the three.
4. **A compiler.** Once the interpreter's pressure-testing has paid off and the first three are solid enough to not need rewriting out from under it.

Allocators and brands sit on top of that base rather than inside it, which is why they're missing from the list above — see "Other Directions I'm Weighing" for where those stand. Feedback, critique, and counterexamples are welcome along the way.
