---
id: linear-types
title: "Linear Types"
type: report
status: active
last_synced_against_model: '2026-07-06'
supersedes: "reports/memory-model/linear-types-and-structural-records-2026-07-06.md sections 3-4"
---

# Linear Types

*Living document — reflects the current state of understanding, not a point-in-time
snapshot. Updated in place; see the changelog note at the point of each substantive
change rather than a new dated file.*

*Exploration, not a decision. Nothing here is ratified. The one binding constraint is
external to this document: RFC-0063 §9 item 5 requires partial consumption to be
resolved before RFC-0071/RFC-0067 implementation begins (Phase 3 steps 1–2 in
`reports/implementation/rfc-implementation-breakdown-2026-07-01.md`).*

*Promoted to RFC status 2026-07-09: §1-2, §4-5, and the Option A/B floor from §3 are now
`internal/rfcs/0-draft/rfc-0089-linear-types.md`. §3's Option C (record-based automatic
downgrade) and the aliasing-question update are now
`internal/rfcs/0-draft/rfc-0091-linear-records.md`, which depends on RFC-0089 and
RFC-0090 (Structural Records). This document remains the living exploration those RFCs
were extracted from; it is not superseded, but new substantive changes to the topics
above should land in the RFCs directly, not here, once they move past draft.*

**Prior art this document builds on, not around.** `archive/per-field-multiplicities.md`
(restored 2026-07-06 from git history after being deleted on 2026-06-28) worked out the
correct theoretical foundation for this whole thread — a per-field multiplicity lattice,
grounded in quantitative type theory — three weeks before this session independently
re-derived a flatter, less general version of the same idea. `archive/substructural-and-
separation-types.md` (same recovery) is where the linear-capability-token pattern (§6
there) and the affine/linear distinction were first worked out for Metel. Both are
folded in below rather than left as a parallel, uncited thread.

---

## 1. The multiplicity lattice, adapted for Metel's affine-by-default reality

`per-field-multiplicities.md` proposes a three-point lattice — 0 (erased) / 1 (linear) /
ω (unrestricted) — standard in quantitative type theory (Atkey 2018, Idris 2, Linear
Haskell). That lattice assumes an ω-default background: ordinary bindings are already
freely copyable, and restriction is something you add. **Metel inverts this.** RFC-0071
(accepted) makes affine — move-by-default, at-most-once, no implicit copy — the
*default* for every struct and enum field; ω-like unrestricted behavior is something you
opt into via `Copy`. A three-point lattice doesn't have a point for Metel's actual
default. The lattice needs four:

```
0      — erased: a compile-time-only marker (a brand, a phantom state tag);
         not present as a runtime value at all
1      — linear: exactly once; no weakening (can't silently drop), no contraction
         (can't duplicate); must be explicitly consumed
affine — at most once: weakening allowed (may drop; Drop::drop runs), no
         contraction (can't duplicate); THE DEFAULT for ordinary fields (RFC-0071)
ω      — unrestricted: weakening and contraction both allowed; Copy fields
```

Ordered by how much the discipline permits: `1` is strictly more restrictive than
`affine` (affine additionally allows silent dropping); `affine` is strictly more
restrictive than `ω` (ω additionally allows duplication). `0` sits outside this ordering
— it's not "fewer uses," it's "not a runtime value," and behaves the way `PhantomBrand`
(RFC-0074) and phantom type-state parameters already do.

**A struct's overall discipline is the join (least upper bound, toward more permissive)
of its fields' multiplicities** — restated from the per-field-multiplicities model. A
struct with any `1` field is linear overall; a struct with only `affine`/`ω` fields (no
`1`) is affine overall; a struct with only `ω` fields may (if it opts in) be `Copy`.
`Drop` is compatible with `affine` and `1` but not `ω` (RFC-0071 §4's existing
`Copy`/`Drop` exclusion is a special case of this general rule, not a separate one).

---

## 2. `Linear` as an aspect — the auto-impl mechanism, reframed as a lattice consequence

`aspect Linear { }` — a marker aspect, structurally identical in form to `Send`
(RFC-0080). Auto-derived, not opt-in: a struct containing a multiplicity-`1` field is
`Linear` (RFC-0080 §3.2's auto-impl rule, substituting `Linear` for `Send`), matching
`per-field-multiplicities.md`'s join rule directly rather than being a bespoke case.
`impl !Linear for X {}` (RFC-0081) is the escape hatch for a type that would otherwise
structurally qualify but shouldn't.

**Mutually exclusive with `Copy`** (obviously — `ω` and `1` can't coexist in the same
field) **and with `Drop`.** `Drop`'s triggers — implicit scope-end, the generic `drop(x)`
free function — have no legitimate firing point for a value that can never legally reach
scope-end unconsumed, and `drop`'s signature should exclude `Linear` via `T: !Linear`
(mirroring RFC-0072's negative-bound mechanism), specifically to avoid the exact hazard
RFC-0049 already documents: a generic `drop` that discharges a linearity obligation
without running real cleanup ("`drop(f)` appears to work but leaves captured values
dangling"). A linear type's teardown logic lives in an ordinary, author-named consuming
method instead, called directly.

### 2.1 Surface syntax: aspect, keyword, or a mix

Every other mechanism in this thread — `drop<T: !Linear>`, `HasField`/`Lacks` conditions
(`structural-records.md`), residual recomposition (§3 below) — needs `Linear` to be
usable in a bound position. A bare keyword with no backing aspect can't supply that; it
either collapses into being sugar for an aspect, or it's a strictly weaker mechanism that
can't participate in the rest of this design. That leaves aspect vs. aspect-plus-sugar,
and aspect-plus-sugar wins on one real capability: declaring a type linear *by fiat*
when nothing about its fields structurally requires it (a capability token wrapping a
plain `i64`, say):

```metel
impl Linear for Receipt {}          // explicit, forces it
linear struct Receipt { id: i64 }   // proposed sugar for exactly the line above
```

The keyword should stay struct-only, never extended to `record` (`structural-records.md`
§5.6) — records have no declaration site to attach it to, and forcing a structurally-
plain row to be linear "by fiat" undermines the premise that a record is *just* its row.

**`Affine` needs no aspect of its own.** It's definitionally "not `Copy` and not
`Linear`" — `T: !Copy + !Linear` (RFC-0072's already-accepted mixed positive/negative
bound form) already says it. RFC-0039 (`aspect` Alias Syntax, draft) is the vehicle to
name it without writing the compound bound at every call site:

```metel
aspect Affine = !Copy + !Linear
```

And, symmetrically to `linear struct`, a struct-only `affine struct` keyword would
desugar to a *locking pair of negative impls* — `impl !Copy for X {} impl !Linear for
X {}` — not a positive capability grant, since affine is an absence, not an addition.
That pair is more than documentation: RFC-0081's negative impls override any later
conflicting impl via ordinary coherence, so `affine struct Handle { fd: i64 }` is a real,
checked commitment that nothing elsewhere in the codebase can later add `impl Copy for
Handle` and silently change what moving a `Handle` means.

None of this — `Linear` as aspect, the keyword sugar, the `Affine` alias — is ratified.

---

## 3. Partial consumption: three options, not one

`per-field-multiplicities.md` §3 already enumerated the design space precisely. Restated
against the four-point lattice: when a struct with mixed multiplicities has its `1`
fields consumed, what happens to the rest?

**Option A — drop everything.** The struct is consumed atomically; `affine`/`ω` fields
are discarded alongside the `1` ones. Simplest, but the caller can never recover an
otherwise-unrestricted field after the terminal action.

**Option B — explicit residual extraction.** The consuming function returns the
non-linear fields as ordinary values; the compiler injects nothing automatically.

```metel
fun close(f: File) -> i64 {
    sys_close(f.fd);
    f.fd   // fd survives; _cap's obligation is satisfied by having been reached at all
}
```

**Option C — automatic downgrade.** The binding's type changes at the point of
consumption, without explicit destructuring — this session's original proposal (residual
= `record { <remaining fields> }`, `structural-records.md` §5.3), and it composes
cleanly with the lattice-join rule from §1: the residual's own discipline is just the
join of *its* remaining fields, recomputed, so "the remainder is still linear and must
still be consumed" falls out automatically rather than needing a bespoke rule.

**`per-field-multiplicities.md` recommends Option B as the practical starting point** —
unambiguous, no per-binding state tracking beyond ordinary move semantics — while
flagging Option C as "the most expressive option but the most complex to implement,"
specifically because of an aliasing question neither this document nor the original
resolves: *if `p = &f` was taken before the downgrade, what type does `p` have
afterward?* This session's earlier framing leaned toward Option C without engaging that
question; it should have. **Revised recommendation:** treat Option B as the floor —
sufficient to meet RFC-0063 §9 item 5's deadline, no new type-formation machinery,
no unresolved aliasing question — and Option C as the fuller vision from
`structural-records.md` §5.4's build order, pursued separately and only once the
aliasing question above has an answer.

**Update (2026-07-08): a candidate answer to the aliasing question now exists**, arrived
at independently while designing `structural-records.md` §10's tier-2 `to_record_mut`/
`from_record_mut` conversions. The answer: `p`'s type becomes the shrunk row (`&mut
record { <remaining fields> }`), sound for an unremarkable reason — `&mut` already
guarantees no other live reference exists to observe the stale, pre-downgrade type, so no
new aliasing machinery (a brand, a fork/join token) is needed beyond ordinary `&mut`
exclusivity and structural row equality. This is promising, not proven: no formal
soundness argument has been written down, only a worked mechanism plus several worked
examples (`structural-records.md`'s `RcBox`, `FileHandle`, and `MaybeUninit`-style
construction cases) that exercise it without incident. Option C should still be treated as
unratified until this gets a real argument, not just examples that haven't broken it —
see item 5 below, updated accordingly.

---

## 4. `NonLinear<T>`: a standalone, nameable projection

Distinct from the residual produced by an actual consumption event (§3), a standalone
type-level operator — `NonLinear<T>`, computed by filtering `T`'s own closed, known
field list to exclude anything at multiplicity `1` — is reusable in a signature without
requiring the caller to have consumed anything locally first:

```metel
struct Session { token: LinearToken, name: String, retries: i64 }

fun archive(entry: NonLinear<Session>) { ... }   // = record { name: String, retries: i64 }
```

The natural companion to `HasField` (`structural-records.md` §5.1) in the same family:
`HasField` is a predicate ("does this row have field X"), `NonLinear<T>` is a function on
rows ("this row, minus whichever fields are multiplicity-`1`"). It needs only a closed,
already-known field list — no row-kind, no unification algorithm — so it's available
independent of whether the open `<row R>` generics step is ever taken.

---

## 5. Two-struct vs. mixed-multiplicity: the same thing, different explicitness

`per-field-multiplicities.md` §4 resolves a question this session's report never posed:
is the "address + capability" pattern —

```metel
struct FileHandle { fd: i64 }          // multiplicity ω (or affine) — freely copyable
linear struct FileCap { fd: i64 }      // multiplicity 1 — must be consumed
```

— a different design from a single mixed-multiplicity struct, or the same design at
different explicitness? **The same design.** Under Option B (§3), consuming a mixed
struct and extracting its non-linear fields produces exactly what the two-struct version
would have given you by holding `FileHandle` independently while consuming `FileCap`.
They differ only in whether the split is manifest in the type definitions or deferred to
the point of consumption:

| | Two-struct | Mixed-multiplicity struct |
|---|---|---|
| Freely alias the handle | Yes — its own type | Yes — via `&Struct` borrows |
| Recover the handle after consuming the cap | Yes — lives on independently | Yes — via residual extraction |
| Typestate | Separate type param per struct | One type param, one struct |
| Syntax weight | Two definitions, two threaded values | One definition, one value |

Two-struct is preferable when the address and the capability genuinely have independent
lifetimes and travel to different parts of a program separately. Mixed-multiplicity is
preferable when they always travel together until the terminal action. Both should
remain available — this is a style choice given the same underlying model, not a
decision between two different models.

---

## 6. Open questions

1. Ship the four-point lattice (§1) as the documented model, or keep presenting `Linear`
   as a flat per-struct property with the lattice as internal justification only —
   affects how this gets written up if formalized, not the mechanics. Leaning toward
   presenting the lattice explicitly, since it's what actually explains the composition
   and reversion rules rather than asserting them.
2. `Linear` as an auto-impl marker aspect, `Linear ⊥ Copy`/`Drop`, `drop<T: !Linear>` —
   leading candidates, not ratified.
3. Struct-only `linear`/`affine` keyword sugar (§2.1) — leaning yes, not ratified.
4. Partial consumption: Option A/B/C (§3) — **revised leaning: B as the floor, C as the
   separately-pursued fuller vision**, reversing this session's earlier lean toward C
   alone. Not ratified.
5. The aliasing question for Option C — what type does a borrow taken before a
   downgrade have afterward — **has a candidate answer as of 2026-07-08** (§3's update:
   the shrunk row type, justified by ordinary `&mut` exclusivity, from
   `structural-records.md` §10's `to_record_mut`/`from_record_mut`). Not yet a proven
   soundness argument — still blocks treating Option C as ratified, but no longer blocks
   it for lack of *any* proposed answer.
6. `NonLinear<T>`'s exact surface syntax (is it a type-level function, a special form,
   something else) — unresolved; only the shape of what it computes is settled.
7. Multiplicity polymorphism (`Guarded<T, Cap>` generic over a field's multiplicity,
   `per-field-multiplicities.md` §5) — noted as a real, later extension; not attempted
   here.
8. Does residual/record typing (Option C), if adopted, replace RFC-0071 §7's affine
   partial-move side-table too, or stay linear/record-scoped only — unresolved.

---

## Relationship to the tracked deadline

Unchanged: RFC-0063 §9 item 5 requires this to be settled before RFC-0071/RFC-0067
implementation begins. Item 4 above (Option B as the floor) is what actually satisfies
that deadline; Option C remains open-ended and explicitly not required to close it.
