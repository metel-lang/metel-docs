---
id: rfc-0245
title: "Effect Rows and Marker Effects"
date: '2026-11-22'
status: draft
---

**Target:** v0.17.0 (stage "Effect rows and markers", design in "Effects design settlement"). Design settlement tracker: metel-core#1672.
Everything below the headings marked *provisional* is a proposal for review, not a decision.

## Summary

A function, closure or callable type may declare a **row of effects**: a checked upper bound on what evaluating it may do. A row
holds two kinds of entry in one calculus: **marker entries**, labels that describe behaviour (`FileRead`, `Network`, `Diverge`) and
that no handler may erase by wrapping, and **operation entries**, abstract requests that a handler can discharge (RFC-0140). Rows
are checked, not documented: a body must fit its declared row, a callable with row `E` is accepted where one with row `F` is
expected when `E ⊆ F`, and a closure's row is inferred from its body and kept through captures, generics, aspect dispatch and
type erasure.

```metel
effect FileRead;                                   // a marker, declared in std: puts `.FileRead` in the vocabulary
effect Console { fun read_line() -> String; }      // an operation interface (RFC-0140)

fun load_config(fs: &ReadDirectory, path: &String) -> Result<String, ReadError> effects .{ .FileRead } { .. }
fun uppercase(s: &String) -> String effects .{} { .. }                         // the empty row: no tracked effects

fun apply<T, U, ..E>(x: T, f: once |T| -> U effects .{ ..E }) -> U effects .{ ..E } { f(x) }

apply(3, |n| n + 1);                    // E is inferred: the closure has no tracked effects
apply(3, |n| { retry_forever(); n });   // E is .{ .Diverge } and the caller's own row must allow it
```

A row is written as an ordinary Metel row, `.{ … }`, with the entries Metel rows already have (RFC-0189): `.x`, `.x: T`, `!.x` and
the open tail `..R`. The empty row `.{}` is the same row as `()` (RFC-0231).

**A row is not a value.** An effect row exists only in types and is erased after checking. `E` in `apply<T, U, ..E>` is a **row
binder** (RFC-0208): a generic parameter that stands only for a row, never for a type, so a bare `E` is not a type and naming it is an
error. It can appear only spliced as `..E` inside a row. `record E` would be the wrong binder, because it stands for a record *type*
(RFC-0186), which a value can have. Markers have no runtime representation at all; an operation entry has a runtime counterpart
only in the evidence a handler passes (RFC-0140), which no program names, constructs or stores.

It also settles three questions the effects work depends on: the **surface** (the keywords `effect` and `effects`, not RFC-0140's
`^`), how `Panic` is treated (**left open**: the working position is that it stays **ambient**, not a tracked label, with a **no-panic
guarantee** available where asked; the alternative is to track it in rows),
and how an operation's **control behaviour** (returns once, may capture, never returns) is classified, so that handling an
operation never hides that it can abort.

This RFC does not specify handlers' runtime, capability objects (metel-core#1673), restricted interpolation (#1674) or execution
budgets.

---

## Motivation

Nothing in Metel's types says what a function may do besides return a value and take its arguments. That has four consequences
the language now has to deal with.

1. **Restricted computation cannot be enforced.** An API that runs a caller-supplied callback, a string interpolation that must not
   perform IO, a predicate that must be total (RFC-0202): each needs the callee to *know* what the callback may do. Today the
   only means is convention.
2. **Natives can hide effects.** Std has about 160 `native(@std...)` declarations (`core` 145, `fs` 10, `env` 2, `process` 2).
   Nothing records that `std.fs.read` reads the filesystem, so nothing can refuse to call it from a restricted place.
3. **RFC-0140 has no type-level home for the effects it handles.** It reads the effect row as "the type-level projection of the
   handler context" (its section 11), but a row of that kind needs a calculus that exists independently of handlers, because most of
   what a row is used for (restricting a callback, labelling a native) involves no handler at all.
4. **Function types are about to carry markers.** RFC-0232 re-expresses `once`, `var` and `copy` as marker aspects on a callable.
   An effect row is the next thing a callable type should carry, and it should reuse that mechanism instead of growing a second one.

The design is a discussion draft first written for metel-core#1662 (sections 2, 6 and 8). This RFC takes it, applies the decisions
made on 2026-11-22 (metel-core#2139), and states what remains open.

---

## Design

### 1. Entries: markers and operations *(provisional syntax)*

```metel
effect Diverge;                          // a marker: declares the label `.Diverge` in the effect vocabulary
effect Console {                         // an operation interface a handler implements
    fun read_line() -> String;
    fun write_line(s: &String);
}
```

A semicolon declares a **marker**; a body declares an **operation interface**. A marker is a label, not an aspect that types can
implement: `extend T: FileRead` is an error, because that would let any type manufacture a permission or erase a function's
effects.

In a row, the two kinds of entry take the two entry forms rows already have:

| Entry | Written | Meaning |
|---|---|---|
| marker | `.FileRead` | the label `.FileRead` (a label of any type, in RFC-0189's terms) |
| operation | `.console: Console` | a handler role `.console` for the interface `Console`, possibly applied, `.state: State<S>` (RFC-0140 section 11: a row of role and handler) |
| absence | `!.Panic` | no such label (section 8) |
| open tail | `..E` | the rest of a row parameter |

**Labels are structural.** RFC-0221 makes a row label a name, written `.name` and never bare, so `.FileRead` is the same label
wherever it is written. The `effect FileRead;` declaration puts the label into the **vocabulary**, and a label in an `effects` row
that is not in the vocabulary is an error: without that, a typo in a negative entry (`!.Panik`) would silently guarantee nothing.
This trades per-declaration identity for the existing row notation. Effects are restrictions, so a collision would make a class
coarser, never unsound; operation entries keep nominal identity through their interface type.

**Only std declares markers in this release.** User code uses them in rows and may declare operation interfaces, but cannot declare a
new marker. Labels share one program-wide namespace, so a marker declared by a library could clash with another's, and no marker
needs minting yet: the only primitive effects come from std's `native` declarations (section 9). How a library mints a marker, and
how it avoids a clash, is settled with Interop, which needs it for user-declared natives.

**The role label of an operation entry is required.** `.console: Console` keeps entries uniform with records (`.x: T`) and with
RFC-0221's rule that a label is never bare. It is redundant under rule 9 (one entry per interface), but it is what would let a
relaxed rule 9 hold two handlers of one interface under distinct roles (`.a: State<i64>`, `.b: State<i64>`) with no new notion of
scoped labels. A lint suggests the interface name in snake case as the role.

Operation labels and marker labels have **distinct names**: an operation `Console` is handled by a handler that may itself use a
terminal, which leaves the markers `ConsoleRead` and `ConsoleWrite` in the residual row. The same operation handled by a fixed
in-memory value leaves none. Two declarations never compete for one meaning.

Effects are **restrictions, never permissions.** A row says what a body may do; nothing in a row grants authority. Authority is a
capability object (metel-core#1673), which is a value passed as an argument. A handler that handles an abstract operation cannot
fabricate filesystem or network authority; it needs a capability for it.

**Initial marker vocabulary** (proposal): `ConsoleRead`, `ConsoleWrite`, `FileRead`, `FileWrite`, `Network`, `Process`, `Env`,
`Clock`, `Random` and `Diverge`. Allocation, blocking and a runtime-managed release marker are **not** in the first vocabulary:
`effects .{}` means "no tracked effects", not "allocation-free" or "cheap" (see Open questions 7). Effect inheritance and aliases
(`Net: IO`) are deferred until the direction of subsumption is specified; the first version has independent labels and explicit sets.

### 2. Rows *(provisional syntax)*

```metel
fun f(..) -> T effects .{ .FileRead, .Network } { .. }  // a declared upper bound
fun g(..) -> T effects .{} { .. }                        // no tracked effects
fun h(..) -> T { .. }                                    // no row: see rule 4
```

**Grammar.** The `effects` clause is its own production, built from parts of the grammar that exist: the keyword `effects`, then
`.{`, a list of `row_field` entries (`bang? label (":" type)?`, as in a row bound, so a label-only entry like `.FileRead` and a
negative entry like `!.Panic` already parse), an optional named tail (`row_tail`, `".." ident?`, as in an open record type), and `}`.
No existing rule is changed and there is no new token. Neither existing rule serves on its own: a row bound has label-only and
negative entries but its tail is a bare `..` with no name, and an open record type has a named tail but every field needs a type.

**Rule 0 (what a closed row means here).** As a record type, a closed row `.{ .a }` has exactly the field `.a`. After the keyword
`effects` a closed row is an **upper bound**: at most these labels. The keyword alone fixes this, since the clause is its own
production and is not read as a record type or a row bound; no further marker is needed. A row with an open tail, `.{ .a, ..E }`, is
"these labels and whatever `E` stands for". The relation in rule 3 is the same one as row narrowing (RFC-0117), read as "a callee's
needs are a projection of what the context provides": the context row is the wider one.

**Rule 1 (upper bound).** A row is an upper bound: it does not say every execution performs every listed effect. A body *fits* a
row when the union of the effects of every evaluated subexpression, every invoked operation and every implicit call is a subset
of it. Every branch contributes, so the bound is conservative. Reachability uses an established analysis, never optimistic constant
folding.

**Rule 2 (calls).** A call contributes the callee's declared row. A higher-order call contributes the callback's row. A call
through abstract dispatch contributes the row the aspect method declares (section 5).

**Rule 3 (widening).** For fixed argument and result types, a callable with row `E` is accepted where a callable with row `F` is
expected when `E ⊆ F`. The rule changes nothing about ownership, multiplicity, parameter variance or capability parameters.

**Rule 4 (no row).** A named function with no `effects` clause is **unrestricted**: its row is the top row, it may do anything, and
it cannot be called from a body whose row is declared. A private (non-`pub`) function without a clause has its row **inferred** from
its body; a `pub` function never has one inferred, so a public signature does not change when a body does. A closure's row is always
inferred. This is gradual: existing programs keep their meaning, and a restriction applies exactly where a row is written.

**Rule 5 (row parameters).** A row can be abstracted over with a **row binder**, `<..E>` (RFC-0208), so a higher-order function
passes its callback's row through (the `apply` example above). An open row is written with the existing rest convention,
`effects .{ .FileRead, ..E }`. This **depends on RFC-0208, which is under review**: today the only binder for a row is `record E`
(RFC-0186), which also lets `E` be used as a type, and an effect row must not be. RFC-0208 is additive (it adds a binder and removes
nothing), and it is settled and implemented in the same release as this RFC (metel-core#1789 and #2167, in the stage that implements
this one), so no interim restriction on `record E` is needed.

**Rule 6 (no erasure).** An effect is never erased by a type: not by a coercion to `dyn`, not by a generic parameter, not by a
closure being stored in a field. Where a row is lost, the result is the top row, which is rejected by any bounded context.

### 3. Callables and RFC-0232

A written function type carries its row after the result: `once |T| -> U effects .{ ..E }`. By RFC-0232 a written function type is
`dyn Callable<Args, Ret>` with markers; the row is one more component of that type. Two properties follow.

- **The direction of widening is the reverse of a capability marker.** For `Copy`, `CallMany` and `CallShared` a callable that
  *has* the marker is accepted where it is not required (`M ⊇ M'`). For an effect row it is the callable that has *fewer* labels
  (`E ⊆ F`). Both are subset rules over one lattice: the callable's behaviour is described by its guarantees (the markers it has) and
  its effects (the labels it may perform), and a value is usable at any type that demands no more guarantees and permits no fewer
  effects. A row can therefore be implemented as part of the marker set with the opposite sense, or as a distinct component with the
  same coercion; the choice is an implementation matter for RFC-0232's mechanism and does not change the surface.
- **A closure's type is its environment type** (RFC-0232 rule 4), so its row is inferred from its body exactly as its markers are,
  and is fixed by the closure literal.

### 4. Generics and polymorphism

A generic function bounded by a callable keeps the row of whatever it is instantiated with. A bound may constrain it:
`F: Callable<.{ .0: T }, U> + effects .{ .FileRead }` states that `F` may perform at most `.FileRead`. The result row of a function
that calls a row-polymorphic callback includes the callback's row, as `apply` shows. Row inference is first-order: it solves for
`E` at a call site from the argument's row, as type arguments are solved today, and does not introduce subtyping constraints into
unification (the same choice Koka makes, see Prior art).

### 5. Aspect dispatch and `dyn`

An aspect method signature may declare a row. An implementation's row must be a subset of its aspect's declared row for that
method (an implementation may do less, never more). A call through a bound `T: A` contributes the aspect's declared row. A method
with no declared row is unrestricted by rule 4, so a bounded context cannot call it; this is the conservative reading and it is
why an aspect meant to be callable from restricted code states a row on each method.

A `dyn` value's row is part of its type (section 3). Reflection, dynamic dispatch and unsafe operations provide no unlabelled
bypass: each yields the top row.

### 6. Operation entries and control classification *(decides RFC-0140 open questions 4 and 6)*

Operation entries share the row calculus of sections 2 to 5. What is different is that a handler can discharge them.

**Rule 7 (discharge).** `handle e { .. }` has the row of `e`, minus the operation labels the handler handles, plus the row of the
handler's own implementation. A marker is never discharged by a handler: it remains in the residual, because wrapping a call in
a handler does not change what the underlying behaviour is.

**Control classification.** An operation declares how it may be resumed. This is the `fun` / `ctl` / `final ctl` split of Koka,
adopted here as the classification the row tracks (RFC-0140 open question 4):

| Class | A handler may | The performer observes |
|---|---|---|
| `fun` | resume exactly once, in tail position | an ordinary call that returns exactly once |
| `ctl` | resume zero or one time, or abort | a call that may not return |
| `final ctl` | never resume | a call that does not return |

An operation is `fun` unless declared otherwise, because it is the case that needs no continuation capture (state reads,
configuration, logging); the class is part of the declaration, so a handler cannot strengthen it.

**Rule 8 (control survives handling).** A body is **control-transparent** when every operation it performs, including operations
it handles itself, is `fun`. Handling a `ctl` or `final ctl` operation inside a block removes its label from the row but does
**not** make the block control-transparent: the label disappearing must not hide that the handler may abort. A policy that
requires "always returns" (restricted interpolation, a restricted callback) checks control-transparency in addition to the row.

**Rule 8a (early exits are control too).** `?`, `return` and `break` are non-local control flow that is not an operation, and rule 8
as written does not see them. A body that contains one whose target lies **outside** a restricted region is not control-transparent
with respect to that region. The case that matters is interpolation: in `"${ f()? }"` the `?` returns from the *enclosing function*
in the middle of building a string, an exit invisible at the placeholder, whereas a `?` inside a restricted callback returns from the
callback and stays local. The language already treats a propagating `?` as an implicitly chosen exit once: RFC-0164 classifies a
mutating closure with one as call-once. A restricted region therefore either rejects an early exit that leaves it or records it as
a control behaviour of the region; which, and how it composes with `Try` (RFC-0190), is open (Open questions 11).

**Rule 9 (one handler per interface).** The entries of a row form a set with at most one entry per operation interface, and in
the first version **at most one handler of a given interface is in scope** (RFC-0113's "ambiguity is always a compile error",
RFC-0140 section 11, where the label is the type). A nested `handle` of an interface already handled is rejected. A role label
such as `.console` is then a name for the interface's one entry, not a way to hold two. This is the conservative answer to RFC-0140 open question 6, chosen because it can be relaxed
later (to scoped labels, with an explicit way to address the outer handler, as Koka's duplicate labels do) without breaking
programs that were accepted under it, whereas the reverse cannot.

Evidence passing is an implementation strategy for handlers and is not part of this RFC. The classification is what lets an
implementation avoid capturing a continuation for `fun` operations.

#### Errors as values, and abort *(proposed position, open)*

Metel handles an expected failure as a value: `Result<T, E>` and `Option<T>` are ordinary types, and `?` is an early `return` that
rebuilds the enclosing return type (RFC-0182, generalized by `Try` and `FromResidual` in RFC-0190). An abort operation (`final ctl`)
does a similar job in effect-polymorphic code, and a panic is itself a non-resumable effect (RFC-0014). Three mechanisms can fail a
computation, and nothing yet says how they relate. The position proposed here, to be confirmed with RFC-0014:

- **`Result` and `?` remain the idiom for recoverable, expected errors.** The error is visible in the function's type.
- **An effect is behaviour that is not in the type.** A function that returns `Result` gets no effect label for failing; an abort
  entry appears in a row only for an operation that really is one.
- **No `Exception` effect in std at first.** Handlers are not in v0.17.0, and an `Exception` effect beside `Result` would give two
  competing styles before there is evidence for either.
- **When handlers arrive, bridges both ways** are specified: a standard handler that turns an abort into `Err`, and `?` rebuilding
  an enclosing type through `FromResidual` (RFC-0190) as the way back. RFC-0014 carries the related open question of whether
  recovering from a panic produces a `Result<T, PanicError>`.

A linear value live at an exit is the same question in both worlds: RFC-0089 section 2.2 lists an early `return` or `?` as an
implicit drop that needs `T: Discard`, so such a value is rejected at `?`, and the Linear types stage extends the rule to handler
abandonment and panic recovery (they have no implicit drop).

### 7. Divergence

`Diverge` is a marker: evaluation may fail to terminate normally because it can keep computing. It is not inferred from a return
type, and `Never` also describes operations such as `panic` that are not infinite loops. Conservative rules for the first version:

- A general `loop` or `while` contributes `Diverge` unless a supported rule proves it finite; a syntactically obvious unconditional
  exit may be admitted.
- A recursive call cycle contributes `Diverge` unless an explicit checker proves a decreasing well-founded measure. The first
  version may reject all recursive cycles from a body whose row omits `Diverge`.
- An eager traversal of a fixed finite collection is admitted only when the iteration and each callback are known to terminate; a
  custom iterator can hide unbounded work in `next()`.
- Abstract dispatch retains `Diverge` when it cannot establish its absence.
- A native without `Diverge` makes a termination promise under its documented runtime assumptions; the annotation is a trusted
  obligation.

The checker may reject terminating programs and does not try to decide termination. It provides no running-time bound: a huge finite
computation can still stall a UI, and blocking IO needs its own policy.

### 8. Panic, and a no-panic guarantee *(open)*

Whether `Panic` is a tracked label is **left open** by this RFC. Panics are effects in the algebraic sense (RFC-0014: non-resumable,
handled by handlers, Drop runs during recovery, an unhandled panic exits immediately), and a handler can catch one. The question is
whether they appear in rows. The spec's sources of panic are integer overflow (unconditionally), division by zero, out-of-bounds
access, `.yolo()` on an absent or error value, a failing `assert` and a direct `panic`.

- **Position A, ambient.** `Panic` is not a tracked label, so rows list declared markers only and a function is not annotated merely
  because it indexes, divides or asserts. This is the **working position** of metel-core#2121 for v0.17.0. Its cost: tracking `Panic`
  later breaks every explicit row that omitted it, so it is to be revisited before the Stability commitment.
- **Position B, tracked in rows** (Koka's `exn`). `.Panic` is an ordinary label, and `effects .{}` then guarantees no panic. It is
  precise, and reversible later with less breakage (dropping a label breaks only code that wrote it). Its cost: every function that
  does arithmetic, indexes or asserts writes `.Panic`, and most of the roughly 145 `core` natives would carry it.

Either way a **guarantee** is needed, by RFC-0202's predicates (no panic, overflow or division by zero) and by restricted
interpolation. Under B it is the absence of `.Panic` from a closed row, with no further machinery. Under A it must be **opt-in**: a
function may declare that it does not panic, and then the compiler checks it. The rest of this section describes that opt-in
guarantee; its content is the same under either position.

- **What it promises:** no language-level panic. **What it does not:** freedom from out-of-memory, process signals or host failure,
  and not termination (`Diverge` is separate).
- **The check:** the body uses none of the panic triggers and calls only functions that carry the guarantee. Closures infer it from
  their body, and a bound can require it of a callback. Checked forms (`get`, `match`, the `checked_*` family) are allowed.
- **Natives** carry it as a trusted obligation, only where true.
- **Known limit, accepted:** plain integer arithmetic is unavailable in such a body, because integer overflow panics, until checked
  arithmetic (RFC-0142, metel-core#841, outside v0.17.0) exists. RFC-0202 predicates over integers meet the same limit.

Under position A, two spellings are candidates, to be chosen in review (Open questions 1):

1. **A positive marker**, working name `NoPanic`, in the marker mechanism of RFC-0232: presence is the guarantee.
2. **A negative entry** `!.Panic` in the row, `effects .{ .FileRead, !.Panic }`. With rows written as `.{ … }` this needs **no new
   grammar**: RFC-0189 already implements negative entries (`!.x`), and RFC-0072 the same idea for aspects (`T: !Aspect`). `.Panic`
   is then an ordinary label that is *unchecked by default*, and `!.Panic` opts in to checking. This reads uniformly with `Diverge`,
   whose guarantee is also its absence, and it makes tracking `Panic` by default later a change of default and not of vocabulary.
   Internally it can still be a positive guarantee bit, so section 3 is unaffected.

### 9. Native effect metadata

A `native` declaration states its row, and the row is **trusted**: it is the declaration's promise about the host code.

```metel
native(@std.fs.read)  pub fun read(path: String) -> Result<String, OsError> effects .{ .FileRead };
native(@std.core.print) pub fun print(s: String) effects .{ .ConsoleWrite };
native(@std.core.list_new) fun new() -> List<T> effects .{};
```

A native with no row is unrestricted by rule 4 and cannot be called from a body with a declared row. Every std native is annotated
before the release that ships this (a std audit item), and a native with unknown external behaviour stays unrestricted. Under position A of
section 8 a native that may panic carries no panic metadata; under B it carries `.Panic`. User-declared natives and the contract for them belong to Interop and extend
this metadata.

### 10. What is deliberately not here

- **Implicit cleanup.** A `Drop` body is not exempt from effect checking, but the checked destruction-effect summary per type,
  including abstract and erased types, is metel-core#1674's prerequisite and is not specified here. Until it exists, rows describe
  **explicit** calls only, and a restricted context must reject unproven cleanup instead of claiming isolation.
- **Capability objects** and filesystem confinement (#1673), **restricted interpolation** and policy aliases (#1674), **handlers'
  runtime** and continuation capture (RFC-0140), and **execution budgets** (an independent mechanism: termination checking is not a
  time bound).

---

## What this changes

| Concern | Today | With this RFC |
|---|---|---|
| What a callback may do | convention | a checked row on its type |
| What a native does | undocumented | trusted row on each `native` declaration |
| A callable's type | markers (RFC-0232) | markers plus a row, one coercion rule |
| Panic-freedom | not expressible | a checked guarantee (opt-in if `Panic` stays ambient) |
| Existing programs | unrestricted | unchanged: a row restricts only where written |

---

## Interactions

- **RFC-0232 and RFC-0161.** The row rides on the callable type and reuses the marker mechanism's widening (section 3). The row
  parameter is a row binder, `<..E>` (RFC-0208, **under review**, a dependency: RFC-0186's `record E` also lets `E` be used as a type,
  which an effect row must not be). Whether RFC-0208 comes first is open (Open questions 3).
- **RFC-0140.** One calculus with two entry kinds (sections 1 and 6). This RFC decides its open questions 4 (the `fun`/`ctl`/`final
  ctl` classification) and 6 (at most one handler per interface, relaxable). RFC-0140's `^ E` notation is replaced by the keywords here.
  Its sections 2, 3, 6, 7 and 8 rest on allocator tags that Memory model settlement (metel-core#2116) amends; that is independent of
  this RFC and keeps handlers out of v0.17.0.
- **RFC-0113 (context parameters).** RFC-0140 section 11 reads the row as the handler context. This RFC does not depend on RFC-0113
  (markers have no handler, capability APIs start with explicit parameters), but rule 9 relies on its uniqueness discipline.
- **RFC-0014.** A panic is a non-resumable effect handled by handlers; section 8 sets out the two positions on whether it is tracked
  in rows, without choosing, and describes the guarantee both need. RFC-0014's own open question of how recovery relates to `Result`
  is the one this RFC's subsection on errors as values defers to it.
- **RFC-0164.** A mutating closure with a propagating `?` is call-once, because the exit is implicitly chosen: the precedent for
  treating an early exit as control (rule 8a).
- **RFC-0190 and RFC-0182 (`?`, `Try`, `FromResidual`).** `?` rebuilds the enclosing return type; it is the way back from an abort to a
  value, and a control edge that rule 8a must see. RFC-0190 is scheduled with Numeric and operator model, after this release.
- **RFC-0089 section 2.2.** An early `return` or `?` is an implicit drop needing `T: Discard`; handler abandonment and panic recovery
  are the same kind of site, which the Linear types stage states.
- **RFC-0202.** Its predicates must not panic, overflow or divide by zero; section 8 is the mechanism, with the integer limit.
- **RFC-0010 and metel-core#1674.** Interpolation lowers to ordinary calls before type checking, so the row sees the lowered form; the
  policy that restricts it is #1674's.
- **RFC-0241 (Core).** Core must reserve effect information (its open questions 29 and 36); rows are checked in the frontend and
  add no runtime representation, so Core only needs a place to carry them for later phases.
- **RFC-0189, RFC-0221, RFC-0231, RFC-0186, RFC-0208, RFC-0117.** The row notation: entries `.x`, `.x: T` and `!.x` (RFC-0189), labels
  written `.name` and never bare (RFC-0221), the empty row `.{}` equal to `()` (RFC-0231), the row binder `<..R>` for a
  row-only parameter (RFC-0208, under review; RFC-0186's `record R` stands for a record type), and narrowing as the relation behind
  rule 3 (RFC-0117). Negative entries are also what candidate 2 of section 8 is.
- **RFC-0072.** Negative bounds on aspects (`T: !Aspect`), the same idea for a different kind of bound.
- **RFC-0194 (linear closures).** A closure that captures a linear value is linear; its row is independent. Exactly-once consumption
  matters for handlers, not for rows.

---

## Alternatives considered

| Alternative | Why it loses |
|---|---|
| Keep RFC-0140's `^ E` notation | A symbol for a clause that restricts a body, used in bounds, on parameters and on types, reads worse than a keyword, and the pipe notation for function types (RFC-0154) already makes the type position crowded. Keywords also let `effects .{}` state "no tracked effects" without a separate `pure`. This is the #1662 draft's recommendation (its decision 7). |
| Bare braces, `effects { FileRead, ..E }`, with per-declaration identity | Introduces a row-like form of its own that does not reuse RFC-0189's entries, the open-tail rest syntax or the row binder, and makes `!Panic` and a row parameter new grammar. It does keep declaration identity across modules, which the chosen form trades for the existing notation. |
| Every marker a typed entry, `.fs: FileRead` | Gives markers nominal identity through a unit-like type, but each entry then needs a role label nobody wants to name, and the row grows two names per marker. |
| Marker effects as ordinary aspects (`effect aspect`) | Any type could then implement one, so `extend T: FileRead` could manufacture a permission or erase an effect. A label is not implementable. |
| Track `Panic` in rows (Koka's `exn`) | **Not rejected: this is position B of section 8, left open.** Precise and reversible later, but with explicit rows every function that does arithmetic, indexes or asserts must write `effects .{ .Panic }`, and most of the `core` natives would carry it; the v0.17.0 slice's tests do not need it. The working position for v0.17.0 is ambient (metel-core#2121), revisited before the Stability commitment. |
| Effects by subtyping instead of row polymorphism | Koka chose rows because the constraints get complex and combining polymorphism with subtyping can make inference undecidable. The subset rule here is applied at coercions, not solved in unification. |
| Infer every named function's row | A public signature would change when a body does, and a missing annotation would read as evidence of purity. Inference is limited to private functions and closures (rule 4). |
| Rows required on every named function | Breaks every existing program for no new guarantee. The gradual rule keeps them. |
| A handler-first design that derives markers from operations | Most uses of a row (restricting a callback, labelling a native) involve no handler; the calculus must exist without one. |

---

## Prior art

| System | What it does | Relevance |
|---|---|---|
| Koka | Effect types are rows, inferred; `exn` and `div` are in rows so a function without them cannot throw or diverge; `fun`/`ctl`/`final ctl` classify operations | the row calculus, the classification, and the choice of rows over subtyping |
| Scala 3 capture checking | A function's type records the capabilities it uses; smaller capture sets are subtypes; the plain arrow is pure and `=>` is shorthand for `->{cap}` | subset widening, and a pure default for the new form next to a permissive legacy form |
| Rust | No effect tracking; panics are not in signatures; `UnwindSafe` is a marker bound at `catch_unwind`; `unsafe`, `async` and `const` are separate keywords | the ambient-panic default |
| Swift, Java | `throws` and `async` are single-purpose, tracked effects; unchecked exceptions are ambient | an effect system that tracks some failure and leaves the rest ambient |
| Ada SPARK | Proves the absence of runtime errors, including overflow and range errors | the no-panic guarantee and its integer-arithmetic limit |
| OCaml 5 | Effect handlers with untracked effects | handlers without rows |

Koka and Scala are sourced from the papers and documentation listed under References; the rest is from general knowledge of the
languages and should be checked before this RFC leaves review.

---

## Open questions

1. **Is `Panic` tracked in rows, or ambient?** (section 8) Position A, ambient, is the working position for v0.17.0
   (metel-core#2121); position B, tracked as `.Panic`, is precise and cheaper to reverse. This RFC leaves it open. Evidence that would
   decide it: how much std and user code carries `.Panic` under B, whether the opt-in guarantee under A is used in practice, and
   whether tracking it later is acceptable before the Stability commitment.
   **If ambient (A), the spelling of the no-panic guarantee:** a positive marker or the negative entry `!.Panic`, which needs no new
   grammar. If `!.Panic`: how `.Panic` is exempt from the rule that a closed row excludes unlisted labels (rule 0 makes a closed row
   an upper bound, so the exemption must be stated); whether a positive `.Panic` entry is meaningless or rejected; that the bound
   needs an analysis of the body, not an impl-table lookup as in RFC-0072; and whether panic-freedom is **inferred** from visible
   bodies and stated only on public or opaque functions, which would remove most of the annotation burden.
   **If tracked (B):** what migration looks like for the std natives and existing programs, and whether `.Panic` is inferred for
   private functions so that only public signatures state it.
2. **The default for a named function with no row** (rule 4): unrestricted, with inference for private functions. Is "unrestricted"
   the right top element, and should a `pub` function without a row be a warning?
3. **Rows as `.{ … }`, what remains.** Settled in this draft: the notation and entry forms (section 1); the grammar, a production of
   its own built from `row_field` and `row_tail` (section 2); a closed row as an upper bound, fixed by the keyword `effects` alone
   (rule 0); the row binder, RFC-0208's `<..E>`, which joins the same release (#1789, #2167); only std declares markers in this
   release; the role label of an operation entry is required, with a lint; a label not in the vocabulary is an error. Still open:
   (a) a turbofish argument for a row parameter (RFC-0192, shared with RFC-0208), so that `apply::<i64, i64, .{ .FileRead }>(..)` can
   pin a row;
   (b) how a library mints a marker, and how it avoids a clash in the program-wide label namespace: deferred to Interop, which needs
   it for user-declared natives, but the answer may change what a label is (a namespaced label, or a declaration that registers a
   name), so it is a question for this RFC to hand over explicitly.
4. **Control classification details** (section 6). Is the class per operation or per interface? Is `fun` the right default? Is
   control-transparency (rule 8) the right condition for restricted interpolation, or must it also bound how many times an operation
   is performed?
5. **One handler per interface** (rule 9). Relaxing it to scoped entries is non-breaking, but what does addressing the outer handler
   look like, and does RFC-0113's uniqueness rule survive it?
6. **Cross-module boundaries and trust.** What stops a function from declaring a row its body does not fit, in a module compiled
   separately? How are trusted native rows audited, and is `unsafe` needed to declare one?
7. **Vocabulary.** Whether allocation, blocking, nondeterminism, clock access and a runtime-managed release need separate labels, and
   what "managed allocation in restricted formatting" must not authorize (arbitrary allocator callbacks).
8. **Implicit cleanup and generic destruction.** The destruction-effect summary of section 10 is a prerequisite to the full
   restriction guarantee, not polish: how does generic code destroying an unknown `T` bound its cleanup?
9. **Termination rules** for finite loops and mutual recursion, and where proof ends and trust begins across modules.
10. **Interaction with comptime** (RFC-0132): is a `comptime fun` required to have `effects .{}`, and the no-panic guarantee where a
    predicate evaluates?
11. **Early exits in restricted regions** (rule 8a). Is `?`, `return` or `break` crossing a restricted region rejected, or recorded as a
    control behaviour of the region? Does the answer for `${ f()? }` differ from the one for a restricted callback? How does it
    compose with a `Try` type other than `Result` and `Option` (RFC-0190)? Restricted interpolation (metel-core#1674) needs the answer.
12. **`Result`, `?` and abort** (the subsection after rule 9). The proposed position (`Result` as the idiom, no `Exception` effect at
    first, bridges when handlers arrive) is to be confirmed with RFC-0014, together with its open question of what recovering from a
    panic produces.

---

## Implementation notes

Staged, each step independent of the next, and **marker entries and rows only** in v0.17.0 (the stage "Effect rows and markers"):

1. The keyword `effect` (markers, std only; operation interfaces, anywhere), the `effects` production of section 2, the vocabulary
   check, and the row binder (RFC-0208); operation interfaces parse and are typed as entries, with no runtime (handlers are
   RFC-0140's). The role-label lint lands with it.
2. The row component of the callable type, the coercion rule and closure inference, on RFC-0232's mechanism.
3. Aspect-method rows and implementation checking; `dyn` rows.
4. The std native audit: a row on each of the roughly 160 `native` declarations.
5. `Diverge` rules (section 7) and the no-panic guarantee (section 8), with fixtures for each panic trigger and a callback API that
   requires a restriction.

No step needs a deprecation period: the language has no users, and rule 4 keeps existing programs unchanged.

---

## References

- Leijen, *Koka: Programming with Row Polymorphic Effect Types* (MSR-TR-2013-79, arXiv 1406.2061).
- Scala 3 reference, *Capture Checking* (experimental).
- metel-core#1662 (the design draft), #1672 (this RFC's tracker), #2139 (the dependency audit and decisions), #2121 (`Panic`).

---

## Decision

**Outcome:** *(pending)*
