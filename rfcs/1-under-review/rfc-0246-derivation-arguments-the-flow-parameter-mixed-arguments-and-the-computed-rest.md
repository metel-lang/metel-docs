---
id: rfc-0246
title: "Derivation arguments: the flow parameter, mixed arguments and the computed rest"
date: '2026-11-23'
status: under-review
updated: '2026-11-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/2172'
---

> **Status — under review (2026-11-23).** Tracked by metel-core#2172.

## Summary

A derivation may accept leading positional arguments, a variadic flow of type parameters
of the target, and keyword arguments. The proposed lowering uses RFC-0247's rest binding
and RFC-0248's final default marker. This RFC owns the flow's type and any comptime
elaboration it needs. It also owns the proposed visibility rule for public computed flows.

## Motivation

RFC-0238 makes derivation clauses calls into comptime derivers. A parameter list with a rest
can separate leading arguments from the flow without a numeric row splice that renumbers its
labels. The flow also needs a way to identify entries as type parameters of the particular
target rather than arbitrary types. A declaration-side default would let `derives A(..)` use
the ordinary call mechanism once that flow contract is expressible.

## Proposal

### 1. What a flow entry is

In `struct S<T, U> derives A(T)`, the argument `T` is resolved in the declaration's generics scope. It is a comptime value of kind
`type`, restricted to the generic parameters of the declaration being derived; call the type of such a value `TypeParam<Target>`.

- `derives Clone(i64)` and `derives Clone(V)` for a `V` that is not a parameter of the declaration are errors (`T0046`, "names no
  type parameter of this declaration"), as RFC-0227 says today.
- A parameter of row or record kind is not accepted (RFC-0224 rule 7), as today.
- A deriver reads an entry through `typeinfo(Target)`, whose list of generic parameters the entries are drawn from.

`Flow` denotes a sequence represented as a dense numeric row `.{ .0 = P, .1 = Q, .. }` of such values, of any width. Its meaning is fixed: the parameters the emitted impl
is **conditional on**, that is, the parameters `P` for which the impl carries the bound `P: A`.

### 2. Binding

The proposed `derive` signature is a parameter list, with the flow receiving the remaining
positional arguments after any fixed positionals. Parameters after the rest bind by keyword.
The signature below is schematic. `Flow<Target>` denotes the variable-width flow contract
this RFC must define. RFC-0247 currently accepts a row-bound tuple or a closed tuple as a
rest type.

```metel
extend Serialize: Derivable {
    comptime fun derive(Target: type, name: String, ..flow: Flow<Target>,
                        rename_all: String) -> Decl { /* ... */ }
}
```

| Clause | Binds |
|---|---|
| `derives Serialize("x", T, U, rename_all = "none")` | name `"x"`, flow `(T, U)`, rename rule `"none"` |
| `derives Serialize("x", rename_all = "none")` | name `"x"`, empty flow, rename rule `"none"` |
| `derives Serialize("x", rename_all = "camel", T)` | error: positional argument after a keyword |
| `derives Serialize(T, "x", rename_all = "none")` | error: the leading positional needs a string |

### 3. Computed flows as defaults

Where a deriver declares a default for its flow, a final bare `..` selects it only
when no explicit flow entry was supplied. A nonempty explicit flow takes precedence
as one complete rest. For example:

```metel
extend Clone: Derivable {
    comptime fun derive(Target: type,
                        ..flow: Flow<Target> = std::derive::needed_flow(Target, Clone)) -> Decl {
        field_wise(Clone, Target, flow)
    }
}
```

- A bare `derives Clone` passes the empty flow. `derives Clone(T)` passes the flow `(T)`.
- `derives Clone(..)` requests the declared default. In this example, `needed_flow` uses
  RFC-0227's field dependence analysis to compute the smallest sufficient flow.
- `derives Clone(T, ..)` passes the explicit flow `(T)`. It never appends computed entries.
- A user deriver can declare a different default, provided it satisfies the flow contract.
  Ordinary RFC-0248 binding handles its other defaults.

The variable-width comptime result and its target-dependent entry types need a checked
interface before this lowering can replace the built-in RFC-0244 behavior.

### 4. The class keyword

`copy` is `derives Clone, Copy` with no condition on the type parameters, and it has no computed form (RFC-0244).
A type that is `Copy` only for some arguments writes the entries: `derives Clone(..), Copy(..)` to compute the condition, or
`derives Clone(T), Copy(T)` to state it. The keyword then means one thing, and the only spelling of "computed" is `(..)`, a default request at the call site. An explicit `derives` entry beside `copy` still replaces the keyword's entry for that aspect, as in RFC-0244 section 3.

### 5. Visibility of public computed flows

The `pub` rule of RFC-0227 section 3 (in RFC-0244's form: a `pub` generic type may use a computed flow only when it is empty) is
replaced by a widening of an existing visibility rule. Today `modules.md` legality-8 says a private field's name cannot appear in a
public signature, so that it never becomes part of the module's API. For a computed derivation flow, apply the corresponding visibility rule:

> A private field cannot determine a public derivation's computed condition.

The derived impls of a `pub` type, with their conditions, are part of its interface. So `(..)` on a `pub` type is an error exactly when
a private field contributes a parameter to the computed flow:

```metel
pub struct Pair<A, B> derives Clone(..), Copy(..) { pub a: A, pub b: B }     // ok: the flow comes from public fields
pub struct Token<T>   derives Clone(..), Copy(..) { pub kind: T, span: i64 } // ok: the private `span` contributes nothing
pub struct Handle<T>  derives Clone(..), Copy(..) { id: u64, tag: T }        // error: the private `tag` decides the flow;
                                                                             // state `Clone(T), Copy(T)`, or make `tag` pub
```

- **Why.** A computed condition decided by a private field is an interface its author can change without seeing it: a private field
  edit that adds a parameter tightens the condition and breaks downstream code, while the author's own build stays green. A public
  field's type is already part of the API, so a flow computed from public fields changes only when the API visibly does.
- **The empty case falls out.** An empty computed flow has no contributing field, so no private one; RFC-0244's "only when empty"
  exception needs no statement.
- **Checking is not deciding.** A stated flow, and the strict check of a bare entry, read private fields freely: they only produce
  errors for the author, and the interface is what is written.
- **It is more permissive than the rule it replaces.** A `pub` type whose contributing fields are public may use `(..)`, which is the
  common case for plain data types.
- **Mechanism.** `needed_flow` reports, with each parameter of the flow, the fields that contributed it (RFC-0227's dependence analysis
  already has this), and the check is made when the `derives` clause of a `pub` declaration is evaluated. The diagnostic names the
  private field.
## Alternatives considered

- Keep the RFC-0238 `Args` row and a renumbering `..Flow` splice. This requires
  positional row concatenation from RFC-0125.
- Use a keyword tuple such as `flow = (T, U)`. It adds syntax to the common
  `derives Clone(T)` case.
- Collect arguments by their type. This makes a `type` argument for another
  purpose ambiguous with a flow entry.
- Add a separate postfix computed marker or a computed `copy` form. RFC-0244
  already supplies the explicit `(..)` spelling.

## Interaction with other work

- **RFC-0227 and RFC-0244:** keep the existing built-in flow behavior until this
  RFC is integrated. This RFC owns any later changes to computed-flow visibility.
- **RFC-0238:** reconcile `derive`'s parameter-list contract with the registration
  proposal's `Args` row before either design relies on it.
- **RFC-0247 and RFC-0248:** supply ordinary rest binding and defaults. Neither
  RFC depends on this derivation-specific lowering.
- **RFC-0092, RFC-0132 and RFC-0237:** supply the relevant comptime, reflection
  and aspect-value machinery.

## Open questions

1. How does the flow contract express target-dependent type-parameter values and
   arbitrary width? Decide whether a row binder suffices or a separate comptime
   sequence type is required.
2. How does a computed default establish a concrete row and satisfy that contract
   before `derive` runs? Specify how the compiler checks its shape and element types.
3. Can a deriver take another flow-like group as a fixed keyword argument? The
   positional call consumes at most one rest.
4. How should the registration contract expose the checked parameter list and its
   defaults? Reconcile this with RFC-0238.

## Decision

**Outcome:** *(pending)*
