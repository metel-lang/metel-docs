---
id: rfc-0195
title: "Local Functions Follow the Closure Capture Rules"
date: '2026-10-30'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1709'
---

> **Status — under review (2026-10-30).** design drafted; tracked by metel-core#1709 (v0.15.0)

## Summary

A `fun` declared inside a function body may reference the enclosing function's locals, under the
**same rules as a closure**: a capture list where the closure rules require one, `Copy`/move/`&`/`&var`
capture, the `once` and `var` qualifiers, and the same diagnostics. A local `fun` that references no
enclosing local is unchanged: an ordinary hoisted item.

```metel
fun count_leaves(root: Tree) -> i64 {
    var n := 0;
    fun walk[&var n] var (t: Tree) {      // recursive, captures n by &var, mutating
        match t {
            Tree.Leaf => { n += 1; },
            Tree.Node { left, right } => { walk(left); walk(right); },
        }
    }
    walk(root);
    n
}
```

Today the behaviour is unspecified and inconsistent (metel-core#1708): a non-generic local `fun`
silently reads and mutates enclosing locals with no capture list, and a generic one is `I0010`.
This RFC replaces both with one stated rule.

> **Prepared for acceptance (2026-10-30).** All five open questions are resolved; the rules for a `var` local
> function and for mutual recursion are added as rules 8 and 9.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### The current behaviour is an accident

Measured on `develop` (87b7c06a):

| local `fun` that references an enclosing local | result |
|---|---|
| non-generic | accepted; reads and mutates the local; no capture list, no qualifier, no check |
| generic (`<T>`) | `I0010`: the definition is accepted and reconstruction rejects `n` as undeclared |
| the same body as a closure | requires `[&var n]` and `var` (RFC-0050, RFC-0153); `T0028` otherwise |

`reference/spec/functions.md` has no rule on whether a local function may see enclosing locals. The
closure rules (legality 6 to 25) deliberately make every capture visible at the creation site; a
non-generic local `fun` is a way around all of them.

### A real use only a capturing, nameable function has

A **recursive** helper that accumulates into an enclosing `var` (the Summary example) cannot be a
closure: a closure cannot refer to its own name (GAP-FUNCTIONS-006). It can be a module-level `fun`
only by passing the accumulator through every call. Likewise a **generic** helper that closes over
state cannot be a closure, which has no type-parameter list (GAP-FUNCTIONS-007, accepted: closures stay
bound-free). The local `fun` is the form that has a name, can recurse and can be generic, so it is where a
capturing helper of that shape belongs. This RFC is the resolution path for GAP-FUNCTIONS-007: a helper
that needs a type parameter, a bound or a row fact, a capturing one included, is a local `fun`.

This also bounds what RFC-0193 and any restriction of closure let-polymorphism can ask of users: if
a polymorphic closure becomes a written `fun f<T>`, a polymorphic closure that captured state needs
this RFC to keep working.

### Rust forbids it

Rust's nested `fn` items cannot capture (`E0434`: can't capture dynamic environment in a `fn`).
That is the smallest consistent rule (Alternative 1) and is a legitimate outcome. This RFC proposes
the other consistent rule because Metel's closures already carry a full capture contract that
local functions can reuse unchanged.

---

## 1. The rule

A `fun` declared in a block is a **local function**. Its **free locals** are the bindings of the
enclosing function (parameters, `let`, `var`, and the captures of an enclosing closure) that its body
references. Module-level items, types and aspects are not free locals (as for closures).

1. **No free locals:** an ordinary item. Hoisted, callable before its declaration, not a value with
   an environment. Unchanged.
2. **Free locals:** the local function is a **capturing local function**. Its captures are classified
   by the closure rules without modification: the capture list is required if a free non-`Copy` local
   is referenced or anything is captured by `&` or `&var` (legality-6), is exhaustive (legality-7),
   `[&var x]` needs `x` declared `var` (legality-13) and implies `var` (legality-25), consuming a
   capture needs `once` (legality-8), and so on. The checks, stage order (legality-19) and
   diagnostics (`T0026` to `T0029`) are the closure ones; no new code.
3. **Where the capture list is written:** after the name and any type parameters, before the
   parameters, in the order a closure literal uses (`[captures] once? var?`):

   ```metel
   fun name<T>[&var n, s.clone()] once var (x: T) -> T { … }
   ```

   It is omitted exactly when a closure's would be (every free local is `Copy` and captured by value,
   or there are none).
4. **Recursion is not a capture.** The function's own name refers to the function. A capturing local
   function may call itself; it does not list itself.
5. **Generics.** Type parameters of the local function and of the enclosing function are usable in
   the signature and body, and the local function carries bounds, a `where` clause and row facts as any
   `fun` does. The capture analysis runs once, on the definition, and instantiation reuses it (this is
   what #1708's `I0010` fails to do). A captured binding's type cannot mention the local function's
   **own** type parameters (the environment exists before any instantiation); a capture whose type mentions
   a type parameter of the *enclosing* function is allowed. A violation is one error: "a capture is formed
   before the function is instantiated; its type cannot mention `T`".
   A generic local function is referenced as `first-class-functions.legality-2` (RFC-0138) allows: called,
   bound with a bare unannotated `let`, or passed where the receiving parameter is concrete. Polymorphism
   is rank-1.
6. **The name's type.** A capturing local function is a value with an environment: its type is the
   function type with the multiplicity and mutation its captures and qualifiers give (RFC-0152,
   RFC-0153, RFC-0163), it is `Copy` exactly when all its captures are (legality-20), and written
   function types lower to move-only (RFC-0166). A non-capturing one keeps the item type.
7. **Evaluation order.** A capturing local function's environment is formed when control reaches its
   declaration, in capture-list order (dynamics as for a closure). It is therefore **not callable
   before its declaration**: a use earlier in the block is a compile error naming the first free
   local, where a non-capturing local function remains hoisted. This is the one place a local `fun`
   stops being hoisted.
8. **A `var` local function.** Writing `var` on the declaration makes the function's name a `var` binding
   for the purposes of RFC-0153's mutating-callee rule; no further syntax is needed. (The current
   implementation does not yet require a `var` binding for any closure call; this rule states what the
   end-state check will require, and adds nothing the closure rules do not.)
9. **Recursion is self-recursion only.** A capturing local function may call itself and any function
   declared before it. Two capturing local functions that call each other are an error, because the first
   would be used before the second's declaration (rule 7); one takes the other as a parameter instead.
   Non-capturing local functions are hoisted and may be mutually recursive as today.

### Diagnostics

| situation | message |
|---|---|
| free non-`Copy` local, no list | the closure message (`T0026`) naming the local and the fix (add the list, or pass it as a parameter) |
| mutates a capture without `var`; consumes without `once` | `T0028`; `T0027`, as for a closure |
| capturing local function used before its declaration | "`walk` captures `n`, so it is not available before its declaration" |
| a free local used where the function is hoisted and the list is absent | as the first row; there is no silent capture |

---

## 2. What does not change

- **Module-level functions, methods, aspect methods** never capture. A module-level `fun` cannot see
  any local (it has none in scope).
- **Closures** are unchanged. A local `fun` with captures is a closure that has a name, a type-parameter
  list and a hoisting exception; it is not a new capture model.
- **RFC-0193** (named declarations write their signature) applies to local functions as to any named
  declaration: parameters and return type are written. The capture list is part of the signature
  only for the declaring block; it is not a public interface.

---

## Alternatives Considered

1. **Local functions never capture (Rust).** Reject a reference to an enclosing local from a local
   `fun` with a clean diagnostic ("a function cannot capture; bind a closure"). Smallest change, no
   new syntax, local `fun` stays a pure item and stays hoisted. It leaves the recursive accumulator
   and the generic state-carrying helper without a local spelling: they pass state through parameters
   or move to a module-level `fun`. A legitimate outcome; this RFC picks the other rule because the
   capture contract already exists.
2. **Implicit capture (today's non-generic behaviour), made uniform.** Make the generic form work
   the same way. Rejected: it makes a local `fun` the way to mutate or move a local with none of
   the closure checks, which contradicts the reason closures write their captures (RFC-0050).
3. **Generic closures** (`<T>|x: T| …`, RFC-0197) instead of capture on `fun`. Solves the generic half, not
   recursion (GAP-FUNCTIONS-006), and is a larger feature with new closure grammar. Considered alongside
   this RFC and deferred (2026-10-30): the local `fun` already covers a generic, bounded, capturing helper, and
   the generic closure's remaining value is the terse form that infers its signature.
4. **Capture list on every local function, even with no free locals.** Rejected: an empty list on
   a pure helper is noise, and the rule above already makes the list required only when a closure's
   would be.

---

## Interactions

- **RFC-0050 (capture lists), RFC-0153 (mutation axis), RFC-0157 D5 (move default), RFC-0152 /
  RFC-0163 (function-type multiplicity), RFC-0166 (written function types):** reused unchanged.
- **RFC-0194 (linear closures):** a capturing local function that captures a `Linear` value is linear,
  by the same derivation. Nothing local to this RFC.
- **RFC-0196 and RFC-0197:** RFC-0196 removes inferred polymorphism from closures; a polymorphic helper that
  captures state is spelled as a capturing local `fun<T>` (this RFC). RFC-0197 (generic closures) would have
  added a closure spelling and is deferred; it is compatible with this RFC and records the closure binder order (binder
  first, matching this RFC's).
- **RFC-0131 (hoist `let`/`var`):** if accepted, a captured binding is hoisted for name resolution but
  still initialised in order; rule 7 still holds, because the environment is formed at the declaration.
- **RFC-0193:** see section 2. Together they let a closure suggestion be replaced by a local `fun`
  that keeps its captures.
- **GAP-FUNCTIONS-006 / 007:** a capturing local function is the existing spelling for a recursive
  or generic capturing helper; neither gap is closed.
- **metel-core#1708:** the I0010 and the missing rule. Its fix is the interim clean diagnostic until
  this RFC is accepted.

---

## Migration

A non-generic local `fun` that references an enclosing local today needs a capture list, or the local
passed as a parameter. Not yet measured: a scan of the corpus (fixtures, spec, tutorial) for local
functions with free locals is an acceptance step, and decides whether a hard cut is cheap. The compiler
knows the free locals at the error and can print the list to write.

---

## Open Questions — resolved 2026-10-30

1. **Where the list goes.** *Resolved: after the name and generics.* `fun name<T>[caps] once? var? (params)`:
   the name stays first, and the list sits next to the qualifiers and parameters in the closure literal's
   `[captures] once? var?` order. The closure literal, if RFC-0197 is ever revived, puts its binder first
   too (`<T>[caps] once var |…|`), so the two forms agree.
2. **How a `var` local function is called.** *Resolved: writing `var` makes the name a `var` binding* (rule 8).
   No `var fun` form. The wording of this question previously said a mutating closure must be called through a
   `var` binding; that is RFC-0153's end state, not what the implementation enforces today, and rule 8 now says so.
3. **Mutual recursion.** *Resolved: forbidden between capturing local functions* (rule 9); a later RFC can add
   declaration groups with a shared environment.
4. **Hoisting.** *Resolved: a capturing local function is not hoisted* (rule 7). Hoisting with an
   initialisation check was rejected as harder to explain and as interacting with RFC-0131.
5. **Should this be done at all?** *Resolved: yes* (language owner, 2026-10-30: local functions follow the same
   capture rules as closures). Rust's rule (Alternative 1) stays recorded as the considered alternative.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: a rule under *Named Function
Declarations* for local functions with free locals, pointing at the *Closures* legality rules rather
than restating them; the *hoisting* statement gains the capturing-local-function exception.
`modules.md` unchanged. No new error code is proposed.

## Acceptance criteria for a prototype

- A capturing local function that calls a later capturing local function is the stated error; the same pair, non-capturing, still compiles.
- A `var` local function mutates its capture when called, and the same body without `var` is `T0028`.
- The Summary example type-checks with `--move-check` and runs; the same body without `[&var n] var`
  is `T0028`.
- A generic capturing local function instantiated at two types (the #1708 shape) compiles; none gives `I0010`.
- A non-capturing local function remains hoisted and unchanged.
- A capturing local function used before its declaration is the stated error.
- The corpus scan (Migration) has a number.

## References

- metel-core#1708: the bug that prompted this RFC.
- RFC-0050 (closure capture lists), RFC-0153 (mutation axis), RFC-0157 (capture default), RFC-0152 and
  RFC-0163 (function-type multiplicity), RFC-0166, RFC-0194 (linear closures), RFC-0131 (hoisting),
  RFC-0193 (named declarations do not infer).
- GAP-FUNCTIONS-006 (a closure cannot call itself), GAP-FUNCTIONS-007 (a closure cannot name a type
  parameter, bound or row fact).
- `reference/spec/functions.md`: Closures, legality 6 to 25.

---

## Decision

**Outcome:** *(pending)*
