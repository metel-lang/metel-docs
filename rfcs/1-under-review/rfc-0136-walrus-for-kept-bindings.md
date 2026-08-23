---
id: rfc-0136
title: "Walrus for Kept Bindings"
date: '2026-08-23'
status: under-review
target:
updated: '2026-08-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/804'
---

> **Status — under review (2026-08-23).** Design-complete three-way split, formalized from reports/syntax/colon-classifies-equals-labels-walrus-binds.md's design discussion; open questions remain (compound ops, RFC-0132 coordination, migration strategy) so under-review, not accepted.

## Summary

`let x = e`, plain reassignment (`x = e`), and `type X = Concrete` all currently spell
"define" with `=` — the same token struct/record field-init (`Point { x = 1.0 }`),
associated-type binding (`Deref<Target = Node>`), and future call-site keyword arguments
(`method(param1 = 4)`) use to mean something different: a label consumed once, at the
site, with no persisting name. This RFC splits the token along that line. `let`, plain
reassignment, and type-alias/associated-type *definition* move to `:=`; field-init,
associated-type *binding*, and keyword arguments stay on `=`; every `:` site is untouched.

---

## Motivation

`reports/syntax/colon-classifies-equals-labels-walrus-binds.md` established, and this
RFC's audit reconfirms, that Metel already satisfies a classify/define invariant at all
fourteen `:`/`=` sites in the grammar: `:` classifies (`x: T`, `T: Bound`), `=` defines or
equates (`let x = e`, `type X = Concrete`, `Deref<Target = Node>`). That invariant is
sound as far as it goes, but it treats two different things as one:

```metel
let total = 0;                    // total is usable from here on
Point { x = 1.0, y = 2.0 };       // x is a field label, gone the instant the value is built
total = total + 1;                // total, again, still usable
Deref<Target = Node>              // Target is a label picking out an associated type; not a name
```

Reading these side by side is where the confusion this RFC responds to actually shows up:
`Point { x = 1.0 }` and `total = total + 1` share a token despite meaning categorically
different things — one introduces a value that is thrown away as soon as it is consumed,
the other names a place that persists. **The core difference is whether the name is
kept** — referenceable again after the statement — **or not kept** — consumed once, at
the site. That distinction is real, it is not currently visible in the syntax, and it
generalizes cleanly across values, types, and (per RFC-0100's still-`1-under-review`
keyword-argument proposal) call arguments too — it is not a records-only or an
assignment-only question.

**Why this needs to happen now rather than later:** RFC-0100's keyword arguments
(`method(param1 = 4)`) are still under review and not yet live. Landing them on `=` first
and correcting the underlying assignment/label conflation afterward would mean touching
every keyword-argument call site a second time. Settling the three-way split before
RFC-0100 ships (or alongside it) avoids that.

---

## Proposal

> **`:` classifies. `=` labels — a value or type consumed at the construction or call
> site, not kept as a name. `:=` binds — a name that outlives the expression it appears
> in.**

- **Kept → `:=`.** `let`/`var` declarations, plain reassignment, `type X := Concrete`
  (type-alias and associated-type *definition*).
- **Not kept → `=`.** Struct/record field-init (`Point { x = 1.0 }`), associated-type
  *binding* at a use site (`Deref<Target = Node>`), and future call-site keyword arguments
  (`method(param1 = 4)`).
- **Unchanged → `:`.** Every site the existing classify/define invariant already calls
  "classifies" — ascription, bounds, param and generic-param types, `where` constraints,
  `extend`'s aspect list. This proposal touches only the `=` side.

### The audit

Every `:`/`=` site in `metel-frontend/src/grammar.pest`, current as of this RFC:

| Line | Rule | Form today | Kept? | Proposed |
|---|---|---|---|---|
| 62–63 | `let_decl`, `let_mut_decl` | `x: T = e` | **kept** | `x: T := e` |
| 76 | `struct_field` | `ident ":" type_expr` | n/a (type position) | unchanged |
| 85–86 | `extend_impl_bodyless`, `_braced` | `extend Foo: Display` | n/a | unchanged |
| 89 | `assoc_type_def` | `type X = type_expr;` | **kept** — `X` usable afterward | `type X := type_expr;` |
| 93 | `assoc_type_decl` | `type X: bound_list;` | n/a | unchanged |
| 98 | `param` | `ident ":" type_expr` | n/a | unchanged |
| 101 | `generic_param` | `T: bound_list` | n/a | unchanged |
| 117 | `assoc_binding` | `Item = type_expr` | **not kept** — label, not referenceable after | stays `=` |
| 119 | `where_constraint` | `T: bound_list` | n/a | unchanged |
| 160 | `assign_op` | `= expr` | **kept** — name already exists, continues to | `:= expr` (compound ops — see Open Questions) |
| 178 | `asc_expr` | `expr ":" type_expr` | n/a | unchanged |
| 260 | `field_init` | `ident ("=" expr)?` | **not kept** — consumed at construction | stays `=` |
| *(RFC-0100, proposed)* | `keyword_arg` | `ident "=" expr` | **not kept** — consumed at the call | stays `=` |

Four rules change: `let_decl`, `let_mut_decl`, `assign_op` (plain `=` only — see Open
Questions #1), `assoc_type_def`. Everything else in the fourteen-site audit is already
where this principle would put it, including RFC-0100's not-yet-live `keyword_arg`, which
needs no change under this proposal.

### Worked examples

```metel
// before                              // after
let total = 0;                         let total := 0;
var count = compute();                 var count := compute();
total = total + 1;                     total := total + 1;
type Meters = f64;                     type Meters := f64;

// unchanged — none of these are "kept" bindings
Point { x = 1.0, y = 2.0 };
Deref<Target = Node>
method(param1 = 4)                     // RFC-0100, not yet live
```

### A resolved side effect: the `f(x = 1)` collision

The original classify/define report flagged, as an accepted cost, that `assign_expr` sits
high in the expression precedence chain, so `f(x = 1)` can parse as a positional argument
containing an assignment — needing a `call_arg` reordering fix in RFC-0100. Under this
proposal that collision disappears rather than needing a fix: once plain assignment
requires `:=`, `=` can no longer parse as `assign_op` inside an argument position at all,
so `f(x = 1)` is unambiguously a keyword-argument label. RFC-0100's `call_arg` ordering
concern is moot if this RFC lands first.

---

## Alternatives Considered

- **Two-way "define vs. mutate" split** (`let x := 1` defines, `x = 2` mutates). The
  framing first proposed in discussion. Rejected: it cannot classify `assoc_binding`
  (`Deref<Target = Node>`) or the field-init/keyword-arg family at all, since none of
  those is a mutation of anything — lumping them under "definition" alongside `let`
  reintroduces the conflation the original classify/define report already fixed. The axis
  that explains every site is *kept vs. not kept*, not *created vs. changed*: `let x :=
  1` and `x := 2` (reassignment) are the same case under kept/not-kept despite one
  "defining" and one "mutating," and landing on the same token is the point.
- **Go-style `:=` means "first occurrence."** Go's `:=` contrasts with `=` on whether the
  name has been declared before, not on whether it persists afterward. Considered and set
  aside: under that rule Metel's plain reassignment (name already exists) would stay `=`,
  which does not resolve the struct-instantiation-vs-assignment confusion motivating this
  RFC — `Point { x = 1.0 }` and `total = total + 1` would still share a token. The
  distinction needed here is whether the name is usable *after* the statement, and by
  that measure reassignment belongs with `let`, not with field-init.
- **Leave `=` alone; disambiguate only at RFC-0100's call sites.** Fixes the narrowest
  visible symptom (keyword args vs. positional assignment) without touching the
  `let`/field-init conflation that motivated this RFC in the first place. Rejected as
  addressing a special case of a general problem rather than the problem.
- **Do nothing; treat it as a report-only style note.** The classify/define report already
  exists and binds nothing normatively. Given the migration scope below, report-only
  status was judged insufficient — see `colon-classifies-equals-labels-walrus-binds.md`'s
  own updated Recommendation.

---

## Costs

**This is the largest syntax-migration surface proposed to date.** `let`/`var`
declarations and plain reassignment are the most common statement forms in any Metel
program. Every existing `.mtl` fixture, every spec example, and every RFC's worked
examples that show a `let` or a reassignment need updating. This is a breaking change to
the most-written syntax in the language, and should not be minimized as a small
punctuation fix.

**A real token to learn and to type.** `:=` is not a single keystroke on most keyboards
the way `=` is. Every language that uses it as sugar for "declare" (Go, Pascal, Ada's
distinct assignment/equality split) accepts that friction deliberately; Metel would accept
it for a narrower reason (kept vs. label, not first-occurrence), which is real but is
still friction for anyone arriving from a `=`-only-means-assignment language — the
overwhelming majority of working programmers (C-family, Python, JavaScript, Rust).

**Precedent is genuinely split**, as the original classify/define report already noted for
the `=`-vs-`:` question and which carries over here: some languages use `:=` for
assignment/declaration (Pascal, Ada, Go), most mainstream languages do not (C-family,
Python, Rust, Swift). Adopting `:=` is a real departure from what most of Metel's likely
readers already know, not a return to a majority convention.

---

## Open Questions

1. **Do compound assignment operators (`+=`, `-=`, `*=`, `/=`, `%=`) move too?**
   `assign_op` bundles plain `=` with the compound forms. This RFC's audit only reasons
   about plain `=` — whether the compound operators also gain a `:` prefix (`+:=`), stay
   exactly as they are (arguable: they inherently presuppose the name already exists, so
   the kept/not-kept signal may be redundant there), or something else, is not decided.
2. **Comptime interaction.** RFC-0132 (Comptime Execution Model), still `1-under-review`,
   defines `comptime let` / `pub comptime let` syntax. Those are `let`-family declarations
   and would need `:=` under this proposal exactly like ordinary `let`. Worth settling
   together with RFC-0132 rather than shipping it first and migrating a second time
   shortly after — a coordination point, not a blocker either direction.
3. **Enum discriminants.** `enum E { A = 1 }` is field-init-shaped under this proposal:
   the discriminant value `1` is a label consumed at the declaration, `A` itself is
   already the kept name (introduced by the variant syntax, not by this `=`). Stays `=`.
   Included here for completeness, not because it is contested.
4. **Migration mechanics.** RFC-0115's field-initializer migration (573 literal sites, a
   parser-driven rewrite rather than a regex sweep, because declarations/patterns/literals
   share brace syntax) is the closest precedent in scale, but this RFC's surface is
   considerably larger (every `let` and every plain reassignment in the corpus, not just
   struct literals). Sizing against the current corpus, choosing a rewrite strategy, and a
   transition-alias decision (RFC-0042 §D1 and RFC-0098 both shipped renames with **no**
   transition alias; whether that precedent should hold here, given the surface size, is
   worth deciding explicitly rather than defaulting to it) are not resolved in this
   document.

**Explicitly out of scope:** declaration-side default parameter values (hypothetical `fun
f(x: T = e)`). Raised once during the discussion that produced this RFC and set aside — a
different syntactic position from the call-site keyword-arg case this RFC addresses (`x`
there is a parameter declaration with a type and a default, not a label), with its own
kept/not-kept answer not decided here. Left for a future RFC.

---

## References

- `reports/syntax/colon-classifies-equals-labels-walrus-binds.md` — the classify/define
  invariant this RFC extends, the full fourteen-site audit (original and extended), and
  the design discussion that produced the kept/not-kept axis
- `public/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` — proposes the
  `keyword_arg` site this RFC's audit covers; unaffected by this proposal (stays `=`), and
  this RFC's resolution of the `f(x = 1)` collision (see Proposal) simplifies RFC-0100's
  own `call_arg` ordering concern
- `public/rfcs/4-implemented/rfc-0115-field-initializer-separator.md` — the closest
  precedent in migration shape and scale (a parser-driven corpus rewrite, no transition
  alias), though smaller in surface than this proposal
- `public/rfcs/1-under-review/rfc-0132-comptime-execution-model-comptime-let-comptime-fun-comptime-if.md` — `comptime let`
  syntax; the coordination point named in Open Questions #2
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the record-syntax
  question the classify/define invariant originally generalized from

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
