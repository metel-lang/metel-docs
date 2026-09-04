---
title: "Ownership and Move Semantics"
---

# Ownership and Move Semantics

> **Availability:** Since v0.12.0 (RFC-0071), behind the `--move-check` flag — not the
> default typechecking path.

Every rule on this page is enforced, and every rule below with a fixture citation is
genuinely checked against the real interpreter — but only when `--move-check` is passed.
Without it, using a value after it's moved is not rejected: the interpreter behaves as
if every value were `Copy` (verified directly — a binding reused after being moved into
another still resolves, and mutating the new binding does not affect the old one). This
is an off-by-default opt-in, not a description of a future model: the existing corpus is
written in a style affine ownership rejects, so the flag stays off by default until a
separate, tracked migration addresses that.

## Values move by default

A value whose type is not `Copy` has exactly one owner at any point. Assigning it, passing it
as an argument, or returning it **moves** it: ownership transfers, and the source binding
becomes invalid.

```metel
struct Buffer { data: i64[] }

fun consume(b: Buffer) -> i64 { b.data.len() }

fun main() {
    let a := Buffer { data = [1, 2, 3] };
    let b := a;          // a is moved into b
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgc2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMV9tb3ZlX3RoZW5fdXNlLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFwiaGVsbG9cIjtcbiAgICBsZXQgbW92ZWQgOj0gcztcbiAgICBsZXQgYWdhaW4gOj0gcztcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDFfbW92ZV90aGVuX3VzZS5tdGwiLCJuYW1lIjoiMDFfbW92ZV90aGVuX3VzZS5tdGwifQ=="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6Ijk2X2NvcHlfZWxpZ2liaWxpdHlfc2Vlc19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTcyIGBDb3B5YCBlbGlnaWJpbGl0eSB0aHJvdWdoIGEgKmdlbmVyaWMqIGZpZWxkIHR5cGUgd2hvc2Ugb3duXG4vLyBgQ29weWAgaW1wbCBpcyBjb25kaXRpb25hbCAoaXNzdWUgIzMwMykuXG4vL1xuLy8gRGVjaWRpbmcgYGV4dGVuZDxUOiBDb3B5PiBPdXRlcjxUPjogQ29weWAgbWVhbnMgYW5zd2VyaW5nIHdoZXRoZXIgdGhlIGZpZWxkXG4vLyB0eXBlIGBJbm5lcjxUPmAgaXMgYENvcHlgIFx1MjAxNCBhIHF1ZXN0aW9uIHdpdGggbm8gYW5zd2VyIGluIHRlcm1zIG9mIGNvbmNyZXRlXG4vLyB0eXBlcywgc2luY2UgYFRgIGlzIG5vdCBvbmUuIEl0IGlzIGFuc3dlcmFibGUgdW5kZXIgdGhlIGltcGwncyBvd24gYm91bmRzOlxuLy8gYFRgIGlzIGFzc3VtZWQgYENvcHlgLCB3aGljaCBkaXNjaGFyZ2VzIHRoZSBib3VuZCBvbiBgSW5uZXJgJ3MgY29uZGl0aW9uYWxcbi8vIGltcGwuIFRoZSBlbGlnaWJpbGl0eSBjaGVjayB1c2VkIHRvIGdpdmUgdXAgaGVyZSBhbmQgcmVqZWN0IHRoZSBwcm9ncmFtLlxuXG5zdHJ1Y3QgSW5uZXI8VD4ge1xuICAgIHZhbHVlOiBULFxufVxuXG5leHRlbmQ8VDogQ29weT4gSW5uZXI8VD46IENvcHk7XG5cbnN0cnVjdCBPdXRlcjxUPiB7XG4gICAgaW5uZXI6IElubmVyPFQ+LFxufVxuXG5leHRlbmQ8VDogQ29weT4gT3V0ZXI8VD46IENvcHk7XG5cbi8vIFRoZSBzYW1lIHNoYXBlIHdpdGggdGhlIGJvdW5kIGluIGEgYHdoZXJlYCBjbGF1c2UgcmF0aGVyIHRoYW4gaW5saW5lLlxuc3RydWN0IFdyYXBwZWQ8VD4ge1xuICAgIGhlbGQ6IElubmVyPFQ+LFxufVxuXG5leHRlbmQ8VD4gV3JhcHBlZDxUPjogQ29weSB3aGVyZSBUOiBDb3B5O1xuXG4vLyBBbmQgdGhyb3VnaCBhbiBlbnVtIHBheWxvYWQsIHdoaWNoIHRha2VzIHRoZSBvdGhlciBicmFuY2ggb2YgdGhlIGNoZWNrLlxuZW51bSBIZWxkPFQ+IHtcbiAgICBPbmUgeyB2YWx1ZTogSW5uZXI8VD4gfSxcbiAgICBOb25lLFxufVxuXG5leHRlbmQ8VDogQ29weT4gSGVsZDxUPjogQ29weTtcblxuZnVuIGlkPFQ6IENvcHk+KHg6IFQpIC0+IFQge1xuICAgIHJldHVybiB4O1xufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgbyA6PSBPdXRlciB7IGlubmVyID0gSW5uZXIgeyB2YWx1ZSA9IDEgfSB9O1xuICAgIGxldCBjb3BpZWQgOj0gaWQobyk7XG4gICAgYXNzZXJ0KGNvcGllZC5pbm5lci52YWx1ZSA9PSAxKTtcblxuICAgIGxldCB3IDo9IFdyYXBwZWQgeyBoZWxkID0gSW5uZXIgeyB2YWx1ZSA9IDIgfSB9O1xuICAgIGxldCB3X2NvcGllZCA6PSBpZCh3KTtcbiAgICBhc3NlcnQod19jb3BpZWQuaGVsZC52YWx1ZSA9PSAyKTtcblxuICAgIGxldCBoIDo9IEhlbGQ6Ok9uZSB7IHZhbHVlID0gSW5uZXIgeyB2YWx1ZSA9IDMgfSB9O1xuICAgIGxldCBoX2NvcGllZCA6PSBpZChoKTtcbiAgICBtYXRjaCAoaF9jb3BpZWQpIHtcbiAgICAgICAgSGVsZDo6T25lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUudmFsdWUgPT0gMyksXG4gICAgICAgIEhlbGQ6Ok5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzk2X2NvcHlfZWxpZ2liaWxpdHlfc2Vlc19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJuYW1lIjoiOTZfY29weV9lbGlnaWJpbGl0eV9zZWVzX2NvbmRpdGlvbmFsX2ltcGxzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## `Drop`

`Drop` gives a type destructor logic that runs when a value goes out of scope:

```metel
struct Handle { fd: i64 }

extend Handle: Drop {
    fun drop(&var self) { close_fd(self.fd); }
}
```

`Drop` is opt in. A type without a `Drop` implementation is reclaimed by recursively dropping
its fields.

> **Changed in v0.13.0 (RFC-0071):** `drop` takes `self: &var Self`, not `self` by value.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.drop.legality-1}

An `extend Type: Drop` declaration gives its type `Drop` status even when its `drop` body is
empty; that status participates in ownership restrictions.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3BhcnRpYWxfbW92ZV9vZl9kcm9wX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IEhhbmRsZSB7XG4gICAgbmFtZTogU3RyaW5nLFxuICAgIGZkOiBpNjQsXG59XG5cbmV4dGVuZCBIYW5kbGU6IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikgeyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgbmFtZSA9IFwieFwiLCBmZCA9IDEgfTtcbiAgICBsZXQgbmFtZSA6PSBoYW5kbGUubmFtZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwiLCJuYW1lIjoiMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwifQ=="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6Ijk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDcxIFx1MDBhNzQgZm9yYmlkcyBvbmUgKnR5cGUqIGhhdmluZyBib3RoIGBDb3B5YCBhbmQgYERyb3BgLiBJdCBkb2VzIG5vdFxuLy8gZm9yYmlkIGEgcHJvZ3JhbSBmcm9tIGNvbnRhaW5pbmcgYW4gaW1wbCBvZiBlYWNoLCBhbmQgdGhlIGNoZWNrIGFkZGVkIGZvclxuLy8gaXNzdWUgIzMwMiBpcyBkZWxpYmVyYXRlbHkgcHJlY2lzZSBhYm91dCB0aGUgZGlmZmVyZW5jZSBcdTIwMTQgYW4gYXBwcm94aW1hdGlvblxuLy8gdGhhdCByZWplY3RlZCBhbnkgYENvcHlgIGltcGwgYW5kIGBEcm9wYCBpbXBsIHNoYXJpbmcgYSB0YXJnZXQgY29uc3RydWN0b3Jcbi8vIHdvdWxkIHJlamVjdCBib3RoIGhhbHZlcyBvZiB0aGlzIGZpbGUuXG4vL1xuLy8gVHdvIHdheXMgdGhlIHR3byBpbXBscyBjYW4gY29leGlzdDpcblxuc3RydWN0IERpc2pvaW50PFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbi8vIDEuIFByb3ZhYmx5IGRpc2pvaW50IGJvdW5kcy4gTm8gYFRgIGlzIGJvdGggYENvcHlgIGFuZCBgIUNvcHlgLCBzbyBub1xuLy8gICAgaW5zdGFudGlhdGlvbiBvZiBgRGlzam9pbnQ8VD5gIGV2ZXIgaGFzIGJvdGggYXNwZWN0cy5cbmV4dGVuZDxUOiBDb3B5PiBEaXNqb2ludDxUPjogQ29weTtcblxuZXh0ZW5kPFQ6ICFDb3B5PiBEaXNqb2ludDxUPjogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnZhciBzZWxmKSB7fVxufVxuXG5zdHJ1Y3QgUmVhY2g8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuLy8gMi4gQSBjb25jcmV0ZSB0YXJnZXQgb3V0c2lkZSB0aGUgYmxhbmtldCdzIHJlYWNoLiBgU3RyaW5nYCBpcyBub3QgYENvcHlgLFxuLy8gICAgc28gdGhlIGJsYW5rZXQgZG9lcyBub3QgYXBwbHkgdG8gYFJlYWNoPFN0cmluZz5gIGFuZCBpdCBpcyBmcmVlIHRvXG4vLyAgICBpbXBsZW1lbnQgYERyb3BgLiBXaXRoIGBpNjRgIGhlcmUgaW5zdGVhZCB0aGlzIGlzIGEgXHUwMGE3NCB2aW9sYXRpb24gXHUyMDE0XG4vLyAgICBzZWUgYHR5cGVjaGVja2luZy9zdHJ1Y3RzL3N0YWdlNV9uZWdfMzVfY29weV9ibGFua2V0X3JlYWNoZXNfZHJvcF9pbnN0YW50aWF0aW9uLm10bGAuXG5leHRlbmQ8VDogQ29weT4gUmVhY2g8VD46IENvcHk7XG5cbmV4dGVuZCBSZWFjaDxTdHJpbmc+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb3B5YWJsZSA6PSBEaXNqb2ludCB7IHZhbCA9IDEgfTtcbiAgICBhc3NlcnQoY29weWFibGUudmFsID09IDEpO1xuXG4gICAgbGV0IGRyb3BwYWJsZSA6PSBEaXNqb2ludCB7IHZhbCA9IFwib3duZWRcIiB9O1xuICAgIGFzc2VydCgoJmRyb3BwYWJsZS52YWwpLmxlbigpID09IDUpO1xuXG4gICAgbGV0IHJlYWNoZWQgOj0gUmVhY2ggeyB2YWwgPSA3IH07XG4gICAgYXNzZXJ0KHJlYWNoZWQudmFsID09IDcpO1xuXG4gICAgbGV0IHVucmVhY2hlZCA6PSBSZWFjaCB7IHZhbCA9IFwib3V0c2lkZVwiIH07XG4gICAgYXNzZXJ0KCgmdW5yZWFjaGVkLnZhbCkubGVuKCkgPT0gNyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bCIsIm5hbWUiOiI5NV9jb3B5X2FuZF9kcm9wX25vbl9vdmVybGFwcGluZ19pbXBscy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBpbXBsZW1lbnQgYm90aCBgQ29weWAgYW5kIGBEcm9wYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV9uZWdfMzRfY29weV9hbmRfZHJvcF9vdmVybGFwcGluZ19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTc0IGFjcm9zcyB0d28gKmNvbmRpdGlvbmFsKiBpbXBscyAoaXNzdWUgIzMwMikuXG4vL1xuLy8gTmVpdGhlciBpbXBsIHRhcmdldCBpcyBjbG9zZWQsIHNvIHRoZSBkZWNsYXJhdGlvbi1zaXRlIGNoZWNrIGluXG4vLyBgdHlwZWNoZWNrZXI6OmluZmVyZW5jZWAgY2Fubm90IGV2YWx1YXRlIGVpdGhlciBvbmUgXHUyMDE0IGl0IGlzIGBjb2hlcmVuY2VgJ3Ncbi8vIGNyb3NzLWFzcGVjdCBvdmVybGFwIGNoZWNrIHRoYXQgcmVqZWN0cyB0aGlzLiBUaGUgYm91bmRzIGFyZSBub3QgZGlzam9pbnQ6XG4vLyBgaTY0YCBpcyBib3RoIGBDb3B5YCBhbmQgYERpc3BsYXlgLCBzbyBgT3ZlcmxhcDxpNjQ+YCB3b3VsZCBoYXZlIGJvdGhcbi8vIGFzcGVjdHMsIHdoaWNoIFx1MDBhNzQgZm9yYmlkcy5cblxuc3RydWN0IE92ZXJsYXA8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuZXh0ZW5kPFQ6IENvcHk+IE92ZXJsYXA8VD46IENvcHk7XG5cbmV4dGVuZDxUOiBEaXNwbGF5PiBPdmVybGFwPFQ+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1X25lZ18zNF9jb3B5X2FuZF9kcm9wX292ZXJsYXBwaW5nX2NvbmRpdGlvbmFsX2ltcGxzLm10bCIsIm5hbWUiOiJzdGFnZTVfbmVnXzM0X2NvcHlfYW5kX2Ryb3Bfb3ZlcmxhcHBpbmdfY29uZGl0aW9uYWxfaW1wbHMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBpbXBsZW1lbnQgYm90aCBgQ29weWAgYW5kIGBEcm9wYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV9uZWdfMzVfY29weV9ibGFua2V0X3JlYWNoZXNfZHJvcF9pbnN0YW50aWF0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDcxIFx1MDBhNzQgd2hlcmUgYSBgQ29weWAgYmxhbmtldCBhbmQgYSBjb25jcmV0ZSBgRHJvcGAgaW1wbCBtZWV0IGF0IG9uZVxuLy8gaW5zdGFudGlhdGlvbiAoaXNzdWUgIzMwMikuXG4vL1xuLy8gYGk2NGAgaXMgYENvcHlgLCBzbyB0aGUgYmxhbmtldCByZWFjaGVzIGBSZWFjaDxpNjQ+YCBcdTIwMTQgdGhlIGV4YWN0IHR5cGUgdGhlXG4vLyBgRHJvcGAgaW1wbCB0YXJnZXRzLiBDb250cmFzdCB0aGUgYWNjZXB0ZWQgY2FzZSBpblxuLy8gYGV2YWx1YXRvci9zdHJ1Y3RzLzk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bGAsIHdoaWNoIGlzXG4vLyB0aGlzIHByb2dyYW0gd2l0aCBgU3RyaW5nYCBpbiBwbGFjZSBvZiBgaTY0YDogdGhlIHJlamVjdGlvbiB0dXJucyBvblxuLy8gd2hldGhlciB0aGUgY29uY3JldGUgYXJndW1lbnQgc2F0aXNmaWVzIHRoZSBibGFua2V0J3MgYm91bmQsIG5vdCBvbiB0aGVcbi8vIHR3byBpbXBscyBtZXJlbHkgc2hhcmluZyBhIHRhcmdldCBjb25zdHJ1Y3Rvci5cblxuc3RydWN0IFJlYWNoPFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbmV4dGVuZDxUOiBDb3B5PiBSZWFjaDxUPjogQ29weTtcblxuZXh0ZW5kIFJlYWNoPGk2ND46IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikge31cbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvc3RydWN0cy9zdGFnZTVfbmVnXzM1X2NvcHlfYmxhbmtldF9yZWFjaGVzX2Ryb3BfaW5zdGFudGlhdGlvbi5tdGwiLCJuYW1lIjoic3RhZ2U1X25lZ18zNV9jb3B5X2JsYW5rZXRfcmVhY2hlc19kcm9wX2luc3RhbnRpYXRpb24ubXRsIn0="></details>
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
    let p := Pair { a = Buffer { data = [1] }, b = 42 };
    let x := p.a;        // p.a moved out; p is partially moved
    let y := p.b;        // still fine — p.b was not moved
    // consume_pair(p); // error: `p` cannot be used as a whole
}
```

Tracking is at **field granularity**. Pattern destructuring may move several fields at once,
under the same rules.

**A type implementing `Drop` may not be partially moved** — its destructor requires the whole
value.

Reassigning a moved-out field restores that field's own accessibility, and — once every
field ever moved out of a value has been reassigned — [restores the value's whole-value
status too](#spec.ownership.partial-moves.legality-3): the compiler tracks *which* fields
are currently missing, not merely whether the value was ever partially moved. Reassigning
only some of several moved-out fields leaves the value partially moved until the rest are
reassigned too.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.partial-moves.legality-1}

After a field of a non-`Drop` struct is moved, the remaining fields may be accessed but the
containing value may not be used as a whole.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgUGFpcmAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7XG4gICAgbGVmdDogU3RyaW5nLFxuICAgIHJpZ2h0OiBpNjQsXG59XG5cbmZ1biB0YWtlKHBhaXI6IFBhaXIpIC0+IGk2NCB7XG4gICAgcGFpci5yaWdodFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHBhaXIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHBhaXIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJuYW1lIjoiMDJfcGFydGlhbF9tb3ZlX3VzZWRfYXNfd2hvbGUubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-2}

A field of a `Drop` type may not be moved out.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3BhcnRpYWxfbW92ZV9vZl9kcm9wX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IEhhbmRsZSB7XG4gICAgbmFtZTogU3RyaW5nLFxuICAgIGZkOiBpNjQsXG59XG5cbmV4dGVuZCBIYW5kbGU6IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikgeyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgbmFtZSA9IFwieFwiLCBmZCA9IDEgfTtcbiAgICBsZXQgbmFtZSA6PSBoYW5kbGUubmFtZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwiLCJuYW1lIjoiMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-3}

Assigning a value to a field that was moved out restores that field's own accessibility.
Once every field ever moved out of a value has been reassigned this way, the value's
whole-value status is restored too, and it may be used as a whole again; reassigning only
some of several moved-out fields is not enough.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIge1xuICAgIGxlZnQ6IFN0cmluZyxcbiAgICByaWdodDogU3RyaW5nLFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IFwiYlwiIH07XG4gICAgbGV0IHRha2VuIDo9IHAubGVmdDtcbiAgICBwLmxlZnQgOj0gXCJjXCI7XG4gICAgbGV0IHdob2xlIDo9IHA7XG4gICAgYXNzZXJ0KHRha2VuID09IFwiYVwiKTtcbiAgICBhc3NlcnQod2hvbGUubGVmdCA9PSBcImNcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIiwibmFtZSI6IjUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgVHdvYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVHdvIHtcbiAgICBsZWZ0OiBTdHJpbmcsXG4gICAgcmlnaHQ6IFN0cmluZyxcbn1cblxuZnVuIHRha2UodDogVHdvKSAtPiBpNjQge1xuICAgIHQubGVmdC5sZW4oKVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSBUd28geyBsZWZ0ID0gXCJhXCIsIHJpZ2h0ID0gXCJiXCIgfTtcbiAgICBsZXQgdGFrZW5fbGVmdCA6PSB0LmxlZnQ7XG4gICAgbGV0IHRha2VuX3JpZ2h0IDo9IHQucmlnaHQ7XG4gICAgdC5sZWZ0IDo9IFwiY1wiO1xuICAgIC8vIHQucmlnaHQgaXMgc3RpbGwgbW92ZWQgb3V0IC0tIHJlYXNzaWduaW5nIG9ubHkgb25lIG9mIHR3byBtb3ZlZCBmaWVsZHMgZG9lc1xuICAgIC8vIG5vdCByZXN0b3JlIHdob2xlLXZhbHVlIHN0YXR1czsgYHRgIHN0YXlzIHBhcnRpYWxseSBtb3ZlZC5cbiAgICBsZXQgbiA6PSB0YWtlKHQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83M19yZWFzc2lnbmluZ19vbmx5X29uZV9vZl90d29fbW92ZWRfZmllbGRzX3N0YXlzX3BhcnRpYWwubXRsIiwibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-4}

Destructuring a struct or tuple with a pattern that binds a subset of its fields (a struct
pattern with `..`, a tuple pattern, a bound field of a matched variant's payload) moves
exactly those fields, leaving the scrutinee partially moved under the same rules as an
explicit field move — including the `Drop`-type ban ([legality-2](#spec.ownership.partial-moves.legality-2)).

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjE2X21hdGNoX2Ryb3BfZmllbGRfcGFydGlhbF9tb3ZlX2lzX2Jhbm5lZC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgSGFuZGxlIHtcbiAgICBuYW1lOiBTdHJpbmcsXG4gICAgZmQ6IGk2NCxcbn1cblxuZXh0ZW5kIEhhbmRsZTogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnZhciBzZWxmKSB7IH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGhhbmRsZSA6PSBIYW5kbGUgeyBuYW1lID0gXCJ4XCIsIGZkID0gMSB9O1xuICAgIGxldCBuIDo9IG1hdGNoIChoYW5kbGUubmFtZSkge1xuICAgICAgICBuYW1lID0+IG5hbWUubGVuKCksXG4gICAgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMTZfbWF0Y2hfZHJvcF9maWVsZF9wYXJ0aWFsX21vdmVfaXNfYmFubmVkLm10bCIsIm5hbWUiOiIxNl9tYXRjaF9kcm9wX2ZpZWxkX3BhcnRpYWxfbW92ZV9pc19iYW5uZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

> **Availability:** Since v0.12.0 (RFC-0071), behind `--move-check`. A `Drop` type may
> still be partially *borrowed*; only moving out is restricted.

> **Planned for v0.14.0 (RFC-0137 §5): legality-2's ban is superseded in design by
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImBwYWlyLjBgIHdhcyBtb3ZlZCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjA0X3R1cGxlX2VsZW1lbnRfbW92ZV90aGVuX3VzZS5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSAoXCJ4XCIsIDEpO1xuICAgIGxldCBsZWZ0IDo9IHBhaXIuMDtcbiAgICBsZXQgYWdhaW4gOj0gcGFpci4wO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wNF90dXBsZV9lbGVtZW50X21vdmVfdGhlbl91c2UubXRsIiwibmFtZSI6IjA0X3R1cGxlX2VsZW1lbnRfbW92ZV90aGVuX3VzZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgdmFsdWVgIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiMDVfZW51bV9wYXlsb2FkX2NvbnN1bWVzX3dob2xlX3ZhbHVlLm10bCIsInNvdXJjZSI6ImVudW0gTWF5YmVUZXh0IHtcbiAgICBFbXB0eSxcbiAgICBGdWxsIHsgdGV4dDogU3RyaW5nIH0sXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB2YWx1ZSA6PSBNYXliZVRleHQ6OkZ1bGwgeyB0ZXh0ID0gXCJ4XCIgfTtcbiAgICBsZXQgbiA6PSBtYXRjaCAodmFsdWUpIHtcbiAgICAgICAgTWF5YmVUZXh0OjpGdWxsIHsgdGV4dCB9ID0+IHRleHQubGVuKCksXG4gICAgICAgIE1heWJlVGV4dDo6RW1wdHkgPT4gMCxcbiAgICB9O1xuICAgIGxldCBhZ2FpbiA6PSB2YWx1ZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDVfZW51bV9wYXlsb2FkX2NvbnN1bWVzX3dob2xlX3ZhbHVlLm10bCIsIm5hbWUiOiIwNV9lbnVtX3BheWxvYWRfY29uc3VtZXNfd2hvbGVfdmFsdWUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImFycmF5IGVsZW1lbnQgbW92ZXMgYXJlIG5vdCBhbGxvd2VkIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiMDZfYXJyYXlfZWxlbWVudF9tb3ZlX2lzX2Jhbm5lZC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gW1wieFwiXTtcbiAgICBsZXQgZmlyc3QgOj0geHNbMF07XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzA2X2FycmF5X2VsZW1lbnRfbW92ZV9pc19iYW5uZWQubXRsIiwibmFtZSI6IjA2X2FycmF5X2VsZW1lbnRfbW92ZV9pc19iYW5uZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgc2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgbGV0IHMgOj0gXCJoZWxsb1wiO1xuICAgIGxldCBmIDo9IFtzXSBvbmNlIHx8IC0+IFN0cmluZyB7IHJldHVybiBzOyB9O1xuICAgIGxldCBhZ2FpbiA6PSBzO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwibmFtZSI6IjA3X2Nsb3N1cmVfY2FwdHVyZV9vZl9ub25fY29weV92YWx1ZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2}

Record fields may be moved independently, at field granularity like struct fields; a
moved field's siblings remain individually accessible, but using the record value as a
whole afterward is rejected as a use of a partially moved value. Moving a field
**narrows the record's static type** to the fields that remain
([narrowing.legality-1](#spec.ownership.narrowing.legality-1), RFC-0117) — the same
mechanism struct narrowing uses, minus the brand.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNl9yZWNvcmRfcm93X25hcnJvd2luZy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhbiBhbm9ueW1vdXNcbi8vIHJlY29yZCBuYXJyb3dzIHRoZSByZWNvcmQncyBzdGF0aWMgdHlwZSB0byB0aGUgZmllbGRzIHRoYXQgcmVtYWluIC0tIHRoZSBzYW1lXG4vLyBtZWNoYW5pc20gc3RydWN0IG5hcnJvd2luZyB1c2VzIChSRkMtMDEzNyksIG1pbnVzIHRoZSBicmFuZC4gVGhlIG5hcnJvd2VkXG4vLyByZWNvcmQgaXMgYW4gb3JkaW5hcnkgdmFsdWU6IGl0cyBzaWJsaW5ncyBzdGF5IHJlYWRhYmxlIGFuZCBpdCBmaXRzIGFcbi8vIHBhcmFtZXRlciB3aG9zZSByb3cgbWF0Y2hlcyBleGFjdGx5LlxuXG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImFcIi50b19zdHJpbmcoKSwgcmlnaHQgPSA3IH07XG4gICAgbGV0IHRha2VuIDo9IHIubGVmdDsgICAgICAgICAgICAgICAgIC8vIHIgOiB7IHJpZ2h0OiBpNjQgfSBmcm9tIGhlcmUgb25cbiAgICBhc3NlcnQoci5yaWdodCA9PSA3KTsgICAgICAgICAgICAgICAgLy8gc2libGluZyBzdGlsbCByZWFkYWJsZVxuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA3KTsgICAgICAgICAgICAvLyBleGFjdC1yb3cgcGFyYW1ldGVyIGFjY2VwdHMgdGhlIG5hcnJvd2VkIHJlY29yZFxuXG4gICAgLy8gQSBgQ29weWAgZmllbGQgcmVhZCBieSB2YWx1ZSBpcyBhIGNvcHksIG5vdCBhIG1vdmUgLS0gbm8gbmFycm93aW5nLlxuICAgIGxldCBwdCA6PSB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCB4X2NvcHkgOj0gcHQueDtcbiAgICBhc3NlcnQocHQueCArIHB0LnkgPT0gMyk7ICAgICAgICAgICAgLy8gcHQgaXMgc3RpbGwgdGhlIHdob2xlIHJlY29yZFxuICAgIGFzc2VydCh4X2NvcHkgPT0gMSk7XG5cbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTA2X3JlY29yZF9yb3dfbmFycm93aW5nLm10bCIsIm5hbWUiOiIxMDZfcmVjb3JkX3Jvd19uYXJyb3dpbmcubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjcxX3JlY29yZF9maWVsZF9tb3ZlZF9pbmRlcGVuZGVudGx5Lm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHIubGVmdDtcbiAgICBhc3NlcnQobGVmdCA9PSBcImFcIik7XG4gICAgYXNzZXJ0KHIucmlnaHQgPT0gMSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzcxX3JlY29yZF9maWVsZF9tb3ZlZF9pbmRlcGVuZGVudGx5Lm10bCIsIm5hbWUiOiI3MV9yZWNvcmRfZmllbGRfbW92ZWRfaW5kZXBlbmRlbnRseS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Narrowing

Every `struct` is represented, for type-checking purposes, as a fixed nominal identity
(its **brand**, minted once at declaration) paired with its current **row** — the set of
fields still present.

**Available now (RFC-0137, metel-core#857): a struct's own field projection is
branded.** `h.{ fd }` — reading fields out on a copy of the reference, not consuming the
original — produces a residual of `h`'s own brand, not a same-shaped anonymous record:

```metel
struct Handle { fd: i64, name: String }

extend Handle {
    fun describe(h: Self.{ fd }) -> i64 { h.fd }
}

fun main() -> i64 {
    let handle := Handle { fd = 3, name = "x" };
    return Handle::describe(handle.{ fd });   // OK -- branded Handle.{ fd }
    // Handle::describe({ fd = 3 })            // rejected -- no brand, T0001
}
```

A projection naming *every* field the struct declares normalizes back to the plain
struct type instead of staying a distinct residual — `h.{ fd, name }` here is just
`Handle`, still rejected by a row bound the same way a bare `Handle` value already is.

> **Since v0.13.0: moving a field out of a value also narrows its *type*** — not just a
> change in what the compiler internally tracks about it (see
> [Partial moves](#partial-moves) above). For a **struct** (RFC-0137 slice 2,
> metel-core#858) `h.name` produces exactly the branded residual type `h.{ fd }`
> (projection) produces — the same mechanism, reached two ways. For an **anonymous
> `record`** (RFC-0117, metel-core#789) `r.left` moved out leaves `r : { right: i64 }`.
> Using the narrowed value where the whole type (or a wider row) is required is a plain
> type error at type-check time, not only a `--move-check` finding.

The residual is an ordinary value: it can be bound, passed, returned, dropped, and
narrowed again. For a value over *N* fields, the space of residual shapes is the subset
lattice, bounded by 2^*N* — there is no row variable and no unification involved in
computing it. The rule applies uniformly to a **nominal struct's** row (residual of the
same brand, `Handle.{ fd }`) and to an **anonymous `record`'s** row (the record type with
the moved label removed, `{ fd: i64 }` — no brand clause). A record-typed **field** is
moved as a **unit** — a residual's row never carries a *narrower* type for a field it
still holds; narrowing a field of a field in place is
RFC-0150's. A field read by
value whose type is `Copy` is a copy, not a move, and does not narrow; a field whose type
is a bare generic parameter or is not yet resolved is held (not dropped from the row)
until its type is known.

> **Difference between the two.** A struct residual is a distinct type (`Type::Residual`,
> a brand plus a strict subset row), so a whole-value use after a partial move reports
> against the binding by name — "a partially-moved `Handle` …". An anonymous record
> residual is just a `Record` with fewer fields, structurally identical to any other
> narrower record, so the same mistake reports as an ordinary record-shape mismatch
> ("cannot unify `{ right }` with `{ left, right }`"). Both are type errors at
> type-check time.

Narrowing is **path-sensitive**: the residual type at a program point reflects the fields
moved on every path reaching it, exactly as move tracking already computes — a field
moved on one arm of an `if` is conservatively moved after the join. A move made inside a
loop body narrows the value after the loop. A use *within* the body that only becomes
invalid on a later iteration is still surfaced by `--move-check` rather than as a
narrowing type error. Narrowing adds no control-flow analysis of its own; it is the
type-level reading of the move state.

**A residual's row is never visible to structural matching, regardless of its width.**
This is unchanged from today's rule that only a `record` (not a `struct`) satisfies a
[row bound](types.md#spec.types.generics.row-bounds.legality-4) — eligibility for
structural matching is scoped to the brand alone, fixed at declaration, never to row
content. A struct value narrowed down to every one of its own fields is still,
unambiguously, that struct — not a same-shaped anonymous record, and not a
`record`-declared type of the same shape.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.narrowing.legality-1}

Moving a field out of a value narrows that value's type to a row with the moved field
removed: for a nominal struct, a residual of the same brand (`Handle.{ fd }`, RFC-0137);
for an anonymous `record`, the record type with that label gone (`{ fd: i64 }`, RFC-0117).
A record-typed field is moved as a whole — the residual never holds a field at a narrower
type. A field read by value whose type is `Copy` is a copy, not a move, and does not
narrow; a field whose type is a bare generic parameter or is not yet resolved is held in
the row until its type is known. Narrowing is path-sensitive: the residual type at a
program point reflects the fields moved on every path reaching it, joined conservatively
at merge points and through loop fixpoints, exactly as move tracking computes.

> **Since v0.13.0.** Struct narrowing is RFC-0137 slice 2 (metel-core#858); anonymous-record
> narrowing is RFC-0117 (metel-core#789). A whole-value use after a partial move is a
> plain type error at type-check time for both — reported against the binding for a struct
> residual, as an ordinary record-shape mismatch for a record. A loop-carried *use*
> invalid only on a later iteration is still a `--move-check` diagnostic.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0117](../../rfcs/4-implemented/rfc-0117-row-narrowing.md), [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNl9yZWNvcmRfcm93X25hcnJvd2luZy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhbiBhbm9ueW1vdXNcbi8vIHJlY29yZCBuYXJyb3dzIHRoZSByZWNvcmQncyBzdGF0aWMgdHlwZSB0byB0aGUgZmllbGRzIHRoYXQgcmVtYWluIC0tIHRoZSBzYW1lXG4vLyBtZWNoYW5pc20gc3RydWN0IG5hcnJvd2luZyB1c2VzIChSRkMtMDEzNyksIG1pbnVzIHRoZSBicmFuZC4gVGhlIG5hcnJvd2VkXG4vLyByZWNvcmQgaXMgYW4gb3JkaW5hcnkgdmFsdWU6IGl0cyBzaWJsaW5ncyBzdGF5IHJlYWRhYmxlIGFuZCBpdCBmaXRzIGFcbi8vIHBhcmFtZXRlciB3aG9zZSByb3cgbWF0Y2hlcyBleGFjdGx5LlxuXG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImFcIi50b19zdHJpbmcoKSwgcmlnaHQgPSA3IH07XG4gICAgbGV0IHRha2VuIDo9IHIubGVmdDsgICAgICAgICAgICAgICAgIC8vIHIgOiB7IHJpZ2h0OiBpNjQgfSBmcm9tIGhlcmUgb25cbiAgICBhc3NlcnQoci5yaWdodCA9PSA3KTsgICAgICAgICAgICAgICAgLy8gc2libGluZyBzdGlsbCByZWFkYWJsZVxuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA3KTsgICAgICAgICAgICAvLyBleGFjdC1yb3cgcGFyYW1ldGVyIGFjY2VwdHMgdGhlIG5hcnJvd2VkIHJlY29yZFxuXG4gICAgLy8gQSBgQ29weWAgZmllbGQgcmVhZCBieSB2YWx1ZSBpcyBhIGNvcHksIG5vdCBhIG1vdmUgLS0gbm8gbmFycm93aW5nLlxuICAgIGxldCBwdCA6PSB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCB4X2NvcHkgOj0gcHQueDtcbiAgICBhc3NlcnQocHQueCArIHB0LnkgPT0gMyk7ICAgICAgICAgICAgLy8gcHQgaXMgc3RpbGwgdGhlIHdob2xlIHJlY29yZFxuICAgIGFzc2VydCh4X2NvcHkgPT0gMSk7XG5cbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTA2X3JlY29yZF9yb3dfbmFycm93aW5nLm10bCIsIm5hbWUiOiIxMDZfcmVjb3JkX3Jvd19uYXJyb3dpbmcubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNyAvIFJGQy0wMTE3IChtZXRlbC1jb3JlIzk1MCk6IHdpdGggYC0tbW92ZS1jaGVja2Agb24sIGEgd2hvbGUtdmFsdWUgdXNlXG4vLyBvZiBhIGJpbmRpbmcgd2hvc2UgdHlwZSBoYXMgbmFycm93ZWQgdG8gYSByZXNpZHVhbCAvIG5hcnJvd2VyIHJlY29yZCBpcyBsZWdhbFxuLy8gLS0gbmFycm93aW5nIHJlbW92ZWQgZXhhY3RseSB0aGUgbW92ZWQgZmllbGRzLCBzbyB0aGUgdXNlIHRvdWNoZXMgbm9uZSBvZiB0aGVtLlxuLy8gQmVmb3JlICM5NTAsIGBtb3ZlX2NoZWNrYCBmbGFnZ2VkIGV2ZXJ5IHdob2xlLXZhbHVlIHVzZSBvZiBhIHBhcnRpYWxseS1tb3ZlZFxuLy8gYmluZGluZyByZWdhcmRsZXNzIG9mIGl0cyBjdXJyZW50IHR5cGUuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuZnVuIHRha2VfZmQoaDogSGFuZGxlLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBTdHJ1Y3Q6IG5hcnJvd2VkIHRvIEhhbmRsZS57IGZkIH0sIHRoZW4gbW92ZWQgaW4gYnkgdmFsdWUgb25jZS5cbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBobiA6PSBoLm5hbWU7XG4gICAgYXNzZXJ0KHRha2VfZmQoaCkgPT0gMyk7XG5cbiAgICAvLyBBbm9ueW1vdXMgcmVjb3JkOiBuYXJyb3dlZCB0byB7IHJpZ2h0OiBpNjQgfSwgdGhlbiBtb3ZlZCBpbiBieSB2YWx1ZSBvbmNlLlxuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDkgfTtcbiAgICBsZXQgcmwgOj0gci5sZWZ0O1xuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA5KTtcblxuICAgIC8vIEEgbmFycm93ZWQgYmluZGluZyByZWFkIChub3QgbW92ZWQpIGFzIGEgd2hvbGUgaXMgZmluZSB0b28uXG4gICAgbGV0IGcgOj0gSGFuZGxlIHsgZmQgPSA0LCBuYW1lID0gXCJ5XCIgfTtcbiAgICBsZXQgZ24gOj0gZy5uYW1lO1xuICAgIGxldCBhbGlhcyA6PSBnLnsgZmQgfTtcbiAgICBhc3NlcnQoYWxpYXMuZmQgPT0gNCk7XG5cbiAgICBwcmludGxuKFwiJHtobn0gJHtybH0gJHtnbn1cIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJuYW1lIjoiMTA3X21vdmVfY2hlY2tfbmFycm93ZWRfd2hvbGVfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogcm93LW5hcnJvd2luZyBtb3ZlIHN0YXRlIGlzIHBhdGgtc2Vuc2l0aXZlIGFjcm9zcyBgaWZgIGFybXMuXG4vLyBCb3RoIGFybXMgbW92ZSB0aGUgc2FtZSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBgcmVjYDsgdGhlIGBlbHNlYCBhcm0gZG9lc1xuLy8gbm90IHNlZSB0aGUgYHRoZW5gIGFybSdzIG1vdmUsIHNvIGVhY2ggaXMgYW4gaW5kZXBlbmRlbnQgcGFydGlhbCBtb3ZlLiBBZnRlclxuLy8gdGhlIGBpZmAgdGhlIGFybXMgam9pbjogYHJlY2AgaXMgbmFycm93ZWQgdG8gYHsga2VlcDogaTY0IH1gIG9uIGV2ZXJ5IHBhdGgsXG4vLyBpdHMgc3Vydml2aW5nIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgYSB3aG9sZS12YWx1ZSB1c2UgYXQgdGhlIG5hcnJvd2VkXG4vLyByb3cgaXMgYWNjZXB0ZWQgKGFsc28gdW5kZXIgLS1tb3ZlLWNoZWNrKS5cbmZ1biBrZWVwX29mKHI6IHsga2VlcDogaTY0IH0pIC0+IGk2NCB7IHIua2VlcCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb25kIDo9IHRydWU7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInhcIi50b19zdHJpbmcoKSwga2VlcCA9IDMgfTtcbiAgICBpZiAoY29uZCkge1xuICAgICAgICBsZXQgYSA6PSByZWMuZ29uZTtcbiAgICAgICAgYXNzZXJ0KGEgPT0gXCJ4XCIpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIGxldCBiIDo9IHJlYy5nb25lO1xuICAgICAgICBhc3NlcnQoYiA9PSBcInhcIik7XG4gICAgfVxuICAgIGFzc2VydChyZWMua2VlcCA9PSAzKTsgICAgICAgICAgLy8gc3Vydml2aW5nIGZpZWxkIHJlYWRhYmxlIGF0IHRoZSBqb2luZWQgcm93XG4gICAgYXNzZXJ0KGtlZXBfb2YocmVjKSA9PSAzKTsgICAgICAvLyB3aG9sZSB2YWx1ZSBmaXRzIHRoZSBuYXJyb3dlZCByb3dcbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJuYW1lIjoiMTEwX25hcnJvd2luZ19pZl9hcm1zX2luZGVwZW5kZW50Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExMV9uYXJyb3dpbmdfbWF0Y2hfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogdGhlIHNhbWUgcGVyLWFybSBmb3JrL2pvaW4gZm9yIGBtYXRjaGAuIFR3byBhcm1zIGVhY2ggbW92ZVxuLy8gdGhlIHNhbWUgbm9uLWBDb3B5YCBmaWVsZCBvZiBhbiBvdXRlciBiaW5kaW5nOyBhIGxhdGVyIGFybSBkb2VzIG5vdCBzZWUgYW5cbi8vIGVhcmxpZXIgYXJtJ3MgbW92ZS4gVGhlIGFybXMgam9pbiBhZnRlciB0aGUgYG1hdGNoYCwgbmFycm93aW5nIGByZWNgIHRvXG4vLyBgeyBrZWVwOiBpNjQgfWAuXG5mdW4ga2VlcF9vZihyOiB7IGtlZXA6IGk2NCB9KSAtPiBpNjQgeyByLmtlZXAgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgc2VsIDo9IDI7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInlcIi50b19zdHJpbmcoKSwga2VlcCA9IDcgfTtcbiAgICBsZXQgdGFnIDo9IG1hdGNoIChzZWwpIHtcbiAgICAgICAgMSA9PiB7IGxldCBhIDo9IHJlYy5nb25lOyAxMCB9LFxuICAgICAgICAyID0+IHsgbGV0IGIgOj0gcmVjLmdvbmU7IDIwIH0sXG4gICAgICAgIF8gPT4geyBsZXQgYyA6PSByZWMuZ29uZTsgMzAgfSxcbiAgICB9O1xuICAgIGFzc2VydCh0YWcgPT0gMjApO1xuICAgIGFzc2VydChyZWMua2VlcCA9PSA3KTtcbiAgICBhc3NlcnQoa2VlcF9vZihyZWMpID09IDcpO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTExX25hcnJvd2luZ19tYXRjaF9hcm1zX2luZGVwZW5kZW50Lm10bCIsIm5hbWUiOiIxMTFfbmFycm93aW5nX21hdGNoX2FybXNfaW5kZXBlbmRlbnQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjcyX3JlY29yZF91c2VkX2FzX3dob2xlX2FmdGVyX2ZpZWxkX21vdmUubXRsIiwic291cmNlIjoiZnVuIHRha2UocjogeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBpNjQgfSkgLT4gaTY0IHtcbiAgICByLnJpZ2h0XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83Ml9yZWNvcmRfdXNlZF9hc193aG9sZV9hZnRlcl9maWVsZF9tb3ZlLm10bCIsIm5hbWUiOiI3Ml9yZWNvcmRfdXNlZF9hc193aG9sZV9hZnRlcl9maWVsZF9tb3ZlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgVHdvYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVHdvIHtcbiAgICBsZWZ0OiBTdHJpbmcsXG4gICAgcmlnaHQ6IFN0cmluZyxcbn1cblxuZnVuIHRha2UodDogVHdvKSAtPiBpNjQge1xuICAgIHQubGVmdC5sZW4oKVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSBUd28geyBsZWZ0ID0gXCJhXCIsIHJpZ2h0ID0gXCJiXCIgfTtcbiAgICBsZXQgdGFrZW5fbGVmdCA6PSB0LmxlZnQ7XG4gICAgbGV0IHRha2VuX3JpZ2h0IDo9IHQucmlnaHQ7XG4gICAgdC5sZWZ0IDo9IFwiY1wiO1xuICAgIC8vIHQucmlnaHQgaXMgc3RpbGwgbW92ZWQgb3V0IC0tIHJlYXNzaWduaW5nIG9ubHkgb25lIG9mIHR3byBtb3ZlZCBmaWVsZHMgZG9lc1xuICAgIC8vIG5vdCByZXN0b3JlIHdob2xlLXZhbHVlIHN0YXR1czsgYHRgIHN0YXlzIHBhcnRpYWxseSBtb3ZlZC5cbiAgICBsZXQgbiA6PSB0YWtlKHQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83M19yZWFzc2lnbmluZ19vbmx5X29uZV9vZl90d29fbW92ZWRfZmllbGRzX3N0YXlzX3BhcnRpYWwubXRsIiwibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180OF9yZWNvcmRfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBvbmNlIGEgZmllbGQgaXMgbW92ZWQgb3V0IG9mIGFuIGFub255bW91cyByZWNvcmQsXG4vLyB0aGUgcmVjb3JkJ3MgdHlwZSBpcyB0aGUgbmFycm93ZXIgcm93IC0tIGB7IHJpZ2h0OiBpNjQgfWAsIG5vdCBgeyBsZWZ0LCByaWdodCB9YC5cbi8vIFBhc3NpbmcgaXQgd2hlcmUgdGhlIHdob2xlIHJlY29yZCBpcyByZXF1aXJlZCBpcyBhIHBsYWluIHR5cGUgZXJyb3IgYXRcbi8vIGluZmVyZW5jZSB0aW1lLCBubyBsb25nZXIgb25seSBhIGAtLW1vdmUtY2hlY2tgIGZpbmRpbmcuIEEgbmFycm93ZWQgcmVjb3JkIGhhc1xuLy8gbm8gZGlzdGluY3QgdHlwZSBtYXJrZXIsIHNvIHRoZSBkaWFnbm9zdGljIGlzIHRoZSBvcmRpbmFyeSByZWNvcmQtc2hhcGVcbi8vIG1pc21hdGNoLlxuXG5mdW4gd2FudHNfZnVsbChyOiB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IGk2NCB9KSAtPiBpNjQgeyByLnJpZ2h0IH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyBsZWZ0ID0gXCJhXCIudG9fc3RyaW5nKCksIHJpZ2h0ID0gMSB9O1xuICAgIGxldCB0YWtlbiA6PSByLmxlZnQ7XG4gICAgbGV0IF8gOj0gd2FudHNfZnVsbChyKTtcbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ4X3JlY29yZF93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDhfcmVjb3JkX3dob2xlX3VzZV9hZnRlcl9wYXJ0aWFsX21vdmUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjOTU4OiB0aGUgam9pbiBpcyB0aGUgKnVuaW9uKiBvZiB0aGUgYXJtcycgbW92ZXMuIE9ubHkgdGhlIGB0aGVuYFxuLy8gYXJtIG1vdmVzIGByZWMuZ29uZWA7IGFmdGVyIHRoZSBgaWZgLCBgcmVjYCBpcyBuYXJyb3dlZCB0byBgeyBrZWVwOiBpNjQgfWAgb25cbi8vIGV2ZXJ5IHBhdGggKHRoZSBtb3ZlIGlzIGpvaW5lZCBpbiBldmVuIHRob3VnaCB0aGUgYGVsc2VgIHBhdGggZGlkbid0IHJ1biBpdCksXG4vLyBzbyBhIHdob2xlLXZhbHVlIHVzZSBhdCB0aGUgd2lkZXIgcm93IGlzIHJlamVjdGVkLlxuZnVuIHdob2xlKHI6IHsgZ29uZTogU3RyaW5nLCBrZWVwOiBpNjQgfSkgLT4gaTY0IHsgci5rZWVwIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGNvbmQgOj0gdHJ1ZTtcbiAgICBsZXQgcmVjIDo9IHsgZ29uZSA9IFwielwiLnRvX3N0cmluZygpLCBrZWVwID0gMSB9O1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIGxldCBhIDo9IHJlYy5nb25lO1xuICAgIH1cbiAgICB3aG9sZShyZWMpICAgICAgICAgICAgICAvLyByZWMgOiB7IGtlZXA6IGk2NCB9IGhlcmUgLS0gd2lkZXIgcm93IHJlcXVpcmVkXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsIm5hbWUiOiJuZWdfNTBfbmFycm93aW5nX29uZV9hcm1fbW92ZV90YWludHNfam9pbi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InYwXzEzXzBfeF9tb3ZlX2NhcHR1cmVfb2ZfbmFycm93ZWRfc3RydWN0Lm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBjbG9zdXJlIGNhcHR1cmVcbi8vIChSRkMtMDE1NyBENSkgbWVldHMgbW92ZS10cmlnZ2VyZWQgc3RydWN0IHJvdyBuYXJyb3dpbmcgKFJGQy0wMTM3IHNsaWNlIDIpLlxuLy8gQSBub24tYENvcHlgIGZpZWxkIGlzIG1vdmVkIG91dCBmaXJzdCwgbmFycm93aW5nIGBoYCB0byBgSGFuZGxlLnsgZmQgfWA7IHRoZVxuLy8gY2xvc3VyZSB0aGVuIGNhcHR1cmVzIHRoZSAqbmFycm93ZWQqIHZhbHVlIGJ5IHZhbHVlLiBUaGUgY2FwdHVyZSBsaXN0IG5hbWVzXG4vLyBgaGAsIHRoZSByZXNpZHVhbCBtb3ZlcyBpbnRvIHRoZSBlbnZpcm9ubWVudCBvbmNlLCBhbmQgYC0tbW92ZS1jaGVja2AgaXNcbi8vIGNsZWFuIC0tIG5hcnJvd2luZyBhbHJlYWR5IHJlbW92ZWQgdGhlIGZpZWxkIHRoYXQgbGVmdC5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAvLyBoIDogSGFuZGxlLnsgZmQgfVxuICAgIGxldCBnZXQgOj0gW2hdIG9uY2UgfHwgeyBoLmZkIH07ICAgICAvLyBjYXB0dXJlcyB0aGUgcmVzaWR1YWwgYnkgdmFsdWVcbiAgICBhc3NlcnQoZ2V0KCkgPT0gNyk7XG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jbG9zdXJlcy92MF8xM18wX3hfbW92ZV9jYXB0dXJlX29mX25hcnJvd2VkX3N0cnVjdC5tdGwiLCJuYW1lIjoidjBfMTNfMF94X21vdmVfY2FwdHVyZV9vZl9uYXJyb3dlZF9zdHJ1Y3QubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-2}

A residual's row is never visible to structural matching; only its brand, fixed at
declaration, determines eligibility, regardless of how narrow or wide the current row is.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0117](../../rfcs/4-implemented/rfc-0117-row-narrowing.md), [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSk6IHRoaXMgaXMgdGhlIGFjdHVhbCBtb3RpdmF0aW5nIGJ1Z1xuLy8gLS0gU2VsZi57IGZkIH0gdXNlZCB0byBhY2NlcHQgYSBiYXJlIGFub255bW91cyByZWNvcmQgbGl0ZXJhbCBvZiB0aGUgc2FtZSBzaGFwZVxuLy8gZXhhY3RseSBhcyByZWFkaWx5IGFzIGEgdmFsdWUgYWN0dWFsbHkgZGVyaXZlZCBmcm9tIGEgcmVhbCBIYW5kbGUsIHNpbmNlIHRoZVxuLy8gcHJvamVjdGlvbiByZXNvbHZlZCB0byBhbiB1bmJyYW5kZWQgcmVjb3JkIHR5cGUuIE5vdyByZWplY3RlZDogYSBzdHJ1Y3QncyBvd25cbi8vIHByb2plY3Rpb24gaXMgYnJhbmRlZCwgYW5kIGEgc2FtZS1zaGFwZWQgYW5vbnltb3VzIHJlY29yZCBuZXZlciBjYXJyaWVzIHRoYXRcbi8vIGJyYW5kLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6IFNlbGYueyBmZCB9KSAtPiBpNjQgeyBoLmZkIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IF8gOj0gSGFuZGxlOjpkZXNjcmliZSh7IGZkID0gMyB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6ImlzIG5vdCBhIHJlY29yZCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180NV9yZXNpZHVhbF9uZXZlcl9zYXRpc2ZpZXNfcm93X2JvdW5kLm10bCIsInNvdXJjZSI6Ii8vIFJlZ3Jlc3Npb24gKG1ldGVsLWNvcmUjODU3LCBSRkMtMDEzNyBzbGljZSAxKTogYSBnZW51aW5lIChub24tZnVsbC13aWR0aCkgYnJhbmRlZFxuLy8gcmVzaWR1YWwgbmV2ZXIgc2F0aXNmaWVzIGEgcm93IGJvdW5kIGVpdGhlciAtLSBlbGlnaWJpbGl0eSBmb3Igc3RydWN0dXJhbFxuLy8gbWF0Y2hpbmcgaXMgc2NvcGVkIHRvIHRoZSBicmFuZCBhbG9uZSAoUkZDLTAxMzcgc2VjMyksIGFuZCBhIHN0cnVjdCdzIGJyYW5kIGlzXG4vLyBuZXZlciB2aXNpYmxlIHRvIG1hdGNoaW5nIHJlZ2FyZGxlc3Mgb2YgaG93IG5hcnJvdyBpdHMgY3VycmVudCByb3cgaXMuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcsIGV4dHJhOiBpNjQgfVxuXG5mdW4gd2FudHNfYV9yZWNvcmQ8cmVjb3JkIFQ6IHsgZmQ6IGk2NCwgLi4gfT4odDogVCkgLT4gaTY0IHsgdC5mZCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gMywgbmFtZSA9IFwieFwiLCBleHRyYSA9IDkgfTtcbiAgICBsZXQgXyA6PSB3YW50c19hX3JlY29yZChoLnsgZmQgfSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180NV9yZXNpZHVhbF9uZXZlcl9zYXRpc2ZpZXNfcm93X2JvdW5kLm10bCIsIm5hbWUiOiJuZWdfNDVfcmVzaWR1YWxfbmV2ZXJfc2F0aXNmaWVzX3Jvd19ib3VuZC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-3}

A projection or a residual naming **every** field the struct declares is not a distinct
residual type — it normalizes back to the plain struct type, and is rejected by a row
bound exactly as a bare struct value already is. A residual's row is therefore always a
strict, non-empty subset of the brand's declared row.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6InN0cnVjdCBuZXZlciBzYXRpc2ZpZXMgYSByb3cgYm91bmQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfNDRfZnVsbF93aWR0aF9wcm9qZWN0aW9uX3N0aWxsX3JlamVjdGVkX2J5X3Jvd19ib3VuZC5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSdzIG93biBub3JtYWxpemF0aW9uIHJ1bGUsIGFuZFxuLy8gUkZDLTAxMzcgc2VjMydzIHdvcmtlZCBleGFtcGxlKTogYSBwcm9qZWN0aW9uIG5hbWluZyBldmVyeSBmaWVsZCBhIHN0cnVjdFxuLy8gZGVjbGFyZXMgbm9ybWFsaXplcyBiYWNrIHRvIHRoZSBwbGFpbiBzdHJ1Y3QgdHlwZSByYXRoZXIgdGhhbiBzdGF5aW5nIGFcbi8vIGRpc3RpbmN0IGJyYW5kZWQgcmVzaWR1YWwuIENvbmZpcm1zIHRoZSBub3JtYWxpemF0aW9uIGRvZXNuJ3QgYWNjaWRlbnRhbGx5XG4vLyBlYXJuIHJvdy1ib3VuZCBlbGlnaWJpbGl0eSAtLSBoLnsgZmQsIG5hbWUgfSwgZnVsbCB3aWR0aCwgaXMgcmVqZWN0ZWQgYnkgYSByb3dcbi8vIGJvdW5kIHRoZSBleGFjdCBzYW1lIHdheSBhIGJhcmUgYEhhbmRsZWAgdmFsdWUgYWxyZWFkeSBpcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biB3YW50c19hX3JlY29yZDxyZWNvcmQgVDogeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcsIC4uIH0+KHQ6IFQpIC0+IGk2NCB7IHQuZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBfIDo9IHdhbnRzX2FfcmVjb3JkKGgueyBmZCwgbmFtZSB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ0X2Z1bGxfd2lkdGhfcHJvamVjdGlvbl9zdGlsbF9yZWplY3RlZF9ieV9yb3dfYm91bmQubXRsIiwibmFtZSI6Im5lZ180NF9mdWxsX3dpZHRoX3Byb2plY3Rpb25fc3RpbGxfcmVqZWN0ZWRfYnlfcm93X2JvdW5kLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-4}

Using a narrowed value where a wider row, or the whole type, is required is a type error
at type-check time — not deferred to `--move-check`. Every still-present field of the
residual stays readable and its methods callable. For a **struct** residual the error
names the binding ("a partially-moved `Handle` …"); for an **anonymous record** it is an
ordinary record-shape mismatch (a narrowed `{ right }` does not unify with `{ left, right
}`).

Conversely, a whole-value use of the binding **at its narrowed type** — moving it,
binding it, passing it to a parameter whose row it matches — is legal, and `--move-check`
does not flag it (metel-core#950): narrowing removed exactly the moved fields, so no live
use touches one.

> **Since v0.13.0.** Struct: RFC-0137 slice 2 (metel-core#858). Anonymous record:
> RFC-0117 (metel-core#789). `--move-check` agreement: metel-core#950.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgUGFpcmAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7XG4gICAgbGVmdDogU3RyaW5nLFxuICAgIHJpZ2h0OiBpNjQsXG59XG5cbmZ1biB0YWtlKHBhaXI6IFBhaXIpIC0+IGk2NCB7XG4gICAgcGFpci5yaWdodFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHBhaXIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHBhaXIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJuYW1lIjoiMDJfcGFydGlhbF9tb3ZlX3VzZWRfYXNfd2hvbGUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNyAvIFJGQy0wMTE3IChtZXRlbC1jb3JlIzk1MCk6IHdpdGggYC0tbW92ZS1jaGVja2Agb24sIGEgd2hvbGUtdmFsdWUgdXNlXG4vLyBvZiBhIGJpbmRpbmcgd2hvc2UgdHlwZSBoYXMgbmFycm93ZWQgdG8gYSByZXNpZHVhbCAvIG5hcnJvd2VyIHJlY29yZCBpcyBsZWdhbFxuLy8gLS0gbmFycm93aW5nIHJlbW92ZWQgZXhhY3RseSB0aGUgbW92ZWQgZmllbGRzLCBzbyB0aGUgdXNlIHRvdWNoZXMgbm9uZSBvZiB0aGVtLlxuLy8gQmVmb3JlICM5NTAsIGBtb3ZlX2NoZWNrYCBmbGFnZ2VkIGV2ZXJ5IHdob2xlLXZhbHVlIHVzZSBvZiBhIHBhcnRpYWxseS1tb3ZlZFxuLy8gYmluZGluZyByZWdhcmRsZXNzIG9mIGl0cyBjdXJyZW50IHR5cGUuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuZnVuIHRha2VfZmQoaDogSGFuZGxlLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBTdHJ1Y3Q6IG5hcnJvd2VkIHRvIEhhbmRsZS57IGZkIH0sIHRoZW4gbW92ZWQgaW4gYnkgdmFsdWUgb25jZS5cbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBobiA6PSBoLm5hbWU7XG4gICAgYXNzZXJ0KHRha2VfZmQoaCkgPT0gMyk7XG5cbiAgICAvLyBBbm9ueW1vdXMgcmVjb3JkOiBuYXJyb3dlZCB0byB7IHJpZ2h0OiBpNjQgfSwgdGhlbiBtb3ZlZCBpbiBieSB2YWx1ZSBvbmNlLlxuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDkgfTtcbiAgICBsZXQgcmwgOj0gci5sZWZ0O1xuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA5KTtcblxuICAgIC8vIEEgbmFycm93ZWQgYmluZGluZyByZWFkIChub3QgbW92ZWQpIGFzIGEgd2hvbGUgaXMgZmluZSB0b28uXG4gICAgbGV0IGcgOj0gSGFuZGxlIHsgZmQgPSA0LCBuYW1lID0gXCJ5XCIgfTtcbiAgICBsZXQgZ24gOj0gZy5uYW1lO1xuICAgIGxldCBhbGlhcyA6PSBnLnsgZmQgfTtcbiAgICBhc3NlcnQoYWxpYXMuZmQgPT0gNCk7XG5cbiAgICBwcmludGxuKFwiJHtobn0gJHtybH0gJHtnbn1cIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJuYW1lIjoiMTA3X21vdmVfY2hlY2tfbmFycm93ZWRfd2hvbGVfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogcm93LW5hcnJvd2luZyBtb3ZlIHN0YXRlIGlzIHBhdGgtc2Vuc2l0aXZlIGFjcm9zcyBgaWZgIGFybXMuXG4vLyBCb3RoIGFybXMgbW92ZSB0aGUgc2FtZSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBgcmVjYDsgdGhlIGBlbHNlYCBhcm0gZG9lc1xuLy8gbm90IHNlZSB0aGUgYHRoZW5gIGFybSdzIG1vdmUsIHNvIGVhY2ggaXMgYW4gaW5kZXBlbmRlbnQgcGFydGlhbCBtb3ZlLiBBZnRlclxuLy8gdGhlIGBpZmAgdGhlIGFybXMgam9pbjogYHJlY2AgaXMgbmFycm93ZWQgdG8gYHsga2VlcDogaTY0IH1gIG9uIGV2ZXJ5IHBhdGgsXG4vLyBpdHMgc3Vydml2aW5nIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgYSB3aG9sZS12YWx1ZSB1c2UgYXQgdGhlIG5hcnJvd2VkXG4vLyByb3cgaXMgYWNjZXB0ZWQgKGFsc28gdW5kZXIgLS1tb3ZlLWNoZWNrKS5cbmZ1biBrZWVwX29mKHI6IHsga2VlcDogaTY0IH0pIC0+IGk2NCB7IHIua2VlcCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb25kIDo9IHRydWU7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInhcIi50b19zdHJpbmcoKSwga2VlcCA9IDMgfTtcbiAgICBpZiAoY29uZCkge1xuICAgICAgICBsZXQgYSA6PSByZWMuZ29uZTtcbiAgICAgICAgYXNzZXJ0KGEgPT0gXCJ4XCIpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIGxldCBiIDo9IHJlYy5nb25lO1xuICAgICAgICBhc3NlcnQoYiA9PSBcInhcIik7XG4gICAgfVxuICAgIGFzc2VydChyZWMua2VlcCA9PSAzKTsgICAgICAgICAgLy8gc3Vydml2aW5nIGZpZWxkIHJlYWRhYmxlIGF0IHRoZSBqb2luZWQgcm93XG4gICAgYXNzZXJ0KGtlZXBfb2YocmVjKSA9PSAzKTsgICAgICAvLyB3aG9sZSB2YWx1ZSBmaXRzIHRoZSBuYXJyb3dlZCByb3dcbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJuYW1lIjoiMTEwX25hcnJvd2luZ19pZl9hcm1zX2luZGVwZW5kZW50Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExMV9uYXJyb3dpbmdfbWF0Y2hfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogdGhlIHNhbWUgcGVyLWFybSBmb3JrL2pvaW4gZm9yIGBtYXRjaGAuIFR3byBhcm1zIGVhY2ggbW92ZVxuLy8gdGhlIHNhbWUgbm9uLWBDb3B5YCBmaWVsZCBvZiBhbiBvdXRlciBiaW5kaW5nOyBhIGxhdGVyIGFybSBkb2VzIG5vdCBzZWUgYW5cbi8vIGVhcmxpZXIgYXJtJ3MgbW92ZS4gVGhlIGFybXMgam9pbiBhZnRlciB0aGUgYG1hdGNoYCwgbmFycm93aW5nIGByZWNgIHRvXG4vLyBgeyBrZWVwOiBpNjQgfWAuXG5mdW4ga2VlcF9vZihyOiB7IGtlZXA6IGk2NCB9KSAtPiBpNjQgeyByLmtlZXAgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgc2VsIDo9IDI7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInlcIi50b19zdHJpbmcoKSwga2VlcCA9IDcgfTtcbiAgICBsZXQgdGFnIDo9IG1hdGNoIChzZWwpIHtcbiAgICAgICAgMSA9PiB7IGxldCBhIDo9IHJlYy5nb25lOyAxMCB9LFxuICAgICAgICAyID0+IHsgbGV0IGIgOj0gcmVjLmdvbmU7IDIwIH0sXG4gICAgICAgIF8gPT4geyBsZXQgYyA6PSByZWMuZ29uZTsgMzAgfSxcbiAgICB9O1xuICAgIGFzc2VydCh0YWcgPT0gMjApO1xuICAgIGFzc2VydChyZWMua2VlcCA9PSA3KTtcbiAgICBhc3NlcnQoa2VlcF9vZihyZWMpID09IDcpO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTExX25hcnJvd2luZ19tYXRjaF9hcm1zX2luZGVwZW5kZW50Lm10bCIsIm5hbWUiOiIxMTFfbmFycm93aW5nX21hdGNoX2FybXNfaW5kZXBlbmRlbnQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgSGFuZGxlYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180Nl93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogb25jZSBhIGZpZWxkIGlzIG1vdmVkIG91dCwgdGhlIHZhbHVlJ3MgdHlwZVxuLy8gaXMgdGhlIHJlc2lkdWFsIC0tIGBIYW5kbGUueyBmZCB9YCAtLSBub3QgdGhlIHdob2xlIGBIYW5kbGVgLiBQYXNzaW5nIGl0IHdoZXJlXG4vLyB0aGUgd2hvbGUgc3RydWN0IGlzIHJlcXVpcmVkIGlzIGEgcGxhaW4gdHlwZSBlcnJvciBhdCBpbmZlcmVuY2UgdGltZSwgbm8gbG9uZ2VyXG4vLyBvbmx5IGEgYC0tbW92ZS1jaGVja2AgZmluZGluZy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biB3YW50c19mdWxsKGg6IEhhbmRsZSkgLT4gaTY0IHsgaC5mZCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gMywgbmFtZSA9IFwieFwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTtcbiAgICBsZXQgXyA6PSB3YW50c19mdWxsKGgpOyAgIC8vIHJlamVjdGVkOiBgaGAgaXMgYEhhbmRsZS57IGZkIH1gXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180Nl93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDZfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180OF9yZWNvcmRfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBvbmNlIGEgZmllbGQgaXMgbW92ZWQgb3V0IG9mIGFuIGFub255bW91cyByZWNvcmQsXG4vLyB0aGUgcmVjb3JkJ3MgdHlwZSBpcyB0aGUgbmFycm93ZXIgcm93IC0tIGB7IHJpZ2h0OiBpNjQgfWAsIG5vdCBgeyBsZWZ0LCByaWdodCB9YC5cbi8vIFBhc3NpbmcgaXQgd2hlcmUgdGhlIHdob2xlIHJlY29yZCBpcyByZXF1aXJlZCBpcyBhIHBsYWluIHR5cGUgZXJyb3IgYXRcbi8vIGluZmVyZW5jZSB0aW1lLCBubyBsb25nZXIgb25seSBhIGAtLW1vdmUtY2hlY2tgIGZpbmRpbmcuIEEgbmFycm93ZWQgcmVjb3JkIGhhc1xuLy8gbm8gZGlzdGluY3QgdHlwZSBtYXJrZXIsIHNvIHRoZSBkaWFnbm9zdGljIGlzIHRoZSBvcmRpbmFyeSByZWNvcmQtc2hhcGVcbi8vIG1pc21hdGNoLlxuXG5mdW4gd2FudHNfZnVsbChyOiB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IGk2NCB9KSAtPiBpNjQgeyByLnJpZ2h0IH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyBsZWZ0ID0gXCJhXCIudG9fc3RyaW5nKCksIHJpZ2h0ID0gMSB9O1xuICAgIGxldCB0YWtlbiA6PSByLmxlZnQ7XG4gICAgbGV0IF8gOj0gd2FudHNfZnVsbChyKTtcbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ4X3JlY29yZF93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDhfcmVjb3JkX3dob2xlX3VzZV9hZnRlcl9wYXJ0aWFsX21vdmUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjOTU4OiB0aGUgam9pbiBpcyB0aGUgKnVuaW9uKiBvZiB0aGUgYXJtcycgbW92ZXMuIE9ubHkgdGhlIGB0aGVuYFxuLy8gYXJtIG1vdmVzIGByZWMuZ29uZWA7IGFmdGVyIHRoZSBgaWZgLCBgcmVjYCBpcyBuYXJyb3dlZCB0byBgeyBrZWVwOiBpNjQgfWAgb25cbi8vIGV2ZXJ5IHBhdGggKHRoZSBtb3ZlIGlzIGpvaW5lZCBpbiBldmVuIHRob3VnaCB0aGUgYGVsc2VgIHBhdGggZGlkbid0IHJ1biBpdCksXG4vLyBzbyBhIHdob2xlLXZhbHVlIHVzZSBhdCB0aGUgd2lkZXIgcm93IGlzIHJlamVjdGVkLlxuZnVuIHdob2xlKHI6IHsgZ29uZTogU3RyaW5nLCBrZWVwOiBpNjQgfSkgLT4gaTY0IHsgci5rZWVwIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGNvbmQgOj0gdHJ1ZTtcbiAgICBsZXQgcmVjIDo9IHsgZ29uZSA9IFwielwiLnRvX3N0cmluZygpLCBrZWVwID0gMSB9O1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIGxldCBhIDo9IHJlYy5nb25lO1xuICAgIH1cbiAgICB3aG9sZShyZWMpICAgICAgICAgICAgICAvLyByZWMgOiB7IGtlZXA6IGk2NCB9IGhlcmUgLS0gd2lkZXIgcm93IHJlcXVpcmVkXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsIm5hbWUiOiJuZWdfNTBfbmFycm93aW5nX29uZV9hcm1fbW92ZV90YWludHNfam9pbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-5}

A residual may itself be projected (`h.{ fd }` on an already-narrowed `h`) for a field
still in its row; naming a field already moved out of it is rejected.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwOF9hbGlhc19xdWFsaWZpZWRfbWV0aG9kX29uX25hcnJvd2VkX3JlY2VpdmVyLm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBhIHRyYW5zcGFyZW50XG4vLyB0eXBlIGFsaWFzIChSRkMtMDE2MCkgcXVhbGlmeWluZyBhIGNhbGwsIGFuIGBleHRlbmRgIG1ldGhvZCB3aG9zZSByZWNlaXZlciBpc1xuLy8gYSBicmFuZGVkIHJlc2lkdWFsIGAmU2VsZi57IGZkIH1gIChSRkMtMDEzNyBzbGljZSAxKSwgYW5kIGEgcmVjZWl2ZXIgbmFycm93ZWRcbi8vIGJ5IGEgcGFydGlhbCBtb3ZlIChSRkMtMDEzNyBzbGljZSAyKS4gVGhlIGFsaWFzIGVyYXNlcyB0byBgSGFuZGxlYCwgc29cbi8vIGBIOjpkZXNjcmliZWAgaXMgYEhhbmRsZTo6ZGVzY3JpYmVgOyB0aGUgbmFycm93ZWQgYGhgIGFuZCBhbiBleHBsaWNpdFxuLy8gcmUtcHJvamVjdGlvbiBgaC57IGZkIH1gIGJvdGggZml0IHRoZSByZXNpZHVhbCBwYXJhbWV0ZXIuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cbnR5cGUgSCA6PSBIYW5kbGU7XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiAmU2VsZi57IGZkIH0pIC0+IGk2NCB7IGguZmQgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaDogSCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBhc3NlcnQoSDo6ZGVzY3JpYmUoJmgpID09IDcpOyAgICAgICAgICAgIC8vIGFsaWFzLXF1YWxpZmllZCBjYWxsLCBuYXJyb3dlZCByZWNlaXZlclxuICAgIGFzc2VydChIOjpkZXNjcmliZSgmaC57IGZkIH0pID09IDcpOyAgICAgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDhfYWxpYXNfcXVhbGlmaWVkX21ldGhvZF9vbl9uYXJyb3dlZF9yZWNlaXZlci5tdGwiLCJuYW1lIjoiMTA4X2FsaWFzX3F1YWxpZmllZF9tZXRob2Rfb25fbmFycm93ZWRfcmVjZWl2ZXIubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.ownership.narrowing.dynamics-1}

A struct's own field projection expression produces exactly the same residual type as the
equivalent partial move.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwOF9hbGlhc19xdWFsaWZpZWRfbWV0aG9kX29uX25hcnJvd2VkX3JlY2VpdmVyLm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBhIHRyYW5zcGFyZW50XG4vLyB0eXBlIGFsaWFzIChSRkMtMDE2MCkgcXVhbGlmeWluZyBhIGNhbGwsIGFuIGBleHRlbmRgIG1ldGhvZCB3aG9zZSByZWNlaXZlciBpc1xuLy8gYSBicmFuZGVkIHJlc2lkdWFsIGAmU2VsZi57IGZkIH1gIChSRkMtMDEzNyBzbGljZSAxKSwgYW5kIGEgcmVjZWl2ZXIgbmFycm93ZWRcbi8vIGJ5IGEgcGFydGlhbCBtb3ZlIChSRkMtMDEzNyBzbGljZSAyKS4gVGhlIGFsaWFzIGVyYXNlcyB0byBgSGFuZGxlYCwgc29cbi8vIGBIOjpkZXNjcmliZWAgaXMgYEhhbmRsZTo6ZGVzY3JpYmVgOyB0aGUgbmFycm93ZWQgYGhgIGFuZCBhbiBleHBsaWNpdFxuLy8gcmUtcHJvamVjdGlvbiBgaC57IGZkIH1gIGJvdGggZml0IHRoZSByZXNpZHVhbCBwYXJhbWV0ZXIuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cbnR5cGUgSCA6PSBIYW5kbGU7XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiAmU2VsZi57IGZkIH0pIC0+IGk2NCB7IGguZmQgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaDogSCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBhc3NlcnQoSDo6ZGVzY3JpYmUoJmgpID09IDcpOyAgICAgICAgICAgIC8vIGFsaWFzLXF1YWxpZmllZCBjYWxsLCBuYXJyb3dlZCByZWNlaXZlclxuICAgIGFzc2VydChIOjpkZXNjcmliZSgmaC57IGZkIH0pID09IDcpOyAgICAgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDhfYWxpYXNfcXVhbGlmaWVkX21ldGhvZF9vbl9uYXJyb3dlZF9yZWNlaXZlci5tdGwiLCJuYW1lIjoiMTA4X2FsaWFzX3F1YWxpZmllZF9tZXRob2Rfb25fbmFycm93ZWRfcmVjZWl2ZXIubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Passing a residual to a function

> **Available now (RFC-0137, metel-core#857), for a projection-produced residual.**
> Once move-triggered narrowing lands (metel-core#858), a residual reached that way is
> passed exactly the same way — nothing here is specific to how the residual arose.

A parameter naming a struct's own projected type (`Handle.{ fd }`, or `Self.{ fd }`
inside `Handle`'s own `extend` block) is ordinary type-matching, available to every
struct regardless of whether it opts into any structural-matching mechanism:

```metel
struct Handle { fd: i64, name: String }

extend Handle {
    fun describe(h: Self.{ fd }) -> i64 { h.fd }
}

fun main() {
    let handle := Handle { fd = 3, name = "x" };
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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwM19icmFuZGVkX3JlY29yZF9wcm9qZWN0aW9uX2FjY2VwdHNfcmVhbF9wcm9qZWN0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJlZ3Jlc3Npb24gKG1ldGVsLWNvcmUjODU3LCBSRkMtMDEzNyBzbGljZSAxKTogYSBzdHJ1Y3QncyBvd24gZmllbGQgcHJvamVjdGlvbiBpc1xuLy8gbm93IGJyYW5kZWQgLS0gU2VsZi57IGZkIH0gYWNjZXB0cyBhIHZhbHVlIGFjdHVhbGx5IHByb2plY3RlZCBmcm9tIGEgcmVhbCBIYW5kbGVcbi8vIChoLnsgZmQgfSksIHRoZSBjYXNlIHRoaXMgZml4dHVyZSBjb25maXJtcyBzdGlsbCB3b3Jrcy4gVGhlIGNvbXBhbmlvbiBuZWdhdGl2ZVxuLy8gY2FzZSAoYSBiYXJlIGFub255bW91cyByZWNvcmQgb2YgdGhlIHNhbWUgc2hhcGUgbXVzdCBub3cgYmUgUkVKRUNURUQsIHdoaWNoIGlzXG4vLyB0aGUgYWN0dWFsIGJ1ZyB0aGlzIGNsb3NlcykgbGl2ZXMgaW4gdHlwZWNoZWNraW5nL3N0cnVjdHMsIHNpbmNlIGl0J3MgYSBUMDAwMVxuLy8gcmVqZWN0aW9uLCBub3Qgc29tZXRoaW5nIGV2YWx1YWJsZS5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiBTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgZmQgPSAzLCBuYW1lID0gXCJ4XCIgfTtcbiAgICBhc3NlcnQoSGFuZGxlOjpkZXNjcmliZShoYW5kbGUueyBmZCB9KSA9PSAzKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTAzX2JyYW5kZWRfcmVjb3JkX3Byb2plY3Rpb25fYWNjZXB0c19yZWFsX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwM19icmFuZGVkX3JlY29yZF9wcm9qZWN0aW9uX2FjY2VwdHNfcmVhbF9wcm9qZWN0aW9uLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSk6IHRoaXMgaXMgdGhlIGFjdHVhbCBtb3RpdmF0aW5nIGJ1Z1xuLy8gLS0gU2VsZi57IGZkIH0gdXNlZCB0byBhY2NlcHQgYSBiYXJlIGFub255bW91cyByZWNvcmQgbGl0ZXJhbCBvZiB0aGUgc2FtZSBzaGFwZVxuLy8gZXhhY3RseSBhcyByZWFkaWx5IGFzIGEgdmFsdWUgYWN0dWFsbHkgZGVyaXZlZCBmcm9tIGEgcmVhbCBIYW5kbGUsIHNpbmNlIHRoZVxuLy8gcHJvamVjdGlvbiByZXNvbHZlZCB0byBhbiB1bmJyYW5kZWQgcmVjb3JkIHR5cGUuIE5vdyByZWplY3RlZDogYSBzdHJ1Y3QncyBvd25cbi8vIHByb2plY3Rpb24gaXMgYnJhbmRlZCwgYW5kIGEgc2FtZS1zaGFwZWQgYW5vbnltb3VzIHJlY29yZCBuZXZlciBjYXJyaWVzIHRoYXRcbi8vIGJyYW5kLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6IFNlbGYueyBmZCB9KSAtPiBpNjQgeyBoLmZkIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IF8gOj0gSGFuZGxlOjpkZXNjcmliZSh7IGZkID0gMyB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Drop dispatch against a narrowed residual

> **Planned for v0.14.0 (RFC-0137 §5, metel-core#858).** Needs the narrowed `drop`
> receiver (RFC-0109); supersedes the `Drop`-type partial-move ban above *in design*,
> and until implemented that ban is enforced exactly as stated.

A struct implementing `Drop` whose destructor needs a field that has since been narrowed
away must not silently skip the destructor's work. Dispatch is **row-bounded**: a `Drop`
impl's required field set is the residual row its `drop` method's receiver is declared
with — the fields named in a projected receiver (`fun drop(&var self: Self.{ fd })`) or
in its `where` clause (`fun drop<row R>(&var self: Self.R) where R: { fd, .. }`). A `drop`
method whose receiver is the bare `&var self` requires the struct's whole row, and no
partial move of such a type is permitted. The destructor fires against any residual of
the correct brand whose current row is a superset of that declared set, regardless of
what else has already been moved out. The destructor body is checked against its declared
receiver row: it may name only fields in that row, and may call only `self`-methods whose
own declared receiver row that row satisfies.

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

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); RFC-0071's unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); RFC-0071's unconditional partial-move-with-Drop ban is still enforced today (behind --move-check, off by default)._</span>
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

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Depends on row-bounded Drop dispatch (above, RFC-0137 slice 2, metel-core#858). dyn Aspect itself is fully implemented now (RFC-0008, metel-core#865/#863/#864, closed 2026-08-28) -- syntax, object safety, and coercion of a value to one -- so the erasure side of this checkpoint is real; what is still missing is the narrowed residual to run it against, which is metel-core#949's job. Do not attempt this checkpoint until #949 lands." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Depends on row-bounded Drop dispatch (above, RFC-0137 slice 2, metel-core#858). dyn Aspect itself is fully implemented now (RFC-0008, metel-core#865/#863/#864, closed 2026-08-28) -- syntax, object safety, and coercion of a value to one -- so the erasure side of this checkpoint is real; what is still missing is the narrowed residual to run it against, which is metel-core#949's job. Do not attempt this checkpoint until #949 lands._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-3}

A `Drop` impl's `drop` method may declare its `&var self` receiver as a residual type of
`Self` — a field projection (`&var self: Self.{ a, b }`) or a row parameter constrained
by an open lower bound (`fun drop<row R>(&var self: Self.R) where R: { a, b, .. }`). The
fields named by that declaration are the impl's required field set (legality-1). A bare
`&var self` names every field.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); the narrowed drop-receiver forms additionally depend on their own not-yet-integrated syntax (RFC-0109 named views for the fixed projection form, RFC-0147; RFC-0146 for the row-parameter form, RFC-0148). Until then a drop receiver is always the whole value and the required set is always the whole row." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); the narrowed drop-receiver forms additionally depend on their own not-yet-integrated syntax (RFC-0109 named views for the fixed projection form, RFC-0147; RFC-0146 for the row-parameter form, RFC-0148). Until then a drop receiver is always the whole value and the required set is always the whole row._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Legality Rule {#spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-4}

Within a `Drop` impl whose `drop` receiver is declared narrowed (legality-3), the
destructor body may read or write only fields in that declared row, and may call a
`self`-method only when that method's own declared receiver row is satisfied by the
`drop` receiver's declared row. Each is a local check at the access or call site; no
whole-body or call-graph analysis derives the required field set.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#949" reason="Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); with no narrowed drop-receiver form yet, there is no declared row for a body to be checked against. The reject_inert_destructor gate (metel-core#292) additionally rejects any non-empty drop body until destructor invocation (metel-core#261) lands." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#949: Row-bounded Drop dispatch is not implemented (RFC-0137 §5, metel-core#949); with no narrowed drop-receiver form yet, there is no declared row for a body to be checked against. The reject_inert_destructor gate (metel-core#292) additionally rejects any non-empty drop body until destructor invocation (metel-core#261) lands._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

### Widening

Reassigning a moved-out field [already restores the containing value's whole-value
status today](#spec.ownership.partial-moves.legality-3), for every struct regardless of
`Drop` — this is existing, unconditional `--move-check` behavior, not itself part of
RFC-0137.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858): once narrowing gives the residual a
> named type (above), reassigning a moved-out field also widens that type back
> automatically** —
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

##### Legality Rule {#spec.ownership.widening.legality-1}

A field assignment on a narrowed residual (`h.name := …`) is legal even though `name` is
absent from the residual's current row — the assigned field is resolved against the
brand's full declared row, and the write reintroduces it. Widening applies only to an
**owned** binding; a non-`Copy` field cannot be moved out of — and so cannot be
reassigned back into — a value reached through a reference
([references-and-moves.legality-1](#spec.ownership.references-and-moves.legality-1)).
Widening performs no constructor-invariant check; that is RFC-0114's, and ordinary field
reassignment bypasses such an invariant today regardless of this feature.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNV93aWRlbmluZ19yZWFzc2lnbl9yZXN0b3Jlc19mdWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogYXNzaWduaW5nIGEgdmFsdWUgdG8gYSBmaWVsZCBtaXNzaW5nIGZyb20gYVxuLy8gcmVzaWR1YWwncyByb3cgd2lkZW5zIHRoZSByZXNpZHVhbCdzIHR5cGUgYmFjayB0byB0aGUgd2hvbGUgYnJhbmRcbi8vIChzcGVjLm93bmVyc2hpcC53aWRlbmluZy5keW5hbWljcy0xKS4gT25seSBmb3IgYW4gb3duZWQgYmluZGluZzsgd2lkZW5pbmcgZG9lc1xuLy8gbm90IHJlLWNoZWNrIGFueSBjb25zdHJ1Y3RvciBpbnZhcmlhbnQuIFdpdGggYC0tbW92ZS1jaGVja2Agb24sIHRoZSB3aWRlbmVkXG4vLyBiaW5kaW5nIGlzIHdob2xlIGFnYWluIC0tIGEgYnktdmFsdWUgdXNlIGlzIGEgY2xlYW4gbW92ZSwgbm90IGEgcGFydGlhbC1tb3ZlXG4vLyB2aW9sYXRpb24uXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gd2FudHNfZnVsbChoOiBIYW5kbGUpIC0+IGk2NCB7IGguZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgaCA6PSBIYW5kbGUgeyBmZCA9IDUsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBoLm5hbWUgOj0gXCJ5XCI7ICAgICAgICAgICAgICAgICAgICAgLy8gd2lkZW5zIGJhY2s6IGggOiBIYW5kbGVcbiAgICBhc3NlcnQoaC5uYW1lID09IFwieVwiKTsgICAgICAgICAgICAgLy8gc2libGluZyByZWFkYWJsZSBhdCB0aGUgd2lkZW5lZCB0eXBlXG4gICAgYXNzZXJ0KHdhbnRzX2Z1bGwoaCkgPT0gNSk7ICAgICAgICAvLyB3aG9sZSBgSGFuZGxlYCBtb3ZlZCBpbiwgb25jZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDVfd2lkZW5pbmdfcmVhc3NpZ25fcmVzdG9yZXNfZnVsbC5tdGwiLCJuYW1lIjoiMTA1X3dpZGVuaW5nX3JlYXNzaWduX3Jlc3RvcmVzX2Z1bGwubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InJlZmVyZW5jZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBuYXJyb3dpbmcgYW5kIHdpZGVuaW5nIGFwcGx5IG9ubHkgdG8gYW5cbi8vIG93bmVkIGJpbmRpbmcuIEEgbm9uLWBDb3B5YCBmaWVsZCBjYW5ub3QgYmUgbW92ZWQgb3V0IG9mIGEgdmFsdWUgcmVhY2hlZFxuLy8gdGhyb3VnaCBhIHJlZmVyZW5jZSAoUkZDLTAwNzEgXHUwMGE3Ny4xKSwgc28gdGhlcmUgaXMgbmV2ZXIgYSByZXNpZHVhbCB0byBuYXJyb3cgdG9cbi8vIG9yIHdpZGVuIGZyb20gYmVoaW5kIG9uZSBcdTIwMTQgdGhpcyBydWxlIGlzIHVuY2hhbmdlZCBieSBSRkMtMDEzNy5cbi8vXG4vLyBOZWVkcyBtb3ZlX2NoZWNrID0gdHJ1ZTogdGhlIG1vdmUtb3V0LW9mLWEtcmVmZXJlbmNlIGJhbiBpcyBhIG1vdmUtY2hlY2tlclxuLy8gcnVsZSwgbm90IG9uZSBvZiB0aGUgYWx3YXlzLW9uIHR5cGVjaGVjayBydWxlcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBjb25zdW1lX25hbWUoaDogJnZhciBIYW5kbGUpIC0+IFN0cmluZyB7XG4gICAgbGV0IG4gOj0gaC5uYW1lOyAgIC8vIHJlamVjdGVkOiBtb3ZpbmcgYG5hbWVgIG91dCB0aHJvdWdoIGAmdmFyIEhhbmRsZWBcbiAgICBuXG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGZkID0gMSwgbmFtZSA9IFwieFwiIH07XG4gICAgcHJpbnRsbihjb25zdW1lX25hbWUoJnZhciBoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.ownership.widening.dynamics-1}

Assigning a value to a field missing from a residual's current row widens the residual's
type to include that field, at the same brand; once every moved-out field has been
reassigned the type is the plain struct again and the value may be used as a whole
([partial-moves.legality-3](#spec.ownership.partial-moves.legality-3)).

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).** For an owned binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwNV93aWRlbmluZ19yZWFzc2lnbl9yZXN0b3Jlc19mdWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogYXNzaWduaW5nIGEgdmFsdWUgdG8gYSBmaWVsZCBtaXNzaW5nIGZyb20gYVxuLy8gcmVzaWR1YWwncyByb3cgd2lkZW5zIHRoZSByZXNpZHVhbCdzIHR5cGUgYmFjayB0byB0aGUgd2hvbGUgYnJhbmRcbi8vIChzcGVjLm93bmVyc2hpcC53aWRlbmluZy5keW5hbWljcy0xKS4gT25seSBmb3IgYW4gb3duZWQgYmluZGluZzsgd2lkZW5pbmcgZG9lc1xuLy8gbm90IHJlLWNoZWNrIGFueSBjb25zdHJ1Y3RvciBpbnZhcmlhbnQuIFdpdGggYC0tbW92ZS1jaGVja2Agb24sIHRoZSB3aWRlbmVkXG4vLyBiaW5kaW5nIGlzIHdob2xlIGFnYWluIC0tIGEgYnktdmFsdWUgdXNlIGlzIGEgY2xlYW4gbW92ZSwgbm90IGEgcGFydGlhbC1tb3ZlXG4vLyB2aW9sYXRpb24uXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gd2FudHNfZnVsbChoOiBIYW5kbGUpIC0+IGk2NCB7IGguZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgaCA6PSBIYW5kbGUgeyBmZCA9IDUsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBoLm5hbWUgOj0gXCJ5XCI7ICAgICAgICAgICAgICAgICAgICAgLy8gd2lkZW5zIGJhY2s6IGggOiBIYW5kbGVcbiAgICBhc3NlcnQoaC5uYW1lID09IFwieVwiKTsgICAgICAgICAgICAgLy8gc2libGluZyByZWFkYWJsZSBhdCB0aGUgd2lkZW5lZCB0eXBlXG4gICAgYXNzZXJ0KHdhbnRzX2Z1bGwoaCkgPT0gNSk7ICAgICAgICAvLyB3aG9sZSBgSGFuZGxlYCBtb3ZlZCBpbiwgb25jZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDVfd2lkZW5pbmdfcmVhc3NpZ25fcmVzdG9yZXNfZnVsbC5tdGwiLCJuYW1lIjoiMTA1X3dpZGVuaW5nX3JlYXNzaWduX3Jlc3RvcmVzX2Z1bGwubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## References and moves

`&T` is `Copy`, so a shared reference is duplicated on use and the original stays valid.

`&var T` is **not** `Copy` — an exclusive reference must stay unique to be exclusive. It is
therefore moved on use, with one exception:

> **Availability:** Since v0.12.0 (RFC-0071), behind `--move-check`. Passing a `&var T`
> as an argument to a parameter of type `&var T` reborrows it rather than moving it —
> the original binding remains usable after the call. Every other use moves.

```metel
struct Counter { n: i64 }

fun bump(r: &var Counter) { }

fun main() {
    var c := Counter { n = 0 };
    let r := &var c;
    bump(r);
    bump(r);      // fine — each call reborrows

    let q := r;    // moves: plain binding is not a reborrow
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6Im5vbi1yZWJvcnJvdyB1c2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIxMF9tdXRfcmVmX25vbl9yZWJvcnJvd19tb3ZlLm10bCIsInNvdXJjZSI6InN0cnVjdCBDb3VudGVyIHtcbiAgICB2YWx1ZTogaTY0LFxufVxuXG5mdW4gYnVtcChyOiAmdmFyIENvdW50ZXIpIHsgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgYyA6PSBDb3VudGVyIHsgdmFsdWUgPSAwIH07XG4gICAgbGV0IHIgOj0gJnZhciBjO1xuICAgIGxldCBxIDo9IHI7XG4gICAgYnVtcChyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMTBfbXV0X3JlZl9ub25fcmVib3Jyb3dfbW92ZS5tdGwiLCJuYW1lIjoiMTBfbXV0X3JlZl9ub25fcmVib3Jyb3dfbW92ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnApYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI0OF9tb3ZlX3Rocm91Z2hfZXhwbGljaXRfZGVyZWZfaXNfYmFubmVkX29uX2ZpcnN0X3VzZS5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ4OiBhIHNoYXJlZCByZWZlcmVuY2Ugb25seSBldmVyIGdyYW50cyBhY2Nlc3MsIG5ldmVyIG93bmVyc2hpcCAoUkZDLTAwNzFcbi8vIFNTNy4xKSAtLSBtb3ZpbmcgYFN0cmluZ2AgKG5vbi1Db3B5KSBvdXQgb2YgYCpwYCBpcyBpbGxlZ2FsIG9uIHRoZSAqZmlyc3QqXG4vLyBjYWxsLCBub3QganVzdCBhIHJlcGVhdGVkIG9uZS4gQmVmb3JlICM2NDggdGhpcyBjb21waWxlZCBhbmQgb25seSB0aGVcbi8vIHNlY29uZCBgZWF0KCpwKWAgd2FzIHJlamVjdGVkLCBhcyBhbiBvcmRpbmFyeSB1c2UtYWZ0ZXItbW92ZSAtLSB0aGUgd3Jvbmdcbi8vIGRpYWdub3Npcywgc2luY2UgdGhlIGZpcnN0IG1vdmUgd2FzIG5ldmVyIGxlZ2FsIHRvIGJlZ2luIHdpdGguXG5mdW4gZWF0KHM6IFN0cmluZykgLT4gaTY0IHsgMSB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFwiaGVsbG9cIjtcbiAgICBsZXQgcCA6PSAmcztcbiAgICBsZXQgZmlyc3QgOj0gZWF0KCpwKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNDhfbW92ZV90aHJvdWdoX2V4cGxpY2l0X2RlcmVmX2lzX2Jhbm5lZF9vbl9maXJzdF91c2UubXRsIiwibmFtZSI6IjQ4X21vdmVfdGhyb3VnaF9leHBsaWNpdF9kZXJlZl9pc19iYW5uZWRfb25fZmlyc3RfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnIpYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI2NV9nZW5lcmFsX2Fzc2lnbm1lbnRfb3V0X29mX2FuX2V4cGxpY2l0X2RlcmVmX2lzX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Ii8vICM2NDgsIFJGQy0wMDcxIFNTNy4xJ3Mgb3duIG5hbWVkIGV4YW1wbGU6IGBsZXQgeDogQiA9ICpyO2AuXG5zdHJ1Y3QgQiB7IHY6IFN0cmluZyB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBiIDo9IEIgeyB2ID0gXCJ4XCIgfTtcbiAgICBsZXQgciA6PSAmYjtcbiAgICBsZXQgeDogQiA6PSAqcjtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNjVfZ2VuZXJhbF9hc3NpZ25tZW50X291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJuYW1lIjoiNjVfZ2VuZXJhbF9hc3NpZ25tZW50X291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnIpYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI2Nl9ieV92YWx1ZV9hcmd1bWVudF9wYXNzaW5nX291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ4LCBSRkMtMDA3MSBTUzcuMSdzIG90aGVyIG5hbWVkIGV4YW1wbGU6IGBmKCpyKWAuXG5zdHJ1Y3QgQiB7IHY6IFN0cmluZyB9XG5cbmZ1biB0YWtlcyhiOiBCKSAtPiBTdHJpbmcge1xuICAgIGIudlxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYiA6PSBCIHsgdiA9IFwieFwiIH07XG4gICAgbGV0IHIgOj0gJmI7XG4gICAgbGV0IG4gOj0gdGFrZXMoKnIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay82Nl9ieV92YWx1ZV9hcmd1bWVudF9wYXNzaW5nX291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJuYW1lIjoiNjZfYnlfdmFsdWVfYXJndW1lbnRfcGFzc2luZ19vdXRfb2ZfYW5fZXhwbGljaXRfZGVyZWZfaXNfcmVqZWN0ZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjcwX3NoYXJlZF9yZWZlcmVuY2VfaXNfY29weS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTc5YSBpdGVtIDE6IGAmVGAgaXMgYENvcHlgIChhIHNoYXJlZCByZWZlcmVuY2UgbWF5IGJlIHVzZWRcbi8vIHJlcGVhdGVkbHkpOyBgJnZhciBUYCBpcyBub3QgKHNlZSAxMF9tdXRfcmVmX25vbl9yZWJvcnJvd19tb3ZlLm10bCBmb3IgdGhlXG4vLyBuZWdhdGl2ZSBoYWxmIC0tIG1vdmluZyBhIGAmdmFyIFRgIGJpbmRpbmcgYW5kIHRoZW4gdXNpbmcgaXQgYWdhaW4gaXNcbi8vIHJlamVjdGVkKS5cbmZ1biBzaG93KHI6ICZpNjQpIC0+IGk2NCB7ICpyIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHggOj0gNTtcbiAgICBsZXQgciA6PSAmeDtcbiAgICBhc3NlcnQoc2hvdyhyKSA9PSA1KTtcbiAgICBhc3NlcnQoc2hvdyhyKSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNzBfc2hhcmVkX3JlZmVyZW5jZV9pc19jb3B5Lm10bCIsIm5hbWUiOiI3MF9zaGFyZWRfcmVmZXJlbmNlX2lzX2NvcHkubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InJlZmVyZW5jZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBuYXJyb3dpbmcgYW5kIHdpZGVuaW5nIGFwcGx5IG9ubHkgdG8gYW5cbi8vIG93bmVkIGJpbmRpbmcuIEEgbm9uLWBDb3B5YCBmaWVsZCBjYW5ub3QgYmUgbW92ZWQgb3V0IG9mIGEgdmFsdWUgcmVhY2hlZFxuLy8gdGhyb3VnaCBhIHJlZmVyZW5jZSAoUkZDLTAwNzEgXHUwMGE3Ny4xKSwgc28gdGhlcmUgaXMgbmV2ZXIgYSByZXNpZHVhbCB0byBuYXJyb3cgdG9cbi8vIG9yIHdpZGVuIGZyb20gYmVoaW5kIG9uZSBcdTIwMTQgdGhpcyBydWxlIGlzIHVuY2hhbmdlZCBieSBSRkMtMDEzNy5cbi8vXG4vLyBOZWVkcyBtb3ZlX2NoZWNrID0gdHJ1ZTogdGhlIG1vdmUtb3V0LW9mLWEtcmVmZXJlbmNlIGJhbiBpcyBhIG1vdmUtY2hlY2tlclxuLy8gcnVsZSwgbm90IG9uZSBvZiB0aGUgYWx3YXlzLW9uIHR5cGVjaGVjayBydWxlcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBjb25zdW1lX25hbWUoaDogJnZhciBIYW5kbGUpIC0+IFN0cmluZyB7XG4gICAgbGV0IG4gOj0gaC5uYW1lOyAgIC8vIHJlamVjdGVkOiBtb3ZpbmcgYG5hbWVgIG91dCB0aHJvdWdoIGAmdmFyIEhhbmRsZWBcbiAgICBuXG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGZkID0gMSwgbmFtZSA9IFwieFwiIH07XG4gICAgcHJpbnRsbihjb25zdW1lX25hbWUoJnZhciBoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIn0="></details>
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
