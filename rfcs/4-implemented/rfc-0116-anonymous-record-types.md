---
id: rfc-0116
title: "Anonymous Record Types"
date: '2026-07-24'
status: implemented
target:
updated: '2026-07-25'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/576'
impl_status: implemented
coverage:
  "1": { spec: "spec.types.anonymous-records.dynamics-1" }
  "2": { spec: "spec.types.anonymous-records.dynamics-1" }
  "3": { spec: "spec.types.anonymous-records.legality-1" }
  "4": { spec: "spec.types.anonymous-records.dynamics-2" }
  "5": { kind: untestable, reason: "The section is a non-functional design rationale for declining an alternative type-system foundation." }
  "6": { spec: "spec.types.anonymous-records.legality-3" }
---

> **Extracted from RFC-0090 (Structural Records — Rows and Tiers) on 2026-07-24**, which
> is superseded by this RFC and five siblings (RFC-0117 Row Narrowing, RFC-0118 Row
> Bounds, RFC-0119 Record Conversions, RFC-0120 Named Records, RFC-0121 Open Rows).
> RFC-0090 had accumulated fourteen open questions and six same-week revision notes while
> bundling six separable features behind one acceptance decision — the pathology
> `PROCESS.md` already names from RFC-0012 ("accumulated 18 open questions before being
> split — most weren't blocking anything, they just made the document read as permanently
> unfinished").
>
> **This is the piece of the cluster with no dependencies at all**, and the reason the
> split is six-way rather than three-way: it can be accepted and implemented today,
> without RFC-0071 (Ownership and Move Semantics, `2-accepted`, 0% implemented), without
> RFC-0076 (Brand Types, `1-under-review`), and without any row-kind or row-unification
> machinery. Everything else in the cluster sits behind one of those.

> **Status — under review (2026-07-24).** Scheduled for v0.12.0 as the records entry point: no dependency on RFC-0071, RFC-0076, or any row kind.

> **Status — accepted (2026-07-24).** OQ1 resolved empirically -- record_lit added to primary_expr, 755 tests green, bare braces parse, if-blocks unaffected, change reverted. Parenthesised conditions make Rust's struct-literal ambiguity structurally impossible. OQ2 scoped out (chained/pattern projection rejected initially). OQ3 reassigned to RFC-0118/0119: an anonymous record has no declaring module, so no private label can leak through it. OQ4 (RFC-0099) is not in this release.

> **Status — integrated 2026-07-24, targeting v0.12.0.** A new "Anonymous Records" section
> is merged into `public/reference/spec/types.md`, placed after Tuples as the labelled
> counterpart to the positional product type, covering the former, exactness, structural
> identity, punning, the usability rules, and projection. Two one-line availability markers
> added.
>
> **Cross-checked against the siblings still in flight for v0.12.0**, per `PROCESS.md`:
>
> - **RFC-0115 (Field Initializer Separator)** — the pairing that put both in this release.
>   With RFC-0115, `Point { x = 1.0 }` is this RFC's `{ x = 1.0 }` plus a path, so the two
>   differ by the brand alone. Shipping either without the other would release a separator
>   mismatch.
> - **RFC-0118 (Row Bounds)** — depends on this RFC and does not conflict. A row *type*
>   here and a row *bound* there both classify with `:`; the open/closed distinction is
>   carried by the trailing `..`, which this RFC does not use.
> - **RFC-0071 (Ownership)** — no interaction. A record is an ordinary owned value; move
>   semantics apply to it exactly as to a struct, and this RFC specifies no narrowing
>   (that is RFC-0117, deliberately out of this release).
> - **RFC-0114 (Construct)** — no conflict. `construct`'s row parameter is a closed record
>   type of the shape this RFC defines.
>
> **One real intersection found, and it is a restriction the spec should carry rather than
> a soundness problem.** `block = { "{" ~ block_item* ~ expr? ~ "}" }`, and
> `if_expr = { "if" ~ "(" ~ expr ~ ")" ~ (block | expr) ~ … }` tries `block` **first**. So
> in any position that admits a block — an if branch, a function body, a loop body — a bare
> `{ x }` is parsed as a *block whose tail expression is `x`*, never as a punned record.
> A function returning a record therefore needs the inner braces:
>
> ```metel
> fun f() -> { x: i64 } { { x = 1 } }   // outer = body block, inner = record
> fun f() -> { x: i64 } { x = 1 }       // NOT a record — tail expr is an assignment
> ```
>
> This is not ambiguity — the alternation order makes it deterministic — but it is a sharp
> edge, and it is the one thing this integration turned up that reading the RFC alone would
> not have.
>
> **Grammar feasibility was settled by building it** (open question 1): `record_lit` added
> to `primary_expr`, 755 tests green, bare braces parsed, if-blocks unaffected, change
> reverted. The reason it is safe is stronger than the RFC first argued — Metel's
> parenthesised conditions make Rust's struct-literal-in-condition ambiguity structurally
> impossible.

> **Status — integrated (2026-07-24).** Anonymous Records section merged into public/reference/spec/types.md after Tuples; two availability markers. Cross-checked against RFC-0115/0118/0071/0114. Grammar feasibility verified by prototype (755 tests green, reverted).

> **Status — implemented (2026-07-25).** Anonymous record types shipped in v0.12.0 (#576, merged e1c0492). Type-former, literals, punning, single projection in expression and type position, structural identity with canonical label sorting, exactness, patterns, Send/Sync composition, and the impl-rejection rules. Two limits recorded in the RFC rather than closed: no local-aspect impls on records (blocked on #581, which affects every structural target) and no impl-based aspect satisfaction at all as a consequence.

## Summary

A closed, anonymous, exact-shape product type written in bare braces: `{ x: f64, y: f64 }`
as a type, `{ x = 1.0, y = 2.0 }` as a value. No keyword, no row variables, no
polymorphism — a record over *N* fields is an ordinary product type with a
compiler-synthesized structural identity, usable anywhere an ordinary type is.

This RFC deliberately specifies **only** the type-former. Narrowing on partial move is
RFC-0117; using a row as a *predicate* is RFC-0118; converting a struct to a record is
RFC-0119; giving a record a name and a brand is RFC-0120; abstracting over the unknown
rest of a row is RFC-0121.

---

## Motivation

Generic code often wants to describe "a value with these fields" without minting a nominal
type for it — a function returning two named results, a configuration fragment assembled
piecewise, the shape a struct exposes when converted. Metel has tuples (positional, no
labels) and structs (labelled, but nominal and declared elsewhere) with nothing in
between.

The narrower motivation, and the reason this is the first thing to build: **every other
feature in the records cluster needs a record type to exist before it can say anything.**
RFC-0090 §3's own recommended build order put the closed type-former at step 1 for this
reason. Splitting it out makes that step independently acceptable rather than gated behind
five features it does not need.

---

## 1. Syntax

```metel
{ x: f64, y: f64 }        // type — a record with exactly these two fields
{ x = 1.0, y = 2.0 }      // value
Handle.{ fd, alloc }      // projection — a receiver's row, narrowed (§4)
```

**Bare braces, no keyword.** Earlier drafts wrote the former as `record { ... }`; the
keyword was dropped on 2026-07-24 because it did exactly one job — mark "this is a row" —
in a position where nothing else can appear. `record` survives only as RFC-0120's
*declaration* keyword, where it mints nominal identity.

**`:` in the type, `=` in the value**, per the separator invariant in
`reports/syntax/colon-classifies-equals-labels-walrus-binds.md`: `:` classifies (`x` *has type* `f64`),
`=` defines (`x` *is* `1.0`). This is also what makes a nominal struct literal, under
RFC-0115, read as this form plus a brand: `Point { x = 1.0 }` is `{ x = 1.0 }` with a name
in front.

**The dot survives only where there is a receiver to project from.** `Handle.{ fd }`
carries it because `Handle { fd }` would collide with `struct_literal`
(`type_path ~ "{" ~ …`); every freestanding position drops it. Full derivation in
`reports/substructural-types/access-and-presence-rows.md` §3.5.

**Label punning.** `field_init`'s value clause is already optional in the grammar
(`ident ~ ("=" ~ expr)?`, since RFC-0115), so `{ x }` — take `x` from the enclosing scope —
is admissible wherever a record literal is.

**But punning does not reach every position, and this is intrinsic, not a bug.** A struct
literal is always prefixed (`Point { x }`), so its leading `type_path` distinguishes it
from a block. An anonymous record drops that prefix, which is exactly the case where a bare
`{ … }` collides with `block`. In any position that admits `(block | expr)` — an `if`/`else`
arm, a `match` arm, a `loop`/function/closure body — `block` is tried first, and a bare
`{ x }` parses as a *block whose tail expression is `x`*, never as the punned record
`{ x: <x> }`. The same is true of `{ x = 1 }`: a block whose tail is the assignment
expression `x = 1`. This is **deterministic, not ambiguous** — the block always wins — but
it means the spec's own punning example works only because it sits in `let`-RHS position:

```metel
let p := { x, y };                     // record: let-RHS is a pure expression position
fun f() -> { x: i64 } { ({ x = 1 }) } // record: parenthesized to force expression position
fun g() -> { x: i64 } { x := 1 }       // NOT a record — block whose tail is `x = 1`
```

Punning and single-field record literals are records in **pure-expression** positions
(`let`/`var` and struct/enum-field initializers, call arguments, array elements, operands,
`return`/`break` operands). In **block-admitting** positions a record must be parenthesized:
`({ … })`. A multi-field literal (`{ x = 1, y = 2 }`) is unaffected — the comma is not valid
inside a block, so it backtracks to the record parse on its own.

## 2. Closed by default, and what that means

A record type names an **exact** shape. `{ x: f64 }` is inhabited only by records with
that row and nothing else; a value of type `{ x: f64, y: f64 }` is not a value of
`{ x: f64 }`.

This is not a limitation awaiting removal — it is what keeps this RFC free of the
machinery the rest of the cluster needs. Width subtyping (silently accepting a wider
record where a narrower one is expected) is the defining move of row polymorphism, and the
one that interacts badly with ownership: a silently-forgotten field that isn't `Copy` is a
leak or worse. RFC-0121 takes that problem up deliberately; closed-by-default sidesteps it
here.

**Structural identity, not nominal.** Two records with the same labels and field types are
the same type, wherever they were written. There is no declaration site and no brand —
that is RFC-0120's job.

**Field order is not part of a record's identity.** `{ x: i64, y: i64 }` and
`{ y: i64, x: i64 }` are the **same type**, and `{ x = 1, y = 2 }` and `{ y = 2, x = 1 }`
are the same value. A record is a label→type map, not an ordered tuple with names; nothing
in the type observes field order, since every access, pattern, and construction is by label.
The implementation gives each record type a **canonical form** by sorting fields
lexicographically by label, and identity, equality, and (on any layout-bearing backend) the
memory layout are all defined over that canonical form. This is not a convenience — it is
forced by the rest of the cluster: RFC-0118's row bounds (`{ x: f64, .. }`) and RFC-0121's
open rows are about *which labels are present*, and would be incoherent if a record's
identity also depended on the order they were written in. Order-insensitivity here is the
same decision, made once at the root so the siblings inherit it.

Duplicate labels in a single record (`{ x: i64, x: f64 }`) are a compile error, not a
last-wins or first-wins rule — the map has no key for the collision to resolve to.

## 3. Where records are usable

**Usable, with no special treatment:**

- **Ordinary value positions** — parameters, returns, `let` bindings, struct and enum
  fields.
- **Allocator-tagged and borrowed positions** — `@a { x: f64, y: f64 }`,
  `&r { x: f64, y: f64 }`. A record is an ordinary owned value and participates in
  `@a T` / `&r T` exactly like a struct.
- **Pattern matching.**
- **Generic instantiation.**
- **Aspect impls, when the aspect is local to you** — reusing RFC-0061's orphan-rule
  treatment of `T[]`, tuples and function types directly.

  > **Not available as of v0.12.0 — the design precedent exists, the implementation does
  > not.** `extend { w: i64 }: LocalAspect { … }` fails, and so do `extend (i64, i64):
  > LocalAspect` and `extend i64[]: LocalAspect`: RFC-0061's structural impl targets are
  > unimplemented for *every* structural type, not just records. Verified 2026-07-25 while
  > reviewing #576 — all three produce the same error, so records inherit an existing gap
  > rather than introducing one. Tracked as **#581**, which also covers the fact that the
  > failure is an internal error rather than a diagnostic.
  >
  > **Consequence for records specifically:** this is the *only* impl-based capability §3
  > grants them, so as shipped a record can satisfy no impl-based aspect at all — not just
  > no stdlib one. The `Copy`/`Display` note in §2 describes the non-local half of that;
  > this is the other half, and it closes when #581 does.
- **Auto-derived aspects** — `Send` and `Sync` extend to records by the same
  field-composition rule already used for structs.

**Not usable, and why:**

- **Inherent impls.** A record has no nominal owner for orphan-rule purposes, so two
  unrelated modules could write conflicting inherent methods for the same shape with no
  principled way to say which wins.
- **Aspect impls for a non-local aspect** — the same rule, other direction.
- **Custom `Drop` logic specifically.** `Drop` is a stdlib aspect, never local to ordinary
  user code, so no record can carry custom teardown. Only nominal types can.

> **Consequence of the two aspect rules above, recorded 2026-07-24 because the restrictions
> were stated without it: an anonymous record cannot satisfy *any* standard-library aspect.**
> `Display`, `From`, `Iterable` are all non-local, so no user module may implement them for
> a record, and stdlib cannot enumerate every shape. Concretely, `println("${p}")` does not
> work for `let p = { x = 1.0, y = 2.0 }`.
>
> **Auto-derived aspects are unaffected** — `Send`, `Sync` and `Linear` are computed from
> field composition (RFC-0096) rather than declared, so records satisfy them structurally.
> The gap is specifically *impl-based* aspects.
>
> **`Copy` is impl-based, so no record is ever `Copy`** — found 2026-07-24 while cross-checking
> RFC-0071. RFC-0096's auto-impl set is a closed list of exactly three (`Send`, `Sync`,
> `Linear`); `Copy` is declared with `extend T: Copy;` (RFC-0071 §2). **Every record is
> therefore affine and must be moved**, including `{ x: i64, y: i64 }`. This is sharper than
> the `Display` case — a small all-primitive record is exactly what a reader expects to copy
> freely — and it also blocks RFC-0121's width-subtyping rule for any dropped field that is
> itself a record. Same fix, RFC-0123.
>
> **The fix is a single stdlib implementation covering all rows at once**, which requires
> constraining every field of a row (`extend<row R> { ..R }: Display where all R: Display`).
> That construct does not exist and is now **RFC-0123 (Field-Wise Row Constraints)**, which
> depends on RFC-0121 — so neither is in v0.12.0. **This is a real usability limit of
> records as first shipped**, and it is stated here rather than discovered later.
>
> **RFC-0121 is therefore load-bearing for this RFC, not merely adjacent.** It is easy to
> read as an optional convenience — RFC-0090 §3 scheduled it "only if a real duck-typing
> need materializes" — but records being usable with stdlib aspects at all runs through it.
> See RFC-0121's own header for the two further things that turn out to depend on it.
- **Serving as an allocator type.** RFC-0063 §2's disjointness story requires allocator
  identity to be per-*instance*, while a record's premise is that two values with the same
  row are interchangeable. A category mismatch, not a coherence technicality.

## 4. Projection: `Handle.{ fd }`

A nominal type's row, narrowed to named fields. Specified here because it is syntax over
an existing type — but note what it does **not** settle: projection yields a record type;
whether the *original* value's type changes as a result is RFC-0117's question, and
whether the result carries the source's brand is RFC-0120's.

A bare identifier inside projection braces is always a **field label**, never a row
variable. That rule exists because the two were genuinely ambiguous before the `..` marker
was adopted — `Handle.{ fd }` and `Handle.{ R }` were separated only by case convention,
which would have made the design depend on RFC-0101 (`0-draft`) to disambiguate. Row
variables are written `..R` and belong to RFC-0121.

## 5. Considered and declined: a fully record-based type system

> **Coverage: untestable** (see frontmatter). This section records a design decision,
> not independently observable language behavior.

Whether records should stop being an *addition* alongside nominal types and become the
foundation everything reduces to — nominal types as sugar over an underlying record.
Declined, and recorded here because this RFC is where someone would next propose it:

- **Enums don't fit.** Records are products; enums are sums. A records-only foundation
  needs a separate structural mechanism for sum types ("variant rows") with a well-known
  cost: materially weaker exhaustiveness checking, since the compiler cannot always know
  the full set of tags for an open variant. Metel's enums lean on closed-world
  exhaustiveness as a real property; trading it for uniformity is a regression.
- **Primitives don't fit either.** `i64` as a one-field record is indirection with no
  payoff.
- **Nominal identity can't become sugar — it's load-bearing.** §3 already establishes that
  records can't be allocators and can't carry inherent or non-local aspect impls. If
  structs were sugar over records, the sugar would have to reintroduce a real identity tag
  for any of that to work — at which point nothing has been reduced, only renamed.
- **Cost for the common case.** Routing every ordinary struct through record machinery
  makes the majority of code that never writes `{ … }` pay for it.

**Verdict:** records as the natural representation for structural, identity-free data —
yes. Records as the universal foundation — no. A live exploration pushing the other way
(`reports/substructural-types/nominal-types-as-branded-rows.md`) is deliberately kept as an
exploration and does not gate this RFC.

---

## 6. Diagnostics

Most of this RFC's user-facing surface is *rejection*, and rejections are only as good as
the message. Each is specified here so the implementation has a target rather than a
generic type error to fall back on.

**No special diagnostic for the block-position collision (§1).** An earlier draft specified
one — "this `{ … }` is being parsed as a block, not a record; wrap it in parentheses." It was
**dropped 2026-07-24 during implementation**, because a diagnostic that fires reliably and
only on the mistake turns out not to exist at the type-checking phase. To detect the shape
after inference, inference must first *accept* the block's tail against the expected record
type — which happens exactly when the tail genuinely is that record and returning it is
correct, so the diagnostic fires on valid code (`fun f() -> { a: i64 } { let r = ({ a = 1 });
r }`). When the tail is not that record, inference reports an ordinary type mismatch first and
the diagnostic never runs. Either unreachable or a false positive. The block-position rule
itself (§1) stands; the collision simply surfaces as the ordinary type error. A parse-time
heuristic could revisit this later, but it is out of scope here.

**The four "no nominal owner" rejections** (§3) each name the missing capability and point
at the one fix available in v0.12.0 — declare a nominal type — since RFC-0119's
`.to_record()` and RFC-0120's `record X` are not in this release:

| attempted on a record | message |
|---|---|
| inherent method (`extend { x: f64 } { fun … }`) | anonymous records cannot have inherent methods; declare a `struct` if you need methods |
| non-local aspect impl (`extend { … }: Display`) | `Display` is not local to this module and cannot be implemented for an anonymous record; declare a `struct` and implement it there |
| custom `Drop` | anonymous records cannot implement `Drop`; teardown logic requires a nominal type |
| used as an allocator (`@r` where `r: { … }`) | an anonymous record cannot be an allocator; allocator identity is per-instance (RFC-0063 §2) |

The `Copy`/`Display` usability gap (§2 note) is *not* an error to improve here — a record
simply does not satisfy those bounds, and the fix is RFC-0123, out of this release.

---

## Open Questions

Carried from RFC-0090, narrowed to what this RFC owns.

1. ~~Does bare `{ … }` survive contact with the rest of the grammar?~~ **Resolved
   2026-07-24 by building it, not by reading.** A `record_lit` alternative was added to
   `primary_expr` ahead of `struct_literal`, the interpreter rebuilt, and the change
   reverted afterwards. Results:
   - **The full suite stayed green — 805 passed, 0 failed.** The alternative breaks nothing
     that exists.
   - **`{ x: 1, y: 2 }` parses.** The resulting failure is
     `parse_expr: unexpected rule record_lit` — a missing AST branch, i.e. the grammar
     accepted it and only the not-yet-written parser arm is absent. That is the expected
     state and the positive result.
   - **`if (n > 1) { … }` still parses as a block**, in the same file as a bare record.
   - **`block_expr_stmt`'s `!"}"` lookahead**, called out as unchecked, is unaffected.

   **The underlying reason is stronger than this RFC originally argued.** The difficulty
   everyone expects is Rust's — `if x == Foo { }` is ambiguous because the condition is
   unbracketed. **Metel requires parenthesised conditions**: `if ( expr )`, `while ( expr )`,
   `for ( … )` (`grammar.pest:137-142, 239`). The brace after `)` is therefore always the
   block and never a literal, so the ambiguity motivating Rust's restriction is
   structurally impossible here. The safety is a property of the condition syntax, not a
   lucky absence of collisions.

   **One residual collision, now specified rather than open:** a bare `{ x }` or `{ x = e }`
   in a *block-admitting* position (an `if`/`else`/`match` arm, a function/closure/loop
   body) parses as a block, not a record — deterministically, block-first. This is not the
   Rust condition ambiguity; it is block-versus-expression precedence, resolved by
   parenthesizing (`({ x })`). §1 states the rule normatively; this question is closed, not
   reopened. (§6 records why no dedicated diagnostic accompanies it.)
2. **Chained projection (`S.{ a }.{ b }`) and projection in pattern position** are
   unspecified — **scoped out of v0.12.0 rather than left ambiguous.** Both are rejected by
   the initial implementation; a single projection in type or expression position is the
   whole of what ships. Neither has a use case in the cluster today, and admitting them
   later is additive. Recorded as a deliberate restriction so the implementation has a
   definite answer rather than an open one.
3. **Field-level visibility (RFC-0032) and structural typing are unreconciled** — **but
   not for this RFC, which is why it does not block acceptance.** The question as inherited
   reads "if a record type mentions a label private to *its declaring module*…", and an
   *anonymous* record has no declaring module: it is written inline and derived from
   nothing. A private label can only leak into a row when the row comes *from* a nominal
   struct, which happens in RFC-0118 (a bound matching a struct's row) and RFC-0119 (a
   conversion producing one). Reassigned there; RFC-0114's open question 8 depends on
   their answer, not on this RFC's. *(From RFC-0090 OQ7, narrowed twice.)*
4. **Interaction with RFC-0099 (Dot-Separated Module Paths), `1-under-review`.** If it
   lands, `.` both separates module paths and projects a record, so `Handle.{ fd }` sits
   beside `mod.Handle`. Still unambiguous — a `{` cannot start a path segment — but the
   two RFCs do not currently know about each other.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` — the RFC this is extracted
  from: §2 (the type-former), §3 step 1 (build order), §5 (usability rules), §6 (the
  declined records-as-foundation reframing)
- RFC-0117 (Row Narrowing), RFC-0118 (Row Bounds), RFC-0119 (Record Conversions),
  RFC-0120 (Named Records), RFC-0121 (Open Rows) — the five siblings, each depending on
  this RFC
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the row-former syntax
  derivation, including why the dot survives only for projection
- `reports/syntax/colon-classifies-equals-labels-walrus-binds.md` — the `:` classifies / `=` defines
  invariant fixing the type/value separators
- RFC-0115 (Field Initializer Separator) — makes a nominal struct literal read as this form
  plus a brand; independent in both directions
- RFC-0061 (Structural Aspect Bounds) — the orphan-rule treatment §3 reuses
- RFC-0063 (Allocator Handles) §2 — the disjointness story ruling records out as allocator
  types
- `reports/substructural-types/structural-records.md` — the living exploratory report
  RFC-0090 was extracted from; **not superseded**, per `PROCESS.md`, and still carrying
  pre-2026-07-24 syntax throughout

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
