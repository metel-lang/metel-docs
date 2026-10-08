---
title: "Ownership and Move Semantics"
---

# Ownership and Move Semantics

> **Availability:** Since v0.12.0, whole-binding move checking is opt-in via `--move-check`.

Whole-binding use-after-move checking is enabled by the opt-in `--move-check` flag.
Without it, reusing a binding moved as a whole is not rejected. Row narrowing and
widening are ordinary type-checking rules and apply independently of that flag:
reading a removed field or requiring a wider row is rejected in either mode.
The flag remains off by default; enabling it also enforces ownership restrictions
that are not expressed by row types.

## Values move by default

A value whose type is not `Copy` has exactly one owner at any point. Assigning it, passing it
as an argument, or returning it **moves** it: ownership transfers, and the source binding
becomes invalid.

```metel
struct Buffer { data: [i64] }

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

<!-- rfc.py:last_reviewed 8ed18533e08f605e0df6c188f1d30797fb72171f -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgc2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMV9tb3ZlX3RoZW5fdXNlLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFwiaGVsbG9cIjtcbiAgICBsZXQgbW92ZWQgOj0gcztcbiAgICBsZXQgYWdhaW4gOj0gcztcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDFfbW92ZV90aGVuX3VzZS5tdGwiLCJuYW1lIjoiMDFfbW92ZV90aGVuX3VzZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgcmAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJnZW5lcmljX3Jvd19mb3J3YXJkaW5nX21vdmVzX3Vua25vd25fdGFpbC5tdGwiLCJzb3VyY2UiOiJmdW4gYWRkPHJvdyBSOiAhe3Rva2VufT4ocjogeyAuLlIgfSkgLT4geyB0b2tlbjogU3RyaW5nLCAuLlIgfSB7XG4gICAgeyAuLnIsIHRva2VuID0gXCJzZWNyZXRcIiB9XG59XG5cbmZ1biBmb3J3YXJkPHJvdyBSOiAhe3Rva2VufT4ocjogeyAuLlIgfSkgLT4gaTY0IHtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW3JdIG9uY2UgfHwge1xuICAgICAgICBsZXQgYWRkZWQgOj0gYWRkKHIpO1xuICAgICAgICBsZXQgYWdhaW4gOj0gcjsgLy8gRVJST1JbVDAwMTldXG4gICAgICAgIDdcbiAgICB9O1xuICAgIGNhbGxiYWNrKClcbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay9nZW5lcmljX3Jvd19mb3J3YXJkaW5nX21vdmVzX3Vua25vd25fdGFpbC5tdGwiLCJuYW1lIjoiZ2VuZXJpY19yb3dfZm9yd2FyZGluZ19tb3Zlc191bmtub3duX3RhaWwubXRsIn0="></details>
</details>
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

<!-- rfc.py:last_reviewed e8fbf1d25144c7627a2a8ac357de96f7fb8a8509 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk2X2NvcHlfZWxpZ2liaWxpdHlfc2Vlc19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTcyIGBDb3B5YCBlbGlnaWJpbGl0eSB0aHJvdWdoIGEgKmdlbmVyaWMqIGZpZWxkIHR5cGUgd2hvc2Ugb3duXG4vLyBgQ29weWAgaW1wbCBpcyBjb25kaXRpb25hbCAoaXNzdWUgIzMwMykuXG4vL1xuLy8gRGVjaWRpbmcgYGV4dGVuZDxUOiBDb3B5PiBPdXRlcjxUPjogQ29weWAgbWVhbnMgYW5zd2VyaW5nIHdoZXRoZXIgdGhlIGZpZWxkXG4vLyB0eXBlIGBJbm5lcjxUPmAgaXMgYENvcHlgIFx1MjAxNCBhIHF1ZXN0aW9uIHdpdGggbm8gYW5zd2VyIGluIHRlcm1zIG9mIGNvbmNyZXRlXG4vLyB0eXBlcywgc2luY2UgYFRgIGlzIG5vdCBvbmUuIEl0IGlzIGFuc3dlcmFibGUgdW5kZXIgdGhlIGltcGwncyBvd24gYm91bmRzOlxuLy8gYFRgIGlzIGFzc3VtZWQgYENvcHlgLCB3aGljaCBkaXNjaGFyZ2VzIHRoZSBib3VuZCBvbiBgSW5uZXJgJ3MgY29uZGl0aW9uYWxcbi8vIGltcGwuIFRoZSBlbGlnaWJpbGl0eSBjaGVjayB1c2VkIHRvIGdpdmUgdXAgaGVyZSBhbmQgcmVqZWN0IHRoZSBwcm9ncmFtLlxuXG5zdHJ1Y3QgSW5uZXI8VD4ge1xuICAgIHZhbHVlOiBULFxufVxuXG5leHRlbmQ8VDogQ29weT4gSW5uZXI8VD46IENvcHk7XG5cbnN0cnVjdCBPdXRlcjxUPiB7XG4gICAgaW5uZXI6IElubmVyPFQ+LFxufVxuXG5leHRlbmQ8VDogQ29weT4gT3V0ZXI8VD46IENvcHk7XG5cbi8vIFRoZSBzYW1lIHNoYXBlIHdpdGggdGhlIGJvdW5kIGluIGEgYHdoZXJlYCBjbGF1c2UgcmF0aGVyIHRoYW4gaW5saW5lLlxuc3RydWN0IFdyYXBwZWQ8VD4ge1xuICAgIGhlbGQ6IElubmVyPFQ+LFxufVxuXG5leHRlbmQ8VD4gV3JhcHBlZDxUPjogQ29weSB3aGVyZSBUOiBDb3B5O1xuXG4vLyBBbmQgdGhyb3VnaCBhbiBlbnVtIHBheWxvYWQsIHdoaWNoIHRha2VzIHRoZSBvdGhlciBicmFuY2ggb2YgdGhlIGNoZWNrLlxuZW51bSBIZWxkPFQ+IHtcbiAgICBPbmUgeyB2YWx1ZTogSW5uZXI8VD4gfSxcbiAgICBOb25lLFxufVxuXG5leHRlbmQ8VDogQ29weT4gSGVsZDxUPjogQ29weTtcblxuZnVuIGlkPFQ6IENvcHk+KHg6IFQpIC0+IFQge1xuICAgIHJldHVybiB4O1xufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgbyA6PSBPdXRlciB7IGlubmVyID0gSW5uZXIgeyB2YWx1ZSA9IDEgfSB9O1xuICAgIGxldCBjb3BpZWQgOj0gaWQobyk7XG4gICAgYXNzZXJ0KGNvcGllZC5pbm5lci52YWx1ZSA9PSAxKTtcblxuICAgIGxldCB3IDo9IFdyYXBwZWQgeyBoZWxkID0gSW5uZXIgeyB2YWx1ZSA9IDIgfSB9O1xuICAgIGxldCB3X2NvcGllZCA6PSBpZCh3KTtcbiAgICBhc3NlcnQod19jb3BpZWQuaGVsZC52YWx1ZSA9PSAyKTtcblxuICAgIGxldCBoIDo9IEhlbGQ6Ok9uZSB7IHZhbHVlID0gSW5uZXIgeyB2YWx1ZSA9IDMgfSB9O1xuICAgIGxldCBoX2NvcGllZCA6PSBpZChoKTtcbiAgICBtYXRjaCAoaF9jb3BpZWQpIHtcbiAgICAgICAgSGVsZDo6T25lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUudmFsdWUgPT0gMyksXG4gICAgICAgIEhlbGQ6Ok5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzk2X2NvcHlfZWxpZ2liaWxpdHlfc2Vlc19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJuYW1lIjoiOTZfY29weV9lbGlnaWJpbGl0eV9zZWVzX2NvbmRpdGlvbmFsX2ltcGxzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## `Drop`

> **Limitation** LIMIT-EVALUATION-005

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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3BhcnRpYWxfbW92ZV9vZl9kcm9wX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IEhhbmRsZSB7XG4gICAgbmFtZTogU3RyaW5nLFxuICAgIGZkOiBpNjQsXG59XG5cbmV4dGVuZCBIYW5kbGU6IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikgeyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgbmFtZSA9IFwieFwiLCBmZCA9IDEgfTtcbiAgICBsZXQgbmFtZSA6PSBoYW5kbGUubmFtZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwiLCJuYW1lIjoiMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwifQ=="></details>
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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDcxIFx1MDBhNzQgZm9yYmlkcyBvbmUgKnR5cGUqIGhhdmluZyBib3RoIGBDb3B5YCBhbmQgYERyb3BgLiBJdCBkb2VzIG5vdFxuLy8gZm9yYmlkIGEgcHJvZ3JhbSBmcm9tIGNvbnRhaW5pbmcgYW4gaW1wbCBvZiBlYWNoLCBhbmQgdGhlIGNoZWNrIGFkZGVkIGZvclxuLy8gaXNzdWUgIzMwMiBpcyBkZWxpYmVyYXRlbHkgcHJlY2lzZSBhYm91dCB0aGUgZGlmZmVyZW5jZSBcdTIwMTQgYW4gYXBwcm94aW1hdGlvblxuLy8gdGhhdCByZWplY3RlZCBhbnkgYENvcHlgIGltcGwgYW5kIGBEcm9wYCBpbXBsIHNoYXJpbmcgYSB0YXJnZXQgY29uc3RydWN0b3Jcbi8vIHdvdWxkIHJlamVjdCBib3RoIGhhbHZlcyBvZiB0aGlzIGZpbGUuXG4vL1xuLy8gVHdvIHdheXMgdGhlIHR3byBpbXBscyBjYW4gY29leGlzdDpcblxuc3RydWN0IERpc2pvaW50PFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbi8vIDEuIFByb3ZhYmx5IGRpc2pvaW50IGJvdW5kcy4gTm8gYFRgIGlzIGJvdGggYENvcHlgIGFuZCBgIUNvcHlgLCBzbyBub1xuLy8gICAgaW5zdGFudGlhdGlvbiBvZiBgRGlzam9pbnQ8VD5gIGV2ZXIgaGFzIGJvdGggYXNwZWN0cy5cbmV4dGVuZDxUOiBDb3B5PiBEaXNqb2ludDxUPjogQ29weTtcblxuZXh0ZW5kPFQ6ICFDb3B5PiBEaXNqb2ludDxUPjogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnZhciBzZWxmKSB7fVxufVxuXG5zdHJ1Y3QgUmVhY2g8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuLy8gMi4gQSBjb25jcmV0ZSB0YXJnZXQgb3V0c2lkZSB0aGUgYmxhbmtldCdzIHJlYWNoLiBgU3RyaW5nYCBpcyBub3QgYENvcHlgLFxuLy8gICAgc28gdGhlIGJsYW5rZXQgZG9lcyBub3QgYXBwbHkgdG8gYFJlYWNoPFN0cmluZz5gIGFuZCBpdCBpcyBmcmVlIHRvXG4vLyAgICBpbXBsZW1lbnQgYERyb3BgLiBXaXRoIGBpNjRgIGhlcmUgaW5zdGVhZCB0aGlzIGlzIGEgXHUwMGE3NCB2aW9sYXRpb24gXHUyMDE0XG4vLyAgICBzZWUgYHR5cGVjaGVja2luZy9zdHJ1Y3RzL3N0YWdlNV9uZWdfMzVfY29weV9ibGFua2V0X3JlYWNoZXNfZHJvcF9pbnN0YW50aWF0aW9uLm10bGAuXG5leHRlbmQ8VDogQ29weT4gUmVhY2g8VD46IENvcHk7XG5cbmV4dGVuZCBSZWFjaDxTdHJpbmc+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb3B5YWJsZSA6PSBEaXNqb2ludCB7IHZhbCA9IDEgfTtcbiAgICBhc3NlcnQoY29weWFibGUudmFsID09IDEpO1xuXG4gICAgbGV0IGRyb3BwYWJsZSA6PSBEaXNqb2ludCB7IHZhbCA9IFwib3duZWRcIiB9O1xuICAgIGFzc2VydCgoJmRyb3BwYWJsZS52YWwpLmxlbigpID09IDUpO1xuXG4gICAgbGV0IHJlYWNoZWQgOj0gUmVhY2ggeyB2YWwgPSA3IH07XG4gICAgYXNzZXJ0KHJlYWNoZWQudmFsID09IDcpO1xuXG4gICAgbGV0IHVucmVhY2hlZCA6PSBSZWFjaCB7IHZhbCA9IFwib3V0c2lkZVwiIH07XG4gICAgYXNzZXJ0KCgmdW5yZWFjaGVkLnZhbCkubGVuKCkgPT0gNyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bCIsIm5hbWUiOiI5NV9jb3B5X2FuZF9kcm9wX25vbl9vdmVybGFwcGluZ19pbXBscy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBpbXBsZW1lbnQgYm90aCBgQ29weWAgYW5kIGBEcm9wYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV9uZWdfMzRfY29weV9hbmRfZHJvcF9vdmVybGFwcGluZ19jb25kaXRpb25hbF9pbXBscy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTc0IGFjcm9zcyB0d28gKmNvbmRpdGlvbmFsKiBpbXBscyAoaXNzdWUgIzMwMikuXG4vL1xuLy8gTmVpdGhlciBpbXBsIHRhcmdldCBpcyBjbG9zZWQsIHNvIHRoZSBkZWNsYXJhdGlvbi1zaXRlIGNoZWNrIGluXG4vLyBgdHlwZWNoZWNrZXI6OmluZmVyZW5jZWAgY2Fubm90IGV2YWx1YXRlIGVpdGhlciBvbmUgXHUyMDE0IGl0IGlzIGBjb2hlcmVuY2VgJ3Ncbi8vIGNyb3NzLWFzcGVjdCBvdmVybGFwIGNoZWNrIHRoYXQgcmVqZWN0cyB0aGlzLiBUaGUgYm91bmRzIGFyZSBub3QgZGlzam9pbnQ6XG4vLyBgaTY0YCBpcyBib3RoIGBDb3B5YCBhbmQgYERpc3BsYXlgLCBzbyBgT3ZlcmxhcDxpNjQ+YCB3b3VsZCBoYXZlIGJvdGhcbi8vIGFzcGVjdHMsIHdoaWNoIFx1MDBhNzQgZm9yYmlkcy5cblxuc3RydWN0IE92ZXJsYXA8VD4ge1xuICAgIHZhbDogVCxcbn1cblxuZXh0ZW5kPFQ6IENvcHk+IE92ZXJsYXA8VD46IENvcHk7XG5cbmV4dGVuZDxUOiBEaXNwbGF5PiBPdmVybGFwPFQ+OiBEcm9wIHtcbiAgICBmdW4gZHJvcCgmdmFyIHNlbGYpIHt9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1X25lZ18zNF9jb3B5X2FuZF9kcm9wX292ZXJsYXBwaW5nX2NvbmRpdGlvbmFsX2ltcGxzLm10bCIsIm5hbWUiOiJzdGFnZTVfbmVnXzM0X2NvcHlfYW5kX2Ryb3Bfb3ZlcmxhcHBpbmdfY29uZGl0aW9uYWxfaW1wbHMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBpbXBsZW1lbnQgYm90aCBgQ29weWAgYW5kIGBEcm9wYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV9uZWdfMzVfY29weV9ibGFua2V0X3JlYWNoZXNfZHJvcF9pbnN0YW50aWF0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDcxIFx1MDBhNzQgd2hlcmUgYSBgQ29weWAgYmxhbmtldCBhbmQgYSBjb25jcmV0ZSBgRHJvcGAgaW1wbCBtZWV0IGF0IG9uZVxuLy8gaW5zdGFudGlhdGlvbiAoaXNzdWUgIzMwMikuXG4vL1xuLy8gYGk2NGAgaXMgYENvcHlgLCBzbyB0aGUgYmxhbmtldCByZWFjaGVzIGBSZWFjaDxpNjQ+YCBcdTIwMTQgdGhlIGV4YWN0IHR5cGUgdGhlXG4vLyBgRHJvcGAgaW1wbCB0YXJnZXRzLiBDb250cmFzdCB0aGUgYWNjZXB0ZWQgY2FzZSBpblxuLy8gYGV2YWx1YXRvci9zdHJ1Y3RzLzk1X2NvcHlfYW5kX2Ryb3Bfbm9uX292ZXJsYXBwaW5nX2ltcGxzLm10bGAsIHdoaWNoIGlzXG4vLyB0aGlzIHByb2dyYW0gd2l0aCBgU3RyaW5nYCBpbiBwbGFjZSBvZiBgaTY0YDogdGhlIHJlamVjdGlvbiB0dXJucyBvblxuLy8gd2hldGhlciB0aGUgY29uY3JldGUgYXJndW1lbnQgc2F0aXNmaWVzIHRoZSBibGFua2V0J3MgYm91bmQsIG5vdCBvbiB0aGVcbi8vIHR3byBpbXBscyBtZXJlbHkgc2hhcmluZyBhIHRhcmdldCBjb25zdHJ1Y3Rvci5cblxuc3RydWN0IFJlYWNoPFQ+IHtcbiAgICB2YWw6IFQsXG59XG5cbmV4dGVuZDxUOiBDb3B5PiBSZWFjaDxUPjogQ29weTtcblxuZXh0ZW5kIFJlYWNoPGk2ND46IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikge31cbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvc3RydWN0cy9zdGFnZTVfbmVnXzM1X2NvcHlfYmxhbmtldF9yZWFjaGVzX2Ryb3BfaW5zdGFudGlhdGlvbi5tdGwiLCJuYW1lIjoic3RhZ2U1X25lZ18zNV9jb3B5X2JsYW5rZXRfcmVhY2hlc19kcm9wX2luc3RhbnRpYXRpb24ubXRsIn0="></details>
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

<!-- rfc.py:exemption kind="blocked" ref="metel-core#261" reason="Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until implementation issue #261 (drop order and explicit drop, RFC-0071 3/4) lands. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#261: Destructor invocation and drop order are not implemented yet -- non-empty Drop bodies are intentionally rejected until implementation issue #261 (drop order and explicit drop, RFC-0071 3/4) lands. Verified directly: the interpreter has no drop-at-scope-end mechanism to observe order against._</span>
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

Moving a field out of a struct leaves the containing value **partially moved**. The remaining
fields stay accessible; the original whole type is no longer available, but the residual
may be used as a whole at its current type. Since v0.13.0 (RFC-0137) the residual
also gets a named type — `Handle` becomes `Handle.{ fd }`, not just internal bookkeeping;
see [Narrowing](#narrowing) below.

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
containing value may not be used at its original whole type. A whole-value use at
its narrowed residual type, including an empty residual, is legal.

<!-- rfc.py:last_reviewed 1287040bb6508c79615a1805bbd3a9feaa4c20ba -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgUGFpcmAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7XG4gICAgbGVmdDogU3RyaW5nLFxuICAgIHJpZ2h0OiBpNjQsXG59XG5cbmZ1biB0YWtlKHBhaXI6IFBhaXIpIC0+IGk2NCB7XG4gICAgcGFpci5yaWdodFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHBhaXIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHBhaXIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJuYW1lIjoiMDJfcGFydGlhbF9tb3ZlX3VzZWRfYXNfd2hvbGUubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-2}

A field of a `Drop` type may not be moved out.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3BhcnRpYWxfbW92ZV9vZl9kcm9wX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IEhhbmRsZSB7XG4gICAgbmFtZTogU3RyaW5nLFxuICAgIGZkOiBpNjQsXG59XG5cbmV4dGVuZCBIYW5kbGU6IERyb3Age1xuICAgIGZ1biBkcm9wKCZ2YXIgc2VsZikgeyB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgbmFtZSA9IFwieFwiLCBmZCA9IDEgfTtcbiAgICBsZXQgbmFtZSA6PSBoYW5kbGUubmFtZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwiLCJuYW1lIjoiMDNfcGFydGlhbF9tb3ZlX29mX2Ryb3BfdHlwZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-3}

Assigning a value to a field that was moved out restores that field's own accessibility.
Once every field ever moved out of a value has been reassigned this way, the value's
whole-value status is restored too, and it may be used as a whole again; reassigning only
some of several moved-out fields is not enough.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIge1xuICAgIGxlZnQ6IFN0cmluZyxcbiAgICByaWdodDogU3RyaW5nLFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IFwiYlwiIH07XG4gICAgbGV0IHRha2VuIDo9IHAubGVmdDtcbiAgICBwLmxlZnQgOj0gXCJjXCI7XG4gICAgbGV0IHdob2xlIDo9IHA7XG4gICAgYXNzZXJ0KHRha2VuID09IFwiYVwiKTtcbiAgICBhc3NlcnQod2hvbGUubGVmdCA9PSBcImNcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIiwibmFtZSI6IjUxX2ZpZWxkX3JlYXNzaWdubWVudF9hZnRlcl9wYXJ0aWFsX21vdmVfaXNfdmFsaWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgVHdvYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVHdvIHtcbiAgICBsZWZ0OiBTdHJpbmcsXG4gICAgcmlnaHQ6IFN0cmluZyxcbn1cblxuZnVuIHRha2UodDogVHdvKSAtPiBpNjQge1xuICAgIHQubGVmdC5sZW4oKVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSBUd28geyBsZWZ0ID0gXCJhXCIsIHJpZ2h0ID0gXCJiXCIgfTtcbiAgICBsZXQgdGFrZW5fbGVmdCA6PSB0LmxlZnQ7XG4gICAgbGV0IHRha2VuX3JpZ2h0IDo9IHQucmlnaHQ7XG4gICAgdC5sZWZ0IDo9IFwiY1wiO1xuICAgIC8vIHQucmlnaHQgaXMgc3RpbGwgbW92ZWQgb3V0IC0tIHJlYXNzaWduaW5nIG9ubHkgb25lIG9mIHR3byBtb3ZlZCBmaWVsZHMgZG9lc1xuICAgIC8vIG5vdCByZXN0b3JlIHdob2xlLXZhbHVlIHN0YXR1czsgYHRgIHN0YXlzIHBhcnRpYWxseSBtb3ZlZC5cbiAgICBsZXQgbiA6PSB0YWtlKHQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83M19yZWFzc2lnbmluZ19vbmx5X29uZV9vZl90d29fbW92ZWRfZmllbGRzX3N0YXlzX3BhcnRpYWwubXRsIiwibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.legality-4}

Destructuring a struct or tuple with a pattern that binds a subset of its fields (a struct
pattern with `..`, a tuple pattern, a bound field of a matched variant's payload) moves
exactly those fields, leaving the scrutinee partially moved under the same rules as an
explicit field move — including the `Drop`-type ban ([legality-2](#spec.ownership.partial-moves.legality-2)).

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJlbG9uZ3MgdG8gYSBgRHJvcGAgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjE2X21hdGNoX2Ryb3BfZmllbGRfcGFydGlhbF9tb3ZlX2lzX2Jhbm5lZC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgSGFuZGxlIHtcbiAgICBuYW1lOiBTdHJpbmcsXG4gICAgZmQ6IGk2NCxcbn1cblxuZXh0ZW5kIEhhbmRsZTogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnZhciBzZWxmKSB7IH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGhhbmRsZSA6PSBIYW5kbGUgeyBuYW1lID0gXCJ4XCIsIGZkID0gMSB9O1xuICAgIGxldCBuIDo9IG1hdGNoIChoYW5kbGUubmFtZSkge1xuICAgICAgICBuYW1lID0+IG5hbWUubGVuKCksXG4gICAgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMTZfbWF0Y2hfZHJvcF9maWVsZF9wYXJ0aWFsX21vdmVfaXNfYmFubmVkLm10bCIsIm5hbWUiOiIxNl9tYXRjaF9kcm9wX2ZpZWxkX3BhcnRpYWxfbW92ZV9pc19iYW5uZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

> **Changed in v0.12.0 (RFC-0071), behind `--move-check`:** moving a field out of a `Drop`
> type is now rejected.

A `Drop` type may still be partially *borrowed*; only moving out is restricted.

> **Gap** GAP-OWNERSHIP-003: legality-2's ban is enforced unconditionally; see [Drop dispatch against a narrowed residual](#drop-dispatch-against-a-narrowed-residual).

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

<!-- rfc.py:last_reviewed 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImBwYWlyLjBgIHdhcyBtb3ZlZCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjA0X3R1cGxlX2VsZW1lbnRfbW92ZV90aGVuX3VzZS5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSAoXCJ4XCIsIDEpO1xuICAgIGxldCBsZWZ0IDo9IHBhaXIuMDtcbiAgICBsZXQgYWdhaW4gOj0gcGFpci4wO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wNF90dXBsZV9lbGVtZW50X21vdmVfdGhlbl91c2UubXRsIiwibmFtZSI6IjA0X3R1cGxlX2VsZW1lbnRfbW92ZV90aGVuX3VzZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgdmFsdWVgIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiMDVfZW51bV9wYXlsb2FkX2NvbnN1bWVzX3dob2xlX3ZhbHVlLm10bCIsInNvdXJjZSI6ImVudW0gTWF5YmVUZXh0IHtcbiAgICBFbXB0eSxcbiAgICBGdWxsIHsgdGV4dDogU3RyaW5nIH0sXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB2YWx1ZSA6PSBNYXliZVRleHQ6OkZ1bGwgeyB0ZXh0ID0gXCJ4XCIgfTtcbiAgICBsZXQgbiA6PSBtYXRjaCAodmFsdWUpIHtcbiAgICAgICAgTWF5YmVUZXh0OjpGdWxsIHsgdGV4dCB9ID0+IHRleHQubGVuKCksXG4gICAgICAgIE1heWJlVGV4dDo6RW1wdHkgPT4gMCxcbiAgICB9O1xuICAgIGxldCBhZ2FpbiA6PSB2YWx1ZTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMDVfZW51bV9wYXlsb2FkX2NvbnN1bWVzX3dob2xlX3ZhbHVlLm10bCIsIm5hbWUiOiIwNV9lbnVtX3BheWxvYWRfY29uc3VtZXNfd2hvbGVfdmFsdWUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImFycmF5IGVsZW1lbnQgbW92ZXMgYXJlIG5vdCBhbGxvd2VkIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiMDZfYXJyYXlfZWxlbWVudF9tb3ZlX2lzX2Jhbm5lZC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gW1wieFwiXTtcbiAgICBsZXQgZmlyc3QgOj0geHNbMF07XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzA2X2FycmF5X2VsZW1lbnRfbW92ZV9pc19iYW5uZWQubXRsIiwibmFtZSI6IjA2X2FycmF5X2VsZW1lbnRfbW92ZV9pc19iYW5uZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InVzZSBvZiBtb3ZlZCB2YWx1ZSBgc2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgbGV0IHMgOj0gXCJoZWxsb1wiO1xuICAgIGxldCBmIDo9IFtzXSBvbmNlIHx8IC0+IFN0cmluZyB7IHJldHVybiBzOyB9O1xuICAgIGxldCBhZ2FpbiA6PSBzO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wN19jbG9zdXJlX2NhcHR1cmVfb2Zfbm9uX2NvcHlfdmFsdWUubXRsIiwibmFtZSI6IjA3X2Nsb3N1cmVfY2FwdHVyZV9vZl9ub25fY29weV92YWx1ZS5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2}

Record fields may be moved independently, at field granularity like struct fields; a
moved field's siblings remain individually accessible. Using the record value at its
original wider type is rejected; whole-value use at its residual type is legal. Moving a field
**narrows the record's static type** to the fields that remain
([narrowing.legality-1](#spec.ownership.narrowing.legality-1), RFC-0117) — the same
mechanism struct narrowing uses, minus the brand.

<!-- rfc.py:last_reviewed 21aa4cd466b110a738a198b3ac9e2d6c6e555bc3 -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNl9yZWNvcmRfcm93X25hcnJvd2luZy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhbiBhbm9ueW1vdXNcbi8vIHJlY29yZCBuYXJyb3dzIHRoZSByZWNvcmQncyBzdGF0aWMgdHlwZSB0byB0aGUgZmllbGRzIHRoYXQgcmVtYWluIC0tIHRoZSBzYW1lXG4vLyBtZWNoYW5pc20gc3RydWN0IG5hcnJvd2luZyB1c2VzIChSRkMtMDEzNyksIG1pbnVzIHRoZSBicmFuZC4gVGhlIG5hcnJvd2VkXG4vLyByZWNvcmQgaXMgYW4gb3JkaW5hcnkgdmFsdWU6IGl0cyBzaWJsaW5ncyBzdGF5IHJlYWRhYmxlIGFuZCBpdCBmaXRzIGFcbi8vIHBhcmFtZXRlciB3aG9zZSByb3cgbWF0Y2hlcyBleGFjdGx5LlxuXG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImFcIi50b19zdHJpbmcoKSwgcmlnaHQgPSA3IH07XG4gICAgbGV0IHRha2VuIDo9IHIubGVmdDsgICAgICAgICAgICAgICAgIC8vIHIgOiB7IHJpZ2h0OiBpNjQgfSBmcm9tIGhlcmUgb25cbiAgICBhc3NlcnQoci5yaWdodCA9PSA3KTsgICAgICAgICAgICAgICAgLy8gc2libGluZyBzdGlsbCByZWFkYWJsZVxuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA3KTsgICAgICAgICAgICAvLyBleGFjdC1yb3cgcGFyYW1ldGVyIGFjY2VwdHMgdGhlIG5hcnJvd2VkIHJlY29yZFxuXG4gICAgLy8gQSBgQ29weWAgZmllbGQgcmVhZCBieSB2YWx1ZSBpcyBhIGNvcHksIG5vdCBhIG1vdmUgLS0gbm8gbmFycm93aW5nLlxuICAgIGxldCBwdCA6PSB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCB4X2NvcHkgOj0gcHQueDtcbiAgICBhc3NlcnQocHQueCArIHB0LnkgPT0gMyk7ICAgICAgICAgICAgLy8gcHQgaXMgc3RpbGwgdGhlIHdob2xlIHJlY29yZFxuICAgIGFzc2VydCh4X2NvcHkgPT0gMSk7XG5cbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTA2X3JlY29yZF9yb3dfbmFycm93aW5nLm10bCIsIm5hbWUiOiIxMDZfcmVjb3JkX3Jvd19uYXJyb3dpbmcubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjcxX3JlY29yZF9maWVsZF9tb3ZlZF9pbmRlcGVuZGVudGx5Lm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHIubGVmdDtcbiAgICBhc3NlcnQobGVmdCA9PSBcImFcIik7XG4gICAgYXNzZXJ0KHIucmlnaHQgPT0gMSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9tb3ZlX2NoZWNrLzcxX3JlY29yZF9maWVsZF9tb3ZlZF9pbmRlcGVuZGVudGx5Lm10bCIsIm5hbWUiOiI3MV9yZWNvcmRfZmllbGRfbW92ZWRfaW5kZXBlbmRlbnRseS5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

### Narrowing

Every `struct` is represented, for type-checking purposes, as a fixed nominal identity
(its **brand**, minted once at declaration) paired with its current **row** — the set of
fields still present.

> **Since v0.13.0 (RFC-0137, metel-core#857):** a struct's own field projection preserves
> its nominal brand.

`h.{ fd }` reads fields from a copy of the reference without consuming the original. It
produces a residual of `h`'s own brand, not a same-shaped anonymous record:

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

> **Since v0.13.0:** moving a field out of a value narrows its type.

For a **struct** (RFC-0137 slice 2, metel-core#858), `h.name` produces the same branded
residual type, `h.{ fd }`, as a projection does. For an **anonymous `record`** (RFC-0117,
metel-core#789), moving `r.left` out leaves `r : { right: i64 }`. Using the narrowed value
where the whole type or a wider row is required is a type error at type-check time, not only
a `--move-check` finding.

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

An anonymous record narrows in the same way, and reading the moved-out label is rejected:

<!-- doc-example: expect-fail reason="`left` was moved out, so the record no longer has it -- T0003 is the point" -->
```metel
fun main() {
    let r := { left = "l", right = "r" };
    let l := r.left;          // r : { right: String }
    println(r.right);         // fine: `right` is still present
    println(r.left);          // error: no field `left` on { right: String }
}
```

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

> **Gap** GAP-OWNERSHIP-002

> **Since v0.13.0.** Struct narrowing is RFC-0137 slice 2 (metel-core#858); anonymous-record
> narrowing is RFC-0117 (metel-core#789).

Moving a field out of a value narrows its type to a row with that field removed: a
same-brand residual for a struct, the record type minus that label for an anonymous
record. A `Copy` field read by value is a copy, not a move, and does not narrow; a field
of unresolved or generic type is held until its type is known. Narrowing is
path-sensitive, joined conservatively at merge points and loop fixpoints, matching move
tracking.

<!-- rfc.py:last_reviewed 17d5dadfd0dfe9ff1ad066cb15fa247db5f4eb2a -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0117](../../rfcs/4-implemented/rfc-0117-row-narrowing.md), [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (11)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNl9yZWNvcmRfcm93X25hcnJvd2luZy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhbiBhbm9ueW1vdXNcbi8vIHJlY29yZCBuYXJyb3dzIHRoZSByZWNvcmQncyBzdGF0aWMgdHlwZSB0byB0aGUgZmllbGRzIHRoYXQgcmVtYWluIC0tIHRoZSBzYW1lXG4vLyBtZWNoYW5pc20gc3RydWN0IG5hcnJvd2luZyB1c2VzIChSRkMtMDEzNyksIG1pbnVzIHRoZSBicmFuZC4gVGhlIG5hcnJvd2VkXG4vLyByZWNvcmQgaXMgYW4gb3JkaW5hcnkgdmFsdWU6IGl0cyBzaWJsaW5ncyBzdGF5IHJlYWRhYmxlIGFuZCBpdCBmaXRzIGFcbi8vIHBhcmFtZXRlciB3aG9zZSByb3cgbWF0Y2hlcyBleGFjdGx5LlxuXG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImFcIi50b19zdHJpbmcoKSwgcmlnaHQgPSA3IH07XG4gICAgbGV0IHRha2VuIDo9IHIubGVmdDsgICAgICAgICAgICAgICAgIC8vIHIgOiB7IHJpZ2h0OiBpNjQgfSBmcm9tIGhlcmUgb25cbiAgICBhc3NlcnQoci5yaWdodCA9PSA3KTsgICAgICAgICAgICAgICAgLy8gc2libGluZyBzdGlsbCByZWFkYWJsZVxuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA3KTsgICAgICAgICAgICAvLyBleGFjdC1yb3cgcGFyYW1ldGVyIGFjY2VwdHMgdGhlIG5hcnJvd2VkIHJlY29yZFxuXG4gICAgLy8gQSBgQ29weWAgZmllbGQgcmVhZCBieSB2YWx1ZSBpcyBhIGNvcHksIG5vdCBhIG1vdmUgLS0gbm8gbmFycm93aW5nLlxuICAgIGxldCBwdCA6PSB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCB4X2NvcHkgOj0gcHQueDtcbiAgICBhc3NlcnQocHQueCArIHB0LnkgPT0gMyk7ICAgICAgICAgICAgLy8gcHQgaXMgc3RpbGwgdGhlIHdob2xlIHJlY29yZFxuICAgIGFzc2VydCh4X2NvcHkgPT0gMSk7XG5cbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTA2X3JlY29yZF9yb3dfbmFycm93aW5nLm10bCIsIm5hbWUiOiIxMDZfcmVjb3JkX3Jvd19uYXJyb3dpbmcubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNyAvIFJGQy0wMTE3IChtZXRlbC1jb3JlIzk1MCk6IHdpdGggYC0tbW92ZS1jaGVja2Agb24sIGEgd2hvbGUtdmFsdWUgdXNlXG4vLyBvZiBhIGJpbmRpbmcgd2hvc2UgdHlwZSBoYXMgbmFycm93ZWQgdG8gYSByZXNpZHVhbCAvIG5hcnJvd2VyIHJlY29yZCBpcyBsZWdhbFxuLy8gLS0gbmFycm93aW5nIHJlbW92ZWQgZXhhY3RseSB0aGUgbW92ZWQgZmllbGRzLCBzbyB0aGUgdXNlIHRvdWNoZXMgbm9uZSBvZiB0aGVtLlxuLy8gQmVmb3JlICM5NTAsIGBtb3ZlX2NoZWNrYCBmbGFnZ2VkIGV2ZXJ5IHdob2xlLXZhbHVlIHVzZSBvZiBhIHBhcnRpYWxseS1tb3ZlZFxuLy8gYmluZGluZyByZWdhcmRsZXNzIG9mIGl0cyBjdXJyZW50IHR5cGUuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuZnVuIHRha2VfZmQoaDogSGFuZGxlLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBTdHJ1Y3Q6IG5hcnJvd2VkIHRvIEhhbmRsZS57IGZkIH0sIHRoZW4gbW92ZWQgaW4gYnkgdmFsdWUgb25jZS5cbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBobiA6PSBoLm5hbWU7XG4gICAgYXNzZXJ0KHRha2VfZmQoaCkgPT0gMyk7XG5cbiAgICAvLyBBbm9ueW1vdXMgcmVjb3JkOiBuYXJyb3dlZCB0byB7IHJpZ2h0OiBpNjQgfSwgdGhlbiBtb3ZlZCBpbiBieSB2YWx1ZSBvbmNlLlxuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDkgfTtcbiAgICBsZXQgcmwgOj0gci5sZWZ0O1xuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA5KTtcblxuICAgIC8vIEEgbmFycm93ZWQgYmluZGluZyByZWFkIChub3QgbW92ZWQpIGFzIGEgd2hvbGUgaXMgZmluZSB0b28uXG4gICAgbGV0IGcgOj0gSGFuZGxlIHsgZmQgPSA0LCBuYW1lID0gXCJ5XCIgfTtcbiAgICBsZXQgZ24gOj0gZy5uYW1lO1xuICAgIGxldCBhbGlhcyA6PSBnLnsgZmQgfTtcbiAgICBhc3NlcnQoYWxpYXMuZmQgPT0gNCk7XG5cbiAgICBwcmludGxuKFwiJHtobn0gJHtybH0gJHtnbn1cIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJuYW1lIjoiMTA3X21vdmVfY2hlY2tfbmFycm93ZWRfd2hvbGVfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogcm93LW5hcnJvd2luZyBtb3ZlIHN0YXRlIGlzIHBhdGgtc2Vuc2l0aXZlIGFjcm9zcyBgaWZgIGFybXMuXG4vLyBCb3RoIGFybXMgbW92ZSB0aGUgc2FtZSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBgcmVjYDsgdGhlIGBlbHNlYCBhcm0gZG9lc1xuLy8gbm90IHNlZSB0aGUgYHRoZW5gIGFybSdzIG1vdmUsIHNvIGVhY2ggaXMgYW4gaW5kZXBlbmRlbnQgcGFydGlhbCBtb3ZlLiBBZnRlclxuLy8gdGhlIGBpZmAgdGhlIGFybXMgam9pbjogYHJlY2AgaXMgbmFycm93ZWQgdG8gYHsga2VlcDogaTY0IH1gIG9uIGV2ZXJ5IHBhdGgsXG4vLyBpdHMgc3Vydml2aW5nIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgYSB3aG9sZS12YWx1ZSB1c2UgYXQgdGhlIG5hcnJvd2VkXG4vLyByb3cgaXMgYWNjZXB0ZWQgKGFsc28gdW5kZXIgLS1tb3ZlLWNoZWNrKS5cbmZ1biBrZWVwX29mKHI6IHsga2VlcDogaTY0IH0pIC0+IGk2NCB7IHIua2VlcCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb25kIDo9IHRydWU7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInhcIi50b19zdHJpbmcoKSwga2VlcCA9IDMgfTtcbiAgICBpZiAoY29uZCkge1xuICAgICAgICBsZXQgYSA6PSByZWMuZ29uZTtcbiAgICAgICAgYXNzZXJ0KGEgPT0gXCJ4XCIpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIGxldCBiIDo9IHJlYy5nb25lO1xuICAgICAgICBhc3NlcnQoYiA9PSBcInhcIik7XG4gICAgfVxuICAgIGFzc2VydChyZWMua2VlcCA9PSAzKTsgICAgICAgICAgLy8gc3Vydml2aW5nIGZpZWxkIHJlYWRhYmxlIGF0IHRoZSBqb2luZWQgcm93XG4gICAgYXNzZXJ0KGtlZXBfb2YocmVjKSA9PSAzKTsgICAgICAvLyB3aG9sZSB2YWx1ZSBmaXRzIHRoZSBuYXJyb3dlZCByb3dcbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJuYW1lIjoiMTEwX25hcnJvd2luZ19pZl9hcm1zX2luZGVwZW5kZW50Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExMV9uYXJyb3dpbmdfbWF0Y2hfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogdGhlIHNhbWUgcGVyLWFybSBmb3JrL2pvaW4gZm9yIGBtYXRjaGAuIFR3byBhcm1zIGVhY2ggbW92ZVxuLy8gdGhlIHNhbWUgbm9uLWBDb3B5YCBmaWVsZCBvZiBhbiBvdXRlciBiaW5kaW5nOyBhIGxhdGVyIGFybSBkb2VzIG5vdCBzZWUgYW5cbi8vIGVhcmxpZXIgYXJtJ3MgbW92ZS4gVGhlIGFybXMgam9pbiBhZnRlciB0aGUgYG1hdGNoYCwgbmFycm93aW5nIGByZWNgIHRvXG4vLyBgeyBrZWVwOiBpNjQgfWAuXG5mdW4ga2VlcF9vZihyOiB7IGtlZXA6IGk2NCB9KSAtPiBpNjQgeyByLmtlZXAgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgc2VsIDo9IDI7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInlcIi50b19zdHJpbmcoKSwga2VlcCA9IDcgfTtcbiAgICBsZXQgdGFnIDo9IG1hdGNoIChzZWwpIHtcbiAgICAgICAgMSA9PiB7IGxldCBhIDo9IHJlYy5nb25lOyAxMCB9LFxuICAgICAgICAyID0+IHsgbGV0IGIgOj0gcmVjLmdvbmU7IDIwIH0sXG4gICAgICAgIF8gPT4geyBsZXQgYyA6PSByZWMuZ29uZTsgMzAgfSxcbiAgICB9O1xuICAgIGFzc2VydCh0YWcgPT0gMjApO1xuICAgIGFzc2VydChyZWMua2VlcCA9PSA3KTtcbiAgICBhc3NlcnQoa2VlcF9vZihyZWMpID09IDcpO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTExX25hcnJvd2luZ19tYXRjaF9hcm1zX2luZGVwZW5kZW50Lm10bCIsIm5hbWUiOiIxMTFfbmFycm93aW5nX21hdGNoX2FybXNfaW5kZXBlbmRlbnQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjcyX3JlY29yZF91c2VkX2FzX3dob2xlX2FmdGVyX2ZpZWxkX21vdmUubXRsIiwic291cmNlIjoiZnVuIHRha2UocjogeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBpNjQgfSkgLT4gaTY0IHtcbiAgICByLnJpZ2h0XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83Ml9yZWNvcmRfdXNlZF9hc193aG9sZV9hZnRlcl9maWVsZF9tb3ZlLm10bCIsIm5hbWUiOiI3Ml9yZWNvcmRfdXNlZF9hc193aG9sZV9hZnRlcl9maWVsZF9tb3ZlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgVHdvYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVHdvIHtcbiAgICBsZWZ0OiBTdHJpbmcsXG4gICAgcmlnaHQ6IFN0cmluZyxcbn1cblxuZnVuIHRha2UodDogVHdvKSAtPiBpNjQge1xuICAgIHQubGVmdC5sZW4oKVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSBUd28geyBsZWZ0ID0gXCJhXCIsIHJpZ2h0ID0gXCJiXCIgfTtcbiAgICBsZXQgdGFrZW5fbGVmdCA6PSB0LmxlZnQ7XG4gICAgbGV0IHRha2VuX3JpZ2h0IDo9IHQucmlnaHQ7XG4gICAgdC5sZWZ0IDo9IFwiY1wiO1xuICAgIC8vIHQucmlnaHQgaXMgc3RpbGwgbW92ZWQgb3V0IC0tIHJlYXNzaWduaW5nIG9ubHkgb25lIG9mIHR3byBtb3ZlZCBmaWVsZHMgZG9lc1xuICAgIC8vIG5vdCByZXN0b3JlIHdob2xlLXZhbHVlIHN0YXR1czsgYHRgIHN0YXlzIHBhcnRpYWxseSBtb3ZlZC5cbiAgICBsZXQgbiA6PSB0YWtlKHQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay83M19yZWFzc2lnbmluZ19vbmx5X29uZV9vZl90d29fbW92ZWRfZmllbGRzX3N0YXlzX3BhcnRpYWwubXRsIiwibmFtZSI6IjczX3JlYXNzaWduaW5nX29ubHlfb25lX29mX3R3b19tb3ZlZF9maWVsZHNfc3RheXNfcGFydGlhbC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180OF9yZWNvcmRfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBvbmNlIGEgZmllbGQgaXMgbW92ZWQgb3V0IG9mIGFuIGFub255bW91cyByZWNvcmQsXG4vLyB0aGUgcmVjb3JkJ3MgdHlwZSBpcyB0aGUgbmFycm93ZXIgcm93IC0tIGB7IHJpZ2h0OiBpNjQgfWAsIG5vdCBgeyBsZWZ0LCByaWdodCB9YC5cbi8vIFBhc3NpbmcgaXQgd2hlcmUgdGhlIHdob2xlIHJlY29yZCBpcyByZXF1aXJlZCBpcyBhIHBsYWluIHR5cGUgZXJyb3IgYXRcbi8vIGluZmVyZW5jZSB0aW1lLCBubyBsb25nZXIgb25seSBhIGAtLW1vdmUtY2hlY2tgIGZpbmRpbmcuIEEgbmFycm93ZWQgcmVjb3JkIGhhc1xuLy8gbm8gZGlzdGluY3QgdHlwZSBtYXJrZXIsIHNvIHRoZSBkaWFnbm9zdGljIGlzIHRoZSBvcmRpbmFyeSByZWNvcmQtc2hhcGVcbi8vIG1pc21hdGNoLlxuXG5mdW4gd2FudHNfZnVsbChyOiB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IGk2NCB9KSAtPiBpNjQgeyByLnJpZ2h0IH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyBsZWZ0ID0gXCJhXCIudG9fc3RyaW5nKCksIHJpZ2h0ID0gMSB9O1xuICAgIGxldCB0YWtlbiA6PSByLmxlZnQ7XG4gICAgbGV0IF8gOj0gd2FudHNfZnVsbChyKTtcbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ4X3JlY29yZF93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDhfcmVjb3JkX3dob2xlX3VzZV9hZnRlcl9wYXJ0aWFsX21vdmUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjOTU4OiB0aGUgam9pbiBpcyB0aGUgKnVuaW9uKiBvZiB0aGUgYXJtcycgbW92ZXMuIE9ubHkgdGhlIGB0aGVuYFxuLy8gYXJtIG1vdmVzIGByZWMuZ29uZWA7IGFmdGVyIHRoZSBgaWZgLCBgcmVjYCBpcyBuYXJyb3dlZCB0byBgeyBrZWVwOiBpNjQgfWAgb25cbi8vIGV2ZXJ5IHBhdGggKHRoZSBtb3ZlIGlzIGpvaW5lZCBpbiBldmVuIHRob3VnaCB0aGUgYGVsc2VgIHBhdGggZGlkbid0IHJ1biBpdCksXG4vLyBzbyBhIHdob2xlLXZhbHVlIHVzZSBhdCB0aGUgd2lkZXIgcm93IGlzIHJlamVjdGVkLlxuZnVuIHdob2xlKHI6IHsgZ29uZTogU3RyaW5nLCBrZWVwOiBpNjQgfSkgLT4gaTY0IHsgci5rZWVwIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGNvbmQgOj0gdHJ1ZTtcbiAgICBsZXQgcmVjIDo9IHsgZ29uZSA9IFwielwiLnRvX3N0cmluZygpLCBrZWVwID0gMSB9O1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIGxldCBhIDo9IHJlYy5nb25lO1xuICAgIH1cbiAgICB3aG9sZShyZWMpICAgICAgICAgICAgICAvLyByZWMgOiB7IGtlZXA6IGk2NCB9IGhlcmUgLS0gd2lkZXIgcm93IHJlcXVpcmVkXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsIm5hbWUiOiJuZWdfNTBfbmFycm93aW5nX29uZV9hcm1fbW92ZV90YWludHNfam9pbi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzEzXzBfeF9tb3ZlX2NhcHR1cmVfb2ZfbmFycm93ZWRfc3RydWN0Lm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBjbG9zdXJlIGNhcHR1cmVcbi8vIChSRkMtMDE1NyBENSkgbWVldHMgbW92ZS10cmlnZ2VyZWQgc3RydWN0IHJvdyBuYXJyb3dpbmcgKFJGQy0wMTM3IHNsaWNlIDIpLlxuLy8gQSBub24tYENvcHlgIGZpZWxkIGlzIG1vdmVkIG91dCBmaXJzdCwgbmFycm93aW5nIGBoYCB0byBgSGFuZGxlLnsgZmQgfWA7IHRoZVxuLy8gY2xvc3VyZSB0aGVuIGNhcHR1cmVzIHRoZSAqbmFycm93ZWQqIHZhbHVlIGJ5IHZhbHVlLiBUaGUgY2FwdHVyZSBsaXN0IG5hbWVzXG4vLyBgaGAsIHRoZSByZXNpZHVhbCBtb3ZlcyBpbnRvIHRoZSBlbnZpcm9ubWVudCBvbmNlLCBhbmQgYC0tbW92ZS1jaGVja2AgaXNcbi8vIGNsZWFuIC0tIG5hcnJvd2luZyBhbHJlYWR5IHJlbW92ZWQgdGhlIGZpZWxkIHRoYXQgbGVmdC5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAvLyBoIDogSGFuZGxlLnsgZmQgfVxuICAgIGxldCBnZXQgOj0gW2hdIG9uY2UgfHwgeyBoLmZkIH07ICAgICAvLyBjYXB0dXJlcyB0aGUgcmVzaWR1YWwgYnkgdmFsdWVcbiAgICBhc3NlcnQoZ2V0KCkgPT0gNyk7XG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jbG9zdXJlcy92MF8xM18wX3hfbW92ZV9jYXB0dXJlX29mX25hcnJvd2VkX3N0cnVjdC5tdGwiLCJuYW1lIjoidjBfMTNfMF94X21vdmVfY2FwdHVyZV9vZl9uYXJyb3dlZF9zdHJ1Y3QubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzEzXzBfeF9zdHJ1Y3RfcGF0dGVybl9wYXJ0aWFsX21vdmVfbmFycm93cy5tdGwiLCJzb3VyY2UiOiIvLyBDcm9zcy1mZWF0dXJlICh2MC4xMy4wKTogYSBgbWF0Y2ggKGgpYCAoUkZDLTAxNTYgcGFyZW50aGVzaXplZCBzY3J1dGluZWUpIGJpbmRzXG4vLyBhIG5vbi1gQ29weWAgZmllbGQgb3V0IG9mIGEgc3RydWN0IHZhbHVlIHRocm91Z2ggYSBzdHJ1Y3QgcGF0dGVyblxuLy8gKG1ldGVsLWNvcmUjNzUzKS4gVGhhdCBwYXJ0aWFsIG1vdmUgbmFycm93cyBgaGAgKFJGQy0wMTM3IHNsaWNlIDIpOiB0aGUgbW92ZWRcbi8vIGZpZWxkIGlzIGdvbmUsIGV2ZXJ5IG90aGVyIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgcmVhc3NpZ25pbmcgdGhlIG1vdmVkXG4vLyBmaWVsZCB3aWRlbnMgYGhgIGJhY2sgdG8gdGhlIHdob2xlIHN0cnVjdC5cblxuc3RydWN0IEhhbmRsZSB7IGlkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGlkID0gNywgbmFtZSA9IFwiZmRcIi50b19zdHJpbmcoKSB9O1xuXG4gICAgLy8gYmluZCBhbmQgY29uc3VtZSBgbmFtZWAgdmlhIGEgc3RydWN0IHBhdHRlcm47IGBoYCBpcyBub3cgYEhhbmRsZS57IGlkIH1gXG4gICAgbGV0IHRha2VuIDo9IG1hdGNoIChoKSB7IEhhbmRsZSB7IG5hbWUsIC4uIH0gPT4gbmFtZSB9O1xuICAgIGFzc2VydCh0YWtlbiA9PSBcImZkXCIpO1xuXG4gICAgLy8gYSBzdGlsbC1wcmVzZW50IGZpZWxkIGlzIHJlYWRhYmxlIG9uIHRoZSBuYXJyb3dlZCB2YWx1ZVxuICAgIGFzc2VydChoLmlkID09IDcpO1xuXG4gICAgLy8gcmVhc3NpZ25pbmcgdGhlIG1vdmVkIGZpZWxkIHdpZGVucyBgaGAgYmFjayB0byB0aGUgd2hvbGUgYEhhbmRsZWBcbiAgICBoLm5hbWUgOj0gXCJmZDJcIi50b19zdHJpbmcoKTtcbiAgICBhc3NlcnQoaC5uYW1lID09IFwiZmQyXCIpO1xuICAgIGFzc2VydChoLmlkID09IDcpO1xuXG4gICAgcHJpbnRsbihcIm9rXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy92MF8xM18wX3hfc3RydWN0X3BhdHRlcm5fcGFydGlhbF9tb3ZlX25hcnJvd3MubXRsIiwibmFtZSI6InYwXzEzXzBfeF9zdHJ1Y3RfcGF0dGVybl9wYXJ0aWFsX21vdmVfbmFycm93cy5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-2}

A residual's row is never visible to structural matching; only its brand, fixed at
declaration, determines eligibility, regardless of how narrow or wide the current row is.

<!-- rfc.py:last_reviewed 00ea5182206865bc4268d46281bafb2767b73cad -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0117](../../rfcs/4-implemented/rfc-0117-row-narrowing.md), [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSk6IHRoaXMgaXMgdGhlIGFjdHVhbCBtb3RpdmF0aW5nIGJ1Z1xuLy8gLS0gU2VsZi57IGZkIH0gdXNlZCB0byBhY2NlcHQgYSBiYXJlIGFub255bW91cyByZWNvcmQgbGl0ZXJhbCBvZiB0aGUgc2FtZSBzaGFwZVxuLy8gZXhhY3RseSBhcyByZWFkaWx5IGFzIGEgdmFsdWUgYWN0dWFsbHkgZGVyaXZlZCBmcm9tIGEgcmVhbCBIYW5kbGUsIHNpbmNlIHRoZVxuLy8gcHJvamVjdGlvbiByZXNvbHZlZCB0byBhbiB1bmJyYW5kZWQgcmVjb3JkIHR5cGUuIE5vdyByZWplY3RlZDogYSBzdHJ1Y3QncyBvd25cbi8vIHByb2plY3Rpb24gaXMgYnJhbmRlZCwgYW5kIGEgc2FtZS1zaGFwZWQgYW5vbnltb3VzIHJlY29yZCBuZXZlciBjYXJyaWVzIHRoYXRcbi8vIGJyYW5kLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6IFNlbGYueyBmZCB9KSAtPiBpNjQgeyBoLmZkIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IF8gOj0gSGFuZGxlOjpkZXNjcmliZSh7IGZkID0gMyB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6InN0cnVjdCBuZXZlciBzYXRpc2ZpZXMgYSByb3cgYm91bmQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfNDVfcmVzaWR1YWxfbmV2ZXJfc2F0aXNmaWVzX3Jvd19ib3VuZC5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSk6IGEgZ2VudWluZSAobm9uLWZ1bGwtd2lkdGgpIGJyYW5kZWRcbi8vIHJlc2lkdWFsIG9mIGEgcGxhaW4gYHN0cnVjdGAgbmV2ZXIgc2F0aXNmaWVzIGEgcm93IGJvdW5kIGVpdGhlciAtLSBlbGlnaWJpbGl0eVxuLy8gZm9yIHN0cnVjdHVyYWwgbWF0Y2hpbmcgaXMgc2NvcGVkIHRvIHRoZSBicmFuZCBhbG9uZSAoUkZDLTAxMzcgc2VjMyksIGFuZCBhXG4vLyBgc3RydWN0YCdzIGJyYW5kIGlzIG5ldmVyIHZpc2libGUgdG8gbWF0Y2hpbmcgcmVnYXJkbGVzcyBvZiBob3cgbmFycm93IGl0c1xuLy8gY3VycmVudCByb3cgaXMuIEEgYHJlY29yZGAncyByZXNpZHVhbCBpcyBlbGlnaWJsZSAoUkZDLTAxMjAgc2VjMy9zZWMtZGVjbGFyYXRpb25zLVxuLy8gcmVjb3Jkcy1sZWdhbGl0eS0yKSAtLSB0aGF0IGlzIHRlc3RlZCBzZXBhcmF0ZWx5LCBub3QgYSBjb250cmFkaWN0aW9uIG9mIHRoaXMgb25lLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nLCBleHRyYTogaTY0IH1cblxuZnVuIHdhbnRzX2FfcmVjb3JkPHJlY29yZCBUOiB7IGZkOiBpNjQsIC4uIH0+KHQ6IFQpIC0+IGk2NCB7IHQuZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiwgZXh0cmEgPSA5IH07XG4gICAgbGV0IF8gOj0gd2FudHNfYV9yZWNvcmQoaC57IGZkIH0pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvc3RydWN0cy9uZWdfNDVfcmVzaWR1YWxfbmV2ZXJfc2F0aXNmaWVzX3Jvd19ib3VuZC5tdGwiLCJuYW1lIjoibmVnXzQ1X3Jlc2lkdWFsX25ldmVyX3NhdGlzZmllc19yb3dfYm91bmQubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-3}

A projection or a residual naming **every** field the struct declares is not a distinct
residual type — it normalizes back to the plain struct type, and is rejected by a row
bound exactly as a bare struct value already is. A residual's row is therefore always a
strict subset of the brand's declared row, possibly empty. A nominal type declaring
no fields has a full-width empty row and remains the plain nominal type.

Write `D(B)` for a nominal brand's declared field-to-type map and `res(B, R)`
for its normalized type at current row `R`, where `R` is a restriction of `D(B)`.
Normalization is defined by:

```text
res(B, R) = B        if R = D(B)
res(B, R) = B.{R}    if R is a strict subset of D(B)
```

Here `B.{R}` denotes the branded residual whose labels are those of `R`;
it is not additional source syntax. Thus `res(B, {}) = B.{}` when `D(B)`
is nonempty, but `res(B, {}) = B` when `D(B) = {}`. For anonymous rows,
`res(anonymous, R) = R`. Different brands remain distinct at every width,
including zero; neither empty form is `Unit`.

<!-- rfc.py:last_reviewed 1af04d209f9a354bb195c078866e38a341535285 -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (6)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2NoZWNrZWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2RlZmF1bHQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9jaGVja2VkLm10bCIsInNvdXJjZSI6InN0cnVjdCBBIHsgdmFsdWU6IFN0cmluZyB9XG5zdHJ1Y3QgQiB7IHZhbHVlOiBTdHJpbmcgfVxuZnVuIHRha2UoeDogQi57fSkge31cbmZ1biBtYWluKCkge1xuICAgIGxldCBhIDo9IEEgeyB2YWx1ZSA9IFwib3duZWRcIiB9O1xuICAgIGxldCB2YWx1ZSA6PSBhLnZhbHVlO1xuICAgIHRha2UoYSk7IC8vIEVSUk9SW1QwMDAxXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9jaGVja2VkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9jaGVja2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9kZWZhdWx0Lm10bCIsInNvdXJjZSI6InN0cnVjdCBBIHsgdmFsdWU6IFN0cmluZyB9XG5zdHJ1Y3QgQiB7IHZhbHVlOiBTdHJpbmcgfVxuZnVuIHRha2UoeDogQi57fSkge31cbmZ1biBtYWluKCkge1xuICAgIGxldCBhIDo9IEEgeyB2YWx1ZSA9IFwib3duZWRcIiB9O1xuICAgIGxldCB2YWx1ZSA6PSBhLnZhbHVlO1xuICAgIHRha2UoYSk7IC8vIEVSUk9SW1QwMDAxXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9kZWZhdWx0Lm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9kaXN0aW5jdF9icmFuZF9kZWZhdWx0Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG50eXBlIEVtcHR5IDo9IFBhaXIue307XG50eXBlIENhbGxiYWNrIDo9IG9uY2UgfHwgLT4gUGFpcjtcblxuZnVuIGVtcHR5KCkgLT4gUGFpci57fSB7XG4gICAgbGV0IHBhaXIgOj0gUGFpciB7IGxlZnQgPSBcIm9sZFwiLCByaWdodCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IGxlZnQgOj0gcGFpci5sZWZ0O1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIHBhaXJcbn1cblxuZnVuIHJlYnVpbGQoZW1wdHk6IFBhaXIue30pIC0+IFBhaXIge1xuICAgIHZhciByZXN0b3JlZCA6PSBlbXB0eTtcbiAgICByZXN0b3JlZC5sZWZ0IDo9IFwibmV3XCI7XG4gICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgcmVzdG9yZWRcbn1cblxuZnVuIGNhcHR1cmVkKGVtcHR5OiBFbXB0eSkgLT4gUGFpciB7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbZW1wdHldIG9uY2UgfHwge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biB3cml0dGVuKGVtcHR5OiBQYWlyLnt9KSAtPiBQYWlyIHtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW2VtcHR5XSBvbmNlIHx8IC0+IFBhaXIge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChyZWJ1aWxkKGVtcHR5KCkpLnJpZ2h0ID09IFwiYmFja1wiKTtcbiAgICBhc3NlcnQoY2FwdHVyZWQoZW1wdHkoKSkubGVmdCA9PSBcIm5ld1wiKTtcbiAgICBhc3NlcnQod3JpdHRlbihlbXB0eSgpKS5yaWdodCA9PSBcImJhY2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6InN0cnVjdCBuZXZlciBzYXRpc2ZpZXMgYSByb3cgYm91bmQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfNDRfZnVsbF93aWR0aF9wcm9qZWN0aW9uX3N0aWxsX3JlamVjdGVkX2J5X3Jvd19ib3VuZC5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSdzIG93biBub3JtYWxpemF0aW9uIHJ1bGUsIGFuZFxuLy8gUkZDLTAxMzcgc2VjMydzIHdvcmtlZCBleGFtcGxlKTogYSBwcm9qZWN0aW9uIG5hbWluZyBldmVyeSBmaWVsZCBhIHN0cnVjdFxuLy8gZGVjbGFyZXMgbm9ybWFsaXplcyBiYWNrIHRvIHRoZSBwbGFpbiBzdHJ1Y3QgdHlwZSByYXRoZXIgdGhhbiBzdGF5aW5nIGFcbi8vIGRpc3RpbmN0IGJyYW5kZWQgcmVzaWR1YWwuIENvbmZpcm1zIHRoZSBub3JtYWxpemF0aW9uIGRvZXNuJ3QgYWNjaWRlbnRhbGx5XG4vLyBlYXJuIHJvdy1ib3VuZCBlbGlnaWJpbGl0eSAtLSBoLnsgZmQsIG5hbWUgfSwgZnVsbCB3aWR0aCwgaXMgcmVqZWN0ZWQgYnkgYSByb3dcbi8vIGJvdW5kIHRoZSBleGFjdCBzYW1lIHdheSBhIGJhcmUgYEhhbmRsZWAgdmFsdWUgYWxyZWFkeSBpcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biB3YW50c19hX3JlY29yZDxyZWNvcmQgVDogeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcsIC4uIH0+KHQ6IFQpIC0+IGk2NCB7IHQuZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBfIDo9IHdhbnRzX2FfcmVjb3JkKGgueyBmZCwgbmFtZSB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ0X2Z1bGxfd2lkdGhfcHJvamVjdGlvbl9zdGlsbF9yZWplY3RlZF9ieV9yb3dfYm91bmQubXRsIiwibmFtZSI6Im5lZ180NF9mdWxsX3dpZHRoX3Byb2plY3Rpb25fc3RpbGxfcmVqZWN0ZWRfYnlfcm93X2JvdW5kLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-4}

> **Since v0.13.0.** Struct: RFC-0137 slice 2 (metel-core#858). Anonymous record:
> RFC-0117 (metel-core#789). `--move-check` agreement: metel-core#950.

Using a narrowed value where a wider row, or the whole type, is required is a type error
at type-check time, not deferred to `--move-check`; every still-present field stays
readable and its methods callable. A whole-value use *at* the narrowed type — moving it,
binding it, passing it to a matching-row parameter — is legal, and `--move-check` does not
flag it.

> **Changed in v0.14.0:** Row narrowing includes empty residuals.

Moving the last remaining non-`Copy` field leaves an empty residual. An anonymous
record has type `{}`; a nominal struct or record retains its brand with an empty
row, written `Name.{}`. Neither becomes `Unit`, and a branded empty residual does
not become an anonymous record. Fields read by copying remain in the row.
Reading any removed field is a `T0003` type error, including when the row is empty,
independently of `--move-check`.

An empty residual may be bound, passed, and returned wherever its exact residual
type is accepted. It does not satisfy the original non-empty type or a wider row;
structural eligibility and visibility are unchanged. Consuming its remaining
fields is distinct from moving the residual binding as a whole. A subsequent
whole-binding move obeys the ordinary ownership rules, whose use-after-move
enforcement remains controlled by `--move-check`.

Let `Γ(p) = res(B, R)` describe an available place's current row, with `B`
either a nominal brand or `anonymous`. Let `R[f ↦ T]` extend a row not
containing `f`. For an otherwise legal by-value field use, the row transition is:

```text
Γ(p) = res(B, R[f ↦ T])    T is known    T: !Copy
------------------------------------------------ consume-field
Γ ⊢ consume(p.f): T  ⇒  Γ[p ↦ res(B, R)]

Γ(p) = res(B, R[f ↦ T])    T: Copy
----------------------------------------------- copy-field
Γ ⊢ read(p.f): T  ⇒  Γ

Γ(p) = res(B, R)    f ∉ dom(R)
----------------------------------------------- absent-field
Γ ⊢ read(p.f)  ⇒  T0003
```

The consume-field conclusion includes `R = {}`. These judgments do not
grant permission to move from a borrowed place or a `Drop` type. An unresolved
field type is held under [legality-1](#spec.ownership.narrowing.legality-1).
The absent-field judgment and row transition apply with or without move checking.

Ordinary binding, argument, and return typing may use `res(B, {})` at that
same type. No empty-residual rule supplies missing fields, erases `B`, or
coerces the result to `Unit`. A whole-binding consumption updates ownership
state separately: when move checking is enabled, consuming a non-`Copy`
residual marks its binding moved, and another whole use reports `T0019`;
consuming its last field does not itself mark that binding wholly moved.

<!-- rfc.py:last_reviewed a05e640b2fd860df61ebd241c1595a7794f941d2 -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (35)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgUGFpcmAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIwMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7XG4gICAgbGVmdDogU3RyaW5nLFxuICAgIHJpZ2h0OiBpNjQsXG59XG5cbmZ1biB0YWtlKHBhaXI6IFBhaXIpIC0+IGk2NCB7XG4gICAgcGFpci5yaWdodFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwiYVwiLCByaWdodCA9IDEgfTtcbiAgICBsZXQgbGVmdDogU3RyaW5nIDo9IHBhaXIubGVmdDtcbiAgICBsZXQgdmFsdWU6IGk2NCA6PSB0YWtlKHBhaXIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8wMl9wYXJ0aWFsX21vdmVfdXNlZF9hc193aG9sZS5tdGwiLCJuYW1lIjoiMDJfcGFydGlhbF9tb3ZlX3VzZWRfYXNfd2hvbGUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEzNyAvIFJGQy0wMTE3IChtZXRlbC1jb3JlIzk1MCk6IHdpdGggYC0tbW92ZS1jaGVja2Agb24sIGEgd2hvbGUtdmFsdWUgdXNlXG4vLyBvZiBhIGJpbmRpbmcgd2hvc2UgdHlwZSBoYXMgbmFycm93ZWQgdG8gYSByZXNpZHVhbCAvIG5hcnJvd2VyIHJlY29yZCBpcyBsZWdhbFxuLy8gLS0gbmFycm93aW5nIHJlbW92ZWQgZXhhY3RseSB0aGUgbW92ZWQgZmllbGRzLCBzbyB0aGUgdXNlIHRvdWNoZXMgbm9uZSBvZiB0aGVtLlxuLy8gQmVmb3JlICM5NTAsIGBtb3ZlX2NoZWNrYCBmbGFnZ2VkIGV2ZXJ5IHdob2xlLXZhbHVlIHVzZSBvZiBhIHBhcnRpYWxseS1tb3ZlZFxuLy8gYmluZGluZyByZWdhcmRsZXNzIG9mIGl0cyBjdXJyZW50IHR5cGUuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuZnVuIHRha2VfZmQoaDogSGFuZGxlLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG5mdW4gcmlnaHRfb2YocjogeyByaWdodDogaTY0IH0pIC0+IGk2NCB7IHIucmlnaHQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBTdHJ1Y3Q6IG5hcnJvd2VkIHRvIEhhbmRsZS57IGZkIH0sIHRoZW4gbW92ZWQgaW4gYnkgdmFsdWUgb25jZS5cbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBobiA6PSBoLm5hbWU7XG4gICAgYXNzZXJ0KHRha2VfZmQoaCkgPT0gMyk7XG5cbiAgICAvLyBBbm9ueW1vdXMgcmVjb3JkOiBuYXJyb3dlZCB0byB7IHJpZ2h0OiBpNjQgfSwgdGhlbiBtb3ZlZCBpbiBieSB2YWx1ZSBvbmNlLlxuICAgIGxldCByIDo9IHsgbGVmdCA9IFwiYVwiLnRvX3N0cmluZygpLCByaWdodCA9IDkgfTtcbiAgICBsZXQgcmwgOj0gci5sZWZ0O1xuICAgIGFzc2VydChyaWdodF9vZihyKSA9PSA5KTtcblxuICAgIC8vIEEgbmFycm93ZWQgYmluZGluZyByZWFkIChub3QgbW92ZWQpIGFzIGEgd2hvbGUgaXMgZmluZSB0b28uXG4gICAgbGV0IGcgOj0gSGFuZGxlIHsgZmQgPSA0LCBuYW1lID0gXCJ5XCIgfTtcbiAgICBsZXQgZ24gOj0gZy5uYW1lO1xuICAgIGxldCBhbGlhcyA6PSBnLnsgZmQgfTtcbiAgICBhc3NlcnQoYWxpYXMuZmQgPT0gNCk7XG5cbiAgICBwcmludGxuKFwiJHtobn0gJHtybH0gJHtnbn1cIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwN19tb3ZlX2NoZWNrX25hcnJvd2VkX3dob2xlX3VzZS5tdGwiLCJuYW1lIjoiMTA3X21vdmVfY2hlY2tfbmFycm93ZWRfd2hvbGVfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogcm93LW5hcnJvd2luZyBtb3ZlIHN0YXRlIGlzIHBhdGgtc2Vuc2l0aXZlIGFjcm9zcyBgaWZgIGFybXMuXG4vLyBCb3RoIGFybXMgbW92ZSB0aGUgc2FtZSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBgcmVjYDsgdGhlIGBlbHNlYCBhcm0gZG9lc1xuLy8gbm90IHNlZSB0aGUgYHRoZW5gIGFybSdzIG1vdmUsIHNvIGVhY2ggaXMgYW4gaW5kZXBlbmRlbnQgcGFydGlhbCBtb3ZlLiBBZnRlclxuLy8gdGhlIGBpZmAgdGhlIGFybXMgam9pbjogYHJlY2AgaXMgbmFycm93ZWQgdG8gYHsga2VlcDogaTY0IH1gIG9uIGV2ZXJ5IHBhdGgsXG4vLyBpdHMgc3Vydml2aW5nIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgYSB3aG9sZS12YWx1ZSB1c2UgYXQgdGhlIG5hcnJvd2VkXG4vLyByb3cgaXMgYWNjZXB0ZWQgKGFsc28gdW5kZXIgLS1tb3ZlLWNoZWNrKS5cbmZ1biBrZWVwX29mKHI6IHsga2VlcDogaTY0IH0pIC0+IGk2NCB7IHIua2VlcCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjb25kIDo9IHRydWU7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInhcIi50b19zdHJpbmcoKSwga2VlcCA9IDMgfTtcbiAgICBpZiAoY29uZCkge1xuICAgICAgICBsZXQgYSA6PSByZWMuZ29uZTtcbiAgICAgICAgYXNzZXJ0KGEgPT0gXCJ4XCIpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIGxldCBiIDo9IHJlYy5nb25lO1xuICAgICAgICBhc3NlcnQoYiA9PSBcInhcIik7XG4gICAgfVxuICAgIGFzc2VydChyZWMua2VlcCA9PSAzKTsgICAgICAgICAgLy8gc3Vydml2aW5nIGZpZWxkIHJlYWRhYmxlIGF0IHRoZSBqb2luZWQgcm93XG4gICAgYXNzZXJ0KGtlZXBfb2YocmVjKSA9PSAzKTsgICAgICAvLyB3aG9sZSB2YWx1ZSBmaXRzIHRoZSBuYXJyb3dlZCByb3dcbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzExMF9uYXJyb3dpbmdfaWZfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJuYW1lIjoiMTEwX25hcnJvd2luZ19pZl9hcm1zX2luZGVwZW5kZW50Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExMV9uYXJyb3dpbmdfbWF0Y2hfYXJtc19pbmRlcGVuZGVudC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzk1ODogdGhlIHNhbWUgcGVyLWFybSBmb3JrL2pvaW4gZm9yIGBtYXRjaGAuIFR3byBhcm1zIGVhY2ggbW92ZVxuLy8gdGhlIHNhbWUgbm9uLWBDb3B5YCBmaWVsZCBvZiBhbiBvdXRlciBiaW5kaW5nOyBhIGxhdGVyIGFybSBkb2VzIG5vdCBzZWUgYW5cbi8vIGVhcmxpZXIgYXJtJ3MgbW92ZS4gVGhlIGFybXMgam9pbiBhZnRlciB0aGUgYG1hdGNoYCwgbmFycm93aW5nIGByZWNgIHRvXG4vLyBgeyBrZWVwOiBpNjQgfWAuXG5mdW4ga2VlcF9vZihyOiB7IGtlZXA6IGk2NCB9KSAtPiBpNjQgeyByLmtlZXAgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgc2VsIDo9IDI7XG4gICAgbGV0IHJlYyA6PSB7IGdvbmUgPSBcInlcIi50b19zdHJpbmcoKSwga2VlcCA9IDcgfTtcbiAgICBsZXQgdGFnIDo9IG1hdGNoIChzZWwpIHtcbiAgICAgICAgMSA9PiB7IGxldCBhIDo9IHJlYy5nb25lOyAxMCB9LFxuICAgICAgICAyID0+IHsgbGV0IGIgOj0gcmVjLmdvbmU7IDIwIH0sXG4gICAgICAgIF8gPT4geyBsZXQgYyA6PSByZWMuZ29uZTsgMzAgfSxcbiAgICB9O1xuICAgIGFzc2VydCh0YWcgPT0gMjApO1xuICAgIGFzc2VydChyZWMua2VlcCA9PSA3KTtcbiAgICBhc3NlcnQoa2VlcF9vZihyZWMpID09IDcpO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTExX25hcnJvd2luZ19tYXRjaF9hcm1zX2luZGVwZW5kZW50Lm10bCIsIm5hbWUiOiIxMTFfbmFycm93aW5nX21hdGNoX2FybXNfaW5kZXBlbmRlbnQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9icmFuZF9jaGVja2VkLm10bCIsInNvdXJjZSI6InN0cnVjdCBTIHsgYTogU3RyaW5nIH1cbmZ1biBhbm9ueW1vdXMocjoge30pIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiIH07XG4gICAgbGV0IHggOj0gcy5hO1xuICAgIGFub255bW91cyhzKTsgLy8gRVJST1JbVDAwMDFdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX2JyYW5kX2NoZWNrZWQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2JyYW5kX2NoZWNrZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9icmFuZF9kZWZhdWx0Lm10bCIsInNvdXJjZSI6InN0cnVjdCBTIHsgYTogU3RyaW5nIH1cbmZ1biBhbm9ueW1vdXMocjoge30pIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiIH07XG4gICAgbGV0IHggOj0gcy5hO1xuICAgIGFub255bW91cyhzKTsgLy8gRVJST1JbVDAwMDFdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX2JyYW5kX2RlZmF1bHQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2JyYW5kX2RlZmF1bHQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfY2FwdHVyZV9taXNzaW5nX2ZpZWxkLm10bCIsInNvdXJjZSI6InN0cnVjdCBQYWlyIHsgbGVmdDogU3RyaW5nLCByaWdodDogU3RyaW5nIH1cbmZ1biBpbnZhbGlkKGVtcHR5OiBQYWlyLnt9KSAtPiBTdHJpbmcge1xuICAgIGxldCBjYWxsYmFjayA6PSBbZW1wdHldIG9uY2UgfHwgLT4gU3RyaW5nIHsgZW1wdHkubGVmdCB9OyAvLyBFUlJPUltUMDAwM11cbiAgICBjYWxsYmFjaygpXG59XG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX2NhcHR1cmVfbWlzc2luZ19maWVsZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfY2FwdHVyZV9taXNzaW5nX2ZpZWxkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2NoZWNrZWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2RlZmF1bHQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9ub21pbmFsX3JlY29yZF9jaGVja2VkLm10bCIsInNvdXJjZSI6InJlY29yZCBTIHsgcHVibGljIGE6IFN0cmluZywgcHVibGljIGI6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiLCBiID0gXCJiXCIgfTtcbiAgICBsZXQgeCA6PSBzLmE7XG4gICAgbGV0IHkgOj0gcy5iO1xuICAgIHByaW50bG4ocy5hKTsgLy8gRVJST1JbVDAwMDNdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX25vbWluYWxfcmVjb3JkX2NoZWNrZWQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX25vbWluYWxfcmVjb3JkX2NoZWNrZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9ub21pbmFsX3JlY29yZF9kZWZhdWx0Lm10bCIsInNvdXJjZSI6InJlY29yZCBTIHsgcHVibGljIGE6IFN0cmluZywgcHVibGljIGI6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiLCBiID0gXCJiXCIgfTtcbiAgICBsZXQgeCA6PSBzLmE7XG4gICAgbGV0IHkgOj0gcy5iO1xuICAgIHByaW50bG4ocy5hKTsgLy8gRVJST1JbVDAwMDNdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX25vbWluYWxfcmVjb3JkX2RlZmF1bHQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX25vbWluYWxfcmVjb3JkX2RlZmF1bHQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG50eXBlIEVtcHR5IDo9IFBhaXIue307XG50eXBlIENhbGxiYWNrIDo9IG9uY2UgfHwgLT4gUGFpcjtcblxuZnVuIGVtcHR5KCkgLT4gUGFpci57fSB7XG4gICAgbGV0IHBhaXIgOj0gUGFpciB7IGxlZnQgPSBcIm9sZFwiLCByaWdodCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IGxlZnQgOj0gcGFpci5sZWZ0O1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIHBhaXJcbn1cblxuZnVuIHJlYnVpbGQoZW1wdHk6IFBhaXIue30pIC0+IFBhaXIge1xuICAgIHZhciByZXN0b3JlZCA6PSBlbXB0eTtcbiAgICByZXN0b3JlZC5sZWZ0IDo9IFwibmV3XCI7XG4gICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgcmVzdG9yZWRcbn1cblxuZnVuIGNhcHR1cmVkKGVtcHR5OiBFbXB0eSkgLT4gUGFpciB7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbZW1wdHldIG9uY2UgfHwge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biB3cml0dGVuKGVtcHR5OiBQYWlyLnt9KSAtPiBQYWlyIHtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW2VtcHR5XSBvbmNlIHx8IC0+IFBhaXIge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChyZWJ1aWxkKGVtcHR5KCkpLnJpZ2h0ID09IFwiYmFja1wiKTtcbiAgICBhc3NlcnQoY2FwdHVyZWQoZW1wdHkoKSkubGVmdCA9PSBcIm5ld1wiKTtcbiAgICBhc3NlcnQod3JpdHRlbihlbXB0eSgpKS5yaWdodCA9PSBcImJhY2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nX21pc3NpbmdfZmllbGQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxuZnVuIHJlYnVpbGQoZW1wdHk6IFBhaXIue30pIC0+IFBhaXIge1xuICAgIHZhciByZXN0b3JlZCA6PSBlbXB0eTtcbiAgICByZXN0b3JlZC5sZWZ0IDo9IFwibmV3XCI7XG4gICAgcmVzdG9yZWQgLy8gRVJST1JbVDAwMDFdXG59XG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlYmluZGluZ19taXNzaW5nX2ZpZWxkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWJpbmRpbmdfbWlzc2luZ19maWVsZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWNvcmRfY2hlY2tlZC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCB4IDo9IHIubGVmdDtcbiAgICBsZXQgeSA6PSByLnJpZ2h0O1xuICAgIHByaW50bG4oci5sZWZ0KTsgLy8gRVJST1JbVDAwMDNdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlY29yZF9jaGVja2VkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWNvcmRfY2hlY2tlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWNvcmRfZGVmYXVsdC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCB4IDo9IHIubGVmdDtcbiAgICBsZXQgeSA6PSByLnJpZ2h0O1xuICAgIHByaW50bG4oci5sZWZ0KTsgLy8gRVJST1JbVDAwMDNdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlY29yZF9kZWZhdWx0Lm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWNvcmRfZGVmYXVsdC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9zdHJ1Y3RfY2hlY2tlZC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUyB7IGE6IFN0cmluZywgYjogU3RyaW5nIH1cbmZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFMgeyBhID0gXCJhXCIsIGIgPSBcImJcIiB9O1xuICAgIGxldCB4IDo9IHMuYTtcbiAgICBsZXQgeSA6PSBzLmI7XG4gICAgcHJpbnRsbihzLmEpOyAvLyBFUlJPUltUMDAwM11cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfc3RydWN0X2NoZWNrZWQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3N0cnVjdF9jaGVja2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9zdHJ1Y3RfZGVmYXVsdC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUyB7IGE6IFN0cmluZywgYjogU3RyaW5nIH1cbmZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFMgeyBhID0gXCJhXCIsIGIgPSBcImJcIiB9O1xuICAgIGxldCB4IDo9IHMuYTtcbiAgICBsZXQgeSA6PSBzLmI7XG4gICAgcHJpbnRsbihzLmEpOyAvLyBFUlJPUltUMDAwM11cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfc3RydWN0X2RlZmF1bHQubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3N0cnVjdF9kZWZhdWx0Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF91bml0X2NoZWNrZWQubXRsIiwic291cmNlIjoiZnVuIHRha2UoeDogKCkpIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IHZhbHVlID0gXCJvd25lZFwiIH07XG4gICAgbGV0IHZhbHVlIDo9IHIudmFsdWU7XG4gICAgdGFrZShyKTsgLy8gRVJST1JbVDAwMDFdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3VuaXRfY2hlY2tlZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfdW5pdF9jaGVja2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF91bml0X2RlZmF1bHQubXRsIiwic291cmNlIjoiZnVuIHRha2UoeDogKCkpIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgciA6PSB7IHZhbHVlID0gXCJvd25lZFwiIH07XG4gICAgbGV0IHZhbHVlIDo9IHIudmFsdWU7XG4gICAgdGFrZShyKTsgLy8gRVJST1JbVDAwMDFdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3VuaXRfZGVmYXVsdC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfdW5pdF9kZWZhdWx0Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjgiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF93aG9sZV9tb3ZlLm10bCIsInNvdXJjZSI6InN0cnVjdCBQYWlyIHsgbGVmdDogU3RyaW5nLCByaWdodDogU3RyaW5nIH1cbmZ1biB0YWtlKHA6IFBhaXIue30pIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgdGFrZShwKTtcbiAgICB0YWtlKHApOyAvLyBFUlJPUltUMDAxOV1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfd2hvbGVfbW92ZS5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfd2hvbGVfbW92ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF93aWRlcl9jaGVja2VkLm10bCIsInNvdXJjZSI6InN0cnVjdCBTIHsgYTogU3RyaW5nIH1cbmZ1biBmdWxsKHM6IFMpIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiIH07XG4gICAgbGV0IHggOj0gcy5hO1xuICAgIGZ1bGwocyk7IC8vIEVSUk9SW1QwMDAxXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF93aWRlcl9jaGVja2VkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF93aWRlcl9jaGVja2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF93aWRlcl9kZWZhdWx0Lm10bCIsInNvdXJjZSI6InN0cnVjdCBTIHsgYTogU3RyaW5nIH1cbmZ1biBmdWxsKHM6IFMpIHt9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBTIHsgYSA9IFwiYVwiIH07XG4gICAgbGV0IHggOj0gcy5hO1xuICAgIGZ1bGwocyk7IC8vIEVSUk9SW1QwMDAxXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF93aWRlcl9kZWZhdWx0Lm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF93aWRlcl9kZWZhdWx0Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6InBhcnRpYWxseS1tb3ZlZCBgSGFuZGxlYCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180Nl93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogb25jZSBhIGZpZWxkIGlzIG1vdmVkIG91dCwgdGhlIHZhbHVlJ3MgdHlwZVxuLy8gaXMgdGhlIHJlc2lkdWFsIC0tIGBIYW5kbGUueyBmZCB9YCAtLSBub3QgdGhlIHdob2xlIGBIYW5kbGVgLiBQYXNzaW5nIGl0IHdoZXJlXG4vLyB0aGUgd2hvbGUgc3RydWN0IGlzIHJlcXVpcmVkIGlzIGEgcGxhaW4gdHlwZSBlcnJvciBhdCBpbmZlcmVuY2UgdGltZSwgbm8gbG9uZ2VyXG4vLyBvbmx5IGEgYC0tbW92ZS1jaGVja2AgZmluZGluZy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biB3YW50c19mdWxsKGg6IEhhbmRsZSkgLT4gaTY0IHsgaC5mZCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gMywgbmFtZSA9IFwieFwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTtcbiAgICBsZXQgXyA6PSB3YW50c19mdWxsKGgpOyAgIC8vIHJlamVjdGVkOiBgaGAgaXMgYEhhbmRsZS57IGZkIH1gXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180Nl93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDZfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180OF9yZWNvcmRfd2hvbGVfdXNlX2FmdGVyX3BhcnRpYWxfbW92ZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExNyAobWV0ZWwtY29yZSM3ODkpOiBvbmNlIGEgZmllbGQgaXMgbW92ZWQgb3V0IG9mIGFuIGFub255bW91cyByZWNvcmQsXG4vLyB0aGUgcmVjb3JkJ3MgdHlwZSBpcyB0aGUgbmFycm93ZXIgcm93IC0tIGB7IHJpZ2h0OiBpNjQgfWAsIG5vdCBgeyBsZWZ0LCByaWdodCB9YC5cbi8vIFBhc3NpbmcgaXQgd2hlcmUgdGhlIHdob2xlIHJlY29yZCBpcyByZXF1aXJlZCBpcyBhIHBsYWluIHR5cGUgZXJyb3IgYXRcbi8vIGluZmVyZW5jZSB0aW1lLCBubyBsb25nZXIgb25seSBhIGAtLW1vdmUtY2hlY2tgIGZpbmRpbmcuIEEgbmFycm93ZWQgcmVjb3JkIGhhc1xuLy8gbm8gZGlzdGluY3QgdHlwZSBtYXJrZXIsIHNvIHRoZSBkaWFnbm9zdGljIGlzIHRoZSBvcmRpbmFyeSByZWNvcmQtc2hhcGVcbi8vIG1pc21hdGNoLlxuXG5mdW4gd2FudHNfZnVsbChyOiB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IGk2NCB9KSAtPiBpNjQgeyByLnJpZ2h0IH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyBsZWZ0ID0gXCJhXCIudG9fc3RyaW5nKCksIHJpZ2h0ID0gMSB9O1xuICAgIGxldCB0YWtlbiA6PSByLmxlZnQ7XG4gICAgbGV0IF8gOj0gd2FudHNfZnVsbChyKTtcbiAgICBwcmludGxuKHRha2VuKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ4X3JlY29yZF93aG9sZV91c2VfYWZ0ZXJfcGFydGlhbF9tb3ZlLm10bCIsIm5hbWUiOiJuZWdfNDhfcmVjb3JkX3dob2xlX3VzZV9hZnRlcl9wYXJ0aWFsX21vdmUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCB1bmlmeSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjOTU4OiB0aGUgam9pbiBpcyB0aGUgKnVuaW9uKiBvZiB0aGUgYXJtcycgbW92ZXMuIE9ubHkgdGhlIGB0aGVuYFxuLy8gYXJtIG1vdmVzIGByZWMuZ29uZWA7IGFmdGVyIHRoZSBgaWZgLCBgcmVjYCBpcyBuYXJyb3dlZCB0byBgeyBrZWVwOiBpNjQgfWAgb25cbi8vIGV2ZXJ5IHBhdGggKHRoZSBtb3ZlIGlzIGpvaW5lZCBpbiBldmVuIHRob3VnaCB0aGUgYGVsc2VgIHBhdGggZGlkbid0IHJ1biBpdCksXG4vLyBzbyBhIHdob2xlLXZhbHVlIHVzZSBhdCB0aGUgd2lkZXIgcm93IGlzIHJlamVjdGVkLlxuZnVuIHdob2xlKHI6IHsgZ29uZTogU3RyaW5nLCBrZWVwOiBpNjQgfSkgLT4gaTY0IHsgci5rZWVwIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGNvbmQgOj0gdHJ1ZTtcbiAgICBsZXQgcmVjIDo9IHsgZ29uZSA9IFwielwiLnRvX3N0cmluZygpLCBrZWVwID0gMSB9O1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIGxldCBhIDo9IHJlYy5nb25lO1xuICAgIH1cbiAgICB3aG9sZShyZWMpICAgICAgICAgICAgICAvLyByZWMgOiB7IGtlZXA6IGk2NCB9IGhlcmUgLS0gd2lkZXIgcm93IHJlcXVpcmVkXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ181MF9uYXJyb3dpbmdfb25lX2FybV9tb3ZlX3RhaW50c19qb2luLm10bCIsIm5hbWUiOiJuZWdfNTBfbmFycm93aW5nX29uZV9hcm1fbW92ZV90YWludHNfam9pbi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2JvdW5kZWRfY2xvbmVfcmVzaWR1YWxfY2FsbGJhY2subXRsIiwic291cmNlIjoicmVjb3JkIFVzZXIgeyBwdWJsaWMgaWQ6IGk2NCwgcHVibGljIG5hbWU6IFN0cmluZywgcHVibGljIGNvdW50OiBpNjQgfVxudHlwZSBVc2VyQWxpYXMgOj0gVXNlcjtcbnR5cGUgQ2FsbGJhY2sgOj0gb25jZSB8fCAtPiBpNjQ7XG5cbmZ1biBjbG9uZV9oZWFkPHJvdyBSPih2YWx1ZTogeyBpZDogaTY0LCAuLlIgfSkgLT4geyBpZDogaTY0LCAuLlIgfVxud2hlcmUgYWxsIFI6IENsb25lIHtcbiAgICB2YWx1ZS5jbG9uZSgpXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB1c2VyOiBVc2VyQWxpYXMgOj0gVXNlciB7IGlkID0gMywgbmFtZSA9IFwibW92ZWRcIiwgY291bnQgPSA1IH07XG4gICAgbGV0IG5hbWUgOj0gdXNlci5uYW1lO1xuICAgIGxldCByZXNpZHVhbCA6PSBjbG9uZV9oZWFkKHVzZXIpO1xuICAgIGFzc2VydChuYW1lID09IFwibW92ZWRcIik7XG4gICAgYXNzZXJ0KHJlc2lkdWFsLmlkICsgcmVzaWR1YWwuY291bnQgPT0gOCk7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbcmVzaWR1YWxdIG9uY2UgfHwge1xuICAgICAgICByZXNpZHVhbC5pZCArIHJlc2lkdWFsLmNvdW50XG4gICAgfTtcbiAgICBhc3NlcnQoY2FsbGJhY2soKSA9PSA4KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvcmVsZWFzZV9tYXRyaXhfYm91bmRlZF9jbG9uZV9yZXNpZHVhbF9jYWxsYmFjay5tdGwiLCJuYW1lIjoicmVsZWFzZV9tYXRyaXhfYm91bmRlZF9jbG9uZV9yZXNpZHVhbF9jYWxsYmFjay5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2Nsb25lX2NhcHR1cmUubXRsIiwic291cmNlIjoicmVjb3JkIExlZGdlciB7IHB1YmxpYyBpZDogaTY0LCBwdWJsaWMgbWVtbzogU3RyaW5nLCBwdWJsaWMgY291bnQ6IGk2NCB9XG50eXBlIExlZGdlckFsaWFzIDo9IExlZGdlcjtcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IG9yaWdpbmFsOiBMZWRnZXJBbGlhcyA6PSBMZWRnZXIgeyBpZCA9IDQsIG1lbW8gPSBcImtlZXBcIiwgY291bnQgPSA2IH07XG4gICAgbGV0IGNvcGllZCA6PSBvcmlnaW5hbC5jbG9uZSgpO1xuICAgIGxldCBtZW1vIDo9IGNvcGllZC5tZW1vO1xuICAgIGxldCBjYWxsYmFjayA6PSBbY29waWVkXSBvbmNlIHx8IHsgY29waWVkLmlkICsgY29waWVkLmNvdW50IH07XG4gICAgYXNzZXJ0KG1lbW8gPT0gXCJrZWVwXCIpO1xuICAgIGFzc2VydChjYWxsYmFjaygpID09IDEwKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvcmVsZWFzZV9tYXRyaXhfY2xvbmVfY2FwdHVyZS5tdGwiLCJuYW1lIjoicmVsZWFzZV9tYXRyaXhfY2xvbmVfY2FwdHVyZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2dlbmVyaWNfcmVzaWR1YWxfY2FwdHVyZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwiZ29uZVwiLCByaWdodCA9IFwia2VwdFwiIH07XG4gICAgbGV0IGxlZnQgOj0gcGFpci5sZWZ0O1xuICAgIGxldCByZXBhaXIgOj0gW3BhaXJdIG9uY2UgfGV4dHJhfCB7IChwYWlyLnJpZ2h0LCBleHRyYSkgfTtcbiAgICBsZXQgcmVzdWx0IDo9IHJlcGFpcig3KTtcbiAgICBhc3NlcnQocmVzdWx0LjAgPT0gXCJrZXB0XCIpO1xuICAgIGFzc2VydChyZXN1bHQuMSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvcmVsZWFzZV9tYXRyaXhfZ2VuZXJpY19yZXNpZHVhbF9jYXB0dXJlLm10bCIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9nZW5lcmljX3Jlc2lkdWFsX2NhcHR1cmUubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X3Jlc2lkdWFsX2Rpc3BhdGNoX2NhcHR1cmUubXRsIiwic291cmNlIjoicmVjb3JkIFBhaXIgeyBwdWJsaWMgbGVmdDogU3RyaW5nLCBwdWJsaWMgcmlnaHQ6IFN0cmluZyB9XG50eXBlIFBhaXJBbGlhcyA6PSBQYWlyO1xudHlwZSBSZXN0b3JlIDo9IG9uY2UgdmFyIHx8IC0+IFBhaXJBbGlhcztcblxuYXNwZWN0IFN0YXRlIHsgZnVuIHN0YXRlKCZzZWxmKSAtPiBpNjQ7IH1cbmV4dGVuZDxyb3cgUjogeyByaWdodDogU3RyaW5nLCAuLiB9PiB7IC4uUiB9OiBTdGF0ZSB7XG4gICAgZnVuIHN0YXRlKCZzZWxmKSAtPiBpNjQgeyAxIH1cbn1cbmV4dGVuZDxyb3cgUjogIXsgcmlnaHQgfT4geyAuLlIgfTogU3RhdGUge1xuICAgIGZ1biBzdGF0ZSgmc2VsZikgLT4gaTY0IHsgMCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBwYWlyOiBQYWlyQWxpYXMgOj0gUGFpciB7IGxlZnQgPSBcImxlZnRcIiwgcmlnaHQgPSBcInJpZ2h0XCIgfTtcbiAgICBhc3NlcnQocGFpci5zdGF0ZSgpID09IDEpO1xuICAgIGxldCBsZWZ0IDo9IHBhaXIubGVmdDtcbiAgICBsZXQgcGFydGlhbCA6PSBwYWlyLmNsb25lKCk7XG4gICAgYXNzZXJ0KHBhcnRpYWwucmlnaHQgPT0gXCJyaWdodFwiKTtcbiAgICBhc3NlcnQocGFpci5zdGF0ZSgpID09IDEpO1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIGFzc2VydChwYWlyLnN0YXRlKCkgPT0gMCk7XG4gICAgbGV0IGVtcHR5OiBQYWlyLnt9IDo9IHBhaXIuY2xvbmUoKTtcbiAgICBhc3NlcnQoZW1wdHkuc3RhdGUoKSA9PSAwKTtcbiAgICBsZXQgcmVzdG9yZTogUmVzdG9yZSA6PSBbcGFpcl0gb25jZSB2YXIgfHwgLT4gUGFpckFsaWFzIHtcbiAgICAgICAgcGFpci5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICAgICAgcGFpci5yaWdodCA6PSBcImFnYWluXCI7XG4gICAgICAgIGFzc2VydChwYWlyLnN0YXRlKCkgPT0gMSk7XG4gICAgICAgIHBhaXJcbiAgICB9O1xuICAgIG1hdGNoIChyZXN0b3JlKCkpIHtcbiAgICAgICAgeyBsZWZ0LCAuLnJlc3QgfSA9PiB7XG4gICAgICAgICAgICBhc3NlcnQobGVmdCA9PSBcInJlc3RvcmVkXCIpO1xuICAgICAgICAgICAgYXNzZXJ0KHJlc3QucmlnaHQgPT0gXCJhZ2FpblwiKTtcbiAgICAgICAgICAgIGFzc2VydChyZXN0LnN0YXRlKCkgPT0gMSk7XG4gICAgICAgIH0sXG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVjb3Jkcy9yZWxlYXNlX21hdHJpeF9yZXNpZHVhbF9kaXNwYXRjaF9jYXB0dXJlLm10bCIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9yZXNpZHVhbF9kaXNwYXRjaF9jYXB0dXJlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X3Jlc2lkdWFsX2R5bl9hbGlhcy5tdGwiLCJzb3VyY2UiOiJyZWNvcmQgSXRlbSB7IHB1YmxpYyBuYW1lOiBTdHJpbmcsIHB1YmxpYyB0b2tlbjogU3RyaW5nIH1cbmFzcGVjdCBEZXNjcmliZSB7IGZ1biBkZXNjcmliZSgmc2VsZikgLT4gU3RyaW5nOyB9XG5leHRlbmQ8cm93IFI6IHsgbmFtZTogU3RyaW5nLCAuLiB9PiB7IC4uUiB9OiBEZXNjcmliZSB7XG4gICAgZnVuIGRlc2NyaWJlKCZzZWxmKSAtPiBTdHJpbmcgeyBzZWxmLm5hbWUuY2xvbmUoKSB9XG59XG50eXBlIFZpZXcgOj0gZHluIERlc2NyaWJlO1xudHlwZSBDYWxsYmFjayA6PSBvbmNlIHx8IC0+IFN0cmluZztcbmZ1biBkaXNwbGF5KHZhbHVlOiAmVmlldykgLT4gU3RyaW5nIHsgdmFsdWUuZGVzY3JpYmUoKSB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBpdGVtIDo9IEl0ZW0geyBuYW1lID0gXCJrZXB0XCIsIHRva2VuID0gXCJkaXNjYXJkZWRcIiB9O1xuICAgIGxldCB0b2tlbiA6PSBpdGVtLnRva2VuO1xuICAgIGxldCBvYmplY3Q6IFZpZXcgOj0gaXRlbTtcbiAgICBhc3NlcnQoZGlzcGxheSgmb2JqZWN0KSA9PSBcImtlcHRcIik7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbb2JqZWN0XSBvbmNlIHx8IHsgb2JqZWN0LmRlc2NyaWJlKCkgfTtcbiAgICBhc3NlcnQoY2FsbGJhY2soKSA9PSBcImtlcHRcIik7XG4gICAgbGV0IGFub255bW91czogVmlldyA6PSB7IG5hbWUgPSBcImFub255bW91c1wiIH07XG4gICAgYXNzZXJ0KGRpc3BsYXkoJmFub255bW91cykgPT0gXCJhbm9ueW1vdXNcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWNvcmRzL3JlbGVhc2VfbWF0cml4X3Jlc2lkdWFsX2R5bl9hbGlhcy5tdGwiLCJuYW1lIjoicmVsZWFzZV9tYXRyaXhfcmVzaWR1YWxfZHluX2FsaWFzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjgiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZXNpZHVhbF9jYXB0dXJlX2FscmVhZHlfbW92ZWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxuZnVuIHRha2UodmFsdWU6IFBhaXIue30pIHt9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgbGVmdCA6PSBwYWlyLmxlZnQ7XG4gICAgbGV0IHJpZ2h0IDo9IHBhaXIucmlnaHQ7XG4gICAgdGFrZShwYWlyKTtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW3BhaXJdIG9uY2UgdmFyIHx8IC0+IFBhaXIgeyAvLyBFUlJPUltUMDAxOV1cbiAgICAgICAgcGFpci5sZWZ0IDo9IFwibmV3XCI7XG4gICAgICAgIHBhaXIucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHBhaXJcbiAgICB9O1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9yZXNpZHVhbF9jYXB0dXJlX2FscmVhZHlfbW92ZWQubXRsIiwibmFtZSI6InJlc2lkdWFsX2NhcHR1cmVfYWxyZWFkeV9tb3ZlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlc2lkdWFsX2NhcHR1cmVfZW50cnkubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxudHlwZSBDYWxsYmFjayA6PSBvbmNlIHZhciB8fCAtPiBQYWlyO1xuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgbGVmdCA6PSBwYWlyLmxlZnQ7XG4gICAgbGV0IHJpZ2h0IDo9IHBhaXIucmlnaHQ7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbcGFpcl0gb25jZSB2YXIgfHwgLT4gUGFpciB7XG4gICAgICAgIHBhaXIubGVmdCA6PSBcIm5ld1wiO1xuICAgICAgICBwYWlyLnJpZ2h0IDo9IFwiYmFja1wiO1xuICAgICAgICBwYWlyXG4gICAgfTtcbiAgICBhc3NlcnQoY2FsbGJhY2soKS5sZWZ0ID09IFwibmV3XCIpO1xuXG4gICAgdmFyIHBhcnRpYWwgOj0gUGFpciB7IGxlZnQgPSBcImdvbmVcIiwgcmlnaHQgPSBcImtlcHRcIiB9O1xuICAgIGxldCByZW1vdmVkIDo9IHBhcnRpYWwubGVmdDtcbiAgICBsZXQgcmVzdG9yZSA6PSBbcGFydGlhbF0gb25jZSB2YXIgfHwgLT4gUGFpciB7XG4gICAgICAgIHBhcnRpYWwubGVmdCA6PSBcInJlc3RvcmVkXCI7XG4gICAgICAgIGFzc2VydChwYXJ0aWFsLnJpZ2h0ID09IFwia2VwdFwiKTtcbiAgICAgICAgcGFydGlhbFxuICAgIH07XG4gICAgYXNzZXJ0KHJlc3RvcmUoKS5sZWZ0ID09IFwicmVzdG9yZWRcIik7XG5cbiAgICB2YXIgYW5vbnltb3VzIDo9IHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgcm93X2xlZnQgOj0gYW5vbnltb3VzLmxlZnQ7XG4gICAgbGV0IHJlc3RvcmVfcm93IDo9IFthbm9ueW1vdXNdIG9uY2UgdmFyIHx8IC0+IHsgcmlnaHQ6IFN0cmluZyB9IHtcbiAgICAgICAgYW5vbnltb3VzLnJpZ2h0IDo9IFwiYmFja1wiO1xuICAgICAgICBhbm9ueW1vdXNcbiAgICB9O1xuICAgIGFzc2VydChyZXN0b3JlX3JvdygpLnJpZ2h0ID09IFwiYmFja1wiKTtcblxuICAgIGxldCBlbXB0eV9hbm9ueW1vdXMgOj0geyBvd25lZCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IG93bmVkIDo9IGVtcHR5X2Fub255bW91cy5vd25lZDtcbiAgICBsZXQgZW1wdHlfY2FsbGJhY2sgOj0gW2VtcHR5X2Fub255bW91c10gb25jZSB8fCAtPiB7fSB7IGVtcHR5X2Fub255bW91cyB9O1xuICAgIGxldCBlbXB0eToge30gOj0gZW1wdHlfY2FsbGJhY2soKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvcmVzaWR1YWxfY2FwdHVyZV9lbnRyeS5tdGwiLCJuYW1lIjoicmVzaWR1YWxfY2FwdHVyZV9lbnRyeS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZXNpZHVhbF9jYXB0dXJlX21pc3NpbmdfZmllbGQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHBhaXIgOj0gUGFpciB7IGxlZnQgPSBcImdvbmVcIiwgcmlnaHQgPSBcImtlcHRcIiB9O1xuICAgIGxldCBsZWZ0IDo9IHBhaXIubGVmdDtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW3BhaXJdIG9uY2UgfHwgLT4gU3RyaW5nIHsgcGFpci5sZWZ0IH07IC8vIEVSUk9SW1QwMDAzXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9yZXNpZHVhbF9jYXB0dXJlX21pc3NpbmdfZmllbGQubXRsIiwibmFtZSI6InJlc2lkdWFsX2NhcHR1cmVfbWlzc2luZ19maWVsZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjEyIiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoicmVzaWR1YWxfY2FwdHVyZV9zb3VyY2VfcmV1c2VkLm10bCIsInNvdXJjZSI6InN0cnVjdCBQYWlyIHsgbGVmdDogU3RyaW5nLCByaWdodDogU3RyaW5nIH1cbmZ1biB0YWtlKHZhbHVlOiBQYWlyLnt9KSB7fVxuZnVuIG1haW4oKSB7XG4gICAgdmFyIHBhaXIgOj0gUGFpciB7IGxlZnQgPSBcIm9sZFwiLCByaWdodCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IGxlZnQgOj0gcGFpci5sZWZ0O1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIGxldCBjYWxsYmFjayA6PSBbcGFpcl0gb25jZSB2YXIgfHwgLT4gUGFpciB7XG4gICAgICAgIHBhaXIubGVmdCA6PSBcIm5ld1wiO1xuICAgICAgICBwYWlyLnJpZ2h0IDo9IFwiYmFja1wiO1xuICAgICAgICBwYWlyXG4gICAgfTtcbiAgICB0YWtlKHBhaXIpOyAvLyBFUlJPUltUMDAxOV1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcmVzaWR1YWxfY2FwdHVyZV9zb3VyY2VfcmV1c2VkLm10bCIsIm5hbWUiOiJyZXNpZHVhbF9jYXB0dXJlX3NvdXJjZV9yZXVzZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlc2lkdWFsX3JlYmluZGluZ19nZW5lcmljX2ZpZWxkcy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgQm94PFQ+IHsgdmFsdWU6IFQsIHRleHQ6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYm94OiBCb3g8aTY0PiA6PSBCb3ggeyB2YWx1ZSA9IDMsIHRleHQgPSBcInhcIiB9O1xuICAgIGxldCB0ZXh0IDo9IGJveC50ZXh0O1xuICAgIHZhciByZWJvdW5kIDo9IGJveDtcbiAgICBhc3NlcnQocmVib3VuZC52YWx1ZSA9PSAzKTtcbiAgICBsZXQgb3RoZXI6IEJveDxTdHJpbmc+IDo9IEJveCB7IHZhbHVlID0gXCJvd25lZFwiLCB0ZXh0ID0gXCJ4XCIgfTtcbiAgICBsZXQgb3RoZXJfdGV4dCA6PSBvdGhlci50ZXh0O1xuICAgIHZhciBvdGhlcl9yZWJvdW5kIDo9IG90aGVyO1xuICAgIGFzc2VydChvdGhlcl9yZWJvdW5kLnZhbHVlID09IFwib3duZWRcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWNvcmRzL3Jlc2lkdWFsX3JlYmluZGluZ19nZW5lcmljX2ZpZWxkcy5tdGwiLCJuYW1lIjoicmVzaWR1YWxfcmViaW5kaW5nX2dlbmVyaWNfZmllbGRzLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.ownership.narrowing.legality-5}

A residual may itself be projected (`h.{ fd }` on an already-narrowed `h`) for a field
still in its row; naming a field already moved out of it is rejected.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:last_reviewed a770445761323bbb96448619152def8053da27ae -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwOF9hbGlhc19xdWFsaWZpZWRfbWV0aG9kX29uX25hcnJvd2VkX3JlY2VpdmVyLm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBhIHRyYW5zcGFyZW50XG4vLyB0eXBlIGFsaWFzIChSRkMtMDE2MCkgcXVhbGlmeWluZyBhIGNhbGwsIGFuIGBleHRlbmRgIG1ldGhvZCB3aG9zZSByZWNlaXZlciBpc1xuLy8gYSBicmFuZGVkIHJlc2lkdWFsIGAmU2VsZi57IGZkIH1gIChSRkMtMDEzNyBzbGljZSAxKSwgYW5kIGEgcmVjZWl2ZXIgbmFycm93ZWRcbi8vIGJ5IGEgcGFydGlhbCBtb3ZlIChSRkMtMDEzNyBzbGljZSAyKS4gVGhlIGFsaWFzIGVyYXNlcyB0byBgSGFuZGxlYCwgc29cbi8vIGBIOjpkZXNjcmliZWAgaXMgYEhhbmRsZTo6ZGVzY3JpYmVgOyB0aGUgbmFycm93ZWQgYGhgIGFuZCBhbiBleHBsaWNpdFxuLy8gcmUtcHJvamVjdGlvbiBgaC57IGZkIH1gIGJvdGggZml0IHRoZSByZXNpZHVhbCBwYXJhbWV0ZXIuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cbnR5cGUgSCA6PSBIYW5kbGU7XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiAmU2VsZi57IGZkIH0pIC0+IGk2NCB7IGguZmQgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaDogSCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBhc3NlcnQoSDo6ZGVzY3JpYmUoJmgpID09IDcpOyAgICAgICAgICAgIC8vIGFsaWFzLXF1YWxpZmllZCBjYWxsLCBuYXJyb3dlZCByZWNlaXZlclxuICAgIGFzc2VydChIOjpkZXNjcmliZSgmaC57IGZkIH0pID09IDcpOyAgICAgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDhfYWxpYXNfcXVhbGlmaWVkX21ldGhvZF9vbl9uYXJyb3dlZF9yZWNlaXZlci5tdGwiLCJuYW1lIjoiMTA4X2FsaWFzX3F1YWxpZmllZF9tZXRob2Rfb25fbmFycm93ZWRfcmVjZWl2ZXIubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.ownership.narrowing.dynamics-1}

A struct's own field projection expression produces exactly the same residual type as the
equivalent partial move.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:last_reviewed a770445761323bbb96448619152def8053da27ae -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBtb3ZpbmcgYSBub24tYENvcHlgIGZpZWxkIG91dCBvZiBhIHN0cnVjdFxuLy8gbmFycm93cyB0aGUgdmFsdWUncyAqdHlwZSogdG8gYSByZXNpZHVhbCBvZiB0aGUgc2FtZSBicmFuZCAtLSBgSGFuZGxlYCBiZWNvbWVzXG4vLyBgSGFuZGxlLnsgZmQgfWAgLS0gYW5kIHRoYXQgcmVzaWR1YWwgaXMgZXhhY3RseSB0aGUgb25lIGFuIGV4cGxpY2l0IHByb2plY3Rpb25cbi8vIGBoLnsgZmQgfWAgcHJvZHVjZXMsIHNvIHRoZSB0d28gYXJlIGludGVyY2hhbmdlYWJsZSBhdCBhIGBTZWxmLnsgZmQgfWBcbi8vIHBhcmFtZXRlciAoc3BlYy5vd25lcnNoaXAubmFycm93aW5nLmR5bmFtaWNzLTEpLiBXaXRoIGAtLW1vdmUtY2hlY2tgIG9uLCBhXG4vLyB3aG9sZS12YWx1ZSB1c2Ugb2YgdGhlIG5hcnJvd2VkIHZhbHVlIGlzICpub3QqIGZsYWdnZWQgYXMgYSBwYXJ0aWFsLW1vdmVcbi8vIHZpb2xhdGlvbiAobWV0ZWwtY29yZSM5NTApIC0tIG5hcnJvd2luZyByZW1vdmVkIGV4YWN0bHkgdGhlIG1vdmVkIGZpZWxkLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6ICZTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFJvdXRlIEE6IGEgcGFydGlhbCBtb3ZlIG5hcnJvd3MgYGhgIGluIHBsYWNlOyBhIGJvcnJvd2VkIHdob2xlLXZhbHVlIHVzZVxuICAgIC8vIG9mIHRoZSBuYXJyb3dlZCB2YWx1ZSBpcyBhY2NlcHRlZCwgcHJvamVjdGlvbiBhbmQgbW92ZSBwcm9kdWNpbmcgdGhlIHNhbWVcbiAgICAvLyByZXNpZHVhbCB0eXBlLlxuICAgIGxldCBoIDo9IEhhbmRsZSB7IGZkID0gNywgbmFtZSA9IFwiYVwiIH07XG4gICAgbGV0IHRha2VuIDo9IGgubmFtZTsgICAgICAgICAgICAgICAgICAgIC8vIGggOiBIYW5kbGUueyBmZCB9IGZyb20gaGVyZSBvblxuICAgIGFzc2VydChoLmZkID09IDcpOyAgICAgICAgICAgICAgICAgICAgICAvLyB0aGUgc2libGluZyBmaWVsZCBzdGF5cyByZWFkYWJsZVxuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoKSA9PSA3KTsgICAgICAvLyBuYXJyb3dlZCB2YWx1ZSBmaXRzIGAmU2VsZi57IGZkIH1gXG4gICAgYXNzZXJ0KEhhbmRsZTo6ZGVzY3JpYmUoJmgueyBmZCB9KSA9PSA3KTsgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuXG4gICAgLy8gUm91dGUgQjogYW4gZXhwbGljaXQgcHJvamVjdGlvbiBvZmYgYSBmcmVzaCB2YWx1ZSBwcm9kdWNlcyB0aGUgc2FtZSB0eXBlLlxuICAgIGxldCBoMiA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcImJcIiB9O1xuICAgIGFzc2VydChIYW5kbGU6OmRlc2NyaWJlKCZoMi57IGZkIH0pID09IDcpO1xuXG4gICAgcHJpbnRsbih0YWtlbik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwNF9uYXJyb3dpbmdfbW92ZV9tYXRjaGVzX3Byb2plY3Rpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwOF9hbGlhc19xdWFsaWZpZWRfbWV0aG9kX29uX25hcnJvd2VkX3JlY2VpdmVyLm10bCIsInNvdXJjZSI6Ii8vIHYwLjEzLjAgY3Jvc3MtZmVhdHVyZSAoaW50ZWdyYXRpb24gc2Vzc2lvbiwgbWV0ZWwtY29yZSM5NTYpOiBhIHRyYW5zcGFyZW50XG4vLyB0eXBlIGFsaWFzIChSRkMtMDE2MCkgcXVhbGlmeWluZyBhIGNhbGwsIGFuIGBleHRlbmRgIG1ldGhvZCB3aG9zZSByZWNlaXZlciBpc1xuLy8gYSBicmFuZGVkIHJlc2lkdWFsIGAmU2VsZi57IGZkIH1gIChSRkMtMDEzNyBzbGljZSAxKSwgYW5kIGEgcmVjZWl2ZXIgbmFycm93ZWRcbi8vIGJ5IGEgcGFydGlhbCBtb3ZlIChSRkMtMDEzNyBzbGljZSAyKS4gVGhlIGFsaWFzIGVyYXNlcyB0byBgSGFuZGxlYCwgc29cbi8vIGBIOjpkZXNjcmliZWAgaXMgYEhhbmRsZTo6ZGVzY3JpYmVgOyB0aGUgbmFycm93ZWQgYGhgIGFuZCBhbiBleHBsaWNpdFxuLy8gcmUtcHJvamVjdGlvbiBgaC57IGZkIH1gIGJvdGggZml0IHRoZSByZXNpZHVhbCBwYXJhbWV0ZXIuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cbnR5cGUgSCA6PSBIYW5kbGU7XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiAmU2VsZi57IGZkIH0pIC0+IGk2NCB7IGguZmQgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaDogSCA6PSBIYW5kbGUgeyBmZCA9IDcsIG5hbWUgPSBcIm5cIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBhc3NlcnQoSDo6ZGVzY3JpYmUoJmgpID09IDcpOyAgICAgICAgICAgIC8vIGFsaWFzLXF1YWxpZmllZCBjYWxsLCBuYXJyb3dlZCByZWNlaXZlclxuICAgIGFzc2VydChIOjpkZXNjcmliZSgmaC57IGZkIH0pID09IDcpOyAgICAgLy8gcmUtcHJvamVjdGluZyB0aGUgcmVzaWR1YWw6IHNhbWUgdHlwZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDhfYWxpYXNfcXVhbGlmaWVkX21ldGhvZF9vbl9uYXJyb3dlZF9yZWNlaXZlci5tdGwiLCJuYW1lIjoiMTA4X2FsaWFzX3F1YWxpZmllZF9tZXRob2Rfb25fbmFycm93ZWRfcmVjZWl2ZXIubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

### Passing a residual to a function

> **Since v0.13.0 (RFC-0137, metel-core#857):** projection-produced residuals match
> compatible projected parameters.

Since v0.13.0 (RFC-0137 slice 2, metel-core#858), a residual reached via move-triggered
narrowing is passed exactly the same way; nothing here is specific to how the residual
arose.

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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwM19icmFuZGVkX3JlY29yZF9wcm9qZWN0aW9uX2FjY2VwdHNfcmVhbF9wcm9qZWN0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJlZ3Jlc3Npb24gKG1ldGVsLWNvcmUjODU3LCBSRkMtMDEzNyBzbGljZSAxKTogYSBzdHJ1Y3QncyBvd24gZmllbGQgcHJvamVjdGlvbiBpc1xuLy8gbm93IGJyYW5kZWQgLS0gU2VsZi57IGZkIH0gYWNjZXB0cyBhIHZhbHVlIGFjdHVhbGx5IHByb2plY3RlZCBmcm9tIGEgcmVhbCBIYW5kbGVcbi8vIChoLnsgZmQgfSksIHRoZSBjYXNlIHRoaXMgZml4dHVyZSBjb25maXJtcyBzdGlsbCB3b3Jrcy4gVGhlIGNvbXBhbmlvbiBuZWdhdGl2ZVxuLy8gY2FzZSAoYSBiYXJlIGFub255bW91cyByZWNvcmQgb2YgdGhlIHNhbWUgc2hhcGUgbXVzdCBub3cgYmUgUkVKRUNURUQsIHdoaWNoIGlzXG4vLyB0aGUgYWN0dWFsIGJ1ZyB0aGlzIGNsb3NlcykgbGl2ZXMgaW4gdHlwZWNoZWNraW5nL3N0cnVjdHMsIHNpbmNlIGl0J3MgYSBUMDAwMVxuLy8gcmVqZWN0aW9uLCBub3Qgc29tZXRoaW5nIGV2YWx1YWJsZS5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmV4dGVuZCBIYW5kbGUge1xuICAgIGZ1biBkZXNjcmliZShoOiBTZWxmLnsgZmQgfSkgLT4gaTY0IHsgaC5mZCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBoYW5kbGUgOj0gSGFuZGxlIHsgZmQgPSAzLCBuYW1lID0gXCJ4XCIgfTtcbiAgICBhc3NlcnQoSGFuZGxlOjpkZXNjcmliZShoYW5kbGUueyBmZCB9KSA9PSAzKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvMTAzX2JyYW5kZWRfcmVjb3JkX3Byb2plY3Rpb25fYWNjZXB0c19yZWFsX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6IjEwM19icmFuZGVkX3JlY29yZF9wcm9qZWN0aW9uX2FjY2VwdHNfcmVhbF9wcm9qZWN0aW9uLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSk6IHRoaXMgaXMgdGhlIGFjdHVhbCBtb3RpdmF0aW5nIGJ1Z1xuLy8gLS0gU2VsZi57IGZkIH0gdXNlZCB0byBhY2NlcHQgYSBiYXJlIGFub255bW91cyByZWNvcmQgbGl0ZXJhbCBvZiB0aGUgc2FtZSBzaGFwZVxuLy8gZXhhY3RseSBhcyByZWFkaWx5IGFzIGEgdmFsdWUgYWN0dWFsbHkgZGVyaXZlZCBmcm9tIGEgcmVhbCBIYW5kbGUsIHNpbmNlIHRoZVxuLy8gcHJvamVjdGlvbiByZXNvbHZlZCB0byBhbiB1bmJyYW5kZWQgcmVjb3JkIHR5cGUuIE5vdyByZWplY3RlZDogYSBzdHJ1Y3QncyBvd25cbi8vIHByb2plY3Rpb24gaXMgYnJhbmRlZCwgYW5kIGEgc2FtZS1zaGFwZWQgYW5vbnltb3VzIHJlY29yZCBuZXZlciBjYXJyaWVzIHRoYXRcbi8vIGJyYW5kLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlKGg6IFNlbGYueyBmZCB9KSAtPiBpNjQgeyBoLmZkIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IF8gOj0gSGFuZGxlOjpkZXNjcmliZSh7IGZkID0gMyB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwiLCJuYW1lIjoibmVnXzQzX2JhcmVfcmVjb3JkX3JlamVjdGVkX2J5X2JyYW5kZWRfcHJvamVjdGlvbl9wYXJhbS5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

### Drop dispatch against a narrowed residual

> **Gap** GAP-OWNERSHIP-003

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

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858):** reassigning a moved-out field
> widens a residual back to its whole type.

`Handle.{ fd }` becomes `Handle` again once `name` is reassigned. This formalizes the
whole-value-restoring behavior reassignment already has; it does not require another RFC.
Widening does not check the reassembled value against constructor invariants. Ordinary field
reassignment can already bypass such an invariant independently of narrowing or widening;
RFC-0114 (Constructor Aspect and Canonical Construction, still `0-draft`) proposes a
separate solution.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.ownership.widening.legality-1}

A field assignment on a narrowed residual (`h.name := …`) is legal even though `name` is
absent from the residual's current row: the assigned field is resolved against the
brand's full declared row, and the write reintroduces it. Widening applies only to an
**owned** binding; a non-`Copy` field cannot be moved out of — and so cannot be
reassigned back into — a value reached through a reference
([references-and-moves.legality-1](#spec.ownership.references-and-moves.legality-1)).

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).**

<!-- rfc.py:last_reviewed 1bf44ca5dc418015d5b862416820f2c04eba5ecb -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNV93aWRlbmluZ19yZWFzc2lnbl9yZXN0b3Jlc19mdWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogYXNzaWduaW5nIGEgdmFsdWUgdG8gYSBmaWVsZCBtaXNzaW5nIGZyb20gYVxuLy8gcmVzaWR1YWwncyByb3cgd2lkZW5zIHRoZSByZXNpZHVhbCdzIHR5cGUgYmFjayB0byB0aGUgd2hvbGUgYnJhbmRcbi8vIChzcGVjLm93bmVyc2hpcC53aWRlbmluZy5keW5hbWljcy0xKS4gT25seSBmb3IgYW4gb3duZWQgYmluZGluZzsgd2lkZW5pbmcgZG9lc1xuLy8gbm90IHJlLWNoZWNrIGFueSBjb25zdHJ1Y3RvciBpbnZhcmlhbnQuIFdpdGggYC0tbW92ZS1jaGVja2Agb24sIHRoZSB3aWRlbmVkXG4vLyBiaW5kaW5nIGlzIHdob2xlIGFnYWluIC0tIGEgYnktdmFsdWUgdXNlIGlzIGEgY2xlYW4gbW92ZSwgbm90IGEgcGFydGlhbC1tb3ZlXG4vLyB2aW9sYXRpb24uXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gd2FudHNfZnVsbChoOiBIYW5kbGUpIC0+IGk2NCB7IGguZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgaCA6PSBIYW5kbGUgeyBmZCA9IDUsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBoLm5hbWUgOj0gXCJ5XCI7ICAgICAgICAgICAgICAgICAgICAgLy8gd2lkZW5zIGJhY2s6IGggOiBIYW5kbGVcbiAgICBhc3NlcnQoaC5uYW1lID09IFwieVwiKTsgICAgICAgICAgICAgLy8gc2libGluZyByZWFkYWJsZSBhdCB0aGUgd2lkZW5lZCB0eXBlXG4gICAgYXNzZXJ0KHdhbnRzX2Z1bGwoaCkgPT0gNSk7ICAgICAgICAvLyB3aG9sZSBgSGFuZGxlYCBtb3ZlZCBpbiwgb25jZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDVfd2lkZW5pbmdfcmVhc3NpZ25fcmVzdG9yZXNfZnVsbC5tdGwiLCJuYW1lIjoiMTA1X3dpZGVuaW5nX3JlYXNzaWduX3Jlc3RvcmVzX2Z1bGwubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nX3dyb25nX3R5cGUubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxuZnVuIGludmFsaWQoZW1wdHk6IFBhaXIue30pIHtcbiAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgcmVzdG9yZWQubGVmdCA6PSAzOyAvLyBFUlJPUltUMDAwMV1cbn1cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nX3dyb25nX3R5cGUubXRsIiwibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3JlYmluZGluZ193cm9uZ190eXBlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InJlZmVyZW5jZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBuYXJyb3dpbmcgYW5kIHdpZGVuaW5nIGFwcGx5IG9ubHkgdG8gYW5cbi8vIG93bmVkIGJpbmRpbmcuIEEgbm9uLWBDb3B5YCBmaWVsZCBjYW5ub3QgYmUgbW92ZWQgb3V0IG9mIGEgdmFsdWUgcmVhY2hlZFxuLy8gdGhyb3VnaCBhIHJlZmVyZW5jZSAoUkZDLTAwNzEgXHUwMGE3Ny4xKSwgc28gdGhlcmUgaXMgbmV2ZXIgYSByZXNpZHVhbCB0byBuYXJyb3cgdG9cbi8vIG9yIHdpZGVuIGZyb20gYmVoaW5kIG9uZSBcdTIwMTQgdGhpcyBydWxlIGlzIHVuY2hhbmdlZCBieSBSRkMtMDEzNy5cbi8vXG4vLyBOZWVkcyBtb3ZlX2NoZWNrID0gdHJ1ZTogdGhlIG1vdmUtb3V0LW9mLWEtcmVmZXJlbmNlIGJhbiBpcyBhIG1vdmUtY2hlY2tlclxuLy8gcnVsZSwgbm90IG9uZSBvZiB0aGUgYWx3YXlzLW9uIHR5cGVjaGVjayBydWxlcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBjb25zdW1lX25hbWUoaDogJnZhciBIYW5kbGUpIC0+IFN0cmluZyB7XG4gICAgbGV0IG4gOj0gaC5uYW1lOyAgIC8vIHJlamVjdGVkOiBtb3ZpbmcgYG5hbWVgIG91dCB0aHJvdWdoIGAmdmFyIEhhbmRsZWBcbiAgICBuXG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGZkID0gMSwgbmFtZSA9IFwieFwiIH07XG4gICAgcHJpbnRsbihjb25zdW1lX25hbWUoJnZhciBoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzEzXzBfeF9zdHJ1Y3RfcGF0dGVybl9wYXJ0aWFsX21vdmVfbmFycm93cy5tdGwiLCJzb3VyY2UiOiIvLyBDcm9zcy1mZWF0dXJlICh2MC4xMy4wKTogYSBgbWF0Y2ggKGgpYCAoUkZDLTAxNTYgcGFyZW50aGVzaXplZCBzY3J1dGluZWUpIGJpbmRzXG4vLyBhIG5vbi1gQ29weWAgZmllbGQgb3V0IG9mIGEgc3RydWN0IHZhbHVlIHRocm91Z2ggYSBzdHJ1Y3QgcGF0dGVyblxuLy8gKG1ldGVsLWNvcmUjNzUzKS4gVGhhdCBwYXJ0aWFsIG1vdmUgbmFycm93cyBgaGAgKFJGQy0wMTM3IHNsaWNlIDIpOiB0aGUgbW92ZWRcbi8vIGZpZWxkIGlzIGdvbmUsIGV2ZXJ5IG90aGVyIGZpZWxkIHN0YXlzIHJlYWRhYmxlLCBhbmQgcmVhc3NpZ25pbmcgdGhlIG1vdmVkXG4vLyBmaWVsZCB3aWRlbnMgYGhgIGJhY2sgdG8gdGhlIHdob2xlIHN0cnVjdC5cblxuc3RydWN0IEhhbmRsZSB7IGlkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGlkID0gNywgbmFtZSA9IFwiZmRcIi50b19zdHJpbmcoKSB9O1xuXG4gICAgLy8gYmluZCBhbmQgY29uc3VtZSBgbmFtZWAgdmlhIGEgc3RydWN0IHBhdHRlcm47IGBoYCBpcyBub3cgYEhhbmRsZS57IGlkIH1gXG4gICAgbGV0IHRha2VuIDo9IG1hdGNoIChoKSB7IEhhbmRsZSB7IG5hbWUsIC4uIH0gPT4gbmFtZSB9O1xuICAgIGFzc2VydCh0YWtlbiA9PSBcImZkXCIpO1xuXG4gICAgLy8gYSBzdGlsbC1wcmVzZW50IGZpZWxkIGlzIHJlYWRhYmxlIG9uIHRoZSBuYXJyb3dlZCB2YWx1ZVxuICAgIGFzc2VydChoLmlkID09IDcpO1xuXG4gICAgLy8gcmVhc3NpZ25pbmcgdGhlIG1vdmVkIGZpZWxkIHdpZGVucyBgaGAgYmFjayB0byB0aGUgd2hvbGUgYEhhbmRsZWBcbiAgICBoLm5hbWUgOj0gXCJmZDJcIi50b19zdHJpbmcoKTtcbiAgICBhc3NlcnQoaC5uYW1lID09IFwiZmQyXCIpO1xuICAgIGFzc2VydChoLmlkID09IDcpO1xuXG4gICAgcHJpbnRsbihcIm9rXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy92MF8xM18wX3hfc3RydWN0X3BhdHRlcm5fcGFydGlhbF9tb3ZlX25hcnJvd3MubXRsIiwibmFtZSI6InYwXzEzXzBfeF9zdHJ1Y3RfcGF0dGVybl9wYXJ0aWFsX21vdmVfbmFycm93cy5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.ownership.widening.dynamics-1}

Assigning a value to a field missing from a residual's current row widens the residual's
type to include that field, at the same brand; once every moved-out field has been
reassigned the type is the plain struct again and the value may be used as a whole
([partial-moves.legality-3](#spec.ownership.partial-moves.legality-3)).

This includes widening from an empty residual. For a mutable anonymous-record
binding the restored labels recover its original record type; for a mutable
nominal binding they recover the original nominal type once all fields are restored.

Using `res` as defined in [narrowing.legality-3](#spec.ownership.narrowing.legality-3),
let `O(p)` be the binding's original field-to-type map (the declared row for
a nominal value, the original inferred or annotated row for an anonymous record).
For a mutable owned binding, restoration obeys:

```text
Γ ⊢ e: T ⇒ Γ₁    Γ₁(p) = res(B, R)    O(p)(f) = T    f ∉ dom(R)
---------------------------------------------------------------- restore-field
Γ ⊢ p.f := e  ⇒  Γ₁[p ↦ res(B, R[f ↦ T])]
```

The right-hand side is evaluated before the field is restored, using the
ordinary field-assignment evaluation rules. The transition applies when `R = {}`;
restoring only one of several missing fields does not restore the others.
An unknown original label, a wrong value type, or an immutable binding is
still rejected by the ordinary assignment rules. Restoration does not revive
a binding that was moved as a whole.

> **Since v0.13.0 (RFC-0137 slice 2, metel-core#858).** For an owned binding.

<!-- rfc.py:last_reviewed b3790b29364c7ce23fed862a6880a4782c3d603b -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0137](../../rfcs/3-integrated/rfc-0137-nominal-types-as-branded-rows.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (12)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwNV93aWRlbmluZ19yZWFzc2lnbl9yZXN0b3Jlc19mdWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTM3IHNsaWNlIDIgKG1ldGVsLWNvcmUjODU4KTogYXNzaWduaW5nIGEgdmFsdWUgdG8gYSBmaWVsZCBtaXNzaW5nIGZyb20gYVxuLy8gcmVzaWR1YWwncyByb3cgd2lkZW5zIHRoZSByZXNpZHVhbCdzIHR5cGUgYmFjayB0byB0aGUgd2hvbGUgYnJhbmRcbi8vIChzcGVjLm93bmVyc2hpcC53aWRlbmluZy5keW5hbWljcy0xKS4gT25seSBmb3IgYW4gb3duZWQgYmluZGluZzsgd2lkZW5pbmcgZG9lc1xuLy8gbm90IHJlLWNoZWNrIGFueSBjb25zdHJ1Y3RvciBpbnZhcmlhbnQuIFdpdGggYC0tbW92ZS1jaGVja2Agb24sIHRoZSB3aWRlbmVkXG4vLyBiaW5kaW5nIGlzIHdob2xlIGFnYWluIC0tIGEgYnktdmFsdWUgdXNlIGlzIGEgY2xlYW4gbW92ZSwgbm90IGEgcGFydGlhbC1tb3ZlXG4vLyB2aW9sYXRpb24uXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5mdW4gd2FudHNfZnVsbChoOiBIYW5kbGUpIC0+IGk2NCB7IGguZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgaCA6PSBIYW5kbGUgeyBmZCA9IDUsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCB0YWtlbiA6PSBoLm5hbWU7ICAgICAgICAgICAgICAgLy8gaCA6IEhhbmRsZS57IGZkIH1cbiAgICBoLm5hbWUgOj0gXCJ5XCI7ICAgICAgICAgICAgICAgICAgICAgLy8gd2lkZW5zIGJhY2s6IGggOiBIYW5kbGVcbiAgICBhc3NlcnQoaC5uYW1lID09IFwieVwiKTsgICAgICAgICAgICAgLy8gc2libGluZyByZWFkYWJsZSBhdCB0aGUgd2lkZW5lZCB0eXBlXG4gICAgYXNzZXJ0KHdhbnRzX2Z1bGwoaCkgPT0gNSk7ICAgICAgICAvLyB3aG9sZSBgSGFuZGxlYCBtb3ZlZCBpbiwgb25jZVxuICAgIHByaW50bG4odGFrZW4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDVfd2lkZW5pbmdfcmVhc3NpZ25fcmVzdG9yZXNfZnVsbC5tdGwiLCJuYW1lIjoiMTA1X3dpZGVuaW5nX3JlYXNzaWduX3Jlc3RvcmVzX2Z1bGwubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2NoZWNrZWQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfY2hlY2tlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX2RlZmF1bHQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxucmVjb3JkIE5hbWVkUGFpciB7IHB1YmxpYyBsZWZ0OiBTdHJpbmcsIHB1YmxpYyByaWdodDogU3RyaW5nIH1cbnN0cnVjdCBaZXJvIHt9XG5mdW4gZW1wdHlfcGFpcihwOiBQYWlyLnt9KSAtPiBQYWlyLnt9IHsgcCB9XG5mdW4gZW1wdHlfbmFtZWQocDogTmFtZWRQYWlyLnt9KSAtPiBOYW1lZFBhaXIue30geyBwIH1cbmZ1biBlbXB0eV9yZWNvcmQocjoge30pIC0+IHt9IHsgciB9XG5mdW4gZnVsbF9wYWlyKHA6IFBhaXIpIC0+IFN0cmluZyB7IHAubGVmdCB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICBwLnJpZ2h0IDo9IFwiYWdhaW5cIjtcbiAgICBhc3NlcnQoZnVsbF9wYWlyKHApID09IFwicmVzdG9yZWRcIik7XG4gICAgdmFyIGEgOj0geyBsZWZ0ID0gXCJsXCIsIHJpZ2h0ID0gXCJyXCIgfTtcbiAgICBsZXQgYWwgOj0gYS5sZWZ0O1xuICAgIGxldCBhciA6PSBhLnJpZ2h0O1xuICAgIGxldCBhZToge30gOj0gZW1wdHlfcmVjb3JkKGEpO1xuICAgIGEubGVmdCA6PSBcImJhY2tcIjtcbiAgICBhLnJpZ2h0IDo9IFwiYWxzb1wiO1xuICAgIGFzc2VydChhLmxlZnQgPT0gXCJiYWNrXCIpO1xuICAgIGxldCBuIDo9IE5hbWVkUGFpciB7IGxlZnQgPSBcImxcIiwgcmlnaHQgPSBcInJcIiB9O1xuICAgIGxldCBubCA6PSBuLmxlZnQ7XG4gICAgbGV0IG5yIDo9IG4ucmlnaHQ7XG4gICAgbGV0IG5lOiBOYW1lZFBhaXIue30gOj0gZW1wdHlfbmFtZWQobik7XG4gICAgbGV0IHEgOj0gUGFpciB7IGxlZnQgPSBcInFcIiwgcmlnaHQgPSBcInNcIiB9O1xuICAgIGxldCBxbCA6PSBxLmxlZnQ7XG4gICAgbGV0IHFyIDo9IHEucmlnaHQ7XG4gICAgbGV0IHFlOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocSk7XG4gICAgbGV0IHFlX2FnYWluOiBQYWlyLnt9IDo9IGVtcHR5X3BhaXIocWUpO1xuICAgIGxldCBjb3BpZWQgOj0geyB0ZXh0ID0gXCJnb25lXCIsIGNvdW50ID0gNyB9O1xuICAgIGxldCB0ZXh0IDo9IGNvcGllZC50ZXh0O1xuICAgIGFzc2VydChjb3BpZWQuY291bnQgPT0gNyk7XG4gICAgbGV0IHplcm86IFplcm8gOj0gWmVybyB7fTtcbiAgICBsZXQgbm9ybWFsaXplZDogWmVyby57fSA6PSB6ZXJvO1xuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfZGVmYXVsdC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9wYXJ0aWFsX3Jlc3RvcmVfY2hlY2tlZC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwiYmFja1wiO1xuICAgIGxldCBtaXNzaW5nIDo9IHAucmlnaHQ7IC8vIEVSUk9SW1QwMDAzXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9wYXJ0aWFsX3Jlc3RvcmVfY2hlY2tlZC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcGFydGlhbF9yZXN0b3JlX2NoZWNrZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9wYXJ0aWFsX3Jlc3RvcmVfZGVmYXVsdC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcCA6PSBQYWlyIHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGwgOj0gcC5sZWZ0O1xuICAgIGxldCByIDo9IHAucmlnaHQ7XG4gICAgcC5sZWZ0IDo9IFwiYmFja1wiO1xuICAgIGxldCBtaXNzaW5nIDo9IHAucmlnaHQ7IC8vIEVSUk9SW1QwMDAzXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9wYXJ0aWFsX3Jlc3RvcmVfZGVmYXVsdC5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcGFydGlhbF9yZXN0b3JlX2RlZmF1bHQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImVtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG50eXBlIEVtcHR5IDo9IFBhaXIue307XG50eXBlIENhbGxiYWNrIDo9IG9uY2UgfHwgLT4gUGFpcjtcblxuZnVuIGVtcHR5KCkgLT4gUGFpci57fSB7XG4gICAgbGV0IHBhaXIgOj0gUGFpciB7IGxlZnQgPSBcIm9sZFwiLCByaWdodCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IGxlZnQgOj0gcGFpci5sZWZ0O1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIHBhaXJcbn1cblxuZnVuIHJlYnVpbGQoZW1wdHk6IFBhaXIue30pIC0+IFBhaXIge1xuICAgIHZhciByZXN0b3JlZCA6PSBlbXB0eTtcbiAgICByZXN0b3JlZC5sZWZ0IDo9IFwibmV3XCI7XG4gICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgcmVzdG9yZWRcbn1cblxuZnVuIGNhcHR1cmVkKGVtcHR5OiBFbXB0eSkgLT4gUGFpciB7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbZW1wdHldIG9uY2UgfHwge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biB3cml0dGVuKGVtcHR5OiBQYWlyLnt9KSAtPiBQYWlyIHtcbiAgICBsZXQgY2FsbGJhY2sgOj0gW2VtcHR5XSBvbmNlIHx8IC0+IFBhaXIge1xuICAgICAgICB2YXIgcmVzdG9yZWQgOj0gZW1wdHk7XG4gICAgICAgIHJlc3RvcmVkLmxlZnQgOj0gXCJuZXdcIjtcbiAgICAgICAgcmVzdG9yZWQucmlnaHQgOj0gXCJiYWNrXCI7XG4gICAgICAgIHJlc3RvcmVkXG4gICAgfTtcbiAgICBjYWxsYmFjaygpXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChyZWJ1aWxkKGVtcHR5KCkpLnJpZ2h0ID09IFwiYmFja1wiKTtcbiAgICBhc3NlcnQoY2FwdHVyZWQoZW1wdHkoKSkubGVmdCA9PSBcIm5ld1wiKTtcbiAgICBhc3NlcnQod3JpdHRlbihlbXB0eSgpKS5yaWdodCA9PSBcImJhY2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlYmluZGluZy5tdGwiLCJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiZW1wdHlfcmVzaWR1YWxfcmViaW5kaW5nX21pc3NpbmdfZmllbGQubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxuZnVuIHJlYnVpbGQoZW1wdHk6IFBhaXIue30pIC0+IFBhaXIge1xuICAgIHZhciByZXN0b3JlZCA6PSBlbXB0eTtcbiAgICByZXN0b3JlZC5sZWZ0IDo9IFwibmV3XCI7XG4gICAgcmVzdG9yZWQgLy8gRVJST1JbVDAwMDFdXG59XG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL2VtcHR5X3Jlc2lkdWFsX3JlYmluZGluZ19taXNzaW5nX2ZpZWxkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yZWJpbmRpbmdfbWlzc2luZ19maWVsZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9jaGVja2VkLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIHZhciByIDo9IHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGxlZnQgOj0gci5sZWZ0O1xuICAgIHIubGVmdCA6PSByLnJpZ2h0O1xuICAgIGFzc2VydChyLmxlZnQgPT0gXCJyXCIpO1xuICAgIGxldCBtaXNzaW5nIDo9IHIucmlnaHQ7IC8vIEVSUk9SW1QwMDAzXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9jaGVja2VkLm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9jaGVja2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9kZWZhdWx0Lm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIHZhciByIDo9IHsgbGVmdCA9IFwibFwiLCByaWdodCA9IFwiclwiIH07XG4gICAgbGV0IGxlZnQgOj0gci5sZWZ0O1xuICAgIHIubGVmdCA6PSByLnJpZ2h0O1xuICAgIGFzc2VydChyLmxlZnQgPT0gXCJyXCIpO1xuICAgIGxldCBtaXNzaW5nIDo9IHIucmlnaHQ7IC8vIEVSUk9SW1QwMDAzXVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvcmVjb3Jkcy9lbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9kZWZhdWx0Lm10bCIsIm5hbWUiOiJlbXB0eV9yZXNpZHVhbF9yaHNfcmVzdG9yZV9kZWZhdWx0Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X3Jlc2lkdWFsX2Rpc3BhdGNoX2NhcHR1cmUubXRsIiwic291cmNlIjoicmVjb3JkIFBhaXIgeyBwdWJsaWMgbGVmdDogU3RyaW5nLCBwdWJsaWMgcmlnaHQ6IFN0cmluZyB9XG50eXBlIFBhaXJBbGlhcyA6PSBQYWlyO1xudHlwZSBSZXN0b3JlIDo9IG9uY2UgdmFyIHx8IC0+IFBhaXJBbGlhcztcblxuYXNwZWN0IFN0YXRlIHsgZnVuIHN0YXRlKCZzZWxmKSAtPiBpNjQ7IH1cbmV4dGVuZDxyb3cgUjogeyByaWdodDogU3RyaW5nLCAuLiB9PiB7IC4uUiB9OiBTdGF0ZSB7XG4gICAgZnVuIHN0YXRlKCZzZWxmKSAtPiBpNjQgeyAxIH1cbn1cbmV4dGVuZDxyb3cgUjogIXsgcmlnaHQgfT4geyAuLlIgfTogU3RhdGUge1xuICAgIGZ1biBzdGF0ZSgmc2VsZikgLT4gaTY0IHsgMCB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBwYWlyOiBQYWlyQWxpYXMgOj0gUGFpciB7IGxlZnQgPSBcImxlZnRcIiwgcmlnaHQgPSBcInJpZ2h0XCIgfTtcbiAgICBhc3NlcnQocGFpci5zdGF0ZSgpID09IDEpO1xuICAgIGxldCBsZWZ0IDo9IHBhaXIubGVmdDtcbiAgICBsZXQgcGFydGlhbCA6PSBwYWlyLmNsb25lKCk7XG4gICAgYXNzZXJ0KHBhcnRpYWwucmlnaHQgPT0gXCJyaWdodFwiKTtcbiAgICBhc3NlcnQocGFpci5zdGF0ZSgpID09IDEpO1xuICAgIGxldCByaWdodCA6PSBwYWlyLnJpZ2h0O1xuICAgIGFzc2VydChwYWlyLnN0YXRlKCkgPT0gMCk7XG4gICAgbGV0IGVtcHR5OiBQYWlyLnt9IDo9IHBhaXIuY2xvbmUoKTtcbiAgICBhc3NlcnQoZW1wdHkuc3RhdGUoKSA9PSAwKTtcbiAgICBsZXQgcmVzdG9yZTogUmVzdG9yZSA6PSBbcGFpcl0gb25jZSB2YXIgfHwgLT4gUGFpckFsaWFzIHtcbiAgICAgICAgcGFpci5sZWZ0IDo9IFwicmVzdG9yZWRcIjtcbiAgICAgICAgcGFpci5yaWdodCA6PSBcImFnYWluXCI7XG4gICAgICAgIGFzc2VydChwYWlyLnN0YXRlKCkgPT0gMSk7XG4gICAgICAgIHBhaXJcbiAgICB9O1xuICAgIG1hdGNoIChyZXN0b3JlKCkpIHtcbiAgICAgICAgeyBsZWZ0LCAuLnJlc3QgfSA9PiB7XG4gICAgICAgICAgICBhc3NlcnQobGVmdCA9PSBcInJlc3RvcmVkXCIpO1xuICAgICAgICAgICAgYXNzZXJ0KHJlc3QucmlnaHQgPT0gXCJhZ2FpblwiKTtcbiAgICAgICAgICAgIGFzc2VydChyZXN0LnN0YXRlKCkgPT0gMSk7XG4gICAgICAgIH0sXG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVjb3Jkcy9yZWxlYXNlX21hdHJpeF9yZXNpZHVhbF9kaXNwYXRjaF9jYXB0dXJlLm10bCIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9yZXNpZHVhbF9kaXNwYXRjaF9jYXB0dXJlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlc2lkdWFsX2NhcHR1cmVfZW50cnkubXRsIiwic291cmNlIjoic3RydWN0IFBhaXIgeyBsZWZ0OiBTdHJpbmcsIHJpZ2h0OiBTdHJpbmcgfVxudHlwZSBDYWxsYmFjayA6PSBvbmNlIHZhciB8fCAtPiBQYWlyO1xuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgbGVmdCA6PSBwYWlyLmxlZnQ7XG4gICAgbGV0IHJpZ2h0IDo9IHBhaXIucmlnaHQ7XG4gICAgbGV0IGNhbGxiYWNrOiBDYWxsYmFjayA6PSBbcGFpcl0gb25jZSB2YXIgfHwgLT4gUGFpciB7XG4gICAgICAgIHBhaXIubGVmdCA6PSBcIm5ld1wiO1xuICAgICAgICBwYWlyLnJpZ2h0IDo9IFwiYmFja1wiO1xuICAgICAgICBwYWlyXG4gICAgfTtcbiAgICBhc3NlcnQoY2FsbGJhY2soKS5sZWZ0ID09IFwibmV3XCIpO1xuXG4gICAgdmFyIHBhcnRpYWwgOj0gUGFpciB7IGxlZnQgPSBcImdvbmVcIiwgcmlnaHQgPSBcImtlcHRcIiB9O1xuICAgIGxldCByZW1vdmVkIDo9IHBhcnRpYWwubGVmdDtcbiAgICBsZXQgcmVzdG9yZSA6PSBbcGFydGlhbF0gb25jZSB2YXIgfHwgLT4gUGFpciB7XG4gICAgICAgIHBhcnRpYWwubGVmdCA6PSBcInJlc3RvcmVkXCI7XG4gICAgICAgIGFzc2VydChwYXJ0aWFsLnJpZ2h0ID09IFwia2VwdFwiKTtcbiAgICAgICAgcGFydGlhbFxuICAgIH07XG4gICAgYXNzZXJ0KHJlc3RvcmUoKS5sZWZ0ID09IFwicmVzdG9yZWRcIik7XG5cbiAgICB2YXIgYW5vbnltb3VzIDo9IHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgcm93X2xlZnQgOj0gYW5vbnltb3VzLmxlZnQ7XG4gICAgbGV0IHJlc3RvcmVfcm93IDo9IFthbm9ueW1vdXNdIG9uY2UgdmFyIHx8IC0+IHsgcmlnaHQ6IFN0cmluZyB9IHtcbiAgICAgICAgYW5vbnltb3VzLnJpZ2h0IDo9IFwiYmFja1wiO1xuICAgICAgICBhbm9ueW1vdXNcbiAgICB9O1xuICAgIGFzc2VydChyZXN0b3JlX3JvdygpLnJpZ2h0ID09IFwiYmFja1wiKTtcblxuICAgIGxldCBlbXB0eV9hbm9ueW1vdXMgOj0geyBvd25lZCA9IFwiZ29uZVwiIH07XG4gICAgbGV0IG93bmVkIDo9IGVtcHR5X2Fub255bW91cy5vd25lZDtcbiAgICBsZXQgZW1wdHlfY2FsbGJhY2sgOj0gW2VtcHR5X2Fub255bW91c10gb25jZSB8fCAtPiB7fSB7IGVtcHR5X2Fub255bW91cyB9O1xuICAgIGxldCBlbXB0eToge30gOj0gZW1wdHlfY2FsbGJhY2soKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlY29yZHMvcmVzaWR1YWxfY2FwdHVyZV9lbnRyeS5tdGwiLCJuYW1lIjoicmVzaWR1YWxfY2FwdHVyZV9lbnRyeS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZXNpZHVhbF9jYXB0dXJlX2luY29tcGxldGVfcmVzdG9yZS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUGFpciB7IGxlZnQ6IFN0cmluZywgcmlnaHQ6IFN0cmluZyB9XG5mdW4gbWFpbigpIHtcbiAgICB2YXIgcGFpciA6PSBQYWlyIHsgbGVmdCA9IFwib2xkXCIsIHJpZ2h0ID0gXCJnb25lXCIgfTtcbiAgICBsZXQgbGVmdCA6PSBwYWlyLmxlZnQ7XG4gICAgbGV0IHJpZ2h0IDo9IHBhaXIucmlnaHQ7XG4gICAgbGV0IGNhbGxiYWNrIDo9IFtwYWlyXSBvbmNlIHZhciB8fCAtPiBQYWlyIHsgLy8gRVJST1JbVDAwMDFdXG4gICAgICAgIHBhaXIubGVmdCA6PSBcIm5ld1wiO1xuICAgICAgICBwYWlyXG4gICAgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcmVzaWR1YWxfY2FwdHVyZV9pbmNvbXBsZXRlX3Jlc3RvcmUubXRsIiwibmFtZSI6InJlc2lkdWFsX2NhcHR1cmVfaW5jb21wbGV0ZV9yZXN0b3JlLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## References and moves

`&T` is `Copy`, so a shared reference is duplicated on use and the original stays valid.

`&var T` is **not** `Copy` — an exclusive reference must stay unique to be exclusive. It is
therefore moved on use, with one exception:

> **Since v0.12.0 (RFC-0071), behind `--move-check`:** `&var T` arguments reborrow.

Passing a `&var T` to an `&var T` parameter reborrows it rather than moving it, so the
original binding remains usable after the call. Every other use moves.

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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (6)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6Im5vbi1yZWJvcnJvdyB1c2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiIxMF9tdXRfcmVmX25vbl9yZWJvcnJvd19tb3ZlLm10bCIsInNvdXJjZSI6InN0cnVjdCBDb3VudGVyIHtcbiAgICB2YWx1ZTogaTY0LFxufVxuXG5mdW4gYnVtcChyOiAmdmFyIENvdW50ZXIpIHsgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgYyA6PSBDb3VudGVyIHsgdmFsdWUgPSAwIH07XG4gICAgbGV0IHIgOj0gJnZhciBjO1xuICAgIGxldCBxIDo9IHI7XG4gICAgYnVtcChyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svMTBfbXV0X3JlZl9ub25fcmVib3Jyb3dfbW92ZS5tdGwiLCJuYW1lIjoiMTBfbXV0X3JlZl9ub25fcmVib3Jyb3dfbW92ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnApYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI0OF9tb3ZlX3Rocm91Z2hfZXhwbGljaXRfZGVyZWZfaXNfYmFubmVkX29uX2ZpcnN0X3VzZS5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ4OiBhIHNoYXJlZCByZWZlcmVuY2Ugb25seSBldmVyIGdyYW50cyBhY2Nlc3MsIG5ldmVyIG93bmVyc2hpcCAoUkZDLTAwNzFcbi8vIFNTNy4xKSAtLSBtb3ZpbmcgYFN0cmluZ2AgKG5vbi1Db3B5KSBvdXQgb2YgYCpwYCBpcyBpbGxlZ2FsIG9uIHRoZSAqZmlyc3QqXG4vLyBjYWxsLCBub3QganVzdCBhIHJlcGVhdGVkIG9uZS4gQmVmb3JlICM2NDggdGhpcyBjb21waWxlZCBhbmQgb25seSB0aGVcbi8vIHNlY29uZCBgZWF0KCpwKWAgd2FzIHJlamVjdGVkLCBhcyBhbiBvcmRpbmFyeSB1c2UtYWZ0ZXItbW92ZSAtLSB0aGUgd3Jvbmdcbi8vIGRpYWdub3Npcywgc2luY2UgdGhlIGZpcnN0IG1vdmUgd2FzIG5ldmVyIGxlZ2FsIHRvIGJlZ2luIHdpdGguXG5mdW4gZWF0KHM6IFN0cmluZykgLT4gaTY0IHsgMSB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBzIDo9IFwiaGVsbG9cIjtcbiAgICBsZXQgcCA6PSAmcztcbiAgICBsZXQgZmlyc3QgOj0gZWF0KCpwKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNDhfbW92ZV90aHJvdWdoX2V4cGxpY2l0X2RlcmVmX2lzX2Jhbm5lZF9vbl9maXJzdF91c2UubXRsIiwibmFtZSI6IjQ4X21vdmVfdGhyb3VnaF9leHBsaWNpdF9kZXJlZl9pc19iYW5uZWRfb25fZmlyc3RfdXNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnIpYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI2NV9nZW5lcmFsX2Fzc2lnbm1lbnRfb3V0X29mX2FuX2V4cGxpY2l0X2RlcmVmX2lzX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Ii8vICM2NDgsIFJGQy0wMDcxIFNTNy4xJ3Mgb3duIG5hbWVkIGV4YW1wbGU6IGBsZXQgeDogQiA9ICpyO2AuXG5zdHJ1Y3QgQiB7IHY6IFN0cmluZyB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBiIDo9IEIgeyB2ID0gXCJ4XCIgfTtcbiAgICBsZXQgciA6PSAmYjtcbiAgICBsZXQgeDogQiA6PSAqcjtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNjVfZ2VuZXJhbF9hc3NpZ25tZW50X291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJuYW1lIjoiNjVfZ2VuZXJhbF9hc3NpZ25tZW50X291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBtb3ZlIGAoKnIpYCBvdXQgb2YgYSByZWZlcmVuY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI2Nl9ieV92YWx1ZV9hcmd1bWVudF9wYXNzaW5nX291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ4LCBSRkMtMDA3MSBTUzcuMSdzIG90aGVyIG5hbWVkIGV4YW1wbGU6IGBmKCpyKWAuXG5zdHJ1Y3QgQiB7IHY6IFN0cmluZyB9XG5cbmZ1biB0YWtlcyhiOiBCKSAtPiBTdHJpbmcge1xuICAgIGIudlxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYiA6PSBCIHsgdiA9IFwieFwiIH07XG4gICAgbGV0IHIgOj0gJmI7XG4gICAgbGV0IG4gOj0gdGFrZXMoKnIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay82Nl9ieV92YWx1ZV9hcmd1bWVudF9wYXNzaW5nX291dF9vZl9hbl9leHBsaWNpdF9kZXJlZl9pc19yZWplY3RlZC5tdGwiLCJuYW1lIjoiNjZfYnlfdmFsdWVfYXJndW1lbnRfcGFzc2luZ19vdXRfb2ZfYW5fZXhwbGljaXRfZGVyZWZfaXNfcmVqZWN0ZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjcwX3NoYXJlZF9yZWZlcmVuY2VfaXNfY29weS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3MSBcdTAwYTc5YSBpdGVtIDE6IGAmVGAgaXMgYENvcHlgIChhIHNoYXJlZCByZWZlcmVuY2UgbWF5IGJlIHVzZWRcbi8vIHJlcGVhdGVkbHkpOyBgJnZhciBUYCBpcyBub3QgKHNlZSAxMF9tdXRfcmVmX25vbl9yZWJvcnJvd19tb3ZlLm10bCBmb3IgdGhlXG4vLyBuZWdhdGl2ZSBoYWxmIC0tIG1vdmluZyBhIGAmdmFyIFRgIGJpbmRpbmcgYW5kIHRoZW4gdXNpbmcgaXQgYWdhaW4gaXNcbi8vIHJlamVjdGVkKS5cbmZ1biBzaG93KHI6ICZpNjQpIC0+IGk2NCB7ICpyIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHggOj0gNTtcbiAgICBsZXQgciA6PSAmeDtcbiAgICBhc3NlcnQoc2hvdyhyKSA9PSA1KTtcbiAgICBhc3NlcnQoc2hvdyhyKSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svNzBfc2hhcmVkX3JlZmVyZW5jZV9pc19jb3B5Lm10bCIsIm5hbWUiOiI3MF9zaGFyZWRfcmVmZXJlbmNlX2lzX2NvcHkubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6InJlZmVyZW5jZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMzcgc2xpY2UgMiAobWV0ZWwtY29yZSM4NTgpOiBuYXJyb3dpbmcgYW5kIHdpZGVuaW5nIGFwcGx5IG9ubHkgdG8gYW5cbi8vIG93bmVkIGJpbmRpbmcuIEEgbm9uLWBDb3B5YCBmaWVsZCBjYW5ub3QgYmUgbW92ZWQgb3V0IG9mIGEgdmFsdWUgcmVhY2hlZFxuLy8gdGhyb3VnaCBhIHJlZmVyZW5jZSAoUkZDLTAwNzEgXHUwMGE3Ny4xKSwgc28gdGhlcmUgaXMgbmV2ZXIgYSByZXNpZHVhbCB0byBuYXJyb3cgdG9cbi8vIG9yIHdpZGVuIGZyb20gYmVoaW5kIG9uZSBcdTIwMTQgdGhpcyBydWxlIGlzIHVuY2hhbmdlZCBieSBSRkMtMDEzNy5cbi8vXG4vLyBOZWVkcyBtb3ZlX2NoZWNrID0gdHJ1ZTogdGhlIG1vdmUtb3V0LW9mLWEtcmVmZXJlbmNlIGJhbiBpcyBhIG1vdmUtY2hlY2tlclxuLy8gcnVsZSwgbm90IG9uZSBvZiB0aGUgYWx3YXlzLW9uIHR5cGVjaGVjayBydWxlcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biBjb25zdW1lX25hbWUoaDogJnZhciBIYW5kbGUpIC0+IFN0cmluZyB7XG4gICAgbGV0IG4gOj0gaC5uYW1lOyAgIC8vIHJlamVjdGVkOiBtb3ZpbmcgYG5hbWVgIG91dCB0aHJvdWdoIGAmdmFyIEhhbmRsZWBcbiAgICBuXG59XG5cbmZ1biBtYWluKCkge1xuICAgIHZhciBoIDo9IEhhbmRsZSB7IGZkID0gMSwgbmFtZSA9IFwieFwiIH07XG4gICAgcHJpbnRsbihjb25zdW1lX25hbWUoJnZhciBoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL25lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ180N19ub19uYXJyb3dpbmdfdGhyb3VnaF9yZWZlcmVuY2UubXRsIn0="></details>
</details>
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
duplicated*. Neither answers *what is borrowed at a given point*, which is a borrow checker's job; see the
References section of the Type System page.

> **Gap** GAP-OWNERSHIP-001

## Known gaps

<!-- records:gaps -->
