---
id: rfc-0220
title: "Binding-Level Linear Qualifiers"
date: '2026-11-06'
status: under-review
updated: '2026-11-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1840'
---

> **Status — draft (2026-11-06).** Designed with the language owner on 2026-11-06 as an extension of the type-level model of RFC-0089 (as amended the same day). Not part of v0.16.0.

> **Status — under review (2026-11-06).** Designed with the language owner as an extension of RFC-0089

## Summary

A type's class is declared (RFC-0089): `copy`, the default affine, or `linear`. This RFC adds a **local discipline** on top: a binding, parameter, return or field may be **stricter than its type**, never looser. The qualifier is `linear`: the value must be consumed exactly once.

```metel
fun open(path: String) -> linear File { ... }     // File is an ordinary affine type
fun close(linear f: File) { ... }                 // the callee consumes f exactly once

fun main() {
    linear let f := open("a");                    // no implicit drop at scope end
    write(&f, "x");                               // a borrow does not consume
    close(f);                                     // consumed exactly once
}
```

An ordinary `File` is dropped (and closed) at scope end. `linear let f` says "I must close this explicitly", without making `File` a linear type for every other user of it. It is a strengthening only, so it is sound locally, adds no type class, and does not spread through containers.

---

## Motivation

- **Must-handle without virality.** Making `File` linear would force `linear` onto every struct that holds one, and onto std types that store it (RFC-0089 section 2, the annotation chain). Most of the time the only thing wanted is that one binding must reach an explicit `close`.
- **A home for guaranteed cleanup of ordinary resources.** Today the options are the implicit `Drop` or making the type linear. The qualifier is the middle.
- **It composes with the settled model.** Types still describe capabilities; bindings carry discipline. Nothing here weakens `linear` types, and nothing is inferred (RFC-0089 amendment, 2026-11-06).
- **Prior art.** Idris 2 puts the multiplicity on binders (`(1 x : T)`), and Linear Haskell on arrows (`%1 ->`); both are verified in the fifth review of the Copy/Clone design. Austral and Swift's `~Copyable` keep it on types. Swift's `consuming` parameter modifier (SE-0377, from memory) is the nearest to a callee-side promise on an ordinary type.

---

## 1. The rule

**Positions.**

| Position | Spelling |
|---|---|
| binding | `linear let x := e;`, `linear var x := e;` |
| parameter and receiver | `fun close(linear f: File)`, `fun m(linear self)` |
| return | `-> linear File` |
| function type | `\|linear File\| -> ()`, `\|T\| -> linear U` |
| field | `struct Pool { linear conn: Conn }` |

`linear` is contextual (RFC-0207) and is written first, like the other prefix keywords. A binding of an intrinsically `linear` type needs no qualifier: the type already forces it.

**Legality.**
1. **Strengthen only.** A binding's discipline is the stricter of its type's class and its qualifier. `linear` is legal on any type. `linear` on a reference parameter (`linear x: &T`) is an error: references do not own.
2. **Exactly once.** A linear binding is consumed exactly once on every path. A consumption is: passing it to a `linear` parameter or receiver; returning it from a `linear` return; destructuring it (rule 3); or passing it to `drop`, which takes a `linear` parameter and requires `T: Discard` (rule 7). A borrow (`&f`, `&var f`) does not consume.
3. **Destructuring inherits** (and is the only way to take a declared linear aggregate apart: RFC-0089 section 2, "Consuming a linear aggregate"). A `match` or `let` pattern on a linear binding consumes it, and each non-`Copy` field binding it introduces is linear. `Copy` fields are copied out and carry no obligation.
4. **No laundering.** A linear binding cannot be moved into an ordinary binding or ordinary parameter, stored in a struct literal field or constructor argument that is not a `linear` field, captured by a closure that is not declared `linear` (RFC-0194), or assigned over. Scope end, shadowing without consuming, a loop body that may consume it twice, and branches that disagree are errors.
5. **Linear results are bound explicitly.** A call to a function with a `linear` return must bind its result with `linear let`, pass it directly to a `linear` parameter, or return it from a `linear` return. Discarding it, or binding it with a plain `let`, is an error whose fix-it writes `linear let`. Nothing is inferred.
6. **Fields.** A `linear` field on a field type that is not itself linear makes the struct hold an obligation, so the struct must be declared `linear struct`. This is checked, and the fix-it adds the keyword. A struct literal may initialise a `linear` field with any value (strengthening). Destructuring the struct yields a linear binding for that field (rule 3).
7. **`drop`.** `drop` takes a `linear` parameter and requires `T: Discard` (RFC-0089 section 2.2). So `linear let f := open(..); drop(f);` is an explicit discard and is legal, and a value of an intrinsically linear type (not `Discard`) cannot be dropped.
8. **Variance in function types.** A function value with a `linear` parameter may be used where an ordinary parameter is expected, since the callee only promises more. A function with a `linear` return may not be used where an ordinary return is expected, since the caller of that slot may drop the result; the reverse is allowed. (To be confirmed in review.)

**Dynamic semantics.** The qualifier has no runtime effect. A linear binding has no scope-end drop: its value is moved into the consuming position, and any destructor runs there (destructor invocation itself is #261).

---

## 2. Worked examples

```metel
fun bad1() { let f := open("a"); }                       // error: a linear result needs `linear let`
fun bad2() { linear let f := open("a"); }                // error: never consumed
fun bad3() { linear let f := open("a"); let g := f; }    // error: cannot move a linear binding into an ordinary one
fun bad4() { linear let f := open("a"); close(f); close(f); }   // error: used after move
fun bad5() { linear let f := open("a"); let c := || { close(f); }; c(); }   // error: capture needs a `linear` closure
fun bad6() { linear let f := open("a"); let h := Holder { file = f }; }     // error: `file` is not a linear field

fun fine() {
    linear let f := open("a");
    let c := [f] linear || { close(f); };     // ok: a linear closure that captures a linear binding
    c();
}

linear struct Pool { linear conn: Conn }
fun finish(linear p: Pool) {
    let Pool { conn } := p;                   // `conn` is a linear binding
    close_conn(conn);
}
```

---

## 3. What this does not do

- **Containers.** Storing a linear binding in `Option<T>`, `List<T>` or a tuple is not allowed (rule 4). A std container holds an intrinsically linear *type* only through the type-level opt-in (RFC-0089 section 2), and this RFC does not change that.
- **Producer-forced obligations** beyond a `linear` return: the creation site cannot force consumption by anything other than rule 5.
- **Weakening.** Nothing makes a type looser than its declared class.

## 4. Staging

Belongs to the "Linear types" theme, after `linear` itself (RFC-0089, metel-core#1831). Needs the consumption analysis of RFC-0089, the `linear` closure of RFC-0194, the function-type qualifier position of RFC-0219, and the partial-consumption rules of RFC-0215. No v0.16.0 work. The contextual keyword positions are reserved with `linear`.

---

## Alternatives considered

1. **Classless types with multiplicity only on binders** (Linear Haskell, Idris 2). No virality and no std opt-in, but the guarantee is conditional ("if the result is consumed once, the argument is consumed once"), and a `Token` can be dropped. Rejected for the capability and exactly-once design (metel-core#1662).
2. **Qualifier-polymorphic types with propagation through containers** (Clean-style uniqueness). Removes the annotation chain and keeps the guarantee, but infers a container's class from what it holds, which reverses the declared-and-checked principle (RFC-0089 amendment).
3. **A field-level `linear` that makes the struct linear by itself.** Inference again; rule 6 requires the keyword instead.
4. **A type qualifier `linear T`** usable inside generic arguments. Raises the propagation question of alternative 2.
5. **An `affine` binding qualifier** (never implicitly copy a `Copy` value). Deferred: the use case is small (accidental copies of `Copy` ids).
6. **`#[must_use]`.** A lint without teeth; this RFC is the checked version.

## Relationship to existing RFCs

- **RFC-0089** — the declared class and `Discard`; this RFC is the designed extension.
- **RFC-0194, RFC-0219** — the `linear` closure and the function-type qualifier position.
- **RFC-0215** — partial consumption of a linear struct stays as there.
- **RFC-0207** — contextual keywords.

## Open questions

1. **Variance** of `linear` parameters and returns in function types (rule 8).
2. **`linear var`.** Whether a mutable linear binding may be reassigned after being consumed (a re-initialisation) or never.
3. **Diagnostic text and error codes.**
4. **`if let` and `while let`** on a linear scrutinee.
5. **Interaction with `?`**: an early return that leaves a linear binding unconsumed is an error; whether a fix-it can suggest consuming it.
6. **`affine` bindings**, deferred (alternative 5).
7. **`dyn`**: whether a linear binding may be coerced into a `dyn Aspect` (the existential-erasure gate, metel-core#1828).

---

## Decision

**Outcome:** *(pending)*
