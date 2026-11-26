---
id: rfc-0100
title: "Nominal Construction Through a Unified Type and Value Namespace"
date: '2026-11-11'
status: accepted
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/807'
---

> **Status — under review.** Review tracked by metel-core#807. The current proposal uses
> plain `T(...)` construction with a unified type/value namespace. Prototype evidence
> and interaction review remain required before acceptance.

> **Revised (2026-11-26, language owner).** `new`/`.(...)` are withdrawn. Construction returns to plain
> call syntax, `Struct(args)`, fixing the original argument-dependent lookup bug by removing its
> precondition instead of adding a visual marker: a module's type and value declarations now share one
> namespace, so a struct and a function can never carry the same name in the first place, and `Struct(args)`
> is never ambiguous because there is only ever one thing `Struct` can mean. The inferred, expected-type
> compact form (previously `.(...)`) is withdrawn from this proposal and deferred to its own future RFC —
> it is an independent question once the namespace collision is gone structurally rather than syntactically.

> **Status — accepted (2026-11-26).** Open questions resolved (section 1 unification grounded in #1560/#1571, enum/alias/generics scope settled, readability and privileged-construction syntax settled); language owner judges the design settled without further prototype gating

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
an enum variant constructor, the call constructs it; if it is a function, the call invokes it; nothing about the
call's own syntax changes between the two cases, and nothing needs to.

Whole-row construction stays explicit: `Point(..row)` supplies a record binding, and
`Point(..{ .x = 1, .y = 2 })` supplies a literal row. Never reinterpret an ordinary
record-valued argument as the whole parameter row.

Bare zero-field struct/named-record construction is retired as its own special case —
`Empty()` is simply a call to whatever `Empty` is, and under namespace unification that is
never ambiguous (section 7).

**The inferred, expected-type compact form is deferred, not part of this proposal.**
`new` is not reserved.

This revision's scope grew beyond construction-call syntax: section 3 also specifies a
privileged representation-construction form, `Point { ... }` — the existing nominal
brace literal, revived narrowly for use only inside a type's own canonical or unchecked
constructor body — and a condition-position restriction needed to keep it unambiguous
with a block. Representation patterns keep their existing spelling, `Point { x, y }`,
unmigrated. This is a substantive, separate design area, not a detail of ordinary
call-syntax construction — see section 3 and open question 6.

This RFC remains under review. Release assignment lives in
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
declarations (`fun`, `let`/`var` at module scope) share one namespace.** A name denotes
one type declaration, one non-function value, or a function overload set. Existing
function overloading remains available under its current rules (language owner,
2026-11-26). A type and function, a type and `let`, or two types of the same name in
the same scope conflict. Unification does not remove function overload sets.

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
declaration-site check, since a name resolves to one declaration or one function overload set; whatever
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
- **Import precedence across declaration categories.** Apply RFC-0030 section 7's existing
  explicit-versus-glob precedence and glob ambiguity rules in the unified namespace
  (language owner, 2026-11-26). Explicit imports of a type and a function under the same local name conflict;
  an explicit import wins over a glob binding of that name regardless of category; competing
  glob bindings remain ambiguous when used. Function overload sets retain their existing
  rules; this decision does not define new merging of functions from separate imports.
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

Construction targets structs, named records, and enum variants as discussed in section 7.
Privileged representation construction is a separate operation, covered in section 3.
It specifies neither heap allocation
nor a fresh runtime identity; storage and ownership keep their rules. It does not mean
raw field initialisation: it invokes the canonical construction operation, including
validation when RFC-0114 supplies it.

```metel
struct Ticket { value: i64 }
let a := Ticket(value = 1);   // construction: `Ticket` names a struct
```

A type alias exposes a construction target, not a new constructor value binding. No
`new` keyword is reserved by this revision.

## 3. Privileged representation construction and patterns

The language owner selected constructor-body privilege on 2026-11-26: an explicit
representation-construction form is available only in the target's own canonical
constructor or explicitly unchecked constructor body, not generally throughout the
declaring module. It creates the final value without recursively invoking that same
constructor. The privileged form may target only that constructor's own type, using
`Self` or its explicit type name; constructing another type uses its ordinary
construction interface (language owner, 2026-11-26). RFC-0114 owns the privilege,
validation, and unchecked-operation rules.
An explicit field-list representation construction initializes every field exactly
once; a missing, duplicate, or extra field is an error (language owner, 2026-11-26).
A whole-row form such as `Self { ..fields }` consumes a complete anonymous record
whose row has exactly the target's fields with matching types and performs the same
privileged final construction (language owner, 2026-11-26). It remains subject to
ordinary ownership and visibility rules. Its exact grammar needs review against row
spread syntax.
Candidate syntax uses `Point { x = 1, y = 2 }` for the privileged construction
operation — the existing nominal brace literal, which construction-call syntax
otherwise retired, revived narrowly for this constructor-body-only use. Ordinary
construction remains `Point(x = 1, y = 2)`.

**This is RFC-0114 §1.1's mechanism, not a second one invented alongside it** — "a
value of `Self`'s complete row type is admitted where `Self` is expected, inside the
body of `Construct::construct` and `ConstructUnchecked::construct_unchecked`, and
nowhere else." RFC-0100 supplies this operation's surface syntax; RFC-0114 supplies
which constructor bodies may use it, its relationship to fallibility, and the
validation it bypasses. Neither RFC independently defines a privileged-construction
channel; there is one mechanism, described from two complementary sides, and RFC-0114
§1.1 must be kept in sync with whichever surface syntax this section currently states
(as of this revision, bare braces with the condition-position restriction below, not
the dotted `Point .{ x = 1, y = 2 }` form an earlier pass of both RFCs shared).
**This section is struct/enum-whole-type scoped only; per-variant privileged
construction is RFC-0114 §9's extension, not this RFC's or RFC-0210's to define.**
RFC-0114 §9 proposes `Self::Variant { field = value }` and bare `Self::Unit` for
minting a specific variant inside the enum impl's own `construct`/`construct_unchecked`
— the same mechanism as this section, scoped one level down, pending RFC-0114's own
acceptance. RFC-0210's "privileged representation construction of a variant" refers to
that proposal, not an independent one.

This revives the struct-literal-vs-block ambiguity nominal brace literals were
originally retired for: a bare `T { ... }` directly in `if`/`while`/`match` condition
position is ambiguous between a construction expression and the start of that
construct's own body block. Resolved the same way other call-syntax languages with this
problem resolve it: **a bare privileged-construction expression is rejected directly in
condition position; parenthesize it there, `if (Point { x = 1 }).active { ... }`**
(language owner, 2026-11-26). This does not affect `Point(x = 1, y = 2)` ordinary
construction, which stays unambiguous in condition position because it opens with `(`
rather than `{`; nor does it affect representation patterns, which never appear in
condition position in the first place. Exact production-level placement of the
restriction needs grammar review; this fixes the specific ambiguity, not every
positional interaction a prototype may still surface. Enum variant
construction needs the equivalent analysis, and empty forms must be unambiguous.

The constructor's public parameter interface need not mirror stored fields. Patterns
describe representation and remain subject to field privacy and ownership rules.
Outside the declaring module, a pattern cannot name a private field and may omit it
with `..`; inside the module it may name it (language owner, 2026-11-26). Omitted
fields remain subject to the existing ownership, discard and destruction rules.
No acceptance of an enum canonical-construction model is implied by the privilege
decision.

**Representation patterns keep their current spelling, the existing nominal brace
pattern `Point { x, y }` (language owner, 2026-11-26) — no migration to any new
syntax.** Patterns were never part of what needed resolving above: they don't appear in
condition position, don't collide with residual projection or anything else, and
nothing about the privileged construction spelling requires changing them. Patterns
remain `Point { x, y }`, unchanged, with their existing binding, exhaustiveness,
visibility and ownership rules.
Nominal representation fields support renaming and nested subpatterns, analogous
to anonymous-record patterns: `Point { x: 0, y: vertical }` matches the first field
against a literal and binds the second under another name (language owner, 2026-11-26).
A refutable field makes the enclosing pattern refutable; `let` patterns must remain
irrefutable. Exhaustiveness must account for nested patterns. Naming a private field
is forbidden outside its declaring module even when its subpattern is `_`.
Nominal struct patterns retain bare `..` for omitted fields; binding a remainder as an
anonymous record with `..rest` is deferred (language owner, 2026-11-26). Its design must
address brand removal, private fields, `Drop`, and ownership before it is admitted.
Zero-field structs and unit enum variants use the existing empty pattern `Empty {}` and
the existing bare unit-variant shorthand (language owner, 2026-11-26), with their
current qualified and expected-type-directed lookup rules. This does not introduce a
bare zero-field struct construction shorthand.

## 4. Deferred: an inferred, expected-type compact form

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

## 5. Positional, keyword and record-valued arguments

Construction retains RFC-0223's argument rules: positional arguments bind in field
declaration order and precede keyword arguments; keywords bind by name; every parameter
is supplied once. Arguments evaluate left to right as written. No new defaults, partial
application or constructor overloading is added.

These field parameters are the synthesized construction interface. Until custom
constructors are specified and implemented, they are the complete interface. A future
custom constructor may replace that interface with its explicitly declared parameters;
calls bind to those parameters, and its implementation supplies the complete row for the
canonical operation (language owner, 2026-11-26). There is one construction interface per
type; constructor overloading remains outside this proposal. RFC-0114 owns the custom
interface's declaration, checking, mapping and fallibility.

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

### Field visibility and construction access

The proposed field-parameter construction preserves the current field-visibility
boundary. A call that supplies a private field is legal in the field's declaring
module and is rejected outside it, even when the type itself is public. This check is
based on the field to which an argument binds, not on whether the argument was written
by name or position. It is applied after resolving the target and binding the complete
argument list; positional arguments cannot be used to bypass a private keyword.

```metel
// account module
pub struct Account { pub name: String, balance: i64 }
pub fun make(name: String) -> Account { Account(name = name, balance = 0) } // allowed

// another module, after importing Account and make
let a := make("Ada");                    // allowed through the module's public API
let b := Account(name = "Ada", balance = 41); // error: balance is private
let c := Account("Ada", 41);            // error: positional argument binds balance
```

The current proposal requires every construction parameter exactly once and has no
field defaults. Consequently an external call to the synthesized field-parameter
constructor is unavailable if any required field is private. A module can expose a
public function that chooses or validates private values and constructs locally.
Access to a public type or a transparent alias of it does not grant access to its
private fields. A qualified call, an alias, an inferred generic argument, or a
whole-row argument cannot change the access check.

RFC-0114's custom `Construct` and its fallibility are not implemented by this RFC.
A future custom constructor may explicitly expose a **different public parameter
interface** and supply or derive private fields itself (language owner, 2026-11-26).
The constructor's declaration and implementation must define how its inputs reach the
canonical construction operation; syntax, checking, and fallibility remain RFC-0114's
work. A private field is not a public parameter merely because the canonical operation
can validate it. Until such an interface is specified and implemented, the field-parameter
visibility rule above applies.

## 6. Whole-row construction: `..r` and `..{ ... }`

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

## 7. Empty types, variants and failure

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

### Enum variant construction

Enum variant construction is in this RFC's scope (language owner, 2026-11-26). The
working direction extends plain call construction to variant targets; the exact handling
of unit variants, expected-type shorthand and canonical enum validation is open. An enum
type alone does not identify a variant. A qualified path does:

```metel
enum Message { Text { body: String }, Number { value: i64 }, Empty }
let a := Message::Text(body = "hello");  // proposed
let b := Message::Number(42);            // proposed positional payload
let c := Message::Empty();               // unit-variant construction call
let d := Message::Empty;                 // retained unit-variant shorthand
// Message(...) does not choose a variant from its arguments.
```

For a payload variant, the candidate uses the same positional and keyword argument
binding, exact-row, evaluation-order and field-visibility principles as struct
construction, applied to that variant's payload. A whole-row operand such as
`Message::Text(..fields)` is the sole argument, is evaluated once, and must match the
complete payload row exactly with matching field types and applicable visibility checks
(language owner, 2026-11-26). Variant-field visibility must be checked against the enum
and privacy specifications. Enum variant names remain in their
existing variant namespace. RFC-0111's expected-type-directed unqualified forms and their
precedence against lexical bindings extend to payload-variant calls (language owner,
2026-11-26): an expected enum type may resolve `Text(body = "hello")`, while an
in-scope binding named `Text` takes precedence. Without a suitable expected enum type,
the caller must qualify the variant; resolution does not search all enums. Argument
binding must not be used to select between a lexical callable and a variant.

Qualified bare unit-variant expressions remain valid alongside `Message::Empty()`
(language owner, 2026-11-26). Existing expected-type-directed unqualified unit-variant
expressions remain subject to RFC-0111's lookup rules; this does not restore bare
zero-field struct construction. Both unit-variant spellings must follow the same
construction and validation contract once RFC-0114's enum interaction is settled.

Enum variants are intended to use one enum-wide canonical operation, synthesized as an
identity unless customized (language owner, 2026-11-26). RFC-0114 owns the operation's
raw representation, result, failure and unchecked rules, subject to RFC-0210's variant-
preservation contract: a successful per-variant constructor returns the requested
variant type or an error, never a different variant. A prototype must cover qualified and unqualified variants,
zero-field and fieldful variants, payload binding and privacy, generic enums, and
collisions with lexical names. Existing match and destructuring patterns are not changed
by this construction proposal; their spelling is a separate design question.

Construction uses the same result handling regardless of how it is spelled: no
implicit unwrap, no caught failure, no bypassed validation. RFC-0114's
`Construct`/fallibility model remains its own design; its current synthesised
infallible scope is not evidence of implemented custom constructor support.

## Interactions and migration

This revision replaces RFC-0100's `new`/`.(...)` consolidation with a return to plain
call syntax, reached through section 1's namespace unification rather than the original,
reverted design's unguarded one. It retains RFC-0100's argument collection and exact-row
contract (sections 5-6), unchanged from the prior revision except for dropping `new`. It
retires RFC-0106's bare shorthand for zero-field structs/named records, now subsumed by
section 7. RFC-0111's enum-variant resolution must be reconciled with section 7.
RFC-0225 owns anonymous record syntax;
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
identical. **Resolved (language owner, 2026-11-26, open question 3): plain call syntax
stands without a dedicated visual marker.** The reason the objection mattered for (2) —
a reader (and the compiler) needing to tell two coexisting meanings apart — no longer
holds once section 1 removes the coexistence itself. Readers who still want a syntactic
construction marker on readability grounds alone get it, if wanted, from a future RFC
addressing section 4's deferred compact form, not as a precondition for soundness.

For record operands, implicit row unpacking based on argument shape is rejected:
it would give a normal record-valued positional argument two possible meanings.
Use `..r` or `..{ ... }` to state whole-row intent explicitly. General implicit
anonymous-record-to-nominal conversion is also outside this proposal.

**Current design direction (2026-11-26):** plain call-syntax construction, a unified
type/value namespace making that syntax sound, ordinary positional/keyword rules,
explicit whole-row operands with `..{ ... }` literal notation, no implicit construction
from bare names, and the inferred compact form deferred to its own future RFC.

**Accepted without a prototype (2026-11-26, language owner):** all open questions were
resolved by review rather than by implementation evidence; the design is settled on
paper, not yet checked against a running compiler. The following is integration work
this acceptance carries forward, not a precondition that was waived silently: a
prototype narrowing the `(module, namespace, name)` key's namespace dimension to one
value (section 1, open question 1); updating or retiring the fixtures
`metel-core#1560`/`#1571` added to pin coexistence as legal (open question 4, a real
audit already run, not yet acted on); revisiting those two closed issues' own
acceptance criteria, which assumed coexistence would remain a permanent invariant;
exact-row, visibility and single-evaluation fixtures carried over from the prior
revision. `3-integrated` does not proceed until these exist and pass, per PROCESS.md's
own `2-accepted`/`3-integrated` distinction — accepted means the design is agreed, not
that it has been built.

The prototype's interaction cases must include private fields supplied by positional,
keyword and whole-row arguments, both directly and through a transparent imported alias.
Check that the declaring module can construct while an external caller receives the
visibility error, including when the source row itself is visible. Check a local function
overload set and explicit/glob imports across type and value categories against section 1.

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
3. **Resolved (language owner, 2026-11-26):** nominal construction uses plain call
   syntax, `Point(...)`, without a dedicated visual marker. The unified namespace resolves
   the target independently of its arguments. Prototype evidence and interaction review
   remain required before acceptance.
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
6. **Resolved (language owner, 2026-11-26) — privileged construction uses the existing
   nominal brace literal, `Point { x = 1, y = 2 }`, with a condition-position
   restriction.** Two earlier candidates were considered and ruled out first: a dotted
   form, `Point .{ x = 1, y = 2 }`, collided with existing `Point.{ .x }` residual
   projection syntax (RFC-0137/RFC-0146) by whitespace alone, which is fragile —
   accidental or reformatted whitespace would silently change meaning; a double-dot
   marker, `Point..{ ... }`, sits in the same bare-postfix-after-a-term position
   existing range expressions already occupy, an unverified and likely-colliding
   position nothing else in the grammar risks. Reviving the nominal brace literal
   (section Design history) instead reopens a different, known problem — struct-literal-
   vs-block ambiguity in condition position — which is settled directly: a bare
   privileged-construction expression is rejected in `if`/`while`/`match` condition
   position, requiring parentheses there (section 3). Representation patterns were
   never part of this collision and keep their current, unmigrated spelling regardless.
   Exact production-level grammar for the condition-position restriction still needs
   review; this resolves the design question, not every parser detail a prototype may
   surface.

**Lifecycle outcome:** Accepted (2026-11-26), tracked by metel-core#807. The design is
settled; no spec integration or implementation transition is claimed. `3-integrated`
requires the prototype and fixture work recorded above, a linked implementation-tracking
issue, and merging this RFC's content into `reference/spec/` with worked examples
checked against the rest of the integrated spec.
