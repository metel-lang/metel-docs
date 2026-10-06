---
id: rfc-0176
title: "Hash Aspect and Structural Hashing"
date: '2026-10-06'
status: draft
---

## Summary

Define a stable Hash aspect for hashable values, primitive implementations, and structural hashing of composite types without assuming unresolved equality or ordering designs.

---

## Motivation

Metel has no public hashing aspect. The interpreter uses Rust hash maps internally,
but user-defined values cannot declare that they have a stable hash and no generic
library API can express a hashable key. Several existing documents mention `Hash`
or structural hash derivation, but none defines the aspect, its contract, the
primitive implementations, or the treatment of composite values.

Hashing must remain independent of ordering. A type may be hashable without being
orderable, and the design must not silently choose the unresolved equality model or
the not-yet-designed `Ord` API.

## Goals

- Define one public `Hash` aspect that generic code can bound.
- Specify the equality-consistency contract required of an implementation.
- Define deterministic structural hashing for records, structs, enums, arrays, and
  tuples when their components satisfy `Hash`.
- Keep hashes independent of object addresses, process-randomized seeds, and field
  declaration order where the value's record semantics are label-based.
- Leave room for a future map/set API and for compiler-registered derives.

## Non-goals

- A cryptographic hash, password hashing, or collision resistance guarantee.
- A `HashMap`/`HashSet` API or a hash operator.
- Defining `Eq`, `PartialEq`, `Ord`, or `==` desugaring. Those remain governed by
  RFC-0168, RFC-0062, and RFC-0011 respectively.
- Making every value hashable automatically. Functions, references, views, and
  other identity-bearing values need an explicit policy before they can implement
  `Hash`.

## Design

### The aspect

The standard library declares:

```metel
public aspect Hash {
    fun hash(&self) -> u64;
}
```

The result is a hash value, not an identity or an ordering. Implementations may
collide. Callers must use the full `u64`; truncating it or interpreting it as a
stable numeric ordering is outside the contract.

### Contract

An implementation must satisfy the following law:

> If two values compare equal under the language's chosen equality relation, their
> `Hash::hash` results are equal.

The converse is not required: distinct values may collide. Hashing must not mutate
the value, observe its address, or depend on the order in which a program happened
to construct it.

The exact name of the equality relation used by this law is intentionally left to
the equality RFC. Once that RFC settles `PartialEq`/`Eq`, the specification should
state whether `Hash` requires the weaker operation or the stronger reflexive
marker. A type that implements `Hash` without satisfying the settled law is an
invalid implementation, not a runtime error.

### Primitive values

`std::core` provides `Hash` implementations for the primitive values whose equality
semantics are settled and suitable for keys: booleans, characters, integers, and
strings. Each implementation is deterministic and uses the value's language-level
representation, not a host pointer.

Floating-point hashing is deferred until the equality RFC settles NaN and signed
zero semantics. In particular, a hash for floating-point values must not be added
merely because Rust can hash the host representation; it must first satisfy the
language equality contract.

### Structural values

Structural hashing combines a type-domain marker with each component hash:

- arrays and tuples hash their elements in positional order;
- records hash their labels and field values in canonical label order, so source
  declaration order does not affect the result;
- nominal structs hash their nominal type identity followed by fields in the
  declaration's canonical field order;
- enums hash their nominal type identity, variant identity, and variant fields in
  declaration order.

Each composite implementation is conditional: a composite implements `Hash` only
when every component it hashes implements `Hash`. Empty composites still hash their
type-domain marker. The type-domain marker prevents values from unrelated nominal
types or structural shapes being required to share a hash namespace, while equality
consistency remains the governing requirement for values that can compare equal.

The exact mixing function is an implementation detail, provided it is deterministic
for the same language value and follows the contract above. The specification should
not promise a particular numeric hash across compiler versions unless a future
serialization or persistent-storage feature requires that guarantee.

### Derivation and registration

Compiler derivation may register the conditional implementations described above,
following the derive-registration mechanism. Derivation is not implicit merely
because a type's fields happen to be hashable; a type declaration or library policy
must request it. A hand-written implementation remains possible where a type needs a
custom canonical representation.

## Open questions

1. Should the method return `u64`, or an opaque hasher state/finalization type once
   map and set APIs exist?
2. Does `Hash` require `PartialEq`, `Eq`, or only the equality-consistency law as a
   semantic obligation?
3. Should floating-point hashing be supported, and if so, how are NaN payloads and
   `-0.0` normalized?
4. Are references and owning views ever hashable by referent value, or are they
   permanently excluded because identity hashing is not portable?
5. Should the type-domain marker be observable across compiler versions, or only be
   guaranteed within one compiled program?
6. Which derive syntax and coherence rules register the structural implementations?

## Relationship to existing work

- RFC-0061 records structural aspect bounds and explicitly defers `Hash` because no
  Hash RFC exists; this RFC supplies that missing design surface.
- RFC-0062 proposes `Ord` separately. This RFC does not make `Hash` imply `Ord` or
  `Eq` imply `Hash`.
- RFC-0168 defines the proposed equality model and deliberately leaves hashing and
  full ordering out of scope. This RFC depends on its settled equality contract only
  at integration time.
- RFC-0093 defines compiler derive registration. Its structural `Hash` entry must be
  reconciled with this RFC before either document is accepted.

## Decision

**Outcome:** *(pending)*


---

## Decision

**Outcome:** *(pending)*
