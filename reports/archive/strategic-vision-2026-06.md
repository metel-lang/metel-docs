---
id: strategic-vision-2026-06
title: "Metel Strategic Vision"
type: report
created_date: '2026-06-07'
---

# Metel Strategic Vision

This report restates the language's strategic direction after the recent interpreter, module-system, and documentation work. It is not an RFC and does not define syntax. Its purpose is to answer a higher-level question:

**What should Metel become, and which technical bets justify continued investment?**

The answer in this document is opinionated:

- Metel should remain **interpreter-first**
- it should keep the **compiler** as a real long-term target, not a decorative aspiration
- its strongest differentiator is not "more features", but a coherent story around **explicit allocation control** and **optional resource discipline**

That story now looks stronger with allocator-style regions than it did in the original Moonlane framing.

---

## 1. Where the Project Stands

Metel is no longer a toy parser or a syntax experiment. The current interpreter has:

- a multi-stage pipeline with explicit stage boundaries
- a real module system with visibility, re-exports, and graph semantics
- a substantial language surface: ADTs, generics, aspects, methods, pointers, collections, and pattern matching
- a spec-first documentation process
- a meaningful integration test corpus

This matters strategically. It means the project has crossed an important line:

**the core risk is no longer "can this be implemented at all?"**

The current risk is different:

**can the language maintain a sharp identity while it continues to grow?**

---

## 2. The Core Strategic Problem

The older Moonlane vision had a sharper thesis than the current implementation narrative:

- Rust-influenced syntax
- first-class interpreter
- first-class compiler
- static typing in both modes
- opt-in resource control rather than mandatory ownership

That was a strong position because it was not just "a typed interpreted language." It was a claim about a specific missing space in the design landscape.

Metel today has made real progress on the interpreter-language axis, but the project has partially drifted toward breadth:

- more public language features
- more standard surface
- stronger module semantics
- stronger runtime and testing discipline

All of that is good. None of it is the differentiator by itself.

If Metel continues expanding feature-by-feature without a renewed thesis, it risks becoming:

- technically respectable
- pleasant to work on
- but strategically ordinary

That is not where the project is strongest.

---

## 3. Recommended Thesis

The best current thesis is:

**Metel should be an interpreter-first statically typed language whose long-term compiler story is justified by explicit allocation control and optional resource discipline.**

This is more specific and more defensible than:

- "Rust but interpreted"
- "a simpler Rust"
- "a scripting language with types"
- "a small systems language"

The thesis has four parts.

### 3.1 Interpreter-first

The interpreter is the present product surface, not scaffolding for a future compiler. It must stay:

- embeddable
- fast enough for iteration and scripting
- spec-faithful
- well-documented

This remains a genuine strength. The project already has the right architecture for it.

### 3.2 Compiler as a serious target

The compiler should remain a real direction, but not as a generic "make it faster" promise. The compiler becomes strategically justified when it can exploit properties that the interpreter also understands semantically.

That means the compiler story should be built around:

- explicit allocation placement
- region-based memory organization
- optional linear/resource-sensitive guarantees

Not around "native code because native code is desirable in general."

### 3.3 Explicit allocation control

This is the strongest practical design direction currently on the table.

The allocator-style region idea from RFC-0056 upgrades regions from a local implementation trick into a real language model:

- `region { ... }` for the ergonomic common case
- explicit `Region<'r>` handles for API boundaries
- caller-chosen allocation destinations
- room for multiple region strategies (`BumpRegion`, `FixedRegion<N>`, `DebugRegion`, later others)

This is where the Zig influence is constructive. Zig's allocator discipline demonstrates that "the caller chooses where allocation happens" is not theoretical purity; it is a scalable programming model.

### 3.4 Optional resource discipline

Linear types and related resource rules should remain part of the identity, but they should no longer be treated as the only interesting memory-management story.

The stronger framing is:

- **regions** solve explicit allocation control
- **resource/linearity rules** solve stronger usage and lifetime discipline where needed

That is better than trying to make every memory-management idea orbit linearity alone.

---

## 4. Why Allocator-Style Regions Matter

The explicit-region direction is not a side feature. It may be the practical center of Metel's long-term identity.

### 4.1 They solve the real API-boundary problem

Plain `region { ... }` blocks are ergonomic, but they only scale naturally when allocating code is textually local. The moment allocation work moves into a callee, the question becomes:

**where does the returned data live?**

Explicit region handles answer that cleanly.

### 4.2 They create a usable discipline

The rule:

**the caller decides where allocation goes**

is simple, legible, and library-friendly. It makes memory placement part of the function contract without requiring pervasive borrow-checker machinery.

### 4.3 They fit the interpreter-first model

This is important. Many systems-language ideas make sense only in a compiler. Explicit regions do not.

In the interpreter, regions still give:

- explicit lifetime and allocation structure
- deterministic bulk cleanup semantics
- debug-oriented region implementations
- API-level memory visibility

In the compiler, they additionally create room for:

- stack-backed fixed regions
- lower allocation overhead
- more predictable memory behavior
- better code generation around region-local values

This is exactly the kind of feature that justifies "first-class both."

### 4.4 They combine well with comptime

RFC-0055 and RFC-0056 reinforce each other:

- `FixedRegion<N>` becomes plausible with comptime-known sizes
- region strategy can become partially compile-time selected
- fixed-size arrays and explicit regions begin to form a more coherent systems-adjacent design space

That is a better strategic arc than treating comptime and memory management as separate tracks.

---

## 5. Recommended Memory Story

Metel should aim for a staged, layered memory model rather than a single all-or-nothing mechanism.

### Layer 1 — Default values

Ordinary values use the default runtime memory model. This keeps the language approachable and keeps the interpreter practical.

### Layer 2 — Implicit scoped regions

`region { ... }` remains the ergonomic form for localized allocation.

### Layer 3 — Explicit region handles

`Region<'r>` becomes the library/API form of the same idea:

- allocate into the caller's region
- make allocation destination visible at the boundary
- allow region strategy to be chosen explicitly

### Layer 4 — Optional resource discipline

Linear/resource-sensitive features apply where stronger guarantees are needed:

- one-owner resources
- no accidental duplication
- consumption-aware APIs
- future concurrency/resource interactions

This is the ordering that keeps the model teachable:

1. values
2. regions
3. explicit region handles
4. stronger resource rules

Not:

1. ownership/linearity everywhere
2. regions as an afterthought

---

## 6. What This Means for the Compiler

The compiler should not be pursued as an independent goal. It should be pursued when the language has something specific for the compiler to exploit.

The right justification is:

- the interpreter defines the semantics
- the spec defines the contract
- the compiler reuses the same front-end semantics
- explicit allocation control and resource-sensitive features give the compiler meaningful optimization and representation wins

Without that, the compiler risks becoming:

- expensive to build
- hard to validate
- strategically vague

With that, it becomes a natural second execution mode rather than an unrelated second project.

---

## 7. What Not To Do

Several tempting directions would weaken the project if pursued too early or too broadly.

### 7.1 Do not optimize for feature count

Metel already has enough surface area to demonstrate seriousness. More features are only valuable if they sharpen the thesis or unblock real programs.

### 7.2 Do not treat all memory ideas as equivalent

RC defaults, regions, linear types, pointers, and comptime are not a grab-bag. They need one unified narrative. If they are developed independently, the language will feel conceptually fragmented.

### 7.3 Do not turn explicit regions into hidden borrow checking

The appeal of the RFC-0056 direction is precisely that it does not require the full Rust model. If the design accumulates enough invisible lifetime coupling that users must think in borrow-checker terms anyway, the language will pay the complexity cost without getting Rust's clarity.

### 7.4 Do not let the compiler dictate present design prematurely

The interpreter is the current product. The language should not accumulate compiler-motivated complexity before the memory and execution model actually justify it.

---

## 8. Recommended 6-12 Month Direction

The next phase should prioritize coherence over breadth.

### Priority 1 — Resolve the memory model narrative

Produce one coherent internal document that explains the relationship between:

- default runtime-managed values
- region-local allocation
- explicit `Region<'r>` handles
- pointers into region-backed values
- optional linear/resource-sensitive values

Right now this is the most important conceptual task.

### Priority 2 — Advance explicit regions as a first-class design area

RFC-0056 should be treated as strategically important, not a peripheral extension. The key design work is:

- handle syntax
- API conventions
- region implementation model
- interaction with lifetimes and pointers
- interaction with error handling and OOM policy

### Priority 3 — Keep the interpreter and spec disciplined

The interpreter remains the place where the language proves it can be coherent. Continue investing in:

- stage boundaries
- tests
- spec precision
- doc quality

This is not maintenance-only work. It is what makes the long-term compiler and research story credible.

### Priority 4 — Narrow compiler work to exploratory architecture

Do compiler work only insofar as it clarifies future boundaries:

- IR shape
- ownership/allocation representation
- what semantic information must survive lowering

Do not broaden into "general code generation progress" unless the memory model is sufficiently settled.

### Priority 5 — Recast the research story around the new center

The old Moonlane research framing emphasized linearity heavily. That still matters, but the academically interesting space may now be better described as:

- explicit allocation control without mandatory ownership
- region/resource interaction
- interpreter-first semantics with a future optimizing backend

That is a stronger and more practically grounded research platform.

---

## 9. Strategic Conclusion

Metel is in a better technical state than many language projects ever reach. The immediate challenge is not implementation competence but strategic focus.

The best direction is not to become a generic typed interpreted language with an ever-growing feature list.

The best direction is to become:

**an interpreter-first language with a strong, explicit memory story built around caller-controlled allocation and optional resource discipline.**

Allocator-style regions are the most promising extension of the original Moonlane idea because they do three things at once:

- they make the resource model practically useful
- they justify the future compiler in concrete terms
- they fit the interpreter-first philosophy rather than fighting it

If Metel adopts that as the center of gravity, the project has a clear technical and strategic arc:

- interpreter as the executable semantics
- spec as the contract
- regions as explicit allocation control
- optional resource rules as stronger discipline
- compiler as the backend that turns those semantics into concrete performance wins

That is a language worth continuing to build.

