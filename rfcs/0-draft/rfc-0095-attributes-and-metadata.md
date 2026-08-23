---
id: rfc-0095
title: "Attributes and Metadata"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects), as part of decomposing that RFC into smaller, independently
> reviewable pieces. Mostly independent of the comptime cluster (RFC-0092/0093/0094):
> pure compiler hints (`#inline`, `#cfg`, `#allow`) need nothing from comptime and could
> ship first. Only the "attributes as comptime-visible metadata" piece (§2) depends on
> RFC-0092's `typeinfo`.
>
> **Sigil changed from `@` to `#`, 2026-08-23 — real collision found, not a taste
> change.** This RFC's original §1 claimed `@` was "already unused in Metel's grammar
> (outside allocators, which use it in a different grammatical position)" — asserted,
> not demonstrated. It doesn't hold: `@` is the sigil of the *accepted*
> allocator/region cluster (RFC-0063, RFC-0065, RFC-0073 — all `2-accepted`), used
> across roughly 400 lines in 42 RFC files, in at least seven distinct grammatical
> positions (`@a T` type-prefix, `@a Node {...}` literal-prefix, `(@a: A)` parameter,
> `<@a>` generic tag, `(@a) -> {...}` closure parameter, `wrap(@a, ...)` call argument,
> bare `@a val`). `@a T` is also cited as a stable scoping boundary inside
> already-*implemented* RFCs (e.g. RFC-0067a: "This RFC does not include ... any
> allocator-pointer (`@a T`)"), and RFC-0063 §4 gives `@` a real mnemonic rationale for
> allocators specifically ("mirrors the address-of sigil — `@` means 'this is about
> allocation'"). No hard PEG ambiguity was found between the two proposed uses —
> attributes always require a following declaration keyword, which no allocator form
> occupies — but the readability cost of two unrelated sub-languages sharing the
> language's most visible sigil was judged real regardless. Moving the allocator sigil
> instead was considered and set aside: its surface is roughly 3-4x this RFC's (42 files
> / ~400 lines vs. 14 files / ~105 lines), it is further along in the process
> (`2-accepted` vs. this RFC's `0-draft`), and it is genuinely cheaper to move the
> sigil that has shipped zero lines of implementation (`grammar.pest` has no allocator
> rule at all yet) than the one other already-implemented RFCs cite as a boundary
> marker. `#` was chosen over `~`, `^`, backtick, `$`, and a keyword-based alternative
> (`attr ...`) — see Alternatives Considered.

## Summary

Specifies `#` as the single grammar symbol for attributes and metadata: compiler hints
(`#inline`, `#cold`, `#must_use`), conditional compilation (`#cfg(...)`), FFI
annotations (`#extern("C")`), lints (`#allow(...)`, `#deny(...)`), and documentation
(`#doc(...)`). Also specifies that field- and type-level attributes are not independent
of the comptime derive mechanism (RFC-0093) the way pure compiler hints are — they are
exactly the kind of metadata a comptime derive function needs to read to customize its
output (skip a field, rename it), matching how nearly every language with both a
metadata layer and a reflection/codegen layer actually uses them.

---

## Motivation

Without a principled attribute syntax, compiler directives accumulate as ad-hoc
keywords or magic comments. A single syntax form (`#`) handles all of them uniformly.

Whether this is independent of the derive mechanism depends on which attribute. Pure
compiler hints (`#inline`, `#cold`, `#must_use`, `#allow`, `#deny`) are: nothing about
RFC-0093 changes what they mean or how they're checked. Field- and type-level
attributes are not — they are exactly the kind of metadata a comptime derive function
needs to read to customize its output, and treating them as unrelated to comptime, as
an earlier revision of this thread's design did, doesn't match how nearly every
language with both a metadata layer and a reflection/codegen layer actually uses them:
Rust's derive macros read sibling attributes (`#[serde(rename = "...")]`,
`#[serde(skip)]`) to customize their generated code; C#/Java's serialization and ORM
frameworks reflect over annotations precisely to decide field-by-field behavior. §2
works this out concretely.

---

## 1. Preferred Syntax: `#`

The preferred grammar symbol for attributes and metadata, derive included, is `#`,
written bare — no brackets — directly before the item it annotates.

```metel
#derive(Clone, Eq)
struct Point {
    x: Float,
    y: Float,
}

#inline
fun fast_path(n: Int) -> Int { n * 2 }

#cfg(target = "linux")
fun platform_init() { ... }

#allow(unused)
let _debug_value = compute();
```

Multiple attributes stack vertically, one per line, before the item they annotate.
Attributes apply to the next declaration or binding — they do not apply to
expressions. Derive uses `#derive(Aspect, ...)`, both to request derivation (attached
to a struct/enum) and to register an implementation (attached to a comptime
function) — see RFC-0093.

The `#` form (bare, no brackets) is preferred because:
- it is genuinely unclaimed in Metel's own grammar — checked directly against
  `grammar.pest`, not assumed. Unlike `@` (allocators, `2-accepted`), `$` (string
  interpolation, `${...}`, *implemented*), `!` (negation and the bottom type), and `?`
  (error propagation), `#` has no existing meaning anywhere in the language;
- it is the closest match to prior art for exactly this concept: Rust's
  `#[derive(...)]` / `#[inline]` / `#[cfg(...)]` map almost one-to-one onto this RFC's
  own headline examples;
- `#(...)` is unambiguous as a prefix — no bracket/brace confusion with other
  constructs, the same property Rust's bracketed `#[...]` has, without needing the
  brackets (see Alternatives Considered for why bare is preferred over bracketed).

The honest cost, stated plainly: `#` is associated with comments in several widely-used
languages (Python, shell, Ruby, PHP) that Metel programmers are likely to have used.
Metel itself never uses `#` for comments (`//` and `/* */` are the only comment forms),
so there is no actual in-language collision — but a reader's first-glance expectation
from those other languages is a real, if soft, cost. See the status note above for why
`#` was chosen over the alternatives that avoid this cost in exchange for a different
one.

---

## 2. Attributes as comptime-visible metadata

Not every `#` attribute interacts with comptime. Pure compiler hints — `#inline`,
`#cold`, `#must_use`, `#allow`, `#deny` — are directives the compiler reads directly;
comptime derive code has no reason to see them, and nothing else in this section
applies to them.

Field- and type-level attributes are different. In nearly every language with both a
metadata layer and a reflection/codegen layer, the two are tightly coupled: Rust's
derive macros read sibling attributes to customize their generated code; C#/Java's
serialization and ORM frameworks reflect over annotations precisely to decide
field-by-field behavior.

Concretely: for a comptime derive function to honor `#skip` or `#rename(...)`,
`typeinfo(T)`'s row (RFC-0092 §2) needs to carry each field's attributes, not just its
name and type — a gap in RFC-0092's row-metadata question (Open Question 1), alongside
declaration order and visibility.

```metel
struct User {
    id: i64,
    #skip
    password_hash: String,
    #rename("full_name")
    name: String,
}

comptime fun derive_display(comptime T: type) {
    let fields = typeinfo(T).row;   // now carrying each field's # attributes too
    emit extend T: Display {
        fun to_string(self: &T) -> String {
            // ordinary comptime code: skip fields tagged #skip, and use
            // #rename's argument in place of the field's own name
        }
    }
}
```

**`#cfg` deserves its own note**, because Zig doesn't have a separate attribute for
conditional compilation at all — it's ordinary `comptime if`, branching on a
comptime-known value, the same mechanism as everything else in the comptime cluster.
Whether Metel's `#cfg` should stay its own attribute or collapse into comptime `if` the
way macros collapsed into generalized `emit` (RFC-0094) is folded into Open Question 4
rather than treated as settled here.

**One open design fork this raises, not resolved here:** should a derive function's own
configuration travel as arguments nested inside `#derive(...)` itself
(`#derive(Serialize(rename_all = "camelCase"))`), or always as separate per-field/
per-type `#` attributes read via `typeinfo`, as sketched above? Rust does the latter —
configuration lives beside the derive, not inside its invocation. Recorded as RFC-0093
Open Question 5 rather than decided here.

---

## Alternatives Considered

### `@` (original preferred choice, reversed 2026-08-23)

The original preference, for the reasons the pre-reversal text of this section gave:
distinct from all current Metel operators (as understood at the time) and consistent
with annotation syntax in several modern languages (Java, Python decorators, Zig's
`@builtins`). Reversed on finding it was not, in fact, unclaimed — see the status note
at the top of this document for the full accounting. The `@` sigil stays with the
allocator cluster (RFC-0063/0065/0073, `2-accepted`), which has both more surface
already written against it and a real mnemonic rationale ("mirrors the address-of
sigil") specific to allocation that wouldn't transfer to metadata.

### `#[...]` Rust-style, bracketed

The literal Rust form. Rejected in favour of bare `#name(...)` (no brackets): the
brackets exist in Rust to delimit a list of attributes and their arguments from
surrounding tokens, but Metel's attributes already stack one per line with no
surrounding ambiguity to resolve (see §1's third bullet), so the brackets add visual
noise without adding disambiguation power here. Both share the `#` sigil and its
comment-association cost; bracketing was independent of that choice and evaluated
separately.

### `~`, `^`, backtick, `$`

Each checked directly against `grammar.pest` for whether it is genuinely free:
- **`~` and `^`** are both unclaimed, but neither carries meaningful attribute
  precedent. `~` reads as Elixir's sigils, a different concept (transforming a literal,
  not declaring metadata); `^` has no attribute precedent at all and pulls a reader's
  expectation toward pointers/types (Odin's dereference operator, F#'s statically
  resolved type parameters) — actively the wrong association for this feature.
- **Backtick** is unclaimed but structurally wrong: it is almost universally a *paired*
  delimiter (Markdown code spans, JS template literals, SQL identifiers), not a leading
  single-character sigil. Unpaired use here would read as a typo more than an
  annotation.
- **`$`** is *not* free — it is live, implemented syntax for string interpolation
  (`${expr}` inside string literals, checked against both `grammar.pest` and
  `public/reference/spec/lexical.md`). A bare `$name` outside a string literal would not
  be a hard parsing collision (different lexical context), but it would be a real
  in-language habit collision: every Metel programmer already reads `$` as "string
  interpolation is happening," from writing ordinary string literals, not from some
  other language's convention. That cost is sharper than `#`'s, because it's already
  true of Metel itself rather than being a maybe-true-if-you-came-from-elsewhere cost.

### No attribute syntax — ad-hoc keywords only

Each compiler directive is its own keyword or syntax form. Avoids designing a general
system but leads to keyword proliferation and inconsistency. Rejected as a long-term
position; acceptable only before v0.5 when no attribute-dependent features have
shipped. A keyword-based prefix (e.g. `attr derive(Clone, Eq)`) was also considered as
a middle ground — it sidesteps the punctuation question entirely, at the cost of the
scannability a single leading symbol gives: attributes are meant to visually jump out
as "not the code path" at a glance, and a keyword blends into ordinary syntax more than
a sigil does.

---

## Interaction with Other RFCs

### RFC-0001 (Pointers) and RFC-0026 (Unsafe Blocks)

`#extern("C")` for FFI function signatures (RFC-0026 open question 4) uses the `#`
attribute syntax defined here. The attribute system is a soft prerequisite for a clean
FFI story; unaffected by the comptime cluster.

### RFC-0009 (Module System)

`#pub`, `#cfg`, and documentation attributes interact with the module system's
visibility model. Also relevant to §2 directly: reflection's need for per-field
visibility (RFC-0092 Open Question 1) means `typeinfo` and the module system's privacy
rules are not fully independent.

---

## Open Questions

1. **`#` attribute scope.** What items can be annotated — struct/enum declarations,
   function declarations, `let` bindings, individual fields? Field-level attributes
   (e.g. `#skip` on a field to exclude it from `Display`) are no longer just "useful
   but add parsing complexity" — §2 gives them a concrete consumer (comptime derive
   functions reading them via `typeinfo`), so this question is load-bearing for
   RFC-0092 Open Question 1, not merely nice-to-have.

2. **Compiler-known attribute registry.** The compiler needs a fixed set of recognised
   `#` attributes (e.g. `#inline`, `#cfg`, `#allow`). Should unknown `#` attributes be a
   compile error, a warning, or silently ignored (for forward compatibility)?

3. **`#cfg` and conditional compilation.** Conditional compilation is a significant
   feature in its own right (platform-specific code, feature flags). Should `#cfg` be
   in scope for this RFC or a separate one?

4. **Does `#cfg` collapse into comptime `if`?** §2 adds a sharper version of Open
   Question 3: Zig has no `#cfg`-equivalent attribute at all, using ordinary
   `comptime if` instead — should Metel's `#cfg` similarly collapse into comptime `if`,
   the way general macros collapsed into generalized `emit` (RFC-0094), rather than
   staying a bespoke directive? Independently corroborated after the fact: RFC-0055
   (Comptime, superseded by RFC-0092), discovered 2026-07-09 via `INDEX.md` after this
   question was already written, reached the same conclusion from its own motivation
   section ("conditional boolean conditions fold cleanly into the generated code with
   no overhead") without knowing this RFC existed. Two independent routes reaching the
   same answer is worth reading as added confidence, not as work needing reconciling.

---

## Timing Recommendation

Pure compiler-hint attributes (`#inline`, `#allow`, `#cfg` as a bespoke directive) need
nothing from the comptime cluster and could ship independently, before v0.5. §2's
attributes-as-comptime-visible-metadata piece is gated on RFC-0092's `typeinfo` and
therefore shares RFC-0092/0093's v0.5+ timeline.

Minimum action before v0.5: reserve `#` as a grammar token so it cannot be used for
other purposes. This prevents a breaking change when the attribute system and comptime
derive land. Unlike the pre-2026-08-23 text this replaces, this is not a claim
resting on an unchecked assumption — `#` is confirmed unclaimed by anything else in the
grammar as of this revision (see §1).

---

## References

- RFC-0092 (Comptime Core) — `typeinfo`'s row-metadata question (Open Question 1),
  which §2's field-attribute reflection need feeds into
- RFC-0093 (Derive Registration) — Open Question 5's derive-configuration fork, which
  §2 raises but does not resolve
- RFC-0094 (Comptime Metaprogramming) — the `emit`-generalization precedent §2's `#cfg`
  question is modeled on
- RFC-0009 (Module System) — visibility and `#cfg` interaction; also field-visibility
  for reflection
- RFC-0026 (Unsafe Blocks) — `#extern` for FFI uses this RFC's attribute syntax
- RFC-0063 (Allocator Handles), RFC-0065 (Allocator Ergonomics) — the `@` sigil's prior
  claim (`2-accepted`), the reason this RFC's own sigil moved to `#`
- Prior art: Rust `#[serde(...)]` sibling-attribute pattern; Java annotations; Python
  decorators; Zig `@builtins`

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+ for §2; pure compiler-hint attributes could ship earlier

*(Decision rationale goes here when the RFC is evaluated.)*
