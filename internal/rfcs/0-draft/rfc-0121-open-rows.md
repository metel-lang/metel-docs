---
id: rfc-0121
title: "Open Rows"
date: '2026-07-24'
status: draft
target:
---

> **Extracted from RFC-0090 §2 (open half), §4 and §7 on 2026-07-24** (superseded; see
> RFC-0116's header for the split rationale). Depends on RFC-0118 (Row Bounds) and RFC-0120
> (Named Records).
>
> **This is the expensive half of the cluster, and RFC-0090's own build order said so:**
> *"`<row R>` open generics later, separately, only if a real duck-typing need
> materializes. This is where the actual cost lives — treat it as its own decision with its
> own timeline, not a prerequisite for step 1."* The split makes that literally true rather
> than an intention inside a document that had to be accepted whole.

## Summary

Row-kinded generic parameters — `<row R>` at the binder, `..R` at every use — letting code
abstract over "the rest of a row" rather than naming a concrete shape. Adds a row equation
form in `where` clauses (`where R = { token: Token, ..Rest }`) which serves as row
*decomposition*, and row-conditional impls, which realize typestate directly in the row.

This is the only piece of the records cluster that introduces a **row kind** and
**row-unification** into the type system. Everything in RFC-0116 through RFC-0120 works over
concrete, closed rows.

---

## Motivation

RFC-0116's records are exact shapes and RFC-0118's bounds are predicates over a type. Neither
lets a function say "I take a record that has `x`, and I give you back whatever else it had."
Every generic helper over record shape — the reusable half of what Rust's view types set out
to solve — needs a name for the unknown remainder.

The typestate application is the more striking one: with a row-typed record, **the state *is*
the row**, and RFC-0036's conditional impl blocks generalize from aspect conditions to
row-shape conditions with no new dispatch mechanism.

---

## 1. `row` declares, `..` marks every use

```metel
fun get_x<row R>(p: { x: f64, ..R }) -> f64 { p.x }
```

A row variable is written `..R` **wherever it appears in a type** — `{ x: f64, ..R }`,
`Handle.{ ..R }`, `Session<..R>`. A bare identifier in type position is therefore always a
*type* variable, never a row.

**The binder keeps `row R`.** A declaration naming its own kind is ordinary (Rust's
`const N: usize` does exactly this, then uses bare `N`), and `<..R>` would read as splicing
into the parameter list rather than declaring.

**The forcing case was a genuine ambiguity, not a preference.** Inside projection braces a
bare identifier could be either a field label or a row variable — `Handle.{ fd }` projects a
field, `Handle.{ R }` a row — separated only by case convention, which would have made the
design depend on RFC-0101 (`0-draft`) to disambiguate.

`..` with no name is the anonymous form and is what makes a bound open (RFC-0118 §1); `..R`
is the same mechanism with the rest named.

## 2. Row algebra: extension is a literal, removal is a decomposition

**Extension needs no operator.** The new label goes in the row literal, exactly as PureScript
(`{ x :: Int | r }`), Koka (`<div|e>`) and OCaml (`< x : int; .. >`) all do it:

```metel
RequestBuilder<{ ..R, auth: String }>
```

**Removal has no literal form and gets a decomposition instead of a subtraction.** Name both
halves and state how they compose:

```metel
impl<row R, row Rest> Session<..R>
where R = { token: Token, ..Rest }
{
    fun authenticate(self) -> Session<..Rest> { ... }
}
```

`Rest` *is* `R` with `token` removed, because the equation says so. This follows PureScript's
`Prim.Row.Cons label typ tail row` — which means exactly `row = (label :: typ | tail)`, and
which types `Record.delete` by using it backwards — rather than Ur/Web's `--` operator.

Three things this buys beyond parsing: the equation **subsumes the bound** (it already
implies `R: { token: Token, .. }` and additionally names the remainder); `=` is the correct
separator because it *equates* two rows, matching `assoc_binding` (`Deref<Target = Node>`),
an equation already living in this channel; and **no label kind or label literal is
required**, unlike any operator-based design.

**The cost, and the condition to revisit.** It is verbose — every removal needs a second row
variable and a `where` clause. If row arithmetic ever appears in more than a handful of
places, an operator starts to look better. Weigh that against the one direct experiment:
**Elm shipped record extension and restriction and then withdrew both**, keeping only update
and open-row annotations, on complexity-versus-benefit grounds. (Recalled, not verified —
confirm before citing as precedent.)

## 3. Typestate via row-conditional impls

```metel
impl<row R, row Rest> Session<..R> where R = { token: Token, ..Rest } {
    fun authenticate(self) -> Session<..Rest> { ... }
}

impl<row R: !{ token: _ }> Session<..R> {
    fun send_data(&self, bytes: Bytes) { ... }
}
```

`send_data` does not *exist* on a `Session` whose row still has `token` — not a runtime
precondition, an absent method. Calling it too early is the same class of error as calling a
method that was never defined.

**Where this is compelling:** protocol and session state machines, where each transition adds
or removes a marker field and the available API tracks it exactly; and builders in the dual
direction, where `.with_timeout()` requiring `R: !{ timeout: _ }` prevents setting the same
field twice at compile time.

**This is one of two competing typestate encodings and which is canonical is undecided.**
`brand-types.md` does typestate with a phantom type parameter — `File<'b, Open>` — which is
simpler and well-precedented. Making the row-conditional form canonical pulls open-row
generics, row-conditional coherence and §4's width-subtyping rule onto the critical path,
which is a point in the phantom form's favour, though not treated as decisive.

## 4. Costs, stated as costs

- **Row-kinded variables and row unification** are a genuinely new piece of the
  elaborator/inference system, not a small patch. This RFC is the only place in the cluster
  that needs them.
- **Width subtyping versus ownership — the genuinely novel problem.** Row polymorphism's
  defining move (silently using a wider record where a narrower is expected, forgetting the
  extra fields) is harmless in garbage-collected OCaml, Elm and PureScript. None of them
  have affine or linear ownership, so none had to ask what happens when a forgotten field
  is not garbage. **Proposed rule:** width subtyping is sound only when every
  silently-dropped field is `Copy`; anything with a drop obligation forces explicit
  handling. Not decided — this is the piece with no precedent to lean on at all.
- **Monomorphization versus erasure.** Storage-transparent constructs elsewhere in this
  cluster monomorphize and erase at runtime. PureScript's row polymorphism typically
  compiles to runtime dictionary passing. A zero-cost row-polymorphic Metel would be its
  own implementation project.
- **Plain-record style over object style.** Metel's aspects already cover
  interface-with-methods polymorphism; an OCaml-object-style structural mechanism for the
  same job would be redundant.

---

## Open Questions

1. **The width-subtyping-requires-`Copy` rule is proposed with no precedent to verify it
   against, and not ratified.** Until it is, open records whose non-empty remainder is
   silently discarded should be rejected outright. *(From RFC-0090 OQ3.)*
   **The half of this that was "no bound expressing 'every field in row `R` is `Copy`' is
   defined anywhere" is now RFC-0123 (Field-Wise Row Constraints), opened 2026-07-24.**
   That construct turned out to be needed identically by RFC-0116 — an anonymous record
   cannot satisfy *any* stdlib aspect, including `Display`, without it — so the two were
   being tracked as unrelated problems in different documents when they are one missing
   feature. What remains here is the rule itself: *whether* `Copy` is the right predicate
   for sound width subtyping, which stays open independently of being able to write it.
2. **Row-conditional impl coherence.** Extending RFC-0036/RFC-0060's conditional-impl
   checking to row-shape conditions — ensuring two impls, one gated on presence and one on
   absence, cannot both apply to an under-constrained row variable — is asserted tractable
   and not worked out. *(From RFC-0090 OQ4.)*
3. **Diagnostics.** "Method does not exist" is a much worse error than "method requires the
   row to contain `token`, but this session's row is `{ tcp_connected }`". The legible
   version is not automatic just because the mechanism works. *(From RFC-0090 §4.)*
4. **Phantom-parameter versus row-conditional typestate — which is canonical, or do both
   stay, and for which cases?** Too early to decide. *(From RFC-0090 OQ5.)*
5. **Grammar work, none of it written.** `<..R>` must be accepted as a generic *argument*
   while `<row R>` remains the *parameter* form; a row body needs a `..`/`..R` tail
   alternative; `where_constraint` needs the `row_equation` alternative §2 requires
   (`where_constraint = { row_equation | ident ~ ":" ~ bound_list }`,
   `row_equation = { ident ~ "=" ~ type_expr }`). The `range_op = { "..=" | ".." }`
   collision was checked and is clean — `range_expr` requires a left operand, so no prefix
   `..` exists in expression position. Grammar reading, not a prototype. *(From RFC-0090
   OQ12.)*
6. **Label polymorphism is not in scope here and may be wanted.** Being generic over *which
   label*, not just over the rest — `drain_field<row R, name, T>` — needs a label kind, a
   label literal, an index-by-label form, and rules for all three. §2's decomposition
   retires the need for a label *literal*, not for label *polymorphism*. Tracked against
   the deferred RFC-0091, where the one construct needing it lives.

---

## References

- `internal/rfcs/5-superseded/rfc-0090-structural-records.md` §2 (open half), §3 step 2,
  §4 (typestate), §7 (costs) — the source
- RFC-0118 (Row Bounds) — the anonymous `..`, of which `..R` is the named form
- RFC-0120 (Named Records) — the tier that makes row-conditional impls resolvable at all
- RFC-0036 (Conditional Impl Blocks) — what §3's row-conditional impls generalize
- RFC-0060 (Aspect Impl Coherence), RFC-0061 (Structural Aspect Bounds) — the coherence
  checking OQ2 must extend
- `reports/substructural-types/brand-types.md` — the phantom-parameter typestate
  alternative in §3 and OQ4
- `reports/substructural-types/access-and-presence-rows.md` §4 — Koka effect rows, and why
  effect rows and field rows are the same open-row shape

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
