# Engineering Standards

metel-core#1157. Standards this codebase holds itself to — not what the system *is*
(`architecture/spec/*.md`), but what a change to it is expected to respect.

Each entry: **Rule**, **Rationale**, **Examples / Counterexamples** (grounded in this
repository), **Enforcement** (how it's checked, if at all — "none yet" is a valid
answer), **Exception process**, **Expiry**.

## 1. One-way dependency: `metel-frontend` never depends on `metel-interpreter`

**Rule.** The frontend crate (module loading through elaboration) never depends on the
interpreter crate (the evaluator and its runtime). Dependencies flow one way:
`metel-interpreter` → `metel-frontend`.

**Rationale.** The frontend must stay usable as an analysis library independent of any
one execution strategy — the current tree-walking evaluator (`LIMIT-EVALUATION-004`), a
future compiler backend (ADR-0004), or a tooling consumer (LSP, browser playground) that
never runs a program.

**Examples / counterexamples.** Conforming: `metel-interpreter/Cargo.toml` depends on
`metel-frontend`; the reverse appears nowhere in `metel-frontend/Cargo.toml`. Violation: a
frontend module importing `metel_interpreter::evaluator::...` instead of duplicating the
needed logic or relocating it to the frontend.

**Enforcement.** Structural: Rust's crate graph forbids a cycle, so a reverse dependency
cannot compile. A new, narrower crate inserted between them that depends the wrong way is
a `Cargo.toml` change any reviewer sees directly.

**Exception process.** None on file. A boundary change of this kind needs
architecture-doc review and usually an ADR (`AGENTS.md`, Architecture invariants).

**Expiry.** Durable.

## 2. One authoritative owner per data model, table, and stable identity

**Rule.** A piece of durable identity (`SymbolId`, `TypeVar`, `BindingId`, a table keyed
by one of them) has exactly one allocator and one owner. A second, independent allocator
for the same identity space is a standing risk, not a convenience.

**Rationale.** ADR-0054's resolved-identity guarantee — identical IDs across runs
"regardless of file iteration order or parallelism" — holds per-allocator, not
automatically; nothing prevents a second allocator for the same space unless one is
deliberately excluded.

**Examples / counterexamples.** Conforming: `identity::allocate`'s structural allocators
(`BindingId`, `LocalId`) — one owner, checked-range construction. Violating, currently
live: `SymbolId`'s space is split across three independent allocators (`SymbolTable`'s
own counter, the overload table's process-global `AtomicU32`, `typeinference`'s
descending block-local counter) — `LIMIT-NAME-RESOLUTION-002/003/004/005`, with two
concrete bugs already caused (`metel-core#1228`, `#1229`: two impls or two overloaded
methods silently sharing one `SymbolId`).

**Enforcement.** None; caught by review recognizing the shape. A structural checker akin
to Standard 3's is a natural follow-up once the `SymbolId` unification those records call
for lands.

**Exception process.** A deliberately independent, scoped identity space gets a
`LIMIT-*` record stating why.

**Expiry.** Revisit once `LIMIT-NAME-RESOLUTION-002/003/004/005` close.

## 3. No unresolved source-name lookup after the resolution boundary

**Rule.** Once a module graph is resolved (`ResolutionMap`, the frozen IR), nothing may
key a lookup by `String` or `Span` — every reference already carries its resolved
identity, with no name-based fallback.

**Rationale.** Already true of this codebase and CI-enforced; stated here for the same
durable shape as the rest of this document.

**Examples / counterexamples.** `tools/check_no_semantic_name_lookup.py` scans the
frozen-IR files (`identity.rs`, `typed_ast/mod.rs`, `place.rs`, `query.rs`) for a
`HashMap`/`BTreeMap` field keyed by `String`/`Span`. `identity::position`
(`PositionIndex`) is the one sanctioned exception (rebuilt per snapshot, per ADR-0054).
The evaluator's `RuntimeRegistry` is a currently uncovered gap (`LIMIT-EVALUATION-003`) —
the natural next extension of `SCAN_FILES`.

**Enforcement.** `tools/check_no_semantic_name_lookup.py --check`, CI-gated.

**Exception process.** Inline `// resolution-freeze-allow: <reason>`, trailing the field
or immediately above it — same convention as `clippy-allow:`.

**Expiry.** Durable; bringing `RuntimeRegistry` under `SCAN_FILES` remains open
(`LIMIT-EVALUATION-003`).

## 4. Narrow phase APIs; no mutable, catch-all context exposed across a stage boundary

**Rule.** Each pipeline stage exposes one typed entry point that consumes the previous
stage's typed output and produces its own — never a shared mutable context a later stage
reaches into.

**Rationale.** A catch-all context crossing a boundary lets a later stage depend on an
earlier one's internal detail instead of its stated contract, which is what keeps stage
boundaries safe to reason about and to refactor independently.

**Examples / counterexamples.** Conforming: the documented pipeline (`ModuleGraph` →
`ResolvedNames` → `NormalizedModuleGraph` → `TypedModuleGraph` → `ElaboratedModuleGraph` →
evaluator), each arrow a typed value. A mutable context (`ConstructCtx`, `InferContext`)
staying inside one stage is fine. Violation: a later stage taking `&mut ConstructCtx`
instead of the `TypedModuleGraph` the typechecker hands off.

**Enforcement.** None automated. `AGENTS.md` already states "do not create a shortcut
entry point that silently skips stages"; a boundary change gets architecture-doc review.

**Exception process.** Same as Standard 1 — an ADR-level decision (Standard 9).

**Expiry.** Durable.

## 5. No production/test mixing

**Rule.** Production code in `src/` never branches on being under test (`cfg!(test)`, not
`#[cfg(test)]`) and never exposes a `pub`/`pub(crate)` item that exists only to be
reachable from a test. `#[cfg(test)] mod tests` colocated with the module it tests is not
itself a violation — but its body always lives in a sibling `tests.rs`, declared via `mod
tests;`, never written inline.

**Rationale.** A runtime branch on "am I under test" is a second, untested code path a
fixture can never catch, since the fixture triggers the other branch. `#[cfg(test)]`
itself excludes a nested test module from every non-test build at zero runtime cost and
lets it see its parent's private items under ordinary visibility rules — a fundamentally
different mechanism from the runtime `cfg!(test)` macro this rule targets. An
implementation file that also carries its own test bodies is harder to read as pure
production code, and an inline test module grows without the size pressure a separate
file provides.

**Examples / counterexamples.** Runtime-branch clause: no `cfg!(test)` branches or
test-only `pub` escape hatches found anywhere in `metel-frontend/src` or
`metel-interpreter/src`. File-separation clause: `identity.rs` → `identity/tests.rs` is
the only file using the required form; the other 27 files with `#[cfg(test)] mod tests`
write the body inline.

**Enforcement.** None yet for either clause. Intended shape: a `clippy_allow_ratchet.py`-
style checker with a grandfathered baseline (the 27 files, for the file-separation
clause); that check is purely syntactic, while the runtime-branch check needs to
distinguish legitimate test-support `cfg!(test)` from a real production branch.

**Exception process.** A deliberate `cfg!(test)` branch or test-only escape hatch gets an
inline `// test-support: <reason>` comment once the checker exists. The 27 unsplit files
are grandfathered by the eventual checker's baseline, not a per-file exception to
request; migrating one opportunistically alongside other work on that file is fine.
Scheduled as part of `metel-core#1231` (frontend pipeline reorganization).

**Expiry.** Revisit once the checker exists and has a real baseline; the file-separation
clause also tracks `#1231`.

## 6. Contract-focused tests at pipeline boundaries

**Rule.** A pipeline-boundary invariant gets a test that constructs the boundary's typed
input directly and asserts on its typed output — not only integration coverage that
happens to exercise the boundary.

**Rationale.** An end-to-end fixture proves a boundary works for the specific program it
contains, not the boundary's actual contract; a refactor that preserves every fixture's
output can still narrow or break the contract for a shape no fixture hits.

**Examples / counterexamples.** `metel-frontend/src/identity/tests.rs`: hand-constructed
`ModuleGraph`s asserting on `ResolutionMap` properties (structural identities, no
cross-body renumbering, distinct shadowing identities, a total reference table),
bypassing file loading entirely.

**Enforcement.** None automated; caught by a `review-typechecker`-style review pass
(`AGENTS.md`).

**Exception process.** None needed — additive to integration coverage, not a
replacement.

**Expiry.** Durable.

## 7. User-facing failures are diagnostics, not panics

**Rule.** A condition a Metel program's author can trigger is a typed `MetelError`
variant with a code and message, never a raw Rust `panic!`/`unwrap`/`expect` reaching the
user.

**Rationale.** A panic carries no error code, position, or actionable message, and
unwinds indiscriminately.

**Examples / counterexamples.** `MetelError`'s variants (`architecture.md`, "Error
Design"): `ParseError`/`TypeError` carry a code, message, span; `RuntimePanic` is the
typed representation of a user-triggered runtime failure (`.yolo()`, out-of-bounds,
division by zero) — a real Rust panic never reaches the user. `Internal` is reserved for
structurally impossible conditions; one a user can actually trigger is a bug, not a
correct use of the variant.

**Enforcement.** None automated; caught by review, and a real panic is highly visible in
any integration run.

**Exception process.** None for a genuinely user-reachable panic — see `Internal`'s scope
above.

**Expiry.** Durable.

## 8. Explicit, non-reentrant lifecycle for context objects

**Rule.** A context object that hands out identity (a generator, counter, allocator)
either owns its counter for the caller's whole allocating lifetime, or is documented by
name as a disposable snapshot that must not be reused after handoff.

**Rationale.** ADR-0044: a disposable `TypeVarGenerator` (`ctx.fresh_var_generator()`)
snapshotted a context's counter without advancing it; a scope with more than one
opaque-returning call reissued the same ids, aliasing an unrelated variable, surfacing as
an unrelated validation bug.

**Examples / counterexamples.** ADR-0044's fix is the conforming shape for that site.
`InferContext::split_gen(&self)` is a currently open instance of the same hazard: it
returns a generator without advancing the context's own counter, so continued allocation
after `split_gen` reissues already-claimed ids (`LIMIT-TYPE-INFERENCE-005`).

**Enforcement.** None automated.

**Exception process.** A context type genuinely meant to be split documents the
ownership transfer in its own doc comment — `TypeVarGenerator`'s module doc already does
this for the `split_gen`-then-thread-through-Pass-2 pattern.

**Expiry.** Revisit once `LIMIT-TYPE-INFERENCE-005`/`-006` close.

## 9. When an ADR is warranted

**Rule.** Write an ADR when multiple reasonable architectural choices exist, a prior
decision is being reversed, or a workaround would surprise a future contributor — not
for an ordinary local implementation decision with one clearly correct shape.

**Rationale.** Already stated in `AGENTS.md`'s Type-system invariants section; cited
here rather than restated.

**Examples / counterexamples.** A durable cross-stage representation, boundary, or
invariant (Standards 1, 2, 4, 8) is ADR territory. A local helper's name, or either of
two equally-fine control-flow structures, is not.

**Enforcement.** None automated — a judgment call by nature.
`architecture/tools/check_architecture.py` validates an ADR's structure once one exists,
never whether one should have been written.

**Exception process.** N/A.

**Expiry.** Durable.

## 10. Completion includes deleting expired shims — and telling one from a live boundary

**Rule.** A change is not complete while it leaves behind a compatibility shim, a
fallback path, or a stale distinction the change itself made unnecessary. Deleting a
real, still-load-bearing boundary because it merely resembles a shim is its own mistake.

**Rationale.** `metel-core#1054` deleted the frontend's `scopes` name-map outright once
every consumer was id-keyed. `metel-core#1147`/`#1149`: `module_loader.rs`'s
`canonicalize_existing` resembled the provider-bypassing shortcut `#1147` targeted; the
fix deleted only the one genuinely redundant call (a duplicate post-resolution
canonicalize in `Loader::load_module`) and kept the other three call sites, which back
`load_root_with`'s real on-disk-root requirement, distinct from `load_virtual_root_with`'s
deliberate non-canonicalization.

**Examples / counterexamples.** `#1054`: delete outright, nothing left depending on the
old path. `#1147`/`#1149`: delete only the redundant call; keep the call sites backing a
real, documented, still-necessary distinction.

**Enforcement.** None automated — a review-time judgment.

**Exception process.** None needed to delete (the default); keeping something that
resembles a shim gets a doc comment stating why, as `load_root_with`'s and
`load_virtual_root_with`'s own doc comments already do.

**Expiry.** Durable.

## 11. Do not use a magic number or range as the sole enforcement of a distinction

**Rule.** When two things must never collide or overlap (two allocators' output, two
identity spaces), the property that keeps them apart is a checked construction, a real
assertion, or a compiler-enforced type — never a hand-picked numeric constant or range
that nothing verifies stays correct.

**Rationale.** A magic number encodes an invariant only in the mind of whoever chose it,
with no mechanism to notice a second, unrelated choice reusing the same number, or a
range's real usage growing past the next one's start. The failure surfaces later, as an
unrelated-looking bug.

**Examples / counterexamples.** `SymbolId`'s three-way range split (Standard 2): builtins
occupy 1-99, the resolver's ids start at 1000, the overload allocator's at
`0x4000_0000` — `LIMIT-NAME-RESOLUTION-003`: "nothing checks that the resolver's range
stays below `OVERLOAD_SYM_START`." `TypeVarGenerator`'s six hard-coded offsets (10,000
through 5,000,000, scattered across six files) — `LIMIT-TYPE-INFERENCE-005`: the
2,000,000 start is already shared by two unrelated users. Conforming:
`identity::allocate::CollisionGuard` turns a `LocalId`/`RefId` structural-hash collision
into a loud `assert!` — "this exists so that 'unlikely' is enforced, not assumed."

**Enforcement.** None automated (would need to distinguish a load-bearing constant from
an ordinary one).

**Exception process.** A range that genuinely cannot be checked (an FFI boundary, a fixed
wire format) documents why beside it. A range inside this codebase's own control that
merely hasn't been made checked yet is not an exception — it's tracked as a `LIMIT-*`
record.

**Expiry.** Revisit once `LIMIT-NAME-RESOLUTION-002/003/004/005` and
`LIMIT-TYPE-INFERENCE-005` close.

## Post-refactor module structure (metel-core#1231)

The target this document's standards apply against once `#1231` (frontend
reorganization by pipeline stage) lands. Verified against real `use crate::...` edges,
not against the pipeline diagram alone — `ResolvedNames` (name resolution's own output)
is read directly by coherence, type checking, and elaboration, not only by its immediate
successor; `typeinference` is read directly by type checking's both passes and by move
check. The tree below accounts for that instead of assuming a stricter single-hop
handoff than the codebase actually has.

```
metel-frontend/src/
  pipeline/
    parsing/            module_loader.rs, parser/, type_alias.rs
    name_resolution/    name_resolver.rs, reference_resolver.rs
    path_normalization/ path_normalizer.rs
    coherence/          coherence.rs
    type_checking/      inference/, construction/, mod.rs, overload.rs, registry.rs,
                         conversions.rs, handoff.rs, object_safety.rs, projections.rs
    move_check/
    elaboration/

  ast/, typed_ast/, types/, error/     data definitions
  symbols.rs, identity/                identity backbone
  typeinference/                       HM substrate: type_checking's both passes, move_check
  place.rs, flow_state.rs              narrowing: type_checking, move_check
  stdlib.rs, native_keys.rs            parsing, type_checking, evaluator
  module_paths.rs                      parsing, name_resolution

  analysis.rs, query.rs                tooling API, not a pipeline stage

metel-interpreter/src/
  evaluator/       stage 08, stays in this crate
  orchestrator.rs  renamed from pipeline.rs (name collision with the frontend's new
                    pipeline/ directory otherwise)
```

**`type_checking/` holds two sub-passes, not two pipeline stages.** `typechecker/inference/*.rs`
and `typechecker/construction/*.rs` are already the two passes `AGENTS.md`'s Type-system
invariants section describes ("Inference emits constraints... Construction reads solved
results and builds typed AST"). They stay siblings under one stage directory, matching
that existing description, rather than becoming two top-level pipeline stages.

**A module joins the shared-substrate group only when a real cross-stage import
justifies it**, not by assumption — each entry above is backed by a direct `use crate::`
edge from a stage other than the one that "owns" the file. `symbols` and `identity` are
read from name resolution through the evaluator; `typeinference` from type checking and
move check; `place`/`flow_state` from type checking and move check; `stdlib`/
`native_keys` from parsing, type checking, and the evaluator; `module_paths` from parsing
and name resolution. `analysis`/`query` import each other and nothing pipeline-shaped
consumes either — a self-contained tooling surface, not a stage and not shared substrate.

**Resolved, from `#1231`'s own "Things to settle":**
- `type_alias.rs` is a sub-module of `pipeline/parsing/`, not its own stage — its only
  current caller is `module_loader`, and nothing here promotes it past that.
- The interpreter's orchestrator is renamed (`orchestrator.rs` or equivalent), not left
  colliding in name with the frontend's `pipeline/` directory.
- The move lands as one mechanical, move-only PR (`git mv` plus path fixes, reviewed as
  a rename check) followed by fix-ups — no re-export shims from the old paths. Standard
  10's discipline applies directly: a compatibility shim here would itself be the kind
  of thing that standard exists to keep out.

**Costs `#1231` itself already names, not repeated in full here:** the Atlas evidence
(`arch-implements`/`arch-verifies` markers, generated links, `last_reviewed`) is
path-keyed and needs a deliberate re-review pass after the move, not an assumption that
the audit will quietly follow renames; `tools/check_no_semantic_name_lookup.py`'s
`SCAN_FILES`, CI path filters, and any doc naming a file by path need updating in the
same change.

## Where this fits

Counterpart to [`PROCESS.md`](PROCESS.md) (the Architecture/Spec Atlas's own generation
pipeline) and `rfcs/PROCESS.md` (the RFC lifecycle) — separate documents for separate
domains. `metel-core`'s own `PROCESSES.md` is a script/CI-workflow inventory, not a
statement of engineering norms.
