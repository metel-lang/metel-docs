---
id: adr-0070
title: "Constructor-Call Construction Is Reverted; Nominal Braces Are Restored"
date: '2026-11-20'
status: accepted
relates: adr-0066, adr-0067
implements: metel-core#1945
---

## Context

RFC-0100 made a nominal type constructible by calling it: `Point(1, 2)` and `Point(.x = 1, .y = 2)` built a `Point`, with
the brace form `Point { x: 1, y: 2 }` retired. It was implemented in the v0.16.0 cycle (metel-core#1860, #1861, #1862,
#1886): the checker treated a call whose callee named a type as a construction, a construction-call module typed it, and
the corpus, standard library and documentation were migrated.

Review then showed the construction was chosen by the arguments. A call `T(args)` meant an ordinary function call or a
construction depending on what `T` named and what was passed, so a function and a type of the same spelling collided, and
the meaning of a call could change when an unrelated declaration was added. A distinct construction proposal (RFC-0226,
metel-core#1944, since consolidated into RFC-0100) replaced the idea of reusing call syntax. The language owner asked for
RFC-0100 to be reopened and for its implementation to be reverted (metel-core#1945).

## Decision

### 1. Construction is by nominal braces again

`Name { field: value, .. }` constructs a struct, including field shorthand, and an enum struct variant is built the same
way. A call whose callee names a type is no longer a construction; it is an ordinary call. The construction-call module and the checker's synthetic spread-temporary bindings (a `BindingId`
minted for a construction call's own temporary) are removed, so the span to `BindingId` bridge again reads only the
identity pass's table.

### 2. Keyword arguments stay

Keyword arguments on ordinary calls, methods, associated functions and aspects (RFC-0223) were built beside construction
calls and do not depend on them. They are kept, with their overload narrowing.

### 3. The rollback does not undo independent work

Dotted row labels (RFC-0221), the Copy and Clone work, and the other v0.16.0 features stay. Only the construction-call
corpus, stdlib and documentation changes were reversed, and no shared history was rewritten: the revert is a new commit.

### 4. RFC-0100 is open again

RFC-0100 returns to `1-under-review` with metel-core#807 as its design tracker. Its explicit (`new T(...)`) and inferred
(`.(...)`) construction proposal is the candidate replacement and is not implemented. The normative construction rules,
the changelog and the stage tracking describe the restored braces.

## Consequences

- A program written against the construction-call spelling during the cycle must return to braces. The cycle never
  shipped it in a release, so no released program does.
- A reader of the checker no longer meets a call that is sometimes a construction. The cost is that a type with a
  required-field constructor spells every field at the use site until RFC-0100 or its successor lands.
- This is a design rollback and not a defect fix against an unchanged specification. A later construction design has to
  answer the argument-dependent collision that ended this one.
