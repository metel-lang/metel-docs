---
id: rfc-0249
title: "Lang items replace aspect declaration properties"
date: '2026-11-23'
status: draft
---

## Summary

Std marks the types and aspects the compiler knows by identity with a **lang item** attribute, and the compiler resolves them by that key:

```metel
#lang_item("copy")
pub aspect Copy requires derived Clone, !Drop { }

#lang_item("clone")
pub aspect Clone { fun clone(&self) -> Self; }

#lang_item("drop")
pub aspect Drop { fun drop(&var self); }

#lang_item("option")
pub enum Option<T> derives Clone(T), Copy(T) { Some { value: T }, None }
```

This replaces three things:

1. **The `implicit` aspect property** (RFC-0212 §3). The compiler asks "which aspect is the `copy` lang item?", and the spec states what the `copy` lang item does in the ownership chapter. No abstract property says "satisfying this aspect copies".
2. **The string-keyed special cases.** `aspect_name == "Drop"` and its siblings become identity lookups of a lang item.
3. **The closed `builtins!` table in `identity/symbols.rs`**, which is a Rust macro listing 21 std items, becomes a list that std declares in its own source.

The remaining aspect properties are retired in the same change. `declared` and `derivable` become **meta-aspects** (RFC-0237, RFC-0238) that the compiler itself identifies by a lang item. `auto` is removed; it has no semantics today. After this RFC, no property keyword precedes `aspect`; only `pub` does.

This is a design draft. Nothing here is accepted. It would supersede RFC-0212 and reopen an alternative that RFC-0206 §8 and RFC-0212 §7 rejected; section "The reversal" explains why.

---

## Motivation

### 1. `implicit` is the definition of `Copy` under another name

RFC-0212 §3 defines `implicit` as "a by-value use of a type satisfying the aspect copies its representation instead of moving it".
That is what `Copy` means. The constraints on the property (it must refine `Clone` through a `deriving` super-aspect, std only, at most one per program) are the constraints of one aspect. The property is a compiler lang item for `Copy`, written as if it were a feature other aspects could use. RFC-0212 says as much: it "organises and exposes the compiler's privileged operation" and "does not make it ordinary library semantics".

A property that only one aspect can have, in one crate, once, is not a property. Calling it a lang item is more honest and leaves the semantic in the ownership chapter where it belongs.

### 2. The compiler still identifies std items by spelling

`metel-frontend/src/identity/symbols.rs` already holds a closed table of std items that the compiler knows by identity: 18 types (`boolean`, `String`, `Char`, the integers and floats, `List`, `Option`, `Result`, `Range`, `RangeInclusive`) and three aspects (`Display`, `Iterable`, `From`). The rest are matched by their spelling:

| Name | String-keyed sites (non-test, `metel-frontend` and `metel-interpreter`) |
|---|---|
| `"Drop"` | about 17: `declarations.rs`, `calls.rs`, `type_engine/mod.rs`, `abstract_bodies.rs`, `move_check/mod.rs`, `coherence/mod.rs`, others |
| `"Clone"` | about 11: `declarations.rs`, `expressions.rs`, `type_engine/mod.rs`, `coherence/properties.rs`, `clause_expansion/mod.rs` |
| `"Send"`, `"Sync"` | 7 in `type_engine/mod.rs`, although std declares neither |
| `"From"`, `"Iterable"` | look-ups by `(target_id, "From".to_string())` at `type_engine/mod.rs:6940-6950`, although both are in the identity table |

RFC-0206 listed "about 38 sites test the spelling `Copy`" and rejected the string-keyed case against ADR-0054, ADR-0066 and ADR-0067 (resolution by identity). `Copy` has since moved to the `implicit` property, but `Drop` and `Clone` have not.

### 3. The property mechanism has one live user and two others in waiting

| Property | State today |
|---|---|
| `implicit` | One user (`Copy`), std only (see 1). |
| `declared` | Live: `Copy`, `Linear`, and user markers. Needed as a general feature. |
| `derivable` | Std only. RFC-0238 already replaces it with a `Derivable` meta-aspect impl. |
| `auto` | Parses, std only, no semantics, no user. Deferred with the `Send`/`Sync` revision. |

So the mechanism's remaining general use is `declared`, and a meta-aspect covers it (RFC-0237).

### 4. The language has no list of what the compiler assumes about each std item

Whether `Option` has a special `?` rule, `Range` a literal syntax, `Display` a use in string interpolation: those assumptions are spread across the type checker. A reader of `core.mtl` cannot tell which declarations the compiler depends on and which are free to change.

---

## Proposal

### 1. The attribute

```
#lang_item("<key>")        // before an aspect, struct, enum or record declaration in std
```

- **Spelling.** `#` is the attribute sigil of RFC-0095 (under review). `@` is not available: RFC-0242 and RFC-0143 use `@s` for storage identities.
- **Std only.** The loader records that a declaration comes from the embedded standard library, as RFC-0212 §3 already does ("provenance is a property of the declaration"). `#lang_item` on a user declaration is an error (`T0045`).
- **The key set is closed and defined by the compiler**, not by std. An unknown key is an error.
- **One declaration per key per program.** A second declaration with the same key is an error at the second declaration.
- **A lang item the program does not use** need not be declared. Using one that has not been declared (a `copy` keyword with no `copy` lang item) is an error at the use, with the message that RFC-0212 gives today.

### 2. The initial key set

| Key | Declaration | What the compiler relies on (specified where) |
|---|---|---|
| `copy` | `Copy` | By-value use duplicates; the `copy` class keyword; sealed `Copy` (ownership chapter, RFC-0206 §2) |
| `clone` | `Clone` | The provided `Clone` for `Copy` types; derivation (RFC-0227, RFC-0234) |
| `drop` | `Drop` | Drop checks and exclusion from `Copy` (move check, RFC-0213) |
| `display` | `Display` | The bound of `print` and `println`, and the string conversion (existing builtin; rule to be listed in the spec row) |
| `iterable` | `Iterable` | Iteration, including `Range` (existing builtin; rule to be listed in the spec row) |
| `from` | `From` | Conversions between types, including the numeric ones (existing builtin; rule to be listed in the spec row) |
| `declared` | `Declared` (new, meta-aspect) | Section 4 |
| `derivable` | `Derivable` (meta-aspect, RFC-0238) | RFC-0238 |
| `boolean`, `string`, `char`, `i8`..`u64`, `f32`, `f64` | The primitive types | Literals and operators (existing builtins; rules to be listed in the spec rows) |
| `list`, `option`, `result`, `range`, `range_inclusive` | The std types | Literals and the special forms the checker gives them (existing builtins; rules to be listed in the spec rows) |
| `send`, `sync`, `linear` | Not declared | Reserved. Their special cases in `type_engine/mod.rs` and the `linear` keyword wait for the RFCs that specify them. |

The first two groups are the compiler's current knowledge, so no row adds an assumption. The table is the new thing: it is in std source and the spec, and each row cites the rule the compiler uses.

### 3. What each lang item fixes in the spec

For each row the spec states, once, what the compiler assumes: the ownership chapter for `copy`, `clone` and `drop`, and the relevant chapter for the others. The aspect's own declaration is no longer the place where a semantic is encoded. This is the answer to motivation 1: "a by-value use copies" is stated for the `copy` lang item and is not a property any aspect could claim.

### 4. `declared` and `derivable` as meta-aspects

`declared` is available to user aspects (`declared aspect Validated` is a legal marker today), so it needs a general form. Under RFC-0237 a **meta-aspect** is an aspect whose `Self` is an aspect:

```metel
#lang_item("declared")
pub aspect Declared for Aspect { }        // granted to an aspect, not a type

aspect Validated;
extend Validated: Declared { }             // Validated is satisfied only by a type's declaration clause
```

`Declared` is a std meta-aspect that the compiler identifies by the `declared` lang item. A user crate opts its own aspect in with an ordinary impl, which the orphan rule (RFC-0060, RFC-0237 §3) allows in the aspect's crate. Two impls for one aspect are `T0015`. `Derivable` is the same shape (RFC-0238 §7, which this RFC adopts unchanged).

`auto` is removed. If the `Send`/`Sync` revision of RFC-0096 needs a structural grant, it adds an `Auto` meta-aspect with its own lang item.

### 5. `Copy` declared in std

```metel
#lang_item("copy")
pub aspect Copy requires derived Clone, !Drop { }
extend Copy: Declared { }
extend Copy: Derivable { /* RFC-0238 section 3 */ }
```

RFC-0236 lets these impls sit inside the declaration. The `copy` class keyword resolves to the `copy` lang item and the keyword's `derives Clone, Copy` expansion to the `clone` and `copy` items. Nothing in the clause expansion refers to a property.

### 6. Resolution

After name resolution the compiler builds its lang-item table: key to `SymbolId`. Every use that now compares a spelling (`"Drop"`, `"Clone"`) or reads a property (`implicit`) reads the table. This makes resolution by identity (ADR-0054, ADR-0066, ADR-0067) the only way the compiler names a std item, with no exceptions.

---

## Staging

The three stages are independent. The first has no language-visible effect.

1. **Identity, now.** Replace the string-keyed sites with `Builtin` ids by extending the `builtins!` table with `Copy`, `Clone`, `Drop` (and `Declared`, `Derivable` when they exist). No attribute, no syntax. It deletes the 17 and 11 string sites and retires `implicit`'s lookup. This is the refactor ADR-0054 already asks for, and it is valuable even if the later stages never land.
2. **The attribute, with RFC-0095.** `#lang_item` replaces the `builtins!` macro: the table is read from `core.mtl`. Needs attributes to be implemented.
3. **Meta-aspects, with RFC-0237 and comptime.** `declared` and `derivable` become impls, and the property keywords are removed from the grammar.

---

## The reversal

RFC-0206 §8 and RFC-0212 §7 rejected "a lang-item attribute for one aspect, or a compiler-known marker" as "an exception keyed to a name", and chose declaration properties because the language owner prefers a general feature to an exception.

What this RFC changes is the generality, not the position. The rejected form was **one** attribute for **one** aspect. This is one registry for every std item the compiler depends on, and it removes exceptions: `Drop`, `Clone`, `From`, `Iterable`, the primitives and `Option` all take the same form. A property that only one aspect could hold was itself the exception; this RFC replaces it with the rule the compiler's other dependencies already follow. The language owner's reason (avoid special cases keyed to a name) is the reason for this RFC.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Keep the properties (status quo) | `implicit` is a one-user property whose definition duplicates `Copy`'s. `auto` has no semantics. The string-keyed sites for `Drop` and `Clone` are unaffected by properties. |
| Lang item for `Copy` only | It would remove `implicit` and leave 28 string sites and the `builtins!` macro as separate exceptions. |
| Only stage 1 (extend `builtins!`, no attribute) | Fixes the identity problem but leaves the set of compiler-known items in Rust source, not in std, and does not retire the properties. It is the first stage of this RFC, and a viable stopping point (question 1). |
| `@lang_item("copy")` | Conflicts with `@s` storage identities (RFC-0242, RFC-0143). |
| `lang` keyword before the declaration | A new keyword for a std-only feature; attributes exist for this (RFC-0095). |
| Derive the key from the declared name (as `builtins!` does) | Ties the compiler's knowledge to a spelling and a module path (`std::core`). The attribute lets the declaration be renamed, moved or re-exported without breaking the compiler. |
| A `std`-only boolean `#builtin` | It identifies the item but not its role, so the compiler would still need a name to know which one it is. |

---

## Interaction with other work

- **RFC-0212** (implemented). Superseded when this RFC is accepted: its properties are replaced as in sections 1 to 5. Its provenance rule (§3) and the T0045 error carry over.
- **RFC-0206** (implemented). §8's rejection of the lang-item form is reopened (see above). §2 (`Copy` semantics) is unchanged.
- **RFC-0213** and **RFC-0235**. Super-aspects (`requires`, `deriving`, negative entries) are unchanged; the `Copy` declaration keeps them.
- **RFC-0237** and **RFC-0238** (drafts). Section 4 depends on meta-aspects and adopts `Derivable`. If they change shape, this RFC follows.
- **RFC-0095** (under review). Supplies the attribute surface; stage 2 depends on it.
- **RFC-0096** (under review). Its `auto` mechanism loses its property; the revision decides what replaces it.
- **RFC-0244** (implemented, metel-core#2153). Independent. The `copy` keyword's lookup changes from "the `implicit` aspect" to "the `copy` lang item"; `copy?` (`derives Clone(..), Copy(..)`) is unaffected.
- **RFC-0246** and **RFC-0247** (under review). Derivation arguments and variadic parameters refine RFC-0238 §1 to 3, which this RFC's section 4 adopts for `Derivable`. They don't touch the properties and need no change here.
- **RFC-0236** (draft). Lets the std impls in section 5 sit inside the declaration.
- **ADR-0054, ADR-0066, ADR-0067.** Resolution by identity; this RFC completes it for std items.

---

## Costs

- **A second source of truth for the key set.** The compiler defines the keys; std attaches them. A typo in std is an error caught at startup, not at the use.
- **Std becomes compiler-coupled.** Moving a lang item is no longer a free edit. That is already true today for the 21 builtins; the attribute makes it visible.
- **Migration.** Stage 1 touches about 30 sites in `metel-frontend`. Stages 2 and 3 change `core.mtl`, the parser and the spec's aspect-property chapter, and remove the `AspectProperty` enum.
- **The one that is not a cost but must be said.** The semantic RFC-0212 §3 called `implicit` does not go away; it moves to the `copy` lang item's row in the spec. Whoever edits that row owns the change.

---

## Open questions

1. **Is the attribute needed, or only stage 1?** Extending `builtins!` fixes identity without attributes. The attribute's gains are that the set lives in std source and the properties retire. Recommendation: do stage 1 regardless, and decide the attribute with RFC-0095.
2. **Does the keyword-level lookup for `copy` and `linear` go through lang items?** Recommendation: yes, `copy` resolves to the `copy` item; `linear` is reserved.
3. **Dead special cases.** The `Send` and `Sync` arms in `type_engine/mod.rs` match names that std does not declare. This RFC reserves the keys; whether the arms are reachable, and whether to remove them now, is for the issue that carries stage 1.
4. **Should user crates get lang items?** For example a `no_std` or alternate core. Out of scope: the registry is std only, and a second std is not a supported configuration.
5. **Separate compilation.** Provenance (RFC-0212 §3, open question 6 there) and the lang-item table must be carried in compiled artifacts.

---

## Decision

**Outcome:** *(pending)*
