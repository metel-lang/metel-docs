---
id: rfc-0183
title: "Initialization-Only Walrus"
date: '2026-10-24'
status: under-review
updated: '2026-10-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/1594'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

## Summary

Make `:=` a pure *initialization* separator: it appears only where a declaration introduces a
name (`let`/`var` bindings, record-pattern declarations, `type` aliases, associated-type
definitions). Plain reassignment returns to `=`:

```metel
var total := 0;        // introduces `total`
total = total + 1;     // stores into an existing place (was: total := total + 1)
obj.count = 3;         // was: obj.count := 3
xs[i] = 0;             // was: xs[i] := 0
```

Compound assignment (`+=`, `-=`, `*=`, `/=`, `%=`) is unchanged.

This **amends RFC-0136** (implemented), which moved plain reassignment onto `:=` along with
`let`. Everything else in RFC-0136 stands: field-init, associated-type binding and keyword
arguments stay on `=`, every `:` site is untouched.

This is a breaking change to the most-written statement form in the language, so it needs
this RFC first (see `metel_rfc_before_implementation`).

---

## Motivation

### RFC-0136's axis does not fit reassignment

RFC-0136 splits the two tokens on whether a name is *kept*: "a separator that introduces a
*kept* name — one referenceable from a later point in the same lexical scope — is `:=`; a
separator that labels a value consumed once is `=`". That is a clean test for `let x := e`
(a name appears and persists) and for `type Item := i64` (a member is added to the impl's
namespace). It is vacuous for reassignment. In `total := total + 1` no name is introduced,
and `total` was already referenceable before and after; "still usable afterwards" is true of
every statement that mentions an existing place. RFC-0136 files reassignment under "kept"
by reading the target as a name that persists, not as a name that is *introduced*; the
normative invariant it states ("a separator that introduces a kept name") does not actually
apply to it. The classification was made to put the `let` family and reassignment on one
token, and the invariant was stretched to fit.

### A better axis exists, and it is simpler

Look at what each `=` site does:

| site | what it does |
|---|---|
| `Point { x = 1.0 }` | puts a value into the existing slot `x` of the value being built |
| `Deref<Target = Node>` | fixes the existing slot `Target` of an aspect instantiation |
| `method(param1 = 4)` *(RFC-0100)* | puts a value into the existing parameter slot |
| `obj.count = 3`, `xs[i] = 0`, `total = 1` | puts a value into an existing slot (field, element, binding) |

Every one is "fill a slot that already exists". `:=` sites are the ones where the left-hand
side *does not exist yet* and the statement creates it. So:

> **`:=` introduces a name. `=` stores into something that already exists.**

That is stated without reference to lifetimes or scopes, and it classifies every site in
RFC-0136's audit, including reassignment, without a special case. It also makes
`Point { x = 1.0 }` and `p.x = 1.0` the same operation spelled the same way, where today the
second is `p.x := 1.0` — the pair RFC-0136's Motivation section used to *illustrate* the
confusion, now lined up differently.

### The compound operators already say this

RFC-0136 §Open Questions #1 resolved that `+=` and friends stay as they are because "a
compound operator is only ever legal against an assignable place that already holds a
value". The same sentence describes plain reassignment. Today the language has `x += 1`
beside `x := x + 1`: one in-place update spelled with `=` and one with `:=`, for the same
kind of target. With this RFC, `x += 1` and `x = x + 1` differ only by what they compute.

### Precedent

RFC-0136's own *Costs* section records that "precedent is genuinely split … Adopting `:=`
is a real departure from what most of Metel's likely readers already know". `=` for
reassignment is what C-family, Python, JavaScript, Rust and Swift readers expect; `:=` for
*declaration* is the Go/Pascal reading and survives unchanged. The cost RFC-0136 accepted
(a second token to type and learn on the most common statement) halves: it remains only on
declarations.

---

## 1. The change

### Grammar

`assign_op`'s plain alternative changes from `":="` to `"=" ~ !("=" | ">")`; the compound
alternatives are untouched. `:=` is removed from `assign_op` and stays in `let_decl`,
`let_mut_decl`, the record-pattern declaration, `type_alias`, and `assoc_type_def`.

Assignment (plain and compound) moves out of `assign_expr` into statement position: a block
statement, a match arm body, and a `for` header's init and update clauses (Open Question 1).

### Audit (RFC-0136's table, restated)

| Rule | Today | Proposed |
|---|---|---|
| `let_decl`, `let_mut_decl`, record-pattern declaration | `x: T := e` | **unchanged** |
| `assoc_type_def`, standalone `type` alias | `type Item := T` | **unchanged** |
| `assign_op`, plain | `lhs := e` | **`lhs = e`** |
| `assign_op`, compound | `lhs += e` | unchanged |
| `field_init`, `assoc_binding`, `keyword_arg` | `=` | unchanged |

### The invariant (replaces RFC-0136's)

> **Within the separator sites (`=` or `:=` between a name/target and a value): `:=` when the
> left-hand side is a name this site introduces; `=` when it is a place, slot or label that
> already exists.**

Future sites are placed by that rule: pattern-position field renaming (`local := field`)
introduces `local`, so `:=`; a keyword argument names an existing parameter, so `=`.

### Worked examples

```metel
// before                                  // after
var total := 0;                            var total := 0;
total := total + 1;                        total = total + 1;
obj.field := obj.field + 1;                obj.field = obj.field + 1;
xs[0] := 5;                                xs[0] = 5;

Point { x = 1.0 };                         Point { x = 1.0 };      // unchanged
```

### Diagnostics

Both old spellings become targeted errors rather than a bare parse failure:

- `let x = 1;` → "a binding is initialized with `:=`"
- `x := 1;` where `x` is not being declared → "`:=` introduces a name; use `=` to assign
  to an existing place"

---

## 2. What this does to RFC-0136's resolved side effect

RFC-0136 notes that once plain assignment requires `:=`, "`f(x = 1)` is unambiguously a
keyword-argument label", so RFC-0100's `call_arg` ordering concern disappears. **This RFC
gives that back.** Assignment is an expression of type `()` today
(`assign_expr = { unary_expr ~ assign_op ~ assign_expr | or_expr }`), so `f(x = 1)` is again
both a keyword argument and an assignment passed as a positional argument; likewise
`if (x = 1)`, which today is a type error only because `()` is not `boolean`.

The proposal does not leave that to the type checker. See Open Question 1.

---

## 3. Alternatives considered

1. **Status quo (RFC-0136 as implemented).** No migration. The axis stays "kept", which does
   not describe reassignment (Motivation), and `x += 1` stays beside `x := x + 1`.
2. **A distinct token for reassignment** (`<-`, `=:`, `set x = e`). Avoids the `=`/keyword-arg
   overlap entirely, but adds a third assignment spelling for the most common operation and
   leaves the language with no majority-convention reading of it. The `=` overlap is a
   parsing-position problem (§2), and a solvable one.
3. **Go-style `:=` ("declare *or* assign if new")**. Rejected by RFC-0136 for good reason and
   not reopened: `:=` meaning different things depending on prior declaration is the
   confusion this RFC removes.
4. **Do nothing and add a lint** warning on `:=` outside a declaration. Doesn't change the
   grammar's meaning; the token still serves two acts.

---

## 4. Costs

- **A second breaking pass over `let`/`var` neighbours.** Declarations do not change, but
  every *reassignment* in every fixture, spec example, blog post and RFC worked example
  does. Reassignment sites are syntactically identifiable (an `assign_op` plain `:=`, never
  a declaration), so the rewrite is mechanical, but it is the same breadth RFC-0136 touched
  weeks ago and users who migrated once migrate again. Pre-1.0 and no edition gating
  (RFC-0020's precedent), but it should not be minimised.
- **Reintroduces `=`-in-expression hazards** (§2) that RFC-0136 happened to remove.
- **Churn in implemented RFCs.** RFC-0136 is `4-implemented`; this amends its normative
  invariant and one audit row, and the spec rule
  `spec.declarations.variables.mutable-bindings.legality-1` (which says "both the initializer
  and a subsequent plain reassignment use the `:=` separator") changes.

---

## Review findings (2026-10-26)

A review against the grammar and the corpus found four things this RFC did not say.

1. **`{ x = 1 }` becomes ambiguous.** With plain assignment on `=` and assignment an expression,
   `{ x = 1 }` is both an anonymous record (RFC-0116) and a block whose tail is the assignment
   `x = 1`. RFC-0116's rule "a block wins in a block-admitting position" would silently turn a
   record tail such as `fun f() -> { x: i64 } { { x = 1 } }` (accepted today) into a block that
   returns `()`. The shorthand `{ x }` has the same shape. Resolved by Open Question 1: assignment
   is a statement, never a block's tail, so a block ending in `x = 1` with no `;` is a record.
2. **The `f(x = 1)` overlap (§2) is future-only.** RFC-0100 (keyword arguments) is
   `1-under-review` and the grammar has no `keyword_arg` rule, so there is no overlap in the
   language today. Making assignment a statement removes it before RFC-0100 can create it.
3. **Measured migration.** Reassignments written `target := expr;` (declarations excluded):
   287 sites in 163 of 1740 fixtures, 5 in the standard library, 29 in 14 spec, tutorial, blog and
   README files, and 23 in 12 RFC worked examples. Every fixture site is a `;`-terminated
   statement except one match arm body (`0 => total := total + i,`); none is a block's tail
   without `;`. Compound assignment appears in 14 `for` update clauses
   (`for (var i := 0; i < n; i += 1)`), which the statement-position rule must keep.
4. **Tokenisation.** The plain operator is `"=" ~ !"="`. Match arms are written `pat => expr`, and
   `=>` begins with `=`; pest backtracks correctly, but the rule should read `"=" ~ !("=" | ">")`
   so a guard such as `n if n > 0 => ...` never attempts an assignment parse.

---

## Open Questions — resolved 2026-10-26

1. **Is assignment still an expression?** *Resolved: no, option (b).* Assignment (plain and
   compound) is a statement. It is allowed as a block statement `target = expr;`, as the body of a
   match arm, and in a `for` header's init and update clauses. It is not an operand, argument,
   initializer, condition, or a block's tail expression. Consequences: `f(x = 1)` and `if (x = 1)`
   are grammar errors (the latter with the hint "`=` assigns; did you mean `==`?"), and
   `{ x = 1 }` stays an anonymous record. The type of an assignment is no longer `()` as a value
   anyone can use.
2. **Migration path.** *Resolved: hard cut*, as RFC-0136 did, with targeted diagnostics for both
   old spellings (§1).
3. **Assignment targets.** *Confirmed.* The parser's `unary_expr` target covers a name, field,
   tuple element and index; each moves to `=` identically. Destructuring targets stay out of scope.
4. **Pattern-position renaming (metel-core#706).** *Confirmed unaffected.* `local := field`
   introduces `local`, so `:=` is still right; nothing relies on RFC-0136's "kept" wording.
5. **Release timing.** *Resolved: v0.15.0*, the milestone already on the tracking issue, so the
   release's explicit-syntax changes (Option rename, `*r`, `?` on Option) migrate once.

---

## References

- RFC-0136 — Walrus for Kept Bindings (implemented). Amended by this RFC.
- RFC-0100 — keyword arguments (`method(param1 = 4)`), interacts via §2.
- RFC-0098 — surface keyword renames (precedent for pre-1.0 lexical migrations).
- RFC-0020 — rebranding (no-edition-gating breaking-change precedent).
- `reference/spec/declarations.md` — `mutable-bindings.legality-1` and the scoping rules
  citing `:=`; `reference/spec/grammar.md` — `AssignOp`.

---

## Decision

**Outcome:** *(pending)*
