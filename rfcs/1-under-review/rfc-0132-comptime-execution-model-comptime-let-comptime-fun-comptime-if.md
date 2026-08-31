---
id: rfc-0132
title: "Comptime Execution Model — comptime let, comptime fun, comptime if"
date: '2026-08-13'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/726'
target:
updated: '2026-08-31'
---

> **Updated 2026-08-31 — `comptime let` / `pub comptime let` and `var` in examples now
> use `:=`.** RFC-0136 (Walrus for Kept Bindings, `1-under-review`) makes `:=` the separator
> for every kept binding; `comptime let` is `let`-family, so it takes `:=` (type
> annotation stays `:`; compound ops like `*=`/`+=` stay `=`). RFC-0132 spells it that
> way from the start so it never needs a second migration — see §1. This RFC does not
> re-decide the separator.

> **New RFC, split out 2026-08-13 from RFC-0092 (Comptime Core).** RFC-0092 itself
> anticipated this split in its own Timing Recommendation — "the base `comptime let`
> mechanism (§0/§0a only, not `type`-as-value or reflection) could in principle ship
> ahead of the rest of this RFC — that's a sequencing question for whoever schedules the
> work, not resolved here." Nobody picked that up for 35 days, during which
> `metel-core#263` recorded `[T; N]: Copy` as still hardcoded in the typechecker,
> "blocked on something that does not exist anywhere in the corpus: const generics."
> This RFC is that sequencing question, answered: §0/§0a become their own independently
> schedulable RFC, and RFC-0092 keeps `type`-as-value, `typeinfo` reflection, and `emit`
> — the parts that genuinely still wait on derive (RFC-0093).
>
> **Why split rather than stage RFC-0092's target:** a separate number is independently
> trackable and independently schedulable. Staying one atomic unit is exactly what let
> the escape hatch RFC-0092 wrote for itself go unused — the same reason RFC-0012 was
> decomposed into RFC-0092/0093/0094/0095 rather than given a phased target
> (`public/rfcs/PROCESS.md`, and RFC-0092's own split note).
>
> **This RFC also closes a connection neither source document made** (RFC-0092 Open
> Question 9, added 2026-08-12; `reports/strategy/OBJECTIVES.md` Trigger 30): RFC-0053
> deferred `[T; N]`'s `N`-as-parameter to "a future RFC once a `const` declaration form
> exists," and RFC-0092 §1's generics-as-comptime-parameters argument already supplies
> the mechanism — it just never generalized past `type`-valued parameters or named
> RFC-0053's deferral as the thing it answers. §3 below does that generalization
> explicitly, which is what makes this RFC, rather than a hypothetical future const-
> generics RFC, the thing #263 is actually blocked on.
>
> **Correction, 2026-08-13, same day.** §1/§2/§4/§5 were moved verbatim from
> RFC-0092/RFC-0055 — prior, already-considered design. §3 is not: it was written from
> scratch while performing this split, and nobody has reviewed it. It was initially
> treated the same as the moved sections, including two GitHub issues (`#727`, `#728`)
> that scheduled milestoned implementation against it — both closed the same day, on
> direct pushback ("I dont want to rush the design of comptime, and the issues you
> created already commit to certain parts of the design"). §3 is marked below as a
> **proposal**, not a decision; see Open Question 7. `reports/strategy/OBJECTIVES.md`'s
> Review Log carries the full account.
>
> **Correction, ported from `internal/rfcs/` to `public/rfcs/` the same day.** The two
> RFC-0083 citations below originally read "#235," copied forward without checking it was
> a **Codeberg** issue number — the exact trap Open Question 5 below independently caught
> for a different pair of numbers in this same file, missed here on the first pass. The
> real GitHub issue is **#539**, fixed at the same time this document moved paths.

> **Status — under review (2026-08-23).** Design-settlement issue #726 has targeted v0.13.0 since 2026-08-13 -- real planned engagement predating this rule, applied retroactively

## Summary

The base compile-time execution model: `comptime let` bindings, `comptime fun` evaluation
and its restrictions, `comptime if`, `pub comptime let` for public value exports, and a
**proposed** mechanism for comptime-known non-type generic parameters (§3, unreviewed —
see Open Question 7) — filling the gap RFC-0053 called "const generics" and deferred.
Deliberately excludes `type`-as-first-class-value,
`typeinfo(T)` reflection, and `emit`, all of which stay in RFC-0092 and continue to wait
on RFC-0093's derive mechanism.

Nothing here requires new type-system machinery. `comptime` staging reuses the existing
evaluator; the one genuinely new checked layer is §3's arity substitution, and that is
narrower than general const-expression evaluation because `N` in `[T; N]` is already a
`u64` baked into `Type::SizedArray` today.

---

## Motivation

Three separate things are blocked on a mechanism that has been drafted but never
scheduled:

- **`metel-core#263` — `[T; N]: Copy` is hardcoded in the typechecker.** Its own words:
  "blocked on something that does not exist anywhere in the corpus: **const generics**.
  Only literal arities parse today (`extend<T: Copy> [T; 2]: Copy;` works; `[T; N]` does
  not), and enumerating arities is not viable for an unbounded `N`. RFC-0053 already
  recorded this — '`<const N: u64>` … left for a future RFC' — and no such RFC has been
  opened." That last clause is what this RFC makes false.
- **RFC-0124 Open Question 3** asks whether `[T; N]: Copy` needs const generics to leave
  the typechecker's hardcoded case. It does, and §3 is the answer, so RFC-0124's OQ3 can
  resolve by reference rather than by its own new design.
- **RFC-0083's public value exports** (superseded into RFC-0092 §0a) have been waiting on
  `comptime let` since 2026-07-12, and its tracking issue (#539) was closed
  unimplemented specifically to avoid building a bespoke restricted evaluator that would
  need reconciling against `comptime let` later. §2 unblocks it without RFC-0092's
  reflection half.

RFC-0092's Timing Recommendation notes this cost honestly — folding `pub let` in meant
public value exports "now wait on `comptime let` reaching a settled, implemented state —
this RFC's own target." Splitting §0 out is what stops that wait from also being a wait
on `typeinfo` and `emit`.

---

## 1. `comptime let`

*(Moved verbatim in substance from RFC-0092 §0, which folded it in from RFC-0055.)*

A binding whose initializer is evaluated at compile time:

```metel
comptime let MAX_CONNECTIONS: i64 := 1024;
comptime let BUFFER_SIZE: i64 := MAX_CONNECTIONS * 64;
```

The initializer separator is **`:=`**, not `=`. `comptime let` is `let`-family, so it
introduces a kept binding and falls under RFC-0136's normative invariant — a kept
binding uses `:=`, a one-shot label uses `=`. The type annotation stays `:` (ascription,
unchanged). This RFC does not re-decide the separator; it just spells `comptime let`
consistently with it from the start, so `comptime let` never has to be migrated a
second time (RFC-0136 §"The invariant"; metel-core#726, #804).

Motivating cases inherited from RFC-0055: derived constants (a buffer size computed from
a protocol limit, rather than duplicated or computed at runtime), and compile-time lookup
tables (`comptime let SIN_TABLE: [f64; 256] := ...`) — zero runtime cost, since the value
is fully computed before any generated code runs.

`comptime let` has **no mutable form**. There is no `comptime var`, at any visibility —
comptime bindings are not mutable regardless of whether they are exported.

## 2. `pub comptime let`: public value exports

*(Moved from RFC-0092 §0a, which resolved RFC-0083's circular dependency.)*

```metel
// config.mtl
pub comptime let MAX_CONNECTIONS: u64 := 1024;
pub comptime let DEFAULT_TIMEOUT_MS: u64 := 5000;

// importer
import config::MAX_CONNECTIONS;
fun accept(current: u64) -> boolean { current < MAX_CONNECTIONS }
```

- **Visibility composes with `comptime let` exactly as it already does with
  `struct`/`enum`/`fun`/`aspect`** (module spec, "Visibility") — no new visibility rule,
  just a new declaration kind `pub` can attach to.
- **Import/export syntax is unchanged.** `import config::MAX_CONNECTIONS;` and
  `export config::MAX_CONNECTIONS;` work exactly as for any other `pub` item.
- **Ordinary (non-`pub`, non-`comptime`) module-level `let`/`var` is untouched.** Their
  evaluation order remains unspecified — an implementation detail (evaluate
  top-to-bottom in declaration order; forward reference is a runtime error), exactly as
  RFC-0083 left it.

## 3. Comptime-known non-type generic parameters — RFC-0053's deferred const generics

> **Status: proposed, not decided (marked 2026-08-13) — see Open Question 7.** Everything
> below is a first-draft proposal, written while splitting this RFC out of RFC-0092, not
> a settled design. Unlike §1/§2/§4/§5, no prior RFC discussion produced it, and nobody
> other than this document's own drafting has weighed it against alternatives. Treat the
> spelling (§3.1), the admissible-instantiation rule (§3.2), and the bound-checking
> placement (§3.3) as this RFC's opening position for review, not as conclusions.

**New in this RFC.** RFC-0092 §1 argues that Metel's `<T>` generics are sugar over
comptime type parameters: `fun first<T>(arr: T[])` is
`fun first(comptime T: type, arr: T[])`, because "a compile-time-known parameter is just
an ordinary parameter, staged." Nothing in that argument depends on the comptime value
being a `type`. Generalizing it to other comptime-known value kinds is exactly what
RFC-0053 deferred:

```metel
// RFC-0053: "not valid in this RFC — N is not a type parameter"
fun reverse<T, comptime N: u64>(arr: [T; N]) -> [T; N] { ... }

// The blanket impl metel-core#263 cannot currently write:
extend<T: Copy, comptime N: u64> [T; N]: Copy;
```

### 3.1 Spelling

`comptime N: u64` inside the existing generic parameter list, not a separate `<const N>`
channel. RFC-0053 wrote its deferral as `<const N: u64>` (Rust's spelling); this RFC uses
`comptime` instead, because Metel is taking Zig's staging model rather than Rust's
separate-const-generics feature, and having both `comptime` and `const` as compile-time
qualifiers would be two words for one concept. **This is a deliberate divergence from
RFC-0053's own guessed spelling**, not an oversight — flagged here rather than silently
changed, per `PROCESS.md`'s rule that new syntax must not silently weaken or reinterpret
what is already written down.

### 3.2 What `N` may be instantiated with

A `u64`-typed comptime-known value: an integer literal (what parses today), a
`comptime let` constant (§1), or a `comptime fun` call (§4). This is the same admissible
set as any other comptime value — §3 introduces no separate notion of "const
expression," which is precisely the circularity RFC-0083 and RFC-0092 fell into and
RFC-0092 §0a resolved.

### 3.3 Bound checking stays where RFC-0061 put it

RFC-0092 §1's recommendation applies unchanged: bounds are checked at the generic
function's own definition against `typeinfo(T)`/impl lookup, **not** deferred to whichever
call site instantiates it — Zig's use-site duck typing is explicitly not adopted. For a
`comptime N: u64` parameter there is no aspect bound to check, so this is simpler than
the type-parameter case: `N`'s only constraint is that it is comptime-known and `u64`.

### 3.4 What this does not include

**No arithmetic in type position.** `[T; N]` is admitted; `[T; N + 1]`, `[T; N * 2]`, and
any other computed arity in a type are **out of scope for this RFC**. Admitting them
requires deciding type-level equality of arithmetic expressions (is `[T; N + 1]` the same
type as `[T; 1 + N]`? as `[T; M]` where `M = N + 1`?), which is where const generics gets
genuinely hard in every language that has it, and none of the three blocked items above
needs it. Deferred explicitly — and, per this RFC's own §Open Questions, deferred *to a
named question here*, not to "a future RFC," which is the pattern that produced this
situation in the first place.

---

## 4. `comptime fun`

*(Moved from RFC-0092 §0.)*

A function evaluable at compile time. The annotation means "the compiler *can* evaluate
this," not "this may only be called at compile time" — an ordinary runtime call site is
still legal:

```metel
comptime fun pow2(n: i64) -> i64 {
    var result := 1;
    var i := 0;
    while (i < n) { result *= 2; i += 1; }   // compound ops stay `=` (RFC-0136 §OQ1)
    result
}

comptime let PAGE_SIZE: i64 := pow2(12);   // 4096, computed at compile time
```

Restrictions, inherited from RFC-0055: no I/O builtins (`print`, `println`); no heap
allocation via runtime allocators; no calls to non-comptime functions; no recursion
beyond a compiler-enforced depth limit.

**Two of these restrictions are not fully specified, and both are load-bearing for this
RFC rather than for RFC-0092's half** — see Open Questions 1 and 2. This is the honest
cost of the split: `type`-as-value and reflection could wait on derive, but recursion
and comptime storage cannot wait on anything, because §1 cannot ship without them.

## 5. `comptime if`

*(Moved from RFC-0092 §0.)*

A conditional whose condition is a comptime-known value is resolved at compile time; the
untaken branch is never type-checked or emitted:

```metel
comptime let IS_64BIT: boolean := target_pointer_width() == 64;

fun word_size() -> i64 {
    comptime if (IS_64BIT) { 8 } else { 4 }
}
```

This is the mechanism RFC-0095 Open Question 4 speculates might subsume `#cfg`; RFC-0055
reached the same conclusion independently. Both converging is treated as confidence in
the answer, not as work to reconcile.

---

## Relationship to RFC-0092

| Concern | Lives in |
|---|---|
| `comptime let`, `pub comptime let`, `comptime fun`, `comptime if` | **this RFC** |
| Comptime-known non-type generic parameters (`comptime N: u64`) | **this RFC** (§3) |
| `type` as a first-class comptime value | RFC-0092 §1 |
| `<T>`-generics-as-comptime-sugar (the type-parameter half) | RFC-0092 §1 |
| `typeinfo(T)` reflection, row metadata | RFC-0092 §2 |
| `emit` (single-declaration form), coherence of emitted impls | RFC-0092 §3 |
| Generalized `emit`, comptime-callable parsing | RFC-0094 |

**RFC-0092 depends on this RFC**, not the reverse: `typeinfo` and `emit` are comptime
functions in this RFC's sense, with additional capabilities layered on. §3's parameter
generalization is deliberately placed here rather than in RFC-0092 §1 despite building on
§1's argument, because it needs nothing from `type`-as-value — only staging, which is
this RFC.

---

## Relationship to frontend monomorphization (metel-core#288)

*Added 2026-08-29. Cross-reference only — no design change here.*

§3's `comptime N: u64` parameters and ordinary `<T>` type parameters are **two axes of
the same instantiation problem**: to lower a `comptime N` function the compiler must know
the concrete `N` values it is called with, exactly as it must know the concrete types a
`<T>` function is called with. RFC-0092 §1 already frames `<T>` generics as
comptime-staging sugar, which makes this one mechanism, not two.

**metel-core#288 ("Frontend monomorphization for compiler-facing typed IR")** builds that
mechanism: a frontend pass that collects concrete generic instantiations across the whole
program (a worklist over concrete call sites) and produces concrete typed specializations
with stable identities, replacing the interpreter's current runtime generic-body
reconstruction. It is milestoned v0.20.1, one point release ahead of the compiler
foundation (metel-core#859) it feeds.

Consequences for this RFC:

- **#288's instantiation-collection pass must cover `comptime N: u64` parameters, not
  only type parameters** — otherwise §3 retrofits a second, parallel instantiation
  collector. Whichever lands first should be designed with the other's axis in mind.
- **#288 does not gate this RFC.** §3's *static* rules — the `comptime N` spelling
  (§3.1), the admissible-instantiation set (§3.2), definition-site bound checking (§3.3)
  — are independent of how instantiations are collected for lowering, and the tree-walk
  interpreter already instantiates generics per call (via runtime reconstruction) without
  #288. This is a "co-design the shared pass" note, not a dependency edge.
- The **no-arithmetic-in-type-position** deferral (§3.4) keeps the `comptime N` axis a
  finite set of concrete `u64` values per function, i.e. the same shape as the type-param
  axis — which is what makes one collector viable. Admitting `[T; N + 1]` later would
  reopen this.

---

## Open Questions

1. **Recursion and termination for `comptime fun`** *(inherited from RFC-0092 OQ6 /
   RFC-0055 OQ1 — now blocking, where it previously was not).* Recursive comptime
   functions with a compiler-enforced depth limit (Zig's approach), or forbid comptime
   recursion entirely? **This must be answered to ship §4**, and therefore §1. It was
   answerable-later while it sat inside RFC-0092 alongside reflection; it is not
   answerable-later here.
2. **Comptime and allocation** *(inherited from RFC-0092 OQ7 / RFC-0055 OQ2 — also now
   blocking).* Can comptime functions allocate? RFC-0092 §0 asserted comptime needs "its
   own scratch storage, distinct from `@a T`'s runtime allocators" without specifying what
   that storage is or how it is bounded. A `comptime let SIN_TABLE: [f64; 256]` in §1
   already constructs a 256-element array at compile time, so "no allocation at all" is
   not obviously viable — this needs a real answer, not an inherited footnote.

   **Sharpened 2026-08-13 — there are two distinct allocation shapes here, not one, and
   only the easier one is currently visible in this question.** `[f64; 256]` is a
   *known-arity* buffer: its size is in its type, so a comptime evaluator can allocate it
   from a bump/scratch region with no growth logic. A comptime **`String`** is the second
   case, and it arrives for free whether or not anyone designs it:

   ```metel
   comptime let VERSION: String := "0.13.0";
   comptime let BANNER: String := "metel v${VERSION}";   // interpolation, at comptime
   ```

   This needs **no new syntax and no new RFC** — RFC-0010 lowers interpolation to `+` and
   `.to_string()` before typechecking, both ordinary operations a comptime evaluator can
   run when the operands are comptime-known, so comptime interpolation falls out of §1 plus
   RFC-0010 the moment `comptime let` accepts a `String`. But a `String` is unbounded and
   grows by concatenation, which is a materially different storage requirement from a
   fixed-arity array. **The consequence to state explicitly: if this question answers "no
   heap-shaped allocation in comptime, only fixed-size scratch values," comptime strings
   die with it** — and with them comptime interpolation, `comptime let` string constants,
   and any `pub comptime let` exporting a computed message (§2's own
   `DEFAULT_TIMEOUT_MS`-style examples are numeric, but nothing restricts public value
   exports to numbers). That is a real product decision hiding inside what reads as an
   implementation detail; it should be made deliberately rather than discovered when a
   `comptime let` over a `String` is first attempted. Found while checking whether
   interpolation should be restricted to comptime values — see
   `reports/substructural-types/algebraic-effects.md` Open Question 7, which rules that
   restriction out from the other direction (0 of 80 corpus interpolation sites are
   comptime-known) while surfacing this case as the genuinely useful additive version.
3. **Comptime error messages** *(inherited from RFC-0092 OQ8 / RFC-0055 OQ5).* A failing
   comptime computation must report the original call site, not the internals of whatever
   comptime function was evaluating. Less blocking than 1 and 2 — a merely-poor diagnostic
   does not make the feature unshippable — but it is the thing most likely to make
   comptime unpleasant in practice.
4. **Computed arities** (§3.4). Is `[T; N + 1]` ever wanted, and if so what decides
   type-level equality of arity expressions? Named here rather than deferred to an unnamed
   future RFC, deliberately — see §3.4.
5. **Does `extend<T: Copy, comptime N: u64> [T; N]: Copy;` actually satisfy
   `metel-core#263`,** or does the hardcoded arm also depend on RFC-0061's structural-impl
   machinery? #263 lists both a const-generics dependency *and* a structural-impl
   dependency, but assigns the latter to the **tuple** half specifically; this question is
   whether the **array** half is genuinely unblocked by this RFC alone.

   **Checked 2026-08-13 — the structural-impl blocker is already gone, and the answer
   looks like yes.** RFC-0061's own qualified-status blockquote and #263 both cite this
   dependency as "metel-core#296 / #353," which are **Codeberg** issue numbers predating
   the GitHub migration — a stale-citation trap, since GitHub's #296 and #353 are
   unrelated closed issues from v0.4/v0.1. The real ones are **GitHub #581** (concrete
   structural targets raising an internal error — closed, v0.12.0) and **GitHub #239**
   (generic tuple/record structural impls accepted then silently inert — closed, v0.12.1).
   Both are fixed. #239's own measured table records `extend<T> T[]: Area` as
   *declaration: accepted / method call: works / bound satisfaction: works*, and #263
   separately measured `extend<T: Copy> [T; 2]: Copy;` as working with a literal arity —
   so sized-array targets already register and dispatch. What is missing is only
   arity-as-a-parameter, which is exactly §3. **Still worth confirming against the built
   interpreter before acceptance rather than inferring it from two issue reports**, but
   the remaining risk is much narrower than "structural impls don't work."

   *Method note, worth carrying:* both stale citations were copied forward into this RFC
   from RFC-0061's blockquote without checking that the numbers were GitHub's. That is the
   same failure `PROCESS.md` records for RFC-0067 ("a description of its own staleness
   that was itself stale") and the same class `metel-core#725` proposes tooling for. Any
   `#NNN` in a pre-migration document should be treated as a Codeberg number until
   verified.
6. **Sequencing against RFC-0124.** RFC-0124 (Sequence Types, `0-draft`) may change what
   `[T; N]` and `T[]` *are*. Its OQ3 is answered by §3, but if RFC-0124 revisits
   `[T; N]`'s role more broadly, §3's parameter mechanism should follow that decision
   rather than precede it — the same warning #263 already gives ("any array work here
   should follow that decision rather than precede it, or it will be written twice").
7. **Is §3 as designed even the right design, or just the first one written down?**
   *(Added 2026-08-13, on direct pushback that this RFC's own scheduling was committing
   to unreviewed design.)* §3 answers a real need (RFC-0053's deferred const generics),
   but its specific answers have not been tested against alternatives by anyone but this
   document's own drafting:
   - **§3.1's spelling** (`comptime N: u64` vs. RFC-0053's guessed `<const N: u64>`, vs.
     some third form) — argued from "one word for one concept," but not weighed against,
     e.g., whether reusing `comptime` for a generic-parameter position reads clearly at
     a call site, or whether a form closer to existing `<T>` sugar is preferable.
   - **§3.2's admissible-instantiation set** — asserted to need "no separate notion of
     const expression," but this is inherited reasoning from §0a's unrelated circularity,
     not independently checked against §3's actual shape.
   - **§3.3's bound-checking placement** — asserted "simpler than the type-parameter
     case" without a written-out example of what goes wrong if it isn't.
   - **§3.4's deferral boundary** (no computed arities) — plausible, but exactly the kind
     of scope line that looks obviously right until someone needs `[T; N + 1]` for a
     concrete case nobody has tried to write yet.

   None of these is flagged because it's suspected wrong — they may all survive review
   unchanged. They're flagged because **this RFC is still `0-draft`, and §3 has had zero
   readers other than its own author.** This question does not resolve by more solo
   drafting; it resolves when RFC-0132 goes through actual review and §3 either survives
   scrutiny or changes. Implementation should not be scheduled against §3 until then —
   see the header correction and `metel-core#727`/`#728` (closed 2026-08-13, re-filed
   only once this RFC reaches `2-accepted`).

---

## References

- **RFC-0092 (Comptime Core), `0-draft`** — this RFC is split from its §0/§0a; RFC-0092
  retains `type`-as-value, `typeinfo`, and `emit`, and depends on this RFC. Its Open
  Question 9 (added 2026-08-12) is what identified §3's connection.
- **RFC-0053 (Fixed-Size Array Type), `4-implemented`** — deferred `N`-as-parameter to "a
  future RFC once a `const` declaration form exists"; §3 is that mechanism, spelled
  `comptime N: u64` rather than RFC-0053's guessed `<const N: u64>` (§3.1).
- **RFC-0124 (Sequence Types), `0-draft`** — its Open Question 3 is answered by §3; see
  Open Question 6 for the sequencing dependency in the other direction.
- **RFC-0055 (Comptime), `5-superseded`** — original source of §1/§4/§5's execution model
  and Open Questions 1-3, via RFC-0092.
- **RFC-0083 (Public Value Exports), `5-superseded`** — §2 is its content; its tracking
  issue (#539) was closed unimplemented pending exactly this mechanism.
- **RFC-0061 (Structural Aspect Bounds), `4-implemented`** — §3.3's bound-checking
  discipline; also relevant to Open Question 5.
- **RFC-0093 (Derive Registration) / RFC-0094 (Comptime Metaprogramming)** — depend on
  RFC-0092's half, not on this one directly.
- `metel-core#263` — the hardcoded `[T; N]: Copy` arm this RFC's §3 exists to retire.
- `metel-core#288` (Frontend monomorphization, v0.20.1) — the instantiation-collection
  pass §3's `comptime N` axis shares with type-parameter monomorphization; see
  "Relationship to frontend monomorphization" above. Co-design, not a dependency edge.
- `reports/strategy/OBJECTIVES.md` Trigger 30 — the strategy-level record of why this
  split is happening now rather than whenever RFC-0092 was next visited.
- Prior art: Zig `comptime` (staging model, `comptime` parameters); Rust const generics
  (`<const N: usize>` — the feature §3 provides, deliberately not the spelling).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
