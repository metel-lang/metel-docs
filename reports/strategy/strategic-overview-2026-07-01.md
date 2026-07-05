---
id: strategic-overview-2026-07-01
title: "Language Design — Strategic Overview and Progress Report"
type: report
created_date: '2026-07-01'
---

# Language Design — Strategic Overview and Progress Report

*This document supersedes the earlier July 1 draft and the June 29 overview. For the
load-bearing identity and prior state, see `strategic-overview-2026-06-29.md` and
`strategic-vision-2026-06-28.md`.*

---

## What Changed

This update covers two sessions of design work on top of the July 1 draft.

**Phase 1 (type system) completed.** RFC-0008, 0036, 0037, 0060, 0061 were reviewed,
amended, and accepted. RFC-0061 received significant amendments in the second session:
auto-impl propagation for `Send`, `Sync`, and `Drop` through `T[]`; a full rewrite of
the function types section (correcting the claim that function types cannot implement
aspects — they do implement `Callable<A, B>`); `Ord` and `Hash` deferred impls added;
and the `T[]` representation made explicit (sized owned fat struct, never `Copy`).

**Phase 2 (region system) substantially completed modulo RFC-0064 and RFC-0074.**
RFC-0072, 0073, 0077, 0078, 0079, 0080, 0081 accepted. RFC-0074 (Shared Ownership)
was subsequently moved back to under review — its type signatures use `brand 'b`
syntax from RFC-0076, which remains unresolved. Three gap-filling RFCs identified
and accepted in the same pass:

- **RFC-0082 (Associated Types)** — `type X;` in aspect blocks and `type X = Y;` in
  impl blocks were used throughout accepted RFCs without formal specification.
  RFC-0082 closes this gap and amends RFC-0069's informal `SubRegion` definition with
  a normative struct + impl form.
- **RFC-0083 (Public Value Exports)** — `heap` and `local_heap` need to be importable
  as values from `std::mem`. The implemented module system does not support `pub let`.
  RFC-0083 specifies the semantics and the three implementation changes required
  (AST, parser, name resolver). Naming convention: `Heap` (type), `heap` (value).
- **RFC-0084 (Fixed-Size Array Syntax)** — `[T; N]` conflicts with the postfix `T[]`
  convention and with the region bracket channel. Replaced with `T[N]`. Repeat
  construction `[expr; N]` removed (bracket channel takes priority over that form).

**RFC-0075 parked.** After scoping to local-only inference (Case 1), the benefit over
explicit `AutoRegion::scoped` became marginal and conflicts with the `@` sigil's role
as a visible allocation signal. Cases 2/3 (inter-function) cannot be fairly evaluated
without implementation experience. Moved to `0-draft`, status parked.

**RFC-0076 remains under review, deferred.** The brand introduction mechanism (Q1)
is unresolved. Resolving RFC-0076 now also unblocks RFC-0074.

**RFC-0074 moved back to under review.** The core Rc/Arc design is sound, but the
type signatures use `brand 'b` from RFC-0076. Blocking: RFC-0076 Q1.

---

## RFC State

### Accepted (22)

| RFC | Title |
|---|---|
| 0008 | Aspect Objects — `dyn Aspect`, fat pointer, object safety |
| 0036 | Conditional Impl Blocks — `where` clause, syntactic negation disjointness |
| 0037 | Return-Position `impl Aspect` — opaque monomorphised return type |
| 0060 | Aspect Impl Coherence — orphan rule, overlap, CWA, auto-impl, priority |
| 0061 | Structural Aspect Bounds — `T[]` blanket impls, auto-impl propagation, `Callable` |
| 0063 | Region Handles — `@[r] T`, bracket channel, sendability |
| 0065 | Region Ergonomics — `@T` elision, call-site inference |
| 0066 | Region Pointer Extraction — move-out semantics, `T: !Drop` constraint |
| 0067 | Reference Types — `&T`, `&mut T` |
| 0068 | Struct-Owned Regions — `[own r]` |
| 0069 | Sub-Region Typing — `SubRegion<R>`, `Outlives` (amended by RFC-0082) |
| 0071 | Ownership and Move Semantics — affine types, `Clone`, `Drop` |
| 0072 | Negative Bounds — `T: !Aspect` |
| 0073 | AutoRegion — five guarantees, compiler latitude |
| 0077 | Region Generics — impl headers, variance, wellformedness |
| 0078 | Bottom Type — `!`, uninhabited coercions, `Result<T, !>` collapse |
| 0079 | Perhaps and Result — formal definitions, prelude membership |
| 0080 | Stdlib Aspects — `Clone`, `Deref`, `Send`, `Sync` |
| 0081 | Negative Impls — `impl !Aspect for Type`, priority over auto-impl |
| 0082 | Associated Types — `type X;` in aspects, `type X = Y;` in impls, projection |
| 0083 | Public Value Exports — `pub let`, `heap`/`local_heap` naming convention |
| 0084 | Fixed-Size Array Syntax — `T[N]` replaces `[T; N]`; `[expr; N]` removed |

None of these is implemented except the memory model primitives in RFC-0063/0065.
Every RFC from 0066 onward is ahead of the interpreter.

### Under Review (2)

**RFC-0076 — Brand Types.** Q1 (brand introduction mechanism) remains unresolved.
Deferred to the follow-on block after Phase 3 begins.

**RFC-0074 — Shared Ownership (`Rc`, `Arc`).** Moved back from accepted. The struct
definitions use `brand 'b` as a type parameter kind (`struct Rc<T, brand 'b>`,
`PhantomBrand<'b>`), which is RFC-0076 syntax. Until RFC-0076 Q1 is resolved, the
type signatures are formally incomplete. The core API design (`new`, `clone`,
`get_mut`, `try_unwrap`, sendability rules) is solid and does not change. Blocking:
RFC-0076.

### Draft / Parked

**RFC-0075 — Region Inference.** Parked. The right scope and tradeoffs cannot be
determined without implementation experience. Revisit after the borrow checker and
region allocators are running.

**Draft backlog (~22 RFCs).** Secondary priorities include RFC-0038 (impl aspect
struct fields), RFC-0039 (aspect alias syntax), RFC-0049 (linear fun type system),
RFC-0064 (fork-join parallelism), RFC-0003 (concurrency model), and others.

---

## The Design/Implementation Gap

The gap named in the June 29 overview has grown wider, not narrower.

23 accepted RFCs specify a coherent, mutually consistent language. The interpreter
enforces none of it. No borrow checker. No region allocator. No move semantics. No
affine type enforcement. The language that runs today is structurally different from
the language the RFCs describe.

This is the dominant risk. The specification is now comprehensive enough to begin
Phase 3. Every additional design RFC written before implementation begins extends the
feedback gap. RFC-0075 is the concrete example of this risk materialising: inference
that looked plausible on paper became speculative without running programs to measure.

---

## Honest Assessment

**Type system** — complete. All five cluster RFCs accepted, amended, and internally
consistent. RFC-0061 in particular required significant rework: the function-types
section was wrong (blanket exclusion from all aspects); auto-impl propagation for
structural types was absent; `T[]` representation was implicit. These are now
specified.

**Region and ownership model** — substantially complete. Allocation, borrowing,
move-out, and drop are fully specified across 14 accepted RFCs. Shared ownership
(RFC-0074) is under review pending RFC-0076: the `brand 'b` parameter in `Rc<T, 'b>`
and `Arc<T, 'b>` cannot be formally grounded until the brand introduction mechanism
is resolved. The core Rc/Arc API design is not in dispute — only the type signatures.
Associated types (RFC-0082), the module system extension (RFC-0083), and array syntax
fix (RFC-0084) close three concrete usability gaps.

**Brand types** — deferred. RFC-0076 Q1 (brand introduction mechanism) is an open
design question that cannot be resolved without implementation feedback. The correct
call is to defer, not speculate.

**Region inference** — parked. RFC-0075 cannot be fairly evaluated without running
programs. The explicit annotation system (RFC-0063 + RFC-0065) is ergonomic enough
to begin with.

**Concurrency** — not started. RFC-0064 (fork-join) is the one remaining Phase 2
design item. It can be scoped without brand-gated tokens; `JoinToken<'b>` integration
is a follow-on when RFC-0076 is resolved.

**Implementation** — the right next step. The specification is stable. Implementing
before it was stable risked rework (RFC-0074 rewrite is the example). That risk is
now past for the core. The borrow checker, region allocators, and move semantics
enforcement have a stable target.

---

## Priorities

### Immediate — RFC-0064 (Fork-Join Parallelism)

The one remaining Phase 2 design item. Scope it without brand-gated tokens. This
closes Phase 2 cleanly and gives the concurrency model a foundation before
implementation begins.

### Phase 3 — Implementation

Begin implementing the borrow checker and region system against the accepted
specification. Recommended order:

1. Move semantics enforcement (RFC-0071) — affine types, no implicit copy
2. Reference types and borrow checking (RFC-0067) — `&T`, `&mut T` lifetime rules
3. Region allocation (RFC-0063) — `@[r] T`, Heap and LocalHeap backed by real allocators
4. `pub let` (RFC-0083) — three-file change; unblocks `heap`/`local_heap` in stdlib
5. Fixed-size array syntax update (RFC-0084) — parser and spec change; mechanical

### Follow-on — RFC-0076 (Brand Types)

Revisit once the borrow checker is running and the ergonomic cost of explicit
annotation is measurable. Q1 (brand introduction mechanism) is the only blocking
design question.

---

## What Would Change This Assessment

The assessment changes in one direction: if Phase 3 is started and the borrow checker
implementation surfaces a fundamental contradiction in the RFC cluster. The cluster
has been reviewed on paper and is internally consistent; implementation may reveal
edge cases the paper review missed. If that happens, targeted RFC amendments are the
right response — not a cluster rewrite.

The assessment does not change if RFC-0076 remains unresolved. Brand types do not
block the core implementation. The concurrency story waits for RFC-0076; the
implementation does not.
