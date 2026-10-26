---
id: rfc-0184
title: "Rename Perhaps to Option"
date: '2026-10-24'
coverage:
  "1": { kind: blocked, reason: "the rename is integrated into spec.types.perhaps-t.legality-2 but not implemented; its fixtures land with the implementation", ref: "metel-core#1625" }
  "3": { kind: untestable, reason: "a cost analysis; it states no rule a program can exhibit" }
status: integrated
updated: '2026-10-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/1595'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1625'
impl_status: not-started
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

> **Status — accepted (2026-10-26).** Rename accepted by the language owner; hard cut, shadowable, RFC-0182 rewritten, dated posts left as records

> **Status — integrated (2026-10-26).** Spec section renamed with a new rule for the removed name; cross-checked against the integrated spec and the sibling RFCs

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

   **Decided (2026-10-26): rename.** Familiarity outweighs the identity argument for this name.
   RFC-0098's "costs nothing" premise does not hold here: the cost of keeping `Perhaps` is paid by
   every reader who knows `Some`/`None` as the variants of `Option`.
2. **Hard cut or transitional alias?** A one-release `type Perhaps<T> := Option<T>` would
   carry type positions, but qualified construction through an alias
   (`Perhaps::Some { … }`) needs checking, and the shadow rules (metel-core#1585) mean an
   alias in `std::core` can itself be shadowed. If the alias cannot keep construction paths
   working, the choice is a hard cut with a precise diagnostic ("`Perhaps` is now `Option`").

   **Decided (2026-10-26): hard cut, no alias.** After this lands `std::core` declares no
   `Perhaps`. Naming it where a type, a path, a pattern or an expression is expected is the existing
   `T0003` (unknown type, unresolved path, undefined name), and the message adds that `Perhaps` is now
   `Option`. The hint applies only while the name resolves to nothing: a module that declares its own
   `Perhaps` is unaffected. Pre-1.0 and a small user base make a one-release alias not worth its
   shadow-rule edge cases (metel-core#1585).
3. **Reserved or shadowable?** `Option` joins `Result` and `List` as a `std::core` type that
   a module may shadow (`spec.declarations.variables.scoping-and-shadowing.legality-9`).
   Is that acceptable for the most-used type, or should it be reserved like the intrinsic
   types (`legality-8`)? Not specific to this RFC; the rename just makes it likelier that a
   user declares a type with that name.

   **Decided (2026-10-26): shadowable**, like `Result` and `List` (`legality-9`). No new
   reserved-name rule; `int_03_generic_option_chain` and the shadowing fixtures keep working.
4. **Timing relative to `?` on `Option`.** If RFC-0182 is accepted, should it be rewritten
   to say `Option` first so the new rule never ships under the old name?

   **Decided (2026-10-26): yes.** RFC-0182's prose and examples were rewritten to `Option` with this
   RFC's acceptance. RFC-0182 stays under review; only its wording changed.
5. **Documentation and blog.** The v0.14.0 records post and getting-started pages show
   `Perhaps`. Are published posts rewritten, or left as dated records with a note?

   **Decided (2026-10-26): left as dated records**, with no note added. The specification, the
   tutorials, the getting-started pages and the README change to `Option` with the implementation;
   the v0.14.0 records post and other dated posts stay as published.

---

## References

- RFC-0020 — Language Keyword Rebranding (`nope` → `None`; `.yolo()` deferral).
- RFC-0098 — Surface Keyword Renames (the "deliberate identity" rationale for `Perhaps`).
- RFC-0079 — `Perhaps<T>` and `Result<T, E>` (refused; the types as described).
- RFC-0182 — `?` on `Perhaps`.
- metel-core#1585, #1570 — by-name lookups of core types, the same sites the rename touches.
- `reference/spec/types.md` — "Perhaps<T>" (`spec.types.perhaps-t.*`).

---

## Integration cross-check (2026-10-26)

The rename is not implemented, so these worked examples are derived from the integrated spec's rules, not
run; each becomes a fixture with the implementation (metel-core#1625). They hunt for interactions with
already-integrated features and with the sibling RFCs still under review.

**1. The removed name, at every site the hint covers** (`spec.types.perhaps-t.legality-2`).

```metel
import std::core::Perhaps;                       // T0003, "`Perhaps` is now `Option`"
fun f(x: Perhaps<i64>) -> i64 { 0 }              // T0003, same hint (type position)
fun g() { let a := std::core::Perhaps::None; }   // T0003, same hint (qualified path)
fun h() { let b := Perhaps::None; }              // T0003, same hint (leading path segment)
```

The hint is an addition to the message of the existing code; no new code, and no change when the name
resolves to something. It must not fire for a path that merely ends in `Perhaps` (`other::Perhaps` where
`other` is a user module that declares no such item): that is an ordinary unresolved path.

**2. A module that declares its own `Perhaps`** is a user type like any other. After the rename it no longer
shadows anything, so `enum Perhaps { Maybe, Not }` plus `Perhaps::Maybe` resolves to the user's enum with no
hint, and the shadowing fixtures written against the old name keep their meaning once they shadow `Option`.

**3. Shadowing `Option`** (`scoping-and-shadowing.legality-9`, metel-core#1585). A module-level or
block-local `enum Option<T> { Has { v: T }, Nothing }` wins for names written in that module; a value
`std::env::get` returns keeps the core type, so `match` on it names core's `Some`/`None`. Naming the core
type from inside the shadowing module works in a type position (`std::core::Option<i64>`, #1587). The
qualified *expression* form (`std::core::Option::Some { value = 1 }`) resolves to the module's own `Option`
today for the same reason it does for `Result` (metel-core#1616, open): the rename inherits that bug, it
does not add one. The interaction is recorded here so the fixture for it is written against #1616's fix, not
against the bug.

**4. Aliased imports of the core type** (#1588). `import std::core::Option as Opt;` then
`let r: Opt<i64> := Opt::Some { value = 1 };` constructs against the annotation, as `import std::core::Result
as CR;` does today. The alias is a user-chosen name, so the hint never applies to it.

**5. `?` on `Option`** (RFC-0182, rewritten to `Option` with this acceptance). The enclosing-return-type
constraint compares the core `Option`, not a name; a function returning a shadowing user `Option` is neither
`Result` nor the core type and keeps the "needs the enclosing function to return" error. No interaction with
the rename beyond the spelling in the messages.

**6. The intrinsic-name reservation** (`legality-8`). `Option` is not an intrinsic type name and is not added
to the list; `T0038` does not apply, and `int_03_generic_option_chain` (a user `enum Option<T>`) keeps
compiling. The reserved list and the shadowable core list stay disjoint.

**7. Diagnostics that print the type.** Unification, bound and record-diff messages print `Option<String>`.
Nothing in the message grammar depends on the name; the `T0001` text in RFC-0182's example becomes
`cannot unify Option<String> with Result<?1, ?2>`.

**8. Identity.** The core declaration is interned once under its new name, and a user `Perhaps` or `Option`
gets its own `Declared` id (ADR-0065: ids are tagged, so no kind can collide). The by-name registry sites
the RFC lists compare the declaring module's id since metel-core#1585/#1604; the rename changes the
registered string and the `Builtin` variant, not how a site finds the type.

**9. Sibling RFCs.** RFC-0182 (rewritten, no remaining dependency on the old name). RFC-0183 (`:=` is
initialization-only), RFC-0185 (type-directed dereference) and RFC-0186 (row operator) do not mention the
type or its variants in a rule; their examples that say `Perhaps` change spelling only, when those RFCs
are next edited.

**Result.** No contradiction with the integrated spec and none with the RFCs active in the same cluster.
One dependency is recorded (example 3, #1616); it is an existing bug the rename does not worsen.


---

## Decision

**Outcome:** accepted, 2026-10-26, by the language owner.

`Perhaps<T>` is renamed `Option<T>`. Variants (`Some { value }`, `None`) and methods are unchanged,
and so are semantics, AST shape and type checking.

- **Hard cut.** `std::core` declares no `Perhaps` once this lands, and there is no alias. Using the
  name where nothing declares it is `T0003` with a message saying `Perhaps` is now `Option`.
- **Shadowable.** `Option` may be shadowed by a module-level or block-local declaration, exactly as
  `Result` and `List` may.
- **RFC-0182** is rewritten to say `Option` (done with this acceptance).
- **Dated posts** are left as records; live pages change with the implementation.
- **Spec anchors** such as `spec.types.perhaps-t.*` keep their ids; prose and headings change.
