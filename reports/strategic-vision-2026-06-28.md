---
id: strategic-vision-2026-06-28
title: "Metel Strategic Vision — Allocators as Lifetimes"
type: report
created_date: '2026-06-28'
supersedes: strategic-vision-2026-06
---

# Metel Strategic Vision — Allocators as Lifetimes

This report supersedes the June 2026 strategic vision. That document asked whether Metel should commit to explicit allocation control as its strategic center. The region RFC cluster (RFC-0063 through RFC-0071, now accepted) answers that question. This document restates the language's identity in light of that answer and sets direction for the next phase.

---

## 1. The Identity

Metel's defining design decision is:

**Every lifetime annotation is the name of a real allocator object visible in scope.**

This is not a implementation detail. It is the load-bearing principle that distinguishes Metel from every other statically typed language currently in use.

In Rust, lifetimes (`'a`, `'b`) are annotations on code regions — a fiction maintained by the borrow checker with no runtime counterpart. Allocators (the `Allocator` trait) are separate runtime objects. The two systems are orthogonal and must be manually kept consistent.

In Zig, allocators are explicit, first-class runtime values. There is no static lifetime system. The programmer passes allocators through the call chain and the compiler does not verify that allocation and deallocation are paired correctly.

In GC-managed languages, both concerns disappear from the programmer's view entirely — at the cost of control, predictability, and the ability to reason about memory placement.

Metel occupies a position none of these hold: **the allocator object and the lifetime tag are the same thing.** When a programmer writes:

```metel
let r = AutoRegion::new();
let node = @[r] Node { val: 1 };
```

`r` is simultaneously:

- a runtime allocator handle — a value that knows how to allocate and free;
- the compile-time lifetime tag for everything allocated into it;
- the name that appears in borrow-checker error messages.

There are no phantom lifetimes. There are no abstract `'a` parameters that reference nothing in the programmer's source. If a lifetime matters, there is a real object to point at.

This unification — **allocators as lifetimes** — is Metel's identity.

---

## 2. What the RFC Cluster Established

The region RFC cluster translated this identity into a complete, accepted design. The key results:

**The bracket channel** (`[r]`) is the uniform syntactic position for allocator/lifetime parameters — in function signatures, struct declarations, and allocation expressions. The same name serves as runtime handle and compile-time tag simultaneously.

**The region interface is open.** `BumpRegion` (bump arena), `AutoRegion` (default scoped arena), `Heap`, and `LocalHeap` are stdlib defaults, not an exhaustive set. Pool allocators, slab allocators, stack arenas, and any custom type implementing the region interface plug into the same bracket channel position and receive the same static guarantees.

**Affine ownership** (RFC-0071) grounds the entire system. Region pointers are non-`Copy` by construction — exactly one live owner at all times. This is what makes allocation lifetime tracking sound and what allows the interpreter and compiler to share identical semantics.

**Struct-owned regions** (RFC-0068) and **sub-region typing** (RFC-0069) extend the model to objects: a struct can own its arena, whose lifetime is then the struct's lifetime. Nesting composes automatically through `SubRegion<R>` and `Outlives` transitivity — no annotation required at the allocation site.

**The interpreter model** is identical to the compiled model. Both run the same type system and the same borrow checker. The difference is allocator implementation only: the interpreter uses a single uniform allocator regardless of region type. Affine ownership makes this safe — because there is always exactly one owner, deterministic drop in the interpreter produces the same observable behavior as region-specific allocators in the compiler.

---

## 3. Why This Is a Genuine Innovation

The design space around memory management is crowded, but "allocators as lifetimes" occupies a genuinely unoccupied position.

| | Static lifetime checking | Explicit allocator objects | Same object for both |
|---|---|---|---|
| Rust | yes | yes (Allocator trait) | no |
| Zig | no | yes | — |
| GC languages | no | no | — |
| Metel | yes | yes | **yes** |

The consequences of that last column:

**Lifetime errors are anchored.** When the borrow checker rejects a program, it names a variable — the same variable the programmer wrote when they allocated. Not `'a cannot outlive 'b` between two abstract parameters, but `node escapes region r` pointing at the actual `let r = AutoRegion::new()`.

**Disjointness is structural.** Two pointers with distinct region tags name distinct allocators and therefore cannot alias. This is a compile-time fact, not a runtime check, not a proof obligation. It falls out of the type system for free.

**Custom allocators are first-class without ceremony.** A pool allocator or a stack arena does not require a separate lifetime annotation system — it plugs into `[r]` and the existing rules apply.

**The interpreter gets lifetime checking.** Because lifetimes are real objects, the semantic model is equally valid in an interpreted and compiled execution context. Metel is not making a "we'll add the borrow checker later" promise; the borrow checker runs now, in the interpreter, on the same programs.

---

## 4. What This Enables

### 4.1 A teachable memory model

Rust's lifetime system is notoriously difficult to teach because abstract lifetime parameters have no concrete referent. Metel's model has a concrete referent for every lifetime: the allocator object. Students can point at it. Debuggers can name it. Errors can link to it.

This does not make the model trivial — `Outlives`, `SubRegion<R>`, and `T: !Drop` are still non-trivial concepts. But they are grounded in objects rather than in abstract code regions.

### 4.2 Caller-controlled allocation

The rule "the caller decides where allocation goes" is simple, legible, and library-friendly. A function that accepts a region handle `[r]` and returns `@[r] T` makes its allocation contract visible at the API boundary. The caller may provide a bump arena, a heap allocation, a pool — the function does not care.

This is the Zig allocator discipline with static lifetime verification added.

### 4.3 A concrete compiler story

The June 2026 vision argued that "the compiler becomes strategically justified when it can exploit properties that the interpreter also understands semantically." That condition is now met.

The compiler can exploit explicit allocation structure in ways that are invisible in languages with implicit or GC-managed memory:

- arena-allocated values have stack-like allocation cost;
- disjoint regions enable parallel ownership without separation logic;
- `SubRegion<R>` nesting lets the compiler reason about memory hierarchy;
- `T: !Drop` enables bulk deallocation without per-element traversal.

None of these require the programmer to annotate anything beyond what the type system already requires for correctness.

### 4.4 A parallelism story

RFC-0064 (Structured Fork-Join Parallelism, currently deferred) is the direct downstream application of region disjointness. Two branches of a parallel combinator that hold pointers into distinct regions cannot race — the borrow checker's ordinary `&mut` exclusivity rule is sufficient. No separation calculus. No atomics. No proof obligations beyond what single-threaded programs already require.

The RFC was deferred pending stabilisation of the core region model. That stabilisation is now done.

---

## 5. What Remains Open

Accepting the region cluster closes the design phase for the core model. Several concrete gaps remain.

### 5.1 Error handling and OOM — in progress

The `Region` aspect now carries a `type AllocationError` associated type. Infallible regions (all three stdlib regions — `Region`, `Heap`, `LocalHeap`) assign `!`, so OOM panics and `@[r] expr` retains its existing `@[r] T` type at those sites. Fallible custom allocators assign a concrete error type; `@[r] expr` returns `Result<@[r] T, E>` and callers propagate with `?`. The design is specified in RFC-0063 §1.1 and §2.

### 5.2 Negative bounds — in progress

RFC-0072 (under review) specifies `T: !Aspect` as a bound satisfied by the absence of a positive impl. `T: !Drop` is automatically satisfied for types with no `Drop` implementation; `T: Copy` implies `T: !Drop` by the mutual exclusion rule. Negative bounds require no opt-out declaration at the type definition site.

### 5.3 Fork-join parallelism (RFC-0064)

The core blocking question — whether the region model can provide a sound foundation for data parallelism — is now answered affirmatively. RFC-0064 can be resumed.

### 5.4 Interpreter implementation

The region system is fully designed but not yet implemented in the interpreter. The interpreter currently uses a single uniform allocator (which is the correct semantics for the interpreter model), but the borrow checker enforcing region constraints is not yet running. This is the most important implementation gap.

### 5.5 Pattern syntax RFC

Partial-move behavior in patterns (§7 of RFC-0071) is resolved in policy but the full pattern syntax — including `ref` binding in destructuring patterns — is deferred to a pattern syntax RFC.

### 5.6 Derived aspects (RFC-0012)

`Copy` currently requires `impl Copy for T {}`. A derive-like shorthand is deferred pending the design of the derived aspects system. RFC-0012 is marked as existing but has not been designed.

---

## 6. Strategic Direction — Next Phase

### Priority 1 — Implement region lifetime checking in the interpreter

The design is complete. The most valuable next move is making it real: implement the borrow checker rules for region constraints in the interpreter. This turns the accepted RFCs into running code and validates the design against real programs.

The interpreter model is simple: a single uniform allocator handles all regions; the borrow checker enforces that region-tagged values do not escape their allocator's scope. No special allocator machinery is needed in the interpreter itself.

### Priority 2 — Finalise error handling and OOM (in progress)

The `AllocationError` associated type design is specified in RFC-0063. What remains is validating the design against real use cases — particularly how fallible allocators interact with error propagation at call sites — and accepting the extension.

### Priority 3 — Accept negative bounds RFC (in progress)

RFC-0072 is under review. It is a small, self-contained RFC with no open questions. Acceptance unblocks the interpreter's `T: !Drop` checking.

### Priority 4 — Resume RFC-0064 (Fork-Join Parallelism)

The region model is stable enough to ground the parallelism design. RFC-0064 should be resumed with the accepted region cluster as its foundation.

### Priority 5 — Compiler architecture (exploratory)

The compiler is not the current product but it is a real direction. Now that the region model is settled, the right compiler work is exploratory architecture: what does the IR look like, how does region information survive lowering, and what does ownership representation look like at the machine level. This informs future design without committing to a full implementation.

---

## 7. What Not To Do

### Do not diffuse the identity

"Allocators as lifetimes" is specific. Every major language decision should be evaluable against it: does this shorten the identity, clarify it, or contradict it? Features that expand the language without touching the core model should be deferred until the core is implemented and tested.

### Do not add a separate lifetime system

Having established that allocator objects are lifetime tags, Metel should not separately introduce abstract lifetime parameters (`'a`-style) even for convenience. That would reintroduce exactly the Rust complexity the identity avoids. If a lifetime needs naming, there should be a real allocator object behind it.

### Do not mistake design for implementation

The region cluster is accepted, not implemented. Strategic direction should continue to prioritize making the design real over extending it further. New RFCs should be held to a higher standard of necessity until the interpreter implements what is already specified.

---

## 8. Conclusion

The June 2026 strategic vision asked whether Metel should commit to explicit allocation control. The region RFC cluster made that commitment concrete. Metel now has a specific, defensible identity:

**a statically typed language where allocator objects and lifetime tags are the same thing.**

This is not a derivative of Rust's model or Zig's model. It is a distinct design point with genuine consequences: grounded error messages, structural disjointness, a sound interpreter model, and a compiler story built on properties the type system already verifies for correctness.

The design work is largely done. The task now is to make it run.
