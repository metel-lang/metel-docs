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
[An inner closure may not capture an *enclosing* closure's by-value capture by `&` /
`&var`](#spec.functions.closures.legality-11).

### Call multiplicity and the mutation axis

A closure's function type carries two written qualifiers besides its parameter and return
types:

- **`once`** — invoking the closure consumes one of its captures. Written when the body
  moves a capture out (returns it, or passes it by value to something that takes
  ownership). [Omitting it when the body consumes a capture is an error](#spec.functions.closures.legality-8);
  the default is *many* (reusable).
- **`mut`** — invoking the closure mutates a capture. Written when the body assigns to a
  by-value capture or takes `&var` of one, and [always when the closure captures `[&var x]`](#spec.functions.closures.legality-8),
  regardless of what the body does through it. The default is *reading*.

The two qualifiers are order-insensitive as a *type* spelling; in a closure *literal* the
[fixed order is `[captures] once? mut? (params)`](#spec.functions.closures.legality-5).

[A function value may be used where a *less permissive* multiplicity is
expected](#spec.functions.closures.legality-9) — a *many* value satisfies a `once` slot, a
*reading* value satisfies a `mut` slot, a `Copy` value satisfies a non-`Copy` slot — at
first-order argument, ascription, field-init, and return positions. The reverse is
rejected. A conditional's type is the least-permissive of its arms, each arm widening to
it.

[A `mutating` call needs exclusive access to the closure value for the call's
duration](#spec.functions.closures.legality-10): the callee must be an owned binding, an
owned temporary, an exclusive projection off one, or a `&var` parameter — not a
shared-`&` callee. [Overlapping and reentrant `mutating` calls on the same closure value
are rejected](#spec.functions.closures.dynamics-9).

### Capture semantics

[By-value capture of a non-`Copy` binding moves it into the closure at creation, consuming
the outer binding; a `Copy` binding is copied; the captured environment is built once and
not re-cloned per call](#spec.functions.closures.dynamics-5).

```metel
fun make_counter() -> mut () -> i64 {
    let n := 0;
    [n] mut () -> i64 { n := n + 1; n }   // `n` moved in; writes persist
}

fun main() -> i64 {
    let mut c := make_counter();
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

Closures [satisfy no aspects](#spec.functions.closures.legality-12): `==`, `<`, and other
aspect-gated operations on closure values do not type-check. [A closure's `Send` / `Sync`
follows the aggregate rule over its captures](#spec.functions.closures.legality-14); a
`mutating` closure is not `Sync`.

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
capture item is `&var ident`, `&ident`, `ident`, or `ident.clone()`. In a closure
*literal* the prefixes appear in the fixed order capture list, then `once`, then `mut`,
then the parameter list; `mut once` and a qualifier before the capture list are parse
errors. As a *function type* spelling, `once` and `mut` are order-insensitive.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
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

`once` and `mut` are written qualifiers, verified against the body at the closure's
creation site. A closure whose body moves a non-`Copy` capture out, written without
`once`, is a compile error. A closure whose body assigns to a by-value capture or takes
`&var` of one, or which captures any binding by `[&var …]`, written without `mut`, is a
compile error. The message names the offending capture and the fix (add the qualifier, or
stop the operation / capture `[&x]` instead).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md), [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md), [rfc-0153](../../rfcs/3-integrated/rfc-0153-closure-mutation-axis.md)_</span>
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
borrow for the call's duration: an owned binding, an owned temporary, an exclusive
(`&var` / owning) projection off one, or a `&var` parameter. A shared-`&` callee — a
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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0050](../../rfcs/3-integrated/rfc-0050-closure-capture-lists.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.functions.closures.legality-12}

A closure value satisfies no aspects. `==`, `<`, and other aspect-gated operations applied
to a closure value are a compile error (aspect not satisfied). Structural equality of two
function *types* is a type relation and does not make their values comparable.

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

##### Dynamic Semantics {#spec.functions.closures.dynamics-1}

When a closure is created, each free variable named in its capture list (or, for a
listless closure, each free `Copy` variable) is placed into the closure's environment
according to its specifier: `[x]` moves a non-`Copy` value / copies a `Copy` value,
`[x.clone()]` stores an independent copy, `[&x]` / `[&var x]` store a reference.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0006](../../rfcs/4-implemented/rfc-0006-closure-capture-semantics.md), [rfc-0134](../../rfcs/3-integrated/rfc-0134-closure-call-capability.md)_</span>
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
