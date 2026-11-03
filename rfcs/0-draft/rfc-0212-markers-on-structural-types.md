---
id: rfc-0212
title: "Markers on Structural Types"
date: '2026-11-02'
status: draft
---

> **Extracted from RFC-0162 on 2026-11-02** (its Axis S), so that RFC-0162 can be accepted without
> it, the way RFC-0206 and RFC-0207 were extracted. RFC-0162 settles that a *named* type states
> copyness in its declaration; this RFC is the structural half: tuples, arrays and anonymous
> records have no declaration to carry a marker. Nothing here is decided.

## Summary

A structural type is `Copy` when its parts are, and nothing is written. That is cheap and has a
hazard: adding a `String` field to a record, or to the type of a tuple element, changes the type
from `Copy` to move-only with no edit at any declaration, and every use downstream changes
meaning. This RFC proposes a **marker on the written type**, using the same items as the
declaration's colon list (RFC-0207), which also states checked promises:

```metel
fun origin() -> { x: i64, y: i64 }: Copy { { x = 0, y = 0 } }
fun f(p: (i64, boolean): Copy) { … }
let q: (i64, i64): Copy := (1, 2);
```

The marker is a refinement of the written type, erased and checked at the definition. An optional
expression form, `({ x = 0 }: extends Copy)`, needs an amendment to RFC-0130. Inference stays as
it is for every unmarked structural type.

---

## Motivation

RFC-0162 moves the grant of `Copy` onto a named type's declaration (RFC-0207, `derives Copy`).
That does not reach a tuple, an array or an anonymous record: each is written where it is used,
with no header. The hazard (D1 of RFC-0162) is sharper here, because structural values are far
commoner than named ones and the change that flips them is far from the code it breaks.

---

## The options


RFC-0162's Axes A to C are about named types, where a declaration exists to hold a grant. The
structural types (tuples, `[T; N]`, anonymous records, the `[T]` view,
function types and closures) are `Copy` by a rule the checker applies to their parts, and
**no declaration exists to hold a keyword**: a tuple is written `(a, b)` and nothing else.
So C2 and P4 of RFC-0162 cannot reach them, and today's answer (S1) is silent. The hazard is the one
D1 names, in a sharper form: adding a `String` field to a record, or to the type of a tuple
element, changes the type from `Copy` to move-only with no edit at any declaration, and
every use site downstream changes meaning.

- **S1. Inferred from the parts (today).** Nothing is written. Cheapest, and the hazard
  above is unmitigated.
- **S2. Never `Copy`.** A structural value is always moved; a user who wants copy semantics
  names the type (`struct`, `record`) and declares it. Explicit and stable, but tuples and
  anonymous records become awkward to pass around, and it removes behaviour that works
  today (a tuple of `i64` copies), so it is a breaking change.
- **S3. Inferred, with an optional assertion.** Inference stays, and `copy` / `once` can be
  written on a structural type and, in expression position, at the construction site:
  `-> copy { x: i64 }`, `let p: copy (i64, boolean) := (1, true)`, `copy (a, b)`. `copy` is
  checked against the parts and is an error if one is not `Copy`; `once` forbids copying
  even when every part is `Copy` (a token). A signature that writes `copy` is stable: adding
  a `String` field breaks that signature and not its callers. For an open record,
  `copy { x: i64, ..R }` is the existing field-wise bound `where ..R: Copy` (RFC-0123).
- **S4. Required qualifier.** Either the default is `once` and every `Copy` tuple writes
  `copy`, or the default is `copy`, verified at construction as for closures, and every
  tuple with a non-`Copy` part writes `once`. Fully explicit, and noisy at every literal:
  structural values are far commoner than closures.

- **S3p. S3, required in public signatures.** S3, with one addition: a structural type that
  appears in a `public` item's signature (a parameter, a return type, a field of a `public`
  type) must state its copyness, `copy` or `once`, just as such a signature must already
  write its function types in full (`T0010`, `spec.modules.visibility.legality-2`). Inside
  a body everything stays inferred. The boundary is where a change of copyness reaches other
  people's code, so the cost of writing it is paid exactly there.

- **S5. Inferred, with a marker ascription at the expression** (optional companion to S6).
  `({ x = 0, y = 0 }: extends Copy)`: an erased check that the value's type extends `Copy`,
  and a `!Copy` form for the negative. The spelling is `extends`, the word Metel already uses
  for "some type that extends this aspect" (RFC-0130): `x: extends Display` in a parameter
  is a bound the caller meets, `-> extends Display` in a return is opaque, and `: extends
  Copy` in an expression or `let` annotation would be a check that leaves the type visible.
  It parses today, but the position is banned on purpose: RFC-0130 (implemented) makes
  `extends Aspect` legal in exactly the parameter and return positions and "does not attempt
  to legalize it anywhere `impl Aspect` is rejected", which metel-core#622 enforces. So S5 is
  **an amendment to RFC-0130**, a third legal position with a non-opaque meaning, and the
  #622 check relaxed for it. RFC-0130's own reasoning supports it ("the keyword reads as a
  predicate about the position's own subject"), and it is the one spelling that keeps
  `: Copy` free to mean the header's. It protects the author at the construction site only; a second
  constructor of the same shape, or the signature a caller reads, is not covered, and it
  cannot make a value move-only. Because `-> extends Copy` hides the result's type, a result
  cannot use this spelling, which is why S6 puts its marker after the type. In a `let`
  annotation it would collide in meaning with the existential form of the draft RFC-0038
  (`let items: extends Display[] := …`, type erased and dispatched through a vtable, which
  RFC-0038 proposes to spell `dyn`): here the type stays visible, so the two need to be
  stated side by side if both are adopted. **S5 is optional**, and is not needed for S6 or
  for the header; it waits on an RFC-0130 amendment, which is why it is not the headline.
- **S6. Inferred, with a marker on the written type.** Inference stays, and a type written
  in a signature or an annotation may carry a bound list of markers, using the header list's
  own items: `-> { x: i64, y: i64 }: Copy`, `p: (i64, boolean): Copy`,
  `let pair: (i64, boolean): Copy := …`, `: !Copy`. It is a refinement of the written type,
  erased, and checked at the definition: for a concrete type it is true or false the moment
  it is written, and for a generic one it follows the derived condition (`(T, T): Copy`
  holds when `T: Copy`). On a result it is a guarantee the author makes and the caller
  reads; on a parameter it also constrains callers. For an open row,
  `{ x: i64, ..R }: Copy` is the field-wise bound `where ..R: Copy` (RFC-0123), so one
  spelling covers both. No multiplicity is carried on tuples and records. It cannot make a
  `Copy` value move-only (`!Copy` on a `(i64, i64)` asserts something false); a token is a
  named type. Markers only (aspects with no required methods). The positions are returns,
  parameters and `let` annotations; a struct field or a type argument is left out at
  first. The alternative spelling is a `where` clause on the function with the type as its
  subject (`where { x: i64, y: i64 }: Copy`), which restates the type and is the more
  verbose of the two. **Neither parses today** (tried against the parser, 2026-11-02): a
  trailing `: Copy` after a parameter, return or `let` type is a parse error, and so is a
  concrete type as the subject of a `where` constraint, whose subject must be an identifier
  (a type parameter) or `..R`; the existing row equation (`where R = { x: i64, ..Rest }`)
  requires an open row with a `..Rest` tail, so it cannot pin a closed type either. Both
  spellings are therefore a grammar change: the suffix as a restricted production
  (`type_expr` followed by `":" ~ !"=" ~ bound_list`, used only in parameters, returns and
  `let` annotations, with the `!"="` keeping it apart from `:=`), the `where` form as a
  generalised subject. **Spelling chosen (language owner, 2026-11-02): the suffix.** It is local,
  mirrors the header's `: Copy`, and does not restate the type; the `where` form stays
  recorded as the alternative.


S3, S3p and S4 share a type-system cost that S1 and S2 do not: the multiplicity becomes part of
the structural type (as `use_multiplicity` is of the function type, RFC-0134 §4), so
unification and the widening rule (a `copy` value satisfies a `once` slot, not the reverse)
extend to tuples and records, and width subtyping for records (RFC-0117) must carry it.
S3 and S3p use the multiplicity vocabulary of closures (`copy`, `once`); S6 uses the header
list's, so one vocabulary (`: Copy`, `!Send`) covers named types and structural values, and
the division is principled: a type with a declaration states an aspect there, a structural
type states it where it is written. Axis S composes with every A/B/C position of RFC-0162.

**Proposed (language owner's lean, 2026-11-02): S6, the marker on the written type, with S5 as an optional expression form.** S3p, which was the position earlier the
same day, is the alternative: it gives a signature-level contract and can express `once`, at
the price of a multiplicity in the structural types and a second vocabulary. An alias
header (`type Origin: Copy := …`) was considered as a third route and not taken, since
aliases are transparent: it could only assert, and `!Copy` could not make a type move-only,
while `: Copy` would mean a grant on a struct and an assertion on an alias. What is still
open is in the open questions below.

### Worked examples

Each was run against the implementation for S1 (today). The other positions are reasoned,
the syntax not existing.

1. **API evolution.** `lib.mtl`: `public fun origin() -> { x: i64, y: i64 }`; `main.mtl`
   calls `show(o)` twice on its result. Someone adds `label: String`. *S1:* the edit is in
   `lib.mtl`; the error is in `main.mtl`, `use of moved value 'o'`, and does not say the
   new field is the cause. *S2:* nothing breaks, because the double use never compiled; the
   caller needs another way to duplicate (see Open Question 3). *S3:* if the author wrote
   `-> copy { x: i64, y: i64 }`, adding `label: String` fails in `lib.mtl` at the signature;
   if not, it behaves as S1. *S3p:* the author had to write it, so it fails there. *S4:*
   as S3p, and also inside bodies.
2. **A tuple used twice** (`let p := (1, 2); f(p); f(p)`). S1, S3, S3p accept. S2 rejects.
   S4 rejects with a `once` default and accepts with a `copy` default.
3. **A tuple with a `String`, used twice.** S1: `use of moved value 'p'`, with no reason.
   Under every position the diagnostic should say *why*: "`(i64, String)` is not `Copy`
   because `String` is not". That change is independent of this axis and should be made
   whichever position is taken.
4. **An open record in generic code.** `fun dup<record R>(r: { x: i64, ..R })` using `r`
   twice is rejected today; `where ..R: Copy` fixes it. Under S3 and S3p
   `copy { x: i64, ..R }` is a second spelling of that same bound, not a new capability.
5. **A transitive flip.** `record Outer { i: Inner, n: i64 }` is `Copy` while `Inner` is;
   adding `name: String` to `Inner` makes `Outer` move-only, and the error is wherever
   `Outer` is used twice, far from `Inner`. A named type is covered by the declaration-site
   spelling of Axis C (`copy record Outer { … }`), which fails at the declaration.
6. **Generic code over a tuple.** `twice<T: Copy>((1, true))`, and with an anonymous record,
   pass today. S2 breaks both, since a tuple could no longer satisfy `T: Copy`.

The pattern across the six: the hazard concentrates at API boundaries and in named types,
where S3p pays; local code (examples 2 and 6) is correct under inference and only loses under
S2 and S4.

---

## Relationship to existing RFCs

- **RFC-0162** — the `Copy`/`Clone` model; this RFC is its Axis S, extracted.
- **RFC-0207** — the colon list whose items the marker reuses: on a structural type nothing is derived, so the marker is an assertion, the same statement the colon list makes for a promise.
- **RFC-0123** — the field-wise row bound `where ..R: Copy`, which `{ x: i64, ..R }: Copy` spells.
- **RFC-0130** — `extends Aspect`, legal only in parameter and return positions today
  (metel-core#622); S5 amends it.
- **RFC-0038** — the existential `extends`/`dyn` in fields and `let` (draft), which S5 must be
  stated beside.
- **RFC-0206** — `Clone`; duplicating a non-`Copy` structural value, and the tuple `Clone` arm.
- **RFC-0166** — written function types are move-only; the closest precedent for a written type
  carrying a copyness fact.

## Open questions

1. **Positions.** Returns, parameters and `let` annotations are proposed; struct fields and type
   arguments are left out at first. Whether a `let` annotation is allowed is open.
2. **Requirement or documentation.** Whether a parameter's marker is also a requirement on
   callers or only documentation.
3. **Duplicating a non-`Copy` structural value.** Records, arrays, primitives and `String` clone;
   tuples have no `Clone` (RFC-0206 settles the tuple arm).
4. **Scope.** Markers only; no move-only structural value (S3p's `once` is the alternative).
5. **S5 against S6.** Whether the expression form is needed at all.
6. **Grammar.** The suffix is a restricted production (`type_expr` then `":" ~ !"=" ~ bound_list`)
   used only in the positions above; the `where` alternative generalises a constraint subject.

---

## Decision

**Outcome:** *(pending)*
