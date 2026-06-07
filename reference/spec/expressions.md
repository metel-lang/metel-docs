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

Each arm body can be an expression, a `return`/`break` statement, or a block:

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
| Literal | `0`, `"hi"`, `true`, `None` | exact value |
| Enum variant | `Direction::North` | unit variant |
| Enum with fields | `Shape::Circle { radius }` | variant, binds fields |
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
    let mut n = 3;
    let mut total = 0;
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
    let mut total = 0;
    for (let mut i = 0; i < 4; i += 1) {
        total += i;
    }
    return total;
}
```

### For-In

> **Availability:**
> Array and range iteration: since v0.1.0.
> User-defined `Iterable<T>` implementations: since v0.4.0.

`for-in` works on any type implementing the `Iterable<T>` aspect. The loop variable
receives type `T`. `T[]`, `[T; N]` (array and fixed-size array), and `Range` (produced by `..` and `..=`) implement
`Iterable<T>` by default. User-defined types can be made iterable by implementing
`Iterable<T>`. The loop binding is immutable by default and may be made loop-locally
mutable with `let mut`:

```metel
aspect Iterable<T> {
    fun next(&mut self) -> Perhaps<T>;
}

fun main() -> i64 {
    return 0;
}
```

```metel
fun main() -> i64 {
    let collection = [1, 2, 3];
    let mut total = 0;
    for (let item in collection) { total += item; }
    for (let mut item in collection) {
        item += 1;
        total += item;
    }
    for (let i in 0..10) { total += i; }
    for (let i in 0..=10) { total += i; }
    return total;
}
```

### Pointers

Regular pointers provide explicit aliasing for non-linear values.

```metel
fun main() -> i64 {
    let mut n = 1;
    let p: *mut i64 = &mut n;
    *p = 4;
    return *p;
}
```

Rules:

- `&expr` creates a read-only pointer `*T` where `expr` is an addressable lvalue
- `&mut x` creates a mutable pointer `*mut T` where `x` is a `let mut` named binding
- `*p` reads through a pointer
- `*p = value` writes through a `*mut T`

Addressable lvalues for `&` include named bindings (`x`), struct field access (`s.field`), tuple element access (`t.0`), array indexing (`arr[i]`), and chains thereof (`nested.outer.field`, `t.1.0`). Non-addressable expressions (call results, arithmetic) are rejected at runtime.

`&mut` requires the operand to be a `let mut` binding — applying it to a plain `let` is a type error ([T0006](../error-codes.md#t0006--assignment-to-immutable-binding)). `&mut` is additionally restricted to named bindings only; `&struct.field` captures a snapshot of the field value at the time of the address-of operation, with subsequent mutations to the original binding not visible through the pointer.

Field access, field assignment, method calls, and function pointer calls auto-dereference one pointer layer:

```metel
struct Counter {
    value: i64,
}

impl Counter {
    fun increment(&mut self) {
        self.value += 1;
    }
}

fun main() -> i64 {
    let mut counter = Counter { value: 0 };
    let p: *mut Counter = &mut counter;
    p.increment();    // auto-deref: equivalent to (*p).increment()
    p.value = 1;      // auto-deref field assign; the pointer binding need not be mut
    return p.value;   // auto-deref: equivalent to (*p).value
}
```

Function pointers (`*() -> T` and `*mut () -> T`) are callable directly without explicit dereference:

```metel
fun main() -> i64 {
    let f = () -> { return 42; };
    let ptr: *() -> i64 = &f;
    return ptr();     // auto-deref: equivalent to (*ptr)()
}
```

This applies uniformly: a closure or named function stored behind a pointer can be called as if it were the function value itself. A common use is passing arrays of function pointers:

```metel
fun apply_all(fns: Array<*() -> ()>) {
    for (let f in fns) {
        f();          // auto-deref each element
    }
}
```

Indexing, plain reads, argument passing, and assignment remain explicit pointer operations.

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

### Break and Continue

`break` exits the innermost loop. `break expr` exits a `loop` and produces `expr` as the loop's value.

`continue` skips to the next iteration of the innermost loop.

### Return

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
