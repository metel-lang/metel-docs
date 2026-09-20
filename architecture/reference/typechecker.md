# Type Checker

The type checker occupies the inference and construction stages of the Atlas
pipeline. It turns resolved source into typed IR: inference establishes facts and
construction consumes those facts without re-performing name lookup.

Start with [Type Inference](../spec/type-inference.md) to understand constraint
solving, then [Type Construction](../spec/type-construction.md) for the typed IR
and diagnostic boundary. Each requirement’s **Implements** and **Verified by**
fields are generated from source and test citations in metel-core; this page does
not duplicate that inventory.

For the whole pipeline boundary, see the [architecture overview](../architecture.md).
