---
id: rfc-0057
title: "Standard Library Layering and Host Module Boundary"
date: '2026-06-06'
---

## Summary

Define the first standard-library boundary for Metel.

This RFC keeps `std::core` as the small, language-adjacent prelude and introduces
host-backed library modules under `std::` for operating-system interaction. The
first host-backed areas are environment variables, command-line arguments, file
operations, and subprocess execution. Networking is explicitly deferred to a
later RFC.

This RFC also fixes the sequencing of the runtime refactor: evaluator-side
builtin and aspect-impl storage may be cleaned up now, but the type and aspect
environment redesign is deferred until the planned System F elaboration work
lands.

---

## Motivation

Metel is at the point where small scripting tasks are desirable, but the current
runtime surface mixes three concerns:

1. Language primitives (`Perhaps`, `Result`, `Display`, `From`, `Iterable`)
2. Convenience runtime functions (`print`, `dbg`, `assert`)
3. Future host integration (environment, files, processes, networking)

Those concerns should not be modeled the same way.

`std::core` exists today as a virtual in-memory module seeded by the interpreter
and typechecker. That is appropriate for language-adjacent primitives, but it is
the wrong place to accumulate operating-system APIs. At the same time, the
current evaluator stores aspect impl methods as ordinary environment bindings
under synthetic string keys, which is known technical debt and a poor basis for
growing a standard library.

The goal of this RFC is to establish a stable boundary now without prematurely
locking in the wrong post-elaboration architecture.

---

## Decisions

### 1. `std::core` remains the language-adjacent prelude

`std::core` remains the implicit, always-available core module. It is not a
general-purpose kitchen-sink module.

The following items belong in `std::core`:

- `Perhaps<T>`
- `Result<T, E>`
- `List<T>` if retained as a core collection type
- `Display`
- `From<S>`
- `Iterable<T>`
- `print`
- `println`
- `dbg`
- `assert`
- `assert_msg`

These items are allowed to remain implemented through interpreter/runtime
support rather than ordinary user-level library code.

`std::core` continues to be auto-imported into every module. User code should
continue to be able to write `Perhaps`, `Result`, and `List` unqualified, while
the fully-qualified paths remain `std::core::Perhaps`, `std::core::Result`, and
`std::core::List`.

This RFC explicitly rejects moving these names to `std::Perhaps`,
`std::Result`, or similar root-level paths. `std` is a namespace root; `core`
is the correct home for language-adjacent primitives.

### 2. Host-backed APIs live in explicit modules under `std::`

Operating-system interaction is not part of the implicit prelude. It must be
placed in explicit modules under `std::`.

The first host-backed modules are:

- `std::env`
- `std::fs`
- `std::process`

These modules are ordinary library namespaces from the language user's
perspective, even if their initial implementation is interpreter-backed.

They are not auto-imported. Programs must import them explicitly.

### 3. Initial scope of `std::env`

`std::env` is the boundary for host process environment inspection.

Initial API direction:

- `var(name: String) -> Perhaps<String>`
- `vars() -> List<(String, String)>` or `[(String, String)]`

Read-only APIs are in scope for the first release. Mutating the host process
environment, such as `set_var` or `remove_var`, is deferred.

### 4. Initial scope of `std::process`

`std::process` covers command-line arguments and subprocess execution.

Initial API direction:

- `args() -> String[]`
- `run(command: String, args: String[]) -> Result<ProcessOutput, OsError>`

`ProcessOutput` is a standard-library data type with at least:

- `status: i64`
- `stdout: String`
- `stderr: String`

The initial subprocess model is synchronous. Streaming stdin/stdout pipes,
background processes, and shell-specific helpers are deferred.

### 5. Initial scope of `std::fs`

`std::fs` covers simple file operations.

Initial API direction:

- `read_to_string(path: String) -> Result<String, OsError>`
- `write_string(path: String, contents: String) -> Result<(), OsError>`
- `append_string(path: String, contents: String) -> Result<(), OsError>`
- `exists(path: String) -> boolean`
- `read_dir(path: String) -> Result<String[], OsError>`
- `create_dir(path: String) -> Result<(), OsError>`
- `create_dir_all(path: String) -> Result<(), OsError>`
- `remove_file(path: String) -> Result<(), OsError>`
- `remove_dir(path: String) -> Result<(), OsError>`
- `remove_dir_all(path: String) -> Result<(), OsError>`

The first file API is text-oriented. Byte arrays, streaming I/O, file handles,
and buffered readers/writers are deferred until Metel has a clearer low-level
data model for those operations.

`read_dir(path: String)` is the directory-listing primitive for the first
stdlib cut. It returns directory entry names rather than a metadata-rich entry
type. More specialized helpers such as file-only filtering are deferred until
Metel has a clearer metadata model.

### 6. Networking is deferred

Networking is not part of the first standard-library milestone.

The reasons are architectural, not merely scope-management:

- networking forces decisions about bytes and buffers
- it forces timeout and blocking semantics
- it raises TLS and platform abstraction questions
- it pressures the language toward an async or evented story too early

When networking is added, it should be designed in a dedicated RFC, likely as
`std::net` with a consciously limited first layer such as HTTP request/response
helpers before lower-level socket APIs.

### 7. A dedicated error type is preferred over `Result<T, String>`

Host-backed APIs should not standardize on raw `String` errors.

The initial host modules should use a dedicated standard-library error type,
provisionally named `OsError`, which at minimum implements `Display`.

This keeps the boundary open for richer error information later without forcing
a breaking redesign of every filesystem and process API.

The exact representation of `OsError` is deferred. It may begin as an opaque
runtime-backed type.

### 8. Evaluator-side impl-method storage may be redesigned now

The evaluator should stop modeling aspect impl methods as ordinary lexical
bindings keyed by synthetic strings. That representation was an acceptable
intermediate step for the current interpreter, but it is not the right runtime
foundation for a standard library.

The intended direction is:

- lexical locals remain in `Environment`
- builtin globals and host intrinsics are stored separately from lexical locals
- aspect impl methods are stored in a dedicated runtime registry rather than as
  fake local variables

This RFC does not prescribe the exact runtime data structure. It only fixes the
boundary: impl methods are runtime metadata, not ordinary user variable
bindings.

### 9. Type and aspect environment redesign is deferred until after System F elaboration

This RFC intentionally does **not** redesign the typechecker-side type and
aspect environments.

The evaluator input is planned to change in the next version through System F
elaboration. That work is likely to alter where polymorphism, dictionaries, or
aspect evidence are represented. Redesigning the type and aspect environments
before that point would risk a short-lived intermediate architecture.

Therefore:

- interpreter/runtime cleanup may proceed now
- standard-library module layering may proceed now
- typechecker environment redesign is deferred until the post-elaboration shape
  is known

This is a sequencing decision, not a claim that the current type-side
representation is ideal long-term.

---

## Module Boundary Rule

The standard library follows this rule:

- If removing the feature would change the language's core semantics, it belongs
  in `std::core`.
- If the feature depends on the host operating system or external world, it does
  not belong in `std::core`.

Examples:

- `Perhaps`, `Result`, `Display`, `From`, and `Iterable` belong in `std::core`
- environment variables, files, subprocesses, and networking do not

---

## Staging

Recommended implementation order:

1. Separate evaluator builtin/impl storage from lexical `Environment`
2. Preserve `std::core` as the current virtual module boundary
3. Add explicit `std::env`
4. Add explicit `std::process`
5. Add explicit `std::fs`
6. Revisit type/aspect environment architecture after System F elaboration
7. Design networking in a dedicated follow-up RFC

This sequencing allows small-script use cases to land without coupling the first
host APIs to a soon-to-be-replaced typechecker architecture.

---

## Non-Goals

- Defining the full concrete API surface of every host module
- Designing async I/O, futures, or an event loop
- Designing sockets, TLS, or general networking APIs
- Finalizing the representation of `OsError`
- Replacing the `std::core` virtual-module model in this RFC
- Redesigning the typechecker's type and aspect environment before System F
  elaboration

---

## References

- ADR-0027: `metel-interpreter/docs/decisions/adr-0027-std-core-virtual-module.md`
- ADR-0013: `metel-interpreter/docs/decisions/adr-0013-aspect-impl-flat-env-and-method-keys.md`
- RFC-0054: `docs/internal/rfcs/3-implemented/rfc-0054-list-type.md`
- Public spec entry point: `docs/public/reference/spec.md`
