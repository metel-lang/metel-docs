# Declarations

`public` may be prefixed to top-level `fun`, `struct`, `enum`, and `aspect`
declarations to mark them as accessible from other modules. Top-level `let` and `var`
bindings remain module-private. See [Modules — Visibility](modules.md#visibility) for
the full rules. The current `public` / `var` / `extend` surface spellings are the
spelling set introduced by RFC-0098.

## Variables

### Immutable Bindings

```metel
fun main() -> i64 {
    let x := 42;
    let name: String := "Vlad";
    if (name == "Vlad") { return x; }
    return 0;
}
```

`let` bindings [cannot be reassigned and must always be initialized](#spec.declarations.variables.immutable-bindings.legality-1). Mutability lives entirely on the binding — a `let` binding is immutable regardless of what value it holds. This means:

- `x := newValue` is rejected (reassignment)
- `x.field = value` is rejected (field assignment through an immutable binding)
- `&var x` is rejected (taking a mutable reference to an immutable binding)

All three forms require `var`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.immutable-bindings.legality-1}

A `let` binding must be initialized with the `:=` separator and cannot be assigned
after initialization. `:=` is the sole separator that introduces a kept binding; the
plain `=` spelling is a parse error (RFC-0136).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_14_legacy_equals_binding_separator.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_14_legacy_equals_binding_separator.mtl), [stage4_neg_05_compound_assign_to_let.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/stage4_neg_05_compound_assign_to_let.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-2}

A conditional aspect implementation may state its bounds inline on its type parameters or
in a `where` clause; the two spellings are equivalent.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [69_conditional_impl_inline_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/69_conditional_impl_inline_bound.mtl), [69b_conditional_impl_where_clause.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/69b_conditional_impl_where_clause.mtl), [80_conditional_impl_defines_assoc_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/80_conditional_impl_defines_assoc_type.mtl), [81_generic_struct_iterable_for_in.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/81_generic_struct_iterable_for_in.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-3}

A conditional aspect implementation applies only to instantiations whose type arguments
satisfy every bound stated by that implementation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [69_conditional_impl_inline_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/69_conditional_impl_inline_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-4}

Conditional implementation bounds are checked whenever the aspect is required, including
method dispatch, bound satisfaction, and implementation selection.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [69_conditional_impl_inline_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/69_conditional_impl_inline_bound.mtl), [69b_conditional_impl_where_clause.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/69b_conditional_impl_where_clause.mtl), [75_conditional_impl_dispatch_runtime.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/75_conditional_impl_dispatch_runtime.mtl), [80_conditional_impl_defines_assoc_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/80_conditional_impl_defines_assoc_type.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_cross_module_merge/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_cross_module_merge_neg/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-5}

A type's declaration bounds and an aspect implementation's conditional bounds are
independent; satisfying one does not satisfy the other.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage17_01_conditional_impl_inline_bound_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_01_conditional_impl_inline_bound_satisfied.mtl), [stage17_02_conditional_impl_where_clause_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_02_conditional_impl_where_clause_satisfied.mtl), [stage17_03_conditional_impl_two_params_both_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_03_conditional_impl_two_params_both_satisfied.mtl), [stage17_05_conditional_impl_bound_satisfied_through_unrelated_generic_fun.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_05_conditional_impl_bound_satisfied_through_unrelated_generic_fun.mtl), [stage17_neg_03_conditional_impl_bound_not_satisfied_through_unrelated_generic_fun.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_neg_03_conditional_impl_bound_not_satisfied_through_unrelated_generic_fun.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-6}

A generic function using a conditional implementation must state the required bounds on
its own type parameters; those bounds are not inferred from the function body.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage17_04_conditional_impl_propagation_through_generic_function.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_04_conditional_impl_propagation_through_generic_function.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-7}

Conditional implementations participate in the ordinary coherence and orphan-rule checks.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_vs_unconditional_impl_conflict/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-8}

Two conditional implementations of the same aspect and target are disjoint only when an
explicit negative bound in one directly negates a positive bound in the other; otherwise
an overlapping pair is rejected with `T0015`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_explicit_negation_added_accepted/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted_for_structural_target/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-9}

A conditional and an unconditional implementation of the same aspect for the same target
conflict, because the unconditional implementation covers every conditional instantiation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_vs_unconditional_impl_conflict/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-10}

A conditional implementation is subject to the orphan rule: either its aspect or its
target's outermost constructor must be local to the implementing module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_orphan_violation/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-11}

When a conditional implementation's bound is unsatisfied, the compiler reports `T0012`
and identifies the unsatisfied condition.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0036](../../rfcs/4-implemented/rfc-0036-conditional-impl-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage17_neg_01_conditional_impl_bound_not_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_neg_01_conditional_impl_bound_not_satisfied.mtl), [stage17_neg_02_conditional_impl_multi_bound_one_violated.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage17_neg_02_conditional_impl_multi_bound_one_violated.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-12}

An implementation method's signature is compared against the aspect method's after
the aspect signature is specialized with the `extend` block's target type for
`Self`, its aspect arguments, and its associated-type definitions. After that
specialization the receiver form, ordinary parameter count and types, and result
type must be equal; method generic-parameter names compare alpha-equivalently.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0129](../../rfcs/4-implemented/rfc-0129-aspect-method-generic-constraint-conformance.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage21_neg_02_concrete_aspect_impl_signature_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_02_concrete_aspect_impl_signature_mismatch.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-13}

After specialization (legality-12) and after normalizing away alpha-renaming,
conjunctive-bound order, duplicate bounds, inline-versus-`where` placement, and
generic-binder-versus-`where` record-kind placement, an implementation method's
generic-constraint conjunction must be structurally equal to the aspect method's.
Equality is over resolved atoms — every aspect, type, associated-type, and
row-label reference stands for the entity it resolves to, not its spelling — and
covers each parameter's record kind, the set of positive and negative aspect
bounds, the set of row bounds, and the set of associated-type equality bindings
(each identified by its resolved projection key and right-hand-side type after
specialization). Neither weakening nor strengthening a constraint conforms.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0129](../../rfcs/4-implemented/rfc-0129-aspect-method-generic-constraint-conformance.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage21_10_aspect_impl_generic_constraints_identical.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_10_aspect_impl_generic_constraints_identical.mtl), [stage21_11_aspect_impl_generic_constraints_alpha_rename_and_reorder.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_11_aspect_impl_generic_constraints_alpha_rename_and_reorder.mtl), [stage21_12_aspect_impl_generic_constraint_in_where_clause.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_12_aspect_impl_generic_constraint_in_where_clause.mtl), [stage21_neg_06_aspect_impl_adds_generic_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_06_aspect_impl_adds_generic_bound.mtl), [stage21_neg_07_aspect_impl_adds_record_kind.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_07_aspect_impl_adds_record_kind.mtl), [stage21_neg_08_aspect_impl_drops_generic_bound_conservative_wrong_no.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_08_aspect_impl_drops_generic_bound_conservative_wrong_no.mtl), [stage21_neg_09_aspect_impl_drops_record_kind_conservative_wrong_no.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_09_aspect_impl_drops_record_kind_conservative_wrong_no.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-14}

An implementation method whose signature (legality-12) or generic constraints
(legality-13) do not conform is a type error on that method's own declaration,
reported with `T0012`. Such a method does not satisfy the aspect and does not
contribute to aspect-method dispatch.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0129](../../rfcs/4-implemented/rfc-0129-aspect-method-generic-constraint-conformance.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage21_neg_06_aspect_impl_adds_generic_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_neg_06_aspect_impl_adds_generic_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Mutable Bindings

```metel
fun main() -> i64 {
    var counter := 0;
    counter := counter + 1;
    counter += 1;
    return counter;
}
```

`var` bindings [can be reassigned and also must be initialized at declaration](#spec.declarations.variables.mutable-bindings.legality-1). Compound assignment operators `+=`, `-=`, `*=`, `/=`, `%=` are supported.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.mutable-bindings.legality-1}

A `var` binding must be initialized and may be assigned after initialization; `var` is the
mutable binding spelling. Both the initializer and a subsequent plain reassignment use the
`:=` separator (RFC-0136); the compound assignment operators `+=`, `-=`, `*=`, `/=`, `%=`
keep `=`. The bare `=` spelling for a `var` initializer or reassignment is a parse error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md), [rfc-0136](../../rfcs/4-implemented/rfc-0136-walrus-for-kept-bindings.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [16_for_loop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/control_flow/16_for_loop.mtl), [neg_14_legacy_equals_binding_separator.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_14_legacy_equals_binding_separator.mtl), [neg_15_legacy_equals_reassignment.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_15_legacy_equals_reassignment.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Scoping and Shadowing

Variables are [lexically scoped](#spec.declarations.variables.scoping-and-shadowing.legality-1). Each block `{ }` introduces a new scope. Inner scopes can shadow outer variables.

`let` and `var` declarations are [sequential](#spec.declarations.variables.scoping-and-shadowing.legality-2) — a binding is visible only from its declaration point to the end of its containing block.

`fun` declarations are [hoisted to the top of their containing block](#spec.declarations.variables.scoping-and-shadowing.legality-3). All `fun` declarations in a block are mutually visible to each other and to all other statements in that block, regardless of declaration order. This enables forward references and mutual recursion at any nesting level.

Hoisting is block-local: a `fun` declared in an inner block is not visible in the outer block. Normal lexical scoping applies across block boundaries — inner blocks see outer declarations, outer blocks do not see inner declarations.

```metel
fun is_even(n: i64) -> boolean {
    if (n == 0) { return true; }
    return is_odd(n - 1);
}

fun is_odd(n: i64) -> boolean {
    if (n == 0) { return false; }
    return is_even(n - 1);
}

fun outer() -> i64 {
    inner();

    fun inner() {
        helper();
        fun helper() { }
    }

    return 1;
}

fun main() -> i64 {
    if (is_odd(3)) { return outer(); }
    return 0;
}
```

An inner function remains scoped to its own block. For example, `helper();` is valid inside `inner()`, but calling `helper();` from `outer()` is a type error.

<!-- doc-example: expect-fail reason="demonstrates that helper() is not visible from outer() -- the type error is the point" -->
```metel
fun outer() {
    fun inner() {
        fun helper() { }
        helper();
    }

    helper();
}

fun main() {
    outer();
}
```

Top-level `struct` and `enum` declarations are [hoisted to program scope](#spec.declarations.variables.scoping-and-shadowing.legality-4) — they may be
referenced before their declaration appears in the source.

Types declared inside a function body are local to that body from their declaration
point onward; they are not visible from other functions.

```metel
fun make_point() -> Point {
    return Point { x = 1.0, y = 2.0 };   // OK — Point is globally visible
}

struct Point {
    x: f64,
    y: f64,
}

fun inner() {
    struct LocalPoint {
        x: f64,
        y: f64,
    }
    let p := LocalPoint { x = 1.0, y = 2.0 };
}

fun main() -> i64 {
    inner();
    let p := make_point();
    return p.x as i64;
}
```

Top-level `extend` blocks follow the same declaration-order rule as the types they extend.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.scoping-and-shadowing.legality-1}

Each block introduces a lexical scope. A declaration in an inner scope may shadow an outer
declaration, and the outer declaration is not visible outside its own scope.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [20_scoping.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/20_scoping.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.variables.scoping-and-shadowing.legality-2}

A `let` or `var` binding is in scope from its declaration through the end of its containing
block, but not before its declaration.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_03_binding_not_visible_before_declaration.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/neg_03_binding_not_visible_before_declaration.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.variables.scoping-and-shadowing.legality-3}

Function declarations are visible throughout their containing block regardless of source
order, including to other functions in that block; this hoisting does not extend out of an
inner block.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [79_nested_fun_forward_ref_in_let_initializer.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/functions/79_nested_fun_forward_ref_in_let_initializer.mtl), [07_forward_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/functions/07_forward_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.variables.scoping-and-shadowing.legality-4}

Top-level struct and enum declarations are visible throughout the program regardless of
source order. A type declared inside a function is visible only from its declaration through
that function body.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [46_local_struct_scope.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/46_local_struct_scope.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

---

## Structs

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p := Point { x = 1.0, y = 2.0 };
    return p.y as i64;
}
```

### Instantiation and Field Access

> **Changed in v0.12.0: field initializers separate with `=`, not `:` — `Point { x = 1.0 }`; field *declarations* keep `:`.**

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p := Point { x = 1.0, y = 2.0 };
    let x := p.x;
    return x as i64;
}
```

When a local variable has the same name as a field, the `= value` part can be omitted
([**shorthand field init**](#spec.declarations.structs.instantiation-and-field-access.legality-1)):

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let x := 1.0;
    let y := 2.0;
    let p := Point { x, y };
    return p.x as i64;
}
```

Shorthand and explicit fields may be mixed freely within one literal.

Zero-field structs [may omit braces entirely](#spec.declarations.structs.instantiation-and-field-access.legality-2).
These two forms are [equivalent](#spec.declarations.structs.instantiation-and-field-access.dynamics-2):

```metel
struct Empty {}

let a := Empty;
let b := Empty {};
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-1}

A struct-literal field initializer is `ident`, optionally followed by `= expr`. When `=
expr` is present, `ident` names the field and `expr` its value. When omitted, `ident` must
name both the field and a local binding in scope at the literal (shorthand/punning field
init). Shorthand and explicit fields may be freely mixed within one struct literal.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [43_shorthand_field.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/43_shorthand_field.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

A shorthand field `ident` in a struct literal evaluates identically to the explicit form
`ident = ident`: the field takes the value of the local binding named `ident` that is in
scope at the literal.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [43_shorthand_field.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/43_shorthand_field.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-2}

A zero-field struct may be constructed either as its bare type name or with empty braces.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [89_empty_constructor_forms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/89_empty_constructor_forms.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-2}

For a zero-field struct, the bare and empty-brace constructor forms evaluate to the same
struct value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [89_empty_constructor_forms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/89_empty_constructor_forms.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-3}

A struct with fields cannot omit its constructor fields; its bare type name is resolved as a
name rather than as a constructor expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage5_neg_42_non_empty_struct_requires_fields.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_42_non_empty_struct_requires_fields.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Methods

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun distance(self, other: Point) -> f64 {
        let dx := self.x - other.x;
        let dy := self.y - other.y;
        return dx * dx + dy * dy;   // squared distance
    }
}

fun main() -> i64 {
    let p := Point { x = 1.0, y = 2.0 };
    let q := Point { x = 4.0, y = 6.0 };
    let d := p.distance(q);
    return d as i64;
}
```

`self` refers to the receiver. Methods are called with dot syntax.

### Receiver Forms

Methods may declare one of three receiver forms:

- `self` — value receiver
- `&self` — shared reference receiver
- `&var self` — mutable reference receiver

Value receivers follow ordinary Metel value semantics. Shared and mutable reference
receivers operate on the original receiver storage and are the right forms for
observers and in-place mutation.

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun length(&self) -> f64 {
        self.x * self.x + self.y * self.y
    }
}
```

```metel
struct Counter {
    value: i64,
}

extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}
```

Calls requiring `&var self` [need a mutable addressable receiver or a `&var T`
reference](#spec.declarations.structs.receiver-forms.legality-1). Calls requiring `&self` may use an addressable receiver or a `&T` / `&var T`
reference (RFC-0067a — missed when that RFC integrated `*T`/`*mut T` → `&T`/`&var T`
elsewhere; caught while integrating this batch).

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
    var c := Counter { value = 1 };
    c.increment();
    return c.value;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-1}

`&var self` is the mutable-reference receiver spelling and requires a mutable addressable
receiver or an `&var T` reference at the call site.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md), [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [67_receiver_references.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/67_receiver_references.mtl), [68_receiver_all_forms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/68_receiver_all_forms.mtl), [69_nested_field_mut_receiver.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/69_nested_field_mut_receiver.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-2}

Methods may use `self`, `&self`, or `&var self` as their receiver.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [67_receiver_references.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/67_receiver_references.mtl), [stage20_02_mut_aspect_method_through_mut_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage20_02_mut_aspect_method_through_mut_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.receiver-forms.dynamics-1}

A value receiver receives the ordinary passed value, so a method that returns a changed
value leaves the caller's original binding unchanged.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [100_value_receiver_keeps_value_semantics.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/100_value_receiver_keeps_value_semantics.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-3}

An `&self` receiver reads the original receiver storage without consuming it.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [67_receiver_references.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/67_receiver_references.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.receiver-forms.dynamics-2}

An `&var self` receiver mutates the original receiver storage in place without consuming
the receiver.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [67_receiver_references.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/67_receiver_references.mtl), [69_nested_field_mut_receiver.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/69_nested_field_mut_receiver.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-4}

Dot-call syntax selects the receiver behavior declared in the method signature; callers
do not supply a distinct receiver-mode syntax.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [67_receiver_references.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/67_receiver_references.mtl), [69_nested_field_mut_receiver.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/69_nested_field_mut_receiver.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-5}

An `Iterable<T>` implementation declares `next` with an `&var self` receiver so repeated
calls can advance the same iterator value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [59_iterable_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/59_iterable_aspect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-6}

An `&var self` method may be called through an `&var T` reference.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage20_02_mut_aspect_method_through_mut_reference.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage20_02_mut_aspect_method_through_mut_reference.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-7}

An aspect method may declare an `&var self` receiver, including `Iterable<T>::next`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0044](../../rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [59_iterable_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/59_iterable_aspect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Generic Structs

```metel
struct Pair<A, B> {
    first: A,
    second: B,
}

fun main() -> i64 {
    let p := Pair { first = 1, second = true };
    return p.first;
}
```

---

## Enums

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir := Direction::North;
    let s := Shape::Circle { radius = 5.0 };
    let area := match (s) {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match (dir) {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

Variants may be unit (no data) or struct-like (named fields). A struct-like variant's
named fields follow the [same `public`/private visibility rules as an ordinary
struct's](modules.md#spec.modules.visibility.legality-6).

When a struct-like variant's field set is empty, [both constructor spellings are
accepted](#spec.declarations.enums.legality-1):

```metel
enum Flag {
    On {},
}

let x := Flag::On;
let y := Flag::On {};
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.legality-1}

A zero-field enum variant may be constructed either as its qualified path or with empty
braces.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [89_empty_constructor_forms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/89_empty_constructor_forms.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.enums.dynamics-1}

For a zero-field enum variant, the bare and empty-brace constructor forms evaluate to the
same variant value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [89_empty_constructor_forms.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/89_empty_constructor_forms.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Instantiation

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir := Direction::North;
    let s := Shape::Circle { radius = 5.0 };
    let area := match (s) {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match (dir) {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.instantiation.legality-1}

A struct-like enum variant with fields cannot omit its constructor fields.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage6_neg_13_non_empty_variant_requires_fields.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/enums/stage6_neg_13_non_empty_variant_requires_fields.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Methods on Enums

`extend` blocks on enums follow the same syntax as structs:

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

extend Shape {
    fun area(self) -> f64 {
        match (self) {
            Circle { radius } => 3.14159 * radius * radius,
            Rectangle { width, height } => width * height,
        }
    }
}

fun main() -> i64 {
    let s := Shape::Circle { radius = 5.0 };
    return s.area() as i64;
}
```

---

## Type Aliases

> **Availability:** Since v0.13.0 (RFC-0160).

A **type alias** gives an existing type a name:

<!-- doc-example: skip reason="RFC-0160 type-alias syntax, pending a develop-latest that parses it (metel-core#921)" -->
```metel
type Bytes := List<u8>;
type Handler := once var |Request, &Config| -> Response;
type Pair<A, B> := (A, B);
```

An alias is **transparent** — erased to its right-hand side before type checking, with no
nominal identity of its own. `Pair<i64, boolean>` and `(i64, boolean)` are the same type,
accepted in the same positions, satisfying the same bounds. An alias defines no impl, so
there is no coherence concern. It may be parameterised and may reference another alias;
`type` inside an `aspect` / `extend` block remains an [associated-type
definition](#spec.declarations.aspects.associated-types.legality-1) — position, not a
keyword, tells the two apart.

A **module-level `public` alias** joins the module's public surface exactly like a
`struct` / `enum` / `fun` — it is imported (by name, under a rename, through a glob) and
referenced with a qualified path in every position a type is written, and each spelling
resolves to the same erased type. A **function- or block-local alias** is never exported;
it may name the enclosing function's generic parameters and it shadows an outer alias of
the same name for the remainder of its block.

##### Legality Rule {#spec.declarations.type-aliases.legality-1}

A type alias is written `public? type Name generic_params? := Type ;` at module scope or
in a function / block body. It introduces `Name` as a transparent synonym for `Type`:
every use of `Name` (with type arguments substituted for its generic parameters) is
replaced by `Type` before name resolution and type checking. An alias use must supply
exactly the alias's declared number of type arguments. `public` is module-scope only, and
naming a non-`public` alias from another module is a visibility error, the same as any
other private item.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0160](../../rfcs/4-implemented/rfc-0160-type-aliases.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [01_basic_and_parameterised.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/01_basic_and_parameterised.mtl), [02_struct_field_and_return.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/02_struct_field_and_return.mtl), [03_block_local.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/03_block_local.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/04_cross_module/main.mtl), [neg_02_arity.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/neg_02_arity.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/neg_03_private_cross_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.type-aliases.legality-2}

A type alias may not be recursive — neither directly nor through a chain of aliases. A
transparent alias has no finite expansion for a cycle; a genuinely recursive shape uses a
`struct` or `enum` indirection point.



---

## Aspects

> **Availability:** Since v0.4.0.

```metel
aspect Printable {
    fun print(self);
}

aspect Comparable {
    fun compare(self, other: Self) -> i64;
}

fun main() -> i64 {
    return 0;
}
```

<details>
<summary>Formal rules</summary>

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_01_recursive.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/type_aliases/neg_01_recursive.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.legality-1}

An aspect declaration is introduced with the `aspect` keyword. Its braced body declares
the methods and associated types that implementing types must provide.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0020](../../rfcs/4-implemented/rfc-0020-language-rebranding.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [06_traits.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/06_traits.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Bodyless Aspect Declarations

```metel
aspect Copy2;
```

An aspect declaration [may end with `;` instead of a braced body when the body would be
empty already: zero methods and zero associated types](#spec.declarations.aspects.bodyless-aspect-declarations.legality-1). This is pure sugar for
`aspect Copy2 { }`.

The shorter spelling does **not** promise that the aspect stays empty forever. If a
later revision adds a method or associated type, the declaration simply switches back
to the braced form.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.bodyless-aspect-declarations.legality-1}

An aspect declaration with `;` in place of a braced body is exactly equivalent to `{ }` —
an aspect with zero methods and zero associated types. The bodyless production has no
syntax to carry a method or associated type, so this is pure notational sugar, not a
conditional exemption to check against a body that could otherwise be non-empty.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0103](../../rfcs/4-implemented/rfc-0103-bodyless-aspect-declarations.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/imported_annotation_names_are_valid/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Implementing an Aspect

```metel
struct Point {
    x: f64,
    y: f64,
}

aspect Printable {
    fun print(self);
}

extend Point: Printable {
    fun print(self) {
        print("(");
        print(self.x.to_string());
        print(", ");
        print(self.y.to_string());
        println(")");
    }
}

fun main() {
    let p := Point { x = 1.0, y = 2.0 };
    p.print();
}
```

**Aspect implementation method set.** An `extend Type: Aspect` block must define
exactly the methods declared by `Aspect`: every declared method must be present unless it
has a default body, and no additional methods are permitted. Put a type-specific method
that is not part of the aspect in an inherent `extend Type { ... }` block; [inherent and
aspect implementations may coexist for the same type](#spec.declarations.aspects.implementing-an-aspect.legality-1).

> **Changed in v0.12.1.** An undeclared method in an aspect implementation is rejected.

**Aspect implementation method signatures.** Each implementation method must
conform to the aspect's declaration of that method. The aspect signature is first
[specialized](#spec.declarations.aspects.implementing-an-aspect.legality-12) with
the block's target type for `Self`, its aspect arguments, and its associated-type
definitions; receiver form, ordinary parameter count and types, and result type
must then be equal. The method's generic constraints must be
[structurally equal](#spec.declarations.aspects.implementing-an-aspect.legality-13)
to the aspect method's after normalization — neither weakened nor strengthened —
with record kind part of the comparison. A method that does not conform is
[rejected at its own declaration](#spec.declarations.aspects.implementing-an-aspect.legality-14)
and does not satisfy the aspect.

```metel
aspect CopyOnly { fun pass<T: Copy>(value: T) -> T; }

extend Holder: CopyOnly {
    fun pass<T: Copy>(value: T) -> T { value }   // ok -- identical constraints
    // fun pass<T>(value: T) -> T { value }       // rejected: weakened (T0012)
}

aspect AnyValue { fun keep<T>(value: T) -> T; }

extend Holder: AnyValue {
    fun keep<record T>(value: T) -> T { value }   // rejected: strengthened (T0012)
}
```

> Letting an implementation *weaken* a constraint — admissible-domain inclusion,
> e.g. accepting `<record T>` in the aspect against a plain `<T>` implementation —
> is a later addition, RFC-0149. Until it lands, a widening is rejected here as a
> conservative wrong-no.

**Conditional extend blocks.** An aspect implementation for a
generic type may be conditional on its own type parameters satisfying additional
bounds, written in a `where` clause after the aspect clause (or inline, before the
target type):

```metel
struct Pair<A, B> { first: A, second: B }

extend Pair<A, B>: Printable where A: Printable, B: Printable {
    fun print(self) { ... }
}

// equivalent, inline form:
extend<A: Printable, B: Printable> Pair<A, B>: Printable { ... }
```

`Pair<i64, String>` is `Printable`; `Pair<i64, SomeNonPrintableType>` is not — both
remain constructable, since a struct's own unconditional bounds (above) and an extend
block's conditional bounds are checked independently. The compiler checks a conditional
block's bounds at every point the aspect is required — method call, bound check, impl
selection — not at the block's own declaration site:

```metel
fun print_pair<A: Printable, B: Printable>(p: Pair<A, B>) {
    p.print();   // ok -- conditional impl applies; A: Printable and B: Printable
}

fun use_pair(p: Pair<i64, SomeNonPrintable>) {
    p.print();   // error T0012: Pair<i64, SomeNonPrintable> does not implement
                 //   Printable, because SomeNonPrintable does not implement Printable
}
```

A generic function propagates a conditional extend block to its own callers by stating
the bound explicitly — the compiler never infers which bounds a caller needs:

```metel
fun print_sorted<T: Comparable + Printable>(list: SortedList<T>) {
    list.print();   // ok -- T: Printable, so the conditional extend block applies
}
```

Negative bounds may appear in a conditional `extend` block's `where` clause on the same
terms as positive ones:

```metel
extend<T: !Drop> Container<T>: BulkDrop { ... }
```

**Coherence.** Two conditional `extend` blocks of the same aspect for the same type are
a coherence error (`T0015`) unless they are provably disjoint. Disjointness is
established by **syntactic negation** only — one block must carry an explicit negative
bound that directly negates a positive bound in the other. The compiler performs no
inference beyond this direct check:

```metel
// Accepted -- T: !Copy directly negates T: Copy; provably disjoint
extend<T: Copy> Wrapper<T>: Serialize { ... }
extend<T: !Copy> Wrapper<T>: Serialize { ... }

// error T0015 -- no direct negation between Clone and Display; not provably disjoint
extend<T: Clone> Wrapper<T>: Serialize { ... }
extend<T: Display> Wrapper<T>: Serialize { ... }
```

A conditional `extend` block and an unconditional `extend` block for the same type
constructor are also a coherence error — the unconditional block already covers every
instantiation the conditional one would. Conditional blocks are subject to the same
orphan rule as unconditional ones (above): the aspect or the type's outermost
constructor must be local.

**Bare-parameter blanket impls.** `extend<T: Bound> T: Aspect` — where the target is
the block's own generic parameter rather than a named struct or enum wrapping it, e.g.
`extend<T: Copy> T: Clone` — is a distinct case from every other example in this
section, which all target a genuine named type (`Pair<A, B>`, `Container<T>`,
`Wrapper<T>`). A bare type parameter has no outermost type constructor for the orphan
rule (below) to check — it isn't declared in any module, including the block's own.
Target-locality is therefore **vacuously unsatisfiable** for this shape: such an extend
is permitted only through the aspect side of the orphan rule, never the target side.

```metel
// std::core — permitted: Clone is local to std::core
extend<T: Copy> T: Clone { fun clone(self: &T) -> T { self } }

// user module — permitted: MyAspect is local here
aspect MyAspect { fun tag(self) -> String; }
extend<T: Copy> T: MyAspect { fun tag(self) -> String { "copyable" } }

// user module — REJECTED (T0014): Display is foreign, and a bare-parameter
// target can never be local, anywhere
extend<T: Copy> T: Display { fun to_string(self) -> String { "?" } }
```

This confines any one aspect's bare-parameter blanket impl to a single module (its own
declaring module, or `std::core` for a built-in aspect) — no separate overlap-detection
mechanism is needed beyond the ordinary rule already stated above (two impls of the
same aspect conflict when some instantiation satisfies both): a competing
bare-parameter blanket from another module can never pass the orphan check in the
first place, and a concrete impl overlapping the blanket (e.g. a type implementing
`Clone` directly while also being `Copy`) is caught by the existing concrete-vs-blanket
overlap rule with no special case. See
`public/rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md`.

**Worked example — interaction with equality-constrained bounds.** A conditional
`extend` block's `where` clause accepts the same equality-constrained bound form
Associated Types (above) specifies for ordinary function bounds, since both are stored
and checked as the same `Bound` structure:

```metel
aspect Container { type Item: Display; fun get(self) -> Item; }

struct Wrapper<T> { inner: T }

extend<T: Container<Item = i64>> Wrapper<T>: Printable {
    fun print(self) { println(self.inner.get().to_string()); }
}
```

This composes without any new mechanism: the conditional block's bound-checking (this
section) and the equality-constraint-checking Associated Types already specifies are
the same call-site check, run once per bound in the `where` clause, regardless of
which kind of aspect the bound names.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-1}

An inherent implementation is written `extend Type { ... }`; an aspect implementation is
written `extend Type: Aspect { ... }`, and both forms may coexist for the same type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [75_inherent_alongside_aspect_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/75_inherent_alongside_aspect_impl.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/negative_impl_overrides_blanket_impl_permitted/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### `dyn Aspect`

> **Available now (RFC-0008, metel-core#865, metel-core#863, metel-core#864):
> syntax, type representation, object safety, coercion (including behind
> `&`/`&var`, at every position below), dispatch, and `List<dyn Aspect>`
> heterogeneous collections.**

`dyn Aspect` is an aspect object: a value whose concrete type is erased, with
dispatch happening through a vtable at runtime. It complements `extends Aspect`
(compile-time-fixed, zero-overhead) with the opposite trade-off — the concrete
type may vary at runtime, at the cost of an indirect call and a pointer's
worth of space:

```metel
fun show(x: &dyn Display) -> i64 { 0 }
fun holds_two(x: &var dyn Display) -> i64 { 0 }
fun many(x: dyn Display[]) -> i64 { 0 }

fun main() -> i64 { 0 }
```

Unlike `extends Aspect` — sugar for a fresh generic parameter, legal only in
parameter or return position — `dyn Aspect` is a real, existential type. It
may appear anywhere an ordinary type can: a `let` binding's annotation, a
struct field, a return type, behind `&`/`&var`, or as an array element.

**Not every aspect can be used this way.** An aspect is *object-safe* only if
every one of its methods can be dispatched through a vtable — see [Object
safety](#object-safety) below. A non-object-safe aspect is still fully usable
with `extends Aspect` (static dispatch); it just cannot appear in `dyn` position.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.dyn-aspect.legality-1}

`dyn Aspect` names a real, visible aspect — the same resolution `extends Aspect`
already uses — and is legal in any type position, with no restriction to
parameter or return position. An aspect object cannot be an `extend` target:
there is no one concrete type to register an impl against.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [dyn_aspect_type_in_various_positions.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/dyn_aspect_type_in_various_positions.mtl), [dyn_aspect_with_type_args.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/dyn_aspect_with_type_args.mtl), [neg_31_dyn_aspect_unknown_aspect_name.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_31_dyn_aspect_unknown_aspect_name.mtl), [neg_32_extend_dyn_aspect_target_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_32_extend_dyn_aspect_target_rejected.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

#### Object safety

An aspect is object-safe only if every one of its methods satisfies three
rules:

1. **Receiver rule.** The method's first parameter must be `self: &Self` or
   `self: &var Self`. A bare by-move receiver (`self: Self`), or no receiver
   at all (an associated function), is not object-safe — moving a value or
   locating an instance both need information `dyn Aspect`'s erasure has
   already discarded. `Self` appearing anywhere else in the signature — a
   non-receiver parameter, the return type — is also not object-safe.
2. **No generic methods.** A method with its own type parameters cannot be
   dispatched through a vtable, because the vtable entry would need to be
   generated per instantiation. Such a method is excluded from the vtable —
   this does not by itself disqualify the rest of the aspect.
3. **No associated types in signature.** A method whose signature references
   one of the aspect's own associated types makes that method's vtable entry
   depend on the concrete impl's binding for it, which erasure has discarded.

```metel
aspect Shape {
    fun area(&self) -> f64;   // object-safe: &self receiver, no Self, no assoc types
}

fun accepts_shape(x: dyn Shape) -> i64 { 0 }

fun main() -> i64 { 0 }
```

<!-- doc-example: expect-fail reason="Clone is not object-safe -- clone returns Self, the entire point of this example" -->
```metel
// `Clone::clone` returns `Self` -- not object-safe.
fun rejected(x: dyn Clone) -> i64 { 0 }
```

`std::core::Drop` needs no exception to rule 1: its one method is declared
`fun drop(&var self);` (RFC-0071), an ordinary `&var Self` receiver — `dyn
Drop` is object-safe the same way `dyn Shape` above is.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.dyn-aspect.legality-2}

A method's first parameter must be `self: &Self` or `self: &var Self` to be
object-safe; a by-move receiver, no receiver at all, or `Self` in any other
signature position, is not.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [dyn_drop_is_object_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/dyn_drop_is_object_safe.mtl), [neg_27_dyn_aspect_returns_self_not_object_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_27_dyn_aspect_returns_self_not_object_safe.mtl), [neg_29_dyn_aspect_self_by_value_receiver_not_object_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_29_dyn_aspect_self_by_value_receiver_not_object_safe.mtl), [neg_30_dyn_aspect_no_receiver_not_object_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_30_dyn_aspect_no_receiver_not_object_safe.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.dyn-aspect.legality-3}

A method with its own generic parameters is excluded from the vtable without
disqualifying the rest of the aspect — including when it is the aspect's
*only* method, the same way a zero-method marker aspect is object-safe.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [dyn_aspect_generic_method_excluded_not_disqualifying.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/dyn_aspect_generic_method_excluded_not_disqualifying.mtl), [dyn_aspect_only_generic_method_is_vacuously_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/dyn_aspect_only_generic_method_is_vacuously_safe.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.dyn-aspect.legality-4}

A method whose signature references one of the aspect's own associated types
is not object-safe.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md), [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_28_dyn_aspect_associated_type_in_signature_not_object_safe.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_28_dyn_aspect_associated_type_in_signature_not_object_safe.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

#### Coercion

A value of concrete type `T` coerces to `dyn Aspect` implicitly wherever a
`dyn Aspect`-typed value is expected — a `let`/`mut` binding, a function
argument, a return value — when `T` implements `Aspect`. No explicit cast is
needed, and the same coercion applies behind `&`/`&var`:

```metel
aspect Shape {
    fun area(&self) -> f64;
}

struct Circle { radius: f64 }

extend Circle: Shape {
    fun area(&self) -> f64 { 3.14159 * self.radius * self.radius }
}

fun main() -> i64 {
    let shape: dyn Shape := Circle { radius = 2.0 };
    let circle := Circle { radius = 1.0 };
    let borrowed: &dyn Shape := &circle;
    0
}
```

A concrete type that does not implement the target aspect is rejected at the
coercion site itself — a compile-time error, not a deferred runtime failure:

<!-- doc-example: expect-fail reason="Rock does not implement Display -- the coercion is rejected at the let site, not deferred to runtime" -->
```metel
struct Rock { }

fun main() -> i64 {
    let x: dyn Display := Rock { };
    0
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.dyn-aspect.legality-6}

A concrete value coerces to `dyn Aspect` implicitly at a binding, `var`
reassignment, function or method argument, return value, `break` value,
`(expr : Type)` ascription, struct-literal field, or array-literal element
position — owned or behind `&`/`&var` — when its type implements the aspect;
rejected with `T0012` when it does not.

A *heterogeneous* array literal — different concrete element types coerced
to `dyn Aspect` within one `[...]` expression — is accepted at a `let`/`var`
binding: each element is checked against the declared element type
independently, not against each other. `List<dyn Aspect>` (see
[Heterogeneous Collections](#heterogeneous-collections) below) remains the
way to build a heterogeneous collection incrementally, one `push` at a
time; a literal is the equivalent all-at-once form. (A heterogeneous
literal used directly as a function argument or struct field, with no
annotated binding in between, isn't covered by this — bind it to a
`let`/`var` first.)

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [100_dyn_aspect_reassignment_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/100_dyn_aspect_reassignment_coercion.mtl), [101_dyn_aspect_array_literal_element_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/101_dyn_aspect_array_literal_element_coercion.mtl), [102_dyn_aspect_return_position_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/102_dyn_aspect_return_position_coercion.mtl), [103_dyn_aspect_break_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/103_dyn_aspect_break_coercion.mtl), [104_dyn_aspect_ascription_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/104_dyn_aspect_ascription_coercion.mtl), [105_dyn_aspect_generic_aspect_return_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/105_dyn_aspect_generic_aspect_return_coercion.mtl), [106_dyn_aspect_reference_to_already_dyn_value.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/106_dyn_aspect_reference_to_already_dyn_value.mtl), [90_dyn_aspect_owned_coercion_and_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/90_dyn_aspect_owned_coercion_and_dispatch.mtl), [91_dyn_aspect_borrowed_reference_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/91_dyn_aspect_borrowed_reference_dispatch.mtl), [95_dyn_aspect_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/95_dyn_aspect_argument_coercion.mtl), [96_dyn_aspect_list_heterogeneous_collection.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/96_dyn_aspect_list_heterogeneous_collection.mtl), [97_dyn_aspect_by_reference_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/97_dyn_aspect_by_reference_argument_coercion.mtl), [98_dyn_aspect_by_mut_reference_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/98_dyn_aspect_by_mut_reference_argument_coercion.mtl), [99_dyn_aspect_struct_field_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/99_dyn_aspect_struct_field_coercion.mtl), [neg_33_dyn_aspect_coercion_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_33_dyn_aspect_coercion_target_type_does_not_implement_aspect.mtl), [neg_34_dyn_aspect_argument_coercion_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_34_dyn_aspect_argument_coercion_target_type_does_not_implement_aspect.mtl), [neg_35_dyn_aspect_list_push_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_35_dyn_aspect_list_push_target_type_does_not_implement_aspect.mtl), [neg_36_dyn_aspect_by_reference_argument_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_36_dyn_aspect_by_reference_argument_target_type_does_not_implement_aspect.mtl), [neg_37_dyn_aspect_by_mut_reference_argument_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_37_dyn_aspect_by_mut_reference_argument_target_type_does_not_implement_aspect.mtl), [neg_38_dyn_aspect_struct_field_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_38_dyn_aspect_struct_field_target_type_does_not_implement_aspect.mtl), [neg_39_dyn_aspect_reassignment_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_39_dyn_aspect_reassignment_target_type_does_not_implement_aspect.mtl), [neg_40_dyn_aspect_array_literal_element_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_40_dyn_aspect_array_literal_element_target_type_does_not_implement_aspect.mtl), [neg_41_dyn_aspect_return_position_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_41_dyn_aspect_return_position_target_type_does_not_implement_aspect.mtl), [neg_42_dyn_aspect_break_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_42_dyn_aspect_break_target_type_does_not_implement_aspect.mtl), [neg_43_dyn_aspect_ascription_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_43_dyn_aspect_ascription_target_type_does_not_implement_aspect.mtl), [neg_44_dyn_aspect_heterogeneous_array_literal_element_target_type_does_not_implement_aspect.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_44_dyn_aspect_heterogeneous_array_literal_element_target_type_does_not_implement_aspect.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

#### Dispatch

Calling a method on a `dyn Aspect` value — owned, `&`, or `&var` — resolves at
runtime to the wrapped concrete value's own implementation of the aspect.
Different concrete values behind the same `dyn Aspect` type dispatch
independently, including through mutation (`&var self`) on an owned binding:

```metel
aspect Shape {
    fun area(&self) -> f64;
}

struct Circle { radius: f64 }
struct Rectangle { w: f64, h: f64 }

extend Circle: Shape {
    fun area(&self) -> f64 { 3.14159 * self.radius * self.radius }
}

extend Rectangle: Shape {
    fun area(&self) -> f64 { self.w * self.h }
}

fun main() -> i64 {
    let a: dyn Shape := Circle { radius = 2.0 };
    let b: dyn Shape := Rectangle { w = 3.0, h = 4.0 };
    // `a.area()` and `b.area()` each dispatch to their own concrete impl.
    0
}
```

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.declarations.aspects.dyn-aspect.dynamics-1}

A method call through a `dyn Aspect` value — owned, `&`, or `&var` — resolves
at runtime to the implementation the wrapped concrete value's own type
provides for the aspect, independent of any other value coerced to the same
`dyn Aspect` type elsewhere in the program.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0008](../../rfcs/4-implemented/rfc-0008-aspect-objects.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [100_dyn_aspect_reassignment_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/100_dyn_aspect_reassignment_coercion.mtl), [101_dyn_aspect_array_literal_element_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/101_dyn_aspect_array_literal_element_coercion.mtl), [102_dyn_aspect_return_position_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/102_dyn_aspect_return_position_coercion.mtl), [103_dyn_aspect_break_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/103_dyn_aspect_break_coercion.mtl), [104_dyn_aspect_ascription_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/104_dyn_aspect_ascription_coercion.mtl), [105_dyn_aspect_generic_aspect_return_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/105_dyn_aspect_generic_aspect_return_coercion.mtl), [106_dyn_aspect_reference_to_already_dyn_value.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/106_dyn_aspect_reference_to_already_dyn_value.mtl), [90_dyn_aspect_owned_coercion_and_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/90_dyn_aspect_owned_coercion_and_dispatch.mtl), [91_dyn_aspect_borrowed_reference_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/91_dyn_aspect_borrowed_reference_dispatch.mtl), [92_dyn_aspect_multiple_concrete_types_dispatch_independently.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/92_dyn_aspect_multiple_concrete_types_dispatch_independently.mtl), [93_dyn_aspect_mutable_receiver_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/93_dyn_aspect_mutable_receiver_dispatch.mtl), [94_dyn_aspect_generic_aspect_type_args.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/94_dyn_aspect_generic_aspect_type_args.mtl), [95_dyn_aspect_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/95_dyn_aspect_argument_coercion.mtl), [96_dyn_aspect_list_heterogeneous_collection.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/96_dyn_aspect_list_heterogeneous_collection.mtl), [97_dyn_aspect_by_reference_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/97_dyn_aspect_by_reference_argument_coercion.mtl), [98_dyn_aspect_by_mut_reference_argument_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/98_dyn_aspect_by_mut_reference_argument_coercion.mtl), [99_dyn_aspect_struct_field_coercion.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/99_dyn_aspect_struct_field_coercion.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

#### Heterogeneous Collections

`List<dyn Aspect>` holds values of different concrete types together, each
satisfying a common aspect (RFC-0008 §7). `push`'s argument coerces to the
list's own `dyn Aspect` element type the same way any other argument
position does (see [Coercion](#coercion) above), and each element then
dispatches independently (see [Dispatch](#dispatch) above):

```metel
aspect Shape {
    fun area(&self) -> f64;
}

struct Circle { radius: f64 }
struct Rectangle { w: f64, h: f64 }

extend Circle: Shape {
    fun area(&self) -> f64 { 3.14159 * self.radius * self.radius }
}

extend Rectangle: Shape {
    fun area(&self) -> f64 { self.w * self.h }
}

fun main() -> i64 {
    var shapes: List<dyn Shape> := List::new();
    shapes.push(Circle { radius = 2.0 });
    shapes.push(Rectangle { w = 3.0, h = 4.0 });
    for (shape in shapes.as_slice()) {
        // each dispatches to its own concrete `area()`
    }
    0
}
```

A concrete type that does not implement the aspect is rejected at the
`push` call site itself, the same as any other argument-position coercion.

`List<T>` does not implement `Iterable<T>` for any `T` today, unrelated to
`dyn Aspect` — iterate via `.as_slice()` above, the same idiom `List<T>`'s
own methods (`map`/`filter`/`fold`/…) already use internally.

### Aspect Implementation Coherence

Every `(aspect, type)` pair has at most one implementation visible to the program, independent of module load order. Two rules make this checkable without a whole-program scan.

**Orphan rule.** `extend Type: Aspect` is permitted only when at least one of `Aspect`
or `Type`'s outermost type constructor is declared in the same module as the extend
block. Built-in aspects and built-in types count as local to `std::core`.

```metel
extend MyStruct: Display { ... }  // ok: MyStruct is local
extend i64: MyAspect { ... }      // ok: MyAspect is local
extend i64: Display { ... }       // ok only inside std::core: both are foreign elsewhere
```

A violating `extend` block is `T0014 — orphan implementation`. The orphan rule is what
keeps coherence a local, per-module property: a module can only add aspect
implementations it owns at least one half of, so no other module's impls need to be
consulted to know whether a given one is even legal.

**Overlap detection.** Two `extend` blocks of the same aspect conflict when some
concrete type instantiation would satisfy both. `extend List<i64>: Display` and
`extend List<String>: Display` don't conflict — disjoint element types — but
registering either one twice does. A conflict is `T0015 — conflicting implementation`,
reported at both impl spans. Combined with the orphan rule, an overlap can only arise
within a single module or between a module and `std::core`, so this check is local too.

**Closed-world assumption.** The set of impls in a program is fixed at compile time — nothing visible at compilation can add an impl later. This is what makes Negative Bounds, below, dischargeable from absence alone: `T: !Aspect` holds whenever no impl, concrete or blanket, applies to `T`, without requiring an explicit negative impl for every excluded type. A blanket `impl<T: Foo> Bar for T` is expanded when checking applicability — `T: !Bar` is provable only once no applicable blanket covers `T` either.

**Auto-impl aspects.** Auto-impls are a separate mechanism from this coherence
section. For coherence purposes, an auto-impl is treated as an ordinary
positive impl generated by the compiler: overlap detection and negative-impl override
both apply to it the same way they apply to an explicit `extend` block, while the
orphan rule does not apply because there is no authored impl site.

**Negative impl priority.** See Negative Impls, below, for the mechanism itself; the priority order coherence establishes is: an explicit negative impl beats an auto-impl or blanket positive impl for the same type, but an explicit positive impl and an explicit negative impl for the same concrete type is itself a `T0015` coherence error, not a priority question.

**What this deliberately doesn't cover.** Coherence here is scoped to a single program's module graph — a future package system, compiling packages separately, needs its own cross-package coherence model, not addressed here. Rejected alternatives (a global overlap check without the orphan rule, last-impl-wins ordering, an open-world assumption, specialisation) are recorded in the RFC, not repeated here — each fails a property this design keeps: coherence errors are local and order-independent, and overlapping impls are always illegal rather than resolved by specificity.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-5}

An authored `extend Type: Aspect` is rejected with `T0014` when neither the aspect nor
the target type's outermost constructor is local to the implementing module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0060](../../rfcs/4-implemented/rfc-0060-aspect-impl-coherence.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/orphan_impl_cross_module_violation/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-6}

Two positive implementations of the same aspect are rejected with `T0015` when a concrete
instantiation is covered by both implementations, including when a blanket implementation
covers an explicit concrete target.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0060](../../rfcs/4-implemented/rfc-0060-aspect-impl-coherence.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_25_negative_impl_conflicts_with_concrete_positive_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/neg_25_negative_impl_conflicts_with_concrete_positive_impl.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/blanket_vs_concrete_impl_conflict/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted_for_structural_target/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conflicting_impl_same_target/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-7}

A negative aspect bound is satisfied only when no reachable concrete or blanket
implementation of that aspect applies to the argument type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0060](../../rfcs/4-implemented/rfc-0060-aspect-impl-coherence.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [68_negative_bound_parses_and_is_unenforced.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/68_negative_bound_parses_and_is_unenforced.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-1}

A bare-parameter blanket implementation is an `extend` whose target is one of its own
generic parameters with no wrapping type constructor, such as `extend<T: Bound> T: Aspect`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0097](../../rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_local_aspect_permitted/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-2}

A bare-parameter target is local to no module. Such an implementation is legal only
when its aspect is local to the implementing module; target locality can never satisfy
the orphan rule for this form.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0097](../../rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_foreign_aspect_is_orphan/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_local_aspect_permitted/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-3}

Two bare-parameter blanket implementations of the same aspect conflict when an
instantiation can satisfy both bound sets, under the ordinary overlap rule; no
bare-parameter-specific overlap rule applies.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0097](../../rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_26_bare_parameter_blanket_overlap.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_26_bare_parameter_blanket_overlap.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-implementation-coherence.legality-4}

The bare-parameter rule applies only when the target is the parameter itself. Named
and structural targets remain subject to their ordinary orphan-rule locality rules.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0097](../../rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_23_structural_blanket_impl_orphan_violation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/neg_23_structural_blanket_impl_orphan_violation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Structural Aspect Bounds

Arrays (`T[]`), tuples (`(A, B)`, …), and function types (`|A| -> B`) are
**structural types** — built into the language rather than declared by a user, with no
name that can serve as an impl target the ordinary way. For the orphan rule (above),
structural type constructors are treated as belonging to `std::core`: a user module
may write `extend T[]: Aspect` only when `Aspect` itself is local to that module.

**Blanket impls for structural constructors.** `std::core` declares aspect impls for
structural constructors using the conditional `extend` syntax (above):

```metel
// std::core
extend<T: Display> T[]: Display {
    fun to_string(self: &T[]) -> String { ... }
}
```

This is what makes `println([1, 2, 3])` compile: `[1, 2, 3]` has type `i64[]`;
`i64: Display`; the conditional extend block applies. Coherence for structural impl
targets follows the same rules as any other conditional block (above) — two impls of
the same aspect for `T[]` conflict (`T0015`) unless one directly negates a bound the
other requires.

**Without a matching impl**, a structural type fails an aspect bound with a diagnostic naming the constructor:

```
T0012: i64[] does not implement Display
       hint: arrays implement Display only when their element type does;
             no extend<T: Display> T[]: Display is registered
```

**Standard array impls.** `std::core` provides `Display`, `Clone`, and `Eq` for
arrays, each conditional on the element type satisfying the same bound (element-wise
`to_string`/join, element-wise clone into new backing storage, and element-wise
equality respectively). These cannot be overridden by user code (orphan rule).
`List<T>` is a separate nominal struct; its impls coexist independently of the array
impls. `Ord` (RFC-0062, still `0-draft`) and `Hash` (not yet proposed) array impls are
not provided in this language version — neither aspect exists in `std::core` at all yet,
for arrays or otherwise.

> **Since v0.12.0 (RFC-0126): `T[]`'s `Clone` impl is replaced, not just
> reconditioned.** Once `T[]` owns nothing, "element-wise clone into new backing storage" is
> not just unconditional on the element type — it is impossible to implement as `T[]: Clone`
> at all: `Clone::clone(&self) -> Self` must produce a `T[]`, and a `T[]` can only ever borrow
> from something that already exists and outlives it, never from a buffer the impl just
> allocated for itself. `Display` and `Eq` are unaffected — they return `String`/`boolean`,
> not `Self`.

**Tuples** are deferred pending a decision on per-arity boilerplate vs. variadic generics — until then, tuples fail aspect bounds the same way arrays do without a matching impl (`(i64, String)` does not implement `Display`, with a hint to use a named struct instead).

**Function types.** A plain function and a closure share one type, `|A| -> B` (see [Functions — First-Class Functions](functions.md#first-class-functions)) — there is no separate `fun(A) -> B` function-pointer type or syntax; `fun(A) -> B` is a parse error. `Callable<A, B>` does not exist in `std::core` yet — despite being referenced elsewhere as the aspect a function type would formally satisfy, writing a bound or `extends Callable<A, B>` against it is a compile error (`T0003`, unknown aspect) today. A `|A| -> B` value behaves like `Copy` under `--move-check` (reusing one after copying it into another binding is accepted), but there is no working `Clone`: `.clone()` on a `|A| -> B` receiver fails to typecheck (`T0002`, cannot infer receiver type) regardless of annotation. `Display`, `Eq`, `Ord`, `Hash`, `Send`, `Sync`, and `Drop` are not implemented for function types either — there is no canonical string form, function equality is undecidable in general, `Send`/`Sync` aren't implemented for any type yet (RFC-0080, still `1-under-review`), and there is no state to drop.

**Array auto-impl propagation.** `T[]: Send`, `T[]: Sync`, and `T[]: Drop` are not
provided in this language version.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-1}

Structural type constructors are owned by `std::core` for orphan-rule purposes; outside
`std::core`, an implementation for one is legal only when the aspect is local.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_23_structural_blanket_impl_orphan_violation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/neg_23_structural_blanket_impl_orphan_violation.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted_for_structural_target/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-2}

`std::core` may declare conditional implementations for structural constructors; a
generic structural target is registered and dispatched subject to its stated bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [79_nested_array_display_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/79_nested_array_display_structural_impl.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted_for_structural_target/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_blocks_positive_bound_for_structural_target/main.mtl), [stage19_08_extend_generic_structural_targets_work.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage19_08_extend_generic_structural_targets_work.mtl), [stage19_neg_07_extend_concrete_array_target.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage19_neg_07_extend_concrete_array_target.mtl), [stage19_neg_07_extend_concrete_fun_target.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage19_neg_07_extend_concrete_fun_target.mtl), [stage19_neg_07_extend_concrete_record_target.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage19_neg_07_extend_concrete_record_target.mtl), [stage19_neg_07_extend_concrete_tuple_target.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage19_neg_07_extend_concrete_tuple_target.mtl), [stage19_neg_03_structural_array_element_bound_required.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage19_neg_03_structural_array_element_bound_required.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-3}

Without an applicable structural implementation, using a structural type where an aspect
bound is required is rejected with `T0012`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage19_neg_03_structural_array_element_bound_required.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage19_neg_03_structural_array_element_bound_required.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-4}

`std::core` provides `Display` and `Eq` for `T[]` when `T` satisfies the same aspect;
these implementations cannot be overridden by user code.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [79_nested_array_display_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/79_nested_array_display_structural_impl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-5}

Array marker-aspect propagation is not part of structural implementation lookup.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [76_array_display_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/76_array_display_structural_impl.mtl), [77_array_clone_structural_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/77_array_clone_structural_impl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-6}

Tuple types have no standard blanket aspect implementations and therefore fail aspect
bounds unless a separately specified implementation applies.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage3_05_tuple_array_suffix.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/types/stage3_05_tuple_array_suffix.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-7}

Function values have the ordinary function type `|A| -> B`; there is no separate
function-pointer type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_function_values_are_copy.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/41_function_values_are_copy.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-8}

`Callable<A, B>` is not available in `std::core`, so function types do not currently
satisfy a `Callable<A, B>` bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_function_values_are_copy.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/41_function_values_are_copy.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-9}

Function values are copyable for move checking, but do not satisfy aspect bounds such as
`Copy` or `Clone`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [41_function_values_are_copy.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/41_function_values_are_copy.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-10}

Function types do not implement `Display`, `Eq`, `Ord`, `Hash`, `Send`, `Sync`, or `Drop`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage19_neg_04_structural_function_eq_bound_required.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage19_neg_04_structural_function_eq_bound_required.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-11}

Closures and plain functions share the same function type; captures distinguish closure
values at runtime rather than introducing a distinct closure type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [07_closure_capture_of_non_copy_value.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/07_closure_capture_of_non_copy_value.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Associated Types

An aspect may declare an **associated type** — a type-level output that each
implementing type must specify — with `type Name;`. An `extend` block defines it with
`type Name = ConcreteType;`:

```metel
aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;
}

struct Boxed { value: i64 }

extend Boxed: Deref {
    type Target = i64;
    fun deref(self: &Boxed) -> &i64 { &self.value }
}
```

Inside the aspect block, the bare name (`Target`) is sugar for `Self::Target`. A bound
may be declared on the associated type, constraining every impl:

```metel
aspect Collection {
    type Item: Display;
}
```

**Projection.** In a generic context where `T: Aspect`, the associated type is written
`T::AssocType`:

```metel
fun deref_display<T: Deref>(x: &T) where T::Target: Display {
    println(x.deref());
}
```

`T::AssocType` is only valid when `T: Aspect` is in scope — writing it without that
bound is a compile error.

**Equality constraints in bounds.** `Aspect<AssocType = ConcreteType>` asserts both that
`T` implements `Aspect` and that its associated type equals a known type, pinning
`T::AssocType` to `ConcreteType` at every use:

```metel
fun deref_to_i64<T: Deref<Target = i64>>(x: &T) -> &i64 {
    x.deref()
}
```

`ConcreteType` doesn't have to be a fixed, known type — it can be a fresh type
parameter instead, which is also how disambiguation works (below).

**Disambiguation.** When `T` is bound to two or more aspects that each declare an
associated type of the same name, the bare projection is ambiguous — a hard error,
matching the existing method-name-collision rule (Static Dispatch Only, below):

```metel
aspect Deref { type Target; fun deref(self: &Self) -> &Target; }
aspect Convert { type Target; fun convert(self: &Self) -> Target; }

fun f<T: Deref + Convert>(x: &T) -> T::Target { ... }
// error: T::Target is ambiguous — both Deref and Convert declare Target
```

There's no dedicated disambiguation syntax for this — the equality constraint above
already covers it, by binding the associated type to a **fresh type parameter** rather
than a concrete one:

```metel
fun f<T: Deref<Target = U> + Convert, U>(x: &T) -> U {
    x.deref()   // ordinary method dispatch — deref and convert are different
                // method names, so this was never ambiguous to begin with
}
```

`U` is used unambiguously everywhere afterward — return type, `where` clauses, `let`
bindings — with no projection syntax involved. In practice this covers the real cases:
code reaches an associated type by calling the aspect's own uniquely-named method, and
the bare-projection ambiguity only arises when a type needs naming abstractly without
going through a call, which the fresh-variable equality constraint already handles.

**Associated type vs. a type parameter on the aspect.** Use an associated type when the
implementing type determines exactly one output (`Deref::Target` — a type has one deref
target). Use a type parameter on the aspect itself when a type may implement it for
multiple type arguments simultaneously (e.g. `From<i64>` and `From<String>` on the same
type). Writing `extend X: Deref<i64> {}` and `extend X: Deref<String> {}` side by side
would be the wrong model for `Deref` specifically — one type has one dereference target,
not several.

**Object safety.** An aspect with associated types is object-safe only if no method
signature references the associated type directly (see Static Dispatch Only, below, and
`dyn Aspect`, deferred to a future release). `Deref` above is *not* object-safe — `deref`
returns `&Target`, which varies per implementor, and a vtable entry cannot encode a
type that differs per implementation.

Negative bounds on projections such as `where T::Target: !Copy` are not specified in
this language version.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-1}

An associated type declared with `type Name;` is part of the aspect interface and must
be defined by each implementation of that aspect.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [71_associated_type_basic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/71_associated_type_basic.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-2}

If an associated-type declaration has a bound, the concrete type supplied by every
implementation must satisfy that bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage13_02_impl_provides_all_assoc_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_02_impl_provides_all_assoc_types.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-3}

Within an aspect or its implementation, a bare associated-type name denotes the
corresponding `Self::Name` projection and may be used in method signatures.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [74_projection_call_site_resolution.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/74_projection_call_site_resolution.mtl), [75_bare_name_sugar_in_default_method.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/75_bare_name_sugar_in_default_method.mtl), [87_self_assoc_type_projection_resolves.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/87_self_assoc_type_projection_resolves.mtl), [89_self_assoc_type_in_body_let_annotation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/89_self_assoc_type_in_body_let_annotation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-4}

An implementation must define every associated type declared by its aspect; its
definition fixes that projection to the implementation's concrete type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [71_associated_type_basic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/71_associated_type_basic.mtl), [80_conditional_impl_defines_assoc_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/80_conditional_impl_defines_assoc_type.mtl), [stage13_02_impl_provides_all_assoc_types.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_02_impl_provides_all_assoc_types.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-5}

A projection `T::AssocType` is valid only when the required `T: Aspect` bound is in
scope, and resolves to that implementation's associated type at an instantiation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [74_projection_call_site_resolution.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/74_projection_call_site_resolution.mtl), [80_conditional_impl_defines_assoc_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/80_conditional_impl_defines_assoc_type.mtl), [88_projection_return_type_infers_without_annotation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/88_projection_return_type_infers_without_annotation.mtl), [89_self_assoc_type_in_body_let_annotation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/89_self_assoc_type_in_body_let_annotation.mtl), [stage13_01_projection_in_return_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_01_projection_in_return_type.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-6}

A bare projection whose name is declared by more than one of `T`'s bound aspects is
ambiguous and is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage13_neg_12_ambiguous_associated_projection.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_neg_12_ambiguous_associated_projection.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.associated-types.legality-7}

An equality constraint such as `Aspect<AssocType = U>` pins the associated type to its
right-hand type; a fresh type parameter may therefore name an otherwise ambiguous
associated type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0082](../../rfcs/4-implemented/rfc-0082-associated-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage13_04_equality_constraint_pins_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_04_equality_constraint_pins_type.mtl), [stage13_10_equality_constraint_mismatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_10_equality_constraint_mismatch.mtl), [stage13_12_fresh_parameter_associated_type_disambiguation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_12_fresh_parameter_associated_type_disambiguation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Default Methods

> **Availability:** Since v0.7.0.

An aspect method may [supply a default body](#spec.declarations.aspects.default-methods.dynamics-1). An `extend` block may omit any method that
has a default; the aspect's implementation is inherited automatically.

```metel
aspect Greet {
    fun name(self) -> String;

    fun greet(self) -> String {
        return "Hello, " + self.name();
    }
}

struct Person {
    name: String,
}

extend Person: Greet {
    fun name(self) -> String {
        return self.name;
    }
    // greet() is inherited from the aspect default
}

fun main() {
    let p := Person { name = "Ada" };
    println(p.greet());   // Hello, Ada
}
```

A method without a default body [must be provided by every `extend` block](#spec.declarations.aspects.default-methods.legality-1); omitting it
is a compile-time error.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.declarations.aspects.default-methods.dynamics-1}

An aspect method with a body is a default implementation. An implementing `extend` block
that omits it inherits and dispatches to that body.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_01_default_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.default-methods.legality-1}

An implementing `extend` block must provide every aspect method that has no default body.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_neg_01_missing_required_with_defaults.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_neg_01_missing_required_with_defaults.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### The Self Type

[`Self` inside an aspect or an `extend` block refers to the concrete implementing type](#spec.declarations.aspects.the-self-type.legality-1).

In an aspect definition, `Self` is the implementing type at the call site:

```metel
aspect Comparable {
    fun compare(self, other: Self) -> i64;
}
```

In a struct or enum `extend` block, `Self` is an alias for the type being implemented:

> **Availability:** Since v0.7.0.

```metel
struct Point {
    x: i64,
}

extend Point {
    fun clone(self) -> Self {
        self
    }

    fun same_as(self, other: Self) -> boolean {
        self.x == other.x
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.the-self-type.legality-1}

Within an aspect declaration, `Self` denotes the type implementing that aspect. Within an
`extend` block, it denotes the block's target type.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage5_03_self_method_signatures.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_03_self_method_signatures.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Aspect Bounds on Function Type Parameters

> **Availability:** Since v0.7.0.

A generic function type parameter may declare an aspect bound using `:` syntax. The bound requires that any concrete type substituted for the parameter implements the named aspect. The named aspect must resolve where the declaration is written; an unknown aspect is error `T0003`, even when the generic function is never called. Passing a type that does not satisfy a resolved bound is error `T0012`, with the span on the offending call-site argument.

```metel
fun print_pair<T: Printable>(a: T, b: T) {
    a.print();
    b.print();
}
```

Inside the function body the typechecker treats `T` as having all methods declared by its bound aspects in scope. Calling a method not declared by any bound aspect on a bounded type parameter is a type error.

**Multiple bounds — inline `+` or `where` clause (equivalent).** Multiple bounds on a single type parameter may be expressed inline using `+`, or via a `where` clause, or a mix of both. The typechecker merges all declared bounds before enforcement — a type argument must satisfy every bound.

```metel
// Inline +
fun process<T: Comparable + Printable>(x: T) { ... }

// where clause (equivalent)
fun process<T>(x: T) where T: Comparable + Printable { ... }

// Mix — inline single bound plus additional where clause bound (also valid)
fun process<T: Comparable>(x: T) where T: Printable { ... }
```

All three forms above have identical semantics. The recommended style is inline `+` for short bound lists and `where` clause for longer or multi-parameter constraints.

**`extends Aspect` shorthand.** For type parameters used only once in a signature and not referenced elsewhere, the anonymous shorthand `extends Aspect` may be used directly in parameter position:

```metel
fun print_all(items: extends Printable[]) { ... }
// equivalent to:
fun print_all<_T: Printable>(items: _T[]) { ... }
```

Each `extends Aspect` occurrence in a signature is a **fresh, independent** type variable. To constrain two parameters to the same type, use a named type parameter.

**Return-position `extends Aspect`.** A function may return `extends Aspect` instead of a named type. The caller sees an opaque type known only to satisfy `Aspect` — no boxing, no heap allocation, no vtable, since the concrete type is fixed by the function's own body:

```metel
aspect Printable {
    fun print(self);
}

struct Adder { n: i64 }

extend Adder: Printable {
    fun print(self) {
        println("adds ${self.n}");
    }
}

fun make_adder(n: i64) -> extends Printable {
    Adder { n = n }
}

let add5 := make_adder(5);
add5.print();   // adds 5 — printable, but its concrete type is not nameable
```

A function returning `extends Aspect` must produce the **same concrete type on every code path** — the compiler resolves one fixed type per function definition, not per call:

<!-- doc-example: expect-fail reason="branches return different concrete types -- the whole point" -->
```metel
fun bad(flag: boolean) -> extends Display {
    if (flag) { 42 } else { "hello" }   // error: branches return different concrete types
}
```

Two calls to the same function return values of the same opaque type; two *different* `extends Aspect`-returning functions never share an opaque type even if their concrete implementations coincide. Each occurrence of `extends Aspect` in a signature is independent (as in parameter position, above) — a function with both an `extends Aspect` parameter and return type may return the parameter directly, in which case ordinary type inference unifies the two independent type variables:

```metel
fun transform(x: extends Display) -> extends Display {
    x   // return type inferred to be the same concrete type as x's
}
```

The caller may call any method the declared aspect provides, store the value, and pass it to anything accepting the same opaque type or aspect bound — but may not name the concrete type, cast it, or call methods outside the aspect even if the concrete type has them. Ownership (ownership/`Copy`/`Drop`, not yet integrated — RFC-0071) applies to the concrete type normally; the caller cannot observe which impls it has beyond the declared aspect bound.

**Worked example — interaction with associated types.** A function may return `extends Aspect` where `Aspect` declares an associated type; the caller can still use the aspect's own methods to produce values of that associated type, and those values type-check normally, even though the caller cannot name the opaque type itself:

```metel
aspect Container { type Item: Display; fun get(self) -> Item; }
struct IntBox { value: i64 }
extend IntBox: Container { type Item := i64; fun get(self) -> i64 { self.value } }

fun make_box(n: i64) -> extends Container {
    IntBox { value = n }
}

let v: i64 := make_box(42).get();   // resolves through Container's Item binding for
                                    // IntBox, the same associated-type mechanism
                                    // Associated Types (above) specifies -- the
                                    // caller never names IntBox, only Container.
```

This composes for free: the opaque return type is a real concrete type internally (erased only from the caller's *naming* surface, not from the typechecker's own bookkeeping), so associated-type resolution runs exactly as it does for a named type.

`extends Aspect` in struct fields, aspect aliases, named linkage between an `extends Aspect`
parameter and return type, and multiple aspect bounds in return position are not part
of this language version.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-1}

In a function parameter type, `extends Aspect` introduces an anonymous type parameter that
must satisfy `Aspect`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md), [rfc-0130](../../rfcs/4-implemented/rfc-0130-extends-aspect-renaming-impl-aspect-for-consistency-with-extend.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_13_legacy_impl_aspect_type_position.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_13_legacy_impl_aspect_type_position.mtl), [stage12_03_impl_aspect_param.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_03_impl_aspect_param.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-2}

Each parameter-position `extends Aspect` occurrence introduces an independent anonymous type
parameter. Reusing one concrete type across parameters requires a named type parameter.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_04_impl_aspect_independent.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_04_impl_aspect_independent.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-3}

Anonymous `extends Aspect` parameter types may coexist with named type parameters; neither
constrains the other unless the signature states a relation between them.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_03_impl_aspect_plus_where.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_03_impl_aspect_plus_where.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-4}

Every argument passed to an `extends Aspect` parameter must implement the declared aspect;
an argument that does not is a `T0012` type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_neg_02_impl_aspect_bound_not_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_neg_02_impl_aspect_bound_not_satisfied.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-5}

`extends Aspect` is rejected in a struct-field type annotation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_neg_10_impl_aspect_struct_field_array.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_10_impl_aspect_struct_field_array.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-6}

`extends Aspect` is rejected in a local binding type annotation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0035](../../rfcs/4-implemented/rfc-0035-impl-aspect-anonymous-params.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_neg_08_impl_aspect_local_let_array.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_08_impl_aspect_local_let_array.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-7}

At a generic-function call, each concrete type argument must satisfy every declared
aspect bound; inferred type arguments are checked by the same rule.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_01_fun_bound_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_01_fun_bound_satisfied.mtl), [stage12_neg_01_fun_bound_not_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_neg_01_fun_bound_not_satisfied.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-8}

A type argument that does not satisfy a function type parameter's aspect bound is a
`T0012` error reported at the offending call-site argument.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage12_neg_01_fun_bound_not_satisfied.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage12_neg_01_fun_bound_not_satisfied.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-9}

Within a generic function body, a bounded type parameter has the methods declared by
each of its bound aspects available; methods outside those bounds are rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_02_body_dispatch_all_bounds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_02_body_dispatch_all_bounds.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-10}

Inline `+` bounds, `where`-clause bounds, and a combination of the two have identical
semantics after their bounds are merged for each type parameter.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_02_body_dispatch_all_bounds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_02_body_dispatch_all_bounds.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-11}

Every bound in a multiple-bound list is independently required at a call site.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_02_body_dispatch_all_bounds.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_02_body_dispatch_all_bounds.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-12}

The bound checks for a parameter introduced by `extends Aspect` are the same as for an
equivalent named type parameter.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_03_impl_aspect_plus_where.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_03_impl_aspect_plus_where.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-13}

Generic methods in an `extend` block enforce their own bounds, while bounds on the
enclosing type remain available in the method body.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0040](../../rfcs/4-implemented/rfc-0040-function-aspect-bound-enforcement.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_11_impl_method_own_generic_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_11_impl_method_own_generic_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-14}

A return-position `extends Aspect` has one concrete type for every path through its function
body; branches that produce different concrete types are rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0037](../../rfcs/4-implemented/rfc-0037-return-position-impl-aspect.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_neg_01_return_impl_aspect_divergent_branches.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_01_return_impl_aspect_divergent_branches.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-15}

Each return-position `extends Aspect` occurrence is an independent opaque type. An
`extends Aspect` return may be inferred equal to an `extends Aspect` parameter when the body
returns that parameter directly.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0037](../../rfcs/4-implemented/rfc-0037-return-position-impl-aspect.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_04_return_impl_aspect_linked_to_param.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_04_return_impl_aspect_linked_to_param.mtl), [stage18_06_return_impl_aspect_tuple_independent.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_06_return_impl_aspect_tuple_independent.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-16}

A caller may use only the declared aspect interface of a return-position `extends Aspect`;
the caller may not name or cast its hidden concrete type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0037](../../rfcs/4-implemented/rfc-0037-return-position-impl-aspect.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_neg_03_return_impl_aspect_caller_cannot_name.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_03_return_impl_aspect_caller_cannot_name.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.dynamics-1}

Calls to the same `extends Aspect`-returning function produce values of the same opaque
type, and aspect methods declared for that return bound dispatch on those values.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0037](../../rfcs/4-implemented/rfc-0037-return-position-impl-aspect.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_01_return_impl_aspect_basic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_01_return_impl_aspect_basic.mtl), [stage18_02_return_impl_aspect_method_dispatch.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_02_return_impl_aspect_method_dispatch.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.dynamics-2}

Return-position `extends Aspect` values follow the ordinary ownership behavior of their
concrete type; opacity changes what callers can name, not the value's ownership.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0037](../../rfcs/4-implemented/rfc-0037-return-position-impl-aspect.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage18_01_return_impl_aspect_basic.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_01_return_impl_aspect_basic.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

---

### Negative Bounds

`T: !Aspect` is the complement of `T: Aspect`: it asserts that `T` does **not**
implement the named aspect. `!` binds tightly to the aspect name — `T: !Drop + Clone`
reads as `T: (!Drop) + Clone` — and positive and negative bounds may mix freely, inline
or in a `where` clause, on the same terms as ordinary bounds above.

```metel
fun move_out<T: !Drop, A: Alloc>(@a: A, ptr: @a T) -> T { ... }
```

**Satisfaction.** For a concrete type, `T: !Aspect` is satisfied exactly when no
implementation of `Aspect` for `T` is reachable — the same lookup used for a positive
bound, inverted. In a generic context, absence of a bound does not imply satisfaction:
a function requiring `T: !Drop` must declare it, since the type parameter could still be
instantiated with a `Drop`-implementing type otherwise.

**`Copy` implies `!Drop`.** Since `Copy` and `Drop` are mutually exclusive (see
Ownership, not yet integrated — RFC-0071), any type satisfying `T: Copy` automatically
satisfies `T: !Drop`, derived without an explicit declaration.

**Compound types.** `T: !Drop` is a claim about `T` itself, not its fields — a struct
with `Drop`-implementing fields but no `impl Drop` of its own satisfies `!Drop`; its
fields still drop normally through the ordinary per-field chain.

> Negative bounds do not by themselves let a type opt out of an aspect an existing
> blanket impl would otherwise grant — that's Negative Impls, directly below. Negative
> bounds are a use-site constraint; negative impls are a definition-site declaration
> that affects what the negative-bound check finds. See Aspect Implementation
> Coherence, above, for exactly which impls are reachable in the first place.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-1}

A negative bound is written `T: !Aspect` and may appear wherever a positive aspect bound
may appear; it binds tightly to the aspect name.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [68_negative_bound_parses_and_is_unenforced.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/68_negative_bound_parses_and_is_unenforced.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-2}

`T: !Aspect` is satisfied precisely when no reachable positive implementation of `Aspect`
applies to `T`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [68_negative_bound_parses_and_is_unenforced.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/68_negative_bound_parses_and_is_unenforced.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-3}

For a concrete type, negative-bound satisfaction is determined by the reachable
implementations of the negated aspect.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [68_negative_bound_parses_and_is_unenforced.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/68_negative_bound_parses_and_is_unenforced.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-4}

A generic type parameter does not satisfy a negative bound unless that bound is stated
and its eventual instantiation satisfies it.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage16_neg_01_negative_bound_violated.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage16_neg_01_negative_bound_violated.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-5}

Every type satisfying `Copy` also satisfies `!Drop`; no type may satisfy both `Copy` and
`Drop`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage16_03_copy_implies_not_drop.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage16_03_copy_implies_not_drop.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-6}

`T: !Drop` concerns `T`'s own `Drop` implementation, not whether any of its fields
implement `Drop`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage16_10_compound_negative_bound_ignores_fields.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage16_10_compound_negative_bound_ignores_fields.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-7}

Negative bounds are permitted in `where` clauses and are equivalent there to inline
negative bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage16_07_where_clause_negative_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage16_07_where_clause_negative_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-8}

A negative bound on a conditional implementation is checked at each instantiation on the
same terms as a positive conditional bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage16_neg_06_struct_negative_bound_violated_via_conditional_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage16_neg_06_struct_negative_bound_violated_via_conditional_impl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-9}

Negative bounds are use-site constraints and do not themselves declare that a type lacks
an aspect implementation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_overrides_blanket_positive/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-bounds.legality-10}

Explicit negative implementations are a distinct definition-site mechanism that affects
which implementations negative-bound checking finds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0072](../../rfcs/4-implemented/rfc-0072-negative-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_overrides_blanket_positive/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Negative Impls

A library author declares that a type **definitively** does not implement an aspect
with `extend Type: !Aspect;` — body always empty, since a negative impl is a
declaration of non-implementation, not a definition of behavior:

```metel
extend<T> Rc<T>: !Send;
extend<T> Rc<T>: !Sync;
```

More generally, a bodyless `extend` block is permitted whenever the body would be empty
already (RFC-0102):

```metel
aspect Copy2;

struct Handle { id: i64 }

extend Handle: Copy2;
extend Handle: !Send;
extend Handle: Copy2, !Send;
```

A methodless aspect declaration may itself be written bodylessly as `aspect Name;`
(RFC-0103), as in the `Copy2` example above.

`extend Type: Aspect;` is valid only when every method of `Aspect` already has a
default body and the aspect declares no associated types. `extend Type: !Aspect;` is
always valid, and the braced negative form is retired in favor of the bodyless one.

**Why this needs its own mechanism, not just the absence of a positive impl.** A
blanket impl can inadvertently grant an aspect to a type that must not have it — `Rc<T>`
would satisfy an auto-derived `Send` blanket (its field is an ordinary, `Send`-by-value
integer) even though sharing it across fibers is unsound. A negative impl overrides any
blanket that would otherwise apply: `Rc<T>: !Send` holds for all `T`, regardless of what
a blanket impl elsewhere says.

**Finality.** No positive impl may coexist with a negative impl for the same type and
aspect — a concrete `extend Type: Aspect` alongside `extend Type: !Aspect` is a
coherence error. A negative impl overriding a *blanket* positive impl is the intended,
allowed case; a negative impl does not propagate to subtypes or supertypes (`extend
Rc<T>: !Send` says nothing about `Arc<T>`).

**Orphan rules apply the same way as positive impls** (Aspect Implementation Coherence,
above) — a negative impl is permitted only when the aspect or the type is local to
the current module or stdlib. A positive and a negative impl for the same concrete
type is `T0015`, the same coherence error two conflicting positive impls produce.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-1}

A bodyless positive `extend Type: Aspect;` is legal exactly when the corresponding empty
braced implementation is legal: the aspect has no required methods and no associated type
requiring a binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0102](../../rfcs/4-implemented/rfc-0102-bodyless-extend-blocks-for-marker-aspects-and-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [94_copy_aspect_accepts_structural_and_nominal.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/94_copy_aspect_accepts_structural_and_nominal.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.aspects.negative-impls.dynamics-1}

A bodyless single-aspect `extend` has the same declaration semantics as the corresponding
empty braced implementation; it introduces no bodyless-specific validation category.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0102](../../rfcs/4-implemented/rfc-0102-bodyless-extend-blocks-for-marker-aspects-and-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [82_bodyless_multi_aspect_extend.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/82_bodyless_multi_aspect_extend.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-2}

An explicit negative implementation overrides an applicable blanket positive
implementation for its concrete target, while an explicit positive and explicit negative
implementation for that same target are rejected with `T0015`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0060](../../rfcs/4-implemented/rfc-0060-aspect-impl-coherence.md), [rfc-0081](../../rfcs/4-implemented/rfc-0081-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_25_negative_impl_conflicts_with_concrete_positive_impl.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/neg_25_negative_impl_conflicts_with_concrete_positive_impl.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-3}

A negative implementation must use the bodyless spelling `extend Type: !Aspect;`; the
braced spelling is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0102](../../rfcs/4-implemented/rfc-0102-bodyless-extend-blocks-for-marker-aspects-and-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [neg_07_negative_extend_requires_bodyless_form.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/neg_07_negative_extend_requires_bodyless_form.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.aspects.negative-impls.dynamics-2}

A bodyless multi-aspect `extend Type: A, B, !C;` is equivalent to independent bodyless
single-aspect declarations for `A`, `B`, and `!C`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0102](../../rfcs/4-implemented/rfc-0102-bodyless-extend-blocks-for-marker-aspects-and-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [82_bodyless_multi_aspect_extend.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/82_bodyless_multi_aspect_extend.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-4}

A negative implementation is a bodyless declaration of non-implementation: it provides no
required or default aspect methods, and may name a generic or concrete target.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0081](../../rfcs/4-implemented/rfc-0081-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [70_negative_impl_parses.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/70_negative_impl_parses.mtl), [73_negative_impl_not_required_to_provide_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/73_negative_impl_not_required_to_provide_methods.mtl), [neg_24_negative_impl_does_not_inherit_default_methods.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/aspects/neg_24_negative_impl_does_not_inherit_default_methods.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-5}

An explicit negative implementation overrides an applicable blanket positive implementation
for its target and satisfies a corresponding negative bound; it applies only to that target,
not to another nominal type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0081](../../rfcs/4-implemented/rfc-0081-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_blocks_positive_bound/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_blocks_positive_bound_for_structural_target/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/generic_negative_impl_overrides_blanket_positive/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/negative_impl_does_not_inherit/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.negative-impls.legality-6}

Negative implementations obey the ordinary orphan rule: the aspect or the target's outermost
constructor must be local to the module containing the `extend` declaration.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0081](../../rfcs/4-implemented/rfc-0081-negative-impls.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/aspects/negative_impl_orphan_violation/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

---

### Aspect Bounds on Struct and Enum Type Parameters

> **Availability:** Since v0.7.0.

A struct or enum generic type parameter may declare an aspect bound. The bound is enforced at **construction time**: instantiating the type with a concrete type argument that does not implement the bound is error `T0012`, with the span on the offending type argument at the construction call site.

```metel
struct SortedList<T: Comparable> {
    items: T[],
}

// error[T0012]: NonComparable does not implement Comparable
let list = SortedList<NonComparable> { items = [] }
```

The same inline `+` and `where` clause forms apply, with identical semantics:

```metel
// Multiple inline bounds
struct Window<T: Comparable + Printable> { items: T[] }

// where clause (equivalent)
struct Cache<K, V> where K: Hashable + Comparable { entries: Pair<K, V>[] }
```

**Bound propagation.** A struct's bounds are automatically available — without re-declaration — in:

- `extend` blocks on the same struct: `extend SortedList<T>` has `T: Comparable` in scope
- `extend Struct<T>: AspectName` blocks: the struct's bounds are inherited
- Match arm bodies when matching a value of the bounded struct or enum type

The bound is an invariant of the type, not of the binding site. It propagates wherever a value of that type is used. See Conditional Impl Blocks, above, for how this interacts with an aspect impl's own additional bounds.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-struct-and-enum-type-parameters.legality-1}

A generic struct or enum parameter may carry aspect bounds inline, in a `where` clause,
or in both forms. `+` joins multiple bounds, and bounds from the two forms on the same
parameter are combined.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0034](../../rfcs/4-implemented/rfc-0034-struct-enum-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage13_03_inline_and_where_merged.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage13_03_inline_and_where_merged.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-struct-and-enum-type-parameters.legality-2}

Constructing a bounded struct or enum with a concrete type argument that does not
satisfy every declared aspect bound is rejected with `T0012` at that type argument.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0034](../../rfcs/4-implemented/rfc-0034-struct-enum-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_neg_04_enum_construction_bound_violated.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_neg_04_enum_construction_bound_violated.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-struct-and-enum-type-parameters.legality-3}

An inherent `extend Struct<T>` inherits the declared aspect bounds of `Struct<T>`; its
methods may use those aspect operations on `T` without restating the bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0034](../../rfcs/4-implemented/rfc-0034-struct-enum-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [stage14_10_impl_method_with_bounded_type_param.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/stage14_10_impl_method_with_bounded_type_param.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-struct-and-enum-type-parameters.legality-4}

An aspect implementation `extend Struct<T>: Aspect` likewise inherits `Struct<T>`'s
declared aspect bounds without a duplicate declaration.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0034](../../rfcs/4-implemented/rfc-0034-struct-enum-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [rfc0034_aspect_extend_and_match_bound.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/rfc0034_aspect_extend_and_match_bound.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.aspect-bounds-on-struct-and-enum-type-parameters.legality-5}

A match arm's body, when matching a value of a bounded struct or enum type, has that
type parameter's declared aspect bounds available the same way any other use site does —
no re-declaration needed.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0034](../../rfcs/4-implemented/rfc-0034-struct-enum-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [struct_pattern_preserves_generic_bound_in_arm_body.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/generics/struct_pattern_preserves_generic_bound_in_arm_body.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

---

### Static Dispatch Only

All aspect dispatch in Metel is [**static** (monomorphised at compile time)](#spec.declarations.aspects.static-dispatch-only.dynamics-1). There are no vtables, no heap allocation, and no runtime type erasure for aspects.

Method resolution must also be **unambiguous** at compile time. If the same receiver
type implements two different aspects that both define the same method name, a call
like `value.method()` is [rejected with `T0013`](#spec.declarations.aspects.static-dispatch-only.legality-1) rather than resolved by declaration order.

`dyn Aspect` (runtime-dispatched existential types with vtable-based dispatch) is not
part of this language version. All polymorphism goes through generic type parameters
with aspect bounds.

Aspect objects (`dyn Aspect`) are not part of the language. All polymorphism is via generics (static dispatch).

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.declarations.aspects.static-dispatch-only.dynamics-1}

Aspect method calls are resolved statically for their concrete type arguments; aspect
values use neither runtime type erasure nor vtable dispatch.

<!-- rfc.py:exemption kind="untestable" reason="Whether the compiler uses monomorphisation rather than vtables is a compilation-strategy property, not behavior an .mtl fixture can observe." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Whether the compiler uses monomorphisation rather than vtables is a compilation-strategy property, not behavior an .mtl fixture can observe._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.declarations.aspects.static-dispatch-only.legality-1}

If applicable aspects for the same receiver type provide the same method name, an unqualified
dot call is ambiguous and is rejected with `T0013`.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>
