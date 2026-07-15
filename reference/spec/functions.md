# Functions

```metel
fun add(a: i64, b: i64) -> i64 {
    return a + b;
}

fun main() -> i64 {
    return add(2, 3);
}
```

Parameter type annotations are optional when types can be inferred from context. The return type follows `->` and is also optional — a function with no return annotation and no `return expr;` returns `()`. `return expr;` and bare `return;` are both valid.

## Associated Functions

`extend` blocks may contain functions with no `self` parameter. These are called on
the type via `::` syntax and serve as the canonical constructor pattern:

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun new(x: f64, y: f64) -> Point {
        return Point { x: x, y: y };
    }
}

fun main() -> i64 {
    let p = Point::new(1.0, 2.0);
    return p.x as i64;
}
```

## First-Class Functions

Functions are first-class values and can be assigned, passed, and returned:

```metel
fun add(a: i64, b: i64) -> i64 {
    return a + b;
}

fun apply(f: (i64) -> i64, x: i64) -> i64 {
    return f(x);
}

fun main() -> i64 {
    let f = add;
    let inc = (x: i64) -> i64 { return x + 1; };
    return f(1, 2) + apply(inc, 4);
}
```

The type of a function or closure is written as `(ParamTypes) -> ReturnType`.

## Closures

Anonymous functions are written with the `(...) -> ... { ... }` form:

```metel
fun main() -> i64 {
    let double = (x: i64) -> i64 { return x * 2; };
    return double(5);
}
```

Closures capture variables from their enclosing scope by value. A captured variable is cloned into the closure environment when the closure is created:

```metel
fun main() -> i64 {
    var count = 0;
    let inc = () -> { count += 1; };
    inc();
    inc();
    return count;   // still 0
}
```

Shared mutable closure state is explicit. If multiple closures must observe and update the same non-linear storage, the program must capture a regular pointer:

```metel
fun main() -> i64 {
    var count = 0;
    let p: &var i64 = &var count;
    let inc = () -> { p += 1; };
    inc();
    inc();
    return *p;
}
```

## Turbofish

> **Availability:** Since v0.8.0.

When a generic function's type parameters cannot be inferred from the arguments, they can be specified explicitly with turbofish syntax: `name::<T, U>(args)`.

```metel
fun identity<T>(x: T) -> T { x }

fun main() -> i64 {
    let x = identity::<i64>(42);
    return x;
}
```

Turbofish is most useful when two or more independent type parameters must be pinned at the call site — for example, a `zip` function that pairs elements from arrays of different types:

```metel
fun zip<A, B>(a: A[], b: B[]) -> (A, B)[] { /* ... */ }

fun main() {
    let pairs = zip::<i64, String>([1, 2], ["a", "b"]);
}
```

Type ascription (`: T`) remains available for annotating the result type. Turbofish and ascription can be used together:

```metel
let result = parse::<i64>("42") : Perhaps<i64>;
```

## The ? Operator

> **Availability:** Matching-error `?` since v0.1.0. `From`-based error coercion since v0.4.0.

Inside a function returning `Result<T, E>`, `?` propagates errors early:

```metel
fun parse_int(s: String) -> Result<i64, String> {
    if (s == "21") {
        return Result::Ok { value: 21 };
    }
    return Result::Err { error: "not a number" };
}

fun parse_and_double(s: String) -> Result<i64, String> {
    let n = parse_int(s)?;   // returns Err early if parse_int fails
    return Result::Ok { value: n * 2 };
}

fun main() -> i64 {
    match parse_and_double("21") {
        Result::Ok { value } => value,
        Result::Err { error } => 0,
    }
}
```

`?` desugars to: if the expression is `Err(e)`, return `Err(E2::from(e))` immediately (where `E2` is the enclosing function's error type); otherwise unwrap to the `Ok` value.

The inner expression's error type `E1` and the function's return error type `E2` must satisfy `E2: From<E1>`. When `E1 == E2` no conversion is performed. When they differ, `From::from` is called automatically on the error value before re-wrapping in `Err`.

`?` does not apply to `Perhaps<T>` in this language version. It is supported only for
`Result<T, E>`, so using `?` on a `Perhaps` value is a type error (`T0001`) rather
than an early `None` return.

## Native Functions (Standard Library Only)

Standard library declarations may be marked `native`, binding them to an
implementation provided by the host interpreter instead of a Metel body:

```metel
// from std::core — not writable in user code
native(@std.core.println) public fun println<T>(x: T);
native(@std.core.clock)   public fun clock() -> i64;
```

A native declaration has no body — it ends with `;` instead of a block. The
`@`-path inside the parentheses is the binding key that selects the host
implementation. The form is also valid on methods inside `extend` blocks; for
example, the primitive `Display` implementations in `std::core` are declared
this way:

```metel
extend i64: Display {
    native(@std.core.to_string) fun to_string(&self) -> String;
}
```

**`native` is reserved for the standard library.** Using it in any module
outside the `std` namespace is a compile error, and user projects cannot place
modules under `std::` (see [Modules](modules.md)). From the caller's side,
native functions are indistinguishable from ordinary functions: they are
imported, typechecked, and called exactly like any other declaration — the
binding key is an implementation detail of the standard library's source.

Native declarations must annotate every parameter type; an omitted return
type means the function returns `()`.
