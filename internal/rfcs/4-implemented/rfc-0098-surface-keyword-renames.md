---
id: rfc-0098
title: "Surface Keyword Renames"
date: '2026-07-13'
status: implemented
target:
updated: '2026-07-14'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/pulls/273'
impl_status: implemented
---

> **Status — accepted (2026-07-14).** Reviewed and revised: extend Type / extend Type: Aspect (Swift-precedent, settles the inherent-impl gap an earlier with/without draft left open), negative impls folded into the same clause via the existing bound-negation !, identifier-collision audit noted for implementation. No open questions block it.

> **Status — integrated (2026-07-14).** Integrated into spec: `public`/`var`/`extend` surface keyword renames

> **Status — implemented (2026-07-14).**

## Summary

Three independent, purely lexical syntax renames with zero semantic impact: impl-block spelling (`extend Type` / `extend Type: Aspect`), `pub` → `public`, and `mut` → `var` (bindings, reference types, and reference expressions all together). Amends RFC-0032, RFC-0042, RFC-0044, and RFC-0067A's surface syntax only — no semantics, AST shape, or type-system behavior from any of the four changes.

---

## Motivation

Metel already diverges from Rust's naming where it costs nothing — `aspect` not `trait`, `Perhaps<T>` not `Option<T>`, `and`/`or` not `&&`/`||` — and it reads as a deliberate identity rather than an accident of copying Rust's grammar. Three more spots are pure keyword-level Rust tells with zero semantic weight: the `impl X for Y` block shape, the `pub` keyword, and the `mut` keyword (in binding, reference-type, and reference-expression position alike). Fixing them is as cheap as any change to a shipped grammar gets — but "cheap to change" and "small in scope" turned out to be different things here: `mut` and `pub` are each the normative spelling in four already-implemented RFCs, not incidental syntax nobody's committed to. This RFC's job is to rename the token everywhere it appears while explicitly leaving each amended RFC's actual semantics — mutability rules, reference/auto-deref behavior, receiver dispatch, field-visibility enforcement — completely alone.

---

## 1. Impl-block spelling

Today, an impl block has two shapes — inherent (no aspect at all) and
aspect-implementing (`for`, aspect named first):

```metel
impl IntBox {
    fun new(value: i64) -> IntBox { return IntBox { value }; }
}

impl Container for IntBox {
    type Item = i64;
    fun get(&self) -> i64 { return self.value; }
}
```

Proposed: `impl` renames to `extend`, and the aspect-implementing form reorders
target-first with a trailing `: Aspect` clause — mirroring Swift's `extension
Type` / `extension Type: ProtocolName`, the closest existing precedent for "one
construct, target named first, an optional trailing conformance clause" (a
survey of Rust/Haskell/TypeScript/Kotlin/C#/Elixir/Go found no language that
invents a *separate* keyword just for the aspectless case; the ones with a
genuinely separate impl-block construct at all — Rust, Swift — both use one
keyword with an optional clause):

```metel
extend IntBox {
    fun new(value: i64) -> IntBox { return IntBox { value }; }
}

extend IntBox: Container {
    type Item = i64;
    fun get(&self) -> i64 { return self.value; }
}
```

The inherent form is simply the `: Aspect` clause omitted — exactly mirroring
`impl_block`'s existing `(named_type ~ "for")?` optionality today, not a new
rule. This matters more than it looks: inherent impls are not a peripheral
case — they're roughly as common as aspect impls in `stdlib/core.mtl` itself
(`impl List<T> { ... }`, `impl Perhaps<T> { ... }`, `impl Result<T, E> { ... }`,
`impl OsError { ... }`, and so on), so any spelling that required *something*
after the target on every impl would touch the majority of the existing
codebase's impl blocks, not just the minority that implement an aspect.

Grammar change is contained to `impl_block`'s keyword and clause order — target
first, then an optional `: Aspect` clause — `ast::ImplBlock`'s fields
(`target_type`, `aspect_name`, `polarity`, `generics`, `where_clause`,
`assoc_type_defs`, etc.) are unchanged, only what `parser::parse_impl_block`
matches against. Generic params keep their existing position, immediately
after the introducing keyword (unchanged from `impl`'s own slot today):

```metel
extend<T: Comparable + Printable> SortedList<T>: Printable {
    fun print(self) -> String { ... }
}
```

Negative impls (RFC-0081) do **not** get their own keyword. Folding them into
the same `: Aspect` clause via the `!` prefix already used for bound negation
(`T: !Copy`) means `!` consistently spells "negative" everywhere it appears in
an impl, rather than introducing a fourth new keyword (`without`) for a single
case — an earlier draft of this RFC proposed exactly that and was walked back
during review:

```metel
extend Type: !Aspect { }
```

Bare-parameter blanket impls (RFC-0097) are unaffected beyond the token
rename — the target is simply the impl's own generic parameter, named
wherever any other target would be:

```metel
extend<T: Copy> T: Clone {
    fun clone(self: &T) -> T { *self }
}
```

The net new keyword surface for this section is `extend` alone — the
colon and `!` are both already-established tokens elsewhere in the grammar
(field/param type annotations and generic bounds use `:`; bound negation
already uses `!`), not new syntax invented for this RFC.

No existing RFC specifies `impl X for Y` as its own subject — every RFC that uses the shape (RFC-0060, RFC-0072, RFC-0081, RFC-0082, and others) does so incidentally, as the pre-existing syntax for a different feature. This section doesn't amend any of them individually; it's a pure token/ordering change underneath all of them at once.

---

## 2. Visibility keyword: `pub` → `public`

Today: `pub struct IntBox { ... }`, `pub fun get(...)`, and, per RFC-0032, `pub` on individual struct fields:
```metel
pub struct Token {
    pub value: String,
    secret: String,
}
```

Proposed:
```metel
public struct Token {
    public value: String,
    secret: String,
}
```

A straight token rename (`pub_kw` in the grammar becomes `public_kw`) — no positional change, no change to RFC-0032's actual visibility semantics (module-private-by-default fields, explicit-annotation-to-expose, the constructibility rule for a `pub struct` with private fields). **Amends RFC-0032**'s surface syntax only.

---

## 3. Mutability keyword: `mut` → `var` (all positions)

`mut` retires as a token everywhere in the grammar, not just in `let` position — bindings, reference types, and reference expressions all use the same keyword, so per RFC-0042's own stated design goal (keeping `mut` "consistently modifier-like" across every position it appears), they change together:

```metel
// binding (RFC-0042)
let x = 5;
var y = 5;                        // was: let mut y = 5;

// reference types (RFC-0067A) and receivers (RFC-0044)
fun get(&self) -> i64 { ... }
fun bump(&var self) { ... }       // was: &mut self
let r: &var i64 = &var x;         // was: &mut i64 / &mut x

// reference expressions (unary &, RFC-0067A §2)
let p = &var value;               // was: &mut value

// for-loop / for-in mutable bindings (RFC-0042)
for (var i = 0; i < 10; i += 1) { ... }        // was: for (let mut i = 0; ...)
for (var item in items) { item = normalize(item); }  // was: for (let mut item in items)
```

Grammar sites affected, all a straight token substitution (`mut_kw` → `var_kw`, no restructuring): the `let`/for-loop/for-in binding forms (RFC-0042's `BindingDeclaration`/`ForInit`/`ForInStatement` productions), `mut_reference_type` (`&mut T` → `&var T`, RFC-0067A §1/§4), `param`'s self-receiver alternative (`&mut self` → `&var self`, RFC-0044), and `unary_expr`'s reference-taking alternative (`&mut expr` → `&var expr`, RFC-0067A §2).

**Amends RFC-0042, RFC-0044, and RFC-0067A's surface syntax only.** Specifically untouched by this section:

- RFC-0042's mutability semantics (immutable-cannot-reassign, mutable-can-reassign, mandatory initialization, shadowing rules) and its D1/D2/D3 resolved decisions (standalone `mut` already dropped; mutable for-in bindings; the parser's internal AST-node choice).
- RFC-0067A's entire auto-deref/read-copy/write-through machinery (§3, §3a), chain-depth guarantee, `&mut T` → `&T` coercion rule, and its dependency on RFC-0071's `Copy` gate — none of this changes meaning, only how the exclusive-reference type is spelled.
- RFC-0044's three receiver forms and their dispatch semantics (`self` value receiver, `&self` shared reference, `&mut self` → `&var self` exclusive reference) — the distinction these three forms encode is unchanged, only the third one's spelling.

RFC-0033 (Field-Level Mutability) is still `0-draft` and uses a bare `mut field` sketch in its own examples; since it hasn't been accepted, this RFC doesn't formally amend it, but whoever picks RFC-0033 back up should spell its `mut` as `var` from the start rather than drafting against a token this RFC retires.

**Identifier collision audit, resolved at implementation time:** reserving `var` as a keyword collided with the existing stdlib item `std::env::var`. The shipped implementation renamed that function to `std::env::get`; the same audit should still be applied to any future surface-keyword additions (`public`, `extend`, and later RFCs) rather than assumed clean.

---

## Alternatives Considered

- **Go-style capitalization instead of `public`**: no keyword at all, capitalization of the identifier itself signals visibility. Rejected for this RFC as a bigger lexer-level change than a token rename, and it would need its own RFC amending RFC-0032 far more invasively than a rename does; worth pursuing separately if desired.
- **Keeping any one of the three as Rust's spelling**: each of the three sections in this RFC is independently reversible and doesn't block the other two — a narrower version of this RFC accepting only a subset is a legitimate outcome of review, not a reason to split into three separate RFCs up front (unlike RFC B/C from the surface-syntax discussion this RFC grew out of, these three don't each carry their own unresolved design question — see "Unresolved Questions" below).
- **`extend Type with Aspect` / `extend Type without Aspect`**: an earlier draft of §1 used `with` for aspect conformance and a separate `without` keyword for negative impls. Rejected during review on two grounds: it left the inherent (aspectless) form completely unspecified — every worked example showed the `with`-clause form, with no indication whether a bare `extend Type { }` was even legal, despite inherent impls being roughly as common as aspect impls in the existing codebase — and `without` was a fourth new keyword spent on a single case that the existing `!` bound-negation token already covers for free.
- **Two distinct keywords, `impl` for inherent + `extend` for aspect conformance**: keeps `impl Type { }` completely unchanged and reserves `extend` only for `extend Type: Aspect { }`, drawing a real semantic line between "defining a type's own methods" and "extending it with a capability from outside." Not chosen: it doubles the impl-introducing keyword surface for a distinction the grammar doesn't otherwise need to make (both forms produce the same `ast::ImplBlock`, differing only in whether `aspect_name` is `None`), and no clear precedent language draws this line at the keyword level either (Rust and Swift both use one keyword for both forms).

---

## Unresolved Questions

None load-bearing. Each of the three sections is independently reversible; none blocks the other two or any other in-flight RFC. RFC-0033's own eventual `mut`-vs-`var` spelling (noted in §3) is a forward pointer for whoever resumes that RFC, not an open question this RFC needs to resolve itself.

---

## References

- RFC-0032 (Field-Level Visibility) — amended, §2 (`pub` → `public` on struct fields).
- RFC-0042 (`let mut` for Mutable Bindings) — amended, §3 (binding-position `mut` → `var`).
- RFC-0044 (Explicit Receiver Semantics) — amended, §3 (`&mut self` → `&var self`).
- RFC-0067A (Reference Types) — amended, §3 (`&mut T` reference type and `&mut expr` address-of → `&var`).
- RFC-0033 (Field-Level Mutability, draft) — not amended (not yet accepted), but should adopt `var` rather than `mut` when resumed.
- RFC-0081 (Negative Impls) — impl-block reordering (§1) folds `!`-prefixed negative impls into the same `: Aspect` clause (`extend Type: !Aspect`), reusing the existing bound-negation token rather than adding a `without` keyword.
- RFC-0034 (Struct-Enum-Aspect Bounds) — `aspect`'s own naming precedent this RFC continues in spirit.
- RFC-0101 (Grammar-Enforced Naming Case Conventions) — reviewed alongside this RFC; no conflict — `extend`, `public`, and `var` are all lowercase, consistent with that RFC's non-type casing category.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
