---
title: "Linear Types in Metel: Explainer and Decision Register"
date: '2026-11-07'
status: report
relates: rfc-0089, rfc-0194, rfc-0206, rfc-0211, rfc-0212, rfc-0213, rfc-0215, rfc-0219, rfc-0220
---

# Linear Types in Metel: Explainer and Decision Register

A map of the ownership-class design for someone who wants to understand it before accepting it. Part 1 explains
the model from scratch. Part 2 is a register of every decision, with its status, the alternatives, and how hard it
is to reverse. Part 3 is a dependency map, so you can see which decisions move together. Part 4 is a set of probe
questions to test understanding. Part 5 is a reading order for the RFCs.

This report records and explains. It does not decide. The **confidence** column is the author's assessment of how
well the decision is supported, not the language owner's. On 2026-11-07 the language owner **settled** the
generic-class model, the elimination rules and closures: D7 to D14 and D19 are accepted (inert until the `linear`
release), and **deferred** D15 (binding-level qualifiers). RFC-0089 carries the scope note.

## Status legend

| Status | Meaning |
|---|---|
| **Accepted** | Decided, binding for v0.16.0. |
| **Reserved** | Written down as the intended design, kept for review, not binding on implementation. |
| **Open** | Not decided, or decided in principle with a named open sub-question. |

## Part 1. The model from scratch

### 1.1 Three ownership classes

Every type has a class that says what a value of the type may do.

| Class | Written | Use at most / exactly | May be dropped | May be copied |
|---|---|---|---|---|
| copy | `copy struct P { .. }` | any number of times | yes | yes, implicitly |
| affine | (default, no keyword) | at most once | yes | no |
| linear | `linear struct Tx { .. }` | exactly once | **no** | no |

Most Metel types are affine, which is the default and what Rust calls "move-only". `copy` is for small
plain-data types. `linear` is the new one: a value of a linear type **must** be consumed. It cannot simply go out of
scope.

### 1.2 Why have a linear class

An obligation that the compiler must enforce. A database transaction must be committed or rolled back. A file
handle must be closed explicitly if closing can fail. A capability token must be returned. Today these are
conventions. A linear type makes forgetting one a compile error.

```metel
linear struct Tx { id: i64 }

fun commit(tx: Tx) { /* consumes tx */ }

fun good() { let tx := begin(); commit(tx); }
fun bad()  { let tx := begin(); }        // error: `tx` is linear and is not consumed
```

### 1.3 Capabilities are bounds

What you may do with a generic value is whatever its bounds say, and nothing more.

| Bound | Lets generic code | Computed or written |
|---|---|---|
| `T: Copy` | copy a `T` implicitly | written |
| `T: Clone` | call `.clone()` | written |
| `T: Discard` | let a `T` go out of scope | written bound, but the capability is computed by the compiler |

A bare `T` is **possibly linear**: it assumes no capabilities, so generic code may not drop it. That is the
conservative reading and it is why writing `T: Discard` is needed in generic code that drops values.

```metel
fun keep<T>(x: T) -> T { x }                      // fine: moves x on
fun lose<T>(x: T) { }                             // error once linear ships: x is dropped, T is not Discard
fun lose_ok<T: Discard>(x: T) { }                 // fine
```

**Staging.** In v0.16.0 every type is `Discard`, so `T: Discard` is accepted and always true. Nothing breaks and
nothing is checked. The check becomes real at the `linear` release.

### 1.4 Generic types

A generic type is **open by default**: any type, linear or not, may be an argument. The class of an instance is
**computed** from its owned fields, the way a tuple's is.

```metel
struct Pair<T> { a: T, b: T }
// Pair<i64>  is affine (or copy if declared so)
// Pair<Tx>   is linear, because it owns two linear values
```

Three refinements:

- `linear struct Ticket<T> { id: i64 }` is linear for every `T`. The keyword is unconditional.
- `copy struct Wrapper<T> { v: T }` states a capability: `Wrapper<X>` is `Copy` exactly when `X` is.
- `struct Closed<T: Discard> { v: T }` refuses linear arguments, and every use of `Closed<T>` in generic code
  repeats the bound.

### 1.5 Taking linear values apart

If a value must be consumed exactly once, you cannot move one field out and leave the rest behind to be dropped,
because the rest might be linear too. So:

- A **nominal** aggregate (struct, enum, named record) that is not known to be `Discard` is consumed whole, either
  by a function that takes it, or by **total destructuring**: bind every field. A field skipped with `..` or `_`
  must itself be `Discard`.
- **Structural** types (tuples, anonymous records) have no declaration, so they work field by field: moving a field
  out leaves a smaller structural type whose class is recomputed.
- A pattern **consumes** the value it destructures. It does not leave a half-moved remainder behind.
- A type with a destructor (`Drop`) is dismantled only by an explicitly marked method in its defining module, and doing so
  skips the destructor (the marker's spelling is open; `consume self` is a placeholder):

```metel
struct Logged<T> { value: T }
extend<T: Discard> Logged<T>: Drop { fun drop(&var self) { log("gone"); } }

extend<T> Logged<T> {
    fun into_inner(consume self) -> T {    // marker, defining module only
        let Logged { value } := self;      // allowed: destructor skipped
        value
    }
}
```

`Logged<Tx>` exists and is linear, but has no destructor, because the destructor impl needs `T: Discard`.

### 1.6 Closures and function types

A closure that captures a linear value must itself be declared `linear` (an error with a fix-it says so). A function
type that is not `linear` is therefore always `Discard`, so a library function such as `Option::map` can drop its
callback without a bound. A `linear` function type can only be filled by a linear closure.

### 1.7 What a user who never touches linear types sees

- Concrete code: nothing. Every type they use is `Discard` or `Copy`.
- Generic code they write: they may need `T: Discard` where a by-value `T` is dropped. A scan of std (2026-11-05)
  found 30 to 40 percent of by-value generic functions drop on some path. Taking `&T` instead removes many.
- Types they define: nothing, unless a field's type is a linear type from a library.

### 1.8 Must-use for an affine type, without binding-level qualifiers

Binding-level qualifiers (D15) are deferred. Two type-level patterns give must-use for an ordinary affine type:

```metel
linear struct OpenFile { file: File }               // forces the obligation on every holder
extend OpenFile {
    fun close(self) { let OpenFile { file } := self; file.close_now(); }
}

fun with_file<T>(path: String, use_it: |&File| -> T) -> T {     // cleanup guaranteed by the bracket
    let f := open(path);
    let r := use_it(&f);
    f.close_now();
    r
}
```

The wrapper makes the producer force the obligation, which a `linear let` the caller may or may not write does not.
The bracket guarantees cleanup around a scope with no linear types at all. Both avoid the composition problem with
generics that stopped D15: a `linear` parameter and return force a `linear let` on every caller, and without
qualifier polymorphism a generic function cannot take a linear binding.

## Part 2. Decision register

Reversibility: **cheap** means a text and checker change with no user-visible break (Metel has no users now),
**moderate** means it changes syntax or many RFCs, **hard** means it changes what the language is.

| ID | Decision | Status | Main alternatives | Confidence | Reversibility | Depends on |
|---|---|---|---|---|---|---|
| D1 | Affine is the default class. Keywords are `copy` and `linear`. There is no `affine` keyword. | Accepted | An `affine` keyword; Rust-style implicit `Copy` | High | Moderate | none |
| D2 | A non-generic named type's class is **declared** and checked against its fields. A type holding a linear field must be declared `linear`, with a fix-it. | Accepted | Infer the class from the fields (Rust auto traits) | High | Moderate | D1 |
| D3 | `Copy` is sealed (representation copy). `Clone` is provided and unwritable for `Copy` types. Grants appear only in the declaration. | Accepted | Rust's open `Copy`/`Clone` | High | Hard | none |
| D4 | Capabilities are written bounds: `T: Copy`, `T: Clone`, `T: Discard`. A bare `T` is possibly linear. | Accepted | Infer `Discard` for bodies; a closed default where `T` is discardable and `?Discard` opts in (Swift style); declare universes (Austral style) | Medium-High | Cheap in v0.16.0 (the bound is vacuous), moderate later | D1 |
| D5 | `Discard` is computed by the compiler. It cannot be implemented or negated by users. `Copy` implies `Discard`, and a `Drop` type is `Discard`. | Accepted | A user-written `Discard` impl | High | Cheap | D4 |
| D6 | In v0.16.0 every type is `Discard`, so `T: Discard` is accepted and always true. The check activates at the `linear` release. | Accepted | Ship the check early | High | Cheap | D4, D5 |
| D7 | The class of a generic instance is **computed** from its owned fields. Generic types are open by default. | **Accepted (2026-11-07)** | Declared class with explicit conditional (Austral `Type` universe, Swift `~Copyable`); closed by default | **Medium: the keystone** | Hard once std is written | D4 |
| D8 | `linear` on a generic type is unconditional. `copy` states a capability (`Copy` exactly when the fields are). | **Accepted (2026-11-07)** | `linear` conditional too | Medium-High | Moderate | D7 |
| D9 | `T: Discard` on a type parameter forbids linear arguments, and every use of the type repeats the bound. | **Accepted (2026-11-07)** | Bound only at the declaration; a separate marker | Medium | Moderate | D4, D7 |
| D10 | A field whose type mentions no type parameter and is linear forces `linear` on a generic type (syntactic rule, error at the field with a fix-it). A field such as `Ticket<T>`, linear for every `T`, is not caught; for a public type the checked `Discard` condition (D19) catches it, for a private type it surfaces at the drop sites. | **Accepted (2026-11-07)** | A symbolic test with every parameter assumed discardable (more precise, needs a solver, limits flagged in review 11); no rule (D7 and D19 only) | Medium-High | Cheap | D7, D19 |
| D11 | A partial move out of a nominal aggregate is legal only when it is known `Discard`. Structural types still narrow. | **Accepted in design (2026-11-07); effective with the `linear` release** | Rust-style residuals; ban partial moves outright; per-field classes | Medium | Moderate | D2, D7 |
| D12 | Destructuring patterns consume the scrutinee. Skipped fields must be `Discard`. Matching through a reference consumes nothing; a whole-value `_` consumes nothing. | **Accepted in design (2026-11-07); effective with the `linear` release** | Rust's `..` leaves a residual | Medium | Moderate (it overrides implemented RFC-0137 pattern narrowing) | D11 |
| D13 | `Drop` impls must prove the target `Discard`. A type with a `Drop` impl is dismantled only by an **explicitly marked** inherent method in its defining module taking an owned `self`, by total destructuring that suppresses only the outer destructor. The marker is illegal on borrowed receivers, aspect defaults, aspect impl methods and outside the defining module. Spelling settles with the `pub` sweep (RFC-0218). | **Accepted in design (2026-11-07); takes effect with D11 and D12** | Implicit own-method authority; Rust-style ban; no conditional `Drop` (a `Drop` type must be `Discard` for every instantiation) | Medium | Moderate | D11, D12 |
| D14 | A closure capturing a linear value must be declared `linear`. A non-`linear` function type is `Discard`. | **Accepted in design (2026-11-07); RFC-0194 awaits formal acceptance** | Infer linearity of closures; allow droppable linear closures | Medium-High | Moderate | D7 |
| D15 | Binding-level qualifiers: `linear let`, `linear` parameters, returns and fields (RFC-0220). | **Deferred (2026-11-07)**: RFC-0220 parked as a draft; wrapper and bracket patterns (section 1.8) cover the strong case | Not adding them; type-level only | Low | Cheap (draft) | D7, D11 |
| D16 | The `dyn` erasure gate, native owning storage (`List<Tx>`), and `consume_each`'s contract. | Open (release gates) | Forbid at first | n/a | n/a | D7 |
| D17 | Do destructors run at panic? When do skipped fields drop (at the pattern, or at scope end)? | Open (#1835, #1843) | n/a | n/a | n/a | D12 |
| D18 | Public generic types state their `Copy`/`Clone` conditions (the interface). `Discard` is computed from fields and, until D19, is not part of the stated interface. | Accepted (RFC-0206 section 6) | State `Discard` too (D19) | Medium | Moderate | D7 |
| D19 | Public generic types also have a stated `Discard` condition. Without a statement, outside code sees the conservative default (`Discard` exactly when every parameter is `Discard`); the effective condition, stated or default, is checked against the fields and a stronger one is a declaration error. Inside the defining module the exact computed class applies. A publish-time interface comparison (M2) is a possible later addition. | **Accepted (2026-11-07)** | Required statement on every public generic type; tooling only; policy only | Medium-High | Moderate | D7, D18 |

**Notes on D11 and D12 (settled 2026-11-07).** D11 is the smallest sound rule (the leftover must be droppable) and
matches prior art, in which linear languages destructure only. D12 was chosen as option P1 (consume everywhere). It
overrides shipped v0.13 behaviour, narrowing through a struct pattern (RFC-0071 legality-4, RFC-0137 slice 2); explicit
field moves still narrow. The RFC-0137 text and fixtures change when the `linear` release implements it (#1843). The
class-dependent variant P2 (`..` leaves a residual when the scrutinee is known `Discard`, otherwise consumes) is the
recorded fallback if P1 proves too costly.

## Part 3. How the decisions depend on each other

```text
D1 D2 D3        classes, declared classes, sealed Copy        (settled; independent of linear)
   |
  D4 D5 D6      capabilities are bounds; Discard computed     (settled; inert until `linear` ships)
   |
  D7            computed class of generic instances           <- keystone, accepted 2026-11-07
 / | \
D8 D9 D10       conditional keywords, bound repetition, guard
   |
  D11           nominal partial moves need known Discard
   |
  D12           patterns consume
   |
  D13           Drop dismantling by a marked method           (accepted in design; takes effect with D11, D12)
D19 (pub states Discard)  depends on D7, D18; guards the public interface of D7
D14 (closures, accepted)  depends on D7
D15 (RFC-0220, deferred)  depends on D7, D11
```

**D7 was settled on 2026-11-07** as the open-by-default model, with D8, D9 and D19. The reasons: in the effects-library
test 24 of 31 parameters are moved rather than dropped, so annotating the dropping minority (8 annotations) is cheaper
than annotating the moving majority (29); Mojo moved toward written destruction bounds; D19 answers the public-API
instability; and the `T: Discard` bound is vacuous in v0.16.0, so the choice is cheapest to change now. The paragraph
below records what a reversal would cost.

**If D7 were wrong:** D8, D9 and D10 are replaced by an explicit-class model (generic types declare which parameters
may be linear, as Austral and Swift do). D11 and D12 survive unchanged, because they depend on whether the class is
known, not on how it is computed. D13 is unaffected. The std library gains annotations on every generic container.

**If D12 is wrong:** only the pattern rule reverts to Rust's residuals, plus a separate ban on residuals of
non-`Discard` aggregates. D7 to D10 are unaffected.

**If D4 is wrong:** the written `T: Discard` spelling changes, but in v0.16.0 the bound is vacuous, so the change is
cheap now and expensive after std is annotated.

## Part 4. Probe questions

Answer these without looking, then check against the text.

1. `fun first<T>(p: Pair<T>) -> T { p.a }` with the named struct `Pair<T> { a: T, b: T }`. Does it compile once
   linear ships? **No.** `Pair<T>` is not known `Discard`, so the field move leaves a residual the compiler cannot
   drop. Fix: `T: Discard`, or `let Pair { a, b } := p; a` (but then `b` must be handled).
2. Same, but `p` is an anonymous record `{ a: T, b: T }`. **Yes** for the field move. It narrows to `{ b: T }`, whose
   class is recomputed, and returning without using `b` is then an error unless `T: Discard`.
3. `struct Cache<T> { marker: &T }`. Is `Cache<Tx>` linear? **No.** It owns a reference, which is `Discard`.
4. Add `ticket: Ticket<T>` where `linear struct Ticket<T> { id: i64 }`. What must change on `Cache`? It must now be
   declared `linear struct Cache<T>`, because the new field is linear for every `T`.
5. `fun f<T>(x: T) { let g := || { use(x); }; }`. Why can't `g` be dropped? It captures a possibly-linear `T`, so it
   must be a `linear` closure or `T` must be `Discard`.
6. What does `into_inner` on `Logged<i64>` do that dropping a `Logged<i64>` does not? It skips the destructor
   ("gone" is not logged).
7. `let Envelope { tx, .. } := e;` where `label: String` is the skipped field. Why is it allowed? `String` is
   `Discard`, so skipping is fine. Skipping `tx: Tx` would be an error.
8. Why can a non-linear user ignore all of this? Every type they use is `Discard`, so every check passes trivially.

## Part 5. Reading order

1. RFC-0206 section 2 and the model overview (`copy-clone-settlement-model-overview.md`): classes, `Copy`, `Clone`.
2. RFC-0089 section 1 and 2.1: declared classes and the keywords.
3. RFC-0089 section 2.2: capabilities as bounds, the demonstration, the std audit, and the rejected alternatives.
   This is where D4 to D10 are argued.
4. `reference/spec/ownership.md`, "Ownership classes" and "Partial moves": the rules in normative form.
5. RFC-0194 and RFC-0219: closures and function types.
6. RFC-0220: binding-level qualifiers (draft).
7. `copy-clone-prior-art-survey.md` and `generic-class-computed-vs-explicit.md`: how other languages answer
   the same questions, and the side-by-side programs for D7.

## Part 6. Where the real uncertainty is

In order of how much I would want more time on:

1. **D7, computed generic classes (now accepted).** It is the only decision that touches every generic type, and it is the hardest
   to reverse once std is written. The comparison report puts the two models side by side.
2. **D13, `Drop` dismantling (accepted in design, marker spelling open).** The most speculative: no prior art handles
   `Drop` plus conditional capability this way, and it needed three review rounds to reach a coherent form; the explicit
   marker replaced the vaguer "own methods" boundary.
3. **D12, patterns consume.** It is a deliberate divergence from Rust and it overrides an implemented v0.13.0
   behavior. The reason (the language reads `{ x, .. }` as consumption) is sound, but it is a language-feel decision,
   not a soundness one.
4. **D19, stated `Discard` for public generic types (now accepted).** It answers the public-API instability of D7, but it adds a
   declaration-site statement for a capability otherwise computed, and the conservative default can over-restrict
   public types that do not own their parameter.
5. **D4, the written `T: Discard` bound.** The cost (about 30 to 40 percent of by-value generic functions) is large,
   though it is the same kind of cost as `Copy` bounds and Metel has no users to migrate.

Decisions D1 to D6 and D18 are the part of the design that does not depend on linear types being right.
