---
id: rfc-0142
title: "Division by Zero and Checked Arithmetic Ergonomics"
date: '2026-08-25'
status: draft
---

> **Written retroactively, 2026-08-25.** Metel's arithmetic operators already ship
> with real behavior for invalid operands — this was never decided by an RFC for
> division/remainder by zero specifically, and diverges from the one RFC that does
> govern the adjacent question (overflow, RFC-0007 D3 — see §2). This document lays
> out the current state precisely, prior art from other languages, and a genuine set
> of design alternatives for division — it does not pre-select one. See "Decision"
> for why no outcome is recorded yet.

## Summary

`a / b` and `a % b` panic on a zero `b` for every integer type, unconditionally —
and per the spec, a panic **terminates the process**, with no in-language recovery
(RFC-0014, `0-draft`, is exploring whether that should ever change, in general, for
all panics). Nothing formally decided this for division specifically; it is the
implementation's inherited default, not a ratified design. This RFC asks whether a
type-safe, ergonomic alternative should exist alongside or instead of the panicking
default — and surveys what other languages actually do before proposing options.

Separately, and not this RFC's main subject: integer *overflow* **does** have a
ratified decision (RFC-0007 D3, `4-implemented`: panic in debug builds, wrap in
release), but the shipped interpreter panics unconditionally in both build modes,
contradicting it. That's a bug against an existing decision, not an open design
question — recorded here because it surfaced in the same investigation, tracked
separately (see §2).

---

## 1. Current behavior, as shipped

Checked directly against `metel-interpreter/src/evaluator/lvalue.rs::eval_binop` on
`develop`.

**Integers** (`i8`/`i16`/`i32`/`i64`/`u8`/`u16`/`u32`/`u64` — identical pattern for
all eight):

```rust
(BinOp::Div, Value::I64(a), Value::I64(b)) => {
    if b == 0 { return Err(MetelError::panic(RuntimeErrorCode::R0007, "division by zero", span)); }
    Value::I64(a.checked_div(b).ok_or_else(|| MetelError::panic(RuntimeErrorCode::R0007, "integer overflow", span))?)
}
```

- `/` and `%` on a zero divisor: `R0007` panic, message `"division by zero"` /
  `"remainder by zero"`.
- `+`, `-`, `*`, `/` on overflow: **also `R0007`**, message `"<type> overflow"`, via
  `checked_add`/`checked_sub`/`checked_mul`/`checked_div`.
- Per `reference/spec/runtime.md`'s Panics section: *"A panic is a hard,
  unrecoverable runtime error... It prints a message and exits the process with a
  non-zero status. Panics cannot be caught."* No `cfg`/`debug_assertions` branch
  exists anywhere in `eval_binop` — this fires identically regardless of build
  profile.

**Floats** (`f32`/`f64`): no checking at all.

```rust
(BinOp::Div, Value::F64(a), Value::F64(b)) => Value::F64(a / b),
(BinOp::Rem, Value::F64(a), Value::F64(b)) => Value::F64(a % b),
```

Plain Rust float operators — full IEEE 754 passthrough. `1.0 / 0.0` is `inf`,
`-1.0 / 0.0` is `-inf`, `0.0 / 0.0` is `NaN`. Never panics, for any float operator.

**No `try`/`catch`/`panic`-recovery construct exists in the grammar
(`metel-frontend/src/grammar.pest`) at all.** A division-by-zero panic today cannot
be handled by the program that triggered it, under any circumstances — it exits the
process. This is what makes the ergonomics question in §3 higher-stakes than it
would be in a language where a panic is merely inconvenient to handle: today there
is no alternative to "avoid triggering it in the first place."

---

## 2. The overflow divergence (not this RFC's subject — recorded, not re-decided)

RFC-0007 (Compiler-Compatible Primitive Type System, `4-implemented`, integrated into
the spec) settled overflow explicitly, as decision D3:

> **In debug builds**: integer overflow panics... **In release builds**: integer
> overflow wraps (two's complement wrapping for signed, modular arithmetic for
> unsigned)... This matches the Rust model... Float overflow follows IEEE 754
> semantics (infinity / NaN) in both build modes — no panicking.

RFC-0013 (Integer Overflow Behaviour) was superseded by this decision and is
`5-superseded`. The float half of D3 matches what §1 found in `eval_binop` exactly.
**The integer half does not**: `eval_binop` calls `checked_add`/`checked_sub`/
`checked_mul`/`checked_div` unconditionally, with no build-mode branch anywhere —
overflow panics in *both* debug and release, contradicting D3's "wrap in release"
half. RFC-0007 also notes: *"Explicit `wrapping_add` / `checked_add` variants are
deferred to the standard library RFC"* — no such stdlib surface exists today either
(confirmed against `core.mtl`: `i64` etc. have only `Copy`, `Display`, `From`).

This is a bug against an already-ratified decision, not an open design question this
RFC should re-litigate. Tracked as metel-core#838 — fix the implementation to match
D3, or bring a case back to amend D3 itself if experience says "always panic" (what's
actually shipped) is preferable to the debug/release split. Out of scope here either
way; §4's options below are about the *zero-divisor* case only, which D3 never
addressed (division by zero is not an overflow condition — there is no "wrapped"
answer for `x / 0` the way there is for `i64::MAX + 1`).

---

## 3. Relationship to RFC-0014 (Panic Recovery, `0-draft`)

RFC-0014 asks a general, *reactive* question: once a panic has occurred, should a
running program be able to catch and recover from it at all? It already names
division by zero as one of panic's three trigger sites (alongside `.yolo()` on an
absent/error value and out-of-bounds access), but proposes no operation-specific
alternative — its options are about a catch mechanism (a `catch` expression, a
fiber-level boundary, etc.), not about changing what `/` itself does.

This RFC is *proactive* and narrower: can specific operations — division chief among
them — be given a type that makes the panic **unreachable by construction**, rather
than merely catchable after the fact? A `NonZero`-typed divisor (§4.3) sidesteps
RFC-0014's question entirely for the call sites that use it: there is nothing to
recover from if the panic can never fire. The two RFCs are complementary, not
competing — RFC-0014 covers the general case (and the operations this RFC doesn't
touch: `.yolo()`, out-of-bounds indexing); this RFC covers what type-level prevention
can do for division specifically, which is strictly stronger where it applies.

---

## 4. Prior art

### 4.1 Survey

- **Rust.** Integer `/`/`%` panic on a zero divisor **unconditionally, in both debug
  and release** — this is *not* governed by the debug/release split that covers
  overflow, because zero has no wrapped answer to fall back to in release mode.
  `checked_div`/`checked_rem` return `Option<T>` (`None` on zero divisor or the
  `MIN / -1` overflow edge case); `wrapping_div` still panics on a zero divisor (only
  the overflow edge case wraps); `saturating_div`, `overflowing_div` exist too. `f64`
  division follows IEEE 754. Separately, `NonZeroU32`/`NonZeroI32`/etc. exist as
  library wrapper types with fallible constructors — division by a value of one of
  these types is possible without a fallible *operation*, because the fallibility
  already happened at construction time, not at the point of division.
- **Swift.** Integer `/` traps (hard crash, no debug/release split at all — Swift
  doesn't have Rust's build-mode distinction for this) on both a zero divisor and
  overflow. Explicit wrapping operators exist for overflow (`&+`, `&-`, `&*`) but
  **there is no `&/`** — Swift's own operator set silently agrees with the
  observation above: wrapping isn't a coherent answer for division by zero the way
  it is for overflow. `dividedReportingOverflow(by:)` returns a
  `(partialValue, overflow: Bool)` tuple as the checked alternative.
- **Zig.** Plain `/` on integers is a **compile error** unless the divisor is
  comptime-known nonzero — the language forces one of `@divTrunc`, `@divFloor`, or
  `@divExact` to be named explicitly instead. Division by zero and overflow are both
  "illegal behavior": a checked panic in `Debug`/`ReleaseSafe` builds, genuine
  undefined behavior in `ReleaseFast`/`ReleaseSmall` (a stricter release-mode stance
  than Rust's defined-wrapping choice). The relevant precedent here isn't the
  build-mode policy — it's that Zig treats "divide by a possibly-zero value" as a
  distinct, explicitly-named operation family rather than one overloaded `/`.
- **Go.** Integer division by a runtime-computed zero panics (a compile-time-constant
  zero divisor is a compile error instead). Overflow is **never** checked, in any
  build mode — silently wraps unconditionally, no debug/release split at all. Float
  division by zero follows IEEE 754, matching Metel's current float behavior exactly.
- **Java.** Integer `/`/`%` throw `ArithmeticException: / by zero` — an ordinary,
  catchable exception, part of the same hierarchy as any other Java exception. `int`/
  `long` overflow is never checked, always silently wraps. Float division follows
  IEEE 754, no exception.
- **C#.** Integer division by zero **always** throws `DivideByZeroException`,
  regardless of context. Overflow is scoped by an explicit `checked`/`unchecked`
  context (a block or expression wrapper, with a project-wide default): `checked`
  throws `OverflowException`, `unchecked` wraps silently. Worth noting as the one
  survey entry with a *contextual, opt-in* checked-arithmetic mechanism rather than a
  single global policy — and that even there, division-by-zero is treated as
  orthogonal to the checked/unchecked overflow context, not folded into it.
- **Python.** `ZeroDivisionError`, an ordinary catchable exception, for **both**
  integer and float division — a deliberate divergence from IEEE 754 (`1.0 / 0.0`
  raises rather than returning `inf`), in the name of surfacing a likely bug rather
  than propagating a sentinel value silently. Python integers are arbitrary-precision,
  so integer overflow doesn't exist as a category at all — not directly relevant to
  Metel's fixed-width types, noted for completeness.
- **Haskell / OCaml / F#.** `div`/`/` raise a runtime exception
  (`divide by zero` / `Division_by_zero`) for integers; floats follow IEEE 754. The
  "safe" alternative in each ecosystem is a library-level `Maybe`/`option`-returning
  function alongside the partial default (the same shape as Rust's `checked_div`),
  not a change to the default operator itself.
- **Ada.** Raises `Constraint_Error` for both division by zero and overflow — a
  single, uniform checked-exception model covering both conditions the same way,
  unlike every other survey entry, which treats them differently.

### 4.2 What the survey actually shows

Every language surveyed **treats integer division-by-zero as strictly worse than
overflow** — none of them extend their "wrap on overflow" escape hatch to cover a
zero divisor, because there is no defined wrapped value for it (Swift's missing `&/`
states this most directly, by omission). Two clusters emerge for *how* the "worse"
case is handled:

- **Catchable exception** (Java, C#, Python, Ada, Haskell/OCaml/F#): the panic is
  real, but the language gives the program a way to recover from it in the moment.
- **Uncatchable trap** (Rust, Swift, Go): division by zero terminates the operation
  (and often the process) with no in-language recovery, full stop — matching Metel's
  current behavior exactly.

**Metel is in the second cluster today, with a gap the first cluster doesn't share
and Rust/Swift partially fill differently: no `checked_div`-equivalent, and no
`NonZero`-equivalent wrapper type exist at all.** Rust and Swift are both in the
uncatchable-trap cluster *and* provide a type-safe escape hatch (`checked_div`/
`NonZero*`, `dividedReportingOverflow`) for code that wants one. Metel currently
provides neither — the panic is the only path, with nothing at the type or API level
to route around it. That gap, not the trap-vs-exception question, is what §5's
options below are actually about closing.

---

## 5. Options

Presented as genuine alternatives, not a pre-selected path — see "Decision."

### 5.1 Option A — Status quo: keep `/`/`%` panicking, add nothing

The baseline every other option is compared against. Zero implementation cost (it's
already shipped), zero new surface to learn, matches Rust's own `/` exactly for the
common case. **Not type-safe**: nothing in a function's signature indicates a
division inside it can terminate the process, and the type checker cannot help a
caller avoid the mistake. **Not ergonomic for code that wants to handle a possibly-
zero divisor**: the only option is a manual `if b == 0 { ... }` guard immediately
before the division — unenforced (nothing stops the guard and the division from
drifting apart during a later edit), and boilerplate repeated at every call site that
cares.

### 5.2 Option B — `checked_div`/`checked_rem`, `Perhaps<T>`-returning, `/` unchanged

Add `a.checked_div(b) -> Perhaps<T>` / `a.checked_rem(b) -> Perhaps<T>` (per integer
type, matching `core.mtl`'s existing per-type method style) alongside the unchanged
panicking `/`/`%`. Directly mirrors Rust's `checked_div`. Cheap to implement (a
native method returning `nope`/`Perhaps::Some` instead of panicking — the zero-check
already exists in `eval_binop`, this just changes what happens on the `true` branch),
composes with `?`/`match`/`unwrap_or` the same as every other `Perhaps`-returning
stdlib function already does (`env::get`, `List::get`).

Ergonomic *for code that remembers to reach for it* — but doesn't change `/`'s own
danger at all, so it's opt-in safety, not structural safety. A reviewer still can't
tell from a signature whether a given division was checked or not; the mistake this
RFC is worried about (a divisor that turns out to be zero at a call site nobody
thought to guard) is exactly as easy to make as it is today. Addresses the ergonomic
half of the ask, not the type-safe half, on its own.

### 5.3 Option C — `NonZero<T>` wrapper type; division accepts it directly

The type-safe candidate. A wrapper type per integer type (or one generic
`NonZero<T: Integer>`), constructed fallibly:

```metel
let n: Perhaps<NonZero<i64>> = NonZero::new(user_input);
```

`a / b` where `b: NonZero<T>` becomes a **total function** — panic-free by
construction, and that guarantee is now visible in any signature that takes a
`NonZero<T>` divisor instead of a plain `T`. This is the only option that gives the
type checker, not just the programmer's memory, responsibility for the guarantee.

**What "ergonomic" requires here, concretely — this is the real design work, not a
detail:**

- **The runtime-computed case still needs a fallible constructor.** This is
  irreducible: whether a runtime value is zero is real information, and it has to
  enter the type system through *some* fallible step, the same as Option B's
  `checked_div`. `NonZero::new` returning `Perhaps<NonZero<T>>` is that step —
  `NonZero<T>` doesn't remove this cost, it relocates it from "checked at every
  division" to "checked once at construction," which pays off only when one
  `NonZero<T>` value gets divided into more than once (a loop, a function called
  repeatedly with the same divisor) — a single-use divisor gains nothing over Option
  B and pays a wrapper-type tax for it.
- **Flow-sensitive narrowing would make the common case free, if the type checker
  supports it.** After `if b != 0 { ... }`, can the checker treat `b` as `NonZero<T>`
  inside the branch without an explicit `NonZero::new` call? This is the difference
  between "ergonomic" and "a wrapper type nobody uses because `checked_div` is less
  ceremony for the same guarantee." **Open question, not resolved by this RFC**:
  does Metel's type checker have (or plan) anything resembling occurrence-typing /
  flow-sensitive refinement anywhere else in the language to build this on, or would
  it be new machinery specific to this feature?
- **A literal divisor should never need a runtime check at all.** `x / 2` — the `2`
  is provably nonzero at compile time; the compiler should accept a nonzero integer
  literal directly where `NonZero<T>` is expected, no `NonZero::new(2).yolo()`
  needed, the same way Zig's `@divExact` reasons about comptime-known operands. This
  is the single highest-leverage ergonomic win available, since dividing by a
  constant is by far the most common shape of division in real code.
- **Interaction with `/`'s own signature.** Does `/` become overloaded — `T / T`
  keeps panicking, `T / NonZero<T>` doesn't — or does `NonZero<T>` division get a
  distinct method/operator? An overloaded `/` is more discoverable (existing code
  keeps working, a caller opts in by changing the divisor's type) but means `/`'s
  panic-or-not behavior now depends on which overload resolved, which needs to be
  legible at the call site, not just in documentation.

Cost: a genuinely new type in the standard library, plus (if the narrowing/literal
ergonomics above are pursued) real type-checker work, not just a library addition —
this is the most expensive option to build well, and the option most likely to be
built *badly* (a `NonZero<T>` nobody reaches for because it's more typing than
`checked_div` for no benefit) if the ergonomics work is skipped.

### 5.4 Option D — `/`/`%` themselves return `Perhaps<T>`/`Result<T, E>`

The maximal-safety end of the spectrum: change what `/` *means* for integers, so
every division is checked, always. No language in the §4 survey does this for its
primary division operator — the closest is Elm's philosophy of returning `Maybe` from
partial operations generally, applied consistently rather than as a special case for
division. Cost is severe and uniform: **every** division needs unwrapping, including
the overwhelming majority where the divisor is a literal or otherwise provably
nonzero — the common case pays the full ergonomic cost of the rare one. Listed for
completeness against "different options," not recommended: this inverts the cost
Option C's literal-inference sub-point is specifically trying to avoid.

### 5.5 Option E — General panic recovery (defer to RFC-0014)

Add a `catch`/recovery mechanism covering panics broadly (RFC-0014's own subject),
and let division keep panicking, relying on recovery to make that survivable. Doesn't
give a type-level guarantee (a signature still can't say "this division is safe"),
and is a substantially larger, more invasive RFC on its own — touches every panic
site, not just arithmetic, and RFC-0014's own open questions (fiber-level boundaries,
interaction with concurrency/RFC-0003) are unresolved. Not mutually exclusive with
Options B/C — see §3 — but not a substitute for them either: recovery answers "what
happens after," not "can this call site provably not fail."

### 5.6 Option F — Lint/diagnostic only

Keep `/`/`%` exactly as they are; add a compiler diagnostic (warning-level, not an
error) when a division's divisor isn't statically provable nonzero (not a literal, no
narrowing guard in scope). Cheapest option that does *something* — no new types, no
new operators, purely a tooling nudge toward the `if b == 0` guard the language
already supports. Weakest guarantee of any option here: a lint can be silenced or
ignored, and gives none of the structural, enforced safety Options B/C do. Reasonable
as a stopgap alongside B or C, not a replacement for either.

---

## 6. A non-binding recommendation

Offered because "here are options" without any weighing isn't that useful on its
own — not a substitute for the review this RFC is explicitly deferring (see
"Decision").

**Ship Option B first.** It's cheap (the zero-check already exists in `eval_binop`;
this only changes the failure path), unblocks safe code immediately, and directly
mirrors a pattern the stdlib already uses everywhere (`Perhaps`-returning methods).
No reason to gate it on Option C's harder questions.

**Treat Option C as the real answer, contingent on the type-checker questions in
§5.3 actually being answered** — a `NonZero<T>` shipped without flow-sensitive
narrowing or literal inference is a wrapper type strictly more expensive than
`checked_div` for the same guarantee, and would likely go unused. Worth its own
follow-up RFC once (or if) an answer to the narrowing question exists, rather than
guessing one into this document.

**Options D and F**: D's cost doesn't seem worth its extra safety margin over C given
C is achievable; F is reasonable as a small, independent addition alongside B/C
(cheap, non-blocking, no reason it can't ship in parallel) but shouldn't be treated
as sufficient on its own.

**Option E (general panic recovery)**: leave to RFC-0014 on its own timeline — real,
but a materially larger question than this RFC's scope.

---

## 7. Open Questions

1. **Does Metel's type checker have, or plan, any flow-sensitive narrowing
   mechanism** (occurrence typing, refinement after a guard) that Option C's
   ergonomic story could build on — or would this be new machinery invented
   specifically for `NonZero<T>`? Blocks a real cost estimate for Option C.
2. **Should `/` be overloaded for a `NonZero<T>` divisor, or should the panic-free
   path be a differently-named operation** (matching Zig's explicit
   `@divTrunc`/`@divExact` naming rather than Rust's overload-by-divisor-type)?
   Affects discoverability and whether a call site's panic-safety is legible without
   checking the divisor's declared type.
3. **The RFC-0007 D3 implementation divergence (§2)**: fix the implementation to
   match the ratified debug-panics/release-wraps decision, or bring evidence back to
   amend D3 itself? Not this RFC's call to make **for division** — that's what §5's
   options are for — but the overflow question needs *an* explicit decision
   somewhere, and currently has neither.
4. **Does `Perhaps<NonZero<T>>::yolo()` for a compile-time-provable-nonzero literal
   need to exist as an ergonomic escape hatch**, or does §5.3's literal-inference
   proposal make that path unnecessary in practice? Only matters if literal inference
   doesn't fully land.

---

## References

- RFC-0007 (Compiler-Compatible Primitive Type System, `4-implemented`) — D3: the
  ratified overflow decision, diverged from by the current implementation (§2).
- RFC-0013 (Integer Overflow Behaviour, `5-superseded` by RFC-0007) — the original,
  narrower overflow-only exploration; superseded, not resurrected here.
- RFC-0014 (Panic Recovery, `0-draft`) — the general, reactive sibling question;
  relationship stated precisely in §3.
- `reference/spec/runtime.md`, Panics section — the canonical, integrated statement
  that a panic is unrecoverable and terminates the process; the fact this RFC's
  stakes rest on.
- `metel-interpreter/src/evaluator/lvalue.rs::eval_binop` — the actual shipped
  behavior §1 is grounded in, checked directly against `develop`.
- `metel-frontend/stdlib/core.mtl` — confirms no `checked_*`/`NonZero` surface
  exists on any numeric type today.

---

## Decision

**Outcome:** *(pending — intentionally.)* This document exists to put real
alternatives in front of a reviewer, not to pre-select one; §6's recommendation is
offered as a starting point for that review, not a claim of consensus. What's settled
by writing this down: the current behavior (§1) is accurately described, the RFC-0007
divergence (§2) is a separate, already-decided question this RFC does not reopen, and
RFC-0014 (§3) is complementary rather than overlapping. What isn't settled: which of
§5's options (or combination) Metel actually adopts.
**Target:** *(blank until accepted.)*
