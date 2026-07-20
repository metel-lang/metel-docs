---
id: rfc-0107
title: "Unqualified Enum Variants in Match Patterns"
date: '2026-07-17'
status: accepted
target:
updated: '2026-07-20'
---

> **Status — under review (2026-07-20).** Thorough draft; sole open question (shadowing lint) has an explicit non-blocking 'ship silent' recommendation. Reviewing with the enum/reference cluster.

> **Status — accepted (2026-07-20).** Design settled; type-directed bare-variant resolution during construction, Pattern::None special case retired. Shadowing lint declined (ship silent, matching Rust).

## Summary

Allow a bare variant name (`Some`, `Red`) in a match arm when it resolves unambiguously
against the scrutinee's known enum type, instead of always requiring the `Enum::`
prefix. Scoped to pattern position only — `match p { Red => ..., Green => ... }`, not
`let c: Colour = Red;` (see "Out of scope").

---

## Motivation

Every enum-variant pattern today requires full qualification, with one pre-existing,
hardcoded exception. `Pattern::None(Span)` is a dedicated AST node special-cased for
exactly `Perhaps::None` (`src/ast/mod.rs`, matched in `src/evaluator/pattern.rs`,
`src/typechecker/construction.rs`'s `pattern_covers_variant`, and elsewhere) — every
existing test fixture already writes `match n { None => -1, Perhaps::Some { value } =>
value }`, never `Perhaps::None`. `None` gets the ergonomic short form; `Some` does not,
and neither does any variant of a user-defined enum:

```metel
enum Colour { Red, Green, Blue }

fun name(c: Colour) -> String {
    match c {
        Colour::Red => "red",
        Colour::Green => "green",
        Colour::Blue => "blue",
    }
}
```

The repetition scales with variant count and is pure noise once the match's scrutinee
type is already known — `c`'s type is `Colour`, so every arm's `Colour::` prefix is
exactly the same, forced, and uninformative. This RFC generalizes the existing
`Perhaps::None` special case into a real language feature covering any enum, rather than
leaving it a one-off exception.

---

## 1. Design

The change is resolved during construction (Pass 2, `src/typechecker/construction.rs`),
not the grammar. A bare pattern identifier's *meaning* (fresh binding vs. a specific
variant tag) depends on the scrutinee's now-known concrete type, which the grammar
cannot see — the same reason `enum_pattern`'s existing `ident ~ "::" ~ ident` form
requires no lexical scope tracking today.

### 1.1 No-field variants (`Red`, `None`) — pure resolution, no grammar change

`bind_pattern = { ident }` already parses `Red` as `Pattern::Binding("Red", span)` —
this doesn't need to change.

**Correction (caught checking this design against the actual call chain, not just
sketched in isolation):** an earlier draft of this section showed the resolution
mutating the pattern node in place through `&mut Pattern`. That doesn't match the real
signatures — `construct_pattern_bindings` takes `pattern: &Pattern` (shared), and its
caller, `construct_match`, builds `TypedMatchArm` via `arm.pattern.clone()` from an
`&MatchExpr` it never owns mutably (construction reads the source AST throughout, it
never mutates it). The resolution has to happen as a **clone-then-rewrite into a new
owned `Pattern`**, produced *before* `TypedMatchArm` is built, not an in-place mutation
through the existing borrow:

```rust
// In construct_match, replacing `pattern: arm.pattern.clone()`:
let pattern = resolve_bare_variants(&arm.pattern, &scrutinee_ty, ctx);
construct_pattern_bindings(&pattern, &scrutinee_ty, ctx)?;
// ... build TypedMatchArm using this `pattern`, not arm.pattern.clone() directly.

fn resolve_bare_variants(pattern: &Pattern, scrutinee_ty: &Type, ctx: &ConstructCtx) -> Pattern {
    if let Pattern::Binding(name, span) = pattern {
        if let Type::Named(enum_name, _) = scrutinee_ty {
            if let Some(info) = ctx.registry.enum_info(enum_name) {
                if let Some(variant) = info.variants.iter().find(|v| &v.name == name) {
                    if variant.fields.is_empty() {
                        return Pattern::EnumVariant {
                            path: vec![enum_name.clone(), name.clone()],
                            fields: vec![],
                            span: span.clone(),
                        };
                    }
                }
            }
        }
    }
    pattern.clone()
}
```

`construct_pattern_bindings` itself stays completely unchanged — it still just binds
names given a pattern and a scrutinee type, exactly as today. The new step is a small
pre-pass producing the pattern `construct_pattern_bindings` (and everything after it)
operates on.

**The design decision this section exists to make, independent of the signature fix
above: resolve bare variants once, into an ordinary fully-qualified `Pattern::EnumVariant`,
at the single point where the scrutinee's type first becomes known, rather than teaching
every downstream consumer about a new ambiguous case.** After resolution,
`is_catch_all_pattern`, `pattern_covers_variant`, `check_match_exhaustiveness` (all in
`construction.rs`), and `src/evaluator/pattern.rs::match_pattern` (which the typed tree
feeds at runtime) see an ordinary, fully-qualified `Pattern::EnumVariant` exactly as if
the user had written `Colour::Red` — **zero changes needed to any of them.** This also
means `Pattern::None`'s existing special case becomes an instance of the general
mechanism rather than a separate hardcoded node once this ships (see §4).

The alternative — leaving `Pattern::Binding` ambiguous and pushing the "is this really a
variant?" check into `is_catch_all_pattern`, `pattern_covers_variant`, and
`match_pattern` separately — was considered and rejected: it means every one of those
(including the runtime evaluator, which only ever sees a `Value`, not the static
scrutinee type, and so has no sound way to resolve the ambiguity itself) would need the
same lookup duplicated, for no benefit over resolving it once during construction.

### 1.2 Fieldful variants (`Some { value }`) — needs one grammar addition

Today, `Some { value }` doesn't parse as a pattern at all: `bind_pattern` is a bare
`ident` with nothing following, and `enum_pattern` requires the `Type ~ "::"` prefix.
This is a genuinely new syntactic form, not a collision with anything that currently
parses successfully, so it can be added as a new alternative without touching
`bind_pattern`:

```
enum_pattern = { ident ~ "::" ~ ident ~ ("{" ident ("," ident)* "}")?   // unchanged
              | ident ~ "{" ident ("," ident)* "}" }                    // new: bare, fieldful
```

The two alternatives are distinguished by the presence of `::`, so there's no PEG
ordering hazard against each other, and neither can be confused with plain
`bind_pattern` (which only matches when there's no trailing `{` at all) — ordinary
catch-all bindings (`x => ...`) are completely unaffected.

This produces `Pattern::EnumVariant { path: vec![name], fields, span }` — a
**one-segment** path, which `path: Vec<String>` already represents without any AST
change. `construct_pattern_bindings`'s existing `Pattern::EnumVariant` arm
(`src/typechecker/construction.rs:2399`) currently destructures unconditionally via
`let [enum_name, variant_name] = path.as_slice() else { return
Err(internal("invalid pattern path")) }` — this becomes the second place needing a
change: when `path` has one element, resolve it against `scrutinee_ty`'s enum the same
way §1.1 does, filling in `enum_name` before proceeding exactly as today. Once resolved,
`path` is rewritten to the full two-segment form for the same reason as §1.1 — every
downstream consumer keeps seeing the fully-qualified shape it already expects.

### 1.3 Resolution is purely type-directed, not scope-based

The candidate enum is *only* the scrutinee's own resolved type — never a general "bring
every enum's variants into lexical scope" mechanism. This sidesteps the scope-collision
problem that a real `import Colour.*`-style bare-variant-import would have (two enums in
scope both declaring `Red`, say) entirely, because there is exactly one enum under
consideration: whatever `scrutinee_ty` already, concretely is. If `scrutinee_ty` isn't a
resolved `Type::Named` pointing at a known enum yet (e.g. inside a generic function
where the scrutinee's type is still an abstract, aspect-bounded type parameter), the
bare identifier falls back to being an ordinary binding, unchanged from today — the sugar
is additive and only ever activates when there's a single, concrete, unambiguous enum to
check against.

### 1.4 `enum_info`'s missing reverse index

`TypeDefinitionRegistry::enum_info(name: &str) -> Option<&EnumInfo>` is keyed forward,
by enum name — exactly what §1.1/§1.2 need, since the scrutinee's enum name is already
known before the variant-name lookup happens. No reverse (variant name → declaring
enum) index is needed for this RFC's mechanism, since resolution is always "does *this
specific* enum have a variant named X," never "which enum(s) somewhere declare a variant
named X." Worth noting only because a bare-variant *expression* (out of scope, §5) would
need exactly that reverse index and would face the real multi-enum ambiguity problem
this RFC's design avoids.

---

## 2. Exhaustiveness

No new logic needed, by construction of §1: because the rewrite in §1.1/§1.2 always
produces an ordinary two-segment `Pattern::EnumVariant` before `check_match_exhaustiveness`
ever runs, `pattern_covers_variant` and `is_catch_all_pattern` require no changes.

**The risk this section exists to flag:** an implementation that skipped the "rewrite
in place" design and instead special-cased `Pattern::Binding` inline inside
`is_catch_all_pattern` (`src/typechecker/construction.rs:2348`) — today the function
unconditionally treats `Pattern::Binding(_, _)` as a catch-all/irrefutable pattern —
would need to duplicate the exact same enum-variant lookup there too, and getting it
wrong (or forgetting it) would silently make `check_match_exhaustiveness` treat a
variant-tag arm as if it covered every case, accepting a genuinely non-exhaustive match.
This is the concrete argument for centralizing the resolution at one rewrite point
(§1.1) rather than distributing an ad hoc check across every consumer.

---

## 3. Ambiguity with shadowing bindings

If a match arm's bare identifier exactly names a no-field variant of the scrutinee's
enum, it is *always* resolved as that variant, never as a fresh binding — there is no
way to write a catch-all arm that happens to share a variant's exact spelling for that
scrutinee type; `_` or a differently-named binding must be used instead. This mirrors a
well-known Rust ergonomic surprise (`bindings_with_variant_name`) rather than avoiding
it, and is called out as an open question below rather than resolved silently.

RFC-0101 (Grammar-Enforced Naming Case Conventions, draft) reduces how often this
actually bites in practice, if both RFCs ship: variants are PascalCase and ordinary
bindings are snake_case, so a bare pattern identifier that happens to be PascalCase is
already, by convention, unlikely to be an intended fresh binding. RFC-0101 §"Unresolved
Questions" item 1 explicitly flags this exact scenario ("worth checking explicitly if
unqualified variant access is ever proposed") — this RFC is that proposal; see the
cross-reference added there. This RFC's mechanism does not *depend* on RFC-0101 (the
type-directed lookup in §1 is the sole authority regardless of naming convention), but
the two are complementary: RFC-0101 makes the shadowing case in this section rarer in
well-cased code, without being required for this RFC's correctness.

---

## 4. `Pattern::None`'s special case becomes redundant

Once this ships, `Pattern::None(Span)` (`src/ast/mod.rs`) — hardcoded to recognize bare
`None` as specifically `Perhaps::None` — is subsumed by the general mechanism: a bare
`None` in a match arm over a `Perhaps<T>` scrutinee resolves via the same §1.1 path any
other no-field variant does. Removing the dedicated AST node, its grammar production,
and its three-or-more call sites (`src/evaluator/pattern.rs`, `construction.rs`'s
`pattern_covers_variant` and `is_catch_all_pattern`, `Literal::None`'s pattern-context
handling) is in scope for this RFC's implementation, not deferred — the whole point is
that `None` stops being a special case. `Literal::None` (the *expression*-position
value) is unaffected; only the pattern-position AST node is retired.

---

## 5. Out of scope

**Bare variant names in expression position** (`let c: Colour = Red;`, mirroring
`Colour::Red`) is a related but separate question, deliberately not addressed here.
Unlike a match pattern, an arbitrary expression's "expected type" isn't always
available at the point a bare identifier needs resolving (e.g. `println(Red)` — nothing
to check `Red` against), so the multi-enum-ambiguity problem §1.3 sidesteps for patterns
resurfaces for expressions and needs its own design (most likely a real reverse
variant→enum index, §1.4). Left for a follow-up RFC if wanted.

**`use Enum::*`-style explicit glob imports of variants into lexical scope** is a
different mechanism (scope-based, not type-directed) with the multi-enum collision
problem this RFC avoids by design — not proposed here.

---

## Alternatives considered

- **Teach `is_catch_all_pattern`/`pattern_covers_variant`/`match_pattern` about the
  ambiguity separately, instead of rewriting the pattern once during construction.**
  Rejected (§1.1, §2) — duplicates the same lookup three-plus times, and the runtime
  evaluator has no sound, type-directed way to do it at all on its own.
- **General lexical scope import of variants** (`use Colour::*`). Rejected for this RFC
  (§5) — reintroduces exactly the cross-enum name-collision problem the type-directed
  design in §1.3 was chosen specifically to avoid.
- **Extend to expression position in the same RFC.** Rejected (§5) — expression position
  lacks a scrutinee to resolve against in the general case; folding it in here would
  force designing the harder reverse-index problem before the pattern-only feature (which
  needs none of it) ships.

---

## Resolved while drafting

**Worked example: matching on a reference-typed scrutinee.** Checked directly against
the built interpreter whether `fun name(c: &Colour) -> String { match c { Colour::Red
=> ..., ... } }` — the *existing*, fully-qualified form — already works today, since
if it didn't, this RFC's bare form would need to independently decide whether to fix or
inherit that gap. It doesn't: `match c { Colour::Red => "red", ... }` on a `c: &Colour`
fails today with `T0001 cannot unify &Colour with Colour`, before pattern construction
is even reached. This is a pre-existing, general limitation of match scrutinees, not
something this RFC introduces or needs to solve — §1's resolution logic runs on
whatever `scrutinee_ty` construction already produces, so it inherits exactly this
existing behavior (works on `Colour`, fails the same way on `&Colour`) with no
divergence between the qualified and bare forms.

**Update 2026-07-17:** this gap is now proposed separately as **RFC-0108**
(Reference-Transparent Match Scrutinees, draft) rather than folded in here — it's a
general match-scrutinee limitation, not specific to bare variants, so it's this RFC's
sibling, not its own scope. RFC-0108 §2 notes the sequencing interaction explicitly:
its peel needs to run before this RFC's `Type::Named` check for both to compose
correctly on a reference-typed scrutinee.

Two of this RFC's original open questions turned out to be settleable directly against
the current codebase rather than genuinely open, so they're recorded here as decisions,
not questions:

- **Interaction with RFC-0106 — moot, not a design choice.** Re-read RFC-0106's actual
  Decision section rather than relying on a paraphrase: it is scoped *exclusively* to
  construction/expression position (`Type::Variant` vs `Type::Variant {}` when
  *building* a value) — its own text says so explicitly ("Non-empty constructors are
  unchanged" is about construction throughout; pattern position is never mentioned).
  `enum_pattern`'s grammar today has no empty-brace qualified *pattern* form at all
  (`Colour::Red {}` as a match arm doesn't parse), so there is no existing "both
  spellings" convention in pattern position for this RFC to match. §1.1's bare,
  brace-free form (`Red`) is therefore the sole and correctly-scoped pattern spelling —
  nothing to reconcile.
- **`Pattern::None` removal is purely additive, not breaking.** Confirmed directly: the
  qualified grammar production (`ident ~ "::" ~ ident ~ ...`) and the bare-identifier
  path (§1.1) are both unchanged by §4's removal — `Perhaps::None` keeps parsing exactly
  as before, and bare `None` keeps working via the general mechanism instead of the
  dedicated node. No spelling a user could write today stops working; only the internal
  representation (one dedicated AST node vs. one general rewrite) changes. No version
  gate needed.

## Open Questions

1. **Shadowing ergonomics (§3).** Should writing a bare identifier that exactly matches
   a no-field variant name, when a fresh binding was actually intended, produce a lint
   or warning (mirroring Rust's `bindings_with_variant_name`)? **Recommendation: no —
   ship silent, matching Rust's own actual default.** Grep confirms Metel has *no*
   warning/lint mechanism anywhere in the interpreter today (only hard `MetelError`
   type errors) — introducing the entire diagnostic-severity category of "warning,
   not error" for this one narrow case would be disproportionate scope for this RFC.
   If a general warning mechanism is ever added (RFC-0005, "Warn on unreachable match
   arms," is an empty stub gesturing at the same gap), this specific lint can be layered
   on then without being a prerequisite now. Left open only in the sense that it's a
   judgment call about scope, not a technical unknown — flagging the recommendation
   explicitly rather than silently deciding it.

---

## References

- `src/ast/mod.rs` — `Pattern` enum, `Pattern::EnumVariant { path: Vec<String>, .. }`,
  `Pattern::None(Span)`.
- `src/grammar.pest` — `pattern`, `enum_pattern`, `bind_pattern` rules.
- `src/typechecker/construction.rs` — `construct_pattern_bindings`,
  `check_match_exhaustiveness`, `is_catch_all_pattern`, `pattern_covers_variant`.
- `src/evaluator/pattern.rs` — `match_pattern`, the runtime counterpart.
- `src/typeinference/mod.rs` — `EnumInfo`, `TypeDefinitionRegistry::enum_info`.
- RFC-0101 (Grammar-Enforced Naming Case Conventions, draft) — Unresolved Question 1
  anticipates this exact proposal; see §3 above.
- RFC-0106 (Optional Braces for Empty Constructors, implemented) — the other recent
  enum-variant ergonomics RFC; scoped to construction only, doesn't touch pattern
  position at all (see "Resolved while drafting").
- RFC-0100 (Constructor-Call Construction, under review) §4 — a related but orthogonal
  axis (destructuring *shape*, `{ field }` vs. call-parens) explicitly kept unchanged by
  that RFC; this RFC only touches *qualification*, not shape.
- RFC-0099 (Dot-Separated Module Paths, under review) — proposes `::` → `.` for
  qualified enum-variant paths among other things; orthogonal to this RFC (separator
  choice vs. whether qualification is required at all) and not yet landed, so this RFC's
  examples use the current `::` form. If RFC-0099 ships first, the rewritten,
  fully-qualified pattern this RFC's §1.1/§1.2 produces just uses whatever separator is
  then current — a mechanical detail, not a design conflict.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
