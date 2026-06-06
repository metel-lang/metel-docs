# Lexical Structure

## Comments

```metel
// Single-line comment

/* Multi-line
   comment */
```

Multi-line comments do not nest.

## Identifiers

Identifiers start with a letter (`a–z`, `A–Z`) or underscore, followed by any combination of letters, digits, or underscores.

```
identifier := [a-zA-Z_][a-zA-Z0-9_]*
```

By convention:
- Types, structs, enums, and aspects use `PascalCase`
- Variables, functions, and fields use `snake_case`

## Keywords

```
and       as        aspect    break     continue  else      enum
export    false     for       fun       if        impl      import
let       loop      match     mut       or        pub       return
root      self      std       struct    super     true      where
while
```

## Literals

**Integers** — decimal, with optional `_` separators:
```metel
42
1_000_000
```

A suffix pins the literal to a specific sized type:

```metel
42i32       // i32
255u8       // u8
1_000i64    // i64
```

An unsuffixed integer literal defaults to `i64` (`Int`).

**Floats:**
```metel
3.14
2.0
```

A suffix pins the literal to a specific sized float type:

```metel
3.14f32     // f32
2.0f64      // f64 (same as Float)
```

An unsuffixed float literal defaults to `f64` (`Float`).

Integer and float are distinct types and do not implicitly coerce.

> Sized literal suffixes: since v0.8.0 (RFC-0007).

**Characters** — single-quoted Unicode scalar values:

```metel
'a'
'\n'
'\t'
'\\'
'\''
'\u{1F600}'
```

The type of a character literal is `Char`.

> `Char` type: since v0.8.0 (RFC-0007).

**Strings** — double-quoted UTF-8:

| Sequence | Meaning         |
|----------|-----------------|
| `\n`     | Newline         |
| `\t`     | Tab             |
| `\\`     | Backslash       |
| `\"`     | Double quote    |
| `\r`     | Carriage return |

**String interpolation.** A string literal may contain one or more `${expr}` placeholders:

```metel
let name = "world";
let msg = "hello, ${name}!";       // "hello, world!"
let n = 42;
let s  = "n=${n}";                 // "n=42"
```

> *Since v0.7.0.*

The expression inside `${…}` may be any expression whose type implements the `Display` aspect (i.e. has a `.to_string()` method). The placeholder desugars to `.to_string()` concatenated with the surrounding literal fragments using `+`. String literals may appear inside `${…}`:

```metel
let x = "${if (true) { "yes" } else { "no" }}";
```

**String concatenation.** Two `String` values may be joined with `+`:

```metel
let full = "hello" + ", " + "world";   // "hello, world"
```

> *Since v0.7.0.*

**Booleans:** `true`, `false`

**Absence literal:** `None`

## Operators

| Category        | Operators                                     |
|-----------------|-----------------------------------------------|
| Arithmetic      | `+`  `-`  `*`  `/`  `%`                       |
| Compound assign | `+=`  `-=`  `*=`  `/=`  `%=`                  |
| Comparison      | `==`  `!=`  `<`  `<=`  `>`  `>=`              |
| Logical         | `&&`  `\|\|`  `!`  (`and` / `or` as aliases)  |
| Assignment      | `=`                                           |
| Error prop      | `?`                                           |
| Type cast       | `as`                                          |
| Path            | `::`                                          |
| Range           | `..`  `..=`  (for use in `for-in` only)       |
