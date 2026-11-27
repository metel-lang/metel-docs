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

<!-- rfc.py:last_reviewed c1d7564c1383c97c13f70c3279b79a2d93742a22 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0100](../../../rfcs/3-integrated/rfc-0100-constructor-call-construction.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFfY2FsbF9jb25zdHJ1Y3RzX2FfZmllbGRmdWxfZW51bV92YXJpYW50Lm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMjIwMSAoUkZDLTAxMDAgc2VjdGlvbiA3YSk6IGEgcXVhbGlmaWVkIGNhbGwgb24gYSB2YXJpYW50IHBhdGggY29uc3RydWN0c1xuLy8gdGhhdCB2YXJpYW50LCB0aGUgc2FtZSB3YXkgYSBiYXJlIHN0cnVjdC1uYW1lIGNhbGwgY29uc3RydWN0cyBhIHN0cnVjdCAobWV0ZWwtY29yZSMyMTk5KS5cbmVudW0gTWVzc2FnZSB7IFRleHQgeyBib2R5OiBTdHJpbmcgfSwgTnVtYmVyIHsgdmFsdWU6IGk2NCB9IH1cbmZ1biBtYWluKCkge1xuICAgIGxldCBhIDo9IE1lc3NhZ2U6OlRleHQoYm9keSA9IFwiaGVsbG9cIik7XG4gICAgbGV0IGIgOj0gTWVzc2FnZTo6TnVtYmVyKDQyKTtcbiAgICBtYXRjaCAoYSkge1xuICAgICAgICBNZXNzYWdlOjpUZXh0IHsgYm9keSB9ID0+IGFzc2VydChib2R5ID09IFwiaGVsbG9cIiksXG4gICAgICAgIF8gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9XG4gICAgbWF0Y2ggKGIpIHtcbiAgICAgICAgTWVzc2FnZTo6TnVtYmVyIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gNDIpLFxuICAgICAgICBfID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvYV9jYWxsX2NvbnN0cnVjdHNfYV9maWVsZGZ1bF9lbnVtX3ZhcmlhbnQubXRsIiwibmFtZSI6ImFfY2FsbF9jb25zdHJ1Y3RzX2FfZmllbGRmdWxfZW51bV92YXJpYW50Lm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFfY2FsbF9jb25zdHJ1Y3RzX2FfdW5pdF9lbnVtX3ZhcmlhbnQubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMyMjAxIChSRkMtMDEwMCBzZWN0aW9uIDdhKTogYSB6ZXJvLWFyZ3VtZW50IGNhbGwgb24gYSB1bml0IHZhcmlhbnQncyBwYXRoXG4vLyBjb25zdHJ1Y3RzIGl0LCBhbG9uZ3NpZGUgdGhlIGV4aXN0aW5nIGJhcmUvcXVhbGlmaWVkIHVuaXQtdmFyaWFudCBmb3Jtcy5cbmVudW0gTWVzc2FnZSB7IEVtcHR5LCBUZXh0IHsgYm9keTogU3RyaW5nIH0gfVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGEgOj0gTWVzc2FnZTo6RW1wdHkoKTtcbiAgICBsZXQgYiA6PSBNZXNzYWdlOjpFbXB0eTtcbiAgICBtYXRjaCAoYSkge1xuICAgICAgICBNZXNzYWdlOjpFbXB0eSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgICAgIF8gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9XG4gICAgbWF0Y2ggKGIpIHtcbiAgICAgICAgTWVzc2FnZTo6RW1wdHkgPT4gYXNzZXJ0KHRydWUpLFxuICAgICAgICBfID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvYV9jYWxsX2NvbnN0cnVjdHNfYV91bml0X2VudW1fdmFyaWFudC5tdGwiLCJuYW1lIjoiYV9jYWxsX2NvbnN0cnVjdHNfYV91bml0X2VudW1fdmFyaWFudC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX2JhcmVfZW51bV9jYWxsX2lzX25vdF9hX3ZhcmlhbnRfY29uc3RydWN0aW9uLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMjIwMSAoUkZDLTAxMDAgc2VjdGlvbiA3YSk6IGFuIHVucXVhbGlmaWVkIGVudW0gdHlwZSBuYW1lIGRvZXMgbm90IGlkZW50aWZ5IGFcbi8vIHZhcmlhbnQgLS0gTWVzc2FnZSgxKSBpcyBub3QgYSB2YXJpYW50IGNvbnN0cnVjdGlvbiwgc28gYE1lc3NhZ2VgIGlzIGp1c3QgYW4gdW5kZWZpbmVkIG5hbWUuXG5lbnVtIE1lc3NhZ2UgeyBOdW1iZXIgeyB2YWx1ZTogaTY0IH0gfVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGEgOj0gTWVzc2FnZSgxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2VudW1zL25lZ19iYXJlX2VudW1fY2FsbF9pc19ub3RfYV92YXJpYW50X2NvbnN0cnVjdGlvbi5tdGwiLCJuYW1lIjoibmVnX2JhcmVfZW51bV9jYWxsX2lzX25vdF9hX3ZhcmlhbnRfY29uc3RydWN0aW9uLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.enums.variant-construction.dynamics-1}

`Enum::Variant(args)` and the existing struct-style brace construction of the same
variant with the same arguments produce the same variant value.

<!-- rfc.py:last_reviewed c1d7564c1383c97c13f70c3279b79a2d93742a22 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImNhbGxfYW5kX2JyYWNlX3ZhcmlhbnRfY29uc3RydWN0aW9uX3Byb2R1Y2VfdGhlX3NhbWVfdmFsdWUubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMyMjAxIChSRkMtMDEwMCBzZWN0aW9uIDdhKTogRW51bTo6VmFyaWFudChhcmdzKSBhbmQgdGhlIGV4aXN0aW5nIHN0cnVjdC1zdHlsZVxuLy8gYnJhY2UgY29uc3RydWN0aW9uIG9mIHRoZSBzYW1lIHZhcmlhbnQgd2l0aCB0aGUgc2FtZSBhcmd1bWVudHMgcHJvZHVjZSB0aGUgc2FtZSB2YWx1ZS5cbmVudW0gTWVzc2FnZSB7IFRleHQgeyBib2R5OiBTdHJpbmcgfSwgRW1wdHkgfVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHZpYV9jYWxsIDo9IE1lc3NhZ2U6OlRleHQoYm9keSA9IFwiaGVsbG9cIik7XG4gICAgbGV0IHZpYV9icmFjZSA6PSBNZXNzYWdlOjpUZXh0IHsgYm9keSA9IFwiaGVsbG9cIiB9O1xuICAgIGxldCBib2R5X2Zyb21fY2FsbCA6PSBtYXRjaCAodmlhX2NhbGwpIHtcbiAgICAgICAgTWVzc2FnZTo6VGV4dCB7IGJvZHkgfSA9PiBib2R5LFxuICAgICAgICBfID0+IFwiXCIudG9fc3RyaW5nKCksXG4gICAgfTtcbiAgICBsZXQgYm9keV9mcm9tX2JyYWNlIDo9IG1hdGNoICh2aWFfYnJhY2UpIHtcbiAgICAgICAgTWVzc2FnZTo6VGV4dCB7IGJvZHkgfSA9PiBib2R5LFxuICAgICAgICBfID0+IFwiXCIudG9fc3RyaW5nKCksXG4gICAgfTtcbiAgICBhc3NlcnQoYm9keV9mcm9tX2NhbGwgPT0gYm9keV9mcm9tX2JyYWNlKTtcblxuICAgIGxldCB1bml0X3ZpYV9jYWxsIDo9IE1lc3NhZ2U6OkVtcHR5KCk7XG4gICAgbGV0IHVuaXRfdmlhX2JhcmUgOj0gTWVzc2FnZTo6RW1wdHk7XG4gICAgbGV0IGlzX2VtcHR5X3ZpYV9jYWxsIDo9IG1hdGNoICh1bml0X3ZpYV9jYWxsKSB7XG4gICAgICAgIE1lc3NhZ2U6OkVtcHR5ID0+IHRydWUsXG4gICAgICAgIF8gPT4gZmFsc2UsXG4gICAgfTtcbiAgICBsZXQgaXNfZW1wdHlfdmlhX2JhcmUgOj0gbWF0Y2ggKHVuaXRfdmlhX2JhcmUpIHtcbiAgICAgICAgTWVzc2FnZTo6RW1wdHkgPT4gdHJ1ZSxcbiAgICAgICAgXyA9PiBmYWxzZSxcbiAgICB9O1xuICAgIGFzc2VydChpc19lbXB0eV92aWFfY2FsbCA9PSBpc19lbXB0eV92aWFfYmFyZSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9lbnVtcy9jYWxsX2FuZF9icmFjZV92YXJpYW50X2NvbnN0cnVjdGlvbl9wcm9kdWNlX3RoZV9zYW1lX3ZhbHVlLm10bCIsIm5hbWUiOiJjYWxsX2FuZF9icmFjZV92YXJpYW50X2NvbnN0cnVjdGlvbl9wcm9kdWNlX3RoZV9zYW1lX3ZhbHVlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

---
