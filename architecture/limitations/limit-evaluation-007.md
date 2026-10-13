---
id: LIMIT-EVALUATION-007
title: "Aspect dispatch on a `{}` residual follows its hidden runtime brand, not its static type"
summary: "A value typed `{}` that was destructured from a named record dispatches to that record's nominal impl; a literal `{}` dispatches to the row-conditional impl."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "v0.14.0 integration rerun (records x dyn / empty residuals), 2026-10-13; skipped fixture `evaluator/records/release_matrix_empty_residual_dispatch_follows_static_type.toml`"
disposition: known
review: null
---

## Limitation

The rest binding of a record pattern has the static type `{}`, but the runtime value keeps
the brand of the record it came from, and brand-exact impl dispatch runs first
(RFC-0121 section 3). Reproduced against `develop` at `9cb4c9de`, with and without
`--move-check`:

```metel
aspect Describe { fun describe(&self) -> String; }
record Point { x: i64, y: i64 }
extend Point: Describe { fun describe(&self) -> String { "point".to_string() } }
extend<row R> { ..R }: Describe where all R: Copy { fun describe(&self) -> String { "copy-row".to_string() } }
fun erase(p: Point) -> {} {
    let { x: _, y: _, ..rest } := p;
    rest
}
fun main() {
    let e: {} := erase(Point { x = 1, y = 2 });
    println(e.describe());    // "point"; a literal `{}` prints "copy-row"
}
```

## Impact

Which impl runs for a `{}` depends on how the value was built, not on its type, so a
function generic over `{ ..R }` can observe a brand its signature does not mention. The
same happens through `dyn Aspect`. Tracked by metel-core#1446 (v0.14.1).

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
