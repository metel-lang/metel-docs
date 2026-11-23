---
id: rfc-0246
title: "Derivation arguments: the flow parameter, mixed arguments and the computed rest"
date: '2026-11-23'
status: under-review
updated: '2026-11-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/2172'
---

> **Status — under review (2026-11-23).** Taken to review as part of the metel-core v0.17.0 plan (#2172)

## Summary

`derives A(args)` is a call: its arguments bind to the `Args` of `A`'s `Derivable` impl (RFC-0238 section 2). This RFC states how, for the
case RFC-0238 leaves open: a derivation that takes a flow **and** other arguments. Three points:

1. A flow entry is a **type parameter of the declaration**, a comptime value of kind `type` that names one of `Target`'s own generic
   parameters. The type of a flow is a row of them.
2. `Flow` is a **trailing positional parameter**. Leading positional arguments bind to the leading numeric labels of `Args`, the
   flow collects the positionals after them, and named labels are keyword arguments, as in RFC-0223.
3. **`..` is the computed flow**, a value like any other flow: `derives Clone(..)`. It replaces the postfix `?` that RFC-0244 put on a
   `derives` entry, which is not an argument and so does not fit the call. The class keyword keeps its mark: `copy?` is
   `derives Clone(..), Copy(..)`.

```metel
extend Serialize: Derivable {
    type Args = .{ .0: String, .rename_all: String = "none", ..Flow };
    comptime fun derive(Target: type, args: Self::Args) -> Decl { /* .. */ }
}

struct Pair<A, B> derives Serialize("pair", A, B)                     { a: A, b: B }  // .0 = "pair", flow = (A, B)
struct Item<T>    derives Serialize("item", rename_all = "camel", T)  { v: T }        // keyword and flow
struct Slot<T>    derives Clone(..)                                   { v: T }        // computed flow
struct Tag<T>     derives Serialize("tag")                            { n: i64 }      // empty flow, the default
```

This is a design draft. It amends RFC-0244 (the `?` mark on an entry), refines RFC-0238 sections 1 to 3 and extends the argument list of
RFC-0227.

---

## Motivation

1. **`derives A?` is not a call.** RFC-0238 makes `derives A(args)` a call to a comptime function whose arguments are checked against a
   parameter row. A postfix `?` is a second mechanism beside the arguments: RFC-0238 section 2 has to special-case it ("the mark
   after the aspect name decides the `Flow` parameters"), and it has no answer for a derivation with two `Flow` parameters or none.
   If "computed" is a value, the call needs no special case.
2. **RFC-0238 does not say how a flow shares `Args` with other arguments.** Positional arguments are numeric labels (`.0`, `.1`), and
   `Flow` is "a row of positional type parameters of any width", so it claims every numeric label. `.{ .0: String, ..Flow }` has two
   `.0`s, and `derives A(T, "x")` has nowhere to put `"x"`. Std needs nothing more than a bare `Flow` (`Clone`, `Copy`), so the gap
   has not mattered. The first user aspect that takes a flow and a name will hit it.
3. **The element type of a flow is not named.** RFC-0238 calls the elements "type parameters of `Target`". A deriver must be able to
   read them (`typeinfo(Target)`), and the checker must reject `derives Clone(i64)`, which names no parameter. That needs a type.

---

## Proposal

### 1. What a flow entry is

In `struct S<T, U> derives A(T)`, the argument `T` is resolved in the declaration's generics scope. It is a comptime value of kind
`type`, restricted to the generic parameters of the declaration being derived; call the type of such a value `TypeParam<Target>`.

- `derives Clone(i64)` and `derives Clone(V)` for a `V` that is not a parameter of the declaration are errors (`T0046`, "names no
  type parameter of this declaration"), as RFC-0227 says today.
- A parameter of row or record kind is not accepted (RFC-0224 rule 7), as today.
- A deriver reads an entry through `typeinfo(Target)`, whose list of generic parameters the entries are drawn from.

`Flow` is the type of a row `.{ .0 = P, .1 = Q, .. }` of such values, of any width. Its meaning is fixed: the parameters the emitted impl
is **conditional on**, that is, the parameters `P` for which the impl carries the bound `P: A`.

### 2. Binding

`<A as Derivable>::Args` is a row. Numeric labels are positional parameters, named labels are keyword parameters, and a label with a
default is optional (RFC-0238 section 1, RFC-0223). This RFC adds one form of row tail:

> `..Flow` at the end of a row type contributes the flow. Its entries are the positional labels that **follow** the numeric labels
> declared before it: in `.{ .0: String, ..Flow }` the first flow entry is `.1`.

At most one `..Flow` may appear in an `Args`, and it is the last of the positional labels by construction. Named labels may appear
anywhere, as in any row. A call binds as RFC-0223 says:

1. Positional arguments bind to the declared numeric labels in order, then the rest are the flow entries.
2. Keyword arguments bind named labels; a keyword that binds no label is an error (as `T0039`), and a positional after a keyword is an
   error (as `T0040`).
3. A label with a default may be omitted. An omitted flow is the **empty** flow (RFC-0244).

So, for `Args = .{ .0: String, .rename_all: String = "none", ..Flow }`:

| Clause | Binds |
|---|---|
| `derives A("x", T, U)` | `.0 = "x"`, flow `(T, U)` |
| `derives A("x", rename_all = "camel", T)` | `.0 = "x"`, `.rename_all = "camel"`, flow `(T)` |
| `derives A("x")` | `.0 = "x"`, empty flow |
| `derives A(T, "x")` | error: `T` is not a `String`, and `"x"` is not a type parameter. The message says the leading positional arguments come before the flow. |
| `derives A` | error: `.0` has no default ("`A` requires arguments") |

A flow always comes after the leading positionals. That is the cost of one rule instead of a type-directed one (see Alternatives).

### 3. `..` is the computed flow

`..` as the **last entry of the flow** (and, in this RFC, the only entry; question 1) is the flow the compiler computes: the smallest
set of parameters such that every field's `A` holds under the impl's bounds (RFC-0227's dependence analysis, applied to the aspect
being derived). It is a value of type `Flow`, resolved by the compiler **before** `derive` runs, so a deriver always receives a
concrete row and never sees `..`.

- `derives Clone(..)` and `derives Copy(..)` are the computed forms of RFC-0227 and RFC-0244. A bare `derives Clone` is the empty flow, as in
  RFC-0244.
- `..` is accepted only in a `Flow` position, and an `Args` with no `Flow` rejects it ("`A` takes no flow"). This replaces RFC-0244's
  error for `?` on a derivation with no `Flow` parameter.
- The `pub` rule of RFC-0227 applies to `..` as it applied to `?`: a `pub` generic type may use it only when the computed set is
  empty, and otherwise states the flow.

### 4. The class keyword

`copy` is `derives Clone, Copy`, and `copy?` is `derives Clone(..), Copy(..)`. The keyword takes no argument list (RFC-0244), so `?`
survives only on the keyword, as one character of sugar for a pair of entries. An explicit `derives Clone(T)` beside `copy?` replaces
the keyword's `Clone` entry and leaves its `Copy` computed, as in RFC-0244 section 3.

### 5. What changes in the implemented specification

- RFC-0244 sections 1 and 2: the `?` suffix on a `derives` entry is replaced by `(..)`. Meaning, error cases and the `pub` rule are
  unchanged. The grammar loses `derive_query` from `derives_clause`, and `derive_args` accepts a lone `..`.
- RFC-0227: the argument list of a field-wise derivation may be the single entry `..`.
- RFC-0238 section 2: the clause on marks goes. Section 1 gains the `..Flow` row tail, and section 3 names `Flow` as the trailing
  positional parameter.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep `derives A?` as RFC-0244 has it | A postfix mark outside the call. It cannot say which `Flow` parameter it applies to when there are two, and RFC-0238 section 2 has to special-case it. |
| The flow is a keyword parameter only: `derives A(flow = (T, U), name = "x")` | Unambiguous, but it makes the common case, `derives Clone(T)`, longer, and needs a sugar rule to get the short form back. |
| Gather every positional argument that is a type parameter into the flow | Type-directed: which parameter an argument binds to depends on what it is. A derivation that wants a `type` argument for another purpose is ambiguous with a flow entry. |
| The flow first, other arguments after | The width of the flow is unbounded, so the boundary between flow and the leading positionals cannot be found without types. A trailing flow has a fixed start. |
| A value `computed` in place of `..`: `Clone(flow = computed)` | A new keyword and a keyword argument for the one thing every field-wise derivation does. `..` already means "the rest" in rows and patterns. |
| `derives A[T]` for the flow | `[]` is held by RFC-0050. |
| `copy(..)` for the keyword form | It brings back the argument list RFC-0244 removed from the keyword, which reads as an argument to `copy`. `copy?` stays. |

---

## Interaction with other work

- **RFC-0227** (implemented): defines the argument list and the flow. This RFC adds `..` to the list and names the entry type.
- **RFC-0244** (implemented): replaces its `?` on an entry with `(..)`. Its default (empty flow), the `pub` rule, `copy?` and the
  error for a bare entry whose field needs a parameter stay, with the fix-it naming `derives A(..)`.
- **RFC-0238** (under review): this RFC supplies the binding rule it lacks. It should adopt sections 1 to 3 here, or be amended with
  them when accepted. Std's `Clone` and `Copy` take a bare `Flow` and are unaffected. RFC-0238's examples write a keyword argument
  `rename_all: "camel"`, while RFC-0223 writes `name = value`; this RFC uses RFC-0223's form, and RFC-0238 should follow.
- **RFC-0223** (implemented): the binding rules are its rules. A derivation clause is the one call whose parameter list is a row.
- **RFC-0125, RFC-0151** (row types): the `..Flow` tail renumbers positional labels after the declared ones, which RFC-0125 says is not
  built and not yet decided (question 3).
- **RFC-0247** (draft): variadic parameters. A rest parameter would give a flow after leading positionals without renumbering a row.
- **RFC-0237, RFC-0092, RFC-0132** (comptime, aspects as values): `TypeParam<Target>` and `typeinfo(Target)` live there.

---

## Costs

- **Respelling an implemented form.** v0.17.0 implements `derives A?` (metel-core#2153). If this RFC is accepted before the release,
  the respelling is mechanical (`derives X?` becomes `derives X(..)`, a rewrite of about two dozen declarations and the spec rules);
  after the release it is a breaking change.
- **A row tail with renumbering.** `..Flow` after declared positionals numbers its entries from the next label. RFC-0125 records that
  positional renumbering of a row is not built and that how to write it is undecided (its designs A, B and C), so this is not a small
  extension. A `Flow` that is the **only** positional entry (`Args = Flow`, which is all std's `Clone` and `Copy` need) renumbers
  nothing and is unaffected. A flow after leading positionals needs RFC-0125's answer, or a rest parameter (RFC-0247).
- **A flow must come last among the positionals.** `derives A(T, "x")` is an error, and the message has to say why.
- **Two spellings of one idea.** `copy?` keeps a mark that `derives` no longer has. It is keyword sugar and expands to the call form,
  so a reader of the expansion sees only `(..)`.

---

## Open questions

1. **Is `(A, ..)` accepted?** It would mean "at least `A`, plus whatever the fields need". It follows from `..` being the last entry of a
   flow, but it is a new capability with its own `pub` rule: such a type could grow its flow silently unless the computed part is a
   subset of the stated one. Recommendation: accept only a lone `(..)` now, and leave `(A, ..)` for a later RFC. This text then says
   `..` is the whole flow.
2. **The name and definition of the entry type.** `TypeParam<Target>` is a placeholder. It needs RFC-0092's `typeinfo` to say how a
   deriver lists and compares the generic parameters of `Target`.
3. **Renumbering row tail, or a rest parameter?** RFC-0125 says renumbering a row is unbuilt and undecided, so the row tail of section 2
   depends on its answer. A rest parameter (RFC-0247) keeps rows unchanged and adds one notion to parameter lists. Recommendation: land
   the form without leading positionals now (`Args = Flow`, which needs no renumbering), and let the mixed form wait for RFC-0125 or
   RFC-0247, whichever is accepted first.
4. **Two flows.** May an `Args` have more than one `Flow`, for a derivation conditional on two groups of parameters? The positional
   split is then undefined. Recommendation: at most one, and a second group is a keyword parameter of `Flow` type.
5. **What does `..` mean for a derivation that is not field-wise?** The computed flow is defined by the field dependence of the aspect
   being derived. A user derivation that takes a `Flow` for another purpose has no such definition. Recommendation: `..` is legal only
   for a `Flow` that is the flow of the emitted impl, which section 1 already states as the meaning of the type.
6. **Keep `copy?`?** The alternative is no keyword mark: conditional types write `derives Clone(..), Copy(..)`, and `copy` means
   unconditional only. That is one rule, and it is longer for a common case. Recommendation: keep `copy?`.

---

## Decision

**Outcome:** *(pending)*
