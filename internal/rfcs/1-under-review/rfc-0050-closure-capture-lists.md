---
id: rfc-0050
title: "Closure Capture Lists"
date: '2026-06-03'
---

## Summary

Add an optional capture list syntax to closure expressions. The capture list supports two specifiers: `&mut ident` captures a non-linear binding by mutable reference, enabling a closure to mutate outer-scope state without a separate `*mut` binding; `move ident` transfers ownership of a linear binding into the closure (RFC-0046). Both specifiers may appear in the same list. All captures are explicit at the closure definition site.

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
capture_item  = "&mut" ident | "move" ident
```

`&mut ident` captures a non-linear binding by mutable reference. `move ident` transfers ownership of a linear binding into the closure (see RFC-0046). Both specifiers may appear in the same list: `[&mut count, move buf]`.

Bindings named with `&mut` in the capture list are captured by mutable reference rather than by value. Inside the closure body they are used with ordinary read and assignment syntax — no pointer dereference required:

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

**`&mut` captures:**
- At closure creation time, each `&mut ident` capture takes the address of the named binding (equivalent to `&mut ident`) and stores the resulting `*mut T` in the closure's captured environment.
- Inside the closure body, reads and writes of the binding are automatically routed through the stored pointer. The programmer never sees the pointer explicitly.
- The outer binding must be declared `let mut`. Attempting to capture a non-mutable binding via `&mut` is a compile error.

**`move` captures:**
- At closure creation time, each `move ident` capture transfers ownership of the named linear binding into the closure's environment. The outer binding is consumed at closure creation — using it after is a compile error.
- A closure with any `move` capture has type `linear fun(...) -> T`: it must be called exactly once (see RFC-0046).
- Linear bindings referenced in the closure body that are not listed with `move` are a type error — linear values cannot be clone-captured.

**Both:**
- A binding may not appear in both the capture list and the value-captured portion of the same closure's environment (no dual capture of the same name).
- Unlisted non-linear bindings continue to be clone-captured (RFC-0006 default).

### Read-only reference captures

This RFC covers only `&mut` captures. Read-only reference capture (`&ident`) is deferred; value capture already handles the immutable case adequately.

---

## Conflict with Region Syntax (RFC-0063)

RFC-0063 and RFC-0065 introduce region parameters on closures using the same bracket
position this RFC uses for capture lists:

```metel
// RFC-0050 — capture list
let inc = [&mut count]() -> () { count += 1; };

// RFC-0063/0065 — region parameter
Region::scoped([region]() -> { process(region) });
```

Both forms place `[…]` immediately before `(`. A closure that needs *both* — a
region-parameterised callback that also captures mutable outer state — has no defined
form under either RFC.

Content-based disambiguation partially rescues the single-bracket case:

- Items beginning with `&mut` or `move` are unambiguously capture specifiers.
- A bare identifier is unambiguously a region parameter.

This works for the two common solo cases. It fails for the combined case, and it creates
a latent parsing ambiguity if future capture specifiers are added that do not begin with a
keyword.

Three solutions are proposed below; the syntax resolved question is re-opened pending a
decision.

### Solution A — Sequential brackets

Assign a fixed order: region parameters always come first, capture list always comes
second. Each bracket retains its existing syntax unchanged.

```
closure_expr = region_params? capture_list? "(" params ")" "->" type block
region_params = "[" ident ("," ident)* "]"
capture_list  = "[" capture_item ("," capture_item)* "]"
capture_item  = "&mut" ident | "move" ident
```

The parser distinguishes the two brackets by content: if the first token after `[` is
`&mut` or `move`, the bracket is a capture list; if it is a bare identifier, it is a
region parameter list. Two consecutive brackets give one of each in order.

```metel
// region only
[region]() -> { ... }

// captures only
[&mut count]() -> { ... }

// both — region first, captures second
[region][&mut count]() -> { ... }
```

**Advantages:** both existing syntaxes are preserved exactly; the combined form is
unambiguous and systematic.

**Disadvantages:** `[region][&mut count]` is visually heavy and double-bracket syntax
is unusual; content-based disambiguation relies on the rule that region parameters are
always bare identifiers, which must be maintained by all future extensions to both RFCs.

### Solution B — Unified bracket

Merge both concerns into a single `[…]` list. Items are distinguished by form: bare
identifiers are region parameters; prefixed items are captures. Both may appear in the
same list.

```
bracket_list = "[" bracket_item ("," bracket_item)* "]"
bracket_item = ident              // region parameter
             | "&mut" ident       // mutable capture
             | "move" ident       // move capture
```

```metel
// region only
[region]() -> { ... }

// captures only
[&mut count]() -> { ... }

// both — order within the bracket is unconstrained
[region, &mut count]() -> { ... }
```

**Advantages:** one bracket, fewer tokens; the solo cases parse identically to today.

**Disadvantages:** the single bracket now carries two independent semantic roles; the
ordering of region parameters relative to capture items is unconstrained, which may make
reading closures harder; a future capture specifier that is also a bare identifier (e.g.
a by-name value capture `ident`) would reintroduce ambiguity.

### Solution C — Keyword-prefixed captures, brackets reserved for regions

Repurpose the `[…]` position exclusively for region parameters (consistent with RFC-0063)
and introduce a new keyword form for captures, placed after the region bracket and before
the parameter list.

```
closure_expr = region_params? ("capture" "(" capture_item ("," capture_item)* ")")?
               "(" params ")" "->" type block
capture_item = "&mut" ident | "move" ident
```

```metel
// region only
[region]() -> { ... }

// captures only — brackets gone; capture keyword used
capture(&mut count)() -> { ... }

// both
[region] capture(&mut count)() -> { ... }
```

**Advantages:** `[…]` is unambiguously region syntax everywhere in the language;
captures are visually distinct from region parameters; no content-based disambiguation
needed.

**Disadvantages:** breaks the capture-list syntax established by this RFC; the `capture`
keyword adds verbosity and a new reserved word; existing documentation and test code
using `[&mut x]` closures must be updated.

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

## Resolved Questions

1. **Lifetime of the mutable reference. ✓ Resolved** — In the interpreter, the outer binding's storage is heap-backed so there is no unsoundness. Under a future compiler, a closure holding `&mut` to a stack binding must not outlive that binding. Precise enforcement defers to the borrow checker. No interpreter-level restriction is imposed now.

2. **Interaction with concurrency. ✓ Resolved** — `*mut T` is not `Send` (RFC-0028, RFC-0003). A closure is `Send` only if all its captured values are `Send`. Any `[&mut x]` closure is therefore automatically non-`Send` — no new rule needed; falls out of the existing model.

3. **Multiple closures capturing the same binding. ✓ Resolved** — Two closures with `[&mut x]` both hold a mutable pointer to `x`. This is safe in the single-threaded interpreter (sequential calls; aliased mutation is not concurrent). Under the borrow checker, at most one live mutable reference at a time will be enforced. Document now; restrict later.

4. **Syntax. ✗ Re-opened** — `[&mut x]` was confirmed jointly with RFC-0046. RFC-0063
   subsequently introduced `[region]` in the same syntactic position for region parameters,
   creating a conflict for closures that need both. Solutions A, B, and C above are the
   live candidates; a decision is required before this RFC can be implemented. The choice
   also determines whether the capture-list grammar in this RFC must be revised, and
   whether existing interpreter code using `[&mut x]` closures needs updating.

---

## Timing Recommendation

This RFC should not be implemented before at least a prototype design exists for linear types (see the Memory and Reference Model RFC). The capture list is semantically a borrow, and the two features need a compatible story for lifetime checking before the interpreter implementation can be considered sound under a future compiler. Implementing it in the interpreter as syntactic sugar over the existing `*mut` pointer mechanism is safe for the short term, but the semantics must be locked down before the compiler milestone.

**Prerequisite:** RFC-0043 (Regular Pointers and Mutable Pointers) — already implemented.

**Suggested order:** RFC-0028 accepted → RFC-0046 accepted → this RFC implemented in interpreter → compiler picks up native reference semantics.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0041: Lambda Syntax for Anonymous Functions
- RFC-0043: Regular Pointers and Mutable Pointers
- Closure capture tests: `tests/evaluator/sources/closures/72_closure_internal_ptr_no_outer_effect.mtl`, `73_closure_direct_assign_no_outer_effect.mtl`, `74_closure_external_ptr_affects_outer.mtl`
- RFC-0046: Linear Closure Capture — `move` specifier in capture lists; `linear fun` type; resolved jointly with this RFC
- RFC-0063: Region Handles — introduces `[region]` in the same bracket position; source of the syntax conflict analysed above
- RFC-0065: Region Ergonomics — uses `[region]() -> {}` closure form throughout; affected by whichever solution is chosen
- C++ lambda capture lists — prior art for syntax and semantics

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
