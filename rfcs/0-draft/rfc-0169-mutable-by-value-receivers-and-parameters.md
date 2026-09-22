---
id: rfc-0169
title: "Mutable-By-Value Receivers and Parameters"
date: '2026-09-22'
status: draft
---

> **Opened 2026-09-22, as a dependency of RFC-0161 (Callable Object Contract).**
> RFC-0161's `Callable` marker derivation for a user-written by-value `call` impl
> needs a *written* distinction between "receives its value and only reads it"
> and "receives its value and mutates its own copy" — the same distinction
> RFC-0044 already gives `&self` / `&var self` for reference receivers, but never
> extended to the by-value case. Split out as a general surface feature rather
> than folded into RFC-0161, because nothing about it is specific to `Callable`.

## Summary

A fourth receiver form, `var self`, and its ordinary-parameter counterpart, `var
name: T`: a by-value receiver or parameter that owns its value (exactly as `self` /
`name: T` do today) and may additionally reassign it in the body, without an
opening `var name := name;` rebind. This is sugar, not a new capability — a `var`
parameter behaves exactly as if the body opened with that rebind — and it reuses
the existing `var` keyword rather than introducing new vocabulary, the same
reasoning RFC-0033 gives for reusing `let` on fields.

## Motivation

### The gap today

Metel has `let` and `var` for local bindings, but a function or method parameter
is always `let`-shaped: reassigning it requires an explicit rebind.

```metel
fun bump(n: i64) -> i64 {
    var n := n;   // required before `n` can be reassigned
    n = n + 1;
    n
}
```

`fun bump(var n: i64) -> i64 { n = n + 1; n }` is a parse error today (verified
against the current interpreter). The same gap exists for the by-value `self`
receiver: `extend Counter { fun step(var self) -> Counter { self.n = self.n + 1;
self } }` does not parse either, only `&var self` does.

### Three independent reasons this needs to exist

1. **RFC-0161 needs it, at the signature.** A `Callable` impl's by-value `call`
   method — the `once` case, the one that consumes its receiver — may or may not
   mutate its own (uniquely owned) copy before returning. Whether it does changes
   nothing observable to a caller, since the value was consumed either way, but it
   is exactly the distinction the closure model already makes explicit and
   *written* (`once` vs `once var`, RFC-0134/RFC-0153) rather than inferred from
   the body. Without this RFC, every by-value receiver looks identical at the
   signature, and RFC-0161's marker derivation (its open question 7) has no way
   to read the distinction without inspecting the body — which the closure model
   deliberately avoids doing, for the reason §2 gives.
2. **RFC-0033 already assumes it exists.** RFC-0033 (Field-Level Mutability,
   still `0-draft`, opened 2026-05-30) writes `fun reconnect(var self) { self.retries
   += 1; }` as ordinary, already-legal syntax. It predates the closure cluster's
   `var`-keyword decision (RFC-0153, 2026-09-01) and was never corrected — a
   second, independent signal that the language has wanted this since before this
   RFC existed.
3. **Ordinary ergonomics.** A function that wants to compute by mutating a local
   copy of a by-value argument writes a boilerplate rebind today, for no reason
   the type system enforces. Kotlin and Swift both allow a function parameter to
   be reassigned in the body without extra syntax (Kotlin's `var` parameters,
   Swift's parameters are `let` by default with explicit local `var` shadowing
   commonly elided by convention); this RFC gives Metel the Kotlin shape, spelled
   with the keyword Metel already uses for the same idea at binding level.

## Proposal

### Syntax

Extend the parameter grammar (today, `grammar.pest`):

```
param = { ("&" ~ mut_kw? ~ "self") | mut_kw? ~ "self" | mut_kw? ~ ident ~ (":" ~ type_expr)? }
```

(`mut_kw` is the grammar's existing internal name for the token spelled `var`,
the same rule `&var self` and a `var` local binding already use.) This adds:

```metel
fun bump(var n: i64) -> i64 { n = n + 1; n }

extend Counter: Callable<(), Counter> {
    fun call(var self) -> Counter { self.n = self.n + 1; self }
}
```

The receiver-form table (`declarations.md`, "Receiver Forms") gains a fourth row:

| Form | Meaning |
|---|---|
| `self` | value receiver |
| `var self` | value receiver, reassignable in the body |
| `&self` | shared reference receiver |
| `&var self` | mutable reference receiver |

Because `param` is the one grammar production every parameter list already goes
through (`fun_decl`, `aspect_method`, and the closure literal's own `param_list`
all reuse it), an ordinary function parameter, an aspect method parameter, and a
closure's own parameter all gain `var` under one grammar change, not three.
Whether closure parameters should have it is Open Question 1 below — the grammar
does not distinguish, so it is a scope decision, not an implementation cost.

### Semantics

`var self` and `var name: T` are exactly sugar for an opening rebind:

```metel
fun f(var x: T) -> U { BODY }
```

behaves identically to

```metel
fun f(x: T) -> U { var x := x; BODY }
```

and correspondingly for `var self`. This RFC defines no new runtime behavior: the
parameter is passed exactly as a plain `let`-shaped one is today (by move or by
copy, per the ordinary ownership rules for its type); `var` only changes whether
the body may reassign the name it is bound to.

**This never writes back to the caller.** `var self` and `var name: T` are
by-value forms; the caller's own storage, if any existed, is unaffected, exactly
as reassigning any other `var` local never affects what it was initialized from.
Write-back is what `&var self` / `&var T` are for, and this RFC changes nothing
about them.

**Type checking.** A `var` parameter is checked as the `var` local binding it
desugars to: ordinary use-after-move rules apply under `--move-check`, and
nothing about the parameter's declared type changes. There is no multiplicity or
`once`/`many` story here beyond what the type's own move semantics already give —
unlike a closure, a plain function has no repeated-call state to reason about.

### Interaction with RFC-0161

With this RFC, a `Callable` impl's by-value `call` can spell the distinction
RFC-0161 §1/§2 needs precisely:

```metel
extend Once: Callable<(), i64> {
    fun call(self) -> i64 { self.n }              // once, reading — no markers
}
extend OnceMut: Callable<(), i64> {
    fun call(var self) -> i64 { self.n = self.n + 1; self.n }   // once, mutating
}
```

matching the closure model's own `once` vs `once var` split. RFC-0161's marker
derivation (its open question 7) can then read the receiver form alone, the same
"written, not inferred" discipline the closure axes already follow — never
inspecting the body to decide a public capability.

### Interaction with object safety (RFC-0008)

`var self`, like plain `self`, is a by-value receiver: the value moves out from
behind a `dyn Aspect`. Whatever RFC-0008 amendment RFC-0161's open question 1
settles for a consuming `self` receiver should treat `var self` identically — one
carve-out, not two. This RFC does not itself amend RFC-0008; it only supplies the
surface syntax that amendment needs to distinguish.

### Interaction with the closure mutation axis

The `var` keyword already names two things: a reassignable local binding, and (as
`var` on a closure literal, RFC-0153) a closure whose own captured environment may
be mutated in place. This RFC adds a third, grammatically distinct use: a
reassignable-by-value parameter or receiver. The three do not interact — a
closure's `once`/`var` qualifiers describe the closure *value itself* and its
captured environment; a `var` on one of that closure's own parameters (if Open
Question 1 admits it) describes only that parameter, exactly as it would on an
ordinary function.

## Non-Goals

- **No change to ownership, move, or copy semantics.** A `var` parameter's type
  is checked exactly as a plain one's.
- **No write-back to the caller.** That is `&var self` / `&var T`, unchanged.
- **No object-safety decision.** RFC-0008's amendment (RFC-0161 open question 1)
  is out of scope here; this RFC only gives it precise syntax to reference.
- **No pattern-destructured `var` parameters** (`var (a, b): (i64, i64)`) —
  raised as Open Question 3, not decided here.
- **No change to `linear struct` receivers**, reserved by RFC-0044 for future
  work and untouched by this RFC.

## Alternatives Considered

- **Status quo: require an explicit rebind.** Rejected as RFC-0161's dependency:
  a rebind buried in the first line of the body is invisible at the signature, so
  a marker-derivation rule (or a reader) cannot see it without reading the body —
  exactly the inference the closure model already rejected for its own axes.
- **Infer mutability from the body**, as an alternative to writing `var`
  explicitly. Rejected for the same reason RFC-0134/RFC-0153 write closure axes
  explicitly rather than inferring them: a public capability (here, which marker
  RFC-0161 derives) would silently change whenever the body changes.
- **A new keyword instead of reusing `var`.** Rejected: `var` already means
  exactly this at binding level, and RFC-0033 gives the same reasoning for
  reusing `let` on fields — no new vocabulary for an idea the language already
  has a word for.

## Open Questions

1. **Closure parameters.** Does `|var y: i64| -> i64 { y = y + 1; y }` become
   legal? The grammar change admits it for free (§Syntax). Recommendation: yes,
   for consistency — a closure parameter is a parameter — but this needs an
   explicit decision rather than a side effect of the grammar edit.
2. **Lint for an unused `var`.** Should a `var self` / `var name: T` that the
   body never reassigns warn, analogous to any other dead-`var` style lint? Low
   priority; not blocking.
3. **Pattern-destructured `var` parameters.** Whether `var` composes with a
   destructuring parameter pattern is unresolved; raised as a Non-Goal above,
   listed here as future work rather than decided.

## References

- **RFC-0044 (Explicit Receiver Semantics, `4-implemented`)** — defines the three
  receiver forms this RFC extends to four; explicitly anticipates extension
  ("this RFC only requires that any future … model not silently reinterpret the
  three receiver forms defined here").
- **RFC-0033 (Field-Level Mutability, `0-draft`)** — already writes `var self` as
  if it exists; should reference this RFC once accepted.
- **RFC-0134 / RFC-0153 (Closure Call Capability / Closure Mutation Axis,
  `4-implemented`)** — the `var` keyword and the "written, not inferred" axis
  discipline this RFC follows for the by-value receiver case.
- **RFC-0161 (Callable Object Contract, `1-under-review`)** — the RFC this one
  unblocks; its open question 7 depends on this RFC's receiver form.
- **RFC-0008 (Aspect Objects, `4-implemented`)** — object safety; the by-value
  `self` amendment this RFC's `var self` shares, not settled here.

---

## Decision

**Outcome:** *(pending — `0-draft`, opened 2026-09-22. Written as a dependency of
RFC-0161; no tracking issue yet.)*
