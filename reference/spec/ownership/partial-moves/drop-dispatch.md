---
sidebar_position: 9
---

# Drop dispatch against a narrowed residual

> **Gap** GAP-OWNERSHIP-003

The ban of [Ownership classes legality-6](../classes.md#spec.ownership.ownership-classes.legality-6) governs types whose `drop` receiver is the whole row. The row-bounded permission below covers a type whose receiver names a narrower row, and is not superseded by it.

[A struct implementing `Drop` whose destructor needs a field that has since been narrowed
away must not silently skip the destructor's work](#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1). Dispatch is **row-bounded**: a `Drop`
impl's required field set is the residual row its `drop` method's receiver is declared
with — the fields named in a projected receiver (`fun drop(&var self: Self.{ .fd })`) or
in its `where` clause (`fun drop<record R>(&var self: Self.R) where R: { fd, .. }`).

A `drop`
method whose receiver is the bare `&var self` requires the struct's whole row, and no
partial move of such a type is permitted. The destructor fires against any residual of
the correct brand whose current row is a superset of that declared set, regardless of
what else has already been moved out.

[The destructor body is checked against its declared
receiver row: it may name only fields in that row, and may call only `self`-methods whose
own declared receiver row that row satisfies](#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-4).

Coercing a value of a `Drop`-implementing type to `dyn Aspect` is one more checkpoint for
the same required set — the row information the check depends on is discarded once the
value is erased behind a fat pointer, so the check must run before that erasure, not
after.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1}

A `Drop` impl's required field set is the residual row its `drop` method's receiver is
declared with; a `drop` method with a bare `&var self` receiver requires the struct's
whole declared row.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented; the unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented; the unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1}

A `Drop` impl's destructor fires against any residual of the correct brand whose current
row is a superset of the impl's required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Depends on the legality rule above; not implemented." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Depends on the legality rule above; not implemented._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-2}

Coercing a value of a `Drop`-implementing type to `dyn Aspect` is rejected when the
value's current row does not satisfy that type's `Drop` impl's required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Depends on row-bounded Drop dispatch (above). `dyn Aspect` itself is fully implemented -- syntax, object safety, and coercion of a value to one -- so the erasure side of this checkpoint is real; what is still missing is the narrowed residual to run it against." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Depends on row-bounded Drop dispatch (above). `dyn Aspect` itself is fully implemented -- syntax, object safety, and coercion of a value to one -- so the erasure side of this checkpoint is real; what is still missing is the narrowed residual to run it against._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-3}

A `Drop` impl's `drop` method may declare its `&var self` receiver as a residual type of
`Self` — a field projection (`&var self: Self.{ .a, .b }`) or a row parameter constrained
by an open lower bound (`fun drop<record R>(&var self: Self.R) where R: { a, b, .. }`). The
fields named by that declaration are the impl's required field set (legality-1). A bare
`&var self` names every field.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented; the narrowed drop-receiver forms additionally depend on their own not-yet-integrated syntax (named views for the fixed projection form, a row parameter for the other). Until then a drop receiver is always the whole value and the required set is always the whole row." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented; the narrowed drop-receiver forms additionally depend on their own not-yet-integrated syntax (named views for the fixed projection form, a row parameter for the other). Until then a drop receiver is always the whole value and the required set is always the whole row._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-4}

Within a `Drop` impl whose `drop` receiver is declared narrowed (legality-3), the
destructor body may read or write only fields in that declared row, and may call a
`self`-method only when that method's own declared receiver row is satisfied by the
`drop` receiver's declared row. Each is a local check at the access or call site; no
whole-body or call-graph analysis derives the required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented; with no narrowed drop-receiver form yet, there is no declared row for a body to be checked against. The inert-destructor gate additionally rejects any non-empty drop body until destructor invocation lands." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented; with no narrowed drop-receiver form yet, there is no declared row for a body to be checked against. The inert-destructor gate additionally rejects any non-empty drop body until destructor invocation lands._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>
