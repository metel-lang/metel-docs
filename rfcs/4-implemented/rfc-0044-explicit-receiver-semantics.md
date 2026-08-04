---
id: rfc-0044
title: "Explicit Receiver Semantics"
date: '2026-06-02'
status: implemented
spec_status: done
---

## Summary

Define explicit receiver semantics for methods and aspect methods.

Metel will support three receiver forms:

- `self` - value receiver
- `&self` - shared reference receiver
- `&var self` - exclusive mutable reference receiver

This RFC settles:

- what each receiver form means
- how method calls desugar
- how receiver forms interact with RFC-0043 regular pointers
- how `Iterable<T>::next` should be expressed in a future-compatible way

This RFC does not settle:

- linear receivers
- unique-pointer receivers
- borrow checking beyond receiver position
- general first-class reference types outside the receiver model

Those remain future work and must stay compatible with RFC-0028.

---

## Motivation

The current spec says:

- methods use `self`
- methods may declare `var self`
- `var self` mutates only a local receiver copy and does not update the caller's binding in place

That is workable for plain value-style APIs, but it breaks down for stateful protocols such as iterators. `Iterable<T>::next` is currently written as:

```metel
fun next(&var self) -> Perhaps<T>;
```

but a real iterator needs mutation of the underlying receiver state across calls. A local mutable copy is not enough.

The problem is broader than iterators:

- APIs need to distinguish read-only receiver access from stateful in-place mutation
- closure and pointer RFCs need a stable story for receiver aliasing
- future linear work needs a separate path for receiver ownership transfer

The language therefore needs explicit receiver modes instead of overloading `var self` to mean two different things.

---

## Proposal

### 1. Receiver Forms

Metel has three explicit receiver forms:

```metel
self
&self
&var self
```

Their meanings are:

| Receiver | Meaning |
|---|---|
| `self` | consume or copy the receiver value according to the ordinary value semantics of the type |
| `&self` | borrow shared read-only access to the receiver for the duration of the call |
| `&var self` | borrow exclusive mutable access to the receiver for the duration of the call |

`var self` is removed as a semantic form. Mutability of the local receiver binding is not the axis that matters; aliasing and update behavior are.

### 2. Value Receivers

`self` keeps value semantics.

For non-linear types, a value receiver operates on the passed value in the ordinary Metel way. If the language copies values on call, then method bodies observe and mutate that passed value only.

```metel
struct Counter {
    value: Int,
}

extend Counter {
    fun increment(self) -> Counter {
        self.value += 1;
        self
    }
}
```

Value receivers are the right form when:

- the method conceptually transforms and returns a new value
- the receiver is small and copy-oriented
- the API should not mutate caller-owned state in place

### 3. Shared Reference Receivers

`&self` provides read-only access to the original receiver.

```metel
extend Point {
    fun length(&self) -> Float {
        self.x * self.x + self.y * self.y
    }
}
```

A method with `&self`:

- may read receiver state
- may not write receiver fields through `self`
- does not consume the receiver

This is the canonical receiver form for observers, queries, formatting, hashing, comparisons, and other read-only behavior.

### 4. Mutable Reference Receivers

`&var self` provides exclusive mutable access to the original receiver.

```metel
extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}
```

A method with `&var self`:

- may mutate the underlying receiver state in place
- does not consume the receiver
- requires an addressable mutable receiver at the call site

This is the receiver form needed for iterators and other stateful protocols.

### 5. Method Call Desugaring

Receiver form determines call-site requirements.

| Method receiver | Call requirement | Desugared shape |
|---|---|---|
| `self` | ordinary method call on a value | `Type::method(receiver, ...)` |
| `&self` | receiver must be addressable or already pointer-backed | method receives a shared reference view |
| `&var self` | receiver must be mutably addressable or already mutable-pointer-backed | method receives an exclusive mutable reference view |

At the language level, dot-call syntax remains:

```metel
counter.increment();
let n = counter.current();
```

The receiver mode is determined by the method signature, not by syntax at the call site.

### 6. Interaction with RFC-0043 Regular Pointers

RFC-0043 introduces regular pointers and pointer auto-deref for field access and method calls. This RFC builds on that:

- calling an `&self` method through `p: *T` is allowed
- calling an `&var self` method through `p: *mut T` is allowed
- calling an `&var self` method through `p: *T` is a type error

Examples:

```metel
let p: *Counter = &counter;
let n = p.current();      // ok if current uses &self

let mp: *mut Counter = &var counter;
mp.increment();           // ok if increment uses &var self
```

This keeps the pointer RFC and receiver RFC aligned:

- pointers handle aliasable storage
- receiver modes express what kind of access a method requires

### 7. `Iterable<T>`

`Iterable<T>` should use an explicit mutable reference receiver:

```metel
aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}
```

This is the correct future-compatible iterator contract:

- the iterator mutates its own internal state across calls
- the caller keeps the same iterator value
- no copy-and-return dance is required

This replaces the current `var self` form for stateful iteration.

### 8. Aspect Methods

Aspect methods use the same receiver forms as ordinary methods.

```metel
aspect Display {
    fun to_string(&self) -> String;
}

aspect Iterable<T> {
    fun next(&var self) -> Perhaps<T>;
}
```

There is no separate receiver model for aspects.

### 9. Addressability Rules

Calls requiring `&self` or `&var self` need an addressable receiver source unless the receiver is already a pointer value with compatible mutability.

Allowed examples:

```metel
var counter = Counter { value = 0 };
counter.increment();      // &var self

let p: *Counter = &counter;
p.current();              // &self
```

Disallowed examples:

```metel
// make_counter().increment();   // error if increment requires &var self
// (&counter).increment();       // error if increment requires &var self through read-only pointer
```

This keeps exclusive mutation tied to stable mutable storage.

### 10. Compatibility with Future Linear Work

This RFC is intentionally limited to ordinary receivers over non-linear values and future-compatible reference views in receiver position.

It does not define:

- `&self` or `&var self` on linear receivers
- how linear values borrow through method receivers
- whether linear methods need separate receiver syntax

Those questions remain with RFC-0028 and related future work. This RFC only requires that any future linear receiver model not silently reinterpret the three receiver forms defined here for ordinary non-linear types.

---

## Migration

This RFC implies the following rewrites:

| Old form | New form |
|---|---|
| `fun f(var self) { ... }` used only for local mutation | either `fun f(self) -> Self` or `fun f(&var self)`, depending on intent |
| `fun next(var self) -> Perhaps<T>` | `fun next(&var self) -> Perhaps<T>` |
| read-only methods using `self` only for observation | `fun f(&self) -> R` |

The important migration decision is semantic, not mechanical: existing `var self` methods must be classified as either:

- value-transforming methods
- in-place mutating methods

They are not the same thing and should no longer share syntax.

---

## Alternatives Considered

### A. Keep `var self` and reinterpret it as in-place mutation

Rejected. That would silently change the meaning of existing code and keep the receiver model ambiguous. The language needs separate syntax for value receivers and reference receivers.

### B. Keep all methods value-based and thread state explicitly

Example:

```metel
fun next(self) -> (Perhaps<T>, Self)
```

Rejected for mainstream APIs such as iterators. It is verbose, infects every caller, and makes method-based protocols harder to use than necessary.

### C. Require pointers in user code for all stateful methods

Example:

```metel
let p: *mut Counter = &var counter;
p.increment();
```

Rejected. Pointer semantics should support explicit aliasing, not replace direct mutable receiver syntax for ordinary in-place methods.

---

## Resolved Decisions

### D1 - `&self` and `&var self` are introduced only in receiver position

This RFC introduces reference receivers without introducing general reference types across the rest of the language. That narrower surface is enough to fix method and iterator semantics now.

### D2 - Linear receiver interaction is explicitly out of scope here

Future linear or unique receiver forms are deferred to RFC-0028 and later follow-up work. This RFC settles ordinary non-linear receiver semantics only.

### D3 - Receiver-style guidance belongs in lints, not the core semantics

Methods that take `self` by value on large non-linear structs may justify a lint or style recommendation, but that is not a language-rule question and is not part of this RFC's semantic contract.

---

## Decision

**Outcome:** Accepted
**Target:** *(pending milestone assignment)*

This RFC is the source of truth for ordinary receiver semantics. The spec and related RFCs should follow it for method receiver rules, `Iterable<T>::next`, closure-related receiver mutation, and the method-dispatch interaction with RFC-0043 pointers.
