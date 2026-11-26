---
id: rfc-0100
title: "Nominal Construction Through a Unified Type and Value Namespace"
date: '2026-11-11'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/807'
---

> **Status — under review (consolidated 2026-11-11).** Review tracked by metel-core#807.
> Revised after the language-owner discussion: explicit `new T(...)` and inferred
> `.(...)` replace the earlier constructor-binding proposal. Prototype evidence
> and interaction review remain required before acceptance.

> **Revised (2026-11-26, language owner).** `new`/`.(...)` are withdrawn. Construction returns to plain
> call syntax, `Struct(args)`, fixing the original argument-dependent lookup bug by removing its
> precondition instead of adding a visual marker: a module's type and value declarations now share one
> namespace, so a struct and a function can never carry the same name in the first place, and `Struct(args)`
> is never ambiguous because there is only ever one thing `Struct` can mean. The inferred, expected-type
> compact form (previously `.(...)`) is withdrawn from this proposal and deferred to its own future RFC —
> it is an independent question once the namespace collision is gone structurally rather than syntactically.

## Design history

RFC-0100 originally proposed `Type(args)` and retired nominal brace literals. That
design was accepted, integrated and implemented in v0.16.0 development, then reopened
after implementation exposed an argument-dependent collision between same-named types
and functions. The constructor-call implementation and its documentation were reverted
by metel-core#1945 (core PR #1946; docs PR #608).

A first revision reserved constructors in the value namespace: it removed the
argument-dependent lookup, but left construction visually identical to an ordinary call,
and the language owner separately found bare `Empty` unclear. A second revision
(consolidating RFC-0226) introduced explicit `new T(...)` and an inferred, expected-type
`.(...)` form, both visually distinct from an ordinary call. Prototype evidence and
interaction review remained outstanding when that revision was itself revisited.

**This revision returns to plain call syntax**, `Struct(args)`, the original spelling —
but reaches it by a different route than the first revision did. Where the first revision
moved constructors into the value namespace while leaving the type namespace as a
separate, coexisting thing (so construction looked exactly like a call because, in a
sense, it now partly was one), this revision removes the *coexistence* itself: a
module's struct/enum declarations and its `fun`/`let` declarations share one namespace, so
declaring a type and a value under the same name is an ordinary redeclaration error, the
same way two functions of the same name already are. `Struct(args)` is never ambiguous
because there is structurally only ever one `Struct` to call. The inferred compact form is
withdrawn from this proposal; whether and how to reintroduce it is a separate, later
question, addressed once a real namespace collision is no longer there to interact with it.

## Summary

Nominal construction is an ordinary call:

```metel
let a := Point(x = 1, y = 2);       // construction: Point is a type
let row := .{ .x = 1, .y = 2 };     // always an anonymous record, never nominal
```

`Struct(args)` resolves `Struct` by ordinary name lookup. Because the type and value
namespaces are unified (section 1), that lookup can never land on "a type or a function,
whichever the arguments suggest" — at most one declaration named `Struct` can exist in
scope at all, so the call unambiguously means whichever one it is. If it is a struct or
enum, the call constructs it; if it is a function, the call invokes it; nothing about the
call's own syntax changes between the two cases, and nothing needs to.

Whole-row construction stays explicit: `Point(..row)` supplies a record binding, and
`Point(..{ .x = 1, .y = 2 })` supplies a literal row. Never reinterpret an ordinary
record-valued argument as the whole parameter row.

Bare zero-field struct/named-record construction is retired as its own special case —
`Empty()` is simply a call to whatever `Empty` is, and under namespace unification that is
never ambiguous (section 6).

**The inferred, expected-type compact form is deferred, not part of this proposal.**
`new` is not reserved. This RFC remains under review. Release assignment lives in
metel-core#807's milestone. The normative spec and interpreter remain unchanged until
integration and implementation through the project lifecycle.

## Motivation and current behaviour

RFC-0100 made construction a call while allowing a type and a function of one
name. The implementation chose between them by argument binding:

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }
fun main() {
    println(Ticket(value = 1).value);
    println(Ticket(input = 1));
    println(Ticket(1));
}
```

The workspace's existing `metel-core/target/debug/metel` printed `1`, `101`,
`101` on 2026-11-11. The inspected
`pipeline/type_checking/construction/expressions.rs::function_takes_the_call`
used argument binding to select between the function and constructor. This is
local-binary evidence, not a release-tag experiment.

**The program above is precisely what this revision makes impossible to write.** Under a
unified namespace, declaring `struct Ticket` and `fun Ticket` in the same module is an
ordinary name collision, caught at the two declarations themselves. There is
therefore no case left in which `Ticket(args)`'s meaning could depend on what the
arguments look like: by the time any call is type-checked, `Ticket` already resolved,
unambiguously, to one declaration. The bug is removed by making its precondition
unrepresentable, not by asking a reader or a type-checker to disambiguate it after the
fact. The `new`/`.(...)` revision instead added a visual marker so a reader (and the
compiler) could tell `Struct(args)` apart from an ordinary call. That marker is no longer
needed for soundness once the two can never actually collide — whether it is still wanted
for readability on its own merits is a fair question, taken up in Alternatives.

## 1. Unified type and value namespace

**A module's nominal type declarations (`struct`, `enum`) and its ordinary value
declarations (`fun`, `let`/`var` at module scope) share one namespace.** Declaring two
of these under the same name in the same scope — two structs, two functions, a struct and
a function, an enum and a `let` — is an ordinary redeclaration error.

**This is new resolver work, not a free reuse of an existing check (checked against
RFC-0030/RFC-0031, both implemented).** The bug example above is itself the proof: it
already compiles one `struct Ticket` and one `fun Ticket` in the same file today, with no
redeclaration error at all — only the argument-dependent dispatch heuristic this revision
removes. That is not an oversight in the current implementation; it follows directly from
how the two are tracked. `ModuleExports` keeps `pub_schemes: HashMap<String, Scheme>`
(values) and `pub_types: HashMap<String, TypeDef>` (types) as two separate maps, so a
module already exports a type and a value of the same name with no conflict. Import
conflict detection (`ScopedEnv = HashMap<String, Binding>`, error `T0011`) is seeded only
from `pub_schemes`; `pub_types` never feeds the same table, so type lookups go through an
entirely separate path that the existing import-conflict check does not see at all. Both
gaps — local, same-module declarations (the primary one, and what the bug actually was)
and cross-module imports (secondary, same shape) — need a genuinely new check that looks
across `pub_types` and `pub_schemes` (and their local, pre-export counterparts), not an
extension of `T0011` as currently scoped. See open question 1 for what shape that check
should take.

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }   // error (new check): `Ticket` is already
                                                  // declared as a struct
```

- **Imports need the same new cross-kind check, not a reuse of `T0011` as it stands.**
  Importing a type named `Ticket` from one module and a function named `Ticket` from
  another into the same scope must collide the same way the local case does — but today's
  `T0011` detection is seeded only from `pub_schemes` (values), so a cross-kind import
  collision is invisible to it as currently implemented (see above; open question 1 lays
  out the two credible ways to close this, and recommends one).
- **Scope, not program-wide, governs the collision.** Two different modules may each have
  their own `Ticket` — one a struct, one a function — exactly as two modules may each
  declare their own function named `f` today; the namespace is unified per scope, not
  flattened across the whole program.
- **What does *not* unify.** Enum variant names stay in their existing, separately-scoped
  namespace (RFC-0107/RFC-0111): unifying module-level types and values says nothing about
  `Option::Some` or its unqualified exposure. Aspect names, generic type parameters, and
  type aliases are not addressed by this section — whether any of them should also join
  the unified namespace is open question 2, not assumed here.
- **What this buys, beyond fixing the lookup bug:** one namespace per scope is the more
  common model outside Rust/Haskell-lineage languages, and removes a whole class of
  "is this shadowing a type or a function" question before it can be asked. What it
  costs: a type and a function can no longer deliberately share a name (for example, a
  type and a conventionally-named smart-constructor function) — a pattern this language's
  own construction syntax already makes unnecessary, since `Struct(args)` already *is*
  the smart constructor's call.

## 2. Construction

`Struct(args)` is a call that resolves `Struct` by ordinary name lookup; because of
section 1, the result is either unambiguously a type (construction) or unambiguously a
value (an ordinary call) — never a choice made from the arguments. Generic construction
uses the existing turbofish spelling, `Pair::<i64>(1, 2)`. Aliases and module
qualification work: `TicketAlias(value = 1)` and `model::Ticket(value = 1)`. Inside an
impl, `Self(...)` identifies its own type.

Construction targets structs and named records. It specifies neither heap allocation
nor a fresh runtime identity; storage and ownership keep their rules. It does not mean
raw field initialisation: it invokes the canonical construction operation, including
validation when RFC-0114 supplies it.

```metel
struct Ticket { value: i64 }
let a := Ticket(value = 1);   // construction: `Ticket` names a struct
```

A type alias exposes a construction target, not a new constructor value binding. No
`new` keyword is reserved by this revision.

## 3. Deferred: an inferred, expected-type compact form

The earlier `.(...)` proposal — construct the single nominal type an expected type
supplies, without naming it — is withdrawn from this RFC, not rejected. It was motivated
by two different things at once: giving construction a compact spelling, and giving it a
spelling visually distinct from an ordinary call so a reader (and, before this revision,
the type-checker) could tell the two apart. The second motivation is gone now that
section 1 removes the ambiguity it was disambiguating. The first — whether a compact,
inferred-target construction form is worth having on its own merits, independent of any
collision concern — is a real, separate question, left for its own future RFC once this
one settles. Nothing here assumes an answer either way; `.(...)`'s syntax is not reserved
by this proposal.

## 4. Positional, keyword and record-valued arguments

Construction retains RFC-0223's argument rules: positional arguments bind in field
declaration order and precede keyword arguments; keywords bind by name; every parameter
is supplied once. Arguments evaluate left to right as written. No new defaults, partial
application or constructor overloading is added.

```metel
let a := Point(10, 20);
let b := Point(y = 20, x = 10);
```

An anonymous record passed normally is one argument, even if its row happens to
match some construction target:

```metel
struct Sample { position: .{ .x: i64, .y: i64 }, weight: i64 }
let a := Sample(.{ .x = 10, .y = 20 }, 5);
```

The record initialises `position`; it is not unpacked into the parameter list.
There is no fallback that retries ordinary positional binding as whole-row binding.

## 5. Whole-row construction: `..r` and `..{ ... }`

A whole-row operand supplies exactly the construction parameter row, with the
same labels and corresponding field types under ordinary checking and generic
inference. It supplies every field, no extra fields, and satisfies the same
visibility requirements as explicit field arguments. Anonymous record field order
does not determine the binding: row labels do.

```metel
let fields := .{ .x = 10, .y = 20 };
let a := Point(..fields);
let c := Point(..{ .x = 10, .y = 20 });
```

`..r` accepts a plain record binding, as in RFC-0100's existing construction-spread
rule. `..{ ... }` is a dedicated whole-row literal argument with the same value
entries as an anonymous record literal (dotted labels, `=`, puns and existing
record-spread/update rules). It is not `..` followed by the `.{` opener.
The contiguous `..{` notation is used instead of `.. .{ ... }`; the latter is not
an alternative spelling. In generic type-argument position `..{ .x: i64 }` keeps
RFC-0180's literal-row meaning; constructor argument position uses value entries.

A whole-row operand must be the sole argument. Reject multiple whole-row operands
and mixtures such as `Point(..fields, x = 5)`. To replace a field, explicitly
build an updated record using the existing record-update rules first, or use a
whole-row literal containing the update:

```metel
let p := Point(..{ ..fields, .x = 5 });
```

The literal's own spread/update semantics are RFC-0191's, not a new constructor
argument-merging mechanism. Evaluate the binding operand or literal once, then
perform the same canonical construction as positional/keyword arguments. No
record-to-nominal coercion is added outside these explicitly marked expressions.

```metel
struct Wrapper { position: .{ .x: i64, .y: i64 } }
Wrapper(fields)                 // position receives one record value
Wrapper(..fields)               // error: the whole row needs .position
Wrapper(..{ .position = fields }) // accepted
```

Arbitrary expression operands after `..` (for example `..make_fields()`) are a
future extension, not included here. A dedicated literal is included in this
proposal; it deliberately extends plain-binding-only operands.

## 6. Empty types, variants and failure

Zero-field structs and named records require an explicit construction call, which is
simply an ordinary call now that no bare-shorthand special case exists:

```metel
struct Empty {}
let a := Empty();
let c := Empty(..{});
```

Under the unified namespace, `Empty` names at most one declaration in scope — the
struct, in this example — so `Empty()` is never ambiguous and needs no implicit-call
special case to make it so. This directly addresses the earlier "bare `Empty` unclear"
objection from a different angle than the `new`/`.(...)` revision did: that revision made
the call visually distinct to resolve the unclarity; this revision removes the thing that
was unclear (whether `Empty` could mean two different declarations) at the point where
`Empty` is declared, not at the point where it is called.

Enum variants retain their existing qualified/unqualified bare and call forms,
unaffected by this proposal (section 1's unification is module-level type/value
declarations, not variant namespacing).

Construction uses the same result handling regardless of how it is spelled: no
implicit unwrap, no caught failure, no bypassed validation. RFC-0114's
`Construct`/fallibility model remains its own design; its current synthesised
infallible scope is not evidence of implemented custom constructor support.

## Interactions and migration

This revision replaces RFC-0100's `new`/`.(...)` consolidation with a return to plain
call syntax, reached through section 1's namespace unification rather than the original,
reverted design's unguarded one. It retains RFC-0100's argument collection and exact-row
contract (sections 4-5), unchanged from the prior revision except for dropping `new`. It
retires RFC-0106's bare shorthand for zero-field structs/named records, now subsumed by
section 6. RFC-0111's enum-variant rules remain. RFC-0225 owns anonymous record syntax;
its literals stay structural. RFC-0114 owns canonical validation, fallibility and
privileged minting.

No compiler behaviour is changed merely by revising this RFC. Before any grammar or
namespace-resolution change ships, the existing std library and test corpus need an
audit for any current type/value name pairs that would become a redeclaration error
under section 1 — this is new migration work section 1 introduces that the prior
`new`/`.(...)` revision did not need, since that revision kept both namespaces separate.
Implement prototypes first; acceptance and spec integration precede product
implementation.

## Alternatives and decision

**Three positions have now been explored for the same underlying problem**, not two:
(1) the original, reverted design — plain call syntax, separate namespaces, resolved by
argument-shape heuristic, unsound; (2) constructors moved into the value namespace —
removes the heuristic, keeps namespaces conceptually separate, but leaves construction
visually identical to a call, which the language owner found to read poorly, compounded
by bare `Empty` being unclear; (3) `new T(...)` / `.(...)` — visually distinct forms,
namespaces stay separate, soundness and readability both addressed by new syntax.
**This revision is a fourth position**: plain call syntax like (1), but sound like (2)
and (3) — reached by removing the *coexistence* that made (1) unsound, rather than by
moving constructors into the value namespace as (2) did, or by adding a visual marker as
(3) did. It is not a return to (1): the collision (1) suffered from cannot occur here,
because it is caught at the two declarations, before any call is ever written.

Position (2)'s readability objection — construction looks exactly like a call — applies
here too, by construction (so to speak): `Struct(args)` and `f(args)` remain visually
identical. **Whether that is still a problem is a genuinely open question under this
revision**, since the reason it mattered for (2) — a reader (and the compiler) needing
to tell two coexisting meanings apart — no longer holds. Readers who want a syntactic
construction marker get it, if wanted, from a future RFC addressing section 3's deferred
compact form, not as a precondition for soundness.

For record operands, implicit row unpacking based on argument shape is rejected:
it would give a normal record-valued positional argument two possible meanings.
Use `..r` or `..{ ... }` to state whole-row intent explicitly. General implicit
anonymous-record-to-nominal conversion is also outside this proposal.

**Current design direction (2026-11-26):** plain call-syntax construction, a unified
type/value namespace making that syntax sound, ordinary positional/keyword rules,
explicit whole-row operands with `..{ ... }` literal notation, no implicit construction
from bare names, and the inferred compact form deferred to its own future RFC.

**Remaining acceptance work:** a resolver prototype for the new cross-kind collision
check (section 1, open question 1 recommends the additive shape, not a `pub_schemes`/
`pub_types` merge); a corpus-wide audit for existing type/value name pairs that would
newly collide; a decision on whether aspects, type aliases or generic parameters also
join the unified namespace (open question 2); exact-row, visibility and
single-evaluation fixtures carried over from the prior revision. These are evidence
requirements, not completed checks.

## Open questions

1. **Resolved — it does not already generalize, checked against RFC-0030 and RFC-0031
   (both implemented).** `ModuleExports` tracks `pub_schemes` (values) and `pub_types`
   (types) as two separate maps, so a module already exports a type and a value under one
   name with no conflict today. The import-conflict table (`ScopedEnv`, error `T0011`) is
   seeded only from `pub_schemes` — `pub_types` never reaches it, so a type/value import
   collision is currently invisible to it, the same way a type/value *local* declaration
   collision is invisible to whatever checks local redeclarations today (the bug example
   in Motivation is direct proof: it already compiles both declarations in one file with
   no error). Unification needs a genuinely new check, at both the local-declaration level
   and the import level, comparing names across `pub_types` and `pub_schemes` (and their
   pre-export, module-local equivalents) rather than within either alone.

   Two credible ways to build it:
   - **(a) Merge `pub_schemes` and `pub_types` into one map** (e.g. an `Item` enum wrapping
     either a `Scheme` or a `TypeDef`). Directly expresses "one namespace" in the data
     structure itself, but is invasive: it touches RFC-0030/0031's existing, already-
     implemented separation, and every consumer of either map independently.
   - **(b) Keep the two maps exactly as they are, and add one new, additive check**
     — at each module's own declaration-collection pass, do its local type-declaration
     names and local value-declaration names overlap; at each importing scope, do the
     type names and value names being brought in (combined with local names at that
     scope) overlap. Reject any overlap. This changes nothing about how `pub_schemes`
     and `pub_types` are populated or consumed elsewhere; it only adds a pass that reads
     both and compares their key sets.

   **Recommendation: (b).** It gets the same language-level guarantee without touching
   machinery RFC-0030/0031 already ship and presumably already have fixture coverage for;
   (a) would need re-verifying all of that coverage against a changed representation for
   no additional guarantee. Whether the new check's error reuses `T0011` or gets its own
   code is an implementation detail for whichever ADR eventually specifies it (PROCESS.md's
   convention), not something this RFC needs to pin down.
2. **Does unification extend beyond struct/enum vs. fun/let?** Aspect names, type
   aliases and generic type parameters are explicitly not addressed here. Each is a
   separate decision, not an implied consequence of this one.
3. **Is the readability objection from position (2) still live, now that its original
   cause (coexistence) is gone?** If reviewers still want a visual construction marker
   on readability grounds alone, that is an argument for revisiting position (3) instead
   of this one, not a soundness objection to this revision.
4. **What does the corpus-wide audit actually find?** Until it runs, the real migration
   cost of section 1 (how many existing type/value name collisions would need renaming)
   is unknown; this could turn out to be a non-event or a real rename campaign.
5. **Interaction with aspect-object dispatch and trait-object-shaped calls**, if any
   exist, needs checking against unification — not investigated here.

**Lifecycle outcome:** Under review, tracked by metel-core#807. No acceptance, spec
integration or implementation transition is claimed.
