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
> uses, which is not specific to `Copy`: a type's header listing marker facts, an `extend`
> that may only refine such a grant, and aspects that declare how they are granted.

> **Status — accepted (2026-11-02).** Accepted with RFC-0162 and RFC-0206 as one set; tracking metel-core#1786. The first implementation (v0.16.0) covers the declaration kinds, the colon list for markers, the `derives` clause with native derivations, and the coherence rules; the templates of RFC-0209 to RFC-0211 and the later stage are separate.

## Summary

An aspect is today granted one way, by an `extend` block anywhere in the type's module. This RFC
proposes further positions, and a declaration that says which an aspect uses. The clause that
grants an aspect depends on what the aspect is:

1. **Marker aspects, after the colon.** A type declaration lists aspects with no methods after
   its name (`struct Point: Copy { … }`, `struct Token: !Send { … }`). A positive item is the
   grant itself; a negative item (`!Send`) denies it. An `extend` of the same aspect is legal only
   to refine the grant, as a negative impl, or for a target with no declaration (a structural
   kind, or a primitive until it has one), and then only in the module that defines the aspect.
   A marker aspect may be declared in user code (`marker aspect Validated;`); its entry is the
   author's promise.
2. **Derivable aspects, after `derives`.** A `derivable aspect` has methods and a derivation: a
   type requests the derivation with a `derives` clause (`struct Doc derives Clone, Debug { … }`),
   and the compiler generates the methods. The aspect may also be written by hand with `extend`.
3. **Auto aspects.** An aspect granted structurally with no grant at all (`Send`, `Sync`,
   `Linear`, RFC-0096), which a type opts out of with a negative item (`: !Send`). std only.
4. **Declaration kinds.** Each aspect is declared `aspect` (granted by `extend` only, as today),
   `marker aspect`, `derivable aspect` or `auto aspect`. The declaration decides the clause, and a
   grant in the wrong position is an error with a fix-it.

The colon says what the type *is* (marker facts); `derives` says what the compiler *writes* for
it. RFC-0162 uses a marker aspect for `Copy` (its position C4); RFC-0206 uses `derives` for
`Clone` on a user type (its §4, option (c)). Both are accepted with this RFC.

## Motivation

RFC-0162 (D6) argues that `Copy` is a grant whose effect, a change in what every use of the
type means, is out of proportion to where it is written: a bodyless `extend T: Copy;`
anywhere in the module. Its answer is to move the grant onto the declaration. Working that out
produced a mechanism that is not about `Copy`: it needs a rule for which aspects may be named
in a header, for what an `extend` of such an aspect may still do, and for how an aspect says
where it is granted, and it overlaps RFC-0096 (auto-impl aspects), RFC-0102 (bodyless
`extend`) and RFC-0105 (aspect lists in declarations). Settling those inside a `Copy`/`Clone`
model RFC buried them, and gave `Clone`, `!Send` and any future marker no home. They get one
here.

---

## Marker entries after the colon (from RFC-0162 C4)

> Added 2026-11-02 at the language owner's request, as a competitor to C2. It is the shape
> the draft RFC-0105 (`struct Token: Copy2, Serializable, !Send { … }`) proposed for aspect
> lists in general, restricted to the case `Copy` needs.

**The idea.** A type declaration may list marker aspects after its name. For an aspect that
declares no required methods, `Copy` among them, a positive item is a grant, the same fact a
bodyless `extend T: Copy;` states today. A negative item (`!Send`) denies, exactly as a
bodyless negative `extend` does (RFC-0102, RFC-0081). An aspect with methods is not
listed after the colon: a derived one uses `derives` (below) and a written one uses `extend`.
Listing method-bearing aspects after the colon, RFC-0105's obligation model, is a possible later
stage that this design leaves room for (see "Spelling and direction").

**What it changes against C2.**

- **The stop rule (D6.3) has a principled answer.** C2 moves `Copy` to a keyword and leaves
  `Drop`, `Send` and `Sync` as aspects, and has to say why. C4's boundary is a class: *marker
  facts about a type are declared on the type; behaviour is implemented in `extend`*. `Copy`
  is a marker; `Drop` is not (it has a method); `Send`/`Sync`/`Linear` are markers, and RFC-0096
  already treats them as structural, with `!Send` the opt-out. No aspect is special-cased.
- **`Copy` stays an aspect and a bound.** Nothing about `T: Copy`, `Copy ⇒ Clone`, the
  conditional rules or coherence changes. The grant's location moves, as in C2.
- **The derive hazard is not closed by the mechanism.** C2 has no impl to emit; C4 has a
  header entry a deriver could add. In practice `#derive(Copy)` would be no shorter than
  `: Copy`, so it would add nothing, and RFC-0162's question 5, the written rule ("`Copy` has no deriver")
  covers it. This is closed by policy and not by construction, which is a real difference.
- **Visibility.** `copy struct P` puts a modifier before the keyword; `struct P: Copy` puts
  the fact after the name, before any generics' `where`. Both are in the header. A modifier is
  harder to miss; a list scales to several facts (`: Copy, !Send`) where a keyword does not.
- **Conditional grants.** The derived condition (RFC-0162's R1) is a rule of `Copy`'s eligibility
  check (every field must be `Copy`), not of marker aspects in general: for a plain user
  marker `struct W<T>: Marker`, there is no field-wise rule to derive from. So under C4 the
  derived-condition rule would belong to a named class, the aspects with a structural
  eligibility rule (`Copy`, and RFC-0096's `Send`/`Sync`/`Linear`), and any other marker
  grant is unconditional or keeps `extend<T: X> W<T>: Marker;`.
- **Vocabulary.** Axis S spells copyness on structural types as a qualifier (`copy`,
  `once`); C4 spells it on named types as an aspect (`: Copy`). Two forms of one fact. C2
  has one word throughout.
- **Cost and dependency.** It adds a clause to type-declaration grammar, and depends on
  RFC-0105 (a `0-draft` that was deferred as "a materially larger surface-language
  commitment") being narrowed to markers and moved forward, or on this RFC absorbing the
  marker-only subset. The obligation check and the registry-injection question RFC-0105 raises do
  not arise for markers, because there is no `extend` to find.

**Spelling and direction (language owner, 2026-11-02).** `: Copy` is the spelling for a marker
because it mirrors the `extend T: Copy` block it replaces. `derives` is the spelling for a
derivation. The two clauses are chosen by what the aspect is, not by taste: markers after the
colon, method-bearing derived aspects after `derives`. The expected later stage is that the
colon list also accepts method-bearing aspects, with their methods written in the body and
qualified by aspect (`fun Display::fmt(&self, …)`, unqualified meaning inherent), so the
header becomes a type's complete capability list: `struct Doc: Display derives Clone, Debug`. This
design is compatible with that stage and does not require it; nothing in the colon list changes
meaning when it arrives.

**Refinable marker grants (added 2026-11-02).** A pure header list cannot express a
condition the compiler cannot derive. The restriction can be relaxed without losing its
invariant, which is: **a named type is `Copy`-capable only if its header says so.** An
`extend` of the aspect is legal in exactly three situations and an error otherwise (with a
fix-it):

1. *It refines a header grant.* The header already names the aspect (`struct W<T>: Copy`),
   and the `extend` supplies the condition: `extend<T: Marker> W<T>: Copy;`. Without an
   `extend`, the condition is derived from the fields (R1, accepted for the first implementation; RFC-0209's exact condition R2 is the intended outcome and accepts everything R1 accepts: every type parameter that occurs
   in a field must be `Copy`; R2, the weakest sufficient condition, needs a solver and is not
   taken; where R1 is too strict, as for `struct W<T> { r: &T }`, this `extend` widens it). With one, the `extend` wins, and must still satisfy the aspect's
   eligibility check, exactly as `check_copy_impl_eligibility` does today.
2. *It is a negative impl.* `extend<T> W<T>: !Copy where T: Marker;` denies and grants
   nothing.
3. *The target has no declaration, and the `extend` is in the aspect's defining module.* This
   is the structural impl: std's `extend<record R> { ..R }: Copy where ..R: Copy;`
   (RFC-0123), and for a user marker aspect `extend<record R> { ..R }: Pod where ..R: Pod;`.
   The orphan rule keeps it with the aspect's author, and a named type can never be granted
   this way, because it has a header. See "Targets with no declaration".

An `extend T: Copy;` for a type whose header does not name `Copy` is rejected, so neither a
deriver nor a distant `extend` can make a type `Copy` silently. This is RFC-0105's obligation
model, header as promise and `extend` as detail, applied to markers only. The check is
module-local, not whole-graph: `Copy` is a std aspect, so the orphan rule (`T0014`) already
puts the grant in the type's own module, which is where the header is. The cost is that a
conditional type can have two places, the header and an optional refining `extend`, and that
a deriver may emit the refining `extend`, though only for a type whose header already names
`Copy`. In the terms of the declaration kinds below this is a *refinable* marker aspect. Refinement
applies to marker aspects only: a `derives` entry has an exact condition (RFC-0209, R2), so a
second impl for it is an overlap, not a refinement.

**Targets with no declaration (decided 2026-11-02).** The third situation above covers two
kinds of target, and both are written impls, not a compiler rule and not inference:

- *Primitives* (`i64`, `boolean`, `Char`, `()`, `String`). std grants them with `extend`
  today because they have no declaration. This is transitional: when std declares them as
  primitive structs they take a header entry like any named type and this case disappears
  for them.
- *Structural kinds* (tuples, `[T; N]`, anonymous records). They will never have a
  declaration, and their grants are impls in the aspect's module, written with the field-wise
  bound of RFC-0123 (`where ..R: Copy`) for records, a compile-time `N` for arrays (RFC-0132
  §3, which RFC-0124 records as the answer to #263), and variadic generics for tuples (#794,
  RFC-0061 §6). Until those prerequisites land the array and tuple arms stay hardcoded in the
  checker, as today; this RFC does not remove that wait. `&T`, `&var T`, the `[T]` view,
  function types and closures are built-in facts of the type system (`&T` always `Copy`,
  `&var T` never, a closure by its use multiplicity), not grants anyone writes.

A user marker aspect can opt in to the same coverage by writing the structural impls itself,
which keeps every grant explicit and in one module; nothing is inferred for it. The
`comptime for` of RFC-0174 does not grant anything: it produces a body, such as the
field-wise `clone` behind `struct P derives Clone` (RFC-0206 §4(c)), which is a native hook
today and a loop over the fields later.

The consequence is that a marker aspect cannot be granted to a named type you do not own (its
header is closed), nor to a primitive or structural type from outside the aspect's module. An
aspect meant to be granted by other people to such targets uses `extend` mode.

**Worked examples** (reasoned; C1 is today's `extend`, C2 is the `copy` keyword alternative kept in RFC-0162):

1. *Adding a field* (`name: String` to a `Copy` struct): C1 errors at the `extend` line, C2
   and C4 at the declaration, next to the field.
2. *Reading the declaration:* C2 `copy struct P`, C4 `struct P: Copy`; both visible. C4 also
   shows `struct P: Copy, !Send` in one place.
3. *Conditional grant, `Holder<T>`, phantom `Witness<T>`:* both derive the condition from the
   fields, C2 by the keyword and C4 by `Copy`'s eligibility rule.
4. *A user marker* (`marker aspect Marker;`, `struct Token: Marker`): C2 does not apply; C4
   grants it, unconditionally, with no `extend`.
5. *`Drop`:* `struct H: Copy` with `extend H: Drop { … }` is rejected at the declaration under
   both, with the same message as C2's.
6. *A derive:* closed by construction under C2, by the written rule under C4, and by the
   header requirement for the refining `extend` (above).
7. *A condition on another aspect* (`extend<T: Marker> Witness<T>: Copy`, used by a
   coherence fixture): inexpressible under C2 and under a pure header list; under refinable
   header grants it is `struct Witness<T>: Copy { … }` plus that `extend`.
8. *std's own grants:* `extend i64: Copy;` and the record rule stay as `extend`, by case 2,
   with no exemption to invent.

**What would decide it.** If the only grant ever moved is `Copy`, C2 is smaller and closes
the derive hazard by construction. If the language wants one place for all marker facts
(including `!Send`, and any future marker), C4 generalises and answers D6.3 without an
exception, at the price of a larger grammar change, an RFC-0105 dependency and two forms of
copyness across named and structural types.

---

## Declaration kinds and grant modes (from RFC-0162 C5)

> Added 2026-11-02 at the language owner's request, as the question "could the language
> enforce the position in which an aspect is granted?". It decides C2 against C4 once and for the
> other aspects too.

**The idea.** An aspect's declaration states how it is granted, and the coherence pass (RFC-0060)
enforces it; a grant in the wrong position is an error with a fix-it.

| Declaration | Methods | Granted by | Clause | Examples |
|---|---|---|---|---|
| `aspect X` (the default) | either | `extend` only, as today | none | `Drop`, user aspects |
| `marker aspect X` | none (checked) | the header; an `extend` is an error except to refine | `:` | `Copy`, a user `Validated` |
| `derivable aspect X` | yes, with a derivation | `extend`, or the compiler's derivation | `derives` | `Clone`, `Debug`, `Display` |
| `auto aspect X` (std only) | none | structurally, with a header opt-out | `: !X` | `Send`, `Sync`, `Linear` (RFC-0096) |

```metel
marker aspect Copy;                                      // : Copy       (sealed; implies a sealed Clone)
marker aspect Validated;                                 // : Validated  (an unchecked promise)
derivable aspect Clone { fun clone(&self) -> Self; }     // derives Clone, or extend Clone { … }
auto aspect Send;                                        // : !Send      to opt out
aspect Drop { … }                                        // extend only
```

The keywords are sketches; the spelling is open (question 1).

**Rules.**
1. *The declaration decides the clause.* A marker aspect after `derives`, or a method-bearing
   aspect after the colon, is an error with a fix-it naming the right clause. A `marker aspect`
   must have no methods and a `derivable aspect` must have methods and a derivation, which is
   checked at the declaration.
2. *A plain methodless aspect stays `extend`-only.* `aspect Marker {}` is granted by a bodyless
   `extend` (RFC-0102) as today; `marker aspect` is the opt-in to granting in the header. Without
   the opt-in a marker would have two ways to be granted.
3. *A `derivable` aspect may still be written by hand.* A type with no `derives Clone` can
   `extend Clone { … }`. A type with both is a coherence overlap error.
4. *`auto` takes only negative entries.* A positive `: Send` is an error, because an auto aspect
   holds without being granted. `auto` is std's.
5. *Sealing.* `Copy implies Clone` is a sealed blanket `extend` in std for a `derivable` aspect;
   the coherence rule that rejects a second `Clone` on a `Copy` type is what seals it.

**Marker aspects.** A `marker aspect` has no methods. `Copy` additionally has an eligibility
check, "every field must implement it", which is today's `check_copy_impl_eligibility`; the
condition of a generic grant belongs to that check, and is available to std aspects that have
one (`Copy`, and RFC-0096's `Send`/`Sync`/`Linear`) and not to user aspects yet.

**User-declared marker aspects (decided 2026-11-02).** Marker aspects are not restricted to std.

- *Markers only.* The grant is a header entry (`struct Order: Validated { … }`) and the aspect
  works as a bound (`fun f<T: Validated>(x: T)`). The compiler gives it no semantics beyond the
  position; the compiler-recognised aspects (`Copy`, `Send`, `Sync`, `Linear`) stay std's.
- *The entry is the author's promise.* The compiler does not check it against the fields, and a
  user aspect has no inferred satisfaction: a structural type satisfies it only if the aspect's
  author wrote the impl for that kind (see "Targets with no declaration"), and a generic type
  states its condition in a refining `extend`. This matches how the surveyed languages treat user
  markers: inference from parts is built into the compiler's own aspects (Rust's `Send`/`Sync`,
  Swift's `Sendable`, Go's `comparable`), and a user marker's field check is library code in the
  declaration (Scala `derives`, Haskell `deriving`, Rust `#[derive(Pod)]`) or an unchecked promise
  (`unsafe impl`). A checked user marker could reuse RFC-0123's field-wise bound in the aspect's
  declaration (question 5), or come from the later stage in which the colon list carries
  derivations (question 3).
- *Negative entries are for `auto` aspects.* For a marker aspect, not granted is the default, so
  `!Validated` says nothing and is an error.
- *`auto` stays std's.* A user-declared `auto` aspect would let users make a property hold with
  no grant, the invisible behaviour D1 objects to; a marker entry is written on the declaration,
  so that objection does not apply to `marker`.

**Derivable aspects and the `derives` clause.** A `derivable aspect` declares methods and a
derivation. `struct Doc derives Clone, Debug { … }` asks the compiler to generate `Clone` and
`Debug` for `Doc`; the derivation is the aspect's template (RFC-0209, RFC-0210) or, once comptime
exists, a comptime derive (see "Blanket impls, derivation and comptime"). Derivation is always
explicit: a type with neither a `derives` entry nor an `extend` does not have the aspect, and
nothing is derived implicitly.

**What it settles**

- **The stop rule (D6.3).** There is nothing to argue about why only `Copy` moved: the aspect
  states how it is granted, and `Drop` says `aspect` (extend only) because its behaviour is
  written.
- **C2 against C4.** The mandatory location is the declaration kind; the modifier
  (`copy struct`) or the list (`struct P: Copy`) is only how a marker grant is written, and can
  be chosen on readability.
- **The derive hazard.** If a marker aspect has no `extend` form, a deriver has no impl to emit,
  which is C2's closure by construction with C4's uniformity.
- **Where a grant may live.** A header grant is in the type's own module, so the orphan rule
  (`T0014`) holds trivially; the foreign-type case stays rejected.

**Worked examples**

1. *`extend Point: Copy;`* under the declaration kinds: error, "`Copy` is granted in the type's
   declaration"; the fix-it moves it after the colon.
2. *`struct H: Drop`* (a method-bearing aspect after the colon): error, "`Drop` has methods and
   is granted with `extend`". `struct H: Clone` is an error pointing at `derives Clone`.
3. *`struct Token: !Send`* on an `auto` aspect: the opt-out, as RFC-0105 first proposed, with
   `Send` otherwise holding because every field is `Send`.
4. *A user marker* (`aspect Marker {}`): `extend`-only, so unchanged; a user may declare it
   `marker aspect` to be granted after the colon instead.
5. *A user marker aspect is a promise:* `struct Vec3: Pod { x: f64, y: f64, z: f64 }` is
   accepted without a field check, and `struct Id: Pod { s: String }` is accepted too (the
   author's claim). `(Vec3, i64)` does not satisfy `Pod` unless the author writes a tuple impl,
   `extend<record R> { ..R }: Pod where ..R: Pod;` covers anonymous records, and
   `struct W<T>: Pod` needs a refining `extend<T: Pod> W<T>: Pod;` to be conditional. `Copy`,
   by contrast, is checked field by field.
6. *A marker aspect on a foreign type:* `extend lib::Point: Pod;` is an error, because the
   type's header is closed; the fix-it points at an ordinary `aspect` for the case.
7. *`struct T: !Validated`* on a marker aspect: an error ("`Validated` is not granted by
   default; remove the entry").
8. *Derive and write:* `struct Doc derives Clone { … }` plus `extend Doc: Clone { … }` is an
   overlap error; `struct Cache { … }` with only the `extend` is fine.
9. *Std's primitives and structural kinds:* `extend i64: Copy;` until std declares primitives
   as structs with headers; `extend<record R> { ..R }: Copy where ..R: Copy;` for anonymous
   records; the tuple and array arms hardcoded until variadic generics and a compile-time
   `N`. All sit in the aspect's defining module, by the third situation.

**Costs and risks**

- A new concept in the aspect system, and a property of each aspect that readers have to learn.
  User aspects default to `aspect` and stay exactly as today unless their author chooses a kind.
- A reader must know whether an aspect has methods to pick the clause; the error and fix-it are
  the mitigation, and `Copy`, `Send`, `Sync` and `Linear` are all markers.
- A marker aspect cannot be granted to a type you do not own, which `extend` can (the orphan
  rule only needs the aspect or the type to be local). The aspect's author picks the kind with
  that in mind.
- RFC-0096's compiler-recognized auto-impl set would become declared properties, which changes an
  under-review RFC; RFC-0105 is narrowed to the marker case now and carries the later stage.
- A user-declared `auto` aspect would let users make a property hold implicitly; hence `auto`
  stays std's.

**What would decide it.** The declaration kinds are worth their weight if more than `Copy`
benefits from an enforced grant position (`Send`/`Sync`/`Linear`, any future marker, derivable
aspects) or if the stop rule cannot otherwise be stated. If `Copy` is the only aspect that ever
needs it, C2 is the smaller change.

---

## Blanket impls, derivation and comptime

**Where a blanket impl over a type's fields stands.**

| Target | A blanket conditional on the fields | How |
|---|---|---|
| anonymous record | yes, automatic | `extend<record R> { ..R }: A where ..R: A` (RFC-0123); a record has no declaration to opt in with |
| `struct`, `enum`, named `record` | no blanket, only an opt-in | a `derives` or marker entry (this RFC) makes the type's row visible to the aspect's template (RFC-0209, RFC-0210) |
| a generic type, conditional on its parameters | yes | an ordinary conditional impl, `extend<T: Foo> Wrapper<T>: Foo` |

There is deliberately no blanket impl over every struct. A type would gain behaviour it never
declared, which is the invisible effect that RFC-0137 and RFC-0162 object to. A user who wants one
anyway has the opt-in: name the aspect after the colon or after `derives`. A blanket with no opt-in exists only as an
`auto` aspect, which is std's.

**What comptime adds.** A `derives` entry runs the aspect's derivation, and a marker entry runs its
check. For an aspect that has one
`{ ..R }` template (or one `enum E` template, RFC-0210), that is the template. Comptime (RFC-0092
`typeinfo` and `emit`, RFC-0093 derive registration, RFC-0174 `comptime for`) covers the rest:

1. **Template bodies.** The field-wise body of a template is a loop over the fields or variants, a
   native hook until RFC-0174 lands.
2. **Derivable aspects with several methods.** A `derivable aspect` supplies a comptime
   derivation in place of a single template: it can generate several methods, read field names and
   types, and emit extra items. `Display` and `Debug` are the typical cases.
3. **Conditions a template cannot state.** A derivation can generate an impl whose condition is
   not a field-wise bound, for example one that depends on a field's attribute. The gate stays: the
   type names the aspect in its header.

**The `#derive` attribute.** RFC-0093 specifies `#derive(Aspect)` as both a request on a
struct or enum and a registration on the comptime function that implements the derive. The
`derives` clause (`struct P derives Clone`) is the request in this RFC, so the two cannot both be
the surface for the same thing. The proposal is that the `derives` clause replaces the request
half and the `derivable` declaration replaces the registration half: the aspect states that it
has a derivation, and names it, so no separate attribute or registry is needed. RFC-0093 would be
amended or narrowed to what a comptime derivation needs. RFC-0093 would be amended when comptime is accepted; until
then std's derivations are native.

## Relationship to existing RFCs

- **RFC-0162** — the `Copy`/`Clone` model; its position C4 is a marker aspect in this RFC's
  terms, and its alternative C2 (`copy struct`) is a spelling of the same declaration kind.
- **RFC-0206** — `Clone`; its §4(c) derives a `Clone` body from a `derives` clause.
- **RFC-0105** — the draft this narrows: aspect lists in declarations, taken here for markers
  only, with no obligation check. Its full model is the later stage described in "Spelling and
  direction".
- **RFC-0096** — the auto-impl set (`Send`, `Sync`, `Linear`) that `auto` mode would turn into
  a declared property.
- **RFC-0209 / RFC-0210** — the templates a header entry runs, for products and for enums.
- **RFC-0092 / RFC-0093 / RFC-0174** — comptime, derive registration and compile-time iteration; see
  "Blanket impls, derivation and comptime".
- **RFC-0102 / RFC-0081** — bodyless and negative `extend`, which remain the form of a
  refinement and of std's own grants.
- **RFC-0060** — the coherence pass that would enforce modes; **RFC-0097** — the orphan rule
  the header grant satisfies trivially.

## Spellings and deferrals fixed at acceptance

1. **Spelling.** `marker aspect`, `derivable aspect`, `auto aspect`, the `derives` clause, and the
   clause order (the colon list first, then `derives`) are the accepted spellings.
2. **User aspects.** `marker` and `derivable` are user-declarable; `auto` stays std's, the closed
   set of RFC-0096 (`Send`, `Sync`, `Linear`).
3. **`#derive`.** The `derives` clause replaces the request half of RFC-0093's
   `#derive(Aspect)` and the `derivable` declaration replaces its registration half. RFC-0093 is
   narrowed to what a comptime derivation needs when it is integrated.
4. **RFC-0096 and RFC-0105.** RFC-0096's recognised-set text is updated for declared `auto`
   aspects, and RFC-0105 is narrowed to the later stage below, at integration. Both carry a
   pointer note to this RFC.
5. **`Copy`'s structural cases** are written impls in the aspect's module (RFC-0123 records, a
   compile-time `N` for arrays, variadic generics for tuples; hardcoded until then), not
   auto-impls.

**Deferred, with homes.**

- *Method-bearing aspects after the colon*, conditional written impls, associated items: RFC-0105.
- *A checked user marker*, a field check stated in the declaration: RFC-0209.
- *Inference for non-public types* (Swift's `Sendable` rule): RFC-0096, which owns when inference
  is allowed.
- *Markers on structural types*: RFC-0212.
- *The exact generic condition* (R2), residual and enum templates: RFC-0209, RFC-0210, RFC-0211.

---

---

## Decision

**Outcome:** accepted 2026-11-02 (language owner), with RFC-0162 and RFC-0206 as one set.

**Accepted:** the four declaration kinds; the colon list for marker facts (`Copy`, `!Send`, user
markers) and the `derives` clause for derivations; derivation always explicit; user marker
aspects as promises; structural coverage as written impls in the aspect's module; the refinement
and negative-impl rules; the coherence rules (including sealing); the spellings above.

**Deferred, with homes:** see the previous section.

**Target:** v0.16.0 (metel-core#1786).
