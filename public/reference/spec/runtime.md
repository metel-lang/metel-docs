# Runtime

## Panics

A panic is a hard, unrecoverable runtime error. It prints a message and exits the process with a non-zero status. Panics cannot be caught.

Panics are triggered by:
- `.yolo()` on `None` or a `Result::Err`
- Out-of-bounds array access
- Integer division by zero
- `assert(false)` or `assert(false, msg)`

## Built-in Functions

These are available in every module without any `import` declaration (provided by `std::core` auto-import):

| Name              | Signature                            | Description                              |
|-------------------|--------------------------------------|------------------------------------------|
| `print`           | `<T>(v: T)`                          | Print to stdout, no newline              |
| `println`         | `<T>(v: T)`                          | Print to stdout with newline             |
| `clock`           | `() -> Int`                          | Unix timestamp in milliseconds          |
| `assert`          | `(cond: boolean)`                    | Panic with `"assertion failed"` if `cond` is `false` |
| `assert`          | `(cond: boolean, msg: String)`       | Overload: panic with `msg` if `cond` is `false` |
| `dbg`             | `<T>(v: T) -> T`                     | Print `[dbg] <value>` to stderr and return the value unchanged |

`assert` is overloaded — the two-argument form carries the panic message.

String length is a method, not a free function: `"hello".len()` returns the
number of characters (Unicode scalar values). Strings are concatenated with
the `+` operator.

## Built-in Aspects

The following aspects are pre-implemented for built-in types:

### Display

```metel
aspect Display {
    fun to_string(&self) -> String;
}
```

`Int`, `Float`, `boolean`, `String`, and `Char` implement `Display`. `.to_string()` returns the canonical string representation. `print` and `println` accept any `Display` type.

### Iterable\<T\>

```metel
aspect Iterable<T> {
    fun next(&mut self) -> Perhaps<T>;
}
```

`T[]` (array) and `Range` (from `..` / `..=`) implement `Iterable<T>`. User-defined types may implement it to be usable in `for-in`.

### From\<S\>

```metel
aspect From<S> {
    fun from(value: S) -> Self;
}
```

`Int` implements `From<Float>` (truncating cast) and `Float` implements `From<Int>`. The `as` operator desugars to `T::from(value)`. User-defined types may implement `From<S>` to enable `as` casts and `?` error coercion.

## String Methods

| Method        | Signature         | Description                        |
|---------------|-------------------|------------------------------------|
| `.len()`      | `() -> Int`       | Number of characters in the string |
| `.to_string()`| `() -> String`    | Returns the string itself          |

## Array Methods

`T[]` and `[T; N]` both expose:

| Method    | Signature       | Description                        |
|-----------|-----------------|------------------------------------|
| `.len()`  | `() -> i64`     | Number of elements                 |

## Char Methods

> Since v0.8.0.

| Method / Function         | Signature                        | Description                                  |
|---------------------------|----------------------------------|----------------------------------------------|
| `.to_u32()`               | `() -> u32`                      | Unicode scalar value as a `u32`              |
| `Char::from_u32(n)`       | `(u32) -> Perhaps<Char>`         | Construct from a code point; `None` if invalid |
| `.to_string()`            | `() -> String`                   | Single-character string                      |
