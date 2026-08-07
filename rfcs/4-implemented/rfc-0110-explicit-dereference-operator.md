---
id: rfc-0110
title: "Explicit Dereference Operator"
date: '2026-07-20'
status: implemented
target:
updated: '2026-07-21'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/559'
impl_status: implemented
---

> **Status — under review (2026-07-20).** Thorough draft; open questions (&*p borrow-checker interaction, redundant-deref lint, Eq/Ne peeling) are all non-blocking or implementation-time. Reviewing with the enum/reference cluster.

> **Status — accepted (2026-07-20).** Design settled; extend auto-deref read-copy to call args/binops, retire bare-identifier write-through for explicit *p=v, add unary * for reads and writes. Open questions non-blocking/impl-time.

> **Status — integrated (2026-07-20).** Merged into expressions.md (Dereference) + types.md; write-through change flagged as Changed in v0.11.0; field/index write-through unchanged; read-copy extension documented.

> **Status — under review (2026-07-21).** Design changed materially: adopting the Go model (explicit *, selector auto-deref only, bare assignment rebinds). Read-copy extensions to call arguments and binary operands split out into RFC-0112, which is still being decided. Spec text backed out.

> **Status — accepted (2026-07-21).** Go model settled: explicit unary * for reads and writes, auto-deref at selectors only, bare assignment rebinds (unlocking repoint). Read-side extensions live in RFC-0112 and are not a dependency. Index-path write-through ships here as an addition; repointing does not wait for RFC-0071. Remaining open questions (&*p borrow interaction, redundant-deref lint) are both explicitly non-blocking.

> **Status — integrated (2026-07-21).** Merged into expressions.md (Dereference) + types.md: explicit * for reads and writes, auto-deref at selectors only, bare assignment rebinds, field and index write-through implicit. Worked examples cross-checked against RFC-0107/0108/0112/0045/0044; RFC-0045 gave the index write-through correction, RFC-0044 surfaced metel-core#563.

> **Status — implemented (2026-07-21).** `*` needed no typechecker or evaluator change for reads — `UnaryOp::Deref` was already fully handled and merely unreachable from surface syntax; writes got `AssignTarget::Deref` lowering to the existing `TypedPlace::Deref`. Migration touched 13 fixtures, not the 3 Migration predicted (it deferred the sweep to implementation time); all mechanical except the two chain fixtures, where one-star-per-layer is a real semantic change. `08_write_through_reference_chain` was rewritten to cover repointing through a chain, which the old peel-every-layer rule made impossible. Dead `write_through_assigns` plumbing removed. 773 tests green.

## Summary

Adopt the Go model for references, for this phase: an explicit unary `*expr` for reading
through a reference and for writing through it (`*p = v`); auto-deref kept **at selectors
only** — field access, field assignment, method dispatch; and bare assignment to a
reference-typed identifier changed to mean *rebind*, as it does for every other type,
which is what unlocks repointing.

**Auto-deref is not one mechanism, and this RFC does not treat it as one.** Metel ships at
least four: selector dispatch, RFC-0045's field/index write-through, RFC-0067a §3a's
type-directed read-copy, and bare-identifier whole-value write-through. Go keeps the first
kind and requires `*` for everything else. This RFC applies that split to the *write* side
and to explicit syntax; the *read* side — where implicit copy-out should and should not
fire — is a separable question, split out into **RFC-0112** and deliberately not decided
here. Nothing in this RFC depends on how RFC-0112 lands.

---

## Motivation

### 1. What the interpreter actually does today — measured, not assumed

Every row below was probed directly against the built interpreter rather than read off
RFC-0067a's text, which turns out to overstate its own coverage (see RFC-0112):

| construct | today |
|---|---|
| `p.x`, `p.i.v` field read through `&` | works |
| `p.x = v` field write-through | works |
| `xs[0] = v` index write-through through a reference | **fails** (`T0001`) |
| `p = v` bare-identifier write-through | works |
| `p = &var b` (repoint) | **fails** — `cannot unify i64 with &var ?t18` |
| `let y: i64 = r` type-directed copy-out | works, including `&&i64` |
| `return p` where the return type is `i64` | works |
| `r + 1` binary operand | fails (`T0001`) |
| `takes(r)` call argument | fails (`T0001`) |
| `let w = W { v = r }` struct-literal field | fails (`T0001`) |
| `match .. { true => r }` arm against an `i64` expected type | fails (`T0001`) |

Two things fall out. First, **repointing is not merely awkward today, it is
unrepresentable** — row 5 is the empirical confirmation of §4.2's premise. Second,
§4.1's claim to keep field- *and index*-path write-through "unchanged" is wrong on the
index half: it does not work through a reference today, so this RFC *adds* it rather than
preserving it (§4.1, corrected).

### 1a. Why Go, and why only for this phase

Go's rule is: `*p` explicit for reads and writes; auto-deref at selectors only (`p.f`,
`p.m()`, `p[i]` for pointer-to-array); `p = q` always rebinds, `*p = v` always writes
through. Rust reaches the same place by a different route (no implicit write-through
either), so the two agree on everything this RFC decides.

The attraction is that it makes exactly one rule carry the ambiguity: **an operation whose
direction could be misread requires the sigil.** `p.x = v` cannot mean anything but "write
into that field," so it stays implicit. `p = v` can mean either "write through" or
"repoint," so it becomes explicit. That is a smaller and more defensible claim than
"implicit mechanisms are worse than explicit ones," which an earlier draft of this RFC
leaned on and which does not survive contact with §4.1.

"for this phase" is load-bearing. Metel has no borrow checker (RFC-0071, accepted, 0%
implemented), so the repointing this RFC unlocks is unpoliced. Assessed rather than waved
past: repointing introduces **no new soundness hole** — a `&var T` can already escape its
referent's scope today without repointing — it only adds more routes to a hole that already
exists and that RFC-0071 is the designated fix for. That is acceptable now and should be
re-examined when RFC-0071 lands, not treated as settled forever.

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
let p: *mut Counter = &var pair.counter;
p.tick();           // pair.counter updated automatically
```

RFC-0067a's rename traded the explicit spelling for implicit-only inference as a side
effect of unifying `*T`/`&x` notation, not because the explicit spelling was judged
wrong on its own terms. This RFC restores it as an available spelling on top of
RFC-0067a's `&`/`&var` notation — alongside the implicit mechanism, not instead of it.

---

## 1-2. Implicit read-coercion: out of scope, see RFC-0112

An earlier version of this RFC proposed extending RFC-0067a §3a's type-directed read-copy
to two further positions — arguments of monomorphic calls, and binary-operator operands —
so that `takes(r)` and `r + 1` would work without a sigil. Under the Go model both stay
errors, written `takes(*r)` and `*r + 1`.

That is not a decision this RFC should make, because it is not really about `*` at all: it
is about how far implicit read-coercion should reach, which positions count, and how that
boundary is enforced as new expected-type-carrying positions get added. **Split out into
RFC-0112 (Auto-Deref Scope and Expected-Type Provenance)**, along with the gap analysis
that motivated the two extensions and the finding that RFC-0067a §3a's text claims more
coverage than it has.

This RFC is independent of that outcome. `*p` is a legal read spelling everywhere,
whatever RFC-0112 decides about where the implicit form also fires — the two compose as
redundant spellings exactly as §5 describes for writes. Section numbering below is left
unchanged so cross-references from other RFCs stay valid.

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

### 4.1 Kept: field-path write-through (RFC-0045) — and index-path, which is an *addition*

Any assignment whose *target* is a `FieldAccess` or `Index` (`obj.field = v`,
`arr[i] = v`, including when auto-deref is needed to reach `obj`/`arr` through a
reference at the root) goes through `resolve_field_assign_root`, a mechanism entirely
separate from the one this RFC touches. There is no competing "repoint" reading for a
field or index target — `obj.field = v` can only ever mean "write into that field" —
so this is the selector case Go keeps implicit, and it stays implicit here:

**Correction to an earlier draft of this section, which claimed both halves were "kept,
unchanged."** Field paths do work today, at arbitrary nesting (`o.i.v = 8` verified).
Index paths through a reference **do not** — `fun f(xs: &var i64[]) { xs[0] = 9; }` fails
today with `cannot unify &var i64[] with ?t19[]`. So the index half is a new capability
this RFC adds, with its own implementation cost and its own fixtures, not a preservation
of existing behavior. It is kept in scope because Go's selector rule covers `p[i]` and
splitting it out would leave the write side half-specified, but it must not be budgeted
as free.

```metel
var q = Point { x = 5, y = 7 };
let qptr: &var Point = &var q;
qptr.y = 99;      // auto-deref field write — unambiguous, unaffected by this RFC
assert(q.y == 99);
```

### 4.2 Retired: bare-identifier whole-value write-through

**This is the one case that collides with repoint, and the one this RFC changes.**
Today, assigning to a plain identifier `p` whose static type is `&var T` (at any chain
depth) writes through every `&var` layer to the innermost `T`, unconditionally,
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
`var`-declared `&var T` binding — `p = &var m;` is a type error today (the right side
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
  for `&var T`-typed bindings.
- `*p = v;` (§5) is the spelling for writing through a bare reference identifier.

```metel
var a = 1;
var b = 2;
var p: &var i64 = &var a;
p = &var b;    // repoint — a type error today; legal after this RFC (p is var)
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

**Reads**, once this exists, are legal everywhere — including the positions where
implicit copy-out already fires, as a redundant but always-available spelling:

```metel
let sum = *p + *q;    // the only spelling for binary operands under the Go model
f(*r);                // the only spelling for call arguments under the Go model
let y: i64 = *r;      // redundant with today's copy-out, and legal either way
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
(`&var T` implicitly coercing to `&T` while a narrower explicit annotation achieves the
same thing; §7 below, where `match *c { .. }` and RFC-0108's auto-transparent
`match c { .. }` will coexist the same way). For a **bare identifier** target,
`*p = v` is not redundant with anything after §4.2 — it is the only spelling that
writes through, since bare `p = v` now means repoint.

---

## 6. Interaction with RFC-0044 (Addressability)

`*p` for `p: &var T` is a new addressable *place* under RFC-0044 §9's existing rule,
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
  applies to the two built-in reference types, `&T`/`&var T`, exactly like RFC-0067a's
  own auto-deref. A user-overloadable version is a separate, larger RFC — RFC-0080 §2
  (under review) already drafts the aspects.

  One forward-compatibility note, since §5's write side is the part that would strain:
  `*p = v` is specified here as an `AssignTarget::Deref` producing a `TypedPlace::Deref`,
  i.e. `*p` names a *place*. RFC-0080 §2.2's `fun deref_mut(self: &var Self) -> &var Target`
  returns a *value* of reference type. Those are not the same thing, and reconciling them
  is the known-hard part of user-overloadable deref (Rust has the same tension). Nothing
  here needs to solve it, but §5's write side should not be read as already covering
  user types.
- **Making `&T` a nominal type (`Ref<T>`/`VarRef<T>`) rather than a structural
  `Type::Reference` variant.** Raised 2026-07-21 while reviewing this RFC. It is a real
  and separable question — see the analysis recorded on it — but it does not change this
  RFC's surface semantics: `*` would dispatch on a nominal type instead of a structural
  variant and behave identically. This RFC is written against `&T`/`&var T` as spelled
  today and stays correct either way.
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
  `&var T`-typed binding still behaves unlike assignment to every other type) rather
  than resolving it.
- **Keep bare-identifier write-through unconditional and disambiguate repoint by the
  right-hand side's type instead** (an RHS of type `T` writes through, an RHS of type
  `&var T` — matching `p`'s own declared type exactly — repoints; generalizes cleanly
  to chains, where each layer of `&var` is its own "rung"). No new syntax at all, and
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
- **Extend implicit read-copy to call arguments and binary operands in this RFC**
  (what the accepted version proposed). Moved out rather than rejected — see §1-2 and
  RFC-0112. Under the Go model these positions stay explicit, but the question deserves
  its own decision rather than riding along with the write-side change.
- **Strict Go, including retiring RFC-0067a §3a's copy-out entirely** so that even
  `let y: i64 = r;` requires `*r`. Rejected for this RFC's scope: §3a is implemented and
  integrated, retiring it is a second breaking change with a different justification from
  §4.2's, and it is squarely RFC-0112's question, not this one's.

---

## Migration

Field-path write-through (§4.1) is untouched; no migration cost. Index-path
write-through through a reference is an addition (§4.1's correction) and so has no
migration cost either — nothing relies on behavior that does not exist.

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
2. **Lint for redundant `*&x` / `*&var x` / `*(obj.field)` where auto-deref alone
   would already do the same thing.** Harmless, not a type error, worth a style lint
   once Metel has a lint pass. Not blocking, and deliberately not a compiler error —
   §5 is explicit that this redundancy is intended for field/index targets, not a
   defect to warn away by default.
3. ~~**Does index-path write-through belong in this RFC?**~~ **Resolved 2026-07-21: yes.**
   It ships here rather than separately — Go's selector rule covers `p[i]`, and the write
   side is half-specified without it. It remains an addition rather than a preservation
   (§4.1's correction), so it carries its own implementation cost and needs its own
   fixtures; that is a budgeting note, not an open design question.
4. ~~**Should repointing be gated behind RFC-0071?**~~ **Resolved 2026-07-21: no.**
   Motivation §1a's assessment stands — repointing adds no new soundness hole, only new
   routes to one that already exists and that RFC-0071 is the designated fix for. §4.2
   ships with the rest of this RFC rather than waiting for the borrow checker.

---

## Resolved while integrating (2026-07-21)

Worked examples combining this RFC with each sibling it can interact with, per PROCESS's
`3-integrated` exit criterion. Two of the four turned up something.

**RFC-0108 (Reference-Transparent Match Scrutinees, implemented) — no conflict, confirmed
redundant by design.** `match *c { .. }` and `match c { .. }` for `c: &Colour` both work
and produce the same result: RFC-0108 peels the scrutinee, and `*c` peels it explicitly
first. §7 predicted this; nothing changes. Checked that RFC-0108's peel runs on the
scrutinee's constructed type, so an explicit `*` simply arrives having already done the
peel — the two do not compound into a double deref.

**RFC-0107 (Unqualified Enum Variants, implemented) — no interaction.** Bare-variant
resolution runs on the *pattern* side against the scrutinee's enum; `*` is expression-level
only (§8). `match *c { Red => .. }` composes both with no ordering question, because the
peel happens before variant resolution either way.

**RFC-0112 (Auto-Deref Scope, draft) — the coupling is one-directional and safe.** RFC-0112
may narrow or widen where *implicit* read-copy fires. Every position it could touch remains
spellable with an explicit `*` regardless, so no outcome of RFC-0112 can invalidate anything
here. The reverse is also true: this RFC adds no new implicit read-copy site. Confirmed the
two RFCs share no code — §5's parser/`AssignTarget` work does not touch `maybe_read_copy`.

**RFC-0045 (Mutable Address-Of for Lvalue Paths, implemented) — turned up the §4.1
correction, already folded in.** Field-path write-through works today at arbitrary nesting;
index-path write-through *through a reference* does not (`fun f(xs: &var i64[]) { xs[0] = 9; }`
fails with `cannot unify &var i64[] with ?t19[]`). This RFC therefore adds it rather than
preserving it. Caught here rather than at implementation time, which is what this stage is
for.

**RFC-0044 (Addressability, implemented) — turned up a live hazard, filed rather than
absorbed.** §6 says `*p` is a new addressable place and `&*p` is a legal reborrow. But
address-of a non-lvalue currently aborts with `[I0001] internal error` rather than a
diagnostic, and there is no static addressability check anywhere in the typechecker — so
`&*p` failing would fail *badly*. Filed as metel-core#563 with the finding that the check is
static-determinable (the evaluator decides purely on typed-AST shape). Not a blocker for
this RFC — `*p` for a reference-typed `p` is always addressable — but §5's write side should
land after #563, not before, so that a malformed `*expr = v` produces a real error.

**Not cross-checked, deliberately:** RFC-0080's `Deref`/`DerefMut` aspects (under review).
§8 scopes user-overloadable deref out entirely, and §8's forward-compatibility note already
records the one place the two would collide — RFC-0080 §2.2's `deref_mut` returns a *value*
of reference type where §5 needs a *place*.

---

## References

- RFC-0043 (Regular Pointers, superseded by RFC-0067a) — the original `*p` design;
  §5's addressability rule and its auto-deref-for-field-access precedent were carried
  forward unchanged by RFC-0067a and are unaffected by this RFC.
- RFC-0045 (Mutable Address-Of for Lvalue Paths, implemented) — designed fat-pointer
  field/index write-through, kept entirely unchanged by this RFC (§4.1); originally
  specified in terms of explicit `*p = v`, which §5 of this RFC restores as available
  syntax for it, redundantly with the auto-deref this RFC leaves alone.
- RFC-0067a (Reference Types, implemented) — this RFC **amends** the bare-identifier
  write-through rule its own amendment blockquotes
  named but never gave a numbered section, retiring it in favor of explicit `*p = v`
  (§4.2) — a real behavioral change, not just documentation, unlike §4.1's mechanism.
  §3's auto-deref chain guarantee and RFC-0045's field/index write-through are
  unaffected.
- RFC-0044 (Explicit Receiver Semantics, implemented) — §9 addressability; `*p` is a
  straightforward new addressable place under the existing rule (§6 above).
- RFC-0067 (Lifetime Anchors, under review) — §1's allocator-pointer borrow-deref (`&a
  expr`) is the analogous but distinct mechanism for `@a T`; unaffected (§8).
- RFC-0071 (Ownership and Move Semantics, accepted, 0% implemented) — the eventual
  home for exclusivity *enforcement*; this RFC only extends/restores notation, same
  posture RFC-0067a itself took.
- RFC-0112 (Auto-Deref Scope and Expected-Type Provenance, draft) — split out of this
  RFC. Owns the read side: where implicit copy-out fires, and the two extensions this RFC
  originally proposed (call arguments, binary operands), declined there under a
  provenance-based rule. Neither RFC depends on the other's outcome.
- RFC-0108 (Reference-Transparent Match Scrutinees) — independently found and
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
