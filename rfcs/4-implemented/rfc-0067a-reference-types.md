---
id: rfc-0067a
title: "Reference Types"
date: '2026-06-28'
updated: '2026-07-11'
status: implemented
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/236'
impl_status: implemented
---

> **Status — accepted.** Split 2026-07-07 from the original RFC-0067 ("Reference Types"),
> which bundled a syntax rename with two genuinely separate concerns: lifetime anchors
> (borrow-checker core) and allocator-pointer (`@a T`) interaction. This RFC keeps only the
> allocator/anchor-independent slice — `&T` / `&var T` replacing `*T` / `*mut T`, and
> auto-deref. It has no dependency on affine types, the borrow checker, or allocators, and
> is accordingly accepted and sequenced into Cluster A (see
> `reports/implementation/roadmap-2026-07-07.md`, Phase 1) rather than Phase 3.
>
> **Amended 2026-07-10, while integrating into the spec.** §3a added: this RFC's original
> text claimed "no explicit dereference operator in safe code — all access goes through
> auto-deref," then specified auto-deref only for field access, method dispatch, and
> reference-to-reference coercion — none of which cover reading a plain value out of a
> reference with no field/method/operator involved (`let y: i64 = r;` where `r: &i64`),
> which the spec's own pre-existing pointer example did via explicit `*p` (`*q = *p + 1;`).
> Removing `*` with nothing specified for this case was an oversight, caught while writing
> the worked examples `3-integrated` requires, not a deliberate omission.
>
> The remaining scope of the original RFC-0067 — lifetime anchors (`&r T`, `<&r>`
> declarations, ordering bounds), allocator-pointer auto-deref/coercion, and move-out from
> `@a T` — stays at `public/rfcs/1-under-review/rfc-0067-lifetime-anchors.md` under the
> same number, since every existing cross-reference to "RFC-0067" in the allocator-cluster
> RFCs (0063/0065/0066/0068/0077) already refers to that anchor/allocator content
> specifically, not to this rename. Supersedes RFC-0043 (Regular Pointers). Amends RFC-0044
> (Explicit Receiver Semantics).

> **Status — integrated (2026-07-10).** Integrated into public/reference/spec/types.md and expressions.md: &T/&mut T reference types replace *T/*mut T, auto-deref, and a new type-directed value-copy-out rule resolving a gap found while writing worked examples (RFC amended, see its own status note).

> **Amended 2026-07-11, after implementation (issue #236).** §3a's own text named only
> `let`/`mut` bindings and explicit ascription as read-copy sites — implementing it
> surfaced that the same rule also has to fire at `return`, `break`, and (since a
> function/method/closure body, an `if`/`else` branch, and a `match` arm all resolve
> against a declared/expected type the same way a `let` binding does) any tail
> expression, or the RFC's own worked pattern — `fun f() -> i64 { ...; p }` with no
> explicit `return` — would be a hole in its own rule. §3a's text and worked example
> updated to state this. Separately, §3's existing chain-depth guarantee ("a `&&T` will
> deref through both levels if needed") turned out to need making explicit that it
> covers read-copy and write-through too, not only field access/method dispatch/
> reference-coercion — the first implementation only peeled one layer for each of the
> three new mechanisms (read-copy, write-through, and — found only because a regression
> test exercised it — the pre-existing method-dispatch/field-access auto-deref itself,
> whose own `deref_value`/receiver-resolution helpers turned out to only follow one
> layer at runtime despite the type-checking side already being fully recursive) —
> each needed a dedicated fix once a `&&T`/`&var &var T`-shaped test caught it.

> **Status — implemented (2026-07-11).**

## Summary

Replace Metel's `*T` / `*mut T` pointer model (RFC-0043) with **reference types**: `&T`
(shared immutable) and `&var T` (exclusive mutable). Remove the explicit `*p` dereference
operator — all value access is through auto-deref.

This RFC does not include lifetime anchors (`&r T`) or any allocator-pointer (`@a T`)
interaction — see the remaining RFC-0067 for both.

---

## Motivation

RFC-0043 uses `&x` / `&var x` at the expression level to produce values of type `*T` /
`*mut T` — the sigil changes between expression position (`&`) and type position (`*`).
This asymmetry is easy to typo around and gives address-of and its resulting type no visible
relationship in source text.

Renaming the type-position sigil to match — `&T` / `&var T` — removes that asymmetry outright,
and does so independently of anything else: it does not require lifetime anchors, allocators,
or the borrow checker to be useful on its own. Two further benefits fall out immediately:

- **Auto-deref removes boilerplate today**, not just once allocators exist. `r.field` instead
  of `(*r).field`, `r.method(args)` instead of `(*r).method(args)`.
- **It sets up the anchor syntax without a second rename.** RFC-0065's elision rules already
  treat the anchor on a borrow as normally elided — so `&T` written under this RFC alone is
  the exact same surface syntax `&T` will still be once the remaining RFC-0067 adds anchor
  tracking behind it in Phase 3. There is no `*T` → `&T` → `&r T` two-step migration; only
  `&T` → (anchor inferred silently) `&r T`.

---

## 1. Reference types

Metel has two reference types:

```metel
&T       // shared immutable reference
&var T   // exclusive mutable reference
```

These replace `*T` and `*mut T` from RFC-0043. Semantics are unchanged: both are non-owning
aliases. `&T` allows multiple simultaneous readers; `&var T` is exclusive — no other reference
to the same location may exist while it is live. (Precise enforcement of exclusivity is the
borrow checker's job, Phase 3, same as it was under RFC-0043 — this RFC changes notation, not
enforcement.)

`&var T` coerces to `&T` implicitly. No other reference coercion is implicit.

---

## 2. Address-of

The address-of operators `&` and `&var` are syntactically unchanged at the expression level:

```metel
let x = 42;
let r: &i64     = &x;      // shared reference to x
var y = 42;
let m: &var i64 = &var y;  // exclusive reference to y
```

Addressability rules from RFC-0043 §5 are preserved: only stable lvalues (named bindings,
fields, array elements, and chains thereof) may be addressed. Temporaries cannot.

---

## 3. Auto-deref

There is no explicit dereference operator in safe code. All access goes through auto-deref:

1. **Field access** — `r.field` where `r: &T` dereferences to access `T.field`.
2. **Method dispatch** — `r.method(args)` inserts the borrow required by the method's
   receiver.
3. **Deref coercions** — `&T` or `&var T` coerces to a less-capable reference when the
   expected type requires it.

Auto-deref chains: a `&&T` will deref through both levels if needed. Chain depth is bounded by
the type structure; no infinite cycles are possible. This applies uniformly to all three
rules above, and to §3a's read-copy and write-through below — none of these are a
single-layer special case; `let x: i64 = rr;` where `rr: &&i64` copies through both
layers, the same as `rr.field` would auto-deref through both to reach a struct.

Auto-deref through an allocator pointer (`@a T`) is specified separately in the remaining
RFC-0067 §2 (Allocator pointer access), since it requires `@a T` to exist (RFC-0063).

---

## 3a. Reading a value out of a reference

None of §3's three auto-deref rules cover the base case: no field, no method, no
reference-to-reference coercion — just wanting the plain value a reference points to,
the way the pre-existing spec example did with explicit `*p` (`*q = *p + 1;`). References
are non-owning aliases (§1), so a value can never be *moved* out of one — only *copied*,
and only when the referent's type actually permits copying.

**Resolution: type-directed copy, the same pattern RFC-0066 §3a already established for
allocator move-out, not a new mechanism.** A `let` binding whose own declared type `T`
differs from its initializer's reference type (`&T` or `&var T`) copies the referent,
provided `T: Copy`:

```metel
let x = 42;
let r: &i64 = &x;
let y: i64 = r;   // type-directed copy — r's type differs from y's declared type
```

**This fires at every position where a declared or expected type is already known, not
only `let`/`mut` bindings and explicit ascription** — the same test that applies to a
`let` binding's own declared type applies equally to a `return` value against the
enclosing function's declared return type, a `break` value against the enclosing
`loop`'s inferred type, and — since a function/method/closure body, an `if`/`else`
branch, and a `match` arm all resolve their result against a declared or expected type
the exact same way a `let` binding does — any tail expression in one of those positions:

```metel
fun bump(p: &var i64) -> i64 {
    p += 1;
    p          // tail expression, no explicit `return` — copies out of p
}

fun read(p: &var i64) -> i64 {
    return p;  // same rule at `return`
}
```

It never fires silently at a plain call site. `fun f(v: i64)` called as `f(r)` where
`r: &i64` is a type error, not an implicit copy: the argument position has no
declared-type-of-its-own for the rule to compare against, the same reason RFC-0066
§3a's extraction never fires implicitly at a plain-parameter call site either. Type
ascription (`r: T`) fires the copy in any expression position, including call sites,
matching RFC-0066 §3's two forms exactly:

```metel
let copy = r: i64;        // ascription in expression position
process(r: i64);          // ascription at call site
```

Chains through multiple reference layers the same way §3's auto-deref does — reaching
the declared type may require copying out of more than one layer:

```metel
let n = 42;
let r: &i64 = &n;
let rr: &&i64 = &r;
let x: i64 = rr;   // copies through both layers of the chain
```

**The `T: Copy` gate depends on RFC-0071, itself accepted but not yet integrated or
implemented.** Until RFC-0071's affine/Copy model lands, the current interpreter has no
move semantics at all (everything is deep-cloned on bind), so this rule applies
universally today — every type behaves as `Copy` in the present implementation. Once
RFC-0071 is integrated, the gate becomes real: a non-`Copy` `T` cannot be produced this
way, and code must go through `.clone()` or an owning path instead.

---

## 4. Supersession of RFC-0043

| RFC-0043 | This RFC |
|----------|----------|
| `*T` | `&T` |
| `*mut T` | `&var T` |
| `&x` → `*T` | `&x` → `&T` |
| `&var x` → `*mut T` | `&var x` → `&var T` |
| `*p` explicit dereference | removed; auto-deref only |
| `*mut T` coerces to `*T` | `&var T` coerces to `&T` |

RFC-0043 §6 (auto-deref for field access, method calls) is preserved. RFC-0043 §8 (no pointer
arithmetic) carries over unchanged. Nullability via `Perhaps<*T>` becomes `Perhaps<&T>`.

---

## Unresolved questions

None.

**Closed — auto-deref chain depth.** The compiler follows the deref chain until it reaches the
expected type, with no explicit depth limit. Chain bounded by type structure.

---

## References

- RFC-0043 (Regular Pointers) — superseded by this RFC.
- RFC-0044 (Explicit Receiver Semantics) — `&self` / `&var self` receivers are now consistent
  with `&T` / `&var T` as general reference types.
- RFC-0067 (the remaining document, now `1-under-review/`) — lifetime anchors (`&r T`, `<&r>`
  declarations, ordering bounds), allocator-pointer auto-deref/coercion, and move-out from
  `@a T`. Builds directly on this RFC's `&T` / `&var T` without changing their syntax.
- `reports/implementation/roadmap-2026-07-07.md` — Phase 1 (Cluster A) placement of this RFC,
  versus Phase 3 for the remaining RFC-0067.
