---
id: rfc-0210
title: "Enum Variant Types and Variant Rows"
date: '2026-11-02'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/1791'
---

## Summary

Explore first-class types for individual enum variants and a way to describe an enum's
variants and their payloads generically. The immediate motivation is variant-preserving
construction: the language owner leans toward a per-variant constructor returning that
variant's type, so a successful `Interval::Closed(...)` cannot produce `Empty`. This is
a design direction, not a settled type system or permission to implement it.

The previous proposal used `<enum E>` and `..E` for a row of variants and based enum
derivation on RFC-0209's per-aspect templates. RFC-0209 is superseded, nominal row-based
derivation is deferred, and RFC-0254's agreed initial direction gives an enum an empty
**ordinary structural field row**. Consequently `..E` cannot simultaneously mean that
field row and a variant inventory. This RFC does not choose a replacement spelling,
binder, or representation for variant enumeration. Its previous template design is
available in git history and remains deferred work.

## 1. Variant types and construction

```metel
enum Interval { Empty, Closed { low: i64, high: i64 } }
// Illustrative only: syntax and result types are not settled
fun make_closed(low: i64, high: i64) -> Interval::Closed { … }
let interval: Interval := make_closed(1, 5); // candidate widening
```

A candidate variant type identifies the enclosing enum declaration, the variant, and
all instantiated enum arguments (language owner, 2026-11-26). This includes unit variants:
`Option<i32>::None` and `Option<String>::None` are distinct types despite empty payloads.
Variant types are nominal (language owner, 2026-11-26): structural matching of public
payload fields does not make a variant interchangeable with a same-shaped anonymous
record or a variant of another enum.
In type position, write the enum arguments before the variant path, as in
`Option<i32>::Some` (language owner, 2026-11-26). Expression-position turbofish,
parsing and name resolution remain to be reconciled with existing syntax.
Variant types require the enclosing enum qualifier in type position (language owner,
2026-11-26); the compiler does not search for an unqualified variant type. Existing or
proposed expected-type shorthand for expressions and patterns is a separate rule.
Variant types are valid generic type arguments, such as `List<Interval::Closed>` and
`Result<Interval::Closed, InvalidBounds>`, subject to ordinary visibility, ownership and
bound rules (language owner, 2026-11-26).
This RFC does not introduce variant types as generic bounds (language owner,
2026-11-26). A function requiring the exact variant can take `&Interval::Closed`
directly; generic aspect and structural bounds follow their own rules.
Variants do not introduce generic parameters of their own in this RFC; a variant type
uses the enclosing enum's parameters and arguments (language owner, 2026-11-26). Any
future variant-local generics require a separate design.
For a generic unit variant, an expected type may determine otherwise unconstrained enum
arguments (language owner, 2026-11-26). When inference cannot determine them, an
annotation or explicit arguments are required; the compiler must not invent an argument.
For example, `let a: Option<i32> := Option::None` supplies `i32`, while an unconstrained
`let a := Option::None` is an error. Explicit expression spelling remains to be checked.
Values of different variants or different enum instantiations remain distinct, and each
widens only to its corresponding enclosing enum instantiation. A variant value implicitly widens to its enclosing enum
where that enum is expected (language owner, 2026-11-26); widening forgets the static
variant fact and preserves the enum instantiation. By-value widening follows ordinary
ownership rules: it moves a non-`Copy` value and copies a `Copy` value, without implicitly
duplicating it (language owner, 2026-11-26). Converting an arbitrary enum value to
a particular variant requires a checked operation. A successful per-variant constructor returns the
requested variant type or an error; it cannot return a different variant. An ordinary
function returning the enclosing enum may choose among variants. This would express the
owner's preferred preservation rule without proving an input/output tag relation in an
unrestricted enum-wide constructor. None of the syntax, widening, fallibility, `Self`,
visibility, or privileged minting details is settled. RFC-0100 and RFC-0114 own the
construction interfaces and must be reviewed together with this proposal.

Following RFC-0114's fallibility direction, an infallible variant constructor returns the
variant type, while a fallible one returns `Result<Variant, Error>` (language owner,
2026-11-26). Handling an error exposes a successful variant value, which may then widen
to its enclosing enum. The exact signature, uninhabited-error behavior and coercion
positions need joint specification with RFC-0114; no implicit error handling is implied.
Each variant constructor may have its own error type (language owner, 2026-11-26); one
variant may be infallible while another returns a `Result` with its own error. The
enclosing enum does not impose a shared constructor error type in this design.
A custom variant constructor may expose a public parameter interface different from its
stored payload and compute private payload fields (language owner, 2026-11-26), as for
struct constructors. Its successful result remains its own variant type. Declaration,
visibility, argument binding and canonical construction require RFC-0100 / RFC-0114
reconciliation; no constructor-overload rule is introduced here.
Privileged representation construction of a variant is available only in that variant's
own canonical constructor or explicitly unchecked counterpart (language owner,
2026-11-26). A constructor for another variant cannot use the privileged form to bypass
it; ordinary code invokes the target variant's construction interface. This is not a
separate mechanism from RFC-0114 §1.1's privileged struct-level construction (split
there from RFC-0100 section 3, 2026-11-27, since it depends on RFC-0114's own
`Construct`/`ConstructUnchecked` aspects): it is RFC-0114 section 9's draft extension of
that same mechanism one level down, proposing the brace form
`Self::Variant { field = value }` and bare `Self::Unit`, minted inside the enum impl's
own `construct`/`construct_unchecked` (own type only, no recursion through the call
form). RFC-0114 §1.1 explicitly scopes its own privileged form to struct/enum-whole-type
construction and defers per-variant privilege to its own section 9 pending that
section's acceptance; this RFC does not independently define variant-level privileged
construction syntax, and should not be read as a third mechanism alongside those two.
RFC-0114 owns the unchecked boundary and the precise minting rules.

A shared reference to a variant may widen to a shared reference to its enclosing enum
(language owner, 2026-11-26), preserving origin and lifetime. Unrestricted widening
from `&var Variant` to `&var Enum` is rejected: a callee could replace the variant and
invalidate the original place's static type. A future restricted access form may revisit
exclusive widening; its soundness and interaction with reborrowing are not settled here.
Variant widening does not by itself introduce conversions between generic container
instantiations: `List<Interval::Closed>` does not automatically become `List<Interval>`
under this RFC (language owner, 2026-11-26). Container variance and any element-wise
conversion remain separate rules; an explicit operation may convert elements where available.
A binding declared with a variant type accepts assignments compatible with that variant,
not a sibling variant (language owner, 2026-11-26). A binding declared with the enclosing
enum type may accept any of its variants by ordinary widening. Inferred mutable-binding
types follow the same inference as immutable bindings: absent an expected enclosing enum
type, a variant constructor yields its variant type (language owner, 2026-11-26). To
assign sibling variants, annotate the binding with the enclosing enum. Flow-sensitive
refinement and interactions with other inference and coercion rules need integration review.

At a control-flow join, branches producing the same instantiated variant retain that
variant type. Branches producing different variants of the same instantiated enum widen
to their common enclosing enum (language owner, 2026-11-26). This does not establish a
join for variants of unrelated enums or different generic instantiations; ordinary join
and coercion rules apply there. Reference joins still obey the shared/exclusive widening
rules and preserve origins and loan lifetimes.

In a successful `Closed` match arm, a usable binding to the whole matched value may be
treated as `Interval::Closed` (language owner, 2026-11-26). A by-value match follows
ordinary move rules; matching through shared or exclusive references yields the
corresponding borrowed variant type. A live narrowed reference prevents replacement of
the active variant. Binding syntax, lifetime propagation and behavior at control-flow
joins still need specification. A variant type must not let code read
a payload after the active variant has changed, bypass privacy, duplicate ownership, or
violate `Drop` and linear obligations. Recursive and generic enums, empty/uninhabited
variants and `Option`/`Result` need worked examples. An enum's memory layout, ABI and
runtime tag are not prescribed by this draft.

A variant type with an uninhabited payload remains a valid, nameable type but has no
values (language owner, 2026-11-26). For example, the `Err` variant of
`Result<i32, !>` is uninhabited. Existing exhaustiveness and bottom-type rules apply;
generic spelling, coercion interactions and diagnostics need integration review.
For a match whose scrutinee has a known variant type, exhaustive coverage is checked
against that variant alone (language owner, 2026-11-26). Its payload patterns must still
cover all inhabited payload cases; sibling variants need no arms. Existing unreachable
pattern and uninhabited-type rules need reconciliation.
A `let` pattern naming the scrutinee's statically known variant is irrefutable when all
of its payload subpatterns are irrefutable (language owner, 2026-11-26). The same
variant pattern against the enclosing enum remains refutable unless existing
inhabitedness rules prove otherwise. Moves, private fields and `Drop` remain subject to
their ordinary pattern and ownership rules.

A variant type may appear in a public API when its enclosing enum and the variant are
visible (language owner, 2026-11-26). Publishing that type does not publish its private
payload fields. Visibility of generic arguments and other signature components follows
the existing public-interface rules. Variant types follow the existing visibility of
their enclosing enum's variants; this RFC adds no per-variant visibility modifier
(language owner, 2026-11-26). Variant resolution needs reconciliation with the enum
declaration and module specifications.
A value statically typed as a particular variant permits direct access to its payload
fields without another match (language owner, 2026-11-26), subject to field visibility,
borrowing and ownership rules. The static type establishes the active variant; partial
moves and variant residuals remain deferred to RFC-0150.

**Working direction (language owner, 2026-11-26):** permit an aspect implementation for
a variant type independently of its enclosing enum. A successful match that narrows a
usable value or reference may therefore make the variant's aspect available even when
the enum lacks it. This needs explicit coherence, orphan, generic and dispatch rules,
and an adversarial comparison with the partial-move concern in RFC-0214. A variant impl
does not automatically imply an impl for the enclosing enum or for sibling variants.
Even when every variant implements an aspect, the enclosing enum requires its own
explicit implementation or derivation (language owner, 2026-11-26). A future forwarding
mechanism may generate that impl but must not grant it implicitly.
An implementation for the enclosing enum and an implementation of the same aspect for
one of its variants may coexist (language owner, 2026-11-26). Dispatch follows the static
receiver type: a variant-typed value uses the variant impl, and a value widened to the
enum uses the enum impl. Same-target overlap, generic conditions, trait-object erasure and
super-aspect obligations still require coherence and dispatch review.
Variant types may also declare inherent methods and associated functions (language
owner, 2026-11-26). They are available through the variant's static type, including a
successfully narrowed match binding; the enclosing enum does not automatically acquire
them. Visibility, generic parameters, name resolution and conflicts need joint review with
the existing inherent-method rules. When the enum and its variant both define an inherent
method with the same name, a variant-typed receiver selects the variant method and an
enum-typed receiver selects the enum method (language owner, 2026-11-26). Interactions with
overloads and aspect methods remain to be checked. Whether an enum method is considered
as a fallback on a variant receiver remains open. Shared reference widening is allowed,
but unrestricted mutable widening is rejected because a method could replace the variant.
The resulting apparent call-site asymmetry needs design: candidates include requiring
explicit widening, a checked variant-preserving mutable receiver capability, or changing
the binding's type after an unrestricted call. The second is a non-binding lean and needs
borrowing, origin, mutation and lookup rules; no automatic enum-method fallback is decided.

## 2. Three different rows

- **Ordinary structural field row.** RFC-0254 currently assigns the enclosing enum an
  empty row; it does not expose one variant's fields by extracting `..E`.
- **Variant inventory.** The enum's set of variants and their payload descriptions is
  sum-type information. How it is represented, constrained, reflected and extracted
  remains open. It is not an ordinary product row by assumption.
- **A particular variant's payload fields.** A variant type's ordinary structural row
  contains its present public payload fields (language owner, 2026-11-26). Thus a
  `Closed` value can satisfy a public `.low` bound while retaining its variant and enum
  identity. Private payload fields remain hidden. Partial moves and residuals of a variant
  are deferred to RFC-0150, their design owner (language owner, 2026-11-26), with ownership
  and `Drop` rules reviewed there. An enum-wide `Clone` implementation must account for every
  variant, not use the empty structural row as a vacuous proof.

RFC-0208's `<..R>` binds a row of labelled fields and is shared by identifier- and
numeric-labelled product rows. It does not currently bind a variant inventory or define
a sum-type row. If variant inventories eventually reuse a general row representation,
their members' kinds, binding, bounds, disjointness and operations must be specified;
no new `<enum E>` kind or reinterpretation of `..E` follows automatically. Conversely,
introducing a distinct inventory kind requires an explicit binder and extraction design.

## 3. Worked interaction cases

1. `Closed<i32>` and `Closed<String>` of a generic enum preserve their distinct enclosing
   arguments. A variant of another enum cannot match merely because its payload is the
   same shape. Exact surface spelling is open.
2. If a `Closed` value widens to `Interval`, subsequent matching must remain exhaustive
   for `Interval`; narrowing on a match must not let a stale reference survive an
   incompatible mutation or replacement.
3. A public variant type must not expose private payload fields through structural bounds,
   generic row extraction, aliases, or reflection. If structural matching is permitted,
   RFC-0243's public-row policy and RFC-0254's ordinary extraction rule apply consistently.
4. A synthesized or custom constructor for `Closed` must not return `Empty` on success.
   A fallible constructor may report an error; a factory returning `Interval` can choose
   either variant. Bare and call-shaped unit-variant expressions must agree on the
   construction contract.
5. An enum with one uninhabited variant does not acquire a value of that variant; review
   RFC-0078's uninhabited-variant and single-inhabited-variant coercion rules.

## 4. Interactions and staging

- **RFC-0208 / RFC-0254:** one general field-row binder and universal ordinary extraction;
  distinguish the known fields of an abstract `T` from its eventual concrete row. The
  enum empty-row rule does not authorize treating an unknown `T` as a concrete empty row.
- **RFC-0243 / RFC-0253:** public structural fields, exact bounds, brand and generic
  projections need reconciliation with any variant type. This RFC does not change the
  agreed policy for whole enum values.
- **RFC-0100 / RFC-0114:** variant-preserving constructors and privileged representation
  construction need joint design; the enum-wide unrestricted-result candidate is not
  assumed sufficient.
- **RFC-0214 / RFC-0217:** residual aspect behavior, row-based nominal implementations
  and field-wise derived `Clone` are separately deferred. Variant types do not settle
  whether narrowing can gain an aspect.
- **RFC-0206 / RFC-0071:** whether `Copy` or `Clone` may differ between a variant and
  its enclosing enum is deferred to the ownership and Copy/Clone work (language owner,
  2026-11-26). RFC-0071 records the question; this RFC grants neither capability.
- **RFC-0150 / RFC-0122 / RFC-0241:** RFC-0150 owns partial moves and residual types of
  variants; place and borrow safety, origins, mutation and control-flow joins need a joint
  soundness review. Until those rules are integrated, RFC-0210 does not authorize variant
  partial-move behavior.
- **RFC-0071 / RFC-0147 / RFC-0148:** destructor behavior for a variant-typed value,
  including any enclosing-enum `Drop` impl and its interaction with widening, is deferred
  to the `Drop` and narrowed-destructor work (language owner, 2026-11-26). This RFC does
  not decide dispatch or introduce an assumption that cleanup is skipped or inherited.
- **RFC-0174 / RFC-0238:** generic variant iteration and derivation are future consumers,
  not prerequisites for deciding basic variant identity or a license to reinterpret `..`.

## Open questions

1. A variant type retains its enclosing enum declaration, variant identity and all enum
   arguments, including for unit variants (language owner, 2026-11-26). Its spelling and
   kind, and the treatment of uninhabited variants, `Option` and `Result`, need review.
2. Widening a variant value to its enclosing enum is implicit (language owner,
   2026-11-26). Specify its expression positions and interaction with inference and
   coercions. Shared-reference widening is allowed and unrestricted mutable-reference
   widening rejected (language owner, 2026-11-26); origin and reborrow rules need review.
   Matching narrows usable whole-value bindings and borrowed references in a
   successful arm; a live narrowed borrow prevents variant replacement (language owner,
   2026-11-26). Specify joins, mutations, moves and `Drop` and verify their soundness.
3. What exactly is the constructor's result and failure interface, and how does its own
   privileged minting preserve the variant? Can a custom constructor alter parameters?
4. A variant type exposes its present public payload fields as its ordinary row (language
   owner, 2026-11-26). Reconcile exact bounds, private fields, partial moves, structural
   matching and aspect coherence with RFCs 0243 and 0254. Independent variant impls are
   the working direction; verify narrowing, dispatch and coherence against RFC-0214.
5. How are variant inventories represented and named? Are they a distinct kind or an
   application of general rows, and how are variants distinguished from fields? What
   binder and extraction syntax avoids conflict with `..T`?
6. How do visibility, separate compilation, exhaustive matching and adding variants or
   fields interact with exposed variant types and inventories?
7. Which pieces can be integrated and implemented independently of comptime iteration,
   variant-wise derive, opaque views and the full borrow checker?

## Decision

**Outcome:** *(pending)*
