---
id: LIMIT-EVALUATION-007
title: "A record rest pattern's remainder kept its record brand at runtime, so aspect dispatch ignored its static type"
summary: "The remainder bound by `..rest` carried the scrutinee's runtime brand, so dispatch picked the nominal impl although the spec says the remainder is anonymous."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "v0.14.0 integration rerun (records x dyn / empty residuals), 2026-10-13"
disposition: resolved
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

## Resolution

Fixed 2026-10-13, metel-core#1446 (v0.14.1). The evaluator built the remainder of a record
rest pattern with the scrutinee's `type_id` (`evaluator/pattern/mod.rs`); it now builds it
with none, matching `spec.expressions` "Record rest patterns" ("the remainder loses the
nominal brand"). The regression fixture
`evaluator/records/release_matrix_empty_residual_dispatch_follows_static_type` is unskipped
and also covers a non-empty remainder and `dyn Aspect` dispatch.
