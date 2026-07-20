---
id: rfc-0110
title: "Explicit Dereference Operator"
date: '2026-07-20'
status: draft
target:
---

## Summary

Extend and formally document Metel's existing auto-deref mechanism (RFC-0067a §3/§3a,
RFC-0045), closing its two real read-side coverage gaps — call arguments and binary
operator operands — confirmed directly against the implementation, not assumed.
Separately, reintroduce a general unary `*expr`, removed by RFC-0067a.

**Auto-deref is not one mechanism, and this RFC does not treat it as one.** Field/method
dispatch, RFC-0045's fat-pointer field/index write-through, and §3a's read-copy (now
extended, §1-§2) are all kept exactly as they are — none of them competes with a second
sensible reading of the same syntax, so none of them changes. The one mechanism that
*does* — bare-identifier whole-value write-through, where `p = v` for `p: &mut T`
silently means "mutate the referent" and forecloses `p` ever being repointed to a
different reference — is retired (§4.2) in favor of the same resolution Rust and Go
both already use: bare assignment rebinds, and the explicit `*p = v` this RFC adds is
the one spelling for writing through. Repoint is unlocked as a direct, mechanical
consequence, not a separate feature.

---

## Motivation

### 1. §3a's read-copy fires only at a fixed set of positions — confirmed, not assumed

RFC-0067a §3a (post-implementation, per its 2026-07-11 amendment) fires at: `let`/`mut`
bindings, explicit type ascription, `return`, `break`, and tail-expression position —
because each of those is the one place `maybe_read_copy` (`construction.rs`, ~line
4131) is called from, chosen specifically because each already has a genuine
declared/expected type in hand. The RFC's own text says this is deliberate: "never
fires silently at a plain call site... the argument position has no
declared-type-of-its-own for the rule to compare against."

**That last claim is only half true, checked directly against `construct_call`
(`construction.rs`, line 2639).** For a call to a monomorphic, already-typed callee,
`param_hints` already extracts each parameter's declared type and threads it into
`construct_expr(a, hint.as_ref(), ctx)` for every argument — the expected type
genuinely exists and is already flowing through the exact same code path §3a's other
five call sites use. `maybe_read_copy` simply isn't called afterward there. This makes
the call-argument gap a real oversight, not a fundamental limitation: `f(r)` where
`f(v: i64)` and `r: &i64` fails today with no read-copy, even though the machinery
needed to fix it (a known expected type, `construct_expr` already given it as a hint)
is already sitting right there.

**Generic (scheme-instantiated) callees are the genuine limitation**, confirmed in the
same function: `instantiate_scheme_for_call` needs the arguments' own types *first* to
infer the callee's type-parameter instantiation, so no parameter-type hint exists
before argument construction for that path — the chicken-and-egg problem RFC-0067a's
text was gesturing at, just true for one call shape, not all of them. This RFC extends
read-copy to the monomorphic case (§1 below) and leaves the generic case as-is.

**Binary operator operands have no expected-type position at all, monomorphic or
not — confirmed directly against `construct_binop` (`construction.rs`, line 3861).**
Every arithmetic and ordering-comparison arm calls `.is_numeric()` (or checks
`Type::Str`/`Type::Char`) on the operand's *raw* constructed type with no peeling
first — `Type::Reference`/`Type::MutReference` fails `is_numeric()` outright, so
`*p + *q` for `p, q: &i64` fails at `T0005` before unification is even reached, with no
workaround short of a throwaway `let` per operand. This is a second real gap this RFC
closes directly (§2 below), reusing `peel_type_references` — already defined in this
same file for method/field-receiver resolution — rather than inventing new machinery.

RFC-0108 (Reference-Transparent Match Scrutinees, draft) independently found and named
this same absence while scoping a narrower fix for match scrutinees specifically,
confirming `match *c { .. }` fails as a *parse* error today (`*` only exists as
`mul_op`) and explicitly flagging general `*expr` as "could still be proposed
separately on its own merits; not a prerequisite for or blocker of this RFC." This is
that RFC.

### 2. Write-through is real and shipped, but was never actually written down

The word "write-through" appears exactly three times in RFC-0067a's current text —
all three in amendment blockquotes describing what the *implementation* did, none in
the RFC's actual proposal body (§1-§4). Line 136 (§3, chain-depth guarantee) claims the
chain-depth rule applies "to §3a's read-copy and write-through below," but §3a's own
title is "Reading a value out of a reference" and its full content — checked directly —
never once mentions `Expr::Assign`, an assignment target, or writing. The mechanism
exists and ships (`inference.rs` ~line 2113, `construction.rs` ~line 1420), and — per
this RFC's design decision below — keeps working exactly as it does today. What's
missing is only that the RFC supposed to own it never wrote the rule down. §4 of this
RFC does that: states the rule precisely, as it is actually implemented, in a real
numbered section instead of an amendment aside.

### 3. `*` was the original spelling for exactly this mechanism

`tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl` — the fixture
covering fat-pointer (field/tuple/array-element) write-through — carries this comment
verbatim: *"RFC-0067a: `*T`/`*mut T` renamed to `&T`/`&var T`; explicit `*p` deref
replaced by write-through assignment and type-directed read-copy."* RFC-0045 (Mutable
Address-Of for Lvalue Paths, implemented) — the RFC that actually designed fat-pointer
write-through — specifies it entirely in terms of `*p`/`*p = v`:

```metel
let p: *mut Counter = &mut pair.counter;
p.tick();           // pair.counter updated automatically
```

RFC-0067a's rename traded the explicit spelling for implicit-only inference as a side
effect of unifying `*T`/`&x` notation, not because the explicit spelling was judged
wrong on its own terms. This RFC restores it as an available spelling on top of
RFC-0067a's `&`/`&mut` notation — alongside the implicit mechanism, not instead of it.

---

## 1. Extending read-copy to call arguments (monomorphic callees)

In `construct_call`, after `typed_args` is built from `param_hints`, apply
`maybe_read_copy` per argument wherever a hint exists — the same call `Decl::Let`
already makes, just one more site:

```rust
let typed_args: Vec<TypedExpr> = args
    .iter()
    .zip(param_hints.iter())
    .map(|(a, hint)| {
        let built = construct_expr(a, hint.as_ref(), ctx)?;
        Ok(match hint {
            Some(h) => maybe_read_copy(h, built, a.span()),
            None => built,
        })
    })
    .collect::<Result<_, _>>()?;
```

```metel
fun f(v: i64) { .. }
let r: &i64 = &a;
f(r);          // read-copy now fires — no ascription needed
```

`param_hints` is only populated for monomorphic callees (`Expr::Ident`/`Path`/
`ResolvedPath` resolving to a known `Type::Fun`); the generic/scheme-instantiation path
is unaffected, per Motivation §1 — its own argument types still drive instantiation,
unchanged. A generic call still needs ascription (`f(r: i64)`, already legal today) or
this RFC's explicit `*` (§5) if the parameter's monomorphized type turns out not to be
a reference.

## 2. Extending read-copy to binary operator operands

In `construct_binop`, peel both operands to their base (non-reference) type
immediately after construction, before any operator-specific type check —
`peel_type_references` already exists in this file for exactly this shape of
operation (method/field-receiver resolution, and RFC-0108's match-scrutinee peeling):

```rust
let lhs_built = construct_expr(lhs, None, ctx)?;
let rhs_built = construct_expr(rhs, None, ctx)?;
let lhs_built = maybe_read_copy(peel_type_references(lhs_built.ty()).clone(), lhs_built, span);
let rhs_built = maybe_read_copy(peel_type_references(rhs_built.ty()).clone(), rhs_built, span);
// ...unchanged from here: the existing is_numeric()/Type::Str/Type::Char checks
// now see the peeled type, exactly as if the caller had written the base type directly.
```

```metel
let p: &i64 = &a;
let q: &i64 = &b;
let sum = p + q;     // now typechecks directly — no *, no ascription
```

Applies uniformly to `Add`/`Sub`/`Mul`/`Div`/`Rem`/`Lt`/`Le`/`Gt`/`Ge` — every arm that
already inspects the operand's own type in this function. `Eq`/`Ne`/`And`/`Or` return
`Type::Boolean` unconditionally in this function today (their operand compatibility, if
any, is enforced elsewhere in the pipeline) and are unaffected by this change either
way; not touched by this RFC.

---

## 3. `T0002` becomes reachable for `*`, unchanged otherwise

Adding parser support for `*` (grammar + `parse_unary_expr`, §5 below) makes
`UnaryOp::Deref`'s existing, already-implemented type rule
(`construction.rs` line 4091: `Type::Reference(inner) | Type::MutReference(inner) =>
*inner.clone()`, else `T0002`) reachable from surface syntax for the first time.
`T0002` is an existing, already-reused type-error code (17 call sites across
`construction.rs`/`inference.rs`/`conversions.rs`/`overload.rs` already share it for
distinct messages, the same one-code-per-*class* convention RFC-0036 §4 documents for
`T0012`) — no new code needed; `*5` becomes its first surface-reachable trigger.

---

## 4. Write-through: kept where it's unambiguous, retired where it collides with repoint

Auto-deref is not one mechanism — RFC-0067a and RFC-0045 together ship at least four
distinct ones (field/method dispatch, RFC-0045's fat-pointer field/index write-through,
§3a's read-copy, and bare-identifier whole-value write-through). Only the last of
these is genuinely ambiguous, because it's the only one competing with a second,
equally sensible reading of the exact same syntax. This RFC keeps the first three
exactly as they are and retires only the fourth.

### 4.1 Kept, unchanged: field- and index-path write-through (RFC-0045)

Any assignment whose *target* is a `FieldAccess` or `Index` (`obj.field = v`,
`arr[i] = v`, including when auto-deref is needed to reach `obj`/`arr` through a
reference at the root) goes through `resolve_field_assign_root`, a mechanism entirely
separate from the one this RFC touches. There is no competing "repoint" reading for a
field or index target — `obj.field = v` can only ever mean "write into that field" —
so nothing here changes:

```metel
var q = Point { x: 5, y: 7 };
let qptr: &var Point = &var q;
qptr.y = 99;      // auto-deref field write — unambiguous, unaffected by this RFC
assert(q.y == 99);
```

### 4.2 Retired: bare-identifier whole-value write-through

**This is the one case that collides with repoint, and the one this RFC changes.**
Today, assigning to a plain identifier `p` whose static type is `&mut T` (at any chain
depth) writes through every `&mut` layer to the innermost `T`, unconditionally,
regardless of whether `p` itself is declared `let` or `var` — confirmed directly
against a shipped fixture
(`tests/integration/sources/evaluator/references/08_write_through_reference_chain.mtl`):

```metel
var n = 1;
var p: &var i64 = &var n;
let pp: &var &var i64 = &var p;

pp = 5;        // today: writes n, through both layers
assert(n == 5);
```

Because this rule is unconditional, there is currently no way to *repoint* a
`var`-declared `&mut T` binding — `p = &var m;` is a type error today (the right side
is `&var i64`, not the `i64` write-through expects), even though `p` is `var` and every
*other* type's `var` binding can be reassigned freely. Rust and Go both avoid this
collision entirely by never having implicit write-through in the first place: bare
assignment always rebinds, and `*p = v` is the only spelling for writing through.

**This RFC adopts the same resolution, but only for this one mechanism.** The special
case in `Expr::Assign`'s handling of `AssignTarget::Ident` (`ctx.mark_write_through` in
`inference.rs` ~line 2113, and the corresponding peeling logic in `construction.rs`
~line 1420-1480) is removed. After this RFC:

- `p = v;` for a bare identifier `p` always means *rebind `p`* — legal exactly when `p`
  is declared `var`, the same rule every other type already follows. No special case
  for `&mut T`-typed bindings.
- `*p = v;` (§5) is the spelling for writing through a bare reference identifier.

```metel
var a = 1;
var b = 2;
var p: &mut i64 = &mut a;
p = &mut b;    // repoint — a type error today; legal after this RFC (p is var)
*p = 5;        // write through — b becomes 5, a unchanged
```

§4.1's field/index write-through is untouched by this change — `resolve_field_assign_root`
never shared code with the `AssignTarget::Ident` special case being removed here, so
nothing about it needs to change for this rule to be dropped cleanly.

---

## 5. Grammar and parser: explicit `*`

For reads, an available synonym alongside auto-deref. For bare-identifier
write-through (§4.2), the only spelling, now that the implicit form is retired.

One line, additive, in `grammar.pest`:

```diff
- unary_expr = { ("!" | "-" | "&" ~ mut_kw?) ~ unary_expr | postfix_expr }
+ unary_expr = { ("!" | "-" | "*" | "&" ~ mut_kw?) ~ unary_expr | postfix_expr }
```

No ambiguity with the existing binary `*` (`mul_op`, used only inside `mul_expr`'s own
repetition, which only ever runs *between* two already-parsed operands). `unary_expr`
sits below `mul_expr` in the precedence chain, so a leading `*` is always consumed as
the unary prefix first — the same resolution-by-parse-position RFC-0001 already used
for this exact sigil overload, and that C, Go, and Rust all rely on. Postfix binds
tighter than this prefix, so `*p.field` parses as `*(p.field)`, matching Rust and C.

`parse_unary_expr` (`parser/mod.rs`, line 2037) gets one more dispatch arm:

```rust
} else if text.starts_with('*') {
    Ok(Expr::UnaryOp(UnaryOp::Deref, Box::new(parse_expr(child, filename)?), span))
```

`UnaryOp::Deref` already exists in `ast::UnaryOp` (line 592) and is already fully
handled, unconditionally, by both `construct_unaryop`/`infer_expr`'s `Deref` arms and
the evaluator's (`evaluator/mod.rs` line 2616) — none of that code checks whether the
node came from the parser or was synthesized internally, so **no typechecker or
evaluator change is needed for reads** beyond removing the now-inaccurate comment at
`construction.rs` line 4131 claiming the parser never produces this node.

**Reads**, once this exists, are legal everywhere §1's read-copy reach doesn't
(unchanged) already covers, plus everywhere it does — a visible, unconditionally-legal
alternative spelling:

```metel
let sum = *p + *q;    // equivalent to `p + q` after §2; both legal
f(*r);                // equivalent to `f(r)` after §1 (monomorphic); both legal
g(*r);                // still needed for a *generic* callee `g` — §1 doesn't reach here
```

**Writes** get one new `ast::AssignTarget` variant, mirroring the existing write-through
construction exactly rather than diverging from it:

```rust
// ast/mod.rs
pub enum AssignTarget {
    Ident(String, Span),
    FieldAccess { .. },
    Index { .. },
    Deref(Box<Expr>, Span),   // new
}

// parser/mod.rs, expr_to_assign_target
Expr::UnaryOp(UnaryOp::Deref, operand, span) => Ok(AssignTarget::Deref(operand, span)),
```

```rust
// construction.rs, assign_target_to_typed_place
AssignTarget::Deref(object, span) => {
    let typed_object = construct_expr(object, None, ctx)?;
    match typed_object.ty() {
        Type::MutReference(_) => Ok(TypedPlace::Deref {
            object: Box::new(typed_object),
            span: span.clone(),
        }),
        t => Err(MetelError::type_error(
            TypeErrorCode::T0002,
            format!("cannot write through `{t}`; `&mut T` required"),
            span,
        )),
    }
}
```

For field/index targets (§4.1), `*(obj.field) = v` and `obj.field = v` would likewise
be synonyms — the same harmless redundancy already tolerated elsewhere in this design
(`&mut T` implicitly coercing to `&T` while a narrower explicit annotation achieves the
same thing; §7 below, where `match *c { .. }` and RFC-0108's auto-transparent
`match c { .. }` will coexist the same way). For a **bare identifier** target,
`*p = v` is not redundant with anything after §4.2 — it is the only spelling that
writes through, since bare `p = v` now means repoint.

---

## 6. Interaction with RFC-0044 (Addressability)

`*p` for `p: &mut T` is a new addressable *place* under RFC-0044 §9's existing rule,
the same way `p` itself already was — writing through it or taking `&(*p)` follow the
existing addressability rule unchanged, not a new one. `&*p` (address-of a deref) is a
legal reborrow once both operators exist; Metel has no borrow checker yet (RFC-0071,
accepted, 0% implemented), so `&*p` and `p` alias identically today. Whether `&*p`
should shorten an effective borrow scope once RFC-0071 lands is real but deferred — see
Open Questions.

---

## 7. Interaction with RFC-0108 (Reference-Transparent Match Scrutinees)

Complementary, not overlapping — RFC-0108's own Alternatives Considered section already
drew this line: general `*expr` was "rejected as the primary fix" for match
scrutinees specifically, but explicitly left open to be "proposed separately on its own
merits." This RFC does that, independent of match entirely. Once both ship,
`match *c { .. }` and RFC-0108's auto-transparent `match c { .. }` are both legal and
produce the same result — the same harmless redundancy §5 already describes for
writes. Neither RFC needs the other; sequencing is immaterial between them.

---

## 8. Out of scope

- **Deref *patterns*** (a `*pat` pattern-position sigil). This RFC is expression-level
  only. RFC-0108 already solves the one pattern-position gap that mattered (match
  scrutinees); nothing here proposes matching *through* an explicit `*` in pattern
  position.
- **`Deref`/`DerefMut` as user-overloadable aspects.** `*` in this RFC only ever
  applies to the two built-in reference types, `&T`/`&mut T`, exactly like RFC-0067a's
  own auto-deref. A user-overloadable version is a separate, larger RFC.
- **Allocator pointers (`@a T`).** RFC-0067 §1 already gives `@a T` its own
  "borrow-deref" operator (`&a expr`) — a different mechanism for a different type.
  `construct_unaryop`'s existing match on `Type::Reference`/`Type::MutReference`
  already excludes `@a T`; this RFC doesn't touch that.
- **A dedicated repoint sigil (`:=`) or type-directed repoint dispatch.** Both were
  considered as ways to add repoint *while keeping* bare-identifier write-through
  unconditional (see Alternatives Considered) — superseded once it was clear the
  write-through rule causing the collision could simply be retired instead, which
  resolves repoint as a side effect rather than needing a new mechanism of its own.

---

## Alternatives Considered

- **Keep bare-identifier write-through unconditional and add a distinct repoint
  sigil (`:=`).** `p := &var b;` repoints, `p = v;` stays write-through. Cleanly
  resolves the ambiguity without touching existing behavior at all. Rejected in favor
  of retiring write-through instead, for two reasons: `:=` carries strong, conflicting
  precedent from other languages (Go: declare-a-new-binding; Pascal/Ada: the *ordinary*
  assignment operator, with `=` reserved for equality) that a Metel reader would likely
  misread; and it leaves the underlying inconsistency in place (assignment to a
  `&mut T`-typed binding still behaves unlike assignment to every other type) rather
  than resolving it.
- **Keep bare-identifier write-through unconditional and disambiguate repoint by the
  right-hand side's type instead** (an RHS of type `T` writes through, an RHS of type
  `&mut T` — matching `p`'s own declared type exactly — repoints; generalizes cleanly
  to chains, where each layer of `&mut` is its own "rung"). No new syntax at all, and
  consistent with §3a's own type-directed-copy precedent. Rejected: it makes the
  write-through/repoint distinction *less* visible than either the status quo or `:=`
  — a reader would need to know both `p`'s exact declared type and the right-hand
  side's inferred type to know which of several behaviors an assignment performs,
  which is the same "no hidden behavior" objection this RFC already raises against
  today's unconditional rule (Motivation §2), not a fix for it.
- **Retire implicit write-through in favor of explicit-only `*p = v`, entirely — a
  breaking change across the board.** An earlier draft of this RFC proposed exactly
  this, framed as a general consistency argument against having two spellings for the
  same effect. That framing was too broad: field/index write-through (§4.1) and
  read-copy (§3a) were never actually inconsistent with anything, since neither
  competes with a second reading of the same syntax the way bare-identifier
  write-through does. This RFC keeps that version's *technical* scope — only
  `AssignTarget::Ident`'s special case is removed, exactly as before — but grounds it
  in the narrower, correct reason: this is the one mechanism that's genuinely
  ambiguous, not "implicit mechanisms in general are worse than explicit ones."
- **Add `*` for reads only; leave the call-argument/binop gaps as auto-deref
  limitations, permanently requiring `*` or ascription there.** Rejected — §1/§2 show
  both gaps are closable with infrastructure that already exists (`param_hints`,
  `peel_type_references`) at low cost; leaving them as permanent `*`-required spots
  would make auto-deref's coverage boundary arbitrary (works for `let`, not for `f(x)`)
  rather than principled (works everywhere a real expected type is knowable).

---

## Migration

Sections 1-2 are pure extensions — every call and binary expression that already
typechecks continues to, unchanged, and strictly more now do; no migration cost.
§4.1 (field/index write-through) is untouched; no migration cost.

§4.2 (retiring bare-identifier write-through) has a real, precisely bounded cost:
three fixtures rely on it today — `04_write_through_thin_reference.mtl`,
`08_write_through_reference_chain.mtl`, `14_mut_field_pointer.mtl`. Every
bare-identifier assignment/compound-assignment in those three (`p = 4`, `p += 6`,
`pp = 5`, `pp += 10`, `px = 10`, `px += 5`, `t1 = 999`, `a1 = 42`, `a1 += 8`,
`brx = 20`) needs a `*` prefix added. `14`'s trailing `qptr.y = 99;` is untouched — a
`FieldAccess` target, covered by §4.1, never part of the ambiguity §4.2 resolves. No
repo-wide grep beyond these three fixtures was performed as part of this RFC; a full
sweep across `tests/` and `stdlib/` is implementation-time work, not a design
question, since the rewrite is mechanical (`p = v` → `*p = v`) and grep-and-fix-able.

---

## Open Questions

1. **`&*p` and future borrow-checker interaction.** Once RFC-0071 lands, does `&*p`
   meaningfully shorten a borrow's effective scope relative to using `p` directly, or
   does Metel's (not yet written) borrow-checker design make the distinction moot? Not
   resolved here — a forward pointer, the same deferral pattern RFC-0067a already used
   repeatedly for exclusivity *enforcement* versus notation.
2. **Lint for redundant `*&x` / `*&mut x` / `*(obj.field)` where auto-deref alone
   would already do the same thing.** Harmless, not a type error, worth a style lint
   once Metel has a lint pass. Not blocking, and deliberately not a compiler error —
   §5 is explicit that this redundancy is intended for field/index targets, not a
   defect to warn away by default.
3. **Should `Eq`/`Ne`/`And`/`Or` get the same peeling §2 gives the other operators?**
   Left open because their operand-compatibility checking, if any, wasn't found in
   `construct_binop` itself (§2) — determining where it actually lives (if anywhere)
   and whether it already tolerates references is implementation-time investigation,
   not resolved by this RFC.

---

## References

- RFC-0043 (Regular Pointers, superseded by RFC-0067a) — the original `*p` design;
  §5's addressability rule and its auto-deref-for-field-access precedent were carried
  forward unchanged by RFC-0067a and are unaffected by this RFC.
- RFC-0045 (Mutable Address-Of for Lvalue Paths, implemented) — designed fat-pointer
  field/index write-through, kept entirely unchanged by this RFC (§4.1); originally
  specified in terms of explicit `*p = v`, which §5 of this RFC restores as available
  syntax for it, redundantly with the auto-deref this RFC leaves alone.
- RFC-0067a (Reference Types, implemented) — this RFC extends §3a's read-copy (§1/§2)
  and **amends** the bare-identifier write-through rule its own amendment blockquotes
  named but never gave a numbered section, retiring it in favor of explicit `*p = v`
  (§4.2) — a real behavioral change, not just documentation, unlike §4.1's mechanism.
  §3's auto-deref chain guarantee and RFC-0045's field/index write-through are
  unaffected.
- RFC-0044 (Explicit Receiver Semantics, implemented) — §9 addressability; `*p` is a
  straightforward new addressable place under the existing rule (§6 above).
- RFC-0067 (Lifetime Anchors, accepted) — §1's allocator-pointer borrow-deref (`&a
  expr`) is the analogous but distinct mechanism for `@a T`; unaffected (§8).
- RFC-0071 (Ownership and Move Semantics, accepted, 0% implemented) — the eventual
  home for exclusivity *enforcement*; this RFC only extends/restores notation, same
  posture RFC-0067a itself took.
- RFC-0108 (Reference-Transparent Match Scrutinees, draft) — independently found and
  named the same "no general deref expression" gap while scoping a narrower,
  match-only fix; its own Alternatives Considered section explicitly left general
  `*expr` open to be proposed separately (§7 above).
- `tests/integration/sources/evaluator/references/04_write_through_thin_reference.mtl`,
  `08_write_through_reference_chain.mtl`,
  `tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl` — the fixtures
  confirming §4.2's write-through rule as implemented today, and (§4.1's trailing
  `qptr.y = 99;` in the last) the field-write mechanism this RFC leaves alone;
  migration cost cited in Migration.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
