---
id: rfc-0171
title: "Prefix array type syntax: [T] and [T; N]"
date: '2026-09-27'
status: accepted
updated: '2026-09-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/1291'
---

> **Same underlying tension as RFC-0084 (refused, 2026-07-10), opposite resolution.**
> RFC-0084 considered moving the fixed-size array type from prefix `[T; N]` to postfix
> `T[N]`, to match the dynamic array `T[]`'s existing postfix convention, and refused it.
> This RFC resolves the same bracket-convention mismatch the other direction: the
> **dynamic** array type moves from postfix `T[]` to prefix `[T]`, matching `[T; N]`'s
> existing convention, which itself does not change. It is not a re-proposal of what
> RFC-0084 refused — see "Relationship to RFC-0084" below.
>
> **This RFC's own drafting session first considered postfix `T[N]` (matching RFC-0084's
> direction) before settling here.** That version is preserved in git history on this
> RFC's branch; it is not linked from this document, since the decision superseded it
> rather than building on it. The deciding factor: nested arrays (`T[N][M]`) need new
> postfix-chaining grammar machinery the `Type` production doesn't have today, while
> `[T]`/`[T; N]` gets nesting for free from recursion `Type` already has. See §2.
>
> **All three open questions closed 2026-09-27.** OQ1 (does lifting `ArrayType`'s old
> base-type restriction need a guard) is ratified as safe — full generality was already
> required for the fixed-array case, so this RFC extends an existing commitment rather
> than creating a new one; see Open Questions below. OQ2 (diagnostic wording) and OQ3
> (sweep-count staleness) were already framed as non-blocking implementation detail in
> the original draft and are confirmed as such. This RFC now reads as ready for review
> toward `1-under-review`; that transition itself is a separate step from this pass.

> **Status — under review (2026-09-27).** All three open questions resolved 2026-09-27; real engagement (RFC-0084 reversal analysis, grammar work, alternatives comparison) already behind this draft.

> **Status — accepted (2026-09-27).** All three open questions closed 2026-09-27: OQ1 (lifting ArrayType's base-type restriction) ratified safe -- already required for the fixed-array case; OQ2/OQ3 confirmed non-blocking. Weighed against two real alternatives (postfix T[]/T[N], Zig's []T/[N]T) before settling on [T]/[T;N].

## Summary

The dynamic array type moves from postfix `T[]` to prefix `[T]`, matching `[T; N]`'s
existing convention. **`[T; N]` itself does not change.** Array literals (`[e1, e2,
e3]`) and repeat-construction expressions (`[expr; N]`) are unaffected — this is a
type-syntax amendment only.

```metel
// Before                                  // After
fun sum(arr: i64[]) -> i64 { ... }         fun sum(arr: [i64]) -> i64 { ... }
let buf: [i64; 4] = [1, 2, 3, 4];          let buf: [i64; 4] = [1, 2, 3, 4];   // unchanged
```

---

## Motivation

RFC-0053 gave the fixed-size array type prefix brackets with a semicolon (`[T; N]`) and
the dynamic array type postfix brackets (`T[]`) — two different bracket conventions for
what is, structurally, the same construct plus a size constraint. RFC-0084 named this
inconsistency in 2026-07-01, then reversed itself and refused to act on it (2026-07-10),
judging the fix (moving `[T; N]` to match `T[]`) not worth its migration cost at the
time.

**Three things are different now, none available to RFC-0084 in July:**

1. **`#1292`'s three-way storage-contract framing** (`T[N]`-shaped fixed storage,
   `T[]`-shaped borrowed view, `List<T>` owning allocation) gives bracket-convention
   consistency functional weight beyond the pure aesthetic RFC-0084 weighed and set
   aside — see RFC-0171's own prior draft (superseded, see header) for that argument
   in full; it applies here too, just pointing the other direction.
2. **RFC-0132 §3** (settled 2026-09-27) needs a concrete spelling for arrays with a
   `comptime N: u64` parameter regardless of which convention wins. Resolved by this RFC
   *without any change to RFC-0132's own text* — see §3 below, the one respect in which
   this direction costs strictly less than the postfix alternative did.
3. **The nested-array grammar cost is asymmetric between the two directions, and only
   surfaced by actually working through it (§2).** Postfix `T[N]` needs the `Type`
   grammar to gain a chaining mechanism it doesn't have today (though precedented
   elsewhere — `PostfixExpression` already chains `"[" Expression "]"` this way). Prefix
   `[T]` needs nothing: `SizedArrayType`'s inner slot is already the fully general `Type`
   nonterminal, and `Type` already lists itself recursively, so `[[T]]`, `[[T; M]]`, and
   `[[T; M]; N]` all fall out for free the moment `[T]` shares that same production
   shape.

**What is not being relitigated:** the real semantic gap between this and Rust's own
`[T]` — Rust's is an unsized slice, always behind `&`/`Box`, never a bare value type,
while Metel's `[T]` here stays exactly what `T[]` already is today (used bare, no
indirection required). This RFC borrows Rust's bracket shape, not (yet) Rust's ownership
semantics; whether it should is `#1292`'s question, explicitly deferred, matching how
the previous draft of this RFC treated the same gap in the other direction.

---

## 1. Type syntax: `[T]`

```metel
T[]   // was
[T]   // is
```

`T` is any type. `[T]` is untyped-size — the dynamic array, exactly what `T[]` already
meant, same runtime representation, same coercions, same everything except the spelling.

`[T; N]` (fixed-size array) is **untouched** — same spelling RFC-0053 gave it.

## 2. Grammar

The current grammar has two separate productions:

```
SizedArrayType → "[" Type ";" INT "]"
ArrayType      → ( "()" | TupleType | RecordProjectionType | RecordType
                  | ExtendsType | DynType | NamedType ) "[]"
```

This RFC merges them into one, by making `SizedArrayType`'s size suffix optional and
retiring `ArrayType` entirely:

```
BracketArrayType → "[" Type ( ";" INT )? "]"
```

**This is a smaller diff than the postfix alternative needed**, and not just because
one line disappears instead of two remaining. `ArrayType`'s old base-type list excluded
`ReferenceType`, `FunType`, `SizedArrayType`, and `ArrayType` itself — a restriction
`SizedArrayType`'s own inner slot never had (it was always the fully general `Type`).
Unifying onto `SizedArrayType`'s shape means the dynamic case gains the same generality
the fixed case already had, closing an asymmetry that likely existed only because
`ArrayType` was never revisited, rather than for a principled reason anyone can point to
— `[&T; N]` and `[|i64| -> T; N]`-shaped fixed arrays are already legal today, per the
grammar as written, whether or not any fixture happens to exercise them; `[&T]`/`[|i64|
-> T]` dynamic arrays becoming legal too is this RFC's one genuine semantic widening,
flagged honestly as Open Question 1 rather than assumed harmless.

**Nesting is a corollary, not a separate mechanism.** `Type` already lists
`BracketArrayType` as one of its own alternatives, so `Type → BracketArrayType → Type`
is ordinary grammar recursion already present for `[T; N]` today (`[[T; M]; N]` already
parses). `[T]` sharing the same production inherits the same recursion automatically:
`[[T]]`, `[[T; M]]`, and `[[T]; N]` all parse without any additional rule.

## 3. Relation to comptime-known `N` (RFC-0132 §3)

**No change needed.** RFC-0132 §3's own examples already use `[T; N]`:

```metel
fun reverse<T, comptime N: u64>(arr: [T; N]) -> [T; N] { ... }
```

This is exactly this RFC's spelling, unmodified — RFC-0132's text does not need
sweeping, unlike the postfix direction this RFC's drafting session first considered.

## 4. Relation to `#263` (fixed-array `Copy`)

Also unchanged:

```metel
extend<T: Copy, comptime N: u64> [T; N]: Copy;
```

Exactly as RFC-0132's own Open Question 5 already wrote it. This RFC's entire footprint
on the records/comptime cluster is the dynamic-array spelling alone.

---

## Migration

**Larger in raw site count than the postfix direction would have been, stated plainly.**
Measured against the corpus at time of writing:

- **~460 sites** in `metel-interpreter/tests/integration/sources/` use postfix `T[]`
  (dynamic array type). All move to `[T]`.
- **~395 sites** in `docs/rfcs/` and `docs/reference/` prose/code-fences use the same
  shape.
- `[T; N]` (fixed array, ~74 fixture sites, ~232 doc sites) is **not touched** — and
  neither is any RFC-0132/`#263` text that already spells it that way (§3, §4 above).

**Flag-day, matching this project's established precedent** (`PROCESS.md`'s RFC-0115
account — 566 sites swept in the same change as the code migration, no dual-spelling
window):

- The parser stops accepting postfix `T[]` in type position the same release this RFC
  integrates.
- Every fixture, RFC, and spec page citing `T[]` is swept in the same change as the
  grammar amendment, per `PROCESS.md`'s exit criteria (no blind regex; scope by
  code-fence language; verify by compiling).
- A parse-error diagnostic for postfix `T[]` in type position, pointing at `[T]`, is
  worth specifying before implementation — left to the implementation issue.

---

## Relationship to RFC-0084

RFC-0084 is `6-refused`. It considered the *other* resolution to this same bracket
mismatch — moving `[T; N]` to match `T[]`'s postfix convention — and refused it on
Rust-familiarity and migration-cost grounds. This RFC does not reopen that specific
proposal or dispute its refusal; it resolves the same underlying inconsistency by moving
the *other* spelling, for reasons RFC-0084 had no occasion to weigh (`#1292`'s framing,
RFC-0132 §3's existence, and the nested-array grammar asymmetry in §2). If those
reasons don't survive review, the right outcome is refusing this RFC on its own terms,
not treating RFC-0084's 2026-07-10 refusal as having already settled this direction —
it settled the other one.

---

## Alternatives Considered

- **Postfix `T[]` / `T[N]`** (this RFC's own first draft — moving `[T; N]` to match
  `T[]` instead of the reverse). Would have left `T[]` untouched (smaller migration:
  ~74 fixture sites instead of ~460) and stayed clear of the already-crowded
  prefix-`[...]` family (array literals, patterns, repeat construction, closure capture
  lists all already share that shape). Set aside because nested arrays need a new
  postfix-chaining mechanism `Type` doesn't have (§2), and no language surveyed uses
  bare postfix `T[N]` — the weakest precedent of any option considered.
- **Zig's exact `[]T` / `[N]T`.** Strongest real precedent of any option — not a
  borrowed shape but Zig's complete, coherent system for both array kinds, and notably
  consistent with RFC-0132 §3's own Zig-derived choice for `comptime`. Set aside because
  it touches both existing spellings (the largest migration of any option: `T[]` *and*
  `[T; N]` both move) and its `[N]T` puts the element type outside the bracket,
  diverging from Metel's own value-level forms (`[e1,e2,e3]`, `[a,b,..rest]`) where
  content always sits inside.

---

## Open Questions

1. ~~**Does lifting `ArrayType`'s old base-type restriction (§2) want a guard, or is
   full generality actually correct?** `[&T]` and `[|i64| -> T]` become legal
   dynamic-array element types under the unified production, matching what `[T; N]`
   already permits.
   No one has identified a reason the old restriction existed beyond `ArrayType` never
   being revisited since RFC-0053 — but "no reason found" isn't the same as "confirmed
   there is none." Worth a deliberate look before integration rather than inheriting the
   widening silently.~~
   **Resolved 2026-09-27 — no guard, full generality is correct, and it isn't actually
   new.** `[&T; N]` is already grammatically legal *today*, for the fixed-array case,
   completely independent of this RFC — `SizedArrayType`'s inner slot was never
   restricted. Whatever the runtime representation and move-/borrow-checking treatment
   of "an array holding references" needs to be, the language is already committed to
   having an answer for it, because the fixed-array case already demands one. This RFC
   doesn't introduce that question; it only extends where the *same* already-required
   answer applies, from fixed arrays to dynamic ones — §1's "same runtime
   representation... same everything except the spelling" already says the two share
   machinery, so there's no separate soundness surface for the dynamic case to open.
   **What this does not confirm:** whether `[&T; N]` is *fully verified* to typecheck
   and move-check correctly today (no fixture in the corpus exercises it either way) —
   that's a pre-existing gap this RFC neither creates nor worsens, tracked on its own
   merits if it isn't already, not a reason to hold this RFC's `T[]`-spelling question
   hostage to an unrelated, already-existing verification gap.
2. **Diagnostic wording for the retired postfix `T[]`.** Non-blocking, confirmed
   2026-09-27 — implementation-quality, not a design question; a parse error pointing at
   `[T]` is wanted, exact text is an implementation-time decision, doesn't gate
   `2-accepted`.
3. **Sweep completeness at integration time.** Non-blocking, confirmed 2026-09-27 — the
   ~460/~395 counts are a snapshot from this drafting session, explicitly stated as such;
   re-counting against the corpus as it stands at integration is a mechanical step for
   whoever integrates this, not an open design question.

---

## References

- RFC-0053 (Fixed-Size Array Type, `4-implemented`) — `[T; N]`'s origin, unchanged by
  this RFC.
- RFC-0084 (Fixed-Size Array Syntax — Retaining `[T; N]`, `6-refused`) — the same
  bracket-mismatch tension, opposite resolution; see "Relationship to RFC-0084" above.
- RFC-0132 (Comptime Execution Model, `1-under-review`, §3 settled 2026-09-27) — needs
  no change under this RFC's direction (§3 above), unlike the postfix alternative.
- `metel-core#263` — likewise needs no change under this RFC's direction (§4 above).
- `metel-core#1291` — this RFC's tracking issue.
- `metel-core#1292` — the storage-contract framing this RFC's Motivation cites; the
  ownership-semantics question (`&[T]` vs. bare `[T]`) this RFC explicitly defers to it.
- `reference/spec/grammar.md` — the actual current `SizedArrayType`/`ArrayType`/
  `PostfixExpression` productions cited in §2, not illustrative sketches.
- `docs/rfcs/PROCESS.md` — RFC-0115's migration-sweep precedent, the model this RFC's
  Migration section follows.

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.14.0
