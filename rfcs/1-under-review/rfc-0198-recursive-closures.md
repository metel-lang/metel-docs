---
id: rfc-0198
title: "Recursive Closures"
date: '2026-10-30'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1667'
---

> **Status — under review (2026-10-30).** design drafted; tracked by metel-core#1667 (v0.15.0)

## Summary

A closure bound with `let rec` may call itself by its own name. The name inside the body refers to the closure
being called, not to a captured copy or reference of the binding, so the closure's environment gains no cycle
and the closure can still be moved, returned and passed. A recursive helper that captures state becomes a
closure, which is where state lives (RFC-0195).

```metel
fun count_leaves(root: Tree) -> i64 {
    var n := 0;
    let rec walk := [&var n] var |t: Tree| -> () {
        match t {
            Tree.Leaf => { n += 1; },
            Tree.Node { left, right } => { walk(left); walk(right); },
        }
    };
    walk(root);
    n
}
```

This resolves GAP-FUNCTIONS-006 (metel-core#1667) with the first of its two stated options (a recursive
binding form); the second, a documented decision to keep recursion to named functions, is Alternative 1.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### What a closure cannot do

`let fact := |n: i64| { … fact(n - 1) };` is `T0003`: the name is bound after the initializer, so it is not in
scope in the closure's own body (`scoping-and-shadowing.legality-2`). A `fun` recurses freely
(GAP-FUNCTIONS-006).

### Why it matters now

- **RFC-0195** makes a local `fun` an item that does not capture. A helper that is both recursive and
  captures state, such as the tree walk above, then has no spelling: not a `fun` (no capture), not a closure
  (no self-reference). The workaround is Rust's, passing the state as a `&var` parameter.
- **RFC-0197** gives a closure generics and bounds. Recursion is the other thing a `fun` has that a closure
  lacks.
- RFC-0193 withholds its closure suggestion for any function that calls itself, directly or through others.

### Precedent

ML marks recursion with `let rec`; in Haskell every `let` and `where` binding is recursive by default. Go
declares the variable first (`var f func(int) int; f = func…`). C++23 gives a lambda an explicit object parameter
(`this auto&& self`), and Rust has no recursive closures: it passes state to a `fn` or a `&dyn Fn` to itself.

---

## 1. The rule

1. **`let rec name := closure`.** The name is in scope in the closure's own body, in addition to the rule that a
   `let` is visible after its declaration. `let rec` is valid only when the initializer is a closure literal.
2. **The name denotes the closure being called.** A call `name(args)` inside the body is a call on the same closure
   value that is executing, through the dispatch every closure call already uses (RFC-0153: the callee is reached
   as `&self` / `&var self`). It is not a capture. The closure's environment is the same as for a closure without
   `rec`; nothing refers to the binding, so the closure can be moved, returned and passed after its declaration.
3. **The return type is written.** A recursive call needs the result type before the body is solved, and
   RFC-0193's philosophy keeps inference inside one body. The parameters may be inferred as for any closure
   (RFC-0196: one type, fixed by use).
4. **Recursion is monomorphic.** The recursive call is at the closure's own type. With a generic binder
   (RFC-0197) it instantiates at the same arguments (no polymorphic recursion).
5. **A `once` closure cannot be `rec`.** It is consumed by its first call, so a recursive call would be a use after
   move. The error names the `once` qualifier.
6. **Qualifiers and captures** are unchanged and checked on the closure as written. A recursive call in a `var`
   closure re-borrows the `&var self` that the outer call already holds; in a `many` closure it reads `&self`.
   **This amends RFC-0153 §3a.** The runtime guard that raises `R0015` ("re-entrant call to a mutating closure")
   fires on any second call to a mutating closure that is still executing, because §3a assumes "a closure cannot
   name its own `let` binding, so never directly". A direct self-call through the `rec` name is not reentrancy
   through an alias; it is a reborrow, sound for the same reason a `&var self` method may call itself. The guard
   keeps catching reentrancy through any other path (a stored handler, an aliasing `&var` binding), and RFC-0122
   rejects those statically. The guard itself is scheduled for removal once RFC-0122 is default-on
   (metel-core#1712), at which point this exemption is moot.
7. **No mutual recursion.** `let rec a := …` cannot refer to a later `b`. Two closures that call each other pass
   one to the other as a parameter. (A declaration group is a later RFC.)

### Diagnostics

| situation | message |
|---|---|
| `let rec` on a non-closure initializer | "`let rec` binds a closure" |
| `let rec` without a written return type | "a recursive closure writes its return type" with the inferred type as the help, where it can be computed |
| `let rec` with `once` | "a `once` closure is consumed by its first call and cannot call itself" |
| the name used in a closure not bound with `rec` | `T0003`, with the help "bind it with `let rec`" |

---

## 2. What does not change

- A closure without `rec` is unchanged: it cannot call itself.
- Local and module-level `fun`s recurse as before, and sibling local functions may be mutually recursive.
- Capture lists, `Copy` derivation, multiplicity and linearity (RFC-0050, RFC-0153, RFC-0157, RFC-0194).

---

## Alternatives Considered

1. **Keep recursion to named functions** (the other resolution GAP-FUNCTIONS-006 names). Smallest: a recursive
   helper that captures state takes it as a parameter. A legitimate outcome. Costs the capturing-and-recursive
   helper its closure spelling, which RFC-0195 now depends on.
2. **A name bound in the closure's initializer** (the binding in scope, captured by reference). Gives the same
   surface, but the closure's environment refers to its own binding: it cannot be moved out of its scope without
   invalidating the reference, and the capture rules would need a self-capture case. Rejected.
3. **An explicit self parameter** (`|&self, n: i64|`, C++23). Needs no `let rec`, but changes the call arity
   from the caller's side and clashes with `self` in a closure inside a method, which already means the method's
   receiver.
4. **A fixpoint combinator in the standard library** (`fix(|self, n| …)`). Library-only, no language change;
   pays an indirection and still needs the explicit self parameter. Compatible with this RFC and not excluded by it.
5. **Inferred return type.** Recursion with an inferred return type is possible under monomorphic recursion.
   Rejected for now: it moves a signature-like fact onto the body; a later RFC can relax rule 3.

---

## Interactions

- **RFC-0195 (local functions do not capture):** this RFC is the recursive-and-capturing spelling.
- **RFC-0197 (generic closures):** `let rec` with a binder, instantiated at its own arguments.
- **RFC-0193:** the closure suggestion can drop its "does not call itself" condition for a function whose
  recursion `let rec` expresses, if both are accepted.
- **RFC-0196:** a recursive closure is monomorphic, consistent with one type per closure.
- **RFC-0153 (call dispatch on `&self` / `&var self`):** rule 2 relies on it. Confirmed against the
  implementation 2026-10-30 (`evaluator/call.rs`, `call_runtime_callable`): the call receives the closure value
  (`RuntimeCallable::Closure(rc)`) and builds the body's environment from it, so the name can be bound in the
  call's environment without entering the captured one, and no cycle forms. **§3a is amended** (rule 6): its
  in-call guard (`call.rs`, `rc.in_call.replace(true)` then `R0015`) would otherwise reject the first recursive call
  of a `var` closure.
- **RFC-0131 (hoist `let`/`var`):** unrelated; `rec` is about the initializer's scope, not the block's.

---

## Migration

Additive. `let rec` is a new form; no existing program changes.

---

## Open Questions

1. **Spelling.** `let rec` (ML) is the recommendation; alternatives are `let name := rec |n| …` or a named closure
   expression. Whether `var rec` is needed for a `var` binding.
2. **Return type required.** Recommended (rule 3). Allow inference later?
3. **Self-reference semantics.** *Resolved (2026-10-30), with one required amendment.* The callee is available at
   the call (see Interactions), so rule 2 holds for a `many` closure and for one that owns captures. A `var` closure
   conflicts with RFC-0153 §3a's in-call guard (rule 6).
4. **How a self-call passes the guard.** The evaluator gives the recursive name a call path that neither checks nor
   sets the in-call flag, since the outer call holds it (recommended); or the flag becomes a depth counter
   distinguishing a self-call from a call through another path. The first is smaller and keeps the guard's
   meaning ("another path into a live mutating call") exact.
5. **Mutual recursion** (rule 7): forbid for now, as proposed, or add a group form.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: *Closures*, a rule for `let rec`; the
declaration scoping rule (`scoping-and-shadowing.legality-2`) gains the `rec` exception. RFC-0153 §3a and the `R0015` text in `runtime.md` are amended to exempt a direct self-call. GAP-FUNCTIONS-006 is
resolved. No new error code is proposed.

## Acceptance criteria for a prototype

- The tree-walk example type-checks with `--move-check` and runs; moved into another function it still works.
- A recursive closure without a written return type, with `once`, or on a non-closure is the stated error.
- A `var` recursive closure mutates its capture across calls and does not raise `R0015`; the same body without `var` is `T0028`.
- A mutating closure reached through an alias or a stored handler while it is executing still raises `R0015`.
- `let fact := |n| … fact(n - 1)` is still `T0003`, now with the `let rec` help.

## References

- GAP-FUNCTIONS-006 (metel-core#1667).
- RFC-0195, RFC-0197, RFC-0193, RFC-0196, RFC-0153, RFC-0050, RFC-0131.
- `reference/spec/functions.md` (Closures); `reference/spec/declarations.md` (scoping-and-shadowing).

---

## Decision

**Outcome:** *(pending)*
