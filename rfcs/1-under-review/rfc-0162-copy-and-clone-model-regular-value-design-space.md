---
id: rfc-0162
title: "Copy and Clone Model — Regular-Value Design Space"
date: '2026-09-01'
status: under-review
target: v0.17.0
updated: '2026-09-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/924'
---

> **Extracted from RFC-0157 on 2026-09-01.** RFC-0157 kept the D5 decision (closure-capture
> default = `move`) and is `3-integrated` with the v0.13.0 closure cluster; this RFC carries the
> longer-horizon regular-value `Copy`/`Clone` model critique, design space, prior-art survey,
> and open questions that D5 did not touch, so they remain trackable.

> **Status — under review (2026-09-01).** Extracted from RFC-0157 on 2026-09-01: the regular-value Copy/Clone model critique, P0-P3 design space, prior-art survey, and open questions D5 did not touch. **Milestoned v0.17.0** — the "coherent Copy and closure capabilities" release, alongside RFC-0135 and RFC-0155.

> **Update (2026-09-02) — a further drawback (D6) and a fourth position (P4), raised in
> review.** D1–D4 all argue about *what* the model grants. D6 argues about **where the
> grant lives**: affine move semantics — the language's central ownership rule — is
> switched off, per type, by an ordinary aspect impl (`extend Foo: Copy;`), spelled
> exactly like `extend Foo: Display`; and once RFC-0093's derive mechanism exists,
> nothing on the current path stops it being switched off by a metaprogramming
> annotation (`#derive(Copy)`), as it routinely is in Rust. That critique is orthogonal
> to D1–D4 and to Axis A/B, so it opens **Axis C** (aspect / declaration keyword /
> attribute) and **P4** — keep Rust's model, both aspects, and the name, but move the
> *grant* onto the type's own declaration as the `copy` keyword **RFC-0163 already
> reserves** for function types. P4 is the one new position the Recommended direction's
> own familiarity argument does not rule out — it renames nothing — so the
> recommendation is left standing but no longer covers the whole space; P4's disposition
> is **OQ4**, and whether `Copy` should be derivable at all is **OQ5**.

## Summary

Metel's **regular-value** duplication model — `Copy` (implicit, cheap, opt-in) plus
`Clone` (explicit, possibly expensive), inherited from Rust essentially verbatim — was
never argued for in an RFC. This RFC is the trade-off study: the drawbacks of that model,
the design space for changing it, a prior-art survey across six language families, and a
recommendation.

**It is extracted from RFC-0157** (2026-09-01). RFC-0157 began as "Copy and Clone Model
Re-analysis" covering both the regular-value model *and* the closure-capture default (its
"D5"). D5 was decided — the closure-capture default is `move` — and RFC-0157 is now the
record of that decision, `3-integrated` as part of the v0.13.0 closure cluster. The
regular-value questions D5 did not touch — D1–D4, the P0–P3 design space, and the open
questions about whether Rust's model is the right one for Metel — have no v0.13.0
consumer and live here so they stay trackable. **Milestoned v0.17.0**, the "coherent
Copy and closure capabilities" release, alongside **RFC-0135** (`Copy → many`) and
**RFC-0155** — a reviewer opening that release's Copy-model work sees the analysis and
the proposals together. Its actionable outcomes map onto that milestone: the D3
relaxation (amends RFC-0071 §4, if OQ2's soundness argument holds), the RFC-0135
disposition (OQ3 — RFC-0135's own v0.17.0 review), and D4 (structural-types Copy
cleanup, #702/#263, already v0.17.0).

**Added in review (2026-09-02):** **D6** — the grant that switches off affine semantics
is an ordinary aspect impl, and would be a metaprogramming annotation once `#derive`
exists — with **Axis C** (where the grant lives) and **P4** (`copy` as a declaration
keyword, reusing RFC-0163's already-reserved word). D6 is orthogonal to D1–D4: it is
about the *mechanism* of the grant, not its content.

**Recommendation (carried from RFC-0157):** on regular values, *keep Rust's model* — no
rename (not to `many`, not to `Dup`), no P1/P2/P3, accept D1 as Rust has it. The only
endorsed value-side changes are **RFC-0158** (the `Clone`/`Share` split) and relaxing the
`Copy` + `Drop` ban (D3) *if* a soundness argument holds. This is a recommendation for
review to push on, not a decision. **It does not dispose of P4**, which was raised after
it was written and which its central argument — familiarity cost — does not reach, since
P4 renames nothing (OQ4).

---

## Motivation

### Why re-open a shipped model

Two things make this worth a dedicated document rather than a paragraph in RFC-0135.
*(A third — "a concrete downstream design (RFC-0050) is blocked on the capture-default
question" — was the original trigger and is now resolved: D5 is decided, RFC-0157.)*

1. **It was never argued.** `Copy`/`Clone` entered Metel as an assumed baseline — the
   earliest RFCs already use `Copy` as a given. RFC-0135 ("Multiplicity for Ordinary
   Types") is the closest thing to a re-examination, and it is explicit that it is *only*
   a vocabulary reframe: "squarely a vocabulary and mechanism-location proposal, not a
   soundness fix… one name for one concept… rather than two names." It renames `Copy` to
   `many` and moves the spelling onto the type declaration; it does not ask whether
   implicit copy should exist, whether the `Copy`/`Clone` split earns its cost, or what
   the capture default should be. Those are this RFC's questions.

2. **The interpreter hides the stakes.** The evaluator deep-clones on every by-value use
   regardless of `Copy`, so `Copy`, `Clone`, and move are today **observationally
   identical** at runtime (RFC-0071 §9 notes this directly — the enforcement is
   `--move-check`, off by default). Every decision in this area is currently being made
   with no runtime pressure telling us which way is right. That is an argument for
   settling the model *before* a compiler backend makes the differences load-bearing and
   expensive to revisit, not after.

### The drawbacks, stated precisely

**D1 — Implicit copy is invisible at the use site, and its presence or absence is an
API-stability hazard.** A `Copy` type silently duplicates on every pass, assignment, and
return. Removing `Copy` from a type — e.g. adding a `String` field to a struct that was
all-`i64` — is not a local change: it flips every by-value use of that type across the
whole program from copy to move, and the errors surface at those distant use sites, not
at the type definition. `Copy`-ness is effectively part of a type's public contract with
no syntax at the use site acknowledging it. Rust lives with this; the question is whether
Metel, which has the chance to decide now, should.

**D2 — Two aspects for one idea (and the wrong two).** `Copy` and `Clone` are separate
aspects connected by a blanket impl, such that `.clone()` on a `Copy` value is a syntactic
no-op that still type-checks and still appears in code. Newcomers must learn both, when to
write `.clone()` (only for non-`Copy` `Clone` types), and why calling it on an `i64` is
allowed but pointless. RFC-0080 §1 preserves the split deliberately ("`Copy` (implicit,
free) and `Clone` (explicit, potentially expensive) is preserved") — this RFC asks
whether that distinction needs two *aspects*, or whether it is better modeled as one
duplication operation whose cost is a property of the type. A second observation: the
split Metel *does* draw (by cost) hides a more useful one it *doesn't* (by meaning) —
`vec.clone()` produces an independent value, `rc.clone()` (RFC-0076: brand-preserving,
"same cell") produces another owner of shared state, and both go through the one `Clone`
aspect with identical spelling. That split is **RFC-0158**'s subject (see Axis B, second
cut); it is orthogonal to the rest of this RFC.

**D3 — `Copy` excludes `Drop`.** RFC-0071 §4 bans a type from being both `Copy` and
`Drop` (enforced in `coherence.rs` via `impls_actually_overlap`). This is inherited from
Rust's rule and is sound there for reasons tied to Rust's move semantics; in Metel it is
a hard expressiveness cliff (a plain-data type that wants a destructor — a
tracing/refcount-debug hook, a scope-exit assertion — must give up implicit copy) that
has not been independently justified for Metel's model.

**D4 — The model is already non-uniform.** Per RFC-0135's own corrected Background:
named types are `Copy` only by explicit `extend`; records can *never* be `Copy`
(RFC-0071 lines 45-69, RFC-0123 is the unbuilt fix); tuples have no aspect impls at all
(RFC-0061 §6); function pointers have a working blanket `Copy` (RFC-0061 §7.2); `T[]`
slices are unconditionally `Copy` (RFC-0126); `[T; N]` has a hardcoded `Copy` arm
(`metel-core#263`); closures compute `Copy`-ness per literal from captures (RFC-0134 §1).
That is six mechanisms, three of them missing. A re-analysis is the natural place to ask
whether a single coherent rule is reachable, or whether the fragmentation is inherent.

**D6 — A load-bearing language rule is gated behind an ordinary, and prospectively
derivable, aspect.** *(D5 is RFC-0157's closure-capture default, decided there; the
numbering is continued rather than reused.)* Added 2026-09-02 from review. Affine
by-value semantics (RFC-0071) is not a library facility — it is the rule that decides
what every by-value expression in the language *means*. Metel switches it off per type
through the ordinary aspect system:

```metel
extend Point: Copy;                                  // changes what every by-value
                                                     // use of Point *means*
extend Point: Display {                              // adds a method
    fun display(self) -> String { return "…"; }
}
```

Both are the same syntactic act — a user-written impl of a stdlib aspect on a local
type, resolved through the same registration path (`bare_impl_bounds`) — and the shorter,
less conspicuous one is the language-semantics switch. Three consequences, stated separately because they have different
weights:

1. **The grant does not look like what it does.** Nothing at an `extend … : Copy;` site
   marks it as changing the ownership discipline for a type, and the site need not be
   near the type: `extend` is a free-standing item, so a type's copyability can be
   granted in a different file from its declaration, while the behavior it governs shows
   up at every use site of the type. This is D1's invisibility problem seen from the
   *declaration* end rather than the use end, and it is the half a keyword can actually
   fix — D1's use-site half survives any Axis-C choice.
2. **Derive would make it worse, and Metel has not yet taken this on.** In Rust the
   grant is most often `#[derive(Copy)]`: an annotation whose ordinary job is generating
   method bodies, sitting in a list beside `Debug` and `PartialEq`, one entry of which
   silently changes the type's ownership behavior. Metel does not have this today —
   `Copy` has no deriver, and `#derive` itself is unimplemented (RFC-0093,
   `1-under-review`; RFC-0080 §1.3 specifies a derive for `Clone` only). But nothing on
   the current path forbids it: RFC-0093's mechanism registers an arbitrary comptime
   function as an aspect's deriver, and a deriver for a marker aspect is trivially
   writable — it emits the bare impl and nothing else. So Metel is one unremarkable
   registration away from Rust's situation, and the decision to allow or forbid it has
   never been made deliberately. **This is a live choice, not a settled inheritance.**
3. **The stop rule is the hard part, and this RFC should not pretend otherwise.** "A
   rule that changes the meaning of code that does not mention it should not be an
   ordinary impl" also reaches `Drop` (end-of-scope behavior, unmentioned at the scope),
   and arguably `Send`/`Sync` (what may cross a thread boundary). `Copy` is the extreme
   case — it changes the meaning of *every* by-value use, in every function, for every
   value of the type — but a proposal that moves only `Copy` to a keyword buys honesty
   for one aspect at the cost of making the aspect system itself less uniform. Axis C
   below is where that trade is stated; OQ4 is where it is decided.

---

## Background: how the model works today

Checked against `metel-frontend/` and the cited RFCs, not assumed. Much of this overlaps
RFC-0135's Background by design — this RFC and that one describe the same machinery.

- **`Copy` for named types is explicit-only.** `extend Foo: Copy;` (or conditional
  `extend<T: Copy> Foo<T>: Copy`), resolved via registered `bare_impl_bounds` in
  `typeinference/mod.rs`. No structural auto-derivation: an all-`Copy`-field struct is
  not `Copy` unless something wrote `extend`.
- **Field eligibility is enforced.** `typechecker/inference.rs`'s
  `check_copy_impl_eligibility` walks every struct field / enum-variant payload and
  rejects `extend … : Copy` with `T0001` if any is non-`Copy`. Empirically confirmed in
  RFC-0135's Background against the release binary.
- **`Copy` ⇒ `Clone`** by blanket impl (RFC-0080 §1.2): `extend<T: Copy> T: Clone { fun
  clone(self: &T) -> T { *self } }`. `Clone` alone (non-`Copy`) runs user code and may
  allocate.
- **`Copy` excludes `Drop`** (RFC-0071 §4), coherence-checked.
- **Structural types**: records never `Copy` (RFC-0071); tuples no impls (RFC-0061 §6);
  fn-pointers blanket `Copy` (RFC-0061 §7.2); `T[]` always `Copy` (RFC-0126).
- **Closures**: RFC-0134 §1 makes a closure `Copy` iff all captures are `Copy`; stored in
  a `use_multiplicity` field on `Type::Fun` (RFC-0134 §4 / RFC-0135's update note),
  because captures are absent from the type.
- **Closure capture**: RFC-0006 — by-value capture is a deep clone at creation time;
  cross-closure sharing needs an explicit reference (`&var` binding, and under RFC-0050 a
  `&var`/`&` capture specifier). RFC-0071 §9 reconciled its wording ("cloned" →
  "copied") but not its default.
- **Enforcement**: `--move-check` only, off by default (RFC-0071 §9 / `metel-core#267`,
  `#579`). Runtime is clone-everything, so the model is currently unobservable.

---

## Design space

Two orthogonal axes.

### Axis A — Does implicit, use-site-invisible duplication exist at all?

- **A1. Yes, open aspect (today).** Any type can opt in via `extend: Copy` (subject to
  field eligibility). Implicit at every by-value use.
- **A2. Yes, closed set.** Implicit duplication is a fixed, language-defined list —
  scalars, `bool`, `char`, unit, maybe fixed-size POD marked with a dedicated keyword —
  not a user-extensible aspect. Adding a type to the set is a deliberate, reviewed
  language change (or a single reserved keyword with a hard eligibility rule), so the D1
  hazard shrinks to "the keyword *is* the API commitment."
- **A3. No.** Every non-reference value moves on by-value use. Duplication is always an
  explicit call. Scalars included, unless A2-style carved out.

### Axis B — One duplication concept or two?

- **B1. Two aspects (today).** `Copy` (implicit, cheap) and `Clone` (explicit, any cost),
  linked by blanket impl.
- **B2. One aspect, cost is a type property.** A single `Dup`/duplication capability;
  whether a given `.dup()` is cheap is documented by the type, not by aspect identity.
  Implicitness (Axis A) becomes a separate marker, not a separate aspect.
- **B3. One axis via RFC-0135's `many`/`once`.** `many` = implicit duplication allowed,
  `once` = move-only; an explicit `dup()` bridges `once` → owned copy. `Clone`
  disappears into "`dup()` on a `once` type."

### Axis B, second cut — duplication vs. aliasing (→ RFC-0158)

B1/B2/B3 cut Axis B by **cost** (cheap vs expensive). There is an orthogonal cut by
**meaning**: `vec.clone()` yields an independent value, `rc.clone()` (RFC-0076:
brand-preserving — same cell) yields another handle to shared state, and both go through
one `Clone` aspect with identical spelling. Splitting them into `Dup` (independent) and
`Share` (aliasing, handle-category types only) is orthogonal to everything else in this
RFC — Axis A, B1/B2/B3, and P0–P3 all compose with it — and can be adopted on its own.
It is therefore tracked separately as **RFC-0158 (Share and Clone: Separating Aliasing
from Duplication)**, split out of this section 2026-08-31. It is not a prerequisite for,
or of, anything here.

### Axis C — Where does the copyability grant live? (D6, added 2026-09-02)

Axes A and B ask what implicit duplication *is* and how many concepts express it. Axis C
asks, given that some types are implicitly duplicated, **what syntactic act makes a type
one of them**. It is orthogonal to both: every A/B combination has to answer it, and
today's answer (C1) was inherited without being chosen.

- **C1. An ordinary aspect impl (today).** `extend Foo: Copy;`, resolved like any other
  bare impl, subject to `check_copy_impl_eligibility`. Uniform with the rest of the
  aspect system; D6 is the cost.
- **C2. A declaration-site keyword.** The grant is a qualifier on the type's own
  declaration — `copy struct Foo { … }` (P4) or `many struct Foo { … }` (RFC-0135) — and
  is not writable as an impl at all. `Copy` may survive as a *bound* (`T: Copy`) that
  only the compiler can grant, in the manner of RFC-0096's auto-impl aspects. The
  language rule is spelled with a language keyword, adjacent to the fields whose
  eligibility it depends on; a derive for it cannot be written, because there is no impl
  to emit.
- **C3. An attribute.** `#copy struct Foo { … }` — RFC-0095's mechanism rather than a
  keyword. Costs no keyword and reads as metadata, which is precisely the objection D6
  raises against `#derive(Copy)`: attributes are the part of the surface that is
  *supposed* to be removable without changing meaning. Listed for completeness; the
  weakest of the three.

C2 has one property C1 cannot have: it makes the grant unforgeable by metaprogramming.
Everything else it buys (locality, a keyword that looks like a language rule) is a matter
of degree. C1 has one property C2 cannot have: uniformity with `Drop`, `Send`, `Sync`,
and every other capability the language expresses as an aspect. That is the whole trade.

### Combined positions worth naming

- **P0 — Status quo + RFC-0135 rename.** A1 + B1, with `Copy` spelled `many` on the
  declaration. No drawback in §Motivation is addressed; D2/D4 are re-labeled. This is the
  currently-milestoned path (RFC-0135, v0.17.0).
- **P1 — Closed implicit set, keep explicit duplication as one operation.** A2 + B2.
  `i64`-and-friends copy implicitly; everything else moves and is duplicated with a
  visible `.dup()`; no `Copy` aspect, `Clone` folded in. Removes D1 (down to the keyword),
  D2, and D3 (a `Drop` type can still be `.dup()`-able), and forces a real answer to D4
  (structural types are just "not in the implicit set"). Cost: churn — every `extend:
  Copy` and every meaningful `.clone()` in stdlib + tests is rewritten; a new keyword;
  the closed set's boundary needs defending.
- **P2 — No implicit duplication.** A3 + B2/B3. Maximally explicit and uniform; every
  duplication is a call, every by-value use is a move. Removes D1 entirely. Cost: the
  largest ergonomic regression (`x.dup()` on integers) unless softened; likely too far
  for a systems-adjacent language, listed for completeness and as the honest endpoint.
- **P4 — Keep the model, move the grant to a keyword.** A1 + B1 + C2, with the keyword
  spelled `copy` (not `many`). Nothing about implicit duplication, the two-aspect split,
  or the use-site experience changes; `extend Foo: Copy;` becomes `copy struct Foo { … }`
  and `Copy` becomes a compiler-granted bound. Addresses D6 only, and the declaration
  half of D1; leaves D2 and the use-site half of D1 exactly as they are. **The only
  position here that changes no vocabulary** — which is why the Recommended direction's
  argument against P1/P2/P3 (familiarity cost) does not reach it. Detailed below.
- **P3 — Unify on multiplicity and go past RFC-0135.** B3 + an Axis-A decision. Requires
  RFC-0134 / RFC-0135 / RFC-0152 landed and mutually coherent first, then extends
  RFC-0135 from "rename `Copy` to `many`" to "one multiplicity mechanism for every
  consume-or-not operation, with `Copy` and `Clone` both dissolved into it." Detailed
  below.

### P3 in detail — unifying on multiplicity

> **Not recommended** (see Recommended direction) — it renames `Copy` away, which spends
> the regular-value familiarity budget this RFC concludes should be conserved. Kept in
> full because it is the most coherent *destination* if the `once`/`many` vocabulary ever
> proves itself through RFC-0134/0135/0152, and because articulating it clarifies what P1
> would have to stay compatible with.

RFC-0135 renames `Copy` to `many` for one operation (by-value use) and stops there,
explicitly keeping `Clone` as a separate aspect and closure-multiplicity as a separate
"home" (RFC-0135 §4). P3 asks what taking the reframe all the way looks like.

**One concept, parameterised by operation.** Every operation that either consumes a value
or leaves it usable gets a multiplicity. `once` = performing it consumes the value/place;
`many` = repeatable. `once` (affine) is the default everywhere; `many` is opt-in and must
be justified — structurally (every field is `many` for that operation) or by a
language-provided blanket.

| operation | `once` | `many` | today's name for the distinction |
|---|---|---|---|
| **use** — assign / pass / return by value | using consumes it | usable repeatedly | `Copy` vs non-`Copy` |
| **call** a closure | a call consumes a capture | callable repeatedly | RFC-0134 `call_multiplicity` |
| **mut-call** a closure | needs exclusive access to call | — | RFC-0153 |
| **receiver** on a method | `self` (by-value) method | `&self` method | already implicit, unnamed |

RFC-0134 §2 already draws the closure-`many` / receiver-kind connection; RFC-0135 adds
the *use* row. P3 is: treat all rows as one mechanism with an operation parameter, rather
than same word / separate homes.

**What changes past RFC-0135:**

1. **The name `Copy` is gone, not re-spelled.** No `Copy` aspect in the namespace;
   `is_copy(T)` becomes `use_multiplicity(T) == many`. Diagnostics read "`T` is `once`
   (move-only); used after move here" rather than "`T` is not `Copy`".
2. **`Clone` folds into a single duplication operation.** Today `Clone` is a distinct
   aspect with a blanket `extend<T: Copy> T: Clone`. Under P3 there is one `Dup` aspect,
   one method: `x.dup()` yields a second owned value regardless of `x`'s use-multiplicity
   — the trivial bitwise path for a `many`-use type, user code (possibly allocating) for a
   `once`-use type. Whether a given `.dup()` is *cheap* is a documented property (or a
   `@[trivial_dup]`-style attribute), not a second aspect identity. The `Copy`-is-free /
   `Clone`-may-cost distinction survives as a fact about the type, not as two names.
3. **Widening is one rule.** RFC-0152's "a `many` value satisfies a `once` slot at
   first-order sites" becomes the only variance rule, applied uniformly to closures and
   ordinary types instead of stated twice. `dup`-ability stays orthogonal — not part of
   the subtype lattice.

**The fork inside P3 — Axis A still has to be answered.** Does by-value use of a `many`
type *silently duplicate*?

- **P3a** — yes; today's `Copy` behavior with new vocabulary. The D1 hazard is unchanged.
- **P3b** — no; `many` means "`.dup()` is available and cheap," but by-value use still
  *moves*, and duplication is always a written `.dup()`. This is P2 with a guaranteed
  cheap path.

The multiplicity framing is what makes P3b coherent where `Copy`/`Clone` cannot express
it: *"this operation is repeatable"* and *"the compiler will silently repeat it for you"*
become **separable bits**. `once`/`many` governs legality (may this be used twice?); a
separate, smaller *implicit-insertion* flag — granted only to a closed primitive set —
governs whether the compiler inserts the duplication. That pairing is **P1's substance
expressed in P3's vocabulary**: P3b + "auto-insertion only for scalars/`bool`/`char`/unit"
is P1, reached from the other direction.

**D3 dissolves under P3b.** `Copy` excludes `Drop` today because auto-duplication plus a
per-instance destructor means an ambiguous or doubled drop. If `many` types *move* on
by-value use (P3b), every value has exactly one owner and a `Drop` type can be
`.dup()`-able with no contradiction — the exclusion is an artifact of auto-insertion, not
of `many` itself.

**Costs and caveats specific to P3:**

- **Vocabulary.** `once`/`many` is unfamiliar outside this RFC cluster (RFC-0135 OQ4),
  and P3 spends it everywhere, including in diagnostics beginners hit early.
- **Field proliferation on `Type::Fun`.** call-multiplicity (RFC-0134), mut-call
  (RFC-0153), the closure's own use-multiplicity (RFC-0134 §1), and dup-cheapness are
  four axes on one type. Real over-abstraction risk; needs a stop rule for which
  operations get a formal multiplicity and which stay documentation.
- **"One mechanism" is partly aspirational.** RFC-0135 §4's distinction holds under P3
  too: closure multiplicity is *per-expression* (a `Type::Fun` field, because two
  closures with the same signature can differ) while named-type multiplicity is
  *per-declaration* (a nominal fact). P3 unifies the *concept* and the *spelling*, not
  the representation — it is one idea with two storage forms, and the RFC should say so
  rather than overclaim.
- **Sequencing.** P3 cannot be evaluated until RFC-0134 (implemented), RFC-0135, and
  RFC-0152 are landed and known to compose; it is the latest-horizon option here.

**Why P3 is listed but not recommended.** It is the most coherent destination if the
`once`/`many` vocabulary proves itself through RFC-0134/0135/0152 in practice. But it is
a large type-system generalization to commit to before that vocabulary has any shipped
mileage, and its concrete user-visible payoff (P3b) is the same as P1's with more
machinery behind it. The Recommended direction treats P1 as the target and P3 as "the
shape to keep P1 compatible with," not a thing to build now.

### P4 in detail — `copy` as a declaration keyword

> Added 2026-09-02 with D6. Not covered either way by the Recommended direction below,
> which was written against P1/P2/P3; see OQ4.

**The spelling already exists.** RFC-0163 (`2-accepted`, v0.13.0) adds `copy` as a
function-type qualifier — `copy |i64| -> i64` is "a callable that may be duplicated by
value" — and **reserves `copy` as a keyword** alongside `once` and `var`. P4 spends no
new lexical budget: it uses the reserved word in a second position.

```metel
copy struct Point { x: i64, y: i64 }          // replaces `extend Point: Copy;`
copy enum Direction { North, South }
fun scale<T: Copy>(p: T, k: i64) -> T { … }   // bound spelling unchanged
```

**Mechanism.** `Copy` stays in the type system exactly as it is — a bound, the
`Copy ⇒ Clone` blanket (RFC-0080 §1.2), the `is_copy` predicate, `use_multiplicity` on
`Type::Fun` (RFC-0134 §4). What changes is only who may establish it for a named type:

1. `copy` on a `struct`/`enum` declaration registers the same bare impl bound that
   `extend Foo: Copy;` registers today, so nothing downstream of registration moves.
2. `extend Foo: Copy;` becomes a parse-or-coherence error with a fix-it pointing at the
   declaration. `Copy` joins the compiler-granted set — the same category as RFC-0096's
   auto-impl aspects, though granted by an explicit keyword rather than structurally.
3. `check_copy_impl_eligibility` (`typechecker/inference.rs`) runs unchanged, at the
   declaration instead of at the `extend`. Its diagnostic improves: "field `name:
   String` is not `Copy`" points at a field a few lines above, not at an item elsewhere
   in the program.
4. Structural and compiler-provided cases are untouched: `T[]` (RFC-0126), fn-pointers
   (RFC-0061 §7.2), `[T; N]` (`metel-core#263`), closures (RFC-0134 §1). P4 does not
   fix D4; it removes one of D4's six mechanisms from the *user-writable* surface, which
   makes the remaining fragmentation easier to describe (everything left is a compiler
   grant) without unifying it.

**What P4 answers, precisely.**

- **D6.1 (the grant doesn't look like what it does):** answered. A keyword in the type's
  own header is a language-rule spelling in the one place a reader looks for the type's
  shape.
- **D6.2 (derive):** answered *by construction*, which is the strongest form. There is no
  impl for a deriver to emit, so `#derive(Copy)` cannot be written and does not have to
  be forbidden by a rule someone has to remember. This is the argument's real payoff:
  the hazard is closed by the mechanism instead of by policy.
- **D6.3 (the stop rule):** **not** answered. P4 moves `Copy` and leaves `Drop`,
  `Send`, and `Sync` as aspects; a reviewer who thinks the D6 argument generalizes should
  say what the principled boundary is, or accept that `Copy` is being special-cased on
  the strength of being the extreme case rather than a different kind of case.
- **D1:** half. The declaration end becomes visible and local; the use site is unchanged,
  and removing `copy` from a declaration still flips every by-value use across the
  program. Anyone who wants D1 solved wants P1, not P4.
- **D2, D3:** untouched. (D3 is independently actionable via OQ2 under any position.)

**Open sub-questions P4 inherits or creates.**

1. **Conditional copyability.** `extend<T: Copy> Foo<T>: Copy` has no obvious keyword
   form. Candidates: `copy struct Foo<T> where T: Copy { … }`, or RFC-0135's
   `many<T: many> struct Foo<T>` shape. RFC-0135 §Open Questions raises exactly this for
   its own qualifier and does not settle it; P4 inherits the question verbatim, and it
   is the most likely reason to keep an `extend`-shaped escape hatch for the conditional
   case only — which would partially reopen D6.2.
2. **One word, two grammatical roles.** On a function *type*, `copy` is a requirement
   placed on a value whose capability was derived from its captures; on a *declaration*
   it is a grant checked against fields. RFC-0163 makes `copy` in closure-*literal*
   prefix position a parse error for exactly this reason ("a literal's concrete
   capability is derived from its captures, never asserted"). P4 must state the rule
   crisply: **`copy` in declaration position asserts and is checked; `copy` in type
   position requires and is matched.** A struct declaration is an assertion site because
   Metel has no structural auto-derivation for named types (Background above); a closure
   literal is not, because it does.
3. **RFC-0163's disjointness claim needs amending, not contradicting.** RFC-0163 says
   its use-multiplicity `copy` "is disjoint from RFC-0162's regular-value `Copy`/`Clone`
   model — it names the `use_multiplicity` field RFC-0134 already carries on `Type::Fun`,
   not a value-level aspect." That sentence is a scoping disclaimer written to keep an
   accepted v0.13.0 RFC out of an unsettled v0.17.0 argument, and P4 is the case where
   the two stop being disjoint: they become one keyword naming one property of values,
   with the field/aspect difference an implementation detail of where it is stored.
   Adopting P4 means amending that paragraph; it does not invalidate anything RFC-0163
   decided, and RFC-0163 needs no change unless P4 is adopted.
4. **Retroactive grants.** `extend Foo: Copy;` for a *foreign* `Foo` is already barred by
   coherence (RFC-0060), so C2 removes no capability that exists today. Worth confirming
   against `coherence.rs` before adoption rather than asserting from the RFC.
5. **Migration.** Mechanical: every `extend … : Copy;` in stdlib, fixtures, and docs
   becomes a declaration qualifier. Smaller than RFC-0135's migration (which changes the
   same sites *and* the word) and much smaller than P1's (which changes call sites).

**Relationship to RFC-0135.** P4 is RFC-0135's mechanism-location move without its
rename: both take the grant off `extend` and put it on the declaration; RFC-0135 spells
it `many` and retires `Copy`, P4 spells it `copy` and keeps `Copy` as the bound. The
Recommended direction's case against RFC-0135 (§3) is entirely about the rename — "the
rename throws away the most valuable transferable term" — and does not touch the
mechanism-location half. **P4 is therefore a concrete candidate answer to OQ3's
"narrowed to a de-cruft-only cleanup" option**: RFC-0135 narrowed to its declaration-site
qualifier, with the word left alone. Anyone reviewing RFC-0135 should weigh P4 against
it directly, since choosing both is not possible.

---

## Recommended direction (regular values)

Stated as a recommendation for review to push on, not a decision. The frame: **where
should Metel spend divergence budget — the regular-value duplication model, or closures?**
The closure half (D5) is decided (RFC-0157); this is the regular-value half, and the
recommendation is *not* to diverge.

1. **Keep `Copy` and `Clone`, and keep implicit-copy ergonomics (P0).** Do not rename
   `Copy` (to `many`, to `Dup`, or anything else) and do not adopt P1/P2/P3. The
   `Copy`↔`Clone` mental model and its use-site feel are years of Rust UX iteration Metel
   gets for free; **D1 stays, accepted, exactly as Rust has it** (editor inlay hints cover
   what visibility anyone wants). P1/P2/P3 are documented above as the honest design space
   and are **not recommended** — the familiarity cost on regular values exceeds the
   benefit.
2. **Remove two retro-compat artifacts, no more.** (a) The `Clone`/`Share` split —
   **RFC-0158** — so `Rc::clone`-as-aliasing stops sharing a name with `Vec::clone`-as-copy;
   additive, no rename, tracks where Rust is heading. (b) Relax the axiomatic `Copy` +
   `Drop` ban (D3) *if* a soundness argument holds for an explicitly-duplicated `Drop`
   type (Open Question 2); Rust would if backwards-compat let it.
3. **Recommend RFC-0135 not proceed as a `Copy` → `many` rename.** The rename throws away
   the most valuable transferable term for an internal-consistency gain. `once`/`many` can
   remain *internal* vocabulary shared with RFC-0134's call axis without renaming the
   surface aspect. Any genuine de-cruft in RFC-0135 (e.g. the `#derive` coupling) can fold
   into RFC-0158 or a small cleanup RFC.

4. **P4 is open, not recommended against (added 2026-09-02).** Items 1–3 were written
   against Axes A and B, where the argument is "Rust's regular-value vocabulary and
   use-site feel are worth more than the internal-consistency gain from changing them."
   P4 (Axis C — `copy` as a declaration keyword) makes no vocabulary change: the word
   `Copy` survives as the bound, the use-site feel is bit-for-bit identical, and the
   keyword is one RFC-0163 already reserves. The familiarity argument therefore does not
   apply to it, and neither endorsing nor refusing P4 follows from anything above. What
   it needs from review is an answer to D6.3 — whether "language rules should not be
   ordinary impls" is a principle Metel adopts (and then owes `Drop`/`Send`/`Sync` an
   answer too), or an observation about `Copy` alone that is not worth a special case.
   **OQ4** carries it. A reviewer who takes P4 should also read OQ3: P4 and RFC-0135 are
   competing answers to the same question, and only one can be adopted.
5. **Decide whether `Copy` is derivable, separately and sooner (added 2026-09-02).**
   Independent of P4's fate: `#derive(Copy)` does not exist today and the derive
   mechanism it would need (RFC-0093) is not accepted, so the cheap move is to record
   now that `Copy` has **no registered deriver** and that adding one is a language
   decision requiring its own RFC — rather than letting it arrive as an unremarkable
   registration once RFC-0093 lands. This costs nothing if P4 is adopted (the hazard
   closes by construction) and is the whole of D6.2's mitigation if it is not. **OQ5.**

The closure-side items (D5, and "keep investing in the closure-capability cluster") are in
**RFC-0157**.

---

## Relationship to existing RFCs

- **RFC-0157 (Closure Capture Default (Move), `3-integrated`)** — the parent. Carries D5
  (closure-capture default = `move`, decided) and the closure-cluster relationship; this
  RFC carries the regular-value model critique and design space it split off.
- **RFC-0135 (Multiplicity for Ordinary Types, `1-under-review`, #892)** — overlaps most.
  RFC-0135 renames `Copy` → `many` on the type declaration, assuming the model; this RFC
  questions the model and concludes the rename should **not** proceed — it spends the
  regular-value familiarity budget for an internal-consistency gain (Recommended direction
  §3). If a reviewer disagrees, P3 (§P3 in detail) is where the full rename leads.
  **Added 2026-09-02:** RFC-0135 is *two* proposals bundled — a mechanism-location move
  (grant onto the declaration) and a rename (`Copy` → `many`). P4 takes the first without
  the second, and is a direct competitor to RFC-0135 rather than a variant of it (OQ3,
  OQ4).
- **RFC-0163 (Function-Type Use-Multiplicity Surface, `2-accepted`, v0.13.0, #936)** —
  supplies P4's keyword. It adds `copy` as a function-type qualifier, reserves `copy`
  beside `once`/`var`, and explicitly scopes itself as *disjoint* from this RFC's
  value-level model. Nothing here changes RFC-0163 or asks it to change; but P4 is the
  position under which the two `copy`s become one concept, and adopting P4 means amending
  that disjointness paragraph (P4 in detail, sub-question 3). RFC-0163's rule that `copy`
  is a parse error in closure-literal prefix position is the precedent P4's
  assert-vs-require distinction has to be stated against.
- **RFC-0093 (Derive Registration, `1-under-review`, #799)** — the mechanism D6.2 is
  about. Its `#derive(Aspect)` registration would make a `Copy` deriver writable with no
  special effort; whether one may exist is OQ5, and is a question for this RFC, not for
  RFC-0093's general mechanism.
- **RFC-0096 (Auto-Impl Aspects, `0-draft`)** — the existing category of
  compiler-granted, not-user-writable aspects (`Send`, `Sync`, `Linear`). Under P4,
  `Copy` joins that category by keyword rather than by structural rule; reconcile the
  two framings if P4 advances.
- **RFC-0095 (Attributes and Metadata, `1-under-review`)** — supplies Axis C's C3
  (`#copy`), listed and not recommended.
- **RFC-0080 (Stdlib Aspects — Clone…, `1-under-review`)** — owns the `Clone` aspect.
  RFC-0158 amends its §1 (tighten `Clone` to independent-duplication-only; add `Share`).
  This RFC's recommended direction leaves `Clone` otherwise untouched.
- **RFC-0158 (Share and Clone, `1-under-review`)** — split out of this analysis's "Axis B,
  second cut": a new `Share` aspect beside `Copy`/`Clone`, no rename. One of the two
  regular-value changes the Recommended direction endorses. Orthogonal to P0–P3.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — §4 (Copy/Drop exclusion)
  is the D3 target. Not proposing to reopen affine-by-default itself.
- **RFC-0074 / RFC-0076 (Rc / Arc, Rc Brands)** — the handle types and brand machinery
  that already distinguish "aliases the same cell" from "independent" in the types;
  RFC-0158 gives that a surface verb.
- **RFC-0123 (Field-Wise Row Constraints, `1-under-review`)** — the named fix path for
  "records can never be `Copy`"; reconcile any structural-type conclusion with it.
- **RFC-0126 (`T[]` Copy view, `4-implemented`)**, **metel-core#263** (`[T; N]`),
  **RFC-0061 §6/§7.2** (tuples / fn-pointers) — the concrete structural cases D4
  enumerates; each is a place a unified rule would land or explicitly exempt.

---

## Prior art

How six language families answer the two questions this RFC poses — (A) does *by-value
use* silently duplicate, and (B) are "cheap implicit copy" and "explicit deep copy" one
concept or two — plus how each moves a value into a closure (the D5 angle). Sources are
listed at the end of this section.

### Rust — the model Metel inherited

`Copy` (implicit, marker aspect, bitwise, opt-in via `derive`/`impl`, every field must be
`Copy`, mutually exclusive with `Drop`) plus `Clone` (explicit `.clone()`, with a blanket
`impl<T: Copy> Clone for T`). This is D1+D2+D3 verbatim — Metel took the whole shape.

Known friction in Rust, from its own discussions:

- **`.clone()` noise** around `Rc`/`Arc`, where the call is semantically "make another
  handle to the same thing," not "duplicate the data" — the two are spelled identically.
- **The D1 hazard is real and lived-with**: adding a non-`Copy` field to a type silently
  flips every by-value use from copy to move, with errors at the use sites.
- **Direction of travel is toward *more* explicitness, not less.** The 2024–2026
  "ergonomic ref-counting" work (RFC 3680) proposes `use ||` closures and `move(expr)`
  *expressions* for precise capture control, plus a `Share`/`Claim`-style trait marking
  "clone that produces an alias." The stated conclusion after review: *"make explicit
  code ergonomic, not make everything implicit … some applications genuinely need to
  track where aliases are created."*
- **Closures** capture by inference (shared ref / unique ref / move, whichever the body
  needs); `move ||` forces by-value capture of *everything*. Note that non-`Copy` values
  the body consumes are *already* moved in without any keyword — `move ||` exists to
  override the inference for values that would otherwise be borrowed, which is not the
  situation Metel's clone-by-default closures are in.

Relevance to Metel: the language closest to ours has concluded that capture wants
*visible, precise* control — which supports RFC-0050's capture **list** — while its
mechanism for *moving into* a closure is either inference or an expression form, never a
per-capture keyword. That is exactly RFC-0050's `move`-specifier drop and this RFC's
recommendation 3.

### C++ — open implicit copy with user-defined hooks, no cost signal

Every class is copyable by default via an implicitly generated member-wise copy
constructor; the author may write their own or `= delete` it. Move (C++11) was added as
an *optimization of* copy, not a distinct concept. The Rule of Three/Five documents that
the five special members are coupled: declaring one suppresses or deletes others, and
"if moves are deleted, the compiler falls back to copy, potentially surprising users."

There is **no marker at all** distinguishing a cheap copy from an allocating one — the
cost is invisible at every call site, strictly worse than Rust's `Copy`/`Clone` split.
C++ is the endpoint Metel should not drift toward, and the strongest single piece of
evidence for D1.

Lambda capture lists (`[x, &y, w = std::move(z)]`) are explicit and close to exhaustive.
Moving a value into a C++ lambda is done with an **init-capture expression**
(`w = std::move(z)`), not a capture keyword — again the expression form, corroborating
recommendation 3.

### Swift — value/reference at the declaration; copies hidden, cost hidden by COW

`struct`/`enum` are value types (copied on assignment and at parameter boundaries);
`class` is a reference type. The copy is implicit and unmarked. Swift's answer to the
cost half of D1 is **copy-on-write**: `Array`, `String`, `Dictionary` and hand-written
value types wrap a reference-typed box and only physically copy on first mutation. So the
cost is paid lazily rather than made visible.

`~Copyable` (SE-0390, Swift 5.9, 2023) lets a type opt *out* of copyability. Swift's own
rationale: for a `Copyable` type "the distinction between borrowing and consuming
operations is largely hidden from the programmer, since Swift will implicitly insert
copies," and for a non-copyable one that distinction "becomes an important part of the
API contract." That is D1 stated from the other side — copyability is precisely what buys
the ability to *not* think about borrow-vs-consume.

Capture lists (`[weak self]`, `[x]`) are explicit but **not exhaustive** — unlisted
variables are still captured.

Relevance: Swift demonstrates the "value vs. reference at the type" alternative, and shows
that hiding implicit-copy cost comfortably requires COW machinery — a runtime mechanism
Metel's model does not have and RFC-0157 is not proposing to add.

### C# — value/reference at the declaration, and *no* cost mitigation

`struct` (value, bitwise/member-wise copy on assignment and argument passing) vs `class`
(reference). Like Swift without copy-on-write. Silent `struct` copies are a documented
footgun (mutable structs, hidden defensive copies), and the standard guidance is
"keep structs small and immutable." Confirms that an open value-type category with
neither a cost signal nor COW needs external discipline rules to be safe.

### Hylo (formerly Val) — mutable value semantics, implicit copy *forbidden*

Every type is a value type; **implicit copies do not exist**. Duplicating a value is an
explicit `x.copy()` call (the same shape as Rust's `.clone()`), and the language
"avoids hidden costs such as implicit copies and therefore avoids heavy dependence on an
optimizer for basic performance." Parameter passing uses explicit conventions
(`let` / `inout` / `sink` / `set`) rather than reference types, so every access a
function can make to a parameter is visible in its signature.

This is RFC-0157's **P2** endpoint, shipped and internally coherent in a systems-oriented
research language. The cost it pays is annotation burden and `.copy()` on small values;
Hylo absorbs much of that through its borrow/`sink` conventions. Evidence that P2 is
*achievable*; the open question is whether its ergonomics fit Metel's intended audience.

### Others, briefly

- **Go** — `struct` values copy shallowly on assignment and at call boundaries with no
  user hook and no marker (the `sync.Mutex`-copied-by-value bug class). "Implicit copy,
  zero control": the position no one defends.
- **Clean (uniqueness types), Pony (reference capabilities), Vale (region borrowing)** —
  sidestep duplication by governing *aliasing* instead: a value is either uniquely owned
  (safe to mutate/consume) or shared (immutable). Metel's affine model (RFC-0071) already
  sits in this family, which is why "who else can see this value" is largely a *settled*
  axis for Metel and "is duplication implicit" can be reasoned about separately.
- **Haskell / ML / pure-functional** — immutability + GC means duplication is never
  observable; there is no `Copy`/`Clone` concept to design. Noted only to place the
  problem: it is specific to the mutable-value-semantics design point Metel has chosen.

### Where the grant lives — the Axis C cut (added 2026-09-02)

The survey above asks what each language *does*; D6 asks what syntactic act *decides* it.
Re-read across the same languages, the answers line up unusually cleanly:

| Language | Copyability decided by | Ordinary user-written impl? | Reachable by metaprogramming? |
| --- | --- | --- | --- |
| **Rust** | `impl Copy` / `#[derive(Copy)]` | yes | **yes** — the common case |
| **C++** | the class's own special members (`= delete`, user-declared) | no — only the class's own members | no |
| **Swift** | default-on; suppressed at the declaration (`~Copyable`, SE-0390) | no — `Copyable` is compiler-known | no |
| **C#** | `struct` vs `class` — a declaration keyword | no | no |
| **Go** | `struct` — a declaration keyword | no | no |
| **Hylo** | nothing: there is no implicit copy to grant | n/a | n/a |

**Rust is alone in the "yes" column, and alone again in the derive column.** Every other
language that has implicit copying puts the decision in the type's own declaration —
usually as a keyword — and none of them let an annotation or macro flip it. That is not
an argument that Rust is wrong (C# and Go pay for their keyword with *no* opt-out at all,
which is worse in a different way), but it is the observation D6 rests on: the mechanism
Metel inherited is the outlier, and it was inherited without being compared.

**Hylo's row is the sharpest one.** Hylo has a `Copyable`-style trait and an explicit
`.copy()`, and nobody objects — because there, the trait grants a *method*, not a change
to what by-value use means. **D6's force is proportional to how much implicit behavior
the grant controls.** Under P2 (and mostly under P1) the objection dissolves without a
keyword, because there is no implicit behavior left to gate. So D6 is not only an
argument for P4: it argues for P1/P2 as well, from a direction D1–D4 do not cover — a
trait that gates nothing implicit is an unobjectionable trait.

### What the survey suggests for Metel

1. **The fully-open, fully-implicit end (C++, Go) is uniformly regretted.** The
   value-category-without-a-cost-signal middle (C#) is only safe with discipline rules.
   The two models people are actually comfortable with are Swift's
   implicit-copy-plus-COW (needs runtime COW Metel lacks) and Hylo's
   no-implicit-copy-plus-conventions (P2).
2. **No language that started explicit has moved toward more implicitness** — Rust is
   moving the other way. Read alone this weighs toward P1/P2. But the same survey shows
   the *cost* of moving: Swift needed COW machinery to stay comfortable, Hylo pays a
   standing annotation tax, and Rust's own motion is on the *closure/`Rc`* side
   (`use ||`, `move(expr)`, `Share`/`Claim`), **not** on plain `Copy` for scalars and
   structs — which nobody is trying to make explicit. That is the split the Recommended
   direction takes: leave plain `Copy` alone, follow Rust's actual motion on closures and
   the `Clone`/`Share` cut.
3. **For D5 specifically:** every surveyed language that can move a value into a closure
   does so by inference or by an *expression* (`std::move`, `move(expr)`), never a
   dedicated per-capture keyword. This independently corroborates RFC-0050's removal of
   its `move` specifier and Recommended direction 4.
4. **Capture *lists* are common and un-regretted** (C++, Swift, Rust's direction).
   RFC-0050's list survives the comparison cleanly; only the `move` specifier *inside*
   it lacked prior-art support.
5. **On Axis C, Rust is the outlier and Metel copied the outlier** (added 2026-09-02).
   Everyone else with implicit copying decides it at the declaration and puts it out of
   reach of metaprogramming. This is the clearest prior-art signal in the survey — much
   clearer than anything Axes A and B produced — and it costs almost nothing to follow
   (P4), because the keyword is already reserved and the word `Copy` is kept. Weigh it
   against the uniformity loss in the aspect system (D6.3), which is the real objection,
   not familiarity.

### Sources

- Rust `Copy`/`Clone`: the standard library reference. Ergonomic ref-counting / `use`
  closures / `move(expr)`: <https://rust-lang.github.io/rust-project-goals/2025h2/ergonomic-rc.html>,
  <https://blog.rust-lang.org/2025/11/19/project-goals-update-october-2025/>, RFC 3680.
- Swift `~Copyable`: SE-0390
  <https://github.com/swiftlang/swift-evolution/blob/main/proposals/0390-noncopyable-structs-and-enums.md>;
  value vs. reference types <https://www.swift.org/documentation/articles/value-and-reference-types.html>.
- C++ Rule of Three/Five: e.g. <https://leimao.github.io/blog/CPP-Rule-of-Five/>; init-capture
  in the C++ standard ([expr.prim.lambda]).
- C# structs: <https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/structs>.
- Hylo: <https://hylo-lang.org/introduction/>; move semantics comparison
  <https://lukas-prokop.at/articles/2024-11-29-move-semantics-in-rust-cpp-and-hylo>.

---

## Open Questions

1. **Is "no value-model change" the right call, or is D1 worse than it looks?** The
   recommendation accepts implicit copy's use-site invisibility and API-stability hazard
   as Rust does. A reviewer who thinks D1 bites harder in Metel's context — or that the
   interpreter's clone-everything phase is exactly the window to change it cheaply — would
   push toward P1. That case is made in full above; this records that it is a **live
   disagreement, not a closed one**. *Reopening condition:* a concrete API-stability
   incident in the corpus, or a compiler-backend decision that makes implicit copy
   expensive and the change costly to defer further.
2. **Does D3 (`Copy`/`Drop` exclusion) need to hold in Metel?** Rust's reason is specific
   to its move/drop-flag model. An explicitly-duplicated `Drop` type — `.clone()` runs
   user code, `Drop` runs once per real value — may be perfectly sound. **Needs a
   soundness argument checked against `--move-check`'s design.** This is the one D-item the
   recommendation proposes to act on beyond RFC-0158. *Reopening / advancing condition:*
   that soundness argument, or a concrete plain-data-with-destructor use case that the ban
   blocks.
3. **Disposition of RFC-0135.** The Recommended direction says the `Copy` → `many` rename
   should not proceed. Does RFC-0135 get refused, narrowed to a de-cruft-only cleanup (the
   `#derive` coupling, generic-`Copy` tidy), or folded into RFC-0158? A call for
   RFC-0135's own review, informed by this one.

4. **Should the copyability grant be a keyword rather than an aspect (Axis C / P4)?**
   Added 2026-09-02 with D6. The narrow question is whether `extend Foo: Copy;` should
   become `copy struct Foo { … }`, reusing RFC-0163's reserved word, with `Copy` demoted
   to a compiler-granted bound. The question review actually has to answer first is
   **D6.3**: is "a rule that changes the meaning of code that does not mention it should
   not be an ordinary impl" a principle Metel adopts — in which case `Drop` (and
   arguably `Send`/`Sync`) need an answer in the same breath — or is `Copy` a
   special case justified by degree alone? P4's cost is small and its migration is
   mechanical; its risk is a one-off exception to the aspect system that later looks
   arbitrary. *Advancing condition:* a stated stop rule that either confines the change
   to `Copy` on principle or names the other aspects that follow it. *Refusing
   condition:* review judging the aspect system's uniformity worth more than the grant's
   honesty — in which case OQ5 becomes the whole of D6's mitigation.
   **Coupled to OQ3:** P4 and RFC-0135 are competing answers; adopting P4 means
   RFC-0135 is narrowed away entirely, and adopting RFC-0135 forecloses P4's spelling.
5. **May `Copy` ever be derived?** Added 2026-09-02 with D6.2. Today the question is
   moot — `#derive` is unimplemented (RFC-0093) and `Copy` has no deriver — which makes
   this the cheapest decision in the RFC and the one with a deadline: it stops being
   cheap the moment RFC-0093 lands and a `Copy` deriver becomes an ordinary
   registration nobody has to justify. Under P4 it answers itself (no impl to emit).
   Under P0 it needs a written rule: `Copy` has no registered deriver, and adding one is
   a language change requiring its own RFC. *Advancing condition:* none needed — this
   can be recorded now, independently of every other question here. *Reopening
   condition:* a concrete case where hand-writing the grant is genuinely onerous, which
   for a marker aspect with a one-line spelling is hard to construct.

*(Prior art beyond Rust — addressed, see the survey above. The aliasing-vs-duplication
split — RFC-0158. The closure-capture default — RFC-0157, decided.)*

---

## Decision

**Outcome:** *(pending — analysis / direction-setting, `1-under-review`. Extracted from
RFC-0157 on 2026-09-01 so the regular-value questions stay trackable after RFC-0157's D5
was decided and accepted. The five Open Questions above carry reopening/advancing
conditions. The recommendation — no regular-value model change — is for review to endorse
or contest, and it does not dispose of P4 (OQ4) or of the derive question (OQ5), both
added 2026-09-02.)*
**Target:** v0.17.0 (metel-core#924) — the "coherent Copy and closure capabilities"
release, alongside RFC-0135 / RFC-0155. Nothing here blocks v0.13.0.
