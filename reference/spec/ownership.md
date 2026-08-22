---
title: "Ownership and Move Semantics"
---

# Ownership and Move Semantics

> **Planned for v0.12.0 (RFC-0071): values move by default; `Copy` and `Drop` are opt-in aspects.**

Nothing on this page is enforced by the current interpreter, which copies every value. The
rules below describe the model v0.12.0 introduces.

## Values move by default

A value whose type is not `Copy` has exactly one owner at any point. Assigning it, passing it
as an argument, or returning it **moves** it: ownership transfers, and the source binding
becomes invalid.

```metel
struct Buffer { data: i64[] }

fun consume(b: Buffer) -> i64 { b.data.len() }

fun main() {
    let a = Buffer { data = [1, 2, 3] };
    let b = a;          // a is moved into b
    // let n = a.data;  // error: `a` was moved
    consume(b);         // b is moved into consume
    // consume(b);      // error: `b` was moved
}
```

Primitive types and any type implementing `Copy` are exempt — they are duplicated instead.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.values-move-by-default.legality-1}

Using a non-`Copy` value in assignment, argument, or return position moves it; a later use
of the source binding is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [01_move_then_use.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## `Copy`

`Copy` marks a type whose values may be duplicated rather than moved. It is **opt in**, and
declared like any other aspect:

```metel
struct Point { x: f64, y: f64 }
extend Point: Copy;
```

A type may implement `Copy` only if every one of its fields — or, for an enum, every payload
in every variant — is itself `Copy`. Fixed-size arrays and tuples are `Copy` when their
elements are.

**References:** `&T` is `Copy`. `&var T` is not — an exclusive reference must remain unique,
so it is moved or reborrowed rather than duplicated.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.copy.legality-1}

A declared `Copy` implementation is legal only when every struct field or enum payload is
`Copy`; conditional implementations are considered under their declared bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [96_copy_eligibility_sees_conditional_impls.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/96_copy_eligibility_sees_conditional_impls.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## `Drop`

`Drop` gives a type destructor logic that runs when a value goes out of scope:

```metel
struct Handle { fd: i64 }

extend Handle: Drop {
    fun drop(self) { close_fd(self.fd); }
}
```

`Drop` is opt in. A type without a `Drop` implementation is reclaimed by recursively dropping
its fields.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.drop.legality-1}

An `extend Type: Drop` declaration gives its type `Drop` status even when its `drop` body is
empty; that status participates in ownership restrictions.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [03_partial_move_of_drop_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/03_partial_move_of_drop_type.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## `Copy` and `Drop` are mutually exclusive

A type may not implement both. A `Copy` value may be duplicated freely, so there is no single
point at which a destructor should run.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.copy-and-drop-are-mutually-exclusive.legality-1}

No concrete type instantiation may implement both `Copy` and `Drop`; overlapping conditional
implementations are rejected only when an instantiation would receive both aspects.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [95_copy_and_drop_non_overlapping_impls.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/95_copy_and_drop_non_overlapping_impls.mtl), [stage5_neg_34_copy_and_drop_overlapping_conditional_impls.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_34_copy_and_drop_overlapping_conditional_impls.mtl), [stage5_neg_35_copy_blanket_reaches_drop_instantiation.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_35_copy_blanket_reaches_drop_instantiation.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Drop order

Within a scope, values are [dropped in **reverse declaration order**](#spec.ownership.drop-order.dynamics-1). A value that has been
moved out is not dropped where it was declared — the new owner drops it.

For a type with a `Drop` implementation, [`drop(self)` runs first, then its fields are dropped
recursively](#spec.ownership.drop-order.dynamics-2).

For a struct that owns an allocator (`struct Parser(@a: BumpAlloc)`), the struct's fields are
dropped before the owned arena is freed, so any `@a T` pointers held as fields are reclaimed
while their backing memory is still valid.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.ownership.drop-order.dynamics-1}

When a scope ends, its still-owned values are dropped in reverse declaration order. A value
moved to another owner is dropped by that owner instead.

##### Dynamic Semantics {#spec.ownership.drop-order.dynamics-2}

Dropping a value with a `Drop` implementation invokes `drop(self)` before recursively dropping
its fields; a struct's fields are dropped before an allocator it owns is freed.

</details>

## Explicit drop

[`drop(x)` consumes `x`, runs its destructor if it has one, and marks the binding moved](#spec.ownership.explicit-drop.dynamics-1). Using
`x` afterwards is [an error, exactly as after any other move](#spec.ownership.explicit-drop.legality-1).

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.explicit-drop.legality-1}

After `drop(x)` consumes a non-`Copy` binding, that binding may not be used again.

##### Dynamic Semantics {#spec.ownership.explicit-drop.dynamics-1}

`drop(x)` consumes `x` and invokes its destructor when its type implements `Drop`.

</details>

## Partial moves

Moving a field out of a struct leaves the containing value **partially moved**. The remaining
fields stay accessible; the value as a whole does not.

<!-- doc-example: skip reason="uses Buffer from the earlier block in this doc" -->
```metel
struct Pair { a: Buffer, b: i64 }

fun main() {
    let p = Pair { a = Buffer { data = [1] }, b = 42 };
    let x = p.a;        // p.a moved out; p is partially moved
    let y = p.b;        // still fine — p.b was not moved
    // consume_pair(p); // error: `p` cannot be used as a whole
}
```

Tracking is at **field granularity**. Pattern destructuring may move several fields at once,
under the same rules.

**A type implementing `Drop` may not be partially moved** — its destructor requires the whole
value.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.partial-moves.legality-1}

After a field of a non-`Drop` struct is moved, the remaining fields may be accessed but the
containing value may not be used as a whole.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [02_partial_move_used_as_whole.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/02_partial_move_used_as_whole.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-2}

A field of a `Drop` type may not be moved out.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [03_partial_move_of_drop_type.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/03_partial_move_of_drop_type.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

> **Planned for v0.12.0 (RFC-0071): a `Drop` type may still be partially *borrowed*; only moving out is restricted.**

### Which constructs support partial moves

| construct | partial move |
|---|---|
| struct fields | yes, at field granularity |
| tuple elements | yes — positional fields are statically named |
| record fields | [yes, and the residual takes a narrower record type](#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2) |
| enum payloads | no — matching a variant and moving its payload consumes the enum wholly |
| array elements | **no** |

An array element cannot be moved out because the index may be computed at run time, so which
element left is not a static fact.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-1}

Tuple elements may be moved independently; moving an enum payload consumes its enum wholly;
array elements may not be moved out; and a non-`Copy` closure capture moves its enclosing binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [04_tuple_element_move_then_use.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/04_tuple_element_move_then_use.mtl), [05_enum_payload_consumes_whole_value.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/05_enum_payload_consumes_whole_value.mtl), [06_array_element_move_is_banned.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/06_array_element_move_is_banned.mtl), [07_closure_capture_of_non_copy_value.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/07_closure_capture_of_non_copy_value.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2}

Record fields may be moved independently; after such a move, the residual record has the
remaining fields' narrower record type.

</details>

## References and moves

`&T` is `Copy`, so a shared reference is duplicated on use and the original stays valid.

`&var T` is **not** `Copy` — an exclusive reference must stay unique to be exclusive. It is
therefore moved on use, with one exception:

> **Planned for v0.12.0 (RFC-0071): passing a `&var T` as an argument to a parameter of type
> `&var T` reborrows it rather than moving it — the original binding remains usable after the
> call. Every other use moves.**

```metel
struct Counter { n: i64 }

fun bump(r: &var Counter) { }

fun main() {
    var c = Counter { n = 0 };
    let r = &var c;
    bump(r);
    bump(r);      // fine — each call reborrows

    let q = r;    // moves: plain binding is not a reborrow
    // bump(r);   // error: `r` was moved into `q`
}
```

Returning a reference, storing one in a struct, and capturing one in a closure all move it,
for the same reason `let` does: a reborrow lasts for a call, and none of those is bounded by
one.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.references-and-moves.legality-1}

A non-`Copy` value may not be moved out through either kind of reference; a shared reference
itself is `Copy`, while an exclusive reference is moved except for an argument-position
reborrow to an `&var` parameter.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [10_mut_ref_non_reborrow_move.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/10_mut_ref_non_reborrow_move.mtl), [48_move_through_explicit_deref_is_banned_on_first_use.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/48_move_through_explicit_deref_is_banned_on_first_use.mtl), [65_general_assignment_out_of_an_explicit_deref_is_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/65_general_assignment_out_of_an_explicit_deref_is_rejected.mtl), [66_by_value_argument_passing_out_of_an_explicit_deref_is_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/66_by_value_argument_passing_out_of_an_explicit_deref_is_rejected.mtl), [70_shared_reference_is_copy.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/70_shared_reference_is_copy.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

The reborrow's *duration* is not tracked — tracking it is the borrow checker's job. The rule
above only prevents a reference from being consumed; it grants no exclusivity guarantee. See
[What ownership does not cover](#what-ownership-does-not-cover).

## Closures

Closures capture by value, so capturing a non-`Copy` value **moves** it. To keep using the
original, capture a shared reference — `&T` is `Copy`, so the reference is duplicated and the
referent is untouched.

## What ownership does not cover

Ownership answers *how many owners a value has*, and `Copy` answers *whether a value may be
duplicated*. Neither answers *what is borrowed at a given point* — that is the borrow
checker's job, and it is not part of this release. In particular, nothing here prevents two
`&var T` references to the same place; see the References section of the Type System page.
