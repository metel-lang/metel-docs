---
id: rfc-0068
title: "Struct-Owned Regions"
date: '2026-06-28'
---

> **Status — accepted.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), and RFC-0067 (Reference Types). Introduces owned region declarations on
> structs, giving the struct's arena the same lifetime as the struct itself and making that
> lifetime available as a type-level tag in method signatures.

## Summary

RFC-0063 establishes two region kinds: `@[Heap] T` (heap, indefinite lifetime) and scoped
`@[r] T` (arena, lifetime bounded by a `Region::scoped` closure). Both treat the region as
an *externally-owned* capability threaded through the bracket channel.

This RFC adds a third form: a struct may declare an **owned region** `[own r]` in its
bracket channel. The arena is created when the struct is constructed and freed when it is
dropped. The tag `r` is not a bracket argument — it is internal to the struct. Within `impl`
blocks, `r` is implicitly in scope and may be used to:

1. allocate values into the struct's arena (`@[r] expr`),
2. tag borrows as valid for the struct's entire lifetime (`&[r] T`, `&mut [r] T`),
3. name the struct's lifetime independently of any particular borrow of it.

---

## Motivation

The existing region forms do not provide a way to tie a region's lifetime to a struct's
lifetime. The two natural workarounds both have friction:

**`Region::scoped` around the struct.** The struct must be contained within the closure;
nothing tagged with the scoped region's tag can escape. This inverts ownership — the scope
owns the struct rather than the struct owning its arena.

**`struct Foo[r]` with external region.** The region is threaded in from the call site. The
struct cannot allocate into its own arena in methods that do not receive the handle, and the
caller must manage the arena's lifetime separately from the struct's.

The canonical motivating pattern is any structure that builds up arena-allocated data
incrementally — a parser constructing an AST, a request parser collecting headers, a query
planner building a plan graph. In all of these the arena's natural lifetime is the object's
lifetime, and the arena-allocated values' natural lifetime is "as long as this object is
alive."

---

## 1. Declaration

An owned region is declared with `own` in the bracket channel:

```metel
struct Parser[own r] {
    source: String,
    nodes:  @[r] List<AstNode>,
}
```

`[own r]` declares that `Parser` owns a region named `r`. The tag `r` does not appear in
`Parser`'s external type — from the call site, the type is just `Parser`, not `Parser[r]`.
The owned region is an implementation detail of the struct.

The owned region is strictly private: no code outside the struct's `impl` blocks may obtain
or name the region handle. A struct may declare at most one owned region (see §8 for the
multi-region question).

---

## 2. Construction and drop

Construction creates the arena implicitly. No explicit region handle is passed:

```metel
let parser = Parser::new(source);
```

The arena is allocated as part of the `Parser` value. Semantically, `[own r]` desugars to
`Region::new()` in the constructor and a drop of the region in the struct's destructor
(RFC-0063 §1). The compiler synthesises both; no user-written Drop impl is required.

When `parser` is dropped — either by going out of scope or by an explicit `drop` — the
arena is freed. If any `&[r] T` borrows are outstanding at drop time, the borrow checker
rejects the program.

The drop ordering is: the struct's own fields are dropped first in declaration order, then
the owned arena is freed. This ensures that any `@[r] T` pointers stored as fields are
unreachable before the bulk free occurs.

---

## 3. Implicit scope in `impl` blocks

Inside any `impl Parser` block, `r` is implicitly in scope as if it were a bracket
parameter. Methods may use `r` in type positions and `@[r] expr` to allocate into the owned
arena:

```metel
impl Parser {
    fun new(source: String) -> Parser {
        Parser { source, nodes: @[r] List::Nil {} }
        //                      ^^^^^ r is in scope; allocates into the new arena
    }

    fun push_node[s](self: &mut [s] Parser, node: AstNode) -> &[r] AstNode {
        let ptr = @[r] node;   // allocate into Parser's arena
        self.nodes = @[r] List::Cons { head: ptr, tail: self.nodes };
        &ptr
    }

    fun root[s](self: &[s] Parser) -> &[r] AstNode {
        &self.nodes.head   // borrow into Parser's arena; valid for r, not just s
    }
}
```

`r` is never written in the impl block header — it is always implicit for structs that
declare `[own r]`.

---

## 4. Two lifetimes in method signatures

Every method on a struct with `[own r]` has access to two distinct lifetimes:

- **`r`** — the struct's own lifetime; the arena lives exactly as long as the struct.
- **`s`** (or any fresh name) — the duration of a particular *borrow* of the struct,
  introduced as an explicit bracket parameter.

These are independent. A borrow of `Parser` (`&[s] Parser`) may be much shorter than the
`Parser` value's lifetime. A return type of `&[r] AstNode` means the returned reference
is valid for the *struct's* lifetime, not just for the duration of the call or the borrow
that enabled it:

```metel
fun root[s](self: &[s] Parser) -> &[r] AstNode { … }
//      ^^^  ^^^^^^^^^^^^^^^^     ^^^^^^^^^^^^^
//      s = duration of this borrow
//                                r = Parser's entire lifetime (the arena)
```

The caller may drop the `&[s] Parser` borrow and still hold the `&[r] AstNode` reference,
provided the `Parser` value itself remains live. The borrow checker enforces this: `parser`
cannot be dropped while any `&[r] T` is outstanding.

This mirrors Rust's two-lifetime method pattern (`&'this self` vs `'arena`) within the
Metel region model.

---

## 5. Allocation requires exclusive access

`@[r] expr` inside a method lowers to a mutable operation on the arena. Therefore,
allocation into the owned region requires an exclusive borrow of `self`:

```metel
fun push[s](self: &mut [s] Parser, node: AstNode) -> &[r] AstNode { … }  // ✓
fun push[s](self: &[s]     Parser, node: AstNode) -> &[r] AstNode { … }  // ✗ — cannot allocate through shared borrow
```

Methods with shared `&[s] Parser` may read and borrow from the arena but may not allocate
into it. This is the same exclusivity constraint as RFC-0063 §1: `@[r] expr` requires
`&mut` access to the arena handle.

---

## 6. Interaction with region ergonomics (RFC-0065)

When a method has only one region in scope — the implicit `r` and no explicit borrow
lifetime — the elision rule from RFC-0065 applies: bare `@T` elides to `@[r] T`, and
omitted bracket arguments at call sites resolve to `r`.

When both `r` and a borrow-duration tag `s` are in scope and `s` appears in the return
type, two regions are present and `@`-elision does not apply; all tags must be named. When
`s` appears only on the receiver and not in any return type, `s` may be elided entirely
from the bracket channel and receiver annotation (see §8.3).

```metel
impl Parser {
    // Single region in scope (r only) — elision applies
    fun init(self: &mut Parser) {
        self.nodes = @List::Nil {};   // @[r] List::Nil {} via elision
    }

    // Two regions in scope (r and s) — all tags explicit
    fun copy_into[s](self: &[s] Parser, dst: &mut [s] Parser) {
        dst.nodes = @[r] clone_list(&[s] self.nodes);  // all tags named
    }
}
```

---

## 7. Interaction with RFC-0063 borrowed regions

`[own r]` and the existing `[r]` bracket parameter are complementary:

| Form | Region owned by | Tag visible externally |
|---|---|---|
| `struct Foo[r]` | Caller | Yes — appears in `Foo[r]` type |
| `struct Foo[own r]` | The struct | No — `r` is internal |

A struct may have both: `struct Foo[own r, s]` owns region `r` and borrows into external
region `s`. `r` is implicit in impl blocks; `s` is an external bracket parameter as usual.

---

## 8. Unresolved questions

1. **Multiple owned regions — deferred.** Whether `[own r, own s]` should be permitted is
   deferred until a concrete use case is established. The straightforward reading — two
   arenas, both freed on drop — is coherent, but the added complexity is not justified
   without evidence of need.

2. **`Outlives` bounds between owned and borrowed regions — resolved.** When
   `struct Foo[own r, s]` holds a field of type `&[s] T`, the borrow checker derives
   `s: Outlives<r>` automatically from the field type — the borrow must be valid for the
   entire lifetime of the struct, which is `r`. No explicit annotation is required. The
   explicit form `[own r, s: Outlives<r>]` is permitted for documentation purposes.
   This follows the same inference rule Rust applies to struct lifetime bounds.

3. **Elision of the borrow-duration tag — resolved.** When `[s]` appears only on the
   receiver and not in any return type, the bracket parameter and the `[s]` tag on `self`
   may both be omitted. The receiver is written as `self: &Foo` or `self: &mut Foo`; the
   compiler infers a fresh anonymous borrow duration. The explicit form is always valid.
   This follows Rust's self-receiver lifetime elision rule. It does not conflict with
   RFC-0065's rule that bare `&T` never expands to `&[r] T` — the elided tag here is a
   borrow duration, not an allocation region.

---

## References

- RFC-0063 (Region Handles) — core region system; `@[r] expr` allocation; bracket channel.
- RFC-0065 (Region Ergonomics) — elision rules; two-or-more region discipline (§1.2).
- RFC-0067 (Reference Types) — `&[r] T` / `&mut [r] T`; auto-deref; lifetime witness in
  return positions.
- RFC-0052 (Lifetime System) — if a lifetime system is later adopted, owned regions and
  struct lifetimes should be reconciled with it.
