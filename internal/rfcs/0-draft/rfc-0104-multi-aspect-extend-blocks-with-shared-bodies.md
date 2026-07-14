---
id: rfc-0104
title: "Multi-Aspect Extend Blocks with Shared Bodies"
date: '2026-07-14'
status: draft
target:
---

## Summary

Lifts RFC-0102 §5's bodyless-only restriction for `extend` blocks specifically: `extend A: Aspect3, Aspect4
{ ... }` with a real, shared, non-empty body. Disambiguation reuses an existing tolerance (extra methods
beyond an aspect's requirements already become ordinary inherent methods today) by checking each named
aspect's own required-method coverage independently, by name, against the shared pool. The one new rule:
if two named aspects in the same list declare a method with the identical name, the whole combination is
rejected outright rather than guessing or introducing a qualified-declaration syntax. Depends on RFC-0102;
split out of an earlier draft of RFC-0103, which covers a separate, narrower feature (bodyless aspect
declarations and struct/enum-embedded lists) that doesn't need this RFC to work.

---

## Motivation

RFC-0102 §5 gives `extend Type: A, B, !C;` — a comma-separated, per-item-polarity aspect list — but
restricts it to bodyless (or explicitly-empty-braced) blocks, flagging a genuinely shared, non-empty body
across multiple aspects as a harder problem and explicitly deferring it. This RFC takes that on.

The obvious-looking obstacle is disambiguation: given `extend A: Aspect3, Aspect4 { fun foo() {...} fun
bar() {...} }`, which named aspect does each method belong to? The answer turns out not to need new syntax
at all, because of something already true of *single*-aspect impls today: `infer_decl`'s existing
completeness check (`inference.rs`) only verifies that an aspect's *required* methods are covered by name
in the body — it never checks the reverse, that every method in the body belongs to the aspect. An impl
can already contain "extra" methods beyond what its aspect requires, and they simply become ordinary
callable methods on the type. Generalizing to multiple named aspects inherits that same tolerance directly,
with one new rule needed for the case that tolerance alone can't resolve: two named aspects sharing a
method name.

---

## 1. The mechanism: a shared method pool, checked per aspect

```metel
extend A: Aspect3, Aspect4 {
    fun foo(&self) { ... }
    fun bar(&self) { ... }
}
```

- The body is one shared pool of methods.
- Each named aspect's own required-method coverage is checked independently against that pool, by name —
  exactly like today's single-aspect check, just run once per named aspect instead of once total.
- A method name matching none of the named aspects becomes an ordinary inherent method, exactly like
  today's already-tolerated "extra method in a single-aspect impl" case.

No new AST shape is needed for this: `ib.methods`/`ib.aspect_name` already generalize to `ib.methods`
against a *list* of aspect names (RFC-0102 §5 already does this generalization for the bodyless case); this
RFC only lifts the restriction that kept the body itself empty.

## 2. The one new rule: reject a method-name collision between named aspects outright

If two or more aspects in the *same* list declare a method with the identical name, the combination is
rejected — at the list level, independent of what the body actually contains. `extend A: Aspect3, Aspect4 {
... }` is a compile error if `Aspect3` and `Aspect4` both declare (say) `fun display(&self) -> String;`,
even before looking at whether the body provides one.

No qualified-declaration syntax (e.g. `fun Aspect3::foo(&self) { ... }`) is introduced to resolve such a
collision — the combination is simply disallowed, and the fix is to stop sharing the body: write `extend A:
Aspect3 { ... }` and `extend A: Aspect4 { ... }` separately, exactly as today, unaffected by this RFC. This
keeps the feature safe by construction: every method name in a body that's accepted at all maps to at most
one named aspect, with no silent "whichever aspect matched first" behavior anywhere.

```metel
aspect Aspect3 { fun foo(&self); }
aspect Aspect4 { fun bar(&self); }

struct A { }

extend A: Aspect3, Aspect4 {
    fun foo(&self) { println("foo"); }   // Aspect3::foo
    fun bar(&self) { println("bar"); }   // Aspect4::bar
    fun helper(&self) { }                 // matches neither -- ordinary inherent method
}

// Rejected -- Aspect3 and Aspect5 both declare `foo`, so this combination
// can never be disambiguated by name, regardless of the body's contents.
aspect Aspect5 { fun foo(&self) -> i64; }
extend A: Aspect3, Aspect5 {   // error: `foo` is declared by both Aspect3 and Aspect5
    fun foo(&self) { ... }
}
```

**Where the collision check runs.** "Two named aspects declare the same method name" is knowable purely
from the aspects' own declarations, independent of the body — this should run as soon as the aspect list
itself is resolved, before the body is type-checked at all, so the error is reported without needing to
look at (or even successfully parse past) the body's contents. Confirming this ordering is achievable
against the actual construction pipeline is implementation work, not assumed here (see Unresolved
Questions).

## 3. Interaction with RFC-0105

RFC-0105 (Struct-Embedded Aspect Lists, draft) covers a positive aspect named on a struct/enum's own
declaration as a checked *obligation*, discharged by an ordinary `extend` block written elsewhere. That
block may itself be a multi-aspect one under this RFC's own rules, with no special interaction beyond
what's already stated in either RFC — the two features compose without needing to know about each other.

---

## Alternatives Considered

- **A qualified method-declaration syntax** (e.g. `fun Aspect3::foo(&self) { ... }`) to disambiguate a
  shared body when two named aspects' method names collide. Rejected in favor of simply disallowing the
  colliding combination — smaller, and the same information a qualifier would carry (which aspect owns
  which method) is exactly what's already unambiguous by name whenever no collision exists.
- **Silently pick one aspect when names collide** (e.g. first-listed wins). Rejected outright — this is
  exactly the "whichever aspect matched first" behavior the chosen design deliberately avoids; a silent,
  order-dependent resolution is a worse outcome than a compile error asking for separate blocks.
- **Status quo — keep RFC-0102 §5's bodyless-only restriction, never allow a shared non-empty body.**
  Simplest, but leaves the exact repetition (writing N separate `extend` blocks for N aspects that
  genuinely share an implementation shape) this RFC exists to remove.

---

## Unresolved Questions

1. **Confirm the collision-check ordering (§2) against the actual construction pipeline** — that it can run
   from the aspect list alone, before the body is type-checked, so a colliding combination is rejected with
   a clean error rather than one entangled with unrelated body-content errors. Not assumed correct here,
   needs verification at implementation time.
2. **Interaction with RFC-0082 associated types**: if two named aspects both declare an associated type
   with the same name (not a method), does the same collision rule apply? This RFC's own examples are
   method-only; associated-type collisions in a multi-aspect list aren't addressed here and should be
   checked against RFC-0082's own completeness machinery before implementation.

---

## References

- RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls) — this RFC depends on it
  directly: the comma-separated, per-item-polarity aspect list (§5) is the same production, just with its
  bodyless-only restriction lifted for a real, shared body.
- RFC-0103 (Bodyless Aspect Declarations) — sibling RFC covering the smaller accepted bodyless-declaration
  feature.
- RFC-0105 (Struct-Embedded Aspect Lists, draft) — sibling RFC covering the deferred struct/enum-embedded
  obligation syntax this RFC can compose with.
- RFC-0098 (Surface Keyword Renames) — `extend Type: Aspect` grammar this RFC's multi-aspect body extends;
  not amended.
- RFC-0060 (Aspect Impl Coherence) — the existing per-aspect completeness check (`infer_decl`) this RFC's
  §1 generalizes from one aspect to several; not amended, only invoked more than once per impl block.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
