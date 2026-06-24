# Memory Strategy — Research Directions

**Date:** 2026-06-13  
**Status:** Research agenda — not a decision  
**Pauses the direction of:** RFC-0025, RFC-0056, RFC-0052, RFC-0051  
**Keeps:** RFC-0028 foundation (linear types, `@T`, `*T`)  
**Related:** `memory-model-programs.md` (Part 7), `regions-by-example.md`, `strategic-vision-2026-06.md`

---

## Why we are reconsidering

The region/lifetime line (RFC-0025, RFC-0056, RFC-0052, RFC-0051) was developed into a coherent design: the region handle carries the lifetime, annotations are optional via conservative inference, and the `region { }` block is aspect sugar mirroring `spawn { }`. The design is internally sound. The problem is its **strategic position**, surfaced by one question: *is this any different from a Rust crate?*

The answer is mostly no:

- **The runtime mechanism is `bumpalo`.** Scoped bump allocation with atomic free, an allocator passed as a value, and borrow-checked references that cannot escape the arena — all of this already exists as a Rust crate, on top of the *existing* borrow checker. `bumpalo`'s `&'bump T` is exactly RFC-0025's `*'r T` with `RegionFree` enforcement.
- **The only part that cannot be a library is "invisible lifetimes"** — conservative elision so the programmer never writes `'r`. Rust cannot do this (elision rules are hardcoded; `struct Parser { input: &str }` is a compile error), so it is genuinely additive. But it still reproduces *Rust's mental model, softened* — and it concentrates all the engineering risk in the single hardest area: cross-module lifetime inference and the diagnostics for lifetimes the programmer never wrote.

Net assessment: **high effort, derivative identity, and risk concentrated exactly where the design is weakest**, competing head-on with a mature incumbent. The strategic-vision report warned against becoming "technically respectable but strategically ordinary"; a softened reimplementation of Rust's regions is that risk made concrete.

This document does **not** discard the region work. It reframes the question — *which safety mechanism?* — and surveys the alternatives, so the next memory decision is made against the whole design space rather than the first path explored.

---

## The actual goal

Strip away "regions" and the goal is:

> **Memory safety and explicit allocation control, without Rust-level annotation burden, in an interpreter-first language.**

The decision variable is the **safety mechanism**. Lifetimes/regions are one mechanism. The most promising research of the last decade reaches the same goal by *avoiding lifetimes entirely* — and those are the non-derivative identities worth studying.

---

## The design space

The mechanisms fall into two families. **Family A — allocation & whole-value mechanisms** decide *how values are stored and reclaimed* (the original five). **Family B — capability & permission mechanisms**, drawn from the substructural-types survey (Bruzzone, "A Friendly Tour of Substructural, Uniqueness, Ownership, and Capabilities Types"), decide *who may access a value and how* — attaching the discipline to references, tokens, or the type context rather than to allocation. Family B matters most for Metel: several members are *top-down and modular* (no whole-program inference — the exact failure mode that sank the lifetime path) and compose with the linear types we are keeping.

**Family A — allocation & whole-value mechanisms.**

### 1. Lifetimes / regions — *the path just explored*

Static lifetime/region analysis; references are proven not to outlive their referent at compile time.

- **Prior art:** Rust, `bumpalo`, Cyclone, MLKit (Tofte–Talpin region inference), Vale's region layer.
- **Identity:** derivative. Even with invisible lifetimes, it is Rust's model softened.
- **Risk:** the inference and its diagnostics — the most expensive possible thing to build well.
- **Interpreter-first fit:** poor. It pushes toward a compile-time borrow-checker-lite, fighting the grain of an interpreter that does not *need* static lifetimes to run safely.

### 2. Mutable value semantics — **Hylo**

Safety falls out of *value semantics* plus the *law of exclusivity*: arguments are passed by `let`/`inout`/`sink`/`set` conventions, there is no first-class reference to alias, and the absence of aliasing is what makes mutation safe — **with no lifetime annotations and no borrow checker.**

- **Prior art:** Hylo (formerly Val); "Implementation Strategies for Mutable Value Semantics" (Racordon et al., 2022).
- **Identity:** novel. This is the closest existing answer to "Rust's safety without Rust's annotations," from a fundamentally different angle.
- **Read this first.** It directly attacks our exact goal.

### 3. Runtime-checked references — **Vale (generational references)**

Use-after-free is caught by a cheap **generation check at dereference** — each allocation carries a generation number; a reference stores the expected generation; a mismatch traps. No borrow checker, no lifetimes. Vale layers optional *region borrow checking* and "hybrid-generational memory" on top to elide checks where statically safe.

- **Prior art:** Vale (Evan Ovadia); generational references, hybrid-generational memory, region borrow checking.
- **Identity:** novel, and Vale's whole thesis is "regions + safety without a borrow checker" — they have already walked much of this road.
- **Interpreter-first fit:** excellent. A runtime check is nearly free in an interpreter that is already indirecting through values, and it dodges the entire static-inference risk.

### 4. Automatic reference counting + reuse — **Koka (Perceus), Roc, Lobster**

Precise reference counting where the compiler inserts `dup`/`drop` and, crucially, **reuse analysis** turns "drop then allocate same shape" into in-place mutation ("functional but in-place"). GC-free, pause-free, and **annotation-free**.

- **Prior art:** "Perceus: Garbage Free Reference Counting with Reuse" (Reinking, Xie, de Moor, Leijen, PLDI 2021); Roc's opportunistic mutation; Lobster's compile-time refcount elision.
- **Identity:** novel-ish and very practical. No manual memory management *and* no annotations.
- **Interpreter-first fit:** good. Refcounting is already the natural interpreter model; reuse analysis is the value-add and survives lowering to a compiler.

### 5. Linear / affine types as the whole story — **Austral**

Make linearity the entire memory-and-resource discipline; deliberately omit lifetimes and the borrow checker. Resources are used exactly once; this alone gives a large fraction of the safety with a fraction of the complexity.

- **Prior art:** Austral (Fernando Borretti); Linear Haskell.
- **Identity:** modest but coherent, and **we already have this** — it is RFC-0028, which survives any pivot.
- **Interpreter-first fit:** good; it is type-system-only and orthogonal to bulk allocation.

**Family B — capability & permission mechanisms** (from the substructural-types survey).

### 6. Reference capabilities — **Pony** — *the strongest new candidate*

A permission qualifier attached to the *reference*, not the object, so two references to the same value can carry different rights. Pony's six: `iso` (unique, mutable, sendable), `val` (deeply immutable, sendable), `ref` (mutable, local), `box` (read-only view), `trn` (writable, convertible to `val`), `tag` (identity only, sendable).

- **Prior art:** Pony (Clebsch et al.); Haller & Odersky, reference capabilities (2010).
- **Identity:** novel for Metel, and a strong fit. It is *top-down and modular* — it reasons about what flows *into* code without inspecting bodies, and works on precompiled libraries — so it eliminates the whole-program-inference risk that sank lifetimes. It also unifies three stories Metel already juggles into one mechanism: `iso` is the RFC-0003 `Send` transfer story, `val` is the `Arc`-shareable immutable, `box`/`ref` are read/write views. Metel's `Send`/`Sync` marker aspects are the seed of exactly this.
- **Interpreter-first fit:** excellent; qualifiers are annotation-light and largely defaultable/inferable, and can be partly enforced as runtime tokens (see synthesis). Cost: the *use/mention* gap — holding `writable` means you *could* write, not that you *do*.
- **The single strongest idea to evaluate from the survey.**

### 7. Linear capabilities / alias types — *separate the pointer from the permission*

The pointer becomes an ordinary, freely-copyable value; a distinct **linear** token `{ρ↦τ}` grants the right to dereference and free, and supports *strong updates* (changing the pointee's type). It is, almost literally, a separation-logic points-to assertion.

- **Prior art:** alias types (Walker, Morrisett, Ahmed); focus/adoption (Fähndrich & DeLine); made Cyclone practical.
- **Identity:** composes directly with the linear types we are keeping (RFC-0028), and reframes our old "the region handle is a linear, non-`Send` capability" (RFC-0056) as an instance of a general, well-studied mechanism. It dissolves linearity's chief ergonomic complaint: you alias the *pointer* freely and thread only the *capability*.
- **Interpreter-first fit:** good. Pair with **linear constraints / qualified types** (Spiwack et al.; Jones) so the compiler threads the capabilities implicitly — dictionary-style — instead of by hand.

### 8. Control-as-you-need — CSC / Syntactic Control of Interference

A design *philosophy* as much as a calculus: permit aliases to mutable state by default, merely *track* them, and enforce separation only where data races are actually possible (e.g. the two sides of `||`), via separation degrees `sep{a} b`. This inverts the Rust model ("enforce a strong invariant globally, relax locally", which demands heavy refactoring to adopt).

- **Prior art:** Reynolds, *Syntactic Control of Interference*; Capture Separation Calculus; reachability types (Bao et al. 2021; Wei et al. 2024, λ◆); Scala capture types (CC<:□).
- **Identity:** this *is* "safety without Rust's annotation burden" stated as a principle — permissive default, constrain only at the points that matter. Directly answers open questions Q3 and Q6 below.
- **Interpreter-first fit:** adopt the *philosophy* now; treat the calculi as research to watch — soundness under polymorphism is 2021–2024-era and not yet a foundation to bet on.

### 9. Typestate — *protocol state in the type*

Encode a value's *state* in its type (`File<Closed>` → `File<Open>`); an operation typechecks only in the right state.

- **Prior art:** Strom & Yemini (1986); Plaid; Rust's phantom-type encodings.
- **Identity:** a cheap, high-value layer on the linear foundation we keep. Typestate's classic weakness — aliasing invalidating a state assumption — is fixed by linearity: a linear handle cannot be duplicated (no double-close) or dropped (no leak). We already own the linear half.
- **Interpreter-first fit:** good and low-risk; composes with linear types and with reference capabilities (an `iso` handle + typestate = a safe, alias-free state machine).

### 10. Object capabilities (ocap) — *a different axis: a possible identity feature*

Not a memory mechanism but a security one. References *are* unforgeable tokens that both name a resource and authorise access; there is no ambient authority (Principle of Least Authority). Deno's `--allow-net` / `--allow-read` is the mainstream example.

- **Prior art:** Lampson (1974); Miller (2006); E, Joe-E, Caja; Deno.
- **Identity:** a possible *differentiator* rather than a memory mechanism. For an interpreter-first, embeddable language (a strategic-report priority), language-level object-capability security gives safe sandboxed embedding nearly for free — the interpreter already mediates every reference. A niche Rust does not occupy.
- **Status:** hold as a candidate *identity* feature, evaluated separately from the memory-safety mechanism.

#### Fractional permissions — the unifying theory (mental model; do not build)

Marshall et al.'s graded uniqueness treats ownership as a fraction in (0, 1]: reading needs any positive fraction, writing needs the whole (p = 1), and many immutable borrows coexist exactly when their fractions sum to ≤ 1. This is the theory that *explains the whole space* — Rust's borrow checker is just a dynamic discipline keeping the sum of active references ≤ 1. Use it as the mental model for *why* reference capabilities and linear capabilities are sound; it is too annotation-heavy to ship.

### Comparison

| Mechanism | Family | Annotations | Safety check | Interpreter-first fit | Identity |
|---|---|---|---|---|---|
| Lifetimes / regions | A | optional (hard inference) | compile time | poor | derivative |
| Mutable value semantics (Hylo) | A | none | compile time | medium | novel |
| Generational refs (Vale) | A | none | runtime (cheap) | **excellent** | novel |
| Refcount + reuse (Perceus) | A | none | runtime + static reuse | good | novel-ish |
| Linear types (Austral) | A/B | declaration-site | compile time | good | already ours |
| **Reference capabilities (Pony)** | B | light, defaultable | compile time (top-down) | **excellent** | **novel, strong fit** |
| Linear / alias capabilities | B | implicit (constraints) | compile time | good | composes with ours |
| Control-as-you-need (CSC) | B | minimal (sep degrees) | compile time | medium (research) | philosophy |
| Typestate | B | state params | compile time | good | layer on linear |
| Object capabilities | — | none (topology) | runtime (mediated) | **excellent** | differentiator (security) |

---

## The interpreter-first argument

The sharpest insight from the reconsideration:

> **Interpreter-first probably wants a *runtime-assisted* safety mechanism, not a static one.**

The region/lifetime path was driving toward the most expensive possible artifact — a compile-time borrow-checker-lite — in a setting where it buys the least. An interpreter does not need static lifetimes to *run* safely; it can refcount or generation-check. So mechanisms (3) and (4) give real memory safety, need **zero annotations**, and **eliminate the static-inference-and-diagnostics risk** that made the region path both expensive and derivative.

The one caveat to research carefully: a runtime-check mechanism must **survive lowering to the future compiler** — the generation checks (Vale) or refcount ops (Perceus) have to be optimizable away in hot code, or they tax compiled performance. Both Vale and Koka have published work on exactly this elision; that work is the thing to evaluate.

---

## Candidate synthesis — capabilities over lifetimes

The Family-B mechanisms are not a menu; three of them, plus the linear types we already have, combine into a single coherent, non-derivative, interpreter-first direction:

> **Keep linear types (RFC-0028). Replace *lifetime annotations* with *reference capabilities* (top-down, modular — no inference risk). Default to *control-as-you-need* (alias freely; constrain only where data races are possible). Layer *typestate* on the linear foundation for protocols.**

Why this is the most promising candidate:

- **It keeps what we are confident about** (linearity) and **drops what made us derivative** (lifetimes).
- **It fixes the risk that sank the region path.** Reference capabilities are top-down and modular, so there is no whole-program lifetime inference and no need to explain inferred lifetimes the programmer never wrote — the §3.8 diagnosability problem disappears.
- **It unifies the concurrency story.** `iso`/`val` *are* the RFC-0003 `Send`/`Sync` transfer-and-sharing rules; the memory model and the concurrency model become one mechanism instead of two.
- **It bridges to the runtime-assist insight.** A capability can be a partly **runtime-checked token** — generational-reference style (Vale, Family A) — which is natural in an interpreter and elidable by the future compiler. Reference capabilities (static, top-down) and generational references (runtime, cheap) are two views of the same "who may touch this" question, and an interpreter-first language can blend them: check statically where it can, fall back to a cheap runtime token where it cannot.
- **Object capabilities ride alongside** as a separate identity bet for embeddable security, not part of the memory mechanism.

This is a *candidate*, not a decision. The next step is to prototype reference capabilities + linear capabilities on a toy and measure the two things that actually matter: annotation burden and error-message quality.

---

## Open questions to resolve before committing

1. **What is the safety guarantee we actually want?** Rank these — no use-after-free, no leaks, no aliasing-UB, deterministic cleanup. Different mechanisms deliver different subsets. (E.g. generational refs give no-UAF but not deterministic cleanup; regions give deterministic cleanup but needed lifetimes.)
2. **Compile-time prevention vs runtime detection?** Given interpreter-first *and* the future compiler, where on this axis do we sit — and does it differ between the two execution modes?
3. **Annotation budget.** Truly zero, or zero-by-default with an opt-in precision escape hatch? This is a product-feel decision as much as a technical one.
4. **Relationship to linearity (RFC-0028).** Does the chosen mechanism subsume linear types, complement them, or sit beside them? Linearity is the one piece we are confident about; the mechanism must compose with it.
5. **What survives lowering?** Whatever we pick must give the eventual compiler something to optimize. A runtime check that cannot be elided is a permanent tax.
6. **What is the *differentiated* story in one sentence?** If we cannot state what no incumbent offers, we have not found the mechanism yet.

---

## What to keep regardless of the outcome

- **RFC-0028 foundation** — linear types, `@T` owning pointer, `*T` raw pointer. Independently valuable, orthogonal to bulk allocation, and a survivor of every branch in this survey. Implementation of the foundation may proceed.
- **The region analysis** — `memory-model-programs.md` Part 7 and `regions-by-example.md` are a clean record of the evaluated "Rust-shaped" branch and *why* it is derivative. Retain them as rejected-branch documentation so the decision is not re-litigated later.

---

## Recommended next steps

1. **Read, in order:** Pony (reference capabilities) and Hylo (mutable value semantics) first — the two strongest "safety without lifetimes" designs — then Vale (generational references) and Koka/Perceus (refcount + reuse) for the runtime-assist angle. **Pony first:** it is the closest fit to Metel's modular, concurrency-aware needs.
2. **Prototype the candidate synthesis** (reference capabilities + linear capabilities + typestate over linear types) on a toy interpreter, and measure the two things that actually matter: annotation burden and error-message quality.
3. **Hold the region/lifetime RFCs** (0025, 0056, 0052, 0051). Proceed only with the RFC-0028 foundation.
4. **Revisit the strategic report's memory section** once a mechanism is chosen — the "explicit allocation control" thesis may be restated around the new mechanism, or replaced by it.

---

## References

- `bumpalo` — Rust bump-allocation crate (the incumbent for the region runtime model)
- Hylo / Val — `hylo-lang.org`; Racordon, Abrahams et al., "Implementation Strategies for Mutable Value Semantics" (JOT, 2022)
- Vale — `vale.dev`; Evan Ovadia, generational references, hybrid-generational memory, region borrow checking
- Koka / Perceus — Reinking, Xie, de Moor, Leijen, "Perceus: Garbage Free Reference Counting with Reuse" (PLDI 2021); functional-but-in-place (FBIP)
- Roc — `roc-lang.org`; opportunistic in-place mutation via reference counting
- Lobster — Wouter van Oortmerssen; compile-time reference counting / ownership analysis
- Austral — `austral-lang.org`; Fernando Borretti; linear types as the safety story
- Cyclone — Grossman, Morrisett et al.; regions + lifetimes in C
- ML Kit — Tofte & Talpin region inference (1994)

*Family B — capability & permission mechanisms (substructural survey):*

- Bruzzone, "A Friendly Tour of Substructural, Uniqueness, Ownership, and Capabilities Types" — the survey that opened this design space
- Pony — Clebsch et al.; reference capabilities (`iso`/`val`/`ref`/`box`/`trn`/`tag`); Haller & Odersky, capabilities for uniqueness and borrowing (2010)
- Alias types — Walker, Morrisett, Ahmed; focus/adoption — Fähndrich & DeLine
- Linear constraints — Spiwack et al. (2022); qualified types — Jones (1994)
- Control-as-you-need — Reynolds, *Syntactic Control of Interference*; Capture Separation Calculus; reachability types — Bao et al. (2021), Wei et al. (2024, λ◆); Scala capture types (CC<:□)
- Typestate — Strom & Yemini (1986); Plaid
- Object capabilities — Lampson (1974); Miller (2006); E, Joe-E, Caja; Deno permission model
- Fractional / graded uniqueness — Marshall et al.; Granule

- Strategic context — `docs/reports/strategic-vision-2026-06.md`
