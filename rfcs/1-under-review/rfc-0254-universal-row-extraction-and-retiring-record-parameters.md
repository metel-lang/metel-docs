---
id: rfc-0254
title: "Universal Row Extraction and Retiring Record Parameters"
date: '2026-11-25'
status: under-review
updated: '2026-11-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/2195'
---

> **Status — under review (2026-11-25).** Scheduled for row visibility and named records design review

## Summary

Every type has an extractable structural row. `..T` extracts that row from an ordinary
type parameter, without requiring a `record` parameter kind or an empty structural bound.
The `record` generic parameter kind is retired. A structural bound states a shape
requirement, and RFC-0208's `<..R>` binds a row rather than a type.

```metel
fun inspect<T>(value: &T) where ..T: Display { … } // proposed field-wise bound
fun read_id<T: .{ .id: i32, .. }>(value: &T) -> i32 { value.id }
fun use_row<..R>(value: &.{ R }) where R: Display { … }
```

The language owner agreed to universal extraction and retiring record parameters.
References expose their referents’ public rows. An abstract type's row is symbolic,
not empty (language owner, 2026-11-28; Cluster reconciliation below).

## Motivation

RFC-0243 retires the named `record` declaration kind and makes public fields available
for structural matching. RFC-0208 separates a row binder from a type parameter. The
remaining `<record T>` kind combines an ordinary type identity with permission to use
its row. If extraction is defined for every type, ordinary `<T>` can carry the identity
and `..T` can extract its row. Structural bounds are needed when code requires fields,
not simply to establish that an extractable row exists.

## 1. Extracted row

For ordinary structural matching and extraction, the row is module-independent:

| Type | Extracted row |
|---|---|
| Struct | Its public fields, after generic substitution |
| Branded residual | Its present public fields |
| Anonymous record or tuple | Its present fields; tuples use numeric labels |
| Primitive | Empty |
| Enclosing enum | Empty ordinary field row; variant inventories and variant types are under review (RFC-0210) |
| Variant type (proposed RFC-0210) | Its present public payload fields |
| Reference (`&T` or `&var T`) | The referent’s public structural row, through all reference layers |
| Array `[T; N]` or slice `[T]` | Empty; elements are indexed, not labeled fields |
| Function type (`\|A, B\| -> R`, `dyn Callable<..>`) | Empty; never the parameter row (see below) |
| `Never` | Empty, vacuously: no value exists to have fields |
| Aspect object (`dyn A`) | Empty; the underlying type is erased, nothing to read statically |
| Type parameter or associated type not yet instantiated | Symbolic: an opaque row whose known fields are exactly those its structural bounds state; never equal to any concrete row, including the empty one (Cluster reconciliation below) |

**The classification is total, by one governing principle (language owner, 2026-11-26), not a list of unrelated
special cases:** a type's extracted row is the maximal set of (label, type) pairs *statically* known, at the point
of extraction, to be selectable through a value by ordinary field access, including reference
auto-dereference. Extraction does not look through erasure (a `dyn` object),
homogeneous indexing (an array or slice), a call signature (a function type), or an
as-yet-undetermined instantiation (a type parameter or associated type) beyond what an explicit
structural bound states; for those the row is symbolic, with the bound's fields as its only known part. Every row above, including the categories already agreed, is this one rule applied. No
category is excluded from universal extraction — every type has *an* answer, even where that answer is uniformly
Empty or, for an abstract type, symbolic.

Field-row extraction and structural shape bounds follow the same rule for shared and
exclusive references (language owner, 2026-11-27). For every `T`, `..&T` and
`..&var T` denote the same row as `..T`, including while that row is symbolic.
This applies recursively to nested references and preserves the referent’s field
types and visibility. An exact `.{ .x: i32, .y: i32 }` bound accepts both a
`Point` with exactly those public fields and `&Point`, while `T: .{}`
accepts `&i32` and rejects `&Point`. A bound preserves the actual type
argument, its reference layers, and its access restrictions. Value-level spread
through those layers follows [RFC-0255](rfc-0255-row-sections-shared-extraction-and-contextual-field-assembly.md).

**A named risk, not an omission: function types and RFC-0232.** RFC-0232 (same release, "Function types" stage)
represents a function's call signature as `dyn Callable<ROW, R>` — a row already sits inside a function type's own
representation. If `..F` extracted *that* row, it would conflate "this function's call signature" with "this
type's own data fields" under one operation, exactly the accidental-conformance risk the row-visibility cluster
(RFC-0243 E4) has been working to keep out. Extraction stays out of it on purpose: a function's parameter row is
reached, if at all, through whatever RFC-0232's own `Callable` aspect exposes, never through `..F`.

**Adversarial check: "module-independent" means always public-only, including from inside the declaring
module.** A natural but wrong intuition is that extraction might see *more* fields when the generic code using
it happens to be written inside the type's own module, where private fields are otherwise freely accessible. It
does not — there is exactly one extracted row per type, computed the same way everywhere:

```metel
struct Account { pub id: i64, secret_key: [u8; 32] }

// written and called from WITHIN Account's own module
fun log_fields<T>(x: &T) where ..T: Display { … }
log_fields(&some_account);   // ..Account is { .id: i64 } here too, never { .id, .secret_key }
```

Ordinary field access (`self.secret_key`) stays fully available inside the module, unaffected — that is a
different operation from extraction. Extraction is the one view that never varies by caller module, by design,
precisely so that generic code built on `..T` means the same thing wherever it is written or called; a
module-dependent extraction would make a generic function's own meaning depend on who happened to call it, the
opposite of what a module-independent, structural operation is supposed to guarantee.

**What a generic body knows about an abstract type's row** is the bound's row and nothing more — the same
parametricity discipline RFC-0146's lower-bounded row receiver already establishes for a residual (a method
checked against `Self.R` where `R: { fd, .. }` may use only `.fd`, never assuming a specific caller's residual
happens to have more). A type parameter and an associated type are the same case under this rule, not two
different ones: both are "a type not yet concretely known at this point," so both extract a symbolic row whose only
known fields are the ones a bound states. With no bound, nothing is known; that is not the same as knowing the row is
empty (Cluster reconciliation below).

These categories, now exhaustive, replace the earlier "initial categories are agreed direction; other current and
future types need classification" framing — this is that classification. Empty means the row contains no fields,
not that the type is the empty record. `..T` forgets the nominal brand, while `T` retains its identity. Extraction
at a privileged derivation boundary may require a different full-field operation; that deferred design is not
specified here.

`T: .{}` is an exact empty **public** row bound. It can hold for a primitive or a struct
with no public fields, including a struct with private fields. It makes no claim about
private state or interchangeability with `.{}`. `T: .{ .. }` imposes no field requirement
and is redundant if extraction is universal. `T: .{ .id: i32, .. }` requires an accessible
public `id` and permits other public fields; the exact form without `..` permits no
other public fields. Matching a bound preserves `T` and does not convert its value.

## 2. Parameters and bounds

An ordinary `T` can occur as a type and `..T` denotes its extracted row. A row-only
parameter `R` declared by `<..R>` denotes fields directly and is used as `R` in row
positions, as proposed by RFC-0208. Field-wise bounds over a *concrete* empty row hold
vacuously (a primitive, an array, an enum's ordinary row); over a symbolic row nothing holds
vacuously, and a field-wise bound must be stated. Either way `where ..T: A` alone does not assert `T: A`. A function using only such a bound
must not invoke an `A` method on `T` itself without a separate `T: A` bound. A negative
field-wise bound (`where ..T: !A`) is vacuously true over an empty row by the same logic.

**Resolved (language owner, 2026-11-26): this vacuous-truth rule is uniform across every aspect, including
ownership and auto aspects — with one named implementation risk, not a language-level special case.** The rule
above already rules out the general danger (a field-wise bound can never assert the whole-type bound) for Send,
Sync, Copy and Linear alike; none of them can be satisfied merely because `where ..T: A` holds vacuously. The real
risk is narrower and belongs to whoever eventually specifies `auto`'s deferred structural rule (RFC-0096, RFC-0212
section 2): an **auto** aspect's grant must be computed from a type's *full* field set, public and private alike,
inspected at the type's own definition — the same way `Copy`'s and `Linear`'s structural checks already work
(RFC-0206 rule 3, RFC-0212 sections 1-2) — never by reusing `..T`'s public-only extracted row. Reusing it would
make the auto-grant itself unsound: a type with a non-`Send` private field could vacuously satisfy a
`Send`-shaped check restricted to its (possibly empty) public row, and be silently granted `Send` it does not
actually have. `Copy`, `Clone` and `Linear` do not share this risk, because their structural checks already
happen at the type's own declaration with full field access by construction; the risk is specific to `auto`'s
no-entry, module-independent grant mechanism, exactly where a public/private mismatch could silently creep in if
implemented by reusing universal extraction instead of a dedicated full-field check. This is a constraint for
`auto`'s still-deferred structural rule to honor, not a bug in anything currently specified.

A bound and a row literal use the syntax of RFC-0208. The `record T` binder is removed
as a distinct generic kind; the declaration kind's retirement is RFC-0243. A plain type
parameter's ordinary well-formedness and kind rules still apply. Type-level extraction
computes a row without evaluating a dereference, moving fields, creating references,
converting ownership, or granting a nominal aspect.

**Resolved (language owner, 2026-11-26), the remaining half of open question 5: the four forms never actually
compete for one grammatical slot, so no new disambiguation rule is needed beyond position and one-token
lookahead.** `<..R>` only ever appears inside a generic parameter list, at a binder-*declaration* site — never
inside an ordinary type or bound, so it cannot be confused with the other three. Variadic spread (a value-level
`..pack`, e.g. `new T(..fields)`) only ever appears in expression/argument position, never in type position, so
it cannot be confused with any of the three type-level forms either. That leaves exactly one real decision, within
type/bound position alone, between `..T` (extraction, naming an existing type) and `..{ .name: i64 }` (a row
literal, introducing a field list): a single token of lookahead after `..` settles it — `{` means a literal,
anything else means extraction of the identifier that follows. RFC-0208's own open question 5 ("tuple packs")
already resolved the one case that could have reopened this: numeric-row packs (RFC-0151) use the same row kind
as everything else, not a separate pack-spread form in type position, so there is no fifth form left to
disambiguate against.

**Resolved (language owner, 2026-11-26).** Most of this collapses to one fact: `..T` is a *derived, one-way
projection* of an already-determined `T`, computed after the fact from the classification table (section 1) — it
never participates in type inference, impl matching or coherence as a *source*, only as a *consumer* of existing,
unchanged machinery.

- **Type inference is unaffected.** `T` is always inferred by the usual means (arguments, return-type context,
  explicit turbofish); `..T` is computed from `T` only once `T` is already known. There is nothing new to infer:
  many different types can share the same extracted row (most share Empty), so inference could never run
  backward from a row to a type, and this RFC does not attempt to.
- **Coherence and the orphan rule are untouched.** Row-conditional impl matching (RFC-0121) and who may write
  such an impl (RFC-0060) are governed entirely by those RFCs and by RFC-0243's decided opt-in rule, neither of
  which this RFC changes. Extraction supplies a row *value* for a bound to check against an aspect
  (`where ..T: A`); it is never itself the thing an impl is matched against. A primitive's or `Never`'s empty
  extracted row does not make it eligible for row-conditional impl matching — that eligibility was never keyed
  on the extracted row to begin with; only a record, or a nominal type that has explicitly opted in (RFC-0202
  section 6, RFC-0250 section 0), is ever a candidate. Both opt-in grants are deferred from v0.17.0
  (RFC-0243, 2026-11-28), so in v0.17.0 no nominal type is a candidate.
- **Negative bounds** (`T: !A`) are about `T` itself, unaffected by extraction directly; the field-wise case is
  covered above.
- **Field-wise aspect constraints** (`where ..R: A`, RFC-0123) keep their existing, already-implemented rule;
  this RFC only widens which types may supply `R` via `..T` — from `record T` only to every `T`.
- **The one real consequence is overload resolution at existing call sites, already named in section 3's
  migration text below, not a new rule to invent.** Because `..T` now type-checks for every `T` rather than being
  a kind error for a non-`record` type, a call site that used to have exactly one eligible overload can gain a
  second one after migration (one candidate's `..T`-involving bound now also type-checks for an argument it
  previously didn't). This needs no new disambiguation rule: existing overload resolution already picks the most
  specific match or reports ambiguity, and a newly-ambiguous call site surfaces as a loud compile error, not a
  silent behavior change — consistent with migration being "not necessarily behavior-preserving," below, rather
  than silently unsound.

## 3. Migration

A candidate migration changes `<record T>` to `<T>` when `T` denotes a type, and its
existing row uses to `..T`. A parameter used only as a row may instead become `<..R>`
with bare `R` uses under RFC-0208. Existing code that depended on the old eligibility
restriction can accept more instantiations; migration is not necessarily behavior-preserving.
Audit constraints, overloads, explicit arguments, method resolution and public generic
interfaces before choosing a mechanical rewrite. Row-based implementations for nominal
types remain deferred, so a new row bound alone does not grant them an aspect.

```metel
// Before (current syntax)
fun count<record T>(value: &T) -> i64 { … }
// Candidate after
fun count<T>(value: &T) -> i64 { … }
```

**Resolved (language owner, 2026-11-26): no staged migration and no compatibility predicate.** Metel has no
active external users yet, so there is no existing API surface this RFC must keep accepting under the old
binder. `<record T>` retires outright: every use in std and the test suite is rewritten directly, as above, and
`<record T>` left in source after integration is a parse/compile error naming the replacement spelling (`<T>`
where `T` is used as a type, `<..R>` where it is used only as a row) — a clean cutover, not a deprecation window.
No deprecated spelling, no transition period, no tooling beyond the mechanical rewrite itself. This also answers
open question 2 directly: there is no "old eligibility" to preserve for any API, because there is no API this
RFC is obligated to keep compiling.

**Resolved (language owner, 2026-11-26): open question 7, split in two.** Its two clauses belong to different
RFCs. This RFC's own fixture need, now that there is no staged migration, is small: ordinary fixtures for the
new syntax exercising section 1's classification and section 2a's findings, plus one negative fixture confirming
`<record T>` is a compile error naming its replacement. "The deliberate loss of automatic nominal row
implementations after record retirement" is RFC-0243's concern, not this RFC's — RFC-0243 retires the `record`
*declaration* kind (a different thing from this RFC's `record T` *parameter* kind) and already has its own
migration story and an eventual bridge mechanism (RFC-0202 section 6, RFC-0250 section 0, both deferred from
v0.17.0); this RFC does not need to fixture
that loss itself.

## 3a. Opacity, aliases, separate compilation and private representation

**Resolved (language owner, 2026-11-26).** Each of the four named interactions turns out to need no new rule,
because extraction's two defining properties — public-only, and module-independent (section 1) — already supply
the answer:

- **Generic aliases.** A plain, transparent alias (RFC-0160) is nominally and structurally the same type it
  names, so `..Alias<T>` extracts exactly what `..T` does — nothing alias-specific to add. For an alias to a
  *residual* that retains a private field in its own row (RFC-0253's subject), extraction still only ever sees
  public fields, by section 1's own rule, regardless of what the alias's definition happens to name — the alias
  being legal to declare with a private field in it (RFC-0253's finding: declaration and access are different
  operations) has no bearing here, because extraction was already excluding private fields before any alias
  entered the picture. There is no way to "leak" a field through an alias that extraction wasn't already going
  to exclude.
- **Separate compilation.** Extraction is defined as module-independent (section 1): its result depends only on
  a type's own declaration, never on which module or crate is doing the extracting. A downstream crate computing
  `..T` for an upstream type gets the same answer the upstream crate itself would. This introduces no new
  separate-compilation hazard beyond the ordinary one that already exists for public-field visibility generally
  (adding or removing a `pub` field is already a breaking API change, with or without this RFC).
- **Private representation changes.** A type's author can freely add, remove, rename or retype *private* fields
  without breaking any external `..T`-based generic code, precisely because extraction never includes private
  fields in the first place. This is the property public/private visibility is supposed to guarantee, and
  extraction's public-only design upholds it by construction rather than needing a separate rule to protect it.
- **Row remainder inference** (open row tails, `.{ .id: i32, R }`) is not this RFC's own mechanism — it is
  RFC-0208's row algebra (itself not fully settled: RFC-0208 open question 2, row equations). This RFC only
  supplies `..T` as one possible *source* of a row value fed into that algebra; it adds no remainder-inference
  rule of its own, and does not need to, since extraction never participates in row algebra as anything but an
  input (section 2a).

## 4. Interactions

- **RFC-0208 / RFC-0186:** one row kind and bare row use; this RFC replaces the record
  type-parameter eligibility gate, rather than changing the difference between a type
  and its extracted row. Explicit arguments compose with RFC-0192 as `record R`'s do (open
  question 5). Row equations are RFC-0208's own open question 2, outside its shared binder
  slice (metel-core#1789, delivered in the same stage); extraction adds no equation, and a
  symbolic `..T` enters RFC-0208's algebra only as an opaque input.
- **RFC-0243 / RFC-0137:** public and present field selection, residual brands and named
  record retirement. Visibility must not depend on the use-site module or reveal private
  fields through remainders, reflection, diagnostics or inferred public interfaces.
- **RFC-0151 / RFC-0125 / RFC-0247:** tuples are numeric rows; positional operations and
  variadic calls retain their own rules. Universal extraction adds no pack kind.
- **RFC-0210:** enclosing enums initially extract an empty ordinary field row; variant
inventories require a separately defined operation. Proposed variant types expose their
  present public payload fields; construction details remain under review.
- **RFC-0121 / RFC-0060 / RFC-0228:** broader structural eligibility affects generic and
  row-conditional impl domains, coherence, orphan rules and dispatch. Existing active
  anonymous-row blankets must not silently grant aspects to nominal types under the
  deferred nominal-implementation design. Checked (2026-11-28): impl matching never reads
  the extracted row (section 2a), so primitives, references and enums gain no
  row-conditional impl from their extracted rows; only anonymous records are candidates
  in v0.17.0 (RFC-0243).
- **RFC-0214 / RFC-0217:** nominal row implementations and residual aspect behavior stay open (RFC-0209, their
  own basis, is superseded with no successor yet); extraction and a vacuous field-wise bound do not settle them
  either way.
- **RFC-0232** (same release, "Function types" stage): represents a callable's parameter row as part of `dyn
  Callable<ROW, R>`. Extraction deliberately never reaches it (section 1) — the two row concepts, a type's own
  fields and a callable's call signature, stay disjoint through this operation.
- **RFC-0253:** generic nominal residual projections retain their instantiated brand and may include row-kind
  arguments. Privacy and substitution are settled (section 3a) by reusing RFC-0253's own adversarial-pass
  finding directly: declaring an alias that retains a private field is legal wherever that field is visible;
  accessing it — through extraction or otherwise — is what ordinary visibility rejects.
- **References and ownership:** shape bounds and `..T` follow ordinary field
  auto-dereference. Field-wise obligations apply to the selected fields’ types.
  Borrowing, Drop, linearity and whole-type aspect lookup follow their own rules.

## Cluster reconciliation: enum variants and abstract rows

RFC-0210 is now in the same settlement and explores first-class variant types. The
enclosing enum's agreed empty ordinary field row differs from a variant type's public
payload row (language owner, 2026-11-26). The representation of an inventory of variants
remains open in RFC-0210; a generic bound over `..T` must not accidentally be interpreted as a bound over
every variant payload. RFC-0208 supplies field-row binders, not yet a variant-inventory
binder.

**Resolved (language owner, 2026-11-28): an abstract type's extracted row is symbolic, not empty.** For a type
parameter or an associated type `T` whose instantiation is not yet known, `..T` is an opaque row, written here
`ρ(T)`. Its known part is exactly the fields its structural bounds state, at their stated types. No other field
can be selected through it. It is never equal to any concrete row, the empty row included. "No fields are statically
known" is not proof that the eventual concrete row is empty, so the earlier classification (Empty) is withdrawn.

1. **Bounds are stated, never derived from emptiness.** An exact bound (`T: .{}`, `T: .{ .id: i32 }`) or a
   field-wise bound (`where ..T: A`) holds for an abstract `T` only when its own bounds state it or imply it.
   Vacuous truth applies only after substitution, to a concrete empty row.
2. **Resolution inside a generic body.** A requirement that is not provable from `ρ(T)` is unsatisfied. An
   overload or bound check never treats it as satisfied by an assumed empty row, so a body cannot pick a
   candidate that its instantiation would reject.
3. **Substitution.** At an instantiation `T := U`, `ρ(T)` becomes `..U` as computed by section 1's table. The
   caller discharges each stated bound against `..U` at the call site; the generic body is checked once,
   against its declared bounds (RFC-0173), and is not rechecked per instantiation.
4. **Equality.** Two symbolic rows are equal only when they are the same parameter's row. `ρ(T)` never unifies
   with a concrete row or with another parameter's row.
5. **References.** `..&T` and `..&var T` are `ρ(T)` while `T` is abstract (the 2026-11-27 reference rule,
   section 1, applies unchanged).
6. **Separate compilation.** `ρ(T)` appears only in the generic's own checked signature and body. A downstream
   instantiation computes `..U` from `U`'s public declaration, module-independently, so no new hazard arises.

```metel
struct Point { pub id: i32 }
fun only_empty<T: .{}>(x: &T) -> i32 { 0 }

fun g<T>(x: &T) -> i32 { only_empty(x) }        // error: `T: .{}` is not stated; ..T is symbolic, not empty
fun h<T: .{}>(x: &T) -> i32 { only_empty(x) }   // OK: the bound is stated

h(&Point(id = 1));   // error at the call: ..Point is .{ .id: i32 }, not exactly empty
h(&5);               // OK: ..i32 is the concrete empty row
```

Under the withdrawn rule, `g` would have type-checked by assuming `..T = .{}` and then been wrong for
`T = Point`. Enums and primitives are unaffected: their rows are concrete empty rows, not symbolic ones.

## Open questions

1. **Resolved (language owner, 2026-11-26), section 1.** Every type now has a classification, by one governing
   principle rather than a list of special cases; none is excluded from universal extraction (every category
   gets an answer, some uniformly Empty). A generic body knows exactly its type parameter's or associated
   type's stated bound, nothing more — the same parametricity discipline RFC-0146's lower-bounded row receiver
   already uses. The function-type case surfaced a real, same-release collision risk with RFC-0232, now named
   explicitly (section 1, section 4) rather than left to be discovered later.
2. **Resolved (language owner, 2026-11-26), section 3.** No staged migration, no compatibility predicate:
   Metel has no active users yet, so there is no existing API this RFC must keep accepting under the old
   binder. `<record T>` retires outright; left-over uses are a compile error naming the replacement.
3. **Resolved (language owner, 2026-11-26), section 2a.** `..T` is a derived, one-way projection and never a
   source for inference, impl matching or coherence; those stay governed entirely by their own existing rules
   (RFC-0121, RFC-0060, RFC-0123, RFC-0243). The one real consequence is overload resolution at existing call
   sites gaining newly-eligible candidates after migration — already named in section 3, caught loudly by
   existing ambiguity detection, not a silent risk needing a new rule.
4. **Resolved (language owner, 2026-11-26), section 3a.** Each of the four interactions resolves from
   extraction's own two defining properties (public-only, module-independent) rather than needing a new rule:
   aliases can't leak what extraction already excludes; separate compilation sees the same answer everywhere by
   construction; private-representation changes can't break external code that never saw those fields; row
   remainder inference is RFC-0208's own algebra, fed by extraction but not extended by it.
5. **Resolved (language owner, 2026-11-26), sections 2 and 2a.** The explicit-argument half was already settled
   (a `<..R>` turbofish argument composes with RFC-0192 exactly as `record R`'s does, RFC-0208 open question 1).
   The grammar half resolves the same way: the four forms occupy four different grammatical positions (a
   binder-declaration site, an expression/argument site, and within type position, one token of lookahead after
   `..` — `{` or not — separates the remaining two), so none of them actually compete for one slot.
6. **Resolved (language owner, 2026-11-26), section 2.** Yes, uniformly, at the language level — no special
   case for ownership or auto aspects. The real risk is implementation-level and narrower: `auto`'s own
   (still-deferred, RFC-0096) structural grant must use a type's full field set, never `..T`'s public-only row,
   or the grant itself becomes unsound. `Copy`/`Clone`/`Linear` don't share this risk, since their checks already
   happen at the declaration with full field access.
7. **Resolved (language owner, 2026-11-26), section 3, split in two.** This RFC's own need is small: ordinary
   fixtures for the new syntax, plus one negative fixture for `<record T>`'s retirement. "The deliberate loss of
   automatic nominal row implementations" is RFC-0243's concern (a different declaration kind), not this RFC's.

8. **Resolved (language owner, 2026-11-28), Cluster reconciliation.** An abstract type's extracted row is
   symbolic, not empty: its known part is its stated bounds, it is never equal to a concrete row, and bounds
   over it are stated rather than derived. This was the last question blocking acceptance.

## Decision

**Outcome:** *(pending)*
