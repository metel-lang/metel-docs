---
sidebar_position: 11
---

# References

References provide explicit aliasing.

```metel
fun main() -> i64 {
    var n := 1;
    let p: &var i64 := &var n;
    *p = 4;   // write-through: mutate the referent via explicit deref
    return *p; // explicit read of the referent
}
```

Rules:

- `&expr` creates a shared reference `&T` where `expr` is an addressable lvalue
- `&var x` creates an exclusive reference `&var T` where `x` is a `var` addressable lvalue
- `*p` dereferences a reference — reading the referent, or, as an assignment target
  (`*p = v`), writing through to it (see "Dereference" below)
- reading a plain value out of a reference is always `*p` (see
  [Types — Reading a value out of a reference](../types/references.md#reading-a-value-out-of-a-reference));
  field access, index, and method dispatch go through auto-deref (below)
- assigning to a reference-typed binding (`p = v`) **rebinds** it, like any other type;
  `*p = v` is the spelling that writes through

Addressable places for both `&` and `&var` include named bindings (`x`), struct field access (`s.field`), tuple element access (`t.0`), array indexing (`arr[i]`), a dereference (`*p` — so `&*p` is a reborrow that shares the referent's storage), and chains thereof (`nested.outer.field`, `t.1.0`).

Neither `&expr` nor `&var expr` requires `expr` to be an addressable place. A literal, call
result, struct or enum construction, or other non-addressable expression is materialized
into a fresh, independent cell and referenced directly — as in `foo(&Vec::new())` or
`foo(&var Vec::new())`, with no intermediate binding. This is sound for both forms because
nothing outside the expression can alias that cell.

```metel
> fun takes_ref(l: &List<i64>) -> i64 { l.len() }
> fun bump(x: &var i64) -> i64 { *x = *x + 1; *x }
> fun main() -> i64 {
>     let a := takes_ref(&List::from([1, 2, 3]));   // no `let` needed for the argument
>     let b := bump(&var 41);                        // &var works on a temporary too
>     return a + b;
> }
```

`&var` requires the operand to be a `var` binding — applying it to a plain `let` is a type error ([T0006](../../error-codes.md#t0006--assignment-to-immutable-binding)). `&var` on a lvalue path ([a struct field](#spec.expressions.references.dynamics-1), [tuple element](#spec.expressions.references.dynamics-2), [array element](#spec.expressions.references.dynamics-3), or [chain of projections](#spec.expressions.references.dynamics-4)) produces a true exclusive reference with write-back semantics, matching `&var` on a named binding exactly — writes through it propagate to the original storage location.

`&` on a field or element also aliases the original storage through [the same path machinery](#spec.expressions.references.dynamics-4), so later writes to the binding remain visible through the shared reference; it is still read-only, so writing through `&T` remains rejected. Reborrowing preserves this: `&*r` shares whatever storage `r` names, and reborrowing a `&var T` as `&T` downgrades to shared. The reverse is rejected — `&var *r` where `r: &T` is a type error ([T0006](../../error-codes.md#t0006--assignment-to-immutable-binding)), since a shared reference never grants write access.

[Tuple elements are assignable](assignment.md#spec.expressions.assignment.legality-1) like struct fields and array elements — `t.0 = v`, `t.0 += v`,
and nested or chained forms (`s.pair.0`, `t.1.0`), including through a `&var` reference. An
[out-of-range index is a type error](../types/tuples.md#spec.types.tuples.legality-8) ([T0003](../../error-codes.md#t0003--undefined-name)), and a
shared `&` grants no write access ([T0006](../../error-codes.md#t0006--assignment-to-immutable-binding)).

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-1}

Evaluating `&var value.field` creates an exclusive reference to that field. A write through
the reference updates the corresponding field in `value`.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-2}

Evaluating `&var value.n` creates an exclusive reference to tuple element `n`. A write
through the reference updates that element and leaves the other tuple elements unchanged.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-3}

Evaluating `&var values[index]` creates an exclusive reference to the selected array
element. A write through the reference is observable through subsequent indexing.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-4}

Evaluating `&var` over a chain of addressable projections creates an exclusive reference
to the chain's leaf storage. A write through the reference updates that original leaf.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## Dereference

`*expr` dereferences a `&T`/`&var T`. As an expression it reads the referent; [as an
assignment target](assignment.md#spec.expressions.assignment.legality-1), `*p = v` writes through a `&var T`. [Applying `*` to a non-reference is
a type error](#spec.expressions.references.legality-1) ([T0002](../../error-codes.md#t0002--annotation-required)).

Auto-deref covers **selectors only** — field access, indexing, and method dispatch, where
the target of the operation is unambiguous. Everywhere else, reading through a reference
is spelled explicitly:

```metel
fun add(x: i64, y: i64) -> i64 { x + y }

fun main() -> i64 {
    let a := 3;
    let b := 4;
    let p: &i64 := &a;
    let q: &i64 := &b;
    return add(*p, *q) + (*p + *q);   // explicit: call arguments and operands
}
```

Bare assignment to a reference-typed binding rebinds it rather than writing through, so a
`&var T` can be repointed:

```metel
fun main() -> i64 {
    var a := 1;
    var b := 2;
    var p: &var i64 := &var a;
    p = &var b;   // repoint: p now refers to b (p is `var`) — a stays 1
    *p = 5;       // write-through: b becomes 5
    return a + b; // 1 + 5
}
```

Field- and index-path targets keep writing through with no `*` needed — `s.field = v` and
`arr[i] = v` have no competing "rebind" reading, so they are unambiguous as they stand:

```metel
struct Point { x: i64, y: i64 }

fun main() -> i64 {
    var q := Point { x = 5, y = 7 };
    let qp: &var Point := &var q;
    qp.y = 99;        // field write-through — no `*` needed
    var xs := [1, 2, 3];
    let xp: &var [i64; 3] := &var xs;
    xp[0] = 9;        // index write-through — no `*` needed
    return q.y + xs[0];
}
```

`*(obj.field) := v` and `obj.field = v` are synonyms; for a bare identifier target, `*p = v`
is the only spelling that writes through.

Field access, field assignment, indexing, and method dispatch auto-dereference through a
reference:

```metel
struct Counter {
    value: i64,
}

extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}

fun main() -> i64 {
    var counter := Counter { value = 0 };
    let p: &var Counter := &var counter;
    p.increment();    // auto-deref: equivalent to accessing through the reference directly
    p.value = 1;      // auto-deref field assign; the reference binding need not be var
    return p.value;   // auto-deref field read
}
```

Function references (`&|| -> T` and `&var || -> T`) are callable directly, the same way:

```metel
fun main() -> i64 {
    let f := || { return 42; };
    let r: &|| -> i64 := &f;
    return r();       // auto-deref: calls through the reference directly
}
```

This applies uniformly: a closure or named function stored behind a reference can be called as if it were the function value itself. A common use is passing arrays of function references:

```metel
fun apply_all(fns: Array<&|| -> ()>) {
    for (let f in fns) {
        f();          // auto-deref each element
    }
}
```

Field access, method dispatch, and calling through a reference all chain through
multiple reference layers, not just one — `rr: &&var Counter` auto-derefs through both
levels to reach the `Counter` for a field read, a field write, or a method call
(`&var self` included: a shared outer layer doesn't remove the write access the inner
`&var` layer carries, it just adds a read-only step to reach it):

```metel
struct Counter { value: i64 }

extend Counter {
    fun increment(&var self) { self.value += 1; }
}

fun main() -> i64 {
    var c := Counter { value = 0 };
    let p: &var Counter := &var c;
    let rr: &&var Counter := &p;
    rr.increment();   // auto-deref through both layers
    return rr.value;  // likewise for a field read
}
```

Indexing, argument passing, and assignment remain ordinary reference operations — none of them is the value-extraction case (see `types.md`); reading the value out is `*p`.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-5}

Evaluating `&place` or `&var place` produces, respectively, a shared or exclusive
reference to the addressed storage; an exclusive reference can write through to that
same storage.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA0X3dyaXRlX3Rocm91Z2hfdGhpbl9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzEvXHUwMGE3Mzogd3JpdGUtdGhyb3VnaCBmb3IgYSB0aGluIHJlZmVyZW5jZSAoVmFsdWU6Ok11dFJlZmVyZW5jZSwgbm90IGFcbi8vIGZhdCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgZXZlcnkgZXhpc3RpbmcgZml4dHVyZSdzIHdyaXRlLXRocm91Z2ggY2FzZSBpcyBhXG4vLyBmaWVsZC90dXBsZS9hcnJheS1lbGVtZW50IHJlZmVyZW5jZTsgdGhpcyBjb3ZlcnMgYSBwbGFpbiBzY2FsYXIgYmluZGluZyBkaXJlY3RseSkuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgbiA6PSAxO1xuICAgIGxldCBwOiAmdmFyIGk2NCA6PSAmdmFyIG47XG4gICAgKnAgPSA0O1xuICAgIGFzc2VydChuID09IDQpO1xuXG4gICAgKnAgKz0gNjtcbiAgICBhc3NlcnQobiA9PSAxMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzA0X3dyaXRlX3Rocm91Z2hfdGhpbl9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjA0X3dyaXRlX3Rocm91Z2hfdGhpbl9yZWZlcmVuY2UubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-6}

Field access, field assignment, method dispatch, and calls through a reference
auto-dereference through every reference layer necessary to reach their receiver.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzM6IGF1dG8tZGVyZWYgZm9yIGZpZWxkIGFjY2Vzcy9tZXRob2QgZGlzcGF0Y2ggYWxyZWFkeSBjaGFpbnMgdGhyb3VnaFxuLy8gYXJiaXRyYXJ5IGRlcHRoIChcIiYmVCBkZXJlZnMgdGhyb3VnaCBib3RoIGxldmVsc1wiKSBpbmRlcGVuZGVudCBvZiByZWFkLWNvcHkgXHUyMDE0XG4vLyBjb25maXJtcyB0aGlzIHByZS1leGlzdGluZyBndWFyYW50ZWUgZXhwbGljaXRseSB1bmRlciB0aGUgbmV3ICZULyZ2YXIgVCBzeW50YXguXG5zdHJ1Y3QgQ291bnRlciB7IHZhbHVlOiBpNjQgfVxuXG5leHRlbmQgQ291bnRlciB7XG4gICAgZnVuIGdldCgmc2VsZikgLT4gaTY0IHtcbiAgICAgICAgc2VsZi52YWx1ZVxuICAgIH1cbiAgICBmdW4gYnVtcCgmdmFyIHNlbGYpIHtcbiAgICAgICAgc2VsZi52YWx1ZSArPSAxO1xuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIGMgOj0gQ291bnRlciB7IHZhbHVlID0gMSB9O1xuICAgIGxldCByOiAmdmFyIENvdW50ZXIgOj0gJnZhciBjO1xuICAgIGxldCBycjogJiZ2YXIgQ291bnRlciA6PSAmcjtcblxuICAgIGFzc2VydChyci52YWx1ZSA9PSAxKTtcbiAgICBhc3NlcnQocnIuZ2V0KCkgPT0gMSk7XG5cbiAgICByci5idW1wKCk7XG4gICAgYXNzZXJ0KGMudmFsdWUgPT0gMik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIiwibmFtZSI6IjA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBULiBSRkMtMDE4NTogcmVhZHMgYXJlIGV4cGxpY2l0IGAqcGAuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBSZWN0IHsgdG9wX2xlZnQ6IFBvaW50LCBib3R0b21fcmlnaHQ6IFBvaW50IH1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gJnZhciBzdHJ1Y3QuZmllbGQgXHUyMDE0IHdyaXRlIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgdmFyIHAgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcHg6ICZ2YXIgaTY0IDo9ICZ2YXIgcC54O1xuICAgICpweCA9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IGV4cGxpY2l0IGAqcHhgIHlpZWxkcyBjdXJyZW50IGZpZWxkIHZhbHVlLlxuICAgIGxldCByZWFkX3g6IGk2NCA6PSAqcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA9IDk5OTtcbiAgICBhc3NlcnQodC4xID09IDk5OSk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMDApO1xuXG4gICAgLy8gJnZhciBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgYTE6ICZ2YXIgaTY0IDo9ICZ2YXIgYXJyWzFdO1xuICAgICphMSA9IDQyO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA0Mik7XG4gICAgYXNzZXJ0KGFyclsyXSA9PSAzKTtcblxuICAgIC8vIENvbXBvdW5kIGFzc2lnbiB0aHJvdWdoIGFycmF5IGVsZW1lbnQgZmF0IHBvaW50ZXIuXG4gICAgKmExICs9IDg7XG4gICAgYXNzZXJ0KGFyclsxXSA9PSA1MCk7XG5cbiAgICAvLyBDaGFpbmVkIHBhdGg6ICZ2YXIgb3V0ZXIuaW5uZXIuZmllbGQgKG5lc3RlZCBzdHJ1Y3QpLlxuICAgIHZhciByIDo9IFJlY3Qge1xuICAgICAgICB0b3BfbGVmdCA9ICAgICBQb2ludCB7IHggPSAwLCB5ID0gMCB9LFxuICAgICAgICBib3R0b21fcmlnaHQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0sXG4gICAgfTtcbiAgICBsZXQgYnJ4OiAmdmFyIGk2NCA6PSAmdmFyIHIuYm90dG9tX3JpZ2h0Lng7XG4gICAgKmJyeCA9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA9IDk5O1xuICAgIGFzc2VydChxLnkgPT0gOTkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMTRfbXV0X2ZpZWxkX3BvaW50ZXIubXRsIiwibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-1}

The unary `*` operator requires a shared or exclusive reference operand. Applying it to a
non-reference is a `T0002` type error.

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAyIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzEyX2RlcmVmX25vbl9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gVFlQRUNIRUNLX0VSUk9SW1QwMDAyXVxuLy8gUkZDLTAxMTAgXHUwMGE3MzogYXBwbHlpbmcgYCpgIHRvIGEgbm9uLXJlZmVyZW5jZSBpcyBhIHR5cGUgZXJyb3IuIEFkZGluZyBwYXJzZXIgc3VwcG9ydFxuLy8gZm9yIGAqYCBpcyB3aGF0IG1ha2VzIGBVbmFyeU9wOjpEZXJlZmAncyBleGlzdGluZyB0eXBlIHJ1bGUgcmVhY2hhYmxlIGZyb20gc3VyZmFjZVxuLy8gc3ludGF4IGZvciB0aGUgZmlyc3QgdGltZS5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhOiBpNjQgOj0gMTtcbiAgICBsZXQgYiA6PSAqYTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvbmVnXzEyX2RlcmVmX25vbl9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ18xMl9kZXJlZl9ub25fcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-2}

Writing through `*place` requires an `&var T` reference; a shared `&T` never grants
write access.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwID0gNTsgICAgICAvLyB0d28gbGF5ZXJzLCB0d28gc3RhcnNcbiAgICBhc3NlcnQobiA9PSA1KTtcblxuICAgICoqcHAgKz0gMTA7XG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuXG4gICAgLy8gT25lIHN0YXIgcmVhY2hlcyB0aGUgaW5uZXIgcmVmZXJlbmNlIGl0c2VsZiwgbm90IHRoZSBpNjQgXHUyMDE0IHdoaWNoIGlzIHdoYXQgbWFrZXNcbiAgICAvLyByZXBvaW50aW5nIHRocm91Z2ggYSBjaGFpbiBleHByZXNzaWJsZSBhdCBhbGwuXG4gICAgdmFyIG0gOj0gMTAwO1xuICAgICpwcCA9ICZ2YXIgbTsgIC8vIHAgbm93IHJlZmVycyB0byBtOyBuIGtlZXBzIGl0cyB2YWx1ZVxuICAgIGFzc2VydChuID09IDE1KTtcbiAgICAqKnBwID0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgPSA1O1xuICAgIGFzc2VydChhID09IDUpO1xuXG4gICAgcCA9ICZ2YXIgYjsgICAgICAvLyByZXBvaW50IFx1MjAxNCBpbXBvc3NpYmxlIGJlZm9yZSBSRkMtMDExMFxuICAgICpwID0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgPSA5OTtcbiAgICBhc3NlcnQocXAueCA9PSA1KTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcblxuICAgIHZhciB4cyA6PSBbMSwgMiwgM107XG4gICAgbGV0IHhwOiAmdmFyIFtpNjQ7IDNdIDo9ICZ2YXIgeHM7XG4gICAgeHBbMF0gPSA5O1xuICAgIHhwWzFdICs9IDEwO1xuICAgIGFzc2VydCh4c1swXSA9PSA5KTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gMTIpO1xufVxuXG4vLyBgKihvYmouZmllbGQpID0gdmAgYW5kIGBvYmouZmllbGQgPSB2YCBhcmUgc3lub255bXMuXG5mdW4gcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCkge1xuICAgIHZhciBxIDo9IFBvaW50IHsgeCA9IDEsIHkgPSAyIH07XG4gICAgbGV0IHFwOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBxcC54ID0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAyIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzExX3dyaXRlX3Rocm91Z2hfc2hhcmVkX3JlZmVyZW5jZS5tdGwiLCJzb3VyY2UiOiIvLyBUWVBFQ0hFQ0tfRVJST1JbVDAwMDJdXG4vLyBSRkMtMDExMCBcdTAwYTc1OiBgKnAgPSB2YCByZXF1aXJlcyBgJnZhciBUYC4gQSBzaGFyZWQgYCZUYCBpcyBuZXZlciB3cml0dGVuIHRocm91Z2ggXHUyMDE0XG4vLyB0aGF0IGlzIHRoZSB3aG9sZSBjb250cmFjdCBvZiBhIHNoYXJlZCByZWZlcmVuY2UuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYSA6PSAxO1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgICpwID0gNTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvbmVnXzExX3dyaXRlX3Rocm91Z2hfc2hhcmVkX3JlZmVyZW5jZS5tdGwiLCJuYW1lIjoibmVnXzExX3dyaXRlX3Rocm91Z2hfc2hhcmVkX3JlZmVyZW5jZS5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-7}

Evaluating `*reference` reads its referent. Explicit dereference is available in every
expression position, while selector operations retain their ordinary auto-dereference.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgPSA1O1xuICAgIGFzc2VydChhID09IDUpO1xuXG4gICAgcCA9ICZ2YXIgYjsgICAgICAvLyByZXBvaW50IFx1MjAxNCBpbXBvc3NpYmxlIGJlZm9yZSBSRkMtMDExMFxuICAgICpwID0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgPSA5OTtcbiAgICBhc3NlcnQocXAueCA9PSA1KTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcblxuICAgIHZhciB4cyA6PSBbMSwgMiwgM107XG4gICAgbGV0IHhwOiAmdmFyIFtpNjQ7IDNdIDo9ICZ2YXIgeHM7XG4gICAgeHBbMF0gPSA5O1xuICAgIHhwWzFdICs9IDEwO1xuICAgIGFzc2VydCh4c1swXSA9PSA5KTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gMTIpO1xufVxuXG4vLyBgKihvYmouZmllbGQpID0gdmAgYW5kIGBvYmouZmllbGQgPSB2YCBhcmUgc3lub255bXMuXG5mdW4gcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCkge1xuICAgIHZhciBxIDo9IFBvaW50IHsgeCA9IDEsIHkgPSAyIH07XG4gICAgbGV0IHFwOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBxcC54ID0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAxIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzA2X25vX3JlYWRfY29weV9hdF9jYWxsX2FyZ3VtZW50Lm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUltUMDAwMV1cbi8vIFJGQy0wMTEwOiB1bmRlciB0aGUgR28gbW9kZWwsIHJlYWRpbmcgdGhyb3VnaCBhIHJlZmVyZW5jZSBpcyBpbXBsaWNpdCBvbmx5IGF0XG4vLyBzZWxlY3RvcnMgKGZpZWxkLCBpbmRleCwgbWV0aG9kKS4gQSBjYWxsIGFyZ3VtZW50IGlzIG5vdCBhIHNlbGVjdG9yLCBzbyBwYXNzaW5nIGFcbi8vIHJlZmVyZW5jZSB3aGVyZSB0aGUgcGFyYW1ldGVyIGV4cGVjdHMgdGhlIHJlZmVyZW50IHR5cGUgaXMgYSBoYXJkIG1pc21hdGNoIFx1MjAxNCB3cml0ZVxuLy8gYHRha2VzX2k2NCgqcilgLlxuLy9cbi8vIE5vdGUgdGhlIHJlYXNvbiBSRkMtMDA2N2EgXHUwMGE3M2Egb3JpZ2luYWxseSBnYXZlIGZvciB0aGlzIFx1MjAxNCBcInRoZXJlIGlzIG5vIGRlY2xhcmVkIHR5cGVcbi8vIGZvciB0aGUgYXJndW1lbnQgaXRzZWxmIHRvIGNvbXBhcmUgYWdhaW5zdFwiIFx1MjAxNCBpcyBmYWN0dWFsbHkgd3Jvbmc6IGBwYXJhbV9oaW50c2Bcbi8vIGFscmVhZHkgdGhyZWFkcyB0aGUgcGFyYW1ldGVyJ3MgZGVjbGFyZWQgdHlwZSBoZXJlIGZvciBtb25vbW9ycGhpYyBjYWxsZWVzLiBUaGVcbi8vIGJlaGF2aW9yIGlzIHJpZ2h0OyB0aGUganVzdGlmaWNhdGlvbiB3YXMgbm90LiBTZWUgUkZDLTAxMTIgXHUwMGE3NC4xLCB3aGljaCByZS1leGFtaW5lZFxuLy8gY2xvc2luZyB0aGlzIGdhcCBhbmQgZGVjbGluZWQgaXQgZGVsaWJlcmF0ZWx5IHJhdGhlciB0aGFuIGJ5IGFjY2lkZW50LlxuZnVuIHRha2VzX2k2NCh4OiBpNjQpIHt9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBuIDo9IDU7XG4gICAgbGV0IHI6ICZpNjQgOj0gJm47XG4gICAgdGFrZXNfaTY0KHIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy9uZWdfMDZfbm9fcmVhZF9jb3B5X2F0X2NhbGxfYXJndW1lbnQubXRsIiwibmFtZSI6Im5lZ18wNl9ub19yZWFkX2NvcHlfYXRfY2FsbF9hcmd1bWVudC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-8}

Each leading `*` reads or writes through exactly one reference layer. A bare assignment
to a reference-typed binding instead rebinds that binding when it is mutable.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwID0gNTsgICAgICAvLyB0d28gbGF5ZXJzLCB0d28gc3RhcnNcbiAgICBhc3NlcnQobiA9PSA1KTtcblxuICAgICoqcHAgKz0gMTA7XG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuXG4gICAgLy8gT25lIHN0YXIgcmVhY2hlcyB0aGUgaW5uZXIgcmVmZXJlbmNlIGl0c2VsZiwgbm90IHRoZSBpNjQgXHUyMDE0IHdoaWNoIGlzIHdoYXQgbWFrZXNcbiAgICAvLyByZXBvaW50aW5nIHRocm91Z2ggYSBjaGFpbiBleHByZXNzaWJsZSBhdCBhbGwuXG4gICAgdmFyIG0gOj0gMTAwO1xuICAgICpwcCA9ICZ2YXIgbTsgIC8vIHAgbm93IHJlZmVycyB0byBtOyBuIGtlZXBzIGl0cyB2YWx1ZVxuICAgIGFzc2VydChuID09IDE1KTtcbiAgICAqKnBwID0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgPSA1O1xuICAgIGFzc2VydChhID09IDUpO1xuXG4gICAgcCA9ICZ2YXIgYjsgICAgICAvLyByZXBvaW50IFx1MjAxNCBpbXBvc3NpYmxlIGJlZm9yZSBSRkMtMDExMFxuICAgICpwID0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgPSA5OTtcbiAgICBhc3NlcnQocXAueCA9PSA1KTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcblxuICAgIHZhciB4cyA6PSBbMSwgMiwgM107XG4gICAgbGV0IHhwOiAmdmFyIFtpNjQ7IDNdIDo9ICZ2YXIgeHM7XG4gICAgeHBbMF0gPSA5O1xuICAgIHhwWzFdICs9IDEwO1xuICAgIGFzc2VydCh4c1swXSA9PSA5KTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gMTIpO1xufVxuXG4vLyBgKihvYmouZmllbGQpID0gdmAgYW5kIGBvYmouZmllbGQgPSB2YCBhcmUgc3lub255bXMuXG5mdW4gcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCkge1xuICAgIHZhciBxIDo9IFBvaW50IHsgeCA9IDEsIHkgPSAyIH07XG4gICAgbGV0IHFwOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBxcC54ID0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-9}

An assignment through a dereference writes the referenced storage; after a mutable
reference binding is rebound, a later dereference writes the new referent.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwID0gNTsgICAgICAvLyB0d28gbGF5ZXJzLCB0d28gc3RhcnNcbiAgICBhc3NlcnQobiA9PSA1KTtcblxuICAgICoqcHAgKz0gMTA7XG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuXG4gICAgLy8gT25lIHN0YXIgcmVhY2hlcyB0aGUgaW5uZXIgcmVmZXJlbmNlIGl0c2VsZiwgbm90IHRoZSBpNjQgXHUyMDE0IHdoaWNoIGlzIHdoYXQgbWFrZXNcbiAgICAvLyByZXBvaW50aW5nIHRocm91Z2ggYSBjaGFpbiBleHByZXNzaWJsZSBhdCBhbGwuXG4gICAgdmFyIG0gOj0gMTAwO1xuICAgICpwcCA9ICZ2YXIgbTsgIC8vIHAgbm93IHJlZmVycyB0byBtOyBuIGtlZXBzIGl0cyB2YWx1ZVxuICAgIGFzc2VydChuID09IDE1KTtcbiAgICAqKnBwID0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgPSA1O1xuICAgIGFzc2VydChhID09IDUpO1xuXG4gICAgcCA9ICZ2YXIgYjsgICAgICAvLyByZXBvaW50IFx1MjAxNCBpbXBvc3NpYmxlIGJlZm9yZSBSRkMtMDExMFxuICAgICpwID0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgPSA5OTtcbiAgICBhc3NlcnQocXAueCA9PSA1KTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcblxuICAgIHZhciB4cyA6PSBbMSwgMiwgM107XG4gICAgbGV0IHhwOiAmdmFyIFtpNjQ7IDNdIDo9ICZ2YXIgeHM7XG4gICAgeHBbMF0gPSA5O1xuICAgIHhwWzFdICs9IDEwO1xuICAgIGFzc2VydCh4c1swXSA9PSA5KTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gMTIpO1xufVxuXG4vLyBgKihvYmouZmllbGQpID0gdmAgYW5kIGBvYmouZmllbGQgPSB2YCBhcmUgc3lub255bXMuXG5mdW4gcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCkge1xuICAgIHZhciBxIDo9IFBvaW50IHsgeCA9IDEsIHkgPSAyIH07XG4gICAgbGV0IHFwOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBxcC54ID0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-10}

Field and index assignment through a reference remains implicit because those targets
are unambiguous selectors; `*(object.field) := value` and `object.field = value` have the
same write effect.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgPSA1O1xuICAgIGFzc2VydChhID09IDUpO1xuXG4gICAgcCA9ICZ2YXIgYjsgICAgICAvLyByZXBvaW50IFx1MjAxNCBpbXBvc3NpYmxlIGJlZm9yZSBSRkMtMDExMFxuICAgICpwID0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgPSA5OTtcbiAgICBhc3NlcnQocXAueCA9PSA1KTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcblxuICAgIHZhciB4cyA6PSBbMSwgMiwgM107XG4gICAgbGV0IHhwOiAmdmFyIFtpNjQ7IDNdIDo9ICZ2YXIgeHM7XG4gICAgeHBbMF0gPSA5O1xuICAgIHhwWzFdICs9IDEwO1xuICAgIGFzc2VydCh4c1swXSA9PSA5KTtcbiAgICBhc3NlcnQoeHNbMV0gPT0gMTIpO1xufVxuXG4vLyBgKihvYmouZmllbGQpID0gdmAgYW5kIGBvYmouZmllbGQgPSB2YCBhcmUgc3lub255bXMuXG5mdW4gcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCkge1xuICAgIHZhciBxIDo9IFBvaW50IHsgeCA9IDEsIHkgPSAyIH07XG4gICAgbGV0IHFwOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBxcC54ID0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg3X3R1cGxlX2Fzc2lnbl9wYXRocy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgSG9sZGVyIHsgdDogKGk2NCwgKGk2NCwgaTY0KSkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSAoMSwgMik7XG4gICAgdC4wID0gNTtcbiAgICBhc3NlcnQodC4wID09IDUpO1xuICAgIHQuMCArPSA0O1xuICAgIGFzc2VydCh0LjAgPT0gOSk7XG5cbiAgICB2YXIgbmVzdGVkIDo9ICgxMCwgKDIwLCAzMCkpO1xuICAgIG5lc3RlZC4xLjAgPSA5OTtcbiAgICBhc3NlcnQobmVzdGVkLjEuMCA9PSA5OSk7XG5cbiAgICB2YXIgcyA6PSBIb2xkZXIgeyB0ID0gKDcsICg4LCA5KSkgfTtcbiAgICBzLnQuMCA9IDExO1xuICAgIGFzc2VydChzLnQuMCA9PSAxMSk7XG5cbiAgICB0dXBsZV9hc3NpZ25fdGhyb3VnaF9yZWZlcmVuY2VzKCk7XG59XG5cbi8vIFR1cGxlLWVsZW1lbnQgYXNzaWdubWVudCBtdXN0IHJlYWNoIHRocm91Z2ggYSByZWZlcmVuY2UgYXQgYW55IHN0ZXAgb2YgdGhlIHBhdGgsIHRoZVxuLy8gd2F5IGZpZWxkLSBhbmQgaW5kZXgtcGF0aCBhc3NpZ25tZW50IGFscmVhZHkgZG8uIE5laXRoZXIgcGFzcyBwZWVsZWQgZm9yIHR1cGxlIHRhcmdldHNcbi8vIHdoZW4gdGhlIHZhcmlhbnQgd2FzIGZpcnN0IGFkZGVkLCBzbyBgdC4wID0gdmAgd29ya2VkIG9uIGEgcGxhaW4gYmluZGluZyBidXQgbm90IG9uIGFcbi8vIGAmdmFyYCByZWNlaXZlciAtLSBhIHNlYW0gYmV0d2VlbiBtZXRlbC1jb3JlIzI4MyBhbmQgdGhlIFJGQy0wMTEwIHJlZmVyZW5jZSB3b3JrLlxuc3RydWN0IFJlZkhvbGRlciB7IHBhaXI6IChpNjQsIGk2NCkgfVxuXG5mdW4gc2V0X2RpcmVjdCh0OiAmdmFyIChpNjQsIGk2NCkpIHtcbiAgICB0LjAgPSA5O1xuICAgIHQuMSArPSA1O1xufVxuXG5mdW4gc2V0X25lc3RlZChoOiAmdmFyIFJlZkhvbGRlcikge1xuICAgIGgucGFpci4wID0gNDI7XG4gICAgaC5wYWlyLjEgKz0gMztcbn1cblxuZnVuIHR1cGxlX2Fzc2lnbl90aHJvdWdoX3JlZmVyZW5jZXMoKSB7XG4gICAgdmFyIHQgOj0gKDEsIDIpO1xuICAgIHNldF9kaXJlY3QoJnZhciB0KTtcbiAgICBhc3NlcnQodC4wID09IDkpO1xuICAgIGFzc2VydCh0LjEgPT0gNyk7XG5cbiAgICB2YXIgcmggOj0gUmVmSG9sZGVyIHsgcGFpciA9ICgxLCAyKSB9O1xuICAgIHNldF9uZXN0ZWQoJnZhciByaCk7XG4gICAgYXNzZXJ0KHJoLnBhaXIuMCA9PSA0Mik7XG4gICAgYXNzZXJ0KHJoLnBhaXIuMSA9PSA1KTtcblxuICAgIC8vIEEgc2hhcmVkIHJlZmVyZW5jZSBzdGlsbCBncmFudHMgbm8gd3JpdGUgYWNjZXNzLlxuICAgIGxldCByOiAmaTY0IDo9ICZyaC5wYWlyLjA7XG4gICAgcmgucGFpci4wID0gNztcbiAgICBhc3NlcnQoKnIgPT0gNyk7ICAgLy8gYW5kIGl0IGFsaWFzZXMgKG1ldGVsLWNvcmUjMjgyKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE2LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvODdfdHVwbGVfYXNzaWduX3BhdGhzLm10bCIsIm5hbWUiOiI4N190dXBsZV9hc3NpZ25fcGF0aHMubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-11}

Taking `&*reference` or `&var *reference` reborrows the storage named by the dereference;
an exclusive reborrow may write that same storage.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA2X2FkZHJlc3NhYmxlX3BsYWNlcy5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzI4MDogZXZlcnkgZm9ybSB0aGUgYWRkcmVzc2FiaWxpdHkgcnVsZSBhZG1pdHMga2VlcHMgd29ya2luZywgaW5jbHVkaW5nXG4vLyBSRkMtMDExMCBcdTAwYTc2J3MgcmVib3Jyb3cgYCYqcGAsIHdoaWNoIHByZXZpb3VzbHkgaGl0IHRoZSBzYW1lIGludGVybmFsIGVycm9yIGRlc3BpdGUgdGhlXG4vLyBSRkMgc3BlY2lmeWluZyBpdCBhcyBsZWdhbC5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBQYWlyIHsgYTogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgbiA6PSAxO1xuICAgIGxldCBhcnIgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB0IDo9ICgxMCwgMjApO1xuICAgIGxldCBwYWlyIDo9IFBhaXIgeyBhID0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSB9O1xuXG4gICAgbGV0IHAxIDo9ICZuOyAgICAgICAgICAgICAgLy8gYmluZGluZ1xuICAgIGxldCBwMiA6PSAmcGFpci5hOyAgICAgICAgIC8vIGZpZWxkXG4gICAgbGV0IHAzIDo9ICZwYWlyLmEueDsgICAgICAgLy8gY2hhaW5lZCBmaWVsZFxuICAgIGxldCBwNCA6PSAmdC4wOyAgICAgICAgICAgIC8vIHR1cGxlIGVsZW1lbnRcbiAgICBsZXQgcDUgOj0gJmFyclsxXTsgICAgICAgICAvLyBhcnJheSBlbGVtZW50XG4gICAgYXNzZXJ0KCpwMSA9PSAxKTtcbiAgICBhc3NlcnQoKnAzID09IDEpO1xuICAgIGFzc2VydCgqcDQgPT0gMTApO1xuICAgIGFzc2VydCgqcDUgPT0gMik7XG4gICAgYXNzZXJ0KHAyLnkgPT0gMik7XG5cbiAgICAvLyBSZWJvcnJvdzogYCYqcGAgc2hhcmVzIHRoZSByZWZlcmVudCdzIHN0b3JhZ2UgcmF0aGVyIHRoYW4gc25hcHNob3R0aW5nIGl0LlxuICAgIHZhciBtIDo9IDU7XG4gICAgbGV0IG1wOiAmdmFyIGk2NCA6PSAmdmFyIG07XG4gICAgbGV0IHJiIDo9ICYqbXA7XG4gICAgYXNzZXJ0KCpyYiA9PSA1KTtcblxuICAgIGxldCByYm0gOj0gJnZhciAqbXA7XG4gICAgKnJibSA9IDk7XG4gICAgYXNzZXJ0KG0gPT0gOSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9hZGRyZXNzYWJpbGl0eS8wNl9hZGRyZXNzYWJsZV9wbGFjZXMubXRsIiwibmFtZSI6IjA2X2FkZHJlc3NhYmxlX3BsYWNlcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>
