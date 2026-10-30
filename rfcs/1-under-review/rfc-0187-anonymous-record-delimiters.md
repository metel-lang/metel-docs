---
id: rfc-0187
title: "Anonymous record delimiters"
date: '2026-10-21'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1639'
---

> **Status — under review (2026-10-26).** Moved to review and scheduled for v0.15.0

> **Scope (2026-10-26, revised 2026-10-27).** This RFC originally also proposed label syntax (`.name`,
> `.[L]`) and rows as record types. The label spelling is now RFC-0188; the row declaration change is
> RFC-0186. This RFC keeps only the record delimiters.

## Summary

**Anonymous records get their own delimiters, `{| … |}`**, so a record is never confused with a
block. A record is written the same way in every position: no parentheses, no "the block wins".

The semantics of records (RFC-0116, RFC-0120) are not changed. This RFC is a syntax change to the
outer delimiters only; label spelling is RFC-0188 and the row kind is RFC-0186.

RFC-0183 makes plain assignment `=`, which gives `{ x = 1 }` a third reading (a block whose tail is
an assignment). With this RFC accepted, RFC-0183 needs no `;` or statement-only rule to keep
records and blocks apart. Its statement-only rule is still the only thing that removes the
`f(x = 1)` and `if (x = 1)` expression hazards (RFC-0183 §2, §5).

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### A record literal collides with a block

An anonymous record `{ x = 1 }` and a block `{ x = 1 }` are the same text. RFC-0116 resolves this
deterministically, by letting the block win, and the consequences are written into the spec and
into the records post as a warning:

- `{ x }` and `{ x = 1 }` are records only in pure-expression positions (the right-hand side of a
  `let`, call arguments, operands). In an `if`/`else` arm, a `match` arm, or a function, closure
  or loop body they are a block whose tail is `x` or the assignment `x = 1`.
- To get a record there you write `({ x = 1 })`.
- A multi-field literal `{ x = 1, y = 2 }` works anywhere, only because a comma is invalid inside
  a block, so the parser backtracks to the record. The rule is therefore subtle, not simple: whether
  a literal needs parentheses depends on its length and its position.
- The type side reads the same way. `fun f() -> { x: i64 } { … }` is two brace groups in a row.

Feedback on the published syntax asked for record delimiters distinct from block delimiters. This
is the same problem seen from the reader's side.

RFC-0183 (initialization-only `:=`) moves plain assignment to `=`. Then `{ x = 1 }` is also a valid
block whose tail is the assignment `x = 1`, where today it is not (assignment is `:=`). The
block-wins rule would then silently turn a record tail such as `fun f() -> { x: i64 } { { x = 1 } }`
into a block returning `()`. A distinct record delimiter removes the collision instead of working
around it.

---

## Proposal

### 1. Record delimiters: `{| … |}`

An anonymous record is written between `{|` and `|}`, in a literal, a pattern, a type, a row bound
and a row equation alike:

```metel
let p := {| x = 1.0, y = 2.0 |};
let q := {| x, y |};                       // punned, valid in every position
fun origin() -> {| x: f64, y: f64 |} {| x = 0.0, y = 0.0 |}
let {| x, y |} := p;                       // pattern
fun len<row R>(p: {| x: f64, ..R |}) -> f64 { … }       // open row type
fun n<row R>(p: {| x: f64, ..R |}) where R = {| y: f64, ..Rest |} { … }
type Req = Request<..{| host: String, ..R |}>;           // RFC-0180's row-literal argument, new delimiters
```

The record forms that exist today keep their other parts and change only the outer delimiters:

| Today | Proposed |
|---|---|
| `{ x = 1, y = 2 }` | `{\| x = 1, y = 2 \|}` |
| `{ x, y }` | `{\| x, y \|}` |
| `{ ..r, auth = a }` (RFC-0178 spread) | `{\| ..r, auth = a \|}` |
| `{ token, ..rest }` (rest pattern) | `{\| token, ..rest \|}` |
| `{ x: f64, ..R }`, `{ .. }` | `{\| x: f64, ..R \|}`, `{\| .. \|}` |
| `R: { x: f64, .. }`, `!{ token }` | `R: {\| x: f64, .. \|}`, `!{\| token \|}` |
| `where R = { token: T, ..Rest }` | `where R = {\| token: T, ..Rest \|}` |
| `Name<..{ host: String, ..R }>` (RFC-0180) | `Name<..{\| host: String, ..R \|}>` |

The empty record is `{| |}`.

**What does not change:**

- Named struct and variant literals and patterns, `Point { x = 1 }` and `Shape::Circle { r }`.
  A leading type path already tells them apart from a block.
- Blocks, including a block that starts with a closure.
- Projection types and expressions, `Handle.{ fd }` and `r.{ a, b }`. Their `.{` is already
  distinct, and they list field names only.
- Closure syntax, `|x| …`, and its capture lists.

#### Parsing

`{|` and `|}` are not tokens in the current grammar: they occur nowhere in the fixture corpus, the
standard library, the spec, the tutorials or the blog. The record production is
`"{|" ~ entries ~ "|}"`. Two cases need a rule:

- **A block that starts with a closure and has no space**, `{|x| x + 1}`. The record parse fails
  (after `{|` a record needs `ident`, `ident = expr`, `..expr` or `|}`; `x| x + 1}` provides none of
  them) and the block parse succeeds. A record is tried wherever `{|` starts one, and otherwise the
  text is a block, so no program changes meaning. A prototype must confirm that no input is accepted
  both ways.
- **`||` and `|}` inside a record.** A field value may be a closure, `{| f = |x| x + 1 |}`, or
  contain `||`. The closing `|}` is recognised only where a binary `|` or `||` could not continue the
  expression, because `}` is not an operand.

The formatter writes `{| … |}` with spaces inside and writes a closure-first block as `{ |x| … }`.
That removes the reader's remaining doubt about `{|x|`.

The rule "a block wins in a block-admitting position" and the parenthesization workaround
`({ x = 1 })` disappear from RFC-0116. A record means the same thing in every position.

---

## Worked examples

Three programs of 40 to 55 lines, each shown as it is written today and with this RFC applied. Only
the outer delimiters of anonymous records change. Everything else (`:=` reassignment, `<row R>`,
`Req<..R>`, named-struct and variant literals such as `Req { data = … }` and `Event::Click { x = 3 }`)
is deliberately left as it is; RFC-0183 and RFC-0186 change those separately.

The "today" programs compile and run on `develop` (with and without `--move-check`). None of this
RFC is implemented, so each "with this RFC" program is checked only by a mechanical round trip:
rewriting `{| ` to `{ `, ` |}` to ` }` and `{| |}` to `{}` reproduces the compiled program exactly.

### Order pricing

Open rows (`<row R>`), a spread-free rebuild with a rest pattern, record arrays and a running summary. Every record is anonymous.

Today:

```metel
// Order pricing: anonymous records, open rows, spread updates and a running total.
fun line_total<row R>(line: { price: i64, qty: i64, ..R }) -> i64 {
    line.price * line.qty
}

fun discounted<row R: !{ price }>(line: { price: i64, ..R }, pct: i64) -> { price: i64, ..R } {
    let { price, ..rest } := line;
    { price = price * (100 - pct) / 100, ..rest }
}

fun summarize(lines: [{ id: i64, price: i64, qty: i64 }; 3]) -> { count: i64, total: i64, max_line: i64 } {
    var summary := { count = 0, total = 0, max_line = 0 };
    for (line in lines) {
        let t := line_total(line);
        summary.count := summary.count + 1;
        summary.total := summary.total + t;
        if (t > summary.max_line) {
            summary.max_line := t;
        }
    }
    summary
}

fun main() {
    var lines := [
        { id = 1, price = 120, qty = 10 },
        { id = 2, price = 450, qty = 2 },
        { id = 3, price = 300, qty = 4 },
    ];
    lines[0] := discounted(lines[0], 10);

    let { count, total, .. } := summarize(lines);
    let { max_line, ..rest } := summarize(lines);

    assert(count == 3);
    assert(total == 1080 + 900 + 1200);
    assert(max_line == 1200);
    assert(rest.count == 3);
    assert(discounted({ id = 9, price = 200, qty = 1, note = 5 }, 50).note == 5);
    println("order ok");
}
```

With this RFC:

```metel
// Order pricing: anonymous records, open rows, spread updates and a running total.
fun line_total<row R>(line: {| price: i64, qty: i64, ..R |}) -> i64 {
    line.price * line.qty
}

fun discounted<row R: !{| price |}>(line: {| price: i64, ..R |}, pct: i64) -> {| price: i64, ..R |} {
    let {| price, ..rest |} := line;
    {| price = price * (100 - pct) / 100, ..rest |}
}

fun summarize(lines: [{| id: i64, price: i64, qty: i64 |}; 3]) -> {| count: i64, total: i64, max_line: i64 |} {
    var summary := {| count = 0, total = 0, max_line = 0 |};
    for (line in lines) {
        let t := line_total(line);
        summary.count := summary.count + 1;
        summary.total := summary.total + t;
        if (t > summary.max_line) {
            summary.max_line := t;
        }
    }
    summary
}

fun main() {
    var lines := [
        {| id = 1, price = 120, qty = 10 |},
        {| id = 2, price = 450, qty = 2 |},
        {| id = 3, price = 300, qty = 4 |},
    ];
    lines[0] := discounted(lines[0], 10);

    let {| count, total, .. |} := summarize(lines);
    let {| max_line, ..rest |} := summarize(lines);

    assert(count == 3);
    assert(total == 1080 + 900 + 1200);
    assert(max_line == 1200);
    assert(rest.count == 3);
    assert(discounted({| id = 9, price = 200, qty = 1, note = 5 |}, 50).note == 5);
    println("order ok");
}
```

### Typed request builder

`record Req<row R>`, row-conditional `extend` blocks and a row equation. Record types appear as arguments, bounds and equations.

Today:

```metel
// A typed request builder: each step changes the row, and methods exist only once the
// fields they need are present.
record Req<row R> { data: { ..R } }

fun empty() -> Req<..{}> { Req { data = {} } }

fun add_host<row R: !{ host }>(r: Req<..R>, h: i64) -> Req<..{ host: i64, ..R }> {
    Req { data = { host = h, ..r.data } }
}

fun add_token<row R: !{ token }>(r: Req<..R>, t: i64) -> Req<..{ token: i64, ..R }> {
    Req { data = { token = t, ..r.data } }
}

extend<row R: { host: i64, .. }> Req<..R> {
    fun route(self) -> i64 { self.data.host * 10 }
}

extend<row R: { host: i64, token: i64, .. }> Req<..R> {
    fun signed(self) -> i64 { self.data.host * 1000 + self.data.token }
}

fun strip_token<row R, row Rest>(r: Req<..R>) -> (i64, Req<..Rest>)
where R = { token: i64, ..Rest }
{
    let { token, ..rest } := r.data;
    (token, Req { data = rest })
}

fun main() {
    let base := add_host(empty(), 7);
    assert(base.route() == 70);

    let full := add_token(base, 42);
    assert(full.signed() == 7042);

    let stripped := strip_token(full);
    assert(stripped.0 == 42);
    assert(stripped.1.route() == 70);
    println("request ok");
}
```

With this RFC:

```metel
// A typed request builder: each step changes the row, and methods exist only once the
// fields they need are present.
record Req<row R> { data: {| ..R |} }

fun empty() -> Req<..{| |}> { Req { data = {| |} } }

fun add_host<row R: !{| host |}>(r: Req<..R>, h: i64) -> Req<..{| host: i64, ..R |}> {
    Req { data = {| host = h, ..r.data |} }
}

fun add_token<row R: !{| token |}>(r: Req<..R>, t: i64) -> Req<..{| token: i64, ..R |}> {
    Req { data = {| token = t, ..r.data |} }
}

extend<row R: {| host: i64, .. |}> Req<..R> {
    fun route(self) -> i64 { self.data.host * 10 }
}

extend<row R: {| host: i64, token: i64, .. |}> Req<..R> {
    fun signed(self) -> i64 { self.data.host * 1000 + self.data.token }
}

fun strip_token<row R, row Rest>(r: Req<..R>) -> (i64, Req<..Rest>)
where R = {| token: i64, ..Rest |}
{
    let {| token, ..rest |} := r.data;
    (token, Req { data = rest })
}

fun main() {
    let base := add_host(empty(), 7);
    assert(base.route() == 70);

    let full := add_token(base, 42);
    assert(full.signed() == 7042);

    let stripped := strip_token(full);
    assert(stripped.0 == 42);
    assert(stripped.1.route() == 70);
    println("request ok");
}
```

### Event reducer

A `type` alias for a nested record, field updates through a `&var` parameter, and record literals inside enum-driven `match` arms.

Today:

```metel
// An event reducer: one record of counters updated in place through a `&var` parameter,
// and a second record accumulated through a helper.
enum Event { Click { x: i64, y: i64 }, Key { code: i64 }, Tick }

type Stats := { clicks: i64, keys: i64, last_key: i64, ticks: i64, last: { x: i64, y: i64 } };

fun apply(s: &var Stats, e: Event) {
    match (e) {
        Event::Click { x, y } => {
            s.clicks := s.clicks + 1;
            s.last := { x = x, y = y };
        },
        Event::Key { code } => {
            s.keys := s.keys + 1;
            s.last_key := code;
        },
        Event::Tick => {
            s.ticks := s.ticks + 1;
        },
    }
}

fun note(seen: &var { n: i64, sum: i64 }, v: i64) {
    seen.n := seen.n + 1;
    seen.sum := seen.sum + v;
}

fun main() {
    var state: Stats := { clicks = 0, keys = 0, last_key = 0, ticks = 0, last = { x = 0, y = 0 } };
    var events: List<Event> := List::new();
    events.push(Event::Click { x = 3, y = 4 });
    events.push(Event::Key { code = 65 });
    events.push(Event::Tick);
    events.push(Event::Click { x = 9, y = 1 });

    var i := 0;
    while (i < events.len()) {
        apply(&var state, events.get(i).unwrap_or(Event::Tick));
        i := i + 1;
    }

    var seen := { n = 0, sum = 0 };
    note(&var seen, state.last.x);
    note(&var seen, state.last.y);

    assert(state.clicks == 2);
    assert(state.keys == 1);
    assert(state.last_key == 65);
    assert(state.ticks == 1);
    assert(state.last.x == 9);
    assert(seen.n == 2 && seen.sum == 10);
    println("events ok");
}
```

With this RFC:

```metel
// An event reducer: one record of counters updated in place through a `&var` parameter,
// and a second record accumulated through a helper.
enum Event { Click { x: i64, y: i64 }, Key { code: i64 }, Tick }

type Stats := {| clicks: i64, keys: i64, last_key: i64, ticks: i64, last: {| x: i64, y: i64 |} |};

fun apply(s: &var Stats, e: Event) {
    match (e) {
        Event::Click { x, y } => {
            s.clicks := s.clicks + 1;
            s.last := {| x = x, y = y |};
        },
        Event::Key { code } => {
            s.keys := s.keys + 1;
            s.last_key := code;
        },
        Event::Tick => {
            s.ticks := s.ticks + 1;
        },
    }
}

fun note(seen: &var {| n: i64, sum: i64 |}, v: i64) {
    seen.n := seen.n + 1;
    seen.sum := seen.sum + v;
}

fun main() {
    var state: Stats := {| clicks = 0, keys = 0, last_key = 0, ticks = 0, last = {| x = 0, y = 0 |} |};
    var events: List<Event> := List::new();
    events.push(Event::Click { x = 3, y = 4 });
    events.push(Event::Key { code = 65 });
    events.push(Event::Tick);
    events.push(Event::Click { x = 9, y = 1 });

    var i := 0;
    while (i < events.len()) {
        apply(&var state, events.get(i).unwrap_or(Event::Tick));
        i := i + 1;
    }

    var seen := {| n = 0, sum = 0 |};
    note(&var seen, state.last.x);
    note(&var seen, state.last.y);

    assert(state.clicks == 2);
    assert(state.keys == 1);
    assert(state.last_key == 65);
    assert(state.ticks == 1);
    assert(state.last.x == 9);
    assert(seen.n == 2 && seen.sum == 10);
    println("events ok");
}
```

What the examples show:

- Every record literal, pattern, type, bound and equation gains two delimiter characters; 35 groups
  across the three programs. Blocks, named literals and variant literals do not change.
- The empty record is `{| |}` where `{}` is today; `Req<..{}>` becomes `Req<..{| |}>`.
- Nested record types (`last: {| x: i64, y: i64 |}`) stay readable because the bars distinguish them
  from blocks at every depth.
- No example needed the `({ x = 1 })` parenthesization workaround today, because each record sits in a
  pure-expression position or has more than one field. The single-field cases the workaround exists for
  are the ones RFC-0183 would otherwise make ambiguous (`{ x = 1 }` as an assignment tail).

---

## Alternatives Considered

### Delimiters

| Option | Record | Verdict |
|---|---|---|
| `{\| … \|}` | `{\| x = 1 \|}` | **Proposed.** Stays in the `{ }` family, covers the empty record, keeps `x` plain. Two characters heavier than today. |
| Field prefix only | `{ .x = 1, .y = 2 }` | Makes a field never start a block, but leaves `{ }` as an empty block, so the empty record needs its own spelling. Marks every field of every literal, and `.x` next to the rest `..r` is a one-dot slip. Declined as the record delimiter; the dot is kept for labels (RFC-0188). |
| `#{ … }` | `#{ x = 1 }` | Unambiguous and light. Declined only because RFC-0175's open question 2 lists `#field` as a label literal form, which would give `#` two meanings. Reconsidered if label literals (RFC-0188) are not `#`-based. |
| `%{ … }` | `%{ x = 1 }` | `%` is the remainder operator. |
| `[\| … \|]` | `[\| x = 1 \|]` | Brackets suggest arrays and capture lists. |
| `(\| … \|)` | `(\| x = 1 \|)` | Parenthesized closures, `(\|x\| x + 1)`, are common, so it collides far more often than `{\|` does. |
| `.{ … }` | `.{ x = 1 }` | Clashes with the `..{` row-literal splice (RFC-0180), `...{`, and with RFC-0099 dot paths. |
| `record { … }` | `record { x = 1 }` | Consistent with named literals, but heavy in every signature. |
| Parser rules, no token | `{ x = 1 }`; `{ x, }` for one pun | Make assignment a statement only, so it cannot be a block tail, and require a trailing comma for a single pun. Changes what some existing blocks mean (a body that is a single unterminated assignment). RFC-0183's review measured it: no fixture ends a block with an assignment lacking `;`, so it is viable if this RFC is declined. |
| Labeled tuple | `(x = 1, y = 2)` | Collides with RFC-0100's keyword-argument calls and with a parenthesized assignment. |
| Keep the status quo | parenthesize in block positions | Keeps the rule the feedback objected to. |

---

## Prior art

| Language | Relevant form |
|---|---|
| Rust | Struct literals are prefixed with a type path (`Point { x: 1 }`) and parenthesized in conditions, which is how Metel's *named* literals already avoid the problem. There is no anonymous record. |
| Zig | Anonymous struct literal `.{ .x = 1 }` with `.field` entries. Both its `.{` and its field prefix are the options weighed above. |
| Erlang | Map literal `#{ k => v }`. |
| Elixir | Map literal `%{ k => v }`. |
| OCaml | `{\| … \|}` is a quoted-string delimiter there, so its use is unrelated and creates no confusion in Metel. |
| Swift | Labeled tuples `(x: 1, y: 2)`. |

---

## Interactions

- **RFC-0116 (Anonymous Record Types):** the block-versus-record rule and the `({ x = 1 })`
  workaround are removed; the type-former, punning, projection and identity rules are unchanged.
- **RFC-0120 (Named Records), RFC-0137, RFC-0117 (Row Narrowing):** semantic content unchanged.
  Only the surface of their examples changes. `record T` and `Point { … }` keep their forms.
- **RFC-0121 (Open Rows), RFC-0178 (Row Remainder Construction), RFC-0180 (Literal rows in row
  arguments):** row bounds, equations, `..R` tails, spreads and rest patterns change delimiters only.
  The row kind and `Name<..R>` argument forms are RFC-0186's.
- **RFC-0183 (Initialization-only `:=`):** plain assignment becomes `=`. This RFC removes the
  `{ x = 1 }` record-versus-block collision that would otherwise need RFC-0183 to forbid an
  assignment as a block's tail. RFC-0183 does not depend on this RFC, but is simpler with it.
- **RFC-0186 (Rows as an operator on record parameters) and RFC-0188 (Label syntax):** both build on
  these delimiters and are independent in meaning.
- **RFC-0099 (dot-separated paths) and RFC-0100 (keyword-argument construction):** a record in
  `{| |}` never starts a path or a call argument; RFC-0100 is the reason parenthesized labeled
  tuples were declined.

---

## Migration

This is a breaking, language-visible change and so at least a minor version when it ships, never a
patch. It is mechanical:

- Every anonymous record literal, pattern, type, row bound, row equation and row-literal argument
  changes outer delimiters. A rough grep of the integration fixtures finds on the order of 80
  anonymous record literal lines and 180 record-type annotation lines, plus the spec, the tutorials,
  the blog posts and the examples inside RFCs.
- A parse-based rewriter produces the new forms, so the migration is not a hand edit. A literal like
  `{ x = 1 }` is a record only in positions where it parses as one today; the rewriter must emit
  `{| x = 1 |}` for exactly those, and leave blocks alone.
- Transition policy is open question 2.

Timing matters: the published records post and the tutorials teach the current syntax, and the
core surface freeze would fix whatever is current at that point. Deciding before the freeze avoids
a post-freeze break.

---

## Changes on Acceptance

- `grammar.pest` and the generated `grammar.md`: `record_lit`, `record_pattern`, `record_type`,
  `open_record_type`, `row_bound`.
- Spec: types (records, open rows), expressions (record literals), patterns, and the removal of the
  block-wins paragraph.
- RFC-0116, RFC-0120, RFC-0121, RFC-0178 and RFC-0180 examples updated.
- Fixtures: the corpus migrated by the rewriter; new fixtures for each position, the closure-first
  block, and the empty record.
- Tutorials and blog examples updated, with the published records post revised or annotated.

---

## Open Questions

1. **Types and bounds:** should `{| … |}` apply in type and bound position (as written here, one
   rule everywhere), or only to literals and patterns, with types and bounds keeping `{ … }`
   because no block can occur there? The cost of the uniform rule is weight in signatures; the
   benefit is `-> {| x: i64 |} { … }` no longer reading as two brace groups.
2. **Transition:** one release where the old forms still parse in unambiguous positions with a
   deprecation diagnostic, or a hard break with the rewriter? The project has no warning channel
   today, so a deprecation would be an error with a suggested rewrite.
3. **Empty-record spelling:** `{| |}` only, or also `{||}`? Recommended `{| |}` as canonical, with
   `{||}` a parse error to keep the closure edge case quiet.
4. **Sequencing with RFC-0183:** implement this RFC first, so that RFC-0183 needs no rule to keep
   records and blocks apart (its statement-only rule then rests on the `f(x = 1)` and
   `if (x = 1)` hazards alone, RFC-0183 §5); or let RFC-0183 ship first with its tail-assignment
   rules and relax them when this lands. Recommended: this RFC first.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- A grammar prototype of `{| … |}` parses the whole integration corpus after the rewriter runs,
  and a differential run shows identical results to the current syntax.
- No input is accepted both as a block and as a record.
- The closure-first block `{|x| x + 1}` and `{| f = |x| x + 1 |}` both parse as intended.

---

## References

- RFC-0116 — Anonymous Record Types (the block-versus-record rule).
- RFC-0120 — Named Records; RFC-0117 — Row Narrowing.
- RFC-0121 — Open Rows; RFC-0137 — Branded rows.
- RFC-0178 — Row Remainder Construction; RFC-0180 — Literal rows in row arguments.
- RFC-0183 — Initialization-Only Walrus (plain assignment on `=`).
- RFC-0186 — Rows as an operator on record parameters; RFC-0188 — Label syntax (split out of this RFC).
- RFC-0099 — Dot-separated module paths; RFC-0100 — Constructor-call construction.

---

## Decision

**Outcome:** *(pending)*
