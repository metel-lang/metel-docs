---
id: structural-records
title: "Structural Records"
type: report
status: active
last_synced_against_model: '2026-07-06'
supersedes: "reports/memory-model/linear-types-and-structural-records-2026-07-06.md section 5"
---

# Structural Records

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Nothing here is ratified. Split out of the combined
linear-types/structural-records report so this thread can grow on its own terms rather
than becoming one ever-larger file — see `README.md` for why.*

See `linear-types.md` for the `Linear` aspect, the multiplicity lattice, and partial
consumption — this document assumes that context and focuses on the structural-typing
half specifically.

---

## 1. Two complementary mechanisms, not one import

Rather than adopting OCaml/PureScript's row-kind system wholesale, this split into two
pieces that each extend something Metel already has:

- **`HasField<"name", T>`-style auto-derived structural aspect bounds** — flow-*in*sensitive,
  for generic code that wants to work on "any struct with a matching field" regardless
  of nominal identity. This is GHC Haskell's actual shipped answer to the same problem
  (`HasField "x" MyRecord Float`, auto-derived, no shared row-kind system needed), and
  translates directly into an extension of RFC-0080's auto-impl pattern: one marker
  aspect *family* instead of one aspect, same machinery.
- **Phantom residual markers** — flow-*sensitive*, per-value, tracking which fields
  *this specific binding* has had consumed. See `linear-types.md` §3 — this extends
  RFC-0071 §7 / RFC-0024 §9's `LinearEnv` rather than the aspect system (aspect
  membership is a global, static fact about a type; "has this field been consumed at
  this program point" is exactly what move-tracking already does, not what aspects do).

## 2. What this buys for partial drops

Re-examining RFC-0071 §7's blanket ban on partially moving `Drop` types: the actual
hazard is narrower than the rule. Recursive per-field drop already safely handles
fields piecemeal — the real danger is specifically that a *custom* `Drop::drop` body
is arbitrary code that might read *any* field, and the compiler has no way to know
which. Proposed resolution: let a `Drop` impl **declare** which fields its body
depends on —

```metel
impl Drop for Handle {
    fun drop(self: Handle) uses (fd) {
        close_fd(self.fd);
    }
}
```

— checked (not just asserted) against the method body, so `tag` may be moved out of
`Handle` first (the residual is still `HasField<"fd", i64>`, all `drop` needs) while
moving `fd` itself out remains rejected. Declared rather than inferred, for the same
reason this whole cluster has repeatedly preferred explicit-and-checked over
implicit-and-inferred (RFC-0065's elision-is-never-a-silent-choice principle,
Storage Transparency): inferring field usage from the body means an unrelated internal
change to `drop` silently changes which partial-move patterns are legal everywhere
else, an action-at-a-distance failure mode.

**Not resolved:** if `drop`'s body calls a helper method, "what does this actually
touch" has to become transitive across that call — either the helper needs its own
declared field-usage that composes through, or field-usage becomes a real effect
system. This is a genuine open problem, not a syntax detail.

**Novelty check:** no mainstream language does this as far as this exploration is
aware — Rust's restriction is exactly as blunt as Metel's current one, for the same
reason (no per-`Drop`-impl field-dependency tracking exists there either). If worked
out, this would be a genuinely distinctive capability.

## 3. The unifying move: `record` as a real type-former

Once `record` exists, a partial-consumption residual (`linear-types.md` §3, Option C)
stops being a bespoke, invisible marker — it *is* a record type. Consuming
`Foo { a: A, b: B }`'s field `a` produces a value typed `record { b: B }`: the struct's
own remaining fields, literally. Since a record containing a linear or `Drop`-needing
field is itself linear/drop-relevant by the same structural composition rule as
ordinary structs, "the remainder still needs consuming" is no longer a rule anyone had
to write — it's the same fact, restated.

Concrete shape:

- **Closed by default.** `record { x: 1.0, y: 2.0 }` as a value is an exact,
  concrete product — no hidden extra fields. This matters specifically because of the
  tension in §8: an *open* record (accept "at least these fields") permits width
  subtyping, i.e. silently forgetting fields, which is exactly what non-`Copy`
  ownership exists to prevent. Closed-by-default sidesteps this for the common case.
- **As a bound, sugar over a bundle of `HasField` facts.** `record { x: f64, y: f64 }`
  in a parameter position means "anything satisfying `HasField<"x", f64> +
  HasField<"y", f64>`." Combined with §1's auto-derivation, **any existing nominal
  struct with matching fields satisfies it with no explicit opt-in** — Go's implicit
  interface satisfaction (a type satisfies an interface by having matching methods,
  with no `implements` declaration) is the closer real-world precedent here than
  OCaml, since it's the same "structural match, no declared relationship" story
  without OCaml's object/method-dispatch baggage, which would be redundant with
  Metel's existing aspects anyway.
- **Open generalization reuses the existing channel pattern.** If genuine row
  polymorphism is wanted later — "at least these fields, generic over the rest" — that
  is exactly the shape of `<&r>` and `<@a>`: an explicit compile-time parameter in the
  `<>` channel. Proposed form: `<row R>`, e.g. `fun get_x<row R>(p: record { x: f64,
  ..R }) -> f64`. Consistent with the pattern this cluster already uses everywhere —
  open/generic behavior is an explicit declared parameter; concrete use stays closed.

## 4. Recommended build order

1. **Closed `record` types + `HasField` auto-derivation first.** Sufficient on its own
   for both partial linear consumption and partial drops (`linear-types.md` §3, §2
   above). No row-kind, no row-unification algorithm — a closed record over *N* fields
   is a product type with a compiler-synthesized identity; the space of "which subset
   remains" is bounded by 2^*N*, trivial for realistic struct sizes.
2. **`<row R>` open generics later, separately, only if a real duck-typing need
   materializes.** This is where the actual cost lives (§8) — treat it as its own
   decision with its own timeline, not a prerequisite for §2/step 1.

## 5. Typestate via row-conditional impls

If step 2 of §4 is ever pursued, it enables something considerably more compelling
than plain duck-typing: **typestate**, realized directly by the row rather than by a
hand-rolled phantom marker. With a row-typed record, the state *is* the row, and
RFC-0036's conditional impl blocks generalize directly from aspect conditions to
row-shape conditions:

```metel
impl<row R: HasField<"token", Token>> Session<R> {
    fun authenticate(self) -> Session<R without "token"> { ... }
}

impl<row R: Lacks<"token">> Session<R> {
    fun send_data(&self, bytes: Bytes) { ... }
}
```

`send_data` does not exist on a `Session` whose row still has `token` — not a runtime
precondition, an absent method. Calling it too early is the same class of error as
calling a method that was never defined.

**This is one of (at least) two competing typestate encodings on the table, not the only
one — and which is canonical is not yet decided (too early).** `brand-types.md` (RFC-0076's
own applications section) does typestate via a phantom type parameter — `File<'b, Open>` —
the conventional approach, simpler, already well-precedented (Rust idiom). Row-conditional
impls are more novel and tie into the larger structural-records vision. One consideration
for whenever this *is* decided: **making row-conditional the canonical path would pull
open-row generics, row-conditional coherence, and the width-subtyping rule (§8) onto the
critical path**, which the build order deliberately avoids — a point in the brand form's
favor, but not treated as decisive. See `brand-types.md` §3 for the comparison and
`README.md` for the cross-thread open question.

**Where row-conditional typestate is compelling, concretely:**

- **Protocol/session state machines** — handshake steps, auth flows, parser
  progress — where each transition adds or removes a marker field and the available
  API tracks it exactly. The standard motivating example for row types in the
  literature, for this reason.
- **Builders, in the dual direction.** Consumption removes a field from a row;
  building one up adds one. A config builder where `.with_timeout()` requires `R:
  Lacks<"timeout">` and returns `R + "timeout"` prevents setting the same field twice,
  at compile time.
- **A linear-allocator session.** A wrapper whose row tracks which capability tokens
  are still held — `{alloc_token, free_token}` — where finishing allocation consumes
  `alloc_token` from the row, moving into a state where only `free`-adjacent methods
  exist. This is the same linearity guarantee from `linear-types.md`, generalized from
  "consume exactly once" into "consume in the right order, proved by the type system"
  — a strictly stronger property than plain `Linear` alone gives, and it is exactly the
  brand-report's "token-gated access" pattern wearing a structural-records costume; see
  `brand-types.md`.

**What it costs, beyond §8's general row-polymorphism costs:**

- **Coherence has to grow, not just get reused.** RFC-0036/RFC-0060's conditional-impl
  coherence checking would need extending to row-shape conditions specifically,
  ensuring two conditional impls (one gated `HasField`, one gated `Lacks`) can't both
  apply to some under-constrained row-variable case. Same framework, genuine
  additional work, not free.
- **Diagnostics need their own care.** "Method does not exist" is a worse error than
  "method requires row to contain `authenticated`, but this session's row is
  `{tcp_connected}`" — getting the legible version is not automatic just because the
  mechanism works.
- **Bounded, but worth remembering.** The 2^*N*-ish monomorphization argument from §4
  still holds for realistic protocol step-counts, but a state machine modeled with many
  independent flags rather than a handful of ordered steps could push on this more than
  a plain closed record would.

This is not part of the recommended build order in §4 — it is a reason step 2 might
eventually earn its cost, not an argument for taking on that cost now.

## 6. Where records are — and aren't — usable

Working through Metel's actual type-position taxonomy position by position, rather
than asking in the abstract:

**Usable, no special treatment needed:**

- **Ordinary value positions** — parameters, returns, `let` bindings, struct/enum
  fields. Records are just types: `fun midpoint(a: record { x: f64, y: f64 }, ...) ->
  record { x: f64, y: f64 } { ... }`.
- **Allocator-tagged and borrowed positions** — `@a record { x: f64, y: f64 }`, `&r
  record { x: f64, y: f64 }`. A record is an ordinary owned value; it participates in
  `@a T` / `&r T` exactly like a struct.
- **Pattern matching** — not optional; load-bearing for the whole partial-consumption
  mechanism (`linear-types.md` §3), not an extra capability.
- **Generic instantiation** — `T` unifying against a concrete record is ordinary
  unification, nothing record-specific.
- **Aspect impls, if the aspect is local to you** — reusing RFC-0061's orphan-rule
  treatment of `T[]`/tuples/function types directly: `aspect impl Describe for record
  { x: f64, y: f64 } { ... }` is legal when `Describe` is your own aspect.
- **Auto-derived aspects** — `Send`, `Sync`, `Linear` all extend to records via the
  same field-composition rule already used for structs; RFC-0080 §3.2's rule already
  reads generically enough ("a struct *or enum*") to cover this without amendment.
- **Open records whose row variable is only ever passed through, never inspected** —
  same reasoning as tag-only allocator preservation: if nothing is discarded, it
  doesn't matter what the row variable's contents are.

**Not usable, and why:**

- **Inherent impls.** `impl record { x: f64, y: f64 } { fun magnitude(&self) -> f64
  {...} }` is banned outright — records have no nominal owner for orphan-rule
  purposes, so two unrelated modules could write conflicting inherent methods for the
  same shape with no principled way to say which wins. RFC-0061's own reasoning for
  `T[]`, applied to user-defined shapes.
- **Aspect impls for a non-local aspect.** `aspect impl Display for record { x: f64, y:
  f64 } { ... }` is banned the same way, the other direction — you may implement your
  own aspect for a shape you don't own, but not someone else's stdlib aspect for a
  shape you also don't own.
- **Custom `Drop` logic, specifically.** A corollary of the rule above, worth stating
  on its own because the consequence matters in practice: `Drop` is a stdlib aspect,
  never local to ordinary user code, so **no record can ever carry custom teardown
  logic** — only nominal structs can. Anything needing its own destructor behavior has
  to be wrapped in a struct first.
- **Serving as an allocator type.** `struct Cache(@a: record { block: RawBlock }) {
  ... }` is a category mismatch, not a coherence technicality: RFC-0063 §2's
  disjointness story depends on allocator identity being per-*instance* (two
  `BumpAlloc` values of the same type still carry distinct tags), while a record's
  entire premise is that two values with the same row are interchangeable. Something
  whose job is proving "these are different even though they look the same" cannot
  also be the thing whose job is "these are the same because they look the same."
- **Using `record { ... }` itself as a bound.** `fun f<T: record { x: f64 }>(v: T) ->
  f64` isn't meaningful — a closed record type names a concrete shape, it isn't a
  predicate. `HasField`/`Lacks` (§1) are the bound forms; `record { ... }` stays for
  concrete positions.
- **Open records where a non-empty row-variable remainder is silently discarded,
  without a guarantee everything in it is `Copy`.** `fun get_x<row R>(p: record { x:
  f64, ..R }) -> f64 { p.x }` lets `R` vanish the moment the function returns — if a
  caller's `R` contains a `Linear` or `Drop`-bearing field, that's a silent leak or
  soundness hole, not a style issue (§8's width-subtyping tension, concretely). No
  bound expressing "every field in `R` is `Copy`" is proposed anywhere yet (see §9),
  so this pattern should be rejected outright for now rather than permitted without a
  guardrail.

## 7. Considered and declined: a fully record-based type system

The natural next question, given §6, is whether records should stop being an
*addition* alongside nominal structs and become the *foundation* everything else
reduces to — nominal types as pure sugar over an underlying record. Considered and
declined, for reasons that go beyond style:

- **Enums don't fit.** Records are products (all these fields, simultaneously); enums
  are sums (exactly one shape, tagged, at runtime). A records-only foundation has
  nothing to say about sum types on its own — it would need a *separate* structural
  mechanism (row polymorphism's dual, sometimes "variant rows," OCaml's polymorphic
  variants) with its own unification story, and that mechanism has a well-known cost:
  materially weaker exhaustiveness checking, since the compiler can't always know the
  full set of possible tags for an open variant. Metel's enum system leans on
  closed-world exhaustiveness as a real, hard-won property (the bottom-type and
  unreachable-pattern work); trading it away for structural uniformity would be a
  regression, not a simplification.
- **Primitives don't fit either.** `i64` as "a one-field record" is indirection with
  no payoff.
- **Nominal identity can't actually become sugar — it's load-bearing.** §6 already
  establishes records can't be allocators (disjointness needs per-*instance* identity,
  which is precisely what structural interchangeability can't express) and can't carry
  inherent impls or non-local aspect impls (no owning module). If "structs are sugar
  over records," the sugar has to reintroduce a real, separate identity/ownership tag
  for any of that to keep working — at which point the reframing hasn't reduced what
  the system has to track, only renamed the part that was never really sugar.
- **Implementation cost for the common case.** Routing every ordinary struct through
  row-unification machinery means the 99% of code that never writes `record {...}` or
  bounds on `HasField` pays for machinery it never asked for — the reverse of keeping
  the common path simple and making the general mechanism strictly additive, which is
  how the current split (§1) already behaves.

**Verdict:** records as the natural representation for structural, identity-free data
— yes, exactly where `linear-types.md` §3 and §3 above already use it. Records as the
universal foundation — no. The two things records are structurally bad at (sum types,
identity) are things the rest of the language genuinely needs, and sugar can't quietly
bring them back without admitting they were never sugar in the first place.

## 8. Consequences and costs, if the fuller version is pursued

- **Row-kinded type variables and row unification** — a genuinely new piece of the
  elaborator/type-inference system (Rémy/Wand-lineage row unification: matching common
  labels, then recursively reconciling remainders), not a small patch, and only needed
  for step 2 of §4.
- **Object-style (OCaml) vs. plain-record-style (Elm/PureScript) — recommend plain
  records.** Metel's aspects already cover interface-with-methods polymorphism; adding
  a second, structural mechanism for the same job would be redundant, not
  complementary.
- **Width subtyping vs. affine/linear ownership — the genuinely novel problem.**
  Row polymorphism's defining move (silently using a wider record where a narrower one
  is expected, forgetting the extra fields) is harmless in garbage-collected OCaml,
  Elm, and PureScript. None of them have affine/linear ownership, so none of them had
  to ask what happens when a forgotten field isn't garbage — it's a resource, or it
  owes a linear consumption. Proposed rule: width subtyping (implicit field-forgetting)
  is only sound when every silently-dropped field is `Copy`; anything `Drop`- or
  `Linear`-bearing forces explicit handling. Not decided; this is the one piece here
  with no precedent to lean on at all.
- **Monomorphization vs. erasure.** The position report leans hard on
  storage-transparent constructs monomorphizing at compile time, erased at runtime
  (`../memory-model/lifetimes-vs-regions-2026-07-02.md` §8 item 7). PureScript's row
  polymorphism typically compiles via runtime dictionary-passing, not monomorphization.
  A zero-cost row-polymorphic feature for Metel would be its own implementation
  project, not something inherited for free by copying the reference languages'
  designs.
- **Implicit structural satisfaction is a real departure from how the rest of the
  aspect system works.** Every other aspect requires an explicit `impl Aspect for
  Type`. Go's implicit interfaces draw exactly this criticism: two unrelated structs
  that happen to both have an `id: i64` field satisfy `record { id: i64 }` whether or
  not that was intended, with nothing marking it deliberate. Given how consistently
  this cluster has favored explicit-and-checked over implicit-and-inferred elsewhere,
  this is worth a deliberate decision, not a default: either accept fully implicit
  satisfaction, or require a lightweight opt-in (e.g. `struct Point derives record {
  ... }`) before a struct is usable structurally.

## 9. Reconciling with the inverse direction: structural types as the foundation

*Added 2026-07-07, from a design conversation exploring the opposite direction from §1:
instead of records as an additive bound layer over an unchanged nominal `Type::Named`,
what if every struct were represented internally as `(row, brand)` — a structural shape
plus an identity tag — making named types a special case of structural types rather than
the reverse? Real precedent exists for the strong version of this (TypeScript: every
named type is a label over a structural descriptor, with nominal safety faked via
manually-added brand fields when it's needed at all; OCaml's object/row system, where a
class name is a constructor convenience over a structural object type).*

**This is not a re-litigation of §7.** §7 already considered exactly this — "nominal
types as pure sugar over an underlying record" — and declined it, for a reason that
still holds at full strength: nominal identity is load-bearing (disjointness, inherent
impls, non-local aspect impls all need it), so the sugar has to reintroduce a real
identity tag to keep working, "at which point the reframing hasn't reduced what the
system has to track, only renamed the part that was never really sugar." Nothing below
disputes that verdict. What survives is narrower: not *elimination* of the tag, but
*reuse* of it.

**Surviving claim 1 — the tag doesn't need to be a bespoke fourth mechanism.**
`brand-kind-unification.md` already proposes that `@a` (allocator tags), `&r` (lifetime
anchors), and `'c` (brands, RFC-0076) are one underlying identity kind under three
sigils. A struct's inevitable identity tag (§7's point) is a plausible fourth surface use
of that same `'c`-role kind, not a new kind alongside it — implementer economy (one
freshness/erasure/rigidity checker), not a new concept for users, consistent with that
document's own recommendation in its §7 not to surface the unification itself. See that
document's Open Questions §3 for the specific new question this raises (whether nesting
a brand-carrying struct inside `@a`/`Rc` is an intentional role-crossing or just ordinary
composition of the same role at two levels — unresolved there, not here).

**Surviving claim 2 — partial consumption's residual can reuse this document's own
row machinery instead of a separate mechanism.** `linear-types.md`'s Option B (the
currently-adopted floor: explicit residual extraction via side-table, no row kind) exists
specifically to avoid needing row unification before Phase 3. But if a struct is already
internally `(row, brand)`, the residual after consuming one field is just `(row - field,
brand)` — the *same* thing `Lacks<"field">` (§5) already names for open records, applied
to a nominal residual with its brand held fixed rather than erased. That would make
nominal partial consumption and this document's row-conditional typestate one mechanism
applied to two syntactic forms, rather than two designs that need separately justifying
and separately maintaining.

This may also be the missing piece for `linear-types.md`'s blocked Option C: the open
question there is what type a borrow taken *before* a downgrade has *after* it. A row
gives the downgrade a precise strong-update semantics (shrink the row, keep the brand)
and — because a row decomposes a value into named slots the checker can already reason
about independently — lets borrow exclusivity be checked per *field* rather than only
per whole struct, narrowing exactly what must be un-borrowed for the consumption to be
legal. Promising, not proven; no soundness argument is written down here, only the shape
of one.

**Scope stays where §7 already drew it.** This is a representation-sharing move for
structs specifically. It says nothing new about enums (§7's sum-type objection is
untouched — no variant-row mechanism is proposed here) or primitives (still not
records-shaped, still not worth the indirection).

**Two new open questions this raises, appended to §10:**

- **Coherence needs a specificity rule between the two axes an impl can now match on.**
  An ordinary `impl Display for Point` is brand-keyed; RFC-0061's structural/blanket
  impls (`impl<row R: HasField<"x", f64>> Display for record R`) are row-keyed. If a
  `Point` value matches both, which wins? The obvious default — brand-keyed beats
  row-keyed blanket impls, more-specific-wins — is not written down as a rule anywhere,
  and RFC-0060/RFC-0061's coherence checking does not yet account for a second axis at
  all.
- **Field-level visibility (RFC-0032) and structural matching haven't been reconciled.**
  If `HasField<"secret", T>` is checked directly against a struct's row, does code
  outside the declaring module get to observe — or structurally match against — a
  private field? It shouldn't, which means the row isn't a single flat structure per
  brand; cross-module structural matching needs to see only a *public projection* of the
  row, with private fields invisible to `HasField`/`Lacks` checks from outside the
  module. This does not appear to be addressed anywhere else in this cluster.

## 10. Open questions

1. Ship closed `record` types only for now, or also `<row R>` open generics
   immediately (§4) — recommend closed-only first; not ratified.
2. Plain-record style vs. OCaml-object style (§8) — recommend plain records; not
   ratified.
3. Width-subtyping-requires-`Copy` rule (§8) — proposed with no existing precedent to
   verify it against; not ratified. No bound expressing "every field in row `R` is
   `Copy`" (an `AllCopy`-shaped predicate) is defined yet, so open records with a
   discarded, uninspected remainder have to be rejected outright until one is designed.
4. Implicit vs. explicit-opt-in structural satisfaction (§8) — genuinely open, no
   leaning stated; needs a deliberate decision either way.
5. Transitive field-usage checking when a `Drop` body calls helper methods (§2) —
   unresolved, no proposal yet.
6. Row-conditional impl coherence (§5) — extending RFC-0036/RFC-0060's conditional-impl
   checking to `HasField`/`Lacks`-style row conditions is asserted to be tractable but
   not worked out; no concrete overlap-checking rule proposed yet.
7. **Phantom-type-parameter typestate (`brand-types.md`) vs. row-conditional-impl
   typestate (§5) — which is canonical, or do both stay, and for which cases?** Not
   resolved — too early to decide; tracked as a cross-thread question in `README.md`. The
   considerations (brand form cheaper and covers state-plus-identity; row form more novel,
   needs deferred open-`<row R>`) are recorded in `brand-types.md` §3 as inputs.
8. **Brand-vs-row impl coherence priority (§9)** — no specificity rule between
   brand-keyed and row-keyed blanket impls is written down; RFC-0060/RFC-0061's
   coherence checking doesn't yet model a second matching axis.
9. **Private-field leakage into cross-module structural matching (§9)** — `HasField`/
   `Lacks` checks need a public-only projection of a struct's row when checked from
   outside its declaring module; no mechanism for this projection is designed yet, and
   the interaction with RFC-0032 field visibility isn't addressed anywhere in this
   cluster.

## Example programs

Illustrative only — see `README.md`'s status note on the whole directory.

### Records, `HasField`, and where they stop being usable

```metel
let point = record { x: 1.0, y: 2.0 };   // closed record — exact shape

fun magnitude<T: HasField<"x", f64> + HasField<"y", f64>>(p: T) -> f64 {
    (p.x * p.x + p.y * p.y).sqrt()
}

println("mag = ${magnitude(point)}");

// Any nominal struct with matching fields satisfies the same bound, no opt-in (§6):
struct ScreenPos { x: f64, y: f64, z_index: i64 }
println("mag = ${magnitude(ScreenPos { x: 3.0, y: 4.0, z_index: 1 })}");

// Not usable, per §6:
//   impl record { x: f64, y: f64 } { fun scale(&self, k: f64) -> ... }
//   -- no owning module; inherent impls on records are banned outright.
//   aspect impl Display for record { x: f64, y: f64 } { ... }
//   -- Display isn't local to this module; banned the other direction of the same rule.
```

### Typestate via row-conditional impls

```metel
struct Session<row R> { data: record { ..R } }

impl<row R: HasField<"token", String>> Session<R> {
    // `R without "token"` is illustrative row-subtraction notation, not proposed
    // syntax; only the resulting bound shape is meant here
    fun authenticate(self) -> Session<R without "token"> { ... }
}

impl<row R: Lacks<"token">> Session<R> {
    fun send_data(&self, bytes: String) {
        println("sending: ${bytes}");
    }
}

fun main() -> i64 {
    let s = Session { data: record { token: "secret", host: "example.com" } };
    let authenticated = s.authenticate();
    authenticated.send_data("hello");
    // s.send_data("hello");   -- would not compile: s's row still has `token`
    0
}
```
