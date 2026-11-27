---
id: rfc-0236
title: "Inline Implementations in a Declaration"
date: '2026-11-16'
status: draft
---

## Summary

A struct, enum or aspect declaration carries its aspect implementations in **named blocks** beside its fields, variants or
signatures. The colon list names the aspects the declaration claims (RFC-0207); a block named for one of them holds its methods:

```metel
struct Token: Display, Validated {
    kind: i64,
    text: String,

    Display { fun fmt(&self) -> String { self.text } }      // the implementation of Display for Token
    Token   { fun len(&self) -> i64 { self.text.len() } }   // inherent methods, in a block named for the type
}

struct Wrapper<T>: Clone {
    value: T,
    Clone where T: Clone { fun clone(&self) -> Wrapper<T> { Wrapper { value = self.value.clone() } } }
}
```

`Validated` is a marker and has no block. `extend` stays, and adds only what the declaration does not list: an implementation for
a type declared elsewhere, or for one instantiation of a generic type, or an aspect another module adds. An implementation
that the declaration lists is written in the declaration and nowhere else.

This RFC takes over RFC-0105 (aspect lists in declarations) and RFC-0104 (shared bodies in multi-aspect `extend` blocks), whose
purposes it serves with one mechanism, and supersedes both. It depends on RFC-0235 (`requires`) for the aspect form. This is a
design draft. Nothing here is accepted.

---

## Motivation

1. **The declaration says what a type claims and not what it is.** RFC-0207 gave the declaration its colon list and `derives`
   clause: a type states there which aspects it claims and which it derives. Every method-bearing aspect still lives in an
   `extend` block elsewhere, so a reader of `struct Token: Display` has to find that block. RFC-0207 names this as "method-bearing
   aspects in the colon list, the later stage of RFC-0105"; RFC-0105's own text never specified it, because it kept the
   declaration's body fields-only and made a positive entry an obligation to be discharged by an `extend` elsewhere.
2. **That obligation model needs a whole-graph pass.** RFC-0105 section 3 checks, at the declaration, that a satisfying `extend`
   exists somewhere in the loaded program, in coherence's pass, and section 4 needs auto aspects injected into the same
   registry. With the body in the declaration the check is local and the registry change is not needed.
3. **Registration by an impl reads best next to the thing registered.** RFC-0227 and RFC-0093's registration design puts a
   derivation in an impl of `Derivable` for the aspect. Written in the aspect's own declaration (stage 2 below) it is one place,
   and the orphan rule is satisfied by construction.
4. **A shared body (RFC-0104) is the wrong answer to a real problem.** RFC-0104 asks for one `extend` body to satisfy several
   aspects, disambiguated by method name and rejected when two aspects declare the same name. Named blocks say which aspect a
   method belongs to, so no shared pool and no collision rule is needed.

---

## Proposal

### 1. Named blocks

A declaration body holds its own items and **named blocks**:

```
block = { path ~ generic_args? ~ where_clause? ~ "{" ~ impl_item* ~ "}" }
```

- **An aspect block** is named for an entry of the declaration's colon list (with its arguments, RFC-0228) and is the
  implementation of that aspect for the declared type. It may carry a `where` clause, which is the impl's conditions
  (`Clone where T: Clone`). Its items are what an `extend` block's would be.
- **An inherent block** is named for the declared type (`Token { .. }`) and holds methods that belong to no aspect.
- A struct body holds fields and blocks, an enum body variants and blocks, in any order. A block never contains fields.
- Two impls of one aspect for different arguments (RFC-0228) are two blocks: `Conv<i64> { .. }` and `Conv<String> { .. }`.

### 2. The colon list is the grant list

The entries are unchanged from RFC-0207: marker aspects (no methods, `declared`), negative entries (`!Send`), and now
method-bearing aspects.

1. A marker or negative entry has no block.
2. A method-bearing entry has a block, or is derived by `derives` (RFC-0207), and otherwise is an error at the declaration:
   "`Display` has required methods; add a `Display { .. }` block". An aspect whose methods all have defaults needs no block.
3. A block named for an aspect that is not in the colon list is an error naming the list.
4. An aspect both in a block and in `derives`, or in two blocks, is `T0015`, the overlap of two implementations.

### 3. What `extend` is for

`extend T: A { .. }` may **not** implement an aspect that the declaration of `T` lists: that is an error whose fix-it moves the
body into the declaration. It remains the only way to write:

- an implementation for a type declared in another module or crate (RFC-0060's coherence rules decide who may);
- an implementation for one instantiation of a generic type (`extend Wrapper<String>: Display`);
- an aspect that no entry of the declaration lists, because the declaring module did not claim it.

`extend` for a `declared` aspect remains an error (RFC-0207): such an aspect is granted in the declaration.

### 4. Enforcement

There is no whole-graph obligation. A listed method-bearing aspect is checked at the declaration against its block, like any
impl, and coherence (RFC-0060) sees the block as the impl. Auto aspects (RFC-0096) are markers and are unchanged.

### 5. Aspect declarations (stage 2)

An aspect declaration has its own colon list, free once RFC-0235 moves super-aspects to `requires`. An entry names a meta-aspect
the aspect is an instance of, with a block for it:

```metel
aspect Serialize: Derivable {
    fun serialize(&self) -> String;                                   // Serialize's own signature
    Derivable { type Args = .{ .rename_all: String = "none" }; comptime fun derive(..) -> Decl { .. } }
}
```

The rules of section 2 apply unchanged. This stage needs aspects as comptime values and a `Derivable` aspect (RFC-0092,
RFC-0132 and the registration RFC), none of which exist. It is specified here so that the grammar leaves room, and takes effect
when they do.

### 6. Enum bodies

A variant (`Circle { r: i64 }`) and a block (`Display { fun fmt(..) .. }`) are both `Name { .. }`. They are told apart by their
items: a block's items are `fun` and `type`, a variant's are fields. A variant named like a listed aspect, or like the enum
itself, is an error, so a name is never both.

---

## Interaction with other work

- **RFC-0207** (implemented): the colon list and `derives` are unchanged; this is the later stage it names.
- **RFC-0105** (draft) and **RFC-0104** (draft): superseded by this RFC.
- **RFC-0102, RFC-0103** (implemented): bodyless `extend` and bodyless aspect declarations are unchanged.
- **RFC-0259** (draft): owns qualified call syntax. Its path-form candidate could inform the
  notation for inline implementation blocks.
- **RFC-0227, RFC-0234** (under review): a derived aspect is not written in a block; `derives` and a block for one aspect is `T0015`.
- **RFC-0235** (draft): the aspect form needs the colon free.
- **RFC-0060** (coherence): an impl in a block is an ordinary impl for the overlap and orphan checks.

---

## Alternatives considered

1. **Obligations discharged by `extend` (RFC-0105).** Keeps the declaration fields-only and needs the whole-graph check and the
   auto-aspect registry change. Rejected: the inline body makes the check local.
2. **A shared `extend` body with a collision rule (RFC-0104).** Rejected under Motivation 4.
3. **Qualified method names (`fun Display::fmt`).** Repeats the prefix per method, groups nothing, and puts methods of different
   aspects in one flat list. A block is an `extend` body with its header implied.
4. **A home rule: impls for a type declared in this module must be inline.** Gives each impl one place by construction. It makes
   large declarations long and forbids grouping impls elsewhere in the same module. Open question 1.
5. **Bodies only for `declared` aspects.** Bodies where the language already requires the declaration, `extend` for the rest.
   One home by aspect property and no bloat, but `struct Foo: Clone { .. }` would be rejected. Open question 1.
6. **Inline impls with no colon-list entry (a block alone grants).** Removes the double mention of an aspect (list and block).
   Open question 2.

---

## Open questions

1. **The partition between declaration and `extend`.** The proposal lets the author choose per aspect, with the two sets disjoint
   (section 3). That leaves two spellings with a free choice. The home rule (alternative 4) and the `declared`-only rule
   (alternative 5) each give one home; which is wanted?
2. **Does a block alone grant?** The proposal names an aspect twice: in the list and in its block. If a block named for an
   aspect also granted it, the list would hold only bodyless entries. The list then no longer summarises the type's aspects.
3. **Enum bodies (section 6).** Is the item-based disambiguation enough, or should blocks be marked (`impl Display { .. }`)?
4. **Order of blocks and fields.** Free, as the draft says, or fields first?
5. **Generic instantiation impls.** Is `extend` for one instantiation the right residue, or should a block take type arguments
   (`Wrapper<String>: Display { .. }` inside the declaration)?
6. **Visibility.** A block's methods follow RFC-0032's rules as in an `extend`; whether a block as a whole has a visibility is
   not decided here.

---

## Decision

**Outcome:** *(pending)*
