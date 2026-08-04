---
id: rfc-0105
title: "Struct-Embedded Aspect Lists"
date: '2026-07-14'
status: draft
target:
updated: '2026-07-14'
---

> **Status — draft (2026-07-14).** Split out of RFC-0103 when the smaller bodyless-aspect-declaration feature was accepted independently and the `struct Type: Aspect { ... }` / `enum Type: Aspect { ... }` syntax was deferred for separate evaluation.

## Summary

This RFC proposes a **struct/enum-declaration-embedded aspect list**:

```metel
struct Token: Copy2, Serializable, !Send {
    value: String,
}
```

and the symmetric enum form. The list reuses RFC-0102's `extend_aspect_list`, but in a
type declaration rather than an `extend` block. A negative item (`!Aspect`) is fully
satisfied by the list itself; a positive item (`Aspect`) declares a checked,
module-wide obligation that some ordinary `extend Type: Aspect { ... }` block exists
elsewhere. The declaration's own body remains fields-only or variants-only: this syntax
does not put method bodies inside a `struct` or `enum`.

This proposal is deferred because it is a materially larger surface-language commitment
than bodyless `extend` blocks or bodyless aspect declarations. It couples declaration
syntax to whole-graph obligation checking, coherence, and auto-impl interactions, and
those trade-offs should be judged on their own rather than bundled into RFC-0103.

## Motivation

A struct or enum declaration has exactly one body, and it is already reserved for fields
or variants, not per-aspect method implementations. Yet some aspect facts read as part
of what a type *is*, rather than something that feels naturally written elsewhere:

```metel
struct Token: Copy2, Serializable, !Send {
    value: String,
}
```

That shape avoids a separate bodyless `extend` block for declarations that are
effectively metadata about the type. It also aligns with a familiar class-declaration
pattern from other languages, adapted into Metel's own `extend`/aspect vocabulary rather
than imported wholesale.

At the same time, positive aspects in that position are not obviously an "implementation"
at all, because there is nowhere in the type body to place the required methods. That
tension is the core design question this RFC isolates.

## Proposed design

### 1. Grammar

```text
struct_decl = { pub_kw? ~ "struct" ~ ident ~ generic_params? ~ (":" ~ extend_aspect_list)?
                 ~ where_clause? ~ "{" ~ struct_fields ~ "}" }
enum_decl   = { pub_kw? ~ "enum" ~ ident ~ generic_params? ~ (":" ~ extend_aspect_list)?
                 ~ where_clause? ~ "{" ~ enum_variants ~ "}" }
```

`extend_aspect_list` is reused directly from RFC-0102 §5 (`bound ~ ("," ~ bound)*`).

### 2. Semantics

`struct Token: A, !B { value: String }` means:

```metel
struct Token { value: String }
extend Token: A;
extend Token: !B;
```

with one important refinement:

- `!Aspect` is fully satisfied by the embedded list itself, exactly like a bodyless
  negative `extend`.
- `Aspect` does **not** implement the aspect there. It declares an obligation that some
  ordinary `extend Token: Aspect { ... }` block exists and satisfies the aspect's own
  completeness rules.

### 3. Obligation model

The declaration remains fields-only or variants-only. Positive items are promises, not
inline implementations. A missing satisfying `extend` block becomes a compile error
reported at the type declaration:

```metel
struct BadToken: Serializable {   // error: no `extend BadToken: Serializable { ... }` found
    value: String,
}
```

The check is inherently whole-graph: the satisfying block may be in another loaded
module. The original RFC-0103 draft placed this check alongside RFC-0060's coherence
pass, reusing the same collected impl graph rather than inventing a second cross-module
scan.

### 4. Auto-impl interaction

If `Send`, `Sync`, or `Linear` are auto-impl aspects under RFC-0096, then
`struct Handle: Send { ... }` should not spuriously fail just because no handwritten
`extend Handle: Send { ... }` exists. Under the original RFC-0103 draft, that meant
RFC-0096's implementation needed to inject auto-impl results into the same
aspect-implementation registry ordinary `extend` blocks populate, so the obligation
check still had a single lookup path.

This remains a key unresolved integration question and one reason this syntax is split
out instead of staying bundled with the simpler bodyless-declaration feature.

## Why deferred

- It changes type-declaration syntax, not just `extend` or `aspect` sugar.
- It introduces a new kind of whole-graph obligation tied to the declaration surface.
- It has nontrivial interaction with coherence and auto-impl aspects.
- It is easy to understand the syntax superficially while still underestimating the
  enforcement and error-model consequences.

Those are all reasons to evaluate it separately rather than smuggle it through under the
same acceptance as bodyless aspect declarations.

## Alternatives Considered

- **Keep it bundled with RFC-0103.** Rejected on split: the bodyless-declaration feature
  stands on its own, while this syntax still needs separate evaluation.
- **Reject positive items entirely; allow only negatives in the embedded list.**
  Smaller, but loses the main ergonomic reason the syntax exists.
- **Treat positive items as fully satisfied when the aspect is currently empty or all
  defaulted.** Rejected in the original RFC-0103 draft because that couples correctness
  to the aspect's current shape and leaves no local place to repair the declaration if
  the aspect later gains a required method.
- **Use an attribute or annotation syntax instead of `struct Type: Aspect`.** Possible,
  but larger than reusing the existing aspect-list grammar.

## Unresolved Questions

- Should Metel allow `struct Type: Aspect { ... }` / `enum Type: Aspect { ... }` at all?
- If yes, should positive items always be obligations, or should some narrower class of
  aspects be satisfiable directly from the list?
- Is the coherence pass the right home for the obligation check?
- Is the auto-impl registry-injection requirement on RFC-0096 the right design, or a
  sign that this syntax is reaching too far into implementation structure?

## References

- RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls) — supplies
  `extend_aspect_list` and the bodyless negative-impl precedent.
- RFC-0103 (Bodyless Aspect Declarations) — this RFC was split out of an earlier,
  broader version of RFC-0103.
- RFC-0060 (Aspect Impl Coherence) — likely host for the obligation check.
- RFC-0081 (Negative Impls) — negative-polarity semantics reused directly.
- RFC-0096 (Auto-Impl Aspects, draft) — interaction point for auto-impl obligations.
- RFC-0104 (Multi-Aspect Extend Blocks with Shared Bodies, draft) — a satisfying
  positive obligation could be discharged by a multi-aspect `extend` block if that RFC
  lands.

## Decision

**Outcome:** Deferred  
**Target:** *(none yet)*
