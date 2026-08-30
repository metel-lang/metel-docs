# Type System

Metel is statically and strongly typed. Types are checked at compile time. There are no implicit conversions.

## Primitive Types

| Type     | Description               | Example   |
|----------|---------------------------|-----------|
| `i64`    | 64-bit signed integer | `42` |
| `f64`    | 64-bit floating point | `3.14` |
| `boolean`| Boolean                   | `true`    |
| `String` | UTF-8 string              | `"hello"` |
| `Char`   | Unicode scalar value      | `'a'`     |
| `()`     | Unit — represents no value | `()`     |

The unit type `()` is only written explicitly when needed as a type parameter (e.g. `Result<(), Error>`). Functions that return nothing omit the `->` annotation entirely.

## Sized Numeric Types

> **Availability:** Since v0.8.0.

Metel provides exact-width numeric types for low-level and systems programming. `i64` and `f64` are the default integer and floating-point types in ordinary code.

**Signed integers:**

| Type  | Width  |
|-------|--------|
| `i8`  | 8-bit  |
| `i16` | 16-bit |
| `i32` | 32-bit |
| `i64` | 64-bit |

**Unsigned integers:**

| Type  | Width  |
|-------|--------|
| `u8`  | 8-bit  |
| `u16` | 16-bit |
| `u32` | 32-bit |
| `u64` | 64-bit |

**Floats:**

| Type  | Width  |
|-------|--------|
| `f32` | 32-bit IEEE 754 |
| `f64` | 64-bit IEEE 754 |

Sized literals use a suffix: `42i32`, `3.14f32`, `255u8`. All casts between sized numeric types are explicit (`as`). Array indices must be `u64`; indexing with an `i64` requires an explicit `as u64` cast.

**Unsuffixed literals are polymorphic.** When the expected type is known from context (annotation, function parameter, struct field, return type, or the other operand in arithmetic/comparison), an unsuffixed numeric literal [adopts that type automatically](#spec.types.sized-numeric-types.legality-3). When no context is available, the literal defaults to `i64` (integer) or `f64` (float).

```metel
let a: i32 = 10;          // 10 is i32
let b: u8  = 255;         // 255 is u8
let c: f32 = 1.5;         // 1.5 is f32

fun scale(x: f32, factor: f32) -> f32 { x * factor }
let r = scale(2.0, 3.0);  // both literals are f32

let x: i32 = 10i32;
let y = x + 5;            // 5 adopts i32 from x; y is i32
```

This also applies to `var` reassignment — the right-hand side of `m = expr` adopts `m`'s declared type:

```metel
var count: i32 = 0;
count = 99;               // 99 is i32
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.sized-numeric-types.legality-1}

The exact-width numeric primitive types are `i8`, `i16`, `i32`, `i64`, `u8`, `u16`,
`u32`, `u64`, `f32`, and `f64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [82_sized_numeric_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/82_sized_numeric_types.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.sized-numeric-types.legality-2}

Conversion between numeric types is written with an explicit `as` cast.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [82_sized_numeric_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/82_sized_numeric_types.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.sized-numeric-types.legality-3}

An unsuffixed numeric literal adopts the numeric type supplied by context; without
context, integer literals default to `i64` and floating-point literals to `f64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [04_polymorphic_literals.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/literals/04_polymorphic_literals.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.sized-numeric-types.dynamics-1}

Integer overflow panics, unconditionally — Metel has no debug/release build-mode
distinction of its own (the interpreter takes no such flag), so this applies the
same way regardless of how the interpreter binary happens to have been compiled.
Floating-point overflow follows IEEE 754 behavior.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [11_overflow_panics.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/arithmetic/11_overflow_panics.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Char

> **Availability:** Since v0.8.0.

`Char` represents a single Unicode scalar value. Character literals use single quotes: `'a'`, `'\n'`, `'\u{1F600}'`.

```metel
fun main() {
    let c: Char = 'a';
    let code: u32 = u32::from(c);
    let back: Char = Char::from(code);
}
```

`Char` is not `u32` and not a string — no implicit coercions exist. Use
[`u32::from(c)`](runtime.md#spec.runtime.char-methods.dynamics-1) to get the Unicode
scalar value and [`Char::from(n)`](runtime.md#spec.runtime.char-methods.dynamics-1) to
construct from a code point; `Char::from` raises a runtime error if `n` is not a valid
Unicode scalar value.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.char.legality-1}

`Char` is a distinct Unicode-scalar type, not an alias for `u32` or `u8`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [81_char.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/81_char.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Type Inference

Types are inferred using the Hindley-Milner algorithm with let-polymorphism. Annotations are optional for all bindings, including function parameters and return types. They may be written explicitly for documentation or to restrict a binding to a less general type.

Annotations are required only where there is no expression to infer from:
- Struct and enum field types
- Aspect method signatures

Every named type in an annotation must resolve in the annotation's declaring scope,
including names nested inside arrays, tuples, function types, and record fields. This is
checked when the declaration is type-checked, even if no value ever reaches the
annotation. A generic parameter in scope and `Self` where it is permitted resolve as
types; every other unknown name is error `T0003`.

```metel
fun add_annotated(a: i64, b: i64) -> i64 { a + b }
fun add_inferred(a, b) { a + b }

fun main() -> i64 {
    let x = 42;           // inferred: i64
    let name = "Vlad";    // inferred: String
    let y: f64 = 3.14;  // explicit annotation (optional here)
    let total = add_annotated(x, 1) + add_inferred(2, 3);
    if (name == "Vlad") { total + (y as i64) } else { 0 }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.type-inference.legality-1}

An expression in `return` position is typechecked against the enclosing function or
method's declared return type, which supplies its expected type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0019](../../rfcs/4-implemented/rfc-0019-return-context-type-propagation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage7_01_return_type_propagation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_01_return_type_propagation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-inference.legality-2}

An expression in `break` position is typechecked against its enclosing `loop`'s value
type, independently of the enclosing function's return type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0019](../../rfcs/4-implemented/rfc-0019-return-context-type-propagation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage7_01_return_type_propagation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_01_return_type_propagation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Tuples

Tuples are lightweight anonymous product types.

```metel
fun main() -> i64 {
    let coord: (i64, i64) = (10, 20);
    let triple: (String, i64, boolean) = ("yes", 42, true);
    return coord.0 + triple.1;
}
```

Positional field access [uses zero-based selectors `.0`, `.1`, etc.](#spec.types.tuples.legality-1):

```metel
fun main() -> i64 {
    let coord: (i64, i64) = (10, 20);
    let x = coord.0;
    let y = coord.1;
    return x + y;
}
```

`()` is the zero-element tuple (unit type).

Tuples can be destructured in `match`:

```metel
fun main() -> i64 {
    let coord: (i64, i64) = (10, 0);
    match coord {
        (0, y) => y,
        (x, 0) => x,
        (x, y) => x + y,
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.tuples.legality-1}

A tuple's elements are addressed by zero-based positional selectors. A selector is valid
only for an element in the tuple's declared arity.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [09_tuple.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/09_tuple.mtl), [neg_09_tuple_oob.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/neg_09_tuple_oob.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Anonymous Records

> **Availability:** Since v0.12.0.

A record is a product type whose components are *labelled*, where a tuple's are positional.
It is written in bare braces, with no keyword:

```metel
{ x: f64, y: f64 }      // the type
{ x = 1.0, y = 2.0 }    // a value of it
```

Field declarations classify and take `:`; field initializers define and take `=` — the same
distinction `let x: i64 = 1` already draws.

**A record type is exact.** `{ x: f64 }` is inhabited only by records with that row and
nothing else; a value of `{ x: f64, y: f64 }` is *not* a value of `{ x: f64 }`. Records are
not implicitly widened or narrowed.

**Records are structurally typed.** Two records with the same labels and field types are the
same type, wherever they were written. A record has no declaration site and no name.
**Field order does not matter:** `{ x: i64, y: i64 }` and `{ y: i64, x: i64 }` are the same
type, and `{ x = 1, y = 2 }` and `{ y = 2, x = 1 }` are indistinguishable — each is usable
wherever the other is. A record is a set of labelled fields, not an ordered one. Repeating a
label in one record (`{ x: i64, x: f64 }`) is an error.

(Indistinguishable is a statement about the type, not about `==`, which no compound type —
record, struct, tuple, or array — supports.)

When a local variable has the same name as a field, the `= value` part may be omitted, as in
a struct literal:

```metel
fun main() {
    let x = 1.0;
    let y = 2.0;
    let p = { x, y };       // { x: f64, y: f64 }
    println("${p.x}");
}
```

Punning, and single-field record literals generally, are read as records only in positions
that expect an expression — a `let`/`var` or field initializer, a call argument, an array
element. In a position that also admits a block — an `if`/`else` or `match` arm, a
function, closure, or loop body — a bare `{ x }` is a **block** whose result is `x`, and
`{ x = 1 }` is a block whose result is the assignment. Write the record in parentheses to
force it: `({ x })`. A multi-field literal needs no parentheses, as `{ x = 1, y = 2 }`
cannot be a block.

### Where records may be used

Records are ordinary values: they may appear as parameters, returns, `let` bindings, and
struct or enum fields; they may be pattern-matched, used as generic arguments, and tagged or
borrowed (`@a { x: f64 }`, `&r { x: f64 }`) exactly as a struct is. `Send` and `Sync` extend
to them by the same field-composition rule used for structs.

Three things a record cannot do, all for the same underlying reason — it has no nominal
owner:

- **No inherent methods.** Two unrelated modules could otherwise write conflicting methods
  for the same shape with no principled way to choose between them.
- **No implementations of a non-local aspect**, by the other direction of that rule. An
  aspect local to the current module may be implemented for a record — but see the note
  below: that is not available yet.
- **No custom `Drop`.** `Drop` is a standard-library aspect and never local to ordinary
  user code, so teardown logic belongs to nominal types only.

> **Not available in v0.12.0: implementing a local aspect for a record.** `extend { w: i64 }:
> MyAspect { … }` does not work. This is not specific to records — `extend` on a tuple
> target fails the same way; implementations for these two structural types are not built
> yet. **Arrays are the exception:** `extend<T> T[]: MyAspect { … }` is supported, per the
> orphan-rule carve-out for structural type constructors — see
> [Declarations — Structural Aspect Bounds](declarations.md#structural-aspect-bounds).
> Until a record or tuple target is supported, **a record satisfies no aspect that requires
> an implementation**, so a record cannot be printed, compared, or passed where any such
> bound is required. Auto-derived aspects are unaffected.

### Projection

A nominal type's row may be projected to a named subset, written with a dot to distinguish
it from a struct literal:

```metel
Handle.{ fd }           // the type: Handle's row, narrowed to `fd`
```

A bare identifier inside projection braces is always a **field label**, never a type or a
row variable. Chained projection (`S.{ a }.{ b }`) and projection in pattern position are not
accepted.

Inside an `extend` block, `Self.{ fd }` projects `Self`'s own row exactly as
`Handle.{ fd }` would project `Handle`'s — `Self` resolves to the enclosing block's
target type here the same way it does everywhere else the target's name can stand in
for it.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.anonymous-records.dynamics-1}

Record identity is structural: records with the same labelled fields and field types are
the same type regardless of declaration-free spelling order.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [91_anonymous_records_extra.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/91_anonymous_records_extra.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.anonymous-records.legality-1}

An anonymous record cannot satisfy an impl-based aspect bound, because no implementation
for a record target is available.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage5_neg_19_record_does_not_satisfy_aspect_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_19_record_does_not_satisfy_aspect_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.anonymous-records.dynamics-2}

Projection `Handle.{ fd, mode }` yields the record made from precisely the named fields of
the nominal receiver type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [101_self_record_projection_resolves.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/101_self_record_projection_resolves.mtl), [102_self_record_projection_in_body_let_annotation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/102_self_record_projection_in_body_let_annotation.mtl), [91_anonymous_records_extra.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/91_anonymous_records_extra.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.anonymous-records.legality-3}

An anonymous record is rejected as an inherent-implementation target, as the target of a
non-local aspect implementation, and as the target of a custom `Drop` implementation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage5_neg_11_anonymous_record_inherent_method.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_11_anonymous_record_inherent_method.mtl), [stage5_neg_12_anonymous_record_drop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_12_anonymous_record_drop.mtl), [stage5_neg_13_anonymous_record_nonlocal_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_13_anonymous_record_nonlocal_aspect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Arrays

`Array<T>` is the built-in ordered sequence type. The shorthand `T[]` is preferred.

```metel
fun main() -> i64 {
    let nums: i64[] = [1, 2, 3];
    let names: Array<String> = ["alice", "bob"];
    if (names.len() == 2) { nums[0] } else { 0 }
}
```

Index access uses `[]` with a `u64` index. Out-of-bounds access causes a panic.

```metel
fun main() -> i64 {
    let nums: i64[] = [1, 2, 3];
    let first = nums[0];
    return first;
}
```

Arrays are usable in `for-in` loops.

> **Since v0.12.0 (RFC-0126): `T[]` is a borrowed view, not an owning buffer.**
> `T[]` will be a non-owning, immutable, unconditionally-`Copy` view over a contiguous run —
> a pointer and a length, produced only by borrowing a `List<T>`, a `[T; N]`, or another
> slice. `a[0] = 9` through a `T[]` will stop compiling; mutation moves to `List<T>` or a
> `[T; N]`. Array literals produce `[T; N]` (below), not `T[]` — `let nums: i64[] = [1, 2,
> 3];` above will keep working via `[T; N]`'s existing implicit coercion to `T[]` (RFC-0053),
> not because the literal itself is a `T[]`.

The three-way split between `T[]`, `[T; N]`, and `List<T>` below reflects the current
design. The exact boundary between them — in particular, how a growable list's storage is
allocated and grown — is not yet fully specified and may change in a future release.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.arrays.legality-1}

`T[]` is an unconditionally-`Copy`, non-owning borrowed view. It has no `Drop`; using a
view does not move the underlying elements out of the view.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md), [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md), [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [76_array_display_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/76_array_display_structural_impl.mtl), [77_array_clone_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/77_array_clone_structural_impl.mtl), [39_borrowed_array_for_in_cannot_move_noncopy.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/39_borrowed_array_for_in_cannot_move_noncopy.mtl), [40_borrowed_array_for_in_copy_is_valid.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/40_borrowed_array_for_in_copy_is_valid.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.arrays.legality-2}

An array index expression must have type `u64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_04_array_negative_index.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/neg_04_array_negative_index.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Fixed-size arrays

`[T; N]` is an array type whose length `N` is a non-negative integer literal known at compile time.
`[T; N]` coerces to `T[]` (not the reverse). `N` must be a non-negative integer literal; variables are not permitted.

```metel
fun main() {
    // Repeat construction: every element is the same value.
    let zeros: [i64; 3] = [0; 3];

    // Literal construction with an explicit sized type.
    let ones: [i64; 3] = [1, 2, 3];

    // Coerces to T[] when a T[] is expected.
    fun first(xs: i64[]) -> i64 { xs[0] }
    let v = first(ones);          // [i64; 3] → i64[]
}
```

Indexing and `for-in` work identically to `T[]`. Array patterns match sized arrays:

```metel
fun sum(xs: [i64; 3]) -> i64 {
    match xs {
        [a, b, c] => a + b + c,   // exact-count pattern on [T; 3]
    }
}
```

> **Availability:** Since v0.8.0.

> **Since v0.12.0 (RFC-0126): array literals produce `[T; N]`, not `T[]`.** `[1, 2,
> 3]` will have type `[i64; 3]`; a literal has a statically known length and owns its
> elements, which is what `[T; N]` already is. Slices arise only from borrowing, never from
> a literal. The `[T; N]` → `T[]` coercion above already applies wherever `T[]` is expected —
> a `let`/`var` target, a function argument, a generic instantiation — so this does not by
> itself require touching call sites that already pass a `[T; N]`-typed or explicitly
> `T[]`-annotated value; it only changes what an *unannotated* literal's own type is.

See the note under "Arrays" above — this split is not considered final.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.fixed-size-arrays.legality-1}

An array literal has fixed-size-array type `[T; N]`, not `T[]`, where `N` is its literal
element count.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage3_04_sized_arrays.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-2}

`[T; N]` implicitly coerces to `T[]` wherever `T[]` is expected. The reverse coercion
is not permitted.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md), [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_borrowed_array_for_in_copy_is_valid.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/40_borrowed_array_for_in_copy_is_valid.mtl), [stage3_04_sized_arrays.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.mtl), [stage3_neg_10_sized_array_dynamic_to_fixed.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_10_sized_array_dynamic_to_fixed.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-3}

`[T; N]` is a fixed-size-array type only when `N` is a non-negative integer literal;
the element type and literal length both participate in type identity, including for
`[T; 0]`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [13_sized_array_extended.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/13_sized_array_extended.mtl), [stage3_04_sized_arrays.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.mtl), [stage3_neg_07_sized_array_n_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_07_sized_array_n_mismatch.mtl), [stage3_neg_08_sized_array_elem_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_08_sized_array_elem_mismatch.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.fixed-size-arrays.dynamics-1}

A repeat array expression `[expr; N]` evaluates `expr` once, then clones that result to
produce all `N` elements.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [fixed_array_repeat_evaluates_once.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/fixed_array_repeat_evaluates_once.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-4}

Where `[T; N]` is expected, an array literal is accepted only when it contains exactly
`N` elements of type `T`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage3_04_sized_arrays.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.mtl), [stage3_neg_07_sized_array_n_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_07_sized_array_n_mismatch.mtl), [stage3_neg_08_sized_array_elem_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_08_sized_array_elem_mismatch.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-5}

A fixed-size array type `[T; N]` is valid as a struct field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [45_lvalue_paths.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/45_lvalue_paths.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-6}

A fixed-size array may have another fixed-size array as its element type, such as
`[[i64; 2]; 2]`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [fixed_array_nested.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/fixed_array_nested.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-7}

An exact array pattern for a `[T; N]` value must have a compatible element count; a
different exact count is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [12_sized_array.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/12_sized_array.mtl), [13_sized_array_extended.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/13_sized_array_extended.mtl), [stage3_neg_09_sized_array_pattern_undercount.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_09_sized_array_pattern_undercount.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-8}

The length in `[T; N]` is an integer literal, not a named generic type parameter or an
arbitrary runtime expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_sized_array_named_length.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_sized_array_named_length.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-9}

Every literal index into `[T; 0]` is statically rejected because it is out of bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage3_neg_11_sized_array_zero_literal_index.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_11_sized_array_zero_literal_index.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## References

> **Availability:** Since v0.10.0.

Reference types provide explicit aliasing.

```metel
fun main() -> i64 {
    var value = 1;
    let p: &i64 = &value;
    let q: &var i64 = &var value;
    *q = *p + 1;
    return q;
}
```

Metel has two reference types:

- `&T` — shared immutable reference to `T`
- `&var T` — exclusive mutable reference to `T`

> **Planned for v0.13.0 (RFC-0122): shared XOR exclusive — a place may have any number of `&T` borrows, or exactly one `&var T`, never both.**

"Exclusive" means exactly that rule. It is **not yet enforced**: the current interpreter has
no borrow checker, so a program may hold two `&var T` to the same place and will not be
rejected.

`&var T` coerces to `&T`. The reverse coercion does not exist. Both are non-owning
aliases — a reference never owns the value it points to.

`&T` is `Copy`; `&var T` is not, so an exclusive reference is moved on use rather than
duplicated. Passing one as an argument reborrows instead of moving — see
[Ownership — References and moves](ownership.md#references-and-moves).

References are first-class values, but they are distinct from the referent type. Ordinary
access — field reads/writes, indexing, method dispatch, reading a plain value out — goes
through auto-deref and type-directed copy; an explicit dereference operator `*p` is also
available (v0.11.0) for reading through a reference and for writing through a
`&var T` (`*p = v`). See [Expressions — References](expressions.md#references).

`&var` accepts arbitrary addressable lvalue paths — struct fields, tuple elements, array elements, and chains thereof. Writes through the resulting `&var T` propagate back to the original storage location:

```metel
struct Counter { value: i64 }

fun main() -> i64 {
    var c = Counter { value = 0 };
    let p: &var i64 = &var c.value;
    *p = 42;
    return c.value;   // 42
}
```

> **Availability:** `&var` for lvalue paths since v0.10.0.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.references.legality-1}

An `&var T` reference may be used where `&T` is expected; an `&T` reference may not be
used where `&var T` is expected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [05_mut_reference_coerces_to_shared.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/05_mut_reference_coerces_to_shared.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Reading a value out of a reference

No field, no method, no operator — just the plain value a reference points to. This
cannot be a *move* (references never own their referent), only a *copy*, and only when
the referent's type permits copying:

```metel
fun main() -> i64 {
    let x = 42;
    let r: &i64 = &x;
    let y: i64 = r;   // type-directed copy: y's declared type differs from r's
    return y;
}
```

**The copy fires at every position where a declared or expected type is already
known** — not only `let`/`var` bindings and explicit ascription, but also a `return`
value against the enclosing function's declared return type, a `break` value against
the enclosing `loop`'s inferred type, and any tail expression of a function/method/
closure body, an `if`/`else` branch, or a `match` arm (each of those resolves its
result against a declared or expected type the same way a `let` binding does):

```metel
fun bump(p: &var i64) -> i64 {
    *p += 1;
    p          // tail expression, no explicit `return` — copies out of p
}
```

It never fires silently at a plain call site; `fun f(v: i64)` called as `f(r)` where
`r: &i64` is a type error, not an implicit copy. Argument position has no declared type
of its own for the rule to compare against, the same reason type-directed extraction of
an allocated value never fires implicitly at a plain-parameter call site either
(`public/rfcs/2-accepted/rfc-0066-allocated-value-extraction.md` §3a — not yet
integrated, cited here only for the parallel).

Chains through multiple reference layers the same way auto-deref does — reaching the
declared type may require copying out of more than one layer:

```metel
fun main() -> i64 {
    let x = 42;
    let r: &i64 = &x;
    let rr: &&i64 = &r;
    let y: i64 = rr;   // copies through both layers of the chain
    return y;
}
```

**Until affine ownership (`Copy`/`Drop`, not yet integrated) lands, this applies to
every type** — the interpreter has no move semantics today (everything is deep-cloned on
bind), so there is no non-`Copy` type yet to exclude. Once ownership is integrated, a
non-`Copy` `T` cannot be produced this way.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.references.reading-a-value-out-of-a-reference.legality-1}

Where a declared or expected non-reference type is known, a reference expression may
copy out its referent through every reference layer only when the referent is `Copy`.
This applies to bindings, ascriptions, returns, breaks, and tail expressions, but not
to an un-ascribed call argument.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [01_read_copy_at_return.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/01_read_copy_at_return.mtl), [02_read_copy_at_tail_expression.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/02_read_copy_at_tail_expression.mtl), [03_read_copy_at_loop_break.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/03_read_copy_at_loop_break.mtl), [07_read_copy_through_reference_chain.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/07_read_copy_through_reference_chain.mtl), [13_read_copy_from_call_result.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/13_read_copy_from_call_result.mtl), [neg_06_no_read_copy_at_call_argument.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/neg_06_no_read_copy_at_call_argument.mtl), [neg_14_read_copy_of_non_copy_value_at_let_is_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/neg_14_read_copy_of_non_copy_value_at_let_is_rejected.mtl), [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## List\<T\>

> **Availability:** Since v0.8.0.

`List<T>` is the standard growable-sequence type. Use it when you need to append, pop, or otherwise mutate a sequence. Use `T[]` when the sequence is fixed after construction.

```metel
fun main() {
    var xs: List<i64> = List::new();
    xs.push(1);
    xs.push(2);
    xs.push(3);
    println(xs.len().to_string());   // 3
    let last = xs.pop();             // Some { value = 3 }
}
```

**Construction:**

| Form | Description |
|------|-------------|
| `List::new()` | Empty list |
| `List::from(arr)` | Construct from a `T[]` — copies elements |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `push` | `(&var self, value: T)` | Append an element |
| `pop` | `(&var self) -> Perhaps<T>` | Remove and return the last element, or `None` |
| `len` | `(&self) -> i64` | Number of elements |
| `get` | `(&self, index: i64) -> Perhaps<T>` | Bounds-checked access |
| `as_slice` | `(&self) -> T[]` | View as an immutable array (no copy) |

`List<T>` does not implicitly coerce to `T[]`. Call `.as_slice()` to get a read-only view.

> **Since v0.12.0 (RFC-0126): `as_slice` is what its signature already says.**
> Today `as_slice` returns the same underlying storage, but the result is deep-copied at
> whatever binding or return receives it, so "no copy" describes only the call itself, not
> the value's subsequent lifetime. Once `T[]` is a genuine borrowed view, the returned slice
> stays a live view for as long as it is used — still bounded by `self`'s lifetime, not
> copied away from it.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.list-t.dynamics-1}

`List::new()` creates an empty list, and `List::from(source)` creates a list containing
the elements of `source`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-2}

`push` appends an element; `pop` removes and returns the last element, or `None` for an
empty list.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-3}

`len` reports the list's current number of elements, including changes made by `push`
and `pop`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-4}

`get(i)` returns `Some` for an in-bounds element and `None` when `i` is out of bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.list-t.legality-1}

A `List<T>` is distinct from `T[]`; obtaining its array view requires an explicit
`.as_slice()` call.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Type Ascription

> **Availability:** Since v0.2.0.

The `:` operator [asserts that an expression has a given type without performing any runtime conversion](#spec.types.type-ascription.legality-1). It is a pure type-inference hint — no code is emitted at runtime.

Type ascription is mainly an ergonomics feature. Most code should type-check from
its surrounding context alone; `:` is for the cases where spelling out the intended
type inline is clearer than introducing a separate annotated binding.

```metel
fun main() -> i64 {
    let xs = [] : i64[];
    let x  = 1 : i64;
    if (xs.len() == 0) { x } else { 0 }
}
```

[Ascription fails at compile time if the inferred type of the sub-expression cannot be unified with the ascribed type](#spec.types.type-ascription.legality-2). For example, `1 : String` is invalid. Use `as` to convert between types; use `:` only when the value already has the target type.

<!-- doc-example: expect-fail reason="demonstrates an ascription failure -- the type error is the point" -->
```metel
fun main() -> i64 {
    let y = 1 : String;
    return 0;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.type-ascription.legality-1}

`expr : T` constrains `expr` to type `T` and supplies `T` as its expected type; it performs
no runtime conversion.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md), [rfc-0023](../../rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage8_04_type_ascription.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_04_type_ascription.mtl), [turbofish_return_and_ascription_param_in_same_call.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/turbofish_return_and_ascription_param_in_same_call.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-2}

An ascription is valid only when the expression's type unifies with the ascribed type;
otherwise it is a type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage8_neg_02_ascribe_type_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-3}

An expression may contain at most one type ascription; a second `:` in the same ascription
position is a parse error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage8_neg_08_chained_type_ascription.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_08_chained_type_ascription.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### When ascription helps

Type inference uses surrounding expected types. That expected type can come from a `let` annotation, a function return type, a callee's parameter types, or the surrounding expression context.

Because of that, ambiguous literals like `[]` and `None` often type-check without explicit ascription when the context already determines their type:

```metel
fun zip_lengths(a: i64[], b: String[]) -> i64 {
    return a.len() + b.len();
}

fun make_row(use_default: boolean, fallback: i64[]) -> i64[] {
    return match use_default {
        true  => [],
        false => fallback,
    };
}

fun first_or_default(items: i64[], fallback: Perhaps<i64>) -> i64 {
    return match fallback {
        Some { value } => value,
        None => if (items.len() > 0) { items[0] } else { 0 },
    };
}

fun main() -> i64 {
    let total = zip_lengths([], ["a", "b"]);
    let row = make_row(true, [1, 2, 3]);
    let first = first_or_default([1, 2, 3], None);
    return total + row.len() + first;
}
```

Ascription is still useful when no surrounding context fixes the type:

```metel
fun main() -> i64 {
    let arr = [] : i64[];
    let value = None : Perhaps<i64>;
    match value {
        Some { value } => value + arr.len(),
        None => arr.len(),
    }
}
```

Without such context, ambiguous literals remain a type error. For example, `let x = None;` does not provide enough information to infer the element type.

<!-- doc-example: expect-fail reason="demonstrates an ambiguous None -- the type error is the point" -->
```metel
fun main() -> i64 {
    let x = None;
    return 0;
}
```

## Type Casting

The `as` operator [performs an explicit conversion from `expr`'s type to `T`](#spec.types.type-casting.dynamics-1). It desugars to a call to the `From` aspect and is infallible — the result is the target type directly.

```metel
fun main() {
    let x: i32 = 1000i32;
    let b: i8  = x as i8;    // wraps: 1000 mod 256 → -24
    let f: f32 = x as f32;   // 1000.0f32
    let u: u64 = x as u64;   // 1000u64

    let pi: f64 = 3.14;
    let n: i32  = pi as i32; // truncates toward zero → 3
}
```

All pairwise casts among `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`, `f32`, `f64` are supported. Narrowing integer casts wrap (two's-complement truncation). f64-to-integer casts truncate toward zero.

Because `as` desugars to `From`, user-defined types become castable by implementing `From<SourceType>` for the target type.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.type-casting.dynamics-1}

`expr as T` evaluates an explicit conversion of `expr` to `T` via `From<S>::from` (where
`S` is `expr`'s type) and produces a value of type `T`. Not restricted to numeric types —
any type with an applicable `From<S>` implementation is a valid cast target.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage8_04_type_ascription.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_04_type_ascription.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Generics

> **Availability:** Built-in generic types (`Perhaps<T>`, `Result<T, E>`, `T[]`) since v0.1.0. User-defined generic functions and types since v0.3.0.

Types and functions can be parameterized with `<T>` syntax.

```metel
struct Stack<T> {
    items: T[],
}

fun first<T>(arr: T[]) -> Perhaps<T> {
    if (arr.len() == 0) {
        return None;
    }
    return Some { value = arr[0] };
}

fun main() -> i64 {
    let stack = Stack { items = [1, 2, 3] };
    match first(stack.items) {
        Some { value } => value,
        None => 0,
    }
}
```

### Row bounds

> **Availability:** Since v0.12.0.

A bound written as a row accepts any type carrying at least the listed fields:

```metel
fun squared_magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64 {
    p.x * p.x + p.y * p.y
}
```

**The trailing `..` is load-bearing.** It stands for "and a rest I am not naming," and its
presence is what makes the bound *open*:

```metel
fun g<record T: { x: f64 }>(p: T)        // closed: T's row is exactly `x`
fun h<record T: { x: f64, .. }>(p: T)    // open:  T has at least `x`
```

A record pattern's own trailing `..` reads the bound's listed fields the same way
[field access](#spec.types.generics.row-bounds.legality-6) does, and — unlike field access
— can discard the rest of an open bound's unlisted fields rather than being unable to name
them at all:

```metel
fun describe<record T: { x: f64, .. }>(p: T) -> String {
    match p {
        { x, .. } => "x is ${x}, plus whatever else the caller passed",
    }
}
```

**The `..` is required to match an open bound at all** — its full field set isn't known
here, so a pattern that doesn't end in `..` can never be exhaustive:

```metel
fun bad<record T: { x: f64, .. }>(p: T) -> f64 {
    match p {
        { x } => x,   // error: open bound's field set isn't known here; add `..`
    }
}
```

A closed bound's fields *are* fully known, so `..` there is optional sugar rather than a
requirement — a pattern matching a closed bound must still name every field the bound
lists unless it uses `..`:

```metel
fun get_x<record T: { x: f64, y: f64 }>(p: T) -> f64 {
    match p {
        { x, y } => x,       // OK: every field of the closed bound is named
        // { x } => x,       // error: `y` isn't named and there's no `..`
    }
}
```

Naming a field the bound doesn't list is still rejected, `..` or not — the pattern's rest
form discards *unnamed* fields, not fields the bound never promised are there:

```metel
fun bad2<record T: { x: f64, .. }>(p: T) -> f64 {
    match p {
        { x, z, .. } => x,   // error: no field `z` on the bound
    }
}
```

**A field may omit its type** to constrain the label only — `{ x }` means "carries an `x`,
whatever its type":

```metel
fun f<record T: { x, .. }>(p: T)          // has an `x` of some type
fun g<record T: { x, y: f64, .. }>(p: T)  // any-typed `x`, `f64` `y`
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

**A row bound is satisfied by a record, not by a nominal struct.** The `record` marker on the
type parameter says so at the declaration; a bare `<T: { … }>` is an error.

The marker may be written at the parameter or in a `where` clause — the two are equivalent,
and a parameter is record-kinded if either one carries it:

```metel
fun f<record T: { x: f64, .. }>(p: T) -> f64
fun g<T>(p: T) -> f64 where record T: { x: f64, .. }
```

**The row bound is optional.** `<record T>` on its own means "any record, whatever its
fields" — the only way to write that, since a bound of `{ .. }` alone is not accepted:

```metel
fun labels<record T>(x: T) -> Symbol[]   // any record; no constraint on its fields
```

```metel
squared_magnitude({ x = 3.0, y = 4.0 });   // a record — satisfies the bound
squared_magnitude(some_point);             // a struct — does not
```

Nominal structs do not satisfy row bounds. **Named records are planned, not implemented**;
they would provide a nominal record kind. See `public/rfcs/2-accepted/rfc-0120-named-records.md`
(RFC-0120: Named Records) — a plain path mention rather than a link while `rfcs/` is
excluded from the website (see metel-website's `docusaurus.config.ts`), so this doesn't
become a broken link once RFCs sync through.

### Why row capability is opt-in

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

### What satisfies which bound

Both bound kinds are opted into; they differ only in *granularity*. An **aspect** bound is
opted into per aspect, by writing an implementation. A **row** bound is opted into per type,
by choosing the `record` kind. Nothing is implicit in either direction.

> **Available now (RFC-0137, metel-core#857): a `struct`'s "no" below is a visibility
> gate, not the absence of a row.** Every struct is represented internally as
> `(brand, row)` (see [Ownership — Narrowing](ownership.md#narrowing)); what the table's
> "no" states is that a plain struct's row is never *visible* to row-bound satisfaction,
> regardless of narrowing or projection — including at full width, where the row's
> content is identical to a same-shaped record's — the same observable outcome as
> before, now restated on the branded-row mechanism itself rather than merely predicted
> of it.

| | non-local aspect (`Display`) | local aspect | row bound |
|---|---|---|---|
| `struct` | yes, with an impl | yes, with an impl | **no** |
| `enum` | yes, with an impl | yes, with an impl | **no** — sums, not products |
| anonymous record | **no** — see below | yes, with an impl | yes |

An anonymous record has no owning module, so the orphan rule permits an implementation only
for an aspect local to the implementing module. Every standard-library aspect is non-local,
which means no anonymous record is `Display` and `println("${r}")` does not work on one.
Auto-derived aspects are unaffected — `Send` and `Sync` are computed from field composition
rather than declared.

### Implementing an aspect for a record

Three forms, with different rules:

```metel
extend { x: f64, y: f64 }: MyAspect { … }                    // one concrete row
extend<row R: { x: f64, .. }> { ..R }: MyAspect { … }         // every row of a given shape
extend<row R> { ..R }: MyAspect { … }                         // every row
```

**None of the three are available in v0.12.0** — this contradicted the "Not available in
v0.12.0" callout above until corrected here; confirmed directly, `extend { x: f64, y: f64 }:
MyAspect { … }` still fails with the same "cannot `extend` an anonymous record type" rejection
tuples and records both hit. The first form is the one this design intends to land first —
exactly one structural type, permitted once the aspect is local — but it is not implemented
yet, unlike the equivalent one-concrete-target form for arrays (`extend<T> T[]: Aspect`,
already supported). The second and third additionally require row variables, which don't
exist at all yet. The second also needs overlap checking between row bounds — two
shape-conditional implementations can be *incomparable* rather than one being more specific,
so they must be disjoint. The third additionally needs a way to require an aspect of every
field in the row, which does not yet exist either.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.generics.row-bounds.legality-1}

A row bound requires `record` on its type parameter, either at the parameter declaration
or in a `where` constraint; `record` without a row bound is also a legal any-record bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [93_row_bounds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/93_row_bounds.mtl), [record_bound_inline_and_where_clause_combined.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/record_bound_inline_and_where_clause_combined.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-2}

A negative row bound is satisfied only when none of its named fields match; it accepts no
trailing `..` and a negative bound in a `where` clause is enforced like an inline one.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [negative_row_bound_rejects_open.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/negative_row_bound_rejects_open.mtl), [neg_row_bound_where_clause_rejects_forbidden_field.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/neg_row_bound_where_clause_rejects_forbidden_field.mtl), [record_bound_inline_and_where_clause_combined.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/record_bound_inline_and_where_clause_combined.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-3}

A field in a row bound may omit its type, constraining the field label while accepting any
field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [93_row_bounds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/93_row_bounds.mtl), [record_bound_inline_and_where_clause_combined.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/record_bound_inline_and_where_clause_combined.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-4}

Only a record satisfies a row bound; a nominal struct is rejected even when it has matching
fields.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_44_full_width_projection_still_rejected_by_row_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/neg_44_full_width_projection_still_rejected_by_row_bound.mtl), [stage5_neg_26_row_bound_struct_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_26_row_bound_struct_rejected.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-5}

Brace syntax after a parameter or `let` annotation denotes an exact record type, while the
same syntax in a generic parameter or `where` constraint denotes a row bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [95_record_type_vs_row_bound_by_position.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/95_record_type_vs_row_bound_by_position.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-6}

A field a row bound lists is accessible via field access (`p.x`) from inside the function
body; a field the bound doesn't list is not, even when a caller's concrete argument
happens to carry it.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [94_row_bound_field_access.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/94_row_bound_field_access.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-7}

A record pattern's trailing `..` binds only the fields it names against a row-bounded
type parameter and discards the rest, the same as it does against a named struct. It is
required to match an open bound at all, since the bound's full field set isn't known;
for a closed bound it is optional, but the pattern must otherwise name every field the
bound lists. Naming a field the bound doesn't list is rejected regardless of `..`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [96_row_bound_rest_pattern.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/96_row_bound_rest_pattern.mtl), [row_bound_pattern_missing_field_without_rest_is_t0001.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/row_bound_pattern_missing_field_without_rest_is_t0001.mtl), [row_bound_pattern_names_field_outside_bound_is_t0003.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/row_bound_pattern_names_field_outside_bound_is_t0003.mtl), [row_bound_pattern_without_rest_on_open_bound_is_t0001.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/row_bound_pattern_without_rest_on_open_bound_is_t0001.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Never Type

> **Availability:** Since v0.10.0.

`!` (Never) is the **uninhabited bottom type** — no value of type `!` can ever be
constructed. A `loop` with no reachable `break` has type `!`:

```metel
fun main() -> i64 {
    let result: i64 = loop { break 42; };
    return result;
}
```

`return <expr>`, `panic(<message>)`, `loop { }` with no reachable `break`, and `break`/`continue` used as value expressions in loop context all have type `!`. If any sub-expression has type `!`, that sub-expression diverges before the outer expression can produce a value, so the outer expression's type is unconstrained and any type is accepted in that position.

### Subtyping and coercion

`!` is a subtype of every type — `! <: T` for all `T` — so an expression of type `!` coerces implicitly, with no cast, to any context expecting `T`. This is what makes the rule above sound: code after a diverging expression is unreachable, but still typechecks against whatever its context requires.

### Match exhaustiveness

A `match` whose scrutinee has type `!` needs no arms — an empty match is vacuously exhaustive, since no value of type `!` can ever reach it:

```metel
fun unreachable_code(x: !) -> i64 {
    match x { }   // exhaustive — no arms needed
}
```

More generally, an enum variant whose payload type is `!` is uninhabited — no value of that variant can ever be constructed — and a `match` may omit the arm for an uninhabited variant while remaining exhaustive:

```metel
enum Foo {
    A { x: i64 },
    B { y: ! },
}

fun handle(f: Foo) -> i64 {
    match f {
        Foo::A { x } => x,
        // Foo::B omitted — exhaustive; B is uninhabited
    }
}
```

### Inhabited-singleton coercion

If an enum has exactly one inhabited variant (every other variant's payload is `!`) and that variant has exactly one field, a value of the enum type coerces implicitly to the field's type — the compiler inserts the destructuring, no explicit `match` required:

```metel
enum Wrapper<T> {
    Present { value: T },
    Absent  { _: ! },
}

fun infallible() -> Wrapper<i64> { Wrapper::Present { value = 42 } }

fun main() -> i64 {
    let x: i64 = infallible();  // implicit coercion via the inhabited-singleton rule
    return x;
}
```

`Result<T, !>` satisfies this: `Ok { value: T }` is the one inhabited variant with one field, so a `Result<T, !>`-returning function's caller can use the result as a plain `T` with no `match`. `Perhaps<!>` does **not** satisfy it — `None` is inhabited but has zero fields — so `Perhaps<!>` never coerces implicitly to anything, though nothing prevents it from arising through generic instantiation.

### `!` as a return type

A function annotated `-> !` promises never to return; every control-flow path must end in a diverging expression, checked by the compiler:

```metel
fun abort(msg: String) -> ! {
    panic(msg);
}
```

A `-> !` function containing a reachable `return` is a type error.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.never-type.legality-1}

`!` is uninhabited: no terminating expression can construct a value of that type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_01_uninhabited_variant_exhaustive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_01_uninhabited_variant_exhaustive.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-2}

`!` is a subtype of every type, and an expression of type `!` implicitly coerces to any
expected type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_04_panic_coerces.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_04_panic_coerces.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-3}

Code made unreachable by a diverging expression remains typechecked in its surrounding
type context.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_03_unreachable_arm_allowed.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_03_unreachable_arm_allowed.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.never-type.dynamics-1}

`return`, `panic`, a non-breaking `loop`, and value-position `break` or `continue`
diverge and have type `!`; an enclosing expression cannot produce a value after such a
subexpression diverges.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_panic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/neg_panic.mtl), [never_04_panic_coerces.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_04_panic_coerces.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-4}

Match exhaustiveness excludes impossible scrutinee values and uninhabited variants.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [uninhabited_match.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/uninhabited_match.mtl), [never_01_uninhabited_variant_exhaustive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_01_uninhabited_variant_exhaustive.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-5}

A match whose scrutinee has type `!` is exhaustive with no arms.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [uninhabited_match.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/uninhabited_match.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-6}

An enum variant containing a `!` payload is uninhabited; its match arm may be omitted or,
if written, is unreachable but not rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [uninhabited_match.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/uninhabited_match.mtl), [never_01_uninhabited_variant_exhaustive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_01_uninhabited_variant_exhaustive.mtl), [never_03_unreachable_arm_allowed.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_03_unreachable_arm_allowed.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-7}

An enum with exactly one inhabited, single-field variant implicitly coerces to that
field's type; zero-field or multi-field inhabited variants do not receive this coercion.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [singleton_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/singleton_coercion.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.never-type.dynamics-2}

When every arm of a match diverges, the match expression has type `!`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_04_panic_coerces.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_04_panic_coerces.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-8}

`Result<T, !>` has an uninhabited `Err` variant and therefore only an `Ok` value can be
constructed.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [singleton_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/singleton_coercion.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-9}

`Result<T, !>` satisfies the inhabited-singleton coercion rule and a match omitting `Err`
is exhaustive.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_02_result_never_err_exhaustive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_02_result_never_err_exhaustive.mtl), [never_03_unreachable_arm_allowed.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_03_unreachable_arm_allowed.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-10}

`Perhaps<!>` has only its zero-field `None` variant inhabited; it does not coerce to a
field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_08_perhaps_never_exhaustive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_08_perhaps_never_exhaustive.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-11}

A function declared `-> !` is legal only when every reachable control-flow path diverges;
a reachable ordinary return is a type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [never_05_ret_never_diverges_ok.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_05_ret_never_diverges_ok.mtl), [never_07_panic_semicolon_diverges.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_07_panic_semicolon_diverges.mtl), [never_neg_01_ret_never_reachable_return.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/never_neg_01_ret_never_reachable_return.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## `Perhaps<T>`

`Perhaps<T>` is the built-in optional type. There is no null — all absence is expressed via `Perhaps<T>`.

[The type of `None` is `Perhaps<T>` for some `T` that must be determinable from context](#spec.types.perhaps-t.legality-1). If no context constrains `T` — for example, a bare `let x = None` with no annotation and no subsequent use that pins the element type — the program is a type error. An explicit annotation is required in that case:

> **Changed in v0.11.0 (RFC-0111): `None` and `Some` are ordinary variants of `Perhaps<T>`, not literals.**

`None` and `Some` have no special status in the grammar or the type system. They resolve exactly as `Red` does for a user-declared `enum Colour { Red, .. }` — bare where the expected type determines the enum, qualified (`Perhaps::None`) anywhere. Everything said here about needing a determinable type follows from that general rule rather than from a rule about `None` specifically, and the same is true of `Result<T, E>`'s `Ok`/`Err`. See [Expressions — Unqualified variant constructors](expressions.md#unqualified-variant-constructors).

```metel
fun main() -> i64 {
    let x: Perhaps<i64> = None;
    match x {
        Some { value } => value,
        None => 0,
    }
}
```

```metel
fun main() -> i64 {
    let result: Perhaps<i64> = None;
    let value: Perhaps<i64> = Some { value = 42 };
    match value {
        Some { value } => value,
        None => match result {
            Some { value } => value,
            None => 0,
        },
    }
}
```

Use `match` to unwrap safely:

```metel
struct User {
    id: i64,
}

fun find_user(id: i64) -> Perhaps<User> {
    if (id == 1) {
        return Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    match find_user(1) {
        Some { value } => value.id,
        None => 0,
    }
}
```

`.yolo()` unwraps, panicking if the value is `None`:

```metel
struct User {
    id: i64,
}

fun find_user(id: i64) -> Perhaps<User> {
    if (id == 1) {
        return Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    let user = find_user(1).yolo();
    return user.id;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.perhaps-t.legality-1}

`None` is the empty variant of `Perhaps<T>` and is valid only where the expected type
determines `T`; `Perhaps::None` is valid wherever the qualified variant is named.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0020](../../rfcs/4-implemented/rfc-0020-language-rebranding.md), [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [39_perhaps.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/39_perhaps.mtl), [41_unqualified_variant_constructors.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/41_unqualified_variant_constructors.mtl), [42_variant_deferral_resolves.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/42_variant_deferral_resolves.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## `Result<T, E>`

`Result<T, E>` represents the outcome of a fallible operation:

```metel
fun divide(a: f64, b: f64) -> Result<f64, String> {
    if (b == 0.0) {
        return Err { error = "division by zero" };
    }
    return Ok { value = a / b };
}

fun main() -> i64 {
    match divide(8.0, 2.0) {
        Ok { value } => value as i64,
        Err { error } => 0,
    }
}
```

Use `match` to handle both cases, or [`?`](functions.md#spec.functions.the-operator.dynamics-2)
to propagate errors.

[`.yolo()`](runtime.md#spec.runtime.panics.dynamics-1) also works on `Result<T, E>`,
panicking on `Err`.
