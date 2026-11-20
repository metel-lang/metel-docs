---
sidebar_position: 4
---

# Type Ascription and Casting

## Type Ascription

The `:` operator [asserts that an expression has a given type](#spec.types.type-ascription.legality-1). It is a type-inference hint that also supplies the expected type for unsizing coercions; it never reads through a reference.

Type ascription is mainly an ergonomics feature. Most code should type-check from
its surrounding context alone; `:` is for the cases where spelling out the intended
type inline is clearer than introducing a separate annotated binding.

```metel
fun main() -> i64 {
    let xs := [] : [i64];
    let x  := 1 : i64;
    if (xs.len() == 0) { x } else { 0 }
}
```

[Ascription fails at compile time if the inferred type of the sub-expression cannot be unified with the ascribed type](#spec.types.type-ascription.legality-2). For example, `1 : String` is invalid. Use `as` to convert between types; use `:` only when the value already has the target type.

<!-- doc-example: expect-fail reason="demonstrates an ascription failure -- the type error is the point" -->
```metel
fun main() -> i64 {
    let y := 1 : String;
    return 0;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.type-ascription.legality-1}

`expr : T` constrains `expr` to type `T` and supplies `T` as its expected type. It never
reads a value out of a reference; it may apply the unsizing coercions that an expected type
already drives (`dyn` erasure, `[T; N]` to `[T]`, singleton types).

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../../rfcs/4-implemented/rfc-0021-type-ascription.md), [rfc-0023](../../../rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE1X2FzY3JpcHRpb25fa2VlcHNfZHluX2FuZF9hcnJheV92aWV3X2NvZXJjaW9ucy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDE4NTogYXNjcmlwdGlvbiBuZXZlciByZWFkcyB0aHJvdWdoIGEgcmVmZXJlbmNlLCBidXQgaXQgc3RpbGwgZHJpdmVzIHRoZVxuLy8gdW5zaXppbmcgY29lcmNpb25zIGFuIGV4cGVjdGVkIHR5cGUgYWxyZWFkeSBpbXBsaWVzIChkeW4gZXJhc3VyZSwgYFtUOyBOXWAgLT4gYFtUXWApLlxuYXNwZWN0IFNoYXBlIHsgZnVuIGFyZWEoJnNlbGYpIC0+IGk2NDsgfVxuc3RydWN0IFNxIHsgczogaTY0IH1cbmV4dGVuZCBTcTogU2hhcGUgeyBmdW4gYXJlYSgmc2VsZikgLT4gaTY0IHsgc2VsZi5zICogc2VsZi5zIH0gfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZCA6PSAoU3EgeyBzID0gMyB9OiBkeW4gU2hhcGUpO1xuICAgIGFzc2VydChkLmFyZWEoKSA9PSA5KTtcblxuICAgIGxldCB2IDo9IChbMSwgMiwgM106IFtpNjRdKTtcbiAgICBhc3NlcnQodi5sZW4oKSA9PSAzKTtcblxuICAgIGxldCBuIDo9IDU7XG4gICAgbGV0IHI6ICZpNjQgOj0gJm47XG4gICAgYXNzZXJ0KCgqcjogaTY0KSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTVfYXNjcmlwdGlvbl9rZWVwc19keW5fYW5kX2FycmF5X3ZpZXdfY29lcmNpb25zLm10bCIsIm5hbWUiOiIxNV9hc2NyaXB0aW9uX2tlZXBzX2R5bl9hbmRfYXJyYXlfdmlld19jb2VyY2lvbnMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgODogdHlwZSBhc2NyaXB0aW9uIG9wZXJhdG9yIGA6YC5cblxuLy8gRW1wdHkgYXJyYXkgZWxlbWVudCB0eXBlIHJlc29sdmVkIHZpYSBhc2NyaXB0aW9uXG5sZXQgbjogW2k2NF0gOj0gW10gOiBbaTY0XTtcblxuLy8gSWRlbnRpdHkgYXNjcmlwdGlvbiBvbiBhIGxpdGVyYWxcbmxldCB4OiBpNjQgOj0gMSA6IGk2NDtcblxuLy8gQXNjcmlwdGlvbiBvbiBhIHZhcmlhYmxlIHJlZmVyZW5jZVxuZnVuIGNoZWNrX3ZhcigpIHtcbiAgICBsZXQgdjogYm9vbGVhbiA6PSB0cnVlO1xuICAgIGxldCB3OiBib29sZWFuIDo9IHYgOiBib29sZWFuO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluIGFyZ3VtZW50IHBvc2l0aW9uXG5mdW4gdGFrZV9pbnRzKGFycjogW2k2NF0pIC0+IGk2NCB7IGFyci5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHRha2VfaW50cyhbXSA6IFtpNjRdKTtcblxuLy8gQXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHR3byBlbXB0eS1hcnJheSBhcmd1bWVudHNcbmZ1biB0d29fYXJyYXlzKGE6IFtpNjRdLCBiOiBbZjY0XSkgLT4gaTY0IHsgYS5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHR3b19hcnJheXMoW10gOiBbaTY0XSwgW10gOiBbZjY0XSk7XG5cbi8vIEFzY3JpcHRpb24gb24gYSBzdHJ1Y3QgbGl0ZXJhbFxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuZnVuIGNoZWNrX3N0cnVjdCgpIHtcbiAgICBsZXQgcDogUG9pbnQgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSA6IFBvaW50O1xufVxuXG4vLyBBc2NyaXB0aW9uIG9uIGEgdHVwbGVcbmZ1biBjaGVja190dXBsZSgpIHtcbiAgICBsZXQgdDogKGk2NCwgYm9vbGVhbikgOj0gKDEsIHRydWUpIDogKGk2NCwgYm9vbGVhbik7XG59XG5cbi8vIEFzY3JpcHRpb24gYXMgdGhlIHRhaWwgZXhwcmVzc2lvbiBvZiBhIGZ1bmN0aW9uIGJvZHlcbmZ1biByZXR1cm5zX2FzY3JpYmVkKCkgLT4gaTY0IHtcbiAgICA0MiA6IGk2NFxufVxuXG4vLyBBc2NyaXB0aW9uIHJlc29sdmVzIHRoZSB0eXBlIG9mIGFuIHVuYW5ub3RhdGVkIGxldCBiaW5kaW5nXG5mdW4gY2hlY2tfaW5mZXJyZWQoKSB7XG4gICAgbGV0IGFyciA6PSBbXSA6IFtpNjRdO1xuICAgIGxldCBfOiBpNjQgOj0gYXJyLmxlbigpO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluc2lkZSBhIGJpbmFyeSBleHByZXNzaW9uIG9wZXJhbmRcbmZ1biBjaGVja19iaW5vcCgpIHtcbiAgICBsZXQgXzogYm9vbGVhbiA6PSAoMSA6IGk2NCkgPT0gMTtcbn1cblxuLy8gYXMgY29udmVyc2lvbiBzdGlsbCB3b3JrcyBhbG9uZ3NpZGUgYXNjcmlwdGlvblxubGV0IGY6IGY2NCA6PSAxIGFzIGY2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InR1cmJvZmlzaF9yZXR1cm5fYW5kX2FzY3JpcHRpb25fcGFyYW1faW5fc2FtZV9jYWxsLm10bCIsInNvdXJjZSI6Ii8vIFR1cmJvZmlzaCBkaXNhbWJpZ3VhdGVzIFQsIHdoaWNoIGFwcGVhcnMgb25seSBpbiB0aGUgcmV0dXJuIHBvc2l0aW9uO1xuLy8gYXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHRoZSBvdGhlcndpc2UtYW1iaWd1b3VzIGBOb25lYCBhcmd1bWVudCwgc2luY2UgYVxuLy8gZ2VuZXJpYy1zY2hlbWUgY2FsbGVlJ3Mgb3duIHBhcmFtZXRlciB0eXBlcyBhcmVuJ3QgYXZhaWxhYmxlIGFzIGhpbnRzIGZvclxuLy8gaXRzIGFyZ3VtZW50cyBhdCBhbGwgKHVubGlrZSBhIGNvbmNyZXRlLCBub24tZ2VuZXJpYyBjYWxsZWUpIC0tIGJvdGhcbi8vIG1lY2hhbmlzbXMgYXJlIGRvaW5nIHJlYWwsIGluZGVwZW5kZW50IHdvcmsgaW4gdGhlIHNhbWUgY2FsbC5cbmZ1biBtYWtlPFQ+KGZhbGxiYWNrOiBPcHRpb248aTY0PikgLT4gVCB7XG4gICAgcmV0dXJuIG1ha2UoZmFsbGJhY2spO1xufVxuXG5mdW4gbWFpbigpIHtcbiAgICBtYWtlOjo8aTY0PihOb25lIDogT3B0aW9uPGk2ND4pO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvZ2VuZXJpY3MvdHVyYm9maXNoX3JldHVybl9hbmRfYXNjcmlwdGlvbl9wYXJhbV9pbl9zYW1lX2NhbGwubXRsIiwibmFtZSI6InR1cmJvZmlzaF9yZXR1cm5fYW5kX2FzY3JpcHRpb25fcGFyYW1faW5fc2FtZV9jYWxsLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-2}

An ascription is valid only when the expression's type unifies with the ascribed type;
otherwise it is a type error.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzAyX2FzY3JpYmVfdHlwZV9taXNtYXRjaC5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA4IG5lZ2F0aXZlOiBhc2NyaXB0aW9uIHdpdGggaW5jb21wYXRpYmxlIHR5cGUgaXMgYSB0eXBlIGVycm9yLlxuLy8gYDEgOiBmNjRgIGlzIGFuIGVycm9yIFx1MjAxNCB1c2UgYDEgYXMgZjY0YCB0byBjb252ZXJ0LlxuXG5sZXQgejogZjY0IDo9IDEgOiBmNjQ7IC8vIEVSUk9SW1QwMDAxXVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYnVpbHRpbnMvc3RhZ2U4X25lZ18wMl9hc2NyaWJlX3R5cGVfbWlzbWF0Y2gubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDJfYXNjcmliZV90eXBlX21pc21hdGNoLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-3}

An expression may contain at most one type ascription; a second `:` in the same ascription
position is a parse error.

<!-- rfc.py:last_reviewed e7d2c1d4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzA4X2NoYWluZWRfdHlwZV9hc2NyaXB0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDIxIFx1MDBhNzQ6IGFuIGV4cHJlc3Npb24gYWNjZXB0cyBhdCBtb3N0IG9uZSB0eXBlIGFzY3JpcHRpb24uXG5sZXQgdmFsdWUgOj0gMSA6IGk2NCA6IGk2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### When ascription helps

Type inference uses surrounding expected types. That expected type can come from a `let` annotation, a function return type, a callee's parameter types, or the surrounding expression context.

Because of that, ambiguous literals like `[]` and `None` often type-check without explicit ascription when the context already determines their type:

```metel
fun zip_lengths(a: [i64], b: [String]) -> i64 {
    return a.len() + b.len();
}

fun make_row(use_default: boolean, fallback: [i64]) -> [i64] {
    return match (use_default) {
        true  => [],
        false => fallback,
    };
}

fun first_or_default(items: [i64], fallback: Option<i64>) -> i64 {
    return match (fallback) {
        Some { value } => value,
        None => if (items.len() > 0) { items[0] } else { 0 },
    };
}

fun main() -> i64 {
    let total := zip_lengths([], ["a", "b"]);
    let built := make_row(true, [1, 2, 3]);
    let first := first_or_default([1, 2, 3], None);
    return total + built.len() + first;
}
```

Ascription is still useful when no surrounding context fixes the type:

```metel
fun main() -> i64 {
    let arr := [] : [i64];
    let value := None : Option<i64>;
    match (value) {
        Some { value } => value + arr.len(),
        None => arr.len(),
    }
}
```

Without such context, ambiguous literals remain a type error. For example, `let x = None;` does not provide enough information to infer the element type.

<!-- doc-example: expect-fail reason="demonstrates an ambiguous None -- the type error is the point" -->
```metel
fun main() -> i64 {
    let x := None;
    return 0;
}
```

## Type Casting

The `as` operator [performs an explicit conversion from `expr`'s type to `T`](#spec.types.type-casting.dynamics-1). It desugars to a call to the `From` aspect and is infallible — the result is the target type directly.

```metel
fun main() {
    let x: i32 := 1000i32;
    let b: i8  := x as i8;    // wraps: 1000 mod 256 → -24
    let f: f32 := x as f32;   // 1000.0f32
    let u: u64 := x as u64;   // 1000u64

    let pi: f64 := 3.14;
    let n: i32  := pi as i32; // truncates toward zero → 3
}
```

All pairwise casts among `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`, `f32`, `f64` are supported. Narrowing integer casts wrap (two's-complement truncation). f64-to-integer casts truncate toward zero.

Because `as` desugars to `From`, user-defined types become castable by implementing `From<SourceType>` for the target type.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.type-casting.dynamics-1}

`expr as T` evaluates an explicit conversion of `expr` to `T` via `From<S>::from` (where
`S` is `expr`'s type) and produces a value of type `T`. Not restricted to numeric types —
any type with an applicable `From<S>` implementation is a valid cast target.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgODogdHlwZSBhc2NyaXB0aW9uIG9wZXJhdG9yIGA6YC5cblxuLy8gRW1wdHkgYXJyYXkgZWxlbWVudCB0eXBlIHJlc29sdmVkIHZpYSBhc2NyaXB0aW9uXG5sZXQgbjogW2k2NF0gOj0gW10gOiBbaTY0XTtcblxuLy8gSWRlbnRpdHkgYXNjcmlwdGlvbiBvbiBhIGxpdGVyYWxcbmxldCB4OiBpNjQgOj0gMSA6IGk2NDtcblxuLy8gQXNjcmlwdGlvbiBvbiBhIHZhcmlhYmxlIHJlZmVyZW5jZVxuZnVuIGNoZWNrX3ZhcigpIHtcbiAgICBsZXQgdjogYm9vbGVhbiA6PSB0cnVlO1xuICAgIGxldCB3OiBib29sZWFuIDo9IHYgOiBib29sZWFuO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluIGFyZ3VtZW50IHBvc2l0aW9uXG5mdW4gdGFrZV9pbnRzKGFycjogW2k2NF0pIC0+IGk2NCB7IGFyci5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHRha2VfaW50cyhbXSA6IFtpNjRdKTtcblxuLy8gQXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHR3byBlbXB0eS1hcnJheSBhcmd1bWVudHNcbmZ1biB0d29fYXJyYXlzKGE6IFtpNjRdLCBiOiBbZjY0XSkgLT4gaTY0IHsgYS5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHR3b19hcnJheXMoW10gOiBbaTY0XSwgW10gOiBbZjY0XSk7XG5cbi8vIEFzY3JpcHRpb24gb24gYSBzdHJ1Y3QgbGl0ZXJhbFxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuZnVuIGNoZWNrX3N0cnVjdCgpIHtcbiAgICBsZXQgcDogUG9pbnQgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSA6IFBvaW50O1xufVxuXG4vLyBBc2NyaXB0aW9uIG9uIGEgdHVwbGVcbmZ1biBjaGVja190dXBsZSgpIHtcbiAgICBsZXQgdDogKGk2NCwgYm9vbGVhbikgOj0gKDEsIHRydWUpIDogKGk2NCwgYm9vbGVhbik7XG59XG5cbi8vIEFzY3JpcHRpb24gYXMgdGhlIHRhaWwgZXhwcmVzc2lvbiBvZiBhIGZ1bmN0aW9uIGJvZHlcbmZ1biByZXR1cm5zX2FzY3JpYmVkKCkgLT4gaTY0IHtcbiAgICA0MiA6IGk2NFxufVxuXG4vLyBBc2NyaXB0aW9uIHJlc29sdmVzIHRoZSB0eXBlIG9mIGFuIHVuYW5ub3RhdGVkIGxldCBiaW5kaW5nXG5mdW4gY2hlY2tfaW5mZXJyZWQoKSB7XG4gICAgbGV0IGFyciA6PSBbXSA6IFtpNjRdO1xuICAgIGxldCBfOiBpNjQgOj0gYXJyLmxlbigpO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluc2lkZSBhIGJpbmFyeSBleHByZXNzaW9uIG9wZXJhbmRcbmZ1biBjaGVja19iaW5vcCgpIHtcbiAgICBsZXQgXzogYm9vbGVhbiA6PSAoMSA6IGk2NCkgPT0gMTtcbn1cblxuLy8gYXMgY29udmVyc2lvbiBzdGlsbCB3b3JrcyBhbG9uZ3NpZGUgYXNjcmlwdGlvblxubGV0IGY6IGY2NCA6PSAxIGFzIGY2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>
