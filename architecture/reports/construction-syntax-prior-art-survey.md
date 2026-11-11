---
title: "Construction syntax: prior-art survey"
date: '2026-11-11'
status: report
relates: rfc-0100, rfc-0106, rfc-0114, rfc-0225, rfc-0226
---

# Construction syntax: prior-art survey

## Question and method

How can Metel make nominal value construction recognisable at the use site,
including zero-field types, without relying on identifier capitalisation or
argument-dependent selection between a type and a function?

Primary documentation was read on 2026-11-11. Findings below are documentation
research, not compiler experiments in the surveyed languages. Links identify the
sources consulted; rolling documentation may change. Metel spellings in the
comparison section are design candidates, not accepted language syntax.

This report separates three properties:

1. **Lookup:** the compiler chooses one declaration without inspecting arguments
   to choose between namespaces.
2. **Recognition:** a reader can identify construction from the written syntax.
3. **Semantics:** every designated construction expression routes through the
   intended construction policy, rather than bypassing invariants.

RFC-0226 addresses the first. The language owner's subsequent concern is the
second. Neither determines the third by itself.

## Primary-source findings

### Explicit construction keyword: C#

C# uses `new T(args)` for constructor invocation, and supports target-typed
`new(args)` when the target type is available. The marker survives even if the
identifier is unfamiliar. Its structs are value types and do not require heap
allocation, so a `new` spelling need not mean heap allocation in a language.
Sources: [new operator](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/new-operator),
[struct proposal](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/proposals/csharp-10.0/parameterless-struct-constructors).

**Metel assessment:** `new Empty()` and `new Ticket(value = 1)` meet the recognition
requirement and can resolve their targets in the type namespace. Metel would need
to define storage independently and decide whether enum variants use the marker.
Target-typed `new()` is separable and need not be included initially.

### Named brace literals: Rust, Go and Zig

Rust's named-field struct expressions use `Point { x: 1, y: 2 }`; empty braced
structs use `Empty {}`. Rust also has tuple-struct call constructors and unit
structs usable as bare values. The latter two forms deliberately do not give all
construction a unique visual marker. Tuple/unit constructors inhabit the value
namespace. Sources: [struct expressions](https://doc.rust-lang.org/reference/expressions/struct-expr.html),
[namespaces](https://doc.rust-lang.org/reference/names/namespaces.html).

Go specifies composite literals such as `Point{X: 1, Y: 2}` and `Empty{}`. A type
head and brace body identify the literal; the specification describes evaluation
as constructing a value. Source: [composite literals](https://go.dev/ref/spec#Composite_literals).

Zig uses `Point{ .x = 1, .y = 2 }`, with `.{ ... }` when the type is omitted.
Its reference demonstrates both contextual struct initialisation and fully
anonymous inferred structs, and uses `.{}` for an
empty struct in an expected-type context. A named `init` can be an ordinary
function returning a literal. Sources: [struct](https://ziglang.org/documentation/master/#struct),
[anonymous struct literals](https://ziglang.org/documentation/master/#Anonymous-Struct-Literals).

**Metel assessment:** `Ticket { value = 1 }` and `Empty {}` are a serious alternative
to a keyword. They resolve a type head and cannot be mistaken for an ordinary
parenthesised function call. They also pair naturally with RFC-0225's anonymous
`.{ .value = 1 }`, while nominal field names retain their existing undotted spelling.
This would reverse RFC-0100's retirement of nominal brace expressions.

Do not copy Zig's contextual nominal initialisation automatically: RFC-0225
specifies anonymous structural records, without expected-type nominal construction.

### Named constructor operations: Crystal and Rust factories

Crystal creates class instances through `.new`, generated around `initialize`.
Source: [new, initialize and allocate](https://crystal-lang.org/reference/1.21/syntax_and_semantics/new,_initialize_and_allocate.html).

Rust commonly uses associated functions named `new` as factories, but its book
explicitly says the name is not special language syntax. Such factories may have
other names. Source: [associated functions](https://doc.rust-lang.org/book/ch05-03-method-syntax.html#associated-functions).

**Metel assessment:** `Ticket::construct(value = 1)` or `Ticket::new(value = 1)`
makes intent explicit in words and avoids competing with a free `Ticket` function.
However, an ordinary associated function called `new` is a convention, not a
guaranteed construction operation. Metel would need to reserve/generate the
canonical member or define it through `Construct`, and specify that all designated
construction expressions use it. A row-accepting `Construct::construct(row)` also
needs an explicit choice about surface field arguments versus a single row operand.

### Type-call syntax: Swift, Kotlin and Scala

Swift initialises structures using `Size(width: 2.0, height: 2.0)` and provides
memberwise initialisers under specified conditions. Source:
[initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/).

Kotlin uses `Person(args)` without `new`, expressly likening it to a function call.
Source: [creating instances](https://kotlinlang.org/docs/classes.html#creating-instances).

Scala 3 generates constructor proxies permitting `StringBuilder(args)`. Its
proxy-generation rules account for competing values or methods in the defining
scope. Sources: [universal apply methods](https://docs.scala-lang.org/scala3/reference/other-new-features/creator-applications.html),
[reference overview](https://docs.scala-lang.org/scala3/reference/overview.html).

**Metel assessment:** strong precedent for concise construction-as-call and for
handling namespace interactions explicitly. These forms do not satisfy the newly
stated requirement that construction be recognisable independently of knowing the
callee. They support RFC-0226's original direction, not a distinctive marker.

### Enforced lexical distinction: OCaml

OCaml's grammar separates lowercase value identifiers and capitalised variant
constructor identifiers. These are data constructors, not general struct
initialisers. Source: [names](https://ocaml.org/manual/5.3/names.html).

**Metel assessment:** enforcing a corresponding casing split could make names
syntactically distinct, but it changes the identifier policy across the language.
It also retains a bare constructor name for a nullary variant. It is an alternative
only if the language owner wants casing itself to carry the distinction.

## Metel candidate comparison

These ratings are design assessments, not claims measured by the cited sources.

| Candidate | Empty form | Recognition without casing | Main cost |
|---|---|---|---|
| `Ticket(value = 1)` + RFC-0226 | `Empty()` | No: ordinary call shape | Constructor value bindings and collision restrictions |
| Mandatory `new Ticket(value = 1)` | `new Empty()` | Yes, dedicated keyword | New syntax, keyword and migration |
| Mandatory `construct Ticket(value = 1)` | `construct Empty()` | Yes, dedicated keyword | Longer; less directly supported by surveyed precedent |
| Mandatory `Ticket { value = 1 }` | `Empty {}` | Yes, type head plus braces | Reverses RFC-0100; must settle block parsing and policy routing |
| Canonical `Ticket::construct(value = 1)` | `Empty::construct()` | Explicit operation name; guarantee requires a language rule | Verbosity, member rules and row/argument mapping |
| Canonical `Ticket::new(value = 1)` | `Empty::new()` | Explicit operation name; guarantee requires a language rule | As above, plus possible allocation association |
| `Ticket.{ .value = 1 }` | `Empty.{}` | Appears distinct but already occupied | Collides with Metel's type/residual projection syntax |
| Enforced constructor casing | `Empty` or `Empty()` | Casing becomes the marker | Broad identifier-policy change; bare values remain |

`Ticket.{ ... }` is an invented Metel candidate here, not a surveyed language's
construction syntax. It is unsuitable as a local change because RFC-0121/0137
already give that form projection meaning. An invented sigil such as `Ticket!(...)`
would need its own lexical/grammar investigation and offers no established meaning
in the sources surveyed; it is not needed to choose among the stronger candidates.

## Construction policy is independent of delimiters

RFC-0100 section 7 plans a `Construct` operation, but its current release scope
uses only a synthesised default. RFC-0114 remains a draft. The current proposal
for raw minting is `Self { ... }` only inside the designated constructor bodies.
These are project design facts, not shipped support for custom constructors.

Importantly, RFC-0114's own revision states that a literal desugaring to `construct`
is not an invariant bypass. Either `new Ticket(...)` or `Ticket { ... }` could
route through exactly the same canonical policy. Braces do not inherently force
raw field initialisation, just as parentheses do not establish validation.

If public braces are chosen, the language must distinguish canonical construction
from the internal minting step. Reusing `Self { ... }` with a context-specific raw
meaning is possible but obscures the distinction; alternatively the minting form
would need another explicit spelling. That is a real interaction requiring a
joint decision with RFC-0114, not grounds to assume braces cannot work.

## Questions to settle before revising RFC-0226

1. Is the goal a unique syntactic marker, or an explicit named operation? This
   chooses keyword/braces versus a constructor member.
2. Should construction accept positional arguments? Parenthesised forms preserve
   them naturally; braces more naturally express named fields. Supporting numeric
   or positional brace entries would be an additional rule.
3. Should enum variants use the same marker, including nullary variants? Keeping
   bare `Option::None` while requiring `new Empty()` is a deliberate distinction
   between variant values and nominal construction, not full visual uniformity.
4. How are arguments mapped to the canonical row and how is fallibility exposed?
   Preserve these policy questions in RFC-0114 rather than silently deciding them
   by changing delimiters.
5. Which form is the sole supported construction syntax after migration? Keeping
   the old `Type(...)` as an alias retains its recognition problem.

## Assessment

The useful shortlist is mandatory `new Type(...)`, named brace construction, or
a canonical `Type::construct(...)` operation. A new keyword is the clearest fit
if positional arguments and a uniform marker matter most. Braces deserve equal
consideration if the language owner prefers visible data shapes and named fields,
especially alongside RFC-0225. An associated operation is attractive if avoiding
new expression syntax matters more than distinguishing construction grammatically
from every other associated call.

This survey makes no lifecycle transition. Following the survey, the language-owner
discussion selected `new T(...)` paired with inferred `.(...)`; RFC-0226 was
revised under review to record that direction and explicit whole-row `..r` /
`..{ ... }` arguments. This is a proposed design, not implemented behaviour.
No performance, user-study or cross-language collision tests were run.
