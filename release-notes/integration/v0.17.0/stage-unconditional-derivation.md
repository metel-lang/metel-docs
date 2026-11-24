# Stage gate — v0.17.0, Unconditional derivation

**Run:** 2026-11-24 · against `develop` at `ed8acab0`.
**Result:** PASS.
**Stages in scope:** Unconditional derivation (the first v0.17.0 stage to be gated).

## Exit test

- RFC-0244 (#2150) accepted and integrated: `4-implemented` (metel-docs#740, #741, #742, #743; metel-core#2171,
  #2174). The spec carries it in `reference/spec/declarations/aspects/declaration-clauses.md`, with no
  `Pending` marker left.
- RFC-0227, RFC-0239, RFC-0234, RFC-0207 and RFC-0224 amended: met by decision, not by edits. #2152 was closed
  as not planned on 2026-11-23: an implemented RFC is design history, the spec is normative
  (`rfcs/PROCESS.md`), and RFC-0244 records what it changes in each.
- The acceptance order with RFC-0238 decided: #2151, closed 2026-11-23. RFC-0244 went first, and the rule for a
  derivation's `Flow` parameters moved to RFC-0238 section 2.
- RFC-0244's open questions decided, recorded in its Open questions section on 2026-11-23: `derives A()` stays
  legal and equals `derives A`; no one-word spelling for the public conditional case; `(..)` applies to std's
  `Clone` and `Copy` before RFC-0238; no `linear?`.
- Implemented (#2153, closed 2026-11-23):
  - a bare `derives A` is unconditional and an error when a field lacks `A` for some instantiation:
    `rfc0244_a_bare_derives_states_no_condition_t0046`, `rfc0244_a_bare_copy_keyword_states_no_condition_t0046`;
  - `(..)` computes the flow: `rfc0244_bare_is_unconditional_and_query_computes` and the three joint fixtures
    below;
  - the `copy` keyword has no conditional form, and `copy(T)` and `copy()` are gone:
    `rfc0244_the_copy_keyword_has_no_conditional_form_p0001`, `rfc0244_the_copy_keyword_takes_no_argument_list_p0001`,
    `rfc0244_a_query_mark_after_a_derives_entry_is_a_parse_error_p0001`;
  - std, fixtures and spec migrated: std has no `copy?`, `copy(` or `derives A?`, and the spec examples pass the
    doc-example checker.

The stage's scope changed while it was open (2026-11-23 and 24): the computed form is spelled `(..)`, not a
postfix `?`, and `copy?` was removed (#2179). RFC-0238 (#2158) and RFC-0246 (#2172) moved to Metaprogramming and
derive, because a deriver is comptime code (metel-core#2184). Both changes are recorded in the milestone
description.

## Features exercised

- Unconditional derivation and the computed flow (RFC-0244, #2153), registered as `rfc-0244` with
  `stage = "Unconditional derivation"`. It is the first v0.17.0 feature in the registry.

## Matrix

`python3 tools/feature_matrix.py v0.17.0 --stage "Unconditional derivation" --blockers`:

```
Release gate scope: 101 new-vs-registry pairs · Tier A/B pairs: 26 · Tier A open (blocking): 0 · Tier A partial (reported): 20 · Tier A bulk-deferred: 0
Registry: 102 features · 0 without spec rule IDs · 0 unresolved introduction releases
Gate: PASS (0 violation(s))
```

The first run was BLOCKED with 8 violations, closed in metel-core#2186:

- Seven open Tier A pairs, RFC-0244 against RFC-0020, 0035, 0037, 0097, 0129, 0130 and 0177. Three joint run
  fixtures close them, each citing only rules it exercises:
  - `rfc0244_derived_impls_meet_extends_bounds`: derived impls meet `extends` bounds in parameter and return position
    (RFC-0035, RFC-0130, RFC-0037);
  - `rfc0244_derived_impls_meet_blanket_impls_and_method_bounds`: a local blanket impl over `Copy` and a
    method-level `Copy` bound accept derived types (RFC-0097, RFC-0129, RFC-0020);
  - `rfc0244_computed_flow_through_option_and_tuple_fields`: the computed flow looks through `Option<T>` and tuple
    fields, with `None` typed from the struct (RFC-0020, RFC-0177).
- The v0.16.0 bulk deferral (#2086, 82 old Tier A cells) had expired at v0.17.0, which failed every v0.17.0 stage
  gate although #2086 is milestoned v0.17.1. A `[[bulk]]` entry may now name `until`; this one lasts until v0.17.1
  (decided by the language owner, 2026-11-24). No `n/a` or individually deferred cells.

## Findings

- **#2185** — calling a bare-parameter blanket impl's method through a generic bound is an internal error (I0001)
  at run time, for every type. Pre-existing and independent of derivation; found while writing the RFC-0097 joint
  fixture, which avoids the call. Deferred to v0.17.1.

## Verification

On `ed8acab0`:

- `cargo test --release` (metel-interpreter): 2286 passed, 0 failed.
- `cargo clippy --release --lib -- -W clippy::pedantic`: no warnings.
- `cargo build --release -p metel`: built.
- `move-check-count`: `skipped_generic_bodies_user_total=8` (baseline 18). `user_move_violations=181`, up 1 from
  180 at v0.16.0. The fixtures added since v0.16.0 report no move error under `--move-check` (each fails only with
  the parse or type error it expects), so the extra one comes from a changed existing fixture; as in earlier
  sessions it was not traced further.
- Doc examples (README, tutorials, spec): 202 passed, 0 failed, 101 skipped (89 unverifiable fragments, 12
  annotated skips).
