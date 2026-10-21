# Move Check {#move-check}

## Overview

Move checking is a validation pass over the typed module graph that rejects programs
which use a value after its ownership has moved elsewhere. It answers one question for
every non-`Copy` value: *can this use still observe the value, or has an earlier use
already consumed it, in whole or in part?* A program that passes cannot read a moved
value, move a field out of a type whose destructor needs it intact, or move out of a
reference, an array element or a borrowed view.

The pass is **opt-in**. It runs only when requested (`--move-check` on the CLI,
`RunOptions::move_check` in the library, the `move_check` option in a fixture's
sidecar), and a run without it executes with no ownership check beyond the closure
capture rules that type checking always applies
([closure captures](#arch.move-check.requirement-3)). It is a **consumer, not an
analyser of source**: it reads the typed graph and the retained definition-time facts that
earlier stages produced, and it never infers or re-checks types.

```text
parse → resolve names → normalise paths → coherence → type check ─┬→ move check (opt-in)
                                                                   ├→ elaborate
                                                                   └→ evaluate
```

| | |
|---|---|
| **Position** | After type checking, before elaboration and evaluation. A failure stops the run before anything executes. |
| **Input** | The typed module graph, including each generic definition's retained abstract signature and body, and the type registry. |
| **Output** | A `MoveCheckReport` (violations, analysed and unanalysed generic bodies). `check_graph` turns it into one error: `T0019` for a violation, `I0011` for an incomplete analysis. |
| **Owner** | `metel-frontend`: `move_check/` for the pass, `ownership/` for the shared place and flow-state algebra. |
| **Guarantee on success** | Every body, generic or not, was analysed and no analysed body violates the move rules. |

## Boundaries

**What it consumes.** The typed graph from type checking; for each generic free function,
impl method and let-bound polymorphic closure, the abstract signature and typed body
retained by definition-time checking
([retained bodies](#arch.move-check.requirement-4)); and the type registry, to decide
`Copy` and `Drop` for concrete types. Everything else it needs is carried by those
artifacts.

**What it shares.** Two components are deliberately analysis-neutral so that no second
analysis re-derives them differently:

- **Places** ([place algebra](#arch.move-check.requirement-2)): a binding root plus a
  path of projections (field, tuple slot, dereference, opaque index). A place carries no
  move-specific state, so a future borrow checker can walk the same places.
- **Flow state** (`FlowState`/`MoveRecord`): which places are currently moved out,
  joined across branches and widened across loop back edges. It holds no diagnostics.
  Move checking turns it into violations; type construction reads the same transitions
  to narrow a binding's static type after a partial move and widen it on reassignment
  ([ADR-0045](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0045-loop-carried-moves-via-back-edge-accumulation.md)).

**What it does not do.**

| Concern | Where it lives |
|---|---|
| Inferring or checking types, including the choice of a generic's bounds | Type checking; move checking only consumes the result. |
| Closure capture legality (capture lists, `once`, `var`, the definition-time `Copy` grant) | Type checking, unconditionally ([closure captures](#arch.move-check.requirement-3), [capture grant](#arch.move-check.requirement-7)). |
| Borrow checking: lifetimes, aliasing of `&`/`&var` | Not implemented. Move checking only enforces that a reference grants access, never ownership. |
| Collecting concrete instantiations, caching instances, specialization | Outside this pass. Move checking never needs a concrete instantiation. |
| Being on by default | Opt-in today; enabling it by default is a separate decision. |
| Reporting every violation | `check_graph` reports the first; `collect_graph_violations` returns all of them for tools. |

## Responsibilities

### What counts as a move

A value is **consumed** where ownership transfers: an initialiser, a by-value argument or
receiver, a returned or `break`-carried value, a field of an aggregate literal, and an
owned closure capture. It is **observed** where it is only read: a borrow, a comparison, a
projection base, an argument passed by reference. Consuming a `Copy` value moves nothing.
Consuming a non-`Copy` place records it as moved, and consuming a *part* of a place
records only that part, so a sibling field stays usable.

### The rules it enforces

Each rule produces one violation kind; `check_graph` reports the first as `T0019`.

| Violation | Meaning |
|---|---|
| Use after move | A place is read after it, or an enclosing place, was consumed. |
| Partial move used as whole | The whole value is used after one of its fields or elements was consumed. |
| Partial move of a `Drop` type | A field is moved out of a type whose destructor needs it intact. |
| Array element move | A non-`Copy` element is moved out of an array by a dynamic index. |
| Borrowed array element move | A non-`Copy` element is moved out of a `T[]` view. |
| Moved `&var` without reborrow | A mutable reference was moved by a use that was not a reborrow, then used. |
| Move out of a reference | A value is moved out of something only reachable through a reference. |

### How control flow is treated

- **Branches** (`if`, `match`): a place moved in *any* arm is moved afterwards; the states
  are joined, not intersected.
- **Reassignment** re-initialises a moved binding: writing to it is not a use, so
  move-then-replace is accepted.
- **Divergence** (`return`, `break`, `continue`, and a `loop` with no reachable `break`)
  removes the paths that cannot fall through, so a move on a path that always exits is not
  seen by later code.
- **Loops** are analysed to a fixed point. The state at the bottom of the body and at
  every `continue` is fed back to the entry and the body is walked again, so a move in
  one iteration is seen by the next. Paths that leave through `break` or `return` are
  excluded from the back edge, so `loop { consume(x); break; }` is accepted. Only the
  final pass reports, so a diagnostic appears once, and a diagnostic for a move from an
  earlier iteration says so. The pass count is bounded (8); a cascade needing more would
  lose later findings, which is a precision limit and not a missed body.

### Deciding `Copy` and `Drop`

For a concrete type the registry answers. For a generic value the answer comes from the
definition's retained facts, never from a sample instantiation
([Copy from declared bounds](#arch.move-check.requirement-8)): an unbounded parameter is
not `Copy`, a parameter declared `T: Copy` is, and an unknown row tail is preserved
rather than treated as an empty record. A residual (a struct after a partial move) never
carries `Drop`, because partially moving a `Drop` type is itself a violation.

## Mode of operation

**Enabling.** The option is off by default. The CLI flag, `RunOptions`, the tooling
analysis option and a fixture's `move_check = true` all select the same pass over the same
graph. The orchestrator runs it once, after type checking, in every entry point
(file, source and fixture runs). Tooling that analyses a partially valid project runs it
over whatever modules type-checked and layers the result on the other diagnostics.

**Traversal.** `collect_graph_violations` walks each module's declarations in order with a
fresh flow state per module and per function body.

- A **concrete** function or method body is walked on the typed AST.
- A **generic** body (free function, impl method, let-bound polymorphic closure) is walked
  from its retained abstract body, with its parameters bound by identity and its declared
  facts in scope. An unused generic definition is checked like any other.
- A **closure** body is walked with its own flow state; the captures it takes at creation
  are consumed or observed in the enclosing state according to their capture mode.
- Standard-library bodies embedded in the compiler are analysed too, but a violation
  located inside them is never reported to the user.

**Reporting.** Violations are collected in a `MoveCheckReport`, with the use and the
original move as spans, so a message can point at both. `check_graph` converts the first
user-visible violation to `T0019`; a body left unanalysed becomes `I0011` and is never
reported as a violation.

### Generic bodies

A generic body is checked against what its **definition** declares, never against a
concrete instantiation. Definition-time checking retains an abstract signature, the
declared facts of each parameter, and a typed body (operations, places, control flow,
receiver and argument ownership modes). Move checking consumes that artifact directly;
it never re-runs inference or re-type-checks source AST, and no generic body is
reconstructed against invented arguments
([no reconstruction](#arch.move-check.requirement-10)). The design and its boundary with
specialization are in
[ADR-0063](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0063-abstract-generic-bodies.md).

Retained subtraction equations propagate field-wise `Copy` from a source row to its
remainder, including chains; every field-wise exception must be among the removed labels,
and a remainder's grant never proves that its source is `Copy`. Copy heads and a `Copy`
remainder compose into a `Copy` structural row, and an unproven alternative decomposition
cannot override a successful proof. Closed-source subtraction equations determine the
actual remainder fields, whose retained types decide `Copy`. Definition templates preserve
declared parameters that appear only in row facts without adding caller-visible
quantifiers, and method templates retain source names and inherited body grants without
changing call-site schemes. Borrowed `self` remains access rather than ownership. An
arithmetic or ordering operation on an unannotated parameter is retained as an observation
of its operands, not as a sampled operator
([operators](#arch.move-check.requirement-9)).

Array reads with retained `u64` indices preserve index evaluation throughout projection
chains and reject non-`Copy` moves through opaque-index places. Structural record patterns
retain typed fields, explicit discards, binding identities and owned remainders, including
unknown open tails; scrutinee inputs are evaluated once rather than once per projected
field. A named remainder consumes the source as a whole, while a pattern without one
consumes its named and explicitly discarded fields separately. Parameter-backed open
shapes require a typed row grant and an exact retained remainder equation; unknown tails
are preserved. See
[ADR-0060](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0060-symbolic-row-ownership-witnesses.md).

### Closures

Closure environment ownership is retained separately from callable axes and preserved
through direct local aliases and nested captures. Owned closure sources carry resolved
entry types from construction, so ownership analysis consumes these explicit captures even
if they are unused or shadowed
([ADR-0062](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0062-owned-capture-entry-types.md)).
A let-bound polymorphic closure is a generic definition with its own retained body
([closures](#arch.move-check.requirement-5)); a bare alias of a generic function
(`let g := f;`) introduces no body, and the function's own is analysed where it is
declared. A closure written without a capture list may capture a still-generic value only
if the definition grants `Copy`, whatever the instantiation.

### Completeness

Analysis is all-or-nothing per body. When an operation or entailment cannot be decided
from the retained facts, the body is recorded as unanalysed and the run fails with `I0011`,
a distinct error from the `T0019` use-after-move diagnostic
([completeness](#arch.move-check.requirement-6)). A passing `--move-check` run has
therefore analysed every generic body, including unused and embedded-standard-library
definitions, and a test over the whole integration corpus asserts that none is left
unanalysed. `I0011` is a safeguard against a regression or a future feature that lacks
ownership integration, not a normal outcome. Conditional variants whose flattened method
symbols collide are tracked by `LIMIT-NAME-RESOLUTION-005`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.move-check.requirement-1}

Move checking is off unless requested (`--move-check` / `RunOptions::move_check`). `check_graph` then rejects seven categories of move violation, reporting the first as `T0019`, and fails with `I0011` if any generic body cannot be analysed, so success means every body was checked.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | d8cb4c3c0582a18b0fd859c8c4ec95fde74db946 |
| `related` | RFC-0071, `#579` |

##### Requirement {#arch.move-check.requirement-2}

Places (a binding root plus a path of projections) carry no move-specific state: `place.rs` lives at the crate root, outside `move_check`, so a future borrow-check pass can analyse the same places without the two analyses disagreeing about partial moves.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 853b2feb32949cce5ac62e59c7e20060c9241be0 |
| `related` | RFC-0071 §9b, ADR-0035 (`TypedPlace` for assignment targets), ADR-0045 |

##### Requirement {#arch.move-check.requirement-3}

Closure capture legality holds with move checking off: type checking rejects unlisted non-`Copy` captures (`T0026`, judged at the definition when generic), consuming captures without `once` (`T0027`), mutating captures without `var` (`T0028`), and shared-access calls of mutating closures (`T0029`).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0052, RFC-0050, RFC-0134, RFC-0153 |

##### Requirement {#arch.move-check.requirement-4}

Definition-time checking retains an abstract signature and typed body for every generic free function, impl method and let-bound polymorphic closure; move checking consumes them directly and never re-type-checks source AST.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6c6828cdbc94434f2debbd7cc6dabbef1cb82ac6 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-5}

A let-bound polymorphic closure is a generic definition: it retains an abstract signature and body keyed by its own span, while a bare alias of a generic function introduces no body and is analysed through the function itself.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6c6828cdbc94434f2debbd7cc6dabbef1cb82ac6 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-6}

Under `--move-check`, a generic body that cannot be analysed is reported as `I0011`, an error distinct from `T0019`, so an incomplete analysis never authorizes execution and success means every body was checked.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-7}

A closure with no capture list may capture a still-generic value only if the definition grants `Copy`; an unbounded or inferred parameter is rejected with `T0026` at the definition, in every mode, whatever the instantiation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | RFC-0050, RFC-0134, `#273` |

##### Requirement {#arch.move-check.requirement-8}

Whether a generic value is `Copy` is decided from the definition's declared facts: an unbounded parameter or unknown row tail is never assumed `Copy`, and a declared `Copy` bound or proven field-wise grant is honoured.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0060, ADR-0063, `#273` |

##### Requirement {#arch.move-check.requirement-9}

An arithmetic or ordering operation on an unannotated parameter is retained in the abstract body without sampling an operand type, and its operands are observed rather than consumed.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | RFC-0173, ADR-0063, `#273` |

##### Requirement {#arch.move-check.requirement-10}

Move checking never reconstructs a generic body against invented concrete arguments: with the scheme environment removed, retained bodies are still analysed and the result is unchanged.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0063, `#273` |

</details>

## Known limitations

<!-- records:limitations -->
