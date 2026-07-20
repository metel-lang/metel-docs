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

> **Updated 2026-07-20 (second pass):** §1's "Static allocators" paragraph guaranteed
> that a merely-*importable* `Heap`/`LocalHeap` never enters the elision candidate set
> inside a `BumpAlloc::scoped` closure — but said nothing about an allocator genuinely
> **declared** two scopes out (e.g. `Heap` as an outer function's own parameter,
> with an inner `BumpAlloc::scoped((@a) -> {...})` closure). Read literally, "in
> scope" had no depth qualifier, so the outer declared allocator and the closure's own
> would both count as candidates, forcing an explicit name inside the closure — exactly
> backwards from what the closure is for, and the concrete shape of a real
> "elision is counterintuitive" critique. Added a general rule directly under that
> same paragraph: elision candidates are computed per lexical scope, innermost first;
> a scope with its own declared allocator shadows every outer one entirely. The
> existing Heap/LocalHeap guarantee is now a degenerate case of this rule rather than
> a separate carve-out.

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

**Two or more allocators.** When two or more allocators are in scope, every `@` must be
named. The disambiguation is forced at the source level — the compiler never silently
picks one:

```metel
fun transfer<A: Alloc, B: Alloc>(@src: A, @dst: B, val: @src T) -> @dst T {
    @dst val: T   // explicit: two allocators, both must be named
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

**Nested scopes: innermost declared allocator shadows every outer one entirely.** The
guarantee above ("never to a heap that happens to be importable") covers only
*merely-importable* Heap/LocalHeap — it does not, as written, say what happens when
an allocator is genuinely **declared** two scopes deep, not just one:

```metel
fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let x = @Node { val: 1 };   // @a or @h? — undefined by the text above
    });
}
```

Read literally, "in scope" has no depth qualifier — `h` (declared on `process`) and
`a` (declared on the closure) are both lexically visible at the point `@Node` appears,
so §1's own "two or more allocators forces an explicit name" rule would make this
ambiguous. That is exactly backwards from what `BumpAlloc::scoped` is *for*: the whole
point of writing that closure is to establish a fresh, local allocation context, and
an outer function's unrelated `Heap` parameter — never referenced inside the closure
at all — forcing an explicit name here is the concrete shape of a real "elision is
counterintuitive" critique, not a hypothetical one.

**Resolution: the elision candidate set is computed per lexical scope, innermost
first.** A scope that declares its own allocator parameter(s) — a function or a
closure literal's own `(@a: A)` — shadows every allocator declared in any enclosing
scope completely; outer allocators are not merged into a wider pool, they are simply
not candidates once an inner declaration exists. Only when the current scope declares
no allocator of its own does resolution fall through to the nearest enclosing scope
that does — the same inner-first walk ordinary name resolution already performs for
any binding, generalized here from "same name" shadowing to "member of the elision
candidate set" shadowing:

```metel
fun process(@h: Heap, items: List<i64>) {
    BumpAlloc::scoped((@a) -> {
        let x = @Node { val: 1 };   // unambiguous: @a Node — h is not a candidate,
                                     // the closure's own scope declares a
    });
    let y = @Node { val: 2 };       // unambiguous: @h Node — no inner declaration
                                     // here, falls through to process's own h
}
```

This is not a special case bolted onto the Heap/LocalHeap rule above — it is the
general form the Heap guarantee was always a degenerate instance of: a *merely
importable* Heap is never a declared candidate at any scope depth, so it was already
being "shadowed" by definition, vacuously, at every point. Stating the rule in terms
of scope depth rather than "importable vs. declared" is what makes the
`BumpAlloc::scoped`-with-an-outer-`Heap`-parameter case fall out for free instead of
needing its own separate carve-out.

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
> exactly one allocator is in scope at the call site. The omitted allocator is not
> a positional gap — the argument list simply has one fewer entry, the same way
> `<@a>` (§1a) never occupies a value-argument slot at all.

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

Explicit `<&r>` declarations and `&r T` / `&r mut T` annotations in signatures are
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

**Rule 3 — `&self` / `&mut self` wins as the output anchor.**

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
- RFC-0067 (Lifetime Anchors) — lifetime anchors, `&r T`, `&r mut T`, anchor elision rules.
- RFC-0050 (Closure Capture Lists) — closure grammar for `(@a) -> {}`.
- RFC-0075 (Region Inference, draft/parked) — a different elision axis (local
  temporaries that never cross a function boundary need no `@` at all); §1b above
  is call-site argument elision for already-explicit signatures, which is why §1b's
  safety argument doesn't depend on RFC-0075's own withdrawn inter-function
  inference, and why the two proposals don't compete for the same scope.
- RFC-0077 (Allocator Generics) — §3.3's `wrap(@a, 42_u64)` worked example, the
  concrete evidence for §1b's motivation.
