---
title: "Metel Language Specification"
type: spec
version: v0.12.0
created_date: '2026-05-16'
---

> This document is the single source of truth for the Metel language.
> Features not described here are not part of the language.
> Availability in this spec is stated by released or planned versions, not by RFC ids or issue numbers.

Source files use the `.mtl` extension.


## Overview

Metel is a statically typed, expression-oriented language with a Rust-inspired syntax.
This specification describes the language accepted by the current interpreter.

The language's core design principles are:

- **Strong static typing** with full Hindley-Milner type inference
- **No classes** — data and behaviour are defined separately via structs, enums, and aspects
- **Algebraic data types** — enums with data-carrying variants and exhaustive pattern matching
- **Explicit nullability** — absence of a value is represented by `Perhaps<T>`, never by null
- **Explicit error handling** — errors are values, represented as `Result<T, E>`
- **Safe memory by default** — affine ownership: a value has one owner, and moves rather
  than being implicitly copied
  > **Since v0.12.0 (RFC-0071), behind `--move-check`:** ownership is enforced only when the flag is passed; without it the interpreter behaves as if every value were `Copy`. See [Ownership and Move Semantics](spec/ownership.md).


## Contents

| File | Contents |
|---|---|
| [Lexical Structure](spec/lexical.md) | Comments, identifiers, keywords, literals, operators |
| [Modules](spec/modules.md) | Files, modules, imports, path roots, visibility, re-exports |
| [Type System](spec/types.md) | Primitive types, inference, tuples, arrays, casting, generics, Never, `Perhaps<T>`, `Result<T,E>` |
| [Ownership](spec/ownership.md) | Moves, `Copy`, `Drop`, drop order, partial moves |
| [Declarations](spec/declarations.md) | Variables, structs, enums, aspects |
| [Functions](spec/functions.md) | Functions, closures, the `?` operator |
| [Expressions](spec/expressions.md) | Pattern matching, control flow |
| [Runtime](spec/runtime.md) | Panics, built-in functions |
| [Grammar](spec/grammar.md) | Formal grammar |
| [Error Codes](error-codes.md) | Every diagnostic the interpreter can report, with a real example |
| [Language Spec Health](spec-health.md) | How many Formal Rules are tested, which are exempt and why, and which gaps remain |

See [Changelog](../release-notes/changelog.md) for version history.
