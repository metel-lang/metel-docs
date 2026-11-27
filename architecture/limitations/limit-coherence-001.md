---
id: LIMIT-COHERENCE-001
title: "`extend<record T: .{...}> T: Aspect` is accepted, then never applies"
summary: "A blanket aspect impl bounded by a row (`extend<record T: .{ .x: f64, .. }> T: A`) passes coherence, but a call through the bound never dispatches to it; the same class of mistake is rejected outright for the equivalent non-generic form."
scope: "architecture/spec/coherence.md#coherence"
owner: metel-frontend
discovered_by: "metel-core#1241"
disposition: resolved
review: null
---

## Limitation

Reproduced against current `develop`:

```metel
aspect A { fun f(self) -> i64; }
extend<record T: .{ .x: f64, .. }> T: A { fun f(self) -> i64 { 1 } }
fun main() {
    let r := .{ .x = 1.0, .y = 2.0 };
    println(r.f().to_string());
}
```

Coherence accepts the `extend`. The call fails: `[T0002] type error: cannot
infer receiver type for method call; add a type annotation` — the impl is
never found. The direct, non-generic form of the same mistake
(`extend { x: f64 }: A { … }`) is rejected outright since `metel-core#239`,
with a clear message ("cannot `extend` an anonymous record type"). This
generic, row-bounded form slips through the same class of check.

This is a different case from `GAP-DECLARATIONS-001` (no local aspect impl for
a tuple or anonymous record target) and `GAP-TYPES-004` (`extend<record R>` does
not parse at all): here the `extend` uses the ordinary, already-supported
`record T: .{ .. }` bound and is accepted, then silently does nothing.

## Impact

The `extend` declares an impl that silently has no effect; the program
compiles and then fails at the call site with a diagnostic that does not name
the real cause.

## Affects

- `spec.declarations.aspects.aspect-implementation-coherence.legality-1`
- `metel-frontend/src/pipeline/coherence/mod.rs`

## Resolution

Resolved by metel-core#1343 (`26c7a330`): `extend<record T: .{ .. }> T: A` is rejected at the declaration with `T0001`, which names the spelling that applies, `extend<row R: { x: f64, .. }> { ..R }: A` (record-target impls, metel-core#1336). Evidence: `typechecking/aspects/extend_record_kinded_type_parameter_is_t0001` and `typechecking/aspects/extend_row_target_replaces_record_kinded_parameter`. The reproduction above now fails with `T0001` at the `extend`, as the second option under Resolution proposed.
