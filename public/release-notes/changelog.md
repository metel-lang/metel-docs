---
title: "Metel Language Changelog"
---

# Changelog

## v0.12.0

**In progress on `develop` — not yet released.** The spec's `Available in v0.12.0` /
`Changed in v0.12.0` markers refer to this entry.

**RFCs implemented:** RFC-0115 (Field Initializer Separator), RFC-0116 (Anonymous
Record Types), RFC-0118 (Row Bounds), RFC-0126 (`T[]` as a Copy Borrowed View).
**RFC-0071 (Ownership and Move Semantics) is partially implemented** — see
"Ownership" below for exactly which parts, and which are declared but inert.

**Anonymous records:**
- Closed, anonymous, exact-shape, structurally typed product types: `{ x: f64, y: f64 }`
  as a type, `{ x = 1.0, y = 2.0 }` as a value, and `Handle.{ fd }` to project a nominal
  type's row.
- Structural identity is order-insensitive — `{ x: i64, y: i64 }` and `{ y: i64, x: i64 }`
  are the same type.
- Records are **exact**: unification requires the same label set, and there is no width
  subtyping. A record with an extra field is a different type, not a subtype.
- Duplicate labels are a parse error.
- A bare `{ x }` or `{ x = e }` where a block may appear is still a **block**. Write a
  record there in parentheses — `({ x = e })`; the diagnostic says so at the point of use.
- Records satisfy `Send`/`Sync` by field composition, but carry no impl-based aspect.
  Inherent methods, non-local aspect impls, and a custom `Drop` on a record are rejected.
- Deliberately not yet shipped: chained and pattern projection, narrowing, record
  conversions, named records, and open rows. Each belongs to a later RFC.

**Row bounds:**
- A bound may be a bare row, constraining a type parameter by the fields it carries rather
  than by an aspect:

  ```metel
  fun magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64
  fun labels<record T>(x: T) -> Symbol[]
  fun f<record T: { x, y: f64, .. }>(p: T)
  fun h<T>(p: T) where record T: { x: f64, .. }
  fun send<record T: !{ token }>(t: T) -> i64
  ```

- Only records satisfy a row bound. A struct never does, and the diagnostic says why.
- A closed row (no `..`) requires exactly that label set; an open row requires at least it.
- A field may omit its type to constrain the label alone. There is no `_` wildcard.
- **Negation is per listed field, not the complement of the whole row.** `!{ x: f64 }` is
  satisfied by a record whose `x` is an `i64`; `!{ x }` rejects the label outright.
- A row bound on a parameter that is `record`-kinded in neither the parameter list nor the
  `where` clause is an error that names the fix.

**Ownership — partially implemented, and partly inert:**
- The `Copy` and `Drop` aspects are declared in the standard library. `Copy` is implemented
  for the twelve numeric primitives plus `boolean` and `Char`.
- Structural rules: a tuple is `Copy` iff every element is, a fixed array iff its element
  type is, `&T` is `Copy`, and `&var T` is not. **Dynamic `T[]` deliberately has no rule in
  either direction** — the question belongs to sequence types, not to this release.
- A struct may implement `Copy` only if every field is; an enum only if every payload in
  every variant is. The diagnostic names the offending field or payload.
- `Copy` and `Drop` are mutually exclusive. This is rejected in either declaration order,
  and also when two *overlapping conditional* impls would give one instantiation both.
- **Move checking is implemented but off by default.** Pass `--move-check` to enable it.
  Nothing in the language moves without that flag; the default remains copy-on-assign.
- **A `Drop` impl compiles and its `drop` method never runs.** Destructor invocation and
  drop order are not in this release. Do not write a type whose correctness depends on its
  destructor firing until that lands.
- **`T[]` is now a non-owning, immutable, unconditionally-`Copy` borrowed view** (RFC-0126),
  resolving the "Dynamic `T[]` deliberately has no rule" gap above. Produced only by
  borrowing a `List<T>`, a `[T; N]`, or another slice; array literals with no expected type
  default to `[T; N]` instead. `a[0] = 9` through a `T[]` no longer compiles — mutate via
  `List<T>` or `[T; N]` instead. The existing `[T; N]` → `T[]` coercion (v0.8.0) means most
  existing code needs no changes: it only fires at a genuinely unannotated literal.
  `List<T>` gains `.set(i, value) -> Perhaps<T>` (overwrites in place, returning the
  replaced value or `None` if out of bounds) to close the resulting gap — nothing let you
  mutate a growable sequence's contents in place otherwise.

**References:**
- **`&<rvalue>` no longer requires binding the value to a name first** (temporary lifetime
  extension, matching Rust/C++: `foo(&Vec::new())`). A literal, a call result, a struct or
  enum construction, or any other non-addressable expression is materialized into a fresh,
  independent cell and referenced directly. `&var` does not get the same treatment and
  still requires an addressable place — a mutable reference to a cell nothing else can ever
  observe again has no expressible effect.

**Breaking changes:**
- **Field initializers use `=`, not `:`** — `Point { x = 1.0, y = 2.0 }`. This completes
  the rule that `:` classifies and `=` defines, with no exceptions left. Field
  *declarations* (`message: String`), enum variant declarations, and patterns are
  unchanged and still use `:`.

  Migration is mechanical but **must not be done with a regex.** Declarations, patterns
  and literals share brace syntax and co-occur on one line — `Perhaps::Some { value } =>
  Perhaps::Some { value = f(value) }` has a pattern and a literal in a single expression,
  and only the literal changes. Rewrite over parsed field-initializer spans.
- **`record` is now a keyword** and can no longer be used as an identifier.

**Diagnostics:**
- New error code [T0019](../reference/error-codes.md#t0019--use-of-moved-value), reported
  only under `--move-check`, with distinct wording per rule rather than one generic
  message: use after move, a partially moved value used as a whole, a partial move of a
  `Drop` type, a banned array-element move, and a `&var` moved by a use that is not a
  reborrow. Each names the binding and the source location of the move.
- A malformed record projection is diagnosed directly, instead of being reported against a
  synthesised type name that appears nowhere in the program.
- A generic field type in a `Copy` eligibility error is rendered as written — `Inner<T>` —
  rather than leaking the inference variable behind it (`Inner<?t16>`).

**Fixes:**
- A record no longer satisfies an aspect bound vacuously; it must actually meet it.
- `..` on a negative row bound is rejected rather than silently accepted, since "at least
  these fields, negated" has no coherent reading.
- `Copy` eligibility now sees conditional impls on generic field types, so
  `extend<T: Copy> Outer<T>: Copy` is accepted when `Outer`'s field is an `Inner<T>` that
  is itself conditionally `Copy`. It was previously rejected outright.
- `String` and `List<T>` methods that only read their receiver (`String`'s entire method
  surface; `List<T>`'s `get`/`len`/`as_slice`/`map`/`filter`/`fold`/`find`/`concat`) now
  take `&self` instead of `self`. Under `--move-check`, calling more than one such method
  on the same binding previously moved it on the first call and rejected the second —
  since neither type is `Copy`, this affected any program exercising the flag at all, not
  just a handful of fixtures.

## v0.11.0

**Released 2026-07-24.** The spec's `Since v0.11.0` / `Changed in v0.11.0` markers
refer to this entry.

**RFCs implemented:** RFC-0107 (Unqualified Enum Variants in Match Patterns),
RFC-0108 (Reference-Transparent Match Scrutinees), RFC-0110 (Explicit Dereference
Operator), RFC-0111 (Unqualified Enum Variants in Expression Position),
RFC-0097 (Orphan Rule for Blanket Impls) — the last of these was already accepted and
marked implemented, but its rule for `extend<T: Bound> T: Aspect` was only satisfied by
coincidence; the check is now deliberate.

**Enum variants:**
- A match arm may name a variant without its `Enum::` prefix when the scrutinee's
  enum determines it: `match c { Red => .., Green => .. }`. Resolution is
  type-directed against the scrutinee's own type — not a lexical import — so two
  enums may both declare `Red` with no ambiguity.
- The same applies in expression position, against the *expected* type:
  `let c: Colour = Red;`, `paint(Blue)`, `fun favourite() -> Colour { Green }`.
- **`None`, `Some`, `Ok` and `Err` are ordinary variants, not literals.** They have
  no special status in the grammar or the type system and resolve exactly as a
  user-declared variant does. Qualified forms remain valid everywhere.
- A bare variant is a last resort: an in-scope binding wins, and so does a
  same-named unit struct. Where no expected type exists the bare form does not
  resolve — there is deliberately no search for "some enum, somewhere".

**References:**
- Explicit `*expr` returns, for reading through a reference and, as an assignment
  target, for writing through a `&var T`. This reverses v0.10.0's removal of
  explicit dereference syntax.
- Auto-deref is now confined to *selectors* — field access, field assignment,
  indexing, and method dispatch. Call arguments and operator operands are spelled
  explicitly: `add(*p, *q)`, `*p + *q`.
- Matching a `&T`/`&var T` scrutinee matches against the referent's own patterns.
- `&*p` is a reborrow that shares the referent's storage; reborrowing a `&var T`
  as `&T` downgrades to shared.
- Index-path write-through works through a reference: `xs[0] = 9` for
  `xs: &var i64[]`.
- Tuple elements are assignable — `t.0 = v`, `t.0 += v`, and nested and chained
  forms — including through a `&var` reference.

**Breaking changes:**
- **Assignment to a reference-typed binding now rebinds it**, like every other
  type. `*p = v` is the spelling that writes through. Previously a bare `p = v`
  wrote through the reference, which made repointing a `&var T` unrepresentable.
  Migration is mechanical: `p = v` becomes `*p = v`.
- **Write-through takes one `*` per reference layer.** The previous rule peeled
  every layer at once, so `pp = 5` on a `&var &var i64` wrote the innermost value;
  it is now `**pp = 5`. In exchange, `*pp = &var m` repoints the inner reference,
  which the old rule could not express.
- `&` applied to a field or element now **aliases** the original storage instead
  of snapshotting a copy, so later writes are visible through it. It remains
  read-only.

**Diagnostics:**
- `==` and `!=` on operand types the evaluator cannot compare — references,
  structs, enums, arrays, tuples, unit — are rejected at compile time
  ([T0005](../reference/error-codes.md#t0005--invalid-operand-types)) instead of
  aborting at run time with an internal error.
- A binary operator whose operands disagree now names the operator:
  ``operator `==` cannot be applied to an integer literal and `String` `` rather
  than a bare `cannot unify`.
- Address-of a non-addressable place — a literal, a call result, a struct or enum
  construction — is a compile-time error with a span, not a runtime internal
  error. The rule was always static-determinable.
- `&var *r` on a shared reference is a compile-time error rather than a runtime
  failure.
- Assigning to a tuple element out of range, or through an immutable binding,
  reports a type error instead of an internal error.

**Fixes:**
- A closure with no declared return type is no longer typed `()` at the call site.
  Pass 1 inferred it correctly and pass 2 discarded it; `let f = () -> { 42 };
  let n = f(); n + 1` failed.
- Type-directed read-copy decides whether to peel against the *substituted* type,
  so `let n: i64 = g();` works for `fun g() -> &i64` — previously only the
  syntactically-a-reference forms did, and a call returning `&T` did not.
- Generic bodies constructed at call time use the argument and receiver types
  recorded at the call site, refined over the runtime-derived ones. An empty
  collection has no element to sample, and the resulting `Never` coerced without
  ever pinning a type parameter, so `[].eq(&[])` failed with an error pointing
  inside `std::core`.
- A bare variant that can never resolve is reported rather than silently accepted.

**Dispatch and bounds:**
- **Two aspects may register a same-named method against the same generic or structural
  target** — `T[]`, `Wrapper<T>` — without silently aliasing. The single-slot registries
  previously kept whichever impl was registered last, regardless of which one's bounds the
  concrete instantiation actually satisfied, so calls could dispatch to the wrong impl.
  Affects nominal generic structs identically, not only arrays.
- **A generic struct or array implementing `Iterable<T>` generically** — `extend<T>
  Wrapper<T>: Iterable<T>`, rather than a concrete `extend Counter: Iterable<i64>` — now
  derives its `for`-in element type correctly. Two separate paths were wrong: inference read
  the registry's recorded type arguments, which for a still-generic impl are the impl's own
  parameter *names* rather than types, and construction searched only the concrete method
  environment, never the polymorphic one.
- **An associated type's declared bound is registered on its projection.** RFC-0082 allows
  `type Item: Display;`, but the placeholder minted for `Self::Item` never carried that
  bound, so chaining directly onto a projection result — `c.get().to_string()` — failed with
  a spurious "cannot infer receiver type" (T0002).

## v0.10.0

**Released 2026-07-17.**

**Language surface:**
- `public`, `var`, and `extend` are now the canonical spellings. The old
  `pub`, `mut`, and `impl` declaration spellings are removed.
- Empty aspect declarations may be written as `aspect Name;`.
- Bodyless positive and negative aspect implementations are accepted:
  `extend Type: Aspect;` and `extend Type: !Aspect;`.
- Zero-field structs and zero-field enum variants may be constructed with or
  without braces: `Empty` / `Empty {}` and `Flag::On` / `Flag::On {}`.
- `return`, `break`, and `continue` are expressions of type `!`, so they work
  in braceless `if` arms, match arms, loop tails, and other expression positions.

**References and control flow:**
- Reference types are now spelled `&T` and `&var T`.
- Explicit dereference syntax is gone; field access, method calls, function
  calls through references, type-directed reads, and write-through assignment
  handle ordinary reference use.
- Reference operations chain through multiple layers such as `&&T` and
  `&&var T`.
- The bottom type `!` is user-writable, coerces to any type, participates in
  exhaustiveness for uninhabited enum variants, and is checked for `-> !`
  functions.

**Aspect and type system:**
- Conditional aspect implementations are enforced, including `where` clauses
  and negative bounds.
- Aspect implementation coherence is enforced with orphan-rule and overlap
  checks.
- Negative bounds (`T: !Aspect`) and negative implementations
  (`extend Type: !Aspect;`) participate in bound checking and coherence.
- Associated types are supported in aspects and implementations, including
  projections such as `T::AssocType` and equality-constrained bounds.
- Return-position `impl Aspect` is supported as an opaque static return type.
- Structural aspect implementations over built-in constructors such as arrays
  participate in aspect-bound satisfaction.
- Bare-parameter blanket implementations such as `extend<T> T: Aspect` are
  allowed only when the aspect is local to the declaring module.
- Coherence's disjoint-negation overlap check now recognizes structural
  targets (arrays, tuples, function types) the same way it already did for
  named types: two conditional implementations for the same structural
  target, distinguished only by a positive versus negative bound on the same
  type parameter, no longer incorrectly conflict.

**Standard library:**
- `Perhaps` and `Result` gain `.yolo()`.
- `Perhaps` gains `.ok_or(error)`.
- `Result` gains `.map_err(f)` and `.ok()`.

**Breaking changes:**
- Replace `pub` with `public`.
- Replace `mut` bindings with `var` bindings.
- Replace `impl` blocks with `extend` blocks.
- Replace `*T` / `*mut T` with `&T` / `&var T`.
- Remove explicit `*p` dereference syntax.

**Fixes and cleanup:**
- Generic method bodies now recover the receiver's own type parameters when
  reconstructing method dispatch.
- Zero-argument generic calls can use the caller's expected type when arguments
  alone do not determine all type parameters.
- Aspect dispatch, import resolution, and the runtime type registry now use
  stable symbol identities, avoiding same-name collisions across modules.
- Generic bounds are preserved when a type variable is aliased to another
  type variable during inference, instead of being silently dropped.
- The RFC/process documentation was reorganized around the current public docs
  and implementation state.

## v0.9.1

Bug fixes. Shipped from sprint/24.

**Fixes:**
- `print` and `println` now print any value whose type implements `Display`, dispatching the user's `to_string` — previously a struct or enum with a `Display` implementation typechecked but panicked at runtime, and had to be printed via an explicit `.to_string()`
- A tuple type now accepts an array suffix: `(T, U)[]` parses and typechecks in return, parameter, local-annotation, and struct-field positions (and a tuple is accepted as a generic type argument, e.g. `List<(String, String)>`)

**Testing and tooling:**
- The integration harness now runs evaluator and typechecking fixtures through the same full module pipeline as the shipped binary, eliminating the old single-program shortcut that drifted from real `std::core` behavior

## v0.9.0

The first presentable standard library. Shipped from sprint/23.

**Language:**
- Methods on generic types now work end-to-end. Generic structs *and* generic enums can carry methods with their own type parameters (`fun map<U>(self, f: (T) -> U) -> Box<U>`), closures, and `match self`, and they dispatch correctly across module boundaries. This unblocks the standard library's methods on `Perhaps`, `Result`, and `List`

**Standard library — `std::core` (auto-imported):**
- `Perhaps<T>` combinators: `is_some`, `is_none`, `map`, `and_then`, `unwrap_or`, `unwrap_or_else`
- `Result<T, E>` combinators: `is_ok`, `is_err`, `map`, `and_then`, `unwrap_or`, `unwrap_or_else`
- `List<T>` ergonomics: `map`, `filter`, `fold`, `find`, `concat` (in addition to `new`/`from`/`push`/`pop`/`len`/`get`/`as_slice`)
- `String` utilities: `is_empty`, `to_upper`, `to_lower`, `trim`, `trim_start`, `trim_end`, `contains`, `starts_with`, `ends_with`, `index_of`, `split`, `replace`, `repeat`, `chars`, `char_at`, `substring`, and the associated `String::join`. Index-based operations count Unicode scalars and are total (out-of-range clamps or returns `None`)
- `OsError` — the error type for the host modules, with a `Display` implementation and a `message()` accessor

**Standard library — host modules (explicit import):**
- `std::env` — `get(name) -> Perhaps<String>`, `vars() -> EnvVar[]` (read-only)
- `std::fs` — text-oriented file operations (`read_to_string`, `write_string`, `append_string`, `exists`, `read_dir`, `create_dir`, `create_dir_all`, `remove_file`, `remove_dir`, `remove_dir_all`), all returning `Result<_, OsError>`
- `std::process` — `args()` and shell-free synchronous `run(command, args) -> Result<ProcessOutput, OsError>`

**Known gaps (tracked):**
- `std::math` and the comparison-dependent `List` methods (`sort`, `contains`) await a forthcoming `Ord`/`Eq` aspect

(The `print`/`println` Display limitation and the tuple array-suffix parse gap noted here at release were fixed in v0.9.1.)

## v0.8.3

Standard library expansion and module system clarifications. Shipped from sprint/22.

**New language features:**
- Function overloading — a module may declare multiple free functions with the same name, distinguished by parameter types. Resolution is exact-match only: argument types must equal a candidate's parameter types exactly, with no implicit numeric coercion participating in selection (bare numeric literals default before selection, so `f(42)` picks an `i64` overload). Overloaded functions must be non-generic with every parameter annotated; calls with no matching candidate list all available signatures in the error
- Aspects can now be implemented for primitive types — `impl Display for i64 { … }` and the like typecheck and run; the standard library's `Display` and `From` implementations for the primitives are declared this way
- `native` declaration syntax for stdlib-only host-backed implementations — free functions, methods, and aspect methods can be marked `native` with an explicit binding key. Reserved for the standard library; using it in user code is a compile error

**Standard library (breaking):**
- `print`/`println` now require `Display` at compile time — passing a type with no `Display` implementation is a type error (`T0012`) instead of a runtime panic
- A module's function overloads extend, rather than replace, a same-named standard-library function: if no overload matches exactly, the call falls back to the outer binding (e.g. overloading `print` for specific types keeps the generic `print` reachable for everything else)
- `assert` is now overloaded: `assert(cond)` and `assert(cond, msg)`. The separate `assert_msg` function is removed — replace `assert_msg(c, m)` with `assert(c, m)`
- `string_len(s)` is removed in favour of a `len` method on `String`: use `s.len()`
- `string_concat(a, b)` is removed — use the `+` operator: `a + b`

**Module system:**
- Using `std` as a top-level module name is now a compile error. A file at `std.mtl` or anywhere under `std/` in the project tree produces: `error: module path std::… is reserved for the standard library`. The `std` keyword was already reserved in the language syntax; the interpreter now enforces the same reservation at the module path level.

**Internal improvements:**
- `std::core` is now a real module compiled into the interpreter binary and checked through the normal module pipeline, rather than a set of hand-registered builtins — the entire core surface (`Perhaps`, `Result`, `Display`/`From`/`Iterable`, `List<T>`, `print`/`println`/`assert`/…) is declared in standard library source. No user-visible behaviour change; `import std::core::…` works as before
- Overloaded calls dispatch by stable symbol identity rather than by name throughout the pipeline
- Symbol definition index — every declared symbol now has a stable definition site recorded during name resolution; used by diagnostics and future tooling
- Error span accessor — all error variants that carry source location now expose it through a uniform interface

## v0.8.2

Generic function recursion and forward-reference fix. Shipped from sprint/21.

**Bug fixes:**
- Generic self-recursion now type-checks correctly; a generic function can refer to itself inside its own body without triggering `T0003 undefined name`
- Generic forward references now work the same way as monomorphic forward references; a generic function can call a later generic function declared in the same scope
- Mutual recursion across generic functions now type-checks and evaluates correctly; the pre-inference hoist pass now registers generic function schemes before any body is inferred

**Performance improvements:**
- **Incremental constraint solving** — `InferContext::solve()` now caches the solved substitution for the append-only prefix of the constraint list instead of re-solving the full set on every eager partial solve. This removes the dominant `0.8.2` baseline bottleneck in generic-heavy programs
- **Typechecker sub-phase profiling** — the benchmark harness now reports registry, inference, solve, scheme-environment, construction, and finalize timings so optimization work can target the real hot paths rather than evaluator guesses
- **Benchmark/profiling workflow** — `metel-bench` now benchmarks evaluator integration fixtures through the same parse → typecheck → evaluate path used by the test suite and emits machine-readable summaries plus call-graph artifacts
- **Measured impact on the release benchmark suite** — representative total runtime improvements from the original `0.8.2` baseline:
  - `int_04_generic_algorithms.mtl`: `1662.887 ms` → `160.724 ms`
  - `int_01_statistics.mtl`: `675.241 ms` → `87.376 ms`
  - `int_03_generic_option_chain.mtl`: `431.502 ms` → `76.467 ms`
  - `int_05_generic_data_pipeline.mtl`: `357.644 ms` → `66.298 ms`
  - `int_11_generic_sized.mtl`: `157.804 ms` → `27.107 ms`

**Internal improvements:**
- `hoist_fun_decls` now pre-registers generic function schemes and their aspect bounds, so generic visibility follows the same pre-pass architecture as monomorphic recursion instead of relying on per-function provisional bindings
- Regression coverage added for generic self-recursion and generic mutual recursion in both the typechecking and evaluator integration suites

## v0.8.1

Post-inference elaboration pipeline. No new language surface. Shipped from sprint/20.

**Internal (interpreter architecture):**
- **Elaboration pass** — a dedicated `elaborator` stage runs between the typechecker and evaluator and resolves every `MethodDispatch` call site to `Inherent` or `Aspect { aspect_id }` before evaluation begins. The evaluator now accepts `ElaboratedModuleGraph` (a newtype proof that elaboration has run) instead of `TypedModuleGraph` directly (METEL-151, ADR-0037).
- **SymbolId infrastructure** — every top-level declaration is assigned a stable `SymbolId` by the name resolver at declaration site, and every import binding carries the same `SymbolId`. Builtin types and aspects have reserved IDs (1–99); user-defined symbols start at 1000 (METEL-172, METEL-104).
- **SymbolId-keyed aspect dispatch** — `RuntimeAspectImpl` carries `aspect_id: Option<SymbolId>` alongside its string name. `RuntimeRegistry::get_aspect_method_by_id` matches on `aspect_id` first, eliminating cross-module name collisions where two unrelated aspects share a method name (METEL-152).
- **Ambiguous same-type aspect methods rejected** — if two distinct aspects define the same method name on the same receiver type, elaboration now rejects the call with `T0013` instead of silently picking one impl by traversal order.
- **Environment documentation** — `TypeDefinitionRegistry` is annotated with its elaboration interface; `ElaboratedModuleGraph` carries a responsibilities table; `architecture.md`, `typechecker.md`, and `evaluator.md` are updated to reflect the new stage (METEL-154, METEL-156).
- **ADR-0037** — records the elaboration boundary decision, the dispatch-map keying rationale, and the long-term constraint that `ElaboratedModuleGraph` is a viable future compiler IR intake point (METEL-157).
- **Regression suite** — four new full-pipeline fixtures cover: polymorphic calls across modules, cross-module aspect dispatch, two aspects with the same method name on different receiver types, and inherent/aspect method coexistence (METEL-155).

## v0.8.0

Sized numeric types, Char, List\<T\>, fixed-size arrays, turbofish, and fat-pointer `&mut`. Shipped from sprint/19.

**New language features:**
- **Sized numeric types** — `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`, `f32`, `f64` (RFC-0007, METEL-124). Sized literal suffixes: `42i32`, `3.14f32`, `255u8`. All casts between sized types are explicit (`as`). Array indices must be `u64`.
- **Polymorphic numeric literals** — unsuffixed integer and float literals unify with whatever numeric type the context demands (let annotation, function parameter, struct field, return type, or the other operand in a binary expression). Without context they default to `i64` / `f64`. `mut` reassignment (`m = 99` where `m: i32`) also propagates the declared type to the literal. Negative minimum literals (`-128i8`, `-32768i16`, `-2147483648i32`) are accepted at the lexer level.
- **Cross-sized numeric `From` impls** — all 90 pairwise casts among the 10 numeric types are supported via `as` (`i8 as u32`, `f32 as i64`, etc.). Previously only `i64 ↔ f64` was supported.
- **`Char` type** — Unicode scalar value; single-quoted literals (`'a'`, `'\u{1F600}'`); `.to_u32()` and `Char::from_u32(n)` conversions; implements `Display` (RFC-0007)
- **`List<T>`** — standard growable-sequence type in `std::core`; replaces ad-hoc `array_push` usage; methods: `new`, `from`, `push`, `pop`, `len`, `get`, `as_slice` (RFC-0054)
- **Fixed-size array type `[T; N]`** — compile-time-known length; repeat construction `[v; N]`; coerces to `T[]`; `.len()` method; array patterns on `[T; N]` (RFC-0053, METEL-135)
- **Turbofish** — explicit type arguments at call sites: `f::<T>(args)`, `zip::<A, B>(as, bs)` (METEL-124)
- **`&mut` for lvalue paths** — `&mut obj.field`, `&mut arr[i]`, and chains thereof produce a `*mut T` that writes back to the original storage location (RFC-0045, METEL-134)

**Bug fixes:**
- Generic functions with multiple independent type parameters (e.g. `fold_left<T, A>`) no longer have their type parameters collapsed when a module-level constraint solve follows a single-parameter generic function (METEL-137)
- Same-tier glob import conflicts (`import a::*` and `import b::*` both exporting the same name) no longer raise an error at import resolution; the error fires at the first use site of the ambiguous name (METEL-98)
- `&mut x` on a non-`let mut` binding is now a type error (T0006); previously accepted silently, allowing immutable bindings to be mutated through a pointer (METEL-118)
- Field assignment (`p.field = v`) on a non-`let mut` binding is now a type error (T0006); previously the field mutability check was missing, allowing struct fields to be mutated through an immutable binding (METEL-119)

**Breaking changes:**
- `array_push` and `array_len` are removed as top-level built-in functions; use `List<T>` for mutation and `.len()` on arrays and lists
- Code that previously relied on `&mut x` or `p.field = v` with a non-`let mut` binding will now fail typechecking

## v0.7.0

Language quality, pointer semantics, closure stabilisation, and aspect bounds. Shipped from sprint/17 and METEL-75–82 (hotfix batch).

**Breaking changes:**
- Anonymous closure expressions now use `(...) -> ... { ... }`; `fun(...)` is no longer accepted in expression position, and function types are written as `(T) -> U` (RFC-0041)
- Struct fields are module-private by default; cross-module field access and construction now require `pub` on each exposed field (RFC-0032)
- Mutable bindings now use `let mut`; standalone `mut x = value;` is no longer accepted, and `for` / `for-in` bindings use the same `let mut` form (RFC-0042)

**New language features:**
- **Explicit receiver semantics** — methods may declare `&self` (shared read) or `&mut self` (shared mutable) receivers; `&mut self` mutations are visible to the caller without a writeback convention (RFC-0044, METEL-112)
- **Regular and mutable pointer types** — `&expr` and `&mut expr` produce `Pointer<T>` and `MutPointer<T>` values; assignment through `*ptr` and function-pointer auto-deref are supported (RFC-0043, METEL-111)
- **Aspect bounds on generic type parameters** — functions, structs, and enums may now declare aspect bounds on their type parameters; bounds are enforced by the typechecker and violation is error `T0012` (RFC-0002, RFC-0034, RFC-0035, RFC-0040, METEL-57, METEL-60, METEL-67, METEL-84–93):
  - Inline single bound: `fun foo<T: Comparable>(x: T)`, `struct SortedList<T: Comparable>`
  - Inline multi-bound with `+`: `fun foo<T: Comparable + Printable>(x: T)` (RFC-0034)
  - `where` clause: `fun foo<T>(x: T) where T: Comparable + Printable`
  - `impl Aspect` anonymous parameters: `fun foo(x: impl Display)` (RFC-0035)
  - Aspect methods declared by a bound are available on the type parameter inside the function body
  - `T0012` is emitted at the call/construction site with span on the offending argument
- **String interpolation** (`${expr}`) — string literals may contain `${…}` placeholders; each hole desugars to `.to_string()` concatenated with surrounding fragments via `+` (RFC-0010, METEL-81, METEL-82)
- **String concatenation** — `String + String -> String` (METEL-78)
- **Aspect default methods** — an aspect method may provide a default body; `impl` blocks may omit defaulted methods and inherit them automatically (METEL-77)
- **`Self` in impl signatures** — `Self` may be used as a parameter or return type in `impl` method signatures (METEL-79)
- **Match arm blocks** — match arm bodies may be a block in addition to a bare expression (RFC-0018, METEL-78)

**Bug fixes:**
- Computed index assignment (`arr[i + 1] = v`, `s.data[offset * 2] = v`) now works correctly; previously any computed index expression caused an internal error (METEL-106)
- `&mut self` methods on nested struct fields now mutate in place (METEL-112)
- `impl` methods with `T`-typed parameters on generic structs now resolve correctly in Pass 2 (METEL-92)
- Bounded type parameter method dispatch correctly enforces arity and argument types (METEL-93)
- `?` (error propagation) — routed through `From`-based coercion; typechecker emits T0007 when no `From` impl exists (METEL-80)
- Generic functions returning an ascribed `None : Perhaps<T>` now correctly constrain the inferred return type (METEL-76)

**Tooling:**
- CLI version is derived from `CARGO_PKG_VERSION` rather than a hardcoded string (METEL-100)
- Source file extension corrected to `.mtl` throughout public docs (METEL-100)
- `mod` and `use` removed from the reserved keyword list (METEL-75)

**Spec clarifications:**
- `pub` is not valid on top-level `let` or `mut` bindings (METEL-99)

## v0.6.4

Module system technical debt. Shipped by Sprint 15 (`sprint/15`).

**Internal improvements:**
- `TypeDefinitionRegistry` is now used as the cross-module type accumulator in `check_graph`, replacing the `Vec<Decl>` approach that cloned raw AST nodes; cross-module struct field type references now resolve correctly even when the field type comes from an indirect dependency (ADR-0032, METEL-3)
- `InferContext::new` accepts `imported_schemes` directly, enforcing the dual-registration invariant (inference + construction passes both see imported names) at the type level (ADR-0022, METEL-6)
- `declared_names` map added to `ResolvedNames` during name resolution, replacing an O(n) AST scan in `build_import_schemes` for T0009/T0003 distinction (METEL-4)
- `resolve_path_root` extracted to `src/module_paths.rs` as a single shared implementation for both `module_loader` and `name_resolver`; fixed a regression where the `Name` path root incorrectly doubled the module name segment (ADR-0023, METEL-7)
- `StdPrelude::schemes()` / evaluator builtin parity assertion added as a compile-time-checked test (ADR-0027, METEL-5)

**Compatibility:**
- No language-visible changes.

## v0.6.3

Module system — feature complete. Shipped by Sprint 14 (`sprint/14`).

**Bug fixes:**
- `return` and `break` are now valid as bare match arm bodies without enclosing braces: `arm => return value` (#226)
- Diamond module dependencies (same physical file reachable via two different logical paths) no longer fail with T0003; the name resolver now dereferences path aliases to their canonical form (#228)

**Internal improvements:**
- `?` operator desugared in a pre-pass (`path_normalizer::desugar_propagate_error`) rather than carried through inference and construction; `Expr::PropagateError` no longer exists after normalization (ADR-0030, #214)
- `Type::Perhaps` and `Type::Result` convenience variants removed from the `Type` enum; both types are now represented uniformly as `Type::Named("Perhaps", ...)` and `Type::Named("Result", ...)` (#150)
- Per-module isolated runtime environments validated with cross-module closure-capture and mutual-recursion tests (#189)
- All aspect method dispatch key construction routed through `ImplMethodKey::to_env_key()`, eliminating ad-hoc format strings in the evaluator (#209)

**Compatibility:**
- No language-visible changes except the match arm body fix (#226), which is purely additive.

## v0.6.2

Evaluator normalization. Shipped by Sprint 13 (`sprint/13`).

**Internal improvements:**
- `Value::Perhaps` and `Value::Result` dedicated variants removed; all `Perhaps` and `Result` values now use the general `Value::Enum { name, variant, fields }` representation, eliminating special-case dispatch throughout the evaluator (ADR-0028, #205)
- `evaluate_graph` now initialises each module in its own isolated `Environment` seeded with builtins and cross-linked via the `imported_names` table populated by `check_graph`; replaces the flat-merge strategy from v0.5.0 (ADR-0029, #210)

**Compatibility:**
- No language-visible changes. All existing programs produce identical output.

## v0.6.1

Type system cleanup and `std::core` virtual module. Shipped by Sprint 12 (`sprint/12`).

**Internal improvements:**
- Unified `TypeDefinitionRegistry` replaces four separate flat maps (`struct_env`, `method_env`, `enum_env`, aspect impls) in the type inference and construction passes; a single registry instance is now the source of truth for all type and impl data (#133)
- `ImplMethodKey` enum replaces flat string concatenation for impl method dispatch keys in the evaluator
- `StdPrelude::default()` is the single source of truth for all built-in function schemes, eliminating the previous divergence between the inference and construction registries

**New language features:**
- `std::core` virtual module: `Perhaps`, `Result`, `Display`, `Iterable`, `From`, and all built-in functions are available in every module without any explicit import (#201, #202)
- Glob import tiers: the runtime auto-imports `std::core` at `Std` tier (lowest priority); user `import path::*` declarations use `User` tier and silently win over `Std` tier without a conflict error (#206)

**Compatibility:**
- All existing programs are unaffected; `std::core` names that were previously available globally continue to work without import statements

## v0.6.0

Module semantics. Shipped by Sprint 11 (`sprint/11`).

**Enforced module semantics (previously deferred from v0.5.0):**
- Visibility enforcement: `pub` is required for a declaration to be importable; private items produce a compile-time error (T0009) when referenced from another module
- Import scoping: only names brought in scope by `import` are accessible; accessing an undeclared name is a compile-time error (T0003)
- Alias resolution: `import mod::name as alias` makes `alias` callable and removes `name` from scope
- Import conflict detection: two imports binding the same local name produce a compile-time error (T0011); explicit imports silently win over conflicting glob imports
- Glob visibility filtering: `import mod::*` now includes only `pub` items from the source module; private items are excluded
- Re-export propagation: names re-exported via `export` are part of the facade module's public API and importable by consumers without importing the underlying module directly
- `pub` declarations require complete type annotations (T0010): every parameter and the return type must be annotated on a `pub fun`

**Internal improvements:**
- Name resolver wired into the type-checking pipeline (`load_root → resolve → normalize → check_graph → evaluate_graph`)
- Flat-merge compatibility shim (ADR-0019) and last-segment fallback (ADR-0020) removed
- `root::`, `self::`, and `super::` path roots now compute correct module paths in both the loader and name resolver

**Compatibility:**
- Single-file programs and programs using only `pub` items across module boundaries are unaffected
- Programs that imported private items or relied on global declaration visibility will need `pub` annotations added

## v0.5.0

Module system. Shipped by Sprint 9 (`sprint/9`).

**New language features:**
- Multi-file programs: each `.mtl` file is a module; the module graph is built from `import` declarations
- `import path::Name;` both loads the referenced file and brings `Name` into scope
- Import forms: single name, alias (`as`), group (`{A, B}`), glob (`*`), module handle
- `export path::Name;` re-exports a name from a submodule into the current module's public API
- `pub` on `fun`, `struct`, `enum`, and `aspect` marks declarations as externally accessible
- Absolute and relative path roots: `root::`, `std::`, `self::`, `super::`
- Fully-qualified paths valid in type and expression position without a preceding `import`
- Circular imports detected at load time with a full chain in the error message
- Facade modules: `parser.mtl` alongside `parser/` directory — no special `mod.mtl` file
- File-to-module mapping via `::` → `/` with no special cases

**Shipped in v0.6.1:**
- `std::core` auto-import and standard library core types (#150, #201, #202)

**Compatibility:**
- Single-file programs with no `import` or `export` declarations remain valid without modification

## v0.4.2

Evaluator refactor, test restructure, and keyword cleanup. Shipped by Sprint 8 (`sprint/8`).

**Breaking changes:**
- `Perhaps::Nope` renamed to `Perhaps::None`; the standalone `nope` keyword is now `None`

## v0.4.1

Technical debt, bug fixes, and internal cleanup. Shipped by Sprint 7 (`sprint/7`).

**Bug fixes:**
- `TypeErrorCode::T0005` ("Invalid operand types") is now emitted for arithmetic operators (`+`, `-`, `*`, `/`, `%`) applied to non-numeric types (e.g. `true + false` is now a type error)
- Unary negation (`-`) on non-numeric types is now a type error
- Ordering comparisons (`<`, `<=`, `>`, `>=`) on non-comparable types (non-numeric, non-String) are now type errors
- `Pattern::Nope` latent bug eliminated — `nope` values are now exclusively `Value::Perhaps(None)`, so the pattern can no longer silently miss the `Value::Enum { name: "Perhaps", variant: "Nope" }` form

**Internal improvements:**
- `Value::YoloResult` renamed to `Value::Result`; `Perhaps` and `Result` values are now first-class runtime variants — no longer stored as `Value::Enum`
- Large enum variants boxed in `Decl`, `Stmt`, `TypedDecl`, `TypedStmt` (stack frame sizes reduced from 896–1040 bytes to 8 bytes)
- Dead utility methods removed (`Program::new`, `Type::is_numeric`, `Type::is_unit`); reserved fields annotated with `#[allow(dead_code)]`
- All clippy style/idiom warnings resolved

## v0.4.0

Aspects and upgraded builtins. Shipped by Sprint 6 (`sprint/6`).

**New language features:**
- Aspect declarations — `aspect Foo { fun method(self) -> T; }`
- `impl Aspect for Type` blocks with method dispatch via `.method()` syntax
- `Iterable<T>` aspect — user-defined types usable in `for-in` loops
- `From<S>` aspect — `as` cast desugars to `T::from(value)`; user-defined casts for any type pair
- `Display` aspect — `.to_string()` on `i64`, `f64`, `boolean`, `String`; `print`/`println` polymorphic via Display
- `?` operator now supports cross-type error coercion: if the function's error type `E2` implements `From<E1>`, `?` calls `E2::from(e)` automatically

**Builtin changes:**
- `print(v)` and `println(v)` are now polymorphic (`<T: Display>`) — accept any Display type
- `i64::from(f: f64)` and `f64::from(n: i64)` built-in From impls replace the hardcoded `as` special case
- Deprecated: `print_int`, `println_int`, `print_float`, `println_float`, `int_to_string`, `float_to_string`, `bool_to_string` (use `.to_string()` and polymorphic `print`/`println`)

**Bug fixes:**
- Keyword-prefix identifiers (`break_sum`, `return_value`, `let_x`) now parse correctly as identifiers
- Multiple `impl From<X> for Y` blocks with different source types now dispatch independently

## v0.3.0

Generics and type-inference improvements. Shipped by Sprint 5 (`sprint/5`).

**New language features:**
- User-defined generic functions — `fun id<T>(x: T) -> T` — monomorphised at each call site
- User-defined generic structs — `struct Box<T> { value: T }`, `struct Pair<A, B> { ... }`
- User-defined generic enums — `enum Maybe<T> { Some { value: T }, None {} }`
- Let-polymorphism — unannotated `let`-bound closures are generalised to polymorphic schemes (`let id = fun(x) { x }` works at `i64`, `boolean`, and `String` in the same scope)
- Braceless `if` body — `if (c) expr` and `if (c) a else b` (RFC-0022)
- `struct` and `enum` declarations are allowed inside function bodies

**Type-inference improvements:**
- `expected_ty` propagates into match arm bodies — bare `[]` and `nope` resolve without ascription when the surrounding return type is known
- Callee parameter types propagate into argument construction — `find(words, nope)` resolves without ascription when the parameter type is `Perhaps<String>`
- Lvalue path assignment — `obj.field = val` and `arr[i] = val` work on non-bare receivers (e.g. `get_foo().bar = 1`)

## v0.2.0

Evaluator improvements, DX features, and language quality fixes. Shipped by Sprint 3 (`sprint/3`).

**New language features:**
- Type ascription operator `:` — `[] : i64[]` guides type inference without runtime cost (RFC-0021)
- Shorthand struct field initialisation — `Point { x, y }` desugars to `Point { x: x, y: y }`
- Trailing commas allowed in function parameter lists and argument lists

**New built-in functions:**
- `assert(cond: boolean)` — panics with `"assertion failed"` if `cond` is `false`
- `assert_msg(cond: boolean, msg: String)` — panics with `msg` if `cond` is `false`
- `dbg<T>(v: T) -> T` — prints `[dbg] <value>` to stderr and returns the value unchanged
- `print_int(n: i64)`, `println_int(n: i64)` — print an `i64` without/with newline
- `print_float(f: f64)`, `println_float(f: f64)` — print a `f64` without/with newline

**Bug fixes:**
- Arrays now have value semantics — binding an array to a new variable produces an independent copy
- Error spans now report `file:line:col` instead of raw byte offsets
- Complex expressions (field access, calls) are now valid array index operands

**Developer experience:**
- Runtime panics now include a call-stack trace showing function name and call site

## v0.1.0

Initial language version. Implemented by the tree-walk interpreter.

**Features included:**
- Primitive types: `i64`, `f64`, `boolean`, `String`, `()`
- Variables: `let` (immutable), `mut` (mutable), lexical scoping, `fun`/type hoisting
- Functions: first-class values, closures with mutable capture, `?` operator (exact error type match only)
- Structs: literals, field access, methods (`impl`), `mut self`, associated functions
- Enums: unit and struct-like variants, `impl` blocks
- Built-in generic types: `Perhaps<T>`, `Result<T, E>`, `Array<T>` / `T[]` (as special cases; user-defined generics are v0.3.0)
- Exhaustive pattern matching: all pattern kinds (see [Pattern Kinds](../reference/spec/expressions.md#pattern-kinds))
- Control flow: `if`/`else`, `while`, `for`, `for-in` (arrays and ranges only), `loop`, `break`/`continue`, `return`
- Type casting: `as` for `i64 ↔ f64`
- Never type (`!`)
- Tuples
- Built-in functions (see [Built-in Functions](../reference/spec/runtime.md#built-in-functions))

**Not included (v0.3.0+):**
- User-defined generic functions and types (see [Generics](../reference/spec/types.md#generics))
- User-defined aspects and `impl Aspect for Type` (see [Aspects](../reference/spec/declarations.md#aspects))
- `From`-based `?` coercion across different error types (see [The ? Operator](../reference/spec/functions.md#the--operator))
- User-defined `Iterable<T>` implementations (see [For-In](../reference/spec/expressions.md#for-in))
