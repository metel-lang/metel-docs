# Metel Error Code Reference

All Metel errors carry a code. Codes are prefixed by phase:

| Prefix | Phase |
|---|---|
| `P` | Parse — invalid source text |
| `T` | Type — type-checker rejection |
| `R` | Runtime — error during execution |
| `I` | Internal — bug in the interpreter (please report) |

---

## Parse errors (P)

### P0001 — Syntax error

The source text does not match the Metel grammar.

```
[P0001] parse error in main.mtl at 12..18 (`let x = ;`): expected expression
```

**Fix:** correct the syntax at the indicated position.

### P0002 — Invalid integer literal

An integer literal is out of range for `i64` (−9,223,372,036,854,775,808 to 9,223,372,036,854,775,807).

```
[P0002] parse error in main.mtl at 4..24: integer literal '99999999999999999999' is out of range for i64
```

**Fix:** use a value that fits in `i64`, or split the computation.

### P0003 — Invalid float literal

A float literal cannot be represented as an `f64`.

```
[P0003] parse error in main.mtl at 4..12: invalid float literal '1e9999'
```

**Fix:** use a value within the `f64` range (~±1.8 × 10³⁰⁸).

---

## Type errors (T)

### T0001 — Type mismatch

Two types that must be equal are not.

```
[T0001] type error in main.mtl at 10..20: expected i64, got boolean
```

**Fix:** ensure the expression produces the expected type. Add an explicit cast if widening (e.g. `x as f64`).

### T0002 — Annotation required

The type checker cannot infer a type without an explicit annotation.

```
[T0002] type error in main.mtl at 5..10: cannot infer type of `x`; add a type annotation
```

**Fix:** annotate the binding: `let x: i64 = ...`.

### T0003 — Undefined name

A name is used but not defined in the current scope.

```
[T0003] type error in main.mtl at 8..12: undefined name `foo`
```

**Fix:** define the variable or function before use, or correct the spelling.

### T0004 — Arity mismatch

A function is called with the wrong number of arguments.

```
[T0004] type error in main.mtl at 5..20: expected 2 arguments, got 3
```

**Fix:** pass the exact number of arguments the function declares.

### T0005 — Invalid operand types

A binary operator is applied to types it does not support.

```
[T0005] type error in main.mtl at 6..13: operator `+` cannot be applied to boolean and i64
```

**Fix:** use compatible types, or cast one operand.

### T0006 — Assignment to immutable binding

A write operation targets a `let` binding. This covers three forms:

- Direct reassignment: `x = newValue`
- Field assignment through an immutable binding: `point.x = 1`
- Taking a mutable pointer to an immutable binding: `&mut x`

```
[T0006] type error in main.mtl at 3..12: `x` is immutable; use `mut x` to allow reassignment
```

**Fix:** change the binding declaration to `let mut`.

### T0007 — Invalid cast

A `as` cast between incompatible types.

```
[T0007] type error in main.mtl at 5..15: cannot cast boolean to i64
```

**Fix:** only cast between numeric types (`i64 as f64`). Use an explicit conversion function for other types.

### T0008 — Non-exhaustive match

A `match` expression does not cover all possible values of the scrutinee type.

```
[T0008] type error in main.mtl at 2..30: match on Colour is non-exhaustive; missing variant `Blue`
```

**Fix:** add the missing arms, or add a wildcard arm `_ => ...`.

### T0013 — Ambiguous aspect method resolution

Two different aspects define the same method name on the same receiver type, so a
call like `value.method()` does not have a unique static target.

```
[T0013] type error in main.mtl at 12..20: ambiguous aspect method `label` on type `S`: both `A` and `B` provide this method
```

**Fix:** rename one of the methods, remove one of the conflicting impls, or change the
design so the receiver type does not expose two indistinguishable aspect methods.

### T0014 — Orphan implementation

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0060-aspect-impl-coherence.md`.

An `impl Aspect for Type` where neither `Aspect` nor `Type`'s outermost type
constructor is declared in the current module (or `std::core`, for built-ins).

```
[T0014] type error in main.mtl at 1..40: orphan implementation: neither `Display` nor `i64` is local to this module
```

**Fix:** move the impl into the module that declares the aspect or the type, or (for
two foreign types) into `std::core` if this is genuinely a standard-library concern.

### T0015 — Conflicting implementation

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0060-aspect-impl-coherence.md`.

Two impls of the same aspect cover the same concrete type — either two identical
impls, or a positive and a negative impl (see Negative Impls in the declarations
reference) for the same concrete type.

```
[T0015] type error in main.mtl at 1..40: conflicting implementation: `Display` is already implemented for `List<i64>` at 10..30
```

**Fix:** remove the duplicate impl, or narrow one impl's type arguments so the two no
longer overlap.

### T0016 — Non-diverging `-> !` function

A function declared `-> !` (RFC-0078) contains a reachable path that doesn't
diverge — most commonly an ordinary `return <expr>` where `<expr>` isn't itself
`!`-typed. A `-> !` function promises never to return; the compiler verifies
every control-flow path ends in a diverging expression (a `panic`, a `loop`
with no reachable `break`, or a `return`/tail expression whose own value is
already `!`-typed).

```
[T0016] type error in main.mtl at 1..40: function `bad` is declared `-> !` but does not diverge on all paths
```

**Fix:** make every path genuinely diverge (`panic(msg)`, `loop { }`, or a
recursive/other `!`-returning call), or drop the `-> !` annotation if the
function is meant to return normally.

---

## Runtime errors (R)

### R0001 — No `main` function defined

Execution requires a `main` function but none was found.

```
[R0001] runtime error in main.mtl at 0..0: no main() function defined
```

**Fix:** add `fn main() { ... }` to your program.

### R0002 — `main` is not a valid entry point

`main` exists but is generic or is not a function.

```
[R0002] runtime error in main.mtl at 0..0: main() is generic — not supported in v0.1
```

**Fix:** `main` must be a concrete, non-generic function with no parameters.

### R0003 — Undefined variable at runtime

A variable name is not found in the current environment. This can occur when a variable is used before it is defined in a branch that the type-checker did not flag.

```
[R0003] runtime error in main.mtl at 10..15: undefined variable `x`
```

### R0004 — Index out of bounds

An array index is negative or ≥ the array length.

```
[R0004] runtime error in main.mtl at 5..10: index 5 out of bounds (len 3)
```

**Fix:** check that the index is within `0..array.len()` before access.

### R0005 — Tuple index out of bounds

A tuple element is accessed by an index that does not exist.

```
[R0005] runtime error in main.mtl at 5..10: tuple index 3 out of bounds
```

**Fix:** tuple indices are fixed at compile time; verify the index against the tuple's declared length.

### R0006 — Non-exhaustive match at runtime

A `match` expression reached its end without any arm matching. This indicates a pattern that the type checker approved as exhaustive but that is not, which is a known limitation.

```
[R0006] runtime error in main.mtl at 2..30: match: no arm matched scrutinee
```

### R0007 — Arithmetic error

Integer division or remainder by zero.

```
[R0007] runtime error in main.mtl at 8..13: division by zero
```

**Fix:** guard with a zero check before dividing.

### R0008 — Field not found

A struct or enum value does not have the accessed field.

```
[R0008] runtime error in main.mtl at 5..12: no field `colour` on value
```

**Fix:** check the field name against the type definition.

### R0009 — Method not found

A method call cannot be resolved for the receiver type.

```
[R0009] runtime error in main.mtl at 5..20: no method `draw` on `Circle`
```

**Fix:** define the method in an `impl` block for the type.

### R0010 — Call on non-callable value

A call expression (`f(...)`) is applied to a value that is not a function or closure.

```
[R0010] runtime error in main.mtl at 3..8: call: expected a closure or builtin
```

### R0011 — Invalid for-in iterator

A `for x in expr` loop where `expr` does not evaluate to an `Array` or `Range`.

```
[R0011] runtime error in main.mtl at 1..20: for-in: expected Array or Range
```

**Fix:** ensure the iterable is an array literal, a range (`a..b`), or a variable of those types.

### R0012 — Error propagation on non-Result value

The `?` operator is applied to a value that is not a `Result`.

```
[R0012] runtime error in main.mtl at 5..10: ?: expected a Result value
```

**Fix:** only use `?` on expressions whose type is `Result[T, E]`.

> **Note:** this misuse is actually caught statically. `?` constrains its operand's
> type to `Result<T, E>` during type inference (`infer_propagate_error`), so a
> non-`Result` operand is rejected as a `T0001` type mismatch before the program
> ever runs. `R0012` does not appear in the interpreter's `RuntimeErrorCode` enum
> today and is unreachable in practice — kept here for the code number, not because
> the described runtime error can currently occur. (Found while investigating
> issue #232; not fixed as part of it, since removing a documented code is a
> separate decision from the yolo/conversion-method work that issue tracked.)

### R0013 — Assertion failed

`assert(cond)` or `assert_msg(cond, msg)` is called with `cond` evaluating to
`false`. The panic message is the fixed string `"assertion failed"` for `assert`,
or the caller-supplied `msg` for `assert_msg`.

```
[R0013] runtime error in main.mtl at 5..10: assertion failed
```

**Fix:** this is not a bug in the interpreter — it means the asserted condition
was actually false at runtime. Fix the condition, or the code that led to it.

### R0014 — Unwrap on `None`/`Err`

`.yolo()` is called on a `Perhaps<T>` that is `None`, or a `Result<T, E>` that is
`Err`. For `Result`, the panic message includes the `Err` value's debug
representation.

```
[R0014] runtime error in main.mtl at 5..10: called `.yolo()` on a `None` value
[R0014] runtime error in main.mtl at 5..10: called `.yolo()` on an `Err` value: "not found"
```

**Fix:** this is not a bug in the interpreter — `.yolo()` is meant only for cases
where `None`/`Err` represents a logic error that should never occur in correct
code. Use `match`, `.unwrap_or`, `.unwrap_or_else`, or (for `Result`) `?` to
handle the expected case instead.

### R0015 — Explicit panic

`panic(msg)` (RFC-0078) is called. Always panics unconditionally with `msg`.

```
[R0015] runtime error in main.mtl at 5..10: boom
```

**Fix:** this is not a bug in the interpreter — `panic` is meant for logic
errors that should never occur in correct code. Handle the expected case with
ordinary control flow instead of reaching the `panic` call.

---

## Internal errors (I)

### I0001 — Internal interpreter error

The interpreter reached an impossible state. This is a bug in the interpreter — the typechecker should have caught it before execution.

```
[I0001] internal error: binop: unsupported operand types (typechecker should have caught this)
```

**What to do:** please file a bug report at [the Metel issue tracker](https://codeberg.org/metel-lang/metel/issues) with the source program that triggered this error.

### I0002 — Not implemented

The program uses a language feature that is not yet supported in this version of the interpreter.

```
[I0002] internal error: generic functions are not supported in v0.1
```

**What to do:** check the [changelog](../release-notes/changelog.md) for the current supported feature set and the release plan for the planned implementation milestone.
