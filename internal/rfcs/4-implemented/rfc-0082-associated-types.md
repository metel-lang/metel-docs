---
id: rfc-0082
title: "Associated Types"
date: '2026-07-01'
status: implemented
updated: '2026-07-13'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/242'
impl_status: implemented
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
> (`public/reference/spec/types.md` §Type Inference) and implemented (RFC-0031), so
> there was no future RFC for this to actually wait on. First pass proposed `<T as
> Aspect>::AssocType`, borrowed from Rust without checking it against Metel's own
> grammar (`as` already has two other uses — import renaming, cast).
>
> **Corrected 2026-07-10, still the same day.** No new syntax needed at all: the bare
> ambiguous projection stays a hard error (matching the existing method-name-collision
> precedent, `T0013`), and §4's existing equality constraint with a fresh type
> parameter already covers every real case. See §3a for the full reasoning.
>
> **Considered and rejected, same day: `<T:Aspect>::AssocType`** (colon instead of
> `as`) as a second candidate spelling — it collides with `<T: Aspect>`'s one existing
> meaning everywhere in Metel (declaring a fresh generic parameter, `grammar.md:44`),
> a stronger clash than `as`'s two prior uses. Neither spelling is adopted; §3a records
> why, so neither gets re-proposed without this reasoning attached.

> **Status — implemented (2026-07-13).** Real projection resolution, equality constraints, impl-completeness, and §1.2 bare-name sugar all enforced; issue #242 (object safety, §6, remains blocked on RFC-0008)

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

extend BumpAlloc: Alloc {
    type AllocationError = !;
}

aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;
}

extend<T, brand 'b> Rc<T, 'b>: Deref {
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
    fun next(self: &var Self) -> Perhaps<Item>;   // Item = Self::Item
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
extend Counter: Iterator {
    type Item = i64;
    fun next(self: &var Counter) -> Perhaps<i64> { ... }
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

### 3a. Disambiguation — no new syntax; use §4's equality constraint with a fresh variable

When `T` is bound to two or more aspects that each declare an associated type of the
same name, the bare projection `T::Target` is ambiguous — the compiler cannot tell
which aspect's `Target` is meant:

```metel
aspect Deref { type Target; fun deref(self: &Self) -> &Target; }
aspect Convert { type Target; fun convert(self: &Self) -> Target; }

fun f<T: Deref + Convert>(x: &T) -> T::Target { ... }
// error: T::Target is ambiguous — both Deref and Convert declare `Target`
```

**This RFC's first pass (2026-07-10, since corrected) proposed a new bracketed
qualifier, `<T as Aspect>::AssocType`, borrowed directly from Rust's UFCS syntax
without checking it against Metel's own grammar first.** It doesn't actually work as
proposed: `as` is already a reserved keyword with two existing uses (import renaming,
`ImportItem → IDENTIFIER ("as" IDENTIFIER)?`; the cast operator, `CastExpression →
AscribeExpression ("as" Type)*`) — a third, type-position use was never specified in
`grammar.md`, and more importantly, it wasn't needed in the first place.

**A second spelling, `<T:Aspect>::AssocType` (colon instead of `as`), was also
considered and rejected the same day, for a sharper reason than aesthetics.**
`<T: Aspect>` already has exactly one meaning everywhere in Metel: declaring a fresh
generic type parameter with a bound —

```
GenericParam → IDENTIFIER ( ":" BoundList )?    // grammar.md:44, RFC-0034
```

— used identically in function signatures, struct/enum declarations, and `impl`
headers. A grep across every RFC stage and the whole public spec found zero instances
of that exact bracketed shape meaning anything other than "introduce a new type
parameter here." Reusing it in projection position to mean "select `T`'s
`Aspect`-specific view instead" collides with the *one, single* meaning that shape has
had everywhere else in the language — a reader's trained association from every other
`<T: Aspect>` is "this declares T," not "this selects among T's existing bounds." That
is a stronger collision than `as`'s two prior uses above, neither of which means
"declare a fresh binding" — so if a bracketed qualifier were ever adopted despite not
being needed, `<T as Aspect>::AssocType` would be the safer of the two spellings, not
`<T:Aspect>::AssocType`. Neither is adopted; this is recorded so neither gets
re-proposed without this reasoning attached.

**The bare projection stays ambiguous — this is a hard error, matching the existing
method-name-collision precedent (Static Dispatch Only, `T0013`) exactly**, not a case
needing its own disambiguation syntax. The escape hatch already exists, unmodified,
in §4: bind the associated type to a **fresh type parameter** instead of a concrete
type, via the equality constraint:

```metel
fun f<T: Deref<Target = U> + Convert, U>(x: &T) -> U {
    x.deref()   // ordinary, unambiguous method dispatch — `deref` and `convert`
                // are different method names, ordinary call resolution applies
}
```

`U` is an ordinary, unambiguous type parameter everywhere it's used — in the return
type, in `where` clauses, in `let` bindings — with no projection syntax involved at
all. This isn't a workaround bolted on after the fact: real code reaches an associated
type by calling the aspect's own (uniquely named) method in the overwhelming majority
of cases, which is unambiguous by ordinary method dispatch regardless of how many
aspects `T` is bound to; the bare-projection ambiguity only ever arises when a type is
named abstractly without going through a call, and §4's equality constraint already
covers that case completely.

**No new resolution machinery, no new grammar, and no dependency on a future
type-inference RFC.** §4's equality constraint and ordinary type inference/ascription
(both already specified and implemented — Hindley-Milner with let-polymorphism, RFC-0031;
ascription, `public/reference/spec/types.md` §Type Ascription) are sufficient. The
original deferral to "the type inference RFC" assumed a future foundational RFC would
need to define new syntax for this; no such RFC exists or is planned, and no new syntax
turned out to be needed either.

---

## 4. Equality Constraints in Bounds

`Aspect<AssocType = ConcreteType>` in a bound asserts that `T` implements `Aspect` and
that its associated type equals `ConcreteType`:

```metel
fun deref_to_node<T: Deref<Target = Node>>(x: &T) -> &Node {
    x.deref()
}

extend<T: Deref<Target = Node>> T: PrintNode { ... }
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
extend SmartPtr: Deref<Node> { ... }
extend SmartPtr: Deref<i64> { ... }

// Right model — associated type: one Target per implementing type
extend SmartPtr: Deref {
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

extend<R: Region> SubRegion<R>: Region {
    type AllocationError = !;
}

extend<R: Region> SubRegion<R>: Outlives<R> {}
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
   §3a (corrected the same day):** no new syntax — the bare projection stays ambiguous
   as a hard error (matching the existing method-name-collision precedent, `T0013`),
   and §4's equality constraint with a fresh type parameter already covers every real
   case. An earlier pass proposed `<T as Aspect>::AssocType`, borrowed from Rust
   without checking it against Metel's grammar (`as` already has two other uses); it
   wasn't needed once the existing mechanism was checked properly. The "type inference
   RFC" this was originally deferred to was never a real dependency either way — type
   inference (RFC-0031) is already implemented.

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
