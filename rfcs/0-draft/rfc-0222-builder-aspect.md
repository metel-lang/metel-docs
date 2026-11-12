---
id: rfc-0222
title: "Builder Aspect"
date: '2026-11-07'
status: draft
---

## Summary

A struct opts in to a typestate builder with `derives Builder`. The builder is a std row template (RFC-0209), not
a compiler-generated type: it tracks which fields have been set in its type, offers one generic setter keyed by a
label, and offers `build()` only when every field is set.

```metel
struct Server derives Builder { host: String, port: i64 }

let s := Server::builder()
    .set(.host, "a.com")        // Building<Server, .., { .host: String }>
    .set(.port, 8080)           // Building<Server, .., { .host: String, .port: i64 }>
    .build();                   // Server::construct({ .host = .., .port = .. }), RFC-0114
```

Setting a field twice, setting a field the struct does not have, setting a value of the wrong type, and calling
`build()` early are all compile errors. The builder consumes itself at each step, so the type can change from one
state to the next. No code is generated per struct.

This is a library-level RFC. It adds no syntax and no compiler feature of its own; it is what RFC-0100, RFC-0114,
RFC-0132, RFC-0188, RFC-0207, RFC-0209 and RFC-0221 make writable, stated so that their combination is checked
once. It is a design draft. Nothing here is accepted, and several of the RFCs it depends on are drafts.

---

## Motivation

### Piecewise construction is already a row

RFC-0114 §3 notes that a value built field by field only constructs once, when its row becomes complete:

```metel
let partial := { .a = compute_a() };
let partial := { ..partial, .b = compute_b() };
let full := Type(..partial);                         // RFC-0100 §7
```

A record is a typestate builder, and `new Type(..r)` is the final step. What it lacks is a method-call form that can
be chained, can be handed across a function boundary with a type that says what is still missing, and can be
requested by a struct with one word.

### What this adds over a record plus `new Type(..r)`

- **A named, nominal state.** `Building<Server, .{ .host: String }, .{ .host: String, .port: i64 }>` tells a reader
  and the checker which fields remain. A bare record's type says which are present but not which are required.
- **Chaining.** `.set(…).set(…).build()` reads in one expression. The record form needs a `let` per step or a
  nested literal.
- **A place for later extensions**: defaults, batch setters and named setters (Open Questions) attach to one
  aspect and not to every struct.
- **No per-struct code.** The alternative that generates `ServerBuilder` and `.host(v)` needs metaprogramming that
  is not close (RFC-0092, RFC-0094).

### Why not a compiler-provided derive

RFC-0207 gives `Copy`, `Clone` and `Debug` compiler-written derives, and RFC-0209 shows the derivation behind
`derives` is the aspect's own row template applied to the type's row. A builder written the same way is a library
aspect that exercises the mechanism from outside the compiler, which is the settlement's stated aim of as few
exceptions as possible.

---

## Proposal

### 1. The pieces

```metel
// std
struct Building<T, record Need, record Have> { fields: .{ ..Have } }

aspect Builder {
    type Start;                       // the empty state, Building<Self, <Self's row>, {}>
    fun builder() -> Self::Start;
}
```

`Building<T, Need, Have>` is the typestate. `T` is the target struct, `Need` is the target's complete row, and
`Have` is the row of fields set so far. `Need` is carried as a parameter so that no associated row (`T.Row`)
is required: the aspect names the state through an ordinary associated type (RFC-0082), and the template in §2
fills it in with a row it has in scope. Both rows are row parameters (RFC-0186, RFC-0208).

### 2. The template

`derives Builder` makes the struct's row visible to `Builder`'s row template (RFC-0209 §1). The template is where
`Need` comes into scope:

```metel
extend<record R> { ..R }: Builder {
    type Start = Building<Self, ..R, ..{}>;
    fun builder() -> Self::Start {
        Building(fields = {})
    }
}
```

For a nominal `T` that granted visibility, `Self` is `T` and `R` is `T`'s row (RFC-0209 rule 3). `builder()` returns
the empty state, `Building<T, ..R, ..{}>`, written with a closed literal row (RFC-0180), and `Server::builder()`
has that type after the associated type is resolved.

### 3. Setting a field

```metel
extend<T, record Need, record Have> Building<T, ..Need, ..Have> {
    fun set<V>(self, comptime l: Label, v: V)
        -> Building<T, ..Need, ..{ .[l]: V, ..Have }>
    where Need: { .[l]: V, .. }, Have: !{.[l]} {
        Building(fields = { .[l] = v, ..self.fields })
    }
}
```

- `l` is a comptime `Label` parameter (RFC-0132 §3.6) and appears in the return type. It is a unification
  variable resolved from the call's argument, as `V` is, and not an expression evaluated during checking.
- `Need: { .[l]: V, .. }` requires the target to have a field `l` of type `V`. `Have: !{.[l]}` (RFC-0189) requires
  that it is not yet set.
- The method takes `self` by value. The result has a different type from the receiver, which a `&var` method
  could not give.

### 4. Building

```metel
extend<T, record R> Building<T, ..R, ..R> {
    fun build(self) -> T {
        new T(..self.fields)
    }
}
```

`build` exists only on `Building<T, ..R, ..R>`: the `Have` row equals `Need`. The result is exactly what
`new T(..self.fields)` yields (RFC-0114 §5): a bare `T` when `T::Error` is `!`, and `Result<T, T::Error>` otherwise.
This RFC adds no result-handling rule. A struct with an invariant therefore validates once, inside `construct`,
when the builder completes.

### 5. Worked example

```metel
struct Server derives Builder { host: String, port: i64 }

fun connection(b: Building<Server, ..{ .host: String, .port: i64 }, ..{ .host: String }>)
    -> Server
{
    b.set(.port, 8080).build()                         // finishes a partly built Server
}

let b := Server::builder().set(.host, "a.com");        // Building<Server, .., { .host: String }>
let s := connection(b);
```

### 6. What is rejected

```metel
Server::builder().set(.host, "a").set(.host, "b");     // Have already has `host`: `Have: !{.host}` fails
Server::builder().set(.hostname, "a");                 // Need has no field `hostname`
Server::builder().set(.port, "80");                    // field `port` is i64, not String
Server::builder().set(.host, "a").build();             // no `build` on a state with `Have` ≠ `Need`
let b := Server::builder();
b.set(.host, "a"); b.set(.port, 1);                    // `b` was moved by the first call
```

The last case is the ordinary affine rule: `set` takes `self` by value, so the builder cannot be used twice.

### 7. Visibility

`set(.secret, v)` names a field label at the call site. `derives Builder` grants the struct's row to the
builder template (RFC-0209), which entitles the template and not its callers, so a call that names a private
field is rejected at that call (RFC-0175 §9). That is the rule RFC-0032 already applies to constructing a struct
with a private field from outside its module (RFC-0100 §7 item 6; RFC-0114 open question 8 asks whether that is
enough once `construct` is public). The consequence is that a caller outside the module cannot
complete the builder of a struct with a private field, because it cannot supply that field. Such a struct should
offer its own constructor function in place of `derives Builder`. This RFC does not add a visibility rule of its
own.

---

## What this does not include

- **Per-field setter names (`.host(v)`).** They need a method named by a label, which is code generation
  (RFC-0092 `emit`, RFC-0094) or a compiler-written derive. The generic `set(.host, v)` is the form this RFC
  offers. A later RFC may add named setters on top without changing `Building`.
- **Defaults and optional fields.** There is no field-default syntax in the corpus. RFC-0119's idea of
  defaulting an omitted `Option<T>` field to `none` was descoped. All fields are required in this RFC. Defaults
  would change `build`'s condition from "`Have` equals `Need`" to "`Have` contains every required label of
  `Need`", a bound between two rows (Open Question 2).
- **A mutating builder.** A `&var` builder cannot change its type, so it would hold `Option` fields and fail at
  `build` at run time. That is a different, weaker design and is not proposed.
- **Enums.** Enums have no `Construct` and no residuals (RFC-0114 §8, RFC-0150).

---

## Alternatives Considered

| Option | Verdict |
|---|---|
| **Std row template, generic `set`** | **Proposed.** No per-struct code, no compiler privilege beyond RFC-0207/0209, and the state is a type. Setters are keyed by label, not by name. |
| Compiler-provided derive (like `Copy`/`Clone`) | Would allow `.host(v)`, but is a compiler special case that cannot be written by a library, against the settlement's aim. |
| Generated builder struct (`ServerBuilder`, `.host(v)`) | The usual shape in other languages. Needs `emit` (RFC-0092/0094), which is not close. A later layer, not a replacement. |
| No builder: record plus `new Type(..r)` | Works today in outline (Motivation). Lacks the chained form and a nominal state. A reasonable position if this RFC is declined. |
| Keyword-argument construction only (RFC-0100) | Covers complete construction. Does not cover partial construction passed between functions. |
| Runtime-checked `&var` builder | Weaker: failure at run time. Not proposed. |

---

## Interactions

- **RFC-0100 / RFC-0114:** `build` is `new T(..fields)`, i.e. `T::construct`. A brace literal for `Building` itself is
  prohibited like any struct's, hence `Building(fields = …)`.
- **RFC-0132 §3, RFC-0175, RFC-0188, RFC-0221:** `set` needs a comptime `Label` parameter in a method, a label
  variable `.[l]` in a row field, and dotted row fields. These are the label model.
- **RFC-0207 / RFC-0209 / RFC-0212:** `derives Builder` is the grant of row visibility. Whether a user or std aspect
  with a row template is derivable is Open Question 1.
- **RFC-0180 (implemented):** supplies the closed and open literal rows in `Building<T, ..R, ..{}>`.
- **RFC-0189 (per-label negative bounds):** `Have: !{.[l]}`.
- **RFC-0123 (field-wise bounds):** unaffected; a builder places no bound on the field types.
- **RFC-0091 / RFC-0137 (residuals):** a narrowed or partially moved struct is another kind of partial value.
  `Building` is the forward counterpart, assembling a struct, and does not interact with residuals.

---

## Costs

- **A comptime parameter in a return type.** `set`'s return type mentions its own comptime `Label` argument
  (RFC-0132 §3.6d). That is unification, not dependent typing, but it is new for a method and is the part
  of the label model this RFC leans on hardest.
- **Setters by label, not by name.** `set(.host, v)` is more verbose than `.host(v)` and a typo is a type error,
  not a missing method. That is a deliberate trade for generating nothing.
- **Type size.** A long chain produces a distinct type per step. They are erased after checking and cost nothing
  at run time, but diagnostics print them. A diagnostic should print `Building<Server, missing: port>`, a point
  for the prototype.
- **A dependency pile.** This RFC cannot be accepted before the label model, RFC-0100 and RFC-0114, RFC-0209,
  and an answer to Open Question 1.

---

## Changes on Acceptance

- std: `Builder`, `Building`, and the template in §2 to §4.
- Spec: aspects, and a short section on typestate builders.
- Fixtures: each case in §5 and §6, and a struct with an invariant (so `build` returns a `Result`).
- A diagnostic printer for `Building` states.

---

## Open Questions

1. **Is `derives` open to an aspect with a row template that is not compiler-written?** RFC-0207 says `derives`
   requests an aspect "that has a derivation (`Copy`, `Clone`, `Debug`)", and RFC-0209 says the derivation is the
   aspect's own template applied to the type's row, with the `derivable` modifier gone from the settled design.
   If any aspect with a template is derivable, `Builder` needs nothing more. If not, this RFC needs either a
   std-only exception or RFC-0212 to define what makes an aspect derivable.
2. **Defaults.** `build` requires `Have` equal to `Need`. Optional fields need a bound between two rows and a
   source of defaults. Neither exists; decide whether a follow-up RFC owns both.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- `set`'s signature type-checks: a method whose return type mentions its own comptime `Label` parameter, with
  a label variable in a row field and in a row bound.
- `build` on `Building<T, ..R, ..R>` is accepted only when the two rows are equal, and rejected otherwise. If a
  repeated parameter in an impl head is not legal, the equality is expressed with a `where` row equation and the
  prototype says which.
- Each rejected case in §6 gives the stated error.
- A struct with an invariant: `build` returns what `new T(..fields)` returns.
- The diagnostic for an incomplete `build` names the missing labels.

---

## References

- RFC-0100 — Constructor-call construction; RFC-0114 — Constructor aspect and canonical construction.
- RFC-0207 — Declaration clauses; RFC-0209 — Per-aspect row visibility; RFC-0212 — Aspect declaration properties.
- RFC-0132 — Comptime execution model (§3); RFC-0175 — Label polymorphism; RFC-0188 — Label syntax;
  RFC-0221 — Dotted row labels.
- RFC-0180 — Literal rows in row arguments; RFC-0189 — Per-label negative row bounds;
  RFC-0186, RFC-0208 — rows as a parameter and the row binder.
- RFC-0092, RFC-0094 — comptime core and metaprogramming (`emit`), the route to named setters.
- RFC-0119 — Record conversions (descoped omitted-field defaulting).
- RFC-0032 — Field-level visibility; RFC-0082 — Associated types.

---

## Decision

**Outcome:** *(pending)*
