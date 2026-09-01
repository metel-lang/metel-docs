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
    let p := Point::new(1.0, 2.0);
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
    let f := add;
    let inc := (x: i64) -> i64 { return x + 1; };
    return f(1, 2) + apply(inc, 4);
}
```

The type of a function or closure is written as `(ParamTypes) -> ReturnType`.

A named function declared with its own `<T>` generics (`fun identity<T>(x: T) -> T
{ ... }`) may always be called directly (`identity(3)`, `identity::<i64>(3)`).

> **Changed in v0.13.0 (RFC-0138):** a generic named function may also be bound
> with a bare, unannotated `let` (the binding itself stays polymorphic, so its own
> later uses may each instantiate it differently — `let alias = identity;
> alias(3); alias("x");`), or passed as a higher-order argument whose receiving
> parameter position is itself concrete (`apply(identity, 3)`, where `apply`'s own
> parameter is `(i64) -> i64`, not itself generic).

Referencing it in a position where nothing pins down a concrete instantiation —
a parameter position that is itself still generic in the callee (rank-2), or an
expression position with no expected type and no enclosing `let` — is still
`T0003`. There is also no standalone instantiation-without-calling value form:
`identity::<i64>` not immediately followed by a call is a parse error, not a
type error — see [Turbofish](#spec.functions.turbofish.legality-3).

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

A non-generic named function and a closure are values of their function type and may be
bound, passed as arguments, and returned as results. A generic named function (declared
with its own `<T>` generics) may be called directly.

> **Changed in v0.13.0 (RFC-0138):** also legal — bound with a bare, unannotated
> `let` (staying polymorphic across that binding's own later uses, the same as an
> unannotated closure literal), or passed as a higher-order argument whose
> receiving parameter position is itself concrete (one instantiation, at that one
> call site).

Referencing it in any other position where nothing pins down a concrete
instantiation — including a parameter position that is itself still generic in
the callee — is `T0003`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0138](../../rfcs/4-implemented/rfc-0138-generic-functions-as-first-class-values.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [101_generic_fn_bare_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/generics/101_generic_fn_bare_reference.mtl), [102_generic_fn_reference_reused_at_multiple_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/generics/102_generic_fn_reference_reused_at_multiple_types.mtl), [103_generic_fn_higher_order_argument.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/generics/103_generic_fn_higher_order_argument.mtl), [104_generic_fn_nested_bare_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/generics/104_generic_fn_nested_bare_reference.mtl), [03_functions_and_closures.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/03_functions_and_closures.mtl), [stage10_10_generic_function_bare_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage10_10_generic_function_bare_reference.mtl), [stage10_11_generic_function_higher_order_argument.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage10_11_generic_function_higher_order_argument.mtl), [stage10_neg_06_generic_function_rank2_still_call_only.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage10_neg_06_generic_function_rank2_still_call_only.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Closures

Anonymous functions are [written with the `[captures]? once? mut? (params) -> ret? { body }` form](#spec.functions.closures.legality-1):

```metel
fun main() -> i64 {
    let double := (x: i64) -> i64 { return x * 2; };
    return double(5);
}
```

> **Planned for v0.13.0 (RFC-0050 / RFC-0134 / RFC-0152 / RFC-0153 / RFC-0157).** The
> capture list, the `once` / `mut` qualifiers, move-by-default capture, the per-call
> re-clone removal, and the mutation axis are specified here but not yet in the
> interpreter. Until they land, closures capture by value (deep clone), no capture list is
> required, and there is no `once` / `mut` verification. The `coverage` entries for the
> new rules are `blocked` on that implementation.

### Capture lists

A closure that reads an outer binding *captures* it. A **capture list** `[…]` before the
parameter list names each captured binding with a specifier:

```metel
fun main() {
    var count := 0;
    let cfg := Config::load();          // non-Copy, read-only in the closure
    let name := "log";                  // non-Copy, moved in

    let handler := [&var count, &cfg, name] mut (req: Request) -> Response {
        count += 1;
        route(req, cfg, name)
    };
}
```

- `[&var x]` captures `x` by **exclusive reference**; the body may read and write it.
- `[&x]` captures `x` by **shared reference**; the body may only read it.
- `[x]` captures `x` **by value** — a copy for a `Copy` binding, a **move** for a non-`Copy`
  one (the outer binding is consumed).
- `[x.clone()]` captures an explicit independent copy of a `Clone` binding, leaving the
  outer binding usable.

The list is [**required** whenever the closure references a free non-`Copy` local, or
captures anything by `&` / `&var`](#spec.functions.closures.legality-6); it is omissible
only when every free variable is a `Copy` binding captured by value, or there are none.
When present it is [**exhaustive**](#spec.functions.closures.legality-7): every free
local binding the body references must appear. Module-level functions, constants, types,
and aspects are not captures and never appear in the list.

A `&var` capture requires the outer binding to be [declared `var`](#spec.functions.closures.legality-13),
and a closure literal [cannot reference its own `let` binding](#spec.functions.closures.legality-13).
A `[&x]` capture is read-only: [assigning to it, or taking `&var` of it, in the body is a
compile error at the capture](#spec.functions.closures.legality-21), not a silent
`mutating` upgrade. Capturing a free variable of a type parameter `T` follows the
[bounds in scope at the closure's definition](#spec.functions.closures.legality-17) —
unbounded `T` is non-`Copy` for every instantiation. When an inner closure captures a
binding that is itself an *enclosing* closure's capture, [the enclosing closure must list
it, an inner `[s]` cannot move out of an enclosing `[&s]` borrow, and an inner `[s]` that
moves an enclosing-held binding makes the enclosing closure
`once`](#spec.functions.closures.legality-22); an inner `&` / `&var` of an enclosing
*by-value* capture is [an interim rejection](#spec.functions.closures.legality-11).

### Call multiplicity and the mutation axis

A closure's function type carries two written qualifiers besides its parameter and return
types:

- **`once`** — invoking the closure consumes one of its captures. Written when the body
  moves a capture out (returns it, or passes it by value to something that takes
  ownership). [Omitting it when the body consumes a capture is an error](#spec.functions.closures.legality-8);
  the default is *many* (reusable).
- **`mut`** — invoking the closure mutates a capture. Written when the body assigns to a
  by-value capture, takes `&var` of one, or calls a `&var self` method on one, and
  [always when the closure captures `[&var x]`](#spec.functions.closures.legality-25),
  regardless of what the body does through it. The default is *reading*.

The two qualifiers are [order-insensitive as a *type* spelling](#spec.functions.closures.legality-24);
in a closure *literal* the [fixed order is `[captures] once? mut? (params)`](#spec.functions.closures.legality-23).
An unqualified literal in a typed position takes [its `once` / `mut` from the expected
type](#spec.functions.closures.legality-18) rather than defaulting and then failing.
Verification runs in a [fixed stage order — capture classification, then `use_multiplicity`,
then `once`, then `mut`](#spec.functions.closures.legality-19); the two axes are checked
independently.

[A function value may be used where a *less permissive* multiplicity is
expected](#spec.functions.closures.legality-9) — a *many* value satisfies a `once` slot, a
*reading* value satisfies a `mut` slot, a `Copy` value satisfies a non-`Copy` slot — at
first-order argument, ascription, field-init, and return positions. The reverse is
rejected. A conditional's type is the least-permissive of its arms, each arm widening to
it. [Widening changes only the static type](#spec.functions.closures.dynamics-12): a
widened `reading` value keeps its plain call behaviour, and a `mut`-typed field that holds
one is [thereafter observed `mut`, with no re-narrowing](#spec.functions.closures.dynamics-14).

Whether a closure value is [`Copy` is exactly whether every capture is
`Copy`](#spec.functions.closures.legality-20); a `Copy` closure is necessarily *many*.

[A `mutating` call needs exclusive access to the closure value for the call's
duration](#spec.functions.closures.legality-10): the callee must be an owned binding, an
owned temporary, an exclusive projection off one, or a `&var` parameter — not a
shared-`&` callee. [Overlapping and reentrant `mutating` calls on the same closure value
are rejected](#spec.functions.closures.dynamics-9). If a `mut` call exits early via `?` or
`return`, [its partial mutations persist and the closure stays
callable](#spec.functions.closures.dynamics-13); a `panic` is uncatchable and ends the
process, so no post-exit state is observable.

### Capture semantics

[By-value capture of a non-`Copy` binding moves it into the closure at creation, consuming
the outer binding; a `Copy` binding is copied; the captured environment is built once and
not re-cloned per call](#spec.functions.closures.dynamics-5).

```metel
fun make_counter() -> mut () -> i64 {
    let n := 0;
    [n] mut () -> i64 { n += 1; n }   // `n` moved in; writes persist
}

fun main() -> i64 {
    var c := make_counter();   // `var`: a `mutating` call is a `&var self`-shaped borrow of `c` (legality-10)
    c();
    c()   // returns 2 — state lives in `c`'s environment
}
```

[A `mutating` closure's writes to its captures persist across
calls](#spec.functions.closures.dynamics-7); a `reading` closure reads its environment in
place. [Copying a `Copy` `mutating` closure gives the copy independent environment
state](#spec.functions.closures.dynamics-8) — the copies do not share a counter.

A `[&x]` / `[&var x]` capture stores a reference in the environment; the borrow is held
for the closure value's whole lifetime. [Captured owned values are dropped when the
closure value is dropped](#spec.functions.closures.dynamics-11), in capture-list order.

Closures [satisfy no aspects](#spec.functions.closures.legality-12): `==`, `<`, `.clone()`,
and other aspect-gated operations on closure values do not type-check. [A
closure's `Send` / `Sync` follows the aggregate rule over its
captures](#spec.functions.closures.legality-14); a `mutating` closure is not `Sync`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.closures.legality-1}

An anonymous function is written as an optional capture list `[…]`, optional `once` and/or
`mut` qualifiers, a parenthesized parameter list, `->`, an optional return type
annotation, and a body block. It may appear wherever an expression is accepted.

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

##### Legality Rule {#spec.functions.closures.legality-5}

A capture list is `[` followed by zero or more comma-separated capture items and `]`. A
capture item is `&var ident`, `&ident`, `ident`, or `ident.clone()`. A binding may not
appear more than once in the list, under any combination of specifiers. The literal prefix
order is [legality-23](#spec.functions.closures.legality-23); the function-type spelling's
order rules are [legality-24](#spec.functions.closures.legality-24).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-23}

In a closure *literal* the prefixes appear in one fixed order: capture list, then `once`,
then `mut`, then the parameter list. `mut once`, a qualifier before the capture list, and
a capture list placed after a qualifier are parse errors — even though the corresponding
function *type* spelling is order-insensitive ([legality-24](#spec.functions.closures.legality-24)).

##### Legality Rule {#spec.functions.closures.legality-24}

As a function *type* spelling the `once` and `mut` qualifiers are order-insensitive:
`once mut fun(T) -> U` and `mut once fun(T) -> U` denote the identical `Type::Fun`. The
fixed order of [legality-23](#spec.functions.closures.legality-23) is a grammar rule for
closure *literals* only.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-6}

A closure must carry a capture list if its body references a free non-`Copy` local
binding, or captures any binding by `&` or `&var`. Referencing a free non-`Copy` local
with no capture list is a compile error. A closure whose only free variables are `Copy`
bindings used by value, or which has no free variables, may omit the list.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-7}

When a closure has a capture list, every free local binding its body references must
appear in the list, with a specifier consistent with how the body uses it. A referenced
free local absent from a non-empty list is a compile error. Module-level functions,
constants, types, and aspects are resolved by ordinary name resolution and are never
capture items.

##### Legality Rule {#spec.functions.closures.legality-8}

`once` is a written qualifier, verified against the body at the closure's creation site;
the default is *many*. A closure whose body moves a non-`Copy` capture out — returns it,
or passes it by value to something that takes ownership — written without `once`, is a
compile error naming the offending capture and the fix (add `once`, or stop moving the
capture).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-25}

`mut` is a written qualifier, verified against the body at the closure's creation site;
the default is *reading*. A closure whose body assigns to a by-value capture, takes `&var`
of one, or calls a `&var self` method on one — and always a closure that captures any
binding `[&var …]`, regardless of what the body does through it — written without `mut`,
is a compile error naming the offending capture and the fix (add `mut`, stop the mutation,
or capture `[&x]` instead).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-9}

A function value of call multiplicity `m`, mutation `u`, and `Copy`-ness `c` satisfies a
slot requiring `m'`, `u'`, `c'` when `m` is at least as permissive as `m'` (*many* ≥
`once`), `u` at least as permissive as `u'` (*reading* ≥ `mut`), and `c` at least as
permissive as `c'` (`Copy` ≥ non-`Copy`). The reverse — a less permissive value into a
more permissive slot — is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md), [rfc-0152](../../rfcs/3-integrated/rfc-0152-function-type-multiplicity-widening.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-15}

The satisfaction rule of legality-9 applies at first-order positions only: a function-typed
argument passed to a function-typed parameter, a `let` / field ascription, a struct-field
initializer, and a return. Below the first level of function-type nesting an exact match is
required.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0152](../../rfcs/3-integrated/rfc-0152-function-type-multiplicity-widening.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-16}

A conditional or `match` expression whose arms are function-typed has, as its type, the
least-permissive arm type under legality-9's order, and each arm is widened to it. A
diverging (`!`-typed) arm does not contribute. A join that would require *narrowing* an
arm is the ordinary type mismatch.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0152](../../rfcs/3-integrated/rfc-0152-function-type-multiplicity-widening.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-10}

A `mutating` call `e(args)` requires `e` to denote a place the caller can exclusively
borrow for the call's duration — the ordinary `&var self` receiver rule: an owned `var`
binding, an owned temporary, an exclusive (`&var` / owning) projection off one, or a
`&var` parameter. An owned but non-`var` (`let`) binding is **not** eligible, exactly as a
`&var self` struct method may not be called on a `let` binding. A shared-`&` callee — a
`&Self` / `&self` receiver, a place reached through a `&` step, or an `&`-captured closure
— is a compile error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-11}

An inner closure may not capture, by `&` or `&var`, a binding that is a by-value capture
of an enclosing closure. It may capture such a binding by value (`[s]`, which moves it out
of the enclosing closure's environment). This restriction is lifted when the borrow
checker lands.

##### Legality Rule {#spec.functions.closures.legality-12}

A closure value satisfies no aspects. `==`, `<`, and other aspect-gated operations applied
to a closure value are a compile error (aspect not satisfied). `c.clone()` likewise does
not type-check — a closure has no `Clone` impl; the only way to duplicate a closure value
is the ordinary by-value copy available when it is `Copy`
([legality-20](#spec.functions.closures.legality-20)). Structural equality of two function
*types* is a type relation and does not make their values comparable.

> A `Share` aspect and `.share()` method don't exist in the language yet (RFC-0158,
> `1-under-review`); once they do, a closure has no `Share` impl either, by the same
> aspect-exemption rule — but that is RFC-0158's claim to spec-integrate, not this one's.

##### Legality Rule {#spec.functions.closures.legality-13}

A `[&var ident]` capture requires `ident` to be a `var` binding; capturing a non-`var`
binding by `&var` is a compile error. A closure literal cannot reference its own `let`
binding — the name is not in scope inside its own initializer.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-14}

A closure value is `Send` (respectively `Sync`) when every one of its captures is `Send`
(respectively `Sync`), applying the reference rules for `&T` / `&var T` captures. A
`mutating` closure value is additionally not `Sync`.

##### Legality Rule {#spec.functions.closures.legality-17}

Whether a captured free variable of type parameter `T` is `Copy` is decided from the
bounds in scope at the closure's definition, not re-decided per instantiation. A capture
of an unbounded `T` is non-`Copy`: `[t]` moves it, and a body that moves it out makes the
closure `once` for *every* instantiation of the enclosing generic, `T = i64` included. A
definition wanting the copyable behaviour adds `T: Copy`, after which `[t]` is a copy and
consumes nothing.

##### Legality Rule {#spec.functions.closures.legality-18}

An unqualified closure literal in a position with an expected function type — a `let` or
parameter ascription, a struct-field initializer, a return, or the tail expression of a
typed block — is checked against that type's `once` / `mut` qualifiers rather than taking
the *many* / *reading* default and then failing. When the expected type does not fix a
qualifier (an unresolved inference variable, or a bare generic parameter), the literal
takes the default and [legality-9](#spec.functions.closures.legality-9) widening resolves
any remaining gap at the concrete site.

##### Legality Rule {#spec.functions.closures.legality-19}

A closure literal is resolved in a fixed stage order: (1) capture classification — which
free variables the body references, each one's `Copy`-ness, whether a list is required,
and, when a list is present, exhaustiveness and specifier-matches-use; (2)
`use_multiplicity` ([legality-20](#spec.functions.closures.legality-20)); (3) `once`
verification ([legality-8](#spec.functions.closures.legality-8)); (4) `mut` verification
([legality-25](#spec.functions.closures.legality-25)). The first failing stage is the
reported error; later stages are suppressed for that closure. Stages 3 and 4 are
independent — a body that both consumes and mutates without the qualifiers is reported
against both, each with its own fix.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-20}

A closure value is `Copy` exactly when every one of its captures is `Copy`. `[x]` of a
`Copy` binding and `[&x]` (a shared reference is `Copy`) preserve it; `[x]` of a
non-`Copy` binding, `[x.clone()]` of a non-`Copy` type, and `[&var x]` (an exclusive
reference is not `Copy`) make the closure non-`Copy`. A `Copy` closure is necessarily
*many* — it holds nothing non-`Copy` for a call to consume.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-21}

A closure that captures `x` by shared reference `[&x]` and whose body assigns to `x`,
takes `&var x`, or calls a `&var self` method on it is a compile error *at the capture* —
the closure is not silently reclassified `mutating`. The fix is to capture `[&var x]`,
which requires `x` to be a `var` binding ([legality-13](#spec.functions.closures.legality-13))
and makes the closure `mutating` ([legality-25](#spec.functions.closures.legality-25)).

##### Legality Rule {#spec.functions.closures.legality-22}

When an inner closure captures a binding `s` that is itself a capture of an *enclosing*
closure: the enclosing closure must list `s` in its own capture list (it is a free
variable of the enclosing body); an inner `[s]` requires the enclosing closure to hold `s`
by value, and an inner `[s]` naming an enclosing `[&s]` / `[&var s]` capture is a `move
out of borrowed content` error; and because evaluating the inner literal performs the
capture, an inner `[s]` that moves an enclosing-held `s` makes the *enclosing* closure
`once` ([legality-8](#spec.functions.closures.legality-8)) even if the inner closure is
never called. An inner `[&s]` / `[&var s]` does not change the enclosing closure's
multiplicity but is subject to [legality-11](#spec.functions.closures.legality-11)'s
interim borrow restriction.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-1}

When a closure is created, each free variable named in its capture list (or, for a
listless closure, each free `Copy` variable) is placed into the closure's environment
according to its specifier: `[x]` moves a non-`Copy` value / copies a `Copy` value,
`[x.clone()]` stores an independent copy, `[&x]` / `[&var x]` store a reference.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [73_closure_direct_assign_no_outer_effect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/73_closure_direct_assign_no_outer_effect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-2}

A `reading` closure does not modify its environment; a `mutating` closure modifies it in
place. In neither case does a write inside the closure body affect an *outer* binding that
was captured by value — the closure operates on its own environment copy.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [73_closure_direct_assign_no_outer_effect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/73_closure_direct_assign_no_outer_effect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-3}

Closures that capture the same binding by `[&x]` / `[&var x]`, or that capture the same
reference value, observe the same referent; a write through an exclusive reference by one
closure is visible through the others.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [74_closure_external_ptr_affects_outer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/74_closure_external_ptr_affects_outer.mtl), [75_two_closures_share_state_via_pointer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/closures/75_two_closures_share_state_via_pointer.mtl), [69_nice_closure_abuse.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/69_nice_closure_abuse.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-4}

A closure that escapes its defining function while holding a captured owned value keeps
that value alive; the environment travels with the closure value. A closure holding a
captured *reference* cannot outlive the referent (checked by the borrow checker when it
lands; unenforced before then).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [69_nice_closure_abuse.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/69_nice_closure_abuse.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-5}

Capturing a non-`Copy` binding by value (`[x]`) moves it: the outer binding is consumed at
closure creation and using it afterward is a moved-value error. A `Copy` binding captured
by value is copied and the outer binding stays usable. `[x.clone()]` produces an
independent copy and leaves the outer binding usable regardless of `Copy`-ness. The
captured environment is constructed once, when the closure value is created; a call does
not re-clone it — each call operates on the same environment held by the closure value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0157](../../rfcs/3-integrated/rfc-0157-copy-and-clone-model-re-analysis.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-7}

A `mutating` closure's assignments to its by-value captures are retained in its
environment and are visible to subsequent calls of the same closure value — the closure
holds private mutable state.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-8}

Copying a closure value whose captures are all `Copy` copies its environment. The copies
have independent environment state: a `mutating` call on one does not affect the other.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-9}

For the dynamic extent of a `mutating` call the callee place is exclusively borrowed. A
second `mutating` call on the same closure value reached from inside the first — directly
or through a structure the body can reach — is rejected: before the borrow checker lands,
as a runtime error; after, as a static borrow conflict.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-10}

A `once` call consumes the callee at the call expression, before the body runs. Any later
use of that closure value is a moved-value error, whether the body returned normally or
exited early.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md)_</span>
<!-- rfc.py:origins:end -->

##### Dynamic Semantics {#spec.functions.closures.dynamics-11}

When a closure value is dropped, its environment is dropped: each owned capture is dropped
in capture-list order, as a struct's fields are. A `once`-consumed or partially-moved
environment drops only its still-owned captures.

##### Dynamic Semantics {#spec.functions.closures.dynamics-12}

Multiplicity widening ([legality-9](#spec.functions.closures.legality-9)) changes only the
static type at the slot, never the closure value's runtime behaviour. A `reading` closure
value widened into a `mut`-typed slot is still invoked by the plain, non-exclusive call
path and consults no in-call flag, because call lowering branches on the closure value's
own mutation axis, not on the slot type. A `many` value in a `once` slot is likewise not
consumed by the call.

##### Dynamic Semantics {#spec.functions.closures.dynamics-13}

"Early exit" from a `mutating` call means the mid-call exits the language has and a caller
can observe: a `?`-propagated `Err` or an early `return` in the body, travelling up as an
ordinary signal through normal call-frame returns. A `panic` is not one of these — it is
hard, uncatchable, and terminates the process ([runtime.md](runtime.md#spec.runtime.panics.dynamics-1)),
so no later program point can observe the closure's post-exit state. On an observable early
exit from a plain `mut` (not `once`) call, the mutations that already ran are visible in
the environment, the exclusive borrow and the in-call flag are released as the frame
returns, and the closure stays callable in a valid-but-partial state — as a `&var self`
method that returned early mid-mutation leaves its receiver. There is no rollback. A `once`
/ `once mut` closure was already consumed at the call expression
([dynamics-10](#spec.functions.closures.dynamics-10)), so it is a moved value however the
body exited; its environment's still-owned fields are still dropped when the value goes out
of scope.

##### Dynamic Semantics {#spec.functions.closures.dynamics-14}

Storing a `reading` closure into a `mut`-typed field, or returning it where a `mut`
function type is named, yields a value thereafter *observed* as `mut`: every later read of
that field or result is a `mut` value that callers must invoke under exclusive access
([legality-10](#spec.functions.closures.legality-10)), even though the underlying closure
never mutates. The coercion is one-way — there is no automatic re-narrowing back to
`reading`.

</details>

## Turbofish

> **Availability:** Since v0.8.0.

When a generic function's type parameters cannot be inferred from the arguments, they [can be specified explicitly with turbofish syntax: `name::<T, U>(args)`](#spec.functions.turbofish.legality-1).

```metel
fun identity<T>(x: T) -> T { x }

fun main() -> i64 {
    let x := identity::<i64>(42);
    return x;
}
```

Turbofish is most useful when two or more independent type parameters must be pinned at the call site — for example, a `zip` function that pairs elements from arrays of different types:

<!-- doc-example: skip reason="elided body -- illustrates the signature only, not runnable" -->
```metel
fun zip<A, B>(a: A[], b: B[]) -> (A, B)[] { /* ... */ }

fun main() {
    let pairs := zip::<i64, String>([1, 2], ["a", "b"]);
}
```

Type ascription (`: T`) remains available for annotating the result type. Turbofish and ascription can be used together:

```metel
let result := parse::<i64>("42") : Perhaps<i64>;
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

##### Legality Rule {#spec.functions.turbofish.legality-3}

Turbofish is a call-postfix production, fused to the immediately following call's
parentheses. There is no standalone instantiation-without-calling value form:
`name::<T>` not immediately followed by `(arguments)` is a parse error.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [generic_function_turbofish_without_call_is_parse_error.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/generic_function_turbofish_without_call_is_parse_error.mtl)_</span>
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
    let n := parse_int(s)?;   // returns Err early if parse_int fails
    return Ok { value = n * 2 };
}

fun main() -> i64 {
    match (parse_and_double("21")) {
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
