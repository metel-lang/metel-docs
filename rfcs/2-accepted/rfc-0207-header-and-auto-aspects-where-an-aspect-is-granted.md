---
id: rfc-0207
title: "Header and Auto Aspects — Where an Aspect Is Granted"
date: '2026-11-02'
status: accepted
updated: '2026-11-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/1786'
---

> **Extracted from RFC-0162 on 2026-11-02**, at the language owner's request, the way RFC-0206
> was extracted from RFC-0080. RFC-0162 keeps the `Copy`/`Clone` model and its position that a
> named type states copyness in its declaration; this RFC owns the *mechanism* that position
> uses, which is not specific to `Copy`: where an aspect may be granted, what the compiler derives
> for it, and how a type's declaration says so.

> **Status — accepted (2026-11-02).** Accepted with RFC-0162 and RFC-0206 as one set; tracking
> metel-core#1786. The first implementation (v0.16.0) covers the two modifiers, the `derives`
> clause and the colon list, native derivations, and the coherence rules; the templates of RFC-0209
> to RFC-0211 and the later stage are separate.

## Summary

An aspect is today granted one way, by an `extend` block anywhere in the type's module. This RFC
separates two properties of an aspect and gives each a declaration modifier:

1. **Position.** A `header` aspect is granted only in a type's declaration, so the declaration is
   the single place to look. An aspect that is not `header` can be written with `extend` as
   today. This is the visibility guarantee, and it covers only `header` aspects.
2. **Derivation.** A `derivable` aspect has a derivation: the compiler checks and generates the
   implementation. A type requests it with a `derives` clause. An aspect that is not `derivable`
   is only ever written by hand or, if `header`, recorded as a promise.

The properties compose. `Copy` is both: it is granted only in the declaration, and its entry
checks every field and generates the sealed `clone` (RFC-0206 §2).

```metel
header derivable aspect Copy;                            // struct Point derives Copy
derivable aspect Clone { fun clone(&self) -> Self; }     // struct Doc derives Clone, or extend Clone { … }
header aspect Validated;                                 // struct Order: Validated  (a promise; no derivation)
auto aspect Send;                                        // struct Token: !Send      (opt-out)
aspect Drop { … }                                        // extend only
```

Two clauses in the type's declaration:

- **`derives A, B`** lists what the compiler derives: every `derivable` aspect, `Copy` included.
- **`: X`** lists promises (a `header` aspect with no derivation) and opt-outs (`: !Send`).

`extend A { … }` stays the explicit implementation, and derivation is always explicit: a type
with neither a `derives` entry nor an `extend` does not have the aspect.

## Motivation

RFC-0162 (D6) argues that `Copy` is a grant whose effect, a change in what every use of the
type means, is out of proportion to where it is written: a bodyless `extend T: Copy;`
anywhere in the module. Its answer is to move the grant onto the declaration. Working that out
produced a mechanism that is not about `Copy`: a rule for where an aspect may be granted, a
rule for what the compiler derives, and a place in the declaration for both. It overlaps
RFC-0096 (auto-impl aspects), RFC-0102 (bodyless `extend`), RFC-0105 (aspect lists in
declarations) and RFC-0093 (derive registration). Settling those inside a `Copy`/`Clone` model
RFC buried them, and gave `Clone`, `!Send` and any future marker no home. They get one here.

---

## The two clauses (from RFC-0162 C4)

> Added 2026-11-02 at the language owner's request, as a competitor to C2. The colon list is the
> shape the draft RFC-0105 (`struct Token: Copy2, Serializable, !Send { … }`) proposed for
> aspect lists in general.

**The idea.** A type's declaration names, after its name, the facts about it that are stated
there. Two clauses carry two different statements:

- `derives Copy, Clone` says the compiler establishes these aspects for the type: it checks the
  fields against each aspect's eligibility rule and generates the implementation (for `Copy`,
  the sealed `clone`). The aspect must be `derivable`.
- `: Validated, !Send` says the type promises an aspect that has no derivation, or opts out of an
  `auto` aspect. A positive item is the grant, the same fact a bodyless `extend T: Validated;`
  states today. A negative item (`!Send`) denies, as a bodyless negative `extend` does
  (RFC-0102, RFC-0081).

**What it changes against C2.**

- **The stop rule (D6.3) has a principled answer.** C2 moves `Copy` to a keyword and leaves
  `Drop`, `Send` and `Sync` as aspects, and has to say why. Here the boundary is a property of the
  aspect: *a `header` aspect is granted only in the declaration; every other aspect is written or
  derived like any impl.* `Copy` is `header`; `Drop` is not, because its behaviour is written.
  No aspect is special-cased.
- **`Copy` stays an aspect and a bound.** Nothing about `T: Copy`, `Copy ⇒ Clone`, the conditional
  rules or coherence changes. The grant's location moves, as in C2.
- **The derive hazard is closed by the position.** A `derives Copy` entry is in the header, where
  the hazard of RFC-0162's D6.2 (a derive hidden away from the declaration) cannot occur. `Copy`'s
  derivation is fixed by std; a user cannot register another deriver for it.
- **Visibility.** `copy struct P` puts a modifier before the keyword; `struct P derives Copy`
  puts the fact after the name. Both are in the declaration, and a clause scales to several facts
  (`derives Copy, Debug`) where a keyword does not.
- **Vocabulary.** Axis S spelled copyness on structural types as a qualifier; RFC-0212 carries
  that question. For named types the clause is `derives` for what the compiler establishes and
  `:` for promises and opt-outs.

**Spelling and direction (language owner, 2026-11-02).** `derives` is the spelling for anything the
compiler generates or checks; the colon list is for promises and opt-outs. The expected later
stage is that the colon list also accepts aspects with methods, with their methods written in
the body and qualified by aspect (`fun Display::fmt(&self, …)`, unqualified meaning inherent),
so the declaration becomes a type's complete capability list:
`struct Doc: Display derives Clone, Debug`. This design is compatible with that stage and does
not require it; nothing in either clause changes meaning when it arrives.

---

## Refinable header grants

A pure header list cannot express a condition the compiler cannot derive. The restriction can be
relaxed without losing its invariant, which is: **a named type has a `header` aspect only if its
declaration says so.** An `extend` of a `header` aspect is legal in exactly three situations and
an error otherwise (with a fix-it):

1. *It refines a header grant.* The declaration already names the aspect (`struct W<T> derives
   Copy`), and the `extend` supplies the condition: `extend<T: Marker> W<T>: Copy;`. Without an
   `extend`, the condition is derived from the fields (R1, accepted for the first
   implementation: every type parameter that occurs in a field must be `Copy`; RFC-0209's exact
   condition R2 is the intended outcome and accepts everything R1 accepts; where R1 is too
   strict, as for `struct W<T> { r: &T }`, this `extend` widens it). With one, the `extend` wins,
   and must still satisfy the aspect's eligibility check, as `check_copy_impl_eligibility` does
   today.
2. *It is a negative impl.* `extend<T> W<T>: !Copy where T: Marker;` denies and grants nothing.
3. *The target has no declaration, and the `extend` is in the aspect's defining module.* This is
   the structural impl: std's `extend<record R> { ..R }: Copy where ..R: Copy;` (RFC-0123), and
   for a user header aspect `extend<record R> { ..R }: Pod where ..R: Pod;`. The orphan rule keeps
   it with the aspect's author, and a named type can never be granted this way, because it has
   a declaration. See "Targets with no declaration".

An `extend T: Copy;` for a type whose declaration does not name `Copy` is rejected, so neither a
deriver nor a distant `extend` can make a type `Copy` silently. The check is module-local, not
whole-graph: `Copy` is a std aspect, so the orphan rule (`T0014`) already puts the grant in the
type's own module, which is where the declaration is. The cost is that a conditional type can
have two places, the declaration and an optional refining `extend`. Refinement applies to `header`
aspects only: a `derives` entry for an aspect that is not `header` has an exact condition
(RFC-0209, R2), so a second impl for it is an overlap, not a refinement.

**Targets with no declaration (decided 2026-11-02).** The third situation covers two kinds of
target, and both are written impls, not a compiler rule and not inference:

- *Primitives* (`i64`, `boolean`, `Char`, `()`, `String`). std grants them with `extend` today
  because they have no declaration. This is transitional: when std declares them as primitive
  structs they take a `derives Copy` entry like any named type and this case disappears for them.
- *Structural kinds* (tuples, `[T; N]`, anonymous records). They will never have a declaration,
  and their grants are impls in the aspect's module, written with the field-wise bound of
  RFC-0123 (`where ..R: Copy`) for records, a compile-time `N` for arrays (RFC-0132 §3, which
  RFC-0124 records as the answer to #263), and variadic generics for tuples (#794, RFC-0061 §6).
  Until those prerequisites land the array and tuple arms stay hardcoded in the checker, as today;
  this RFC does not remove that wait. `&T`, `&var T`, the `[T]` view, function types and closures
  are built-in facts of the type system (`&T` always `Copy`, `&var T` never, a closure by its use
  multiplicity), not grants anyone writes.

A user `header` aspect can opt in to the same coverage by writing the structural impls itself,
which keeps every grant explicit and in one module; nothing is inferred for it. The `comptime for`
of RFC-0174 does not grant anything: it produces a body, such as the field-wise `clone` behind
`struct P derives Clone` (RFC-0206 §4(c)), a native hook today and a loop over the fields later.

The consequence is that a `header` aspect cannot be granted to a named type you do not own (its
declaration is closed), nor to a primitive or structural type from outside the aspect's module.
An aspect meant to be granted by other people to such targets is not `header`.

---

## Modifiers and grant modes (from RFC-0162 C5)

> Added 2026-11-02 at the language owner's request, as the question "could the language enforce
> the position in which an aspect is granted?". It decides C2 against C4 once and for the other
> aspects too.

**The idea.** An aspect's declaration states how it is granted and whether it has a derivation,
and the coherence pass (RFC-0060) enforces both; a grant in the wrong position is an error with a
fix-it.

| Declaration | Granted by | Clause | Examples |
|---|---|---|---|
| `aspect X` (default) | `extend` only | none | `Drop`, user aspects |
| `derivable aspect X` | `extend`, or the derivation | `derives` | `Clone`, `Debug`, `Display` |
| `header derivable aspect X` | the derivation, in the declaration only | `derives` | `Copy` |
| `header aspect X` | a promise, in the declaration only | `:` | a user `Validated` |
| `auto aspect X` (std only) | structurally; opt-out in the declaration | `: !X` | `Send`, `Sync`, `Linear` (RFC-0096) |

```metel
header derivable aspect Copy;                            // derives Copy   (sealed; implies a sealed Clone)
derivable aspect Clone { fun clone(&self) -> Self; }     // derives Clone, or extend Clone { … }
header aspect Validated;                                 // : Validated    (an unchecked promise)
auto aspect Send;                                        // : !Send        to opt out
aspect Drop { … }                                        // extend only
```

The keywords are sketches; the spelling is open to the implementation's review of the grammar.

**Rules.**
1. *The declaration decides the clause.* `derives X` is legal exactly when `X` is `derivable`; `: X`
   is legal exactly when `X` is `header` and not `derivable`; `: !X` exactly when `X` is `auto`. A
   wrong clause is an error with a fix-it naming the right one.
2. *A `header` aspect without a derivation has no methods* (checked at the declaration): its entry
   is a promise, and nothing could implement a method. A `derivable` aspect with methods carries a
   derivation, which is checked at the declaration.
3. *A plain methodless aspect stays `extend`-only.* `aspect Marker {}` is granted by a bodyless
   `extend` (RFC-0102) as today; `header aspect` is the opt-in to the single-place form. Without
   the opt-in a marker would have two ways to be granted.
4. *A `derivable` aspect that is not `header` may be written by hand.* A type with no `derives
   Clone` can `extend Clone { … }`. A type with both is a coherence overlap error.
5. *`auto` takes only negative entries.* A positive `: Send` is an error, because an auto aspect
   holds without being granted. `auto` is std's.
6. *Sealing.* `Copy implies Clone` is a sealed blanket `extend` in std for a `derivable` aspect; the
   coherence rule that rejects a second `Clone` on a `Copy` type is what seals it, so `derives
   Copy` with `derives Clone` (or an `extend Clone`) is an error with no extra rule.
7. *The visibility guarantee.* It is a property of position: only a `header` aspect can be granted
   only in the declaration. `derivable` gives explicit derivation, not visibility, so a hand-written
   `extend Cache: Clone` elsewhere in the module is not visible at the declaration. That is
   deliberate: a `Clone` impl changes no other code's meaning, because someone has to call it. The
   guarantee for every aspect is the later stage.

**`Copy`.** `Copy` is `header derivable`. Its derivation checks every field against the eligibility
rule ("every field must implement `Copy`", today's `check_copy_impl_eligibility`), derives the
generic condition (R1), and supplies the sealed `clone` through the `Copy ⟹ Clone` blanket. The
same applies to std aspects with a recognised rule (RFC-0096's `Send`/`Sync`/`Linear`, which are
`auto`). It is not a special case: it is a `header derivable` aspect whose derivation std defines.

**User-declared aspects (decided 2026-11-02).** `header` and `derivable` are user-declarable;
`auto` stays std's.

- *A user `header` aspect without a derivation is a promise.* `struct Order: Validated { … }`
  grants it, and it works as a bound (`fun f<T: Validated>(x: T)`). The entry is the author's
  claim: the compiler does not check it against the fields, and a user aspect has no inferred
  satisfaction: a structural type satisfies it only if the aspect's author wrote the impl for that
  kind, and a generic type states its condition in a refining `extend`. This matches the surveyed
  languages: inference from parts is built into the compiler's own aspects (Rust's `Send`/`Sync`,
  Swift's `Sendable`, Go's `comparable`), and a user marker's field check is library code in the
  declaration (Scala `derives`, Haskell `deriving`, Rust `#[derive(Pod)]`) or an unchecked promise
  (`unsafe impl`).
- *A user `derivable` aspect* supplies a derivation (RFC-0209 templates now, comptime later), so a
  user `header derivable` aspect gets a checked entry; this is how a checked user marker arrives
  (RFC-0209).
- *Negative entries are for `auto` aspects.* For a `header` aspect, not granted is the default, so
  `!Validated` says nothing and is an error.
- *`auto` stays std's.* A user-declared `auto` aspect would let users make a property hold with no
  grant, the invisible behaviour D1 objects to; a `header` entry is written on the declaration, so
  that objection does not apply to `header`.

**What it settles**

- **The stop rule (D6.3).** The aspect states where it is granted, so there is nothing to argue
  about why only `Copy` moved; `Drop` is plain because its behaviour is written.
- **C2 against C4.** The mandatory location is the `header` modifier; the modifier on the keyword
  (`copy struct`) or the clause (`derives Copy`) is only how it is written, chosen on readability.
- **The derive hazard.** A `header` aspect has no `extend` form, so a deriver has no impl to emit
  away from the declaration.
- **Where a grant may live.** A header grant is in the type's own module, so the orphan rule
  (`T0014`) holds trivially; the foreign-type case stays rejected.

**Worked examples**

1. *`extend Point: Copy;`* under the modifiers: error, "`Copy` is granted in the type's
   declaration"; the fix-it moves it to `derives Copy`.
2. *`struct H: Drop`* (a plain aspect after the colon): error, "`Drop` is granted with `extend`".
   `struct H: Clone` is an error pointing at `derives Clone`; `struct H derives Validated` is an
   error pointing at the colon.
3. *`struct Token: !Send`* on an `auto` aspect: the opt-out, as RFC-0105 first proposed, with
   `Send` otherwise holding because every field is `Send`.
4. *A user marker* (`aspect Marker {}`): `extend`-only, so unchanged; declaring it `header aspect`
   makes it a promise granted after the colon instead.
5. *A user header promise:* `struct Vec3: Pod { x: f64, y: f64, z: f64 }` is accepted without a
   field check, and `struct Id: Pod { s: String }` is accepted too (the author's claim).
   `(Vec3, i64)` does not satisfy `Pod` unless the author writes a tuple impl,
   `extend<record R> { ..R }: Pod where ..R: Pod;` covers anonymous records, and `struct W<T>: Pod`
   needs a refining `extend<T: Pod> W<T>: Pod;` to be conditional. `derives Copy`, by contrast, is
   checked field by field.
6. *A header aspect on a foreign type:* `extend lib::Point: Pod;` is an error, because the type's
   declaration is closed; the fix-it points at a plain `aspect` for the case.
7. *`struct T: !Validated`* on a `header` aspect: an error ("`Validated` is not granted by
   default; remove the entry").
8. *Derive and write:* `struct Doc derives Clone { … }` plus `extend Doc: Clone { … }` is an
   overlap error; `struct Cache { … }` with only the `extend` is fine, and the declaration does not
   show it (rule 7).
9. *`Copy` with `Drop`:* `struct H derives Copy` with `extend H: Drop { … }` is rejected at the
   declaration, with the same message C2 gave.
10. *Std's primitives and structural kinds:* `extend i64: Copy;` until std declares primitives as
    structs; `extend<record R> { ..R }: Copy where ..R: Copy;` for anonymous records; the tuple and
    array arms hardcoded until variadic generics and a compile-time `N`. All sit in the aspect's
    defining module, by the third situation.

**Costs and risks**

- Two modifiers and two clauses are more to learn than one. User aspects default to plain `aspect`
  and stay exactly as today unless their author opts in.
- A reader must know whether an aspect is `derivable` or a promise to pick the clause; the error
  and fix-it are the mitigation, and the common aspects are all `derives`.
- A `header` aspect cannot be granted to a type you do not own, which `extend` can (the orphan
  rule only needs the aspect or the type to be local). The aspect's author picks the modifiers with
  that in mind.
- RFC-0096's compiler-recognized auto-impl set would become declared properties, which changes an
  under-review RFC; RFC-0105 is narrowed now and carries the later stage.
- The visibility guarantee covers `header` aspects only (rule 7); extending it to every aspect is
  the later stage.

**What would decide it.** The modifiers are worth their weight if more than `Copy` benefits from an
enforced grant position (`Send`/`Sync`/`Linear`, future markers, derivable aspects) or if the stop
rule cannot otherwise be stated. If `Copy` is the only aspect that ever needs it, C2 is the
smaller change.

---

## Blanket impls, derivation and comptime

**Where a blanket impl over a type's fields stands.**

| Target | A blanket conditional on the fields | How |
|---|---|---|
| anonymous record | yes, automatic | `extend<record R> { ..R }: A where ..R: A` (RFC-0123); a record has no declaration to opt in with |
| `struct`, `enum`, named `record` | no blanket, only an opt-in | a `derives` entry (this RFC) makes the type's row visible to the aspect's template (RFC-0209, RFC-0210) |
| a generic type, conditional on its parameters | yes | an ordinary conditional impl, `extend<T: Foo> Wrapper<T>: Foo` |

There is deliberately no blanket impl over every struct. A type would gain behaviour it never
declared, which is the invisible effect that RFC-0137 and RFC-0162 object to. A user who wants one
anyway has the opt-in: name the aspect after `derives`. A blanket with no opt-in exists only as an
`auto` aspect, which is std's.

**What comptime adds.** A `derives` entry runs the aspect's derivation. For an aspect that has one
`{ ..R }` template (or one `enum E` template, RFC-0210), that is the template. Comptime (RFC-0092
`typeinfo` and `emit`, RFC-0093 derive registration, RFC-0174 `comptime for`) covers the rest:

1. **Template bodies.** The field-wise body of a template is a loop over the fields or variants, a
   native hook until RFC-0174 lands.
2. **Derivable aspects with several methods.** A `derivable aspect` supplies a comptime derivation
   in place of a single template: it can generate several methods, read field names and types, and
   emit extra items. `Display` and `Debug` are the typical cases.
3. **Conditions a template cannot state.** A derivation can generate an impl whose condition is not
   a field-wise bound, for example one that depends on a field's attribute. The gate stays: the
   type names the aspect after `derives`.

**The `#derive` attribute.** RFC-0093 specifies `#derive(Aspect)` as both a request on a struct or
enum and a registration on the comptime function that implements the derive. The `derives` clause
is the request in this RFC, so the two cannot both be the surface for the same thing. The
`derives` clause replaces the request half and the `derivable` declaration replaces the
registration half: the aspect states that it has a derivation, and names it, so no separate
attribute or registry is needed. RFC-0093 is narrowed to what a comptime derivation needs.

---

## Relationship to existing RFCs

- **RFC-0162** — the `Copy`/`Clone` model; its position C4 is the `derives Copy` entry of a
  `header derivable` aspect, and its alternative C2 (`copy struct`) is a spelling of the same grant.
- **RFC-0206** — `Clone`; its §4(c) derives a `Clone` body from a `derives` clause.
- **RFC-0105** — the draft this narrows: aspect lists in declarations. Its full model is the later
  stage described in "Spelling and direction".
- **RFC-0096** — the auto-impl set (`Send`, `Sync`, `Linear`) that `auto` makes a declared property.
- **RFC-0209 / RFC-0210 / RFC-0211** — the templates a `derives` entry runs, for products, enums and
  residuals.
- **RFC-0092 / RFC-0093 / RFC-0174** — comptime, derive registration and compile-time iteration; see
  "Blanket impls, derivation and comptime".
- **RFC-0212** — markers on structural types.
- **RFC-0102 / RFC-0081** — bodyless and negative `extend`, which remain the form of a promise
  outside the declaration, a refinement and std's own grants.
- **RFC-0060** — the coherence pass that enforces the modifiers; **RFC-0097** — the orphan rule the
  header grant satisfies trivially.

## Spellings and deferrals fixed at acceptance

1. **Spelling.** The modifiers `header` and `derivable` (composable), `auto`, the `derives` clause
   and the colon list, and the clause order (the colon list first, then `derives`), are accepted.
   The keyword combination for `Copy` (`header derivable aspect`) is accepted as written.
2. **User aspects.** `header` and `derivable` are user-declarable; `auto` stays std's, the closed
   set of RFC-0096 (`Send`, `Sync`, `Linear`).
3. **`#derive`.** The `derives` clause replaces the request half of RFC-0093's `#derive(Aspect)`
   and the `derivable` declaration replaces its registration half. RFC-0093 is narrowed when it is
   integrated.
4. **RFC-0096 and RFC-0105.** RFC-0096's recognised-set text is updated for declared `auto`
   aspects, and RFC-0105 is narrowed to the later stage below, at integration. Both carry a pointer
   note to this RFC.
5. **`Copy`'s structural cases** are written impls in the aspect's module (RFC-0123 records, a
   compile-time `N` for arrays, variadic generics for tuples; hardcoded until then), not
   auto-impls.
6. **The visibility guarantee** covers `header` aspects (rule 7 above).

**Deferred, with homes.**

- *Method-bearing aspects after the colon*, conditional written impls, associated items; and the
  visibility guarantee for every aspect: RFC-0105.
- *A checked user marker*, a field check stated in the declaration: RFC-0209.
- *Inference for non-public types* (Swift's `Sendable` rule): RFC-0096, which owns when inference
  is allowed.
- *Markers on structural types*: RFC-0212.
- *The exact generic condition* (R2), residual and enum templates: RFC-0209, RFC-0210, RFC-0211.

---

## Decision

**Outcome:** accepted 2026-11-02 (language owner), with RFC-0162 and RFC-0206 as one set.

**Accepted:** the `header` and `derivable` modifiers and the `auto` kind; the `derives` clause for
derivations (`Copy` included) and the colon list for promises and opt-outs; derivation always
explicit; user header aspects as promises; structural coverage as written impls in the aspect's
module; the refinement and negative-impl rules; the coherence rules (including sealing); the
visibility guarantee scoped to `header` aspects; the spellings above.

**Deferred, with homes:** see the previous section.

**Target:** v0.16.0 (metel-core#1786).
