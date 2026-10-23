# Name & Reference Resolution {#name-resolution}

The pipeline stage after module loading ([Module Loading & Parsing](parsing.md)): every top-level declaration across the loaded `ModuleGraph` gets a stable `SymbolId`, import/glob visibility is settled per module, and every reference site is classified against that symbol space. Owning crate: `metel-frontend`. Defined in `name_resolver.rs`, `reference_resolver.rs`, and `symbols.rs`.

This is adjacent to, but distinct from, [Resolution](resolution.md) (`arch.resolution.*`, ADR-0054's identity-freeze model in `identity/`). That section covers structural `LocalId`/`RefId`/`FieldId`/`VariantId` allocation for lexical bindings and member declarations. This section covers an earlier, different concern: binding a top-level *declaration* to a `SymbolId`, and classifying which *references* point at one. A reader should not conflate the two symbol/identity systems just because both produce stable ids.

## Model

Resolution begins by giving every declaration one canonical `SymbolId`; imports and
aliases then point back to that declaration rather than minting local replacements
([declaration identity](#arch.name-resolution.requirement-1)). Import precedence is
settled before reference classification, so explicit imports and globs behave
predictably ([import scopes](#arch.name-resolution.requirement-2)).

Reference collection records the identity selected at each use site
([references](#arch.name-resolution.requirement-3)). Path normalization is a
following, separate stage; both precede the structural identity freeze described
in the Resolution section.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.name-resolution.requirement-1}

Every top-level declaration gets a `SymbolId` from one `SymbolTable` keyed by (module, namespace, name), so a struct and a function of one name differ. Builtins are `Builtin` ids, the rest `Declared`; overloads and block-local types are separate kinds. A declaration keeps one id under any importer or alias.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | d05bbfd47ae51437f565e0142a58f8e8a950d114 |
| `related` | METEL-185, ADR-0041 |

##### Requirement {#arch.name-resolution.requirement-2}

An explicit `import` beats a glob, and two explicit imports of one local name in one namespace are an error. A user glob silently beats the auto-inserted std glob; `T0011` fires only when two globs of the same tier export one name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | `T0011`, ADR-0026 |

##### Requirement {#arch.name-resolution.requirement-3}

Each bare-identifier reference is `Res::Def` (a top-level declaration, with its `SymbolId`) or `Res::Local` (parameter, `let`/`mut`, `for` or match binding); a local shadows a same-named global. Only `Def` references are recorded, keyed by `Span`, before the resolution freeze.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | METEL-187, ADR-0041 |

</details>

## Known limitations

<!-- records:limitations -->
