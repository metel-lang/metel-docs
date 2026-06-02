---
id: rfc-0043
title: "Regular Pointers and Mutable Pointers"
date: '2026-06-02'
status: implemented
spec_status: done
---

## Summary

Define Metel's regular pointer model for non-linear values:

- read-only pointers: `*T`
- writable pointers: `*mut T`
- address-of operators: `&x` and `&mut x`
- explicit dereference: `*p`

This RFC is intentionally scoped to regular pointers only. It does not define:

- linear-compatible heap indirection
- unique pointers
- read references for linear values
- borrow-checked or lifetime-tracked references

Those remain in RFC-0028.

The goal is to settle the pointer surface needed by closure sharing without blocking the later linear-type design or prejudging the eventual concurrency model.

---

## Motivation

Metel needs a way to express explicit aliasing for non-linear values.

The immediate uses are:

- shared mutable state between closures
- self-referential and recursive non-linear data structures
- APIs that need indirect mutation without consume-and-return

At the same time, the pointer model introduced now must not conflict with:

- RFC-0006's closure capture semantics
- RFC-0028's unified memory and reference model for linear types, read references, and unique pointers
- future concurrency or lifetime proposals that may restrict pointer escape or transfer

The central compatibility rule is therefore:

**regular pointers are for non-linear aliasing only.**

If Metel later adopts linear types, regular pointers must not become a loophole that defeats exactly-once ownership. Heap indirection for linear values needs its own distinct mechanism, owned by RFC-0028 rather than folded into `*T` and `*mut T`.

---

## Scope

This RFC settles the following decisions:

1. Pointer type syntax: `*T` and `*mut T`
2. Address-of syntax: `&x` and `&mut x`
3. Dereference syntax: `*p` for read, `*p = v` for write-through
4. Mutability rules and coercions
5. Closure rule: shared closure state is explicit and pointer-based
6. Linearity rule: regular pointers cannot target linear values
7. Compatibility constraint: future concurrency or lifetime rules may impose additional restrictions on pointer escape or transfer

This RFC does not settle unique pointers or linear read references. Those remain open in RFC-0028.

---

## Proposal

### 1. Pointer Types

Metel has two regular pointer types:

```metel
*T
*mut T
```

`*T` is a readable pointer to `T`.

`*mut T` is a readable and writable pointer to `T`.

Both are first-class values:

- they can be stored in bindings
- they can be passed to functions
- they can appear in structs and enums
- they can be cloned, producing another alias to the same pointed-to location

They are distinct from `T`. There is no implicit dereference.

### 2. Address-Of

Address-of is explicit:

```metel
&x
&mut x
```

Rules:

| Expression | Result type | Rule |
|---|---|---|
| `&x` | `*T` | valid for addressable non-linear values |
| `&mut x` | `*mut T` | valid only for addressable mutable non-linear values |

The mutability of the pointer is chosen at the address-of site, not inferred from the binding.

```metel
let x = 1;
let p = &x;        // *Int
// let q = &mut x; // error

let mut y = 2;
let r = &y;        // *Int
let s = &mut y;    // *mut Int
```

This keeps mutability explicit and keeps `&x` stable in meaning.

### 3. Dereference

Dereference is explicit:

```metel
let value = *p;
*p = 42;
```

Rules:

- `*p` reads through either `*T` or `*mut T`
- `*p = v` is valid only when `p: *mut T`
- dereferencing a non-pointer is a type error

### 4. Mutability Coercion

`*mut T` coerces to `*T` implicitly.

`*T` never coerces to `*mut T`.

This is the only implicit pointer coercion:

```metel
fun read(p: *Int) -> Int { *p }

let mut x = 1;
let p: *mut Int = &mut x;
let n = read(p);   // ok: *mut Int -> *Int
```

### 5. Addressability

Only addressable lvalues may appear after `&` or `&mut`.

Initially, the language guarantees addressability for:

- named bindings
- fields of addressable values
- indexed elements of addressable arrays

Non-addressable expressions are rejected:

```metel
// &(x + 1)      // error
// &make_point() // error
```

This keeps pointer identity tied to stable storage locations rather than temporary expression results.

### 6. Auto-Deref at Field Access, Method Calls, and Function Pointer Calls

Metel auto-dereferences one pointer layer for field access, method calls, and function pointer calls.

```metel
let p: *Point = &point;
let x = p.x;
let d = p.distance(other);
```

```metel
let f = () -> { return 42; };
let ptr: *() -> Int = &f;
let result = ptr();   // auto-deref: equivalent to (*ptr)()
```

This is an acceptable tradeoff between explicitness and ergonomics. Regular pointers are already explicit at their creation sites (`&x`, `&mut x`) and in type position (`*T`, `*mut T`). Requiring `(*p).field`, `(*p).method(...)`, and `(*fp)()` everywhere adds repetition without improving the aliasing story.

This yields a simple rule:

- field access may auto-dereference one pointer layer to access fields on the pointee type
- method dispatch may auto-dereference one pointer layer to find methods on the pointee type
- a call expression whose callee resolves to `*(() -> T)` or `*mut (() -> T)` auto-dereferences one pointer layer before dispatching the call

Auto-deref applies exclusively to these three syntactic positions. Reads, writes, and argument passing still require the ordinary pointer rules.

### 7. No Pointer Arithmetic

Pointer arithmetic is out of scope and invalid.

```metel
// p + 1   // type error
```

Metel pointers are managed references to language values, not raw byte addresses.

### 8. Nullability

There is no null pointer literal.

Optional pointers are modeled with `Perhaps<*T>` or `Perhaps<*mut T>`.

```metel
let next: Perhaps<*Node> = nope;
```

This keeps absence explicit and consistent with the rest of the type system.

### 9. Pointer Semantics

Regular pointers are non-owning aliases to runtime-managed storage.

The spec-level guarantee is:

- taking the address of an addressable value yields a pointer to a stable shared location
- cloning a pointer yields another alias to the same location
- writes through one `*mut T` pointer are observable through all aliases to that location

The current interpreter may implement this using reference-counted cells, but the RFC does not commit the language to a specific runtime representation. The contract is shared-location semantics, not `Rc<RefCell<T>>` as a public language concept.

### 10. Future Concurrency and Lifetime Compatibility

This RFC does not decide whether regular pointers are governed by `Send`, limited lifetimes, non-escaping rules, or another future transfer discipline.

It only fixes the compatibility boundary that future work must respect:

- regular pointers introduce aliasing to non-linear storage
- any future concurrency or lifetime model must account for that aliasing explicitly
- the eventual rule may restrict pointer escape, pointer transfer, or concurrent use, but this RFC does not choose which rule wins

### 11. Linearity Compatibility

Regular pointers cannot target linear values.

Both forms are type errors:

```metel
// &linear_value
// &mut linear_value
```

This is the key future-compatibility boundary with RFC-0028.

If linear values become part of the language, they require aliasing rules that preserve exactly-once usage. Regular cloneable pointers cannot satisfy that constraint. Heap indirection for linear values must therefore be expressed with a distinct linear-compatible mechanism such as unique pointers, not by relaxing `*T` or `*mut T`.

### 12. Closure Compatibility

Closures capture by value. Shared closure state is explicit:

```metel
let mut counter = 0;
let p: *mut Int = &mut counter;

let inc = () -> () { *p += 1; };
let get = () -> Int { *p };
```

This aligns RFC-0006 with the pointer model:

- default closure capture remains clone-by-value
- aliasing across closures happens only when the programmer explicitly introduces a pointer

This prevents implicit shared-mutation semantics from leaking into closure capture.

---

## Recursive Types

Regular pointers allow recursive non-linear data structures:

```metel
struct Node {
    value: Int,
    next: Perhaps<*Node>,
}
```

This is valid because `*Node` is an indirection boundary for a non-linear type.

Recursive linear data structures are explicitly out of scope for this RFC and remain in RFC-0028's space.

---

## Equality

Pointer equality is identity equality.

```metel
p == q
```

is true when `p` and `q` point to the same location, not when `*p == *q`.

Value equality remains explicit:

```metel
*p == *q
```

This keeps pointer identity and pointee equality distinct.

---

## Interaction with Future Concurrency Work

Regular pointers create explicit aliasing to non-linear storage. Any future concurrency or lifetime RFC must define how that aliasing interacts with escaping scope and concurrent execution.

This RFC intentionally does not commit Metel to `Send` as the permanent boundary. If the language adopts a limited-lifetime model or another transfer discipline instead, RFC-0043 should remain compatible because it exposes aliasing explicitly rather than hiding it.

---

## Interaction with RFC-0006

RFC-0006 currently depends on explicit pointers for shared mutable closure state. This RFC provides the concrete pointer contract that RFC-0006 needs:

- explicit `&mut`
- cloneable aliasing pointers
- pointer-based explicit sharing rather than implicit reference capture

RFC-0006 should be updated, after this RFC is accepted, to reference RFC-0043 instead of RFC-0001 for regular pointer semantics.

---

## Interaction with RFC-0028

RFC-0028 currently combines three concerns:

- linear types
- read references for linear values
- regular and unique pointers

After this RFC is accepted, RFC-0028 should be revised so that:

1. regular pointer syntax and semantics come from RFC-0043
2. RFC-0028 keeps ownership of linearity, `@T`, and unique linear-compatible indirection
3. any duplicated regular-pointer rules are either removed or reduced to a compatibility summary

This RFC does not supersede RFC-0028. It extracts and settles the regular-pointer slice that other RFCs need now.

---

## Resolved Decisions

### D1 - Pointer types are allowed in public APIs

Pointer types may appear in public signatures immediately. This RFC treats them as part of the language surface, not as an internal-only escape hatch.

### D2 - Field access, method dispatch, and function pointer calls auto-deref

Field access, method dispatch, and call expressions whose callee is a function pointer all auto-deref one regular-pointer layer. This is the accepted ergonomic rule for ordinary pointer use.

### D3 - Indexing and argument passing remain explicit

Array or slice indexing through a pointer, passing pointers as arguments, and reading pointer values all still require explicit dereference. Auto-deref is scoped to field access, method dispatch, and function pointer calls — it does not become a general implicit-dereference rule.

---

## Decision

**Outcome:** Accepted
**Target:** *(pending milestone assignment)*

This RFC is the source of truth for Metel's regular pointer model. RFC-0006 and RFC-0028 should reference it for regular-pointer semantics, and future concurrency work must define the transfer or escape rules that apply to these pointers.
