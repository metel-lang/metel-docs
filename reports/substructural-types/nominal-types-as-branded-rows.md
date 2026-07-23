---
id: nominal-types-as-branded-rows
title: "Nominal Types as Branded Rows — A Structural-First Reconsideration"
type: report
status: active
last_synced_against_model: '2026-07-22'
supersedes: null
revives: null
---

# Nominal Types as Branded Rows

*Written 2026-07-22, out of a full audit of the records/views cluster
(`access-and-presence-rows.md`) that surfaced `HasField` as bolted onto nominal types
rather than derived from them, plus a chain of findings about `uses (…)` and RFC-0090's
own internal contradictions. This document asks a more radical question than that audit
did: what if every nominal type's canonical representation is `(brand, row)`, not just
tier-3's opt-in "named record"? It is a genuinely different thesis from
`access-and-presence-rows.md` and is kept separate deliberately, not merged into it —
that document argues within the current three-tier architecture; this one asks whether
the architecture itself should change underneath it.*

**Status: pressure-tested, not settled.** Several findings below are sharp enough that
the model's central promise — a single mechanism, invisible to ordinary code — is not
yet proven. Read this as the state of an argument in progress, not a proposal ready to
replace anything.

---

## 1. The intuition, stated plainly

Every nominal type — not just tier-3's opt-in "named record" — is represented as
`(brand, row)` under the hood. As long as a value has all its original fields, the
surface presents it exactly as an ordinary struct; nothing about writing or reading
`Handle` looks any different from today. When a field is moved out, the value's
*type* degrades to a narrower row of the same brand — `Handle` becomes `Handle.{ fd }`
— rather than becoming an opaque "partially moved" marker with no structural content.
Per-field multiplicity, on this view, is not a separate mechanism layered on top of
ordinary structs; it's what the existing representation already gives you, once the
representation itself is row-shaped by default. Ergonomic sugar is then a separate,
later question about how much of this stays invisible — not a justification for the
mechanism's existence.

---

## 2. What this responds to

`access-and-presence-rows.md`'s audit found that `HasField` as RFC-0090 §1 drafts it is
an **auto-derived aspect family checked externally** against an untouched `Type::Named`
struct — a fact *about* the type, computed by a separate mechanism, not a query against
the type's own structure. RFC-0090 §9 already sketches the alternative — "representing
every named type as `(row, brand)` internally... not elimination of the tag, but reuse of
it" — but §9 is the RFC's *last* substantive section, framed as a reconciliation against
an architecture (§1–§8) that assumes the opposite by default. This document asks what
happens if §9's move is taken as the foundation rather than an afterthought, **and pushes
it one step further than §9 itself does**: §9 is about sharing a representation for
*identity* purposes; nothing in it proposes that the row *degrades on partial move*. The
degradation is this document's own addition, not already present in RFC-0090.

---

## 3. What the model resolves immediately

### 3.1 `HasField` stops being bolted on

If every nominal type already carries a row, `HasField<"fd", i64>` is not a derived fact
computed by a second mechanism — it is the same row-membership query already used for
anonymous records and row-conditional impls. One representation, one query.

### 3.2 Presence and access collapse into one operation, not two roles of one mechanism

`access-and-presence-rows.md` §3.6 concluded "one row mechanism whose field types carry
the distinction" — presence and access as two *roles* of a shared solver. This model is a
cleaner unification than that: there is exactly **one operation, narrowing**, applied to
either an owned value (a partial move: `Handle` → `Handle.{ fd }`, fields are gone) or a
borrowed one (a view: `&mut Handle` → `record { fd: &mut i32 }`, fields are aliased
elsewhere). The distinction was never between two kinds of row — it was always about
whether the thing being narrowed is owned or borrowed, the same axis that already
distinguishes ordinary field access everywhere else in the language.

### 3.3 `uses (…)` stops needing a declaration

Once "which fields remain" is the value's actual, ordinary type, there is nothing left to
declare. The type checker already knows.

---

## 4. The sharp fork this surfaces: how does `Drop` dispatch?

Take `struct Handle { fd: i32, tag: u64 }` with a custom destructor tearing down `fd`.
Once `tag` is moved out, `self`'s type is `Handle.{ fd }`. When that value's scope ends,
does the custom `Drop::drop` fire?

**Reading (i) — `Drop` fires only against the exact original row** (brand *and* full
shape, not brand alone). A narrower residual reaching end-of-scope instead falls back to
ordinary recursive per-field drop. This reading has a concrete, serious hole:

```metel
struct Handle { fd: i32, tag: u64 }
impl Drop for Handle { fun drop(self) { close_fd(self.fd) } }

fun leak(h: Handle) {
    let t = h.tag;       // h narrows to Handle.{ fd }
}                        // h's scope ends here — reading (i): custom drop does NOT fire,
                         // fd (a bare i32, no Drop impl of its own) gets ordinary
                         // per-field drop, which does nothing. close_fd never runs.
```

**Reading (ii) — `Drop` is row-bounded, inferred from the body**, the same "accuracy
checking, not a declared-and-trusted annotation" discipline RFC-0109 §4.10 already
specifies for self-view narrowing. `drop`'s body reads `self.fd`, so its bound is
`HasField<"fd", i32>`; it fires on *any* residual satisfying that bound, regardless of
what else was moved out first. This closes the leak, and it also beats plain
decomposition (the earlier proposed fix for `uses (…)`) specifically on this case: no
wrapper type is needed, `fd` stays a direct field of `Handle`, `HasField<"fd", i32>`
stays satisfiable on `Handle` itself — the `HasField`-transparency gap
`access-and-presence-rows.md`'s audit found in the decomposition fix does not arise here.

**The real cost, stated plainly.** Reading (ii) requires row-*bounded* method dispatch on
`Drop`'s own critical path — ahead of RFC-0090 §3's recommended build order, which defers
`<row R>` open generics "only if a real duck-typing need materializes." `Drop`'s own
dispatch turns out to be exactly that need, immediately, not eventually. Narrow and
arguably unavoidable given reading (i)'s leak — but a real exception to name, not one to
let slide in silently.

---

## 5. The scope consequence: this reaches past the cluster under review

RFC-0071 §7 states its rule as a blanket ban: "A struct implementing `Drop` may not be
partially moved — the destructor requires access to the complete value." That rule is
written under the assumption that **no representation exists** for "which fields remain"
on a `Drop`-implementing type. Under this model, one always does. §7 is not narrowed by
an exception under this proposal (which is what RFC-0091 §1's `uses (…)` tried to do) —
it is **obsolete as stated** and needs rewriting at the source. That is a materially
bigger blast radius than "the four RFCs under review" — RFC-0071 has been `2-accepted`
since 2026-06-28.

---

## 6. Pressure test 1 — the sharpest problem found: widening reopens OQ10 as a general risk

RFC-0090's own worked example for constructor-invariant bypass:

```metel
struct SortedPair { small: i32, big: i32 }   // invariant: small <= big, enforced by SortedPair::new
```

Its **open question 10** asks whether `FromRecord` needs a guard against reconstructing a
`SortedPair` that violates this, since "auto-derived reconstruction can silently skip
validation a hand-written constructor enforces" — scoped, in the RFC's text, to that one
explicit conversion function.

If narrowing and widening are both fully automatic — a move narrows the type, a field
assignment widens it back, no conversion function involved anywhere — the same bypass is
reachable through nothing more than ordinary code:

```metel
fun mess_with_it(p: &mut SortedPair) {
    let old_small = p.small;   // move small out; p narrows to .{ big }
    p.small = 999_999;         // assign an arbitrary value back in; p widens to full SortedPair
    // no call to SortedPair::new, anywhere. invariant possibly broken.
}
```

**Precision about what's actually new here.** Plain mutable-field reassignment already
has this exact problem today, with zero row machinery involved — `p.small = 999_999`
bypasses `new` right now, in the current language, if the field is accessible. The model
does not create a hole from nothing. What it does is reveal that **OQ10 was mis-scoped
from the start** — RFC-0090 frames it as a risk specific to the `FromRecord` conversion
path, but it was always a general constructor-invariant problem, reachable via ordinary
field mutation. Taking narrow/widen fully seriously just makes that pre-existing
mis-scoping impossible to keep ignoring, since move-then-reassign is now *structurally
identical* to what `FromRecord` already does.

**The practical consequence:** whatever fixes OQ10 has to be a general answer about
mutable-field access on invariant-bearing types — banning automatic widening outright,
requiring it to re-run some validation, or something else not yet proposed here — not
something that can live inside one conversion function's design. This is left genuinely
open below; no answer was settled on while working through it.

---

## 7. Pressure test 2 — does universal `(brand, row)` reopen ambient structural matching?

RFC-0090 §8's whole argument for opt-in tiers: "Structural matching stays non-ambient —
the overwhelming majority of types never raise 'does this support drain/restore,
Lacks-typestate, or some absence-idiom' at all, because the answer is fixed once, by the
author, at the declaration or derive, never re-litigated per call site."

If **every** struct is always `(brand, row)`, and a row-conditional blanket impl exists
anywhere in the corpus (RFC-0061), every struct becomes structurally eligible to match it
— whether its author ever opted into structural exposure or not. That is the exact
TypeScript failure mode §8 exists to prevent, reintroduced at the level of coherence
rather than at the level of a type's own declared capability.

**Proposed reconciliation, not yet fully checked:** separate *"has a row, for narrowing
purposes"* (universal — needed for move-tracking to work uniformly across every struct)
from *"row is visible to `HasField`/row-conditional-impl matching"* (stays opt-in, gated
exactly the way tier 3 gates it today). The representation can be uniform without the row
being an ambient input to coherence.

**The caveat this puts on §3.1's win.** The *mechanism* becomes uniform — one query,
checked the same way everywhere — but *eligibility* to be checked still needs a
deliberate gate. The opt-in does not disappear under this model; it moves from "does this
struct have a row at all" to "is this struct's row visible to structural matching." That
is a real, if smaller, concession against the model's promise of one unified mechanism
with nothing bolted on.

---

## 8. Flagged, not worked through

**Enums stay out of scope**, consistent with §6/§9's existing scoping — this is a
structs-only move. Worth stating explicitly in whatever eventually gets written, rather
than left to be assumed.

**Generic structs are unresolved homework.** `Pair<T> { a: T, b: T }`'s row depends on
`T`. Metel's generics are monomorphization-based, and generic function bodies are already
deferred to call time (`FunBody::Generic`/`TypedExpr::GenericClosure`, constructed from
runtime values). Does row-narrowing and `HasField`-checking on a generic struct's fields
need the same deferral? Plausible, not examined here.

---

## 9. The zero-cost claim: a commitment to validate, not a settled property

The model's appeal rests partly on "the surface does not care that it's actually a row."
For that to be true at the implementation level, not just the surface-syntax level, an
unnarrowed value's type would need to stay representationally identical to today's plain
`Type::Named` — row machinery activating only at an actual narrowing operation (a move,
or a projection), never for code that does neither. That is a defensible design
*commitment*, not yet a demonstrated property. It needs checking once any of this becomes
concrete enough to build, not assumed from the surface argument alone.

---

## 10. Status summary

| | Resolved by this model | Newly opened by this model | Flagged, unexamined |
|---|---|---|---|
| `HasField` bolted-on-ness | ✅ §3.1 | — | eligibility-gating caveat, §7 |
| presence/access split | ✅ §3.2 — one operation, not two roles | — | — |
| `uses (…)`'s declaration | ✅ §3.3 | `Drop` dispatch must become row-bounded (§4) | pulls `<row R>` onto `Drop`'s critical path early |
| `HasField`-transparency gap (from `access-and-presence-rows.md`) | ✅ §4, via reading (ii) | — | — |
| RFC-0071 §7 | — | needs rewriting, not narrowing (§5) | — |
| RFC-0090 OQ10 | — | reopens as a general risk, not `FromRecord`-specific (§6) | fix split out to RFC-0114; its own fallibility question still open |
| RFC-0090 §8's non-ambient guarantee | — | at risk under universal rows (§7) | reconciliation proposed, not checked |
| enums | out of scope, unchanged | — | should be stated explicitly |
| generic structs | — | — | monomorphization-timing question, open |
| zero-cost-for-ordinary-structs | — | — | commitment stated, not validated |

---

## Open Questions

1. **How does OQ10's reopened, general form get fixed?** *Split out 2026-07-23 into its
   own RFC:* `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md`
   proposes a `Construct` aspect — `construct(row) -> Self` as the one path any value of a
   nominal type is produced through, whether fresh or reassembled after narrowing — with a
   separate, opt-in `ConstructUnchecked` escape hatch for code that already knows the
   invariant holds. That RFC does **not** close this question, though: it carries forward,
   as its own most consequential open item, whether an automatically-firing `construct()`
   can support a genuinely *rejecting* (not just self-healing) invariant without an
   ordinary-looking field assignment becoming able to fail or panic. Treat this item as
   "answered by delegation, not resolved" until RFC-0114's own fallibility question
   settles.
2. **Is "has a row" vs. "row is visible to structural matching" (§7) a clean, implementable
   separation, or does it just relocate the two-tier complexity this model was trying to
   get away from?**
3. **Does `Drop`'s row-bounded dispatch (§4, reading ii) actually require general `<row R>`
   machinery, or can it be special-cased narrowly enough to avoid pulling open generics
   onto the critical path for everything else** — including ordinary generic functions
   that have nothing to do with `Drop`?
4. **Does row-narrowing/`HasField`-checking on generic structs need to defer to
   monomorphization time**, the way generic function bodies already do? Unexamined (§8).
5. **Does the zero-cost-for-ordinary-structs property actually hold at the implementation
   level**, or only at the level of the surface-syntax argument (§9)? Unvalidated.
6. **What is this document's precise relationship to RFC-0090 §9?** §9 proposes
   representation-sharing for identity purposes only; this document's degrade-on-move
   extension is not present in §9 at all. Is this an amendment to §9, or a distinct,
   further claim that should be argued on its own terms rather than presented as "§9,
   promoted"?
7. **Process question, not a design one:** if this line of argument survives further
   pressure-testing, does it become an RFC-0090 rewrite, an RFC-0071 amendment, a new
   draft RFC of its own, or does it wait until §1's open question is resolved before any
   of that is decided? Not addressed here.

---

## References

- `internal/rfcs/0-draft/rfc-0114-constructor-aspect-and-canonical-construction.md` —
  the proposed (partial) answer to Open Question 1, split out 2026-07-23; leaves
  fallibility open as its own most consequential question
- `access-and-presence-rows.md` — the audit that found `HasField` bolted-on and worked
  through `uses (…)`'s reduction to existing mechanisms; this document responds to and
  extends that audit's findings, particularly §3 (views desugar to rows of borrows) and
  its finding that decomposition breaks `HasField` transparency
- `internal/rfcs/1-under-review/rfc-0090-structural-records.md` §1 (`HasField` as
  currently drafted), §3 (recommended build order, `<row R>` deferral), §8 (the
  non-ambient-structural-matching argument, the `SortedPair`/OQ10 example), §9 (the
  narrower, representation-sharing-only sketch this document extends)
- `internal/rfcs/1-under-review/rfc-0091-linear-records.md` §1/§1.1 — `uses (…)` and the
  `Handle`/`RcBox` motivating examples, resolved here without a declared field-usage
  mechanism
- `internal/rfcs/1-under-review/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  §4.10 — the "accuracy checking, not a declared-and-trusted annotation" discipline §4
  reuses for `Drop`'s row-bounded dispatch
- `internal/rfcs/2-accepted/rfc-0071-ownership-and-move-semantics.md` §7 — the blanket
  partial-move ban this proposal requires rewriting, not narrowing
