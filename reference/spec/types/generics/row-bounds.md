---
sidebar_position: 14
---

# Row Bounds

## Row bounds

A bound written as a row accepts any type carrying at least the listed fields:

```metel
fun squared_magnitude<record T: .{ .x: f64, .y: f64, .. }>(p: T) -> f64 {
    p.x * p.x + p.y * p.y
}
```

**The trailing `..` is load-bearing.** It stands for "and a rest I am not naming," and its
presence is what makes the bound *open*:

```metel
fun g<record T: .{ .x: f64 }>(p: T)        // closed: T's row is exactly `x`
fun h<record T: .{ .x: f64, .. }>(p: T)    // open:  T has at least `x`
```

A record pattern's own trailing `..` reads the bound's listed fields the same way
[field access](implementing-an-aspect-for-a-record.md#spec.types.generics.row-bounds.legality-6) does, and — unlike field access
— can discard the rest of an open bound's unlisted fields rather than being unable to name
them at all:

```metel
fun describe<record T: .{ .x: f64, .. }>(p: T) -> String {
    match (p) {
        .{ .x, .. } => "x is ${x}, plus whatever else the caller passed",
    }
}
```

**The `..` is required to match an open bound at all** — its full field set isn't known
here, so a pattern that doesn't end in `..` can never be exhaustive:

```metel
fun bad<record T: .{ .x: f64, .. }>(p: T) -> f64 {
    match (p) {
        .{ .x } => x,   // error: open bound's field set isn't known here; add `..`
    }
}
```

A closed bound's fields *are* fully known, so `..` there is optional sugar rather than a
requirement — a pattern matching a closed bound must still name every field the bound
lists unless it uses `..`:

```metel
fun get_x<record T: .{ .x: f64, .y: f64 }>(p: T) -> f64 {
    match (p) {
        .{ .x, .y } => x,       // OK: every field of the closed bound is named
        // { x } => x,       // error: `y` isn't named and there's no `..`
    }
}
```

Naming a field the bound doesn't list is still rejected, `..` or not — the pattern's rest
form discards *unnamed* fields, not fields the bound never promised are there:

```metel
fun bad2<record T: .{ .x: f64, .. }>(p: T) -> f64 {
    match (p) {
        .{ .x, .z, .. } => x,   // error: no field `z` on the bound
    }
}
```

**A field may omit its type** to constrain the label only — `{ x }` means "carries an `x`,
whatever its type":

```metel
fun f<record T: { x, .. }>(p: T)          // has an `x` of some type
fun g<record T: .{ .x, .y: f64, .. }>(p: T)  // any-typed `x`, `f64` `y`
```

Negation reuses the `!` that bounds already accept, and is the **complement** of the positive
bound — just as `!Copy` means "does not implement `Copy`". It takes no `..`, since absence
has no rest to quantify over:

```metel
fun send<record T: !{ token }>(t: T) -> i64 { … }        // carries no `token` at all
fun tag<record T: !{ id: String }>(t: T) -> i64 { … }    // no `String`-typed `id`
```

Note the second form is satisfied by a record whose `id` is an `i64` — it does not have a
`String` `id`. Write `!{ id }` for "no `id` of any type".

**[A row bound is satisfied by a record, not by a nominal struct.](implementing-an-aspect-for-a-record.md#spec.types.generics.row-bounds.legality-4)** The `record` marker on the
type parameter says so at the declaration; a bare `<T: { … }>` is an error.

The marker may be written at the parameter or in a `where` clause — the two are equivalent,
and a parameter is record-kinded if either one carries it:

```metel
fun f<record T: .{ .x: f64, .. }>(p: T) -> f64
fun g<T>(p: T) -> f64 where record T: .{ .x: f64, .. }
```

**The row bound is optional.** `<record T>` on its own means "any record, whatever its
fields" — the only way to write that, since a bound of `.{ .. }` alone is not accepted:

```metel
fun labels<record T>(x: T) -> [Symbol]   // any record; no constraint on its fields
```

```metel
squared_magnitude(.{ .x = 3.0, .y = 4.0 });   // a record — satisfies the bound
squared_magnitude(some_point);             // a struct — does not
```

Nominal structs do not satisfy row bounds.

## Why row capability is opt-in

A nominal type's API is what it **declares**. An anonymous record's API is what it
**contains**.

Once a type satisfies row bounds, its field names and types are part of its public interface,
whether the author intended that or not. Renaming a field breaks every caller who wrote a
bound mentioning it; adding one can make the type accidentally satisfy a bound its author
never heard of. On a `struct`, a field rename is an internal change.

That is why structural capability is opt-in rather than automatic:

| | encapsulation | structural flexibility |
|---|---|---|
| `struct` | layout is private; the API is what you declare | none |

Most types want the first. A value whose *shape* is genuinely the contract — a coordinate
pair or a configuration fragment — can use an anonymous record.

## What satisfies which bound

Both bound kinds are opted into; they differ only in *granularity*. An **aspect** bound is
opted into per aspect, by writing an implementation. A **row** bound is opted into per type,
by choosing the `record` kind. Nothing is implicit in either direction.

Every struct is represented internally as `(brand, row)` (see [Ownership —
Narrowing](../../ownership/partial-moves/narrowing.md)). The table's "no" is a visibility gate, not the absence
of a row: a plain struct's row is never *visible* to row-bound satisfaction, regardless of
narrowing or projection — including at full width, where its content is identical to a
same-shaped record's. This preserves the same observable outcome as before, expressed on the
branded-row mechanism itself.

| | non-local aspect (`Display`) | local aspect | row bound |
|---|---|---|---|
| `struct` | yes, with an impl | yes, with an impl | **no** |
| `enum` | yes, with an impl | yes, with an impl | **no** — sums, not products |
| anonymous record | **no** — see below | yes, with an impl | yes |

An anonymous record has no owning module, so the orphan rule permits an implementation only
for an aspect local to the implementing module. Every standard-library aspect is non-local,
which means a program cannot implement one for an anonymous record, and `println("${r}")` works on one only through the standard
library's own row impls (`Display`, `Clone` and `Copy` for every record of such fields, see [Implementing an aspect for a
record](implementing-an-aspect-for-a-record.md)), printed as the [source form of the record](../records/projection.md#spec.types.anonymous-records.dynamics-3).
Auto-derived aspects are unaffected — `Send` and `Sync` are computed from field composition
rather than declared.
