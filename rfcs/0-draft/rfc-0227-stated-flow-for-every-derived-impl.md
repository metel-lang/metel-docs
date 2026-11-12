---
id: rfc-0227
title: "Stated flow for every derived impl"
date: '2026-11-12'
status: draft
---

## Summary

RFC-0224 lets a `derives Copy` entry state which type parameters its copy-ness flows from, `derives Copy via A + B`,
and restricts the clause to `Copy` (its section 1 and 3). This RFC states the general rule that clause is a case of:

> A derivation is the compiler writing an ordinary conditional impl. `derives A via P + Q` means
> `extend<P: A, Q: A, R> T<P, Q, R>: A`, with a body the compiler writes. `via` chooses which type parameters carry
> the bound.

The rule applies to every `derives` entry whose derivation is field-wise (every type parameter a field holds by value
has the aspect), which today means `Copy` and `Clone` and, when comptime lets a user declare one, any `derivable`
aspect that makes the same promise. The properties of `Copy` stay with `Copy`: its exclusion of `Drop`, the ban on
a negative grant, and the rejection of row-kinded parameters belong to the aspect's declaration, not to `via`.

```metel
struct Pair<A, B> derives Clone via A + B { a: A, b: B }           // Pair<X, Y>: Clone when X and Y are
struct Tagged<T> derives Clone via T { id: i64 }                    // Clone only when T is, whatever the fields become
struct Wrapper<T> derives Copy via T, Clone { value: T }            // Copy via T; the Clone it brings has the same flow
```

This is a design draft. Nothing here is accepted, and RFC-0224's implementation (metel-core#1941) keeps `via` on
`Copy` only until this RFC is decided.

---

## Motivation

### The restriction is a scope choice, not a rule

RFC-0224 section 1 allows `via` on `Copy` alone because `Copy` was the case that had lost something (RFC-0206's
stored condition). Nothing in the mechanism is specific to it:

- The derived impl already bounds each parameter a field holds by value by the derived aspect itself
  (`impl_generics` in the clause expansion). `via` only replaces the computed set of bounded parameters with a stated one.
- The sufficiency rule (the stated set must contain every parameter a field depends on, and may contain more) names no aspect.
- The only `Copy`-specific code is one guard that rejects `via` on another entry, and the rules that come from
  `Copy`'s own properties.

### What a `Clone`-only type cannot do today

`derives Clone` on a generic type bounds every parameter a field mentions by `Clone`. A type cannot say that it is
`Clone` only when a smaller set of parameters is, so a public generic type's interface moves with its fields, which
is the reason RFC-0224 makes a `pub` type state its `Copy` flow. `Option`, `Result` and `List` in std are exactly this
case. The over-approximation of a nested nominal field (metel-core#1938) affects `Clone` as much as `Copy`.

### One rule, not one per marker

RFC-0224 section 3 defers `Discard`, `Send` and `Sync` to the RFCs that land them, and a derivable aspect added later
(`Debug`, `Eq`, `Hash`, a user's under RFC-0092) would otherwise need its own decision. Stating the rule once, in terms
of what a derivation is, removes the decision.

---

## 1. The rule

**Definition.** A `derives` entry for an aspect `A` is a *field-wise derivation* when the impl the compiler writes holds
at an instantiation exactly when every field type has `A` there. For such an entry the **flow set** is the set of type
parameters on whose `A` the impl depends, and the written impl is

```
extend<P1: A, .., Pk: A, Q1, .., Qm> T<P1, .., Pk, Q1, .., Qm>: A        // P1..Pk is the flow set
```

`via P1 + .. + Pk` states the flow set; omitting it asks the compiler to compute the smallest sufficient set from the
fields. This is RFC-0224 section 1 with `Copy` replaced by `A`.

**Legality** (RFC-0224 section 2, restated for `A`).
1. *Sufficient.* The stated set must contain every parameter a field's `A` depends on (a parameter, a nominal
   application through its own flow, a tuple or array through its components; a reference depends on nothing).
2. *May be larger.* A parameter the fields do not need may be listed; the type then has `A` only when its argument does.
3. *Type parameters only.* A name after `via` is a type parameter of the declaration, not row- or record-kinded.
4. *Field-wise derivations only.* `via` on an entry whose derivation is not field-wise is an error.

**What stays with the aspect.** `Copy`'s `declared` grant, its exclusion of `Drop` and `Linear` (RFC-0213), the ban on
a negative grant of `Copy`, and the provided `Clone` are properties of `Copy`'s declaration (RFC-0212) and apply to
every `Copy` entry whatever `via` says. `Clone` has none of them.

---

## 2. Brought super-aspects

`derives Copy` also derives the `Clone` that `Copy` marks `deriving` (RFC-0213 section 4), under the same condition. The
brought entry takes the flow of the entry that brought it, so `Wrapper<X>: Clone` holds when `X: Copy`, exactly as in
RFC-0224 section 3. When an explicit entry names the same aspect as a brought one:

- an explicit entry that states no flow adopts the brought flow;
- two stated flows must be equal sets, or the declaration is an error naming both (one condition under which
  `T: Copy` proves `T: Clone`).

---

## 3. The `pub` statement

RFC-0224 rule 3: a `pub` generic type that derives `Copy` may omit `via` only when its computed set is empty; otherwise
the omission is an error with a fix-it showing the computed set. Under this RFC the same rule applies to every field-wise
derived impl, for the same reason: a field edit cannot change a public interface silently. In std, `Option<T>`,
`Result<T, E>` and the others that derive `Clone` write `derives Clone via T` (or `via T + E`). Non-`pub` types keep the
computed set.

---

## 4. What a field-wise derivation is not

Not every `derives` entry is field-wise. `derives Builder` (draft RFC-0222) makes the struct's row visible to a row
template; there is no impl bounded parameter by parameter and no flow set to state. Such a derivation is not
`derivable` in the sense of section 1, and `via` on it is an error (legality 4). The decision is whether that boundary
is drawn by definition (open question 1) or by a declared property.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep `via` on `Copy` only (RFC-0224 as written) | One special case per marker; a `Clone`-only public type cannot pin its interface |
| `via` on any `derives` entry | Meaningless for a template derivation such as `Builder` |
| Condition clauses (`when`, `if`, `given`) on every derive | The flow is a set of parameters; a condition language invites bounds that are not about the fields (RFC-0224 section 5) |
| Write `extend<T: Clone> W<T>: Clone` by hand | Loses the derivation: the body is written by the compiler (the native field-wise clone) |

---

## Relationship to existing RFCs

- **RFC-0224** (integrated). Sections 1 and 3 say `via` is accepted on `Copy` only and defer the other markers; this RFC
  would replace that restriction with the rule of section 1. RFC-0224's rules 1 to 3 and 9 are unchanged and become the
  `A = Copy` case. Its rules 6 to 8 (row-kinded parameters of a `Copy`, negative grants, `Drop`) stay `Copy` rules.
- **RFC-0207** (integrated). The `derives` clause gains the optional `via` list on any field-wise entry.
- **RFC-0212** (integrated). `derivable` would be defined as: the compiler writes an impl bounded parameter by parameter
  by the aspect itself. A derivation that is not (a row template) needs its own property when it arrives (RFC-0222).
- **RFC-0213** (integrated). Brought supers keep the flow of the entry that brought them (section 2).
- **RFC-0222** (draft). `derives Builder` is the counterexample that bounds the rule (section 4).

---

## Open questions

1. **Where is the field-wise boundary drawn?** By definition: `derivable` means field-wise, and a template derivation gets
   its own property later. Or by a declared property on the aspect (`structural`), accepted by `via`. Recommended: by
   definition, because no template derivation exists yet and a property whose only users are `Copy` and `Clone` costs
   a declaration for nothing.
2. **Does the `pub` statement (section 3) widen to every derived impl, or only to the ownership aspects?** Recommended:
   every field-wise derived impl; std's three or four public derives gain a `via`.
3. **Duplicate flows (section 2).** Recommended: equal sets or an error; an unstated explicit entry adopts the brought flow.
4. **User-declared derivables.** Once comptime lets a user supply a derivation (RFC-0092, RFC-0093), who checks that it is
   field-wise? Not decided here; the answer belongs with those RFCs.

---

## Decision

**Outcome:** *(pending)*
