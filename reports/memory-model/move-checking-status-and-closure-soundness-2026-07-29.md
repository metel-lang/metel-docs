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
- fields, tuple elements, indexed elements, dereferences, and destructuring patterns;
- use after move, use of a whole value after a partial move, and partial moves of a
  `Drop` type;
- `if`, `match`, `while`, `for`, `loop`, and `for-in`, using a conservative join of
  possible moved state, with loop bodies analysed to a fixed point so that a move in one
  iteration is visible to the next (see "Control flow is conservative" below), and with
  shadowing scoped correctly — a binding that shadows another restores it when its scope
  ends, including across a `break` or `continue` out of the scope;
- `Copy` and `Drop` aspect satisfaction, including generic bounds, conditional impls,
  generic functions, generic impl methods, aspect-bound calls, and associated-type
  bounds; and
- ordinary closure capture: a free non-`Copy` root captured by a closure is treated as
  moved at closure creation; and
- a by-value `self` method reached through any reference — rejected outright, at the first
  call, regardless of whether the reference is the receiver's own binding, a projection of
  one, reached via an explicit deref or a generic bound, or a call/`if`/`match`/cast result
  with no nameable place at all, and regardless of how many layers of reference the
  receiver's type has (`&&T` names every layer in the diagnostic). Unaffected when the
  pointee's own type is `Copy` — reading a copy through a reference is exactly what `Copy`
  permits (RFC-0071 §7.1/§3a, metel-core#348).

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
gap, but it is still a false-negative route.

*Revised 2026-07-30:* this section previously named two further gaps that turned out not
to exist.

- **Anonymous generic closures** were described as having no scheme lookup key and being
  reported as unchecked. `TypedExpr::GenericClosure` has exactly one construction site
  (`typechecker/construction.rs`), reached only from a `let` whose value is a closure, and
  it always sets `name: Some(..)`. The `None` arm that records the skip is therefore
  unreachable, and every generic closure that exists is reconstructed and checked. The
  `name: Option<String>` field could be narrowed to a plain `String` to make that
  structural.
- **Parameters using `impl Aspect`** caused the checker to skip the *entire* body, not
  just the parameter. That was reachable only for a nested occurrence (`impl Printable[]`),
  because a top-level one was already lowered before move checking ran. metel-core#331
  lowers nested occurrences too, so nothing reaches it; the guard has been removed.
  This was the more serious of the two — a silent false negative for every move in an
  affected body.

### The place abstraction is shared, not move-specific

*Added 2026-07-31 (metel-core#291).* RFC-0071 §9b requires that whatever represents `x`,
`x.f`, `x.f.g`, and "reached through a dynamic index" be a standalone, reusable component
with no move-specific assumptions, so that borrow checking can later run a second analysis
over the *same* places without rebuilding them.

That component is `metel-interpreter/src/place.rs`. It was previously
`src/move_check/place.rs` — owned by, and reachable only through, the move checker's
namespace — and it could not represent a dereference at all: both constructors returned
`None` for `*p`, which a borrow checker needs. It now sits at the crate root beside the
analyses that use it, and carries a neutral `Projection::Deref`.

Policy stays with each analysis. That a move out of a dynamically indexed element is
rejected, or that a move through a reference needs a reborrow, are facts about moves and
live in `move_check`; `place` only says such a place exists and how it relates to its
prefixes.

### This is not a borrow checker

The checker has a narrow `&var` reborrow rule, but it does not perform lifetime,
aliasing, or escape analysis. It therefore cannot provide Rust-style guarantees about
overlapping mutable references. Runtime `RefCell` behaviour remains the final guard for
some mutable-reference mistakes.

*Revised 2026-08-01:* rejecting a by-value method through a reference (metel-core#348,
above) is deliberately **not** an exception to this. It needs no aliasing or lifetime
analysis — a reference's own type already says it does not own its pointee, which the
checker already knows from `Type::Reference`/`Type::MutReference` and the method's own
declared receiver kind. Nothing about *which* other bindings might alias the same memory
is involved. Borrow checking proper (RFC-0122) remains a distinct, larger analysis over
the same places `place.rs` already exists to share.

*Revised 2026-08-01 (adversarial review):* the initial #348 commit missed two shapes —
a non-place receiver (a call/`if`/`match`/cast result whose *type* is still a reference,
which has no `Place` for the second signal to find) was silently accepted, and a
multi-layer reference (`rr: &&B`) named only one `Deref` layer in its diagnostic
regardless of how many the type actually had. Both are fixed: the non-place case now
falls back to naming the moved value `<temporary>` rather than skipping the check, and
`deref_layers` counts every layer from the receiver's own type rather than assuming one.
The review also found the check itself lacked the `Copy` gate `illegal_move_kind` (the
sibling unconditional-ban mechanism this reuses) already had, wrongly rejecting a
`Copy` pointee's by-value method through a reference; fixed by gating on
`is_copy(peel_type_references(receiver.ty()))` before rejecting, mirrored above. §7.1's
own text has been narrowed to state its enforced scope is the method-receiver position
only — general assignment and by-value argument passing through a reference are not yet
checked, the same open gap as `maybe_read_copy`'s missing `Copy` check at read-copy
positions (§3a).

### Control flow is conservative

The checker unions possible moved state across branches without proving reachability.
That can produce false positives for an unreachable move; it does not make the ownership
check unsound.

*Revised 2026-07-31:* two parts of this have since changed (metel-core#291).

- **Loop bodies are now analysed to a fixed point.** The single pass described above
  unioned a body's exit state *outwards* but never fed it back in, so a move in a loop
  body was invisible to the next iteration — a false negative, not a false positive, and
  the more serious direction. Each body is now re-walked until the state entering it
  stops growing.
- **A path that leaves through `break`, `continue`, or `return` no longer contributes its
  moves to the code that follows it.** Those moves go where control goes: out of the loop
  for `break`, round it for `continue`, nowhere for `return`. This is what keeps the fixed
  point from rejecting `loop { let moved = s; break; }`, and it also removed a
  pre-existing false positive outside loops, where a move in a returning `if` branch was
  joined into the code after the `if`.

What remains conservative is the join itself: a branch's moves are still unioned without
asking whether that branch can be taken. Divergence is the only reachability fact the
checker uses. The visible cost is a loop bounded by its condition rather than by `break`:

```metel
while (i < 1) {        // runs once, but nothing proves that
    i += 1;
    let moved = s;     // reported as loop-carried
}
```

Writing the exit as a `break` avoids it. A trip-count analysis for this shape would close
the gap without a control-flow graph.

### What loop checking misses

Each of these was reproduced against the built interpreter.

*A seventh gap — shadowing a binding erased the shadowed binding's moved state, laundering
a carried move — was found by review and **fixed** (metel-core#343), not listed. Binding a
name now records what it displaced, and a `break` or `continue` unwinds the scopes it
jumps out of before recording its state.*

- **Calling a closure never consumes its captures** (metel-core#330), so a loop that calls
  a closure capturing a non-`Copy` value on every iteration is accepted. Capturing at
  creation *inside* a loop is caught, since that is an ordinary move. See "Confirmed
  closure soundness hole" below — this is the same hole, seen from the loop side, and it
  is the most significant thing loop checking does not catch.
- **Widening stops after eight passes.** A move cascade needing more would lose what a
  further pass would have found. Theoretical; the deepest case tested settles in one
  extra pass.
- **A generic body whose reconstruction fails is skipped** — see "Generic reconstruction
  can fail open" above. Every loop inside such a body goes unchecked with it.
- **Only the first violation is reported** (metel-core#338), so a loop body with several
  loop-carried moves surfaces them one at a time.

Writing to a moved place reinitializes it rather than counting as a use, so the idiomatic
move-then-replace loop body is accepted:

```metel
var s = "hello";
loop {
    let moved = s;
    s = "again";       // `s` is valid again from here
    …
}
```

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

*Revised 2026-07-30:* borrowed iteration has since landed (metel-core#329). The
duplication mechanism is **not** missing — `aspect Clone` exists in `stdlib/core.mtl`, a
user type may implement it, and `arr[i].clone()` under a `T: Clone` bound typechecks and
passes move checking. What is missing is stdlib *coverage*: the only impl is the blanket
`extend<T: Clone> T[]: Clone`, and neither `i64` nor `String` implements `Clone`, so
`T: Clone` is not a usable bound for a primitive (metel-core#335).

This means the callback pattern above is more avoidable than it looks. Where the elements
are `Copy` — as they are in most of the affected fixtures — a `T: Copy` bound removes the
callback today, which is what the sentence above already recommends. Reserve the callback
for genuinely non-`Copy` elements whose type has no `Clone` impl.

*Revised 2026-07-31:* the borrowing form this section recommends is now writable
directly. Calling an aspect method on a `&T` under a `T: Aspect` bound used to fail to
resolve, so such a body needed an explicit `(*x).method()`; metel-core#334 fixed the
auto-deref, and the workaround has been removed from the fixtures that carried it.

## Confirmed closure soundness hole

The move checker currently classifies every `Type::Fun` as `Copy`. That is appropriate
for a named function pointer, but it is not generally appropriate for a closure with a
non-`Copy` capture. The checker also validates a closure body at creation time without
tracking consumption of captures across later calls.

*Revised 2026-07-30:* the hole has two halves with different ages, which this section
originally ran together.

| use of a closure capturing a non-`Copy` value | before `541b925` | after |
|---|---|---|
| through a higher-order function — `call(f); call(f)` | rejected `T0019` | **accepted** |
| called directly — `f(); f()` | accepted | accepted |
| a *named function* value — `apply(g); apply(g)` | rejected `T0019` | accepted (correct) |

Only the direct-call half is long-standing: invoking a closure has never updated its
captures' moved state. The higher-order half is newer — `541b925`, satisfying #329's
"reusing a function value of a `Copy` function type remains valid", widened `is_copy` to
*every* `Type::Fun` rather than to function pointers, which is the third row working as
intended and the first row as collateral. So a fix must narrow that rule without
re-breaking row three.

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

*Revised 2026-07-31:* that issue is metel-core#330, and it has been **deliberately
deferred to v0.13.0** rather than fixed for v0.12.0. Two things came out of working the
option space that change how step 1 above should be read.

**Step 1 is not a matter of recovering a distinction — it does not exist.**
`Type::Fun(Vec<Type>, Box<Type>)` carries parameters and a return type and nothing else,
so a closure and a named function with the same signature have the same type. And at
runtime `RuntimeCallable` has only `Closure` and `Intrinsic`: a named function is built as
a closure value with a captured environment. "Distinguish plain function pointers from
closures" therefore means *creating* that distinction at both levels, not reading one.
RFC-0049 meets the same wall from the other side — a closure has no named type, so a
programmer cannot write an impl for one.

**Steps 2 and 3 are separable, and only step 2 is a regression.** Deriving `Copy` from
captures (step 2) rejects `call(f); call(f)`, the half that #329 introduced. It does not
reject `f(); f()`, because a call's callee is observed rather than consumed — that needs
step 3, and step 3 is long-standing rather than new.

The tempting middle path — tracking capture copyability on the *binding* as dataflow,
without touching the type — was considered and rejected. It fixes the published repro
while leaving the guarantee false wherever the closure crosses a call boundary, lands in a
field, or is returned. A checker that is right on the example and wrong on the shape is a
worse thing to ship under `--move-check` than a stated exclusion.

The principled routes (a capability bit on the function type, or explicit capture lists)
are RFC-0049 and RFC-0050, both drafts, and RFC-0050's `move` half waits on a successor to
the refused RFC-0046. The blocker is a design decision, not implementation time. The full
comparison is recorded on metel-core#330.

## Practical guidance

Treat `--move-check` as valuable early enforcement, not yet as a proof of complete
ownership safety. In particular, do not rely on reusing closures that capture non-`Copy`
state, do not treat an unchecked-generic warning as harmless, and keep ownership-sensitive
generic algorithms explicit about borrowing, copying, or cloning.

Put more sharply, for v0.12.0: the checker enforces ownership of **values**, not of
**closures**. A closure capturing a non-`Copy` value may be reused freely and calling one
never consumes what it captured (metel-core#330, deferred to v0.13.0). Everything else it
reports stands.
