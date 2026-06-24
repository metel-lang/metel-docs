---
id: rfc-0057
title: "Standard Library Layering and Host Module Boundary"
date: '2026-06-06'
revised: '2026-06-11'
---

## Summary

Define the first standard-library boundary for Metel.

`std::core` is the small, language-adjacent prelude. It keeps the core sum
types, the core aspects, and `List<T>` — and, with this revision, it also owns
the collection and iteration ergonomics (`map`, `filter`, `fold`, `contains`,
`find`, …) as methods on `List<T>`, plus the string utility surface (`trim`,
`split`, `to_upper`, `contains`, `chars`, …) as methods on `String`, rather than
splitting these into separate `std::collections` / `std::iter` / `std::str`
modules. The only ordinary (non-prelude, non-host) library module in the first
cut is `std::math`.

This RFC introduces host-backed library modules under `std::` for operating-
system interaction: environment variables (`std::env`), file operations
(`std::fs`), and subprocess execution + command-line arguments
(`std::process`). Networking is explicitly deferred to a later RFC.

This is the canonical definition of the stdlib area for the first presentable
release. It supersedes the broader module list in the original draft.

---

## Motivation

Metel is at the point where small scripting tasks are desirable, but the
runtime surface still needs a clear layering between:

1. Language primitives (`Perhaps`, `Result`, `Display`, `From`, `Iterable`,
   `List<T>`)
2. In-language ergonomics over those primitives (collection/iteration helpers,
   `Perhaps`/`Result` combinators)
3. Convenience runtime functions (`print`, `println`, `dbg`, `assert`)
4. Host integration (environment, files, processes; networking later)

The first three concerns are language-adjacent and host-independent, so they
live in `std::core`. The fourth touches the operating system and must be
explicitly imported.

The original draft proposed a wider set of ordinary modules
(`std::collections`, `std::iter`, `std::cmp`, `std::math`). Experience from
sprint 22 — where `List<T>` became a real nominal struct in the embedded
`std::core` source with native methods — shows the collection and iteration
ergonomics are most natural as **methods on `List<T>`** in `std::core`, not as
free functions in satellite modules. This revision tightens the scope
accordingly: one numeric module (`std::math`) plus the three host modules.

---

## Decisions

### 1. `std::core` is the language-adjacent prelude

`std::core` is the implicit, always-available core module, auto-imported into
every module. It is a real embedded module compiled into the binary (see
ADR-0039), not a virtual injection. It is not a general-purpose kitchen-sink.

The following items belong in `std::core`:

- `Perhaps<T>`
- `Result<T, E>`
- `List<T>` (core collection type, with its ergonomic method surface — see
  Decision 3)
- the `String` utility surface (methods on the primitive `String` — see
  Decision 4)
- `Display`
- `From<S>`
- `Iterable<T>`
- `print`
- `println`
- `dbg`
- `assert` (including the two-argument message overload)

These items are allowed to remain implemented through native host support
rather than ordinary user-level library code.

User code writes `Perhaps`, `Result`, and `List` unqualified; the
fully-qualified paths remain `std::core::Perhaps`, `std::core::Result`, and
`std::core::List`. This RFC explicitly rejects moving these names to
`std::Perhaps` / `std::Result`. `std` is a namespace root; `core` is the home
for language-adjacent primitives.

### 2. `Perhaps` / `Result` utilities live on the core sum types

`Perhaps<T>` and `Result<T, E>` gain a small method surface so they are usable
in ordinary pipelines, in `std::core` itself.

Initial API direction:

- `Perhaps<T>`: `map`, `and_then`, `unwrap_or`, `unwrap_or_else`, `is_some`,
  `is_none`
- `Result<T, E>`: `map`, `and_then`, `unwrap_or`, `unwrap_or_else`, `is_ok`,
  `is_err`

These belong with the core sum types, not in a separate convenience module.

### 3. Collection and iteration ergonomics live on `List<T>` in `std::core`

The original draft carved out `std::collections` and `std::iter` as separate
modules. This revision folds both into `std::core`: the ergonomic surface is a
set of methods on `List<T>` (and, where natural, on arrays), not free functions
in satellite modules.

Initial API direction (methods on `List<T>`):

- Collection ergonomics: `append`/`concat`, `contains` (where equality is
  available), `find(pred: (T) -> boolean) -> Perhaps<T>`
- Iteration transforms: `map`, `filter`, `fold`

Whether each helper is an inherent method on `List<T>` or eventually rides an
`Iterable<T>`-based abstraction is intentionally left open. The first goal is
usefulness over a final iterator architecture; a lazy iterator design remains
deferred to a follow-up RFC. There is **no** `std::collections`, `std::iter`,
or `std::cmp` module in the first cut — comparison helpers (`min`/`max`/`clamp`)
are covered by `std::math` (Decision 5).

### 4. String utilities live on `String` in `std::core`

`String` is a primitive, language-adjacent type — `String::len` already lives in
`std::core` as a native method — so its utility surface belongs there too, as
methods on `String`, not in a separate `std::str` / `std::string` module. They
are host-backed (native), computed by the runtime string value.

Indexing is by **Unicode scalar value**, consistent with `String::len` (which
counts scalars, not bytes); byte-level and grapheme-level APIs are deferred.
Operations are total — out-of-range indices clamp or yield `Perhaps::None`
rather than panicking.

Initial API direction (methods on `String`):

- **Case & trim:** `to_upper`, `to_lower`, `trim`, `trim_start`, `trim_end`,
  `is_empty` (the last derivable as `self.len() == 0`).
- **Search & test:** `contains(needle)`, `starts_with(prefix)`,
  `ends_with(suffix)`, `index_of(needle) -> Perhaps<i64>`.
- **Split, join, replace:** `split(sep) -> String[]`, `replace(from, to)`,
  `repeat(n)`, and the associated `String::join(parts: String[], sep: String) ->
  String`.
- **Chars & slicing:** `chars() -> Char[]`, `char_at(i) -> Perhaps<Char>`,
  `substring(start, end) -> String` (scalar-indexed, clamped).

Regex, formatting/interpolation, Unicode normalization, and encoding conversions
are out of scope for the first cut.

### 5. `std::math` is the one ordinary library module

`std::math` is the single non-prelude, non-host module in the first cut. It is
an ordinary library namespace — not auto-imported; programs import it
explicitly.

Initial API direction:

- `abs`
- `min`
- `max`
- `clamp`

Additional numeric functionality should be added only when it clearly supports
real programs. This RFC does not attempt to define a large numerical library.

### 6. Host-backed APIs live in explicit modules under `std::`

Operating-system interaction is not part of the implicit prelude. It must be
placed in explicit modules under `std::`.

The first host-backed modules are:

- `std::env`
- `std::fs`
- `std::process`

These modules are ordinary library namespaces from the language user's
perspective, even though their implementation is host-backed (native). They are
not auto-imported. Programs must import them explicitly.

### 7. Initial scope of `std::env`

`std::env` is the boundary for host process environment inspection.

Initial API direction:

- `var(name: String) -> Perhaps<String>`
- `vars() -> List<(String, String)>` or `[(String, String)]`

Read-only APIs are in scope for the first release. Mutating the host process
environment, such as `set_var` or `remove_var`, is deferred.

### 8. Initial scope of `std::process`

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

### 9. Initial scope of `std::fs`

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

### 10. A dedicated error type is preferred over `Result<T, String>`

Host-backed APIs should not standardize on raw `String` errors.

The initial host modules should use a dedicated standard-library error type,
provisionally named `OsError`, which at minimum implements `Display`.

This keeps the boundary open for richer error information later without forcing
a breaking redesign of every filesystem and process API.

The exact representation of `OsError` is deferred. It may begin as an opaque
runtime-backed type.

### 11. Networking is deferred

Networking is not part of the first standard-library milestone.

The reasons are architectural, not merely scope-management:

- networking forces decisions about bytes and buffers
- it forces timeout and blocking semantics
- it raises TLS and platform abstraction questions
- it pressures the language toward an async or evented story too early

When networking is added, it should be designed in a dedicated RFC, likely as
`std::net` with a consciously limited first layer such as HTTP request/response
helpers before lower-level socket APIs.

---

## Module Boundary Rule

The standard library follows this rule:

- If removing the feature would change the language's core semantics, it belongs
  in `std::core`.
- If the feature is a host-independent ergonomic over core primitives, it also
  belongs in `std::core` (as methods on the relevant core type) unless it forms
  a coherent standalone domain — `std::math` is the one such domain in the first
  cut.
- If the feature depends on the host operating system or external world, it does
  not belong in `std::core`; it goes in an explicit `std::` module.

Examples:

- `Perhaps`, `Result`, `Display`, `From`, `Iterable`, `List<T>` (with its
  collection/iteration methods), and the `String` utility methods belong in
  `std::core`
- numeric helpers (`abs`/`min`/`max`/`clamp`) belong in `std::math`
- environment variables, files, subprocesses, and networking do not belong in
  `std::core`

---

## Staging

Prerequisites already landed: System F elaboration (sprint 20) and the
real-embedded-`std::core` pipeline with native declarations (sprint 22,
ADR-0039). The first stdlib implementation pass is therefore built on the
post-elaboration architecture, as the original draft required.

Recommended implementation order:

1. `Perhaps` / `Result` utility methods in `std::core`
2. `List<T>` collection + iteration ergonomics in `std::core`
3. `String` utility methods in `std::core`
4. `OsError` host error type
5. `std::env`
6. `std::fs`
7. `std::process`
8. `std::math` (after the `Ord` aspect, RFC-0062)
9. Public spec / reference updates and tutorial refresh
10. Design networking in a dedicated follow-up RFC

---

## Non-Goals

- Defining the full concrete API surface of every host module
- Finalizing whether every collection helper is an inherent method or an
  `Iterable`-based abstraction
- Designing a lazy iterator architecture in the first stdlib cut
- String regex, formatting/interpolation, Unicode normalization, byte/grapheme
  indexing, or encoding conversions (the first cut is scalar-indexed utilities)
- Designing async I/O, futures, or an event loop
- Designing sockets, TLS, or general networking APIs
- Finalizing the representation of `OsError`
- Introducing `std::collections`, `std::iter`, or `std::cmp` as modules in the
  first cut

---

## References

- ADR-0039: `metel-interpreter/docs/decisions/adr-0039-native-bindings-embedded-stdcore.md`
  (native bindings, embedded `std::core`; supersedes ADR-0027)
- ADR-0038: `metel-interpreter/docs/decisions/adr-0038-overload-resolution-symbolid-dispatch.md`
- RFC-0054: `docs/internal/rfcs/3-implemented/rfc-0054-list-type.md`
- Public spec entry point: `docs/public/reference/spec.md`
