---
id: rfc-0110
title: "Explicit Dereference Operator"
date: '2026-07-20'
status: draft
target:
---

## Summary

Reintroduce a general unary dereference operator, `*expr`, for `&T` / `&mut T` values.
RFC-0067a removed the explicit `*p` that RFC-0043/RFC-0045 originally specified,
betting entirely on auto-deref (field access, method dispatch, reference coercion) plus
a narrower "type-directed copy" mechanism (§3a) for the remaining read case. That bet
left two real gaps, both confirmed directly against the current implementation, not
assumed: §3a's copy only fires at a short enumerated list of positions that have a
declared/expected type in hand, not at arbitrary subexpressions or call arguments; and
*writing* through a reference today happens via an implicit, undocumented inference
rule — the parser can't produce a node for it, so a plain `p = value;` silently decides
between "write through the reference" and "rebind `p`" based on `p`'s static type alone,
with no way to ask for the other one. This RFC adds `*` back as the explicit spelling
for both, and — because an explicit spelling now exists — retires the implicit
write-through inference rather than keeping two mechanisms that do the same thing.

---

## Motivation

### 1. §3a's read-copy fires only at a fixed set of positions — confirmed, not assumed

RFC-0067a §3a (post-implementation, per its 2026-07-11 amendment) fires at: `let`/`mut`
bindings, explicit type ascription, `return`, `break`, and tail-expression position —
because each of those is the one place `maybe_read_copy` (`construction.rs`, ~line
4131) is called from, and each call site is chosen specifically because it has a
genuine declared/expected type to compare against. The RFC's own text is explicit that
this is deliberate, not an oversight: "never fires silently at a plain call site... the
argument position has no declared-type-of-its-own for the rule to compare against."

That leaves two classes of expression with no read path at all today:

- **Call arguments**, exactly as §3a's own text predicts: `fun f(v: i64) {}` called as
  `f(r)` where `r: &i64` is a type error, with §3a's own documented workaround being
  ascription at the call site (`f(r: i64)`) — verbose, and easy to forget since nothing
  about `f`'s signature hints that a reference argument needs it.
- **Binary operator operands.** Confirmed directly: `infer_binop` (`inference.rs`,
  line 2957) unifies `lhs_ty`/`rhs_ty` against each other and, for arithmetic, a fresh
  result variable — there is no `peel_all_references` call anywhere in it, unlike
  `Expr::Index`'s object type (line ~2071) or method-receiver resolution, both of which
  do peel. `p + q` for `p, q: &i64` has no expected-type position for either operand to
  compare against, so it isn't just missing an ergonomic shortcut — there is no
  workaround at all, ascription included, short of introducing a throwaway `let` for
  each operand first.

RFC-0108 (Reference-Transparent Match Scrutinees, draft) independently found and named
this same absence while scoping a narrower fix for match scrutinees specifically,
confirming `match *c { .. }` fails as a *parse* error today (`*` only exists as
`mul_op`) and explicitly flagging general `*expr` as "could still be proposed
separately on its own merits; not a prerequisite for or blocker of this RFC." This is
that RFC.

### 2. Write-through is real, shipped, and undocumented in RFC-0067a's own numbered sections

The word "write-through" appears exactly three times in RFC-0067a's current text —
all three in amendment blockquotes describing what the *implementation* did, none in
the RFC's actual proposal body (§1-§4). Line 136 (§3, chain-depth guarantee) claims the
rule applies "to §3a's read-copy and write-through below," but §3a's own title is
"Reading a value out of a reference" and its full content — checked directly — never
once mentions `Expr::Assign`, an assignment target, or writing. The mechanism exists
and ships (`inference.rs` ~line 2113, `construction.rs` ~line 1420), but the RFC that's
supposed to specify it never actually wrote the rule down; the implementation filled
the gap silently. Confirmed by reading the rule as shipped:

```rust
// inference.rs, Expr::Assign / AssignTarget::Ident
match ctx.lookup_mono_raw(name) {
    Some(InferType::MutReference(inner)) => {
        ctx.mark_write_through(span.clone());
        // ... peels every &mut layer, unconditionally
    }
    _ => ctx.lookup_for_write(name, target_span)?,
}
```

Any identifier whose *static type* is `&mut T` (or `&mut &mut T`, peeled to arbitrary
depth) writes through on plain assignment — **regardless of whether the binding itself
is `let` or `var`.** The comment justifying this in the source is explicit about why no
alternative was considered: "no fixture in this corpus ever reassigns a reference
binding to a *different* reference, so there is no competing repoint interpretation to
preserve here." That is a description of the test corpus at the time the rule was
written, not a principled argument — and it has a direct, checkable consequence: **there
is currently no way to repoint a `var`-declared `&mut T` binding to a different
reference.** `var p: &mut i64 = &mut a; p = &mut b;` does not compile today — the
left-hand `p = ...` is interpreted as a write-through target expecting an `i64` value,
and `&mut b` is a `&mut i64`, a type mismatch.

This is also, concretely, a hidden-behavior gap the project has already rejected
elsewhere on principle. RFC-0060 §7 rejects last-impl-wins semantics because
"order-dependent semantics are a footgun and contradict Metel's design preference for
no hidden behaviour"; RFC-0001 rejected Go-style auto-deref field access for the same
reason ("Metel's design principle of *no implicit conversions* rules this out"). The
current write-through rule is exactly this kind of hidden behavior: `pp = 5;` for
`pp: &mut &mut i64` silently writes through *two* layers of indirection with nothing in
the source text indicating it, confirmed directly against a real shipped fixture
(`tests/integration/sources/evaluator/references/08_write_through_reference_chain.mtl`):

```metel
var n = 1;
var p: &var i64 = &var n;
let pp: &var &var i64 = &var p;

pp = 5;        // writes n, not p — nothing at this line says so
assert(n == 5);
```

### 3. This is not a new mechanism — it's the one RFC-0045/RFC-0043 originally specified

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

`*p = v` was the original, explicit design for exactly this write path. RFC-0067a's
rename traded it for implicit inference as a side effect of unifying `*T`/`&x` notation
— not because the explicit spelling was judged wrong on its own terms, and not as a
decision RFC-0067a's own text actually argues for anywhere. This RFC restores the
explicit spelling RFC-0045 designed for, on top of RFC-0067a's `&`/`&mut` notation
rather than RFC-0043's `*T`/`&x` asymmetry it replaced.

---

## 1. Grammar

One line, additive, in `grammar.pest`:

```diff
- unary_expr = { ("!" | "-" | "&" ~ mut_kw?) ~ unary_expr | postfix_expr }
+ unary_expr = { ("!" | "-" | "*" | "&" ~ mut_kw?) ~ unary_expr | postfix_expr }
```

No ambiguity with the existing binary `*` (`mul_op`, used only inside `mul_expr`'s
`(mul_op ~ cast_expr)*` repetition, which only ever runs *between* two already-parsed
operands). `unary_expr` sits below `mul_expr` in the precedence chain (`mul_expr =
{ cast_expr ~ (mul_op ~ cast_expr)* }`, and `cast_expr` bottoms out through `asc_expr`
into `unary_expr`), so a leading `*` is always consumed as the unary prefix before
`mul_expr`'s own alternation ever gets a chance to see it as an operator — the same
resolution-by-parse-position RFC-0001 already used for this exact sigil overload, and
that C, Go, and Rust all rely on. Postfix binds tighter than this prefix (`unary_expr`
recurses into `postfix_expr`, not the other way around), so `*p.field` parses as
`*(p.field)`, matching Rust and C.

---

## 2. Parser

`parse_unary_expr` (`parser/mod.rs`, line 2037) already dispatches on `pair.as_str()`'s
leading token for `!`, `&mut`, `&`, `-`, falling through to the bare operand otherwise.
One more arm:

```rust
} else if text.starts_with('*') {
    Ok(Expr::UnaryOp(
        UnaryOp::Deref,
        Box::new(parse_expr(child, filename)?),
        span,
    ))
```

`UnaryOp::Deref` already exists in `ast::UnaryOp` (`ast/mod.rs`, line 592) — it has
never had a variant added or removed since RFC-0043; RFC-0067a only stopped the parser
from ever constructing it, using it exclusively as an internal node the typechecker
synthesizes (`maybe_read_copy`, the write-through peeling loop in `construction.rs`
~line 1462). No AST enum changes needed for reads.

**Write targets need one new `AssignTarget` variant.** The grammar's assignment LHS is
parsed as an ordinary `unary_expr` (`assign_expr = { unary_expr ~ assign_op ~
assign_expr | or_expr }`) and then narrowed by `expr_to_assign_target` (`parser/mod.rs`,
line 2460), which today matches `Expr::Ident` / `Expr::FieldAccess` / `Expr::Index` and
rejects everything else with an internal error — reachable only in principle today,
since the parser could never produce an `Expr::UnaryOp(Deref, ..)` for it to reject.
Add:

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

---

## 3. Reads: already fully implemented, only unreachable

`construct_unaryop`'s `UnaryOp::Deref` arm (`construction.rs`, line 4091) and
`infer_expr`'s (`inference.rs`, line 3115) are both unconditional — they pattern-match
on the operand's type (`Type::Reference(inner) | Type::MutReference(inner) =>
*inner.clone()`, else `T0002`) with no check for whether the node came from the parser
or was synthesized internally. The evaluator side is the same:
`(UnaryOp::Deref, Value::Reference(rc) | Value::MutReference(rc))` (`evaluator/mod.rs`,
line 2616) and the `MutFieldReference` case immediately after it — both already handle
an arbitrary `Deref` node regardless of origin. **No typechecker or evaluator change is
needed for reads** — only the parser change in §2, plus removing the now-inaccurate
comment at `construction.rs` line 4131 ("the parser never produces `UnaryOp::Deref` any
more") since after this RFC it will.

This closes both gaps in Motivation §1 directly, with no new mechanism:

```metel
let p: &i64 = &a;
let q: &i64 = &b;
let sum = *p + *q;         // binary operator operand — no workaround existed before

fun f(v: i64) { .. }
f(*p);                     // call argument — §3a's own documented non-coverage
```

`T0002` ("cannot dereference non-pointer type") is an existing, already-reused type-
error code (confirmed: 17 call sites across `construction.rs`/`inference.rs`/
`conversions.rs`/`overload.rs` already share it for distinct messages, matching the
established convention of one code per *error class*, not per message — the same
convention RFC-0036 §4 already documents for `T0012`). `*5` — deref of a non-reference
— becomes the first surface-syntax-reachable trigger of this particular `T0002`
message; no new code needed.

Chain depth is unchanged from the existing internal mechanism: `**pp` for `pp: &&i64`
parses as `Expr::UnaryOp(Deref, Expr::UnaryOp(Deref, pp))`, two ordinary nested nodes —
the same shape `maybe_read_copy` already synthesizes internally, now expressible
directly rather than only inferred.

---

## 4. Writes: explicit `*p = v`, and retiring the implicit inference

`assign_target_to_typed_place` (`construction.rs`, line 4219) gets one new arm:

```rust
AssignTarget::Deref(object, span) => {
    let typed_object = construct_expr(object, None, ctx)?;
    match typed_object.ty() {
        Type::MutReference(_) => Ok(TypedPlace::Deref {
            object: Box::new(typed_object),
            span: span.clone(),
        }),
        Type::Reference(_) => Err(MetelError::type_error(
            TypeErrorCode::T0002,
            "cannot write through a shared reference (`&T`); `&mut T` required",
            span,
        )),
        t => Err(MetelError::type_error(
            TypeErrorCode::T0002,
            format!("cannot dereference non-pointer type `{t}`"),
            span,
        )),
    }
}
```

`TypedPlace::Deref` already exists (`typed_ast/mod.rs`) and is already fully wired
through the evaluator's lvalue resolution (`evaluator/lvalue.rs`, both the field-assign
root walker at line 50 and the plain-assign path at line 98) — this arm is the only new
code writes need. Compound assignment (`*p += 1`) needs no separate handling: `+=`
already resolves through the same `TypedPlace` the plain `=` path does (confirmed by
`04_write_through_thin_reference.mtl`'s `p += 6;` already exercising the identical
`TypedPlace::Deref` path today via the implicit rule), so it carries over unchanged.

**This RFC retires the implicit write-through-via-plain-assignment rule described in
Motivation §2.** Once `*p = v` exists as a visible, explicit spelling, keeping an
invisible inference alongside it means two spellings for the same effect, one of them
undetectable at the call site — exactly the asymmetry RFC-0001 and RFC-0060 §7 already
argued against elsewhere. After this RFC:

- `p = v;` for a bare identifier `p` always means *rebind `p`* — legal exactly when `p`
  is declared `var`, the same rule every other type already follows. No special case
  for `&mut T`-typed bindings.
- `*p = v;` is the one spelling for writing through a reference.

Concretely, `inference.rs`'s `AssignTarget::Ident` special case for
`InferType::MutReference` (the `ctx.mark_write_through` branch, ~line 2113) is removed
in favor of always calling `ctx.lookup_for_write`; `construction.rs`'s corresponding
`write_through` bookkeeping (the `ctx.write_through` set, the peeling loop at
~line 1462) is removed with it, since nothing produces the condition it checks for
anymore.

**This unlocks repoint, which is impossible today:**

```metel
var a = 1;
var b = 2;
var p: &mut i64 = &mut a;
p = &mut b;        // repoint — a type error today; legal after this RFC (p is var)
*p = 5;             // write through — b becomes 5, a unchanged
```

**Migration cost against the existing corpus is small and precisely bounded**, checked
directly rather than assumed: three fixtures rely on implicit write-through today —
`04_write_through_thin_reference.mtl`, `08_write_through_reference_chain.mtl`, and
`14_mut_field_pointer.mtl`. Every bare-identifier assignment/compound-assignment in
those three (`p = 4`, `p += 6`, `pp = 5`, `pp += 10`, `px = 10`, `px += 5`, `t1 = 999`,
`a1 = 42`, `a1 += 8`, `brx = 20`) needs a `*` prefix added. `14`'s trailing
`qptr.y = 99;` is untouched — it's a `FieldAccess` target, not a bare `Ident`, so it was
never part of the ambiguous case this RFC resolves; auto-deref field-write-through
(RFC-0045's fat-pointer mechanism, reached through `resolve_field_assign_root`'s
existing `Ident`-with-one-auto-deref-level handling) is unaffected by this RFC
entirely. No repo-wide grep beyond these three fixtures was performed as part of this
RFC; a full sweep across `tests/` and `stdlib/` is implementation-time work, not a
design question, since the rewrite is mechanical (`p = v` → `*p = v`) and
grep-and-fix-able rather than requiring case-by-case judgment.

---

## 5. Interaction with RFC-0044 (Addressability)

RFC-0044 §9 requires an addressable receiver source for `&self`/`&mut self` calls.
`*p` for `p: &mut T` is a new addressable *place* by the same logic §9 already applies
to named bindings, fields, and array elements — writing through it or taking `&(*p)`
follow the existing addressability rule, not a new one: `*p` is addressable whenever
`p`'s value is available, exactly as `p` itself already was. No change to §9's rule
text is needed; this is a straightforward instance of it, not an extension.

`&*p` (address-of a deref) is a legal combination once both operators exist — a
reborrow, producing a fresh `&mut T` (or `&T`) from an existing one. Metel has no
borrow checker yet (RFC-0071 is accepted but 0% implemented), so today `&*p` and `p`
alias the identical `Rc<RefCell<Value>>` with no observable difference; whether `&*p`
should shorten an *effective* borrow's scope once RFC-0071 lands is real but explicitly
deferred — see Open Questions.

---

## 6. Interaction with RFC-0108 (Reference-Transparent Match Scrutinees)

Complementary, not overlapping — RFC-0108's own Alternatives Considered section already
drew this line: general `*expr` was "rejected as the primary fix" for match
scrutinees specifically, since RFC-0108's narrower auto-peel is strictly less
machinery for that one case, but was explicitly left open to be "proposed separately on
its own merits." This RFC does exactly that, on the merits laid out in Motivation §1-2,
independent of match at all.

Once both ship, `match *c { .. }` and RFC-0108's auto-transparent `match c { .. }` are
both legal and produce the same result for a `&T` scrutinee — the same kind of
harmless redundancy `&mut T` → `&T` implicit coercion already creates alongside
explicit narrowing elsewhere in the language. Neither RFC needs the other; sequencing
is immaterial between them (unlike RFC-0108 §2's real sequencing note against
RFC-0107, which is about two mechanisms touching the *same* code path).

---

## 7. Out of scope

- **Deref *patterns*** (a `*pat` pattern-position sigil, Rust's `box`-pattern-adjacent
  territory). This RFC is expression-level only: `*expr` as a value-producing
  expression and as an assignment target. RFC-0108 already solves the one pattern-
  position gap that mattered (match scrutinees); nothing here proposes matching
  *through* an explicit `*` in pattern position.
- **`Deref`/`DerefMut` as user-overloadable aspects** (Rust's `std::ops::Deref`,
  letting a user-defined smart-pointer type opt into `*`/auto-deref). Out of scope
  entirely — `*` in this RFC only ever applies to the two built-in reference types,
  `&T`/`&mut T`, exactly like RFC-0067a's own auto-deref. A user-overloadable version
  would be a separate, much larger RFC with its own aspect-coherence questions.
- **Allocator pointers (`@a T`).** RFC-0067 §1 (Lifetime Anchors) already gives `@a T`
  its own "borrow-deref" operator (`&a expr`, obtaining a `&T`/`&mut T` without
  consuming the allocator pointer) — a different mechanism for a different type
  entirely. `*` in this RFC never applies to `@a T` directly; `construct_unaryop`'s
  existing match on `Type::Reference`/`Type::MutReference` already excludes it, and
  this RFC doesn't touch that.

---

## Alternatives Considered

- **Add `*` for reads only; keep implicit write-through.** Rejected — this is the
  status quo's asymmetry, just partially patched. It would leave exactly the
  hidden-behavior problem from Motivation §2 in place (`pp = 5` still silently writing
  through two layers) while adding a second way to spell reads that §3a's mechanism
  already half-covers, net new inconsistency for no simplification.
- **Keep both spellings live — implicit write-through *and* explicit `*p = v`, as
  synonyms.** Rejected — two spellings for an operation with real consequences (which
  storage location gets mutated) is worse than either extreme; a reader seeing
  `p = v;` for a `&mut T`-typed `p` would need to know both the implicit rule and check
  for an explicit-only-elsewhere convention to know which happened. Explicit-only makes
  every write-through visible at its call site, matching `&`/`&mut` themselves already
  being mandatory rather than inferred from usage.
- **Repoint-only, no write-through inference change, add `*p = v` as a strictly new
  capability alongside the unchanged implicit rule.** This is a variant of the "keep
  both" option above with the same rejection: it would make `p = v;`'s meaning depend
  on whether `p` is `let` or `var` (repoint only possible for `var`, so `let p: &mut T`
  could stay write-through while `var p: &mut T` became ambiguous or contextual) —
  more special-casing, not less, and still hidden at the call site.

---

## Open Questions

1. **`&*p` and future borrow-checker interaction.** Once RFC-0071 lands, does `&*p`
   meaningfully shorten a borrow's effective scope relative to using `p` directly (the
   real motivation for this idiom in Rust), or is Metel's borrow-checker design (not
   yet written) going to make the distinction moot? Not resolved here — flagged as a
   forward pointer for whoever designs Metel's borrow checker, the same deferral
   pattern RFC-0067a already used repeatedly for exclusivity *enforcement* versus
   notation.
2. **Lint for redundant `*&x` / `*&mut x`.** Trivially simplifiable (dereferencing an
   address-of you just took), harmless, and not a type error — worth a style lint once
   Metel has a lint pass, not a compiler error. Not blocking.
3. **Full-corpus migration sweep.** Noted in §4 as implementation-time work, not a
   design question — flagged here only so it isn't silently dropped between RFC
   acceptance and implementation.

---

## References

- RFC-0043 (Regular Pointers, superseded by RFC-0067a) — the original `*p` design;
  §5's addressability rule, §6's auto-deref-for-field-access precedent, both carried
  forward unchanged by RFC-0067a and unaffected by this RFC.
- RFC-0045 (Mutable Address-Of for Lvalue Paths, implemented) — designed fat-pointer
  write-through entirely in terms of explicit `*p = v`; this RFC restores that
  spelling on top of RFC-0067a's `&`/`&mut` notation.
- RFC-0067a (Reference Types, implemented) — **amended by this RFC**: retracts the
  implicit write-through-via-plain-assignment behavior described only in amendment
  blockquotes, never specified in a numbered section (Motivation §2); §3's auto-deref
  chain guarantee and §3a's read-copy rule are otherwise unchanged and continue to
  apply exactly as before — this RFC adds a second, explicit way to reach the same
  read, not a replacement for §3a's positions.
- RFC-0044 (Explicit Receiver Semantics, implemented) — §9 addressability; `*p`
  is a straightforward new addressable place under the existing rule (§5 above).
- RFC-0067 (Lifetime Anchors, accepted) — §1's allocator-pointer borrow-deref (`&a
  expr`) is the analogous but distinct mechanism for `@a T`; unaffected by this RFC
  (§7).
- RFC-0071 (Ownership and Move Semantics, accepted, 0% implemented) — the eventual
  home for exclusivity *enforcement*; this RFC only restores notation, same posture
  RFC-0067a itself took.
- RFC-0108 (Reference-Transparent Match Scrutinees, draft) — independently found and
  named the same "no general deref expression" gap while scoping a narrower,
  match-only fix; its own Alternatives Considered section explicitly left general
  `*expr` open to be proposed separately (§6 above).
- `tests/integration/sources/evaluator/references/04_write_through_thin_reference.mtl`,
  `08_write_through_reference_chain.mtl`,
  `tests/integration/sources/evaluator/types/14_mut_field_pointer.mtl` — the three
  fixtures exercising today's implicit write-through rule; migration cost cited in §4.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
