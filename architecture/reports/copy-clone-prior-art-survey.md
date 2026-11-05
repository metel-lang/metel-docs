---
title: "Copyness in Other Languages: Prior-Art Survey"
date: '2026-11-03'
status: report
relates: rfc-0162, rfc-0206, rfc-0207, rfc-0212, rfc-0213
---

# Copyness in Other Languages: Prior-Art Survey

A survey of how other languages decide whether a value is duplicated implicitly, how a type states
that, and how the answer interacts with generics, tuples, closures, references and destructors.
It was written to inform the redesign of Metel's `Copy`/`Clone` model (RFC-0162, RFC-0206,
RFC-0207). It records findings and open questions. It does not choose a design. Sections 4 to 10 survey
copyness itself; section 11 (added 2026-11-04) surveys the sub-systems of the resulting proposal
(declaration clauses, derivation, super-aspects, exclusion, aspect properties, structural rules),
and includes Haskell and Scala.

## 1. Method and confidence

Findings are marked by source quality:

- **Verified** means read in a primary document (language reference, accepted proposal, release
  notes) during this survey. Sources are listed in section 12.
- **Memory** means stated from general knowledge and not re-checked here.
- **Unconfirmed** means a search was attempted and returned nothing usable, or the sources
  disagreed.

The older prior-art section of RFC-0162 covers Rust, C++, Swift, C# and Hylo in less depth. This
survey adds primary-source detail for Swift and Mojo, and a wider table of other languages.

## 2. The questions

Every language answers five questions, and the answers are largely independent:

1. **Default.** Does a plain assignment or argument pass duplicate the value or move it?
2. **Opting in or out.** How does a type change that default: an opt-in (Rust) or an opt-out
   (Swift, C++, Ada, D)?
3. **Where it is stated.** On the declaration, in an impl, in a derive, or by a lint?
4. **User code.** Can code of the author's choosing run during an implicit copy?
5. **Explicit duplication.** Is there a separate operation for a duplicate the programmer asks
   for, and how does it relate to the implicit one?

## 3. Summary table

| Language | Default | How a type differs | Written where | User code in implicit copy | Explicit duplicate | Confidence |
|---|---|---|---|---|---|---|
| Rust | move | opt in to `Copy` | an impl or a derive, anywhere in the crate | no, always a bit copy | `.clone()` | verified |
| Swift (structs, enums) | copy, inferred from fields | opt out with `~Copyable` | the declaration only | no (bitwise or copy-on-write) | `copy x` operator for borrowed bindings | verified |
| Swift (classes) | reference | not applicable | not applicable | not applicable | not applicable | verified |
| Mojo | move; implicit copy needs a marker | opt in with `ImplicitlyCopyable` | the struct's trait list | yes, a user copy initializer may run | `.copy()` | verified |
| C++ | copy | opt out with `= delete`, or write the copy constructor | the class | yes | the copy constructor | memory |
| D | copy | opt out with `@disable this(this)` | the struct | yes (postblit, copy constructors) | `.dup` for arrays | verified (bug threads) |
| Nim (ARC/ORC) | copy for value types | opt out with an error pragma on `=copy` | hook procedures | yes (`=copy`, `=sink`, `=dup`) | `=dup` | verified |
| Ada | copy (assignment) | opt out with `limited` | the type declaration | `Adjust` for controlled types | explicit procedures | verified |
| Go | copy everything | none; `go vet` flags copying a lock | a lint, not a type property | no | convention | verified |
| C# | copy for `struct`, reference for `class` | the declaration kind | the declaration | no | `Clone()` by convention | memory |
| Zig | copy everything | none | not applicable | no | convention | memory |
| Hylo | move; avoids implicit copies | not established | not established | not established | not established | unconfirmed |
| Carbon, Austral | not established | not established | not established | not established | not established | unconfirmed |

## 4. Rust

The `Copy` trait documentation states the model plainly.

- `Copy` is "types whose values can be duplicated simply by copying bits". Its behaviour "is not
  overloadable; it is always a simple bit-wise copy".
- `pub trait Copy: Clone {}`: "`Clone` is a supertrait of `Copy`, so everything which is `Copy`
  must also implement `Clone`. If a type is `Copy` then its `Clone` implementation only needs to
  return `*self`." The documentation does not state an agreement rule; the `*self` sentence is the
  expectation.
- A type cannot be `Copy` if a field is not (error E0204) or if it implements `Drop`.
- Derive adds a bound on every type parameter, which the documentation calls imprecise: `&T` is
  `Copy` for any `T`. The documented remedy is a manual impl with the exact bound.
- "Implementing `Copy` is part of the public API of your type", so adding a non-`Copy` field later
  is a breaking change.

The direction of travel is toward more explicitness. The 2026 ergonomic ref-counting project goal
proposes a `Share` trait, a subtrait of `Clone`, meaning "creates an alias", distinct from "is
cheap to clone", with closures that capture selected values by `move(...)`. This is a goal with
prototypes planned, not shipped.

## 5. Swift

### 5.1 Copyability is a protocol with an implicit default

- `Copyable` has "no explicit requirements, and it has some special behaviors". Structs are
  implicitly `Copyable` "unless [they have] a noncopyable stored property", enums unless an
  associated value is noncopyable. Classes and actors always are, copied by retain and release.
  "Extensions to the `Copyable` protocol are not allowed."
- A struct or enum opts out with `~Copyable` on its declaration. Suppression is not allowed in an
  extension, on a class, or where it "must hold for some other reason".
- Generic parameters implicitly carry `Copyable`. `func f<T: ~Copyable>` accepts both kinds. A
  protocol opts into noncopyable conformers by suppressing its own default, and the top type `Any`
  is `any Copyable`.
- Making a copyable type noncopyable is a breaking change. The reverse is source compatible.

### 5.2 Conditional copyability is deliberately narrow

`extension List: Copyable where T: Copyable {}` is the form. The conditions must be `T: Copyable`
on a generic parameter, the extension must be in the type's own file, and it is not allowed on a
type with a `deinit`. An unconditional `extension Optional: Copyable {}` is rejected.

### 5.3 Copies are implicit, with an explicit operator where it matters

Copying a copyable type is implicit. SE-0377 added `borrowing` and `consuming` parameter
modifiers, and a revision made such bindings not implicitly copyable: where a copy is needed one
writes `copy x`, an operator that yields an independently owned copy and "may still be optimized
away". The motivation is visibility of copies that defeat ownership optimisation. The exact rule
as shipped could not be confirmed from the sources found.

### 5.4 Tuples, closures and function types

- Tuples of copyable types are copyable (the `Copyable` documentation). SE-0390 lists tuples among
  places a noncopyable type cannot appear, with the future direction that a tuple holding one
  would itself be noncopyable. Whether that shipped is unconfirmed.
- Only nonescaping closures are excluded from the implicit default: they have scoped lifetimes and
  "can borrow their captures". Escaping closures are copyable whatever they capture, and values
  they capture "behave like class properties" (shared boxes). A noncopyable value cannot be
  consumed when captured by an escaping closure, and there is no one-shot closure type.
- A nonescaping function type is a distinct type from an escaping one, and all function types are
  escapable, which is why `withoutActuallyEscaping` can reverse nonescapingness. That API is a
  promise the compiler no longer checks.

### 5.5 References and views

- `Span`, a read-only view, is declared `Copyable, ~Escapable`. Making it noncopyable "was in the
  early vision", but that "would make `Span` a poor match to model borrowing semantics".
- `MutableSpan` is `~Copyable, ~Escapable`: "Mutability requires exclusive access ... This
  explains why the type which models mutations must be non-copyable." It cannot be a subtype of
  `Span`, and it hands out a read-only `Span` through a borrowing accessor.
- `Copyable` and `Escapable` are independent: "There is no relationship between `Copyable` and
  `Escapable`". A nonescapable value may be copied freely within the current scope.

### 5.6 Destructors

Noncopyable structs and enums may declare `deinit`, which runs when the value's lifetime ends.
Conditional copyability is not allowed on a type with a `deinit`.

## 6. Mojo

### 6.1 The model was reversed in v0.25.6

Before: `Copyable` meant implicitly copyable and `ExplicitlyCopyable` covered the rest. Now:

- `Copyable` is a type whose value can be explicitly copied with `.copy()`.
- `ImplicitlyCopyable` is "a marker trait to permit the compiler to insert implicit calls to the
  copy constructor". It "inherits from `Copyable`, and requires no additional methods".
- The stated reason is a "long-standing issue with Mojo effectively forcing implicit copyability
  upon all types", and fewer "performance and correctness issues caused by accidental implicit
  copies". The change was staged: a warning for `List` and `Dict` in one release, an error in the
  next.

### 6.2 One definition of the copy

- The required hook is the copy initializer, `__init__(out self, *, copy: Self)`. `copy()` is a
  provided convenience for `Self(copy=self)`, and "overriding this method is not allowed".
- The initializer is synthesised "when possible". `ImplicitlyCopyable` is synthesised only when all
  fields are `ImplicitlyCopyable`. For mixed fields the author declares it and writes the
  initializer, copying the others with `.copy()`, so user code can run at an implicit copy.
- The reason given for the refinement is that it ensures "only one definition for the logic of how
  a type is copied".
- Triviality is a separate computed property: a copy is trivial "when the compiler generates it
  and all of `T`'s fields are themselves trivially copyable".
- Guidance: "Use `ImplicitlyCopyable` only when implicit copying is required by the compiler or an
  API contract. Prefer an explicit `copy()` call, especially when copying may allocate memory or
  otherwise have significant cost." Generic code should bound on `Copyable`. The standard
  collections require only `Copyable` of their elements.

### 6.3 Move, tuples, closures, views

- Every `Copyable` type is `Movable`. A `Movable`-only type is move-only, and a type with neither
  is immovable.
- `Tuple` is `struct Tuple[*Ts: Movable]`, with `Copyable` and `ImplicitlyCopyable` each listed
  `where all_conforms_to[...]` over the element types.
- "A closure is `Copyable` when every value it captures is `Copyable`." A move-only capture makes
  it `Movable` only. Copying a closure runs each captured value's copy initializer, at assignment.
  Captures are chosen in a capture list (read, mut, var copy, transfer). Escaping closures are not
  supported, and there is no one-shot closure type yet. The `thin` effect marks a function type as
  a stateless function pointer. Whether closures are `ImplicitlyCopyable` is not stated.
- A default (`read`) argument is a reference, not a copy. `mut` arguments are checked for
  exclusivity at the call. `Span` is parameterised by mutability and origin, and its stable page
  lists `Copyable` and `ImplicitlyCopyable`; whether that holds for mutable instantiations is
  unconfirmed.

## 7. Other languages

- **C++** (memory). Every class has an implicitly generated copy constructor that the author can
  replace or delete. The coupled special members are documented as the rules of three, five and
  zero. There is no marker separating a cheap copy from an allocating one.
- **D** (verified). Structs copy with postblit or copy constructors, which are user code.
  `@disable this(this)` makes a struct non-copyable; the maintainers treat the resulting errors
  when appending to arrays as intended.
- **Nim** (verified). `=copy`, `=sink`, `=dup` and `=destroy` are user hooks. A copy can be
  disabled by declaring `=copy` with the error pragma.
- **Ada** (verified). A `limited` type forbids assignment. A controlled type customises it
  through `Adjust`, and a limited controlled variant exists without `Adjust`.
- **Go** (verified). Everything copies. `go vet` reports copying a value that contains a lock
  (assignments, parameters, receivers, range variables). The protection is a lint, not a type
  property.
- **C# and Zig** (memory). `struct` copies bitwise on assignment with no user hook in C#, as
  does Zig; neither has a copy marker.
- **Hylo** (unconfirmed). Its introduction says it "avoids hidden costs such as implicit copies".
  Its rules on explicit copy could not be found.

## 8. Cross-cutting findings

1. **Opting out on the declaration is the usual shape for languages that copy by default.**
   Swift `~Copyable`, Ada `limited`, D `@disable this(this)`, C++ `= delete` and Nim's error pragma
   all place the property on the type. Rust is the exception among them: its grant is an impl or a
   derive that may be far from the type.
2. **Two levels recur in the languages that move by default.** Rust (`Clone`, `Copy`) and Mojo
   (`Copyable`, `ImplicitlyCopyable`) separate "can be duplicated" from "is duplicated for you".
   Mojo's version makes the second a method-less marker that refines the first, so there is one
   definition of the copy.
3. **User code at an implicit copy splits the field.** Allowed in C++, D, Nim, Ada (controlled
   types) and Mojo's initializer. Not allowed in Rust, Go, Zig, C# and Swift structs.
4. **Generics integration is by implicit bound or by refinement, not by impl per type.** Swift gives
   every generic parameter an implicit `Copyable` bound that can be suppressed. Mojo asks generic
   code to bound on the explicit trait.
5. **Conditional copyability is restricted.** Swift allows only `T: Copyable` on parameters, in the
   type's file. Mojo uses conditional conformance over a variadic pack for tuples.
6. **Structural types copy by their parts.** Tuples in Swift and Mojo, with no way to assert it.
7. **Closure copyability follows captures in Mojo and escapingness in Swift.**
8. **Mutable views are non-copyable (Swift) or exclusivity-checked at the call (Mojo).** Read-only
   views are copyable in both.
9. **Destructors and copyability interact.** Swift forbids conditional copyability on a type with a
   `deinit`, and Rust forbids `Copy` with `Drop`.
10. **Visible cost is the stated motive in the newest changes** (Swift `copy x`, Mojo `.copy()`
    and its migration, Rust's proposed `Share`).
11. **Migrations are staged.** Mojo's change went warning, then error. Swift keeps new suppression
    out of extensions to avoid breaking existing code.

## 9. Observations for Metel

These are observations that bear on the open questions in RFC-0162. They are not decisions.

- The current Metel pair already has Mojo's shape under Rust's names: `Clone` is the explicit
  level and `Copy` is the implicit marker. The difference is that Metel's marker is a separate
  aspect with a blanket relationship, while Mojo's refines the explicit trait by declaration.
- A refinement relation, declared once, makes the coverage gap found in the adversarial review
  structurally impossible: every implicit-copy type, references and views included, must be
  explicitly copyable.
- A name pair that keeps `Clone` and renames the implicit marker (for example `ImplicitClone`)
  avoids reusing `Copy` with a different meaning, which would be a false friend for Rust
  programmers. A pair that reuses `Copy` for the explicit level does not.
- Swift's rule that copyability is fixed where the type is declared, and that conditional forms are
  limited and local, is the closest precedent for the visibility concern in RFC-0162's D6.
- No surveyed language lets a user assert copyability on a tuple type. A structural marker
  (RFC-0212) would be new.
- Nothing found supports sealing the implicit copy to a bitwise body. Mojo permits user code in
  the initializer and advises against costly implicit copies instead.
- Both Swift and Mojo tie closure and function-type copyability to different things (escapingness
  against captures), and Metel's RFC-0134 rule matches Mojo's.

## 10. Unconfirmed items and how to settle them

- Which Swift standard-library types shipped as conditionally copyable, whether noncopyable tuple
  elements shipped, and the exact form of the `copy x` rule: read the current SE-0377, SE-0427 and
  standard library source.
- Whether Mojo closures and mutable `Span` values are `ImplicitlyCopyable`, and whether references
  and pointers are copyable: read the Mojo standard library source.
- Hylo, Carbon and Austral: read their specifications directly.
- Mojo documentation moves between hosts and versions; the pages cited below were reachable on
  2026-11-03.

## 11. Prior art by sub-system of the proposal

Added 2026-11-04, after the settlement of RFC-0206, RFC-0207, RFC-0212 and RFC-0213. Each entry
states what the other languages do and where the proposal sits relative to them. Confidence marks
are as in section 1.

### 11.1 Two levels, with a method-less marker refining the explicit one

- Rust: `Copy: Clone` (verified). Mojo: `ImplicitlyCopyable` implies `Copyable`, and the docs say
  all implicitly copyable types must be `Copyable` (verified).
- Swift infers copyability and suppresses it with `~Copyable` (verified, section 5).
- Haskell has no copy concept; the same refinement shape appears as `Eq => Ord` (memory).
- Proposal: Mojo's shape with Rust's names, so every implicit-copy type is explicitly cloneable by
  construction.

### 11.2 Where the grant is written

- Rust: an impl or derive anywhere in the crate (verified, section 4). Haskell: instances anywhere,
  orphans allowed with a warning (memory).
- Swift synthesizes only in the type declaration or a same-file extension (verified, SE-0185).
  Mojo: the struct's trait list (verified).
- Proposal: `declared`, the strictest form: only the declaration clauses; `extend T: ImplicitClone;`
  is an error.

### 11.3 Derivation as a request in the header

- Haskell `deriving` and `StandaloneDeriving`, Scala 3 `derives` (a companion `derived` method;
  the instance is placed in the companion; verified), Rust `#[derive]` (verified).
- In Swift and Mojo the colon in the header is itself the request and the compiler synthesizes
  unless the member is written (verified: SE-0185; Mojo's `Copyable` generates the copy constructor
  unless one is written). This is the "synthesized unless written" model: a reader cannot tell
  from the header who wrote the implementation.
- Haskell, Scala and Rust report a duplicate instance when both a derive and a written instance
  exist (memory).
- Haskell's `DerivingVia` and newtype deriving reuse the representation's instance; GHC notes their contexts often cannot be inferred and must
  then be written with standalone deriving (verified: GHC issue #18219). Nothing in the proposal
  corresponds to them.
- Proposal: `derives` means the compiler wrote it and `:` means the author did; both together are
  `T0015`. This keeps the duplicate-instance rule of Haskell, Scala and Rust and adds a header
  that records authorship.

### 11.4 Super-aspects and deriving them

- Haskell (`deriving Ord` without an `Eq` instance is an error) and Rust (`derive(Copy)` without
  `Clone`) only require the super-aspect. The Haskell rule is that `Eq` is a superclass of `Ord`, so an `Ord`
  instance needs an `Eq` instance (verified in GHC discussions; the exact current error text was
  not seen); the Rust rule is memory.
- Swift derives a missing super-aspect: declaring `Hashable` synthesizes `Equatable` as well
  (verified: SE-0185), and a hand-written `==` takes precedence.
- Both Haskell and Rust accept a derived `Ord` over a hand-written `Eq`; the consistency between
  the two is a convention (memory).
- Proposal: a super-aspect entry is an obligation unless marked `derived`; `derives A` derives `A` and
  every marked super-aspect, and a written impl of a derived one is `T0015` (RFC-0213 section 4). A
  derived marker is sound only over a derived base. This is opt-in per entry where Swift derives what is
  missing, and it never derives over a written impl.

### 11.5 Exclusion and negative entries

- Rust hardcodes the `Copy`/`Drop` exclusion (error E0184; verified); negative impls
  (`negative_impls`) and user-defined auto traits (`auto_traits`) are unstable features (verified:
  Unstable Book). An auto trait cannot have items or supertraits (verified). Swift's `~Copyable` suppresses a default requirement and is not an
  exclusion between two protocols (verified).
- Haskell has no negative instances; exclusion is simulated with closed type families or custom
  type errors (memory). C++ constraints can negate a concept (not checked).
- Proposal: a negative entry in the super list (`aspect ImplicitClone: Clone, !Drop`). No surveyed
  language declares an exclusion on the aspect itself.

### 11.6 Properties of the aspect declaration

- Rust: lang items and unstable auto traits. Swift: `Sendable` and `@_marker`. Swift's `@_marker`
  is a compiler-internal underscored attribute: a marker protocol has no requirements and no runtime
  representation (verified). Haskell: classes solved by the compiler and closed to user instances,
  such as `Typeable`, `Coercible` and `KnownNat` (verified: GHC error index and base docs;
  `HasField` not checked).
- Visibility of structural grants is a semver question. Swift infers `Sendable` only for types
  that are not publicly ABI-exposed, because inference on a public type is an API commitment
  (verified: the SE-0302 review). The Rust language team calls each auto trait a semver hazard:
  adding a private field can remove `Send` from a public type (verified: the lang-team design
  note on auto traits), and `cargo-semver-checks` carries lints for it.
- Proposal: the semantics are declared properties read by identity; `implicit` is std only;
  `declared` avoids the leak. `auto` (Send/Sync/Linear) would inherit the Rust hazard and is
  deferred with the RFC-0096 revision.

### 11.7 The field-wise rule

- C++: the implicit copy constructor is defaulted or deleted per instantiation from the members
  (verified in part: cppreference lists the cases in which the implicit copy constructor is deleted,
  among them a member whose copy constructor cannot be selected). It is the closest precedent for
  an exact per-instantiation predicate.
- Rust: `derive(Clone)` adds a bound on every type parameter, over-approximating. The "perfect
  derive" fix is not in the language; a third-party crate prototypes it (verified).
- Haskell infers the context of a derived instance, accepts only contexts of bare type variables
  without repetition, and otherwise requires `StandaloneDeriving` with a written context (verified:
  GHC user guide). Swift conditional conformance is explicit and,
  for copyability, limited to `T: Copyable` (verified).
- The rule itself can be library code: Haskell `GHC.Generics` with `DefaultSignatures` and `DeriveAnyClass` (verified: GHC user guide), and Scala
  `Mirror` with Magnolia (verified for Scala).
- Proposal: a std-written row template (RFC-0123 form), exact per instantiation, checked at the
  declaration when the field types are concrete.

### 11.8 Built-in structural kinds

- Rust: the compiler implements `Copy` for tuples of `Copy` types, function pointers and items, and
  closures whose captures are `Copy`, and supplies `Clone` for them (verified: Rust Reference). Arrays
  are not in that list; their impls are library code (memory). Mojo uses
  conditional conformance over a variadic pack (verified, section 6). Haskell's base defines
  tuple instances by hand up to a fixed arity; a 2005 mailing-list source gives 15 for `Eq` and `Ord`,
  the current limit was not confirmed.
- Proposal: compiler rules for tuples and arrays until variadics (RFC-0125) and compile-time
  lengths (RFC-0132 section 3) exist, then impls.

### 11.9 User code at an implicit copy

- Allowed in C++, D, Nim and Mojo; not allowed in Rust and Swift structs (section 8, finding 3).
- Mojo advises against implicit copies of costly types and against bounding generic code on
  `ImplicitlyCopyable` (verified). C++ states the corresponding promise with `noexcept` and
  `is_nothrow_copy_constructible` (verified: cppreference).
- Proposal: the hook is the type's own `Clone`; the cheap, total and effect-free contract is stated
  and checked only once an effect system exists.

### 11.10 Destructors

- Rust rejects `Copy` together with `Drop` (E0184). The compiler documentation gives the reason as
  an unsound implementation (issue #20126), not a stated drop-twice rule (verified). Swift forbids
  conditional copyability with a `deinit` (section 8, finding 9). Mojo allows a destructor on a
  type with a user copy initializer (memory).
- Proposal: `!Drop` on `ImplicitClone` is a policy, not a soundness rule, because the hook can
  duplicate the resource. It can be relaxed by removing one super-list entry.

### 11.11 Equality

- Haskell's single `Eq` makes `Eq Double` violate reflexivity (`NaN /= NaN`) (verified: the base documentation for `Eq Double` states that `0/0 == 0/0` is `False`). Rust's
  `PartialEq`/`Eq` split is the fix and RFC-0168 follows it.

### 11.12 Summary of positions

| Sub-system | Closest precedent | Where the proposal differs |
|---|---|---|
| Marker refining the explicit level | Mojo | Rust's names; guaranteed coverage of built-in kinds |
| Grant only in the declaration | Swift (synthesis), Mojo | Stricter: no same-file extension |
| `derives` versus `:` | Scala `derives`, Haskell `deriving` | The colon authorizes, `derives` generates |
| Marked super-aspect derivation | Swift `Hashable` | Opt-in per super entry; never over a written impl |
| Exclusion in the declaration | none (Rust hardcodes it) | New |
| Declared aspect properties | Rust lang items, Swift `Sendable` | Properties are data, `implicit` std only |
| Exact structural rule | C++ implicit copy constructor | Checked at the declaration, written in std |
| User hook at implicit copy | C++, Mojo | Opt-in marker, reserved effect bound |

### 11.13 Verification status

Checked on 2026-11-04 against primary or near-primary sources: Swift synthesis and `Sendable`
inference, Scala `derives`, Mojo `ImplicitlyCopyable` implying `Copyable`, Rust `perfect derive`
status and auto-trait semver hazard, Rust E0184, Unstable Book entries for `negative_impls` and
`auto_traits`, Rust Reference on built-in `Copy` and `Clone`, cppreference on the deleted implicit
copy constructor and `is_nothrow_copy_constructible`, GHC user guide on deriving contexts,
standalone deriving, `DefaultSignatures` and `DeriveAnyClass`, base documentation on `Eq Double`,
`Coercible` and `Typeable`, and Swift `@_marker`.

Still unconfirmed:
- Whether Mojo permits a destructor on an `ImplicitlyCopyable` type (the page fetch failed and the
  search results are silent).
- The current size limit of base's hand-written tuple instances in Haskell.
- Whether Haskell's `HasField` is solved by the compiler as claimed.
- Rust's rule that `derive(Copy)` requires `Clone`, and that `derive(Ord)` accepts a hand-written
  `Eq` (both memory).
- Haskell and Rust acceptance of a derived `Ord` over a hand-written `Eq`, and the duplicate-instance
  behaviour for derive plus written impl in Haskell, Scala and Rust (memory).
- That C++ constraints can negate a concept.

## 12. Sources

- Rust: https://doc.rust-lang.org/std/marker/trait.Copy.html and the 2026 ergonomic ref-counting
  goal at https://rust-lang.github.io/rust-project-goals/2026/ergonomic-rc.html
- Swift: SE-0390 (noncopyable structs and enums), SE-0427 (noncopyable generics), SE-0377
  (parameter ownership modifiers), SE-0446 (nonescapable types), SE-0447 (Span) and SE-0467
  (MutableSpan) under https://github.com/swiftlang/swift-evolution/tree/main/proposals, and
  https://developer.apple.com/documentation/swift/copyable
- Mojo: https://mojolang.org/releases/v0.25.6/ ,
  https://mojolang.static.modular.com/docs/std/traits/copyable/Copyable/ ,
  https://mojolang.org/docs/manual/lifecycle/life ,
  https://mojolang.org/docs/manual/values/ownership/ ,
  https://mojolang.org/docs/reference/closure-declarations/ ,
  https://mojolang.org/docs/std/builtin/tuple/Tuple/ ,
  https://forum.modular.com/t/mojo-closures-2026/3013 ,
  https://mojolang.org/releases/v1.0.0b1/
- Ada: https://docs.adacore.com/live/wave/arm12/html/arm12/arm12-7-6.html
- Nim: https://nim-lang.org/docs/destructors.html
- D: https://issues.dlang.org/bugs/20367/
- Go: https://go.dev/src/cmd/vet/testdata/copylock/copylock.go
- Hylo: https://hylo-lang.org/introduction/
- Swift synthesis and Sendable inference: SE-0185 at
  https://github.com/swiftlang/swift-evolution/blob/main/proposals/0185-synthesize-equatable-hashable.md
  and the SE-0302 review at https://forums.swift.org/t/accepted-se-0302-sendable-and-sendable-closures/45786
- Mojo `ImplicitlyCopyable`: https://docs.modular.com/mojo/std/builtin/value/ImplicitlyCopyable
- Scala 3 derivation: https://dotty.epfl.ch/3.0.0/docs/reference/contextual/derivation.html
- Rust perfect derive: https://github.com/lucentflux/perfect-derive ; auto traits and semver:
  https://lang-team.rust-lang.org/design_notes/auto_traits.html
- Verification sources (2026-11-04): https://doc.rust-lang.org/unstable-book/language-features/auto-traits.html ,
  https://doc.rust-lang.org/unstable-book/language-features/negative-impls.html ,
  https://rust.googlesource.com/rust/+show/03028df750147a93f3199fef95932cfecdc2b375/compiler/rustc_error_codes/src/error_codes/E0184.md ,
  https://downloads.haskell.org/ghc/latest/docs/users_guide/exts/deriving_inferred.html ,
  https://ghc.gitlab.haskell.org/ghc/doc/users_guide/exts/standalone_deriving.html ,
  https://gitlab.haskell.org/ghc/ghc/-/issues/18219 ,
  https://errors.haskell.org/messages/GHC-97044/ ,
  https://hackage.haskell.org/package/base-4.14.0.0/docs/Data-Eq.html ,
  https://hackage.haskell.org/package/base-4.14.0.0/docs/Data-Coerce.html ,
  https://cppreference.com/cpp/language/copy_constructor ,
  https://cppreference.com/cpp/types/is_copy_constructible ,
  https://github.com/swiftlang/swift/pull/39812
