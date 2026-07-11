---
id: rfc-0078
title: "Bottom Type — `!`"
date: '2026-07-01'
status: integrated
updated: '2026-07-10'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/234'
impl_status: not-started
---

> **Status — accepted.** Depends on RFC-0071 (Ownership and Move Semantics).
> Formally specifies `!` as the bottom of the type hierarchy: its subtyping rule,
> coercion behaviour, and match exhaustiveness implications. Establishes the general
> uninhabited-variant rule and the inhabited-singleton coercion rule that together
> underpin infallible region allocation (RFC-0063 §1.1).
>
> **Amended 2026-07-10, while integrating into the spec.** §4.2's terminology corrected
> — it still used pre-split "region"/`@[r]` bracket-channel syntax and RFC-0063's old
> title ("Region Handles"), predating the 2026-07-05 allocator/lifetime split. Semantic
> content unchanged.

> **Status — integrated (2026-07-10).** Integrated into public/reference/spec/types.md: ! subtyping, coercion, match exhaustiveness, inhabited-singleton coercion, and -> ! return type. RFC's own stale @[r] allocator syntax fixed first.

## Summary

`!` (pronounced "never") is already in the language as the inferred type of diverging
expressions. This RFC gives it a formal specification: `!` is the **uninhabited bottom
type** — no value of type `!` can ever be constructed. As the bottom of the type
hierarchy, `!` is a subtype of every type. This has three normative consequences:
expressions of type `!` coerce freely to any type; any enum variant whose payload
contains `!` is uninhabited and may be omitted from match exhaustiveness; and any enum
with exactly one inhabited variant that has exactly one field implicitly coerces to
that field's type (the inhabited-singleton coercion rule). `Result<T, !>` satisfies
all three as a special case of the general rules.

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

### 3.2 Uninhabited variants

A general rule: an enum variant whose payload type is `!` is uninhabited. No value
of that variant can ever be constructed. A match arm for an uninhabited variant is
unreachable — the compiler may warn but must not reject it; the arm need not be
written for the match to be exhaustive.

This applies to any enum, not only to `Result`. If a user defines:

```metel
enum Foo {
    A { x: i64 },
    B { y: ! },
}
```

then `Foo::B` is uninhabited, and a match on `Foo` that omits the `B` arm is
exhaustive. The rule follows from `!` being uninhabited and applies wherever `!`
appears as a variant's payload type, regardless of the surrounding type.

### 3.3 Inhabited-singleton coercion

If an enum type has exactly one inhabited variant (all other variants are uninhabited
per §3.2), and that inhabited variant has exactly one field, a value of that enum type
implicitly coerces to that field's type. The compiler inserts the destructuring; no
explicit match is required at the use site.

Conditions for the rule to apply:
1. The enum has more than one variant.
2. Exactly one variant is inhabited; all others have a payload type of `!`.
3. The inhabited variant has exactly one field (any name).

```metel
enum Wrapper<T> {
    Present { value: T },
    Absent  { _: ! },
}

fun infallible() -> Wrapper<i64> { Wrapper::Present { value: 42 } }

let x: i64 = infallible();  // implicit coercion via inhabited-singleton rule
```

If the single inhabited variant has zero fields or more than one field, the rule does
not apply — there is no single type to coerce to.

`Result<T, !>` satisfies the conditions: `Ok { value: T }` is the one inhabited
variant with one field; `Err { error: ! }` is uninhabited. See §4.1.

`Perhaps<!>` does not satisfy the conditions: `None` is inhabited but has zero fields.
`Perhaps<!>` does not implicitly coerce to any type.

### 3.4 Inference through match

If all arms of a `match` expression diverge (have type `!`), the overall `match`
expression has type `!`.

---

## 4. `Result<T, !>` — Consequences of Uninhabitedness

When `E = !`, the `Err` variant of `Result<T, E>` is uninhabited by the general rule
in §3.2. A `Result<T, !>` can only ever be `Result::Ok { value }`.

### 4.1 Coercion and exhaustiveness

`Result<T, !>` satisfies the inhabited-singleton coercion rule (§3.3): `Ok` is the
one inhabited variant and has exactly one field. A `Result<T, !>` value may therefore
be used wherever `T` is expected with no explicit match:

```metel
fun infallible() -> Result<i64, !> {
    Result::Ok { value: 42 }
}

fun main() -> i64 {
    let x: i64 = infallible();  // implicit coercion — no match needed
    x
}
```

A match that omits the `Err` arm is exhaustive (§3.2). If the `Err` arm is written,
the compiler warns that it is unreachable:

```metel
fun use_result(r: Result<i64, !>) -> i64 {
    match r {
        Result::Ok { value } => value,
        // Err arm omitted — exhaustive; Err is uninhabited
    }
}
```

### 4.2 `AllocationError = !` (RFC-0063)

RFC-0063 gives each allocator a `type AllocationError`. When an allocator sets
`AllocationError = !` (as all stdlib allocators do), the `@a expr` allocation
expression has type `@a T` — not `Result<@a T, !>`. This is a rule on the
allocation expression itself: the type of `@a expr` is determined by the allocator's
`AllocationError` type, and when that type is `!` the expression directly produces
`@a T`. This is distinct from a post-hoc coercion from `Result<@a T, !>` to
`@a T`; no coercion is needed because the `Result` wrapper is never surfaced.

Fallible custom allocators (where `AllocationError = SomeError`) produce
`Result<@a T, SomeError>` and require the caller to handle or propagate the error.

> Terminology corrected 2026-07-10, while integrating into the spec: this section
> originally used pre-split "region"/`@[r]` bracket-channel syntax throughout. RFC-0063
> moved to allocator/`@a` tag-based syntax on 2026-07-05; the semantic content here
> (infallible-allocation collapse) is unchanged, only the notation was stale.

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

2. **Coercion precedence.** When the inhabited-singleton coercion (§3.3) and another
   coercion are both applicable at a use site, resolution order is deferred to the
   type inference RFC.

---

## References

- RFC-0063 (Allocator Handles) — `AllocationError = !`; infallible allocation;
  `Result<@a T, !>` collapse at allocation sites.
- RFC-0071 (Ownership and Move Semantics) — move semantics; `!` values are never
  moved (they cannot be constructed).
- RFC-0079 (Perhaps and Result, refused 2026-07-10 — most of its content was already
  implemented/spec'd by the time it was written; real remaining gaps tracked at
  https://app.clickup.com/t/86cap1wzb) — `Result<T, !>`'s exhaustiveness and the
  inhabited-singleton collapse this RFC specifies (§3.3-§4.1) are what actually govern
  `Result<T, !>`'s relationship to `!`; unaffected by RFC-0079's refusal.
- Public spec `types.md §Never Type` — existing description of `!` as the type
  of diverging expressions; this RFC formalises that description.
