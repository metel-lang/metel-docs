---
id: rfc-0046
title: "Linear Closure Capture"
date: '2026-06-04'
---

## Summary

Define how closures may capture linear values (RFC-0028). The current closure model (RFC-0006) handles non-linear values only — clone-by-value capture, explicit pointer capture for shared mutable state. Linear values cannot be clone-captured: cloning would violate the exactly-once guarantee. This RFC decides what syntax, if any, permits a linear binding to enter a closure's captured environment, and what the type-level consequences are for the closure itself.

---

## Motivation

RFC-0006 explicitly defers linear closure capture:

> "Linear values remain future work. A later RFC may permit some form of explicit move capture or ownership capture for linear bindings, but that must be expressed as a distinct rule. The non-linear capture machinery described here must not be treated as automatically applicable to linear values."

With linear types now settled in RFC-0028, the open question can be addressed. Three concrete cases motivate the design:

**1. Callback that consumes a resource**

```metel
let buf: Buffer = Buffer::alloc(1024);
let flush: linear fun() -> () = [move buf] () -> () {
    buf.write(footer).flush().free();
};
// buf is consumed; flush owns it
flush();   // flush consumed here
```

**2. Region handle inside a closure**

```metel
region {
    let p: *Node = Region::alloc(Node { ... });
    let process: linear fun() -> () = [move p] () -> () { process(p); };
    process();   // called inside the block; p is region-internal, not Send
}
```

**3. Linear closure passed to higher-order functions**

```metel
fun run_once(f: linear fun() -> ()) { f(); }
run_once(flush);   // flush: linear fun() -> (); consumed by run_once
```

---

## Background

A linear value has exactly-once consumption. For a closure to capture a linear binding it must **transfer ownership** from the outer scope into the closure environment. This differs from both value capture (clone — not valid for linear) and pointer capture (alias — violates exactly-once without a borrow-checker).

The consequence: once a linear value is captured into a closure, the original binding is consumed. The closure becomes the new owner. If the closure itself is callable more than once, and the linear value is consumed inside the body, the second call would use an already-consumed value — a type error. This means a closure that captures and consumes a linear value is itself linear: it may be called exactly once.

---

## Design

### Capture syntax

Linear bindings are moved into a closure by naming them in the capture list with the `move` specifier, extending RFC-0050's unified capture list:

```
capture_item = "&mut" ident   // mutable reference capture (RFC-0050)
             | "move" ident   // ownership transfer of a linear binding
```

Both specifiers may appear in the same list:

```metel
let flush = [move buf] () -> () {
    buf.write(footer).flush().free();
};

// Combined with mutable reference capture:
let f = [&mut count, move buf] () -> () {
    count += 1;
    buf.write(footer).flush().free();
};
```

A linear binding referenced in the closure body that is not listed with `move` is a type error — linear values cannot be clone-captured. Unlisted non-linear bindings continue to be clone-captured (RFC-0006 default).

`move buf` consumes `buf` at closure creation time. After the closure is created, `buf` is dead in the enclosing scope — using it is a compile error.

### `linear fun` type

A closure that move-captures a linear value has type `linear fun() -> ()`. Calling the closure consumes it. This is consistent with RFC-0028 OQ-10: "`linear` means 'exactly-once consumption' wherever it appears" — the same keyword used for `linear struct`, `linear enum`, and `fun<linear T>`.

```metel
let flush: linear fun() -> () = [move buf] () -> () {
    buf.write(footer).flush().free();
};
flush();   // flush consumed here; cannot call again
```

A `fun() -> ()` parameter only accepts closures with no linear captures. A `linear fun() -> ()` parameter accepts closures that own linear captures and must be called exactly once:

```metel
fun run_once(f: linear fun() -> ()) { f(); }
fun run_many(f: fun() -> ()) { f(); f(); }
```

A closure is `linear fun` only when it contains a `move` capture. Closures with only `&mut` or clone captures remain `fun`.

### Region closures and the `Send` exit constraint

A closure that captures a region-internal value is not `Send` and cannot escape the `region { }` block — the block's interim exit constraint is `Send` (RFC-0025, RFC-0051). A `*T` pointer produced inside the region is not `Send`; a closure holding one via `move` is not `Send`.

```metel
region {
    let p: *Node = Region::alloc(Node { ... });
    let f = [move p] () -> () { process(p); };
    // f holds *Node — not Send — type error to return from block
    f();   // valid — called inside the block
}
```

### Direct move-capture and `@T`

Direct `[move buf]` capture of an unboxed linear value is supported. Boxing before capture (`@buf`) is also valid but not required. The programmer chooses based on whether heap indirection is independently useful.

---

## Constraints

1. **No silent duplication** — A linear value may not appear in both the outer scope and the closure's captured environment simultaneously.
2. **Consume-at-capture** — The outer binding is consumed when the closure is created, not when it is called.
3. **Single-call safety** — A closure that consumes a linear value in its body cannot be called twice. The `linear fun` type enforces this.

---

## Resolved Questions

1. **Capture syntax ✓** — `[move x]` in the capture list, extending RFC-0050's unified `[...]` syntax. Per-variable and explicit.
2. **Closure type ✓** — `linear fun() -> ()`. Consistent with `linear` as exactly-once-consumption marker throughout the language.
3. **Region closures ✓** — closure holding region-internal `*T` is not `Send`; cannot escape the block. Becomes `RegionFree<'r>`-gated when RFC-0051 lands.
4. **Direct move-capture ✓** — supported without requiring `@T` boxing.

---

## Relationship to Other RFCs

- **RFC-0006** — establishes non-linear closure semantics; explicitly defers linear capture to this RFC
- **RFC-0028** — linear types, `@T`, `fun<linear T>`; the foundation for this RFC
- **RFC-0025** — `Region` is linear; `Send` is the interim exit constraint for region blocks
- **RFC-0051** — full `RegionFree<'r>` marker replacing `Send`; closure typing updated when this lands
- **RFC-0050** — `[&mut x]` capture list; `[move x]` extends the same syntax; resolved jointly
- **RFC-0026** — inside `unsafe`, linear capture restrictions may be relaxed; deferred

---

## References

- RFC-0006: `docs/internal/rfcs/4-implemented/rfc-0006-closure-capture-semantics.md` — §"Fit with Linear Types and the Compiler"
- RFC-0028: `docs/internal/rfcs/1-under-review/rfc-0028-memory-and-reference-model.md`
- RFC-0025: `docs/internal/rfcs/1-under-review/rfc-0025-region-allocation.md`
- RFC-0050: `docs/internal/rfcs/1-under-review/rfc-0050-closure-capture-lists.md`
