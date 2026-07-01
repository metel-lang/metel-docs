---
id: rfc-0079
title: "Perhaps<T> and Result<T, E>"
date: '2026-07-01'
---

> **Status — accepted.** Depends on RFC-0071 (Ownership and Move Semantics)
> and RFC-0078 (Bottom Type). Formally defines `Perhaps<T>` and `Result<T, E>` as
> built-in enum types with specified methods. Resolves RFC-0015 (Unwrap Syntax) in
> favour of the method form: `.yolo()` is a method, not a keyword. Specifies that
> `.yolo()` must be implemented as a proper method dispatch rather than a compiler
> or interpreter special case.

## Summary

`Perhaps<T>` (nullable) and `Result<T, E>` (fallible) are the two primary
sum types in Metel. Both are already in the language and the public spec, but
neither has a formal RFC specifying their definition, variants, or methods.
The current interpreter implements `.yolo()` as a special case rather than as
method dispatch on the types themselves. This RFC:

1. Formally defines both types as built-in enums.
2. Specifies their methods, including `.yolo()` as a proper method.
3. Resolves RFC-0015 in favour of the method form.
4. Specifies the `?` propagation operator for `Result<T, E>`.
5. Documents the implementation requirement to move from special-casing to
   method dispatch.

---

## 1. Type Definitions

Both types are built-in enums. They are defined conceptually as if they were
written in Metel source, but they are provided by the runtime and do not require
an import. Their variant names (`Perhaps::Some`, `Perhaps::None`, `Result::Ok`,
`Result::Err`) are accessible without qualification in all modules.

### 1.1 `Perhaps<T>`

```metel
enum Perhaps<T> {
    Some { value: T },
    None,
}
```

`Perhaps<T>` represents a value that may or may not be present. It is the only
way to express absence in Metel — there is no null. The `None` variant carries
no data; the `Some` variant wraps exactly one value of type `T`.

### 1.2 `Result<T, E>`

```metel
enum Result<T, E> {
    Ok  { value: T },
    Err { error: E },
}
```

`Result<T, E>` represents the outcome of a fallible operation. `Ok` carries the
success value; `Err` carries the error. Both variants use named fields.

---

## 2. Construction

### 2.1 `Perhaps<T>`

```metel
let present: Perhaps<i64> = Perhaps::Some { value: 42 };
let absent:  Perhaps<i64> = Perhaps::None;

// None is also available unqualified:
let absent2: Perhaps<i64> = None;
```

The unqualified `None` is syntactic sugar for `Perhaps::None`. The type of `None`
must be inferrable from context; a bare `let x = None` with no surrounding type
information is a type error.

### 2.2 `Result<T, E>`

```metel
let ok:  Result<i64, String> = Result::Ok  { value: 42 };
let err: Result<i64, String> = Result::Err { error: "something went wrong" };
```

No unqualified aliases are provided for `Ok` and `Err` — they must be qualified
with `Result::` to avoid ambiguity when both are in scope.

---

## 3. Pattern Matching

Pattern matching is the primary way to consume a `Perhaps<T>` or `Result<T, E>`.
Match arms must be exhaustive.

```metel
fun describe(x: Perhaps<i64>) -> String {
    match x {
        Perhaps::Some { value } => "got a value",
        Perhaps::None           => "nothing here",
    }
}

fun handle(r: Result<i64, String>) -> i64 {
    match r {
        Result::Ok  { value } => value,
        Result::Err { error } => {
            panic!(error);
        },
    }
}
```

For `Result<T, !>`, the `Err` arm is unreachable and may be omitted. See
RFC-0078 §4.2 for the exhaustiveness rule.

---

## 4. Methods on `Perhaps<T>`

### 4.1 `.yolo() -> T`

Unwraps the value, panicking if the variant is `None`.

```metel
fun find(id: i64) -> Perhaps<i64> { ... }

let x: i64 = find(42).yolo();
```

The panic message is implementation-defined but must include the call site.
`.yolo()` is appropriate when `None` is a logic error that should never occur
in correct code. It must not be used for expected error conditions — use
`match` or `.unwrap_or` instead.

### 4.2 `.is_some() -> boolean`

Returns `true` if the variant is `Some`, `false` if `None`.

### 4.3 `.is_none() -> boolean`

Returns `true` if the variant is `None`, `false` if `Some`.

### 4.4 `.unwrap_or(default: T) -> T`

Returns the contained value if `Some`, or `default` if `None`. The default
expression is evaluated eagerly — if the default is expensive to compute, use
`.unwrap_or_else` instead.

```metel
let val: i64 = find(42).unwrap_or(0);
```

### 4.5 `.unwrap_or_else(f: fun() -> T) -> T`

Returns the contained value if `Some`, or calls `f()` and returns its result
if `None`. The closure is called only when the value is absent.

```metel
let val: i64 = find(42).unwrap_or_else(fun() -> i64 { compute_default() });
```

### 4.6 `.map<U>(f: fun(T) -> U) -> Perhaps<U>`

Applies `f` to the contained value if `Some`, returning `Perhaps::Some { value: f(v) }`.
Returns `Perhaps::None` unchanged if `None`. The contained value is moved into `f`.

```metel
let doubled: Perhaps<i64> = find(42).map(fun(x: i64) -> i64 { x * 2 });
```

### 4.7 `.ok_or<E>(error: E) -> Result<T, E>`

Converts `Perhaps<T>` to `Result<T, E>`. `Some { value }` becomes `Ok { value }`;
`None` becomes `Err { error }`.

```metel
let result: Result<i64, String> = find(42).ok_or("not found");
```

---

## 5. Methods on `Result<T, E>`

### 5.1 `.yolo() -> T`

Unwraps the `Ok` value, panicking with the `Err` value's debug representation if
the variant is `Err`.

```metel
fun parse(s: String) -> Result<i64, String> { ... }

let x: i64 = parse("42").yolo();
```

As with `Perhaps::yolo()`, this is appropriate only when `Err` represents a
logic error. Propagate errors with `?` or handle them with `match`.

### 5.2 `.is_ok() -> boolean`

Returns `true` if the variant is `Ok`.

### 5.3 `.is_err() -> boolean`

Returns `true` if the variant is `Err`.

### 5.4 `.map<U>(f: fun(T) -> U) -> Result<U, E>`

Applies `f` to the `Ok` value, leaving `Err` unchanged.

```metel
let doubled: Result<i64, String> = parse("21").map(fun(x: i64) -> i64 { x * 2 });
```

### 5.5 `.map_err<F>(f: fun(E) -> F) -> Result<T, F>`

Applies `f` to the `Err` value, leaving `Ok` unchanged. Useful for converting
between error types.

```metel
let r: Result<i64, MyError> = parse("42").map_err(fun(s: String) -> MyError { MyError { msg: s } });
```

### 5.6 `.ok() -> Perhaps<T>`

Converts `Result<T, E>` to `Perhaps<T>`. `Ok { value }` becomes
`Perhaps::Some { value }`; `Err` becomes `Perhaps::None`. The error value is
discarded.

```metel
let maybe: Perhaps<i64> = parse("42").ok();
```

---

## 6. The `?` Propagation Operator

`?` applied to a `Result<T, E>` expression inside a function returning
`Result<U, E>` (for any `U`, same `E`) evaluates to `T` if the result is `Ok`,
or immediately returns `Err { error }` from the enclosing function if `Err`.

```metel
fun read_and_parse(s: String) -> Result<i64, String> {
    let n: i64 = parse(s)?;   // propagates Err; binds T on Ok
    Result::Ok { value: n * 2 }
}
```

The desugaring is:

```metel
let n: i64 = match parse(s) {
    Result::Ok  { value } => value,
    Result::Err { error } => return Result::Err { error },
};
```

`?` on `Perhaps<T>` inside a function returning `Perhaps<U>` propagates `None`
the same way:

```metel
fun double_found(id: i64) -> Perhaps<i64> {
    let x: i64 = find(id)?;   // propagates None; binds T on Some
    Perhaps::Some { value: x * 2 }
}
```

The desugaring:

```metel
let x: i64 = match find(id) {
    Perhaps::Some { value } => value,
    Perhaps::None           => return Perhaps::None,
};
```

`?` requires the enclosing function's return type to match the propagated error
or absence type. Using `?` on `Result<T, E1>` inside a function returning
`Result<U, E2>` where `E1 ≠ E2` is a type error — the types must match or an
explicit `.map_err` must bridge them first.

---

## 7. Resolves RFC-0015

RFC-0015 asked whether `.yolo()` should be a method or a keyword. This RFC
resolves the question in favour of the **method form**:

- `.yolo()` is a regular method defined on `Perhaps<T>` and `Result<T, E>`.
- There is no `yolo` keyword.
- The method form is consistent with `.map`, `.unwrap_or`, and other methods on
  these types.
- The typechecker handles `.yolo()` via standard method dispatch, not as a
  compiler special case.

RFC-0015 is superseded by this RFC.

---

## 8. Implementation Note

The current interpreter implements `.yolo()` as a special case rather than as
method dispatch on the types. This RFC requires that to change:

- `Perhaps<T>` and `Result<T, E>` must have their methods registered in the
  interpreter's method dispatch table.
- `.yolo()` must be callable as a normal method call — the interpreter should
  not check for the literal string `"yolo"` and branch on it.
- All other methods in §4 and §5 must be implemented as dispatched methods, not
  built-in special cases.

The type definitions in §1 are built-in and do not require source-level parsing.
Their variants must be registered so that `Perhaps::Some`, `Perhaps::None`,
`Result::Ok`, `Result::Err` are resolvable without an import.

---

## Unresolved Questions

1. **`.yolo()` rename.** RFC-0020 deferred the rename of `.yolo()`. This RFC
   keeps the name as-is. A future RFC may rename it; when it does, the new name
   simply replaces the method name specified here.

2. **Error type conversion with `?`.** Whether `?` should support automatic error
   conversion (analogous to Rust's `From` trait) — allowing `?` on `Result<T, E1>`
   inside `Result<U, E2>` when `E1` is convertible to `E2` — is deferred. The
   current specification requires exact type match.

3. **`.yolo()` panic message format.** The exact format of the panic message is
   left to the implementation. A future RFC may standardise it.

4. **`Perhaps<T>` and `?` in `Result`-returning functions.** Whether `?` on a
   `Perhaps<T>` inside a `Result`-returning function (converting `None` to a
   default error) is supported is deferred.

---

## References

- RFC-0015 (Unwrap Syntax) — superseded by this RFC; the decision is method form.
- RFC-0020 (Language Rebranding) — `.yolo()` rename deferred; still pending.
- RFC-0071 (Ownership and Move Semantics) — move semantics of `T` inside `Perhaps`
  and `Result`; `.map()` moves the contained value.
- RFC-0078 (Bottom Type) — `Result<T, !>` collapse; `!` as `AllocationError`;
  exhaustiveness of `Err` arm when `E = !`.
- Public spec `types.md §Perhaps` and `§Result` — existing user-facing
  description; this RFC is the normative backing for that section.
