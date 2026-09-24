---
id: LIMIT-COHERENCE-001
title: "`extend<record T: {...}> T: Aspect` is accepted, then never applies"
summary: "A blanket aspect impl bounded by a row (`extend<record T: { x: f64, .. }> T: A`) passes coherence, but a call through the bound never dispatches to it; the same class of mistake is rejected outright for the equivalent non-generic form."
scope: "architecture/spec/coherence.md#coherence"
owner: metel-frontend
discovered_by: "metel-core#1241"
disposition: known
review: null
---

## Limitation

Reproduced against current `develop`:

```metel
aspect A { fun f(self) -> i64; }
extend<record T: { x: f64, .. }> T: A { fun f(self) -> i64 { 1 } }
fun main() {
    let r := { x = 1.0, y = 2.0 };
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
a tuple or anonymous record target) and `GAP-TYPES-004` (`extend<row R>` does
not parse at all): here the `extend` uses the ordinary, already-supported
`record T: { .. }` bound and is accepted, then silently does nothing.

## Impact

The `extend` declares an impl that silently has no effect; the program
compiles and then fails at the call site with a diagnostic that does not name
the real cause.

## Affects

- `spec.declarations.aspects.aspect-implementation-coherence.legality-1`
- `metel-frontend/src/pipeline/coherence/mod.rs`

## Resolution

None yet; tracked as `metel-core#1241`. Either the impl is made to apply, or
(matching `metel-core#239`'s precedent) the `extend` is rejected at the
declaration site with a message naming the real cause.
