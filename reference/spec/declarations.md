# Declarations

`public` may be prefixed to top-level `fun`, `struct`, `enum`, and `aspect`
declarations to mark them as accessible from other modules. Top-level `let` and `var`
bindings remain module-private. See [Modules — Visibility](modules.md#visibility) for
the full rules. The current `public` / `var` / `extend` surface spellings are the
spelling set introduced by RFC-0098.

## Variables

### Immutable Bindings

```metel
fun main() -> i64 {
    let x = 42;
    let name: String = "Vlad";
    if (name == "Vlad") { return x; }
    return 0;
}
```

`let` bindings cannot be reassigned and must always be initialized. Mutability lives entirely on the binding — a `let` binding is immutable regardless of what value it holds. This means:

- `x = newValue` is rejected (reassignment)
- `x.field = value` is rejected (field assignment through an immutable binding)
- `&var x` is rejected (taking a mutable reference to an immutable binding)

All three forms require `var`.

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.immutable-bindings.legality-1}

A `let` binding must be initialized and cannot be assigned after initialization.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Mutable Bindings

```metel
fun main() -> i64 {
    var counter = 0;
    counter = counter + 1;
    counter += 1;
    return counter;
}
```

`var` bindings can be reassigned and also must be initialized at declaration. Compound assignment operators `+=`, `-=`, `*=`, `/=`, `%=` are supported.

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.variables.mutable-bindings.legality-1}

A `var` binding must be initialized and may be assigned after initialization; `var` is the
mutable binding spelling.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0042](../../rfcs/4-implemented/rfc-0042-let-mut-bindings.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Scoping and Shadowing

Variables are lexically scoped. Each block `{ }` introduces a new scope. Inner scopes can shadow outer variables.

`let` and `var` declarations are sequential — a binding is visible only from its declaration point to the end of its containing block.

`fun` declarations are hoisted to the top of their containing block. All `fun` declarations in a block are mutually visible to each other and to all other statements in that block, regardless of declaration order. This enables forward references and mutual recursion at any nesting level.

Hoisting is block-local: a `fun` declared in an inner block is not visible in the outer block. Normal lexical scoping applies across block boundaries — inner blocks see outer declarations, outer blocks do not see inner declarations.

```metel
fun is_even(n: i64) -> boolean {
    if (n == 0) { return true; }
    return is_odd(n - 1);
}

fun is_odd(n: i64) -> boolean {
    if (n == 0) { return false; }
    return is_even(n - 1);
}

fun outer() -> i64 {
    inner();

    fun inner() {
        helper();
        fun helper() { }
    }

    return 1;
}

fun main() -> i64 {
    if (is_odd(3)) { return outer(); }
    return 0;
}
```

An inner function remains scoped to its own block. For example, `helper();` is valid inside `inner()`, but calling `helper();` from `outer()` is a type error.

<!-- doc-example: expect-fail reason="demonstrates that helper() is not visible from outer() -- the type error is the point" -->
```metel
fun outer() {
    fun inner() {
        fun helper() { }
        helper();
    }

    helper();
}

fun main() {
    outer();
}
```

Top-level `struct` and `enum` declarations are hoisted to program scope — they may be
referenced before their declaration appears in the source.

Types declared inside a function body are local to that body from their declaration
point onward; they are not visible from other functions.

```metel
fun make_point() -> Point {
    return Point { x = 1.0, y = 2.0 };   // OK — Point is globally visible
}

struct Point {
    x: f64,
    y: f64,
}

fun inner() {
    struct LocalPoint {
        x: f64,
        y: f64,
    }
    let p = LocalPoint { x = 1.0, y = 2.0 };
}

fun main() -> i64 {
    inner();
    let p = make_point();
    return p.x as i64;
}
```

Top-level `extend` blocks follow the same declaration-order rule as the types they extend.

---

## Structs

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p = Point { x = 1.0, y = 2.0 };
    return p.y as i64;
}
```

### Instantiation and Field Access

> **Changed in v0.12.0: field initializers separate with `=`, not `:` — `Point { x = 1.0 }`; field *declarations* keep `:`.**

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p = Point { x = 1.0, y = 2.0 };
    let x = p.x;
    return x as i64;
}
```

When a local variable has the same name as a field, the `= value` part can be omitted
([**shorthand field init**](#spec.declarations.structs.instantiation-and-field-access.legality-1)):

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let x = 1.0;
    let y = 2.0;
    let p = Point { x, y };
    return p.x as i64;
}
```

Shorthand and explicit fields may be mixed freely within one literal.

Zero-field structs [may omit braces entirely](#spec.declarations.structs.instantiation-and-field-access.legality-2).
These two forms are [equivalent](#spec.declarations.structs.instantiation-and-field-access.dynamics-2):

```metel
struct Empty {}

let a = Empty;
let b = Empty {};
```

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-1}

A struct-literal field initializer is `ident`, optionally followed by `= expr`. When `=
expr` is present, `ident` names the field and `expr` its value. When omitted, `ident` must
name both the field and a local binding in scope at the literal (shorthand/punning field
init). Shorthand and explicit fields may be freely mixed within one struct literal.
(ADR-0050 pilot: migrated from RFC-0115 §1, `2026-08-20`.)

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [43_shorthand_field.toml](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/43_shorthand_field.toml)_</span>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

A shorthand field `ident` in a struct literal evaluates identically to the explicit form
`ident = ident`: the field takes the value of the local binding named `ident` that is in
scope at the literal. (ADR-0050 pilot: migrated from RFC-0115 §2, `2026-08-20`.)

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [43_shorthand_field.toml](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/43_shorthand_field.toml)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-2}

A zero-field struct may be constructed either as its bare type name or with empty braces.

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-2}

For a zero-field struct, the bare and empty-brace constructor forms evaluate to the same
struct value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-3}

A struct with fields cannot omit its constructor fields; its bare type name is resolved as a
name rather than as a constructor expression.

</details>

### Methods

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun distance(self, other: Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        return dx * dx + dy * dy;   // squared distance
    }
}

fun main() -> i64 {
    let p = Point { x = 1.0, y = 2.0 };
    let q = Point { x = 4.0, y = 6.0 };
    let d = p.distance(q);
    return d as i64;
}
```

`self` refers to the receiver. Methods are called with dot syntax.

### Receiver Forms

Methods may declare one of three receiver forms:

- `self` — value receiver
- `&self` — shared reference receiver
- `&var self` — mutable reference receiver

Value receivers follow ordinary Metel value semantics. Shared and mutable reference
receivers operate on the original receiver storage and are the right forms for
observers and in-place mutation.

```metel
struct Point {
    x: f64,
    y: f64,
}

extend Point {
    fun length(&self) -> f64 {
        self.x * self.x + self.y * self.y
    }
}
```

```metel
struct Counter {
    value: i64,
}

extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}
```

Calls requiring `&var self` need a mutable addressable receiver or a `&var T`
reference. Calls requiring `&self` may use an addressable receiver or a `&T` / `&var T`
reference (RFC-0067a — missed when that RFC integrated `*T`/`*mut T` → `&T`/`&var T`
elsewhere; caught while integrating this batch).

```metel
struct Counter {
    value: i64,
}

extend Counter {
    fun increment(&var self) {
        self.value += 1;
    }
}

fun main() -> i64 {
    var c = Counter { value = 1 };
    c.increment();
    return c.value;
}
```

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.receiver-forms.legality-1}

`&var self` is the mutable-reference receiver spelling and requires a mutable addressable
receiver or an `&var T` reference at the call site.

</details>

### Generic Structs

```metel
struct Pair<A, B> {
    first: A,
    second: B,
}

fun main() -> i64 {
    let p = Pair { first = 1, second = true };
    return p.first;
}
```

---

## Enums

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir = Direction::North;
    let s = Shape::Circle { radius = 5.0 };
    let area = match s {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match dir {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

Variants may be unit (no data) or struct-like (named fields).

When a struct-like variant's field set is empty, both constructor spellings are
accepted:

```metel
enum Flag {
    On {},
}

let x = Flag::On;
let y = Flag::On {};
```

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.legality-1}

A zero-field enum variant may be constructed either as its qualified path or with empty
braces.

##### Dynamic Semantics {#spec.declarations.enums.dynamics-1}

For a zero-field enum variant, the bare and empty-brace constructor forms evaluate to the
same variant value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Instantiation

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir = Direction::North;
    let s = Shape::Circle { radius = 5.0 };
    let area = match s {
        Circle { radius }           => radius * radius * 3.14159,
        Rectangle { width, height } => width * height,
    };
    match dir {
        North => area as i64,
        South => 0,
        East => 0,
        West => 0,
    }
}
```

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.enums.instantiation.legality-1}

A struct-like enum variant with fields cannot omit its constructor fields.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0106](../../rfcs/4-implemented/rfc-0106-optional-braces-for-empty-constructors.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Methods on Enums

`extend` blocks on enums follow the same syntax as structs:

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

extend Shape {
    fun area(self) -> f64 {
        match self {
            Circle { radius } => 3.14159 * radius * radius,
            Rectangle { width, height } => width * height,
        }
    }
}

fun main() -> i64 {
    let s = Shape::Circle { radius = 5.0 };
    return s.area() as i64;
}
```

---

## Aspects

> **Availability:** Since v0.4.0.

```metel
aspect Printable {
    fun print(self);
}

aspect Comparable {
    fun compare(self, other: Self) -> i64;
}

fun main() -> i64 {
    return 0;
}
```

### Bodyless Aspect Declarations

```metel
aspect Copy2;
```

An aspect declaration may end with `;` instead of a braced body when the body would be
empty already: zero methods and zero associated types. This is pure sugar for
`aspect Copy2 { }`.

The shorter spelling does **not** promise that the aspect stays empty forever. If a
later revision adds a method or associated type, the declaration simply switches back
to the braced form.

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.bodyless-aspect-declarations.legality-1}

An aspect declaration may use `;` instead of a braced body only when it declares zero
methods and zero associated types.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0103](../../rfcs/4-implemented/rfc-0103-bodyless-aspect-declarations.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Implementing an Aspect

```metel
struct Point {
    x: f64,
    y: f64,
}

aspect Printable {
    fun print(self);
}

extend Point: Printable {
    fun print(self) {
        print("(");
        print(self.x.to_string());
        print(", ");
        print(self.y.to_string());
        println(")");
    }
}

fun main() {
    let p = Point { x = 1.0, y = 2.0 };
    p.print();
}
```

**Aspect implementation method set.** An `extend Type: Aspect` block must define
exactly the methods declared by `Aspect`: every declared method must be present unless it
has a default body, and no additional methods are permitted. Put a type-specific method
that is not part of the aspect in an inherent `extend Type { ... }` block; inherent and
aspect implementations may coexist for the same type.

> **Changed in v0.12.1.** An undeclared method in an aspect implementation is rejected.

**Conditional extend blocks.** An aspect implementation for a
generic type may be conditional on its own type parameters satisfying additional
bounds, written in a `where` clause after the aspect clause (or inline, before the
target type):

```metel
struct Pair<A, B> { first: A, second: B }

extend Pair<A, B>: Printable where A: Printable, B: Printable {
    fun print(self) { ... }
}

// equivalent, inline form:
extend<A: Printable, B: Printable> Pair<A, B>: Printable { ... }
```

`Pair<i64, String>` is `Printable`; `Pair<i64, SomeNonPrintableType>` is not — both
remain constructable, since a struct's own unconditional bounds (above) and an extend
block's conditional bounds are checked independently. The compiler checks a conditional
block's bounds at every point the aspect is required — method call, bound check, impl
selection — not at the block's own declaration site:

```metel
fun print_pair<A: Printable, B: Printable>(p: Pair<A, B>) {
    p.print();   // ok -- conditional impl applies; A: Printable and B: Printable
}

fun use_pair(p: Pair<i64, SomeNonPrintable>) {
    p.print();   // error T0012: Pair<i64, SomeNonPrintable> does not implement
                 //   Printable, because SomeNonPrintable does not implement Printable
}
```

A generic function propagates a conditional extend block to its own callers by stating
the bound explicitly — the compiler never infers which bounds a caller needs:

```metel
fun print_sorted<T: Comparable + Printable>(list: SortedList<T>) {
    list.print();   // ok -- T: Printable, so the conditional extend block applies
}
```

Negative bounds may appear in a conditional `extend` block's `where` clause on the same
terms as positive ones:

```metel
extend<T: !Drop> Container<T>: BulkDrop { ... }
```

**Coherence.** Two conditional `extend` blocks of the same aspect for the same type are
a coherence error (`T0015`) unless they are provably disjoint. Disjointness is
established by **syntactic negation** only — one block must carry an explicit negative
bound that directly negates a positive bound in the other. The compiler performs no
inference beyond this direct check:

```metel
// Accepted -- T: !Copy directly negates T: Copy; provably disjoint
extend<T: Copy> Wrapper<T>: Serialize { ... }
extend<T: !Copy> Wrapper<T>: Serialize { ... }

// error T0015 -- no direct negation between Clone and Display; not provably disjoint
extend<T: Clone> Wrapper<T>: Serialize { ... }
extend<T: Display> Wrapper<T>: Serialize { ... }
```

A conditional `extend` block and an unconditional `extend` block for the same type
constructor are also a coherence error — the unconditional block already covers every
instantiation the conditional one would. Conditional blocks are subject to the same
orphan rule as unconditional ones (above): the aspect or the type's outermost
constructor must be local.

**Bare-parameter blanket impls.** `extend<T: Bound> T: Aspect` — where the target is
the block's own generic parameter rather than a named struct or enum wrapping it, e.g.
`extend<T: Copy> T: Clone` — is a distinct case from every other example in this
section, which all target a genuine named type (`Pair<A, B>`, `Container<T>`,
`Wrapper<T>`). A bare type parameter has no outermost type constructor for the orphan
rule (below) to check — it isn't declared in any module, including the block's own.
Target-locality is therefore **vacuously unsatisfiable** for this shape: such an extend
is permitted only through the aspect side of the orphan rule, never the target side.

```metel
// std::core — permitted: Clone is local to std::core
extend<T: Copy> T: Clone { fun clone(self: &T) -> T { self } }

// user module — permitted: MyAspect is local here
aspect MyAspect { fun tag(self) -> String; }
extend<T: Copy> T: MyAspect { fun tag(self) -> String { "copyable" } }

// user module — REJECTED (T0014): Display is foreign, and a bare-parameter
// target can never be local, anywhere
extend<T: Copy> T: Display { fun to_string(self) -> String { "?" } }
```

This confines any one aspect's bare-parameter blanket impl to a single module (its own
declaring module, or `std::core` for a built-in aspect) — no separate overlap-detection
mechanism is needed beyond the ordinary rule already stated above (two impls of the
same aspect conflict when some instantiation satisfies both): a competing
bare-parameter blanket from another module can never pass the orphan check in the
first place, and a concrete impl overlapping the blanket (e.g. a type implementing
`Clone` directly while also being `Copy`) is caught by the existing concrete-vs-blanket
overlap rule with no special case. See
`public/rfcs/4-implemented/rfc-0097-orphan-rule-for-bare-parameter-blanket-impls.md`.

**Worked example — interaction with equality-constrained bounds.** A conditional
`extend` block's `where` clause accepts the same equality-constrained bound form
Associated Types (above) specifies for ordinary function bounds, since both are stored
and checked as the same `Bound` structure:

```metel
aspect Container { type Item: Display; fun get(self) -> Item; }

struct Wrapper<T> { inner: T }

extend<T: Container<Item = i64>> Wrapper<T>: Printable {
    fun print(self) { println(self.inner.get().to_string()); }
}
```

This composes without any new mechanism: the conditional block's bound-checking (this
section) and the equality-constraint-checking Associated Types already specifies are
the same call-site check, run once per bound in the `where` clause, regardless of
which kind of aspect the bound names.

<details open>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.aspects.implementing-an-aspect.legality-1}

An inherent implementation is written `extend Type { ... }`; an aspect implementation is
written `extend Type: Aspect { ... }`, and both forms may coexist for the same type.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

</details>

### Aspect Implementation Coherence

Every `(aspect, type)` pair has at most one implementation visible to the program, independent of module load order. Two rules make this checkable without a whole-program scan.

**Orphan rule.** `extend Type: Aspect` is permitted only when at least one of `Aspect`
or `Type`'s outermost type constructor is declared in the same module as the extend
block. Built-in aspects and built-in types count as local to `std::core`.

```metel
extend MyStruct: Display { ... }  // ok: MyStruct is local
extend i64: MyAspect { ... }      // ok: MyAspect is local
extend i64: Display { ... }       // ok only inside std::core: both are foreign elsewhere
```

A violating `extend` block is `T0014 — orphan implementation`. The orphan rule is what
keeps coherence a local, per-module property: a module can only add aspect
implementations it owns at least one half of, so no other module's impls need to be
consulted to know whether a given one is even legal.

**Overlap detection.** Two `extend` blocks of the same aspect conflict when some
concrete type instantiation would satisfy both. `extend List<i64>: Display` and
`extend List<String>: Display` don't conflict — disjoint element types — but
registering either one twice does. A conflict is `T0015 — conflicting implementation`,
reported at both impl spans. Combined with the orphan rule, an overlap can only arise
within a single module or between a module and `std::core`, so this check is local too.

**Closed-world assumption.** The set of impls in a program is fixed at compile time — nothing visible at compilation can add an impl later. This is what makes Negative Bounds, below, dischargeable from absence alone: `T: !Aspect` holds whenever no impl, concrete or blanket, applies to `T`, without requiring an explicit negative impl for every excluded type. A blanket `impl<T: Foo> Bar for T` is expanded when checking applicability — `T: !Bar` is provable only once no applicable blanket covers `T` either.

**Auto-impl aspects.** Auto-impls are a separate mechanism from this coherence
section. For coherence purposes, an auto-impl is treated as an ordinary
positive impl generated by the compiler: overlap detection and negative-impl override
both apply to it the same way they apply to an explicit `extend` block, while the
orphan rule does not apply because there is no authored impl site.

**Negative impl priority.** See Negative Impls, below, for the mechanism itself; the priority order coherence establishes is: an explicit negative impl beats an auto-impl or blanket positive impl for the same type, but an explicit positive impl and an explicit negative impl for the same concrete type is itself a `T0015` coherence error, not a priority question.

**What this deliberately doesn't cover.** Coherence here is scoped to a single program's module graph — a future package system, compiling packages separately, needs its own cross-package coherence model, not addressed here. Rejected alternatives (a global overlap check without the orphan rule, last-impl-wins ordering, an open-world assumption, specialisation) are recorded in the RFC, not repeated here — each fails a property this design keeps: coherence errors are local and order-independent, and overlapping impls are always illegal rather than resolved by specificity.

### Structural Aspect Bounds

Arrays (`T[]`), tuples (`(A, B)`, …), and function types (`(A) -> B`) are
**structural types** — built into the language rather than declared by a user, with no
name that can serve as an impl target the ordinary way. For the orphan rule (above),
structural type constructors are treated as belonging to `std::core`: a user module
may write `extend T[]: Aspect` only when `Aspect` itself is local to that module.

**Blanket impls for structural constructors.** `std::core` declares aspect impls for
structural constructors using the conditional `extend` syntax (above):

```metel
// std::core
extend<T: Display> T[]: Display {
    fun to_string(self: &T[]) -> String { ... }
}
```

This is what makes `println([1, 2, 3])` compile: `[1, 2, 3]` has type `i64[]`;
`i64: Display`; the conditional extend block applies. Coherence for structural impl
targets follows the same rules as any other conditional block (above) — two impls of
the same aspect for `T[]` conflict (`T0015`) unless one directly negates a bound the
other requires.

**Without a matching impl**, a structural type fails an aspect bound with a diagnostic naming the constructor:

```
T0012: i64[] does not implement Display
       hint: arrays implement Display only when their element type does;
             no extend<T: Display> T[]: Display is registered
```

**Standard array impls.** `std::core` provides `Display`, `Clone`, and `Eq` for
arrays, each conditional on the element type satisfying the same bound (element-wise
`to_string`/join, element-wise clone into new backing storage, and element-wise
equality respectively). These cannot be overridden by user code (orphan rule).
`List<T>` is a separate nominal struct; its impls coexist independently of the array
impls. `Ord` (RFC-0062, still `0-draft`) and `Hash` (not yet proposed) array impls are
not provided in this language version — neither aspect exists in `std::core` at all yet,
for arrays or otherwise.

> **Since v0.12.0 (RFC-0126): `T[]`'s `Clone` impl is replaced, not just
> reconditioned.** Once `T[]` owns nothing, "element-wise clone into new backing storage" is
> not just unconditional on the element type — it is impossible to implement as `T[]: Clone`
> at all: `Clone::clone(&self) -> Self` must produce a `T[]`, and a `T[]` can only ever borrow
> from something that already exists and outlives it, never from a buffer the impl just
> allocated for itself. `Display` and `Eq` are unaffected — they return `String`/`boolean`,
> not `Self`.

**Tuples** are deferred pending a decision on per-arity boilerplate vs. variadic generics — until then, tuples fail aspect bounds the same way arrays do without a matching impl (`(i64, String)` does not implement `Display`, with a hint to use a named struct instead).

**Function types.** A plain function and a closure share one type, `(A) -> B` (see [Functions — First-Class Functions](functions.md#first-class-functions)) — there is no separate `fun(A) -> B` function-pointer type or syntax; `fun(A) -> B` is a parse error. `Callable<A, B>` does not exist in `std::core` yet — despite being referenced elsewhere as the aspect a function type would formally satisfy, writing a bound or `impl Callable<A, B>` against it is a compile error (`T0003`, unknown aspect) today. A `(A) -> B` value behaves like `Copy` under `--move-check` (reusing one after copying it into another binding is accepted), but there is no working `Clone`: `.clone()` on a `(A) -> B` receiver fails to typecheck (`T0002`, cannot infer receiver type) regardless of annotation. `Display`, `Eq`, `Ord`, `Hash`, `Send`, `Sync`, and `Drop` are not implemented for function types either — there is no canonical string form, function equality is undecidable in general, `Send`/`Sync` aren't implemented for any type yet (RFC-0080, still `1-under-review`), and there is no state to drop.

**Array auto-impl propagation.** `T[]: Send`, `T[]: Sync`, and `T[]: Drop` are not
provided in this language version.

### Associated Types

An aspect may declare an **associated type** — a type-level output that each
implementing type must specify — with `type Name;`. An `extend` block defines it with
`type Name = ConcreteType;`:

```metel
aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;
}

struct Boxed { value: i64 }

extend Boxed: Deref {
    type Target = i64;
    fun deref(self: &Boxed) -> &i64 { &self.value }
}
```

Inside the aspect block, the bare name (`Target`) is sugar for `Self::Target`. A bound
may be declared on the associated type, constraining every impl:

```metel
aspect Collection {
    type Item: Display;
}
```

**Projection.** In a generic context where `T: Aspect`, the associated type is written
`T::AssocType`:

```metel
fun deref_display<T: Deref>(x: &T) where T::Target: Display {
    println(x.deref());
}
```

`T::AssocType` is only valid when `T: Aspect` is in scope — writing it without that
bound is a compile error.

**Equality constraints in bounds.** `Aspect<AssocType = ConcreteType>` asserts both that
`T` implements `Aspect` and that its associated type equals a known type, pinning
`T::AssocType` to `ConcreteType` at every use:

```metel
fun deref_to_i64<T: Deref<Target = i64>>(x: &T) -> &i64 {
    x.deref()
}
```

`ConcreteType` doesn't have to be a fixed, known type — it can be a fresh type
parameter instead, which is also how disambiguation works (below).

**Disambiguation.** When `T` is bound to two or more aspects that each declare an
associated type of the same name, the bare projection is ambiguous — a hard error,
matching the existing method-name-collision rule (Static Dispatch Only, below):

```metel
aspect Deref { type Target; fun deref(self: &Self) -> &Target; }
aspect Convert { type Target; fun convert(self: &Self) -> Target; }

fun f<T: Deref + Convert>(x: &T) -> T::Target { ... }
// error: T::Target is ambiguous — both Deref and Convert declare Target
```

There's no dedicated disambiguation syntax for this — the equality constraint above
already covers it, by binding the associated type to a **fresh type parameter** rather
than a concrete one:

```metel
fun f<T: Deref<Target = U> + Convert, U>(x: &T) -> U {
    x.deref()   // ordinary method dispatch — deref and convert are different
                // method names, so this was never ambiguous to begin with
}
```

`U` is used unambiguously everywhere afterward — return type, `where` clauses, `let`
bindings — with no projection syntax involved. In practice this covers the real cases:
code reaches an associated type by calling the aspect's own uniquely-named method, and
the bare-projection ambiguity only arises when a type needs naming abstractly without
going through a call, which the fresh-variable equality constraint already handles.

**Associated type vs. a type parameter on the aspect.** Use an associated type when the
implementing type determines exactly one output (`Deref::Target` — a type has one deref
target). Use a type parameter on the aspect itself when a type may implement it for
multiple type arguments simultaneously (e.g. `From<i64>` and `From<String>` on the same
type). Writing `extend X: Deref<i64> {}` and `extend X: Deref<String> {}` side by side
would be the wrong model for `Deref` specifically — one type has one dereference target,
not several.

**Object safety.** An aspect with associated types is object-safe only if no method
signature references the associated type directly (see Static Dispatch Only, below, and
`dyn Aspect`, deferred to a future release). `Deref` above is *not* object-safe — `deref`
returns `&Target`, which varies per implementor, and a vtable entry cannot encode a
type that differs per implementation.

Negative bounds on projections such as `where T::Target: !Copy` are not specified in
this language version.

### Default Methods

> **Availability:** Since v0.7.0.

An aspect method may supply a default body. An `extend` block may omit any method that
has a default; the aspect's implementation is inherited automatically.

```metel
aspect Greet {
    fun name(self) -> String;

    fun greet(self) -> String {
        return "Hello, " + self.name();
    }
}

struct Person {
    name: String,
}

extend Person: Greet {
    fun name(self) -> String {
        return self.name;
    }
    // greet() is inherited from the aspect default
}

fun main() {
    let p = Person { name = "Ada" };
    println(p.greet());   // Hello, Ada
}
```

A method without a default body must be provided by every `extend` block; omitting it
is a compile-time error.

### The Self Type

`Self` inside an aspect or an `extend` block refers to the concrete implementing type.

In an aspect definition, `Self` is the implementing type at the call site:

```metel
aspect Comparable {
    fun compare(self, other: Self) -> i64;
}
```

In a struct or enum `extend` block, `Self` is an alias for the type being implemented:

> **Availability:** Since v0.7.0.

```metel
struct Point {
    x: i64,
}

extend Point {
    fun clone(self) -> Self {
        self
    }

    fun same_as(self, other: Self) -> boolean {
        self.x == other.x
    }
}
```

### Aspect Bounds on Function Type Parameters

> **Availability:** Since v0.7.0.

A generic function type parameter may declare an aspect bound using `:` syntax. The bound requires that any concrete type substituted for the parameter implements the named aspect. The named aspect must resolve where the declaration is written; an unknown aspect is error `T0003`, even when the generic function is never called. Passing a type that does not satisfy a resolved bound is error `T0012`, with the span on the offending call-site argument.

```metel
fun print_pair<T: Printable>(a: T, b: T) {
    a.print();
    b.print();
}
```

Inside the function body the typechecker treats `T` as having all methods declared by its bound aspects in scope. Calling a method not declared by any bound aspect on a bounded type parameter is a type error.

**Multiple bounds — inline `+` or `where` clause (equivalent).** Multiple bounds on a single type parameter may be expressed inline using `+`, or via a `where` clause, or a mix of both. The typechecker merges all declared bounds before enforcement — a type argument must satisfy every bound.

```metel
// Inline +
fun process<T: Comparable + Printable>(x: T) { ... }

// where clause (equivalent)
fun process<T>(x: T) where T: Comparable + Printable { ... }

// Mix — inline single bound plus additional where clause bound (also valid)
fun process<T: Comparable>(x: T) where T: Printable { ... }
```

All three forms above have identical semantics. The recommended style is inline `+` for short bound lists and `where` clause for longer or multi-parameter constraints.

**`impl Aspect` shorthand.** For type parameters used only once in a signature and not referenced elsewhere, the anonymous shorthand `impl Aspect` may be used directly in parameter position:

```metel
fun print_all(items: impl Printable[]) { ... }
// equivalent to:
fun print_all<_T: Printable>(items: _T[]) { ... }
```

Each `impl Aspect` occurrence in a signature is a **fresh, independent** type variable. To constrain two parameters to the same type, use a named type parameter.

**Return-position `impl Aspect`.** A function may return `impl Aspect` instead of a named type. The caller sees an opaque type known only to satisfy `Aspect` — no boxing, no heap allocation, no vtable, since the concrete type is fixed by the function's own body:

```metel
aspect Printable {
    fun print(self);
}

struct Adder { n: i64 }

extend Adder: Printable {
    fun print(self) {
        println("adds ${self.n}");
    }
}

fun make_adder(n: i64) -> impl Printable {
    Adder { n = n }
}

let add5 = make_adder(5);
add5.print();   // adds 5 — printable, but its concrete type is not nameable
```

A function returning `impl Aspect` must produce the **same concrete type on every code path** — the compiler resolves one fixed type per function definition, not per call:

<!-- doc-example: expect-fail reason="branches return different concrete types -- the whole point" -->
```metel
fun bad(flag: boolean) -> impl Display {
    if (flag) { 42 } else { "hello" }   // error: branches return different concrete types
}
```

Two calls to the same function return values of the same opaque type; two *different* `impl Aspect`-returning functions never share an opaque type even if their concrete implementations coincide. Each occurrence of `impl Aspect` in a signature is independent (as in parameter position, above) — a function with both an `impl Aspect` parameter and return type may return the parameter directly, in which case ordinary type inference unifies the two independent type variables:

```metel
fun transform(x: impl Display) -> impl Display {
    x   // return type inferred to be the same concrete type as x's
}
```

The caller may call any method the declared aspect provides, store the value, and pass it to anything accepting the same opaque type or aspect bound — but may not name the concrete type, cast it, or call methods outside the aspect even if the concrete type has them. Ownership (ownership/`Copy`/`Drop`, not yet integrated — RFC-0071) applies to the concrete type normally; the caller cannot observe which impls it has beyond the declared aspect bound.

**Worked example — interaction with associated types.** A function may return `impl Aspect` where `Aspect` declares an associated type; the caller can still use the aspect's own methods to produce values of that associated type, and those values type-check normally, even though the caller cannot name the opaque type itself:

```metel
aspect Container { type Item: Display; fun get(self) -> Item; }
struct IntBox { value: i64 }
extend IntBox: Container { type Item = i64; fun get(self) -> i64 { self.value } }

fun make_box(n: i64) -> impl Container {
    IntBox { value = n }
}

let v: i64 = make_box(42).get();   // resolves through Container's Item binding for
                                    // IntBox, the same associated-type mechanism
                                    // Associated Types (above) specifies -- the
                                    // caller never names IntBox, only Container.
```

This composes for free: the opaque return type is a real concrete type internally (erased only from the caller's *naming* surface, not from the typechecker's own bookkeeping), so associated-type resolution runs exactly as it does for a named type.

`impl Aspect` in struct fields, aspect aliases, named linkage between an `impl Aspect`
parameter and return type, and multiple aspect bounds in return position are not part
of this language version.

---

### Negative Bounds

`T: !Aspect` is the complement of `T: Aspect`: it asserts that `T` does **not**
implement the named aspect. `!` binds tightly to the aspect name — `T: !Drop + Clone`
reads as `T: (!Drop) + Clone` — and positive and negative bounds may mix freely, inline
or in a `where` clause, on the same terms as ordinary bounds above.

```metel
fun move_out<T: !Drop, A: Alloc>(@a: A, ptr: @a T) -> T { ... }
```

**Satisfaction.** For a concrete type, `T: !Aspect` is satisfied exactly when no
implementation of `Aspect` for `T` is reachable — the same lookup used for a positive
bound, inverted. In a generic context, absence of a bound does not imply satisfaction:
a function requiring `T: !Drop` must declare it, since the type parameter could still be
instantiated with a `Drop`-implementing type otherwise.

**`Copy` implies `!Drop`.** Since `Copy` and `Drop` are mutually exclusive (see
Ownership, not yet integrated — RFC-0071), any type satisfying `T: Copy` automatically
satisfies `T: !Drop`, derived without an explicit declaration.

**Compound types.** `T: !Drop` is a claim about `T` itself, not its fields — a struct
with `Drop`-implementing fields but no `impl Drop` of its own satisfies `!Drop`; its
fields still drop normally through the ordinary per-field chain.

> Negative bounds do not by themselves let a type opt out of an aspect an existing
> blanket impl would otherwise grant — that's Negative Impls, directly below. Negative
> bounds are a use-site constraint; negative impls are a definition-site declaration
> that affects what the negative-bound check finds. See Aspect Implementation
> Coherence, above, for exactly which impls are reachable in the first place.

### Negative Impls

A library author declares that a type **definitively** does not implement an aspect
with `extend Type: !Aspect;` — body always empty, since a negative impl is a
declaration of non-implementation, not a definition of behavior:

```metel
extend<T, brand 'b> Rc<T, 'b>: !Send;
extend<T, brand 'b> Rc<T, 'b>: !Sync;
```

More generally, a bodyless `extend` block is permitted whenever the body would be empty
already (RFC-0102):

```metel
aspect Copy2;

struct Handle { id: i64 }

extend Handle: Copy2;
extend Handle: !Send;
extend Handle: Copy2, !Send;
```

A methodless aspect declaration may itself be written bodylessly as `aspect Name;`
(RFC-0103), as in the `Copy2` example above.

`extend Type: Aspect;` is valid only when every method of `Aspect` already has a
default body and the aspect declares no associated types. `extend Type: !Aspect;` is
always valid, and the braced negative form is retired in favor of the bodyless one.

**Why this needs its own mechanism, not just the absence of a positive impl.** A
blanket impl can inadvertently grant an aspect to a type that must not have it — `Rc<T>`
would satisfy an auto-derived `Send` blanket (its field is an ordinary, `Send`-by-value
integer) even though sharing it across fibers is unsound. A negative impl overrides any
blanket that would otherwise apply: `Rc<T>: !Send` holds for all `T`, regardless of what
a blanket impl elsewhere says.

**Finality.** No positive impl may coexist with a negative impl for the same type and
aspect — a concrete `extend Type: Aspect` alongside `extend Type: !Aspect` is a
coherence error. A negative impl overriding a *blanket* positive impl is the intended,
allowed case; a negative impl does not propagate to subtypes or supertypes (`extend
Rc<T>: !Send` says nothing about `Arc<T>`).

**Orphan rules apply the same way as positive impls** (Aspect Implementation Coherence,
above) — a negative impl is permitted only when the aspect or the type is local to
the current module or stdlib. A positive and a negative impl for the same concrete
type is `T0015`, the same coherence error two conflicting positive impls produce.

---

### Aspect Bounds on Struct and Enum Type Parameters

> **Availability:** Since v0.7.0.

A struct or enum generic type parameter may declare an aspect bound. The bound is enforced at **construction time**: instantiating the type with a concrete type argument that does not implement the bound is error `T0012`, with the span on the offending type argument at the construction call site.

```metel
struct SortedList<T: Comparable> {
    items: T[],
}

// error[T0012]: NonComparable does not implement Comparable
let list = SortedList<NonComparable> { items = [] }
```

The same inline `+` and `where` clause forms apply, with identical semantics:

```metel
// Multiple inline bounds
struct Window<T: Comparable + Printable> { items: T[] }

// where clause (equivalent)
struct Cache<K, V> where K: Hashable + Comparable { entries: Pair<K, V>[] }
```

**Bound propagation.** A struct's bounds are automatically available — without re-declaration — in:

- `extend` blocks on the same struct: `extend SortedList<T>` has `T: Comparable` in scope
- `extend Struct<T>: AspectName` blocks: the struct's bounds are inherited
- Match arm bodies when matching a value of the bounded struct or enum type

The bound is an invariant of the type, not of the binding site. It propagates wherever a value of that type is used. See Conditional Impl Blocks, above, for how this interacts with an aspect impl's own additional bounds.

---

### Static Dispatch Only

All aspect dispatch in Metel is **static** (monomorphised at compile time). There are no vtables, no heap allocation, and no runtime type erasure for aspects.

Method resolution must also be **unambiguous** at compile time. If the same receiver
type implements two different aspects that both define the same method name, a call
like `value.method()` is rejected with `T0013` rather than resolved by declaration order.

`dyn Aspect` (runtime-dispatched existential types with vtable-based dispatch) is not
part of this language version. All polymorphism goes through generic type parameters
with aspect bounds.

Aspect objects (`dyn Aspect`) are not part of the language. All polymorphism is via generics (static dispatch).
