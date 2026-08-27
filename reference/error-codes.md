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

> **Note:** neither route to this message is currently reachable. The grammar has no
> exponent notation, so `1e9999` above is actually `P0001`; a literal long enough to
> overflow `f64` in plain decimal notation silently saturates to infinity instead of
> erroring.

---

## Type errors (T)

### T0001 — Type mismatch, or an impl that is not allowed

Two types that must be equal are not.

```
[T0001] type error in main.mtl at 10..20: expected i64, got boolean
```

**Fix:** ensure the expression produces the expected type. Add an explicit cast if widening (e.g. `x as f64`).

The same code also covers an `extend` block the language does not permit, which is a
distinct situation sharing one code:

- a target that cannot carry the impl at all — `extend { … }: Drop` on an anonymous record;
- a target with nowhere to register, so its methods could never be found — a tuple, an
  anonymous record, a `fun` type, or an array whose element is not one of the impl's own
  type parameters. Only `extend<T> T[]: Aspect` — the array's element spelled exactly as
  one of the impl's own generics — is implemented today;
- a `drop` body, while destructor invocation is not yet implemented.

```
[T0001] type error in main.mtl at 3..9: cannot `extend` a tuple type: this block's methods could never be found. To fix it, use a named struct
```

**Fix:** each message names the way forward — usually a named struct, or the generic form
where one exists.

### T0002 — Annotation required

The type checker cannot infer a type without an explicit annotation.

```
[T0002] type error in main.mtl at 5..10: cannot infer type of `x`; add a type annotation
```

**Fix:** annotate the binding: `let x: i64 = ...`.

The same code also covers dereferencing (`*expr`) an operand that isn't a reference type at
all — not an inference gap, but sharing the code with the annotation case above since both
are "the checker has nothing to work with here":

```
[T0002] type error in main.mtl at 5..10: cannot dereference non-pointer type `i64`
```

**Fix:** remove the `*`, or check that the operand actually has reference type (`&T` / `&var T`).

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

An operator is applied to operands it does not support. Three forms share this code:

- **Mismatched operands.** The two sides of a binary operator disagree, e.g. `1 == "x"`.
  The message names the operator and both types.
- **Binary arithmetic/ordering** on unsupported types.
- **Equality** (`==`, `!=`) on anything other than a numeric type, `boolean`, `String` or
  `char`. `==` does not yet dispatch through the `Eq` aspect, so structs, enums, arrays,
  tuples and references are rejected; use `.eq(..)` on a type that implements `Eq`.

> **Since v0.12.0:** address-of (`&`, `&var`) applied to a non-addressable expression — a
> literal, a call result, a struct/enum construction — is no longer one of this code's
> cases. Both forms now get temporary lifetime extension instead of being rejected; see
> [Expressions — References](spec/expressions.md#references).

```
[T0005] type error in main.mtl at 6..13: operator `+` cannot be applied to boolean and i64
```

**Fix:** use compatible types, cast one operand, or bind the value to a name so it has an
address.

### T0006 — Assignment to immutable binding

A write operation targets a `let` binding. This covers three forms:

- Direct reassignment: `x = newValue`
- Field assignment through an immutable binding: `point.x = 1`
- Taking a mutable reference to an immutable binding: `&var x`

```
[T0006] type error in main.mtl at 3..12: `x` is immutable; use `var x` to allow reassignment
```

**Fix:** change the binding declaration to `var`.

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

### T0012 — Aspect bound not satisfied

A generic type parameter's bound is not satisfied by the concrete type at the call
site or construction site. Covers both directions: a positive bound (`T: Aspect`)
requires an implementation that isn't reachable, or a negative bound (`T: !Aspect`,
RFC-0072) is violated because the concrete type *does* implement the aspect. Also
covers a conditional `extend` block's own `where`-clause bounds (RFC-0036) failing at a
use site — the same check as an ordinary function bound, just reached through an
implementation block's
condition instead of a function's generic parameter.

```
[T0012] type error in main.mtl at 5..15: `i64` does not implement `Display` (required by `show`)
[T0012] type error in main.mtl at 8..20: `Handle` implements `Drop`; `!Drop` bound not satisfied (required by `move_out`)
[T0012] type error in main.mtl at 3..12: `Pair<i64, SomeNonPrintable>` does not implement `Printable`, because `SomeNonPrintable` does not implement `Printable`
```

A type satisfying `T: Copy` automatically satisfies `T: !Drop` (RFC-0072 §2.3) even
though it implements `Drop` — this is a narrow, Copy/Drop-specific exception, not a
general rule.

**Fix:** implement the required aspect for the type, or (for a negative bound) remove
the conflicting positive implementation.

### T0013 — Ambiguous aspect method/associated-type resolution

Two different aspects define the same method name on the same receiver type, so a
call like `value.method()` does not have a unique static target — or (RFC-0082 §3a)
two different aspects bound on the same generic type parameter both declare an
associated type of the same name, so a bare projection like `T::AssocName` doesn't
have a unique target either.

```
[T0013] type error in main.mtl at 12..20: ambiguous aspect method `label` on type `S`: both `A` and `B` provide this method
[T0013] type error in main.mtl at 8..16: ambiguous associated type `Target`: multiple aspects declare it: Deref, Convert
```

**Fix (method case):** rename one of the methods, remove one of the conflicting impls,
or change the design so the receiver type does not expose two indistinguishable
aspect methods.

**Fix (associated-type case):** bind the associated type to a fresh type parameter via
an equality-constrained bound instead of projecting it directly — e.g.
`fun f<T: Deref<Target = U> + Convert, U>(x: &T) -> U` — which resolves unambiguously
since `U` is an ordinary type parameter, not a projection.

### T0014 — Orphan implementation

An `extend Type: Aspect` block where neither `Aspect` nor `Type`'s outermost type
constructor is declared in the current module (or `std::core`, for built-ins).

```
[T0014] type error in main.mtl at 1..40: orphan implementation: neither `Display` nor `i64` is local to this module
```

**Fix:** move the `extend` block into the module that declares the aspect or the type, or (for
two foreign types) into `std::core` if this is genuinely a standard-library concern.

### T0015 — Conflicting implementation

Two implementations of the same aspect cover the same concrete type — either two
identical `extend` blocks, or a positive and a negative impl (see Negative Impls in the declarations
reference) for the same concrete type.

```
[T0015] type error in main.mtl at 1..40: conflicting implementation: `Display` is already implemented for `List<i64>` at 10..30
```

**Fix:** remove the duplicate `extend` block, or narrow one block's type arguments so the two no
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

### T0017 — Missing associated type definition

An `extend Type: Aspect` block omits a `type Name = ConcreteType;` definition for an
associated type the aspect declares (RFC-0082 §2). Every implementation of an aspect with
associated types must define all of them.

```
[T0017] type error in main.mtl at 1..40: `IntBox` is missing associated type `Item` required by aspect `Container`
```

**Fix:** add the missing `type Item = ConcreteType;` definition to the `extend` block.

---

### T0018 — Naming the concrete type of an opaque return value

A function returning `impl Aspect` (RFC-0037) hides its concrete return type. Using the
result in a position that pins it to a specific type — annotating it, or unifying it with a
concrete type — defeats that, and is rejected.

```
[T0018] type error in main.mtl at 1..40: cannot name the concrete type of an opaque `impl Aspect` return value; use `impl Aspect` or a generic bound instead (resolved to `i64`)
```

**Fix:** keep the value opaque — annotate it as `impl Aspect` too, or accept it through a
generic parameter with the same bound.

---

### T0019 — Use of moved value

> **Since v0.12.0, under `--move-check` only.** Move checking is off by default in this release.

An ownership rule from RFC-0071 §1/§7 was violated. Seven distinct situations share this
code, each with its own message:

- a value used after it was moved;
- a partially moved value used as a whole;
- a partial move out of a type that implements `Drop`, which is never allowed;
- a move out of an array element, which is banned outright;
- a move of a non-`Copy` element out of a borrowed `T[]` view;
- a `&var` binding moved by a use that is not a reborrow;
- a value moved out of a reference — by calling a by-value `self` method through it,
  in general assignment or by-value argument position, or by reading a field through it
  with no explicit `*` at all. A reference only grants access, never ownership, so its
  pointee cannot be moved out this way, unless the pointee's own type is `Copy` (in which
  case the read is a copy, exactly as `T: Copy` already permits at read-copy positions
  per §3a).

Each message names the binding and the location of the move. When the move happened on an
earlier iteration of an enclosing loop, the message says so — a loop-carried move is
usually the *same* expression as the use, one iteration later, so naming only its location
would point back at the line you are already reading.

```
[T0019] type error in main.mtl at 30..40: use of moved value `p`: `p` was moved at main.mtl:30:14
[T0019] type error in main.mtl at 12..20: cannot partially move value `h`: `h.name` belongs to a `Drop` type
[T0019] type error in main.mtl at 8..14: cannot move from `xs[0]`: array element moves are not allowed
[T0019] type error in main.mtl at 62..70: use of moved value `s`: `s` was moved here on an earlier iteration
[T0019] type error in main.mtl at 40..48: cannot move `(*r)` out of a reference: a reference only grants access to the value it points at, never ownership of it
```

**Fix:** depending on the rule — borrow instead of moving (`&x`), clone the value, move the
whole value rather than a field of a `Drop` type, or index-and-copy rather than moving an
element out of an array.

---

### T0021 — `break`/`continue` with no enclosing loop

`break` or `continue` appeared with no enclosing loop of any kind (`loop`, `while`, `for`,
or `for-in`) to bind to. This includes a `break`/`continue` written inside a closure body
— a closure is never considered to be "inside" whatever loop happens to lexically
surround its definition, since the closure may be called long after that loop has exited,
or from somewhere the loop never ran at all.

```
[T0021] type error in main.mtl:2:20: `break` used with no enclosing loop
[T0021] type error in main.mtl:3:23: `continue` used with no enclosing loop
```

**Fix:** remove the keyword, or move it inside the loop it is meant to control. If it is
meant to control a loop that encloses the *call site* of a closure rather than the
closure's own definition, restructure the code — a closure cannot break or continue a
loop it does not itself contain.

---

### T0022 — `impl Aspect` outside parameter or return position

`impl Aspect` was written somewhere other than a function parameter's type or a
function's return type — for example, a `let`/`var` annotation, a struct or enum
variant field, a cast target (`x as impl P`), or a generic bound. Parameter position is
lowered to a fresh bounded type parameter, and return position is RFC-0037's opaque
return type; every other position is not part of this language version.

```
[T0022] type error in main.mtl:2:12: `impl Aspect` is only allowed in parameter or return position
```

**Fix:** name a concrete type instead, or restructure the code so the aspect bound is
expressed through a parameter or return type.

---

### T0023 — Assignment through a non-owning view

An index assignment targets a `T[]` value. Since RFC-0126, `T[]` is an unconditionally
`Copy`, non-owning view — it never grants write access through its indices, independent
of whether the binding holding it is `let` or `var`. This is a different failure shape
than T0006 (all three of T0006's forms are about a `let` binding that declaring it `var`
would fix); no annotation or binding-mutability change can fix this one.

```
[T0023] type error in main.mtl:3:5: cannot assign through `T[]`: array views are immutable; use `[T; N]` or `List<T>`
```

**Fix:** use `[T; N]` (a fixed-size array) or `List<T>` (a growable, owned collection)
instead of `T[]` for storage that needs index-write access.

---

### T0024 — Read-copy of a non-`Copy` value out of a reference

> **Since v0.12.1.**

RFC-0067a §3a's "read-copy": a `let`/`mut` binding, `return`/`break` value, tail
expression, or explicit ascription (`expr: T`) whose own declared type differs from
its initializer's reference type (`&U`/`&var U`) implicitly copies the referent out —
but only when `U` is `Copy`. A reference only grants access, never ownership, so
reading a non-`Copy` value out this way would silently duplicate it with no move and
no explicit clone.

<!-- doc-example: expect-fail reason="demonstrates T0024 -- the whole point of this entry" -->
```metel
struct NotCopy { v: String }

fun main() {
    let owned = NotCopy { v = "x" };
    let r: &NotCopy = &owned;
    let copy: NotCopy = r;   // T0024 — NotCopy is not Copy
}
```

```
[T0024] type error in main.mtl:6:5: cannot copy `NotCopy` out of a reference: `NotCopy` does not implement `Copy`
       hint: use `.clone()` if `NotCopy` implements `Clone`, or restructure to take ownership instead
```

Checked once against the fully-dereferenced type at the end of a reference chain, not
each intermediate layer — `let x: i64 = rr;` where `rr: &&i64` is unaffected, since
`i64` is `Copy` regardless of how many reference layers it's read through.

**Fix:** call `.clone()` if the type implements `Clone`, or restructure the code to
take ownership of the value directly instead of reading it through a reference.

---

## Runtime errors (R)

### R0001 — No `main` function defined

Execution requires a `main` function but none was found.

```
[R0001] runtime error in main.mtl at 0..0: no main() function defined
```

**Fix:** add `fun main() { ... }` to your program.

### R0002 — `main` is not a valid entry point

`main` exists but is generic or is not a function.

```
[R0002] runtime error in main.mtl at 0..0: main() body could not be typed
```

**Fix:** `main` must be a concrete, non-generic function with no parameters.

> **Note:** also raised for a generic closure invoked with no call-site type context,
> with a different message — this entry covers the `main` case only.

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

> **Note:** not confirmed reachable from ordinary source. A tuple index is always a
> literal token, never a computed expression, so an out-of-range index was caught as
> `T0003` statically in every construction tried. Unlike `P0003` above, the raise site
> is real code — just unconfirmed.

### R0006 — Non-exhaustive match at runtime

A `match` expression reached its end without any arm matching. This indicates a pattern that the type checker approved as exhaustive but that is not, which is a known limitation.

```
[R0006] runtime error in main.mtl at 2..30: match: no arm matched scrutinee
```

### R0007 — Arithmetic error

Integer division or remainder by zero, **or** integer overflow on `+`, `-`, `*`, or
`/` (RFC-0007 D3, amended 2026-08-26 — panics unconditionally in every build; there
is no debug/release distinction). Floating-point arithmetic never raises this code —
float overflow and division by zero follow IEEE 754 (`inf`/`-inf`/`NaN`), never a
panic.

```
[R0007] runtime error in main.mtl at 8..13: division by zero
[R0007] runtime error in main.mtl at 4..11: integer overflow
```

**Fix:** guard with a zero check before dividing, or ensure operands stay in range
before an operation that could overflow.

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

**Fix:** define the method in an `extend` block for the type.

### R0010 — Call on non-callable value

A call expression (`f(...)`) is applied to a value that is not a function or closure.

```
[R0010] runtime error in main.mtl at 3..8: call: expected a closure or builtin
```

### R0011 — Invalid for-in iterator

A `for x in expr` loop where `expr` does not evaluate to an `Array`, a `Range`, or a type
implementing `Iterable`.

```
[R0011] runtime error in main.mtl at 1..20: for-in: expected Array or Range
```

**Fix:** ensure the iterable is an array literal, a range (`a..b`), a value of those types,
or a type with its own `Iterable` implementation (see `expressions.md`, "for-in").

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
> issue #536; not fixed as part of it, since removing a documented code is a
> separate decision from the yolo/conversion-method work that issue tracked.)

### R0013 — Assertion failed

`assert(cond)` or `assert(cond, msg)` is called with `cond` evaluating to
`false`. The panic message is the fixed string `"assertion failed"` for the
one-argument form, or the caller-supplied `msg` for the two-argument form.

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

**What to do:** please file a bug report at [the Metel issue tracker](https://github.com/metel-lang/metel-core/issues) with the source program that triggered this error.

### I0002 — Not implemented

The program uses a language feature that is not yet supported in this version of the interpreter.

```
[I0002] internal error: generic functions are not supported in v0.1
```

**What to do:** check the [changelog](../release-notes/changelog.md) for the current supported feature set and the release plan for the planned implementation milestone.
