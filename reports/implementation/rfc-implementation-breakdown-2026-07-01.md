---
id: rfc-implementation-breakdown-2026-07-01
title: "Accepted RFCs — Implementation Work Breakdown"
type: report
created_date: '2026-07-01'
---

# RFC Implementation Work Breakdown

*Companion to `strategic-overview-2026-07-05.md`. Updated 2026-07-05 to reflect the split
model: 8 accepted region RFCs moved back to under review and rewritten; 4 retracted (RFC-0069,
0085, 0086, 0087). The 14 accepted RFCs specify a coherent static type system and ownership
model; the 8 under-review allocator/lifetime RFCs specify the memory model (pending ratification
as RFC-0088). This document breaks the implementation of all 22 RFCs into workstreams.*

*Sequencing strategy: **dependency-pure** — build the static type-system layer (Cluster A) before
the runtime ownership/allocator layer (Cluster B), converging on the capstone items in Phase 4.*

---

## Scope at a Glance

| Cluster | RFCs | Nature | In interpreter today? |
|---|---|---|---|
| **A. Type system (static)** | 0060, 0036, 0061, 0072, 0081, 0082, 0037, 0008 | Upgrade the existing basic-aspect HM system to full coherence / conditional / associated-type / negative / trait-objects | Basic aspects + bounds + generics exist; none of these 8 do |
| **B. Allocator & ownership (runtime)** | 0071, 0063, 0065, 0066, 0067, 0068, 0073, 0077 | Entirely new memory model: affine types, borrow checker, allocators (`@a T`), lifetime anchors (`&r T`) | None exist; today is GC-via-`Rc` + deep-clone-on-bind |
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
5. **New borrow/allocator-checker pipeline stage** (between typecheck and evaluator): allocator-scope
   liveness (`@a T` tags vs allocator binding scope), lifetime anchor tracking (`&r T` valid while `r`
   alive), borrow exclusivity (`&var` vs `&`), wellformedness of nested allocator-tagged types,
   move/affine tracking. `Outlives` is **not** a constraint the checker solves — it is derived
   structurally from scope nesting. **Brand new — the largest single piece of work in the whole effort.**
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
| 4 | **0081** Negative impls — `extend T: !Aspect;` (empty body); negative registry; priority item 1 | S | 0060, 0072 | 0074, 0080 |
| 5 | **0082** Associated types — `type X;` / `type X = T;`; projection; equality-constraint unification | **L** | 0060 | 0063, 0080, 0008 §6 |
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

## Cluster B — Allocator & Ownership (New Memory Model, Highest Risk)

0071 is the root. The borrow/allocator-checker stage (prereq 5) is built with 0063 and is touched
by nearly every item in this cluster — design it as one extensible stage with sub-passes, not
per-RFC checks. RFC-0069 (SubRegion) is retracted; `Outlives` is not a constraint to solve —
it is derived from scope nesting by the checker.

| # | RFC | Complexity | Depends on | Notes |
|---|---|---|---|---|
| 1 | **0071** Ownership & move semantics — affine types, `Copy`/`Clone`/`Drop`, drop order with interleaved move-out | **L** | — | drives the value-repr overhaul (prereq 6) |
| 2 | **0063** Allocator handles — `@a T`, value-channel allocator params `(@a: A)`, `Alloc` aspect, allocation expressions, **borrow-checker stage** (prereq 5) | **XL** | 0071 | introduces the new stage; `@a` tag is instance-level, unusual for the typechecker |
| 3 | **0067** Reference types — `&r T`/`&r var T`, lifetime anchors, auto-deref, deref coercions; **removes** `*T`/`*mut T`/`*p` | M | 0063 | **batch with 0066** |
| 3 | **0066** Allocated value extraction — borrow-deref, move-out/copy-out, `T: !Drop` legality matrix | M | 0063, 0065, 0072 | batch with 0067 |
| 4 | **0065** Allocator ergonomics — `@` elision (single allocator in scope), lifetime anchor elision (4 rules) | M | 0063, 0067 | |
| 5 | **0068** Struct-owned allocators — `(@a: AllocType)` primary constructor, implicit `a` in impl scope, synthesized ctor/dtor | M/L | 0063, 0065, 0067 | `own` keyword dropped; no `Outlives` auto-derivation needed |
| 6 | **0077** Allocator generics — `<A: Alloc>(@a: A)` impl headers, wellformedness (scope-nesting derived), variance for `@a T`/`&r T`/`&r var T` | **L** | 0063, 0065, 0068 | wellformedness ↔ variance tension (§4.3) remains |
| 7 | **0073** AutoAlloc — strategy selection; ship the sound "heap-everything" fallback first | **L** | 0063, 0065, 0066, 0071, 0072 | under-specified (UQ1/2) |

**Dependency graph (Cluster B):**
```
0071 ──► 0063 ─┬─► 0067 ◄──┐
               ├─► 0066 ◄──┤  (batched; 0067/0066 amend each other)
               ├─► 0065    │
               ├─► 0068 ──► 0077
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

**Phase 3 — Allocator system (Cluster B)**
0063 (borrow-checker stage) → 0067 + 0066 (batched) → 0065 → 0068 → 0077 → 0073.
RFC-0069 is retracted; it is removed from the sequence. No `Outlives` constraint solver is needed.

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

The borrow/allocator checker (0063) and the coherence engine (0060) are the two large greenfield
subsystems; everything else composes on top of them.

---

## Flags Worth Keeping in View

- **RFC-0088 (Allocators and Lifetimes)** is the ratification vehicle for the split model. Until it
  is accepted, the 8 Cluster B RFCs are technically under review. Phase 3 implementation can begin
  against the settled model; ratification is a formality that does not block work.
- **RFC-0064 (Fork-Join Parallelism)** is still a **draft**. It is out of scope for implementation
  of the accepted RFCs, but it blocks the concurrency story. Scope it after ratification.
- **RFC-0076 (Brand Types)** is **draft** (Q1 — brand introduction mechanism — unresolved).
  RFC-0074's type signatures depend on it; RFC-0074 is in 0-draft pending RFC-0076.

---

## Biggest Risks

1. **The borrow/allocator checker is brand new.** No existing stage does allocator-scope liveness,
   lifetime anchor tracking, or borrow exclusivity. Dominant cost and risk of the whole effort.
2. **Deep-clone-on-bind conflicts with move semantics (0071).** A value-representation change, not just
   a typecheck change — it ripples through the entire evaluator.
3. **Wellformedness vs variance constrain in opposite directions (0077 §4.3).** The most error-prone
   type-system interaction; scope-nesting derived wellformedness and covariance must be reconciled.
4. **AutoAlloc is under-specified (0073 UQ1/2).** Even the sound "heap-everything" fallback requires
   correct drop tracking; risk of a sound-but-misleading implementation.
5. **Sendability auto-impl vs negative impls (0074 §2.6).** Without correct negative impls, `Rc<T>`
   would silently become `Send` — a data-race bug.
6. **`@a T` instance-level distinctness (0063).** Tags distinguish allocator *instances*, not types —
   unusual for a typechecker; affects type equality, hashing, and caching throughout.
