# Runtime

## Panics

A panic is a [hard, unrecoverable runtime error](#spec.runtime.panics.dynamics-1). It prints a message and exits the process with a non-zero status. Panics cannot be caught.

Panics are triggered by:
- `.yolo()` on `None` or an `Err`
- Out-of-bounds array access
- Integer division by zero
- `assert(false)` or `assert(false, msg)`
- `panic(msg)`, called directly

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.panics.dynamics-1}

A panic prints its message, terminates the process with a non-zero status, and cannot be
caught. Calling `panic`, a failing `assert`, `.yolo()` on an absent or error variant,
out-of-bounds array access, and integer division by zero trigger a panic.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_panic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/never/neg_panic.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Built-in Functions

These are available in every module without any `import` declaration (provided by `std::core` auto-import):

| Name              | Signature                            | Description                              |
|-------------------|--------------------------------------|------------------------------------------|
| `print`           | `<T>(v: T)`                          | Print to stdout, no newline              |
| `println`         | `<T>(v: T)`                          | Print to stdout with newline             |
| `clock`           | `() -> i64`                          | Unix timestamp in milliseconds          |
| `assert`          | `(cond: boolean)`                    | Panic with `"assertion failed"` if `cond` is `false` |
| `assert`          | `(cond: boolean, msg: String)`       | Overload: panic with `msg` if `cond` is `false` |
| `dbg`             | `<T>(v: T) -> T`                     | Print `[dbg] <value>` to stderr and return the value unchanged |
| `panic`           | `(msg: String) -> !`                 | Panic unconditionally with `msg` (RFC-0078) |

`assert` is overloaded — [the two-argument form carries the panic message](#spec.runtime.built-in-functions.dynamics-2).

`panic`'s return type `!` [coerces to whatever type its calling context expects](types.md#spec.types.never-type.legality-2) — see [Never Type](types.md#never-type).

`print` and `println` [require their argument to implement `Display`](#spec.runtime.built-in-functions.legality-1)
(`print<T: Display>`): passing a struct or enum with no `Display`
implementation is a compile-time error. A value whose type implements `Display`
is [printed through that implementation's `to_string`](#spec.runtime.built-in-functions.dynamics-1) — user structs and enums,
not only the built-in primitives.

String length is a method, not a free function: `"hello".len()` returns the
number of characters (Unicode scalar values). Strings are concatenated with
the `+` operator.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-functions.legality-1}

`print` and `println` accept only values whose type implements `Display`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage8_neg_02_println_requires_display.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_println_requires_display.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-1}

`print` writes a `Display` value's `to_string` result to stdout without a newline; `println`
writes the same result followed by a newline.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [77_println_user_display.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/77_println_user_display.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-2}

`assert(false)` panics with `"assertion failed"`; `assert(false, msg)` panics with `msg`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [80_assert_panic_messages.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/80_assert_panic_messages.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-3}

`dbg(v)` writes its debug rendering to stderr and evaluates to `v` unchanged.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [dbg_builtin.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/dbg_builtin.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-4}

`clock()` returns the current Unix timestamp in milliseconds.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [81_clock_is_unix_milliseconds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/81_clock_is_unix_milliseconds.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Built-in Aspects

The following aspects are pre-implemented for built-in types:

### Display

```metel
aspect Display {
    fun to_string(&self) -> String;
}
```

[`i64`, `f64`, `boolean`, `String`, and `Char` implement `Display`](#spec.runtime.built-in-aspects.display.legality-1). `.to_string()` returns the canonical string representation. `print` and `println` accept any `Display` type.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.display.legality-1}

`i64`, `f64`, `boolean`, `String`, and `Char` have built-in `Display` implementations whose
`to_string` methods return their canonical string representations.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl), [82_embedded_core_impls.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/82_embedded_core_impls.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Iterable\<T\>

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}
```

[`T[]` (array) and `Range` (from `..` / `..=`) implement `Iterable<T>`](#spec.runtime.built-in-aspects.iterable-t.legality-1). User-defined types may implement it to be usable in `for-in`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.iterable-t.legality-1}

Arrays and ranges implement `Iterable<T>`; a user-defined type is usable in `for-in` only
when it implements that aspect.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [59_iterable_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/59_iterable_aspect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### From\<S\>

```metel
aspect From<S> {
    fun from(value: S) -> Self;
}
```

[`i64` implements `From<f64>` (truncating cast) and `f64` implements `From<i64>`](#spec.runtime.built-in-aspects.from-s.legality-1). The [`as` operator desugars to `T::from(value)`](types.md#spec.types.type-casting.dynamics-1). User-defined types may implement `From<S>` to enable `as` casts and `?` error coercion.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.from-s.legality-1}

`i64` implements `From<f64>` and `f64` implements `From<i64>`; user-defined `From<S>`
implementations make their target type available for `as` casts and `?` error coercion.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [82_embedded_core_impls.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/82_embedded_core_impls.mtl), [61_propagate_error_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/error_handling/61_propagate_error_coercion.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

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

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.string-methods.dynamics-1}

String utility methods operate on Unicode scalar values; index-based operations are total,
clamping a slice boundary and returning `None` for an absent character or search result
rather than panicking.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [85_string_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/85_string_methods.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>


## Array Methods

`T[]` and `[T; N]` both expose:

| Method    | Signature       | Description                        |
|-----------|-----------------|------------------------------------|
| `.len()`  | `() -> i64`     | Number of elements                 |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.array-methods.dynamics-1}

Calling `.len()` on either `T[]` or `[T; N]` returns its number of elements.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [13_sized_array_extended.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/13_sized_array_extended.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Char Methods

> **Availability:** Since v0.8.0.

| Method / Function         | Signature                        | Description                                  |
|---------------------------|----------------------------------|----------------------------------------------|
| [`u32::from(c)`](#spec.runtime.char-methods.dynamics-1)            | `(Char) -> u32`                  | Unicode scalar value as a `u32`              |
| [`Char::from(n)`](#spec.runtime.char-methods.dynamics-1)           | `(u32) -> Char`                  | Construct from a code point; runtime error if not a valid scalar value |
| `.to_string()`            | `() -> String`                   | Single-character string                      |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.char-methods.dynamics-1}

`u32::from(c)` returns `c`'s Unicode scalar value, and `Char::from(n)` returns the matching
character or raises a runtime error when `n` is not a valid Unicode scalar value. A character's
`to_string()` result is its one-character string.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [81_char.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/81_char.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Core Sum Types

> **Availability:** Core methods since v0.9.0. `.yolo()`, `.ok_or()`, `.map_err()`, and `.ok()` since v0.10.0.

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

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.core-sum-types.dynamics-1}

The listed `Perhaps<T>` and `Result<T, E>` combinators operate on their corresponding sum
variants: transforms preserve the non-selected variant, and predicates report which variant
is present.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [83_perhaps_result_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/83_perhaps_result_methods.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## List\<T\>

> **Availability:** Since v0.9.0.

`List<T>` is the growable collection type in `std::core`, available unqualified.

> **Since v0.12.0: `.set(i, value)`.** Added alongside RFC-0126 — `T[]` becoming an
> immutable borrowed view meant index-assignment through a slice stopped working, and
> `List<T>` had no way to overwrite an element in place at all, so an in-place algorithm
> (a bubble sort, for instance) had no expression until this existed.

| Method / function    | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `List::new()`        | `() -> List<T>`                    | A new empty list                             |
| `List::from(arr)`    | `(T[]) -> List<T>`                 | A list with a copy of the array's elements   |
| `.push(x)`           | `(&var self, T)`                   | Append an element                            |
| `.pop()`             | `(&var self) -> Perhaps<T>`        | Remove and return the last element           |
| `.len()`             | `() -> i64`                        | Number of elements                           |
| `.get(i)`            | `(i64) -> Perhaps<T>`              | Element at index `i`, or `None`              |
| `.set(i, value)`     | `(&var self, i64, T) -> Perhaps<T>`| Overwrite the element at `i`; returns the replaced value, or `None` if `i` is out of bounds |
| `.as_slice()`        | `() -> T[]`                        | The backing array                            |
| `.map(f)`            | `<U>((T) -> U) -> List<U>`         | A new list of `f` applied to each element    |
| `.filter(pred)`      | `((T) -> boolean) -> List<T>`      | The elements satisfying `pred`               |
| `.fold(init, f)`     | `<A>(A, (A, T) -> A) -> A`         | Reduce to a single value, left to right      |
| `.find(pred)`        | `((T) -> boolean) -> Perhaps<T>`   | The first element satisfying `pred`          |
| `.concat(other)`     | `(&List<T>) -> List<T>`            | This list's elements followed by `other`'s   |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.list-t.dynamics-2}

`List<T>` collection and iteration methods are methods of `List<T>` in `std::core`, not
free functions in separate collection or iteration modules.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [84_list_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/84_list_methods.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.list-t.dynamics-1}

`List::from(source)` copies the elements of `source`, so mutating the resulting list
does not mutate that source.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [86_list_from_copies_source.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/86_list_from_copies_source.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## OsError

> **Availability:** Since v0.9.0.

`OsError` is the error type returned by the host-backed standard-library modules
(`std::fs`, `std::process`). It is in `std::core` (available unqualified) and
implements `Display`.

| Method        | Signature       | Description                          |
|---------------|-----------------|--------------------------------------|
| `.message()`  | `() -> String`  | The human-readable error description |

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.oserror.legality-1}

Host-backed fallible APIs use `OsError`, rather than `String`, as their error type; `OsError`
is available from `std::core` and implements `Display`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/std_fs_host_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

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

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-env.dynamics-1}

`std::env` exposes read-only process-environment inspection through `get` and `vars`; it is
an explicitly imported host-backed module, not part of the automatic prelude.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/std_env_host_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

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

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-fs.dynamics-1}

`std::fs` is an explicitly imported host-backed module whose text-oriented file operations
have the signatures listed above and report fallible outcomes as `Result<_, OsError>`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/std_fs_host_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

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

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-process.dynamics-1}

`std::process::run` launches `command` directly with `args`, without shell parsing. A launched
program returns `Ok(ProcessOutput)` even for a non-zero exit status; only failure to launch
returns `Err(OsError)`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/std_process_host_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>
