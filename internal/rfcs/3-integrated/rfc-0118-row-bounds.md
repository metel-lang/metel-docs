---
id: rfc-0118
title: "Row Bounds"
date: '2026-07-24'
status: integrated
target:
updated: '2026-07-24'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/289'
impl_status: not-started
---

> **Extracted from RFC-0090 on 2026-07-24** (superseded; see RFC-0116's header for the
> split rationale).
>
> **Depends on RFC-0116 (Anonymous Record Types)** for the row syntax it reuses in bound
> position, and on nothing else. It does **not** depend on RFC-0121 (Open Rows): a bound
> is a predicate over a type, not a row variable, and the two were conflated in RFC-0090
> partly because they shared a spelling.

> **Status — under review (2026-07-24).** Scheduled for v0.12.0 alongside RFC-0116, which is its only dependency.

> **Status — accepted (2026-07-24).** OQ1/OQ2 resolved by prototype (wildcard_type + row_bound built, 755 tests green, reverted). OQ3 resolved: bounds match the public projection of a row, making satisfaction module-relative -- acceptable because a bound grants no capability. OQ4 deferred to RFC-0121, which is not in this release and is the only thing that could make it reachable. OQ5 is an implementation-location question, not a design one.

> **Status — integrated 2026-07-24, targeting v0.12.0.** A "Row bounds" subsection is
> merged into `public/reference/spec/types.md` under Generics, covering open and closed
> bounds, the trailing `..`, negation with the type wildcard, why implicit structural
> satisfaction is safe, and the public-projection rule. Three one-line availability markers.
>
> **Cross-checked against the siblings still in flight for v0.12.0**, per `PROCESS.md`:
>
> - **RFC-0116 (Anonymous Record Types)** — this RFC's only dependency, now `3-integrated`.
>   No conflict: a row *type* and a row *bound* are distinguished by position, and by the
>   `..` marker for the open reading, which RFC-0116's closed types never carry.
> - **RFC-0115 (Field Initializer Separator)** — no interaction. Bounds and row fields both
>   classify and keep `:`; RFC-0115 moves only *initializers* to `=`.
> - **RFC-0071 (Ownership)** — no interaction. Bound satisfaction is a static question about
>   a type's fields, not about any value's multiplicity.
> - **RFC-0121 (Open Rows), not in this release** — inherits two questions from here
>   (impl-selection coherence, and the module-relative consequence of the public-projection
>   rule). Both are unreachable in v0.12.0 because nothing in it lets an impl be keyed on a
>   row; re-checked against RFC-0116 and this RFC rather than assumed.
>
> **The design questions that were open at review are settled, two of them by building the
> change rather than reasoning about it.** `wildcard_type` and a `row_bound` alternative to
> `bound_head` were added to the grammar, run against the suite (755 green), and reverted:
> `T: { x: f64, y: f64, .. }` and `T: !{ token: … }` both parse, `T: Show + Clone` is
> unaffected. The prototype also settled a detail the RFC had not specified — the trailing
> `..` is admitted only after at least one field, so bare `{ .. }` does not parse.
>
> **Amended 2026-07-24, hours after integration, and the amendment is the substantive
> part.** As first integrated, §3 said any struct with matching fields satisfies a row bound
> implicitly, and open question 3 was resolved with a "public projection" rule to stop that
> leaking private fields. **Both were wrong, and the second only existed because of the
> first.**
>
> **What was missed:** RFC-0090 contradicts itself on whether structs satisfy bounds. Its
> §2 and §7 say yes, implicitly; its §8 tier 1 and tier 2 say never. §7 even claims to be
> "resolved by the tier system (§8)" while asserting the opposite of §8. This RFC inherited
> §2/§7's side without noticing §8's, and the integration cross-check above did not catch
> it — it compared this RFC against its *siblings* and against the grammar, but not against
> the superseded parent's own tier text, which is where the conflict lived.
>
> **§3 now takes §8's side: a row bound is satisfied by a record, not by a struct.** A
> struct converts first (RFC-0119). The tier rule then applies without exception.
>
> **Two consequences.** The public-projection rule is **withdrawn** — a record has no
> declaring module and no private fields, so nothing needs projecting; the question moves
> to RFC-0119, where `to_record()` is the actual capability. And in v0.12.0 row bounds are
> useful over record literals but not over structs, since conversions are not in this
> release — the headline case is deferred, not abandoned, and needs no further change to
> this RFC when RFC-0119 lands.
>
> **This is `3-integrated` doing its job rather than failing at it**, per `PROCESS.md`: a
> problem surfaced at integration sends the RFC back for amendment instead of carrying it
> into implementation. It surfaced late and by challenge rather than by my own cross-check,
> which is worth recording as the more useful fact.

> **Status — integrated (2026-07-24).** Row bounds merged into public/reference/spec/types.md under Generics; three availability markers. Cross-checked against RFC-0116/0115/0071 and RFC-0121 (which inherits the impl-coherence and module-relative questions). Grammar verified by prototype.

> **Amended 2026-07-25, while assessing implementation readiness (#289).** Three changes,
> all to §1/§2 and the grammar delta; the semantics of what satisfies a bound (§3) are
> untouched.
>
> - **The `record` kind marker is retained**, after being proposed for deferral and the
>   proposal withdrawn. The argument for dropping it — that a row bound already implies
>   record-kindedness — fails on `<record T>` with *no* row bound, which is the only way to
>   write "any record, whatever its shape" and is the signature RFC-0092's comptime row
>   reflection needs. The kind gates what the body may do, not merely what the caller may
>   pass. See §1.
> - **Two forms are now specified that never were:** the row bound is optional
>   (`<record T>` alone is valid), and `record` may be written in a `where` constraint as
>   well as at the parameter.
> - **The type-position wildcard `_` is withdrawn** (open question 1, reopened and closed
>   the other way). Its 2026-07-24 resolution added `wildcard_type` to `type_expr`, which
>   would have made `_` writable in every type position while this RFC defined it in one.
>   Replaced by letting a row field omit its type: `{ x }` means "a label `x`, any type", in
>   either polarity. §2 also now states that negation is the **complement** of the positive
>   bound — consistent with `!Copy` — so `!{ x: f64 }` is satisfied by a record whose `x` is
>   an `i64`, and `!{ x }` is the "no such label at all" form.
>
> The last two came out of challenges during the readiness review rather than from my own
> cross-check, which is the more useful fact to record.

## Summary

A bound written as a bare row: `record T: { x: f64, y: f64, .. }` means "any type carrying at
least these fields." A field may omit its type (`{ x }`) to constrain the label only.
Negation reuses the bound grammar's existing `!` and is the complement of the positive
bound: `T: !{ token }` means "any type carrying no field named `token`." **Any nominal struct with matching
fields satisfies a row bound with no explicit opt-in** — this is the one implicit,
structural satisfaction rule in an otherwise nominal aspect system, and §3 explains why
that is safe here specifically.

Replaces the `HasField<"x", f64>` / `Lacks<"tag">` aspect family, which **never parsed** —
`bound_arg` accepts only `assoc_binding` or `type_expr`, and `type_expr` has no
string-literal alternative.

---

## Motivation

Generic code often wants "anything with an `x` and a `y`," not a specific nominal type.
Without a structural bound, every such case needs either a bespoke aspect per field shape
— unworkable at scale — or forces callers to wrap values in a common nominal type to
satisfy a bound that was never about identity.

GHC's `HasField "x" r Float` answers the same problem. The first draft of this feature
copied that shape directly and inherited a spelling Metel's grammar cannot parse; writing
the bound as a row instead removes the string literal, compacts an ANDed chain of
per-field facts into one bound naming several labels, and reuses syntax that already
exists for an unrelated reason.

---

## 1. Positive bounds, and the `..` that makes them open

```metel
fun magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64 { ... }
```

**The `record` kind marker is required; a bare `<T: { … }>` is an error.** *(Adopted
2026-07-24.)* A row bound is satisfiable only by a record (§3), so a type parameter carrying
one is record-kinded whether or not it says so. Making it say so follows the same
explicit-over-inferred principle as RFC-0065's "elision is never a silent choice" and as
`<row R>` itself, which is declared rather than inferred from `..R` usage.

**It is deliberately *not* spelled `row T`.** `row R` (RFC-0121) declares R to be a **row** —
a label-to-type mapping, spliced as `..R`. `record T` declares T to be a **record type**,
used directly as `T`. Those are different kinds, and reusing one keyword for both is the
error this cluster has spent its whole history removing.

### The marker is capability-granting, not decorative

*(Recorded 2026-07-25, after the marker was proposed for deferral and the proposal was
withdrawn.)* The case for dropping it ran: a row bound is satisfiable only by a record, so
the kind is inferable from the bound and the marker adds nothing but explicitness. **That is
wrong, and the reason is `<record T>` with no row bound at all.**

```metel
fun labels<record T>(x: T) -> Symbol[] { ... }   // any record, whatever its shape
```

There is no other spelling for that. `<T>` is unconstrained and admits `i64`; `<T: { .. }>`
**does not parse**, deliberately — see open question 2, where the trailing `..` is admitted
only after at least one field. So without the marker, record-kindedness is obtainable only
as a side effect of constraining specific fields, and a function that wants "any record"
would have to invent a fake field constraint to get it.

That case is not hypothetical. **RFC-0092 (Comptime Core) already models `TypeInfo::Struct
{ row: Row }`** and states that the payload "is exactly what RFC-0090's row concept already
models", with `typeinfo` inspecting the row at comptime. Label-level operations over an
otherwise unconstrained record are a designed direction, and `<record T>` is the signature
they need.

**So the kind gates what the body may do, not merely what the caller may pass.** A row bound
is an optional further constraint on an already-record-kinded parameter:

```metel
fun labels<record T>(x: T) -> Symbol[]                  // any record
fun magnitude<record T: { x: f64, y: f64, .. }>(p: T)   // a record with at least x and y
```

### Where the marker may be written

`record` may appear at the parameter's declaration **or** in a `where` constraint for it, the
same way an aspect bound may be written in either place. The two are equivalent, and writing
it in both is redundant but legal:

```metel
fun f<record T: { x: f64, .. }>(p: T) -> f64 { ... }
fun g<record T>(p: T) -> f64 where T: { x: f64, .. } { ... }
fun h<T>(p: T) -> f64 where record T: { x: f64, .. } { ... }   // kind declared in `where`
```

**A parameter is record-kinded iff `record` precedes its name in at least one of those two
positions.** A row bound written for a parameter that is record-kinded in neither is the
error this section opened with — the diagnostic should name the fix (`add `record` before
the type parameter`) rather than just rejecting the bound.

The marker composes with aspect bounds, since a *named* record may implement aspects:

```metel
fun render<record T: Show + { x: f64, .. }>(p: T) -> String { ... }
```

`record` is currently a valid identifier — `let record = 5;` compiles today (verified
2026-07-25) — so reserving it is a **deliberate breaking change**. It is cheap here (the
corpus uses the word only in comments) and unavoidable regardless: RFC-0120 needs the same
reservation for `record X { … }`, so taking it now costs one break rather than two.

`record` is free as a keyword: checked against `grammar.pest` (not currently reserved) and
against `stdlib/` and the test corpus (one occurrence, in a comment). No rename is needed,
unlike RFC-0098's `var`/`std::env::var` collision.

**The trailing `..` is load-bearing.** It is an *anonymous row variable* — "and a rest I am
not naming" — and its presence is what makes the bound open:

```metel
fun f(p: { x: f64 })              // a closed type: exactly x
fun g<record T: { x: f64 }>(p: T)        // a closed bound: T's row is exactly x
fun h<record T: { x: f64, .. }>(p: T)    // an open bound: T has at least x
```

Without the marker, the closed and open readings would be spelled identically and told
apart only by grammatical position — and the closed *bound* reading could not be written at
all. The named form `..R` (RFC-0121) is the same mechanism with the rest given a name.

## 2. Negative bounds

`!` already means "does not satisfy" everywhere else in the bound grammar — `T: !Copy` is
"T does not implement `Copy`". A negative row bound is the same idea applied to each named
field. Reuses `bound = { bang? ~ bound_head }` unchanged.

**The precise rule: `!{ … }` holds when the record has no field matching *any* of the listed
entries.** An entry matches when the label matches and, if a type is written, the field's
type is that type.

```metel
record T: !{ x: f64 }    // holds unless T has an `x` of type f64
record T: !{ x }         // holds unless T has an `x` at all, of any type
record T: !{ a, b: i64 } // holds when T has no `a`, and no i64-typed `b`
```

So `!{ x: f64 }` **is satisfied by a record whose `x` is an `i64`** — it has no `f64`-typed
`x`. That is the surprising case and it is deliberate; `!{ x }` is the form that rejects the
label outright.

**The complement is taken per listed field, not against the row as a whole.** Reading it the
other way — "T does not satisfy the closed bound `{ x: f64 }`" — would make `!{ x: f64 }`
hold for `{ x: f64, y: i64 }`, since a two-field record does not satisfy a closed one-field
bound. That is plainly not the intent, and the distinction is invisible until someone writes
a wider record, so it is fixed here rather than left to the implementation.

**Negative bounds take no `..`**: absence has no rest to quantify over.

## 2a. A field may omit its type, in either polarity

`{ x }` in bound position means "carries a label `x`, of any type". *(Adopted 2026-07-25,
replacing a type-position wildcard — see open question 1.)*

```metel
fun f<record T: { x, .. }>(p: T)            // has an `x`; its type is unconstrained
fun g<record T: { x, y: f64, .. }>(p: T)    // mixed: any-typed `x`, f64 `y`
fun h<record T: !{ token }>(t: T)           // carries no `token`, whatever its type
```

Earlier drafts spelled the any-type case `{ x: _ }`, with `_` a new type-position wildcard.
Omitting the annotation says the same thing with no new construct, and it matches the shape
the language already uses when a part is inferable — a record literal's `{ x }` likewise
drops what need not be written. **The wildcard is therefore not introduced.**

No ambiguity arises: a record *type* requires `ident : type` for every field
(`record_type_field`), so a bare `{ x }` is not a well-formed type and this spelling is
reachable only in bound position.

## 3. What satisfies a row bound: records, not structs

**A row bound is satisfied by a record.** A nominal `struct` does not satisfy one, however
its fields are shaped. To pass a struct where a row bound is expected, convert it first —
`h.to_record()` (RFC-0119) — which is an explicit, opt-in capability the struct's author
granted.

```metel
fun magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64 { … }

magnitude({ x = 3.0, y = 4.0 });    // a record — satisfies the bound
magnitude(some_point);              // a struct — does not, whatever its fields
magnitude(some_point.to_record());  // explicit conversion, once RFC-0119 lands
```

**This is the tier rule applied consistently, not an exception carved for bounds.** No
structural capability is ambient: a plain `struct` (tier 1) has no row-shaped behaviour at
all, and gaining any of it — conversion, bound satisfaction, row-conditional impls — is
something an author opts into.

### Why the alternative was rejected, since the corpus argued for it

An earlier draft of this section said the opposite: that any struct with matching fields
satisfies a bound implicitly, on the argument that **a bound grants no capability over the
type itself** — it only lets a generic function accept the type. That argument is correct as
far as it goes, and it is why RFC-0090 §2 and §7 both stated the implicit rule.

**An earlier version of this section rebutted it badly and the rebuttal is withdrawn.** It
claimed implicit satisfaction creates "ambient structural compatibility — the TypeScript
collapse." That conflates two different things. TypeScript's collapse is *subtyping*: a
`ScreenPos` **is** a `Point`, substitutable wherever one is expected. A row bound does
nothing of the kind — under `record T: { x: f64, .. }`, `Point` and `ScreenPos` both satisfy
the bound and remain **completely unrelated to each other**. The function is polymorphic;
the types do not collapse. Constrained genericity is not substitutability.

**The two arguments that do hold:**

- **Privacy.** Under implicit struct satisfaction, `{ secret: i64, .. }` becomes an oracle
  for private structure: outside code can learn which fields a struct has by observing which
  bounds it satisfies. That defeats RFC-0032, and it is what forced the awkward
  "public projection" rule this RFC briefly carried and then withdrew. Records-only makes
  the problem vanish rather than needing a rule.
- **Declaration-gating symmetry.** Both bound kinds are opted into; they differ only in
  granularity. An **aspect** bound is opted into *per aspect*, by writing an impl. A **row**
  bound is opted into *per type*, by choosing the `record` kind. Nothing is ambient in
  either direction, and that is a sharper statement of the tier principle than "no
  capability is ambient."
- **And the reason the opt-in is worth having, which the corpus never stated.** RFC-0090 §6
  justified the tier split on implementation cost — "the 99% of code that never writes a row
  bound pays for machinery it never asked for." That answers the wrong question. The real
  cost is borne by the *type's author*, not the compiler:

  > **A nominal type's API is what it declares. A record's API is what it contains.**

  Once a type satisfies row bounds, its field names and types are public interface whether
  the author meant that or not. Renaming a field breaks every caller who wrote a bound
  mentioning it; adding one can make the type accidentally satisfy a bound its author never
  heard of. On a `struct`, a field rename is internal. **That is the disadvantage of purely
  structural type systems, and making it opt-in is the whole point of the distinction** —
  not saving the typechecker work.

  **This also retires an observation that looked like a design flaw.** A named record can do
  everything a struct can *plus* satisfy row bounds, which reads as strict domination and
  invites "why would anyone write `struct`?". That treats every capability as desirable.
  Publishing your layout is a capability most types should decline. The relation is a trade,
  not a hierarchy:

  | | encapsulation | structural flexibility |
  |---|---|---|
  | `struct` | layout private; API is what you declare | none |
  | `record X` | layout **is** the API | full |

  Prior art agrees: **Go** deliberately refuses to let interfaces constrain on fields —
  methods only, so layout is never API. **Rust** is nominal with traits as the sole API
  surface. **OCaml** has both and uses objects sparingly. **TypeScript** is the
  counter-example that demonstrates the cost.

**Why GHC's counter-example does not bind.** GHC solves `HasField` directly against nominal
records with no conversion — the design rejected here. But GHC has **only one kind of type**,
so a structural predicate must apply to nominal types or be useless. Metel has a dedicated
kind for row behaviour, so it does not need to make structs structural: you write `record`
when you want it. **PureScript is the closer analogue** — it has both nominal `data` and
structural `Record`, and row machinery applies only to the latter, reached by unwrapping the
constructor. It sides with this RFC.

**RFC-0090 contradicted itself on exactly this point**, and the contradiction was inherited
here before being caught during this RFC's own integration review:

- §2 — "any existing nominal struct with matching fields satisfies it with no explicit
  opt-in"
- §7 — "**Resolved by the tier system (§8)** — a struct satisfies a field-shape bound just
  by having the right fields, no opt-in required"
- §8 tier 1 — "no `Lacks`/row-conditional typestate applicable to it"
- §8 tier 2 — "**no `HasField`/`Lacks` bound is ever satisfied by it implicitly**"

§7 claims to be resolved *by* §8 while asserting the opposite of what §8 says. This RFC
takes §8's side. See the superseded RFC-0090 for the note recording the conflict.

**Consequence for this release, stated plainly:** in v0.12.0 a row bound is useful over
record literals (RFC-0116) and not over structs, because RFC-0119's conversions are not in
this release. The headline case — a generic accepting any struct with matching fields — is
**deferred, not abandoned**; it arrives with RFC-0119, and needs no change to this RFC when
it does.

## 4. Relationship to RFC-0116's closed types

A closed record type and a row bound are now spelled with the same braces, distinguished by
position: after `:` in a `param` or `let` annotation it is RFC-0116's exact type; after `:`
in a `generic_param` or `where_constraint` it is this RFC's predicate. They remain
semantically distinct — a closed type cannot be used as a predicate, a bound cannot be used
as a type — and with the `..` marker present they are different token sequences, so no
position admits both readings.

---

## Open Questions

1. ~~The type-position wildcard `_` does not exist.~~ **Closed 2026-07-25 as not needed —
   the wildcard is withdrawn, not added.** It was resolved on 2026-07-24 by prototyping
   `wildcard_type = { "_" ~ !(ASCII_ALPHANUMERIC | "_") }` into `type_expr`, and that
   resolution is retracted.

   **Why it was wrong:** adding the alternative to `type_expr` makes `_` writable in *every*
   type position — `let x: _ = 5`, `fun f(x: _)`, `{ x: _ }` as a record type — while this
   RFC defined its meaning in exactly one of them. It would have shipped a construct whose
   semantics were undefined almost everywhere it could be written, to be settled later by
   whoever first hit it.

   **What replaces it:** a row field may simply omit its type (§2a). `{ x }` means "carries
   a label `x`, of any type", in either polarity. Same expressiveness, no new construct, and
   it matches the shape the language already uses where a part is inferable. A general
   inference placeholder remains available as a separate future decision, on its own merits
   rather than as a side effect of negative bounds.
2. ~~`bound_head` needs a new alternative.~~ **Resolved 2026-07-24 by the same prototype**,
   with `row_field` since amended to make the type optional (§2a):

   ```
   bound_head = { row_bound | type_path ~ ("<" ~ bound_arg ~ … ~ ">")? }
   row_bound  = { "{" ~ (row_field ~ ("," ~ row_field)*)? ~ ("," ~ "..")? ~ ","? ~ "}" }
   row_field  = { ident ~ (":" ~ type_expr)? }
   ```

   **Both were built, run and reverted**, rather than reasoned about:
   - **755 tests green** with both additions.
   - `fun magnitude<T: { x: f64, y: f64, .. }>(p: T)` **parses** — the failure is
     `path: unexpected rule row_field`, a missing parser arm, not a grammar conflict.
   - `fun send<T: !{ token: _ }>(t: T)` **parsed**, exercising the negative bound and the
     then-proposed wildcard together. The wildcard has since been withdrawn (open question 1);
     the negative-bound half of that result still stands, and the spelling is now
     `!{ token }`.
   - `fun f<T: Show + Clone>(t: T)` still works — existing named bounds unaffected.

   **The prototype predates the `record` kind marker** adopted later the same day (§1), so
   it exercised the bare `<T: { … }>` form. **Three further grammar changes are therefore
   not yet verified**, and they are the only unprototyped part of this RFC:

   ```
   generic_param    = { record_kw? ~ ident ~ (":" ~ bound_list)? }
   where_constraint = { record_kw? ~ ident ~ ":" ~ bound_list }
   record_kw        = @{ "record" ~ !(ASCII_ALPHANUMERIC | "_") }
   ```

   Note `generic_param`'s bound stays optional, which is what admits the bound-less
   `<record T>` form §1 relies on. Reserving `record` is a deliberate breaking change —
   `let record = 5;` compiles today — and is discussed in §1.

   **One detail the prototype settled that the RFC had not specified:** the rule above
   admits the trailing `..` only *after* at least one field, so `{ .. }` alone does not
   parse. **That is now load-bearing rather than incidental:** it is precisely why the
   `record` marker cannot be dropped, since "any record, whatever its shape" has no other
   spelling than `<record T>` (§1). Written as a bound it would have to be `{ .. }`, which
   the grammar rejects.
3. ~~Cross-module private-field leakage.~~ **Withdrawn 2026-07-24 — the question does not
   arise for this RFC, and the resolution briefly recorded here is retracted.** It was
   resolved as "a bound matches the *public projection* of a type's row," which made bound
   satisfaction module-relative and left a hole for negative bounds (`!{ secret: _ }` would
   have succeeded outside the declaring module and failed inside — an affirmatively wrong
   answer, not merely a non-match).

   **Both the rule and its hole were artifacts of §3's earlier claim that structs satisfy
   bounds directly.** Under §3 as it now stands, a row bound is satisfied by a *record*, and
   an anonymous record has no declaring module and no private fields — so there is nothing
   to project and nothing to leak.

   **The question is real and moves to RFC-0119**, where it belongs: what does
   `to_record()` produce for a struct with private fields, and who may call it? That is a
   question about a *conversion*, which is a capability, which is what the tier system
   actually governs. *(From RFC-0090 OQ7, via RFC-0116 OQ3, now RFC-0119's.)*
4. **Coherence between structural and nominal impl selection** — **real, but not reachable
   in v0.12.0, and therefore not blocking.** An ordinary `extend Point: Display` is keyed on
   nominal identity; RFC-0121's row-conditional impls are keyed on shape, and if a value
   matched both there would be no written rule for which wins. **That collision needs impls
   keyed on rows, which is RFC-0121 and is not in this release** — this RFC contributes
   bounds only, and a bound selects nothing. Re-checked rather than assumed: nothing in
   RFC-0116 or this RFC lets an impl be written against a row. Deferred to RFC-0121, where
   open question 3 above also lands. *(From RFC-0090 OQ6.)*
5. **How does row-membership checking relate to RFC-0096's auto-impl algorithm?**
   RFC-0096 §7 worked out that `HasField`-style satisfaction is *existential*, not the
   universal recursion `Send`/`Sync`/`Linear` use, so it does not fit that algorithm. The
   bare-row spelling does not change this — only the surface. What checks a row bound, and
   where it lives in the typechecker, is unspecified.

---

## References

- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` §1, §2, §7 — the source
- RFC-0116 (Anonymous Record Types) — the row syntax reused in bound position
- RFC-0121 (Open Rows) — `..R`, the named form of §1's anonymous `..`
- RFC-0096 (Auto-Impl Aspects) §7 — works out precisely how row-membership differs from
  the `Send`/`Sync`/`Linear` auto-impl algorithm, and flags the same coherence gap
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern this extends structurally
- RFC-0060 (Aspect Impl Coherence), RFC-0061 (Structural Aspect Bounds) — the coherence
  checking OQ4 would extend
- RFC-0032 (Field-Level Visibility) — the visibility model OQ3 must be reconciled with
- `reports/substructural-types/nominal-types-as-branded-rows.md` §12 — the derivation of
  the bare-row bound spelling and why `HasField` was replaced outright

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
