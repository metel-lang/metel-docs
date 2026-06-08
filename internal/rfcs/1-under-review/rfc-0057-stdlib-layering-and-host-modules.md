---
id: rfc-0057
title: "Standard Library Layering and Host Module Boundary"
date: '2026-06-06'
---

## Summary

Define the first standard-library boundary for Metel.

This RFC keeps `std::core` as the small, language-adjacent prelude and introduces
ordinary library modules under `std::` for collection, iteration, comparison,
math, and value-utility ergonomics. It also introduces
host-backed library modules under `std::` for operating-system interaction. The
first host-backed areas are environment variables, command-line arguments, file
operations, and subprocess execution. Networking is explicitly deferred to a
later RFC.

This RFC also fixes the sequencing of the runtime refactor: the first stdlib
implementation pass should follow the planned System F elaboration work so the
library boundary is built on the post-elaboration architecture rather than a
short-lived intermediate shape.

---

## Motivation

Metel is at the point where small scripting tasks are desirable, but the current
runtime surface mixes three concerns:

1. Language primitives (`Perhaps`, `Result`, `Display`, `From`, `Iterable`)
2. Ordinary library ergonomics (collections, iterators, comparisons, math,
   small utility helpers)
3. Convenience runtime functions (`print`, `dbg`, `assert`)
4. Future host integration (environment, files, processes, networking)

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

### 2. Ordinary stdlib modules live in explicit modules under `std::`

Metel's first "presentable stdlib" cut is not only about host integration. It
also includes explicit, non-host ordinary library modules that are not part of
the prelude but are expected to be widely useful:

- `std::collections`
- `std::iter`
- `std::cmp`
- `std::math`

These modules are ordinary library namespaces. They are not auto-imported.
Their purpose is to make small real programs pleasant to write without bloating
`std::core`.

### 3. Initial scope of `std::collections`

`std::collections` is the first ergonomics layer over `List<T>` and array-like
data.

Initial API direction:

- `List<T>` helpers such as:
  - `append(other: List<T>) -> List<T>` or mutation-oriented equivalent
  - `contains(value: T) -> boolean` where equality is available
  - `find(pred: (T) -> boolean) -> Perhaps<T>`
- array/slice-oriented helpers that do not require host interaction and do not
  belong in the implicit prelude

This RFC does not commit to whether every helper is modeled as an inherent
method on `List<T>`, a free function in `std::collections`, or a mixture. It
does commit to the scope: collection ergonomics is part of the first stdlib
milestone.

### 4. Initial scope of `Perhaps` / `Result` utilities

`Perhaps<T>` and `Result<T, E>` remain in `std::core`, but they should gain a
small method surface so they are usable in ordinary pipelines.

Initial API direction:

- `Perhaps<T>`:
  - `map`
  - `and_then`
  - `unwrap_or`
  - `unwrap_or_else`
  - `is_some`
  - `is_none`
- `Result<T, E>`:
  - `map`
  - `and_then`
  - `unwrap_or`
  - `unwrap_or_else`
  - `is_ok`
  - `is_err`

These utilities belong with the core sum types rather than in a separate host
or convenience module.

### 5. Initial scope of `std::iter`

`std::iter` is the home for common iteration transforms that are useful but do
not belong in the implicit prelude.

Initial API direction:

- `map`
- `filter`
- `fold`

Whether these are implemented as eager helpers over `List<T>` / arrays or later
grow into a richer iterator abstraction is intentionally left open. The first
goal is usefulness, not a final iterator architecture.

### 6. Initial scope of `std::cmp`

`std::cmp` provides small comparison-oriented helpers that are broadly useful
and host-independent.

Initial API direction:

- `min`
- `max`
- `clamp`

This module should stay small. It exists to prevent the core prelude from
becoming a dumping ground for tiny, widely useful helpers.

### 7. Initial scope of `std::math`

`std::math` provides a deliberately modest first set of numeric helpers.

Initial API direction:

- `abs`
- `min`
- `max`
- `clamp`

Additional numeric functionality should be added only when it clearly supports
real programs. This RFC does not attempt to define a large numerical library.

### 8. Host-backed APIs live in explicit modules under `std::`

Operating-system interaction is not part of the implicit prelude. It must be
placed in explicit modules under `std::`.

The first host-backed modules are:

- `std::env`
- `std::fs`
- `std::process`

These modules are ordinary library namespaces from the language user's
perspective, even if their initial implementation is interpreter-backed.

They are not auto-imported. Programs must import them explicitly.

### 9. Initial scope of `std::env`

`std::env` is the boundary for host process environment inspection.

Initial API direction:

- `var(name: String) -> Perhaps<String>`
- `vars() -> List<(String, String)>` or `[(String, String)]`

Read-only APIs are in scope for the first release. Mutating the host process
environment, such as `set_var` or `remove_var`, is deferred.

### 10. Initial scope of `std::process`

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

The first subprocess API must be **shell-free** at the Metel boundary. The
recommended shape remains:

- `run(command: String, args: String[]) -> Result<ProcessOutput, OsError>`

not:

- `run(command_line: String) -> ...`

This keeps quoting, shell expansion, and platform-specific command parsing out
of the first stdlib cut. Users can still invoke a shell explicitly if they want
one.

### 11. Initial scope of `std::fs`

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

### 12. Networking is deferred

Networking is not part of the first standard-library milestone.

The reasons are architectural, not merely scope-management:

- networking forces decisions about bytes and buffers
- it forces timeout and blocking semantics
- it raises TLS and platform abstraction questions
- it pressures the language toward an async or evented story too early

When networking is added, it should be designed in a dedicated RFC, likely as
`std::net` with a consciously limited first layer such as HTTP request/response
helpers before lower-level socket APIs.

### 13. A dedicated error type is preferred over `Result<T, String>`

Host-backed APIs should not standardize on raw `String` errors.

The initial host modules should use a dedicated standard-library error type,
provisionally named `OsError`, which at minimum implements `Display`.

This keeps the boundary open for richer error information later without forcing
a breaking redesign of every filesystem and process API.

The exact representation of `OsError` is deferred. It may begin as an opaque
runtime-backed type.

### 14. Evaluator-side impl-method storage may be redesigned now

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

### 15. System F elaboration precedes the first stdlib implementation pass

This RFC intentionally does **not** redesign the typechecker-side type and
aspect environments in their current pre-elaboration form.

The evaluator input is planned to change in the next version through System F
elaboration. That work is likely to alter where polymorphism, dictionaries, or
aspect evidence are represented. Implementing the first stdlib layer before
that point would risk building collection helpers, host modules, and runtime
boundaries against a short-lived intermediate architecture.

Therefore:

- stdlib **design** work may proceed now
- interpreter/runtime cleanup that is clearly compatible with the post-
  elaboration direction may proceed now
- System F elaboration should land before the first stdlib implementation pass
- typechecker environment redesign should be done against the post-elaboration
  shape, not before it

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
- collection, iteration, comparison, and basic math helpers belong in explicit
  ordinary library modules under `std::`
- environment variables, files, subprocesses, and networking do not

---

## Staging

Recommended implementation order:

1. Separate evaluator builtin/impl storage from lexical `Environment`
2. Preserve `std::core` as the current virtual module boundary at the design level
3. Land System F elaboration and establish the post-elaboration evaluator/type boundary
4. Add the first ordinary stdlib ergonomics layer:
   - `Perhaps` / `Result` utilities
   - `std::collections`
   - `std::iter`
   - `std::cmp`
   - `std::math`
5. Add explicit `std::env`
6. Add explicit `std::process`
7. Add explicit `std::fs`
8. Finalize the post-elaboration type/aspect environment architecture as needed by the library work
9. Design networking in a dedicated follow-up RFC

This sequencing allows small-script use cases to land without coupling the first
host APIs or core-library helpers to a soon-to-be-replaced typechecker and
runtime architecture.

---

## Non-Goals

- Defining the full concrete API surface of every host module
- Finalizing whether every collection helper is a method, a free function, or a
  trait/aspect-based abstraction
- Designing a lazy iterator architecture in the first stdlib cut
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
