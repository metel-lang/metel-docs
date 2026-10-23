# Type Construction {#type-construction}

The pass that builds the typed IR from [Type Inference](type-inference.md)'s results: `typechecker::construction` (~8,050 lines across `typechecker/construction.rs` and `typechecker/construction/{declarations,expressions,calls,patterns,narrowing}.rs`), `typed_ast/` (748 lines, the typed IR itself), and the typechecker's shared support consumed by construction — `registry.rs`, `projections.rs`, `overload.rs`, `conversions.rs`, `object_safety.rs`, `handoff.rs` (~3,500 lines). ~12,300 lines total. Owning crate: `metel-frontend`. This section consumes [Type Inference](type-inference.md)'s output; it does not re-derive it.

## Model

Construction turns solved facts into the typed program consumed by move checking,
elaboration, and evaluation. It processes modules in dependency order and carries
their exported schemes forward ([module handoff](#arch.type-construction.requirement-1)).
Where earlier stages resolved an identity, construction preserves it on typed nodes
instead of replacing it with another name lookup ([identity stamping](#arch.type-construction.requirement-2)).

It is also the last place to enforce rules whose operands must already be concrete:
ascriptions disappear after guiding construction ([ascriptions](#arch.type-construction.requirement-6)),
operator and import diagnostics retain their distinct meanings
([operators](#arch.type-construction.requirement-7), [visibility](#arch.type-construction.requirement-8)),
and defaults, overload selections, and generic shape recovery become explicit typed
facts ([defaults](#arch.type-construction.requirement-9), [overloads](#arch.type-construction.requirement-10),
[generic reconstruction](#arch.type-construction.requirement-12)).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.type-construction.requirement-1}

`check_graph` typechecks a normalized module graph in topological order, running inference then construction per module, and accumulates each module's exported schemes in `GlobalExports` so later modules import them without re-inferring.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 2c95c6d9c5f131d86fa08889153355b451e12c9e |
| `related` | ADR-0022 |

##### Requirement {#arch.type-construction.requirement-2}

Construction stamps the typed IR with the identities the frontend already produced (`FieldId`/`VariantId` member ids, the span-to-`BindingId` bridge) through a `FrozenIdentity` bundle in `check_graph_with_report`; callers that pass `None` get every id as `None`, so construction degrades gracefully.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 69cfa63c874aa18a07d0aafaea58ac8357084211 |
| `related` | `arch.resolution.requirement-2`, `arch.resolution.requirement-3`, ADR-0054, `#1051`, `#1052` |

##### Requirement {#arch.type-construction.requirement-3}

Opaque return variables are validated at constraint-composition time, not only against the final substitution: when an opaque-return marker resolves directly to a concrete type, inference reports `T0018`, and construction must not reintroduce the concrete identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 945b99728c0dfff47ec0a42ae9d2a2ff4f6c1b72 |
| `related` | ADR-0044, RFC-0037 |

##### Requirement {#arch.type-construction.requirement-4}

The typechecker treats `[T]` as `Copy` unconditionally, as a deliberate `InferType::Array` special case that does not inspect the element type; other array-aspect eligibility stays conditional on the element through ordinary stdlib impl and bound machinery.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 8ed18533e08f605e0df6c188f1d30797fb72171f |
| `related` | ADR-0046, RFC-0126 |

##### Requirement {#arch.type-construction.requirement-5}

Until destructors run, a `std::core::Drop` impl may declare only an empty `drop` body: construction identifies the standard aspect by declaring module (a same-named user aspect is unaffected) and rejects a non-empty body with `T0001`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 945b99728c0dfff47ec0a42ae9d2a2ff4f6c1b72 |
| `related` | ADR-0047, RFC-0071 §9c, `#261` |

##### Requirement {#arch.type-construction.requirement-6}

Type ascriptions constrain inference and construction but are erased from typed IR: construction builds the inner expression using the resolved annotation as context instead of emitting a runtime no-op `TypedExpr::Ascribe` node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 08f7f2e7a381fffe4a6b24f19231a55ea4b8bddd |
| `related` | ADR-0009 |

##### Requirement {#arch.type-construction.requirement-7}

Operand legality is checked once operand types are resolved: arithmetic and unary negation accept numeric or `Never` operands, ordering comparisons also accept `Str`, and construction reports `T0005` rather than leaving invalid operator shapes for evaluation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 945b99728c0dfff47ec0a42ae9d2a2ff4f6c1b72 |
| `related` | ADR-0017, `T0005` |

##### Requirement {#arch.type-construction.requirement-8}

Import visibility is diagnosed while building import schemes, where the full module graph is known: name resolution records import bindings without collapsing a private-item error into a missing-item one, so construction reports `T0009` (visibility) apart from `T0003` (absence).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0024, `T0003`, `T0009` |

##### Requirement {#arch.type-construction.requirement-9}

Aspect default methods are materialized as typed methods before evaluation: inference collects an impl's inherited defaults and construction emits a typed body for each, except that negative impls acquire none, so runtime dispatch never evaluates untyped default-method syntax.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6469705aaeb2aefd7c60ead845b69e7b6c8dcab4 |
| `related` | ADR-0034 |

##### Requirement {#arch.type-construction.requirement-10}

Free-function overload selection is exact-match, and construction stamps the selected callable's `SymbolId` on the typed call, an id derived from the program and so identical on every compilation; the runtime dispatches it through its symbol-value registry, and overload sets stay module-local.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | fdf9591ce7923f93c5974ae00d281b7a7d20343d |
| `related` | ADR-0038, `arch.evaluation.requirement-2`, `LIMIT-TYPE-CONSTRUCTION-002` |

##### Requirement {#arch.type-construction.requirement-11}

At a generic struct literal or field access, construction instantiates the declared raw field template with the receiver's resolved type arguments; it does not cache one concrete field type under the generic declaration's surface name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0012 |

##### Requirement {#arch.type-construction.requirement-12}

Generic runtime reconstruction recovers a struct or enum's type arguments from its typed field values against the declared field templates when the value carries no argument list; this is best-effort for values whose fields reveal no parameter, rather than storing generic metadata on every value.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#type-construction` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 41b0f74be0c6e648506cce4821b4d76b2f41e6f8 |
| `related` | ADR-0043 |

</details>

## Known limitations

<!-- records:limitations -->
