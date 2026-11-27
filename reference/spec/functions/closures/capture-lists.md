---
sidebar_position: 5
---

# Capture lists

A closure that reads an outer binding *captures* it. A function declared in an enclosing block is an
item, not a binding, so a closure may call it without listing it, with or without a capture list. A
**capture list** `[…]` before the parameter list names each captured binding with a specifier:

<!-- doc-example: skip reason="illustrative handler types and helpers are deliberately elided" -->
```metel
fun main() {
    var count := 0;
    let cfg := Config::load();          // non-Copy, read-only in the closure
    let name := "log";                  // non-Copy, moved in

    let handler := [&var count, &cfg, name] var |req: Request| -> Response {
        count += 1;
        route(req, cfg, name)
    };
}
```

- `[&var x]` captures `x` by **exclusive reference**; the body may read and write it.
- `[&x]` captures `x` by **shared reference**; the body may only read it.
- `[x]` captures `x` **by value** — a copy for a `Copy` binding, a **move** for a non-`Copy`
  one (the outer binding is consumed).
- `[x.clone()]` captures an explicit independent copy of a `Clone` binding, leaving the
  outer binding usable.

The list is [**required** whenever the closure references a free non-`Copy` local, or
captures anything by `&` / `&var`](capture-semantics.md#spec.functions.closures.legality-6); it is omissible
only when every free variable is a `Copy` binding captured by value, or there are none.
When present it is [**exhaustive**](capture-semantics.md#spec.functions.closures.legality-7): every free
local binding the body references must appear. Module-level functions, constants, types,
and aspects are not captures and never appear in the list.

A `&var` capture requires the outer binding to be [declared `var`](capture-semantics.md#spec.functions.closures.legality-13),
and a closure literal [cannot reference its own `let` binding](capture-semantics.md#spec.functions.closures.legality-13).
A `[&x]` capture is read-only: [assigning to it, or taking `&var` of it, in the body is a
compile error at the capture](capture-semantics.md#spec.functions.closures.legality-21), not a silent
`mutating` upgrade.

Capturing a free variable of a type parameter `T` follows the
[bounds in scope at the closure's definition](capture-semantics.md#spec.functions.closures.legality-17) —
unbounded `T` is non-`Copy` for every instantiation.

When an inner closure captures a
binding that is itself an *enclosing* closure's capture, [the enclosing closure must list
it, an inner `[s]` cannot move out of an enclosing `[&s]` borrow, and an inner `[s]` that
moves an enclosing-held binding makes the enclosing closure
`once`](capture-semantics.md#spec.functions.closures.legality-22); an inner `&` / `&var` of an enclosing
*by-value* capture is [an interim rejection](capture-semantics.md#spec.functions.closures.legality-11).
