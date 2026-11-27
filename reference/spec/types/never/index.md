---
sidebar_position: 18
---

# Never Type

`!` (Never) is the **uninhabited bottom type** — no value of type `!` can ever be
constructed. A `loop` with no reachable `break` has type `!`:

```metel
fun main() -> i64 {
    let result: i64 := loop { break 42; };
    return result;
}
```

`return <expr>`, `panic(<message>)`, `loop { }` with no reachable `break`, and `break`/`continue` used as value expressions in loop context all have type `!`. If any sub-expression has type `!`, that sub-expression diverges before the outer expression can produce a value, so the outer expression's type is unconstrained and any type is accepted in that position.

## Subtyping and coercion

`!` is a subtype of every type — `! <: T` for all `T` — so an expression of type `!` coerces implicitly, with no cast, to any context expecting `T`. This is what makes the rule above sound: code after a diverging expression is unreachable, but still typechecks against whatever its context requires.

## Match exhaustiveness

A `match` whose scrutinee has type `!` needs no arms — an empty match is vacuously exhaustive, since no value of type `!` can ever reach it:

```metel
fun unreachable_code(x: !) -> i64 {
    match x { }   // exhaustive — no arms needed
}
```

More generally, an enum variant whose payload type is `!` is uninhabited — no value of that variant can ever be constructed — and a `match` may omit the arm for an uninhabited variant while remaining exhaustive:

```metel
enum Foo {
    A { x: i64 },
    B { y: ! },
}

fun handle(f: Foo) -> i64 {
    match (f) {
        Foo::A { x } => x,
        // Foo::B omitted — exhaustive; B is uninhabited
    }
}
```

## Inhabited-singleton coercion

If an enum has exactly one inhabited variant (every other variant's payload is `!`) and that variant has exactly one field, a value of the enum type coerces implicitly to the field's type — the compiler inserts the destructuring, no explicit `match` required:

```metel
enum Wrapper<T> {
    Present { value: T },
    Absent  { _: ! },
}

fun infallible() -> Wrapper<i64> { Wrapper::Present(value = 42) }

fun main() -> i64 {
    let x: i64 := infallible();  // implicit coercion via the inhabited-singleton rule
    return x;
}
```

`Result<T, !>` satisfies this: `Ok { value: T }` is the one inhabited variant with one field, so a `Result<T, !>`-returning function's caller can use the result as a plain `T` with no `match`. `Option<!>` does **not** satisfy it — `None` is inhabited but has zero fields — so `Option<!>` never coerces implicitly to anything, though nothing prevents it from arising through generic instantiation.
