---
sidebar_position: 9
---

# Enums

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir := Direction::North;
    let s := Shape::Circle { radius = 5.0 };
    let area := match (s) {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match (dir) {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

[Call-syntax variant construction](#spec.declarations.enums.variant-construction.legality-1)
is available alongside the existing forms shown above.

Variants may be unit (no data) or struct-like (named fields). A struct-like variant's
named fields follow the [same `pub`/private visibility rules as an ordinary
struct's](../modules.md#spec.modules.visibility.legality-6).

When a struct-like variant's field set is empty, [both constructor spellings are
accepted](#spec.declarations.enums.legality-1):

```metel
enum Flag {
    On {},
}

let x := Flag::On;
let y := Flag::On {};
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.legality-1}

A zero-field enum variant may be constructed either as its qualified path or with empty
braces.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg5X2VtcHR5X2NvbnN0cnVjdG9yX2Zvcm1zLm10bCIsInNvdXJjZSI6InN0cnVjdCBFbXB0eSB7fVxuXG5lbnVtIEZsYWcge1xuICAgIE9uIHt9LFxufVxuXG5mdW4gdXNlX2VtcHR5KHg6IEVtcHR5KSAtPiBpNjQge1xuICAgIDFcbn1cblxuZnVuIHVzZV9mbGFnKGY6IEZsYWcpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKGYpIHtcbiAgICAgICAgRmxhZzo6T24gPT4gNyxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhIDo9IEVtcHR5O1xuICAgIGxldCBiIDo9IEVtcHR5IHt9O1xuICAgIGxldCB4IDo9IEZsYWc6Ok9uO1xuICAgIGxldCB5IDo9IEZsYWc6Ok9uIHt9O1xuXG4gICAgYXNzZXJ0KHVzZV9lbXB0eShhKSA9PSAxKTtcbiAgICBhc3NlcnQodXNlX2VtcHR5KGIpID09IDEpO1xuICAgIGFzc2VydCh1c2VfZmxhZyh4KSA9PSA3KTtcbiAgICBhc3NlcnQodXNlX2ZsYWcoeSkgPT0gNyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzg5X2VtcHR5X2NvbnN0cnVjdG9yX2Zvcm1zLm10bCIsIm5hbWUiOiI4OV9lbXB0eV9jb25zdHJ1Y3Rvcl9mb3Jtcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.enums.dynamics-1}

For a zero-field enum variant, the bare and empty-brace constructor forms evaluate to the
same variant value.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg5X2VtcHR5X2NvbnN0cnVjdG9yX2Zvcm1zLm10bCIsInNvdXJjZSI6InN0cnVjdCBFbXB0eSB7fVxuXG5lbnVtIEZsYWcge1xuICAgIE9uIHt9LFxufVxuXG5mdW4gdXNlX2VtcHR5KHg6IEVtcHR5KSAtPiBpNjQge1xuICAgIDFcbn1cblxuZnVuIHVzZV9mbGFnKGY6IEZsYWcpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKGYpIHtcbiAgICAgICAgRmxhZzo6T24gPT4gNyxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhIDo9IEVtcHR5O1xuICAgIGxldCBiIDo9IEVtcHR5IHt9O1xuICAgIGxldCB4IDo9IEZsYWc6Ok9uO1xuICAgIGxldCB5IDo9IEZsYWc6Ok9uIHt9O1xuXG4gICAgYXNzZXJ0KHVzZV9lbXB0eShhKSA9PSAxKTtcbiAgICBhc3NlcnQodXNlX2VtcHR5KGIpID09IDEpO1xuICAgIGFzc2VydCh1c2VfZmxhZyh4KSA9PSA3KTtcbiAgICBhc3NlcnQodXNlX2ZsYWcoeSkgPT0gNyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzg5X2VtcHR5X2NvbnN0cnVjdG9yX2Zvcm1zLm10bCIsIm5hbWUiOiI4OV9lbXB0eV9jb25zdHJ1Y3Rvcl9mb3Jtcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Instantiation

[A struct-like enum variant with fields cannot omit its constructor fields](#spec.declarations.enums.instantiation.legality-1):

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir := Direction::North;
    let s := Shape::Circle { radius = 5.0 };
    let area := match (s) {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match (dir) {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.instantiation.legality-1}

A struct-like enum variant with fields cannot omit its constructor fields.


<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6ImZpZWxkZnVsIHZhcmlhbnQgYW5kIGhhcyBubyBiYXJlLXZhbHVlIGZvcm0iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTZfbmVnXzEzX25vbl9lbXB0eV92YXJpYW50X3JlcXVpcmVzX2ZpZWxkcy5tdGwiLCJzb3VyY2UiOiIvLyBBIG5vbi1lbXB0eSBlbnVtIHZhcmlhbnQgY2Fubm90IG9taXQgaXRzIGNvbnN0cnVjdG9yIGZpZWxkcy5cblxuZW51bSBDaG9pY2Uge1xuICAgIFZhbHVlIHsgdmFsdWU6IGk2NCB9LFxufVxuXG5sZXQgY2hvaWNlOiBDaG9pY2UgOj0gQ2hvaWNlOjpWYWx1ZTtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2VudW1zL3N0YWdlNl9uZWdfMTNfbm9uX2VtcHR5X3ZhcmlhbnRfcmVxdWlyZXNfZmllbGRzLm10bCIsIm5hbWUiOiJzdGFnZTZfbmVnXzEzX25vbl9lbXB0eV92YXJpYW50X3JlcXVpcmVzX2ZpZWxkcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Methods on Enums

`extend` blocks on enums follow the same syntax as structs:

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

extend Shape {
    fun area(self) -> f64 {
        match (self) {
            Circle { radius } => 3.14159 * radius * radius,
            Rectangle { width, height } => width * height,
        }
    }
}

fun main() -> i64 {
    let s := Shape::Circle { radius = 5.0 };
    return s.area() as i64;
}
```

## Call-syntax variant construction

A qualified variant path followed by a call
[constructs that variant](#spec.declarations.enums.variant-construction.legality-1):
`Message::Text(body = "hello")` for a payload variant, `Message::Empty()` for a unit
variant, using the same positional/keyword/exact-row rules as struct construction. An
enum type alone, with no variant qualification, does not identify a variant —
`Message(...)` does not choose a variant from its arguments. The existing
bare/qualified unit-variant forms above remain valid alongside the call form.

<!-- doc-example: skip reason="enum variant construction is not implemented yet; the qualified-call form currently hits an internal error rather than constructing" -->
```metel
enum Message { Text { body: String }, Number { value: i64 }, Empty }

fun main() {
    let a := Message::Text(body = "hello");
    let b := Message::Number(42);
    let c := Message::Empty();
    let d := Message::Empty;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.variant-construction.legality-1}

A call `Enum::Variant(args)`, where the qualified path names a variant, constructs that
variant using the same positional/keyword argument binding, exact-row, and
field-visibility rules as struct construction applied to the variant's payload. An
unqualified enum type name does not identify a variant; `Enum(args)` is not a variant
construction.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#2197" reason="Qualified call-syntax variant construction is not implemented: struct-style construction is still the only way to build a payload variant (verified against this page's own legality-1/instantiation.legality-1 fixtures), and call syntax on a variant path is ordinary call resolution, not construction." -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0100](../../../rfcs/3-integrated/rfc-0100-constructor-call-construction.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#2197: Qualified call-syntax variant construction is not implemented: struct-style construction is still the only way to build a payload variant (verified against this page's own legality-1/instantiation.legality-1 fixtures), and call syntax on a variant path is ordinary call resolution, not construction._</span>
<!-- rfc.py:exemption:rendered:end -->

##### Dynamic Semantics {#spec.declarations.enums.variant-construction.dynamics-1}

`Enum::Variant(args)` and the existing struct-style brace construction of the same
variant with the same arguments produce the same variant value.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#2197" reason="Same root gap as variant-construction.legality-1: there is no call-syntax construction to compare against the existing brace form." -->

<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#2197: Same root gap as variant-construction.legality-1: there is no call-syntax construction to compare against the existing brace form._</span>
<!-- rfc.py:exemption:rendered:end -->

</details>

---
