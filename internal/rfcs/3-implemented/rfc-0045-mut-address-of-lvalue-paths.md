---
id: rfc-0045
title: "Mutable Address-Of for Lvalue Paths"
date: '2026-06-02'
---

## Summary

Extend `&mut` to accept arbitrary addressable lvalue paths — struct field access, tuple element access, array indexing, and chains thereof — with true mutable reference semantics: writes through the pointer propagate back to the original storage location.

This is the `&mut` counterpart to RFC-0043 §5 and METEL-111, which extended `&` (read-only address-of) to lvalue paths.

---

## Motivation

RFC-0043 §5 defines addressability for both `&` and `&mut`:

> The language guarantees addressability for:
> - named bindings
> - fields of addressable values
> - indexed elements of addressable arrays

METEL-111 implemented `&` for field, tuple, and array lvalue paths. `&mut` remains restricted to named bindings because the current storage model provides no stable shared location for sub-elements.

The restriction is artificial: users expect `&mut pair.counter` to produce a pointer through which mutations propagate back to `pair.counter`, exactly as `&mut x` does for a named binding. Forcing users to extract sub-elements into their own bindings first is boilerplate that defeats the ergonomic promise of lvalue paths.

```metel
// Today: workaround required
let mut c = pair.counter;
let p: *mut Counter = &mut c;
p.tick();
pair.counter = c;   // manual write-back

// After this RFC
let p: *mut Counter = &mut pair.counter;
p.tick();           // pair.counter updated automatically
```

---

## Blocker

The current `Value` representation uses:

- `Value::Struct { fields: HashMap<String, Value>, .. }` — field values stored directly
- `Value::Tuple(Vec<Value>)` — elements stored directly
- `Value::Array(Rc<RefCell<Vec<Value>>>)` — array stored in a shared cell, but elements inside `Vec<Value>` are plain values

There is no `Rc<RefCell<Value>>` per field or per element. Taking the address of a sub-element today copies the value into a fresh cell. The fresh cell has no connection to the original storage location, so writes through the resulting `*mut T` are silently discarded.

---

## Proposed Approaches

### Option A — Fat Pointer

Introduce a `Value::MutFieldPointer` variant that carries a path back to the source:

```
MutFieldPointer {
    root:    Rc<RefCell<Value>>,   // root binding cell
    path:    Vec<PathSegment>,     // field names, tuple indices, array indices
}
```

`PathSegment` is an enum:

```
enum PathSegment {
    Field(String),
    TupleIndex(usize),
    ArrayIndex(i64),
}
```

Reads (`*p`) walk the path and return a clone of the leaf value.
Writes (`*p = v`) walk the path and update the leaf value in place.

This does not require restructuring the `Value` enum for struct, tuple, or array storage. It is contained to the pointer representation and the dereference evaluation code.

**Trade-off:** complicates the `Value` enum and pointer write path; path-walking on every dereference adds indirection.

### Option B — Per-Field Rc Storage

Change struct fields to `HashMap<String, Rc<RefCell<Value>>>` and tuple elements to `Vec<Rc<RefCell<Value>>>`. `&mut struct.field` then returns the existing `Rc` directly, matching the identity semantics of `&mut x` for named bindings.

**Trade-off:** pervasive change to struct and tuple evaluation; every field read and write would need unwrapping.

### Option C — Per-Array-Element Rc

A narrower version of Option B targeting only arrays: change `Vec<Value>` inside `Value::Array` to `Vec<Rc<RefCell<Value>>>`. Struct and tuple fields retain plain-value storage and use Option A.

**Trade-off:** partial solution; structs and tuples still need Option A for `&mut`.

---

## Preferred Direction

Option A (fat pointer) is the least invasive change and can be implemented incrementally without touching struct or tuple storage. It is the recommended starting point.

The `MutFieldPointer` variant should be invisible at the language level — it is an implementation detail of how `*mut T` values are represented when created from a lvalue path. The language surface remains `*mut T` for all mutable pointers.

---

## Interactions

- **RFC-0043 §5** — this RFC completes the addressability guarantee for `&mut`.
- **RFC-0028** — if Metel eventually introduces linear types, fat-pointer write-back must be compatible with ownership tracking. The path representation may need to carry ownership metadata.
- **METEL-111** — the work item that implemented `&` for lvalue paths and deferred `&mut`.

---

## Resolved Decisions

**Implementation approach — Option A (fat pointer).** Introduce `Value::MutFieldPointer { root: Rc<RefCell<Value>>, path: Vec<PathSegment> }`. Struct and tuple storage remain flat. Option B (per-field `Rc<RefCell<Value>>`) was rejected: it would deepen interpreter reliance on `Rc`-backed storage that the technical debt audit already identifies as a compiler-readiness blocker, and all that restructuring would be discarded when a typed lvalue/place IR lands. The fat pointer's `(root, path)` shape is semantically adjacent to a `Place` projection and eases that future transition. `MutFieldPointer` is an interpreter implementation detail invisible at the language level.

---

## Decision

**Outcome:** Accepted — Option A (fat pointer)  
**Target:** *(unscheduled)*
