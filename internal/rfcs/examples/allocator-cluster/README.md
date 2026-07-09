---
id: allocator-cluster-examples
title: "Allocator RFC Cluster — Example Programs"
type: report
created_date: '2026-07-06'
---

# Allocator RFC Cluster — Example Programs

Worked `.mtl` examples for the current allocator/lifetime cluster: allocators as
first-class values in the value channel (`()`, `@` prefix), lifetime anchors as
compile-time parameters in the type channel (`<>`, `&` prefix). The model is
laid out in full in `reports/memory-model/lifetimes-vs-regions-2026-07-02.md`
("the split model") and specified RFC-by-RFC in `internal/rfcs/1-under-review/`.

**Status: illustrative, not executable.** The interpreter (`metel-core`) has no
borrow checker, no allocator backend, and no move-semantics enforcement yet —
it deep-clones values and leans on internal reference counting. Every file
below type-checks against the RFC text as written but cannot be run today.
Treat these as "what the surface syntax and behavior will look like," not as
a working test suite. `08-shared-ownership-rc-arc.mtl` is one step further out:
RFC-0074 itself is still in `0-draft`, blocked on RFC-0076 (brand types) Q1.

None of RFC-0069 (`SubRegion`), RFC-0085 (`PhantomRegion`), or RFC-0087
(universal own-region) appear here — all three are retracted by the split
model (see position report §5) and have moved to `6-refused/`.

## Files

| File | RFC(s) | Covers |
|---|---|---|
| [`01-allocators-and-alloc-expressions.mtl`](01-allocators-and-alloc-expressions.mtl) | 0063 | `Alloc` aspect, stdlib allocators, `@a T`, `@a expr`, fallible allocation, allocator parameters, scoped creation, sendability |
| [`02-elision-and-ergonomics.mtl`](02-elision-and-ergonomics.mtl) | 0065 | Allocator elision (`@`), lifetime-anchor elision rules 1–4, ordering bounds |
| [`03-references-and-lifetime-anchors.mtl`](03-references-and-lifetime-anchors.mtl) | 0067 | `&T` / `&mut T`, `&r T` / `&r mut T`, address-of, auto-deref, coercion |
| [`04-move-out-and-extraction.mtl`](04-move-out-and-extraction.mtl) | 0066, 0072 | Borrow-deref, move-out (`Heap` vs bulk-deallocating), `T: !Drop`, `T: Copy`, clone extraction |
| [`05-struct-owned-allocators.mtl`](05-struct-owned-allocators.mtl) | 0068 | Primary-constructor allocator ownership, implicit scope in `impl`, two lifetimes, exclusive-access rule |
| [`06-generic-allocators-and-variance.mtl`](06-generic-allocators-and-variance.mtl) | 0077 | `<A: Alloc>` bounds, generic `impl`/`aspect impl` headers, wellformedness, variance |
| [`07-auto-alloc.mtl`](07-auto-alloc.mtl) | 0073 | `AutoAlloc`, compiler-chosen strategy, drop/move-out guarantees |
| [`08-shared-ownership-rc-arc.mtl`](08-shared-ownership-rc-arc.mtl) | 0074 (draft) | `Rc<T>` / `Arc<T>` as library structs, `SharedPointer`, `get_mut`, `try_unwrap`, sendability |
| [`09-storage-preservation.mtl`](09-storage-preservation.mtl) | 0063, 0065, 0066, 0067 | Tag-only allocator parameters (`<@a>` / elided `@T`); why a plain `T` parameter never implicitly accepts `@a T`; extraction vs. preservation |

Read them in order — later files assume the allocator/anchor vocabulary
established earlier and lean on elision once it has been introduced in `02`.

## A note on file 09

`09-storage-preservation.mtl` is the odd one out: it doesn't correspond to a
single RFC section the way the others do. It answers a question that came up
during review and wasn't previously addressed anywhere — what a plain,
`@`-free `T` parameter does when called with an `@a T` argument. The answer
settled on (full analysis in the position report §12) is: a signature's plain
types fall into three, never-conflated categories —

| Form | Meaning | Accepts `@a T` without ascription? |
|---|---|---|
| `T` (bare) | Storage-independent ownership | No — compile error; extract explicitly (RFC-0066 §3) |
| `@T` / `<@a>` | Preserve whatever storage flows in | Yes — free, monomorphized per call site |
| `&T` / `&r T` | Borrow, storage irrelevant | Yes — already free (RFC-0067 §5), unaffected by this |

The middle row is the new piece; the other two already existed. See the file
itself for the reasoning against the two rejected alternatives (implicit
move-out, and fully-implicit preservation without the `@`/`<@a>` marker).
