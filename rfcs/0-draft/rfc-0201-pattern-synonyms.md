---
id: rfc-0201
title: "Pattern Synonyms"
date: '2026-11-01'
status: draft
---

## Summary

A **pattern synonym** is a named, user-defined pattern. It lets a type expose a matching
interface that differs from its representation, for use in `match`, `let` destructuring, and
(for bidirectional synonyms) as an expression.

```metel
pattern Cartesian { x: f64, y: f64 } for Polar {
    match (p)      => { x = p.r * cos(p.theta), y = p.r * sin(p.theta) }
    build (x, y)   => Polar { r = sqrt(x*x + y*y), theta = atan2(y, x) }
}
```

---

## Motivation

Pattern matching is Metel's main tool for taking values apart, but patterns can only name the
representation's own variants and fields. This forces a choice between exposing a type's
internals (and being unable to change them) and offering only methods (and losing `match`,
exhaustiveness checking, and nested patterns).

Typical cases: a polar/cartesian pair, a normalised view of a string, an enum with an internal
encoding, a sequence viewed as head/tail.

---

## Design

### 1. Declaration

```metel
pattern Name { fields } for Subject {
    match (v) => <expr yielding the record of fields>     // required
    build (args) => <expr yielding Subject>                // optional
}
```

- The **match** clause is total: it always produces the fields (the synonym is a projection,
  not a test). A *partial* synonym is written with an `Option` result (`match (v) => Some {...}`
  / `None`) and `pattern partial Name ...`.
- The **build** clause makes the synonym usable as an expression (`Cartesian { x = 1.0, y = 2.0 }`).

### 2. Use

```metel
fun quadrant(p: Polar) -> i64 {
    match (p) {
        Cartesian { x, y } => {
            if (x >= 0.0 && y >= 0.0) { 1 }
            else if (y >= 0.0) { 2 }
            else if (x < 0.0) { 3 }
            else { 4 }
        },
    }
}
```

A total synonym is irrefutable, so the single arm above is exhaustive.

### 3. Exhaustiveness

- A total synonym counts as covering its subject, exactly as an unguarded struct pattern does.
- A partial synonym is refutable. A group of partial synonyms may be declared jointly
  exhaustive with `complete (A | B | C) for Subject;`; the compiler checks nothing about
  the claim beyond that it is stated once and only in the declaring module (see Open Question 2).

### 4. Ownership

The `match` clause is a **function of the subject** and follows ordinary call rules:

- `match (p)` receives `p` by reference by default (`&Subject`), so matching a synonym does not
  move the subject.
- `pattern own Name ...` receives it by value and moves it, for synonyms that destructure
  resources.
- Bindings in the pattern are copies or moves of the *produced* fields, never aliases into the
  subject.

### 5. Visibility

A synonym is exported with `pub`, independently of its subject's fields. This is the point: a
module may keep its representation private and export only the patterns.

---

## Interactions

- **RFC-0109 / RFC-0144 (reference destructuring):** both define how patterns bind through
  references. A synonym's `match` clause is ordinary code, so it composes with them but does not
  extend them.
- **RFC-0165 / RFC-0170 (unions, literal types):** a synonym can present a union as variants.
- **RFC-0137 (branded rows):** patterns over the *residual* row after a partial move are not
  expressible by a synonym; synonyms see whole values.
- **RFC-0202 (refinement):** `Percent::try_from` is a natural partial synonym.
- **RFC-0100 (constructor calls):** the `build` clause reuses whichever construction syntax that
  RFC settles.

---

## Alternatives considered

1. **Only methods** (`p.x()`, `p.y()`). No `match`, no exhaustiveness.
2. **View patterns** (`match (f(v)) { ... }` written inline at every site). Duplicates the
   projection at each use; no name; no export boundary.
3. **Active patterns** (F#). Similar; a partial active pattern here is `partial` + `Option`.

---

## Open Questions

1. Should synonyms be allowed inside *nested* patterns with sub-patterns on their fields
   (`Cartesian { x = 0.0, y }`)? The straightforward lowering is a nested match on the produced
   record, but literal sub-patterns may require re-evaluating the projection.
2. How strong should `complete` be? An unchecked claim is unsound if the subject changes; a
   checked one requires a theorem prover for arbitrary predicates.
3. Is the cost model acceptable? A `match` clause runs once per arm that mentions the synonym
   unless the compiler memoises it across arms.
4. Parameterised synonyms (`pattern Divisible(n) ...`).
5. How does the grammar (see ADR-0015 on keyword-prefix identifiers) handle `pattern`, `match`, and
   `build` as contextual keywords?

---

## Decision

**Outcome:** *(pending)*
