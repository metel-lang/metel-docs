# Expressions

## Pattern Matching

`match` performs exhaustive pattern matching. All cases must be covered.

```metel
fun main() -> i64 {
    let value = 1;
    match value {
        1 => 10,
        _ => 0,
    }
}
```

Each arm body can be any expression, or a block. `return`/`break`/`continue` are
themselves expressions of type `!` (see [Break, Continue, and Return](#break-continue-and-return)
below), so a bare arm body like `1 => return 10` needs no special grammar case —
it's just an ordinary expression arm, like any other:

```metel
// Match arm body forms start here.
fun classify(value: i64) -> i64 {
    loop {
        break match value {
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
    let x = 1;
    let label = match x {
        0 => "zero",
        1 => "one",
        _ => "other",
    };
    return label.len();
}
```

Arms with blocks follow the same rules as function bodies: the block's tail expression (if present) is the arm's value; a block with no tail produces `Unit`.

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let shape = Shape::Circle { radius: 3.0 };
    let desc: String = match shape {
        Shape::Circle { radius } => {
            let area = radius * radius;
            (area as i64).to_string()
        },
        Shape::Rectangle { width, height } => "rectangle",
    };
    return desc.len();
}
```

### Pattern Kinds

| Pattern | Example | Matches |
|---------|---------|---------|
| Wildcard | `_` | anything, binds nothing |
| Binding | `n` | anything, binds to `n` |
| Literal | `0`, `"hi"`, `true` | exact value |
| Enum variant | `Direction::North`, `North` | unit variant (qualified or, since v0.11.0, bare) |
| Enum with fields | `Shape::Circle { radius }`, `Circle { radius }` | variant, binds fields |
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
    let shape = Shape::Rectangle { width: 4.0, height: 2.0 };
    let x = -3;
    let point: (i64, i64) = (0, 7);

    let a = match shape {
        Shape::Circle { radius } => radius as i64,
        Shape::Rectangle { width, height } => width as i64,
    };

    let b = match x {
        0          => 0,
        n if n < 0 => 1,
        _          => 2,
    };

    let c = match point {
        (0, 0) => 0,
        (x, 0) => x,
        (0, y) => y,
        (x, y) => x + y,
    };

    return a + b + c;
}
```

### Unqualified variant patterns

> **Since v0.11.0 (RFC-0107).**

A match arm may name an enum variant without its `Enum::` prefix when the variant
resolves unambiguously against the scrutinee's known enum type. The candidate enum is
*only* the scrutinee's own type — this is type-directed resolution, not a lexical import
of variant names — so there is no cross-enum collision to resolve:

```metel
enum Colour { Red, Green, Blue }

fun name(c: Colour) -> String {
    match c {
        Red   => "red",
        Green => "green",
        Blue  => "blue",
    }
}
```

Fieldful variants may also be written bare:

```metel
fun unwrap_or_zero(v: Perhaps<i64>) -> i64 {
    match v {
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

### Matching through a reference

> **Since v0.11.0 (RFC-0108).**

A scrutinee of reference type (`&T`, `&var T`, and chains thereof) matches against `T`'s
own patterns — reference layers are peeled before pattern resolution, the same way field
access and method dispatch already auto-dereference:

```metel
enum Colour { Red, Green, Blue }

fun name(c: &Colour) -> String {
    match c {
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
    match c {
        Red   => "red",     // c is peeled &Colour -> Colour, then Red resolves against Colour
        Green => "green",
        Blue  => "blue",
    }
}
```

---

## Control Flow

### If / Else

```metel
fun main() -> i64 {
    let condition = false;
    let other = true;
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
    let x = 1;
    let label = if (x > 0) { "positive" } else { "non-positive" };
    return label.len();
}
```

**Braceless bodies.** A single expression may be used as the branch body without braces:

```metel
fun print_state() { }

fun main() -> i64 {
    let debug = true;
    let flag = false;
    let value_a = 10;
    let value_b = 20;
    if (debug) print_state();
    let x = if (flag) value_a else value_b;
    return x;
}
```

The braceless form desugars to a single-expression block. Three restrictions apply:

1. **Arm style must be consistent.** Both the `then` and `else` arms must use the same style — either both braced or both braceless. Mixing is a parse error.
2. **Dangling-else is forbidden.** If the outer body is braceless, the body expression must not itself be an `if–else`. Use braces on the outer body to resolve the ambiguity.
   ```metel
   fun main() -> i64 {
       let a = true;
       let b = false;
       if (a) if (b) { return 1; }
       if (a) { if (b) { return 2; } else { return 3; } }
       return 4;
   }
   ```
   ```metel
   fun main() {
       let a = true;
       let b = false;
       if (a) if (b) { return; } else { return; }
   }
   ```
3. **No semicolon between braceless arms.** Write `if (c) a else b;`, not `if (c) a; else b;` — the `;` terminates the statement before the `else`.

### While

```metel
fun main() -> i64 {
    var n = 3;
    var total = 0;
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
    var total = 0;
    for (var i = 0; i < 4; i += 1) {
        total += i;
    }
    return total;
}
```

### For-In

> **Availability:** Array and range iteration since v0.1.0. User-defined `Iterable<T>` implementations since v0.4.0.

`for-in` works on any type implementing the `Iterable<T>` aspect. The loop variable
receives type `T`. `T[]`, `[T; N]` (array and fixed-size array), and `Range` (produced by `..` and `..=`) implement
`Iterable<T>` by default. User-defined types can be made iterable by implementing
`Iterable<T>`. The loop binding is immutable by default and may be made loop-locally
mutable with `var`:

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
    let collection = [1, 2, 3];
    var total = 0;
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

### References

> **Availability:** Since v0.10.0.

References provide explicit aliasing for non-linear values.

```metel
fun main() -> i64 {
    var n = 1;
    let p: &var i64 = &var n;
    *p = 4;   // write-through: mutate the referent via explicit deref
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

Addressable places for both `&` and `&var` include named bindings (`x`), struct field access (`s.field`), tuple element access (`t.0`), array indexing (`arr[i]`), a dereference (`*p` — so `&*p` is a reborrow that shares the referent's storage), and chains thereof (`nested.outer.field`, `t.1.0`). Non-addressable expressions (literals, call results, struct and enum construction, arithmetic) are rejected at compile time with [T0005](../error-codes.md#t0005--invalid-operand-types).

`&var` requires the operand to be a `var` binding — applying it to a plain `let` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)). `&var` on a lvalue path (`&var s.field`, `&var arr[i]`) produces a true exclusive reference with write-back semantics, matching `&var` on a named binding exactly — writes through it propagate to the original storage location (RFC-0045, already implemented; this section previously described `&var struct.field` as a non-propagating snapshot, which was the *pre*-RFC-0045 behavior and had never been updated to match). `&` on a field or element also aliases the original storage through the same path machinery, so later writes to the binding remain visible through the shared reference; it is still read-only, so writing through `&T` remains rejected. Reborrowing preserves this: `&*r` shares whatever storage `r` names, and reborrowing a `&var T` as `&T` downgrades to shared. The reverse is rejected — `&var *r` where `r: &T` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)), since a shared reference never grants write access.

#### Dereference

> **Changed in v0.11.0 (RFC-0110): `*p` added; assignment to a reference-typed binding now rebinds it, use `*p = v` to write through.**

`*expr` dereferences a `&T`/`&var T`. As an expression it reads the referent; as an
assignment target, `*p = v` writes through a `&var T`. Applying `*` to a non-reference is
a type error ([T0002](../error-codes.md#t0002--cannot-infer-type)).

Auto-deref covers **selectors only** — field access, indexing, and method dispatch, where
the target of the operation is unambiguous. Everywhere else, reading through a reference
is spelled explicitly:

```metel
fun add(x: i64, y: i64) -> i64 { x + y }

fun main() -> i64 {
    let a = 3;
    let b = 4;
    let p: &i64 = &a;
    let q: &i64 = &b;
    return add(*p, *q) + (*p + *q);   // explicit: call arguments and operands
}
```

Bare assignment to a reference-typed binding rebinds it rather than writing through, so a
`&var T` can be repointed:

```metel
fun main() -> i64 {
    var a = 1;
    var b = 2;
    var p: &var i64 = &var a;
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
    var q = Point { x: 5, y: 7 };
    let qp: &var Point = &var q;
    qp.y = 99;        // field write-through — no `*` needed
    var xs = [1, 2, 3];
    let xp: &var i64[] = &var xs;
    xp[0] = 9;        // index write-through — no `*` needed
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
    var counter = Counter { value: 0 };
    let p: &var Counter = &var counter;
    p.increment();    // auto-deref: equivalent to accessing through the reference directly
    p.value = 1;      // auto-deref field assign; the reference binding need not be var
    return p.value;   // auto-deref field read
}
```

Function references (`&() -> T` and `&var () -> T`) are callable directly, the same way:

```metel
fun main() -> i64 {
    let f = () -> { return 42; };
    let r: &() -> i64 = &f;
    return r();       // auto-deref: calls through the reference directly
}
```

This applies uniformly: a closure or named function stored behind a reference can be called as if it were the function value itself. A common use is passing arrays of function references:

```metel
fun apply_all(fns: Array<&() -> ()>) {
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
    var c = Counter { value: 0 };
    let p: &var Counter = &var c;
    let rr: &&var Counter = &p;
    rr.increment();   // auto-deref through both layers
    return rr.value;  // likewise for a field read
}
```

Indexing, argument passing, and assignment remain ordinary reference operations — none of them are the value-extraction case (see `types.md`), so none require type-directed copy.

### Loop

`loop` creates an infinite loop. It is the only loop form that can produce a value:

```metel
fun main() -> i64 {
    let result = loop {
        break 42;
    };
    return result;
}
```

**Typing rules:**

- `loop { break expr; }` has type `T` where `expr: T`. All `break` arms must produce the same type.
- `loop { }` — a loop with no reachable `break` — has type `!` (Never). See [Never Type](types.md#never-type).

### Break, Continue, and Return

> **Availability:** Since v0.10.0.

`return`, `break`, and `continue` are expressions of type `!` (Never — see
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
    var i = 0;
    loop {
        i = i + 1;
        if (i == 5) {
            break i * 10   // loop-body tail, no trailing `;`
        }
    }
}

fun classify(value: i64) -> i64 {
    match value {
        0 => 0,
        1 => return 10,   // match-arm body, same as any other expression arm
        _ => 20,
    }
}

fun nested(c: boolean) -> i64 {
    let x = if (c) return 99 else 0;   // nested expression position
    x
}
```

`break` exits the innermost loop; `break expr` exits a `loop` and produces
`expr` as the loop's value (`break` with no value produces `Unit`).
`continue` skips to the next iteration of the innermost loop. `return`/
`return expr` returns from the enclosing function, using the function's
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
