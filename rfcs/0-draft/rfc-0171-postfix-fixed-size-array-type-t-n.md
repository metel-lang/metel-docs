---
id: rfc-0171
title: "Postfix fixed-size array type T[N]"
date: '2026-09-27'
status: draft
---

> **Reopens RFC-0084 (refused, 2026-07-10), on new grounds.** RFC-0084 was itself a
> reversal: its original text (2026-07-01) proposed exactly this change, then rewrote
> itself the same document to reaffirm `[T; N]` instead, then was refused once it had
> nothing left to propose. This RFC does not dispute RFC-0084's reasoning at the time —
> it argues that two things have changed since: the `#1292` storage-contract framing
> (`T[N]` / `T[]` / `List<T>` as three deliberately distinct roles) gives postfix
> consistency functional weight beyond the aesthetic argument RFC-0084 weighed and set
> aside, and RFC-0132 §3 (settled 2026-09-27) fixes what `T[N]`'s generic-parameter case
> actually needs to look like. See "Relationship to RFC-0084" below.

## Summary

Amend RFC-0053: the fixed-size array **type** spells as postfix `T[N]`, matching the
existing postfix dynamic-array type `T[]`, instead of RFC-0053's prefix `[T; N]`.
**Nothing else changes.** Array literals (`[e1, e2, e3]`) and repeat-construction
expressions (`[expr; N]`) stay exactly as specified — this is a type-syntax amendment
only, not a value-syntax or semantics change, and it does not touch `T[]`'s own spelling
or its eventual ownership semantics (`#1292`'s job, explicitly out of scope here).

```metel
// Before (RFC-0053)                    // After (this RFC)
let buf: [i64; 4] = [1, 2, 3, 4];        let buf: i64[4] = [1, 2, 3, 4];
fun sum(arr: [i64; 3]) -> i64 { ... }    fun sum(arr: i64[3]) -> i64 { ... }
[value; 8]  // repeat construction — UNCHANGED, still prefix, still `;`
```

---

## Motivation

RFC-0053 gave the dynamic array type postfix brackets (`T[]`) and the fixed-size array
type prefix brackets with a semicolon (`[T; N]`) — two different bracket conventions for
what is, structurally, the same construct plus a size constraint. RFC-0084 already
named this inconsistency and judged it real but not worth the migration cost at the time
(2026-07-01, nothing had shipped against either spelling yet).

**Two things are different now, neither available to RFC-0084 in July:**

1. **`#1292`'s three-way storage-contract framing.** `T[N]` (inline fixed storage),
   `T[]` (borrowed contiguous view), and `List<T>` (owning runtime-sized allocation) are
   being formalized as three deliberately distinct roles in the same design space.
   Visual consistency between the two array-shaped members of that trio — both sharing
   the postfix-bracket convention, both visually distinct from `List<T>`'s name-based
   form — does real work in *reading* the three-way distinction, not just in matching
   `T[]`'s existing spelling for its own sake. RFC-0084 only ever weighed `T[N]` against
   `[T; N]` in isolation; it had no third form to distinguish either from.
2. **RFC-0132 §3 exists now** (settled 2026-09-27, `comptime N: u64` generic
   parameters) and needs a spelling for `T[N]`-with-a-parameter regardless of which
   bracket convention wins — `extend<T: Copy, comptime N: u64> T[N]: Copy;` is the form
   this RFC's own §3 (below) settles.

**What has not changed, and is not being relitigated:** RFC-0084's cost argument was
real, and migration cost here is non-trivial — this RFC does not claim otherwise (see
Migration below for the actual scope). What changed is the *value* side of the
weighing, not the cost side.

---

## 1. Type syntax: `T[N]`

```metel
[T; N]   // was
T[N]     // is
```

`T` is any type; `N` is the same admissible set RFC-0053 always specified for this
position — a non-negative integer literal — now additionally including a `comptime N:
u64` generic parameter per RFC-0132 §3 (§3 below). Two `T[N]` types are equal only when
both the element type and the size match, unchanged from RFC-0053.

`T[]` (dynamic array) is **untouched** — same spelling, same grammar production it
already had.

## 2. Grammar

The current grammar (`reference/spec/grammar.md`) has two separate top-level `Type`
alternatives for this:

```
SizedArrayType → "[" Type ";" INT "]"
ArrayType      → ( "()" | TupleType | RecordProjectionType | RecordType
                  | ExtendsType | DynType | NamedType ) "[]"
```

This RFC merges them into one production, with the bracket's contents optional:

```
ArrayType → ArrayBaseType "[" ArraySize? "]"
ArrayBaseType → "()" | TupleType | RecordProjectionType | RecordType
              | ExtendsType | DynType | NamedType
ArraySize → INT | IDENTIFIER
```

`ArraySize`'s `IDENTIFIER` alternative is a reference to a comptime-known `u64` value in
scope — a `comptime N: u64` generic parameter (RFC-0132 §3) or, once RFC-0132's wider
scope settles, a `comptime let` constant. `SizedArrayType` retires; `[T; N]` is no
longer valid type syntax after this RFC integrates (see Migration).

**`ArrayBaseType` is carried over unchanged, not widened, and that's a real gap to name
explicitly — see Open Question 1.** The current list already excludes `ReferenceType`,
`FunType`, and — critically for this RFC — both `SizedArrayType` and `ArrayType`
themselves. That means nested arrays (`T[N][M]`, `T[][]`, `T[N][]`) are not directly
expressible through this production as merely restated; whether that's already true
today for `ArrayType`'s dynamic half (worth checking independently of this RFC) or a new
gap this merge introduces for the sized half (`[[T; M]; N]` parses fine today, since
`SizedArrayType`'s inner slot is the fully general `Type`) needs resolving, not silently
carrying forward an asymmetry.

## 3. Relation to comptime-known `N` (RFC-0132 §3)

RFC-0132 §3, settled 2026-09-27: `comptime N: u64` generic parameters admit an integer
literal or a `comptime let` constant as their instantiation — not a `comptime fun` call,
for now. Under this RFC's spelling:

```metel
fun reverse<T, comptime N: u64>(arr: T[N]) -> T[N] { ... }
```

replaces RFC-0132 §3's own `[T; N]`-spelled example verbatim. Nothing about §3's rules —
the admissible-instantiation set, definition-site bound checking — changes; only the
surface spelling of the type they apply to does. RFC-0132's own text should be swept to
`T[N]` once this RFC integrates (see Migration).

## 4. Relation to `#263` (fixed-array `Copy`)

`#263`'s blocked hardcoded `Copy` arm, once RFC-0132 §3 supplies `comptime N`, is
written:

```metel
extend<T: Copy, comptime N: u64> T[N]: Copy;
```

replacing the `[T; N]`-spelled form RFC-0132's own Open Question 5 used when checking
this against the interpreter's structural-impl machinery. This RFC does not change
`#263`'s dependency structure (still gated on RFC-0132 §3 landing, per RFC-0132's own
Open Question 5) — only the spelling of the impl target.

---

## Migration

**This is real, non-trivial migration, stated honestly rather than minimized.**
Measured against the actual corpus at the time of writing:

- **74 sites** in `metel-interpreter/tests/integration/sources/` use `[T; N]`-shaped
  sized-array type syntax (grep count, type position only — repeat-construction
  expressions are excluded and unaffected).
- **232 sites** in `docs/rfcs/` and `docs/reference/` prose/code-fences use the same
  shape, spread across every RFC in the records/arrays/comptime cluster (RFC-0053 itself,
  RFC-0061, RFC-0092, RFC-0118, RFC-0124, RFC-0132, and others).
- `T[]` (dynamic array, ~460 sites) is **not touched** — only the sized-array spelling
  moves.

**Flag-day, not a deprecation window** — matching this project's own established
precedent (`PROCESS.md`'s RFC-0115 account: a field-separator migration sweeping 566
sites in the same change as the code migration, not as a follow-up, with no dual-spelling
transition period). A syntax that parses as both old and new simultaneously is more
machinery than a one-time mechanical sweep costs, and this project's own discipline
already rejects that trade for a comparable-sized migration:

- The parser stops accepting `[T; N]` in type position the same release this RFC
  integrates. `[expr; N]` (repeat construction, expression position) is unaffected and
  never stops parsing — the two are different grammar positions and this RFC does not
  touch the expression form.
- Every fixture, RFC, and spec page citing the old spelling is swept in the same change
  as the grammar amendment, per `PROCESS.md`'s exit criteria for a syntax-changing RFC
  (no blind regex; scope by code-fence language; verify by compiling, not by reading).
- A clear, specific parse-error diagnostic for `[T; N]` in type position, pointing at
  `T[N]`, is worth specifying before implementation — left to the implementation issue
  rather than fixed here, but flagged so it isn't forgotten (see Open Question 2).

---

## Relationship to RFC-0084

RFC-0084 is `6-refused`. This RFC does not transition it, supersede it, or claim it was
wrong for its time — RFC-0084's own text already concedes the postfix-consistency
argument is real ("that inconsistency still exists in the language as specified"); it
judged the argument outweighed by cost when cost was the only thing on the value side of
the scale. This RFC's Motivation section states what's different: `#1292`'s three-way
framing and RFC-0132 §3's existence. If those are not judged sufficient on review, the
right outcome is refusing this RFC too, not silently amending RFC-0084's own text.

---

## Alternatives Considered

Two other spellings were weighed seriously before settling on `T[N]`, both changing
`T[]` as well as the fixed-array form — set aside primarily because `T[]` is
established, heavily-used syntax (~460 corpus sites) this RFC has no independent reason
to touch, not because either alternative is weaker in isolation:

- **`[T]` / `[T; N]`** (prefix, keeping `[T; N]` exactly as RFC-0053 specified it,
  changing only `T[]` → `[T]`). Strongest symmetry with Metel's own value-level array
  syntax — `[e1, e2, e3]` (literal), `[a, b, ..rest]` (pattern), and `[expr; N]`
  (repeat) are all already prefix-bracket, and `[T]`/`[T; N]` would echo that shape
  exactly, type position mirroring value position. Weaker precedent than it first
  reads: `[T; N]` is exactly Rust's spelling, but Rust's `[T]` is an *unsized slice*,
  always accessed through `&[T]`/`&mut [T]` — never a bare value type — so `[T]` here
  would borrow Rust's bracket shape without (yet) borrowing Rust's actual semantics,
  a question this RFC deliberately leaves to `#1292`.
- **`[]T` / `[N]T`** (Zig's exact convention, prefix, size-or-nothing inside the
  brackets, element type outside). The strongest real precedent of any option
  considered — not a borrowed shape but Zig's complete, coherent system for both array
  kinds at once, and notably consistent with RFC-0132 §3's own choice to follow Zig's
  staging model over Rust's for `comptime` generic parameters. Costs the most to
  migrate of any option surveyed, since it touches both `T[]` and the fixed-array form
  rather than either alone, and its `[N]T` puts the element type outside the bracket,
  diverging from Metel's own value-level forms where the content always sits inside the
  brackets.

Both remain live candidates for a *different* RFC that also revisits `T[]`'s own
spelling; nothing here forecloses that. This RFC's scope is deliberately narrow: settle
`#1291` without also deciding whether `T[]` itself should move.

---

## Open Questions

1. **Nested arrays and `ArrayBaseType`'s scope (§2).** `T[N][M]`, `T[][]`, and
   `T[N][]` are not directly expressible through `ArrayBaseType`'s current restricted
   list, which excludes both array-type forms recursively. Needs resolving before
   integration: either widen `ArrayBaseType` to admit `ArrayType` itself (recursive
   nesting, matching what `SizedArrayType`'s fully-general inner `Type` slot already
   allows today for the sized half), or confirm nested arrays are already unreachable
   through `ArrayType`'s dynamic half today and this RFC merely preserves an existing
   restriction rather than introducing a new one. Either answer is fine; leaving it
   unchecked is not — RFC-0084's own worked example (`[[f64; 4]; 4]`, a 4×4 matrix)
   needs a `T[N][M]`-shaped equivalent to exist under this RFC's grammar, and which
   nesting order (`T[N][M]` = N-outer-of-M-inner, or the reverse) reads correctly needs
   stating explicitly, not inferred from the old prefix form's own stated convention.
2. **Diagnostic wording for the retired `[T; N]` type syntax.** A parse error pointing
   users at `T[N]` is clearly wanted (flagged in Migration); its exact text is an
   implementation-time decision, not fixed here.
3. **Sweep completeness at integration time.** The 74/232 counts above are a snapshot
   from this RFC's own drafting session; re-count against the corpus as it stands when
   this RFC is actually integrated, not against this document's numbers, which will be
   stale by then.

---

## References

- RFC-0053 (Fixed-Size Array Type, `4-implemented`) — the RFC this amends; `[T; N]`'s
  origin.
- RFC-0084 (Fixed-Size Array Syntax — Retaining `[T; N]`, `6-refused`) — proposed and
  then refused this exact change; see "Relationship to RFC-0084" above.
- RFC-0132 (Comptime Execution Model, `1-under-review`, §3 settled 2026-09-27) — the
  `comptime N: u64` mechanism this RFC's §3 spells against.
- `metel-core#263` — the hardcoded `[T; N]: Copy` arm this RFC's §4 respells, gated on
  RFC-0132 §3 as before.
- `metel-core#1292` — the `T[N]`/`T[]`/`List<T>` storage-contract framing this RFC's
  Motivation cites; does not depend on `#1292` reaching any particular stage, only cites
  its existing framing.
- `reference/spec/grammar.md` — the actual current `SizedArrayType`/`ArrayType`
  productions this RFC merges (§2), not an illustrative sketch.
- `docs/rfcs/PROCESS.md` — RFC-0115's migration-sweep precedent (566 sites, one change,
  no dual-spelling window), the model this RFC's Migration section follows.

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.14.0
