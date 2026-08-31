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
as        aspect    break     continue  else      enum      export
extend    false     for       fun       if        impl      import
let       loop      match     public    return    root      self
std       struct    super     true      var       where     while
```

## Literals

**Integers** — decimal, with optional `_` separators:
```metel
42
1_000_000
```

A suffix [pins the literal to a specific sized type](#spec.lexical.literals.legality-1):

```metel
42i32       // i32
255u8       // u8
1_000i64    // i64
```

An unsuffixed integer literal [defaults to `i64`](types.md#spec.types.sized-numeric-types.legality-3) when no context constrains its type.

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

An unsuffixed float literal [defaults to `f64`](types.md#spec.types.sized-numeric-types.legality-3) when no context constrains its type.

Integer and float are [distinct types and do not implicitly coerce](#spec.lexical.literals.legality-3).

**Polymorphic literal coercion.** When the surrounding context provides a numeric type — a `let` annotation, a function parameter type, a struct field type, or a return type — an unsuffixed literal [adopts that type automatically](types.md#spec.types.sized-numeric-types.legality-3):

```metel
let x: i32  := 10;       // 10 is i32
let y: u8   := 255;      // 255 is u8
let z: f32  := 3.14;     // 3.14 is f32

fun add(a: i32, b: i32) -> i32 { a + b }
let r := add(1, 2);      // 1 and 2 are i32

struct Pixel { r: u8, g: u8, b: u8 }
let p := Pixel { r = 255, g = 128, b = 0 };  // fields are u8
```

Arithmetic and comparison operators propagate the type from a sized operand to an unsuffixed sibling:

```metel
let x: i32 := 10i32;
let y := x + 5;          // 5 adopts i32; y is i32
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

The type of a character literal [is `Char`](#spec.lexical.literals.legality-5).

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
let name := "world";
let msg := "hello, ${name}!";       // "hello, world!"
let n := 42;
let s  := "n=${n}";                 // "n=42"
```

> **Availability:** Since v0.7.0.

The expression inside `${…}` may be any expression whose type implements the `Display` aspect (i.e. has a `.to_string()` method). The placeholder desugars to `.to_string()` concatenated with the surrounding literal fragments using `+`. String literals may appear inside `${…}`:

```metel
let x := "${if (true) { "yes" } else { "no" }}";
```

**"Any expression" is deliberate, and includes control flow, closures, and side effects.**
Because `${…}` re-parses its content as an ordinary expression, and `if`/`match`/`loop` and
immediately-invoked closures are all ordinary expressions, a `${…}` placeholder is not
limited to "format an already-computed value" — a loop, a mutation, or a call with an
observable effect can run as a side effect of constructing the string. This is a deliberate
design choice ([metel-core#704](https://github.com/metel-lang/metel-core/issues/704)),
not an oversight: restricting `${…}` to calls only would break idiomatic usage this corpus
already depends on (the `if`/`else` example above), for a purity guarantee the rest of the
language does not otherwise make today. This puts Metel's interpolation with Kotlin's,
Swift's, and C#'s full-expression model rather than Rust's macro-based one — Rust needs
`format!` to be a macro because it has no string-literal grammar rule of its own to attach
interpolation to; Metel does, so no macro workaround is needed.

> This is not necessarily permanent. Once an effect system exists, whether an
> effect-performing call should be allowed inside `${…}` is an open design question —
> not a soundness one, since effect-row inference sees the fully lowered form regardless
> of whether the effectful call sits inside a literal or not, but a discoverability one: a
> `${…}` site reads as data, and nothing marks it as a place a computation can suspend and
> hand control to a handler. Two narrower restrictions (comptime-only, place-expressions-only)
> are already ruled out against the current corpus; an effect-axis restriction specifically —
> `${…}` may not perform an effect — is the only one that would remain viable, and it is
> only expressible once an effect system lands, so today's full-expression scope holds by
> default until then. See `algebraic-effects.md` §15 and Open Question 7 (active design
> report, not yet an RFC).

```metel
fun side_effect() -> i64 {
    println("side effect!");
    7
}

fun main() {
    println("start ${side_effect()} end");
}
// prints:
//   side effect!
//   start 7 end
```

The call inside `${…}` runs — and its own `println` fires — while the outer string is still
being constructed, before `println("start ${side_effect()} end")`'s own argument is even
fully evaluated. Per the Dynamic Semantics rules below, each placeholder's expression is
evaluated exactly once, in source order, with the same evaluation semantics as anywhere
else `expr` is legal.

**String concatenation.** Two `String` values may be joined with `+`:

```metel
let full := "hello" + ", " + "world";   // "hello, world"
```

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.lexical.literals.dynamics-1}

A string literal may contain `${expr}` placeholders; each placeholder's expression is
rendered to text and the result is a `String`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0010](../../rfcs/4-implemented/rfc-0010-string-interpolation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.lexical.literals.dynamics-2}

Placeholder expressions are evaluated once each, in source order.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0010](../../rfcs/4-implemented/rfc-0010-string-interpolation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [86_interpolation_evaluation_order.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/86_interpolation_evaluation_order.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.lexical.literals.dynamics-3}

Interpolation combines literal fragments and rendered placeholder values using ordinary
string-concatenation semantics.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0010](../../rfcs/4-implemented/rfc-0010-string-interpolation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.lexical.literals.dynamics-4}

Within a string literal, `\${` produces the literal characters `${`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0010](../../rfcs/4-implemented/rfc-0010-string-interpolation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [38_builtins.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/38_builtins.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.lexical.literals.legality-1}

An integer literal with an integer suffix has the suffix's sized integer type; a float
literal with a float suffix has the suffix's sized float type.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [02_sized_int_literals.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/literals/02_sized_int_literals.mtl), [03_sized_float_literals.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/literals/03_sized_float_literals.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.lexical.literals.legality-3}

An integer literal and a float literal do not implicitly coerce between integer and float
types.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage3_neg_12_suffixed_integer_not_float.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_12_suffixed_integer_not_float.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.lexical.literals.legality-5}

A character literal has type `Char`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [81_char.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/builtins/81_char.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

> **Availability:** Since v0.7.0.

**Booleans:** `true`, `false`

**Absence literal:** `None`

## Operators

| Category        | Operators                                     |
|-----------------|-----------------------------------------------|
| Arithmetic      | `+`  `-`  `*`  `/`  `%`                       |
| Compound assign | `+=`  `-=`  `*=`  `/=`  `%=`                  |
| Comparison      | `==`  `!=`  `<`  `<=`  `>`  `>=`              |
| Logical         | `&&`  `\|\|`  `!`                             |
| Assignment      | `=`                                           |
| Error prop      | `?`                                           |
| Type cast       | `as`                                          |
| Path            | `::`                                          |
| Range           | `..`  `..=`  (for use in `for-in` only)       |
