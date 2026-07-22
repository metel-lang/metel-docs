---
id: access-and-presence-rows
title: "Access Rows and Presence Rows: Two Row Kinds, and What Connects Views to Effects"
type: report
status: active
last_synced_against_model: '2026-07-22'
supersedes: null
revives: null
---

# Access Rows and Presence Rows

*Written 2026-07-22, out of a design conversation about whether the records cluster
should be built from structural records downward or from views upward. It does not
resolve that question. It argues that the question is being asked about **two different
row concepts that the cluster currently treats as one**, and that separating them
changes what each has to justify.*

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

The split is about **rules, not representation**. §3 argues the two roles should share one
row solver and differ in four specific rules; it is the section to read first if the
obvious objection ("aren't these the same thing with a well-formedness check?") is the one
you have.

---

## 2. Where the corpus currently merges them

This is not a strawman; the merge is explicit and deliberate in the current drafts.

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

## 3. Why one semantics plus a well-formedness check isn't enough

The natural objection to §1, and the one worth answering in full: if access rows are just
presence rows whose labels are restricted to fields that actually exist on the referenced
struct, why are they a separate concept at all? Add the check, reuse everything else.

**The check is real and necessary.** It does the work of rejecting a view that names a
field the struct doesn't have, and of keeping a view tied to a nominal type — RFC-0109
relies on something like it already, noting that a view's brand "is exactly what prevents
it from ever satisfying a *generic* structural bound the way an anonymous record could."

What it cannot do is settle the rules below, because those don't follow from which labels
are legal.

### 3.1 The generating difference: what the complement means

- **Presence row** — `record { fd }`: the fields *not* in the row **do not exist**. The
  value is smaller; `alloc` was moved out and is gone.
- **Access row** — `&mut Handle.{fd}`: the fields not in the row **exist and are live**.
  `alloc` is still owned by the original value, and may be in use through another view at
  the same moment. That simultaneity is the entire purpose of view types.

Same syntactic structure, opposite reading of what is missing. Everything below is a
consequence of that one difference.

### 3.2 The consequences

| | Presence row | Access row |
|---|---|---|
| The row describes | a **value** | a **reference or computation** |
| Fields outside the row | gone | live, possibly in use elsewhere |
| `Drop` behaviour | computed **from the row** | drops **nothing** — a borrow |
| `Linear`/`Send`/`Sync` | recomputed from the row | inherited from the whole struct |
| Narrowing the row | **unsound** for owned values | **always safe** |
| Read/write modes | none | required |
| How many per value | exactly one | many, simultaneously |
| The empty row `{}` | a useless value | maximally composable |

Three of these deserve expanding, because they are rules rather than checks.

**Narrowing runs in opposite directions.** RFC-0090 §2 states that an open record "permits
width subtyping, i.e. silently forgetting fields, which is exactly what non-`Copy`
ownership exists to prevent," and §5 rejects the pattern outright until some
`AllCopy`-shaped bound exists to guard it. For access rows, narrowing is never dangerous —
promising to touch *fewer* fields cannot leak anything — and it is the operation performed
constantly, whenever a `{a, b}` reference is passed to something requiring `{a}`. A shared
solver would therefore need its subtyping rule parameterised by role. That is the
definition of different rules, not of one semantics with a guard.

*Precision, so this isn't overstated:* presence rows in **bound** position narrow safely —
a wider struct satisfying `HasField<"x", f64>` is fine, which is RFC-0090 §7's own
resolution ("a bound alone grants no new capability *over the type itself*"). The
unsoundness is specific to owned-value positions, where narrowing means fields are
silently dropped.

**`Drop` is a computation, not a check.** Under presence semantics a record's destructor
and its `Linear`/`Send`/`Sync` status are *derived from its row*, by RFC-0090 §5's
field-composition rule. Give a view the same semantics and `Handle.{fd}` would claim to own
and drop `fd` — while the real owner drops it too. Nothing about label legality prevents
that; the derivation itself has to be switched off for the access role.

**Modes are an additional axis with no presence-row counterpart.** RFC-0109 §4.9 types
`self` as a tuple of views with independent `&`/`&mut` per slot, checked pairwise-disjoint.
Access rows need a per-label mode and a compatibility relation *between two rows over the
same value*. Presence rows have neither, because a value has exactly one shape — there is
no second row to be compatible with.

### 3.3 The resolution: one mechanism, two roles

The conclusion is not that these need separate implementations. The representation — a
finite label map with row variables, unification, subset and disjointness checks — should
be shared, along with its inference and its diagnostics. Building it twice would be
indefensible.

The precedent is already in this directory. `brand-kind-unification.md` argues that `@a`
(allocator tags), `&r` (lifetime anchors), and `'c` (brands) are **three sigil-selected
roles of a single kind** — unified at the mechanism level, with distinct rules per role,
for implementer economy rather than user-facing uniformity. Rows appear to want the same
treatment: one row kind, two roles, with role-parameterised rules for narrowing, `Drop`
derivation, mode, and cardinality.

If that holds, it is a second independent instance of the same unification pattern, which
is mild evidence for the pattern itself rather than a coincidence of this cluster.

---

## 4. Access rows are effect rows

The framing this document proposes: **an access row is a statement about what a
computation does, over a finite label set.** That is the same shape as an effect row.

| Mechanism | Reads as |
|---|---|
| Rust's `fn process(&mut self { statistics })` | this function's field-access row is `{statistics}` |
| RFC-0109's named view | a named access-row alias |
| Rust's *abstract fields* (trait members) | row variables over access rows |
| RFC-0091 §1's `uses (fd)` | the destructor's access row |
| **transitivity through helper calls** | **effect-row propagation** |

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

1. **What is the minimal set of role-parameterised rules?** §3 answers the earlier, vaguer
   version of this question — the representation should be shared, the rules should not —
   and identifies four rules that differ: narrowing direction, `Drop`/multiplicity
   derivation, per-label mode, and cardinality per value. Whether those four are
   sufficient, or whether unification and inference also need role-awareness (they may:
   an access row unified with a presence row is presumably ill-formed, and something has
   to say so), is not worked out.
2. **Does the `uses (…)` transitivity problem actually dissolve into the effect system,
   or only look like it does?** The shapes match; no worked example has been written
   through `algebraic-effects.md`'s actual `^ {E}` mechanism.
3. **If field-access becomes an effect, what is its interaction with real effects?** A
   function that both touches `self.x` and performs `IO` would carry two rows over
   different label universes. Composition unexamined.
4. **Does the finite-label-set argument survive abstraction?** §5 concedes variables
   reappear at boundaries; whether the remaining core is enough to avoid PureScript's
   error-message failure is unknown.
5. **Is row-tracked partial consumption still unprecedented after a proper literature
   search?** §5's negative claim rests on targeted searching, not a systematic review,
   and one earlier negative claim in this area has already been falsified once.
6. **Does separating the kinds change Trigger 6's answer** (RFC-0089's dependency on
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
