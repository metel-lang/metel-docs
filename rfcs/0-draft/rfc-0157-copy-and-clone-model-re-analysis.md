---
id: rfc-0157
title: "Copy and Clone Model Re-analysis"
date: '2026-08-31'
status: draft
target:
---

> **This RFC is analysis and direction-setting, not a language change.** It exists to
> record a trade-off study that was never written down: Metel took `Copy`/`Clone` and
> implicit-copy semantics from Rust, and the closure-capture default from a pre-ownership
> PoC, and no RFC has since asked whether that whole shape is the one Metel wants. Nothing
> below is asserted as decided — every design choice that isn't already shipped behavior
> is an Open Question. Concrete mechanism changes, if any survive review, spin out into
> successor RFCs or amendments to RFC-0135 / RFC-0006, named per option in §5.

> **Origin, 2026-08-31.** Opened out of the RFC-0050 (Closure Capture Lists) correction
> pass. RFC-0050 had a `move` capture specifier; reframing it off `linear` reduced it to
> "do an ordinary affine move at the capture site," at which point it had no reason to be
> a keyword — an affine move takes none anywhere else in Metel. Whether closure capture is
> a deliberate exception turns on the closure-capture default (RFC-0006's clone-by-default)
> and the `Copy`/`Clone` model under it. RFC-0050 dropped `move` and deferred
> ownership-transfer capture to "a future RFC that settles the default." This is that RFC.

## Summary

Metel's value-duplication model is inherited, not designed:

- **`Copy`** — an opt-in aspect (`extend T: Copy;`) marking a type whose by-value use is
  an implicit, cheap duplication rather than a move. Taken from Rust essentially verbatim,
  including the `Copy`/`Drop` mutual-exclusion rule (RFC-0071 §4) and the requirement that
  every field be `Copy` (`check_copy_impl_eligibility`).
- **`Clone`** — a separate aspect (RFC-0080, `1-under-review`) for explicit, possibly
  expensive duplication via `.clone()`, with a blanket `extend<T: Copy> T: Clone`.
- **Closure capture default** — RFC-0006 captures every free variable *by deep clone* at
  closure-creation time. This predates RFC-0071's affine ownership model and is the one
  place in the language where "use a value by value" means clone rather than move.

This RFC surveys the drawbacks of that model — the invisibility and API-stability hazard
of implicit copy, the doubled vocabulary of the two-aspect split, the `Copy`/`Drop`
cliff, the model's existing non-uniformity across named vs. structural types, and the
capture-default inconsistency — and the alternatives, from "keep it, rename via RFC-0135"
through "move-by-default with explicit duplication" to "implicit copy only for a closed
primitive set." A prior-art survey (Rust, C++, Swift, C#, Hylo, and the Go /
uniqueness-typed / pure-functional families) grounds the comparison. It recommends a
direction and names what each direction would cost.

---

## Motivation

### Why re-open a shipped model

Three things make this worth a dedicated document rather than a paragraph in RFC-0135:

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

3. **A concrete downstream design is blocked on it.** RFC-0050 cannot answer "does moving
   a binding into a closure need a keyword" without a position on whether closure capture
   by value should mean move (consistent with `let y := x`) or clone (RFC-0006 as it
   stands). That question is a specific instance of the general one.

### The drawbacks, stated precisely

**D1 — Implicit copy is invisible at the use site, and its presence or absence is an
API-stability hazard.** A `Copy` type silently duplicates on every pass, assignment, and
return. Removing `Copy` from a type — e.g. adding a `String` field to a struct that was
all-`i64` — is not a local change: it flips every by-value use of that type across the
whole program from copy to move, and the errors surface at those distant use sites, not
at the type definition. `Copy`-ness is effectively part of a type's public contract with
no syntax at the use site acknowledging it. Rust lives with this; the question is whether
Metel, which has the chance to decide now, should.

**D2 — Two aspects for one idea.** `Copy` and `Clone` are separate aspects connected by a
blanket impl, such that `.clone()` on a `Copy` value is a syntactic no-op that still
type-checks and still appears in code. Newcomers must learn both, when to write
`.clone()` (only for non-`Copy` `Clone` types), and why calling it on an `i64` is
allowed but pointless. RFC-0080 §1 preserves the split deliberately ("`Copy` (implicit,
free) and `Clone` (explicit, potentially expensive) is preserved") — this RFC asks
whether that distinction needs two *aspects*, or whether it is better modeled as one
duplication operation whose cost is a property of the type.

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

**D5 — The closure-capture default contradicts move semantics.** Everywhere in Metel a
non-`Copy` value used by value is *moved* (`let y := x;`, `f(x)` — no keyword, RFC-0071).
A closure that captures a free variable by value *clones* it (RFC-0006). So the same
surface act — "name an outer binding in an inner scope" — means move in a block and clone
in a closure body. RFC-0006 chose clone before RFC-0071 existed; nothing has re-tested
the choice against the settled model. Its consequence is visible in RFC-0050: because
capture is clone, a non-`Copy`, non-`Clone` value cannot enter a closure at all, and
RFC-0050 needs a `move`-shaped escape hatch — which then wants a keyword only because the
default is surprising.

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
- **P3 — Unify on multiplicity and go past RFC-0135.** B3 + an Axis-A decision. Requires
  RFC-0135 to land first and then extends it from "rename" to "the model."

### Closure-capture default (the D5 sub-question)

Independent of Axes A/B, RFC-0006's default can be restated as: **by-value capture uses
the same rule as by-value use in a block.** Under RFC-0071 that means a non-`Copy` free
variable is *moved* into the closure (consumed in the enclosing scope), a `Copy` one is
copied, and a `Clone`-not-`Copy` one is an error unless explicitly `.clone()`d at the
capture site — exactly `let y := x` semantics. Cross-closure sharing and
mutate-the-outer-binding stay on explicit references (RFC-0050's `&`/`&var`), which is
already the design. This would:

- make ownership-transfer capture need no keyword (settling RFC-0050's deferred question
  as "no specifier — bare capture of a non-`Copy` value is the move");
- change an observable default (a closure that captures `s: String` today leaves `s`
  usable; under this it consumes `s`), so it is a breaking change requiring the
  edition/migration treatment RFC-0017 or a `--edition` gate provides;
- need a decision on whether an unannotated closure should *ever* implicitly move, or
  whether an explicit capture list is required the moment a move would happen (the
  "explicit at the definition site" principle RFC-0050 and the *Implicit mutable capture*
  rejection both lean on).

---

## Recommended direction

Stated as a recommendation for review to push on, not a decision. The Prior art survey
below is the main evidence base: no language that started from an explicit model has
moved toward more implicitness, the fully-open end (C++, Go) is uniformly regretted, and
for D5 every surveyed language moves into a closure by inference or an expression, never
a per-capture keyword.

1. **Do not ship RFC-0135 as a pure rename first.** Renaming `Copy` → `many` before this
   analysis concludes bakes A1 + B1 into the vocabulary and makes P1/P2 a second rename.
   Either sequence RFC-0135 after this RFC, or fold RFC-0135's declaration-site spelling
   into whichever position wins here.
2. **Lean toward P1 (closed implicit set + single explicit duplication operation).** It
   removes the three drawbacks that are actually costs rather than unfamiliarity (D1, D2,
   D3), it is the smallest step that does so, and it makes D4 a definition rather than a
   fragmentation. P2 (Hylo's shipped model) is cleaner still but pays more ergonomically
   than Metel's audience is likely to accept; P0 pays nothing and fixes nothing.
3. **Adopt the D5 capture-default change (`let y := x` semantics for by-value capture)**
   regardless of the Axis-A/B outcome, behind an edition gate, and require an explicit
   capture list at the point a capture would move. This settles RFC-0050's deferred
   question in the "no keyword" direction (matching C++ init-capture and Rust's
   `move(expr)` direction) and makes closures consistent with the rest of the language.

If P1 is adopted, the follow-up work is: a keyword/marker for the closed implicit set and
its eligibility rule (successor RFC); collapsing `Clone` into a single duplication aspect
(amend RFC-0080); restating structural-type duplication in the new terms (amend or
supersede RFC-0135); the capture-default edition change (amend RFC-0006, unblock
RFC-0050).

---

## Relationship to existing RFCs

- **RFC-0135 (Multiplicity for Ordinary Types, `1-under-review`, #892)** — overlaps most.
  RFC-0135 is a vocabulary/spelling change that assumes the model; this RFC questions the
  model. They should be reviewed together and sequenced deliberately (see Recommended
  direction §1). If P0 wins, RFC-0135 proceeds unchanged; otherwise RFC-0135 is amended
  or absorbed.
- **RFC-0134 (Closure Call Capability, `2-accepted`, #269)** — not in scope to reopen.
  Its `call_multiplicity` axis (does *calling* a closure consume a capture) is orthogonal
  to *by-value-use* duplication; a change here would at most re-spell the `use_multiplicity`
  field RFC-0134 §4 already carries.
- **RFC-0050 (Closure Capture Lists, `1-under-review`, #803)** — the immediate
  beneficiary. RFC-0050 deliberately dropped its `move` specifier and deferred
  ownership-transfer capture to this RFC. If §Recommended-direction 3 is adopted, RFC-0050
  needs no new specifier; if the capture default is left as-is, RFC-0050 (or this RFC)
  must design one.
- **RFC-0006 (Closure Capture Semantics, `4-implemented`)** — the D5 change amends it.
  It is `4-implemented`, so this touches settled spec text and must go through the normal
  review/accepted/integrated path plus an edition/migration story before any code moves.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — the settled affine
  foundation this RFC measures the model against. §4 (Copy/Drop exclusion) is the D3
  target. Not proposing to reopen affine-by-default itself.
- **RFC-0080 (Stdlib Aspects — Clone…, `1-under-review`)** — owns the `Clone` aspect;
  B2/B3 would fold it in. If P0 wins, RFC-0080 is unaffected.
- **RFC-0123 (Field-Wise Row Constraints, `1-under-review`)** — the named fix path for "records
  can never be `Copy`." Whatever this RFC concludes about structural types should be
  reconciled with RFC-0123 rather than duplicating it.
- **RFC-0126 (`T[]` as a Copy view, `4-implemented`)** and **`metel-core#263`** (`[T;
  N]` Copy arm), **RFC-0061 §6/§7.2** (tuples / fn-pointers) — the concrete structural
  cases D4 enumerates; each is a place a unified rule would have to land or explicitly
  exempt.

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

### What the survey suggests for Metel

1. **The fully-open, fully-implicit end (C++, Go) is uniformly regretted.** The
   value-category-without-a-cost-signal middle (C#) is only safe with discipline rules.
   The two models people are actually comfortable with are Swift's
   implicit-copy-plus-COW (needs runtime COW Metel lacks) and Hylo's
   no-implicit-copy-plus-conventions (P2).
2. **No language that started explicit has moved toward more implicitness.** Rust, our
   closest relative, is moving the other way. This weighs against **P0** and toward
   **P1/P2**.
3. **For D5 specifically:** every surveyed language that can move a value into a closure
   does so by inference or by an *expression* (`std::move`, `move(expr)`), never a
   dedicated per-capture keyword. This independently corroborates RFC-0050's removal of
   its `move` specifier and recommendation 3.
4. **Capture *lists* are common and un-regretted** (C++, Swift, Rust's direction).
   RFC-0050's list survives the comparison cleanly; only the `move` specifier *inside*
   it lacked prior-art support.

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

1. **Is P1's closed implicit set defensible, and what defines membership?** Scalars and
   `bool`/`char`/unit are uncontroversial; the hard part is whether user PODs can join
   (a `copy struct` keyword with `check_copy_impl_eligibility`-style rules — which
   reintroduces a weaker D1) or whether the set is truly language-fixed (cleaner, but
   `Vec2 { x: f64, y: f64 }` then always moves, which many will find surprising).
2. **Does D3 (`Copy`/`Drop` exclusion) actually need to hold in Metel?** Rust's reason is
   specific to its move/drop-flag model. If Metel keeps a duplication operation distinct
   from an implicit-copy marker (B2), a `Drop` type being `.dup()`-able may be perfectly
   sound. Needs a soundness argument either way, checked against `--move-check`'s design.
3. **Edition/migration cost of the D5 capture-default change.** How many fixtures and
   stdlib closures actually rely on capture-by-clone leaving the outer binding usable?
   Measure before committing. Is `RFC-0017`'s edition system far enough along to gate it,
   or does this wait on that?
4. **Should an unannotated closure ever implicitly move a capture, or must a capture list
   be present the moment a move would occur?** The stricter rule is more predictable and
   matches RFC-0050's exhaustiveness philosophy; the looser rule is less boilerplate for
   the common "make a closure that owns this and return it" case.
5. **Sequencing with RFC-0135.** Block RFC-0135 on this RFC, run them concurrently with a
   shared reviewer, or let RFC-0135 ship P0 and treat this as a possible future
   super-session? The Recommended direction argues for the first; reviewers may disagree.
6. **Is this too large for one RFC?** The model critique (Axes A/B) and the capture
   default (D5) are separable. If D5 is the only part with a blocked consumer (RFC-0050),
   a reviewer may want D5 split into its own fast-tracked RFC and the model critique left
   as a longer-horizon document. Recorded as a real option, not resisted.
7. **Prior art beyond Rust. ✓ Addressed** — see the Prior art section above (Rust, C++,
   Swift, C#, Hylo, plus Go / uniqueness-typed / pure-functional families). Its four
   conclusions feed the Recommended direction; what remains open is which of P1 / P2 the
   survey's evidence best supports for Metel's specific audience, which is Open Question 1's
   territory, not a gap in the survey.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
