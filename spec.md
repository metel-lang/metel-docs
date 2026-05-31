# Metel Language Specification

> **Status:** Active. This document is the single source of truth for the Metel language.
> Features not described here are not part of the language.

Source files use the `.mln` extension.

---

## Overview

Metel is a statically typed, expression-oriented language with a Rust-inspired syntax. Today, the implemented execution mode is the interpreter. A native compiler is planned, but is not part of the current implementation yet.

The language's core design principles are:

- Strong static typing with full Hindley-Milner type inference
- No classes - data and behaviour are defined separately via structs, enums, and aspects
- Algebraic data types - enums with data-carrying variants and exhaustive pattern matching
- Explicit nullability - absence of a value is represented by `Perhaps<T>`, never by null
- Explicit error handling - errors are values, represented as `Result<T, E>`
- Safe memory by default - reference counting, no ownership semantics required
- Planned opt-in memory control - linear types are planned, but are not implemented yet

### Execution modes

> **Planned:** The compiler and linear-type behaviour described in this section are planned design targets, not implemented features.

| Mode | Use case | Memory model |
|---|---|---|
| **Interpreter** | Scripting, embedding, rapid iteration, REPL | RC runtime |
| **Compiler** | Planned for production, performance-critical code, native binaries | Planned: linear types enforced statically + zero-cost at runtime |

The current implementation is interpreter-only. The compiler target and the linear type system are planned so the language surface can grow toward them without implying that they are available today.

---

## Contents

| File | Contents |
|---|---|
| [Lexical Structure](spec/lexical.md) | Comments, identifiers, keywords, literals, operators |
| [Modules](spec/modules.md) | Files, modules, imports, path roots, visibility, re-exports |
| [Type System](spec/types.md) | Primitive types, inference, tuples, arrays, casting, generics, Never, `Perhaps<T>`, `Result<T,E>` |
| [Declarations](spec/declarations.md) | Variables, structs, enums, aspects |
| [Functions](spec/functions.md) | Functions, closures, the `?` operator |
| [Expressions](spec/expressions.md) | Pattern matching, control flow |
| [Runtime](spec/runtime.md) | Panics, built-in functions |
| [Grammar](spec/grammar.md) | Formal grammar |

See [Changelog](changelog.md) for version history.
