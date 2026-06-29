---
id: rfc-0075
title: "Region Inference — Implicit AutoRegion"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region Ergonomics),
> RFC-0073 (AutoRegion). Proposes a third elision level that elides both the `@` and the
> region tag when a region-aware type appears without any annotation. The compiler infers an
> implicit AutoRegion whose scope is derived from usage.

## Summary

RFC-0065 introduced the first two elision levels:

| Form | Elides | Fires when |
|---|---|---|
| `@[r] T` | nothing — fully explicit | always |
| `@T` | the region tag | exactly one region in scope |

This RFC proposes a third level:

| Form | Elides | Fires when |
|---|---|---|
| `T` (no `@`) | the `@` prefix and the region tag | no explicit region required by context |

When the compiler sees a type or value expression that requires a region pointer but
carries no `@` annotation and no explicit tag, it inserts an implicit AutoRegion. The
scope of that AutoRegion is derived from how the value is actually used — the borrow
checker determines the narrowest scope consistent with the program's lifetime constraints.

The inferred regions are not invisible. They have compiler-generated names that appear in
error messages. The programmer can always step up to `@T` or `@[r] T` when the inferred
name is insufficient.

---

## Motivation

The following function constructs an intermediate list and returns it:

```metel
// Today — explicit regions everywhere
fun collect_evens[r](nums: &List<I32>) -> @[r] List<I32> {
    let result: @[r] List<I32> = @[r] List::Nil {};
    for num in nums {
        if num % 2 == 0 {
            result = @[r] List::Cons { head: num, tail: result };
        }
    }
    result
}
```

The region `r` carries real information: it tells the caller what lifetime scope the
returned list belongs to. But the function's author did not choose that scope — the
caller did, by naming the region they pass as `[r]`. The `@[r]` annotations are bookkeeping,
not decisions.

With region inference:

```metel
// With region inference — write the logic
fun collect_evens(nums: &List<I32>) -> List<I32> {
    let result = List::Nil {};
    for num in nums {
        if num % 2 == 0 {
            result = List::Cons { head: num, tail: result };
        }
    }
    result
}
```

The compiler infers an implicit AutoRegion for the list allocations. The lifetime
relationship — the returned list is valid as long as the caller keeps it — is preserved;
it is now derived from usage rather than stated explicitly.

Region annotations remain valuable when the programmer needs to express specific
contracts: allocating into a `BumpRegion` for performance, requiring `@[Heap] T` for
sendability, or using named regions when two allocation scopes appear in the same
function. Inference eliminates the ceremony for everything else.

---

## Design

### The elision tower

Three elision levels compose. Each level desugar to the one below:

```
T           →   @T          →   @[auto_r] T
(RFC-0075)      (RFC-0065)      (explicit)
```

**Level 2 — `T` (this RFC)**: The `@` is absent. The compiler sees the type in a position
that requires a region pointer and inserts an implicit AutoRegion whose scope it derives
from the value's usage. This desugars to level 1.

**Level 1 — `@T` (RFC-0065)**: The `@` is present but no tag is given. The compiler fills
in the single region in lexical scope. If no region is in scope or more than one is, this
is an error — the programmer must be explicit.

**Level 0 — `@[r] T` (RFC-0063)**: Fully explicit. No inference. No ambiguity.

The three levels are orthogonal choices for each annotation site. A single function may
use all three in different positions.

### Where level-2 elision fires

Level-2 elision fires when a type appears in a **region-requiring position** without any
`@` prefix and without an explicit region parameter in scope to supply via RFC-0065. The
region-requiring positions are:

- **Value expressions**: `T { ... }`, `T::Variant { ... }`, function call results of
  type `T`, when `T` has region-allocated fields.
- **Let bindings**: `let x = expr` where the inferred type of `expr` is region-allocated.
- **Function return types**: `-> T` where `T`'s concrete representation requires region
  storage.
- **Struct and enum fields** declared without a region parameter when the field type
  requires one.

Level-2 elision does **not** fire when:

- A `@` is present (level 1 fires instead).
- A named region is in scope and level-1 elision applies.
- The type has no region-allocated content (plain value types like `I32`, `(I32, Bool)`,
  or structs with only value-type fields never need a region and do not trigger elision).

### Inferred region names

Each inferred AutoRegion receives a compiler-generated name. In error messages the
compiler uses a name like `'auto.42` where `42` encodes the source location. The
programmer never writes this name; it exists so error messages can refer to distinct
inferred regions by name rather than by description.

```
error: borrowed value does not live long enough
  --> src/main.mt:12:5
   |
11 |     let inner = List::Cons { head: 1, tail: List::Nil {} };
   |                 ---- value allocated in inferred region 'auto.11
12 |     return &inner;
   |     ^^^^^^ returns a reference to a value in a shorter-lived region
   |
   = note: region 'auto.11 is inferred from usage; to control the scope,
           write @[r] and introduce an explicit AutoRegion or BumpRegion
```

If the programmer needs to refer to an inferred region explicitly — to annotate a
second binding that must share the same scope — they can promote it by writing
`AutoRegion::scoped([r]() -> { ... })` and using `@[r]` on both bindings. This is the
"step up" escape hatch.

### Scope derivation

The inferred AutoRegion's scope is the narrowest region consistent with all lifetime
constraints the borrow checker derives from usage. The compiler considers three cases:

**Case 1 — value does not escape the function.** The inferred AutoRegion is scoped to
the current lexical scope. The compiler is free to stack-allocate, arena-allocate, or
use any other AutoRegion strategy (RFC-0073).

```metel
fun process_nodes(specs: &List<Spec>) {
    let nodes = build_nodes(specs);   // inferred AutoRegion: local scope
    analyze(&nodes);
    // nodes dropped here; inferred region ends here
}
```

**Case 2 — value escapes via a return type.** When the returned type contains
region-allocated content with no explicit region, the compiler infers an implicit
AutoRegion parameter and wires it to the return position. The returned value lives in
an AutoRegion scoped to the caller's usage.

```metel
// Programmer writes:
fun make_list(n: I32) -> List<I32> { ... }

// Compiler elaborates to:
fun make_list[auto_r](n: I32) -> @[auto_r] List<I32> { ... }
```

The caller receives a value in a compiler-managed scope whose lifetime is whatever the
caller needs, up to the caller's own AutoRegion. The elaboration is not visible in the
programmer's source; it appears only in error messages when necessary.

**Case 3 — value escapes further.** If the returned value is itself assigned to a
binding that escapes another function, the compiler propagates the inference upward
through the call graph. This terminates at one of:

- A function with an explicit `@[r]` return type — inference stops and the inferred
  region is unified with `r`.
- A function that stores the value into `@[Heap] T` — inference stops and the value
  migrates to the heap (a `move` through a Heap allocation, not a region pointer).
- A fiber boundary — the value must be sendable; `@[auto_r] T` is not sendable, so the
  programmer must explicitly choose `@[Heap] T` or `@[Arc] T`. This is a type error
  that prompts the programmer to be explicit.

### Function signatures with inferred regions

A function with an inferred region in its return type implicitly gains a region
parameter. This implicit parameter participates in the borrow checker identically to an
explicit one; the only difference is that it is not written in source.

When a caller calls such a function, the compiler infers the scope of the implicit
parameter from the caller's usage:

```metel
fun make_pair() -> (Node, Node) {
    (Node { val: 1 }, Node { val: 2 })
}

// Caller:
let pair = make_pair();   // inferred AutoRegion for pair's scope
use(pair.0);
use(pair.1);
// region ends here
```

If the programmer needs to name the implicit region — for example, to express that two
return values share a region — they must write the region parameter explicitly:

```metel
// Explicit: the two nodes are in the same region
fun make_pair[r]() -> (@[r] Node, @[r] Node) {
    (@[r] Node { val: 1 }, @[r] Node { val: 2 })
}
```

### Where inference does not apply

Inference always produces an AutoRegion. It cannot produce:

- **`@[Heap] T`**: The programmer must write `@[Heap]` explicitly when indefinite
  lifetime or sendability is required. The compiler does not escalate an inferred
  AutoRegion to Heap — doing so would silently change the sendability of the value.
- **`@[Rc] T` or `@[Arc] T`**: Shared ownership (RFC-0074) is a deliberate semantic
  commitment — the programmer is saying "multiple owners." The compiler cannot infer
  shared ownership from usage.
- **`@[BumpRegion] T`**: The bump arena is chosen for its performance contract. The
  programmer must choose it explicitly.

If a value's usage requires one of these explicit regions, the programmer gets a
diagnostic:

```
error: cannot infer region for value that must outlive its scope
  --> src/main.mt:8:14
   |
8  |     spawn(fun() { use(node) });
   |                   ^^^^ this value is sent across a fiber boundary
   |
   = note: inferred AutoRegion values are not sendable; use @[Heap] or @[Arc]
```

---

## Interaction with RFC-0065

RFC-0065 fires when `@` is present but the tag is absent and exactly one region is in
scope. RFC-0075 fires when `@` is absent entirely.

The two rules compose: a function may use RFC-0065 elision for some expressions (where a
named region is in scope for context) and RFC-0075 inference for others (where no region
is in scope at all). The programmer does not need to think about which rule applies; both
rules simply eliminate annotation noise at their respective levels.

If exactly one named region is in scope and a bare `T { ... }` expression appears, the
compiler currently must decide between RFC-0065 elision (use the in-scope region) and
RFC-0075 inference (create a new implicit AutoRegion). The rule: **RFC-0065 takes
priority**. A bare `T { ... }` with one in-scope region is treated as `@T { ... }` and
resolved by RFC-0065. Only when no named region is in scope does RFC-0075 inference fire.

This keeps RFC-0065's semantics unchanged: existing code with a single in-scope region
continues to use that region for all `@T` expressions. The new inference layer only adds
behaviour when there is no named region at all.

---

## Interaction with RFC-0073

All inferred regions are AutoRegions — they carry the full AutoRegion semantics from
RFC-0073:

- **Infallible**: `AllocationError = !`. The compiler selects a strategy that succeeds;
  OOM panics rather than returning an error.
- **Compiler latitude**: The compiler may stack-allocate, arena-allocate, heap-allocate,
  inline, or elide allocations freely, subject to RFC-0073's five guarantees.
- **Non-sendable**: `@[auto_r] T` is never sendable, regardless of `T`.
- **Drop completeness and ordering**: Destructors run in reverse-declaration order, as
  if the values had been explicit stack locals.

The difference between an inferred AutoRegion and an explicit `AutoRegion::scoped` is
purely syntactic: the inferred form elides the binding and the scope block; the compiler
derives the scope from usage.

---

## Examples

### Linked list construction

```metel
// Fully annotated (pre-RFC-0075)
fun filter_evens[r](input: &List<I32>) -> @[r] List<I32> {
    let result: @[r] List<I32> = @[r] List::Nil {};
    for n in input {
        if n % 2 == 0 {
            result = @[r] List::Cons { head: n, tail: result };
        }
    }
    result
}

// Region-inferred (RFC-0075)
fun filter_evens(input: &List<I32>) -> List<I32> {
    let result = List::Nil {};
    for n in input {
        if n % 2 == 0 {
            result = List::Cons { head: n, tail: result };
        }
    }
    result
}
```

### AST construction

```metel
// Region-inferred — the programmer writes only the logic
fun parse_expr(tokens: &[Token]) -> Expr {
    match tokens {
        [Token::Num(n), rest @ ..] =>
            Expr::Lit { value: n },
        [Token::Ident(name), Token::LParen, rest @ ..] => {
            let args = parse_args(rest);
            Expr::Call { name, args }
        }
        _ => error("unexpected token"),
    }
}
```

The `Expr::Call` variant's `args` field is region-allocated. The compiler infers an
implicit AutoRegion scoped to the caller's usage of the returned `Expr`.

### Mixed: inferred and explicit

When one allocation needs a different region than the rest, the programmer mixes levels:

```metel
fun build_response(req: &Request) -> @[Heap] Response {
    // response goes to Heap (sendable, indefinite lifetime) — explicit
    let headers = parse_headers(req.headers);   // inferred AutoRegion: local
    let body    = transform(req.body);           // inferred AutoRegion: local
    @[Heap] Response { headers: headers.into_owned(), body }
    // ^ headers.into_owned() migrates headers data to the heap explicitly
}
```

### Struct with inferred region

```metel
// Pre-RFC-0075: region parameter required in struct definition
struct Tree[r] {
    value: I32,
    children: @[r] List<Tree[r]>,
}

// Post-RFC-0075: region elided from struct definition
struct Tree {
    value: I32,
    children: List<Tree>,
}
```

When the programmer instantiates `Tree { ... }`, the compiler infers an AutoRegion for
the `children` field. The struct's region parameter becomes implicit.

---

## Opting back in to explicit regions

Inference is the default; explicitness is always available. Three steps of explicitness:

1. **Write `@` on a specific expression** — RFC-0065 takes over, using the single
   in-scope region. Use this when you are inside an `AutoRegion::scoped` block and want
   to allocate into it.

2. **Write `@[r]` on specific expressions** — fully explicit region for those
   allocations. Other allocations in the same function may still be inferred.

3. **Name the entire scope** — wrap the body in `AutoRegion::scoped([r]() -> { ... })`
   and use `@[r]` throughout. This is the RFC-0073 explicit form; it gives the
   programmer a name for the region that appears in error messages.

There is no "all or nothing" choice. Inference fills in the common case; explicit
annotations override it selectively.

---

## Alternatives considered

### Require all region annotations (status quo)

The explicit style of RFC-0063/0065 is fully specified, unambiguous, and produces clear
error messages. Its cost is that routine code — parsers, data builders, intermediate
computations — carries annotation noise that communicates no useful information because the
compiler would derive the same constraints from usage anyway.

Region inference shifts this annotation burden to cases where it carries signal: explicit
`@[Heap]` communicates sendability, explicit `@[BumpRegion]` communicates a performance
commitment, explicit `@[Rc]`/`@[Arc]` communicates shared ownership. The annotations that
remain are decisions, not bookkeeping.

### Always infer, never require annotations

An extreme inference mode would infer not just AutoRegions but also Heap, Rc, and Arc
allocations. This is how garbage-collected languages work: the programmer never mentions
memory. The cost is that the allocation strategy becomes invisible — the programmer
cannot predict or control whether a value is reference-counted, heap-allocated, or
stack-allocated.

Metel's design goal is to keep allocation decisions explicit when they are decisions. The
present RFC infers only AutoRegions, where the programmer has genuinely no preference.
Explicit regions remain available and remain the right tool when the allocation strategy
matters.

### Compile-time-only inference (no implicit region parameters on functions)

A restricted form of inference could limit itself to values that are fully consumed
within a single function body, rejecting any case where inference would need to produce
an implicit region parameter on a function signature. This avoids the complexity of
inter-function scope derivation at the cost of limiting inference to pure local
variables. Most useful data structures (lists, trees, graphs) require region parameters
because they carry pointers — this restricted form would fail to infer their common
cases. Deferred as a possible stepping stone rather than a final design.

---

## Unresolved questions

1. **Inference across module boundaries.** When a function with an inferred region
   parameter is compiled as part of a library (separate compilation unit), the inferred
   parameter becomes part of the function's interface. Should the library author be
   required to make it explicit in the published signature? Or does the compiler generate
   an ABI-compatible elaboration automatically? Deferred.

2. **Type aliases with inferred regions.** If a type alias `type NodeList = List<Node>`
   is defined without a region parameter, instantiating it with inferred regions creates
   an implicit parameter on the alias. The interaction between type aliases, region
   parameters, and inference needs a precise elaboration pass. Deferred.

3. **Interaction with generic bounds.** A bound `T: SomeAspect` where `T` is a
   region-carrying type raises the question of whether the region parameter is also
   generic, inferred, or fixed. The interaction between the aspect system and inferred
   region parameters is not fully specified. Deferred.

4. **Minimum inference guarantee.** This RFC specifies what the compiler is allowed to
   infer, not what it must. A conservative implementation that always requires explicit
   annotations is conformant. Whether the language should mandate a minimum inference
   depth — e.g., "the compiler must infer single-function local AutoRegions" — is a
   specification question. Deferred.

5. **Error message quality.** Inferred region names like `'auto.42` are legible but may
   be confusing to programmers accustomed to seeing `@[r]` in error messages. The exact
   format of inferred-region diagnostics — how much context to show, whether to suggest
   the explicit form — is an implementation concern left to the compiler. The RFC only
   requires that inferred regions be *nameable* in error output.

6. **Interaction with RFC-0068 (`[own r]` struct regions).** The `[own r]` mechanism in
   struct declarations names an owned region explicitly. Whether the owned region can
   itself be inferred (so that `struct Foo { ... }` with region-allocated fields
   automatically gets an owned AutoRegion) is an open question. Deferred.

---

## References

- RFC-0063 (Region Handles) — `@[r] T`; region allocator interface; sendability rules;
  the explicit form that all inferred regions desugar to.
- RFC-0065 (Region Ergonomics) — `@T` elision (level 1); call-site inference; RFC-0075
  adds level 2 above this layer without changing level 1 semantics.
- RFC-0071 (Ownership and Move Semantics) — move semantics; `Drop` ordering that
  inferred AutoRegions must preserve regardless of backing strategy.
- RFC-0073 (AutoRegion) — the semantic backing for all inferred regions; compiler
  latitude; the five guarantees; sendability.
- RFC-0074 (Shared Ownership) — `Rc`/`Arc`; inference never produces shared ownership;
  the programmer must explicitly choose `@[Rc]`/`@[Arc]`.
