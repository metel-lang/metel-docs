---
sidebar_position: 5
---

# Drop

## `Drop`

> **Limitation** LIMIT-EVALUATION-005

[`Drop` gives a type destructor logic](#spec.ownership.drop.legality-1) that runs when a value goes out of scope:

```metel
struct Handle { fd: i64 }

extend Handle: Drop {
    fun drop(&var self) { close_fd(self.fd); }
}
```

`Drop` is opt in. A type without a `Drop` implementation is reclaimed by recursively dropping
its fields.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.drop.legality-1}

An `extend Type: Drop` declaration gives its type `Drop` status even when its `drop` body is
empty; that status participates in ownership restrictions.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3BhcnRpYWxfbW92ZV9vZl9kcm9wX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IEhhbmRsZSB7XG4gICAgbmFtZTogU3RyaW5nLFxuICAgIGZkOiBpNjQsXG59XG5cbmV4dGVuZCBIYW5kbGU6IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikgeyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgbmFtZSA9IFwieFwiLCBmZCA9IDEgfTtcbiAgICBsZXQgbmFtZSA6PSBoYW5kbGUubmFtZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwiLCJuYW1lIjoiMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## `Copy` and `Drop` are mutually exclusive

[A type may not implement both](#spec.ownership.copy-and-drop-are-mutually-exclusive.legality-1). A `Copy` value may be duplicated freely, so there is no single
point at which a destructor should run.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.copy-and-drop-are-mutually-exclusive.legality-1}

No concrete type instantiation may implement both `Copy` and `Drop`; overlapping conditional
implementations are rejected only when an instantiation would receive both aspects.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDcxIFx1MDBhNzQgZm9yYmlkcyBvbmUgKnR5cGUqIGhhdmluZyBib3RoIGBDb3B5YCBhbmQgYERyb3BgLiBJdCBkb2VzIG5vdFxuLy8gZm9yYmlkIGEgcHJvZ3JhbSBmcm9tIGNvbnRhaW5pbmcgYW4gaW1wbCBvZiBlYWNoLCBhbmQgdGhlIGNoZWNrIGFkZGVkIGZvclxuLy8gaXNzdWUgIzMwMiBpcyBkZWxpYmVyYXRlbHkgcHJlY2lzZSBhYm91dCB0aGUgZGlmZmVyZW5jZSBcdTIwMTQgYW4gYXBwcm94aW1hdGlvblxuLy8gdGhhdCByZWplY3RlZCBhbnkgYENvcHlgIGltcGwgYW5kIGBEcm9wYCBpbXBsIHNoYXJpbmcgYSB0YXJnZXQgY29uc3RydWN0b3Jcbi8vIHdvdWxkIHJlamVjdCBib3RoIGhhbHZlcyBvZiB0aGlzIGZpbGUuXG4vL1xuLy8gVHdvIHdheXMgdGhlIHR3byBpbXBscyBjYW4gY29leGlzdDpcblxuaW5mZXIgY29weSBzdHJ1Y3QgRGlzam9pbnQ8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuLy8gMS4gUHJvdmFibHkgZGlzam9pbnQgYm91bmRzLiBObyBgVGAgaXMgYm90aCBgQ29weWAgYW5kIGAhQ29weWAsIHNvIG5vXG4vLyAgICBpbnN0YW50aWF0aW9uIG9mIGBEaXNqb2ludDxUPmAgZXZlciBoYXMgYm90aCBhc3BlY3RzLlxuXG5leHRlbmQ8VDogIUNvcHk+IERpc2pvaW50PFQ+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmluZmVyIGNvcHkgc3RydWN0IFJlYWNoPFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbi8vIDIuIEEgY29uY3JldGUgdGFyZ2V0IG91dHNpZGUgdGhlIGJsYW5rZXQncyByZWFjaC4gYFN0cmluZ2AgaXMgbm90IGBDb3B5YCxcbi8vICAgIHNvIHRoZSBibGFua2V0IGRvZXMgbm90IGFwcGx5IHRvIGBSZWFjaDxTdHJpbmc+YCBhbmQgaXQgaXMgZnJlZSB0b1xuLy8gICAgaW1wbGVtZW50IGBEcm9wYC4gV2l0aCBgaTY0YCBoZXJlIGluc3RlYWQgdGhpcyBpcyBhIFx1MDBhNzQgdmlvbGF0aW9uIFx1MjAxNFxuLy8gICAgc2VlIGB0eXBlY2hlY2tpbmcvc3RydWN0cy9zdGFnZTVfbmVnXzM1X2NvcHlfYmxhbmtldF9yZWFjaGVzX2Ryb3BfaW5zdGFudGlhdGlvbi5tdGxgLlxuXG5leHRlbmQgUmVhY2g8U3RyaW5nPjogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnZhciBzZWxmKSB7fVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgY29weWFibGUgOj0gRGlzam9pbnQgeyB2YWwgPSAxIH07XG4gICAgYXNzZXJ0KGNvcHlhYmxlLnZhbCA9PSAxKTtcblxuICAgIGxldCBkcm9wcGFibGUgOj0gRGlzam9pbnQgeyB2YWwgPSBcIm93bmVkXCIgfTtcbiAgICBhc3NlcnQoKCZkcm9wcGFibGUudmFsKS5sZW4oKSA9PSA1KTtcblxuICAgIGxldCByZWFjaGVkIDo9IFJlYWNoIHsgdmFsID0gNyB9O1xuICAgIGFzc2VydChyZWFjaGVkLnZhbCA9PSA3KTtcblxuICAgIGxldCB1bnJlYWNoZWQgOj0gUmVhY2ggeyB2YWwgPSBcIm91dHNpZGVcIiB9O1xuICAgIGFzc2VydCgoJnVucmVhY2hlZC52YWwpLmxlbigpID09IDcpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy85NV9jb3B5X2FuZF9kcm9wX25vbl9vdmVybGFwcGluZ19pbXBscy5tdGwiLCJuYW1lIjoiOTVfY29weV9hbmRfZHJvcF9ub25fb3ZlcmxhcHBpbmdfaW1wbHMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBib3RoIGJlIGdyYW50ZWQgdG8gb25lIHR5cGUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJjb3B5X2NsYXNzX2tleXdvcmRfZXhjbHVkZXNfZHJvcF90MDAxNS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDIwNiBzZWN0aW9uIDI6IGBhc3BlY3QgQ29weTogIURyb3BgIGV4Y2x1ZGVzIHRoZSBwYWlyLCBzbyBhIGBjb3B5IHN0cnVjdGAgY2Fubm90IGFsc28gYmUgYERyb3BgLlxuY29weSBzdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCB9XG5leHRlbmQgSGFuZGxlOiBEcm9wIHsgZnVuIGRyb3AoJnZhciBzZWxmKSB7IH0gfSAvLyBFUlJPUltUMDAxNV1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9jb3B5X2NsYXNzX2tleXdvcmRfZXhjbHVkZXNfZHJvcF90MDAxNS5tdGwiLCJuYW1lIjoiY29weV9jbGFzc19rZXl3b3JkX2V4Y2x1ZGVzX2Ryb3BfdDAwMTUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBib3RoIGJlIGdyYW50ZWQgdG8gb25lIHR5cGUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTVfbmVnXzM0X2NvcHlfYW5kX2Ryb3Bfb3ZlcmxhcHBpbmdfY29uZGl0aW9uYWxfaW1wbHMubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNzEgXHUwMGE3NCBhY3Jvc3MgdHdvICpjb25kaXRpb25hbCogaW1wbHMgKGlzc3VlICMzMDIpLlxuLy9cbi8vIE5laXRoZXIgaW1wbCB0YXJnZXQgaXMgY2xvc2VkLCBzbyB0aGUgZGVjbGFyYXRpb24tc2l0ZSBjaGVjayBpblxuLy8gYHR5cGVjaGVja2VyOjppbmZlcmVuY2VgIGNhbm5vdCBldmFsdWF0ZSBlaXRoZXIgb25lIFx1MjAxNCBpdCBpcyBgY29oZXJlbmNlYCdzXG4vLyBjcm9zcy1hc3BlY3Qgb3ZlcmxhcCBjaGVjayB0aGF0IHJlamVjdHMgdGhpcy4gVGhlIGJvdW5kcyBhcmUgbm90IGRpc2pvaW50OlxuLy8gYGk2NGAgaXMgYm90aCBgQ29weWAgYW5kIGBEaXNwbGF5YCwgc28gYE92ZXJsYXA8aTY0PmAgd291bGQgaGF2ZSBib3RoXG4vLyBhc3BlY3RzLCB3aGljaCBcdTAwYTc0IGZvcmJpZHMuXG5cbmluZmVyIGNvcHkgc3RydWN0IE92ZXJsYXA8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuZXh0ZW5kPFQ6IERpc3BsYXk+IE92ZXJsYXA8VD46IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikge31cbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvc3RydWN0cy9zdGFnZTVfbmVnXzM0X2NvcHlfYW5kX2Ryb3Bfb3ZlcmxhcHBpbmdfY29uZGl0aW9uYWxfaW1wbHMubXRsIiwibmFtZSI6InN0YWdlNV9uZWdfMzRfY29weV9hbmRfZHJvcF9vdmVybGFwcGluZ19jb25kaXRpb25hbF9pbXBscy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBib3RoIGJlIGdyYW50ZWQgdG8gb25lIHR5cGUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTVfbmVnXzM1X2NvcHlfYmxhbmtldF9yZWFjaGVzX2Ryb3BfaW5zdGFudGlhdGlvbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTc0IHdoZXJlIGEgYENvcHlgIGJsYW5rZXQgYW5kIGEgY29uY3JldGUgYERyb3BgIGltcGwgbWVldCBhdCBvbmVcbi8vIGluc3RhbnRpYXRpb24gKGlzc3VlICMzMDIpLlxuLy9cbi8vIGBpNjRgIGlzIGBDb3B5YCwgc28gdGhlIGJsYW5rZXQgcmVhY2hlcyBgUmVhY2g8aTY0PmAgXHUyMDE0IHRoZSBleGFjdCB0eXBlIHRoZVxuLy8gYERyb3BgIGltcGwgdGFyZ2V0cy4gQ29udHJhc3QgdGhlIGFjY2VwdGVkIGNhc2UgaW5cbi8vIGBldmFsdWF0b3Ivc3RydWN0cy85NV9jb3B5X2FuZF9kcm9wX25vbl9vdmVybGFwcGluZ19pbXBscy5tdGxgLCB3aGljaCBpc1xuLy8gdGhpcyBwcm9ncmFtIHdpdGggYFN0cmluZ2AgaW4gcGxhY2Ugb2YgYGk2NGA6IHRoZSByZWplY3Rpb24gdHVybnMgb25cbi8vIHdoZXRoZXIgdGhlIGNvbmNyZXRlIGFyZ3VtZW50IHNhdGlzZmllcyB0aGUgYmxhbmtldCdzIGJvdW5kLCBub3Qgb24gdGhlXG4vLyB0d28gaW1wbHMgbWVyZWx5IHNoYXJpbmcgYSB0YXJnZXQgY29uc3RydWN0b3IuXG5cbmluZmVyIGNvcHkgc3RydWN0IFJlYWNoPFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbmV4dGVuZCBSZWFjaDxpNjQ+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1X25lZ18zNV9jb3B5X2JsYW5rZXRfcmVhY2hlc19kcm9wX2luc3RhbnRpYXRpb24ubXRsIiwibmFtZSI6InN0YWdlNV9uZWdfMzVfY29weV9ibGFua2V0X3JlYWNoZXNfZHJvcF9pbnN0YW50aWF0aW9uLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Drop order

> **Limitation** LIMIT-EVALUATION-005

Within a scope, values are [dropped in **reverse declaration order**](#spec.ownership.drop-order.dynamics-1). A value that has been
moved out is not dropped where it was declared — the new owner drops it.

For a type with a `Drop` implementation, [`drop(self)` runs first, then its fields are dropped
recursively](#spec.ownership.drop-order.dynamics-2).

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.ownership.drop-order.dynamics-1}

When a scope ends, its still-owned values are dropped in reverse declaration order. A value
moved to another owner is dropped by that owner instead.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until they are. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until they are. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.drop-order.dynamics-2}

Dropping a value with a `Drop` implementation invokes `drop(self)` before recursively dropping
its fields.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Same root gap as drop-order.dynamics-1: destructor invocation is not implemented, so drop(self)-before-fields ordering cannot be observed." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Same root gap as drop-order.dynamics-1: destructor invocation is not implemented, so drop(self)-before-fields ordering cannot be observed._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

## Explicit drop

> **Limitation** LIMIT-EVALUATION-005

[`drop(x)` consumes `x`, runs its destructor if it has one, and marks the binding moved](#spec.ownership.explicit-drop.dynamics-1). Using
`x` afterwards is [an error, exactly as after any other move](#spec.ownership.explicit-drop.legality-1).

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.explicit-drop.legality-1}

After `drop(x)` consumes a non-`Copy` binding, that binding may not be used again.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Explicit drop(x) is not implemented -- drop is not a built-in name today (verified directly: it produces a T0003 undefined-name error), so this use-after-drop rejection cannot be observed. It also depends on move tracking." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Explicit drop(x) is not implemented -- drop is not a built-in name today (verified directly: it produces a T0003 undefined-name error), so this use-after-drop rejection cannot be observed. It also depends on move tracking._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.ownership.explicit-drop.dynamics-1}

`drop(x)` consumes `x` and invokes its destructor when its type implements `Drop`.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Same root gap as explicit-drop.legality-1: drop is not a built-in yet, so this dynamic-semantics claim cannot be exercised." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Same root gap as explicit-drop.legality-1: drop is not a built-in yet, so this dynamic-semantics claim cannot be exercised._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>
