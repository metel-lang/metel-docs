---
sidebar_position: 15
---

# Structural Aspect Bounds

Arrays (`[T]`), tuples (`(A, B)`, …), and function types (`|A| -> B`) are
**structural types** — built into the language rather than declared by a user, with no
name that can serve as an impl target the ordinary way. For the orphan rule (above),
structural type constructors are treated as belonging to `std::core`: a user module
may write `extend [T]: Aspect` only when `Aspect` itself is local to that module.

**Blanket impls for structural constructors.** `std::core` declares aspect impls for
structural constructors using the conditional `extend` syntax (above):

```metel
// std::core
extend<T: Display> [T]: Display {
    fun to_string(self: &[T]) -> String { ... }
}
```

This is what makes `println([1, 2, 3])` compile: `[1, 2, 3]` has type `[i64; 3]`;
`i64: Display`; [the conditional extend block applies](#spec.declarations.structural-aspect-bounds.legality-2). Coherence for structural impl
targets follows the same rules as any other conditional block (above) — two impls of
the same aspect for `[T]` conflict (`T0015`) unless one directly negates a bound the
other requires.

Structural aspect lookup is coercion-aware: when the expression's intrinsic type does
not match a structural target directly, lookup may consider a finite path of legal
implicit coercions, retain the selected path, and insert it at the use site. This does
not merge the source and target types for identity or coherence, and coercion remains
directional (`[T; N]` to `[T]`, never the reverse).

**Without a matching impl**, a structural type fails an aspect bound with a diagnostic naming the constructor:

```
T0012: [i64] does not implement Display
       hint: arrays implement Display only when their element type does;
             no extend<T: Display> [T]: Display is registered
```

**Standard array impls.** `std::core` provides `Display`, `Clone`, and `Eq` for
arrays, each conditional on the element type satisfying the same bound (element-wise
`to_string`/join, element-wise clone into new backing storage, and element-wise
equality respectively). These cannot be overridden by user code (orphan rule).
`List<T>` is a separate nominal struct; its impls coexist independently of the array
impls.

> **Gap** GAP-DECLARATIONS-003

Once `[T]` owns nothing, an element-wise clone into new backing storage is impossible:
`Clone::clone(&self) -> Self` must produce a `[T]`, which can borrow only from storage that
already exists and outlives it, not from a buffer the implementation just allocated.
`Display` and `Eq` are unaffected because they return `String` and `boolean`, not `Self`.

A tuple is a row ([Tuples](../../types/tuples.md#spec.types.tuples.legality-4)), so it satisfies an aspect bound through the row impls of `Display`, `Clone` and `Copy`: `(i64, i64)` is all three, `(i64, String)` is `Display` and `Clone` but not `Copy`, and a bound it does not meet is a `T0012` error. A tuple has no `Eq`, `Ord` or `Hash` until operators dispatch through aspects.

**Function types.** A plain function and a closure share one type, `|A| -> B` (see [Functions — First-Class Functions](../../functions/first-class-functions.md)) — [there is no separate `fun(A) -> B` function-pointer type or syntax](#spec.declarations.structural-aspect-bounds.legality-7); `fun(A) -> B` is a parse error. There is [no `Callable<A, B>` aspect to bound a function type by](#spec.declarations.structural-aspect-bounds.legality-8).

A closure value keeps its own copyability until it flows into a slot with a written function type, where it becomes move-only ([First-Class Functions](../../functions/first-class-functions.md)), and [there is no working `Clone`](#spec.declarations.structural-aspect-bounds.legality-9): `.clone()` on a `|A| -> B` receiver fails to typecheck (`T0003`, no method on a function type: it implements no aspect) regardless of annotation.

[`Display`, `Eq`, `Ord`, `Hash`, `Send`, `Sync`, and `Drop` do not apply to function types either — there is no canonical string form, function equality is undecidable in general, and there is no state to drop.](#spec.declarations.structural-aspect-bounds.legality-10)

> **Gap** GAP-FUNCTIONS-002

**Array auto-impl propagation.** `[T]: Send`, `[T]: Sync`, and `[T]: Drop` are not
provided in this language version.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-1}

Structural type constructors are owned by `std::core` for orphan-rule purposes; outside
`std::core`, an implementation for one is legal only when the aspect is local.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6Im9ycGhhbiBpbXBsZW1lbnRhdGlvbiIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ18yM19zdHJ1Y3R1cmFsX2JsYW5rZXRfaW1wbF9vcnBoYW5fdmlvbGF0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUltvcnBoYW4gaW1wbGVtZW50YXRpb25dXG4vLyBSRkMtMDA2MTogc3RydWN0dXJhbCB0eXBlIGNvbnN0cnVjdG9ycyAoW1RdLCB0dXBsZXMsIGZ1biB0eXBlcykgYXJlIG93bmVkIGJ5XG4vLyBzdGQ6OmNvcmUgZm9yIG9ycGhhbi1ydWxlIHB1cnBvc2VzLiBBIHVzZXIgbW9kdWxlIGltcGxlbWVudGluZyBhIHN0ZDo6Y29yZVxuLy8gYXNwZWN0IChEaXNwbGF5KSBmb3IgYSBzdHJ1Y3R1cmFsIHRhcmdldCAoW1RdKSBvd25zIG5laXRoZXIgaGFsZiBvZiB0aGUgcGFpciBcdTIwMTRcbi8vIHRoaXMgbXVzdCBzdGlsbCBiZSByZWplY3RlZCBhcyBhbiBvcnBoYW4gaW1wbGVtZW50YXRpb24sIGV4YWN0bHkgYXMgZm9yIGFcbi8vIG5vbWluYWwgdGFyZ2V0LCBjb25maXJtaW5nIGlzc3VlICMyMzMncyBJbXBsQmxvY2sgZ2VuZXJhbGl6YXRpb24gZGlkbid0IGJ5cGFzc1xuLy8gdGhlIGV4aXN0aW5nIGNvaGVyZW5jZSBwYXNzIChpc3N1ZSAjMjM4KSBmb3IgdGhlIG5ldyBzdHJ1Y3R1cmFsLXRhcmdldCBzaGFwZS5cblxuZXh0ZW5kPFQ6IERpc3BsYXk+IFtUXTogRGlzcGxheSB7XG4gICAgZnVuIHRvX3N0cmluZygmc2VsZikgLT4gU3RyaW5nIHtcbiAgICAgICAgcmV0dXJuIFwiYXJyYXlcIjtcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvbmVnXzIzX3N0cnVjdHVyYWxfYmxhbmtldF9pbXBsX29ycGhhbl92aW9sYXRpb24ubXRsIiwibmFtZSI6Im5lZ18yM19zdHJ1Y3R1cmFsX2JsYW5rZXRfaW1wbF9vcnBoYW5fdmlvbGF0aW9uLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjEgXHUwMGE3MjogXCJDb2hlcmVuY2UgcnVsZXMgZm9yIHN0cnVjdHVyYWwgaW1wbCB0YXJnZXRzIGZvbGxvdyBSRkMtMDA2MFxuLy8gXHUwMGE3MiBhbmQgUkZDLTAwMzYgXHUwMGE3My4xIHdpdGhvdXQgc3BlY2lhbCBjYXNlcy5cIiBUaGlzIGlzIHRoZSBzdHJ1Y3R1cmFsLXRhcmdldFxuLy8gY291bnRlcnBhcnQgb2YgY29uZGl0aW9uYWxfaW1wbF9uZWdhdGlvbl9kaXNqb2ludF9hY2NlcHRlZCAod2hpY2ggdGFyZ2V0cyBhXG4vLyBub21pbmFsIHN0cnVjdCk6IGBpbXBsPFQ6IENvcHkzPiAuLi5gIGFuZCBgaW1wbDxUOiAhQ29weTM+IC4uLmAgZm9yIHRoZVxuLy8gc2FtZSBsb2NhbGx5LWRlY2xhcmVkIGFzcGVjdCBvbiB0aGUgKnNhbWUgc3RydWN0dXJhbCB0YXJnZXQqIChgW1RdYCkgYXJlXG4vLyBwcm92YWJseSBkaXNqb2ludCB2aWEgc3ludGFjdGljIG5lZ2F0aW9uIGFuZCBtdXN0IG5vdCBiZSByZXBvcnRlZCBhcyBhXG4vLyBjb2hlcmVuY2UgY29uZmxpY3QuIGBTZXJpYWxpemUzYCBpcyBkZWNsYXJlZCBsb2NhbGx5LCBzbyB0aGUgb3JwaGFuIHJ1bGVcbi8vIHBlcm1pdHMgYSB1c2VyIG1vZHVsZSB0byBpbXBsZW1lbnQgaXQgZm9yIGBbVF1gIGF0IGFsbCAoUkZDLTAwNjEgXHUwMGE3MSkuXG5cbmFzcGVjdCBDb3B5MyB7XG4gICAgZnVuIGR1cChzZWxmKSAtPiBpNjQ7XG59XG5cbmFzcGVjdCBTZXJpYWxpemUzIHtcbiAgICBmdW4gc2VyKHNlbGYpIC0+IFN0cmluZztcbn1cblxuZXh0ZW5kPFQ6IENvcHkzPiBbVF06IFNlcmlhbGl6ZTMge1xuICAgIGZ1biBzZXIoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwiY29weWFibGVcIjsgfVxufVxuXG5leHRlbmQ8VDogIUNvcHkzPiBbVF06IFNlcmlhbGl6ZTMge1xuICAgIGZ1biBzZXIoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwibm90LWNvcHlhYmxlXCI7IH1cbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9jb25kaXRpb25hbF9pbXBsX25lZ2F0aW9uX2Rpc2pvaW50X2FjY2VwdGVkX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCIsIm5hbWUiOiJjb25kaXRpb25hbF9pbXBsX25lZ2F0aW9uX2Rpc2pvaW50X2FjY2VwdGVkX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-2}

`std::core` may declare conditional implementations for structural constructors; a
generic structural target is registered and dispatched subject to its stated bounds.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md), [rfc-0177](../../../../rfcs/4-implemented/rfc-0177-coercion-aware-structural-aspect-lookup.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (7)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc5X25lc3RlZF9hcnJheV9kaXNwbGF5X3N0cnVjdHVyYWxfaW1wbC5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogYFtUXTogRGlzcGxheWAgaXMgaXRzZWxmIGNvbmRpdGlvbmFsIG9uIGBUOiBEaXNwbGF5YCAoUkZDLTAwNjFcbi8vIFx1MDBhNzIvXHUwMGE3NCksIHNvIGl0IG11c3QgYXBwbHkgcmVjdXJzaXZlbHkgd2hlbiBgVGAgaXMgaXRzZWxmIGFuIGFycmF5IC0tIGFuXG4vLyBhcnJheS1vZi1hcnJheXMgaXMgRGlzcGxheSBhcyBsb25nIGFzIHRoZSBpbm5lcm1vc3QgZWxlbWVudCB0eXBlIGlzLlxuLy8gRXhlcmNpc2VzIGB0eXBlX3NhdGlzZmllc19hc3BlY3RgJ3MgYFR5cGU6OkFycmF5YCBhcm0gcmVjdXJzaW5nIHRocm91Z2hcbi8vIGBjaGVja19jb25kaXRpb25hbF9lbnRyeWAgb24gYSBuZXN0ZWQgYFR5cGU6OkFycmF5YCBhcmd1bWVudCByYXRoZXIgdGhhbiBhXG4vLyBgTmFtZWRgL3ByaW1pdGl2ZSBvbmUuXG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBncmlkOiBbW2k2NF07IDJdIDo9IFtbMSwgMl0sIFszLCA0XV07XG4gICAgYXNzZXJ0KGdyaWQudG9fc3RyaW5nKCkgPT0gXCJbWzEsIDJdLCBbMywgNF1dXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYXNwZWN0cy83OV9uZXN0ZWRfYXJyYXlfZGlzcGxheV9zdHJ1Y3R1cmFsX2ltcGwubXRsIiwibmFtZSI6Ijc5X25lc3RlZF9hcnJheV9kaXNwbGF5X3N0cnVjdHVyYWxfaW1wbC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlMTlfMDhfZXh0ZW5kX2dlbmVyaWNfc3RydWN0dXJhbF90YXJnZXRzX3dvcmsubXRsIiwic291cmNlIjoiYXNwZWN0IEFyZWEge1xuICAgIGZ1biBhcmVhKCZzZWxmKSAtPiBpNjQ7XG59XG5cbi8vIFRoZSBnZW5lcmljIGZvcm0gaXMgd2hhdCBSRkMtMDA2MSBpbXBsZW1lbnRzLCBhbmQgaXQgZGlzcGF0Y2hlcy5cbmV4dGVuZDxUPiBbVF06IEFyZWEge1xuICAgIGZ1biBhcmVhKCZzZWxmKSAtPiBpNjQgeyByZXR1cm4gNzsgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYTogW2k2NF0gOj0gWzEsIDJdO1xuICAgIGFzc2VydChhLmFyZWEoKSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2FzcGVjdHMvc3RhZ2UxOV8wOF9leHRlbmRfZ2VuZXJpY19zdHJ1Y3R1cmFsX3RhcmdldHNfd29yay5tdGwiLCJuYW1lIjoic3RhZ2UxOV8wOF9leHRlbmRfZ2VuZXJpY19zdHJ1Y3R1cmFsX3RhcmdldHNfd29yay5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjE2Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOV9uZWdfMDNfc3RydWN0dXJhbF9hcnJheV9lbGVtZW50X2JvdW5kX3JlcXVpcmVkLm10bCIsInNvdXJjZSI6Ii8vIE5lZ2F0aXZlOiBhbiBhcnJheSdzIGNvbmRpdGlvbmFsIGltcGwgaXMgZ2F0ZWQgb24gdGhlIGVsZW1lbnQgdHlwZSwgbm90XG4vLyBncmFudGVkIHVuY29uZGl0aW9uYWxseSB0byBldmVyeSBhcnJheS4gYFtPcGFxdWVdYCBkb2VzIG5vdCBpbXBsZW1lbnRcbi8vIGBEaXNwbGF5YCBiZWNhdXNlIGBPcGFxdWVgIGl0c2VsZiBkb2VzIG5vdCAoUkZDLTAwNjEgXHUwMGE3Mi0zKSAtLSB0aGlzIGlzIHRoZVxuLy8gYXJyYXkgY291bnRlcnBhcnQgdG8gc3RhZ2UxOV9uZWdfMDEgKHR1cGxlKSBhbmQgc3RhZ2UxOV9uZWdfMDIgKGZ1bmN0aW9uKS5cblxuc3RydWN0IE9wYXF1ZSB7XG4gICAgdmFsdWU6IGk2NCxcbn1cblxuZnVuIHNob3c8VDogRGlzcGxheT4oeDogVCkgLT4gU3RyaW5nIHtcbiAgICByZXR1cm4geC50b19zdHJpbmcoKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGl0ZW1zIDo9IFtPcGFxdWUgeyB2YWx1ZSA9IDEgfSwgT3BhcXVlIHsgdmFsdWUgPSAyIH1dO1xuICAgIGxldCBfIDo9IHNob3coaXRlbXMpOyAvLyBFUlJPUltUMDAxMl1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3N0YWdlMTlfbmVnXzAzX3N0cnVjdHVyYWxfYXJyYXlfZWxlbWVudF9ib3VuZF9yZXF1aXJlZC5tdGwiLCJuYW1lIjoic3RhZ2UxOV9uZWdfMDNfc3RydWN0dXJhbF9hcnJheV9lbGVtZW50X2JvdW5kX3JlcXVpcmVkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNvdWxkIG5ldmVyIGJlIGZvdW5kIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOV9uZWdfMDdfZXh0ZW5kX2NvbmNyZXRlX2FycmF5X3RhcmdldC5tdGwiLCJzb3VyY2UiOiJhc3BlY3QgQXJlYSB7XG4gICAgZnVuIGFyZWEoJnNlbGYpIC0+IGk2NDtcbn1cblxuLy8gUkZDLTAwNjEgZ3JhbnRzIHN0cnVjdHVyYWwgaW1wbCB0YXJnZXRzLCBidXQgb25seSB0aGUgZ2VuZXJpYyBmb3JtIGlzXG4vLyByZWdpc3RlcmVkLiBBIGNvbmNyZXRlIG9uZSBoYXMgbm93aGVyZSB0byBrZXkgb24sIHNvIGl0cyBtZXRob2RzIGNvdWxkIG5ldmVyXG4vLyBiZSBmb3VuZCBcdTIwMTQgcmVqZWN0ZWQgcmF0aGVyIHRoYW4gYWNjZXB0ZWQtYW5kLXVucmVhY2hhYmxlIChtZXRlbC1jb3JlIzU4MSkuXG5leHRlbmQgW2k2NF06IEFyZWEge1xuICAgIGZ1biBhcmVhKCZzZWxmKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxufVxuXG5mdW4gbWFpbigpIHtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2FzcGVjdHMvc3RhZ2UxOV9uZWdfMDdfZXh0ZW5kX2NvbmNyZXRlX2FycmF5X3RhcmdldC5tdGwiLCJuYW1lIjoic3RhZ2UxOV9uZWdfMDdfZXh0ZW5kX2NvbmNyZXRlX2FycmF5X3RhcmdldC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNvdWxkIG5ldmVyIGJlIGZvdW5kIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOV9uZWdfMDdfZXh0ZW5kX2NvbmNyZXRlX2Z1bl90YXJnZXQubXRsIiwic291cmNlIjoiYXNwZWN0IEFyZWEge1xuICAgIGZ1biBhcmVhKCZzZWxmKSAtPiBpNjQ7XG59XG5cbi8vIFJGQy0wMDYxIGdyYW50cyBzdHJ1Y3R1cmFsIGltcGwgdGFyZ2V0cywgYnV0IG9ubHkgdGhlIGdlbmVyaWMgYXJyYXkgZm9ybSBpc1xuLy8gcmVnaXN0ZXJlZC4gQSBjb25jcmV0ZSBvbmUgaGFzIG5vd2hlcmUgdG8ga2V5IG9uLCBzbyBpdHMgbWV0aG9kcyBjb3VsZCBuZXZlclxuLy8gYmUgZm91bmQgXHUyMDE0IHJlamVjdGVkIHJhdGhlciB0aGFuIGFjY2VwdGVkLWFuZC11bnJlYWNoYWJsZSAobWV0ZWwtY29yZSM1ODEpLlxuZXh0ZW5kIHxpNjR8IC0+IGk2NDogQXJlYSB7XG4gICAgZnVuIGFyZWEoJnNlbGYpIC0+IGk2NCB7IHJldHVybiAxOyB9XG59XG5cbmZ1biBtYWluKCkge1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9zdGFnZTE5X25lZ18wN19leHRlbmRfY29uY3JldGVfZnVuX3RhcmdldC5tdGwiLCJuYW1lIjoic3RhZ2UxOV9uZWdfMDdfZXh0ZW5kX2NvbmNyZXRlX2Z1bl90YXJnZXQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjEgXHUwMGE3MjogXCJDb2hlcmVuY2UgcnVsZXMgZm9yIHN0cnVjdHVyYWwgaW1wbCB0YXJnZXRzIGZvbGxvdyBSRkMtMDA2MFxuLy8gXHUwMGE3MiBhbmQgUkZDLTAwMzYgXHUwMGE3My4xIHdpdGhvdXQgc3BlY2lhbCBjYXNlcy5cIiBUaGlzIGlzIHRoZSBzdHJ1Y3R1cmFsLXRhcmdldFxuLy8gY291bnRlcnBhcnQgb2YgY29uZGl0aW9uYWxfaW1wbF9uZWdhdGlvbl9kaXNqb2ludF9hY2NlcHRlZCAod2hpY2ggdGFyZ2V0cyBhXG4vLyBub21pbmFsIHN0cnVjdCk6IGBpbXBsPFQ6IENvcHkzPiAuLi5gIGFuZCBgaW1wbDxUOiAhQ29weTM+IC4uLmAgZm9yIHRoZVxuLy8gc2FtZSBsb2NhbGx5LWRlY2xhcmVkIGFzcGVjdCBvbiB0aGUgKnNhbWUgc3RydWN0dXJhbCB0YXJnZXQqIChgW1RdYCkgYXJlXG4vLyBwcm92YWJseSBkaXNqb2ludCB2aWEgc3ludGFjdGljIG5lZ2F0aW9uIGFuZCBtdXN0IG5vdCBiZSByZXBvcnRlZCBhcyBhXG4vLyBjb2hlcmVuY2UgY29uZmxpY3QuIGBTZXJpYWxpemUzYCBpcyBkZWNsYXJlZCBsb2NhbGx5LCBzbyB0aGUgb3JwaGFuIHJ1bGVcbi8vIHBlcm1pdHMgYSB1c2VyIG1vZHVsZSB0byBpbXBsZW1lbnQgaXQgZm9yIGBbVF1gIGF0IGFsbCAoUkZDLTAwNjEgXHUwMGE3MSkuXG5cbmFzcGVjdCBDb3B5MyB7XG4gICAgZnVuIGR1cChzZWxmKSAtPiBpNjQ7XG59XG5cbmFzcGVjdCBTZXJpYWxpemUzIHtcbiAgICBmdW4gc2VyKHNlbGYpIC0+IFN0cmluZztcbn1cblxuZXh0ZW5kPFQ6IENvcHkzPiBbVF06IFNlcmlhbGl6ZTMge1xuICAgIGZ1biBzZXIoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwiY29weWFibGVcIjsgfVxufVxuXG5leHRlbmQ8VDogIUNvcHkzPiBbVF06IFNlcmlhbGl6ZTMge1xuICAgIGZ1biBzZXIoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwibm90LWNvcHlhYmxlXCI7IH1cbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9jb25kaXRpb25hbF9pbXBsX25lZ2F0aW9uX2Rpc2pvaW50X2FjY2VwdGVkX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCIsIm5hbWUiOiJjb25kaXRpb25hbF9pbXBsX25lZ2F0aW9uX2Rpc2pvaW50X2FjY2VwdGVkX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIyIiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA4MSArIFJGQy0wMDYxOiBhIGJsYW5rZXQgbmVnYXRpdmUgaW1wbCBvbiBhIHN0cnVjdHVyYWwgdGFyZ2V0IChgW1RdYClcbi8vIG11c3Qgb3ZlcnJpZGUgYSBibGFua2V0IHBvc2l0aXZlIGltcGwgdGhlIHNhbWUgd2F5IGl0IGFscmVhZHkgZG9lcyBmb3IgYVxuLy8gbmFtZWQgZ2VuZXJpYyB0YXJnZXQgKHNlZSBnZW5lcmljX25lZ2F0aXZlX2ltcGxfYmxvY2tzX3Bvc2l0aXZlX2JvdW5kKSAtLVxuLy8gbmVnYXRpdmUtaW1wbCBwcmlvcml0eSBvdmVyIGEgYmxhbmtldCBwb3NpdGl2ZSBpcyBhIHByb3BlcnR5IG9mIHRoZVxuLy8gYXNwZWN0L3RhcmdldCBwYWlyLCBub3Qgc29tZXRoaW5nIHRoYXQgc2hvdWxkIGRlcGVuZCBvbiB3aGV0aGVyIHRoZVxuLy8gdGFyZ2V0IGhhcHBlbnMgdG8gYmUgYE5hbWVkYCBvciBzdHJ1Y3R1cmFsLlxuXG5hc3BlY3QgTWFya2VyIHtcbiAgICBmdW4gbWFyayhzZWxmKSAtPiBTdHJpbmc7XG59XG5cbmV4dGVuZDxUPiBbVF06IE1hcmtlciB7XG4gICAgZnVuIG1hcmsoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwiYmxhbmtldFwiOyB9XG59XG5cbmV4dGVuZDxUPiBbVF06ICFNYXJrZXI7XG5cbmZ1biBuZWVkc19tYXJrZXI8VTogTWFya2VyPih4OiBVKSB7fVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gWzEsIDIsIDNdO1xuICAgIG5lZWRzX21hcmtlcih4cyk7IC8vIEVSUk9SW1QwMDEyXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9nZW5lcmljX25lZ2F0aXZlX2ltcGxfYmxvY2tzX3Bvc2l0aXZlX2JvdW5kX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCIsIm5hbWUiOiJnZW5lcmljX25lZ2F0aXZlX2ltcGxfYmxvY2tzX3Bvc2l0aXZlX2JvdW5kX2Zvcl9zdHJ1Y3R1cmFsX3RhcmdldCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-3}

Without an applicable structural implementation, using a structural type where an aspect
bound is required is rejected with `T0012`.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjE2Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOV9uZWdfMDNfc3RydWN0dXJhbF9hcnJheV9lbGVtZW50X2JvdW5kX3JlcXVpcmVkLm10bCIsInNvdXJjZSI6Ii8vIE5lZ2F0aXZlOiBhbiBhcnJheSdzIGNvbmRpdGlvbmFsIGltcGwgaXMgZ2F0ZWQgb24gdGhlIGVsZW1lbnQgdHlwZSwgbm90XG4vLyBncmFudGVkIHVuY29uZGl0aW9uYWxseSB0byBldmVyeSBhcnJheS4gYFtPcGFxdWVdYCBkb2VzIG5vdCBpbXBsZW1lbnRcbi8vIGBEaXNwbGF5YCBiZWNhdXNlIGBPcGFxdWVgIGl0c2VsZiBkb2VzIG5vdCAoUkZDLTAwNjEgXHUwMGE3Mi0zKSAtLSB0aGlzIGlzIHRoZVxuLy8gYXJyYXkgY291bnRlcnBhcnQgdG8gc3RhZ2UxOV9uZWdfMDEgKHR1cGxlKSBhbmQgc3RhZ2UxOV9uZWdfMDIgKGZ1bmN0aW9uKS5cblxuc3RydWN0IE9wYXF1ZSB7XG4gICAgdmFsdWU6IGk2NCxcbn1cblxuZnVuIHNob3c8VDogRGlzcGxheT4oeDogVCkgLT4gU3RyaW5nIHtcbiAgICByZXR1cm4geC50b19zdHJpbmcoKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGl0ZW1zIDo9IFtPcGFxdWUgeyB2YWx1ZSA9IDEgfSwgT3BhcXVlIHsgdmFsdWUgPSAyIH1dO1xuICAgIGxldCBfIDo9IHNob3coaXRlbXMpOyAvLyBFUlJPUltUMDAxMl1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3N0YWdlMTlfbmVnXzAzX3N0cnVjdHVyYWxfYXJyYXlfZWxlbWVudF9ib3VuZF9yZXF1aXJlZC5tdGwiLCJuYW1lIjoic3RhZ2UxOV9uZWdfMDNfc3RydWN0dXJhbF9hcnJheV9lbGVtZW50X2JvdW5kX3JlcXVpcmVkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-4}

`std::core` provides `Display` and `Eq` for `[T]` when `T` satisfies the same aspect;
these implementations cannot be overridden by user code.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc5X25lc3RlZF9hcnJheV9kaXNwbGF5X3N0cnVjdHVyYWxfaW1wbC5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogYFtUXTogRGlzcGxheWAgaXMgaXRzZWxmIGNvbmRpdGlvbmFsIG9uIGBUOiBEaXNwbGF5YCAoUkZDLTAwNjFcbi8vIFx1MDBhNzIvXHUwMGE3NCksIHNvIGl0IG11c3QgYXBwbHkgcmVjdXJzaXZlbHkgd2hlbiBgVGAgaXMgaXRzZWxmIGFuIGFycmF5IC0tIGFuXG4vLyBhcnJheS1vZi1hcnJheXMgaXMgRGlzcGxheSBhcyBsb25nIGFzIHRoZSBpbm5lcm1vc3QgZWxlbWVudCB0eXBlIGlzLlxuLy8gRXhlcmNpc2VzIGB0eXBlX3NhdGlzZmllc19hc3BlY3RgJ3MgYFR5cGU6OkFycmF5YCBhcm0gcmVjdXJzaW5nIHRocm91Z2hcbi8vIGBjaGVja19jb25kaXRpb25hbF9lbnRyeWAgb24gYSBuZXN0ZWQgYFR5cGU6OkFycmF5YCBhcmd1bWVudCByYXRoZXIgdGhhbiBhXG4vLyBgTmFtZWRgL3ByaW1pdGl2ZSBvbmUuXG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBncmlkOiBbW2k2NF07IDJdIDo9IFtbMSwgMl0sIFszLCA0XV07XG4gICAgYXNzZXJ0KGdyaWQudG9fc3RyaW5nKCkgPT0gXCJbWzEsIDJdLCBbMywgNF1dXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYXNwZWN0cy83OV9uZXN0ZWRfYXJyYXlfZGlzcGxheV9zdHJ1Y3R1cmFsX2ltcGwubXRsIiwibmFtZSI6Ijc5X25lc3RlZF9hcnJheV9kaXNwbGF5X3N0cnVjdHVyYWxfaW1wbC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-5}

Array marker-aspect propagation is not part of structural implementation lookup.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc2X2FycmF5X2Rpc3BsYXlfc3RydWN0dXJhbF9pbXBsLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCB4cyA6PSBbMSwgMiwgM107XG4gICAgYXNzZXJ0KHhzLnRvX3N0cmluZygpID09IFwiWzEsIDIsIDNdXCIpO1xuICAgIGFzc2VydChbNCwgNV0udG9fc3RyaW5nKCkgPT0gXCJbNCwgNV1cIik7XG4gICAgYXNzZXJ0KHNob3coWzYsIDddKSA9PSBcIls2LCA3XVwiKTtcbn1cblxuZnVuIHNob3c8VDogRGlzcGxheT4odmFsdWU6IFQpIC0+IFN0cmluZyB7XG4gICAgdmFsdWUudG9fc3RyaW5nKClcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvNzZfYXJyYXlfZGlzcGxheV9zdHJ1Y3R1cmFsX2ltcGwubXRsIiwibmFtZSI6Ijc2X2FycmF5X2Rpc3BsYXlfc3RydWN0dXJhbF9pbXBsLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc3X2FycmF5X2Nsb25lX3N0cnVjdHVyYWxfaW1wbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgQm94IHtcbiAgICB2YWx1ZTogaTY0LFxufVxuXG5leHRlbmQgQm94OiBEaXNwbGF5IHtcbiAgICBmdW4gdG9fc3RyaW5nKCZzZWxmKSAtPiBTdHJpbmcge1xuICAgICAgICByZXR1cm4gc2VsZi52YWx1ZS50b19zdHJpbmcoKTtcbiAgICB9XG59XG5cbmV4dGVuZCBCb3g6IENsb25lIHtcbiAgICBmdW4gY2xvbmUoJnNlbGYpIC0+IFNlbGYge1xuICAgICAgICByZXR1cm4gQm94IHsgdmFsdWUgPSBzZWxmLnZhbHVlIH07XG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gW0JveCB7IHZhbHVlID0gMSB9LCBCb3ggeyB2YWx1ZSA9IDIgfSwgQm94IHsgdmFsdWUgPSAzIH1dO1xuICAgIGxldCB5cyA6PSB4cy5jbG9uZSgpO1xuICAgIGFzc2VydCh5cy50b19zdHJpbmcoKSA9PSBcIlsxLCAyLCAzXVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvNzdfYXJyYXlfY2xvbmVfc3RydWN0dXJhbF9pbXBsLm10bCIsIm5hbWUiOiI3N19hcnJheV9jbG9uZV9zdHJ1Y3R1cmFsX2ltcGwubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-6}

A tuple is a row, so it satisfies an aspect bound through the row impls of `Display`, `Clone` and `Copy`
and through a local aspect implementation for its tuple type; a bound it does not meet is `T0012`.

<!-- rfc.py:last_reviewed e3bcda82e7d6dd9cc14dc080a2f6923bf450aa6b -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlM18wNV90dXBsZV9hcnJheV9zdWZmaXgubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgMyByZWdyZXNzaW9uOiB0aGUgcG9zdGZpeCBgW11gIGFycmF5IHN1ZmZpeCBtdXN0IGJpbmQgdG8gdHVwbGUgdHlwZXMgaW5cbi8vIGV2ZXJ5IGFubm90YXRpb24gcG9zaXRpb24sIG5vdCBvbmx5IG5hbWVkIHR5cGVzIChNRVRFTC0xOTEpLlxuXG5zdHJ1Y3QgUGFpclRhYmxlIHtcbiAgICByb3dzOiBbKFN0cmluZywgaTY0KV0sXG59XG5cbmZ1biBrZWVwKHJvd3M6IFsoU3RyaW5nLCBpNjQpXSkgLT4gWyhTdHJpbmcsIGk2NCldIHtcbiAgICByb3dzXG59XG5cbmxldCByb3dzX2Zvcl90YWJsZTogWyhTdHJpbmcsIGk2NCldIDo9IFsoXCJhbHBoYVwiLCAxKSwgKFwiYmV0YVwiLCAyKV07XG5sZXQgdGFibGUgOj0gUGFpclRhYmxlIHsgcm93cyA9IGtlZXAocm93c19mb3JfdGFibGUpIH07XG5sZXQgbmFtZTogJlN0cmluZyA6PSAmdGFibGUucm93c1swXS4wO1xubGV0IHZhbHVlOiBpNjQgOj0gdGFibGUucm93c1swXS4xO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzXzA1X3R1cGxlX2FycmF5X3N1ZmZpeC5tdGwiLCJuYW1lIjoic3RhZ2UzXzA1X3R1cGxlX2FycmF5X3N1ZmZpeC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-7}

Function values have the ordinary function type `|A| -> B`; there is no separate
function-pointer type.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQxX2Z1bmN0aW9uX3ZhbHVlc19hcmVfY29weS5tdGwiLCJzb3VyY2UiOiJmdW4gaW5jcmVtZW50KHZhbHVlOiBpNjQpIC0+IGk2NCB7IHZhbHVlICsgMSB9XG5cbmZ1biBhcHBseShmOiB8aTY0fCAtPiBpNjQpIC0+IGk2NCB7IGYoMSkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZiA6PSBpbmNyZW1lbnQ7XG4gICAgYXNzZXJ0KGFwcGx5KGYpID09IDIpO1xuICAgIGFzc2VydChhcHBseShmKSA9PSAyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNDFfZnVuY3Rpb25fdmFsdWVzX2FyZV9jb3B5Lm10bCIsIm5hbWUiOiI0MV9mdW5jdGlvbl92YWx1ZXNfYXJlX2NvcHkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-8}

`Callable<A, B>` is not available in `std::core`, so function types do not currently
satisfy a `Callable<A, B>` bound.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQxX2Z1bmN0aW9uX3ZhbHVlc19hcmVfY29weS5tdGwiLCJzb3VyY2UiOiJmdW4gaW5jcmVtZW50KHZhbHVlOiBpNjQpIC0+IGk2NCB7IHZhbHVlICsgMSB9XG5cbmZ1biBhcHBseShmOiB8aTY0fCAtPiBpNjQpIC0+IGk2NCB7IGYoMSkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZiA6PSBpbmNyZW1lbnQ7XG4gICAgYXNzZXJ0KGFwcGx5KGYpID09IDIpO1xuICAgIGFzc2VydChhcHBseShmKSA9PSAyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNDFfZnVuY3Rpb25fdmFsdWVzX2FyZV9jb3B5Lm10bCIsIm5hbWUiOiI0MV9mdW5jdGlvbl92YWx1ZXNfYXJlX2NvcHkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-9}

Function values are copyable for move checking, but do not satisfy aspect bounds such as
`Copy` or `Clone`.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQxX2Z1bmN0aW9uX3ZhbHVlc19hcmVfY29weS5tdGwiLCJzb3VyY2UiOiJmdW4gaW5jcmVtZW50KHZhbHVlOiBpNjQpIC0+IGk2NCB7IHZhbHVlICsgMSB9XG5cbmZ1biBhcHBseShmOiB8aTY0fCAtPiBpNjQpIC0+IGk2NCB7IGYoMSkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZiA6PSBpbmNyZW1lbnQ7XG4gICAgYXNzZXJ0KGFwcGx5KGYpID09IDIpO1xuICAgIGFzc2VydChhcHBseShmKSA9PSAyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNDFfZnVuY3Rpb25fdmFsdWVzX2FyZV9jb3B5Lm10bCIsIm5hbWUiOiI0MV9mdW5jdGlvbl92YWx1ZXNfYXJlX2NvcHkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-10}

Function types do not implement `Display`, `Eq`, `Ord`, `Hash`, `Send`, `Sync`, or `Drop`.

<!-- rfc.py:last_reviewed dbaadc2b79588e63a5bc20714720147d1f563956 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjE5Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOV9uZWdfMDRfc3RydWN0dXJhbF9mdW5jdGlvbl9lcV9ib3VuZF9yZXF1aXJlZC5tdGwiLCJzb3VyY2UiOiIvLyBOZWdhdGl2ZTogZnVuY3Rpb24gcG9pbnRlcnMgZG8gbm90IGltcGxlbWVudCBgRXFgIC0tIGZ1bmN0aW9uIGVxdWFsaXR5IGlzXG4vLyB1bmRlY2lkYWJsZSBpbiBnZW5lcmFsIChSRkMtMDA2MSBcdTAwYTc3LjMpLiBFeHBlY3QgVDAwMTIsIHRoZSBmdW5jdGlvbi10eXBlXG4vLyBzaWJsaW5nIG9mIHN0YWdlMTlfbmVnXzAyICh3aGljaCBjb3ZlcnMgYERpc3BsYXlgKSBmb3IgYSBkaWZmZXJlbnQgYXNwZWN0XG4vLyBmcm9tIHRoZSBcImFzcGVjdHMgZnVuY3Rpb24gcG9pbnRlcnMgZG8gbm90IGltcGxlbWVudFwiIHRhYmxlLlxuXG5mdW4gc2hvd19lcTxUOiBFcT4oYTogVCwgYjogVCkgLT4gYm9vbGVhbiB7XG4gICAgcmV0dXJuIGEuZXEoJmIpO1xufVxuXG5mdW4gcGx1c19vbmUoeDogaTY0KSAtPiBpNjQge1xuICAgIHJldHVybiB4ICsgMTtcbn1cblxuZnVuIG1pbnVzX29uZSh4OiBpNjQpIC0+IGk2NCB7XG4gICAgcmV0dXJuIHggLSAxO1xufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgXyA6PSBzaG93X2VxKHBsdXNfb25lLCBtaW51c19vbmUpOyAvLyBFUlJPUltUMDAxMl1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3N0YWdlMTlfbmVnXzA0X3N0cnVjdHVyYWxfZnVuY3Rpb25fZXFfYm91bmRfcmVxdWlyZWQubXRsIiwibmFtZSI6InN0YWdlMTlfbmVnXzA0X3N0cnVjdHVyYWxfZnVuY3Rpb25fZXFfYm91bmRfcmVxdWlyZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structural-aspect-bounds.legality-11}

Closures and plain functions share the same function type; captures distinguish closure
values at runtime rather than introducing a distinct closure type.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgc2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgbGV0IHMgOj0gXCJoZWxsb1wiO1xuICAgIGxldCBmIDo9IFtzXSBvbmNlIHx8IC0+IFN0cmluZyB7IHJldHVybiBzOyB9O1xuICAgIGxldCBhZ2FpbiA6PSBzO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwibmFtZSI6IjA3X2Nsb3N1cmVfY2FwdHVyZV9vZl9ub25fY29weV92YWx1ZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>
