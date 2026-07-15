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
export    extend    false     for       fun       if        impl
import    let       loop      match     or        public    return
root      self      std       struct    super     true      var
where     while
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

An unsuffixed integer literal defaults to `i64` when no context constrains its type.

**Floats:**
```metel
3.14
2.0
```

A suffix pins the literal to a specific sized float type:

```metel
3.14f32     // f32
2.0f64      // f64
```

An unsuffixed float literal defaults to `f64` when no context constrains its type.

Integer and float are distinct types and do not implicitly coerce.

**Polymorphic literal coercion.** When the surrounding context provides a numeric type — a `let` annotation, a function parameter type, a struct field type, or a return type — an unsuffixed literal adopts that type automatically:

```metel
let x: i32  = 10;       // 10 is i32
let y: u8   = 255;      // 255 is u8
let z: f32  = 3.14;     // 3.14 is f32

fun add(a: i32, b: i32) -> i32 { a + b }
let r = add(1, 2);      // 1 and 2 are i32

struct Pixel { r: u8, g: u8, b: u8 }
let p = Pixel { r: 255, g: 128, b: 0 };  // fields are u8
```

Arithmetic and comparison operators propagate the type from a sized operand to an unsuffixed sibling:

```metel
let x: i32 = 10i32;
let y = x + 5;          // 5 adopts i32; y is i32
assert(x > 5);          // 5 adopts i32
```

> **Availability:** Sized literal suffixes and polymorphic literal coercion since v0.8.0.

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

> **Availability:** `Char` since v0.8.0.

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

> **Availability:** Since v0.7.0.

The expression inside `${…}` may be any expression whose type implements the `Display` aspect (i.e. has a `.to_string()` method). The placeholder desugars to `.to_string()` concatenated with the surrounding literal fragments using `+`. String literals may appear inside `${…}`:

```metel
let x = "${if (true) { "yes" } else { "no" }}";
```

**String concatenation.** Two `String` values may be joined with `+`:

```metel
let full = "hello" + ", " + "world";   // "hello, world"
```

> **Availability:** Since v0.7.0.

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
