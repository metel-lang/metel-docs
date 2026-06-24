# Linear and Affine Types: A Unified Overview

*Design synthesis — June 2026*

This report recaps the linear/affine substructural story as it is currently scattered
across three RFCs and three reports, and rebuilds it as one model **under the assumption
that the region/lifetime layer of `capability-region-synthesis.md` is accepted** (regions
as lifetimes, `Heap`/`LocalHeap`, the `Arc`/`RefCell`/`Mutex` stdlib, and the reduced
`*own`/`*mut`/`*` capability core). That assumption is decisive: several restrictions in
the existing RFCs exist *only* because borrows of linear values were unavailable without
lifetimes. Once lifetimes land, those restrictions dissolve, and the per-field /
multiplicity direction the reports point at becomes implementable rather than aspirational.

Sources merged here:

- **RFC-0028** (Memory and Reference Model) — the accepted foundation: `linear` types, the
  `@T` owning pointer, `*T`/`*mut T` raw pointers.
- **RFC-0046** (Linear Closure Capture) — `[move x]` capture, the `linear fun` type.
- **RFC-0050** (Closure Capture Lists) — the unified `[&mut x | move x]` capture list.
- **substructural-and-separation-types.md** — the survey: affine default, `own T`,
  typestate, `iso T`, linear capability tokens.
- **per-field-multiplicities.md** — the generalization: 0/1/ω multiplicities per field.
- **capability-region-synthesis.md** — the region/lifetime/capability frame this overview
  assumes as the ambient system.

---

## 1. What each source currently establishes

| Source | Establishes | Status |
|---|---|---|
| RFC-0028 §1 | `linear struct`/`enum`; exactly-once; consume-and-return for reads; `drop` vs `Drop`; `fun<linear T>` | accepted foundation (regions on hold) |
| RFC-0028 §2 | `@T` owning heap pointer; handle "always linear, must be consumed"; recursion via `@T` | accepted |
| RFC-0028 §3 | `*T`/`*mut T` raw pointers, **non-linear values only** until lifetimes | accepted, restriction provisional |
| RFC-0028 OQ-9 | **Affine types not introduced — "linear only"** | accepted, but see §3.1 |
| RFC-0046 | `[move x]` transfers a linear binding into a closure ⇒ closure is `linear fun` (call once); region captures non-`Send` | under review |
| RFC-0050 | `[&mut x]` mutable-ref capture + `[move x]` in one list | under review |
| substructural §2 | Structs **affine by default**, `Copy` opt-in — "the foundation of the whole ownership model" | report (option) |
| substructural §3 | `own T` unique heap owner; in-place mutation; recursion | report (option) |
| substructural §4 | Typestate via consuming receivers + `phantom` state params | report; mostly expressible today |
| substructural §5 | `iso T` isolated reference; fractional uniqueness p=1; `own ⇒ iso` | report (option) |
| substructural §6 | Linear capability tokens (address vs permission split) | report (option) |
| per-field §2–5 | Per-field multiplicities (0/1/ω); borrow suspends the linear field; residual extraction; struct multiplicity = lub of fields | report (direction) |

The recap exposes that the **RFC layer and the report layer disagree on the foundation**,
and that the disagreement is entirely about whether borrows of linear values exist. That is
exactly what the region layer settles.

---

## 2. The three tensions to resolve

### T1 — "Affine not introduced" (RFC-0028 OQ-9) vs "affine is the foundation" (substructural §2, synthesis Layer 0)

RFC-0028 deliberately ships *linear only* and declines affine, because without move
semantics in the evaluator there was nothing for "at-most-once" to mean. But the synthesis
makes **affine-by-default structs Layer 0**, and the `*own`/`*mut`/`*` capabilities it
accepts *presuppose* move semantics — a capability discipline is meaningless if every value
is freely copied. Accepting the synthesis therefore implies accepting affine default. OQ-9
is not wrong, it is *superseded by its own dependency*: the moment you take the caps, you
have taken affine.

### T2 — Consume-and-return (RFC-0028 §1.4–1.5) vs borrowing linear values

RFC-0028 forces `fun buf_len(buf: Buffer) -> (Buffer, Int)` — thread the value out and back —
purely because `*T` may not point at a linear value "without lifetime enforcement"
(§3.1, §1.5 explicitly says the borrow form "will" replace this once lifetimes arrive). The
per-field report's central mechanism — a `&self` borrow that *suspends* the linear
obligation and reinstates it on expiry — is precisely the borrow RFC-0028 deferred. Regions
supply it.

### T3 — Flat per-struct linearity (RFC-0028) vs per-field multiplicities (per-field report)

RFC-0028: a struct is linear iff it has a linear field, and must carry an explicit `linear`
annotation. The per-field report argues this is too coarse — the `fd: i64` in a `linear`
file struct ought to be freely readable and recoverable, which only works if fields carry
*individual* multiplicities and the struct's is the join. This generalization is sound but
only *usable* once borrows-of-linear exist (T2); otherwise you can never read the ω field
without consuming the 1 field.

All three tensions reduce to the same hinge: **does the language have borrows of linear
values?** Under the accepted region layer, yes. So all three resolve in the same direction.

---

## 3. The unified model: one multiplicity spine

### 3.1 Affine is the default; linear is the opt-in (resolves T1)

Every struct/enum is **affine** unless it opts into `Copy` (then ω) or `linear` (then 1):

```
multiplicity   structural rule dropped   meaning                       opt-in
ω  unrestricted   none                    freely copied & dropped       impl Copy
1  affine (DEFAULT) contraction           moved, not copied; may drop   (default)
1! linear           contraction + weakening must be explicitly consumed  linear struct
0  erased           —                      phantom; no runtime presence  phantom
```

This is the substructural lattice of substructural §1, with **affine as the resting state**
(Rust's model) and **linear as the strictly stronger discipline** for values whose silent
drop is a bug (open connection, uncommitted transaction). It supersedes RFC-0028 OQ-9, but
keeps everything OQ-9 actually built: `linear struct`, the linearity checker, `drop`/`Drop`,
`fun<linear T>` are unchanged — affine simply becomes the floor beneath them instead of
"absent."

A consequence worth stating plainly, because it relaxes an RFC-0028 rule: **the owning
pointer becomes affine, not linear.** RFC-0028 §2.1 makes the `@T` handle "always linear —
must be consumed exactly once." In the affine-default world with `Drop` (RAII), an unconsumed
owner at scope/region exit is simply *freed* — weakening runs the destructor, exactly as
Rust's `Box<T>` is affine, not linear. `linear` is then reserved for resources that need an
explicit terminal action the compiler must witness. (RFC-0028 already half-admits this via
the auto-`Drop` insert of §1.9; the unification just names the result "affine.")

### 3.2 Per-field multiplicities as the generalization (resolves T3)

A struct's fields each carry a multiplicity; the struct's own multiplicity is the **least
upper bound** of its fields'. Access follows the field, not the struct:

| Field mult. | via `&self` / `*[r] self` borrow | via consuming `self` |
|---|---|---|
| ω | free copy, no cost | extracted or dropped |
| 1 (affine) | readable; obligation suspended for borrow, reinstated on expiry | moved/consumed |
| 1! (linear) | readable; obligation suspended, reinstated on expiry | **must** be consumed (no weakening) |
| 0 (phantom) | not a value | not a value |

`phantom linear ()` from the reports is just the surface syntax for a multiplicity-1!,
size-0 field. Consumption uses **residual extraction** (per-field Option B): consuming the
linear field releases the ω fields as standalone values. This makes the "two-struct vs
mixed-struct capability token" question (per-field §4) a non-question — they are the same
model at different explicitness.

This whole table is dead without T2's borrow. With it, it is the natural model.

---

## 4. How accepting regions/lifetimes changes the picture

This is the section that the existing RFCs could not write, because they predate the region
decision. Each change below is a *direct consequence* of taking the synthesis layer.

### 4.1 Borrows of linear values become legal — consume-and-return retires

The RFC-0028 §3.1 restriction ("`&x` where `x` is linear is a type error") is lifted exactly
as RFC-0028 itself anticipated. A region-tagged borrow `*[r] T` (or `*mut[r] T`) into a
linear value is sound because the region bounds its life: the borrow provably cannot outlive
the referent, so it cannot create a second consuming path. The per-field "suspend and
reinstate" rule is the borrow checker observing that a `*[r]` borrow holds no consuming
power — it can read ω fields and read-but-not-consume 1/1! fields, and the obligation resumes
when the borrow's region closes.

```metel
// Before (RFC-0028 §1.5): consume-and-return tax
fun buf_len(buf: Buffer) -> (Buffer, Int) { let n = buf.len; (buf, n) }

// After (regions accepted): an ordinary borrow
fun buf_len(buf: *Buffer) -> Int { buf.len }   // Buffer stays linear, unconsumed
```

This is the single largest ergonomic change and it removes a whole category of boilerplate
from RFC-0028.

### 4.2 `@T` is `*own[Heap]`; "the linear handle is the lifetime" is the untagged case

RFC-0028's `@T` and the synthesis's `*own[r] T` are the same unique-owner concept at
different points on the region axis:

```
@T            ==  *own[Heap] T     unique owner in the global heap (RAII-freed)
*own[arena] T                       unique owner in an arena (freed in O(1) at arena drop)
```

RFC-0028's framing "no lifetime annotation needed — the linear handle *is* the lifetime"
survives intact as the `[Heap]`/untagged special case: a heap owner's life is its own
liveness, which the affine checker already tracks. Region tags generalize this to owners that
live in a *named* allocator, with the synthesis's send rule (a region-tagged owner is
non-sendable) falling straight out.

### 4.3 Sendability of linear/affine values across fibers

The capability×region send rule applies uniformly to substructural values: a value may cross
a fiber boundary iff it is sendable **and** its tag is static-or-absent.

```
sendable across spawn / channel :  own T (==@T) / iso T / linear T@[Heap] / Arc<T> / Copy
NOT sendable                    :  *own[arena] T,  *mut/*  borrows,  linear T@[arena]
```

This is exactly RFC-0046's region-closure rule ("a closure holding region-internal `*T` is
not `Send`") generalized from closures to all values, and it makes channels the natural
transport for linear values (RFC-0028 / substructural §8): `Chan<linear T>`'s send *is* the
single consumption.

### 4.4 `Drop`, linear consumption, and region drop compose in a fixed order

Three reclamation mechanisms now coexist and must be ordered:

1. **Linear consumption** — an explicit terminal call (`close`, `commit`) the checker
   witnesses; mandatory for 1! values.
2. **Affine `Drop`** — RAII destructor on scope exit for affine owners that were not moved.
3. **Region drop** — the arena frees all `*own[r]` allocations in O(1) at scope exit.

The rule that keeps these consistent: **a linear (1!) obligation must be discharged before
the region it lives in drops.** A `linear T` allocated in arena `r` cannot be left to region
drop — region drop is a bulk free, not a terminal action, so it would silently violate
exactly-once. The checker rejects an unconsumed 1! value at region exit exactly as it does at
ordinary scope exit (unless the type implements `Drop`, which downgrades the obligation to
affine). Affine and ω values, by contrast, are happily reclaimed by whichever of (2)/(3)
owns their storage.

---

## 5. Owning pointers, `iso`, and capabilities are one axis

With regions accepted, the report-era zoo (`own T`, `iso T`, `*own`, `@T`) collapses onto a
single uniqueness axis, parameterised by *where the value lives* (the region tag) and
*whether it is a pointer or a value qualifier*:

| Form | Pointer/value | Lives | Meaning |
|---|---|---|---|
| `*own[r] T` / `@T` | pointer (owner) | heap / arena `r` | unique owner; frees its cell |
| `iso T` | value qualifier | inline / anywhere | sole live reference; p=1; sendable bridge |
| `*mut[r] T` | pointer (borrow) | — | exclusive borrow; p=1 on loan |
| `*[r] T` | pointer (borrow) | — | shared read borrow; p ∈ (0,1) |

`own ⇒ iso` (substructural §5.3) holds: an owner is trivially the sole reference. `iso` is
the value-side spelling of the same uniqueness `*own` carries pointer-side (the distinction
discussed in the synthesis vocabulary note), and it is what licenses sending an aggregate
that *contains* owned pointers across a fiber. The fractional-uniqueness invariant
(Σ active fractions ≤ 1) is the borrow checker's accounting; regions make "when do borrows
expire" answerable by named scope rather than inferred lifetime.

---

## 6. Closures (RFC-0046 / RFC-0050) under the unified model

Nothing in the closure RFCs needs to change; they slot in cleanly:

- `[move x]` is **affine/linear move-capture**: it consumes `x` into the closure environment.
  If `x` is 1! (linear), the closure is `linear fun` (callable once); if `x` is plain affine,
  the closure is an ordinary `fun` that owns a moved value.
- `[&mut x]` is a `*mut[r]` borrow-capture; the closure is non-`Send` and region-bound,
  consistent with §4.3.
- A closure that move-captures a region-bound value is itself region-bound and non-sendable
  — RFC-0046's rule, now a corollary of the general send rule rather than a special case.

One refinement the unified model offers: RFC-0046 ties `linear fun` to "contains a `move`
capture." Under per-field multiplicities the sharper statement is "**a closure's multiplicity
is the lub of its captures' multiplicities**" — a closure capturing only affine values is
affine (call-once-by-default but droppable), and only a *linear* capture forces 1!. This is
the same lub rule as struct fields (§3.2), applied to the closure's environment.

---

## 7. Capability tokens, phantom, and typestate

These compose without new machinery on top of §3:

- **Capability tokens** (substructural §6): the `FileHandle`/`FileCap` split is the
  two-struct extreme of per-field multiplicities; the mixed `File { fd: i64, _cap: phantom
  linear () }` is the one-struct extreme; residual extraction (§3.2) converts between them.
- **`phantom`** is the multiplicity-0 field; `phantom linear ()` is multiplicity-1!-size-0.
- **Typestate** (substructural §4) needs only consuming receivers + `phantom` state params,
  both already expressible; pairing it with 1! makes "protocol must be *completed*"
  enforceable (no silently-dropped half-finished protocol).
- **Multiplicity polymorphism** (per-field §5, `Guarded<T, Cap>`) is the optional capstone:
  type parameters that range over {ω, 1, 1!}. Powerful, QTT-grade, and explicitly deferred —
  it is the one piece that adds real type-system weight.

---

## 8. Decision ledger

| # | Question | Unified position | Confidence |
|---|---|---|---|
| D1 | Affine introduced after all? | Yes — affine default, linear opt-in; supersedes RFC-0028 OQ-9 | high (implied by accepted caps) |
| D2 | Is `@T`/`*own` linear or affine? | **Affine** (RAII free on drop); reserve `linear` for explicit-terminal-action types | medium — reverses RFC-0028 §2.1 |
| D3 | Borrow linear values? | Yes, via `*[r]`/`*mut[r]`; consume-and-return retired | high (RFC-0028 anticipated it) |
| D4 | Per-field multiplicities? | Adopt 0/1/1!/ω with lub + residual extraction; needed for ergonomic mixed structs | medium — bigger checker change |
| D5 | Linear value in an arena? | Allowed, but 1! obligation must be discharged before region drop | high |
| D6 | Closure multiplicity | lub of captures; `linear fun` only when a 1! is captured | medium — refines RFC-0046 |
| D7 | Multiplicity polymorphism | Defer; optional library-abstraction capstone | high (defer) |

The only genuinely contested item is **D2** (does plain heap allocation force explicit
consumption, Rust-`Box` style affine vs RFC-0028's must-consume handle). Everything else is
either already anticipated by the RFCs or falls out of accepting the region layer.

---

## 9. Implementation staging

1. **Affine move checker** (substructural §2): liveness map in `InferContext`, reject use of
   moved bindings, `Copy` opt-out. This is the floor D1/D2 stand on.
2. **Linear checker** (RFC-0028 §4.1): the existing `LinearEnv` pass, now layered *above* the
   affine checker rather than instead of it.
3. **Region-tagged borrows of linear values** (D3): lift the RFC-0028 §3.1 non-linear
   restriction once `*[r]` exists; implement borrow-suspends-obligation.
4. **Per-field multiplicities** (D4): field-level multiplicity annotations, lub derivation,
   residual extraction on consume. Builds on (3).
5. **Closure multiplicity = lub** (D6): generalize RFC-0046/0050 capture typing.
6. **Multiplicity polymorphism** (D7): deferred.

Steps 1–3 are the high-value, low-controversy core and unblock the bulk of the ergonomic
wins; 4–5 are the per-field generalization; 6 is optional.

---

## References

- RFC-0028 (`rfc-0028-memory-and-reference-model.md`), RFC-0046
  (`rfc-0046-linear-closure-capture.md`), RFC-0050 (`rfc-0050-closure-capture-lists.md`).
- `substructural-and-separation-types.md`, `per-field-multiplicities.md`,
  `capability-region-synthesis.md` (the region/lifetime/capability frame this overview
  assumes).
- Prior art: Girard 1987; Wadler 1990; Barendsen & Smetsers 1996 (Clean); Atkey 2018 /
  McBride 2016 / Brady 2021 (QTT); Bernardy et al. 2018 (Linear Haskell); Marshall & Orchard
  2024 (fractional uniqueness); Rust `Box`/ownership.
