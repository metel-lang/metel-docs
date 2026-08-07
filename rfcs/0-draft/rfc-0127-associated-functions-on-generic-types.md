---
id: rfc-0127
title: "Associated Functions on Generic Types"
date: '2026-08-01'
status: draft
target:
---

## Summary

An `extend` block may already declare a function with no receiver, and calling it through
the type's path already works — for a **non-generic** type:

```metel
struct Counter { n: i64 }
extend Counter { fun new() -> Counter { return Counter { n = 0 }; } }

let c = Counter::new();          // works today
```

The same declaration on a **generic** type parses, typechecks and is unreachable:

```metel
struct Tok<T> { v: T }
extend<T> Tok<T> { fun make(v: T) -> Tok<T> { return Tok { v = v }; } }

let t = Tok::make(7);            // [T0003] unresolved path `Tok::make`
```

This RFC closes that gap. It is a small feature with a large blast radius: the design
corpus assumes it in **140 call sites across 31 files**, and the standard library declares
generic associated functions that only work because they are natively bound.

---

## Motivation

### The feature is already assumed everywhere

`Rc::new` appears 18 times in RFC prose, `BumpAlloc::scoped` 13, `List::new` 6,
`Bar::default` 6, `BumpRegion::scoped` 6, `Handle::from_record` 4, `Chan::new` 3. Whole
designs — RFC-0074 (shared ownership), RFC-0076 (Rc brands), RFC-0063/0065 (allocator
handles) — are written in terms of a constructor call that no user can write today. None of
those RFCs proposes associated functions, because every author reasonably assumed they
existed.

### The standard library ships an API shaped like one

```metel
extend List<T> {
    native(@std.core.list_new)   fun new() -> List<T>;
    native(@std.core.list_from)  fun from(src: T[]) -> List<T>;
}
```

`List::new()` and `List::from([1, 2, 3])` both work. But they work because `List` is a
builtin whose methods are seeded into the scheme table directly; the same two lines on a
user's own generic type do not resolve. So the language's own standard library models an
idiom the language does not offer, which is the most misleading possible state: users copy
the pattern and it fails.

### It is the only remaining way to write a constructor with a name

RFC-0114 (`Construct` aspect) gives canonical construction through an *aspect method*.
RFC-0100 gives call-shaped construction, `Point(x = 1.0)`. Neither offers a **named**
alternative constructor — `Rect::square(4)`, `Chan::bounded(16)`, `Date::from_iso(s)` — and
for a generic type there is currently no way to write one at all.

---

## 1. What works today, measured

Run against `develop` (`dfeb5b4`) on 2026-08-01. This section is the actual boundary, not
an approximation of it.

| form | today |
|---|---|
| `Counter::new()` — non-generic type, inherent | **works** |
| `S::make()` — non-generic, function declared by an aspect | **works** |
| `List::new()` — generic, builtin with `native` binding | **works** |
| `Opt::Nothing` — generic *enum variant* path | **works** |
| `Tok::make(7)` — generic, user-defined | `T0003 unresolved path` |
| `Tok::make(7)` with `let t: Tok<i64> = …` | `T0003` — the annotation does not help |
| `Tok<i64>::make(7)` — explicit target arguments | **parse error** |
| `Tok::make::<i64>(7)` — turbofish after the name | `T0003` |
| `Mk::make()` — through the *aspect* name rather than the type | `T0003` |

Two conclusions matter for scope. The declaration side is **complete** — a no-receiver
`fun` in an `extend` block on a generic type parses, typechecks, and its body is checked.
And the feature is not missing so much as **inconsistently reachable**: three of the four
working rows above are the same operation as the failing one.

### Why it fails

Path resolution ends in `typechecker/inference.rs`:

```rust
if let Some((scheme, _)) = ctx.method_scheme_for(type_name, member_name) { … }
if let Some(info) = ctx.get_enum(type_name) { … }        // enum variants
Err(unresolved path `{path_str}`)
```

`method_scheme_for` is keyed on `(type_name, member_name)` and holds one scheme. A method
on a generic type is not registered there — generic methods live in the *variant* registry
(`method_scheme_variants_for`), each variant carrying its own bounds, because a type may
have several impls with different bounds providing the same name. The path lookup never
consults it, so the entry exists and is not found.

That also explains the enum row: enum variants have their own arm, which mints fresh type
arguments for the enum's parameters — exactly the step associated functions need.

---

## 2. Proposal

A path `Type::name` in expression position resolves to a no-receiver function declared in
an `extend` block whose target head is `Type`, for generic and non-generic types alike.

```metel
struct Tok<T> { v: T }
extend<T> Tok<T> {
    fun make(v: T) -> Tok<T> { return Tok { v = v }; }
}

let t = Tok::make(7);            // t : Tok<i64>
```

The type's own parameters are **instantiated fresh at the call site** and solved by
ordinary inference, the same as calling a generic free function. Nothing about the callee's
body changes; only the path resolves.

### 2.1 Receiverless is the trigger, not a new keyword

A function in an `extend` block is an associated function precisely when it declares no
receiver. That is already the parsed distinction (`Param.receiver: Option<ReceiverKind>`),
already what makes `Counter::new()` work, and it needs no `static` keyword. RFC-0044
settled the three receiver forms; this is the fourth case it did not name — their absence.

A method **with** a receiver stays unreachable through the path form. `Tok::get(t)`
(UFCS-style explicit-receiver calls) is a separate feature with its own ambiguity
questions, and is out of scope.

### 2.2 Aspect-declared associated functions

`extend S: Mk { fun make() -> S { … } }` already makes `S::make()` work for a non-generic
`S`. That must extend to generic targets unchanged, since a `Construct`-style aspect
(RFC-0114) is otherwise uncallable on any generic type.

---

## 3. Open questions

### OQ1 — When the target's parameters are not inferable

```metel
extend<T> Tok<T> { fun empty() -> i64 { return 0; } }
let n = Tok::empty();            // T appears nowhere
```

`T` is unconstrained. Options: reject with "cannot infer type arguments for `Tok`, annotate
the call", or accept and leave `T` free where it is genuinely unused. Rust rejects. Leaning
reject — an unconstrained parameter almost always means the author expected inference to
find something.

### OQ2 — Which turbofish position, and does the other become an error?

`Tok::make::<i64>(7)` currently fails resolution but *parses* — the grammar has
`"::<" ~ type_args ~ ">" ~ "(" …` for call and method-call postfix. `Tok<i64>::make(7)`
does not parse at all.

Note the ambiguity these disambiguate is real but distinct: `Tok::make::<i64>` names the
**function's** parameters, while `Tok<i64>::make` names the **type's**. For
`fun make<U>(v: U) -> Tok<T>` they are different lists. RFC-0023 settled ascription versus
turbofish for free functions; this needs the same treatment one level deeper. Leaning:
support `Tok::make::<…>` for the function's own parameters only, and leave the type's
parameters to inference or to an annotation on the binding — but that leaves no spelling
for the OQ1 case, which is the argument against.

### OQ3 — `Aspect::method()`

`Mk::make()` fails today even for a non-generic `S`. Rust allows `Trait::method(x)` and
`<S as Trait>::method()`, which matter when two aspects give a type the same name. Metel
has that collision — `stage19_neg_05/06` are fixtures for ambiguous aspect methods on one
target. Out of scope here, but the resolution rule this RFC adds should not foreclose it.

### OQ4 — Coherence with several bounded impls

`method_scheme_variants_for` exists because a type may have several impls providing one
name under different bounds (RFC-0036 conditional impls):

```metel
extend<T: Copy>  Wrapper<T> { fun make(v: T) -> Wrapper<T> { … } }
extend<T: !Copy> Wrapper<T> { fun make(v: T) -> Wrapper<T> { … } }
```

For a *method* the receiver's type picks the variant. For an associated function there is
no receiver, so selection must come from the call's arguments and expected type. If neither
determines it, is that an ambiguity error or a deferred constraint? This is the one place
the feature is genuinely harder than "consult a second registry", and it is why this is an
RFC rather than a bug report.

### OQ5 — Does this change the orphan rule?

RFC-0097 governs blanket impls on bare parameters. `extend<T> T { fun make() -> T }` would
declare an associated function on *every* type. Presumably already refused by RFC-0097's
rule, but it should be confirmed rather than assumed.

---

## 4. Implementation sketch

Deliberately thin — the design questions above dominate the cost.

1. Extend the `Path` arm in `inference.rs` to consult the generic-method variant registry
   after `method_scheme_for` misses, instantiating the target's type parameters fresh, the
   way the enum-variant arm below it already does for its own parameters.
2. Mirror it in `typechecker/construction.rs`, whose `unresolved path` site is the
   construction-pass twin. **Both** sites need it — RFC-0127's own siblings #592 and #598
   were each one half of a two-site rule where only one side had been updated, so this is a
   known failure mode in this area.
3. Variant selection per OQ4, which is where the real work is.
4. The evaluator already dispatches these for non-generic types; confirm no runtime change
   is needed beyond the resolved scheme carrying its type arguments.

---

## 5. Prior art

- **Rust** — `impl<T> Vec<T> { fn new() -> Self }`, called `Vec::new()`, `Vec::<i32>::new()`
  or by inference. Both turbofish positions exist and mean different things, which is the
  OQ2 question already answered once by someone else.
- **Swift** — static/type methods on generic types, with the type's parameters inferred
  from context or written `Array<Int>.init()`.
- **Metel's own enum variants** — `Opt::Nothing` on a generic enum already mints fresh type
  arguments. The mechanism this RFC needs exists in the same match statement, ten lines
  below the branch that fails.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
