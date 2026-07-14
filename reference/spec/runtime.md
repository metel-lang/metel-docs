# Runtime

## Panics

A panic is a hard, unrecoverable runtime error. It prints a message and exits the process with a non-zero status. Panics cannot be caught.

Panics are triggered by:
- `.yolo()` on `None` or a `Result::Err`
- Out-of-bounds array access
- Integer division by zero
- `assert(false)` or `assert(false, msg)`
- `panic(msg)`, called directly

## Built-in Functions

These are available in every module without any `import` declaration (provided by `std::core` auto-import):

| Name              | Signature                            | Description                              |
|-------------------|--------------------------------------|------------------------------------------|
| `print`           | `<T>(v: T)`                          | Print to stdout, no newline              |
| `println`         | `<T>(v: T)`                          | Print to stdout with newline             |
| `string_len`      | `(s: String) -> i64`                 | Number of characters in a string        |
| `string_concat`   | `(a: String, b: String) -> String`   | Concatenate two strings                 |
| `clock`           | `() -> i64`                          | Unix timestamp in milliseconds          |
| `assert`          | `(cond: boolean)`                    | Panic with `"assertion failed"` if `cond` is `false` |
| `assert`          | `(cond: boolean, msg: String)`       | Overload: panic with `msg` if `cond` is `false` |
| `dbg`             | `<T>(v: T) -> T`                     | Print `[dbg] <value>` to stderr and return the value unchanged |
| `panic`           | `(msg: String) -> !`                 | Panic unconditionally with `msg` (RFC-0078) |

`assert` is overloaded — the two-argument form carries the panic message.

`panic`'s return type `!` coerces to whatever type its calling context expects — see [Never Type](types.md#never-type).

`print` and `println` require their argument to implement `Display`
(`print<T: Display>`): passing a struct or enum with no `Display`
implementation is a compile-time error. A value whose type implements `Display`
is printed through that implementation's `to_string` — user structs and enums,
not only the built-in primitives.

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

`i64`, `f64`, `boolean`, `String`, and `Char` implement `Display`. `.to_string()` returns the canonical string representation. `print` and `println` accept any `Display` type.

### Iterable\<T\>

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}
```

`T[]` (array) and `Range` (from `..` / `..=`) implement `Iterable<T>`. User-defined types may implement it to be usable in `for-in`.

### From\<S\>

```metel
aspect From<S> {
    fun from(value: S) -> Self;
}
```

`i64` implements `From<f64>` (truncating cast) and `f64` implements `From<i64>`. The `as` operator desugars to `T::from(value)`. User-defined types may implement `From<S>` to enable `as` casts and `?` error coercion.

## String Methods
> Utilities since v0.9.0. All index-based operations count **Unicode scalar
> values** (matching `.len()`), and are total — out-of-range indices clamp or
> return `None` rather than panicking.

| Method                    | Signature                         | Description                                       |
|---------------------------|-----------------------------------|---------------------------------------------------|
| `.len()`                  | `() -> i64`                       | Number of characters (Unicode scalars)            |
| `.is_empty()`             | `() -> boolean`                   | Whether the string has no characters              |
| `.to_string()`            | `() -> String`                    | Returns the string itself                         |
| `.to_upper()`             | `() -> String`                    | Uppercased copy                                   |
| `.to_lower()`             | `() -> String`                    | Lowercased copy                                   |
| `.trim()`                 | `() -> String`                    | Whitespace removed from both ends                 |
| `.trim_start()`           | `() -> String`                    | Leading whitespace removed                        |
| `.trim_end()`             | `() -> String`                    | Trailing whitespace removed                       |
| `.contains(needle)`       | `(String) -> boolean`             | Whether `needle` occurs in the string             |
| `.starts_with(prefix)`    | `(String) -> boolean`             | Whether the string begins with `prefix`           |
| `.ends_with(suffix)`      | `(String) -> boolean`             | Whether the string ends with `suffix`             |
| `.index_of(needle)`       | `(String) -> Perhaps<i64>`        | Scalar index of the first occurrence, or `None`   |
| `.split(sep)`             | `(String) -> String[]`            | Split on each `sep` (empty `sep` ⇒ whole string)  |
| `.replace(from, to)`      | `(String, String) -> String`      | Replace every `from` with `to`                    |
| `.repeat(n)`              | `(i64) -> String`                 | The string repeated `n` times (`n <= 0` ⇒ `""`)   |
| `.chars()`                | `() -> Char[]`                    | The characters as an array                        |
| `.char_at(i)`             | `(i64) -> Perhaps<Char>`          | Character at scalar index `i`, or `None`          |
| `.substring(start, end)`  | `(i64, i64) -> String`            | Scalar range `[start, end)`, indices clamped      |

| Associated function       | Signature                         | Description                                       |
|---------------------------|-----------------------------------|---------------------------------------------------|
| `String::join(parts, sep)`| `(String[], String) -> String`    | Concatenate `parts` with `sep` between each       |

Strings are concatenated with the `+` operator.


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

## Core Sum Types

> Methods since v0.9.0.

`Perhaps<T>` and `Result<T, E>` are the core optional/fallible types, both in
`std::core` and available unqualified. Their combinator methods let them be used
in pipelines without explicit `match`:

`Perhaps<T>` — `Some { value: T }` or `None`:

| Method               | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `.is_some()`         | `() -> boolean`                    | Whether this is `Some`                       |
| `.is_none()`         | `() -> boolean`                    | Whether this is `None`                       |
| `.map(f)`            | `<U>((T) -> U) -> Perhaps<U>`      | Transform the value, passing `None` through  |
| `.and_then(f)`       | `<U>((T) -> Perhaps<U>) -> Perhaps<U>` | Chain a `Perhaps`-returning function     |
| `.unwrap_or(d)`      | `(T) -> T`                         | The value, or `d` when `None`                |
| `.unwrap_or_else(f)` | `(() -> T) -> T`                   | The value, or `f()` when `None`              |
| `.yolo()`            | `() -> T`                          | The value, or panics (`R0014`) when `None`   |
| `.ok_or(error)`      | `<E>(E) -> Result<T, E>`           | `Some` becomes `Ok`; `None` becomes `Err(error)` |

`Result<T, E>` — `Ok { value: T }` or `Err { error: E }`:

| Method               | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `.is_ok()`           | `() -> boolean`                    | Whether this is `Ok`                         |
| `.is_err()`          | `() -> boolean`                    | Whether this is `Err`                        |
| `.map(f)`            | `<U>((T) -> U) -> Result<U, E>`    | Transform the success value, passing `Err` through |
| `.and_then(f)`       | `<U>((T) -> Result<U, E>) -> Result<U, E>` | Chain a `Result`-returning function |
| `.unwrap_or(d)`      | `(T) -> T`                         | The success value, or `d` when `Err`         |
| `.unwrap_or_else(f)` | `(() -> T) -> T`                   | The success value, or `f()` when `Err`       |
| `.yolo()`            | `() -> T`                          | The success value, or panics (`R0014`) when `Err`, including the error's debug representation |
| `.map_err(f)`        | `<F>((E) -> F) -> Result<T, F>`    | Transform the error value, passing `Ok` through |
| `.ok()`              | `() -> Perhaps<T>`                 | `Ok` becomes `Some`; `Err` becomes `None`, discarding the error |

> `.yolo()`, `.ok_or()`, `.map_err()`, and `.ok()`: implemented 2026-07-11
> (issue #232, following up on the refused RFC-0079), not yet released in a
> tagged version — will get their own changelog entry when `sprint/25` ships.

## List\<T\>

> Since v0.9.0.

`List<T>` is the growable collection type in `std::core`, available unqualified.

| Method / function    | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `List::new()`        | `() -> List<T>`                    | A new empty list                             |
| `List::from(arr)`    | `(T[]) -> List<T>`                 | A list with a copy of the array's elements   |
| `.push(x)`           | `(&var self, T)`                   | Append an element                            |
| `.pop()`             | `(&var self) -> Perhaps<T>`        | Remove and return the last element           |
| `.len()`             | `() -> i64`                        | Number of elements                           |
| `.get(i)`            | `(i64) -> Perhaps<T>`              | Element at index `i`, or `None`              |
| `.as_slice()`        | `() -> T[]`                        | The backing array                            |
| `.map(f)`            | `<U>((T) -> U) -> List<U>`         | A new list of `f` applied to each element    |
| `.filter(pred)`      | `((T) -> boolean) -> List<T>`      | The elements satisfying `pred`               |
| `.fold(init, f)`     | `<A>(A, (A, T) -> A) -> A`         | Reduce to a single value, left to right      |
| `.find(pred)`        | `((T) -> boolean) -> Perhaps<T>`   | The first element satisfying `pred`          |
| `.concat(other)`     | `(List<T>) -> List<T>`             | This list's elements followed by `other`'s   |

## OsError

> Since v0.9.0.

`OsError` is the error type returned by the host-backed standard-library modules
(`std::fs`, `std::process`). It is in `std::core` (available unqualified) and
implements `Display`.

| Method        | Signature       | Description                          |
|---------------|-----------------|--------------------------------------|
| `.message()`  | `() -> String`  | The human-readable error description |

## Standard Library Modules

These modules are **not** auto-imported — a program must import them explicitly
(e.g. `import std::fs::{read_to_string, write_string};`). Their operations are
host-backed.

### std::env

Read-only process environment inspection.

| Function     | Signature                       | Description                                   |
|--------------|---------------------------------|-----------------------------------------------|
| `get(name)`  | `(String) -> Perhaps<String>`   | The value of an environment variable, or `None` |
| `vars()`     | `() -> EnvVar[]`                | All environment variables (`EnvVar { name, value }`) |

### std::fs

Text-oriented file operations. Fallible operations return `Result<_, OsError>`.

| Function                    | Signature                                       | Description                          |
|-----------------------------|-------------------------------------------------|--------------------------------------|
| `read_to_string(path)`      | `(String) -> Result<String, OsError>`           | Read an entire file into a string    |
| `write_string(path, s)`     | `(String, String) -> Result<(), OsError>`       | Write `s`, replacing any existing file |
| `append_string(path, s)`    | `(String, String) -> Result<(), OsError>`       | Append `s`, creating the file if absent |
| `exists(path)`              | `(String) -> boolean`                           | Whether a file or directory exists   |
| `read_dir(path)`            | `(String) -> Result<String[], OsError>`         | The entry names within a directory   |
| `create_dir(path)`          | `(String) -> Result<(), OsError>`               | Create a single directory            |
| `create_dir_all(path)`      | `(String) -> Result<(), OsError>`               | Create a directory and all parents   |
| `remove_file(path)`         | `(String) -> Result<(), OsError>`               | Remove a file                        |
| `remove_dir(path)`          | `(String) -> Result<(), OsError>`               | Remove an empty directory            |
| `remove_dir_all(path)`      | `(String) -> Result<(), OsError>`               | Remove a directory and its contents  |

### std::process

Command-line arguments and shell-free synchronous subprocess execution.

| Function              | Signature                                                  | Description                                |
|-----------------------|-----------------------------------------------------------|--------------------------------------------|
| `args()`              | `() -> String[]`                                          | The process command-line arguments         |
| `run(command, args)`  | `(String, String[]) -> Result<ProcessOutput, OsError>`    | Run `command` with `args`, capturing output |

`run` executes the command directly — there is no shell, so quoting and shell
expansion never apply. A non-zero exit status is a successful `Ok` result, not
an error; only a failure to launch the command is an `Err`. The result type is
`ProcessOutput { status: i64, stdout: String, stderr: String }`.
