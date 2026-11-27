---
sidebar_position: 17
---

# Default Methods and Self

## Default Methods

An aspect method may [supply a default body](#spec.declarations.aspects.default-methods.dynamics-1). An `extend` block may omit any method that
has a default; the aspect's implementation is inherited automatically.

```metel
aspect Greet {
    fun name(self) -> String;

    fun greet(self) -> String {
        return "Hello, " + self.name();
    }
}

struct Person {
    name: String,
}

extend Person: Greet {
    fun name(self) -> String {
        return self.name;
    }
    // greet() is inherited from the aspect default
}

fun main() {
    let p := Person(name = "Ada");
    println(p.greet());   // Hello, Ada
}
```

A method without a default body [must be provided by every `extend` block](#spec.declarations.aspects.default-methods.legality-1); omitting it
is a compile-time error.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.declarations.aspects.default-methods.dynamics-1}

An aspect method with a body is a default implementation. An implementing `extend` block
that omits it inherits and dispatches to that body.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2dlbmVyaWNfZHluX2RlZmF1bHRzLm10bCIsInNvdXJjZSI6ImFzcGVjdCBUcmFuc2Zvcm08QSwgQj4ge1xuICAgIGZ1biB0cmFuc2Zvcm0oJnNlbGYsIHZhbHVlOiBBKSAtPiBCO1xuICAgIGZ1biBhZ2Fpbigmc2VsZiwgdmFsdWU6IEEpIC0+IEIgeyBzZWxmLnRyYW5zZm9ybSh2YWx1ZSkgfVxuICAgIGZ1biBpZGVudGl0eTxUPigmc2VsZiwgdmFsdWU6IFQpIC0+IFQgeyB2YWx1ZSB9XG59XG5zdHJ1Y3QgRG91YmxlciB7fVxuZXh0ZW5kIERvdWJsZXI6IFRyYW5zZm9ybTxpNjQsIGk2ND4ge1xuICAgIGZ1biB0cmFuc2Zvcm0oJnNlbGYsIHZhbHVlOiBpNjQpIC0+IGk2NCB7IHZhbHVlICogMiB9XG59XG50eXBlIFRyYW5zZm9ybWVyPEEsIEI+IDo9IGR5biBUcmFuc2Zvcm08QSwgQj47XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgY29uY3JldGUgOj0gRG91YmxlciB7fTtcbiAgICBhc3NlcnQoY29uY3JldGUuYWdhaW4oNikgPT0gMTIpO1xuICAgIGFzc2VydChjb25jcmV0ZS5pZGVudGl0eShcInN0YXRpYyBnZW5lcmljXCIpID09IFwic3RhdGljIGdlbmVyaWNcIik7XG4gICAgbGV0IG9iamVjdDogVHJhbnNmb3JtZXI8aTY0LCBpNjQ+IDo9IGNvbmNyZXRlO1xuICAgIGFzc2VydChvYmplY3QudHJhbnNmb3JtKDcpID09IDE0KTtcbiAgICBhc3NlcnQob2JqZWN0LmFnYWluKDgpID09IDE2KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvcmVsZWFzZV9tYXRyaXhfZ2VuZXJpY19keW5fZGVmYXVsdHMubXRsIiwibmFtZSI6InJlbGVhc2VfbWF0cml4X2dlbmVyaWNfZHluX2RlZmF1bHRzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlMTJfMDFfZGVmYXVsdF9tZXRob2RzLm10bCIsInNvdXJjZSI6Ii8vIFBvc2l0aXZlOiBhc3BlY3QgZGVmYXVsdCBtZXRob2RzIGNhbiBiZSBvbWl0dGVkIGluIGltcGwgYmxvY2tzIGFuZCBpbmhlcml0ZWQuXG5cbnN0cnVjdCBQZXJzb24ge1xuICAgIG5hbWU6IFN0cmluZyxcbn1cblxuYXNwZWN0IEdyZWV0IHtcbiAgICBmdW4gbmFtZShzZWxmKSAtPiBTdHJpbmc7XG5cbiAgICBmdW4gZ3JlZXQoc2VsZikgLT4gU3RyaW5nIHtcbiAgICAgICAgcmV0dXJuIFwiSGVsbG8sIFwiICsgc2VsZi5uYW1lKCk7XG4gICAgfVxufVxuXG5leHRlbmQgUGVyc29uOiBHcmVldCB7XG4gICAgZnVuIG5hbWUoc2VsZikgLT4gU3RyaW5nIHtcbiAgICAgICAgcmV0dXJuIHNlbGYubmFtZTtcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBwIDo9IFBlcnNvbihuYW1lID0gXCJBZGFcIik7XG4gICAgbGV0IG1zZzogU3RyaW5nIDo9IHAuZ3JlZXQoKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2FzcGVjdHMvc3RhZ2UxMl8wMV9kZWZhdWx0X21ldGhvZHMubXRsIiwibmFtZSI6InN0YWdlMTJfMDFfZGVmYXVsdF9tZXRob2RzLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.aspects.default-methods.legality-1}

An implementing `extend` block must provide every aspect method that has no default body.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6ImRvZXMgbm90IGltcGxlbWVudCIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlMTJfbmVnXzAxX21pc3NpbmdfcmVxdWlyZWRfd2l0aF9kZWZhdWx0cy5tdGwiLCJzb3VyY2UiOiIvLyBOZWdhdGl2ZTogYSByZXF1aXJlZCBtZXRob2QgKG5vIGRlZmF1bHQgYm9keSkgbXVzdCBzdGlsbCBiZSBwcm92aWRlZCBldmVuIHdoZW5cbi8vIHRoZSBpbXBsIHByb3ZpZGVzIG90aGVyIG1ldGhvZHMgdGhhdCBoYXZlIGRlZmF1bHRzIGluIHRoZSBhc3BlY3QuXG5cbnN0cnVjdCBXaWRnZXQge1xuICAgIGlkOiBpNjQsXG59XG5cbmFzcGVjdCBSZW5kZXIge1xuICAgIGZ1biBkcmF3KHNlbGYpIC0+IFN0cmluZztcblxuICAgIGZ1biBwcmV2aWV3KHNlbGYpIC0+IFN0cmluZyB7XG4gICAgICAgIHJldHVybiBcInByZXZpZXc6IFwiICsgc2VsZi5kcmF3KCk7XG4gICAgfVxufVxuXG5leHRlbmQgV2lkZ2V0OiBSZW5kZXIgeyAvLyBFUlJPUltUMDAxMl1cbiAgICBmdW4gcHJldmlldyhzZWxmKSAtPiBTdHJpbmcge1xuICAgICAgICByZXR1cm4gXCJvdmVycmlkaW5nIHRoZSBkZWZhdWx0XCI7XG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYXNwZWN0cy9zdGFnZTEyX25lZ18wMV9taXNzaW5nX3JlcXVpcmVkX3dpdGhfZGVmYXVsdHMubXRsIiwibmFtZSI6InN0YWdlMTJfbmVnXzAxX21pc3NpbmdfcmVxdWlyZWRfd2l0aF9kZWZhdWx0cy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## The Self Type

[`Self` inside an aspect or an `extend` block refers to the concrete implementing type](#spec.declarations.aspects.the-self-type.legality-1).

In an aspect definition, `Self` is the implementing type at the call site:

```metel
aspect Comparable {
    fun compare(self, other: Self) -> i64;
}
```

In a struct or enum `extend` block, `Self` is an alias for the type being implemented:

```metel
struct Point {
    x: i64,
}

extend Point {
    fun clone(self) -> Self {
        self
    }

    fun same_as(self, other: Self) -> boolean {
        self.x == other.x
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.the-self-type.legality-1}

Within an aspect declaration, `Self` denotes the type implementing that aspect. Within an
`extend` block, it denotes the block's target type.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV8wM19zZWxmX21ldGhvZF9zaWduYXR1cmVzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDU6IGBTZWxmYCBzaG91bGQgcmVzb2x2ZSBpbiBvcmRpbmFyeSBzdHJ1Y3QgYW5kIGVudW0gbWV0aG9kIHNpZ25hdHVyZXMuXG5cbnN0cnVjdCBQb2ludCB7XG4gICAgeDogaTY0LFxufVxuXG5leHRlbmQgUG9pbnQge1xuICAgIGZ1biBjbG9uZSgmc2VsZikgLT4gU2VsZiB7XG4gICAgICAgIFBvaW50IHsgeCA9IHNlbGYueCB9XG4gICAgfVxuXG4gICAgZnVuIHNhbWVfYXMoJnNlbGYsIG90aGVyOiBTZWxmKSAtPiBib29sZWFuIHtcbiAgICAgICAgc2VsZi54ID09IG90aGVyLnhcbiAgICB9XG59XG5cbmVudW0gVG9rZW4ge1xuICAgIGk2NCB7IHZhbHVlOiBpNjQgfSxcbn1cblxuZXh0ZW5kIFRva2VuIHtcbiAgICBmdW4gaWRlbnRpdHkoc2VsZikgLT4gU2VsZiB7XG4gICAgICAgIHNlbGZcbiAgICB9XG59XG5cbmxldCBwIDo9IFBvaW50KHggPSAxKTtcbmxldCBxOiBQb2ludCA6PSBwLmNsb25lKCk7XG5sZXQgc2FtZTogYm9vbGVhbiA6PSBwLnNhbWVfYXMocSk7XG5cbmxldCB0b2tlbiA6PSBUb2tlbjo6aTY0KHZhbHVlID0gNyk7XG5sZXQgdG9rZW5fY29weTogVG9rZW4gOj0gdG9rZW4uaWRlbnRpdHkoKTtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1XzAzX3NlbGZfbWV0aG9kX3NpZ25hdHVyZXMubXRsIiwibmFtZSI6InN0YWdlNV8wM19zZWxmX21ldGhvZF9zaWduYXR1cmVzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>
