---
sidebar_position: 6
---

# Records and Rows

## Records and Rows at a Glance

This section is a map; the rules are stated where each topic is specified, linked below.

Every product type in Metel has a **row**: the set of its labelled fields, each with a
type. An [anonymous record](#anonymous-records) *is* its row. A `struct` or `record`
declaration is a **brand** (its name, fixed at declaration) paired with a row. Rows are
what generic code can talk about structurally, in three increasingly general ways:

| To say | Write | Specified in |
|---|---|---|
| "a record with *at least* these fields" | `<record T: .{ .x: f64, .. }>` | [Row bounds](../generics/row-bounds.md) |
| "a record with *no* such field" | `<record T: !{ token }>` | [Row bounds](../generics/row-bounds.md) |
| "…and name *the rest*, so a signature can carry it" | `<record R>` with `.{ .x: f64, ..R }` | [Open rows](../generics/open-rows.md) |
| "…the rest is this field plus a remainder" | `where R = .{ .token: Token, ..Rest }` | [Open rows](../generics/open-rows.md) |
| "every field's *type* satisfies an aspect" | `where ..R: Copy` | [Field-wise row constraints](../generics/field-wise-row-constraints.md) |
| "this impl applies to every record of this shape" | `extend<record R: { x, .. }> .{ ..R }: A` | [Implementing an aspect for a record](../generics/implementing-an-aspect-for-a-record.md) |

Which types a row bound or row-conditional impl can match is decided by the declaration
kind, not by the fields written:

| | row visible to bounds and row-conditional impls | inherent methods |
|---|---|---|
| anonymous record | yes | no |
| `record` ([Records](../../declarations/records.md)) | yes | yes |
| `struct` | **no** | yes |
| `enum` | **no** | yes |

Narrowing connects these to ownership. Moving a field out of a value leaves a value with
a smaller row ([Narrowing](../../ownership/partial-moves/narrowing.md)); a row-conditional impl or bound is
checked against that *current* row. Passing a wider record by value to a parameter that
names only some of its fields is *width subtyping*, and is allowed only when no
non-`Copy` field would be forgotten ([Open rows](../generics/open-rows.md)).

The example below uses each piece once:

```metel
record Session<record R> { id: i64, data: .{ ..R } }

// A bound: any record carrying `user: i64`.
fun user_of<record T: .{ .user: i64, .. }>(e: T) -> i64 { e.user }

// A row variable: carry the rest through unchanged.
fun keep<record R>(p: .{ .user: i64, ..R }) -> .{ .user: i64, ..R } { p }

// Row-conditional methods: which exist depends on the session's row.
extend<record R: .{ .token: String, .. }> Session<..R> {
    fun send(self) -> i64 { self.id * 10 }
}
extend<record R: !{ .token }> Session<..R> {
    fun login(self) -> i64 { self.id }
}

fun main() {
    assert(user_of(.{ .user = 7, .kind = 1 }) == 7);
    assert(keep(.{ .user = 1, .extra = 2 }).extra == 2);

    let anon: Session<.{ .user: i64 }> := Session(id = 2, data = .{ .user = 1 });
    let authed: Session<.{ .token: String }> := Session(id = 1, data = .{ .token = "t" });
    assert(anon.login() == 2);
    assert(authed.send() == 10);
}
```

## Anonymous Records

A record is a product type whose components are *labelled*, where a tuple's are positional.
It is written with a dot before the braces, `.{ ... }`, and no keyword:

```metel
.{ .x: f64, .y: f64 }      // the type
.{ .x = 1.0, .y = 2.0 }    // a value of it
```

Field declarations classify and take `:`; field initializers define and take `=` — the same
distinction `let x: i64 = 1` already draws.

**A record type is exact.** `.{ .x: f64 }` is inhabited only by records with that row and
nothing else; a value of `.{ .x: f64, .y: f64 }` is *not* a value of `.{ .x: f64 }`. Records are
not implicitly widened or narrowed.

**Records are structurally typed.** [Two records with the same labels and field types are the
same type, wherever they were written](projection.md#spec.types.anonymous-records.dynamics-1). A record has no declaration site and no name.
**Field order does not matter:** `.{ .x: i64, .y: i64 }` and `.{ .y: i64, .x: i64 }` are the same
type, and `.{ .x = 1, .y = 2 }` and `.{ .y = 2, .x = 1 }` are indistinguishable — each is usable
wherever the other is. A record is a set of labelled fields, not an ordered one. Repeating a
label in one record (`.{ .x: i64, .x: f64 }`) is an error.

(Indistinguishable is a statement about the type, not about `==`, which no compound type —
record, struct, tuple, or array — supports.)

When a local variable has the same name as a field, the `= value` part may be omitted, as in
a struct literal:

```metel
fun main() {
    let x := 1.0;
    let y := 2.0;
    let p := .{ .x, .y };       // { x: f64, y: f64 }
    println("${p.x}");
}
```

A record opens with `.{`, so it is never mistaken for a block: `.{ .x }` is always a record, `.{}` is the empty record, and a bare
`{ x }` or `{}` is a block. A function, closure or loop body is a block, so a record returned from one is written inside it, `{ .{ .x = 1 } }`;
where an expression arm is allowed, as in `if`/`else` and `match`, the record needs no parentheses.

### Where records may be used

Records are ordinary values: they may appear as parameters, returns, `let` bindings, and
struct or enum fields; they may be pattern-matched, used as generic arguments, and borrowed
(`&{ .x: f64 }`) exactly as a struct is. `Send` and `Sync` extend
to them by the same field-composition rule used for structs.

Three things a record cannot do, all for the same underlying reason — it has no nominal
owner:

- **No inherent methods.** Two unrelated modules could otherwise write conflicting methods
  for the same shape with no principled way to choose between them.
- **No implementations of a non-local aspect**, by the other direction of that rule. An
  aspect local to the current module may be implemented for a record: for one concrete
  row, or for every row of a given shape ([Implementing an aspect for a
  record](../generics/implementing-an-aspect-for-a-record.md)).
- **No custom `Drop`.** `Drop` is a standard-library aspect and never local to ordinary
  user code, so teardown logic belongs to nominal types only.

Arrays are the other structural target: `extend<T> [T]: MyAspect { … }` is supported, per
the orphan-rule carve-out for structural type constructors — see
[Declarations — Structural Aspect Bounds](../../declarations/aspects/structural-bounds.md).
Auto-derived aspects are unaffected.
