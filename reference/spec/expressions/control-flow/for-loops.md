---
sidebar_position: 8
---

# For Loops

## For

A C-style `for` initializer [may declare a loop-local `var` binding](#spec.expressions.control-flow.for.legality-1):

```metel
fun main() -> i64 {
    var total := 0;
    for (var i := 0; i < 4; i += 1) {
        total += i;
    }
    return total;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.for.legality-1}

A C-style `for` initializer may declare a mutable loop-local binding with `var`; that
binding may be reassigned by the loop body or step expression.

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE2X2Zvcl9sb29wLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEJhc2ljIGNvdW50aW5nLlxuICAgIHZhciBzdW0gOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCA1OyBpICs9IDEpIHsgc3VtICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtID09IDEwKTtcbiAgICAvLyBCcmVhayBleGl0cyB0aGUgbG9vcC5cbiAgICB2YXIgY291bnQgOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCAxMDA7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSA1KSB7IGJyZWFrOyB9XG4gICAgICAgIGNvdW50ICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjb3VudCA9PSA1KTtcbiAgICAvLyBDb250aW51ZSBzdGlsbCBleGVjdXRlcyB0aGUgc3RlcCBleHByZXNzaW9uLlxuICAgIHZhciBjMiA6PSAwO1xuICAgIGZvciAodmFyIGkgOj0gMDsgaSA8IDU7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSAyKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIGMyICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjMiA9PSA0KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2NvbnRyb2xfZmxvdy8xNl9mb3JfbG9vcC5tdGwiLCJuYW1lIjoiMTZfZm9yX2xvb3AubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## For-In

[`for-in` works on any type implementing the `Iterable<T>` aspect](../../runtime.md#spec.runtime.built-in-aspects.iterable-t.legality-1). The loop variable
receives type `T`. `[T]`, `[T; N]` (array and fixed-size array), and `Range` (produced by
`..` and `..=`) implement `Iterable<T>` by default. A `[T]` loop binding denotes an
element of an immutable borrowed view: with move checking enabled, a non-`Copy` binding
may be read or borrowed but not consumed. User-defined types can be made iterable by
implementing `Iterable<T>`. The loop binding is immutable by default and [may be made
loop-locally mutable with `var`](#spec.expressions.control-flow.for-in.legality-1):

```metel
aspect Iterable<T> {
    fun next(&var self) -> Option<T>;
}

fun main() -> i64 {
    return 0;
}
```

```metel
fun main() -> i64 {
    let collection := [1, 2, 3];
    var total := 0;
    for (let item in collection) { total += item; }
    for (var item in collection) {
        item += 1;
        total += item;
    }
    for (let i in 0..10) { total += i; }
    for (let i in 0..=10) { total += i; }
    return total;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.control-flow.for-in.legality-1}

A `for-in` binding may be declared with `var`, making that iteration's loop-local binding
mutable.

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE3X2Zvcl9pbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICAvLyBBcnJheSBpdGVyYXRpb24uXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMF07XG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIGZvciAoeCBpbiBhcnIpIHsgc3VtICs9IHg7IH1cbiAgICBhc3NlcnQoc3VtID09IDYwKTtcbiAgICAvLyBFeGNsdXNpdmUgcmFuZ2UuXG4gICAgdmFyIHN1bTIgOj0gMDtcbiAgICBmb3IgKGkgaW4gMC4uNSkgeyBzdW0yICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtMiA9PSAxMCk7XG4gICAgLy8gSW5jbHVzaXZlIHJhbmdlLlxuICAgIHZhciBzdW0zIDo9IDA7XG4gICAgZm9yIChpIGluIDEuLj00KSB7IHN1bTMgKz0gaTsgfVxuICAgIGFzc2VydChzdW0zID09IDEwKTtcbiAgICAvLyBNdXRhYmxlIGZvci1pbiBiaW5kaW5nIG1heSBiZSByZWJvdW5kIGxvY2FsbHkuXG4gICAgdmFyIGJ1bXBlZCA6PSAwO1xuICAgIGZvciAodmFyIHggaW4gWzEsIDIsIDNdKSB7XG4gICAgICAgIHggKz0gMTtcbiAgICAgICAgYnVtcGVkICs9IHg7XG4gICAgfVxuICAgIGFzc2VydChidW1wZWQgPT0gOSk7XG4gICAgLy8gQnJlYWsgc3RvcHMgZWFybHkuXG4gICAgdmFyIHN1bTQgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDMsIDQsIDVdKSB7XG4gICAgICAgIGlmICh4ID09IDMpIHsgYnJlYWs7IH1cbiAgICAgICAgc3VtNCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQoc3VtNCA9PSAzKTtcbiAgICAvLyBDb250aW51ZSBza2lwcyB0aGUgY3VycmVudCBlbGVtZW50LlxuICAgIHZhciBzdW01IDo9IDA7XG4gICAgZm9yICh4IGluIFsxLCAyLCAzLCA0LCA1XSkge1xuICAgICAgICBpZiAoeCA9PSAzKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIHN1bTUgKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bTUgPT0gMTIpO1xuICAgIC8vIEJpbmRpbmcgZG9lcyBub3QgbGVhayBpbnRvIHRoZSBvdXRlciBzY29wZS5cbiAgICBsZXQgeCA6PSA0MjtcbiAgICB2YXIgaW5uZXIgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDNdKSB7IGlubmVyICs9IHg7IH1cbiAgICBhc3NlcnQoaW5uZXIgPT0gNik7XG4gICAgYXNzZXJ0KHggICA9PSA0Mik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTdfZm9yX2luLm10bCIsIm5hbWUiOiIxN19mb3JfaW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.for-in.dynamics-1}

Reassigning a `var` `for-in` binding changes only that iteration's loop-local binding and
does not write the replacement value back into the iterated source.

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE3X2Zvcl9pbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICAvLyBBcnJheSBpdGVyYXRpb24uXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMF07XG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIGZvciAoeCBpbiBhcnIpIHsgc3VtICs9IHg7IH1cbiAgICBhc3NlcnQoc3VtID09IDYwKTtcbiAgICAvLyBFeGNsdXNpdmUgcmFuZ2UuXG4gICAgdmFyIHN1bTIgOj0gMDtcbiAgICBmb3IgKGkgaW4gMC4uNSkgeyBzdW0yICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtMiA9PSAxMCk7XG4gICAgLy8gSW5jbHVzaXZlIHJhbmdlLlxuICAgIHZhciBzdW0zIDo9IDA7XG4gICAgZm9yIChpIGluIDEuLj00KSB7IHN1bTMgKz0gaTsgfVxuICAgIGFzc2VydChzdW0zID09IDEwKTtcbiAgICAvLyBNdXRhYmxlIGZvci1pbiBiaW5kaW5nIG1heSBiZSByZWJvdW5kIGxvY2FsbHkuXG4gICAgdmFyIGJ1bXBlZCA6PSAwO1xuICAgIGZvciAodmFyIHggaW4gWzEsIDIsIDNdKSB7XG4gICAgICAgIHggKz0gMTtcbiAgICAgICAgYnVtcGVkICs9IHg7XG4gICAgfVxuICAgIGFzc2VydChidW1wZWQgPT0gOSk7XG4gICAgLy8gQnJlYWsgc3RvcHMgZWFybHkuXG4gICAgdmFyIHN1bTQgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDMsIDQsIDVdKSB7XG4gICAgICAgIGlmICh4ID09IDMpIHsgYnJlYWs7IH1cbiAgICAgICAgc3VtNCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQoc3VtNCA9PSAzKTtcbiAgICAvLyBDb250aW51ZSBza2lwcyB0aGUgY3VycmVudCBlbGVtZW50LlxuICAgIHZhciBzdW01IDo9IDA7XG4gICAgZm9yICh4IGluIFsxLCAyLCAzLCA0LCA1XSkge1xuICAgICAgICBpZiAoeCA9PSAzKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIHN1bTUgKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bTUgPT0gMTIpO1xuICAgIC8vIEJpbmRpbmcgZG9lcyBub3QgbGVhayBpbnRvIHRoZSBvdXRlciBzY29wZS5cbiAgICBsZXQgeCA6PSA0MjtcbiAgICB2YXIgaW5uZXIgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDNdKSB7IGlubmVyICs9IHg7IH1cbiAgICBhc3NlcnQoaW5uZXIgPT0gNik7XG4gICAgYXNzZXJ0KHggICA9PSA0Mik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTdfZm9yX2luLm10bCIsIm5hbWUiOiIxN19mb3JfaW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>
