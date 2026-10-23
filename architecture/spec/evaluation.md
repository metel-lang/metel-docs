# Evaluation {#evaluation}

The tree-walk over `ElaboratedModuleGraph` to program output. Owning crate: `metel-interpreter`. Defined in `evaluator/` (`mod.rs`, `call.rs`, `display.rs`, `lvalue.rs`, `pattern.rs`, `type_of.rs`, `builtins.rs`) and `pipeline.rs` (stage orchestration).

## Model

Evaluation executes the elaborated graph with identity-keyed lexical frames. A local
binding, closure capture, and module-level value share cells only when the earlier
pipeline deliberately established that relationship; spelling is not a fallback
semantic key ([environment](#arch.evaluation.requirement-1)). The runtime registry
extends the same principle to callable and nominal dispatch
([registry](#arch.evaluation.requirement-2)).

Values retain language-level behaviour rather than exposing evaluator shortcuts:
built-in sum types use the common enum representation
([enum values](#arch.evaluation.requirement-3)); receiver modes determine mutation
visibility ([receivers](#arch.evaluation.requirement-4)); and arrays copy at binding
boundaries ([array values](#arch.evaluation.requirement-5)). Runtime reconstruction,
dynamic aspects, and error call stacks are explicit mechanisms, not hidden evaluator
fallbacks ([generic calls](#arch.evaluation.requirement-7), [dynamic aspects](#arch.evaluation.requirement-8),
[call stacks](#arch.evaluation.requirement-6)).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.evaluation.requirement-1}

`Environment` is keyed entirely by `LocalId`, not name: two distinct `LocalId`s never alias, and no name-map fallback exists. Each module evaluates in its own isolated `Environment`, seeded from its already-evaluated dependencies' environments.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | c5619cae663b522b9c41aaa04f5a82788394dbbe |
| `related` | `arch.resolution.requirement-1`, `arch.resolution.requirement-2`, ADR-0029, ADR-0054, `#1052a`/`#1052b` series |

##### Requirement {#arch.evaluation.requirement-3}

`Perhaps` and `Result` are ordinary `Value::Enum { name, variant, fields, .. }` values with no dedicated `Value` variants; name-specific handling is confined to `display.rs`, the built-in constructors, and the `for`-loop's end check on `Perhaps::None`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | fa9d787ff51e4383f6b09366a6b987da6add9b91 |
| `related` | ADR-0028, `arch.evaluation.requirement-2` |

##### Requirement {#arch.evaluation.requirement-4}

Method dispatch preserves the typed AST's receiver mode: value receivers use the ordinary call path, `&self` a read-only view, and `&mut self` shares the caller's receiver cell into the method frame, so mutations, including nested-field ones, are immediately visible.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | c5619cae663b522b9c41aaa04f5a82788394dbbe |
| `related` | ADR-0036, RFC-0044 |

##### Requirement {#arch.evaluation.requirement-5}

Array values use value semantics at evaluator binding and assignment boundaries: `Environment::define` and `Environment::set` deep-clone their stored value, recursively cloning arrays and nested aggregate contents rather than allowing an ordinary assignment to create a mutable array alias.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | c5619cae663b522b9c41aaa04f5a82788394dbbe |
| `related` | ADR-0007 |

##### Requirement {#arch.evaluation.requirement-6}

The evaluator maintains call frames in thread-local storage. Call entry pushes its function name and source call-site, normal and error exits pop it, and diagnostic construction reads the resulting stack without adding a stack parameter through every evaluation helper.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | c5619cae663b522b9c41aaa04f5a82788394dbbe |
| `related` | ADR-0008 |

##### Requirement {#arch.evaluation.requirement-7}

Generic functions and let-polymorphic closures retain an untyped body plus typechecking context at runtime. A call reconstructs the body with the call-site types before evaluation, rather than storing one incorrectly monomorphic typed body for all instantiations.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter`, `metel-frontend` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 5f038b189cb67c5ec40e51d16a3e11a831a4535e |
| `related` | ADR-0010, ADR-0011, `LIMIT-EVALUATION-001` |

##### Requirement {#arch.evaluation.requirement-8}

`dyn Aspect` values are an explicit `Value::DynAspect` wrapper holding the erased value and its resolved concrete type and principal-aspect identities, introduced by typed `DynCoerce` nodes; `value_to_type` rebuilds the dyn type from that metadata without exposing the concrete value.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter`, `metel-frontend` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | d05bbfd47ae51437f565e0142a58f8e8a950d114 |
| `related` | ADR-0053, RFC-0008 |

##### Requirement {#arch.evaluation.requirement-2}

`RuntimeRegistry` dispatches struct/enum entries and function values by stable `SymbolId`, not by name at call time. Only `type_ids` (name to `SymbolId`) and `pattern_methods` (receivers with no `type_id`) stay name-keyed by design; the no-semantic-lookup check does not yet cover the registry.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | d05bbfd47ae51437f565e0142a58f8e8a950d114 |
| `related` | `arch.resolution.requirement-1`, `tools/check_no_semantic_name_lookup.py` |

</details>

## Known limitations

<!-- records:limitations -->
