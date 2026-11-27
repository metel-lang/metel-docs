---
sidebar_position: 2
---

# Ownership classes

> **Pending** metel-core#1831 the ownership classes beyond `Copy` and the affine default are accepted by the language but not yet by the checker.

> **Settled in design, inert until the `linear` release.** The computed class of generic instances, unconditional `linear`, conditional `copy` and `T: Discard` on a type parameter ([legality-7](#spec.ownership.ownership-classes.legality-7)), the Discard-based partial-move rule ([legality-6](#spec.ownership.ownership-classes.legality-6)) and consuming patterns ([partial-moves.legality-4](partial-moves/index.md#spec.ownership.partial-moves.legality-4)) are decided; every type is `Discard` before it.

Every type has one of four ownership classes, ordered by how much a value of the type may do:

| Class | At most / exactly | May be dropped | May be copied |
|---|---|---|---|
| erased | not a runtime value | not applicable | not applicable |
| linear | exactly once | no | no |
| affine (the default) | at most once | yes | no |
| copy | any number | yes | yes |

A named type with no type parameters has a declared class, and the compiler checks it against the fields (a generic instantiation computes its class from its components, as do tuples, arrays and anonymous records; a field that mentions no type parameter and is linear forces `linear` on a generic type too): the declared class must be at
least as restrictive as every field.

[A `copy` type needs every field `Copy`](copy.md#spec.ownership.copy.legality-1); a type with no keyword is affine and may hold no
linear field; a `linear` type may hold anything. A mismatch is an error at the field, and the fix-it adds the missing keyword.

[`Drop` is compatible with
the affine class only](drop.md#spec.ownership.copy-and-drop-are-mutually-exclusive.legality-1): not with copy, because a representation copy cannot run per-owner cleanup, and not with
linear, because a linear value is never implicitly discarded.

The class keywords `copy` and `linear` before `struct` and `enum` state the class in one word; affine is the default and has
no keyword. A closure that captures a linear value is declared `linear` as well. `linear` is reserved: the keyword and the
`Linear` aspect cannot be used.

**Dropping in generic code.** A generic body can drop a value of a type-parameter type without writing a call:
at scope end, on an early `return` or `?`, by overwriting a binding, by leaving an argument unused, or by discarding
an expression statement. Dropping is permitted when the type is [`Discard`](#spec.ownership.ownership-classes.legality-1).
`Discard` holds for every type that is not linear, and its implementations are never written by a user.

A bare type parameter is
[possibly linear](#spec.ownership.ownership-classes.legality-2): a generic body may move it, return it and pass it,
but may not drop or copy it unless its bounds say so. Nothing is inferred: a function that
[drops such a value](#spec.ownership.ownership-classes.legality-3) writes `T: Discard`, as copying writes `T: Copy`, and the
diagnostic suggests the bound. A generic type's parameters [admit linear arguments by default](#spec.ownership.ownership-classes.legality-7);
`T: Discard` on a type parameter forbids them.

Until `linear` is implemented every type is `Discard`, so a bare type
parameter behaves as affine and no program changes.

<!-- doc-example: skip reason="accepted design, not yet implemented" -->
```metel
fun identity<T>(x: T) -> T { x }       // x is moved into the result: no bound needed
fun sink<T: Discard>(x: T) { }         // drops x: the bound is written
fun api<T: Discard>(x: T) { sink(x) }  // forwarding to sink needs the bound too, by the ordinary rule
```

`Clone` is explicit creation of another value and is not the duplication that the linear class forbids: a linear
type may have a written `Clone`, and a derived `Clone` requires every field to satisfy `Clone`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.ownership-classes.legality-1}

`Discard` is computed by the compiler. For a concrete type it holds exactly when the type is not linear, and `T: Copy` entails `T: Discard`. Writing or negating a `Discard` impl is an error.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1831" reason="Discard and Linear are not yet implemented" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1831: Discard and Linear are not yet implemented_</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.ownership-classes.legality-2}

In a generic body, a value whose type is a bare type parameter may not be dropped or copied unless a bound of the function entails `Discard` or `Copy` for it.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1831" reason="Every type is Discard until linear is implemented" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1831: Every type is Discard until linear is implemented_</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.ownership-classes.legality-3}

An implicit or explicit drop of a value whose `Discard` depends on a type parameter requires a bound of the function that entails `Discard`, and so does a call to a function whose own bound requires it. A missing bound is an error at that site whose diagnostic suggests it. For a method of a generic impl the bound attaches to the method.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1827" reason="Drop sites are not yet recorded and every type is Discard" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1827: Drop sites are not yet recorded and every type is Discard_</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.ownership-classes.legality-5}

A linear type may have a written `Clone`. A derived `Clone` requires every field to satisfy `Clone`, including linear fields.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1831" reason="Linear types are reserved" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1831: Linear types are reserved_</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.ownership-classes.legality-6}

A partial move out of a nominal aggregate is legal only when the aggregate is known `Discard` in the current context. Otherwise it is consumed only by total destructuring or by passing it to a function that consumes it. A field of such a value cannot be moved out on its own, a destructuring pattern consumes its scrutinee, so a field skipped with `..` or `_` must be `Discard`, and assigning to a linear field is an error. Reading a `Copy` field and borrowing a field are allowed. A type with a `Drop` impl is dismantled only by a marked dismantling method (an inherent method in its defining module whose receiver is an owned `self` carrying the dismantling marker), by total destructuring that suppresses only the outer destructor, and is otherwise never destructured, partially moved or used in a record spread, even in its own module. An anonymous record or tuple that holds a linear value is not nominal, and narrows when a field moves out.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1831" reason="Linear types are reserved" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1831: Linear types are reserved_</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.ownership-classes.legality-7}

A generic type's class is computed per instantiation from its owned fields. `linear` on a generic type is unconditional, and a field whose type mentions no type parameter and is linear forces `linear` on the declaration. A type parameter written `T: Discard` forbids linear arguments, and naming such a type requires the bound. A `Drop` impl must prove its target `Discard` under the impl's bounds: an unconditional `Drop` impl on a possibly-linear target is an error, and a conditional impl adds no bound to the type.

<!-- rfc.py:last_reviewed 5a5736ded3411d96420faf80578d72a85cfda2e3 -->

<!-- rfc.py:exemption kind="blocked" ref="metel-core#1831" reason="Linear types are reserved" -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#1831: Linear types are reserved_</span>
<!-- rfc.py:exemption:rendered:end -->

</details>
