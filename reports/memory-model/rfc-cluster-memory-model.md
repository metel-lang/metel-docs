# RFC Cluster: Memory Model

**Status:** Under resolution  
**Tracking issue:** #118  
**RFCs in scope:** RFC-0028, RFC-0003, RFC-0006, RFC-0025, RFC-0026  
**Last updated:** 2026-06-04

---

## Overview

Four open RFCs collectively define Metel's memory and concurrency model. They were written independently but are deeply interdependent — accepting or implementing any one of them without resolving the others will produce inconsistencies that require breaking changes later. This document maps the conflicts, establishes the decisions that must be made, and proposes a resolution order.

The four RFCs:

| RFC | Title | Status | Current target |
|---|---|---|---|
| RFC-0028 | Memory and Reference Model | Draft | v0.3 |
| RFC-0003 | Concurrency Model | **Resolved** | v0.4 |
| RFC-0006 | Closure Capture Semantics | Draft | — |
| RFC-0025 | Region Allocation | Draft | v0.4 |
| RFC-0026 | Unsafe Blocks | Draft | v0.4 |
| RFC-0043 | Regular Pointers and Mutable Pointers | **Incorporated** | v0.3 |
| ~~RFC-0001~~ | ~~Pointer Syntax and Semantics~~ | Superseded by RFC-0028/RFC-0043 | — |
| ~~RFC-0024~~ | ~~Linear Types~~ | Superseded by RFC-0028 | — |

---

## Dependency Graph

```
RFC-0024 (Linear Types)
    │
    ├──► conflicts with ──► RFC-0001 (Pointers)
    │        │
    │        └──► depended on by ──► RFC-0006 (Closure Capture)
    │                                    │
    │                                    └──► depends on ──► RFC-0003 (Concurrency)
    │
    ├──► constrains ──► RFC-0003 (Concurrency)
    │
    ├──► required by ──► RFC-0025 (Region Allocation)
    │        │
    │        └──► escape hatch from ──► RFC-0026 (Unsafe Blocks)
    │
    └──► escape hatch from ──► RFC-0026 (Unsafe Blocks)
             │
             └──► also escapes ──► RFC-0001, RFC-0003, RFC-0006
```

RFC-0006 explicitly lists RFC-0001 and RFC-0003 as blocking dependencies. RFC-0024 introduces constraints on both RFC-0001 (aliasing) and RFC-0006 (capture). RFC-0003 is the most independent but is constrained by both RFC-0001 and RFC-0024.

---

## Conflict Analysis

### Conflict 1 — The `&` syntax collision (RFC-0001 vs RFC-0024) ✓ Resolved

RFC-0001 proposes `&x` as the address-of operator, producing a storable, RC-backed `*T` pointer:

```metel
mut x: Int = 42;
let p: *Int = &x;       // p is a *Int — storable, cloneable, RC-backed
let q: *mut Int = &mut x;
```

RFC-0024 proposes `&T` as a read reference — a non-storable, expression-only view used to inspect a linear value without consuming it:

```metel
let buf = Buffer::alloc(1024);
let len = buf_len(&buf);   // &buf is a temporary — cannot be stored, cannot outlive the expression
```

The same sigil means different things with incompatible semantics. This is not a minor syntactic overlap — `*T` (RFC-0001) is reference-counted and storable, `&T` (RFC-0024) is non-storable and has no runtime representation. Shipping both independently creates a language where `&x` means two different things depending on context.

**Decision:** Option A — differentiate the sigils.

- **Option A — Differentiate the sigils.** ✓ **Adopted.** Keep `&` for RFC-0001's address-of; `&x` always produces `*T`, always RC-backed and storable. RFC-0024's read reference uses `@x` / `@T` — a distinct sigil, unused elsewhere in the language, visually unambiguous.
- **Option B — Unify under `&`.** Rejected. `&x` would produce `*T` for non-linear targets and `@T` for linear targets — different result types behind the same operator. Type-dependent operator behavior behind a single sigil is at odds with Metel's no-implicit-conversions principle and makes generic code difficult to reason about.
- **Option C — Restrict RFC-0001 to non-linear types only.** Rejected for the same reason as Option B — same syntax, incompatible result types depending on linearity.

`&x` is now unambiguous across the entire language: it always means address-of and always produces `*T`. RFC-0024's read reference operator is `@x` / `@T` throughout.

---

### Conflict 2 — Aliasing vs linearity (RFC-0001 vs RFC-0024) ✓ Resolved

RFC-0001's mechanism for sharing state between closures is: take a pointer, then clone the pointer. Cloning `*mut T` produces a second mutable alias to the same RC cell. This is the entire point of pointers in RFC-0001's model.

Linear types require the opposite: a linear value has exactly one owner. A second alias is a violation of the invariant — two aliases mean two potential consumers, breaking the exactly-once guarantee.

**Consequence:** `*T` and `*mut T` cannot point to linear values. Attempting to take `&x` where `x` is linear must be a type error under RFC-0001's semantics. This is not a small restriction — it means the two features operate in completely separate worlds: pointers for non-linear (RC-managed) values, and RFC-0024's `@T` read reference for linear values.

**Decision:** The hard separation is adopted. `*T` and `*mut T` are exclusively for non-linear types. `unique *T` (RFC-0028 OQ-2) is the linear-compatible heap indirection — a pointer whose handle is itself linear and cannot be cloned. This is the tracked unique pointer form; it is in scope for RFC-0028.

---

### Conflict 3 — Clone capture vs linear values (RFC-0006 vs RFC-0024) — Open

RFC-0006 proposes that closures capture all free variables by cloning at definition time. A linear value cannot be cloned — there is by definition only one copy of it. Implicit clone capture of a linear value is therefore a type error.

Explicit pointer capture (RFC-0006's workaround for shared mutable state) is also forbidden for linear values (Conflict 2 above).

This leaves no way to use a linear value from an enclosing scope inside a closure body under RFC-0006's current model.

**Missing feature:** RFC-0006 has no move-capture mechanism. A move capture would transfer the linear value into the closure at definition time, consuming it in the outer scope. This is the only sound option for closures and linear types.

**Decision required:** RFC-0006 must be amended to add move capture, at minimum for linear types. The question is whether move capture should be:

- **Linear-only** — the compiler automatically move-captures linear values; non-linear values continue to clone-capture.
- **Explicit opt-in** — a `move` qualifier on the closure (as in Rust's `move || { ... }`) transfers all linear free variables. Non-linear values can still be clone-captured.
- **Per-variable** — something like `capture(move buf, clone counter)` in the closure header. Maximum control, maximum verbosity.

The explicit opt-in (`move fun(...) { ... }`) is the most consistent with Metel's "no implicit conversions" principle. Automatic move-capture for linear values specifically is a reasonable middle ground since the linear type system already tracks whether a value is consumed.

---

### Conflict 4 — Shared ownership types vs linearity (RFC-0003 vs RFC-0024) ✓ Resolved

RFC-0003 introduces `Arc<T>` as the mechanism for sharing values across fiber boundaries. `Arc<T>` works by cloning the Arc handle, producing multiple co-owners of the inner value — the reference count determines when the value is freed.

For a linear `T`, this is unsound: `Arc<LinearT>` would allow the same linear value to be accessible from multiple Arc handles simultaneously, with no guarantee about which one "consumes" it. `Arc::clone` would violate linearity.

`Rc<LinearT>` is the same problem within a single fiber.

**Decision (RFC-0003):** `Arc<LinearT>` and `Rc<LinearT>` are forbidden — the type system rejects them. `Mutex<LinearT>` is also forbidden: the Mutex model (permanent shared ownership of a fixed inner value) is incompatible with linear types (transient unique ownership with mandatory transfer), even though access is exclusive at any instant.

**Channel send is compatible.** `ch <- value` transfers the value into the channel — this is consumption. A linear value sent through a channel satisfies the exactly-once rule: the sender no longer holds it, the receiver receives it once. Channels are the natural cross-fiber transport for linear values. This is settled and documented in RFC-0003.

---

## Proposed Resolution Order

The RFCs must be resolved in a specific order because later decisions depend on earlier ones.

### Step 1 — Resolve the `&` syntax conflict (RFC-0001 × RFC-0024) ✓ Done

This was the foundational decision. All other conflicts depend on knowing what `&x` means.

**Decision:** Option A — differentiate the sigils. `&x` always means address-of and always produces `*T` (RFC-0001 semantics). RFC-0024's read reference uses `@x` / `@T` — a distinct sigil with no other meaning in the language.

**Output:** RFC-0001 and RFC-0024 superseded by RFC-0028, which incorporates all resolved decisions and carries forward all open questions in unified form.

### Step 2 — Establish the linear/pointer boundary ✓ Done

RFC-0043 (implemented) establishes `&x`/`&mut x` as address-of for non-linear types only. RFC-0028 carries the explicit rule: `&x` where `x` is linear is a type error. Linear values are not addressable via `*T` or `*mut T`.

Tracked unique pointers (`unique *T`) are in scope for RFC-0028 as the linear-compatible heap indirection mechanism. The handle is itself linear (cannot be cloned), satisfying the exactly-once invariant.

**Output:** RFC-0043 (incorporated), RFC-0028 OQ-2 (unique pointer syntax — still open).

### Step 3 — Add move capture to RFC-0006 — Open

Move capture for linear values is not yet resolved. The recommended form remains `move fun` as an explicit qualifier. RFC-0006 must be amended before RFC-0028 can be fully implemented. See D3 below.

**Output:** pending RFC-0006 amendment.

### Step 4 — Close RFC-0003 restrictions on linear types ✓ Done

RFC-0003 (resolved 2026-06-04) now contains:

- `Arc<LinearT>` and `Rc<LinearT>` forbidden — type error.
- `Mutex<LinearT>` forbidden — incompatible ownership model.
- Linear `Send` derivation rule: a linear type is `Send` if all fields are `Send` (same as non-linear).
- Channels as the idiomatic linear-value cross-fiber transport — documented in RFC-0003.

**Output:** RFC-0003 resolved.

### Step 5 — Final acceptance

Remaining RFCs to resolve before the memory cluster is closed:

| RFC | Status | Target | Blocking |
|---|---|---|---|
| RFC-0043 | **Incorporated** | v0.3 | — |
| RFC-0003 | **Resolved** | v0.4 | — |
| RFC-0028 | Draft — open questions remain | v0.3 | D3 (move capture), OQ-1 (linearity sigil), OQ-2/3 (unique ptr) |
| RFC-0006 | Draft — move capture not yet defined | v0.3 | RFC-0028 OQ-1 |
| RFC-0025 | Draft | v0.4 | RFC-0028 (Region is a linear struct) |
| RFC-0026 | Draft | v0.4 | RFC-0028 (linearity checker relaxed in unsafe) |
| ~~RFC-0001~~ | Superseded by RFC-0043 + RFC-0028 | — | — |
| ~~RFC-0024~~ | Superseded by RFC-0028 | — | — |

---

## Decision Log

| # | Decision | Status |
|---|---|---|
| D1 | `&` syntax: unify under one sigil or differentiate | **Resolved** — `&x` always address-of (`*T`); RFC-0024 read reference uses `@x` / `@T` |
| D2 | Tracked unique pointers: in or out of scope for v0.3 | **Resolved** — `unique *T` is in scope for RFC-0028; handle is linear, cannot be cloned |
| D3 | Move capture: linear-only automatic, or explicit `move` qualifier | **Open** — RFC-0006 amendment pending |
| D4 | `Mutex<LinearT>`: forbidden or permitted with restrictions | **Resolved** — forbidden (RFC-0003). `Arc<LinearT>` and `Rc<LinearT>` also forbidden. |
| D5 | Linear `Send` derivation rule | **Resolved** — same field-based rule as non-linear types (RFC-0003) |
| D6 | Region access: scope/callback (Option A) vs direct in `unsafe` (Option B) vs both | **Open** — RFC-0025 pending |
| D7 | `unsafe fun` syntax: lock in at v0.3 with RFC-0001 or defer to v0.4 | **Open** — RFC-0026 pending |
| D8 | Auto-deref at field access, method calls, function pointer calls | **Resolved** — RFC-0043: one pointer layer auto-dereffed at those three positions only |
| D9 | Addressability rules | **Resolved** — RFC-0043: named bindings, field/element chains addressable; temporaries not |
| D10 | Pointer equality | **Resolved** — RFC-0043: identity equality; value equality requires explicit `*p == *q` |

---

## References

- RFC-0028: `docs/internal/rfcs/rfc-0028-memory-and-reference-model.md` ← primary reference for pointers and linear types
- RFC-0003: `docs/internal/rfcs/rfc-0003-concurrency-model.md`
- RFC-0006: `docs/internal/rfcs/rfc-0006-closure-capture-semantics.md`
- RFC-0025: `docs/internal/rfcs/rfc-0025-region-allocation.md`
- RFC-0026: `docs/internal/rfcs/rfc-0026-unsafe-blocks.md`
- RFC-0001: `docs/internal/rfcs/rfc-0001-pointer-syntax.md` (superseded — historical record)
- RFC-0024: `docs/internal/rfcs/rfc-0024-linear-types.md` (superseded — historical record)
