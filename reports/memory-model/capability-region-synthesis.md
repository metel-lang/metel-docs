# Reference Capabilities + Arena Handles: A Merged Memory Model

*Design synthesis — June 2026*

This report merges the two June-2026 explorations — **reference capabilities / separation
types** (`substructural-and-separation-types.md`) and **arena handles as lifetime
annotations** (`arena-handles-as-lifetime-annotations.md`) — into one coherent proposal,
refines the capability set down to a minimal core, and assesses the result against the
concerns that paused the earlier region/lifetime branch
(`memory-strategy-research-directions.md`, `regions-by-example.md`).

The two reports were written as separate surveys. They are not independent: the arena
report is built *on top of* the capability vocabulary the substructural report
introduces. Merging them is mostly a matter of stating the single system they jointly
describe and resolving the one apparent contradiction between them.

> **Vocabulary note.** This report writes the unique-owner capability as `*own` (the
> substructural and arena reports call it `*iso`). The two names denote the same
> capability — unique, mutable, sendable — and `*own` is preferred here because it reads
> as "the owning pointer" and avoids confusion with the `iso T` *value* qualifier.

---

## 1. The contradiction to resolve first

The substructural report opens with:

> *Linear arenas as the primary memory-management mechanism have been set aside.*

The arena report puts arenas back at the centre. These are reconciled by a change of
*role*, not a reversal:

- **Old (paused) role:** the region/`bumpalo` arena was *the* memory mechanism, and a
  Rust-style lifetime `'r` — inferred whole-program — was the safety device. Memory
  safety *was* lifetime inference.
- **New role:** the **reference capability** is the safety device. The arena is one
  *allocation strategy* among several, and its handle is reused as a **lifetime tag on a
  capability**, not as a free-standing inferred lifetime variable.

So arenas are not "primary" in the merged system — capabilities are. The arena handle is
demoted from "the mechanism" to "a tag that one of the capabilities can carry." That is
the reconciliation, and it is what makes the merge coherent rather than a return to the
paused branch.

---

## 2. The layered system

The merged model is six layers, least to most invasive, each from one of the two reports:

| Layer | Mechanism | Source | Guarantee |
|---|---|---|---|
| 0 | Affine structs (move semantics, `Copy` opt-in) | substructural §2 | no silent duplication |
| 1 | Reference capabilities `*own *mut *` (+ `Arc`/`Weak`, `Sync` marker — see §4) | substructural §3,5 + arena §6 | who may read / write / send |
| 2 | Arena-handle region tags `[r]` on `*own` (and `Arc`) | arena §1–4 | scope / lifetime, named after a real object |
| 3 | Linear capability tokens (`linear struct`) + typestate | substructural §4,6 | must-consume protocols |
| 4 | Structured fork-join (`\|\|`, `fork{}`) over disjoint state | substructural §7,8, refined §6 | data-race-free parallelism without ownership transfer |
| 5 | Stdlib (`Box`/`Arc`/`Rc`/`Weak`, interior-mutability cells, `Heap`/`LocalHeap`, `Arena` aspect) | arena §7,10,11 | ergonomic surface; allocator polymorphism |

The whole point of the merge is that **layers 1, 2 and 4 share one carrier**. A single
annotation does triple duty:

- **the capability** (`*own`, `*mut`, …) says *who may touch it and whether it sends* —
  layer 1;
- **the region tag** (`[r]`) says *how long it lives*, named after a visible arena
  handle — layer 2;
- **the region tag, again**, gives structured parallelism a *static disjointness proof* —
  two values with different tags provably cannot alias, so fork-join over them is race-free
  by construction — layer 4.

```metel
let a: *own[r1] Counter = r1.alloc(Counter { value: 0 });
let b: *own[r2] Counter = r2.alloc(Counter { value: 0 });
a.inc() || b.inc();   // [r1] ∩ [r2] = ∅ statically → parallel for free
```

That dual use of the region tag — *lifetime bound* and *disjointness witness* in one
symbol — is the load-bearing novelty of the merge and exists in neither report alone.
Section 6 revisits *how much machinery* the parallelism layer needs to cash this in: in the
reduced system the tag **is** the proof, and the CSC capture-set calculus the two reports
proposed around it is no longer required.

---

## 3. The two orthogonal axes

Capability and region are independent axes. The capability decides mutability and
sendability; the region decides lifetime and (for sendables) whether sending is even
permitted. The two reports propose **five** capabilities; laid against the region axis
they are:

| | no tag | `[r]` (scoped) | `[Heap]` (static) |
|---|---|---|---|
| `*own T` (unique, mutable) | sendable | scope-bound, **not** sendable | sendable |
| `*val T` (immutable) | sendable, global | scope-bound, not sendable | sendable |
| `*mut T` (mutable borrow) | local | local (tag redundant) | local |
| `*T` (read borrow) | local | local (tag redundant) | local |
| `*tag T` (identity only) | sendable | scope-bound | sendable → `Weak` |

The tag is *meaningful only on the sendable capabilities*: it is the mechanism that
**removes** sendability by binding the value to a non-static scope. On the borrow
capabilities it is redundant (they are already non-sendable and non-escaping).

Section 4 argues that two of these five rows — `*val` and `*tag` — are not primitive and
should be library types. The remaining three (`*own`, `*mut`, `*`) are the irreducible
core.

---

## 4. Minimizing the capability set

Every capability is a point in three independent axes — **mutability** (write / read /
none), **aliasing** (unique / shared / exclusive-borrow), and **sendability** (sendable /
local). Read the §3 table that way and a pattern appears: `*val` and `*tag` are the only
two cells that combine **shared aliasing with sendability**, which is exactly the job
description of a reference-counted smart pointer.

### 4.1 The irreducible three

`*own`, `*mut`, and `*` are the standard own / `&mut` / `&` trio and are mutually
irreducible:

- `*own` — the unique heap owner; the only capability that makes recursive types and
  cross-fiber *move* work. Not derivable from a borrow.
- `*mut` — exclusive mutable borrow; the writer side of borrow checking and of fork-join
  disjointness.
- `*` — shared read borrow; the reader side. Many can coexist (the fractional `p ∈ (0,1)`).

You cannot build `*mut` from `*` (writer vs reader is the whole point of the discipline)
nor `*own` from `*mut` (owning indirection vs a loan). Keep all three.

### 4.2 `*val` → `Arc<T>`

`*val` is deeply-immutable, freely-aliased, sendable. Its concrete jobs — backing
`Arc<T>`, being the result of `freeze`, and direct cross-fiber immutable sharing — are all
`Arc<T>`'s job description. And `Arc` can be *implemented* without `*val` as a primitive:

- **aliasing / reclamation** is handled by `Arc`'s own refcount ("N co-owners, freed at
  zero"); no single capability describes that — it is what the library type is *for*. The
  inner pointer is a frozen `*own` to the `ArcInner` cell, managed by the refcount;
- **immutability** is enforced by `Arc` handing out only `*T`, never `*mut T`;
- **sendability** is a `Sync`/`Send` *marker* on `Arc`.

A sharper point: a bare, tag-free `*val` has **no reclamation story** — "freely copyable,
sendable, not tied to any arena" leaks unless it is region-bounded or refcounted, and
adding the refcount *is* rebuilding `Arc`. So `*val` as a primitive is underspecified, and
the fix collapses it into `Arc`. `freeze` becomes the honest "unique → refcounted shared"
conversion (`Arc::from_own`) with an explicit free point.

### 4.3 `*tag` → `Weak<T>`

`*tag` is even more clearly redundant: its *only* consumer in either report is `Weak<T>`,
and `Weak<T>` enforces "identity only, no deref" through its **method surface** (no
`Deref`; you must `upgrade()` first), not through a pointer capability. Its sendability is
again a marker. The other classic `tag` use — identity comparison — is already covered by
plain `*` (RFC-0043 D10: pointer-identity equality). With only `Weak` as a consumer, it is
a library type, not a primitive.

### 4.4 The decision underneath: Pony-style vs Rust-style

This is really a choice the two reports left straddled:

- **Pony-style** — *everything* is a capability, because Pony has no `unsafe` and no
  markers; every guarantee must be a cap. That justifies a 6-cap lattice.
- **Rust-style** — a minimal cap core plus *library* smart pointers whose sendability
  rides on `Send`/`Sync` markers.

The reports borrow Pony's *vocabulary* (`iso`/`val`/`tag`) but Rust's *stdlib* (arena §7:
"Box/Arc/Rc are ordinary stdlib structs… no compiler magic"). Those cannot both hold: if
`Arc`/`Box` are plain library structs, then `*val`/`*tag` — which exist only to back
`Arc`/`Weak` — belong library-side too. Metel already has the ingredients to pick
Rust-style: affine structs, `linear`, `Send`/`Sync` markers.

### 4.5 The reduced system

```
primitives:  *own   unique owner, sendable
             *mut   exclusive borrow
             *      shared borrow
library:     Arc<T>   = frozen *own + refcount + Sync marker   (replaces *val)
             Weak<T>  = same cell, identity-only API + marker  (replaces *tag)
marker:      Immutable / Sync   (recovers deep-immutability as a checkable fact)
```

Net effect: the cap×region matrix shrinks from five rows to three, `freeze` gains an
explicit reclamation story, and the vocabulary stops being half-Pony/half-Rust. The one
genuine casualty is *unsafe-free* immutable sharing — the same price Rust pays — recovered
in the no-UB sense by §5. If a hard goal is "zero trusted code in stdlib, all sharing
compiler-proven," `*val` earns its place back and the design should own the Pony-style
position fully; otherwise the three-primitive core is the cleaner choice.

---

## 5. Safe shared mutability without `unsafe`

`unsafe` (RFC-0026) is not yet implemented and its RFC is pending. A fair question for the
reduced system is whether **shared mutability** — many live aliases that all write — is
still expressible safely without it. It is, but not by composing the three primitives:
they enforce **aliasing XOR mutability** by construction, and there is no operation that
produces a write from a `*` (shared) reference. Shared mutability must therefore be a type
that re-establishes safety by a *runtime* check rather than static exclusivity — which is
true of any such system, Rust included (`RefCell`/`Mutex` exist precisely because the
static rules forbid what they provide).

### 5.1 "No `unsafe`" relocates the trust boundary; it does not block it

In Rust the trusted root is `UnsafeCell`, and `RefCell`/`Mutex` are built on it in library
code using `unsafe`. Without an `unsafe` keyword, Metel instead provides
`Cell`/`RefCell`/`Mutex`/`RwLock` as **sealed runtime intrinsics** — types implemented by
the runtime, exactly as `Arc`'s refcount, the arena allocator, and channels already are.
The trust boundary becomes *"this type is provided by the implementation,"* not *"this
block is unsafe"* — and no user-facing unsafe primitive needs to exist at all.

This is more natural for Metel than for Rust because the interpreter's values are already
`Rc<RefCell<Value>>` (substructural §2). Shared mutability is the runtime's *native*
representation; the static capabilities are a discipline layered on top that *restricts*
it, and an interior-mutability type is the controlled opt-out back to the check the
interpreter already performs.

### 5.2 Mechanism: runtime exclusivity + a linear guard

The guard returned by a borrow/lock is a **linear/affine token** — reusing layer 3, not
new machinery:

```metel
// single fiber: runtime borrow flag
let cell = Rc::new(RefCell::new(Counter { value: 0 }));
let a = cell.clone();
let b = cell.clone();                   // two shared owners — both can mutate
{
    let g: *mut Counter = a.borrow_mut();  // g is a linear guard; flag set
    g.value += 1;
}                                        // g dropped → flag cleared
b.borrow_mut().value += 1;               // OK: previous borrow released

// cross fiber: runtime lock
let shared = Arc::new(Mutex::new(Counter { value: 0 }));   // Arc<Mutex<T>>: Send
spawn { shared.lock().value += 1 };      // lock() -> linear Guard derefs to *mut T
```

Each piece maps onto the reduced system: `Arc` gives shared *ownership* (frozen `*own` +
refcount + `Sync`); `Mutex`/`RefCell` gives interior *mutability* via a runtime
exclusivity check that proves, dynamically, the precondition for handing out the existing
`*mut` primitive; the guard is the linear token that releases the flag/lock on drop.
`Arc<Mutex<T>>` is the cross-fiber shared-mutable, `Rc<RefCell<T>>` the single-fiber one —
both within **3 primitives + library types + marker**, no fourth capability and no user
`unsafe`.

### 5.3 The tradeoff, and what it costs

The interior-mutability types trade a *static* guarantee for a *runtime* one: a violation
**traps deterministically** (`RefCell` double-borrow panics; `Mutex` serializes) instead
of causing UB. It is still memory-safe. That runtime check is precisely the
"runtime-assist" mechanism the research-directions report argued an interpreter-first
language should prefer, and it survives lowering (Concern 5): a future compiler keeps the
borrow-flag / lock where it cannot prove exclusivity statically and elides it where it can.

The one real constraint: interior mutability cannot be written in safe user Metel (you
cannot produce a write from `*`), so these types **must** be runtime intrinsics — a fixed,
sealed stdlib set. That is sufficient for the standard `Cell`/`RefCell`/`Mutex`/`RwLock`
family. Only letting *users build their own novel* interior-mutability primitives is
deferred to a future `unsafe`; it is not on the critical path for safe shared mutability.

---

## 6. Reconsidering the separation layer: fork-join, not a calculus

Layer 4 was imported from the substructural report as the full **Capture Separation
Calculus** — capture sets tracked in the inference context, a `||` operator whose safety is
*checked* by capture-set disjointness, and `sep{}` parameter annotations to carry that proof
across call boundaries. Once the rest of the merged system is fixed — regions as lifetimes,
`Heap`/`LocalHeap`, and the `Arc`/`RefCell`/`Mutex`/`RwLock` stdlib of §4–5 — most of that
machinery turns out to be redundant. This section pares it back to what the reduced system
actually needs.

### 6.1 The calculus did two jobs; only one survives

The CSC `||` conflated **scheduling** ("fork these two, join them") with **safety** ("this
is the point where I verify the two sides don't race"). In the reduced system the safety job
is already discharged elsewhere:

- two distinct region tags ⇒ provably disjoint memory (`[r1] ∩ [r2] = ∅`, §2);
- `*mut` is an *exclusive* borrow ⇒ you cannot even form two writers to the same place;
- `split_at_mut` (a sealed intrinsic, like `RefCell` in §5) ⇒ vends two non-aliasing borrows
  into one allocation;
- disjoint-place borrows (`&mut s.a`, `&mut s.b`) ⇒ disjoint struct fields;
- `Mutex`/`RefCell` ⇒ the runtime-checked shared-mutable escape hatch.

Every disjointness the capture-set pass was meant to prove is already producible by one of
these. So the `capture_env` side-channel, the `Separated` parameter kind, and the call-site
separation proofs are **not needed**: two parallel branches are safe iff each branch
independently type-checks against the *ordinary* rules — exactly the way Rust's
`rayon::join` rides on the borrow checker with no bespoke machinery. The calculus collapses;
the operator remains.

### 6.2 What the operator is *for*: parallelism over non-sendable region borrows

If safety no longer needs `||`, why keep it at all — why not just `spawn`? Because of a
property the region model forces (§8): a `spawn`'d fiber may capture only **sendable** values
(`*own T`, `Arc<T>`, `Copy`, channel endpoints), and region-bound values are non-sendable
**by construction** (`*own[arena] T` is rejected at send). A fiber may outlive the region, so
it can never hold a borrow into one.

That makes region-allocated data single-threaded under `spawn` alone: to parallelise over it
you would first have to copy it to the `Heap` or wrap it in `Arc` — defeating the arena.
**Structured fork-join is the one construct that escapes this**, precisely because it is
structured: `||` guarantees both sides complete before the expression returns, *inside* the
region's scope, so handing each side an `*[r]`/`*mut[r]` borrow is sound — the borrow cannot
escape the join, hence cannot outlive the region.

```metel
Arena::scoped(fun(a: &mut Arena) {
    let t = build(a, ...);                 // *own[a] Node — non-sendable; spawn cannot take it
    let (ls, rs) = sum(&t.left) || sum(&t.right);   // borrows into a, in parallel — sound
});                                        // both halves provably finished before a drops
```

So the operator's justification is no longer "it checks separation" but "**it is the only
parallelism primitive compatible with the region layer's non-sendable borrows**." Nothing
else in the system provides this; without it, arenas and parallelism can never be used
together.

### 6.3 Use cases, and the division of labour with fibers

Fork-join owns *structured, CPU-bound* parallelism; fibers + channels own *unstructured,
communicating* concurrency. The split is clean:

| Want | Tool |
|---|---|
| divide-and-conquer (parallel sort / reduce / tree fold) | `||`, binary, recursive |
| "need both of these independent results now" (parallel `let`) | `||` or `fork{}` |
| map-reduce over a collection (runtime arity, homogeneous) | `par_iter` / `chunks_mut().par_map(..)` |
| long-lived tasks, IO overlap, mid-flight communication | `spawn` + `Chan<T>` |

Divide-and-conquer is intrinsically *binary-recursive*, which is exactly what a binary `||`
expresses: the recursion builds the fork tree and a work-stealing scheduler balances it.
Data-parallelism over a collection is `par_iter` regardless of the operator's arity.

### 6.4 Shape: a library combinator with `||` as sugar — and the n-ary question

Because safety is external (§6.1), fork-join need not be a primitive with its own checker. It
is a **sealed library combinator** running on the existing M:N scheduler:

```metel
fun join<A, B>(a: fun() -> A, b: fun() -> B) -> (A, B)   // run on the fiber pool
```

with `e₁ || e₂` as thin sugar for the binary case. `split_at_mut` is the companion sealed
intrinsic that *produces* disjoint borrows; `join` merely *consumes* two independently-typed
closures. No capture sets, no `sep{}`, no new type-system surface — and it lowers trivially
(run sequentially at small leaves, steal-join at large ones).

On **arity**: a chained infix `||` does *not* give clean n-ary fork-join — `a || b || c`
nests as `((A,B),C)` and biases the fork into a tree, and flattening a run of `||` is a
surprising exception to ordinary infix associativity (the more so because the glyph reads as
short-circuiting logical-or, whereas parallel `||` must always run both sides). If an n-ary
form is wanted, it should be a **bracketed `fork { e₁, e₂, … }`** returning a flat tuple, not
a flattened operator: it is naturally variadic, sidesteps Metel's lack of variadic generics
(the compiler desugars each occurrence at its known arity), and gives an obvious place to
hang a scheduling annotation. But n-ary earns its keep only for *statically-known,
heterogeneous* fan-out of three or more tasks — the rarest of the three shapes above;
divide-and-conquer stays binary and data-parallelism is `par_iter`. The recommendation is
therefore: ship binary `||` (sugar over `join`) plus `par_iter`, and add `fork { … }` only if
fixed heterogeneous fan-out proves common enough in real programs to deserve its own surface.

### 6.5 Net effect

Layer 4 shrinks from a calculus to a combinator. The capture-set pass and the `sep{}` grammar
leave the design; what remains is a library `join`/`par_iter` plus the **region-tag-as-
disjointness rule** of §2 (distinct tags ⇒ parallel for free), which is where the genuine
novelty always lived. The headline property — *the annotation that bounds a value's lifetime
also proves it cannot race* — survives intact and gets cheaper: the tag **is** the proof, so
no separate separation calculus is needed to cash it in. This also moves layer 4 off the
static-analysis ledger that Concern 3 charges against (§10): a runtime combinator on the
scheduler, not a compile-time capture-set check.

---

## 7. What the programmer actually writes

Most code sees no annotations. The capability vocabulary is defaulted/inferred; the region
tag is inferred from the allocation site (`r.alloc(..)` → `*own[r] ..`), exactly the way a
type is inferred from a constructor.

```metel
fun main() {
    let b = Box::new(Counter { value: 0 });   // Box<Counter>[Heap] — no annotation
    let a = Arc::new(Config { workers: 4 });  // Arc<Config>[Heap]
    Arena::scoped(fun(arena: &mut Arena) {
        let n = arena.alloc(Node { val: 1 }); // *own[arena] Node — tag inferred
        process(n) || work_elsewhere();        // disjoint tags → parallel for free
    });                                         // arena drops; n freed in O(1)
}
```

Region tags surface explicitly only in two places:

1. **stdlib / region-polymorphic library code** — the `[R]` clause and `Outlives<R>`
   aspect (`fun transfer<T>[Src, Dst: Outlives<Src>](..)`);
2. **structs that hold a pointer into a region they don't own** — `struct Parser[R] {
   input: *own[R] str }`.

Both are the cases where, in the paused branch, you would have written `'a` / `<'a, 'b:
'a>`. The difference is that `[R]` is bound to a parameter or handle the reader can point
at, and the common single-region case needs no clause at all.

---

## 8. Concurrency, end to end

The two reports join cleanly at the concurrency model (substructural §8), because the
capability and the region tag together decide what may cross a fiber boundary:

```
fiber boundary  :  *own T  /  Arc<T>  /  Chan endpoint   — sendable; ownership transfers
                   *own[r] T                              — REJECTED at send (scope-bound)
       ↓ each fiber owns its data
split_at_mut    :  *own T → (*own A, *own B)             — distinct roots, disjoint by construction
       ↓
e₁ || e₂        :  disjoint by region tag / split / ownership — structured fork-join (§6)
fork { … }      :  n-ary fan-out; pairwise-disjoint branches, joined at the brace
```

The region tag makes the send check trivial: a value is sendable iff its capability is
sendable **and** its tag is static (or absent). `*own[arena] T` fails the send check by
construction — the precise property the paused branch needed `RegionFree`/`Send`
approximations to express. And because region-bound values fail that check, **fork-join —
not `spawn` — is the only way to process them in parallel**: its structured join keeps the
borrows inside the region's scope (§6.2).

---

## 9. The one-sentence identity

> *A memory model where every lifetime annotation is the name of a real allocator object
> you can see in scope, the same annotation that bounds a value's lifetime also proves it
> cannot race, and the allocator behind it is an ordinary, swappable library value.*

That sentence contains three things no incumbent offers together: lifetime tags that are
real objects (not Rust's phantom `'a`), tags reused as fork-join disjointness witnesses — the
same tag that bounds a value's lifetime also licenses parallel access to it (neither Rust nor
Pony nor Vale does this) — and Zig-style swappable allocators carrying a *static* lifetime
(Zig has the allocators but no static safety).

---

## 10. Assessment: does this address what paused the previous branch?

The region/lifetime branch was paused for five concerns
(`memory-strategy-research-directions.md`). Taken one at a time:

### Concern 1 — Derivative identity ("is this any different from a Rust crate?")

**Partially — and the split is instructive.** The paused branch's runtime model *was*
`bumpalo`, and its only additive part — invisible lifetimes — was judged "Rust's mental
model, softened." The arena-handle layer **on its own does not escape that verdict**:
`*own[arena] T` tied to the `arena` handle is, mechanically, still `bumpalo`'s `&'bump T`
tied to its `bump` handle. Naming the lifetime after the handle is the same "softened
Rust" the earlier report already weighed.

What changes the identity is **not** the arena layer but the layers around it: reference
capabilities (top-down, Pony-shaped, the report's own recommended non-derivative
direction) and — decisively — the **dual use of the region tag as a fork-join disjointness
witness**, which is genuinely novel. §6 makes this *cheaper without weakening it*: the
novelty survives the removal of the CSC capture-set calculus, because the tag itself is the
disjointness proof. The merged system has a defensible identity; but that identity lives in
layers 1 and 4, and the arena layer is carried by them rather than standing on its own. This is a real improvement over the paused branch, where the region
*was* the whole story and had nothing non-derivative to lean on.

It is also worth recording that the strategic-vision report does **not** reject explicit
allocation control — it nominates "caller-controlled allocation, API-level memory
visibility, library-friendly" as a likely identity centre. The `Arena`-as-aspect /
`InfallibleArena` design (arena §11) is squarely that Zig-flavoured story, not the
Rust-flavoured one. So the arena layer is derivative *as a safety mechanism* but aligned
with the stated identity *as an allocation-control mechanism*. The merge is strongest when
the arena is presented as the latter.

### Concern 2 — Risk concentrated in cross-module lifetime inference and diagnostics

**Addressed for the common case; reappears for the hard case.** The genuine win
(arena §5): region checking for single-region code reduces to *liveness of a named
variable* — "is `arena` still in scope here?" — which the compiler already computes, and
errors name the actual arena (`*own[arena] value escapes the scope of arena`) instead of an
abstract `'a`. That directly dissolves the §3.8 "explain a lifetime the programmer never
wrote" diagnostic problem the earlier branch was most afraid of.

But the moment regions arrive from outside — `fun transfer[Src, Dst: Outlives<Src>]`,
`struct Session[Req, Resp: Outlives<Req>]`, auto-generated `Outlives` impls from
whole-program scope analysis — you are back to `<'a, 'b: 'a>` constraint machinery under a
new spelling. The report concedes it: *"the inference algorithm is not fundamentally
simpler — escape analysis is escape analysis."* So the expensive, risky part
(cross-module, multi-region, the relationship between regions) is mitigated but not
removed. Net: the *frequency* of hitting the hard path drops a lot; the *difficulty* of the
hard path is unchanged.

### Concern 3 — Interpreter-first fit; the "runtime-assist, not static" insight

**Not addressed — this is the weakest point.** The sharpest conclusion of the
reconsideration was: *interpreter-first wants a runtime-assisted safety mechanism
(generational references, refcount+reuse), not a compile-time borrow-checker-lite, which is
"the most expensive possible artifact in a setting where it buys the least."* The
arena-handle layer is precisely a compile-time escape analysis. It re-commits to the static
direction the report argued against for the interpreter.

There are mitigations, and §5–6 sharpen them: the interior-mutability cells, the fork-join
combinator (now a runtime construct on the scheduler rather than a static capture-set check,
§6), and arena drop are all runtime mechanisms the interpreter performs natively — and
dropping the CSC calculus removes one static pass outright. The capability layer *could* be
backed by Vale-style generational tokens (the
research report explicitly notes caps and generational refs are "two views of the same
question") — but the arena report does not take that route for the *region tag*; it leans
on static escape analysis there. If interpreter-first fit is a hard requirement, the merge
still needs an explicit answer for layer 2: either the region tag is enforced by a runtime
arena-generation check (interpreter) that the future compiler elides where escape analysis
proves it safe, or the static analysis is accepted as a compiler-era feature that the
interpreter approximates conservatively.

### Concern 4 — High effort, competing head-on with a mature incumbent

**Mixed, and improved by §4 and §6.** Reducing the capability set from five to three lowers
the surface and the teaching cost, and §6 cuts further by removing the CSC capture-set
calculus and `sep{}` grammar — the parallelism layer becomes a library `join`/`par_iter`
plus the tag-as-disjointness rule, not a checker pass. The competition is now split: the
region/`Outlives` layer still competes head-on with Rust, while the capability + fork-join
layers compete in the far less crowded Pony / Scala-capture-types space. Effort is high
regardless; the strategic exposure is lower because the differentiated layers are not the
ones fighting Rust.

### Concern 5 — What survives lowering to the compiler?

**Fine.** Bump allocation is a standard compiler target; capabilities are static and erase;
the fork-join combinator is an ordinary library/runtime construct that lowers trivially
(sequential at small leaves, steal-join at large ones); the `Outlives` relation lowers like
any region calculus; and
the interior-mutability runtime checks (§5.3) are exactly the kind a compiler elides where
exclusivity is statically provable. The open item is whichever runtime-assist answer
Concern 3 forces for layer 2 — *that* is the thing that must be elidable.

### Verdict

| Concern | Addressed? | Where it stands |
|---|---|---|
| 1 — Derivative identity | **Partially** | Identity now lives in caps + tag-as-disjointness-witness (intact without the CSC calculus, §6); arena layer alone is still softened Rust |
| 2 — Inference / diagnostics risk | **Common case yes** | Single-region = named-variable liveness; multi-region = old `Outlives` machinery returns |
| 3 — Interpreter-first / runtime-assist | **No (layer 2)** | Cells and fork-join are runtime, and §6 removes the static CSC pass; but the region tag still re-commits to static escape analysis |
| 4 — Effort vs incumbent | **Mixed** | Reduced cap set helps; differentiated layers don't fight Rust |
| 5 — Survives lowering | **Yes** | Standard targets; only the (missing) runtime-assist answer for layer 2 is at risk |

**Bottom line.** The merge is a real advance on the paused branch on the two concerns about
*ergonomics and diagnostics* (1 and 2), because it anchors lifetimes to real objects and
overlays a genuinely novel separation story; §4 sharpens it further by cutting the
capability core to `*own`/`*mut`/`*` with `Arc`/`Weak` as library types, §5 shows that even
safe shared mutability needs no new capability and no user `unsafe`, and §6 cuts the
separation layer from a capture-set calculus down to a fork-join combinator whose only job
is to make the region layer's non-sendable borrows usable in parallel. What the merge still
does **not** resolve is the concern the reconsideration treated as decisive —
*interpreter-first wants runtime assistance, not a static borrow-checker-lite* — and on that
axis the arena-handle layer (layer 2) reintroduces exactly what was set aside. The cleanest
path forward is to keep layers 0/1/3/4/5 (the reduced capabilities, linearity, typestate,
the structured fork-join of §6, the Zig-style allocator surface) as the spine, and to make
the region tag of layer 2 **runtime-enforced in the interpreter with compile-time elision** —
turning the one re-incurred concern into the bridge the research report said capabilities and
generational references could form.

---

## References

See `arena-handles-as-lifetime-annotations.md`, `substructural-and-separation-types.md`,
and `memory-strategy-research-directions.md` for the full citation sets. The decisive
framing for this assessment is the research-directions report's "interpreter-first
argument" and "candidate synthesis — capabilities over lifetimes."
