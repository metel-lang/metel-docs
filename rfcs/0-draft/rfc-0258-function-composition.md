---
id: rfc-0258
title: "Function Composition"
date: '2026-11-27'
status: draft
---

## Summary

Compose two functions into a reusable callable using `f.then(g)`. A companion
`try_then` would compose fallible functions through the `Try` contract. Symbolic
operators remain deferred. This proposal was split from RFC-0204 so that the
pipeline operator can be accepted independently.

## Motivation

A pipeline evaluates a chain for one input. A composition builds a function that
can be stored, passed, or applied to multiple inputs:

```metel
let normalize := trim.then(to_lower).then(collapse_spaces);
```

An explicit closure already expresses this behavior. Composition gives the
ordered pair of calls a standard vocabulary.

## Plain composition: `f.then(g)`

```metel
let normalize := trim.then(to_lower).then(collapse_spaces);
// normalize: |String| -> String
```

`f.then(g)` is `|x| g(f(x))`: left to right, "f then g".

**Typing.** If `f : |A| -> B` and `g : |B| -> C`, then `f.then(g) : |A| -> C`. Any other
operand types are a type error naming which side failed to match.

**Proposed capture rules.** If either function is `once`, the result is `once`. If either
is `var`, the result is `var`. Question 2 covers the interaction with the full callable
contract, including linear captures.

**Where the method lives.** RFC-0161 and RFC-0232 supply a candidate `Callable` contract.
Question 1 considers a method on that contract, a compiler-provided method, and a free
function `compose(f, g)` with the same typing.

**No new grammar.** `then` is an ordinary identifier after a `.`. It is not a keyword and
nothing is reserved. (At the time of writing it appears neither in `grammar.pest` nor in the
spec's lexical keyword list.)

---

## Candidate operators

A dedicated operator is a deferred extension. If this proposal later includes one, it must
satisfy these constraints:

1. **Do not take `<<` or `>>`** (or `>>=`, `>>>`). Shifts and bitwise operators are not
   specified today, but RFC-0154 and ADR-0017 both anticipate bitwise operators, and taking
   the shift tokens would be hard to undo.
2. **Keep `->` meaning "a type follows"**, so parsers, highlighters and readers can rely on
   it.
3. **Be visibly distinct from the pipeline `|>`**, whose loosest precedence is the opposite
   of what a function-composition operator needs (tighter than comparison, looser than
   arithmetic).
4. **Stay a pure sugar for `then`**, so the typing rule for plain composition is unchanged.
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
cannot be specified before RFC-0190 is accepted. The [error-propagation spec](../../reference/spec/functions/error-propagation.md) already specifies that
`?` returns from its enclosing function or closure.

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


## Interactions

- **RFC-0161 and RFC-0232:** callable contracts and markers determine where the
  composition method lives and what callable type can be returned.
- **RFC-0134, RFC-0153, RFC-0157, and RFC-0194:** composition captures its operands.
  The design must account for ownership, mutation, and calling a linear operand
  exactly once. It must also account for any early exit that could skip the second
  operand.
- **RFC-0197:** retaining a generic operand's polymorphism needs generic closures.
- **RFC-0190:** `try_then` depends on `Try` and `FromResidual`. Closure-local
  propagation is already specified.
- **RFC-0204 and RFC-0205:** pipelines and hole sections are independent. A section
  can be passed as an operand if it satisfies the callable contract.

## Alternatives considered

- A free function `compose(f, g)` has the same typing and remains an option if a
  composition method has no suitable home.
- An infix `then` keyword adds grammar for the same operation.
- Ordinary closures already express both plain and fallible composition.

## Open questions

1. Where does `then` live, and is `then` the right name? Consider a library
   function, a compiler-provided method, or a callable-aspect method.
2. How do shared, exclusive, `once`, `copy`, and linear operands compose?
   Specify evaluation, captures, and the resulting callable contract. Check
   whether a fallible composition can skip a linear operand.
3. Should `try_then` live here or with RFC-0190? Is that the right name?
4. Which fallible result families may compose? Start from what `Try` and
   `FromResidual` admit under RFC-0190.
5. Revisit symbolic operators after shifts and bitwise tokens are settled.
   Decide whether the plain and fallible operators should be proposed together.

## Decision

**Outcome:** *(pending)*
