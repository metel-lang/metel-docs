---
id: LIMIT-MOVE-CHECK-002
title: "Move-check skips generic bodies whose placeholder lacks a row bound or bound methods"
summary: "Under `--move-check`, a generic body that reads a row-bound field or uses some bound methods is skipped with a warning, so a use-after-move there passes."
scope: "architecture/spec/move-check.md#move-check"
owner: metel-frontend
discovered_by: "metel-core#1212 limitation analysis; `move-check-count` corpus totals (21 user and 30 embedded-std skipped generic bodies)"
disposition: known
review: null
---

## Limitation

Move-check analyses a generic body by constructing it against symbolic
arguments, one `__metel_move_check_generic_N` placeholder per generic
parameter. The placeholder carries no row bound, and some bound-provided
methods are not registered on it, so a body that reads a row-bound field
(`value.y` with `T: { y: i64, .. }`) or calls a method supplied by a
`match`/`extend` bound cannot be constructed. Move-check then records the body
as skipped (`record_skipped_generic_body`) and prints a warning instead of
analysing it. Reproduced against current `develop`:

```metel
fun f<record T: { y: i64, .. }>(value: T) -> (T, T, i64) {
    let n := value.y;
    let a := value;
    let b := value;
    (a, b, n)
}
```

```
warning: move checking could not analyze generic body …: [I0001] internal error: no field `y` on `__metel_move_check_generic_17`
```

exit status 0. Without the `value.y` line the same body is analysed and the
second `let` is rejected (`T0019`).

## Impact

Under `--move-check`, a use-after-move inside a skipped generic body is not
reported; only the warning is printed and the run succeeds. Move-check is
opt-in (`LIMIT-MOVE-CHECK-001`), so the exposure is limited to programs that
use it. The symptom is tracked as `metel-core#1226`.

## Affects

- `arch.move-check.requirement-1`
- `metel-frontend/src/pipeline/move_check/mod.rs` (`generic_sample_args`, `record_skipped_generic_body`)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/move_check/mod.rs::generic_sample_args`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/move_check/mod.rs#L521)
- [`metel-frontend/src/pipeline/move_check/mod.rs::record_skipped_generic_body`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/move_check/mod.rs#L1676)
<!-- limit.py:markers:end -->

## Resolution

None yet; `metel-core#1226`. Either the placeholder learns the row bound and
the bound's methods, or a skip becomes a hard failure under `--move-check`.
