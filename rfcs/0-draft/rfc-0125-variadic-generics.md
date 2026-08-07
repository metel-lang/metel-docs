---
id: rfc-0125
title: "Variadic Generics"
date: '2026-07-25'
status: draft
target:
---

## Summary

A **type-parameter pack** — `<..Ts>` — so one impl can cover tuples of every arity:

```metel
extend<..Ts> (..Ts): Copy where all Ts: Copy;
```

This replaces the per-arity boilerplate RFC-0061 §6 deferred, and closes a gap three RFCs
already record: RFC-0061 §6 ("variadic generics: no design exists; deferred"), RFC-0061's
open question 1, and RFC-0096 §7, which "inherits that gap rather than" solving it.

**Bounds on a pack reuse RFC-0123's `all` quantifier rather than inventing a second one.**
`all Ts: Copy` is the same construct as `all R: Copy`, quantified over an ordered list of
types instead of a row's field types.

The RFC proposes a **staged** design, because the driving use case needs far less than the
general feature — see §3.

---

## Motivation

### Tuples satisfy nothing, and the workaround was rejected once already

A tuple satisfies no aspect today. `(i64, i64)` is not `Display`, not `Copy`, not `Eq`. The
diagnostic RFC-0061 §6 specifies is in the typechecker verbatim:

```
T0012: (i64, String) does not implement Display
       hint: tuple impls are not yet provided; use a named struct instead
```

Two ways out were identified in RFC-0061 §6, and **both were deferred rather than chosen**:

- **Per-arity impls** (Rust's approach — a macro emitting 12 copies), deferred "pending a
  decision on where boilerplate of this kind lives".
- **Variadic generics**, deferred because "no design exists".

This RFC supplies the missing design so the choice can be made on merits rather than on one
option being unspecified.

### It is now blocking concrete work

Issue #263 tracks moving `Copy` for tuples and fixed arrays out of the typechecker, where
#578 is about to hardcode them, and into `stdlib/`. Its tuple half is blocked on exactly
this: even once structural impl targets work (#581), *what to write* remains undecided. A
variadic impl is one line; per-arity is twelve near-identical blocks that must be kept in
sync across `Copy`, `Display`, `Eq`, `Clone`, `Send`, `Sync` — six aspects × twelve arities.

### The cost of not having it is paid repeatedly

RFC-0096's auto-impl rule for `Send`/`Sync` "applies to tuples as soon as per-arity blanket
impls land" (RFC-0061 §6). So does every future aspect. Each one either writes the
boilerplate again or leaves tuples out.

---

## 1. Prior art

The design space is unusually well explored, and the lesson is about *cost*, not
feasibility.

| language | mechanism | notes |
|---|---|---|
| **C++11** | `template<typename... Ts>`, `Ts...`, `sizeof...(Ts)` | Powerful; expansion contexts accreted ad hoc and are a byword for complexity |
| **Swift 5.9** (SE-0393) | `each T`, `repeat each T` | Recent and deliberately readable — spells expansion with keywords rather than punctuation |
| **D** | template tuple parameters, `T...` | Practical, long-standing, low ceremony |
| **TypeScript** | variadic tuple types `[...T]` | Type-level only; no value-level expansion needed |
| **Zig** | none — `comptime` + `anytype` + tuple iteration | Sidesteps the feature entirely (§4) |
| **Rust** | **none** — macros emitting per-arity impls | Discussed for a decade; never landed |

**Swift is the best syntactic model.** `each`/`repeat` reads at a glance where C++'s `...`
requires knowing which of several expansion contexts you are in.

### 1.1 Rust's decade of proposals, and what to take from it

Rust is the most instructive entry, because it has the strongest motivation of any language
here and *still has not shipped the feature* after discussing it since 2013. The lang team
maintains a design note aggregating the attempts:
<https://github.com/rust-lang/lang-team/blob/main/src/design_notes/variadic_generics.md>

Four named drafts, ordered by ambition:

| draft | shape | notable |
|---|---|---|
| **EddyB** | variadic types *are* tuples; `..` expansion; recursive head-tail destructuring | oldest and simplest — `type Tuple<..T> = T;` |
| **Cramertj** | C++-flavoured, with a `Tuple` trait carrying `AsRefs`/`AsMuts` helpers | `impl<Head, Tail> MyTrait for (Head, ...Tail) where Tail: Tuple {}` |
| **Fredpointzero** | adds ergonomics and imperative loops over packs, finer bound control | `struct Foo<(..T)> where ..(T: Debug)` |
| **Jules Bertholet** | most comprehensive: lifetime *and* const variadics, MxN→NxM transforms, homogeneous varargs | explicit iteration via `static for future in futures { … }` |

Their stated use cases are close to Metel's: multi-argument functions (`zip`, `join`),
**implementing traits for tuples**, homogeneous varargs, and *macro-free `derive`*.

**Five lessons, each of which changes something in this RFC.**

**1. The core shape is settled; only the ergonomics are contested.** All four drafts converge
on dots for packing and unpacking, acting on tuples to obtain variable arity. That is
§2.1–§2.2 exactly, so this RFC is adopting a decade-old consensus rather than inventing a
spelling. The note's own summary of what remains is "usability and 'extra' ergonomic
functionality still requires a lot of work" — not the core.

**2. The complexity gradient across the four drafts is why nothing shipped, and it is the
argument for §3's staging.** EddyB is minimal; Bertholet adds lifetime variadics, const
variadics and a new loop form. Each successive proposal is more capable and less likely to
land. Rust did not fail to design variadics — it designed them four times and could not
choose. **Staging is the mitigation**: ship the part with a caller today, defer the part
where the gradient starts.

**3. The tuple-layout blocker does not bite stage 1, and that determines the model.** The
lang team records a critical blocker: Rust gives no layout guarantees for tuple fields, which
limits *subsetting* operations on tuple references. That blocker is specific to head-tail
recursion — `(Head, ...Tail)`, the EddyB and Cramertj model — because taking `Tail` by
reference requires knowing where it starts. **This RFC therefore does not adopt head-tail
recursion.** `all Ts: A` quantifies over the whole pack without ever forming a sub-tuple, so
the question never arises. Metel would inherit the same blocker the moment it took the
recursive route, and it is avoidable by construction.

**4. Bertholet's `static for` is the right model for stage 2 — and it is comptime.** An
explicit compile-time loop over the pack is far more legible than C++'s implicit expansion
contexts, and it is *the same construct* as RFC-0092's comptime iteration. This reframes §4:
comptime is not only an alternative to variadic generics, it is plausibly the best
**implementation of stage 2**. The two converge instead of competing, which is worth knowing
before either is designed further.

**5. Metel's motivation for the "macro-free derive" use case is stronger than Rust's.** Rust
falls back on macros; **Metel has no macro system at all**, so the fallback available to
Rust — generate the boilerplate — is not available here (§5). What is a convenience for Rust
is closer to a necessity for Metel.

### 1.2 The `..` collision, checked rather than assumed

The lang team notes that `..` overlaps Rust's range syntax. **Metel has the same overlap** —
`range_op = { "..=" | ".." }` — so the concern transfers and was verified rather than waved
away.

It is nonetheless not a problem here, and the evidence is already in the language: `..`
**already** means "and a rest" in row bounds (RFC-0118) and row variables (RFC-0121), and
coexists with ranges today because the two occur in different grammatical positions —
`{ x: f64, .. }` in a bound, `0..10` in an expression. A pack in a generic parameter list is
separated the same way. So `..Ts` inherits an established meaning at no new cost, where in
Rust the same spelling would have been a fresh collision.

---

## 2. Proposal

### 2.1 Declaring a pack

`..Ts` in a generic parameter list declares **Ts** as a type-parameter pack — zero or more
types, ordered:

```metel
extend<..Ts> (..Ts): Copy where all Ts: Copy;
fun arity<..Ts>(t: (..Ts)) -> i64 { … }
```

A declaration may hold at most one pack, and it must come last. Both restrictions exist for
the same reason: with two packs, or a pack followed by an ordinary parameter, matching
`(i64, String, boolean)` against the parameter list is ambiguous.

The spelling deliberately matches `..R`, `{ x: f64, .. }` and `..Ts` across the corpus: `..`
consistently means "the rest, however many". It is **not** `record`-marked — a pack is a
list of types, not a record kind (see RFC-0118 §1 for why that distinction is kept sharp).

### 2.2 Expanding a pack into a tuple type

`(..Ts)` is the tuple type formed from the pack in order. For `Ts = [i64, String]` it is
`(i64, String)`. For the empty pack it is `()`, which is already Metel's unit type — the
degenerate case is therefore already meaningful, not a special case.

### 2.3 Bounds — reusing `all`

A bound over every member of a pack is written with RFC-0123's quantifier:

```metel
extend<..Ts> (..Ts): Copy    where all Ts: Copy;
extend<..Ts> (..Ts): Display where all Ts: Display { … }
```

`all Ts: A` holds when every type in the pack satisfies `A`, and holds **vacuously on the
empty pack** — matching `all R: A` on the empty row.

**This is a deliberate unification, not a coincidence of spelling.** RFC-0123's `all R: A`
quantifies an aspect over a row's field types; `all Ts: A` quantifies the same aspect over a
pack's members. The two differ only in what they range over — an unordered label→type map
versus an ordered list. Specifying one quantifier that ranges over both is cheaper than two,
and it means a reader who has learned `all` once has learned it everywhere.

**Consequence: this RFC depends on RFC-0123**, or at least on its quantifier being lifted
out. That dependency is real and should be settled before acceptance rather than discovered
during implementation.

### 2.4 What is *not* proposed here

No value-level packs (variadic *functions* — `print(a, b, c)`), no `sizeof...`, no pack
indexing, and no expansion in arbitrary type positions. Metel has no variadic function today
— `print<T: Display>(x: T)` takes exactly one argument — so there is no established need,
and each of those features is separable. §3 explains why the omission is load-bearing rather
than laziness.

---

## 3. Staging: the driving case needs much less than the feature

The aspects that need tuple impls split cleanly, and the split should drive scope:

| aspect | needs | why |
|---|---|---|
| `Copy`, `Send`, `Sync`, `Linear` | **bounds only** | marker aspects — no method bodies, so nothing must iterate the pack |
| `Display`, `Eq`, `Clone`, `Hash` | **bounds + body-level expansion** | must visit each element to format, compare or clone it |

**Stage 1 — packs, `(..Ts)`, and `all` bounds. No body expansion.**

This is enough for `extend<..Ts> (..Ts): Copy where all Ts: Copy;` and the same for
`Send`/`Sync`/`Linear` — which is precisely what #263 and RFC-0096 are blocked on. It needs
no way to *iterate* a pack, only to constrain it, and it is where the whole design's risk is
lowest.

**Stage 2 — expansion inside method bodies.**

Required for `Display` and friends, and where every language in §1 accumulated its
complexity: C++'s expansion contexts, Swift's `repeat each`. Deferring it lets stage 1 ship
against a real need without pre-committing to the hard half.

**The staging is the main proposal of this RFC.** A single all-at-once variadic design is
what "no design exists" has meant in practice for two years; a stage-1-only design is small
enough to actually land.

---

## 4. Considered: comptime instead

**RFC-0092 (Comptime Core) could substitute**, and this is the strongest alternative rather
than a straw man. Zig has no variadic generics: it passes a tuple and iterates it at
`comptime`, and that is sufficient for exactly the cases in §3's second row. RFC-0092 already
models `TypeInfo::Struct { row: Row }` and inspects it at compile time.

Arguments for comptime instead:

- No new type-system machinery — packs, expansion, coherence with packs, all avoided.
- It generalises past tuples to any shape reflection can see.
- RFC-0092 is already planned, so the cost may be shared.

Arguments against, and why this RFC exists anyway:

- **A comptime-generated impl is per concrete shape**, not one impl covering all of them.
  RFC-0123 §2 makes exactly this argument against comptime derive for rows: it "produces one
  impl per concrete record shape encountered, whereas this produces one impl covering all".
  The same argument transfers, and the difference matters most for a *bound* —
  `fun f<..Ts>(t: (..Ts)) where all Ts: Copy` is a constraint on callers, which no amount of
  generated impls expresses.
- **Comptime cannot help stage 1.** `Copy` on tuples is a bound question, not a codegen
  question.
- RFC-0092 is `0-draft` and larger than this RFC.

**Not mutually exclusive — and §1.1 lesson 4 sharpens this considerably.** Rust's most
comprehensive draft (Bertholet) spells body-level expansion as `static for`, an explicit
compile-time loop over the pack. That is not merely *similar* to comptime iteration; it is
the same construct under another name. So the likely end state is not "variadics or
comptime" but **stage 1 as type-system machinery plus comptime as stage 2's expansion
mechanism** — which would let Metel skip the ad-hoc expansion contexts C++ accreted, and
reuse a feature it is building anyway. Recorded as open question 4.

## 5. Considered: per-arity boilerplate (the Rust answer)

Write twelve impls per aspect, generated or by hand. Rust does this and it works.

**Against:** RFC-0061 §6 deferred it "pending a decision on where boilerplate of this kind
lives", and that decision has not become easier. Metel has no macro system, so the twelve
copies would be *written*, not generated, and would be duplicated per aspect —
`Copy`, `Send`, `Sync`, `Linear`, `Display`, `Eq`, `Clone` is seven × twelve = 84 blocks that
must stay consistent. It also caps arity arbitrarily, which C++ and Swift users do hit.

**For:** it needs no new language feature at all, and would unblock #263's tuple half
immediately once #581 lands.

**But note what makes Metel's position different from Rust's.** Rust chose this route and
sustains it because `macro_rules!` generates the twelve copies from one source of truth.
**Metel has no macro system**, so the same choice means twelve *hand-written, hand-maintained*
copies per aspect. The option Rust actually took is not the option available here — a point
worth making explicitly, since "Rust does per-arity impls" is otherwise a persuasive
one-liner.

**This is the real competitor to stage 1**, and the comparison is close enough that it should
be decided explicitly rather than by default.

---

## Open Questions

1. **Does this depend on RFC-0123, or should the `all` quantifier be lifted into its own
   RFC?** Both RFCs need it over different collections. Specifying it twice is the wrong
   answer; which document owns it is not obvious.
2. **What is the pack spelling — `..Ts`, or Swift's `each T`?** `..Ts` matches the corpus's
   existing use of `..` for "the rest", and all four Rust drafts converged on dots (§1.1
   lesson 1), so it is the well-trodden choice. `each`/`repeat` is more readable at the
   *expansion* site, which matters in stage 2 and not at all in stage 1. Deciding now risks
   choosing for stage 1 and regretting it in stage 2 — though if stage 2 turns out to be
   comptime `for` (§4), the expansion site may never need a sigil at all, which would settle
   this in favour of `..Ts`.
3. **How does a pack interact with coherence?** `extend<..Ts> (..Ts): Copy` is a blanket impl
   over an infinite family. RFC-0060's coherence pass and `coherence.rs`'s overlap check are
   built on canonicalised types with a finite head; a pack has none. This is the question most
   likely to make stage 1 harder than it looks, and it should be answered before acceptance.
4. **Stage 2 by expansion, or by comptime?** See §4. Deciding early would let stage 1's syntax
   be chosen to fit.
5. **Do fixed arrays want the same treatment?** `[T; N]` needs const generics (RFC-0053
   deferred them; no RFC exists), which is a *value* pack rather than a type pack. Related,
   deliberately out of scope, and tracked for arrays in #263.
6. **Arity limits.** Should a pack be bounded in practice (diagnostics, compile time), and
   does an unbounded pack interact badly with monomorphisation?

---

## References

- RFC-0061 (Structural Aspect Bounds), `4-implemented` — §6 defers tuple impls and names
  this RFC's absence as the reason; open question 1 restates it. Note §6's interim diagnostic
  is already implemented.
- RFC-0096 (Auto-Impl Aspects), `0-draft` — §7 "inherits that gap rather than" closing it;
  `Send`/`Sync` for tuples land as soon as this does.
- RFC-0123 (Field-Wise Row Constraints), `0-draft` — owns the `all` quantifier this reuses,
  and §2's argument against comptime derive transfers directly to §4 here.
- RFC-0092 (Comptime Core), `0-draft` — the principal alternative (§4).
- RFC-0118 (Row Bounds), `4-implemented` — establishes `..` as "the rest, however many", the
  spelling §2.1 inherits.
- RFC-0053 (Fixed-Size Arrays), `4-implemented` — defers const generics, the value-pack
  sibling question.
- Issues #263 (blocked on this for tuples), #581 (structural impl targets must work first),
  #578 (hardcodes tuple `Copy` in the meantime).
- **Rust lang-team design note on variadic generics** —
  <https://github.com/rust-lang/lang-team/blob/main/src/design_notes/variadic_generics.md> —
  aggregates the EddyB, Cramertj, Fredpointzero and Bertholet drafts, the tuple-layout
  blocker, and the use-case list. §1.1 draws five lessons from it.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
