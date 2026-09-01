---
id: rfc-0157
title: "Closure Capture Default (Move)"
date: '2026-08-31'
status: accepted
target: v0.13.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/918'
---


> **Status — accepted 2026-09-01**, as part of the v0.13.0 closure cluster (RFC-0050 /
> RFC-0134 / RFC-0152 / RFC-0153 / RFC-0157). Implementation shape: **ADR-0052**.

> **Scope.** This RFC carries one decision — **D5, the closure-capture default is
> `move`** — and its rationale. It began as a broader "Copy and Clone Model Re-analysis";
> the regular-value `Copy`/`Clone` model critique, the P0–P3 design space, and the
> prior-art survey are now **RFC-0162** (`1-under-review`, v0.17.0), so this document is
> D5-only.

## Summary

Everywhere in Metel a non-`Copy` value used by value is *moved* (`let y := x`, `f(x)` —
no keyword, RFC-0071). RFC-0006 made closure capture the one exception: a closure that
captures a free variable by value *deep-clones* it. RFC-0006 chose that before RFC-0071's
affine model existed, and nothing re-tested it. The consequence surfaced in RFC-0050: a
non-`Copy`, non-`Clone` value could not enter a closure at all, and RFC-0050 needed a
`move`-shaped escape hatch that only wanted a keyword because the default was surprising.

**Decision (2026-09-01, language owner): the closure-capture default is `move`.** By-value
capture obeys the same rule as by-value use in a block. This removes the exception, drops
RFC-0050's need for any ownership-transfer specifier, and removes RFC-0006's per-call
environment re-clone. It lands with the v0.13.0 closure cluster as one hard change (no
`--edition` gate — Metel has no public users).

## The closure-capture default (D5) — ✓ DECIDED: move

RFC-0006's default can be restated as: **by-value capture uses
the same rule as by-value use in a block.** Under RFC-0071 that means a non-`Copy` free
variable is *moved* into the closure (consumed in the enclosing scope), a `Copy` one is
copied, and a `Clone`-not-`Copy` one is an error unless explicitly `.clone()`d at the
capture site — exactly `let y := x` semantics. Cross-closure sharing and
mutate-the-outer-binding stay on explicit references (RFC-0050's `&`/`&var`), which is
already the design. This:

- makes ownership-transfer capture need no keyword (settling RFC-0050's deferred question
  as "no specifier — bare capture of a non-`Copy` value is the move");
- changes an observable default (a closure that captured `s: String` under RFC-0006 left
  `s` usable; now it consumes `s`) — a breaking change, but Metel has no public users, so
  it is applied wholesale with the interpreter's own fixture corpus updated in the same
  change, not behind an `--edition` gate;
- **removes RFC-0006's per-call `call_env = captured.clone()` re-clone** — the value is
  moved in once, so there is nothing to re-clone per call; a `reading` closure reads the
  moved-in aggregate in place, a `mutating` one mutates it in place (RFC-0153 §1a). This
  also settles RFC-0050 RQ5's "large read-only value deep-cloned per call for no reason."
- **resolves Open Question 4 the strict way:** an explicit capture list is required the
  moment a move would happen — no *implicit* move of a non-`Copy` capture — following the
  "explicit at the definition site" principle RFC-0050 and the *Implicit mutable capture*
  rejection both lean on. An unannotated closure only ever captures `Copy` values (by
  copy) or nothing.

## Direction

**D5 is the divergence worth making.** Rust's regular-value `Copy`/`Clone`/move model is
stable and the strongest transferable intuition a newcomer brings — so **RFC-0162
recommends not diverging there**. Rust's *closure* story is visibly unfinished, and its
capture default (clone) is the one part Metel's own affine model already contradicts. D5
fixes that, and the capability cluster (RFC-0134 `call_multiplicity`, RFC-0152 widening,
RFC-0153 mutation axis, RFC-0050 capture lists) is where Metel iterates past
`Fn`/`FnMut`/`FnOnce`.

Follow-up: RFC-0006 (`4-implemented`) is amended to match through the normal path — its
body + `spec/functions.md` sync ride the cluster's implementation PR; RFC-0006 is now
`spec_status: pending`, `amended_by: rfc-0157, rfc-0050, rfc-0153`. The regular-value
follow-ups (RFC-0158 `Clone`/`Share`, the D3 relaxation, an RFC-0135 disposition) are
**RFC-0162**'s.

## Relationship to existing RFCs

- **RFC-0162 (Copy and Clone Model — Regular-Value Design Space, `1-under-review`)** — the
  extracted sibling. Carries D1–D4, the P0–P3 design space, the prior-art survey, and the
  "keep Rust's regular-value model" recommendation with its open questions. No v0.13.0
  consumer.
- **RFC-0050 (Closure Capture Lists, `2-accepted`, #803)** — carries the surface rule:
  capture list required for a non-`Copy`/by-ref capture, bare `[s]` = move for non-`Copy`,
  `[s.clone()]` for an explicit copy. D5 settled RFC-0050's deferred ownership-transfer
  question as "no keyword."
- **RFC-0134 (Closure Call Capability, `2-accepted`, #269)** — the matching amendment:
  `many` by default, `once` written explicitly, §2 a check against that default.
- **RFC-0153 (Closure Mutation Axis, `2-accepted`, #902)** — §1a's move-once environment
  with write-back is the runtime side of "the per-call re-clone is removed".
- **RFC-0006 (Closure Capture Semantics, `4-implemented`)** — the default this RFC
  changes; amended (see above).
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — the affine foundation D5
  makes closure capture conform to.

## Open Questions

None. A capture list is required the moment a move would occur — no *implicit* move of a
non-`Copy` capture (the stricter rule, for predictability and consistency with RFC-0050's
exhaustiveness). The corpus-sweep sizing is a delivery task on RFC-0050 #803 / ADR-0052,
not an open design question. The regular-value `Copy`/`Clone` questions (D1 severity, D3
soundness, RFC-0135 disposition) are **RFC-0162**'s.

---

## Decision

**DECIDED 2026-09-01 (language owner): the closure-capture default is `move`.** A by-value
capture of a non-`Copy` free variable moves it into the closure (consuming the outer
binding); a `Copy` one is copied; a `Clone`-not-`Copy` one is an error unless `.clone()`d
at the capture site — `let y := x` semantics. A capture list is required the moment a move
would occur (Open Question 4). RFC-0006's per-call environment re-clone is removed with
it: the environment is moved in once and read/mutated in place (RFC-0153 §1a). Mechanism
and rollout: **RFC-0050** (#803) and the **RFC-0134** amendment (#269), landing v0.13.0 as
one hard change; RFC-0006 amended to match.

Accepted as part of the v0.13.0 closure cluster (with RFC-0050 / RFC-0134 / RFC-0152 /
RFC-0153). The regular-value `Copy`/`Clone` questions are **not** decided here and are not
on the v0.13.0 path — they are RFC-0162's, with stated reopening conditions.

**Target:** v0.13.0 (via RFC-0050 #803 / RFC-0134 #269 / RFC-0153 #902).

