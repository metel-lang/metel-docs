# Evaluator

Evaluation consumes elaborated typed IR. It executes modules in dependency order,
keeps module environments isolated, and dispatches using the identities recorded
by earlier stages rather than source-name lookup.

[Evaluation](../spec/evaluation.md) is the canonical reader-facing description of
those guarantees. Its generated **Implements** and **Verified by** fields link to
the exact metel-core items and tests, so this reference deliberately does not
maintain a parallel list of evaluator files.

See [Elaboration](../spec/elaboration.md) for the stage immediately before it.
