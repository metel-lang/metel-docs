---
id: rfc-0132
title: "Comptime Execution Model — comptime let, comptime fun, comptime if"
date: '2026-08-13'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/726'
updated: '2026-10-01'
---

> **§1.1 and §3.5 added, 2026-10-01 — a general "comptime value" rule, and three gaps
> closed in the already-ratified §3.1–§3.4.** Checked directly against the built
> interpreter: §3's own flagship worked example (`fun reverse<T, comptime N: u64>(arr:
> [T; N])`) does not parse under the current grammar, and neither the resolved `Type`
> enum nor the inference-phase `InferType` enum has ever had anywhere for an unresolved
> array size to live. §1.1 names the general "comptime-known expression" rule §3.2 was
> always an unstated restriction of. §3.5 fixes the grammar and representation (symmetric
> with how `T` itself already works — a unification variable, not new machinery) and
> settles `#726`'s "allowed type positions" acceptance criterion by confirming `comptime
> N` on `struct`/`enum` declarations, not only `fun`/`extend`. None of this reopens
> anything §3.1–§3.4 already ratified 2026-09-27; it fills in what ratifying the spelling
> never checked could be written.

> **Updated 2026-08-31 — `comptime let` / `pub comptime let` and `var` in examples now
> use `:=`.** RFC-0136 (Walrus for Kept Bindings, `4-implemented`) makes `:=` the separator
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
>
> **§3 settled for #726's narrow slice, 2026-09-27 — this is not the whole RFC reaching
> `2-accepted`.** `#726` scopes to "the smallest RFC-0132 slice needed for comptime-known
> non-type parameters and fixed-size array types," explicitly excluding "general user
> comptime allocation... and generalized metaprogramming" — i.e. §3 and its relation to
> `#1291`/`#263`, not §1/§2/§4/§5's full execution model. Within that scope: §3.1
> (spelling), §3.3 (bound-checking placement) and §3.4 (no computed arities) are ratified
> as originally proposed; §3.2 (admissible instantiation set) is **narrowed** — `N` may be
> a literal or a `comptime let` constant, but *not* a `comptime fun` call, for now (see §3
> below). That narrowing is what lets OQ1/OQ2 (recursion, allocation — both about
> `comptime fun`) stay genuinely open without blocking this slice: a `comptime let`
> constant of `u64` type is pure constant-folding and needs neither. OQ1/OQ2/OQ3 remain
> open for §1/§2/§4/§5's broader scope, which this pass does not settle and does not
> claim to. See Open Questions below for the full account, including OQ5 and OQ6.

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

### 1.1 What counts as a comptime value

*(New, 2026-10-01 — closes a gap used implicitly throughout §1/§3/§5 but never defined.
"Comptime-known" is used as if it already names a closed, checkable set — in this
section's own opening sentence, in §3's "comptime-known non-type generic parameters,"
in §5's "a conditional whose condition is a comptime-known value" — and nowhere does it.
Only a comptime value may initialize a comptime binding; this is the rule that makes
that true.)*

An expression is **comptime-known** exactly when it is one of:

1. A literal (`i64`/`u64`/…, `f32`/`f64`, `String`, `boolean`, `Char`).
2. A reference to an in-scope `comptime let` or `pub comptime let` binding (§1, §2).
3. A reference to an in-scope `comptime N: u64`-style generic parameter (§3), within the
   body of the `fun`/`struct`/`enum`/`extend` that declares it — comptime-known even
   though its concrete value is not fixed until that declaration is instantiated.
4. An operator, field-access, or index expression, all of whose operands are
   comptime-known.
5. *(Full RFC scope, not `#726`'s slice — see below.)* A `comptime fun` call (§4), all of
   whose arguments are comptime-known.

And explicitly **not** comptime-known:

- A reference to an ordinary (non-`comptime`) `let`/`var` binding — **regardless of
  whether its own initializer happens to be a literal or otherwise statically
  computable.** Comptime-ness is a property of the binding's declared kind, checked by
  its keyword, not inferred by constant-propagation over arbitrary runtime code. This is
  the same "no separate notion of const expression" principle §3.2 already relies on for
  its own narrower rule — stated here once, generally, instead of re-derived per
  position.
- A reference to an ordinary (non-`comptime`) function parameter, even inside a function
  that also has `comptime` parameters — consistent with §3.3's definition-site checking:
  the body is checked once, independent of what any call site happens to supply.

**`comptime let`'s initializer (§1, above) must be comptime-known.** `comptime if`'s
condition (§5) is the same requirement under a different name.

**For `#726`'s narrow slice specifically** (§1/§2/§3 only — not §4), rule 5 is inert: no
`comptime fun` exists yet to supply it. The practically available comptime-known
expressions for this slice are rules 1–4 — literals, `comptime let` references, in-scope
`comptime N` references, and arithmetic/field/index expressions built from those. Rule 5
is stated for completeness, and because §4's own example
(`comptime let PAGE_SIZE: i64 := pow2(12);`) already assumes it; writing the full rule
and noting which part isn't reachable yet costs this slice nothing, where a slice-local
rule would need restating once §4 ships.

**§3.2 is a restriction stated against this rule, not an independent one** — see the note
added there.

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

> **Status: ratified for #726's narrow slice, 2026-09-27 — see Open Question 7.** Reviewed
> against alternatives for the first time since the 2026-08-13 split. §3.1 (spelling),
> §3.3 (bound-checking placement) and §3.4 (deferral boundary) survive unchanged from the
> original proposal, each with the reasoning that was previously missing now written out.
> §3.2 (admissible-instantiation rule) is narrowed, not ratified as originally written —
> see §3.2 below. This settles §3 for the purpose `#726` actually needs (comptime-known
> array sizes for `#1291`/`#263`); it is not a claim that RFC-0132 as a whole is ready for
> `2-accepted`, since §1/§2/§4/§5 and Open Questions 1–3 remain outside this review's
> scope.

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

### 3.1 Spelling, ratified 2026-09-27

`comptime N: u64` inside the existing generic parameter list, not a separate `<const N>`
channel. RFC-0053 wrote its deferral as `<const N: u64>` (Rust's spelling); this RFC uses
`comptime` instead, because Metel is taking Zig's staging model rather than Rust's
separate-const-generics feature, and having both `comptime` and `const` as compile-time
qualifiers would be two words for one concept. **This is a deliberate divergence from
RFC-0053's own guessed spelling**, not an oversight — flagged here rather than silently
changed, per `PROCESS.md`'s rule that new syntax must not silently weaken or reinterpret
what is already written down.

**Weighed against the alternative OQ7 asked for.** A separate `<const N: u64>` channel
(Rust's own spelling, and RFC-0053's guess) would read clearly at a call site too — the
question is whether Metel wants a second compile-time-qualifier vocabulary alongside
`comptime let`/`comptime fun`/`comptime if`, all three already fixed by §1/§4/§5. It
doesn't: every other staged construct in this RFC uses `comptime`, so a lone `const` for
generic parameters would be the one place a reader has to remember a different word means
the same thing. No alternative surfaced that beats "reuse the vocabulary the rest of the
RFC already commits to." Ratified as proposed.

### 3.2 What `N` may be instantiated with, narrowed 2026-09-27

> **Connected to a general rule, 2026-10-01.** §1.1 (new) names the general
> "comptime-known expression" definition this section was always a restriction of,
> without saying so. Re-read against it: this section admits §1.1's rules 1–2 (literal,
> `comptime let` reference) and rule 4 (arithmetic/field/index over those), withholding
> only rule 5 (`comptime fun` calls) — for exactly the reason given below. Nothing in
> this section's own ratified content changes; §1.1 just gives the restriction a general
> rule to be a restriction *of*, instead of re-deriving "no separate notion of const
> expression" from scratch here.

**For `#726`'s slice: a `u64`-typed integer literal (what parses today), or a
`comptime let` constant (§1).** `comptime fun` calls (§4) are **excluded** from this
slice's admissible set — the original proposal included them, treating `N`'s admissible
set as identical to any other comptime value's, on the grounds that §3 introduces no
separate notion of "const expression." That reasoning still holds for *whether* a
`comptime fun` result should eventually be admissible; it says nothing about *when*, and
admitting it now would mean this slice inherits Open Questions 1 (recursion) and 2
(allocation) — both genuinely unresolved, both scoped to `comptime fun` specifically, and
both explicitly excluded from `#726`'s own acceptance criteria ("general user comptime
allocation... generalized metaprogramming").

**Why the narrower set is sufficient and doesn't need those questions answered.** A
`comptime let N: u64 := EXPR;` where `EXPR` is arithmetic over `u64` literals and other
`comptime let` constants is pure constant-folding — no recursion (there is no function
call), no allocation (a `u64` is a fixed-width scalar). Neither blocking question is
reachable through this path. Every actual driver — `#263`'s `[T; N]: Copy`, `#1291`'s
`T[N]` syntax — needs `N` to be a compile-time constant, and nothing in either issue
needs that constant to be the result of an arbitrary computation.

**Not a permanent restriction — strictly wideneable later.** Admitting `comptime fun`
calls as an `N`-source is additive: it accepts more programs than the literal/`comptime
let` set does, so extending it once OQ1/OQ2 are answered (as part of §4's own broader
settlement) cannot invalidate anything accepted under this narrower rule. Nothing here
needs to be written twice.

### 3.3 Bound checking stays where RFC-0061 put it, ratified 2026-09-27

RFC-0092 §1's recommendation applies unchanged: bounds are checked at the generic
function's own definition against `typeinfo(T)`/impl lookup, **not** deferred to whichever
call site instantiates it — Zig's use-site duck typing is explicitly not adopted. For a
`comptime N: u64` parameter there is no aspect bound to check, so this is simpler than
the type-parameter case: `N`'s only constraint is that it is comptime-known and `u64`.

**The worked example OQ7 asked for, showing what breaks under the alternative.**

```metel
fun reverse<T, comptime N: u64>(arr: [T; N]) -> [T; N] {
    var out: [T; N] = arr;
    var i: u64 := 0;
    while (i < N) { out[i] = arr[N - 1 - i]; i += 1; }
    out
}
```

Typechecking `reverse`'s own body needs to know, at the definition site, that `N` is a
`u64` — not any particular value of it — to accept `arr[N - 1 - i]` as a well-typed index
expression at all. Under use-site duck typing, the body would not be checked until a call
site supplied a concrete `N`, which means `reverse` itself has no checked type until
someone calls it — exactly the property definition-site checking exists to guarantee for
ordinary `<T>` generics (a generic function is checked once, not once per call site), and
losing it for `comptime N` while keeping it for `T` would make the two parameter kinds
behave inconsistently within the same parameter list. Definition-site checking is the only
choice that keeps `comptime N` and `T` uniform.

### 3.4 What this does not include

**No arithmetic in type position.** `[T; N]` is admitted; `[T; N + 1]`, `[T; N * 2]`, and
any other computed arity in a type are **out of scope for this RFC**. Admitting them
requires deciding type-level equality of arithmetic expressions (is `[T; N + 1]` the same
type as `[T; 1 + N]`? as `[T; M]` where `M = N + 1`?), which is where const generics gets
genuinely hard in every language that has it, and none of the three blocked items above
needs it. Deferred explicitly — and, per this RFC's own §Open Questions, deferred *to a
named question here*, not to "a future RFC," which is the pattern that produced this
situation in the first place.

**Confirmed 2026-09-27.** Checked against both drivers this slice exists for: `#263`'s
blanket `Copy` impl (`extend<T: Copy, comptime N: u64> [T; N]: Copy;`) and `#1291`'s `T[N]`
syntax amendment both need only a bare `comptime N` parameter, never a computed arity in a
type. The boundary drawn here doesn't need to move for either. Stays open (Open Question
4) rather than resolved, exactly as originally scoped — this confirms the line is drawn in
the right place, not that the question behind it is answered.

> **Stale cross-reference, caught 2026-10-01.** This section (written 2026-08-13) and the
> paragraph above both describe `#1291` as a "`T[N]` syntax amendment" — its original
> framing, moving the *fixed*-size array to postfix. `#1291` actually shipped as
> RFC-0171, which supersedes that direction: the **dynamic** array moves prefix (`T[]` →
> `[T]`), and `[T; N]` is untouched, exactly as this paragraph's own "none of the three
> blocked items above needs \[a computed arity\]" conclusion already assumed. The
> conclusion stands; only the syntax-amendment description was stale. RFC-0171 itself
> (`4-implemented`, 2026-10-01) is the authoritative account.

### 3.5 Grammar, representation, and declaration scope

*(New, 2026-10-01 — closes gaps found checking §3 against the actual grammar and type
representation, and against `#726`'s own "allowed type positions" acceptance criterion.
All three gaps sit inside the already-ratified §3.1–§3.4; none of them reopens anything
ratified 2026-09-27.)*

#### 3.5a Grammar: the array-size slot must admit an identifier, not only a literal

**Checked directly, 2026-10-01, against `metel-frontend/src/grammar.pest` (post-RFC-0171).**
`bracket_array_type = { "[" ~ type_expr ~ (";" ~ decimal_int)? ~ "]" }` — the slot after
`;` accepts only `decimal_int`, a literal. **§3's own flagship worked example (§3.3,
`reverse`) does not parse today:** `N` is an identifier there, not a `decimal_int`. This
was true before RFC-0171 too — the old `sized_array_type` production had the identical
restriction. §3.1–§3.4 were ratified without anyone checking that the spelling they
ratified is writable.

**Fix:** a new production for the array-size slot, admitting a bare identifier alongside
the literal:

```
array_size = { decimal_int | ident }
bracket_array_type = { "[" ~ type_expr ~ (";" ~ array_size)? ~ "]" }
```

An identifier here is resolved at typecheck time against in-scope `comptime N: u64`
parameters — never evaluated as a general expression. This is deliberately narrower than
"any comptime-known expression" (§1.1): `[T; N + 1]` stays out of scope, unchanged from
§3.4's own deferral above. The grammar now *parses* a name in that slot; typechecking
still rejects anything there besides a literal or a bare reference to an in-scope
`comptime N` parameter.

#### 3.5b Representation: `N` is resolved the same way `T` is — a unification variable, not a type-level slot

**Checked directly against `metel-frontend/src/data/types/mod.rs` and
`.../pipeline/type_checking/type_engine/mod.rs`, 2026-10-01.** Neither the resolved
`Type` enum nor the inference-phase `InferType` enum has ever had a slot for
"unresolved" anything. `T`'s own unresolved occurrence is not a permanent tag on a type —
it is `InferType::Var(TypeVar)`, a transient **unification variable** (`TypeVar` is a bare
`struct TypeVar(pub u32)`), resolved by unifying against the concrete call-site argument.
`Type::SizedArray(Box<Type>, u64)` and `InferType::SizedArray(Box<InferType>, u64)` are
*both* a bare `u64` today, because arrays could only ever be written with literal
arities — there has never been anywhere, at any layer, for an unresolved size to live.

**The fix mirrors `TypeVar` exactly, at the same layer `T` is resolved at.** A `ConstVar`
(identical shape — a fresh opaque id per unresolved `comptime` value, resolved by
unification against the concrete call-site value), used only in `InferType`:

```rust
enum ArraySize {
    Literal(u64),
    Var(ConstVar),
}
// InferType::SizedArray(Box<InferType>, ArraySize)   -- was: (Box<InferType>, u64)
```

**`Type::SizedArray` is untouched.** By the time anything becomes a resolved `Type`,
every generic parameter — `T` and `N` alike — is already substituted via the existing
per-call-site reconstruction (`metel-frontend/src/pipeline/type_checking/construction/
mod.rs`'s generic-body construction); a resolved `Type::SizedArray` has always been able
to assume a concrete arity and keeps being able to. This is smaller and more consistent
than baking an `ArraySize` variant into `Type` itself would be — that would give `N` more
permanent machinery than `T` has ever needed.

**What this settles about `N`'s own nature.** `comptime N: u64` is a genuine generic
parameter, in the same sense `T` is and via the identical mechanism — a fresh unification
variable, declared in the same `generic_params` list, resolved per call/construction
site, checked at definition site per §3.3 — not a comptime value admitted into a type
position as a special-cased exception. What *is* deliberately restricted is the **syntax
position** it may appear in: `T` is legal almost anywhere `type_expr` is, while `N`, for
`#726`'s slice, is legal only in `[T; N]`'s size slot (§3.5a), and only as a bare
reference there (§3.4) — a scope boundary, not a difference in mechanism.

#### 3.5c Declaration scope: `comptime N` on `struct`/`enum`, not only `fun`/`extend`

**Checked directly against `metel-frontend/src/grammar.pest`, 2026-10-01.**
`generic_params` is one shared production across `fun_decl`, `struct_decl`, `enum_decl`,
`extend_impl_block`, `aspect_decl`, and `type_alias`. Once `comptime N: u64` is added as a
`generic_param` alternative (§3.1), it becomes available **everywhere** `<...>` appears —
struct and enum declarations included — whether or not this RFC says anything about it;
the production is shared, not per-declaration-kind. `#726`'s own acceptance criteria name
"allowed type positions" (plural); this is the part of that criterion §3.1–§3.4 left
unaddressed.

**In scope, confirmed against `#726`'s own boundary.** The obvious case:

```metel
struct FixedBuffer<comptime N: u64> {
    data: [u8; N],
}

extend<comptime N: u64> FixedBuffer<N> {
    fun len(&self) -> u64 { N }
}
```

— is squarely inside §3.4's existing deferral boundary: a bare `N` in the field's
array-size slot, no arithmetic. Definition-site bound checking (§3.3) generalizes without
change: "is `N` comptime-known and `u64`" doesn't depend on whether the enclosing
declaration is a `fun`, a `struct`, or an `enum`. No new rule is needed beyond stating
explicitly that struct/enum declarations are included — the grammar already includes them
for free, and nothing about §3.2's instantiation rule or §3.3's checking discipline is
`fun`-specific.

**Not addressed here: a struct/enum's own field types computing a new arity from `N`.**
`struct Matrix<comptime Rows: u64, comptime Cols: u64> { data: [f64; Rows * Cols] }` needs
arithmetic in type position (`Rows * Cols`), which stays out of scope per §3.4 unchanged —
this section extends *where* a bare `comptime N` may be declared and referenced, not
*what* may be computed from it.

**Validation note, same posture as Open Question 5.** §3.5a/b's grammar and
representation sketches, and §3.5c's struct/enum scope, are sufficient for design
purposes — confirming they compile and integrate cleanly with the existing
`construct_generic_body`/unification machinery is empirical validation at implementation
time, not a design decision left open, exactly as Open Question 5 already treats the
equivalent step for §3 as a whole.

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

### 4.1 Closures and first-class function values at comptime

*(Design intent relocated here from RFC-0153's Non-Goals, 2026-09-01. The v0.13.0 closure
cluster — RFC-0134 / RFC-0152 / RFC-0153 — specifies closures for the runtime language
only; how they behave under comptime evaluation is this RFC's concern and is not
spec-integrated until this RFC is.)*

A closure literal evaluated inside a `comptime fun`, or in a `comptime let` initializer, is
an ordinary comptime value. The comptime evaluator is the same interpreter, so a closure
created at compile time behaves exactly as one created at runtime; the three `Type::Fun`
axes the closure cluster adds all carry over unchanged:

- **`once` consumption** — calling a `once` closure at comptime consumes it at the call
  expression; a second comptime call is the ordinary moved-value error.
- **`mut` write-back** — a `comptime` `[n] mut () -> i64` counter advances between comptime
  calls, its environment mutated in place, exactly as at runtime (RFC-0153 §1a).
- **the reentrancy guard** — a `mutating` call reached from inside a still-live one
  (RFC-0153 §3a) is rejected. At comptime it surfaces as a compile-time evaluation
  diagnostic with a source span — the comptime analogue of the runtime abort, not an
  evaluator panic and not unguarded recursion — and composes with the recursion-depth
  limit (Open Question 1) rather than replacing it.

There is no separate `const` / comptime closure model and no relaxation of RFC-0153 §3's
exclusive-place rule. A closure that escapes comptime into a runtime value — returned from
a `comptime fun` invoked at a runtime call site, or bound by a non-`comptime` `let` — is
subject to the ordinary runtime rules from that point on. Closures capturing runtime
allocators or performing I/O remain barred by §4's inherited restrictions regardless of
their axes.

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
reconstruction. It is milestoned v0.17.0 (the compiler-ready freeze), ahead of the compiler
expansion (metel-core#859, v0.24.0) it feeds.

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
   RFC-0055 OQ1 — now blocking, where it previously was not).*
   **Out of scope for `#726`'s slice, 2026-09-27 — still genuinely open for §1/§4's
   broader scope.** §3.2's narrowing (above) excludes `comptime fun` calls as an
   `N`-source specifically so this question doesn't have to be answered before `#726`'s
   slice can settle; it remains a real blocker for shipping §4 itself, unchanged. Recursive
   comptime functions with a compiler-enforced depth limit (Zig's approach), or forbid comptime
   recursion entirely? **This must be answered to ship §4**, and therefore §1. It was
   answerable-later while it sat inside RFC-0092 alongside reflection; it is not
   answerable-later here.
2. **Comptime and allocation** *(inherited from RFC-0092 OQ7 / RFC-0055 OQ2 — also now
   blocking).* **Out of scope for `#726`'s slice, 2026-09-27, for the same reason as OQ1**
   — a `comptime let` constant needs no allocation; only `comptime fun` does, and that's
   excluded from this slice's admissible set. Still open for §1/§4's broader scope. Can
   comptime functions allocate? RFC-0092 §0 asserted comptime needs "its
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
3. **Comptime error messages** *(inherited from RFC-0092 OQ8 / RFC-0055 OQ5).*
   **Non-blocking for `#726`'s slice, formalized 2026-09-27** — already stated as less
   blocking than OQ1/OQ2 below, and doubly so once those are out of scope here: a
   `comptime let` constant-folding failure is a much simpler diagnostic surface than a
   failing arbitrary `comptime fun` call. Still worth a good answer eventually, tracked as
   follow-up, not part of what `#726` needs settled. A failing
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

   **Sufficient for design purposes, 2026-09-27.** The evidence above (RFC-0061's own
   measured table, #263's independent measurement of `[T; 2]: Copy` working with a literal
   arity) is enough to settle the *design* question this open question actually asks —
   whether §3's mechanism is the right shape to unblock #263's array half. The remaining
   "confirm against the built interpreter" step is empirical validation at implementation
   time, not a design decision left open; it belongs to whoever implements §3, not to this
   review pass.
6. **Sequencing against RFC-0124.** RFC-0124 (Sequence Types, `1-under-review`) may change
   what `[T; N]` and `T[]` *are*. Its OQ3 is answered by §3, but if RFC-0124 revisits
   `[T; N]`'s role more broadly, §3's parameter mechanism should follow that decision
   rather than precede it — the same warning #263 already gives ("any array work here
   should follow that decision rather than precede it, or it will be written twice").

   **Checked 2026-09-27, no conflict currently visible.** RFC-0124's own comparison table
   already cites this RFC's §3 as the answer to its OQ3, and its two still-open questions
   (mutable slices; the RFC-0067 lifetime-anchor dependency) are both about `T[]`, not
   `[T; N]` — nothing in RFC-0124's current text is contesting `[T; N]`'s basic role.
   **Not a full resolution:** `#1292` (the T[N]/T[]/List<T> storage-contract umbrella,
   still `needs-design` and not yet reviewed this session) is the thing actually
   positioned to reopen this, since coordinating RFC-0053/0124/0126/0133 is its explicit
   job. This narrowing stands until `#1292` says otherwise, not permanently.
7. ~~**Is §3 as designed even the right design, or just the first one written down?**
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
   unchanged. They're flagged because **this RFC is still `0-draft`** (stale — this RFC
   moved to `1-under-review` 2026-08-23; corrected here 2026-09-27), **and §3 has had zero
   readers other than its own author.** This question does not resolve by more solo
   drafting; it resolves when RFC-0132 goes through actual review and §3 either survives
   scrutiny or changes. Implementation should not be scheduled against §3 until then —
   see the header correction and `metel-core#727`/`#728` (closed 2026-08-13, re-filed
   only once this RFC reaches `2-accepted`).~~

   **Resolved for `#726`'s narrow slice, 2026-09-27 — not for RFC-0132 as a whole.** §3
   went through the actual review this question asked for, weighed against alternatives
   point by point:
   - §3.1's spelling — ratified as proposed (§3.1: reusing `comptime` beats a second
     `const` vocabulary; no alternative surfaced that read more clearly).
   - §3.2's admissible-instantiation set — **narrowed**, not ratified as originally
     written: literal or `comptime let` constant, excluding `comptime fun` calls for now
     (§3.2). This is the one place review actually changed the proposal.
   - §3.3's bound-checking placement — ratified, with the previously-missing worked
     example now written out (§3.3): deferring to use-site would make `comptime N` and
     `T` behave inconsistently within one parameter list.
   - §3.4's deferral boundary — confirmed against both of this slice's actual drivers
     (§3.4): neither `#263` nor `#1291` needs a computed arity, so the line doesn't move.

   **What this does not resolve.** RFC-0132's §1/§2/§4/§5 and Open Questions 1–3 are
   untouched by this pass — §3 answers `#726`'s narrow need, it does not make the whole
   RFC `2-accepted`-ready. `metel-core#727`/`#728` stay closed until RFC-0132 in full
   reaches that bar, exactly as this question originally specified.

---

## References

- **RFC-0092 (Comptime Core), `1-under-review`** (stale as `0-draft` here since
  2026-08-13; corrected 2026-09-27) — this RFC is split from its §0/§0a; RFC-0092
  retains `type`-as-value, `typeinfo`, and `emit`, and depends on this RFC. Its Open
  Question 9 (added 2026-08-12) is what identified §3's connection.
- **RFC-0053 (Fixed-Size Array Type), `4-implemented`** — deferred `N`-as-parameter to "a
  future RFC once a `const` declaration form exists"; §3 is that mechanism, spelled
  `comptime N: u64` rather than RFC-0053's guessed `<const N: u64>` (§3.1).
- **RFC-0124 (Sequence Types), `1-under-review`** (stale as `0-draft` here since
  2026-08-13; corrected 2026-09-27) — its Open Question 3 is answered by §3; see
  Open Question 6 for the sequencing dependency in the other direction.
- **RFC-0055 (Comptime), `5-superseded`** — original source of §1/§4/§5's execution model
  and Open Questions 1-3, via RFC-0092.
- **RFC-0083 (Public Value Exports), `5-superseded`** — §2 is its content; its tracking
  issue (#539) was closed unimplemented pending exactly this mechanism.
- **RFC-0061 (Structural Aspect Bounds), `4-implemented`** — §3.3's bound-checking
  discipline; also relevant to Open Question 5.
- **RFC-0134 / RFC-0152 / RFC-0153 (v0.13.0 closure cluster), `3-integrated`** — specify
  closures for the runtime language; §4.1 here owns their comptime-evaluation behaviour,
  relocated from RFC-0153's Non-Goals.
- **RFC-0093 (Derive Registration) / RFC-0094 (Comptime Metaprogramming)** — depend on
  RFC-0092's half, not on this one directly.
- `metel-core#263` — the hardcoded `[T; N]: Copy` arm this RFC's §3 exists to retire.
- `metel-core#288` (Frontend monomorphization, v0.17.0) — the instantiation-collection
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
