---
id: rfc-0078
title: "Bottom Type — `!`"
date: '2026-07-01'
---

> **Status — under review.** Depends on RFC-0071 (Ownership and Move Semantics).
> Formally specifies `!` as the bottom of the type hierarchy: its subtyping rule,
> coercion behaviour, match exhaustiveness implications, and the `Result<T, !>`
> collapse rule that underpins infallible region allocation (RFC-0063 §1.1).

## Summary

`!` (pronounced "never") is already in the language as the inferred type of diverging
expressions. This RFC gives it a formal specification: `!` is the **uninhabited bottom
type** — no value of type `!` can ever be constructed. As the bottom of the type
hierarchy, `!` is a subtype of every type. This subtyping rule has two important
consequences: expressions of type `!` coerce freely to any type, and `Result<T, !>`
collapses to `T` because the `Err` variant is uninhabited and unreachable.

---

## 1. Definition

`!` is a type with no inhabitants. No expression can produce a value of type `!`
without the program diverging (looping forever, panicking, or exiting). `!` can
appear in any type position: as a return type, a type parameter, a field type, or
an error type in `Result<T, E>`.

### 1.1 Subtyping

`!` is a subtype of every type:

```
! <: T    for all types T
```

This is the standard definition of a bottom type. It means any expression of type
`!` is valid in any context that expects any type `T`. The coercion is implicit and
requires no cast.

### 1.2 Uninhabitedness

Since `!` has no inhabitants, any code after a diverging expression is unreachable.
The compiler may emit an unreachable-code warning but must still typecheck it. The
unreachable code has whatever type its context requires — the `! <: T` rule makes
this sound.

---

## 2. Expressions of Type `!`

The following expressions have type `!`:

| Expression | Condition |
|---|---|
| `return <expr>` | In any function body |
| `panic!(<message>)` | Always |
| `loop { }` | When the loop has no reachable `break` |
| `break` / `continue` | In loop context (type `!` as a value expression) |
| A variable binding of type `!` | Vacuously — bindings of type `!` are never reached |

If any sub-expression in a larger expression has type `!`, that sub-expression
diverges before the outer expression can produce a value. The outer expression's type
is therefore unconstrained and the compiler accepts any type in that position.

---

## 3. Match Exhaustiveness

### 3.1 Matching on `!`

A `match` expression whose scrutinee has type `!` requires no arms. An empty match
is vacuously exhaustive because no value of type `!` can reach it:

```metel
fun unreachable_code(x: !) -> i64 {
    match x { }   // exhaustive — no arms needed
}
```

### 3.2 Unreachable arms

A match arm whose pattern has type `!` is unreachable. The compiler may warn but
must not reject it. This applies to:

- An `Err { error }` arm in a `match result: Result<T, !>` — the `Err` variant
  cannot be constructed, so the arm is dead.

### 3.3 Inference through match

If all arms of a `match` expression diverge (have type `!`), the overall `match`
expression has type `!`.

---

## 4. `Result<T, !>` — Infallible Results

When `E = !`, the `Err` variant of `Result<T, E>` is uninhabited. A
`Result<T, !>` can only ever be `Result::Ok { value }`. The compiler applies the
**infallible result rule**:

> A `Result<T, !>` is treated as equivalent to `T` at the type level. It may be
> used wherever `T` is expected without an explicit match.

### 4.1 Implicit unwrap

A `Result<T, !>` value coerces implicitly to `T`:

```metel
fun infallible() -> Result<i64, !> {
    Result::Ok { value: 42 }
}

fun main() -> i64 {
    let x: i64 = infallible();  // implicit coercion — no match needed
    x
}
```

The compiler inserts a conceptual `match result { Ok { value } => value }` during
lowering. Since the `Err` arm is uninhabited, it is never generated.

### 4.2 Partial match

A `match` on `Result<T, !>` that omits the `Err` arm is exhaustive:

```metel
fun use_result(r: Result<i64, !>) -> i64 {
    match r {
        Result::Ok { value } => value,
        // Err arm omitted — compiler accepts this; Err is uninhabited
    }
}
```

The compiler does not require the `Err` arm and does not warn about its absence.
If the `Err` arm is written explicitly, the compiler warns that it is unreachable.

### 4.3 `AllocationError = !` (RFC-0063)

RFC-0063 gives each region a `type AllocationError`. When a region sets
`AllocationError = !` (as all stdlib regions do), the `@[r] expr` allocation
expression has type `@[r] T` — not `Result<@[r] T, !>`. This is the infallible
result rule applied at the allocation expression site: the compiler sees
`Result<@[r] T, !>` in the intermediate type and collapses it to `@[r] T` before
surfacing it to the programmer.

Fallible custom allocators (where `AllocationError = SomeError`) produce
`Result<@[r] T, SomeError>` and require the caller to handle or propagate the error.

---

## 5. `Perhaps<T>` and `!`

`Perhaps<!>` is a type with only one inhabited variant: `Perhaps::None`. The
`Some` variant would require a value of type `!`, which cannot be constructed.
This type is not practically useful and the compiler may warn when it appears in
user-written code. It is not prohibited — it can arise from generic instantiation.

---

## 6. `!` as a Return Type

A function annotated `-> !` promises never to return:

```metel
fun abort(msg: String) -> ! {
    panic!(msg)
}
```

Such a function must diverge on all code paths. The compiler verifies this: every
control-flow path must end in a diverging expression. A function annotated `-> !`
that contains a reachable `return` is a type error.

---

## 7. Alternatives Considered

### Treating `!` as a special compiler internal

The current implementation infers `!` for diverging expressions without exposing
it as a first-class type. This works for the basic cases but cannot express
`Result<T, !>` collapse or `-> !` return types without special-casing each site.
Making `!` a proper type with a formal subtyping rule is the uniform solution.

### A `Never` named type

Some languages use a named type (`Never`, `Void`, `Nothing`) rather than `!`.
Metel uses `!` for consistency with the existing spec and the `AllocationError = !`
convention already established in RFC-0063.

---

## Unresolved Questions

1. **`!` in generic bounds.** Whether `T: !` is a meaningful bound (asserting `T`
   is uninhabited) is deferred. The practical need is low.

2. **Coercion precedence.** When both an implicit `Result<T, !>` coercion and
   another coercion are applicable, the resolution order is deferred to the
   type inference RFC.

---

## References

- RFC-0063 (Region Handles) — `AllocationError = !`; infallible allocation;
  `Result<@[r] T, !>` collapse at allocation sites.
- RFC-0071 (Ownership and Move Semantics) — move semantics; `!` values are never
  moved (they cannot be constructed).
- RFC-0079 (Perhaps and Result) — formal definitions of `Perhaps<T>` and
  `Result<T, E>`; methods including `.yolo()`; depends on this RFC for
  `Result<T, !>` semantics.
- Public spec `types.md §Never Type` — existing description of `!` as the type
  of diverging expressions; this RFC formalises that description.
