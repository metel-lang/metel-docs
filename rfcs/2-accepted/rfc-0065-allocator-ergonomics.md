---
id: rfc-0065
title: "Allocator and Lifetime Ergonomics"
date: '2026-06-27'
updated: '2026-07-20'
status: accepted
---

> **Status — under review.** Rewritten 2026-07-05. The original RFC specified elision
> for the bracket channel (`@[r]` → `@`). Under the split model the bracket channel is
> gone: allocators live in the value channel `()`, lifetime anchors in the type channel
> `<>`. This RFC restates elision for both. Depends on RFC-0063 (Allocator Handles) and
> RFC-0067 (Lifetime Anchors). Do not implement before RFC-0063 is resolved.
>
> **Updated 2026-07-06:** added §1a, elision for RFC-0063's new tag-only allocator
> parameters (`<@a>`). Reuses the existing single-input/self/ambiguous structure of
> §2 rather than introducing a third rule set.

> **Updated 2026-07-20:** added §1b, call-site allocator-argument elision. Every
> worked example in the accepted allocator cluster (`wrap(@a, 42_u64)` — RFC-0077
> §3.3, checked directly, not assumed) writes the allocator argument out in full at
> every call, including calls made from inside a scope with only one allocator, where
> §1's own type-position rule would already elide it if it were a type annotation
> instead of a call argument. That gap — real code threading an allocator through
> several layers of helper calls still spells `@a` at every single call — is the
> concrete substance behind a real critique of this cluster's ergonomics (verbose even
> with §1/§1a/§2 all active), cross-checked against how Zig, Odin, and Kotlin handle
> the same problem (see §1b's own Alternatives note). Unlike RFC-0075's withdrawn
> inter-function inference, this rule never adds anything invisible to a *signature*
> — the callee's `(@a: A)` parameter stays exactly as explicit as it is today; only a
> caller's redundant re-naming of an already-unambiguous argument is elided.

> **Updated 2026-07-20 (second pass):** a real critique — an allocator genuinely
> **declared** two scopes out (e.g. `Heap` as an outer function's own parameter, with
> an inner `BumpAlloc::scoped((@a) -> {...})` closure) had no stated resolution;
> read literally, both would count as candidates for a bare allocation expression
> inside the closure, forcing an explicit name — exactly backwards from what the
> closure is for. A first draft of this fix proposed silent depth-based shadowing
> (innermost declared allocator always wins); **reverted after discussion.** Silent
> shadowing between two differently-named, differently-typed candidates is closer to
> overload resolution than to ordinary name scoping, and reintroduces exactly the
> hazard this RFC's own "ambiguity is always a compile error, never a silent choice"
> invariant exists to prevent: adding an unrelated `BumpAlloc::scoped` closure
> anywhere inside a function would silently change what every already-elided
> allocation inside it means, with no diagnostic. Replaced with **type-directed
> candidate filtering** (new subsection under §1): "in scope" for elision means *in
> scope and of the type this position statically requires*, whenever a concrete type
> is known — which resolves the `Heap`-vs-`BumpAlloc` case for free, for any
> concretely-typed position, with no shadowing rule needed at all, since the two
> never share a type to begin with. The one residual shape — a bare allocation
> expression with no concrete type to filter by — stays a hard compile error, not a
> silent tiebreak, matching how Kotlin's own context parameters (already surveyed in
> §1b) resolve a genuine same-type collision: loudly, not by nesting depth. §1b
> updated to state explicitly that it inherits this same type-directed filtering.

> **Status — accepted (2026-07-10).** Phase 0 ratification sweep: split model consistency-checked (RFC-0063 sec9 items 1/2/5 synced with roadmap-2026-07-07 Phase 0 decision; RFC-0066/0068 stale titles fixed); sweeping the cluster from under-review to accepted per reports/implementation/roadmap-2026-07-07.md Phase 0.

## Summary

RFC-0063 and RFC-0067 specify the core allocator and lifetime-anchor systems in explicit
form. This RFC adds elision layers that make the common cases annotation-free:

1. **Allocator elision** (§1) — bare `@` without a name resolves to the unique
   in-scope allocator; two or more forces an explicit name.
2. **Tag-only allocator elision** (§1a) — the same bare `@`, when no value-channel
   allocator is in scope at all, resolves to a fresh compile-time-only tag rather
   than a type error.
3. **Call-site allocator-argument elision** (§1b) — a call to a function with
   exactly one value-channel allocator parameter may omit that argument entirely
   when exactly one allocator is in scope at the call site.
4. **Lifetime anchor elision** (§2) — the common one-to-one and self-anchor cases
   need no explicit `<&r>` declaration.

All four rules share one invariant: **elision is legal only when the compiler can
determine the unique correct answer**; ambiguity is always a compile error, never a
silent choice.

---

## 1. Allocator elision

If exactly one allocator is in scope, the name after `@` may be dropped:

```metel
BumpAlloc::scoped((@a) -> {
    let x = @Node { val: 1 };     // @a Node — `a` is the sole allocator
    let y = @List::Cons { head: x, tail: @List::Nil {} };
});
```

`@` alone always implies allocation; it never means "address-of" (that is `&`). Elision
applies in both type position and expression position:

```metel
// type position
fun build_node(@a: BumpAlloc, val: i64) -> @Node { ... }
//                                          ^^^^^ == @a Node

// expression position
let node = @Node { val: 1 };   // == @a Node { val: 1 }
```

**Type-directed candidate filtering.** "In scope," for elision purposes, means *in
scope and of the type this position statically requires*, whenever a specific
concrete type is known — not merely "any value implementing `Alloc`, of any type,
pooled into one flat set." A position resolves against `Alloc` generically only when
nothing more specific is known (a `<A: Alloc>` type parameter, as in `transfer` below
— there is no concrete type to filter by, so every in-scope allocator is a candidate
regardless of its own concrete type). A position with a genuinely concrete
requirement — a call to a non-generic `fun build_node(@a: BumpAlloc, ...)`, or a type
annotation against one — filters candidates down to that exact type first. Two
allocators of *different* concrete types therefore never collide at such a position,
by construction, regardless of how they're nested:

```metel
fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let n = build_node(1);   // requires BumpAlloc specifically (§1b elision) —
                                  // h: Heap was never a candidate; resolves to a
    });
}
```

**Two or more allocators (of the same required type, or no concrete type to filter
by).** When two or more *candidates* remain after type-directed filtering, every `@`
must be named. The disambiguation is forced at the source level — the compiler never
silently picks one:

```metel
fun transfer<A: Alloc, B: Alloc>(@src: A, @dst: B, val: @src T) -> @dst T {
    @dst val: T   // explicit: two allocators, both must be named — A and B are
                  // abstract type parameters, so there is no concrete type to
                  // filter by; type-directed filtering cannot help here
}
```

**Static allocators.** `Heap` and `LocalHeap` are always accessible by name and may be
used explicitly (`@Heap expr`) anywhere. They enter the elision candidate set only when
they appear as declared parameters in the current function or scope:

```metel
fun store(@h: Heap, val: T) -> @h T {
    @val   // h is the sole allocator in scope; elides to @h T
}
```

This keeps heap allocations visible — a bare `@` inside a `BumpAlloc::scoped` block
always resolves to the scoped allocator, never to a heap that happens to be importable.

**Nested scopes: type-directed filtering resolves the common case; a residual
same-type collision is a hard error, not a silent shadow.** An allocator can be
genuinely **declared** two lexical scopes out, not just importable:

```metel
fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let x = @Node { val: 1 };   // bare allocation expression — no signature
                                     // constrains a required type here
    });
}
```

`@Node { val: 1 }` is a *bare allocation expression* — nothing about it requires a
specific concrete allocator type the way calling `build_node(@a: BumpAlloc, ...)`
does, so type-directed candidate filtering (above) has nothing to filter by: `h:
Heap` and `a: BumpAlloc` are both structurally valid candidates for "any `Alloc`,"
regardless of depth. This is genuinely different from the call-site and
concretely-typed-annotation cases, which type-directed filtering already resolves
for free — this is the one residual shape where a real answer is still needed.

**Resolution: this is ambiguous, and stays a compile error — it is not resolved by
depth-based shadowing.** An earlier version of this section proposed that the
innermost scope's own declared allocator should silently shadow every outer one.
Rejected: shadowing by nesting depth alone is a *silent* choice among two
differently-named, differently-typed candidates — closer to overload resolution
than to ordinary name scoping — and it reintroduces exactly the hazard this RFC's
own governing invariant exists to prevent: introduce a `BumpAlloc::scoped` closure
anywhere inside `process` for an unrelated reason, and every bare allocation
expression already inside it silently starts meaning the new arena instead of `h`,
with no diagnostic marking the change. Kotlin's own context parameters — the
precedent §1b already surveys — answer this exact shape of question the same way:
a genuine same-type collision between two in-scope candidates is a compile error,
full stop; there is no implicit "closer one wins" rule.

```metel
fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let x = @a Node { val: 1 };   // explicit: h and a are both bare-Alloc
                                        // candidates here; name the one you mean
    });
}
```

Type-directed filtering (above) is what keeps this error rare in practice rather
than common: it already resolves every elided position with a concretely-known
required type — which covers most real code, since an outer "ambient" allocator
(`Heap`, or a caller-supplied arena) and an inner throwaway one (`BumpAlloc` for a
hot loop) are, in the overwhelming majority of real cases, different concrete
types to begin with. The residual bare-expression, same-type case above is the
genuinely rare shape this RFC leaves as an explicit-naming requirement rather than
inventing a silent tiebreak for.

---

## 1a. Tag-only allocator elision

RFC-0063's tag-only allocator parameter (`<@a>`) has its own elision layer, reusing
§1's `@` sigil rather than introducing a new one. The two rules are distinguished by
whether a real value-channel allocator is in scope at the point `@` appears:

- If one is in scope, bare `@` names it (§1, unchanged).
- If none is in scope, bare `@` introduces a fresh, compile-time-only tag-only
  parameter instead of being a type error.

```metel
fun identity(val: @Node) -> @Node { val }
// no (@a: A) parameter anywhere in scope — @ here elides a fresh <@a>,
// exactly as if the signature had been fun identity<@a>(val: @a Node) -> @a Node
```

Relating the elided tag across multiple positions follows the same structure as
lifetime anchor elision (§2), because a tag-only parameter and a lifetime anchor are
both, mechanically, a bare compile-time name with no runtime companion:

**Single input, no relation needed.** One input position carrying the tag; the
elided output tag is that same one (compare §2 Rule 2):

```metel
fun identity(val: @Node) -> @Node { val }
```

**Two independent tag-only positions get independent tags by default** (compare §2
Rule 1) — there is no assumption that two separately-elided `@` positions refer to
the same allocator:

```metel
fun pair(a: @Node, b: @Node) -> ()
// two distinct, unrelated elided tags — nothing forces them to match
```

**Forcing two positions to share a tag requires an explicit declaration** (compare
§2 Rule 4 — ambiguity is a compile error, not a silent choice):

```metel
fun same_arena<@a>(x: @a Node, y: @a Node) -> @a Node { x }
// explicit: x, y, and the return all share tag `a`
```

**Extraction is never part of this elision.** Tag-only elision only ever produces
`@_ T` (some tag, generic or explicit) — never plain `T`. A signature with no `@` at
all (e.g. `fun identity(val: Node) -> Node`) is unaffected by this section: it
denotes a genuinely untagged parameter, and passing an `@a T` argument to it is
governed by RFC-0066 §3a (explicit ascription required; never implicit), not by
elision. The presence or absence of `@` on a plain type is exactly what distinguishes
"preserve whatever storage flows in" (`@Node`) from "requires already-extracted
ownership" (`Node`).

---

## 1b. Call-site allocator-argument elision

§1 and §1a elide the allocator *name* inside a type or expression, but neither
touches the argument list of a call — every worked example in the accepted cluster,
checked directly rather than assumed, spells the allocator argument out in full at
every single call site, including calls made from a scope with only one allocator
in it:

```metel
fun wrap<T, A: Alloc>(@a: A, val: T) -> @a T { @a val }

BumpAlloc::scoped((@a) -> {
    let x = wrap(@a, 42_u64);   // RFC-0077 §3.3 — `a` is the sole allocator, yet
                                 // still written out in full at the call site
});
```

That is the real substance of "the elision rules are insufficient" — a helper
threading an allocator down through several layers of calls still writes `@a` at
every layer, even though every one of those call sites already has exactly one
candidate in scope. This section closes that gap:

> A call to a function whose signature declares **exactly one** value-channel
> allocator parameter `(@a: A)` may omit the corresponding argument entirely when
> exactly one *matching* allocator is in scope at the call site — subject to the
> same type-directed filtering §1 already defines: if the parameter's declared type
> is concrete (e.g. `@a: BumpAlloc`), only in-scope allocators of that exact type
> count as candidates; if it is a generic `<A: Alloc>` bound (as `wrap` above), any
> in-scope allocator counts, the same as an ordinary §1 elision site. The omitted
> allocator is not a positional gap — the argument list simply has one fewer entry,
> the same way `<@a>` (§1a) never occupies a value-argument slot at all.

```metel
fun build_node(@a: BumpAlloc, val: i64) -> @a Node { @a Node { val, next: null } }

fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let n = build_node(1);   // requires BumpAlloc specifically — h: Heap was
                                  // never a candidate; resolves to a unambiguously,
                                  // regardless of h being in scope at all
    });
}
```

```metel
BumpAlloc::scoped((@a) -> {
    let x = wrap(42_u64);   // == wrap(@a, 42_u64) — the sole allocator, elided
});
```

**Scoped strictly to single-allocator signatures — this does not extend to
multi-allocator calls.** `transfer<T, A: Alloc, B: Alloc>(@src: A, @dst: B, val: @src
T) -> @dst T` from RFC-0063 §4 keeps its two allocator arguments explicit at every
call site, even when the caller happens to have exactly two allocators in scope:
which in-scope allocator plays `src` and which plays `dst` is a *positional*
question elision cannot answer from type compatibility alone — unlike Kotlin's
context parameters (see Alternatives, below), where two differently-*named*
same-typed parameters in one signature are already a compiler-flagged ambiguity, not
a case elision is expected to resolve either. This mirrors §1's own existing
"two or more allocators forces explicit naming" invariant exactly, generalized from
"in scope" to "in the callee's own signature."

**Why this is safe where RFC-0075's withdrawn inter-function inference wasn't.**
RFC-0075 considered and rejected giving a function an *implicit* allocator
parameter inferred from its body, for three reasons: hidden lifetime contracts,
stack-overflow risk from invisibly-allocated recursive structures, and ABI changes
invisible at the signature. None of those apply here — the callee's signature is
untouched; `(@a: A)` is exactly as explicit as it was before this section. Only a
caller's *redundant* re-statement of an argument the compiler can already determine
uniquely is elided, the same class of "legal only when the answer is unique, never a
silent choice" rule §1/§1a/§2 already use.

### Alternatives considered

Three real languages solve the same underlying problem — a value every call in a
chain needs, but nobody wants to repeat at every call site — with different
tradeoffs, surveyed directly rather than from memory:

- **Zig** has no such mechanism at all, by explicit design: the allocator is always
  a visible, explicit parameter, every time, permanently. Rejected as this section's
  model precisely because that's the status quo being amended.
- **Odin**'s implicit `context` struct (carrying `context.allocator`) is passed on
  every call automatically under the default calling convention and read implicitly
  by anything that allocates; a scope reassigns `context` to override it, and a
  function opts out entirely via the `"contextless"` calling convention. This solves
  verbosity completely but reintroduces exactly what RFC-0075 already rejected for
  inference: which allocator a function actually uses becomes invisible at its call
  site, resolved from mutable ambient state rather than readable off a signature.
  Rejected for the same reason RFC-0075's inter-function inference was.
- **Kotlin**'s context parameters (`context(users: UserService) fun f(...)`, stable
  as of Kotlin 2.4) are the closest precedent to this section's rule: every function
  that needs one still declares it in its own signature — no silent propagation
  across call depth — but the call site never re-passes it by name, resolving it by
  type from an ambient `context(users) { ... }` block or the caller's own context
  parameters; ambiguity between two same-typed candidates is a compile error. That
  last rule is verbatim this RFC's own governing invariant, arrived at
  independently. Kotlin's own design history is a useful cross-check: context
  parameters replaced an earlier, nameless "context receivers" design specifically
  because namelessness broke traceability — this section's rule keeps the parameter
  named in every signature for the same reason, never anonymous.

---

## 2. Lifetime anchor elision

Explicit `<&r>` declarations and `&r T` / `&r var T` annotations in signatures are
needed only when the compiler cannot infer the anchor relationship. Four rules cover the
common cases:

**Rule 1 — Each elided `&` input gets a distinct fresh anchor.**

```metel
fun process(&Str, &i64) -> ()
// each & gets its own anonymous anchor; no relationship between them
```

**Rule 2 — Single input anchor propagates to output.**

```metel
fun first_char(&Str) -> &Char
// one input anchor → output uses the same anchor; no declaration needed
```

**Rule 3 — `&self` / `&var self` wins as the output anchor.**

```metel
fun get(&self, key: &Key) -> &Val
// self anchor wins over key; return borrow valid for self's lifetime
```

**Rule 4 — Ambiguous → compile error, explicit `<&r>` required.**

```metel
fun longest(&Str, &Str) -> &Str
// two distinct anchors; which one bounds the return? compile error.

fun longest<&r>(&r Str, &r Str) -> &r Str { ... }
// explicit: both inputs and the output share the same anchor
```

These four rules together eliminate anchor annotations from the vast majority of
function signatures. Explicit `<&r>` declarations appear only at the handful of points
where the anchor relationship genuinely matters and is not derivable from structure.

---

## 3. What the programmer actually writes

With both rules active, the annotation surface is minimal. A full single-allocator API,
without elision on the left and with elision on the right:

```
── explicit (RFC-0063 + RFC-0067) ──────────────────────────────────┐  ── with elision ──────────────────────────────────────────────┐
                                                                     │                                                               │
struct Header<&a> {                                                  │  struct Header<&a> {                                          │
    name:  @a String,                                                │      name:  @String,                                         │
    value: @a String,                                                │      value: @String,                                         │
}                                                                    │  }                                                            │
                                                                     │                                                               │
fun parse_header(@a: BumpAlloc,                                      │  fun parse_header(@a: BumpAlloc,                              │
    line: String,                                                    │      line: String,                                            │
) -> Perhaps<@a Header> {                                            │  ) -> Perhaps<@Header> {                                      │
    @a Header { name: ..., value: ... }                              │      @Header { name: ..., value: ... }                        │
}                                                                    │  }                                                            │
                                                                     │                                                               │
fun find_header<&a>(@a: BumpAlloc,                                   │  fun find_header(@a: BumpAlloc,                               │
    req:  &a Request,                                                │      req:  &Request,                                          │
    name: String,                                                    │      name: String,                                            │
) -> Perhaps<&a String> { ... }                                      │  ) -> Perhaps<&String> { ... }                                │
```

The allocator parameter is still declared — that is the decision point where an
allocation strategy is named. Elision applies to the `@`-bearing type positions inside
the signature and the `&`-bearing positions that follow from it.

---

## 4. Unresolved questions

1. **Closures.** The grammar for allocator parameters on closure literals
   (`BumpAlloc::scoped((@a) -> { ... })`) is left to RFC-0050 (Closure Capture Lists).

2. **§1b's exact spelling at the parser level.** This RFC specifies that the omitted
   argument is not a positional gap — the call's argument list simply has one fewer
   entry, mirroring `<@a>` never occupying a value-argument slot. An alternative
   spelling would keep a bare `@` placeholder in the call (`wrap(@, 42_u64)`),
   mirroring §1's own `@a Node` → `@Node` pattern more literally at the cost of
   giving up the full ergonomic win. This RFC's position is the former (full
   omission); recorded here as the one specific grammar-level choice left to confirm
   once §1b's rule is actually implemented, not left ambiguous in the rule itself.

---

## References

- RFC-0063 (Allocator Handles) — allocator parameters, `@a T`, `@a expr`, and the
  tag-only parameter form (§4) this section elides.
- RFC-0066 (Allocated Value Extraction) — §3a: why a plain, `@`-free `T` never
  implicitly accepts an `@a T` argument, which is what distinguishes it from the
  elided tag-only form here.
- RFC-0067 (Lifetime Anchors) — lifetime anchors, `&r T`, `&r var T`, anchor elision rules.
- RFC-0050 (Closure Capture Lists) — closure grammar for `(@a) -> {}`.
- RFC-0075 (Region Inference, draft/parked) — a different elision axis (local
  temporaries that never cross a function boundary need no `@` at all); §1b above
  is call-site argument elision for already-explicit signatures, which is why §1b's
  safety argument doesn't depend on RFC-0075's own withdrawn inter-function
  inference, and why the two proposals don't compete for the same scope.
- RFC-0077 (Allocator Generics) — §3.3's `wrap(@a, 42_u64)` worked example, the
  concrete evidence for §1b's motivation.
