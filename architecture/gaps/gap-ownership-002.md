---
id: GAP-OWNERSHIP-002
title: "A deeper move does not narrow the enclosing value's row"
summary: "Moving `root.a` narrows `root`'s type, but moving `root.a.b` does not: a record-typed field moves as a unit, so the type checker still treats `root` as whole."
scope: "reference/spec/ownership.md#spec.ownership.narrowing.legality-1"
owner: language
discovered_by: "maintainer note on `flow_state.rs` `moved_shallow_projections`; checked against reference/spec/ownership.md (Narrowing)"
disposition: planned
review: null
---

## Gap

Row narrowing (RFC-0117 for anonymous records, RFC-0137 for structs) narrows a
binding's type when a field is moved directly out of it: after `let x := o.a;`,
`o : Outer.{ d }`. Only a **depth-1** projection narrows. The type checker reads
`moved_shallow_projections`, which keeps just moves whose place has exactly one
projection, and `record_move_of_place` returns early for anything deeper. The
Language Spec states the boundary: "A record-typed **field** is moved as a
**unit** — a residual's row never carries a *narrower* type for a field it still
holds; narrowing a field of a field in place is RFC-0150's."

Reproduced against current `develop`:

```metel
struct Inner { b: String, c: String }
struct Outer { a: Inner, d: String }
fun take(o: Outer) -> i64 { 1 }
fun main() {
    let o := Outer { a = Inner { b = "b", c = "c" }, d = "d" };
    let x := o.a.b;      // deeper move
    take(o);             // whole use after the partial move
}
```

Without flags this type-checks (exit 0). With `--move-check` it is rejected
(`T0019 use of partially moved value o`). For contrast, a depth-1 move
(`let x := o.a;` then `take(o)`) is always a type error: "a partially-moved
`Outer` (now `Outer.{ d }`) cannot be used where the whole `Outer` is required".

## Impact

After a deeper partial move the value is still typed as whole, so passing it (or
its enclosing field) where the whole type is required is not caught by ordinary
type checking; only the opt-in move checker reports it. That mirrors the rest of
the ownership model, which is enforced only under `--move-check`, but it means
the always-on narrowing does not cover nested paths.

## Affects

- `spec.ownership.narrowing.legality-1`
- `RFC-0150`

## Resolution

Planned: RFC-0150 (Nested Row Narrowing, `1-under-review`) is tracked as
metel-core#900, milestone v0.14.1. When it is accepted and implemented, a move
of `root.a.b` narrows the row of `a` inside `root`'s residual, and this gap
closes against that RFC.
