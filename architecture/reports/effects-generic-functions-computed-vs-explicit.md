---
title: "Twenty Effects-Library Generic Functions under Both Generic-Class Models"
date: '2026-11-07'
status: report
relates: rfc-0089, rfc-0140, rfc-0206
---

# Twenty Effects-Library Generic Functions under Both Generic-Class Models

The test proposed in `generic-class-computed-vs-explicit.md` section 4: write the first 20 generic functions an
effects library needs under Model X (open by default, `T: Discard` where a value is dropped) and Model Y (opt-in,
`?Discard` where a parameter must accept linear values), then count (a) annotations and (b) which functions cannot
accept linear arguments without opting in. It records a measurement. It does not choose.

## 1. Method, and what this test can and cannot show

- **Source of the functions.** RFC-0140 (Algebraic Effects) is under review and has no library code. The 20 functions
  below are this author's selection of what an effects library plausibly needs, derived from the constructs of
  RFC-0140: continuations (sections 1 and 2), the standard handlers State, Reader, Writer, Exception and Choice
  (sections 1 and 6), bracketing and linear capability tokens (section 9), and generators. A reader who disagrees
  with the selection can re-run the count with the rules in section 4; the counts are mechanical once the functions
  are fixed.
- **Parity.** Both models give each parameter the same capability: a parameter X leaves open (the body does not drop
  it) is `?Discard` in Y; a parameter X closes with `T: Discard` (the body drops it) is unannotated in Y. So the
  models accept exactly the same programs, and the comparison is purely annotation placement.
- **Types.** Generic types the functions use are counted separately: Model Y annotates the type parameters that
  must accept linear values, and Model X needs a stated `Discard` condition (D19) only where a type does not own a
  parameter it carries.
- **Out of scope.** A continuation that captured a linear value would itself have to be `linear`, as a closure does
  (RFC-0194; RFC-0140 section 9 and open question 2). That is a class-of-the-capture question, not a class-of-`R`
  question, and both models are equally affected. `Continuation<R, F>` is therefore modelled as an affine
  heap value with no stored `R` or `F`.

## 2. The twenty functions under Model X

```metel
// A. Continuation and handler plumbing
fun resume<R, F>(k: Continuation<R, F>, v: R) -> F { .. }          // moves v into the continuation
fun abort<R, F>(k: Continuation<R, F>) { .. }                       // drops k (Continuation states Discard)
fun handle_with<H, T>(h: H, body: |H| -> T) -> T { .. }             // h moves into body
fun then<R, F, G>(k: Continuation<R, F>, f: |F| -> G) -> Continuation<R, G> { .. }

// B. Standard handlers
fun state_put<S: Discard>(h: &var StateHandler<S>, s: S) { .. }     // drops the old state
fun state_take<S>(h: &var StateHandler<Option<S>>) -> Option<S> { .. }
fun reader_ask<E>(h: &ReaderHandler<E>) -> &E { .. }
fun writer_tell<W>(h: &var WriterHandler<W>, w: W) { .. }           // moves w into the log
fun writer_into_log<W>(h: WriterHandler<W>) -> List<W> { .. }
fun catch<T, E>(body: || -> Result<T, E>, on_err: |E| -> T) -> T { .. }
fun unwrap_or<T: Discard, E: Discard>(r: Result<T, E>, d: T) -> T { .. }   // drops d or the error

// C. Control and resources
fun bracket<R, T>(acquire: || -> R, use_it: |&R| -> T, release: |R| -> ()) -> T { .. }
fun finally<T>(body: || -> T, cleanup: || -> ()) -> T { .. }
fun with_transaction<Tx, T>(tx: Tx, f: |&var Tx| -> T) -> (Tx, T) { .. }

// D. Choice and results
fun choose<T: Discard>(a: T, b: T, first: boolean) -> T { .. }      // drops the loser
fun collect_all<T>(xs: List<T>) -> List<T> { .. }
fun first_success<T: Discard, E: Discard>(rs: List<Result<T, E>>) -> Option<T> { .. }   // drops the rest

// E. Generators and relays
fun yield_all<T>(xs: List<T>, emit: |T| -> ()) { xs.consume_each(emit); }
fun take_n<T: Discard>(xs: List<T>, n: i64) -> List<T> { .. }       // drops the tail
fun zip_effects<A, B>(a: A, b: B) -> (A, B) { (a, b) }

// Types used: Continuation states `Discard` (D19); StateHandler, ReaderHandler, WriterHandler own their
// parameters, so the conservative default already fits.
```

## 3. The same functions under Model Y

```metel
// A. Continuation and handler plumbing
fun resume<R: ?Discard, F: ?Discard>(k: Continuation<R, F>, v: R) -> F { .. }
fun abort<R: ?Discard, F: ?Discard>(k: Continuation<R, F>) { .. }
fun handle_with<H: ?Discard, T: ?Discard>(h: H, body: |H| -> T) -> T { .. }
fun then<R: ?Discard, F: ?Discard, G: ?Discard>(k: Continuation<R, F>, f: |F| -> G) -> Continuation<R, G> { .. }

// B. Standard handlers
fun state_put<S>(h: &var StateHandler<S>, s: S) { .. }              // S is discardable by default
fun state_take<S: ?Discard>(h: &var StateHandler<Option<S>>) -> Option<S> { .. }
fun reader_ask<E: ?Discard>(h: &ReaderHandler<E>) -> &E { .. }
fun writer_tell<W: ?Discard>(h: &var WriterHandler<W>, w: W) { .. }
fun writer_into_log<W: ?Discard>(h: WriterHandler<W>) -> List<W> { .. }
fun catch<T: ?Discard, E: ?Discard>(body: || -> Result<T, E>, on_err: |E| -> T) -> T { .. }
fun unwrap_or<T, E>(r: Result<T, E>, d: T) -> T { .. }

// C. Control and resources
fun bracket<R: ?Discard, T: ?Discard>(acquire: || -> R, use_it: |&R| -> T, release: |R| -> ()) -> T { .. }
fun finally<T: ?Discard>(body: || -> T, cleanup: || -> ()) -> T { .. }
fun with_transaction<Tx: ?Discard, T: ?Discard>(tx: Tx, f: |&var Tx| -> T) -> (Tx, T) { .. }

// D. Choice and results
fun choose<T>(a: T, b: T, first: boolean) -> T { .. }
fun collect_all<T: ?Discard>(xs: List<T>) -> List<T> { .. }
fun first_success<T, E>(rs: List<Result<T, E>>) -> Option<T> { .. }

// E. Generators and relays
fun yield_all<T: ?Discard>(xs: List<T>, emit: |T| -> ()) { xs.consume_each(emit); }
fun take_n<T>(xs: List<T>, n: i64) -> List<T> { .. }
fun zip_effects<A: ?Discard, B: ?Discard>(a: A, b: B) -> (A, B) { (a, b) }

// Types used: each type whose parameter must accept linear values opts in.
struct Continuation<R: ?Discard, F: ?Discard> { .. }
struct StateHandler<S: ?Discard> { .. }
struct ReaderHandler<E: ?Discard> { .. }
struct WriterHandler<W: ?Discard> { .. }
```

## 4. Counting rules

- **Model X:** one `T: Discard` per type parameter the body drops, plus one stated `Discard` per generic type that
  does not own the parameters it carries.
- **Model Y:** one `?Discard` per type parameter that must accept linear values, plus one `?Discard` per type
  parameter of a generic type that must accept linear values.
- A parameter is *dropped* when the body can drop a value of that type on some path (including by assignment, which
  drops the old value). Closures are `Discard` (RFC-0194), so a closure parameter never counts.

## 5. Results

| # | Function | Params | Dropped (X annotates) | Open (Y annotates) |
|---|---|---|---|---|
| 1 | `resume` | R, F | | R, F |
| 2 | `abort` | R, F | | R, F |
| 3 | `handle_with` | H, T | | H, T |
| 4 | `then` | R, F, G | | R, F, G |
| 5 | `state_put` | S | S | |
| 6 | `state_take` | S | | S |
| 7 | `reader_ask` | E | | E |
| 8 | `writer_tell` | W | | W |
| 9 | `writer_into_log` | W | | W |
| 10 | `catch` | T, E | | T, E |
| 11 | `unwrap_or` | T, E | T, E | |
| 12 | `bracket` | R, T | | R, T |
| 13 | `finally` | T | | T |
| 14 | `with_transaction` | Tx, T | | Tx, T |
| 15 | `choose` | T | T | |
| 16 | `collect_all` | T | | T |
| 17 | `first_success` | T, E | T, E | |
| 18 | `yield_all` | T | | T |
| 19 | `take_n` | T | T | |
| 20 | `zip_effects` | A, B | | A, B |
| | **Totals** | 31 parameters | **7 (5 functions)** | **24 (15 functions)** |

### (a) Annotations

| | Functions | Types | Total |
|---|---|---|---|
| **Model X** | 7 | 1 (`Continuation` states `Discard`) | **8** |
| **Model Y, full parity** (every parameter X leaves open) | 24 | 5 (`Continuation` 2, three handlers 1 each) | **29** |
| **Model Y, essential only** (opt in `resume`, `handle_with`, `bracket`, `with_transaction` and `Continuation`) | 8 | 2 | **10** |
| **Model Y, none** (author never opts in) | 0 | 0 | **0** |

### (b) Functions that cannot accept linear arguments

| Question | Model X | Model Y |
|---|---|---|
| Functions that cannot accept linear values for some parameter because the body drops it | 5 (#5, 11, 15, 17, 19) | the same 5 (the API is the same) |
| Functions that need an explicit opt-in to accept linear values | **0** | **15** (all those with an open parameter) |
| Of those, functions the effects design needs to accept linear values (judged from RFC-0140 section 9: a capability token resumed through an effect, a resource bracket, a transaction handle, a handler that owns a resource) | n/a | **4** (#1, 3, 12, 14); up to 6 if `then` and `zip_effects` are counted |
| Functions linear callers are blocked on under "essential only" | n/a | **11** |

The 5 functions that drop have an alternative design that accepts linear values: hand the dropped value to a consumer
(`choose` with a `dispose: |T| -> ()`), return it (`state_put` returns the old state), or take the rest as a
`List` result (`take_n` returns the tail). That changes the API in both models.

## 6. What the measurement says

- **The parameters are mostly moved, not dropped.** 24 of 31 parameters (77 percent) are open. That is higher than
  the std census (30 to 40 percent of by-value functions drop on some path): effects plumbing forwards values to
  continuations, handlers and consumers, and rarely discards them. In this sample 5 of 20 functions drop (25
  percent) and 7 of 31 parameters (23 percent).
- **Cost under full parity is 8 versus 29.** Model Y costs 3.6 times Model X for the same accepted programs, because
  the annotation falls on the larger group (moved parameters).
- **Cost is symmetric if Y authors opt in selectively, but then linear callers are blocked.** Opting in only where
  the effects design requires it costs 10, close to X's 8, but leaves 11 of 20 functions unusable with linear
  arguments, which is the case C1 wants to avoid.
- **X does not cost anything to the authors of the 15 functions that only move.** Its 8 annotations are concentrated on
  5 functions and one type, each of which drops a value: the places where "this might be linear" matters.
- **The result depends on the mix.** The count flips if most of the code a library contains drops its arguments. For
  an effects library, which exists to carry values through control transfers, it does not.

## 7. Limits of this measurement

- The selection is mine. Twenty functions from one design is a sample, not a census, and an effects library with
  more collection and formatting helpers would drop more.
- Bodies are not written out, so the dropped/open classification is by the intended behaviour (for example `choose`
  keeps one argument and drops the other).
- `Continuation<R, F>` is modelled as affine with no stored `R` or `F`. The real treatment of a continuation that
  captured a linear value (RFC-0140 open question 2) may change both columns equally.
- Counts of annotations are not a measure of effort. Model Y's `?Discard` is mechanical (one token per parameter);
  Model X's `T: Discard` forces a decision at the drop site, which is more informative but costs more per instance.
- It does not test the public-API stability question (D19), the diagnostics, or interactions with `Drop` and
  patterns. It tests annotation placement only.
