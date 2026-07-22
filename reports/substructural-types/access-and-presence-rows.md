---
id: access-and-presence-rows
title: "Access Rows and Presence Rows: What Views Share With Records, and What Connects Them to Effects"
type: report
status: active
last_synced_against_model: '2026-07-22'
supersedes: null
revives: null
---

# Access Rows and Presence Rows

*Written 2026-07-22, out of a design conversation about whether the records cluster
should be built from structural records downward or from views upward. It does not
resolve that question. It distinguishes two things the cluster currently names alike —
which fields a value **has**, and which fields a computation **touches** — and then finds
that most of the distinction dissolves into one mechanism, leaving a much smaller residue
that is the part actually worth arguing about.*

*Revised the same day, after the desugaring in §3 was proposed against the first draft.
The first draft claimed four rules had to differ between the two; three of them do not.
The revision is kept visible rather than smoothed over, because which arguments survived
is the useful part.*

**Framing note.** Metel is an experimental language: its purpose includes exploring
design ideas that are interesting before they are proven necessary. Several arguments
below would read as "defer this" under a production-language filter and are deliberately
not written that way. Where the evidence is "no one has needed this yet," that is
recorded as what it is — an absence of external demand, not a verdict — and the
interesting-if-unproven reading is given its own hearing.

---

## 1. The claim

Two distinct row concepts appear in this cluster under one name:

- **Presence rows** — *which fields a value has.* RFC-0090's `record { ... }`
  type-former, RFC-0091's partial-consumption residual, row-conditional typestate.
- **Access rows** — *which fields a computation touches.* RFC-0109's named views,
  RFC-0091 §1's `uses (fd)` declaration on `Drop`, and everything Rust calls view types.

They are related but they are not the same claim, they have different costs, and — the
substantive point — **the access side is the one that connects to effects**, which is
where its unsolved problem already lives.

**How much of a split this is, is §3's subject, and the answer is "less than it looks."**
Views desugar to ordinary presence rows whose field types are borrows, which dissolves most
of the difference. What remains is one coercion rule, one decision about nominal identity,
and one case that genuinely does not desugar — `uses (…)` over an owned value, which is
where §4's effect connection attaches.

---

## 2. Where the corpus currently merges them

The merge is explicit and deliberate in the current drafts. §3 finds it largely *right* —
the interest is in which parts of it are, and which one part isn't.

**RFC-0109 defines named views in terms of presence rows.** Its header states the
dependency directly: it "depends on RFC-0090 (Structural Records) for the `record { ... }`
vocabulary and RFC-0091 (Linear Records) for the `(row, brand)` representation," and §4
gives a view's meaning as `(row: { golden_tickets: Token }, brand: brand_of(Ticketing))`,
"a *named point* in that same lattice, reached non-consumingly (borrowed) rather than by
move."

**Its second mechanism is not.** RFC-0109's reference-destructuring patterns
(`let &mut { a, b } = h;`) are, in the RFC's own words, "deliberately **not** built on
RFC-0090's" machinery — they are ordinary sequential field borrows performed in one
place. So RFC-0109 already contains one access-side mechanism that needs no presence
rows at all, sitting beside one that is defined through them.

**`uses (fd)` is an access row filed under presence.** RFC-0091 §1 lets a `Drop` impl
declare which fields its body depends on, and specifies its meaning in presence terms —
which fields may be *moved out* before `drop` runs, with the residual required to still
satisfy what `drop` needs. The declaration is about access; its specification is about
presence.

---

## 3. Views desugar to rows of borrows

The obvious objection to §1: if access rows are presence rows whose labels are restricted
to fields that exist on the referenced struct, why are they a separate concept at all?

The strong form of that objection is a **desugaring**, and it mostly works. Read
`&mut Handle.{fd, alloc}` as

```metel
record { fd: &mut i32, alloc: &mut Buffer }
```

— an ordinary presence row whose *field types* are references. This document's first draft
argued that four rules had to differ between the roles. Three of them, and the single
difference the other three were derived from, evaporate under this reading. That draft was
overstated and is corrected here.

### 3.1 What the desugaring dissolves

**The complement.** The first draft's central claim was that fields outside a presence row
do not exist, while fields outside an access row are live and possibly in use elsewhere —
and that everything else followed from it. Under the desugaring the tension is gone,
because a record of borrows is a **separate value** from the struct it was taken from.
Fields it omits are not "gone"; it simply doesn't mention them. That is the correct
reading, obtained for free rather than by a special rule.

**`Drop` and multiplicity.** The fields are references, and references carry no drop
obligation, so RFC-0090 §5's field-composition rule computes "drops nothing" by itself. No
derivation has to be suppressed for the access role. `Send`/`Sync`/`Linear` likewise
compose to the right answers, because `&T`/`&mut T`'s own status is already right.

**Modes — and here the desugaring is an improvement on RFC-0109, not merely a
simplification.** It puts the mode *inside* the row, in each field's type (`&T` versus
`&mut T`). RFC-0109 puts it *outside*, on the view reference (`&TicketView` /
`&mut TicketView`), which is exactly why it needs §4.9's tuple-of-views-with-independent-
modes as a separate construct to express mixed access. With the mode in the field type,
mixed modes are just a record with mixed field types, and §4.9's construct is unnecessary.

**Cardinality.** Many records of borrows coexist, each being its own value. There is no
"two rows over one value" compatibility relation left to define.

The desugaring also **unifies RFC-0109's two mechanisms**, which that RFC deliberately
keeps apart: reference-destructuring *produces* the record of borrows, and a named view
*names its type*.

### 3.2 What survives

**1. Call-site coercion — the one that matters.** For `h.should_insert_ticket()` to work
with no call-site syntax, `&mut Handle` must coerce implicitly to
`record { golden_tickets: &Token }`. RFC-0090 §8 forbids precisely that: a struct "must
never be silently accepted wherever a row-generic bound is expected — `.to_record()` has to
appear in the source," because allowing it "would quietly re-widen tier 2 into tier 3
without the type author having asked for it."

This is not incidental; it is RFC-0109's stated reason to exist. Its motivation says that
rule "is exactly what stands between Metel and view types' actual headline benefit: calling
an ordinary method while another field is separately in use, with **zero new syntax at the
call site**."

The desugaring does not remove that problem. It **relocates** it — from "views need their
own semantics" to "views need one coercion rule that tier 2 explicitly bans." That is a
better place for it to live: one rule to argue about, in one document, rather than a
parallel mechanism.

**2. Nominal identity becomes a live choice again.** A bare record of borrows carries no
brand, so two unrelated structs with matching field names and types produce the *same* view
type. That is either the reusability win (one helper working across structs, §6) or the
silent-nominal-collapse failure the tier system exists to prevent — depending on whether
views should be structurally satisfiable. RFC-0109 chose branded specifically to prevent
it, noting the brand "is exactly what prevents it from ever satisfying a *generic*
structural bound the way an anonymous record could." The desugaring reopens that as a
decision rather than settling it — **§3.4 maps the options, which are not the binary this
paragraph implies.**

**3. `uses (fd)` does not desugar.** `fun drop(self: Handle) uses (fd)` takes `self` **by
value**. There is no borrow to encode as a field type; the declaration constrains which
fields the body may read, so that *other* fields may have been moved out beforehand. This
is an access constraint over an owned value, and nothing in the desugaring reaches it. §2's
observation stands unchanged for this case, and it is the case §4 is really about.

**4. Disjointness is proved elsewhere.** Constructing `record { a: &mut A, b: &mut B }` from
one `&mut h` requires knowing `a` and `b` are disjoint paths. That is the borrow checker's
obligation, not the row solver's — RFC-0109 defers it to "ordinary sequential field
borrows" once RFC-0071's field-sensitive tracking exists. The desugaring makes the *result*
typeable without making the *construction* checkable.

### 3.3 A guard in RFC-0090 that borrows pull apart

Independently of the above, pushing views through presence rows exposes an inconsistency
worth fixing. RFC-0090 states its width-subtyping guard twice, and the two disagree:

- §7: "width subtyping is only sound when every silently-dropped field is `Copy`; anything
  `Drop`- or `Linear`-bearing forces explicit handling."
- §5 rejects discarding a row remainder "without a guarantee everything in it is `Copy`."

`&mut T` is **not `Copy`**, and also not `Drop`- or `Linear`-bearing. Forgetting one is
entirely safe — it ends a borrow early. So the `Copy` guard is strictly stronger than the
hazard used to justify it, and a row of borrows is exactly the case that separates them.
The right guard is **"carries no drop obligation," not "`Copy`."**

Under the `Copy` phrasing, narrowing a record of borrows would be rejected — which would
break the desugaring's most common operation (passing a `{a, b}` record where `{a}` is
wanted). Under the §7 phrasing it is fine.

### 3.4 What identity should a view carry?

§3.2 leaves this open. It is the sharpest of the surviving questions, and it is not the
binary it looks like.

**Inheriting the source struct's brand already has precedent in this cluster**, narrowly
scoped: RFC-0090 §8's "Exception: a fiat-linear source struct's `ToRecord` output carries
its origin brand, not a bare row." RFC-0109's `(row, brand)` view is the same idea again.
So "the desugared record inherits the struct's brand" generalizes an accepted mechanism
rather than introducing one — a row of borrows can carry a brand exactly as a row of
values can.

But inherit-or-not is a false binary. The space:

| | View type | Reuse across structs | Prevents collapse |
|---|---|---|---|
| **A** Bare | `record { fd: &mut i32 }` | ✓ free | ✗ |
| **B** Brand-rigid *(RFC-0109 today)* | `record {…} @ brand_of(Handle)` | ✗ | ✓ |
| **C** Brand-polymorphic | `record {…} @ 'b`, generic in `'b` | ✓ | ✓ |
| **D** Nominal constructor | `View<Handle, {fd}>` | ✓ via `View<S, R>` | ✓ |
| **E** Branded identity + structural *bounds* | B, accepted via `HasField` bounds | ✓ in bound position | ✓ |
| **F** Inherit, with explicit erasure | B, plus an explicit "forget the brand" step | ✓ when asked | ✓ by default |

**C beats both extremes rather than trading between them.** With identity as a
*parameter*, a helper can be generic over which struct a view came from **and** can require
that two views came from the *same* value — `f<'b>(x: record { a: &mut A } @ 'b, y: record
{ b: &mut B } @ 'b)`. Neither extreme expresses that: bare rows cannot distinguish two
structs, rigid brands cannot abstract over them. "Two views of the same value" is exactly
the property disjointness and reassembly reasoning needs.

**D is C with machinery that already exists.** If a view is a nominal constructor
parameterised by source struct and row, the identity is an ordinary type parameter and
nothing depends on RFC-0076, still `0-draft`. Narrowing becomes `View<S, R - name>` — the
shape RFC-0091's `drain_field<row R, name, T>` wants, and far more readable than the same
operation on a bare record. Its one cost is a type-level field lookup (given `S` and label
`fd`, what type?), which is what `HasField<"fd", T>` already provides — expressible, not new.

**E applies a distinction RFC-0090 has already resolved.** §7 concluded that
`HasField`/`Lacks` in *bound* position stays implicit "because a bound alone grants no new
capability *over the type itself*; it only lets a generic function accept it," while the
tiers gate capability that changes what a type can do on its own. Applied here: give the
view a branded identity, and let generic helpers accept it structurally *via bounds*. Both
properties, no new mechanism, consistent with a question this RFC already settled.

E's limit is real: it serves helpers that **consume** a view, not ones that **return a
narrowed** view, since a narrowed return type needs a row operation. So D and E are layers,
not competitors — D for transforming helpers, E for consuming ones.

**The argument for inheriting identity that is not about hygiene: reassembly.** RFC-0090 §8
currently types `from_record_mut` purely structurally — the row must "have already grown
back to `Handle`'s exact full shape… so there is nothing beyond structural row-matching to
check." That means *any* view of matching shape can be reassembled into a `Handle`, which
is precisely the hole RFC-0090's **open question 10** names: `FromRecord` bypassing a
constructor's invariants (the `SortedPair` case), with "no compile-time check for this
proposed."

Inherited identity closes it for the borrowed case: `Handle::from_record_mut` can require
the view's identity to *be* `Handle`'s, so only what was taken apart can be put back
together. **The identity question and open question 10 are therefore the same question**,
which neither RFC currently says.

**Leaning: D, with E as the bound-position complement**, and F retained as the escape hatch
whichever wins — erasing to a bare structural row should be something written, not
something that happens, per RFC-0065's "elision is never a silent choice." Reach for real
brands (B/C) only if something forces it; the likeliest forcing case is `RcBox`
(RFC-0091 §1.1), where the residual outlives the borrow and is reached through many
handles.

### 3.5 Surface syntax: one row former, one declaration form

Superficial on its face, but the choice interacts with §3.4 rather than merely decorating
it. **Design decision taken 2026-07-22: wherever a row appears as a type or a value — an
anonymous record, a view type, a view value — it is spelled the same way.** `.{ … }` is the
row former; a prefix says what to project from, and its absence means "free-standing."
Declaring a *named* record is a declaration, not a type expression, and joins the
`struct`/`enum`/`aspect` family instead.

```metel
.{ x: f64, y: f64 }     // anonymous record type
.{ x = 1.0, y = 2.0 }   // anonymous record value (§3.6's separator invariant)
Handle.{ fd, alloc }    // view type — project Handle's row
h.{ fd, alloc }         // view value — project the value h

type   X = .{ … }       // alias — structural, no new identity (§3.4 option A)
record X { … }          // declaration — new identity carrying the row (§3.4 option D)
```

**What uniformity buys, beyond consistency:**

- **It answers RFC-0090's open question 8** — "What syntactically marks tier 3, the named
  record kind — a separate keyword vs. a modifier on `struct`? Not decided." It takes the
  first: a `record` declaration sits in the same family as `struct`, `enum` and `aspect`,
  since it does the same job of minting a nominal type.
- **`type` versus `record` becomes the identity switch**, turning §3.4's question into a
  choice visible at the declaration site rather than a rule stated elsewhere:
  `type X = .{ … }` binds a name to a row and mints nothing, while `record X { … }` mints
  identity. The two *look* as different as they are, rather than differing by one token.
- **Anonymous records and views become one construct**, prefixed or not, rather than two
  that happen to share a delimiter.
- **Label-only entries are already how Metel works.** `Handle.{ fd }` lists labels without
  types because the types come from `Handle`; `grammar.pest:245`'s
  `field_init = { ident ~ (":" ~ expr)? }` already makes the `:` part optional, so `Handle
  { x }` punning exists today. The general rule — *a bare label means "take it from
  context"* — is a generalization, not a new mechanism.
- **`h.{ fd, alloc }` gives RFC-0109 an expression form it currently lacks.** That RFC has
  named views and destructuring patterns, but no way to say "make me a view of these fields
  right here."

**Why the leading dot, when bare braces would also work.** Both halves are borrowed rather
than invented — Zig spells anonymous struct literals `.{ … }`, Rust spells view types
`Foo.{a}` — but the operative reason is **independence**. `struct_literal = { type_path ~
"{" ~ … }` already occupies the prefixed bare-brace form, so a bare-brace record syntax
would only be clean once RFC-0100 removes struct literals, and RFC-0100 is itself
`1-under-review` with its future uncertain (`OBJECTIVES.md` Trigger 14). The dot lets
`Handle { … }` and `Handle.{ fd }` coexist indefinitely, so the record syntax can be settled
now and stay settled regardless of how RFC-0100 resolves. **Deliberately chosen as the
lower-dependency option while the semantics are still moving.**

**Feasibility, verified against `grammar.pest`:**

- Nothing starts with `.` in expression position — float literals require digits on both
  sides (`ASCII_DIGIT+ ~ "." ~ ASCII_DIGIT+`), and `range_expr = { add_expr ~ (range_op ~
  add_expr)? }` needs a left operand, so there is no prefix `..`.
- Nothing starts with `.` in type position either — `type_expr`'s alternatives begin with a
  path, `(`, `&`, `[`, `impl`, or `!`.
- Postfix `.` accepts only `.0`, `.ident(…)` and `.ident`, so `.{` is free for projection.
- Pest is scannerless, so no maximal-munch tokenisation hazard is inherited.

**Where the dot applies, and where it does not.** `.{ … }` marks a row appearing in *type
or expression position*, where it must be told apart from a block and from a struct literal.
A **declaration** is not either of those: `record X { … }`'s braces are a field list, the
same as `struct X { … }`'s, and the type being declared is spelled `X`. So the declaration
form takes no dot and no `=`, and this is not a second spelling of the same thing — there is
no type expression there to spell twice.

**The accepted cost is narrower than that:** the dot is still noise in a type annotation
that could not be ambiguous, such as `let r: .{ x: f64 }`. Dropping it *there* would mean
one type written two ways depending on position, which is the case worth paying a character
to avoid.

**Options considered and set aside:**

| Form | Status |
|---|---|
| bare `{ … }` | **would work, and is the upgrade path** — see below |
| `#{ … }` (Erlang/Clojure) | `#` is genuinely unused in the whole grammar, but projection reads badly |
| `record { … }` (RFC-0090 as drafted) | verbose, and **fails uniformity** — `Handle.record { fd }` is unusable |
| `{\| … \|}` (F#) | F# needs it because nominal literals occupy plain braces; that motivation does not transfer, and it is heavier than the dot |
| `_.{ … }` | prefix always present, marginal uniformity gain, more noise |
| `( … )` | collides three ways — tuple type, parenthesized expression, parenthesized ascription |
| `[ … ]` | collides with array and sized-array types |
| `<: … :>` | collides with the `<…>` compile-time parameter channel that RFC-0090 §2 invokes for `<row R>`; also C's digraphs for `[` and `]` |

**Bare `{ … }` as a later simplification, and the finding that makes it possible.** A bare
block is **not an expression** in this grammar: the primary alternation (lines 196–208)
lists `closure_expr`, `match_expr`, `if_expr`, `loop_expr`, `struct_literal`, `path_expr`
and friends, but no `block`. Blocks appear only in dedicated slots — function and closure
bodies, and `(block | expr)` in `if_expr` and match arms, where `block` is tried **first**.
So bare braces would collide with nothing, and the entire cost would be that an anonymous
record literal used as an *unparenthesized* if-branch or match-arm body needs parens.

Worth recording because it is not obvious and it is a real, if accidental, advantage over
Rust — Metel can afford bare-brace records precisely because it chose not to make blocks
first-class expressions. **If RFC-0100 lands and removes struct literals, dropping the dot
becomes a purely mechanical simplification** with no semantic consequence. Until then the
dot costs one character and buys freedom from that dependency.

**Remaining condition:** this was decided from grammar reading, not from a built prototype.
Chained projection `S.{ R }.{ R' }`, projection in pattern position, and any interaction
with `block_expr_stmt`'s `!"}"` lookahead are unchecked.

*Elsewhere this document keeps RFC-0090's current `record { … }` spelling, since the
syntax question is separable from the semantic one.*

**Interaction to watch: RFC-0099 (Dot-Separated Module Paths), currently `1-under-review`.**
If it lands, `.` separates module paths *and* projects a record, so `Handle.{ fd }` sits
next to `mod.Handle`. Still unambiguous (a `{` cannot start a path segment), but it makes
`.` carry two unrelated jobs, and the two RFCs do not currently know about each other.

*Correction, same day.* An earlier version of this section claimed a type/value ambiguity
in `record { x: f64 }` versus `record { x: 1.0 }`. **There is no such ambiguity.** Types and
values occupy disjoint nonterminals, and `field_init` already matches `ident ~ ":"` directly
rather than routing the field name through `expr` — which is why today's struct literals do
not collide with type ascription. The real collision in this area is ascription against
*keyword arguments*, which arises only where contents route through a general `expr`
(`arg_list`); RFC-0100 §3 analysed and fixed it, and that analysis generalizes into the
separator invariant recorded in `../syntax/colon-classifies-equals-defines.md`.

### 3.6 Revised resolution

Presence rows are the mechanism. **"Access row" names a *use* of that mechanism** — a row
whose fields are borrows — plus exactly two things the desugaring forces into the open: a
call-site coercion rule (§3.2), and what identity the view carries (§3.4, leaning toward a
nominal `View<S, R>` constructor rather than a brand, since it needs nothing from
RFC-0076 and makes narrowing and reassembly both expressible). §3.5 proposes a surface
syntax in which those two identity choices are two different spellings, so erasing one to
the other is visible in the source.

One case stays genuinely outside it: **access declared over an owned value**, which is
`uses (…)`, and which is where the transitivity problem lives. That is the subject of §4,
and the narrowing of scope is a gain — the effect connection now attaches to the one case
that actually needs it, rather than to views generally.

The shared-representation argument from the first draft still holds, and is now stronger
rather than weaker: not two roles over one solver, but **one row mechanism whose field
types carry the distinction**. `brand-kind-unification.md`'s "one kind, several roles"
precedent is therefore *not* needed here — a simpler answer was available.

---

## 4. Access rows are effect rows

The framing this document proposes: **an access row is a statement about what a
computation does, over a finite label set.** That is the same shape as an effect row.

**Scope, after §3.** Where a view is a parameter — Rust's `&mut self.{statistics}`,
RFC-0109's named views — the desugaring to a row of borrows already handles propagation
without any of this: the callee's access is *its parameter type*, so it composes through
calls the way ordinary types do. The effect framing earns its keep for the case the
desugaring does **not** reach, which is access declared over a value held **by value**:
`uses (…)`. That narrowing is a gain, not a retreat — it is the case where the problem is
actually open.

| Mechanism | Reads as | Covered by §3's desugaring? |
|---|---|---|
| Rust's `fn process(&mut self { statistics })` | this function's field-access row is `{statistics}` | yes — parameter type |
| RFC-0109's named view | a named access-row alias | yes — a named row of borrows |
| Rust's *abstract fields* (trait members) | row variables over access rows | partly — needs a public projection |
| RFC-0091 §1's `uses (fd)` | the destructor's access row | **no** — `self` is owned |
| **transitivity through helper calls** | **effect-row propagation** | **no** — the open problem |

The last line is the payoff, and it is not a new problem invented here. RFC-0091 §1
lists it as unresolved:

> **Not resolved:** if `drop`'s body calls a helper method, "what does this actually
> touch" has to become transitive across that call — either the helper needs its own
> declared field-usage that composes through, or field-usage becomes a real effect
> system (possibly an application of `algebraic-effects.md`'s already-planned effect
> system rather than a fourth new mechanism).

That parenthesis is the whole thesis of this document, filed as a hazard rather than as
a design direction. Propagating "what does this call touch" up a call graph is precisely
what effect systems do; it is the *only* thing in this cluster whose obvious solution is
already specified elsewhere in the same directory.

**Metel's effect annotation is already row-shaped in all but syntax.** `algebraic-effects.md`
§13.4 records that the current design uses `^ {E}` with a type variable for effect
polymorphism, achieving what Koka's open effect rows achieve, and flags making the
open/closed distinction syntactically explicit (`{IO}` vs `{IO | E}`) as a Koka borrow
worth taking — rated "low cost, medium value" in §13.6's priority table. Effects
themselves desugar to aspects (§8), so this is a surface-syntax question, not a change of
foundation.

**The honest asymmetry**, stated because it is the strongest objection to the framing:
an effect row ranges over an open world of effect labels, while a field-access row ranges
over one struct's finitely many declared fields. They are not the same kind, and this
document does not claim they should share an implementation. The claim is narrower — that
they share the *problem structure* (declare a set, propagate it through calls, abstract
over it at boundaries), and that the field-access case is the better-behaved one.

---

## 5. Prior art, verified

Checked directly rather than recalled. Two claims made earlier in the originating
conversation were **wrong and are corrected here**.

### Rust converged on fixed field sets, over five years

[View types (2021)](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
→ [view types redux and abstract fields (2025)](https://smallcultfollowing.com/babysteps/blog/2025/02/25/view-types-redux/)
→ [maximally minimal view types (March 2026)](https://smallcultfollowing.com/babysteps/blog/2026/03/21/view-types-max-min/)
→ [tracking issue #155938](https://github.com/rust-lang/rust/issues/155938), experimental
as of April 2026.

The design being implemented is `&mut Foo.{a}` — **fixed named field sets, no
polymorphism**. Row polymorphism is named as a possible future technique for field-set
*inference*, not as part of the design. The [Notes on partial borrows](https://internals.rust-lang.org/t/notes-on-partial-borrows/20020)
thread, read specifically looking for counterexamples, contains **no** motivating example
requiring genericity over field sets; every one names concrete fields.

Two of its deferrals are worth naming because Metel has the same ones open:

- **`pub` is a hard error in the MVP.** Rust's stated concern — *"does this mean that the
  names of our private fields become part of our interface? That seems obviously
  undesirable"* — is, word for word, RFC-0090 §9's open question 7 (private-field leakage
  into cross-module structural matching). Independent convergence; the RFC found it
  unaided.
- **"View groups are not considered at the moment."** Named field sets, deferred.

Rust's eventual answer to the encapsulation problem is *abstract fields*: a public
symbolic name for a private field set, declarable as a trait member, with different impls
mapping it to different underlying fields. **That is a named indirection, not a row
variable** — and it is approximately RFC-0109's named view.

### Linear types and rows do coexist in prior work — correction

An earlier claim in the originating conversation, that no prior work combines linear
types with row polymorphism, is **false**. [Lindley and Morris's *Lightweight Functional
Session Types*](https://homepages.inf.ed.ac.uk/slindley/papers/fst-extended.pdf) (FST)
extends GV with polymorphism, row typing (for extensible records, variants, *and* session
types), and a subkinding system explicitly to integrate linear and unlimited types.
[Ferrite](https://arxiv.org/pdf/2205.06921) embeds session types in Rust using extensible
sums and products.

What those systems do is not what this cluster proposes. In FST, rows describe
**extensibility** — of records, variants, and protocol choice — while linearity is a
**kind-level property of whole values**. Rows and linearity coexist; rows do not track
linearity *within* a value.

**The narrower claim, which searching did not falsify:** no prior work found uses a row to
track the **partial consumption of one value's fields** — the row shrinking as individual
fields are moved out, with the residual as a first-class type. That is RFC-0090 §7's own
"the one piece with no precedent to lean on at all," and it survives contact with the
literature. Stated as *not found*, not as *does not exist*.

### The languages that ship rows

| System | Rows used for | Ownership | Outcome |
|---|---|---|---|
| [Koka](https://arxiv.org/abs/1406.2061) | effects | none | rows chosen over subtyping, which made inference undecidable; scoped/duplicate labels give principal unification |
| [Links](https://homepages.inf.ed.ac.uk/slindley/papers/corelinks.pdf) | records, variants, **and** effects | none | one row mechanism across all three |
| [PureScript](https://purescript-resources.readthedocs.io/en/latest/eff-to-effect.html) | records; effects until 0.12 | none | **kept record rows, dropped effect rows** |
| Rust | none | affine | view types = fixed field sets |
| FST / Ferrite | records, variants, session choice | linear (by kind) | rows and linearity coexist, do not interact per-field |

Links is the closest existing point to "one row mechanism, several applications, in one
language," and it has no ownership. The cell combining rows with per-field ownership is
empty.

### Why PureScript dropped effect rows, and what transfers

The relevant failure, since it is the closest run of this experiment: PureScript carried
one row mechanism across records and effects and abandoned the effect half in 0.12. The
[stated reasons](https://purescript-resources.readthedocs.io/en/latest/eff-to-effect.html)
were unification errors users could not solve, anti-modularity (effects need a canonical
declaration site), boilerplate, and too little benefit at small and medium scale.

Which of those transfer to **field-access** rows:

- **Anti-modularity — does not transfer.** A field-access row's labels are one struct's
  own declared fields, fixed at its declaration. There is no canonical-location question
  because the declaration site is the struct.
- **Open-world growth — does not transfer.** The label set is finite and closed per type,
  the same observation RFC-0090 §3 makes about closed records being bounded by 2^N and
  "trivial for realistic struct sizes," applied to the access side.
- **Little benefit — does not transfer.** PureScript's effect rows tracked something the
  language did not otherwise need. Under affine ownership, "which fields does this touch"
  is what makes partial borrows work at all.
- **Unification error messages — transfers directly, and is the real risk.** This is the
  one to design against from the start rather than discover late.

**The limit of the finite-label-set argument**, stated so it is not oversold: it holds for
a *concrete* struct. The moment access rows abstract over a boundary — Rust's abstract
fields as trait members, or any generic function over "some struct with some accessible
subset" — variables reappear and so does unification. The finiteness buys a well-behaved
core, not immunity.

---

## 6. What rows buy that fixed field sets cannot

The positive case, which the originating conversation initially got wrong by looking only
outside the corpus. **RFC-0109 already contains the strongest example**, in its
Motivation:

> RFC-0090/RFC-0091's records, as drafted, solve the *reusable* half of Rust's view-types
> motivation — a generic `drain_field<row R, name, T>` function works across any
> `ToRecord`-deriving struct, which Rust's per-signature `&{a, b} self` annotation cannot
> do (it names concrete paths on one concrete type, at one call site, non-reusably).

That is a real capability, it is genuinely beyond Rust's design, and it requires
polymorphism over field sets. RFC-0109's contribution is the observation that this solves
the *reusable* half while leaving the *original* motivating case — calling an ordinary
method while another field is in use, with zero call-site syntax — completely unaddressed.

So the two halves are complementary, and the cluster already knows it:

| Need | Mechanism | Rows? |
|---|---|---|
| Call a method while another field is in use, no call-site ceremony | named view / self-view narrowing | no |
| Split one `&mut` into disjoint sub-borrows locally | reference-destructuring patterns | no |
| One `drain_field` reusable across every struct | row-polymorphic generic | **yes** |
| Public API that doesn't leak private field names | abstract fields / view groups | naming, then maybe |
| Reconstruct any `FromRecord` type from a partial record (RFC-0090 §8) | row-generic | **yes** |

Fixed field sets cover the ownership cases. Rows cover the *library* cases — writing one
function that works across many shapes. That is a real and interesting capability; it is
just not the same capability as making partial borrows work, and conflating them is what
made the cluster's dependency direction hard to settle.

---

## 7. What this suggests

Not a decision — the cluster is under review and this is one input.

1. **Separate the two row kinds explicitly in the RFCs**, even if both are kept. The
   presence/access distinction is currently implicit, and every hard question in the
   cluster (Trigger 6's dependency direction, RFC-0109's layering, `uses (…)`'s
   specification) is a question about which kind is doing the work.
2. **Let each justify itself on its own evidence.** Access rows are justified by
   ownership, by Rust's decade of demand, and by the transitivity problem. Presence rows
   are justified by library reusability (`drain_field`, generic `from_record`) and by
   typestate — a genuinely interesting case that does not need to borrow the ownership
   argument to stand up.
3. **Treat the access/effect connection as a design direction, not a hazard.** It is the
   one place in this cluster where an open problem has an answer already specified in a
   neighbouring document.
4. **Design the error messages first**, for whichever row survives. It is the single
   failure mode with direct evidence behind it.

---

## Open questions

1. **What identity should a view carry, and is it a brand or a type parameter?** §3.4 maps
   six options and leans toward a nominal `View<S, R>` constructor (identity as an ordinary
   type parameter, no dependence on RFC-0076) with structural *bound*-position acceptance
   as its complement. Not settled — in particular, whether `View<S, R - name>` needs
   type-level row arithmetic that the closed-record build order (RFC-0090 §3 step 1)
   deliberately avoids.
2. **Does inherited view identity actually close RFC-0090's open question 10?** §3.4 argues
   the identity question and OQ10 (`FromRecord` bypassing constructor invariants) are the
   same question, since structural-only reassembly lets any matching-shaped view rebuild a
   `Handle`. The argument is stated for the borrowed case only; whether it extends to the
   by-value `from_record` is unexamined, and neither RFC currently connects the two.
3. **Does `.{ … }` / `S.{ … }` survive contact with the rest of the grammar?** §3.5 checks
   the direct collisions — nothing starts with `.` in expression or type position, postfix
   `.` takes only three forms — but not the indirect ones: chained projection
   `S.{ R }.{ R' }`, projection in pattern position, the overlap with RFC-0099's
   dot-separated module paths, and whether `block_expr_stmt`'s `!"}"` lookahead interacts
   badly. Decided from grammar reading, not from a built prototype.
4. **What exactly is the call-site coercion rule?** §3.2 relocates the whole
   views-vs-records tension into it. RFC-0090 §8 bans implicit structural coercion; view
   types' headline benefit requires it. A rule narrow enough to permit the second without
   reopening the first has not been written.
5. **Does the `uses (…)` transitivity problem actually dissolve into the effect system,
   or only look like it does?** The shapes match; no worked example has been written
   through `algebraic-effects.md`'s actual `^ {E}` mechanism.
6. **If field-access becomes an effect, what is its interaction with real effects?** A
   function that both touches `self.x` and performs `IO` would carry two rows over
   different label universes. Composition unexamined.
7. **Does the finite-label-set argument survive abstraction?** §5 concedes variables
   reappear at boundaries; whether the remaining core is enough to avoid PureScript's
   error-message failure is unknown.
8. **Is row-tracked partial consumption still unprecedented after a proper literature
   search?** §5's negative claim rests on targeted searching, not a systematic review,
   and one earlier negative claim in this area has already been falsified once.
9. **Does separating the kinds change Trigger 6's answer** (RFC-0089's dependency on
   RFC-0090), or only clarify what the question was? Not worked through.

---

## References

- `internal/rfcs/1-under-review/rfc-0090-structural-records.md` — presence rows: §3's
  build order, §7's width-subtyping-vs-ownership problem, §9's open question 7
- `internal/rfcs/1-under-review/rfc-0091-linear-records.md` — §1's `uses (…)` and its
  unresolved transitivity; §1.1's `RcBox` case; §2's Option C
- `internal/rfcs/1-under-review/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  — named views as `(row, brand)`; reference-destructuring deliberately not row-based;
  the `drain_field<row R, name, T>` reusability argument
- `algebraic-effects.md` §8 (effects desugar to aspects), §13.4 (open effect rows),
  §13.6 (borrow priority table)
- `structural-records.md` §2 — the `RcBox` partial-drop case and the `unsafe`-gap catalogue
- External sources are linked inline in §5.
