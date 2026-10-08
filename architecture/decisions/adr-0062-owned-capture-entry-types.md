---
id: adr-0062
title: "Owned Closure Captures Carry Entry Types"
date: '2026-10-08'
status: accepted
relates: RFC-0137
implements: metel-core#1409
---

## Context

Ownership analysis previously discovered captures by traversing a closure body.
An assignment target supplied no type, causing fallback to the outer binding's
original declaration. A later body read could instead supply a type widened by
restoration. Neither describes the value when it entered the environment. Body
traversal also omits explicit captures that are unused or shadowed.

## Decision

Construction records the resolved current type of each explicit owned capture
before entering or constructing the body. `Closure` and `GenericClosure` carry
these owned-source entry facts alongside their capture specs and lexical IDs.
The facts use the existing narrowed-read operation and otherwise the solved
environment type; construction performs no new inference or substitution.

Ownership analysis consumes these sources once at closure creation, using their
entry types. It excludes the same owned names from body-derived capture
consumption. Other capture modes retain their existing analysis. The snapshot
does not reset outer move state: a source already moved as a whole is still
unavailable, and consuming a non-`Copy` residual makes later outer uses illegal.

For a polymorphic closure, owned-source consumption precedes speculative body
reconstruction. An inability to analyze that body must not erase the known
ownership transfer at environment creation. Runtime evaluation and elaboration
do not alter or interpret these ownership-only facts.

## Alternatives Considered

**Use the first typed body read.** Rejected because restoration can precede it,
and the body may not read the capture at all.

**Reconstruct entry rows inside ownership analysis.** Rejected because the
construction pass already has the resolved current type, including nominal
brands and row facts. Repeating narrowing there would introduce a second
type-resolution path.

## Consequences

Fixtures cover empty and partial nominal restoration, callback aliases,
anonymous-row captures, explicit captures shadowed or unused by generic bodies,
and rejection of incomplete restoration, missing fields, capture after a whole
move, and outer source reuse. #1406 supplies the inference-side preservation of
narrowed captures; this change is its separate ownership-analysis follow-up.
