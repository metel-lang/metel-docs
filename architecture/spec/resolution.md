# Resolution {#resolution}

This section is the Architecture Spec's versioned description of how the
frontend resolves source spellings to stable identities, and the boundary that
binds typechecking, elaboration, and evaluation to those identities instead of
re-deriving meaning from names. It documents the implemented resolved-identity
model described by [ADR-0054](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0054-resolved-identity-freeze-and-generic-instance-preparation.md);
the `arch-*` requirements below are its checkable claims.

Owning crate: `metel-frontend`. The model is defined in `identity/` (`mod.rs`, `allocate.rs`, `lexical_path.rs`, `member.rs`, `position.rs`), and consumed by `name_resolver.rs`, `reference_resolver.rs`, `typed_ast/`, and every later pipeline stage.

## Model

The resolution freeze separates source spelling from durable semantic identity. Every
reference is total—local or global—and later stages consume that result rather than
looking the spelling up again ([frozen references](#arch.resolution.requirement-1)).
Lexical bindings and uses receive structural identities that survive unrelated edits
([lexical identity](#arch.resolution.requirement-2)); fields and variants receive the
same treatment at the declaration level ([member identity](#arch.resolution.requirement-3)).
The walk leaves no code uncovered: a module's bare top-level statements get identities too, and a
top-level declaration's span maps to its symbol ([coverage](#arch.resolution.requirement-5)).

Editor lookup is intentionally different. A position index maps an ephemeral parsed
snapshot back to these identities, but position never becomes a semantic key
([position isolation](#arch.resolution.requirement-4)). This distinction lets tools be
responsive without making formatting alter program meaning.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.resolution.requirement-1}

Once inference has solved a body and the frontend has frozen its resolution, no later phase looks anything up by source spelling: every meaning is found by a stable identity, and every value reference has a total `Resolution` (`Global(SymbolId)` or `Local(LocalId)`), with no silent unresolved case.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | cf5f79ec5df599d1a56643c1d1ce895f76d76544 |
| `related` | ADR-0054, ADR-0041, ADR-0042 |

##### Requirement {#arch.resolution.requirement-2}

Bindings and value references get structural identities (`LocalId`, `RefId`) from a parse-driven walk keyed on `LexicalPath`, not on byte offsets or traversal counters, so reformatting, an earlier sibling binding, or an edit to another body does not change an existing identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | cf5f79ec5df599d1a56643c1d1ce895f76d76544 |
| `related` | ADR-0054 (2026-09-10 amendment) |

##### Requirement {#arch.resolution.requirement-3}

Struct fields and enum variants are interned to stable `FieldId` / `VariantId`, keyed by `(owning type SymbolId, member name)` before inference, and threaded onto the typed IR as `Option<FieldId>` / `Option<VariantId>` rather than re-derived from a string.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | ff5f034708f0d82a875011500bd1e974446b39fc |
| `related` | ADR-0054 step 3, `#1051` |

##### Requirement {#arch.resolution.requirement-4}

`PositionIndex` is the one byte-position-keyed lookup: rebuilt from a parsed snapshot, never persisted, never a semantic input. `BindingSpans` is a transient construction-time bridge; every durable resolved artifact (`ResolutionMap`, the frozen IR) is keyed by identity, not position.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0054 (2026-09-10 amendment) |

##### Requirement {#arch.resolution.requirement-5}

The identity walk covers every body of code, including a module's bare top-level statements (walked as one block under a per-module owner), and maps a top-level declaration's own span to its `SymbolId`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | ``metel-frontend`` |
| `specified by` | `#resolution` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | cf5f79ec5df599d1a56643c1d1ce895f76d76544 |
| `related` | ADR-0054, `#1570` |

</details>

## Known limitations

<!-- records:limitations -->
