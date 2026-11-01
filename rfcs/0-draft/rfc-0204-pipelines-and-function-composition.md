---
id: rfc-0204
title: "Pipelines and Function Composition"
date: '2026-11-01'
status: draft
---

## Summary

Two small conveniences for chaining function calls:

1. **Pipeline operator:** `x |> f(a)` is `f(x, a)`.
2. **Composition method:** `f.then(g)` is a function that applies `f`, then `g`.

Both lower to ordinary calls and closures before type checking. **This RFC deliberately does
not add a composition operator.** The symbolic spelling is deferred (see "Deferred: a
composition operator"), because the obvious choice, `>>`, would take a token that a future
integer-shift RFC is likely to want, and every alternative has a real cost. `f.then(g)` is
the stable lowering target any later operator would be sugar for, so deferring loses nothing
and breaks nothing. The preferred direction, recorded below, is a **pair**: `>->` for plain
composition and `>=>` for composing fallible functions, to be specified together once the
`Try` aspect (RFC-0190) settles.

Short function arguments are the subject of RFC-0205 (hole sections and operator functions);
the two RFCs read well together but neither requires the other.

---

## Motivation

Method chains work when every step is a method of the previous value. They do not work for
free functions, and they offer no way to build a function out of other functions:

```metel
let name := collapse_spaces(to_lower(trim(raw)));   // reads inside-out
```

A pipeline reads in execution order, and `then` names the whole chain as a reusable function
value:

```metel
let name      := raw |> trim() |> to_lower() |> collapse_spaces();
let normalize := trim.then(to_lower).then(collapse_spaces);
```

---

## Design

### 1. Pipeline

```metel
xs |> filter(is_odd) |> map(times_ten) |> fold(0, add)
```

`a |> f(args)` is syntactic sugar for `f(a, args)` and is left-associative, with lower
precedence than every other binary operator. If `f` is a method of `a`'s type, `a |> f(args)`
resolves it as `a.f(args)`; otherwise it resolves a free function `f`.

The token `|>` is unambiguous in the current grammar (a closure parameter list ends in `|`, and
`|>` cannot follow a closure parameter list), but must be confirmed against the grammar's
empty-closure token `||` (Open Question 2).

### 2. Composition: `f.then(g)`

```metel
let normalize := trim.then(to_lower).then(collapse_spaces);
// normalize: |String| -> String
```

`f.then(g)` is `|x| g(f(x))`: left to right, "f then g".

**Typing.** If `f : |A| -> B` and `g : |B| -> C`, then `f.then(g) : |A| -> C`. Any other
operand types are a type error naming which side failed to match.

**Capture qualifiers compose.** If either function is `once`, the result is `once`; if either
is `var`, the result is `var`.

**Where the method lives.** Function and closure types are structural (`|A| -> B`), so they
have no aspect impls to hang a method on. The mechanism is an open question (Open Question 3).
The leading option is a compiler-provided method on function types; if RFC-0161's callable
aspect lands first, `then` becomes a default method of it. A free function
`compose(f, g)` is a fallback with identical typing.

**No new grammar.** `then` is an ordinary identifier after a `.`. It is not a keyword and
nothing is reserved. (At the time of writing it appears neither in `grammar.pest` nor in the
spec's lexical keyword list.)

---

## Deferred: a composition operator

A dedicated operator is intentionally left out of this RFC. Any later proposal must satisfy
these constraints, which are what eliminated the candidates below:

1. **Do not take `<<` or `>>`** (or `>>=`, `>>>`). Shifts and bitwise operators are not
   specified today, but RFC-0154 and ADR-0017 both anticipate bitwise operators, and taking
   the shift tokens would be hard to undo.
2. **Keep `->` meaning "a type follows"**, so parsers, highlighters and readers can rely on
   it.
3. **Be visibly distinct from the pipeline `|>`**, whose loosest precedence is the opposite
   of what a function-composition operator needs (tighter than comparison, looser than
   arithmetic).
4. **Stay a pure sugar for `then`**, so the typing rule in section 2 is unchanged.
5. **Leave room for a fallible sibling.** `>=>` is reserved for composing fallible functions
   under the `Try` aspect (RFC-0190); a plain-composition spelling should form a recognisable
   pair with it.

Candidates considered. The first row is the preferred direction (see the next subsection);
the rest are in rough order of preference:

| Spelling | Clashes with future shifts | Main cost |
|---|---|---|
| `>->` (**preferred**) | No | Starts with `>`, so it can be skimmed as a comparison. Distinct from `->`, which it does not overload. Forms a pair with `>=>`. |
| `-\|>` | No | One character from `\|>`; needs a `"-" ~ !"\|>"` lookahead against binary minus; UML association with inheritance. |
| `\|>>` | No | Longest-match ordering against `\|>`, `\|\|`, `\|`; extra bar clutter next to closures; looks like a sibling of `\|>` but binds tighter. |
| `->` | No | Overloads the type arrow: `\|x: i64\| -> i64 { x } -> double` has two meanings of `->` on one line. |
| `then` (infix keyword) | No | A new contextual keyword, which is the hardest of these to retract once code uses it. |
| `>>` | **Yes** | The conflict above. Parses fine otherwise: the PEG closes generics with a literal `>`, so `List<List<T>>` is unaffected. |
| `>>` plus `>>>` for shifts | Moved | Taxes shifts, which low-level and hashing code uses constantly (RFC-0176), and `>>>` is *unsigned* shift in Java, JavaScript and C#, a silent trap when porting code. |
| `\|>` for both uses | No | `x \|> f()` applies and `f \|> g` composes, distinguished by one pair of parentheses; a missing `()` silently changes meaning. |
| `.>`, `>>>`, `∘` | Varies | Rejected: field-access lookalike, unsigned-shift lookalike, and hard-to-type Unicode respectively. |

### Preferred direction: `>->` and `>=>` as a pair

If a composition operator is added, the preferred design is two operators that read as a
family, the way `->` and `=>` already read as related arrows:

| Operator | Meaning | Method form | Lowering |
|---|---|---|---|
| `f >-> g` | plain composition | `f.then(g)` | `\|x\| g(f(x))` |
| `f >=> g` | composition of fallible functions | `f.try_then(g)` | `\|x\| g(f(x)?)` |

```metel
let normalize := trim >-> to_lower >-> collapse_spaces;       // String -> String
let validate  := parse_age >=> check_adult >=> to_group;      // String -> Result<String, E>
```

**`>=>` is sugar over `?` and a closure.** In the lowering, `?` exits the synthesized closure,
not any enclosing function, and RFC-0190's `Try` and `FromResidual` aspects decide what that
means for the operand and result types. No new type-system concept is needed, but the operator
cannot be specified before RFC-0190 is accepted. This assumes `?` inside a closure returns from
that closure, which should be confirmed against the spec (Open Question 7).

**Why a pair rather than one operator.** Haskell has both (`>>>` or `.` flipped, and `>=>`)
because plain composition cannot chain `|A| -> M<B>` with `|B| -> M<C>`. The same holds here:
`parse_age.then(check_adult)` is a type error when `check_adult` takes an `i64` and `parse_age`
returns `Result<i64, E>`.

**Lexical safety.** Both are distinct tokens, ordered before `>=` and `>` at a tier tighter
than comparison. `>=>` appears only between two expressions, so it cannot be read as `>=`
followed by `>`; a type followed directly by `=>` in a pattern is parsed in type context, where
composition is not attempted. A formatter should still insert spaces around both.

**Known hazards of the pair.**
1. `f >-> g` and `f >=> g` differ by one character. A mix-up is normally a type error. The
   exception is when `g` takes the wrapped type (`f >-> handle_result` where
   `handle_result: |Result<T, E>| -> R`): that is valid and means something different, so the
   compiler cannot catch it.
2. `Result::and_then` already exists with different semantics, so the method form cannot be
   `and_then`; `try_then` is proposed.
3. The benefit is smaller than in Haskell: `?` already makes the closure form short
   (`|x| g(f(x)?)`), so the operators mainly help point-free chains. Two operators to learn is a
   real cost against that.
4. Reverse variants (`<=<`, `<-<`) are not proposed; `<=` is a comparison operator and the
   lexical cost is not worth it.

---

## Interactions

- **RFC-0205 (hole sections and operator functions):** sections such as `(_ * 10)` are natural
  arguments to `|>` stages and to `then`. Independent: every example here works with named
  functions or ordinary closures.
- **RFC-0154 (function type spelling):** composition produces values of `|A| -> C`; its note
  about bitwise `|` and closure bars is the precedent for reserving operator tokens.
- **RFC-0134 / RFC-0153 / RFC-0157 (closure qualifiers, default capture):** governs capture of
  composed closures.
- **RFC-0161 (callable object contract):** may supply the home for `then`.
- **RFC-0197 (generic closures):** `then` over a generic function needs generic closure
  support to avoid pinning type arguments.
- **RFC-0190 (`Try`):** `>=>` and `try_then` are defined in terms of `Try` and `FromResidual`;
  the pair cannot be specified until that RFC is accepted.
- **RFC-0100 (keyword arguments):** `|>` inserts the piped value as the first positional
  argument; keyword arguments are unaffected.
- **RFC-0203 (comprehensions):** the two features overlap on `map`/`filter`; this RFC has no
  dependency on it.
- **RFC-0199 (`Lazy<T>`):** `Lazy::map` composes with `|>`.

---

## Alternatives considered

1. **Ship a composition operator now.** Rejected for this RFC; see the deferred section. The
   decision is postponed, not made against.
2. **Infix `then` keyword now.** Same expressiveness as the method with a grammar commitment;
   see the table.
3. **A free function `compose(f, g)` only.** Valid, and the stated fallback if there is no
   place for a method on function types.
4. **Haskell-style `$` application.** Not needed: ordinary call syntax has no precedence
   problem that `$` solves.
5. **Do nothing.** Valid; this RFC is ergonomics only.

---

## Open Questions

1. Should the pipeline thread into the *last* argument (OCaml/F#) or the *first* (Elixir)?
   First is proposed because it matches method-call receivers.
2. Is `|>` safe next to `||` and closure parameter bars in all positions? A prototype parser
   test is needed.
3. Where does `then` live? A compiler-provided method on function types, a default method of a
   callable aspect (RFC-0161), or only a free `compose` function?
4. Is `then` the right name? `compose` and `and_then` are already used elsewhere (`Result`),
   and `Result::and_then` has different semantics (it sequences fallible steps, it does not
   compose functions). Does that risk confusion?
5. Should a pipeline stage be allowed to omit its parentheses (`x |> trim`)? That makes `x |> f`
   and `x |> f()` the same, at the cost of a second spelling, and would block ever reusing
   `|>` for composition.
6. Should `>->` and `>=>` be specified in this RFC once RFC-0190 is accepted, or should `>=>`
   and `try_then` live in RFC-0190 and only `>->` here?
7. Does `?` inside a closure return from the closure? The `>=>` lowering depends on it.
8. Is `try_then` the right method name, given `Result::and_then` already exists?
9. What are the rules when the two functions return different families (`Option` then
   `Result`)? The default is whatever RFC-0190's closed `?` rule allows, with no extra
   conversion.
10. When (and on what evidence) should the deferred operator be revisited? One reasonable
   trigger: the bitwise and shift operators are specified, so the remaining free tokens are
   known.

---

## Decision

**Outcome:** *(pending)*
