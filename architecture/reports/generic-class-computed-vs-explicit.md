---
title: "Generic Type Classes: Computed (Open by Default) versus Explicit (Opt-In)"
date: '2026-11-07'
status: report
relates: rfc-0089, rfc-0206, rfc-0212
---

# Generic Type Classes: Computed (Open by Default) versus Explicit (Opt-In)

A side-by-side comparison for decision D7 of `linear-types-decision-register.md`: how a generic type or function
decides whether it accepts linear arguments. It records both models on the same programs. It does not choose.

## 1. The two models

The question is the **default for a type parameter**. Both models are sound, and both compute the class of an
instance from its fields. They differ in who must write something.

| | **Model X: open by default** (the reserved design, D4 and D7) | **Model Y: opt-in** (Austral `Type`, Swift `~Copyable` style) |
|---|---|---|
| Bare `T` in a function | possibly linear, assumes no capabilities | assumed `Discard`, so droppable |
| Accepting a linear argument | automatic | the parameter is written `T: ?Discard` |
| Dropping a `T` in generic code | needs `T: Discard` | free for a bare `T`; needs `T: Discard` again only inside a `?Discard` parameter |
| A generic type's class | computed from owned fields per instantiation | computed only through `?Discard` parameters; other parameters are discardable by definition |
| A type that must reject linear arguments | writes `T: Discard` on the parameter | does nothing; this is the default |
| Who is annotated | code that drops a value | code that wants to support linear values |
| Error when a linear value meets code that cannot take it | at the drop site, inside the generic body | at the call site: "`T` is not `?Discard`" |

Two further models were considered and set aside:

- **Model Z: a declared class per generic type, with no conditional class.** `Pair<T>` is either always affine or
  always linear. It cannot serve both `Pair<i64>` and `Pair<Tx>`, so a linear user needs a second container type.
- **Model H: open for functions, opt-in for types.** A function over `Option<T>` could not stay open while `Option`
  is closed, so every function on a generic type inherits the type's opt-in. It degenerates into Model Y.

## 2. Eight programs under both models

"Linear-ready" means the author wants linear arguments to work. Counts are annotation occurrences added when linear
types ship (`T: Discard` for X, `?Discard` or a re-tightening `T: Discard` for Y). Std Option and Result method
bodies follow the stdlib, with the drops identified by the review-10 audit.

### P1. `Option<T>` methods

```metel
extend<T> Option<T> {
    fun is_some(&self) -> boolean { .. }
    fun map<U>(self, f: |T| -> U) -> Option<U> { .. }
    fun and_then<U>(self, f: |T| -> Option<U>) -> Option<U> { .. }
    fun unwrap_or(self, d: T) -> T { .. }          // drops `d` or the payload
}
extend<T> Option<T> { fun ok_or<E>(self, e: E) -> Result<T, E> { .. } }   // drops `e`
```

- **X:** `unwrap_or` writes `where T: Discard`, `ok_or` writes `where E: Discard`. **2.**
- **Y (linear-ready):** both impl blocks opt in with `T: ?Discard` (2), and `unwrap_or` re-tightens `T: Discard` (1).
  The `E` that `ok_or` drops is discardable by default. **3.**
- **Y (not linear-ready):** **0.** `Option<Tx>` is then impossible.

### P2. A growable `List<T>`

```metel
struct List<T> { .. }
extend<T> List<T> {
    fun push(&var self, x: T) { .. }
    fun pop(&var self) -> Option<T> { .. }
    fun len(&self) -> i64 { .. }
    fun clear(&var self) { .. }                       // drops the elements
}
```

- **X:** `clear` needs `where T: Discard`. **1.**
- **Y (linear-ready):** `struct List<T: ?Discard>` (1), `extend<T: ?Discard> List<T>` (1), `clear` re-tightens (1). **3.**
- **Y (not linear-ready):** **0.**

### P3. A user function that only moves

```metel
fun swap<T>(a: T, b: T) -> (T, T) { (b, a) }
```

- **X:** **0.**
- **Y (linear-ready):** `T: ?Discard`. **1.** (not ready: **0**)

### P4. A callback API

```metel
fun apply<T, U>(x: T, f: |T| -> U) -> U { f(x) }
```

- **X:** **0.** A non-`linear` function type is `Discard`, and `x` and the result move through.
- **Y (linear-ready):** `T: ?Discard, U: ?Discard`. **2.** (not ready: **0**)

### P5. A function that only reads

```metel
fun show<T: Display>(x: T) { print(&x); }      // drops x at the end
```

- **X:** `T: Discard`, or take `&T` instead. **1.**
- **Y:** **0.** `T` is discardable, and a linear caller is rejected with a note about `?Discard`.

### P6. A wrapper with a destructor

```metel
struct Logged<T> { value: T }
extend<T> Logged<T>: Drop { fun drop(&var self) { log("gone"); } }
```

- **X:** the impl becomes conditional, `extend<T: Discard> Logged<T>: Drop`. Plus the own-method dismantling rule
  for `into_inner` (D13). **1.**
- **Y (linear-ready):** `struct Logged<T: ?Discard>` (1), the conditional drop impl `T: Discard` (1), plus the same
  dismantling rule. **2.** (not ready: **0**, and `Logged<Tx>` is impossible)

### P7. A forwarder

```metel
fun relay<T>(x: T) -> T { identity(x) }
```

- **X:** **0.**
- **Y (linear-ready):** **1.** (not ready: **0**)

### P8. A non-linear user's ordinary generic function

```metel
fun max_of<T: Ord>(a: T, b: T) -> T { if a > b { a } else { b } }     // drops the smaller
```

- **X:** `T: Discard` is needed once linear ships, even though this author never uses a linear type. **1.**
- **Y:** **0.**

### Totals

| | X | Y (all linear-ready) | Y (author not linear-ready) |
|---|---|---|---|
| P1 | 2 | 3 | 0 |
| P2 | 1 | 3 | 0 |
| P3 | 0 | 1 | 0 |
| P4 | 0 | 2 | 0 |
| P5 | 1 | 0 | 0 |
| P6 | 1 | 2 | 0 |
| P7 | 0 | 1 | 0 |
| P8 | 1 | 0 | 0 |
| **Total** | **6** | **12** | **0** |

Read the table as a trade, not a score:

- **X charges every generic author a little, always.** The 6 land on code that drops a value, whether or not the
  author cares about linear types (P5, P8 are the cases C2 worries about).
- **Y charges nothing to authors who do not care, and about twice as much to those who do.** The 12 land on code that
  moves values, which is most generic code (P2, P3, P4, P7).
- **The break-even is the fraction of generic code whose author wants linear arguments to work.** For a standard library
  that is meant to be usable with linear types, that fraction is close to 100 percent, which favours X. For application
  code it is close to 0, which favours Y.

The 6 versus 12 count uses these eight programs only. The earlier std census (2026-11-05) found 30 to 40 percent of
by-value generic functions drop a value on some path, so X's cost is a fraction of generic functions and Y's
linear-ready cost is the remaining 60 to 70 percent plus every generic type declaration and impl block.

## 3. Other axes

### Who is blocked when code does not cooperate

- **X:** a linear user is blocked only by generic code that actually drops its argument. A library that forgets to
  say `T: Discard` is rejected when the check turns on, at its own definition, and the library author fixes it.
- **Y:** a linear user is blocked by every library generic that has not opted in, and cannot fix it. The ecosystem
  has to adopt `?Discard` before linear types are usable with it. Rust's `?Sized` and Swift's `~Copyable` both show
  years of staged adoption across their standard libraries (MEMORY: Swift needed SE-0427 and a series of follow-up
  proposals for std types; not re-checked).

### Prior art on the default

| Language | Default | Source quality |
|---|---|---|
| Rust | implicit `Sized`, relaxed with `?Sized` (opt-in, Model Y shape) | VERIFIED in codex review 10: Rust reference, trait bounds |
| Swift | implicit `Copyable`, relaxed with `~Copyable` (Y shape) | VERIFIED in codex review 10: SE-0427 |
| Austral | explicit universe `Type` (Y shape, declared) | VERIFIED in codex review 10: Austral spec |
| Mojo | moved from implied destructibility to **explicit destruction bounds** in the 1.0 line (X direction) | VERIFIED in codex review 10: release notes v1.0.0b2 |

The prior art splits, and the one language that moved did so toward X. Languages that keep Y shapes (Rust, Swift) do
so mainly because their ecosystem already existed when the capability was introduced.

### Public API stability

- **X:** an owned `T` field added to a public generic type changes only which instantiations are linear. Adding a field
  that is linear for every instantiation forces the keyword (D10), so that change is explicit. Linear users and
  generic clients without `T: Discard` are affected. Rust documents the same hazard for auto traits (RFC 1105).
  **Mitigation (D19, reserved):** a public generic type states its `Discard` condition like its `Copy` and `Clone`
  conditions. With no statement, outside code sees the conservative default (`Discard` exactly when every parameter
  is), and the statement is checked against the fields. Making a type more permissive is then never breaking, and
  making it less permissive than stated is an error at the declaration.
- **Y:** supporting linear arguments is itself a visible, versioned edit (`?Discard` appears in the signature), so
  removing support is a visible breaking change.

### Teaching and spelling

- **X:** `T: Discard` is a positive capability, spelled like `Copy` and `Clone`.
- **Y:** `?Discard` is a relaxation of an implicit bound, which is the form of `?Sized`, widely cited as a hard
  concept (MEMORY).

### Cost of changing the decision

- Metel has no users, and the std generic surface is small today: 8 generic declarations across `stdlib/*.mtl`
  (a generic function, `List<T>` and array impls, and the row-generic impls) plus the Option and Result methods.
  The `T: Discard` bound is vacuous in v0.16.0, so **switching now costs almost nothing**.
- After std and user code are written against one model, switching either way touches every generic declaration.

## 4. What would change my view

- **Toward X if:** the standard library and the first real libraries are meant to work with linear values (most
  likely for effects and capabilities, which want exactly-once consumption), because Y would then annotate nearly
  every generic declaration.
- **Toward Y if:** linear types stay a niche feature used mostly in application code, because then X's 6 annotations
  per 8 programs are paid by authors who never use them. C2 becomes the stronger criterion.
- **A test that would decide it:** write the first 20 generic functions of the effects design under both models and
  count (a) annotations and (b) how many cannot be written without opting in.

## 5. Recommendation space (not a decision)

1. **Keep X.** Consistent with the owner's C1. Accept that every generic author writes `T: Discard` where they drop.
2. **Switch to Y.** Consistent with C2. Accept that linear support is opt-in and every std generic is annotated.
3. **Keep X for now, test with the effects design before the `linear` release.** The bound is vacuous in v0.16.0,
   so the decision can wait, but it must be made before std grows. This is the course the reserved status in RFC-0089
   already implies.
