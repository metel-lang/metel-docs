---
id: rfc-0141
title: "Aspect Objects: Explicit Allocator Placement"
date: '2026-08-25'
status: accepted
---

> **Status — accepted (2026-08-25), inherited from the split.** Split out of RFC-0008
> (Aspect Objects, `2-accepted`) the same day: RFC-0008 was originally written
> entirely in terms of this RFC's `@[r] dyn Aspect` region-tagged syntax, because
> RFC-0063 (Allocator Handles) was already `2-accepted` at draft time. Checked
> directly against `metel-frontend/src/grammar.pest` on `develop`: neither `@[`
> allocator-handle syntax nor `dyn` exists in the grammar yet, and RFC-0063 itself is
> still `2-accepted`, not integrated or implemented. That left RFC-0008 reading as
> blocked on RFC-0063 in its entirety, when only this piece actually is. This RFC
> carries exactly that piece — the design content is unchanged from what RFC-0008
> originally specified for the region-tagged form; only the document boundary moved.
> Depends on RFC-0008 (base `dyn Aspect` design — object safety, vtable dispatch,
> coercion, the implicit-allocation owned form) and on RFC-0063 (Allocator Handles,
> `2-accepted`, not integrated or implemented — the actual blocker on this RFC
> specifically, not on RFC-0008 as a whole).

## Summary

Extends RFC-0008's `dyn Aspect` with an explicitly allocator-tagged owned form,
`@[r] dyn Aspect` — the same aspect-object mechanism, placed in a named region
instead of wherever the interpreter's implicit allocation puts it. Adds allocator
choice (which region, which allocator strategy) without changing anything about
object safety, vtable dispatch, or the coercion rule, all of which RFC-0008 already
specifies completely and independently of allocator strategy.

---

## 1. Syntax

The owned form gains an explicit allocator tag:

```metel
@[r] dyn Display      // owned aspect object in region r
```

(RFC-0008's borrowed forms, `&dyn Display` and `&var dyn Display`, are unaffected —
a reference to an existing value has no allocator of its own to name.)

A value of concrete type `T` where `T: Aspect` is coerced to `@[r] dyn Aspect` by
allocating it in region `r`:

```metel
let shape: @[r] dyn Shape = @[r] Circle { radius = 5.0 };
let shape2: @[r] dyn Shape = @[r] Rectangle { w = 3.0, h = 4.0 };
```

---

## 2. Representation

Same fat pointer as RFC-0008 §2 — a data pointer and a vtable pointer — with the
data pointer now targeting a value allocated in region `r` instead of the
interpreter's implicit heap:

- **Data pointer** — points to the concrete value, allocated in region `r`.
- **Vtable pointer** — unchanged from RFC-0008 §2; the same compiler-generated table
  either way.

---

## 3. Ownership and Drop

Same as RFC-0008 §5, with the deallocation step made explicit: when the fat pointer
is dropped, the runtime calls the concrete type's `Drop` destructor via the vtable's
drop pointer (if present), then deallocates the memory in region `r` — rather than
however the interpreter's implicit heap reclaims an unreferenced value. *When* drop
fires is unchanged from RFC-0008 §5; only what the final deallocation step does
differs.

---

## 4. Heterogeneous Collections

RFC-0008 §7's example, with an explicit region:

```metel
let shapes: List<@[r] dyn Shape> = List::new();
shapes.push(@[r] Circle { radius = 5.0 });
shapes.push(@[r] Rectangle { w = 3.0, h = 4.0 });

for shape in shapes {
    println(shape.area());   // dispatched through vtable
}
```

Each element is a fat pointer into region `r`, rather than into the interpreter's
implicit heap. Object safety, dispatch, and the collection mechanics themselves are
entirely RFC-0008's; this section only changes which allocator backs each element.

---

## 5. Unresolved Questions

1. **Aspect object and brand parameters.** Whether `dyn Aspect` may appear inside a
   branded type — e.g., `@[Rc<'b>] dyn Aspect` — is deferred. The interaction with
   the brand's type invariants requires careful analysis. (Moved here 2026-08-25 from
   RFC-0008 §9 item 3 — specific to this RFC's region-tagged form, not applicable
   before it exists.)

---

## References

- RFC-0008 (Aspect Objects) — the base `dyn Aspect` design this RFC extends: object
  safety, vtable dispatch, the coercion rule, and the implicit-allocation owned form.
  Everything in this RFC composes with RFC-0008's design unchanged.
- RFC-0063 (Allocator Handles, `2-accepted`, not integrated or implemented) — the
  region-handle mechanism `@[r]` this RFC's syntax depends on. The actual blocker on
  this RFC.
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) — move/drop timing,
  unchanged from RFC-0008 §5.

---

## Decision

**Outcome:** Accepted (2026-08-25), inherited from RFC-0008's own acceptance at the
point of the split — the design was already settled as part of RFC-0008 before being
carved out into its own document; nothing here has had an independent review pass as
a standalone RFC. Blocked on RFC-0063 reaching real implementation before this RFC's
own syntax can be built.
**Target:** Blocked on RFC-0063 (Allocator Handles, `2-accepted`, not integrated or
implemented).
