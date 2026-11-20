---
sidebar_position: 7
---

# If / Else

```metel
fun main() -> i64 {
    let condition := false;
    let other := true;
    if (condition) {
        return 1;
    } else if (other) {
        return 2;
    } else {
        return 3;
    }
}
```

`if` is also an expression ([both branches must produce the same type](#spec.expressions.control-flow.if-else.legality-3)):

```metel
fun main() -> i64 {
    let x := 1;
    let label := if (x > 0) { "positive" } else { "non-positive" };
    return label.len();
}
```

**Braceless bodies.** A single expression may be used as the branch body without braces:

```metel
fun print_state() { }

fun main() -> i64 {
    let debug := true;
    let flag := false;
    let value_a := 10;
    let value_b := 20;
    if (debug) print_state();
    let x := if (flag) value_a else value_b;
    return x;
}
```

The braceless form desugars to a single-expression block. Three restrictions apply:

1. **Arm style must be consistent.** [Both the `then` and `else` arms must use the same style](#spec.expressions.control-flow.if-else.legality-5) — either both braced or both braceless. Mixing is a parse error.
2. **Dangling-else is forbidden.** [If the outer body is braceless, the body expression must not itself be an `if–else`](#spec.expressions.control-flow.if-else.legality-4). Use braces on the outer body to resolve the ambiguity.
   ```metel
   fun main() -> i64 {
       let a := true;
       let b := false;
       if (a) if (b) { return 1; }
       if (a) { if (b) { return 2; } else { return 3; } }
       return 4;
   }
   ```
   <!-- doc-example: expect-fail reason="demonstrates the forbidden dangling-else case -- the parse error is the point" -->
   ```metel
   fun main() {
       let a := true;
       let b := false;
       if (a) if (b) { return; } else { return; }
   }
   ```
3. **No semicolon between braceless arms.** Write `if (c) a else b;`, not `if (c) a; else b;` — the `;` terminates the statement before the `else`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-1}

An `if` branch may be a single braceless expression.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQ3X2JyYWNlbGVzc19pZi5tdGwiLCJzb3VyY2UiOiIvLyBCcmFjZWxlc3MgaWYgYm9keSBzeW50YXggKFJGQy0wMDIyKS5cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQnJhY2VsZXNzIGlmIGluIHN0YXRlbWVudCBwb3NpdGlvbiAobm8gZWxzZSkuXG4gICAgdmFyIHggOj0gMDtcbiAgICBpZiAodHJ1ZSkgeyB4ID0gMTsgfTtcbiAgICBhc3NlcnQoeCA9PSAxKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBcdTIwMTQgY29uZGl0aW9uIGZhbHNlLCBib2R5IG5vdCBleGVjdXRlZC5cbiAgICBpZiAoZmFsc2UpIHsgeCA9IDk5OyB9O1xuICAgIGFzc2VydCh4ID09IDEpO1xuXG4gICAgLy8gQnJhY2VsZXNzIGlmXHUyMDEzZWxzZSBpbiBleHByZXNzaW9uIHBvc2l0aW9uLlxuICAgIGxldCBhIDo9IGlmICh0cnVlKSAxMCBlbHNlIDIwO1xuICAgIGFzc2VydChhID09IDEwKTtcblxuICAgIGxldCBiIDo9IGlmIChmYWxzZSkgMTAgZWxzZSAyMDtcbiAgICBhc3NlcnQoYiA9PSAyMCk7XG5cbiAgICAvLyBOZXN0ZWQgYnJhY2VsZXNzOiBpbm5lciBpZiBoYXMgbm8gZWxzZSBcdTIwMTQgb2suXG4gICAgdmFyIGZsYWcgOj0gZmFsc2U7XG4gICAgaWYgKHRydWUpIGlmICh0cnVlKSB7IGZsYWcgPSB0cnVlOyB9O1xuICAgIGFzc2VydChmbGFnKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgdXNlZCBhcyBhIGZ1bmN0aW9uIGFyZ3VtZW50LlxuICAgIGFzc2VydCgoaWYgKHRydWUpIDcgZWxzZSA4KSA9PSA3KTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBpbiBhIGxvb3AuXG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgd2hpbGUgKGkgPCA1KSB7XG4gICAgICAgIGlmIChpICUgMiA9PSAwKSB7IHN1bSA9IHN1bSArIGk7IH07XG4gICAgICAgIGkgPSBpICsgMTtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSA2KTsgIC8vIDAgKyAyICsgNFxuXG4gICAgLy8gQnJhY2VsZXNzIGVsc2UtaWYgY2hhaW4uXG4gICAgbGV0IHYgOj0gMjtcbiAgICBsZXQgbGFiZWwgOj0gaWYgKHYgPT0gMSkgMTAwIGVsc2UgaWYgKHYgPT0gMikgMjAwIGVsc2UgMzAwO1xuICAgIGFzc2VydChsYWJlbCA9PSAyMDApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93LzQ3X2JyYWNlbGVzc19pZi5tdGwiLCJuYW1lIjoiNDdfYnJhY2VsZXNzX2lmLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-2}

A braceless `if` without `else` has type `Unit` and may occur wherever a `Unit`-typed
expression is accepted.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg4X2JyYWNlbGVzc19pZl9ub19lbHNlX2luX2V4cHJlc3Npb25fcG9zaXRpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwMjIgXHUwMGE3MiAoY29ycmVjdGVkIG1ldGVsLWNvcmUjNzUwKTogYSBicmFjZWxlc3MgYGlmYCB3aXRoIG5vIGBlbHNlYCBoYXNcbi8vIHR5cGUgVW5pdCwgYW5kIGlzIG5vdCByZXN0cmljdGVkIHRvIHN0YXRlbWVudCBwb3NpdGlvbiAtLSBpdCdzIHVzYWJsZVxuLy8gYW55d2hlcmUgYSBVbml0LXR5cGVkIGV4cHJlc3Npb24gaXMsIGluY2x1ZGluZyBhIGBsZXRgIGJpbmRpbmcnc1xuLy8gaW5pdGlhbGl6ZXIuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgY2FsbHMgOj0gMDtcbiAgICBsZXQgY2FsbHNfcmVmOiAmdmFyIGk2NCA6PSAmdmFyIGNhbGxzO1xuICAgIGxldCB2YWx1ZSA6PSBpZiAodHJ1ZSkgeyAqY2FsbHNfcmVmICs9IDE7IH07XG4gICAgYXNzZXJ0KGNhbGxzID09IDEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93Lzg4X2JyYWNlbGVzc19pZl9ub19lbHNlX2luX2V4cHJlc3Npb25fcG9zaXRpb24ubXRsIiwibmFtZSI6Ijg4X2JyYWNlbGVzc19pZl9ub19lbHNlX2luX2V4cHJlc3Npb25fcG9zaXRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-3}

A braceless `if`-`else` is an expression when its two branches have the same type.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQ3X2JyYWNlbGVzc19pZi5tdGwiLCJzb3VyY2UiOiIvLyBCcmFjZWxlc3MgaWYgYm9keSBzeW50YXggKFJGQy0wMDIyKS5cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQnJhY2VsZXNzIGlmIGluIHN0YXRlbWVudCBwb3NpdGlvbiAobm8gZWxzZSkuXG4gICAgdmFyIHggOj0gMDtcbiAgICBpZiAodHJ1ZSkgeyB4ID0gMTsgfTtcbiAgICBhc3NlcnQoeCA9PSAxKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBcdTIwMTQgY29uZGl0aW9uIGZhbHNlLCBib2R5IG5vdCBleGVjdXRlZC5cbiAgICBpZiAoZmFsc2UpIHsgeCA9IDk5OyB9O1xuICAgIGFzc2VydCh4ID09IDEpO1xuXG4gICAgLy8gQnJhY2VsZXNzIGlmXHUyMDEzZWxzZSBpbiBleHByZXNzaW9uIHBvc2l0aW9uLlxuICAgIGxldCBhIDo9IGlmICh0cnVlKSAxMCBlbHNlIDIwO1xuICAgIGFzc2VydChhID09IDEwKTtcblxuICAgIGxldCBiIDo9IGlmIChmYWxzZSkgMTAgZWxzZSAyMDtcbiAgICBhc3NlcnQoYiA9PSAyMCk7XG5cbiAgICAvLyBOZXN0ZWQgYnJhY2VsZXNzOiBpbm5lciBpZiBoYXMgbm8gZWxzZSBcdTIwMTQgb2suXG4gICAgdmFyIGZsYWcgOj0gZmFsc2U7XG4gICAgaWYgKHRydWUpIGlmICh0cnVlKSB7IGZsYWcgPSB0cnVlOyB9O1xuICAgIGFzc2VydChmbGFnKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgdXNlZCBhcyBhIGZ1bmN0aW9uIGFyZ3VtZW50LlxuICAgIGFzc2VydCgoaWYgKHRydWUpIDcgZWxzZSA4KSA9PSA3KTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBpbiBhIGxvb3AuXG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgd2hpbGUgKGkgPCA1KSB7XG4gICAgICAgIGlmIChpICUgMiA9PSAwKSB7IHN1bSA9IHN1bSArIGk7IH07XG4gICAgICAgIGkgPSBpICsgMTtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSA2KTsgIC8vIDAgKyAyICsgNFxuXG4gICAgLy8gQnJhY2VsZXNzIGVsc2UtaWYgY2hhaW4uXG4gICAgbGV0IHYgOj0gMjtcbiAgICBsZXQgbGFiZWwgOj0gaWYgKHYgPT0gMSkgMTAwIGVsc2UgaWYgKHYgPT0gMikgMjAwIGVsc2UgMzAwO1xuICAgIGFzc2VydChsYWJlbCA9PSAyMDApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93LzQ3X2JyYWNlbGVzc19pZi5tdGwiLCJuYW1lIjoiNDdfYnJhY2VsZXNzX2lmLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-4}

A braceless outer branch cannot contain an inner `if`-`else`; braces are required to
avoid dangling-`else` ambiguity.

<!-- rfc.py:last_reviewed 90ce03190abb6a5e7304b51d513a85e2bbb3265e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImJyYWNlbGVzcyBpZiBib2R5IG1heSBub3QgY29udGFpbiBhbiBpZlx1MjAxM2Vsc2UgZXhwcmVzc2lvbiIsImxpbmUiOm51bGwsInN0YXR1cyI6InBhcnNlX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzE5X2JyYWNlbGVzc19pZl9kYW5nbGluZ19lbHNlLm10bCIsInNvdXJjZSI6Ii8vIFBBUlNFX0VSUk9SW2JyYWNlbGVzcyBpZiBib2R5IG1heSBub3QgY29udGFpbiBhbiBpZlx1MjAxM2Vsc2UgZXhwcmVzc2lvbl1cbi8vIE91dGVyIGJvZHkgaXMgYnJhY2VsZXNzIGFuZCBjb250YWlucyBhbiBpbm5lciBpZlx1MjAxM2Vsc2UgXHUyMDE0IGRhbmdsaW5nLWVsc2UgYW1iaWd1aXR5LlxuZnVuIG1haW4oKSB7XG4gICAgaWYgKHRydWUpIGlmIChmYWxzZSkgMSBlbHNlIDI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvbmVnXzE5X2JyYWNlbGVzc19pZl9kYW5nbGluZ19lbHNlLm10bCIsIm5hbWUiOiJuZWdfMTlfYnJhY2VsZXNzX2lmX2RhbmdsaW5nX2Vsc2UubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-5}

The `then` and `else` branches of an `if`-`else` must use the same body style: both
braced or both braceless.

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6Im1pc21hdGNoZWQgaWYgYXJtIHN0eWxlcyIsImxpbmUiOm51bGwsInN0YXR1cyI6InBhcnNlX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzIwX2JyYWNlbGVzc19pZl9taXhlZF9hcm1zLm10bCIsInNvdXJjZSI6Ii8vIFBBUlNFX0VSUk9SW21pc21hdGNoZWQgaWYgYXJtIHN0eWxlc11cbi8vIHRoZW4gYnJhbmNoIHVzZXMgYnJhY2VzLCBlbHNlIGJyYW5jaCBkb2VzIG5vdC5cbmZ1biBtYWluKCkge1xuICAgIGxldCB4IDo9IGlmICh0cnVlKSB7IDEgfSBlbHNlIDI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvbmVnXzIwX2JyYWNlbGVzc19pZl9taXhlZF9hcm1zLm10bCIsIm5hbWUiOiJuZWdfMjBfYnJhY2VsZXNzX2lmX21peGVkX2FybXMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>
