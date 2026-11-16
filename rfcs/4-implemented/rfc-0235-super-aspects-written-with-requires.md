---
id: rfc-0235
title: "Super-Aspects Written with requires"
date: '2026-11-16'
status: implemented
updated: '2026-11-16'
tracking: 2065
coverage:
  "1": { spec: "spec.declarations.aspects.super-aspects.legality-1" }
  "2": { kind: untestable, reason: "The clause order only matters once an aspect may have an instance list (RFC-0236); no rule exists to cite yet." }
  "3": { spec: "spec.declarations.aspects.super-aspects.legality-6" }
  "4": { spec: "spec.declarations.aspects.super-aspects.legality-4" }
  "5": { kind: untestable, reason: "The migration section lists corpus edits and states no rule." }
impl_tracking: 2068
impl_status: implemented
---

> **Status — under review (2026-11-16).**

> **Status — accepted (2026-11-16).** No open questions; design settled with the language owner 2026-11-16.

> **Status — integrated (2026-11-16).**

> **Status — implemented (2026-11-16).**

## Summary

An aspect's super-aspects are introduced by a dedicated keyword, `requires`, instead of the colon list, and the mark that says a
super-aspect must be *derived* is spelled `derived`:

```metel
aspect Ord requires Eq { fun cmp(&self, other: &Self) -> Ordering; }          // was `aspect Ord: Eq`
aspect Copy requires derived Clone, !Drop { }                                  // was `aspect Copy: deriving Clone, !Drop`
aspect Eq requires derived PartialEq { }                                       // was `aspect Eq: deriving PartialEq`
aspect Cold requires !Hot;                                                     // was `aspect Cold: !Hot;`
```

Only the spelling changes. The entries (positive, negative `!`, the derived-obligation mark of RFC-0213 section 4 and RFC-0234),
their meaning and every rule about them stay as RFC-0168, RFC-0213 and RFC-0234 state them. What changes is that **the colon after
a declared name means one thing everywhere**: `struct P: A` and `extend P: A` say that `P` is an instance of `A`, and after this
RFC `aspect Foo: B` is free to say the same of an aspect, which RFC-0236 uses.

This is a design draft under review. It is a prerequisite of RFC-0236 and is independent of every other RFC; it is scheduled
with RFC-0234 and RFC-0227 so the aspect-declaration syntax and the derivation clause are migrated in one pass.

---

## Motivation

1. **The colon has two readings in one position.** `aspect Error: Display` says every `Error` is `Display` (a requirement on the
   types that satisfy it). If an aspect may also be an instance of a meta-aspect (RFC-0236: `aspect Serialize: Derivable`), the
   same syntax would say either that or "`Serialize` itself is a `Derivable`", and the reader would have to know the kind of the
   named aspect to tell them apart. A kind-directed reading of one syntax is a trap.
2. **The relation deserves its own word.** A super-aspect entry is not membership; it is a requirement on the types that satisfy
   the aspect, positive (`requires Eq`) or negative (`requires !Drop`). `requires` states both. A colon borrows the meaning of
   `struct P: A`, a fact about a single type.
3. **The mark's old word describes a design that is gone.** `deriving` meant that deriving the sub-aspect also generated the
   super-aspect. Under RFC-0234 nothing is generated: deriving `Copy` requires that `Clone` also be derived. `derived` says that.
4. **The cost is small and the language has no users.** About 20 aspect declarations in the fixtures and std, two spec mentions
   and the examples in RFC-0168, RFC-0207, RFC-0212, RFC-0213 and RFC-0234 change.

---

## Proposal

### 1. The grammar

```
aspect_decl     = { pub_kw? ~ aspect_property* ~ "aspect" ~ ident ~ generic_params? ~ requires_clause? ~ (";" | "{" ~ .. ~ "}") }
requires_clause = { "requires" ~ super_aspect ~ ("," ~ super_aspect)* }
super_aspect    = { bang? ~ derived_mark? ~ type_path }
derived_mark    = { "derived" }                                   // was deriving_mark
```

`requires` and `derived` are reserved words. A search of the fixtures, std and the grammar finds neither used as an identifier.
Entries have the checks they have today (RFC-0168, RFC-0213 sections 2 to 4, RFC-0234).

### 2. Position among the clauses

The colon list comes first, then the clauses, as `struct Receipt: Validated derives Copy` does (RFC-0207): an aspect with both
writes the instance list, then `requires`, then the body.

```metel
aspect Serialize: Derivable requires Display { .. }        // RFC-0236: instance list, then requires
```

### 3. The old spellings

`aspect Foo: B` is a parse error whose message names the new spelling ("write `aspect Foo requires B`"), and `deriving` as a mark is
a parse error ("write `derived`"). The colon after an aspect's name has no meaning until RFC-0236 gives it one, so it is rejected
and not silently accepted.

### 4. Negative entries

`aspect Copy requires !Drop` states an exclusion: no type may satisfy both (RFC-0213 section 3). It is a requirement on the
satisfying type, as a positive entry is, so it sits in the same clause.

### 5. Migration

Rewrite each `aspect A: ...` header and each `deriving` mark. The language has no users, and no program depends on the old
spelling beyond the corpus.

---

## Interaction with other work

- **RFC-0168** (draft) and **RFC-0213** (implemented): introduced and specified the entries; the colon and `deriving` in their
  examples become `requires` and `derived`. Nothing else in either changes.
- **RFC-0234** (under review): the mark is the obligation to derive, now written `derived`.
- **RFC-0236** (draft): needs the colon free so that an aspect can list instances of meta-aspects.
- **RFC-0207** (implemented): the colon list of a type and the `extend` form are untouched.
- **RFC-0238** (draft): `derivable` stops being a property (RFC-0238); `derived` is an entry mark and is unrelated to it.

---

## Alternatives considered

1. **Keep the colon.** The reading conflict above; RFC-0236 would need a kind-directed rule.
2. **`refines`.** RFC-0168's word for the relation, and it reads well for a positive entry (`Ord refines Eq`). A negative entry
   (`Copy refines !Drop`) is an exclusion, not a refinement, so the word stretches, and `refines derived Clone` reads poorly.
3. **`extends`.** One letter from the `extend` block keyword; rejected on confusability.
4. **`where Self: A`.** An expressible encoding (Rust's `trait A where Self: B`), but longer, and it hides the relation among the
   other bounds.
5. **`implies`.** States the direction wrongly: an aspect `Ord` implies `Eq`, but the entry belongs to `Ord` as a requirement.
6. **Keep `deriving` as the mark.** Describes generation, which RFC-0234 removed; `requires deriving Clone` reads as a requirement
   to be deriving something.

---

## Open questions

None known.

---

## Decision

**Outcome:** *(pending)*
