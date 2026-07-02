---
id: blog-regions-not-lifetimes-2026-07-02
title: "Introducing Metel: Current state and future of the region system"
type: blog
created_date: '2026-07-02'
---

# Introducing Metel: Current state and future of the region system

Metel is a programming language that was born out of personal interest in type systems and memory safety. It started as a toy project, but has grown into a serious development effort. While the language is still in its early stages and does not have the pretension of being a competitor to Rust, Zig, Go, or C/C++, it has a unique approach to memory safety that is worth exploring. In this post, I will discuss the current state of Metel's type system, the design of its region system, and the future direction of the language.

## The type system is settled

The basic type system is now stable, and the language has a working interpreter. There are a few rough edges, but the core features are in place and the soundness improvements are already in progress. The core of the type system is very similar to Rust's, with a few small tweaks.

The most important feature is the planned region system, which tries to mix the best of Rust's lifetimes with Zig's Allocator model. The goal is to provide static memory safety while allowing for more flexible memory management than Rust offers out of the box.

## Regions: the core idea

A region is an allocation arena with a scope. Its handle is an ordinary runtime value, and that handle's *name* does triple duty — lifetime tag, disjointness proof, and the allocation strategy for the region. The compiler uses the name to prove that two pointers tagged with different regions can't alias, and to determine when a region can be safely deallocated:

```metel
fun build_node[region](val: i64) -> @[region] Node {
    @[region] Node { val, next: null }
}

BumpRegion::scoped([region]() -> {
    let n = build_node(42);   // [region] inferred — sole handle in scope
});
```

Two pointers tagged with different regions are provably non-aliasing at compile time — no locks, no runtime checks. It's the same guarantee Rust's borrow checker gives, but the "lifetime" is `region`, a variable sitting right there in scope. Errors can say "value escapes the scope of `region`" instead of explaining an abstraction the programmer never wrote.

## Cutting the ceremony: elision and inference

Every example above is the *explicit* form — always legal, never ambiguous, but noisy once a function touches more than one field or a struct holds more than one pointer. In practice almost all code only ever has a single region in scope at a time, so two ergonomics rules do most of the work of getting rid of the noise.

The first rule: wherever exactly one region is in scope, a bare `@` stands in for `@[region]`. This applies in type position and in expression position alike, so it collapses both a struct's field types and the allocation expressions that fill them:

```metel
// fully explicit
struct Header[r] {
    name:  @[r] String,
    value: @[r] String,
}

fun parse_header[region](line: String) -> Perhaps<@[region] Header> {
    @[region] Header { name: parse_name(line), value: parse_value(line) }
}

// same thing, elided
struct Header[r] {
    name:  @String,
    value: @String,
}

fun parse_header[region](line: String) -> Perhaps<@Header> {
    @Header { name: parse_name(line), value: parse_value(line) }
}
```

The `[region]` binder on the function itself never goes away — that's the one place a region has to be introduced by name. Elision only strips the tag everywhere *inside* the signature and body.

The second rule handles the call site, not just the type: if a function takes a region parameter and there's exactly one region handle in scope where you're calling it, you can drop the bracket argument entirely and let it get filled in for you:

```metel
fun build_list[region](vals: i64[]) -> @[region] Node {
    let mut head = @[region] Node { val: vals[0], next: null };
    for (let i in 1..array_len(vals)) {
        head = build_node(vals[i]);      // [region] inferred — no need to write build_node[region](...)
    }
    head
}
```

Both rules share the same escape hatch: the moment a second region enters scope, elision switches off and every tag has to be named again. That's deliberate — it's the same discipline Rust uses for lifetime elision. A two-region function like a "copy from one region into another" helper has to spell out both:

```metel
fun transfer<T>[src, dst: Outlives<src>](val: @[src] T) -> @[dst] T {
    @[dst] *val
}
```

There's one more wrinkle worth knowing about: `Heap` and `LocalHeap` are always usable by name, but they only join the pool of "things elision might infer" once you explicitly `use Heap;` (or `LocalHeap`). Inside a scoped arena that hasn't imported `Heap`, the scoped region is the only candidate and everything infers cleanly. Import `Heap` in that same scope and now there are two candidates, so inference refuses to guess and asks you to disambiguate:

```metel
use Heap;

BumpRegion::scoped([region]() -> {
    let a = make_node(1);           // error: ambiguous — Heap or region?
    let b = make_node[region](1);   // @[region] Node — arena-allocated
    let c = make_node[Heap](1);     // @[Heap] Node — a visible, deliberate escape from the arena
});
```

That ambiguity error is a feature, not friction — it's the compiler catching the one moment where "what region did this allocation escape into?" actually matters and making you say so.

## PhantomRegion: getting Rust's lifetimes back for plain borrows

Everything so far has been about *allocation* — a region you actually allocate into. But plenty of borrow-checking has nothing to do with allocation at all. Take the classic example:

```metel
fun longest(x: &Str, y: &Str) -> &Str { ... }
```

`x` and `y` are plain borrows. Nobody's allocating anything here, so there's no `[region]` in sight — and yet the borrow checker still needs to reason about how long `x` and `y` live relative to each other to know how long the returned borrow is allowed to live. This is exactly the case that sank the original phantom-lifetime design: you need *something* to hang that relationship on, but a bare `'a` with no runtime correspondent is precisely the "nothing in scope you could point at" complaint that regions were invented to fix. Reintroducing a `'a`-shaped escape hatch just to handle plain borrows would undercut the whole pitch.

The fix keeps faith with that pitch instead of abandoning it: **`PhantomRegion`** is a completely ordinary region — same `Region` interface as `BumpRegion` or `Heap` — with one extra guarantee: every allocation into it is unconditionally elided. It's real, constructible, sits in the type system like any other region; it just happens to compile away to nothing, always. That's the load-bearing difference from a bare `'a` — it's not phantom in the bad sense, it's just free.

The second piece: instead of making you declare one of these explicitly, **every binding of every type owns one by default.** `x: &Str` and `y: &Str` already, silently, each have their own `PhantomRegion` scoped to their own binding — the same way every value already has a drop obligation and a liveness range without you writing either down. Since the default region costs nothing to construct, giving one to every binding costs nothing either.

That alone doesn't let you *say* anything about the relationship between `x`'s region and `y`'s — for that there's a small piece of sugar that lets a region-tag position name the bindings directly, instead of requiring a separately-declared region parameter to exist purely as an anchor:

```metel
// what you'd have to write without the sugar — `a` exists for no reason
// except to be a name the bound can attach to
fun longest[a: PhantomRegion](x: &[a] Str, y: &[a] Str) -> &[a] Str {
    if x.len() > y.len() { x } else { y }
}

// with the sugar — x and y keep their plain types,
// the relationship is stated once, where it's actually needed
fun longest(x: &Str, y: &Str) -> &[x, y] Str {
    if x.len() > y.len() { x } else { y }
}
```

A region-tag position already resolves a bare name to a region — that's the same `[r]` from `&[r] T` earlier in this post. The sugar just extends that lookup: a name that isn't a declared region resolves to *that binding's own region* instead, and a list of names resolves to the tightest region all of them outlive. `[x, y]` here means the same thing an explicit `Outlives` bound would mean between two named regions — it's just reached by naming the bindings directly rather than inventing a throwaway anchor for the bound to sit on. (An earlier version of this sugar spelled it `Outlives<x, y>`, putting the bound's name itself in the tag slot — but `Outlives` everywhere else in the design is something you write *after* a region name, not a stand-in for one, so that got dropped in favor of extending the plain lookup rule instead.) Structurally, this is Rust's lifetime elision by another name: the common case reads exactly like `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str`, minus the part where `'a` is an annotation invented purely for the compiler's benefit. Here it's still a real region underneath, it's just one that happens to be free.

I'll admit this is still the least battle-tested piece of the region story — it's a small generalization of an existing rule rather than a load-bearing mechanism of its own, but I want to see it survive contact with real code before I'd call it settled. Still, it's the missing piece that lets plain borrows get the same "no phantom annotations" treatment as everything else in the region system.

## Design is ahead of the interpreter

I want to be upfront about this: the design is currently running well ahead of the implementation. The interpreter today still deep-clones values on bind and leans on reference counting under the hood — there's no borrow checker, no region allocator, none of the affine-move enforcement the design calls for. That's on purpose. I'd rather nail down a stable target on paper than build a borrow checker against a spec that's still shifting under it. But it does mean most of what's described here — regions included — is closer to "this is the plan" than "you can run this today."

## What's still open

Three bigger ideas are still unresolved. None of them block the core region work, but they'll shape how the language feels once they land.

**Brand types.** Regions solve disjointness for uniquely-owned data — two different `[r]` tags can't alias, full stop. But shared, reference-counted data doesn't fit that story: two `Rc` handles to the *same* cell are supposed to alias. What's missing is a lightweight way to give the compiler an unforgeable per-instance identity — a "brand" — so it can still reason about aliasing precisely even when ownership is shared instead of unique. The idea is solid in outline; the part I haven't settled is how a brand actually gets introduced into a program without turning into its own parallel annotation system.

**Compile-time unique `Rc`.** Right now, the plan for mutating through a shared pointer is a runtime check: ask "am I the only owner?", get back a maybe, and handle the case where the answer is no. That's always sound, but it's a runtime cost and an ergonomic tax for code that structurally *is* unique, just not provably so to the type system. The direction I like is a token-gated pattern, roughly GhostCell-style: a linear token whose exclusive borrow grants mutable access to every cell sharing its brand, with soundness coming from ordinary `&mut` exclusivity rather than a refcount check. It turns "prove I'm the sole owner at runtime" into "prove I hold the only `&mut` token at compile time" — but it depends on brand types existing first.

**Algebraic effects.** This one's further out and more exploratory. The appeal is structured, resumable side-effect handling — a computation declares the effects it might perform, and a surrounding handler intercepts them and decides whether to resume, abort, or resume more than once. What I like about how it might fit Metel is that most of the safety story falls out of rules the region model already has: a captured continuation is just an ordinary affine, heap-allocated value, so one-shot resumption isn't a special case bolted on for effects — it's what affine ownership already gives you for free. Multi-shot resumption is the part that doesn't fall out for free and is still an open question.

