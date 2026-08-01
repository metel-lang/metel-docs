---
id: rfc-0114
title: "Constructor Aspect and Canonical Construction"
date: '2026-07-23'
status: draft
target:
updated: '2026-07-24'
---

> **New RFC, split out 2026-07-23** from `reports/substructural-types/nominal-types-as-branded-rows.md`
> §6/Open Question 1 — that document found a construction-invariant bypass reachable
> through ordinary code once row-narrowing and widening are both automatic, and this RFC
> is the proposed fix, formalized separately so it can be reviewed on its own terms.
> `rfc.py new`'s overlap check flagged RFC-0090, RFC-0096, RFC-0038, RFC-0103, RFC-0105 —
> checked each: RFC-0090 owns `ToRecord`/`FromRecord` and names the problem (§8, open
> question 10) without proposing this fix; RFC-0096 owns the *auto-impl* pattern
> (`Send`/`Sync`/`Linear`, a closed, compiler-intrinsic list) which this RFC's default
> derivation resembles in spirit but does not reuse directly (§7); none of the others
> touch construction at all. Depends on RFC-0100 (still `1-under-review`, reopened) for
> removing bare struct literals, and names RFC-0026 (`unsafe` blocks, `0-draft`,
> deferred) as the foundation for §6's escape hatch.
>
> **Revised 2026-07-23, later the same day.** §5's fallibility question — left with
> three unadopted candidates in the first draft — is resolved: `construct` returns
> `Result<Self, Self::Error>`, with `Self::Error` defaulting to `!`. Both halves of the
> resolution reuse already-*implemented* rules from RFC-0078 (uninhabited-variant
> exhaustiveness, inhabited-singleton coercion) rather than inventing new type-system
> machinery. The three original candidates are kept below, marked superseded, not
> deleted.
>
> **Revised 2026-07-24 — surface syntax corrected, and one hole closed.** The first draft
> spelled rows `.{ … }` in freestanding positions, which was already stale when written:
> `reports/substructural-types/access-and-presence-rows.md` §3.5 keeps the dot **only**
> where a receiver is projected from (`Handle.{ fd }`), and this RFC's rows are all
> freestanding. They are restated here in RFC-0090's normative `record { … }` former (§1),
> with record *values* separated by `=` per
> `reports/syntax/colon-classifies-equals-defines.md` and RFC-0100 §1 — the same invariant,
> same day, in both RFCs. Correcting the examples surfaced a real gap the stale syntax had
> been hiding: **`construct`'s own body cannot construct a `Self`** without either
> recursing into itself or using the bare literal §2 abolishes. §1.1 settles that
> (row-to-`Self` is admitted inside `construct`/`construct_unchecked` and nowhere else),
> which also makes §1's synthesized default `Ok(row)` typecheck — it did not, as written.
> Separately, the examples used two pre-RFC-0098 spellings (`extend Type: Aspect`,
> `&var`) despite this RFC post-dating that RFC's implementation by nine days; both are
> corrected to `extend Type: Aspect` and `&var`. A new Open Question 8 records a privacy
> question §1.1 exposed and does not answer.
>
> **Revised again 2026-07-24, later the same day — the `record` keyword is gone.** The
> revision above used RFC-0090's then-normative `record { … }` former and noted that
> `access-and-presence-rows.md` §3.5 recommended bare braces instead, declining to adopt
> an unadopted spelling unilaterally. **RFC-0090 has since been amended to drop the
> keyword from anonymous records**, so this RFC follows: rows are `{ small: i32, big: i32 }`
> as types and `{ small = 3, big = 1 }` as values. `record` now appears in this RFC not at
> all — it survives only as RFC-0090 tier 3's *declaration* keyword, which this RFC has no
> occasion to use.
>
> **Revised a third time 2026-07-24 — the RFC-0100 dependency is gone entirely.** RFC-0100
> was split, its separator half becoming RFC-0115 (braces kept, `field_init`'s `:` → `=`).
> Reworking §2 against that surfaced that the dependency was never real: this RFC required
> RFC-0100 to *remove* brace literals, assuming a surviving literal bypasses `construct`.
> **A literal that desugars to `construct` is not a bypass.** §2 is rewritten to state what
> this RFC actually needs — every surface form producing a `Self` desugars to `construct`,
> with §1.1 the only exception — which every candidate syntax satisfies. Open question 2 is
> resolved by dissolving its premise, and this RFC now has no blocking dependency on any
> under-review RFC.

## Summary

A `Construct` aspect makes producing a value of a nominal type canonical: every `Self`
value, whether built fresh or reassembled after a partial move narrowed it away, comes
into existence through exactly one function, `Construct::construct(row) ->
Result<Self, Self::Error>`. This closes RFC-0090's open question 10 (`FromRecord`
bypassing constructor invariants) in its original scope and in the more general form
`reports/substructural-types/nominal-types-as-branded-rows.md` §6 found — automatic
widening after an ordinary partial move, not just an explicit conversion call. A
type author who has no invariant to enforce writes nothing; the compiler synthesizes a
trivial default, `Self::Error = !`, and RFC-0078's already-implemented coercion rules
make the resulting `Result<Self, !>` collapse to bare `Self` with no unwrap, no match,
and no runtime branch — provably, not by convention. A type whose invariant can
genuinely reject gets a real, typed error instead, and loses the automatic-firing sugar
in exchange — the same rule, applied uniformly, decides both. A separate, opt-in aspect,
`ConstructUnchecked`, gives performance-sensitive code an explicit, `unsafe`-gated way to
skip validation entirely when it already knows the invariant holds — mirroring Rust's
`new`/`new_unchecked` convention directly.

---

## Motivation

RFC-0090 §8 already names the risk, scoped narrowly: `SortedPair { small: i32, big: i32
}`'s invariant (`small <= big`), enforced only by `SortedPair::new`, can be silently
violated if `FromRecord` is auto-derived, because "auto-derived reconstruction can
silently skip validation a hand-written constructor enforces." Its own text limits the
concern to that one conversion function.

`nominal-types-as-branded-rows.md` §6 found the same bypass reachable through nothing
more than ordinary code, once narrowing and widening are both automatic and structural:

```metel
fun mess_with_it(p: &var SortedPair) {
    let old_small = p.small;   // move small out; p narrows to SortedPair.{ big }
    p.small = 999_999;         // assign an arbitrary value back in; p widens to full SortedPair
    // no call to SortedPair::new, anywhere. invariant possibly broken.
}
```

That document was explicit that plain mutable-field reassignment already has this
problem today, with zero row machinery involved — the finding is not a new hole, it is
that OQ10 was mis-scoped as `FromRecord`-specific when the underlying problem is general.

A second, independent motivation: without a single canonical path, a type with several
surface constructors (`new`, `from_str`, …) has no structural guarantee they stay in
sync with the same invariant — each is free-standing code that happens to duplicate
validation logic, or forgets to.

---

## 1. The `Construct` aspect

```metel
aspect Construct {
    type Error;
    fun construct(row: { /* all of Self's fields */ }) -> Result<Self, Self::Error>;
}

extend SortedPair: Construct {
    type Error = !;
    fun construct(row: { small: i32, big: i32 }) -> Result<Self, !> {
        if row.small <= row.big { Ok(row) }                    // §1.1
        else { Ok({ small = row.big, big = row.small }) }
    }
}
```

`construct` takes the type's own complete row and produces a `Result`, not a bare `Self`
— the signature that makes §5's fallibility resolution possible. `ToRecord`/`FromRecord`
(RFC-0090 §8) use bare `Self`; `construct` deliberately does not, for the reason §5
works through.

**Syntax note.** Rows are bare braces in every position this RFC uses, per RFC-0090's
2026-07-24 amendment and `access-and-presence-rows.md` §3.5: `{ small: i32, big: i32 }` as
a type, `{ small = row.big }` as a value (the `=` per RFC-0100 §1's separator invariant),
and `SortedPair.{ big }` for projection — the dot surviving only where there is a receiver
to project from. `construct`'s parameter is a **closed** record type, not a bound: it names
the type's exact complete row, and a caller supplying a wider row does not satisfy it.
RFC-0090's open question 13 records that closed types and bounds now share a spelling and
are told apart by position alone; `construct`'s signature sits in `param` position, so it
reads as the closed type.

**A struct with no invariant writes nothing.** The compiler synthesizes a trivial default
— `type Error = !; construct(row) { Ok(row) }` — the same way `Send`/`Sync`/`Linear`
compose a default from field-level facts today. Whether this specific default (a *whole*
synthesized impl, not a partial one) is expressible with mechanisms this corpus already
has is Open Question 3 — RFC-0082 (associated types) explicitly declined a *general*
default-associated-type mechanism, for reasons that don't obviously transfer to this
narrower case; see that question for why. This default must compile away entirely for
types that never customize it; construction for the overwhelming majority of structs
should cost exactly what a bare field-literal costs now. That is a *commitment*, matching
`nominal-types-as-branded-rows.md` §9's own unvalidated zero-cost claim for the
representation generally — not a new promise, the same one recurring here.

### 1.1 What `construct`'s own body may build — the one privileged site

Correcting the syntax above exposed a hole the first draft's examples had papered over:
its `construct` body wrote `SortedPair { small: …, big: … }`, **a bare struct literal that
§2 abolishes.** The general problem is not cosmetic — every route to a `Self` value now
goes through `construct`, including the route out of `construct` itself, which is circular.
The synthesized default just above, `construct(row) { Ok(row) }`, has the same problem in
miniature: as written it returns a row where `Self` is expected.

**Rule: a value of `Self`'s complete row type is admitted where `Self` is expected, inside
the body of `Construct::construct` and `ConstructUnchecked::construct_unchecked`, and
nowhere else in the language.** That is the primitive the whole mechanism bottoms out in.
Three things worth stating about it:

- **The privilege sits exactly where the responsibility already sits.** `construct`'s
  entire job is to be the one place a valid `Self` is minted; giving it — and only it — the
  ability to actually mint one is not an extra concession, it is the same statement from
  the other side. Rust's analogous primitive (the struct literal) is always available and
  gated only by field visibility; this narrows the gate from a module to a function.
- **It makes §1's synthesized default well-typed** rather than merely plausible. `Ok(row)`
  typechecks under this rule and does not under any other reading.
- **It does not depend on the branded-rows thesis, though it is cleaner under it.**
  If `nominal-types-as-branded-rows.md`'s central claim holds, this is not a coercion at
  all — `Self` *is* `(brand, row)`, and `construct` is simply the site where the brand is
  affixed. If that thesis is dropped, the rule survives unchanged as an ordinary typing
  rule about one function. That independence is deliberate: the thesis was explicitly left
  non-gating for this cluster.

**The cost, stated plainly: validation cannot be factored out into a `Self`-returning
helper.** A type whose checking logic is long enough to want its own function must have
that helper take and return the *row*, with `construct` performing the final step itself.
Tolerable, and arguably a good pressure, but it is a real constraint on how such code is
written and it follows from the rule rather than being independent of it.

---

## 2. Canonical construction: all construction is `Self::construct(row)`

**Rewritten 2026-07-24 (third revision): this section no longer depends on RFC-0100, or
on any particular construction syntax.** The first two drafts required RFC-0100 to *remove*
brace literals, on the reasoning that a surviving literal would be a bypass around
`construct`. That was the wrong requirement. **A literal is not a bypass if it desugars to
`construct`** — and once it does, which surface form the language settles on stops
mattering to this RFC at all:

```metel
SortedPair { small = 3, big = 1 }      // brace literal (today's form, RFC-0115's separator)
SortedPair(small = 3, big = 1)         // call-shaped   (if RFC-0100 lands)
// both desugar to
SortedPair::construct({ small = 3, big = 1 })
```

**The brace form's desugaring reads directly off the surface, which is worth noting rather
than treating the two as merely equivalent.** `SortedPair { small = 3, big = 1 }` is
visibly a brand applied to a row, so rewriting it to "apply that brand's constructor to
that row" is close to a no-op syntactically — the row is already written as a row. The
call-shaped form has to collect keyword arguments into a row first. Both work; the brace
form is the more transparent of the two, which is the opposite of what the first draft
assumed.

Fresh construction and post-narrowing reconstruction (§3) become the *same* operation, not
two mechanisms that happen to need the same validation. Positional construction
(`SortedPair(3, 1)`, RFC-0100 §1's one-or-two-field sugar) desugars identically after
positional-to-label assignment, if RFC-0100 lands.

Both get the *same* result-handling treatment from §5, uniformly: `let p = SortedPair {
small = 3, big = 1 };` binds a bare `SortedPair` when `Self::Error = !` (RFC-0078's
inhabited-singleton coercion applies automatically), and binds a `Result<SortedPair, E>` the
caller must handle otherwise — ordinary, unsurprising behavior either way.

**What this RFC actually needs, stated precisely now that it is not "RFC-0100 must land":**
every surface form that produces a `Self` must desugar to `construct`, and §1.1's
privileged row-to-`Self` admission must be the only exception. Nothing more. RFC-0115
(separator only, braces kept) satisfies this; RFC-0100 (call-shaped, literal retired)
satisfies it; today's grammar with neither would satisfy it too, since `field_init`'s
separator is irrelevant to whether a literal desugars. **This RFC has no blocking
dependency on either.**

**One cost the brace form carries and the call form does not, recorded because the split
should not lose track of it.** Braces read as inert data, but `construct` runs code and may
normalize — `SortedPair { small = 3, big = 1 }` evaluates to `small = 1, big = 3`. §5's
rule keeps genuinely *fallible* types out of this sugar entirely, so the surprise is
bounded to silent normalization, not silent failure. It is still a surprise. RFC-0115's own
open question 1 records the same tension from the other side.

---

## 3. Row-completion firing `construct()` automatically

The mechanism `nominal-types-as-branded-rows.md` §6 needed: any assignment that completes
a narrowed row — every label present again — is sugar for calling `construct()` on the
completed row and replacing the narrowed value with the result, rather than a bare
in-place write.

**Piecewise building composes the same way.** A value built up field by field —
`structural-records.md`'s `MaybeUninit`-avoidance example, `let partial = { a =
compute_a() }; let partial = { ..partial, b = compute_b() }; …` — only calls
`construct()` once, at the point the row becomes complete, exactly as a single literal
would. Intermediate partial states are ordinary, fully-valid values of a narrower type;
nothing fires until nothing is missing.

---

## 4. Collapsing `FromRecord` into `Construct`

`ToRecord`/`FromRecord` (RFC-0090 §8) are the same shape as `construct`'s signature under
a different calling convention. `ToRecord` needs nothing from this RFC — RFC-0090 already
states reading fields out of an already-valid value "is always safe." `FromRecord`'s
half, though, is the *exact* danger OQ10 names, under a different name for the same
operation. Under this RFC, `from_record(row)` is sugar for `Self::construct(row)`; there
is no second validation story to maintain. **This RFC does not itself amend RFC-0090's
text** — that reconciliation is left as a note for whichever review pass reconciles the
two, not decided unilaterally here.

---

## 5. Fallibility — resolved, reusing already-implemented rules

`SortedPair::construct` above is **infallible and self-healing** — it never rejects, only
reorders. Not every invariant can be repaired that way. A `NonEmptyList<T>` cannot
manufacture an element out of nothing if its row completes empty; its invariant must be
able to *reject*, not just normalize. `construct` therefore returns
`Result<Self, Self::Error>` (§1) rather than bare `Self` — but that alone would leave the
same problem §2 already names: **an ordinary field assignment looks syntactically
infallible.** `p.small = 999_999` reads as plain mutation; if `construct` can genuinely
fail, what does the automatic firing (§3) do with an `Err`?

**The resolution reuses two already-*implemented* rules from RFC-0078 (Bottom Type,
`4-implemented`, integrated 2026-07-10), rather than inventing a new one:**

- **§3.2, uninhabited variants:** "an enum variant whose payload type is `!` is
  uninhabited. No value of that variant can ever be constructed." `Result<Self, !>`'s
  `Err(!)` branch is therefore not reachable — not by convention, by construction.
- **§3.3, inhabited-singleton coercion:** "If an enum type has exactly one inhabited
  variant... and that inhabited variant has exactly one field, a value of that enum type
  implicitly coerces to that field's type. The compiler inserts the destructuring; no
  explicit match is required." `Result<Self, !>` matches this exactly — `Ok` is the sole
  inhabited variant, holding exactly `Self`.

**For the default case (`Self::Error = !`), these two rules together mean the compiler
already, today, implicitly coerces `Result<Self, !>` to bare `Self` — no unwrap, no
match, no runtime branch, and *provably* safe rather than trusted.** The automatic firing
in §3 needs no special casing: it calls `construct`, the result coerces silently, the
assignment stays exactly as ordinary as it looks.

**For a genuinely fallible type** (`type Error = NonEmptyListError;`),
`Result<Self, Error>` has two inhabited variants, so §3.3's coercion simply does not
trigger — there is no silent path to bare `Self`. Concretely, this means **the
automatic-firing sugar in §3 is not available for such a type**: completing its row
cannot happen through a bare assignment at all: the compiler has no implicit coercion to
insert, so the assignment is rejected, and reconstruction must go through an explicit
call to `construct`, handled with the same already-existing machinery ordinary fallible
calls already use (`?`, `match`, `.unwrap_or`) — the `?` operator with `From`-based error
coercion has been live since v0.4.0 (noted in RFC-0079's own refusal record, which
otherwise only confirms `Result<T, E>` and `Perhaps<T>` are already implemented and
spec'd, not that anything about them needs inventing here).

**One rule decides both halves, and it is not a new rule.** Whether a type gets the
automatic-firing convenience or requires explicit result-handling falls entirely out of
whether `Self::Error` is uninhabited — the same declaration that expresses "can this
fail" also decides "does this get silent re-widening," with no separate flag to keep in
sync. This applies uniformly to fresh construction and post-narrowing reconstruction
alike (§2) — the same rule, not two rules that happen to agree.

**`ConstructUnchecked` (§6) is a genuinely different flavor of trust, not made redundant
by this.** `Construct`'s infallibility, when claimed, is *proven* by the type system
(`Err` uninhabited, checked exhaustively). `ConstructUnchecked`'s is *asserted* by the
programmer, via `unsafe`, unchecked — the escape hatch remains necessary for types whose
invariant is real but whose author, in a specific call site, already knows it holds and
wants to skip re-proving it.

**Superseded, kept for the record — the first draft's three candidates, before this
resolution:** *(a)* only infallible impls participate in automatic firing, others opt
out of implicit narrow/widen entirely; *(b)* `construct` stays infallible by convention,
genuine rejection lives only in separate explicit constructors; *(c)* `construct` panics
on failure, treated as infallible at the type level. Reading them back, (a) is what the
resolution above actually *is*, made precise and automatic via RFC-0078 rather than left
as a design choice to enforce by hand; (b) and (c) are no longer needed.

---

## 6. The unsafe escape hatch: `ConstructUnchecked`

A systems language needs a way to skip redundant validation when a caller already knows
the invariant holds — Rust's `NonZeroU32::new` (checked) alongside `new_unchecked`
(unsafe, no check) is the direct precedent.

```metel
aspect ConstructUnchecked {
    unsafe fun construct_unchecked(row: { /* all of Self's fields */ }) -> Self;
}
```

**Separate from `Construct`, deliberately.** Not auto-derived, not implied by
implementing `Construct` — a type author writes it explicitly, taking on the
responsibility the `unsafe` block already signals elsewhere in the language. Ordinary
row-completion (§3) never calls it; only code that explicitly reaches for
`construct_unchecked` inside an `unsafe` block does.

**It gets §1.1's privileged site too, necessarily.** `construct_unchecked` returns bare
`Self` and skips validation, so its body has no other way to produce one — the typical
implementation is exactly `row`, unchecked. This is the sharper statement of what the
`unsafe` is buying: not "skip a branch", but "affix the brand without earning it."

**This depends on RFC-0026 (`unsafe` blocks), which is not a solid foundation yet.**
RFC-0026 is `0-draft`, and its own header still describes itself as deferred pending
RFC-0028 (Memory and Reference Model) and RFC-0046 (Linear Closure Capture) — **both of
which are actually `6-refused`**, not open or unresolved as RFC-0026's text currently
claims. That drift is RFC-0026's own to fix, not addressed here, but it means the
foundation this section leans on is staler than a first read of RFC-0026 suggests, and
may in fact be closer to revisitable than its own header currently states.

---

## 7. Generics and monomorphization

A generic struct's row depends on its type parameter — `Pair<T> { a: T, b: T }`'s row
isn't fully known until `T` is concrete. Whether `construct()` resolution needs to defer
to monomorphization time, the way Metel's generic function bodies already do
(`FunBody::Generic`/`TypedExpr::GenericClosure`, constructed from runtime values), is the
same question `nominal-types-as-branded-rows.md` open question 4 already asks, recurring
here rather than being separate. Not worked through in either document.

---

## 8. Scope

**Enums are out of scope**, consistent with RFC-0090 §6/§9 and
`nominal-types-as-branded-rows.md` — this is a structs-only mechanism. Stated explicitly
rather than left to be assumed.

This RFC does not propose changes to `Drop` dispatch (`nominal-types-as-branded-rows.md`
§4) beyond noting the parallel: `Construct`/`ConstructUnchecked` govern how a value is
*born*, the same way `Drop` governs how it is *torn down* — two ends of the same
lifecycle, addressed by two separate, independently-motivated RFCs rather than one.

---

## Open Questions

1. ~~Fallibility.~~ **Resolved 2026-07-23, §5:** `construct` returns
   `Result<Self, Self::Error>`; RFC-0078's already-implemented uninhabited-variant and
   inhabited-singleton-coercion rules make the default (`Error = !`) collapse to bare
   `Self` provably, and a real `Error` type loses the automatic-firing sugar in exchange,
   both by the same mechanism. Kept as a struck-through entry rather than removed, per
   this corpus's convention of leaving resolved questions visible.
2. ~~Does this RFC need its own literal-banning rule independent of RFC-0100 (§2)?~~
   **Resolved 2026-07-24 by dissolving the premise, not by answering it.** The question
   assumed a surviving brace literal is a bypass around `construct`. It is not, if it
   desugars to `construct` — and §2 is rewritten on that basis. No literal-banning rule is
   needed, from this RFC or RFC-0100, so the fallback that was "not worked out here" no
   longer needs working out. **This also removes this RFC's only blocking dependency on an
   under-review RFC**, which is a larger consequence than the question itself: RFC-0114 is
   now compatible with RFC-0115, with RFC-0100, with both, or with neither.
3. **What derives `Construct`'s default implementation, mechanically?** §5's resolution
   sharpens this rather than settling it: RFC-0082 (associated types, `4-implemented`)
   explicitly declined a *general* default-associated-type mechanism — "a default would
   create a compiler-generated impl that could conflict with user impls under the
   overlap rules" — but that objection is about a *partial* default merging into a
   user-written impl. `Construct`'s need is a *whole* synthesized impl
   (`type Error = !` and the trivial body together), existing only when the user writes
   no impl at all, which is structurally closer to RFC-0096's auto-impl pattern
   (`Send`/`Sync`/`Linear`) than to what RFC-0082 declined — but RFC-0096's own pattern is
   a closed, compiler-intrinsic list of exactly three aspects (RFC-0096 §1), not a
   general mechanism either. Whether RFC-0082's stated objection actually applies to this
   narrower, whole-impl case is unexamined. RFC-0093's comptime-derive mechanism is a
   third candidate, itself `0-draft`. Not resolved here.
4. **Monomorphization timing for generic structs** (§7) — open in both this RFC and
   `nominal-types-as-branded-rows.md`.
5. ~~Does the compiler need to separately enforce that hand-written surface constructors
   (`new`, `from_str`) route through `construct()`?~~ **Resolved 2026-07-24 by §1.1: no,
   and the reason is now precise rather than plausible.** The first draft guessed this was
   automatic "once no other way to produce a `Self` exists structurally" — §1.1 makes that
   exact, by naming the one remaining way and confining it. Row-to-`Self` is admitted only
   inside `construct` and `construct_unchecked`, so a hand-written `new` has no primitive
   available to it at all: its only routes to a `Self` are calling `construct` (checked) or
   `construct_unchecked` (`unsafe`, explicitly opted into). No separate enforcement rule is
   needed, because there is nothing left to enforce it against.
6. **Is RFC-0026 a solid enough foundation for §6?** Its own cited blockers are both
   already refused, not open — which may mean it is closer to revisitable than its
   current text suggests, but that is RFC-0026's maintenance question, not settled here.
7. **Does a fallible type's narrowed-but-incomplete row ever get stuck**, the same
   liveness-not-safety gap RFC-0090 §8 already accepts for `restore` ("nothing stops code
   from never calling `restore`")? Presumably yes, and presumably fine for the same
   reason — not checked against a concrete example here.
8. **Can a type still refuse to be constructible from outside its module?** *(New,
   2026-07-24.)* Raised by §1.1, not answered there. Checked directly against `grammar.pest`: `extend_impl_block`
   carries **no** visibility modifier — unlike `struct_decl`, `enum_decl` and
   `aspect_decl`, which all have `public_kw?` — so an `extend SortedPair: Construct { … }`
   impl cannot be made private, and `SortedPair::construct` is therefore callable wherever
   `SortedPair` is nameable. Two readings, and which holds is genuinely undecided:
   - **The hole is closed by field visibility.** The caller must supply a `{ small: i32,
     big: i32 }`, naming every field including private ones. If a private label
     cannot be written in a record literal from outside the declaring module — the natural
     extension of RFC-0090 §8's non-ambient guarantee, and of the brand-scoped visibility
     `nominal-types-as-branded-rows.md` §7.1–7.3 settles — then outside code cannot
     construct the argument, and `construct`'s public callability is harmless.
   - **The hole is real.** If record literals are structurally typed and label visibility
     is not inherited from the declaring struct, then making `Construct` canonical hands
     every struct a public constructor it may not want, and privacy would have to be
     recovered some other way (a visibility modifier on `extend`, or an
     `Error`-typed refusal, neither of which exists).

   The first reading is the one this RFC assumes, and it is *load-bearing* rather than
   incidental — it should be confirmed against RFC-0090's own text before acceptance, not
   after. Note this is a question about record-literal typing, so it is now RFC-0116's to
   answer (its open question 3), not this RFC's to decide unilaterally.
9. **Deferred 2026-07-24. Should `FromRecord` reuse this RFC's call syntax and default to `construct`'s logic?**
   *(Corrected 2026-07-24 — first recorded here as "collapse `FromRecord` into
   `Construct`", which is a different and weaker proposal that was not the one made.)*
   Worked through in **RFC-0119 open question 5**. The shape that matters for *this* RFC:
   `FromRecord` stays a separate opt-in aspect, but is spelled `Handle({ … })` rather than
   `Handle::from_record(…)`, and its default body is `construct`. **That makes `Construct`
   the internal rule for how a `Self` comes into existence and `FromRecord` the external
   permission to invoke it from a row** — capability and logic separated, with the tier
   gate untouched.

   The consequence to settle here: **if `FromRecord` is overridable, an author can bypass
   `construct`**, reinstating the exact hole §1.1 and §2 close. The likely answer is that
   it must not have a body at all — a permission, not an implementation.

   *Also withdrawn with the misreading:* the claim that the tier gate could become
   *visibility* rather than a derive, making this question, open question 8 above and
   RFC-0116's open question 3 "the same question asked three ways." They are not. Open
   question 8 stands on its own.

   **Deferred with RFC-0119 OQ5, same day.** Not refused — but it cannot be evaluated until
   RFC-0100 settles what `Handle(r)` means positionally, and its overridability
   sub-question has to be answered before the syntax rather than after. Nothing in this RFC
   depends on it: §2 already states that every surface form producing a `Self` desugars to
   `construct`, and that holds whatever `FromRecord` ends up being spelled as.
10. ~~§3's automatic firing has no story for the borrowed case.~~ **Closed 2026-07-24, and
    §3 is the half that survived.** The contradiction was between §3 (any assignment
    completing a narrowed row is sugar for `construct()`) and RFC-0119's `from_record_mut`
    path, which completed a row behind a `&var` view and claimed nothing beyond structural
    row-matching needed checking. **RFC-0119 dropped its by-reference mode entirely**, as
    superseded by RFC-0109's named views, so the contradicting site no longer exists.
    Rebuilding a struct now always goes through `from_record` — that is, through
    `construct` — by value. §3 stands unamended, which is what it was written to be.
    The asymmetry that made this hard is worth recording: `construct` returns an owned
    `Self`, so it could never have been what fires behind a borrow, and any future proposal
    to complete a row through a borrow has to answer that first.

---

## References

- `reports/substructural-types/nominal-types-as-branded-rows.md` — §6 and Open Question
  1, the problem this RFC is the proposed answer to
- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` §5 (field-composition
  auto-derivation), §8 (`ToRecord`/`FromRecord`, the `SortedPair` example, open question
  10 in its original, narrower scope)
- `internal/rfcs/4-implemented/rfc-0078-bottom-type.md` §3.2 (uninhabited variants), §3.3
  (inhabited-singleton coercion) — the two already-implemented rules §5's fallibility
  resolution reuses rather than inventing new machinery
- `internal/rfcs/6-refused/rfc-0079-perhaps-and-result.md` — refused as redundant with
  reality, not with the type itself: confirms `Result<T, E>`/`Perhaps<T>` and the
  `?`-operator with `From`-based error coercion are already implemented, live since
  v0.4.0, which §5 depends on for the fallible-type path
- `internal/rfcs/4-implemented/rfc-0082-associated-types.md` §9 — the declined general
  default-associated-type mechanism, cited precisely in Open Question 3 rather than
  assumed to transfer to `Construct`'s narrower case
- `internal/rfcs/0-draft/rfc-0096-auto-impl-aspects-compiler-recognized-structural-aspects.md`
  — the auto-impl pattern `Construct`'s default derivation resembles but does not reuse
  directly (§1, §3)
- `internal/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` — call-shaped
  construction and general keyword arguments. **No longer a dependency of this RFC** (§2,
  open question 2): if it lands, `Type(args)` desugars to `construct`; if it does not, a
  brace literal does. Its reopening reason, tracked by `OBJECTIVES.md` Trigger 14, was
  found dissolved on 2026-07-24 — relevant to that RFC's own prospects, not to this one's
- `internal/rfcs/4-implemented/rfc-0115-field-initializer-separator.md` — the separator half
  split out of RFC-0100 the same day; keeps brace literals and changes only `field_init`'s
  `:` to `=`, which is what makes `SortedPair { small = 3, big = 1 }` desugar so directly
  to `SortedPair::construct({ small = 3, big = 1 })` (§2). Also not a dependency
- `reports/syntax/colon-classifies-equals-defines.md` — the `:` classifies / `=` defines
  invariant that fixes the separator in this RFC's record values and RFC-0100's keyword
  arguments identically
- `reports/substructural-types/access-and-presence-rows.md` §3.5 — the settled row-former
  rules this RFC now follows in full: dot only where a receiver is projected
  (`SortedPair.{ big }`), bare braces everywhere else (§1's syntax note)
- `internal/rfcs/4-implemented/rfc-0098-surface-keyword-renames.md` — `extend Type: Aspect`
  and `&var`, the spellings this RFC's examples were corrected to on 2026-07-24
- `internal/rfcs/0-draft/rfc-0026-unsafe-blocks.md` — the foundation for
  `ConstructUnchecked`; `0-draft`, deferred, with a stale dependency note (§6)
- `internal/rfcs/0-draft/rfc-0093-derive-registration.md` — the comptime-derive
  mechanism possibly relevant to `Construct`'s default (open question 3)
- `reports/substructural-types/structural-records.md` — the piecewise-`MaybeUninit`
  worked example §3 generalizes

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
