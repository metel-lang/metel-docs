---
id: rfc-0195
title: "Local Functions Do Not Capture"
date: '2026-10-30'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1709'
---

> **Status — under review (2026-10-30).** design drafted; tracked by metel-core#1709 (v0.15.0)

> **Rewritten (2026-10-30).** This RFC first proposed the opposite: that a local `fun` follow the closure
> capture rules (a capture list on the declaration, a capturing `fun` not hoisted). On review the rule was
> reversed: a `fun` is an item and never captures, a closure is the form that has an environment, and the
> two gaps that left (a generic helper that captures, a recursive one) are filled on the closure side by
> RFC-0197 and RFC-0198. The first design is kept as Alternative 1.

## Summary

A `fun` declared inside a function body is an **item**, not a value with an environment. It does not
capture: naming a local of the enclosing function (a parameter, a `let` or `var`, or a closure's capture) from
its body is a compile error, and the closure is the fix. One test then decides which form to write: *does it
have an environment?* If yes, it is a closure; if no, it is a `fun`.

```metel
fun main() {
    var n := 0;
    fun bump() { n += 1; }          // error[T0003]: `bump` is a function and cannot use `n`, a local of `main`
    //   help: bind a closure, which captures:   let bump := [&var n] var || { n += 1; };
    //   help: or pass `n` as a parameter:       fun bump(n: &var i64) { n += 1; }
}
```

Today the behaviour is unspecified and inconsistent (metel-core#1708): a non-generic local `fun` reads and
mutates enclosing locals with no capture list, a generic one is `I0010` or a type mismatch, and the enclosing
function's type parameters are unusable with a misleading message. This RFC replaces all of that with one
stated rule.

---

## Motivation

### The current behaviour is an accident

Measured on `develop` (87b7c06a and later):

| local `fun` that mentions an enclosing name | result |
|---|---|
| a `let` or `var`, non-generic | accepted; reads and mutates it; no list, no qualifier, none of the closure checks |
| a local, generic | `I0010` (the definition is accepted and reconstruction rejects the name), or `T0001` when the type is an opaque enclosing parameter |
| a type parameter of the enclosing function | `T0001: expected T, found type parameter T`, which does not say the name is out of scope |
| a sibling local `fun`, or a local `record` | accepted; these are items |

`reference/spec/functions.md` has no rule. The closure rules (legality 6 to 25) make every capture visible at
the creation site; a non-generic local `fun` bypasses all of them.

### What uses it

A scan of the project (fixtures, standard library, spec, tutorial, RFC examples; a heuristic over tokens, so a
lower bound for user code) finds 15 nested `fun` declarations, none in the standard library, and 2 that use an
enclosing name:

- `evaluator/functions/79_nested_fun_forward_ref_in_let_initializer` (metel-core#712), where a nested `fun`
  mutates an enclosing `var hit`. It tests forward references, not capture.
- `typechecking/generics/rigid_nested_function_captures_enclosing_parameter` (RFC-0173 D1), a negative test.

Neither is a program that depends on capture. The other 13 are items.

### Why a function does not capture

- **A `fun` is an item.** It is hoisted, exportable (`public fun`), usable in methods and aspects, and has a
  written signature (RFC-0193). Giving it an environment adds an exception to each: a capturing `fun` cannot be
  hoisted, needs a capture list on a declaration, and has a type that depends on what it captured.
- **Captures are already specified for closures** (RFC-0050, RFC-0153, RFC-0157). Making a `fun` capture means
  either duplicating those rules on a second form, or letting the form bypass them, which is today's accident.
- **The two gaps are closure gaps.** A generic or bounded helper that captures state wants a generic closure
  (RFC-0197). A recursive one wants a recursive closure (RFC-0198). Neither wants a different kind of `fun`.

### Precedent

Rust's nested `fn` items cannot capture (`E0434`) or use the enclosing generics (`E0401`), and Zig has no
closures; both use a separate closure or a struct for state. Go has no local named functions. Swift, Kotlin and
Scala let a local function capture implicitly; Metel's captures are explicit (RFC-0050), and implicit capture on a
declaration would be the one place they are not written.

---

## 1. The rule

A local `fun`'s body can see:

- its own parameters, locals and type parameters;
- module-level items, types, aspects and constants;
- items declared in an enclosing block: sibling local `fun`s and local `record`/`enum`/`struct` types.

It cannot see the **locals of an enclosing function**: parameters, `let` and `var` bindings, the receiver `self`,
and the captures of an enclosing closure. It cannot see the **type parameters of the enclosing function**; a
local generic helper declares its own `<T>`.

1. **A reference to an excluded name is `T0003`** (undefined name) with a note that the name is a local of the
   enclosing function and the two fixes: bind a closure, or pass it as a parameter. A type parameter gets the
   note "`T` is a type parameter of `outer`; declare `<T>` on `inner`".
2. **Hoisting is unchanged and now uniform.** Every local `fun` is hoisted in its block; sibling local functions
   may be mutually recursive.
3. **A local function inside a closure** sees the closure's captures and parameters as locals of the enclosing
   function, so it cannot use them either.
4. **Module-level functions and methods** are unchanged; they have no enclosing locals.

### Diagnostics

| situation | message |
|---|---|
| a local name used from a local `fun` | `` `bump` is a function and cannot use `n`, a local of `main` ``; help: bind a closure (the rewrite with its capture list), or pass it as a parameter |
| an enclosing type parameter used from a local `fun` | `` `T` is a type parameter of `outer`; declare `<T>` on `inner` `` |

---

## 2. What this amends

- **RFC-0173 D1**: "a closure or nested generic function inside a generic body sees the enclosing parameters as
  rigid" becomes "a closure sees the enclosing parameters as rigid; a nested generic function declares its
  own." The negative fixture `rigid_nested_function_captures_enclosing_parameter` becomes a name error.
- **Fixture `79_nested_fun_forward_ref_in_let_initializer`**: the `var hit` case becomes a closure or a
  parameter. The forward-reference cases are unchanged.
- **`spec.functions`**: a rule for local functions (no enclosing locals), pointing at the Closures rules for the
  alternative.

---

## Alternatives Considered

1. **Local functions follow the closure capture rules** (this RFC's first draft, 2026-10-30). A `fun` with free
   locals is a capturing local function: capture list after the name and generics
   (`fun name<T>[caps] once? var? (params)`), writing `var` makes the name a `var` binding, mutual recursion
   between capturing local functions forbidden, a capturing local function not hoisted. Closure rules apply
   unchanged. Gives a recursive, generic, bounded, capturing helper in one form. Rejected: it adds a capture list
   to a declaration, a hoisting exception, and a second way to spell a capturing function, for the benefit of the
   recursive-and-capturing case that RFC-0198 now covers on the closure side.
2. **Implicit capture, made uniform** (today's non-generic behaviour, and Swift/Kotlin). Rejected: it is the
   one place captures would not be written, and it bypasses the closure checks.
3. **Forbid only the generic form.** Fixes `I0010` and leaves the non-generic capture; the inconsistency stays.

---

## Interactions

- **RFC-0197 (generic closures)** is the replacement for a generic, bounded or row-fact helper that captures
  state. Until it is accepted, such a helper takes its state as a parameter.
- **RFC-0198 (recursive closures)** is the replacement for a recursive helper that captures state. Until it is
  accepted, such a helper takes its state as a `&var` parameter, as in the Summary.
- **RFC-0193** (named declarations write their signature) applies to local functions as to any `fun`.
- **RFC-0196** (remove inferred let-polymorphism): a polymorphic local helper is a `fun<T>` (no state) or a
  generic closure (state).
- **RFC-0050, RFC-0153, RFC-0157, RFC-0194:** closure rules, untouched.
- **GAP-FUNCTIONS-006, GAP-FUNCTIONS-007:** closed on the closure side by RFC-0198 and RFC-0197.
- **metel-core#1708:** this RFC is the design; the interim fix is the clean diagnostic in section 1.

---

## Migration

A local `fun` that uses an enclosing name becomes a closure with a capture list, or takes the name as a
parameter; the compiler prints both. In the project it affects two fixtures; user code is not measured. A hard
cut, as the project has no warning channel (RFC-0187).

---

## Open Questions

1. **Error code.** `T0003` with an enriched message (recommended), or a new code. A new code adds a spec row for
   a message that reads the same.
2. **Enclosing type parameters.** Out of scope, as in Rust (recommended), or visible and rigid (RFC-0173 D1 as
   written). Out of scope matches what the checker does today and makes a local generic helper self-contained.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: a legality rule for local functions (the
visible names above, `T0003` for the rest) and a dynamics note that they are hoisted. RFC-0173 D1's paragraph on
nested generic functions is amended. No new error code is proposed.

## Acceptance criteria for a prototype

- The #1708 repro is one `T0003` in both the generic and the non-generic form, with the closure rewrite.
- A sibling local `fun`, a local `record`, a module-level item and the function's own locals are visible.
- An enclosing type parameter used in a local `fun` is `T0003` with the "declare `<T>`" note.
- The two affected fixtures are rewritten; the forward-reference cases of #712 still pass.

## References

- metel-core#1708: the bug. #1709: this RFC's tracker. #712: forward references of nested functions.
- RFC-0050, RFC-0153, RFC-0157 (closure capture), RFC-0173 (rigid parameters), RFC-0193, RFC-0194, RFC-0196,
  RFC-0197, RFC-0198.
- GAP-FUNCTIONS-006, GAP-FUNCTIONS-007.
- `reference/spec/functions.md`: Closures, legality 6 to 25.

---

## Decision

**Outcome:** *(pending)*
