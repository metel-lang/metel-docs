# Metel Error Code Reference

All Metel errors carry a code. Codes are prefixed by phase:

| Prefix | Phase |
|---|---|
| `P` | Parse — invalid source text |
| `T` | Type — type-checker rejection |
| `R` | Runtime — error during execution |
| `I` | Internal — bug in the interpreter (please report) |

---

## Parse errors (P)

### P0001 — Syntax error

The source text does not match the Metel grammar.

**Fix:** correct the syntax at the indicated position.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzA4X2NoYWluZWRfdHlwZV9hc2NyaXB0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDIxIFx1MDBhNzQ6IGFuIGV4cHJlc3Npb24gYWNjZXB0cyBhdCBtb3N0IG9uZSB0eXBlIGFzY3JpcHRpb24uXG5sZXQgdmFsdWUgOj0gMSA6IGk2NCA6IGk2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### P0002 — Invalid integer literal

An integer literal is out of range for `i64` (−9,223,372,036,854,775,808 to 9,223,372,036,854,775,807).

**Fix:** use a value that fits in `i64`, or split the computation.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAyIiwiY29sIjoiMTUiLCJjb250YWlucyI6bnVsbCwibGluZSI6IjEiLCJzdGF0dXMiOiJwYXJzZV9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ18wMl9pbnRfb3ZlcmZsb3cubXRsIiwic291cmNlIjoibGV0IHg6IGk2NCA6PSA5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uZWdfMDJfaW50X292ZXJmbG93Lm10bCIsIm5hbWUiOiJuZWdfMDJfaW50X292ZXJmbG93Lm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### P0003 — Invalid float literal

A float literal cannot be represented as an `f64`.

```
[P0003] parse error in main.mtl at 4..12: invalid float literal '1e9999'
```

**Fix:** use a value within the `f64` range (~±1.8 × 10³⁰⁸).

<!-- rfc.py:exemption kind="untestable" ref="metel-core#717" reason="Neither documented route is reachable: the grammar has no exponent notation, so a literal like `1e9999` is actually P0001, not P0003; and a literal long enough to overflow f64 in plain decimal notation silently saturates to infinity instead of erroring." -->

---

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Neither documented route is reachable: the grammar has no exponent notation, so a literal like `1e9999` is actually P0001, not P0003; and a literal long enough to overflow f64 in plain decimal notation silently saturates to infinity instead of erroring._</span>
<!-- rfc.py:exemption:rendered:end -->

## Type errors (T)

### T0001 — Type mismatch, or an impl that is not allowed

Two types that must be equal are not.

**Fix:** ensure the expression produces the expected type. Add an explicit cast if widening (e.g. `x as f64`).

The same code also covers an `extend` block the language does not permit, which is a
distinct situation sharing one code:

- a target that cannot carry the impl at all — `extend { … }: Drop` on an anonymous record;
- a target with nowhere to register, so its methods could never be found — a tuple, an
  anonymous record, a `fun` type, or an array whose element is not one of the impl's own
  type parameters. Only `extend<T> T[]: Aspect` — the array's element spelled exactly as
  one of the impl's own generics — is implemented today;
- a `drop` body, while destructor invocation is not yet implemented.

**Fix:** each message names the way forward — usually a named struct, or the generic form
where one exists.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzAyX2FzY3JpYmVfdHlwZV9taXNtYXRjaC5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA4IG5lZ2F0aXZlOiBhc2NyaXB0aW9uIHdpdGggaW5jb21wYXRpYmxlIHR5cGUgaXMgYSB0eXBlIGVycm9yLlxuLy8gYDEgOiBmNjRgIGlzIGFuIGVycm9yIFx1MjAxNCB1c2UgYDEgYXMgZjY0YCB0byBjb252ZXJ0LlxuXG5sZXQgejogZjY0IDo9IDEgOiBmNjQ7IC8vIEVSUk9SW1QwMDAxXVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYnVpbHRpbnMvc3RhZ2U4X25lZ18wMl9hc2NyaWJlX3R5cGVfbWlzbWF0Y2gubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDJfYXNjcmliZV90eXBlX21pc21hdGNoLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0002 — Annotation required

The type checker cannot infer a type without an explicit annotation.

**Fix:** annotate the binding: `let x: i64 = ...`.

The same code also covers dereferencing (`*expr`) an operand that isn't a reference type at
all — not an inference gap, but sharing the code with the annotation case above since both
are "the checker has nothing to work with here":

**Fix:** remove the `*`, or check that the operand actually has reference type (`&T` / `&var T`).

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjgiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTZfbmVnXzEyX3VucmVzb2x2ZWRfdmFyaWFudF9kZWZlcnJhbC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzI4NTogYSBiYXJlIHZhcmlhbnQgdGhhdCBuZXZlciByZXNvbHZlcyBtdXN0IGJlIHJlcG9ydGVkLCBub3Qgc2lsZW50bHlcbi8vIGFjY2VwdGVkLiBQYXNzIDEgZGVmZXJzIGl0IChSRkMtMDExMSBcdTAwYTczLjEpIGFuZCBvbmx5IHBhc3MgMiByZXNvbHZlcyBpdCBhZ2FpbnN0IGFuXG4vLyBleHBlY3RlZCB0eXBlIC0tIGJ1dCBhbiB1bmNhbGxlZCBjbG9zdXJlJ3MgYm9keSBpcyBuZXZlciBjb25zdHJ1Y3RlZCwgc28gbm8gZXhwZWN0ZWRcbi8vIHR5cGUgZXZlciBhcnJpdmVzIGFuZCBub3RoaW5nIHVzZWQgdG8gbm90aWNlLiBDaGVja2VkIGFmdGVyIHRoZSBmaW5hbCBzb2x2ZSBpbnN0ZWFkLlxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGYgOj0gfHwgeyBSZWQgfTsgLy8gRVJST1JbVDAwMDJdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9lbnVtcy9zdGFnZTZfbmVnXzEyX3VucmVzb2x2ZWRfdmFyaWFudF9kZWZlcnJhbC5tdGwiLCJuYW1lIjoic3RhZ2U2X25lZ18xMl91bnJlc29sdmVkX3ZhcmlhbnRfZGVmZXJyYWwubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0003 — Undefined name

A name is used but not defined in the current scope.

**Fix:** define the variable or function before use, or correct the spelling.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6InVuZGVmaW5lZCBuYW1lIGB2YWx1ZWAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMDNfYmluZGluZ19ub3RfdmlzaWJsZV9iZWZvcmVfZGVjbGFyYXRpb24ubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgbGV0IF9iZWZvcmUgOj0gdmFsdWU7XG4gICAgbGV0IHZhbHVlIDo9IDQyO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvZnVuY3Rpb25zL25lZ18wM19iaW5kaW5nX25vdF92aXNpYmxlX2JlZm9yZV9kZWNsYXJhdGlvbi5tdGwiLCJuYW1lIjoibmVnXzAzX2JpbmRpbmdfbm90X3Zpc2libGVfYmVmb3JlX2RlY2xhcmF0aW9uLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0004 — Arity mismatch

A function is called with the wrong number of arguments.

**Fix:** pass the exact number of arguments the function declares.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA0IiwiY29sIjpudWxsLCJjb250YWlucyI6InR5cGUgYXJndW1lbnQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMDJfYXJpdHkubXRsIiwic291cmNlIjoiLy8gUkZDLTAxNjAgXHUwMGE3MzogYW4gYWxpYXMgdXNlIG11c3Qgc3VwcGx5IGV4YWN0bHkgdGhlIGFsaWFzJ3MgZGVjbGFyZWQgbnVtYmVyIG9mXG4vLyB0eXBlIGFyZ3VtZW50cy5cbnR5cGUgUGFpcjxBLCBCPiA6PSAoQSwgQik7XG5mdW4gbWFpbigpIC0+IFBhaXI8aTY0PiB7ICgxLCAyKSB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci90eXBlX2FsaWFzZXMvbmVnXzAyX2FyaXR5Lm10bCIsIm5hbWUiOiJuZWdfMDJfYXJpdHkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0005 — Invalid operand types

An operator is applied to operands it does not support. Three forms share this code:

- **Mismatched operands.** The two sides of a binary operator disagree, e.g. `1 == "x"`.
  The message names the operator and both types.
- **Binary arithmetic/ordering** on unsupported types.
- **Equality** (`==`, `!=`) on anything other than a numeric type, `boolean`, `String` or
  `char`. `==` does not yet dispatch through the `Eq` aspect, so structs, enums, arrays,
  tuples and references are rejected; use `.eq(..)` on a type that implements `Eq`.

> **Since v0.12.0:** address-of (`&`, `&var`) applied to a non-addressable expression — a
> literal, a call result, a struct/enum construction — is no longer one of this code's
> cases. Both forms now get temporary lifetime extension instead of being rejected; see
> [Expressions — References](spec/expressions.md#references).

**Fix:** use compatible types, cast one operand, or bind the value to a name so it has an
address.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImdvdCBgaTY0YCBhbmQgYFN0cmluZ2AiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMDVfZ2VuZXJpY19maWVsZF9saXRlcmFsX2FkZF9zdHJpbmcubXRsIiwic291cmNlIjoiLy8gU2libGluZyBvZiBuZWdfMDEvbmVnXzAyLCBvbmUgbGV2ZWwgb2YgaW5kaXJlY3Rpb24gcmVtb3ZlZCAoIzIzNiBmb2xsb3ctdXApOlxuLy8gdGhlIG51bWVyaWMgbGl0ZXJhbCBoZXJlIGlzIHJlY292ZXJlZCB0aHJvdWdoIGEgZ2VuZXJpYyBzdHJ1Y3QgZmllbGQgcmF0aGVyXG4vLyB0aGFuIHdyaXR0ZW4gZGlyZWN0bHkgYXQgdGhlIGArYCBzaXRlLiBUaGUgVDAwMDUgbWVzc2FnZSBtdXN0IG5hbWUgdGhlXG4vLyBjb25jcmV0ZSB0eXBlIHRoaXMgcmVzb2x2ZXMgdG8gKGBpNjRgKSwgbm90IHRoZSBpbnRlcm5hbCBUeXBlVmFyIGl0IHdhc1xuLy8gdW5pZmllZCB3aXRoIFx1MjAxNCBzZWUgLnRvbWwgc2lkZWNhci5cbnN0cnVjdCBQYWlyPEEsIEI+IHsgZmlyc3Q6IEEsIHNlY29uZDogQiB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBwIDo9IFBhaXIgeyBmaXJzdCA9IDEsIHNlY29uZCA9IFwieFwiIH07XG4gICAgbGV0IF9iYWQgOj0gcC5maXJzdCArIFwieVwiOyAvLyBFUlJPUltUMDAwNV1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2xpdGVyYWxzL25lZ18wNV9nZW5lcmljX2ZpZWxkX2xpdGVyYWxfYWRkX3N0cmluZy5tdGwiLCJuYW1lIjoibmVnXzA1X2dlbmVyaWNfZmllbGRfbGl0ZXJhbF9hZGRfc3RyaW5nLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0006 — Assignment to immutable binding

A write operation targets a `let` binding. This covers three forms:

- Direct reassignment: `x = newValue`
- Field assignment through an immutable binding: `point.x = 1`
- Taking a mutable reference to an immutable binding: `&var x`

**Fix:** change the binding declaration to `var`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA2IiwiY29sIjoiNSIsImNvbnRhaW5zIjpudWxsLCJsaW5lIjoiMTYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMDlfcmVmX211dF9yZWNlaXZlcl9yZXF1aXJlc19tdXRhYmxlX2JpbmRpbmcubXRsIiwic291cmNlIjoiLy8gQ2FsbGluZyBhIG1ldGhvZCB3aG9zZSByZWNlaXZlciBpcyBgJnZhciBzZWxmYCByZXF1aXJlcyB0aGUgcmVjZWl2ZXJcbi8vIGV4cHJlc3Npb24gaXRzZWxmIHRvIGJlIGEgbXV0YWJsZSAoYHZhcmApIGJpbmRpbmcgLS0gYW4gaW1tdXRhYmxlIGBsZXRgXG4vLyBiaW5kaW5nIG9mIHRoZSBzYW1lIHN0cnVjdCB0eXBlIGlzIHJlamVjdGVkLlxuc3RydWN0IENvdW50ZXIge1xuICAgIHZhbHVlOiBpNjQsXG59XG5cbmV4dGVuZCBDb3VudGVyIHtcbiAgICBmdW4gaW5jcmVtZW50KCZ2YXIgc2VsZikge1xuICAgICAgICBzZWxmLnZhbHVlICs9IDE7XG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgY291bnRlciA6PSBDb3VudGVyIHsgdmFsdWUgPSAwIH07XG4gICAgY291bnRlci5pbmNyZW1lbnQoKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2FkZHJlc3NhYmlsaXR5L25lZ18wOV9yZWZfbXV0X3JlY2VpdmVyX3JlcXVpcmVzX211dGFibGVfYmluZGluZy5tdGwiLCJuYW1lIjoibmVnXzA5X3JlZl9tdXRfcmVjZWl2ZXJfcmVxdWlyZXNfbXV0YWJsZV9iaW5kaW5nLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0007 — Invalid cast

A `as` cast between incompatible types.

**Fix:** only cast between numeric types (`i64 as f64`). Use an explicit conversion function for other types.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA3IiwiY29sIjoiMjEiLCJjb250YWlucyI6bnVsbCwibGluZSI6IjExIiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2U2X25lZ18wNl9lcnJvcl9wcm9wYWdhdGlvbl9taXNtYXRjaGVkX3R5cGVzLm10bCIsInNvdXJjZSI6Ii8vID8gd2l0aCBtaXNtYXRjaGVkIGVycm9yIHR5cGVzIGFuZCBubyBGcm9tIGltcGwgbXVzdCBmYWlsIHdpdGggVDAwMDcuXG4vLyBNRVRFTC04MCByb3V0ZXMgPyB0aHJvdWdoIEZyb20tYmFzZWQgY29lcmNpb247IHdoZW4gbm8gRnJvbSBpbXBsIGV4aXN0cyxcbi8vIHRoZSBjb2VyY2lvbiBpcyBpbnZhbGlkIGFuZCB0aGUgdHlwZWNoZWNrZXIgZW1pdHMgVDAwMDcgKGludmFsaWQgY2FzdCkuXG4vLyBGcm9tIGNvZXJjaW9uIGZvciBhcmJpdHJhcnkgdHlwZSBwYWlycyBpcyBkZWZlcnJlZCB0byAjMTMuXG5cbmZ1biBpbm5lcigpIC0+IFJlc3VsdDxpNjQsIFN0cmluZz4ge1xuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDQyIH1cbn1cblxuZnVuIG91dGVyKCkgLT4gUmVzdWx0PGk2NCwgaTY0PiB7XG4gICAgbGV0IHggOj0gaW5uZXIoKT87IC8vIEVSUk9SW1QwMDA3XVxuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IHggfVxufVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9lcnJvcl9oYW5kbGluZy9zdGFnZTZfbmVnXzA2X2Vycm9yX3Byb3BhZ2F0aW9uX21pc21hdGNoZWRfdHlwZXMubXRsIiwibmFtZSI6InN0YWdlNl9uZWdfMDZfZXJyb3JfcHJvcGFnYXRpb25fbWlzbWF0Y2hlZF90eXBlcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0008 — Non-exhaustive match

A `match` expression does not cover all possible values of the scrutinee type.

**Fix:** add the missing arms, or add a wildcard arm `_ => ...`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA4IiwiY29sIjoiNSIsImNvbnRhaW5zIjoibm9uLWV4aGF1c3RpdmUgbWF0Y2giLCJsaW5lIjoiNiIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ18xN19iYXJlX3ZhcmlhbnRfaXNfbm90X2NhdGNoYWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA3IFx1MDBhNzI6IGEgYmFyZSB2YXJpYW50IHRhZyBpcyByZXdyaXR0ZW4gYmVmb3JlIGV4aGF1c3RpdmVuZXNzIGNoZWNraW5nO1xuLy8gaXQgaXMgbm90IGEgY2F0Y2gtYWxsIGJpbmRpbmcuXG5lbnVtIENvbG91ciB7IFJlZCwgQmx1ZSB9XG5cbmZ1biBuYW1lKGM6IENvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gXCJyZWRcIixcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2VudW1zL25lZ18xN19iYXJlX3ZhcmlhbnRfaXNfbm90X2NhdGNoYWxsLm10bCIsIm5hbWUiOiJuZWdfMTdfYmFyZV92YXJpYW50X2lzX25vdF9jYXRjaGFsbC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0012 — Aspect bound not satisfied

A generic type parameter's bound is not satisfied by the concrete type at the call
site or construction site. Covers both directions: a positive bound (`T: Aspect`)
requires an implementation that isn't reachable, or a negative bound (`T: !Aspect`,
RFC-0072) is violated because the concrete type *does* implement the aspect. Also
covers a conditional `extend` block's own `where`-clause bounds (RFC-0036) failing at a
use site — the same check as an ordinary function bound, just reached through an
implementation block's
condition instead of a function's generic parameter.

A type satisfying `T: Copy` automatically satisfies `T: !Drop` (RFC-0072 §2.3) even
though it implements `Drop` — this is a narrow, Copy/Drop-specific exception, not a
general rule.

**Fix:** implement the required aspect for the type, or (for a negative bound) remove
the conflicting positive implementation.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6ImRvZXMgbm90IGltcGxlbWVudCBgRGlzcGxheWAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzAyX3ByaW50bG5fcmVxdWlyZXNfZGlzcGxheS5tdGwiLCJzb3VyY2UiOiIvLyBwcmludGxuL3ByaW50IHJlcXVpcmUgRGlzcGxheSAoTUVURUwtMTgxKTogcGFzc2luZyBhIHR5cGUgd2l0aCBub1xuLy8gRGlzcGxheSBpbXBsIGlzIGEgY29tcGlsZS10aW1lIGVycm9yLCBub3QgYSBydW50aW1lIHBhbmljLlxuXG5zdHJ1Y3QgVGVzdCB7XG4gICAgYXR0cjogaTgsXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB4IDo9IFRlc3QgeyBhdHRyID0gMWk4IH07XG4gICAgcHJpbnRsbih4KTsgLy8gRVJST1JbVDAwMTJdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9idWlsdGlucy9zdGFnZThfbmVnXzAyX3ByaW50bG5fcmVxdWlyZXNfZGlzcGxheS5tdGwiLCJuYW1lIjoic3RhZ2U4X25lZ18wMl9wcmludGxuX3JlcXVpcmVzX2Rpc3BsYXkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0013 — Ambiguous aspect method/associated-type resolution

Two different aspects define the same method name on the same receiver type, so a
call like `value.method()` does not have a unique static target — or (RFC-0082 §3a)
two different aspects bound on the same generic type parameter both declare an
associated type of the same name, so a bare projection like `T::AssocName` doesn't
have a unique target either.

**Fix (method case):** rename one of the methods, remove one of the conflicting impls,
or change the design so the receiver type does not expose two indistinguishable
aspect methods.

**Fix (associated-type case):** bind the associated type to a fresh type parameter via
an equality-constrained bound instead of projecting it directly — e.g.
`fun f<T: Deref<Target = U> + Convert, U>(x: &T) -> U` — which resolves unambiguously
since `U` is an ordinary type parameter, not a projection.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjExIiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxM19uZWdfMTJfYW1iaWd1b3VzX2Fzc29jaWF0ZWRfcHJvamVjdGlvbi5tdGwiLCJzb3VyY2UiOiJhc3BlY3QgRGVyZWYge1xuICAgIHR5cGUgVGFyZ2V0O1xuICAgIGZ1biBkZXJlZigmc2VsZikgLT4gVGFyZ2V0O1xufVxuXG5hc3BlY3QgQ29udmVydCB7XG4gICAgdHlwZSBUYXJnZXQ7XG4gICAgZnVuIGNvbnZlcnQoJnNlbGYpIC0+IFRhcmdldDtcbn1cblxuZnVuIGFtYmlndW91czxUOiBEZXJlZiArIENvbnZlcnQ+KHg6ICZUKSAtPiBUOjpUYXJnZXQge1xuICAgIHguZGVyZWYoKVxufVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL3N0YWdlMTNfbmVnXzEyX2FtYmlndW91c19hc3NvY2lhdGVkX3Byb2plY3Rpb24ubXRsIiwibmFtZSI6InN0YWdlMTNfbmVnXzEyX2FtYmlndW91c19hc3NvY2lhdGVkX3Byb2plY3Rpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0014 — Orphan implementation

An `extend Type: Aspect` block where neither `Aspect` nor `Type`'s outermost type
constructor is declared in the current module (or `std::core`, for built-ins).

**Fix:** move the `extend` block into the module that declares the aspect or the type, or (for
two foreign types) into `std::core` if this is genuinely a standard-library concern.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE0IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDk3OiBhIGJhcmUtcGFyYW1ldGVyIGJsYW5rZXQgaW1wbCBjYW4gbmV2ZXIgc2F0aXNmeSB0aGUgb3JwaGFuIHJ1bGUgdmlhXG4vLyB0aGUgdGFyZ2V0IHNpZGUsIHNpbmNlIGJhcmUgYFRgIGhhcyBubyBkZWNsYXJpbmcgbW9kdWxlIGF0IGFsbC4gVXNpbmcgYVxuLy8gZm9yZWlnbiBhc3BlY3QgbXVzdCB0aGVyZWZvcmUgYmUgcmVqZWN0ZWQuXG5cbmV4dGVuZDxUPiBUOiBEaXNwbGF5IHsgLy8gRVJST1JbVDAwMTRdXG4gICAgZnVuIHRvX3N0cmluZyhzZWxmKSAtPiBTdHJpbmcge1xuICAgICAgICByZXR1cm4gXCI/XCI7XG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2JhcmVfcGFyYW1ldGVyX2JsYW5rZXRfZm9yZWlnbl9hc3BlY3RfaXNfb3JwaGFuIiwibmFtZSI6ImJhcmVfcGFyYW1ldGVyX2JsYW5rZXRfZm9yZWlnbl9hc3BlY3RfaXNfb3JwaGFuIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0015 — Conflicting implementation

Two implementations of the same aspect cover the same concrete type — either two
identical `extend` blocks, or a positive and a negative impl (see Negative Impls in the declarations
reference) for the same concrete type.

**Fix:** remove the duplicate `extend` block, or narrow one block's type arguments so the two no
longer overlap.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE1IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIwIiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA2MCBcdTAwYTcyOiBhIGJsYW5rZXQgaW1wbCBhbmQgYSBjb25jcmV0ZSBpbXBsIG9mIHRoZSBzYW1lIGFzcGVjdFxuLy8gY29uZmxpY3Qgd2hlbiB0aGUgY29uY3JldGUgaW5zdGFudGlhdGlvbiBpcyBhbHJlYWR5IGNvdmVyZWQgYnkgdGhlXG4vLyBibGFua2V0IC0tIHRoZSBwcmUtIzI0NCBvdmVybGFwIGNoZWNrIG9ubHkgZXZlciBjb21wYXJlZCBpZGVudGljYWxseS1cbi8vIHNoYXBlZCBjYW5vbmljYWwgdGFyZ2V0cywgc28gdGhpcyBzaGFwZS1jcm9zc2luZyBwYWlyIHNpbGVudGx5IG1pc3NlZFxuLy8gZWFjaCBvdGhlci4gRml4ZWQgYnkgdHJlYXRpbmcgVHlwZVBhcmFtIGFzIGEgd2lsZGNhcmQgd2hlbiBjb21wYXJpbmdcbi8vIGNhbm9uaWNhbGl6ZWQgdGFyZ2V0cyAoaXNzdWUgIzI0NCkuXG5cbmFzcGVjdCBNYXJrZXIge1xuICAgIGZ1biBtYXJrKHNlbGYpIC0+IFN0cmluZztcbn1cblxuc3RydWN0IEZvbzxUPiB7XG4gICAgdmFsdWU6IFQsXG59XG5cbmV4dGVuZDxUPiBGb288VD46IE1hcmtlciB7XG4gICAgZnVuIG1hcmsoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwiYmxhbmtldFwiOyB9XG59XG5cbmV4dGVuZCBGb288aTY0PjogTWFya2VyIHsgLy8gRVJST1JbVDAwMTVdXG4gICAgZnVuIG1hcmsoc2VsZikgLT4gU3RyaW5nIHsgcmV0dXJuIFwiY29uY3JldGVcIjsgfVxufVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL2JsYW5rZXRfdnNfY29uY3JldGVfaW1wbF9jb25mbGljdCIsIm5hbWUiOiJibGFua2V0X3ZzX2NvbmNyZXRlX2ltcGxfY29uZmxpY3QifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0016 — Non-diverging `-> !` function

A function declared `-> !` (RFC-0078) contains a reachable path that doesn't
diverge — most commonly an ordinary `return <expr>` where `<expr>` isn't itself
`!`-typed. A `-> !` function promises never to return; the compiler verifies
every control-flow path ends in a diverging expression (a `panic`, a `loop`
with no reachable `break`, or a `return`/tail expression whose own value is
already `!`-typed).

**Fix:** make every path genuinely diverge (`panic(msg)`, `loop { }`, or a
recursive/other `!`-returning call), or drop the `-> !` annotation if the
function is meant to return normally.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE2IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZXZlcl9uZWdfMDFfcmV0X25ldmVyX3JlYWNoYWJsZV9yZXR1cm4ubXRsIiwic291cmNlIjoiLy8gTmVnYXRpdmU6IFJGQy0wMDc4IFx1MDBhNzYgLS0gYSBmdW5jdGlvbiBkZWNsYXJlZCBgLT4gIWAgY29udGFpbmluZyBhIHJlYWNoYWJsZSxcbi8vIG9yZGluYXJ5IGByZXR1cm5gIChvbmUgd2hvc2UgdmFsdWUgaXMgTk9UIGl0c2VsZiBgIWAtdHlwZWQpIGlzIGEgdHlwZSBlcnJvcjpcbi8vIHRoZSBmdW5jdGlvbiBhY3R1YWxseSByZXR1cm5zLCB3aGljaCBgLT4gIWAgZm9yYmlkcy5cblxuZnVuIGJhZCgpIC0+ICEgeyAvLyBFUlJPUltUMDAxNl1cbiAgICByZXR1cm4gNTtcbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfbmVnXzAxX3JldF9uZXZlcl9yZWFjaGFibGVfcmV0dXJuLm10bCIsIm5hbWUiOiJuZXZlcl9uZWdfMDFfcmV0X25ldmVyX3JlYWNoYWJsZV9yZXR1cm4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0017 — Missing associated type definition

An `extend Type: Aspect` block omits a `type Name = ConcreteType;` definition for an
associated type the aspect declares (RFC-0082 §2). Every implementation of an aspect with
associated types must define all of them.

**Fix:** add the missing `type Item = ConcreteType;` definition to the `extend` block.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE3IiwiY29sIjpudWxsLCJjb250YWlucyI6ImFzc29jaWF0ZWQgdHlwZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ180NV9taXNzaW5nX2Fzc29jaWF0ZWRfdHlwZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA4MiBcdTAwYTcyOiBldmVyeSBpbXBsZW1lbnRhdGlvbiBvZiBhbiBhc3BlY3Qgd2l0aCBhc3NvY2lhdGVkIHR5cGVzIG11c3Rcbi8vIGRlZmluZSBhbGwgb2YgdGhlbSAtLSBgSW50Qm94YCdzIGV4dGVuZCBibG9jayBvbWl0cyBgdHlwZSBJdGVtYC5cbmFzcGVjdCBDb250YWluZXIge1xuICAgIHR5cGUgSXRlbTtcbiAgICBmdW4gZ2V0KCZzZWxmKSAtPiBJdGVtO1xufVxuXG5zdHJ1Y3QgSW50Qm94IHsgdjogaTY0IH1cblxuZXh0ZW5kIEludEJveDogQ29udGFpbmVyIHtcbiAgICBmdW4gZ2V0KCZzZWxmKSAtPiBpNjQgeyBzZWxmLnYgfVxufVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hc3BlY3RzL25lZ180NV9taXNzaW5nX2Fzc29jaWF0ZWRfdHlwZS5tdGwiLCJuYW1lIjoibmVnXzQ1X21pc3NpbmdfYXNzb2NpYXRlZF90eXBlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0018 — Naming the concrete type of an opaque return value

A function returning `extends Aspect` (RFC-0037) hides its concrete return type. Using the
result in a position that pins it to a specific type — annotating it, or unifying it with a
concrete type — defeats that, and is rejected.

**Fix:** keep the value opaque — annotate it as `extends Aspect` too, or accept it through a
generic parameter with the same bound.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE4IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjI2Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2UxOF9uZWdfMDNfcmV0dXJuX2ltcGxfYXNwZWN0X2NhbGxlcl9jYW5ub3RfbmFtZS5tdGwiLCJzb3VyY2UiOiIvLyBOZWdhdGl2ZTogY2FsbGVyIGNhbm5vdCBuYW1lIGNvbmNyZXRlIHR5cGUgc2hvdWxkIGZhaWwgd2l0aCBUMDAxOFxuLy8gQXR0ZW1wdGluZyB0byBhc3NpZ24gb3BhcXVlIHJldHVybiB0byBjb25jcmV0ZSB0eXBlIHZhcmlhYmxlXG5cbmFzcGVjdCBEaXNwbGF5IHtcblx0ZnVuIGRpc3BsYXkoJnNlbGYpIC0+IFN0cmluZztcbn1cblxuc3RydWN0IE15SW50IHtcblx0dmFsdWU6IGk2NCxcbn1cblxuZXh0ZW5kIE15SW50OiBEaXNwbGF5IHtcblx0ZnVuIGRpc3BsYXkoJnNlbGYpIC0+IFN0cmluZyB7XG5cdFx0c2VsZi52YWx1ZS50b19zdHJpbmcoKVxuXHR9XG59XG5cbi8vIEZ1bmN0aW9uIHJldHVybmluZyBleHRlbmRzIERpc3BsYXlcbmZ1biBtYWtlX2ludCgpIC0+IGV4dGVuZHMgRGlzcGxheSB7XG5cdE15SW50IHsgdmFsdWUgPSA0MiB9XG59XG5cbmZ1biBtYWluKCkge1xuXHRsZXQgaW50X3ZhbCA6PSBtYWtlX2ludCgpO1xuXHQvLyBUaGlzIHNob3VsZCBmYWlsIC0gY2Fubm90IG5hbWUgdGhlIGNvbmNyZXRlIHR5cGUgb2Ygb3BhcXVlIHJldHVyblxuXHRsZXQgY29uY3JldGU6IE15SW50IDo9IGludF92YWw7IC8vIEVSUk9SW1QwMDE4XVxufSJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3N0YWdlMThfbmVnXzAzX3JldHVybl9pbXBsX2FzcGVjdF9jYWxsZXJfY2Fubm90X25hbWUubXRsIiwibmFtZSI6InN0YWdlMThfbmVnXzAzX3JldHVybl9pbXBsX2FzcGVjdF9jYWxsZXJfY2Fubm90X25hbWUubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0019 — Use of moved value

> **Since v0.12.0, under `--move-check` only.** Move checking is off by default in this release.

An ownership rule from RFC-0071 §1/§7 was violated. Seven distinct situations share this
code, each with its own message:

- a value used after it was moved;
- a partially moved value used as a whole;
- a partial move out of a type that implements `Drop`, which is never allowed;
- a move out of an array element, which is banned outright;
- a move of a non-`Copy` element out of a borrowed `T[]` view;
- a `&var` binding moved by a use that is not a reborrow;
- a value moved out of a reference — by calling a by-value `self` method through it,
  in general assignment or by-value argument position, or by reading a field through it
  with no explicit `*` at all. A reference only grants access, never ownership, so its
  pointee cannot be moved out this way, unless the pointee's own type is `Copy` (in which
  case the read is a copy, exactly as `T: Copy` already permits at read-copy positions
  per §3a).

Each message names the binding and the location of the move. When the move happened on an
earlier iteration of an enclosing loop, the message says so — a loop-carried move is
usually the *same* expression as the use, one iteration later, so naming only its location
would point back at the line you are already reading.

**Fix:** depending on the rule — borrow instead of moving (`&x`), clone the value, move the
whole value rather than a field of a `Drop` type, or index-and-copy rather than moving an
element out of an array.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6Im1vdmVkIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoidjBfMTNfMF9uZWdfdXNlX2FmdGVyX21vdmVfY2FwdHVyZS5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xMy4wIGNsb3N1cmUgY2x1c3RlciAoUkZDIDAxNTcgRDUpOiBgW3NdYCBtb3ZlcyBhIG5vbi1Db3B5IGJpbmRpbmcgaW50b1xuLy8gdGhlIGNsb3N1cmUsIGNvbnN1bWluZyB0aGUgb3V0ZXIgYmluZGluZy4gVXNpbmcgaXQgYWZ0ZXJ3YXJkIGlzIHRoZVxuLy8gb3JkaW5hcnkgbW92ZWQtdmFsdWUgZXJyb3IgKFJGQyAwMTM0IFx1MDBhNzIgY2l0ZXMgVDAwMTkncyBleGlzdGluZyBzaGFwZSkuXG4vL1xuLy8gTmVlZHMgbW92ZV9jaGVjayA9IHRydWU6IHRoaXMgaXMgdGhlIGdlbmVyYWwgYWZmaW5lLW1vdmUgY2hlY2sgKFJGQyAwMDcxKSxcbi8vIG5vdCBvbmUgb2YgdGhlIGNsb3N1cmUtc3BlY2lmaWMgYWx3YXlzLW9uIGNoZWNrcyAoQURSLTAwNTIgXHUwMGE3MSkuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBcImhlbGxvXCI7XG4gICAgbGV0IGdyZWV0IDo9IFtzXSBvbmNlIHx8IHsgcyB9O1xuICAgIHByaW50bG4ocyk7IC8vIG1vdmVkLXZhbHVlIGVycm9yIC0tIGBzYCB3YXMgbW92ZWQgaW50byBgZ3JlZXRgXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jbG9zdXJlcy92MF8xM18wX25lZ191c2VfYWZ0ZXJfbW92ZV9jYXB0dXJlLm10bCIsIm5hbWUiOiJ2MF8xM18wX25lZ191c2VfYWZ0ZXJfbW92ZV9jYXB0dXJlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0021 — `break`/`continue` with no enclosing loop

`break` or `continue` appeared with no enclosing loop of any kind (`loop`, `while`, `for`,
or `for-in`) to bind to. This includes a `break`/`continue` written inside a closure body
— a closure is never considered to be "inside" whatever loop happens to lexically
surround its definition, since the closure may be called long after that loop has exited,
or from somewhere the loop never ran at all.

**Fix:** remove the keyword, or move it inside the loop it is meant to control. If it is
meant to control a loop that encloses the *call site* of a closure rather than the
closure's own definition, restructure the code — a closure cannot break or continue a
loop it does not itself contain.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDIxIiwiY29sIjpudWxsLCJjb250YWlucyI6Im5vIGVuY2xvc2luZyBsb29wIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX2JyZWFrX291dHNpZGVfbG9vcC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBicmVhaztcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2NvbnRyb2xfZmxvdy9uZWdfYnJlYWtfb3V0c2lkZV9sb29wLm10bCIsIm5hbWUiOiJuZWdfYnJlYWtfb3V0c2lkZV9sb29wLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0022 — `extends Aspect` outside parameter or return position

`extends Aspect` was written somewhere other than a function parameter's type or a
function's return type — for example, a `let`/`var` annotation, a struct or enum
variant field, a cast target (`x as extends P`), or a generic bound. Parameter position is
lowered to a fresh bounded type parameter, and return position is RFC-0037's opaque
return type; every other position is not part of this language version.

**Fix:** name a concrete type instead, or restructure the code so the aspect bound is
expressed through a parameter or return type.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDIyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjkiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTE4X25lZ18wOF9pbXBsX2FzcGVjdF9sb2NhbF9sZXRfYXJyYXkubXRsIiwic291cmNlIjoiLy8gTmVnYXRpdmU6IGBleHRlbmRzIEFzcGVjdGAgaXMgbm90IHBlcm1pdHRlZCBpbnNpZGUgYSBsb2NhbCBsZXQgYW5ub3RhdGlvbi5cbmFzcGVjdCBQIHsgZnVuIHAoJnNlbGYpOyB9XG5cbnN0cnVjdCBMIHsgdDogU3RyaW5nIH1cblxuZXh0ZW5kIEw6IFAgeyBmdW4gcCgmc2VsZikge30gfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdmFsdWVzOiBleHRlbmRzIFBbXSA6PSBbTCB7IHQgPSBcInhcIiB9XTsgLy8gRVJST1JbVDAwMjJdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9nZW5lcmljcy9zdGFnZTE4X25lZ18wOF9pbXBsX2FzcGVjdF9sb2NhbF9sZXRfYXJyYXkubXRsIiwibmFtZSI6InN0YWdlMThfbmVnXzA4X2ltcGxfYXNwZWN0X2xvY2FsX2xldF9hcnJheS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0023 — Assignment through a non-owning view

An index assignment targets a `T[]` value. Since RFC-0126, `T[]` is an unconditionally
`Copy`, non-owning view — it never grants write access through its indices, independent
of whether the binding holding it is `let` or `var`. This is a different failure shape
than T0006 (all three of T0006's forms are about a `let` binding that declaring it `var`
would fix); no annotation or binding-mutability change can fix this one.

**Fix:** use `[T; N]` (a fixed-size array) or `List<T>` (a growable, owned collection)
instead of `T[]` for storage that needs index-write access.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDIzIiwiY29sIjpudWxsLCJjb250YWlucyI6ImFycmF5IHZpZXdzIGFyZSBpbW11dGFibGUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfYXJyYXlfdmlld19pbmRleF9hc3NpZ24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMjY6IGBUW11gIGlzIGFuIHVuY29uZGl0aW9uYWxseSBDb3B5LCBub24tb3duaW5nIHZpZXcgLS0gaXQgbmV2ZXJcbi8vIGdyYW50cyB3cml0ZSBhY2Nlc3MgdGhyb3VnaCBpdHMgaW5kaWNlcywgcmVnYXJkbGVzcyBvZiBsZXQvdmFyLlxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGE6IGk2NFtdIDo9IFsxLCAyLCAzXTtcbiAgICBhWzB1NjRdIDo9IDU7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy90eXBlcy9uZWdfYXJyYXlfdmlld19pbmRleF9hc3NpZ24ubXRsIiwibmFtZSI6Im5lZ19hcnJheV92aWV3X2luZGV4X2Fzc2lnbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0024 — Read-copy of a non-`Copy` value out of a reference

> **Since v0.12.1.**

RFC-0067a §3a's "read-copy": a `let`/`mut` binding, `return`/`break` value, tail
expression, or explicit ascription (`expr: T`) whose own declared type differs from
its initializer's reference type (`&U`/`&var U`) implicitly copies the referent out —
but only when `U` is `Copy`. A reference only grants access, never ownership, so
reading a non-`Copy` value out this way would silently duplicate it with no move and
no explicit clone.

Checked once against the fully-dereferenced type at the end of a reference chain, not
each intermediate layer — `let x: i64 = rr;` where `rr: &&i64` is unaffected, since
`i64` is `Copy` regardless of how many reference layers it's read through.

**Fix:** call `.clone()` if the type implements `Clone`, or restructure the code to
take ownership of the value directly instead of reading it through a reference.

---

The closure cluster reserves the contiguous T0026–T0030 block, split below so each
code's own coverage is visible rather than folded into one shared entry (an
implementation gap in only one of the five would otherwise hide behind the other four).

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDI0IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzE0X3JlYWRfY29weV9vZl9ub25fY29weV92YWx1ZV9hdF9sZXRfaXNfcmVqZWN0ZWQubXRsIiwic291cmNlIjoiLy8gVFlQRUNIRUNLX0VSUk9SW1QwMDI0XVxuLy8gIzY0OTogUkZDLTAwNjdhIFx1MDBhNzNhJ3MgcmVhZC1jb3B5IHJlcXVpcmVzIHRoZSByZWZlcmVudCB0byBiZSBgQ29weWAgLS0gcmVhZGluZyBhXG4vLyBub24tYENvcHlgIHZhbHVlIG91dCBvZiBhIHNoYXJlZCByZWZlcmVuY2UgYXQgYSBgbGV0YCBiaW5kaW5nIG11c3QgYmUgcmVqZWN0ZWQsXG4vLyBub3Qgc2lsZW50bHkgZHVwbGljYXRlZC5cbnN0cnVjdCBOb3RDb3B5IHsgdjogU3RyaW5nIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IG93bmVkIDo9IE5vdENvcHkgeyB2ID0gXCJ4XCIgfTtcbiAgICBsZXQgcjogJk5vdENvcHkgOj0gJm93bmVkO1xuICAgIGxldCBjb3B5OiBOb3RDb3B5IDo9IHI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzL25lZ18xNF9yZWFkX2NvcHlfb2Zfbm9uX2NvcHlfdmFsdWVfYXRfbGV0X2lzX3JlamVjdGVkLm10bCIsIm5hbWUiOiJuZWdfMTRfcmVhZF9jb3B5X29mX25vbl9jb3B5X3ZhbHVlX2F0X2xldF9pc19yZWplY3RlZC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0026 — Capture list required, incomplete, or incompatible

> **Availability:** Since v0.13.0.

A capture list is required, incomplete, or uses an incompatible capture form.

**Fix:** use the capture list the closure body's captures actually require.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDI2IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhcHR1cmUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJ2MF8xM18wX25lZ19jYXB0dXJlX2xpc3RfcmVxdWlyZWQubXRsIiwic291cmNlIjoiLy8gdjAuMTMuMCBjbG9zdXJlIGNsdXN0ZXIgKFJGQyAwMDUwIGxlZ2FsaXR5LTYpOiBhIGNsb3N1cmUgbXVzdCBjYXJyeSBhXG4vLyBjYXB0dXJlIGxpc3QgaWYgaXRzIGJvZHkgcmVmZXJlbmNlcyBhIGZyZWUgbm9uLUNvcHkgbG9jYWwgYmluZGluZy5cbi8vXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgbmFtZSA6PSBcImxvZ1wiO1xuICAgIGxldCBncmVldCA6PSB8fCB7IG5hbWUgfTsgLy8gbWlzc2luZyBjYXB0dXJlIGxpc3QgZm9yIGBuYW1lYFxuICAgIGFzc2VydChncmVldCgpID09IFwibG9nXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY2xvc3VyZXMvdjBfMTNfMF9uZWdfY2FwdHVyZV9saXN0X3JlcXVpcmVkLm10bCIsIm5hbWUiOiJ2MF8xM18wX25lZ19jYXB0dXJlX2xpc3RfcmVxdWlyZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0027 — Consuming capture without `once`

> **Availability:** Since v0.13.0.

A closure body consumes a capture but the literal/type is not `once`.

**Fix:** mark the closure `once`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDI3IiwiY29sIjpudWxsLCJjb250YWlucyI6Im9uY2UiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJ2MF8xM18wX25lZ19vbmNlX3JlcXVpcmVkX2Zvcl9jb25zdW1pbmdfYm9keS5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xMy4wIGNsb3N1cmUgY2x1c3RlciAoUkZDIDAxMzQgbGVnYWxpdHktOCk6IGEgY2xvc3VyZSB3aG9zZSBib2R5IG1vdmVzXG4vLyBhIG5vbi1Db3B5IGNhcHR1cmUgb3V0IG11c3QgYmUgd3JpdHRlbiBgb25jZWA7IG9taXR0aW5nIGl0IGlzIGEgY29tcGlsZVxuLy8gZXJyb3IgYXQgdGhlIGRlZmluaXRpb24gc2l0ZS5cbi8vXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgcyA6PSBcImhlbGxvXCI7XG4gICAgbGV0IHRha2UgOj0gW3NdIHx8IHsgcyB9OyAvLyBtb3ZlcyBgc2Agb3V0OyBtaXNzaW5nIGBvbmNlYFxuICAgIHRha2UoKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2Nsb3N1cmVzL3YwXzEzXzBfbmVnX29uY2VfcmVxdWlyZWRfZm9yX2NvbnN1bWluZ19ib2R5Lm10bCIsIm5hbWUiOiJ2MF8xM18wX25lZ19vbmNlX3JlcXVpcmVkX2Zvcl9jb25zdW1pbmdfYm9keS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### T0028 — Mutating capture without `var`

> **Availability:** Since v0.13.0.

A closure body mutates a capture, or uses `[&var x]`, but is not `var`.

**Fix:** mark the closure `var`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDI4IiwiY29sIjpudWxsLCJjb250YWlucyI6InZhciB8Li4ufCB7IC4uLiB9IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoidjBfMTNfMF9uZWdfcmVmdmFyX2NhcHR1cmVfbmVlZHNfdmFyX3F1YWxpZmllci5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xMy4wIGNsb3N1cmUgY2x1c3RlciAoUkZDIDAxNTMgbGVnYWxpdHktMjUgLyBtZXRlbC1jb3JlIzk1OSk6IGEgYFsmdmFyIHhdYFxuLy8gY2FwdHVyZSBvdmVyIGEgYHZhcmAgYmluZGluZyBzdGlsbCByZXF1aXJlcyB0aGUgYHZhcmAgcXVhbGlmaWVyIG9uIHRoZSBjbG9zdXJlXG4vLyBsaXRlcmFsIGl0c2VsZi4gVGhlIGRpYWdub3N0aWMgbmFtZXMgdGhlIHBpcGUgc3BlbGxpbmcgaW50cm9kdWNlZCBieSBSRkMtMDE1NFxuLy8gLS0gYFsuLi5dIHZhciB8Li4ufCB7IC4uLiB9YCAtLSBub3QgdGhlIHBhcmVudGhlc2l6ZWQgZm9ybSB0aGF0IFJGQyByZW1vdmVkLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIGNvdW50IDo9IDA7XG4gICAgbGV0IGJ1bXAgOj0gWyZ2YXIgY291bnRdIHx8IHsgY291bnQgOj0gY291bnQgKyAxOyB9OyAvLyBtaXNzaW5nIGB2YXJgIHF1YWxpZmllclxuICAgIGJ1bXAoKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2Nsb3N1cmVzL3YwXzEzXzBfbmVnX3JlZnZhcl9jYXB0dXJlX25lZWRzX3Zhcl9xdWFsaWZpZXIubXRsIiwibmFtZSI6InYwXzEzXzBfbmVnX3JlZnZhcl9jYXB0dXJlX25lZWRzX3Zhcl9xdWFsaWZpZXIubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### T0029 — `var` closure called through a shared reference

> **Availability:** Since v0.13.0.

A `var` closure is called through a shared reference.

**Fix:** call through an owned binding or an exclusive (`&var`) reference instead.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDI5IiwiY29sIjpudWxsLCJjb250YWlucyI6InNoYXJlZCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzEzXzBfbmVnX3Zhcl9jYWxsX3Rocm91Z2hfc2hhcmVkX3JlZi5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xMy4wIGNsb3N1cmUgY2x1c3RlciAoUkZDIDAxNTMgbGVnYWxpdHktMTApOiBhIGBtdXRhdGluZ2AgY2FsbCBuZWVkc1xuLy8gZXhjbHVzaXZlIGFjY2VzcyB0byB0aGUgY2FsbGVlIGZvciB0aGUgY2FsbCdzIGR1cmF0aW9uLiBDYWxsaW5nIG9uZSB0aHJvdWdoXG4vLyBhIHNoYXJlZCBgJmAgcmVmZXJlbmNlIChoZXJlIGEgYCZDZWxsYCByZWNlaXZlcikgaXMgYSBjb21waWxlIGVycm9yLlxuLy9cbnN0cnVjdCBDZWxsIHtcbiAgICBnbzogdmFyIHx8IC0+IGk2NCxcbn1cblxuZnVuIHBlZWsoYzogJkNlbGwpIC0+IGk2NCB7XG4gICAgKGMuZ28pKCkgLy8gZXJyb3IgKFQwMDI0KTogYHZhcmAgY2xvc3VyZSBjYWxsZWQgdGhyb3VnaCBhIHNoYXJlZCBgJmAgcmVmZXJlbmNlXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBuIDo9IDA7XG4gICAgbGV0IGMgOj0gQ2VsbCB7IGdvID0gW25dIHZhciB8fCB7IG4gOj0gbiArIDE7IG4gfSB9O1xuICAgIGFzc2VydChwZWVrKCZjKSA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2Nsb3N1cmVzL3YwXzEzXzBfbmVnX3Zhcl9jYWxsX3Rocm91Z2hfc2hhcmVkX3JlZi5tdGwiLCJuYW1lIjoidjBfMTNfMF9uZWdfdmFyX2NhbGxfdGhyb3VnaF9zaGFyZWRfcmVmLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### T0030 — Inner closure borrows an outer by-value capture

An inner closure borrows an enclosing closure's by-value capture.

<!-- rfc.py:exemption kind="blocked" ref="RFC-0122" reason="requires RFC-0122's borrow analysis, not yet implemented" -->

**Fix:** restructure the code until RFC-0122 supplies the necessary borrow analysis.

---

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on RFC-0122: requires RFC-0122's borrow analysis, not yet implemented_</span>
<!-- rfc.py:exemption:rendered:end -->

## Runtime errors (R)

### R0001 — No `main` function defined

Execution requires a `main` function but none was found.

**Fix:** add `fun main() { ... }` to your program.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6Im5vIG1haW4iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzA3X25vX21haW4ubXRsIiwic291cmNlIjoiLy8gUlVOVElNRV9FUlJPUltubyBtYWluXVxubGV0IHggOj0gMTtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2Z1bmN0aW9ucy9uZWdfMDdfbm9fbWFpbi5tdGwiLCJuYW1lIjoibmVnXzA3X25vX21haW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### R0002 — `main` is not a valid entry point

`main` exists but is generic or is not a function.

**Fix:** `main` must be a concrete, non-generic function with no parameters.

> **Note:** also raised for a generic closure invoked with no call-site type context,
> with a different message — this entry covers the `main` case only.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDAyIiwiY29sIjpudWxsLCJjb250YWlucyI6Im5vdCBhIGZ1bmN0aW9uIiwibGluZSI6bnVsbCwic3RhdHVzIjoicnVudGltZV9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ18wOF9tYWluX25vdF9hX2Z1bmN0aW9uLm10bCIsInNvdXJjZSI6Ii8vIGBtYWluYCBleGlzdHMgYnV0IGlzIGEgYmluZGluZywgbm90IGEgZnVuY3Rpb24gLS0gUjAwMDIncyBvdGhlciBkb2N1bWVudGVkXG4vLyB0cmlnZ2VyICh0aGUgc2libGluZyBjYXNlIGlzIGEgZ2VuZXJpYyBtYWluLCBzZWUgZXJyb3ItY29kZXMubWQpLlxubGV0IG1haW4gOj0gNTtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2Z1bmN0aW9ucy9uZWdfMDhfbWFpbl9ub3RfYV9mdW5jdGlvbi5tdGwiLCJuYW1lIjoibmVnXzA4X21haW5fbm90X2FfZnVuY3Rpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### R0003 — Undefined variable at runtime

A variable name is not found in the current environment. This can occur when a variable is used before it is defined in a branch that the type-checker did not flag.

```
[R0003] runtime error in main.mtl at 10..15: undefined variable `x`
```

<!-- rfc.py:exemption kind="blocked" ref="metel-core#733" reason="Confirmed live raise sites (lvalue.rs, mod.rs), but no repro found in the time spent. #712's precedent (an analogous nested-fun forward-reference gap) suggests a real gap plausibly still exists in hoisting/scoping, just not located yet." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#733: Confirmed live raise sites (lvalue.rs, mod.rs), but no repro found in the time spent. #712's precedent (an analogous nested-fun forward-reference gap) suggests a real gap plausibly still exists in hoisting/scoping, just not located yet._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0004 — Index out of bounds

An array index is negative or ≥ the array length.

**Fix:** check that the index is within `0..array.len()` before access.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDA0IiwiY29sIjpudWxsLCJjb250YWlucyI6Im91dCBvZiBib3VuZHMiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzAzX2FycmF5X29vYi5tdGwiLCJzb3VyY2UiOiIvLyBSVU5USU1FX0VSUk9SW291dCBvZiBib3VuZHNdXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYXJyIDo9IFsxLCAyXTtcbiAgICBsZXQgX3ggOj0gYXJyWzVdO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvbmVnXzAzX2FycmF5X29vYi5tdGwiLCJuYW1lIjoibmVnXzAzX2FycmF5X29vYi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### R0005 — Tuple index out of bounds

A tuple element is accessed by an index that does not exist.

```
[R0005] runtime error in main.mtl at 5..10: tuple index 3 out of bounds
```

**Fix:** tuple indices are fixed at compile time; verify the index against the tuple's declared length.

<!-- rfc.py:exemption kind="untestable" ref="metel-core#717" reason="Checked and found unreachable via ordinary source -- tuple indices are fixed at compile time and out-of-range access is caught statically, not deferred to runtime." -->

> **Note:** not confirmed reachable from ordinary source. A tuple index is always a
> literal token, never a computed expression, so an out-of-range index was caught as
> `T0003` statically in every construction tried. Unlike `P0003` above, the raise site
> is real code — just unconfirmed.

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Checked and found unreachable via ordinary source -- tuple indices are fixed at compile time and out-of-range access is caught statically, not deferred to runtime._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0006 — Non-exhaustive match at runtime

A `match` expression reached its end without any arm matching. This indicates a pattern that the type checker approved as exhaustive but that is not, which is a known limitation.

```
[R0006] runtime error in main.mtl at 2..30: match: no arm matched scrutinee
```

<!-- rfc.py:exemption kind="blocked" ref="metel-core#733" reason="A known limitation (the type checker approving a match as exhaustive when it is not) -- no attempt made to construct a real typechecker exhaustiveness gap." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#733: A known limitation (the type checker approving a match as exhaustive when it is not) -- no attempt made to construct a real typechecker exhaustiveness gap._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0007 — Arithmetic error

Integer division or remainder by zero, **or** integer overflow on `+`, `-`, `*`, or
`/` (RFC-0007 D3, amended 2026-08-26 — panics unconditionally in every build; there
is no debug/release distinction). Floating-point arithmetic never raises this code —
float overflow and division by zero follow IEEE 754 (`inf`/`-inf`/`NaN`), never a
panic.

**Fix:** guard with a zero check before dividing, or ensure operands stay in range
before an operation that could overflow.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDA3IiwiY29sIjpudWxsLCJjb250YWlucyI6Im92ZXJmbG93IiwibGluZSI6bnVsbCwic3RhdHVzIjoicnVudGltZV9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX292ZXJmbG93X3Bhbmljcy5tdGwiLCJzb3VyY2UiOiIvLyBSVU5USU1FX0VSUk9SW292ZXJmbG93XVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGE6IGk4IDo9IDEyN2k4ICsgMWk4O1xuICAgIGxldCBfIDo9IGE7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9hcml0aG1ldGljLzExX292ZXJmbG93X3Bhbmljcy5tdGwiLCJuYW1lIjoiMTFfb3ZlcmZsb3dfcGFuaWNzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### R0008 — Field not found

A struct or enum value does not have the accessed field.

```
[R0008] runtime error in main.mtl at 5..12: no field `colour` on value
```

**Fix:** check the field name against the type definition.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#733" reason="Confirmed live raise site, but every attempted repro (a generic function reading an unconstrained field) was caught statically as T0002 instead. A real repro likely needs a generic/dynamic-dispatch angle not yet tried." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#733: Confirmed live raise site, but every attempted repro (a generic function reading an unconstrained field) was caught statically as T0002 instead. A real repro likely needs a generic/dynamic-dispatch angle not yet tried._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0009 — Method not found

A method call cannot be resolved for the receiver type.

```
[R0009] runtime error in main.mtl at 5..20: no method `draw` on `Circle`
```

**Fix:** define the method in an `extend` block for the type.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#733" reason="Same investigation and same open question as R0008 -- struct fields and named-type methods appear to always resolve statically for concrete types." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#733: Same investigation and same open question as R0008 -- struct fields and named-type methods appear to always resolve statically for concrete types._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0010 — Call on non-callable value

A call expression (`f(...)`) is applied to a value that is not a function or closure.

```
[R0010] runtime error in main.mtl at 3..8: call: expected a closure or builtin
```

<!-- rfc.py:exemption kind="blocked" ref="metel-core#733" reason="Confirmed live raise site, but calling a plain i64 variable was caught statically as T0001. Same open question as R0008/R0009." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#733: Confirmed live raise site, but calling a plain i64 variable was caught statically as T0001. Same open question as R0008/R0009._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0011 — Invalid for-in iterator

A `for x in expr` loop where `expr` does not evaluate to an `Array`, a `Range`, or a type
implementing `Iterable`.

```
[R0011] runtime error in main.mtl at 1..20: for-in: expected Array or Range
```

**Fix:** ensure the iterable is an array literal, a range (`a..b`), a value of those types,
or a type with its own `Iterable` implementation (see `expressions.md`, "for-in").

<!-- rfc.py:exemption kind="blocked" ref="metel-core#981" reason="Confirmed live raise sites (evaluator/mod.rs), but a plain non-iterable typed value (e.g. for (x in n) where n: i64) is caught statically as T0001 before reaching this runtime path. A real repro likely needs a generic/dynamic-typed angle, not found in this session." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#981: Confirmed live raise sites (evaluator/mod.rs), but a plain non-iterable typed value (e.g. for (x in n) where n: i64) is caught statically as T0001 before reaching this runtime path. A real repro likely needs a generic/dynamic-typed angle, not found in this session._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0012 — Error propagation on non-Result value

The `?` operator is applied to a value that is not a `Result`.

```
[R0012] runtime error in main.mtl at 5..10: ?: expected a Result value
```

**Fix:** only use `?` on expressions whose type is `Result[T, E]`.

<!-- rfc.py:exemption kind="untestable" ref="metel-core#733" reason="Confirmed absent from the RuntimeErrorCode enum entirely (verified directly in metel-frontend/src/error/mod.rs -- the enum jumps from R0011 to R0013). This entry documents a code that does not exist in the current implementation; needs a follow-up decision (implement it, or remove/renumber the entry) outside this issue's scope." -->

> **Note:** this misuse is actually caught statically. `?` constrains its operand's
> type to `Result<T, E>` during type inference (`infer_propagate_error`), so a
> non-`Result` operand is rejected as a `T0001` type mismatch before the program
> ever runs. `R0012` does not appear in the interpreter's `RuntimeErrorCode` enum
> today and is unreachable in practice — kept here for the code number, not because
> the described runtime error can currently occur. (Found while investigating
> issue #536; not fixed as part of it, since removing a documented code is a
> separate decision from the yolo/conversion-method work that issue tracked.)

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Confirmed absent from the RuntimeErrorCode enum entirely (verified directly in metel-frontend/src/error/mod.rs -- the enum jumps from R0011 to R0013). This entry documents a code that does not exist in the current implementation; needs a follow-up decision (implement it, or remove/renumber the entry) outside this issue's scope._</span>
<!-- rfc.py:exemption:rendered:end -->

### R0013 — Assertion failed

`assert(cond)` or `assert(cond, msg)` is called with `cond` evaluating to
`false`. The panic message is the fixed string `"assertion failed"` for the
one-argument form, or the caller-supplied `msg` for the two-argument form.

**Fix:** this is not a bug in the interpreter — it means the asserted condition
was actually false at runtime. Fix the condition, or the code that led to it.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDEzIiwiY29sIjpudWxsLCJjb250YWlucyI6ImN1c3RvbSBhc3NlcnRpb24gZmFpbHVyZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InJ1bnRpbWVfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI4MF9hc3NlcnRfcGFuaWNfbWVzc2FnZXMubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGZhbHNlLCBcImN1c3RvbSBhc3NlcnRpb24gZmFpbHVyZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2J1aWx0aW5zLzgwX2Fzc2VydF9wYW5pY19tZXNzYWdlcy5tdGwiLCJuYW1lIjoiODBfYXNzZXJ0X3BhbmljX21lc3NhZ2VzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

### R0014 — Unwrap on `None`/`Err`

`.yolo()` is called on a `Perhaps<T>` that is `None`, or a `Result<T, E>` that is
`Err`. For `Result`, the panic message includes the `Err` value's debug
representation.

**Fix:** this is not a bug in the interpreter — `.yolo()` is meant only for cases
where `None`/`Err` represents a logic error that should never occur in correct
code. Use `match`, `.unwrap_or`, `.unwrap_or_else`, or (for `Result`) `?` to
handle the expected case instead.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDE0IiwiY29sIjpudWxsLCJjb250YWlucyI6InlvbG8iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX3lvbG9fbm9uZS5tdGwiLCJzb3VyY2UiOiIvLyBSVU5USU1FX0VSUk9SW1IwMDE0XVxuLy8gaXNzdWUgIzIzMjogLnlvbG8oKSBvbiBOb25lIHBhbmljcyB3aXRoIFIwMDE0LlxuZnVuIG1haW4oKSB7XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGxldCBfIDo9IG5vbmUueW9sbygpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcGVyaGFwc19yZXN1bHQvbmVnX3lvbG9fbm9uZS5tdGwiLCJuYW1lIjoibmVnX3lvbG9fbm9uZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

### R0015 — Explicit panic

`panic(msg)` (RFC-0078) is called. Always panics unconditionally with `msg`.

**Fix:** this is not a bug in the interpreter — `panic` is meant for logic
errors that should never occur in correct code. Handle the expected case with
ordinary control flow instead of reaching the `panic` call.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDE1IiwiY29sIjpudWxsLCJjb250YWlucyI6ImJvb20iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX3BhbmljLm10bCIsInNvdXJjZSI6Ii8vIFJVTlRJTUVfRVJST1JbYm9vbV1cbi8vIFJGQy0wMDc4OiBwYW5pYyhtc2cpIGFsd2F5cyBwYW5pY3MgKFIwMDE1KSB3aXRoIHRoZSBnaXZlbiBtZXNzYWdlLlxuZnVuIG1haW4oKSB7XG4gICAgcGFuaWMoXCJib29tXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbmV2ZXIvbmVnX3BhbmljLm10bCIsIm5hbWUiOiJuZWdfcGFuaWMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

### R0016 — Re-entrant mutating closure call

> **Availability:** Since v0.13.0.

A `var` closure tried to call the same closure value again before its current invocation
finished. This is an uncatchable assertion-class runtime error.

**Fix:** restructure the callback/control flow so a mutating closure is not re-entered.

---

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlIwMDE2IiwiY29sIjpudWxsLCJjb250YWlucyI6InJlLWVudHJhbnQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoidjBfMTNfMF9uZWdfbXV0YXRpbmdfcmVlbnRyYW5jeV9yZWplY3RlZC5tdGwiLCJzb3VyY2UiOiIvLyB2MC4xMy4wIGNsb3N1cmUgY2x1c3RlciAoUkZDIDAxNTMgZHluYW1pY3MtOSk6IGZvciB0aGUgZXh0ZW50IG9mIGFcbi8vIGBtdXRhdGluZ2AgY2FsbCB0aGUgY2FsbGVlIGlzIGV4Y2x1c2l2ZWx5IGJvcnJvd2VkLiBBIHNlY29uZCBgbXV0YXRpbmdgXG4vLyBjYWxsIG9uIHRoZSBzYW1lIGNsb3N1cmUgdmFsdWUgcmVhY2hlZCBmcm9tIGluc2lkZSB0aGUgZmlyc3QgaXMgcmVqZWN0ZWQgLS1cbi8vIGJlZm9yZSB0aGUgYm9ycm93IGNoZWNrZXIgbGFuZHMsIGFzIGEgcnVudGltZSBlcnJvciAoUjAwMDcpLlxuLy9cbnN0cnVjdCBDZWxsIHtcbiAgICBnbzogdmFyIHx8IC0+IGk2NCxcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIGMgOj0gQ2VsbCB7IGdvID0gfHwgeyAwIH0gfTtcbiAgICBjLmdvIDo9IFsmdmFyIGNdIHZhciB8fCB7XG4gICAgICAgIChjLmdvKSgpICsgMSAvLyByZS1lbnRlcnMgdGhlIHNhbWUgYHZhcmAgY2xvc3VyZSB3aGlsZSBpdHMgZmlyc3QgY2FsbCBpcyBsaXZlXG4gICAgfTtcbiAgICAoYy5nbykoKTsgLy8gcnVudGltZSBlcnJvciBSMDAwNyAtLSByZS1lbnRyYW50IGNhbGwgdG8gYSBtdXRhdGluZyBjbG9zdXJlXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jbG9zdXJlcy92MF8xM18wX25lZ19tdXRhdGluZ19yZWVudHJhbmN5X3JlamVjdGVkLm10bCIsIm5hbWUiOiJ2MF8xM18wX25lZ19tdXRhdGluZ19yZWVudHJhbmN5X3JlamVjdGVkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

## Internal errors (I)

### I0001 — Internal interpreter error

The interpreter reached an impossible state. This is a bug in the interpreter — the typechecker should have caught it before execution.

```
[I0001] internal error: binop: unsupported operand types (typechecker should have caught this)
```

**What to do:** please file a bug report at [the Metel issue tracker](https://github.com/metel-lang/metel-core/issues) with the source program that triggered this error.

<!-- rfc.py:exemption kind="untestable" ref="metel-core#733" reason="Forcing an internal-error state deliberately isn't meaningfully the same kind of check as an ordinary trigger -- a real repro would mean finding an actual interpreter bug, not demonstrating a language rule (not attempted)." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Forcing an internal-error state deliberately isn't meaningfully the same kind of check as an ordinary trigger -- a real repro would mean finding an actual interpreter bug, not demonstrating a language rule (not attempted)._</span>
<!-- rfc.py:exemption:rendered:end -->

### I0002 — Not implemented

The program uses a language feature that is not yet supported in this version of the interpreter.

```
[I0002] internal error: generic functions are not supported in v0.1
```

**What to do:** check the [changelog](../release-notes/changelog.md) for the current supported feature set and the release plan for the planned implementation milestone.

<!-- rfc.py:exemption kind="untestable" ref="metel-core#733" reason="Same reasoning as I0001 -- deliberately forcing an unimplemented-feature panic isn't meaningfully the same kind of check as an ordinary trigger (not attempted)." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — untestable: Same reasoning as I0001 -- deliberately forcing an unimplemented-feature panic isn't meaningfully the same kind of check as an ordinary trigger (not attempted)._</span>
<!-- rfc.py:exemption:rendered:end -->
