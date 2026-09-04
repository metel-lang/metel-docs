# Type System

Metel is statically and strongly typed. Types are checked at compile time. There are no implicit conversions.

## Primitive Types

| Type     | Description               | Example   |
|----------|---------------------------|-----------|
| `i64`    | 64-bit signed integer | `42` |
| `f64`    | 64-bit floating point | `3.14` |
| `boolean`| Boolean                   | `true`    |
| `String` | UTF-8 string              | `"hello"` |
| `Char`   | Unicode scalar value      | `'a'`     |
| `()`     | Unit — represents no value | `()`     |

The unit type `()` is only written explicitly when needed as a type parameter (e.g. `Result<(), Error>`). Functions that return nothing omit the `->` annotation entirely.

## Sized Numeric Types

> **Availability:** Since v0.8.0.

Metel provides exact-width numeric types for low-level and systems programming. `i64` and `f64` are the default integer and floating-point types in ordinary code.

**Signed integers:**

| Type  | Width  |
|-------|--------|
| `i8`  | 8-bit  |
| `i16` | 16-bit |
| `i32` | 32-bit |
| `i64` | 64-bit |

**Unsigned integers:**

| Type  | Width  |
|-------|--------|
| `u8`  | 8-bit  |
| `u16` | 16-bit |
| `u32` | 32-bit |
| `u64` | 64-bit |

**Floats:**

| Type  | Width  |
|-------|--------|
| `f32` | 32-bit IEEE 754 |
| `f64` | 64-bit IEEE 754 |

Sized literals use a suffix: `42i32`, `3.14f32`, `255u8`. All casts between sized numeric types are explicit (`as`). Array indices must be `u64`; indexing with an `i64` requires an explicit `as u64` cast.

**Unsuffixed literals are polymorphic.** When the expected type is known from context (annotation, function parameter, struct field, return type, or the other operand in arithmetic/comparison), an unsuffixed numeric literal [adopts that type automatically](#spec.types.sized-numeric-types.legality-3). When no context is available, the literal defaults to `i64` (integer) or `f64` (float).

```metel
let a: i32 := 10;          // 10 is i32
let b: u8  := 255;         // 255 is u8
let c: f32 := 1.5;         // 1.5 is f32

fun scale(x: f32, factor: f32) -> f32 { x * factor }
let r := scale(2.0, 3.0);  // both literals are f32

let x: i32 := 10i32;
let y := x + 5;            // 5 adopts i32 from x; y is i32
```

This also applies to `var` reassignment — the right-hand side of `m := expr` adopts `m`'s declared type:

```metel
var count: i32 := 0;
count := 99;               // 99 is i32
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.sized-numeric-types.legality-1}

The exact-width numeric primitive types are `i8`, `i16`, `i32`, `i64`, `u8`, `u16`,
`u32`, `u64`, `f32`, and `f64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgyX3NpemVkX251bWVyaWNfdHlwZXMubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gXHUyNTAwXHUyNTAwIFNpemVkIGludGVnZXIgbGl0ZXJhbHMgYW5kIGVxdWFsaXR5IFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCBhOiBpOCAgOj0gMTI3aTg7XG4gICAgbGV0IGI6IGkxNiA6PSAzMjc2N2kxNjtcbiAgICBsZXQgYzogaTMyIDo9IDIxNDc0ODM2NDdpMzI7XG4gICAgbGV0IGQ6IHU4ICA6PSAyNTV1ODtcbiAgICBsZXQgZTogdTE2IDo9IDY1NTM1dTE2O1xuICAgIGxldCBmOiB1MzIgOj0gNDI5NDk2NzI5NXUzMjtcbiAgICBsZXQgZzogdTY0IDo9IDE4NDQ2NzQ0MDczNzA5NTUxNjE1dTY0O1xuICAgIGxldCBoOiBmMzIgOj0gMS41ZjMyO1xuXG4gICAgYXNzZXJ0KGEgPT0gMTI3aTgpO1xuICAgIGFzc2VydChiID09IDMyNzY3aTE2KTtcbiAgICBhc3NlcnQoYyA9PSAyMTQ3NDgzNjQ3aTMyKTtcbiAgICBhc3NlcnQoZCA9PSAyNTV1OCk7XG4gICAgYXNzZXJ0KGUgPT0gNjU1MzV1MTYpO1xuICAgIGFzc2VydChmID09IDQyOTQ5NjcyOTV1MzIpO1xuICAgIGFzc2VydChnID09IDE4NDQ2NzQ0MDczNzA5NTUxNjE1dTY0KTtcbiAgICBhc3NlcnQoaCA9PSAxLjVmMzIpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIEFyaXRobWV0aWMgcHJlc2VydmVzIHR5cGUgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IHg6IGkzMiA6PSAxMGkzMiArIDVpMzI7XG4gICAgYXNzZXJ0KHggPT0gMTVpMzIpO1xuICAgIGxldCB5OiB1OCA6PSAyMDB1OCAtIDEwMHU4O1xuICAgIGFzc2VydCh5ID09IDEwMHU4KTtcbiAgICBsZXQgejogZjMyIDo9IDIuMGYzMiAqIDMuMGYzMjtcbiAgICBhc3NlcnQoeiA9PSA2LjBmMzIpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIENvbXBhcmlzb24gb3BlcmF0b3JzIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGFzc2VydCgxMGkzMiA8IDIwaTMyKTtcbiAgICBhc3NlcnQoMjU1dTggPT0gMjU1dTgpO1xuICAgIGFzc2VydCgxLjBmMzIgPCAyLjBmMzIpO1xuICAgIGFzc2VydCgxMDB1MTYgPD0gMTAwdTE2KTtcbiAgICBhc3NlcnQoNWk4ICE9IDZpOCk7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgRnJvbSBjYXN0czogc2l6ZWQgXHUyMTkyIGk2NCAvIGY2NCBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgZnJvbV9pODogIGk2NCA6PSA0Mmk4ICBhcyBpNjQ7XG4gICAgbGV0IGZyb21faTE2OiBpNjQgOj0gMTAwMGkxNiBhcyBpNjQ7XG4gICAgbGV0IGZyb21faTMyOiBpNjQgOj0gMTAwMDAwaTMyIGFzIGk2NDtcbiAgICBsZXQgZnJvbV91ODogIGk2NCA6PSAyMDB1OCAgYXMgaTY0O1xuICAgIGxldCBmcm9tX3UxNjogaTY0IDo9IDUwMDAwdTE2IGFzIGk2NDtcbiAgICBsZXQgZnJvbV91MzI6IGk2NCA6PSAxMjM0NTZ1MzIgYXMgaTY0O1xuICAgIGxldCBmcm9tX3U2NDogaTY0IDo9IDk5dTY0IGFzIGk2NDtcbiAgICBsZXQgZnJvbV9mMzJfdG9faTY0OiBpNjQgOj0gN2k4IGFzIGk2NDtcblxuICAgIGFzc2VydChmcm9tX2k4ICA9PSA0Mik7XG4gICAgYXNzZXJ0KGZyb21faTE2ID09IDEwMDApO1xuICAgIGFzc2VydChmcm9tX2kzMiA9PSAxMDAwMDApO1xuICAgIGFzc2VydChmcm9tX3U4ICA9PSAyMDApO1xuICAgIGFzc2VydChmcm9tX3UxNiA9PSA1MDAwMCk7XG4gICAgYXNzZXJ0KGZyb21fdTMyID09IDEyMzQ1Nik7XG4gICAgYXNzZXJ0KGZyb21fdTY0ID09IDk5KTtcbiAgICBhc3NlcnQoZnJvbV9mMzJfdG9faTY0ID09IDcpO1xuXG4gICAgbGV0IGZyb21faThfZjogIGY2NCA6PSA0Mmk4ICBhcyBmNjQ7XG4gICAgbGV0IGZyb21fZjMyX2Y6IGY2NCA6PSAxLjVmMzIgYXMgZjY0O1xuICAgIGFzc2VydChmcm9tX2k4X2YgPT0gNDIuMCk7XG4gICAgYXNzZXJ0KGZyb21fZjMyX2YgPT0gMS41KTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBGcm9tIGNhc3RzOiBpNjQgLyBmNjQgXHUyMTkyIHNpemVkIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCB0b191ODogIHU4ICA6PSAyMDAgYXMgdTg7XG4gICAgbGV0IHRvX2kzMjogaTMyIDo9IDQyICBhcyBpMzI7XG4gICAgbGV0IHRvX3UzMjogdTMyIDo9IDk5OSBhcyB1MzI7XG4gICAgbGV0IHRvX3U2NDogdTY0IDo9IDAgICBhcyB1NjQ7XG5cbiAgICBhc3NlcnQodG9fdTggID09IDIwMHU4KTtcbiAgICBhc3NlcnQodG9faTMyID09IDQyaTMyKTtcbiAgICBhc3NlcnQodG9fdTMyID09IDk5OXUzMik7XG4gICAgYXNzZXJ0KHRvX3U2NCA9PSAwdTY0KTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBOZWdhdGlvbiBvbiBzaWduZWQgdHlwZXMgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IG5lZ19pODogIGk4ICA6PSAtNDJpODtcbiAgICBsZXQgbmVnX2kzMjogaTMyIDo9IC0xMDAwaTMyO1xuICAgIGFzc2VydChuZWdfaTggID09IC00Mmk4KTtcbiAgICBhc3NlcnQobmVnX2kzMiA9PSAtMTAwMGkzMik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci90eXBlcy84Ml9zaXplZF9udW1lcmljX3R5cGVzLm10bCIsIm5hbWUiOiI4Ml9zaXplZF9udW1lcmljX3R5cGVzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.sized-numeric-types.legality-2}

Conversion between numeric types is written with an explicit `as` cast.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgyX3NpemVkX251bWVyaWNfdHlwZXMubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gXHUyNTAwXHUyNTAwIFNpemVkIGludGVnZXIgbGl0ZXJhbHMgYW5kIGVxdWFsaXR5IFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCBhOiBpOCAgOj0gMTI3aTg7XG4gICAgbGV0IGI6IGkxNiA6PSAzMjc2N2kxNjtcbiAgICBsZXQgYzogaTMyIDo9IDIxNDc0ODM2NDdpMzI7XG4gICAgbGV0IGQ6IHU4ICA6PSAyNTV1ODtcbiAgICBsZXQgZTogdTE2IDo9IDY1NTM1dTE2O1xuICAgIGxldCBmOiB1MzIgOj0gNDI5NDk2NzI5NXUzMjtcbiAgICBsZXQgZzogdTY0IDo9IDE4NDQ2NzQ0MDczNzA5NTUxNjE1dTY0O1xuICAgIGxldCBoOiBmMzIgOj0gMS41ZjMyO1xuXG4gICAgYXNzZXJ0KGEgPT0gMTI3aTgpO1xuICAgIGFzc2VydChiID09IDMyNzY3aTE2KTtcbiAgICBhc3NlcnQoYyA9PSAyMTQ3NDgzNjQ3aTMyKTtcbiAgICBhc3NlcnQoZCA9PSAyNTV1OCk7XG4gICAgYXNzZXJ0KGUgPT0gNjU1MzV1MTYpO1xuICAgIGFzc2VydChmID09IDQyOTQ5NjcyOTV1MzIpO1xuICAgIGFzc2VydChnID09IDE4NDQ2NzQ0MDczNzA5NTUxNjE1dTY0KTtcbiAgICBhc3NlcnQoaCA9PSAxLjVmMzIpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIEFyaXRobWV0aWMgcHJlc2VydmVzIHR5cGUgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IHg6IGkzMiA6PSAxMGkzMiArIDVpMzI7XG4gICAgYXNzZXJ0KHggPT0gMTVpMzIpO1xuICAgIGxldCB5OiB1OCA6PSAyMDB1OCAtIDEwMHU4O1xuICAgIGFzc2VydCh5ID09IDEwMHU4KTtcbiAgICBsZXQgejogZjMyIDo9IDIuMGYzMiAqIDMuMGYzMjtcbiAgICBhc3NlcnQoeiA9PSA2LjBmMzIpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIENvbXBhcmlzb24gb3BlcmF0b3JzIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGFzc2VydCgxMGkzMiA8IDIwaTMyKTtcbiAgICBhc3NlcnQoMjU1dTggPT0gMjU1dTgpO1xuICAgIGFzc2VydCgxLjBmMzIgPCAyLjBmMzIpO1xuICAgIGFzc2VydCgxMDB1MTYgPD0gMTAwdTE2KTtcbiAgICBhc3NlcnQoNWk4ICE9IDZpOCk7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgRnJvbSBjYXN0czogc2l6ZWQgXHUyMTkyIGk2NCAvIGY2NCBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgZnJvbV9pODogIGk2NCA6PSA0Mmk4ICBhcyBpNjQ7XG4gICAgbGV0IGZyb21faTE2OiBpNjQgOj0gMTAwMGkxNiBhcyBpNjQ7XG4gICAgbGV0IGZyb21faTMyOiBpNjQgOj0gMTAwMDAwaTMyIGFzIGk2NDtcbiAgICBsZXQgZnJvbV91ODogIGk2NCA6PSAyMDB1OCAgYXMgaTY0O1xuICAgIGxldCBmcm9tX3UxNjogaTY0IDo9IDUwMDAwdTE2IGFzIGk2NDtcbiAgICBsZXQgZnJvbV91MzI6IGk2NCA6PSAxMjM0NTZ1MzIgYXMgaTY0O1xuICAgIGxldCBmcm9tX3U2NDogaTY0IDo9IDk5dTY0IGFzIGk2NDtcbiAgICBsZXQgZnJvbV9mMzJfdG9faTY0OiBpNjQgOj0gN2k4IGFzIGk2NDtcblxuICAgIGFzc2VydChmcm9tX2k4ICA9PSA0Mik7XG4gICAgYXNzZXJ0KGZyb21faTE2ID09IDEwMDApO1xuICAgIGFzc2VydChmcm9tX2kzMiA9PSAxMDAwMDApO1xuICAgIGFzc2VydChmcm9tX3U4ICA9PSAyMDApO1xuICAgIGFzc2VydChmcm9tX3UxNiA9PSA1MDAwMCk7XG4gICAgYXNzZXJ0KGZyb21fdTMyID09IDEyMzQ1Nik7XG4gICAgYXNzZXJ0KGZyb21fdTY0ID09IDk5KTtcbiAgICBhc3NlcnQoZnJvbV9mMzJfdG9faTY0ID09IDcpO1xuXG4gICAgbGV0IGZyb21faThfZjogIGY2NCA6PSA0Mmk4ICBhcyBmNjQ7XG4gICAgbGV0IGZyb21fZjMyX2Y6IGY2NCA6PSAxLjVmMzIgYXMgZjY0O1xuICAgIGFzc2VydChmcm9tX2k4X2YgPT0gNDIuMCk7XG4gICAgYXNzZXJ0KGZyb21fZjMyX2YgPT0gMS41KTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBGcm9tIGNhc3RzOiBpNjQgLyBmNjQgXHUyMTkyIHNpemVkIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCB0b191ODogIHU4ICA6PSAyMDAgYXMgdTg7XG4gICAgbGV0IHRvX2kzMjogaTMyIDo9IDQyICBhcyBpMzI7XG4gICAgbGV0IHRvX3UzMjogdTMyIDo9IDk5OSBhcyB1MzI7XG4gICAgbGV0IHRvX3U2NDogdTY0IDo9IDAgICBhcyB1NjQ7XG5cbiAgICBhc3NlcnQodG9fdTggID09IDIwMHU4KTtcbiAgICBhc3NlcnQodG9faTMyID09IDQyaTMyKTtcbiAgICBhc3NlcnQodG9fdTMyID09IDk5OXUzMik7XG4gICAgYXNzZXJ0KHRvX3U2NCA9PSAwdTY0KTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBOZWdhdGlvbiBvbiBzaWduZWQgdHlwZXMgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IG5lZ19pODogIGk4ICA6PSAtNDJpODtcbiAgICBsZXQgbmVnX2kzMjogaTMyIDo9IC0xMDAwaTMyO1xuICAgIGFzc2VydChuZWdfaTggID09IC00Mmk4KTtcbiAgICBhc3NlcnQobmVnX2kzMiA9PSAtMTAwMGkzMik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci90eXBlcy84Ml9zaXplZF9udW1lcmljX3R5cGVzLm10bCIsIm5hbWUiOiI4Ml9zaXplZF9udW1lcmljX3R5cGVzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.sized-numeric-types.legality-3}

An unsuffixed numeric literal adopts the numeric type supplied by context; without
context, integer literals default to `i64` and floating-point literals to `f64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA0X3BvbHltb3JwaGljX2xpdGVyYWxzLm10bCIsInNvdXJjZSI6Ii8vIFBvbHltb3JwaGljIGludGVnZXIgYW5kIGZsb2F0IGxpdGVyYWxzOiB1bnN1ZmZpeGVkIG51bWVyaWMgbGl0ZXJhbHMgdW5pZnkgd2l0aFxuLy8gd2hhdGV2ZXIgdHlwZSB0aGUgY29udGV4dCBkZW1hbmRzLCBkZWZhdWx0aW5nIHRvIGk2NCAvIGY2NCB3aGVuIHVuY29uc3RyYWluZWQuXG5cbnN0cnVjdCBQaXhlbCB7XG4gICAgcjogdTgsXG4gICAgZzogdTgsXG4gICAgYjogdTgsXG59XG5cbmZ1biBhZGRfaTMyKHg6IGkzMiwgeTogaTMyKSAtPiBpMzIgeyB4ICsgeSB9XG5mdW4gc2NhbGVfZjMyKHg6IGYzMiwgZmFjdG9yOiBmMzIpIC0+IGYzMiB7IHggKiBmYWN0b3IgfVxuZnVuIGlkZW50aXR5X3U4KHg6IHU4KSAtPiB1OCB7IHggfVxuZnVuIHJldHVybnNfaTE2KCkgLT4gaTE2IHsgMTAwMCB9XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFx1MjUwMFx1MjUwMCBEZWZhdWx0OiB1bmNvbnN0cmFpbmVkIGxpdGVyYWxzIGJlY29tZSBpNjQgLyBmNjQgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IGEgOj0gNDI7XG4gICAgbGV0IGIgOj0gMy4xNDtcbiAgICBhc3NlcnQoYSA9PSA0Mik7XG4gICAgYXNzZXJ0KGIgPT0gMy4xNCk7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgVHlwZSBhbm5vdGF0aW9uIGNvZXJjZXMgdGhlIGxpdGVyYWwgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IGM6IGk4ICA6PSAxMDA7XG4gICAgbGV0IGQ6IGkxNiA6PSAxMDAwO1xuICAgIGxldCBlOiBpMzIgOj0gNTAwMDA7XG4gICAgbGV0IGY6IHU4ICA6PSAyMDA7XG4gICAgbGV0IGc6IHUxNiA6PSA2MDAwMDtcbiAgICBsZXQgaDogdTMyIDo9IDEwMDAwMDtcbiAgICBsZXQgaTogdTY0IDo9IDk5OTk5OTtcbiAgICBhc3NlcnQoYyA9PSAxMDBpOCk7XG4gICAgYXNzZXJ0KGQgPT0gMTAwMGkxNik7XG4gICAgYXNzZXJ0KGUgPT0gNTAwMDBpMzIpO1xuICAgIGFzc2VydChmID09IDIwMHU4KTtcbiAgICBhc3NlcnQoZyA9PSA2MDAwMHUxNik7XG4gICAgYXNzZXJ0KGggPT0gMTAwMDAwdTMyKTtcbiAgICBhc3NlcnQoaSA9PSA5OTk5OTl1NjQpO1xuXG4gICAgbGV0IHA6IGYzMiA6PSAxLjU7XG4gICAgYXNzZXJ0KHAgPT0gMS41ZjMyKTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBBcml0aG1ldGljIHByb3BhZ2F0ZXMgdGhlIGNvbnN0cmFpbmVkIHR5cGUgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IHg6IGkzMiA6PSAxMDtcbiAgICBsZXQgeSA6PSB4ICsgNTsgICAgICAgICAgLy8gNSBwaWNrcyB1cCBpMzIgZnJvbSB4XG4gICAgYXNzZXJ0KHkgPT0gMTVpMzIpO1xuXG4gICAgbGV0IGZ4OiBmMzIgOj0gMi4wZjMyO1xuICAgIGxldCBmeSA6PSBmeCArIDEuMDsgICAgICAvLyAxLjAgcGlja3MgdXAgZjMyIGZyb20gZnhcbiAgICBhc3NlcnQoZnkgPT0gMy4wZjMyKTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBGdW5jdGlvbiBhcmd1bWVudCBjb2VyY2lvbiBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgcjEgOj0gYWRkX2kzMigzLCA0KTtcbiAgICBhc3NlcnQocjEgPT0gN2kzMik7XG5cbiAgICBsZXQgcjIgOj0gc2NhbGVfZjMyKDIuMCwgMy4wKTtcbiAgICBhc3NlcnQocjIgPT0gNi4wZjMyKTtcblxuICAgIGxldCByMyA6PSBpZGVudGl0eV91OCgyNTUpO1xuICAgIGFzc2VydChyMyA9PSAyNTV1OCk7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgUmV0dXJuIHR5cGUgY29lcmNpb24gXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IHI0OiBpMTYgOj0gcmV0dXJuc19pMTYoKTtcbiAgICBhc3NlcnQocjQgPT0gMTAwMGkxNik7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgU3RydWN0IGZpZWxkIGNvZXJjaW9uIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCBweCA6PSBQaXhlbCB7IHIgPSAyNTUsIGcgPSAxMjgsIGIgPSAwIH07XG4gICAgYXNzZXJ0KHB4LnIgPT0gMjU1dTgpO1xuICAgIGFzc2VydChweC5nID09IDEyOHU4KTtcbiAgICBhc3NlcnQocHguYiA9PSAwdTgpO1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIEFycmF5IGVsZW1lbnQgdHlwZSBwcm9wYWdhdGlvbiBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgYXJyOiBpMzJbXSA6PSBbMSwgMiwgM107XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxaTMyKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDJpMzIpO1xuICAgIGFzc2VydChhcnJbMl0gPT0gM2kzMik7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgQ2FzdCBjb2VyY2lvbiBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcbiAgICBsZXQgY2FzdF91ODogdTggOj0gNDIgYXMgdTg7XG4gICAgYXNzZXJ0KGNhc3RfdTggPT0gNDJ1OCk7XG5cbiAgICBsZXQgY2FzdF9mMzI6IGYzMiA6PSA3IGFzIGYzMjtcbiAgICBhc3NlcnQoY2FzdF9mMzIgPT0gNy4wZjMyKTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBNZXRob2QgZGlzcGF0Y2ggZGVmYXVsdHMgbGl0ZXJhbCB0byBpNjQgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG4gICAgbGV0IHMxIDo9IDQyLnRvX3N0cmluZygpO1xuICAgIGFzc2VydChzMSA9PSBcIjQyXCIpO1xuXG4gICAgbGV0IHMyIDo9IDAudG9fc3RyaW5nKCk7XG4gICAgYXNzZXJ0KHMyID09IFwiMFwiKTtcblxuICAgIGxldCBzMyA6PSAzLjE0LnRvX3N0cmluZygpO1xuICAgIGFzc2VydChzMyA9PSBcIjMuMTRcIik7XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgQ29tcGFyaXNvbiBiZXR3ZWVuIGxpdGVyYWwgYW5kIHNpemVkIHZhcmlhYmxlIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCB2aTMyOiBpMzIgOj0gNWkzMjtcbiAgICBhc3NlcnQodmkzMiA9PSA1KTsgICAgICAvLyA1IGNvZXJjZXMgdG8gaTMyXG5cbiAgICBsZXQgdmYzMjogZjMyIDo9IDEuMGYzMjtcbiAgICBhc3NlcnQodmYzMiA9PSAxLjApOyAgICAvLyAxLjAgY29lcmNlcyB0byBmMzJcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBOZWdhdGl2ZSBsaXRlcmFscyBjb2VyY2UgY29ycmVjdGx5IFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuICAgIGxldCBuZWdfaTg6ICBpOCAgOj0gLTEwMDtcbiAgICBsZXQgbmVnX2kzMjogaTMyIDo9IC01MDAwMDtcbiAgICBsZXQgbmVnX2YzMjogZjMyIDo9IC0yLjU7XG4gICAgYXNzZXJ0KG5lZ19pOCAgPT0gLTEwMGk4KTtcbiAgICBhc3NlcnQobmVnX2kzMiA9PSAtNTAwMDBpMzIpO1xuICAgIGFzc2VydChuZWdfZjMyID09IC0yLjVmMzIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbGl0ZXJhbHMvMDRfcG9seW1vcnBoaWNfbGl0ZXJhbHMubXRsIiwibmFtZSI6IjA0X3BvbHltb3JwaGljX2xpdGVyYWxzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.sized-numeric-types.dynamics-1}

Integer overflow panics, unconditionally — Metel has no debug/release build-mode
distinction of its own (the interpreter takes no such flag), so this applies the
same way regardless of how the interpreter binary happens to have been compiled.
Floating-point overflow follows IEEE 754 behavior.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6Im92ZXJmbG93IiwibGluZSI6bnVsbCwic3RhdHVzIjoicnVudGltZV9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6IjExX292ZXJmbG93X3Bhbmljcy5tdGwiLCJzb3VyY2UiOiIvLyBSVU5USU1FX0VSUk9SW292ZXJmbG93XVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGE6IGk4IDo9IDEyN2k4ICsgMWk4O1xuICAgIGxldCBfIDo9IGE7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9hcml0aG1ldGljLzExX292ZXJmbG93X3Bhbmljcy5tdGwiLCJuYW1lIjoiMTFfb3ZlcmZsb3dfcGFuaWNzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## Char

> **Availability:** Since v0.8.0.

`Char` represents a single Unicode scalar value. Character literals use single quotes: `'a'`, `'\n'`, `'\u{1F600}'`.

```metel
fun main() {
    let c: Char := 'a';
    let code: u32 := u32::from(c);
    let back: Char := Char::from(code);
}
```

`Char` is not `u32` and not a string — no implicit coercions exist. Use
[`u32::from(c)`](runtime.md#spec.runtime.char-methods.dynamics-1) to get the Unicode
scalar value and [`Char::from(n)`](runtime.md#spec.runtime.char-methods.dynamics-1) to
construct from a code point; `Char::from` raises a runtime error if `n` is not a valid
Unicode scalar value.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.char.legality-1}

`Char` is a distinct Unicode-scalar type, not an alias for `u32` or `u8`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjgxX2NoYXIubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7XG4gICAgLy8gTGl0ZXJhbHMgYW5kIGJhc2ljIGVxdWFsaXR5XG4gICAgbGV0IGE6IENoYXIgOj0gJ0EnO1xuICAgIGxldCB6OiBDaGFyIDo9ICd6JztcbiAgICBsZXQgemVybzogQ2hhciA6PSAnMCc7XG4gICAgYXNzZXJ0KGEgPT0gJ0EnKTtcbiAgICBhc3NlcnQoeiA9PSAneicpO1xuICAgIGFzc2VydCh6ZXJvID09ICcwJyk7XG4gICAgYXNzZXJ0KGEgIT0geik7XG5cbiAgICAvLyBFc2NhcGUgc2VxdWVuY2VzXG4gICAgbGV0IG5ld2xpbmU6IENoYXIgOj0gJ1xcbic7XG4gICAgbGV0IHRhYjogQ2hhciA6PSAnXFx0JztcbiAgICBsZXQgYmFja3NsYXNoOiBDaGFyIDo9ICdcXFxcJztcbiAgICBsZXQgc2luZ2xlX3F1b3RlOiBDaGFyIDo9ICdcXCcnO1xuICAgIGFzc2VydChuZXdsaW5lICE9IHRhYik7XG4gICAgYXNzZXJ0KGJhY2tzbGFzaCA9PSAnXFxcXCcpO1xuICAgIGFzc2VydChzaW5nbGVfcXVvdGUgPT0gJ1xcJycpO1xuXG4gICAgLy8gVW5pY29kZSBlc2NhcGVcbiAgICBsZXQgc21pbGV5OiBDaGFyIDo9ICdcXHV7MUY2MDB9JztcbiAgICBhc3NlcnQoc21pbGV5ID09ICdcXHV7MUY2MDB9Jyk7XG5cbiAgICAvLyB0b19zdHJpbmdcbiAgICBhc3NlcnQoYS50b19zdHJpbmcoKSA9PSBcIkFcIik7XG4gICAgYXNzZXJ0KHplcm8udG9fc3RyaW5nKCkgPT0gXCIwXCIpO1xuICAgIGFzc2VydChzaW5nbGVfcXVvdGUudG9fc3RyaW5nKCkgPT0gXCInXCIpO1xuXG4gICAgLy8gQ29tcGFyaXNvbiBvcGVyYXRvcnMgKFVuaWNvZGUgc2NhbGFyIG9yZGVyKVxuICAgIGFzc2VydCgnQScgPCAnQicpO1xuICAgIGFzc2VydCgneicgPiAnYScpO1xuICAgIGFzc2VydCgnMCcgPCAnOScpO1xuICAgIGFzc2VydCgnQScgPD0gJ0EnKTtcbiAgICBhc3NlcnQoJ0InID49ICdBJyk7XG5cbiAgICAvLyBDb252ZXJzaW9uIHRvIHUzMiAoVW5pY29kZSBjb2RlIHBvaW50KVxuICAgIGxldCBjb2RlOiB1MzIgOj0gYSBhcyB1MzI7XG4gICAgYXNzZXJ0KGNvZGUgPT0gNjV1MzIpO1xuXG4gICAgLy8gQ29udmVyc2lvbiBmcm9tIHUzMiBiYWNrIHRvIENoYXJcbiAgICBsZXQgYmFjazogQ2hhciA6PSA2NXUzMiBhcyBDaGFyO1xuICAgIGFzc2VydChiYWNrID09ICdBJyk7XG5cbiAgICAvLyBSb3VuZC10cmlwXG4gICAgbGV0IG9yaWc6IENoYXIgOj0gJ00nO1xuICAgIGxldCByb3VuZDogQ2hhciA6PSAob3JpZyBhcyB1MzIpIGFzIENoYXI7XG4gICAgYXNzZXJ0KHJvdW5kID09IG9yaWcpO1xuXG4gICAgLy8gUGF0dGVybiBtYXRjaGluZ1xuICAgIGxldCBncmVldGluZzogU3RyaW5nIDo9IG1hdGNoIChhKSB7XG4gICAgICAgICdBJyA9PiBcImFscGhhXCIsXG4gICAgICAgICdCJyA9PiBcImJldGFcIixcbiAgICAgICAgXyAgID0+IFwib3RoZXJcIixcbiAgICB9O1xuICAgIGFzc2VydChncmVldGluZyA9PSBcImFscGhhXCIpO1xuXG4gICAgbGV0IGNhdGVnb3J5OiBTdHJpbmcgOj0gbWF0Y2ggKHplcm8pIHtcbiAgICAgICAgJzAnID0+IFwiZGlnaXRcIixcbiAgICAgICAgJ2EnID0+IFwibG93ZXJcIixcbiAgICAgICAgJ0EnID0+IFwidXBwZXJcIixcbiAgICAgICAgXyAgID0+IFwib3RoZXJcIixcbiAgICB9O1xuICAgIGFzc2VydChjYXRlZ29yeSA9PSBcImRpZ2l0XCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvODFfY2hhci5tdGwiLCJuYW1lIjoiODFfY2hhci5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Type Inference

Types are inferred using the Hindley-Milner algorithm with let-polymorphism. Annotations are optional for all bindings, including function parameters and return types. They may be written explicitly for documentation or to restrict a binding to a less general type.

Annotations are required only where there is no expression to infer from:
- Struct and enum field types
- Aspect method signatures

Every named type in an annotation must resolve in the annotation's declaring scope,
including names nested inside arrays, tuples, function types, and record fields. This is
checked when the declaration is type-checked, even if no value ever reaches the
annotation. A generic parameter in scope and `Self` where it is permitted resolve as
types; every other unknown name is error `T0003`.

```metel
fun add_annotated(a: i64, b: i64) -> i64 { a + b }
fun add_inferred(a, b) { a + b }

fun main() -> i64 {
    let x := 42;           // inferred: i64
    let name := "Vlad";    // inferred: String
    let y: f64 := 3.14;  // explicit annotation (optional here)
    let total := add_annotated(x, 1) + add_inferred(2, 3);
    if (name == "Vlad") { total + (y as i64) } else { 0 }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.type-inference.legality-1}

An expression in `return` position is typechecked against the enclosing function or
method's declared return type, which supplies its expected type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0019](../../rfcs/4-implemented/rfc-0019-return-context-type-propagation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMV9yZXR1cm5fdHlwZV9wcm9wYWdhdGlvbi5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA3OiByZXR1cm4gdHlwZSBwcm9wYWdhdGlvbiBmcm9tIGZ1bmN0aW9uIGNvbnRleHQuXG4vLyBQYXNzIDIgbXVzdCBwcm9wYWdhdGUgdGhlIGRlY2xhcmVkIHJldHVybiB0eXBlIGludG8gcmV0dXJuL2JyZWFrIGV4cHJlc3Npb25zXG4vLyBzbyB0aGF0IE5vbmUgYW5kIGJhcmUgZW51bSB2YXJpYW50cyBjYW4gYmUgdHlwZWQgd2l0aG91dCBhIGxvY2FsIGFubm90YXRpb24uXG5cbi8vIFJldHVybiBOb25lIGluIGEgUGVyaGFwczxpNjQ+LXJldHVybmluZyBmdW5jdGlvbi5cbmZ1biBmaW5kKGFycjogaTY0W10sIHRhcmdldDogaTY0KSAtPiBQZXJoYXBzPGk2ND4ge1xuICAgIHJldHVybiBOb25lO1xufVxuXG4vLyBSZXR1cm4gUmVzdWx0OjpFcnIgd2hlcmUgVCBpcyBub3QgcHJlc2VudCBpbiBFcnIncyBmaWVsZHMuXG5mdW4gZGl2aWRlKGE6IGY2NCwgYjogZjY0KSAtPiBSZXN1bHQ8ZjY0LCBTdHJpbmc+IHtcbiAgICBpZiAoYiA9PSAwLjApIHtcbiAgICAgICAgcmV0dXJuIFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBcImRpdmlzaW9uIGJ5IHplcm9cIiB9O1xuICAgIH1cbiAgICByZXR1cm4gUmVzdWx0OjpPayB7IHZhbHVlID0gYSAvIGIgfTtcbn1cblxuLy8gQnJlYWsgTm9uZSBpbiBhIGxvb3Agd2hvc2UgcmVzdWx0IGlzIGFubm90YXRlZCBhcyBQZXJoYXBzPGk2ND4uXG5mdW4gZmlyc3RfcG9zaXRpdmUoYXJyOiBpNjRbXSkgLT4gUGVyaGFwczxpNjQ+IHtcbiAgICBsZXQgcmVzdWx0OiBQZXJoYXBzPGk2ND4gOj0gbG9vcCB7XG4gICAgICAgIGJyZWFrIE5vbmU7XG4gICAgfTtcbiAgICByZXN1bHRcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2Z1bmN0aW9ucy9zdGFnZTdfMDFfcmV0dXJuX3R5cGVfcHJvcGFnYXRpb24ubXRsIiwibmFtZSI6InN0YWdlN18wMV9yZXR1cm5fdHlwZV9wcm9wYWdhdGlvbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-inference.legality-2}

An expression in `break` position is typechecked against its enclosing `loop`'s value
type, independently of the enclosing function's return type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0019](../../rfcs/4-implemented/rfc-0019-return-context-type-propagation.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlN18wMV9yZXR1cm5fdHlwZV9wcm9wYWdhdGlvbi5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA3OiByZXR1cm4gdHlwZSBwcm9wYWdhdGlvbiBmcm9tIGZ1bmN0aW9uIGNvbnRleHQuXG4vLyBQYXNzIDIgbXVzdCBwcm9wYWdhdGUgdGhlIGRlY2xhcmVkIHJldHVybiB0eXBlIGludG8gcmV0dXJuL2JyZWFrIGV4cHJlc3Npb25zXG4vLyBzbyB0aGF0IE5vbmUgYW5kIGJhcmUgZW51bSB2YXJpYW50cyBjYW4gYmUgdHlwZWQgd2l0aG91dCBhIGxvY2FsIGFubm90YXRpb24uXG5cbi8vIFJldHVybiBOb25lIGluIGEgUGVyaGFwczxpNjQ+LXJldHVybmluZyBmdW5jdGlvbi5cbmZ1biBmaW5kKGFycjogaTY0W10sIHRhcmdldDogaTY0KSAtPiBQZXJoYXBzPGk2ND4ge1xuICAgIHJldHVybiBOb25lO1xufVxuXG4vLyBSZXR1cm4gUmVzdWx0OjpFcnIgd2hlcmUgVCBpcyBub3QgcHJlc2VudCBpbiBFcnIncyBmaWVsZHMuXG5mdW4gZGl2aWRlKGE6IGY2NCwgYjogZjY0KSAtPiBSZXN1bHQ8ZjY0LCBTdHJpbmc+IHtcbiAgICBpZiAoYiA9PSAwLjApIHtcbiAgICAgICAgcmV0dXJuIFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBcImRpdmlzaW9uIGJ5IHplcm9cIiB9O1xuICAgIH1cbiAgICByZXR1cm4gUmVzdWx0OjpPayB7IHZhbHVlID0gYSAvIGIgfTtcbn1cblxuLy8gQnJlYWsgTm9uZSBpbiBhIGxvb3Agd2hvc2UgcmVzdWx0IGlzIGFubm90YXRlZCBhcyBQZXJoYXBzPGk2ND4uXG5mdW4gZmlyc3RfcG9zaXRpdmUoYXJyOiBpNjRbXSkgLT4gUGVyaGFwczxpNjQ+IHtcbiAgICBsZXQgcmVzdWx0OiBQZXJoYXBzPGk2ND4gOj0gbG9vcCB7XG4gICAgICAgIGJyZWFrIE5vbmU7XG4gICAgfTtcbiAgICByZXN1bHRcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2Z1bmN0aW9ucy9zdGFnZTdfMDFfcmV0dXJuX3R5cGVfcHJvcGFnYXRpb24ubXRsIiwibmFtZSI6InN0YWdlN18wMV9yZXR1cm5fdHlwZV9wcm9wYWdhdGlvbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Tuples

Tuples are lightweight anonymous product types.

```metel
fun main() -> i64 {
    let coord: (i64, i64) := (10, 20);
    let triple: (String, i64, boolean) := ("yes", 42, true);
    return coord.0 + triple.1;
}
```

Positional field access [uses zero-based selectors `.0`, `.1`, etc.](#spec.types.tuples.legality-1):

```metel
fun main() -> i64 {
    let coord: (i64, i64) := (10, 20);
    let x := coord.0;
    let y := coord.1;
    return x + y;
}
```

`()` is the zero-element tuple (unit type).

Tuples can be destructured in `match`:

```metel
fun main() -> i64 {
    let coord: (i64, i64) := (10, 0);
    match (coord) {
        (0, y) => y,
        (x, 0) => x,
        (x, y) => x + y,
    }
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.tuples.legality-1}

A tuple's elements are addressed by zero-based positional selectors. A selector is valid
only for an element in the tuple's declared arity.

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA5X3R1cGxlLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIENvbnN0cnVjdGlvbiBhbmQgZWxlbWVudCBhY2Nlc3MuXG4gICAgbGV0IHQgOj0gKDEwLCAyMCk7XG4gICAgYXNzZXJ0KHQuMCA9PSAxMCk7XG4gICAgYXNzZXJ0KHQuMSA9PSAyMCk7XG4gICAgLy8gTWl4ZWQgdHlwZXMuXG4gICAgbGV0IHBhaXIgOj0gKDEsIHRydWUpO1xuICAgIGFzc2VydChwYWlyLjAgPT0gMSk7XG4gICAgYXNzZXJ0KHBhaXIuMSk7XG4gICAgLy8gTmVzdGVkIHR1cGxlLlxuICAgIGxldCBuZXN0ZWQgOj0gKDEsICgyLCAzKSk7XG4gICAgbGV0IGlubmVyIDo9IG5lc3RlZC4xO1xuICAgIGFzc2VydChpbm5lci4wID09IDIpO1xuICAgIGFzc2VydChpbm5lci4xID09IDMpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvMDlfdHVwbGUubXRsIiwibmFtZSI6IjA5X3R1cGxlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6Im91dCBvZiBib3VuZHMiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfMDlfdHVwbGVfb29iLm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUltvdXQgb2YgYm91bmRzXVxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHQgOj0gKDEsIDIpO1xuICAgIGxldCBfeCA6PSB0LjU7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci90eXBlcy9uZWdfMDlfdHVwbGVfb29iLm10bCIsIm5hbWUiOiJuZWdfMDlfdHVwbGVfb29iLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Anonymous Records

> **Availability:** Since v0.12.0.

A record is a product type whose components are *labelled*, where a tuple's are positional.
It is written in bare braces, with no keyword:

```metel
{ x: f64, y: f64 }      // the type
{ x = 1.0, y = 2.0 }    // a value of it
```

Field declarations classify and take `:`; field initializers define and take `=` — the same
distinction `let x: i64 = 1` already draws.

**A record type is exact.** `{ x: f64 }` is inhabited only by records with that row and
nothing else; a value of `{ x: f64, y: f64 }` is *not* a value of `{ x: f64 }`. Records are
not implicitly widened or narrowed.

**Records are structurally typed.** Two records with the same labels and field types are the
same type, wherever they were written. A record has no declaration site and no name.
**Field order does not matter:** `{ x: i64, y: i64 }` and `{ y: i64, x: i64 }` are the same
type, and `{ x = 1, y = 2 }` and `{ y = 2, x = 1 }` are indistinguishable — each is usable
wherever the other is. A record is a set of labelled fields, not an ordered one. Repeating a
label in one record (`{ x: i64, x: f64 }`) is an error.

(Indistinguishable is a statement about the type, not about `==`, which no compound type —
record, struct, tuple, or array — supports.)

When a local variable has the same name as a field, the `= value` part may be omitted, as in
a struct literal:

```metel
fun main() {
    let x := 1.0;
    let y := 2.0;
    let p := { x, y };       // { x: f64, y: f64 }
    println("${p.x}");
}
```

Punning, and single-field record literals generally, are read as records only in positions
that expect an expression — a `let`/`var` or field initializer, a call argument, an array
element. In a position that also admits a block — an `if`/`else` or `match` arm, a
function, closure, or loop body — a bare `{ x }` is a **block** whose result is `x`, and
`{ x = 1 }` is a block whose result is the assignment. Write the record in parentheses to
force it: `({ x })`. A multi-field literal needs no parentheses, as `{ x = 1, y = 2 }`
cannot be a block.

### Where records may be used

Records are ordinary values: they may appear as parameters, returns, `let` bindings, and
struct or enum fields; they may be pattern-matched, used as generic arguments, and tagged or
borrowed (`@a { x: f64 }`, `&r { x: f64 }`) exactly as a struct is. `Send` and `Sync` extend
to them by the same field-composition rule used for structs.

Three things a record cannot do, all for the same underlying reason — it has no nominal
owner:

- **No inherent methods.** Two unrelated modules could otherwise write conflicting methods
  for the same shape with no principled way to choose between them.
- **No implementations of a non-local aspect**, by the other direction of that rule. An
  aspect local to the current module may be implemented for a record — but see the note
  below: that is not available yet.
- **No custom `Drop`.** `Drop` is a standard-library aspect and never local to ordinary
  user code, so teardown logic belongs to nominal types only.

> **Not available in v0.12.0: implementing a local aspect for a record.** `extend { w: i64 }:
> MyAspect { … }` does not work. This is not specific to records — `extend` on a tuple
> target fails the same way; implementations for these two structural types are not built
> yet. **Arrays are the exception:** `extend<T> T[]: MyAspect { … }` is supported, per the
> orphan-rule carve-out for structural type constructors — see
> [Declarations — Structural Aspect Bounds](declarations.md#structural-aspect-bounds).
> Until a record or tuple target is supported, **a record satisfies no aspect that requires
> an implementation**, so a record cannot be printed, compared, or passed where any such
> bound is required. Auto-derived aspects are unaffected.

### Projection

A nominal type's row may be projected to a named subset, written with a dot to distinguish
it from a struct literal:

```metel
Handle.{ fd }           // the type: Handle's row, narrowed to `fd`
```

A bare identifier inside projection braces is always a **field label**, never a type or a
row variable. Chained projection (`S.{ a }.{ b }`) and projection in pattern position are not
accepted.

Inside an `extend` block, `Self.{ fd }` projects `Self`'s own row exactly as
`Handle.{ fd }` would project `Handle`'s — `Self` resolves to the enclosing block's
target type here the same way it does everywhere else the target's name can stand in
for it.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.anonymous-records.dynamics-1}

Record identity is structural: records with the same labelled fields and field types are
the same type regardless of declaration-free spelling order.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjkxX2Fub255bW91c19yZWNvcmRzX2V4dHJhLm10bCIsInNvdXJjZSI6Ii8vIEV4dHJhIGFub255bW91cy1yZWNvcmQgY292ZXJhZ2UgKFJGQy0wMTE2KTogbmVzdGluZywgcmVjb3JkcyBhcyBzdHJ1Y3Rcbi8vIGZpZWxkcywgd2hvbGUtdmFsdWUgYW5kIGZpZWxkIG11dGF0aW9uLCBtdWx0aS1maWVsZCBwcm9qZWN0aW9uLCB0aGVcbi8vIG9yZGVyLWluc2Vuc2l0aXZlIGlkZW50aXR5IGFjcm9zcyBhIGZ1bmN0aW9uIGJvdW5kYXJ5LCBhbmQgcGF0dGVybiBiaW5kaW5nLlxuXG5zdHJ1Y3QgV3JhcCB7IGlubmVyOiB7IHg6IGk2NCwgeTogaTY0IH0gfVxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgdGFnOiBpNjQsIG1vZGU6IGk2NCB9XG5cbi8vIFRoZSBkZWNsYXJlZCByZXR1cm4gcm93IGlzIHdyaXR0ZW4gYHsgYiwgYSB9YDsgdGhlIGNhbGwgc2l0ZSBiZWxvdyBhbm5vdGF0ZXNcbi8vIGB7IGEsIGIgfWAuIFRoZXkgYXJlIHRoZSBzYW1lIHR5cGUgXHUyMDE0IGZpZWxkIG9yZGVyIGlzIG5vdCBwYXJ0IG9mIGlkZW50aXR5LlxuZnVuIHN3YXBfbmFtZXMoYTogaTY0LCBiOiBpNjQpIC0+IHsgYjogaTY0LCBhOiBpNjQgfSB7XG4gICAgKHsgYSA9IGEsIGIgPSBiIH0pXG59XG5cbi8vIEEgYmxvY2sgd2hvc2UgdGFpbCBpcyBhIHJlY29yZC10eXBlZCBpZGVudGlmaWVyIGlzIGEgcGVyZmVjdGx5IG9yZGluYXJ5XG4vLyByZWNvcmQgcmV0dXJuIFx1MjAxNCBubyBwYXJlbnRoZXNlcyBuZWVkZWQuIChSZWdyZXNzaW9uIGd1YXJkOiBhbiBlYXJsaWVyXG4vLyBibG9jay12cy1yZWNvcmQgaGV1cmlzdGljIHdyb25nbHkgcmVqZWN0ZWQgdGhpcyB2YWxpZCBmb3JtLilcbmZ1biB2aWFfaWRlbnQoKSAtPiB7IGE6IGk2NCB9IHtcbiAgICBsZXQgciA6PSAoeyBhID0gMSB9KTtcbiAgICByXG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIE5lc3RlZCByZWNvcmRzLCBhbmQgYWNjZXNzIHRocm91Z2ggdHdvIGxldmVscy5cbiAgICBsZXQgbmVzdGVkIDo9IHsgb3V0ZXIgPSB7IGlubmVyID0gNyB9IH07XG4gICAgYXNzZXJ0KG5lc3RlZC5vdXRlci5pbm5lciA9PSA3KTtcblxuICAgIC8vIEEgcmVjb3JkIGFzIGEgc3RydWN0IGZpZWxkLlxuICAgIGxldCB3IDo9IFdyYXAgeyBpbm5lciA9IHsgeCA9IDEsIHkgPSAyIH0gfTtcbiAgICBhc3NlcnQody5pbm5lci54ID09IDEpO1xuICAgIGFzc2VydCh3LmlubmVyLnkgPT0gMik7XG5cbiAgICAvLyBPcmRlci1pbnNlbnNpdGl2ZSBpZGVudGl0eSBhY3Jvc3MgYSBjYWxsOiBgeyBiLCBhIH1gIHJlc3VsdCB1c2VkIHdoZXJlXG4gICAgLy8gYHsgYSwgYiB9YCBpcyBhbm5vdGF0ZWQuXG4gICAgbGV0IGFiOiB7IGE6IGk2NCwgYjogaTY0IH0gOj0gc3dhcF9uYW1lcygxMCwgMjApO1xuICAgIGFzc2VydChhYi5hID09IDEwKTtcbiAgICBhc3NlcnQoYWIuYiA9PSAyMCk7XG5cbiAgICAvLyBSZWNvcmQtdHlwZWQgaWRlbnRpZmllciBhcyBhIGJsb2NrIHRhaWwgKHJlZ3Jlc3Npb24gZ3VhcmQpLlxuICAgIGFzc2VydCh2aWFfaWRlbnQoKS5hID09IDEpO1xuXG4gICAgLy8gV2hvbGUtdmFsdWUgbXV0YXRpb24gdGhyb3VnaCBhIGB2YXJgIGJpbmRpbmcuXG4gICAgdmFyIHAgOj0geyB4ID0gMSwgeSA9IDEgfTtcbiAgICBwIDo9IHsgeCA9IDUsIHkgPSA2IH07XG4gICAgYXNzZXJ0KHAueCA9PSA1KTtcbiAgICBhc3NlcnQocC55ID09IDYpO1xuXG4gICAgLy8gRmllbGQgbXV0YXRpb24uXG4gICAgcC55IDo9IDk7XG4gICAgYXNzZXJ0KHAueSA9PSA5KTtcblxuICAgIC8vIE11bHRpLWZpZWxkIHByb2plY3Rpb24gb2YgYSBub21pbmFsIHR5cGUncyByb3cuXG4gICAgbGV0IGggOj0gSGFuZGxlIHsgZmQgPSAzLCB0YWcgPSA0LCBtb2RlID0gNSB9O1xuICAgIGxldCBwaWNrZWQgOj0gaC57IGZkLCBtb2RlIH07XG4gICAgYXNzZXJ0KHBpY2tlZC5mZCA9PSAzKTtcbiAgICBhc3NlcnQocGlja2VkLm1vZGUgPT0gNSk7XG5cbiAgICAvLyBQYXR0ZXJuIGJpbmRpbmcsIGJvdGggZmllbGRzIHVzZWQuXG4gICAgbGV0IHRvdGFsIDo9IG1hdGNoIChwKSB7IHsgeCwgeSB9ID0+IHggKyB5LCB9O1xuICAgIGFzc2VydCh0b3RhbCA9PSAxNCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzkxX2Fub255bW91c19yZWNvcmRzX2V4dHJhLm10bCIsIm5hbWUiOiI5MV9hbm9ueW1vdXNfcmVjb3Jkc19leHRyYS5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.anonymous-records.legality-1}

An anonymous record cannot satisfy an impl-based aspect bound, because no implementation
for a record target is available.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6ImFueXRoaW5nIGltcGwtYmFzZWQgbmVlZHMgYSBub21pbmFsIHR5cGUiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTVfbmVnXzE5X3JlY29yZF9kb2VzX25vdF9zYXRpc2Z5X2FzcGVjdF9ib3VuZC5tdGwiLCJzb3VyY2UiOiIvLyBOZWdhdGl2ZSAoUkZDLTAxMTYgXHUwMGE3Myk6IGFuIGFub255bW91cyByZWNvcmQgaGFzIG5vIG5vbWluYWwgb3duZXIsIHNvIGl0IHNhdGlzZmllcyBub1xuLy8gaW1wbC1iYXNlZCBhc3BlY3QuIEl0IG11c3QgYmUgcmVqZWN0ZWQgYXQgdGhlIGNhbGwgc2l0ZSwgbGlrZSBhIHR1cGxlIG9yIGEgc3RydWN0XG4vLyB3aXRob3V0IHRoZSBpbXBsIFx1MjAxNCBub3QgYWNjZXB0ZWQgYW5kIHRoZW4gYmxvd24gdXAgYXQgcnVuIHRpbWUuXG5mdW4gc2hvdzxUOiBEaXNwbGF5Pih4OiBUKSAtPiBTdHJpbmcgeyB4LnRvX3N0cmluZygpIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyB4ID0gMSB9O1xuICAgIGxldCBzIDo9IHNob3cocik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL3N0YWdlNV9uZWdfMTlfcmVjb3JkX2RvZXNfbm90X3NhdGlzZnlfYXNwZWN0X2JvdW5kLm10bCIsIm5hbWUiOiJzdGFnZTVfbmVnXzE5X3JlY29yZF9kb2VzX25vdF9zYXRpc2Z5X2FzcGVjdF9ib3VuZC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.anonymous-records.dynamics-2}

Projection `Handle.{ fd, mode }` yields the record made from precisely the named fields of
the nominal receiver type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwMV9zZWxmX3JlY29yZF9wcm9qZWN0aW9uX3Jlc29sdmVzLm10bCIsInNvdXJjZSI6Ii8vICM3NzQ6IGBTZWxmYCByZXNvbHZlcyBpbnNpZGUgYSByZWNvcmQgcHJvamVjdGlvbiAoYFNlbGYueyBmaWVsZCB9YCkgZXhhY3RseSBhc1xuLy8gaXQgZG9lcyBhcyBhIHBsYWluIHR5cGUgaW4gdGhlIHNhbWUgcG9zaXRpb24gLS0gY29uZmlybWVkIGJ5IHdyaXRpbmcgdGhlIHNhbWVcbi8vIG1ldGhvZCBib3RoIHdheXMgYW5kIGdldHRpbmcgdGhlIHNhbWUgcmVzdWx0IGZyb20gdGhlIHNhbWUgc2hhcGVkIGFyZ3VtZW50LlxuLy8gQmVmb3JlIHRoZSBmaXgsIG9ubHkgdGhlIGBIYW5kbGUueyBmZCB9YCAoY29uY3JldGUtbmFtZSkgc3BlbGxpbmcgcmVzb2x2ZWQ7XG4vLyBgU2VsZi57IGZkIH1gIGZhaWxlZCB3aXRoIFwidW5rbm93biB0eXBlIGBTZWxmYFwiIGR1cmluZyB0aGUgZWFnZXJcbi8vIHByb2plY3Rpb25zLXZhbGlkaXR5IHBhc3MsIGFuZCAtLSBvbmNlIHRoYXQgcGFzcyBubyBsb25nZXIgbWFza2VkIGl0IC0tIGFcbi8vIHNlY29uZCwgaW5kZXBlbmRlbnQgZ2FwIGluIHRoZSByZWFsIHNpZ25hdHVyZSByZXNvbHV0aW9uIChubyByZWdpc3RyeSBhY2Nlc3Ncbi8vIGF0IHRoZSBvbmUgcGxhY2UgYFNlbGZgIGFsb25lIGFscmVhZHkgaGFkIGEgdGFyZ2V0IG5hbWUgdG8gcmVzb2x2ZSBhZ2FpbnN0KVxuLy8gc3VyZmFjZWQgcmlnaHQgYmVoaW5kIGl0LlxuLy9cbi8vIENhbGxlZCB3aXRoIGBoLnsgZmQgfWAgLS0gUkZDLTAxMTYncyBleHByZXNzaW9uLXBvc2l0aW9uIHByb2plY3Rpb24sIHdoaWNoXG4vLyBldmFsdWF0ZXMgdGhlIHJlYWwgYEhhbmRsZWAgdmFsdWUgYW5kIGV4dHJhY3RzIGEgZ2VudWluZSBgeyBmZDogaTY0IH1gIHJlY29yZFxuLy8gZnJvbSBpdCAtLSByYXRoZXIgdGhhbiBhIGJhcmUgYEhhbmRsZWAgdmFsdWUuIEEgcGFyYW1ldGVyIHR5cGVkIGBTZWxmLnsgZmQgfWAvXG4vLyBgSGFuZGxlLnsgZmQgfWAgaW50ZW50aW9uYWxseSBkb2VzIG5vdCBhY2NlcHQgYSBiYXJlIHN0cnVjdCB2YWx1ZTogbm8gaW1wbGljaXRcbi8vIHN0cnVjdC10by1yZWNvcmQgY29lcmNpb24gZXhpc3RzIGFueXdoZXJlIChSRkMtMDExOCdzIGFscmVhZHktc2hpcHBlZCByb3ctYm91bmRcbi8vIHJ1bGUgaXMgdGhlIHNhbWUgcHJpbmNpcGxlOiBcIm9ubHkgYSByZWNvcmQgc2F0aXNmaWVzIGEgcm93IGJvdW5kOyBhIG5vbWluYWxcbi8vIHN0cnVjdCBpcyByZWplY3RlZCBldmVuIHdoZW4gaXQgaGFzIG1hdGNoaW5nIGZpZWxkc1wiKS4gYC57IGZkIH1gIGlzIHRoZVxuLy8gZXhwbGljaXQsIGFscmVhZHktaW1wbGVtZW50ZWQgd2F5IHRvIHByb2R1Y2UgdGhlIG5hcnJvd2VyIHZhbHVlIHRoZSBwYXJhbWV0ZXJcbi8vIGFza3MgZm9yIC0tIG5vdCBhIHdvcmthcm91bmQsIHRoZSBpbnRlbmRlZCBwYWlyaW5nLlxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgbmFtZTogU3RyaW5nIH1cblxuZXh0ZW5kIEhhbmRsZSB7XG4gICAgZnVuIGRlc2NyaWJlX3NlbGYoaDogU2VsZi57IGZkIH0pIC0+IGk2NCB7XG4gICAgICAgIHJldHVybiBoLmZkO1xuICAgIH1cbiAgICBmdW4gZGVzY3JpYmVfbmFtZWQoaDogSGFuZGxlLnsgZmQgfSkgLT4gaTY0IHtcbiAgICAgICAgcmV0dXJuIGguZmQ7XG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInN0ZGluXCIgfTtcbiAgICBhc3NlcnQoSGFuZGxlOjpkZXNjcmliZV9zZWxmKGgueyBmZCB9KSA9PSAzKTtcbiAgICBhc3NlcnQoSGFuZGxlOjpkZXNjcmliZV9uYW1lZChoLnsgZmQgfSkgPT0gMyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzEwMV9zZWxmX3JlY29yZF9wcm9qZWN0aW9uX3Jlc29sdmVzLm10bCIsIm5hbWUiOiIxMDFfc2VsZl9yZWNvcmRfcHJvamVjdGlvbl9yZXNvbHZlcy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEwMl9zZWxmX3JlY29yZF9wcm9qZWN0aW9uX2luX2JvZHlfbGV0X2Fubm90YXRpb24ubXRsIiwic291cmNlIjoiLy8gIzc3NCBhcmNoaXRlY3R1cmFsIHJldmlzaW9uOiBhIGJvZHktaW50ZXJuYWwgYGxldCB4OiBTZWxmLnsgZmllbGQgfSA9IC4uLjtgXG4vLyBhbm5vdGF0aW9uIHJlc29sdmVzIHRoZSBzYW1lIHdheSBgU2VsZi57IGZpZWxkIH1gIGFscmVhZHkgZG9lcyBpbiBwYXJhbS9yZXR1cm5cbi8vIHBvc2l0aW9uLCBub3cgdGhhdCBgU2VsZmAgaXMgYm91bmQgYXMgYW4gb3JkaW5hcnkgdHlwZSBwYXJhbWV0ZXIgZm9yIHRoZSB3aG9sZVxuLy8gbWV0aG9kIHJhdGhlciB0aGFuIG9ubHkgaXRzIG93biBzaWduYXR1cmUuIFRoZSB2YWx1ZSBzaWRlIHVzZXMgYHNlbGYueyBmZCB9YFxuLy8gKFJGQy0wMTE2J3MgZXhwcmVzc2lvbi1wb3NpdGlvbiBwcm9qZWN0aW9uIG9uIHRoZSByZWNlaXZlciBpdHNlbGYpLCB0aGVcbi8vIGlkaW9tYXRpYyB3YXkgdG8gcHJvZHVjZSBpdCAtLSBub3QgYW4gYW5vbnltb3VzIHJlY29yZCBsaXRlcmFsIGJ1aWx0IGJ5IGhhbmQuXG5cbnN0cnVjdCBIYW5kbGUgeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcgfVxuXG5leHRlbmQgSGFuZGxlIHtcbiAgICBmdW4gbmFycm93X2xldChzZWxmKSAtPiBpNjQge1xuICAgICAgICBsZXQgeDogU2VsZi57IGZkIH0gOj0gc2VsZi57IGZkIH07XG4gICAgICAgIHJldHVybiB4LmZkO1xuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGggOj0gSGFuZGxlIHsgZmQgPSAzLCBuYW1lID0gXCJzdGRpblwiIH07XG4gICAgYXNzZXJ0KGgubmFycm93X2xldCgpID09IDMpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy8xMDJfc2VsZl9yZWNvcmRfcHJvamVjdGlvbl9pbl9ib2R5X2xldF9hbm5vdGF0aW9uLm10bCIsIm5hbWUiOiIxMDJfc2VsZl9yZWNvcmRfcHJvamVjdGlvbl9pbl9ib2R5X2xldF9hbm5vdGF0aW9uLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjkxX2Fub255bW91c19yZWNvcmRzX2V4dHJhLm10bCIsInNvdXJjZSI6Ii8vIEV4dHJhIGFub255bW91cy1yZWNvcmQgY292ZXJhZ2UgKFJGQy0wMTE2KTogbmVzdGluZywgcmVjb3JkcyBhcyBzdHJ1Y3Rcbi8vIGZpZWxkcywgd2hvbGUtdmFsdWUgYW5kIGZpZWxkIG11dGF0aW9uLCBtdWx0aS1maWVsZCBwcm9qZWN0aW9uLCB0aGVcbi8vIG9yZGVyLWluc2Vuc2l0aXZlIGlkZW50aXR5IGFjcm9zcyBhIGZ1bmN0aW9uIGJvdW5kYXJ5LCBhbmQgcGF0dGVybiBiaW5kaW5nLlxuXG5zdHJ1Y3QgV3JhcCB7IGlubmVyOiB7IHg6IGk2NCwgeTogaTY0IH0gfVxuXG5zdHJ1Y3QgSGFuZGxlIHsgZmQ6IGk2NCwgdGFnOiBpNjQsIG1vZGU6IGk2NCB9XG5cbi8vIFRoZSBkZWNsYXJlZCByZXR1cm4gcm93IGlzIHdyaXR0ZW4gYHsgYiwgYSB9YDsgdGhlIGNhbGwgc2l0ZSBiZWxvdyBhbm5vdGF0ZXNcbi8vIGB7IGEsIGIgfWAuIFRoZXkgYXJlIHRoZSBzYW1lIHR5cGUgXHUyMDE0IGZpZWxkIG9yZGVyIGlzIG5vdCBwYXJ0IG9mIGlkZW50aXR5LlxuZnVuIHN3YXBfbmFtZXMoYTogaTY0LCBiOiBpNjQpIC0+IHsgYjogaTY0LCBhOiBpNjQgfSB7XG4gICAgKHsgYSA9IGEsIGIgPSBiIH0pXG59XG5cbi8vIEEgYmxvY2sgd2hvc2UgdGFpbCBpcyBhIHJlY29yZC10eXBlZCBpZGVudGlmaWVyIGlzIGEgcGVyZmVjdGx5IG9yZGluYXJ5XG4vLyByZWNvcmQgcmV0dXJuIFx1MjAxNCBubyBwYXJlbnRoZXNlcyBuZWVkZWQuIChSZWdyZXNzaW9uIGd1YXJkOiBhbiBlYXJsaWVyXG4vLyBibG9jay12cy1yZWNvcmQgaGV1cmlzdGljIHdyb25nbHkgcmVqZWN0ZWQgdGhpcyB2YWxpZCBmb3JtLilcbmZ1biB2aWFfaWRlbnQoKSAtPiB7IGE6IGk2NCB9IHtcbiAgICBsZXQgciA6PSAoeyBhID0gMSB9KTtcbiAgICByXG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIE5lc3RlZCByZWNvcmRzLCBhbmQgYWNjZXNzIHRocm91Z2ggdHdvIGxldmVscy5cbiAgICBsZXQgbmVzdGVkIDo9IHsgb3V0ZXIgPSB7IGlubmVyID0gNyB9IH07XG4gICAgYXNzZXJ0KG5lc3RlZC5vdXRlci5pbm5lciA9PSA3KTtcblxuICAgIC8vIEEgcmVjb3JkIGFzIGEgc3RydWN0IGZpZWxkLlxuICAgIGxldCB3IDo9IFdyYXAgeyBpbm5lciA9IHsgeCA9IDEsIHkgPSAyIH0gfTtcbiAgICBhc3NlcnQody5pbm5lci54ID09IDEpO1xuICAgIGFzc2VydCh3LmlubmVyLnkgPT0gMik7XG5cbiAgICAvLyBPcmRlci1pbnNlbnNpdGl2ZSBpZGVudGl0eSBhY3Jvc3MgYSBjYWxsOiBgeyBiLCBhIH1gIHJlc3VsdCB1c2VkIHdoZXJlXG4gICAgLy8gYHsgYSwgYiB9YCBpcyBhbm5vdGF0ZWQuXG4gICAgbGV0IGFiOiB7IGE6IGk2NCwgYjogaTY0IH0gOj0gc3dhcF9uYW1lcygxMCwgMjApO1xuICAgIGFzc2VydChhYi5hID09IDEwKTtcbiAgICBhc3NlcnQoYWIuYiA9PSAyMCk7XG5cbiAgICAvLyBSZWNvcmQtdHlwZWQgaWRlbnRpZmllciBhcyBhIGJsb2NrIHRhaWwgKHJlZ3Jlc3Npb24gZ3VhcmQpLlxuICAgIGFzc2VydCh2aWFfaWRlbnQoKS5hID09IDEpO1xuXG4gICAgLy8gV2hvbGUtdmFsdWUgbXV0YXRpb24gdGhyb3VnaCBhIGB2YXJgIGJpbmRpbmcuXG4gICAgdmFyIHAgOj0geyB4ID0gMSwgeSA9IDEgfTtcbiAgICBwIDo9IHsgeCA9IDUsIHkgPSA2IH07XG4gICAgYXNzZXJ0KHAueCA9PSA1KTtcbiAgICBhc3NlcnQocC55ID09IDYpO1xuXG4gICAgLy8gRmllbGQgbXV0YXRpb24uXG4gICAgcC55IDo9IDk7XG4gICAgYXNzZXJ0KHAueSA9PSA5KTtcblxuICAgIC8vIE11bHRpLWZpZWxkIHByb2plY3Rpb24gb2YgYSBub21pbmFsIHR5cGUncyByb3cuXG4gICAgbGV0IGggOj0gSGFuZGxlIHsgZmQgPSAzLCB0YWcgPSA0LCBtb2RlID0gNSB9O1xuICAgIGxldCBwaWNrZWQgOj0gaC57IGZkLCBtb2RlIH07XG4gICAgYXNzZXJ0KHBpY2tlZC5mZCA9PSAzKTtcbiAgICBhc3NlcnQocGlja2VkLm1vZGUgPT0gNSk7XG5cbiAgICAvLyBQYXR0ZXJuIGJpbmRpbmcsIGJvdGggZmllbGRzIHVzZWQuXG4gICAgbGV0IHRvdGFsIDo9IG1hdGNoIChwKSB7IHsgeCwgeSB9ID0+IHggKyB5LCB9O1xuICAgIGFzc2VydCh0b3RhbCA9PSAxNCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzkxX2Fub255bW91c19yZWNvcmRzX2V4dHJhLm10bCIsIm5hbWUiOiI5MV9hbm9ueW1vdXNfcmVjb3Jkc19leHRyYS5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.anonymous-records.legality-3}

An anonymous record is rejected as an inherent-implementation target, as the target of a
non-local aspect implementation, and as the target of a custom `Drop` implementation.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0116](../../rfcs/4-implemented/rfc-0116-anonymous-record-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBoYXZlIGluaGVyZW50IG1ldGhvZHMiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTVfbmVnXzExX2Fub255bW91c19yZWNvcmRfaW5oZXJlbnRfbWV0aG9kLm10bCIsInNvdXJjZSI6Ii8vIE5lZ2F0aXZlOiBhbm9ueW1vdXMgcmVjb3JkcyBoYXZlIG5vIG5vbWluYWwgb3duZXIsIHNvIG5vIGluaGVyZW50IG1ldGhvZHMuXG5leHRlbmQgeyB4OiBpNjQgfSB7XG4gICAgZnVuIGdldCgmc2VsZikgLT4gaTY0IHsgc2VsZi54IH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1X25lZ18xMV9hbm9ueW1vdXNfcmVjb3JkX2luaGVyZW50X21ldGhvZC5tdGwiLCJuYW1lIjoic3RhZ2U1X25lZ18xMV9hbm9ueW1vdXNfcmVjb3JkX2luaGVyZW50X21ldGhvZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBpbXBsZW1lbnQgYERyb3BgIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoic3RhZ2U1X25lZ18xMl9hbm9ueW1vdXNfcmVjb3JkX2Ryb3AubXRsIiwic291cmNlIjoiLy8gTmVnYXRpdmU6IGFub255bW91cyByZWNvcmRzIGNhbm5vdCBjYXJyeSBjdXN0b20gdGVhcmRvd24gbG9naWMuXG5leHRlbmQgeyB4OiBpNjQgfTogRHJvcCB7XG4gICAgZnVuIGRyb3AoJnNlbGYpIHt9XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL3N0YWdlNV9uZWdfMTJfYW5vbnltb3VzX3JlY29yZF9kcm9wLm10bCIsIm5hbWUiOiJzdGFnZTVfbmVnXzEyX2Fub255bW91c19yZWNvcmRfZHJvcC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE0IiwiY29sIjpudWxsLCJjb250YWlucyI6Im9ycGhhbiBpbXBsZW1lbnRhdGlvbiIsImxpbmUiOm51bGwsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlNV9uZWdfMTNfYW5vbnltb3VzX3JlY29yZF9ub25sb2NhbF9hc3BlY3QubXRsIiwic291cmNlIjoiLy8gTmVnYXRpdmU6IGBEaXNwbGF5YCBpcyBhIHN0YW5kYXJkLWxpYnJhcnkgYXNwZWN0IChub3QgbG9jYWwgdG8gdGhpcyBtb2R1bGUpLFxuLy8gc28gaXQgY2Fubm90IGJlIGltcGxlbWVudGVkIGZvciBhbiBhbm9ueW1vdXMgcmVjb3JkLlxuZXh0ZW5kIHsgeDogaTY0IH06IERpc3BsYXkge1xuICAgIGZ1biB0b19zdHJpbmcoJnNlbGYpIC0+IFN0cmluZyB7IFwieFwiIH1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvc3RhZ2U1X25lZ18xM19hbm9ueW1vdXNfcmVjb3JkX25vbmxvY2FsX2FzcGVjdC5tdGwiLCJuYW1lIjoic3RhZ2U1X25lZ18xM19hbm9ueW1vdXNfcmVjb3JkX25vbmxvY2FsX2FzcGVjdC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Arrays

`Array<T>` is the built-in ordered sequence type. The shorthand `T[]` is preferred.

```metel
fun main() -> i64 {
    let nums: i64[] := [1, 2, 3];
    let names: Array<String> := ["alice", "bob"];
    if (names.len() == 2) { nums[0] } else { 0 }
}
```

Index access uses `[]` with a `u64` index. Out-of-bounds access causes a panic.

```metel
fun main() -> i64 {
    let nums: i64[] := [1, 2, 3];
    let first := nums[0];
    return first;
}
```

Arrays are usable in `for-in` loops.

> **Since v0.12.0 (RFC-0126): `T[]` is a borrowed view, not an owning buffer.**
> `T[]` will be a non-owning, immutable, unconditionally-`Copy` view over a contiguous run —
> a pointer and a length, produced only by borrowing a `List<T>`, a `[T; N]`, or another
> slice. `a[0] = 9` through a `T[]` will stop compiling; mutation moves to `List<T>` or a
> `[T; N]`. Array literals produce `[T; N]` (below), not `T[]` — `let nums: i64[] = [1, 2,
> 3];` above will keep working via `[T; N]`'s existing implicit coercion to `T[]` (RFC-0053),
> not because the literal itself is a `T[]`.

The three-way split between `T[]`, `[T; N]`, and `List<T>` below reflects the current
design. The exact boundary between them — in particular, how a growable list's storage is
allocated and grown — is not yet fully specified and may change in a future release.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.arrays.legality-1}

`T[]` is an unconditionally-`Copy`, non-owning borrowed view. It has no `Drop`; using a
view does not move the underlying elements out of the view.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0061](../../rfcs/4-implemented/rfc-0061-structural-aspect-bounds.md), [rfc-0071](../../rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md), [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE5IiwiY29sIjpudWxsLCJjb250YWlucyI6Iml0IGlzIGJvcnJvd2VkIGZyb20gYSBgVFtdYCB2aWV3IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoiMzlfYm9ycm93ZWRfYXJyYXlfZm9yX2luX2Nhbm5vdF9tb3ZlX25vbmNvcHkubXRsIiwic291cmNlIjoiZnVuIGZpcnN0PFQ+KGl0ZW1zOiBUW10pIC0+IFQge1xuICAgIGZvciAoaXRlbSBpbiBpdGVtcykge1xuICAgICAgICByZXR1cm4gaXRlbTtcbiAgICB9XG4gICAgcGFuaWMoXCJlbXB0eVwiKVxufVxuXG5mdW4gbWFpbigpIHsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay8zOV9ib3Jyb3dlZF9hcnJheV9mb3JfaW5fY2Fubm90X21vdmVfbm9uY29weS5tdGwiLCJuYW1lIjoiMzlfYm9ycm93ZWRfYXJyYXlfZm9yX2luX2Nhbm5vdF9tb3ZlX25vbmNvcHkubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQwX2JvcnJvd2VkX2FycmF5X2Zvcl9pbl9jb3B5X2lzX3ZhbGlkLm10bCIsInNvdXJjZSI6ImZ1biBmaXJzdDxUOiBDb3B5PihpdGVtczogVFtdKSAtPiBUIHtcbiAgICBmb3IgKGl0ZW0gaW4gaXRlbXMpIHtcbiAgICAgICAgcmV0dXJuIGl0ZW07XG4gICAgfVxuICAgIHBhbmljKFwiZW1wdHlcIilcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHZhbHVlczogaTY0W10gOj0gWzEsIDIsIDNdO1xuICAgIGFzc2VydChmaXJzdCh2YWx1ZXMpID09IDEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay80MF9ib3Jyb3dlZF9hcnJheV9mb3JfaW5fY29weV9pc192YWxpZC5tdGwiLCJuYW1lIjoiNDBfYm9ycm93ZWRfYXJyYXlfZm9yX2luX2NvcHlfaXNfdmFsaWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc2X2FycmF5X2Rpc3BsYXlfc3RydWN0dXJhbF9pbXBsLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIGxldCB4cyA6PSBbMSwgMiwgM107XG4gICAgYXNzZXJ0KHhzLnRvX3N0cmluZygpID09IFwiWzEsIDIsIDNdXCIpO1xuICAgIGFzc2VydChbNCwgNV0udG9fc3RyaW5nKCkgPT0gXCJbNCwgNV1cIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9hc3BlY3RzLzc2X2FycmF5X2Rpc3BsYXlfc3RydWN0dXJhbF9pbXBsLm10bCIsIm5hbWUiOiI3Nl9hcnJheV9kaXNwbGF5X3N0cnVjdHVyYWxfaW1wbC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijc3X2FycmF5X2Nsb25lX3N0cnVjdHVyYWxfaW1wbC5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgQm94IHtcbiAgICB2YWx1ZTogaTY0LFxufVxuXG5leHRlbmQgQm94OiBEaXNwbGF5IHtcbiAgICBmdW4gdG9fc3RyaW5nKCZzZWxmKSAtPiBTdHJpbmcge1xuICAgICAgICByZXR1cm4gc2VsZi52YWx1ZS50b19zdHJpbmcoKTtcbiAgICB9XG59XG5cbmV4dGVuZCBCb3g6IENsb25lIHtcbiAgICBmdW4gY2xvbmUoJnNlbGYpIC0+IFNlbGYge1xuICAgICAgICByZXR1cm4gQm94IHsgdmFsdWUgPSBzZWxmLnZhbHVlIH07XG4gICAgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeHMgOj0gW0JveCB7IHZhbHVlID0gMSB9LCBCb3ggeyB2YWx1ZSA9IDIgfSwgQm94IHsgdmFsdWUgPSAzIH1dO1xuICAgIGxldCB5cyA6PSB4cy5jbG9uZSgpO1xuICAgIGFzc2VydCh5cy50b19zdHJpbmcoKSA9PSBcIlsxLCAyLCAzXVwiKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2FzcGVjdHMvNzdfYXJyYXlfY2xvbmVfc3RydWN0dXJhbF9pbXBsLm10bCIsIm5hbWUiOiI3N19hcnJheV9jbG9uZV9zdHJ1Y3R1cmFsX2ltcGwubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.arrays.legality-2}

An array index expression must have type `u64`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0007](../../rfcs/4-implemented/rfc-0007-uint-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImFycmF5IGluZGV4IG11c3QgYmUgdTY0IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzA0X2FycmF5X25lZ2F0aXZlX2luZGV4Lm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUlthcnJheSBpbmRleCBtdXN0IGJlIHU2NF1cbmZ1biBtYWluKCkge1xuICAgIGxldCBhcnIgOj0gWzEsIDIsIDNdO1xuICAgIGxldCBfeCA6PSBhcnJbLTFdO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvbmVnXzA0X2FycmF5X25lZ2F0aXZlX2luZGV4Lm10bCIsIm5hbWUiOiJuZWdfMDRfYXJyYXlfbmVnYXRpdmVfaW5kZXgubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Fixed-size arrays

`[T; N]` is an array type whose length `N` is a non-negative integer literal known at compile time.
`[T; N]` coerces to `T[]` (not the reverse). `N` must be a non-negative integer literal; variables are not permitted.

```metel
fun main() {
    // Repeat construction: every element is the same value.
    let zeros: [i64; 3] := [0; 3];

    // Literal construction with an explicit sized type.
    let ones: [i64; 3] := [1, 2, 3];

    // Coerces to T[] when a T[] is expected.
    fun first(xs: i64[]) -> i64 { xs[0] }
    let v := first(ones);          // [i64; 3] → i64[]
}
```

Indexing and `for-in` work identically to `T[]`. Array patterns match sized arrays:

```metel
fun sum(xs: [i64; 3]) -> i64 {
    match (xs) {
        [a, b, c] => a + b + c,   // exact-count pattern on [T; 3]
    }
}
```

> **Availability:** Since v0.8.0.

> **Since v0.12.0 (RFC-0126): array literals produce `[T; N]`, not `T[]`.** `[1, 2,
> 3]` will have type `[i64; 3]`; a literal has a statically known length and owns its
> elements, which is what `[T; N]` already is. Slices arise only from borrowing, never from
> a literal. The `[T; N]` → `T[]` coercion above already applies wherever `T[]` is expected —
> a `let`/`var` target, a function argument, a generic instantiation — so this does not by
> itself require touching call sites that already pass a `[T; N]`-typed or explicitly
> `T[]`-annotated value; it only changes what an *unannotated* literal's own type is.

See the note under "Arrays" above — this split is not considered final.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.fixed-size-arrays.legality-1}

An array literal has fixed-size-array type `[T; N]`, not `T[]`, where `N` is its literal
element count.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlM18wNF9zaXplZF9hcnJheXMubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgMzogZml4ZWQtc2l6ZSBhcnJheSB0eXBlIFtUOyBOXVxuLy9cbi8vIFtleHByOyBOXSAgY29uc3RydWN0cyBhIFNpemVkQXJyYXkuXG4vLyBbVDsgTl0gICAgIGlzIHRoZSB0eXBlIGFubm90YXRpb24gc3ludGF4LlxuLy8gW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIChvbmUtZGlyZWN0aW9uYWwpLlxuLy8gSW5kZXhpbmcgW1Q7IE5dIHlpZWxkcyBULlxuLy8gZm9yLWluIG92ZXIgW1Q7IE5dIHlpZWxkcyBULlxuLy8gUGF0dGVybiBbYSwgYiwgY10gbWF0Y2hlcyBbVDsgM10gZXhhY3RseS5cbi8vIFBhdHRlcm4gW2hlYWQsIC4ucmVzdF0gbWF0Y2hlcyBhbnkgYXJyYXkuXG5cbmZ1biBzdW0zKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHtcbiAgICB4c1swXSArIHhzWzFdICsgeHNbMl1cbn1cblxubGV0IHplcm9zOiBbaTY0OyAzXSA6PSBbMDsgM107XG5sZXQgb25lczogIFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbmxldCByZXN1bHQ6IGk2NCA6PSBzdW0zKG9uZXMpO1xuXG4vLyBDb2VyY2lvbjogW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIHdoZW4gcGFzc2VkIGFzIFRbXSBhcmd1bWVudC5cbmZ1biBmaXJzdCh4czogaTY0W10pIC0+IGk2NCB7IHhzWzBdIH1cbmxldCBjb2VyY2VkOiBpNjQgOj0gZmlyc3QoemVyb3MpO1xuXG4vLyBGb3ItaW4gb3ZlciBzaXplZCBhcnJheS5cbmZ1biB0b3RhbCh4czogW2k2NDsgM10pIC0+IGk2NCB7XG4gICAgdmFyIGFjYyA6PSAwO1xuICAgIGZvciAoeCBpbiB4cykge1xuICAgICAgICBhY2MgKz0geDtcbiAgICB9XG4gICAgYWNjXG59XG5cbi8vIGxlbigpIGlzIGF2YWlsYWJsZSBvbiBzaXplZCBhcnJheXMuXG5mdW4gc2l6ZWRfbGVuKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHsgeHMubGVuKCkgfVxubGV0IF9uOiBpNjQgOj0gc2l6ZWRfbGVuKG9uZXMpO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwiLCJuYW1lIjoic3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-2}

`[T; N]` implicitly coerces to `T[]` wherever `T[]` is expected. The reverse coercion
is not permitted.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md), [rfc-0126](../../rfcs/4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQwX2JvcnJvd2VkX2FycmF5X2Zvcl9pbl9jb3B5X2lzX3ZhbGlkLm10bCIsInNvdXJjZSI6ImZ1biBmaXJzdDxUOiBDb3B5PihpdGVtczogVFtdKSAtPiBUIHtcbiAgICBmb3IgKGl0ZW0gaW4gaXRlbXMpIHtcbiAgICAgICAgcmV0dXJuIGl0ZW07XG4gICAgfVxuICAgIHBhbmljKFwiZW1wdHlcIilcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHZhbHVlczogaTY0W10gOj0gWzEsIDIsIDNdO1xuICAgIGFzc2VydChmaXJzdCh2YWx1ZXMpID09IDEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbW92ZV9jaGVjay80MF9ib3Jyb3dlZF9hcnJheV9mb3JfaW5fY29weV9pc192YWxpZC5tdGwiLCJuYW1lIjoiNDBfYm9ycm93ZWRfYXJyYXlfZm9yX2luX2NvcHlfaXNfdmFsaWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlM18wNF9zaXplZF9hcnJheXMubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgMzogZml4ZWQtc2l6ZSBhcnJheSB0eXBlIFtUOyBOXVxuLy9cbi8vIFtleHByOyBOXSAgY29uc3RydWN0cyBhIFNpemVkQXJyYXkuXG4vLyBbVDsgTl0gICAgIGlzIHRoZSB0eXBlIGFubm90YXRpb24gc3ludGF4LlxuLy8gW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIChvbmUtZGlyZWN0aW9uYWwpLlxuLy8gSW5kZXhpbmcgW1Q7IE5dIHlpZWxkcyBULlxuLy8gZm9yLWluIG92ZXIgW1Q7IE5dIHlpZWxkcyBULlxuLy8gUGF0dGVybiBbYSwgYiwgY10gbWF0Y2hlcyBbVDsgM10gZXhhY3RseS5cbi8vIFBhdHRlcm4gW2hlYWQsIC4ucmVzdF0gbWF0Y2hlcyBhbnkgYXJyYXkuXG5cbmZ1biBzdW0zKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHtcbiAgICB4c1swXSArIHhzWzFdICsgeHNbMl1cbn1cblxubGV0IHplcm9zOiBbaTY0OyAzXSA6PSBbMDsgM107XG5sZXQgb25lczogIFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbmxldCByZXN1bHQ6IGk2NCA6PSBzdW0zKG9uZXMpO1xuXG4vLyBDb2VyY2lvbjogW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIHdoZW4gcGFzc2VkIGFzIFRbXSBhcmd1bWVudC5cbmZ1biBmaXJzdCh4czogaTY0W10pIC0+IGk2NCB7IHhzWzBdIH1cbmxldCBjb2VyY2VkOiBpNjQgOj0gZmlyc3QoemVyb3MpO1xuXG4vLyBGb3ItaW4gb3ZlciBzaXplZCBhcnJheS5cbmZ1biB0b3RhbCh4czogW2k2NDsgM10pIC0+IGk2NCB7XG4gICAgdmFyIGFjYyA6PSAwO1xuICAgIGZvciAoeCBpbiB4cykge1xuICAgICAgICBhY2MgKz0geDtcbiAgICB9XG4gICAgYWNjXG59XG5cbi8vIGxlbigpIGlzIGF2YWlsYWJsZSBvbiBzaXplZCBhcnJheXMuXG5mdW4gc2l6ZWRfbGVuKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHsgeHMubGVuKCkgfVxubGV0IF9uOiBpNjQgOj0gc2l6ZWRfbGVuKG9uZXMpO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwiLCJuYW1lIjoic3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzEwX3NpemVkX2FycmF5X2R5bmFtaWNfdG9fZml4ZWQubXRsIiwic291cmNlIjoiLy8gQSBkeW5hbWljIGFycmF5IGhhcyBubyBzdGF0aWNhbGx5IGtub3duIGxlbmd0aCBhbmQgY2Fubm90IHNhdGlzZnkgW1Q7IE5dLlxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGR5bmFtaWM6IGk2NFtdIDo9IFsxLCAyLCAzXTtcbiAgICBsZXQgZml4ZWQ6IFtpNjQ7IDNdIDo9IGR5bmFtaWM7ICAvLyBFUlJPUltUMDAwMV1cbiAgICBwcmludGxuKGZpeGVkWzBdLnRvX3N0cmluZygpKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL3N0YWdlM19uZWdfMTBfc2l6ZWRfYXJyYXlfZHluYW1pY190b19maXhlZC5tdGwiLCJuYW1lIjoic3RhZ2UzX25lZ18xMF9zaXplZF9hcnJheV9keW5hbWljX3RvX2ZpeGVkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-3}

`[T; N]` is a fixed-size-array type only when `N` is a non-negative integer literal;
the element type and literal length both participate in type identity, including for
`[T; 0]`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEVtcHR5IHNpemVkIGFycmF5IFtUOyAwXSBcdTIwMTQgbGVuKCkgcmV0dXJucyAwLlxuICAgIGxldCBlbXB0eTogW2k2NDsgMF0gOj0gWzA7IDBdO1xuICAgIGFzc2VydChlbXB0eS5sZW4oKSA9PSAwKTtcblxuICAgIC8vIFNpbmdsZS1lbGVtZW50IHNpemVkIGFycmF5LlxuICAgIGxldCBzaW5nbGU6IFtpNjQ7IDFdIDo9IFs0Ml07XG4gICAgYXNzZXJ0KHNpbmdsZVswXSA9PSA0Mik7XG5cbiAgICAvLyBSZXBlYXQgd2l0aCBhIG5vbi10cml2aWFsIGV4cHJlc3Npb24uXG4gICAgbGV0IGNvbXB1dGVkOiBbaTY0OyAzXSA6PSBbMiArIDM7IDNdO1xuICAgIGFzc2VydChjb21wdXRlZFswXSA9PSA1KTtcbiAgICBhc3NlcnQoY29tcHV0ZWRbMV0gPT0gNSk7XG4gICAgYXNzZXJ0KGNvbXB1dGVkWzJdID09IDUpO1xuXG4gICAgLy8gTXV0YXRpb24gb2YgYSBzaXplZCBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBhcnJbMV0gOj0gOTk7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDk5KTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29lcmNpb246IFtUOyBOXSBpdGVyYXRlcyB2aWEgZm9yLWluIChzYW1lIGFzIFRbXSkuXG4gICAgbGV0IHNpemVkOiBbaTY0OyA0XSA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIHZhciBkeW5fc3VtIDo9IDA7XG4gICAgZm9yICh4IGluIHNpemVkKSB7XG4gICAgICAgIGR5bl9zdW0gKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KGR5bl9zdW0gPT0gMTAwKTtcblxuICAgIC8vIFBhdHRlcm46IC4ucmVzdCBpcyBlbXB0eSB3aGVuIG9ubHkgb25lIGVsZW1lbnQgaW4gdGhlIHNpemVkIGFycmF5LlxuICAgIGxldCBhcnIxOiBbaTY0OyAxXSA6PSBbNDJdO1xuICAgIGxldCByZXN0X2VtcHR5IDo9IG1hdGNoIChhcnIxKSB7XG4gICAgICAgIFtoZWFkLCAuLnJlc3RdID0+IHtcbiAgICAgICAgICAgIHZhciBjbnQgOj0gMDtcbiAgICAgICAgICAgIGZvciAoXyBpbiByZXN0KSB7IGNudCArPSAxOyB9XG4gICAgICAgICAgICBoZWFkICsgY250XG4gICAgICAgIH0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9lbXB0eSA9PSA0Mik7XG5cbiAgICAvLyBQYXR0ZXJuOiAuLnJlc3QgY29sbGVjdHMgcmVtYWluaW5nIGVsZW1lbnRzLlxuICAgIGxldCBhcnIyOiBbaTY0OyA0XSA6PSBbMSwgMiwgMywgNF07XG4gICAgbGV0IHJlc3Rfc3VtIDo9IG1hdGNoIChhcnIyKSB7XG4gICAgICAgIFtfYSwgX2IsIC4ucmVzdF0gPT4gcmVzdFswXSArIHJlc3RbMV0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9zdW0gPT0gNyk7XG5cbiAgICAvLyBFeGFjdC1jb3VudCBwYXR0ZXJuOiBlbGVtZW50IGJpbmRpbmdzIGFyZSBjb3JyZWN0LlxuICAgIGxldCBjb29yZHM6IFtpNjQ7IDNdIDo9IFszLCA0LCAwXTtcbiAgICBsZXQgZGlzdF9zcSA6PSBtYXRjaCAoY29vcmRzKSB7XG4gICAgICAgIFt4LCB5LCBfel0gPT4geCAqIHggKyB5ICogeSxcbiAgICB9O1xuICAgIGFzc2VydChkaXN0X3NxID09IDI1KTtcblxuICAgIC8vIGZvci1pbiBvdmVyIGEgcmVwZWF0LWNvbnN0cnVjdGVkIHNpemVkIGFycmF5LlxuICAgIHZhciB0b3RhbCA6PSAwO1xuICAgIGZvciAodiBpbiBbNzsgNV0pIHtcbiAgICAgICAgdG90YWwgKz0gdjtcbiAgICB9XG4gICAgYXNzZXJ0KHRvdGFsID09IDM1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsIm5hbWUiOiIxM19zaXplZF9hcnJheV9leHRlbmRlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlM18wNF9zaXplZF9hcnJheXMubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgMzogZml4ZWQtc2l6ZSBhcnJheSB0eXBlIFtUOyBOXVxuLy9cbi8vIFtleHByOyBOXSAgY29uc3RydWN0cyBhIFNpemVkQXJyYXkuXG4vLyBbVDsgTl0gICAgIGlzIHRoZSB0eXBlIGFubm90YXRpb24gc3ludGF4LlxuLy8gW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIChvbmUtZGlyZWN0aW9uYWwpLlxuLy8gSW5kZXhpbmcgW1Q7IE5dIHlpZWxkcyBULlxuLy8gZm9yLWluIG92ZXIgW1Q7IE5dIHlpZWxkcyBULlxuLy8gUGF0dGVybiBbYSwgYiwgY10gbWF0Y2hlcyBbVDsgM10gZXhhY3RseS5cbi8vIFBhdHRlcm4gW2hlYWQsIC4ucmVzdF0gbWF0Y2hlcyBhbnkgYXJyYXkuXG5cbmZ1biBzdW0zKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHtcbiAgICB4c1swXSArIHhzWzFdICsgeHNbMl1cbn1cblxubGV0IHplcm9zOiBbaTY0OyAzXSA6PSBbMDsgM107XG5sZXQgb25lczogIFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbmxldCByZXN1bHQ6IGk2NCA6PSBzdW0zKG9uZXMpO1xuXG4vLyBDb2VyY2lvbjogW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIHdoZW4gcGFzc2VkIGFzIFRbXSBhcmd1bWVudC5cbmZ1biBmaXJzdCh4czogaTY0W10pIC0+IGk2NCB7IHhzWzBdIH1cbmxldCBjb2VyY2VkOiBpNjQgOj0gZmlyc3QoemVyb3MpO1xuXG4vLyBGb3ItaW4gb3ZlciBzaXplZCBhcnJheS5cbmZ1biB0b3RhbCh4czogW2k2NDsgM10pIC0+IGk2NCB7XG4gICAgdmFyIGFjYyA6PSAwO1xuICAgIGZvciAoeCBpbiB4cykge1xuICAgICAgICBhY2MgKz0geDtcbiAgICB9XG4gICAgYWNjXG59XG5cbi8vIGxlbigpIGlzIGF2YWlsYWJsZSBvbiBzaXplZCBhcnJheXMuXG5mdW4gc2l6ZWRfbGVuKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHsgeHMubGVuKCkgfVxubGV0IF9uOiBpNjQgOj0gc2l6ZWRfbGVuKG9uZXMpO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwiLCJuYW1lIjoic3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzA3X3NpemVkX2FycmF5X25fbWlzbWF0Y2gubXRsIiwic291cmNlIjoiLy8gW2V4cHI7IE5dIHdpdGggYW5ub3RhdGlvbiBbVDsgTV0gd2hlcmUgTiBcdTIyNjAgTSBtdXN0IGJlIHJlamVjdGVkLlxubGV0IHg6IFtpNjQ7IDNdIDo9IFswOyA0XTsgIC8vIEVSUk9SW1QwMDAxXVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzX25lZ18wN19zaXplZF9hcnJheV9uX21pc21hdGNoLm10bCIsIm5hbWUiOiJzdGFnZTNfbmVnXzA3X3NpemVkX2FycmF5X25fbWlzbWF0Y2gubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzA4X3NpemVkX2FycmF5X2VsZW1fbWlzbWF0Y2gubXRsIiwic291cmNlIjoiLy8gRWxlbWVudCB0eXBlIG1pc21hdGNoIGluIHJlcGVhdCBjb25zdHJ1Y3Rpb246IFtib29sZWFuOyAzXSBjYW5ub3Qgc2F0aXNmeSBbaTY0OyAzXS5cbmxldCB4OiBbaTY0OyAzXSA6PSBbdHJ1ZTsgM107ICAvLyBFUlJPUltUMDAwMV1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL3N0YWdlM19uZWdfMDhfc2l6ZWRfYXJyYXlfZWxlbV9taXNtYXRjaC5tdGwiLCJuYW1lIjoic3RhZ2UzX25lZ18wOF9zaXplZF9hcnJheV9lbGVtX21pc21hdGNoLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.fixed-size-arrays.dynamics-1}

A repeat array expression `[expr; N]` evaluates `expr` once, then clones that result to
produce all `N` elements.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImZpeGVkX2FycmF5X3JlcGVhdF9ldmFsdWF0ZXNfb25jZS5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICB2YXIgY2FsbHMgOj0gMDtcbiAgICB2YXIgY2FsbHNfcmVmOiAmdmFyIGk2NCA6PSAmdmFyIGNhbGxzO1xuICAgIHZhciBuZXh0IDo9IFsmdmFyIGNhbGxzX3JlZl0gdmFyIHx8IC0+IGk2NCB7XG4gICAgICAgICpjYWxsc19yZWYgKz0gMTtcbiAgICAgICAgKmNhbGxzX3JlZlxuICAgIH07XG4gICAgbGV0IHZhbHVlczogW2k2NDsgM10gOj0gW25leHQoKTsgM107XG4gICAgYXNzZXJ0KGNhbGxzID09IDEpO1xuICAgIGFzc2VydCh2YWx1ZXNbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KHZhbHVlc1sxXSA9PSAxKTtcbiAgICBhc3NlcnQodmFsdWVzWzJdID09IDEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvZml4ZWRfYXJyYXlfcmVwZWF0X2V2YWx1YXRlc19vbmNlLm10bCIsIm5hbWUiOiJmaXhlZF9hcnJheV9yZXBlYXRfZXZhbHVhdGVzX29uY2UubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-4}

Where `[T; N]` is expected, an array literal is accepted only when it contains exactly
`N` elements of type `T`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlM18wNF9zaXplZF9hcnJheXMubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgMzogZml4ZWQtc2l6ZSBhcnJheSB0eXBlIFtUOyBOXVxuLy9cbi8vIFtleHByOyBOXSAgY29uc3RydWN0cyBhIFNpemVkQXJyYXkuXG4vLyBbVDsgTl0gICAgIGlzIHRoZSB0eXBlIGFubm90YXRpb24gc3ludGF4LlxuLy8gW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIChvbmUtZGlyZWN0aW9uYWwpLlxuLy8gSW5kZXhpbmcgW1Q7IE5dIHlpZWxkcyBULlxuLy8gZm9yLWluIG92ZXIgW1Q7IE5dIHlpZWxkcyBULlxuLy8gUGF0dGVybiBbYSwgYiwgY10gbWF0Y2hlcyBbVDsgM10gZXhhY3RseS5cbi8vIFBhdHRlcm4gW2hlYWQsIC4ucmVzdF0gbWF0Y2hlcyBhbnkgYXJyYXkuXG5cbmZ1biBzdW0zKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHtcbiAgICB4c1swXSArIHhzWzFdICsgeHNbMl1cbn1cblxubGV0IHplcm9zOiBbaTY0OyAzXSA6PSBbMDsgM107XG5sZXQgb25lczogIFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbmxldCByZXN1bHQ6IGk2NCA6PSBzdW0zKG9uZXMpO1xuXG4vLyBDb2VyY2lvbjogW1Q7IE5dIGNvZXJjZXMgdG8gVFtdIHdoZW4gcGFzc2VkIGFzIFRbXSBhcmd1bWVudC5cbmZ1biBmaXJzdCh4czogaTY0W10pIC0+IGk2NCB7IHhzWzBdIH1cbmxldCBjb2VyY2VkOiBpNjQgOj0gZmlyc3QoemVyb3MpO1xuXG4vLyBGb3ItaW4gb3ZlciBzaXplZCBhcnJheS5cbmZ1biB0b3RhbCh4czogW2k2NDsgM10pIC0+IGk2NCB7XG4gICAgdmFyIGFjYyA6PSAwO1xuICAgIGZvciAoeCBpbiB4cykge1xuICAgICAgICBhY2MgKz0geDtcbiAgICB9XG4gICAgYWNjXG59XG5cbi8vIGxlbigpIGlzIGF2YWlsYWJsZSBvbiBzaXplZCBhcnJheXMuXG5mdW4gc2l6ZWRfbGVuKHhzOiBbaTY0OyAzXSkgLT4gaTY0IHsgeHMubGVuKCkgfVxubGV0IF9uOiBpNjQgOj0gc2l6ZWRfbGVuKG9uZXMpO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwiLCJuYW1lIjoic3RhZ2UzXzA0X3NpemVkX2FycmF5cy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzA3X3NpemVkX2FycmF5X25fbWlzbWF0Y2gubXRsIiwic291cmNlIjoiLy8gW2V4cHI7IE5dIHdpdGggYW5ub3RhdGlvbiBbVDsgTV0gd2hlcmUgTiBcdTIyNjAgTSBtdXN0IGJlIHJlamVjdGVkLlxubGV0IHg6IFtpNjQ7IDNdIDo9IFswOyA0XTsgIC8vIEVSUk9SW1QwMDAxXVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvc3RhZ2UzX25lZ18wN19zaXplZF9hcnJheV9uX21pc21hdGNoLm10bCIsIm5hbWUiOiJzdGFnZTNfbmVnXzA3X3NpemVkX2FycmF5X25fbWlzbWF0Y2gubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjIiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzA4X3NpemVkX2FycmF5X2VsZW1fbWlzbWF0Y2gubXRsIiwic291cmNlIjoiLy8gRWxlbWVudCB0eXBlIG1pc21hdGNoIGluIHJlcGVhdCBjb25zdHJ1Y3Rpb246IFtib29sZWFuOyAzXSBjYW5ub3Qgc2F0aXNmeSBbaTY0OyAzXS5cbmxldCB4OiBbaTY0OyAzXSA6PSBbdHJ1ZTsgM107ICAvLyBFUlJPUltUMDAwMV1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL3N0YWdlM19uZWdfMDhfc2l6ZWRfYXJyYXlfZWxlbV9taXNtYXRjaC5tdGwiLCJuYW1lIjoic3RhZ2UzX25lZ18wOF9zaXplZF9hcnJheV9lbGVtX21pc21hdGNoLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-5}

A fixed-size array type `[T; N]` is valid as a struct field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQ1X2x2YWx1ZV9wYXRocy5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uOiBmaWVsZCBhbmQgaW5kZXggYXNzaWdubWVudCBtdXN0IHdvcmsgd2l0aCBjaGFpbmVkIGZpZWxkIGFjY2Vzcyxcbi8vIG5vdCBqdXN0IGJhcmUgaWRlbnRpZmllcnMgKCMxMTApLlxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyBTdHJ1Y3QgZGVjbGFyYXRpb25zIGluc2lkZSBmdW5jdGlvbiBib2RpZXMgKCMxMjUpLlxuICAgIHN0cnVjdCBQb2ludCAgICAgeyB4OiBpNjQsIHk6IGk2NCB9XG4gICAgc3RydWN0IExpbmUgICAgICB7IHN0YXJ0OiBQb2ludCwgZW5kOiBQb2ludCB9XG4gICAgc3RydWN0IENvbnRhaW5lciB7IGl0ZW1zOiBbaTY0OyAzXSB9XG5cbiAgICAvLyBDaGFpbmVkIGZpZWxkIGFzc2lnbm1lbnQ6IGEuYi5jID0gdmFsICgjMTEwKVxuICAgIHZhciBsbiA6PSBMaW5lIHsgc3RhcnQgPSBQb2ludCB7IHggPSAwLCB5ID0gMCB9LCBlbmQgPSBQb2ludCB7IHggPSAxMCwgeSA9IDEwIH0gfTtcbiAgICBsbi5zdGFydC54IDo9IDU7XG4gICAgbG4uc3RhcnQueSA6PSA3O1xuICAgIGxuLmVuZC54ICAgOj0gMjA7XG4gICAgYXNzZXJ0KGxuLnN0YXJ0LnggPT0gNSk7XG4gICAgYXNzZXJ0KGxuLnN0YXJ0LnkgPT0gNyk7XG4gICAgYXNzZXJ0KGxuLmVuZC54ICAgPT0gMjApO1xuICAgIGFzc2VydChsbi5lbmQueSAgID09IDEwKTsgIC8vIHVuY2hhbmdlZFxuXG4gICAgLy8gSW5kZXggYXNzaWdubWVudCB2aWEgYSBmaWVsZC1hY2Nlc3MgcmVjZWl2ZXI6IGEuZmllbGRbaV0gPSB2YWwgKCMxMTApXG4gICAgdmFyIGMgOj0gQ29udGFpbmVyIHsgaXRlbXMgPSBbMSwgMiwgM10gfTtcbiAgICBjLml0ZW1zWzFdIDo9IDk5O1xuICAgIGFzc2VydChjLml0ZW1zWzFdID09IDk5KTtcbiAgICBhc3NlcnQoYy5pdGVtc1swXSA9PSAxKTsgICAvLyB1bmNoYW5nZWRcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvNDVfbHZhbHVlX3BhdGhzLm10bCIsIm5hbWUiOiI0NV9sdmFsdWVfcGF0aHMubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-6}

A fixed-size array may have another fixed-size array as its element type, such as
`[[i64; 2]; 2]`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImZpeGVkX2FycmF5X25lc3RlZC5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIHtcbiAgICBsZXQgbWF0cml4OiBbW2k2NDsgMl07IDJdIDo9IFtbMSwgMl0sIFszLCA0XV07XG4gICAgYXNzZXJ0KG1hdHJpeFswXVsxXSA9PSAyKTtcbiAgICBhc3NlcnQobWF0cml4WzFdWzBdID09IDMpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvdHlwZXMvZml4ZWRfYXJyYXlfbmVzdGVkLm10bCIsIm5hbWUiOiJmaXhlZF9hcnJheV9uZXN0ZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-7}

An exact array pattern for a `[T; N]` value must have a compatible element count; a
different exact count is rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEyX3NpemVkX2FycmF5Lm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIFJlcGVhdCBjb25zdHJ1Y3Rpb246IFtleHByOyBOXS5cbiAgICBsZXQgemVyb3MgOj0gWzA7IDNdO1xuICAgIGFzc2VydCh6ZXJvc1swXSA9PSAwKTtcbiAgICBhc3NlcnQoemVyb3NbMV0gPT0gMCk7XG4gICAgYXNzZXJ0KHplcm9zWzJdID09IDApO1xuXG4gICAgLy8gTGl0ZXJhbCBjb25zdHJ1Y3Rpb24gdHlwZWQgYXMgW1Q7IE5dLlxuICAgIGxldCBvbmVzOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgYXNzZXJ0KG9uZXNbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KG9uZXNbMV0gPT0gMik7XG4gICAgYXNzZXJ0KG9uZXNbMl0gPT0gMyk7XG5cbiAgICAvLyBJbmRleGluZy5cbiAgICBsZXQgYXJyOiBbaTY0OyA0XSA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIGFzc2VydChhcnJbMF0gPT0gMTApO1xuICAgIGFzc2VydChhcnJbM10gPT0gNDApO1xuXG4gICAgLy8gRm9yLWluIGl0ZXJhdGlvbi5cbiAgICB2YXIgc3VtIDo9IDA7XG4gICAgZm9yICh4IGluIFsxOyA0XSkge1xuICAgICAgICBzdW0gKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KHN1bSA9PSA0KTtcblxuICAgIC8vIEFycmF5IHBhdHRlcm4gXHUyMDE0IGV4YWN0IG1hdGNoIChzaXplZCBhcnJheSBzY3J1dGluZWUpLlxuICAgIGxldCBzaXplZDogW2k2NDsgM10gOj0gWzEsIDIsIDNdO1xuICAgIGxldCBnb3QgOj0gbWF0Y2ggKHNpemVkKSB7XG4gICAgICAgIFthLCBiLCBjXSA9PiBhICsgYiArIGMsXG4gICAgfTtcbiAgICBhc3NlcnQoZ290ID09IDYpO1xuXG4gICAgLy8gQXJyYXkgcGF0dGVybiBcdTIwMTQgcmVzdCBiaW5kaW5nICh3b3JrcyBvbiBhbnkgYXJyYXkpLlxuICAgIGxldCBhcnIyOiBbaTY0OyA0XSA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIGxldCB0YWlsX3N1bSA6PSBtYXRjaCAoYXJyMikge1xuICAgICAgICBbX2hlYWQsIC4ucmVzdF0gPT4gcmVzdFswXSArIHJlc3RbMV0gKyByZXN0WzJdLFxuICAgIH07XG4gICAgYXNzZXJ0KHRhaWxfc3VtID09IDkwKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzEyX3NpemVkX2FycmF5Lm10bCIsIm5hbWUiOiIxMl9zaXplZF9hcnJheS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIEVtcHR5IHNpemVkIGFycmF5IFtUOyAwXSBcdTIwMTQgbGVuKCkgcmV0dXJucyAwLlxuICAgIGxldCBlbXB0eTogW2k2NDsgMF0gOj0gWzA7IDBdO1xuICAgIGFzc2VydChlbXB0eS5sZW4oKSA9PSAwKTtcblxuICAgIC8vIFNpbmdsZS1lbGVtZW50IHNpemVkIGFycmF5LlxuICAgIGxldCBzaW5nbGU6IFtpNjQ7IDFdIDo9IFs0Ml07XG4gICAgYXNzZXJ0KHNpbmdsZVswXSA9PSA0Mik7XG5cbiAgICAvLyBSZXBlYXQgd2l0aCBhIG5vbi10cml2aWFsIGV4cHJlc3Npb24uXG4gICAgbGV0IGNvbXB1dGVkOiBbaTY0OyAzXSA6PSBbMiArIDM7IDNdO1xuICAgIGFzc2VydChjb21wdXRlZFswXSA9PSA1KTtcbiAgICBhc3NlcnQoY29tcHV0ZWRbMV0gPT0gNSk7XG4gICAgYXNzZXJ0KGNvbXB1dGVkWzJdID09IDUpO1xuXG4gICAgLy8gTXV0YXRpb24gb2YgYSBzaXplZCBhcnJheSBlbGVtZW50LlxuICAgIHZhciBhcnI6IFtpNjQ7IDNdIDo9IFsxLCAyLCAzXTtcbiAgICBhcnJbMV0gOj0gOTk7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDk5KTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29lcmNpb246IFtUOyBOXSBpdGVyYXRlcyB2aWEgZm9yLWluIChzYW1lIGFzIFRbXSkuXG4gICAgbGV0IHNpemVkOiBbaTY0OyA0XSA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIHZhciBkeW5fc3VtIDo9IDA7XG4gICAgZm9yICh4IGluIHNpemVkKSB7XG4gICAgICAgIGR5bl9zdW0gKz0geDtcbiAgICB9XG4gICAgYXNzZXJ0KGR5bl9zdW0gPT0gMTAwKTtcblxuICAgIC8vIFBhdHRlcm46IC4ucmVzdCBpcyBlbXB0eSB3aGVuIG9ubHkgb25lIGVsZW1lbnQgaW4gdGhlIHNpemVkIGFycmF5LlxuICAgIGxldCBhcnIxOiBbaTY0OyAxXSA6PSBbNDJdO1xuICAgIGxldCByZXN0X2VtcHR5IDo9IG1hdGNoIChhcnIxKSB7XG4gICAgICAgIFtoZWFkLCAuLnJlc3RdID0+IHtcbiAgICAgICAgICAgIHZhciBjbnQgOj0gMDtcbiAgICAgICAgICAgIGZvciAoXyBpbiByZXN0KSB7IGNudCArPSAxOyB9XG4gICAgICAgICAgICBoZWFkICsgY250XG4gICAgICAgIH0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9lbXB0eSA9PSA0Mik7XG5cbiAgICAvLyBQYXR0ZXJuOiAuLnJlc3QgY29sbGVjdHMgcmVtYWluaW5nIGVsZW1lbnRzLlxuICAgIGxldCBhcnIyOiBbaTY0OyA0XSA6PSBbMSwgMiwgMywgNF07XG4gICAgbGV0IHJlc3Rfc3VtIDo9IG1hdGNoIChhcnIyKSB7XG4gICAgICAgIFtfYSwgX2IsIC4ucmVzdF0gPT4gcmVzdFswXSArIHJlc3RbMV0sXG4gICAgfTtcbiAgICBhc3NlcnQocmVzdF9zdW0gPT0gNyk7XG5cbiAgICAvLyBFeGFjdC1jb3VudCBwYXR0ZXJuOiBlbGVtZW50IGJpbmRpbmdzIGFyZSBjb3JyZWN0LlxuICAgIGxldCBjb29yZHM6IFtpNjQ7IDNdIDo9IFszLCA0LCAwXTtcbiAgICBsZXQgZGlzdF9zcSA6PSBtYXRjaCAoY29vcmRzKSB7XG4gICAgICAgIFt4LCB5LCBfel0gPT4geCAqIHggKyB5ICogeSxcbiAgICB9O1xuICAgIGFzc2VydChkaXN0X3NxID09IDI1KTtcblxuICAgIC8vIGZvci1pbiBvdmVyIGEgcmVwZWF0LWNvbnN0cnVjdGVkIHNpemVkIGFycmF5LlxuICAgIHZhciB0b3RhbCA6PSAwO1xuICAgIGZvciAodiBpbiBbNzsgNV0pIHtcbiAgICAgICAgdG90YWwgKz0gdjtcbiAgICB9XG4gICAgYXNzZXJ0KHRvdGFsID09IDM1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzEzX3NpemVkX2FycmF5X2V4dGVuZGVkLm10bCIsIm5hbWUiOiIxM19zaXplZF9hcnJheV9leHRlbmRlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA4IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzA5X3NpemVkX2FycmF5X3BhdHRlcm5fdW5kZXJjb3VudC5tdGwiLCJzb3VyY2UiOiIvLyBFeGFjdC1jb3VudCBwYXR0ZXJuIFthLCBiXSBvbiBhIFtpNjQ7IDNdIHNjcnV0aW5lZSBoYXMgdGhlIHdyb25nIGVsZW1lbnQgY291bnQuXG4vLyBUaGUgY29uc3RyYWludCBbaTY0OyAzXSB+IFtpNjQ7IDJdIGZhaWxzLCBsZWF2aW5nIHRoZSBtYXRjaCBub24tZXhoYXVzdGl2ZS5cbmZ1biBtYWluKCkge1xuICAgIGxldCBzaXplZDogW2k2NDsgM10gOj0gWzEsIDIsIDNdO1xuICAgIGxldCBfIDo9IG1hdGNoIChzaXplZCkgeyBbYSwgYl0gPT4gYSArIGIsIH07ICAvLyBFUlJPUltUMDAwOF1cbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL3N0YWdlM19uZWdfMDlfc2l6ZWRfYXJyYXlfcGF0dGVybl91bmRlcmNvdW50Lm10bCIsIm5hbWUiOiJzdGFnZTNfbmVnXzA5X3NpemVkX2FycmF5X3BhdHRlcm5fdW5kZXJjb3VudC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-8}

The length in `[T; N]` is an integer literal, not a named generic type parameter or an
arbitrary runtime expression.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfc2l6ZWRfYXJyYXlfbmFtZWRfbGVuZ3RoLm10bCIsInNvdXJjZSI6ImxldCB2YWx1ZXM6IFtpNjQ7IE5dID0gWzEsIDJdO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL25lZ19zaXplZF9hcnJheV9uYW1lZF9sZW5ndGgubXRsIiwibmFtZSI6Im5lZ19zaXplZF9hcnJheV9uYW1lZF9sZW5ndGgubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.fixed-size-arrays.legality-9}

Every literal index into `[T; 0]` is statically rejected because it is out of bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0053](../../rfcs/4-implemented/rfc-0053-fixed-size-arrays.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTNfbmVnXzExX3NpemVkX2FycmF5X3plcm9fbGl0ZXJhbF9pbmRleC5tdGwiLCJzb3VyY2UiOiIvLyBFdmVyeSBsaXRlcmFsIGluZGV4IGlzIG91dCBvZiBib3VuZHMgZm9yIGFuIGVtcHR5IGZpeGVkLXNpemUgYXJyYXkuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZW1wdHk6IFtpNjQ7IDBdIDo9IFtdO1xuICAgIGxldCB4IDo9IGVtcHR5WzBdOyAgLy8gRVJST1JbVDAwMDFdXG4gICAgcHJpbnRsbih4LnRvX3N0cmluZygpKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL3N0YWdlM19uZWdfMTFfc2l6ZWRfYXJyYXlfemVyb19saXRlcmFsX2luZGV4Lm10bCIsIm5hbWUiOiJzdGFnZTNfbmVnXzExX3NpemVkX2FycmF5X3plcm9fbGl0ZXJhbF9pbmRleC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## References

> **Availability:** Since v0.10.0.

Reference types provide explicit aliasing.

```metel
fun main() -> i64 {
    var value := 1;
    let p: &i64 := &value;
    let q: &var i64 := &var value;
    *q := *p + 1;
    return q;
}
```

Metel has two reference types:

- `&T` — shared immutable reference to `T`
- `&var T` — exclusive mutable reference to `T`

> **Planned for v0.13.0 (RFC-0122): shared XOR exclusive — a place may have any number of `&T` borrows, or exactly one `&var T`, never both.**

"Exclusive" means exactly that rule. It is **not yet enforced**: the current interpreter has
no borrow checker, so a program may hold two `&var T` to the same place and will not be
rejected.

`&var T` coerces to `&T`. The reverse coercion does not exist. Both are non-owning
aliases — a reference never owns the value it points to.

`&T` is `Copy`; `&var T` is not, so an exclusive reference is moved on use rather than
duplicated. Passing one as an argument reborrows instead of moving — see
[Ownership — References and moves](ownership.md#references-and-moves).

References are first-class values, but they are distinct from the referent type. Ordinary
access — field reads/writes, indexing, method dispatch, reading a plain value out — goes
through auto-deref and type-directed copy; an explicit dereference operator `*p` is also
available (v0.11.0) for reading through a reference and for writing through a
`&var T` (`*p = v`). See [Expressions — References](expressions.md#references).

`&var` accepts arbitrary addressable lvalue paths — struct fields, tuple elements, array elements, and chains thereof. Writes through the resulting `&var T` propagate back to the original storage location:

```metel
struct Counter { value: i64 }

fun main() -> i64 {
    var c := Counter { value = 0 };
    let p: &var i64 := &var c.value;
    *p := 42;
    return c.value;   // 42
}
```

> **Availability:** `&var` for lvalue paths since v0.10.0.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.references.legality-1}

An `&var T` reference may be used where `&T` is expected; an `&T` reference may not be
used where `&var T` is expected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA1X211dF9yZWZlcmVuY2VfY29lcmNlc190b19zaGFyZWQubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzE6ICZ2YXIgVCBjb2VyY2VzIHRvICZUICh0aGUgcmV2ZXJzZSBkb2VzIG5vdCBleGlzdCkuXG5mdW4gcmVhZF9zaGFyZWQocjogJmk2NCkgLT4gaTY0IHtcbiAgICByZXR1cm4gcjtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gNztcbiAgICBsZXQgbTogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBtMjogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCBzOiAmaTY0IDo9IG0yO1xuICAgIGFzc2VydChyZWFkX3NoYXJlZChzKSA9PSA3KTtcbiAgICBhc3NlcnQocmVhZF9zaGFyZWQobSkgPT0gNyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzA1X211dF9yZWZlcmVuY2VfY29lcmNlc190b19zaGFyZWQubXRsIiwibmFtZSI6IjA1X211dF9yZWZlcmVuY2VfY29lcmNlc190b19zaGFyZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### Reading a value out of a reference

No field, no method, no operator — just the plain value a reference points to. This
cannot be a *move* (references never own their referent), only a *copy*, and only when
the referent's type permits copying:

```metel
fun main() -> i64 {
    let x := 42;
    let r: &i64 := &x;
    let y: i64 := r;   // type-directed copy: y's declared type differs from r's
    return y;
}
```

**The copy fires at every position where a declared or expected type is already
known** — not only `let`/`var` bindings and explicit ascription, but also a `return`
value against the enclosing function's declared return type, a `break` value against
the enclosing `loop`'s inferred type, and any tail expression of a function/method/
closure body, an `if`/`else` branch, or a `match` arm (each of those resolves its
result against a declared or expected type the same way a `let` binding does):

```metel
fun bump(p: &var i64) -> i64 {
    *p += 1;
    p          // tail expression, no explicit `return` — copies out of p
}
```

It never fires silently at a plain call site; `fun f(v: i64)` called as `f(r)` where
`r: &i64` is a type error, not an implicit copy. Argument position has no declared type
of its own for the rule to compare against, the same reason type-directed extraction of
an allocated value never fires implicitly at a plain-parameter call site either
(`public/rfcs/2-accepted/rfc-0066-allocated-value-extraction.md` §3a — not yet
integrated, cited here only for the parallel).

Chains through multiple reference layers the same way auto-deref does — reaching the
declared type may require copying out of more than one layer:

```metel
fun main() -> i64 {
    let x := 42;
    let r: &i64 := &x;
    let rr: &&i64 := &r;
    let y: i64 := rr;   // copies through both layers of the chain
    return y;
}
```

**Until affine ownership (`Copy`/`Drop`, not yet integrated) lands, this applies to
every type** — the interpreter has no move semantics today (everything is deep-cloned on
bind), so there is no non-`Copy` type yet to exclude. Once ownership is integrated, a
non-`Copy` `T` cannot be produced this way.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.references.reading-a-value-out-of-a-reference.legality-1}

Where a declared or expected non-reference type is known, a reference expression may
copy out its referent through every reference layer only when the referent is `Copy`.
This applies to bindings, ascriptions, returns, breaks, and tail expressions, but not
to an un-ascribed call argument.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0067a](../../rfcs/4-implemented/rfc-0067a-reference-types.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (8)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjAxX3JlYWRfY29weV9hdF9yZXR1cm4ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzNhOiByZWFkaW5nIGEgcGxhaW4gdmFsdWUgb3V0IG9mIGEgcmVmZXJlbmNlIHZpYSBhbiBleHBsaWNpdCBgcmV0dXJuYFxuLy8gd2l0aCBhIGRlY2xhcmVkIHJldHVybiB0eXBlLiBUaGlzIGlzIHRoZSBSRkMncyBvd24gd29ya2VkIGV4YW1wbGUuXG5mdW4gZigpIC0+IGk2NCB7XG4gICAgdmFyIG4gOj0gMTtcbiAgICBsZXQgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgICpwIDo9IDQ7XG4gICAgcmV0dXJuIHA7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChmKCkgPT0gNCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzAxX3JlYWRfY29weV9hdF9yZXR1cm4ubXRsIiwibmFtZSI6IjAxX3JlYWRfY29weV9hdF9yZXR1cm4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjAyX3JlYWRfY29weV9hdF90YWlsX2V4cHJlc3Npb24ubXRsIiwic291cmNlIjoiLy8gUkZDLTAwNjdhIFx1MDBhNzNhOiByZWFkLWNvcHkgYXQgYW4gaW1wbGljaXQgdGFpbCBleHByZXNzaW9uIChubyBgcmV0dXJuYCBrZXl3b3JkKSxcbi8vIGluY2x1ZGluZyB0aHJvdWdoIGFuIGBpZmAvYGVsc2VgIHdob3NlIGJyYW5jaGVzIGFyZSBib3RoIHJlZmVyZW5jZS10eXBlZCB3aGlsZSB0aGVcbi8vIGZ1bmN0aW9uJ3Mgb3duIGRlY2xhcmVkIHJldHVybiB0eXBlIGlzIHRoZSBwbGFpbiByZWZlcmVudCB0eXBlLlxuZnVuIHBpY2soY29uZDogYm9vbGVhbiwgYTogJmk2NCwgYjogJmk2NCkgLT4gaTY0IHtcbiAgICBpZiAoY29uZCkgeyBhIH0gZWxzZSB7IGIgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeCA6PSAxMDtcbiAgICBsZXQgeSA6PSAyMDtcbiAgICBhc3NlcnQocGljayh0cnVlLCAmeCwgJnkpID09IDEwKTtcbiAgICBhc3NlcnQocGljayhmYWxzZSwgJngsICZ5KSA9PSAyMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzLzAyX3JlYWRfY29weV9hdF90YWlsX2V4cHJlc3Npb24ubXRsIiwibmFtZSI6IjAyX3JlYWRfY29weV9hdF90YWlsX2V4cHJlc3Npb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjAzX3JlYWRfY29weV9hdF9sb29wX2JyZWFrLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDY3YSBcdTAwYTczYTogcmVhZC1jb3B5IGF0IGEgYGxvb3AgeyBicmVhayB2YWx1ZTsgfWAgd2hlcmUgdGhlIGJyZWFrIHZhbHVlIGlzIGFcbi8vIHJlZmVyZW5jZSwgbWFkZSBjb25jcmV0ZSB2aWEgYW4gZXhwbGljaXQgYXNjcmlwdGlvbiBvbiB0aGUgYnJlYWsgdmFsdWUgaXRzZWxmLlxuZnVuIG1haW4oKSB7XG4gICAgdmFyIG4gOj0gMDtcbiAgICBsZXQgcDogJnZhciBpNjQgOj0gJnZhciBuO1xuICAgIGxldCByZXN1bHQ6IGk2NCA6PSBsb29wIHtcbiAgICAgICAgYnJlYWsgKHA6IGk2NCk7XG4gICAgfTtcbiAgICBhc3NlcnQocmVzdWx0ID09IDApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy8wM19yZWFkX2NvcHlfYXRfbG9vcF9icmVhay5tdGwiLCJuYW1lIjoiMDNfcmVhZF9jb3B5X2F0X2xvb3BfYnJlYWsubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjA3X3JlYWRfY29weV90aHJvdWdoX3JlZmVyZW5jZV9jaGFpbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA2N2EgXHUwMGE3MzogYXV0by1kZXJlZiBjaGFpbnMgdGhyb3VnaCBhcmJpdHJhcnkgZGVwdGggKFwiYSAmJlQgd2lsbCBkZXJlZlxuLy8gdGhyb3VnaCBib3RoIGxldmVscyBpZiBuZWVkZWRcIikgYXBwbGllcyB0byByZWFkLWNvcHkgdGhlIHNhbWUgYXMgb3JkaW5hcnlcbi8vIGF1dG8tZGVyZWYgXHUyMDE0IHJlYWRpbmcgYSBwbGFpbiB2YWx1ZSBvdXQgb2YgYSBjaGFpbiBvZiByZWZlcmVuY2VzIG11c3QgcGVlbFxuLy8gZXZlcnkgbGF5ZXIsIG5vdCBqdXN0IG9uZS5cbmZ1biBtYWluKCkge1xuICAgIGxldCBuIDo9IDc7XG4gICAgbGV0IHI6ICZpNjQgOj0gJm47XG4gICAgbGV0IHJyOiAmJmk2NCA6PSAmcjtcbiAgICBsZXQgcnJyOiAmJiZpNjQgOj0gJnJyO1xuXG4gICAgbGV0IHg6IGk2NCA6PSBycjtcbiAgICBhc3NlcnQoeCA9PSA3KTtcblxuICAgIGxldCB5OiBpNjQgOj0gcnJyO1xuICAgIGFzc2VydCh5ID09IDcpO1xuXG4gICAgLy8gTWl4ZWQgc2hhcmVkL211dCBjaGFpbi5cbiAgICB2YXIgbSA6PSA5O1xuICAgIGxldCBtcjogJnZhciBpNjQgOj0gJnZhciBtO1xuICAgIGxldCBybXI6ICYmdmFyIGk2NCA6PSAmbXI7XG4gICAgbGV0IHo6IGk2NCA6PSBybXI7XG4gICAgYXNzZXJ0KHogPT0gOSk7XG5cbiAgICAvLyBSZWFkLWNvcHkgdGhyb3VnaCBhIGNoYWluIGF0IGByZXR1cm5gLCBub3QganVzdCBgbGV0YC5cbiAgICBhc3NlcnQocmVhZF90aHJvdWdoX2NoYWluKCZycikgPT0gNyk7XG59XG5cbmZ1biByZWFkX3Rocm91Z2hfY2hhaW4ocnJwOiAmJiZpNjQpIC0+IGk2NCB7XG4gICAgcmV0dXJuIHJycDtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3JlZmVyZW5jZXMvMDdfcmVhZF9jb3B5X3Rocm91Z2hfcmVmZXJlbmNlX2NoYWluLm10bCIsIm5hbWUiOiIwN19yZWFkX2NvcHlfdGhyb3VnaF9yZWZlcmVuY2VfY2hhaW4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjEzX3JlYWRfY29weV9mcm9tX2NhbGxfcmVzdWx0Lm10bCIsInNvdXJjZSI6Ii8vIFJlYWQtY29weSAoUkZDLTAwNjdhIFx1MDBhNzNhKSBtdXN0IGRlY2lkZSB3aGV0aGVyIHRvIHBlZWwgYWdhaW5zdCB0aGUgKnN1YnN0aXR1dGVkKiB0eXBlLFxuLy8gbm90IHRoZSByYXcgb25lLiBBIGNhbGwgcmV0dXJuaW5nIGAmVGAgeWllbGRzIGEgZnJlc2ggaW5mZXJlbmNlIHZhcmlhYmxlIGF0IHRoZSBwb2ludFxuLy8gYGNvbnN0cmFpbl93aXRoX3JlYWRfY29weWAgcnVuczsgbWF0Y2hpbmcgdGhhdCByYXcgdmFyaWFibGUgYWdhaW5zdCBhIHJlZmVyZW5jZSBwYXR0ZXJuXG4vLyBmYWlscywgc28gdGhlIHBlZWwgd2FzIHNpbGVudGx5IHNraXBwZWQgYW5kIHRoZSBsYXRlciB1bmlmaWNhdGlvbiByZXBvcnRlZCBUMDAwMS5cbi8vXG4vLyBUaGUgZWZmZWN0IHdhcyB0aGF0IGBsZXQgbjogaTY0ID0gZygpO2AgZmFpbGVkIHdoZXJlIGBsZXQgbjogaTY0ID0gcjtgIHN1Y2NlZWRlZCAtLVxuLy8gc2FtZSBwb3NpdGlvbiwgc2FtZSB0eXBlcywgZGlmZmVyZW50IHZhbHVlIHNoYXBlLiBSRkMtMDExMiBcdTAwYTcxLjAuXG5cbmZ1biBzaGFyZWQoKSAtPiAmaTY0IHtcbiAgICBsZXQgYSA6PSA0MjtcbiAgICByZXR1cm4gJmE7XG59XG5cbmZ1biBjaGFpbmVkKCkgLT4gJiZpNjQge1xuICAgIGxldCBhIDo9IDQyO1xuICAgIGxldCByOiAmaTY0IDo9ICZhO1xuICAgIHJldHVybiAmcjtcbn1cblxuZnVuIHRocm91Z2hfcmV0dXJuKCkgLT4gaTY0IHtcbiAgICByZXR1cm4gc2hhcmVkKCk7XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIGxldCBhbm5vdGF0aW9uXG4gICAgbGV0IG46IGk2NCA6PSBzaGFyZWQoKTtcbiAgICBhc3NlcnQobiA9PSA0Mik7XG5cbiAgICAvLyBiaW5kaW5nIHRoZSBjYWxsIHJlc3VsdCBmaXJzdCwgdGhlbiBjb3B5aW5nIG91dCBhdCB0aGUgYW5ub3RhdGlvblxuICAgIGxldCByIDo9IHNoYXJlZCgpO1xuICAgIGxldCBtOiBpNjQgOj0gcjtcbiAgICBhc3NlcnQobSA9PSA0Mik7XG5cbiAgICAvLyBhc2NyaXB0aW9uXG4gICAgbGV0IGEgOj0gc2hhcmVkKCk6IGk2NDtcbiAgICBhc3NlcnQoYSA9PSA0Mik7XG5cbiAgICAvLyByZXR1cm4gcG9zaXRpb25cbiAgICBhc3NlcnQodGhyb3VnaF9yZXR1cm4oKSA9PSA0Mik7XG5cbiAgICAvLyBldmVyeSBsYXllciBpcyBwZWVsZWQsIG5vdCBqdXN0IG9uZVxuICAgIGxldCBjOiBpNjQgOj0gY2hhaW5lZCgpO1xuICAgIGFzc2VydChjID09IDQyKTtcblxuICAgIC8vIHRoZSByZWZlcmVuY2UgaXRzZWxmIGlzIHN0aWxsIGF2YWlsYWJsZSB3aGVuIHRoYXQgaXMgd2hhdCBpcyBhc2tlZCBmb3JcbiAgICBsZXQga2VlcCA6PSBzaGFyZWQoKTtcbiAgICBhc3NlcnQoKmtlZXAgPT0gNDIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy8xM19yZWFkX2NvcHlfZnJvbV9jYWxsX3Jlc3VsdC5tdGwiLCJuYW1lIjoiMTNfcmVhZF9jb3B5X2Zyb21fY2FsbF9yZXN1bHQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjE0X211dF9maWVsZF9wb2ludGVyLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDQ1OiBNdXRhYmxlIGFkZHJlc3Mtb2YgbHZhbHVlIHBhdGhzIFx1MjAxNCBmYXQgcG9pbnRlciAoTXV0RmllbGRQb2ludGVyKSB0ZXN0cy5cbi8vIFJGQy0wMDY3YTogKlQvKm11dCBUIHJlbmFtZWQgdG8gJlQvJnZhciBUOyBleHBsaWNpdCAqcCBkZXJlZiByZXBsYWNlZCBieVxuLy8gd3JpdGUtdGhyb3VnaCBhc3NpZ25tZW50IGFuZCB0eXBlLWRpcmVjdGVkIHJlYWQtY29weS5cblxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuc3RydWN0IFJlY3QgeyB0b3BfbGVmdDogUG9pbnQsIGJvdHRvbV9yaWdodDogUG9pbnQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgd3JpdGUgdGhyb3VnaCBmYXQgcG9pbnRlci5cbiAgICB2YXIgcCA6PSBQb2ludCB7IHggPSAxLCB5ID0gMiB9O1xuICAgIGxldCBweDogJnZhciBpNjQgOj0gJnZhciBwLng7XG4gICAgKnB4IDo9IDEwO1xuICAgIGFzc2VydChwLnggPT0gMTApO1xuICAgIGFzc2VydChwLnkgPT0gMik7XG5cbiAgICAvLyAmdmFyIHN0cnVjdC5maWVsZCBcdTIwMTQgY29tcG91bmQgYXNzaWduIHRocm91Z2ggZmF0IHBvaW50ZXIuXG4gICAgKnB4ICs9IDU7XG4gICAgYXNzZXJ0KHAueCA9PSAxNSk7XG5cbiAgICAvLyBSZWFkIHRocm91Z2ggZmF0IHBvaW50ZXIgXHUyMDE0IHR5cGUtZGlyZWN0ZWQgY29weSB5aWVsZHMgY3VycmVudCBmaWVsZCB2YWx1ZS5cbiAgICBsZXQgcmVhZF94OiBpNjQgOj0gcHg7XG4gICAgYXNzZXJ0KHJlYWRfeCA9PSAxNSk7XG5cbiAgICAvLyAmdmFyIHR1cGxlIGVsZW1lbnQuXG4gICAgdmFyIHQgOj0gKDEwMCwgMjAwKTtcbiAgICBsZXQgdDE6ICZ2YXIgaTY0IDo9ICZ2YXIgdC4xO1xuICAgICp0MSA6PSA5OTk7XG4gICAgYXNzZXJ0KHQuMSA9PSA5OTkpO1xuICAgIGFzc2VydCh0LjAgPT0gMTAwKTtcblxuICAgIC8vICZ2YXIgYXJyYXkgZWxlbWVudC5cbiAgICB2YXIgYXJyOiBbaTY0OyAzXSA6PSBbMSwgMiwgM107XG4gICAgbGV0IGExOiAmdmFyIGk2NCA6PSAmdmFyIGFyclsxXTtcbiAgICAqYTEgOj0gNDI7XG4gICAgYXNzZXJ0KGFyclswXSA9PSAxKTtcbiAgICBhc3NlcnQoYXJyWzFdID09IDQyKTtcbiAgICBhc3NlcnQoYXJyWzJdID09IDMpO1xuXG4gICAgLy8gQ29tcG91bmQgYXNzaWduIHRocm91Z2ggYXJyYXkgZWxlbWVudCBmYXQgcG9pbnRlci5cbiAgICAqYTEgKz0gODtcbiAgICBhc3NlcnQoYXJyWzFdID09IDUwKTtcblxuICAgIC8vIENoYWluZWQgcGF0aDogJnZhciBvdXRlci5pbm5lci5maWVsZCAobmVzdGVkIHN0cnVjdCkuXG4gICAgdmFyIHIgOj0gUmVjdCB7XG4gICAgICAgIHRvcF9sZWZ0ID0gICAgIFBvaW50IHsgeCA9IDAsIHkgPSAwIH0sXG4gICAgICAgIGJvdHRvbV9yaWdodCA9IFBvaW50IHsgeCA9IDEwLCB5ID0gMTAgfSxcbiAgICB9O1xuICAgIGxldCBicng6ICZ2YXIgaTY0IDo9ICZ2YXIgci5ib3R0b21fcmlnaHQueDtcbiAgICAqYnJ4IDo9IDIwO1xuICAgIGFzc2VydChyLmJvdHRvbV9yaWdodC54ID09IDIwKTtcbiAgICBhc3NlcnQoci50b3BfbGVmdC54ID09IDApO1xuXG4gICAgLy8gQXV0by1kZXJlZiBmaWVsZCBhY2Nlc3MgdGhyb3VnaCBNdXRGaWVsZFJlZmVyZW5jZSBcdTIwMTQgRmllbGRBY2Nlc3MgYXV0by1kZXJlZi5cbiAgICB2YXIgcSA6PSBQb2ludCB7IHggPSA1LCB5ID0gNyB9O1xuICAgIGxldCBxcHRyOiAmdmFyIFBvaW50IDo9ICZ2YXIgcTtcbiAgICBhc3NlcnQocXB0ci54ID09IDUpO1xuICAgIHFwdHIueSA6PSA5OTtcbiAgICBhc3NlcnQocS55ID09IDk5KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3R5cGVzLzE0X211dF9maWVsZF9wb2ludGVyLm10bCIsIm5hbWUiOiIxNF9tdXRfZmllbGRfcG9pbnRlci5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDAxIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzA2X25vX3JlYWRfY29weV9hdF9jYWxsX2FyZ3VtZW50Lm10bCIsInNvdXJjZSI6Ii8vIFRZUEVDSEVDS19FUlJPUltUMDAwMV1cbi8vIFJGQy0wMTEwOiB1bmRlciB0aGUgR28gbW9kZWwsIHJlYWRpbmcgdGhyb3VnaCBhIHJlZmVyZW5jZSBpcyBpbXBsaWNpdCBvbmx5IGF0XG4vLyBzZWxlY3RvcnMgKGZpZWxkLCBpbmRleCwgbWV0aG9kKS4gQSBjYWxsIGFyZ3VtZW50IGlzIG5vdCBhIHNlbGVjdG9yLCBzbyBwYXNzaW5nIGFcbi8vIHJlZmVyZW5jZSB3aGVyZSB0aGUgcGFyYW1ldGVyIGV4cGVjdHMgdGhlIHJlZmVyZW50IHR5cGUgaXMgYSBoYXJkIG1pc21hdGNoIFx1MjAxNCB3cml0ZVxuLy8gYHRha2VzX2k2NCgqcilgLlxuLy9cbi8vIE5vdGUgdGhlIHJlYXNvbiBSRkMtMDA2N2EgXHUwMGE3M2Egb3JpZ2luYWxseSBnYXZlIGZvciB0aGlzIFx1MjAxNCBcInRoZXJlIGlzIG5vIGRlY2xhcmVkIHR5cGVcbi8vIGZvciB0aGUgYXJndW1lbnQgaXRzZWxmIHRvIGNvbXBhcmUgYWdhaW5zdFwiIFx1MjAxNCBpcyBmYWN0dWFsbHkgd3Jvbmc6IGBwYXJhbV9oaW50c2Bcbi8vIGFscmVhZHkgdGhyZWFkcyB0aGUgcGFyYW1ldGVyJ3MgZGVjbGFyZWQgdHlwZSBoZXJlIGZvciBtb25vbW9ycGhpYyBjYWxsZWVzLiBUaGVcbi8vIGJlaGF2aW9yIGlzIHJpZ2h0OyB0aGUganVzdGlmaWNhdGlvbiB3YXMgbm90LiBTZWUgUkZDLTAxMTIgXHUwMGE3NC4xLCB3aGljaCByZS1leGFtaW5lZFxuLy8gY2xvc2luZyB0aGlzIGdhcCBhbmQgZGVjbGluZWQgaXQgZGVsaWJlcmF0ZWx5IHJhdGhlciB0aGFuIGJ5IGFjY2lkZW50LlxuZnVuIHRha2VzX2k2NCh4OiBpNjQpIHt9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBuIDo9IDU7XG4gICAgbGV0IHI6ICZpNjQgOj0gJm47XG4gICAgdGFrZXNfaTY0KHIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvcmVmZXJlbmNlcy9uZWdfMDZfbm9fcmVhZF9jb3B5X2F0X2NhbGxfYXJndW1lbnQubXRsIiwibmFtZSI6Im5lZ18wNl9ub19yZWFkX2NvcHlfYXRfY2FsbF9hcmd1bWVudC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6IlQwMDI0IiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnXzE0X3JlYWRfY29weV9vZl9ub25fY29weV92YWx1ZV9hdF9sZXRfaXNfcmVqZWN0ZWQubXRsIiwic291cmNlIjoiLy8gVFlQRUNIRUNLX0VSUk9SW1QwMDI0XVxuLy8gIzY0OTogUkZDLTAwNjdhIFx1MDBhNzNhJ3MgcmVhZC1jb3B5IHJlcXVpcmVzIHRoZSByZWZlcmVudCB0byBiZSBgQ29weWAgLS0gcmVhZGluZyBhXG4vLyBub24tYENvcHlgIHZhbHVlIG91dCBvZiBhIHNoYXJlZCByZWZlcmVuY2UgYXQgYSBgbGV0YCBiaW5kaW5nIG11c3QgYmUgcmVqZWN0ZWQsXG4vLyBub3Qgc2lsZW50bHkgZHVwbGljYXRlZC5cbnN0cnVjdCBOb3RDb3B5IHsgdjogU3RyaW5nIH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IG93bmVkIDo9IE5vdENvcHkgeyB2ID0gXCJ4XCIgfTtcbiAgICBsZXQgcjogJk5vdENvcHkgOj0gJm93bmVkO1xuICAgIGxldCBjb3B5OiBOb3RDb3B5IDo9IHI7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9yZWZlcmVuY2VzL25lZ18xNF9yZWFkX2NvcHlfb2Zfbm9uX2NvcHlfdmFsdWVfYXRfbGV0X2lzX3JlamVjdGVkLm10bCIsIm5hbWUiOiJuZWdfMTRfcmVhZF9jb3B5X29mX25vbl9jb3B5X3ZhbHVlX2F0X2xldF9pc19yZWplY3RlZC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## List\<T\>

> **Availability:** Since v0.8.0.

`List<T>` is the standard growable-sequence type. Use it when you need to append, pop, or otherwise mutate a sequence. Use `T[]` when the sequence is fixed after construction.

```metel
fun main() {
    var xs: List<i64> := List::new();
    xs.push(1);
    xs.push(2);
    xs.push(3);
    println(xs.len().to_string());   // 3
    let last := xs.pop();             // Some { value = 3 }
}
```

**Construction:**

| Form | Description |
|------|-------------|
| `List::new()` | Empty list |
| `List::from(arr)` | Construct from a `T[]` — copies elements |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `push` | `(&var self, value: T)` | Append an element |
| `pop` | `(&var self) -> Perhaps<T>` | Remove and return the last element, or `None` |
| `len` | `(&self) -> i64` | Number of elements |
| `get` | `(&self, index: i64) -> Perhaps<T>` | Bounds-checked access |
| `as_slice` | `(&self) -> T[]` | View as an immutable array (no copy) |

`List<T>` does not implicitly coerce to `T[]`. Call `.as_slice()` to get a read-only view.

> **Since v0.12.0 (RFC-0126): `as_slice` is what its signature already says.**
> Today `as_slice` returns the same underlying storage, but the result is deep-copied at
> whatever binding or return receives it, so "no copy" describes only the call itself, not
> the value's subsequent lifetime. Once `T[]` is a genuine borrowed view, the returned slice
> stays a live view for as long as it is used — still bounded by `self`'s lifetime, not
> copied away from it.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.list-t.dynamics-1}

`List::new()` creates an empty list, and `List::from(source)` creates a list containing
the elements of `source`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-2}

`push` appends an element; `pop` removes and returns the last element, or `None` for an
empty list.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-3}

`len` reports the list's current number of elements, including changes made by `push`
and `pop`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.list-t.dynamics-4}

`get(i)` returns `Some` for an in-bounds element and `None` when `i` is out of bounds.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.list-t.legality-1}

A `List<T>` is distinct from `T[]`; obtaining its array view requires an explicit
`.as_slice()` call.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0054](../../rfcs/4-implemented/rfc-0054-list-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM4X2J1aWx0aW5zLm10bCIsInNvdXJjZSI6ImZ1biBtYWluKCkge1xuICAgIC8vIHRvX3N0cmluZyBtZXRob2RcbiAgICBhc3NlcnQoMC50b19zdHJpbmcoKSAgICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCg0Mi50b19zdHJpbmcoKSAgICA9PSBcIjQyXCIpO1xuICAgIGFzc2VydCgoLTcpLnRvX3N0cmluZygpICA9PSBcIi03XCIpO1xuICAgIGFzc2VydCgxLjUudG9fc3RyaW5nKCkgICA9PSBcIjEuNVwiKTtcbiAgICBhc3NlcnQoMC4wLnRvX3N0cmluZygpICAgPT0gXCIwXCIpO1xuICAgIGFzc2VydCh0cnVlLnRvX3N0cmluZygpICA9PSBcInRydWVcIik7XG4gICAgYXNzZXJ0KGZhbHNlLnRvX3N0cmluZygpID09IFwiZmFsc2VcIik7XG4gICAgLy8gU3RyaW5nOjpsZW5cbiAgICBhc3NlcnQoXCJcIi5sZW4oKSAgICAgICAgPT0gMCk7XG4gICAgYXNzZXJ0KFwiaGVsbG9cIi5sZW4oKSAgID09IDUpO1xuICAgIGFzc2VydChcImFiY1wiLmxlbigpICAgICA9PSAzKTtcbiAgICAvLyBzdHJpbmcgY29uY2F0ZW5hdGlvblxuICAgIGFzc2VydChcImZvb1wiICsgXCJiYXJcIiA9PSBcImZvb2JhclwiKTtcbiAgICBhc3NlcnQoXCJcIiArIFwieHl6XCIgICAgPT0gXCJ4eXpcIik7XG4gICAgYXNzZXJ0KFwiYWJjXCIgKyBcIlwiICAgID09IFwiYWJjXCIpO1xuICAgIGFzc2VydChcImhlbGxvXCIgKyBcIiwgXCIgKyBcIndvcmxkXCIgPT0gXCJoZWxsbywgd29ybGRcIik7XG4gICAgbGV0IHdobyA6PSBcIndvcmxkXCI7XG4gICAgYXNzZXJ0KFwiaGVsbG8sICR7d2hvfVwiID09IFwiaGVsbG8sIHdvcmxkXCIpO1xuICAgIGFzc2VydChcIm49JHs0Mn1cIiA9PSBcIm49NDJcIik7XG4gICAgYXNzZXJ0KFwiZmxhZz0ke3RydWV9XCIgPT0gXCJmbGFnPXRydWVcIik7XG4gICAgYXNzZXJ0KFwidmFsdWU9JHtcXFwieFxcXCJ9XCIgPT0gXCJ2YWx1ZT14XCIpO1xuICAgIGFzc2VydChcInBhaXI9JHtcXFwieFxcXCIgKyBcXFwieVxcXCJ9XCIgPT0gXCJwYWlyPXh5XCIpO1xuICAgIGFzc2VydChcIlxcJHt2YWx1ZX1cIiA9PSBcIlxcJHt2YWx1ZX1cIik7XG4gICAgYXNzZXJ0KFwiJDVcIiA9PSBcIiQ1XCIpO1xuICAgIC8vIExpc3Q8VD46IG5ldywgcHVzaCwgbGVuLCBnZXQsIHBvcCwgYXNfc2xpY2UsIGZyb21cbiAgICB2YXIgbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgYXNzZXJ0KCgmbHN0KS5sZW4oKSA9PSAwKTtcbiAgICBsc3QucHVzaCgxMCk7XG4gICAgbHN0LnB1c2goMjApO1xuICAgIGxzdC5wdXNoKDMwKTtcbiAgICBhc3NlcnQoKCZsc3QpLmxlbigpID09IDMpO1xuICAgIC8vIGdldCByZXR1cm5zIFBlcmhhcHM8VD4gKGJvdW5kcy1jaGVja2VkKVxuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICgoJmxzdCkuZ2V0KDk5KSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCByZW1vdmVzIGFuZCByZXR1cm5zIHRoZSBsYXN0IGVsZW1lbnRcbiAgICBtYXRjaCAobHN0LnBvcCgpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMCksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIGFzc2VydCgoJmxzdCkubGVuKCkgPT0gMik7XG4gICAgLy8gYXNfc2xpY2UgcmV0dXJucyBhIFRbXSB2aWV3XG4gICAgbHN0LnB1c2goOTkpO1xuICAgIGxldCBzbCA6PSAoJmxzdCkuYXNfc2xpY2UoKTtcbiAgICBhc3NlcnQoc2xbMF0gPT0gMTApO1xuICAgIGFzc2VydChzbFsyXSA9PSA5OSk7XG4gICAgLy8gTGlzdDo6ZnJvbSBjb3BpZXMgYW4gZXhpc3RpbmcgVFtdIGFycmF5XG4gICAgbGV0IHNyYzogaTY0W10gOj0gWzEsIDIsIDMsIDQsIDVdO1xuICAgIGxldCBsc3QyIDo9IExpc3Q6OmZyb20oc3JjKTtcbiAgICBhc3NlcnQobHN0Mi5sZW4oKSA9PSA1KTtcbiAgICAvLyBCdWlsZGluZyBhIGxpc3Qgd2l0aCBhIGxvb3AgdGhlbiBjb252ZXJ0aW5nIHRvIFRbXVxuICAgIHZhciBidWlsdDogTGlzdDxpNjQ+IDo9IExpc3Q6Om5ldygpO1xuICAgIHZhciBpIDo9IDE7XG4gICAgd2hpbGUgKGkgPD0gNSkge1xuICAgICAgICBidWlsdC5wdXNoKGkgKiBpKTtcbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBhc3NlcnQoKCZidWlsdCkubGVuKCkgPT0gNSk7XG4gICAgbGV0IGJ1aWx0X2FyciA6PSAoJmJ1aWx0KS5hc19zbGljZSgpO1xuICAgIGFzc2VydChidWlsdF9hcnJbMF0gPT0gMSk7XG4gICAgYXNzZXJ0KGJ1aWx0X2Fycls0XSA9PSAyNSk7XG4gICAgLy8gZ2V0IGF0IGJvdW5kYXJ5IGluZGljZXNcbiAgICB2YXIgYm91bmRhcnk6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBib3VuZGFyeS5wdXNoKDEwMCk7XG4gICAgYm91bmRhcnkucHVzaCgyMDApO1xuICAgIGJvdW5kYXJ5LnB1c2goMzAwKTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoKCZib3VuZGFyeSkuZ2V0KDIpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzMDApLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBwb3Agb24gZW1wdHkgbGlzdCByZXR1cm5zIE5vbmVcbiAgICB2YXIgZW1wdHlfbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgbWF0Y2ggKGVtcHR5X2xzdC5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuICAgIC8vIHBvcCB1bnRpbCBlbXB0eSwgdmVyaWZ5aW5nIGVhY2ggdmFsdWVcbiAgICB2YXIgZHJhaW46IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBkcmFpbi5wdXNoKDcpO1xuICAgIGRyYWluLnB1c2goOCk7XG4gICAgZHJhaW4ucHVzaCg5KTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDkpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDgpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICBtYXRjaCAoZHJhaW4ucG9wKCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcbiAgICBhc3NlcnQoZHJhaW4ubGVuKCkgPT0gMCk7XG4gICAgLy8gcHVzaCBhZnRlciBwb3BcbiAgICB2YXIgcmV1c2U6IExpc3Q8aTY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICByZXVzZS5wdXNoKDEpO1xuICAgIHJldXNlLnB1c2goMik7XG4gICAgcmV1c2UucG9wKCk7XG4gICAgcmV1c2UucHVzaCg5OSk7XG4gICAgYXNzZXJ0KCgmcmV1c2UpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJnJldXNlKS5nZXQoMSkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDk5KSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgLy8gTGlzdDo6ZnJvbSBvbiBlbXB0eSBhcnJheVxuICAgIGxldCBlbXB0eV9zcmM6IGk2NFtdIDo9IFtdO1xuICAgIGxldCBsc3RfZnJvbV9lbXB0eSA6PSBMaXN0Ojpmcm9tKGVtcHR5X3NyYyk7XG4gICAgYXNzZXJ0KGxzdF9mcm9tX2VtcHR5LmxlbigpID09IDApO1xuICAgIC8vIGFzX3NsaWNlIG9uIGVtcHR5IGxpc3QgcHJvZHVjZXMgZW1wdHkgYXJyYXlcbiAgICBsZXQgZW1wdHlfc2xpY2UgOj0gKCZlbXB0eV9sc3QpLmFzX3NsaWNlKCk7XG4gICAgYXNzZXJ0KGVtcHR5X3NsaWNlLmxlbigpID09IDApO1xuICAgIC8vIExpc3Q8U3RyaW5nPlxuICAgIHZhciB3b3JkczogTGlzdDxTdHJpbmc+IDo9IExpc3Q6Om5ldygpO1xuICAgIHdvcmRzLnB1c2goXCJoZWxsb1wiKTtcbiAgICB3b3Jkcy5wdXNoKFwid29ybGRcIik7XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDIpO1xuICAgIG1hdGNoICgoJndvcmRzKS5nZXQoMCkpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IFwiaGVsbG9cIiksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIG1hdGNoICh3b3Jkcy5wb3AoKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gXCJ3b3JsZFwiKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG4gICAgYXNzZXJ0KCgmd29yZHMpLmxlbigpID09IDEpO1xuICAgIC8vIExpc3Q8ZjY0PlxuICAgIHZhciBmbG9hdHM6IExpc3Q8ZjY0PiA6PSBMaXN0OjpuZXcoKTtcbiAgICBmbG9hdHMucHVzaCgxLjUpO1xuICAgIGZsb2F0cy5wdXNoKDIuNSk7XG4gICAgZmxvYXRzLnB1c2goMy41KTtcbiAgICBhc3NlcnQoKCZmbG9hdHMpLmxlbigpID09IDMpO1xuICAgIG1hdGNoICgoJmZsb2F0cykuZ2V0KDEpKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyLjUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcbiAgICAvLyBMaXN0PGJvb2xlYW4+XG4gICAgdmFyIGZsYWdzOiBMaXN0PGJvb2xlYW4+IDo9IExpc3Q6Om5ldygpO1xuICAgIGZsYWdzLnB1c2godHJ1ZSk7XG4gICAgZmxhZ3MucHVzaChmYWxzZSk7XG4gICAgZmxhZ3MucHVzaCh0cnVlKTtcbiAgICBhc3NlcnQoKCZmbGFncykubGVuKCkgPT0gMyk7XG4gICAgbWF0Y2ggKCgmZmxhZ3MpLmdldCgyKSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gdHJ1ZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuICAgIC8vIGZvci1pbiBvdmVyIGFzX3NsaWNlIHJlc3VsdFxuICAgIHZhciBzdW1fbHN0OiBMaXN0PGk2ND4gOj0gTGlzdDo6bmV3KCk7XG4gICAgc3VtX2xzdC5wdXNoKDEwKTtcbiAgICBzdW1fbHN0LnB1c2goMjApO1xuICAgIHN1bV9sc3QucHVzaCgzMCk7XG4gICAgdmFyIHRvdGFsIDo9IDA7XG4gICAgZm9yICh4IGluIHN1bV9sc3QuYXNfc2xpY2UoKSkge1xuICAgICAgICB0b3RhbCArPSB4O1xuICAgIH1cbiAgICBhc3NlcnQodG90YWwgPT0gNjApO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvYnVpbHRpbnMvMzhfYnVpbHRpbnMubXRsIiwibmFtZSI6IjM4X2J1aWx0aW5zLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

## Type Ascription

> **Availability:** Since v0.2.0.

The `:` operator [asserts that an expression has a given type without performing any runtime conversion](#spec.types.type-ascription.legality-1). It is a pure type-inference hint — no code is emitted at runtime.

Type ascription is mainly an ergonomics feature. Most code should type-check from
its surrounding context alone; `:` is for the cases where spelling out the intended
type inline is clearer than introducing a separate annotated binding.

```metel
fun main() -> i64 {
    let xs := [] : i64[];
    let x  := 1 : i64;
    if (xs.len() == 0) { x } else { 0 }
}
```

[Ascription fails at compile time if the inferred type of the sub-expression cannot be unified with the ascribed type](#spec.types.type-ascription.legality-2). For example, `1 : String` is invalid. Use `as` to convert between types; use `:` only when the value already has the target type.

<!-- doc-example: expect-fail reason="demonstrates an ascription failure -- the type error is the point" -->
```metel
fun main() -> i64 {
    let y := 1 : String;
    return 0;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.type-ascription.legality-1}

`expr : T` constrains `expr` to type `T` and supplies `T` as its expected type; it performs
no runtime conversion.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md), [rfc-0023](../../rfcs/4-implemented/rfc-0023-ascription-vs-turbofish.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgODogdHlwZSBhc2NyaXB0aW9uIG9wZXJhdG9yIGA6YC5cblxuLy8gRW1wdHkgYXJyYXkgZWxlbWVudCB0eXBlIHJlc29sdmVkIHZpYSBhc2NyaXB0aW9uXG5sZXQgbjogaTY0W10gOj0gW10gOiBpNjRbXTtcblxuLy8gSWRlbnRpdHkgYXNjcmlwdGlvbiBvbiBhIGxpdGVyYWxcbmxldCB4OiBpNjQgOj0gMSA6IGk2NDtcblxuLy8gQXNjcmlwdGlvbiBvbiBhIHZhcmlhYmxlIHJlZmVyZW5jZVxuZnVuIGNoZWNrX3ZhcigpIHtcbiAgICBsZXQgdjogYm9vbGVhbiA6PSB0cnVlO1xuICAgIGxldCB3OiBib29sZWFuIDo9IHYgOiBib29sZWFuO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluIGFyZ3VtZW50IHBvc2l0aW9uXG5mdW4gdGFrZV9pbnRzKGFycjogaTY0W10pIC0+IGk2NCB7IGFyci5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHRha2VfaW50cyhbXSA6IGk2NFtdKTtcblxuLy8gQXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHR3byBlbXB0eS1hcnJheSBhcmd1bWVudHNcbmZ1biB0d29fYXJyYXlzKGE6IGk2NFtdLCBiOiBmNjRbXSkgLT4gaTY0IHsgYS5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHR3b19hcnJheXMoW10gOiBpNjRbXSwgW10gOiBmNjRbXSk7XG5cbi8vIEFzY3JpcHRpb24gb24gYSBzdHJ1Y3QgbGl0ZXJhbFxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuZnVuIGNoZWNrX3N0cnVjdCgpIHtcbiAgICBsZXQgcDogUG9pbnQgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSA6IFBvaW50O1xufVxuXG4vLyBBc2NyaXB0aW9uIG9uIGEgdHVwbGVcbmZ1biBjaGVja190dXBsZSgpIHtcbiAgICBsZXQgdDogKGk2NCwgYm9vbGVhbikgOj0gKDEsIHRydWUpIDogKGk2NCwgYm9vbGVhbik7XG59XG5cbi8vIEFzY3JpcHRpb24gYXMgdGhlIHRhaWwgZXhwcmVzc2lvbiBvZiBhIGZ1bmN0aW9uIGJvZHlcbmZ1biByZXR1cm5zX2FzY3JpYmVkKCkgLT4gaTY0IHtcbiAgICA0MiA6IGk2NFxufVxuXG4vLyBBc2NyaXB0aW9uIHJlc29sdmVzIHRoZSB0eXBlIG9mIGFuIHVuYW5ub3RhdGVkIGxldCBiaW5kaW5nXG5mdW4gY2hlY2tfaW5mZXJyZWQoKSB7XG4gICAgbGV0IGFyciA6PSBbXSA6IGk2NFtdO1xuICAgIGxldCBfOiBpNjQgOj0gYXJyLmxlbigpO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluc2lkZSBhIGJpbmFyeSBleHByZXNzaW9uIG9wZXJhbmRcbmZ1biBjaGVja19iaW5vcCgpIHtcbiAgICBsZXQgXzogYm9vbGVhbiA6PSAoMSA6IGk2NCkgPT0gMTtcbn1cblxuLy8gYXMgY29udmVyc2lvbiBzdGlsbCB3b3JrcyBhbG9uZ3NpZGUgYXNjcmlwdGlvblxubGV0IGY6IGY2NCA6PSAxIGFzIGY2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InR1cmJvZmlzaF9yZXR1cm5fYW5kX2FzY3JpcHRpb25fcGFyYW1faW5fc2FtZV9jYWxsLm10bCIsInNvdXJjZSI6Ii8vIFR1cmJvZmlzaCBkaXNhbWJpZ3VhdGVzIFQsIHdoaWNoIGFwcGVhcnMgb25seSBpbiB0aGUgcmV0dXJuIHBvc2l0aW9uO1xuLy8gYXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHRoZSBvdGhlcndpc2UtYW1iaWd1b3VzIGBOb25lYCBhcmd1bWVudCwgc2luY2UgYVxuLy8gZ2VuZXJpYy1zY2hlbWUgY2FsbGVlJ3Mgb3duIHBhcmFtZXRlciB0eXBlcyBhcmVuJ3QgYXZhaWxhYmxlIGFzIGhpbnRzIGZvclxuLy8gaXRzIGFyZ3VtZW50cyBhdCBhbGwgKHVubGlrZSBhIGNvbmNyZXRlLCBub24tZ2VuZXJpYyBjYWxsZWUpIC0tIGJvdGhcbi8vIG1lY2hhbmlzbXMgYXJlIGRvaW5nIHJlYWwsIGluZGVwZW5kZW50IHdvcmsgaW4gdGhlIHNhbWUgY2FsbC5cbmZ1biBtYWtlPFQ+KGZhbGxiYWNrOiBQZXJoYXBzPGk2ND4pIC0+IFQge1xuICAgIHJldHVybiBtYWtlKGZhbGxiYWNrKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbWFrZTo6PGk2ND4oTm9uZSA6IFBlcmhhcHM8aTY0Pik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9nZW5lcmljcy90dXJib2Zpc2hfcmV0dXJuX2FuZF9hc2NyaXB0aW9uX3BhcmFtX2luX3NhbWVfY2FsbC5tdGwiLCJuYW1lIjoidHVyYm9maXNoX3JldHVybl9hbmRfYXNjcmlwdGlvbl9wYXJhbV9pbl9zYW1lX2NhbGwubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-2}

An ascription is valid only when the expression's type unifies with the ascribed type;
otherwise it is a type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzAyX2FzY3JpYmVfdHlwZV9taXNtYXRjaC5tdGwiLCJzb3VyY2UiOiIvLyBTdGFnZSA4IG5lZ2F0aXZlOiBhc2NyaXB0aW9uIHdpdGggaW5jb21wYXRpYmxlIHR5cGUgaXMgYSB0eXBlIGVycm9yLlxuLy8gYDEgOiBmNjRgIGlzIGFuIGVycm9yIFx1MjAxNCB1c2UgYDEgYXMgZjY0YCB0byBjb252ZXJ0LlxuXG5sZXQgejogZjY0IDo9IDEgOiBmNjQ7IC8vIEVSUk9SW1QwMDAxXVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvYnVpbHRpbnMvc3RhZ2U4X25lZ18wMl9hc2NyaWJlX3R5cGVfbWlzbWF0Y2gubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDJfYXNjcmliZV90eXBlX21pc21hdGNoLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.type-ascription.legality-3}

An expression may contain at most one type ascription; a second `:` in the same ascription
position is a parse error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZThfbmVnXzA4X2NoYWluZWRfdHlwZV9hc2NyaXB0aW9uLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDIxIFx1MDBhNzQ6IGFuIGV4cHJlc3Npb24gYWNjZXB0cyBhdCBtb3N0IG9uZSB0eXBlIGFzY3JpcHRpb24uXG5sZXQgdmFsdWUgOj0gMSA6IGk2NCA6IGk2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF9uZWdfMDhfY2hhaW5lZF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

### When ascription helps

Type inference uses surrounding expected types. That expected type can come from a `let` annotation, a function return type, a callee's parameter types, or the surrounding expression context.

Because of that, ambiguous literals like `[]` and `None` often type-check without explicit ascription when the context already determines their type:

```metel
fun zip_lengths(a: i64[], b: String[]) -> i64 {
    return a.len() + b.len();
}

fun make_row(use_default: boolean, fallback: i64[]) -> i64[] {
    return match (use_default) {
        true  => [],
        false => fallback,
    };
}

fun first_or_default(items: i64[], fallback: Perhaps<i64>) -> i64 {
    return match (fallback) {
        Some { value } => value,
        None => if (items.len() > 0) { items[0] } else { 0 },
    };
}

fun main() -> i64 {
    let total := zip_lengths([], ["a", "b"]);
    let row := make_row(true, [1, 2, 3]);
    let first := first_or_default([1, 2, 3], None);
    return total + row.len() + first;
}
```

Ascription is still useful when no surrounding context fixes the type:

```metel
fun main() -> i64 {
    let arr := [] : i64[];
    let value := None : Perhaps<i64>;
    match (value) {
        Some { value } => value + arr.len(),
        None => arr.len(),
    }
}
```

Without such context, ambiguous literals remain a type error. For example, `let x = None;` does not provide enough information to infer the element type.

<!-- doc-example: expect-fail reason="demonstrates an ambiguous None -- the type error is the point" -->
```metel
fun main() -> i64 {
    let x := None;
    return 0;
}
```

## Type Casting

The `as` operator [performs an explicit conversion from `expr`'s type to `T`](#spec.types.type-casting.dynamics-1). It desugars to a call to the `From` aspect and is infallible — the result is the target type directly.

```metel
fun main() {
    let x: i32 := 1000i32;
    let b: i8  := x as i8;    // wraps: 1000 mod 256 → -24
    let f: f32 := x as f32;   // 1000.0f32
    let u: u64 := x as u64;   // 1000u64

    let pi: f64 := 3.14;
    let n: i32  := pi as i32; // truncates toward zero → 3
}
```

All pairwise casts among `i8`, `i16`, `i32`, `i64`, `u8`, `u16`, `u32`, `u64`, `f32`, `f64` are supported. Narrowing integer casts wrap (two's-complement truncation). f64-to-integer casts truncate toward zero.

Because `as` desugars to `From`, user-defined types become castable by implementing `From<SourceType>` for the target type.

<details>
<summary>Formal rules</summary>

##### Dynamic Semantics {#spec.types.type-casting.dynamics-1}

`expr as T` evaluates an explicit conversion of `expr` to `T` via `From<S>::from` (where
`S` is `expr`'s type) and produces a value of type `T`. Not restricted to numeric types —
any type with an applicable `From<S>` implementation is a valid cast target.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0021](../../rfcs/4-implemented/rfc-0021-type-ascription.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwic291cmNlIjoiLy8gU3RhZ2UgODogdHlwZSBhc2NyaXB0aW9uIG9wZXJhdG9yIGA6YC5cblxuLy8gRW1wdHkgYXJyYXkgZWxlbWVudCB0eXBlIHJlc29sdmVkIHZpYSBhc2NyaXB0aW9uXG5sZXQgbjogaTY0W10gOj0gW10gOiBpNjRbXTtcblxuLy8gSWRlbnRpdHkgYXNjcmlwdGlvbiBvbiBhIGxpdGVyYWxcbmxldCB4OiBpNjQgOj0gMSA6IGk2NDtcblxuLy8gQXNjcmlwdGlvbiBvbiBhIHZhcmlhYmxlIHJlZmVyZW5jZVxuZnVuIGNoZWNrX3ZhcigpIHtcbiAgICBsZXQgdjogYm9vbGVhbiA6PSB0cnVlO1xuICAgIGxldCB3OiBib29sZWFuIDo9IHYgOiBib29sZWFuO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluIGFyZ3VtZW50IHBvc2l0aW9uXG5mdW4gdGFrZV9pbnRzKGFycjogaTY0W10pIC0+IGk2NCB7IGFyci5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHRha2VfaW50cyhbXSA6IGk2NFtdKTtcblxuLy8gQXNjcmlwdGlvbiBkaXNhbWJpZ3VhdGVzIHR3byBlbXB0eS1hcnJheSBhcmd1bWVudHNcbmZ1biB0d29fYXJyYXlzKGE6IGk2NFtdLCBiOiBmNjRbXSkgLT4gaTY0IHsgYS5sZW4oKSB9XG5sZXQgXzogaTY0IDo9IHR3b19hcnJheXMoW10gOiBpNjRbXSwgW10gOiBmNjRbXSk7XG5cbi8vIEFzY3JpcHRpb24gb24gYSBzdHJ1Y3QgbGl0ZXJhbFxuc3RydWN0IFBvaW50IHsgeDogaTY0LCB5OiBpNjQgfVxuZnVuIGNoZWNrX3N0cnVjdCgpIHtcbiAgICBsZXQgcDogUG9pbnQgOj0gUG9pbnQgeyB4ID0gMSwgeSA9IDIgfSA6IFBvaW50O1xufVxuXG4vLyBBc2NyaXB0aW9uIG9uIGEgdHVwbGVcbmZ1biBjaGVja190dXBsZSgpIHtcbiAgICBsZXQgdDogKGk2NCwgYm9vbGVhbikgOj0gKDEsIHRydWUpIDogKGk2NCwgYm9vbGVhbik7XG59XG5cbi8vIEFzY3JpcHRpb24gYXMgdGhlIHRhaWwgZXhwcmVzc2lvbiBvZiBhIGZ1bmN0aW9uIGJvZHlcbmZ1biByZXR1cm5zX2FzY3JpYmVkKCkgLT4gaTY0IHtcbiAgICA0MiA6IGk2NFxufVxuXG4vLyBBc2NyaXB0aW9uIHJlc29sdmVzIHRoZSB0eXBlIG9mIGFuIHVuYW5ub3RhdGVkIGxldCBiaW5kaW5nXG5mdW4gY2hlY2tfaW5mZXJyZWQoKSB7XG4gICAgbGV0IGFyciA6PSBbXSA6IGk2NFtdO1xuICAgIGxldCBfOiBpNjQgOj0gYXJyLmxlbigpO1xufVxuXG4vLyBBc2NyaXB0aW9uIGluc2lkZSBhIGJpbmFyeSBleHByZXNzaW9uIG9wZXJhbmRcbmZ1biBjaGVja19iaW5vcCgpIHtcbiAgICBsZXQgXzogYm9vbGVhbiA6PSAoMSA6IGk2NCkgPT0gMTtcbn1cblxuLy8gYXMgY29udmVyc2lvbiBzdGlsbCB3b3JrcyBhbG9uZ3NpZGUgYXNjcmlwdGlvblxubGV0IGY6IGY2NCA6PSAxIGFzIGY2NDtcbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2J1aWx0aW5zL3N0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIiwibmFtZSI6InN0YWdlOF8wNF90eXBlX2FzY3JpcHRpb24ubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Generics

> **Availability:** Built-in generic types (`Perhaps<T>`, `Result<T, E>`, `T[]`) since v0.1.0. User-defined generic functions and types since v0.3.0.

Types and functions can be parameterized with `<T>` syntax.

```metel
struct Stack<T> {
    items: T[],
}

fun first<T>(arr: T[]) -> Perhaps<T> {
    if (arr.len() == 0) {
        return None;
    }
    return Some { value = arr[0] };
}

fun main() -> i64 {
    let stack := Stack { items = [1, 2, 3] };
    match (first(stack.items)) {
        Some { value } => value,
        None => 0,
    }
}
```

### Row bounds

> **Availability:** Since v0.12.0.

A bound written as a row accepts any type carrying at least the listed fields:

```metel
fun squared_magnitude<record T: { x: f64, y: f64, .. }>(p: T) -> f64 {
    p.x * p.x + p.y * p.y
}
```

**The trailing `..` is load-bearing.** It stands for "and a rest I am not naming," and its
presence is what makes the bound *open*:

```metel
fun g<record T: { x: f64 }>(p: T)        // closed: T's row is exactly `x`
fun h<record T: { x: f64, .. }>(p: T)    // open:  T has at least `x`
```

A record pattern's own trailing `..` reads the bound's listed fields the same way
[field access](#spec.types.generics.row-bounds.legality-6) does, and — unlike field access
— can discard the rest of an open bound's unlisted fields rather than being unable to name
them at all:

```metel
fun describe<record T: { x: f64, .. }>(p: T) -> String {
    match (p) {
        { x, .. } => "x is ${x}, plus whatever else the caller passed",
    }
}
```

**The `..` is required to match an open bound at all** — its full field set isn't known
here, so a pattern that doesn't end in `..` can never be exhaustive:

```metel
fun bad<record T: { x: f64, .. }>(p: T) -> f64 {
    match (p) {
        { x } => x,   // error: open bound's field set isn't known here; add `..`
    }
}
```

A closed bound's fields *are* fully known, so `..` there is optional sugar rather than a
requirement — a pattern matching a closed bound must still name every field the bound
lists unless it uses `..`:

```metel
fun get_x<record T: { x: f64, y: f64 }>(p: T) -> f64 {
    match (p) {
        { x, y } => x,       // OK: every field of the closed bound is named
        // { x } => x,       // error: `y` isn't named and there's no `..`
    }
}
```

Naming a field the bound doesn't list is still rejected, `..` or not — the pattern's rest
form discards *unnamed* fields, not fields the bound never promised are there:

```metel
fun bad2<record T: { x: f64, .. }>(p: T) -> f64 {
    match (p) {
        { x, z, .. } => x,   // error: no field `z` on the bound
    }
}
```

**A field may omit its type** to constrain the label only — `{ x }` means "carries an `x`,
whatever its type":

```metel
fun f<record T: { x, .. }>(p: T)          // has an `x` of some type
fun g<record T: { x, y: f64, .. }>(p: T)  // any-typed `x`, `f64` `y`
```

Negation reuses the `!` that bounds already accept, and is the **complement** of the positive
bound — just as `!Copy` means "does not implement `Copy`". It takes no `..`, since absence
has no rest to quantify over:

```metel
fun send<record T: !{ token }>(t: T) -> i64 { … }        // carries no `token` at all
fun tag<record T: !{ id: String }>(t: T) -> i64 { … }    // no `String`-typed `id`
```

Note the second form is satisfied by a record whose `id` is an `i64` — it does not have a
`String` `id`. Write `!{ id }` for "no `id` of any type".

**A row bound is satisfied by a record, not by a nominal struct.** The `record` marker on the
type parameter says so at the declaration; a bare `<T: { … }>` is an error.

The marker may be written at the parameter or in a `where` clause — the two are equivalent,
and a parameter is record-kinded if either one carries it:

```metel
fun f<record T: { x: f64, .. }>(p: T) -> f64
fun g<T>(p: T) -> f64 where record T: { x: f64, .. }
```

**The row bound is optional.** `<record T>` on its own means "any record, whatever its
fields" — the only way to write that, since a bound of `{ .. }` alone is not accepted:

```metel
fun labels<record T>(x: T) -> Symbol[]   // any record; no constraint on its fields
```

```metel
squared_magnitude({ x = 3.0, y = 4.0 });   // a record — satisfies the bound
squared_magnitude(some_point);             // a struct — does not
```

Nominal structs do not satisfy row bounds. **Named records are planned, not implemented**;
they would provide a nominal record kind. See `public/rfcs/2-accepted/rfc-0120-named-records.md`
(RFC-0120: Named Records) — a plain path mention rather than a link while `rfcs/` is
excluded from the website (see metel-website's `docusaurus.config.ts`), so this doesn't
become a broken link once RFCs sync through.

### Why row capability is opt-in

A nominal type's API is what it **declares**. An anonymous record's API is what it
**contains**.

Once a type satisfies row bounds, its field names and types are part of its public interface,
whether the author intended that or not. Renaming a field breaks every caller who wrote a
bound mentioning it; adding one can make the type accidentally satisfy a bound its author
never heard of. On a `struct`, a field rename is an internal change.

That is why structural capability is opt-in rather than automatic:

| | encapsulation | structural flexibility |
|---|---|---|
| `struct` | layout is private; the API is what you declare | none |

Most types want the first. A value whose *shape* is genuinely the contract — a coordinate
pair or a configuration fragment — can use an anonymous record.

### What satisfies which bound

Both bound kinds are opted into; they differ only in *granularity*. An **aspect** bound is
opted into per aspect, by writing an implementation. A **row** bound is opted into per type,
by choosing the `record` kind. Nothing is implicit in either direction.

> **Available now (RFC-0137, metel-core#857): a `struct`'s "no" below is a visibility
> gate, not the absence of a row.** Every struct is represented internally as
> `(brand, row)` (see [Ownership — Narrowing](ownership.md#narrowing)); what the table's
> "no" states is that a plain struct's row is never *visible* to row-bound satisfaction,
> regardless of narrowing or projection — including at full width, where the row's
> content is identical to a same-shaped record's — the same observable outcome as
> before, now restated on the branded-row mechanism itself rather than merely predicted
> of it.

| | non-local aspect (`Display`) | local aspect | row bound |
|---|---|---|---|
| `struct` | yes, with an impl | yes, with an impl | **no** |
| `enum` | yes, with an impl | yes, with an impl | **no** — sums, not products |
| anonymous record | **no** — see below | yes, with an impl | yes |

An anonymous record has no owning module, so the orphan rule permits an implementation only
for an aspect local to the implementing module. Every standard-library aspect is non-local,
which means no anonymous record is `Display` and `println("${r}")` does not work on one.
Auto-derived aspects are unaffected — `Send` and `Sync` are computed from field composition
rather than declared.

### Implementing an aspect for a record

Three forms, with different rules:

```metel
extend { x: f64, y: f64 }: MyAspect { … }                    // one concrete row
extend<row R: { x: f64, .. }> { ..R }: MyAspect { … }         // every row of a given shape
extend<row R> { ..R }: MyAspect { … }                         // every row
```

**None of the three are available in v0.12.0** — this contradicted the "Not available in
v0.12.0" callout above until corrected here; confirmed directly, `extend { x: f64, y: f64 }:
MyAspect { … }` still fails with the same "cannot `extend` an anonymous record type" rejection
tuples and records both hit. The first form is the one this design intends to land first —
exactly one structural type, permitted once the aspect is local — but it is not implemented
yet, unlike the equivalent one-concrete-target form for arrays (`extend<T> T[]: Aspect`,
already supported). The second and third additionally require row variables, which don't
exist at all yet. The second also needs overlap checking between row bounds — two
shape-conditional implementations can be *incomparable* rather than one being more specific,
so they must be disjoint. The third additionally needs a way to require an aspect of every
field in the row, which does not yet exist either.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.generics.row-bounds.legality-1}

A row bound requires `record` on its type parameter, either at the parameter declaration
or in a `where` constraint; `record` without a row bound is also a legal any-record bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjkzX3Jvd19ib3VuZHMubXRsIiwic291cmNlIjoiZnVuIGNsb3NlZF9vazxyZWNvcmQgVDogeyB4OiBpNjQsIHk6IGk2NCB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDEgfVxuXG5mdW4gb3Blbl9vazxyZWNvcmQgVDogeyB4OiBpNjQsIC4uIH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgMiB9XG5cbmZ1biBsYWJlbF9vbmx5X29rPHJlY29yZCBUOiB7IHRva2VuIH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgMyB9XG5cbmZ1biBtaXhlZF9vazxyZWNvcmQgVDogeyB0b2tlbiwgeTogaTY0LCAuLiB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDQgfVxuXG5mdW4gd2hlcmVfbWFya2VyX29rPFQ+KF92YWx1ZTogVCkgLT4gaTY0XG53aGVyZSByZWNvcmQgVDogeyB4OiBpNjQsIC4uIH0ge1xuICAgIDVcbn1cblxuZnVuIGFueV9yZWNvcmQ8cmVjb3JkIFQ+KF92YWx1ZTogVCkgLT4gaTY0IHsgNiB9XG5cbmZ1biBuZWdfdHlwZWRfb2s8cmVjb3JkIFQ6ICF7IHg6IGY2NCB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDcgfVxuXG5mdW4gbmVnX2xhYmVsX29rPHJlY29yZCBUOiAheyB6IH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgOCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChjbG9zZWRfb2soeyB4ID0gMSwgeSA9IDIgfSkgPT0gMSk7XG4gICAgYXNzZXJ0KG9wZW5fb2soeyB4ID0gMSwgeSA9IDIsIGV4dHJhID0gMyB9KSA9PSAyKTtcbiAgICBhc3NlcnQobGFiZWxfb25seV9vayh7IHRva2VuID0gXCJpZFwiIH0pID09IDMpO1xuICAgIGFzc2VydChtaXhlZF9vayh7IHRva2VuID0gdHJ1ZSwgeSA9IDksIGV4dHJhID0gMSB9KSA9PSA0KTtcbiAgICBhc3NlcnQod2hlcmVfbWFya2VyX29rKHsgeCA9IDEsIGV4dHJhID0gMiB9KSA9PSA1KTtcbiAgICBhc3NlcnQoYW55X3JlY29yZCh7IGFueXRoaW5nID0gMSB9KSA9PSA2KTtcbiAgICBhc3NlcnQobmVnX3R5cGVkX29rKHsgeCA9IDEgfSkgPT0gNyk7XG4gICAgYXNzZXJ0KG5lZ19sYWJlbF9vayh7IHggPSAxIH0pID09IDgpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy85M19yb3dfYm91bmRzLm10bCIsIm5hbWUiOiI5M19yb3dfYm91bmRzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExOCBcdTAwYTcxOiB0aGUgYHJlY29yZGAgbWFya2VyIGFuZCBhIHJvdyBib3VuZCBtYXkgYmUgd3JpdHRlbiBhdCB0aGVcbi8vIGdlbmVyaWMgcGFyYW1ldGVyJ3Mgb3duIGRlY2xhcmF0aW9uIEFORCBzZXBhcmF0ZWx5IGluIGEgYHdoZXJlYCBjbGF1c2UgZm9yXG4vLyB0aGUgc2FtZSBwYXJhbWV0ZXI7IHRoZSB0d28gcG9zaXRpb25zIGNvbXBvc2UuIEFsc28gZXhlcmNpc2VzIFx1MDBhNzJhIChhIGJvdW5kXG4vLyBmaWVsZCwgYHhgLCBtYXkgb21pdCBpdHMgdHlwZSkgYW5kIFx1MDBhNzIgKGEgbmVnYXRpdmUgd2hlcmUtY2xhdXNlIGJvdW5kIGlzXG4vLyBlbmZvcmNlZCwgbm90IGp1c3QgcGFyc2VkKS5cbmZ1biBmPHJlY29yZCBUOiB7IHgsIHk6IGk2NCwgLi4gfT4odmFsdWU6IFQpIC0+IGk2NFxud2hlcmUgcmVjb3JkIFQ6ICF7IHogfSB7XG4gICAgdmFsdWUueVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgb2sgOj0geyB4ID0gXCJoaVwiLCB5ID0gNSB9O1xuICAgIGxldCByZXN1bHQgOj0gZihvayk7XG4gICAgYXNzZXJ0KHJlc3VsdCA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3JlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJuYW1lIjoicmVjb3JkX2JvdW5kX2lubGluZV9hbmRfd2hlcmVfY2xhdXNlX2NvbWJpbmVkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-2}

A negative row bound is satisfied only when none of its named fields match; it accepts no
trailing `..` and a negative bound in a `where` clause is enforced like an inline one.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjoiMjAiLCJjb250YWlucyI6Im5lZ2F0aXZlIHJvdyBib3VuZCBgIXsgeiB9YCIsImxpbmUiOiIxMiIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im5lZ19yb3dfYm91bmRfd2hlcmVfY2xhdXNlX3JlamVjdHNfZm9yYmlkZGVuX2ZpZWxkLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMTE4IFx1MDBhNzI6IGEgbmVnYXRpdmUgcm93IGJvdW5kIHdyaXR0ZW4gaW4gYSBgd2hlcmVgIGNsYXVzZSBpcyBlbmZvcmNlZFxuLy8gdGhlIHNhbWUgYXMgb25lIHdyaXR0ZW4gaW5saW5lIC0tIGEgcmVjb3JkIGNhcnJ5aW5nIHRoZSBmb3JiaWRkZW4gbGFiZWwgaXNcbi8vIHJlamVjdGVkLCBub3Qgc2lsZW50bHkgYWNjZXB0ZWQgYmVjYXVzZSB0aGUgYm91bmQgbGl2ZXMgaW4gYSBzZXBhcmF0ZVxuLy8gY2xhdXNlIGZyb20gdGhlIHBhcmFtZXRlcidzIG93biBkZWNsYXJhdGlvbi5cbmZ1biBmPHJlY29yZCBUOiB7IHgsIHk6IGk2NCwgLi4gfT4odmFsdWU6IFQpIC0+IGk2NFxud2hlcmUgcmVjb3JkIFQ6ICF7IHogfSB7XG4gICAgdmFsdWUueVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYmFkIDo9IHsgeCA9IDEsIHkgPSAyLCB6ID0gMyB9O1xuICAgIGxldCByZXN1bHQgOj0gZihiYWQpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvZ2VuZXJpY3MvbmVnX3Jvd19ib3VuZF93aGVyZV9jbGF1c2VfcmVqZWN0c19mb3JiaWRkZW5fZmllbGQubXRsIiwibmFtZSI6Im5lZ19yb3dfYm91bmRfd2hlcmVfY2xhdXNlX3JlamVjdHNfZm9yYmlkZGVuX2ZpZWxkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6Im5lZ2F0aXZlIHJvdyBib3VuZCB0YWtlcyBubyIsImxpbmUiOm51bGwsInN0YXR1cyI6InBhcnNlX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnYXRpdmVfcm93X2JvdW5kX3JlamVjdHNfb3Blbi5tdGwiLCJzb3VyY2UiOiIvLyBOZWdhdGl2ZSAoUkZDLTAxMTggXHUwMGE3Mik6IGEgbmVnYXRpdmUgcm93IGJvdW5kIG5hbWVzIGxhYmVscyB0aGF0IG11c3QgYmUgYWJzZW50LCBzbyB0aGVyZVxuLy8gaXMgbm8gcmVzdCB0byBxdWFudGlmeSBvdmVyIGFuZCBgLi5gIGlzIG1lYW5pbmdsZXNzLiBSZWplY3RlZCByYXRoZXIgdGhhbiBpZ25vcmVkLlxuZnVuIGY8cmVjb3JkIFQ6ICF7IHgsIC4uIH0+KHY6IFQpIC0+IGk2NCB7IDEgfVxuXG5mdW4gbWFpbigpIHsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL25lZ2F0aXZlX3Jvd19ib3VuZF9yZWplY3RzX29wZW4ubXRsIiwibmFtZSI6Im5lZ2F0aXZlX3Jvd19ib3VuZF9yZWplY3RzX29wZW4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExOCBcdTAwYTcxOiB0aGUgYHJlY29yZGAgbWFya2VyIGFuZCBhIHJvdyBib3VuZCBtYXkgYmUgd3JpdHRlbiBhdCB0aGVcbi8vIGdlbmVyaWMgcGFyYW1ldGVyJ3Mgb3duIGRlY2xhcmF0aW9uIEFORCBzZXBhcmF0ZWx5IGluIGEgYHdoZXJlYCBjbGF1c2UgZm9yXG4vLyB0aGUgc2FtZSBwYXJhbWV0ZXI7IHRoZSB0d28gcG9zaXRpb25zIGNvbXBvc2UuIEFsc28gZXhlcmNpc2VzIFx1MDBhNzJhIChhIGJvdW5kXG4vLyBmaWVsZCwgYHhgLCBtYXkgb21pdCBpdHMgdHlwZSkgYW5kIFx1MDBhNzIgKGEgbmVnYXRpdmUgd2hlcmUtY2xhdXNlIGJvdW5kIGlzXG4vLyBlbmZvcmNlZCwgbm90IGp1c3QgcGFyc2VkKS5cbmZ1biBmPHJlY29yZCBUOiB7IHgsIHk6IGk2NCwgLi4gfT4odmFsdWU6IFQpIC0+IGk2NFxud2hlcmUgcmVjb3JkIFQ6ICF7IHogfSB7XG4gICAgdmFsdWUueVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgb2sgOj0geyB4ID0gXCJoaVwiLCB5ID0gNSB9O1xuICAgIGxldCByZXN1bHQgOj0gZihvayk7XG4gICAgYXNzZXJ0KHJlc3VsdCA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3JlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJuYW1lIjoicmVjb3JkX2JvdW5kX2lubGluZV9hbmRfd2hlcmVfY2xhdXNlX2NvbWJpbmVkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-3}

A field in a row bound may omit its type, constraining the field label while accepting any
field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjkzX3Jvd19ib3VuZHMubXRsIiwic291cmNlIjoiZnVuIGNsb3NlZF9vazxyZWNvcmQgVDogeyB4OiBpNjQsIHk6IGk2NCB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDEgfVxuXG5mdW4gb3Blbl9vazxyZWNvcmQgVDogeyB4OiBpNjQsIC4uIH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgMiB9XG5cbmZ1biBsYWJlbF9vbmx5X29rPHJlY29yZCBUOiB7IHRva2VuIH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgMyB9XG5cbmZ1biBtaXhlZF9vazxyZWNvcmQgVDogeyB0b2tlbiwgeTogaTY0LCAuLiB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDQgfVxuXG5mdW4gd2hlcmVfbWFya2VyX29rPFQ+KF92YWx1ZTogVCkgLT4gaTY0XG53aGVyZSByZWNvcmQgVDogeyB4OiBpNjQsIC4uIH0ge1xuICAgIDVcbn1cblxuZnVuIGFueV9yZWNvcmQ8cmVjb3JkIFQ+KF92YWx1ZTogVCkgLT4gaTY0IHsgNiB9XG5cbmZ1biBuZWdfdHlwZWRfb2s8cmVjb3JkIFQ6ICF7IHg6IGY2NCB9PihfdmFsdWU6IFQpIC0+IGk2NCB7IDcgfVxuXG5mdW4gbmVnX2xhYmVsX29rPHJlY29yZCBUOiAheyB6IH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgOCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChjbG9zZWRfb2soeyB4ID0gMSwgeSA9IDIgfSkgPT0gMSk7XG4gICAgYXNzZXJ0KG9wZW5fb2soeyB4ID0gMSwgeSA9IDIsIGV4dHJhID0gMyB9KSA9PSAyKTtcbiAgICBhc3NlcnQobGFiZWxfb25seV9vayh7IHRva2VuID0gXCJpZFwiIH0pID09IDMpO1xuICAgIGFzc2VydChtaXhlZF9vayh7IHRva2VuID0gdHJ1ZSwgeSA9IDksIGV4dHJhID0gMSB9KSA9PSA0KTtcbiAgICBhc3NlcnQod2hlcmVfbWFya2VyX29rKHsgeCA9IDEsIGV4dHJhID0gMiB9KSA9PSA1KTtcbiAgICBhc3NlcnQoYW55X3JlY29yZCh7IGFueXRoaW5nID0gMSB9KSA9PSA2KTtcbiAgICBhc3NlcnQobmVnX3R5cGVkX29rKHsgeCA9IDEgfSkgPT0gNyk7XG4gICAgYXNzZXJ0KG5lZ19sYWJlbF9vayh7IHggPSAxIH0pID09IDgpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy85M19yb3dfYm91bmRzLm10bCIsIm5hbWUiOiI5M19yb3dfYm91bmRzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InJlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExOCBcdTAwYTcxOiB0aGUgYHJlY29yZGAgbWFya2VyIGFuZCBhIHJvdyBib3VuZCBtYXkgYmUgd3JpdHRlbiBhdCB0aGVcbi8vIGdlbmVyaWMgcGFyYW1ldGVyJ3Mgb3duIGRlY2xhcmF0aW9uIEFORCBzZXBhcmF0ZWx5IGluIGEgYHdoZXJlYCBjbGF1c2UgZm9yXG4vLyB0aGUgc2FtZSBwYXJhbWV0ZXI7IHRoZSB0d28gcG9zaXRpb25zIGNvbXBvc2UuIEFsc28gZXhlcmNpc2VzIFx1MDBhNzJhIChhIGJvdW5kXG4vLyBmaWVsZCwgYHhgLCBtYXkgb21pdCBpdHMgdHlwZSkgYW5kIFx1MDBhNzIgKGEgbmVnYXRpdmUgd2hlcmUtY2xhdXNlIGJvdW5kIGlzXG4vLyBlbmZvcmNlZCwgbm90IGp1c3QgcGFyc2VkKS5cbmZ1biBmPHJlY29yZCBUOiB7IHgsIHk6IGk2NCwgLi4gfT4odmFsdWU6IFQpIC0+IGk2NFxud2hlcmUgcmVjb3JkIFQ6ICF7IHogfSB7XG4gICAgdmFsdWUueVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgb2sgOj0geyB4ID0gXCJoaVwiLCB5ID0gNSB9O1xuICAgIGxldCByZXN1bHQgOj0gZihvayk7XG4gICAgYXNzZXJ0KHJlc3VsdCA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3JlY29yZF9ib3VuZF9pbmxpbmVfYW5kX3doZXJlX2NsYXVzZV9jb21iaW5lZC5tdGwiLCJuYW1lIjoicmVjb3JkX2JvdW5kX2lubGluZV9hbmRfd2hlcmVfY2xhdXNlX2NvbWJpbmVkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-4}

Only a record satisfies a row bound; a nominal struct is rejected even when it has matching
fields.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6InN0cnVjdCBuZXZlciBzYXRpc2ZpZXMgYSByb3cgYm91bmQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZWdfNDRfZnVsbF93aWR0aF9wcm9qZWN0aW9uX3N0aWxsX3JlamVjdGVkX2J5X3Jvd19ib3VuZC5tdGwiLCJzb3VyY2UiOiIvLyBSZWdyZXNzaW9uIChtZXRlbC1jb3JlIzg1NywgUkZDLTAxMzcgc2xpY2UgMSdzIG93biBub3JtYWxpemF0aW9uIHJ1bGUsIGFuZFxuLy8gUkZDLTAxMzcgc2VjMydzIHdvcmtlZCBleGFtcGxlKTogYSBwcm9qZWN0aW9uIG5hbWluZyBldmVyeSBmaWVsZCBhIHN0cnVjdFxuLy8gZGVjbGFyZXMgbm9ybWFsaXplcyBiYWNrIHRvIHRoZSBwbGFpbiBzdHJ1Y3QgdHlwZSByYXRoZXIgdGhhbiBzdGF5aW5nIGFcbi8vIGRpc3RpbmN0IGJyYW5kZWQgcmVzaWR1YWwuIENvbmZpcm1zIHRoZSBub3JtYWxpemF0aW9uIGRvZXNuJ3QgYWNjaWRlbnRhbGx5XG4vLyBlYXJuIHJvdy1ib3VuZCBlbGlnaWJpbGl0eSAtLSBoLnsgZmQsIG5hbWUgfSwgZnVsbCB3aWR0aCwgaXMgcmVqZWN0ZWQgYnkgYSByb3dcbi8vIGJvdW5kIHRoZSBleGFjdCBzYW1lIHdheSBhIGJhcmUgYEhhbmRsZWAgdmFsdWUgYWxyZWFkeSBpcy5cblxuc3RydWN0IEhhbmRsZSB7IGZkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG5cbmZ1biB3YW50c19hX3JlY29yZDxyZWNvcmQgVDogeyBmZDogaTY0LCBuYW1lOiBTdHJpbmcsIC4uIH0+KHQ6IFQpIC0+IGk2NCB7IHQuZmQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgaCA6PSBIYW5kbGUgeyBmZCA9IDMsIG5hbWUgPSBcInhcIiB9O1xuICAgIGxldCBfIDo9IHdhbnRzX2FfcmVjb3JkKGgueyBmZCwgbmFtZSB9KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3N0cnVjdHMvbmVnXzQ0X2Z1bGxfd2lkdGhfcHJvamVjdGlvbl9zdGlsbF9yZWplY3RlZF9ieV9yb3dfYm91bmQubXRsIiwibmFtZSI6Im5lZ180NF9mdWxsX3dpZHRoX3Byb2plY3Rpb25fc3RpbGxfcmVqZWN0ZWRfYnlfcm93X2JvdW5kLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEyIiwiY29sIjpudWxsLCJjb250YWlucyI6InN0cnVjdCBuZXZlciBzYXRpc2ZpZXMgYSByb3cgYm91bmQiLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJzdGFnZTVfbmVnXzI2X3Jvd19ib3VuZF9zdHJ1Y3RfcmVqZWN0ZWQubXRsIiwic291cmNlIjoic3RydWN0IFBvaW50IHtcbiAgICB4OiBpNjQsXG59XG5cbmZ1biBuZWVkX3JlY29yZDxyZWNvcmQgVDogeyB4OiBpNjQsIC4uIH0+KF92YWx1ZTogVCkgLT4gaTY0IHsgMCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBfIDo9IG5lZWRfcmVjb3JkKFBvaW50IHsgeCA9IDEgfSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL3N0YWdlNV9uZWdfMjZfcm93X2JvdW5kX3N0cnVjdF9yZWplY3RlZC5tdGwiLCJuYW1lIjoic3RhZ2U1X25lZ18yNl9yb3dfYm91bmRfc3RydWN0X3JlamVjdGVkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-5}

Brace syntax after a parameter or `let` annotation denotes an exact record type, while the
same syntax in a generic parameter or `where` constraint denotes a row bound.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0118](../../rfcs/4-implemented/rfc-0118-row-bounds.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk1X3JlY29yZF90eXBlX3ZzX3Jvd19ib3VuZF9ieV9wb3NpdGlvbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDExOCBcdTAwYTc0OiB0aGUgc2FtZSBgeyAuLi4gfWAgYnJhY2Ugc3ludGF4IG1lYW5zIGFuIFJGQy0wMTE2IGNsb3NlZCByZWNvcmQgdHlwZVxuLy8gYWZ0ZXIgYDpgIGluIGEgcGFyYW0vbGV0IGFubm90YXRpb24sIGFuZCBhIHJvdyBib3VuZCBhZnRlciBgOmAgaW4gYSBnZW5lcmljX3BhcmFtIG9yXG4vLyB3aGVyZV9jb25zdHJhaW50IC0tIGRpc3Rpbmd1aXNoZWQgYnkgcG9zaXRpb24gYWxvbmUsIGJvdGggaW4gb25lIHByb2dyYW0uXG5cbmZ1biB0YWtlc19yZWNvcmQocDogeyB4OiBpNjQsIHk6IGk2NCB9KSAtPiBpNjQge1xuICAgIHAueCArIHAueVxufVxuXG5mdW4gdGFrZXNfcm93X2JvdW5kPHJlY29yZCBUOiB7IHg6IGk2NCwgLi4gfT4odjogVCkgLT4gaTY0IHtcbiAgICB2Lnhcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHIgOj0geyB4ID0gMSwgeSA9IDIgfTtcbiAgICBhc3NlcnQodGFrZXNfcmVjb3JkKHIpID09IDMpO1xuXG4gICAgbGV0IHdpZGVyIDo9IHsgeCA9IDUsIHkgPSA2LCB6ID0gNyB9O1xuICAgIGFzc2VydCh0YWtlc19yb3dfYm91bmQod2lkZXIpID09IDUpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy85NV9yZWNvcmRfdHlwZV92c19yb3dfYm91bmRfYnlfcG9zaXRpb24ubXRsIiwibmFtZSI6Ijk1X3JlY29yZF90eXBlX3ZzX3Jvd19ib3VuZF9ieV9wb3NpdGlvbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-6}

A field a row bound lists is accessible via field access (`p.x`) from inside the function
body; a field the bound doesn't list is not, even when a caller's concrete argument
happens to carry it.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk0X3Jvd19ib3VuZF9maWVsZF9hY2Nlc3MubXRsIiwic291cmNlIjoiLy8gIzY0NTogZG90LWFjY2VzcyB0byBhIGZpZWxkIGV4cGxpY2l0bHkgbmFtZWQgaW4gYSByb3cgYm91bmQsIHRocm91Z2ggYW4gYWJzdHJhY3QsXG4vLyByb3ctYm91bmRlZCBnZW5lcmljIHR5cGUgcGFyYW1ldGVyIFx1MjAxNCBib3RoIGNsb3NlZCBhbmQgb3BlbiBib3VuZHMsIHR5cGVkIGFuZCB1bnR5cGVkXG4vLyBmaWVsZCBmb3JtcywgYW5kIHdyaXRpbmcgdGhyb3VnaCBhIG11dGFibGUgcmVmZXJlbmNlLlxuXG5mdW4gZ2V0X3g8cmVjb3JkIFQ6IHsgeDogZjY0IH0+KHA6IFQpIC0+IGY2NCB7XG4gICAgcC54XG59XG5cbmZ1biBzcXVhcmVkX21hZ25pdHVkZTxyZWNvcmQgVDogeyB4OiBmNjQsIHk6IGY2NCwgLi4gfT4ocDogVCkgLT4gZjY0IHtcbiAgICBwLnggKiBwLnggKyBwLnkgKiBwLnlcbn1cblxuZnVuIGdldF9uYW1lPHJlY29yZCBUOiB7IG5hbWUsIC4uIH0+KHA6IFQpIC0+IGk2NCB7XG4gICAgcC5uYW1lXG59XG5cbmZ1biBidW1wPHJlY29yZCBUOiB7IGNvdW50OiBpNjQsIC4uIH0+KHA6ICZ2YXIgVCkge1xuICAgIHAuY291bnQgKz0gMTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGdldF94KHsgeCA9IDMuMCB9KSA9PSAzLjApO1xuICAgIGFzc2VydChzcXVhcmVkX21hZ25pdHVkZSh7IHggPSAzLjAsIHkgPSA0LjAgfSkgPT0gMjUuMCk7XG4gICAgYXNzZXJ0KHNxdWFyZWRfbWFnbml0dWRlKHsgeCA9IDMuMCwgeSA9IDQuMCwgZXh0cmEgPSBcImlnbm9yZWRcIiB9KSA9PSAyNS4wKTtcbiAgICBhc3NlcnQoZ2V0X25hbWUoeyBuYW1lID0gNDIsIG90aGVyID0gXCJoaVwiIH0pID09IDQyKTtcblxuICAgIHZhciByIDo9IHsgY291bnQgPSAxIH07XG4gICAgYnVtcCgmdmFyIHIpO1xuICAgIGFzc2VydChyLmNvdW50ID09IDIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy85NF9yb3dfYm91bmRfZmllbGRfYWNjZXNzLm10bCIsIm5hbWUiOiI5NF9yb3dfYm91bmRfZmllbGRfYWNjZXNzLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.generics.row-bounds.legality-7}

A record pattern's trailing `..` binds only the fields it names against a row-bounded
type parameter and discards the rest, the same as it does against a named struct. It is
required to match an open bound at all, since the bound's full field set isn't known;
for a closed bound it is optional, but the pattern must otherwise name every field the
bound lists. Naming a field the bound doesn't list is rejected regardless of `..`.

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (4)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Ijk2X3Jvd19ib3VuZF9yZXN0X3BhdHRlcm4ubXRsIiwic291cmNlIjoiLy8gIzY0NjogYSByZWNvcmQgcGF0dGVybidzIHRyYWlsaW5nIGAuLmAgcmVhZHMgYSByb3ctYm91bmRlZCB0eXBlIHBhcmFtZXRlcidzIGxpc3RlZFxuLy8gZmllbGRzIGFuZCBkaXNjYXJkcyB0aGUgcmVzdCAtLSByZXF1aXJlZCBmb3IgYW4gb3BlbiBib3VuZCAod2hvc2UgZnVsbCBmaWVsZCBzZXQgaXNuJ3Rcbi8vIGtub3duIGhlcmUpLCBvcHRpb25hbCBzdWdhciBmb3IgYSBjbG9zZWQgYm91bmQgKHdob3NlIGZpZWxkcyBhcmUgYWxyZWFkeSBleGhhdXN0aXZlbHlcbi8vIGxpc3RlZCBieSB0aGUgYm91bmQgaXRzZWxmKS5cblxuZnVuIGRlc2NyaWJlPHJlY29yZCBUOiB7IHg6IGY2NCwgLi4gfT4ocDogVCkgLT4gZjY0IHtcbiAgICBtYXRjaCAocCkge1xuICAgICAgICB7IHgsIC4uIH0gPT4geCxcbiAgICB9XG59XG5cbmZ1biBnZXRfeF9jbG9zZWQ8cmVjb3JkIFQ6IHsgeDogZjY0IH0+KHA6IFQpIC0+IGY2NCB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgeyB4LCAuLiB9ID0+IHgsXG4gICAgfVxufVxuXG5mdW4gZ2V0X3hfY2xvc2VkX25vX3Jlc3Q8cmVjb3JkIFQ6IHsgeDogZjY0LCB5OiBmNjQgfT4ocDogVCkgLT4gZjY0IHtcbiAgICBtYXRjaCAocCkge1xuICAgICAgICB7IHgsIHkgfSA9PiB4ICsgeSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChkZXNjcmliZSh7IHggPSAzLjAgfSkgPT0gMy4wKTtcbiAgICBhc3NlcnQoZGVzY3JpYmUoeyB4ID0gMy4wLCB5ID0gNC4wLCBsYWJlbCA9IFwiaWdub3JlZFwiIH0pID09IDMuMCk7XG4gICAgYXNzZXJ0KGdldF94X2Nsb3NlZCh7IHggPSA1LjAgfSkgPT0gNS4wKTtcbiAgICBhc3NlcnQoZ2V0X3hfY2xvc2VkX25vX3Jlc3QoeyB4ID0gMS4wLCB5ID0gMi4wIH0pID09IDMuMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzk2X3Jvd19ib3VuZF9yZXN0X3BhdHRlcm4ubXRsIiwibmFtZSI6Ijk2X3Jvd19ib3VuZF9yZXN0X3BhdHRlcm4ubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyb3dfYm91bmRfcGF0dGVybl9taXNzaW5nX2ZpZWxkX3dpdGhvdXRfcmVzdF9pc190MDAwMS5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ2OiBhIGNsb3NlZCByb3cgYm91bmQncyBmaWVsZHMgYXJlIGZ1bGx5IGtub3duLCBidXQgYSByZWNvcmQgcGF0dGVybiB3aXRob3V0IGAuLmBcbi8vIG11c3Qgc3RpbGwgbmFtZSBldmVyeSBvbmUgb2YgdGhlbSAtLSB0aGUgc2FtZSBjb21wbGV0ZW5lc3MgcnVsZSBhbiBhbm9ueW1vdXMgcmVjb3JkIG9yXG4vLyBuYW1lZCBzdHJ1Y3QgcGF0dGVybiBhbHJlYWR5IGVuZm9yY2VzLlxuZnVuIGdldF94PHJlY29yZCBUOiB7IHg6IGY2NCwgeTogZjY0IH0+KHA6IFQpIC0+IGY2NCB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgeyB4IH0gPT4geCxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIHByaW50bG4oZ2V0X3goeyB4ID0gMS4wLCB5ID0gMi4wIH0pKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3Jvd19ib3VuZF9wYXR0ZXJuX21pc3NpbmdfZmllbGRfd2l0aG91dF9yZXN0X2lzX3QwMDAxLm10bCIsIm5hbWUiOiJyb3dfYm91bmRfcGF0dGVybl9taXNzaW5nX2ZpZWxkX3dpdGhvdXRfcmVzdF9pc190MDAwMS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyb3dfYm91bmRfcGF0dGVybl9uYW1lc19maWVsZF9vdXRzaWRlX2JvdW5kX2lzX3QwMDAzLm10bCIsInNvdXJjZSI6Ii8vICM2NDY6IGAuLmAgZGlzY2FyZHMgZmllbGRzIHRoZSBwYXR0ZXJuIGRvZXNuJ3QgbmFtZSAtLSBpdCBkb2Vzbid0IGxldCB0aGUgcGF0dGVybiBuYW1lXG4vLyBhIGZpZWxkIHRoZSBib3VuZCBuZXZlciBwcm9taXNlZCBpcyB0aGVyZSwgZXZlbiBvbmUgYSBwYXJ0aWN1bGFyIGNhbGxlciBoYXBwZW5zIHRvIHBhc3MuXG5mdW4gZGVzY3JpYmU8cmVjb3JkIFQ6IHsgeDogZjY0LCAuLiB9PihwOiBUKSAtPiBmNjQge1xuICAgIG1hdGNoIChwKSB7XG4gICAgICAgIHsgeCwgeiwgLi4gfSA9PiB4ICsgeixcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIHByaW50bG4oZGVzY3JpYmUoeyB4ID0gMS4wLCB6ID0gMi4wIH0pKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL2dlbmVyaWNzL3Jvd19ib3VuZF9wYXR0ZXJuX25hbWVzX2ZpZWxkX291dHNpZGVfYm91bmRfaXNfdDAwMDMubXRsIiwibmFtZSI6InJvd19ib3VuZF9wYXR0ZXJuX25hbWVzX2ZpZWxkX291dHNpZGVfYm91bmRfaXNfdDAwMDMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyb3dfYm91bmRfcGF0dGVybl93aXRob3V0X3Jlc3Rfb25fb3Blbl9ib3VuZF9pc190MDAwMS5tdGwiLCJzb3VyY2UiOiIvLyAjNjQ2OiBhbiBvcGVuIHJvdyBib3VuZCdzIGZ1bGwgZmllbGQgc2V0IGlzbid0IGtub3duIGhlcmUsIHNvIGEgcmVjb3JkIHBhdHRlcm4gdGhhdFxuLy8gZG9lc24ndCBlbmQgaW4gYC4uYCBjYW4gbmV2ZXIgYmUgZXhoYXVzdGl2ZSBhZ2FpbnN0IGl0LlxuZnVuIGRlc2NyaWJlPHJlY29yZCBUOiB7IHg6IGY2NCwgLi4gfT4ocDogVCkgLT4gZjY0IHtcbiAgICBtYXRjaCAocCkge1xuICAgICAgICB7IHggfSA9PiB4LFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgcHJpbnRsbihkZXNjcmliZSh7IHggPSAxLjAgfSkpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvZ2VuZXJpY3Mvcm93X2JvdW5kX3BhdHRlcm5fd2l0aG91dF9yZXN0X29uX29wZW5fYm91bmRfaXNfdDAwMDEubXRsIiwibmFtZSI6InJvd19ib3VuZF9wYXR0ZXJuX3dpdGhvdXRfcmVzdF9vbl9vcGVuX2JvdW5kX2lzX3QwMDAxLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Never Type

> **Availability:** Since v0.10.0.

`!` (Never) is the **uninhabited bottom type** — no value of type `!` can ever be
constructed. A `loop` with no reachable `break` has type `!`:

```metel
fun main() -> i64 {
    let result: i64 := loop { break 42; };
    return result;
}
```

`return <expr>`, `panic(<message>)`, `loop { }` with no reachable `break`, and `break`/`continue` used as value expressions in loop context all have type `!`. If any sub-expression has type `!`, that sub-expression diverges before the outer expression can produce a value, so the outer expression's type is unconstrained and any type is accepted in that position.

### Subtyping and coercion

`!` is a subtype of every type — `! <: T` for all `T` — so an expression of type `!` coerces implicitly, with no cast, to any context expecting `T`. This is what makes the rule above sound: code after a diverging expression is unreachable, but still typechecks against whatever its context requires.

### Match exhaustiveness

A `match` whose scrutinee has type `!` needs no arms — an empty match is vacuously exhaustive, since no value of type `!` can ever reach it:

```metel
fun unreachable_code(x: !) -> i64 {
    match x { }   // exhaustive — no arms needed
}
```

More generally, an enum variant whose payload type is `!` is uninhabited — no value of that variant can ever be constructed — and a `match` may omit the arm for an uninhabited variant while remaining exhaustive:

```metel
enum Foo {
    A { x: i64 },
    B { y: ! },
}

fun handle(f: Foo) -> i64 {
    match (f) {
        Foo::A { x } => x,
        // Foo::B omitted — exhaustive; B is uninhabited
    }
}
```

### Inhabited-singleton coercion

If an enum has exactly one inhabited variant (every other variant's payload is `!`) and that variant has exactly one field, a value of the enum type coerces implicitly to the field's type — the compiler inserts the destructuring, no explicit `match` required:

```metel
enum Wrapper<T> {
    Present { value: T },
    Absent  { _: ! },
}

fun infallible() -> Wrapper<i64> { Wrapper::Present { value = 42 } }

fun main() -> i64 {
    let x: i64 := infallible();  // implicit coercion via the inhabited-singleton rule
    return x;
}
```

`Result<T, !>` satisfies this: `Ok { value: T }` is the one inhabited variant with one field, so a `Result<T, !>`-returning function's caller can use the result as a plain `T` with no `match`. `Perhaps<!>` does **not** satisfy it — `None` is inhabited but has zero fields — so `Perhaps<!>` never coerces implicitly to anything, though nothing prevents it from arising through generic instantiation.

### `!` as a return type

A function annotated `-> !` promises never to return; every control-flow path must end in a diverging expression, checked by the compiler:

```metel
fun abort(msg: String) -> ! {
    panic(msg);
}
```

A `-> !` function containing a reachable `return` is a type error.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.never-type.legality-1}

`!` is uninhabited: no terminating expression can construct a value of that type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogUkZDLTAwNzggXHUwMGE3My4yIC0tIGFuIGVudW0gdmFyaWFudCB3aG9zZSBwYXlsb2FkIGlzIGAhYCBpc1xuLy8gdW5pbmhhYml0ZWQsIHNvIGEgbWF0Y2ggbWF5IG9taXQgaXRzIGFybSBhbmQgc3RpbGwgYmUgZXhoYXVzdGl2ZS5cblxuZW51bSBGb28ge1xuICAgIEEgeyB4OiBpNjQgfSxcbiAgICBCIHsgeTogISB9LFxufVxuXG5mdW4gaGFuZGxlKGY6IEZvbykgLT4gaTY0IHtcbiAgICBtYXRjaCAoZikge1xuICAgICAgICBGb286OkEgeyB4IH0gPT4geCxcbiAgICAgICAgLy8gRm9vOjpCIG9taXR0ZWQgLS0gZXhoYXVzdGl2ZTsgQiBpcyB1bmluaGFiaXRlZC5cbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBoYW5kbGUoRm9vOjpBIHsgeCA9IDUgfSlcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL25ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJuYW1lIjoibmV2ZXJfMDFfdW5pbmhhYml0ZWRfdmFyaWFudF9leGhhdXN0aXZlLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-2}

`!` is a subtype of every type, and an expression of type `!` implicitly coerces to any
expected type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA0X3BhbmljX2NvZXJjZXMubXRsIiwic291cmNlIjoiLy8gUG9zaXRpdmU6IFJGQy0wMDc4IFx1MDBhNzEuMS9cdTAwYTcyIC0tIGBwYW5pYyhtc2cpYCBoYXMgdHlwZSBgIWAsIHdoaWNoIGNvZXJjZXNcbi8vIGltcGxpY2l0bHkgdG8gYW55IHR5cGUgd2hlcmV2ZXIgdGhlIHN1cnJvdW5kaW5nIGNvbnRleHQgaXMgb3RoZXJ3aXNlXG4vLyB1bmNvbnN0cmFpbmVkLlxuXG5mdW4gcGljayhjb25kOiBib29sZWFuKSAtPiBpNjQge1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIHBhbmljKFwibm9wZVwiKVxuICAgIH0gZWxzZSB7XG4gICAgICAgIDVcbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBwaWNrKGZhbHNlKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwiLCJuYW1lIjoibmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-3}

Code made unreachable by a diverging expression remains typechecked in its surrounding
type context.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCIsInNvdXJjZSI6Ii8vIFBvc2l0aXZlOiBSRkMtMDA3OCBcdTAwYTczLjIvXHUwMGE3NC4xIC0tIHdyaXRpbmcgdGhlIGFybSBmb3IgYW4gdW5pbmhhYml0ZWQgdmFyaWFudCBpc1xuLy8gYWxsb3dlZCAobWVyZWx5IHVucmVhY2hhYmxlLCBub3QgcmVqZWN0ZWQpOyB0aGUgY29tcGlsZXIgbWF5IHdhcm4gYnV0IG11c3Rcbi8vIG5vdCBlcnJvci5cblxuZnVuIHVzZV9yZXN1bHQocjogUmVzdWx0PGk2NCwgIT4pIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHIpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBwYW5pYyhcInVucmVhY2hhYmxlXCIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIHVzZV9yZXN1bHQoUmVzdWx0OjpPayB7IHZhbHVlID0gMyB9KVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDNfdW5yZWFjaGFibGVfYXJtX2FsbG93ZWQubXRsIiwibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.never-type.dynamics-1}

`return`, `panic`, a non-breaking `loop`, and value-position `break` or `continue`
diverge and have type `!`; an enclosing expression cannot produce a value after such a
subexpression diverges.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImJvb20iLCJsaW5lIjpudWxsLCJzdGF0dXMiOiJydW50aW1lX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibmVnX3BhbmljLm10bCIsInNvdXJjZSI6Ii8vIFJVTlRJTUVfRVJST1JbYm9vbV1cbi8vIFJGQy0wMDc4OiBwYW5pYyhtc2cpIGFsd2F5cyBwYW5pY3MgKFIwMDE1KSB3aXRoIHRoZSBnaXZlbiBtZXNzYWdlLlxuZnVuIG1haW4oKSB7XG4gICAgcGFuaWMoXCJib29tXCIpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvbmV2ZXIvbmVnX3BhbmljLm10bCIsIm5hbWUiOiJuZWdfcGFuaWMubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA0X3BhbmljX2NvZXJjZXMubXRsIiwic291cmNlIjoiLy8gUG9zaXRpdmU6IFJGQy0wMDc4IFx1MDBhNzEuMS9cdTAwYTcyIC0tIGBwYW5pYyhtc2cpYCBoYXMgdHlwZSBgIWAsIHdoaWNoIGNvZXJjZXNcbi8vIGltcGxpY2l0bHkgdG8gYW55IHR5cGUgd2hlcmV2ZXIgdGhlIHN1cnJvdW5kaW5nIGNvbnRleHQgaXMgb3RoZXJ3aXNlXG4vLyB1bmNvbnN0cmFpbmVkLlxuXG5mdW4gcGljayhjb25kOiBib29sZWFuKSAtPiBpNjQge1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIHBhbmljKFwibm9wZVwiKVxuICAgIH0gZWxzZSB7XG4gICAgICAgIDVcbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBwaWNrKGZhbHNlKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwiLCJuYW1lIjoibmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-4}

Match exhaustiveness excludes impossible scrutinee values and uninhabited variants.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogUkZDLTAwNzggXHUwMGE3My4yIC0tIGFuIGVudW0gdmFyaWFudCB3aG9zZSBwYXlsb2FkIGlzIGAhYCBpc1xuLy8gdW5pbmhhYml0ZWQsIHNvIGEgbWF0Y2ggbWF5IG9taXQgaXRzIGFybSBhbmQgc3RpbGwgYmUgZXhoYXVzdGl2ZS5cblxuZW51bSBGb28ge1xuICAgIEEgeyB4OiBpNjQgfSxcbiAgICBCIHsgeTogISB9LFxufVxuXG5mdW4gaGFuZGxlKGY6IEZvbykgLT4gaTY0IHtcbiAgICBtYXRjaCAoZikge1xuICAgICAgICBGb286OkEgeyB4IH0gPT4geCxcbiAgICAgICAgLy8gRm9vOjpCIG9taXR0ZWQgLS0gZXhoYXVzdGl2ZTsgQiBpcyB1bmluaGFiaXRlZC5cbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBoYW5kbGUoRm9vOjpBIHsgeCA9IDUgfSlcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL25ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJuYW1lIjoibmV2ZXJfMDFfdW5pbmhhYml0ZWRfdmFyaWFudF9leGhhdXN0aXZlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InVuaW5oYWJpdGVkX21hdGNoLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDc4IFx1MDBhNzMuMjogbWF0Y2hpbmcgb25seSB0aGUgaW5oYWJpdGVkIHZhcmlhbnQgb2YgYW4gZW51bSB3aXRoIGFcbi8vIGAhYC1wYXlsb2FkIHZhcmlhbnQsIGV4ZXJjaXNlZCBlbmQtdG8tZW5kIHRvIGNvbmZpcm0gZGlzcGF0Y2ggYW5kIHZhbHVlXG4vLyBleHRyYWN0aW9uIHdvcmsgY29ycmVjdGx5IGF0IHJ1bnRpbWUsIG5vdCBqdXN0IGF0IHR5cGVjaGVjayB0aW1lLlxuXG5lbnVtIEZvbyB7XG4gICAgQSB7IHg6IGk2NCB9LFxuICAgIEIgeyB5OiAhIH0sXG59XG5cbmZ1biBoYW5kbGUoZjogRm9vKSAtPiBpNjQge1xuICAgIG1hdGNoIChmKSB7XG4gICAgICAgIEZvbzo6QSB7IHggfSA9PiB4LFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGhhbmRsZShGb286OkEgeyB4ID0gNSB9KSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL25ldmVyL3VuaW5oYWJpdGVkX21hdGNoLm10bCIsIm5hbWUiOiJ1bmluaGFiaXRlZF9tYXRjaC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-5}

A match whose scrutinee has type `!` is exhaustive with no arms.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InVuaW5oYWJpdGVkX21hdGNoLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDc4IFx1MDBhNzMuMjogbWF0Y2hpbmcgb25seSB0aGUgaW5oYWJpdGVkIHZhcmlhbnQgb2YgYW4gZW51bSB3aXRoIGFcbi8vIGAhYC1wYXlsb2FkIHZhcmlhbnQsIGV4ZXJjaXNlZCBlbmQtdG8tZW5kIHRvIGNvbmZpcm0gZGlzcGF0Y2ggYW5kIHZhbHVlXG4vLyBleHRyYWN0aW9uIHdvcmsgY29ycmVjdGx5IGF0IHJ1bnRpbWUsIG5vdCBqdXN0IGF0IHR5cGVjaGVjayB0aW1lLlxuXG5lbnVtIEZvbyB7XG4gICAgQSB7IHg6IGk2NCB9LFxuICAgIEIgeyB5OiAhIH0sXG59XG5cbmZ1biBoYW5kbGUoZjogRm9vKSAtPiBpNjQge1xuICAgIG1hdGNoIChmKSB7XG4gICAgICAgIEZvbzo6QSB7IHggfSA9PiB4LFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGhhbmRsZShGb286OkEgeyB4ID0gNSB9KSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL25ldmVyL3VuaW5oYWJpdGVkX21hdGNoLm10bCIsIm5hbWUiOiJ1bmluaGFiaXRlZF9tYXRjaC5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-6}

An enum variant containing a `!` payload is uninhabited; its match arm may be omitted or,
if written, is unreachable but not rejected.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogUkZDLTAwNzggXHUwMGE3My4yIC0tIGFuIGVudW0gdmFyaWFudCB3aG9zZSBwYXlsb2FkIGlzIGAhYCBpc1xuLy8gdW5pbmhhYml0ZWQsIHNvIGEgbWF0Y2ggbWF5IG9taXQgaXRzIGFybSBhbmQgc3RpbGwgYmUgZXhoYXVzdGl2ZS5cblxuZW51bSBGb28ge1xuICAgIEEgeyB4OiBpNjQgfSxcbiAgICBCIHsgeTogISB9LFxufVxuXG5mdW4gaGFuZGxlKGY6IEZvbykgLT4gaTY0IHtcbiAgICBtYXRjaCAoZikge1xuICAgICAgICBGb286OkEgeyB4IH0gPT4geCxcbiAgICAgICAgLy8gRm9vOjpCIG9taXR0ZWQgLS0gZXhoYXVzdGl2ZTsgQiBpcyB1bmluaGFiaXRlZC5cbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBoYW5kbGUoRm9vOjpBIHsgeCA9IDUgfSlcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL25ldmVyXzAxX3VuaW5oYWJpdGVkX3ZhcmlhbnRfZXhoYXVzdGl2ZS5tdGwiLCJuYW1lIjoibmV2ZXJfMDFfdW5pbmhhYml0ZWRfdmFyaWFudF9leGhhdXN0aXZlLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCIsInNvdXJjZSI6Ii8vIFBvc2l0aXZlOiBSRkMtMDA3OCBcdTAwYTczLjIvXHUwMGE3NC4xIC0tIHdyaXRpbmcgdGhlIGFybSBmb3IgYW4gdW5pbmhhYml0ZWQgdmFyaWFudCBpc1xuLy8gYWxsb3dlZCAobWVyZWx5IHVucmVhY2hhYmxlLCBub3QgcmVqZWN0ZWQpOyB0aGUgY29tcGlsZXIgbWF5IHdhcm4gYnV0IG11c3Rcbi8vIG5vdCBlcnJvci5cblxuZnVuIHVzZV9yZXN1bHQocjogUmVzdWx0PGk2NCwgIT4pIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHIpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBwYW5pYyhcInVucmVhY2hhYmxlXCIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIHVzZV9yZXN1bHQoUmVzdWx0OjpPayB7IHZhbHVlID0gMyB9KVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDNfdW5yZWFjaGFibGVfYXJtX2FsbG93ZWQubXRsIiwibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InVuaW5oYWJpdGVkX21hdGNoLm10bCIsInNvdXJjZSI6Ii8vIFJGQy0wMDc4IFx1MDBhNzMuMjogbWF0Y2hpbmcgb25seSB0aGUgaW5oYWJpdGVkIHZhcmlhbnQgb2YgYW4gZW51bSB3aXRoIGFcbi8vIGAhYC1wYXlsb2FkIHZhcmlhbnQsIGV4ZXJjaXNlZCBlbmQtdG8tZW5kIHRvIGNvbmZpcm0gZGlzcGF0Y2ggYW5kIHZhbHVlXG4vLyBleHRyYWN0aW9uIHdvcmsgY29ycmVjdGx5IGF0IHJ1bnRpbWUsIG5vdCBqdXN0IGF0IHR5cGVjaGVjayB0aW1lLlxuXG5lbnVtIEZvbyB7XG4gICAgQSB7IHg6IGk2NCB9LFxuICAgIEIgeyB5OiAhIH0sXG59XG5cbmZ1biBoYW5kbGUoZjogRm9vKSAtPiBpNjQge1xuICAgIG1hdGNoIChmKSB7XG4gICAgICAgIEZvbzo6QSB7IHggfSA9PiB4LFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgYXNzZXJ0KGhhbmRsZShGb286OkEgeyB4ID0gNSB9KSA9PSA1KTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL25ldmVyL3VuaW5oYWJpdGVkX21hdGNoLm10bCIsIm5hbWUiOiJ1bmluaGFiaXRlZF9tYXRjaC5tdGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-7}

An enum with exactly one inhabited, single-field variant implicitly coerces to that
field's type; zero-field or multi-field inhabited variants do not receive this coercion.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InNpbmdsZXRvbl9jb2VyY2lvbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3OCBcdTAwYTczLjM6IGluaGFiaXRlZC1zaW5nbGV0b24gY29lcmNpb24sIGV4ZXJjaXNlZCBlbmQtdG8tZW5kIChub3QganVzdFxuLy8gdHlwZWNoZWNrKSB0byBjb25maXJtIHRoZSBjb2VyY2VkIHJ1bnRpbWUgdmFsdWUgaXMgYWN0dWFsbHkgY29ycmVjdC5cblxuZW51bSBXcmFwcGVyPFQ+IHtcbiAgICBQcmVzZW50IHsgdmFsdWU6IFQgfSxcbiAgICBBYnNlbnQgIHsgcGxhY2Vob2xkZXI6ICEgfSxcbn1cblxuZnVuIGluZmFsbGlibGUoKSAtPiBXcmFwcGVyPGk2ND4ge1xuICAgIFdyYXBwZXI6OlByZXNlbnQgeyB2YWx1ZSA9IDQyIH1cbn1cblxuZnVuIGluZmFsbGlibGVfcmVzdWx0KCkgLT4gUmVzdWx0PGk2NCwgIT4ge1xuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDcgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeDogaTY0IDo9IGluZmFsbGlibGUoKTtcbiAgICBsZXQgeTogaTY0IDo9IGluZmFsbGlibGVfcmVzdWx0KCk7XG4gICAgYXNzZXJ0KHggPT0gNDIpO1xuICAgIGFzc2VydCh5ID09IDcpO1xuICAgIGFzc2VydCh4ICsgeSA9PSA0OSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9uZXZlci9zaW5nbGV0b25fY29lcmNpb24ubXRsIiwibmFtZSI6InNpbmdsZXRvbl9jb2VyY2lvbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.types.never-type.dynamics-2}

When every arm of a match diverges, the match expression has type `!`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA0X3BhbmljX2NvZXJjZXMubXRsIiwic291cmNlIjoiLy8gUG9zaXRpdmU6IFJGQy0wMDc4IFx1MDBhNzEuMS9cdTAwYTcyIC0tIGBwYW5pYyhtc2cpYCBoYXMgdHlwZSBgIWAsIHdoaWNoIGNvZXJjZXNcbi8vIGltcGxpY2l0bHkgdG8gYW55IHR5cGUgd2hlcmV2ZXIgdGhlIHN1cnJvdW5kaW5nIGNvbnRleHQgaXMgb3RoZXJ3aXNlXG4vLyB1bmNvbnN0cmFpbmVkLlxuXG5mdW4gcGljayhjb25kOiBib29sZWFuKSAtPiBpNjQge1xuICAgIGlmIChjb25kKSB7XG4gICAgICAgIHBhbmljKFwibm9wZVwiKVxuICAgIH0gZWxzZSB7XG4gICAgICAgIDVcbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICBwaWNrKGZhbHNlKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwiLCJuYW1lIjoibmV2ZXJfMDRfcGFuaWNfY29lcmNlcy5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-8}

`Result<T, !>` has an uninhabited `Err` variant and therefore only an `Ok` value can be
constructed.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InNpbmdsZXRvbl9jb2VyY2lvbi5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3OCBcdTAwYTczLjM6IGluaGFiaXRlZC1zaW5nbGV0b24gY29lcmNpb24sIGV4ZXJjaXNlZCBlbmQtdG8tZW5kIChub3QganVzdFxuLy8gdHlwZWNoZWNrKSB0byBjb25maXJtIHRoZSBjb2VyY2VkIHJ1bnRpbWUgdmFsdWUgaXMgYWN0dWFsbHkgY29ycmVjdC5cblxuZW51bSBXcmFwcGVyPFQ+IHtcbiAgICBQcmVzZW50IHsgdmFsdWU6IFQgfSxcbiAgICBBYnNlbnQgIHsgcGxhY2Vob2xkZXI6ICEgfSxcbn1cblxuZnVuIGluZmFsbGlibGUoKSAtPiBXcmFwcGVyPGk2ND4ge1xuICAgIFdyYXBwZXI6OlByZXNlbnQgeyB2YWx1ZSA9IDQyIH1cbn1cblxuZnVuIGluZmFsbGlibGVfcmVzdWx0KCkgLT4gUmVzdWx0PGk2NCwgIT4ge1xuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDcgfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgeDogaTY0IDo9IGluZmFsbGlibGUoKTtcbiAgICBsZXQgeTogaTY0IDo9IGluZmFsbGlibGVfcmVzdWx0KCk7XG4gICAgYXNzZXJ0KHggPT0gNDIpO1xuICAgIGFzc2VydCh5ID09IDcpO1xuICAgIGFzc2VydCh4ICsgeSA9PSA0OSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9uZXZlci9zaW5nbGV0b25fY29lcmNpb24ubXRsIiwibmFtZSI6InNpbmdsZXRvbl9jb2VyY2lvbi5tdGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-9}

`Result<T, !>` satisfies the inhabited-singleton coercion rule and a match omitting `Err`
is exhaustive.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAyX3Jlc3VsdF9uZXZlcl9lcnJfZXhoYXVzdGl2ZS5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogUkZDLTAwNzggXHUwMGE3NC4xIC0tIFJlc3VsdDxULCAhPiBzYXRpc2ZpZXMgdGhlIHVuaW5oYWJpdGVkLXZhcmlhbnQgcnVsZVxuLy8gYXMgYSBzcGVjaWFsIGNhc2Ugb2YgdGhlIGdlbmVyYWwgcnVsZSAoXHUwMGE3My4yKTsgYSBtYXRjaCBvbWl0dGluZyBgRXJyYCBpc1xuLy8gZXhoYXVzdGl2ZS5cblxuZnVuIHVzZV9yZXN1bHQocjogUmVzdWx0PGk2NCwgIT4pIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHIpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIC8vIFJlc3VsdDo6RXJyIG9taXR0ZWQgLS0gZXhoYXVzdGl2ZTsgRXJyIGlzIHVuaW5oYWJpdGVkIHdoZW4gRSA9ICEuXG4gICAgfVxufVxuXG5mdW4gbWFpbigpIC0+IGk2NCB7XG4gICAgdXNlX3Jlc3VsdChSZXN1bHQ6Ok9rIHsgdmFsdWUgPSAzIH0pXG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy90eXBlcy9uZXZlcl8wMl9yZXN1bHRfbmV2ZXJfZXJyX2V4aGF1c3RpdmUubXRsIiwibmFtZSI6Im5ldmVyXzAyX3Jlc3VsdF9uZXZlcl9lcnJfZXhoYXVzdGl2ZS5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCIsInNvdXJjZSI6Ii8vIFBvc2l0aXZlOiBSRkMtMDA3OCBcdTAwYTczLjIvXHUwMGE3NC4xIC0tIHdyaXRpbmcgdGhlIGFybSBmb3IgYW4gdW5pbmhhYml0ZWQgdmFyaWFudCBpc1xuLy8gYWxsb3dlZCAobWVyZWx5IHVucmVhY2hhYmxlLCBub3QgcmVqZWN0ZWQpOyB0aGUgY29tcGlsZXIgbWF5IHdhcm4gYnV0IG11c3Rcbi8vIG5vdCBlcnJvci5cblxuZnVuIHVzZV9yZXN1bHQocjogUmVzdWx0PGk2NCwgIT4pIC0+IGk2NCB7XG4gICAgbWF0Y2ggKHIpIHtcbiAgICAgICAgUmVzdWx0OjpPayB7IHZhbHVlIH0gPT4gdmFsdWUsXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBwYW5pYyhcInVucmVhY2hhYmxlXCIpLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIHVzZV9yZXN1bHQoUmVzdWx0OjpPayB7IHZhbHVlID0gMyB9KVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDNfdW5yZWFjaGFibGVfYXJtX2FsbG93ZWQubXRsIiwibmFtZSI6Im5ldmVyXzAzX3VucmVhY2hhYmxlX2FybV9hbGxvd2VkLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-10}

`Perhaps<!>` has only its zero-field `None` variant inhabited; it does not coerce to a
field type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA4X3BlcmhhcHNfbmV2ZXJfZXhoYXVzdGl2ZS5tdGwiLCJzb3VyY2UiOiIvLyBSRkMtMDA3OCBcdTAwYTc1OiBQZXJoYXBzPCE+IGhhcyBvbmx5IG9uZSBpbmhhYml0ZWQgdmFyaWFudCAtLSBOb25lLiBUaGUgU29tZVxuLy8gdmFyaWFudCB3b3VsZCByZXF1aXJlIGEgdmFsdWUgb2YgdHlwZSAhLCB3aGljaCBjYW5ub3QgYmUgY29uc3RydWN0ZWQsIHNvXG4vLyBhIG1hdGNoIG9taXR0aW5nIFNvbWUgaXMgZXhoYXVzdGl2ZS5cbmZ1biB1c2VfcGVyaGFwcyhwOiBQZXJoYXBzPCE+KSAtPiBpNjQge1xuICAgIG1hdGNoIChwKSB7XG4gICAgICAgIFBlcmhhcHM6Ok5vbmUgPT4gMCxcbiAgICAgICAgLy8gU29tZSBvbWl0dGVkIC0tIGV4aGF1c3RpdmU7IFNvbWUgaXMgdW5pbmhhYml0ZWQgd2hlbiBUID0gIS5cbiAgICB9XG59XG5cbmZ1biBtYWluKCkgLT4gaTY0IHtcbiAgICB1c2VfcGVyaGFwcyhQZXJoYXBzOjpOb25lKVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDhfcGVyaGFwc19uZXZlcl9leGhhdXN0aXZlLm10bCIsIm5hbWUiOiJuZXZlcl8wOF9wZXJoYXBzX25ldmVyX2V4aGF1c3RpdmUubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.types.never-type.legality-11}

A function declared `-> !` is legal only when every reachable control-flow path diverges;
a reachable ordinary return is a type error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0078](../../rfcs/4-implemented/rfc-0078-bottom-type.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA1X3JldF9uZXZlcl9kaXZlcmdlc19vay5tdGwiLCJzb3VyY2UiOiIvLyBQb3NpdGl2ZTogUkZDLTAwNzggXHUwMGE3NiAtLSBhIGZ1bmN0aW9uIGRlY2xhcmVkIGAtPiAhYCB0eXBlY2hlY2tzIHdoZW4gZXZlcnlcbi8vIHBhdGggZ2VudWluZWx5IGRpdmVyZ2VzIChhIGBwYW5pY2AgdGFpbCBleHByZXNzaW9uLCBvciBhIGBsb29wYCB3aXRoIG5vXG4vLyByZWFjaGFibGUgYGJyZWFrYCkuXG5cbmZ1biBhYm9ydChtc2c6IFN0cmluZykgLT4gISB7XG4gICAgcGFuaWMobXNnKVxufVxuXG5mdW4gbG9vcF9mb3JldmVyKCkgLT4gISB7XG4gICAgbG9vcCB7IH1cbn1cblxuZnVuIGFib3J0X3ZpYV9yZXR1cm4obXNnOiBTdHJpbmcpIC0+ICEge1xuICAgIC8vIEFsc28gZmluZTogdGhlIGByZXR1cm5gZWQgZXhwcmVzc2lvbiBpdHNlbGYgbmV2ZXIgcHJvZHVjZXMgYSB2YWx1ZS5cbiAgICByZXR1cm4gcGFuaWMobXNnKTtcbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfMDVfcmV0X25ldmVyX2RpdmVyZ2VzX29rLm10bCIsIm5hbWUiOiJuZXZlcl8wNV9yZXRfbmV2ZXJfZGl2ZXJnZXNfb2subXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im5ldmVyXzA3X3BhbmljX3NlbWljb2xvbl9kaXZlcmdlcy5tdGwiLCJzb3VyY2UiOiIvLyBJc3N1ZSAjMjI5L1JGQy0wMDc4IFx1MDBhNzY6IGEgYmFyZSBgcGFuaWMobXNnKTtgICh0cmFpbGluZyBgO2AsIG5vdCB0YWlsXG4vLyBwb3NpdGlvbikgYXMgYSBmdW5jdGlvbidzIGxhc3Qgc3RhdGVtZW50IG11c3Qgc3RpbGwgYmUgcmVjb2duaXplZCBhc1xuLy8gZGl2ZXJnZW50LiBQcmV2aW91c2x5IGBmdW5fYm9keV9kaXZlcmdlc2Agb25seSBzcGVjaWFsLWNhc2VkIHRoZSByZW1vdmVkXG4vLyBgVHlwZWRTdG10OjpSZXR1cm5gL2BCcmVha2AvYENvbnRpbnVlYCB2YXJpYW50cyBkaXJlY3RseSBhbmQgb3RoZXJ3aXNlXG4vLyBhbHdheXMgcmV0dXJuZWQgYGZhbHNlYCBmb3IgYW55IG90aGVyIGxhc3Qtc3RhdGVtZW50IHNoYXBlIC0tIGEgbGF0ZW50IGdhcFxuLy8gdGhhdCBtYWRlIHRoaXMgZXhhY3QgY2FzZSAoYSBzZW1pY29sb24tdGVybWluYXRlZCBkaXZlcmdpbmcgY2FsbCwgbm90IGFcbi8vIHRhaWwgZXhwcmVzc2lvbikgaW5jb3JyZWN0bHkgcmVqZWN0ZWQgdW5kZXIgYC0+ICFgLlxuZnVuIGFib3J0X3N0bXQobXNnOiBTdHJpbmcpIC0+ICEge1xuICAgIHBhbmljKG1zZyk7XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3R5cGVzL25ldmVyXzA3X3BhbmljX3NlbWljb2xvbl9kaXZlcmdlcy5tdGwiLCJuYW1lIjoibmV2ZXJfMDdfcGFuaWNfc2VtaWNvbG9uX2RpdmVyZ2VzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDE2IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJuZXZlcl9uZWdfMDFfcmV0X25ldmVyX3JlYWNoYWJsZV9yZXR1cm4ubXRsIiwic291cmNlIjoiLy8gTmVnYXRpdmU6IFJGQy0wMDc4IFx1MDBhNzYgLS0gYSBmdW5jdGlvbiBkZWNsYXJlZCBgLT4gIWAgY29udGFpbmluZyBhIHJlYWNoYWJsZSxcbi8vIG9yZGluYXJ5IGByZXR1cm5gIChvbmUgd2hvc2UgdmFsdWUgaXMgTk9UIGl0c2VsZiBgIWAtdHlwZWQpIGlzIGEgdHlwZSBlcnJvcjpcbi8vIHRoZSBmdW5jdGlvbiBhY3R1YWxseSByZXR1cm5zLCB3aGljaCBgLT4gIWAgZm9yYmlkcy5cblxuZnVuIGJhZCgpIC0+ICEgeyAvLyBFUlJPUltUMDAxNl1cbiAgICByZXR1cm4gNTtcbn1cblxuZnVuIG1haW4oKSB7fVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmV2ZXJfbmVnXzAxX3JldF9uZXZlcl9yZWFjaGFibGVfcmV0dXJuLm10bCIsIm5hbWUiOiJuZXZlcl9uZWdfMDFfcmV0X25ldmVyX3JlYWNoYWJsZV9yZXR1cm4ubXRsIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## `Perhaps<T>`

`Perhaps<T>` is the built-in optional type. There is no null — all absence is expressed via `Perhaps<T>`.

[The type of `None` is `Perhaps<T>` for some `T` that must be determinable from context](#spec.types.perhaps-t.legality-1). If no context constrains `T` — for example, a bare `let x = None` with no annotation and no subsequent use that pins the element type — the program is a type error. An explicit annotation is required in that case:

> **Changed in v0.11.0 (RFC-0111): `None` and `Some` are ordinary variants of `Perhaps<T>`, not literals.**

`None` and `Some` have no special status in the grammar or the type system. They resolve exactly as `Red` does for a user-declared `enum Colour { Red, .. }` — bare where the expected type determines the enum, qualified (`Perhaps::None`) anywhere. Everything said here about needing a determinable type follows from that general rule rather than from a rule about `None` specifically, and the same is true of `Result<T, E>`'s `Ok`/`Err`. See [Expressions — Unqualified variant constructors](expressions.md#unqualified-variant-constructors).

```metel
fun main() -> i64 {
    let x: Perhaps<i64> := None;
    match (x) {
        Some { value } => value,
        None => 0,
    }
}
```

```metel
fun main() -> i64 {
    let result: Perhaps<i64> := None;
    let value: Perhaps<i64> := Some { value = 42 };
    match (value) {
        Some { value } => value,
        None => match (result) {
            Some { value } => value,
            None => 0,
        },
    }
}
```

Use `match` to unwrap safely:

```metel
struct User {
    id: i64,
}

fun find_user(id: i64) -> Perhaps<User> {
    if (id == 1) {
        return Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    match (find_user(1)) {
        Some { value } => value.id,
        None => 0,
    }
}
```

`.yolo()` unwraps, panicking if the value is `None`:

```metel
struct User {
    id: i64,
}

fun find_user(id: i64) -> Perhaps<User> {
    if (id == 1) {
        return Some { value = User { id = 1 } };
    }
    return None;
}

fun main() -> i64 {
    let user := find_user(1).yolo();
    return user.id;
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.types.perhaps-t.legality-1}

`None` is the empty variant of `Perhaps<T>` and is valid only where the expected type
determines `T`; `Perhaps::None` is valid wherever the qualified variant is named.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0020](../../rfcs/4-implemented/rfc-0020-language-rebranding.md), [rfc-0111](../../rfcs/4-implemented/rfc-0111-unqualified-enum-variants-in-expression-position.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjM5X3BlcmhhcHMubXRsIiwic291cmNlIjoiZnVuIGZpbmQoYXJyOiBpNjRbXSwgdGFyZ2V0OiBpNjQpIC0+IFBlcmhhcHM8aTY0PiB7XG4gICAgdmFyIGkgOj0gMDtcbiAgICB3aGlsZSAoaSA8IGFyci5sZW4oKSkge1xuICAgICAgICBpZiAoYXJyW2kgYXMgdTY0XSA9PSB0YXJnZXQpIHtcbiAgICAgICAgICAgIHJldHVybiBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSBpIH07XG4gICAgICAgIH1cbiAgICAgICAgaSArPSAxO1xuICAgIH1cbiAgICBOb25lXG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIE5vbmUgbGl0ZXJhbCBtYXRjaGVzIHRoZSBOb25lIHBhdHRlcm4uXG4gICAgbGV0IG46IFBlcmhhcHM8aTY0PiA6PSBOb25lO1xuICAgIGxldCByMSA6PSBtYXRjaCAobikgeyBOb25lID0+IC0xLCBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSwgfTtcbiAgICBhc3NlcnQocjEgPT0gLTEpO1xuICAgIC8vIFBlcmhhcHM6OlNvbWUgY29uc3RydWN0aW9uIGFuZCBmaWVsZCBleHRyYWN0aW9uIHZpYSBtYXRjaC5cbiAgICBsZXQgcyA6PSBQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA0MiB9O1xuICAgIGxldCByMiA6PSBtYXRjaCAocykgeyBOb25lID0+IC0xLCBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSwgfTtcbiAgICBhc3NlcnQocjIgPT0gNDIpO1xuICAgIC8vIFBlcmhhcHMgYXMgZnVuY3Rpb24gcmV0dXJuIHR5cGUgXHUyMDE0IGZvdW5kIGNhc2UuXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMCwgNDBdO1xuICAgIGxldCBpZHggOj0gZmluZChhcnIsIDMwKTtcbiAgICBsZXQgcjMgOj0gbWF0Y2ggKGlkeCkgeyBOb25lID0+IC0xLCBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiB2YWx1ZSwgfTtcbiAgICBhc3NlcnQocjMgPT0gMik7XG4gICAgLy8gUGVyaGFwcyBhcyBmdW5jdGlvbiByZXR1cm4gdHlwZSBcdTIwMTQgbm90LWZvdW5kIGNhc2UuXG4gICAgbGV0IGlkeDIgOj0gZmluZChhcnIsIDk5KTtcbiAgICBsZXQgcjQgOj0gbWF0Y2ggKGlkeDIpIHsgTm9uZSA9PiAtMSwgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gdmFsdWUsIH07XG4gICAgYXNzZXJ0KHI0ID09IC0xKTtcbiAgICAvLyBQZXJoYXBzIGluIGV4cHJlc3Npb24gcG9zaXRpb24gXHUyMDE0IHRoZSBtYXRjaCByZXN1bHQgaXMgdXNhYmxlIGRpcmVjdGx5LlxuICAgIGxldCBkb3VibGVkIDo9IG1hdGNoIChmaW5kKGFyciwgMjApKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IHZhbHVlICogMixcbiAgICAgICAgTm9uZSA9PiAwLFxuICAgIH07XG4gICAgYXNzZXJ0KGRvdWJsZWQgPT0gMik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9lbnVtcy8zOV9wZXJoYXBzLm10bCIsIm5hbWUiOiIzOV9wZXJoYXBzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCIsInNvdXJjZSI6ImVudW0gQ29sb3VyIHsgUmVkLCBHcmVlbiwgQmx1ZSB9XG5cbnN0cnVjdCBIb2xkZXIge1xuICAgIGNvbG91cjogQ29sb3VyLFxuICAgIG1heWJlOiBQZXJoYXBzPGk2ND4sXG4gICAgbm90aGluZzogUGVyaGFwczxpNjQ+LFxuICAgIG9rOiBSZXN1bHQ8aTY0LCBTdHJpbmc+LFxuICAgIGVycjogUmVzdWx0PGk2NCwgU3RyaW5nPixcbn1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHtcbiAgICBtYXRjaCAoYykge1xuICAgICAgICBSZWQgPT4gMSxcbiAgICAgICAgR3JlZW4gPT4gMixcbiAgICAgICAgQmx1ZSA9PiAzLFxuICAgIH1cbn1cblxuZnVuIGZhdm91cml0ZSgpIC0+IENvbG91ciB7XG4gICAgR3JlZW5cbn1cblxuZnVuIHNoYWRvdyhSZWQ6IGk2NCkgLT4gaTY0IHtcbiAgICByZXR1cm4gUmVkO1xufVxuXG5mdW4gdW53cmFwX3Jlc3VsdChyOiBSZXN1bHQ8aTY0LCBTdHJpbmc+KSAtPiBpNjQge1xuICAgIG1hdGNoIChyKSB7XG4gICAgICAgIE9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiAtMSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBjOiBDb2xvdXIgOj0gUmVkO1xuICAgIGxldCBjMjogQ29sb3VyIDo9IFJlZCB7fTtcbiAgICBhc3NlcnQocGFpbnQoYykgPT0gMSk7XG4gICAgYXNzZXJ0KHBhaW50KGMyKSA9PSAxKTtcbiAgICBhc3NlcnQocGFpbnQoQmx1ZSkgPT0gMyk7XG4gICAgYXNzZXJ0KHBhaW50KGZhdm91cml0ZSgpKSA9PSAyKTtcblxuICAgIGxldCBob2xkZXIgOj0gSG9sZGVyIHtcbiAgICAgICAgY29sb3VyID0gQmx1ZSxcbiAgICAgICAgbWF5YmUgPSBTb21lIHsgdmFsdWUgPSA1IH0sXG4gICAgICAgIG5vdGhpbmcgPSBOb25lLFxuICAgICAgICBvayA9IE9rIHsgdmFsdWUgPSA5IH0sXG4gICAgICAgIGVyciA9IEVyciB7IGVycm9yID0gXCJiYWRcIiB9LFxuICAgIH07XG5cbiAgICBhc3NlcnQocGFpbnQoaG9sZGVyLmNvbG91cikgPT0gMyk7XG4gICAgYXNzZXJ0KHNoYWRvdyg3KSA9PSA3KTtcblxuICAgIG1hdGNoIChob2xkZXIubWF5YmUpIHtcbiAgICAgICAgU29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfVxuXG4gICAgbWF0Y2ggKGhvbGRlci5ub3RoaW5nKSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KHRydWUpLFxuICAgIH1cblxuICAgIGFzc2VydCh1bndyYXBfcmVzdWx0KGhvbGRlci5vaykgPT0gOSk7XG4gICAgYXNzZXJ0KHVud3JhcF9yZXN1bHQoaG9sZGVyLmVycikgPT0gLTEpO1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3IvZW51bXMvNDFfdW5xdWFsaWZpZWRfdmFyaWFudF9jb25zdHJ1Y3RvcnMubXRsIiwibmFtZSI6IjQxX3VucXVhbGlmaWVkX3ZhcmlhbnRfY29uc3RydWN0b3JzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQyX3ZhcmlhbnRfZGVmZXJyYWxfcmVzb2x2ZXMubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMyODUncyBjaGVjayBtdXN0IG5vdCBmaXJlIG9uIGEgZGVmZXJyYWwgdGhhdCAqZG9lcyogcmVzb2x2ZSwgYXQgYW55IG9mIHRoZVxuLy8gcG9zaXRpb25zIFJGQy0wMTExIHN1cHBvcnRzLCBhbmQgbXVzdCBsZWF2ZSBnZW51aW5lbHkgcG9seW1vcnBoaWMgZGVmZXJyYWxzIGFsb25lLlxuZW51bSBDb2xvdXIgeyBSZWQsIEdyZWVuLCBCbHVlIH1cblxuZnVuIHBhaW50KGM6IENvbG91cikgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbmZ1biBmYXZvdXJpdGUoKSAtPiBDb2xvdXIgeyBHcmVlbiB9XG5cbi8vIEEgY2xvc3VyZSB3aXRoIGEgZGVjbGFyZWQgcmV0dXJuIHR5cGUgZ2l2ZXMgaXRzIGJvZHkgYW4gZXhwZWN0ZWQgdHlwZSwgc28gYSBiYXJlXG4vLyB2YXJpYW50IGluc2lkZSBpdCByZXNvbHZlcyBub3JtYWxseS5cbmZ1biBhbm5vdGF0ZWRfY2xvc3VyZSgpIC0+IENvbG91ciB7XG4gICAgbGV0IGYgOj0gfHwgLT4gQ29sb3VyIHsgUmVkIH07XG4gICAgcmV0dXJuIGYoKTtcbn1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGM6IENvbG91ciA6PSBSZWQ7XG4gICAgYXNzZXJ0KHBhaW50KGMpID09IDEpO1xuICAgIGFzc2VydChwYWludChCbHVlKSA9PSAxKTtcblxuICAgIGxldCBnOiBDb2xvdXIgOj0gZmF2b3VyaXRlKCk7XG4gICAgYXNzZXJ0KHBhaW50KGcpID09IDEpO1xuXG4gICAgbGV0IHA6IFBlcmhhcHM8aTY0PiA6PSBTb21lIHsgdmFsdWUgPSA1IH07XG4gICAgbGV0IHE6IFBlcmhhcHM8aTY0PiA6PSBOb25lO1xuICAgIGFzc2VydChwYWludChhbm5vdGF0ZWRfY2xvc3VyZSgpKSA9PSAxKTtcblxuICAgIC8vIEFuIGVtcHR5IGFycmF5IGxpdGVyYWwgaXMgZGVmZXJyZWQgdG9vLCBhbmQgaXMgKmdlbnVpbmVseSogcG9seW1vcnBoaWMgLS0gdGhlXG4gICAgLy8gIzI4NSBjaGVjayBpcyBzY29wZWQgdG8gYmFyZSB2YXJpYW50cyBwcmVjaXNlbHkgc28gdGhpcyBrZWVwcyB3b3JraW5nLlxuICAgIGxldCBtayA6PSB8fCB7IFtdIH07XG4gICAgbGV0IGludHM6IGk2NFtdIDo9IG1rKCk7XG4gICAgbGV0IHN0cnM6IFN0cmluZ1tdIDo9IG1rKCk7XG4gICAgYXNzZXJ0KGludHMubGVuKCkgPT0gMCk7XG4gICAgYXNzZXJ0KHN0cnMubGVuKCkgPT0gMCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9lbnVtcy80Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCIsIm5hbWUiOiI0Ml92YXJpYW50X2RlZmVycmFsX3Jlc29sdmVzLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## `Result<T, E>`

`Result<T, E>` represents the outcome of a fallible operation:

```metel
fun divide(a: f64, b: f64) -> Result<f64, String> {
    if (b == 0.0) {
        return Err { error = "division by zero" };
    }
    return Ok { value = a / b };
}

fun main() -> i64 {
    match (divide(8.0, 2.0)) {
        Ok { value } => value as i64,
        Err { error } => 0,
    }
}
```

Use `match` to handle both cases, or [`?`](functions.md#spec.functions.the-operator.dynamics-2)
to propagate errors.

[`.yolo()`](runtime.md#spec.runtime.panics.dynamics-1) also works on `Result<T, E>`,
panicking on `Err`.
