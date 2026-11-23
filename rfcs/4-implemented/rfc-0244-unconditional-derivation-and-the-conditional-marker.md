---
id: rfc-0244
title: "Unconditional derivation and the conditional marker"
date: '2026-11-22'
status: implemented
updated: '2026-11-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/2150'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/2153'
impl_status: implemented
coverage:
  "1": { spec: "spec.declarations.aspects.declaration-clauses.legality-11" }
  "2": { spec: "spec.declarations.aspects.declaration-clauses.legality-13" }
  "3": { spec: "spec.declarations.aspects.declaration-clauses.legality-6" }
  "4": { spec: "spec.declarations.aspects.declaration-clauses.legality-13" }
  "5": { spec: "spec.declarations.aspects.declaration-clauses.legality-5" }
---

> **Status — under review (2026-11-22).** Taken to review as part of the metel-core v0.17.0 plan (#2150)
>
> **Review (2026-11-23).** Checked against RFC-0227, RFC-0234, RFC-0239, RFC-0207, RFC-0224 and the grammar. Consistent: the changes it
> makes to each are the ones stated here, and every program the new default affects fails to compile with a fix-it, none changes
> meaning silently. Three corrections follow: std's `List` declares no `derives` (Interaction, Std), the grammar sketch of section 1
> repeated the parentheses of `derive_args`, and the legacy `via` clause is now stated. The four open questions are decided
> (below), and the rule for a derivation that takes arguments (bare gives an empty `Flow`, `(..)` the computed one) is stated once, in RFC-0238 section 2 (#2151).

> **Status — accepted (2026-11-23).** Accepted after the acceptance review: consistent with RFC-0227, 0234, 0239, 0207 and 0224; open questions decided; accepted before RFC-0238 (metel-core#2150, #2151)

> **Status — integrated (2026-11-23).** Integrated into the spec: declaration-clauses rules 5, 6, 11, 13 and 18 and the Copy and residual examples; checked against RFC-0227, 0234, 0239, 0207, 0224 (metel-core#2150)

> **Status — implemented (2026-11-23).** Implemented in metel-core#2153: bare derives and copy are unconditional, ? computes the flow, copy(..) is removed; the rule for derivations that take arguments moved to RFC-0238 section 2

## Summary

A `derives` entry with no arguments is **unconditional**, and the argument `..` asks the compiler to **compute** the
condition from the fields: `derives A(..)`. A `derives` entry is a call to the aspect's derivation (RFC-0238), so the computed flow is
a value passed as an argument, not a mark on the entry. The `copy` class keyword follows, since it is `derives Clone, Copy`, and its
one-character form `copy?` is `derives Clone(..), Copy(..)`:

```metel
copy struct Point { x: i64, y: i64 }                  // = derives Clone, Copy; no parameter is involved
copy struct Id<T> { n: i64 }                          // Copy for every T (today: copy() struct Id<T>)
copy? struct Boxed<T> { value: T }                    // = derives Clone(..), Copy(..); Copy when T is (today: copy struct Boxed<T>)
struct Pair<A, B> derives Clone(..) { a: A, b: B }    // Clone when A and B are (today: derives Clone)
struct Tagged<T> derives Clone(T) { id: i64 }         // unchanged: the condition is stated
pub struct W<T> derives Clone(T), Copy(T) { value: T } // unchanged: a pub type states it
```

| Written | Condition on the declaration's type parameters |
|---|---|
| `derives A` and `copy` | None. Every field must have `A` for every instantiation, or the entry is an error. |
| `derives A(..)` and `copy?` | Computed: the smallest set the fields need (RFC-0227's flow). |
| `derives A(P, Q)` | Stated, as in RFC-0227. |

Three things follow. The default of a bare entry changes from *computed* to *none*. The `copy(T)` and `copy()` forms of RFC-0239 are
removed, since `copy` is `copy()` and `copy(T)` is `derives Clone(T), Copy(T)`. And `(..)` is one rule for every aspect with a
field-wise derivation, so `copy?` is its sugar and not an exception.

It amends RFC-0227 and RFC-0239, both implemented, and is the rule RFC-0238 section 2 applies to a derivation's `Flow` parameters.

---

## Motivation

1. **`copy(T)` reads as an argument to `copy`.** `copy(T) struct Point<T> { x: i64, y: i64, z: T }` suggests "copy of `T`" or a
   parameterized keyword. It means "Copy when `T` is Copy", which is a condition on a type parameter. The parentheses are
   the argument list of a derivation (RFC-0227), but the keyword form hides that, so a reader has no way to see it.
2. **The same word has three forms with two defaults.** Bare `copy` computes the condition, `copy()` states none, and `copy(T)`
   states one. `copy()` and bare `copy` differ in a single pair of parentheses and in whether the impl is conditional.
3. **Whether a type is conditionally Copy is invisible at the declaration.** `copy struct Boxed<T> { value: T }` and
   `copy struct Id<T> { n: i64 }` look alike, but one makes `Boxed<String>` non-Copy. The difference is in the fields.
   The conditional form is the one that takes a decision about the public interface (RFC-0227 section 3), so it is the one
   that should be visible.
4. **Computing is a decision, and the default should not take it silently.** A field edit can change which instantiations of a
   type are Copy. RFC-0227 section 3 answers that for a `pub` type by making it state its flow. That rule has two halves, and this
   RFC treats them separately. *Consent:* a declaration that does not say "computed" gets exactly what it says, and making the
   computed form a marked, opt-in choice extends that to every type. *Edit-time diagnostic:* a field edit must not change a public
   interface silently. `(..)` cannot give that second half, because the declaration says "computed" and a field edit still changes the
   public bounds with no error, so a `pub` type keeps the rule even where it would write `(..)` (section 4).
5. **`copy` should mean what it says.** A reader of `copy struct S<T>` should be able to conclude that `S<X>` is Copy for any `X`
   without reading the fields.

---

## Proposal

### 1. The computed flow

```
derive_entry = { type_path ~ derive_args? }
derive_args  = { "(" ~ (derive_rest | (ident ~ ("," ~ ident)* ~ ","?)?) ~ ")" }
derive_rest  = { ".." }
class_kw     = { copy_kw ~ "?"? | linear_kw }
```

`derive_args` is the rule that exists today, and `..` is its one new entry. The legacy `via` clause (RFC-0224) is untouched: it still
parses so that it can be rejected with its message naming the stated form, and `via` does not combine with `(..)`.

`(..)` is the whole argument list: it does not combine with named parameters. It is accepted on every entry whose derivation is
field-wise (RFC-0227 section 2). On another entry (`derives Builder(..)`, RFC-0222) it is an error: such a derivation has no flow to
compute. A postfix `?` after an entry (`derives Clone?`) is a parse error whose message names `derives Clone(..)`. The class keyword
takes the one-character `?` (section 3) and not `linear`, which is reserved (RFC-0207) and has no condition to compute.

### 2. Meaning

For an entry of a field-wise derivation of `A` on a declaration `T<P1, .., Pn>`:

- `derives A` is `derives A()`: the flow is empty, and legality 1 of RFC-0227 section 2 applies to it. If some field's `A` depends on
  a type parameter, the entry is an error. Its fix-it names the computed flow: "write `derives A(..)`, or `derives A(P, Q)`".
- `derives A(..)` computes the flow, as a bare `derives A` did before this RFC (RFC-0227 section 1).
- `derives A(P, Q)` is unchanged.

The three forms differ in the flow only. The impl the compiler writes, the sufficiency rule, the entailment of `Clone` inside
`Copy` (RFC-0234), and everything that stays with the aspect (RFC-0227 section 2) apply to all of them.

### 3. The `copy` class keyword

`copy` is `derives Clone, Copy`, and `copy?` is `derives Clone(..), Copy(..)` (RFC-0234 section 3). The argument-list form of RFC-0239
(`copy(T)`, `copy(A, B)`, `copy()`) is removed. It is a parse error whose message names the replacement: "write `copy?` to compute the
condition, or `derives Clone(T), Copy(T)` to state it".

An explicit `derives` entry for `Clone` or `Copy` beside the keyword still replaces the entry the keyword stands for, as in
RFC-0239 section 3's first rule (metel-core#2070). That section's second rule, the error for a keyword that has a list, goes with the
list. `copy? struct P<T> derives Clone(T)` states the `Clone` flow and computes the `Copy` flow.

### 4. The `pub` rule

RFC-0227 section 3 allows a `pub` generic type to omit its flow only when the computed set is empty. Under this RFC the omission
has two spellings, and the rule applies to the one that computes:

- `pub copy struct S<T>` and `pub struct S<T> derives Clone`: legal exactly when the fields need nothing from `T`, which is the
  strictness of section 2. The error is section 2's, with no separate `pub` case.
- `pub copy? struct S<T>` and `pub struct S<T> derives Clone(..)`: legal exactly when the computed flow is empty, as RFC-0227 section 3
  says (it is then the same impl as the bare form). Otherwise `T0046`, with the fix-it "write `derives Clone(T), Copy(T)`".

So a public generic type that is conditionally Copy still writes `derives Clone(T), Copy(T)`: the flow stays visible in the
interface. `copy(T)` was RFC-0239's one-word spelling of that, and this RFC removes it. That is its cost (see Costs).

The computed form does not lift the rule because they answer different silences: `(..)` removes the silent default, and the rule removes the
silent interface change at a field edit (Motivation 4). Today a broken use of a changed type is a loud error at the use site, so the
rule protects separately compiled consumers, which Metel has no package system for yet (metel-core#1357).

### 5. The legality of the strict form is the existing legality 1

Strictness needs no new check. `derives A()` already requires the empty flow to be sufficient (RFC-0227 section 2, rule 1), and
`copy() struct Id<T> { n: i64 }` is accepted today for that reason. This RFC changes which spelling reaches that check.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep `copy(T)` | The motivation: a condition reads as an argument to the keyword. |
| `copy where T: Copy` | A bound says what must hold of `T`, while the entry states which parameters the impl is bounded on (the flow), and the compiler would have to translate one into the other for each aspect. A larger change to the clause grammar than a suffix. It may still be the better spelling of the *stated* form later (question 2). |
| A strict `copy` keyword and no computed form | Leaves `derives Clone`, with the meaning it has today (computed), and a differently-behaved `copy`. Breaks "`copy` is `derives Clone, Copy`" (RFC-0234). |
| A computed form on the keyword only (`copy?`) | The keyword is a spelling of two `derives` entries, so a keyword-only form would be a second rule for the same thing, and a user's aspect (RFC-0238) could not use it. `copy?` exists as sugar for the entries' `(..)`. |
| A postfix `?` on a `derives` entry (`derives Clone?`) | An entry is a call to the aspect's derivation (RFC-0238), and a postfix mark is not an argument: it needs a special rule in the call, and cannot say which `Flow` parameter it applies to when there are several. The computed flow is a value, `(..)`. This RFC first wrote `?` and replaced it before release (RFC-0246). |
| `(..)` as a comptime `try_derive` that skips on failure | A conditional impl is not a yes or no at the declaration; it is a condition on the parameters, evaluated per instantiation. RFC-0238 section 5 has the deriver emit bounds, and the checks decide. A skip-on-failure derivation would need the deriver to see impls, which section 5 rules out. |
| Default conditional everywhere (Rust's derive) | The over-constraint of Rust's heuristic and, for a public type, an interface that moves with its fields (RFC-0227). |
| `copy` strict only on `pub` types | Two meanings for one keyword, depending on visibility. |
| Allow `pub copy?` (the marker as the author's consent) | `(..)` answers the silent default, not the silent interface change: the declaration says "computed" and a field edit still changes the public bounds with no error. Relaxing the rule later is non-breaking and tightening it later is not, so it starts strict. Decided 2026-11-23 (kept after discussion); revisit with the package system (metel-core#1357) and evidence of the cost. |
| Make a bare `derives A()` an error as redundant | The two are the same; see question 1. |

---

## Interaction with other work

- **RFC-0227** (implemented). Section 1's "No parentheses asks the compiler to compute the arguments" becomes "`(..)` asks ...", and
  "no parentheses" means the empty flow. Section 1's `derives Clone()` is the same as `derives Clone`. Section 3 (the `pub` rule) is
  restated by section 4 above and is unchanged in effect for the computed form. Its examples change: `Plain<T> derives Clone` becomes
  `derives Clone(..)`.
- **RFC-0238** (under review). A derivation that takes arguments reads the marks of this RFC: a bare entry gives each `Flow`
  parameter the empty flow and `(..)` the computed one. RFC-0238 section 2 states that rule, so it is stated once, and this RFC
  covers std's `Clone` and `Copy` (metel-core#2151).
- **RFC-0239** (implemented). Sections 1, 2 and 4 are superseded; the first rule of section 3 stays. The RFC moves to
  `5-superseded` only if the whole of it is replaced; this RFC supersedes the argument list, and states the remainder in section 3.
- **RFC-0234** (implemented). The keyword stays the one-word form of `derives Clone, Copy`. The flow entailment of section 2 of that
  RFC is unchanged: with `(..)` on both entries the computed `Clone` flow is inside the computed `Copy` flow.
- **RFC-0207** (implemented). The class keyword grammar gains `?` on `copy`.
- **RFC-0224** (integrated). Rules 1 to 3 and 9 are unchanged. Rule 3's fix-it text changes.
- **RFC-0219** (implemented). `copy` before a closure literal and in a written function type are different positions and
  unaffected. `?` is not accepted there.
- **Std** (`core.mtl`). `Option` and `Result` already state their flows (`derives Clone(T), Copy(T)` and `derives Clone(T, E),
  Copy(T, E)`), so they do not change. `List` declares no `derives`.

---

## Costs

- **A default changes meaning.** A bare `copy` or `derives A` on a generic type whose fields need a parameter, a program that
  compiles today, is an error after this RFC with a fix-it to write `(..)`. It is a mechanical edit. About 43 generic `copy`
  declarations and 19 generic bare `derives` lines in the fixtures need a look, and those whose computed flow is empty do not change.
  The compiler's error names the computed flow, so each is a one-line fix.
- **`copy(T)` and `copy()` go.** About 14 fixture declarations use them, and 4 places in the spec. `copy()` becomes `copy`. `copy(T)` becomes
  `copy?` or, for a `pub` type, `derives Clone(T), Copy(T)`.
- **The public conditional case is longer.** `pub copy(T) struct W<T>` returns to `pub struct W<T> derives Clone(T), Copy(T)`. This is
  the "status quo" that RFC-0239 section "Alternatives considered", item 1 weighed and rejected. It is the price of removing the
  list from the keyword. See question 2.
- **A new argument to learn.** `(..)` on a derivation is only an opt-in to computing, and it is the same on every aspect, but it is one
  more form than there is today.
- **Parser and expansion.** `derive_args` gains `..`, the class keyword gains `?`, and `from_class_keyword` in the clause expansion is replaced by a per-entry
  "computed" mark. The `Copy`-only guard and the keyword-list conflict check are removed. The legality 1 error gains a fix-it.

---

## Open questions

1. **Is `derives A()` still legal?** It is now the same as `derives A`. Keeping both is harmless and a spelling the user may have
   written on purpose to be explicit. Rejecting it removes the redundancy. Recommendation: keep it legal and say so, since removing it
   breaks existing programs for nothing. **Decided 2026-11-23:** it stays legal, and the spec says it is the same as `derives A`.
2. **Should a one-word spelling of the public conditional case exist?** Without `copy(T)`, `pub` conditionally-Copy types write
   `derives Clone(T), Copy(T)`. A later RFC could give the stated form a different, clearer spelling (the `where` form in the
   alternatives is one candidate) without touching `(..)`. Recommendation: leave it, and revisit when the `derives` stated form is
   next changed. **Decided 2026-11-23:** no one-word spelling; a `pub` conditionally-`Copy` type writes `derives Clone(T), Copy(T)`.
3. **Does `(..)` apply to a user's derivation before RFC-0238 is accepted?** Only std's `Clone` and `Copy` have a field-wise
   derivation today, so the marks have no user-visible effect on a user's aspect until then. Recommendation: accept this RFC for
   the two std derivations and let RFC-0238 state the rule for derivations that take arguments. **Decided 2026-11-23:** as
   recommended; RFC-0238 section 2 states it, and this implementation covers std's `Clone` and `Copy`.
4. **Other class keywords.** `linear` is reserved. If it takes a flow later, this RFC does not decide whether `linear?` exists;
   section 1 rejects it for now. **Decided 2026-11-23:** no `linear?`; `linear` stays reserved.

---

## Decision

**Outcome:** *(pending)*
