---
id: rfc-0202
title: "Predicates and Refinement Types"
date: '2026-11-01'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/2098'
---

> **Rewritten 2026-11-14.** This RFC was "Refinement and Smart-Constructor Types": a nominal type with a checked constructor for a
> value predicate. It now also covers predicates over the labels of a row, which two other drafts need (RFC-0151 section 5a, RFC-0125
> Option A), as the same mechanism. A separate draft for row predicates was folded in and withdrawn before it was merged. The
> original design is sections 2 and 6.

> **Status — under review (2026-11-19).** Given a design-settlement tracker (2026-11-19, #2098); unmilestoned

## Summary

A **predicate** is a pure, total, compile-time-evaluable expression over a **subject**. One mechanism covers two kinds of subject,
and one rule decides what a predicate becomes:

> **If the subject is known at compile time, the predicate is checked and is a bound. If it is known only at run time, the
> predicate is carried by a sealed type with a checked entry.**

```metel
type Percent := i64 satisfying (0 <= self && self <= 100);              // subject: a value, known at run time: a sealed type
aspect Dense satisfying (integer_labels_are_a_prefix(self));            // subject: a row, a type: a bound
aspect Tuple: Dense satisfying (closed(self) && no_identifier_labels(self));
```

- **A value subject** gives a distinct nominal type, entered only through a checked construction (`Percent::try_from`), with
  literals checked at compile time. The nominal wrapper is not a choice of style: the property cannot be recomputed from the type,
  so the type has to carry it.
- **A type subject**, a row, gives an aspect granted by inspecting the row's labels (`R: Tuple`, `R: !Tuple`, impls over it). The
  property can always be recomputed from the type, so nothing is wrapped and the row stays the same type: every record operation
  applies to it unchanged.

Both share one predicate language, one set of comptime restrictions (RFC-0132), one diagnostic shape, and one account of what
follows from what. Reasoning about predicates is by construction and by logic, with no solver; a solver is a named extension
point, and nothing here rules it out (section 5). It is a design draft. Nothing here is accepted.

---

## Motivation

### Values: smart constructors by hand

A smart constructor today is a one-field struct whose field is private:

```metel
pub struct Percent { value: i64 }
extend Percent {
    pub fun new(v: i64) -> Result<Percent, String> { ... }
}
```

The invariant is invisible to the compiler and to readers (it is buried in a function body), every such type repeats the
boilerplate, literals pay a run-time check, and the usual accessors (`unwrap`, ordering, arithmetic) are rewritten by hand.

### Rows: a statement with no spelling

Two designs in review need "the integer labels of this row are dense":

- **RFC-0151 section 5a** names the property, `Tuple`, a derived fact used to print `(A, B)` and to choose a dense layout, and leaves
  open whether a program can write it.
- **RFC-0125, Option A** writes positional operations (`cons`, `tail`, `append`, `zip`) as comptime functions over a row that carries
  it. A call's argument list is a mixed row (`.{ .0, .1, .x }`), so it needs the weaker "the integer labels are dense" (`Dense`),
  so that a shift leaves `.x` alone.

Row bounds (RFC-0118, RFC-0189) cannot say it: they state presence, absence and type of *named* labels, and "the integer labels form
a gap-free prefix" quantifies over an unbounded set. RFC-0123's `..R: A` ranges over a row's field *types*, not its label set.

### Why one mechanism

Both ask a compile-time-evaluable predicate whether a subject is acceptable. They differ only in what the compiler knows about the
subject. Treating them separately would mean two predicate languages, two sets of comptime restrictions, two diagnostics, and a
user-declared row predicate (which the row side wants) that is a second `satisfying` beside the first.

| Case | Subject | Known | Result |
|---|---|---|---|
| `Percent`, `Port` | an `i64` value | at run time | a sealed type, `try_from` |
| a literal `8080` where a `Port` is wanted | an `i64` value | at compile time | checked, then coerced to `Port` |
| `Tuple`, `Dense` | a row | always, at compile time | a bound; nothing wrapped |
| `NonEmpty<T>` (`self.len() > 0`) | a value of `T[]` | at run time | a sealed type |
| `struct Config: satisfying Positive` | a type, checked at the declaration | at compile time | section 6 |

---

## Design

### 1. Predicates

`satisfying` is a contextual keyword. `self` in the predicate is the subject. The predicate must be a **pure, total,
compile-time-evaluable expression** (RFC-0132's `comptime fun` restrictions apply): no effects, and no panic, overflow or division by
zero (RFC-0142), so evaluation always yields `true` or `false`. A predicate that fails to evaluate is a compile error, never
`false`. (`where` is not used: it already introduces aspect and row bounds.)

**Obligations are goals.** A check "subject `s` satisfies `P`" is recorded as a goal, and the compiler **discharges** it to one of
three answers: *Proved*, *Refuted* or *Unknown*. Today the discharger is evaluation, for a subject known at compile time, together
with the logical rules of section 4. *Unknown* is an error whose note says what could not be established. A stronger discharger can
turn some *Unknown* into *Proved* without changing what any predicate means (section 5).

### 2. Value subjects: sealed types

```metel
type Name := Base satisfying (predicate);
```

A distinct nominal type (like a newtype, RFC-0200) whose only way in is a *checked* construction. The predicate is evaluated once, at
construction; afterwards the type is the proof. Literals are checked at compile time through comptime evaluation (RFC-0132).

**Generated surface**

```metel
Percent::try_from(n: i64) -> Result<Percent, RefineError>   // run-time check
Percent::unchecked(n: i64) -> Percent                         // unsafe-marked; see below
p.get() -> i64                                                // read the base value
```

`RefineError` carries the failing predicate's source text and the offending value (`Display`). `unchecked` is gated behind `unsafe`
(RFC-0026) or restricted to the declaring module.

**Literal checking.** A literal of the base type in a context expecting the refined type is evaluated at compile time:

```metel
apply_discount(200, 15);      // ok: 0 <= 15 <= 100 holds
apply_discount(200, 150);     // error: 150 does not satisfy `0 <= self && self <= 100`
```

Non-literal values use `try_from`.

**Operations**

- A refined type has the base type's aspects only if derived (`deriving (Eq, Ord, Hash, Display)`), the same mechanism as RFC-0200.
- Arithmetic is **not** forwarded: `Percent + Percent` can leave the range. Provide total-by-construction operations
  (`checked_add -> Option<Percent>`) or write them by hand.
- Narrowing is free: `Percent` to `i64` is `get()`. Widening is `try_from`.
- A refinement can be refined further (`type Half := Percent satisfying (self <= 50)`); the predicates conjoin, which is entailment by
  extension (section 4).

**Example**

```metel
type Port := i64 satisfying (1 <= self && self <= 65535) deriving (Eq, Display);

fun listen(p: Port) { ... }

fun main() {
    listen(8080);                                       // literal: checked now
    match (Port::try_from(read_int())) {
        Ok { value } => listen(value),
        Err { value } => println("bad port: ${value}"),
    }
}
```

**Mutation of a sealed value** is left open: see open question 1.

### 3. Type subjects: predicates over a row

```metel
aspect Dense satisfying (integer_labels_are_a_prefix(self));
aspect Tuple: Dense satisfying (closed(self) && no_identifier_labels(self));
```

| Predicate | Holds for a row when | Examples |
|---|---|---|
| `Dense` | its **integer** labels are exactly `.0 .. .N-1` for some `N ≥ 0`; identifier labels are unconstrained | `.{ .0: A, .1: B }`, `.{ .0: A, .x: C }`, `.{}`; not `.{ .0: A, .2: C }` |
| `Tuple` | it is **closed**, `Dense`, and has **no identifier labels** | `.{ .0: A, .1: B }`, `.{}`; not `.{ .0: A, .x: C }`, not an open row |

**A predicate over a row is an aspect granted by shape.** The language already has an aspect granted with no impl, from the
structure of a type, with a negative impl to opt out (the `auto` property: *granted structurally with no entry; a type opts out
with a negative impl*; std only, reserved; `Send` and `Sync`). `Dense` and `Tuple` are of that kind, granted from a row's label
set instead of its field types. That gives them, with no new construct:

- **Bounds**, positive and negative: `R: Tuple`, `R: !Tuple`, and the `+` and `where` forms (RFC-0040);
- **impl selection**: `extend<record R: Tuple> R: A` is a row-conditional impl (RFC-0121) whose condition is a predicate;
- **diagnostics**: an unsatisfied bound is `T0012`, with a note naming the cause, as RFC-0211's residual notes do: ``.{ .0: A, .2: C }`
  is not a `Tuple`: the integer label `.1` is missing``.

**How a predicate over a row is decided.**

- *A closed row*: by inspecting its labels, with no annotation, proof or solver.
- *An abstract or open row*: only by a declared bound. A parameter `record R: Tuple` is `Tuple`; `.{ .0: A, ..R }` with `R: Dense`
  says nothing about the whole row, because `R` is a row whose labels start where they start. The shift that relates them is what
  RFC-0125 computes, not a rule here.
- *After a narrowing*: the residual is a new closed row and its predicates are decided afresh. A partial move that leaves a gap
  leaves a row that is not a `Tuple`; one that removes a suffix leaves one that is. No rule is needed (RFC-0151 section 4a).

**What a row predicate does not change.** Type identity: `(A, B)` and `.{ .0: A, .1: B }` are one type, with no brand. Operations: a
row satisfying `Tuple` has every operation of a record, and a function that takes `R: Tuple` takes a record and uses it as one.
Layout and printing: RFC-0151 section 5a states them in terms of `Tuple`; this RFC supplies the predicate.

**It is not a type former.** The row is the same row; the predicate is a fact about it. A row cannot opt out of a shape fact, so
`extend .{ .0: A }: !Tuple` is an error (open question 3).

### 4. Entailment and coherence

**Entailment is by extension only.** `aspect B: A satisfying (extra)` means `B(x) = A(x) && extra(x)`, so `B ⇒ A` holds by
construction, with nothing to trust and nothing to check. `Tuple ⇒ Dense`, and `Half ⇒ Percent` in section 2, are of this kind.
An implication `P ⇒ Q` where `Q` is not a conjunct of `P` is not expressible. This keeps reasoning local to each declaration, as
the orphan rule keeps coherence local: no other module's declarations are needed to know what implies what.

**Coherence is propositional and conservative.** The rule stays that two impls whose conditions do not exclude each other overlap
and are rejected (`T0015`). With predicates as named atoms and extension edges, "do they exclude each other" is a small
propositional question: overlap exists iff both conditions can hold at once, given the extension edges.

- `P` and `!P` are disjoint for any predicate, without evaluating it.
- `Tuple` and `!Dense` are disjoint, by contraposition of `Tuple ⇒ Dense`.
- `Q` extends `P`, so impls on `P` and on `Q` overlap (there is no specialization); the author writes `P + !Q` beside `Q`.
- Unrelated predicates are treated as overlapping, unless the standard library states that the std predicates exclude each other
  (for example, `Tuple` has no identifier label).

The conservative direction is safe: the worst outcome is a `T0015` the author resolves, never an unsound pair of impls. There is no
`excludes` declaration yet.

**Negative bounds.** `R: !Tuple` holds on a closed row when the predicate evaluates false, which is the spec's closed-world rule; on
an abstract row only if declared as a bound.

### 5. What is deferred, and the extension points

**Flow-sensitive refinement is deferred, not a non-goal.** The type system does not track facts (`if (n >= 0) .{ ... }` does not give
`n` a refined type), because that needs a proof engine. Row narrowing for moves is already path-sensitive (RFC-0117), so the
infrastructure for path-sensitive facts has precedent.

**A solver is a named extension point.** The design is shaped so that one can be added without changing the meaning of any program:

1. Obligations are goals with a three-valued answer (section 1). A solver can only turn *Unknown* into *Proved*, so it accepts more
   programs and never changes which values satisfy a predicate.
2. A predicate is classified into a **named analyzable fragment** when it falls inside one, and is evaluation-only otherwise.
   Whether classification is implicit or declared is open question 2.
3. Each fragment is a **decision procedure specified in the language**, in-tree, with no heuristic search and no time limits, so
   acceptance is defined by the language and not by a tool. Two candidates: label-set theory (finite sets, prefixes of the
   integers) and linear integer arithmetic. Both are specified as extension points when a driving case exists, and neither is built
   now. Each is added by its own RFC.
4. An external SMT backend, if ever used, is an opt-in tool outside the language definition and never affects acceptance.
5. The goal interface is stated minimally here. The abstract ownership solver (#1813, goals answered yes with a witness, no, or
   unknown) is the intended first host, decided when that solver exists.

**No longer deferred: the checked impl form is specified in section 6** (language owner, 2026-11-26). It touches RFC-0137's
rule that a struct never satisfies a row bound, as expected when this was deferred; RFC-0243 carries that amendment.

**Deferred in this RFC.**

- *Length predicates and indexing* (`Len(N)`, `Tuple<N + 1>`): they need a compile-time integer in a bound, which is const generics
  (RFC-0053 deferred them; #1811 waits on RFC-0132's compile-time `N`).
- *Predicates over field types* beyond what row bounds already say.

### 6. Granting a predicate aspect: the colon list, refined, never `extend`

A predicate aspect has no body — `Dense` and `Tuple` have none — so it is never granted through `extend`: there is nothing
to extend, and `extend` stays reserved for aspects with real behavior (RFC-0250's `using Name`, a different and unrelated
mechanism, below). Instead (language owner, 2026-11-26), `satisfying` is an explicit refinement of RFC-0212's `declared`
property, and granting a predicate aspect to a named type is an extension of RFC-0207's existing colon list, not a new
grant site.

- **Both keywords are written explicitly on the aspect's own declaration; neither implies the other.**
  `declared aspect Positive satisfying (self > 0);` is declared *and* has a condition. `declared` alone is RFC-0207's
  original, unchecked promise. `satisfying` alone is a predicate usable wherever section 3 already applies one ambiently —
  closed rows, open-row bounds — but it has **no named-type grant path at all**: `declared` is what opens that door, and
  writing `satisfying` does not open it on its own. A colon-list entry naming an aspect that is `satisfying` but not
  `declared` is rejected (`declared` required).
- **A `declared` aspect's colon-list entry is bare (`T: A`) unless `A` is also `satisfying`, in which case the entry must be
  `T: satisfying A`.** A bare entry naming a `declared, satisfying` aspect is a hard error — `satisfying A` is required,
  never silently accepted as the unchecked form. `satisfying A`'s predicate is evaluated with `self` bound to `T`'s row, by
  the same rule section 3 already uses for a closed row: inspecting its labels, with no annotation, proof or solver.
  Accepted iff the predicate holds. No body is installed; the grant only records that `A` holds for `T`, the same fact
  bounds already read from a row directly.
- **This reuses RFC-0212 section 1's existing rule, not a new one.** `declared` already makes `extend T: A` an error with
  a fix-it, for any `declared` aspect, checked or not — `satisfying` adds a second, checked colon-list entry to the one
  door `declared` already opens; it does not change what `extend` does.

This directly answers the motivating example above, now spelled `struct Config: satisfying Positive;`, and is RFC-0207's
answer for a `declared` user marker (rule 1): the marker stops being an unchecked promise once both keywords are written.
`A: Derivable` (RFC-0238) is a different and unrelated route to a type's aspects — a comptime deriver computes a new impl's
body by running restricted code against `typeinfo(T)`, where this section only records a fact some other declaration
already states; a `satisfying` aspect has no deriver to register, and this section's grant never calls one.

**This section does not close RFC-0243's migration gap.** A struct migrated from a `record` that automatically matched a
plain aspect's *blanket impl* — real behavior, not a fact — needs RFC-0250's `extend T: A using Name;`, always named, never
bare. That belongs there: this section is for facts with no body; RFC-0250's mechanism is for adopting someone else's body
by explicit reference.

---

## Interactions

- **RFC-0200 (newtypes):** a refined type is a newtype plus a predicate; `deriving` is shared.
- **RFC-0132 / RFC-0092 (comptime):** the predicate and the literal check run through comptime; its restrictions are the predicate's.
- **RFC-0151 / RFC-0125:** `Tuple` and `Dense` are what they name and need. RFC-0125's Option A takes `R: Tuple` and `R: Dense`.
- **RFC-0118 / RFC-0123 / RFC-0189:** the row-bound language this extends by one kind of atom, a label-set predicate.
- **RFC-0096:** the `auto` property, a separate std-reserved category from `declared`/`satisfying` (section 6).
- **RFC-0121 / RFC-0060:** row-conditional impls and coherence; unaffected by section 6, which never involves one — a
  predicate aspect has no impl, named or otherwise.
- **RFC-0137 / RFC-0243:** section 6 touches RFC-0137's rule that a struct never satisfies a row bound without an explicit
  entry. RFC-0243's migration gap (named records losing an automatic plain-aspect *blanket impl* on retirement) motivated
  this section's design but is closed by RFC-0250's `using Name`, not by section 6 — section 6 only ever grants a fact with
  no body.
- **RFC-0212:** section 1's `declared` is the property `satisfying` refines (section 6); both keywords are required,
  explicitly, on the aspect's own declaration, and `declared`'s existing "`extend` is an error" rule is what section 6
  relies on rather than restating.
- **RFC-0238:** `Derivable` is a different and unrelated route to a type's aspects; section 6 states that the two do not
  compose.
- **RFC-0250:** the mechanism for adopting an existing aspect's *behavior* by explicit reference (`extend T: A using
  Name;`, always named, never bare) — complementary to, and never confused with, this section's predicate-only grants.
- **RFC-0213:** the super-aspect relation, whose "a proof of `A` proves `B`" extension by `aspect B: A satisfying` mirrors.
- **RFC-0241 (Metel-Core), section 7.9:** where a solver and flow-sensitive refinement would sit on the compiler's typed
  representation: a pass over Core, with a predicate slot reserved on types and facts through references waiting on borrow checking.
- **RFC-0170 / RFC-0165 (literal types, unions):** `Port` could be seen as a large union of literal types; refinement avoids
  enumerating it.
- **RFC-0142 (checked arithmetic):** `checked_*` results feed `try_from`; its totality requirement is the predicate's.
- **RFC-0119 (record conversions):** `try_from` follows the same naming; fallible direction.
- **RFC-0201 (pattern synonyms):** a partial synonym over a refined type gives `match` support.
- **RFC-0160 (aliases):** plain aliases stay transparent; only `satisfying` on a `type` introduces identity.
- **RFC-0207 / RFC-0212:** user markers (`declared aspect`) stay an unchecked promise until also made `satisfying` and
  checked by section 6.
- **RFC-0211 / RFC-0214:** a residual's predicates are decided afresh; an impl for a residual may name one.

---

## Alternatives considered

1. **Two RFCs: value refinement and row predicates.** The earlier split. Rejected: the same predicate language, comptime
   restrictions, diagnostics and derivation, and a user-declared row predicate would be a second `satisfying`.
2. **Status quo** (private field and `new`). Fully expressible today for values; this RFC is ergonomics and compile-time literal
   checking, and for rows there is no spelling at all.
3. **Full refinement or dependent types** (Liquid Haskell) now. Rejected: it needs an SMT-style solver and a stable core surface
   (roadmap *Compiler-ready pipeline*). Section 5 keeps the door open for decision procedures per fragment.
4. **A new bound class** with its own expression language (`where labels(R) = 0..n`). More general, and a second language for
   conditions beside aspects; the aspect route gets bounds, negation, impl selection and coherence at once.
5. **Only literal types** (RFC-0170). Cannot express ranges or label-set shapes.
6. **Label arithmetic** in label variables (`.[L + 1]`, RFC-0188), stating a shift in the row syntax. It addresses RFC-0125's
   renumbering, not the predicate, and composes with this RFC.

---

## Open questions

1. **Mutation of a sealed value** (section 2). If a sealed `NonEmpty<T>` lets its inner `T[]` be mutated through `&var`, `pop` breaks
   the invariant. Four policies are on the table, and none is chosen:

   | Policy | How it works | Cost |
   |---|---|---|
   | **M1: immutable** | no `&var` to the inner; updates are `self -> Self` | O(1) by ownership (move the inner out, push, re-wrap with the module-private `unchecked`), but a `&var` context (a struct field updated from `&var self`) must move the value out and put a valid replacement back, and a sealed `NonEmpty` has no empty placeholder, so a throwaway value must be built |
   | **M2: checked mutation** | `&var self` methods allowed in the declaring module, with the predicate re-checked at the method's exit | a run-time check per call, and rules for early `return`, panics and nested borrows |
   | **M3: trusted module** | outside the declaring module only `get()` and consuming operations; inside it `&var` to the inner is allowed and the module is trusted to keep the invariant (what `unchecked` already means, and what private-field-plus-`new` gives today) | the compiler guarantees nothing about the invariant; M2 can be added later as an opt-in check, so choosing M3 locks nothing out |
   | **M4: guarded access** | `&var` gives a scoped guard that re-checks on release | the heaviest design |

   A caution on the argument for M1: facts about a sealed value live in its type, so they survive mutation by trusted module code;
   flow facts concern plain variables (`n: i64` after `if n >= 0`), which an assignment kills regardless.
2. **Is analyzability implicit or declared?** Under implicit classification, a predicate falls into a named fragment (or not) by its
   form, and the author is told by a note only when it is opaque. The risk is a silent cliff: a small rewrite can change whether a
   predicate is analyzable, though never what it means, only how many programs are accepted. Declared analyzability (a separate form,
   or an error when a predicate is outside the fragment) is explicit, at the cost of two forms.
3. **The `auto` property, or a new one?** `auto` allows a type to opt out by a negative impl; a shape fact has no opt-out. Reuse
   `auto` and make the negative impl of a shape predicate an error, or add a property for aspects decided by structure alone?
4. **Names.** `Tuple` collides with the type former and, if a program defines its own, with that; `Dense` is vague outside rows.
   Are `Positional` and `Sequence` better, and is a name that shadows legal?
5. **User-declared type predicates.** The mechanism allows `aspect X satisfying (...)` over a row's `TypeInfo`. The `auto` property is
   std-only and reserved, so the first version has only `Dense` and `Tuple`. When may a program declare its own, and how is
   coherence stated for predicates the compiler cannot compare?
6. **Open rows and non-`record` parameters.** `Dense` of `.{ .0: A, ..R }` is undecidable; may a bound on `R` ever imply something
   about the whole row? May a predicate bound appear on a parameter that is not a row, and is it then simply unsatisfied?
7. **Carried from the original draft.** Is a `satisfying` keyword preferable to attribute syntax (`#refine(...)`)? Must the predicate
   be total, and what happens at compile time when it overflows or divides by zero (section 1 requires totality)? Does `unchecked`
   need `unsafe` (RFC-0026 is a draft) or is module-private enough? Do `Copy`, `Clone` and `Drop` of a refined type follow the base
   unconditionally? How are refined types represented in generic code (`List<Percent>`)?
8. **Length.** If RFC-0125's result types need a length, this RFC needs const generics; if they do not, it does not.
9. **Error text.** The `T0012` note for an unsatisfied row predicate names the missing label; for an open row it must say the row is
   open.

---

## Implementation notes

- **Value subjects:** the `type ... satisfying` declaration, the generated `try_from`, `unchecked` and `get`, and comptime literal
  checking; the first stage needs only RFC-0132's evaluator.
- **Type subjects:** the standard library declares `Dense` and `Tuple`; the compiler grants them from a row's label set and
  implements that `Tuple` implies `Dense`. Bounds, negative bounds, impl selection and coherence reuse the aspect machinery, so no new
  bound class is needed. No new syntax beyond `satisfying`.
- **Granting a predicate aspect (section 6):** extends RFC-0207's colon-list grammar with a `satisfying <name>` entry form,
  alongside the existing bare one. `declared` and `satisfying` are both read from the aspect's own declaration (RFC-0212);
  no new grammar is needed on `extend` itself, since this section never touches it. `T0045`-style rejects: a bare entry for
  a `declared, satisfying` aspect, and any colon-list entry at all for a `satisfying`-without-`declared` aspect.
- **Goals:** obligations are recorded as goals with a three-valued discharge; the first discharger is evaluation and the
  propositional rules of section 4.
- **Fixtures:** each predicate on closed rows (satisfied, gap, identifier label, open), a bound on a parameter, an impl over `Tuple`,
  disjoint impls (`Tuple` and `!Tuple`, `Tuple` and `!Dense`), the residual after a partial move, the error note; for values, the
  literal check, `try_from`, a refined type refined further, and a predicate that fails to evaluate.

---

## Decision

**Outcome:** *(pending)*
