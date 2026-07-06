---
id: linear-types-and-structural-records
title: "Linear Types and Structural Records — A Design Exploration"
type: report
created_date: '2026-07-06'
---

# Linear Types and Structural Records — A Design Exploration

*Exploration, not a decision — nothing in this report is ratified, and nothing in it
should be read as amending any RFC. It exists to make an already-tracked deferral
cheaper to resolve later, not to pre-empt that resolution. The deferral itself is
recorded in RFC-0063 §9 (items 1, 2, and 5) and the position report
`lifetimes-vs-regions-2026-07-02.md` §11: allocator teardown discipline (affine vs.
linear) and `drop`'s interaction with it are open with no urgency (the allocator layer
is Phase 3 step 3 — nothing implementation-side depends on them yet); partial
consumption of a linear struct is open **with** a deadline — it has to be settled
before RFC-0071 (move semantics) / RFC-0067 (borrow checking) implementation begins
(Phase 3 steps 1–2). This report is the working-through of that last item, and of how
far the same machinery can be pushed toward a general "structural records" feature.*

---

## 1. Why this exists

The allocator-teardown discussion (RFC-0063 §9 item 1) raised whether allocators
should be `Linear` rather than ordinary affine values, with a designated `.free()` as
the only consumer. Pursuing that surfaced a harder, pre-existing question: what
happens when a linear-typed struct has more than one linear field, and you want to
consume them separately rather than all at once? This is not a new problem — RFC-0024
(Linear Types, superseded) already had an answer for the narrow case — but the
question of whether a *better* answer exists turned out to connect to a much larger,
genuinely distinctive feature: structural records. This report captures that whole
line of exploration in one place.

---

## 2. Prior art already in the repo

- **RFC-0024 (Linear Types, superseded by the now-refused RFC-0028).** Worked out a
  complete `linear` keyword mechanism: exactly-once consumption, a struct containing a
  linear field is *automatically* linear ("need not (and should not) be repeated" —
  unlike `Copy`'s opt-in-at-every-level model), a narrow `@T` read-reference (now
  unusable as spelled — the split model has since reassigned `@` to allocator tags;
  `&T`, RFC-0067, is the modern equivalent), and — critically — `drop` for a linear
  value is specified as a **checker-only escape hatch that does not call any
  destructor**. §7 gives the existing partial-consumption rule: destructuring may bind
  and individually consume each linear field, but *ignoring* one with `_`/`..` is a
  compile error.
- **RFC-0049 (`linear fun` type system, draft, orphaned) and RFC-0046 (Linear Closure
  Capture, refused).** Document the exact hazard a naive `drop`/linearity interaction
  hits: *"`drop(f)` appears to work but leaves captured values dangling"* — a generic
  `drop` that satisfies a linearity obligation without running real cleanup is a
  known, previously-encountered bug class, not a hypothetical one.
- **RFC-0080 / RFC-0081 (accepted).** `Send` is declared as `aspect Send { }` — a
  marker aspect with no methods — and is an **auto-impl**: *"the compiler
  automatically derives `Send` for any type all of whose fields are `Send`... No
  annotation is needed."* RFC-0081's negative impls (`impl !Send for MyType {}`) are
  the override. This is the exact template §3 below reuses for `Linear`.
- **RFC-0071 §7 (accepted).** The current affine partial-move rule: moved fields are
  tracked in a side-table, invisible in the value's type; a partially-moved value may
  not be used as a whole; a `Drop`-implementing type may not be partially moved at all,
  because the destructor needs the complete value.
- **RFC-0061 (accepted).** Narrower existing precedent for "structural" auto-impl
  propagation — specifically for the built-in `T[]`/tuple/function-type constructors,
  not user-defined types — and confirms `Send`, `Sync`, and **`Drop`** already
  propagate through `T[]` structurally via the RFC-0060 §4 auto-impl rule.
- **RFC-0026 (Unsafe Blocks, deferred).** Names "custom allocators" as a motivating
  use case, blocked on the now-refused RFC-0028, still written against pre-split
  pointer syntax. Needed for anyone actually implementing a custom `Alloc`/`Linear`
  type's teardown logic, independent of everything below.

---

## 3. `Linear` as an aspect

`aspect Linear { }` — a marker aspect, structurally identical in form to `Send`. Two
properties, both reusing existing accepted machinery rather than inventing new:

- **Auto-impl, not opt-in.** A struct containing a `Linear` field is automatically
  `Linear` (RFC-0080 §3.2's rule, substituting `Linear` for `Send`), matching RFC-0024's
  original "need not be repeated" behavior. This is the right template, not `Copy`'s —
  `Copy` requires re-declaring `impl Copy for X {}` at every level even when
  structurally derivable, which would be a genuine safety hole here: forgetting to
  redeclare `Linear` on a composed type must not silently make it non-linear.
  `impl !Linear for X {}` (RFC-0081) is the escape hatch for the rare case a type would
  otherwise structurally qualify but shouldn't.
- **Mutually exclusive with `Copy`** (obviously — free duplication and exactly-once
  consumption can't coexist) **and with `Drop`.** `Drop`'s only triggers — implicit
  scope-end, and the generic `drop(x)` free function — have no legitimate firing point
  for a value that can never legally reach scope-end unconsumed, and that a `T: !Linear`
  bound on `drop` (mirroring RFC-0072's negative-bound mechanism) excludes from the free
  function entirely, specifically to avoid RFC-0049's documented failure mode
  recurring for `Linear` generally. A linear type's teardown logic instead lives in an
  ordinary, author-named consuming method (`.free()`, `.close()`, whatever fits),
  called directly.

None of this is ratified. It's the leading candidate shape, not a decision.

---

## 4. Partial consumption

### 4.1 What already exists

RFC-0024 §7 solves the *safety* problem (no linear field silently unconsumed) for the
all-at-once destructuring case only, via a special-cased rule bolted onto
destructuring specifically. It does not cover RFC-0071 §7's broader sequential,
one-field-at-a-time style (`let a = p.a;` now, `let b = p.b;` later).

### 4.2 The proposed alternative

Instead of a side-table update, each field consumption produces a **residual type** —
structurally, "the struct minus that field." The payoff: if the residual still
contains a linear field, it is *still linear* by the ordinary composition rule from
§3 — "you must still consume the rest" falls out automatically, with no bespoke rule
needed the way RFC-0024 §7 needed one. It also sidesteps RFC-0071 §7's
`Drop`-needs-the-whole-value hazard entirely, since `Linear` and `Drop` are not
expected to coexist (§3) — there is no destructor waiting on a complete value to
protect against.

### 4.3 Does this need full row polymorphism?

No, and this is the load-bearing simplification for the *narrow* case. OCaml's object
row types, Elm's records, and PureScript's row-polymorphic records (`Record.delete`,
the actual precedent for "field removal produces a residual type") all need **open**
rows — a row variable standing for an unknown, possibly-infinite remainder — because
their motivating use case is open-world structural compatibility across types that
were never declared related (duck typing). Metel's motivating use case here is the
opposite: a single, already-nominal struct's own, statically-fixed, finite field set.
Tracking "which of *this* struct's known fields remain" needs no unknown-remainder
variable at all. A phantom marker riding the existing nominal type — structurally the
same trick as `PhantomBrand<'b>` (RFC-0074) or an allocator tag (RFC-0063 §2) — is
sufficient for this narrow case, with no new type-formation kind required.

---

## 5. Pushing further: structural records

### 5.1 Two complementary mechanisms, not one import

Rather than adopting OCaml/PureScript's row-kind system wholesale, the exploration
split into two pieces that each extend something Metel already has:

- **`HasField<"name", T>`-style auto-derived structural aspect bounds** — flow-*in*sensitive,
  for generic code that wants to work on "any struct with a matching field" regardless
  of nominal identity. This is GHC Haskell's actual shipped answer to the same problem
  (`HasField "x" MyRecord Float`, auto-derived, no shared row-kind system needed), and
  translates directly into an extension of RFC-0080's auto-impl pattern: one marker
  aspect *family* instead of one aspect, same machinery.
- **Phantom residual markers** — flow-*sensitive*, per-value, tracking which fields
  *this specific binding* has had consumed. This is §4.2, extending RFC-0071 §7 /
  RFC-0024 §9's `LinearEnv` rather than the aspect system (aspect membership is a
  global, static fact about a type; "has this field been consumed at this program
  point" is exactly what move-tracking already does, not what aspects do).

### 5.2 What this buys for partial drops

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

### 5.3 The unifying move: `record` as a real type-former

Once `record` exists, §4.2's residual stops being a bespoke, invisible marker — it *is*
a record type. Consuming `Foo { a: A, b: B }`'s field `a` produces a value typed
`record { b: B }`: the struct's own remaining fields, literally. Since a record
containing a linear or `Drop`-needing field is itself linear/drop-relevant by the same
structural composition rule as ordinary structs, "the remainder still needs
consuming" is no longer a rule anyone had to write — it's the same fact, restated.

Concrete shape:

- **Closed by default.** `record { x: 1.0, y: 2.0 }` as a value is an exact,
  concrete product — no hidden extra fields. This matters specifically because of the
  tension in §6: an *open* record (accept "at least these fields") permits width
  subtyping, i.e. silently forgetting fields, which is exactly what non-`Copy`
  ownership exists to prevent. Closed-by-default sidesteps this for the common case.
- **As a bound, sugar over a bundle of `HasField` facts.** `record { x: f64, y: f64 }`
  in a parameter position means "anything satisfying `HasField<"x", f64> +
  HasField<"y", f64>`." Combined with §5.1's auto-derivation, **any existing nominal
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

### 5.4 Recommended build order

1. **Closed `record` types + `HasField` auto-derivation first.** Sufficient on its own
   for both partial linear consumption and partial drops (§4, §5.2). No row-kind, no
   row-unification algorithm — a closed record over *N* fields is a product type with
   a compiler-synthesized identity; the space of "which subset remains" is bounded by
   2^*N*, trivial for realistic struct sizes.
2. **`<row R>` open generics later, separately, only if a real duck-typing need
   materializes.** This is where the actual cost lives (§6) — treat it as its own
   decision with its own timeline, not a prerequisite for §4/§5.2.

---

## 6. Consequences and costs, if the fuller version is pursued

- **Row-kinded type variables and row unification** — a genuinely new piece of the
  elaborator/type-inference system (Rémy/Wand-lineage row unification: matching common
  labels, then recursively reconciling remainders), not a small patch, and only needed
  for step 2 of §5.4.
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
  `Linear`-bearing forces explicit handling. Not decided; this is the one piece of §6
  with no precedent to lean on at all.
- **Monomorphization vs. erasure.** The position report leans hard on
  storage-transparent constructs monomorphizing at compile time, erased at runtime
  (`lifetimes-vs-regions-2026-07-02.md` §8 item 7). PureScript's row polymorphism
  typically compiles via runtime dictionary-passing, not monomorphization. A zero-cost
  row-polymorphic feature for Metel would be its own implementation project, not
  something inherited for free by copying the reference languages' designs.
- **Implicit structural satisfaction is a real departure from how the rest of the
  aspect system works.** Every other aspect requires an explicit `impl Aspect for
  Type`. Go's implicit interfaces draw exactly this criticism: two unrelated structs
  that happen to both have an `id: i64` field satisfy `record { id: i64 }` whether or
  not that was intended, with nothing marking it deliberate. Given how consistently
  this cluster has favored explicit-and-checked over implicit-and-inferred elsewhere,
  this is worth a deliberate decision, not a default: either accept fully implicit
  satisfaction, or require a lightweight opt-in (e.g. `struct Point derives record {
  ... }`) before a struct is usable structurally.

---

## 7. Open questions — explicitly not decided

1. `Linear` as an auto-impl marker aspect (§3), reusing RFC-0080/0081's template —
   leading candidate, not ratified.
2. `Linear` ⊥ `Drop` mutual exclusion, and `drop<T: !Linear>` (§3) — leading candidate,
   not ratified.
3. Partial consumption: extend RFC-0071 §7's side-table, or adopt residual/record
   typing (§4.2) — not decided.
4. Ship closed `record` types only for now, or also `<row R>` open generics
   immediately (§5.4) — recommend closed-only first; not ratified.
5. Plain-record style vs. OCaml-object style (§6) — recommend plain records; not
   ratified.
6. Width-subtyping-requires-`Copy` rule (§6) — proposed with no existing precedent to
   verify it against; not ratified.
7. Implicit vs. explicit-opt-in structural satisfaction (§6) — genuinely open, no
   leaning stated; needs a deliberate decision either way.
8. Transitive field-usage checking when a `Drop` body calls helper methods (§5.2) —
   unresolved, no proposal yet.
9. Does residual/record typing, if adopted, replace RFC-0071 §7's mechanism for
   ordinary affine partial moves too, or stay linear/record-scoped only — unresolved.

---

## 8. Relationship to the tracked deferral and its deadline

This report changes nothing about the deferral already recorded in RFC-0063 §9 and
position report §11. Items 1 and 2 there (teardown discipline, `drop`'s interaction
with it) remain open with no urgency — the allocator layer is Phase 3 step 3, and
nothing implementation-side depends on them yet. Item 5 (partial consumption) keeps
its deadline: it concerns the same partial-move mechanism that move-semantics
(RFC-0071) and borrow-checker (RFC-0067) implementation — Phase 3 **steps 1–2** —
have to build regardless of whether `Linear` or `record` ship alongside them, so it
has to be settled before that work starts, not whenever the rest of this design
catches up at its own pace. This report is the working material toward that
resolution, not a substitute for making it.
