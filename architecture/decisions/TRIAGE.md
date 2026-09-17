# ADR Lifecycle Triage

`#1158`. Every ADR in this directory gets an explicit lifecycle status —
**current** (a live architectural constraint), **superseded** (linked to its
replacement), **historical** (useful rationale, not normative today), or
**retired** (explicitly no longer applies) — plus, where its content is
covered by the Architecture Spec (`../spec/`), which section carries it
forward. This is the triage `#1158` asked for, redirected per explicit
instruction: split ADRs into spec sections and fold their still-live content
into those sections, rather than only labeling status in place.

**Method and its limits.** Every row below reflects at least a title/frontmatter
read; supersession links were verified by grep across the whole corpus (see
below), and every ADR cited in this triage as feeding a specific spec-section
`related` field was cross-checked against that section's current text. This is
not a line-by-line re-read of all 56 ADRs' full bodies — treat "current" as
"nothing found that contradicts it," not as "independently re-verified against
source the way `arch-*`/`LIMIT-*` records are." Two real, load-bearing
corrections *did* come out of this pass (below) — the method isn't just
mechanical box-ticking.

## Real corrections this triage produced

**`LIMIT-NAME-RESOLUTION-001`** originally cited `adr-0027` directly for "std::core
has no physical module file." `adr-0027`'s own frontmatter already reads
`status: superseded by adr-0039` — missed when the record was first filed
(grep context cut off before the file's own amendment note). Verified against
current source: real files exist at `metel-frontend/stdlib/*.mtl`, embedded at
build time (`build.rs`, `stdlib.rs`'s `EMBEDDED_STDLIB`), and the three-step
manual registration (`build_registry`/`pub_surface` injection/`StdPrelude`)
no longer exists in source at all. The record now carries `disposition:
resolved` with that evidence, not deleted — the historical fact and its
resolution both stay traceable. See the record itself for the full account.

**`LIMIT-TYPE-CONSTRUCTION-003`** (`?` error coercion needing an explicit
`From` impl) cited `evaluator.md`'s own text, which says the `From`-impl
check runs "during construction." Checked directly against current source
while adding `ADR-0030` as a `related` citation: the actual call site
(`ctx.has_from_impl`) is in `typechecker/inference.rs`, not
`typechecker/construction.rs` — `path_normalizer` desugars `?` into a
`PropagateError` node, but the compatibility check itself is an inference-pass
concern. Renamed to `LIMIT-TYPE-INFERENCE-001` and moved to `#type-inference`
(new `arch.type-inference.requirement-3`) rather than left misfiled under
`#type-construction` for consistency with a citation it happened to share.

## Supersession chains (verified by corpus-wide grep, not assumed)

- `adr-0016` → superseded by `adr-0028`
- `adr-0019` → superseded by `adr-0029`
- `adr-0027` → superseded by `adr-0039`
- `adr-0041`'s dual-keyed-rollout framing → superseded by `adr-0054` (stated in `adr-0054`'s own text; `adr-0041` itself otherwise stands)

## Triage table

Status legend: **C** current, **S→X** superseded by X, **H** historical, **—** no Architecture Spec section (foundational/cross-cutting, language-feature-scope, or docs/RFC tooling — out of the compiler-architecture spec's scope as currently written).

| ADR | Title | Status | Spec section |
|---|---|---|---|
| adr-0001 | TypeRegistry Structure and Location | H (effectively folded into adr-0025/adr-0032's unification) | type-inference |
| adr-0002 | Inference Pass Structure | C | type-inference |
| adr-0003 | v0.1 Feature Set Scope | H | — (language feature scope, not architecture) |
| adr-0004 | Interpreter Architecture | C | — (foundational; already `architecture.md`'s own cited rationale) |
| adr-0005 | if-Expression Grammar and AST Unification | C | parsing |
| adr-0006 | Evaluator Runtime Design | C, but frontmatter status is stale (`proposed` — the evaluator obviously exists; not corrected in this pass, flagged for whoever next touches this file) | evaluation |
| adr-0007 | Array Value Semantics via Deep-Clone at Bind Sites | C | evaluation |
| adr-0008 | Thread-Local Call Stack for Runtime Error Traces | C | evaluation |
| adr-0009 | Type Ascription Erased at Construction | C | type-construction |
| adr-0010 | Generic Monomorphization via Runtime Re-Construction | C | evaluation / type-construction (already cited — `LIMIT-EVALUATION-001`) |
| adr-0011 | Let-Polymorphism via `mono_env` Absence | C | type-inference |
| adr-0012 | Generic Struct Split-Env in Construction Pass | C | type-construction |
| adr-0013 | Aspect Impl Flat Env and Method Keys | C | evaluation (`RuntimeRegistry.pattern_methods`) |
| adr-0014 | Mut-Self Writeback for Iterators | H — likely resolved (its "known limitation" is absent from `evaluator.md`'s *current* Known Limitations list, checked directly this session; not confirmed by an ADR-side amendment, so marked historical rather than formally superseded) | evaluation |
| adr-0015 | Grammar Rule Ordering for Keyword-Prefix Identifiers | C | parsing |
| adr-0016 | Dedicated `Perhaps`/`Result` Value Variants | **S→adr-0028** | evaluation |
| adr-0017 | Operand Type Validation (T0005) in Pass 2 | C | type-construction |
| adr-0018 | `None` Literal Not a Keyword | C | parsing |
| adr-0019 | Flat Module Merge for Typechecker | **S→adr-0029** | evaluation |
| adr-0020 | Qualified Path Last-Segment Fallback | C | name-resolution |
| adr-0021 | Path Normalization Pre-Pass | C | name-resolution (now cited — `arch.name-resolution.requirement-4`) |
| adr-0022 | `check_graph` `GlobalExports` Accumulator | C | type-construction (already cited) |
| adr-0023 | Module Paths Are Hierarchical | C | parsing (now cited — `arch.parsing.requirement-1`) |
| adr-0024 | T0009 Detection in Typechecker, Not Name Resolver | C | type-construction |
| adr-0025 | Unified `TypeDefinitionRegistry` | C | type-inference (now cited — `arch.type-inference.requirement-2`) |
| adr-0026 | Glob Import Tiers | C | name-resolution (now cited — `arch.name-resolution.requirement-2`) |
| adr-0027 | `std::core` Virtual Module | **S→adr-0039** | name-resolution / parsing |
| adr-0028 | Enum Dispatch for `Perhaps`/`Result` | C (supersedes adr-0016) | evaluation |
| adr-0029 | Per-Module Isolated Environments | C (supersedes adr-0019) | evaluation (now cited — `arch.evaluation.requirement-1`) |
| adr-0030 | `?` Propagate-Error Desugar Pre-Pass | C | type-inference (now cited — `arch.type-inference.requirement-3`, `LIMIT-TYPE-INFERENCE-001`; moved here from an initial type-construction misplacement, see corrections above) |
| adr-0031 | Diamond Dependency Path Aliases | C | parsing (already cited) |
| adr-0032 | Type Registry Cross-Module Accumulator | H (overlaps adr-0025; not confirmed which is the current authoritative statement without a deeper read) | type-inference |
| adr-0033 | String Interpolation Lowered in Parser | C | parsing |
| adr-0034 | Aspect Defaults Synthesized in Construction | C | type-construction |
| adr-0035 | `TypedPlace` for Assignment Targets | C | move-check / type-construction (now cited — `arch.move-check.requirement-2`) |
| adr-0036 | Explicit Receiver Dispatch | C | type-construction |
| adr-0037 | Elaboration Boundary | C | elaboration (already cited) |
| adr-0038 | Overload Resolution, `SymbolId` Dispatch | C | type-construction (already cited — `LIMIT-TYPE-CONSTRUCTION-002`) |
| adr-0039 | Native Bindings, Embedded `std::core` | C (supersedes adr-0027) | parsing (now cited — `arch.parsing.requirement-2`) |
| adr-0040 | Test Harness Uses Full Module Pipeline | C | — (test infrastructure, not architecture) |
| adr-0041 | `SymbolId` Migration via Resolution Pass | C (framing partially superseded by adr-0054) | name-resolution (already cited) |
| adr-0042 | Resolution Completeness via Sealed Accessors | C | name-resolution / type-construction (already cited) |
| adr-0043 | Generic Type Arg Recovery from Field Values | C | type-construction |
| adr-0044 | Validation Strategy for Opaque Return Variables | C | type-construction |
| adr-0045 | Loop-Carried Moves via Back-Edge Accumulation | C | move-check (already cited) |
| adr-0046 | `T[]` Unconditionally `Copy` | C | type-construction |
| adr-0047 | Reject Non-Empty `drop()` Body | C | type-construction / coherence |
| adr-0048 | Frontend Workspace Boundary | C | — (foundational; already cited in `architecture.md`) |
| adr-0049 | RFC Section Fixture Coverage | C | — (docs/RFC tooling, not compiler architecture) |
| adr-0050 | Spec-Anchored Legality Coverage | C | — (docs/spec tooling) |
| adr-0051 | Single Public Docs Source | C | — (docs infrastructure) |
| adr-0052 | v0.13.0 Closure Cluster — Implementation Shape | C | move-check / evaluation (already cited — `LIMIT-MOVE-CHECK-001`) |
| adr-0053 | `dyn Aspect` — Tree-Walk Runtime Representation | C | evaluation |
| adr-0054 | Resolved Identity Freeze and Generic Instance Preparation | C | resolution (already the primary source) |
| adr-0055 | Architecture Integrity Records and Verification | C | — (the framework itself) |
| adr-0056 | Architecture Atlas Reader Is a Deferred Projection | C | — (the framework itself) |

## Not done in this pass

- No individual ADR file's own frontmatter was rewritten (status/date/scope
  backfill on the ~20 pre-frontmatter files, `adr-0006` through `adr-0024`ish,
  each still using a plain `**Status:**` header instead of YAML frontmatter).
  That's real, bounded, mechanical work — 20-some individual file edits — left
  for a follow-up rather than done speculatively here.
- `adr-0013`, `adr-0028`, `adr-0036`, `adr-0044`, `adr-0046`, `adr-0047` are
  marked current and section-mapped but not yet cited in that section's
  `related` field — real content, not yet folded in; a reasonable next
  increment, not done in this pass to keep this one bounded.
- Nine ADRs (adr-0004/0048/0055/0056 foundational; adr-0003 language-feature
  scope; adr-0040 test infra; adr-0049/0050/0051 docs tooling) intentionally
  have no spec section — they're current and real, just outside what the
  compiler-architecture spec (as scoped) covers.
