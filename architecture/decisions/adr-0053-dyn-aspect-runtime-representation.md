---
id: adr-0053
title: "dyn Aspect — Tree-Walk Runtime Representation"
date: '2026-09-06'
status: accepted
relates: adr-0013, adr-0045, adr-0025
implements: "metel-core#865, #866, #870, #864, #872"
---

## Context

RFC-0008 (`4-implemented`, v0.13.0) specifies `dyn Aspect` as a **fat pointer**: a
`(data, vtable)` pointer pair, the vtable a compiler-generated table of method function
pointers plus size/align/drop metadata for the `(concrete type, aspect)` pair, generated
from RFC-0060's coherence output.

That is the model for a compiled backend. The tree-walk interpreter has no vtable
machinery and no compilation step to generate one — and RFC-0008's own coverage frontmatter
marks section 2 `untestable` ("the fat-pointer / vtable representation … is a
compiler-internal strategy, not behaviour an `.mtl` fixture can observe"). So the interpreter
is free to pick a representation that yields the same observable behaviour by a different
mechanism. This ADR records that mechanism so a future reader does not go looking for a
vtable that was never built.

## Decision

### 1. A `dyn Aspect` value is a tagged wrapper, not a fat pointer

`metel-interpreter/src/evaluator/mod.rs`:

```rust
Value::DynAspect {
    data: Rc<RefCell<Value>>,   // the erased concrete value
    type_id: SymbolId,          // its concrete type, resolved once at coercion
    aspect_id: SymbolId,        // the principal (method-bearing) aspect it was coerced to
    aspect_name: String,        // ─┐ redundant with aspect_id, kept so value_to_type can
    type_args: Vec<Type>,       // ─┘ rebuild Type::Dyn without unwrapping `data`
}
```

- **`data`** is `Rc<RefCell<Value>>` — the same box `Array` / `Reference` / `MutReference`
  already use for a value that must be referenced heterogeneously or mutated through a
  `&var` receiver (RFC-0008 §2 names this box explicitly as the data-pointer stand-in).
  `&var dyn Aspect` mutable-receiver dispatch works because the `RefCell` is shared.
- **No generated vtable.** `type_id` *is* the dispatch key.

### 2. Dispatch reuses the existing type-keyed method registry — there is no separate vtable

A method call on any value already resolves through
`RuntimeRegistry::resolve_value_type_id(value)` → `get_regular_method(type_id, name)`
(adr-0013, adr-0025 — the unified `TypeDefinitionRegistry` / per-type runtime entry).
`resolve_value_type_id` returns `type_id` directly for a `Value::DynAspect`, so a call
`d.method()` on a `dyn Aspect` lands on exactly the same lookup as `concrete.method()`
would — "the vtable" is the registry the interpreter already keeps for every type. The
`aspect_id` is not consulted at call time; it exists for object-safety diagnostics and
for `value_to_type`.

### 3. Erasure is enforced by keeping the wrapper opaque, never by unwrapping `data`

The concrete type must not leak back out through a `dyn Aspect` value — its static type
stays `dyn Aspect` everywhere, including when a generic function body is re-constructed
from a runtime argument (metel-core#286). `value_to_type` therefore rebuilds
`Type::Dyn { aspect, type_args }` from the wrapper's own `aspect_name` / `type_args`
fields and **does not** inspect `data`. This is the same `name`-vs-`type_id` redundancy
`Value::Struct` / `Value::Enum` already carry.

### 4. Coercion is an explicit typed node, inserted by the checker

`TypedExpr::DynCoerce { inner, aspect_id, ty }` is planted by the type checker at every
expected-`dyn` position — argument, `let` with a `dyn` annotation, array / `List` element,
`return`, `break`. Evaluating it: run `inner`, `resolve_value_type_id` the result once,
wrap. A heterogeneous array / `List<dyn Aspect>` literal has one `DynCoerce` per element,
each element inferred against the declared `dyn` element type rather than against the
others (metel-core#864 / #872).

### 5. Object safety stays a frontend, compile-time check

`metel-frontend/src/typechecker/object_safety.rs` (RFC-0008 §3 / §3a / §3b): an aspect
with a `Self`-by-value receiver, a `Self` return, a generic method, or an associated type
in a method signature is rejected at the coercion site. `Drop::drop` (`&var self`,
RFC-0071) is object-safe. None of this touches the runtime — a value only reaches
`DynCoerce` if its aspect already passed.

## Consequences

- **The `dyn Aspect` fixture corpus is behavioural, not representational.**
  `evaluator/aspects/9*_dyn_aspect_*` assert method results, coercion in every position,
  and heterogeneous collections — never the pointer layout, which RFC-0008 §2 correctly
  says an `.mtl` cannot observe.
- **The vtable's size / align / drop-pointer metadata has no interpreter analogue.**
  `Drop` through a `dyn Aspect` (RFC-0008 §5) is blocked on destructor invocation
  (metel-core#261) regardless; when it lands it dispatches `drop` through the same
  registry path, not a vtable slot.
- **A compiled backend will need the real thing.** This ADR is explicitly the tree-walk
  shape; RFC-0008 §2 remains the spec for codegen, and `by_aspect` from `coherence.rs` is
  already the input it names.
- **`aspect_id` being unused at dispatch is deliberate**, not dead state — §9 UQ1 limits a
  `dyn` to one method-bearing aspect, so the principal aspect is fixed at coercion and
  the concrete `type_id` is a sufficient dispatch key on its own.
