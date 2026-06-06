# Type System

Metel is statically and strongly typed. Types are checked at compile time. There are no implicit conversions.

## Primitive Types

| Type     | Description               | Example   |
|----------|---------------------------|-----------|
| `Int`    | 64-bit signed integer (`i64` alias) | `42` |
| `Float`  | 64-bit floating point (`f64` alias) | `3.14` |
| `boolean`| Boolean                   | `true`    |
| `String` | UTF-8 string              | `"hello"` |
| `Char`   | Unicode scalar value      | `'a'`     |
| `()`     | Unit — represents no value | `()`     |

The unit type `()` is only written explicitly when needed as a type parameter (e.g. `Result<(), Error>`). Functions that return nothing omit the `->` annotation entirely.

## Sized Numeric Types

> **Availability:** Since v0.8.0 (RFC-0007).

Metel provides exact-width numeric types for low-level and systems programming. `Int` and `Float` are permanent ergonomic aliases for `i64` and `f64` — they are not deprecated.

**Signed integers:**

| Type  | Width  |
|-------|--------|
| `i8`  | 8-bit  |
| `i16` | 16-bit |
| `i32` | 32-bit |
| `i64` | 64-bit (`Int`) |

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
| `f64` | 64-bit IEEE 754 (`Float`) |

Sized literals use a suffix: `42i32`, `3.14f32`, `255u8`. All casts between sized numeric types are explicit (`as`). Array indices must be `u64`; indexing with `Int` (`i64`) requires an explicit `as u64` cast.

## Char

> **Availability:** Since v0.8.0 (RFC-0007).

`Char` represents a single Unicode scalar value. Character literals use single quotes: `'a'`, `'\n'`, `'\u{1F600}'`.

```metel
fun main() {
    let c: Char = 'a';
    let code: u32 = c.to_u32();
    let back: Perhaps<Char> = Char::from_u32(code);
}
```

`Char` is not `u32` and not a string — no implicit coercions exist. Use `c.to_u32()` to get the Unicode scalar value and `Char::from_u32(n)` (returns `Perhaps<Char>`) to construct from a code point.

## Type Inference

Types are inferred using the Hindley-Milner algorithm with let-polymorphism. Annotations are optional for all bindings, including function parameters and return types. They may be written explicitly for documentation or to restrict a binding to a less general type.

Annotations are required only where there is no expression to infer from:
- Struct and enum field types
- Aspect method signatures

```metel
fun add_annotated(a: Int, b: Int) -> Int { a + b }
fun add_inferred(a, b) { a + b }

fun main() -> Int {
    let x = 42;           // inferred: Int
    let name = "Vlad";    // inferred: String
    let y: Float = 3.14;  // explicit annotation (optional here)
    let total = add_annotated(x, 1) + add_inferred(2, 3);
    if (name == "Vlad") { total + (y as Int) } else { 0 }
}
```

## Tuples

Tuples are lightweight anonymous product types.

```metel
fun main() -> Int {
    let coord: (Int, Int) = (10, 20);
    let triple: (String, Int, boolean) = ("yes", 42, true);
    return coord.0 + triple.1;
}
```

Positional field access uses `.0`, `.1`, etc.:

```metel
fun main() -> Int {
    let coord: (Int, Int) = (10, 20);
    let x = coord.0;
    let y = coord.1;
    return x + y;
}
```

`()` is the zero-element tuple (unit type).

Tuples can be destructured in `match`:

```metel
fun main() -> Int {
    let coord: (Int, Int) = (10, 0);
    match coord {
        (0, y) => y,
        (x, 0) => x,
        (x, y) => x + y,
    }
}
```

## Arrays

`Array<T>` is the built-in ordered sequence type. The shorthand `T[]` is preferred.

```metel
fun main() -> Int {
    let nums: Int[] = [1, 2, 3];
    let names: Array<String> = ["alice", "bob"];
    if (array_len(names) == 2) { nums[0] } else { 0 }
}
```

Index access uses `[]` with an `Int` index. Out-of-bounds access causes a panic.

```metel
fun main() -> Int {
    let nums: Int[] = [1, 2, 3];
    let first = nums[0];
    return first;
}
```

Arrays are usable in `for-in` loops.

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

> Fixed-size array type `[T; N]`: since v0.8.0 (RFC-0053).

## Pointers

Regular pointer types provide explicit aliasing for non-linear values.

```metel
fun main() -> Int {
    let mut value = 1;
    let p: *Int = &value;
    let q: *mut Int = &mut value;
    *q = *p + 1;
    return *q;
}
```

Metel has two regular pointer types:

- `*T` — readable pointer to `T`
- `*mut T` — readable and writable pointer to `T`

`*mut T` coerces to `*T`. The reverse coercion does not exist.

Regular pointers are first-class values, but they are distinct from the pointee type.
There is no implicit dereference for ordinary reads or writes.

Regular pointers are only for non-linear aliasing. They cannot target linear values.

`&mut` accepts arbitrary addressable lvalue paths — struct fields, tuple elements, array elements, and chains thereof. Writes through the resulting `*mut T` propagate back to the original storage location:

```metel
struct Counter { value: Int }

fun main() -> Int {
    let mut c = Counter { value: 0 };
    let p: *mut Int = &mut c.value;
    *p = 42;
    return c.value;   // 42
}
```

> `&mut` for lvalue paths: since v0.8.0 (RFC-0045).

## List\<T\>

> **Availability:** Since v0.8.0 (RFC-0054).

`List<T>` is the standard growable-sequence type. Use it when you need to append, pop, or otherwise mutate a sequence. Use `T[]` when the sequence is fixed after construction.

```metel
fun main() {
    let mut xs: List<i64> = List::new();
    xs.push(1);
    xs.push(2);
    xs.push(3);
    println(xs.len().to_string());   // 3
    let last = xs.pop();             // Perhaps::Some { value: 3 }
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
| `push` | `(&mut self, value: T)` | Append an element |
| `pop` | `(&mut self) -> Perhaps<T>` | Remove and return the last element, or `None` |
| `len` | `(&self) -> i64` | Number of elements |
| `get` | `(&self, index: i64) -> Perhaps<T>` | Bounds-checked access |
| `as_slice` | `(&self) -> T[]` | View as an immutable array (no copy) |

`List<T>` does not implicitly coerce to `T[]`. Call `.as_slice()` to get a read-only view.

## Type Ascription

> **Availability:** Since v0.2.0.

The `:` operator asserts that an expression has a given type without performing any runtime conversion. It is a pure type-inference hint — no code is emitted at runtime.

Type ascription is mainly an ergonomics feature. Most code should type-check from
its surrounding context alone; `:` is for the cases where spelling out the intended
type inline is clearer than introducing a separate annotated binding.

```metel
fun main() -> Int {
    let xs = [] : Int[];
    let x  = 1 : Int;
    if (array_len(xs) == 0) { x } else { 0 }
}
```

Ascription fails at compile time if the inferred type of the sub-expression cannot be unified with the ascribed type. For example, `1 : String` is invalid. Use `as` to convert between types; use `:` only when the value already has the target type.

```metel
fun main() -> Int {
    let y = 1 : String;
    return 0;
}
```

### When ascription helps

Type inference uses surrounding expected types. That expected type can come from a `let` annotation, a function return type, a callee's parameter types, or the surrounding expression context.

Because of that, ambiguous literals like `[]` and `None` often type-check without explicit ascription when the context already determines their type:

```metel
fun zip_lengths(a: Int[], b: String[]) -> Int {
    return array_len(a) + array_len(b);
}

fun make_row(use_default: boolean, fallback: Int[]) -> Int[] {
    return match use_default {
        true  => [],
        false => fallback,
    };
}

fun first_or_default(items: Int[], fallback: Perhaps<Int>) -> Int {
    return match fallback {
        Perhaps::Some { value } => value,
        None => if (array_len(items) > 0) { items[0] } else { 0 },
    };
}

fun main() -> Int {
    let total = zip_lengths([], ["a", "b"]);
    let row = make_row(true, [1, 2, 3]);
    let first = first_or_default([1, 2, 3], None);
    return total + array_len(row) + first;
}
```

Ascription is still useful when no surrounding context fixes the type:

```metel
fun main() -> Int {
    let arr = [] : Int[];
    let value = None : Perhaps<Int>;
    match value {
        Perhaps::Some { value } => value + array_len(arr),
        Perhaps::None => array_len(arr),
    }
}
```

Without such context, ambiguous literals remain a type error. For example, `let x = None;` does not provide enough information to infer the element type.

```metel
fun main() -> Int {
    let x = None;
    return 0;
}
```

## Type Casting

The `as` operator casts between numeric primitive types. It desugars to a call to the `From` aspect and is infallible — the result is the target type directly.

```metel
fun main() -> Int {
    let x: Int = 42;
    let f: Float = x as Float;
    let f2: Float = 3.99;
    let i: Int = f2 as Int;
    return i + (f as Int);
}
```

Allowed primitive casts: `Int` ↔ `Float`.

Because `as` desugars to `From`, user-defined types become castable by implementing `From<SourceType>` for the target type.

## Generics

> **Availability:**
> User-defined generic functions and types: since v0.3.0.
> Built-in generic types (`Perhaps<T>`, `Result<T, E>`, `T[]`): since v0.1.0.

Types and functions can be parameterized with `<T>` syntax.

```metel
struct Stack<T> {
    items: T[],
}

fun first<T>(arr: T[]) -> Perhaps<T> {
    if (array_len(arr) == 0) {
        return None;
    }
    return Perhaps::Some { value: arr[0] };
}

fun main() -> Int {
    let stack = Stack { items: [1, 2, 3] };
    match first(stack.items) {
        Perhaps::Some { value } => value,
        Perhaps::None => 0,
    }
}
```

## Never Type

`!` (Never) is the bottom type — the type of an expression that never produces a value because it diverges (runs forever, panics, or exits). A `loop` with no reachable `break` has type `!`:

```metel
fun main() -> Int {
    let result: Int = loop { break 42; };
    return result;
}
```

`!` is not a type users write in practice; it appears as an inferred type when the typechecker determines a branch or expression cannot return. It is the type of `return`, `panic!`, and `loop { }` with no reachable `break`.

## `Perhaps<T>`

`Perhaps<T>` is the built-in optional type. There is no null — all absence is expressed via `Perhaps<T>`.

The type of `None` is `Perhaps<T>` for some `T` that must be determinable from context. If no context constrains `T` — for example, a bare `let x = None` with no annotation and no subsequent use that pins the element type — the program is a type error. An explicit annotation is required in that case:

```metel
fun main() -> Int {
    let x: Perhaps<Int> = None;
    match x {
        Perhaps::Some { value } => value,
        Perhaps::None => 0,
    }
}
```

```metel
fun main() -> Int {
    let result: Perhaps<Int> = None;
    let value: Perhaps<Int> = 42;
    match value {
        Perhaps::Some { value } => value,
        Perhaps::None => match result {
            Perhaps::Some { value } => value,
            Perhaps::None => 0,
        },
    }
}
```

Use `match` to unwrap safely:

```metel
struct User {
    id: Int,
}

fun find_user(id: Int) -> Perhaps<User> {
    if (id == 1) {
        return Perhaps::Some { value: User { id: 1 } };
    }
    return None;
}

fun main() -> Int {
    match find_user(1) {
        Perhaps::Some { value } => value.id,
        Perhaps::None => 0,
    }
}
```

`.yolo()` unwraps, panicking if the value is `None`:

```metel
struct User {
    id: Int,
}

fun find_user(id: Int) -> Perhaps<User> {
    if (id == 1) {
        return Perhaps::Some { value: User { id: 1 } };
    }
    return None;
}

fun main() -> Int {
    let user = find_user(1).yolo();
    return user.id;
}
```

## `Result<T, E>`

`Result<T, E>` represents the outcome of a fallible operation:

```metel
fun divide(a: Float, b: Float) -> Result<Float, String> {
    if (b == 0.0) {
        return Result::Err { error: "division by zero" };
    }
    return Result::Ok { value: a / b };
}

fun main() -> Int {
    match divide(8.0, 2.0) {
        Result::Ok { value } => value as Int,
        Result::Err { error } => 0,
    }
}
```

Use `match` to handle both cases, or `?` to propagate errors.

`.yolo()` also works on `Result<T, E>`, panicking on `Err`.
