---
sidebar_position: 2
---

# Pattern Matching

`match` performs exhaustive pattern matching. All cases must be covered.

```metel
fun main() -> i64 {
    let value := 1;
    match (value) {
        1 => 10,
        _ => 0,
    }
}
```

[Each arm body can be any expression, or a block](#spec.expressions.pattern-matching.legality-1). `return`/`break`/`continue` are
themselves expressions of type `!` (see [Break, Continue, and Return](../control-flow/break-continue-return.md)
below), so a bare arm body like `1 => return 10` needs no special grammar case —
it's just an ordinary expression arm, like any other:

```metel
// Match arm body forms start here.
fun classify(value: i64) -> i64 {
    loop {
        break match (value) {
            0 => 0,
            1 => return 10,
            _ => { 20 },
        };
    }
}

fun main() -> i64 {
    return classify(0);
}
```

`match` is an expression — all arms must produce the same type:

```metel
fun main() -> i64 {
    let x := 1;
    let label := match (x) {
        0 => "zero",
        1 => "one",
        _ => "other",
    };
    return label.len();
}
```

Arms with blocks follow the same rules as function bodies: [the block's tail expression (if present) is the arm's value; a block with no tail produces `Unit`](#spec.expressions.pattern-matching.dynamics-1).

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let shape := Shape::Circle { radius = 3.0 };
    let desc: String := match (shape) {
        Shape::Circle { radius } => {
            let area := radius * radius;
            (area as i64).to_string()
        },
        Shape::Rectangle { width, height } => "rectangle",
    };
    return desc.len();
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.pattern-matching.legality-1}

A match arm body may be either a single expression or a block, and both forms may appear in
the same `match` expression.

<!-- rfc.py:last_reviewed 58b51abc04d9a96abb3604f28b34f09b66dcaa36 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2R5bl9hc3BlY3RfcGF0dGVybi5tdGwiLCJzb3VyY2UiOiJyZWNvcmQgTWVzc2FnZSB7IHRleHQ6IFN0cmluZyB9XG5hc3BlY3QgUmVuZGVyIHsgZnVuIHJlbmRlcigmc2VsZikgLT4gU3RyaW5nOyB9XG5leHRlbmQgTWVzc2FnZTogUmVuZGVyIHtcbiAgICBmdW4gcmVuZGVyKCZzZWxmKSAtPiBTdHJpbmcgeyBzZWxmLnRleHQuY2xvbmUoKSB9XG59XG5cbnR5cGUgUmVuZGVyYWJsZSA6PSBkeW4gUmVuZGVyO1xuZW51bSBEaXNwbGF5IHsgSXRlbSB7IHJlbmRlcmFibGU6IFJlbmRlcmFibGUgfSwgRW1wdHkgfVxuXG5mdW4gcmVuZGVyKGRpc3BsYXk6IERpc3BsYXkpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGRpc3BsYXkpIHtcbiAgICAgICAgRGlzcGxheTo6SXRlbSB7IHJlbmRlcmFibGUgfSA9PiByZW5kZXJhYmxlLnJlbmRlcigpLFxuICAgICAgICBEaXNwbGF5OjpFbXB0eSA9PiBcImVtcHR5XCIsXG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZGlzcGxheSA6PSBEaXNwbGF5OjpJdGVtIHsgcmVuZGVyYWJsZSA9IE1lc3NhZ2UgeyB0ZXh0ID0gXCJtYXRjaGVkXCIgfSB9O1xuICAgIGFzc2VydChyZW5kZXIoZGlzcGxheSkgPT0gXCJtYXRjaGVkXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYXNwZWN0cy9yZWxlYXNlX21hdHJpeF9keW5fYXNwZWN0X3BhdHRlcm4ubXRsIiwibmFtZSI6InJlbGVhc2VfbWF0cml4X2R5bl9hc3BlY3RfcGF0dGVybi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBPcHRpb248aTY0PiA6PSBPcHRpb246OlNvbWUgeyB2YWx1ZSA9IDEgfTtcbm1hdGNoIChtc2cpIHtcbiAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzE2XzBfZ2VuZXJpY19yZWNvcmRfcGF0dGVybnNfd2l0aF9leGhhdXN0aXZlbmVzc19zcHJlYWRzX2FuZF90dXBsZXMubXRsIiwic291cmNlIjoiLy8gdjAuMTYuMCBpbnRlZ3JhdGlvbjogYSBuYW1lZCByZWNvcmQgcGF0dGVybiBpbiBhIGdlbmVyaWMgYm9keSB4IG1hdGNoIGV4aGF1c3RpdmVuZXNzIG92ZXIgcmVjb3JkcyBhbmQgdHVwbGVzIHggcmVjb3JkXG4vLyBzcHJlYWQgdGhlbiByZXBsYWNlIHggYXNwZWN0cyBvbiBhIHJlc2lkdWFsIHggdHVwbGVzIGFzIHJvd3MgeCByZWNvcmQtcmVzdCBhbmQgbmVzdGVkIGZpZWxkIHBhdHRlcm5zLlxuY29weSBzdHJ1Y3QgVGFnIHsgbjogaTY0IH1cbmNvcHkgcmVjb3JkIENlbGwgeyB0YWc6IFRhZywgcGFpcjogKGk2NCwgaTY0KSwgZXh0cmE6IGk2NCB9XG5lbnVtIE1vZGUgeyBPbiwgT2ZmIH1cblxuZnVuIHBpY2s8VD4oYzogQ2VsbCwgdW51c2VkOiBUKSAtPiBpNjQge1xuICAgIGxldCAueyAudGFnOiBUYWcgeyBuIH0sIC5wYWlyOiAoYSwgYiksIC4uIH0gOj0gYztcbiAgICBuICsgYSArIGJcbn1cblxuZnVuIGNsYXNzaWZ5KG06IE1vZGUsIGM6IENlbGwpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKChtLCBjLnBhaXIpKSB7XG4gICAgICAgIChNb2RlOjpPbiwgKGEsIF8pKSA9PiBhLFxuICAgICAgICAoTW9kZTo6T2ZmLCAoXywgYikpID0+IHsgYiB9LFxuICAgIH1cbn1cblxuZnVuIHJlc3Q8VD4oYzogQ2VsbCwgdW51c2VkOiBUKSAtPiBpNjQge1xuICAgIGxldCByIDo9IC57IC4uYywgLmV4dHJhID0gOSB9O1xuICAgIGxldCAueyAuZXh0cmEsIC4uIH0gOj0gcjtcbiAgICBleHRyYVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYyA6PSBDZWxsIHsgdGFnID0gVGFnIHsgbiA9IDEgfSwgcGFpciA9ICgyLCAzKSwgZXh0cmEgPSA0IH07XG4gICAgYXNzZXJ0KHBpY2soYywgMCkgPT0gNik7XG4gICAgYXNzZXJ0KGNsYXNzaWZ5KE1vZGU6Ok9uLCBjKSA9PSAyKTtcbiAgICBhc3NlcnQoY2xhc3NpZnkoTW9kZTo6T2ZmLCBjKSA9PSAzKTtcbiAgICBhc3NlcnQocmVzdChjLCAwKSA9PSA5KTtcbiAgICBsZXQgYWdhaW4gOj0gYztcbiAgICBhc3NlcnQoYWdhaW4uZXh0cmEgPT0gNCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9pbnRlZ3JhdGlvbi92MF8xNl8wX2dlbmVyaWNfcmVjb3JkX3BhdHRlcm5zX3dpdGhfZXhoYXVzdGl2ZW5lc3Nfc3ByZWFkc19hbmRfdHVwbGVzLm10bCIsIm5hbWUiOiJ2MF8xNl8wX2dlbmVyaWNfcmVjb3JkX3BhdHRlcm5zX3dpdGhfZXhoYXVzdGl2ZW5lc3Nfc3ByZWFkc19hbmRfdHVwbGVzLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.dynamics-1}

A block arm evaluates its statements and then its tail expression, if any; that tail is the
arm's result, while a block with no tail produces `()`.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFic3RyYWN0X2Jvb2xlYW5fbWF0Y2gubXRsIiwic291cmNlIjoiZnVuIGNob29zZTxUPihjb25kaXRpb246IGJvb2xlYW4sIGZpcnN0OiBULCBzZWNvbmQ6IFQpIC0+IFQge1xuICAgIG1hdGNoIChjb25kaXRpb24pIHsgdHJ1ZSA9PiBmaXJzdCwgZmFsc2UgPT4gc2Vjb25kIH1cbn1cblxuZnVuIHJlc3RvcmVkPFQ+KGNvbmRpdGlvbjogYm9vbGVhbiwgb3JpZ2luYWw6IFQsIHJlcGxhY2VtZW50OiBUKSAtPiBUIHtcbiAgICB2YXIgdmFsdWUgOj0gb3JpZ2luYWw7XG4gICAgbGV0IGNvbnN1bWVkIDo9IHZhbHVlO1xuICAgIG1hdGNoIChjb25kaXRpb24pIHsgdHJ1ZSA9PiB7IHZhbHVlID0gcmVwbGFjZW1lbnQ7IH0sIF8gPT4geyB2YWx1ZSA9IHJlcGxhY2VtZW50OyB9IH1cbiAgICB2YWx1ZVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBhc3NlcnQoY2hvb3NlKHRydWUsIDcsIDkpID09IDcpO1xuICAgIGFzc2VydChjaG9vc2UoZmFsc2UsIDcsIDkpID09IDkpO1xuICAgIGFzc2VydChyZXN0b3JlZCh0cnVlLCAxLCAyKSA9PSAyKTtcbiAgICBhc3NlcnQocmVzdG9yZWQoZmFsc2UsIDEsIDMpID09IDMpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE1LjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay9hYnN0cmFjdF9ib29sZWFuX21hdGNoLm10bCIsIm5hbWUiOiJhYnN0cmFjdF9ib29sZWFuX21hdGNoLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFic3RyYWN0X3Jlc29sdmVkX21hdGNoLm10bCIsInNvdXJjZSI6ImVudW0gRmxhZyB7IE9uLCBPZmYgfVxuZW51bSBQYXlsb2FkPFQ+IHsgUHJlc2VudCB7IHZhbHVlOiBUIH0sIE1pc3NpbmcgfVxuc3RydWN0IEVudmVsb3BlPFQ+IHsgdmFsdWU6IFQgfVxuY29weSBzdHJ1Y3QgVGlja2V0IHsgY291bnQ6IGk2NCB9XG5cbmZ1biBjb3B5X3dpdG5lc3M8VD4odW51c2VkOiBUKSAtPiBpNjQge1xuICAgIGxldCB3aXRuZXNzIDo9IFRpY2tldCB7IGNvdW50ID0gMiB9O1xuICAgIGxldCBmaXJzdCA6PSB3aXRuZXNzO1xuICAgIGxldCBhZ2FpbiA6PSB3aXRuZXNzO1xuICAgIGZpcnN0LmNvdW50ICsgYWdhaW4uY291bnRcbn1cblxuZnVuIGV4dHJhY3Rfc2F2ZWQ8VD4odmFsdWU6IFBheWxvYWQ8VD4pIC0+IFQge1xuICAgIG1hdGNoICh2YWx1ZSkgeyBQcmVzZW50IHsgdmFsdWUgfSA9PiB2YWx1ZSwgTWlzc2luZyA9PiB7IGxvb3Age30gfSB9XG59XG5cbmZ1biB1bndyYXA8VD4odmFsdWU6IEVudmVsb3BlPFQ+KSAtPiBUIHsgdmFsdWUudmFsdWUgfVxuXG5mdW4gZmxhZzxUPih0YWc6IEZsYWcsIHVudXNlZDogVCkgLT4gYm9vbGVhbiB7XG4gICAgbWF0Y2ggKHRhZykgeyBPbiA9PiB0cnVlLCBPZmYgPT4gZmFsc2UgfVxufVxuXG5mdW4gY2hvb3NlPFQ+KHRhZzogaTY0LCBmaXJzdDogVCwgc2Vjb25kOiBUKSAtPiBUIHtcbiAgICBtYXRjaCAodGFnKSB7IDEgPT4gZmlyc3QsIF8gPT4gc2Vjb25kIH1cbn1cblxuZnVuIHdob2xlPFQ+KHZhbHVlOiBUKSAtPiBUIHtcbiAgICBtYXRjaCAodmFsdWUpIHsgYm91bmQgPT4gYm91bmQgfVxufVxuXG5mdW4gbWFrZTxUPih2YWx1ZTogVCwgbWFyazogJnZhciBpNjQpIC0+IE9wdGlvbjxUPiB7XG4gICAgKm1hcmsgPSAqbWFyayArIDE7XG4gICAgT3B0aW9uOjpTb21lIHsgdmFsdWUgPSB2YWx1ZSB9XG59XG5cbmZ1biBleHRyYWN0PFQ+KHZhbHVlOiBULCBtYXJrOiAmdmFyIGk2NCkgLT4gVCB7XG4gICAgbWF0Y2ggKG1ha2UodmFsdWUsIG1hcmspKSB7IFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLCBOb25lID0+IHsgbG9vcCB7fSB9IH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGZsYWcoRmxhZzo6T24sIFwidW51c2VkXCIpKTtcbiAgICBhc3NlcnQoIWZsYWcoRmxhZzo6T2ZmLCAwKSk7XG4gICAgYXNzZXJ0KGNob29zZSgxLCBcImZpcnN0XCIsIFwic2Vjb25kXCIpID09IFwiZmlyc3RcIik7XG4gICAgYXNzZXJ0KGNob29zZSgyLCBcImZpcnN0XCIsIFwic2Vjb25kXCIpID09IFwic2Vjb25kXCIpO1xuICAgIGFzc2VydCh3aG9sZShcIm93bmVkXCIpID09IFwib3duZWRcIik7XG4gICAgdmFyIG1hcmsgOj0gMDtcbiAgICBhc3NlcnQoZXh0cmFjdChcInBheWxvYWRcIiwgJnZhciBtYXJrKSA9PSBcInBheWxvYWRcIik7XG4gICAgYXNzZXJ0KG1hcmsgPT0gMSk7XG4gICAgYXNzZXJ0KGV4dHJhY3Rfc2F2ZWQoUGF5bG9hZDo6UHJlc2VudCB7IHZhbHVlID0gXCJzYXZlZFwiIH0pID09IFwic2F2ZWRcIik7XG4gICAgYXNzZXJ0KHVud3JhcChFbnZlbG9wZSB7IHZhbHVlID0gXCJlbmNsb3NlZFwiIH0pID09IFwiZW5jbG9zZWRcIik7XG4gICAgYXNzZXJ0KGNvcHlfd2l0bmVzcyhcInVudXNlZFwiKSA9PSA0KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL21vdmVfY2hlY2svYWJzdHJhY3RfcmVzb2x2ZWRfbWF0Y2gubXRsIiwibmFtZSI6ImFic3RyYWN0X3Jlc29sdmVkX21hdGNoLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBPcHRpb248aTY0PiA6PSBPcHRpb246OlNvbWUgeyB2YWx1ZSA9IDEgfTtcbm1hdGNoIChtc2cpIHtcbiAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-2}

Bindings introduced by an arm's pattern are in scope throughout that arm's block body.

<!-- rfc.py:last_reviewed 8156f9b70d40f62450255e0a8c9ce9c1af2d21b4 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBPcHRpb248aTY0PiA6PSBPcHRpb246OlNvbWUgeyB2YWx1ZSA9IDEgfTtcbm1hdGNoIChtc2cpIHtcbiAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-3}

A `match` expression's scrutinee must be enclosed in parentheses — `match (x) { … }`.
The bare form `match x { … }` is a parse error. A tuple scrutinee's own parentheses
satisfy this (`match (a, b) { … }`), as does the unit literal (`match () { … }`).

<!-- rfc.py:last_reviewed 7ff6bac2f3c159c0d57a74f61abbe3fcb3000089 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0156](../../../../rfcs/4-implemented/rfc-0156-parenthesize-match-scrutinee.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1hdGNoX3NjcnV0aW5lZV9wYXJlbnRoZXNpemVkLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTU2OiB0aGUgcGFyZW50aGVzaXplZCBgbWF0Y2hgIHNjcnV0aW5lZSBmb3JtcyBcdTIwMTQgYSBwbGFpbiBwYXJlbnRoZXNpemVkXG4vLyBleHByZXNzaW9uLCBhIHR1cGxlIChpdHMgb3duIHBhcmVucyBzYXRpc2Z5IHRoZSByZXF1aXJlbWVudCksIGFuZCB0aGUgdW5pdFxuLy8gbGl0ZXJhbC5cbmZ1biBjbGFzc2lmeShuOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKG4pIHtcbiAgICAgICAgMCA9PiAwLFxuICAgICAgICBfID0+IDEsXG4gICAgfVxufVxuXG5mdW4gbWFpbigpIC0+IGk2NCB7XG4gICAgbGV0IHBhaXI6IChpNjQsIGk2NCkgOj0gKDEsIDIpO1xuICAgIGxldCBhIDo9IG1hdGNoIChwYWlyKSB7XG4gICAgICAgICgxLCAyKSA9PiAxMCxcbiAgICAgICAgXyA9PiAwLFxuICAgIH07XG4gICAgbGV0IGIgOj0gbWF0Y2ggKDEsIDIpIHtcbiAgICAgICAgKDEsIDIpID0+IDIwLFxuICAgICAgICBfID0+IDAsXG4gICAgfTtcbiAgICBsZXQgYyA6PSBtYXRjaCAoKSB7XG4gICAgICAgIF8gPT4gMzAsXG4gICAgfTtcbiAgICByZXR1cm4gY2xhc3NpZnkoMCkgKyBhICsgYiArIGM7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3BhcnNpbmcvbWF0Y2hfc2NydXRpbmVlX3BhcmVudGhlc2l6ZWQubXRsIiwibmFtZSI6Im1hdGNoX3NjcnV0aW5lZV9wYXJlbnRoZXNpemVkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMTZfYmFyZV9tYXRjaF9zY3J1dGluZWUubXRsIiwic291cmNlIjoiLy8gUkZDLTAxNTY6IGEgYG1hdGNoYCBzY3J1dGluZWUgbXVzdCBiZSBwYXJlbnRoZXNpemVkLCBsaWtlIGBpZmAvYHdoaWxlYC9gZm9yYC5cbi8vIFRoZSBiYXJlIGBtYXRjaCB4IHsgLi4uIH1gIGZvcm0gaXMgYSBoYXJkIHBhcnNlIGVycm9yIFx1MjAxNCBubyBhbGlhcy5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBtYXRjaCAxIHtcbiAgICAgICAgMSA9PiAxMCxcbiAgICAgICAgXyA9PiAwLFxuICAgIH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNS4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uZWdfMTZfYmFyZV9tYXRjaF9zY3J1dGluZWUubXRsIiwibmFtZSI6Im5lZ18xNl9iYXJlX21hdGNoX3NjcnV0aW5lZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzE2XzBfZGlzcGxheV9jbG9uZV9jb3B5X2RlY2xhcmF0aW9uc19hbmRfZXhoYXVzdGl2ZV9tYXRjaGVzLm10bCIsInNvdXJjZSI6Ii8vIHYwLjE2LjAgaW50ZWdyYXRpb246IERpc3BsYXkgb2YgYW5vbnltb3VzIHJlY29yZHMgYW5kIGAoKWAgeCBidWlsdC1pbiBhbmQgZGVyaXZlZCBDbG9uZSB4IGNvcHkoVCkgYW5kIENvcHkgZGVjbGFyYXRpb25zIHhcbi8vIGV4aGF1c3RpdmUgbWF0Y2hlcyBvdmVyIHR1cGxlcywgbmFtZWQgcmVjb3JkcyBhbmQgbmVzdGVkIHBhdHRlcm5zIHggYSBjbG9zdXJlIGFuZCBhIGNvcHkgZnVuY3Rpb24gaW4gYSBnZW5lcmljIGJvZHkuXG5jb3B5KFQpIHN0cnVjdCBCb3hlZDxUPiB7IHZhbHVlOiBUIH1cbmNvcHkgc3RydWN0IFRhZyB7IG46IGk2NCB9XG5jb3B5IHJlY29yZCBDZWxsIHsgdGFnOiBUYWcsIHBhaXI6IChpNjQsIGk2NCksIGV4dHJhOiBpNjQgfVxuZW51bSBNb2RlIHsgT24sIE9mZiB9XG5cbmZ1biBjbGFzc2lmeShtOiBNb2RlLCBjOiBDZWxsKSAtPiBpNjQge1xuICAgIG1hdGNoICgobSwgYykpIHtcbiAgICAgICAgKE1vZGU6Ok9uLCAueyAudGFnOiBUYWcgeyBuIH0sIC5wYWlyOiAoYSwgXyksIC4uIH0pID0+IG4gKyBhLFxuICAgICAgICAoTW9kZTo6T2ZmLCAueyAuZXh0cmEsIC4uIH0pID0+IGV4dHJhLFxuICAgIH1cbn1cblxuZnVuIHR3aWNlPFQ+KGM6IENlbGwsIGY6IGNvcHkgfGk2NHwgLT4gaTY0LCB1bnVzZWQ6IFQpIC0+IGk2NCB7XG4gICAgbGV0IGcgOj0gfHwgeyBjLmV4dHJhIH07XG4gICAgbGV0IGggOj0gZjtcbiAgICBsZXQgayA6PSBmO1xuICAgIGgoZygpKSArIGsoYy5wYWlyLjApXG59XG5cbmZ1biBkdXA8VDogQ29weT4oeDogVCkgLT4gVCB7IHguY2xvbmUoKSB9XG5cbmZ1biB1bnBhY2s8VD4oYzogQ2VsbCwgdW51c2VkOiBUKSAtPiBpNjQge1xuICAgIGxldCAueyAuZXh0cmEsIC4uIH0gOj0gYztcbiAgICBtYXRjaCAoYykge1xuICAgICAgICAueyAudGFnOiBUYWcgeyBuIH0sIC4uIH0gPT4gbiArIGV4dHJhLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGQgOj0gLnsgLmEgPSAxLCAuYiA9IDIgfTtcbiAgICBsZXQgY29weV9vZiA6PSBkLmNsb25lKCk7XG4gICAgYXNzZXJ0KFwiJHtjb3B5X29mfVwiID09IFwiJHtkfVwiKTtcbiAgICBhc3NlcnQoXCIke2R9XCIgPT0gXCIueyAuYTogMSwgLmI6IDIgfVwiKTtcbiAgICBhc3NlcnQoXCIkeygpfVwiID09IFwiKClcIik7XG4gICAgbGV0IGIgOj0gQm94ZWQgeyB2YWx1ZSA9IDIgfTtcbiAgICBsZXQgYjIgOj0gYjtcbiAgICBsZXQgYjMgOj0gYjtcbiAgICBhc3NlcnQoYjIudmFsdWUgKyBiMy52YWx1ZSA9PSA0KTtcbiAgICBsZXQgYjQgOj0gZHVwKGIpO1xuICAgIGFzc2VydChiNC52YWx1ZSA9PSAyKTtcbiAgICBsZXQgYyA6PSBDZWxsIHsgdGFnID0gVGFnIHsgbiA9IDEgfSwgcGFpciA9ICgyLCAzKSwgZXh0cmEgPSA0IH07XG4gICAgbGV0IGluYzogY29weSB8aTY0fCAtPiBpNjQgOj0gfHh8IHsgeCArIDEgfTtcbiAgICBhc3NlcnQoY2xhc3NpZnkoTW9kZTo6T24sIGMpID09IDMpO1xuICAgIGFzc2VydChjbGFzc2lmeShNb2RlOjpPZmYsIGMpID09IDQpO1xuICAgIGFzc2VydCh0d2ljZShjLCBpbmMsIDApID09IDgpO1xuICAgIGFzc2VydCh1bnBhY2soYywgMCkgPT0gNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTUuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9pbnRlZ3JhdGlvbi92MF8xNl8wX2Rpc3BsYXlfY2xvbmVfY29weV9kZWNsYXJhdGlvbnNfYW5kX2V4aGF1c3RpdmVfbWF0Y2hlcy5tdGwiLCJuYW1lIjoidjBfMTZfMF9kaXNwbGF5X2Nsb25lX2NvcHlfZGVjbGFyYXRpb25zX2FuZF9leGhhdXN0aXZlX21hdGNoZXMubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Pattern Kinds

| Pattern | Example | Matches |
|---------|---------|---------|
| Wildcard | `_` | anything, binds nothing |
| Binding | `n` | anything, binds to `n` |
| Literal | `0`, `"hi"`, `true` | exact value |
| Enum variant | `Direction::North`, `North` | unit variant (qualified or bare) |
| Enum with fields | `Shape::Circle { radius }`, `Circle { radius }` | variant, binds fields |
| Struct | `Point { x, y }`, `Token { kind, .. }` | struct, binds named fields |
| Tuple | `(a, b)` | tuple, binds elements |
| Guard | `n if n < 0` | binding + boolean condition |

## Examples

```metel
// Pattern examples start here.
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let shape := Shape::Rectangle { width = 4.0, height = 2.0 };
    let x := -3;
    let point: (i64, i64) := (0, 7);

    let a := match (shape) {
        Shape::Circle { radius } => radius as i64,
        Shape::Rectangle { width, height } => width as i64,
    };

    let b := match (x) {
        0          => 0,
        n if n < 0 => 1,
        _          => 2,
    };

    let c := match (point) {
        (0, 0) => 0,
        (x, 0) => x,
        (0, y) => y,
        (x, y) => x + y,
    };

    return a + b + c;
}
```
