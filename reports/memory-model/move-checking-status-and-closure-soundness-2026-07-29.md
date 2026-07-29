# Move Checking Status and Closure Soundness

**Date:** 2026-07-29
**Status:** implementation assessment; not a language-spec change

## Scope

This report records the state of the interpreter's opt-in move checker after the
generic-body work and the borrowed-array iteration work on
`fix/329-borrowed-array-iteration`. It separates rules that are implemented from
known limits and temporary corpus workarounds. It is intentionally an assessment of
the current interpreter, not a claim that affine ownership is fully implemented.

## Implemented checking

With `--move-check` (or a fixture's `move_check = true` option), the checker tracks
moves of bindings and places through:

- by-value assignments, returns, call arguments, method receivers, struct and record
  construction, tuples, arrays, and temporary-reference construction;
- fields, tuple elements, indexed elements, and destructuring patterns;
- use after move, use of a whole value after a partial move, and partial moves of a
  `Drop` type;
- `if`, `match`, `while`, `for`, `loop`, and `for-in`, using a conservative join of
  possible moved state;
- `Copy` and `Drop` aspect satisfaction, including generic bounds, conditional impls,
  generic functions, generic impl methods, aspect-bound calls, and associated-type
  bounds; and
- ordinary closure capture: a free non-`Copy` root captured by a closure is treated as
  moved at closure creation.

Array rules are deliberately ownership-sensitive. Indexed element moves are rejected.
A `[T; N]` `for-in` binding is treated as an owned element, while a `T[]` loop binding
is a value from an immutable borrowed view: it may be read or borrowed, but a non-`Copy`
element may not be consumed. This is the #329 rule.

The checker reports `T0019` for the first user-visible violation. Its lower-level report
retains all collected violations and counts generic bodies that it could not analyse.

## Limits that remain

### Enforcement is opt-in

Move checking is disabled by default. Without `--move-check`, the interpreter retains
its copy-on-assignment behaviour. Corpus migration and making the check the default are
tracked by metel-core#310.

### Generic reconstruction can fail open

Most named generic functions, generic impl methods, aspect-bound calls, and associated
types are reconstructed and checked. When reconstruction fails, the checker emits a
warning containing the reason and continues compilation. This is a deliberate visible
gap, but it is still a false-negative route. Anonymous generic closures have no scheme
lookup key and are explicitly reported as unchecked.

### This is not a borrow checker

The checker has a narrow `&var` reborrow rule, but it does not perform lifetime,
aliasing, or escape analysis. It therefore cannot provide Rust-style guarantees about
overlapping mutable references. Runtime `RefCell` behaviour remains the final guard for
some mutable-reference mistakes.

### Control flow is conservative

The checker unions possible moved state across branches and loop bodies without proving
reachability. That can produce false positives for an unreachable move; it does not make
the ownership check unsound.

### Ownership RFC work remains incomplete

Drop execution and ordering are separate unfinished work (metel-core#292), as is the
remaining partial-move work (metel-core#293). The move checker can diagnose important
partial-move cases before those runtime semantics are complete.

## Current workarounds

Generic read-only algorithms should accept borrowing callbacks, for example
`(&T) -> U` and `(&T) -> boolean`. An algorithm that must retain an owned value from a
borrowed `T[]` currently takes an explicit callback:

```metel
fun filter<T>(arr: T[], pred: (&T) -> boolean, clone: (&T) -> T) -> T[] {
    // select through `pred`, then obtain an owned output value through `clone`
}
```

This is temporary. It avoids moving through a borrowed view while the standard `Clone`
surface and the remaining borrowed-iteration design work are not both available. Code
that merely duplicates values should instead require `T: Copy`.

## Confirmed closure soundness hole

The move checker currently classifies every `Type::Fun` as `Copy`. That is appropriate
for a named function pointer, but it is not generally appropriate for a closure with a
non-`Copy` capture. The checker also validates a closure body at creation time without
tracking consumption of captures across later calls.

The following program was accepted by the release interpreter with `--move-check` on
2026-07-29:

```metel
fun call(f: () -> String) -> String { f() }

fun main() {
    let s = "hello";
    let f = () -> String { s };

    let first = call(f);
    let second = call(f); // accepted, although `f` consumes captured `s`
}
```

Under affine semantics, this closure is `FnOnce`: invoking it consumes its captured
`String`, so a second by-value use of `f` must be rejected. Today it is accepted because
the function value is considered `Copy` and calls do not update capture state.

This is an ownership-soundness hole, not memory unsafety in the current interpreter. The
runtime deep-clones an environment when a closure is created and later shares the closure
object, so it can produce two strings. That runtime implementation detail is precisely
why it must not be used as evidence that the affine contract holds.

The proper fix is a closure-capability design:

1. distinguish plain function pointers from closures;
2. derive `Copy` for a closure only when all captures are `Copy`; and
3. model whether invoking a closure consumes, mutably borrows, or shared-borrows its
   captures (an `FnOnce`/`FnMut`/`Fn`-like distinction).

metel-core#252, closure capture lists, is related design work. This specific move-check
hole should receive its own implementation issue before the move checker is enabled by
default.

## Practical guidance

Treat `--move-check` as valuable early enforcement, not yet as a proof of complete
ownership safety. In particular, do not rely on reusing closures that capture non-`Copy`
state, do not treat an unchecked-generic warning as harmless, and keep ownership-sensitive
generic algorithms explicit about borrowing, copying, or cloning.
