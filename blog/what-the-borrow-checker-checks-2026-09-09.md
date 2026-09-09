---
slug: what-the-borrow-checker-checks
title: "What the Borrow Checker Actually Checks"
date: 2026-09-09
authors: [vladislav]
tags: [design, ownership, types, metel]
draft: true
---

# What the Borrow Checker Actually Checks

The borrow checker is often described as the difficult part of Rust. A clearer
starting point is that it answers a different question from ownership.

Ownership asks who may consume or clean up a value. Borrow checking asks who may
**access** that value right now. A borrow lets code use data without becoming its
owner; the checker makes sure that access remains valid and that reading and
writing do not make incompatible promises at the same time.

## Shared Or Exclusive Access

Rust has two ordinary kinds of reference:

| Reference | Access it grants |
| --- | --- |
| `&T` | Shared, read-only access. Many may exist at once. |
| `&mut T` | Exclusive, read-write access. It may not overlap with any other access to the same value. |

The rule can be stated compactly: at a given time, a value may have **one
mutable reference or any number of immutable references, but not both**.

That lets ordinary reading stay cheap and flexible:

```rust
let name = String::from("Metel");
let first = &name;
let second = &name;

println!("{first} / {second}");
```

Neither reference can change `name`, so the two readers cannot invalidate each
other's view. Mutation is different:

```rust
let mut name = String::from("Metel");
let writer = &mut name;

writer.push_str(" language");
println!("{writer}");
```

The mutable reference is allowed because it is the only active access. Rust will
reject a second mutable reference, or a shared reference that overlaps it. The
point is not to make mutation impossible; it is to make the authority to mutate
unambiguous.

This is why the rule is sometimes summarized as “aliasing XOR mutability.”
Either data is shared for reading, or it is exclusively available for writing.
The [Rust Book's borrowing chapter](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)
walks through the resulting compiler errors and their fixes.

## Lifetimes Are The Duration Of A Promise

A reference is not valid forever. It promises that the value it points to will
remain available for the duration of the borrow. A *lifetime* is the part of the
program during which that promise holds.

In everyday Rust, lifetime annotations are usually absent because the compiler
can infer them. The important idea is not the annotation syntax; it is that a
reference cannot outlive the value it refers to. Nor can its exclusive or shared
access rights overlap in a way that breaks the rule above.

The duration is often shorter than a lexical scope. Rust can see that a shared
reference is no longer used and permit a later mutable borrow:

```rust
let mut name = String::from("Metel");
let reader = &name;
println!("{reader}"); // last use of `reader`

let writer = &mut name; // permitted after the last read
writer.push_str(" language");
```

This is a useful correction to the idea that the checker only counts braces. It
tracks the accesses that remain relevant to the program, so it can reject an
overlap that would be unsafe without needlessly rejecting a finished borrow.

## What The Checker Buys

Together, validity and exclusivity rule out several error classes before runtime:

- A reference to data that has already gone away.
- A write while another part of the program relies on a stable shared view.
- Two unsynchronized writers to the same value.

They do not prove that a program has the right algorithm, the right business
rule, or the right API. They also do not make every valid design easy to express.
The borrow checker is a conservative static analysis: it makes a specific set of
access guarantees, and sometimes requires a program's structure to make those
guarantees visible.

## What This Means For Metel

Metel currently has references, written `&T` and `&var T`, but its current move
checker does not enforce Rust-style borrow durations or exclusive-access rules.
A reference grants access; it does not take ownership. That distinction is
already useful, but it is not a borrow checker.

Borrow checking and lifetime anchors are active design work in Metel. The
proposal is to make the common lifetime relationship name an existing binding,
rather than require a fresh abstract name such as Rust's `'a`. Whether that
spelling remains the right choice has to be earned by the same tests and
interactions that shape the rest of the language.

For now, the important boundary is simple: Metel's move checker answers whether
a non-`Copy` value has been consumed. A future borrow checker will answer whether
the accesses to that value are compatible and remain valid. Later posts on
references, lifetime anchors, allocator identity, and field-sensitive ownership
all build on that difference.
