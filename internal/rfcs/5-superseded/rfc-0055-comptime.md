---
id: rfc-0055
title: "Comptime"
date: '2026-06-05'
updated: '2026-07-09'
status: superseded
superseded_by: rfc-0092, rfc-0093, rfc-0095
---

> **Superseded 2026-07-09**, discovered via `internal/rfcs/INDEX.md` — the first RFC
> that index surfaced as a silent duplicate. This RFC sat in draft since 2026-06-05;
> RFC-0092/0093/0094 were drafted independently starting 2026-07-09 without anyone
> checking whether comptime had prior art in this repository, because no index existed
> to check against. Building the index the same day surfaced the overlap immediately.
>
> This RFC's foundational execution model (`comptime let`, `comptime fun`'s
> restrictions, `comptime if`) was real, correct, and missing from RFC-0092 as
> originally drafted — folded into RFC-0092 §0 rather than silently dropped. Its Open
> Questions 1-2 (recursion/termination, comptime and allocation) and OQ-5 (error
> message quality) are folded into RFC-0092's Open Questions 6-8. Its OQ-4 (comptime
> aspect inspection, "could replace some uses of conditional `impl` blocks") is
> answered more precisely by RFC-0093's `@derive(Aspect)` registration than by this
> RFC's own `comptime has_aspect(T, Aspect)` sketch. Its motivating observation about
> conditional compilation folding into comptime `if` with no separate mechanism needed
> is independently corroborated by, not merged into, RFC-0095's Open Question 4 — the
> two were written from opposite directions and arrived at the same place.
>
> - **RFC-0092 (Comptime Core)** — the primary successor; `type`-as-value, `typeinfo`
>   reflection, `emit`, and (as of this reconciliation) this RFC's own execution-model
>   foundation.
> - **RFC-0093 (Derive Registration)** — answers this RFC's OQ-4.
> - **RFC-0095 (Attributes and Metadata)** — independently corroborates this RFC's
>   `@cfg`/comptime-`if` observation.
>
> Kept as historical record. Read it in full before touching the comptime cluster
> again — this reconciliation pass was not exhaustive, only targeted at the gaps
> found on one read-through.

## Summary

*(Superseded — see the three successor RFCs above. Original content preserved below
for historical reference.)*

Introduce a `comptime` evaluation phase that allows expressions, constants, and function calls to be evaluated at compile time. A `comptime` expression is guaranteed to produce its result before any generated code runs. Comptime values may be used wherever a compile-time constant is required — array sizes, type arguments, conditional compilation — and comptime functions may manipulate types as first-class values.

*(Full original Motivation, Proposal, Alternatives Considered, Open Questions, Timing
Recommendation, and References sections are preserved in this repository's git history
prior to 2026-07-09, and their substance is carried forward into RFC-0092/0093/0095 per
the supersession note above.)*

---

## Decision

**Outcome:** Superseded by RFC-0092, RFC-0093, RFC-0095.
**Target:** n/a — see successor RFCs.
