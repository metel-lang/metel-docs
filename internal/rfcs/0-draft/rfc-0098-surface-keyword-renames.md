---
id: rfc-0098
title: "Surface Keyword Renames"
date: '2026-07-13'
status: draft
target:
---

## Summary

Three independent, purely lexical syntax renames with zero semantic impact: impl-block spelling (`extend X with Y`), `pub` → `public`, and `mut` → `var` (bindings, reference types, and reference expressions all together). Amends RFC-0032, RFC-0042, RFC-0044, and RFC-0067A's surface syntax only — no semantics, AST shape, or type-system behavior from any of the four changes.

---

## Motivation

Metel already diverges from Rust's naming where it costs nothing — `aspect` not `trait`, `Perhaps<T>` not `Option<T>`, `and`/`or` not `&&`/`||` — and it reads as a deliberate identity rather than an accident of copying Rust's grammar. Three more spots are pure keyword-level Rust tells with zero semantic weight: the `impl X for Y` block shape, the `pub` keyword, and the `mut` keyword (in binding, reference-type, and reference-expression position alike). Fixing them is as cheap as any change to a shipped grammar gets — but "cheap to change" and "small in scope" turned out to be different things here: `mut` and `pub` are each the normative spelling in four already-implemented RFCs, not incidental syntax nobody's committed to. This RFC's job is to rename the token everywhere it appears while explicitly leaving each amended RFC's actual semantics — mutability rules, reference/auto-deref behavior, receiver dispatch, field-visibility enforcement — completely alone.

---

## 1. Impl-block spelling

Today:
```metel
impl Container for IntBox {
    type Item = i64;
    fun get(&self) -> i64 { return self.value; }
}
```

Proposed:
```metel
extend IntBox with Container {
    type Item = i64;
    fun get(&self) -> i64 { return self.value; }
}
```

Grammar change is contained entirely to `impl_block`'s two keyword tokens and their order (target first, aspect second, matching the new preposition) — `ast::ImplBlock`'s fields (`target_type`, `aspect_name`, `polarity`, `generics`, `where_clause`, `assoc_type_defs`, etc.) are unchanged, only what `parser::parse_impl_block` matches against. Negative impls (RFC-0081) follow the same reordering: `impl !Aspect for Type` becomes `extend Type without Aspect`.

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

---

## Alternatives Considered

- **Go-style capitalization instead of `public`**: no keyword at all, capitalization of the identifier itself signals visibility. Rejected for this RFC as a bigger lexer-level change than a token rename, and it would need its own RFC amending RFC-0032 far more invasively than a rename does; worth pursuing separately if desired.
- **Keeping any one of the three as Rust's spelling**: each of the three sections in this RFC is independently reversible and doesn't block the other two — a narrower version of this RFC accepting only a subset is a legitimate outcome of review, not a reason to split into three separate RFCs up front (unlike RFC B/C from the surface-syntax discussion this RFC grew out of, these three don't each carry their own unresolved design question — see "Unresolved Questions" below).

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
- RFC-0081 (Negative Impls) — impl-block reordering (§1) must account for `!`-prefixed negative impls too (`extend Type without Aspect`).
- RFC-0034 (Struct-Enum-Aspect Bounds) — `aspect`'s own naming precedent this RFC continues in spirit.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
