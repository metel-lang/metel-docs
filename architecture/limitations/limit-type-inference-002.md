---
id: LIMIT-TYPE-INFERENCE-002
title: "Field access needs a concrete receiver type at the access site"
summary: "A field access on an unannotated parameter is rejected; add a type annotation."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#1218 limitation analysis; fixture `typechecking/generics/limit_03_field_access_needs_annotation.mtl`"
disposition: known
review: null
---

## Limitation

Inference resolves a field access, method call or tuple-index access by
calling `ctx.solve()` eagerly to learn the receiver's struct name. If the
receiver is an unannotated parameter, no constraint has been emitted yet, so
its type is still a type variable and the access is rejected. Reproduced
against current `develop`:

```metel
struct Point { x: i64, y: i64 }
fun get_x(p) { p.x }
```

```
[T0002] type error: cannot infer struct type for field access; add a type annotation
```

## Impact

Visible to Metel programmers: an unannotated parameter used with `.field` is
rejected, although the Language Spec says annotations are optional for all
bindings, including function parameters. Adding `p: Point` works around it.
The cause is the eager solve, an implementation choice; a constraint-based
field access (deferred until the receiver resolves) would remove the
restriction.

## Affects

- `arch.type-inference.requirement-1`
- `metel-frontend/src/pipeline/type_checking/inference.rs` (eager partial solve)

## Resolution

None yet. The negative fixture `limit_03_field_access_needs_annotation.mtl`
pins the current behaviour and should flip to a positive fixture when the
restriction is lifted.
