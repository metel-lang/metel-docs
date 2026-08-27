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

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until implementation issue #261 (drop order and explicit drop, RFC-0071 3/4) lands. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until implementation issue #261 (drop order and explicit drop, RFC-0071 3/4) lands. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.drop-order.dynamics-2}

Dropping a value with a `Drop` implementation invokes `drop(self)` before recursively dropping
its fields; a struct's fields are dropped before an allocator it owns is freed.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Same root gap as drop-order.dynamics-1: destructor invocation is not implemented, so drop(self)-before-fields ordering cannot be observed. #261 also separately tracks the allocator-ordering half." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Same root gap as drop-order.dynamics-1: destructor invocation is not implemented, so drop(self)-before-fields ordering cannot be observed. #261 also separately tracks the allocator-ordering half._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

## Explicit drop

[`drop(x)` consumes `x`, runs its destructor if it has one, and marks the binding moved](#spec.ownership.explicit-drop.dynamics-1). Using
`x` afterwards is [an error, exactly as after any other move](#spec.ownership.explicit-drop.legality-1).

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.explicit-drop.legality-1}

After `drop(x)` consumes a non-`Copy` binding, that binding may not be used again.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Explicit drop(x) is not implemented -- drop is not a built-in name today (verified directly: it produces a T0003 undefined-name error), so this use-after-drop rejection cannot be observed. Tracked by #261, which also depends on move tracking (#579)." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Explicit drop(x) is not implemented -- drop is not a built-in name today (verified directly: it produces a T0003 undefined-name error), so this use-after-drop rejection cannot be observed. Tracked by #261, which also depends on move tracking (#579)._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.explicit-drop.dynamics-1}

`drop(x)` consumes `x` and invokes its destructor when its type implements `Drop`.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Same root gap as explicit-drop.legality-1: drop is not a built-in yet, so this dynamic-semantics claim cannot be exercised." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Same root gap as explicit-drop.legality-1: drop is not a built-in yet, so this dynamic-semantics claim cannot be exercised._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

## Partial moves

> **Planned for v0.13.0 (RFC-0137): the residual gets a named type, not just internal
> bookkeeping — `Handle` becomes `Handle.{ fd }`.** See "Narrowing" below.

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

> **Planned for v0.13.0 (RFC-0137): legality-2's ban is superseded in design by
> row-bounded `Drop` dispatch — see "Drop dispatch against a narrowed residual" below.
> Until that mechanism is built, this ban is enforced exactly as stated, unconditionally.**

### Which constructs support partial moves

| construct | partial move |
|---|---|
| struct fields | yes, at field granularity |
| tuple elements | yes — positional fields are statically named |
| record fields | [yes, at field granularity](#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2) |
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

Record fields may be moved independently, at field granularity like struct fields; a
moved field's siblings remain individually accessible, but using the record value as a
whole afterward is rejected as a use of a partially moved value. Moving a field does not
change the record's static type — there is no narrower record type for the residual
value, only per-field move tracking.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [71_record_field_moved_independently.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/71_record_field_moved_independently.mtl), [72_record_used_as_whole_after_field_move.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/move_check/72_record_used_as_whole_after_field_move.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

### Narrowing

> **Planned for v0.13.0 (RFC-0137).** Every `struct` is represented, for type-checking
> purposes, as a fixed nominal identity (its **brand**, minted once at declaration) paired
> with its current **row** — the set of fields still present. Nothing below is built yet;
> see the exemption note on each rule.

Moving a field out of a struct narrows the value's *type* to a row with that field
removed, at the same brand — not just a change in what the compiler internally tracks
about it:

```metel
struct Handle { fd: i64, name: String }

fun main() {
    let h = Handle { fd = 3, name = "x" };
    let n = h.name;   // h : Handle.{ fd } from this point on
}
```

The residual is an ordinary value: it can be bound, passed, returned, dropped, and
narrowed again. For a struct over *N* fields, the space of residual shapes is the subset
lattice, bounded by 2^*N* — there is no row variable and no unification involved in
computing it. A struct's own field projection (`h.{ fd }`) produces exactly the same
residual type as the equivalent partial move, performed explicitly on a copy of the
reference rather than as a side effect of consuming the original.

**A residual's row is never visible to structural matching, regardless of its width.**
This is unchanged from today's rule that only a `record` (not a `struct`) satisfies a
[row bound](types.md#spec.types.generics.row-bounds.legality-4) — narrowing changes a
struct's row, never its brand, and eligibility for structural matching is scoped to the
brand alone, fixed at declaration. A struct value narrowed down to every one of its own
fields is still, unambiguously, that struct — not a same-shaped anonymous record, and not
a `record`-declared type of the same shape.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.narrowing.legality-1}

Moving a field out of a struct value narrows that value's type to a row with the moved
field removed, at the same brand.


<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="RFC-0137's row-bounded representation is not implemented -- a partial move today changes only compiler-internal move-tracking state, never the value's static type. Verified directly: `let h = Handle {...}; let n = h.name;` leaves `h`'s inferred type unchanged." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: RFC-0137's row-bounded representation is not implemented -- a partial move today changes only compiler-internal move-tracking state, never the value's static type. Verified directly: `let h = Handle {...}; let n = h.name;` leaves `h`'s inferred type unchanged._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-2}

A residual's row is never visible to structural matching; only its brand, fixed at
declaration, determines eligibility, regardless of how narrow or wide the current row is.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on the residual-type representation above existing at all; not implemented." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on the residual-type representation above existing at all; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.narrowing.dynamics-1}

A struct's own field projection expression produces exactly the same residual type as the
equivalent partial move.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on the residual-type representation above existing at all; not implemented." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on the residual-type representation above existing at all; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

### Passing a residual to a function

> **Planned for v0.13.0 (RFC-0137).**

A parameter naming a struct's own projected type (`Handle.{ fd }`, or `Self.{ fd }`
inside `Handle`'s own `extend` block) is ordinary type-matching, available to every
struct regardless of whether it opts into any structural-matching mechanism:

```metel
struct Handle { fd: i64, name: String }

extend Handle {
    fun describe(h: Self.{ fd }) -> i64 { h.fd }
}

fun main() {
    let handle = Handle { fd = 3, name = "x" };
    Handle::describe(handle.{ fd });
}
```

A caller must match the parameter's row exactly — there is no implicit truncation at the
call boundary. Passing `Handle.{ fd, name }` where `Handle.{ fd }` is expected requires
the caller to narrow itself first; the call never silently discards `name`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.passing-a-residual-to-a-function.legality-1}

A function parameter may name a struct's own projected type; a caller's argument must
match that row exactly, with no implicit narrowing at the call site.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on residual types existing at all; not implemented." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on residual types existing at all; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

### Drop dispatch against a narrowed residual

> **Planned for v0.13.0 (RFC-0137).** Supersedes the `Drop`-type partial-move ban above
> *in design*; until implemented, that ban is enforced exactly as stated.

A struct implementing `Drop` whose destructor reads a field that has since been narrowed
away must not silently skip the destructor's work. Dispatch is **row-bounded**: for a
given `Drop` impl, the compiler computes once, at compile time, the fixed set of fields
the destructor's body reads — directly, or transitively through `self`-methods it calls.
The destructor fires against any residual of the correct brand whose current row is a
superset of that fixed set, regardless of what else has already been moved out.

Coercing a value of a `Drop`-implementing type to `dyn Aspect` is one more checkpoint for
the same required set — the row information the check depends on is discarded once the
value is erased behind a fat pointer, so the check must run before that erasure, not
after.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1}

A `Drop` impl's required field set is the union of the fields its destructor body reads
directly and, recursively, the required sets of every `self`-method it calls.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Row-bounded Drop dispatch is not implemented; RFC-0071's unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Row-bounded Drop dispatch is not implemented; RFC-0071's unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1}

A `Drop` impl's destructor fires against any residual of the correct brand whose current
row is a superset of the impl's required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on the legality rule above; not implemented." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on the legality rule above; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-2}

Coercing a value of a `Drop`-implementing type to `dyn Aspect` is rejected when the
value's current row does not satisfy that type's `Drop` impl's required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on both row-bounded Drop dispatch and dyn Aspect (RFC-0008, 2-accepted, not integrated) existing; neither is implemented." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on both row-bounded Drop dispatch and dyn Aspect (RFC-0008, 2-accepted, not integrated) existing; neither is implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

### Widening

Reassigning a moved-out field already restores the containing value's whole-value status
today, for every struct regardless of `Drop` — this is existing, unconditional
`--move-check` behavior, not itself part of RFC-0137.

> **Planned for v0.13.0 (RFC-0137): once narrowing gives the residual a named type
> (above), reassigning a moved-out field also widens that type back automatically** —
> `Handle.{ fd }` becomes `Handle` again once `name` is reassigned. This is not a new
> capability requiring any other RFC first: it is the residual-type formalization
> naming what reassignment's existing whole-value-restoring behavior already produces.
> Widening does not check the reassembled value against any constructor invariant — an
> invariant a struct's constructor enforces can be bypassed through ordinary field
> reassignment today, independent of narrowing or widening; RFC-0114 (Constructor
> Aspect and Canonical Construction, still `0-draft`) is the proposed fix for that,
> unrelated to whether this section is implemented.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.ownership.widening.dynamics-1}

Assigning a value to a field missing from a residual's current row widens the residual's
type to include that field, at the same brand.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#836" reason="Depends on residual types existing at all; not implemented." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#836: Depends on residual types existing at all; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

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
