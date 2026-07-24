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

**Unsuffixed literals are polymorphic.** When the expected type is known from context (annotation, function parameter, struct field, return type, or the other operand in arithmetic/comparison), an unsuffixed numeric literal adopts that type automatically. When no context is available, the literal defaults to `i64` (integer) or `f64` (float).

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

## Char

> **Availability:** Since v0.8.0.

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

## Tuples

Tuples are lightweight anonymous product types.

```metel
fun main() -> i64 {
    let coord: (i64, i64) = (10, 20);
    let triple: (String, i64, boolean) = ("yes", 42, true);
    return coord.0 + triple.1;
}
```

Positional field access uses `.0`, `.1`, etc.:

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

## Anonymous Records

> **Planned for v0.12.0 (RFC-0116): an anonymous, exact-shape product type written in bare braces.**

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
  aspect local to the current module may be implemented for a record.
- **No custom `Drop`.** `Drop` is a standard-library aspect and never local to ordinary
  user code, so teardown logic belongs to nominal types only.

### Projection

A nominal type's row may be projected to a named subset, written with a dot to distinguish
it from a struct literal:

```metel
Handle.{ fd }           // the type: Handle's row, narrowed to `fd`
```

> **Planned for v0.12.0 (RFC-0116): a bare identifier inside projection braces is always a field label.**

Chained projection (`S.{ a }.{ b }`) and projection in pattern position are not accepted.

## Arrays

`Array<T>` is the built-in ordered sequence type. The shorthand `T[]` is preferred.

```metel
fun main() -> i64 {
    let nums: i64[] = [1, 2, 3];
    let names: Array<String> = ["alice", "bob"];
    if (names.len() == 2) { nums[0] } else { 0 }
}
```

Index access uses `[]` with an `i64` index. Out-of-bounds access causes a panic.

```metel
fun main() -> i64 {
    let nums: i64[] = [1, 2, 3];
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

> **Availability:** Since v0.8.0.

## References

> **Availability:** Since v0.10.0.

Reference types provide explicit aliasing for non-linear values.

```metel
fun main() -> i64 {
    var value = 1;
    let p: &i64 = &value;
    let q: &var i64 = &var value;
    q = p + 1;
    return q;
}
```

Metel has two reference types:

- `&T` — shared immutable reference to `T`
- `&var T` — exclusive mutable reference to `T`

`&var T` coerces to `&T`. The reverse coercion does not exist. Both are non-owning
aliases — a reference never owns the value it points to.

References are first-class values, but they are distinct from the referent type. Ordinary
access — field reads/writes, indexing, method dispatch, reading a plain value out — goes
through auto-deref and type-directed copy; an explicit dereference operator `*p` is also
available (v0.11.0) for reading through a reference and for writing through a
`&var T` (`*p = v`). See [Expressions — References](expressions.md#references).

References are only for non-linear aliasing. They cannot target linear values.

`&var` accepts arbitrary addressable lvalue paths — struct fields, tuple elements, array elements, and chains thereof. Writes through the resulting `&var T` propagate back to the original storage location:

```metel
struct Counter { value: i64 }

fun main() -> i64 {
    var c = Counter { value = 0 };
    let p: &var i64 = &var c.value;
    p = 42;
    return c.value;   // 42
}
```

> **Availability:** `&var` for lvalue paths since v0.10.0.

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
    p += 1;
    p          // tail expression, no explicit `return` — copies out of p
}
```

It never fires silently at a plain call site; `fun f(v: i64)` called as `f(r)` where
`r: &i64` is a type error, not an implicit copy. Argument position has no declared type
of its own for the rule to compare against, the same reason type-directed extraction of
an allocated value never fires implicitly at a plain-parameter call site either
(`internal/rfcs/2-accepted/rfc-0066-allocated-value-extraction.md` §3a — not yet
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
    let last = xs.pop();             // Perhaps::Some { value = 3 }
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

## Type Ascription

> **Availability:** Since v0.2.0.

The `:` operator asserts that an expression has a given type without performing any runtime conversion. It is a pure type-inference hint — no code is emitted at runtime.

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

Ascription fails at compile time if the inferred type of the sub-expression cannot be unified with the ascribed type. For example, `1 : String` is invalid. Use `as` to convert between types; use `:` only when the value already has the target type.

```metel
fun main() -> i64 {
    let y = 1 : String;
    return 0;
}
```

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
        Perhaps::Some { value } => value,
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
        Perhaps::Some { value } => value + arr.len(),
        Perhaps::None => arr.len(),
    }
}
```

Without such context, ambiguous literals remain a type error. For example, `let x = None;` does not provide enough information to infer the element type.

```metel
fun main() -> i64 {
    let x = None;
    return 0;
}
```

## Type Casting

The `as` operator casts between any two numeric primitive types. It desugars to a call to the `From` aspect and is infallible — the result is the target type directly.

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
    return Perhaps::Some { value = arr[0] };
}

fun main() -> i64 {
    let stack = Stack { items = [1, 2, 3] };
    match first(stack.items) {
        Perhaps::Some { value } => value,
        Perhaps::None => 0,
    }
}
```

### Row bounds

> **Planned for v0.12.0 (RFC-0118): a bound may be a bare row, constraining a type by the fields it carries rather than by an aspect.**

A bound written as a row accepts any type carrying at least the listed fields:

```metel
fun magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64 {
    (p.x * p.x + p.y * p.y).sqrt()
}
```

**The trailing `..` is load-bearing.** It stands for "and a rest I am not naming," and its
presence is what makes the bound *open*:

```metel
fun g<record T: { x: f64 }>(p: T)        // closed: T's row is exactly `x`
fun h<record T: { x: f64, .. }>(p: T)    // open:  T has at least `x`
```

Negation asserts a label is absent, reusing the `!` that bounds already accept. It takes no
`..`, since absence has no rest to quantify over; `_` means "any type":

```metel
fun send<record T: !{ token: _ }>(t: T) -> i64 { … }
```

> **Planned for v0.12.0 (RFC-0118): a row bound is satisfied by a record; a `struct` does not satisfy one, whatever its fields.**

**A row bound is satisfied by a record, not by a nominal struct.** The `record` marker on the
type parameter says so at the declaration; a bare `<T: { … }>` is an error.

```metel
magnitude({ x = 3.0, y = 4.0 });   // a record — satisfies the bound
magnitude(some_point);             // a struct — does not
```

To give a nominal type row behaviour, **declare it as a record** — that is the primary
route, not conversion:

```metel
record Point { x: f64, y: f64 }    // satisfies row bounds directly
struct Point { x: f64, y: f64 }    // does not
```

Converting an existing struct (`some_point.to_record()`) is the escape hatch for types you
do not control, not the ordinary path.

### What satisfies which bound

Both bound kinds are opted into; they differ only in *granularity*. An **aspect** bound is
opted into per aspect, by writing an implementation. A **row** bound is opted into per type,
by choosing the `record` kind. Nothing is implicit in either direction.

| | non-local aspect (`Display`) | local aspect | row bound |
|---|---|---|---|
| `struct` | yes, with an impl | yes, with an impl | **no** |
| `enum` | yes, with an impl | yes, with an impl | **no** — sums, not products |
| anonymous record | **no** — see below | yes, with an impl | yes |
| `record X` (named) | yes, with an impl | yes, with an impl | yes |

> **Planned for v0.12.0 (RFC-0116): an anonymous record cannot implement a non-local aspect, so it satisfies no standard-library aspect bound.**

An anonymous record has no owning module, so the orphan rule permits an implementation only
for an aspect local to the implementing module. Every standard-library aspect is non-local,
which means no anonymous record is `Display` and `println("${r}")` does not work on one.
Auto-derived aspects are unaffected — `Send` and `Sync` are computed from field composition
rather than declared. A named record has an owning module and does not have this limit.

### Implementing an aspect for a record

Three forms, with different rules:

```metel
extend { x: f64, y: f64 }: MyAspect { … }                    // one concrete row
extend<row R: { x: f64, .. }> { ..R }: MyAspect { … }         // every row of a given shape
extend<row R> { ..R }: MyAspect { … }                         // every row
```

The first applies to exactly one structural type and is permitted when the aspect is local.
The second and third require row variables and are not available in v0.12.0. The second also
needs overlap checking between row bounds — two shape-conditional implementations can be
*incomparable* rather than one being more specific, so they must be disjoint. The third
additionally needs a way to require an aspect of every field in the row, which does not yet
exist.

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

## `Perhaps<T>`

`Perhaps<T>` is the built-in optional type. There is no null — all absence is expressed via `Perhaps<T>`.

The type of `None` is `Perhaps<T>` for some `T` that must be determinable from context. If no context constrains `T` — for example, a bare `let x = None` with no annotation and no subsequent use that pins the element type — the program is a type error. An explicit annotation is required in that case:

> **Changed in v0.11.0 (RFC-0111): `None` and `Some` are ordinary variants of `Perhaps<T>`, not literals.**

`None` and `Some` have no special status in the grammar or the type system. They resolve exactly as `Red` does for a user-declared `enum Colour { Red, .. }` — bare where the expected type determines the enum, qualified (`Perhaps::None`) anywhere. Everything said here about needing a determinable type follows from that general rule rather than from a rule about `None` specifically, and the same is true of `Result<T, E>`'s `Ok`/`Err`. See [Expressions — Unqualified variant constructors](expressions.md#unqualified-variant-constructors).

```metel
fun main() -> i64 {
    let x: Perhaps<i64> = None;
    match x {
        Perhaps::Some { value } => value,
        Perhaps::None => 0,
    }
}
```

```metel
fun main() -> i64 {
    let result: Perhaps<i64> = None;
    let value: Perhaps<i64> = 42;
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
    id: i64,
}

fun find_user(id: i64) -> Perhaps<User> {
    if (id == 1) {
        return Perhaps::Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    match find_user(1) {
        Perhaps::Some { value } => value.id,
        Perhaps::None => 0,
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
        return Perhaps::Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    let user = find_user(1).yolo();
    return user.id;
}
```

## `Result<T, E>`

`Result<T, E>` represents the outcome of a fallible operation:

```metel
fun divide(a: f64, b: f64) -> Result<f64, String> {
    if (b == 0.0) {
        return Result::Err { error = "division by zero" };
    }
    return Result::Ok { value = a / b };
}

fun main() -> i64 {
    match divide(8.0, 2.0) {
        Result::Ok { value } => value as i64,
        Result::Err { error } => 0,
    }
}
```

Use `match` to handle both cases, or `?` to propagate errors.

`.yolo()` also works on `Result<T, E>`, panicking on `Err`.
