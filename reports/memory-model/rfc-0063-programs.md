# RFC-0063 Programs

**Date:** 2026-06-27
**Status:** Design material — illustrates RFC-0063 (Region Handles) and RFC-0065 (Region Ergonomics)

Three allocation-heavy programs written in the syntax those RFCs define. Each compiles
against the core alone (RFC-0063); inference annotations in comments mark the spots where
RFC-0065 removes ceremony.

---

## Program 1 — Rope

A rope is a binary tree of string fragments. Concatenation is O(1); it only pays for a flat
`String` when one is explicitly requested. All tree nodes live in a caller-supplied region;
the only value that escapes to the heap is the materialised `String`.

Shows: recursive region-parameterised enum, bracket channel functions, `@[Heap]` as the
escape target, call-site inference (RFC-0065 §2).

```metel
enum Rope[r] {
    Leaf { bytes: @[r] str },
    Node { left: @[r] Rope, right: @[r] Rope, len: usize },
}

// ── Construction ──────────────────────────────────────────────────────────────

fun leaf[region](text: &str) -> @[region] Rope {
    region.alloc(Rope::Leaf { bytes: region.alloc(str_copy(text)) })
}

fun concat[region](left: @[region] Rope, right: @[region] Rope) -> @[region] Rope {
    let len = rope_len(&left) + rope_len(&right);
    region.alloc(Rope::Node { left, right, len })
}

// ── Queries ───────────────────────────────────────────────────────────────────

fun rope_len[r](rope: &[r] Rope) -> usize {
    match rope {
        Rope::Leaf { bytes }    => str_len(bytes),
        Rope::Node { len, .. }  => len,
    }
}

fun rope_char_at[r](rope: &[r] Rope, idx: usize) -> char {
    match rope {
        Rope::Leaf { bytes } => str_char_at(bytes, idx),
        Rope::Node { left, right, .. } => {
            let ll = rope_len(left);
            if idx < ll { rope_char_at(left, idx) }
            else        { rope_char_at(right, idx - ll) }
        }
    }
}

// ── Slicing: allocates new nodes into the same region ────────────────────────

fun rope_slice[region](rope: &[region] Rope, from: usize, to: usize) -> @[region] Rope {
    if from == 0 && to == rope_len(rope) { return *rope; }
    match rope {
        Rope::Leaf { bytes } =>
            leaf(str_slice(bytes, from, to)),   // [region] inferred (RFC-0065)
        Rope::Node { left, right, .. } => {
            let ll = rope_len(left);
            if to <= ll {
                rope_slice(left, from, to)
            } else if from >= ll {
                rope_slice(right, from - ll, to - ll)
            } else {
                // [region] inferred on both calls
                concat(rope_slice(left, from, ll), rope_slice(right, 0, to - ll))
            }
        }
    }
}

// ── Materialisation: write into a heap-allocated String ───────────────────────
// [r] is abstract — works for any rope regardless of which region it lives in.

fun rope_write[r](rope: &[r] Rope, out: &mut [Heap] String) {
    match rope {
        Rope::Leaf { bytes }           => string_push(out, bytes),
        Rope::Node { left, right, .. } => { rope_write(left, out); rope_write(right, out); }
    }
}

fun rope_to_string[r](rope: &[r] Rope) -> @[Heap] String {
    let mut s = Heap.alloc(String::with_capacity(rope_len(rope)));
    rope_write(rope, &mut s);
    s
}

// ── Main ──────────────────────────────────────────────────────────────────────

fun main() {
    let result: @[Heap] String = Region::scoped([region]() -> {
        let words = ["the ", "quick ", "brown ", "fox ", "jumps"];

        let mut rope = leaf(words[0]);
        for w in words[1..] {
            rope = concat(rope, leaf(w));    // [region] inferred throughout
        }

        let sub = rope_slice(&rope, 4, 9);  // "quick"
        assert(rope_char_at(&sub, 0) == 'q');
        assert(rope_len(&sub) == 5);

        rope_to_string(&rope)               // @[Heap] String — the only thing that escapes
        // All Rope nodes freed here in O(1)
    });

    println(result);  // the quick brown fox jumps
}
```

### Post RFC-0065 — Rope

Return types use bare `@`; call sites need no bracket argument; local allocations drop their
type annotations. The `@[Heap]` return on `rope_to_string` stays explicit because `Heap` is
not declared in the bracket channel — it is a static handle, not a region parameter, so
elision does not apply.

```metel
enum Rope[r] {
    Leaf { bytes: @[r] str },
    Node { left: @[r] Rope, right: @[r] Rope, len: usize },
}

fun leaf[region](text: &str) -> @Rope {
    region.alloc(Rope::Leaf { bytes: region.alloc(str_copy(text)) })
}

fun concat[region](left: @[region] Rope, right: @[region] Rope) -> @Rope {
    let len = rope_len(&left) + rope_len(&right);
    region.alloc(Rope::Node { left, right, len })
}

fun rope_len[r](rope: &[r] Rope) -> usize {
    match rope {
        Rope::Leaf { bytes }    => str_len(bytes),
        Rope::Node { len, .. }  => len,
    }
}

fun rope_char_at[r](rope: &[r] Rope, idx: usize) -> char {
    match rope {
        Rope::Leaf { bytes } => str_char_at(bytes, idx),
        Rope::Node { left, right, .. } => {
            let ll = rope_len(left);
            if idx < ll { rope_char_at(left, idx) }
            else        { rope_char_at(right, idx - ll) }
        }
    }
}

fun rope_slice[region](rope: &[region] Rope, from: usize, to: usize) -> @Rope {
    if from == 0 && to == rope_len(rope) { return *rope; }
    match rope {
        Rope::Leaf { bytes } => leaf(str_slice(bytes, from, to)),
        Rope::Node { left, right, .. } => {
            let ll = rope_len(left);
            if to <= ll {
                rope_slice(left, from, to)
            } else if from >= ll {
                rope_slice(right, from - ll, to - ll)
            } else {
                concat(rope_slice(left, from, ll), rope_slice(right, 0, to - ll))
            }
        }
    }
}

fun rope_write[r](rope: &[r] Rope, out: &mut [Heap] String) {
    match rope {
        Rope::Leaf { bytes }           => string_push(out, bytes),
        Rope::Node { left, right, .. } => { rope_write(left, out); rope_write(right, out); }
    }
}

fun rope_to_string[r](rope: &[r] Rope) -> @[Heap] String {
    let mut s = Heap.alloc(String::with_capacity(rope_len(rope)));
    rope_write(rope, &mut s);
    s
}

fun main() {
    let result: @[Heap] String = Region::scoped([region]() -> {
        let words = ["the ", "quick ", "brown ", "fox ", "jumps"];
        let mut rope = leaf(words[0]);
        for w in words[1..] { rope = concat(rope, leaf(w)); }

        let sub = rope_slice(&rope, 4, 9);
        assert(rope_char_at(&sub, 0) == 'q');
        assert(rope_len(&sub) == 5);

        rope_to_string(&rope)
    });
    println(result);
}
```

---

## Program 2 — Per-request HTTP parser

A minimal HTTP parser. Each call to `handle_request` creates a fresh arena, parses the
request into it (headers, method, path, body bytes), extracts a plain-value `Summary`, then
discards everything at once. A `Config` shared across calls lives on the heap.

Shows: region-parameterised structs, nested allocation, reading from a region pointer without
consuming it, and the pattern of "process in arena, extract plain-value result."

```metel
struct Config {
    max_headers:    usize,
    max_body_bytes: usize,
}

struct Header[r] {
    name:  @[r] str,
    value: @[r] str,
}

struct Request[r] {
    method:  @[r] str,
    path:    @[r] str,
    headers: @[r] Vec<@[r] Header>,
    body:    @[r] [u8],
}

// Plain values only — escapes the arena without carrying any region pointer.
struct Summary {
    status:       u16,
    content_type: @[Heap] str,
    body_bytes:   usize,
}

// ── Parsing into the request arena ───────────────────────────────────────────

fun parse_header[region](line: &str) -> Perhaps<@[region] Header> {
    match str_find(line, ':') {
        Perhaps::None {}           => Perhaps::None {},
        Perhaps::Some { value: i } => {
            let name  = region.alloc(str_trim(str_slice(line, 0, i)));
            let value = region.alloc(str_trim(str_slice(line, i + 1, str_len(line))));
            Perhaps::Some { value: region.alloc(Header { name, value }) }
        }
    }
}

fun parse_request[region](raw: &str) -> Perhaps<@[region] Request> {
    let lines = str_lines(raw);
    if vec_len(&lines) == 0 { return Perhaps::None {}; }

    let parts = str_split(vec_get(&lines, 0), ' ');
    if vec_len(&parts) < 2 { return Perhaps::None {}; }

    let method = region.alloc(str_copy(vec_get(&parts, 0)));
    let path   = region.alloc(str_copy(vec_get(&parts, 1)));
    let mut headers: @[region] Vec<@[region] Header> = region.alloc(Vec::new());

    let mut i = 1;
    while i < vec_len(&lines) {
        let line = vec_get(&lines, i);
        if str_is_empty(line) { i += 1; break; }
        if let Perhaps::Some { value: h } = parse_header(line) {  // [region] inferred
            vec_push(&mut headers, h);
        }
        i += 1;
    }

    let body = region.alloc(str_to_bytes(str_from_offset(raw, i)));
    Perhaps::Some { value: region.alloc(Request { method, path, headers, body }) }
}

// ── Processing while the arena is live ───────────────────────────────────────

fun find_header[r](req: &[r] Request, name: &str) -> Perhaps<@[r] str> {
    for h in req.headers {
        if str_eq_ignore_case(h.name, name) { return Perhaps::Some { value: h.value }; }
    }
    Perhaps::None {}
}

fun validate[r](req: &[r] Request, cfg: &Config) -> bool {
    vec_len(&req.headers) <= cfg.max_headers
        && vec_len(&req.body) <= cfg.max_body_bytes
}

fun build_summary[r](req: &[r] Request) -> Summary {
    // content_type is copied to the heap — it must outlive the arena.
    let ct = match find_header(req, "content-type") {
        Perhaps::Some { value: v } => Heap.alloc(str_copy(v)),
        Perhaps::None {}           => Heap.alloc(str_copy("application/octet-stream")),
    };
    Summary { status: 200, content_type: ct, body_bytes: vec_len(&req.body) }
}

// ── Entry point: one arena per request ───────────────────────────────────────

fun handle_request(raw: &str, cfg: &Config) -> Perhaps<Summary> {
    Region::scoped([region]() -> {
        match parse_request(raw) {   // [region] inferred
            Perhaps::None {}             => Perhaps::None {},
            Perhaps::Some { value: req } =>
                if validate(&req, cfg) {
                    Perhaps::Some { value: build_summary(&req) }
                    // req, headers, all str copies freed here in O(1)
                } else {
                    Perhaps::None {}
                }
        }
    })
}

fun main() {
    let cfg = Config { max_headers: 64, max_body_bytes: 1_048_576 };
    let raw = "POST /upload HTTP/1.1\r\nContent-Type: application/json\r\nHost: api.example.com\r\n\r\n{\"key\":\"value\"}";

    match handle_request(raw, &cfg) {
        Perhaps::None {}           => println("400 Bad Request"),
        Perhaps::Some { value: s } =>
            println(u16_to_string(s.status) + " body=" + usize_to_string(s.body_bytes)),
    }
}
```

### Post RFC-0065 — HTTP parser

Return types use bare `@` where a single region is in scope. Local allocations drop their
type annotations entirely — `let mut headers = region.alloc(Vec::new())` is inferred as
`@[region] Vec<@[region] Header>` once the push calls provide the element type. The
`@[Heap] str` in `Summary` and in `build_summary` stays explicit: `Heap` is a static
handle, not a bracket parameter.

```metel
struct Config {
    max_headers:    usize,
    max_body_bytes: usize,
}

struct Header[r] {
    name:  @[r] str,
    value: @[r] str,
}

struct Request[r] {
    method:  @[r] str,
    path:    @[r] str,
    headers: @[r] Vec<@[r] Header>,
    body:    @[r] [u8],
}

struct Summary {
    status:       u16,
    content_type: @[Heap] str,
    body_bytes:   usize,
}

fun parse_header[region](line: &str) -> Perhaps<@Header> {
    match str_find(line, ':') {
        Perhaps::None {}           => Perhaps::None {},
        Perhaps::Some { value: i } => {
            let name  = region.alloc(str_trim(str_slice(line, 0, i)));
            let value = region.alloc(str_trim(str_slice(line, i + 1, str_len(line))));
            Perhaps::Some { value: region.alloc(Header { name, value }) }
        }
    }
}

fun parse_request[region](raw: &str) -> Perhaps<@Request> {
    let lines = str_lines(raw);
    if vec_len(&lines) == 0 { return Perhaps::None {}; }

    let parts = str_split(vec_get(&lines, 0), ' ');
    if vec_len(&parts) < 2 { return Perhaps::None {}; }

    let method  = region.alloc(str_copy(vec_get(&parts, 0)));
    let path    = region.alloc(str_copy(vec_get(&parts, 1)));
    let mut headers = region.alloc(Vec::new());

    let mut i = 1;
    while i < vec_len(&lines) {
        let line = vec_get(&lines, i);
        if str_is_empty(line) { i += 1; break; }
        if let Perhaps::Some { value: h } = parse_header(line) {
            vec_push(&mut headers, h);
        }
        i += 1;
    }

    let body = region.alloc(str_to_bytes(str_from_offset(raw, i)));
    Perhaps::Some { value: region.alloc(Request { method, path, headers, body }) }
}

fun find_header[r](req: &[r] Request, name: &str) -> Perhaps<@[r] str> {
    for h in req.headers {
        if str_eq_ignore_case(h.name, name) { return Perhaps::Some { value: h.value }; }
    }
    Perhaps::None {}
}

fun validate[r](req: &[r] Request, cfg: &Config) -> bool {
    vec_len(&req.headers) <= cfg.max_headers
        && vec_len(&req.body) <= cfg.max_body_bytes
}

fun build_summary[r](req: &[r] Request) -> Summary {
    let ct = match find_header(req, "content-type") {
        Perhaps::Some { value: v } => Heap.alloc(str_copy(v)),
        Perhaps::None {}           => Heap.alloc(str_copy("application/octet-stream")),
    };
    Summary { status: 200, content_type: ct, body_bytes: vec_len(&req.body) }
}

fun handle_request(raw: &str, cfg: &Config) -> Perhaps<Summary> {
    Region::scoped([region]() -> {
        match parse_request(raw) {
            Perhaps::None {}             => Perhaps::None {},
            Perhaps::Some { value: req } =>
                if validate(&req, cfg) {
                    Perhaps::Some { value: build_summary(&req) }
                } else {
                    Perhaps::None {}
                }
        }
    })
}

fun main() {
    let cfg = Config { max_headers: 64, max_body_bytes: 1_048_576 };
    let raw = "POST /upload HTTP/1.1\r\nContent-Type: application/json\r\nHost: api.example.com\r\n\r\n{\"key\":\"value\"}";

    match handle_request(raw, &cfg) {
        Perhaps::None {}           => println("400 Bad Request"),
        Perhaps::Some { value: s } =>
            println(u16_to_string(s.status) + " body=" + usize_to_string(s.body_bytes)),
    }
}
```

---

## Program 3 — BFS with scratch arena and two-region transfer

A shortest-path finder over a heap-resident graph. Each BFS call allocates a fresh scratch
arena for the queue and visited array, then frees it in O(1) when the call returns. The
reconstructed path is written into a second, longer-lived result region via a two-region
`copy_vec` function that uses an `Outlives` bound.

Shows: `@[Heap]` for persistent data, per-call scratch regions, the `Outlives<src>` bound
for copying between two region lifetimes, and the pattern of accumulating results into a
result region across multiple scratch scopes.

```metel
struct Node {
    id:        u32,
    label:     @[Heap] str,
    neighbors: @[Heap] Vec<u32>,
}

struct Graph {
    nodes: @[Heap] Vec<@[Heap] Node>,
}

// ── Graph construction ────────────────────────────────────────────────────────

fun graph_new() -> @[Heap] Graph {
    Heap.alloc(Graph { nodes: Heap.alloc(Vec::new()) })
}

fun add_node(g: &mut [Heap] Graph, label: &str) -> u32 {
    let id = vec_len(&g.nodes) as u32;
    vec_push(&mut g.nodes, Heap.alloc(Node {
        id,
        label:     Heap.alloc(str_copy(label)),
        neighbors: Heap.alloc(Vec::new()),
    }));
    id
}

fun add_edge(g: &mut [Heap] Graph, from: u32, to: u32) {
    vec_push(&mut g.nodes[from as usize].neighbors, to);
}

// ── Two-region transfer ───────────────────────────────────────────────────────
// Copies a Vec<u32> from a short-lived source region into a longer-lived
// destination region. The Outlives<src> bound is the static proof that dst
// will still be alive when the copy is read — the compiler enforces it.

fun copy_vec<[src, dst: Outlives<src>]>(v: &[src] Vec<u32>) -> @[dst] Vec<u32> {
    let out = dst.alloc(Vec::with_capacity(vec_len(v)));
    for &x in v { vec_push(&mut out, x); }
    out
}

// ── BFS in a scratch arena ────────────────────────────────────────────────────

fun bfs_into[scratch, result: Outlives<scratch>](
    graph:  &[Heap] Graph,
    start:  u32,
    target: u32,
) -> Perhaps<@[result] Vec<u32>> {
    let n = vec_len(&graph.nodes);

    // All BFS state lives in the scratch arena.
    let visited: @[scratch] Vec<bool>  = scratch.alloc(vec_repeat(false, n));
    let parent:  @[scratch] Vec<i64>   = scratch.alloc(vec_repeat(-1_i64, n));
    let queue:   @[scratch] Queue<u32> = scratch.alloc(Queue::new());

    visited[start as usize] = true;
    queue_push(&mut queue, start);

    let mut found = false;
    while !queue_is_empty(&queue) {
        let cur = queue_pop(&mut queue);
        if cur == target { found = true; break; }
        for &nb in graph.nodes[cur as usize].neighbors {
            if !visited[nb as usize] {
                visited[nb as usize] = true;
                parent[nb as usize]  = cur as i64;
                queue_push(&mut queue, nb);
            }
        }
    }

    if !found { return Perhaps::None {}; }

    // Reconstruct path into scratch, then copy it into the result region.
    let mut path: @[scratch] Vec<u32> = scratch.alloc(Vec::new());
    let mut cur = target;
    loop {
        vec_push(&mut path, cur);
        if cur == start { break; }
        cur = parent[cur as usize] as u32;
    }
    vec_reverse(&mut path);

    // copy_vec[scratch, result] transfers ownership across the region boundary.
    Perhaps::Some { value: copy_vec[scratch, result](&path) }
}

// ── Batch queries: each BFS gets its own scratch region ──────────────────────

fun shortest_paths[result](
    graph:   &[Heap] Graph,
    queries: &[(u32, u32)],
) -> @[result] Vec<Perhaps<@[result] Vec<u32>>> {
    let results: @[result] Vec<Perhaps<@[result] Vec<u32>>> = result.alloc(Vec::new());
    for &(start, target) in queries {
        // scratch is nested inside result, so result Outlives scratch — bound satisfied.
        let path = Region::scoped([scratch]() -> {
            bfs_into[scratch, result](&graph, start, target)
        });
        vec_push(&mut results, path);
    }
    results
}

// ── Main ──────────────────────────────────────────────────────────────────────

fun main() {
    let mut g = graph_new();
    let a = add_node(&mut g, "A");
    let b = add_node(&mut g, "B");
    let c = add_node(&mut g, "C");
    let d = add_node(&mut g, "D");
    let e = add_node(&mut g, "E");

    add_edge(&mut g, a, b);
    add_edge(&mut g, a, d);
    add_edge(&mut g, b, c);
    add_edge(&mut g, d, c);
    add_edge(&mut g, c, e);

    let queries: [(u32, u32)] = [(a, e), (b, d), (d, b)];

    // Both the path vectors and the results vec live in the outer region.
    // Each BFS call uses a nested scratch region that is freed on return.
    Region::scoped([result]() -> {
        let paths = shortest_paths[result](&g, &queries);

        for (i, path_opt) in vec_enumerate(&paths) {
            let (s, t) = queries[i];
            match path_opt {
                Perhaps::None {}           =>
                    println(u32_to_string(s) + " → " + u32_to_string(t) + ": no path"),
                Perhaps::Some { value: p } => {
                    let labels: @[result] Vec<@[Heap] str> =
                        vec_map(&p, (id) -> { g.nodes[id as usize].label });
                    println(vec_join(&labels, " → "));
                }
            }
        }
    });
}
```

### Post RFC-0065 — BFS

`shortest_paths` gains return-position elision on both `@[result]` occurrences in its return
type. Inside `bfs_into`, local allocations drop their type annotations; the variables are
typed by the alloc calls. The two-region calls `bfs_into[scratch, result]` and
`copy_vec[scratch, result]` stay explicit — two region handles are in scope at those points
so inference would be ambiguous.

```metel
struct Node {
    id:        u32,
    label:     @[Heap] str,
    neighbors: @[Heap] Vec<u32>,
}

struct Graph {
    nodes: @[Heap] Vec<@[Heap] Node>,
}

fun graph_new() -> @[Heap] Graph {
    Heap.alloc(Graph { nodes: Heap.alloc(Vec::new()) })
}

fun add_node(g: &mut [Heap] Graph, label: &str) -> u32 {
    let id = vec_len(&g.nodes) as u32;
    vec_push(&mut g.nodes, Heap.alloc(Node {
        id,
        label:     Heap.alloc(str_copy(label)),
        neighbors: Heap.alloc(Vec::new()),
    }));
    id
}

fun add_edge(g: &mut [Heap] Graph, from: u32, to: u32) {
    vec_push(&mut g.nodes[from as usize].neighbors, to);
}

fun copy_vec<[src, dst: Outlives<src>]>(v: &[src] Vec<u32>) -> @[dst] Vec<u32> {
    let out = dst.alloc(Vec::with_capacity(vec_len(v)));
    for &x in v { vec_push(&mut out, x); }
    out
}

fun bfs_into[scratch, result: Outlives<scratch>](
    graph:  &[Heap] Graph,
    start:  u32,
    target: u32,
) -> Perhaps<@[result] Vec<u32>> {
    let n       = vec_len(&graph.nodes);
    let visited = scratch.alloc(vec_repeat(false, n));
    let parent  = scratch.alloc(vec_repeat(-1_i64, n));
    let queue   = scratch.alloc(Queue::new());

    visited[start as usize] = true;
    queue_push(&mut queue, start);

    let mut found = false;
    while !queue_is_empty(&queue) {
        let cur = queue_pop(&mut queue);
        if cur == target { found = true; break; }
        for &nb in graph.nodes[cur as usize].neighbors {
            if !visited[nb as usize] {
                visited[nb as usize] = true;
                parent[nb as usize]  = cur as i64;
                queue_push(&mut queue, nb);
            }
        }
    }

    if !found { return Perhaps::None {}; }

    let mut path = scratch.alloc(Vec::new());
    let mut cur  = target;
    loop {
        vec_push(&mut path, cur);
        if cur == start { break; }
        cur = parent[cur as usize] as u32;
    }
    vec_reverse(&mut path);

    Perhaps::Some { value: copy_vec[scratch, result](&path) }
}

fun shortest_paths[result](
    graph:   &[Heap] Graph,
    queries: &[(u32, u32)],
) -> @Vec<Perhaps<@Vec<u32>>> {
    let results = result.alloc(Vec::new());
    for &(start, target) in queries {
        let path = Region::scoped([scratch]() -> {
            bfs_into[scratch, result](&graph, start, target)
        });
        vec_push(&mut results, path);
    }
    results
}

fun main() {
    let mut g = graph_new();
    let a = add_node(&mut g, "A");
    let b = add_node(&mut g, "B");
    let c = add_node(&mut g, "C");
    let d = add_node(&mut g, "D");
    let e = add_node(&mut g, "E");

    add_edge(&mut g, a, b);
    add_edge(&mut g, a, d);
    add_edge(&mut g, b, c);
    add_edge(&mut g, d, c);
    add_edge(&mut g, c, e);

    let queries: [(u32, u32)] = [(a, e), (b, d), (d, b)];

    Region::scoped([result]() -> {
        let paths = shortest_paths(&g, &queries);

        for (i, path_opt) in vec_enumerate(&paths) {
            let (s, t) = queries[i];
            match path_opt {
                Perhaps::None {}           =>
                    println(u32_to_string(s) + " → " + u32_to_string(t) + ": no path"),
                Perhaps::Some { value: p } => {
                    let labels = vec_map(&p, (id) -> { g.nodes[id as usize].label });
                    println(vec_join(&labels, " → "));
                }
            }
        }
    });
}
```

---

## What the three programs cover

| Feature | Prog 1 | Prog 2 | Prog 3 |
|---|:---:|:---:|:---:|
| Recursive region-parameterised type | ✓ | | |
| Region-parameterised struct | | ✓ | ✓ |
| `r.alloc(v)` for owned allocation | ✓ | ✓ | ✓ |
| `Heap.alloc(v)` for persistent allocation | ✓ | ✓ | ✓ |
| `@[r] T` across function boundaries | ✓ | ✓ | ✓ |
| Abstract region param (`[r]` read-only) | ✓ | ✓ | |
| `Outlives<src>` two-region bound | | | ✓ |
| `Region::scoped` | ✓ | ✓ | ✓ |
| Return-position elision `@T` (RFC-0065 §1) | ✓ | ✓ | ✓ |
| Call-site inference (RFC-0065 §2) | ✓ | ✓ | |
| Explicit bracket required (two regions) | | | ✓ |
| Nested scratch within outer region | | | ✓ |
| Plain-value escape from arena | ✓ | ✓ | |
| Borrow (`&[r] T`) without consuming | ✓ | ✓ | ✓ |
