---
id: rfc-0112
title: "Auto-Deref Scope and Expected-Type Provenance"
date: '2026-07-21'
status: draft
target:
---

## Summary

Decide how far Metel's implicit type-directed read-copy (RFC-0067a §3a) reaches — which
expression positions get a value silently copied out of a reference, and which require an
explicit spelling — and make that boundary *mechanically enforced* rather than an emergent
property of wherever an expected type happens to be available.

The proposed rule is one sentence:

> **Implicit read-copy fires when the expected type originates in the declaration the
> expression is lexically inside; not when it comes from a different declaration being
> referenced, from a sibling expression's inferred type, or from compiler-internal
> machinery.**

Enforcement is a provenance tag carried alongside the expected type, so that each site
supplying one must classify it, and the classification is checked by the compiler rather
than remembered by the author.

This RFC was split out of RFC-0110, which originally proposed widening read-copy to call
arguments and binary operands. Those two extensions are re-examined here (§4) and declined
under the proposed rule. RFC-0110 keeps the write-side change and the explicit `*`
operator, and does not depend on this RFC's outcome.

---

## Motivation

### 1. RFC-0067a §3a claims more coverage than it has

RFC-0067a §3a's text says read-copy fires "at every position where a declared or expected
type is already known, not just `let`," and names struct-literal fields and `match` arms
among them. Probed directly against the built interpreter:

| position | §3a's text | actually |
|---|---|---|
| `let y: i64 = r;` | fires | **works** |
| ascription `r: i64` | fires | **works** |
| `return r` (return type `i64`) | fires | **works** |
| `W { v: r }` struct-literal field | fires | **fails** `T0001` |
| `match .. { true => r }` against `i64` | fires | **fails** `T0001` |
| `takes(r)` call argument | does not fire | fails `T0001` |
| `r + 1` binary operand | does not fire | fails `T0001` |

So the implemented set is `let`/`var` annotation, ascription, `return`/`break`, and tail
position — the five sites `maybe_read_copy` (`construction.rs`, ~line 4131) is actually
called from. The RFC's own generalization overshot its implementation by two positions,
and nobody noticed because the narrower behavior is the one people write code against.

That drift is the motivation. A rule stated as "everywhere an expected type is known" is
not enforceable, because "an expected type is known" is a property of whatever the
compiler happens to thread where — it changes whenever someone adds a hint for an
unrelated reason. This RFC proposes replacing it with a rule that can be checked.

### 2. Two in-flight RFCs turn the same knob in opposite directions

This is the concrete reason to fix it now rather than leave it as documentation debt.

- **RFC-0111** (Unqualified Enum Variants in Expression Position) wants expected types
  threaded to *more* positions, so that bare `Red` resolves in more places. Its §1.3
  explicitly names widening `param_hints` and method-call arguments as desirable.
- **RFC-0110** under the Go model wants implicit read-coercion in *fewer* positions —
  ideally exactly the ones it has today, with `*p` everywhere else.

Both read the same parameter: `construct_expr(expr, expected_ty: Option<&Type>, ctx)`.

If read-copy stays keyed on "is `expected_ty` `Some`," then implementing RFC-0111's
widening silently reintroduces call-argument auto-deref — RFC-0110's old §1 — as a side
effect nobody reviewed, in a commit whose subject line is about enum variants. That is the
same class of failure the RFC-0063 precedent exists to catch, and it is avoidable cheaply.

### 3. "Is `expected_ty` `Some`" is far too broad a trigger anyway

Tracing every caller that passes a non-`None` expected type in `construction.rs` turns up
five distinct kinds of thing, not one:

1. **Authored here** — `let`/`var` annotation (lines 512, 536, 1078, 1105), type ascription
   (1970), `return`/`break` via `current_return_ty`/`break_ty` (2027, 2047).
2. **Authored elsewhere** — `param_hints` for call arguments (2778, 3095, 3227),
   struct-literal field hints (1742). The type comes from a *different* declaration that
   this expression merely references.
3. **Sibling-inferred** — binary-operator cross-propagation (3938, 3940), where each
   operand is constructed against the *other operand's* inferred type. No annotation exists
   anywhere; this is how `let x: i64 = 1 + 2` resolves its literals.
4. **Structural / compiler-internal** — index expressions get `Some(&Type::U64)` (1364,
   4302, 4339); array literals decompose an expected array type into an element hint
   (1315, 1324, 1342). Machinery, not a statement of anyone's intent.
5. **Inherited** — block tail (1030), array elements, `if`/`match` arms: these carry
   whatever the parent had.
6. **Inference-derived** *(added 2026-07-21, after metel-core#565)* — a closure body is now
   constructed against the closure's own return type, and for an *unannotated* closure that
   type comes from pass 1's inference rather than from anything an author wrote. Before
   #565 this supplier did not exist: `body_expected` was `None` whenever the closure had no
   `-> T`, because pass 2 had no access to the inferred type at all.

   This is a genuinely new kind, not a re-labelling of category 1. The type is real and
   correct, but nobody wrote it down anywhere, so "authored in the declaration the
   expression is lexically inside" does not describe it. §1's rule must say what it does
   with this case before it can be accepted; the safe default, consistent with the rest of
   the rule, is that read-copy does **not** fire on it. Not decided here.

Category 3 is the sharpest illustration. `r + 1` propagates `1`'s inferred `i64` onto `r`.
A trigger keyed on `Some` would make that deref — reintroducing RFC-0110's old §2 through a
path nobody chose, from a type nobody wrote down.

---

## 1. The rule

Implicit read-copy fires **iff the expected type's provenance is category 1** — authored in
the declaration the expression is lexically inside.

Restated without reference to the category numbering, since this is the form that belongs
in the spec:

> A value is copied out of a reference implicitly when the type it is being checked against
> was written in the declaration you are currently inside — a `let`/`var` annotation, an
> ascription, or the enclosing function's return type. When the type comes from somewhere
> else — a callee's parameter list, a struct's field declaration, another operand, or the
> compiler's own bookkeeping — the copy must be spelled explicitly.

### 1.0 The rule was not positional; it is now — resolved 2026-07-21

**Found while checking this RFC against the implementation, then fixed.** The rule below is
stated *positionally*: read-copy fires at these positions and not those. That was not what
the implementation did. `constrain_with_read_copy` decided whether to peel by
pattern-matching `actual` **raw**, without applying the current substitution — so the peel
depended on whether the value's type happened to be in reference form already:

| at a `let` annotation (category 1 throughout) | before | now |
|---|---|---|
| `let n: i64 = r;` where `let r: &i64 = &a;` | works | works |
| `let n: i64 = s.r;` where the field's type is `&i64` | works | works |
| `let n: i64 = g();` where `fun g() -> &i64` | **`T0001`** | works |
| `let r = g(); let n: i64 = r;` | **`T0001`** | works |
| `let n = g(): i64;` (ascription) | **`T0001`** | works |
| `return g();` from a `-> i64` function | **`T0001`** | works |

A call returns a fresh inference variable, which matches no reference pattern, so the peel
decision was made *before the information needed to make it existed* and was silently made
wrong. `let n: i64 = g()` failing where `let n: i64 = r` succeeds is not a distinction any
user could predict, so this was treated as a defect to remove rather than a design to
codify. Fixed by solving and applying before the peel test — the same shape `infer_match`
(RFC-0108) and `Expr::Call`'s auto-deref already used; `constrain_with_read_copy` was the
one place still inspecting raw. Fixture:
`evaluator/references/13_read_copy_from_call_result.mtl`.

**Consequence for this RFC: §1's rule is now literally true, and §2's zero-behaviour-change
claim is restored.** It was briefly false, and it is worth recording that it was — the claim
is this RFC's main evidence that the rule describes the design rather than being imposed on
it, and it survived only because the implementation was corrected to match, not because the
rule was right about the code as it stood.

**One related limitation deliberately left alone.** `let f: () -> i64 = () -> { g() };`
still fails. There the declared type is the closure's own return variable, and the
constraint that would resolve it is not generated until after the body is inferred — so
applying the current substitution is a no-op. That is an ordering limitation in constraint
generation, not a missing `apply`, and substituting `declared` was tried and fixed nothing.
Out of scope for this RFC; it is not a provenance question.

Three properties worth stating, because each rules out a worse formulation:

- **It is not a distance or visibility judgment.** "Same line," "nearby," "visible on
  screen" are all unstatable and formatting-sensitive. This rule asks a structural
  question — which declaration authored this type — that has an exact answer at every site.
- **It does not depend on how much the compiler happens to know.** Widening hints for
  RFC-0111 adds category-2 expected types; the rule is unmoved.
- **It matches what is implemented today** (§2), so adopting it changes no behavior.

### 1.1 Why `return` is category 1

`return r` where the enclosing function returns `i64` works today, and under this rule it
keeps working: the return type is authored in the declaration the expression sits inside.

The alternative reading — that a signature 200 lines above a nested `return` is not
meaningfully "here", so `return *r` should be required — is more strictly Go. It is
rejected because it smuggles distance back in: it needs a threshold, and any threshold is
arbitrary and formatting-sensitive. "Which declaration authored this type" is a question
with one answer regardless of how long the function is. Accepting the occasional long
function is the price of a rule that never needs a judgment call.

### 1.2 What this does *not* govern

Selector auto-deref — `p.x`, `p.x = v`, `p.m()` — is a separate mechanism and is untouched
by this RFC. It resolves off the receiver's own inferred type with no expected type
involved at all, so provenance does not arise. Two independent rules, not one rule with an
exception.

---

## 2. Consequences: none, today

Applying the rule to the implemented behavior in Motivation §1:

| position | category | rule says | today |
|---|---|---|---|
| `let`/`var` annotation | 1 | fires | fires |
| ascription | 1 | fires | fires |
| `return` / `break` | 1 | fires | fires |
| tail expression | 5 (inherits) | inherits | fires |
| struct-literal field | 2 | does not fire | does not fire |
| `match`/`if` arm | 5 (inherits) | inherits | does not fire |
| call argument | 2 | does not fire | does not fire |
| binary operand | 3 | does not fire | does not fire |
| index / array element | 4 | does not fire | does not fire |

Every row agrees. **This RFC is a formalization with zero behavior change**, which is the
strongest available evidence that the rule is a description of the design rather than a
constraint imposed on it after the fact — with the caveat recorded in §1.0 that this became
true only after the implementation was corrected to be genuinely positional.

One row deserves a note: `match`/`if` arms inherit, and today inherit from a parent that
does not propagate, so they do not fire. If arm propagation is ever fixed (it is a plausible
independent improvement), they would begin firing when the parent is category 1 — e.g.
`let c: i64 = match b { true => r, false => r };`. That is the correct outcome under the
rule, not a violation of it, and it is worth knowing in advance that the change would have
that effect.

---

## 3. Enforcement

Replace the bare expected type with one that carries its provenance:

```rust
#[derive(Clone, Copy)]
pub(super) struct Expected<'a> {
    pub ty: &'a Type,
    pub origin: Origin,
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Origin {
    /// let/var annotation, ascription, enclosing return/break type.
    AuthoredHere,
    /// Callee parameter types, struct field declarations.
    AuthoredElsewhere,
    /// Another operand's inferred type.
    SiblingInferred,
    /// Index u64, array element decomposition, other compiler bookkeeping.
    Structural,
}
```

`construct_expr`'s signature becomes `construct_expr(expr, expected: Option<Expected<'_>>,
ctx)`. `maybe_read_copy` is called only where `origin == AuthoredHere`. Inheriting sites
(block tail, arms, elements) pass the parent's `Expected` through unchanged and must never
construct a fresh `AuthoredHere`.

Three things this buys that a comment would not:

- **New expected-type suppliers must classify themselves.** There is no default; the
  author of the next hint-threading change picks an origin deliberately. RFC-0111's
  widening becomes `AuthoredElsewhere` and cannot silently widen read-copy.
- **RFC-0111 is unblocked and independent.** Bare-variant resolution fires on *any*
  origin — the expected type is equally usable for choosing an enum whatever authored it.
  Only read-copy is origin-gated. The two features stop competing for one knob.
- **The drift in Motivation §1 becomes unrepresentable.** A rule stated as "everywhere an
  expected type is known" cannot be checked; `origin == AuthoredHere` can.

Cost: mechanical but wide — every `construct_expr` call site gains a classification. There
are roughly two dozen. No new machinery, no new passes.

---

## 4. The two extensions RFC-0110 originally proposed, re-examined

RFC-0110, in the version that reached `3-integrated` on 2026-07-20, proposed widening read-copy to call arguments
and binary operands. Both are declined under §1's rule. The original arguments are recorded
here rather than discarded, because they were substantive and correct on their own terms.

### 4.1 Call arguments of monomorphic callees — declined

**The original argument, which still holds factually.** RFC-0067a §3a's text justifies
excluding call arguments by saying "the argument position has no declared-type-of-its-own
for the rule to compare against." That is not true for monomorphic callees: `param_hints`
(`construction.rs:2750`) already extracts each parameter's declared type and threads it
into `construct_expr` for every argument. The expected type genuinely exists and already
flows through the same path the five firing sites use; `maybe_read_copy` simply is not
called afterward. So the gap is an oversight in the sense that nothing *prevents* closing
it.

**Why it is still declined.** The type is authored in the callee's declaration, not here —
category 2. `f(r)` reads as passing a reference; whether it silently becomes a copy depends
on a signature elsewhere in the file, or in another module. That is exactly the indirection
the Go model exists to remove, and "we could" is not "we should."

Note also that *generic* callees remain a genuine limitation regardless:
`instantiate_scheme_for_call` needs argument types first in order to infer the callee's
type-parameter instantiation, so no hint exists before argument construction on that path.
Firing on monomorphic calls only would mean `f(r)` compiles and `g(r)` does not, for
reasons invisible at the call site — a worse boundary than "never."

The existing negative fixture `neg_06_no_read_copy_at_call_argument.mtl` stays valid, rather
than being inverted.

### 4.2 Binary operator operands — declined

**The original argument.** `construct_binop` (`construction.rs:3861`) calls `.is_numeric()`
on each operand's *raw* constructed type with no peeling, so `Type::Reference` fails
outright and `p + q` for `p, q: &i64` errors at `T0005` with no workaround short of a
throwaway `let` per operand. `peel_type_references` already exists in the same file. Cheap
to fix.

**Why it is still declined.** Category 3: there is no authored type anywhere in `r + 1` —
the expected type is the *other operand's* inferred type. Firing here would mean an
implicit deref driven by a type nobody wrote. Once RFC-0110's `*` exists the workaround is
`*p + *q`, which is one character per operand rather than a throwaway binding, so the
original motivation largely evaporates.

**A question RFC-0110 left open here has now been answered, and it turned out not to
belong to either RFC.** RFC-0110 noted that `Eq`/`Ne`/`And`/`Or` return `Type::Boolean`
unconditionally in `construct_binop` and that their operand compatibility checking could not
be located, and asked whether `&i64 == &i64` compares referents or addresses today.

It does neither: it typechecks and then aborts with `[I0001] internal error: binop:
unsupported operand types ... (typechecker should have caught this)`. There is no semantics
to discover. `construct_binop`'s `Eq | Ne` arm has no operand check at all — Pass 1 only
constrains the two operands to unify with each other, so mixed types are caught by
unification while same-type-on-both-sides reaches an evaluator whose `==` arms cover only
the numeric scalars, `Boolean`, `Str` and `Char`. This is not reference-specific: structs,
enums (including `Perhaps`), arrays, tuples and unit all behave the same way.

**Filed as issue #561**, with the design fix (routing `==` through the `Eq` aspect that
already exists at `stdlib/core.mtl:194` and already works via `.eq()` method dispatch)
tracked separately at #259 / RFC-0062. Neither is this RFC's business, and neither is
RFC-0110's — auto-deref has nothing to do with it, and the bug predates both. Recorded here
only so the trail from RFC-0110's open question to its answer is not lost.

---

## 5. Alternatives considered

- **Leave it as documentation.** Fix RFC-0067a §3a's text to describe the five real sites
  and stop there; the rule holds by convention. Cheapest, and honest about what most
  languages do. Rejected for the Motivation §2 reason specifically — RFC-0111 is actively
  going to widen hints, and convention does not survive a change made for an unrelated
  reason by someone who has not read this RFC.
- **Strict Go: retire read-copy entirely**, so even `let y: i64 = r;` requires `*r`. Most
  consistent with RFC-0110's model, and it makes this whole RFC unnecessary. Rejected: §3a
  is implemented and integrated, retiring it is a breaking change across existing code, and
  the annotation is right there at the use site — the ambiguity that justifies requiring a
  sigil elsewhere genuinely is absent here.
- **A syntactic locality rule** ("the annotation is on the same statement"). Rejected —
  formatting-sensitive, needs a threshold for `return`, and gives different answers for the
  same code reflowed. §1's structural question has an exact answer everywhere.
- **Origin as a boolean rather than a four-way enum.** Simpler, and only the
  `AuthoredHere` distinction is load-bearing today. Rejected narrowly: the four categories
  cost nothing extra to carry and make the *reason* a site does not fire self-documenting
  at each call site, which is most of the value when someone adds the twenty-fifth one.

---

## 6. Unresolved questions

1. **Does `return` stay category 1?** §1.1 argues yes and it matches today's behavior, but
   it is the single place where the "authored in the enclosing declaration" framing is
   doing real work rather than confirming the obvious. Worth a second opinion before this
   is accepted.
2. **Should `match`/`if` arms propagate the parent's expected type at all?** They do not
   today (Motivation §1), which is why §2 shows no behavior change. Fixing that is
   plausibly desirable for RFC-0111 independently, and §2 notes it would make copy-out
   start firing in arms. Not proposed here; flagged so it is a decision rather than a
   surprise.
3. ~~**`Eq`/`Ne` on references.**~~ Answered and moved out — see §4.2. It is a general
   `==` typechecking hole, not a reference or auto-deref question; issue #561, with the
   aspect-dispatch design fix at #259 / RFC-0062.
4. ~~**The solve-order dependency — fix it, or write it into the rule?**~~ **Resolved
   2026-07-21: fixed.** See §1.0. The peel test now runs against the substituted type, so
   §1's rule is positional in fact and not only on paper.
5. **Does read-copy fire on the inference-derived expected type (category 6)?** The safe
   default, consistent with the rest of §1, is no — it is not authored by anyone. But this
   category only came into existence with metel-core#565 and has had no design attention.
   §1's rule as written already excludes it (it fires *iff* category 1), so the answer is
   "no" by construction; what is unresolved is whether that is the intended answer or an
   accident of how the rule was phrased before the category existed.

---

## References

- RFC-0067a (Reference Types, implemented) — §3a's read-copy is the mechanism this RFC
  scopes; Motivation §1 documents where its text overstates its implementation.
- RFC-0110 (Explicit Dereference Operator) — this RFC was split out of it.
  RFC-0110 keeps the write side and explicit `*`; §4 here re-examines and declines the two
  read-side extensions it originally carried. Neither RFC depends on the other's outcome.
- RFC-0111 (Unqualified Enum Variants in Expression Position) — Motivation §2 argued the
  two RFCs turn the same knob in opposite directions and that §3's origin tag was needed to
  decouple them. **That coupling turned out not to exist** (RFC-0111 §1.3, corrected
  2026-07-21): method arguments and struct-literal fields already carry hints, so RFC-0111
  widens nothing and needs no tag to stay safe. Motivation §2's argument for this RFC is
  weaker as a result — the tag's value is now the forward-looking one (a *future* widening
  cannot silently widen auto-deref), not an active conflict between two in-flight RFCs.
- RFC-0045 (Mutable Address-Of for Lvalue Paths, implemented) — field/index write-through;
  a write-side mechanism, unaffected by this RFC (§1.2).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
