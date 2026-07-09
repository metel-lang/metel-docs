---
id: rfc-0012
title: "Attributes, Metadata, Macros, and Derived Aspects"
date: '2026-05-21'
updated: '2026-07-09'
status: draft
target:
---

> **Rewritten 2026-07-09.** Previously presented four implementation paths for derive
> with no preference among them. This revision recommends **Path D — comptime derive**
> as the primary mechanism and rewrites the RFC around it; Paths A/B/C are kept as
> alternatives considered, not as live options of equal standing. This followed a
> Zig-style comptime design discussion in `reports/substructural-types/`, which also
> surfaced that `typeinfo`'s struct-describing arm should reuse the row concept from
> `structural-records.md` rather than invent a parallel descriptor type — folded in
> below. RFC-0080 (Standard Library Aspects) was moved back from accepted to
> under-review the same day: its §1.3 had specified `Clone` derive using
> `#[derive(Clone)]`, a syntax this RFC's Alternatives Considered section explicitly
> rejects. §1.3 now uses `derives Clone` (this RFC's chosen surface syntax) provisionally;
> RFC-0080 is blocked on this RFC's decision, not the reverse.
>
> **Updated 2026-07-09 (same day).** Folded in a full pass on whether comptime derive
> also closes the RFC's original, still-open "does Metel need a general macro system"
> question. It mostly does: generalizing `emit` to multiple declarations and to
> expression position (§4), plus exposing Metel's own parser as a comptime-callable
> function over strings (§5), covers nearly everything a macro system is normally for —
> including cases previously written off as categorically out of reach. What remains is
> narrower than "macros are still open": span-tracked diagnostics for comptime-parsed
> strings (§6), and a short list of genuinely unclosed residual cases (§5). The Macros
> subsection of Motivation, the Lisp-style-macros alternative, and the open questions are
> rewritten accordingly.

## Summary

This RFC proposes **comptime derive** as Metel's mechanism for automatically generating
aspect implementations: derive is not a special compiler feature, but ordinary code —
written in Metel itself — that runs at compile time over a reflected description of a
type's structure and emits a coherence-checked `impl` block. This follows Zig's
`comptime` model directly: there is no separate macro language, no token stream, no
hygiene problem, because compile-time code and run-time code are the same language,
staged differently. It requires two things new to Metel: `type` as a first-class
comptime value, and a reflection primitive over it.

This does not replace the rest of the meta-feature layer. The `@` attribute/metadata
system (`@inline`, `@cfg`, `@allow`, `@doc`) remains in scope, unaffected — those are
compiler hints and conditional compilation, not code generation, and gain nothing from
comptime.

What comptime derive does replace turns out to be larger than just derive's own
extensibility. Generalizing `emit` to produce more than one declaration, and to
splice an expression at its call site rather than only a top-level declaration
elsewhere (§4), plus exposing Metel's own parser as an ordinary comptime-callable
function over string values (§5), covers nearly every case this RFC previously listed
under "general macro system, still open" — repetitive declaration generation,
compile-time-validated embedded DSLs, and even pattern-as-argument macros
(Rust's `matches!`), all without a token-stream grammar, a macro-invocation syntax
form, or a hygiene system to design. What's left over (§5, §6) is a short, named list —
not an open-ended deferred feature.

All features in this RFC remain tentatively deferred to **v0.5+**, after the core
language (generics, aspects, concurrency, memory model) is stable — comptime derive
specifically also requires `type`-as-value and reflection to exist first, which is new,
non-trivial design surface in its own right (see Open Questions).

---

## Motivation

### Derived aspect implementations

Writing `impl Eq for Point { fun eq(self, other: Point) -> boolean { self.x == other.x && self.y == other.y } }` by hand for every struct is tedious and error-prone. A derive mechanism generates these implementations structurally — field-by-field for structs, variant-by-variant for enums. The primary use cases are `Eq`, `Ord`/`Comparable`, `Display`, `Clone`, `Hash`, and `Linear` (for types that are linear by structure rather than explicit declaration).

The question this RFC exists to answer is not *whether* derive is useful — that much is
uncontested and already assumed by RFC-0080 — but *what kind of mechanism* generates
the impl: a closed list the compiler special-cases, or open code that anyone can write.

### Attributes and metadata

Beyond derive, a general attribute/metadata system enables:
- Compiler hints (`@inline`, `@cold`, `@must_use`)
- Conditional compilation (`@cfg(...)`)
- FFI annotations (`@extern("C")`)
- Lints and suppressions (`@allow(...)`, `@deny(...)`)
- Documentation metadata (`@doc(...)`)

Without a principled attribute syntax, these accumulate as ad-hoc keywords or magic comments. A single syntax form (`@`) handles all of them uniformly. This part of the RFC is independent of the derive mechanism and is unaffected by the Path D recommendation below.

### Macros — mostly closed by comptime, not just superseded for derive

A general macro system enables syntactic abstraction — generating code from a compact
notation, operating on unexpanded syntax. Comptime derive (Path D) gets derive's
extensibility without one, and — once `emit` is generalized (§4) and Metel's parser is
exposed as a comptime-callable function (§5) — it reaches most of what a macro system is
normally reached for, not only derive:

- **Repetitive declaration generation** (one getter per field, one match arm per
  variant, builder-pattern boilerplate) — a loop over `typeinfo(T).row` emitting one
  declaration per iteration. No grammar needed; this is ordinary comptime control flow.
- **Compile-time-validated embedded DSLs** (a `sql("SELECT ...", id)` that parses and
  type-checks its query string at compile time) — a comptime function receiving a
  string literal and parsing it with an exposed grammar production, producing a value
  or a type. No foreign parser integration or macro-invocation syntax needed.
- **Pattern-as-argument macros** (Rust's `matches!(expr, Pattern::Variant(x) if x > 0)`)
  — previously assumed to need genuine syntax-level macros. It does not: a comptime
  function parses the pattern from a string using the same exposed grammar, then emits
  an expression *at the call site* (§4), evaluated against the caller's own locals.
  Because the parsed text is spliced back at the exact position the caller wrote it,
  there is no cross-scope identifier injection and therefore no new hygiene problem to
  solve — the caller's `x` binds exactly where they typed it.

What remains is a short, specific list, not "everything else is still open": tooling
ergonomics for DSL text embedded in string literals (§6, closable with span-tracked
comptime strings), auto-capturing a caller's own source text without them retyping it
as a string (a narrow, separately addressable ask), and genuinely bare, unquoted foreign
syntax appearing directly in Metel source with no call-syntax wrapping at all (the one
case that is structurally out of reach — Zig does not support this either). None of the
three motivate a token-stream/hygiene macro system on their own.

---

## Proposal: Comptime Derive (Path D)

Derive is an ordinary function that runs at compile time (`comptime`) over a reflected
description of a type's structure and produces an `impl` block as a value the compiler
registers. There is no macro grammar, no token stream, no hygiene problem — comptime
code is the same language as runtime code, staged earlier, because the same evaluator
runs it.

### 1. Generics as comptime sugar

A `type` (e.g. `Point`, `i64`, `Perhaps<T>`) can be bound, passed, and returned like any
other comptime-known value. This is also the natural explanation for Metel's existing
`<T>` generics (spec: `public/reference/spec/types.md`, "Generics"): Zig does not have
`<T>`-style generics as a mechanism separate from comptime — `fun first(comptime T: type, arr: T[])`
*is* how Zig spells a generic function, because a compile-time-known `type` parameter
is just an ordinary parameter, staged. Under Path D, `fun first<T>(arr: T[])` is sugar
over the same comptime type-parameter mechanism, rather than a second,
independently-specified feature living alongside it.

This is worth more than a passing mention, because it isn't a free-standing design
choice — it interacts with two things Metel's generics already commit to in accepted
RFCs, one confirming the unification and one in tension with it.

**Monomorphization is already assumed, not a retrofit.** RFC-0008 (Aspect Objects,
accepted) draws its entire dynamic-dispatch proposal as a contrast against an existing
default: "Static dispatch (generics + monomorphisation) requires the concrete type to
be known at compile time... a function accepting `impl Aspect` is monomorphised per
caller type." That is exactly what comptime-parameter semantics produce: a distinct,
compile-time-known `T` triggers a fresh evaluation of the function body specialized to
that `T`, i.e. monomorphization, by construction, with no separate codegen step to
design. Adopting Path D for generics doesn't change Metel's dispatch model — it gives
the model RFC-0008 already assumes an actual mechanism, rather than leaving
"monomorphisation" as an unexamined word every generics-adjacent RFC (RFC-0008,
RFC-0036, RFC-0037, RFC-0061, RFC-0072, RFC-0082) currently relies on without
specifying how it happens.

**Bound-checking timing is a real tension, not a free unification.** RFC-0061
(Structural Aspect Bounds, accepted) already assumes a *bound checker*: aspect bounds
like `T: Display` are checked with "a precise diagnostic" when a bound cannot be
satisfied, implying failures are caught systematically against the bound, not merely
wherever a missing method happens to be called. Zig's actual comptime generics have no
equivalent: there is no bound-checking layer at all. A Zig generic function's body is
type-checked only once instantiated with a concrete `T`; a call to a method that `T`
does not provide fails at the use site, deep inside that specific instantiation,
frequently with an error pointing into generic library code rather than at the caller
who chose an unsuitable `T`. This is a well-known, deliberate ergonomic trade in Zig (simplicity of
"just duck-type it") that Metel's aspect system has already rejected in favour of
checked bounds. Adopting Path D's *execution model* for generics does not require
adopting Zig's *checking discipline* along with it — but naming them as "the same
mechanism" without saying so risks implying it does.

**Recommendation:** keep `<T: Clone>`-style bounds checked structurally at the generic
function's own definition, as RFC-0061 already establishes for structural types —
implemented as a constraint verified against `typeinfo(T)` and aspect-impl lookups
*before* any instantiation is permitted, not as a property only discovered during
comptime evaluation of the body. Concretely:

```metel
fun first<T: Clone>(arr: T[]) -> Perhaps<T> {
    // comptime T: type, with `T: Clone` checked against typeinfo(T)/impl lookup
    // at this definition, exactly as RFC-0061's bound checker already does today —
    // not deferred to whichever call site happens to instantiate T
    if (array_len(arr) == 0) { return None; }
    return Perhaps::Some { value: arr[0] };
}
```

This gets Metel Zig's single-execution-model economy (one evaluator, staged, no
separate generics-codegen machinery to specify) without Zig's weaker error locality.
The cost is that this checked layer is itself new design work: neither Zig (which has
no such layer) nor RFC-0061 (which specifies checked bounds but not a comptime
substitution mechanism underneath them) hands it over pre-assembled. Designing exactly
how bound-checking composes with comptime substitution — a distinct compiler pass
before evaluation, or a comptime-expressible assertion the aspect system inserts
automatically — is tracked as Open Question 3 below.

### 2. Reflection: `typeinfo(T)`, and its relationship to structural records

`typeinfo(T)` (Zig calls its equivalent `@typeInfo`) returns an ordinary, inspectable
comptime value describing `T`'s shape. `@` is not reused for this name because `@`
already denotes allocators in Metel (RFC-0063 and the allocator-handle cluster);
colliding an established sigil with an unrelated meaning is worth avoiding even though
Zig itself overloads `@` for both.

`typeinfo` cannot be a single record type, because different kinds of type have
different shapes to describe — a struct has fields, an enum has variants, a primitive
has a bit width and signedness. That is a sum type, which is what Metel's enums are
for:

```metel
enum TypeInfo {
    Struct { row: Row },
    Enum { variants: (name: Symbol, fields: Row)[] },
    Int { bits: i64, signed: boolean },
    Float { bits: i64 },
    Pointer { target: type },
    // ...
}
```

The `Struct` arm's payload, however, is exactly what `structural-records.md`'s **row**
concept already models: a name-to-type mapping, already used there for `HasField`/`Lacks`
bound satisfaction and Tier 2/3 record conversion. Rather than invent a parallel
`FieldInfo[]` descriptor type for reflection, the struct arm of `typeinfo` should return
`T`'s own row, reified as a comptime value. This gives one concept spanning two phases:
`typeinfo` inspects the row at comptime; `ToRecord`/`FromRecord` (structural-records.md
Tier 2) converts to/from a value of that row at runtime. A derive function and a
runtime record-conversion are, underneath, working with the same fact about `T`.

This reuse is not free, and surfaces two gaps neither document currently resolves:

- **Rows may need metadata they don't currently carry.** Rows as scoped in
  `structural-records.md` are presence facts — name/type pairs — used for bound
  satisfaction and conversion, where declaration order and per-field visibility don't
  matter. Reflection likely needs both: order, for deterministic codegen (a derived
  `Clone` or `Display` needs a stable field order, not whatever order a set happens to
  iterate in); visibility, to decide whether a comptime function defined outside a
  type's module should see its private fields at all. Whether this means extending the
  row concept itself with this metadata, or defining a reflection-only superset of it,
  is open.

- **Reflection and the tier system are orthogonal, not layered.** Reflecting a
  struct's shape at comptime grants no *runtime* capability — it is compile-time only,
  in the same category `structural-records.md` §8 already resolved for `HasField`-as-
  bound: implicit, available on any struct, regardless of tier. `typeinfo` must work on
  plain Tier-1 structs — RFC-0080's own `Point` (§1.3) is a plain struct, and its
  `Clone` derive example requires reflecting it — even though Tier 1 structs never
  opt into `ToRecord`/`FromRecord` at runtime. Comptime reflection therefore should not
  be gated behind the tier-2/3 opt-in that governs runtime record conversion; the two
  mechanisms answer different questions (what does `T` look like at compile time, vs.
  what can be done with a value of `T` at runtime) and should stay decoupled.

### 3. Emitting the impl

Comptime code needs a way to **emit a declaration** — specifically, a coherence-checked
`impl Aspect for T` — as a side effect of compile-time evaluation, not just compute a
value or a type. This is the one genuine extension beyond Zig's own model: Zig has no
nominal aspect/impl/coherence system to target (a Zig "generic" function returning a
`type` returns a struct with its methods already inside it), so Zig itself never had to
solve "synthesize an impl of an existing nominal aspect for an existing type." Metel's
aspect system means this is new design work, not a transplant, and it is where this
RFC's soundness questions concentrate (see Open Questions): does normal orphan-rule/
coherence checking (RFC-0060) apply unchanged to an emitted impl? Can a comptime
function emit an impl for a type it does not own?

### 4. Emitting more than one declaration, and at expression position

Derive only ever needs `emit` to produce a single `impl` block. Reaching the macro-like
use cases in Motivation needs two generalizations of the same primitive, neither of
which changes what kind of thing `emit` fundamentally does — a side effect of
compile-time evaluation that registers a checked declaration:

- **Multiple declarations from one comptime function.** `emit` inside a loop over
  `typeinfo(T).row` can run once per field, each iteration emitting its own
  declaration (a getter function, a match arm, a builder method). This requires no new
  concept — ordinary comptime control flow around an `emit` that was always going to
  run zero or more times, not exactly once.

- **Expression-position `emit`.** Rather than registering a declaration to live
  elsewhere, comptime code can produce an expression that is spliced back in *at its
  own call site*, evaluated in the caller's lexical scope against the caller's own
  locals. This is the piece that makes pattern-as-argument macros (§5) possible: a
  comptime function receiving `"Variant(x) if x > 0"` as a string can parse it and emit
  the resulting pattern expression back into the `match` the caller wrote, binding `x`
  exactly where the caller's own code expects it. Because the splice target is the same
  textual position the caller invoked from — not some other scope the macro expansion
  reaches into — this does not reintroduce the identifier-capture hygiene problems
  syntax-level macros are known for; the caller's own scoping rules apply unchanged.

### 5. Comptime-callable parsing: closing most of the remaining gap with macros

The other piece needed is exposing Metel's own parser as an ordinary function callable
from comptime code — parsing a string value into a pattern, expression, or (subject to
Open Question 11) other grammar productions, rather than requiring a macro-invocation
syntax form that operates on unexpanded surrounding tokens.

```metel
comptime fun matches_str(comptime pat: string, expr: T) -> boolean {
    let parsed = parse_pattern(pat);   // Metel's own pattern grammar, comptime-callable
    emit match expr {
        parsed => true,
        _ => false,
    }   // expression-position emit (§4): spliced back at the call site
}
```

```metel
comptime fun sql(comptime query: string, params: ...) -> QueryResult {
    let validated = parse_sql(query);   // validated at compile time against schema
    // ordinary comptime code computing a result type/value from `validated`
}
```

Both read a string the caller wrote directly as an argument — not raw, unexpanded
surrounding syntax the way a syntax-level macro would receive it — and both produce
either a value/type (the `sql` case) or a spliced-back expression via §4 (the
`matches_str` case). Neither needs a macro grammar, a separate expansion phase, or
hygiene machinery: it is a function call with a string-literal argument, using the same
`comptime`/`emit`/`type`-as-value pieces already proposed above.

**What this does not close**, honestly: an embedded DSL inside a string literal loses
editor syntax highlighting and autocomplete even when the compiler validates it
correctly (§6 addresses diagnostics, not highlighting, directly); auto-capturing a
caller's own literal source text without them retyping it as a string (Rust's `dbg!`
printing both a value and its literal expression text) is a separate, narrower ask this
does not provide by itself; and genuinely bare, unquoted foreign syntax appearing
directly in Metel source (no wrapping call, no quotes) is structurally out of reach,
because it requires the parser to accept something other than Metel's own grammar at
that exact position — which comptime, operating strictly after Metel's own parse
completes, cannot do. Zig does not support this case either.

### 6. Span-tracked comptime strings and diagnostics

Good error messages for a comptime-parsed string need more than "the call to `sql(...)`
on line 10 failed" — they need to point at the exact offset inside the string literal
where parsing broke. This requires the compiler to preserve, for any string value
originating from a literal at a comptime-known source location, a mapping from
byte-offset-within-the-string back to absolute source position, and a span-aware
error-reporting primitive (e.g. `compileError(msg, at: span)`) that the exposed parser
(§5) can call using spans it already tracks internally while walking the string.

This also happens to be the same primitive an LSP would need to offer semantic
highlighting for embedded DSL text — by invoking the same comptime-exposed parser
interactively over a string literal's known span and mapping the resulting tokens back
to editor ranges. That is downstream tooling architecture, not something this RFC
specifies, but it rests on nothing beyond the span-tracking this section already needs
for diagnostics.

**A real limit, not a hand-wave:** this works cleanly only for strings that are literals
typed directly at the call site. A string built up via comptime concatenation or
`format`-style assembly from multiple pieces has no single contiguous source range the
final value corresponds to, so span attribution degrades or disappears — mirroring a
well-known limitation in existing macro/DSL tooling (a literal format string gets
precise diagnostics; a dynamically assembled one usually does not).

### 7. Body reflection: a plausible but much larger extension, not proposed here

`typeinfo(T)` reflects a *type's* shape — a flat row of (name, type) pairs, a handful
of enum arms. It is natural to ask whether the same idea extends to a *function's own
body*: a `bodyinfo(f)`-style value exposing its statements, expressions, and control
flow to comptime code, for uses like linting, custom style-rule enforcement, or
security auditing ("does this function call an unsafe operation").

This does not belong in this RFC's proposed mechanism, for two separate reasons, and is
recorded here only as a scoped, deliberately-not-designed open question:

- **It is a much larger reflection surface than `typeinfo`.** A type's shape is a flat
  set of fields; a function body is arbitrarily nested expressions, control flow,
  closures, pattern matches. Where `TypeInfo` (§2) has a handful of arms, a body
  representation would need to cover every expression and statement form in the
  grammar — closer to exposing the compiler's own AST than to `typeinfo`'s narrow,
  purpose-built shape.

- **The motivating use case — auditing for a property like "performs IO" or "uses
  unsafe" — is a transitive, whole-call-graph question that body reflection cannot
  actually answer, regardless of how much of it gets built.** Checking "does this
  function, or anything it calls, do X" requires walking into every callee, and RFC-0008
  (Aspect Objects) already establishes that a `dyn Aspect` method call's concrete callee
  is not known until runtime. Auditing cannot walk into a call it cannot resolve at
  compile time — this is not a design gap more comptime power closes, it is what dynamic
  dispatch means by definition. The properly-scoped mechanism for exactly this
  motivation is an effect system, not source inspection: `reports/substructural-types/algebraic-effects.md`
  §11.1 already works through IO as a tracked effect, checked and propagated through a
  function's *signature*, compositionally, and (because the obligation lives on the
  aspect's interface contract rather than requiring the compiler to inspect whatever
  concrete type shows up at a `dyn` boundary) does not hit the same dynamic-dispatch
  wall that defeats body reflection for this purpose.

If Metel ever wants shallow, non-transitive body reflection for its own sake (custom
lints, style-rule enforcement scoped to a single function's own written code, not its
transitive callees), that remains a legitimate, separate design question — just not one
this RFC scopes or proposes a mechanism for.

### Worked example

```metel
comptime fun derive_clone(comptime T: type) {
    let fields = typeinfo(T).row;   // T's row, reified as a comptime value
    emit impl Clone for T {
        fun clone(self: &T) -> T {
            // built field-by-field from `fields` by ordinary comptime code —
            // a loop generating a constructor expression, not a macro template
        }
    }
}
```

Surface syntax at the call site stays exactly what RFC-0080 §1.3 already uses
provisionally: `struct Point derives Clone { x: f64, y: f64 }`. `derives Clone` parses
as Path C's syntax and resolves to a standard-library comptime function per Path D —
closed-list ergonomics today, with an open path to user-defined derivable aspects later,
with no syntax change required when that lands.

### Pros and cons

**Pros:** open/extensible like Path B (any library can write a comptime function that
emits an impl), without Path B's macro-hygiene and token-stream complexity — there is
only one language, not two. Subsumes the `linear` keyword vs. derive question (Open
Question 6) for free: `derives Linear` becomes an ordinary comptime function inspecting
field linearity via `typeinfo`, not a special case. Unifies with `<T>` generics rather
than sitting beside them as an unrelated feature. Reaches most of what a general macro
system (Path B, and the "Lisp-style macros" alternative below) would have been for,
covered by §4/§5 instead of a second grammar/expansion/hygiene system — a much larger
scope reduction than "derive doesn't need macros" alone.

**Cons:** requires `type` to become a first-class comptime value and a reflection
primitive over it — both new to the language, not currently specified anywhere in the
type system (`public/reference/spec/types.md`'s "Generics" section has no notion of
`type`-as-value). Emitting a coherence-checked impl from arbitrary user code raises
soundness questions not yet worked out. Larger design surface than Path A or C in
isolation, though smaller than a full Path B macro system, and the row-reuse in §2
above is itself not yet fully specified (ordering, visibility). Reaching macro-like
expressivity (§4/§5) adds its own new surface on top of derive alone: expression-position
`emit`'s scoping rules, a comptime-callable parser's API shape, and span-tracked string
provenance for diagnostics (§6) — none of these are needed for derive by itself, and all
are presently unspecified beyond the sketch above.

---

## Derivable Aspects (initial standard-library set)

Regardless of how much of Path D's extensibility ships initially, the standard library
should provide comptime derive functions for at least:

| Aspect | Behaviour |
|---|---|
| `Eq` | Field-by-field equality |
| `Ord` / `Comparable` | Lexicographic field ordering |
| `Display` | Structural `to_string` (see Open Question 3) |
| `Clone` | Deep field-by-field clone (RFC-0080 §1.3) |
| `Hash` | Structural hash combining all fields |
| `Linear` | Marks the type linear if all fields are linear (see RFC-0024) |

Under Path D, `Linear` as a derivable aspect is not merely an alternative to the
`linear` keyword — it is the same mechanism as the others, an ordinary comptime
function reading `typeinfo(T)` and checking each field's linearity, rather than a
bespoke compiler rule.

---

## Preferred Syntax: `@`, for non-derive attributes

The preferred grammar symbol for attributes and metadata *other than derive* is `@`.
This is distinct from all current Metel operators and consistent with annotation syntax
in several modern languages (Java, Python decorators, Zig's `@builtins`).

```metel
struct Point derives Clone, Eq {
    x: Float,
    y: Float,
}

@inline
fun fast_path(n: Int) -> Int { n * 2 }

@cfg(target = "linux")
fun platform_init() { ... }

@allow(unused)
let _debug_value = compute();
```

Multiple attributes stack vertically, one per line, before the item they annotate.
Attributes apply to the next declaration or binding — they do not apply to
expressions. Derive uses `derives`, not `@derive(...)` — see Proposal above.

The `@` form is preferred over Rust's `#[...]` because:
- `#` is visually associated with comments in many languages; `@` is unambiguously an annotation sigil
- `@` is already unused in Metel's grammar (outside allocators, which use it in a different grammatical position)
- `@(...)` is unambiguous as a prefix — no bracket/brace confusion with other constructs

---

## Alternatives Considered

### Path A — Compiler-built-in derive (no macro system)

Derive is a closed set of structurally derivable aspects known to the compiler, with no
user extensibility. Simple to implement, guaranteed-correct, but third-party libraries
can never add derivable aspects. Superseded by Path D, which gets the same closed
initial set (see Derivable Aspects above) without foreclosing extensibility later.

### Path B — Attribute macros (procedural macros)

`@derive(Aspect)` expands to an `impl` block generated by a macro associated with
`Aspect` — Rust's model. Fully extensible, but procedural macros are notoriously
complex to write and maintain, and require a full macro system (token streams, hygiene)
as a prerequisite. Superseded by Path D, which reaches the same extensibility by
running ordinary staged code over reflected values instead of syntax.

### Path C — Derive as a language keyword, closed

Derive expressed with a `derives` keyword rather than the `@` attribute system, but
still a closed, compiler-known list with no extensibility:

```metel
struct Point derives Eq, Ord, Display { x: Float, y: Float }
```

Ergonomic and self-contained, but does not scale to user-defined derivable aspects.
Not superseded so much as **absorbed**: this is the exact surface syntax Path D uses,
with the compiler-known list becoming the standard library's initial comptime derive
functions rather than a hardcoded special case. Path C is what a user of Path D sees
before writing a custom derivable aspect.

### `#[...]` Rust-style attributes

Familiar to Rust programmers but visually ambiguous with comments (`#`). Rejected in
favour of `@`. (RFC-0080 §1.3 briefly used this syntax for `Clone`'s derive example;
corrected 2026-07-09 to `derives Clone`, consistent with this RFC.)

### Lisp-style macros (hygienic, syntax-level)

Full hygienic macro system allowing arbitrary syntactic transformation over unexpanded
syntax. Maximum power, maximum complexity — well outside the scope of a v0.5 feature
for a language at v0.1, and no longer motivated by derive specifically now that Path D
covers that case. More than that: §4/§5 above show that generalized `emit` plus a
comptime-callable parser already reaches repetitive declaration generation,
compile-time-validated embedded DSLs, and pattern-as-argument macros — the use cases
that would normally motivate reaching for this alternative in the first place. What
remains unreachable without it is narrow: genuinely bare, unquoted foreign syntax with
no call-site wrapping at all. Not ruled out for that one residual case, but no longer a
broad, open-ended future direction — a small, specific, likely-skippable gap.

### No attribute syntax — ad-hoc keywords only

Each compiler directive is its own keyword or syntax form. Avoids designing a general
system but leads to keyword proliferation and inconsistency. Rejected as a long-term
position; acceptable only before v0.5 when no attribute-dependent features have shipped.

---

## Interaction with Other RFCs

### `structural-records.md` (design report, not yet an RFC)

`typeinfo(T)`'s struct arm reuses the row concept defined there for `HasField`/`Lacks`
and Tier 2/3 record conversion (§2 above). This is the load-bearing dependency for Path
D's reflection design and is not yet reconciled in either direction — row ordering and
visibility metadata, needed for reflection, are not currently specified there either.

### RFC-0080 (Standard Library Aspects)

`Clone`'s derive (§1.3) is the concrete first test case for this RFC's mechanism.
RFC-0080 was moved back to under-review 2026-07-09 pending this RFC's resolution, and
currently spells derive as `derives Clone` provisionally, matching the syntax this RFC
recommends regardless of whether the underlying mechanism is Path C or Path D.

### RFC-0024 (Linear Types)

The `linear` keyword on struct/enum declarations could be replaced by `derives Linear`
resolving to a comptime function per Path D. The keyword form is simpler and available
sooner; the derive form is more uniform and consistent with every other derivable
aspect once Path D lands. Open question for RFC-0024's final form.

### RFC-0008 (Aspect Objects)

RFC-0008's entire proposal is framed as a contrast against an already-assumed default:
"static dispatch (generics + monomorphisation)." §1 above treats this as confirmation,
not tension — comptime type parameters produce monomorphization by construction, so
Path D's generics-as-comptime-sugar unification gives RFC-0008's assumed dispatch model
an actual mechanism rather than introducing a new one.

### RFC-0061 (Structural Aspect Bounds)

RFC-0061 already specifies a bound checker that rejects unsatisfiable aspect bounds
"with a precise diagnostic" — a checked-bounds discipline Zig's own comptime generics
do not have. §1 above recommends preserving RFC-0061's declaration-site checking as a
layer on top of comptime substitution rather than adopting Zig's use-site duck typing
wholesale; see Open Question 3 for the unresolved mechanics of that composition.

### RFC-0001 (Pointers) and RFC-0026 (Unsafe Blocks)

`@extern("C")` for FFI function signatures (RFC-0026 open question 4) uses the `@`
attribute syntax defined here. The attribute system is a soft prerequisite for a clean
FFI story; unaffected by the Path D recommendation.

### RFC-0009 (Module System)

`@pub`, `@cfg`, and documentation attributes interact with the module system's
visibility model. Also relevant to Path D directly: reflection's need for per-field
visibility (§2 above) means `typeinfo` and the module system's privacy rules are not
fully independent.

### RFC-0011 (Operator Overloading)

Deriving `Eq` and `Ord` generates implementations of the operator aspects. RFC-0011
must be accepted before derived `Eq`/`Ord` can be implemented, regardless of mechanism.

---

## Open Questions

1. **Row metadata for reflection.** Do rows need declaration order and per-field
   visibility added to their definition in `structural-records.md`, or should
   `typeinfo`'s `Row` be a reflection-specific superset that carries this without
   changing the row concept used for `HasField`/`Lacks`/Tier 2-3? Blocks a concrete
   `typeinfo` spec.

2. **`emit` soundness.** Does ordinary orphan-rule/coherence checking (RFC-0060) apply
   unchanged to an impl emitted by comptime code? Can a comptime function emit an impl
   for a type it does not own (e.g. a third-party library deriving an aspect for a
   stdlib type)? This is the crux of Path D's "cons" above and needs its own worked
   examples before the mechanism can be specified precisely.

3. **Expression-position `emit`'s scoping rules.** §4 asserts that splicing a
   comptime-parsed expression back at its own call site avoids syntax-macro-style
   hygiene problems because the caller's own scope applies unchanged — but the precise
   rule (what exactly counts as "the call site" once a comptime function itself calls
   other comptime functions before emitting; whether an emitted expression can reference
   comptime-local bindings from inside the emitting function, not just the caller's
   locals) is asserted, not specified. Needs a formal scoping rule before §4/§5's
   pattern-as-argument examples can be trusted.

4. **Comptime-callable parser API surface.** §5 sketches `parse_pattern`/`parse_sql`-
   style functions informally. Which grammar productions does Metel actually expose as
   comptime-callable (expressions only? patterns? statement lists? full item
   declarations?), and is this a small fixed set of builtins or a general
   "parse-a-production-by-name" facility? The broader the surface, the more this
   overlaps with exposing the compiler's own parser as a library, which is a larger
   commitment than derive alone needs.

5. **Scope of span-tracking, and whether highlighting is this RFC's concern.** §6
   commits to span-tracked comptime strings for diagnostics but explicitly limits this
   to literal strings, not computed/concatenated ones — is that limitation acceptable
   long-term, or does it need a real solution (e.g. span-preserving string
   concatenation) before v0.5? Separately: is LSP/editor semantic-highlighting support
   for embedded DSL text in scope for this RFC at all, or does it belong in a dedicated
   tooling RFC that merely depends on the span-tracking primitive specified here?

6. **Is body reflection in scope for this RFC at all?** §7 deliberately does not
   propose a mechanism for reflecting over a function's own statements/expressions
   (as opposed to `typeinfo`'s reflection over a *type's* shape), on the grounds that
   it is a much larger reflection surface and that its main motivating use case
   (auditing for a property like "performs IO" or "uses unsafe") is better served by
   an effect system (`algebraic-effects.md`) than by source inspection, since auditing
   cannot see through a `dyn Aspect` call's runtime-resolved callee (RFC-0008) while an
   effect obligation on the aspect's own interface can. Confirm this scoping decision,
   or, if shallow non-transitive body reflection is wanted for its own sake (lints,
   style rules), decide whether it belongs in this RFC or a separate one.

7. **How does declaration-site bound checking compose with comptime substitution?**
   §1 recommends keeping RFC-0061's checked-bounds discipline (`T: Clone` verified at
   the generic function's own definition) layered on top of comptime type parameters,
   rather than drifting toward Zig's use-site duck typing. Is that check a distinct
   compiler pass that runs before any comptime evaluation of the body, or is it itself
   expressible as comptime code (an assertion the aspect system inserts automatically
   at the top of every bounded generic function)? Neither Zig nor RFC-0061 specifies
   this composition today — it is new design work either way.

8. **Is the `<T>`-generics/comptime unification required, or just recommended?** Path D
   works even if `<T>` generics remain a separate, unrelated mechanism — the unification
   in §1 is presented as desirable (one explanation instead of two, and a concrete
   mechanism underneath RFC-0008's assumed monomorphisation) but not load-bearing for
   derive itself. Confirm whether pursuing it is in scope for this RFC or belongs in a
   generics-specific RFC — no such RFC currently exists; `public/reference/spec/types.md`'s
   "Generics" section is the only current specification, and it does not address dispatch
   model or bound-checking timing at all.

9. **Incremental rollout.** Can `typeinfo`'s `TypeInfo` enum be introduced starting with
   only the `Struct` arm (sufficient for every aspect in the initial derivable set),
   deferring `Enum`/`Int`/`Pointer`/... arms until something actually needs them? Or
   does the sum type need to be specified in full before any of it ships, to avoid a
   breaking change to `TypeInfo` later?

10. **`@` attribute scope.** What items can be annotated — struct/enum declarations, function declarations, `let` bindings, individual fields? Field-level attributes (e.g. `@skip` on a field to exclude it from `Display`) are useful but add parsing complexity.

11. **`Display` vs `From` for string conversion.** `print` currently only accepts `String`. When aspects land, `print` should accept any type with a string representation. The question is which aspect owns that conversion:
   - A `Display` aspect (`fun to_string(self) -> String`) implemented by the source type — the natural direction for user-defined types.
   - `String` implementing `From<T>` for each printable type — consistent with the `from` pattern but puts the responsibility on `String`, which cannot know about user-defined types without open dispatch.
   These serve different purposes and should likely remain separate aspects. Resolve before finalising the `print` signature.

12. **Compiler-known attribute registry.** The compiler needs a fixed set of recognised `@` attributes (e.g. `@inline`, `@cfg`, `@allow`). Should unknown `@` attributes be a compile error, a warning, or silently ignored (for forward compatibility)?

13. **`@cfg` and conditional compilation.** Conditional compilation is a significant feature in its own right (platform-specific code, feature flags). Should `@cfg` be in scope for this RFC or a separate one?

14. **`linear` keyword vs `derives Linear`.** Should RFC-0024's `linear` keyword be removed in favour of `derives Linear` once this RFC is accepted? The keyword form is available sooner (v0.3); the derive form is more uniform but requires v0.5+ and Path D's mechanism specifically. A possible migration: accept `linear` keyword now, deprecate in favour of derive when comptime derive lands.

---

## Timing Recommendation

All features in this RFC are **deferred to v0.5+**. The core language must stabilise first:

- Generics and aspects (v0.2) — derive requires aspects to exist, and Path D's `type`-as-value proposal (§1) touches generics directly
- Memory model (v0.3) — `@extern` for FFI requires unsafe blocks (RFC-0026)
- Concurrency (v0.4) — `@cfg` and platform attributes interact with the concurrency model

The `linear` keyword (RFC-0024) is the one meta-adjacent feature that ships early (v0.3) as a plain keyword, to be revisited for derive integration at v0.5.

Path D specifically has a longer critical path than Paths A/C would have had: `type`-
as-comptime-value and `typeinfo` reflection (with the row-metadata question in Open
Question 1 resolved) must exist before any derive function can be written, comptime or
otherwise. RFC-0080's `Clone` derive is blocked on this, not just on syntax.

Minimum action before v0.5: reserve `@` as a grammar token so it cannot be used for other purposes. Reserve `derives` and `comptime` as keywords for the same reason. This prevents a breaking change when the attribute system and comptime derive land.

---

## References

- Language spec: `public/reference/spec/types.md` ("Generics" section — no current notion of `type`-as-value)
- `reports/substructural-types/structural-records.md` — row concept reused by `typeinfo`'s struct arm (§2); §8's implicit/tier-gated split is the model for reflection vs. runtime conversion
- RFC-0011: `docs/internal/rfcs/rfc-0011-operator-overloading.md` — `Eq`/`Ord` derive depends on operator aspects
- RFC-0009: `docs/internal/rfcs/rfc-0009-module-system.md` — visibility and `@cfg` interaction; also field-visibility for reflection (Open Question 1)
- RFC-0024: `docs/internal/rfcs/rfc-0024-linear-types.md` — `linear` keyword vs `derives Linear`
- RFC-0026: `docs/internal/rfcs/rfc-0026-unsafe-blocks.md` — `@extern` for FFI uses attribute syntax
- RFC-0060: `docs/internal/rfcs/rfc-0060-aspect-impl-coherence.md` — coherence/orphan rules `emit` must respect (Open Question 2)
- RFC-0008: `docs/internal/rfcs/rfc-0008-aspect-objects.md` — states "static dispatch
  (generics + monomorphisation)" as Metel's existing default, confirming §1's
  generics-as-comptime-sugar unification rather than introducing a new dispatch model;
  also the source of the dynamic-dispatch limit §7 relies on to scope body reflection
  out of this RFC
- `reports/substructural-types/algebraic-effects.md` — §11.1's tracked IO effect is the
  recommended mechanism for audit-style motivations (§7), in place of body reflection
- RFC-0061: `docs/internal/rfcs/rfc-0061-structural-aspect-bounds.md` — the existing
  bound checker (checked declaration-site aspect bounds) §1 recommends preserving
  alongside comptime substitution, in place of Zig's use-site duck typing
- RFC-0080: `docs/internal/rfcs/rfc-0080-stdlib-aspects.md` — `Clone`/`Send`/`Sync` derive
  and auto-impl semantics depend on this RFC's mechanism; moved back to under-review
  2026-07-09 pending it
- Prior art: Zig `comptime`, `@typeInfo`, `comptime T: type` — no separate macro
  language; `type` as a first-class comptime value; generics unified with comptime
- Prior art (superseded paths): Rust `#[derive(...)]` and proc-macro system, Java annotations, Python decorators
- Prior art (§4-§6, macro-closing): Rust `matches!`/`dbg!` (motivating pattern-as-argument
  and source-capture cases); compile-time-validated query-builder libraries in
  macro-free languages (motivating comptime-on-strings for embedded DSLs); `syn`/
  proc-macro span-tracked diagnostics (motivating §6's span-aware `compileError`)

---

## Decision

**Outcome:** *(pending — Path D recommended by this revision, not yet formally accepted)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
