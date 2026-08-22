---
id: rfc-0108
title: "Reference-Transparent Match Scrutinees"
date: '2026-07-17'
status: implemented
target:
updated: '2026-07-21'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/559'
impl_status: implemented
coverage:
  "1": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.legality-1" }
  "1.1": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.legality-2" }
  "1.2": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.legality-3" }
  "1.3": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.dynamics-1" }
  "1.4": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.dynamics-2" }
  "2": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.legality-4" }
  "3": { spec: "spec.expressions.pattern-matching.matching-through-a-reference.legality-5" }
---

> **Status — under review (2026-07-20).** Thorough draft with resolved worked examples; open questions (exhaustiveness wording, 0107 sequencing) are non-blocking recommendations. Reviewing as part of the enum/reference cluster (0107/0108/0110).

> **Status — accepted (2026-07-20).** Design settled; peel-references-before-pattern-resolution using existing helpers, no open questions block it. Sequencing with RFC-0107 noted (peel before variant resolution).

> **Status — integrated (2026-07-20).** Merged into expressions.md (Matching through a reference) with a cross-check example composing with RFC-0107's bare-variant resolution; peel runs before variant resolution.

> **Status — implemented (2026-07-21).** Scrutinee references are peeled at type-check time (`peel_all_references` / `peel_type_references`) and at run time (`deref_value`), before RFC-0107 variant resolution. Fixture: `evaluator/references/10_match_through_reference.mtl`.

## Summary

Allow matching a `&T`/`&var T` scrutinee directly against `T`'s ordinary patterns —
peeling reference layers before pattern resolution, the same way field access and
method dispatch already do (RFC-0067a) — instead of failing outright with no
workaround available.

---

## Motivation

Confirmed directly against the built interpreter, not assumed:

```metel
enum Colour { Red, Green, Blue }

fun name(c: &Colour) -> String {
    match c {
        Colour::Red => "red",
        Colour::Green => "green",
        Colour::Blue => "blue",
    }
}
```

fails with `T0001 cannot unify &Colour with Colour`. The same failure reproduces
identically for a plain local binding (`let r: &Colour = &c; match r { ... }`), so
it isn't specific to function parameters.

**There is no workaround.** Metel has no general explicit-deref expression — `*` only
exists as the multiplication operator in the grammar (`mul_op`), not as a unary prefix
anywhere `match *c { ... }` could parse. Confirmed directly: `match *c { ... }` fails
with a *parse* error (`expected assign_expr`), not a type error — the deref-then-match
idiom Rust programmers would reach for doesn't exist as syntax at all. A caller holding
a `&Colour` has no way to pattern-match it, full stop, short of changing the function's
signature to take `Colour` by value instead — which isn't always possible or desirable
(e.g. a shared helper that also needs to work on borrowed data).

**This isn't a wholly novel ask — two other contexts already give you exactly this
transparency, via their own separate, narrower mechanisms, which is part of what makes
its absence here feel like an oversight rather than a deliberate design choice:**

- **`self` inside any method body already resolves to the bare type, regardless of
  receiver kind.** `construct_impl_method`'s `self_ty` (`src/typechecker/construction.rs`)
  is unconditionally `Type::Named(target_name, ..)` (or the primitive equivalent) —
  never wrapped in `Reference`/`MutReference` — so `fun name(&self) -> String { match
  self { Colour::Red => ..., .. } }` already works today, confirmed directly. The
  receiver's `&`/`&var`/by-value-ness is tracked separately (`ReceiverKind`, for
  mutability/borrow bookkeeping), completely independent of what type `self` is bound
  to for matching purposes.
- **`for (item in &collection)` loop variables are already bound by the element's bare
  type**, not a reference to it — confirmed directly with `for (c in &self.colours) {
  match c { Colour::Red => ..., .. } }` inside a `&self` method, which works today.
  `ForIn`'s element-type derivation (`src/typechecker/construction.rs`,
  `src/typechecker/inference.rs`) extracts the array's element type structurally
  (`Type::Array(elem) => *elem.clone()`) regardless of whether the array expression
  itself was reached through a reference.

So the *only* place reference-transparency is missing is the plain case: an ordinary
`let`-bound or parameter-bound variable whose own declared type is `&T`/`&var T`. This
RFC regularizes that gap using the same principle (and, largely, the same existing
helper functions) already used for the two contexts above and for RFC-0067a's field
access / method dispatch auto-deref chain.

---

## 1. Design

### 1.1 Type inference (Pass 1, `infer_match` — `src/typechecker/inference.rs`)

```rust
fn infer_match(m: &MatchExpr, ctx: &mut InferContext, ..) -> Result<InferType, MetelError> {
    let scrutinee_ty = peel_all_references(&infer_expr(&m.scrutinee, ctx, ..)?);
    // ...unchanged from here — infer_pattern already receives scrutinee_ty by value.
}
```

`peel_all_references` (`inference.rs`) already exists, already recurses through
arbitrary nesting (`&&T`, `&var &T`, ...), and is already used for exactly this purpose
at method-call receiver resolution. One call, at the single point `scrutinee_ty` is
first obtained; every pattern kind (`Literal`, `EnumVariant`, `Tuple`, `Array`, ...)
already receives `scrutinee_ty` by value from there, so none of `infer_pattern`'s
existing match arms need to change.

Note: `infer_expr`'s result at this point may still contain unresolved `TypeVar`s
depending on solve order — `peel_all_references` only peels the *shape* it can already
see (`InferType::Reference`/`MutReference` constructors), which is exactly the same
partial-information constraint `peel_all_references`'s existing method-dispatch caller
already lives with today. Not a new limitation this RFC introduces.

### 1.2 Construction (Pass 2, `construct_match` — `src/typechecker/construction.rs`)

```rust
fn construct_match(m: &MatchExpr, expected_ty: Option<&Type>, ctx: &mut ConstructCtx) -> Result<TypedExpr, MetelError> {
    let scrutinee = construct_expr(&m.scrutinee, None, ctx)?;
    let scrutinee_ty = peel_type_references(scrutinee.ty()).clone();
    // ...unchanged from here.
}
```

Same principle, using construction's own existing `peel_type_references` (already used
for method-call/field-access receivers there too). Because `check_match_exhaustiveness`
and `construct_pattern_bindings` both receive `scrutinee_ty` from this single point
(§1's own earlier design already established this data flow), peeling once here covers
exhaustiveness checking for free — no separate change needed there.

**Important: `scrutinee.ty()` itself — the typed scrutinee *expression*'s own recorded
type — is untouched.** Only the local copy used for pattern resolution is peeled. The
overall match expression's typing (its own result type, computed from arm bodies) is
unaffected.

### 1.3 Runtime (`TypedExpr::Match` — `src/evaluator/mod.rs`)

```rust
TypedExpr::Match(m) => {
    let scrutinee_raw = eval_expr(&m.scrutinee, env, runtime)?.into_value();
    let scrutinee = deref_value(&scrutinee_raw, &m.span)?.unwrap_or(scrutinee_raw);
    for arm in &m.arms {
        // ...unchanged: pattern::match_pattern(&arm.pattern, &scrutinee, ..)
    }
}
```

`deref_value` (`evaluator/mod.rs`) already exists, already fully unwraps
`Value::Reference`/`Value::MutReference`/`Value::MutFieldReference` to arbitrary depth,
and is already used at exactly this point in `eval_method_call_expr` for receiver
dispatch. `match_pattern` (`src/evaluator/pattern.rs`) itself needs no changes — it
already just matches a plain `Value` against a `Pattern`; it never sees a reference-
wrapped value once this runs.

### 1.4 Bindings copy the (peeled) value — no new binding-mode machinery

A pattern like `Colour::Red` introduces no bindings, so §1.1-1.3 alone fully cover
this RFC's motivating example. For a fieldful variant matched through a reference
(`match r { Perhaps::Some { value } => .. }` where `r: &Perhaps<i64>`), `value` binds
to a *copy* of the field — the same "type-directed copy" semantics RFC-0066 §3a /
RFC-0067a already established for reading a field through a reference generally, not a
new rule invented here. Metel has no move/borrow-checking yet (RFC-0071 is accepted,
0% implemented per the current roadmap), so there is no Rust-style question of whether
a binding should become a `ref`/`ref mut` binding to avoid an illegal move — every
binding in Metel is already a value-semantics copy today (deep-clone-on-bind), and this
RFC doesn't change that convention, only extends *which scrutinee types* can reach a
pattern at all.

---

## 2. Interaction with RFC-0107 (Unqualified Enum Variants in Match Patterns)

RFC-0107's own resolution logic (§1.1 there: `if let Type::Named(enum_name, _) =
scrutinee_ty`) needs to run against the *peeled* scrutinee type this RFC produces, not
a raw `Type::Reference(Named(..))` — otherwise a bare variant pattern matched through a
reference (`fun name(c: &Colour) -> String { match c { Red => .., .. } }`) would fail
the same way the qualified form does today, defeating the point of shipping both. This
is a sequencing note, not a conflict: whichever RFC lands second should peel before (or
reuse) the other's scrutinee-type handling. Recommend landing this RFC first, since
RFC-0107's design already centralizes scrutinee-type handling at one point per pass —
threading the peel through there is a small, localized change either way.

---

## 3. Scope boundary — not general auto-deref

This RFC only widens what a *match scrutinee* accepts. It does not add a general
unary deref expression, does not change what `let`/function-parameter type annotations
mean, and does not touch non-match contexts. A value typed `&Colour` is still `&Colour`
everywhere else — assigning it, passing it, returning it are all unaffected. Only the
specific position "the expression being matched" gains the same transparency `self` and
`for`-loop element bindings already quietly have.

---

## Alternatives considered

- **Add a general unary deref expression (`*expr`) instead**, and let users write
  `match *c { .. }` explicitly. Rejected as the primary fix: it's a materially bigger
  grammar/semantics change (a new general expression form, with its own type-checking
  and — eventually, once RFC-0071 ships — move/ownership implications) to solve a
  problem RFC-0067a's existing auto-deref-chain principle already covers for every
  *other* read-through-a-reference context. Could still be proposed separately on its
  own merits; not a prerequisite for or blocker of this RFC.
- **Leave it as manual signature adjustment** (change `&T` parameters to `T` when a
  match is needed). Rejected as the status quo, not a fix — documented in Motivation as
  the reason this is worth doing, not an acceptable alternative.

---

## Open Questions

1. **Exhaustiveness diagnostics wording.** Once this ships, an error like
   "non-exhaustive match" fires for the *peeled* type (`Colour`, not `&Colour`) even
   though the scrutinee expression's own type is `&Colour`. Worth confirming the error
   message reads sensibly either way — likely fine unchanged, since the message doesn't
   currently name the scrutinee's type at all (`src/typechecker/construction.rs`'s
   `check_match_exhaustiveness` message is generic), but flagged rather than assumed.
2. **Sequencing against RFC-0107** (§2) — which lands first, if both are accepted.
   Recommendation given, not mandated.

---

## References

- `src/typechecker/inference.rs` — `infer_match`, `infer_pattern`,
  `peel_all_references` (already exists, already used for method dispatch).
- `src/typechecker/construction.rs` — `construct_match`, `construct_pattern_bindings`,
  `check_match_exhaustiveness`, `peel_type_references` (already exists, already used
  for method/field receivers), `construct_impl_method`'s `self_ty` (the existing
  `self`-specific precedent for this transparency).
- `src/evaluator/mod.rs` — `TypedExpr::Match` handling, `deref_value` (already exists,
  already used in `eval_method_call_expr`).
- `src/evaluator/pattern.rs` — `match_pattern`, unchanged by this RFC.
- RFC-0067a (Reference Types, implemented) — establishes the auto-deref-chain
  principle for field access and method dispatch this RFC extends to match scrutinees.
- RFC-0066 §3a (Allocated Value Extraction, accepted) — "type-directed copy," the
  existing convention §1.4 relies on rather than reinvents.
- RFC-0107 (Unqualified Enum Variants in Match Patterns) — see §2 for the
  sequencing interaction.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
