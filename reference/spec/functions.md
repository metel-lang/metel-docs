# Functions

```metel
fun add(a: i64, b: i64) -> i64 {
    return a + b;
}

fun main() -> i64 {
    return add(2, 3);
}
```

## Named Function Declarations

[Parameter type annotations are optional when types can be inferred from context](#spec.functions.named-function-declarations.legality-2). The return type follows `->` and is also optional — [a function with no return annotation and no `return expr;` returns `()`](#spec.functions.named-function-declarations.dynamics-1). `return expr;` and bare `return;` are both valid.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.named-function-declarations.legality-1}

Named function declarations begin with `fun`; `fun` is not an anonymous-function
expression introducer.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [33_closure.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/33_closure.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.named-function-declarations.legality-2}

Function parameter and return-type annotations may be omitted when their types can be
inferred from context.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [80_named_function_inferred_signature.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/80_named_function_inferred_signature.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.named-function-declarations.dynamics-1}

A function with no return annotation and no `return expr;` returns `()`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [18_return.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/18_return.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Associated Functions

`extend` blocks may contain functions with no `self` parameter. [These are called on
the type via `::` syntax](#spec.functions.associated-functions.legality-1) and serve as
the canonical constructor pattern:

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun new(x: f64, y: f64) -> Point {
        return Point { x = x, y = y };
    }
}

fun main() -> i64 {
    let p = Point::new(1.0, 2.0);
    return p.x as i64;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.associated-functions.legality-1}

A function declared in an `extend` block without a `self`, `&self`, or `&var self`
parameter is an associated function and is called through its target type with `::`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/elaboration_inherent_and_aspect_coexist/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## First-Class Functions

[Functions are first-class values and can be assigned, passed, and returned](#spec.functions.first-class-functions.legality-2):

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

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.first-class-functions.legality-1}

Function and closure types use `(ParameterTypes) -> ReturnType`; the former
`fun(ParameterTypes) -> ReturnType` spelling is not a function-type syntax.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [33_closure.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/33_closure.mtl), [unannotated_closure_return_type_inferred.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/unannotated_closure_return_type_inferred.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.first-class-functions.legality-2}

Named functions and closures are values of their function type and may be bound, passed
as arguments, and returned as results.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [03_functions_and_closures.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/03_functions_and_closures.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Closures

Anonymous functions are [written with the `(...) -> ... { ... }` form](#spec.functions.closures.legality-1):

```metel
fun main() -> i64 {
    let double = (x: i64) -> i64 { return x * 2; };
    return double(5);
}
```

Closures [capture variables from their enclosing scope by value](#spec.functions.closures.dynamics-1). A captured variable is copied into the closure environment when the closure is created:

```metel
fun main() -> i64 {
    var count = 0;
    let inc = () -> { count += 1; };
    inc();
    inc();
    return count;   // still 0
}
```

> **Planned for v0.12.0 (RFC-0071): a captured value of a non-`Copy` type is *moved* into the closure, not copied — the original binding is invalid afterwards.**

Capture is by value, so a `Copy` type is copied and the original stays usable. Once move
semantics are enforced, a non-`Copy` capture transfers ownership: the closure owns the value
and the enclosing binding may not be used again. To keep using the original, capture a
reference instead — a shared reference is `Copy`, so capturing one copies the reference and
leaves the referent alone.

Shared mutable closure state is explicit. If [multiple closures must observe and update the
same storage, the program captures a reference](#spec.functions.closures.dynamics-3):

```metel
fun main() -> i64 {
    var count = 0;
    let p: &var i64 = &var count;
    let inc = () -> { *p += 1; };
    inc();
    inc();
    return *p;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.closures.legality-1}

An anonymous function is written as a parenthesized parameter list, followed by `->`, an
optional return type annotation, and a body block. It may appear wherever an expression is
accepted.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [33_closure.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/33_closure.mtl), [unannotated_closure_return_type_inferred.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/unannotated_closure_return_type_inferred.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.closures.legality-2}

After a parenthesized expression or parameter list, `->` begins a closure. Without `->`,
the parenthesized construct is not a closure; `(parameters) { body }` is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_lambda_without_arrow.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_lambda_without_arrow.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.closures.legality-3}

A zero-argument closure is written `() -> { body }`; a bare block is not an anonymous
function.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [unannotated_closure_return_type_inferred.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/unannotated_closure_return_type_inferred.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.closures.legality-4}

The former anonymous `fun(parameters) -> return_type { body }` spelling is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0041](../../rfcs/4-implemented/rfc-0041-lambda-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_11_old_fun_closure_syntax_in_expression_position.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_11_old_fun_closure_syntax_in_expression_position.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-1}

When a closure is created, each captured free variable is captured by value in the
closure's environment.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [73_closure_direct_assign_no_outer_effect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/73_closure_direct_assign_no_outer_effect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-2}

Mutating a captured-by-value binding changes the closure's captured value, not the
enclosing binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [73_closure_direct_assign_no_outer_effect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/73_closure_direct_assign_no_outer_effect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-3}

Closures that capture the same explicit reference observe the same referent; writes through
that reference by one closure are visible through the others.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [74_closure_external_ptr_affects_outer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/74_closure_external_ptr_affects_outer.mtl), [75_two_closures_share_state_via_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/75_two_closures_share_state_via_pointer.mtl), [69_nice_closure_abuse.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/69_nice_closure_abuse.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-4}

A closure that escapes its defining function while holding a captured pointer to a
still-reachable local keeps that storage alive and correctly mutable after the
defining function returns.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [69_nice_closure_abuse.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/69_nice_closure_abuse.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Turbofish

> **Availability:** Since v0.8.0.

When a generic function's type parameters cannot be inferred from the arguments, they [can be specified explicitly with turbofish syntax: `name::<T, U>(args)`](#spec.functions.turbofish.legality-1).

```metel
fun identity<T>(x: T) -> T { x }

fun main() -> i64 {
    let x = identity::<i64>(42);
    return x;
}
```

Turbofish is most useful when two or more independent type parameters must be pinned at the call site — for example, a `zip` function that pairs elements from arrays of different types:

<!-- doc-example: skip reason="elided body -- illustrates the signature only, not runnable" -->
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

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.turbofish.legality-1}

A generic call may supply explicit type arguments with `name::<T, U>(arguments)`, pinning
each named parameter to the given type. A pinned type must satisfy that parameter's own
bounds (e.g. `T: Display`).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0023](../../rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [83_turbofish.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/generics/83_turbofish.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.turbofish.legality-2}

The call's arguments must unify with their pinned types exactly as they would with an
inferred one.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0023](../../rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [turbofish_argument_type_mismatch_is_t0001.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/turbofish_argument_type_mismatch_is_t0001.mtl), [turbofish_pinned_type_unifies_with_unsuffixed_literal.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/turbofish_pinned_type_unifies_with_unsuffixed_literal.mtl), [turbofish_return_and_ascription_param_in_same_call.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/turbofish_return_and_ascription_param_in_same_call.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## The ? Operator

> **Availability:** Matching-error `?` since v0.1.0. `From`-based error coercion since v0.4.0.

Inside a function returning `Result<T, E>`, [`?` propagates errors early](#spec.functions.the-operator.dynamics-2):

```metel
fun parse_int(s: String) -> Result<i64, String> {
    if (s == "21") {
        return Ok { value = 21 };
    }
    return Err { error = "not a number" };
}

fun parse_and_double(s: String) -> Result<i64, String> {
    let n = parse_int(s)?;   // returns Err early if parse_int fails
    return Ok { value = n * 2 };
}

fun main() -> i64 {
    match parse_and_double("21") {
        Ok { value } => value,
        Err { error } => 0,
    }
}
```

`?` desugars to: if the expression is `Err(e)`, [return `Err(E2::from(e))`
immediately](#spec.functions.the-operator.dynamics-2) (where `E2` is the enclosing
function's error type); otherwise [unwrap to the `Ok` value](#spec.functions.the-operator.dynamics-1).

The inner expression's error type `E1` and the function's return error type `E2` [must
satisfy `E2: From<E1>`](#spec.functions.the-operator.legality-2). When `E1 == E2` no
conversion is performed. When they differ, `From::from` is called automatically on the
error value before re-wrapping in `Err`.

[`?` does not apply to `Perhaps<T>`](#spec.functions.the-operator.legality-1) in this
language version. It is supported only for `Result<T, E>`, so using `?` on a `Perhaps`
value is a type error (`T0001`) rather than an early `None` return.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.the-operator.legality-1}

The `?` operator requires a `Result<T, E>` operand; applying it to `Perhaps<T>` or any
other type is a type error.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage6_neg_05_error_propagation_non_result.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/error_handling/stage6_neg_05_error_propagation_non_result.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.the-operator.legality-2}

The enclosing function's return type must be `Result<U, E2>`, and the operand error
type `E1` must equal `E2` or satisfy `E2: From<E1>`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage6_neg_06_error_propagation_mismatched_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/error_handling/stage6_neg_06_error_propagation_mismatched_types.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.the-operator.dynamics-1}

Evaluating `Ok { value }?` produces `value` and evaluation continues in the enclosing
function.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [34_propagate_error.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/error_handling/34_propagate_error.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.the-operator.dynamics-2}

Evaluating `Err { error }?` immediately returns `Err { error }` from the enclosing
function; when the error types differ, the returned error is `E2::from(error)`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [61_propagate_error_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/error_handling/61_propagate_error_coercion.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

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

**[`native` is reserved for the standard library](#spec.functions.native-functions-standard-library-only.legality-1).** Using it in any module
outside the `std` namespace is a compile error, and user projects cannot place
modules under `std::` (see [Modules](modules.md)). From the caller's side,
native functions are indistinguishable from ordinary functions: they are
imported, typechecked, and called exactly like any other declaration — the
binding key is an implementation detail of the standard library's source.

Native declarations [must annotate every parameter type](#spec.functions.native-functions-standard-library-only.legality-3); an omitted return
type means the function returns `()`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-1}

Only a declaration in the `std` namespace may use the `native` modifier; a `native`
declaration in a user module is rejected.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [native_outside_std.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/native_outside_std.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-2}

A native declaration has a dotted `@` host-binding key and no Metel body: it ends with
`;`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [native_decl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/native_decl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-3}

Every native-function parameter has an explicit type annotation. An omitted return type
denotes `()`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [native_decl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/native_decl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>
