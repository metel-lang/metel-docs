---
id: rfc-0128
title: "Exportable overload sets and shadow-versus-extend semantics"
date: '2026-08-04'
status: draft
target:
---

## Summary

Define how same-name functions form overload sets, how exports and imports preserve them, and when a declaration shadows versus extends an existing callable.

---

## Motivation

Metel does not specify how same-named functions, exports, lexical shadowing, and aspect
`extend` methods interact. This leaves lookup dependent on incidental implementation
details and makes a module's callable API impossible to reason about from its exports.

## Proposal

At module scope, same-named `fun` declarations form one **overload set**. Members must
have distinct parameter shapes; arity, receiver form, and parameter types distinguish
members, but return type alone never does.

```metel
fun parse(text: String) -> Ast { ... }
fun parse(tokens: Token[]) -> Ast { ... }
```

At a call, lookup first selects one lexical overload set, then type checking selects one
member. No applicable member, or more than one equally applicable member, is an error
listing that set's candidates. An inner binding shadows the whole outer set: argument
types never cause lookup to escape a nearer binding.

`export parse;` exports a complete overload set, and an import or alias binds that whole
set. Selective export of a member is unsupported. Two imports with the same local name
are a conflict and are never silently unioned, even if currently disjoint; explicit
forwarding functions are required to combine APIs. Glob imports keep their existing
priority/conflict rules, then expose the winning set.

`extend Type: Aspect` supplies declared aspect methods through aspect/dot dispatch. It
does not add free-function overloads, and a free `fun` cannot reopen an aspect method.

## Consequences

- Function environments and module exports represent a name as a collection of schemes,
  not an overwrite-prone `name -> scheme` map.
- Runtime registration uses the selected typed callable identity rather than a string
  name, so overloads cannot overwrite one another.
- Adding an overload may make a call ambiguous, with the diagnostic emitted at that call.

## Alternatives

- **One function per name:** rejected because it forces arbitrary API spellings.
- **Merge same-named imports:** rejected because dependency changes could silently alter
  an importer's API and make semantics depend on import order.
- **Treat `extend` methods as free overloads:** rejected because it erases receiver/proof
  context and undermines aspect-coherence diagnostics.

## Open questions

1. Does a monomorphic member outrank a generic member when both accept a call, or are
   ties initially ambiguous?
2. Does RFC-0127 use this model for associated functions, or a type-qualified variant?
3. What compatibility tooling should report an exported overload that makes a consumer's
   call ambiguous?

## Implementation sketch

This adds no syntax. Function scheme environments, module exports, typed calls, runtime
registration, and diagnostics must be designed together. Open an implementation issue
only after this RFC is accepted.



---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
