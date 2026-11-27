---
id: LIMIT-NAME-RESOLUTION-006
title: "A type and a value may still share a name; RFC-0100's unified namespace is not implemented"
summary: "struct Foo and fun Foo still coexist today, reversing RFC-0100's accepted (not yet implemented) design that they must not."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "RFC-0100 entering 3-integrated with no implementation yet, reversing LIMIT-NAME-RESOLUTION-005's case 1"
disposition: planned
tracked_by: metel-core#2197
rfc: RFC-0100
review: null
---

## Limitation

The symbol table is keyed `(module, namespace, name)` with type and value as the two
namespace values (`metel-core#1560`/`#1571`), and duplicate-name detection (`T0037`)
runs correctly within one namespace value but not across both — by deliberate policy,
not oversight: `LIMIT-NAME-RESOLUTION-005`'s case 1 explicitly states "[a struct and a
function sharing a name] is legal... that pair is legal (types and values are separate
namespaces) and behaves correctly," pinned by a dedicated fixture,
`a_type_and_a_function_may_share_a_name.mtl`. **This record supersedes that statement.**
RFC-0100 (integrated 2026-11-27) reverses it: a module's type and value declarations are
to share one namespace, so `struct Foo` and `fun Foo` in the same scope become an
ordinary redeclaration error. Reproduced against current `develop`:

```metel
struct Foo { n: i64 }
fun Foo() -> i64 { 1 }
fun main() {
    assert(Foo { n = 1 }.n == 1);
    assert(Foo() == 1);
}
```

Both declarations coexist today and both calls succeed; under RFC-0100's accepted
design, the second declaration would be a duplicate-declaration error at the point
`fun Foo` is written, never reaching a call site at all.

Nothing about `LIMIT-NAME-RESOLUTION-005`'s actual bug fixes (cases 2 and 3: a method's
key now carries its impl's type arguments; a repeated method name collides as `T0034`)
is affected or reversed. Only case 1's policy conclusion — that the pair is legal — no
longer holds once this limitation is lifted.

## Impact

Visible to Metel programmers: a type and a same-named function still coexist legally,
and the import/duplicate-detection narrowing RFC-0100 §1 describes (collapsing the
symbol key's namespace dimension from two values to one, reusing `T0037` rather than
building new machinery) does not exist. This is also what keeps the original
argument-dependent-lookup bug (metel-core#1945/#1946) structurally possible to write
again once call-syntax construction (`LIMIT-TYPE-CONSTRUCTION-005`) is implemented
without this limitation being lifted first or alongside it.

## Affects

- `spec.modules.visibility.legality-6`
- RFC-0100
- `LIMIT-NAME-RESOLUTION-005` (case 1's "that pair is legal" conclusion, superseded)

## Resolution

Planned: tracked as metel-core#2197 (RFC-0100 implementation). Narrows the symbol
table's existing `(module, namespace, name)` key from two namespace values to one;
reuses `T0037`'s existing duplicate-detection machinery rather than adding a parallel
check. Also requires retiring or inverting `#1560`'s own pinning fixture,
`a_type_and_a_function_may_share_a_name.mtl`, and revisiting `#1560`/`#1571`'s closed
acceptance criteria, which assumed coexistence would remain a permanent invariant.
