---
id: rfc-0142
title: "Division by Zero and Checked Arithmetic Ergonomics"
date: '2026-08-25'
status: under-review
updated: '2026-08-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/841'
---

> **Written retroactively, 2026-08-25; expanded 2026-08-27.** Metel's arithmetic
> operators already ship with real behavior for invalid operands — none of it was
> ever decided by an RFC at the ergonomics level. Division/remainder by zero panics
> unconditionally, with no formal decision behind that and no escape hatch (§1, §6).
> Overflow panics unconditionally too — RFC-0007 D3 originally specified a
> debug-panics/release-wraps split for it, but that was amended 2026-08-26 to match
> what was actually shipped (no debug/release build-mode concept exists in Metel at
> all — see §2) rather than building one. **That amendment settled *whether overflow
> panics*, not *whether an alternative to panicking should exist*** — RFC-0007 itself
> flagged exactly that as future work ("explicit `wrapping_add`/`checked_add`
> variants are deferred to the standard library RFC") and it was never written. This
> document is that RFC, expanded to cover both operand conditions together: they
> share the same underlying shape (a panicking default, no type-safe way around it)
> even though their available *answers* differ in an important, concrete way (§5).
> Options are presented for both — none pre-selected. See "Decision."

> **Status — under review (2026-08-27).** Committed to v0.13.0 (issue #841, milestoned 2026-08-27); RFC-0142 must be accepted, integrated, and implemented before std::math (#254) is implemented.

## Summary

`a / b` and `a % b` panic on a zero `b`, for every integer type, unconditionally.
`a + b`, `a - b`, `a * b`, and `a / b` also panic on overflow, for every integer
type, unconditionally (RFC-0007 D3, amended 2026-08-26 to state this plainly instead
of a debug/release split that was never implemented). Per the spec, a panic
**terminates the process**, with no in-language recovery at all (RFC-0014, `0-draft`,
is exploring whether that should ever change, in general, for all panics — §3).

Neither condition has a type-safe or ergonomic alternative today: no `checked_*`
method, no wrapping/saturating variant, no wrapper type that makes either condition
provably unreachable. This RFC surveys what other languages do for both — division
and overflow are related but not identical problems, and the survey (§4, §5) finds a
real asymmetry between them worth designing around rather than papering over: every
language surveyed treats a zero divisor as *strictly worse* than overflow, because
overflow has coherent non-panicking answers (wrap, saturate) that a zero divisor
simply doesn't. Options follow for each (§6, §7), and a non-binding recommendation
(§8) — but this document's purpose is to put real alternatives in front of a
reviewer, not to pre-select one.

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
  exists anywhere in `eval_binop` — both conditions fire identically regardless of
  build profile (confirmed as intentional, not a gap, by RFC-0007 D3's amendment —
  see §2).

**Floats** (`f32`/`f64`): no checking at all, for either condition.

```rust
(BinOp::Div, Value::F64(a), Value::F64(b)) => Value::F64(a / b),
(BinOp::Rem, Value::F64(a), Value::F64(b)) => Value::F64(a % b),
```

Plain Rust float operators — full IEEE 754 passthrough. `1.0 / 0.0` is `inf`,
`-1.0 / 0.0` is `-inf`, `0.0 / 0.0` is `NaN`; float overflow produces `inf`/`-inf`
the same way. Never panics, for any float operator, for either condition.

**No `try`/`catch`/`panic`-recovery construct exists in the grammar
(`metel-frontend/src/grammar.pest`) at all.** A panic today cannot be handled by the
program that triggered it, under any circumstances — it exits the process. This is
what makes the ergonomics questions in §6/§7 higher-stakes than they would be in a
language where a panic is merely inconvenient to handle: today there is no
alternative to "avoid triggering it in the first place," for division or overflow
alike.

---

## 2. Overflow: whether it panics is settled; whether an alternative exists is not

RFC-0007 (Compiler-Compatible Primitive Type System, `4-implemented`, integrated into
the spec) originally specified overflow's default behavior, as decision D3, with a
debug-panics/release-wraps split matching Rust's build-profile model. The shipped
interpreter never implemented the release-wraps half — `eval_binop` calls
`checked_add`/`checked_sub`/`checked_mul`/`checked_div` unconditionally, with no
build-mode branch anywhere, so overflow panicked in every build from the feature's
introduction.

**Resolved 2026-08-26, not by this RFC**: D3 was amended rather than the
implementation changed. Metel has no debug/release build-mode concept for the
*programs it runs* at all (the `metel` interpreter's full CLI surface is `file`,
`--debug-ast`, `--move-check` — no `--release`) — the split was borrowed from Rust's
own build-profile model without Metel having an equivalent to borrow it *onto*.
Building one solely to give overflow two behaviors was judged not worth it. D3 now
reads: integer overflow panics unconditionally, in every build; float overflow's
IEEE-754 half was already correct and is unchanged. See RFC-0007's own "Overflow
Semantics" section and `reference/spec/types.md`'s
`spec.types.sized-numeric-types.dynamics-1` for the normative text. metel-core#838
tracked this; closed by the correction.

**What that amendment did *not* settle, and this RFC now does cover**: RFC-0007
itself, in the same "Overflow Semantics" section, noted *"Explicit `wrapping_add` /
`checked_add` variants are deferred to the standard library RFC."* No such RFC was
ever written, and no such stdlib surface exists today (confirmed against
`core.mtl`: `i64` etc. have only `Copy`, `Display`, `From`). The *default* behavior
question (panic, unconditionally) is closed. The *escape-hatch* question — should a
checked, wrapping, or saturating alternative exist for code that wants one, mirroring
what §6 asks for division — was never asked at all. §5 and §7 ask it.

---

## 3. Relationship to RFC-0014 (Panic Recovery, `0-draft`)

RFC-0014 asks a general, *reactive* question: once a panic has occurred, should a
running program be able to catch and recover from it at all? It already names
division by zero as one of panic's three trigger sites (alongside `.yolo()` on an
absent/error value and out-of-bounds access) — overflow isn't named there but is the
same shape of problem. RFC-0014's own options are about a catch mechanism (a `catch`
expression, a fiber-level boundary, etc.), not about changing what any specific
operator does.

This RFC is *proactive* and narrower: can specific operations — division and the
four overflow-checked operators chief among them — be given a type or an alternative
that makes the panic **unreachable by construction**, rather than merely catchable
after the fact? A `NonZero`-typed divisor (§6.3) sidesteps RFC-0014's question
entirely for the call sites that use it: there is nothing to recover from if the
panic can never fire. A `wrapping_add` (§7.3) sidesteps it even more cheaply for
overflow, since wrapping is already a total, panic-free function with no fallible
step anywhere. The two RFCs are complementary, not competing — RFC-0014 covers the
general case (and the operations this RFC doesn't touch: `.yolo()`, out-of-bounds
indexing); this RFC covers what type-level or total-function prevention can do for
arithmetic specifically, which is strictly stronger where it applies.

---

## 4. Prior art: division

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
to route around it. That gap, not the trap-vs-exception question, is what §6's
options below are actually about closing.

---

## 5. Prior art: overflow

### 5.1 Survey

- **Rust.** The richest survey entry, deliberately: **four** distinct alternative
  operation families per arithmetic operator, not one. `checked_add`/`checked_sub`/
  `checked_mul`/`checked_div` return `Option<T>` (`None` on overflow). `wrapping_add`
  etc. return `T` directly — two's-complement wraparound, a **total function, no
  fallibility at all**. `saturating_add` etc. also return `T` directly — clamped to
  the type's `MIN`/`MAX` instead of wrapping, a different total answer for code where
  "stop at the boundary" is more sensible than "wrap around it" (a health bar, a
  volume level, a counter that shouldn't go negative). `overflowing_add` etc. return
  `(T, bool)` — the wrapped result *and* whether it overflowed, the most
  information-preserving of the four. All four exist because wrapping and saturating
  are *both* coherent, non-panicking, total answers to overflow — unlike division by
  zero, which has neither (§4.2).
- **Swift.** Wraparound is a first-class **operator**, not a method: `&+`, `&-`, `&*`
  (no `&/` — division's own lack of a coherent wrapped answer, §4.1, holds here too).
  `.addingReportingOverflow(_:)` etc. return the Rust-`overflowing_*`-equivalent
  tuple. No built-in saturating operator or method in the standard library.
- **Zig.** Mirrors its division stance: wraparound is an explicit **operator sigil**
  (`+%`, `-%`, `*%`), not a method — plain `+`/`-`/`*` is checked (panic in
  `Debug`/`ReleaseSafe`, undefined behavior in `ReleaseFast`/`ReleaseSmall`). Same
  underlying philosophy as division: a distinct, explicitly-named/sigiled operation
  family instead of one overloaded operator whose behavior depends on invisible
  build-mode state.
- **Go.** No escape hatch in *either* direction: `+`/`-`/`*` always wrap, silently,
  unconditionally, with no way to opt into a checked variant at all. The minimal end
  of the whole survey — Go doesn't treat this as needing a decision.
- **Java.** Never checked, always silently wraps for `int`/`long` — no checked,
  wrapping (redundant, since default already wraps), or saturating variant exists in
  the language or its core library.
- **C#.** The one contextual, scope-based precedent in the survey: `checked { ... }`
  / `unchecked { ... }` wrap a block or a single expression, flipping whether `+`/
  `-`/`*` throw `OverflowException` or wrap silently *without changing which operator
  is written* — existing arithmetic syntax keeps meaning what it already means, the
  surrounding context changes what happens on overflow. A project-wide compiler
  setting picks the default when neither is written explicitly.
- **Python.** Arbitrary-precision integers — overflow isn't a category that exists.

### 5.2 What the survey actually shows

Unlike division (§4.2's two clusters), overflow's survey splits along a different
axis: **whether wrapping is opt-in-per-operation (Rust's methods, Swift/Zig's
sigils) or the language's only answer (Go, Java's unconditional default) or
scope-based (C#'s `checked`/`unchecked`)**. Every language that offers a checked
*or* an explicit-wrapping alternative to its default (Rust, Swift, Zig, C#) treats
that alternative as **cheaper to provide than division's equivalent**, because
wrapping and saturating need no fallible constructor, no wrapper type, and no
narrowing story — they're already total functions. The entire ergonomic-cost
argument that makes division's `NonZero<T>` (§6.3) expensive to get right (the
runtime-computed case needs *some* fallible step, irreducibly) **does not apply to
overflow's wrapping/saturating alternatives at all**. That's the asymmetry §7 is
built around: division's hard problem (a genuinely fallible operation, dressed up to
look total) isn't overflow's problem (an operation that already has multiple total,
non-panicking answers, none of which Metel currently exposes).

**Metel today has none of the four Rust-shaped alternatives, no operator sigils, and
no contextual block** — every other language surveyed that treats overflow as worth
a decision at all (everyone except Go and Python) provides at least one alternative
to its default. Metel provides none.

---

## 6. Options: division

Presented as genuine alternatives, not a pre-selected path — see "Decision."

### 6.1 Option A — Status quo: keep `/`/`%` panicking, add nothing

The baseline every other option is compared against. Zero implementation cost (it's
already shipped), zero new surface to learn, matches Rust's own `/` exactly for the
common case. **Not type-safe**: nothing in a function's signature indicates a
division inside it can terminate the process, and the type checker cannot help a
caller avoid the mistake. **Not ergonomic for code that wants to handle a possibly-
zero divisor**: the only option is a manual `if b == 0 { ... }` guard immediately
before the division — unenforced (nothing stops the guard and the division from
drifting apart during a later edit), and boilerplate repeated at every call site that
cares.

### 6.2 Option B — `checked_div`/`checked_rem`, `Perhaps<T>`-returning, `/` unchanged

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

### 6.3 Option C — `NonZero<T>` wrapper type; division accepts it directly

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
  B and pays a wrapper-type tax for it. (Overflow's equivalent options, §7.3/§7.4,
  don't share this cost at all — see §5.2.)
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

### 6.4 Option D — `/`/`%` themselves return `Perhaps<T>`/`Result<T, E>`

The maximal-safety end of the spectrum: change what `/` *means* for integers, so
every division is checked, always. No language in the §4 survey does this for its
primary division operator — the closest is Elm's philosophy of returning `Maybe` from
partial operations generally, applied consistently rather than as a special case for
division. Cost is severe and uniform: **every** division needs unwrapping, including
the overwhelming majority where the divisor is a literal or otherwise provably
nonzero — the common case pays the full ergonomic cost of the rare one. Listed for
completeness against "different options," not recommended: this inverts the cost
Option C's literal-inference sub-point is specifically trying to avoid.

### 6.5 Option E — General panic recovery (defer to RFC-0014)

Add a `catch`/recovery mechanism covering panics broadly (RFC-0014's own subject),
and let division keep panicking, relying on recovery to make that survivable. Doesn't
give a type-level guarantee (a signature still can't say "this division is safe"),
and is a substantially larger, more invasive RFC on its own — touches every panic
site, not just arithmetic, and RFC-0014's own open questions (fiber-level boundaries,
interaction with concurrency/RFC-0003) are unresolved. Not mutually exclusive with
Options B/C — see §3 — but not a substitute for them either: recovery answers "what
happens after," not "can this call site provably not fail."

### 6.6 Option F — Lint/diagnostic only

Keep `/`/`%` exactly as they are; add a compiler diagnostic (warning-level, not an
error) when a division's divisor isn't statically provable nonzero (not a literal, no
narrowing guard in scope). Cheapest option that does *something* — no new types, no
new operators, purely a tooling nudge toward the `if b == 0` guard the language
already supports. Weakest guarantee of any option here: a lint can be silenced or
ignored, and gives none of the structural, enforced safety Options B/C do. Reasonable
as a stopgap alongside B or C, not a replacement for either.

---

## 7. Options: overflow

Presented as genuine alternatives, not a pre-selected path — see "Decision." Several
of these are cheaper than their division counterparts precisely because wrapping and
saturating are already total functions (§5.2) — that asymmetry is load-bearing
throughout this section, not incidental.

### 7.1 Option A′ — Status quo: keep `+`/`-`/`*`/`/` panicking on overflow, add nothing

The baseline. Zero cost (already shipped, and now correctly specified — §2). **Not
type-safe**, same as division's Option A. **Arguably worse ergonomically than
division's status quo**: a manual pre-check for division is one comparison
(`if b == 0`); a manual pre-check for overflow requires knowing the type's `MIN`/
`MAX` and getting a boundary comparison right by hand at every call site
(`if a > T::MAX - b` for addition, and the equivalent is fiddlier still for
multiplication) — exactly the kind of thing a language provides a checked primitive
for rather than leaving to be re-derived correctly on every use.

### 7.2 Option B′ — `checked_add`/`checked_sub`/`checked_mul`/`checked_div`, `Perhaps<T>`-returning

Direct mirror of division's Option B (§6.2), applied to all four operators. Cheap for
the same reason: the `checked_*` calls already exist in `eval_binop`, this only
changes what happens on the `None` branch instead of panicking. Same limitation too:
opt-in safety, not structural — `+` itself stays exactly as dangerous as it is today,
this just gives code that remembers to reach for it a way out.

### 7.3 Option C′ — `wrapping_add`/`wrapping_sub`/`wrapping_mul`/`wrapping_div`, `T`-returning

**No division equivalent exists in this document** — this is new territory, and the
cheapest genuinely type-safe option in either half of this RFC. Two's-complement
wraparound, returned directly as `T`: no `Perhaps`, no fallible constructor, no
narrowing story, because wrapping is *already* a total function over every possible
`(a, b)` pair — there is no input that makes it fail. `wrapping_div` still needs the
zero-divisor guard `checked_div` does (wrapping doesn't rescue *that* condition,
consistent with §4.2's finding that nothing rescues it) — only `wrapping_add`/
`wrapping_sub`/`wrapping_mul` are unconditionally total.

Worth stating plainly: **this is close to what RFC-0007 D3 originally intended for
"release mode,"** just delivered as an explicit, opt-in method instead of an
invisible property of how the interpreter binary happened to be compiled. Read that
way, shipping this is closer to honoring D3's original spirit than the amendment in
§2 was — the amendment corrected the *default*; this would supply the *choice* D3
was trying to give release builds, as something a caller opts into deliberately
rather than something that varies with an environment fact the program can't see.

### 7.4 Option D′ — `saturating_add`/`saturating_sub`/`saturating_mul`/`saturating_div`, `T`-returning

Also a total function, also no division-shaped irreducible cost. Clamps to the
type's `MIN`/`MAX` instead of wrapping around past it — the right answer for a
health bar, a volume level, a counter that should stop rather than roll over to a
huge negative. Distinct semantics from wrapping, not a variant of it; both are cheap
for the same underlying reason (§5.2), so there's no cost argument for shipping one
without the other, only a "how much surface at once" one.

### 7.5 Option E′ — `overflowing_add`/etc., `(T, boolean)`-returning

The information-preserving option: returns the wrapped result *and* whether it
overflowed, in one call, for code that needs both (log the overflow, but keep
running with the wrapped value). Metel has tuple types already (`Value::Tuple`
exists in the evaluator, and tuple syntax is ordinary Metel), so this needs no new
type at all — strictly additive over Option C′, for the cases that want the flag.
Marginal value over shipping C′ and D′ alone; lowest priority of the four `T`/tuple-
returning options unless a concrete use case asks for it.

### 7.6 Option F′ — Contextual `checked { }` / `unchecked { }` block (C#'s model)

The one option in this RFC that doesn't add a method or operator, but changes what
existing `+`/`-`/`*`/`/` syntax means within a lexical scope. Appealing because it
requires no call-site rewriting — existing arithmetic-heavy code gains or loses
overflow checking by being wrapped in a block, not by having every operator call
renamed. Real cost: this is type-checker and evaluator *scoping* work, not a stdlib
addition — a materially different (and larger) kind of change than any other option
in this document, closer in shape to a small language feature than a library
function. C# is real, working precedent that the idea is sound, not evidence it's
cheap to build.

### 7.7 Option G′ — Lint/diagnostic only

Mirrors division's Option F (§6.6): keep the default panicking behavior untouched,
add a warning-level diagnostic for an arithmetic operation whose operands aren't
statically provable in-range. Same cost/guarantee trade-off as its division
counterpart — cheap, additive, not a substitute for a real alternative.

---

## 8. A non-binding recommendation

Offered because "here are options" without any weighing isn't that useful on its
own — not a substitute for the review this RFC is explicitly deferring (see
"Decision").

**Division.** Ship Option B (§6.2) first — cheap, unblocks safe code immediately,
directly mirrors a pattern the stdlib already uses everywhere. Treat Option C
(`NonZero<T>`, §6.3) as the real answer, contingent on the type-checker questions in
§6.3 actually being answered — shipped without flow-sensitive narrowing or literal
inference, it's a wrapper type strictly more expensive than `checked_div` for the
same guarantee, likely to go unused. Worth its own follow-up once (or if) an answer
to the narrowing question exists, rather than guessing one into this document.
Option D's cost doesn't seem worth its extra safety margin over C given C is
achievable; Option F is reasonable as a small, independent addition alongside B/C but
not sufficient alone; Option E (general recovery) stays RFC-0014's to decide, on its
own timeline.

**Overflow.** Ship Options C′ and D′ together (§7.3, §7.4) — `wrapping_*` and
`saturating_*` — before, or at least alongside, Option B′ (`checked_*`, §7.2). This
inverts the division recommendation's ordering, deliberately: for division, the
checked/`Perhaps` option was the cheap one and the type-safe wrapper was the
expensive, contingent one. For overflow, §5.2's asymmetry flips that — wrapping and
saturating are *already* the cheap, unconditionally type-safe options (no `Perhaps`,
no wrapper type, no narrowing story needed at all), while `checked_*` adds nothing
over them except a way to detect the condition happened, which `overflowing_*`
(Option E′, §7.5) already subsumes. Ship C′/D′ now; add B′/E′ only if a real use case
asks for the boolean/`Perhaps` shape specifically rather than a clamped or wrapped
value. Option F′ (contextual `checked`/`unchecked`, §7.6) is real, working precedent
elsewhere, but is language-feature-sized work, not stdlib-addition-sized — worth its
own follow-up RFC if pursued, not bundled into this one's recommendation. Option G′,
like its division counterpart, is a fine small addition alongside whichever of the
above ships, not a substitute for any of it.

---

## 9. Open Questions

1. **Does Metel's type checker have, or plan, any flow-sensitive narrowing
   mechanism** (occurrence typing, refinement after a guard) that Option C's
   ergonomic story (§6.3) could build on — or would this be new machinery invented
   specifically for `NonZero<T>`? Blocks a real cost estimate for that option. Does
   not affect overflow's options at all (§5.2) — this is a division-only question.
2. **Should `/` be overloaded for a `NonZero<T>` divisor, or should the panic-free
   path be a differently-named operation** (matching Zig's explicit
   `@divTrunc`/`@divExact` naming rather than Rust's overload-by-divisor-type)?
   Affects discoverability and whether a call site's panic-safety is legible without
   checking the divisor's declared type.
3. ~~The RFC-0007 D3 implementation divergence: fix the implementation to match the
   ratified debug-panics/release-wraps decision, or bring evidence back to amend D3
   itself?~~ **Resolved 2026-08-26 — D3 amended, not the implementation.** No
   debug/release build-mode concept exists for Metel programs at all; building one
   solely for this was judged not worth it. See §2.
4. **Does `Perhaps<NonZero<T>>::yolo()` for a compile-time-provable-nonzero literal
   need to exist as an ergonomic escape hatch**, or does §6.3's literal-inference
   proposal make that path unnecessary in practice? Only matters if literal inference
   doesn't fully land.
5. **Methods or operator sigils for overflow's alternatives (§7.3-§7.5)?** Rust's
   `wrapping_add`-style methods need only stdlib additions; Swift/Zig's `&+`/`+%`
   sigils need new grammar and parser work. Affects implementation cost directly —
   methods are far cheaper to ship, sigils are more visually distinct at the call
   site (a reviewer sees `&+` inline rather than having to notice a method name).
6. **Is Option F′ (contextual `checked`/`unchecked`, §7.6) worth pursuing at all, or
   is per-call-site `wrapping_*`/`checked_*` sufficient?** Given its cost is
   qualitatively different (type-checker/evaluator scoping, not a stdlib addition),
   this is closer to "does this deserve its own RFC" than "which option wins" —
   flagged rather than folded into §8's recommendation as a peer of the other
   options.

---

## References

- RFC-0007 (Compiler-Compatible Primitive Type System, `4-implemented`) — D3: the
  overflow-panics decision, amended 2026-08-26 (§2); its own "explicit `wrapping_add`
  / `checked_add`... deferred to the standard library RFC" line is what makes §5/§7
  of this document that deferred RFC.
- RFC-0013 (Integer Overflow Behaviour, `5-superseded` by RFC-0007) — the original,
  narrower overflow-only exploration; superseded, not resurrected here.
- RFC-0014 (Panic Recovery, `0-draft`) — the general, reactive sibling question;
  relationship stated precisely in §3.
- `reference/spec/runtime.md`, Panics section — the canonical, integrated statement
  that a panic is unrecoverable and terminates the process; the fact this RFC's
  stakes rest on.
- `reference/spec/types.md`, `spec.types.sized-numeric-types.dynamics-1` — the
  corrected (2026-08-26) normative overflow text §2 is grounded in.
- `reference/error-codes.md`, R0007 — documents both triggers (division/remainder by
  zero, overflow) as of the same correction.
- `metel-interpreter/src/evaluator/lvalue.rs::eval_binop` — the actual shipped
  behavior §1 is grounded in, checked directly against `develop`.
- `metel-frontend/stdlib/core.mtl` — confirms no `checked_*`/`wrapping_*`/
  `saturating_*`/`NonZero` surface exists on any numeric type today.

---

## Decision

**Outcome:** *(pending — intentionally.)* This document exists to put real
alternatives in front of a reviewer, not to pre-select one; §8's recommendation is
offered as a starting point for that review, not a claim of consensus. What's settled
by writing this down: the current behavior (§1) is accurately described; RFC-0007
D3's own question (does overflow panic) is closed and not reopened (§2); RFC-0014
(§3) is complementary to both halves of this document rather than overlapping;
division and overflow's *available answers* differ in a real, load-bearing way (§4.2
vs. §5.2) that shapes why their option sets (§6, §7) aren't symmetric. What isn't
settled: which of §6's options Metel adopts for division, and which of §7's it adopts
for overflow — independently; nothing here requires the same answer for both.
**Target:** *(blank until accepted.)*
