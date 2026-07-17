---
id: rfc-0103
title: "Bodyless Aspect Declarations"
date: '2026-07-14'
status: implemented
target:
updated: '2026-07-14'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/commit/a9b49a570e034be5954b70580b162e10e2b52cb6'
impl_status: implemented
---

> **Status — accepted (2026-07-14).** Scope narrowed on split: this RFC now covers bodyless aspect declarations only. The struct/enum-embedded aspect-list proposal that previously lived here has been extracted into deferred RFC-0105. No open questions block the remaining bodyless-declaration feature.

> **Status — integrated (2026-07-14).** Integrated into spec: bodyless aspect declarations (`aspect Name;`)

> **Status — implemented (2026-07-14).**

## Summary

One addition on top of RFC-0102, extending its own bodyless theme one production earlier.
**Bodyless aspect declarations** (`aspect Copy2;`) are pure sugar for `aspect Copy2 { }`, legal
whenever the braced form already would be: the aspect declares zero methods and zero associated
types. This mirrors RFC-0102's bodyless `extend`-block sugar at the aspect's own declaration site,
with no new semantic category and no permanence guarantee beyond "currently empty."

---

## Motivation

RFC-0102 makes `extend Type: Aspect;` legal whenever an empty `extend`-block body already would be.
The aspect declaration itself has the same "nothing to write" shape one production earlier: an aspect
with no methods and no associated types at all (the `Send`/`Sync`-style case) still has to write
`aspect Copy2 { }` today. Those braces are pure noise, exactly the pattern `fun_decl`'s own
`(block | ";")` alternative and RFC-0102's `extend_block` sugar already exist to remove.

This project's docs corpus already uses the term "marker aspect" for exactly this case — RFC-0080 §3
calls `Send`/`Sync` "marker aspect[s] with no methods" — so this RFC gives that existing,
already-named shape a shorter spelling, not a new concept.

## 1. Grammar

```
aspect_decl = { pub_kw? ~ "aspect" ~ ident ~ generic_params?
                 ~ (("{" ~ (assoc_type_decl | aspect_method)* ~ "}") | ";") }
```

```metel
aspect Copy2;
```

Pure sugar, exactly like RFC-0102 §2: `aspect Copy2;` desugars to `aspect Copy2 { }` before anything else
runs. There is no separate "is this a marker aspect" check and no permanence guarantee attached to this
spelling — an aspect declared bodyless today can gain a method tomorrow by simply switching to the braced
form, exactly as freely as an aspect that happened to start out `aspect Foo { }`. The bodyless spelling is
legal if and only if the aspect declares zero methods and zero associated types, the same "currently empty"
condition RFC-0102 already uses for `extend` blocks, applied here to the aspect's own declaration instead.

## 2. Semantics: sugar, not a new rule

`aspect Copy2;` desugars to `aspect Copy2 { }` before any validation runs. There is no
separate "is this a marker aspect" check, no permanence guarantee attached to the
bodyless spelling, and no new semantic category. Whatever already validates an aspect
declaration today continues to validate the desugared form unchanged.

The legality rule is intentionally simple: the bodyless spelling is valid if and only if
the braced declaration would be empty already. An aspect with any method or any
associated type still uses braces.

```metel
aspect Copy2;

aspect Serializable {
    fun serialize(&self) -> String;
}
```

Changing a previously bodyless aspect later is still ordinary source evolution:

```metel
// Earlier revision
aspect Copy2;

// Later revision
aspect Copy2 {
    fun clone(&self) -> Self;
}
```

Nothing about the `;` spelling promises that the aspect can never grow. It only says
that, at this revision, there is nothing to write in the body.

---

## Alternatives Considered

- **Status quo — always require braces.** Simplest, zero grammar change, but leaves
  exactly the syntactic noise this RFC exists to remove for a currently-empty aspect.
- **A dedicated `marker` keyword giving a permanent zero-methods guarantee.** Rejected:
  the useful part is the shorter spelling for an empty declaration, not a stronger
  promise about future evolution. Once an aspect can grow by switching to the braced
  form, a dedicated keyword adds surface area without paying for itself.
- **Tie bodyless aspect declarations to auto-impl or marker semantics.** Rejected:
  whether an aspect is auto-implemented, marker-like, or ordinary remains a separate
  semantic question. This RFC only shortens a syntactic shape that is already empty.

---

## Unresolved Questions

None remaining. The bodyless-declaration feature is pure syntactic sugar over an already
legal empty aspect declaration, with no unresolved semantic questions left once the
stronger `marker` keyword idea was dropped.

---

## References

- RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls) — the direct
  precedent. This RFC mirrors RFC-0102's bodyless `extend`-block sugar one production
  earlier, at the aspect declaration.
- RFC-0080 (Standard Library Aspects — Clone, Deref, Send, Sync) — uses the already
  established "marker aspect" idea (`Send`/`Sync` as zero-method aspects). This RFC does
  not change those semantics; it only gives the empty declaration a shorter spelling.
- RFC-0105 (Struct-Embedded Aspect Lists, draft) — extracted from an earlier, broader
  version of RFC-0103 when that larger syntax was deferred.

---

## Decision

**Outcome:** Accepted
**Target:** *(set when scheduled for implementation)*
