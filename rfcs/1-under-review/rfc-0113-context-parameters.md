---
id: rfc-0113
title: "Context Parameters"
date: '2026-07-21'
status: under-review
target: v0.13.1
updated: '2026-08-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/808'
---

> **Tracking added retroactively (2026-08-23).** This RFC reached under-review before
> the tracking-issue requirement existed (PROCESS.md, 2026-08-23); filed metel-core#808
> (design-settlement, no code — all five open questions below).

> **Status — under review (2026-07-21).** Fills the substrate hole OBJECTIVES.md named as the largest unwritten one (Priority 3 since the 2026-07-22 reorder). Substantiated proposal with declaration, provision and resolution specified, grounded in RFC-0065's four elision rules and its reverted depth-shadowing attempt. Five open questions remain, chiefly syntax and whether contexts propagate through intermediate frames. Reviewing with the records/views cluster it shares a substrate with.

## Summary

A **context parameter** is a value a call tree needs, declared on the callee, and supplied
by the caller *from scope by type* rather than written at every call site. Ambiguity is a
compile error, never a silent choice.

```metel
context(alloc: Heap)
fun make_user(name: String) -> @alloc User { ... }

fun run(context alloc: Heap) {
    let u = make_user("Ada");   // `alloc` is threaded, not written
}
```

This is proposed as a **substrate primitive**, not allocator ergonomics.
`OBJECTIVES.md` Priority 2 lists it alongside structural records, per-field multiplicity,
brand semantics and lifetime validity, and singles it out as

> the one member of this list with **no RFC of any kind yet** — the largest unwritten hole
> on the allocator critical path, larger than any open brand or borrow-checker question,
> since those at least have a document.

This RFC exists to close that hole. It is deliberately written **without** allocator
syntax in its core design: if the mechanism is general, `(@a: A)` must fall out of it as an
instance, not the other way round.

---

## Motivation

### 1. The allocator cluster spent four elision rules on one general problem

RFC-0065 (accepted) is almost entirely about threading one value through a call tree
without writing it everywhere. Its §1 elides the allocator in type position, §1a handles
the tag-only case, §1b elides it in *call-argument* position, and §2 does the same for
lifetime anchors. All four share one stated invariant — "elision is legal only when the
compiler can determine the unique correct answer; ambiguity is always a compile error,
never a silent choice."

That invariant is not about allocators. It is the definition of context-parameter
resolution.

RFC-0065's own revision history makes the point more sharply than an argument could. Its
2026-07-20 second pass tried **depth-based shadowing** (innermost declared allocator wins)
and reverted it, because "adding an unrelated `BumpAlloc::scoped` closure anywhere inside a
function would silently change what every already-elided allocation inside it means, with
no diagnostic." The replacement was **type-directed candidate filtering**, explicitly
modelled on Kotlin's context parameters. So the allocator cluster has already converged on
context-parameter semantics by re-deriving them under a different name, twice, and got the
scoping rule wrong once on the way.

### 2. `allocators-as-emergent-synthesis.md` names it as the missing column

That report decomposes the allocator design into four general capabilities and reports
their status:

| Allocator machinery | General feature | Status |
|---|---|---|
| `(@a: A)` param + elision + §1b call-site inference | **context parameters** | **no RFC exists at all** |
| `@a T`'s instance tag; disjointness; sendability | brands (`'c`) | draft (RFC-0076) |
| `@a T` owned/affine/moved | owned box + borrow checker | unbuilt |
| `@a expr`; the `Alloc` aspect | ordinary aspect + library | already implemented |

Three of four columns have a document. This is the fourth.

The report is also precise about what context parameters do **not** do, and this RFC
inherits that scoping exactly: they replace the *threading* and nothing else. A context
parameter is shared, borrow-shaped, and neither affine nor move-tracked. That describes the
allocator *handle* being passed down a call tree; it describes the allocated *values*
`@a T` not at all. Anyone reading this RFC as "context parameters could replace allocators"
has read it wrong — §7 says so directly.

### 3. It is not allocator-specific in the first place

The same shape recurs wherever a value is needed deep in a call tree but is uninteresting
at every intermediate layer:

- an allocator handle (the motivating case);
- a capability or effect handler — RFC-0076's own §"Capability tokens" already sketches
  `fun println<brand 'io>(given cap: IO<'io>, s: String)`, using an invented `given`
  keyword for want of this mechanism;
- a logger, tracing span, or request context;
- a database transaction or connection handle;
- a locale, arena, or configuration bundle.

Metel has no general answer today, so each of these would otherwise arrive with its own
bespoke elision rule — which is exactly how the allocator cluster ended up with four.

---

## 1. Declaration

A function declares context parameters in a `context(...)` clause preceding it:

```metel
context(alloc: Heap)
fun make_user(name: String) -> @alloc User { ... }

context(alloc: Heap, log: Logger)
fun seed(count: i64) { ... }
```

Context parameters are **named and typed**, exactly like ordinary parameters. The name is
in scope in the body and is an ordinary binding there.

Naming them is a deliberate departure from Kotlin's original *context receivers*, which
were nameless. Kotlin replaced that design with named `context(users: UserService)`
parameters in KEEP-0367 (stable in 2.4) specifically for traceability — a nameless context
makes it impossible to say which of two same-shaped values a body is using. Metel takes the
post-revision form directly rather than repeating the intermediate step.

### 1.1 They are part of the signature, not inferred into it

A context parameter is **declared**, never inferred. A function that needs an allocator
says so. This is the line RFC-0075 (withdrawn inter-function inference) crossed and
RFC-0065 §1b deliberately did not: §1b's own note is that it "never adds anything invisible
to a *signature* — the callee's `(@a: A)` parameter stays exactly as explicit as it is
today; only a caller's redundant re-naming of an already-unambiguous argument is elided."

Same rule here. Elision happens at **call sites**, never at declarations.

---

## 2. Providing a context

A caller satisfies a callee's context parameter from its own scope. Three ways a value gets
into context scope, in decreasing explicitness:

**A `context` parameter of the caller** — the value flows straight through:

```metel
context(alloc: Heap)
fun outer() {
    make_user("Ada");   // `alloc` satisfies make_user's `alloc`
}
```

**A `with` block** — introduces a context for a lexical region:

```metel
fun main() {
    let heap = Heap::new();
    with (heap) {
        make_user("Ada");
    }
}
```

**An explicit argument** — always available, and always wins:

```metel
make_user(context alloc = other_heap, "Ada");
```

Explicit passing is never removed. Every elided call has a spelled-out form, and the
spelled-out form is what a reader can fall back to and what a diagnostic can suggest.

---

## 3. Resolution

At a call site, for each of the callee's context parameters, the compiler collects the
candidates in scope whose type satisfies that parameter's declared type, and:

- **exactly one candidate** → it is used;
- **no candidate** → compile error naming the parameter and its type;
- **two or more candidates** → compile error listing them.

### 3.1 Type-directed filtering, not shadowing

"In scope" means *in scope and of the type this position requires*. Two candidates of
different types never compete, so a `Heap` in an outer scope and a `BumpAlloc` in an inner
one both resolve unambiguously for their own positions — no nesting rule needed.

This is RFC-0065's own conclusion after its reverted attempt, generalized. **Nesting depth
never breaks a tie.** Where two candidates share a type, the call is ambiguous and the user
names one. Silent innermost-wins is rejected for the reason RFC-0065 recorded: adding an
unrelated inner binding would silently change the meaning of every already-elided call
inside it, with no diagnostic.

### 3.2 Ambiguity is an error, always

There is no tiebreak: not depth, not declaration order, not "most recently introduced." A
same-type collision is a compile error with both candidates named. This is the invariant
RFC-0065 states for all four of its elision rules, adopted verbatim as this mechanism's
defining property.

---

## 4. Interaction with the allocator cluster

**If this RFC is accepted, RFC-0065 §1, §1a and §1b become instances of it rather than
rules of their own**, and `(@a: A)` becomes surface syntax over a context parameter of type
`A`. That is the point: the allocator cluster stops carrying a general mechanism inside it.

Deliberately **not** proposed here:

- retiring or amending RFC-0063/0065 — that is a follow-up once this mechanism is settled,
  and doing it in the same RFC would repeat the coupling this one exists to break;
- the `@` sigil, allocation expressions, or the `Alloc` aspect — all genuinely
  allocator-specific and unaffected;
- lifetime anchors (RFC-0065 §2). Anchors are not values threaded through a call tree; they
  are scope-validity facts the borrow checker derives. §2's elision looks similar on the
  page and is a different mechanism underneath. Folding it in would be exactly the
  over-unification §7 warns about.

---

## 5. Interaction with brands (RFC-0076)

RFC-0076's capability-token pattern currently invents a keyword for want of this mechanism:

```metel
fun println<brand 'io>(given cap: IO<'io>, s: String) { ... }
```

`given` there is context parameters under another name. Once this RFC exists, that
sketch is written with `context(cap: IO<'io>)` and RFC-0076 drops its invented syntax.

Note what this does **not** do: a branded context parameter is still resolved by *type*,
and two distinct brands give two distinct types, so `IO<'main>` and `IO<'test>` never
collide. Brands and context parameters compose without either needing to know about the
other — which is evidence for the decomposition thesis rather than an extra rule.

---

## 6. Alternatives considered

- **Implicit parameters resolved by type alone, with no declaration** (Scala 2 `implicit`).
  Rejected: it puts information into a signature that the signature does not show, which is
  precisely why RFC-0075 was withdrawn, and Scala 3 itself moved away from it.
- **Nameless context receivers** (Kotlin pre-KEEP-0367). Rejected: untraceable when two
  same-shaped values are in scope; Kotlin replaced it for that reason and this RFC starts
  from the replacement.
- **Dynamic scoping / an ambient context struct** (Odin's implicit `context`). Genuinely
  ergonomic and worth naming honestly: Odin threads an implicit `context` struct through
  every non-`"contextless"` call, and `context.allocator` is exactly the motivating use
  case. Rejected because it is one global bundle rather than a typed set — adding a field
  changes every call, and there is no way to require *only* an allocator.
- **Nothing; keep per-feature elision rules.** The status quo. Rejected because the
  allocator cluster already shows where it leads: four rules, one reverted scoping design,
  and a second feature (capability tokens) inventing a third syntax for the same idea.
- **Explicit threading only** (Zig's position — pass the allocator, always, everywhere).
  Genuinely defensible and the honest baseline: it needs no mechanism at all and makes cost
  visible. Rejected for Metel because RFC-0065 already judged the resulting verbosity
  unacceptable *for allocators specifically*, and that judgment is what this RFC generalizes
  — but it deserves to be re-argued if the elision rules prove hard to specify.

---

## 7. Non-goals

- **Context parameters do not replace allocators.** They replace the threading of the
  handle. Allocated values are owned, affine and move-tracked; that is the box + brand +
  borrow-checker column, untouched here. `allocators-as-emergent-synthesis.md` §2 calls the
  opposite reading "the seductive-but-wrong version of this thesis."
- **Not effect tracking.** A context parameter says a value is *available*, not that a
  function *performs* an effect. Capability-style effect control is a use of this mechanism
  (§5), not this mechanism.
- **Not dynamic scoping.** Resolution is static, by type, at the call site.
- **No implicit conversions.** A candidate satisfies a parameter or it does not.

---

## 8. Unresolved questions

1. **Syntax.** `context(name: T)` is taken from Kotlin because it is the closest
   post-revision prior art, not because it has been weighed against Metel's own grammar. It
   collides with nothing today, but `with (heap) { .. }` (§2) is a new block form and
   `context alloc = x` (§2) a new argument form; both need a real grammar pass.
2. **Do context parameters propagate implicitly through intermediate frames?** If `a` calls
   `b` calls `c`, and only `c` declares `context(alloc: Heap)`, must `b` declare it too?
   Kotlin says yes — every frame that needs it declares it. That is more verbose but keeps
   signatures honest, and matches §1.1. Recommended, but it is the single decision that most
   changes how the feature feels, and it deserves a worked example on a real call tree
   before it is settled.
3. **Aspect-typed context parameters.** May a parameter be declared `context(a: Alloc)` — an
   aspect rather than a concrete type — with any in-scope implementor satisfying it? That is
   what the allocator use case actually wants, and it makes §3's "satisfies that type" a
   bound-satisfaction query rather than a type match. Cheap to state, not cheap to specify.
4. **Interaction with closures and function types.** *(Expanded 2026-09-01 alongside
   RFC-0160 Type Aliases §"Context parameters".)* Two regimes, both wanted:

   - **Default — definition-site capture.** A `context c: C` in scope where a closure
     literal is written is an ordinary free binding the closure closes over at creation,
     the same as any other outer binding. The closure's type stays plain (`(T) -> U`) and
     carries no context requirement. This is the only regime consistent with §3's static
     resolution, and it is what `BumpAlloc::scoped((@a) -> { .. })` (RFC-0065) relies on.
   - **Deferral — a context function type.** `context(c: C) (T) -> U` is a closure type
     whose *caller* must supply `c` from scope at each call. This is Scala 3's context
     functions (`(using T) ?=> R`). It is genuine type information — an alias carries it,
     a struct field can hold it, RFC-0152 widening applies to it.

   Consequences to specify:
   - **Capture-list carve-out (RFC-0050).** In a deferred-context closure, `c` is used in
     the body but is **not** listed in the capture list — it is threaded per call, not
     captured. RFC-0050's "free variable" exemption (currently module-level
     functions/constants/types/aspects) gains context parameters as a third category, for
     the same reason: they are resolved, not closed over. Exhaustiveness stays honest.
   - **Where it lives on the type.** The `context(...)` clause is a **row** of `(role,
     type)` requirements — orthogonal to the `once` / `mut` multiplicity axes (RFC-0134 /
     RFC-0153), following the row shape RFC-0140 already uses for its handler channel and
     RFC-0121 supplies. Whether it becomes a fourth `Type::Fun` field or contexts are
     capture-only (no deferral, so never reaching the type) is this RFC's call.
   - **Propagation (UQ2) recurs here:** a deferred-context closure value passed through an
     intermediate frame carries its requirement in its type, so it need not be re-declared
     — the value-side answer to the same question.
5. **Does this subsume RFC-0065 §1b, or coexist with it?** §4 asserts it should subsume it.
   The migration is not specified here, and RFC-0065 is `2-accepted`, so this is a real
   cross-RFC amendment to sequence, not a footnote.

---

## References

- `reports/strategy/OBJECTIVES.md` Priority 2 — names context parameters a substrate
  primitive and this RFC's absence as "the largest unwritten hole on the allocator critical
  path."
- `reports/substructural-types/allocators-as-emergent-synthesis.md` §1–§2 — the
  decomposition table this RFC fills the missing row of, and the precise statement of what
  context parameters do and do not replace.
- RFC-0065 (Allocator Ergonomics, accepted) — §1/§1a/§1b, the four elision rules this
  generalizes; its 2026-07-20 second pass is the reverted-shadowing precedent behind §3.1.
- RFC-0076 (Brand Types, under review) — the capability-token pattern whose invented `given`
  keyword this replaces (§5).
- RFC-0075 (withdrawn) — inter-function inference; the line §1.1 declines to cross.
- Kotlin KEEP-0367 (context parameters, stable 2.4) — the named-parameter design this
  follows, and its own supersession of nameless context receivers.
- Odin's implicit `context` struct, and Zig's explicit-allocator convention — the two
  alternatives weighed in §6.
- **RFC-0160 (Type Aliases), `0-draft`** — its §"Context parameters" and §"Function and
  closure types" mirror Unresolved Question 4; the two are kept in sync. Also the RFC that
  would let `context(theme: Theme) mut (Widget) -> Html` be named once instead of repeated.
- Scala 3 context functions (`(using T) ?=> R`) — the deferral regime in UQ4.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
