# Declarations

`pub` may be prefixed to any top-level `fun`, `struct`, `enum`, `aspect`, or `let`
declaration to mark it as accessible from other modules. See
[Modules — Visibility](modules.md#visibility) for the full rules, including `pub let`
(module-level exported values).

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
- `&mut x` is rejected (taking a mutable pointer to an immutable binding)

All three forms require `let mut`.

### Mutable Bindings

```metel
fun main() -> i64 {
    let mut counter = 0;
    counter = counter + 1;
    counter += 1;
    return counter;
}
```

`let mut` bindings can be reassigned and also must be initialized at declaration. Compound assignment operators `+=`, `-=`, `*=`, `/=`, `%=` are supported.

### Scoping and Shadowing

Variables are lexically scoped. Each block `{ }` introduces a new scope. Inner scopes can shadow outer variables.

`let` and `let mut` declarations are sequential — a binding is visible only from its declaration point to the end of its containing block.

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
    return Point { x: 1.0, y: 2.0 };   // OK — Point is globally visible
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
    let p = LocalPoint { x: 1.0, y: 2.0 };
}

fun main() -> i64 {
    inner();
    let p = make_point();
    return p.x as i64;
}
```

Top-level `impl` blocks follow the same declaration-order rule as the types they extend.

---

## Structs

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p = Point { x: 1.0, y: 2.0 };
    return p.y as i64;
}
```

### Instantiation and Field Access

```metel
struct Point {
    x: f64,
    y: f64,
}

fun main() -> i64 {
    let p = Point { x: 1.0, y: 2.0 };
    let x = p.x;
    return x as i64;
}
```

When a local variable has the same name as a field, the `: value` part can be omitted (**shorthand field init**):

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

### Methods

```metel
struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fun distance(self, other: Point) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        return dx * dx + dy * dy;   // squared distance
    }
}

fun main() -> i64 {
    let p = Point { x: 1.0, y: 2.0 };
    let q = Point { x: 4.0, y: 6.0 };
    let d = p.distance(q);
    return d as i64;
}
```

`self` refers to the receiver. Methods are called with dot syntax.

### Receiver Forms

Methods may declare one of three receiver forms:

- `self` — value receiver
- `&self` — shared reference receiver
- `&mut self` — mutable reference receiver

Value receivers follow ordinary Metel value semantics. Shared and mutable reference
receivers operate on the original receiver storage and are the right forms for
observers and in-place mutation.

```metel
struct Point {
    x: f64,
    y: f64,
}

impl Point {
    fun length(&self) -> f64 {
        self.x * self.x + self.y * self.y
    }
}
```

```metel
struct Counter {
    value: i64,
}

impl Counter {
    fun increment(&mut self) {
        self.value += 1;
    }
}
```

Calls requiring `&mut self` need a mutable addressable receiver or a `&mut T`
reference. Calls requiring `&self` may use an addressable receiver or a `&T` / `&mut T`
reference (RFC-0067a — missed when that RFC integrated `*T`/`*mut T` → `&T`/`&mut T`
elsewhere; caught while integrating this batch).

```metel
struct Counter {
    value: i64,
}

impl Counter {
    fun increment(&mut self) {
        self.value += 1;
    }
}

fun main() -> i64 {
    let mut c = Counter { value: 1 };
    c.increment();
    return c.value;
}
```

### Generic Structs

```metel
struct Pair<A, B> {
    first: A,
    second: B,
}

fun main() -> i64 {
    let p = Pair { first: 1, second: true };
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
    let s = Shape::Circle { radius: 5.0 };
    match dir {
        Direction::North => s.radius as i64,
        Direction::South => 0,
        Direction::East => 0,
        Direction::West => 0,
    }
}
```

Variants may be unit (no data) or struct-like (named fields).

### Instantiation

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

fun main() -> i64 {
    let dir = Direction::North;
    let s = Shape::Circle { radius: 5.0 };
    match dir {
        Direction::North => s.radius as i64,
        Direction::South => 0,
        Direction::East => 0,
        Direction::West => 0,
    }
}
```

### Methods on Enums

`impl` blocks on enums follow the same syntax as structs:

```metel
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}

impl Shape {
    fun area(self) -> f64 {
        match self {
            Shape::Circle { radius } => 3.14159 * radius * radius,
            Shape::Rectangle { width, height } => width * height,
        }
    }
}

fun main() -> i64 {
    let s = Shape::Circle { radius: 5.0 };
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

### Implementing a Aspect

```metel
struct Point {
    x: f64,
    y: f64,
}

aspect Printable {
    fun print(self);
}

impl Printable for Point {
    fun print(self) {
        print("(");
        print(self.x.to_string());
        print(", ");
        print(self.y.to_string());
        println(")");
    }
}

fun main() {
    let p = Point { x: 1.0, y: 2.0 };
    p.print();
}
```

### Aspect Implementation Coherence

> **Not yet implemented** — see `internal/rfcs/3-integrated/rfc-0060-aspect-impl-coherence.md`; the interpreter currently has no orphan-rule or overlap check, so any impl is accepted regardless of where it's written.

Every `(aspect, type)` pair has at most one implementation visible to the program, independent of module load order. Two rules make this checkable without a whole-program scan.

**Orphan rule.** `impl Aspect for Type` is permitted only when at least one of `Aspect` or `Type`'s outermost type constructor is declared in the same module as the impl. Built-in aspects and built-in types count as local to `std::core`.

```metel
impl Display for MyStruct { ... }  // ok: MyStruct is local
impl MyAspect for i64 { ... }      // ok: MyAspect is local
impl Display for i64 { ... }       // ok only inside std::core: both are foreign elsewhere
```

A violating impl is `T0014 — orphan implementation`. The orphan rule is what keeps coherence a local, per-module property: a module can only add impls it owns at least one half of, so no other module's impls need to be consulted to know whether a given impl is even legal.

**Overlap detection.** Two impls of the same aspect conflict when some concrete type instantiation would satisfy both. `impl Display for List<i64>` and `impl Display for List<String>` don't conflict — disjoint element types — but registering either one twice does. A conflict is `T0015 — conflicting implementation`, reported at both impl spans. Combined with the orphan rule, an overlap can only arise within a single module or between a module and `std::core`, so this check is local too.

**Closed-world assumption.** The set of impls in a program is fixed at compile time — nothing visible at compilation can add an impl later. This is what makes Negative Bounds, below, dischargeable from absence alone: `T: !Aspect` holds whenever no impl, concrete or blanket, applies to `T`, without requiring an explicit negative impl for every excluded type. A blanket `impl<T: Foo> Bar for T` is expanded when checking applicability — `T: !Bar` is provable only once no applicable blanket covers `T` either.

**Auto-impl aspects.** A marker aspect (no methods) may be an auto-impl aspect: the compiler derives an implementation for any type whose field types (all of them, for a struct; all of them in every variant, for an enum) also implement the aspect, with no explicit `impl` required. `Send`/`Sync` are intended auto-impl aspects once `internal/rfcs/1-under-review/rfc-0080-stdlib-aspects.md` (currently under review, not yet accepted) settles — an auto-impl is an ordinary positive impl for coherence purposes: overlap detection and negative-impl override both apply to it the same as an explicit one. The surface syntax an aspect declaration uses to opt into auto-impl is deferred to the derive-registration mechanism (RFC-0093, draft).

**Negative impl priority.** See Negative Impls, below, for the mechanism itself; the priority order coherence establishes is: an explicit negative impl beats an auto-impl or blanket positive impl for the same type, but an explicit positive impl and an explicit negative impl for the same concrete type is itself a `T0015` coherence error, not a priority question.

**What this deliberately doesn't cover.** Coherence here is scoped to a single program's module graph — a future package system, compiling packages separately, needs its own cross-package coherence model, not addressed here. Rejected alternatives (a global overlap check without the orphan rule, last-impl-wins ordering, an open-world assumption, specialisation) are recorded in the RFC, not repeated here — each fails a property this design keeps: coherence errors are local and order-independent, and overlapping impls are always illegal rather than resolved by specificity.

### Associated Types

An aspect may declare an **associated type** — a type-level output that each
implementing type must specify — with `type Name;`. An impl block defines it with
`type Name = ConcreteType;`:

```metel
aspect Deref {
    type Target;
    fun deref(self: &Self) -> &Target;
}

struct Boxed { value: i64 }

impl Deref for Boxed {
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
type). Writing `impl Deref<i64> for X {}` and `impl Deref<String> for X {}` side by side
would be the wrong model for `Deref` specifically — one type has one dereference target,
not several.

**Object safety.** An aspect with associated types is object-safe only if no method
signature references the associated type directly (see Static Dispatch Only, below, and
`dyn Aspect`, deferred to a future release). `Deref` above is *not* object-safe — `deref`
returns `&Target`, which varies per implementor, and a vtable entry cannot encode a
type that differs per implementation.

> **Not yet decided:** whether a negative bound on a projection (`where T::Target:
> !Copy`) is meaningful — neither this RFC nor RFC-0072 addresses bounds on projections
> specifically, only on bare type parameters. (Disambiguation, above, was resolved
> 2026-07-10 — the "type inference RFC" it was deferred to doesn't exist; type
> inference is already implemented and this didn't depend on it.)

### Default Methods

> *Since v0.7.0.*

An aspect method may supply a default body. An `impl` block may omit any method that has a default; the aspect's implementation is inherited automatically.

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

impl Greet for Person {
    fun name(self) -> String {
        return self.name;
    }
    // greet() is inherited from the aspect default
}

fun main() {
    let p = Person { name: "Ada" };
    println(p.greet());   // Hello, Ada
}
```

A method without a default body must be provided by every `impl` block; omitting it is a compile-time error.

### The Self Type

`Self` inside an aspect or an `impl` block refers to the concrete implementing type.

In an aspect definition, `Self` is the implementing type at the call site:

```metel
aspect Comparable {
    fun compare(self, other: Self) -> i64;
}
```

In a struct or enum `impl` block, `Self` is an alias for the type being implemented:

> *Since v0.7.0.*

```metel
struct Point {
    x: i64,
}

impl Point {
    fun clone(self) -> Self {
        self
    }

    fun same_as(self, other: Self) -> boolean {
        self.x == other.x
    }
}
```

### Aspect Bounds on Function Type Parameters

> *Since v0.7.0. Specified by RFC-0002, RFC-0034, RFC-0035, and RFC-0040.*

A generic function type parameter may declare an aspect bound using `:` syntax. The bound requires that any concrete type substituted for the parameter implements the named aspect. Passing a type that does not satisfy the bound is error `T0012`, with the span on the offending call-site argument.

```metel
fun print_pair<T: Printable>(a: T, b: T) {
    a.print();
    b.print();
}
```

Inside the function body the typechecker treats `T` as having all methods declared by its bound aspects in scope. Calling a method not declared by any bound aspect on a bounded type parameter is a type error.

**Multiple bounds — inline `+` or `where` clause (equivalent).** Multiple bounds on a single type parameter may be expressed inline using `+`, or via a `where` clause, or a mix of both. The typechecker merges all declared bounds before enforcement — a type argument must satisfy every bound.

```metel
// Inline + (since v0.7.0; RFC-0034)
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

> **Not yet implemented (deferred):**
> - `impl Aspect` in return position (`fun foo() -> impl Display`) — RFC-0037
> - `impl Aspect` in struct fields (`dyn Aspect`) — RFC-0038
> - `aspect` alias syntax (`aspect Sortable = Comparable + Display + Clone`) — RFC-0039
> - Conditional impls (`impl Aspect for S<T> where T: OtherAspect`) — RFC-0036

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
with `impl !Aspect for Type {}` — body always empty, since a negative impl is a
declaration of non-implementation, not a definition of behavior:

```metel
impl<T, brand 'b> !Send for Rc<T, 'b> {}
impl<T, brand 'b> !Sync for Rc<T, 'b> {}
```

**Why this needs its own mechanism, not just the absence of a positive impl.** A
blanket impl can inadvertently grant an aspect to a type that must not have it — `Rc<T>`
would satisfy an auto-derived `Send` blanket (its field is an ordinary, `Send`-by-value
integer) even though sharing it across fibers is unsound. A negative impl overrides any
blanket that would otherwise apply: `Rc<T>: !Send` holds for all `T`, regardless of what
a blanket impl elsewhere says.

**Finality.** No positive impl may coexist with a negative impl for the same type and
aspect — a concrete `impl Aspect for Type` alongside `impl !Aspect for Type` is a
coherence error. A negative impl overriding a *blanket* positive impl is the intended,
allowed case; a negative impl does not propagate to subtypes or supertypes (`impl !Send
for Rc<T>` says nothing about `Arc<T>`).

**Orphan rules apply the same way as positive impls** (Aspect Implementation Coherence,
above) — a negative impl is permitted only when the aspect or the type is local to
the current module or stdlib. A positive and a negative impl for the same concrete
type is `T0015`, the same coherence error two conflicting positive impls produce.

---

### Aspect Bounds on Struct and Enum Type Parameters

> *Since v0.7.0. Specified by RFC-0034.*

A struct or enum generic type parameter may declare an aspect bound. The bound is enforced at **construction time**: instantiating the type with a concrete type argument that does not implement the bound is error `T0012`, with the span on the offending type argument at the construction call site.

```metel
struct SortedList<T: Comparable> {
    items: T[],
}

// error[T0012]: NonComparable does not implement Comparable
let list = SortedList<NonComparable> { items: [] }
```

The same inline `+` and `where` clause forms apply, with identical semantics:

```metel
// Multiple inline bounds
struct Window<T: Comparable + Printable> { items: T[] }

// where clause (equivalent)
struct Cache<K, V> where K: Hashable + Comparable { entries: Pair<K, V>[] }
```

**Bound propagation.** A struct's bounds are automatically available — without re-declaration — in:

- `impl` blocks on the same struct: `impl SortedList<T>` has `T: Comparable` in scope
- `impl AspectName for Struct<T>` blocks: the struct's bounds are inherited
- Match arm bodies when matching a value of the bounded struct or enum type

The bound is an invariant of the type, not of the binding site. It propagates wherever a value of that type is used.

> **Not yet implemented (deferred):**
> - Conditional impls (`impl Aspect for S<T> where T: OtherAspect`) — RFC-0036

---

### Static Dispatch Only

All aspect dispatch in Metel is **static** (monomorphised at compile time). There are no vtables, no heap allocation, and no runtime type erasure for aspects.

Method resolution must also be **unambiguous** at compile time. If the same receiver
type implements two different aspects that both define the same method name, a call
like `value.method()` is rejected with `T0013` rather than resolved by declaration order.

`dyn Aspect` (runtime-dispatched existential types with vtable-based dispatch) is **not part of the language** in this version. Dynamic dispatch is specified by RFC-0038 and will be introduced in a future release. Until then, all polymorphism must go through generic type parameters with aspect bounds.

Aspect objects (`dyn Aspect`) are not part of the language. All polymorphism is via generics (static dispatch).
