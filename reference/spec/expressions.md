# Expressions

## Pattern Matching

`match` performs exhaustive pattern matching. All cases must be covered.

```metel
fun main() -> i64 {
    let value := 1;
    match (value) {
        1 => 10,
        _ => 0,
    }
}
```

[Each arm body can be any expression, or a block](#spec.expressions.pattern-matching.legality-1). `return`/`break`/`continue` are
themselves expressions of type `!` (see [Break, Continue, and Return](#break-continue-and-return)
below), so a bare arm body like `1 => return 10` needs no special grammar case —
it's just an ordinary expression arm, like any other:

```metel
// Match arm body forms start here.
fun classify(value: i64) -> i64 {
    loop {
        break match (value) {
            0 => 0,
            1 => return 10,
            _ => { 20 },
        };
    }
}

fun main() -> i64 {
    return classify(0);
}
```

`match` is an expression — all arms must produce the same type:

```metel
fun main() -> i64 {
    let x := 1;
    let label := match (x) {
        0 => "zero",
        1 => "one",
        _ => "other",
    };
    return label.len();
}
```

Arms with blocks follow the same rules as function bodies: [the block's tail expression (if present) is the arm's value; a block with no tail produces `Unit`](#spec.expressions.pattern-matching.dynamics-1).

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let shape := Shape::Circle { radius = 3.0 };
    let desc: String := match (shape) {
        Shape::Circle { radius } => {
            let area := radius * radius;
            (area as i64).to_string()
        },
        Shape::Rectangle { width, height } => "rectangle",
    };
    return desc.len();
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.pattern-matching.legality-1}

A match arm body may be either a single expression or a block, and both forms may appear in
the same `match` expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage7_02_match_arm_blocks.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_02_match_arm_blocks.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.dynamics-1}

A block arm evaluates its statements and then its tail expression, if any; that tail is the
arm's result, while a block with no tail produces `()`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage7_02_match_arm_blocks.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_02_match_arm_blocks.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-2}

Bindings introduced by an arm's pattern are in scope throughout that arm's block body.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage7_02_match_arm_blocks.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_02_match_arm_blocks.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-3}

A `match` expression's scrutinee must be enclosed in parentheses — `match (x) { … }`.
The bare form `match x { … }` is a parse error. A tuple scrutinee's own parentheses
satisfy this (`match (a, b) { … }`), as does the unit literal (`match () { … }`).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0156](../../rfcs/4-implemented/rfc-0156-parenthesize-match-scrutinee.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [match_scrutinee_parenthesized.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/match_scrutinee_parenthesized.mtl), [neg_16_bare_match_scrutinee.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_16_bare_match_scrutinee.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Pattern Kinds

| Pattern | Example | Matches |
|---------|---------|---------|
| Wildcard | `_` | anything, binds nothing |
| Binding | `n` | anything, binds to `n` |
| Literal | `0`, `"hi"`, `true` | exact value |
| Enum variant | `Direction::North`, `North` | unit variant (qualified or, since v0.11.0, bare) |
| Enum with fields | `Shape::Circle { radius }`, `Circle { radius }` | variant, binds fields |
| Struct | `Point { x, y }`, `Token { kind, .. }` | struct, binds named fields |
| Tuple | `(a, b)` | tuple, binds elements |
| Guard | `n if n < 0` | binding + boolean condition |

### Examples

```metel
// Pattern examples start here.
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let shape := Shape::Rectangle { width = 4.0, height = 2.0 };
    let x := -3;
    let point: (i64, i64) := (0, 7);

    let a := match (shape) {
        Shape::Circle { radius } => radius as i64,
        Shape::Rectangle { width, height } => width as i64,
    };

    let b := match (x) {
        0          => 0,
        n if n < 0 => 1,
        _          => 2,
    };

    let c := match (point) {
        (0, 0) => 0,
        (x, 0) => x,
        (0, y) => y,
        (x, y) => x + y,
    };

    return a + b + c;
}
```

### Unqualified variant constructors

> **Since v0.11.0 (RFC-0111).**

A bare variant name may be used where the *expected* type determines which enum is meant —
the expression-position counterpart of "Unqualified variant patterns" below. Both no-field
and fieldful variants participate, and per RFC-0106 the empty-brace spelling `Red {}` is
equally valid:

```metel
enum Colour { Red, Green, Blue }

fun paint(c: Colour) { }
fun favourite() -> Colour { Green }        // return type supplies the expected type

fun main() {
    let c: Colour := Red;                   // annotation supplies it
    paint(Blue);                           // parameter type supplies it
    let p: Perhaps<i64> := Some { value = 5 };
    let q: Perhaps<i64> := None;            // `None` is an ordinary variant, not a literal
}
```

Resolution is type-directed against the expected type only — never a lexical import of
variant names — so two enums may both declare `Red` with no ambiguity.

**A bare variant is a last resort, never a shadowing mechanism.** It resolves only when the
name means nothing else in scope — not a binding, and not a unit struct (`struct Red {}` and
`enum C { Red }` may coexist, and `Red` then means the struct even where a `C` is expected;
write `C::Red`).

**An in-scope binding wins over a variant of the same name.** This is the opposite of
pattern position, and deliberately so: a pattern *introduces* names, so a bare identifier
there is always the variant, while an expression *uses* names and must resolve to the
nearest binding or lexical scoping breaks.

```metel
fun demo(Red: i64) -> i64 {
    return Red;          // the parameter, not Colour::Red
}
```

**Where no expected type exists, the bare form does not resolve** and the name is reported
as undefined ([T0003](../error-codes.md#t0003--undefined-name)) — there is deliberately no
search for "some enum, somewhere, declaring `Red`". Qualify (`Colour::Red`) or ascribe
(`Red: Colour`). This affects an unannotated `let x = Red;`, an argument to a *generic*
callee (whose parameter types are not known until the arguments are), and the body of a
closure with no declared return type. `None` without a determinable type keeps its existing
[T0002](../error-codes.md#t0002--annotation-required) "add a type annotation" diagnostic
rather than degrading to T0003.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-1}

A bare no-field or fieldful enum variant is valid in expression position when the
expected type determines its enum and no binding or declaration of that name is in scope.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_unqualified_variant_constructors.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/41_unqualified_variant_constructors.mtl), [42_variant_deferral_resolves.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/42_variant_deferral_resolves.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-2}

An in-scope binding of the same name takes precedence over a bare enum variant in
expression position.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_unqualified_variant_constructors.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/41_unqualified_variant_constructors.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-3}

Expected types from an annotation, return type, monomorphic call parameter, or
struct-literal field may direct bare-variant resolution.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_unqualified_variant_constructors.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/41_unqualified_variant_constructors.mtl), [42_variant_deferral_resolves.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/42_variant_deferral_resolves.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-4}

Without an expected enum type, a bare variant does not resolve by searching other enums;
the program must qualify or ascribe it.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage6_neg_12_unresolved_variant_deferral.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/enums/stage6_neg_12_unresolved_variant_deferral.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Unqualified variant patterns

> **Since v0.11.0 (RFC-0107).**

A match arm may name an enum variant without its `Enum::` prefix when the variant
resolves unambiguously against the scrutinee's known enum type. The candidate enum is
*only* the scrutinee's own type — this is type-directed resolution, not a lexical import
of variant names — so there is no cross-enum collision to resolve:

```metel
enum Colour { Red, Green, Blue }

fun name(c: Colour) -> String {
    match (c) {
        Red   => "red",
        Green => "green",
        Blue  => "blue",
    }
}
```

Fieldful variants may also be written bare:

```metel
fun unwrap_or_zero(v: Perhaps<i64>) -> i64 {
    match (v) {
        Some { value } => value,
        None           => 0,
    }
}
```

Resolution happens during type-checking, against the scrutinee's concrete type. If that
type is not a known enum at the point of matching (for example an abstract, aspect-bounded
type parameter inside a generic function), a bare identifier is an ordinary binding, as
before. A bare identifier that exactly names a no-field variant of the scrutinee's enum is
*always* the variant, never a fresh binding — use `_` or a differently-named binding for a
catch-all. The fully-qualified form (`Colour::Red`) remains valid everywhere; qualification
is optional, not removed.

### Struct patterns

> **Since v0.13.0.**

A named struct's fields may be destructured directly in a match arm, the same
bare-field syntax a struct literal uses:

```metel
struct Point { x: i64, y: i64 }

fun magnitude_squared(p: Point) -> i64 {
    match (p) {
        Point { x, y } => x * x + y * y,
    }
}
```

[Naming every field is required unless the pattern ends in `..`](#spec.expressions.struct-patterns.legality-1), which
matches the struct against any value of that type regardless of the fields it doesn't
name:

```metel
struct Token { kind: i64, span: i64, offset: i64 }

fun kind_and_span(t: Token) -> i64 {
    match (t) {
        Token { kind, span, .. } => kind + span,
    }
}
```

A field's own visibility applies the same way it does to ordinary field access — see
[Visibility](modules.md#visibility). An external pattern (outside the struct's declaring
module) that names a private field is a `T0009` visibility error; the field must be
omitted, which requires `..`.

A struct pattern's sub-patterns are always plain field bindings — there is no
`field: subpattern` form for matching a field's own value against something other than a
bare name. An unguarded struct-pattern arm is exhaustive for its struct type on its own:
a struct has exactly one shape, so naming every field (or every field plus `..`) always
covers it.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.struct-patterns.legality-1}

A struct pattern with no trailing `..` must name every field of the struct; one that
ends in `..` may name any subset, including none.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [struct_pattern_matches_all_fields.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/struct_pattern_matches_all_fields.mtl), [struct_pattern_missing_field_without_rest_is_t0001.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/struct_pattern_missing_field_without_rest_is_t0001.mtl), [struct_pattern_rest_omits_remaining_fields.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/struct_pattern_rest_omits_remaining_fields.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Matching through a reference

> **Since v0.11.0 (RFC-0108).**

A scrutinee of reference type (`&T`, `&var T`, and chains thereof) matches against `T`'s
own patterns — reference layers are peeled before pattern resolution, the same way field
access and method dispatch already auto-dereference:

```metel
enum Colour { Red, Green, Blue }

fun name(c: &Colour) -> String {
    match (c) {
        Colour::Red   => "red",
        Colour::Green => "green",
        Colour::Blue  => "blue",
    }
}
```

Bindings introduced by a pattern matched through a reference copy the referent, following
the ordinary type-directed copy rule (see [Types](types.md#reading-a-value-out-of-a-reference)).

Reference-transparency and unqualified variants compose — peeling happens first, so a bare
variant resolves against the referent's enum:

```metel
fun name(c: &Colour) -> String {
    match (c) {
        Red   => "red",     // c is peeled &Colour -> Colour, then Red resolves against Colour
        Green => "green",
        Blue  => "blue",
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-1}

A no-field enum variant may be written as a bare match pattern when it is a variant of
the scrutinee's known enum type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl), [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-2}

A fieldful enum variant may likewise omit its enum prefix in a match pattern.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-3}

Bare-variant pattern resolution is directed only by the scrutinee's concrete enum type;
when that type is not a known enum, the identifier remains an ordinary binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-4}

A bare variant tag is not a catch-all binding and therefore does not satisfy match
exhaustiveness for the enum's other variants.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_17_bare_variant_is_not_catchall.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/enums/neg_17_bare_variant_is_not_catchall.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-5}

When a bare identifier exactly names a no-field variant of the scrutinee enum, it is the
variant rather than a fresh binding; `_` or another name is required for a catch-all.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-6}

The fully qualified enum-variant pattern remains valid wherever its bare spelling is
valid.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-7}

`None` in pattern position is resolved by the ordinary unqualified-variant rule for a
`Perhaps<T>` scrutinee.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [40_unqualified_variant_patterns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/enums/40_unqualified_variant_patterns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-1}

A `&T`, `&var T`, or nested-reference scrutinee is accepted against the ordinary
patterns of its referent type `T`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-2}

Type checking a match uses the reference-peeled scrutinee type when checking its
patterns.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-3}

Exhaustiveness checking a match uses the reference-peeled scrutinee type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-1}

At runtime, matching through a reference compares the patterns with the fully dereferenced
scrutinee value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-2}

Bindings introduced while matching through a reference copy values from the peeled
referent under the ordinary type-directed copy rule.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-3}

For a reference scrutinee, `match reference` and `match *reference` compare patterns
against the same referent value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-4}

Reference peeling happens before unqualified-variant resolution, so a bare variant is
resolved against the referent's enum type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_match_through_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/10_match_through_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-5}

Reference transparency is limited to the match-scrutinee position and does not change
the types required in call arguments or other non-match contexts.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_13_reference_scrutinee_peel_does_not_generalize_to_call_args.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/enums/neg_13_reference_scrutinee_peel_does_not_generalize_to_call_args.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

---

## Control Flow

### If / Else

```metel
fun main() -> i64 {
    let condition := false;
    let other := true;
    if (condition) {
        return 1;
    } else if (other) {
        return 2;
    } else {
        return 3;
    }
}
```

`if` is also an expression (both branches must produce the same type):

```metel
fun main() -> i64 {
    let x := 1;
    let label := if (x > 0) { "positive" } else { "non-positive" };
    return label.len();
}
```

**Braceless bodies.** A single expression may be used as the branch body without braces:

```metel
fun print_state() { }

fun main() -> i64 {
    let debug := true;
    let flag := false;
    let value_a := 10;
    let value_b := 20;
    if (debug) print_state();
    let x := if (flag) value_a else value_b;
    return x;
}
```

The braceless form desugars to a single-expression block. Three restrictions apply:

1. **Arm style must be consistent.** Both the `then` and `else` arms must use the same style — either both braced or both braceless. Mixing is a parse error.
2. **Dangling-else is forbidden.** If the outer body is braceless, the body expression must not itself be an `if–else`. Use braces on the outer body to resolve the ambiguity.
   ```metel
   fun main() -> i64 {
       let a := true;
       let b := false;
       if (a) if (b) { return 1; }
       if (a) { if (b) { return 2; } else { return 3; } }
       return 4;
   }
   ```
   <!-- doc-example: expect-fail reason="demonstrates the forbidden dangling-else case -- the parse error is the point" -->
   ```metel
   fun main() {
       let a := true;
       let b := false;
       if (a) if (b) { return; } else { return; }
   }
   ```
3. **No semicolon between braceless arms.** Write `if (c) a else b;`, not `if (c) a; else b;` — the `;` terminates the statement before the `else`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-1}

An `if` branch may be a single braceless expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [47_braceless_if.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/47_braceless_if.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-2}

A braceless `if` without `else` has type `Unit` and may occur wherever a `Unit`-typed
expression is accepted.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [88_braceless_if_no_else_in_expression_position.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/88_braceless_if_no_else_in_expression_position.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-3}

A braceless `if`-`else` is an expression when its two branches have the same type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [47_braceless_if.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/47_braceless_if.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-4}

A braceless outer branch cannot contain an inner `if`-`else`; braces are required to
avoid dangling-`else` ambiguity.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_19_braceless_if_dangling_else.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/neg_19_braceless_if_dangling_else.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-5}

The `then` and `else` branches of an `if`-`else` must use the same body style: both
braced or both braceless.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_20_braceless_if_mixed_arms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/neg_20_braceless_if_mixed_arms.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### While

```metel
fun main() -> i64 {
    var n := 3;
    var total := 0;
    while (n > 0) {
        total += n;
        n -= 1;
    }
    return total;
}
```

### For

```metel
fun main() -> i64 {
    var total := 0;
    for (var i := 0; i < 4; i += 1) {
        total += i;
    }
    return total;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.for.legality-1}

A C-style `for` initializer may declare a mutable loop-local binding with `var`; that
binding may be reassigned by the loop body or step expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [16_for_loop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/16_for_loop.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### For-In

> **Availability:** Array and range iteration since v0.1.0. User-defined `Iterable<T>` implementations since v0.4.0.

[`for-in` works on any type implementing the `Iterable<T>` aspect](runtime.md#spec.runtime.built-in-aspects.iterable-t.legality-1). The loop variable
receives type `T`. `T[]`, `[T; N]` (array and fixed-size array), and `Range` (produced by
`..` and `..=`) implement `Iterable<T>` by default. A `T[]` loop binding denotes an
element of an immutable borrowed view: with move checking enabled, a non-`Copy` binding
may be read or borrowed but not consumed. User-defined types can be made iterable by
implementing `Iterable<T>`. The loop binding is immutable by default and [may be made
loop-locally mutable with `var`](#spec.expressions.control-flow.for-in.legality-1):

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}

fun main() -> i64 {
    return 0;
}
```

```metel
fun main() -> i64 {
    let collection := [1, 2, 3];
    var total := 0;
    for (let item in collection) { total += item; }
    for (var item in collection) {
        item += 1;
        total += item;
    }
    for (let i in 0..10) { total += i; }
    for (let i in 0..=10) { total += i; }
    return total;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.for-in.legality-1}

A `for-in` binding may be declared with `var`, making that iteration's loop-local binding
mutable.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [17_for_in.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/17_for_in.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.for-in.dynamics-1}

Reassigning a `var` `for-in` binding changes only that iteration's loop-local binding and
does not write the replacement value back into the iterated source.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [17_for_in.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/17_for_in.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### References

> **Availability:** Since v0.10.0.

References provide explicit aliasing.

```metel
fun main() -> i64 {
    var n := 1;
    let p: &var i64 := &var n;
    *p := 4;   // write-through: mutate the referent via explicit deref
    return p; // type-directed copy: reads the value out at `return`
}
```

Rules:

- `&expr` creates a shared reference `&T` where `expr` is an addressable lvalue
- `&var x` creates an exclusive reference `&var T` where `x` is a `var` addressable lvalue
- `*p` dereferences a reference — reading the referent, or, as an assignment target
  (`*p = v`), writing through to it (see "Dereference" below)
- reading a plain value out of a reference with no field/method involved can also go
  through type-directed copy (see
  [Types — Reading a value out of a reference](types.md#reading-a-value-out-of-a-reference)),
  and field access, index, and method dispatch go through auto-deref (below)
- assigning to a reference-typed binding (`p = v`) **rebinds** it, like any other type;
  `*p = v` is the spelling that writes through

Addressable places for both `&` and `&var` include named bindings (`x`), struct field access (`s.field`), tuple element access (`t.0`), array indexing (`arr[i]`), a dereference (`*p` — so `&*p` is a reborrow that shares the referent's storage), and chains thereof (`nested.outer.field`, `t.1.0`).

> **Since v0.12.0: `&<rvalue>` / `&var <rvalue>` — temporary lifetime extension.**
> Neither `&expr` nor `&var expr` requires `expr` to be an addressable place anymore: a
> literal, a call result, a struct or enum construction, or any other non-addressable
> expression is materialized into a fresh, independent cell and referenced directly
> (matching Rust and C++: `foo(&Vec::new())`, `foo(&var Vec::new())` — both need no
> intermediate binding). Sound for both forms — nothing outside the expression can ever
> alias the cell, so a mutable reference to it can never conflict with anything else.
>
> ```metel
> fun takes_ref(l: &List<i64>) -> i64 { l.len() }
> fun bump(x: &var i64) -> i64 { *x := *x + 1; *x }
> fun main() -> i64 {
>     let a := takes_ref(&List::from([1, 2, 3]));   // no `let` needed for the argument
>     let b := bump(&var 41);                        // &var works on a temporary too
>     return a + b;
> }
> ```

`&var` requires the operand to be a `var` binding — applying it to a plain `let` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)). `&var` on a lvalue path ([a struct field](#spec.expressions.references.dynamics-1), [tuple element](#spec.expressions.references.dynamics-2), [array element](#spec.expressions.references.dynamics-3), or [chain of projections](#spec.expressions.references.dynamics-4)) produces a true exclusive reference with write-back semantics, matching `&var` on a named binding exactly — writes through it propagate to the original storage location (RFC-0045, already implemented; this section previously described `&var struct.field` as a non-propagating snapshot, which was the *pre*-RFC-0045 behavior and had never been updated to match). `&` on a field or element also aliases the original storage through the same path machinery, so later writes to the binding remain visible through the shared reference; it is still read-only, so writing through `&T` remains rejected. Reborrowing preserves this: `&*r` shares whatever storage `r` names, and reborrowing a `&var T` as `&T` downgrades to shared. The reverse is rejected — `&var *r` where `r: &T` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)), since a shared reference never grants write access.

Tuple elements are assignable like struct fields and array elements — `t.0 = v`, `t.0 += v`,
and nested or chained forms (`s.pair.0`, `t.1.0`), including through a `&var` reference. An
out-of-range index is a type error ([T0003](../error-codes.md#t0003--undefined-name)), and a
shared `&` grants no write access ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)).

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-1}

Evaluating `&var value.field` creates an exclusive reference to that field. A write through
the reference updates the corresponding field in `value`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-2}

Evaluating `&var value.n` creates an exclusive reference to tuple element `n`. A write
through the reference updates that element and leaves the other tuple elements unchanged.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-3}

Evaluating `&var values[index]` creates an exclusive reference to the selected array
element. A write through the reference is observable through subsequent indexing.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-4}

Evaluating `&var` over a chain of addressable projections creates an exclusive reference
to the chain's leaf storage. A write through the reference updates that original leaf.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

#### Dereference

> **Changed in v0.11.0 (RFC-0110): `*p` added; assignment to a reference-typed binding now rebinds it, use `*p = v` to write through.**

`*expr` dereferences a `&T`/`&var T`. As an expression it reads the referent; as an
assignment target, `*p = v` writes through a `&var T`. Applying `*` to a non-reference is
a type error ([T0002](../error-codes.md#t0002--annotation-required)).

Auto-deref covers **selectors only** — field access, indexing, and method dispatch, where
the target of the operation is unambiguous. Everywhere else, reading through a reference
is spelled explicitly:

```metel
fun add(x: i64, y: i64) -> i64 { x + y }

fun main() -> i64 {
    let a := 3;
    let b := 4;
    let p: &i64 := &a;
    let q: &i64 := &b;
    return add(*p, *q) + (*p + *q);   // explicit: call arguments and operands
}
```

Bare assignment to a reference-typed binding rebinds it rather than writing through, so a
`&var T` can be repointed:

```metel
fun main() -> i64 {
    var a := 1;
    var b := 2;
    var p: &var i64 := &var a;
    p := &var b;   // repoint: p now refers to b (p is `var`) — a stays 1
    *p := 5;       // write-through: b becomes 5
    return a + b; // 1 + 5
}
```

Field- and index-path targets keep writing through with no `*` needed — `s.field = v` and
`arr[i] = v` have no competing "rebind" reading, so they are unambiguous as they stand:

```metel
struct Point { x: i64, y: i64 }

fun main() -> i64 {
    var q := Point { x = 5, y = 7 };
    let qp: &var Point := &var q;
    qp.y := 99;        // field write-through — no `*` needed
    var xs := [1, 2, 3];
    let xp: &var [i64; 3] := &var xs;
    xp[0] := 9;        // index write-through — no `*` needed
    return q.y + xs[0];
}
```

`*(obj.field) = v` and `obj.field = v` are synonyms; for a bare identifier target, `*p = v`
is the only spelling that writes through.

Field access, field assignment, indexing, and method dispatch auto-dereference through a
reference:

```metel
struct Counter {
    value: i64,
}

extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}

fun main() -> i64 {
    var counter := Counter { value = 0 };
    let p: &var Counter := &var counter;
    p.increment();    // auto-deref: equivalent to accessing through the reference directly
    p.value := 1;      // auto-deref field assign; the reference binding need not be var
    return p.value;   // auto-deref field read
}
```

Function references (`&() -> T` and `&var () -> T`) are callable directly, the same way:

```metel
fun main() -> i64 {
    let f := () -> { return 42; };
    let r: &() -> i64 := &f;
    return r();       // auto-deref: calls through the reference directly
}
```

This applies uniformly: a closure or named function stored behind a reference can be called as if it were the function value itself. A common use is passing arrays of function references:

```metel
fun apply_all(fns: Array<&() -> ()>) {
    for (let f in fns) {
        f();          // auto-deref each element
    }
}
```

Field access, method dispatch, and calling through a reference all chain through
multiple reference layers, not just one — `rr: &&var Counter` auto-derefs through both
levels to reach the `Counter` for a field read, a field write, or a method call
(`&var self` included: a shared outer layer doesn't remove the write access the inner
`&var` layer carries, it just adds a read-only step to reach it):

```metel
struct Counter { value: i64 }

extend Counter {
    fun increment(&var self) { self.value += 1; }
}

fun main() -> i64 {
    var c := Counter { value = 0 };
    let p: &var Counter := &var c;
    let rr: &&var Counter := &p;
    rr.increment();   // auto-deref through both layers
    return rr.value;  // likewise for a field read
}
```

Indexing, argument passing, and assignment remain ordinary reference operations — none of them are the value-extraction case (see `types.md`), so none require type-directed copy.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-5}

Evaluating `&place` or `&var place` produces, respectively, a shared or exclusive
reference to the addressed storage; an exclusive reference can write through to that
same storage.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [04_write_through_thin_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/04_write_through_thin_reference.mtl), [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-6}

Field access, field assignment, method dispatch, and calls through a reference
auto-dereference through every reference layer necessary to reach their receiver.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [09_auto_deref_field_access_through_chain.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/09_auto_deref_field_access_through_chain.mtl), [14_mut_field_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-1}

The unary `*` operator requires a shared or exclusive reference operand. Applying it to a
non-reference is a `T0002` type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_12_deref_non_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/neg_12_deref_non_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-2}

Writing through `*place` requires an `&var T` reference; a shared `&T` never grants
write access.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [08_write_through_reference_chain.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/08_write_through_reference_chain.mtl), [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl), [neg_11_write_through_shared_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/neg_11_write_through_shared_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-7}

Evaluating `*reference` reads its referent. Explicit dereference is available in every
expression position, while selector operations retain their ordinary auto-dereference.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl), [neg_06_no_read_copy_at_call_argument.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/neg_06_no_read_copy_at_call_argument.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-8}

Each leading `*` reads or writes through exactly one reference layer. A bare assignment
to a reference-typed binding instead rebinds that binding when it is mutable.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [08_write_through_reference_chain.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/08_write_through_reference_chain.mtl), [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-9}

An assignment through a dereference writes the referenced storage; after a mutable
reference binding is rebound, a later dereference writes the new referent.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [08_write_through_reference_chain.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/08_write_through_reference_chain.mtl), [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-10}

Field and index assignment through a reference remains implicit because those targets
are unambiguous selectors; `*(object.field) = value` and `object.field = value` have the
same write effect.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [11_explicit_deref.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/references/11_explicit_deref.mtl), [87_tuple_assign_paths.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/types/87_tuple_assign_paths.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-11}

Taking `&*reference` or `&var *reference` reborrows the storage named by the dereference;
an exclusive reborrow may write that same storage.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [06_addressable_places.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/addressability/06_addressable_places.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Loop

[`loop` creates an infinite loop](types.md#spec.types.never-type.dynamics-1). It is the only loop form that can produce a value:

```metel
fun main() -> i64 {
    let result := loop {
        break 42;
    };
    return result;
}
```

**Typing rules:**

- `loop { break expr; }` has type `T` where `expr: T`. All `break` arms must produce the same type; a `break` expression is [typechecked against its enclosing loop value type](types.md#spec.types.type-inference.legality-2).
- `loop { }` — a loop with no reachable `break` — has type `!` (Never). See [Never Type](types.md#never-type).

### Break, Continue, and Return

> **Availability:** Since v0.10.0.

[`return`, `break`, and `continue` are expressions of type `!`](types.md#spec.types.never-type.dynamics-1) (Never — see
[Never Type](types.md#never-type)), not statements. Since `!` is a subtype of
every type, they're valid anywhere an expression is valid — a block tail with
no trailing `;`, a braceless `if`-arm, a match-arm body, or nested inside
another expression — not just as a semicolon-terminated statement on its own
line:

```metel
fun pick(ok: boolean) -> i64 {
    if (ok) return 42;   // braceless if-arm, no braces needed
    0
}

fun compute() -> i64 {
    var i := 0;
    loop {
        i := i + 1;
        if (i == 5) {
            break i * 10   // loop-body tail, no trailing `;`
        }
    }
}

fun classify(value: i64) -> i64 {
    match (value) {
        0 => 0,
        1 => return 10,   // match-arm body, same as any other expression arm
        _ => 20,
    }
}

fun nested(c: boolean) -> i64 {
    let x := if (c) return 99 else 0;   // nested expression position
    x
}
```

[`break` exits the innermost loop](#spec.expressions.control-flow.break-continue-and-return.dynamics-1); `break expr` exits a `loop` and produces
`expr` as the loop's value (`break` with no value produces `Unit`).
[`continue` skips to the next iteration of the innermost loop](#spec.expressions.control-flow.break-continue-and-return.dynamics-2). `return`/
`return expr` [returns from the enclosing function](#spec.expressions.control-flow.break-continue-and-return.dynamics-3), using the function's
declared return type (or `Unit`, if omitted):

```metel
fun returns_unit() {
    return;
}

fun returns_value() -> i64 {
    return 42;
}

fun main() -> i64 {
    returns_unit();
    return returns_value();
}
```

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-1}

`break` transfers control out of the innermost enclosing loop. In a value-producing
`loop`, `break expr` supplies that loop's result and bare `break` supplies `()`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [13_loop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/13_loop.mtl), [91_nested_break_propagation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/91_nested_break_propagation.mtl), [stage6_09_nested_loop_break.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/control_flow/stage6_09_nested_loop_break.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-2}

`continue` abandons the current iteration of the innermost enclosing loop and begins its
next iteration.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [13_loop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/13_loop.mtl), [stage6_10_loop_control_statements.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/control_flow/stage6_10_loop_control_statements.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-3}

`return expr` transfers control out of the enclosing function with `expr` as its result;
bare `return` returns `()`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [81_return_exits_early_and_bare_return_is_unit.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/81_return_exits_early_and_bare_return_is_unit.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>
