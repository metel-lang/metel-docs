---
id: rfc-0045
title: "Closure Capture Lists"
date: '2026-06-03'
status: draft
---

## Summary

Add an optional capture list syntax to closure expressions that allows individual outer bindings to be captured by mutable reference. This enables a closure to mutate outer-scope state without requiring a separate `*mut` pointer binding in the outer scope, while keeping the mutation intent explicit at the closure definition site.

---

## Motivation

Closures in Metel currently capture all outer bindings by value (deep clone at creation time). To share mutable state between a closure and its enclosing scope, the programmer must explicitly declare a `*mut` pointer in the outer scope before the closure is defined:

```metel
fun main() {
    let mut count = 0;
    let p: *mut Int = &mut count;   // extra binding required

    let inc = () -> () { *p += 1; };
    inc();
    inc();
    // count is now 2
}
```

This pattern works but carries a cost: `p` is a binding whose sole purpose is to outlive the closure capture window. It adds a name to the scope that has no semantic value beyond enabling the share, and it distances the expression of intent (mutation of `count`) from the place where it matters — the closure definition.

An attempt to take `&mut count` inside the closure body does not work — the closure's captured environment is a deep clone, so the pointer targets the copy, not the original binding. This is a non-obvious gotcha that the current documentation has to explain at length. Tests 72–74 in `tests/evaluator/sources/closures/` confirm and document this behaviour.

A capture list allows the programmer to declare the mutable capture at the closure site, eliminating the extra binding and making the intent legible without sacrificing explicitness.

---

## Proposal

Extend the closure expression syntax with an optional capture list placed before the parameter list:

```
closure_expr  = capture_list? "(" params ")" "->" return_type block
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&mut" ident
```

Bindings named in the capture list are captured by mutable reference rather than by value. Inside the closure body they are used with ordinary read and assignment syntax — no pointer dereference required:

```metel
fun main() {
    let mut count = 0;

    let inc = [&mut count] () -> () {
        count += 1;
    };

    inc();
    inc();
    assert(count == 2);
}
```

Bindings not listed in the capture list continue to be captured by value (deep clone), preserving the current semantics for the common case.

### Semantics

- At closure creation time, each `&mut ident` capture takes the address of the named binding (equivalent to the existing `&mut ident` address-of operation) and stores the resulting `*mut T` in the closure's captured environment.
- Inside the closure body, reads and writes of a by-reference-captured binding are automatically routed through the stored pointer. The programmer never sees the pointer explicitly.
- The outer binding must be declared `let mut`. Attempting to capture a non-mutable binding via `&mut` is a compile error.
- A binding may not appear in both the capture list and the value-captured portion of the same closure's environment (no dual capture of the same name).

### Read-only reference captures

This RFC covers only `&mut` captures. Read-only reference capture (`&ident`) is deferred; value capture already handles the immutable case adequately.

---

## Alternatives Considered

### Keep requiring an outer `*mut` pointer (status quo)

Works today. Verbose, non-obvious, and puts a semantically empty binding in the outer scope. Rejected as the permanent answer given the ergonomic cost.

### Allow `&mut ident` inside the closure body

Syntactically simple but does not work under the current capture semantics — the closure holds a deep-cloned copy, so the internal pointer targets the copy, not the original. Making it work would require abandoning deep-clone capture entirely or adding a special case that distinguishes "address-of a captured binding" from "address-of a local binding", both of which are more invasive than a capture list.

### Implicit mutable capture

Allow closures to detect at analysis time that a captured binding is assigned and automatically capture it by reference. Rejected: breaks the design principle that mutation is always explicit in Metel, and makes closure behaviour harder to reason about from the definition site alone.

### Exhaustive capture lists

Require every captured binding to appear in the list, with `&mut` or by-value markers. More explicit, but adds significant boilerplate for the common case where most captures are read-only values. Deferred as a possible opt-in lint or future strict mode, not a language requirement.

---

## Open Questions

1. **Lifetime of the mutable reference.** With the current interpreter the outer binding's storage lives as long as its `Rc` cell, so there is no unsoundness. Under a future compiler with stack allocation, a closure holding a `&mut` to a stack binding must not outlive that binding. This RFC does not resolve the lifetime story; it defers to the linear types / borrow checker RFC.

2. **Interaction with concurrency.** A closure holding a mutable reference to an outer binding must not be sent to another thread without synchronisation. The capture list makes this visible (the closure type could be marked non-`Send`), but the mechanism is not specified here.

3. **Multiple closures capturing the same binding.** Two closures with `[&mut x]` in the same scope both hold a mutable pointer to `x`. This is safe in the single-threaded interpreter (sequential calls) but is aliased mutation. Under linear types or a borrow checker this would require further restrictions. Deferred.

4. **Syntax alternatives.** `[&mut x]` reuses existing syntax and reads naturally given RFC-0043. Alternatives such as `mut(x)` or a `capture` keyword have been considered but are not preferred.

---

## Timing Recommendation

This RFC should not be implemented before at least a prototype design exists for linear types (see the Memory and Reference Model RFC). The capture list is semantically a borrow, and the two features need a compatible story for lifetime checking before the interpreter implementation can be considered sound under a future compiler. Implementing it in the interpreter as syntactic sugar over the existing `*mut` pointer mechanism is safe for the short term, but the semantics must be locked down before the compiler milestone.

**Prerequisite:** RFC-0043 (Regular Pointers and Mutable Pointers) — already implemented.

**Suggested order:** linear types RFC accepted → this RFC implemented in interpreter → compiler picks up native reference semantics.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0041: Lambda Syntax for Anonymous Functions
- RFC-0043: Regular Pointers and Mutable Pointers
- Closure capture tests: `tests/evaluator/sources/closures/72_closure_internal_ptr_no_outer_effect.mtl`, `73_closure_direct_assign_no_outer_effect.mtl`, `74_closure_external_ptr_affects_outer.mtl`
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
