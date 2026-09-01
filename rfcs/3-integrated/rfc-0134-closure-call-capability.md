---
id: rfc-0134
title: "Closure Call Capability"
date: '2026-08-13'
status: integrated
target: v0.13.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/269'
coverage:
  "1": { spec: "spec.functions.closures.legality-20" }
  "2": { spec: "spec.functions.closures.legality-8" }
  "3": { spec: "spec.functions.closures.legality-9" }
  "3a": { kind: untestable, reason: "Base function-type spelling — deferred to RFC-0154; no rule of its own here." }
  "4": { kind: untestable, reason: "Internal type representation — Type::Fun gains three multiplicity fields — not user-observable syntax or behaviour. The field semantics are spec-anchored at legality-8/9 and dynamics-6..10." }
  "5": { spec: "spec.functions.closures.dynamics-10" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/927'
impl_status: not-started
---


> **Status — accepted 2026-08-30** (co-required with RFC-0152, accepted together);
> part of the v0.13.0 closure cluster (RFC-0134 / RFC-0152 / RFC-0050 / RFC-0153 /
> RFC-0157). Implementation shape: **ADR-0052**. Tracker metel-core#269.

> **Scoped deliberately narrow.** This proposes only the type-level distinction move
> checking needs for closures — not a revival of RFC-0046 (refused), not `linear`
> vocabulary, not `Drop`-for-closures. RFC-0050's capture-list syntax is a separate
> document; this RFC is the capability half.

**Model, as accepted.** A closure's *call multiplicity* — whether invoking it consumes a
capture — is a field on `Type::Fun` (§4), joined by `use_multiplicity` (§1, the `Copy`
rule) and, from RFC-0153, `call_mutation`. The multiplicity of a function type is **`many`
by default, `once` only when written** (§3): the CFG consumption analysis of §2 runs to
*verify* the declared/default value, not to source it — a `many`/unqualified closure whose
body moves a non-`Copy` capture out is a compile error at the definition site. `many`
satisfies a `once` slot by first-order directional matching, delivered by RFC-0152.

> **Status — integrated (2026-09-01).** Closure cluster spec-integrated: reference/spec/functions.md Closures section rewritten as Legality Rules 1-25 / Dynamic Semantics 1-15; this RFC's sections anchor at Legality 8/9/20 and Dynamics 10; coverage.spec frontmatter added; fixtures blocked on implementation (metel-core#925). Shape: ADR-0052.

## Summary

Give the type system a way to know whether *calling* a closure can consume one of its
own captures, so the move checker can reject a second call to a closure that already
consumed a non-`Copy` capture on its first call — the same way it already rejects a
second use of any other moved value. Proposes inferring this from the closure's body
(does some path through it move a non-`Copy` capture out) rather than requiring the
programmer to declare it, because a closure literal has no declaration site to hang an
annotation on — the precise justification is the move checker's own **receiver-kind**
handling, which already answers "does this call consume the thing being called on" and
already keeps that answer separate from `Copy` (§2's reconciliation note). An explicit
qualifier is added for the two cases inference cannot cover (§3). The resulting
call-count capability (`many`/`once`) is proposed as its own axis, independent of §1's
by-value-use axis and of any future mutation-capability axis — see §4 — rather than a
Rust-style single hierarchy.

*(An earlier version of this Summary justified the inference by analogy to "how
`Copy`/`Drop` are already structurally derived elsewhere in the language." That analogy
was false in both halves and is withdrawn: RFC-0071 (`3-integrated`) establishes `Copy`
is deliberately **declared**, not derived, and the affine-`once` decision below notes
`Drop` is an explicit opt-in aspect too. §2 had already replaced the analogy with the receiver-kind
argument; the Summary had not been updated to match.)*

---

## Motivation

`reports/memory-model/move-checking-status-and-closure-soundness-2026-07-29.md` records a
confirmed, reproduced soundness hole, accepted by the release interpreter with
`--move-check` on:

```metel
fun call(f: () -> String) -> String { f() }

fun main() {
    let s := "hello";
    let f := () -> String { s };

    let first := call(f);
    let second := call(f); // accepted, although `f` consumes captured `s`
}
```

Under affine semantics this closure is call-once: invoking it consumes its captured
`String`, so the second call should be rejected the same way a second use of any other
moved value is. It is accepted today for two compounding reasons:

1. **`Type::Fun` carries no distinction between a closure and a named function pointer at
   all** — same representation, same runtime shape (`RuntimeCallable` has only `Closure`
   and `Intrinsic`; a named function is built as a closure with a captured environment).
   The capability marker (§4) therefore has to be *created*, not read off an existing
   distinction — and, per §4, it doesn't need a new nominal type to carry it, only a
   field that already degenerates correctly for the zero-capture case.
2. **The move checker has never modeled what invoking a closure does to its captures.**
   A closure body is checked once, at creation, for internal soundness; nothing tracks
   that a *later call* is itself a use of the captured environment.

This is a real gap in a shipped, opt-in check (`--move-check`), not a hypothetical. It is
explicitly named in `metel-core#269`'s own tracking as a precondition for `metel-core#267`
(enabling move checking by default) — a checker that is silently unsound for closures is a
worse thing to make the default than one that stays opt-in with the gap documented.

### Why this needs a type-level answer, not a checker patch

A dataflow-only fix — tracking capture-copyability on the *binding*, without touching the
type — was already considered and rejected in the status report: it fixes the repro above
but stays wrong wherever the closure crosses a call boundary, lands in a struct field, or
is returned. The type has to carry the answer for the checker to be sound anywhere a
closure's *value* travels, not just at its immediate call site.

---

## Background: what exists and what doesn't

- **RFC-0006 (`4-implemented`)** is the current, shipped capture model: closures
  capture free variables **by value (clone) at creation**. Sharing mutable state across
  closures goes through an explicit pointer taken before closing over it — capture itself
  never aliases. This RFC does not change any of that; it is about what happens to a
  capture *after* it is inside the closure.
- **`is_copy` currently treats every `Type::Fun` as `Copy`**, unconditionally. That is
  correct for a named function pointer — it is word-sized and carries no captured state,
  and RFC-0061 §7.2 (`4-implemented`) specifies exactly this outcome, though as
  `std::core`-provided blanket impls that turn out not to exist (see that RFC's
  2026-08-14 correction, and the two-notions-of-`Copy` finding in Open Questions below;
  the *move checker's* answer is what this bullet is about) — and wrong for a closure
  that captured a non-`Copy` value — reusing
  such a closure (`call(f); call(f)`
  as two *separate* uses of the value `f`) is accepted today when it shouldn't be, a
  regression introduced incidentally while fixing an unrelated case
  (`metel-core#596`, "reusing a function value of a `Copy` function type remains valid",
  which correctly needed function pointers to stay `Copy` but widened the rule to every
  `Type::Fun`). Worth noting so this isn't mistaken for a broader pattern: `Type::Fun` is
  not the only structural type answering `Copy` unconditionally — `InferType::Array` does
  too — but that one is **correct and deliberate**, per RFC-0126 (`4-implemented`), which
  redefined `T[]` as a non-owning borrowed view that is `Copy` regardless of its element
  type. Only the `Type::Fun` case is a regression. (That both are hardcoded in the
  typechecker rather than expressed as stdlib impls is tracked separately as
  `metel-core#263`.)
- **Calling a closure has never been treated as a use of its captures**, independent of
  the `Copy`-derivation question above — this is the harder, longer-standing half, and
  the one the repro above actually exercises (`f(); f();` — the *same* binding, called
  directly, not passed around).

These are separable, and the status report already separates them; this RFC proposes
answers for both, since a type-level capability marker needs both to be sound.

---

## Prior art

**Rust's `Fn`/`FnMut`/`FnOnce` is inferred, never declared** — worth separating the
mechanism from the count. The compiler synthesizes an anonymous struct per closure
literal and derives which traits it implements purely from how the body uses each
capture: moves one by value → `FnOnce` only; needs `&mut` access without moving →
`FnMut`+`FnOnce`; only reads → all three. Nobody writes `impl FnOnce for ...`. This
validates §2's inference-from-body approach; it does not by itself validate adopting
three tiers — see below.

**`FnMut` specifically answers a question Metel's closures cannot currently ask.** A
Rust closure's captured environment *is* its own private, persistent storage —
`move || { counter += 1; counter }` mutates a field that survives between calls, because
nothing re-clones it. Metel's runtime does re-clone it: `call_runtime_callable`
(`metel-interpreter/src/evaluator/call.rs`) does `let mut call_env =
closure.captured.clone();` on every call, from the closure's original captured
snapshot, which is never written back to. A Metel closure cannot retain mutated state
across repeated calls to itself today — not as an oversight, but because RFC-0006
(`4-implemented`) deliberately routes every cross-call mutable-sharing need through an
*explicit* pointer taken before closing over it, stating its own rationale as "no
implicit aliasing — the programmer always sees a clone at the definition site." An
`FnMut`-shaped capability would mean a closure holding private mutable state nothing
else can see, which is a real reversal of that stance, not a small extension of it.

**OCaml's newer mode system (multicore/OxCaml) treats this as two orthogonal axes, not
one hierarchy** — a `once`/`many` axis for call count, and a separate `unique`/`shared`
(and `local`/`global`) axis for aliasing/mutation, rather than Rust's single
`Fn: FnMut: FnOnce` ladder that conflates the two. That is a better structural fit here:
Metel doesn't have a mutation-capability question to answer yet, but keeping call-count
as its own clean axis means a mutation axis can be added *alongside* it later — if the
runtime ever gains persistent per-closure state — without redefining what "call-once"
means. See §4.

**C++'s `mutable` lambdas** show the underlying feature (private state persisting across
calls) is a real pattern worth having eventually — accumulators, counters, stateful
callbacks — just not something C++ enforces move-once semantics on top of. Evidence the
capability is worth reserving room for, not evidence it belongs in this RFC now.

**Austral has no closures at all**, specifically because closures interacting with a
linear-type system were judged not worth the complexity. Not applicable to Metel —
closures already shipped — but the sharpest illustration that this corner is hard enough
that other designers have sometimes declined to open it.

**Swift and Kotlin aren't close comparisons.** Both capture by implicit
reference/boxing with GC backing them, no affine or move semantics, so there is no
consumption question to answer. Swift's `@escaping` and Kotlin's `inline`/`noinline`
are a lifetime/inlining axis, not this one.

---

## Proposal

### 1. `Copy` derives from captures, not blanket-`Copy` for every `Type::Fun`

A closure's own value is `Copy` if and only if every one of its captures is `Copy`. A
named function pointer has no captures, so it is trivially `Copy` — `metel-core#596`'s
case keeps working. This alone fixes `call(f); call(f)`: a closure capturing a non-`Copy`
value stops being freely reusable as a *value*, and ordinary move checking (already
sound for every other non-`Copy` type) takes over without any new mechanism.

**Capture `Copy`-ness of the capture forms.** A bare by-value capture is `Copy` iff the
captured type is. A `&`-reference capture is `Copy` (`&T` is `Copy`, per RFC-0067a,
mirroring Rust's `&`). A `&var`-reference capture is **not** `Copy` (`&var T` is not
`Copy`, mirroring `&mut`), so any `[&var x]` closure is non-`Copy` through this rule with
no special case. `[x.clone()]` (RFC-0050) captures an owned value, `Copy` iff that type
is. This means the mutation axis (RFC-0153) needs no separate "a `mutating` closure is not
`Copy`" rule — a closure that mutates outer state holds a `&var` capture and is non-`Copy`
here; a closure that mutates an owned non-`Copy` capture is non-`Copy` here; a closure
that mutates an owned `Copy` capture (`[n] mut { n += 1 }`, `n: i64`) *is* `Copy`, and
soundly so (each copy gets its own counter). RFC-0153 §3's earlier "not `Copy`" rule is
withdrawn accordingly.

**Why no existing mechanism can express this rule — checked, not assumed.** RFC-0061
(`4-implemented`) §2 allows `std::core` to write conditional blanket impls against
structural constructors, and §7.2 uses exactly that to grant bare function pointers
`Copy`. A natural question is whether closures could get this rule the same way — some
conditional impl reading "`Copy` when the captures are `Copy`." They cannot, for a
structural reason: a conditional impl's bounds key on the **target type's own type
parameters**, resolved positionally (`coherence.rs`'s `scoped_type_param_bounds` maps
each impl-scoped param to a position in the target — an array's element type, a function
type's parameters and return). A closure's captures appear in none of those positions.
`() -> String` says nothing whatsoever about a captured `String`. RFC-0096's auto-impl
algorithm fails for the same reason from the other direction — it recurses over a type's
own structure, and the captures are not part of that structure. So this section's rule
genuinely requires its own mechanism; that is a finding about what the existing
machinery can represent, not a preference for building something new.

**But that same fact leaves this section with a gap it does not currently close: where
the answer is stored.** If captures are not in the type, then `Copy`-ness of a closure is
not computable *from* the type — and the type is the only thing the checker gets.
Confirmed at both ends:

- `is_copy(&self, current_module: &[String], ty: &Type) -> bool` (`move_check/mod.rs`) —
  receives a `Type` and nothing else.
- §4 proposes `Type::Fun(Vec<Type>, Box<Type>, Multiplicity)` — parameters, return,
  call-multiplicity. No captures, no `Copy`-ness.

After this section lands, `is_copy` is therefore asked whether some `Type::Fun` is `Copy`
and still has no way to answer. It cannot fall back to `type_satisfies_aspect`: no
registry entry exists for a structural closure type, which is the whole point of the
paragraph above. It cannot derive the answer from `Multiplicity` either — §2 establishes
`Copy ⟹ many` but explicitly **not** the converse, since a closure that only *reads* a
non-`Copy` capture is `many` while being non-`Copy`, which is the entire reason §2 exists
rather than collapsing into §1. Two closures of identical type `() -> String`, one
capturing a `String` and one capturing nothing, must differ in `Copy`-ness with nothing
in the proposed type distinguishing them.

This cannot be pushed back into the move checker instead. This RFC's own Motivation
("Why this needs a type-level answer, not a checker patch") already rejects a
dataflow-only fix, because it stays wrong wherever a closure crosses a call boundary,
lands in a struct field, or is returned. That argument applies verbatim to `Copy`-ness;
this section simply had not noticed it applies to itself. **§4's type shape is corrected
accordingly** — see there.

### 2. Whether *calling* consumes is checked against the declared/default multiplicity

A closure's call multiplicity is **`many` by default, `once` when written**; the analysis
in this section runs to **verify** that value against the body, not to source it. A
`many`/unqualified closure whose body moves a non-`Copy` capture out is a compile error at
the definition site — *"consumes captured `s`; annotate `once (…) -> …` or don't move
it"* — exactly as a body returning the wrong type is an error against a declared return
type.

**An expected function type supplies the qualifier to an unqualified literal**, the same
way it supplies parameter and return types — from a `let` / parameter ascription, a
struct-field initializer, or a block's tail expression in a typed position. So
`fun make(s: String) -> once () -> String { [s] () -> String { s } }` type-checks: the
literal is checked as `once`, it does not default to `many` and then fail. When the
expected type does *not* fix the multiplicity — an unresolved type variable, or a bare
generic parameter `F` — the literal takes the default and RFC-0152 widening resolves any
gap at the concrete site. A conditional / `match` type is the greatest lower bound (least
permissive) of its arms under the widening order, each arm widening to it.

For a closure whose captures are non-`Copy` (via §1), the check asks whether invoking it
can move one out:

Concretely: walk the closure body along the same paths the move checker already walks
for internal soundness. If every path leaves every non-`Copy` capture un-consumed (only
read, or read through a reference, or not touched), the closure is **reusable** — callable
any number of times, exactly like today. If some reachable path consumes a non-`Copy`
capture (moves it out, passes it by value to something that takes ownership, etc.), the
closure is **call-once** — the *first* call is accepted and consumes the captures on the
checker's model; a second call is rejected as a use of an already-moved value, with a
diagnostic naming the capture (not just the closure), matching `T0019`'s existing shape
for every other moved-value case.

**Formal predicate, stated precisely.** The analysis runs *after* type checking, over
the *same* control-flow graph the move checker already builds for the closure body — not
a second traversal with its own rules. A non-`Copy` capture `c` is classified
**consumed** exactly when the existing move checker, run on that CFG, would register a
move out of the capture place `c` (equivalently, the field-projection modeling `c` on
the closure's own place — see the diagnostic-shape note below) on **some path from entry
that reaches the consuming statement**. "Reaches" is *syntactic-conservative*: a path
counts if it exists in the CFG, with no constant-folding of branch conditions and no
dead-code pruning beyond what the move checker already performs for ordinary bodies. A
capture consumed only on a path the move checker itself already proves unreachable is
therefore not classified consumed — but nothing weaker than that is assumed. If *any*
conservatively-reachable path consumes `c`, the closure is `once`; it is `many` only if
*every* such path leaves *every* non-`Copy` capture un-consumed. This is deliberately
the same conservative-reachability standard the move checker uses for `T0019` today, so
the two analyses cannot disagree about whether a given place is moved.

**Generic captures — definition-site, not per-monomorphisation** *(added 2026-09-01,
adversarial review)*. Whether a capture `c: T` (for a type parameter `T`) is `Copy` is
decided by the bounds in scope at the closure's definition, not re-decided at each
instantiation. So a capture of an unbounded `T` is non-`Copy`; a body that moves it out
makes the closure `once` **for every instantiation of that definition, including `T =
i64`** — the closure's type is fixed where it is written. A definition that wants the
`many` behaviour when `T` is copyable adds `T: Copy` (then moving `[x]` is a copy and the
body consumes nothing), or restructures to read rather than move. This matches how the
move checker already treats a generic `let y := x` — conservative on the bound, not
clairvoyant about instantiations.

**Operational rule at the call site.** Calling a `once` closure **consumes the callee
place at the call expression itself**, before the call's arguments and body are checked
or evaluated. That is the primary state transition: after `f()` where
`f: once (…) -> …`, the binding `f` is moved, and any later use of `f` — including a
*recursive or re-entrant* call reached from within the first call's own dynamic extent —
is rejected as use of a moved value by the ordinary moved-value rule. The per-capture
projection ("field or element `c` was moved at …") is *diagnostic refinement* layered on
top: it tells the reader which capture forced the closure to be `once`, but the closure
value becoming unusable does not depend on the checker first attributing the move to a
specific capture. A `many` call consumes nothing and routes through `observe_expr`,
exactly as a `&self` method call does.

No new syntax is needed for this — nothing here requires RFC-0050's `move` specifier (or
any capture-list syntax at all) to exist first. That is what makes this independent of
RFC-0050's own stated dependency.

**Reconciliation with `Copy` — real relationship, but not the one to unify with.** There
is a genuine logical connection: since `Copy` (§1) already means every capture is
`Copy`, a `Copy` closure has nothing non-`Copy` for its body to consume, so it is
necessarily `many` — **`Copy` implies `many`**. The converse doesn't hold: a closure
with a non-`Copy` capture it only *reads* is `many` without being `Copy`, which is the
entire reason this section exists rather than reusing §1 alone (treating every
non-`Copy` closure as call-once, with no consumption analysis, would wrongly forbid
calling such a closure a second time). So `once`/`many` isn't a second way to say what
`Copy` already says — collapsing it into `Copy` would lose exactly the case this section
was built for.

The concept `once`/`many` actually reconciles with isn't `Copy` at all — it's
**receiver-kind**, which the move checker already has for ordinary methods and already
keeps separate from `Copy` for the identical reason. Checked directly
(`move_check/mod.rs`):

```rust
match receiver_kind {
    Some(ReceiverKind::Value) => {
        // ...
        self.consume_expr_with_cause(receiver, ..., MoveCause::ByValueReceiver);
    }
    Some(ReceiverKind::Ref | ReceiverKind::RefMut) | None => {
        self.observe_expr(receiver, current_module, state);
    }
}
```

A by-value `self` method call consumes its receiver; a `&self`/`&var self` method call
only observes it — callable any number of times regardless of `Copy` (`Copy` only gates
whether a *consuming* path ever registers as a real move; a `Ref`-kind path never
consumes regardless of `Copy` either way, exactly mirroring the `Copy ⟹ many` relationship
above). `once` is what happens when a closure's implicit "call" behaves like a by-value
`self` method; `many` is what happens when it behaves like `&self`. The only real
difference is mechanism, not concept: a method **declares** its receiver kind
(`self`/`&self`/`&var self`, written by the programmer); a closure has no method
declaration to write one on, so this section **infers** the equivalent from the body —
which is the actual, precise justification for inference here, sharper than the
`Copy`/`Drop`-derivation analogy this section leaned on in an earlier draft.

This points at a concrete implementation simplification worth flagging, not just a
conceptual one: rather than building consumption-analysis for closure calls as a wholly
separate move-checker mechanism, it can route through the *same* consume-vs-observe
dispatch already shown above — a `once` call consuming via `MoveCause::ByValueReceiver`
(or a closely-related cause), a `many` call going through `observe_expr` — reusing
existing machinery instead of adding parallel new machinery next to it. Consistent with
the diagnostic-shape reuse of `PartialMoveUsedAsWhole` below, which leans on the same
`ByValueReceiver`-adjacent infrastructure for a related reason.

**Diagnostic shape, resolved rather than left open:** this doesn't need a new
`MoveViolationKind` or a new message format. A second call to a `once` closure is
structurally the same situation as `MoveViolationKind::PartialMoveUsedAsWhole` already
covers — a value used as a whole after one of its parts was moved out — and that
existing message (`move_check/mod.rs`) already names *both* the closure binding and the
specific moved place: `"use of partially moved value `{binding}`: field or element
`{place}` was {moved-at clause}"`. A closure's capture is representable as an ordinary
`Projection::Field(name)` on the closure's own place — the same projection kind already
used for struct fields — so a consumed capture `s` inside closure `f` reads as "use of
partially moved value `f`: field or element `s` was moved at ...", naming the capture
for the reader (more actionable, as the status report's repro already suggested) while
still identifying which binding is unusable. No new diagnostic design needed, only
modeling a capture as a field-projection of the closure's own place — plumbing this
section already needs for the consumption analysis itself to track *which* capture
moved.

**Scope boundary, worth stating rather than leaving implicit: this needs a constructed
body to walk.** That's available whenever a closure is called directly, or nested inside
a generic function's own construction (§3 covers the latter). It is *not* available for
a generic *named function* referenced as a first-class value rather than called — the
runtime represents that case as `ClosureBody::Untyped`
(`metel-interpreter/src/evaluator/mod.rs`: `FunBody::Generic(b) => ClosureBody::Untyped(b.clone())`),
deferring the entire body to actual call time with nothing constructed for the
move-checker to walk in the meantime. This is not a gap this RFC introduces: it is the
same shape as `metel-core#736` ("generic functions cannot be referenced as values at
all"), already filed and characterized this cycle. Since the underlying capability is
already broken independent of this RFC, there is no body to analyze for this case until
#736 lands — this RFC's guarantee does not yet extend to a generic function used this
way, and shouldn't be assumed to until that dependency is resolved.

### 3. A parameter's required multiplicity: `many` by default, `once` when written


A function-typed **parameter / return / field** is **`many`-required by default**; `once`
only when the qualifier is written. This is not inferred from any enclosing body — the
default covers the common case, and the difficulty of inferring a required multiplicity
from a possibly-generic body (which an earlier draft developed at length) does not arise.

**Why an explicit `once` / `many` is a promise, not a re-derivation.** A pure-inference
requirement is invisible in the signature: `fun call(f: () -> String)` reads the same
whether its body calls `f` zero, one, or — after a later edit — two times. Rust's `F:
FnOnce` vs. `F: Fn` is a *written*, semver-relevant part of a generic function's contract:
an author writes `F: Fn` even when today's body calls `f` once, to promise callers that
reusability keeps working. The `many` default gives that for free (a `many`-required
parameter never silently strengthens), and writing `once` is the deliberate choice to
accept call-once callbacks. Drift can only make a rule *stricter* — a visible compile
error — never silently weaker.

**Checking: first-order directional matching (RFC-0152).** A function value of call
multiplicity `m` satisfies a required multiplicity `r` when `m` is at least as permissive
as `r` — `many` satisfies both `once` and `many`; `once` satisfies only `once`. This is
what makes `f: once (T) -> U` a *usable* upper bound: it accepts a bare function, a
reusable closure, or a genuinely call-once one, because all satisfy "called at most once."
The relation is a subtyping one, not something a symmetric unifier expresses, so its
first-order form (a function-typed argument passed to a function-typed parameter, and a
function-typed return) is specified in **RFC-0152**, and RFC-0134 depends on it — the two
are accepted together. The *higher-order* (contravariant) positions and the question of a
full `Type::Fun` subtype lattice are **RFC-0155**'s; below the first level of nesting an
exact match is required, a sound under-approximation.

**Stdlib `once`-annotation sweep — a delivery item.** Under the `many` default, every
unqualified closure-typed stdlib parameter is `many`-required. That is correct for
loop-calling combinators (`List::map` / `filter` / `fold` / `find`, `for_each`) but
over-constrains ones that call the callback at most once (`Perhaps::map` / `Result::map` /
`Perhaps::and_then` / `unwrap_or_else` / `filter` / `map_or` and siblings) — those get
`f: once (T) -> U` as part of landing this RFC. Mechanical (grep `core.mtl` for
closure-typed parameters, classify by call shape); tracked on #269 / ADR-0052.

### 3a. Base function-type spelling — see RFC-0154

The `once` / `many` qualifier goes wherever the base function-type spelling is. That
spelling is itself under revision — the current `(T) -> U` (RFC-0041) collides with
grouping, tuples, and RFC-0151's records — but that is a corpus-wide grammar question,
not this RFC's to settle. It is **RFC-0154 (Pipe Notation for Closures and Function
Types)**, which proposes `|T| -> U` for the type and `|x| body` for the literal.

This RFC's qualifier composes as a prefix on whatever RFC-0154 settles: `once |T| -> U`
today would read `once fun(T) -> U` under the alternative RFC-0154 rejects, and
`once (T) -> U` if the spelling does not change. **Examples throughout this document use
the current `(T) -> U`** — they are the shipped syntax, not a proposal.

### 4. Where the marker lives in the type system: one multiplicity per operation, one type

The capability information for a closure decomposes into structurally independent axes —
one multiplicity per *operation*, deliberately modeled on OCaml's mode system rather than
Rust's single three-value hierarchy — and all of them live on `Type::Fun` itself, not on
a nominally separate closure type:

- **The call-count axis — this RFC's headline proposal.** `many` (reusable) or `once`
  (call-once, §2's consumption-analysis case), asked about the *call* operation. This is
  not a name invented for this RFC: OCaml's mode system already calls this exact axis
  **`linearity`** (`many`/`once`), kept independent of its separate uniqueness/locality
  axes. Whether this axis's `once` value can later be *strengthened* toward OCaml's
  fuller, forced-consumption reading without becoming a different axis is addressed in
  the affine-`once` decision below.
- **The by-value-use axis — §1's `Copy` rule, and a second axis rather than part of the
  first.** Whether the closure *value itself* may be used by value more than once, which
  is what `Copy` already means. §2 establishes `Copy ⟹ many` but not the converse, so
  this genuinely cannot be folded into the call axis: a closure that only reads a
  non-`Copy` capture is `many` on the call axis while being `once` on this one. An
  earlier draft of this section listed only the call axis here and treated §1's rule as
  feeding into it; that was wrong, and §1 now records why (the storage gap).
- **A mutation-capability axis — `reading` / `mutating`.** OCaml's counterpart is its
  separate `uniqueness` (aliasing) axis. **Designed as RFC-0153 (Closure Mutation Axis),
  co-landing with this RFC in v0.13.0.** The `call_mutation` field ships in `Type::Fun`
  together with §4's two, so the type carries all three multiplicity axes from the start.
  RFC-0153 also takes the runtime consequence: a `mutating` closure's by-value captures
  are written back across calls (reversing the per-call re-clone-and-discard quoted in
  Prior Art), which is what finally lets a Metel closure hold private mutable state —
  Rust's `move ||` + `FnMut`. Kept a separate binary field, never a third value stacked
  onto the call-count axis the way Rust's `FnMut` sits between `Fn` and `FnOnce`.

**No distinct closure type is needed to carry any of these axes.** An earlier draft of this
section left that as an open choice, inherited from RFC-0049's "step 1" (distinguish
plain function pointers from closures as separate types) without checking whether the
reason RFC-0049 wanted that still applies here. It doesn't: RFC-0049 needed the split
because its `linear fun` design required `Drop`-for-closures and region/allocator
machinery that only makes sense for a value with captures — a function pointer
genuinely has nothing to `Drop`. §5 rules that machinery out entirely for this RFC, and
once it's out, so is the reason for a nominal split:

- **Both axes are already capture-derived, not type-kind-derived.** §1's `Copy` rule
  (`Copy` iff every capture is `Copy`) already treats a function pointer as the
  degenerate zero-captures case, not a different kind of thing — it never needs to know
  "this is nominally a function pointer" ahead of time, only that its capture list is
  empty. §2's multiplicity inference degenerates the same way: "does some path consume
  a non-`Copy` capture" is vacuously false with zero captures, so a function pointer
  lands on `many` by falling out of the general rule, not by a type-level carve-out.
- **The runtime doesn't distinguish them either** (Background, above) —
  `RuntimeCallable` has only `Closure` and `Intrinsic`; a named function is already
  *built as* a closure with an empty captured environment. A nominal type split would
  invent a distinction that doesn't exist at the value level, not reflect one that does.
- **A single type needs no coercion rule.** Two separate types would need something to
  define how `let f: () -> String = some_named_fn;` type-checks — a
  function-pointer-to-closure coercion, exactly the kind of new machinery this RFC's own
  "no new syntax, no new machinery" scope (header note, §5) is trying to avoid. A single
  `Type::Fun` carrying multiplicity fields (shape below) needs none of that: no coercion
  between two kinds of function type is required, because there is only one type.
- **One consequence worth stating outright:** a named function value used anywhere a
  closure is expected is `many` on both axes for free — not a special case checked
  against the type, the same zero-captures fact computed once and reused. (A prior draft
  of this RFC carried this as its own separate Open Question, pending §4 being settled;
  it wasn't a second question, it was this one asked twice.) Such a value satisfies a
  parameter declared `once (T) -> U` — `many` is usable wherever `once` is wanted, per
  §3's first-order directional matching (RFC-0152). An earlier draft of this RFC, when
  it still proposed exact-match unification, listed the opposite as an ergonomic cost;
  that cost is what adopting RFC-0152's first-order rule removes.

**This directly conflicts with RFC-0061 §7.4's description, worth flagging rather than
silently overriding.** RFC-0061 (`4-implemented`) states closures "have distinct
anonymous types... generated per-closure-site," explicitly distinguishing them from
`fun(A) -> B`. Checked directly against the type-checker's own representation
(`metel-frontend/src/types/mod.rs`) rather than assumed: `Type` has exactly one
function-type variant, `Fun(Vec<Type>, Box<Type>)` — no separate closure case, no
per-closure-site tag anywhere in the enum, matching this section's claim and not
RFC-0061's. RFC-0061 §7.4 predates this investigation by several weeks and defers the
closure case entirely to RFC-0050 without citing code for the "distinct type" claim; the
more likely explanation is that it stated an assumption inherited from RFC-0050/RFC-0049's
framing that the implementation never actually followed, rather than describing a real
mechanism this RFC's own code-check missed. Two accepted-track documents shouldn't
describe the same type contradictorily — RFC-0061 §7.4 needs a dated correction note
(the same pattern it already uses for its own #549/#581/#239 status updates) once this
RFC's outcome is known, since "no distinct closure type" is this section's load-bearing
claim.

So: **fields on `Type::Fun`, no distinct closure type.** This RFC's own count is two, not
one — §1's storage gap (see there) establishes that `Copy`-ness of a closure is equally
uncomputable from the type unless the type carries it. With RFC-0153 co-landing in
v0.13.0 (see the top amendment) the shipped shape is three:

```
Type::Fun(Vec<Type>, Box<Type>, call_multiplicity, use_multiplicity, call_mutation)
```

- `call_multiplicity` — §2/§3's axis. Does *invoking* this closure consume a capture?
- `use_multiplicity` — §1's axis. Is the closure *value itself* `Copy`? Equivalently:
  is the by-value-use operation on it `once` or `many`?
- `call_mutation` — RFC-0153's axis. Does *invoking* mutate a capture (needing `&var`
  access for the call)? `reading` unless written `mut`.

These are the same axis asked about two different operations, which is precisely
RFC-0135's reframing (`Copy` is `many` answered for by-value use). Both are computed the
same way — inspect the closure at its creation site, where captures and body are both
available, and store the result in the type — which is itself evidence they are siblings
rather than one real field plus an ad-hoc `Copy` bit bolted alongside it. §4's reserved
mutation axis becomes a third field of the same kind, on the same rationale, whenever
something needs it.

**Only one of the two is writable, and that asymmetry is deliberate.** §3's `once`/`many`
qualifier always denotes `call_multiplicity`. `use_multiplicity` has **no surface syntax
and should not be given any**:

- It is always inferable, from captures, with no case where a programmer would need to
  override it — unlike §3's call axis, whose entire motivation is a declared signature
  needing to promise more than the current body happens to require.
- RFC-0071's reason for `Copy` being *declared* rather than derived for named types is
  that a type's author may want resource semantics even when every field is `Copy`. A
  closure literal has no declaration site and no author to express that intent, so
  inference is the only available source. Closures are consistent with RFC-0071 here
  rather than an exception to it: they are not getting a structural `Copy`-derivation
  grafted onto the aspect system RFC-0071 deliberately kept declaration-only — they are
  the one kind of type whose multiplicities are per-expression and therefore live in the
  type instead of the impl registry.
- Reusing `once`/`many` in the same prefix slot for a second axis would make
  `once (T) -> U` ambiguous about which operation it qualifies, and inventing a second
  keyword pair to disambiguate would add surface area for a fact nobody needs to write.

Note this keeps the *shape* of the current implementation rather than restructuring it:
`is_copy` already special-cases `Type::Fun` ahead of the aspect lookup
(`matches!(peel_type_references(ty), Type::Fun(_, _)) || …`). The fix makes that branch
read `use_multiplicity` instead of returning `true` unconditionally. The existing
hardcode is wrongly *valued*, not wrongly *placed*.

RFC-0049 stays cited in References as the origin of the "distinguish function pointers
from closures" framing this RFC considered and did not adopt, and as prior art for the
parts of its own scope (unconsumed-closure `Drop`, linear subtyping) that remain
genuinely out of scope here.

### 5. What this deliberately does not include

- **No `linear` vocabulary, no `Drop`-for-closures, and deliberately not waiting on "the
  rest of the linear-types tower."** RFC-0050's own Timing Recommendation ties `move`
  captures to linear types having "a settled design" — reasonable for `move` capture
  *syntax specifically*, since a `linear fun(...) -> T` closure type is exactly what
  RFC-0046 tried to specify. But the confirmed hole this RFC exists to close
  (`f(); f();`) is not a linearity question at all: `String` is an ordinary affine value
  everywhere else in the language, movable and droppable, with no exactly-once
  obligation. The soundness gap is that a closure *calling itself* isn't currently
  recognized as a use of its own captures — the same gap would exist even in a language
  with no linear types whatsoever. Treating it as affine (may be silently dropped
  unconsumed, exactly like any other non-`Copy` value at scope exit) rather than linear
  (must be consumed or explicitly discarded) is what lets this RFC proceed without
  waiting for RFC-0028's linear-types tower to settle — it is a narrower, different
  claim than what RFC-0046/0049/0050's `move` half were reaching for, not a shortcut
  through the same claim.
- **No capture-list syntax.** RFC-0050 owns that, independently timed, per its own text.
- **No `FnMut`-shaped capability *in this section*.** §4's mutation axis carries it —
  **RFC-0153 (Closure Mutation Axis)**, co-landing with this RFC in v0.13.0. RFC-0153
  also takes the runtime change it needs: a `mutating` closure's by-value captures are
  written back across calls, so a Metel closure can hold private mutable state (a
  returnable counter / accumulator), which is not possible today (the per-call re-clone
  quoted in Prior Art discards it). Its `call_mutation` field ships in `Type::Fun`
  alongside this RFC's two.
- **No unification of `Copy` with `once`/`many` for ordinary (non-closure) types.** The
  two turn out to be the same underlying question, not just an analogy: `Copy` is what
  `many` means when the operation being asked about is "by-value use" instead of
  "call" — `Copy` ⟺ that operation is `many`; ordinary affine/non-`Copy` ⟺ `once`. That
  framing correctly predicts a fact already true today with no stated relation to `Copy`
  anywhere: `&self` methods are repeatable on non-`Copy` receivers, because that's
  `many`/`once` answered for a *different* operation (borrow-call) than the one `Copy`
  answers (by-value use) — the same relationship §2's reconciliation note draws between
  closure `many` and receiver-kind. A real, coherent generalization, not a coincidence —
  but it reaches every type in the language, not just closures, and the two cases don't
  share a *mechanism* even if they'd share a *name*: closure multiplicity has to live
  per-expression (the field §4 proposes on `Type::Fun` — two closures sharing a
  structural type can have different multiplicities), while `Copy` is and would stay a
  per-*declaration*, nominal fact (every `Pair` value has the same `Copy`-ness, looked up
  by name) — so this would be a rename of what `Copy` means, not a reuse of the
  `once`/`many` qualifier syntax §3 proposes for function types. Worth its own RFC if
  pursued; out of scope here. **RFC-0135 (Multiplicity for Ordinary Types) is that RFC**,
  opened once this idea was worth writing down rather than only naming. **Note the
  relationship has since tightened for §1 specifically:** §4's `use_multiplicity` field
  *is* RFC-0135's "`Copy` is `many` for the by-value-use operation," applied to closures.
  §1 needs somewhere to put its answer regardless of whether RFC-0135 is accepted, so
  this is not a hard dependency — but the two documents now describe the same
  representation, and if RFC-0135 is refused, §1's second field stays and simply keeps
  the name `Copy` rather than gaining the unified vocabulary.

  **Update (2026-08-31):** **RFC-0157 (Closure Capture Default (Move), `2-accepted`; regular-value analysis split to RFC-0162)**
  recommends exactly that outcome — `Copy` keeps its name on ordinary types, no
  `Copy → many` rename; `once`/`many` stays internal vocabulary plus §3's function-type
  qualifier. Under that recommendation `use_multiplicity` is read as an internal
  `Type::Fun` field carrying the move checker's `Copy` answer for closures, not as
  adopting RFC-0135's ordinary-type reframing. Nothing in this RFC changes either way —
  the field is forced by §1's storage gap regardless of what ordinary-type `Copy` ends up
  called. RFC-0157 also proposes (its "D5") changing RFC-0006's capture *default* from
  clone to move/copy-per-value-rule; that is orthogonal to §2 — the call-consumption
  question is identical however a capture arrived inside the closure.

---

## Open Questions

**None blocking.** Every question this RFC opened with has been answered from existing
code or settled as a decision — where the marker lives, the diagnostic shape for a second
call, builtin higher-order callbacks (§2, §3, §4), how multiplicity mismatches are
rejected (§3's first-order directional matching, with RFC-0152), and whether §4's
`use_multiplicity` field disturbs the two implications keyed on the name `Copy` (resolved
immediately below). One item is recorded as a **decision with a stated reopening
condition**, not as an open
question, per PROCESS.md's rule that a question blocked on nothing that exists can block
acceptance indefinitely while having nothing anyone could schedule.

### Resolved: `use_multiplicity` disturbs neither `Copy` implication — because neither ever applied to function types

Two shipped mechanisms are keyed on the literal aspect name `Copy`, and moving closure
`Copy`-ness into a type field (§4) raised the question of whether either silently breaks:
RFC-0072 §2.3's `Copy` ⟹ `!Drop` rule, and RFC-0080's `Copy` ⟹ `Clone` blanket. Both are
unaffected, but the reason is not the reassuring one — the premise behind the question
was wrong.

**Function types satisfy no aspects at all.** `infer_type_satisfies_aspect`
(`typeinference/mod.rs`) answers every aspect query for a function type with `false`, by a
single arm whose own comment says so: `InferType::Var(_) | InferType::Never |
InferType::Fun(_, _) => false` — *"`Never` and `Fun` implement nothing."* Confirmed
empirically against the release binary, for a named function and a closure alike:

```
[T0012] `(i64) -> i64` does not implement `Copy` (required by `needs_copy`)
[T0012] `(i64) -> i64` does not implement `Clone` (required by `needs_clone`)
[T0012] `() -> String` does not implement `Copy` (required by `needs_copy`)
```

From that, both implications resolve mechanically:

- **`Copy` ⟹ `!Drop` is unreachable for function types, not broken by this RFC.** The rule
  (`typechecker/construction.rs`) only consults `Copy` as an *escape hatch*, inside a
  branch that fires when the type already satisfies the negated aspect: `if
  registry.type_satisfies_aspect(…, aspect)` then `if aspect == "Drop" &&
  type_satisfies_aspect(…, "Copy") { continue; }`. A function type never satisfies `Drop`,
  so the outer branch never fires and the `Copy` check is never reached. `T: !Drop` is
  satisfied by a closure today for an entirely independent reason — verified: a closure
  passed to `fun needs_no_drop<T: !Drop>(x: T)` is accepted. §5 rules out
  `Drop`-for-closures, so this stays unreachable.
- **`Copy` ⟹ `Clone` never fires for function types either.** The blanket is keyed on
  aspect-`Copy`, which a function type does not have, so it grants nothing to close
  either way — verified above.

**The real finding, which this RFC must state rather than inherit silently: there are
already two disjoint notions of `Copy` in the shipped compiler.**

| | `move_check::is_copy` | `registry.type_satisfies_aspect(…, "Copy")` |
|---|---|---|
| Used for | move checking | bound satisfaction (`T: Copy`) |
| `Type::Fun` | `true` (hardcoded special case) | `false` (implements nothing) |

Both answers are live simultaneously. One program shows the split directly: the same
closure is rejected by `needs_copy(c)` with `T0012` *("`() -> String` does not implement
`Copy`")* while `call(f); call(f)` — this RFC's own motivating repro — is accepted,
because move checking took the other path.

**§1 and §4 are about the move-checking notion only.** `use_multiplicity` replaces the
hardcoded `true` in `is_copy` with a computed answer. It does **not** enter the aspect
registry, does not make closures satisfy `T: Copy` bounds, and is not intended to. A
closure remains outside the aspect system after this RFC, exactly as it is before it.

**That divergence is a real pre-existing gap this RFC deliberately does not close, and it
now has an owner.** It is not introduced here — bare function pointers have it today — and
closing it means deciding how structural types enter the aspect registry, which is
RFC-0061/RFC-0096 territory and substantially larger than this RFC's scope. It is filed as
**`metel-core#739`**, which records the mechanism (`InferType::Fun => false`), the
verified `T0012` results, the two-notions table above, and the fact that RFC-0061 §7.2's
`Copy`/`Clone`/`Send`/`Sync` blanket impls and §7.1's `Callable<A, B>` auto-impl are
specification that was never built (RFC-0061 now carries a dated correction note saying
so). Related existing work: `metel-core#702` is the architectural root cause (model
structural types as regular types), and `metel-core#263` tracks the same class of debt for
tuples and fixed arrays.

Nothing in this RFC depends on #739 landing first: §1's rule is about the move-checking
notion, which works today and continues to. But if #739 is resolved by making function
types satisfy `Copy` through the aspect registry, `is_copy`'s `Type::Fun` special case
becomes deletable and `use_multiplicity` becomes the single source of truth for both
notions — the outcome this RFC would prefer, without requiring it.

### Decision: affine `once`, not linear — and what would reopen it

This RFC's `once` is **affine**: a call-once closure that is never called is silently
dropped at scope exit, exactly like any other unused non-`Copy` value. It carries no
exactly-once obligation. This is adopted as a decision rather than left open, on three
grounds:

- **The axis supports strengthening later without redesign.** §4 names the call-count
  axis after OCaml's own `linearity` mode (`many`/`once`), whose `once` is already closer
  to forced-consumption than this RFC's. If a real case later needs the stronger
  guarantee, it arrives as a strengthening of *this* axis's `once` value — an enforcement
  flag, or splitting `once` into `once-affine`/`once-linear` — not as a third axis and
  not as an abandonment of the design.
- **Nothing else in the language currently guarantees cleanup either, so affine `once`
  gives up nothing that exists.** An earlier version of this bullet claimed the
  resource-leak worry was "already covered" by `Drop` — that a closure capturing a `Drop`
  value runs the capture's cleanup when the closure drops. **That was false on two
  independent counts, both now verified.** First, a closure is never `Drop`: function
  types satisfy no aspects at all (`InferType::Fun(_, _) => false`, `typeinference/mod.rs`
  — "`Never` and `Fun` implement nothing"), so the propagation the earlier bullet assumed
  cannot happen. Second, and more decisively, **destructors do not run for any type yet**:
  `metel-core#292` is unimplemented, and the compiler actively rejects a non-empty `drop`
  body with `T0001` — *"a `drop` body cannot run yet: destructor invocation is not
  implemented (metel-core#292), so this cleanup would silently never happen. Leave the
  body empty to declare the type `Drop` for its type-level effects."* `Drop` today is
  purely type-level: `Copy` exclusion, `!Drop` bounds, and the partial-move ban. So
  affine `once` does not forgo a working guarantee — it declines to add an
  exactly-once obligation to a language where cleanup is not yet enforced for anything.
- **What is genuinely uncovered is narrow and speculative.** Whether the language should
  statically flag "this closure's intended effect was never triggered" as a bug in its
  own right. Nobody has hit this in Metel code, because the affine `once` this RFC
  specifies does not exist yet to be exercised.

**Reopening condition, stated so this is testable rather than permanent:** real Metel
code that exercises affine `once` and produces a bug that forced consumption would have
caught. Note this condition is now *stronger* than when it was first written, since the
`Drop`-already-catches-it escape clause it originally carried turned out not to exist:
once `metel-core#292` lands and destructors actually run, this decision is worth
re-examining, because the trade-off it was made against will have changed.

---

## References

- **RFC-0006 (Closure Capture Semantics), `4-implemented`** — the base capture model
  this RFC builds on unchanged; value-capture at creation, sharing via explicit pointers.
- **RFC-0046 (Linear Closure Capture), `6-refused`** — precedent and terminology this RFC
  deliberately does not inherit (linear-specific, pre-split-model). RFC-0050 names this
  RFC as (part of) its intended successor.
- **RFC-0049 (`linear fun` Type System), `0-draft`** — built directly on RFC-0046; its
  "step 1" (distinguish plain function pointers from closures as separate types) is the
  origin of a framing §4 considered and did not adopt, once the `Drop`-for-closures
  machinery that motivated it turned out to be exactly what this RFC rules out (§5).
  RFC-0049 is otherwise about questions (unconsumed-closure `Drop`, linear subtyping)
  this RFC treats as out of scope under an affine rather than linear discipline. May
  need its own re-scoping once this RFC's outcome is known — not resolved here.
- **RFC-0050 (Closure Capture Lists), `2-accepted`** — actively maintained against the
  current model. It formerly carried a `move` capture specifier that "needs a split-model
  successor to RFC-0046"; this RFC was written to be that successor for the capability
  question. RFC-0050 has since **dropped the `move` specifier** (2026-08-31) and deferred
  ownership-transfer capture to RFC-0157, so RFC-0134 no longer has RFC-0050 as a
  downstream consumer — but this RFC's own motivation (the `f(); f()` soundness repro)
  never depended on RFC-0050. RFC-0050's `&var`/`&`/clone capture-list syntax is untouched
  and independently timed.
- **RFC-0061 (Structural Aspect Bounds), `4-implemented`** — specifies `Copy`/`Clone`/
  `Send`/`Sync`/`Callable` for bare function pointers (§7) as `std::core`-provided
  blanket impls — a specification this RFC's own investigation found is **not
  implemented** (function types satisfy no aspects at all), now recorded as a dated
  correction in RFC-0061 and analysed in this RFC's Open Questions section. Its §2
  conditional-blanket-impl mechanism is the one
  §1 checks against and finds structurally unable to express a capture-dependent rule.
  Its §7.4 claim that closures have "distinct
  anonymous types" was checked against actual code while drafting §4 below, found not to
  match the current `Type` representation, and now carries its own dated correction
  block in RFC-0061 itself (2026-08-14) rather than staying an unresolved conflict
  between the two documents.
- **RFC-0096 (Auto-Impl Aspects), `0-draft`** — the closed `{Send, Sync, Linear}`
  auto-impl set. Its structural-recursion algorithm is the second mechanism §1 checks
  and rules out: it recurses over a type's own structure, and a closure's captures are
  not part of that structure.
- **RFC-0071 (Ownership and Move Semantics), `3-integrated`** — establishes that `Copy`
  is deliberately declared rather than derived, and that consequently no anonymous record
  can ever be `Copy`. §4's argument for `use_multiplicity` being inference-only is
  checked against this: closures have no declaration site for an author to express
  resource intent through, so inference is the only available source, making them
  consistent with RFC-0071's rationale rather than an exception to it.
- **RFC-0135 (Multiplicity for Ordinary Types), `1-under-review`** — §5's deferred idea;
  §4's `use_multiplicity` describes the same representation (`Copy` as `many` for
  by-value use, applied to closures). Not a hard dependency — see §5. **RFC-0157
  recommends RFC-0135's `Copy → many` rename not proceed**; that does not affect this
  RFC (see §5's 2026-08-31 update).
- **RFC-0157 (Closure Capture Default (Move)), `2-accepted`** — the trade-off study
  for the regular-value `Copy`/`Clone` model. Recommends no divergence there (keep `Copy`
  as Rust has it, no rename) and spending divergence budget on closures — of which this
  RFC is the main existing example. Its "D5" would change RFC-0006's capture default
  (clone → move/copy). Neither affects anything here; see §5's 2026-08-31 update.
- **RFC-0158 (Share and Clone: Separating Aliasing from Duplication), `1-under-review`** —
  splits an aliasing `Share` aspect out of `Clone` for `Rc`/`Arc`. Orthogonal to closure
  multiplicity; listed because it, RFC-0135, and §4/§5 all touch the `Copy`/`Clone`/
  multiplicity area.
- **RFC-0154 (Pipe Notation for Closures and Function Types), `1-under-review`** — owns
  the base function-type spelling. §3a was split into it 2026-08-30; this RFC's
  `once`/`many` qualifier prefixes whatever RFC-0154 settles (`|T| -> U` as proposed).
- **RFC-0152 (Function-Type Multiplicity Widening), `2-accepted`** — the directional
  "`many` satisfies `once`" rule §3 needs to be coherent. Accepted 2026-08-30 as a
  co-requirement of this RFC.
- **RFC-0155 (Higher-Order Function-Type Multiplicity Variance), `1-under-review`** — the
  contravariant-nesting and subtype-lattice questions split out of RFC-0152 the same
  day; not needed by this RFC.
- **RFC-0153 (Closure Mutation Axis), `2-accepted` (v0.13.0, #902)** — §4's third
  `Type::Fun` field (`call_mutation`) and the `mut` qualifier that composes with
  `once`/`many`. Widened 2026-08-31 to also change RFC-0006's runtime so a `mutating`
  closure's by-value captures persist across calls (the `FnMut` / private-state case).
  **Co-lands with this RFC in v0.13.0** — the shipped `Type::Fun` carries all three
  multiplicity fields at once.
- **RFC-0151 (Tuples as Numeric-Label Rows), `0-draft`** — the reason the current
  `(T) -> U` function-type spelling is genuinely ambiguous, not just fragile (once
  `(A, B)` is a record type). Motivates RFC-0154.
- `metel-core#269` — "Model closure move capability separately from function pointers,"
  the issue this RFC exists to unblock; its own tracking states the blocker is a design
  decision, not implementation time.
- `metel-core#267` — enabling move checking by default; `#269`'s own text names itself as
  a stated precondition.
- `reports/memory-model/move-checking-status-and-closure-soundness-2026-07-29.md` — the
  source of the confirmed repro and the separable step-2/step-3 analysis this RFC builds
  its two-part proposal on.
- `metel-core#716`, `metel-core#717` — unrelated fixes landed this cycle, cited only for
  §3's `construct_generic_body`/generic-body-construction connection.
- `metel-core#292` — destructor invocation is not implemented; `drop` bodies never run
  and a non-empty one is rejected outright, so `Drop` is purely type-level today. The
  affine-`once` decision's cost is measured against this, and the decision is worth
  re-examining once #292 lands.
- `metel-core#739` — "Function types satisfy no aspects, so RFC-0061 §7 is unimplemented
  and move checking compensates with a hardcoded `Copy` special case," filed from this
  RFC's Open Questions investigation. Owns the two-notions-of-`Copy` split this RFC
  records but deliberately does not close.
- `metel-core#702` — architectural root cause of #739 (model non-record structural types
  as regular types); `needs-design`, no direction chosen.
- `metel-core#263` — "Migrate hardcoded `Copy` rules for tuples and fixed arrays out of
  the typechecker into stdlib." The same class of work as #739, for other structural
  types.
- `metel-core#736` — "Generic functions cannot be referenced as values at all," filed
  this cycle. §2's scope-boundary note depends on it: a generic named function used as a
  first-class value has no constructed body for the move-checker to walk
  (`ClosureBody::Untyped`) until this is fixed, so this RFC's multiplicity guarantee does
  not yet reach that case.

---

## Decision

**Accepted 2026-08-30**, together with RFC-0152 (co-requirement — RFC-0134's `once`
qualifier is not sound-and-usable without RFC-0152's first-order directional matching).
Part of the v0.13.0 closure cluster (RFC-0134 / RFC-0152 / RFC-0050 / RFC-0153 / RFC-0157).
`call_multiplicity` and `use_multiplicity` are fields on `Type::Fun` (§4), joined by
RFC-0153's `call_mutation`. `many` by default, `once` written; §2 verifies. The
`use_multiplicity` / `Copy` concern is scoped to the move-checking notion of `Copy` only
(the aspect-registry split is metel-core#739); the base function-type spelling is
RFC-0154's.

**Target:** v0.13.0 (metel-core#269) — one implementation PR; shape per ADR-0052.
