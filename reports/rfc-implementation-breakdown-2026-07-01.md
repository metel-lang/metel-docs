---
id: rfc-implementation-breakdown-2026-07-01
title: "Accepted RFCs — Implementation Work Breakdown"
type: report
created_date: '2026-07-01'
---

# Accepted RFCs — Implementation Work Breakdown

*Companion to `strategic-overview-2026-07-01.md`. The strategic overview establishes that
Phase 1 (type system) and Phase 2 (region system) design are complete, with 23 accepted RFCs
specifying a coherent language the interpreter does not yet enforce. This document breaks the
implementation of those 23 RFCs into workstreams with dependencies, complexity, and a sequencing
plan.*

*Sequencing strategy: **dependency-pure** — build the static type-system layer (Cluster A) before
the runtime ownership/region layer (Cluster B), converging on the capstone items in Phase 4.*

---

## Scope at a Glance

| Cluster | RFCs | Nature | In interpreter today? |
|---|---|---|---|
| **A. Type system (static)** | 0060, 0036, 0061, 0072, 0081, 0082, 0037, 0008 | Upgrade the existing basic-aspect HM system to full coherence / conditional / associated-type / negative / trait-objects | Basic aspects + bounds + generics exist; none of these 8 do |
| **B. Region & ownership (runtime)** | 0071, 0063, 0065, 0066, 0067, 0068, 0069, 0073, 0074, 0077 | Entirely new memory model: affine types, borrow checker, regions, allocators | None exist; today is GC-via-`Rc` + deep-clone-on-bind |
| **C. Stdlib & misc** | 0078, 0079, 0080, 0083, 0084 | Polish + new stdlib aspects + module value exports | 0078/0079/0084 substantially done (residual only); 0080/0083 not started |

The interpreter today is a tree-walking Rust program (`metel-core/metel-interpreter`, v0.9.1):
PEG parser (`src/grammar.pest`) → name resolver → path normalizer → two-pass typechecker
(`src/typechecker/`, HM with let-polymorphism) → elaborator → evaluator. The typechecker keys
aspect-impl resolution on **string type names** (`impl_aspect_env`), enforces **no** coherence,
and the evaluator **deep-clones every value on bind**. Both of these are load-bearing obstacles
for the accepted RFCs and are called out as prerequisites below.

---

## Already-Done / Verify-Only (Quick Wins)

These three are substantially implemented; schedule the residual work as low-risk wins.

- **RFC-0078 (`!`)** — `Never` unifies with anything; numeric defaulting present. *Residual:* expose
  `!` as a writable type in any position, uninhabited-variant exhaustiveness, inhabited-singleton
  coercion insertion, `-> !` divergence analysis, the `AllocationError = !` allocation rule (needs
  0063). **M.**
- **RFC-0079 (`Perhaps`/`Result`)** — both sum types live in `std::core`. *Residual:* `?` propagation
  operator, remove the `if name == "yolo"` special-case in favour of method dispatch, fill the method
  set (`.unwrap_or_else`, `.ok_or`, `.map_err`, `.ok`), unqualified `None` sugar. **M.**
- **RFC-0084 (`T[N]`)** — `Type::SizedArray` and `[T; N]` parse. *Residual:* swap to postfix `T[N]`
  grammar, drop `[expr; N]` repeat construction, spec/RFC example sweep. **S.**

---

## Cross-Cutting Prerequisites (The Critical Path)

Shared foundations that unblock both clusters. Most of the real risk lives here; these should land
early and be designed for extension.

1. **Impl-resolution refactor.** Replace the string-keyed `impl_aspect_env` (`src/typeinference/mod.rs`)
   with a structured `ImplKey { aspect: DefId, type_head, type_args, bounds, polarity }` and a
   resolution function returning `{ found: Option<ImplDefId>, via: Negative|Explicit|Auto|Blanket,
   trace }`. Required by 0060, 0036, 0061, 0072, 0081, 0082, 0080. **The single biggest static prerequisite.**
2. **`DefId`/module-id** for orphan classification (is this aspect/type local, or `std::core`-local?).
   Needed by 0060, 0081, 0061. String-name comparison is insufficient.
3. **New coherence pipeline stage** (between name resolution and typecheck inference): collect all
   impls (positive, negative, auto-synthesized, structural), run orphan filter + overlap scan + auto-impl
   synthesis, hand a frozen impl registry to the typechecker under the closed-world assumption.
4. **AST generalizations — one refactor, serves many RFCs.** `Bound { polarity, equality-constraints }`,
   `TypeRef { structural, dyn, projection }`, `ImplBlock { polarity, where_clause, associated_type_defs,
   span }`. Avoids three parallel bound/impl representations.
5. **New borrow/region-checker pipeline stage** (between typecheck and evaluator): region-handle liveness,
   `Outlives` constraint solving, borrow exclusivity (`&mut` vs `&`), wellformedness, move/affine tracking.
   **Brand new — the largest single piece of work in the whole effort.**
6. **Value-representation overhaul (RFC-0071 §1).** Replace deep-clone-on-bind with move-on-bind plus
   deterministic drop glue. Conflicts fundamentally with the current `Rc`/`RefCell` eval model.
   **The dominant runtime risk.**
7. **Fat-pointer `Value` variant** (`data_ptr, vtable_ptr`) for RFC-0008; coordinate its drop path with
   the ownership model (0061/0071).
8. **Stabilize `SymbolId` with a dedicated generation pass after the inference pass.** Today `SymbolId`s
   are minted during name resolution and threaded through a pipeline whose later stages (two-pass
   typecheck, monomorphisation-by-reconstruction, cross-module TypeVar alpha-renaming into the
   `2_000_000+` range) interact with symbol identity in inconsistent, leaky ways. Rather than inherit
   that inconsistency, introduce a single `SymbolId` generation pass that runs **after inference** and
   assigns stable identifiers from a settled, post-inference view of the program. **Leave the current
   scheme in place and you risk committing the whole forthcoming feature set to an inconsistent, leaky
   architecture** — every coherence query, associated-type projection, negative-impl lookup, and region
   wellformedness check (prereqs 1, 3, 5) leans on symbol identity, so this must be stabilized *before*
   Cluster A is built on top of it. Targeted at Phase 0 as foundational plumbing.

---

## Cluster A — Type System (Static, Low Runtime Risk)

Order from the dependency analysis. 0060 is the root; almost everything else keys off its
resolution function and coherence pass.

| # | RFC | Complexity | Depends on | Unblocks |
|---|---|---|---|---|
| 1 | **0060** Coherence — orphan rule, overlap detection, CWA, auto-impl, priority resolution + the resolution refactor (prereq 1–3) | **XL** | — | all of A; 0080, 0074 (B) |
| 2 | **0036** Conditional impl blocks — `where` on impl; use-site applicability; syntactic-negation disjointness | M | 0060 | 0061, 0072§4 |
| 3 | **0072** Negative bounds — `!Aspect` polarity flag; inverted discharger; `Copy ⇒ !Drop` rule | S | 0060 | 0066, 0073, 0074, 0081 |
| 4 | **0081** Negative impls — `impl !Aspect for T {}` (empty body); negative registry; priority item 1 | S | 0060, 0072 | 0074, 0080 |
| 5 | **0082** Associated types — `type X;` / `type X = T;`; projection; equality-constraint unification; amends 0069's `SubRegion` form | **L** | 0060 | 0063, 0080, 0008 §6 |
| 6 | **0061** Structural aspect bounds — blanket impls for `T[]`, `(A,B)`, `fun(A)->B`; `Callable`; Send/Sync/Drop auto-propagation | M | 0060, 0036 | — |
| 7 | **0037** Return-position `impl Aspect` — opaque anonymous type per fn; return-site unification | S/M | 0060 | — |

**Dependency graph (Cluster A):**
```
0060 ─┬─► 0036 ──► 0061
      ├─► 0072 ──► 0081
      ├─► 0082
      └─► 0037
```

RFC-0008 (`dyn Aspect`) is part of Cluster A conceptually but deferred to Phase 4 — it needs the
fat-pointer value variant, object-safety analysis (0082 §6), and a coherent drop path (0071).

---

## Cluster B — Region & Ownership (New Memory Model, Highest Risk)

0071 is the root. The borrow/region-checker stage (prereq 5) is built with 0063 and is touched by
nearly every item in this cluster — design it as one extensible stage with sub-passes, not per-RFC checks.

| # | RFC | Complexity | Depends on | Notes |
|---|---|---|---|---|
| 1 | **0071** Ownership & move semantics — affine types, `Copy`/`Clone`/`Drop`, drop order, partial moves | **L** | — | drives the value-repr overhaul (prereq 6) |
| 2 | **0063** Region handles — `@[r] T`, bracket channel, `Region` aspect, allocation expressions, **borrow-checker stage** (prereq 5) | **XL** | 0071 | introduces the new stage |
| 3 | **0067** Reference types — `&T`/`&mut T`, auto-deref, deref coercions; **removes** `*T`/`*mut T`/`*p` | M | 0063 | **batch with 0066** (mutually amend) |
| 3 | **0066** Region pointer extraction — borrow-deref, move-out/copy-out, `T: !Drop` legality matrix | M | 0063, 0065, 0072 | batch with 0067 |
| 4 | **0065** Region ergonomics — `@` elision, call-site inference, `use`-gated candidate set | M | 0063 | |
| 5 | **0068** Struct-owned regions — `[own r]`, implicit impl scope, synthesized ctor/dtor, `Outlives` auto-derivation | M/L | 0063, 0065, 0067 | |
| 6 | **0069** Sub-region typing — `SubRegion<R>`, allocation-site inference, transitive `Outlives` | M | 0063, 0068 | 0082 amends its form |
| 7 | **0077** Region generics — impl headers, wellformedness, variance (wellformedness ↔ variance tension) | **L** | 0063, 0065, 0068, 0069 | |
| 8 | **0073** AutoRegion — strategy selection; ship the sound "heap-everything" fallback first | **L** | 0063, 0065, 0066, 0071, 0072 | under-specified (UQ1/2/5) |

**Dependency graph (Cluster B):**
```
0071 ──► 0063 ─┬─► 0067 ◄──┐
               ├─► 0066 ◄──┤  (batched; 0067/0066 amend each other)
               ├─► 0065    │
               ├─► 0068 ──► 0069 ──► 0077
               └─► 0073

0074 (Rc/Arc) ──► needs 0071, 0072, 0081, 0080, 0076(brand)  [Phase 4]
```

---

## Cluster C — Stdlib & Misc

| # | RFC | Complexity | Depends on |
|---|---|---|---|
| 1 | **0084** Array syntax `T[N]` (residual) | S | — |
| 2 | **0083** `pub let` — four edits: AST `visibility` on `LetDecl`, parser, name-resolver arm, evaluator module-scope exposure | S | RFC-0030 (done) |
| 3 | **0078** `!` (residual) | M | 0071 (move parts); 0063 (alloc rule) |
| 4 | **0079** `?` + methods (residual) | M | 0078 |
| 5 | **0080** Stdlib aspects — `Clone`/`Deref`/`DerefMut`/`Send`/`Sync`, auto-impl, `#[derive(Clone)]`, Deref coercion | **XL** | 0060, 0081, 0074, 0067 |
| 6 | **0074** Rc/Arc — refcounting, `SharedPointer` aspect, `!Send`/`!Sync` | M | 0071, 0081, 0080, (0076 brand = deferred) |

Intra-cluster edge: only 0078 → 0079. The rest are mutually independent and depend only on
external RFCs.

---

## Proposed Sequence (Dependency-Pure)

**Phase 0 — Foundations & quick wins**
- **`SymbolId` generation pass after inference (prereq 8)** — stabilize symbol identity first; every
  downstream feature leans on it. Do this before any Cluster A work.
- AST generalizations (prereq 4) — shared prep for both clusters.
- RFC-0084 (array `T[N]`), RFC-0083 (`pub let`) — independent; unblock `std::mem::heap`/`local_heap`.
- RFC-0078/0079 *static* residuals (exhaustiveness, `?` operator, method set). *Move-dependent parts
  deferred to Phase 2.*

**Phase 1 — Static type layer (Cluster A)**
0060 → 0036 → 0072 → 0081 → 0082 → 0061 → 0037.
Coherence + the resolution refactor (0060) is the gate. This phase is largely runtime-independent —
it can proceed without touching the evaluator. RFC-0008 deferred to Phase 4 (needs fat pointers).

**Phase 2 — Ownership & value overhaul**
RFC-0071 (move semantics, `Copy`/`Clone`/`Drop`, drop glue) plus the value-representation change
(prereq 6). Carries the 0078/0079 move-dependent residuals (`.map` moves, `!`-value move semantics).

**Phase 3 — Region system (Cluster B)**
0063 (borrow-checker stage) → 0067 + 0066 (batched) → 0065 → 0068 → 0069 → 0077 → 0073.

**Phase 4 — Convergence (needs both clusters)**
RFC-0080 (stdlib aspects) → RFC-0074 (Rc/Arc) → RFC-0008 (`dyn Aspect`). These are the capstone
items that depend on the static layer (A) and the runtime layer (B) being complete.

---

## Cross-Cluster Dependency Notes

Cluster B is not self-contained — it depends on several Cluster A items. This is why the
dependency-pure order puts A first:

- **0066** needs **0072** (negative bounds, for the `T: !Drop` move-out rule).
- **0073** needs **0072** (negative bounds).
- **0074** needs **0072**, **0081** (negative impls for `!Send`/`!Sync`), and **0080** (Send/Sync auto-impl).
- **0080** needs **0060** (closed-world coherence for auto-impl), **0081**, **0082** (associated-type
  projection for `Deref::Target`), and **0067** (Deref coercion).

The borrow checker (0063) and the coherence engine (0060) are the two large greenfield subsystems;
everything else composes on top of them.

---

## Flags Worth Keeping in View

- **RFC-0064 (Fork-Join Parallelism)** is still a **draft** — the strategic overview's "immediate"
  design item and the one remaining Phase 2 design piece. It is out of scope for *implementation* of
  the accepted RFCs, but it blocks the concurrency story; 0073 and 0074 both reference it. Scope it
  soon.
- **RFC-0076 (Brand Types)** is **under review** (Q1 — brand introduction mechanism — unresolved).
  RFC-0074's `RcToken` future work depends on it; the accepted portion of 0074 can ship without it.

---

## Biggest Risks

1. **The borrow checker is brand new.** No existing stage does region liveness, `Outlives` solving, or
   borrow exclusivity. Dominant cost and risk of the whole effort.
2. **Deep-clone-on-bind conflicts with move semantics (0071).** A value-representation change, not just
   a typecheck change — it ripples through the entire evaluator.
3. **Wellformedness vs variance constrain in opposite directions (0077 §4.4).** The most error-prone
   type-system interaction.
4. **AutoRegion is under-specified (0073 UQ1/2/5).** Even the sound "heap-everything" fallback requires
   correct drop tracking; risk of a sound-but-misleading implementation.
5. **Sendability auto-impl vs negative impls (0074 §2.6).** Without correct negative impls, `Rc<T>`
   would silently become `Send` — a data-race bug.
6. **`@[r] T` instance-level distinctness (0063).** Tags distinguish *instances*, not types — unusual,
   affects type equality/hashing/caching throughout the typechecker.
