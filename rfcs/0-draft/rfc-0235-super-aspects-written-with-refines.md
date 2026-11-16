---
id: rfc-0235
title: "Super-Aspects Written with refines"
date: '2026-11-16'
status: draft
---

## Summary

An aspect's super-aspects are introduced by a dedicated keyword, `refines`, instead of the colon list:

```metel
aspect Ord refines Eq { fun cmp(&self, other: &Self) -> Ordering; }          // was `aspect Ord: Eq`
aspect Copy refines deriving Clone, !Drop { }                                // was `aspect Copy: deriving Clone, !Drop`
aspect Loud refines Greeter { fun shout(&self) -> String; }
```

Only the introducer changes. The entries (positive, negative `!`, the `deriving` mark of RFC-0213 and RFC-0234), their meaning and
every rule about them stay as RFC-0168 and RFC-0213 state them. What changes is that **the colon after a declared name means one
thing everywhere**: `struct P: A` and `extend P: A` say that `P` is an instance of `A`, and after this RFC `aspect Foo: B` is
free to say the same of an aspect, which RFC-0236 uses.

This is a design draft. Nothing here is accepted. It is a prerequisite of RFC-0236 and of nothing else.

---

## Motivation

1. **The colon has two readings in one position.** `aspect Error: Display` says every `Error` is `Display` (a refinement over
   types). If an aspect may also be an instance of a meta-aspect (RFC-0236: `aspect Serialize: Derivable`), the same syntax would say
   either that or "`Serialize` itself is a `Derivable`", and the reader would have to know the kind of the named aspect to tell
   them apart. A kind-directed reading of one syntax is a trap.
2. **The relation deserves its own word.** A super-aspect entry is not membership; it is a requirement on the types that satisfy
   the aspect. RFC-0168 calls it a refinement. A keyword states it, where a colon borrows the meaning of `struct P: A`, a fact
   about a single type.
3. **The cost is small and the language has no users.** About 20 aspect declarations in the fixtures and std, two spec mentions
   and the examples in RFC-0168, RFC-0207, RFC-0212 and RFC-0213 change.

---

## Proposal

### 1. The grammar

```
aspect_decl    = { pub_kw? ~ aspect_property* ~ "aspect" ~ ident ~ generic_params? ~ refines_clause? ~ (";" | "{" ~ .. ~ "}") }
refines_clause = { "refines" ~ super_aspect ~ ("," ~ super_aspect)* }
super_aspect   = { bang? ~ deriving_mark? ~ type_path }          // unchanged
```

`refines` is a reserved word. Its entries are today's `super_aspects` entries, with the same checks (RFC-0168 section on
super-aspects, RFC-0213 sections 2 to 4).

### 2. The old spelling

`aspect Foo: B` is a parse error whose message names the new spelling ("write `aspect Foo refines B`"). The colon after an aspect's
name has no meaning until RFC-0236 gives it one, so it is rejected and not silently accepted.

### 3. Negative entries

`aspect Copy refines !Drop` states an exclusion: no type may satisfy both (RFC-0213 section 3). It is a requirement on the
satisfying type, as a positive entry is, so it sits in the same clause. Open question 1 asks whether the word suits it.

### 4. Migration

Rewrite each `aspect A: ...` header. The language has no users, and no program depends on the old spelling beyond the corpus.

---

## Interaction with other work

- **RFC-0168** (draft) and **RFC-0213** (implemented): introduced and specified the entries; the colon in their examples becomes
  `refines`. Nothing else in either changes.
- **RFC-0234** (under review): the `deriving` mark stays on the entry (`refines deriving Clone`).
- **RFC-0236** (draft): needs the colon free so that an aspect can list instances of meta-aspects.
- **RFC-0207** (implemented): the colon list of a type and the `extend` form are untouched.

---

## Alternatives considered

1. **Keep the colon.** The reading conflict above; RFC-0236 would need a kind-directed rule.
2. **`requires`.** Reads naturally for positive and negative entries (`Copy requires Clone, !Drop`), and says "obligation on the
   satisfying type" directly. It also sounds like a bound on `Self`, which is accurate. Open question 1.
3. **`extends`.** One letter from the `extend` block keyword; rejected on confusability.
4. **`where Self: A`.** An expressible encoding (Rust's `trait A where Self: B`), but longer, and it hides the relation among
   the other bounds.
5. **`implies`.** States the direction wrongly: an aspect `Ord` implies `Eq`, but the entry belongs to `Ord` as a requirement.

---

## Open questions

1. **`refines` or `requires`.** `refines` is RFC-0168's word for the relation and reads well for positive entries (`Ord refines
   Eq`). A negative entry (`Copy refines !Drop`) is an exclusion and not a refinement, so the word stretches. `requires` covers
   both. The draft uses `refines`; the choice is open.
2. **Order against the instance list.** When an aspect has both `refines` and a colon list (RFC-0236), which comes first? This RFC
   leaves the colon list unspecified; RFC-0236 decides.

---

## Decision

**Outcome:** *(pending)*
