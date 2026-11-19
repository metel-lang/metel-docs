# Audit of the 76 GAP and LIMIT records

Supports ADR-0070. Taken 2026-11-19 against `develop`; issue states are from GitHub the same day (`O` open, `C` closed, `M` merged).

Each record is assigned to what would replace it. No record was found that needs its own record kind.

| Replacement | Records |
|---|---:|
| Delete (resolved or superseded) | 29 |
| Marker + issue (planned, in flight) | 14 |
| Open question (issue labelled needs-design) | 11 |
| Re-track or close (known, every tracking issue closed) | 9 |
| Implementation note (ADR consequence or architecture requirement) | 7 |
| Spec prose (a boundary of the language) | 6 |

## Delete (resolved or superseded) (29)

- `GAP-DECLARATIONS-006` (resolved) `via` stated a flow for `Copy` only [#2069:M #2067:C]
- `GAP-TYPES-003` (resolved) There is no nominal record kind, so named records are unavailable [#1303:M #1300:C]
- `GAP-TYPES-004` (resolved) A blanket row-conditional aspect impl's body cannot require an aspect of every field 
- `GAP-TYPES-006` (resolved) A generic body cannot construct or consume a row remainder [#1399:C]
- `LIMIT-DECLARATIONS-001` (resolved) `record` declarations are not implemented [#1300:C #1303:M]
- `LIMIT-EVALUATION-002` (superseded) Cross-module mutual recursion is not supported [#189:C]
- `LIMIT-EVALUATION-006` (resolved) RFC-0167's error-code reclassification and main-entry Legality Rule are not implemented [#991:C #986:C #989:C]
- `LIMIT-EVALUATION-007` (resolved) A record rest pattern's remainder kept its record brand at runtime, so aspect dispatch ign [#1446:C]
- `LIMIT-MOVE-CHECK-002` (resolved) Move-check skips generic bodies whose placeholder lacks a row bound or bound methods [#273:C]
- `LIMIT-NAME-RESOLUTION-001` (resolved) std::core had no physical module file (resolved by ADR-0039) 
- `LIMIT-NAME-RESOLUTION-002` (resolved) Overload SymbolIds come from a process-global counter that is never reset [#1546:C #1551:M]
- `LIMIT-NAME-RESOLUTION-003` (resolved) The SymbolId space is split between three allocators by convention, with no cross-check [#1542:C #1546:C #1548:M]
- `LIMIT-NAME-RESOLUTION-004` (resolved) Builtin SymbolIds are a hard-coded list of 21 names; other std declarations are numbered p [#1542:C #1546:C #1548:M #1559:C]
- `LIMIT-NAME-RESOLUTION-005` (resolved) Symbol identity is a (module, name-string) key, so distinct declarations can share one Sym [#1560:C #1571:C #1228:C #1322:C #1229:C]
- `LIMIT-PARSING-001` (resolved) The dynamic array type's RFC-0171 spelling (`[T]`) does not parse yet [#1291:C]
- `LIMIT-TYPE-CONSTRUCTION-004` (resolved) Construction finds module-level values and their schemes by name [#1604:C #1608:M #1609:M #1610:M]
- `LIMIT-TYPE-INFERENCE-001` (superseded) `?` error coercion requires an explicit From impl [#13:C]
- `LIMIT-TYPE-INFERENCE-004` (resolved) `List<T>` iteration [#871:C]
- `LIMIT-TYPE-INFERENCE-005` (resolved) TypeVar identity is a global number, and generator ranges are kept apart by hard-coded off [#1541:C]
- `LIMIT-TYPE-INFERENCE-008` (resolved) Field-wise Clone is not entailed for a borrowed open row [#1422:M #1412:C #1302:C]
- `LIMIT-TYPE-INFERENCE-009` (resolved) A partial nominal residual cannot be coerced to a row-conditional dyn aspect [#1422:M #1413:C]
- `LIMIT-TYPE-INFERENCE-010` (resolved) A transparent public alias omitted its nominal type dependency [#1422:M #1414:C]
- `LIMIT-TYPE-INFERENCE-011` (resolved) A field-wise Clone grant does not entail Clone for an open-row record [#1422:M #1420:C #273:C]
- `LIMIT-TYPE-INFERENCE-012` (resolved) Field-wise Clone is unavailable for records imported from another module [#1422:M #1421:C]
- `LIMIT-TYPE-INFERENCE-013` (resolved) A private free function still infers its signature; RFC-0193 requires it written 
- `LIMIT-TYPE-INFERENCE-014` (resolved) A local function still sees the locals of its enclosing function; RFC-0195 says it does no 
- `LIMIT-TYPES-001` (resolved) RFC-0121 open rows were incomplete [#1301:C #1306:C #1384:M]
- `LIMIT-TYPES-002` (resolved) RFC-0123 field-wise row constraints were incomplete [#1302:C #1364:C]
- `LIMIT-TYPES-004` (resolved) RFC-0173 generic-body checking was incomplete [#1364:C]

## Marker + issue (planned, in flight) (14)

- `GAP-DECLARATIONS-002` (planned) Aspect implementations may not safely widen a method's generic constraints [#895:O]
- `GAP-DECLARATIONS-004` (planned) `let` and `var` bindings are not hoisted, so a function cannot use a later closure binding [#933:O]
- `GAP-DECLARATIONS-005` (planned) `derivable` is a property only std aspects have, and the derivations are written by the co [#799:O #1829:O]
- `GAP-DECLARATIONS-007` (planned) A direct call among several impls of one aspect is not resolved by its expected type [#2018:O]
- `GAP-FUNCTIONS-002` (planned) `Callable<A, B>` does not exist, so a function type cannot be bounded by an aspect [#923:O]
- `GAP-FUNCTIONS-003` (planned) Written function types are move-only, with no `copy` qualifier or `Erased` state yet [#936:O]
- `GAP-FUNCTIONS-006` (planned) A `let`-bound closure cannot call itself [#1667:O]
- `GAP-FUNCTIONS-007` (planned) A closure cannot name a type parameter, a bound or a row fact [#1668:O]
- `GAP-OWNERSHIP-001` (known) No borrow checking: reference exclusivity and duration are not enforced [#1293:O]
- `GAP-OWNERSHIP-002` (planned) A deeper move does not narrow the enclosing value's row [#900:O]
- `GAP-OWNERSHIP-003` (planned) A field cannot be moved out of a `Drop` type, even where its destructor would not need it [#949:O]
- `GAP-OWNERSHIP-004` (planned) Structural `Copy` for named types and their residuals is a compiler rule, not something th [#1823:O #1834:O]
- `LIMIT-EVALUATION-005` (planned) Destructor invocation is not implemented; only empty `drop` bodies are accepted [#261:O]
- `LIMIT-TYPES-003` (planned) Record `Display` is a runtime built-in, not Metel code [#1340:O #1338:C]

## Open question (issue labelled needs-design) (11)

- `GAP-DECLARATIONS-003` (known) No `Ord` or `Hash` aspect exists, so no type has ordering or hashing impls 
- `GAP-EXPRESSIONS-001` (known) A record rest pattern cannot borrow the remainder through a reference 
- `GAP-FUNCTIONS-001` (known) Free-function overloading is implemented but the Language Spec does not describe it 
- `GAP-FUNCTIONS-004` (known) `?` is defined for the core `Result` and `Option` only; there is no `Try` aspect [#1637:O]
- `GAP-MODULES-003` (known) Top-level `let` and `var` bindings cannot be exported 
- `GAP-TYPES-002` (known) The storage model of `List<T>` and its boundary with `T[]` and `[T; N]` is not specified 
- `GAP-TYPES-005` (known) No spelling for an operator on a generic parameter 
- `GAP-TYPES-008` (known) A record literal accepts at most one row spread 
- `GAP-TYPES-009` (known) Tuples have no rest pattern or spread over their numeric-label row 
- `LIMIT-TYPE-INFERENCE-002` (known) Field access needs a concrete receiver type at the access site 
- `LIMIT-TYPE-INFERENCE-003` (known) `..` is not supported in an anonymous record pattern 

## Re-track or close (known, every tracking issue closed) (9)

- `GAP-DECLARATIONS-001` (known) Tuples cannot implement an aspect [#1306:C #239:C #1217:C]
- `GAP-FUNCTIONS-005` (known) Explicit type arguments are not supported on a function with a row parameter [#1647:C]
- `LIMIT-COHERENCE-001` (known) `extend<record T: .{...}> T: Aspect` is accepted, then never applies [#1241:C #239:C]
- `LIMIT-PATH-NORMALIZATION-001` (known) `root::`/`super::` are rejected in expression position when the target is declared directl [#1221:C]
- `LIMIT-RESOLUTION-002` (known) Inference-time type lookup falls back to a name-approximate, cross-module search [#1222:C]
- `LIMIT-TYPE-CONSTRUCTION-001` (known) Call::callee_id falls back to name dispatch for first-class functions [#542:C]
- `LIMIT-TYPE-CONSTRUCTION-002` (known) Overload sets are not exportable across modules [#258:C]
- `LIMIT-TYPE-CONSTRUCTION-003` (known) `==` and `!=` reject non-primitive operands instead of dispatching through `Eq` [#263:C]
- `LIMIT-TYPE-INFERENCE-007` (known) Type checking time grows super-linearly with the number of functions in a module [#1232:C]

## Implementation note (ADR consequence or architecture requirement) (7)

- `LIMIT-ELABORATION-001` (known) ElaboratedModuleGraph's field is fully public, unlike NormalizedModuleGraph's 
- `LIMIT-EVALUATION-001` (accepted) Generic function dispatch re-constructs on every call 
- `LIMIT-EVALUATION-003` (known) RuntimeRegistry is not fully covered by the resolution-freeze checker 
- `LIMIT-EVALUATION-004` (known) The evaluator is a deliberate PoC, not the target implementation shape 
- `LIMIT-MOVE-CHECK-001` (accepted) Closure move-check is always-on while general move-check stays opt-in [#267:O]
- `LIMIT-RESOLUTION-001` (accepted) Resolved-identity model is in-memory only 
- `LIMIT-TYPE-INFERENCE-006` (known) Type checking is sequential by construction: one shared generator, one export generator, R 

## Spec prose (a boundary of the language) (6)

- `GAP-MODULES-001` (known) Module graphs may not be cyclic, so modules cannot be mutually dependent 
- `GAP-MODULES-002` (accepted) A directory cannot be a module on its own: there is no `mod.mtl` equivalent 
- `GAP-TYPES-001` (known) No higher-rank polymorphism 
- `GAP-TYPES-010` (accepted) A function cannot return an open record while hiding its extra fields 
- `GAP-TYPES-011` (accepted) A written function type cannot say it accepts any record with at least these fields 
- `GAP-TYPES-012` (accepted) A record or struct field cannot have an open-record type with an anonymous tail 

## Evidence of staleness found by running the records' own reproductions

- `LIMIT-TYPE-INFERENCE-003` (known): `..` in an anonymous record pattern now compiles and runs.
- `LIMIT-TYPE-INFERENCE-002` (known): the reproduction now fails with `T0010` (RFC-0193), not the recorded `T0002`.
- `LIMIT-COHERENCE-001` (known): the reproduction now fails with `T0001`, not the recorded `T0002`.
- Only 18 of 76 records contain a runnable ```metel block, and 7 of those have no `main`.
