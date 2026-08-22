---
id: rfc-0111
title: "Unqualified Enum Variants in Expression Position"
date: '2026-07-21'
status: implemented
target:
updated: '2026-07-21'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/572'
impl_status: implemented
coverage:
  "1": { spec: "spec.expressions.unqualified-variant-constructors.legality-1" }
  "1.1": { spec: "spec.types.perhaps-t.legality-1" }
  "1.2": { spec: "spec.expressions.unqualified-variant-constructors.legality-2" }
  "1.3": { spec: "spec.expressions.unqualified-variant-constructors.legality-3" }
  "1.4": { spec: "spec.expressions.unqualified-variant-constructors.legality-4" }
  "2.1": { kind: untestable, reason: "This is rationale for rejecting scope-based glob imports, not a specified language behavior." }
  "2.2": { kind: untestable, reason: "This is rationale for rejecting a reverse-index resolution mechanism, not fixture-observable behavior." }
  "2.3": { kind: untestable, reason: "This is rationale for rejecting leading-dot syntax, not a specified language behavior." }
  "2.4": { kind: untestable, reason: "This is rationale for rejecting the status quo, not a separate behavioral rule." }
  "3": { spec: "spec.expressions.unqualified-variant-constructors.legality-1" }
  "3.1": { spec: "spec.expressions.unqualified-variant-constructors.legality-4" }
  "3.2": { spec: "spec.types.perhaps-t.legality-1" }
  "3.3": { spec: "spec.expressions.unqualified-variant-constructors.legality-1" }
---

> **Status — under review (2026-07-21).** Substantiated proposal with a verified implementation sketch. All three original open questions resolved against the implementation (2026-07-21): no param_hints widening is needed, method args and struct fields already carry hints, Result's Ok/Err falls out free. Dependency on RFC-0112 removed as a consequence.

> **Status — accepted (2026-07-21).** Design settled: type-directed resolution against the expected type, binding wins over variant in expression position (the deliberate asymmetry with RFC-0107), no reverse-index fallback when no expected type exists. Scope import weighed and declined for consistency with RFC-0107. No open questions remain and no RFC dependency.

> **Status — integrated (2026-07-21).** Merged into expressions.md (Unqualified variant constructors) and types.md (Perhaps<T> reframed: None/Some are ordinary variants, not literals). Worked examples cross-checked against RFC-0106/0107/0101/0112; turned up that a unit struct may share a name with a variant, resolved by reading SS1.1's third condition as covering unit-struct constructors -- a bare variant is a last resort, never a shadowing mechanism.

> **Status — implemented (2026-07-21).** Pass 1 defers a bare identifier only when `has_variant_named` says some enum declares it, never using that index to pick an enum; Pass 2 resolves against `expected_ty` at two hooks, both placed after the binding lookup and the struct-literal branch so §1.2's binding-wins and the integrate-stage unit-struct-wins rule hold. `Literal::None` and `none_lit` are gone entirely — zero occurrences remain — and `None`/`Some`/`Ok`/`Err` all route through the general mechanism. 797 tests green, including the 51 existing fixtures using `None`. Fixtures: `evaluator/enums/41_unqualified_variant_constructors.mtl` plus negatives for no-expected-type and unit-struct-wins.

> **Known limitation, inherited not introduced (2026-07-21).** A bare variant inside an *uncalled* closure body is silently accepted: `let f = () -> { Red };` compiles. This is not specific to this RFC — `let f = () -> { [] };` behaves identically and predates it. An uncalled generic closure's body is never constructed, so no Pass 2 resolution runs over it and any deferred-resolution construct escapes. Filed as metel-core#573. §3.1's goal of preserving the `T0003` typo diagnostic is met everywhere else: a name no enum declares still errors in Pass 1, and a bare variant in any reachable position still errors.

## Summary

Allow a bare variant name in expression position — `let c: Colour = Red;`,
`Some { value: 5 }`, `None` — resolved type-directed against the *expected* type at
that position, mirroring RFC-0107's type-directed resolution in pattern position.

The concrete payoff is that `None` stops being a language special case. Today
`Literal::None` is a dedicated AST node with hardcoded `Perhaps` semantics in the
parser, both type-checker passes, and the evaluator; RFC-0107 already retired its
pattern-position twin (`Pattern::None`). This RFC retires the expression-position half,
after which `None` is an ordinary variant of an ordinary enum that happens to be
built in, resolved by the same general mechanism as `Red`.

---

## Motivation

### The remaining special case

RFC-0107 retired `Pattern::None`: a bare `None` in a match arm now resolves through the
general bare-variant mechanism against the scrutinee's enum. Its expression-position
counterpart survives untouched:

- `src/parser/mod.rs` — `Rule::none_lit => Literal::None`
- `src/typechecker/inference.rs:2977` — `Literal::None => InferType::Named("Perhaps", [fresh])`
- `src/typechecker/construction.rs:3914` — `Literal::None => expected_ty.cloned().ok_or(T0002)`
- `src/evaluator/mod.rs:2474` — `Literal::None => Value::Enum { .. }`

So `Perhaps` is privileged in a way no user-defined enum can be. A user writing
`enum Colour { Red, Green, Blue }` must write `Colour::Red` in every expression, while
the builtin `Perhaps` gets `None` for free. That asymmetry is the motivation; the
ergonomic win on user enums is a consequence, not the primary goal.

### The mechanism already exists — it is just wired to one hardcoded name

`construct_expr(expr, expected_ty: Option<&Type>, ctx)` already threads an expected type
through the whole of Pass 2, and `Literal::None`'s arm at `construction.rs:3914` is
already *exactly* the resolution this RFC wants — read the expected type, use it, error
with T0002 if absent. This RFC does not invent an expected-type mechanism. It replaces
a one-variant hardcoded consumer of that mechanism with a general one.

That framing sets the honest scope: the work is in Pass 1, which has no expected type
at all (§3), not in Pass 2, which is nearly ready.

### What this is *not* — a correction to the Rust analogy

This RFC was requested as "follow the same logic as Rust: when the type can be inferred,
the variant name does not have to be fully qualified." Checked rather than assumed:
**Rust does not do this.** In Rust, `let c: Colour = Red;` does not compile, and neither
does `match c { Red => ... }`. Bare `None`/`Some` work in Rust for one reason only —
`std::option::Option::*` is glob-imported by the prelude — and the general mechanism a
user reaches for is `use Colour::*;`, a *lexical scope import*, not type-directed
resolution.

So there are two genuinely different designs available, and the Rust precedent points at
the one this RFC does not choose. §2 weighs them. The short version: Metel already
committed to type-directed resolution in pattern position when RFC-0107 shipped, and
RFC-0107 §1.3 chose it specifically to avoid the cross-enum collision problem that scope
imports have. Doing scope-import in expression position and type-directed in pattern
position would leave the language with two unrelated mechanisms for the same-looking
syntax.

---

## 1. Proposal

### 1.1 Resolution rule

At any expression position with a known expected type `E`:

- if `E` resolves to a known enum, and
- the bare identifier `V` names a variant of `E`, and
- `V` is not bound by any enclosing binding or declaration in scope,

then `V` is that variant — `E::V`. Both the no-field form (`Red`) and the fieldful form
(`Some { value: 5 }`) participate, and per RFC-0106 the empty-brace spelling `Red {}` is
equally valid, since RFC-0106 already makes `Colour::Red` and `Colour::Red {}` equivalent
and this RFC changes only qualification, not brace rules.

```metel
enum Colour { Red, Green, Blue }

let c: Colour = Red;                     // §1.1 — let annotation supplies E
fun favourite() -> Colour { Green }      // return type supplies E
fun paint(c: Colour) { }
paint(Blue);                             // parameter type supplies E (§1.3 caveat)

let p: Perhaps<i64> = Some { value = 5 };
let q: Perhaps<i64> = None;              // `None` via the general mechanism
```

If any of the three conditions fails, nothing changes: the identifier is resolved exactly
as today, producing today's binding lookup or today's `T0003 undefined name`.

### 1.2 A local binding wins — the deliberate asymmetry with RFC-0107

RFC-0107 §1.1 made the *variant* win in pattern position: a bare identifier that names a
no-field variant of the scrutinee's enum is always the variant, never a fresh binding.
This RFC does the opposite — an in-scope binding wins over a variant of the same name:

```metel
enum Colour { Red, Green, Blue }

fun demo(Red: i64) -> i64 {
    return Red;          // the parameter, not Colour::Red
}
```

This is not an inconsistency to be smoothed over. Pattern position *introduces* names, so
"is this a binder or a variant?" is a genuine fork and RFC-0107 had to pick one. Expression
position *uses* names, and a use-site must resolve to the nearest binding or the language
loses lexical scoping — a new enum declared anywhere could silently capture an existing
variable reference. Implementation-wise this falls out for free: the hook point in both
passes sits after the `ctx.lookup(name)` early return.

(RFC-0101's PascalCase-for-types convention makes the collision above unidiomatic anyway,
but this RFC does not depend on that convention holding — it must be correct for code that
violates it, since RFC-0101 is still a draft.)

### 1.3 Which positions have an expected type

RFC-0067a §"type-directed copy" already enumerated the positions where a declared or
expected type is known, and this RFC deliberately inherits that same list rather than
inventing a parallel one — `let`/`var` annotations, `return` (via RFC-0019's
`current_return_ty`), function-call arguments, struct-literal fields, and the arms of an
`if`/`match` resolved against the expression's own expected type.

**Correction, 2026-07-21.** An earlier version of this section claimed *two* gaps. Only one
is real; the other was my error, and it was load-bearing for this RFC's dependencies, so it
is worth stating plainly rather than quietly editing.

- **Generic callees get no hints — real, and inherent.** `param_hints`
  (`construction.rs:2750`) only populates for a monomorphic callee already in scope as
  `Type::Fun`. Generic scheme-based callees need argument types *first* in order to
  instantiate, so no hint can exist before argument construction. Confirmed against the
  implementation: `fun take<T>(p: T)` called as `take(None)` fails with `T0002` today.
  This is a chicken-and-egg property of instantiation, not an oversight to widen away.
- ~~**Method-call arguments get no hints at all.**~~ **False.** The cited
  `construct_expr(arg, None, ctx)` at `construction.rs:1552` is the *array-builtin* branch,
  not the general method path. The general path goes through `construct_method_args`
  (`construction.rs:275`), which skips `params[0]` (the receiver) and threads each remaining
  parameter's declared type as a hint. Verified: a method taking `Perhaps<i64>` accepts a
  bare `None` argument today, which is only possible if the hint reaches it.

Struct-literal fields likewise get hints (`field_hints`), also verified with a bare `None`.

**Consequence: there is no `param_hints` widening for this RFC to do**, and therefore no
sequencing dependency on any other RFC. Every position this RFC needs already carries an
expected type; the single gap is generic callees, which cannot be closed by widening. A
bare variant there does not resolve and the user qualifies (`Colour::Red`) or ascribes
(`Red: Colour`, RFC-0021) — a coverage limit, not an unsoundness, since the feature is
additive where it fires and inert where it does not.

### 1.4 No expected type is an error, not a guess

Where no expected type exists — `let x = Red;` with no annotation, a bare variant into a
generic parameter — this RFC deliberately does **not** fall back to searching for an enum
that declares `Red`. The bare form simply does not resolve, and the user qualifies or
ascribes.

This is the single most important scoping decision in the RFC, and it is what makes the
multi-enum ambiguity problem RFC-0107 §1.4 flagged for expression position *not arise*.
Under a global-uniqueness fallback ("if exactly one enum in the program declares `Red`,
use it"), declaring an unrelated second enum with a `Red` variant in a distant module
would break code that never mentioned either enum. That failure mode — a seemingly
unrelated change silently breaking distant code — is precisely the objection raised
against depth-based allocator elision in RFC-0065's revision, and it should not be
reintroduced here for a smaller feature.

Consequence for error messages: `let x = None;` today produces
`T0002 cannot infer type of \`None\`; add a type annotation`. Under this RFC it must keep
producing an equivalent message rather than degrading to `T0003 undefined name \`None\``.
See §3.2.

---

## 2. Alternatives considered

### 2.1 Scope-based glob import (`use Colour::*`) — the actual Rust design

> **Coverage: untestable** (see frontmatter). Rejected-design rationale only.

Bring an enum's variants into lexical scope explicitly; bare `Red` then resolves by
ordinary name lookup with no expected type needed anywhere. `None` stops being special by
being prelude-imported, exactly as in Rust.

**Genuine advantages, stated fairly.** It is the mechanism the requester named. It works
uniformly in every position — no `param_hints` gap (§1.3), no "no expected type" hole
(§1.4), no Pass 1 problem (§3) at all, because resolution happens during name resolution
where an enum name is already in hand. It is explicit and greppable at the import site.

**Why not chosen.** RFC-0107 already shipped type-directed resolution in pattern position,
having rejected scope import there by name (RFC-0107 §5, Alternatives) for the cross-enum
collision problem: two imported enums both declaring `Red` make bare `Red` ambiguous, and
the resolution rules for that (error? first-wins? shadowing?) are a real design surface
this project does not currently need. Choosing scope import here would mean the same
surface syntax — a bare `Red` — resolves by two unrelated mechanisms depending on whether
it sits left or right of a `=>`, and `use Colour::*` would additionally *not* make
RFC-0107's pattern form redundant, so the language would carry both permanently.

**Not foreclosed.** The two mechanisms are compatible if scope import is ever wanted for
its own sake: import would populate the binding environment, and §1.2's binding-wins rule
already gives a defined interaction with no new ambiguity rules. This RFC declines to
build it, it does not rule it out.

### 2.2 A reverse variant→enum index as the resolution mechanism

> **Coverage: untestable** (see frontmatter). Rejected-design rationale only.

RFC-0107 §1.4 anticipated that expression position "would need exactly that reverse index."
Rejected as a *resolution* mechanism for the reason in §1.4 (action at a distance), but see
§3.1 — the index is still built, in a much weaker role where it never decides which enum a
name belongs to.

### 2.3 Leading-dot syntax (`.red`, Swift-style)

> **Coverage: untestable** (see frontmatter). Rejected-design rationale only.

Swift spells the type-directed form with a leading dot precisely so it is syntactically
marked as "resolve me against the expected type." This would eliminate §1.2's asymmetry
entirely — `.Red` can never collide with a binding — and make the feature's activation
visible at the use site.

Rejected because it does not achieve this RFC's primary goal: `None` would have to be
spelled `.None`, which is a breaking change to every existing use and does not make `None`
an ordinary variant so much as give it a new special spelling. It also does not compose
with RFC-0107, which chose the undotted form for patterns.

### 2.4 Do nothing — keep `Literal::None`

> **Coverage: untestable** (see frontmatter). Rejected-design rationale only.

The status quo works. Rejected: it permanently privileges one builtin enum over every
user-defined one, and RFC-0107 has already paid most of the conceptual cost of the general
mechanism, leaving this as the smaller remaining half of a job already begun.

---

## 3. Implementation sketch

### 3.1 Pass 1 is where the actual work is

Pass 2 (`construction.rs`) threads `expected_ty` already; the change there is
mechanical — extend the `Expr::Ident` arm (`construction.rs:1225`, after the
`ctx.lookup` early return, alongside the existing empty-struct-literal case) and the
`Expr::StructLiteral` arm's `path.len() == 1` branch (the `else` of `construction.rs:1746`) to rewrite a
bare variant into the qualified form before the existing `construct_enum_literal_ty` runs.

Pass 1 (`inference.rs`) is the problem: `infer_expr(expr, ctx, fun_generalizations)` has
**no expected-type parameter at all**. `Literal::None` gets away with
`InferType::Named("Perhaps", [fresh_var])` only because it hardcodes its enum. A bare `Red`
cannot do that.

Three options, and the recommendation is the third:

- **(a) Reverse-index resolution in Pass 1.** Rejected — this is §2.2 / §1.4's action at a
  distance, and it would make Pass 1 and Pass 2 resolve by different rules.
- **(b) Thread expected types through Pass 1.** Principled, and it would want a new
  deferred constraint kind in the solver ("this var must resolve to an enum having a
  variant `Red`"). Materially larger than the rest of this RFC combined; not proposed.
- **(c) Defer in Pass 1, resolve in Pass 2 — recommended.** Pass 1 emits a fresh type var
  for a bare identifier it cannot otherwise resolve, and Pass 2 does the real resolution
  against `expected_ty`. Matches how `Literal::None` already splits its work across the two
  passes.

Option (c) has one hazard that must be handled: blanket-deferring every unresolvable
identifier would destroy Pass 1's `T0003 undefined name` diagnostic, turning every typo
into a fresh var with a worse downstream error. The fix is where the reverse index earns
its place — **build the variant-name→declaring-enum index, but use it only as a gate on
deferral, never to pick an enum.** Pass 1 defers only if some enum somewhere declares a
variant of that name; every other unresolvable identifier errors in Pass 1 exactly as
today. Because the index answers only "could this plausibly be a variant?" and never
"which enum," a second enum declaring `Red` changes nothing about how any existing code
resolves — §1.4's property is preserved.

### 3.2 Retiring `Literal::None`

Once §1 works, all four `Literal::None` sites listed in the Motivation are removable, plus
`Rule::none_lit` in the grammar and the `(Literal::None, Value::Enum { .. })` arm in
`evaluator/pattern.rs`. `none_lit`'s removal was checked directly rather than assumed, the same way RFC-0107 checked
`None`'s keyword status for pattern position. `keyword` (`grammar.pest:337`) does not list
`None`, so `ident` matches it. In `primary_expr` (`grammar.pest:184`) `none_lit` currently sits
above `struct_literal` and `path_expr`; deleting it lets `None` fall through to `path_expr` →
`ident`, which is exactly the general path §1 needs, while `Some { value: 5 }` reaches
`struct_literal` with a one-segment path. No reordering is required.

The T0002 diagnostic must survive the retirement (§1.4). Suggested: when a bare identifier
gates as a possible variant (§3.1) but no expected type is available, emit T0002 with the
"add a type annotation" wording rather than falling through to T0003.

### 3.3 Test surface

Per-form fixtures for each position in §1.3 that does resolve (`let` annotation, `return`,
monomorphic call argument, struct-literal field, `if`/`match` arm), the fieldful form,
RFC-0106's `Red {}` spelling, and §1.2's binding-wins case. Negative fixtures for each
non-resolving position in §1.3/§1.4, asserting the diagnostic is the intended one and not a
degraded `T0003`. Every existing `None` fixture is a regression test for §3.2 and must pass
unchanged.

---

## 4. Unresolved questions

All three questions this RFC opened are now resolved (2026-07-21). None blocks
implementation.

1. ~~**Does the `param_hints` widening belong to this RFC or to RFC-0110?**~~ **Moot.**
   RFC-0110 shipped under the Go model, which dropped the read-copy extensions that would
   have touched `construct_call`'s hint threading — it never went near `param_hints`. And
   per §1.3's correction there is no widening to do at all: method arguments and
   struct-literal fields already carry hints, and the one genuine gap (generic callees) is
   inherent to instantiation rather than closable by widening.

   **This also removes the dependency on RFC-0112.** That RFC's §2 argued the two features
   turn the same knob in opposite directions — RFC-0111 widening hints, RFC-0110 narrowing
   auto-deref — so an origin tag was needed to decouple them. Since this RFC widens nothing,
   the coupling does not arise and RFC-0111 can be implemented while RFC-0112 remains
   parked. RFC-0112 still stands on its own merits; it is simply not a prerequisite here.
2. ~~**Should method-call arguments get hints at all?**~~ **They already do**, via
   `construct_method_args`. The premise was my error — see §1.3. Nothing to decide.
3. ~~**`Result`'s variants.**~~ **Confirmed, falls out for free.** `Result<T, E>` is an
   ordinary `public enum` in `stdlib/core.mtl:86` with no `Literal` special case, and bare
   `Ok`/`Err` already work in *pattern* position through RFC-0107's general mechanism.
   Expression position needs nothing beyond §1.

One case has appeared since this RFC was drafted and is worth stating, though it needs no
decision: **an inference-derived expected type** (RFC-0112 §3's category 6, which came into
existence with metel-core#565 — a closure body is now constructed against its own inferred
return type). Inside `let f = () -> { Red };` there is no authored type for `Red` to resolve
against, so §1.4 applies unchanged and the bare form simply does not resolve. Consistent
with the rest of the design; recorded so it is not rediscovered as a surprise.

---

## Resolved while integrating (2026-07-21)

Worked examples combining this RFC with each sibling that could interact, per PROCESS's
`3-integrated` exit criterion. One turned up a case the design had not considered.

**RFC-0106 (Optional Braces for Empty Constructors, implemented) — no conflict.**
`C::Red {}` and `C::Red` are already equivalent, so the bare forms `Red` and `Red {}` are
too. §1.1 says so; confirmed against the implementation that the qualified empty-brace form
works today, so the bare form inherits it rather than introducing a second rule.

**RFC-0107 (Unqualified Variant Patterns, implemented) — the asymmetry is deliberate and
holds.** Pattern position: variant beats a fresh binding. Expression position: an in-scope
binding beats the variant. Confirmed by example that a parameter named `Red` shadowing an
enum variant `Red` compiles today and returns the parameter — so §1.2's rule preserves
existing behaviour rather than changing it.

**RFC-0101 (Grammar-Enforced Naming, draft) — unaffected either way.** §1.2 must be correct
for code that violates the PascalCase convention, and the shadowing example above does
violate it and still behaves correctly. This RFC does not depend on RFC-0101 landing.

**RFC-0112 (Auto-Deref Scope, draft) — coupling removed, see §4 Q1.** RFC-0112's Motivation
§2 was written on the assumption that this RFC would widen `param_hints`. It will not, so
the two are independent and either may land first.

### The finding: a unit struct may share a name with an enum variant

Not previously considered by this RFC, and legal today:

```metel
struct Red { }
enum C { Red }

fun main() {
    let s = Red;        // resolves to the unit struct — works today
    let c: C = Red;     // T0001: cannot unify Red with C
}
```

`construct_expr`'s `Expr::Ident` arm tries the empty-struct-literal path *before* the point
where §3.1 would hook in bare-variant resolution, so a unit struct wins on name. The second
line is the interesting one: an expected type of `C` does not rescue it.

**Resolution: the unit struct keeps winning, and the rule is stated as a last resort.**
§1.1's third condition ("`V` is not bound by any enclosing binding or declaration in scope")
is hereby read as covering unit-struct constructors as well as bindings — same justification
as §1.2, since a unit-struct constructor is equally a *use* of a name already in scope, and
an expression must resolve to what that name already means. So:

> A bare variant resolves only when the name means nothing else — not a binding, not a
> unit struct. It is a last resort, never a shadowing mechanism.

Chosen over "expected type wins" because that would make the meaning of `Red` depend on
context in a way the reader cannot see locally, which is the same objection §1.4 raises
against a global reverse-index fallback. The cost is that `let c: C = Red;` stays a T0001
in that (rare, and RFC-0101-discouraged) situation; the user writes `C::Red`. Implementation
consequence: §3.1's hook must sit *after* the existing struct-literal branch, not before it,
and the Pass 1 deferral gate must likewise not fire for a name that resolves to a struct.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
