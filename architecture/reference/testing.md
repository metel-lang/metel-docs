# Testing the Architecture

Architecture claims are verified from the test side. A Rust unit test places an
`arch-verifies` annotation immediately before its `#[test]` function; a source
fixture records `arch_verifies` in its TOML sidecar. The Atlas generator collects
those backward citations into the relevant claim’s **Verified by** field.

Production Rust uses `arch-implements` immediately before the item implementing a
claim. Both citation kinds are required unless the claim records the corresponding
reviewable exemption. This keeps test and implementation evidence close to the
code that owns it, while readers see it where the claim is explained.

The [Architecture Spec pages](../architecture.md) hold the canonical claims; this page only explains where their evidence comes from.
