# Runtime

## Panics

A panic is a [hard, unrecoverable runtime error](#spec.runtime.panics.dynamics-1). It prints a message and exits the process with a non-zero status. Panics cannot be caught.

Panics are triggered by:
- `.yolo()` on `None` or an `Err`
- Out-of-bounds array access
- Integer division by zero
- `assert(false)` or `assert(false, msg)`
- `panic(msg)`, called directly

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.panics.dynamics-1}

A panic prints its message, terminates the process with a non-zero status, and cannot be
caught. Calling `panic`, a failing `assert`, `.yolo()` on an absent or error variant,
out-of-bounds array access, and integer division by zero trigger a panic.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImJvb20iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX3BhbmljLm10bCIsInNvdXJjZSI6Ii8vIFJVTlRJTUVfRVJST1JbYm9vbV1cbi8vIFJGQy0wMDc4OiBwYW5pYyhtc2cpIGFsd2F5cyBwYW5pY3MgKFIwMDE1KSB3aXRoIHRoZSBnaXZlbiBtZXNzYWdlLlxuZnVuIG1haW4oKSB7XG4gICAgcGFuaWMoXCJib29tXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbmV2ZXIvbmVnX3BhbmljLm10bCIsIm5hbWUiOiJuZWdfcGFuaWMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Built-in Functions

These are available in every module without any `import` declaration (provided by `std::core` auto-import):

| Name              | Signature                            | Description                              |
|-------------------|--------------------------------------|------------------------------------------|
| `print`           | `<T>(v: T)`                          | Print to stdout, no newline              |
| `println`         | `<T>(v: T)`                          | Print to stdout with newline             |
| `clock`           | `() -> i64`                          | Unix timestamp in milliseconds          |
| `assert`          | `(cond: boolean)`                    | Panic with `"assertion failed"` if `cond` is `false` |
| `assert`          | `(cond: boolean, msg: String)`       | Overload: panic with `msg` if `cond` is `false` |
| `dbg`             | `<T>(v: T) -> T`                     | Print `[dbg] <value>` to stderr and return the value unchanged |
| `panic`           | `(msg: String) -> !`                 | Panic unconditionally with `msg` (RFC-0078) |

`assert` is overloaded — [the two-argument form carries the panic message](#spec.runtime.built-in-functions.dynamics-2).

`panic`'s return type `!` [coerces to whatever type its calling context expects](types.md#spec.types.never-type.legality-2) — see [Never Type](types.md#never-type).

`print` and `println` [require their argument to implement `Display`](#spec.runtime.built-in-functions.legality-1)
(`print<T: Display>`): passing a struct or enum with no `Display`
implementation is a compile-time error. A value whose type implements `Display`
is [printed through that implementation's `to_string`](#spec.runtime.built-in-functions.dynamics-1) — user structs and enums,
not only the built-in primitives.

String length is a method, not a free function: `"hello".len()` returns the
number of characters (Unicode scalar values). Strings are concatenated with
the `+` operator.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-functions.legality-1}

`print` and `println` accept only values whose type implements `Display`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6ImRvZXMgbm90IGltcGxlbWVudCBgRGlzcGxheWAiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzAyX3ByaW50bG5fcmVxdWlyZXNfZGlzcGxheS5tdGwiLCJzb3VyY2UiOiIvLyBwcmludGxuL3ByaW50IHJlcXVpcmUgRGlzcGxheSAoTUVURUwtMTgxKTogcGFzc2luZyBhIHR5cGUgd2l0aCBub1xuLy8gRGlzcGxheSBpbXBsIGlzIGEgY29tcGlsZS10aW1lIGVycm9yLCBub3QgYSBydW50aW1lIHBhbmljLlxuXG5zdHJ1Y3QgVGVzdCB7XG4gICAgYXR0cjogaTgsXG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB4IDo9IFRlc3QgeyBhdHRyID0gMWk4IH07XG4gICAgcHJpbnRsbih4KTsgLy8gRVJST1JbVDAwMTJdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9idWlsdGlucy9zdGFnZThfbmVnXzAyX3ByaW50bG5fcmVxdWlyZXNfZGlzcGxheS5tdGwiLCJuYW1lIjoic3RhZ2U4X25lZ18wMl9wcmludGxuX3JlcXVpcmVzX2Rpc3BsYXkubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-1}

`print` writes a `Display` value's `to_string` result to stdout without a newline; `println`
writes the same result followed by a newline.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc3X3ByaW50bG5fdXNlcl9kaXNwbGF5Lm10bCIsInNvdXJjZSI6Ii8vIHByaW50L3ByaW50bG4gbXVzdCBkaXNwYXRjaCBhIHVzZXItZGVmaW5lZCBgRGlzcGxheWAgaW1wbCwgbm90IG9ubHkgZm9ybWF0XG4vLyBwcmltaXRpdmVzLiBCZWZvcmUgTUVURUwtMTkyIHRoZXNlIGNhbGxzIHR5cGVjaGVja2VkIGJ1dCBwYW5pY2tlZCBhdCBydW50aW1lXG4vLyB3aXRoIFIwMDA5IGJlY2F1c2UgdGhlIGhvc3QgZm9ybWF0dGVyIG9ubHkgaGFuZGxlZCBwcmltaXRpdmUgdmFsdWVzLiBUaGVcbi8vIHB1YmxpYyBwcmludC9wcmludGxuIG5vdyBsb3dlciB0byBgeC50b19zdHJpbmcoKWAgaW4tbGFuZ3VhZ2UsIHNvIGFueVxuLy8gYERpc3BsYXlgIHZhbHVlIChzdHJ1Y3QsIGVudW0sIHByaW1pdGl2ZSkgcHJpbnRzIHZpYSBpdHMgb3duIGltcGwuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZXh0ZW5kIFBvaW50OiBEaXNwbGF5IHtcblx0ZnVuIHRvX3N0cmluZygmc2VsZikgLT4gU3RyaW5nIHtcblx0XHRcIigke3NlbGYueH0sICR7c2VsZi55fSlcIlxuXHR9XG59XG5cbmVudW0gQ29sb3IgeyBSZWQsIEdyZWVuIH1cblxuZXh0ZW5kIENvbG9yOiBEaXNwbGF5IHtcblx0ZnVuIHRvX3N0cmluZygmc2VsZikgLT4gU3RyaW5nIHtcblx0XHRtYXRjaCAoc2VsZikge1xuXHRcdFx0Q29sb3I6OlJlZCA9PiBcInJlZFwiLFxuXHRcdFx0Q29sb3I6OkdyZWVuID0+IFwiZ3JlZW5cIixcblx0XHR9XG5cdH1cbn1cblxuZnVuIG1haW4oKSB7XG5cdC8vIHN0cnVjdCB3aXRoIGEgdXNlciBEaXNwbGF5IGltcGxcblx0cHJpbnRsbihQb2ludCB7IHggPSAxLCB5ID0gMiB9KTtcblx0Ly8gZW51bSB3aXRoIGEgdXNlciBEaXNwbGF5IGltcGxcblx0cHJpbnQoQ29sb3I6OlJlZCk7XG5cdHByaW50bG4oQ29sb3I6OkdyZWVuKTtcblx0Ly8gcHJpbWl0aXZlcyBtdXN0IHN0aWxsIHByaW50IHVuY2hhbmdlZFxuXHRwcmludGxuKDQyKTtcblx0cHJpbnRsbihcImRvbmVcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9mdW5jdGlvbnMvNzdfcHJpbnRsbl91c2VyX2Rpc3BsYXkubXRsIiwibmFtZSI6Ijc3X3ByaW50bG5fdXNlcl9kaXNwbGF5Lm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-2}

`assert(false)` panics with `"assertion failed"`; `assert(false, msg)` panics with `msg`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImN1c3RvbSBhc3NlcnRpb24gZmFpbHVyZSIsImxpbmUiOm51bGwsInN0YXR1cyI6InJ1bnRpbWVfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiI4MF9hc3NlcnRfcGFuaWNfbWVzc2FnZXMubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGZhbHNlLCBcImN1c3RvbSBhc3NlcnRpb24gZmFpbHVyZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2J1aWx0aW5zLzgwX2Fzc2VydF9wYW5pY19tZXNzYWdlcy5tdGwiLCJuYW1lIjoiODBfYXNzZXJ0X3BhbmljX21lc3NhZ2VzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-3}

`dbg(v)` writes its debug rendering to stderr and evaluates to `v` unchanged.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImRiZ19idWlsdGluLm10bCIsInNvdXJjZSI6Ii8vIGRiZyh4KSBcdTIwMTQgcHJpbnQtYW5kLXJldHVybjogcHJpbnRzIHRvIHN0ZGVyciwgcmV0dXJucyB2YWx1ZSB1bmNoYW5nZWQuXG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFNjYWxhciB0eXBlcyBwYXNzIHRocm91Z2ggdW5jaGFuZ2VkLlxuICAgIGxldCB4OiBpNjQgOj0gZGJnKDQyKTtcbiAgICBhc3NlcnQoeCA9PSA0Mik7XG5cbiAgICBsZXQgYjogYm9vbGVhbiA6PSBkYmcodHJ1ZSk7XG4gICAgYXNzZXJ0KGIgPT0gdHJ1ZSk7XG5cbiAgICBsZXQgczogU3RyaW5nIDo9IGRiZyhcImhlbGxvXCIpO1xuICAgIGFzc2VydChzID09IFwiaGVsbG9cIik7XG5cbiAgICAvLyBBcml0aG1ldGljIGV4cHJlc3Npb24gcGFzc2VkIHRocm91Z2guXG4gICAgbGV0IHk6IGk2NCA6PSBkYmcoMiArIDMpO1xuICAgIGFzc2VydCh5ID09IDUpO1xuXG4gICAgLy8gSW5saW5lOiBkYmcoeCkgaW5zaWRlIGEgbGFyZ2VyIGV4cHJlc3Npb24uXG4gICAgbGV0IHo6IGk2NCA6PSBkYmcoMTApICogMjtcbiAgICBhc3NlcnQoeiA9PSAyMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9idWlsdGlucy9kYmdfYnVpbHRpbi5tdGwiLCJuYW1lIjoiZGJnX2J1aWx0aW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.built-in-functions.dynamics-4}

`clock()` returns the current Unix timestamp in milliseconds.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgxX2Nsb2NrX2lzX3VuaXhfbWlsbGlzZWNvbmRzLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCBiZWZvcmUgOj0gY2xvY2soKTtcbiAgICBsZXQgYWZ0ZXIgOj0gY2xvY2soKTtcbiAgICBhc3NlcnQoYmVmb3JlID4gMV82MDBfMDAwXzAwMF8wMDBpNjQpO1xuICAgIGFzc2VydChhZnRlciA+PSBiZWZvcmUpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvODFfY2xvY2tfaXNfdW5peF9taWxsaXNlY29uZHMubXRsIiwibmFtZSI6IjgxX2Nsb2NrX2lzX3VuaXhfbWlsbGlzZWNvbmRzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## Built-in Aspects

The following aspects are pre-implemented for built-in types:

### Display

```metel
aspect Display {
    fun to_string(&self) -> String;
}
```

[`i64`, `f64`, `boolean`, `String`, and `Char` implement `Display`](#spec.runtime.built-in-aspects.display.legality-1). `.to_string()` returns the canonical string representation. `print` and `println` accept any `Display` type.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.display.legality-1}

`i64`, `f64`, `boolean`, `String`, and `Char` have built-in `Display` implementations whose
`to_string` methods return their canonical string representations.

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIiwic291cmNlIjoiLy8gVGhlIHByaW1pdGl2ZSBEaXNwbGF5IGltcGxzIGFuZCB0aGUgbnVtZXJpYyBGcm9tIGNyb3NzLXByb2R1Y3QgYXJlIGRlY2xhcmVkXG4vLyBpbiB0aGUgZW1iZWRkZWQgc3RkOjpjb3JlIHNvdXJjZSAoc3RkbGliL2NvcmUubXRsKSBhbmQgYm91bmQgdG8gaG9zdFxuLy8gaW1wbGVtZW50YXRpb25zIHZpYSBuYXRpdmUga2V5cyAoTUVURUwtMTgxKS4gVGhpcyBsb2NrcyB0aGUgZGVyaXZlZCBwYXRoOlxuLy8gbm8gaGFuZC1yZWdpc3RlcmVkIGJ1aWx0aW4gYmFja3MgYW55IG9mIHRoZXNlLlxuZnVuIG1haW4oKSB7XG4gICAgLy8gRGlzcGxheTo6dG9fc3RyaW5nIG9uIGV2ZXJ5IGRpc3BsYXlhYmxlIHByaW1pdGl2ZSBraW5kXG4gICAgYXNzZXJ0KDQyaTgudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpMTYudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpMzIudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpNjQudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJ1OC50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnUxNi50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnUzMi50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnU2NC50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpID09IFwidHJ1ZVwiKTtcbiAgICBhc3NlcnQoJ0EnLnRvX3N0cmluZygpID09IFwiQVwiKTtcbiAgICBhc3NlcnQoXCJoaVwiLnRvX3N0cmluZygpID09IFwiaGlcIik7XG5cbiAgICAvLyBOdW1lcmljIEZyb20gY29udmVyc2lvbnMgdmlhIGNhc3RzIChpbnQgXHUyMTkyIGludCwgaW50IFx1MjE5MiBmbG9hdCwgZmxvYXQgXHUyMTkyIGludClcbiAgICBsZXQgYTogaTggOj0gN2k2NCBhcyBpODtcbiAgICBhc3NlcnQoYSA9PSA3aTgpO1xuICAgIGxldCBiOiB1NjQgOj0gN2k4IGFzIHU2NDtcbiAgICBhc3NlcnQoYiA9PSA3dTY0KTtcbiAgICBsZXQgYzogZjMyIDo9IDJpNjQgYXMgZjMyO1xuICAgIGxldCBkOiBpNjQgOj0gYyBhcyBpNjQ7XG4gICAgYXNzZXJ0KGQgPT0gMik7XG4gICAgbGV0IGU6IGY2NCA6PSAzaTMyIGFzIGY2NDtcbiAgICBsZXQgZjogaTMyIDo9IGUgYXMgaTMyO1xuICAgIGFzc2VydChmID09IDMpO1xuXG4gICAgLy8gQ2hhciBcdTIxOTQgdTMyIChVbmljb2RlIGNvZGUgcG9pbnQpXG4gICAgbGV0IGNvZGU6IHUzMiA6PSAnWicgYXMgdTMyO1xuICAgIGFzc2VydChjb2RlID09IDkwdTMyKTtcbiAgICBsZXQgY2g6IENoYXIgOj0gOTB1MzIgYXMgQ2hhcjtcbiAgICBhc3NlcnQoY2ggPT0gJ1onKTtcblxuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2J1aWx0aW5zLzgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIiwibmFtZSI6IjgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

### Iterable\<T\>

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}
```

[`T[]` (array) and `Range` (from `..` / `..=`) implement `Iterable<T>`](#spec.runtime.built-in-aspects.iterable-t.legality-1). User-defined types may implement it to be usable in `for-in`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.iterable-t.legality-1}

Arrays and ranges implement `Iterable<T>`; a user-defined type is usable in `for-in` only
when it implements that aspect.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjU5X2l0ZXJhYmxlX2FzcGVjdC5tdGwiLCJzb3VyY2UiOiIvLyBVc2VyLWRlZmluZWQgSXRlcmFibGUgdmlhIGFzcGVjdCBcdTIwMTQgZm9yLWluIGRpc3BhdGNoZXMgdGhyb3VnaCBuZXh0KCkuXG5cbmFzcGVjdCBJdGVyYWJsZTxUPiB7XG4gICAgZnVuIG5leHQoJnZhciBzZWxmKSAtPiBQZXJoYXBzPFQ+O1xufVxuXG5zdHJ1Y3QgQ291bnRlciB7XG4gICAgY3VycmVudDogaTY0LFxuICAgIGxpbWl0OiAgIGk2NCxcbn1cblxuZXh0ZW5kIENvdW50ZXIge1xuICAgIGZ1biBuZXcobGltaXQ6IGk2NCkgLT4gQ291bnRlciB7XG4gICAgICAgIHJldHVybiBDb3VudGVyIHsgY3VycmVudCA9IDAsIGxpbWl0ID0gbGltaXQgfTtcbiAgICB9XG59XG5cbmV4dGVuZCBDb3VudGVyOiBJdGVyYWJsZTxpNjQ+IHtcbiAgICBmdW4gbmV4dCgmdmFyIHNlbGYpIC0+IFBlcmhhcHM8aTY0PiB7XG4gICAgICAgIGlmIChzZWxmLmN1cnJlbnQgPCBzZWxmLmxpbWl0KSB7XG4gICAgICAgICAgICBsZXQgdmFsIDo9IHNlbGYuY3VycmVudDtcbiAgICAgICAgICAgIHNlbGYuY3VycmVudCA6PSBzZWxmLmN1cnJlbnQgKyAxO1xuICAgICAgICAgICAgcmV0dXJuIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IHZhbCB9O1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiBOb25lO1xuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIGxldCBjIDo9IENvdW50ZXI6Om5ldyg1KTtcbiAgICBmb3IgKHggaW4gYykge1xuICAgICAgICBzdW0gKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSAxMCk7IC8vIDArMSsyKzMrNFxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYXNwZWN0cy81OV9pdGVyYWJsZV9hc3BlY3QubXRsIiwibmFtZSI6IjU5X2l0ZXJhYmxlX2FzcGVjdC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

### From\<S\>

```metel
aspect From<S> {
    fun from(value: S) -> Self;
}
```

[`i64` implements `From<f64>` (truncating cast) and `f64` implements `From<i64>`](#spec.runtime.built-in-aspects.from-s.legality-1). The [`as` operator desugars to `T::from(value)`](types.md#spec.types.type-casting.dynamics-1). User-defined types may implement `From<S>` to enable `as` casts and `?` error coercion.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.built-in-aspects.from-s.legality-1}

`i64` implements `From<f64>` and `f64` implements `From<i64>`; user-defined `From<S>`
implementations make their target type available for `as` casts and `?` error coercion.

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjYxX3Byb3BhZ2F0ZV9lcnJvcl9jb2VyY2lvbi5tdGwiLCJzb3VyY2UiOiIvLyBgP2Agb3BlcmF0b3Igd2l0aCBGcm9tIGNvZXJjaW9uOiBFMSAhPSBFMi5cblxuYXNwZWN0IEZyb208VD4ge1xuICAgIGZ1biBmcm9tKHZhbHVlOiBUKSAtPiBTZWxmO1xufVxuXG5zdHJ1Y3QgUGFyc2VFcnJvciB7XG4gICAgbXNnOiBTdHJpbmcsXG59XG5cbnN0cnVjdCBBcHBFcnJvciB7XG4gICAgbXNnOiBTdHJpbmcsXG59XG5cbmV4dGVuZCBBcHBFcnJvcjogRnJvbTxQYXJzZUVycm9yPiB7XG4gICAgZnVuIGZyb20odmFsdWU6IFBhcnNlRXJyb3IpIC0+IEFwcEVycm9yIHtcbiAgICAgICAgcmV0dXJuIEFwcEVycm9yIHsgbXNnID0gXCJwYXJzZSBlcnJvcjogXCIgKyB2YWx1ZS5tc2cgfTtcbiAgICB9XG59XG5cbmZ1biBwYXJzZV9pbnQoczogU3RyaW5nKSAtPiBSZXN1bHQ8aTY0LCBQYXJzZUVycm9yPiB7XG4gICAgaWYgKHMgPT0gXCI0MlwiKSB7XG4gICAgICAgIHJldHVybiBSZXN1bHQ6Ok9rIHsgdmFsdWUgPSA0MiB9O1xuICAgIH1cbiAgICByZXR1cm4gUmVzdWx0OjpFcnIgeyBlcnJvciA9IFBhcnNlRXJyb3IgeyBtc2cgPSBcImludmFsaWQgaW50ZWdlclwiIH0gfTtcbn1cblxuZnVuIGxvYWQoczogU3RyaW5nKSAtPiBSZXN1bHQ8aTY0LCBBcHBFcnJvcj4ge1xuICAgIGxldCBuIDo9IHBhcnNlX2ludChzKT87XG4gICAgcmV0dXJuIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IG4gKiAyIH07XG59XG5cbmZ1biBtYWluKCkge1xuICAgIG1hdGNoIChsb2FkKFwiNDJcIikpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDg0KSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIG1hdGNoIChsb2FkKFwiYmFkXCIpKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IubXNnID09IFwicGFyc2UgZXJyb3I6IGludmFsaWQgaW50ZWdlclwiKSxcbiAgICB9O1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZXJyb3JfaGFuZGxpbmcvNjFfcHJvcGFnYXRlX2Vycm9yX2NvZXJjaW9uLm10bCIsIm5hbWUiOiI2MV9wcm9wYWdhdGVfZXJyb3JfY29lcmNpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIiwic291cmNlIjoiLy8gVGhlIHByaW1pdGl2ZSBEaXNwbGF5IGltcGxzIGFuZCB0aGUgbnVtZXJpYyBGcm9tIGNyb3NzLXByb2R1Y3QgYXJlIGRlY2xhcmVkXG4vLyBpbiB0aGUgZW1iZWRkZWQgc3RkOjpjb3JlIHNvdXJjZSAoc3RkbGliL2NvcmUubXRsKSBhbmQgYm91bmQgdG8gaG9zdFxuLy8gaW1wbGVtZW50YXRpb25zIHZpYSBuYXRpdmUga2V5cyAoTUVURUwtMTgxKS4gVGhpcyBsb2NrcyB0aGUgZGVyaXZlZCBwYXRoOlxuLy8gbm8gaGFuZC1yZWdpc3RlcmVkIGJ1aWx0aW4gYmFja3MgYW55IG9mIHRoZXNlLlxuZnVuIG1haW4oKSB7XG4gICAgLy8gRGlzcGxheTo6dG9fc3RyaW5nIG9uIGV2ZXJ5IGRpc3BsYXlhYmxlIHByaW1pdGl2ZSBraW5kXG4gICAgYXNzZXJ0KDQyaTgudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpMTYudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpMzIudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJpNjQudG9fc3RyaW5nKCkgPT0gXCI0MlwiKTtcbiAgICBhc3NlcnQoNDJ1OC50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnUxNi50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnUzMi50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCg0MnU2NC50b19zdHJpbmcoKSA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpID09IFwidHJ1ZVwiKTtcbiAgICBhc3NlcnQoJ0EnLnRvX3N0cmluZygpID09IFwiQVwiKTtcbiAgICBhc3NlcnQoXCJoaVwiLnRvX3N0cmluZygpID09IFwiaGlcIik7XG5cbiAgICAvLyBOdW1lcmljIEZyb20gY29udmVyc2lvbnMgdmlhIGNhc3RzIChpbnQgXHUyMTkyIGludCwgaW50IFx1MjE5MiBmbG9hdCwgZmxvYXQgXHUyMTkyIGludClcbiAgICBsZXQgYTogaTggOj0gN2k2NCBhcyBpODtcbiAgICBhc3NlcnQoYSA9PSA3aTgpO1xuICAgIGxldCBiOiB1NjQgOj0gN2k4IGFzIHU2NDtcbiAgICBhc3NlcnQoYiA9PSA3dTY0KTtcbiAgICBsZXQgYzogZjMyIDo9IDJpNjQgYXMgZjMyO1xuICAgIGxldCBkOiBpNjQgOj0gYyBhcyBpNjQ7XG4gICAgYXNzZXJ0KGQgPT0gMik7XG4gICAgbGV0IGU6IGY2NCA6PSAzaTMyIGFzIGY2NDtcbiAgICBsZXQgZjogaTMyIDo9IGUgYXMgaTMyO1xuICAgIGFzc2VydChmID09IDMpO1xuXG4gICAgLy8gQ2hhciBcdTIxOTQgdTMyIChVbmljb2RlIGNvZGUgcG9pbnQpXG4gICAgbGV0IGNvZGU6IHUzMiA6PSAnWicgYXMgdTMyO1xuICAgIGFzc2VydChjb2RlID09IDkwdTMyKTtcbiAgICBsZXQgY2g6IENoYXIgOj0gOTB1MzIgYXMgQ2hhcjtcbiAgICBhc3NlcnQoY2ggPT0gJ1onKTtcblxuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2J1aWx0aW5zLzgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIiwibmFtZSI6IjgyX2VtYmVkZGVkX2NvcmVfaW1wbHMubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## String Methods
> Utilities since v0.9.0. All index-based operations count **Unicode scalar
> values** (matching `.len()`), and are total — out-of-range indices clamp or
> return `None` rather than panicking.

| Method                    | Signature                         | Description                                       |
|---------------------------|-----------------------------------|---------------------------------------------------|
| `.len()`                  | `() -> i64`                       | Number of characters (Unicode scalars)            |
| `.is_empty()`             | `() -> boolean`                   | Whether the string has no characters              |
| `.to_string()`            | `() -> String`                    | Returns the string itself                         |
| `.to_upper()`             | `() -> String`                    | Uppercased copy                                   |
| `.to_lower()`             | `() -> String`                    | Lowercased copy                                   |
| `.trim()`                 | `() -> String`                    | Whitespace removed from both ends                 |
| `.trim_start()`           | `() -> String`                    | Leading whitespace removed                        |
| `.trim_end()`             | `() -> String`                    | Trailing whitespace removed                       |
| `.contains(needle)`       | `(String) -> boolean`             | Whether `needle` occurs in the string             |
| `.starts_with(prefix)`    | `(String) -> boolean`             | Whether the string begins with `prefix`           |
| `.ends_with(suffix)`      | `(String) -> boolean`             | Whether the string ends with `suffix`             |
| `.index_of(needle)`       | `(String) -> Perhaps<i64>`        | Scalar index of the first occurrence, or `None`   |
| `.split(sep)`             | `(String) -> String[]`            | Split on each `sep` (empty `sep` ⇒ whole string)  |
| `.replace(from, to)`      | `(String, String) -> String`      | Replace every `from` with `to`                    |
| `.repeat(n)`              | `(i64) -> String`                 | The string repeated `n` times (`n <= 0` ⇒ `""`)   |
| `.chars()`                | `() -> Char[]`                    | The characters as an array                        |
| `.char_at(i)`             | `(i64) -> Perhaps<Char>`          | Character at scalar index `i`, or `None`          |
| `.substring(start, end)`  | `(i64, i64) -> String`            | Scalar range `[start, end)`, indices clamped      |

| Associated function       | Signature                         | Description                                       |
|---------------------------|-----------------------------------|---------------------------------------------------|
| `String::join(parts, sep)`| `(String[], String) -> String`    | Concatenate `parts` with `sep` between each       |

Strings are concatenated with the `+` operator.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.string-methods.dynamics-1}

String utility methods operate on Unicode scalar values; index-based operations are total,
clamping a slice boundary and returning `None` for an absent character or search result
rather than panicking.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg1X3N0cmluZ19tZXRob2RzLm10bCIsInNvdXJjZSI6Ii8vIHN0ZDo6Y29yZSBTdHJpbmcgdXRpbGl0eSBtZXRob2RzIChNRVRFTC0xOTMpLiBOYXRpdmUtYmFja2VkIG1ldGhvZHMgb24gdGhlXG4vLyBTdHJpbmcgcHJpbWl0aXZlLCBhdXRvLWltcG9ydGVkIHZpYSBzdGQ6OmNvcmUuIEluZGV4aW5nIGlzIGJ5IFVuaWNvZGUgc2NhbGFyXG4vLyBhbmQgdG90YWwgKG91dC1vZi1yYW5nZSBjbGFtcHMgb3IgeWllbGRzIE5vbmUpLlxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBcdTI1MDBcdTI1MDAgQ2FzZSAmIHRyaW0gXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgYXNzZXJ0KFwiICBIZWxsbywgV29ybGQgIFwiLnRyaW0oKSA9PSBcIkhlbGxvLCBXb3JsZFwiKTtcbiAgICBhc3NlcnQoXCIgIHhcIi50cmltX3N0YXJ0KCkgPT0gXCJ4XCIpO1xuICAgIGFzc2VydChcInggIFwiLnRyaW1fZW5kKCkgPT0gXCJ4XCIpO1xuICAgIGFzc2VydChcImFiY1wiLnRvX3VwcGVyKCkgPT0gXCJBQkNcIik7XG4gICAgYXNzZXJ0KFwiQUJDXCIudG9fbG93ZXIoKSA9PSBcImFiY1wiKTtcbiAgICBhc3NlcnQoXCJcIi5pc19lbXB0eSgpKTtcbiAgICBhc3NlcnQoIVwieFwiLmlzX2VtcHR5KCkpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIFNlYXJjaCAmIHRlc3QgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgYXNzZXJ0KFwiaGVsbG8gd29ybGRcIi5jb250YWlucyhcIndvcmxkXCIpKTtcbiAgICBhc3NlcnQoIVwiaGVsbG9cIi5jb250YWlucyhcInpcIikpO1xuICAgIGFzc2VydChcImhlbGxvXCIuc3RhcnRzX3dpdGgoXCJoZVwiKSk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5lbmRzX3dpdGgoXCJsb1wiKSk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5pbmRleF9vZihcImxcIikudW53cmFwX29yKC0xKSA9PSAyKTtcbiAgICBhc3NlcnQoXCJoZWxsb1wiLmluZGV4X29mKFwielwiKS5pc19ub25lKCkpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIFNwbGl0LCBqb2luLCByZXBsYWNlIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCBwYXJ0cyA6PSBcImEsYixjXCIuc3BsaXQoXCIsXCIpO1xuICAgIGFzc2VydChwYXJ0cy5sZW4oKSA9PSAzKTtcbiAgICBhc3NlcnQocGFydHNbMF0gPT0gXCJhXCIpO1xuICAgIGFzc2VydChwYXJ0c1syXSA9PSBcImNcIik7XG4gICAgYXNzZXJ0KFwiYS1iLWNcIi5yZXBsYWNlKFwiLVwiLCBcIitcIikgPT0gXCJhK2IrY1wiKTtcbiAgICBhc3NlcnQoXCJhYlwiLnJlcGVhdCgzKSA9PSBcImFiYWJhYlwiKTtcbiAgICBhc3NlcnQoXCJhYlwiLnJlcGVhdCgwKSA9PSBcIlwiKTtcbiAgICBhc3NlcnQoU3RyaW5nOjpqb2luKFtcImFcIiwgXCJiXCIsXCJjXCJdLCBcIi1cIikgPT0gXCJhLWItY1wiKTtcbiAgICBhc3NlcnQoU3RyaW5nOjpqb2luKFtdIDogU3RyaW5nW10sIFwiLFwiKSA9PSBcIlwiKTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBDaGFycyAmIHNsaWNpbmcgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgLy8gJ1x1MDBlOScgaXMgb25lIFVuaWNvZGUgc2NhbGFyLCBzbyBjaGFycygpL2xlbigpIGNvdW50IGl0IG9uY2UuXG4gICAgbGV0IGNzIDo9IFwiaFx1MDBlOWxsb1wiLmNoYXJzKCk7XG4gICAgYXNzZXJ0KGNzLmxlbigpID09IDUpO1xuICAgIGFzc2VydChjc1swXSA9PSAnaCcpO1xuICAgIGFzc2VydChcImFiY1wiLmNoYXJfYXQoMSkudW53cmFwX29yKCd6JykgPT0gJ2InKTtcbiAgICBhc3NlcnQoXCJhYmNcIi5jaGFyX2F0KDkpLmlzX25vbmUoKSk7XG4gICAgYXNzZXJ0KFwiYWJjXCIuY2hhcl9hdCgwIC0gMSkuaXNfbm9uZSgpKTtcbiAgICBhc3NlcnQoXCJoZWxsb1wiLnN1YnN0cmluZygxLCA0KSA9PSBcImVsbFwiKTtcbiAgICBhc3NlcnQoXCJoZWxsb1wiLnN1YnN0cmluZygzLCAxMDApID09IFwibG9cIik7ICAgLy8gZW5kIGNsYW1wcyB0byBsZW5ndGhcbiAgICBhc3NlcnQoXCJoZWxsb1wiLnN1YnN0cmluZyg0LCAyKSA9PSBcIlwiKTsgICAgICAgLy8gcmV2ZXJzZWQgcmFuZ2UgLT4gZW1wdHlcblxuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2J1aWx0aW5zLzg1X3N0cmluZ19tZXRob2RzLm10bCIsIm5hbWUiOiI4NV9zdHJpbmdfbWV0aG9kcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>


## Array Methods

`T[]` and `[T; N]` both expose:

| Method    | Signature       | Description                        |
|-----------|-----------------|------------------------------------|
| `.len()`  | `() -> i64`     | Number of elements                 |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.array-methods.dynamics-1}

Calling `.len()` on either `T[]` or `[T; N]` returns its number of elements.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEVtcHR5IHNpemVkIGFycmF5IFtUOyAwXSBcdTIwMTQgbGVuKCkgcmV0dXJucyAwLlxuICAgIGxldCBlbXB0eTogW2k2NDsgMF0gOj0gWzA7IDBdO1xuICAgIGFzc2VydChlbXB0eS5sZW4oKSA9PSAwKTtcblxuICAgIC8vIFNpbmdsZS1lbGVtZW50IHNpemVkIGFycmF5LlxuICAgIGxldCBzaW5nbGU6IFtpNjQ7IDFdIDo9IFs0Ml07XG4gICAgYXNzZXJ0KHNpbmdsZVswXSA9PSA0Mik7XG5cbiAgICAvLyBSZXBlYXQgd2l0aCBhIG5vbi10cml2aWFsIGV4cHJlc3Npb24uXG4gICAgbGV0IGNvbXB1dGVkOiBbaTY0OyAzXSA6PSBbMiArIDM7IDNdO1xuICAgIGFzc2VydChjb21wdXRlZFswXSA9PSA1KTtcbiAgICBhc3NlcnQoY29tcHV0ZWRbMV0gPT0gNSk7XG4gICAgYXNzZXJ0KGNvbXB1dGVkWzJdID09IDUpO1xuXG4gICAgLy8gTXV0YXRpb24gb2YgYSBzaXplZCBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBhcnJbMV0gOj0gOTk7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDk5KTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29lcmNpb246IFtUOyBOXSBpdGVyYXRlcyB2aWEgZm9yLWluIChzYW1lIGFzIFRbXSkuXG4gICAgbGV0IHNpemVkOiBbaTY0OyA0XSA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIHZhciBkeW5fc3VtIDo9IDA7XG4gICAgZm9yICh4IGluIHNpemVkKSB7XG4gICAgICAgIGR5bl9zdW0gKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KGR5bl9zdW0gPT0gMTAwKTtcblxuICAgIC8vIFBhdHRlcm46IC4ucmVzdCBpcyBlbXB0eSB3aGVuIG9ubHkgb25lIGVsZW1lbnQgaW4gdGhlIHNpemVkIGFycmF5LlxuICAgIGxldCBhcnIxOiBbaTY0OyAxXSA6PSBbNDJdO1xuICAgIGxldCByZXN0X2VtcHR5IDo9IG1hdGNoIChhcnIxKSB7XG4gICAgICAgIFtoZWFkLCAuLnJlc3RdID0+IHtcbiAgICAgICAgICAgIHZhciBjbnQgOj0gMDtcbiAgICAgICAgICAgIGZvciAoXyBpbiByZXN0KSB7IGNudCArPSAxOyB9XG4gICAgICAgICAgICBoZWFkICsgY250XG4gICAgICAgIH0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9lbXB0eSA9PSA0Mik7XG5cbiAgICAvLyBQYXR0ZXJuOiAuLnJlc3QgY29sbGVjdHMgcmVtYWluaW5nIGVsZW1lbnRzLlxuICAgIGxldCBhcnIyOiBbaTY0OyA0XSA6PSBbMSwgMiwgMywgNF07XG4gICAgbGV0IHJlc3Rfc3VtIDo9IG1hdGNoIChhcnIyKSB7XG4gICAgICAgIFtfYSwgX2IsIC4ucmVzdF0gPT4gcmVzdFswXSArIHJlc3RbMV0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9zdW0gPT0gNyk7XG5cbiAgICAvLyBFeGFjdC1jb3VudCBwYXR0ZXJuOiBlbGVtZW50IGJpbmRpbmdzIGFyZSBjb3JyZWN0LlxuICAgIGxldCBjb29yZHM6IFtpNjQ7IDNdIDo9IFszLCA0LCAwXTtcbiAgICBsZXQgZGlzdF9zcSA6PSBtYXRjaCAoY29vcmRzKSB7XG4gICAgICAgIFt4LCB5LCBfel0gPT4geCAqIHggKyB5ICogeSxcbiAgICB9O1xuICAgIGFzc2VydChkaXN0X3NxID09IDI1KTtcblxuICAgIC8vIGZvci1pbiBvdmVyIGEgcmVwZWF0LWNvbnN0cnVjdGVkIHNpemVkIGFycmF5LlxuICAgIHZhciB0b3RhbCA6PSAwO1xuICAgIGZvciAodiBpbiBbNzsgNV0pIHtcbiAgICAgICAgdG90YWwgKz0gdjtcbiAgICB9XG4gICAgYXNzZXJ0KHRvdGFsID09IDM1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsIm5hbWUiOiIxM19zaXplZF9hcnJheV9leHRlbmRlZC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Char Methods

> **Availability:** Since v0.8.0.

| Method / Function         | Signature                        | Description                                  |
|---------------------------|----------------------------------|----------------------------------------------|
| [`u32::from(c)`](#spec.runtime.char-methods.dynamics-1)            | `(Char) -> u32`                  | Unicode scalar value as a `u32`              |
| [`Char::from(n)`](#spec.runtime.char-methods.dynamics-1)           | `(u32) -> Char`                  | Construct from a code point; runtime error if not a valid scalar value |
| `.to_string()`            | `() -> String`                   | Single-character string                      |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.char-methods.dynamics-1}

`u32::from(c)` returns `c`'s Unicode scalar value, and `Char::from(n)` returns the matching
character or raises a runtime error when `n` is not a valid Unicode scalar value. A character's
`to_string()` result is its one-character string.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgxX2NoYXIubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gTGl0ZXJhbHMgYW5kIGJhc2ljIGVxdWFsaXR5XG4gICAgbGV0IGE6IENoYXIgOj0gJ0EnO1xuICAgIGxldCB6OiBDaGFyIDo9ICd6JztcbiAgICBsZXQgemVybzogQ2hhciA6PSAnMCc7XG4gICAgYXNzZXJ0KGEgPT0gJ0EnKTtcbiAgICBhc3NlcnQoeiA9PSAneicpO1xuICAgIGFzc2VydCh6ZXJvID09ICcwJyk7XG4gICAgYXNzZXJ0KGEgIT0geik7XG5cbiAgICAvLyBFc2NhcGUgc2VxdWVuY2VzXG4gICAgbGV0IG5ld2xpbmU6IENoYXIgOj0gJ1xcbic7XG4gICAgbGV0IHRhYjogQ2hhciA6PSAnXFx0JztcbiAgICBsZXQgYmFja3NsYXNoOiBDaGFyIDo9ICdcXFxcJztcbiAgICBsZXQgc2luZ2xlX3F1b3RlOiBDaGFyIDo9ICdcXCcnO1xuICAgIGFzc2VydChuZXdsaW5lICE9IHRhYik7XG4gICAgYXNzZXJ0KGJhY2tzbGFzaCA9PSAnXFxcXCcpO1xuICAgIGFzc2VydChzaW5nbGVfcXVvdGUgPT0gJ1xcJycpO1xuXG4gICAgLy8gVW5pY29kZSBlc2NhcGVcbiAgICBsZXQgc21pbGV5OiBDaGFyIDo9ICdcXHV7MUY2MDB9JztcbiAgICBhc3NlcnQoc21pbGV5ID09ICdcXHV7MUY2MDB9Jyk7XG5cbiAgICAvLyB0b19zdHJpbmdcbiAgICBhc3NlcnQoYS50b19zdHJpbmcoKSA9PSBcIkFcIik7XG4gICAgYXNzZXJ0KHplcm8udG9fc3RyaW5nKCkgPT0gXCIwXCIpO1xuICAgIGFzc2VydChzaW5nbGVfcXVvdGUudG9fc3RyaW5nKCkgPT0gXCInXCIpO1xuXG4gICAgLy8gQ29tcGFyaXNvbiBvcGVyYXRvcnMgKFVuaWNvZGUgc2NhbGFyIG9yZGVyKVxuICAgIGFzc2VydCgnQScgPCAnQicpO1xuICAgIGFzc2VydCgneicgPiAnYScpO1xuICAgIGFzc2VydCgnMCcgPCAnOScpO1xuICAgIGFzc2VydCgnQScgPD0gJ0EnKTtcbiAgICBhc3NlcnQoJ0InID49ICdBJyk7XG5cbiAgICAvLyBDb252ZXJzaW9uIHRvIHUzMiAoVW5pY29kZSBjb2RlIHBvaW50KVxuICAgIGxldCBjb2RlOiB1MzIgOj0gYSBhcyB1MzI7XG4gICAgYXNzZXJ0KGNvZGUgPT0gNjV1MzIpO1xuXG4gICAgLy8gQ29udmVyc2lvbiBmcm9tIHUzMiBiYWNrIHRvIENoYXJcbiAgICBsZXQgYmFjazogQ2hhciA6PSA2NXUzMiBhcyBDaGFyO1xuICAgIGFzc2VydChiYWNrID09ICdBJyk7XG5cbiAgICAvLyBSb3VuZC10cmlwXG4gICAgbGV0IG9yaWc6IENoYXIgOj0gJ00nO1xuICAgIGxldCByb3VuZDogQ2hhciA6PSAob3JpZyBhcyB1MzIpIGFzIENoYXI7XG4gICAgYXNzZXJ0KHJvdW5kID09IG9yaWcpO1xuXG4gICAgLy8gUGF0dGVybiBtYXRjaGluZ1xuICAgIGxldCBncmVldGluZzogU3RyaW5nIDo9IG1hdGNoIChhKSB7XG4gICAgICAgICdBJyA9PiBcImFscGhhXCIsXG4gICAgICAgICdCJyA9PiBcImJldGFcIixcbiAgICAgICAgXyAgID0+IFwib3RoZXJcIixcbiAgICB9O1xuICAgIGFzc2VydChncmVldGluZyA9PSBcImFscGhhXCIpO1xuXG4gICAgbGV0IGNhdGVnb3J5OiBTdHJpbmcgOj0gbWF0Y2ggKHplcm8pIHtcbiAgICAgICAgJzAnID0+IFwiZGlnaXRcIixcbiAgICAgICAgJ2EnID0+IFwibG93ZXJcIixcbiAgICAgICAgJ0EnID0+IFwidXBwZXJcIixcbiAgICAgICAgXyAgID0+IFwib3RoZXJcIixcbiAgICB9O1xuICAgIGFzc2VydChjYXRlZ29yeSA9PSBcImRpZ2l0XCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvODFfY2hhci5tdGwiLCJuYW1lIjoiODFfY2hhci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Core Sum Types

> **Availability:** Core methods since v0.9.0. `.yolo()`, `.ok_or()`, `.map_err()`, and `.ok()` since v0.10.0.

`Perhaps<T>` and `Result<T, E>` are the core optional/fallible types, both in
`std::core` and available unqualified. Their combinator methods let them be used
in pipelines without explicit `match`:

`Perhaps<T>` — `Some { value: T }` or `None`:

| Method               | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `.is_some()`         | `() -> boolean`                    | Whether this is `Some`                       |
| `.is_none()`         | `() -> boolean`                    | Whether this is `None`                       |
| `.map(f)`            | `<U>((T) -> U) -> Perhaps<U>`      | Transform the value, passing `None` through  |
| `.and_then(f)`       | `<U>((T) -> Perhaps<U>) -> Perhaps<U>` | Chain a `Perhaps`-returning function     |
| `.unwrap_or(d)`      | `(T) -> T`                         | The value, or `d` when `None`                |
| `.unwrap_or_else(f)` | `(() -> T) -> T`                   | The value, or `f()` when `None`              |
| `.yolo()`            | `() -> T`                          | The value, or panics (`R0014`) when `None`   |
| `.ok_or(error)`      | `<E>(E) -> Result<T, E>`           | `Some` becomes `Ok`; `None` becomes `Err(error)` |

`Result<T, E>` — `Ok { value: T }` or `Err { error: E }`:

| Method               | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `.is_ok()`           | `() -> boolean`                    | Whether this is `Ok`                         |
| `.is_err()`          | `() -> boolean`                    | Whether this is `Err`                        |
| `.map(f)`            | `<U>((T) -> U) -> Result<U, E>`    | Transform the success value, passing `Err` through |
| `.and_then(f)`       | `<U>((T) -> Result<U, E>) -> Result<U, E>` | Chain a `Result`-returning function |
| `.unwrap_or(d)`      | `(T) -> T`                         | The success value, or `d` when `Err`         |
| `.unwrap_or_else(f)` | `(() -> T) -> T`                   | The success value, or `f()` when `Err`       |
| `.yolo()`            | `() -> T`                          | The success value, or panics (`R0014`) when `Err`, including the error's debug representation |
| `.map_err(f)`        | `<F>((E) -> F) -> Result<T, F>`    | Transform the error value, passing `Ok` through |
| `.ok()`              | `() -> Perhaps<T>`                 | `Ok` becomes `Some`; `Err` becomes `None`, discarding the error |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.core-sum-types.dynamics-1}

The listed `Perhaps<T>` and `Result<T, E>` combinators operate on their corresponding sum
variants: transforms preserve the non-selected variant, and predicates report which variant
is present.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgzX3BlcmhhcHNfcmVzdWx0X21ldGhvZHMubXRsIiwic291cmNlIjoiLy8gc3RkOjpjb3JlIFBlcmhhcHM8VD4gYW5kIFJlc3VsdDxULCBFPiBlcmdvbm9taWMgbWV0aG9kcyAoTUVURUwtMTU5KS5cbi8vIFB1cmUtTWV0ZWwgbWV0aG9kcyBkZWZpbmVkIG9uIHRoZSBjb3JlIHN1bSB0eXBlcywgYXV0by1pbXBvcnRlZCB2aWEgc3RkOjpjb3JlLlxuLy9cbi8vIG1hcC9hbmRfdGhlbi91bndyYXBfb3IvdW53cmFwX29yX2Vsc2UvbWFwX2Vyci9vayBhbGwgdGFrZSBgc2VsZmAgYnkgdmFsdWVcbi8vIChSRkMtMDA2N2EgU1MzYTogYSB2YWx1ZSBjYW4gbmV2ZXIgYmUgbW92ZWQgb3V0IG9mIGEgcmVmZXJlbmNlKSwgc28gZWFjaFxuLy8gY29uc3VtaW5nIGNhbGwgYmVsb3cgZ2V0cyBpdHMgb3duIGZyZXNoIFBlcmhhcHMvUmVzdWx0IHJhdGhlciB0aGFuIHJldXNpbmdcbi8vIG9uZSBiaW5kaW5nIGFjcm9zcyBzZXZlcmFsIGJ5LXZhbHVlIGNhbGxzLlxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBcdTI1MDBcdTI1MDAgUGVyaGFwcyBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgc29tZSA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSAyMSB9O1xuICAgIGxldCBub25lOiBQZXJoYXBzPGk2ND4gOj0gUGVyaGFwczo6Tm9uZTtcblxuICAgIGFzc2VydCgoJnNvbWUpLmlzX3NvbWUoKSk7XG4gICAgYXNzZXJ0KCEoJnNvbWUpLmlzX25vbmUoKSk7XG4gICAgYXNzZXJ0KCgmbm9uZSkuaXNfbm9uZSgpKTtcbiAgICBhc3NlcnQoISgmbm9uZSkuaXNfc29tZSgpKTtcblxuICAgIC8vIG1hcCB0cmFuc2Zvcm1zIFNvbWUsIHBhc3NlcyB0aHJvdWdoIE5vbmVcbiAgICBsZXQgc29tZV9tYXAxIDo9IFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDIxIH07XG4gICAgYXNzZXJ0KHNvbWVfbWFwMS5tYXAofHg6IGk2NHwgLT4gaTY0IHsgeCAqIDIgfSkudW53cmFwX29yKDApID09IDQyKTtcbiAgICBsZXQgbm9uZV9tYXA6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChub25lX21hcC5tYXAofHg6IGk2NHwgLT4gaTY0IHsgeCAqIDIgfSkudW53cmFwX29yKC0xKSA9PSAtMSk7XG4gICAgLy8gbWFwIG1heSBjaGFuZ2UgdGhlIGVsZW1lbnQgdHlwZVxuICAgIGxldCBzb21lX21hcDIgOj0gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMjEgfTtcbiAgICBhc3NlcnQoc29tZV9tYXAyLm1hcCh8eDogaTY0fCAtPiBTdHJpbmcgeyBcInZcIiB9KS51bndyYXBfb3IoXCJub25lXCIpID09IFwidlwiKTtcblxuICAgIC8vIGFuZF90aGVuIGNoYWlucyBhIFBlcmhhcHMtcmV0dXJuaW5nIGZ1bmN0aW9uXG4gICAgbGV0IHNvbWVfYW5kX3RoZW4xIDo9IFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDIxIH07XG4gICAgYXNzZXJ0KHNvbWVfYW5kX3RoZW4xLmFuZF90aGVuKHx4OiBpNjR8IC0+IFBlcmhhcHM8aTY0PiB7IFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IHggKyAxIH0gfSkudW53cmFwX29yKDApID09IDIyKTtcbiAgICBsZXQgc29tZV9hbmRfdGhlbjIgOj0gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMjEgfTtcbiAgICBhc3NlcnQoc29tZV9hbmRfdGhlbjIuYW5kX3RoZW4ofHg6IGk2NHwgLT4gUGVyaGFwczxpNjQ+IHsgUGVyaGFwczo6Tm9uZSB9KS5pc19ub25lKCkpO1xuXG4gICAgLy8gdW53cmFwX29yIC8gdW53cmFwX29yX2Vsc2VcbiAgICBsZXQgc29tZV91bndyYXAxIDo9IFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDIxIH07XG4gICAgYXNzZXJ0KHNvbWVfdW53cmFwMS51bndyYXBfb3IoMCkgPT0gMjEpO1xuICAgIGxldCBub25lX3Vud3JhcDE6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChub25lX3Vud3JhcDEudW53cmFwX29yKDcpID09IDcpO1xuICAgIGxldCBub25lX3Vud3JhcDI6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChub25lX3Vud3JhcDIudW53cmFwX29yX2Vsc2UofHwgLT4gaTY0IHsgOSB9KSA9PSA5KTtcbiAgICBsZXQgc29tZV91bndyYXAyIDo9IFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDIxIH07XG4gICAgYXNzZXJ0KHNvbWVfdW53cmFwMi51bndyYXBfb3JfZWxzZSh8fCAtPiBpNjQgeyA5IH0pID09IDIxKTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBSZXN1bHQgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDEwIH07XG4gICAgbGV0IGVycjogUmVzdWx0PGk2NCwgU3RyaW5nPiA6PSBSZXN1bHQ6OkVyciB7IGVycm9yID0gXCJib29tXCIgfTtcblxuICAgIGFzc2VydCgoJm9rKS5pc19vaygpKTtcbiAgICBhc3NlcnQoISgmb2spLmlzX2VycigpKTtcbiAgICBhc3NlcnQoKCZlcnIpLmlzX2VycigpKTtcbiAgICBhc3NlcnQoISgmZXJyKS5pc19vaygpKTtcblxuICAgIGxldCBva19tYXA6IFJlc3VsdDxpNjQsIFN0cmluZz4gOj0gUmVzdWx0OjpPayB7IHZhbHVlID0gMTAgfTtcbiAgICBhc3NlcnQob2tfbWFwLm1hcCh8eDogaTY0fCAtPiBpNjQgeyB4ICsgNSB9KS51bndyYXBfb3IoMCkgPT0gMTUpO1xuICAgIGxldCBlcnJfbWFwMTogUmVzdWx0PGk2NCwgU3RyaW5nPiA6PSBSZXN1bHQ6OkVyciB7IGVycm9yID0gXCJib29tXCIgfTtcbiAgICBhc3NlcnQoZXJyX21hcDEubWFwKHx4OiBpNjR8IC0+IGk2NCB7IHggKyA1IH0pLnVud3JhcF9vcig5OSkgPT0gOTkpO1xuICAgIC8vIG1hcCBwcmVzZXJ2ZXMgdGhlIEVyciBwYXlsb2FkXG4gICAgbGV0IGVycl9tYXAyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBcImJvb21cIiB9O1xuICAgIGFzc2VydChlcnJfbWFwMi5tYXAofHg6IGk2NHwgLT4gaTY0IHsgeCArIDUgfSkuaXNfZXJyKCkpO1xuXG4gICAgbGV0IG9rX2FuZF90aGVuMTogUmVzdWx0PGk2NCwgU3RyaW5nPiA6PSBSZXN1bHQ6Ok9rIHsgdmFsdWUgPSAxMCB9O1xuICAgIGFzc2VydChva19hbmRfdGhlbjEuYW5kX3RoZW4ofHg6IGk2NHwgLT4gUmVzdWx0PGk2NCwgU3RyaW5nPiB7IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IHggKiAzIH0gfSkudW53cmFwX29yKDApID09IDMwKTtcbiAgICBsZXQgb2tfYW5kX3RoZW4yOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDEwIH07XG4gICAgYXNzZXJ0KG9rX2FuZF90aGVuMi5hbmRfdGhlbih8eDogaTY0fCAtPiBSZXN1bHQ8aTY0LCBTdHJpbmc+IHsgUmVzdWx0OjpFcnIgeyBlcnJvciA9IFwibm9cIiB9IH0pLmlzX2VycigpKTtcblxuICAgIGxldCBva191bndyYXA6IFJlc3VsdDxpNjQsIFN0cmluZz4gOj0gUmVzdWx0OjpPayB7IHZhbHVlID0gMTAgfTtcbiAgICBhc3NlcnQob2tfdW53cmFwLnVud3JhcF9vcigwKSA9PSAxMCk7XG4gICAgbGV0IGVycl91bndyYXAxOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBcImJvb21cIiB9O1xuICAgIGFzc2VydChlcnJfdW53cmFwMS51bndyYXBfb3IoMykgPT0gMyk7XG4gICAgbGV0IGVycl91bndyYXAyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBcImJvb21cIiB9O1xuICAgIGFzc2VydChlcnJfdW53cmFwMi51bndyYXBfb3JfZWxzZSh8fCAtPiBpNjQgeyA0IH0pID09IDQpO1xuXG4gICAgcHJpbnRsbihcIm9rXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvODNfcGVyaGFwc19yZXN1bHRfbWV0aG9kcy5tdGwiLCJuYW1lIjoiODNfcGVyaGFwc19yZXN1bHRfbWV0aG9kcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## List\<T\>

> **Availability:** Since v0.9.0.

`List<T>` is the growable collection type in `std::core`, available unqualified.

> **Since v0.12.0: `.set(i, value)`.** Added alongside RFC-0126 — `T[]` becoming an
> immutable borrowed view meant index-assignment through a slice stopped working, and
> `List<T>` had no way to overwrite an element in place at all, so an in-place algorithm
> (a bubble sort, for instance) had no expression until this existed.

| Method / function    | Signature                          | Description                                  |
|----------------------|------------------------------------|----------------------------------------------|
| `List::new()`        | `() -> List<T>`                    | A new empty list                             |
| `List::from(arr)`    | `(T[]) -> List<T>`                 | A list with a copy of the array's elements   |
| `.push(x)`           | `(&var self, T)`                   | Append an element                            |
| `.pop()`             | `(&var self) -> Perhaps<T>`        | Remove and return the last element           |
| `.len()`             | `() -> i64`                        | Number of elements                           |
| `.get(i)`            | `(i64) -> Perhaps<T>`              | Element at index `i`, or `None`              |
| `.set(i, value)`     | `(&var self, i64, T) -> Perhaps<T>`| Overwrite the element at `i`; returns the replaced value, or `None` if `i` is out of bounds |
| `.as_slice()`        | `() -> T[]`                        | The backing array                            |
| `.map(f)`            | `<U>((T) -> U) -> List<U>`         | A new list of `f` applied to each element    |
| `.filter(pred)`      | `((T) -> boolean) -> List<T>`      | The elements satisfying `pred`               |
| `.fold(init, f)`     | `<A>(A, (A, T) -> A) -> A`         | Reduce to a single value, left to right      |
| `.find(pred)`        | `((T) -> boolean) -> Perhaps<T>`   | The first element satisfying `pred`          |
| `.concat(other)`     | `(&List<T>) -> List<T>`            | This list's elements followed by `other`'s   |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.list-t.dynamics-2}

`List<T>` collection and iteration methods are methods of `List<T>` in `std::core`, not
free functions in separate collection or iteration modules.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg0X2xpc3RfbWV0aG9kcy5tdGwiLCJzb3VyY2UiOiIvLyBzdGQ6OmNvcmUgTGlzdDxUPiBjb2xsZWN0aW9uICsgaXRlcmF0aW9uIGVyZ29ub21pY3MgKE1FVEVMLTE2MCkuXG4vLyBQdXJlLU1ldGVsIG1ldGhvZHMgb3ZlciB0aGUgYmFja2luZyBhcnJheSwgYXV0by1pbXBvcnRlZCB2aWEgc3RkOjpjb3JlLlxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gTGlzdDo6ZnJvbShbMSwgMiwgMywgNCwgNV0pO1xuXG4gICAgLy8gbWFwIChzYW1lIGFuZCBjaGFuZ2VkIGVsZW1lbnQgdHlwZSlcbiAgICBsZXQgZG91YmxlZCA6PSAoJnhzKS5tYXAofHg6IGk2NHwgLT4gaTY0IHsgeCAqIDIgfSk7XG4gICAgYXNzZXJ0KCgmZG91YmxlZCkubGVuKCkgPT0gNSk7XG4gICAgYXNzZXJ0KCgmZG91YmxlZCkuZ2V0KDApLnVud3JhcF9vcigwKSA9PSAyKTtcbiAgICBhc3NlcnQoKCZkb3VibGVkKS5nZXQoNCkudW53cmFwX29yKDApID09IDEwKTtcbiAgICBsZXQgbGFiZWxzIDo9ICgmeHMpLm1hcCh8eDogaTY0fCAtPiBTdHJpbmcgeyBcIm5cIiB9KTtcbiAgICBhc3NlcnQoKCZsYWJlbHMpLmxlbigpID09IDUpO1xuICAgIGFzc2VydCgoJmxhYmVscykuZ2V0KDApLnVud3JhcF9vcihcIlwiKSA9PSBcIm5cIik7XG5cbiAgICAvLyBmaWx0ZXJcbiAgICBsZXQgZXZlbnMgOj0gKCZ4cykuZmlsdGVyKHx4OiBpNjR8IC0+IGJvb2xlYW4geyB4ICUgMiA9PSAwIH0pO1xuICAgIGFzc2VydCgoJmV2ZW5zKS5sZW4oKSA9PSAyKTtcbiAgICBhc3NlcnQoKCZldmVucykuZ2V0KDApLnVud3JhcF9vcigwKSA9PSAyKTtcbiAgICBhc3NlcnQoKCZldmVucykuZ2V0KDEpLnVud3JhcF9vcigwKSA9PSA0KTtcbiAgICBsZXQgbm9uZV9wYXNzIDo9ICgmeHMpLmZpbHRlcih8eDogaTY0fCAtPiBib29sZWFuIHsgeCA+IDk5IH0pO1xuICAgIGFzc2VydCgoJm5vbmVfcGFzcykubGVuKCkgPT0gMCk7XG5cbiAgICAvLyBmb2xkIChzdW0gYW5kIGEgdHlwZS1jaGFuZ2luZyBmb2xkIHRvIFN0cmluZyBsZW5ndGggY291bnQpXG4gICAgbGV0IHN1bSA6PSAoJnhzKS5mb2xkKDBpNjQsIHxhY2M6IGk2NCwgeDogaTY0fCAtPiBpNjQgeyBhY2MgKyB4IH0pO1xuICAgIGFzc2VydChzdW0gPT0gMTUpO1xuICAgIGxldCBjb3VudCA6PSAoJnhzKS5mb2xkKDBpNjQsIHxhY2M6IGk2NCwgeDogaTY0fCAtPiBpNjQgeyBhY2MgKyAxIH0pO1xuICAgIGFzc2VydChjb3VudCA9PSA1KTtcblxuICAgIC8vIGZpbmRcbiAgICBhc3NlcnQoKCZ4cykuZmluZCh8eDogaTY0fCAtPiBib29sZWFuIHsgeCA+IDMgfSkudW53cmFwX29yKDApID09IDQpO1xuICAgIGFzc2VydCgoJnhzKS5maW5kKHx4OiBpNjR8IC0+IGJvb2xlYW4geyB4ID4gOTkgfSkuaXNfbm9uZSgpKTtcblxuICAgIC8vIGNvbmNhdFxuICAgIGxldCBleHRyYSA6PSBMaXN0Ojpmcm9tKFs2LCA3XSk7XG4gICAgbGV0IGpvaW5lZCA6PSAoJnhzKS5jb25jYXQoJmV4dHJhKTtcbiAgICBhc3NlcnQoKCZqb2luZWQpLmxlbigpID09IDcpO1xuICAgIGFzc2VydCgoJmpvaW5lZCkuZ2V0KDUpLnVud3JhcF9vcigwKSA9PSA2KTtcbiAgICBhc3NlcnQoKCZqb2luZWQpLmdldCg2KS51bndyYXBfb3IoMCkgPT0gNyk7XG5cbiAgICAvLyBjaGFpbmluZyB0cmFuc2Zvcm1zXG4gICAgbGV0IHJlc3VsdCA6PSB4c1xuICAgICAgICAuZmlsdGVyKHx4OiBpNjR8IC0+IGJvb2xlYW4geyB4ICUgMiA9PSAxIH0pXG4gICAgICAgIC5tYXAofHg6IGk2NHwgLT4gaTY0IHsgeCAqIDEwIH0pXG4gICAgICAgIC5mb2xkKDBpNjQsIHxhOiBpNjQsIHg6IGk2NHwgLT4gaTY0IHsgYSArIHggfSk7XG4gICAgYXNzZXJ0KHJlc3VsdCA9PSA5MCk7XG5cbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9idWlsdGlucy84NF9saXN0X21ldGhvZHMubXRsIiwibmFtZSI6Ijg0X2xpc3RfbWV0aG9kcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.runtime.list-t.dynamics-1}

`List::from(source)` copies the elements of `source`, so mutating the resulting list
does not mutate that source.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg2X2xpc3RfZnJvbV9jb3BpZXNfc291cmNlLm10bCIsInNvdXJjZSI6Ii8vIExpc3Q6OmZyb20gb3ducyBhIGNvcHksIHJhdGhlciB0aGFuIGFuIGFsaWFzLCBvZiBpdHMgc291cmNlIGFycmF5LlxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgc291cmNlOiBpNjRbXSA6PSBbMSwgMl07XG4gICAgdmFyIGxpc3QgOj0gTGlzdDo6ZnJvbShzb3VyY2UpO1xuICAgIGxpc3QucHVzaCgzKTtcblxuICAgIGFzc2VydChzb3VyY2UubGVuKCkgPT0gMik7XG4gICAgYXNzZXJ0KHNvdXJjZVswXSA9PSAxKTtcbiAgICBhc3NlcnQoc291cmNlWzFdID09IDIpO1xuICAgIGFzc2VydChsaXN0LmxlbigpID09IDMpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvODZfbGlzdF9mcm9tX2NvcGllc19zb3VyY2UubXRsIiwibmFtZSI6Ijg2X2xpc3RfZnJvbV9jb3BpZXNfc291cmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## OsError

> **Availability:** Since v0.9.0.

`OsError` is the error type returned by the host-backed standard-library modules
(`std::fs`, `std::process`). It is in `std::core` (available unqualified) and
implements `Display`.

| Method        | Signature       | Description                          |
|---------------|-----------------|--------------------------------------|
| `.message()`  | `() -> String`  | The human-readable error description |

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.runtime.oserror.legality-1}

Host-backed fallible APIs use `OsError`, rather than `String`, as their error type; `OsError`
is available from `std::core` and implements `Display`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gc3RkOjpmcyBob3N0IG1vZHVsZSAoTUVURUwtMTY1KTogdGV4dCBmaWxlIG9wcyByZXR1cm5pbmcgUmVzdWx0PF8sIE9zRXJyb3I+LlxuLy8gVXNlcyBhIHVuaXF1ZSB0ZW1wIGRpcmVjdG9yeSBhbmQgY2xlYW5zIHVwIGFmdGVyIGl0c2VsZi5cbmltcG9ydCBzdGQ6OmZzOjp7XG4gICAgcmVhZF90b19zdHJpbmcsIHdyaXRlX3N0cmluZywgYXBwZW5kX3N0cmluZywgZXhpc3RzLCByZWFkX2RpcixcbiAgICBjcmVhdGVfZGlyX2FsbCwgcmVtb3ZlX2ZpbGUsIHJlbW92ZV9kaXJfYWxsLFxufTtcblxuZnVuIG1haW4oKSB7XG4gICAgLy8gY3JlYXRlX2Rpcl9hbGwgKyBleGlzdHNcbiAgICBhc3NlcnQoY3JlYXRlX2Rpcl9hbGwoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKS5pc19vaygpKTtcbiAgICBhc3NlcnQoZXhpc3RzKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTJcIikpO1xuXG4gICAgLy8gd3JpdGUgdGhlbiBhcHBlbmQsIHJlYWQgYmFjayB0aGUgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydCh3cml0ZV9zdHJpbmcoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMi9ub3RlLnR4dFwiLCBcImhlbGxvXCIpLmlzX29rKCkpO1xuICAgIGFzc2VydChhcHBlbmRfc3RyaW5nKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbm90ZS50eHRcIiwgXCIgd29ybGRcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KGV4aXN0cyhcIi90bXAvbWV0ZWxfZnNfZml4dHVyZV94N3EyL25vdGUudHh0XCIpKTtcbiAgICBhc3NlcnQocmVhZF90b19zdHJpbmcoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMi9ub3RlLnR4dFwiKS51bndyYXBfb3IoXCJcIikgPT0gXCJoZWxsbyB3b3JsZFwiKTtcblxuICAgIC8vIHJlYWRfZGlyIHJldHVybnMgdGhlIHNpbmdsZSBlbnRyeSBuYW1lXG4gICAgbGV0IGVudHJpZXMgOj0gcmVhZF9kaXIoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKS51bndyYXBfb3IoW10pO1xuICAgIGFzc2VydChlbnRyaWVzLmxlbigpID09IDEpO1xuICAgIGFzc2VydChlbnRyaWVzWzBdID09IFwibm90ZS50eHRcIik7XG5cbiAgICAvLyBlcnJvciBwYXRoOiBhIG1pc3NpbmcgZmlsZSB5aWVsZHMgRXJyIHdpdGggYSBub24tZW1wdHkgT3NFcnJvciBtZXNzYWdlXG4gICAgbWF0Y2ggKHJlYWRfdG9fc3RyaW5nKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbWlzc2luZy50eHRcIikpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChlcnJvci5tZXNzYWdlKCkubGVuKCkgPiAwKSxcbiAgICB9XG5cbiAgICAvLyBjbGVhbnVwXG4gICAgYXNzZXJ0KHJlbW92ZV9maWxlKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbm90ZS50eHRcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KHJlbW92ZV9kaXJfYWxsKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTJcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KCFleGlzdHMoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKSk7XG5cbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3Mvc3RkX2ZzX2hvc3RfbW9kdWxlIiwibmFtZSI6InN0ZF9mc19ob3N0X21vZHVsZSJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## Standard Library Modules

These modules are **not** auto-imported — a program must import them explicitly
(e.g. `import std::fs::{read_to_string, write_string};`). Their operations are
host-backed.

### std::env

Read-only process environment inspection.

| Function     | Signature                       | Description                                   |
|--------------|---------------------------------|-----------------------------------------------|
| `get(name)`  | `(String) -> Perhaps<String>`   | The value of an environment variable, or `None` |
| `vars()`     | `() -> EnvVar[]`                | All environment variables (`EnvVar { name, value }`) |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-env.dynamics-1}

`std::env` exposes read-only process-environment inspection through `get` and `vars`; it is
an explicitly imported host-backed module, not part of the automatic prelude.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gc3RkOjplbnYgaG9zdCBtb2R1bGUgKE1FVEVMLTE2NCk6IGV4cGxpY2l0IGltcG9ydCwgcmVhZC1vbmx5IGVudmlyb25tZW50XG4vLyBpbnNwZWN0aW9uLiBEZXRlcm1pbmlzdGljIFx1MjAxNCBkb2VzIG5vdCBhc3N1bWUgYW55IHBhcnRpY3VsYXIgdmFyaWFibGUgaXMgc2V0LlxuaW1wb3J0IHN0ZDo6ZW52Ojp7Z2V0LCB2YXJzLCBFbnZWYXJ9O1xuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBBIG5hbWUgdGhhdCBzaG91bGQgbm90IGV4aXN0IGluIGFueSB0ZXN0IGVudmlyb25tZW50IHJlc29sdmVzIHRvIE5vbmUuXG4gICAgYXNzZXJ0KGdldChcIk1FVEVMX0RFRklOSVRFTFlfVU5TRVRfOXo4eTd4XCIpLmlzX25vbmUoKSk7XG5cbiAgICAvLyB2YXJzKCkgeWllbGRzIGFuIEVudlZhcltdOyBMaXN0IGVyZ29ub21pY3MgYXBwbHkgYWZ0ZXIgTGlzdDo6ZnJvbSwgYW5kXG4gICAgLy8gbWFwcGluZyBwcmVzZXJ2ZXMgdGhlIGVsZW1lbnQgY291bnQuXG4gICAgbGV0IGFsbCA6PSB2YXJzKCk7XG4gICAgbGV0IG5hbWVzIDo9IExpc3Q6OmZyb20oYWxsKS5tYXAofGU6IEVudlZhcnwgLT4gU3RyaW5nIHsgZS5uYW1lIH0pO1xuICAgIGFzc2VydChuYW1lcy5sZW4oKSA9PSBhbGwubGVuKCkpO1xuXG4gICAgcHJpbnRsbihcIm9rXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3N0ZF9lbnZfaG9zdF9tb2R1bGUiLCJuYW1lIjoic3RkX2Vudl9ob3N0X21vZHVsZSJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

### std::fs

Text-oriented file operations. Fallible operations return `Result<_, OsError>`.

| Function                    | Signature                                       | Description                          |
|-----------------------------|-------------------------------------------------|--------------------------------------|
| `read_to_string(path)`      | `(String) -> Result<String, OsError>`           | Read an entire file into a string    |
| `write_string(path, s)`     | `(String, String) -> Result<(), OsError>`       | Write `s`, replacing any existing file |
| `append_string(path, s)`    | `(String, String) -> Result<(), OsError>`       | Append `s`, creating the file if absent |
| `exists(path)`              | `(String) -> boolean`                           | Whether a file or directory exists   |
| `read_dir(path)`            | `(String) -> Result<String[], OsError>`         | The entry names within a directory   |
| `create_dir(path)`          | `(String) -> Result<(), OsError>`               | Create a single directory            |
| `create_dir_all(path)`      | `(String) -> Result<(), OsError>`               | Create a directory and all parents   |
| `remove_file(path)`         | `(String) -> Result<(), OsError>`               | Remove a file                        |
| `remove_dir(path)`          | `(String) -> Result<(), OsError>`               | Remove an empty directory            |
| `remove_dir_all(path)`      | `(String) -> Result<(), OsError>`               | Remove a directory and its contents  |

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-fs.dynamics-1}

`std::fs` is an explicitly imported host-backed module whose text-oriented file operations
have the signatures listed above and report fallible outcomes as `Result<_, OsError>`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gc3RkOjpmcyBob3N0IG1vZHVsZSAoTUVURUwtMTY1KTogdGV4dCBmaWxlIG9wcyByZXR1cm5pbmcgUmVzdWx0PF8sIE9zRXJyb3I+LlxuLy8gVXNlcyBhIHVuaXF1ZSB0ZW1wIGRpcmVjdG9yeSBhbmQgY2xlYW5zIHVwIGFmdGVyIGl0c2VsZi5cbmltcG9ydCBzdGQ6OmZzOjp7XG4gICAgcmVhZF90b19zdHJpbmcsIHdyaXRlX3N0cmluZywgYXBwZW5kX3N0cmluZywgZXhpc3RzLCByZWFkX2RpcixcbiAgICBjcmVhdGVfZGlyX2FsbCwgcmVtb3ZlX2ZpbGUsIHJlbW92ZV9kaXJfYWxsLFxufTtcblxuZnVuIG1haW4oKSB7XG4gICAgLy8gY3JlYXRlX2Rpcl9hbGwgKyBleGlzdHNcbiAgICBhc3NlcnQoY3JlYXRlX2Rpcl9hbGwoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKS5pc19vaygpKTtcbiAgICBhc3NlcnQoZXhpc3RzKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTJcIikpO1xuXG4gICAgLy8gd3JpdGUgdGhlbiBhcHBlbmQsIHJlYWQgYmFjayB0aGUgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydCh3cml0ZV9zdHJpbmcoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMi9ub3RlLnR4dFwiLCBcImhlbGxvXCIpLmlzX29rKCkpO1xuICAgIGFzc2VydChhcHBlbmRfc3RyaW5nKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbm90ZS50eHRcIiwgXCIgd29ybGRcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KGV4aXN0cyhcIi90bXAvbWV0ZWxfZnNfZml4dHVyZV94N3EyL25vdGUudHh0XCIpKTtcbiAgICBhc3NlcnQocmVhZF90b19zdHJpbmcoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMi9ub3RlLnR4dFwiKS51bndyYXBfb3IoXCJcIikgPT0gXCJoZWxsbyB3b3JsZFwiKTtcblxuICAgIC8vIHJlYWRfZGlyIHJldHVybnMgdGhlIHNpbmdsZSBlbnRyeSBuYW1lXG4gICAgbGV0IGVudHJpZXMgOj0gcmVhZF9kaXIoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKS51bndyYXBfb3IoW10pO1xuICAgIGFzc2VydChlbnRyaWVzLmxlbigpID09IDEpO1xuICAgIGFzc2VydChlbnRyaWVzWzBdID09IFwibm90ZS50eHRcIik7XG5cbiAgICAvLyBlcnJvciBwYXRoOiBhIG1pc3NpbmcgZmlsZSB5aWVsZHMgRXJyIHdpdGggYSBub24tZW1wdHkgT3NFcnJvciBtZXNzYWdlXG4gICAgbWF0Y2ggKHJlYWRfdG9fc3RyaW5nKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbWlzc2luZy50eHRcIikpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChlcnJvci5tZXNzYWdlKCkubGVuKCkgPiAwKSxcbiAgICB9XG5cbiAgICAvLyBjbGVhbnVwXG4gICAgYXNzZXJ0KHJlbW92ZV9maWxlKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTIvbm90ZS50eHRcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KHJlbW92ZV9kaXJfYWxsKFwiL3RtcC9tZXRlbF9mc19maXh0dXJlX3g3cTJcIikuaXNfb2soKSk7XG4gICAgYXNzZXJ0KCFleGlzdHMoXCIvdG1wL21ldGVsX2ZzX2ZpeHR1cmVfeDdxMlwiKSk7XG5cbiAgICBwcmludGxuKFwib2tcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3Mvc3RkX2ZzX2hvc3RfbW9kdWxlIiwibmFtZSI6InN0ZF9mc19ob3N0X21vZHVsZSJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

### std::process

Command-line arguments and shell-free synchronous subprocess execution.

| Function              | Signature                                                  | Description                                |
|-----------------------|-----------------------------------------------------------|--------------------------------------------|
| `args()`              | `() -> String[]`                                          | The process command-line arguments         |
| `run(command, args)`  | `(String, String[]) -> Result<ProcessOutput, OsError>`    | Run `command` with `args`, capturing output |

`run` executes the command directly — there is no shell, so quoting and shell
expansion never apply. A non-zero exit status is a successful `Ok` result, not
an error; only a failure to launch the command is an `Err`. The result type is
`ProcessOutput { status: i64, stdout: String, stderr: String }`.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.runtime.standard-library-modules.std-process.dynamics-1}

`std::process::run` launches `command` directly with `args`, without shell parsing. A launched
program returns `Ok(ProcessOutput)` even for a non-zero exit status; only failure to launch
returns `Err(OsError)`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gc3RkOjpwcm9jZXNzIGhvc3QgbW9kdWxlIChNRVRFTC0xNjYpOiBhcmd2IGFuZCBzaGVsbC1mcmVlIHN1YnByb2Nlc3MgcnVuLlxuLy8gVXNlcyBQT1NJWCBgdHJ1ZWAvYGZhbHNlYCBmb3IgZGV0ZXJtaW5pc3RpYyBleGl0IHN0YXR1c2VzLlxuaW1wb3J0IHN0ZDo6cHJvY2Vzczo6e2FyZ3MsIHJ1biwgUHJvY2Vzc091dHB1dH07XG5cbmZ1biBzdGF0dXNfb2YocjogUmVzdWx0PFByb2Nlc3NPdXRwdXQsIE9zRXJyb3I+KSAtPiBpNjQge1xuICAgIG1hdGNoIChyKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSB9ID0+IHZhbHVlLnN0YXR1cyxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IC05OTksXG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBhcmd2IGlzIGFsd2F5cyBub24tZW1wdHkgKGF0IGxlYXN0IHRoZSBpbnRlcnByZXRlciBwYXRoKS5cbiAgICBhc3NlcnQoYXJncygpLmxlbigpID4gMCk7XG5cbiAgICAvLyBBIHN1Y2Nlc3NmdWwgY29tbWFuZCBleGl0cyAwOyBhIGZhaWxpbmcgb25lIGV4aXRzIG5vbi16ZXJvIFx1MjAxNCBib3RoIGFyZSBPa1xuICAgIC8vIChhIG5vbi16ZXJvIHN0YXR1cyBpcyBhIHJlc3VsdCwgbm90IGFuIGVycm9yKS5cbiAgICBhc3NlcnQoc3RhdHVzX29mKHJ1bihcInRydWVcIiwgW10pKSA9PSAwKTtcbiAgICBhc3NlcnQoc3RhdHVzX29mKHJ1bihcImZhbHNlXCIsIFtdKSkgIT0gMCk7XG5cbiAgICAvLyBBIGNvbW1hbmQgdGhhdCBjYW5ub3QgYmUgbGF1bmNoZWQgaXMgYW4gRXJyIGNhcnJ5aW5nIGFuIE9zRXJyb3IgbWVzc2FnZS5cbiAgICBtYXRjaCAocnVuKFwibWV0ZWxfbm9fc3VjaF9jb21tYW5kX3o5XCIsIFtdKSkge1xuICAgICAgICBSZXN1bHQ6Ok9rIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGVycm9yLm1lc3NhZ2UoKS5sZW4oKSA+IDApLFxuICAgIH1cblxuICAgIHByaW50bG4oXCJva1wiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9zdGRfcHJvY2Vzc19ob3N0X21vZHVsZS9tYWluLm10bCIsIm5hbWUiOiJtYWluLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>
