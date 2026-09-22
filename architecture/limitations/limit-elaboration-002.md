---
id: LIMIT-ELABORATION-002
title: "A `dyn` type spelled through an import alias for its aspect fails method dispatch"
summary: "`&dyn Sh` where `Sh` is an import alias for an aspect (`import path::Shape as Sh;`) parses but a method call through it fails with `no method on dyn Sh`; the unaliased name works."
scope: "architecture/spec/elaboration.md#elaboration"
owner: metel-frontend
discovered_by: "metel-core#1223"
disposition: known
review: null
---

## Limitation

Reproduced against current `develop`: given `import root::shapes::Shape as
Sh;` and a variable of type `&dyn Sh`, a call to a method the aspect declares
is rejected with `no method `area` on `dyn Sh``. The same program with the
aspect imported under its own name (`import root::shapes::Shape;`, `&dyn
Shape`) resolves and runs correctly. Nothing in the Language Spec ties `dyn`
dispatch to how the aspect's name was imported; an import alias is meant to be
transparent everywhere else a name is used.

## Impact

`&dyn Aspect` cannot be spelled through an aliased import, only through the
aspect's own declared name — a narrower restriction than aliasing has
anywhere else in the language.

## Affects

- `spec.declarations.aspects.dyn-aspect.legality-1`

## Resolution

None yet; tracked as `metel-core#1223`.
