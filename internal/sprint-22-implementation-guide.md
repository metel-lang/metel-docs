# Sprint 22 — Implementation Guide

**Cycle:** Sprint 22 — "stdlib prep, native keyword"
**Milestone:** 0.8.3
**Plane issues:** METEL-180, METEL-181, METEL-182, METEL-183 (RFC-0058), METEL-184 (RFC-0059)

## 1. Scope and goal

Five Plane issues are in this cycle. They form one architectural transition:

1. **METEL-180** — Carry `SymbolId` (not surface name) as the dispatch identity
   for every call site after typechecking.
2. **METEL-184** — RFC-0059: add `definitions: HashMap<SymbolId, Span>` to
   `ResolvedNames` and allocate `SymbolId`s for methods. Shares the name
   resolver work with METEL-180.
3. **METEL-182** — Add a stdlib-only `native(@…)` declaration form that
   produces normal callable decls bound to an explicit `NativeKey`.
4. **METEL-183** — RFC-0058: introduce the `SourceProvider` trait on
   `module_loader` so embedded stdlib and LSP overlays share one read
   abstraction.
5. **METEL-181** — Replace the `StdPrelude` + `register_builtins` twin
   registries with a single synthetic `std::core` module that flows through
   the normal loader → resolver → typechecker → evaluator pipeline.

Ordering matters: 180+184 first (stable identity before anything depends on
it), then 182 (native decls need `SymbolId` for each overload), then 183
(loader abstraction before the std:: bypass is removed), then 181 (unified
`std::core` last — it depends on all prior stages).

Overload resolution scope for this sprint is **full**: argument types, generic
constraints, and aspect bounds all participate in candidate ranking. Out of
scope: expanding stdlib surface area, operator-overload integration, FFI /
user-facing `native`. Those are 0.8.4+.

**Branch:** `sprint/22`, cut from current `main`. All implementation commits go
directly on `sprint/22`. There are no intermediate pull requests — one PR opens
at sprint close from `sprint/22` to `main` per the standard sprint workflow in
`AGENTS.md`. Keep the tree green (tests passing) after each stage before moving
to the next.

**Documentation commitments** (sprint-close gate):
- ✅ ADRs in `metel-interpreter/docs/decisions/`: `adr-0038` (overload
  resolution + SymbolId dispatch, Stage A) and `adr-0039` (native binding
  model + embedded std::core, Stages B/C; supersedes ADR-0027).
- ✅ Spec: `native(@…)` section in `docs/public/reference/spec/functions.md`
  (stdlib-only restriction, bodiless form, caller-side transparency) and the
  `NativeBinding` production in `grammar.md`.
- ✅ Changelog entry in `docs/public/release-notes/changelog.md` for 0.8.3.
- No RFC for `native` — treated as an internal compiler form, not a public
  language feature (decision recorded above).

## 2. Current state (verified against `main`)

- `symbols.rs` already defines `SymbolId(u32)` with reserved low IDs for
  builtin types and aspects, and `SymbolTable::intern` keys by
  `(source_module, source_name)` — so same-name overloads collide today.
- Typechecker free-function environment is `HashMap<String, TypeScheme>`
  (`typechecker/mod.rs:21`, `SchemeEnv`). Construction env is also string-keyed
  (`typechecker/construction.rs:84,89`).
- `StdPrelude` (`typechecker/mod.rs:94`) is built from
  `registry::populate_std_schemes` and is the typechecker-side builtin source.
- `evaluator::builtins::register_builtins` (`evaluator/builtins.rs:61`) is the
  evaluator-side mirror; `free_function_names()` exists only to back the
  parity test at `typechecker/mod.rs:779`.
- `module_loader` short-circuits any `std::` import; `name_resolver` injects
  `std::core` as a virtual export set.
- Aspect dispatch is already keyed by `SymbolId` for the aspect itself
  (METEL-152), but method selection within an aspect is still by string name.
- `ResolvedNames` has no `definitions` field; method declarations have no
  `SymbolId`.

## 3. Stage A — Callable identity and definition index (METEL-180 + METEL-184)

These two tasks share the name resolver pass and should land together.

**Goal:** after typechecking, every typed AST call node carries the `SymbolId`
(or equivalent `CalleeId`) of its resolved target. `ResolvedNames` maps every
declared symbol — including methods — to its definition span. No later phase
re-resolves callees by surface name.

### A.1 Introduce `CalleeId`

- New type in `symbols.rs`:
  ```rust
  pub enum CalleeId {
      Free(SymbolId),
      Method { recv: SymbolId, method: SymbolId },
      AspectMethod { aspect: SymbolId, method: SymbolId },
  }
  ```
- Reserve a small block of `SymbolId`s for builtin callables (next to the
  existing aspect block) so Stage B can hand them out deterministically.

### A.2 Overload sets and definition index in name resolution (METEL-180 + METEL-184)

- Change `SymbolTable::intern` to allow multiple `SymbolId`s per
  `(module, name)`: `HashMap<(Vec<String>, String), SmallVec<[SymbolId; 1]>>`
  so the single-decl case stays cheap.
- Allocate a `SymbolId` for each method and aspect-method declaration during
  name resolution (previously only free functions and type decls got one).
  This is the shared step between METEL-180 (dispatch identity) and METEL-184
  (definition index).
- `name_resolver` returns a `CandidateSet` for every callable reference
  instead of a single binding. Non-callable refs (types, modules) stay
  single-binding.
- Add `pub definitions: HashMap<SymbolId, Span>` to `ResolvedNames`. Populate
  it for every declaration that produces a `SymbolId`, storing the **name
  token span** only (not the full declaration span). This invariant must be
  preserved as new declaration kinds are added.
- Remove `#[allow(dead_code)]` on `FieldDef::span` and `VariantDef::span`
  in `ast/mod.rs`. Those spans also store the name token only.
- Add `MetelError::primary_span() -> Option<Span>` in `error/mod.rs`: one
  `match` arm per error variant, returning the span where one exists.

### A.3 Overload resolution in typecheck

- In `typechecker/inference.rs` and `typechecker/construction.rs`, replace the
  `SchemeEnv: HashMap<String, TypeScheme>` for callables with
  `HashMap<SymbolId, TypeScheme>` plus a `HashMap<String, SmallVec<SymbolId>>`
  candidate index.
- Resolution is **full**: a candidate matches if (a) its instantiated
  parameter types unify with the argument types, (b) its generic constraints
  are satisfiable in the current environment, and (c) any required aspect
  bounds on its parameters are discharged for the inferred argument types.
- Ranking when multiple candidates survive: prefer the more-specific signature
  (concrete over generic, fewer aspect bounds over more). Genuine ambiguity is
  a hard error with a list of viable candidates. Reuse the diagnostic style
  from METEL-173.
- Method resolution (`construction.rs` method-call paths and aspect dispatch)
  uses the same algorithm, with the receiver type as an additional ranking
  axis. Aspect-bounded methods participate in the same candidate set as
  inherent methods.
- The algorithm needs a clear failure-mode contract: when generic constraints
  can't be checked until later (e.g. inferred via a deferred unification var),
  the resolver records a *pending* candidate set instead of committing. Capture
  this in the ADR — it is the part most likely to bite later.

### A.4 Typed AST changes

- `typed_ast` `Call` / `MethodCall` nodes gain a `callee: CalleeId` field.
- Elaborator and evaluator switch their dispatch lookup to `CalleeId`. The
  evaluator's `RuntimeRegistry` gets a `by_symbol: HashMap<SymbolId, …>` index
  alongside the existing name maps; name maps survive only for diagnostics
  during this stage.

### A.5 Migration tactic

- Introduce `CalleeId` + dual lookup, then flip the evaluator to symbol-first
  lookup, then delete the string fallback **for user code**. The METEL-152
  `get_aspect_method_by_id` name fallback for builtin aspects must remain until
  Stage C — builtins still register without a `SymbolId` until they become a
  real module.
- Existing `TypedExpr::MethodCall.method: String` stays as the diagnostic
  label; a new `method_id: SymbolId` field carries dispatch identity.
- Existing `MethodDispatch::Aspect { aspect_id }` and `Dynamic` variants are
  preserved. `CalleeId::AspectMethod` is the call-site identity;
  `MethodDispatch` remains the elaboration-time decision about *how* to
  dispatch.

**Acceptance (METEL-180):**
- `tests/integration/sources/evaluator/functions/overloading.mtl` (already on
  disk, untracked) passes: two `print` overloads on `i32` and `i64` dispatch
  correctly.
- Methods overload by argument type and by generic constraint.
- Aspect-bounded function parameters dispatch correctly to inherent vs aspect
  methods based on candidate ranking.
- No `HashMap<String, …>` keyed by callable name remains in `evaluator/*`
  for **user** dispatch (diagnostic-only is fine; builtin-aspect name
  fallback survives until Stage C).
- Ambiguous-overload, no-matching-overload, and unsatisfiable-bound
  diagnostics exist and are covered by tests.

**Acceptance (METEL-184):**
- `ResolvedNames::definitions` is populated for all top-level declarations
  and impl/aspect methods; given a `SymbolId`, the defining `Span` is
  reachable in O(1).
- `MetelError::primary_span()` returns a span for all error variants that
  carry one.
- All existing tests pass.

## 4. Stage B — `native` declarations (METEL-182)

**Goal:** stdlib source files can declare host-backed callables using
`native(@…)` syntax, producing normal declarations with a `NativeKey` binding.
Stage B does not yet move existing builtins — it only proves the mechanism.

### B.1 Parser

- Extend `grammar.pest` to accept `native ( @ <dotted_ident> )` as a function
  modifier in front of `fun` (free or in `impl`). Body is required to be
  absent (`;` instead of `{ … }`).
- Stdlib-only enforcement: gate at the resolver / loader, not the parser, by
  rejecting `native` declarations from any module whose root is not `std`.
  Parser stays uniform; the restriction is a single check with a clear
  diagnostic.

### B.2 AST and lowering

- New AST node `NativeBinding { source_id: Vec<String> }` attached to
  `FunDecl`. Lowering converts `@std.core.print` → `NativeKey::StdCorePrint`
  via a closed enum in `evaluator/native_keys.rs`.
- Unknown source ids in a stdlib module become a hard error at lowering —
  the enum is the single source of truth for what host code provides.

### B.3 Runtime registry

- `RuntimeRegistry` grows `natives: HashMap<NativeKey, RuntimeCallable>`.
- Host implementations register themselves into this map at startup; the
  evaluator looks up by `NativeKey` only when dispatching a callable whose
  declaration carries one.
- Each native callable still has a `SymbolId` from Stage A; the dispatch path
  is `CalleeId → declaration → NativeKey → host fn`.

### B.4 Coverage check

- A test asserts that every variant of `NativeKey` is referenced by exactly
  one stdlib declaration and registered in exactly one host impl. This is the
  permanent replacement for `free_function_names()` parity.

**Acceptance:**
- A toy stdlib file `native(@std.core.test_echo) fun test_echo(x: String) -> String;`
  parses, typechecks, runs, and routes to a host impl looked up by
  `NativeKey::StdCoreTestEcho`.
- Same `native` declaration in a user (non-`std::*`) module is rejected with
  a clear diagnostic.

## 5. Stage C — `SourceProvider` and unified `std::core` (METEL-183 + METEL-181)

### C.1 `SourceProvider` trait (METEL-183)

Introduce the trait before touching the std:: bypass so the two changes are
independent commits.

- Define in `module_loader.rs`:
  ```rust
  pub trait SourceProvider {
      fn read(&self, module_path: &[String]) -> Result<String, MetelError>;
  }
  ```
  The key is the logical module path (`&[String]`), not a filesystem path.
- `FsSourceProvider { root: PathBuf }` performs the segment-to-filesystem
  conversion currently done inline in the loader.
- `load_root` becomes `pub fn load_root<P: SourceProvider>(path, provider: &P)`.
  Generic, not `&dyn` — call sites always have a concrete type.
- All `fs::read_to_string` calls in `module_loader.rs` are replaced with
  `provider.read(module_path)`.
- Add `validate_std_namespace` alongside `validate_super_root`: reject any
  filesystem-resolved module path beginning with `["std"]` with
  `error: module path std::… is reserved for the standard library`. This
  enforces at the file-discovery layer the reservation that already exists at
  the keyword level.
- No behaviour change for the CLI; all existing tests pass.

### C.2 Unified `std::core` (METEL-181)

- Embed `stdlib/core.mtl` (and any other `stdlib/*.mtl` files) via
  `include_str!` / `build.rs`. Files use Stage B's `native(@…)` for every
  existing builtin (`print`, `println`, `string_len`, `string_concat`,
  `List::new`, `List::from`, `clock`, `assert`, `assert_msg`, `dbg`).
- Add `EmbeddedStdlibProvider` wrapping `FsSourceProvider`:
  ```rust
  impl SourceProvider for EmbeddedStdlibProvider {
      fn read(&self, module_path: &[String]) -> Result<String, MetelError> {
          if let Some(src) = stdlib::lookup(module_path) { return Ok(src.to_owned()); }
          self.inner.read(module_path)
      }
  }
  ```
  `stdlib::lookup` is a `build.rs`-generated map keyed on `&[&str]` segment
  slices. Paths beginning with `["std", …]` that are not in the embedded map
  fall through to the filesystem — but `validate_std_namespace` blocks
  filesystem-originated `std` paths, so the user can never shadow the stdlib.
- `module_loader` stops short-circuiting `std::` imports. The loader
  synthesizes the `std::core` module from the embedded source and feeds it
  into the normal `ModuleGraph` ahead of user modules.
- Delete `StdPrelude` and the `populate_std_schemes` path.
- Delete `register_builtins`. Runtime registry is populated by walking the
  elaborated `std::core` module (registering `SymbolId`s and `NativeKey`s),
  then host registering `NativeKey → fn` entries.
- Delete `evaluator::builtins::free_function_names` and the parity test at
  `typechecker/mod.rs:779`. Replace with the Stage B.4 coverage test.
- Remove the virtual `std::core` injection from `name_resolver.rs`; the
  module now flows through `resolve_module` like any other.
- Confirm that `SYM_TYPE_*` / `SYM_ASPECT_*` reserved IDs are still claimed
  before user-decl interning begins — that pre-seeding is independent of this
  change and must stay.

**Acceptance (METEL-183):**
- `load_root` accepts a `SourceProvider`; `FsSourceProvider` produces
  identical behaviour to the previous direct reads; all existing tests pass.
- A module at `std.mln` or under `std/` produces the reserved-namespace error.

**Acceptance (METEL-181):**
- Grep for `StdPrelude`, `register_builtins`, `free_function_names` returns
  nothing in `src/`.
- `std::core::print` resolves via the normal resolver, typechecks via the
  normal typechecker, dispatches via `CalleeId → NativeKey`.
- All existing integration tests pass without behaviour change.

## 6. Risks and notes

- **Test churn.** Many integration tests likely import builtins implicitly.
  Audit before Stage C; do not let test breakage drive design.
- **TypeVar generator collisions.** `StdPrelude` currently starts at 10000 to
  avoid colliding with `build_registry` (ADR-0027). When `std::core` becomes a
  normal module, it allocates from the normal generator and the offset goes
  away. Verify no test depends on the 10000 base.
- **Diagnostic regressions.** Switching to `SymbolId`-keyed dispatch can
  produce worse messages if the original source name is not threaded into
  diagnostics. Keep a `display_name: String` on typed-AST call nodes purely
  for rendering.
- **Not in this sprint:** overload-set ergonomics (good error spans, "did you
  mean" suggestions), user-facing `native`, FFI shape, expanding stdlib
  surface area. Capture these as 0.8.4 follow-ups.

## 7. Resolved decisions

> **As-built status (sprint 22, final).** All five issues shipped:
> Stages A (METEL-180 + METEL-184), B (METEL-182), C.1 (METEL-183), and
> C.2 (METEL-181) are complete on `sprint/22` (worktree branch
> `sprint/22-stdcore` developed the C.2 cutover and was fast-forward merged).
> The full core surface — Perhaps/Result, the core aspects, List<T>, the
> primitive Display impls, the numeric From cross-product, Char ↔ u32 — is
> declared in the embedded `stdlib/core.mtl`; the resolver injection, the
> GlobalExports seed, and the name-mangling intermediate are all deleted.
> See `metel-interpreter/docs/METEL-181-handoff.md` for the landed state and
> ADR-0038/ADR-0039 for the architecture.
>
> Deviations from the plan as written: the three-variant `CalleeId` enum was
> never introduced (decision 12); `StdPrelude` was renamed and retained as the
> derived `CorePrelude` rather than deleted (decision 13); §A.3's "full"
> overload ranking was superseded by exact-match-only (decision 9). Residual
> string lookups are tracked in METEL-185 (type registries + method-level ids
> + aspect string fallback) and METEL-187 (lexical-env function lookup).

1. **`CalleeId` keeps three variants.** *(Design for METEL-181; 180 shipped with
   mangling instead — see decision 8.)* Dynamic aspects make `AspectMethod`
   necessarily distinct from `Method`: static method dispatch has a known
   concrete receiver `SymbolId`; aspect dispatch resolves via a vtable for
   `dyn Aspect` receivers. Same `CalleeId` variant, two backends — but a
   different mechanism from `Method`. `AspectMethod` intentionally omits
   `recv`.
2. **Closed `NativeKey` enum.** Compile-time coverage checks and no
   string-keyed runtime dispatch — that is the point of this sprint.
   Third-party native providers are an FFI-era problem.
3. **Multi-file `std::core`.** Loader takes a manifest of
   `(module_path, embedded_source)` pairs and walks it like the disk. One
   extra `match` in the loader now; avoids re-splitting later as stdlib
   grows (`io`, `collections`, `time`, …).
4. **No rollback feature flag.** A flag re-creates the `StdPrelude` /
   `register_builtins` duplication the sprint exists to delete. Stage A → B
   → C as separate commits on `sprint/22`, tree green at each step.
5. **`SourceProvider` receives both the module path and the resolved file path.**
   As-built: `fn read(&self, module_path: &[String], file_path: &Path)`. The
   loader discovers files by multi-candidate probing (`parser.mtl` vs
   `parser/ast.mtl`, longest prefix wins), which a pure segment→path join
   cannot reproduce — so the resolved `file_path` is passed alongside the
   logical `module_path`. `FsSourceProvider` reads the file path;
   `EmbeddedStdlibProvider` (METEL-181) will key on the module path and fall
   through to the file path. *(Supersedes the earlier "keyed by `&[String]`
   only" plan in RFC-0058.)*
6. **Goto-definition on re-exports resolves to the original definition.**
   Natural consequence of `SymbolTable::intern` keying on `(source_module,
   source_name)` — two imports of the same re-exported symbol share a
   `SymbolId`. No extra tracking needed.
7. **`definitions` stores declaration spans.** Populated for every top-level
   declaration during name resolution. Method-level coverage arrives with the
   METEL-181 method-`SymbolId` allocation. Hover uses the typed AST directly;
   the definitions map is for navigation and diagnostics.

### Decisions made during implementation (sprint 22)

8. **Overload dispatch via name-mangling (intermediate), not `CalleeId`.**
   METEL-180 gives each overloaded definition a unique mangled runtime name
   (`print$i32`, `print$i64`) and rewrites the declaration and every call site
   to it in construction, so the runtime needs no overload-specific logic.
   Single-definition functions are never mangled. This is a stepping stone:
   the overload *selection* logic (`overload::build_overload_table`, `select`)
   is permanent, but the string `mangle`/`type_mangle` machinery was deleted
   later in the same sprint when each overload gained a `SymbolId` and call
   sites began carrying `callee_id` (see decision 12 and ADR-0038).
9. **Overload ranking is exact-match only.** A candidate matches only when the
   argument types equal its parameter types exactly; no implicit numeric `From`
   coercion participates in selection. Chosen because coercion would make
   multiple candidates viable (`1i32` matches `i32` exactly *and* `i64` via
   coercion), forcing specificity ranking. Coercion still applies to
   non-overloaded calls.
10. **`SymbolId` dispatch scope is callables only.** METEL-181 rekeys functions,
    methods, and aspect methods to `SymbolId` dispatch after name resolution.
    The struct/type/enum registries (`TypeDefinitionRegistry`,
    `RuntimeRegistry.types`) stay name-keyed; rekeying them is a separate
    follow-up tracked in **METEL-185**.
11. **`Display`/`to_string` covers all numeric primitives.** A latent gap
    registered Display/`to_string` only for `i64`/`f64`; the fix (single
    `primitive_type_name` source of truth + a registration loop across all
    sized integers and `f32`) was required by the METEL-180 acceptance test,
    whose body displays an `i32`. Landed as its own commit. (Later subsumed:
    the impls now live in `stdlib/core.mtl` as real declarations.)

12. **No `CalleeId` enum; `Option<SymbolId>` on `Call` instead.** Only free
    functions can be overloaded, so the typed AST carries
    `TypedExpr::Call::callee_id: Option<SymbolId>` and
    `TypedFunDecl::symbol_id: Option<SymbolId>`; the evaluator dispatches
    `Some(id)` calls through a SymbolId-keyed registry
    (`RuntimeRegistry::symbol_values`). Overload SymbolIds come from a
    process-global allocator in a dedicated range
    (`symbols::OVERLOAD_SYM_START = 0x4000_0000`), not from the name
    resolver's `SymbolTable` — the §A.2 multi-id interning design was never
    needed. The three-variant enum can arrive with METEL-185's method
    rekeying. Overloads never enter the name-keyed scheme env or the export
    surface. (ADR-0038.)

13. **`CorePrelude` retained (renamed from `StdPrelude`), not deleted.** The
    single-program pipeline (`check`/`evaluate_with_ctx`) performs no module
    loading, so it still needs per-context seeding — but the prelude is now a
    pure *derivation* of the embedded `stdlib/core.mtl`
    (`populate_schemes_from_embedded_core`), not a hand-maintained list.
    Likewise `register_builtins` survives as a thin shell: the embedded-core
    derivation call plus the String/array `len` pattern methods and the
    Range/RangeInclusive Iterable impls, none of which are expressible as
    named-type declarations. The §C.2 "delete StdPrelude / register_builtins"
    bullets are superseded in this form. (ADR-0039.)

14. **Value-driven native keys.** One `@std.core.to_string` key serves all 13
    primitive Display impls (the host formats by runtime value); the numeric
    `From` cross-product uses one key per *target* type (the source type
    travels in the value; `u32`'s host also accepts `Char`). 27 keys total
    cover the full core surface.

15. **Follow-ups filed from the post-sprint string-dispatch audit.**
    METEL-185 (expanded): type-registry rekeying + method-level SymbolIds in
    `MethodCall`/`MethodDispatch` + deletion of the evaluator's aspect
    string fallback (root cause: single-program embedded-core seeding
    registers aspect methods with `aspect_id: None`). METEL-187 (new):
    symbol-keyed resolution for ordinary function values in the lexical
    environment — an architectural question about first-class values, kept
    out of METEL-185. METEL-186 (new): RFC-0060 aspect impl coherence /
    orphan rule.
