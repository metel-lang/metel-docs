---
id: rfc-0227
title: "Derivation Arguments"
date: '2026-11-12'
status: integrated
updated: '2026-11-16'
tracking: 'https://github.com/metel-lang/metel-core/issues/2002'
coverage:
  "1": { spec: "spec.declarations.aspects.declaration-clauses.legality-11" }
  "2": { spec: "spec.declarations.aspects.declaration-clauses.legality-12" }
  "3": { spec: "spec.declarations.aspects.declaration-clauses.legality-13" }
  "4": { kind: blocked, reason: "The grouped entailment rule is blocked on metel-core#2067 and metel-core#2066.", ref: "https://github.com/metel-lang/metel-core/issues/2067" }
impl_tracking: 2067
impl_status: not-started
---

> **Status — under review (2026-11-16).** Rewritten from "Stated flow for every derived impl": the `via` keyword is replaced by
> arguments to the derivation, and the registration of user derivations is left to a later RFC (the registration RFC, which
> supersedes the remaining half of RFC-0093). Milestone: v0.16.0.

> **Status — accepted (2026-11-16).** No open questions; design settled with the language owner 2026-11-16.

> **Status — integrated (2026-11-16).**

## Summary

A `derives` entry may carry **arguments** that are passed to the derivation of its aspect:

```metel
struct Pair<A, B> derives Clone(A, B) { a: A, b: B }              // Pair<X, Y>: Clone when X and Y are
struct Tagged<T> derives Clone(T) { id: i64 }                     // Clone only when T is, whatever the fields become
struct Wrapper<T> derives Clone(T), Copy(T) { value: T }          // Copy when T is Copy; Clone when T is Clone
struct Plain<T> derives Clone { v: T }                            // no arguments: the compiler computes the flow
struct Free<T> derives Clone() { n: i64 }                         // an empty argument list: Clone whatever T is
```

This replaces RFC-0224's `via` clause, which passed one fixed argument (the set of type parameters an impl's bounds depend on, its
**flow**) to one fixed derivation (`Copy`'s). The arguments of a derivation are those of any call: it has a signature and the
clause supplies the values. For the field-wise derivations the compiler provides (`Clone`, `Copy`), the signature is a list of the
declaration's type parameters. A derivation that declares no parameters accepts no arguments.

The rule of the clause, stated once:

> A derivation is the compiler writing an ordinary conditional impl. `derives A(P, Q)` means
> `extend<P: A, Q: A, R> T<P, Q, R>: A`, with a body the compiler writes. The arguments choose which type parameters carry the
> bound.

This is a design draft. Nothing here is accepted. RFC-0224's `via` is implemented for `Copy` only (metel-core#1941) and is
replaced when this RFC is.

---

## Motivation

### `via` was a keyword for one argument of one derivation

RFC-0224 section 1 allows `via` on `Copy` alone because `Copy` was the case that had lost something (RFC-0206's stored
condition). Nothing in the mechanism is specific to `Copy`:

- The derived impl already bounds each parameter a field holds by value by the derived aspect itself (`impl_generics` in the
  clause expansion). The flow only replaces the computed set of bounded parameters with a stated one.
- The sufficiency rule (the stated set must contain every parameter a field depends on, and may contain more) names no aspect.
- The only `Copy`-specific code is one guard that rejects `via` on another entry, and the rules that come from `Copy`'s own
  properties.

A keyword for this one argument stops making sense once a derivation is understood as something with parameters: a derivation
that is not field-wise, or a user's (the registration RFC), takes arguments of its own, and a keyword per parameter does not scale.

### What a `Clone`-only type cannot do today

`derives Clone` on a generic type bounds every parameter a field mentions by `Clone`. A type cannot say that it is `Clone` only
when a smaller set of parameters is, so a public generic type's interface moves with its fields, which is the reason RFC-0224
makes a `pub` type state its `Copy` flow. `Option`, `Result` and `List` in std are exactly this case. The over-approximation of a
nested nominal field (metel-core#1938) affects `Clone` as much as `Copy`.

### One rule, not one per marker

RFC-0224 section 3 defers `Discard`, `Send` and `Sync` to the RFCs that land them, and a derivable aspect added later (`Debug`,
`Eq`, `Hash`, a user's) would otherwise need its own decision. Stating the rule once, in terms of what a derivation is, removes it.

---

## 1. The clause

```
derives_clause = { "derives" ~ derive_entry ~ ("," ~ derive_entry)* }
derive_entry   = { type_path ~ ("(" ~ derive_args? ~ ")")? }
derive_args    = { ident ~ ("," ~ ident)* }              // for the field-wise derivations: type parameters of the declaration
```

- **No parentheses** asks the compiler to compute the arguments (for a field-wise derivation, the smallest sufficient flow).
- **Empty parentheses** state an empty argument list: the impl has no conditions on the declaration's parameters. This is distinct
  from no list, which computes: on a `pub` generic type it is how a phantom parameter is stated (`pub struct Id<T> derives Clone() { n: i64 }`),
  and legality 1 still applies, so `derives Clone()` on a type whose fields hold `T` by value is an error.
- **Parentheses and not angle brackets**, since an aspect's own type arguments (RFC-0228) already use `<>`: `derives Conv<i64>(T)`
  is the derivation of the aspect `Conv<i64>` with the argument `T`.
- **Positional arguments are numeric-label rows** (`.0`, `.1`, RFC-0151) as call arguments are (RFC-0223); a keyword argument is
  an error until a derivation declares a parameter it can bind to (the registration RFC).
- `via` is removed. It is a parse error whose message names the new form ("write `derives Copy(T)`").

## 2. Field-wise derivations

A `derives` entry for an aspect `A` is a *field-wise derivation* when the impl the compiler writes holds at an instantiation
exactly when every field type has `A` there. Its signature is a list of type parameters, the **flow**, and the written impl is

```
extend<P1: A, .., Pk: A, Q1, .., Qm> T<P1, .., Pk, Q1, .., Qm>: A        // P1..Pk is the flow
```

**Legality** (RFC-0224 section 2, restated for `A`).
1. *Sufficient.* The flow must contain every parameter a field's `A` depends on (a parameter, a nominal application through its own
   flow, a tuple or array through its components; a reference depends on nothing).
2. *May be larger.* A parameter the fields do not need may be listed; the type then has `A` only when its argument does.
3. *Type parameters only.* An argument is a type parameter of the declaration, not row- or record-kinded.
4. *Only a derivation that takes arguments.* Arguments on a derivation that declares no parameters are an error ("`Builder` takes
   no arguments"). A derivation that is not field-wise, such as `derives Builder` (draft RFC-0222), has no flow to state.

**What stays with the aspect.** `Copy`'s `declared` grant, its exclusion of `Drop` and `Linear` (RFC-0213), the ban on a negative
grant of `Copy`, and the rule that `Copy` requires a derived `Clone` (RFC-0234) are properties of the aspects' declarations and
apply to every entry whatever its arguments say.

## 3. The `pub` statement

RFC-0224 rule 3: a `pub` generic type that derives `Copy` may omit its flow only when the computed set is empty; otherwise the
omission is an error with a fix-it showing the computed set. Under this RFC the same rule applies to every field-wise derived
impl, for the same reason: a field edit cannot change a public interface silently. In std, `Option<T>`, `Result<T, E>` and the
others write `derives Clone(T), Copy(T)` (or `(T, E)`) where they are `Copy` as well, and `derives Clone(T)` where they are not.
Non-`pub` types keep the computed set.

The rule is the same for every field-wise aspect, not only the ownership aspects: a `pub` generic type's bounds are part of its
interface whichever aspect they bound. A non-generic `pub` type, a non-`pub` type, and a `pub` generic type whose computed flow
is empty (a parameter no field holds by value) are not subject to it.

A derivation that declares its own parameters (the registration RFC) says which of them are subject to this rule, by their type.

## 4. Two entries that share a flow

`derives Clone(T), Copy(T)` states `T` twice. The flows must entail (RFC-0234): `Clone` holds wherever `Copy` does, so a `Clone`
flow larger than the `Copy` flow is an error at the `Copy` impl. A group syntax that states one flow for several aspects is not
introduced: the repetition is short and a second spelling of the list costs more.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep `via` and generalise it to every field-wise derivation (this RFC's earlier form) | A keyword for one argument of one kind of derivation; user derivations need parameters of their own |
| A group `derives (Clone, Copy) via T` | A second spelling for the sake of the repetition `derives Clone(T), Copy(T)` |
| The flow as a list argument (`derives Clone(flow: [T, U])`) | A temporary surface; positional arguments are the final one and need no variadics for compiler-provided derivations |
| Condition clauses (`when`, `if`, `given`) on every derive | The flow is a set of parameters; a condition language invites bounds that are not about the fields (RFC-0224 section 5) |
| Write `extend<T: Clone> W<T>: Clone` by hand | Loses the derivation: the body is written by the compiler (the native field-wise clone) |
| `via` on any `derives` entry | Meaningless for a template derivation such as `Builder` |

---

## Relationship to existing RFCs

- **RFC-0224** (integrated). Its `via` clause is replaced by section 1; its rules 1 to 3 and 9 are unchanged and become section
  2's legality and section 3 for `A = Copy`. Rules 6 to 8 (row-kinded parameters of a `Copy`, negative grants, `Drop`) stay `Copy`
  rules.
- **RFC-0207** (implemented). The `derives` clause gains optional arguments on an entry.
- **RFC-0212** (integrated). `derivable` is a property of the aspect; defining what a derivation is, and who may provide one, is
  the registration RFC's.
- **RFC-0234** (under review). `Copy` requires a derived `Clone`; its flow entailment (section 4 here) applies to arguments.
- **RFC-0093** (under review). Its request half is the clause; its registration half is not decided here.
- **RFC-0222** (draft). `derives Builder` is the counterexample that bounds legality 4.
- **RFC-0228** (under review). Aspect type arguments use `<>`, which is why derivation arguments use `()`.

---

## Open questions

None known.

---

## Implementation notes

Replace the `via` production with the derive entry's optional argument list; lift the `Copy`-only guard in the clause expansion's
flow check (`check_flow`) and give `Clone` a stated flow; widen the `pub` check (#1820's rule) to every field-wise derive; rewrite
the existing `via` uses (38 lines in 30 fixture files at the time of writing, and about 14 mentions in the spec) mechanically.

---

## Decision

**Outcome:** *(pending)*
