---
id: rfc-0163
title: "Function-Type Use-Multiplicity Surface"
date: '2026-09-02'
status: accepted
target: v0.13.0
updated: '2026-09-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/936'
---

> **Status — accepted (2026-09-02).** Design settled: bare function types erase
> use-multiplicity, `copy` is the positive assertion. Alternatives A–D weighed; an
> adversarial pass the same day added the literal-`copy` diagnostic, RFC-0162
> disjointness, the Migration section, and the nested-`copy` integration example.
> RFC-0155 (higher-order variance, unscheduled) is scoped out and unweakened.

> **Status — accepted, spec-review pass (2026-09-03).** A second adversarial pass
> (F1–F12) hardened the proposal without reopening the outcome:
> - **Erasure is first-order only.** Below the first function-type level the use
>   axis joins `once` / `var` as an *exactly*-matched axis — no erasure, no
>   `copy`↔bare in either direction. This removes any conflict with RFC-0152 and
>   leaves RFC-0155's variance question untouched (F1, F5).
> - **`Erased` is defined against `Move`** as the precision-loss top of the use
>   lattice — callable and movable, never copyable, never provably move-only — and
>   MUST NOT be collapsed into `Move` (F4). The directional table is made total
>   over `Erased`, including joins and generic instantiation (F3, F6).
> - **`copy` names the `use_multiplicity` field, not a new axis** (F2); RFC-0162
>   is untouched. *(The second pass briefly tied `copy` to an `F: Copy` bound; the
>   fourth pass retracts that — see below.)*
> - Generics section added (F7); Migration hardened (F8); literal-`copy`
>   diagnostic given a class and message (F9); `copy` reservation fallout
>   enumerated with a `native_path` carve-out (F10); integration examples
>   rewritten as a per-row fixture checklist (F11); a single-directional-relation
>   implementation constraint added (F12).
>
> **Third pass (2026-09-03, G1–G8) reframed the trigger and closed the gaps the
> second pass opened:**
> - **Erasure is a *coercion into a written bare function type*, not a syntactic
>   position.** A generic type variable, an unannotated `let`, an unannotated
>   aggregate literal, and a closure capture write no function type and so do not
>   erase — the concrete `Copy` / `Move` from RFC-0134 is preserved (G3, G4, G5).
> - **Inferred joins take the information-lattice LUB** — `Copy ⊔ Copy = Copy`,
>   `Move ⊔ Move = Move`, mixed/`Erased` `= Erased` — so a homogeneous move-only
>   join keeps its future exact-`move` proof (G1). A join reaching a *written*
>   type is a coercion instead.
> - **Classification is after full alias expansion** (G8); the nested-exact rule
>   now names its acknowledged higher-order limitation and its first-order
>   erasing-adapter bridge (G2).
> - **`Erased ≠ Move` is a representation invariant**, source-unobservable in
>   v0.13.0; `4-implemented` backs it with an implementation-level assertion, or
>   defers the normative distinction until exact `move` (G6).
> - **Migration uses the move checker's CFG-aware consumed-place analysis**, not a
>   textual "used twice" count, and calls out post-elaboration copies as a
>   separate obligation (G7). The erased-non-copy guarantee is stated **under move
>   checking**; every fixture sets `move_check = true` (Part C).
>
> **Fourth pass (2026-09-03, H1–H8) closed the last core-semantics gaps:**
> - **`copy` is a requirement on the function type, not an aspect bound.** Per
>   RFC-0134 a function value satisfies no value aspects — there is no `F: Copy`
>   route to a duplicable callback, and a generic body cannot ascribe an
>   unconstrained `F` to a function type. All `F: Copy` claims are removed (H1, H6).
> - **"Written" is a `WrittenFunctionBoundary` provenance marker** over the
>   expected-type AST, surviving alias expansion and associated-type resolution —
>   not inferred from the final `Type::Fun`. The marked positions are enumerated,
>   including assignment into an annotated `var` and declared vs inferred returns
>   (H2, H3).
> - **Joins are strictly two-stage**: LUB finalizes an un-annotated join at its
>   own boundary before any downstream annotation can coerce the result; the
>   annotation never flows back into the arms (H4).
> - **The nested-limitation bridge is a first-order boundary *before* the call**
>   (`let adapter: |i64| -> i64 := …; g(adapter)`); passing a fresh literal into
>   the nested slot is itself rejected (H5).
> - **`Erased ≠ Move`** is backed by a *mandatory* typed-AST unit test; the only
>   alternative is a fully-specified `Move`-only model that still forbids `Copy`
>   recovery (H8).
> - **Move checking stays opt-in in v0.13.0**; erased non-copyability is a
>   checked-mode guarantee. No "mandatory for function types only" mode (H7).
>
> **Fifth pass (2026-09-03, I1–I6):** provenance moved off `Option<&Type>` onto a
> threaded expected-type value; join classification framed as expected-context +
> LUB; declared generic parameters made rigid against a body ascription; the
> erased-non-copy rule marked a checked-mode error (I5); "store a callback and
> call it repeatedly" confirmed unaffected (I4).
>
> **Sixth pass (2026-09-03, J1–J5) made the mechanism precise:**
> - **`written` is a per-node boolean** on every `Type::Fun` node of an expected
>   type — composable, set once by the source, copied verbatim through alias
>   expansion, associated-type resolution, and substitution *into aggregate
>   fragments*. The four-way discriminant is dropped (it overlapped). Only the
>   first-order node erases; a nested node matches exactly whatever its `written`
>   (J1, J5, Part C).
> - **Generic-substitution timing pinned**: a value crossing a `written` boundary
>   erases *once, there*; an unannotated read of an `F`-typed value is not a fresh
>   boundary (J2).
> - **The join rule is stated as a required outcome**, architecture-neutral:
>   first-order `written` node ⇒ that node's axis; else the LUB; an outside
>   expected type never re-opens the join. Expected-type push and LUB-then-coerce
>   both satisfy it (J3).
> - **Generic rigidity is scoped**: `F` is rigid against a function-type
>   ascription *unless* a declared `where` / assoc-type-equality / RFC-0036
>   obligation proves the shape — impossible pre-RFC-0161, so always rejected
>   today, but the rule needs no amendment when callable bounds arrive (J4).

> **Status — accepted (2026-09-02).** design settled (bare=Erased, copy assertion, A-D weighed); adversarial pass folded in; RFC-0155 scoped out

## Summary

RFC-0134 gives every function value a use-multiplicity axis: it is `Copy` exactly
when its captures are `Copy`, otherwise it is move-only. RFC-0152 permits
capability widening only at first-order sites and requires exact capability
matching below the first nested function level.

Written function types can spell `once` and `var`, but cannot spell the
use-multiplicity axis. Consequently `|T| -> U` is ambiguous: it may be a
requirement for a `Copy` callable, a requirement for a move-only callable, or
an axis-agnostic callable type. The ambiguity becomes observable in generic
higher-order APIs such as `map(f: |T| -> U)`: a concrete `Copy` named function
and a function-type annotation must be reconciled without silently turning the
RFC-0152 first-order limit into a general nested widening rule.

This RFC proposes a surface representation and corresponding matching rule. It
does not reopen the v0.13.0 capture default, `once`/`many`, `var`, or the
higher-order variance question deferred to RFC-0155.

---

## Motivation

The three fields carried by `Type::Fun` are not equally visible in source:

| Axis | Source spelling | Default |
| --- | --- | --- |
| call multiplicity | `once` | `many` |
| call mutation | `var` | reading |
| by-value use multiplicity | *none* | unspecified |

The missing third spelling was exposed while implementing the closure cluster.
The frontend must currently reconcile a written generic callback type with a
concrete callable whose `Copy`-ness is known from its captures. Treating a
written type as move-only rejects ordinary named callbacks in generic APIs;
treating the mismatch as general widening contradicts RFC-0152's exact-nested
rule. Neither behavior is a satisfactory implicit language decision.

The issue is also user-facing. A signature communicates the call and mutation
requirements it places on a callback, but currently cannot communicate whether
the callback is retained, copied, or consumed by value. That makes an API's
ownership contract incomplete precisely where higher-order functions need it.

## Scope and constraints

- Preserve RFC-0152's first-order-only rule for actual capability widening, and
  its exact match for every axis below the first function-type level.
- Preserve RFC-0134's fact that a closure's concrete `Copy`-ness is derived
  from its captures, not inferred from call sites.
- Keep a generic callback signature usable with ordinary named functions and
  capture-free closures.
- The chosen spelling is a **positive assertion** (`copy`) over an otherwise
  **axis-agnostic abstraction** (bare / `Erased`); construction, the move
  checker, and diagnostics must agree, and must do so from one resolved fact
  rather than three independent comparisons.
- Do not touch RFC-0155: variance and subtyping for genuinely nested function
  types stay entirely its problem. Erasure is a coercion into a written bare
  function type at a first-order site; nested use-axis matching is left exact.
- Preserve RFC-0134's concrete `Copy` / `Move` wherever no function type is
  written — a generic type parameter, an unannotated binding or aggregate, a
  closure capture. Only a written bare function type erases.

## Proposal

### Surface syntax

A bare function type erases its use multiplicity:

```metel
fun map<T, U>(xs: List<T>, f: |T| -> U) -> List<U> { /* ... */ }
```

It accepts either a `Copy` or a move-only function value. It does **not** give
the holder permission to copy the value: an erased value is usable as a
move-only value unless the type says otherwise.

This RFC adds `copy` as a function-type qualifier for an API that requires a
copyable callable:

```metel
fun duplicate_callback(f: copy |i64| -> i64) -> () { /* may copy `f` */ }
```

`copy` composes with the existing qualifiers in the same prefix position:

```metel
copy once |T| -> U
copy var |T| -> U
copy once var |T| -> U
```

As with `once` and `var`, the type spelling's qualifier order is
order-insensitive.

**`copy` is rejected in closure-literal-prefix position.** A closure literal has
its independently specified `[captures] once? var? |params|` prefix and does not
take `copy`. The grammar admits a `copy` token there only so the compiler can
emit a precise diagnostic instead of a bare "expected expression" — lowering
then rejects it with `T00xx` (final code assigned at `4-implemented`):

> `copy` is a function-type qualifier only; a closure literal's copyability is
> derived from its captures, not asserted.

This fires for every prefix permutation (`[x] copy |y| { … }`, `copy [x] |y| {
… }`, `copy once |y| { … }`, `once copy |y| { … }`, bare `copy |y| { … }`).

`copy` joins `once` and `var` as a reserved keyword in v0.13.0. The reservation
removes `copy` from **every identifier-bearing position** — a `let` / `var`
binding, function / method / associated-function name, parameter, generic
parameter, type-alias name, `import … as` alias, struct field, enum variant,
`for` / `match` pattern binding, and generated identifiers. The one carve-out is
a `native(@…)` path: `native_path` segments are host identifiers in an FFI
namespace and already admit keywords, so `@std.core.copy` stays legal. A future
RFC may make the whole `once` / `var` / `copy` family contextual, but only as one
combined lexer / parser / compatibility change for all three words.

**`copy` is a requirement on the written function type, not an aspect bound.** It
names the `use_multiplicity` field RFC-0134 already carries on `Type::Fun` — a
requirement that the supplied callable be one RFC-0134 proved copyable from its
captures. Per RFC-0134 a function value satisfies **no value aspects**, `Copy`
included; `use_multiplicity` is the move checker's fact, not aspect membership.
So `copy` does **not** make a callable satisfy a `Copy` / `Clone` bound and does
not interact with RFC-0162's regular-value model at all. Duplicating a callback
is expressed by writing `copy |T| -> U` — the function type itself — never by an
`F: Copy` constraint on a type parameter.

> **Relationship to RFC-0162 (`1-under-review`, v0.17.0).** This disjointness is a
> *scoping* choice for a v0.13.0 RFC, not a claim that the two concepts are
> permanently separate. RFC-0162's **P4 / Axis C / OQ4** is the position under
> which the value-side `copy` (a declaration keyword, `copy struct Foo`) and this
> RFC's function-type `copy` become **one keyword naming one property of
> values**, with the aspect-vs-`use_multiplicity`-field split an implementation
> detail of where the fact is stored. Under P4 a `copy |T| -> U` value would
> then satisfy a regular-value `F: Copy` bound — restoring the `dup<F: Copy>`
> shape this RFC's adversarial review removed as unavailable today. RFC-0163
> **neither blocks nor depends on** that outcome: if P4 is adopted, the
> unification is a one-paragraph amendment to this section with no change to the
> `Erased` state, the coercion table, or the per-node `written` model — those
> exist because a closure's capability is capture-derived and a written function
> type cannot carry it, which no Axis-C choice affects.

There is intentionally no source `move` qualifier in this proposal. A caller
that merely accepts, stores, returns, or consumes a callable needs no stronger
promise than a bare erased type gives it. `copy` is needed because copying is
the capability that must be statically established. A future use case for an
exact move-only assertion may extend this RFC, but must not redefine bare
types in the meantime.

### Type model and matching

`Type::Fun`'s `use_multiplicity` field gains a third state, `Erased`, beside its
concrete `Copy` and `Move` states:

- **`Copy`** — a function value proven copyable: a named function, a capture-free
  closure, or a closure whose captures are all `Copy`.
- **`Move`** — a function value proven *not* copyable: a closure with a non-`Copy`
  capture.
- **`Erased`** — the concrete capability is unknown. Produced **only** by lowering
  a written function type that has no `copy` qualifier, and by coercing a value
  into such a type (below). Never *inferred* for a constructed value, and never
  produced by a position that has no written function type.

`Erased` is the top of the use lattice — least information. An `Erased` value can
be **called** (subject to its `once` / `var`) and **moved**; it can never be
**copied**, and it can never satisfy a hypothetical future exact-`move`
assertion either, because "unknown" cannot prove move-only any more than it can
prove `Copy`. Two `Erased` function types are equal iff their parameters, return,
`once` / `many`, and `var` / reading match.

#### Erasure is a coercion, not a syntactic position

Erasure happens when a value is **coerced into an explicitly written function
type** whose use axis is bare. There is one coercion relation, directional on
the use axis:

| Actual `use_multiplicity` | Written expected axis | Allowed | Result at the coercion |
| --- | --- | --- | --- |
| `Copy` | bare | yes | `Erased` |
| `Move` | bare | yes | `Erased` |
| `Erased` | bare | yes | `Erased` |
| `Copy` | `copy` | yes | `Copy` |
| `Move` | `copy` | no | — |
| `Erased` | `copy` | no | — |

The two "no" rows are a **type error** unconditionally (they are a pure
type-check failure, independent of the move checker). The *other* half of the
guarantee — that an `Erased`-typed binding cannot be duplicated — is a
**checked-mode error**: the move checker raises it, and with move checking off
the default evaluator still deep-clones (see §"Ownership through an erased type"
→ "Enforcement mode").

**"Written" is provenance**, not a property of the final `Type::Fun` — after
normalization a transparent alias, an associated-type projection, and a
genuinely inferred type can all be the same `Type::Fun`. It is carried
**per type-tree node**, not on a root discriminant.

##### The `written` flag: per-node, composable, monotone

Every `Type::Fun` node in an **expected type** carries a boolean `written`:
"the source literally spelled a function type at *this node's* position." It is:

- **Per node.** In `|copy |B| -> C| -> ()`, the outer node and the inner
  parameter node each carry their own `written`. Only the node that is *the whole
  expected type at a value-flow site* (the first-order node) can erase; a
  `Type::Fun` node nested inside another matches exactly regardless of its
  `written` (nesting is positional — §"Nested matching is exact"). `written` on a
  nested node records authorship, not permission.
- **Composable, not a tag.** The old four-way `Written` / `AliasOrigin` /
  `Substituted` / `Inferred` discriminant is dropped: it overlaps (an
  alias-expanded generic argument is *both* alias-derived and substituted) and
  would need an arbitrary precedence. There is nothing to disambiguate — a node's
  `written` is set once by the source and never recomputed.
- **Monotone through normalization.** Transparent-alias expansion (RFC-0160),
  associated-type resolution, and generic substitution copy each node's `written`
  **verbatim** into wherever the fragment lands, including fragments spliced into
  an aggregate. `type W<T> := (T,); let y: W<|i64| -> i64> := (add_one,)` — after
  expansion the tuple's element node is a `written` `Type::Fun` (the source spelled
  it at the generic argument), and the element is the whole expected type for
  `add_one`'s flow, so it erases. A field typed `W<F>` carries the flag on its
  own inner node and each construction derives the field's expected type from the
  declared type with the flag intact. `type Cb := |i64| -> i64` — the `written`
  node from `Cb`'s definition travels to every use of `Cb`.

The expected type threaded through checking is this node-annotated tree, produced
in inference and **passed unchanged into construction** — construction never
reconstructs `written` from a bare `Type`.

##### Boundary positions

Erasure fires when a value flows to a site whose first-order expected node is
`written` and bare. Those sites:

- a **written parameter type**;
- the initializer of a `let` / `var` with a **written annotation**, and the RHS
  of an **assignment** into such a binding;
- an **ascription** (`expr : Type`);
- a **declared** function or method return type (an *inferred* return is not a
  boundary);
- a **written struct-field type**, at each construction and field write;
- a **written aggregate element type**;
- a `?` value against a **declared** function-return slot.

An **inferred** return, `let`, aggregate, or join carries no `written` node: it
computes its own result (or LUB, below), and a later coercion of *that result*
is what erases. Methods follow the function rule, including a builder returning
`self` — declared function-typed result coerces, inferred does not.

The node-annotated expected-type tree is a hard `4-implemented` prerequisite,
called out in the Decision.

Erasure is **idempotent and absorbing**: once a value's type is `Erased` it
stays `Erased` through every later binding, conditional, alias, re-export, and
instantiation. Concrete `Copy` is never re-derived downstream; it is available
only at the value's own definition.

#### Positions with no written function type do not erase

Where nothing writes a function type, the concrete `use_multiplicity` from
RFC-0134 is **preserved**, not erased:

- **An unannotated `let` / `var`** (`let g := add_one;`) keeps `add_one`'s
  `Copy`.
- **An unannotated aggregate literal** (`let p := (add_one,);`, `[add_one]` as a
  list) keeps each element's concrete axis; the tuple/list type carries `Copy`
  through.
- **A generic type parameter** is not a `Type::Fun` node and carries no `written`
  flag. `fun identity<F>(f: F) -> F` binds `F` to the argument value's *resolved*
  type verbatim — `Copy` in → `Copy` out, `Erased` in → `Erased` out. No coercion
  happens at a type-variable parameter (there is no `written` node to coerce
  against), so `identity(add_one)` does **not** erase. Erasure of an `F`-typed
  value happens **once**, if and when the body coerces it across a `written` bare
  boundary (`let x: |i64| -> i64 := f;`) — not on every read. `let x := f;`
  inside the body is unannotated, so `x` simply takes `f`'s type (already
  `Erased` if `f` was, by absorption; still `Copy` if it was).
- **A closure capture of a function value** follows RFC-0134: `[add_one] |x:
  i64| -> i64 { add_one(x) }` is `Copy` because its one capture is `Copy`. A
  capture is not a coercion site (there is no written capture-storage type in the
  surface language to be bare).

#### Joins: an observable outcome, not a checker architecture

A join (`if` / `match` arms, a `||` / `&&` result, a loop-`break` set) has one
**required outcome** on the use axis, stated without reference to any particular
checking strategy:

1. **If the join expression's own first-order expected node is `written`** — the
   join stands where a declared function/method return, an annotated binding RHS,
   a written parameter, an ascription, a `return`-subexpression under a declared
   return, or a `?` under a declared return demands that type — the join's result
   axis is that node's: a `written` bare node ⇒ `Erased`; a `written` `copy` node
   ⇒ every arm must independently be `Copy`. `fun f(c) -> |i64| -> i64 { if (c) {
   add_one } else { add_one } }` ⇒ `Erased`.
2. **Otherwise** the join's result axis is the information-lattice LUB of its
   arms: `Copy ⊔ Copy = Copy` · `Move ⊔ Move = Move` · everything else `= Erased`.
   A homogeneous move-only join stays `Move`, keeping a future exact-`move`
   proof.
3. **No retro-flow.** An expected type that first appears *outside* the join —
   `let h := if (c) { m } else { m }; let e: |i64| -> i64 := h;` — does not
   re-open case 1. It coerces `h`'s already-completed type (`Move`) at `let e`;
   the arms and `m` are untouched.

These outcomes do not require a bidirectional checker. A checker that pushes the
expected type into the arms and one that infers each arm, LUBs, then coerces the
result at the enclosing site produce **the same axis** at every site: coercing
`{Copy, Copy}`'s LUB into a `written` bare node gives `Erased`, exactly as
coercing each arm does; a mixed `{Copy, Move}` LUB (`Erased`) into a `written`
`copy` node fails, exactly as the non-`Copy` arm fails when checked directly. The
only place the two strategies must agree by rule is case 3's no-retro-flow, which
both can honor by finalizing an un-expected join before any later coercion.

#### `Erased` is distinct from `Move` — a representation invariant

In v0.13.0, with no exact-`move` spelling, `Erased` and `Move` impose identical
*source-observable* use behavior: call + move, never copy, never accepted into
`copy`. No `.mtl` fixture can distinguish them. They must nevertheless remain
distinct type states, so that (a) construction never re-derives `Copy` for a
value that passed through a bare written type, and (b) a future `move` qualifier
can accept a proven-`Move` value while rejecting an `Erased` one.

Because the distinction is source-unobservable now, `4-implemented` **must** back
it with a **mandatory** implementation-level unit test over the typed AST: a
`Copy` value coerced across a marked bare function-type boundary is recorded
`Erased`, not `Move`. (Inspecting the typed AST directly is enough — no
serialization facility is required.)

The **only** alternative, if the `Erased` state itself is dropped for v0.13.0, is
this fully-specified temporary model — not a vague "defer": a bare coercion
lowers to `Move`; there is **no `Erased` state and no exact-`move` claim** in the
language; construction is **still forbidden** from recovering `Copy` for any
value that crossed a bare boundary (the deleted normalization stays deleted);
and a later `move` RFC introduces both `Erased` and its own distinction from
scratch. "Keep `Move` but leave `Copy` recovery unspecified" is not permitted.

#### Nested matching is exact

Below the first function-type level — a function type that is itself a
parameter, return, element, or field *of another function type*, decided after
alias expansion — the use axis is matched **exactly**, exactly as `once` / `var`
are: bare ↔ bare, `copy` ↔ `copy`, and nothing else. No erasure and no
`copy`↔bare relaxation at a nested position, in either direction. Given
contravariant parameter position, `|copy |B| -> C| -> ()` and `||B| -> C| -> ()`
do not match either way; a mismatch is a type error.

This keeps every axis below the first nesting literally exact (`once`, `var`, and
now the use axis), so the RFC touches nothing in RFC-0152 or RFC-0155: the
first-order coercion above is the only new latitude, and there is no recursive
`copy`-vs-bare relation for RFC-0155's future variance rules to accommodate.

**Acknowledged limitation.** Exactness at nested positions rejects a direct value
flow that is not itself unsound. In

```metel
fun apply(g: ||i64| -> i64| -> i64) -> i64 { g(add_one) }
```

`g`'s parameter is a nested bare `|i64| -> i64`; `add_one` is concrete `Copy`;
`Copy` ≠ bare *at a nested position* is a type error — even though a callee
holding a bare callback cannot copy it. This is RFC-0155's under-approximation,
taken deliberately rather than pre-deciding variance.

Passing a fresh closure literal directly (`g(|x: i64| { add_one(x) })`) does
**not** help — the literal is still concrete `Copy` (capture-free) flowing into
the nested bare slot. The working bridge is a **first-order erasure boundary
first**: bind the adapter through a written bare annotation, so it is already
`Erased` before it reaches `g`, and the nested match is then bare ↔ bare exact:

```metel
let adapter: |i64| -> i64 := |x: i64| { add_one(x) };  // first-order coercion → Erased
g(adapter);                                            // nested bare ↔ bare: exact match
```

An expression ascription `g((|x: i64| { add_one(x) }) : |i64| -> i64)` does the
same. `3-integrated` carries `g(add_one)` and `g(|x| { add_one(x) })` as
**negative** fixtures and the `adapter` form as the **positive** one.

#### One resolved fact, not three comparisons

There is exactly one directional use-axis relation, evaluated in inference. The
resolved axis is part of the `Type::Fun` written onto every typed node, and it
flows through substitution, generic instantiation, alias expansion, and join
inference like any other component of a type. The elaborator, the move checker,
and construction **read that field**; they never recompute the axis from
captures except at a value's own definition, and never re-run capability
matching. The current frontend's Copy-to-Move handling — the named
move-placeholder normalization *and* every adjacent special case in `unify_seq`,
nested matching, and generic construction — is deleted, not gated.

### Ownership through an erased type

An erased value may be called subject to its written `once` and `var`
qualifiers, and it may be moved into another binding, field, or return value.
It may not be copied merely because the runtime value happened to be `Copy`.
For example:

```metel
fun consume(f: |i64| -> i64) -> () {
    let saved := f;       // move: permitted
    saved(1);
}

fun duplicate(f: copy |i64| -> i64) -> () {
    let a := f;           // copy: permitted
    let b := f;
    a(1);
    b(2);
}
```

A return type, field, or alias containing a bare function type similarly
forgets a concrete callable's copyability. This conservative loss is
intentional; an API that promises or needs copyability writes `copy`.

**Enforcement mode.** The "may not be copied" guarantee is a *static* property
checked by the move checker. The default evaluator still deep-clones a by-value
use, so a program that copies an erased callable runs today with move checking
off. v0.13.0 **keeps move checking opt-in**; erased non-copyability is specified
as a **checked-mode guarantee** — it holds for a program run with the move
checker on, and every RFC-0163 integration fixture sets `move_check = true`.
Whether the move checker becomes mandatory language-wide is a separate question
this RFC does not decide, and a "mandatory only for function-typed places" mode
is explicitly **not** proposed — the checker analyses whole places, aggregates,
captures, and control flow, and a function value can be moved by being stored
inside a non-function value.

### Generic callbacks

The ordinary higher-order signature remains useful for both categories of
callable:

```metel
fun map<T, U>(xs: List<T>, f: |T| -> U) -> List<U> { /* call `f` for each item */ }
fun add_one(x: i64) -> i64 { x + 1 }

let mapped := map([1, 2], add_one);
let offset := 10;
let shifted := map([1, 2], [offset] |x: i64| -> i64 { x + offset });
```

If an implementation copies a callback rather than merely calling or moving
it, its signature must require `copy`. This makes the ownership contract
visible without introducing `Callable` bounds before RFC-0161.

### Generics and `copy`

A **written function type** is a coercion boundary; a **bare type parameter** is
not. The two shapes an API chooses between:

```metel
// 1. Type parameter, no bound. `F` binds to the argument's resolved type
//    verbatim — `Copy` in, `Copy` out; `Erased` in, `Erased` out. Nothing is
//    erased because no function type is written. `F` cannot be *called* without
//    a callable bound (RFC-0161), so this shape is for pass-through / storage.
fun identity<F>(f: F) -> F { f }

// 2. Written function type. Bare erases (`relabel` returns `Erased` even for a
//    `Copy` input); `copy` requires a copyable callable and may duplicate it.
fun relabel(f: |i64| -> i64) -> |i64| -> i64 { f }
fun fork(f: copy |i64| -> i64) -> (copy |i64| -> i64, copy |i64| -> i64) { (f, f) }
```

**There is no `F: Copy` route to a duplicable callback.** RFC-0134 gives a
function value no value aspects, so `F: Copy` cannot be satisfied by one and
`fun dup<F: Copy>(f: F)` does not accept a callable. Copying a callback requires
the `copy` function type. Making function values satisfy the value `Copy` aspect
is a separate change owned by RFC-0161 / RFC-0162 and is out of scope here.

**A generic body cannot ascribe its way past the missing bound.**

```metel
fun adapt<F>(f: F) -> |i64| -> i64 { f : |i64| -> i64 }   // rejected
```

Inside its own body a declared generic parameter `F` is **rigid against a
function-type ascription** *unless the function's own declared constraints on `F`
prove the shape* — a `where F: Bound`, a `where F::Assoc = X` equality, or an
RFC-0036 conditional-impl obligation that establishes `F` is that function type.
An ascription alone never unifies `F`. In v0.13.0 there is **no** function-shape
or callable bound to write (that is RFC-0161), so `fun adapt<F>(f: F) -> |i64| ->
i64 { f : |i64| -> i64 }` is always rejected and an adapter takes a written
function parameter (`f: |i64| -> i64`), not `F`. Once RFC-0161 lands, `where F:
Callable<i64, i64>` would make the ascription legal — the rule is scoped so that
addition needs no amendment here.

This may be a **behavior change** if today's inference unifies an unconstrained
generic variable with an ascribed concrete type. The Migration sweep audits the
corpus for `<generic> : <function type>` body ascriptions (an unusual pattern —
the expected count is ~0) and rewrites any to a written function parameter; a
non-trivial count sends the rule back for review before `3-integrated`.

The diagnostic when an **unconstrained** `F` is used by value twice — `fun
bad<F>(f: F) -> (F, F) { (f, f) }` — is a use-after-move on the second `f`,
pointing at it and noting that no bound makes `F` duplicable; the fix is a
concrete `copy` function-typed parameter.

## Alternatives considered

### A. Concrete default with qualifiers for both capabilities

Giving bare types either a `Copy` or move-only concrete default makes nested
matching literal, but cannot express the common "accept either" callback API
without a second abstraction. It either rejects stateful closures or ordinary
named callbacks. The proposal instead makes that abstraction explicit in the
meaning of omission.

### B. Axis-agnostic bare types without a `copy` spelling

This solves `map`, but leaves an API unable to say it will duplicate a callback
or return one that callers may duplicate. The proposal retains axis erasure for
bare types and adds only the positive `copy` requirement.

### C. Default written function types to `Copy`

A bare type would require a `Copy` callable; a separate spelling would be
needed for move-only values. This keeps the common named-function case simple
and lets nested matching remain literal, but risks making APIs unintentionally
exclude closures that capture owned non-`Copy` state.

### D. Default written function types to move-only

A bare type would require a move-only callable, with a separate spelling for
`Copy`. This is conservative for ownership but makes ordinary named functions
need a special reconciliation rule or annotation, which is the current gap.

## Migration

Adding `copy` and switching bare types to `Erased` is a breaking change in three
narrow places — hard switch, one sweep (Metel has no public users). It runs
**after** the RFC-0050 / RFC-0153 closure-cluster corpus sweeps (they change
closure *spelling*; this changes function-type *semantics*).

- **`copy` as an identifier.** `once` and `var` are already reserved; `copy` is
  not. The sweep audits every identifier-bearing production for a `copy`, not
  just `let copy := …`: bindings, function / method / associated-function names,
  parameters, generic parameters, type-alias names, `import … as` aliases, struct
  fields, enum variants, and pattern bindings, across the corpus, the stdlib, and
  the docs / tutorial examples. `native(@…)` path segments are exempt (host FFI
  identifiers, already keyword-permissive) and are left alone.
- **Bare callback params that copy the callback.** A signature `f: |T| -> U`
  whose body duplicates `f` previously relied on the frontend normalising a
  written function type to concrete `Copy`. Under this RFC that body is a
  use-after-move error; the fix is `f: copy |T| -> U`. Signatures that only call,
  store, move, or return `f` once need no change.

  The audit **runs the move checker over the whole corpus explicitly** — not
  opportunistically, since normal evaluation still deep-clones and an offending
  body runs fine with move checking off. The signal is the move checker's own
  **CFG-aware consumed-place analysis**: a place whose type is a bare (non-`Copy`)
  function type is used again *after* it was consumed on the same control-flow
  path. This is not a textual "used more than once" count — `if (c) { g(f) }
  else { g(f) }` uses `f` twice syntactically but consumes it at most once per
  path and is fine. The shapes it must flag beyond `let a := f; let b := f;`:
  - the parameter placed into a tuple / record / array literal after another
    by-value use of it on the same path;
  - an `if` / `match` arm that moves `f` where a sibling arm's result requires a
    still-live `f`;
  - `return`ing the parameter in two positions of one aggregate;
  - field-shorthand construction from an already-consumed binding.

  Copies introduced *after* move checking — by elaboration / desugaring that
  reads a value twice — are out of the move checker's reach at that stage.
  `4-implemented` must either forbid elaboration from duplicating a value or add
  a post-elaboration ownership-preservation check; the RFC does not treat the
  pre-elaboration sweep as sufficient on its own.

  Each fixed site gets a fixture; each shape above gets at least one negative
  fixture proving it is now rejected without `copy` (with `move_check = true`).
- **Rigid generic ascription (from I3).** Audit the corpus for a `<generic
  param> : <function type>` ascription inside its own generic body — a pattern
  §"Generics and `copy`" now rejects (a declared generic parameter does not
  unify with an ascribed shape). Expected count ~0; rewrite any hit to a written
  function parameter. If the sweep finds a non-trivial number, the rigidity rule
  is reconsidered before `3-integrated` rather than shipped as a silent break.

The normalisation this replaces is `typeinference`'s synthetic Copy-to-Move
mismatch handling *and its siblings* in `unify_seq`, nested matching, and generic
construction (see §"Type model and matching" → "One resolved fact"); the whole
set is deleted, not gated.

## Required integration examples

`3-integrated` must land a named fixture for every row of the coercion table and
every nested / join / generic context. **Every fixture runs with `move_check =
true`** (see §"Ownership through an erased type" → "Enforcement mode"). Minimum
set:

**First-order, accepted**

- `Copy → bare` — a named `add_one` into `map(xs, f: |i64| -> i64)`; result binds,
  the callback's `Copy`-ness is dropped (observably: cannot be copied downstream).
- `Move → bare` — a closure capturing an owned non-`Copy` value into the same
  `map`; accepted, runs.
- `Erased → bare` — the `Erased` result of one `map`-shaped call fed straight
  into another bare slot; stays `Erased` (round-trip; alias in between).
- `Copy → copy` — `fork(f: copy |i64| -> i64)` duplicating `f` and calling both
  copies.

**First-order, rejected**

- `Move → copy` — a capturing closure passed where `copy` is required.
- `Erased → copy` — an `Erased` value (from a bare return, a bare-typed field, or
  a bare alias expansion) passed into a `copy` parameter *and* returned as a
  `copy` type.

**Nested (exact — no erasure, no `copy`↔bare)**

- `copy` param vs bare param, contravariant: `sink(cb: ||B| -> C| -> ())` given a
  value of type `|copy |B| -> C| -> ()` — rejected.
- bare param vs `copy` param, the other direction — also rejected.
- nested `once` / `var` mismatch still rejected exactly as before — erasure did
  not touch it.
- **The acknowledged limitation and its bridge**: `fun apply(g: ||i64| -> i64|
  -> i64) { g(add_one) }` and `g(|x: i64| { add_one(x) })` are both **negative**
  (concrete `Copy` into a nested bare slot); `let adapter: |i64| -> i64 := |x:
  i64| { add_one(x) }; g(adapter);` and the equivalent ascription are the
  **positive** cases (first-order erasure, then a bare↔bare nested match).
- **Alias / projection / substitution at the boundary**: `type Cb := |i64| ->
  i64; fun h(g: |Cb| -> ())` — after expansion the `Cb` node sits *nested* under
  `g`, so it matches exactly, not by erasure. `type Direct := |i64| -> i64; fun
  p(f: Direct)` — a *first-order* node — still erases. `type W<T> := (T,); let y:
  W<|i64| -> i64> := (add_one,);` — the substituted tuple-element node is
  `written` and first-order → erases. A `struct S { cb: W<|i64| -> i64> }` field
  write and a resolved associated-type projection that lands on a written
  function type each carry the per-node `written` flag through.

**Join / aggregate (no written type → LUB; written type → coercion)**

- `if`-join of two `Copy` arms into an **unannotated** `let` → `Copy` (LUB).
- **`if`-join of two arms of the same move-only closure type → `Move`** (LUB;
  the future exact-`move` proof is kept).
- `if`-join of a `Copy` arm and a `Move` arm into an unannotated `let` → `Erased`
  (LUB); then coercing that into a `copy` slot → rejected.
- `if`-join of two `Copy` arms into a **written bare** slot → `Erased`
  (coercion); into a **written `copy`** slot → accepted.
- an **unannotated** tuple / `List` literal from `Copy` values → elements keep
  `Copy`; the same literal against a **written** bare element type → `Erased`.

**Generic**

- `identity<F>(f: F) -> F` preserves `Copy` (result copyable) and preserves
  `Move` / `Erased` verbatim; `relabel(f: |i64| -> i64) -> |i64| -> i64` erases
  (result `Erased`). `identity(add_one)` does **not** erase.
- `fun dup<F: Copy>(f: F)` does **not** accept `add_one` — a function value
  satisfies no value aspect (RFC-0134) — a negative fixture.
- `fun adapt<F>(f: F) -> |i64| -> i64 { f : |i64| -> i64 }` — rejected (no
  function-shape bound on `F`); a negative fixture.
- unconstrained `fun bad<F>(f: F) -> (F, F) { (f, f) }` — use-after-move on the
  second `f`.
- a closure capturing a `Copy` function value — `[add_one] |x: i64| { add_one(x)
  }` — is `Copy` and duplicable (RFC-0134, not erased by capture).

**Reassignment / inferred vs declared return** — `var f: |i64| -> i64 :=
add_one; f = add_one;` erases each RHS at the declared binding type; `fun
inferred() { add_one }` (inferred return) does not erase, `fun declared() ->
|i64| -> i64 { add_one }` does.

**Two-stage join** — `let h := if (c) { m } else { m }; let e: |i64| -> i64 :=
h;` keeps `h` at `Move` (LUB) then erases `e`; `let e: |i64| -> i64 := if (c) {
m } else { m };` erases each arm. A fixture pair proving the annotation does not
flow back into the un-annotated join's arms.

**Literal-`copy` diagnostic** — one negative fixture per prefix permutation from
§"Surface syntax".

**Representation invariant** — a mandatory implementation-level unit test over
the typed AST (not an `.mtl` fixture): a `Copy` value coerced across a marked
bare function-type boundary is recorded `Erased`, not `Move`.

Every example keeps surface-axis erasure distinct from RFC-0152 widening:
erasure is a first-order coercion of an *omitted* use axis into a written bare
type, and never relaxes the exact `once` / `var` / use match RFC-0152 requires
below the first function-type level.


---

## Decision

**Outcome:** **Accepted 2026-09-02** (`2-accepted`, #936). Bare function types erase
use-multiplicity to `Erased` (callable + movable, never copyable); `copy` is a positive
assertion of a `Copy` callable — surface syntax for RFC-0134's capture-derived
function-value `Copy` capability, not a new axis — and joins `once` / `var` as a reserved
order-insensitive type qualifier, never on a literal. Alternatives A–D weighed; the
axis-agnostic-erasure + positive-`copy` combination (B plus the `copy` spelling) is the
choice.

Six adversarial passes (2026-09-02, then 2026-09-03 ×5) hardened it without reopening the
outcome. The settled shape:

- **Erasure is a coercion into a `written` bare function-type node**, not a syntactic slot.
  `written` is a **per-node** boolean on every `Type::Fun` node of an *expected type* — set
  once by the source, copied verbatim through RFC-0160 alias expansion, associated-type
  resolution, and generic substitution (including into aggregate fragments), and never
  reconstructed from `Type`. It is composable, not a discriminant. Only the first-order
  node (the whole expected type at a value-flow site) can erase; a nested `Type::Fun` node
  matches exactly whatever its `written`. A generic type variable, an unannotated `let` /
  aggregate / return / join, and a closure capture carry no `written` node and preserve
  RFC-0134's concrete `Copy` / `Move` (F3/F5, G3/G4/G5/G8, H2/H3, I1, J1/J5). Erasure of an
  `F`-typed value happens once at a `written` boundary, not per read (J2). The
  node-annotated expected-type tree is a hard `4-implemented` prerequisite.
- **Nested use-axis matching is exact**, like `once` / `var` — no recursive `copy`-vs-bare
  relation, nothing for RFC-0155 to accommodate. The rejected direct-flow case is named;
  the working bridge is a **first-order** erasure boundary (an annotated `let` or an
  ascription) *before* the nested call — passing a fresh literal to the nested slot does
  not help (F1, G2, H5).
- **A join has one required outcome, stated architecture-neutrally** (G1, H4, I2, J3): if
  the join's own first-order expected node is `written`, the result axis is that node's
  (bare ⇒ `Erased`; `copy` ⇒ every arm independently `Copy`); otherwise it is the
  information-lattice LUB of the arms (`Move ⊔ Move = Move`); an expected type appearing
  *outside* the join never re-opens it. Expected-type push and LUB-then-coerce both satisfy
  this.
- **`Erased ≠ Move` is a representation invariant** — source-unobservable in v0.13.0 —
  backed by a **mandatory** typed-AST unit test, or, only if `Erased` is dropped entirely
  for v0.13.0, a fully-specified `Move`-only temporary model that still forbids `Copy`
  recovery (F4, G6, H8).
- **`copy` is a requirement on the written function type, not an aspect bound.** Per
  RFC-0134 a function value satisfies no value aspects, so there is no `F: Copy` route to a
  duplicable callback and `copy` does not touch RFC-0162's model. A declared generic
  parameter is **rigid against a function-type ascription** unless its own declared
  constraints (`where F: Bound`, an assoc-type equality, an RFC-0036 obligation) prove the
  shape — impossible in v0.13.0 without RFC-0161, so `fun adapt<F>(f: F) -> |…| { f : |…| }`
  is always rejected; Migration sweeps for the pattern (F2, F7, H1, H6, I3, J4). ("Store a
  callback and call it repeatedly" — `fun later(f: |i64| -> i64) -> i64 { f(1) + f(2) }` —
  still works; only *retaining independent copies* needs `copy`, I4.)
- **One directional relation in inference**; the resolved axis is part of the `Type::Fun`
  on every typed node and flows through substitution / instantiation / joins; the
  elaborator, move checker, and construction read it and never re-decide (F12).
- **Migration** uses the move checker's CFG-aware consumed-place analysis, flags
  post-elaboration copies as a separate `4-implemented` obligation, and runs under
  `move_check = true` (F8, G7, H7, Part C). v0.13.0 keeps move checking opt-in; erased
  non-copyability is a checked-mode guarantee, and no partial mandatory mode is proposed.
  `copy` reservation fallout is enumerated with a `native_path` carve-out (F10); the
  literal-`copy` diagnostic has a class and message (F9).

RFC-0155 (higher-order variance) is scoped out and unweakened. **Target: v0.13.0** — the
missing third `Type::Fun` surface, needed to stop the frontend guessing (see Motivation).

`3-integrated` adds a `spec.functions.first-class-functions` block for the `Erased` state,
the coercion relation and the per-node `written` model, the architecture-neutral join
outcome, the "nested is exact" rule with its acknowledged limitation, and the "one
resolved fact" constraint — plus every fixture in §"Required integration examples"
(including re-exported-alias, associated-projection, generic-argument-function-type,
substitution-into-aggregate, tail-`if`/`match`, and `return if` cases), the
representation-invariant assertion, and the rigid-generic-ascription corpus sweep result.
`4-implemented` is: the node-annotated expected-type tree threaded through inference and
construction (a hard prerequisite); `copy` reserved word + `fun_type_qualifier` grammar
slot + literal-prefix rejection diagnostic; the `Erased` `use_multiplicity` state on
`Type::Fun`; the single directional relation replacing `typeinference`'s Copy-to-Move
handling and its siblings (deleted, not gated); the move-checker CFG analysis +
post-elaboration ownership check; and the corpus / stdlib / docs migration.
