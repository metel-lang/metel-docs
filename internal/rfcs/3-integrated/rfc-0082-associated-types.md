---
id: rfc-0082
title: "Associated Types"
date: '2026-07-01'
status: integrated
updated: '2026-07-10'
impl_tracking: 'https://app.clickup.com/t/86cam5fmd'
impl_status: not-started
---

> **Status — accepted.** Depends on RFC-0060 (Aspect Impl Coherence). Formally
> specifies associated types: `type X;` declarations in aspect blocks and `type X = Y;`
> definitions in impl blocks. This syntax is assumed pre-existing across the accepted
> allocator RFC cluster (RFC-0063, RFC-0074, RFC-0080) without formal specification.
> §7 amends RFC-0069's now-superseded `type SubRegion<R> impl ...` notation — kept as
> historical record; see §7's own note.
>
> **Corrected 2026-07-10, while integrating into the spec.** The motivating example (§1,
> §6) used the pre-split `Region` aspect name and `@[r] expr` bracket syntax — updated to
> RFC-0063's ratified `Alloc` aspect and `@a expr` syntax. RFC-0069 was retracted as part
> of the 2026-07-05 split (its `SubRegion` concept no longer exists — RFC-0073's own
> status note confirms "SubRegion interaction removed"); §7 is kept for historical record
> only, not as still-applicable content.

> **Status — integrated (2026-07-10).** Integrated into public/reference/spec/declarations.md: associated types (type X;/type X = Y;, projection, equality-constrained bounds, object safety). RFC's stale Region/@[r] naming fixed and its RFC-0069 amendment (SubRegion, retracted) marked historical-only, not integrated.
>
> **Amended 2026-07-10, later the same day.** §10 Open Question 1 (disambiguation for
> identically-named associated types) resolved rather than left deferred to a
> nonexistent "type inference RFC" — type inference is already specified
> (`public/reference/spec/types.md` §Type Inference) and implemented (RFC-0031),
> so there was no future RFC for this to actually wait on. New §3a: `<T as
> Aspect>::AssocType`, required only when ambiguous, always legal otherwise.

## Summary

Aspects may declare **associated types** — type-level output parameters that each
implementing type must specify. An associated type is declared with `type Name;` in an
aspect block and defined with `type Name = ConcreteType;` in an impl block. Associated
types allow aspect method signatures to reference types that vary per implementation
without making them generic type parameters on the aspect itself.

The primary motivating examples already in accepted RFCs:

```metel
aspect Alloc {
    type AllocationError;
}

impl Alloc for BumpAlloc {
    type AllocationError = !;
}

aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;
}

impl<T, brand 'b> Deref for Rc<T, 'b> {
    type Target = T;
    fun deref(self: &Rc<T, 'b>) -> &T { ... }
}
```

This RFC is the formal specification that makes those definitions normative.

---

## 1. Declaration in Aspect Blocks

An associated type is declared with the `type` keyword inside an aspect definition:

```metel
aspect Aspect {
    type Name;
}
```

The name becomes part of the aspect's interface. Any impl of `Aspect` must define `Name`.

### 1.1 Bounds on the declaration

A bound may appear on the declaration:

```metel
aspect Collection {
    type Item: Display;
}
```

The bound constrains every impl: a type implementing `Collection` must provide a
`type Item = ConcreteItem` where `ConcreteItem: Display`. The compiler enforces this
at the impl site. When no bound is declared, the associated type is unconstrained;
usage sites may add bounds independently via where clauses (§4).

### 1.2 Use in method signatures

An associated type may appear anywhere a type is expected in the aspect's method
signatures. Inside an aspect block, the bare name `Target` is sugar for `Self::Target`:

```metel
aspect Iterator {
    type Item;
    fun next(self: &mut Self) -> Perhaps<Item>;   // Item = Self::Item
}

aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;            // Target = Self::Target
}
```

---

## 2. Definition in Impl Blocks

An impl block must define all associated types declared by the aspect:

```metel
impl Iterator for Counter {
    type Item = i64;
    fun next(self: &mut Counter) -> Perhaps<i64> { ... }
}
```

`type Name = ConcreteType;` binds the associated type to a concrete type for this impl.
The `ConcreteType` must satisfy any bound declared on the association (§1.1). A missing
associated type definition is a compile error.

Within the impl body, the bare name `Item` resolves to `Self::Item` — the concrete type
defined by this impl.

---

## 3. Projection — `T::AssocType`

In a generic context where `T: Aspect`, the associated type is referenced as `T::AssocType`:

```metel
fun deref_display<T: Deref>(x: &T) where T::Target: Display {
    println(x.deref());
}
```

`T::Target` is a **projection** — the compiler resolves it to the concrete associated
type for the specific `T` at each instantiation. Projections may appear in:

- Function signatures: `fun f<T: Deref>(x: &T) -> &T::Target`
- Where clauses: `where T::Target: Display`
- Type positions in bodies: `let y: T::Target = x.deref();`

`T::AssocType` is only valid when `T: Aspect` is in scope. Writing `T::Target` without
`T: Deref` in scope is a compile error.

### 3a. Disambiguation — `<T as Aspect>::AssocType`

When `T` is bound to two or more aspects that each declare an associated type of the
same name, the bare projection `T::Target` is ambiguous — the compiler cannot tell
which aspect's `Target` is meant:

```metel
aspect Deref { type Target; fun deref(self: &Self) -> &Target; }
aspect Convert { type Target; fun convert(self: &Self) -> Target; }

fun f<T: Deref + Convert>(x: &T) -> T::Target { ... }
// error: T::Target is ambiguous — both Deref and Convert declare `Target`
```

The fully qualified form `<T as Aspect>::AssocType` names which aspect's associated
type is meant:

```metel
fun f<T: Deref + Convert>(x: &T) -> <T as Deref>::Target { ... }
```

**Required only when ambiguous; always legal otherwise.** `T::AssocType` remains valid
and preferred whenever exactly one bound aspect declares that name — the fully
qualified form is available at every projection site, not just ambiguous ones, but
writing it where the bare form would already resolve unambiguously is unnecessary
verbosity, not an error. This matches every other elision mechanism in the language
(allocator elision, lifetime-anchor elision): the explicit form is always accepted,
the terse form is used whenever the compiler can determine the unique correct answer
on its own, and ambiguity — never silent choice — is what forces the explicit spelling.

**No new resolution machinery, and no dependency on a future type-inference RFC.**
Resolving `<T as Aspect>::AssocType` is an ordinary lookup at the same
associated-type-projection step §3 already specifies — the aspect name simply selects
which of `T`'s bound aspects to project from, before that step runs, rather than
requiring the step itself to disambiguate. It does not touch unification, generalization,
or any other part of the inference algorithm (Hindley-Milner with let-polymorphism,
already implemented per RFC-0031 and `public/reference/spec/types.md` §Type Inference).
The original deferral to "the type inference RFC" assumed a future foundational RFC
would need to define this; no such RFC exists or is planned — type inference is already
specified and implemented, and this disambiguation rule doesn't touch any part of it.

---

## 4. Equality Constraints in Bounds

`Aspect<AssocType = ConcreteType>` in a bound asserts that `T` implements `Aspect` and
that its associated type equals `ConcreteType`:

```metel
fun deref_to_node<T: Deref<Target = Node>>(x: &T) -> &Node {
    x.deref()
}

impl<T: Deref<Target = Node>> PrintNode for T { ... }
```

The equality constraint is the mechanism for pinning an associated type to a known type
at a use site. Without it, `T: Deref` leaves `T::Target` abstract; with
`T: Deref<Target = Node>`, the compiler knows `T::Target = Node` and can unify them
with `Node` at every use.

Multiple constraints may be combined:

```metel
fun f<T: Deref<Target = Node> + Iterator<Item = i64>>(x: &T) { ... }
```

---

## 5. Associated Types vs Generic Type Parameters on the Aspect

The key distinction: an associated type is uniquely determined by the implementing type.
A type `T` has exactly one `Deref::Target` — the compiler can infer it from `T`. A
generic type parameter on the aspect would allow multiple impls per type:

```metel
// Wrong model — generic parameter allows both:
impl Deref<Node> for SmartPtr { ... }
impl Deref<i64>  for SmartPtr { ... }

// Right model — associated type: one Target per implementing type
impl Deref for SmartPtr {
    type Target = Node;   // unique
}
```

Use an associated type when the output type is a function of the implementing type.
Use a type parameter on the aspect when a type may implement the aspect for multiple
type arguments (e.g., `From<T>` in other languages — a type may be `From<i64>` and
`From<String>` simultaneously).

---

## 6. Object Safety

RFC-0008 §3 specifies that an aspect with associated types is object-safe only if no
method signature references the associated type directly. This RFC is the normative
basis for that rule.

`Deref` is **not** object-safe: `deref` returns `&Target`, which varies per impl.
A vtable entry for `deref` cannot encode a type that differs per implementor — the
vtable is fixed at compile time.

`Alloc` is object-safe with respect to associated types: its allocation methods do
not surface `AllocationError` in their vtable signatures. The return type of the
`@a expr` allocation expression is handled by the allocation expression rule
(RFC-0063 §3), not by vtable dispatch.

---

## 7. Amendment to RFC-0069 — SubRegion (historical — RFC-0069 retracted, not integrated)

**This section no longer describes anything in the ratified design.** RFC-0069 was
retracted as part of the 2026-07-05 allocator/lifetime split; `SubRegion` does not exist
in RFC-0063/0065/0066/0067/0068/0073/0077, and RFC-0073's own status note confirms
"SubRegion interaction removed." Kept below as historical record of what this RFC once
amended, not as spec content — nothing here is integrated into
`public/reference/spec/`.

RFC-0069 §1 defines `SubRegion<R>` with a non-standard notation:

```metel
// RFC-0069 §1 (informal, superseded by this RFC)
type SubRegion<R: Region> impl Region, Outlives<R> { … }
```

This notation has no meaning in Metel's type system. `SubRegion<R>` is a concrete
stdlib struct, not a type alias. The normative definition is:

```metel
struct SubRegion<R: Region> {
    // compiler-managed internal state
}

impl<R: Region> Region for SubRegion<R> {
    type AllocationError = !;
}

impl<R: Region> Outlives<R> for SubRegion<R> {}
```

`SubRegion<R>` implements `Region` (so it participates in the bracket channel) and
`Outlives<R>` (so the `R: Outlives<SubRegion<R>>` bound holds automatically). It is
compiler-assigned — the programmer does not construct it directly — but may be named in
type annotations and bounds as established by RFC-0069 §6 UQ1 (resolved).

RFC-0069's conceptual pseudo-code is amended to read as above. All other content of
RFC-0069 is unchanged.

---

## 8. Standalone Type Aliases

Standalone type aliases — `type Alias = ConcreteType;` at module level — are a distinct
feature. They have no aspect, no impl, and no associated type mechanism. They are
deferred to a future RFC.

---

## 9. Alternatives Considered

### Default associated types

Allowing `type Name = DefaultType;` in an aspect definition as an overridable default
is deferred. Interaction with the closed-world coherence model (RFC-0060) is non-trivial
— a default would create a compiler-generated impl that could conflict with user impls
under the overlap rules. No current use case requires defaults.

---

## 10. Unresolved Questions

1. ~~Disambiguation for identically-named associated types.~~ **Resolved 2026-07-10,
   §3a:** `<T as Aspect>::AssocType`, required only when ambiguous, always legal
   otherwise. The "type inference RFC" this was deferred to was never a real
   dependency — type inference (RFC-0031) is already implemented, and this
   disambiguation is an ordinary lookup at the projection step this RFC already
   specifies, not something inference itself needs to define.

2. **Higher-kinded associated types.** Whether an associated type may itself be generic
   (`type Container<T>;`) is deferred. No current use case requires this.

3. **Standalone type aliases.** `type Alias = ConcreteType;` at module level is deferred
   (§8).

---

## References

- RFC-0060 (Aspect Impl Coherence) — orphan rule and coherence rules apply to impl
  blocks that define associated types.
- RFC-0063 (Allocator Handles) — primary consumer; `type AllocationError` in the
  `Alloc` aspect; `AllocationError = !` for infallible impls.
- RFC-0069 (Sub-Region Typing, refused) — `SubRegion<R>` definition §7 amended;
  retracted 2026-07-05, §7 kept as historical record only.
- RFC-0074 (Shared Pointers) — `Deref` impl for `Rc<T>` and `Arc<T>`; associated type
  `Target = T`.
- RFC-0080 (Stdlib Aspects) — `Deref` aspect definition; associated type `Target` in
  `deref` method signature.
- RFC-0008 (Aspect Objects) — object safety rule for aspects whose method signatures
  reference associated types.
