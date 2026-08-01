---
id: affine-by-default-inversion
title: "Inverting the Default: Copy-by-Default with Opt-In Affinity and Explicit Moves"
type: report
status: active
last_synced_against_model: '2026-07-31'
supersedes: null
revives: null
---

# Inverting the Default

*Exploration, not a decision. Nothing here is ratified, and it argues against a
constraint that **is** ratified: RFC-0071 (`3-integrated`) makes affine the default for
every struct and enum field. Written 2026-07-31 out of a design conversation, immediately
after the loop-carried-move work on metel-core#291, when the question came up of whether
the whole default is pointed the wrong way.*

*It does not recommend adopting the inversion. It establishes what the idea is in the
vocabulary this directory already uses, what the prior art actually shows (three shipping
languages have each taken half of it), where the design would live or die, and what
Metel's own corpus says. The single most useful thing in it is §4: both languages that
thought hardest about this reached the same conclusion from opposite ends, and it is not
the conclusion either default suggests.*

**Read [`linear-types.md`](linear-types.md) first.** This document is a direct challenge
to its §1 and a re-derivation of its §2, and uses its lattice throughout.

---

## 1. The proposal, in the lattice's own terms

Two separable changes:

- **(A) Invert the default.** A type is unrestricted (`ω`, freely copyable) unless it
  opts into affinity, via a marker aspect or a declaration keyword.
- **(B) Make moves explicit.** An affine value cannot be transferred by ordinary use. It
  must be moved by a distinguished operation, so that ownership transfer is always
  visible at the point it happens.

`linear-types.md` §1 already names exactly what (A) undoes:

> `per-field-multiplicities.md` proposes a three-point lattice — 0 / 1 / ω — standard in
> quantitative type theory. That lattice assumes an ω-default background: ordinary
> bindings are already freely copyable, and restriction is something you add. **Metel
> inverts this.** […] A three-point lattice doesn't have a point for Metel's actual
> default. The lattice needs four.

So (A) is not a new axis. It is a proposal to *un-invert* — to move Metel back onto the
ω-default background that quantitative type theory assumes, which would make the standard
three-point lattice fit again with `affine` as an ordinary interior point rather than as
the unmarked case. That is a real simplification of the lattice, and it should be counted
in the proposal's favour.

It is also a real cost elsewhere in the same document, and §6 works through where.

(B) is orthogonal to (A). You can have either without the other. Rust has neither
explicit moves nor an ω default; C++ has both an ω default and explicit moves; Hylo has
explicit *copies* and no ω default at all. They are worth judging separately, because
their track records differ sharply.

---

## 2. The motivating complaint is weakly evidenced

The idea is usually motivated by the claim that Rust users find implicit moves
confusing. Searching for that constituency in 2026 does not find much.

The Rust project's own synthesis of ~70 interviews and ~5,500 survey responses
([*What we heard about Rust's challenges*](https://blog.rust-lang.org/2026/03/20/rust-challenges/),
2026-03) lists "borrow checking and ownership" as a **single** universal challenge and
never separates move semantics out of it. Its finding is that the difficulty is a
beginner phenomenon: *"Rust experts don't really complain about the borrow checker
anymore: it is a challenge that goes away with experience."* The companion
[*many journeys of learning Rust*](https://blog.rust-lang.org/2026/06/25/vision-doc-journeys-to-learning-rust/)
(2026-06) reports the same shape — what dominates is borrowing and lifetimes, and the
named friction is *"clone guilt,"* newcomers assuming they must avoid copies before they
have working code.

Two things follow, and both cut against the motivation rather than for it:

1. The reported pain is that copying is **expensive**, not that moving is **invisible**.
   An explicit-move design does not address that; if anything it adds ceremony to the
   operation people are already reluctant to reach for.
2. The pain is concentrated in **aliasing**, which this proposal does not touch. Affinity
   and borrowing are separate mechanisms — RFC-0122 is a separate RFC for a reason — and
   inverting the affinity default leaves the borrow checker exactly as hard as it was.

Explicit-relocation ideas do surface periodically in Rust's own forums (e.g.
[internals #6704](https://internals.rust-lang.org/t/idea-limited-custom-move-semantics-through-explicitly-specified-relocations/6704/15)),
and `E0382` is a real beginner stumbling block. But the recurring counterargument there
is that "move is memcpy" is a load-bearing simplification, and no organised demand for
inverting the default appears in the survey data.

**Conclusion for this section:** if the case for the inversion rests on user demand, it
is weak, and the report should say so plainly. The case has to be made on design merit.
That case is considerably stronger.

---

## 3. Prior art: three shipping languages, each with half of it

### (A) ω-default with opt-in restriction — Swift, Austral

[Swift SE-0390](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0390-noncopyable-structs-and-enums.md)
(shipped in 5.9) is (A) exactly. Every type, generic parameter, protocol and associated
type conforms to `Copyable` implicitly; `struct FileDescriptor: ~Copyable` suppresses it.
Their rationale is close to word-for-word what this proposal would argue: for copyable
types the borrow/consume distinction "is largely hidden from the programmer," and that
becomes impossible only for values that cannot be copied.

[Austral](https://borretti.me/article/introducing-austral) partitions types into a *free*
universe and a *linear* universe, with entry to the linear universe by fiat or by
containment. It chose that split explicitly for "fits-in-head simplicity" — the linearity
checker is a page of text. Note that Austral's containment rule is Metel's join rule
under another name: linearity is viral through fields, exactly as `linear-types.md` §1
already specifies.

### (B) Explicit transfer — Mojo, Pony, C++

[Mojo](https://docs.modular.com/mojo/manual/values/ownership/) requires the `^` transfer
sigil to give up ownership, and pitches it directly against Rust: these decisions
"provide an easier-to-use programming model compared to Rust, since developers must
consciously use the `^` operator rather than having moves occur automatically." Pony's
`consume` is the same idea with a keyword.

C++ is the cautionary half and the one worth internalising. `std::move` is explicit, and
a moved-from object is left in a "valid but unspecified state" — use-after-move is a lint,
not a type error. C++ therefore pays the full syntactic cost of explicitness and collects
almost none of the safety benefit.

**Explicitness and static enforcement are orthogonal.** This proposal wants both, and
Metel is already positioned for the second: `T0019` exists, and after metel-core#291
tracks moves through loops and dereferences. Any write-up of (B) should be explicit that
it is not proposing C++'s design, because that is the one most readers will pattern-match
onto.

---

## 4. Where it lives or dies: generic code

This is the section that matters, and the evidence is unusually clear because it comes
from both directions at once.

**Swift, having done (A), reports the cost.**
[SE-0427 (noncopyable generics)](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0427-noncopyable-generics.md)
states that *"the expectation that everything is copyable has been a crucial simplifying
assumption throughout Swift's API design work,"* which "allowed developers to define
convenient interfaces without thinking too deeply about ownership." SE-0427 let
noncopyable types participate in generics but **deliberately stopped short of adapting
the standard library**, and generalising associated types over suppressed `Copyable`
requirements was judged too large a design problem to attempt in the proposal at all.
That is years of work in a well-resourced language, and the cause is having two universes
where the library was written assuming one.

**Hylo, facing the same problem, inverted in the opposite direction.**
[Hylo](https://hylo-lang.org/introduction/) makes *all* types non-copyable and requires
copies to be explicit — `x.copy()`, even for `Int`. Its
[stated reasoning](https://github.com/hylo-lang/Documentation/blob/main/val-for-swift-users.md)
is that once its parameter conventions eliminate most copies, the remaining need for
copying is rare enough that making every copy explicit *"simplif[ies] the story for
generic code."*

So Swift and Hylo agree on the diagnosis and disagree on the cure:

> **Generic code is easier when the universe is uniform. Whichever operation is rare
> should be the one that is explicit.**

Neither language concluded that the right answer is a comfortable default plus an escape
hatch. Swift has that and is still paying for it; Hylo rejected it in advance.

This is the strongest argument against the proposal *as stated*, because the proposal is
non-uniform by construction: it creates two universes and makes the rare operation
(moving an affine value) explicit **while also** keeping the common universe implicit.
It inherits Swift's problem.

It is also the strongest hint about where a better version might be. Hylo's mechanism is
not a type-level marker at all — its `sink` convention is a property of a **parameter**,
not of a type. A parameter-convention design says "this function consumes its argument"
rather than "this type must always be moved explicitly," which keeps a single universe of
types and puts the ownership information at the call boundary where generic code can
abstract over it uniformly. That is a materially different design from (A)+(B) and is not
explored here.

**Concretely for Metel**, the question to answer before anything else: what does

```metel
fun first<T>(xs: T[]) -> T
```

mean when `T` is affine? Either every generic grows an affinity bound (Swift's route, and
the reason its stdlib migration stalled), or the language needs a "conditionally affine"
notion. Metel has aspects, bounds, associated types, conditional impls, and negative impls
— that is precisely the machinery that got complicated in Swift, and it is all already
built.

---

## 5. What Metel's own corpus says

Measured on 2026-07-31 against the `fix/291` build, using `move-check-count` over
`tests/integration/sources`.

| | |
|---|---|
| Programs the tool could load and check | ≈460 |
| User-code move violations | 32, across 30 fixtures |
| Embedded-stdlib move violations | **10 sites** |

Two cautions about these numbers, because both are easy to misread:

- The **32 user violations are almost entirely deliberate**. They are the
  `evaluator/move_check/*.mtl` negative fixtures, which exist to violate the rules. The
  v0.12.0 changelog's claim that "the move-check corpus has no unintentional violations
  left" is consistent with this. Ordinary corpus code is already affine-clean.
- The **10 stdlib sites** are the honest figure. The raw report prints
  `embedded_std_move_violations=4590`, but the embedded stdlib is re-checked once per
  program; checking a single trivial program yields 10. The 4590 is ≈460 × 10, not 4590
  distinct sites. Any argument built on the larger number is wrong by two orders of
  magnitude.

**What this actually supports is weaker than it first appears.** The tempting argument —
"affine-by-default forces a huge stdlib migration, so inverting the default makes
metel-core#310 shippable" — does not survive the correction. Ten sites is a morning's
work, not a migration. And ordinary corpus code being already affine-clean says the
affine default is *not* currently costing expressiveness either.

The correct reading is that **Metel's corpus is too small and too simple to discriminate
between the two designs.** ≈460 mostly-toy programs and a small stdlib will not reproduce
the pressure that a mature standard library puts on this decision. Swift's experience is
the better predictor of what happens at scale, and it points the other way.

### Where the inversion would genuinely pay off

One concrete win survives the scrutiny, and it is not about migration:

**metel-core#330 largely evaporates.** The closure `Copy` hole is a hole because closures
capturing ordinary values must be non-`Copy`, which forces the checker to reason about
whether invoking a closure consumes its captures. If ordinary values are `ω`, only
closures capturing *affine* values need the `FnOnce`/`FnMut`/`Fn` distinction — a much
smaller feature, better motivated, and one that would no longer gate #310.

A second, weaker win: affinity would line up naturally with resource ownership, letting
`Drop` imply the affine marker. That gives RFC-0071 §9c's release gate ("#290 must not
ship without #292") a cleaner story, since the types with destructors would be exactly
the types with restricted use.

---

## 6. What it would change inside this directory

The inversion is not confined to RFC-0071. It rewrites parts of `linear-types.md`:

- **§1's four-point lattice collapses back to three.** With an ω default, `affine` stops
  needing a point that the standard 0/1/ω lattice lacks; it becomes an ordinary interior
  point that a type opts into. This is a simplification, and the clearest thing the
  proposal has going for it.
- **§2's "`Affine` needs no aspect of its own" inverts.** That claim holds only because
  affine is currently an *absence* — definitionally `!Copy + !Linear`, expressible with
  RFC-0072's mixed bound form and nameable via an RFC-0039 alias. Under an ω default,
  affinity becomes a **positive** capability and needs a real marker aspect that a type
  can implement, with the join rule deriving it structurally through fields.
- **§2.1's `affine struct` sugar changes meaning.** It currently desugars to a *locking
  pair of negative impls* (`extend X: !Copy;` + `extend X: !Linear;`), whose value is that RFC-0081
  coherence prevents anyone later adding `extend X: Copy` and silently changing what moving
  the type means. Under the inversion it becomes an ordinary positive grant, and that
  locking property has to be recovered some other way — or given up.
- **The `Copy`/`Drop` exclusion (RFC-0071 §4) stops being a special case of the join
  rule** in the same way, since `Drop` would now be the thing that *implies* restriction
  rather than a constraint that coexists with an already-restricted default.

None of this is fatal. All of it is work that has not been costed, and it lands on a
document that the RFC-0089 / RFC-0091 drafts were extracted from.

---

## 7. The explicit-move mechanism should not be an aspect method

The conversation that produced this report proposed spelling the move as an aspect method
call. That specific mechanism is the weakest part, for reasons worth recording so it is
not re-proposed:

- **A move has no runtime behaviour.** It is a static annotation about ownership. As an
  ordinary aspect method it would be user-implementable per type, which is semantically
  meaningless, and generic code could not rely on what any particular implementation did.
- **The compiler must special-case it regardless**, so it should *look* special. Mojo,
  Pony and C++ all reached for a sigil or keyword rather than a method, and a form like
  `consume x` or `x^` is more honest about being compiler-known.
- **Method syntax is mildly circular**: `x.move()` uses `x` as a receiver in order to
  make `x` unusable.

The aspect is the right shape for the **marker** — a pure marker aspect, structurally
identical to how `linear-types.md` §2 already proposes `Linear`, with `Drop` implying it.
Marker: aspect. Operation: keyword.

---

## 8. Open questions

Ordered by how much the answer would change the design.

1. **The generic instantiation rule** (§4). Every generic gets an affinity bound, or
   there is a conditional-affinity notion, or the design does not work. Swift's stalled
   stdlib migration is the evidence that this is not a detail.
2. **Type-level marker or parameter convention?** Hylo's `sink` suggests the whole thing
   may belong at the parameter boundary rather than on types, which would keep one
   universe and dissolve most of (1). This is the most promising unexplored direction and
   is not covered here.
3. **Does `Drop` imply affinity**, or is the marker independent? A capability token
   wanting unique ownership without a destructor argues for independence; the release
   gate argues for implication.
4. **What does §6's lost locking property cost?** `affine struct` currently makes a
   checked commitment that nothing can later add `impl Copy`. An opt-in positive grant
   does not, by itself.
5. **Confirm the borrow checker is untouched.** It should be — affinity and aliasing are
   separate, and RFC-0122 is separate for that reason. Worth stating explicitly in any
   RFC, because §2 shows aliasing is where the real user pain lives, and a reader will
   otherwise assume this proposal is aimed at it.

**Not open:** whether this is motivated by demand from Rust users. §2 answers that, and
the answer is no. If the inversion is worth doing it is worth doing on the grounds in §4
and §5, and any RFC should say so rather than lead with an ergonomics claim the evidence
does not support.

---

## Sources

- [SE-0390: Noncopyable structs and enums](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0390-noncopyable-structs-and-enums.md)
- [SE-0427: Noncopyable generics](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0427-noncopyable-generics.md)
- [Mojo: Ownership and the transfer operator](https://docs.modular.com/mojo/manual/values/ownership/)
- [Introducing Austral: A Systems Language with Linear Types and Capabilities](https://borretti.me/article/introducing-austral)
- [Hylo: Introduction](https://hylo-lang.org/introduction/) and [Val for Swift users](https://github.com/hylo-lang/Documentation/blob/main/val-for-swift-users.md)
- [What we heard about Rust's challenges](https://blog.rust-lang.org/2026/03/20/rust-challenges/) (Rust Blog, 2026-03-20)
- [The many journeys of learning Rust](https://blog.rust-lang.org/2026/06/25/vision-doc-journeys-to-learning-rust/) (Rust Blog, 2026-06-25)
- [Rust internals: limited custom move semantics through explicitly specified relocations](https://internals.rust-lang.org/t/idea-limited-custom-move-semantics-through-explicitly-specified-relocations/6704/15)
