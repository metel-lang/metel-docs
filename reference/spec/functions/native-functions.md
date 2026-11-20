---
sidebar_position: 10
---

# Native Functions (Standard Library Only)

Standard library declarations may be marked `native`, binding them to an
implementation provided by the host interpreter instead of a Metel body:

```metel
// from std::core — not writable in user code
native(@std.core.println) pub fun println<T>(x: T);
native(@std.core.clock)   pub fun clock() -> i64;
```

A native declaration has no body — it ends with `;` instead of a block. The
`@`-path inside the parentheses is the binding key that selects the host
implementation. The form is also valid on methods inside `extend` blocks; for
example, the primitive `Display` implementations in `std::core` are declared
this way:

```metel
extend i64: Display {
    native(@std.core.to_string) fun to_string(&self) -> String;
}
```

**[`native` is reserved for the standard library](#spec.functions.native-functions-standard-library-only.legality-1).** Using it in any module
outside the `std` namespace is a compile error, and user projects cannot place
modules under `std::` (see [Modules](../modules.md)). From the caller's side,
native functions are indistinguishable from ordinary functions: they are
imported, typechecked, and called exactly like any other declaration — the
binding key is an implementation detail of the standard library's source.

Native declarations [must annotate every parameter type](#spec.functions.native-functions-standard-library-only.legality-3); an omitted return
type means the function returns `()`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-1}

Only a declaration in the `std` namespace may use the `native` modifier; a `native`
declaration in a user module is rejected.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6Im5hdGl2ZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5hdGl2ZV9vdXRzaWRlX3N0ZC5tdGwiLCJzb3VyY2UiOiIvLyBgbmF0aXZlYCBpcyBhIHN0ZGxpYi1vbmx5IGNvbnN0cnVjdDsgZGVjbGFyaW5nIG9uZSBpbiBhIHVzZXIgbW9kdWxlIChhbnlcbi8vIG1vZHVsZSB3aG9zZSBwYXRoIGRvZXMgbm90IGJlZ2luIHdpdGggYHN0ZGApIGlzIHJlamVjdGVkLlxubmF0aXZlKEBzdGQuY29yZS5wcmludGxuKSBmdW4gc2hvdXQoeDogU3RyaW5nKTsgLy8gRVJST1JbVDAwMDNdXG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL25hdGl2ZV9vdXRzaWRlX3N0ZC5tdGwiLCJuYW1lIjoibmF0aXZlX291dHNpZGVfc3RkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-2}

A native declaration has a dotted `@` host-binding key and no Metel body: it ends with
`;`.

<!-- rfc.py:last_reviewed de95f8a18ed0ec19509be179013604e7c1964a76 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5hdGl2ZV9kZWNsLm10bCIsInNvdXJjZSI6Ii8vIFRoZSBgbmF0aXZlKEBcdTIwMjYpYCBob3N0LWJpbmRpbmcgc3ludGF4IHBhcnNlczogYSBib2R5bGVzcyBmdW5jdGlvbiB3aXRoIGFcbi8vIGRvdHRlZCBob3N0IGtleS4gKFN0ZGxpYi1vbmx5IGVuZm9yY2VtZW50IGhhcHBlbnMgYXQgdHlwZS1jaGVjaywgbm90IHBhcnNlLilcbm5hdGl2ZShAc3RkLmNvcmUucHJpbnQpIGZ1biBwcmludF9vbmUoeDogU3RyaW5nKTtcbm5hdGl2ZShAc3RkLmNvcmUuY2xvY2spIGZ1biBub3coKSAtPiBpNjQ7XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uYXRpdmVfZGVjbC5tdGwiLCJuYW1lIjoibmF0aXZlX2RlY2wubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.functions.native-functions-standard-library-only.legality-3}

Every native-function parameter has an explicit type annotation. An omitted return type
denotes `()`.

<!-- rfc.py:last_reviewed de95f8a18ed0ec19509be179013604e7c1964a76 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5hdGl2ZV9kZWNsLm10bCIsInNvdXJjZSI6Ii8vIFRoZSBgbmF0aXZlKEBcdTIwMjYpYCBob3N0LWJpbmRpbmcgc3ludGF4IHBhcnNlczogYSBib2R5bGVzcyBmdW5jdGlvbiB3aXRoIGFcbi8vIGRvdHRlZCBob3N0IGtleS4gKFN0ZGxpYi1vbmx5IGVuZm9yY2VtZW50IGhhcHBlbnMgYXQgdHlwZS1jaGVjaywgbm90IHBhcnNlLilcbm5hdGl2ZShAc3RkLmNvcmUucHJpbnQpIGZ1biBwcmludF9vbmUoeDogU3RyaW5nKTtcbm5hdGl2ZShAc3RkLmNvcmUuY2xvY2spIGZ1biBub3coKSAtPiBpNjQ7XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uYXRpdmVfZGVjbC5tdGwiLCJuYW1lIjoibmF0aXZlX2RlY2wubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>
