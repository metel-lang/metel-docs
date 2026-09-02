---
id: rfc-0165
title: "Structural Union Types"
date: '2026-09-02'
status: under-review
target:
updated: '2026-09-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/937'
---

> **Opened 2026-09-02 from RFC-0154's adversarial review (F11).** RFC-0154 makes `|` a
> delimiter in type position (`|A| -> B`). Its "Grammar: the `|` wrinkle" section reserves
> the question of a future `A | B` union spelling and says a later RFC "must reconcile
> them." This is that RFC. It records the spelling reconciliation (§1, close to settled)
> and the semantic design space; the load-bearing question — tagged vs untagged (Open
> Question 1) — is unresolved, which is why this is `1-under-review` and **not scheduled**
> (no milestone). Tracking: metel-core#937.

> **Status — under review (2026-09-02).** spelling reconciliation with RFC-0154 recorded; OQ1 (tagged vs untagged) is the open decision

## Summary

Add an **anonymous sum-type former**, written `A | B | C` — a value that is exactly one of
several types, tagged, with no named declaration. It is the coproduct dual of RFC-0116's
anonymous record types (`{ x: A, y: B }`) and RFC-0151's tuples (`(A, B)`); today Metel
has structural *products* without a name but only *nominal* sums (`enum`). The spelling
`|` coexists with RFC-0154's pipe notation by the same operand-vs-operator position rule
that already separates `|| expr` from `a || b`.

## Motivation

Metel already has:

- **Nominal sums** — `enum Shape { Circle(f64), Rect(f64, f64) }` (spec
  `declarations.md#enums`, RFC-0034 / RFC-0107 / RFC-0111). Every alternative and the type
  as a whole must be *declared and named* before use.
- **Anonymous products** — `{ x: A, y: B }` (RFC-0116), `(A, B)` (RFC-0151, `0-draft`).
  Written inline, structurally identified, no declaration.

The gap is an **anonymous sum**. Cases where declaring an `enum` is pure ceremony:

```
fun parse_token(s: String) -> Number | Ident | Punct { … }   // three existing types, no new name wanted
fun lookup(k: Key) -> Value | NotFound { … }
type Json = Null | Bool | Number | String | Json[] | { String: Json };   // RFC-0160 alias over a union
```

Every mainstream structural type system has this — TypeScript `A | B`, Flow, Scala 3
`A | B`, Python `A | B` (PEP 604), Kotlin's planned union return types. It is also what a
`Result`-free error-return style needs (`T | ParseError`), and the natural target for a
future `Perhaps<T>` / `Result<T, E>` desugaring question (Open Question 6).

RFC-0154 forces the spelling question now: after it lands, `|` means "closure/function
delimiter" in type position. If a union is ever wanted, its spelling has to be settled
against that, or `|` is spent.

## Proposal

### 1. Spelling and grammar

```
union_type = { type_no_union ~ ("|" ~ type_no_union)+ }
```

`A | B | C`. Rules, all positional — no lexer state, no backtracking:

1. **Infix only. No leading or trailing `|`.** `A | B`, never `| A | B` (unlike OCaml /
   Rust `enum` bodies). This is the whole reconciliation with RFC-0154: a `|` at the
   *head* of a type position — or after `->`, `,`, `(`, `[`, or a `once` / `var` / `&`
   qualifier — is always RFC-0154's function-type delimiter; a `|` with a complete type to
   its **left** is always union. Exactly the `|| expr` vs `a || b` rule (RFC-0154 §"the `|`
   wrinkle"), one level up in the grammar.
2. **Union binds looser than `->`.** `|A| -> B | C` is `(|A| -> B) | C`, matching
   TypeScript and Scala 3. `A | B | C` is flat — `|` is associative.
3. **A function type as a union *member* is parenthesised.** `(|A| -> B) | C`. Without the
   parens, rule 2 makes `|A| -> B | C` mean `(|A| -> B) | C` in return position but there
   is no unambiguous reading for "a function returning `B | C`" — write `|A| -> (B | C)`.
   Requiring the parens on a function-type member removes the guess; this is a hard rule,
   not the advisory treatment RFC-0154 §5 gives ordinary nesting.
4. **A union as a bare function-type parameter or return is parenthesised by
   convention.** `|(A | B)| -> C`, `|X| -> (A | B)`. `|A | B| -> C` does parse (the inner
   `|` is operator position, the outer two are delimiters) but reads badly — same
   readability recommendation, and same non-enforcement, as RFC-0154 §5.

`||` in type position stays unambiguously the nullary function type: a union needs two
members and has no leading bar, so there is no "empty union" spelling to collide with.
Inside `<…>`, after `as`, in a `let` annotation — `|` resolves by the same left-operand
test everywhere.

### 2. Semantics — a tagged structural coproduct *(lean)*

`A | B` is a value that is **exactly one of** `A` or `B`, carrying a **tag** that says
which. It is *not* a set-theoretic "A or B" with runtime type tests (that is the untagged
alternative — see Alternatives). Concretely:

- A value of type `A` coerces into `A | B` by wrapping with the `A` tag; likewise `B`.
- Eliminating a `A | B` is a `match` on the tag, one arm per member; the compiler checks
  exhaustiveness against the member list.
- Representation is an implementation choice (tag + max-payload, like an `enum`); no RTTI,
  no vtable, compatible with monomorphisation.

This makes `A | B` behave as an **anonymous, structurally-identified `enum`** whose
variants are keyed by their member *type* rather than by a declared name.

### 3. Type identity

Two union types are the same type iff they have the same **set** of members:

- **Commutative** — `A | B` ≡ `B | A`.
- **Associative / flattening** — `(A | B) | C` ≡ `A | (B | C)` ≡ `A | B | C`.
- **Idempotent** — `A | A` ≡ `A`; `A | B | A` ≡ `A | B`. A one-member union is just that
  type (`A | A` collapses before it is ever a union).
- **`!` absorbs** — `A | !` ≡ `A` (the never type, spec `types.md`, has no values to tag).

"Same member" is type equality *after* alias expansion (RFC-0160) and normalisation. This
is the crux tension with §2's tagging: if members are keyed by type, `A | A` cannot be a
two-payload thing — it must collapse. See Open Question 3 for `A | B` where a generic
instantiation makes `A` and `B` equal.

### 4. Construction and elimination

**Construction** is implicit widening at a coercion site (assignment, argument, return,
`match`-arm result), the same shape as RFC-0152's function-multiplicity widening:

```
fun classify(n: i64) -> Even | Odd {
    if n % 2 == 0 { Even { n } } else { Odd { n } }   // each branch widens to Even | Odd
}
```

An explicit form (`(x as A | B)`) is available where inference has nothing to drive it.

**Elimination** is `match` with a type pattern per member:

```
match tok {
    Number(v) => …,
    Ident(s)  => …,
    Punct(c)  => …,
}
```

Exhaustiveness is checked against the member list; `!`-typed members may be omitted (spec
`types.md` uninhabited-variant rule). Whether a bare `is`/`as` narrowing (RFC-0109) also
eliminates a union, or only `match`, is Open Question 4.

### 5. Relationship to nominal `enum`

`enum` stays. It is the tool when the alternatives want **names**, **methods**
(`extend`), **recursion through the type's own name**, or a **closed public contract**. A
structural union is the tool when the members are *existing types* and a name would be
noise. An `enum` is **not** a subtype of, and does not implicitly convert to, a union of
its payloads — they are different types with different identity rules. A `type` alias
(RFC-0160) over a union gives it a name without giving it nominal identity.

### 6. The never type and option/result shapes

`!` is the identity element (§3). This RFC does **not** propose redefining `Perhaps<T>` or
`Result<T, E>` as `T | None` / `T | E` — those are nominal today and carry methods
(`?`, `.map`, …). Whether a future RFC re-expresses them structurally is Open Question 6;
this RFC only needs to not *preclude* it.

### 7. Subtyping and widening

`A` is coercible to `A | B` (member → union). `A | B` is coercible to `A | B | C`
(union → wider union). `A | B` is **not** coercible to `A` (no narrowing without a
`match`). This is a join semilattice on the member-set order, and it is the same
"more-permissive target accepts less-permissive source" direction RFC-0152 uses — a union
RFC should state explicitly how the two lattices compose when a union member is itself a
function type.

## Interactions

- **RFC-0154 (Pipe Notation), `1-under-review`** — the trigger. This RFC's rule 1 is the
  reconciliation RFC-0154 §"the `|` wrinkle" defers. If RFC-0154 does not land, `A | B`
  competes with nothing and rules 2–4 are the only content.
- **RFC-0116 (Anonymous Record Types)** — the product this is the coproduct of; identity
  and coercion rules should mirror RFC-0116's structural treatment where they can.
- **RFC-0151 (Tuples as Numeric-Label Rows), `0-draft`** — same family; `(A, B) | C` and
  `(A | B, C)` are both well-formed and distinct.
- **RFC-0160 (Type Aliases), `1-under-review`** — `type Json = … | …;` is the expected way
  to name a recursive or wide union; alias expansion happens *before* union normalisation
  (§3).
- **RFC-0107 / RFC-0111 (unqualified enum variants in patterns / expressions)** — `match`
  on a structural union reuses the pattern machinery; the arm patterns are *type*
  patterns, not variant paths.
- **RFC-0109 (Self-View Narrowing)** — Open Question 4: does narrowing eliminate a union,
  or only `match`?
- **RFC-0034 (struct / enum Aspect bounds)** — a union satisfies an aspect bound iff
  *every* member does (à la an intersection of the members' impls); needs its own rule.
- **RFC-0080 (Send / Sync), `1-under-review`** — a union is `Send` / `Sync` iff every
  member is.
- **Monomorphisation** — §2's tagged representation is deliberately vtable-free so this
  does not force RTTI into the runtime.

## Alternatives considered

### Untagged set-union with type tests (TypeScript's model)

`A | B` is "a value that is an `A` or a `B`", eliminated by `is`/`as` type tests at
runtime. No wrapping on construction (`A` *is already* a `A | B`). Rejected as the lean
because it needs runtime type information for the tests, interacts badly with
monomorphisation and with `A | A` (indistinguishable members), and makes `i64 | i64` or
`Cat | Animal` (where `Cat <: Animal`) ill-defined. Kept as an option because it is the
zero-construction-cost model and matches the largest existing ecosystem.

### A keyword spelling — `union<A, B>` / `A or B`

Sidesteps the `|` question entirely. `+` is unavailable (RFC-0039 / RFC-0061 aspect
bounds). `union<…>` reads as a generic and is verbose; `or` as a type operator is
unusual. Only worth it if rule 1 proves too subtle in practice.

### No anonymous sums — `enum` only

The status quo. Every sum type is declared. Rejected by the Motivation cases, but it is
the "do nothing" baseline and RFC-0154's `|` reconciliation still has to be written down
even under it (as "`A | B` is reserved / a parse error, pending this RFC").

### Allow a leading `|` when parenthesised — `(| A | B)`

A distinct opener `(|` could permit OCaml-style leading bars for formatting. Marginal
benefit, another special form. Rejected.

## Open Questions

1. **Tagged (§2) vs untagged (Alternatives).** The load-bearing decision; everything else
   flexes around it. Lean: tagged, for monomorphisation and `A | A` sanity.
2. **Construction ergonomics.** Implicit widening at every coercion site (§4), or an
   explicit wrap required at least sometimes? Implicit matches records/tuples; explicit is
   clearer about the tag cost.
3. **Generic members that collapse.** `fun f<T, U>(…) -> T | U` instantiated at `T == U`:
   is the result `T`, or a two-tag union that happens to hold the same type twice? §3 says
   collapse; that means a generic union's arity is not statically fixed. Consequence for
   `match` exhaustiveness needs working out.
4. **Elimination surface.** `match` only, or also `is` / `as` narrowing (RFC-0109)? If
   narrowing, does it need the tagged representation to expose a discriminant?
5. **Ordering vs `->` and `&`.** Rule 2 sets union looser than `->`. Where does it sit
   relative to `&T` / reference types, `T[]`, and generic application `F<T>`? Full
   precedence table pending.
6. **`Perhaps` / `Result`.** Does this RFC's landing create pressure to re-express them as
   `T | None` / `T | E`, and should it pre-empt that by saying explicitly it does not?
7. **Exhaustiveness and `_`.** Is a wildcard arm allowed on a structural-union `match`, or
   is it always fully enumerated (the member list is right there in the type)?
8. **Diagnostics.** A missing `match` arm names a *type*, not a variant path — message
   wording, and how it reads when a member is itself a union or a function type.

---

## Decision

**Outcome:** *(pending — `1-under-review` (metel-core#937), opened 2026-09-02 from
RFC-0154's F11. The `|` spelling reconciliation (§1) is close to settled; the
tagged-vs-untagged semantics (Open Question 1) is the open decision that blocks
acceptance, and seven further open questions flex around it.)*
**Target:** *(none — not scheduled; the spelling reconciliation only matters once RFC-0154
lands, and Open Question 1 needs a decision before this is more than a sketch. The
tracking issue is deliberately unmilestoned.)*
