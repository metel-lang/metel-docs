---
slug: what-affine-means
title: "What “Affine” Means: Ownership, Moves, and Copy"
date: 2026-09-09
authors: [vladislav]
tags: [design, ownership, types, metel]
draft: true
---

# What “Affine” Means: Ownership, Moves, and `Copy`

Before talking about Metel's move checker, records, or resource types, it helps
to name one small idea that Rust made familiar to many programmers: a resource
may be used **at most once**.

That is what *affine* means here. It does not mean “a value must be used exactly
once.” It means that once an operation consumes a value, the old name cannot be
used again. The value may also be left unused. That distinction matters.

## One Owner, One Cleanup

Consider a heap-allocated string in Rust:

```rust
let first = String::from("Metel");
let second = first;

println!("{first}"); // error: `first` was moved
println!("{second}");
```

`second = first` does not make a second independently owned string. It transfers
ownership from `first` to `second`. Rust calls that a *move*, and rejects the
later use of `first`.

This rule is not an arbitrary inconvenience. A `String` owns an allocation, and
the owner is responsible for cleaning it up. If two names could both believe
they owned that allocation, both could try to free it. If a name could keep
using the allocation after its owner had freed it, it could become a dangling
pointer. Moving ownership instead of silently duplicating it rules out both
mistakes before the program runs.

Passing a value to a function or returning it uses the same idea:

```rust
fn consume(text: String) {
    println!("{text}");
}

let name = String::from("Metel");
consume(name);
// `name` cannot be used here: ownership moved into `consume`.
```

The [Rust Book's ownership chapter](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
has the full account of this model. The useful mental model is simpler: an
owned value has one current owner, and a move changes who that owner is.

## `Copy` Is The Deliberate Exception

Some values do not represent a resource that needs a single cleanup authority.
An integer, boolean, or pair of integers can be duplicated cheaply and safely.
Rust types that make this promise implement `Copy`:

```rust
let first: i64 = 42;
let second = first;

println!("{first}");  // fine
println!("{second}"); // also fine
```

The assignment copied the integer, so both names are valid. `Copy` is not a
request for the compiler to guess when duplication is convenient; it is part of
the type's contract. Rust consequently forbids a type from being both `Copy` and
custom-cleaned-up through `Drop`: a freely duplicable value cannot also carry a
unique destruction obligation.

## Affine Is Not Linear

The names are easy to mix up:

| Discipline | What it requires |
| --- | --- |
| Ordinary unrestricted use | A value may be duplicated or discarded freely. |
| **Affine** use | A value may be consumed at most once; discarding it is allowed. |
| Linear use | A value must be consumed exactly once. |

Rust ownership is usually described as affine because a non-`Copy` value cannot
be used after it moves, but it can simply go out of scope. Its destructor, if it
has one, handles that ordinary end of life. Linear types are stricter: they make
the program account for every resource use explicitly.

This is why “linear types” are not just another name for Rust ownership. They
start from a related question — how should a program account for a resource? —
but impose a stronger answer. That distinction will matter when Metel considers
linear types later.

## What This Does Not Explain

Ownership and moves answer a question about **who may consume a value**. They do
not yet answer a different question: **who may access it, and for how long?**

For example, a program may want to inspect a value without taking it, or update
it temporarily without giving up its owner. That is borrowing. Rust's borrow
checker governs the relationship between shared reads, exclusive writes, and the
duration of those accesses. It is a separate layer, which the next post covers.

Keeping the two layers distinct makes later design discussions much easier to
read. A “use after move” is an ownership problem. Two incompatible accesses to
the same place are a borrowing problem. They often appear together, but neither
rule is a substitute for the other.

## Where Metel Is Today

Metel uses the same basic vocabulary, but it should not be mistaken for a Rust
clone or for a finished ownership system. Its move checker enforces the first
slice: non-`Copy` values move, `Copy` values may be reused, and `Drop` marks a
destruction obligation. This is affine move checking, not linear typing and not
yet borrow checking.

The implementation is deliberately opt-in while the model is being pressure
tested. The [Metel ownership specification](/docs/reference/spec/ownership)
describes the current rules; future posts will cover how those rules interact
with closures, records, and field-sensitive ownership. The next prerequisite is
the borrow checker itself: what it protects, and what it does not.
