---
id: rfc-0167
title: "Reclassify unsoundness-only runtime errors as internal errors; split R0002"
date: '2026-09-04'
status: under-review
target: v0.14.0
updated: '2026-09-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/991'
---

> **Status — under review (2026-09-04).** Milestoned v0.14.0 -- real engagement per PROCESS.md's milestoning trigger

## Summary

Six documented runtime-error codes — **R0003** (undefined variable), **R0006**
(non-exhaustive match), **R0008** (field not found), **R0009** (method not found),
**R0010** (call on non-callable value), **R0011** (invalid for-in iterator) — should
never fire for a well-typed Metel program if the type checker is sound. Each one's
existence is a claim the checker is *supposed* to have already verified statically;
if the runtime check fails anyway, the type checker is wrong, not the program. That
is a different kind of event than the genuinely value-dependent runtime errors
(array-out-of-bounds, arithmetic overflow, `.yolo()`, explicit `panic`) sitting
alongside them in the same `R00NN` series, and it deserves a different code family:
**internal errors (`I00NN`)**, whose existing framing ("if you see this, the
interpreter has a bug — please report it") is the *correct* framing for these six,
and the misleading one for a user reading `error-codes.md` today.

Separately, **R0001** ("no `main` function defined") and R0002's main-entry-point
uses ("`main` is not a function" / "`main` is generic" / "`main`'s body could not be
typed") are purely static, declarative facts — answerable from the declaration table
alone, with no dependency on program execution — currently checked lazily at
evaluator startup instead of during typechecking. These become a real compile-time
Legality Rule instead.

R0002 turns out to be a third, orthogonal problem on top of this: it is used for
three semantically unrelated failures under one code (the main-entry-point cases
above; an ordinary function call on a non-callable value, which is R0010's job
description; and a generic-closure construction-machinery failure with no relation
to `main` at all). This RFC splits it along with reclassifying it.

---

## Motivation

`reference/error-codes.md`'s `R00NN` series documents "Dynamic Semantics" —
`STYLEGUIDE.md`'s own dividing line for that category is "a runtime-behavior claim,"
distinct from a Legality Rule's "static, compile-time claim." Nothing in that
category description asks whether the runtime behavior in question is something a
*user's own program logic* can legitimately trigger, versus something that can only
happen if the compiler itself violated a guarantee it makes elsewhere. The R-series
today conflates both.

Compare two documented R-codes side by side:

- **R0007** (arithmetic error) fires because a *value only known at runtime* —
  a computed divisor, a computed operand — happened to be zero, or overflowed. No
  amount of static analysis resolves this ahead of time; it is inherent to the
  operation. A user's own logic legitimately triggers it, and the fix is to guard
  the operation in their own code.
- **R0006** (non-exhaustive match at runtime) fires because *the type checker
  approved a `match` as exhaustive and it wasn't*. Nothing about a `match`
  expression's exhaustiveness depends on a runtime value — it is a purely static
  property of the pattern set against the scrutinee type, fully decidable before
  the program ever runs. If this code ever fires, the type checker's own
  `check_match_exhaustiveness` approved something false. `error-codes.md`'s own
  entry for R0006 already says as much: "a known limitation."

The same argument applies to R0003 (does this name resolve — a scoping fact),
R0008/R0009 (does this type have this field/method — a structural fact, checked at
the point of `extend`/struct declaration), R0010 (is this value callable — a type
fact, and in v0.13.0 there is not even a dynamic-dispatch mechanism, `dyn Callable`,
that could make it otherwise; see RFC-0161), and R0011 (does this type implement
`Iterable` — a bound fact, checked wherever the iteration is typed).

**This is not a hypothetical concern.** metel-core#986's audit (2026-09-04) went
looking for a real, legitimate way a well-typed program could trigger any of these
six and did not find one, across two investigation rounds. What it *did* find,
twice, is direct evidence for this RFC's premise instead:

- **#712** (closed, v0.12.1-adjacent): a nested `fun`'s forward reference typechecked
  cleanly and failed at runtime with what the interpreter reported as R0002
  ("call: target is Unit, not a function") — a genuine typechecker/evaluator
  hoisting disagreement. A compiler bug, not a case of user code legitimately
  hitting a dynamic edge.
- **#989** (open, filed alongside this RFC): two aspects sharing a short name in
  different modules corrupt each other's dispatch resolution —
  `TypeRegistry::aspect_decl_modules` and the elaborator's `build_aspect_id_map`
  are both keyed by bare aspect name, not a qualified path. In the variant
  constructed, this surfaced as a false *static* rejection of a valid program
  rather than a runtime R0009 — but it is the same shape of bug again: an
  implementation defect in the exact machinery R0009's raise site exists to guard,
  not a legitimate dynamic uncertainty.

Both of the *only two* confirmed real-world instances anyone has produced of this
error class firing (or nearly firing) were compiler bugs. `error-codes.md` documents
these six as if a user could reasonably expect to hit one and needs advice for their
own code — R0008's current `Fix:` line reads "check the field name against the type
definition." If the code is even reachable, that advice is aimed at the wrong
person; the actual fix is a compiler patch, and the actual next action for whoever
hits it is to file a bug, exactly as I0001/I0002 already say today for their own
entries.

**R0001/R0002's main-entry cases are a different, more mundane problem: nobody
moved an easy check earlier.** `env.get("main")` in `evaluator/mod.rs` is a
declaration-table lookup with zero runtime dependency — it does not even require
type inference, only that declarations have been collected. There is no
soundness claim being violated by deferring it (the type checker never claimed
to check this), just an unforced, static fact sitting behind the "runtime error"
label for no structural reason.

---

## Proposal

### 1. Six codes move from `R00NN` to `I00NN`

| Current | Message today | New |
|---|---|---|
| R0003 | undefined variable at runtime | I-series (scoping/hoisting invariant) |
| R0006 | non-exhaustive match at runtime | I-series (exhaustiveness-checker invariant) |
| R0008 | field not found | I-series (field-resolution invariant) |
| R0009 | method not found | I-series (method-dispatch invariant) |
| R0010 | call on non-callable value | I-series (callability invariant) — *merges with R0002's non-`main` call-target case, see §3* |
| R0011 | invalid for-in iterator | I-series (iterator-dispatch invariant) |

Each keeps its own distinct code under the `I` prefix rather than collapsing into
`I0001`'s generic bucket — a maintainer triaging a bug report benefits from "I0004:
match exhaustiveness violated" the same way today's R-series benefits from
distinguishing R0008 from R0009 rather than having one catch-all "something went
wrong." Exact new numbers are an integration-time decision (§ Migration) — this RFC
fixes the scheme, not the digits.

Each entry's `Fix:` guidance changes from user-facing code advice to the existing
I0001/I0002 framing: this indicates an interpreter bug; please file one, with the
program that triggered it.

`R0005` (tuple index out of bounds) is **not** included here — it was investigated
and confirmed unreachable independently (metel-core#987/#990), but its own
"Fix:"/reasoning was already accurate (the entry already reads as a defensive,
compile-time-fixed-index case, not user-facing advice pointing at the wrong thing)
and its exemption already reflects that. No reclassification needed there; it stays
documented as it is.

### 2. R0001 and R0002's main-entry cases become a Legality Rule

A new static check, run during typechecking (or module/program assembly, whichever
this project's pipeline treats as the right stage for a whole-program declaration
fact — an implementation decision, not a design one): the program's root module
must declare exactly one function named `main`, callable with zero arguments, with a
body the type checker can type. Violating this becomes a `T00NN` Legality Rule
diagnostic, replacing:

- R0001 "no main() function defined"
- R0002 "main() is generic — not supported"
- R0002 "`main` is not a function"
- R0002 "main() body could not be typed" (both raise sites)

`R0001` and `R0002`'s main-entry meaning are retired, not reused for anything else
(§ Migration).

### 3. R0002's other two uses go to their real destinations

R0002 has two more raise sites (`evaluator/call.rs`) with no relationship to `main`
at all, found while investigating metel-core#986/#987:

- `call.rs:150`, `"call: target is Unit, not a function"` — an *ordinary* function
  call (not `main`) on a non-callable value. This is R0010's own documented job
  description. Recode to whatever R0010 becomes under §1 (an `I00NN` code) —
  it is the exact same claim ("this value is callable") as R0010's existing raise
  site, just triggered from a different call path; there is no reason for two
  codes to mean the same thing.
- `call.rs:104` and `call.rs:272`, `"generic closure/method has no type context —
  construction-at-call-time unavailable"` — a construction-machinery plumbing
  failure (the generic-body-at-call-time mechanism, metel-core#286, needed a
  `type_ctx` that was not supplied). Unrelated to call-target shape or `main`
  entirely; this is its own internal-invariant case, a new `I00NN` code.

After §2 and §3, **R0002 has no remaining raise sites** and is fully retired.

### 4. A durable rule for future codes

Going forward, a new diagnostic code should be classified by asking: does firing
depend on a value only known at runtime (→ `R00NN`, Dynamic Semantics)? Is it a
static property currently checked too late, with no soundness claim at stake (→
`T00NN`, a Legality Rule, checked earlier)? Or does firing mean an already-made
static guarantee was violated (→ `I00NN`, an internal error)? Worth adding to
`reference/spec/STYLEGUIDE.md`'s error-codes section once this RFC integrates —
tracked as follow-up, not part of this RFC's own scope.

---

## Migration

- **Renumbering is real churn, scoped and bounded.** Six codes retire from
  `R00NN` and gain new `I00NN` numbers; `R0001`/`R0002` retire outright, replaced
  by one new `T00NN`. Every fixture currently citing one of R0001/R0002/R0003/
  R0006/R0008/R0009/R0010/R0011 via `[expect].code` or the sidecar's `error =
  [...]` key (metel-core#977/#988's citation mechanism) needs its expectation and
  citation updated to match. `rfc.py check`'s per-fixture citation-consistency
  check (metel-core#988) catches anything missed mechanically.
- **Retired codes are never reused.** Matching this project's existing convention
  for spec rigor-block ids ("`n` is never reused, even after the block it named is
  deleted," `STYLEGUIDE.md`) — R0001 and R0002 stay retired, documented in
  `error-codes.md` with a note pointing at their replacements, not silently
  deleted from the page and not reassigned to a future unrelated diagnostic.
- **New number assignment happens at integration time**, checked against both
  `error-codes.md`'s current corpus and the actual `RuntimeErrorCode`/new
  `InternalErrorCode`/`TypeErrorCode` Rust enums directly — not guessed here and
  risked colliding with something assigned in the meantime.
- **#989 is not a prerequisite.** Fixing the aspect-dispatch collision bug is
  independent implementation work; this RFC's reclassification is correct whether
  R0009 (however renumbered) ever actually fires or not — the point is what firing
  *means*, not whether it currently can.

---

## Forward compatibility

None of this changes user-facing language semantics — no new syntax, no changed
type-checking behavior, no changed runtime behavior for any program that compiles
today. It only changes which numbered bucket a handful of already-existing
diagnostics live in, and where the `main`-entry check runs. A program that
typechecks cleanly today continues to typecheck and run identically; a program that
was rejected today (missing `main`) is still rejected, just earlier and under a
different code.

---

## Relationship to existing RFCs

- **RFC-0004** (`main() return type`, `0-draft`) asks whether `main` should be
  allowed to return `Result<(), E>`. Orthogonal to this RFC — that is a question
  about `main`'s *signature*; this RFC is about when and how `main`'s *existence
  and basic shape* gets checked. Neither blocks the other.
- **RFC-0014** (`Panic Recovery`, `0-draft`) asks whether panics should become
  recoverable. Orthogonal — this RFC does not touch panic semantics (R0007,
  R0013-R0016 are untouched; they remain genuinely dynamic, catchable-or-not per
  whatever RFC-0014 eventually decides, same as today).
- **RFC-0161** (`dyn Callable`, deferred in full) is the mechanism that would, if
  and when it lands, give R0010's successor code a genuine reason to depend on a
  runtime value again (a dynamically-dispatched call target whose callability
  isn't statically decidable). If RFC-0161 ships, this RFC's classification of
  that code should be revisited — noted here so that revisit isn't missed.

---

## Open Questions

- Exact new code numbers (§ Migration) — resolved at integration time.
- Whether the whole-program `main`-declaration check (§2) belongs in the ordinary
  per-module typecheck pass or a separate "program assembly" stage that runs after
  the module graph is fully typed — an implementation detail with no observable
  difference to a program author, left to whoever implements this.
- Whether `I00NN` diagnostics should carry a distinct exit-code/reporting
  convention from `R00NN` ones (e.g. always print a "please file a bug" pointer to
  the issue tracker) — a good idea, but a UX decision separable from the
  classification question this RFC is actually about.

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.14.0
