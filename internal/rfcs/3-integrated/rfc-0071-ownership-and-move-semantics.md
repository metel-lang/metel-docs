---
id: rfc-0071
title: "Ownership and Move Semantics"
date: '2026-06-28'
status: integrated
updated: '2026-07-26'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/291'
impl_status: not-started
---

> **Status — accepted.** Establishes the foundational ownership model for Metel
> values. Required by RFC-0063 (Allocator Handles) and all downstream allocator RFCs, which
> depend on affine ownership as a given.

> **Refreshed 2026-07-24, before integration — this RFC had gone stale in place.** Accepted
> 2026-06-28 and never touched since, it missed every subsequent corpus-wide change because
> nothing was working on it. Four kinds of drift, all corrected, none semantic:
>
> | was | now | why |
> |---|---|---|
> | "the `Copy` trait" | "the `Copy` aspect" | Metel has aspects; "trait" is not the language's word |
> | `impl Copy for Point {}` | `extend Point: Copy;` | RFC-0098 (`4-implemented`), plus v0.10.0's bodyless form |
> | `@[r] T` | `@a T` | RFC-0063's allocator syntax |
> | "the region system", RFC-0063 "(Region Handles)" | the allocator system | the region cluster is **`6-refused`** (RFC-0025/0028/0056/0069/0087); RFC-0063/0066/0068 were renamed 2026-07-10 |
>
> **The last row is the substantive one.** §8 described this RFC's interaction with a
> subsystem that has since been refused outright and replaced. The claims themselves survive
> — affine ownership is what makes allocator lifetimes sound, exactly as it made region
> lifetimes sound — but they were stated about a system that no longer exists.
>
> **Worth recording as a process observation, not just a diff.** RFC-0063, RFC-0066 and
> RFC-0068 were all renamed in the 2026-07-10 sweep. RFC-0071 sits in the same cluster and
> was missed, because it was `2-accepted` with no open work against it — the one state in
> the lifecycle where nobody has a reason to open the file. It is the most-depended-on
> document in the corpus and it spent a month describing a refused subsystem.

> **Cross-checked 2026-07-24 against the records cluster, which did not exist when this RFC
> was accepted.** Four interactions; three are clean and the fourth is a real gap.
>
> **§7 versus RFC-0117 (Row Narrowing) — consistent, and worth saying so.** §7 states a
> partially-moved value "may not be used as a whole"; RFC-0117 states that a partially-moved
> *record* narrows to a first-class value of a narrower type. These read as contradictory and
> are not: a struct has no row to narrow *to*, so §7's rule is what remains when row
> machinery is absent. The tier system is doing the work.
>
> **§7's `Drop` ban versus RFC-0116 §3 — clean by construction.** §7 forbids partially moving
> a `Drop` type. RFC-0116 §3 forbids custom `Drop` on a record entirely. So a record is never
> `Drop`, and RFC-0117's narrowing can never collide with §7's ban.
>
> **§7 versus RFC-0114 (Construct) — no conflict, but §7 is silent where RFC-0114 speaks.**
> §7 covers moving *out*; it says nothing about reassembly, because a partially-moved struct
> simply stays unusable. RFC-0114 §3 governs the inverse for records (completing a row fires
> `construct`). Neither contradicts the other; the silence is the design.
>
> **§2 versus RFC-0116 §3 — a real gap: no anonymous record can ever be `Copy`.** §2 makes
> `Copy` an opt-in aspect declared with `extend T: Copy;`. RFC-0096's auto-impl list is a
> closed set of exactly three — `Send`, `Sync`, `Linear` — and `Copy` is not in it, so it must
> be declared. RFC-0116 §3 bans non-local aspect impls for records, and `Copy` is
> standard-library. **Therefore every record is affine and must be moved**, including
> `{ x: i64, y: i64 }`, which is precisely the shape a reader would expect to be freely
> copyable.
>
> This is the same class of problem as records not being `Display`, and it bites harder in one
> place: RFC-0121's width-subtyping rule requires every silently-dropped field to be `Copy`,
> so a dropped field that is *itself* a record could never satisfy it. Both need RFC-0123's
> field-wise constraints. Recorded in RFC-0116 and RFC-0123 as well; **not** a blocker for
> this RFC, which is correct as written — `Copy` being declared rather than derived is
> deliberate.

> **Status — integrated 2026-07-24, targeting v0.12.0.** §1–§7 are merged into
> `public/reference/spec/` as a **new page**, `spec/ownership.md` — the spec had no home for
> ownership at all, and `Copy`/`Drop` appeared in it only as bounds inside coherence
> examples, never defined. Added to the Contents table between Type System and Declarations.
> Four one-line availability markers.
>
> **Integration found two contradictions in the spec's own front matter, both from the
> language having moved on without it:**
>
> - **`spec.md` listed a core design principle reading "Safe memory by default — reference
>   counting, no ownership semantics required."** That is the direct negation of this RFC.
>   It described v0.7-era Metel accurately and has been false-in-intent since this RFC was
>   accepted on 2026-06-28. Replaced with affine ownership, carrying a marker stating that
>   the interpreter still copies everything until v0.12.0.
> - **`spec.md`'s frontmatter said `version: v0.7.0`**, four releases stale. Now v0.11.0.
>   The two are related: that block had not been revisited since v0.7, which is why the
>   principle survived.
>
> **Sibling cross-checks are in §9a** and were done before this pass — three clean
> interactions with the records cluster and one real gap (no record can ever be `Copy`).
> Nothing in the spec merge changed them.
>
> **What the page deliberately does not claim.** Its closing section states that ownership
> answers "how many owners" and `Copy` answers "may this be duplicated", and that neither
> answers "what is borrowed right now" — with an explicit note that nothing here prevents
> two `&var T` to the same place. That is RFC-0122's rule and is not in this release; saying
> so on the page is better than letting a reader infer exclusivity from the word "exclusive"
> two pages away.

> **Status — integrated (2026-07-24).** New spec page ownership.md covering sections 1-7; four availability markers; Contents table updated. Found and fixed two spec contradictions: the 'reference counting, no ownership semantics required' design principle, and a v0.7.0 version stamp. Tracked as #290-#293; #291 (move checking) is canonical.

## Summary

Metel values are **affine by default**: a non-`Copy` value has exactly one owner at any
point in time. Moving a value transfers ownership to a new binding; the source becomes
invalid. This RFC specifies:

1. move semantics as the default for all struct and enum values;
2. `Copy` as an opt-in aspect for types that may be bitwise duplicated;
3. `Drop` as an opt-in aspect for types with destructor logic;
4. the mutual exclusion of `Copy` and `Drop`;
5. drop order within a scope;
6. explicit drop and partial moves.

---

## Motivation

Affine ownership is the foundation of Metel's memory safety model. The allocator system
(RFC-0063 and downstream) relies on allocator-tagged pointers being affine — if `@a T` could
be copied freely, the entire lifetime and disjointness analysis would be unsound. The borrow
checker's single-owner invariant, the `T: !Drop` constraint on scoped move-out (RFC-0066),
and the drop ordering that makes struct-owned arenas safe (RFC-0068) all assume that values
move rather than copy by default.

This RFC makes that assumption explicit and normative.

---

## 1. Values move by default

When a value of a non-`Copy` type is assigned, passed as an argument, or returned, it is
**moved**: ownership transfers from the source to the destination. After a move, the source
binding is invalid and may not be used.

```metel
let x = Node { val = 1 };
let y = x;          // x is moved into y; x is now invalid
process(y);         // y is moved into process; y is now invalid
```

The compiler enforces this statically. A use of an invalidated binding is a compile error:

```
error: use of moved value `x`
  --> ...
   | let y = x;   // x moved here
   | …
   | let z = x;   // error: x is no longer valid
```

Move semantics apply to **every non-`Copy` value** by default. Primitive types and types
implementing `Copy` are excluded (§2).

*(Wording widened 2026-07-24. This previously read "all struct and enum values", which was
exhaustive when written and no longer is — it excludes records, tuples and arrays by
omission. See §9a.)*

---

## 2. The `Copy` aspect

A type implementing `Copy` is **bitwise-copyable**: whenever it appears in a value
position, a copy of its bits is made and the original remains valid. No ownership transfer
occurs.

```metel
let x: i64 = 42;
let y = x;   // copy — x is still valid
let z = x;   // copy again — x is still valid
```

`Copy` is opt-in. The following are `Copy` by default:

- Primitive numeric types (`i8`–`i64`, `u8`–`u64`, `f32`, `f64`)
- `boolean`, `Char`
- Fixed-size arrays whose element type is `Copy`
- Tuples whose element types are all `Copy`

> **Corrected 2026-07-25:** this list said `bool` and `char`. Metel's primitives are named
> `boolean` and `Char`; the earlier spelling names two types that do not exist.

**Where each of these lives is not a free choice — measured against the implementation on
2026-07-25:**
>
> - **The primitives go in `stdlib/`**, one `extend i64: Copy;` per type. Verified: a
>   primitive is a valid `extend` target today.
> - **Fixed-size arrays and tuples must be built into the checker for now**, and should carry
>   a comment saying so. `extend (A, B): Copy` on a concrete tuple raises an internal error
>   (#296), and the generic form `extend<A: Copy, B: Copy> (A, B): Copy;` is *accepted but
>   never satisfies* — a silent no-op, which is worse. `[T; N]` would need a const-generic
>   arity that does not exist; only literal arities parse. **The migration out of the
>   typechecker is tracked as #299**, which records what must exist first: #296 plus
>   RFC-0061 §6's deferred per-arity decision for tuples, and a const-generics RFC (none
>   exists; RFC-0053 defers to it) plus RFC-0124 for arrays.
> - **Do not write `extend<T: Copy> T[]: Copy;`.** It works today and is *wrong*: `T[]` is
>   the dynamic, `Rc`-backed array, so a "copy" would duplicate the handle and silently alias
>   one buffer. Only fixed-size arrays are `Copy`, exactly as this section says. (Noted
>   because the one array form stdlib can express is the one that must not be written.)

Structs and enums are not `Copy` unless explicitly declared. A type may implement `Copy`
only if all its fields (for structs) or all payload types (for enum variants) are `Copy`;
the compiler enforces this structurally:

```metel
struct Point { x: f64, y: f64 }
extend Point: Copy;   // valid — f64 is Copy

struct Node { val: i64, next: @a Node }
extend Node: Copy;    // compile error — @a Node is not Copy
```

---

## 3. The `Drop` aspect

A type implementing `Drop` declares destructor logic that runs when its last owner is
dropped — either by going out of scope or by an explicit `drop` call (§6).

```metel
struct Handle { fd: u64 }

extend Handle: Drop {
    fun drop(self) {
        close_fd(self.fd);
    }
}

{
    let h = Handle { fd = open("file.txt") };
    use_handle(&h);
}   // h goes out of scope; Handle::drop runs automatically
```

`Drop` is opt-in. Types without a `Drop` impl are reclaimed by recursively dropping their
fields, with no user-defined logic.

---

## 4. `Copy` and `Drop` are mutually exclusive

A type may not implement both `Copy` and `Drop`. The combination is unsound: if a `Copy`
type could be duplicated freely, the destructor would run once per copy, potentially
releasing the same resource multiple times.

```metel
extend Handle: Copy;   // compile error — Handle implements Drop
```

The negative bound `T: !Drop` (RFC-0066) is satisfied by any type with no `Drop` impl.
All `Copy` types satisfy `T: !Drop` by this mutual exclusion rule — `Copy` implies `!Drop`.

---

## 5. Drop order

Within a scope, values are dropped in **reverse declaration order** — the last-declared
value is dropped first:

```metel
{
    let a = A::new();   // dropped third
    let b = B::new();   // dropped second
    let c = C::new();   // dropped first
}   // c drops, then b, then a
```

Struct fields are dropped in **declaration order** — first field first. This is symmetric
with construction order and allows later fields to safely depend on earlier ones at init
time without requiring reverse cleanup logic.

```metel
struct Conn {
    socket: Socket,   // dropped first
    buffer: Buffer,   // dropped second
}
```

For structs that own an allocator (`struct Parser(@a: BumpAlloc)`, RFC-0068), the struct's
fields are dropped before the owned arena is freed. This ensures that any `@a T` pointers
stored as fields
are unreachable before the bulk free, preventing use-after-free at the drop site.

---

## 6. Explicit drop

A value may be dropped before the end of its scope with the free function `drop`:

```metel
let handle = Handle { fd = open("file.txt") };
use_handle(&handle);
drop(handle);   // destructor runs here; handle is invalid from this point
```

`drop` takes ownership of its argument. The compiler treats the binding as moved-out after
the call; any subsequent use is a compile error.

---

## 7. Partial moves

Moving out of a struct field leaves the containing value **partially moved**. A partially
moved value may not be used as a whole; only the remaining un-moved fields may be accessed:

```metel
let p = Pair { a = String { … }, b = 42i64 };
let s = p.a;   // p.a moved out; p is partially moved
let n = p.b;   // p.b moved out; p is now fully consumed
// p itself cannot be used as a whole at any point after the first partial move
```

A struct implementing `Drop` may not be partially moved — the destructor requires access
to the complete value. The compiler rejects partial moves of `Drop` types:

```metel
let h = Handle { fd = open("file.txt"), tag = 1u64 };
let fd = h.fd;   // compile error — Handle implements Drop; partial move not allowed
```

---

## 8. Interaction with the allocator system

Allocator-tagged pointers (`@a T`) are non-`Copy` by construction — they carry an allocation
that must have a single owner at all times. Affine ownership is the mechanism that makes
allocator lifetime guarantees sound:

- Because `@a T` is affine, any allocator-tagged value always has exactly one live owner.
  This is what allows the interpreter's uniform allocator to provide deterministic drop
  semantics equivalent to the compiled allocator system.
- The `T: !Drop` bound in RFC-0066 §2.2 requires the definitions of `Drop` and the
  negative bound mechanism established in §3–4 of this RFC.
- The drop ordering in §5 directly determines the order in which arena-allocated fields
  become unreachable before `drop(r)` reclaims the arena's backing memory.

---

## 9c. Implementation tracking

*Filed 2026-07-24, against milestone `v0.12.0`.* Four issues rather than the one per RFC
`AGENTS.md` prescribes — a deliberate exception, because this RFC is seven sections of
essentially unbuilt work with a real dependency order between the pieces:

| issue | sections | depends on |
|---|---|---|
| [#290](https://codeberg.org/metel-lang/metel-core/issues/290) — `Copy` and `Drop` aspects | §2, §3, §4, §9 q3 | — |
| [#291](https://codeberg.org/metel-lang/metel-core/issues/291) — move checking | §1 | #290 |
| [#292](https://codeberg.org/metel-lang/metel-core/issues/292) — drop order and explicit drop | §5, §6 | #290, #291 |
| [#293](https://codeberg.org/metel-lang/metel-core/issues/293) — partial moves | §7, §9a | #291 |

**§9b's place-abstraction requirement is stated in #291**, which is where it constrains the
design. **§9a's rules for tuples, arrays and enum payloads are in #293.** #293 is also the
one v0.13.0 depends on — RFC-0117 is built on field-granularity partial-move tracking, so
descoping it pushes RFC-0119 and the blog's short-term commitment out another release.

> **Release gate: #290 must not ship without #292.** *(Recorded 2026-07-25.)* #290 declares
> the `Drop` aspect and enforces its eligibility rules, but destructor *invocation* is #292.
> Between them, `extend Handle: Drop { fun drop(self) { … } }` compiles and the destructor
> **never runs** — a feature that looks functional and silently does nothing, which is the
> failure mode this project has already hit twice elsewhere.
>
> This is acceptable only because both issues target **v0.12.0**, so the gap exists on
> `develop` and never in a release. **If #292 slips out of v0.12.0, #290 must gain a
> rejection for `Drop` impls before release** rather than shipping them inert. The same does
> not apply to `Copy`: declaring it changes no runtime behaviour either way, since the
> evaluator already duplicates every value — its observable effect is that `T: Copy` bounds
> begin to resolve.

---

## 9b. Implementation requirement inherited from RFC-0122

*Added 2026-07-24, from answering RFC-0122's open question 3.*

Move checking (this RFC) and borrow checking (RFC-0122) are **two analyses over one shared
place abstraction** — Rust's structure, where initialization/move tracking and borrow tracking
are separate dataflow analyses over a shared place-and-move-path representation.

**The requirement that follows, and it is the only thing RFC-0122 asks of this RFC:**

> The place abstraction — whatever represents `x`, `x.f`, `x.f.g` and "reached through a
> dynamic index" — must be a **standalone, reusable component with no move-specific
> assumptions baked in.**

Given that, this RFC ships in v0.12.0 and borrow checking adds a second analysis over the
same places in a later release, with no rework. If places are instead folded into
move-specific state, the borrow checker has to rebuild them, and the two will disagree about
partial moves — which §7's field-granularity tracking makes observable immediately.

**Related, and already consistent:** RFC-0122 resolved its granularity question to *per-field
for statically-named fields, whole-value through a dynamic index* — which is exactly §7's
field granularity plus §9a's array-element ban, arrived at independently. The two documents
agree without either being amended to fit the other.

---

## 9a. Completeness audit against constructs added since acceptance

*Added 2026-07-24 during integration review.* This RFC was accepted 2026-06-28, when structs
and enums were the only aggregates. Six constructs it does not cover, with proposed
resolutions where precedent is unambiguous.

**1. Are `&T` and `&var T` themselves `Copy`? — was unspecified anywhere, and was the one blocking gap.**
Nothing in this RFC, RFC-0067a, or the rest of the corpus states it. RFC-0067a §205 defers
its `T: Copy` gate to "RFC-0071's affine/Copy model," and this RFC never mentions references,
so the two documents point at each other. The consequence if `&T` is affine:

```metel
let r = &x;
f(r);
g(r);        // error — r was moved into f?
```

Shared borrows would be single-use, which is unusable. **Resolved 2026-07-24: `&T` is `Copy`; `&var T` is
not** — Rust's rule, and near-universal. An exclusive reference must stay unique, so it moves
or reborrows; a shared reference has no such obligation. See §9 question 3.

**2. Moving out of an array element — no rule, and it is the case static tracking cannot
handle.** §7 tracks partial moves "at field granularity". `xs[0]` has no field; the index may
be dynamic, so which element is gone is not a static fact. **Resolved: banned outright.**
Rust reaches the same conclusion for the same reason.

**3. Partial moves out of a tuple — no rule.** §7 is written entirely in terms of struct
fields, but v0.11.0 shipped tuple element assignment (`t.0 = v`), so `let a = t.0;` is
writable today. **Resolved: identical to struct fields** — tuple elements are positional
fields and are statically named, so the machinery applies unchanged.

**4. Moving a payload out of an enum variant — no rule.** §1 says move semantics apply to
enums; §7's partial-move rules never mention them. **Resolved: matching a variant and moving
its payload consumes the enum wholly**, not partially — there is no "rest of the value" to
retain, since the other variants were never inhabited.

**5. Closure capture — resolved 2026-07-24; the rule already existed and this RFC had not
caught up.** The spec states capture is **by value**, and by-value capture of a non-`Copy`
type under affine ownership is a **move**. No design was needed — only noticing that
`functions.md` had already decided it, and correcting its word "cloned" to match. See §9
question 4.

> **Items 2, 3 and 4 read "Proposed" until 2026-07-26, and that was stale rather than
> undecided.** All three were adopted normatively when this RFC was integrated — they are the
> `array elements` / `tuple elements` / `enum payloads` rows of the partial-move table in
> `public/reference/spec/ownership.md`, written in the same commit that moved this RFC to
> `3-integrated`. The audit text was simply never updated to match the spec it fed. Marked
> resolved here so the two documents agree; no decision changed, and per PROCESS.md the spec
> was already the normative statement of all three.

**6. Records.** Not a gap in substance — RFC-0117 owns narrowing on partial move, and this
RFC correctly says nothing about it. Only §1's scope sentence needed widening, done above.

---

## 9. Unresolved questions

1. **`Copy` declaration syntax — resolved.** `Copy` is declared via `extend T: Copy;`.
   This is consistent with how other aspects are implemented in Metel. A derive-like
   shorthand (e.g. `derive(Copy)`) will be considered when the derived aspects system
   (RFC-0012) is designed; until then, the explicit impl is the only supported form.

2. **Partial moves and pattern matching — resolved.** Pattern destructuring may
   simultaneously move out of multiple fields, subject to the same rules as sequential
   partial moves: the compiler tracks moved fields at field granularity, `Drop` types may
   not be partially destructured, and a partially destructured value may not be used as a
   whole. Whether individual pattern bindings may borrow rather than move a field (a `ref`
   binding modifier or equivalent) is deferred to the pattern syntax RFC.
3. ~~Are `&T` and `&var T` themselves `Copy`?~~ **Resolved 2026-07-24: `&T` is `Copy`;
   `&var T` is not.** A shared reference carries no obligation — duplicating one grants no
   capability the holder did not already have, and if it were affine a shared borrow would be
   single-use, which is unusable. An exclusive reference must stay unique to *be* exclusive,
   so it moves or reborrows. This is Rust's rule and it is near-universal.

   Recorded here because the gap was circular: RFC-0067a defers its `T: Copy` gate to "this
   RFC's affine/Copy model", and this RFC did not mention references at all. **RFC-0067a's
   own gate is a separate question and is unaffected** — that gate is about reading a
   *referent* of type `T` through a reference, which still requires `T: Copy`. `&T` being
   `Copy` is about duplicating the *reference*.

   **Important qualifier, so this resolution is not over-read: `&var T: !Copy` is necessary
   for exclusivity and nowhere near sufficient.** It prevents *duplicating* an exclusive
   reference:

   ```metel
   let a = &var x;
   let b = a;         // a is moved — no duplication
   ```

   It does nothing about *independent creation*:

   ```metel
   let a = &var x;
   let b = &var x;    // two exclusive references to x — this RFC forbids nothing here
   ```

   The second case needs a checker tracking *what is currently borrowed*, which is neither
   ownership nor `Copy`-ness and is therefore outside this RFC entirely. **The rule that
   makes `&var` actually exclusive — any number of `&T`, or exactly one `&var T`, never
   both — is stated nowhere in the corpus**; it is now RFC-0122's headline. Recorded here
   because "exclusive references are not `Copy`" reads like a guarantee of uniqueness and is
   not one.
4. ~~Closure capture semantics are unspecified.~~ **Resolved 2026-07-24 — the spec already
   settled it and this RFC had not caught up.** `public/reference/spec/functions.md` states
   that "closures capture variables from their enclosing scope **by value**." Under affine
   ownership, by-value capture of a non-`Copy` type is a **move**: the closure takes
   ownership and the enclosing binding is invalid afterwards. Cloning it instead is precisely
   what affine ownership forbids.

   **The spec's wording needed one correction, not its rule.** It said a captured variable is
   "*cloned* into the closure environment", which is accurate for the current
   everything-clones interpreter and wrong once this RFC is enforced. Now "copied", with a
   `Planned for v0.12.0` marker stating the move rule for non-`Copy` captures.
   RFC-0050 (Closure Capture Lists, `0-draft`) may later add explicit capture modes; it is not
   needed for the default, which follows from by-value capture plus affine ownership.

5. ~~Does passing an exclusive reference consume it?~~ **Resolved 2026-07-26 — an interim
   rule, deliberately narrower than RFC-0122's eventual one.** Question 3 above says an
   exclusive reference "moves *or reborrows*" and then specifies only the move. That gap
   became load-bearing the moment `&var T: !Copy` was implemented (#290): with move checking
   (#291), every use of an exclusive reference is a move, and this — which compiles today —
   would stop compiling:

   ```metel
   let r = &var c;
   bump(r);
   bump(r);         // `r` was moved into the previous call
   ```

   That is the same failure §9a question 1 used to decide `&T` must be `Copy`: *"shared
   borrows would be single-use, which is unusable."* The argument transfers to `&var`, and
   the mechanism that answers it is reborrowing — which is **RFC-0122's scope**, and
   RFC-0122 is `0-draft` and deliberately out of v0.12.0.

   **The rule, confined to argument position:**

   > Passing a `&var T` value as an argument to a parameter of type `&var T` **reborrows**
   > it: the reference is borrowed through for the duration of the call, and the original
   > binding remains usable afterwards. **Every other use moves**, including `let q = p;`,
   > returning a reference, storing one in a struct, and capturing one in a closure.

   **The boundary is set by question 3's own example, not chosen freely.** That example
   requires `let b = a;` to move — *"`a` is moved — no duplication"* — so any rule broad
   enough to cover plain binding would contradict a resolution already taken. Argument
   position is what is left, and it is exactly what the failing case needs.

   **Why an interim rule rather than pulling RFC-0122 forward.** Its own question 3 resolved
   that move and borrow checking split safely across releases given §9b, and concluded *"the
   argument for pulling this RFC into v0.12.0 falls away."* Pulling it in would mean three
   lifecycle transitions, an integration cross-check against the thirteen RFCs that reference
   borrow checking, and two unsettled questions (lexical vs. non-lexical; whether any of it
   is observable while the evaluator deep-clones) — to obtain one bullet of it. The narrow
   rule is a strict subset of what RFC-0122 will specify, so it is subsumed rather than
   contradicted when that lands.

   **What this does not do, stated so the rule is not over-read.** A reborrow's *duration* is
   not tracked, because tracking it is borrow checking. In v0.12.0 the rule does exactly one
   thing: it stops move checking from consuming the reference. Two `&var T` to one place
   remain unrejected, as §9 question 3 already records — no guarantee is gained here, and
   none is lost.

---

## References

- RFC-0024 (Linear Types, superseded) — prior exploration of linear/affine ownership in
  Metel; this RFC is the settled formulation of the same core idea.
- RFC-0049 (Linear Function Type System, draft) — function-level linearity constraints;
  orthogonal to but compatible with the value-level move semantics specified here.
- RFC-0063 (Allocator Handles) — depends on affine ownership of `@a T`; §2 states the
  non-`Copy` property of allocator-tagged pointers without grounding it in a prior RFC.
- RFC-0066 (Allocated Value Extraction) — the `T: !Drop` bound is founded on §3–4 of
  this RFC.
- RFC-0068 (Struct-Owned Allocators) — drop ordering in §5 of this RFC governs when
  struct fields become unreachable relative to arena freeing.
