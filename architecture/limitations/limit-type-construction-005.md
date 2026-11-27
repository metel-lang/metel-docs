---
id: LIMIT-TYPE-CONSTRUCTION-005
title: "Call-syntax nominal construction (RFC-0100) is not implemented; nominal brace literals remain the only construction form"
summary: "`Point(x = 1, y = 2)` does not construct `Point`; a bare brace literal `Point { x = 1, y = 2 }` is still the only way to construct a struct or enum variant."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "RFC-0100 entering 3-integrated with no implementation yet"
disposition: planned
tracked_by: metel-core#2197
rfc: RFC-0100
review: null
---

## Limitation

`Point(args)` is ordinary call resolution today: if `Point` names a struct or enum, the
call is rejected or, when a same-named function also exists, dispatched to the
function — never to construction. Nominal construction is still the brace literal,
`Point { x = 1, y = 2 }`. Reproduced against current `develop` (this is
`rfc0100_rollback_braces_and_function_calls_are_distinct.mtl`, pinned since
metel-core#1945):

```metel repro=T0003
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }
fun main() {
    let ticket := Ticket { value = 3 };
    assert(Ticket(input = 1) == 101);
}
```

```
Ticket(input = 1) calls the function, returning 101 -- it never constructs a `Ticket`.
```

None of RFC-0100's accepted design is implemented: not call-syntax construction itself,
not section 3's privileged representation-construction form (`Point { x = 1, y = 2 }`
restricted to a constructor body, with a condition-position restriction), not whole-row
construction arguments' relationship to call syntax, and not enum variant construction
via a qualified call (`Message::Text(body = "hello")`). The Language Spec states this
design as the accepted one ahead of the implementation (Swift-Evolution-style:
`impl_status: not-started`), per this project's convention for an RFC that has reached
`3-integrated` without a prototype.

## Impact

Visible to Metel programmers: `Point(args)` still constructs nothing; `Point { args }`
is still required. A struct and a function may still legally share a name (the opposite
of RFC-0100's accepted design — see `LIMIT-NAME-RESOLUTION-006`), and the
argument-dependent lookup bug this RFC exists to fix (metel-core#1945/#1946) is not
fixed: it is simply not yet reachable, because call-syntax construction that would
trigger it does not exist yet either.

## Affects

- `spec.declarations.structs.instantiation-and-field-access.legality-1`
- `spec.declarations.structs.instantiation-and-field-access.legality-2`
- `spec.declarations.structs.call-syntax-construction.legality-1`
- `spec.declarations.structs.call-syntax-construction.dynamics-1`
- `spec.declarations.structs.privileged-representation-construction.legality-1`
- `spec.declarations.structs.privileged-representation-construction.legality-2`
- `spec.declarations.structs.whole-row-construction.legality-1`
- `spec.declarations.enums.legality-1`
- `spec.declarations.enums.variant-construction.legality-1`
- `spec.declarations.enums.variant-construction.dynamics-1`
- RFC-0100

## Resolution

Planned: tracked as metel-core#2197 (RFC-0100 implementation). Depends on
`LIMIT-NAME-RESOLUTION-006` (the unified-namespace check this RFC's soundness
argument relies on) landing first or alongside it — call-syntax construction without
namespace unification would reintroduce the exact argument-dependent-lookup bug
metel-core#1945/#1946 reverted.
