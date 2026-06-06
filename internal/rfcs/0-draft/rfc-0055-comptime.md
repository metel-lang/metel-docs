---
id: rfc-0055
title: "Comptime"
date: '2026-06-05'
status: draft
---

## Summary

Introduce a `comptime` evaluation phase that allows expressions, constants, and function calls to be evaluated at compile time. A `comptime` expression is guaranteed to produce its result before any generated code runs. Comptime values may be used wherever a compile-time constant is required — array sizes, type arguments, conditional compilation — and comptime functions may manipulate types as first-class values.

---

## Motivation

Metel currently has no mechanism for computation at compile time beyond type inference. Several recurring patterns cannot be expressed efficiently:

**Derived constants.** A constant that depends on another constant (e.g., a buffer size derived from a protocol limit) requires either manual duplication or a runtime computation that the compiler cannot fold.

**Compile-time lookup tables.** Generating a `[T; N]` array of precomputed values (hash seeds, trigonometric tables, CRC polynomials) requires either hardcoding literals or computing at program startup. With comptime, the table is a zero-runtime-cost constant.

**Type-level predicates.** Aspect bounds (`where T: Display`) constrain types but cannot ask questions like "how many fields does T have?" or "does T implement Iterable?" that would enable zero-cost type-directed dispatch without virtual dispatch.

**Conditional code generation.** Platform-specific or capability-specific code paths currently require runtime flags or separate compilation units. Comptime boolean conditions fold cleanly into the generated code with no overhead.

The inspiration is Zig's `comptime` mechanism, which demonstrates that a single orthogonal keyword — applied uniformly to expressions, parameters, and variables — can replace macros, templates, and generics with a simpler, more predictable model. Metel does not need to copy Zig's approach wholesale (Metel has a rich type system and generics already), but the core idea — evaluable at compile time, type-safe, no separate macro sublanguage — is directly applicable.

---

## Proposal

### The `comptime` keyword

`comptime expr` evaluates `expr` at compile time. The expression must be *comptime-pure*: it may only call functions that are themselves comptime-evaluable (no I/O, no external state, no runtime allocation outside comptime-managed storage).

```metel
comptime let MAX_CONNECTIONS: i64 = 1024;
comptime let BUFFER_SIZE: i64 = MAX_CONNECTIONS * 64;

comptime let SIN_TABLE: f64[256] = comptime_generate_sin_table();
```

### Comptime functions

A function marked `comptime fun` is evaluable at compile time. It may also be called at runtime — the `comptime` annotation means "this function *can* be evaluated by the compiler", not "this function *must only* be called at compile time."

```metel
comptime fun pow2(n: i64) -> i64 {
    let mut result = 1;
    let mut i = 0;
    while (i < n) { result *= 2; i += 1; }
    result
}

comptime let PAGE_SIZE: i64 = pow2(12);   // 4096, computed at compile time
```

Restrictions on comptime functions:
- No I/O builtins (`print`, `println`)
- No heap allocation via runtime regions (comptime has its own scratch storage)
- No calls to non-comptime functions
- No recursion beyond a compiler-enforced depth limit (open question — see OQ-1)

### Comptime parameters

A function parameter marked `comptime` is erased at the call site — the compiler specialises the function for each distinct comptime argument, similar to monomorphisation for type parameters. This is the mechanism by which types become first-class comptime values.

```metel
fun typed_zero(comptime T: Type) -> T {
    comptime if (T == i64) { 0 }
    else if (T == f64)     { 0.0 }
    else if (T == boolean)    { false }
    else { comptime_error("typed_zero: unsupported type") }
}

let z_int  = typed_zero(i64);   // 0
let z_float = typed_zero(f64);  // 0.0
```

`Type` is the comptime-only type of type values. `T: Type` may appear as a comptime parameter but not as a runtime value.

### `comptime if`

Conditionals whose condition is a comptime expression are evaluated at compile time — the untaken branch is never type-checked or emitted. This enables platform-specific code without dead-code overhead.

```metel
comptime let IS_64BIT: boolean = target_pointer_width() == 64;

fun word_size() -> i64 {
    comptime if (IS_64BIT) { 8 } else { 4 }
}
```

### Comptime and generics

Comptime parameters are the lower-level mechanism; Metel's generic system (`fun f<T>`) remains the primary abstraction for type-parameterised code. The two interact at the boundary where a generic parameter is interrogated structurally:

```metel
// Aspect-based approach (preferred for nominal dispatch)
fun serialize<T: Serializable>(value: T) -> Bytes { ... }

// Comptime approach (for structural interrogation not expressible as an aspect)
fun field_count(comptime T: Type) -> i64 {
    comptime_struct_fields(T).len()
}
```

Comptime does not replace generics for ordinary polymorphism. It supplements them for cases where the type system's nominal abstractions are insufficient.

### Interaction with fixed-size arrays

Comptime is the natural enabler for fixed-size array sizes (RFC-0053). `T[N]` requires `N` to be a comptime `i64`:

```metel
comptime let CHUNK: i64 = 64;
let buf: u8[CHUNK] = [0; CHUNK];   // stack-allocated 64-byte buffer
```

---

## Alternatives Considered

**Macros.** A macro system (procedural or hygienic) can generate code at compile time but introduces a separate sublanguage, separate syntax, and separate error messages. Comptime reuses the same language, same type checker, and same error format. Zig's experience confirms that this is practically sufficient and far easier to learn.

**`const` keyword only.** A weaker design where only simple literal-based constants are allowed (`const X: i64 = 42`) is simpler but does not enable lookup tables, conditional compilation, or type-level programming. The `const` keyword could be syntax sugar for `comptime let`.

**Dependent types.** Full dependent types subsume comptime but are significantly more complex to implement and reason about. Comptime is the pragmatic 80% solution.

---

## Open Questions

### OQ-1 — Recursion and termination

Zig allows recursive comptime functions but enforces a recursion depth limit. Should Metel allow comptime recursion? If yes, what is the limit and how is it surfaced as an error? If no, comptime loops (`while`, `for`) must cover all cases, and some programs expressible recursively cannot be written as comptime.

### OQ-2 — Comptime and regions

Can comptime functions allocate memory? Zig's comptime has its own allocation space. Metel's region system (RFC-0025) is runtime-scoped. The question is whether comptime should have its own separate allocator (a "comptime region") or whether allocation is simply disallowed in comptime functions.

### OQ-3 — `Type` as a first-class value

Making types comptime-passable values (`comptime T: Type`) is powerful but raises questions: Can `Type` values be stored in comptime arrays? Can you iterate over the fields of a struct type at comptime? What operations does `Type` support? This needs a dedicated sub-design.

### OQ-4 — Interaction with aspects

Can comptime code inspect whether a type implements an aspect? `comptime has_aspect(T, Display)` would enable conditional dispatch without adding new aspect syntax. This could replace some uses of conditional `impl` blocks (RFC-0036).

### OQ-5 — Error messages

When a comptime computation fails (e.g., division by zero, assertion failure, unsupported type), the error must be reported with a source location in the original comptime call site, not in the evaluated function. The quality of comptime error messages is a significant usability concern.

---

## Timing Recommendation

Comptime depends on having a stable type system and a clear picture of which language features need compile-time support. Prerequisite: fixed-size arrays (RFC-0053) are the first consumer of comptime sizes. Suggested sequence: (1) `comptime let` for simple constants; (2) `comptime fun` for pure functions; (3) `comptime if`; (4) comptime parameters and `Type` values.

This RFC is a design sketch. A follow-up RFC should nail down the `Type` API and the interaction with generics before implementation begins.

---

## References

- Zig comptime documentation: https://ziglang.org/documentation/master/#comptime
- RFC-0053: Fixed-size array type `[T; N]` — first consumer of comptime sizes
- Language spec: `docs/public/spec.md`

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
