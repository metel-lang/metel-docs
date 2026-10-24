---
id: rfc-0184
title: "Rename Perhaps to Option"
date: '2026-10-24'
status: draft
---

## Summary

Rename the core absence type `Perhaps<T>` to `Option<T>`. The variants `Some { value }` and
`None` are unchanged, as are all methods (`is_some`, `unwrap_or`, `and_then`, `ok_or`,
`yolo`, ...). Only the type's name changes, in the type position, in qualified paths
(`std::core::Option::Some`), in diagnostics, and in the specification.

```metel
fun first(xs: [i64]) -> Option<i64> {     // was Perhaps<i64>
    if (xs.len() == 0) { return None; }
    Some { value = xs[0] }
}
```

This reverses a deliberate naming choice, so it states the case for and against below
rather than treating the rename as cosmetic. It is a breaking change to a name used in a
large part of every program that handles absence, so it needs this RFC first (see
`metel_rfc_before_implementation`).

---

## Motivation

### Familiarity

`Option` (Rust, Scala, OCaml, F#; `Optional` in Swift and Java) is what most readers already
call this type. RFC-0020
renamed the empty variant from `nope` to `None` on exactly this ground: "`None` is the
near-universal spelling for an absent optional value … `nope` is memorable but teaches the
wrong habit and surprises every developer familiar with typed languages." The type name has
the same property: `Some`/`None` are the universal pair of variants and `Option` is the
universal name of the type that has them; `Perhaps` is the one piece of the trio that is
not.

### The name reads against its own variants

`Perhaps<T>` with variants `Some` and `None` mixes registers: "perhaps" is an adverb of
uncertainty, "some/none" are quantities. `Option<T>` reads as a noun for a thing that may or
may not hold a value, and its spelling tells the reader what `Some`/`None` are variants *of*.
In diagnostics today, the user sees `Perhaps<String>` next to `Some`/`None` in the same
message and has to learn they belong to the same thing.

### Collision pressure from user code

Programs written by people who know the type as `Option` define their own: the integration
fixture `int_03_generic_option_chain.mtl` declares `enum Option<T>`. Since metel-core#1585
shadowing a core type is allowed and the user's definition wins, so this works, but it is a
sign of what authors reach for. With the core type called `Option`, there is nothing to
reinvent.

### Not a new axis

This is a pure rename. It changes no semantics, no AST shape, no type-checking behaviour.

---

## Prior decisions this has to answer

- **RFC-0098** lists `Perhaps<T>` not `Option<T>` among the places where Metel "already
  diverges from Rust's naming where it costs nothing — … a deliberate identity rather than
  an accident of copying Rust's grammar". That RFC's rationale is the main argument *against*
  this one, and its premise ("costs nothing") is the thing to check: the cost of keeping
  `Perhaps` is the familiarity friction above, paid by every reader, while the cost of
  renaming is paid once, now, by a small user base. Whether the identity argument outweighs
  that is the central open question (Open Question 1).
- **RFC-0020** deferred the rename of `.yolo()` "pending the stdlib migration of `Result` and
  `Perhaps`; the rename will be decided as part of that work, when the full method surface of
  both types is known." That migration has happened (`Perhaps` and `Result` are declared in
  `std::core`), and this RFC does not touch `.yolo()`; if it is to be reconsidered it is a
  separate question.
- **RFC-0079** (refused) describes `Perhaps` and `Result` as the two primary types; nothing
  in it is a design objection to the name.

---

## 1. Scope of the rename

| Surface | Change |
|---|---|
| Type name in `std::core` (`enum Perhaps<T>` in `core.mtl`) | `enum Option<T>` |
| Qualified paths (`std::core::Perhaps::Some`) | `std::core::Option::Some` |
| Diagnostics that print the type (`cannot unify Perhaps<String> with …`) | `Option<String>` |
| Variants `Some { value }`, `None`; bare-variant patterns | unchanged |
| Methods (`ok_or`, `unwrap_or`, `yolo`, `and_then`, `is_some`, ...) | unchanged |
| `Result::ok(self) -> Perhaps<T>` and every other signature that mentions the type | spelled `Option<T>` |
| Spec anchors such as `spec.types.perhaps-t.*` | keep stable ids; the prose and headings change |
| Other RFCs' prose and worked examples | updated mechanically when this lands |

### Implementation surface (for sizing, not a design)

- `std::core` declarations in `core.mtl` (about 30 occurrences) and one in `env.mtl`.
- The compiler names the type as a string literal at 13 sites across 8 Rust files
  (inference and construction of enum literals, path normalisation, builtins, display,
  symbols, the stdlib docs checker, stdlib tests). These are the same by-name sites that
  metel-core#1570 / #1585 track; the rename is a good moment to key them by the core
  declaration's id instead of by spelling.
- Roughly 60 integration fixtures and 50 spec lines mention `Perhaps`; about 70 Markdown
  files in this repository do.

### The path forward for users

Pre-1.0 and no edition gating (RFC-0020's precedent). Two options, in Open Question 2:
a hard cut, or one release in which `Perhaps` remains as a deprecated alias.

---

## 2. Alternatives considered

1. **Keep `Perhaps`.** The identity argument of RFC-0098: the name is distinctive, already
   shipped, and every doc and fixture uses it. Costs nothing to do; the friction is
   ongoing and unmeasured.
2. **`Maybe`** (Haskell/Elm). Shorter and also an English word, but the `Some`/`None`
   variants are the Rust/ML family's, and `Maybe` goes with `Just`/`Nothing`. It trades one
   mismatch for another.
3. **`Optional`** (Swift, Java). Longer than `Option`, no stronger ground.
4. **Both names for ever**, `Option` as an alias of `Perhaps`. Two spellings of the most
   common type in the language split every codebase's style and every diagnostic's wording;
   rejected for permanence, though a *transitional* alias is Open Question 2.
5. **Sugar `T?`** (Kotlin/Swift). A separate surface-syntax question that would conflict
   with `?` as the propagation operator (RFC-0182 and the spec's "The ? Operator"). Not
   proposed.

---

## 3. Costs

- **A breaking rename of a type named in most programs.** Every signature, annotation,
  qualified path and message that says `Perhaps` changes. The rewrite is mechanical
  (token `Perhaps` in type or path position, never a variable name), but it is a
  whole-codebase edit.
- **Churn in implemented RFCs and the spec.** RFC-0020, RFC-0098, RFC-0142 and
  others use `Perhaps` in normative examples; the spec has dozens of mentions. Anchors stay
  stable; prose changes.
- **Loss of a distinctive spelling** (RFC-0098's point). Unquantifiable, and the thing most
  likely to decide the RFC either way.
- **Interaction with open drafts.** RFC-0182 (`?` on `Perhaps`) and other drafts name the
  type; whichever merges second rewrites its examples.

---

## Open Questions

1. **Does the identity argument (RFC-0098) outweigh the familiarity argument?** This is a
   taste decision with a recorded precedent on each side (`nope` → `None` for familiarity,
   `Perhaps` kept for identity). The RFC's job is to make the trade explicit; the decision
   is the language owner's.
2. **Hard cut or transitional alias?** A one-release `type Perhaps<T> := Option<T>` would
   carry type positions, but qualified construction through an alias
   (`Perhaps::Some { … }`) needs checking, and the shadow rules (metel-core#1585) mean an
   alias in `std::core` can itself be shadowed. If the alias cannot keep construction paths
   working, the choice is a hard cut with a precise diagnostic ("`Perhaps` is now `Option`").
3. **Reserved or shadowable?** `Option` joins `Result` and `List` as a `std::core` type that
   a module may shadow (`spec.declarations.variables.scoping-and-shadowing.legality-9`).
   Is that acceptable for the most-used type, or should it be reserved like the intrinsic
   types (`legality-8`)? Not specific to this RFC; the rename just makes it likelier that a
   user declares a type with that name.
4. **Timing relative to `?` on `Option`.** If RFC-0182 is accepted, should it be rewritten
   to say `Option` first so the new rule never ships under the old name?
5. **Documentation and blog.** The v0.14.0 records post and getting-started pages show
   `Perhaps`. Are published posts rewritten, or left as dated records with a note?

---

## References

- RFC-0020 — Language Keyword Rebranding (`nope` → `None`; `.yolo()` deferral).
- RFC-0098 — Surface Keyword Renames (the "deliberate identity" rationale for `Perhaps`).
- RFC-0079 — `Perhaps<T>` and `Result<T, E>` (refused; the types as described).
- RFC-0182 — `?` on `Perhaps`.
- metel-core#1585, #1570 — by-name lookups of core types, the same sites the rename touches.
- `reference/spec/types.md` — "Perhaps<T>" (`spec.types.perhaps-t.*`).

---

## Decision

**Outcome:** *(pending)*
