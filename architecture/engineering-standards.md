# Engineering Standards

metel-core#1157. A concise, versioned inventory of the standards this codebase actually
holds itself to, split out of the Architecture Atlas umbrella (metel-core#1141) because
it's a different kind of document from the Architecture Spec: not what the system *is*
(`architecture/spec/*.md`), but what a change to it is expected to *respect*.

Most of what follows normalizes an existing, working norm rather than inventing a new
one — several are already stated informally in `AGENTS.md` or already enforced in CI;
this document's job is to give each one the same shape, so a norm doesn't stay implicit
until someone breaks it by accident. Where a standard is genuinely new (not yet true of
the codebase), that is stated plainly, not smoothed over — see Standard 5 in particular.

Every entry below has the same six parts: **Rule** (the norm itself), **Rationale**
(why), **Examples / Counterexamples** (what conforming and violating code look like,
grounded in this repository, not hypothetical), **Enforcement** (how it's checked, if at
all — "none yet" is an honest answer, not a gap in this document), **Exception process**
(how to knowingly deviate), and **Expiry** (whether and when this standard itself is
revisited).

## 1. One-way dependency: `metel-frontend` never depends on `metel-interpreter`

**Rule.** The frontend crate (module loading through elaboration) must never depend on
the interpreter crate (the evaluator and its runtime). Dependencies flow one way:
`metel-interpreter` → `metel-frontend`, never the reverse.

**Rationale.** The frontend is meant to be reusable as an analysis library independent of
any one execution strategy — today's tree-walking evaluator (`LIMIT-EVALUATION-004`
records that this evaluator is a deliberate PoC, expected to be replaced), a future
compiler backend (ADR-0004), or a tooling consumer like an LSP or the browser playground
that never runs a program at all. A frontend that pulled in evaluator types could not be
used that way.

**Examples / counterexamples.** Conforming, verified directly: `metel-interpreter/Cargo.toml`
depends on `metel-frontend`; `metel-frontend/Cargo.toml` has no dependency on
`metel-interpreter` anywhere in its manifest. A violation would look like a frontend
module importing `metel_interpreter::evaluator::...` to reuse a runtime helper instead of
either duplicating the small amount of logic needed or moving the shared piece into the
frontend where both sides can reach it.

**Enforcement.** Structural, not a lint: Rust's crate graph does not allow a cycle, so the
reverse edge cannot compile once it exists. The only way to violate the *spirit* of this
rule without a compile error is to add a new, narrower crate between them that itself
depends the wrong way — a `Cargo.toml` change any reviewer sees directly.

**Exception process.** None on file. A workspace restructuring that needs to cross this
boundary is exactly the "boundary change requires architecture-doc review and usually an
ADR" case `AGENTS.md`'s own Architecture invariants section already states.

**Expiry.** Durable — this is a foundational boundary, not a temporary one.

## 2. One authoritative owner per data model, table, and stable identity

**Rule.** A given piece of durable identity (a `SymbolId`, a `TypeVar`, a `BindingId`, a
lookup table keyed by one of them) has exactly one allocator and one owner. A second,
independent allocator for the same identity space is a standing risk, not a convenience.

**Rationale.** ADR-0054 states the resolved-identity model's core guarantee: two runs over
the same resolved module graph produce identical IDs "regardless of file iteration order
or parallelism." That guarantee is per-allocator, not automatic — nothing prevents a
second allocator for the same nominal space unless one is deliberately kept from ever
existing.

**Examples / counterexamples — this one currently has known, tracked violations, not just
a hypothetical.** `identity::allocate`'s structural allocators (`BindingId`, `LocalId`)
are the conforming shape: one owner, checked-range construction, no second path to mint
one. The counterexample is real and already inventoried, not invented for this document:
`SymbolId`'s space is split across **three independent allocators** by convention alone
(`SymbolTable`'s own counter, the overload table's process-global `AtomicU32`, and
`typeinference`'s block-local counter descending from the top of the `u32` range) —
`LIMIT-NAME-RESOLUTION-002`, `-003`, `-004`, and `-005` are the Atlas records tracking
exactly this family of violation, down to the concrete bugs it has already caused
(`metel-core#1228`, `#1229`: two method impls or two overloaded methods silently sharing
one `SymbolId`). Citing the violations here rather than only the clean cases is
deliberate — this standard exists *because* the SymbolId family shows what happens
without it, and pretending the codebase already fully conforms would make this document
useless as a guide for recognizing the same mistake elsewhere.

**Enforcement.** None today beyond code review recognizing the shape ("does this add a
second counter for an identity another allocator already owns?"). A structural checker
in the spirit of `tools/check_no_semantic_name_lookup.py` (Standard 3) is a natural
follow-up once the SymbolId unification those `LIMIT-*` records call for actually lands —
premature before that, since it would need to special-case the very thing it's meant to
prevent.

**Exception process.** A record-worthy exception (a genuinely independent, deliberately
scoped identity space, not an accidental second allocator) gets a `LIMIT-*` record stating
why, the same way the existing SymbolId split already does.

**Expiry.** Revisit once `LIMIT-NAME-RESOLUTION-002/003/004/005` close — at that point this
standard should be checkable, not just statable.

## 3. No unresolved source-name lookup after the resolution boundary

**Rule.** Once a module graph has been resolved (`ResolutionMap`, the frozen IR), nothing
may key a lookup by `String` or `Span` — every reference must already carry the identity
resolution assigned it, with no fallback path that re-derives an answer from a name.

**Rationale.** This is the standard the acceptance criteria for this document calls out by
name as "already true" — stated here to give it the same durable shape as every other
entry, not to introduce a new rule.

**Examples / counterexamples.** Already CI-enforced, not aspirational:
`tools/check_no_semantic_name_lookup.py` scans a curated list of frozen-IR-holding files
(`identity.rs`, `typed_ast/mod.rs`, `place.rs`, `query.rs`) for a `HashMap`/`BTreeMap`
field whose key type mentions `String` or `Span`. `identity::position` (`PositionIndex`)
is the one sanctioned exception — rebuilt fresh per snapshot, never a durable artifact,
per ADR-0054's own design. The evaluator's `RuntimeRegistry` is a known, currently
*un*-covered gap in this same rule's spirit (`LIMIT-EVALUATION-003`) — named here as the
next natural extension of `SCAN_FILES`, not silently left out of this standard.

**Enforcement.** `tools/check_no_semantic_name_lookup.py --check`, CI-gated.

**Exception process.** An inline `// resolution-freeze-allow: <reason>` comment, trailing
the field or immediately above it — the same convention `clippy_allow_ratchet.py` uses
for `clippy-allow:`. Every exemption must justify itself so a reviewer can ask whether it
still holds.

**Expiry.** Durable, with one known open extension: bring `RuntimeRegistry` under
`SCAN_FILES` (`LIMIT-EVALUATION-003`'s own stated resolution path).

## 4. Narrow phase APIs; no mutable, catch-all context exposed across a stage boundary

**Rule.** Each pipeline stage exposes one typed entry point that consumes the previous
stage's typed output and produces its own — not a shared mutable context object that
downstream stages reach into.

**Rationale.** A catch-all context crossing a boundary is exactly what lets a later stage
depend on an earlier one's internal implementation detail instead of its stated contract,
which is what makes stage boundaries safe to reason about (and, eventually, to refactor
independently — the deliberately-not-yet-filed frontend reorganization `#1141` names as
following this spec, not preceding it).

**Examples / counterexamples.** The pipeline itself is the conforming shape, already
documented in `architecture.md` and `AGENTS.md`: `ModuleGraph` →
`name_resolver::resolve` → `ResolvedNames` → `path_normalizer::normalize` →
`NormalizedModuleGraph` → `typechecker::check_graph` → `TypedModuleGraph` →
`elaborator` → `ElaboratedModuleGraph` → the evaluator — each arrow a typed value, not a
shared mutable handle. Within one stage, a mutable context (`ConstructCtx`,
`InferContext`) is fine — it never crosses the stage's own public boundary. A violation
would look like a later stage taking `&mut ConstructCtx` (a typechecker-internal type)
as an argument instead of the `TypedModuleGraph` the typechecker is supposed to hand off.

**Enforcement.** None automated. `AGENTS.md`'s existing "Architecture invariants" section
already states "do not create a shortcut entry point that silently skips stages," which
this standard extends to the context-object shape specifically; a boundary change is
expected to get architecture-doc review per that same section.

**Exception process.** Same as Standard 1 — a boundary change warranting an exception is
an ADR-level decision (Standard 9), not a quiet one.

**Expiry.** Durable.

## 5. No production/test mixing — new standard, not yet true of this codebase

**Rule, stated precisely rather than as the issue's original shorthand:** production code
in `src/` must never branch on being under test (`cfg!(test)`, not `#[cfg(test)]`) and
must never expose a `pub`/`pub(crate)` item that exists *only* to be reachable from a
test rather than from a real caller. This standard does **not** forbid `#[cfg(test)] mod
tests` colocated with the module it tests — but a `#[cfg(test)]` unit-test module is
always declared as `mod tests;` pointing at a sibling `tests.rs` (or, for a directory
module, `<module>/tests.rs`), never with its body written inline in the same file as the
code it tests.

**Why the narrower reading of the first clause, stated honestly.** The issue that
requested this document phrased the mixing rule as "no `#[cfg(test)]` modules, fixtures,
test-only branches, or test-only escape hatches in application `src/`," bundling four
different things together. Taken completely literally, the first of those four would
flag **28 files** across `metel-frontend/src` and `metel-interpreter/src` — colocated
`#[cfg(test)] mod tests` is this codebase's normal, working, everywhere-established
convention, not an exception to it, and it's also the idiomatic Rust convention more
broadly (the Rust Book's own "Test Organization" chapter, `cargo new --lib`'s default
scaffold): a nested test module sees its parent's private items under ordinary Rust
visibility rules with no extra exposure, and `#[cfg(test)]` excludes it from every
non-test build at zero runtime cost — a fundamentally different mechanism from the
runtime `cfg!(test)` macro this standard actually targets, despite the similar name.
Writing a standard that banned it outright would contradict 28 files of existing,
idiomatic practice on day one. Audited directly for the other three (`cfg!(test)`
runtime branches, test-only `pub` escape hatches, baked-in fixture data): **none found**
anywhere in `metel-frontend/src` or `metel-interpreter/src`.

**The file-separation clause, added 2026-09-22 at the project's request, and the honest
state of the codebase against it.** Of the same 28 files, only **one**
(`metel-frontend/src/identity.rs`, via `#[cfg(test)] mod tests;` pointing at
`identity/tests.rs`) already uses the separate-file form this clause requires; the other
**27** write the test module's body inline. This is not the "already true" case Standard
3 is — it is closer to Standard 5's original first clause before that audit, a
genuinely new requirement with almost the whole codebase currently on the wrong side of
it. Stated plainly rather than smoothed over, the same way Standard 2's and Standard 8's
open violations are: adopting this clause is a real, sizable migration, not a
formality, and this document does not itself perform that migration — see Exception
process below for how the gap is carried in the meantime. The separate-file form is not
invented for this rule: `identity/tests.rs` already demonstrates it, and Rust's own
community guidance names splitting a test module into its own file (over moving it to
`tests/`) as the standard answer to a colocated test module growing large enough to hurt
incremental-compile time — this clause just makes that the rule for every file, not only
the one that happened to grow large enough to need it.

**Rationale.** The runtime-branch/escape-hatch clause: a branch on "am I under test" is a
second, untested code path hiding behind the real one — the exact shape of bug a fixture
can never catch, because the fixture itself triggers the *other* branch. The
file-separation clause: an implementation file that also contains its own test bodies is
harder to scan as pure production code (in a diff, in a file listing, in a reviewer's
first read), and inline test bodies grow without the natural size pressure a separate
file provides; splitting costs nothing semantically (`use super::*` still reaches the
parent module's items identically from a sibling file) and is already this codebase's own
proven shape in the one file that already needed it.

**Examples / counterexamples.** Conforming (runtime-branch clause): every one of the 28
`#[cfg(test)] mod tests` blocks audited — each is unit tests colocated with its module,
compiled out of any non-test build, never a runtime branch. Conforming (file-separation
clause): `identity.rs`'s `#[cfg(test)] mod tests;` + `identity/tests.rs`, the only current
instance. Violating (runtime-branch clause): `if cfg!(test) { .. } else { .. }` inside
real dispatch logic, or a `pub fn` whose only real caller is a test module in a different
file — neither found in an audit of this codebase. Violating (file-separation clause): the
other 27 files' `#[cfg(test)] mod tests { .. }` with the body written in place — found
throughout this codebase today, not hypothetical.

**Enforcement.** None yet for either clause — this is the "new enforcement surface" the
source issue itself says is a follow-up, not required by this document. The intended
shape, when built, is the same for both: a checker in `clippy_allow_ratchet.py`'s own
grandfathered-baseline pattern (a JSON baseline recording today's count per file — for
the file-separation clause, the 27 files above — new bare occurrences fail CI, existing
ones are not retroactively broken). The file-separation clause's check is purely
syntactic (does `#[cfg(test)]` precede `mod tests { ... }` or `mod tests;`?), simpler to
build correctly than the runtime-branch clause's, which needs to tell a legitimate
`cfg!(test)` use in test-support code from a real production branch.

**Exception process.** A deliberate, reasoned `cfg!(test)` branch or test-only escape
hatch gets an inline `// test-support: <reason>` comment — same shape as
`clippy-allow:`/`resolution-freeze-allow:` — once the checker exists to look for it. The
27 files not yet split are grandfathered by the same baseline the eventual checker will
carry, exactly like `clippy-allow-baseline.json` already grandfathers pre-existing Clippy
suppressions — not a standing exception to request per file, just the starting count a
ratchet checker would need. Migrating one of the 27 (moving its inline test body into a
sibling `tests.rs`, mechanically) is welcome opportunistically wherever a PR is already
touching that file's tests, but is not itself this document's job to schedule. Until a
checker exists, review is the only enforcement for both clauses, so a reviewer flags
either pattern by eye.

**Expiry.** Revisit once the checker is actually built and has a real baseline to compare
against; until then this standard is statement-only for both clauses, and the
file-separation clause additionally awaits a decision on whether/how to schedule the
27-file migration.

## 6. Contract-focused tests at pipeline boundaries

**Rule.** A pipeline-boundary invariant gets a test that constructs the boundary's typed
input directly and asserts on its typed output — not only integration coverage that
happens to exercise the boundary as a side effect of running a whole program.

**Rationale.** An end-to-end fixture proves a boundary works for the specific program it
happens to contain; it does not pin the boundary's actual contract, and a refactor that
preserves every fixture's output can still silently narrow or break the contract for a
shape no fixture happens to hit.

**Examples / counterexamples.** `metel-frontend/src/identity/tests.rs` is the conforming
shape already in the codebase: "adversarial fixtures for the resolved-identity contract"
that hand-construct a `ModuleGraph` directly and assert on `ResolutionMap` properties
(identities are structural, an edit to one body doesn't renumber another, shadowing
yields distinct identities, the reference table is total) — bypassing real file loading
entirely, the same way `metel-core#1147`'s own investigation notes this approach already
being used for import/module-path query coverage rather than building new end-to-end
fixtures for the same purpose.

**Enforcement.** None automated (no coverage-shape checker); a `review-typechecker`-style
review pass is where this gets caught today, per `AGENTS.md`'s existing verification
guidance.

**Exception process.** None needed — this is additive to integration coverage, not a
replacement for it, so there is nothing to except.

**Expiry.** Durable.

## 7. User-facing failures are diagnostics, not panics

**Rule.** A condition a Metel program's author can trigger is a typed `MetelError`
variant with a code and a message, never a raw Rust `panic!`/`unwrap`/`expect` reaching
the user.

**Rationale.** A panic gives no error code, no position, and no message a diagnostic
consumer (the CLI, a future LSP) can act on; it also unwinds indiscriminately, which a
typed error return does not.

**Examples / counterexamples.** `MetelError` (`architecture.md`'s own "Error Design"
section) already draws this line structurally: `ParseError`/`TypeError` carry a code,
message, and span; `RuntimePanic` is the deliberately-named, still-typed representation
of a *user-triggered* runtime failure (`.yolo()` on `nope`, out-of-bounds, division by
zero) — itself proof this standard is already a real design decision, not a new one,
since even a "panic" in Metel's own vocabulary is a typed value, not an actual Rust
panic reaching the process boundary. `Internal` is the escape hatch for a condition that
should be structurally impossible (an invariant violation, not a user mistake) — an
`Internal` the user can actually trigger by writing a particular program is itself a bug
in this standard's own terms, not a correct use of the variant.

**Enforcement.** None automated (no panic-linting pass); caught by review and, in
practice, by the fact that a real panic during interpretation is highly visible in any
integration run.

**Exception process.** None on file for genuinely user-reachable panics — see the
"structurally impossible" framing above; a would-be exception is evidence `Internal` is
being used to paper over a real, reachable case, which is the bug to fix, not the
standard to except.

**Expiry.** Durable.

## 8. Explicit, non-reentrant lifecycle for context objects

**Rule.** A context object that hands out identity (a generator, a counter, an allocator)
either owns the counter it hands out for the whole lifetime a caller might keep
allocating, or is documented, by name, as a disposable snapshot that must not be reused
after handing off — never silently in between.

**Rationale — and this rule exists because of a real incident, not a hypothetical one.**
ADR-0044 records exactly this mistake happening: call-site instantiation for an
opaque-returning function used a disposable `TypeVarGenerator`
(`ctx.fresh_var_generator()`) that snapshotted the context's real counter *without*
advancing it, so a scope with more than one opaque-returning call reissued the same ids —
aliasing an unrelated variable, with a failure that looked like an unrelated validation
bug until traced back to the generator itself.

**Examples / counterexamples — including a currently-open one.** The fix in ADR-0044 is
the conforming shape for that specific site. `InferContext::split_gen(&self)` is a
**currently open instance of the same hazard class**, not a hypothetical counterexample:
it returns a generator starting at the context's current counter *without* advancing the
context's own, so a context that keeps allocating after calling `split_gen` reissues ids
`split_gen`'s caller already claimed — tracked as `LIMIT-TYPE-INFERENCE-005`. Naming this
here rather than only citing the already-fixed ADR-0044 case is deliberate, for the same
reason Standard 2 names its own open violations: a standard that only cites its clean
precedent teaches less than one that also names the still-live case matching its own
description.

**Enforcement.** None automated. The shape a checker would need — flag a function
returning a fresh generator/counter derived from `&self` without also documenting
"disposable, do not reuse after this call" — is not yet built.

**Exception process.** A context type that is genuinely meant to be split and handed off
(not a bug) documents that explicitly in its own doc comment, naming the ownership
transfer, the way `TypeVarGenerator`'s own module doc already explains the
`split_gen`-then-thread-through-Pass-2 pattern for the cases where it's used correctly.

**Expiry.** Revisit once `LIMIT-TYPE-INFERENCE-005`/`-006` close (one allocator owning
the whole `TypeVar` space, replacing the constants and the `split_gen` hazard) — at that
point this standard's own currently-open counterexample goes away.

## 9. When an ADR is warranted

**Rule, consolidating what `AGENTS.md` already states rather than restating it
independently:** write an ADR when multiple reasonable architectural choices exist, a
prior decision is being reversed, or a workaround would surprise a future contributor —
not for an ordinary local implementation decision with one clearly correct shape.

**Rationale.** This line already exists in `AGENTS.md`'s Type-system invariants section;
duplicating it with different wording here would be exactly the two-sources-of-truth
problem the RFC-0055-lifecycle document (`rfcs/PROCESS.md`) and this codebase's own ADR
corpus have both hit before. Citing it, not re-deriving it, is the correct move.

**Examples / counterexamples.** A durable cross-stage representation, a boundary, or an
invariant (any of Standards 1, 2, 4, or 8 above, when actually changed) is ADR territory.
Picking a local helper function's name, or choosing between two equally-fine ways to
structure one function's internal control flow, is not.

**Enforcement.** None automated (an ADR's necessity is a judgment call by nature);
`architecture/tools/check_architecture.py` validates an ADR's *structure* once one
exists (frontmatter, status, supersession), never whether one *should* have been
written.

**Exception process.** N/A — this standard is itself the exception process for when a
decision needs one.

**Expiry.** Durable.

## 10. Completion includes deleting expired shims — and telling one from a live boundary

**Rule.** A change is not complete while it leaves behind a compatibility shim, a
fallback path, or a stale architectural distinction the change itself made unnecessary.
Equally: deleting a real, still-load-bearing boundary because it merely *resembles* a
shim is its own mistake, not a virtue.

**Rationale, with a real precedent for the harder half of this rule (telling the two
apart).** `metel-core#1054`'s fallback-removal sweep is the clean case: the frontend's
`scopes` name-map was deleted outright once every consumer was id-keyed, with nothing
left depending on the name-keyed path. `metel-core#1147`/`#1149` is the more instructive
case, because it is not clean: `module_loader.rs`'s `canonicalize_existing` (a real,
hardcoded `.canonicalize()` filesystem call) looked, at first glance, like exactly the
kind of provider-bypassing shortcut `#1147` was filed to remove. The actual fix (`#1149`)
deleted only the one call that really was redundant (a duplicate post-resolution
canonicalize in `Loader::load_module`) and *kept* `canonicalize_existing` at its other
three call sites — because those sites back `load_root_with`, which is documented to
require a real, on-disk root, unlike `load_virtual_root_with`, which is documented not
to canonicalize at all. Removing `canonicalize_existing` everywhere on the assumption
that "it looks like the same bug" would have broken the deliberate real-root-vs-virtual-
root distinction the fix was actually built to preserve.

**Examples / counterexamples.** `#1054`: delete outright, nothing left depending on the
old path. `#1147`/`#1149`: delete only the genuinely redundant call; keep the
call sites backing a real, documented, still-necessary distinction. The mistake this
standard actually guards against is treating every instance of a suspicious-looking
pattern as interchangeable, rather than checking whether each one is still load-bearing.

**Enforcement.** None automated — this is a review-time judgment, not a checkable
property.

**Exception process.** None needed in the "delete it" direction (that's the default);
choosing to *keep* something that resembles a shim gets a doc comment stating why, the
way `load_root_with`'s own doc comment already explains why it canonicalizes and
`load_virtual_root_with`'s explains why it deliberately does not.

**Expiry.** Durable — this is a standing discipline, not a time-bound rule.

## 11. Do not use a magic number or range as the sole enforcement of a distinction

**Rule.** When two things must never collide or overlap (two allocators' output, two
enum-like states, two identity spaces), the property that keeps them apart is a checked
construction, a real assertion, or a type the compiler enforces — never just a
hand-picked numeric constant or range that nothing verifies stays correct as the code
around it changes.

**Rationale.** A magic number encodes an invariant only in the mind of whoever chose it.
It has no mechanism to notice when a second, unrelated choice reuses the same number, when
one range's real usage grows past where the next one starts, or when someone adds a new
case without knowing the convention exists at all. The property degrades silently —
nothing fails until two things actually collide, at which point the failure looks like an
unrelated bug (aliasing, wrong dispatch, a "shouldn't happen" panic somewhere downstream),
not like what it actually is.

**Examples / counterexamples — the violations are real and already tracked, not
hypothetical.** `SymbolId`'s space (Standard 2's own example) is exactly this mistake:
builtins occupy 1-99, the resolver's ids start at 1000, the overload allocator's at
`0x4000_0000` — three ranges kept apart by comment and convention alone. `LIMIT-NAME-
RESOLUTION-003` states the consequence directly: "nothing checks that the resolver's
range stays below `OVERLOAD_SYM_START` or that the two ascending allocators stay clear of
the descending one." `TypeVarGenerator`'s hard-coded starting offsets are the same
mistake at a larger scale — 10,000, 1,000,000, 2,000,000, 3,000,000, 4,000,000, 5,000,000,
scattered across six files, with **the 2,000,000 start already shared by two unrelated
users** (`LIMIT-TYPE-INFERENCE-005`'s own finding, not a hypothetical risk). Both records
note the same thing this standard is built to prevent: "nothing enforces the widths."

The conforming shape already exists in the same codebase, right next to one of the
violations: `identity::allocate::CollisionGuard` turns a `LocalId`/`RefId`
structural-hash collision into a loud `assert!`-driven panic instead of a silently merged
identity, with a doc comment that states the philosophy this standard generalizes
verbatim — "this exists so that 'unlikely' is enforced, not assumed." That is the
difference: `CollisionGuard` doesn't just pick a hash width it hopes is wide enough and
stop there; it actively checks, every time, and fails loudly the moment the assumption
would have been wrong.

**Enforcement.** None automated (no scanner for bare numeric-literal range boundaries —
a real one would need to tell a load-bearing constant from an ordinary one, which isn't
a pattern-match). Caught by review today; the honest state matches Standard 2's own
open violations, since this is the mechanism-level version of that standard's
organizational point.

**Exception process.** A range or constant that genuinely cannot be checked (an FFI
boundary, a wire format's fixed layout) documents why in a comment beside it, the same
way an exemption anywhere else in this document does. A range inside this codebase's own
control that merely hasn't been made checked yet is not an exception — it's the debt
this standard exists to name, tracked the normal way (a `LIMIT-*` record, as the two
examples above already are).

**Expiry.** Revisit once `LIMIT-NAME-RESOLUTION-002/003/004/005` and
`LIMIT-TYPE-INFERENCE-005` close — the same expiry condition Standards 2 and 8 already
carry, since this standard, those two, and those five records are all facets of the same
underlying identity-allocation redesign.

## Where this fits

This document is the engineering-standards counterpart to
[`PROCESS.md`](PROCESS.md) (the Architecture/Spec Atlas's own generation
pipeline and invariants) and to `rfcs/PROCESS.md` (the RFC lifecycle) — three
different documents answering three different "how does this actually work, and why"
questions, kept separate because they cover genuinely different domains rather than
merged into one document that would serve none of the three well. `metel-core`'s own
`PROCESSES.md` is a fourth, adjacent one again: an inventory of scripts and CI workflows
across all four repositories, not a statement of engineering norms.
