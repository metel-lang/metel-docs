# Regions and Lifetimes by Example — Proposed Syntax

**Date:** 2026-06-13  
**Status:** Exploratory — **paused branch**  
**Related RFCs:** RFC-0028, RFC-0025, RFC-0056, RFC-0052, RFC-0051, RFC-0043  

> **⏸ Paused branch (2026-06-13).** This report illustrates the region/lifetime design, which is **on hold** pending a memory-strategy reconsideration: its runtime model is essentially `bumpalo` and its differentiator is a softened reimplementation of Rust's lifetimes. It is retained as the worked record of the evaluated "Rust-shaped" branch. For the current direction, see `memory-strategy-research-directions.md`.

---

## Purpose

This report shows what Metel programs look like under the proposed region-and-lifetime model, using the **current** syntax (RFC-0028 resolved, RFC-0025/RFC-0056 design). It is a companion to `memory-model-programs.md` Part 7, which sets out the design thesis; this report makes that thesis concrete with runnable-shaped programs.

Two things to keep in mind while reading, both from Part 7:

1. **Lifetimes are fully implemented and enforced under the hood. The annotations are optional.** Most examples below are written *without* a single `'r`. Where one appears, it is there for **precision** (to beat the conservative default), never to satisfy basic soundness.
2. **The region handle carries the lifetime.** A `Region<'r>` value is both a Zig-style allocator *and* the carrier of the compile-time lifetime `'r`. Passing the allocator and annotating the lifetime are the same act.

Part 1 solves common problems. Part 2 walks the safety gradient in one program. Part 3 shows where the model is conservative, unchecked, or simply cannot express something — its real limitations.

---

## Notation cheat sheet

| Form | Meaning |
|---|---|
| `region { ... }` | region block, nothing named; allocations inside go to its bump allocator, freed atomically at the closing brace |
| `region reg { ... }` | block binding the handle `reg: Region<'_>` (anonymous lifetime) |
| `region 'r { ... }` | block naming the lifetime `'r` (for `*'r T` annotations); no handle bound |
| `region 'r reg { ... }` | block binding `reg: Region<'r>` with a named lifetime |
| `region reg: DebugRegion { ... }` | block binding a handle with an explicit backing strategy |
| `Region::run((reg) -> { ... })` | callback form; the handle arrives as an explicit closure parameter |
| `reg.alloc(v)` | allocate `v` in `reg`'s backing block → `*'r T` |
| `*'r T` | a raw pointer into region `'r` |
| `*T`, `*mut T` | raw non-owning pointers (RFC-0043); `&x` / `&mut x` to take them |
| `@T`, `@x` | owning heap pointer (linear handle) and the box operator |
| `linear struct/enum` | a type with exactly-once consumption; no use-site sigil |
| `drop(x)` / `Drop` | linearity discard / opt-in destructor aspect |
| `RegionFree` | exit constraint: a value may leave a region block only if it holds no pointer into that region (interim approximation: `Send`) |

The rule that ties it together: a region block's value must be `RegionFree` — nothing pointing **into** the region may escape it. Everything else is ordinary code.

---

## Opening a region — block and callback forms

A region is opened in one of two interchangeable ways. Both bind a handle (when you want one) and both apply the `RegionFree` exit bound. **There is no magic `Region::handle()`** — the handle is a binding you introduce in the header, or a closure parameter.

**Block form.** The lifetime and the handle are *both optional* in the header, named only when you need them:

```metel
region { ... }                 // nothing named: implicit allocation only (common case)
region reg { ... }             // handle bound as reg: Region<'_>; lifetime anonymous
region 'r { ... }              // lifetime named (for *'r T annotations); no handle
region 'r reg { ... }          // both: reg: Region<'r>
region reg: DebugRegion { ... }// handle bound, backing strategy chosen
```

You name `'r` only when a type annotation needs to mention it; you name `reg` only when you allocate explicitly or pass the handle to a callee.

**Callback form.** The same scope as a higher-order call; the handle arrives as an explicit closure parameter:

```metel
let summary = Region::run((reg) -> {           // reg: Region<'r>
    let items = build_items(reg, n);
    compute_summary(items)                     // RegionFree result escapes
});

let report = Region::run_with(DebugRegion, (reg) -> { ... });   // strategy injection
```

Use the block for ordinary lexical scopes; use the callback when the scope is itself a value — passed to a combinator, selected at runtime, or constructed by a library. `region 'r reg { BODY }` desugars to `Region::run((reg) -> { BODY })`.

---

## Part 1 — Common problems, solved

### 1.1 Arena-allocated lexer — the bread-and-butter case

A lexer builds many short-lived token objects, then hands back a result. All scratch dies at once; nothing escapes. **No lifetime annotation, no handle, no manual free** — the bare block with implicit allocation.

```metel
struct Token { kind: TokenKind, start: Int, len: Int }

fun lex(source: String) -> List<Token> {
    region {
        // Every allocation here goes to the region's bump allocator.
        mut tokens: List<Token> = List::new();
        mut i = 0;
        while i < source.len() {
            let tok = scan_one(source, i);   // region-allocated scratch
            i = tok.start + tok.len;
            tokens = tokens.append(tok);
        }
        tokens.to_owned()   // RegionFree: a List<Token> of plain values — copied out
    }
    // all region scratch freed here
}
```

**What this shows:** the common case is annotation-free, handle-free, and free-of-`free`. The `RegionFree` exit bound is the only rule in play — `Token` is a pure value type, so the result copies out and the arena is reclaimed in one operation.

---

### 1.2 Passing the allocator — the Zig pattern, RFC-0056

When the allocating work moves into a callee, the caller binds a handle in the header and passes it down. The lifetime rides on the handle's type, so the callee is lifetime-agnostic and the caller decides where the data lives. Still no `'r` written for soundness — only as the header label.

```metel
// Allocates into whatever region it is handed. '_' = "some caller's region".
fun build_items(reg: impl Region<'_>, n: Int) -> *'_ Items {
    mut items = reg.alloc(Items::empty());
    mut i = 0;
    while i < n {
        items.push(reg.alloc(Item::new(i)));
        i += 1;
    }
    items
}

fun summarise(source: Input) -> Summary {
    region 'r reg {                            // reg: Region<'r>, bound in the header
        let items = build_items(reg, source.count);   // items: *'r Items
        compute_summary(items)                 // Summary is RegionFree — escapes
    }
}
```

**What this shows:** "pass the allocator" *is* "annotate the lifetime." `build_items` works against any region implementation (`impl Region<'_>`), and the returned pointer automatically lives in the caller's region. This is the design's center of gravity. The same body as a callback:

```metel
fun summarise(source: Input) -> Summary {
    Region::run((reg) -> { compute_summary(build_items(reg, source.count)) })
}
```

---

### 1.3 Zero-copy borrowed view — conservative elision in action

Returning a pointer that borrows from an input is the classic case where Rust forces `<'a>`. Here it is **elided**: with one borrowing input and one borrowing output, the default ties them — the return cannot outlive `input`.

```metel
// No annotation. Default: the output borrow is bounded by the input borrow.
fun first_word(input: *str) -> *str {
    match input.find(' ') {
        nope                       => input,
        Perhaps::Some { value: i } => input.slice(0, i),
    }
}

region reg {
    let line = reg.alloc("hello world");   // *'r str
    let w = first_word(line);              // *'r str — borrows from line, inferred
    println(w);                            // "hello"
}   // line and w freed together
```

**What this shows:** zero-copy slicing with no annotation and no allocation. The conservative default (`output lifetime = min(inputs)`) is exactly right when there is only one input to borrow from. The handle `reg` is bound only because we allocate explicitly.

---

### 1.4 A struct that borrows — region-parameterized, but elided

A parser that holds a pointer into the source buffer is region-parameterized *under the hood*. The `'r` parameter exists and is enforced; the programmer does not write it.

```metel
// The '<'r>' parameter is inferred from the field type — not authored.
struct Parser { input: *str, pos: Int }

fun parser_of(src: *str) -> Parser { Parser { input: src, pos: 0 } }

fun peek(p: *Parser) -> Perhaps<Char> { p.input.char_at(p.pos) }

fun parse_config(text: String) -> Config {
    region reg {
        let src = reg.alloc(text);    // *'r str
        let p = parser_of(src);       // Parser borrowing 'r — cannot escape
        run(p)                        // Config is RegionFree — escapes
    }
}
```

**What this shows:** "structs that hold a borrow" — Part 5's headline expressiveness gap in the old model — is just ordinary code now. `Parser` cannot outlive the region because the compiler tracks the inferred `'r` on its field, and the `RegionFree` bound stops it escaping. No `Parser<'r>` syntax appears.

---

### 1.5 Graph with bidirectional edges — region-safe, no cycle leak

Cyclic and back-referencing structures are the pain point on a refcounted heap. Inside a region they are trivial: every pointer dies with the arena, so cycles cannot leak.

```metel
struct GraphNode { id: Int, visited: boolean, edges: List<*mut GraphNode> }

fun connected_components(n: Int, edges: List<Edge>) -> Int {
    region reg {
        mut nodes: List<*mut GraphNode> = List::new();
        mut i = 0;
        while i < n {
            nodes = nodes.append(reg.alloc(GraphNode { id: i, visited: false, edges: List::new() }));
            i += 1;
        }
        for (let e in edges) {
            let a = nodes.get(e.from);
            let b = nodes.get(e.to);
            (*a).edges = (*a).edges.append(b);
            (*b).edges = (*b).edges.append(a);   // back-edge: a cycle — and that is fine
        }

        mut count = 0;
        for (let node in nodes) {
            if !(*node).visited { dfs(node); count += 1; }
        }
        count   // an Int — RegionFree
    }
    // every GraphNode and every edge pointer freed atomically
}
```

**What this shows:** the region makes the structure **region-safe** — the whole graph lives and dies together — which is the safety you actually want for a graph. You write plain `*mut` pointer code with no weak references, no manual cycle-breaking, and no GC. (The trade-off is in §3.4.)

---

### 1.6 Nested regions — scratch freed early, relationship for free

A long-lived result is built in an outer region while a hot loop uses an inner region for per-iteration scratch that is reclaimed each pass. The lexical nesting *is* the proof that `'outer` outlives `'inner` — no `'outer: 'inner` bound is written.

```metel
fun render_frames(scene: Scene, count: Int) -> List<Frame> {
    region 'outer out_reg {
        mut frames: List<Frame> = List::new();

        mut f = 0;
        while f < count {
            let frame = region 'inner scratch {
                let visible = cull(scene, scratch);   // *'inner — scratch only
                rasterise(visible)                    // Frame is RegionFree — leaves 'inner
            };   // all per-frame scratch freed here, every iteration
            frames = frames.append(frame);
            f += 1;
        }
        frames.to_owned()
    }
}
```

**What this shows:** lexical regions give you the lifetime *relationship* for free — the common nested case (parent outlives child) needs no annotation beyond the header labels. A `*'inner` pointer physically cannot escape into `'outer`; the compiler rejects it, and the inner arena is reclaimed every iteration so memory stays flat.

---

### 1.7 When you *do* write `'r` — precision, not soundness

The one case the conservative default over-rejects: two borrowing inputs where the output comes from one of them. The default assumes it borrows from *both* (`min` of the two), which is sound but too strict if the caller's regions differ. An explicit annotation says "the result borrows from exactly these."

```metel
// Without annotation: rejected when 'a and 'b have different extents,
// because the default forces the result to outlive neither.
fun longest<'a>(x: *'a str, y: *'a str) -> *'a str {
    if x.len() >= y.len() { x } else { y }
}
```

**What this shows:** the annotation is a *precision tool*. You reach for `'a` only to express "these share one lifetime and the result is tied to it" — a strictly more permissive claim than the safe default. This is the inversion from Rust: here the annotation unlocks programs rather than being the price of compiling at all. (Whether this syntax ships in v1 or is deferred until over-rejection bites is the open decision in Part 7 §7.8.)

---

### 1.8 Swappable region strategies

Because `Region<'r>` is an aspect, the backing allocator is chosen in the header (or the callback). Production code bumps; tests use a use-after-free–detecting region; bounded work can use a stack-backed fixed region. The allocating code is identical.

```metel
fun parse_into(reg: impl Region<'_>, src: String) -> *'_ Ast {
    reg.alloc(build_ast(src))
}

// Production: bump allocator (the default backing).
let ast = region reg { parse_into(reg, src) };

// Tests: same code, DebugRegion chosen in the header — poisons freed memory,
// traps stale reads.
fun test_parse() {
    region reg: DebugRegion {
        let ast = parse_into(reg, "1 + 2");
        assert_eq(ast.kind, AstKind::Add);
    }   // DebugRegion reports any pointer that outlived the scope
}
```

**What this shows:** the Zig "choose your allocator" discipline, with the lifetime safety Zig lacks. Swapping `BumpRegion` → `DebugRegion` changes nothing in the allocating function — only the header. (`FixedRegion<N>` is the third strategy — see §3.7 for why it is not available yet.)

---

### 1.9 A linear resource living inside a region

Regions handle batch-lifetime scratch; linear types handle resources with their own deterministic release. They compose: a linear `FileHandle` is used *inside* a region without being region-allocated — its linearity, not the region, governs its release.

```metel
linear struct FileHandle { fd: Int }

fun close(self: FileHandle) { os_close(self.fd); }   // consumes self

fun count_words(path: String) -> Int {
    region reg {
        let f = FileHandle::open(path);     // linear — NOT region-managed
        let text = f.read_all();            // consume-and-return would apply if reused
        f.close();                          // explicit release — linearity demands it
        let words = tokenise(text, reg);    // *'r scratch in the region
        words.count()                       // Int — RegionFree
    }
}
```

**What this shows:** the two systems stay in their lanes. The region frees `text` and the token scratch; the `FileHandle` must still be explicitly `close`d (or carry `Drop`) because its lifetime is a resource concern, not a scratch concern. Forgetting `f.close()` is a *linearity* error, caught independently of the region.

---

## Part 2 — The safety gradient in one program

The same task — summarise a document — written at each level of the gradient, showing what you opt into as you climb.

```metel
// LEVEL 0 — default values, refcounted. No lifetimes, no pointers. Always safe.
fun summarise_v0(doc: String) -> Summary {
    let words = doc.split(' ');        // owned List<String>, Arc-backed
    Summary { count: words.count() }
}

// LEVEL 1 — lexical region. Annotation-free; scratch freed atomically.
fun summarise_v1(doc: String) -> Summary {
    region reg {
        let toks = tokenise(doc, reg);   // *'r scratch
        Summary { count: toks.count() }  // RegionFree
    }
}

// LEVEL 2 — explicit handle across an API boundary. Optional name for precision.
fun summarise_v2(reg: impl Region<'_>, doc: String) -> *'_ Summary {
    reg.alloc(Summary { count: tokenise(doc, reg).count() })
}

// LEVEL 3 — unsafe manual region. No RegionFree, no lifetime tagging. Your problem.
fun summarise_v3(doc: String) -> Summary {
    unsafe {
        let reg = Region::new(4096);
        let toks = reg.alloc(tokenise_raw(doc));
        let s = Summary { count: toks.count() };
        reg.free();          // toks now dangles — must not be touched again
        s
    }
}
```

**What this shows:** you meet a lifetime concept only when you deliberately climb. Levels 0–1 are annotation-free; Level 2 optionally names `'r` at the boundary; Level 3 trades all guarantees for manual control behind `unsafe`. A program can mix levels freely — the only hard edge is that a `*'r T` from a region must never escape into a Level-0 refcounted value that outlives `'r`.

---

## Part 3 — Limitations

The model is deliberately not Rust. These are the places it is conservative, unchecked, or inexpressive — stated plainly so they are design inputs, not surprises.

### 3.1 Conservative over-rejection

The `min`-of-inputs default rejects some programs that are actually safe. A function that returns a borrow from *one* of two inputs is refused unless you add the precision annotation (§1.7).

```metel
// Over-rejected without annotation: the compiler assumes the result
// borrows from BOTH a and b, so it may outlive neither.
fun pick(a: *str, b: *str, which: boolean) -> *str {
    if which { a } else { b }   // ERROR under conservative default
}
```

**Cost / mitigation:** either write `<'a>` to state the real relationship, or restructure so the function returns an owned value. This is the price of total elision: soundness is free, *precision* is opt-in. If v1 ships without annotation syntax (Part 7 §7.8), the only escape is the owned-copy restructure until the syntax lands.

---

### 3.2 Aliased `*mut` is not statically checked

Lifetimes prove *no dangling*. They say nothing about *aliasing*. Metel does not run Rust's XOR-mutability borrow check, so two live `*mut` pointers to the same storage are indistinguishable to the type system.

```metel
region reg {
    let p: *mut Counter = reg.alloc(Counter { n: 0 });
    let q: *mut Counter = p;        // second mutable alias — accepted
    (*p).n = 1;
    (*q).n = 2;                     // no error; (*p).n is now 2, perhaps surprisingly
}
```

**What you get instead:** the interpreter backstop guarantees this is **never memory corruption** — the value representation is safe underneath. What you *don't* get is a guarantee against *logically* surprising mutation, iterator invalidation, or a statically-proven `split_at_mut`-style disjoint split. Algorithms that rely on certified non-overlap (parallel in-place partitioning) cannot be expressed safely; they must be serialised or split by separate allocations. (The future compiler reopens this — aliasing becomes optimization-relevant — but that is deferred.)

---

### 3.3 You cannot return data from a region you created

A function may return a `*'r T` only when `'r` was *given to it* (a passed-in handle, §1.2). A function that opens its own region block and tries to return a pointer into it is a use-after-free, and is rejected.

```metel
fun make_widget() -> *Widget {
    region reg {
        reg.alloc(Widget::new())   // ERROR: *'r escapes its region
    }
}
```

**Mitigation:** either take the destination region as a parameter (`fun make_widget(reg: impl Region<'_>) -> *'_ Widget`) — the caller owns the lifetime — or return an owned value / `@Widget` (heap, linear) instead of a region pointer. This is a rule, not an inference weakness: the region's storage is gone at the brace.

---

### 3.4 Region-safe is not edge-safe

The arena makes the *whole graph* safe to free at once (§1.5), but it does **not** validate individual references within the live region. A stale index into the node list, or a pointer to a logically-removed node, is not caught — the memory is still mapped, so it reads as live.

```metel
region reg {
    let a = reg.alloc(Node::new(0));
    let b = reg.alloc(Node::new(1));
    (*a).next = b;
    logically_remove(b);     // your bookkeeping says b is gone...
    let stale = (*a).next;   // ...but *stale still reads valid region memory
}
```

**Cost:** regions give you *spatial* safety (no dangling across the region boundary), not *logical* validity within it. For graphs where individual nodes are inserted and removed over the arena's life, you need your own generation/tombstone scheme — the region won't catch a use-after-logical-delete. This is the granularity trade you accept in exchange for cheap cyclic structures.

---

### 3.5 No cross-fiber region sharing

`Region<'r>` is single-fiber: the handle is linear and not `Send`, so it cannot be captured by `spawn { }` or sent on a channel. Two fibers allocating into one arena would race at the allocator with no synchronisation.

```metel
region reg {
    // spawn { build_items(reg, n) }   ← ERROR: Region<'r> is not Send
    let items = build_items(reg, n);   // must stay on this fiber
}
```

**Mitigation:** each fiber creates its own region block; results cross fiber boundaries as `RegionFree` values over channels. A synchronised `SharedRegion<'r>` is explicitly out of scope (RFC-0056 OQ-3). For most workloads (per-request, per-frame, per-parse arenas) the single-fiber model is the natural fit, but genuinely shared scratch is not expressible.

---

### 3.6 A single self-referential struct (not via an arena) is still hard

The arena pattern handles *graphs*. A lone struct that points at itself — without an enclosing region to own both ends — has no lifetime to anchor the inner pointer to.

```metel
// No region in sight: what owns the pointee, and how long does it live?
struct SelfRef { value: Int, me: *SelfRef }   // not expressible safely standalone
```

**Mitigation:** use `@SelfRef` (owning heap pointer, linear) for tree-shaped ownership, or put the structure in a region and reference by `*'r`. True standalone self-reference (the `Pin`/`Rc<RefCell>` territory in Rust) is intentionally not supported — it is the case even mature systems languages handle only with ceremony.

---

### 3.7 `FixedRegion<N>` needs comptime — not available yet

The stack-backed, zero-heap region strategy requires a compile-time-known size `N`, which depends on comptime (RFC-0055). Until comptime lands, only the heap-backed `BumpRegion` and `DebugRegion` strategies exist.

```metel
// Desired: no heap touch at all, N known at compile time.
region reg: FixedRegion<4096> {        // ← needs RFC-0055
    let scratch = reg.alloc(SmallThing::new());
    use(scratch)
}
```

**Cost:** the most predictable, allocation-free region strategy — the one most attractive for the eventual compiler and for embedded-style use — is gated behind a separate feature. Bounded, no-heap scratch is not available in the interpreter-first cut.

---

### 3.8 Invisible lifetimes have a diagnosability cost

The flip side of "you never write `'r`" is that when inference *rejects* a program, the error must explain a lifetime the programmer never named. There is no annotation on the page to point at.

```text
error: value cannot escape its region
  --> parse.metel:14
   |
14 |     p                       // returning a Parser that borrows region 'r
   |     ^ this borrows from the region opened on line 11, which is freed here
   = note: `Parser` holds a pointer into `'r` (inferred from field `input: *str`)
   = help: return an owned value, or take a `Region` parameter from the caller
```

**Cost:** the quality of these diagnostics *is* the usability of the feature. Lexical regions keep the offending scope visible (you can see the block), which is the saving grace versus whole-program inference — but the compiler must reconstruct and name an inferred lifetime well, or the model trades annotation burden for debugging burden. This is the single biggest implementation risk of the "optional annotations" bet.

---

### 3.9 Summary of limitations

| # | Limitation | Root cause | Escape hatch |
|---|---|---|---|
| 3.1 | Over-rejects borrow-from-one-of-many | conservative `min`-of-inputs default | explicit `'a`, or return owned |
| 3.2 | Aliased `*mut` unchecked | no XOR-mutability borrow check | interpreter backstop (no corruption); separate allocations for disjointness |
| 3.3 | Can't return data from a self-owned region | region storage gone at brace | pass `Region` in, or return owned / `@T` |
| 3.4 | Region-safe ≠ edge-safe | arena validity is spatial, not logical | own generation/tombstone scheme |
| 3.5 | No cross-fiber region | `Region` not `Send` | per-fiber regions + channels |
| 3.6 | Standalone self-reference | no lifetime to anchor the inner pointer | `@T` for trees, or wrap in a region |
| 3.7 | `FixedRegion<N>` unavailable | needs comptime (RFC-0055) | use `BumpRegion` until comptime lands |
| 3.8 | Errors name un-written lifetimes | optional annotations | high-quality diagnostics + lexical scopes |

The throughline: the model buys **annotation-free spatial memory safety with deterministic bulk cleanup**, and pays for it in **conservative rejection, unchecked aliasing, and the burden of explaining inferred lifetimes**. For the interpreter-first product that is a deliberate and, on balance, favourable trade — but these seven-plus edges are exactly where the design should expect pushback and where v1 should set honest expectations.

---

## References

- Memory model thesis & design decisions — `docs/reports/memory-model/memory-model-programs.md` (Part 7)
- RFC-0028: Memory and Reference Model — `docs/internal/rfcs/1-under-review/rfc-0028-memory-and-reference-model.md`
- RFC-0025: Region Allocation — `docs/internal/rfcs/1-under-review/rfc-0025-region-allocation.md`
- RFC-0056: Explicit Region Parameters (handle syntax — OQ-1 resolved here: `region 'r reg { }` + callback) — `docs/internal/rfcs/0-draft/rfc-0056-explicit-region-parameters.md`
- RFC-0052: Lifetime System — `docs/internal/rfcs/0-draft/rfc-0052-lifetime-system.md`
- RFC-0051: RegionFree Exit Constraint — `docs/internal/rfcs/1-under-review/rfc-0051-regionfree-exit-constraint.md`
- RFC-0043: Regular Pointers — `docs/internal/rfcs/3-implemented/rfc-0043-regular-pointers.md`
- Prior art: Zig `std.mem.Allocator`; Tofte & Talpin region inference / ML Kit (1994); Cyclone regions (2002); Rust lifetimes + NLL
