# Declarations

`pub` may be prefixed to any top-level `fun`, `struct`, `enum`, or `aspect` declaration to mark it as accessible from other modules. See [Modules — Visibility](modules.md#visibility) for the full rules.

## Variables

### Immutable Bindings

```metel
fun main() -> Int {
    let x = 42;
    let name: String = "Vlad";
    if (name == "Vlad") { return x; }
    return 0;
}
```

`let` bindings cannot be reassigned and must always be initialized.

### Mutable Bindings

```metel
fun main() -> Int {
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
fun is_even(n: Int) -> Bool {
    if (n == 0) { return true; }
    return is_odd(n - 1);
}

fun is_odd(n: Int) -> Bool {
    if (n == 0) { return false; }
    return is_even(n - 1);
}

fun outer() -> Int {
    inner();

    fun inner() {
        helper();
        fun helper() { }
    }

    return 1;
}

fun main() -> Int {
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
    x: Float,
    y: Float,
}

fun inner() {
    struct LocalPoint {
        x: Float,
        y: Float,
    }
    let p = LocalPoint { x: 1.0, y: 2.0 };
}

fun main() -> Int {
    inner();
    let p = make_point();
    return p.x as Int;
}
```

Top-level `impl` blocks follow the same declaration-order rule as the types they extend.

---

## Structs

```metel
struct Point {
    x: Float,
    y: Float,
}

fun main() -> Int {
    let p = Point { x: 1.0, y: 2.0 };
    return p.y as Int;
}
```

### Instantiation and Field Access

```metel
struct Point {
    x: Float,
    y: Float,
}

fun main() -> Int {
    let p = Point { x: 1.0, y: 2.0 };
    let x = p.x;
    return x as Int;
}
```

When a local variable has the same name as a field, the `: value` part can be omitted (**shorthand field init**):

```metel
struct Point {
    x: Float,
    y: Float,
}

fun main() -> Int {
    let x = 1.0;
    let y = 2.0;
    let p = Point { x, y };
    return p.x as Int;
}
```

Shorthand and explicit fields may be mixed freely within one literal.

### Methods

```metel
struct Point {
    x: Float,
    y: Float,
}

impl Point {
    fun distance(self, other: Point) -> Float {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        return dx * dx + dy * dy;   // squared distance
    }
}

fun main() -> Int {
    let p = Point { x: 1.0, y: 2.0 };
    let q = Point { x: 4.0, y: 6.0 };
    let d = p.distance(q);
    return d as Int;
}
```

`self` refers to the receiver. Methods are called with dot syntax.

### Mutable Receiver

> **Availability:** Since v0.1.0.

Methods that mutate the receiver declare `mut self`.

`mut self` gives the method a mutable local receiver value, but method calls do not
update the caller's binding in place.

```metel
struct Counter {
    value: Int,
}

impl Counter {
    fun increment(mut self) {
        self.value += 1;
    }
}

fun main() -> Int {
    let c = Counter { value: 1 };
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

fun main() -> Int {
    let p = Pair { first: 1, second: true };
    return p.first;
}
```

---

## Enums

```metel
enum Direction { North, South, East, West }

enum Shape {
    Circle { radius: Float },
    Rectangle { width: Float, height: Float },
}

fun main() -> Int {
    let dir = Direction::North;
    let s = Shape::Circle { radius: 5.0 };
    match dir {
        Direction::North => s.radius as Int,
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
    Circle { radius: Float },
    Rectangle { width: Float, height: Float },
}

fun main() -> Int {
    let dir = Direction::North;
    let s = Shape::Circle { radius: 5.0 };
    match dir {
        Direction::North => s.radius as Int,
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
    Circle { radius: Float },
    Rectangle { width: Float, height: Float },
}

impl Shape {
    fun area(self) -> Float {
        match self {
            Shape::Circle { radius } => 3.14159 * radius * radius,
            Shape::Rectangle { width, height } => width * height,
        }
    }
}

fun main() -> Int {
    let s = Shape::Circle { radius: 5.0 };
    return s.area() as Int;
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
    fun compare(self, other: Self) -> Int;
}

fun main() -> Int {
    return 0;
}
```

### Implementing a Aspect

```metel
struct Point {
    x: Float,
    y: Float,
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
    fun compare(self, other: Self) -> Int;
}
```

In a struct or enum `impl` block, `Self` is an alias for the type being implemented:

> *Since v0.7.0.*

```metel
struct Point {
    x: Int,
}

impl Point {
    fun clone(self) -> Self {
        self
    }

    fun same_as(self, other: Self) -> Bool {
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

`dyn Aspect` (runtime-dispatched existential types with vtable-based dispatch) is **not part of the language** in this version. Dynamic dispatch is specified by RFC-0038 and will be introduced in a future release. Until then, all polymorphism must go through generic type parameters with aspect bounds.

Aspect objects (`dyn Aspect`) are not part of the language. All polymorphism is via generics (static dispatch).
