---
id: LIMIT-TYPE-INFERENCE-013
title: "A private free function still infers its signature; RFC-0193 requires it written"
summary: "A private free function infers its parameter and return types from its body, and a method with no return type returns `()`, so one omitted type means two things."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#1544 (the measurement behind RFC-0193)"
disposition: resolved
review: null
---

## Limitation

The specification says a named declaration writes every parameter's type and its return type, or returns `()`
(`spec.functions.named-function-declarations.legality-2`, RFC-0193). The checker does not enforce it yet. A
private free function with an unannotated parameter or no return type gets a fresh type variable and is
inferred from its body, in dependency order, while a method's signature is built with the unit type for the
same omission:

```metel
fun double(value) { value * 2 }     // accepted today: inferred as (i64) -> i64 at its uses
fun f() { 1 }                       // accepted today: returns 1
```

```metel
extend Box { fun get(&self) { self.v } }   // T0001: cannot unify i64 with ()
```

## Impact

A body edit changes every caller's type for a private function, and the same omission means different things
for a function and a method. Fixtures that test inference of a named signature
(`typechecking/functions/80_named_function_inferred_signature`, `abstract_inferred_operand_*`, `limit_01`,
`limit_03`, `typechecking/functions/06_let_polymorphism`) cite the rule above and pass today; they are
rewritten by the implementation change. A `public let`/`public var` is a parse error today where the spec
asks for a targeted message that names the fix.

## Affects

- `spec.functions.named-function-declarations.legality-2`
- `spec.modules.visibility.legality-10`

## Resolution

Resolved by RFC-0193 (`4-implemented`): a parameter of a named function or method with no type is `T0010`; an omitted return type means `()` at every declaration kind, so a non-unit body is a `T0001` that names the omitted annotation; `public let` is a targeted parse error. Evidence: `evaluator/functions/v0_15_0_neg_named_function_no_return_type_offers_closure`, `v0_15_0_neg_named_function_no_return_type_names_the_type`, `v0_15_0_neg_named_function_literal_body_no_return_type`, `v0_15_0_neg_method_no_return_type`, `v0_15_0_neg_named_function_unannotated_parameter`, `v0_15_0_neg_method_unannotated_parameter`, `v0_15_0_neg_public_let_is_not_valid` and the positive `v0_15_0_named_function_signature_written_or_unit`.
