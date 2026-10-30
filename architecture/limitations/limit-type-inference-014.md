---
id: LIMIT-TYPE-INFERENCE-014
title: "A local function still sees the locals of its enclosing function; RFC-0195 says it does not"
summary: "A non-generic local `fun` reads and mutates enclosing locals with no capture list, and a generic one is `I0010`."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#1708"
disposition: resolved
review: null
---

## Limitation

The specification says the body of a local `fun` does not see the locals or type parameters of its enclosing
function (`spec.functions.local-functions.legality-1`, RFC-0195). The checker does not enforce it. A non-generic
local function reads and mutates an enclosing `var`, and the generic form is rejected on reconstruction:

```metel
fun main() {
    var n := 0;
    fun bump() { n += 1; }              // accepted today; `n` is a local of `main`
    bump();
}
```

```metel
fun main() {
    var n := 0;
    fun bump<T>(x: T) -> T { n += 1; x }   // I0010: the definition is accepted, reconstruction rejects `n`
}
```

The enclosing function's type parameter is rejected too, with a misleading `T0001: expected T, found type parameter T`.

## Impact

The closure checks (capture lists, `once`, `var`) are bypassed by a local `fun`, and the generic and non-generic
forms disagree. Two fixtures touch it: `evaluator/functions/79_nested_fun_forward_ref_in_let_initializer` mutates an
enclosing `var`, and `typechecking/generics/rigid_nested_function_captures_enclosing_parameter` expects `T0001`.
Both are rewritten by the implementation change.

## Affects

- `spec.functions.local-functions.legality-1`
- `spec.types.generics.rigid-type-parameters.legality-1`

## Resolution

Resolved by RFC-0195 (`4-implemented`): the checker rejects a local function that names an enclosing local or type parameter with `T0003`, for the generic and non-generic form alike. Evidence: `evaluator/functions/v0_15_0_neg_local_fun_uses_enclosing_var`, `v0_15_0_neg_generic_local_fun_uses_enclosing_var`, `v0_15_0_neg_local_fun_uses_enclosing_parameter`, `v0_15_0_neg_local_fun_uses_enclosing_type_parameter` and `typechecking/generics/nested_function_cannot_use_enclosing_parameter`; `v0_15_0_local_fun_sees_items_not_locals` keeps the visible names working.
