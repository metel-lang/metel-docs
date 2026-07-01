---
id: rfc-0075
title: "Region Inference — Local AutoRegion"
date: '2026-07-01'
---

> **Status — draft, parked.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), RFC-0073 (AutoRegion). Deferred until the explicit region system is
> implemented and real annotation burden can be measured. The right scope and
> tradeoffs for inference (local-only vs inter-function; Case 1 vs Cases 2/3) are
> speculative without implementation experience.

## Summary

RFC-0065 introduced two annotation levels:

| Form | Elides | Fires when |
|---|---|---|
| `@[r] T` | nothing — fully explicit | always |
| `@T` | the region tag | exactly one named region is in scope |

This RFC adds a third level, scoped strictly to **local values within function bodies**:

| Form | Elides | Fires when |
|---|---|---|
| `T` (no `@`) | the `@` prefix and the region tag | value is local and does not escape the function |

When a local binding requires a region-allocated type and carries no `@` annotation, the
compiler inserts an implicit AutoRegion scoped to the narrowest enclosing block in which
the value is used. The inferred region never propagates beyond the function boundary.

**Function signatures are excluded.** Return types and parameter types that require
region-allocated content continue to require explicit annotation — `@[r] T` or `@T`.
This RFC does not add implicit region parameters to function signatures.

---

## Motivation

The explicit form using RFC-0065 within a function body:

```metel
fun process(nodes: &List<i64>) {
    AutoRegion::scoped([r]() -> {
        let mut result: @[r] List<i64> = @[r] List::Nil {};
        for n in nodes {
            result = @[r] List::Cons { head: *n, tail: result };
        }
        analyze(&result);
    });
}
```

With local inference (this RFC):

```metel
fun process(nodes: &List<i64>) {
    let mut result = List::Nil {};
    for n in nodes {
        result = List::Cons { head: *n, tail: result };
    }
    analyze(&result);
    // result dropped here; inferred AutoRegion ends here
}
```

The list is built, used, and dropped within the function body. The compiler infers an
AutoRegion for it. The function's signature is unchanged — no implicit region parameter
is added to `process`.

The benefit is reduced annotation noise for temporary data structures that live and die
within a single function. The constraint is sharp: if `result` were returned or moved
into an outer binding, the compiler would reject the program and direct the programmer
to add an explicit region parameter to the function signature.

### What explicit annotations are still for

Explicit regions remain the right tool whenever the allocation decision is meaningful:

- `@[r]` when the region is named in the function's bracket channel and the caller
  controls the allocation scope.
- `@[Heap]` when the value must outlive the function or cross a fiber boundary.
- `@[Rc]`/`Arc::new()` when shared ownership is required.
- `@[BumpRegion]` when the bump-arena performance contract is the point.

Local inference covers only the case where the programmer has no opinion on the
allocation strategy and the value is entirely local.

---

## Design

### Where level-2 elision fires

Level-2 elision fires on a local binding when **all** of the following hold:

1. The expression produces a value of a region-carrying type.
2. No `@` prefix is present on the expression.
3. No named region is in lexical scope — otherwise RFC-0065 level-1 elision fires
   instead.
4. The value does not escape the current function: it is not returned, not moved into
   a non-local binding, and not passed to a position whose type requires a specific
   non-AutoRegion region.

If any condition fails, the compiler requires an explicit annotation.

### Inferred AutoRegion scope

The inferred AutoRegion is scoped to the narrowest enclosing lexical block in which the
value is used — always within the current function body. It follows RFC-0073 semantics:
the compiler chooses any allocation strategy (stack, arena, heap, or combinations), and
the five RFC-0073 guarantees hold regardless of strategy.

Drop ordering is preserved: destructors run in reverse-declaration order, as if the
inferred values were explicit local bindings with `AutoRegion::scoped`.

### Function signatures are always explicit

Return types and parameter types are never inferred. A function that takes or returns
a region-carrying type must declare a bracket parameter:

```metel
// correct — explicit region parameter
fun collect[r](input: &List<i64>) -> @[r] List<i64> { ... }

// error — return type requires a region
fun collect(input: &List<i64>) -> List<i64> { ... }
//          List<i64> in return position requires @[r] — infer is not applicable here
```

This rule ensures that function signatures remain honest contracts. A caller can always
read a function's bracket parameters to understand the lifetime relationships of its
inputs and outputs.

### Error when escape is attempted

If a value with an inferred region is used in a position that would require it to
escape the function, the compiler reports a directed error:

```
error: region-allocated value cannot escape the function without an explicit region
  --> src/main.mt:8:5
   |
4  |     let result = List::Nil {};
   |                  ---------- value allocated in inferred local AutoRegion
8  |     result
   |     ^^^^^^ returned here, but inferred AutoRegion ends when function returns
   |
   = note: to return a region-allocated value, add an explicit region parameter:
           fun collect[r](input: &List<i64>) -> @[r] List<i64>
```

### Inferred region names in diagnostics

Each inferred AutoRegion receives a compiler-generated name (e.g., `'auto.4`) derived
from the source location. This name appears only in error messages — the programmer
never writes it. When a clearer name is needed, the programmer promotes the inferred
region to an explicit `AutoRegion::scoped([r]() -> { ... })` and uses `@[r]` on the
relevant bindings.

---

## Interaction with RFC-0065

RFC-0065 fires when `@` is present but the tag is absent and exactly one named region
is in scope. RFC-0075 fires when `@` is absent entirely and no named region is in scope.

If one named region is in scope and a bare `T { ... }` expression appears, RFC-0065
takes priority — the expression is treated as `@T { ... }` and resolved by RFC-0065.
RFC-0075 inference fires only when no named region is in scope at all.

The two levels compose without conflict: a function may use RFC-0065 elision for some
expressions (within an explicit `AutoRegion::scoped` block) and RFC-0075 inference for
others (outside any named region). RFC-0073 backing semantics apply to both.

---

## Interaction with RFC-0073

All inferred local regions are AutoRegions. RFC-0073's five guarantees hold:
soundness, drop completeness, drop ordering, move-out safety, and observational
equivalence. The inferred region is semantically identical to an explicit
`AutoRegion::scoped` block whose scope is the narrowest block containing all uses of
the value.

---

## Examples

### Temporary accumulator

```metel
fun sum_evens(input: &List<i64>) -> i64 {
    let mut evens = List::Nil {};     // inferred AutoRegion: local
    for n in input {
        if *n % 2 == 0 {
            evens = List::Cons { head: *n, tail: evens };
        }
    }
    fold_left(&evens, 0, |acc, n| acc + n)
    // evens dropped here; inferred region ends
}
```

The list is temporary — it is built, consumed by `fold_left`, and dropped within the
function. No annotation is needed.

### Temporary AST node

```metel
fun emit_binop(op: Op, lhs: Expr, rhs: Expr) -> Bytecode {
    let node = BinopNode { op, lhs, rhs };   // inferred AutoRegion
    node.emit()
    // node dropped after emit() returns
}
```

### Mixed: inferred and explicit

When one allocation needs a specific region and another is purely local, the programmer
mixes levels:

```metel
fun build_response[r](req: &Request) -> @[r] Response {
    let headers = parse_headers(req.headers);   // inferred AutoRegion: local
    let body    = transform(req.body);           // inferred AutoRegion: local
    @[r] Response {
        headers: headers.to_string(),   // headers content copied into r
        body,
    }
    // headers, body dropped here; inferred regions end
}
```

The returned `Response` lives in the caller's explicit region `r`. The intermediate
`headers` and `body` values are local temporaries in inferred regions.

### Escape attempt — error case

```metel
fun bad_collect(input: &List<i64>) -> List<i64> {
    let result = List::Nil {};   // inferred AutoRegion
    // ...
    result   // error: cannot return value from inferred AutoRegion
}
```

The fix: add an explicit region parameter.

```metel
fun good_collect[r](input: &List<i64>) -> @[r] List<i64> {
    let mut result: @[r] List<i64> = @[r] List::Nil {};
    // ...
    result   // ok: result lives in caller-supplied region r
}
```

---

## Alternatives considered

### Inter-function inference (withdrawn)

An earlier version of this RFC included inference that propagated across function
boundaries. A function returning `List<i64>` with no annotation would gain an implicit
region parameter, and the compiler would wire it to the caller's AutoRegion.

This was withdrawn for three reasons:

**Hidden lifetime contracts.** The caller cannot see that the returned value has a
scoped lifetime. The contract — that the returned data lives in a compiler-managed
AutoRegion that may be dropped when no longer needed — is invisible in the source.

**Stack overflow risk for recursive types.** AutoRegion may stack-allocate. A caller
writing `let big = build_big_list(1_000_000)` could inadvertently stack-allocate one
million linked list nodes. Nothing in the source signals this risk because the region
decision is hidden inside the function.

**Invisible implicit function parameters.** Adding implicit region parameters to
function signatures changes their ABI without any visible indication to the programmer.
Two functions with identical source signatures could have different compiled interfaces
depending on whether the compiler inferred a region parameter. This violates the
principle that the source is the specification.

The scoped-to-body rule eliminates all three problems: the programmer sees every region
that crosses a function boundary, the function's signature is what it looks like, and
large allocations in functions with explicit `@[Heap]` or `@[r]` return types are
clearly marked.

### Full explicit annotations (status quo)

RFC-0063 + RFC-0065 already provide good ergonomics with `@T` elision when one region
is in scope. The additional level introduced here targets the case where no region is
in scope at all — a function that builds a temporary structure purely for local use.
Without this RFC, that function must either wrap the body in `AutoRegion::scoped` or
accept a region parameter it would not otherwise need. Both are annotation noise. The
restricted inference in this RFC removes that noise without hiding any interface
contracts.

---

## Unresolved Questions

1. **Interaction with generic bounds.** When a local binding has type `T` where
   `T: SomeAspect` and `T` is region-carrying, the interaction between the inferred
   AutoRegion and the aspect bound is deferred to the type inference RFC.

2. **Interaction with RFC-0068 (`[own r]` struct regions).** Whether the owned region
   of a struct declared `[own r]` can be inferred when the struct is a purely local
   binding is deferred to a follow-on RFC.

3. **Standalone type aliases.** If a type alias `type NodeList = List<Node>` is used
   in a local binding without a region parameter, the elaboration is deferred to the
   standalone type alias RFC (RFC-0082 §8).

---

## References

- RFC-0063 (Region Handles) — `@[r] T`; region allocator interface; the explicit form
  all inferred regions desugar to.
- RFC-0065 (Region Ergonomics) — `@T` elision (level 1); RFC-0075 adds level 2 above
  this layer without changing level 1 semantics.
- RFC-0071 (Ownership and Move Semantics) — drop ordering that inferred AutoRegions
  must preserve.
- RFC-0073 (AutoRegion) — backing semantics for all inferred regions; the five
  guarantees; compiler latitude.
- RFC-0074 (Shared Ownership) — inference never produces `Rc`/`Arc`; the programmer
  must explicitly choose shared ownership.
