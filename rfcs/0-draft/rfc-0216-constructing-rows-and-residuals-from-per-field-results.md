---
id: rfc-0216
title: "Constructing Rows and Residuals from Per-Field Results"
date: '2026-11-05'
updated: '2026-11-07'
status: draft
---

> **Status — draft (2026-11-05).** First draft. Nothing here is decided.

> **Not a dependency.** The `Copy`/`Clone` settlement (RFC-0206, RFC-0207, RFC-0211, RFC-0212,
> RFC-0213) does not wait for this RFC. It is the construction half of RFC-0214's row-generic impl and
> takes RFC-0174's open question 7 out of that RFC.

## Summary

A `comptime for` loop over a row (RFC-0174) can read every field. It cannot yet **build** a value from
the per-field results, so a method that returns `Self` (`clone`, `default`, a deserializer) cannot be
written once over a row. This RFC adds two things:

1. **A computed-label record literal**, `{ .[field.name] = expr, .. }`, whose labels are `Label` values
   (RFC-0175), so a loop can produce a record of the same row as its input.
2. **A residual construction** for a branded type: inside the defining module, a record of the right row
   is spread into a call of the residual, `T.{ ..R }(..record)` (RFC-0100 §7), which builds a residual of
   the brand. Outside that module it is not available.

```metel
extend Doc: Clone<record R> where ..R: Clone {          // RFC-0214 row-generic form
    fun clone(&self: Self.{ ..R }) -> Self.{ ..R } {
                return Self.{ ..R }(..{                         // residual construction, defining module only
            comptime for field in fields(R) {
                .[field.name] = self.[field.name].clone(),
            }
        });
    }
}
```

## Motivation

1. **RFC-0174 stops at reading.** It lets a body walk a row but says `Clone` and `Default` "need to
   *build* a record whose labels are compile-time values" and leaves that to open question 7 and to
   RFC-0093. Without it the only Self-returning aspects that can be written over a row are the ones the
   compiler generates.
2. **RFC-0214 cannot offer a written template without it.** A row-generic residual impl (RFC-0214
   section 1) exists so that an author can write `Clone` once for every width of a brand with their own
   tweak. Its `Self`-returning methods need a way to produce a residual.
3. **The std templates need the same thing.** RFC-0209's `Copy`/`Clone`/`Eq` templates generate
   exactly this code. Specifying the construction makes the template mechanism user-accessible instead
   of a compiler privilege, which is the point of the settlement's "as few exceptions as possible".
4. **A residual is produced only by projection or partial move today** (RFC-0137). A type with a
   private field cannot let outside code forge a residual, so the construction must be restricted.

## 1. Computed-label record literal

`{ .[e] = v, .. }` is a record literal whose label is the `Label` `e` (RFC-0175, RFC-0188). It may appear
only where `e` is comptime-known (RFC-0132 §1.1), normally `field.name` of an enclosing `comptime for`
(RFC-0174 D2). A `comptime for` may appear inside a record literal and contributes one
`.[field.name] = v` entry per iteration, in field order.

Typing: the literal's row is the union of its literal entries and the entries its loops produce. A
loop over `fields(R)` whose entries are `.[field.name] = f(self.[field.name])` has row `.{ ..R' }`, where
`R'` maps each field type through `f`. For `clone`, `R' = R`; the checker proves this once, against the
symbolic field of RFC-0174 D3, from the bound `..R: Clone` (RFC-0123), not per instantiation.

## 2. Residual construction

`T.{ ..R }(..record)` builds a residual of the brand `T` from a record, with these rules. The brace form
`T.{ ..R } { entries }` is a brace construction and is prohibited by RFC-0100 §5; the record is passed by the
spread of RFC-0100 §7, as `new Type(..r)` is for a struct.

1. **Defining module only.** It may be written only in the module that defines `T` (RFC-0214 rule 1).
   A brand with private fields therefore cannot be forged from outside.
2. **Row match.** The record must be exactly the row `R` of the residual type, no more, no fewer.
3. **Constructor invariants and authority.** A brand's constructors may enforce invariants (RFC-0137 section 6).
   A residual construction bypasses them. A projection or partial move only keeps values the brand already
   produced, whereas arbitrary construction can create field combinations no constructor allows. "Entries derived from
   a value of the same brand" is not yet a checkable typing rule, so the authority for construction is **open**
   (open question 2): the defining-module restriction of rule 1 is the only rule fixed here.
4. **Full width.** When `R` is the brand's whole row the result normalises to `T` (RFC-0137).
5. **Enums** have no residuals (RFC-0150) and are outside this rule.

## 3. Relationship to existing RFCs

- **RFC-0175 / RFC-0188** — the `Label` type and the spelling `.[e]` of a computed label.
- **RFC-0100** — the whole-row construction expression `new T(..r)` this RFC's residual construction uses, and the prohibition of the
  brace form (§5).
- **RFC-0174** — supplies the loop and computed access; this RFC closes its open question 7 for rows
  and residuals. Whether `emit` (RFC-0093) is still needed for other outputs is left to RFC-0093.
- **RFC-0214** — the row-generic impl form is the consumer.
- **RFC-0137** — residual types, the constructor-invariant risk of section 6.
- **RFC-0123, RFC-0208** — `where ..R: A` and the row binder.
- **RFC-0209, RFC-0217** — the std templates are the compiler's instance of this mechanism.
- **RFC-0093 / RFC-0092** — derive functions and `emit`; the alternative route to construction.

## Alternatives considered

- **`emit` / derive functions only (RFC-0093).** Generates code rather than values; larger and not
  yet settled. The literal form needs no new execution model.
- **Compiler-only construction.** Keeps the std templates working and leaves written templates
  impossible, so a type with a customised `Clone` loses it on every projection. Rejected for the
  reason RFC-0214 gives.
- **A `clone_residual` intrinsic.** One more special form per aspect, the exception the settlement
  avoids.

## Out of Scope

- Reading and writing through computed access beyond RFC-0174 D2.
- Construction of residuals of a foreign brand.
- Enum variants and variant rows (RFC-0210).

## Unresolved Questions

1. **Spelling.** The call form `T.{ ..R }(..record)` follows RFC-0100 §7. Confirm that it parses as a call
   whose head is a projection type, and that it does not collide with RFC-0137's projection `.{ }`
   (a projection expression lists labels and has no `..R` tail).
2. **How narrow is the capability.** Should construction be restricted to bodies that take the brand
   itself as input (clone-shaped), or may a defining-module body build a residual from arbitrary
   values? The second is the constructor-invariant risk.
3. **Mapping field types.** Whether a loop may change field types (`Default`, a serializer) or only
   preserve them (`Clone`), and how `R'` is inferred or written.
4. **Order and duplicates.** The unrolled entries are in field order (RFC-0174 open question 3);
   whether an explicit entry may override a looped one (a custom tweak such as resetting `hits`).
5. **Failure cleanup.** A clone that fails or panics halfway leaves partly built values; RFC-0206's
   derived-clone cleanup order must apply to the loop, and a linear intermediate result needs its own rule
   (RFC-0089 section 2.2).
6. **Interaction with `Drop`.** A residual of a `Drop` brand cannot be built field-wise without
   deciding who runs the destructor (RFC-0137 section 5).

---

## Decision

**Outcome:** *(pending)*
