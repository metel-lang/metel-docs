---
id: rfc-0226
title: "Constructors in the value namespace"
date: '2026-11-11'
status: under-review
updated: '2026-11-11'
tracking: 'https://github.com/metel-lang/metel-core/issues/1944'
---

> **Status — under review (2026-11-11).** Language owner requested review and scheduled design settlement; constructor-binding prototype and interaction review remain required.

## Summary

Keep `Type(args)` as the construction syntax, but make a struct or named record
introduce its constructor name into the value namespace as well as its type name
into the type namespace. A competing value declaration in the same scope is an
error. Resolve the callee before binding or checking arguments; a failed call
never falls back to another namespace.

```metel
struct Ticket { value: i64 }
fun make_ticket(input: i64) -> Ticket { Ticket(value = input) }

// Rejected in the same scope as the struct:
// fun Ticket(input: i64) -> i64 { input + 100 }
```

The language owner agreed to this direction on 2026-11-11. The RFC is under
review, tracked by metel-core#1944; scheduling lives in that issue's milestone.
It does not amend the normative spec or authorise implementation before integration.

## Motivation and reproduction

RFC-0100 made construction a call while the scoping rules allow a type and a
function of the same name. The implementation chooses between them using the
call's arguments. The following program was run with the workspace's existing
`metel-core/target/debug/metel` binary on 2026-11-11:

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }
fun main() {
    println(Ticket(value = 1).value);
    println(Ticket(input = 1));
    println(Ticket(1));
}
```

Observed output: `1`, `101`, `101`. The first expression constructs a struct;
the other two call the function. In
`pipeline/type_checking/construction/expressions.rs`, `function_takes_the_call`
uses the argument binder to decide whether a same-named function takes the call.
This evidence describes that binary and the inspected code; it is not a claim
that a release-tag reproduction was performed.

A parameter rename can therefore redirect a construction-looking expression to
a function. A missing keyword can select the other namespace rather than report
the intended call's error. Neither casing conventions nor expected return types
provide a stable answer to which declaration a written call names.

## 1. Declarations and conflicts

A `struct Ticket` declaration introduces a type identity and an associated
constructor binding named `Ticket` in the same lexical scope. A named `record`
declaration does the same. The constructor binding identifies the construction
operation for that type; it is not a user function overload.

In that scope a constructor conflicts with a `fun`, `let`, `var`, or another
constructor of the same value name, regardless of parameter names, arity, argument
types, generic parameters, or result type. A constructor must not silently join a
function overload set. Declaration order does not change the result.

Report a duplicate-value declaration using the existing duplicate-declaration
category (T0037), pointing to the conflicting declarations and explaining that
the type introduces a constructor. Function-only overloading retains its existing
rules. Type names without constructors, including aspects, do not reserve value
names merely because they inhabit the type namespace.

```metel
struct Ticket { value: i64 }
// Each is a same-scope conflict, even with a different signature:
// fun Ticket() -> i64 { 0 }
// let Ticket := 7;
```

This is a change to name binding, not a rule requiring capitalised function or
type names. A constructor named `ticket` follows exactly the same rules.

## 2. Lookup, shadowing and call checking

For `Name(args)`, perform lexical value lookup first. The result determines
whether this is a function call, a call through a local value, or a construction
call. Only then bind keywords, choose among a function's ordinary overloads, infer
generic arguments and check types. None of these steps may switch from a value
binding to a same-spelled type.

An inner-scope value binding may shadow an outer constructor, just as it shadows
an outer function. The type namespace is unaffected:

```metel
struct Ticket { value: i64 }
fun main() {
    let Ticket := |n: i64| { n + 100 };
    let result := Ticket(1);          // calls the closure
    // let p: Ticket := ...;          // Ticket still denotes the type here
    // Ticket(value = 1);             // invalid call through a function value;
                                       // no constructor fallback
}
```

If the shadowing value is not callable, report that error. Do not attempt
construction. A nested type declaration introduces its constructor in the nested
scope by the same rules. Qualified value paths resolve the selected module's
constructor or value binding; qualification does not enable argument-dependent
fallback. Use an existing module qualification or import alias when a constructor
must remain accessible under a local shadow.

An expected type, keyword spelling, positional arity, turbofish, or argument type
must not override the resolved callee. `Self(...)` inside an impl identifies the
enclosing type's construction operation directly; `Self` is not an unrelated
value name selected by argument binding.

## 3. Imports, exports and aliases

Importing a constructible type brings its type identity and constructor binding
under the imported name. An alias renames both: `import model::Ticket as ModelTicket;`
makes `ModelTicket` usable in annotations and `ModelTicket(value = 1)` usable for
construction. Re-exporting such an item preserves the association and visibility.
Module-qualified construction uses that same constructor identity.

Two different value identities competing for the same imported name must be a
conflict or an ambiguous name under the existing import rules. No explicit/glob
import combination may merge an unrelated function with a constructor and let
arguments select between them. Existing import-precedence rules may still select
one binding where they already do so; once selected, failure does not retry the
other. Repeated imports of the same identity follow existing deduplication rules.

A transparent type alias to a constructible struct or named record exposes a
constructor binding under the alias name, targeting the same underlying type.
It participates in conflicts and shadowing exactly like the original constructor;
it introduces neither a new nominal identity nor a distinct construction policy.
An alias to a type without a construction operation introduces no constructor.
Alias resolution must establish constructibility before validating these value
conflicts, so source order cannot change the answer. Generic aliases retain their
existing argument substitution and bound rules.

This RFC adds no type-only import or new qualification syntax.

## 4. Empty types, variants and constructor values

Zero-field structs and named records reserve their value name too. Keep the
existing bare-value shorthand: `Empty` produces the empty value and `Empty()`
constructs it. Both use the constructor binding's identity; this RFC does not
reinterpret bare `Empty` as a function value. Shadowing applies to both spellings.

Enum variant constructors occupy the enum's member value names. Qualified forms
such as `Option::Some(value = 1)` keep their construction rules. An enum type name
itself has no single constructor and therefore introduces no callable binding
merely by being an enum. Existing unqualified-variant lookup and value-shadowing
rules (RFC-0111) remain; a selected ordinary value never retries a variant after
its call fails. Explicitly imported variant constructors participate in ordinary
value-name conflicts.

A constructor binding is a name-resolution category, not a promise that
constructors become first-class functions. This RFC adds no `let make := Ticket`
or higher-order constructor conversion for fieldful types, no constructor
address-taking, and no new keyword calls through function values. Such uses keep
their existing legality; a wrapper function remains available. This avoids
silently changing the empty-type shorthand or designing callable constructors as
a side effect of fixing name collisions.

## 5. Construction semantics and adjacent RFCs

RFC-0100 continues to own positional/keyword field binding, evaluation order,
visibility, construction spreads and nominal construction. RFC-0223 continues to
own argument binding and function overload rules. This RFC only removes the
choice between a constructor and an unrelated function based on those arguments.

RFC-0114's proposed `Construct` customisation would supply the operation behind
the constructor binding; it would not introduce a competing free function or
change lookup precedence. Its invariant, fallibility and minting questions remain
with that RFC. No construction visibility is widened by exposing the binding.

RFC-0225's anonymous `.{ ... }` records are independent: they have no declaration
name to reserve. Nominal construction remains `Ticket(...)`, rather than gaining
another spelling in this RFC.

On integration, amend the scoping/namespace rules, module imports and aliases,
struct/named-record construction, and affected variant rules. Reconcile RFC-0100,
RFC-0106 and RFC-0111 where their current wording relies on type-namespace
fallback. RFC-0128 (exportable overload sets, draft) must explicitly exclude
mixing an unrelated function with a constructor. Historical decisions remain
recorded; current claims must explain this amendment.

## Alternatives considered

- **`new Ticket(...)`:** expresses construction explicitly and permits unrestricted
  type/function name coexistence, but adds a keyword and changes every constructor
  call. Viable if retaining that coexistence is more important than `Type(...)`.
- **`Ticket::new(...)` or `Ticket::construct(...)`:** ordinary-looking associated
  calls, but requires a standard member name and revisits the construction surface.
- **Always prefer the value and fall back only when absent:** predictable lookup
  but still allows adding a function/import to capture calls previously constructing
  the type. The proposed constructor binding makes a same-scope collision explicit.
- **Prefer the type or use expected result types:** hides the function or makes
  call identity depend on surrounding inference. Neither fixes the underlying
  competition for one callable spelling.
- **Treat constructors as overload candidates:** still allows argument changes to
  select an unrelated operation and complicates overload/import coherence.
- **Capitalisation rules:** conventions do not resolve imports, aliases or local
  shadows, and mandatory casing would be a separate language restriction.

## Migration and implementation plan

Inventory same-scope constructor/function/binding collisions and aliases/imports
before implementation. Rename a competing function (for example `make_ticket`),
rename an import, or qualify accesses using existing module paths. Update each
call using its resolved identity under the old rules; a text-only rename cannot
distinguish constructor calls from same-spelled function calls.

Reserve constructor identities during name resolution, preserving the associated
type identity through imports, aliases and re-exports. Type checking and typed-AST
construction consume the resolved choice; they do not repeat argument-dependent
namespace decisions. Respect the inference/construction boundary. Remove
`function_takes_the_call`'s fallback role and audit other constructor recovery paths
for the same behaviour, including generic and cross-module calls.

Land documentation and changelog with implementation, using the public-docs PR
and core docs-pin workflow. This is a language-visible namespace change requiring
a minor release under the project versioning rule. Release assignment lives in
the design-settlement tracker metel-core#1944. Implementation requires acceptance,
spec integration and an implementation tracking issue first.

## Acceptance and verification

Before acceptance, prototype constructor binding and inventory migration sites.
Turn the motivation program into a duplicate-declaration regression and verify:

- Same-scope collisions with functions, overload sets, bindings and constructors
  are diagnosed regardless of order, arity, labels, genericity or casing.
- Ordinary constructors keep positional/keyword, generic, `Self`, spread,
  visibility and evaluation-order behaviour.
- Nested bindings shadow normally; wrong keywords, types and arity, or calling a
  non-callable shadow, cannot fall back to construction.
- Explicit/glob imports, aliases, re-exports and qualified paths preserve identity
  and existing precedence, without argument-dependent namespace selection.
- Transparent aliases, generic aliases and aliases to nonconstructible types
  produce the intended constructor bindings and order-independent conflicts.
- Empty-type bare values and calls keep their behaviour; qualified and unqualified
  variants keep their existing precedence with no retry after a selected call fails.
- Generic-body definition checking and typed-AST construction use the same resolved
  callee identity, including calls across modules.

The agreed direction is constructor ownership of the value name. Alias binding,
import precedence interactions and empty-type handling are explicit proposals in
this proposal that require review against the existing resolver, rather than claims
that a prototype already proves them.

## Decision

**Design direction agreed (2026-11-11):** preserve `Type(...)`, introduce the
constructor in the value namespace, reject same-scope competing values, retain
ordinary lexical shadowing, and remove argument-dependent namespace fallback.

**Lifecycle outcome:** Under review, tracked by metel-core#1944. Prototype,
detailed interaction review, formal acceptance and spec integration remain
outstanding.
