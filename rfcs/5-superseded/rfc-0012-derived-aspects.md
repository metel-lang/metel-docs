---
id: rfc-0012
title: "Attributes, Metadata, Macros, and Derived Aspects"
date: '2026-05-21'
updated: '2026-07-09'
status: superseded
superseded_by: rfc-0092, rfc-0093, rfc-0094, rfc-0095
---

> **Superseded 2026-07-09** by four smaller, independently reviewable RFCs, split out
> after this RFC grew to cover generics-as-comptime-sugar, reflection, derive
> registration, general metaprogramming, and attributes/metadata all in one document —
> too much for one review, and with a real dependency-ordering problem this split
> resolves: comptime derive (this RFC) needed structural records' row concept, while
> structural records' `ToRecord`/`FromRecord` derive convenience needed comptime derive
> — circular only if the row concept and the derive-sugar convenience are conflated.
> Splitting them dissolved the cycle into a DAG. This document is kept as historical
> record; all decisions, worked examples, and open questions have been carried forward
> into the four successors below, plus RFC-0089/0090/0091 (also split out the same day,
> from the parallel `linear-types.md`/`structural-records.md` circular dependency).
>
> - **RFC-0092 (Comptime Core)** — `type`-as-value, `typeinfo` reflection,
>   single-declaration `emit`. This RFC's §1-3.
> - **RFC-0093 (Derive Registration)** — `@derive(Aspect)` as request and registration,
>   the Derivable Aspects table (with `Linear` corrected out of it — see RFC-0089 §2),
>   Path A/B/C alternatives. This RFC's §9, Derivable Aspects, and the derive-specific
>   Alternatives Considered entries.
> - **RFC-0094 (Comptime Metaprogramming)** — generalized multi-declaration/expression-
>   position `emit`, comptime-callable parsing, span-tracked diagnostics, body
>   reflection scoping. This RFC's §4-7, the Macros motivation subsection, and the
>   Lisp-style-macros alternative.
> - **RFC-0095 (Attributes and Metadata)** — the `@` attribute system, attributes as
>   comptime-visible metadata. This RFC's Motivation "Attributes and metadata"
>   subsection, §8, and "Preferred Syntax."
>
> RFC-0080 (Standard Library Aspects) now depends on RFC-0093 for `Clone`'s derive
> mechanism, not this RFC directly.

## Summary

*(Superseded — see the four successor RFCs above for current content. The original
summary, motivation, and full text of this RFC as of 2026-07-09 are preserved in this
repository's git history and in the successor RFCs' own revision-history blockquotes,
which trace the design decisions made under this RFC number before the split.)*

---

## Decision

**Outcome:** Superseded by RFC-0092, RFC-0093, RFC-0094, RFC-0095.
**Target:** n/a — see successor RFCs.
