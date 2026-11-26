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

**This revision explicitly reverses metel-core#1560, a recent, deliberate, already-implemented
language-owner decision — not a green-field choice.** While this RFC's construction syntax was
being reworked, a separate bug (`LIMIT-NAME-RESOLUTION-005`: the symbol table silently shared one
id between unrelated declarations) was fixed on 2026-10-23, and fixing it required settling the
adjacent policy question of whether a type and a value may share a name at all. The decision,
quoted from the issue: *"structs, enums, aspects and type aliases share the type namespace;
functions, `let` and `var` share the value namespace; a type and a value may share a name (`struct
Foo` + `fun Foo` still coexist)."* The follow-up issue (metel-core#1571, closed 2026-10-24) went
further and gave the symbol table a `(module, namespace, name)` key, with type and value as the two
namespace values, specifically so `struct Foo` and `fun Foo` get distinct, independently-trackable
identities — fixing the bug *while preserving* coexistence as policy, pinned by a dedicated fixture.

**Why reversing it is still worth it.** `#1560` settled whether the symbol table could correctly
track two coexisting declarations (yes, once fixed) — a question about identity bookkeeping. It did
not, and from where it stood could not, settle whether *construction via plain call syntax* stays
sound when they coexist, because that is a question about a different layer (call resolution, not
symbol identity), and the concrete evidence that it does not stay sound is this RFC's own reverted
implementation (metel-core#1945/#1946), discovered on essentially the same scenario around the same
time. `#1560`'s fix is not undone by this revision — duplicate-name detection *within* one namespace
(`T0037`) stays exactly as implemented. What this revision reverses is narrower: the one policy
choice `#1560` made *alongside* that fix, once a concrete, costly consequence of that specific
choice is in hand that `#1560` itself had no way to anticipate.

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

**This is a narrower, more surgical change than it might sound, checked directly against the
current implementation history (metel-core#1560, #1571, both closed and merged 2026-10-23/24) —
and it reverses one specific, recent policy choice rather than building unification from
nothing.** `#1560` fixed a silent symbol-identity bug by giving every declaration a
`(module, namespace, name)` key, with type and value as the two namespace values, and
*deliberately* decided that a type and a value may share a `name` as long as their `namespace`
differs — the quoted policy in Design History. `#1571` then made that key real throughout
`ModuleScope` bindings, imports, exports and the reference resolver, which "tries the value
namespace and then the type namespace for a bare name." Duplicate-name detection (`T0037`)
already runs correctly *within* one namespace value; it does not run *across* the two, because
`#1560` explicitly asked it not to.

**Unification is this: stop treating type and value as two namespace values, and make the
duplicate check that already exists for one namespace value cover both.** It does not need a
new parallel structure, a merged map, or a new resolver pass — the namespace dimension is
already a clean, first-class part of the key; this narrows it to a single value (or, equivalently,
makes the existing duplicate check look up a name under *either* namespace instead of only its
own). The bare-name resolver's "value, then type" fallback becomes moot for a name's own
declaration-site check, since at most one declaration can exist per name once unified; whatever
is left of that fallback order for other purposes is a question for whoever implements this, not
settled here.

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }   // error: `Ticket` is already declared as a
                                                  // struct -- the duplicate check `#1560` built
                                                  // for one namespace value now covers both
```

- **Imports need the same narrowing, not a separate mechanism.** Per `#1571`, "an import or
  re-export brings a name in every namespace the source module provides it in." Importing a
  type named `Ticket` from one module and a function named `Ticket` from another into the
  same scope must collide the same way the local case does; since both already go through the
  one namespace-aware import path `#1571` built, this is the same narrowing as the local
  case, not a second thing to design.
- **Scope, not program-wide, governs the collision.** Two different modules may each have
  their own `Ticket` — one a struct, one a function — exactly as two modules may each
  declare their own function named `f` today; the namespace is unified per scope, not
  flattened across the whole program.
- **Aspects and type aliases join automatically, not as a separate decision.** `#1560`'s
  existing policy already groups `struct`, `enum`, `aspect` and `type` alias declarations
  into one type namespace; unifying that with the value namespace carries all four along
  (open question 2). Nothing here needs to separately re-decide including them.
- **What does *not* unify.** Enum variant names stay in their existing, separately-scoped
  namespace (RFC-0107/RFC-0111): unifying module-level types and values says nothing about
  `Option::Some` or its unqualified exposure. Generic type parameters do not unify either —
  they are ordinary lexical shadowing, scoped to one declaration's own signature, the same
  mechanism a function parameter already uses (open question 2).
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

No compiler behaviour is changed merely by revising this RFC. The audit this revision's
namespace unification needs (open question 4) has already been run against the real
`metel-core` checkout, not left for later: 9 files out of 2,385 have a type/value name
pair that would become a redeclaration error under section 1, all of them test fixtures,
none in the standard library, several being `metel-core#1560`'s own fixtures (including the
one that deliberately pins coexistence as legal). This is new migration work section 1
introduces that the prior `new`/`.(...)` revision did not need, since that revision kept
both namespaces separate — but it is bounded and small, not a rename campaign. It also
means revisiting two *closed* issues (`#1560`, `#1571`) whose own acceptance criteria
assumed coexistence would remain a permanent invariant. Implement prototypes first;
acceptance and spec integration precede product implementation.

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

**Remaining acceptance work:** a prototype narrowing the `(module, namespace, name)` key's
namespace dimension to one value (section 1, open question 1); updating or retiring the
fixtures `metel-core#1560`/`#1571` added to pin coexistence as legal (open question 4, a
real audit already run); revisiting those two closed issues' own acceptance criteria,
which assumed coexistence would remain a permanent invariant; exact-row, visibility and
single-evaluation fixtures carried over from the prior revision. These are evidence
requirements, not completed checks.

## Open questions

1. **Resolved — checked against the actual current implementation history
   (metel-core#1560, #1571; both closed, merged 2026-10-23/24), which supersedes an earlier
   draft of this answer based on the older RFC-0030/RFC-0031 prose.** The symbol table is
   already keyed `(module, namespace, name)` with type and value as the two namespace
   values (`#1571`), and duplicate-name detection (`T0037`) already runs correctly within
   one namespace value — it does not run across both, because `#1560` explicitly decided
   it should not. Unification is narrower than "add new resolver machinery": it is
   collapsing that one dimension of an already-well-factored key from two values to one, so
   the duplicate check `#1560`/`#1571` already built does the rest unchanged. Imports
   inherit this for free too, since `#1571`'s "an import brings a name in every namespace
   the source module provides it in" already threads the namespace dimension through
   `ModuleScope`, imports, exports and the reference resolver — narrowing it in one place
   narrows it everywhere that dimension is read. Whether the resulting error reuses `T0037`
   or gets its own code, and what becomes of the reference resolver's "value, then type"
   fallback order once at most one declaration can exist per name, are implementation
   details for whichever follow-up issue does this, not settled here.
2. **Resolved — unification reaches aspects and type aliases automatically, by the
   existing grouping `#1560` already decided; generic type parameters are a different
   question, answered no.** `#1560`'s policy already puts structs, enums, aspects and type
   aliases in the one type namespace being unified with the value namespace here, so this
   RFC does not need to separately decide to include them — excluding any of the four would
   be the thing needing its own justification, not the default. Generic type parameters are
   different in kind: they are scoped to a single declaration's own signature and shadow
   outer bindings under the language's ordinary lexical-scoping rules, the same way a
   function parameter already can; that is pre-existing shadowing, not module-level
   redeclaration, and unification does not change it.
3. **Genuinely open, and independent of `#1560`'s own reasoning.** `#1560`'s decision to
   allow coexistence was a symbol-identity policy call, not a readability judgment — it
   says nothing about whether plain call-syntax construction reads well, so this question
   cannot be answered by appeal to that history either way. If reviewers still want a
   visual construction marker on readability grounds alone, independent of the soundness
   issue this revision fixes, that is an argument for revisiting position (3) instead of
   this one — a style preference, not a defect in this revision. Plain call syntax for
   construction is also unremarkable in mainstream languages outside the Rust/Haskell
   lineage (Python, Kotlin, Scala's `apply` convention, Swift's call-syntax initializers all
   construct with no dedicated marker), which is relevant context for whoever judges this,
   not a verdict in itself.
4. **Resolved — audited directly against the real metel-core checkout, not left
   hypothetical.** A scan of all 2,385 `.mtl` files under `metel-core/` for a top-level
   `struct`/`enum` name also used as a top-level `fun`/`let`/`var` name in the same file
   found exactly 9 matches, every one a test fixture, none in the standard library
   (`metel-frontend/stdlib/`). Several are `#1560`'s own fixtures, including the one that
   deliberately pins coexistence as legal (`a_type_and_a_function_may_share_a_name.mtl`,
   cited by name in its own comment). The real migration cost is small and bounded — not a
   rename campaign — but it specifically means retiring or inverting `#1560`'s own
   regression fixture into a negative test, and revisiting that closed issue's acceptance
   criteria, which assumed coexistence was a permanent invariant rather than a point-in-time
   policy.
5. **Resolved — not a real interaction, pruned.** A `dyn Aspect` value that happens to be
   callable (for example a `dyn Callable<..>`, RFC-0232) is invoked as an ordinary value
   call; the thing being called already lives in the value namespace regardless of this
   RFC. There is no scenario here in which an *aspect name itself* is called with `(args)`
   syntax the way a type or function name is, so unification does not interact with
   aspect-object dispatch at all. This was an overcautious question with nothing concrete
   behind it; PROCESS.md's "prune harder" rule applies.

**Lifecycle outcome:** Under review, tracked by metel-core#807. No acceptance, spec
integration or implementation transition is claimed.
