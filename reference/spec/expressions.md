# Expressions

## Pattern Matching

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
themselves expressions of type `!` (see [Break, Continue, and Return](#break-continue-and-return)
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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBQZXJoYXBzPGk2ND4gOj0gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMSB9O1xubWF0Y2ggKG1zZykge1xuICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.dynamics-1}

A block arm evaluates its statements and then its tail expression, if any; that tail is the
arm's result, while a block with no tail produces `()`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBQZXJoYXBzPGk2ND4gOj0gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMSB9O1xubWF0Y2ggKG1zZykge1xuICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-2}

Bindings introduced by an arm's pattern are in scope throughout that arm's block body.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0018](../../rfcs/4-implemented/rfc-0018-match-arm-blocks.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCIsInNvdXJjZSI6Ii8vIFN0YWdlIDc6IG1hdGNoIGFybXMgd2l0aCBibG9jayBib2RpZXMgKFJGQy0wMDE4KS5cbi8vIEFybXMgY2FuIHVzZSBlaXRoZXIgYD0+IGV4cHJgIG9yIGA9PiB7IHN0bXRzKiBleHByPyB9YC5cblxuZW51bSBTaGFwZSB7XG4gICAgQ2lyY2xlIHsgcmFkaXVzOiBmNjQgfSxcbiAgICBSZWN0YW5nbGUgeyB3aWR0aDogZjY0LCBoZWlnaHQ6IGY2NCB9LFxufVxuXG5sZXQgczogU2hhcGUgOj0gU2hhcGU6OkNpcmNsZSB7IHJhZGl1cyA9IDMuMCB9O1xuXG4vLyBCbG9jayBhcm0gd2l0aCBhIGxvY2FsIGJpbmRpbmcgYW5kIGNvbXB1dGF0aW9uLlxubGV0IGFyZWE6IGY2NCA6PSBtYXRjaCAocykge1xuICAgIFNoYXBlOjpDaXJjbGUgeyByYWRpdXMgfSA9PiB7XG4gICAgICAgIGxldCByIDo9IHJhZGl1cztcbiAgICAgICAgciAqIHJcbiAgICB9LFxuICAgIFNoYXBlOjpSZWN0YW5nbGUgeyB3aWR0aCwgaGVpZ2h0IH0gPT4gd2lkdGggKiBoZWlnaHQsXG59O1xuXG4vLyBCbG9jayBhcm0gcHJvZHVjaW5nIHVuaXQgKG5vIHRhaWwgZXhwcmVzc2lvbikuXG5sZXQgbXNnOiBQZXJoYXBzPGk2ND4gOj0gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMSB9O1xubWF0Y2ggKG1zZykge1xuICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IHtcbiAgICAgICAgbGV0IHYgOj0gdmFsdWU7XG4gICAgfSxcbiAgICBOb25lID0+IHt9LFxufTtcblxuLy8gTWl4ZWQ6IG9uZSBhcm0gaXMgYSBiYXJlIGV4cHIsIG9uZSBpcyBhIGJsb2NrLlxubGV0IG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+IDo9IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDUgfTtcbmxldCBuOiBpNjQgOj0gbWF0Y2ggKG9rKSB7XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHtcbiAgICAgICAgbGV0IGZhbGxiYWNrIDo9IDA7XG4gICAgICAgIGZhbGxiYWNrXG4gICAgfSxcbn07XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9mdW5jdGlvbnMvc3RhZ2U3XzAyX21hdGNoX2FybV9ibG9ja3MubXRsIiwibmFtZSI6InN0YWdlN18wMl9tYXRjaF9hcm1fYmxvY2tzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.legality-3}

A `match` expression's scrutinee must be enclosed in parentheses — `match (x) { … }`.
The bare form `match x { … }` is a parse error. A tuple scrutinee's own parentheses
satisfy this (`match (a, b) { … }`), as does the unit literal (`match () { … }`).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0156](../../rfcs/4-implemented/rfc-0156-parenthesize-match-scrutinee.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1hdGNoX3NjcnV0aW5lZV9wYXJlbnRoZXNpemVkLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTU2OiB0aGUgcGFyZW50aGVzaXplZCBgbWF0Y2hgIHNjcnV0aW5lZSBmb3JtcyBcdTIwMTQgYSBwbGFpbiBwYXJlbnRoZXNpemVkXG4vLyBleHByZXNzaW9uLCBhIHR1cGxlIChpdHMgb3duIHBhcmVucyBzYXRpc2Z5IHRoZSByZXF1aXJlbWVudCksIGFuZCB0aGUgdW5pdFxuLy8gbGl0ZXJhbC5cbmZ1biBjbGFzc2lmeShuOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKG4pIHtcbiAgICAgICAgMCA9PiAwLFxuICAgICAgICBfID0+IDEsXG4gICAgfVxufVxuXG5mdW4gbWFpbigpIC0+IGk2NCB7XG4gICAgbGV0IHBhaXI6IChpNjQsIGk2NCkgOj0gKDEsIDIpO1xuICAgIGxldCBhIDo9IG1hdGNoIChwYWlyKSB7XG4gICAgICAgICgxLCAyKSA9PiAxMCxcbiAgICAgICAgXyA9PiAwLFxuICAgIH07XG4gICAgbGV0IGIgOj0gbWF0Y2ggKDEsIDIpIHtcbiAgICAgICAgKDEsIDIpID0+IDIwLFxuICAgICAgICBfID0+IDAsXG4gICAgfTtcbiAgICBsZXQgYyA6PSBtYXRjaCAoKSB7XG4gICAgICAgIF8gPT4gMzAsXG4gICAgfTtcbiAgICByZXR1cm4gY2xhc3NpZnkoMCkgKyBhICsgYiArIGM7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3BhcnNpbmcvbWF0Y2hfc2NydXRpbmVlX3BhcmVudGhlc2l6ZWQubXRsIiwibmFtZSI6Im1hdGNoX3NjcnV0aW5lZV9wYXJlbnRoZXNpemVkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMTZfYmFyZV9tYXRjaF9zY3J1dGluZWUubXRsIiwic291cmNlIjoiLy8gUkZDLTAxNTY6IGEgYG1hdGNoYCBzY3J1dGluZWUgbXVzdCBiZSBwYXJlbnRoZXNpemVkLCBsaWtlIGBpZmAvYHdoaWxlYC9gZm9yYC5cbi8vIFRoZSBiYXJlIGBtYXRjaCB4IHsgLi4uIH1gIGZvcm0gaXMgYSBoYXJkIHBhcnNlIGVycm9yIFx1MjAxNCBubyBhbGlhcy5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBtYXRjaCAxIHtcbiAgICAgICAgMSA9PiAxMCxcbiAgICAgICAgXyA9PiAwLFxuICAgIH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvcGFyc2luZy9uZWdfMTZfYmFyZV9tYXRjaF9zY3J1dGluZWUubXRsIiwibmFtZSI6Im5lZ18xNl9iYXJlX21hdGNoX3NjcnV0aW5lZS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Pattern Kinds

| Pattern | Example | Matches |
|---------|---------|---------|
| Wildcard | `_` | anything, binds nothing |
| Binding | `n` | anything, binds to `n` |
| Literal | `0`, `"hi"`, `true` | exact value |
| Enum variant | `Direction::North`, `North` | unit variant (qualified or, since v0.11.0, bare) |
| Enum with fields | `Shape::Circle { radius }`, `Circle { radius }` | variant, binds fields |
| Struct | `Point { x, y }`, `Token { kind, .. }` | struct, binds named fields |
| Tuple | `(a, b)` | tuple, binds elements |
| Guard | `n if n < 0` | binding + boolean condition |

### Examples

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

### Unqualified variant constructors

> **Since v0.11.0 (RFC-0111).**

A bare variant name may be used where the *expected* type determines which enum is meant —
the expression-position counterpart of "Unqualified variant patterns" below. Both no-field
and fieldful variants participate, and per RFC-0106 the empty-brace spelling `Red {}` is
equally valid:

```metel
enum Colour { Red, Green, Blue }

fun paint(c: Colour) { }
fun favourite() -> Colour { Green }        // return type supplies the expected type

fun main() {
    let c: Colour := Red;                   // annotation supplies it
    paint(Blue);                           // parameter type supplies it
    let p: Perhaps<i64> := Some { value = 5 };
    let q: Perhaps<i64> := None;            // `None` is an ordinary variant, not a literal
}
```

Resolution is type-directed against the expected type only — never a lexical import of
variant names — so two enums may both declare `Red` with no ambiguity.

**A bare variant is a last resort, never a shadowing mechanism.** It resolves only when the
name means nothing else in scope — not a binding, and not a unit struct (`struct Red {}` and
`enum C { Red }` may coexist, and `Red` then means the struct even where a `C` is expected;
write `C::Red`).

**An in-scope binding wins over a variant of the same name.** This is the opposite of
pattern position, and deliberately so: a pattern *introduces* names, so a bare identifier
there is always the variant, while an expression *uses* names and must resolve to the
nearest binding or lexical scoping breaks.

```metel
fun demo(Red: i64) -> i64 {
    return Red;          // the parameter, not Colour::Red
}
```

**Where no expected type exists, the bare form does not resolve** and the name is reported
as undefined ([T0003](../error-codes.md#t0003--undefined-name)) — there is deliberately no
search for "some enum, somewhere, declaring `Red`". Qualify (`Colour::Red`) or ascribe
(`Red: Colour`). This affects an unannotated `let x = Red;`, an argument to a *generic*
callee (whose parameter types are not known until the arguments are), and the body of a
closure with no declared return type. `None` without a determinable type keeps its existing
[T0002](../error-codes.md#t0002--annotation-required) "add a type annotation" diagnostic
rather than degrading to T0003.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-1}

A bare no-field or fieldful enum variant is valid in expression position when the
expected type determines its enum and no binding or declaration of that name is in scope.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCIsInNvdXJjZSI6ImVudW0gQ29sb3VyIHsgUmVkLCBHcmVlbiwgQmx1ZSB9XG5cbnN0cnVjdCBIb2xkZXIge1xuICAgIGNvbG91cjogQ29sb3VyLFxuICAgIG1heWJlOiBQZXJoYXBzPGk2ND4sXG4gICAgbm90aGluZzogUGVyaGFwczxpNjQ+LFxuICAgIG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+LFxuICAgIGVycjogUmVzdWx0PGk2NCwgU3RyaW5nPixcbn1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gMSxcbiAgICAgICAgR3JlZW4gPT4gMixcbiAgICAgICAgQmx1ZSA9PiAzLFxuICAgIH1cbn1cblxuZnVuIGZhdm91cml0ZSgpIC0+IENvbG91ciB7XG4gICAgR3JlZW5cbn1cblxuZnVuIHNoYWRvdyhSZWQ6IGk2NCkgLT4gaTY0IHtcbiAgICByZXR1cm4gUmVkO1xufVxuXG5mdW4gdW53cmFwX3Jlc3VsdChyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+KSAtPiBpNjQge1xuICAgIG1hdGNoIChyKSB7XG4gICAgICAgIE9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjOiBDb2xvdXIgOj0gUmVkO1xuICAgIGxldCBjMjogQ29sb3VyIDo9IFJlZCB7fTtcbiAgICBhc3NlcnQocGFpbnQoYykgPT0gMSk7XG4gICAgYXNzZXJ0KHBhaW50KGMyKSA9PSAxKTtcbiAgICBhc3NlcnQocGFpbnQoQmx1ZSkgPT0gMyk7XG4gICAgYXNzZXJ0KHBhaW50KGZhdm91cml0ZSgpKSA9PSAyKTtcblxuICAgIGxldCBob2xkZXIgOj0gSG9sZGVyIHtcbiAgICAgICAgY29sb3VyID0gQmx1ZSxcbiAgICAgICAgbWF5YmUgPSBTb21lIHsgdmFsdWUgPSA1IH0sXG4gICAgICAgIG5vdGhpbmcgPSBOb25lLFxuICAgICAgICBvayA9IE9rIHsgdmFsdWUgPSA5IH0sXG4gICAgICAgIGVyciA9IEVyciB7IGVycm9yID0gXCJiYWRcIiB9LFxuICAgIH07XG5cbiAgICBhc3NlcnQocGFpbnQoaG9sZGVyLmNvbG91cikgPT0gMyk7XG4gICAgYXNzZXJ0KHNoYWRvdyg3KSA9PSA3KTtcblxuICAgIG1hdGNoIChob2xkZXIubWF5YmUpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxuXG4gICAgbWF0Y2ggKGhvbGRlci5ub3RoaW5nKSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KHRydWUpLFxuICAgIH1cblxuICAgIGFzc2VydCh1bndyYXBfcmVzdWx0KGhvbGRlci5vaykgPT0gOSk7XG4gICAgYXNzZXJ0KHVud3JhcF9yZXN1bHQoaG9sZGVyLmVycikgPT0gLTEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvNDFfdW5xdWFsaWZpZWRfdmFyaWFudF9jb25zdHJ1Y3RvcnMubXRsIiwibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQyX3ZhcmlhbnRfZGVmZXJyYWxfcmVzb2x2ZXMubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMyODUncyBjaGVjayBtdXN0IG5vdCBmaXJlIG9uIGEgZGVmZXJyYWwgdGhhdCAqZG9lcyogcmVzb2x2ZSwgYXQgYW55IG9mIHRoZVxuLy8gcG9zaXRpb25zIFJGQy0wMTExIHN1cHBvcnRzLCBhbmQgbXVzdCBsZWF2ZSBnZW51aW5lbHkgcG9seW1vcnBoaWMgZGVmZXJyYWxzIGFsb25lLlxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbmZ1biBmYXZvdXJpdGUoKSAtPiBDb2xvdXIgeyBHcmVlbiB9XG5cbi8vIEEgY2xvc3VyZSB3aXRoIGEgZGVjbGFyZWQgcmV0dXJuIHR5cGUgZ2l2ZXMgaXRzIGJvZHkgYW4gZXhwZWN0ZWQgdHlwZSwgc28gYSBiYXJlXG4vLyB2YXJpYW50IGluc2lkZSBpdCByZXNvbHZlcyBub3JtYWxseS5cbmZ1biBhbm5vdGF0ZWRfY2xvc3VyZSgpIC0+IENvbG91ciB7XG4gICAgbGV0IGYgOj0gfHwgLT4gQ29sb3VyIHsgUmVkIH07XG4gICAgcmV0dXJuIGYoKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGM6IENvbG91ciA6PSBSZWQ7XG4gICAgYXNzZXJ0KHBhaW50KGMpID09IDEpO1xuICAgIGFzc2VydChwYWludChCbHVlKSA9PSAxKTtcblxuICAgIGxldCBnOiBDb2xvdXIgOj0gZmF2b3VyaXRlKCk7XG4gICAgYXNzZXJ0KHBhaW50KGcpID09IDEpO1xuXG4gICAgbGV0IHA6IFBlcmhhcHM8aTY0PiA6PSBTb21lIHsgdmFsdWUgPSA1IH07XG4gICAgbGV0IHE6IFBlcmhhcHM8aTY0PiA6PSBOb25lO1xuICAgIGFzc2VydChwYWludChhbm5vdGF0ZWRfY2xvc3VyZSgpKSA9PSAxKTtcblxuICAgIC8vIEFuIGVtcHR5IGFycmF5IGxpdGVyYWwgaXMgZGVmZXJyZWQgdG9vLCBhbmQgaXMgKmdlbnVpbmVseSogcG9seW1vcnBoaWMgLS0gdGhlXG4gICAgLy8gIzI4NSBjaGVjayBpcyBzY29wZWQgdG8gYmFyZSB2YXJpYW50cyBwcmVjaXNlbHkgc28gdGhpcyBrZWVwcyB3b3JraW5nLlxuICAgIGxldCBtayA6PSB8fCB7IFtdIH07XG4gICAgbGV0IGludHM6IGk2NFtdIDo9IG1rKCk7XG4gICAgbGV0IHN0cnM6IFN0cmluZ1tdIDo9IG1rKCk7XG4gICAgYXNzZXJ0KGludHMubGVuKCkgPT0gMCk7XG4gICAgYXNzZXJ0KHN0cnMubGVuKCkgPT0gMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9lbnVtcy80Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCIsIm5hbWUiOiI0Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-2}

An in-scope binding of the same name takes precedence over a bare enum variant in
expression position.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCIsInNvdXJjZSI6ImVudW0gQ29sb3VyIHsgUmVkLCBHcmVlbiwgQmx1ZSB9XG5cbnN0cnVjdCBIb2xkZXIge1xuICAgIGNvbG91cjogQ29sb3VyLFxuICAgIG1heWJlOiBQZXJoYXBzPGk2ND4sXG4gICAgbm90aGluZzogUGVyaGFwczxpNjQ+LFxuICAgIG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+LFxuICAgIGVycjogUmVzdWx0PGk2NCwgU3RyaW5nPixcbn1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gMSxcbiAgICAgICAgR3JlZW4gPT4gMixcbiAgICAgICAgQmx1ZSA9PiAzLFxuICAgIH1cbn1cblxuZnVuIGZhdm91cml0ZSgpIC0+IENvbG91ciB7XG4gICAgR3JlZW5cbn1cblxuZnVuIHNoYWRvdyhSZWQ6IGk2NCkgLT4gaTY0IHtcbiAgICByZXR1cm4gUmVkO1xufVxuXG5mdW4gdW53cmFwX3Jlc3VsdChyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+KSAtPiBpNjQge1xuICAgIG1hdGNoIChyKSB7XG4gICAgICAgIE9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjOiBDb2xvdXIgOj0gUmVkO1xuICAgIGxldCBjMjogQ29sb3VyIDo9IFJlZCB7fTtcbiAgICBhc3NlcnQocGFpbnQoYykgPT0gMSk7XG4gICAgYXNzZXJ0KHBhaW50KGMyKSA9PSAxKTtcbiAgICBhc3NlcnQocGFpbnQoQmx1ZSkgPT0gMyk7XG4gICAgYXNzZXJ0KHBhaW50KGZhdm91cml0ZSgpKSA9PSAyKTtcblxuICAgIGxldCBob2xkZXIgOj0gSG9sZGVyIHtcbiAgICAgICAgY29sb3VyID0gQmx1ZSxcbiAgICAgICAgbWF5YmUgPSBTb21lIHsgdmFsdWUgPSA1IH0sXG4gICAgICAgIG5vdGhpbmcgPSBOb25lLFxuICAgICAgICBvayA9IE9rIHsgdmFsdWUgPSA5IH0sXG4gICAgICAgIGVyciA9IEVyciB7IGVycm9yID0gXCJiYWRcIiB9LFxuICAgIH07XG5cbiAgICBhc3NlcnQocGFpbnQoaG9sZGVyLmNvbG91cikgPT0gMyk7XG4gICAgYXNzZXJ0KHNoYWRvdyg3KSA9PSA3KTtcblxuICAgIG1hdGNoIChob2xkZXIubWF5YmUpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxuXG4gICAgbWF0Y2ggKGhvbGRlci5ub3RoaW5nKSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KHRydWUpLFxuICAgIH1cblxuICAgIGFzc2VydCh1bndyYXBfcmVzdWx0KGhvbGRlci5vaykgPT0gOSk7XG4gICAgYXNzZXJ0KHVud3JhcF9yZXN1bHQoaG9sZGVyLmVycikgPT0gLTEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvNDFfdW5xdWFsaWZpZWRfdmFyaWFudF9jb25zdHJ1Y3RvcnMubXRsIiwibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-3}

Expected types from an annotation, return type, monomorphic call parameter, or
struct-literal field may direct bare-variant resolution.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCIsInNvdXJjZSI6ImVudW0gQ29sb3VyIHsgUmVkLCBHcmVlbiwgQmx1ZSB9XG5cbnN0cnVjdCBIb2xkZXIge1xuICAgIGNvbG91cjogQ29sb3VyLFxuICAgIG1heWJlOiBQZXJoYXBzPGk2ND4sXG4gICAgbm90aGluZzogUGVyaGFwczxpNjQ+LFxuICAgIG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+LFxuICAgIGVycjogUmVzdWx0PGk2NCwgU3RyaW5nPixcbn1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gMSxcbiAgICAgICAgR3JlZW4gPT4gMixcbiAgICAgICAgQmx1ZSA9PiAzLFxuICAgIH1cbn1cblxuZnVuIGZhdm91cml0ZSgpIC0+IENvbG91ciB7XG4gICAgR3JlZW5cbn1cblxuZnVuIHNoYWRvdyhSZWQ6IGk2NCkgLT4gaTY0IHtcbiAgICByZXR1cm4gUmVkO1xufVxuXG5mdW4gdW53cmFwX3Jlc3VsdChyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+KSAtPiBpNjQge1xuICAgIG1hdGNoIChyKSB7XG4gICAgICAgIE9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjOiBDb2xvdXIgOj0gUmVkO1xuICAgIGxldCBjMjogQ29sb3VyIDo9IFJlZCB7fTtcbiAgICBhc3NlcnQocGFpbnQoYykgPT0gMSk7XG4gICAgYXNzZXJ0KHBhaW50KGMyKSA9PSAxKTtcbiAgICBhc3NlcnQocGFpbnQoQmx1ZSkgPT0gMyk7XG4gICAgYXNzZXJ0KHBhaW50KGZhdm91cml0ZSgpKSA9PSAyKTtcblxuICAgIGxldCBob2xkZXIgOj0gSG9sZGVyIHtcbiAgICAgICAgY29sb3VyID0gQmx1ZSxcbiAgICAgICAgbWF5YmUgPSBTb21lIHsgdmFsdWUgPSA1IH0sXG4gICAgICAgIG5vdGhpbmcgPSBOb25lLFxuICAgICAgICBvayA9IE9rIHsgdmFsdWUgPSA5IH0sXG4gICAgICAgIGVyciA9IEVyciB7IGVycm9yID0gXCJiYWRcIiB9LFxuICAgIH07XG5cbiAgICBhc3NlcnQocGFpbnQoaG9sZGVyLmNvbG91cikgPT0gMyk7XG4gICAgYXNzZXJ0KHNoYWRvdyg3KSA9PSA3KTtcblxuICAgIG1hdGNoIChob2xkZXIubWF5YmUpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxuXG4gICAgbWF0Y2ggKGhvbGRlci5ub3RoaW5nKSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KHRydWUpLFxuICAgIH1cblxuICAgIGFzc2VydCh1bndyYXBfcmVzdWx0KGhvbGRlci5vaykgPT0gOSk7XG4gICAgYXNzZXJ0KHVud3JhcF9yZXN1bHQoaG9sZGVyLmVycikgPT0gLTEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvNDFfdW5xdWFsaWZpZWRfdmFyaWFudF9jb25zdHJ1Y3RvcnMubXRsIiwibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQyX3ZhcmlhbnRfZGVmZXJyYWxfcmVzb2x2ZXMubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMyODUncyBjaGVjayBtdXN0IG5vdCBmaXJlIG9uIGEgZGVmZXJyYWwgdGhhdCAqZG9lcyogcmVzb2x2ZSwgYXQgYW55IG9mIHRoZVxuLy8gcG9zaXRpb25zIFJGQy0wMTExIHN1cHBvcnRzLCBhbmQgbXVzdCBsZWF2ZSBnZW51aW5lbHkgcG9seW1vcnBoaWMgZGVmZXJyYWxzIGFsb25lLlxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbmZ1biBmYXZvdXJpdGUoKSAtPiBDb2xvdXIgeyBHcmVlbiB9XG5cbi8vIEEgY2xvc3VyZSB3aXRoIGEgZGVjbGFyZWQgcmV0dXJuIHR5cGUgZ2l2ZXMgaXRzIGJvZHkgYW4gZXhwZWN0ZWQgdHlwZSwgc28gYSBiYXJlXG4vLyB2YXJpYW50IGluc2lkZSBpdCByZXNvbHZlcyBub3JtYWxseS5cbmZ1biBhbm5vdGF0ZWRfY2xvc3VyZSgpIC0+IENvbG91ciB7XG4gICAgbGV0IGYgOj0gfHwgLT4gQ29sb3VyIHsgUmVkIH07XG4gICAgcmV0dXJuIGYoKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGM6IENvbG91ciA6PSBSZWQ7XG4gICAgYXNzZXJ0KHBhaW50KGMpID09IDEpO1xuICAgIGFzc2VydChwYWludChCbHVlKSA9PSAxKTtcblxuICAgIGxldCBnOiBDb2xvdXIgOj0gZmF2b3VyaXRlKCk7XG4gICAgYXNzZXJ0KHBhaW50KGcpID09IDEpO1xuXG4gICAgbGV0IHA6IFBlcmhhcHM8aTY0PiA6PSBTb21lIHsgdmFsdWUgPSA1IH07XG4gICAgbGV0IHE6IFBlcmhhcHM8aTY0PiA6PSBOb25lO1xuICAgIGFzc2VydChwYWludChhbm5vdGF0ZWRfY2xvc3VyZSgpKSA9PSAxKTtcblxuICAgIC8vIEFuIGVtcHR5IGFycmF5IGxpdGVyYWwgaXMgZGVmZXJyZWQgdG9vLCBhbmQgaXMgKmdlbnVpbmVseSogcG9seW1vcnBoaWMgLS0gdGhlXG4gICAgLy8gIzI4NSBjaGVjayBpcyBzY29wZWQgdG8gYmFyZSB2YXJpYW50cyBwcmVjaXNlbHkgc28gdGhpcyBrZWVwcyB3b3JraW5nLlxuICAgIGxldCBtayA6PSB8fCB7IFtdIH07XG4gICAgbGV0IGludHM6IGk2NFtdIDo9IG1rKCk7XG4gICAgbGV0IHN0cnM6IFN0cmluZ1tdIDo9IG1rKCk7XG4gICAgYXNzZXJ0KGludHMubGVuKCkgPT0gMCk7XG4gICAgYXNzZXJ0KHN0cnMubGVuKCkgPT0gMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9lbnVtcy80Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCIsIm5hbWUiOiI0Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.unqualified-variant-constructors.legality-4}

Without an expected enum type, a bare variant does not resolve by searching other enums;
the program must qualify or ascribe it.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAyIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjgiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTZfbmVnXzEyX3VucmVzb2x2ZWRfdmFyaWFudF9kZWZlcnJhbC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzI4NTogYSBiYXJlIHZhcmlhbnQgdGhhdCBuZXZlciByZXNvbHZlcyBtdXN0IGJlIHJlcG9ydGVkLCBub3Qgc2lsZW50bHlcbi8vIGFjY2VwdGVkLiBQYXNzIDEgZGVmZXJzIGl0IChSRkMtMDExMSBcdTAwYTczLjEpIGFuZCBvbmx5IHBhc3MgMiByZXNvbHZlcyBpdCBhZ2FpbnN0IGFuXG4vLyBleHBlY3RlZCB0eXBlIC0tIGJ1dCBhbiB1bmNhbGxlZCBjbG9zdXJlJ3MgYm9keSBpcyBuZXZlciBjb25zdHJ1Y3RlZCwgc28gbm8gZXhwZWN0ZWRcbi8vIHR5cGUgZXZlciBhcnJpdmVzIGFuZCBub3RoaW5nIHVzZWQgdG8gbm90aWNlLiBDaGVja2VkIGFmdGVyIHRoZSBmaW5hbCBzb2x2ZSBpbnN0ZWFkLlxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGYgOj0gfHwgeyBSZWQgfTsgLy8gRVJST1JbVDAwMDJdXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9lbnVtcy9zdGFnZTZfbmVnXzEyX3VucmVzb2x2ZWRfdmFyaWFudF9kZWZlcnJhbC5tdGwiLCJuYW1lIjoic3RhZ2U2X25lZ18xMl91bnJlc29sdmVkX3ZhcmlhbnRfZGVmZXJyYWwubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Unqualified variant patterns

> **Since v0.11.0 (RFC-0107).**

A match arm may name an enum variant without its `Enum::` prefix when the variant
resolves unambiguously against the scrutinee's known enum type. The candidate enum is
*only* the scrutinee's own type — this is type-directed resolution, not a lexical import
of variant names — so there is no cross-enum collision to resolve:

```metel
enum Colour { Red, Green, Blue }

fun name(c: Colour) -> String {
    match (c) {
        Red   => "red",
        Green => "green",
        Blue  => "blue",
    }
}
```

Fieldful variants may also be written bare:

```metel
fun unwrap_or_zero(v: Perhaps<i64>) -> i64 {
    match (v) {
        Some { value } => value,
        None           => 0,
    }
}
```

Resolution happens during type-checking, against the scrutinee's concrete type. If that
type is not a known enum at the point of matching (for example an abstract, aspect-bounded
type parameter inside a generic function), a bare identifier is an ordinary binding, as
before. A bare identifier that exactly names a no-field variant of the scrutinee's enum is
*always* the variant, never a fresh binding — use `_` or a differently-named binding for a
catch-all. The fully-qualified form (`Colour::Red`) remains valid everywhere; qualification
is optional, not removed.

### Struct patterns

> **Since v0.13.0.**

A named struct's fields may be destructured directly in a match arm, the same
bare-field syntax a struct literal uses:

```metel
struct Point { x: i64, y: i64 }

fun magnitude_squared(p: Point) -> i64 {
    match (p) {
        Point { x, y } => x * x + y * y,
    }
}
```

[Naming every field is required unless the pattern ends in `..`](#spec.expressions.struct-patterns.legality-1), which
matches the struct against any value of that type regardless of the fields it doesn't
name:

```metel
struct Token { kind: i64, span: i64, offset: i64 }

fun kind_and_span(t: Token) -> i64 {
    match (t) {
        Token { kind, span, .. } => kind + span,
    }
}
```

A field's own visibility applies the same way it does to ordinary field access — see
[Visibility](modules.md#visibility). An external pattern (outside the struct's declaring
module) that names a private field is a `T0009` visibility error; the field must be
omitted, which requires `..`.

A struct pattern's sub-patterns are always plain field bindings — there is no
`field: subpattern` form for matching a field's own value against something other than a
bare name. An unguarded struct-pattern arm is exhaustive for its struct type on its own:
a struct has exactly one shape, so naming every field (or every field plus `..`) always
covers it.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.struct-patterns.legality-1}

A struct pattern with no trailing `..` must name every field of the struct; one that
ends in `..` may name any subset, including none.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0cnVjdF9wYXR0ZXJuX21hdGNoZXNfYWxsX2ZpZWxkcy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgUG9pbnQgeyB4OiBpNjQsIHk6IGk2NCB9XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAzLCB5ID0gNCB9O1xuICAgIG1hdGNoIChwKSB7XG4gICAgICAgIFBvaW50IHsgeCwgeSB9ID0+IHggKyB5LFxuICAgIH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RydWN0X3BhdHRlcm5fbWF0Y2hlc19hbGxfZmllbGRzLm10bCIsIm5hbWUiOiJzdHJ1Y3RfcGF0dGVybl9tYXRjaGVzX2FsbF9maWVsZHMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdHJ1Y3RfcGF0dGVybl9taXNzaW5nX2ZpZWxkX3dpdGhvdXRfcmVzdF9pc190MDAwMS5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVG9rZW4geyBraW5kOiBpNjQsIHNwYW46IGk2NCwgb2Zmc2V0OiBpNjQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdCA6PSBUb2tlbiB7IGtpbmQgPSAxLCBzcGFuID0gMiwgb2Zmc2V0ID0gMyB9O1xuICAgIG1hdGNoICh0KSB7XG4gICAgICAgIFRva2VuIHsga2luZCwgc3BhbiB9ID0+IHByaW50bG4oa2luZCArIHNwYW4pLFxuICAgIH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RydWN0X3BhdHRlcm5fbWlzc2luZ19maWVsZF93aXRob3V0X3Jlc3RfaXNfdDAwMDEubXRsIiwibmFtZSI6InN0cnVjdF9wYXR0ZXJuX21pc3NpbmdfZmllbGRfd2l0aG91dF9yZXN0X2lzX3QwMDAxLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0cnVjdF9wYXR0ZXJuX3Jlc3Rfb21pdHNfcmVtYWluaW5nX2ZpZWxkcy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVG9rZW4geyBraW5kOiBpNjQsIHNwYW46IGk2NCwgb2Zmc2V0OiBpNjQgfVxuXG5mdW4gbWFpbigpIC0+IGk2NCB7XG4gICAgbGV0IHQgOj0gVG9rZW4geyBraW5kID0gMSwgc3BhbiA9IDIsIG9mZnNldCA9IDMgfTtcbiAgICBtYXRjaCAodCkge1xuICAgICAgICBUb2tlbiB7IGtpbmQsIHNwYW4sIC4uIH0gPT4ga2luZCArIHNwYW4sXG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvc3RydWN0cy9zdHJ1Y3RfcGF0dGVybl9yZXN0X29taXRzX3JlbWFpbmluZ19maWVsZHMubXRsIiwibmFtZSI6InN0cnVjdF9wYXR0ZXJuX3Jlc3Rfb21pdHNfcmVtYWluaW5nX2ZpZWxkcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Matching through a reference

> **Since v0.11.0 (RFC-0108).**

A scrutinee of reference type (`&T`, `&var T`, and chains thereof) matches against `T`'s
own patterns — reference layers are peeled before pattern resolution, the same way field
access and method dispatch already auto-dereference:

```metel
enum Colour { Red, Green, Blue }

fun name(c: &Colour) -> String {
    match (c) {
        Colour::Red   => "red",
        Colour::Green => "green",
        Colour::Blue  => "blue",
    }
}
```

Bindings introduced by a pattern matched through a reference copy the referent, following
the ordinary type-directed copy rule (see [Types](types.md#reading-a-value-out-of-a-reference)).

Reference-transparency and unqualified variants compose — peeling happens first, so a bare
variant resolves against the referent's enum:

```metel
fun name(c: &Colour) -> String {
    match (c) {
        Red   => "red",     // c is peeled &Colour -> Colour, then Red resolves against Colour
        Green => "green",
        Blue  => "blue",
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-1}

A no-field enum variant may be written as a bare match pattern when it is a variant of
the scrutinee's known enum type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-2}

A fieldful enum variant may likewise omit its enum prefix in a match pattern.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-3}

Bare-variant pattern resolution is directed only by the scrutinee's concrete enum type;
when that type is not a known enum, the identifier remains an ordinary binding.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-4}

A bare variant tag is not a catch-all binding and therefore does not satisfy match
exhaustiveness for the enum's other variants.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA4IiwiY29sIjoiNSIsImNvbnRhaW5zIjoibm9uLWV4aGF1c3RpdmUgbWF0Y2giLCJsaW5lIjoiNiIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ18xN19iYXJlX3ZhcmlhbnRfaXNfbm90X2NhdGNoYWxsLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA3IFx1MDBhNzI6IGEgYmFyZSB2YXJpYW50IHRhZyBpcyByZXdyaXR0ZW4gYmVmb3JlIGV4aGF1c3RpdmVuZXNzIGNoZWNraW5nO1xuLy8gaXQgaXMgbm90IGEgY2F0Y2gtYWxsIGJpbmRpbmcuXG5lbnVtIENvbG91ciB7IFJlZCwgQmx1ZSB9XG5cbmZ1biBuYW1lKGM6IENvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gXCJyZWRcIixcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2VudW1zL25lZ18xN19iYXJlX3ZhcmlhbnRfaXNfbm90X2NhdGNoYWxsLm10bCIsIm5hbWUiOiJuZWdfMTdfYmFyZV92YXJpYW50X2lzX25vdF9jYXRjaGFsbC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-5}

When a bare identifier exactly names a no-field variant of the scrutinee enum, it is the
variant rather than a fresh binding; `_` or another name is required for a catch-all.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-6}

The fully qualified enum-variant pattern remains valid wherever its bare spelling is
valid.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.unqualified-variant-patterns.legality-7}

`None` in pattern position is resolved by the ordinary unqualified-variant rule for a
`Perhaps<T>` scrutinee.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0107](../../rfcs/4-implemented/rfc-0107-unqualified-enum-variants-in-match-patterns.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwic291cmNlIjoiLy8gUkZDLTAxMDdcdTAwYTcxLCBSRkMtMDEwN1x1MDBhNzEuMSwgUkZDLTAxMDdcdTAwYTcxLjIsIFJGQy0wMTA3XHUwMGE3MS4zLCBSRkMtMDEwN1x1MDBhNzMsIGFuZCBSRkMtMDEwN1x1MDBhNzQ6XG4vLyBhIGJhcmUgdmFyaWFudCBuYW1lIGluIGEgbWF0Y2ggYXJtIHJlc29sdmVzIHR5cGUtZGlyZWN0ZWQgYWdhaW5zdCB0aGVcbi8vIHNjcnV0aW5lZSdzIG93biBlbnVtLiBDb3ZlcnMgbm8tZmllbGQgdmFyaWFudHMgKHBhcnNlZCBhcyBhIGJpbmRpbmcsIHJld3JpdHRlbiB0b1xuLy8gYW4gRW51bVZhcmlhbnQpLCBmaWVsZGZ1bCB2YXJpYW50cyAodGhlIG5ldyBiYXJlIGBWYXJpYW50IHsgZmllbGRzIH1gIGdyYW1tYXIpLCB0aGVcbi8vIHN0aWxsLXZhbGlkIHF1YWxpZmllZCBmb3JtLCBhbmQgYmFyZSBgTm9uZWAgXHUyMDE0IHdoaWNoIG5vIGxvbmdlciBoYXMgYSBkZWRpY2F0ZWRcbi8vIFBhdHRlcm46Ok5vbmUgbm9kZSBhbmQgaW5zdGVhZCBnb2VzIHRocm91Z2ggdGhpcyBzYW1lIGdlbmVyYWwgbWVjaGFuaXNtLlxuXG5lbnVtIENvbG91ciB7IFJlZCwgR3JlZW4sIEJsdWUgfVxuXG5mdW4gbmFtZShjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbmZ1biB1bndyYXBfb3IodjogUGVyaGFwczxpNjQ+LCBkOiBpNjQpIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHYpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIE5vbmUgICAgICAgICAgID0+IGQsXG4gICAgfVxufVxuXG5mdW4gcXVhbGlmaWVkX3N0aWxsX3dvcmtzKHY6IFBlcmhhcHM8aTY0PikgLT4gaTY0IHtcbiAgICBtYXRjaCAodikge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUGVyaGFwczo6Tm9uZSA9PiAtMSxcbiAgICB9XG59XG5cbi8vIEEgYmFyZSBpZGVudGlmaWVyIHRoYXQgbmFtZXMgbm8gdmFyaWFudCBvZiB0aGUgc2NydXRpbmVlJ3MgZW51bSBzdGF5cyBhbiBvcmRpbmFyeVxuLy8gYmluZGluZywgZXhhY3RseSBhcyBiZWZvcmUuXG5mdW4gYmluZGluZ19mYWxsYmFjayhjOiBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkID0+IFwicmVkXCIsXG4gICAgICAgIG90aGVyID0+IG5hbWUob3RoZXIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpSZWQpID09IFwicmVkXCIpO1xuICAgIGFzc2VydChuYW1lKENvbG91cjo6R3JlZW4pID09IFwiZ3JlZW5cIik7XG4gICAgYXNzZXJ0KG5hbWUoQ29sb3VyOjpCbHVlKSA9PSBcImJsdWVcIik7XG5cbiAgICBhc3NlcnQodW53cmFwX29yKFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IDUgfSwgMCkgPT0gNSk7XG4gICAgYXNzZXJ0KHVud3JhcF9vcihQZXJoYXBzOjpOb25lLCA5KSA9PSA5KTtcblxuICAgIGFzc2VydChxdWFsaWZpZWRfc3RpbGxfd29ya3MoUGVyaGFwczo6U29tZSB7IHZhbHVlID0gMyB9KSA9PSAzKTtcbiAgICBhc3NlcnQocXVhbGlmaWVkX3N0aWxsX3dvcmtzKFBlcmhhcHM6Ok5vbmUpID09IC0xKTtcblxuICAgIGFzc2VydChiaW5kaW5nX2ZhbGxiYWNrKENvbG91cjo6UmVkKSA9PSBcInJlZFwiKTtcbiAgICBhc3NlcnQoYmluZGluZ19mYWxsYmFjayhDb2xvdXI6OkJsdWUpID09IFwiYmx1ZVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2VudW1zLzQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIiwibmFtZSI6IjQwX3VucXVhbGlmaWVkX3ZhcmlhbnRfcGF0dGVybnMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-1}

A `&T`, `&var T`, or nested-reference scrutinee is accepted against the ordinary
patterns of its referent type `T`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-2}

Type checking a match uses the reference-peeled scrutinee type when checking its
patterns.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-3}

Exhaustiveness checking a match uses the reference-peeled scrutinee type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-1}

At runtime, matching through a reference compares the patterns with the fully dereferenced
scrutinee value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-2}

Bindings introduced while matching through a reference copy values from the peeled
referent under the ordinary type-directed copy rule.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.pattern-matching.matching-through-a-reference.dynamics-3}

For a reference scrutinee, `match reference` and `match *reference` compare patterns
against the same referent value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-4}

Reference peeling happens before unqualified-variant resolution, so a bare variant is
resolved against the referent's enum type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTA4OiBhIGAmVGAvYCZ2YXIgVGAgc2NydXRpbmVlIG1hdGNoZXMgYWdhaW5zdCB0aGUgcmVmZXJlbnQncyBvd24gcGF0dGVybnMgXHUyMDE0XG4vLyByZWZlcmVuY2UgbGF5ZXJzIGFyZSBwZWVsZWQgYmVmb3JlIHBhdHRlcm4gcmVzb2x1dGlvbiwgdGhlIHNhbWUgd2F5IGZpZWxkIGFjY2VzcyBhbmRcbi8vIG1ldGhvZCBkaXNwYXRjaCBhbHJlYWR5IGF1dG8tZGVyZWZlcmVuY2UuIEFsc28gY292ZXJzIGNvbXBvc2l0aW9uIHdpdGggUkZDLTAxMDc6XG4vLyBwZWVsaW5nIGhhcHBlbnMgZmlyc3QsIHNvIGEgYmFyZSB2YXJpYW50IHJlc29sdmVzIGFnYWluc3QgdGhlIHJlZmVyZW50J3MgZW51bS5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuXG5mdW4gbmFtZV9xdWFsaWZpZWQoYzogJkNvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG5hbWVfYmFyZShjOiAmQ29sb3VyKSAtPiBTdHJpbmcge1xuICAgIG1hdGNoIChjKSB7XG4gICAgICAgIFJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIEdyZWVuID0+IFwiZ3JlZW5cIixcbiAgICAgICAgQmx1ZSAgPT4gXCJibHVlXCIsXG4gICAgfVxufVxuXG5mdW4gbmFtZV9tdXQoYzogJnZhciBDb2xvdXIpIC0+IFN0cmluZyB7XG4gICAgbWF0Y2ggKGMpIHtcbiAgICAgICAgUmVkICAgPT4gXCJyZWRcIixcbiAgICAgICAgR3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBCbHVlICA9PiBcImJsdWVcIixcbiAgICB9XG59XG5cbi8vIEJpbmRpbmdzIGludHJvZHVjZWQgdGhyb3VnaCBhIHJlZmVyZW5jZS1tYXRjaGVkIHBhdHRlcm4gY29weSB0aGUgcmVmZXJlbnQuXG5mdW4gcGF5bG9hZCh2OiAmUGVyaGFwczxpNjQ+KSAtPiBpNjQge1xuICAgIG1hdGNoICh2KSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBOb25lICAgICAgICAgICA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjIDo9IENvbG91cjo6R3JlZW47XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZjKSA9PSBcImdyZWVuXCIpO1xuICAgIGFzc2VydChuYW1lX2JhcmUoJmMpID09IFwiZ3JlZW5cIik7XG5cbiAgICB2YXIgZCA6PSBDb2xvdXI6OkJsdWU7XG4gICAgYXNzZXJ0KG5hbWVfbXV0KCZ2YXIgZCkgPT0gXCJibHVlXCIpO1xuXG4gICAgbGV0IHNvbWU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH07XG4gICAgbGV0IG5vbmU6IFBlcmhhcHM8aTY0PiA6PSBQZXJoYXBzOjpOb25lO1xuICAgIGFzc2VydChwYXlsb2FkKCZzb21lKSA9PSA3KTtcbiAgICBhc3NlcnQocGF5bG9hZCgmbm9uZSkgPT0gLTEpO1xuXG4gICAgLy8gQSBub24tcmVmZXJlbmNlIHNjcnV0aW5lZSBpcyB1bmFmZmVjdGVkIGJ5IHRoZSBwZWVsLlxuICAgIGxldCByZWQgOj0gQ29sb3VyOjpSZWQ7XG4gICAgYXNzZXJ0KG5hbWVfcXVhbGlmaWVkKCZyZWQpID09IFwicmVkXCIpO1xuXG4gICAgLy8gTWF0Y2hpbmcgYSByZWZlcmVuY2UgdG8gYSBzdHJ1Y3Qgc3RpbGwgYmluZHMgYnkgdmFsdWUgdGhyb3VnaCB0aGUgcGVlbC5cbiAgICBsZXQgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCByOiAmUG9pbnQgOj0gJnA7XG4gICAgYXNzZXJ0KHIueCA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMTBfbWF0Y2hfdGhyb3VnaF9yZWZlcmVuY2UubXRsIiwibmFtZSI6IjEwX21hdGNoX3Rocm91Z2hfcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.pattern-matching.matching-through-a-reference.legality-5}

Reference transparency is limited to the match-scrutinee position and does not change
the types required in call arguments or other non-match contexts.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0108](../../rfcs/4-implemented/rfc-0108-reference-transparent-match-scrutinees.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjE4Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzEzX3JlZmVyZW5jZV9zY3J1dGluZWVfcGVlbF9kb2VzX25vdF9nZW5lcmFsaXplX3RvX2NhbGxfYXJncy5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDEwOCBcdTAwYTczOiByZWZlcmVuY2UtdHJhbnNwYXJlbmN5IGlzIHNjb3BlZCB0byBtYXRjaCBzY3J1dGluZWVzIG9ubHkuIEEgYCZDb2xvdXJgXG4vLyB2YWx1ZSB0aGF0IG1hdGNoZXMgZmluZSBhcyBhIHNjcnV0aW5lZSBkb2VzIG5vdCBzaWxlbnRseSB3aWRlbiB0byBgQ29sb3VyYCBpbiBhXG4vLyBjYWxsLWFyZ3VtZW50IHBvc2l0aW9uIC0tIHRoYXQgaXMgYW4gb3JkaW5hcnkgdHlwZSBtaXNtYXRjaCwgbm90IGEgcGVlbC5cblxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuZnVuIHRha2VzX2J5X3ZhbHVlKGM6IENvbG91cikgLT4gU3RyaW5nIHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBDb2xvdXI6OlJlZCAgID0+IFwicmVkXCIsXG4gICAgICAgIENvbG91cjo6R3JlZW4gPT4gXCJncmVlblwiLFxuICAgICAgICBDb2xvdXI6OkJsdWUgID0+IFwiYmx1ZVwiLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGMgOj0gQ29sb3VyOjpHcmVlbjtcbiAgICBsZXQgcjogJkNvbG91ciA6PSAmYztcbiAgICBwcmludGxuKHRha2VzX2J5X3ZhbHVlKHIpKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2VudW1zL25lZ18xM19yZWZlcmVuY2Vfc2NydXRpbmVlX3BlZWxfZG9lc19ub3RfZ2VuZXJhbGl6ZV90b19jYWxsX2FyZ3MubXRsIiwibmFtZSI6Im5lZ18xM19yZWZlcmVuY2Vfc2NydXRpbmVlX3BlZWxfZG9lc19ub3RfZ2VuZXJhbGl6ZV90b19jYWxsX2FyZ3MubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

---

## Control Flow

### If / Else

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

`if` is also an expression (both branches must produce the same type):

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

1. **Arm style must be consistent.** Both the `then` and `else` arms must use the same style — either both braced or both braceless. Mixing is a parse error.
2. **Dangling-else is forbidden.** If the outer body is braceless, the body expression must not itself be an `if–else`. Use braces on the outer body to resolve the ambiguity.
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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQ3X2JyYWNlbGVzc19pZi5tdGwiLCJzb3VyY2UiOiIvLyBCcmFjZWxlc3MgaWYgYm9keSBzeW50YXggKFJGQy0wMDIyKS5cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQnJhY2VsZXNzIGlmIGluIHN0YXRlbWVudCBwb3NpdGlvbiAobm8gZWxzZSkuXG4gICAgdmFyIHggOj0gMDtcbiAgICBpZiAodHJ1ZSkgeCA6PSAxO1xuICAgIGFzc2VydCh4ID09IDEpO1xuXG4gICAgLy8gQnJhY2VsZXNzIGlmIFx1MjAxNCBjb25kaXRpb24gZmFsc2UsIGJvZHkgbm90IGV4ZWN1dGVkLlxuICAgIGlmIChmYWxzZSkgeCA6PSA5OTtcbiAgICBhc3NlcnQoeCA9PSAxKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgaW4gZXhwcmVzc2lvbiBwb3NpdGlvbi5cbiAgICBsZXQgYSA6PSBpZiAodHJ1ZSkgMTAgZWxzZSAyMDtcbiAgICBhc3NlcnQoYSA9PSAxMCk7XG5cbiAgICBsZXQgYiA6PSBpZiAoZmFsc2UpIDEwIGVsc2UgMjA7XG4gICAgYXNzZXJ0KGIgPT0gMjApO1xuXG4gICAgLy8gTmVzdGVkIGJyYWNlbGVzczogaW5uZXIgaWYgaGFzIG5vIGVsc2UgXHUyMDE0IG9rLlxuICAgIHZhciBmbGFnIDo9IGZhbHNlO1xuICAgIGlmICh0cnVlKSBpZiAodHJ1ZSkgZmxhZyA6PSB0cnVlO1xuICAgIGFzc2VydChmbGFnKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgdXNlZCBhcyBhIGZ1bmN0aW9uIGFyZ3VtZW50LlxuICAgIGFzc2VydCgoaWYgKHRydWUpIDcgZWxzZSA4KSA9PSA3KTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBpbiBhIGxvb3AuXG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgd2hpbGUgKGkgPCA1KSB7XG4gICAgICAgIGlmIChpICUgMiA9PSAwKSBzdW0gOj0gc3VtICsgaTtcbiAgICAgICAgaSA6PSBpICsgMTtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSA2KTsgIC8vIDAgKyAyICsgNFxuXG4gICAgLy8gQnJhY2VsZXNzIGVsc2UtaWYgY2hhaW4uXG4gICAgbGV0IHYgOj0gMjtcbiAgICBsZXQgbGFiZWwgOj0gaWYgKHYgPT0gMSkgMTAwIGVsc2UgaWYgKHYgPT0gMikgMjAwIGVsc2UgMzAwO1xuICAgIGFzc2VydChsYWJlbCA9PSAyMDApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93LzQ3X2JyYWNlbGVzc19pZi5tdGwiLCJuYW1lIjoiNDdfYnJhY2VsZXNzX2lmLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-2}

A braceless `if` without `else` has type `Unit` and may occur wherever a `Unit`-typed
expression is accepted.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijg4X2JyYWNlbGVzc19pZl9ub19lbHNlX2luX2V4cHJlc3Npb25fcG9zaXRpb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwMjIgXHUwMGE3MiAoY29ycmVjdGVkIG1ldGVsLWNvcmUjNzUwKTogYSBicmFjZWxlc3MgYGlmYCB3aXRoIG5vIGBlbHNlYCBoYXNcbi8vIHR5cGUgVW5pdCwgYW5kIGlzIG5vdCByZXN0cmljdGVkIHRvIHN0YXRlbWVudCBwb3NpdGlvbiAtLSBpdCdzIHVzYWJsZVxuLy8gYW55d2hlcmUgYSBVbml0LXR5cGVkIGV4cHJlc3Npb24gaXMsIGluY2x1ZGluZyBhIGBsZXRgIGJpbmRpbmcnc1xuLy8gaW5pdGlhbGl6ZXIuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgY2FsbHMgOj0gMDtcbiAgICBsZXQgY2FsbHNfcmVmOiAmdmFyIGk2NCA6PSAmdmFyIGNhbGxzO1xuICAgIGxldCB2YWx1ZSA6PSBpZiAodHJ1ZSkgKmNhbGxzX3JlZiArPSAxO1xuICAgIGFzc2VydChjYWxscyA9PSAxKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2NvbnRyb2xfZmxvdy84OF9icmFjZWxlc3NfaWZfbm9fZWxzZV9pbl9leHByZXNzaW9uX3Bvc2l0aW9uLm10bCIsIm5hbWUiOiI4OF9icmFjZWxlc3NfaWZfbm9fZWxzZV9pbl9leHByZXNzaW9uX3Bvc2l0aW9uLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-3}

A braceless `if`-`else` is an expression when its two branches have the same type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjQ3X2JyYWNlbGVzc19pZi5tdGwiLCJzb3VyY2UiOiIvLyBCcmFjZWxlc3MgaWYgYm9keSBzeW50YXggKFJGQy0wMDIyKS5cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQnJhY2VsZXNzIGlmIGluIHN0YXRlbWVudCBwb3NpdGlvbiAobm8gZWxzZSkuXG4gICAgdmFyIHggOj0gMDtcbiAgICBpZiAodHJ1ZSkgeCA6PSAxO1xuICAgIGFzc2VydCh4ID09IDEpO1xuXG4gICAgLy8gQnJhY2VsZXNzIGlmIFx1MjAxNCBjb25kaXRpb24gZmFsc2UsIGJvZHkgbm90IGV4ZWN1dGVkLlxuICAgIGlmIChmYWxzZSkgeCA6PSA5OTtcbiAgICBhc3NlcnQoeCA9PSAxKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgaW4gZXhwcmVzc2lvbiBwb3NpdGlvbi5cbiAgICBsZXQgYSA6PSBpZiAodHJ1ZSkgMTAgZWxzZSAyMDtcbiAgICBhc3NlcnQoYSA9PSAxMCk7XG5cbiAgICBsZXQgYiA6PSBpZiAoZmFsc2UpIDEwIGVsc2UgMjA7XG4gICAgYXNzZXJ0KGIgPT0gMjApO1xuXG4gICAgLy8gTmVzdGVkIGJyYWNlbGVzczogaW5uZXIgaWYgaGFzIG5vIGVsc2UgXHUyMDE0IG9rLlxuICAgIHZhciBmbGFnIDo9IGZhbHNlO1xuICAgIGlmICh0cnVlKSBpZiAodHJ1ZSkgZmxhZyA6PSB0cnVlO1xuICAgIGFzc2VydChmbGFnKTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZlx1MjAxM2Vsc2UgdXNlZCBhcyBhIGZ1bmN0aW9uIGFyZ3VtZW50LlxuICAgIGFzc2VydCgoaWYgKHRydWUpIDcgZWxzZSA4KSA9PSA3KTtcblxuICAgIC8vIEJyYWNlbGVzcyBpZiBpbiBhIGxvb3AuXG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgd2hpbGUgKGkgPCA1KSB7XG4gICAgICAgIGlmIChpICUgMiA9PSAwKSBzdW0gOj0gc3VtICsgaTtcbiAgICAgICAgaSA6PSBpICsgMTtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSA2KTsgIC8vIDAgKyAyICsgNFxuXG4gICAgLy8gQnJhY2VsZXNzIGVsc2UtaWYgY2hhaW4uXG4gICAgbGV0IHYgOj0gMjtcbiAgICBsZXQgbGFiZWwgOj0gaWYgKHYgPT0gMSkgMTAwIGVsc2UgaWYgKHYgPT0gMikgMjAwIGVsc2UgMzAwO1xuICAgIGFzc2VydChsYWJlbCA9PSAyMDApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93LzQ3X2JyYWNlbGVzc19pZi5tdGwiLCJuYW1lIjoiNDdfYnJhY2VsZXNzX2lmLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-4}

A braceless outer branch cannot contain an inner `if`-`else`; braces are required to
avoid dangling-`else` ambiguity.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImJyYWNlbGVzcyBpZiBib2R5IG1heSBub3QgY29udGFpbiBhbiBpZlx1MjAxM2Vsc2UgZXhwcmVzc2lvbiIsImxpbmUiOm51bGwsInN0YXR1cyI6InBhcnNlX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzE5X2JyYWNlbGVzc19pZl9kYW5nbGluZ19lbHNlLm10bCIsInNvdXJjZSI6Ii8vIFBBUlNFX0VSUk9SW2JyYWNlbGVzcyBpZiBib2R5IG1heSBub3QgY29udGFpbiBhbiBpZlx1MjAxM2Vsc2UgZXhwcmVzc2lvbl1cbi8vIE91dGVyIGJvZHkgaXMgYnJhY2VsZXNzIGFuZCBjb250YWlucyBhbiBpbm5lciBpZlx1MjAxM2Vsc2UgXHUyMDE0IGRhbmdsaW5nLWVsc2UgYW1iaWd1aXR5LlxuZnVuIG1haW4oKSB7XG4gICAgaWYgKHRydWUpIGlmIChmYWxzZSkgMSBlbHNlIDI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvbmVnXzE5X2JyYWNlbGVzc19pZl9kYW5nbGluZ19lbHNlLm10bCIsIm5hbWUiOiJuZWdfMTlfYnJhY2VsZXNzX2lmX2RhbmdsaW5nX2Vsc2UubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.control-flow.if-else.legality-5}

The `then` and `else` branches of an `if`-`else` must use the same body style: both
braced or both braceless.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0022](../../rfcs/4-implemented/rfc-0022-braceless-if-body-syntax.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6Im1pc21hdGNoZWQgaWYgYXJtIHN0eWxlcyIsImxpbmUiOm51bGwsInN0YXR1cyI6InBhcnNlX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzIwX2JyYWNlbGVzc19pZl9taXhlZF9hcm1zLm10bCIsInNvdXJjZSI6Ii8vIFBBUlNFX0VSUk9SW21pc21hdGNoZWQgaWYgYXJtIHN0eWxlc11cbi8vIHRoZW4gYnJhbmNoIHVzZXMgYnJhY2VzLCBlbHNlIGJyYW5jaCBkb2VzIG5vdC5cbmZ1biBtYWluKCkge1xuICAgIGxldCB4IDo9IGlmICh0cnVlKSB7IDEgfSBlbHNlIDI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvbmVnXzIwX2JyYWNlbGVzc19pZl9taXhlZF9hcm1zLm10bCIsIm5hbWUiOiJuZWdfMjBfYnJhY2VsZXNzX2lmX21peGVkX2FybXMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### While

```metel
fun main() -> i64 {
    var n := 3;
    var total := 0;
    while (n > 0) {
        total += n;
        n -= 1;
    }
    return total;
}
```

### For

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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE2X2Zvcl9sb29wLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEJhc2ljIGNvdW50aW5nLlxuICAgIHZhciBzdW0gOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCA1OyBpICs9IDEpIHsgc3VtICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtID09IDEwKTtcbiAgICAvLyBCcmVhayBleGl0cyB0aGUgbG9vcC5cbiAgICB2YXIgY291bnQgOj0gMDtcbiAgICBmb3IgKHZhciBpIDo9IDA7IGkgPCAxMDA7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSA1KSB7IGJyZWFrOyB9XG4gICAgICAgIGNvdW50ICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjb3VudCA9PSA1KTtcbiAgICAvLyBDb250aW51ZSBzdGlsbCBleGVjdXRlcyB0aGUgc3RlcCBleHByZXNzaW9uLlxuICAgIHZhciBjMiA6PSAwO1xuICAgIGZvciAodmFyIGkgOj0gMDsgaSA8IDU7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA9PSAyKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIGMyICs9IDE7XG4gICAgfVxuICAgIGFzc2VydChjMiA9PSA0KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2NvbnRyb2xfZmxvdy8xNl9mb3JfbG9vcC5tdGwiLCJuYW1lIjoiMTZfZm9yX2xvb3AubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### For-In

> **Availability:** Array and range iteration since v0.1.0. User-defined `Iterable<T>` implementations since v0.4.0.

[`for-in` works on any type implementing the `Iterable<T>` aspect](runtime.md#spec.runtime.built-in-aspects.iterable-t.legality-1). The loop variable
receives type `T`. `T[]`, `[T; N]` (array and fixed-size array), and `Range` (produced by
`..` and `..=`) implement `Iterable<T>` by default. A `T[]` loop binding denotes an
element of an immutable borrowed view: with move checking enabled, a non-`Copy` binding
may be read or borrowed but not consumed. User-defined types can be made iterable by
implementing `Iterable<T>`. The loop binding is immutable by default and [may be made
loop-locally mutable with `var`](#spec.expressions.control-flow.for-in.legality-1):

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE3X2Zvcl9pbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICAvLyBBcnJheSBpdGVyYXRpb24uXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMF07XG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIGZvciAoeCBpbiBhcnIpIHsgc3VtICs9IHg7IH1cbiAgICBhc3NlcnQoc3VtID09IDYwKTtcbiAgICAvLyBFeGNsdXNpdmUgcmFuZ2UuXG4gICAgdmFyIHN1bTIgOj0gMDtcbiAgICBmb3IgKGkgaW4gMC4uNSkgeyBzdW0yICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtMiA9PSAxMCk7XG4gICAgLy8gSW5jbHVzaXZlIHJhbmdlLlxuICAgIHZhciBzdW0zIDo9IDA7XG4gICAgZm9yIChpIGluIDEuLj00KSB7IHN1bTMgKz0gaTsgfVxuICAgIGFzc2VydChzdW0zID09IDEwKTtcbiAgICAvLyBNdXRhYmxlIGZvci1pbiBiaW5kaW5nIG1heSBiZSByZWJvdW5kIGxvY2FsbHkuXG4gICAgdmFyIGJ1bXBlZCA6PSAwO1xuICAgIGZvciAodmFyIHggaW4gWzEsIDIsIDNdKSB7XG4gICAgICAgIHggKz0gMTtcbiAgICAgICAgYnVtcGVkICs9IHg7XG4gICAgfVxuICAgIGFzc2VydChidW1wZWQgPT0gOSk7XG4gICAgLy8gQnJlYWsgc3RvcHMgZWFybHkuXG4gICAgdmFyIHN1bTQgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDMsIDQsIDVdKSB7XG4gICAgICAgIGlmICh4ID09IDMpIHsgYnJlYWs7IH1cbiAgICAgICAgc3VtNCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQoc3VtNCA9PSAzKTtcbiAgICAvLyBDb250aW51ZSBza2lwcyB0aGUgY3VycmVudCBlbGVtZW50LlxuICAgIHZhciBzdW01IDo9IDA7XG4gICAgZm9yICh4IGluIFsxLCAyLCAzLCA0LCA1XSkge1xuICAgICAgICBpZiAoeCA9PSAzKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIHN1bTUgKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bTUgPT0gMTIpO1xuICAgIC8vIEJpbmRpbmcgZG9lcyBub3QgbGVhayBpbnRvIHRoZSBvdXRlciBzY29wZS5cbiAgICBsZXQgeCA6PSA0MjtcbiAgICB2YXIgaW5uZXIgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDNdKSB7IGlubmVyICs9IHg7IH1cbiAgICBhc3NlcnQoaW5uZXIgPT0gNik7XG4gICAgYXNzZXJ0KHggICA9PSA0Mik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTdfZm9yX2luLm10bCIsIm5hbWUiOiIxN19mb3JfaW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.for-in.dynamics-1}

Reassigning a `var` `for-in` binding changes only that iteration's loop-local binding and
does not write the replacement value back into the iterated source.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE3X2Zvcl9pbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICAvLyBBcnJheSBpdGVyYXRpb24uXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMF07XG4gICAgdmFyIHN1bSA6PSAwO1xuICAgIGZvciAoeCBpbiBhcnIpIHsgc3VtICs9IHg7IH1cbiAgICBhc3NlcnQoc3VtID09IDYwKTtcbiAgICAvLyBFeGNsdXNpdmUgcmFuZ2UuXG4gICAgdmFyIHN1bTIgOj0gMDtcbiAgICBmb3IgKGkgaW4gMC4uNSkgeyBzdW0yICs9IGk7IH1cbiAgICBhc3NlcnQoc3VtMiA9PSAxMCk7XG4gICAgLy8gSW5jbHVzaXZlIHJhbmdlLlxuICAgIHZhciBzdW0zIDo9IDA7XG4gICAgZm9yIChpIGluIDEuLj00KSB7IHN1bTMgKz0gaTsgfVxuICAgIGFzc2VydChzdW0zID09IDEwKTtcbiAgICAvLyBNdXRhYmxlIGZvci1pbiBiaW5kaW5nIG1heSBiZSByZWJvdW5kIGxvY2FsbHkuXG4gICAgdmFyIGJ1bXBlZCA6PSAwO1xuICAgIGZvciAodmFyIHggaW4gWzEsIDIsIDNdKSB7XG4gICAgICAgIHggKz0gMTtcbiAgICAgICAgYnVtcGVkICs9IHg7XG4gICAgfVxuICAgIGFzc2VydChidW1wZWQgPT0gOSk7XG4gICAgLy8gQnJlYWsgc3RvcHMgZWFybHkuXG4gICAgdmFyIHN1bTQgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDMsIDQsIDVdKSB7XG4gICAgICAgIGlmICh4ID09IDMpIHsgYnJlYWs7IH1cbiAgICAgICAgc3VtNCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQoc3VtNCA9PSAzKTtcbiAgICAvLyBDb250aW51ZSBza2lwcyB0aGUgY3VycmVudCBlbGVtZW50LlxuICAgIHZhciBzdW01IDo9IDA7XG4gICAgZm9yICh4IGluIFsxLCAyLCAzLCA0LCA1XSkge1xuICAgICAgICBpZiAoeCA9PSAzKSB7IGNvbnRpbnVlOyB9XG4gICAgICAgIHN1bTUgKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bTUgPT0gMTIpO1xuICAgIC8vIEJpbmRpbmcgZG9lcyBub3QgbGVhayBpbnRvIHRoZSBvdXRlciBzY29wZS5cbiAgICBsZXQgeCA6PSA0MjtcbiAgICB2YXIgaW5uZXIgOj0gMDtcbiAgICBmb3IgKHggaW4gWzEsIDIsIDNdKSB7IGlubmVyICs9IHg7IH1cbiAgICBhc3NlcnQoaW5uZXIgPT0gNik7XG4gICAgYXNzZXJ0KHggICA9PSA0Mik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTdfZm9yX2luLm10bCIsIm5hbWUiOiIxN19mb3JfaW4ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### References

> **Availability:** Since v0.10.0.

References provide explicit aliasing.

```metel
fun main() -> i64 {
    var n := 1;
    let p: &var i64 := &var n;
    *p := 4;   // write-through: mutate the referent via explicit deref
    return p; // type-directed copy: reads the value out at `return`
}
```

Rules:

- `&expr` creates a shared reference `&T` where `expr` is an addressable lvalue
- `&var x` creates an exclusive reference `&var T` where `x` is a `var` addressable lvalue
- `*p` dereferences a reference — reading the referent, or, as an assignment target
  (`*p = v`), writing through to it (see "Dereference" below)
- reading a plain value out of a reference with no field/method involved can also go
  through type-directed copy (see
  [Types — Reading a value out of a reference](types.md#reading-a-value-out-of-a-reference)),
  and field access, index, and method dispatch go through auto-deref (below)
- assigning to a reference-typed binding (`p = v`) **rebinds** it, like any other type;
  `*p = v` is the spelling that writes through

Addressable places for both `&` and `&var` include named bindings (`x`), struct field access (`s.field`), tuple element access (`t.0`), array indexing (`arr[i]`), a dereference (`*p` — so `&*p` is a reborrow that shares the referent's storage), and chains thereof (`nested.outer.field`, `t.1.0`).

> **Since v0.12.0: `&<rvalue>` / `&var <rvalue>` — temporary lifetime extension.**
> Neither `&expr` nor `&var expr` requires `expr` to be an addressable place anymore: a
> literal, a call result, a struct or enum construction, or any other non-addressable
> expression is materialized into a fresh, independent cell and referenced directly
> (matching Rust and C++: `foo(&Vec::new())`, `foo(&var Vec::new())` — both need no
> intermediate binding). Sound for both forms — nothing outside the expression can ever
> alias the cell, so a mutable reference to it can never conflict with anything else.
>
> ```metel
> fun takes_ref(l: &List<i64>) -> i64 { l.len() }
> fun bump(x: &var i64) -> i64 { *x := *x + 1; *x }
> fun main() -> i64 {
>     let a := takes_ref(&List::from([1, 2, 3]));   // no `let` needed for the argument
>     let b := bump(&var 41);                        // &var works on a temporary too
>     return a + b;
> }
> ```

`&var` requires the operand to be a `var` binding — applying it to a plain `let` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)). `&var` on a lvalue path ([a struct field](#spec.expressions.references.dynamics-1), [tuple element](#spec.expressions.references.dynamics-2), [array element](#spec.expressions.references.dynamics-3), or [chain of projections](#spec.expressions.references.dynamics-4)) produces a true exclusive reference with write-back semantics, matching `&var` on a named binding exactly — writes through it propagate to the original storage location (RFC-0045, already implemented; this section previously described `&var struct.field` as a non-propagating snapshot, which was the *pre*-RFC-0045 behavior and had never been updated to match). `&` on a field or element also aliases the original storage through the same path machinery, so later writes to the binding remain visible through the shared reference; it is still read-only, so writing through `&T` remains rejected. Reborrowing preserves this: `&*r` shares whatever storage `r` names, and reborrowing a `&var T` as `&T` downgrades to shared. The reverse is rejected — `&var *r` where `r: &T` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)), since a shared reference never grants write access.

Tuple elements are assignable like struct fields and array elements — `t.0 = v`, `t.0 += v`,
and nested or chained forms (`s.pair.0`, `t.1.0`), including through a `&var` reference. An
out-of-range index is a type error ([T0003](../error-codes.md#t0003--undefined-name)), and a
shared `&` grants no write access ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)).

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-1}

Evaluating `&var value.field` creates an exclusive reference to that field. A write through
the reference updates the corresponding field in `value`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-2}

Evaluating `&var value.n` creates an exclusive reference to tuple element `n`. A write
through the reference updates that element and leaves the other tuple elements unchanged.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-3}

Evaluating `&var values[index]` creates an exclusive reference to the selected array
element. A write through the reference is observable through subsequent indexing.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-4}

Evaluating `&var` over a chain of addressable projections creates an exclusive reference
to the chain's leaf storage. A write through the reference updates that original leaf.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0045](../../rfcs/4-implemented/rfc-0045-mut-address-of-lvalue-paths.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

#### Dereference

> **Changed in v0.11.0 (RFC-0110): `*p` added; assignment to a reference-typed binding now rebinds it, use `*p = v` to write through.**

`*expr` dereferences a `&T`/`&var T`. As an expression it reads the referent; as an
assignment target, `*p = v` writes through a `&var T`. Applying `*` to a non-reference is
a type error ([T0002](../error-codes.md#t0002--annotation-required)).

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
    p := &var b;   // repoint: p now refers to b (p is `var`) — a stays 1
    *p := 5;       // write-through: b becomes 5
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
    qp.y := 99;        // field write-through — no `*` needed
    var xs := [1, 2, 3];
    let xp: &var [i64; 3] := &var xs;
    xp[0] := 9;        // index write-through — no `*` needed
    return q.y + xs[0];
}
```

`*(obj.field) = v` and `obj.field = v` are synonyms; for a bare identifier target, `*p = v`
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
    p.value := 1;      // auto-deref field assign; the reference binding need not be var
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

Indexing, argument passing, and assignment remain ordinary reference operations — none of them are the value-extraction case (see `types.md`), so none require type-directed copy.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.references.dynamics-5}

Evaluating `&place` or `&var place` produces, respectively, a shared or exclusive
reference to the addressed storage; an exclusive reference can write through to that
same storage.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA0X3dyaXRlX3Rocm91Z2hfdGhpbl9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzEvXHUwMGE3Mzogd3JpdGUtdGhyb3VnaCBmb3IgYSB0aGluIHJlZmVyZW5jZSAoVmFsdWU6Ok11dFJlZmVyZW5jZSwgbm90IGFcbi8vIGZhdCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgZXZlcnkgZXhpc3RpbmcgZml4dHVyZSdzIHdyaXRlLXRocm91Z2ggY2FzZSBpcyBhXG4vLyBmaWVsZC90dXBsZS9hcnJheS1lbGVtZW50IHJlZmVyZW5jZTsgdGhpcyBjb3ZlcnMgYSBwbGFpbiBzY2FsYXIgYmluZGluZyBkaXJlY3RseSkuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgbiA6PSAxO1xuICAgIGxldCBwOiAmdmFyIGk2NCA6PSAmdmFyIG47XG4gICAgKnAgOj0gNDtcbiAgICBhc3NlcnQobiA9PSA0KTtcblxuICAgICpwICs9IDY7XG4gICAgYXNzZXJ0KG4gPT0gMTApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy8wNF93cml0ZV90aHJvdWdoX3RoaW5fcmVmZXJlbmNlLm10bCIsIm5hbWUiOiIwNF93cml0ZV90aHJvdWdoX3RoaW5fcmVmZXJlbmNlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-6}

Field access, field assignment, method dispatch, and calls through a reference
auto-dereference through every reference layer necessary to reach their receiver.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzM6IGF1dG8tZGVyZWYgZm9yIGZpZWxkIGFjY2Vzcy9tZXRob2QgZGlzcGF0Y2ggYWxyZWFkeSBjaGFpbnMgdGhyb3VnaFxuLy8gYXJiaXRyYXJ5IGRlcHRoIChcIiYmVCBkZXJlZnMgdGhyb3VnaCBib3RoIGxldmVsc1wiKSBpbmRlcGVuZGVudCBvZiByZWFkLWNvcHkgXHUyMDE0XG4vLyBjb25maXJtcyB0aGlzIHByZS1leGlzdGluZyBndWFyYW50ZWUgZXhwbGljaXRseSB1bmRlciB0aGUgbmV3ICZULyZ2YXIgVCBzeW50YXguXG5zdHJ1Y3QgQ291bnRlciB7IHZhbHVlOiBpNjQgfVxuXG5leHRlbmQgQ291bnRlciB7XG4gICAgZnVuIGdldCgmc2VsZikgLT4gaTY0IHtcbiAgICAgICAgc2VsZi52YWx1ZVxuICAgIH1cbiAgICBmdW4gYnVtcCgmdmFyIHNlbGYpIHtcbiAgICAgICAgc2VsZi52YWx1ZSArPSAxO1xuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIGMgOj0gQ291bnRlciB7IHZhbHVlID0gMSB9O1xuICAgIGxldCByOiAmdmFyIENvdW50ZXIgOj0gJnZhciBjO1xuICAgIGxldCBycjogJiZ2YXIgQ291bnRlciA6PSAmcjtcblxuICAgIGFzc2VydChyci52YWx1ZSA9PSAxKTtcbiAgICBhc3NlcnQocnIuZ2V0KCkgPT0gMSk7XG5cbiAgICByci5idW1wKCk7XG4gICAgYXNzZXJ0KGMudmFsdWUgPT0gMik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIiwibmFtZSI6IjA5X2F1dG9fZGVyZWZfZmllbGRfYWNjZXNzX3Rocm91Z2hfY2hhaW4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-1}

The unary `*` operator requires a shared or exclusive reference operand. Applying it to a
non-reference is a `T0002` type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAyIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzEyX2RlcmVmX25vbl9yZWZlcmVuY2UubXRsIiwic291cmNlIjoiLy8gVFlQRUNIRUNLX0VSUk9SW1QwMDAyXVxuLy8gUkZDLTAxMTAgXHUwMGE3MzogYXBwbHlpbmcgYCpgIHRvIGEgbm9uLXJlZmVyZW5jZSBpcyBhIHR5cGUgZXJyb3IuIEFkZGluZyBwYXJzZXIgc3VwcG9ydFxuLy8gZm9yIGAqYCBpcyB3aGF0IG1ha2VzIGBVbmFyeU9wOjpEZXJlZmAncyBleGlzdGluZyB0eXBlIHJ1bGUgcmVhY2hhYmxlIGZyb20gc3VyZmFjZVxuLy8gc3ludGF4IGZvciB0aGUgZmlyc3QgdGltZS5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhOiBpNjQgOj0gMTtcbiAgICBsZXQgYiA6PSAqYTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvbmVnXzEyX2RlcmVmX25vbl9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ18xMl9kZXJlZl9ub25fcmVmZXJlbmNlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.expressions.references.legality-2}

Writing through `*place` requires an `&var T` reference; a shared `&T` never grants
write access.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwIDo9IDU7ICAgICAgLy8gdHdvIGxheWVycywgdHdvIHN0YXJzXG4gICAgYXNzZXJ0KG4gPT0gNSk7XG5cbiAgICAqKnBwICs9IDEwO1xuICAgIGFzc2VydChuID09IDE1KTtcblxuICAgIC8vIE9uZSBzdGFyIHJlYWNoZXMgdGhlIGlubmVyIHJlZmVyZW5jZSBpdHNlbGYsIG5vdCB0aGUgaTY0IFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzXG4gICAgLy8gcmVwb2ludGluZyB0aHJvdWdoIGEgY2hhaW4gZXhwcmVzc2libGUgYXQgYWxsLlxuICAgIHZhciBtIDo9IDEwMDtcbiAgICAqcHAgOj0gJnZhciBtOyAgLy8gcCBub3cgcmVmZXJzIHRvIG07IG4ga2VlcHMgaXRzIHZhbHVlXG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuICAgICoqcHAgOj0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAyIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzExX3dyaXRlX3Rocm91Z2hfc2hhcmVkX3JlZmVyZW5jZS5tdGwiLCJzb3VyY2UiOiIvLyBUWVBFQ0hFQ0tfRVJST1JbVDAwMDJdXG4vLyBSRkMtMDExMCBcdTAwYTc1OiBgKnAgPSB2YCByZXF1aXJlcyBgJnZhciBUYC4gQSBzaGFyZWQgYCZUYCBpcyBuZXZlciB3cml0dGVuIHRocm91Z2ggXHUyMDE0XG4vLyB0aGF0IGlzIHRoZSB3aG9sZSBjb250cmFjdCBvZiBhIHNoYXJlZCByZWZlcmVuY2UuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYSA6PSAxO1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgICpwIDo9IDU7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzL25lZ18xMV93cml0ZV90aHJvdWdoX3NoYXJlZF9yZWZlcmVuY2UubXRsIiwibmFtZSI6Im5lZ18xMV93cml0ZV90aHJvdWdoX3NoYXJlZF9yZWZlcmVuY2UubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-7}

Evaluating `*reference` reads its referent. Explicit dereference is available in every
expression position, while selector operations retain their ordinary auto-dereference.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAxIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzA2X25vX3JlYWRfY29weV9hdF9jYWxsX2FyZ3VtZW50Lm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUltUMDAwMV1cbi8vIFJGQy0wMTEwOiB1bmRlciB0aGUgR28gbW9kZWwsIHJlYWRpbmcgdGhyb3VnaCBhIHJlZmVyZW5jZSBpcyBpbXBsaWNpdCBvbmx5IGF0XG4vLyBzZWxlY3RvcnMgKGZpZWxkLCBpbmRleCwgbWV0aG9kKS4gQSBjYWxsIGFyZ3VtZW50IGlzIG5vdCBhIHNlbGVjdG9yLCBzbyBwYXNzaW5nIGFcbi8vIHJlZmVyZW5jZSB3aGVyZSB0aGUgcGFyYW1ldGVyIGV4cGVjdHMgdGhlIHJlZmVyZW50IHR5cGUgaXMgYSBoYXJkIG1pc21hdGNoIFx1MjAxNCB3cml0ZVxuLy8gYHRha2VzX2k2NCgqcilgLlxuLy9cbi8vIE5vdGUgdGhlIHJlYXNvbiBSRkMtMDA2N2EgXHUwMGE3M2Egb3JpZ2luYWxseSBnYXZlIGZvciB0aGlzIFx1MjAxNCBcInRoZXJlIGlzIG5vIGRlY2xhcmVkIHR5cGVcbi8vIGZvciB0aGUgYXJndW1lbnQgaXRzZWxmIHRvIGNvbXBhcmUgYWdhaW5zdFwiIFx1MjAxNCBpcyBmYWN0dWFsbHkgd3Jvbmc6IGBwYXJhbV9oaW50c2Bcbi8vIGFscmVhZHkgdGhyZWFkcyB0aGUgcGFyYW1ldGVyJ3MgZGVjbGFyZWQgdHlwZSBoZXJlIGZvciBtb25vbW9ycGhpYyBjYWxsZWVzLiBUaGVcbi8vIGJlaGF2aW9yIGlzIHJpZ2h0OyB0aGUganVzdGlmaWNhdGlvbiB3YXMgbm90LiBTZWUgUkZDLTAxMTIgXHUwMGE3NC4xLCB3aGljaCByZS1leGFtaW5lZFxuLy8gY2xvc2luZyB0aGlzIGdhcCBhbmQgZGVjbGluZWQgaXQgZGVsaWJlcmF0ZWx5IHJhdGhlciB0aGFuIGJ5IGFjY2lkZW50LlxuZnVuIHRha2VzX2k2NCh4OiBpNjQpIHt9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBuIDo9IDU7XG4gICAgbGV0IHI6ICZpNjQgOj0gJm47XG4gICAgdGFrZXNfaTY0KHIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy9uZWdfMDZfbm9fcmVhZF9jb3B5X2F0X2NhbGxfYXJndW1lbnQubXRsIiwibmFtZSI6Im5lZ18wNl9ub19yZWFkX2NvcHlfYXRfY2FsbF9hcmd1bWVudC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-8}

Each leading `*` reads or writes through exactly one reference layer. A bare assignment
to a reference-typed binding instead rebinds that binding when it is mutable.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwIDo9IDU7ICAgICAgLy8gdHdvIGxheWVycywgdHdvIHN0YXJzXG4gICAgYXNzZXJ0KG4gPT0gNSk7XG5cbiAgICAqKnBwICs9IDEwO1xuICAgIGFzc2VydChuID09IDE1KTtcblxuICAgIC8vIE9uZSBzdGFyIHJlYWNoZXMgdGhlIGlubmVyIHJlZmVyZW5jZSBpdHNlbGYsIG5vdCB0aGUgaTY0IFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzXG4gICAgLy8gcmVwb2ludGluZyB0aHJvdWdoIGEgY2hhaW4gZXhwcmVzc2libGUgYXQgYWxsLlxuICAgIHZhciBtIDo9IDEwMDtcbiAgICAqcHAgOj0gJnZhciBtOyAgLy8gcCBub3cgcmVmZXJzIHRvIG07IG4ga2VlcHMgaXRzIHZhbHVlXG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuICAgICoqcHAgOj0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-9}

An assignment through a dereference writes the referenced storage; after a mutable
reference binding is rebound, a later dereference writes the new referent.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwIFx1MDBhNzQuMi9cdTAwYTc1OiB3cml0ZS10aHJvdWdoIGlzIHNwZWxsZWQgZXhwbGljaXRseSwgb25lIGAqYCBwZXIgcmVmZXJlbmNlIGxheWVyLlxuLy8gVGhpcyByZXBsYWNlcyBSRkMtMDA2N2EncyBpbXBsaWNpdCBydWxlLCB1bmRlciB3aGljaCBhIGJhcmUgYHBwID0gNWAgcGVlbGVkICpldmVyeSpcbi8vIGAmdmFyYCBsYXllciBhdCBvbmNlIFx1MjAxNCBjb252ZW5pZW50LCBidXQgaXQgbWFkZSB0aGUgbnVtYmVyIG9mIGxheWVycyBpbnZpc2libGUgYXQgdGhlXG4vLyB3cml0ZSBzaXRlIGFuZCBsZWZ0IG5vIHdheSB0byByZXBvaW50IGFueSBvZiB0aGVtLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBwcDogJnZhciAmdmFyIGk2NCA6PSAmdmFyIHA7XG5cbiAgICAqKnBwIDo9IDU7ICAgICAgLy8gdHdvIGxheWVycywgdHdvIHN0YXJzXG4gICAgYXNzZXJ0KG4gPT0gNSk7XG5cbiAgICAqKnBwICs9IDEwO1xuICAgIGFzc2VydChuID09IDE1KTtcblxuICAgIC8vIE9uZSBzdGFyIHJlYWNoZXMgdGhlIGlubmVyIHJlZmVyZW5jZSBpdHNlbGYsIG5vdCB0aGUgaTY0IFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzXG4gICAgLy8gcmVwb2ludGluZyB0aHJvdWdoIGEgY2hhaW4gZXhwcmVzc2libGUgYXQgYWxsLlxuICAgIHZhciBtIDo9IDEwMDtcbiAgICAqcHAgOj0gJnZhciBtOyAgLy8gcCBub3cgcmVmZXJzIHRvIG07IG4ga2VlcHMgaXRzIHZhbHVlXG4gICAgYXNzZXJ0KG4gPT0gMTUpO1xuICAgICoqcHAgOj0gNztcbiAgICBhc3NlcnQobSA9PSA3KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDhfd3JpdGVfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIiwibmFtZSI6IjA4X3dyaXRlX3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-10}

Field and index assignment through a reference remains implicit because those targets
are unambiguous selectors; `*(object.field) = value` and `object.field = value` have the
same write effect.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjExX2V4cGxpY2l0X2RlcmVmLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTEwOiBleHBsaWNpdCBgKmAgZm9yIHJlYWRzIGFuZCBmb3Igd3JpdGluZyB0aHJvdWdoLCBhdXRvLWRlcmVmIGF0IHNlbGVjdG9yc1xuLy8gb25seSwgYW5kIGJhcmUgYXNzaWdubWVudCB0byBhIHJlZmVyZW5jZS10eXBlZCBiaW5kaW5nIHJlYmluZGluZyByYXRoZXIgdGhhbiB3cml0aW5nXG4vLyB0aHJvdWdoIFx1MjAxNCB3aGljaCBpcyB3aGF0IG1ha2VzIHJlcG9pbnRpbmcgZXhwcmVzc2libGUuXG5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cblxuZnVuIGFkZCh4OiBpNjQsIHk6IGk2NCkgLT4gaTY0IHsgcmV0dXJuIHggKyB5OyB9XG5cbi8vIGAqYCBpcyB0aGUgc3BlbGxpbmcgaW4gdGhlIHBvc2l0aW9ucyBhdXRvLWRlcmVmIGRlbGliZXJhdGVseSBkb2VzIG5vdCBjb3Zlcjpcbi8vIGNhbGwgYXJndW1lbnRzIGFuZCBiaW5hcnkgb3BlcmFuZHMuXG5mdW4gZXhwbGljaXRfcmVhZHMoKSB7XG4gICAgbGV0IGEgOj0gMztcbiAgICBsZXQgYiA6PSA0O1xuICAgIGxldCBwOiAmaTY0IDo9ICZhO1xuICAgIGxldCBxOiAmaTY0IDo9ICZiO1xuXG4gICAgYXNzZXJ0KCpwID09IDMpO1xuICAgIGFzc2VydChhZGQoKnAsICpxKSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKyAqcSA9PSA3KTtcbiAgICBhc3NlcnQoKnAgKiAqcSA9PSAxMik7ICAgLy8gdW5hcnkgYCpgIGFuZCBiaW5hcnkgYCpgIGluIG9uZSBleHByZXNzaW9uXG59XG5cbi8vIEJhcmUgYXNzaWdubWVudCByZWJpbmRzOyBgKnAgPSB2YCB3cml0ZXMgdGhyb3VnaC5cbmZ1biByZXBvaW50X2FuZF93cml0ZV90aHJvdWdoKCkge1xuICAgIHZhciBhIDo9IDE7XG4gICAgdmFyIGIgOj0gMjtcbiAgICB2YXIgcDogJnZhciBpNjQgOj0gJnZhciBhO1xuXG4gICAgKnAgOj0gNTtcbiAgICBhc3NlcnQoYSA9PSA1KTtcblxuICAgIHAgOj0gJnZhciBiOyAgICAgIC8vIHJlcG9pbnQgXHUyMDE0IGltcG9zc2libGUgYmVmb3JlIFJGQy0wMTEwXG4gICAgKnAgOj0gOTtcbiAgICBhc3NlcnQoYSA9PSA1KTsgIC8vIGEgaXMgdW50b3VjaGVkIGJ5IHRoZSB3cml0ZSB0aHJvdWdoIHRoZSByZXBvaW50ZWQgcFxuICAgIGFzc2VydChiID09IDkpO1xuXG4gICAgKnAgKz0gMTtcbiAgICBhc3NlcnQoYiA9PSAxMCk7XG59XG5cbi8vIFNlbGVjdG9ycyBzdGF5IGltcGxpY2l0OiBubyBgKmAgbmVlZGVkIGZvciBmaWVsZCwgaW5kZXgsIG9yIG1ldGhvZCBhY2Nlc3MuXG5mdW4gc2VsZWN0b3JzX3N0YXlfaW1wbGljaXQoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gNSwgeSA9IDcgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnkgOj0gOTk7XG4gICAgYXNzZXJ0KHFwLnggPT0gNSk7XG4gICAgYXNzZXJ0KHEueSA9PSA5OSk7XG5cbiAgICB2YXIgeHMgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB4cDogJnZhciBbaTY0OyAzXSA6PSAmdmFyIHhzO1xuICAgIHhwWzBdIDo9IDk7XG4gICAgeHBbMV0gKz0gMTA7XG4gICAgYXNzZXJ0KHhzWzBdID09IDkpO1xuICAgIGFzc2VydCh4c1sxXSA9PSAxMik7XG59XG5cbi8vIGAqKG9iai5maWVsZCkgPSB2YCBhbmQgYG9iai5maWVsZCA9IHZgIGFyZSBzeW5vbnltcy5cbmZ1biByZWR1bmRhbnRfc3Rhcl9vbl9hX2ZpZWxkX3BhdGgoKSB7XG4gICAgdmFyIHEgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfTtcbiAgICBsZXQgcXA6ICZ2YXIgUG9pbnQgOj0gJnZhciBxO1xuICAgIHFwLnggOj0gMztcbiAgICBhc3NlcnQocS54ID09IDMpO1xufVxuXG5lbnVtIENob2ljZSB7IExlZnQsIFJpZ2h0IH1cblxuZnVuIGV4cGxpY2l0X2FuZF90cmFuc3BhcmVudF9tYXRjaF9hcmVfZXF1aXZhbGVudCgpIHtcbiAgICBsZXQgY2hvaWNlIDo9IENob2ljZTo6UmlnaHQ7XG4gICAgbGV0IHJlZmVyZW5jZTogJkNob2ljZSA6PSAmY2hvaWNlO1xuICAgIGxldCB0cmFuc3BhcmVudCA6PSBtYXRjaCAocmVmZXJlbmNlKSB7IENob2ljZTo6TGVmdCA9PiAxLCBDaG9pY2U6OlJpZ2h0ID0+IDIgfTtcbiAgICBsZXQgZXhwbGljaXQgOj0gbWF0Y2ggKCpyZWZlcmVuY2UpIHsgQ2hvaWNlOjpMZWZ0ID0+IDEsIENob2ljZTo6UmlnaHQgPT4gMiB9O1xuICAgIGFzc2VydCh0cmFuc3BhcmVudCA9PSBleHBsaWNpdCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGV4cGxpY2l0X3JlYWRzKCk7XG4gICAgcmVwb2ludF9hbmRfd3JpdGVfdGhyb3VnaCgpO1xuICAgIHNlbGVjdG9yc19zdGF5X2ltcGxpY2l0KCk7XG4gICAgcmVkdW5kYW50X3N0YXJfb25fYV9maWVsZF9wYXRoKCk7XG4gICAgZXhwbGljaXRfYW5kX3RyYW5zcGFyZW50X21hdGNoX2FyZV9lcXVpdmFsZW50KCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzExX2V4cGxpY2l0X2RlcmVmLm10bCIsIm5hbWUiOiIxMV9leHBsaWNpdF9kZXJlZi5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6Ijg3X3R1cGxlX2Fzc2lnbl9wYXRocy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgSG9sZGVyIHsgdDogKGk2NCwgKGk2NCwgaTY0KSkgfVxuXG5mdW4gbWFpbigpIHtcbiAgICB2YXIgdCA6PSAoMSwgMik7XG4gICAgdC4wIDo9IDU7XG4gICAgYXNzZXJ0KHQuMCA9PSA1KTtcbiAgICB0LjAgKz0gNDtcbiAgICBhc3NlcnQodC4wID09IDkpO1xuXG4gICAgdmFyIG5lc3RlZCA6PSAoMTAsICgyMCwgMzApKTtcbiAgICBuZXN0ZWQuMS4wIDo9IDk5O1xuICAgIGFzc2VydChuZXN0ZWQuMS4wID09IDk5KTtcblxuICAgIHZhciBzIDo9IEhvbGRlciB7IHQgPSAoNywgKDgsIDkpKSB9O1xuICAgIHMudC4wIDo9IDExO1xuICAgIGFzc2VydChzLnQuMCA9PSAxMSk7XG5cbiAgICB0dXBsZV9hc3NpZ25fdGhyb3VnaF9yZWZlcmVuY2VzKCk7XG59XG5cbi8vIFR1cGxlLWVsZW1lbnQgYXNzaWdubWVudCBtdXN0IHJlYWNoIHRocm91Z2ggYSByZWZlcmVuY2UgYXQgYW55IHN0ZXAgb2YgdGhlIHBhdGgsIHRoZVxuLy8gd2F5IGZpZWxkLSBhbmQgaW5kZXgtcGF0aCBhc3NpZ25tZW50IGFscmVhZHkgZG8uIE5laXRoZXIgcGFzcyBwZWVsZWQgZm9yIHR1cGxlIHRhcmdldHNcbi8vIHdoZW4gdGhlIHZhcmlhbnQgd2FzIGZpcnN0IGFkZGVkLCBzbyBgdC4wID0gdmAgd29ya2VkIG9uIGEgcGxhaW4gYmluZGluZyBidXQgbm90IG9uIGFcbi8vIGAmdmFyYCByZWNlaXZlciAtLSBhIHNlYW0gYmV0d2VlbiBtZXRlbC1jb3JlIzI4MyBhbmQgdGhlIFJGQy0wMTEwIHJlZmVyZW5jZSB3b3JrLlxuc3RydWN0IFJlZkhvbGRlciB7IHBhaXI6IChpNjQsIGk2NCkgfVxuXG5mdW4gc2V0X2RpcmVjdCh0OiAmdmFyIChpNjQsIGk2NCkpIHtcbiAgICB0LjAgOj0gOTtcbiAgICB0LjEgKz0gNTtcbn1cblxuZnVuIHNldF9uZXN0ZWQoaDogJnZhciBSZWZIb2xkZXIpIHtcbiAgICBoLnBhaXIuMCA6PSA0MjtcbiAgICBoLnBhaXIuMSArPSAzO1xufVxuXG5mdW4gdHVwbGVfYXNzaWduX3Rocm91Z2hfcmVmZXJlbmNlcygpIHtcbiAgICB2YXIgdCA6PSAoMSwgMik7XG4gICAgc2V0X2RpcmVjdCgmdmFyIHQpO1xuICAgIGFzc2VydCh0LjAgPT0gOSk7XG4gICAgYXNzZXJ0KHQuMSA9PSA3KTtcblxuICAgIHZhciByaCA6PSBSZWZIb2xkZXIgeyBwYWlyID0gKDEsIDIpIH07XG4gICAgc2V0X25lc3RlZCgmdmFyIHJoKTtcbiAgICBhc3NlcnQocmgucGFpci4wID09IDQyKTtcbiAgICBhc3NlcnQocmgucGFpci4xID09IDUpO1xuXG4gICAgLy8gQSBzaGFyZWQgcmVmZXJlbmNlIHN0aWxsIGdyYW50cyBubyB3cml0ZSBhY2Nlc3MuXG4gICAgbGV0IHI6ICZpNjQgOj0gJnJoLnBhaXIuMDtcbiAgICByaC5wYWlyLjAgOj0gNztcbiAgICBhc3NlcnQoKnIgPT0gNyk7ICAgLy8gYW5kIGl0IGFsaWFzZXMgKG1ldGVsLWNvcmUjMjgyKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvODdfdHVwbGVfYXNzaWduX3BhdGhzLm10bCIsIm5hbWUiOiI4N190dXBsZV9hc3NpZ25fcGF0aHMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.references.dynamics-11}

Taking `&*reference` or `&var *reference` reborrows the storage named by the dereference;
an exclusive reborrow may write that same storage.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0110](../../rfcs/4-implemented/rfc-0110-explicit-dereference-operator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjA2X2FkZHJlc3NhYmxlX3BsYWNlcy5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzI4MDogZXZlcnkgZm9ybSB0aGUgYWRkcmVzc2FiaWxpdHkgcnVsZSBhZG1pdHMga2VlcHMgd29ya2luZywgaW5jbHVkaW5nXG4vLyBSRkMtMDExMCBcdTAwYTc2J3MgcmVib3Jyb3cgYCYqcGAsIHdoaWNoIHByZXZpb3VzbHkgaGl0IHRoZSBzYW1lIGludGVybmFsIGVycm9yIGRlc3BpdGUgdGhlXG4vLyBSRkMgc3BlY2lmeWluZyBpdCBhcyBsZWdhbC5cbnN0cnVjdCBQb2ludCB7IHg6IGk2NCwgeTogaTY0IH1cbnN0cnVjdCBQYWlyIHsgYTogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgbiA6PSAxO1xuICAgIGxldCBhcnIgOj0gWzEsIDIsIDNdO1xuICAgIGxldCB0IDo9ICgxMCwgMjApO1xuICAgIGxldCBwYWlyIDo9IFBhaXIgeyBhID0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSB9O1xuXG4gICAgbGV0IHAxIDo9ICZuOyAgICAgICAgICAgICAgLy8gYmluZGluZ1xuICAgIGxldCBwMiA6PSAmcGFpci5hOyAgICAgICAgIC8vIGZpZWxkXG4gICAgbGV0IHAzIDo9ICZwYWlyLmEueDsgICAgICAgLy8gY2hhaW5lZCBmaWVsZFxuICAgIGxldCBwNCA6PSAmdC4wOyAgICAgICAgICAgIC8vIHR1cGxlIGVsZW1lbnRcbiAgICBsZXQgcDUgOj0gJmFyclsxXTsgICAgICAgICAvLyBhcnJheSBlbGVtZW50XG4gICAgYXNzZXJ0KCpwMSA9PSAxKTtcbiAgICBhc3NlcnQoKnAzID09IDEpO1xuICAgIGFzc2VydCgqcDQgPT0gMTApO1xuICAgIGFzc2VydCgqcDUgPT0gMik7XG4gICAgYXNzZXJ0KHAyLnkgPT0gMik7XG5cbiAgICAvLyBSZWJvcnJvdzogYCYqcGAgc2hhcmVzIHRoZSByZWZlcmVudCdzIHN0b3JhZ2UgcmF0aGVyIHRoYW4gc25hcHNob3R0aW5nIGl0LlxuICAgIHZhciBtIDo9IDU7XG4gICAgbGV0IG1wOiAmdmFyIGk2NCA6PSAmdmFyIG07XG4gICAgbGV0IHJiIDo9ICYqbXA7XG4gICAgYXNzZXJ0KCpyYiA9PSA1KTtcblxuICAgIGxldCByYm0gOj0gJnZhciAqbXA7XG4gICAgKnJibSA6PSA5O1xuICAgIGFzc2VydChtID09IDkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYWRkcmVzc2FiaWxpdHkvMDZfYWRkcmVzc2FibGVfcGxhY2VzLm10bCIsIm5hbWUiOiIwNl9hZGRyZXNzYWJsZV9wbGFjZXMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Loop

[`loop` creates an infinite loop](types.md#spec.types.never-type.dynamics-1). It is the only loop form that can produce a value:

```metel
fun main() -> i64 {
    let result := loop {
        break 42;
    };
    return result;
}
```

**Typing rules:**

- `loop { break expr; }` has type `T` where `expr: T`. All `break` arms must produce the same type; a `break` expression is [typechecked against its enclosing loop value type](types.md#spec.types.type-inference.legality-2).
- `loop { }` — a loop with no reachable `break` — has type `!` (Never). See [Never Type](types.md#never-type).

### Break, Continue, and Return

> **Availability:** Since v0.10.0.

[`return`, `break`, and `continue` are expressions of type `!`](types.md#spec.types.never-type.dynamics-1) (Never — see
[Never Type](types.md#never-type)), not statements. Since `!` is a subtype of
every type, they're valid anywhere an expression is valid — a block tail with
no trailing `;`, a braceless `if`-arm, a match-arm body, or nested inside
another expression — not just as a semicolon-terminated statement on its own
line:

```metel
fun pick(ok: boolean) -> i64 {
    if (ok) return 42;   // braceless if-arm, no braces needed
    0
}

fun compute() -> i64 {
    var i := 0;
    loop {
        i := i + 1;
        if (i == 5) {
            break i * 10   // loop-body tail, no trailing `;`
        }
    }
}

fun classify(value: i64) -> i64 {
    match (value) {
        0 => 0,
        1 => return 10,   // match-arm body, same as any other expression arm
        _ => 20,
    }
}

fun nested(c: boolean) -> i64 {
    let x := if (c) return 99 else 0;   // nested expression position
    x
}
```

[`break` exits the innermost loop](#spec.expressions.control-flow.break-continue-and-return.dynamics-1); `break expr` exits a `loop` and produces
`expr` as the loop's value (`break` with no value produces `Unit`).
[`continue` skips to the next iteration of the innermost loop](#spec.expressions.control-flow.break-continue-and-return.dynamics-2). `return`/
`return expr` [returns from the enclosing function](#spec.expressions.control-flow.break-continue-and-return.dynamics-3), using the function's
declared return type (or `Unit`, if omitted):

```metel
fun returns_unit() {
    return;
}

fun returns_value() -> i64 {
    return 42;
}

fun main() -> i64 {
    returns_unit();
    return returns_value();
}
```

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-1}

`break` transfers control out of the innermost enclosing loop. In a value-producing
`loop`, `break expr` supplies that loop's result and bare `break` supplies `()`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEzX2xvb3AubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gQnJlYWsgd2l0aCBhIHZhbHVlLlxuICAgIGxldCB4IDo9IGxvb3AgeyBicmVhayA0MjsgfTtcbiAgICBhc3NlcnQoeCA9PSA0Mik7XG4gICAgLy8gQ29udGludWUgc2tpcHMgdGhlIGN1cnJlbnQgaXRlcmF0aW9uLlxuICAgIHZhciBjb3VudCA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgbG9vcCB7XG4gICAgICAgIGlmIChpID49IDUpIHsgYnJlYWs7IH1cbiAgICAgICAgaSA6PSBpICsgMTtcbiAgICAgICAgaWYgKGkgPT0gMykgeyBjb250aW51ZTsgfVxuICAgICAgICBjb3VudCA6PSBjb3VudCArIDE7XG4gICAgfVxuICAgIGFzc2VydChjb3VudCA9PSA0KTtcbiAgICAvLyBBc3NpZ25tZW50cyBpbnNpZGUgdGhlIGxvb3AgYXJlIHZpc2libGUgaW4gc3Vic2VxdWVudCBpdGVyYXRpb25zLlxuICAgIHZhciBhY2MgOj0gMDtcbiAgICB2YXIgaiA6PSAxO1xuICAgIGxvb3Age1xuICAgICAgICBpZiAoaiA+IDUpIHsgYnJlYWs7IH1cbiAgICAgICAgYWNjICs9IGo7XG4gICAgICAgIGogKz0gMTtcbiAgICB9XG4gICAgYXNzZXJ0KGFjYyA9PSAxNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTNfbG9vcC5tdGwiLCJuYW1lIjoiMTNfbG9vcC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjkxX25lc3RlZF9icmVha19wcm9wYWdhdGlvbi5tdGwiLCJzb3VyY2UiOiIvLyBJc3N1ZSAjMjI5OiBhIGBicmVha2Agd3JpdHRlbiBhcyBhIG5lc3RlZCBgaWZgLXRhaWwgb3IgbWF0Y2gtYXJtLXRhaWwgbXVzdFxuLy8gc3RpbGwgY29ycmVjdGx5IHByb3BhZ2F0ZSB0byB0aGUgZW5jbG9zaW5nIGxvb3AncyBvd24gaW5mZXJyZWQgdHlwZSAtLVxuLy8gYGZpbmRfbG9vcF9icmVha190eXBlYCBwcmV2aW91c2x5IG9ubHkgY2hlY2tlZCBgYmxvY2suc3RtdHNgLCBuZXZlclxuLy8gYGJsb2NrLnRhaWxgIGFuZCBuZXZlciByZWN1cnNlZCBpbnRvIGBNYXRjaGAsIGJvdGggcHJlLWV4aXN0aW5nIGdhcHMgb25seVxuLy8gcmVhY2hhYmxlIGluIHByYWN0aWNlIG9uY2UgYGJyZWFrYCBjb3VsZCBiZSBhIHRhaWwgZXhwcmVzc2lvbiBhdCBhbGwuXG5mdW4gdmlhX2lmKGM6IGJvb2xlYW4pIC0+IGk2NCB7XG4gICAgbG9vcCB7XG4gICAgICAgIGlmIChjKSB7IGJyZWFrIDcgfVxuICAgIH1cbn1cblxuZnVuIHZpYV9tYXRjaChjOiBib29sZWFuKSAtPiBpNjQge1xuICAgIGxvb3Age1xuICAgICAgICBtYXRjaCAoYykge1xuICAgICAgICAgICAgdHJ1ZSA9PiBicmVhayA4LFxuICAgICAgICAgICAgZmFsc2UgPT4gYnJlYWsgOCxcbiAgICAgICAgfVxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KHZpYV9pZih0cnVlKSA9PSA3KTtcbiAgICBhc3NlcnQodmlhX21hdGNoKHRydWUpID09IDgpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvY29udHJvbF9mbG93LzkxX25lc3RlZF9icmVha19wcm9wYWdhdGlvbi5tdGwiLCJuYW1lIjoiOTFfbmVzdGVkX2JyZWFrX3Byb3BhZ2F0aW9uLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InN0YWdlNl8wOV9uZXN0ZWRfbG9vcF9icmVhay5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA2OiBicmVhayBuZXN0ZWQgaW5zaWRlIGlmIGJyYW5jaGVzIGlzIHZpc2libGUgdG8gZmluZF9sb29wX2JyZWFrX3R5cGUuXG5cbi8vIGJyZWFrIGluc2lkZSBpZi10aGVuIGJyYW5jaCBvbmx5XG5sZXQgX2E6IGk2NCA6PSBsb29wIHtcbiAgICBpZiAodHJ1ZSkgeyBicmVhayA0MjsgfVxufTtcblxuLy8gYnJlYWsgaW4gYm90aCB0aGVuIGFuZCBlbHNlIGJyYW5jaGVzXG5sZXQgX2I6IGk2NCA6PSBsb29wIHtcbiAgICBpZiAodHJ1ZSkgeyBicmVhayA0MjsgfSBlbHNlIHsgYnJlYWsgMDsgfVxufTtcblxuLy8gaW5uZXIgbG9vcCBicmVhayBkb2VzIG5vdCBlc2NhcGUgdG8gb3V0ZXIgbG9vcDsgb3V0ZXIgZGl2ZXJnZXMgKE5ldmVyKS5cbi8vIEJvdGggdHJhaWxpbmctc2VtaWNvbG9uIGFuZCBuby1zZW1pY29sb24gZm9ybXMgYXJlIHZhbGlkIGluIHN0YXRlbWVudCBwb3NpdGlvbi5cbmZ1biBkaXZlcmdlX291dGVyX3dpdGhfc2VtaSgpIC0+IGk2NCB7XG4gICAgbG9vcCB7XG4gICAgICAgIGxvb3AgeyBicmVhayBcImlubmVyXCI7IH07XG4gICAgICAgIGxvb3AgeyBicmVhayBcImlubmVyXCI7IH07XG4gICAgfVxufVxuXG5mdW4gZGl2ZXJnZV9vdXRlcl9ub19zZW1pKCkgLT4gaTY0IHtcbiAgICBsb29wIHtcbiAgICAgICAgbG9vcCB7IGJyZWFrIFwiaW5uZXJcIjsgfVxuICAgICAgICBsb29wIHsgYnJlYWsgXCJpbm5lclwiOyB9XG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvY29udHJvbF9mbG93L3N0YWdlNl8wOV9uZXN0ZWRfbG9vcF9icmVhay5tdGwiLCJuYW1lIjoic3RhZ2U2XzA5X25lc3RlZF9sb29wX2JyZWFrLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-2}

`continue` abandons the current iteration of the innermost enclosing loop and begins its
next iteration.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjEzX2xvb3AubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gQnJlYWsgd2l0aCBhIHZhbHVlLlxuICAgIGxldCB4IDo9IGxvb3AgeyBicmVhayA0MjsgfTtcbiAgICBhc3NlcnQoeCA9PSA0Mik7XG4gICAgLy8gQ29udGludWUgc2tpcHMgdGhlIGN1cnJlbnQgaXRlcmF0aW9uLlxuICAgIHZhciBjb3VudCA6PSAwO1xuICAgIHZhciBpIDo9IDA7XG4gICAgbG9vcCB7XG4gICAgICAgIGlmIChpID49IDUpIHsgYnJlYWs7IH1cbiAgICAgICAgaSA6PSBpICsgMTtcbiAgICAgICAgaWYgKGkgPT0gMykgeyBjb250aW51ZTsgfVxuICAgICAgICBjb3VudCA6PSBjb3VudCArIDE7XG4gICAgfVxuICAgIGFzc2VydChjb3VudCA9PSA0KTtcbiAgICAvLyBBc3NpZ25tZW50cyBpbnNpZGUgdGhlIGxvb3AgYXJlIHZpc2libGUgaW4gc3Vic2VxdWVudCBpdGVyYXRpb25zLlxuICAgIHZhciBhY2MgOj0gMDtcbiAgICB2YXIgaiA6PSAxO1xuICAgIGxvb3Age1xuICAgICAgICBpZiAoaiA+IDUpIHsgYnJlYWs7IH1cbiAgICAgICAgYWNjICs9IGo7XG4gICAgICAgIGogKz0gMTtcbiAgICB9XG4gICAgYXNzZXJ0KGFjYyA9PSAxNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9jb250cm9sX2Zsb3cvMTNfbG9vcC5tdGwiLCJuYW1lIjoiMTNfbG9vcC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InN0YWdlNl8xMF9sb29wX2NvbnRyb2xfc3RhdGVtZW50cy5tdGwiLCJzb3VyY2UiOiIvLyBgYnJlYWtgIGFuZCBgY29udGludWVgIHJlbWFpbiB2YWxpZCBpbiBldmVyeSBsb29wIGZvcm0uXG5cbmZ1biB3aGlsZV9jb250cm9scygpIHtcbiAgICB2YXIgaSA6PSAwO1xuICAgIHdoaWxlIChpIDwgMykge1xuICAgICAgICBpICs9IDE7XG4gICAgICAgIGlmIChpIDwgMikge1xuICAgICAgICAgICAgY29udGludWU7XG4gICAgICAgIH1cbiAgICAgICAgYnJlYWs7XG4gICAgfVxufVxuXG5mdW4gZm9yX2NvbnRyb2xzKCkge1xuICAgIGZvciAodmFyIGkgOj0gMDsgaSA8IDM7IGkgKz0gMSkge1xuICAgICAgICBpZiAoaSA8IDIpIHtcbiAgICAgICAgICAgIGNvbnRpbnVlO1xuICAgICAgICB9XG4gICAgICAgIGJyZWFrO1xuICAgIH1cbn1cblxuZnVuIGZvcl9pbl9jb250cm9scygpIHtcbiAgICBmb3IgKGl0ZW0gaW4gWzEsIDIsIDNdKSB7XG4gICAgICAgIGlmIChpdGVtIDwgMikge1xuICAgICAgICAgICAgY29udGludWU7XG4gICAgICAgIH1cbiAgICAgICAgYnJlYWs7XG4gICAgfVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvY29udHJvbF9mbG93L3N0YWdlNl8xMF9sb29wX2NvbnRyb2xfc3RhdGVtZW50cy5tdGwiLCJuYW1lIjoic3RhZ2U2XzEwX2xvb3BfY29udHJvbF9zdGF0ZW1lbnRzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.expressions.control-flow.break-continue-and-return.dynamics-3}

`return expr` transfers control out of the enclosing function with `expr` as its result;
bare `return` returns `()`.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6IjgxX3JldHVybl9leGl0c19lYXJseV9hbmRfYmFyZV9yZXR1cm5faXNfdW5pdC5tdGwiLCJzb3VyY2UiOiJmdW4gZWFybHkoZmxhZzogYm9vbGVhbikgLT4gaTY0IHtcbiAgICBpZiAoZmxhZykge1xuICAgICAgICByZXR1cm4gNDI7XG4gICAgfVxuICAgIGxldCBfb25seV9yZWFjaGVkX3dpdGhvdXRfZWFybHlfcmV0dXJuIDo9IDEgLyAwO1xuICAgIDBcbn1cblxuZnVuIHJldHVybnNfdW5pdCgpIHtcbiAgICByZXR1cm47XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChlYXJseSh0cnVlKSA9PSA0Mik7XG4gICAgbGV0IHVuaXQ6ICgpIDo9IHJldHVybnNfdW5pdCgpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZnVuY3Rpb25zLzgxX3JldHVybl9leGl0c19lYXJseV9hbmRfYmFyZV9yZXR1cm5faXNfdW5pdC5tdGwiLCJuYW1lIjoiODFfcmV0dXJuX2V4aXRzX2Vhcmx5X2FuZF9iYXJlX3JldHVybl9pc191bml0Lm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>
